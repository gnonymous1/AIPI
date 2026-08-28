"""
oauth_manager.py - Universal OAuth 2.0 & Device Code Flow Manager for AIPI.
Supports 1-Click OAuth connection for GitHub Copilot, Google Gemini, Anthropic/Claude Code, and major providers.
Developed by gnonymous.
"""
import os
import json
import time
import uuid
import base64
import hashlib
import secrets
import threading
import urllib.request
import urllib.parse
from db import get_raw_config, save_all_config, add_or_update_provider
from vault import encrypt_key

# Standard Client IDs used for IDE & CLI tool integrations
GITHUB_COPILOT_CLIENT_ID = "Iv1.b507a08c87ecfe81" # Standard VSCode/CLI Copilot client
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "936475272427-pvhscbb0gclmr4u4la0k17u34b6b6s11.apps.googleusercontent.com")

_active_device_flows = {} # flow_id -> flow_dict
_active_pkce_flows = {}   # state -> pkce_dict

def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

# ==============================================================================
# 1. GITHUB COPILOT DEVICE CODE OAUTH FLOW
# ==============================================================================
def start_github_copilot_flow() -> dict:
    """
    Starts GitHub Device Flow for Copilot:
    1. Requests device_code and user_code from github.com
    2. Spawns background polling worker to capture token upon user confirmation
    """
    flow_id = str(uuid.uuid4())[:8]
    data = urllib.parse.urlencode({
        "client_id": GITHUB_COPILOT_CLIENT_ID,
        "scope": "read:user"
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://github.com/login/device/code",
        data=data,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode())
    except Exception as e:
        return {"ok": False, "error": f"Failed to initiate GitHub device flow: {e}"}

    device_code = body.get("device_code")
    user_code = body.get("user_code")
    verification_uri = body.get("verification_uri", "https://github.com/login/device")
    interval = int(body.get("interval", 5))
    expires_in = int(body.get("expires_in", 900))

    flow_record = {
        "flow_id": flow_id,
        "provider": "GitHub Copilot",
        "device_code": device_code,
        "user_code": user_code,
        "verification_uri": verification_uri,
        "status": "pending",
        "created_at": time.time(),
        "expires_at": time.time() + expires_in,
        "token": None,
        "error": None
    }
    _active_device_flows[flow_id] = flow_record

    # Start background polling thread
    t = threading.Thread(target=_poll_github_copilot_token, args=(flow_id, device_code, interval), daemon=True)
    t.start()

    return {
        "ok": True,
        "flow_id": flow_id,
        "user_code": user_code,
        "verification_uri": verification_uri,
        "expires_in": expires_in,
        "message": f"Enter code {user_code} at {verification_uri}"
    }

def _poll_github_copilot_token(flow_id: str, device_code: str, interval: int):
    poll_url = "https://github.com/login/oauth/access_token"
    start_time = time.time()

    while time.time() - start_time < 900:
        time.sleep(interval)
        if flow_id not in _active_device_flows:
            break

        data = urllib.parse.urlencode({
            "client_id": GITHUB_COPILOT_CLIENT_ID,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
        }).encode("utf-8")

        req = urllib.request.Request(
            poll_url,
            data=data,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                res_data = json.loads(resp.read().decode())
        except Exception:
            continue

        if "access_token" in res_data:
            gh_token = res_data["access_token"]
            # Exchange GitHub OAuth token for Copilot internal session token
            copilot_token = _exchange_copilot_token(gh_token)
            
            # Register provider in AIPI
            add_or_update_provider({
                "name": "GitHub Copilot",
                "format": "openai",
                "base_url": "https://api.githubcopilot.com",
                "api_key": copilot_token or gh_token,
                "default_model": "gpt-4o",
                "notes": "Connected via 1-Click GitHub OAuth Flow",
                "default_temperature": 0.7,
                "default_max_tokens": 4096
            })

            _active_device_flows[flow_id]["status"] = "completed"
            _active_device_flows[flow_id]["token"] = copilot_token or gh_token
            break

        error = res_data.get("error")
        if error == "authorization_pending":
            continue
        elif error == "slow_down":
            interval += 5
        elif error in ("expired_token", "access_denied", "unsupported_grant_type"):
            _active_device_flows[flow_id]["status"] = "error"
            _active_device_flows[flow_id]["error"] = error
            break

def _exchange_copilot_token(github_token: str) -> str:
    """Exchange standard GitHub OAuth token for Copilot backend token."""
    req = urllib.request.Request(
        "https://api.github.com/copilot_internal/v2/token",
        headers={
            "Authorization": f"token {github_token}",
            "Accept": "application/json",
            "User-Agent": "AIPI/1.0"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get("token", github_token)
    except Exception:
        return github_token


# ==============================================================================
# 2. GOOGLE GEMINI / ANTIGRAVITY OAUTH PKCE FLOW
# ==============================================================================
def start_google_oauth_flow(redirect_uri: str = "http://127.0.0.1:11434/v1/oauth/callback/google") -> dict:
    """
    Generates PKCE code challenge and OAuth 2.0 authorization URL for Google Gemini.
    """
    state = secrets.token_urlsafe(16)
    verifier = secrets.token_urlsafe(32)
    challenge = _base64url_encode(hashlib.sha256(verifier.encode('utf-8')).digest())

    _active_pkce_flows[state] = {
        "provider": "Google Gemini",
        "verifier": verifier,
        "redirect_uri": redirect_uri,
        "created_at": time.time()
    }

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/generative-language https://www.googleapis.com/auth/cloud-platform",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256"
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)

    return {
        "ok": True,
        "state": state,
        "auth_url": auth_url,
        "message": "Open the authorization URL in browser"
    }

def handle_google_oauth_callback(code: str, state: str) -> dict:
    """
    Exchanges authorization code for Google access and refresh tokens.
    """
    if state not in _active_pkce_flows:
        return {"ok": False, "error": "Invalid or expired OAuth state."}

    pkce_data = _active_pkce_flows.pop(state)
    verifier = pkce_data["verifier"]
    redirect_uri = pkce_data["redirect_uri"]

    payload = urllib.parse.urlencode({
        "client_id": GOOGLE_CLIENT_ID,
        "code": code,
        "code_verifier": verifier,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        return {"ok": False, "error": f"Failed to exchange Google OAuth code: {e}"}

    access_token = data.get("access_token")
    if not access_token:
        return {"ok": False, "error": "No access token returned by Google."}

    # Save Google Gemini provider
    add_or_update_provider({
        "name": "Google Gemini (OAuth)",
        "format": "openai",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "api_key": access_token,
        "default_model": "gemini-2.0-flash",
        "notes": "Connected via Google OAuth 2.0 PKCE",
        "default_temperature": 0.7,
        "default_max_tokens": 2048
    })

    return {
        "ok": True,
        "provider": "Google Gemini (OAuth)",
        "message": "Successfully connected Google Gemini via OAuth!"
    }


# ==============================================================================
# 3. CLAUDE CODE / ANTHROPIC AUTO-IMPORT CONNECTOR
# ==============================================================================
def import_claude_code_session() -> dict:
    """
    Auto-detects and imports existing Claude Code CLI auth tokens from user environment.
    """
    home = os.path.expanduser("~")
    possible_paths = [
        os.path.join(home, ".claude.json"),
        os.path.join(home, ".claude", "credentials.json"),
        os.path.join(home, ".config", "claude", "credentials.json")
    ]

    for p in possible_paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                    token = cdata.get("sessionKey") or cdata.get("apiKey") or cdata.get("token")
                    if token:
                        add_or_update_provider({
                            "name": "Anthropic (Claude Code)",
                            "format": "anthropic",
                            "base_url": "https://api.anthropic.com",
                            "api_key": token,
                            "default_model": "claude-3-7-sonnet-20250219",
                            "notes": f"Auto-imported from {p}",
                            "default_temperature": 0.7,
                            "default_max_tokens": 4096
                        })
                        return {"ok": True, "provider": "Anthropic (Claude Code)", "message": f"Successfully imported Claude Code credentials from {p}"}
            except Exception:
                continue

    env_key = os.environ.get("ANTHROPIC_API_KEY")
    if env_key:
        add_or_update_provider({
            "name": "Anthropic Claude",
            "format": "anthropic",
            "base_url": "https://api.anthropic.com",
            "api_key": env_key,
            "default_model": "claude-3-7-sonnet-20250219",
            "notes": "Auto-imported from ANTHROPIC_API_KEY environment variable",
            "default_temperature": 0.7,
            "default_max_tokens": 4096
        })
        return {"ok": True, "provider": "Anthropic Claude", "message": "Successfully imported from ANTHROPIC_API_KEY"}

    return {"ok": False, "error": "No existing Claude Code CLI session found on this machine."}


# ==============================================================================
# 4. STATUS & OAUTH FLOW INSPECTION
# ==============================================================================
def get_flow_status(flow_id: str) -> dict:
    if flow_id in _active_device_flows:
        flow = _active_device_flows[flow_id]
        return {
            "ok": True,
            "status": flow["status"],
            "provider": flow["provider"],
            "user_code": flow.get("user_code"),
            "verification_uri": flow.get("verification_uri"),
            "error": flow.get("error")
        }
    return {"ok": False, "error": "Flow ID not found or expired."}


# ==============================================================================
# 5. FRONTEND POLL ENDPOINT HELPER
# ==============================================================================
def poll_github_copilot(device_code: str) -> dict:
    """
    Called by the POST /v1/oauth/github-copilot/poll endpoint.
    Checks in-memory flow store for a completed token, or re-polls GitHub directly.
    """
    # First check our in-memory store
    for fid, flow in _active_device_flows.items():
        if flow.get("device_code") == device_code:
            if flow["status"] == "completed" and flow["token"]:
                return {"access_token": flow["token"]}
            elif flow["status"] == "error":
                return {"error": flow.get("error", "authorization_failed")}
            else:
                return {"error": "authorization_pending"}

    # If not found, poll GitHub directly (for cases where background thread missed it)
    poll_url = "https://github.com/login/oauth/access_token"
    data = urllib.parse.urlencode({
        "client_id": GITHUB_COPILOT_CLIENT_ID,
        "device_code": device_code,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
    }).encode("utf-8")
    req = urllib.request.Request(poll_url, data=data, headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            res_data = json.loads(resp.read().decode())
        if "access_token" in res_data:
            return {"access_token": res_data["access_token"]}
        return {"error": res_data.get("error", "authorization_pending")}
    except Exception as e:
        return {"error": str(e)}


# ==============================================================================
# 6. GOOGLE OAUTH CALLBACK HANDLER
# ==============================================================================
def handle_google_oauth_callback(code: str, state: str) -> dict:
    """
    Exchanges the auth code for an access token and saves the Google Gemini provider.
    """
    if not code:
        return {"ok": False, "error": "No authorization code received"}

    # Find PKCE verifier from state
    pkce = _active_pkce_flows.get(state)
    if not pkce:
        # If state not found (e.g., restart), just try with minimal params
        pkce = {"code_verifier": "", "redirect_uri": "http://localhost:8080/v1/oauth/google/callback"}

    redirect_uri = pkce.get("redirect_uri", "http://localhost:8080/v1/oauth/google/callback")
    token_data = urllib.parse.urlencode({
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "code_verifier": pkce.get("code_verifier", ""),
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }).encode("utf-8")

    token_req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=token_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    try:
        with urllib.request.urlopen(token_req, timeout=10) as resp:
            token_response = json.loads(resp.read().decode())
    except Exception as e:
        return {"ok": False, "error": f"Token exchange failed: {e}"}

    access_token = token_response.get("access_token")
    if not access_token:
        return {"ok": False, "error": token_response.get("error_description", "No access token")}

    add_or_update_provider({
        "name": "Google Gemini (OAuth)",
        "format": "openai",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "api_key": access_token,
        "default_model": "gemini-2.0-flash",
        "notes": f"Connected via Google OAuth 2.0 on {time.strftime('%Y-%m-%d')}",
        "default_temperature": 0.7,
        "default_max_tokens": 2048
    })

    # Clean up PKCE state
    _active_pkce_flows.pop(state, None)
    return {"ok": True, "provider": "Google Gemini (OAuth)", "message": "Google Gemini connected via OAuth!"}


# ==============================================================================
# 7. GOOGLE ANTIGRAVITY (AGY) OAUTH FLOW & SESSION MANAGER
# ==============================================================================
ANTIGRAVITY_CLIENT_ID = os.environ.get("ANTIGRAVITY_OAUTH_CLIENT_ID", "1071006060591-tmhssin2h21lcre235vtolojh4g403ep.apps.googleusercontent.com")
ANTIGRAVITY_CLIENT_SECRET = os.environ.get("ANTIGRAVITY_OAUTH_CLIENT_SECRET", "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")
ANTIGRAVITY_SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/cclog",
    "https://www.googleapis.com/auth/experimentsandconfigs",
]

def read_antigravity_token_from_credential_store() -> dict:
    """
    Read the Antigravity access + refresh token directly from Windows Credential Manager
    (target: 'gemini:antigravity'). Falls back gracefully on non-Windows platforms.
    Returns dict with 'access_token', 'refresh_token', 'token_type' or empty dict on failure.
    """
    try:
        import ctypes, ctypes.wintypes as wt
        CRED_TYPE_GENERIC = 1

        class _CRED_ATTR(ctypes.Structure):
            _fields_ = [('Keyword', wt.LPWSTR), ('Flags', wt.DWORD),
                        ('ValueSize', wt.DWORD), ('Value', ctypes.POINTER(wt.BYTE))]

        class _CREDENTIAL(ctypes.Structure):
            _fields_ = [
                ('Flags', wt.DWORD), ('Type', wt.DWORD), ('TargetName', wt.LPWSTR),
                ('Comment', wt.LPWSTR), ('LastWritten', wt.FILETIME),
                ('CredentialBlobSize', wt.DWORD), ('CredentialBlob', ctypes.POINTER(wt.BYTE)),
                ('Persist', wt.DWORD), ('AttributeCount', wt.DWORD),
                ('Attributes', ctypes.POINTER(_CRED_ATTR)),
                ('TargetAlias', wt.LPWSTR), ('UserName', wt.LPWSTR)
            ]

        advapi32 = ctypes.windll.advapi32
        target = "gemini:antigravity"
        pcred = ctypes.POINTER(_CREDENTIAL)()
        if not advapi32.CredReadW(target, CRED_TYPE_GENERIC, 0, ctypes.byref(pcred)):
            return {}
        cred = pcred.contents
        blob = bytes(cred.CredentialBlob[:cred.CredentialBlobSize])
        advapi32.CredFree(pcred)
        raw = json.loads(blob.decode("utf-8"))
        token_obj = raw.get("token", raw)  # Antigravity wraps in {"token": {...}}
        return {
            "access_token": token_obj.get("access_token", ""),
            "refresh_token": token_obj.get("refresh_token", ""),
            "token_type": token_obj.get("token_type", "Bearer"),
            "expiry": token_obj.get("expiry", ""),
            "auth_method": raw.get("auth_method", "consumer"),
        }
    except Exception:
        return {}

def auto_refresh_antigravity_token() -> str:
    """
    Full auto-refresh sequence for Antigravity:
    1. Read current token from Windows Credential Manager
    2. If refresh_token available, call Google token endpoint
    3. Update AIPI DB provider record with new access_token + refresh_token
    4. Return new access_token, or '' on failure
    """
    cred = read_antigravity_token_from_credential_store()
    refresh_token = cred.get("refresh_token", "")

    # Also check the DB for a stored refresh token as fallback
    if not refresh_token:
        try:
            from db import get_providers
            from vault import decrypt_key
            providers = get_providers()
            agy = next((p for p in providers if
                        "antigravity" in (p.get("name") or "").lower() or
                        (p.get("format") or "").lower() == "antigravity"), None)
            if agy:
                rt = agy.get("refresh_token", "")
                if rt and str(rt).startswith("enc:"):
                    rt = decrypt_key(rt)
                refresh_token = rt or ""
        except Exception:
            pass

    if not refresh_token:
        return ""

    new_token = refresh_antigravity_token(refresh_token)
    if new_token:
        # Persist new access token to DB
        try:
            from db import get_providers, add_or_update_provider
            providers = get_providers()
            agy = next((p for p in providers if
                        "antigravity" in (p.get("name") or "").lower() or
                        (p.get("format") or "").lower() == "antigravity"), None)
            if agy:
                agy["api_key"] = new_token
                if refresh_token and not agy.get("refresh_token"):
                    agy["refresh_token"] = refresh_token
                add_or_update_provider(agy)
        except Exception:
            pass
    return new_token or ""

def start_antigravity_oauth_flow(redirect_uri: str = "http://127.0.0.1:11434/v1/oauth/callback/antigravity") -> dict:
    """
    Initiates Google Antigravity OAuth 2.0 PKCE flow:
    Generates state and authorization URL for Google's Antigravity consumer client.
    """
    state = secrets.token_urlsafe(16)
    verifier = secrets.token_urlsafe(32)
    challenge = _base64url_encode(hashlib.sha256(verifier.encode('utf-8')).digest())

    _active_pkce_flows[state] = {
        "provider": "Antigravity",
        "verifier": verifier,
        "redirect_uri": redirect_uri,
        "created_at": time.time()
    }

    params = {
        "client_id": ANTIGRAVITY_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(ANTIGRAVITY_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256"
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)

    return {
        "ok": True,
        "state": state,
        "auth_url": auth_url,
        "message": "Open the Google Antigravity authorization page in browser"
    }

def handle_antigravity_oauth_callback(code: str, state: str = None, redirect_uri: str = None) -> dict:
    """
    Exchanges code for Google OAuth access + refresh tokens, discovers Project ID,
    and registers the native Antigravity provider in AIPI.
    """
    if not code:
        return {"ok": False, "error": "No authorization code received"}

    pkce = _active_pkce_flows.get(state) or {}
    red_uri = redirect_uri or pkce.get("redirect_uri") or "http://127.0.0.1:11434/v1/oauth/callback/antigravity"
    verifier = pkce.get("verifier", "")

    token_body = {
        "code": code,
        "client_id": ANTIGRAVITY_CLIENT_ID,
        "client_secret": ANTIGRAVITY_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "redirect_uri": red_uri
    }
    if verifier:
        token_body["code_verifier"] = verifier

    token_data = urllib.parse.urlencode(token_body).encode("utf-8")
    token_req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=token_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    try:
        with urllib.request.urlopen(token_req, timeout=12) as resp:
            token_response = json.loads(resp.read().decode())
    except Exception as e:
        return {"ok": False, "error": f"Antigravity token exchange failed: {e}"}

    access_token = token_response.get("access_token")
    refresh_token = token_response.get("refresh_token")
    if not access_token:
        return {"ok": False, "error": token_response.get("error_description", "No access token")}

    # Get User Info
    user_email = ""
    try:
        u_req = urllib.request.Request(
            "https://www.googleapis.com/oauth2/v1/userinfo?alt=json",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        with urllib.request.urlopen(u_req, timeout=8) as u_resp:
            u_data = json.loads(u_resp.read().decode())
            user_email = u_data.get("email", "")
    except Exception:
        pass

    # Discover Project ID via loadCodeAssist
    project_id = ""
    tier = "Google AI Pro"
    try:
        assist_req = urllib.request.Request(
            "https://cloudcode-pa.googleapis.com/v1internal:loadCodeAssist",
            data=json.dumps({
                "metadata": {
                    "ideType": "IDE_UNSPECIFIED",
                    "ideVersion": "1.107.0",
                    "pluginVersion": "1.107.0"
                }
            }).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "User-Agent": "antigravity/1.107.0 darwin/arm64"
            }
        )
        with urllib.request.urlopen(assist_req, timeout=10) as assist_resp:
            assist_data = json.loads(assist_resp.read().decode())
            p_obj = assist_data.get("cloudaicompanionProject")
            if isinstance(p_obj, dict):
                project_id = p_obj.get("id", "")
            elif isinstance(p_obj, str):
                project_id = p_obj
            tier = assist_data.get("currentTier", {}).get("name") or tier
    except Exception:
        pass

    # Save Antigravity Provider into DB
    provider_entry = {
        "name": "Antigravity",
        "format": "antigravity",
        "base_url": "https://cloudcode-pa.googleapis.com",
        "api_key": access_token,
        "default_model": "antigravity/claude-sonnet-4-6",
        "notes": f"Google Antigravity OAuth ({user_email or 'active account'}) | Project: {project_id or 'auto'}",
        "default_temperature": 0.7,
        "default_max_tokens": 4096,
        "refresh_token": refresh_token,
        "project_id": project_id,
        "email": user_email
    }
    add_or_update_provider(provider_entry)

    _active_pkce_flows.pop(state, None)
    return {
        "ok": True,
        "provider": "Antigravity",
        "email": user_email,
        "project_id": project_id,
        "message": f"Successfully connected Google Antigravity ({user_email or 'active account'}) directly to AIPI!"
    }

def refresh_antigravity_token(refresh_token: str) -> str:
    """Refresh an expired Google OAuth access token for Antigravity."""
    if not refresh_token:
        return None
    data = urllib.parse.urlencode({
        "client_id": ANTIGRAVITY_CLIENT_ID,
        "client_secret": ANTIGRAVITY_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            token_response = json.loads(resp.read().decode())
            new_access_token = token_response.get("access_token")
            return new_access_token
    except Exception:
        return None
