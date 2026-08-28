"""
license.py - Tiered Commercial Licensing Engine for AI Model Manager.
Tiers: community (free) / pro / enterprise. HMAC-SHA256 signed license keys.
"""
import os
import time
import json
import hmac
import hashlib
import base64

APP_DIR = os.path.dirname(os.path.abspath(__file__))
LICENSE_PATH = os.path.join(APP_DIR, "license.json")

# Secret used to sign licenses — MUST be overridden via env in production builds
_DEFAULT_LICENSE_SECRET = "AIMM-LICENSE-v1-SECRET"
SIGNING_SECRET = os.environ.get("AIMM_LICENSE_SECRET", _DEFAULT_LICENSE_SECRET)

if SIGNING_SECRET == _DEFAULT_LICENSE_SECRET:
    import sys
    print(
        "⚠️  LICENSE WARNING: Using default AIMM_LICENSE_SECRET. "
        "Set AIMM_LICENSE_SECRET env var to a strong secret in production to prevent forged license keys.",
        file=sys.stderr, flush=True
    )

TIERS = {
    "community": {
        "label": "Community (Free)",
        "price": 0,
        "features": ["providers", "presets", "router", "cache", "virtual_keys"],
        "max_users": 1,
        "max_requests_per_min": 60
    },
    "pro": {
        "label": "Pro",
        "price": 12,
        "features": ["providers", "presets", "router", "cache", "virtual_keys",
                     "analytics", "reports", "rate_limits", "rbac"],
        "max_users": 10,
        "max_requests_per_min": 600
    },
    "enterprise": {
        "label": "Enterprise",
        "price": 39,
        "features": ["providers", "presets", "router", "cache", "virtual_keys",
                     "analytics", "reports", "rate_limits", "rbac", "sso", "docker"],
        "max_users": 1000,
        "max_requests_per_min": 10000
    }
}

def _sign(payload: str) -> str:
    return hmac.new(SIGNING_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()

def generate_license(owner: str, tier: str = "pro", months: int = 12) -> dict:
    tier = tier if tier in TIERS else "pro"
    issued = int(time.time())
    expires = issued + months * 30 * 24 * 3600
    payload = json.dumps({"owner": owner, "tier": tier, "issued": issued, "expires": expires},
                         sort_keys=True, separators=(",", ":"))
    sig = _sign(payload)
    key = base64.urlsafe_b64encode(f"{payload}.{sig}".encode("utf-8")).decode("ascii")
    return {"license_key": key, "owner": owner, "tier": tier, "expires": expires}

def validate_license(license_key: str) -> dict:
    """Returns license info dict, raises ValueError on invalid/expired."""
    if not license_key:
        raise ValueError("No license key provided")
    try:
        raw = base64.urlsafe_b64decode(license_key.encode("ascii")).decode("utf-8")
        payload, sig = raw.rsplit(".", 1)
        expected = _sign(payload)
        if not hmac.compare_digest(expected, sig):
            raise ValueError("Invalid license signature")
        data = json.loads(payload)
        if int(data["expires"]) < time.time():
            raise ValueError("License expired")
        tier = data.get("tier", "community")
        if tier not in TIERS:
            raise ValueError(f"Unknown tier: {tier}")
        return {**data, "tier_info": TIERS[tier]}
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError, IndexError) as e:
        raise ValueError(f"Invalid license key: {e}")

def activate_license(license_key: str) -> dict:
    info = validate_license(license_key)
    with open(LICENSE_PATH, "w", encoding="utf-8") as f:
        json.dump({"license_key": license_key, "activated_at": time.strftime("%Y-%m-%d %H:%M:%S")}, f, indent=2)
    return {"status": "activated", **info}

def get_license_status() -> dict:
    if os.path.exists(LICENSE_PATH):
        try:
            with open(LICENSE_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            return {"status": "active", **validate_license(saved.get("license_key", ""))}
        except Exception as e:
            return {"status": "invalid", "error": str(e)}
    return {"status": "community", "tier": "community", "tier_info": TIERS["community"]}

def feature_enabled(feature: str) -> bool:
    status = get_license_status()
    return feature in TIERS.get(status.get("tier", "community"), {}).get("features", [])
