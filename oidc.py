"""
oidc.py - SSO / OIDC (Single Sign-On) integration for AI Model Manager Enterprise.
Configurable with any standard OIDC provider (Google, Azure AD, Okta, Keycloak).
No credentials configured -> graceful community mode.
"""
import os
import json
import time
import base64
import urllib.request
import urllib.parse

APP_DIR = os.path.dirname(os.path.abspath(__file__))
OIDC_CONFIG_PATH = os.path.join(APP_DIR, "oidc_config.json")

def get_oidc_config() -> dict:
    if os.path.exists(OIDC_CONFIG_PATH):
        try:
            with open(OIDC_CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            return cfg
        except Exception:
            pass
    # env fallback
    cfg = {
        "issuer": os.environ.get("AIMM_OIDC_ISSUER", ""),
        "client_id": os.environ.get("AIMM_OIDC_CLIENT_ID", ""),
        "client_secret": os.environ.get("AIMM_OIDC_CLIENT_SECRET", ""),
        "redirect_uri": os.environ.get("AIMM_OIDC_REDIRECT_URI", "http://127.0.0.1:11434/v1/auth/oidc/callback"),
    }
    return cfg

def save_oidc_config(cfg: dict) -> dict:
    clean = {
        "issuer": (cfg.get("issuer") or "").strip(),
        "client_id": (cfg.get("client_id") or "").strip(),
        "client_secret": (cfg.get("client_secret") or "").strip(),
        "redirect_uri": (cfg.get("redirect_uri") or "").strip(),
    }
    with open(OIDC_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2)
    return clean

def _discover(issuer: str) -> dict:
    """Fetch OIDC discovery document (/.well-known/openid-configuration)."""
    url = issuer.rstrip("/") + "/.well-known/openid-configuration"
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))

def is_configured() -> bool:
    cfg = get_oidc_config()
    return bool(cfg.get("issuer") and cfg.get("client_id"))

def build_auth_url(state: str = "aimm") -> str:
    if not is_configured():
        raise ValueError("OIDC/SSO is not configured. Set issuer + client_id in /v1/admin/oidc/config or env vars.")
    cfg = get_oidc_config()
    meta = _discover(cfg["issuer"])
    params = {
        "client_id": cfg["client_id"],
        "response_type": "code",
        "scope": "openid profile email",
        "redirect_uri": cfg["redirect_uri"],
        "state": state,
    }
    return meta["authorization_endpoint"] + "?" + urllib.parse.urlencode(params)

def exchange_code(code: str) -> dict:
    """Exchange authorization code for tokens and fetch userinfo."""
    if not is_configured():
        raise ValueError("OIDC/SSO is not configured")
    cfg = get_oidc_config()
    meta = _discover(cfg["issuer"])
    token_data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": cfg["redirect_uri"],
        "client_id": cfg["client_id"],
        "client_secret": cfg.get("client_secret", ""),
    }).encode("utf-8")
    req = urllib.request.Request(meta["token_endpoint"], data=token_data,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=15) as r:
        tokens = json.loads(r.read().decode("utf-8"))
    access_token = tokens.get("access_token", "")
    # fetch userinfo
    userinfo = {}
    if access_token and meta.get("userinfo_endpoint"):
        try:
            ureq = urllib.request.Request(meta["userinfo_endpoint"],
                                          headers={"Authorization": "Bearer " + access_token})
            with urllib.request.urlopen(ureq, timeout=10) as ur:
                userinfo = json.loads(ur.read().decode("utf-8"))
        except Exception:
            pass
    return {
        "email": userinfo.get("email") or userinfo.get("preferred_username") or "sso-user",
        "name": userinfo.get("name", ""),
        "sub": userinfo.get("sub", ""),
        "raw_userinfo": userinfo,
    }

def oidc_status() -> dict:
    cfg = get_oidc_config()
    return {
        "configured": is_configured(),
        "issuer": cfg.get("issuer", "") or "(not set)",
        "client_id": cfg.get("client_id", "") or "(not set)",
        "redirect_uri": cfg.get("redirect_uri", ""),
    }
