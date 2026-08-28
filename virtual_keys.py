"""
virtual_keys.py - AIPI Platform API Key Generator & Multi-Tenant Access Controller.
Developed by gnonymous.

Generates and manages cryptographically secure AIPI API keys (aipi-live-...)
with budget enforcement, rate limits, model authorization, and auto-provisioned master keys.
"""
import time
import secrets
import json
from datetime import datetime, timedelta
from db import get_connection, init_db

KEY_PREFIX = "aipi-live-"
VALID_PREFIXES = ("aipi-live-", "px-live-", "sk-proxia-", "sk-mgr-")


def generate_key_string(prefix: str = KEY_PREFIX) -> str:
    """Generate a high-entropy, URL-safe API key string."""
    entropy = secrets.token_urlsafe(32).replace("-", "").replace("_", "")[:36]
    return f"{prefix}{entropy}"


def ensure_master_key() -> dict:
    """
    Ensure that a default Master AIPI API key exists for the platform.
    Auto-provisions one on first startup.
    """
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM virtual_keys WHERE name = 'Master AIPI Key' AND status = 'active'").fetchone()
        if row:
            k = dict(row)
            sk = k.get("secret_key", "")
            if sk.startswith("aipi-live-"):
                k["masked_key"] = sk[:12] + "…" + sk[-4:] if len(sk) > 16 else sk
                return k

    # Auto-provision master key
    master_key = create_virtual_key(
        name="Master AIPI Key",
        max_monthly_budget=0.0,  # Unlimited
        allowed_models=[],       # All models
        rate_limit_rpm=0,        # Unlimited
        expires_in_days=0        # Never
    )
    return master_key


def get_master_key() -> dict:
    """Return the primary active Master AIPI API key."""
    return ensure_master_key()


def create_virtual_key(
    name: str,
    max_monthly_budget: float = 0.0,
    allowed_models: list = None,
    rate_limit_rpm: int = 0,
    expires_in_days: int = 0
) -> dict:
    """
    Mint a new platform API key for AIPI.
    """
    init_db()
    name = (name or "AIPI API Key").strip()
    key_id = "pk_" + secrets.token_hex(6)
    secret_key = generate_key_string()

    models_list = [m.strip() for m in (allowed_models or []) if m and m.strip()]
    models_json = json.dumps(models_list)

    expires_at = None
    if expires_in_days and expires_in_days > 0:
        exp_dt = datetime.now() + timedelta(days=int(expires_in_days))
        expires_at = exp_dt.strftime("%Y-%m-%d %H:%M:%S")

    created_at = time.strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO virtual_keys (
                key_id, name, secret_key, max_monthly_budget, current_spend,
                allowed_models, rate_limit_rpm, expires_at, last_used_at, status, created_at
            )
            VALUES (?, ?, ?, ?, 0.0, ?, ?, ?, NULL, 'active', ?)
        """, (
            key_id, name, secret_key, float(max_monthly_budget),
            models_json, int(rate_limit_rpm), expires_at, created_at
        ))

    return {
        "key_id": key_id,
        "name": name,
        "secret_key": secret_key,
        "masked_key": secret_key[:11] + "…" + secret_key[-4:],
        "max_monthly_budget": float(max_monthly_budget),
        "current_spend": 0.0,
        "allowed_models": models_list,
        "rate_limit_rpm": int(rate_limit_rpm),
        "expires_at": expires_at,
        "last_used_at": None,
        "status": "active",
        "created_at": created_at
    }


def validate_key(secret_key: str, requested_model: str = None) -> tuple:
    """
    Validate an AIPI API key.
    Returns (is_valid: bool, reason: str, key_info: dict).
    """
    if not secret_key:
        return False, "Missing API key", None

    secret_key = secret_key.strip()
    if not any(secret_key.startswith(p) for p in VALID_PREFIXES):
        return False, "Invalid API key format (expected aipi-live-...)", None

    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM virtual_keys WHERE secret_key = ?", (secret_key,)).fetchone()
        if not row:
            return False, "API key not found or unrecognized", None

        k = dict(row)

        # 1. Check status
        if k.get("status") != "active":
            return False, "This API key has been revoked", k

        # 2. Check expiration
        expires_at = k.get("expires_at")
        if expires_at:
            try:
                exp_dt = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
                if datetime.now() > exp_dt:
                    return False, f"This API key expired on {expires_at}", k
            except Exception:
                pass

        # 3. Check budget limits
        budget = float(k.get("max_monthly_budget", 0.0))
        spend = float(k.get("current_spend", 0.0))
        if budget > 0.0 and spend >= budget:
            return False, f"Monthly budget limit reached (${spend:.2f} / ${budget:.2f})", k

        # 4. Check model whitelist authorization
        raw_allowed = k.get("allowed_models") or "[]"
        try:
            allowed_list = json.loads(raw_allowed) if isinstance(raw_allowed, str) else raw_allowed
        except Exception:
            allowed_list = []

        if allowed_list and requested_model:
            req_clean = requested_model.strip().lower()
            if not any(req_clean == am.strip().lower() for am in allowed_list):
                return False, f"Model '{requested_model}' not authorized for this API key", k

        # 5. Check rate limit
        rpm = int(k.get("rate_limit_rpm", 0))
        if rpm > 0:
            try:
                from ratelimit import check_rate_limit
                rl_res = check_rate_limit(secret_key, rate_per_minute=float(rpm), capacity=float(rpm // 5 or 5))
                if not rl_res.get("allowed", True):
                    return False, f"Rate limit exceeded ({rpm} req/min). Retry in {rl_res.get('retry_after_s', 1):.1f}s", k
            except Exception:
                pass

        # Update last_used_at timestamp
        try:
            now_str = time.strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("UPDATE virtual_keys SET last_used_at = ? WHERE secret_key = ?", (now_str, secret_key))
            k["last_used_at"] = now_str
        except Exception:
            pass

        return True, "API key valid", k


def record_spend(secret_key: str, amount_usd: float):
    """Record financial spend against an API key."""
    if not secret_key or amount_usd <= 0.0:
        return
    init_db()
    with get_connection() as conn:
        conn.execute("""
            UPDATE virtual_keys 
            SET current_spend = current_spend + ? 
            WHERE secret_key = ?
        """, (float(amount_usd), secret_key))


def list_virtual_keys() -> list:
    """List all minted AIPI API keys."""
    init_db()
    ensure_master_key()
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT key_id, name, secret_key, max_monthly_budget, current_spend,
                   allowed_models, rate_limit_rpm, expires_at, last_used_at, status, created_at
            FROM virtual_keys
            ORDER BY created_at DESC
        """).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            sk = d.get("secret_key", "")
            d["masked_key"] = sk[:11] + "…" + sk[-4:] if len(sk) > 15 else sk
            raw_models = d.get("allowed_models") or "[]"
            try:
                d["allowed_models"] = json.loads(raw_models) if isinstance(raw_models, str) else raw_models
            except Exception:
                d["allowed_models"] = []
            result.append(d)
        return result


def revoke_key(key_id: str) -> bool:
    """Revoke or delete an API key."""
    init_db()
    with get_connection() as conn:
        cursor = conn.execute("UPDATE virtual_keys SET status = 'revoked' WHERE key_id = ?", (key_id.strip(),))
        if cursor.rowcount > 0:
            return True
        # If not updated, try deleting
        cursor2 = conn.execute("DELETE FROM virtual_keys WHERE key_id = ?", (key_id.strip(),))
        return cursor2.rowcount > 0


def delete_key(key_id: str) -> bool:
    """Permanently delete an API key."""
    init_db()
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM virtual_keys WHERE key_id = ?", (key_id.strip(),))
        return cursor.rowcount > 0
