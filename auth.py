"""
auth.py - RBAC (Role-Based Access Control) for AI Model Manager Team Edition.
Roles: admin > member > viewer. Passwords hashed with PBKDF2-HMAC-SHA256 (stdlib only).
"""
import os
import time
import json
import hashlib
import secrets
from db import get_connection, init_db

DEFAULT_ROLE = "member"
ROLE_RANK = {"viewer": 1, "member": 2, "admin": 3}

def _init_auth_table():
    init_db()
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT,
                salt TEXT,
                role TEXT DEFAULT 'member',
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                username TEXT,
                role TEXT,
                expires_at REAL
            )
        """)
        conn.commit()

def _hash_password(password: str, salt: str = None) -> (str, str):
    salt = salt or secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000).hex()
    return h, salt

def create_user(username: str, password: str, role: str = DEFAULT_ROLE) -> dict:
    _init_auth_table()
    username = (username or "").strip().lower()
    if not username or len(username) < 3:
        raise ValueError("Username must be at least 3 characters")
    if len(password or "") < 6:
        raise ValueError("Password must be at least 6 characters")
    role = role if role in ROLE_RANK else DEFAULT_ROLE
    ph, salt = _hash_password(password)
    with get_connection() as conn:
        exists = conn.execute("SELECT username FROM users WHERE username = ?", (username,)).fetchone()
        if exists:
            raise ValueError(f"User '{username}' already exists")
        conn.execute("""
            INSERT INTO users (username, password_hash, salt, role, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (username, ph, salt, role, time.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    return {"username": username, "role": role}

def authenticate(username: str, password: str) -> dict:
    """Returns (user_dict) on success, raises ValueError on failure."""
    _init_auth_table()
    username = (username or "").strip().lower()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if not row:
            raise ValueError("Invalid username or password")
        ph, salt = _hash_password(password, row["salt"])
        if ph != row["password_hash"]:
            raise ValueError("Invalid username or password")
        token = "sess-" + secrets.token_urlsafe(24)
        expires = time.time() + 24 * 3600  # 24h session
        conn.execute("INSERT OR REPLACE INTO sessions (token, username, role, expires_at) VALUES (?, ?, ?, ?)",
                     (token, row["username"], row["role"], expires))
        conn.commit()
        return {"username": row["username"], "role": row["role"], "token": token}

def validate_session(token: str) -> dict:
    """Validate a session token. expires_at is stored and compared as a Unix epoch timestamp (float)."""
    _init_auth_table()
    if not token:
        raise ValueError("Missing session token")
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE token = ?", (token,)).fetchone()
        if not row:
            raise ValueError("Invalid or expired session")
        try:
            exp_time = float(row["expires_at"])
        except (ValueError, TypeError):
            exp_time = 0.0
        if exp_time < time.time():
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            raise ValueError("Session expired")
        return {"username": row["username"], "role": row["role"]}

def list_users() -> list:
    _init_auth_table()
    with get_connection() as conn:
        rows = conn.execute("SELECT username, role, created_at FROM users ORDER BY created_at").fetchall()
        return [dict(r) for r in rows]

def delete_user(username: str, current_role: str = "admin") -> bool:
    _init_auth_table()
    username = (username or "").strip().lower()
    if username == "admin":
        raise ValueError("Cannot delete the built-in admin account")
    if ROLE_RANK.get(current_role, 0) < ROLE_RANK["admin"]:
        raise ValueError("Admin role required")
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.execute("DELETE FROM sessions WHERE username = ?", (username,))
        conn.commit()
        return cur.rowcount > 0

def set_user_role(username: str, role: str, current_role: str = "admin") -> dict:
    _init_auth_table()
    if role not in ROLE_RANK:
        raise ValueError(f"Invalid role: {role}")
    if ROLE_RANK.get(current_role, 0) < ROLE_RANK["admin"]:
        raise ValueError("Admin role required")
    username = (username or "").strip().lower()
    with get_connection() as conn:
        cur = conn.execute("UPDATE users SET role = ? WHERE username = ?", (role, username))
        conn.commit()
        if cur.rowcount == 0:
            raise ValueError(f"User '{username}' not found")
    return {"username": username, "role": role}

def ensure_admin_bootstrap(password: str = "admin123") -> dict:
    """Auto-create the default admin account on first boot."""
    _init_auth_table()
    with get_connection() as conn:
        exists = conn.execute("SELECT username FROM users WHERE username = 'admin'").fetchone()
    if not exists:
        result = create_user("admin", password, "admin")
        import sys
        print(
            "\n" + "=" * 70 + "\n"
            "  ⚠️  SECURITY WARNING: Default admin account created.\n"
            "  Username: admin   Password: admin123\n"
            "  Change your password immediately via the Admin tab in the\n"
            "  web dashboard or POST /v1/admin/change-password.\n"
            + "=" * 70 + "\n",
            file=sys.stderr, flush=True
        )
        return result
    return {"username": "admin", "role": "admin", "message": "already exists"}

def change_password(username: str, old_password: str, new_password: str) -> bool:
    """Verify old password and set new password."""
    _init_auth_table()
    username = (username or "").strip().lower()
    if not new_password or len(new_password) < 6:
        raise ValueError("New password must be at least 6 characters")
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if not row:
            raise ValueError(f"User '{username}' not found")
        ph, salt = _hash_password(old_password, row["salt"])
        if ph != row["password_hash"]:
            raise ValueError("Incorrect current password")
        new_ph, new_salt = _hash_password(new_password)
        conn.execute("UPDATE users SET password_hash = ?, salt = ? WHERE username = ?", (new_ph, new_salt, username))
        conn.commit()
    return True

def has_admin_users() -> bool:
    """Returns True if at least one admin user exists in DB."""
    _init_auth_table()
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'admin'").fetchone()
        return (row["cnt"] if row else 0) > 0

def check_auth_lock(token_or_key: str) -> dict:
    """
    Validates token against active user sessions OR Master Virtual API Keys.
    Raises ValueError if unauthorized.
    """
    _init_auth_table()
    if not token_or_key:
        raise ValueError("Authentication required: missing X-Admin-Token or Bearer Key")

    token_clean = token_or_key.replace("Bearer ", "").strip()

    # 1. Try user session token
    if token_clean.startswith("sess-"):
        return validate_session(token_clean)

    # 2. Try Virtual Master Key
    try:
        from virtual_keys import validate_virtual_key
        vk = validate_virtual_key(token_clean)
        if vk:
            return {"username": f"key:{vk.get('name','master')}", "role": "admin"}
    except Exception:
        pass

    raise ValueError("Invalid authentication credentials")

