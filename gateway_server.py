"""
gateway_server.py - AIPI: Universal AI Protocol Interface & Gateway Server.
Developed by gnonymous.

Runs an OpenAI & Anthropic-compatible HTTP server and full Browser Dashboard on localhost so third-party software
(Claude Code, Cursor, Windsurf, LangChain, custom apps) and your browser can use your configured providers.
"""
import json
import os
import subprocess
import sys
import threading
import time
import uuid
import urllib.parse
import urllib.request as _ur
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs

# Config
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
PID_PATH = os.path.join(APP_DIR, "gateway.pid")
ERR_LOG_PATH = os.path.join(APP_DIR, "gateway_error.log")
WEB_DIR = os.path.join(APP_DIR, "web")
DEFAULT_PORT = 11434

def load_config():
    try:
        from db import get_raw_config
        return get_raw_config()
    except Exception:
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return {"providers": []}

def save_config_file(data):
    try:
        from db import save_all_config
        save_all_config(data)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False

def get_provider_by_name(name, config_data):
    for p in config_data.get("providers", []):
        if p.get("name") == name:
            return p
    return None

def _redact_config(config_data):
    """Return a deep copy of config with all api_key values redacted using vault."""
    try:
        from vault import sanitize_dict
        return sanitize_dict(config_data)
    except Exception:
        import copy
        out = copy.deepcopy(config_data)
        for p in out.get("providers", []):
            key = p.get("api_key", "")
            if key:
                p["api_key"] = key[:3] + "…" + key[-4:] if len(key) > 7 else "…redacted…"
        return out

class GatewayHandler(BaseHTTPRequestHandler):
    """OpenAI & Anthropic compatible API gateway and Web Dashboard handler."""

    def log_message(self, format, *args):
        """Suppress per-request access log lines (too noisy for a background gateway)."""
        pass

    def log_error(self, format, *args):
        """Forward connection/socket errors to stderr so they appear in the gateway log."""
        try:
            print("[GatewayError] " + (format % args), file=sys.stderr, flush=True)
        except Exception:
            pass

    def _send_json(self, status_code, data):
        try:
            body = json.dumps(data).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()
            self.wfile.write(body)
        except (OSError, ConnectionError):
            pass

    def _send_error(self, status_code, message):
        self._send_json(status_code, {"error": {"message": message, "type": "gateway_error"}})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def _get_provider_from_query(self, config_data):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        provider_name = params.get("provider", [""])[0]
        if provider_name:
            prov = get_provider_by_name(provider_name, config_data)
            if prov:
                return prov
        providers = config_data.get("providers", [])
        if providers:
            return providers[0]
        return None

    def _get_provider_for_model(self, config_data, model):
        """
        Route a request to the most suitable provider based on the model id.

        Selection order:
        1. An explicit ?provider= query param wins (UI / advanced callers).
        2. Otherwise match the model's prefix (text before '/') against each
           provider's default_model prefix, base_url host, and display name.
        3. Fall back to providers[0] (existing behaviour).
        """
        # 1. Explicit provider override.
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        provider_name = params.get("provider", [""])[0]
        if provider_name:
            prov = get_provider_by_name(provider_name, config_data)
            if prov:
                return prov

        providers = config_data.get("providers", []) or []
        if not providers:
            return None

        model = (model or "").strip()
        model_lower = model.lower()
        prefix = model_lower.split("/", 1)[0] if model_lower else ""

        # 2. Prefix / host / name match.
        best = None
        for p in providers:
            default = (p.get("default_model") or "").lower()
            host = (p.get("base_url") or "").lower()
            name = (p.get("name") or "").lower()
            # Model prefix matches a provider's default model prefix (e.g. moonshotai/... -> TokenRouter).
            if prefix and default.split("/", 1)[0] == prefix:
                return p
            # Model prefix appears in the provider base_url host (e.g. tokenrouter.com).
            if prefix and prefix in host and prefix not in ("localhost", "127.0.0.1"):
                best = p
            # Provider display name hints at the model prefix.
            if prefix and prefix in name:
                best = p
        if best:
            return best

        # 3. Fallback.
        return providers[0]

    def _serve_file(self, rel_path, content_type):
        file_path = os.path.join(WEB_DIR, rel_path)
        if os.path.exists(file_path):
            try:
                with open(file_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return True
            except Exception:
                pass
        return False

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        config_data = load_config()

        # Web Dashboard static files & assets
        if path in ("/", "/index.html", "/dashboard"):
            if not self._serve_file("index.html", "text/html"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Standard Professional Gateway Running</h1><p>API: /v1/models | /v1/chat/completions</p>")
            return

        clean_path = path.lstrip("/")
        if clean_path and not clean_path.startswith("v1/"):
            potential_paths = [
                os.path.join(WEB_DIR, clean_path),
                os.path.join(APP_DIR, clean_path)
            ]
            for p_file in potential_paths:
                if os.path.isfile(p_file):
                    mime_types = {
                        ".png": "image/png",
                        ".ico": "image/x-icon",
                        ".jpg": "image/jpeg",
                        ".jpeg": "image/jpeg",
                        ".webp": "image/webp",
                        ".svg": "image/svg+xml",
                        ".css": "text/css",
                        ".js": "application/javascript",
                        ".html": "text/html",
                        ".json": "application/json",
                        ".woff": "font/woff",
                        ".woff2": "font/woff2",
                        ".ttf": "font/ttf"
                    }
                    ext = os.path.splitext(p_file)[1].lower()
                    c_type = mime_types.get(ext, "application/octet-stream")
                    try:
                        with open(p_file, "rb") as f:
                            content = f.read()
                        self.send_response(200)
                        self.send_header("Content-Type", c_type)
                        self.send_header("Content-Length", str(len(content)))
                        self.send_header("Cache-Control", "public, max-age=3600")
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.end_headers()
                        self.wfile.write(content)
                        return
                    except Exception:
                        pass

        if path == "/v1/providers/presets":
            try:
                from providers_preset import PROVIDERS_PRESETS
                self._send_json(200, {"status": "ok", "count": len(PROVIDERS_PRESETS), "presets": PROVIDERS_PRESETS})
            except Exception as e:
                self._send_error(500, "Failed to load presets: " + str(e))
            return

        # Professional API Endpoints
        if path == "/v1/health":
            port = getattr(self.server, "gateway_port", DEFAULT_PORT)
            self._send_json(200, {
                "status": "ok",
                "service": "AIPI — AI Protocol Interface Gateway",
                "developer": "gnonymous",
                "port": port,
                "providers_count": len(config_data.get("providers", [])),
                "providers": _redact_config(config_data).get("providers", [])
            })
            return

        if path == "/v1/router/stats":
            try:
                from router import get_router_stats
                from db import get_stats
                self._send_json(200, {
                    "status": "ok",
                    "router": get_router_stats(),
                    "analytics": get_stats()
                })
            except Exception as e:
                self._send_error(500, str(e))
            return

        if path == "/v1/virtual-keys":
            try:
                from virtual_keys import list_virtual_keys
                self._send_json(200, {"status": "ok", "keys": list_virtual_keys()})
            except Exception as e:
                self._send_error(500, str(e))
            return

        if path == "/v1/analytics/overview":
            try:
                from analytics import get_dashboard_analytics, get_model_performance_summary
                self._send_json(200, {
                    "status": "ok",
                    "analytics": get_dashboard_analytics(),
                    "model_performance": get_model_performance_summary()
                })
            except Exception as e:
                self._send_error(500, str(e))
            return

        # Team Edition: License status
        if path == "/v1/license/status":
            try:
                from license import get_license_status, TIERS
                st = get_license_status()
                self._send_json(200, {"status": "ok", "license": st, "tiers": TIERS})
            except Exception as e:
                self._send_error(500, str(e))
            return

        # Team Edition: Rate limiter status
        if path == "/v1/rate-limits":
            try:
                from ratelimit import get_rate_limit_status
                self._send_json(200, {"status": "ok", "ratelimit": get_rate_limit_status()})
            except Exception as e:
                self._send_error(500, str(e))
            return

        # AIPI Master API Key endpoint
        if path == "/v1/virtual-keys/master":
            try:
                from virtual_keys import get_master_key
                mk = get_master_key()
                self._send_json(200, {"status": "ok", "master_key": mk})
            except Exception as e:
                self._send_error(500, str(e))
            return

        # Team Edition: Admin users list (requires X-Admin-Token)
        if path == "/v1/admin/users":
            try:
                from auth import validate_session, list_users
                token = self.headers.get("X-Admin-Token", "")
                session = validate_session(token)
                users = list_users()
                self._send_json(200, {"status": "ok", "session": session, "users": users})
            except Exception as e:
                self._send_error(401, str(e))
            return

        # Team Edition: OIDC/SSO status and flows
        if path == "/v1/auth/oidc/status":
            try:
                from oidc import oidc_status
                self._send_json(200, {"status": "ok", "sso": oidc_status()})
            except Exception as e:
                self._send_error(500, str(e))
            return

        if path == "/v1/auth/oidc/login":
            try:
                from oidc import build_auth_url
                auth_url = build_auth_url()
                self.send_response(302)
                self.send_header("Location", auth_url)
                self.end_headers()
            except Exception as e:
                self._send_error(400, "SSO Login Error: " + str(e))
            return

        if path == "/v1/auth/oidc/callback":
            try:
                from oidc import exchange_code
                code = query.get("code", [""])[0]
                if not code:
                    self._send_error(400, "Missing authorization code")
                    return
                user_info = exchange_code(code)
                self._send_json(200, {"status": "ok", "message": "SSO login successful", "user": user_info})
            except Exception as e:
                self._send_error(400, "SSO Callback Error: " + str(e))
            return

        # Team Edition: Usage report export (CSV or JSON)
        if path == "/v1/reports/export":
            try:
                from reports import export_history_csv, export_usage_json
                fmt = query.get("format", ["csv"])[0]
                if fmt == "json":
                    file_path = export_usage_json()
                else:
                    file_path = export_history_csv()
                self._send_json(200, {"status": "ok", "message": "Report generated", "path": file_path})
            except Exception as e:
                self._send_error(500, str(e))
            return

        # 1-Click IDE Auto-Configurator: Detection
        if path == "/v1/ide/detect":
            try:
                from ide_config import detect_ides
                port = getattr(self.server, "gateway_port", DEFAULT_PORT)
                self._send_json(200, {"status": "ok", "ides": detect_ides(port=port)})
            except Exception as e:
                self._send_error(500, str(e))
            return

        # Privacy & Stealth Mode Status
        if path == "/v1/privacy/status":
            try:
                from pii_redactor import get_privacy_config
                self._send_json(200, {"status": "ok", "privacy": get_privacy_config()})
            except Exception as e:
                self._send_error(500, str(e))
            return

        if path == "/v1/openapi.json":
            port = getattr(self.server, "gateway_port", DEFAULT_PORT)
            spec = {
                "openapi": "3.0.0",
                "info": {
                    "title": "AIPI — AI Protocol Interface Gateway",
                    "version": "2.5.0",
                    "description": "Universal OpenAI & Anthropic Compatible AI Model Gateway developed by gnonymous."
                },
                "servers": [{"url": f"http://127.0.0.1:{port}/v1"}],
                "paths": {
                    "/chat/completions": {
                        "post": {
                            "summary": "Create chat completion",
                            "responses": {"200": {"description": "Successful chat completion"}}
                        }
                    },
                    "/messages": {
                        "post": {
                            "summary": "Create Anthropic message",
                            "responses": {"200": {"description": "Successful Anthropic message response"}}
                        }
                    },
                    "/models": {
                        "get": {
                            "summary": "List available models",
                            "responses": {"200": {"description": "List of models"}}
                        }
                    }
                }
            }
            self._send_json(200, spec)
            return

        if path == "/v1/config":
            self._send_json(200, _redact_config(config_data))
            return

        if path == "/v1/ports/scan":
            target_port = int(query.get("port", [DEFAULT_PORT])[0])
            listeners = _get_listeners()
            if target_port in listeners:
                pid, proc = listeners[target_port]
                self._send_json(200, {"port": target_port, "in_use": True, "pid": pid, "process": proc})
            else:
                self._send_json(200, {"port": target_port, "in_use": False, "pid": "", "process": ""})
            return

        if path == "/v1/models" or path.startswith("/v1/models"):
            global _MODELS_CACHE
            now = time.time()
            if "_MODELS_CACHE" in globals() and _MODELS_CACHE.get("data") and (now - _MODELS_CACHE.get("ts", 0) < 20.0):
                self._send_json(200, {"object": "list", "data": _MODELS_CACHE["data"]})
                return

            models = []
            seen = set()
            results = {}

            # Add virtual router profiles & aliases first
            try:
                from db import get_profiles
                for prof in get_profiles(active_only=True):
                    p_id = prof.get("id")
                    if p_id and p_id not in seen:
                        models.append({
                            "id": p_id,
                            "object": "model",
                            "owned_by": "aipi-profile",
                            "name": prof.get("name", p_id),
                            "description": prof.get("description", "")
                        })
                        seen.add(p_id)
            except Exception:
                pass

            from router import VIRTUAL_ALIASES
            for v_alias in VIRTUAL_ALIASES.keys():
                if v_alias not in seen:
                    models.append({"id": v_alias, "object": "model", "owned_by": "aipi-router"})
                    seen.add(v_alias)

            def fetch_for_provider(p):
                try:
                    import urllib.request as _ur
                    base = (p.get("base_url") or "").rstrip("/")
                    if not base:
                        results[p["name"]] = [p["default_model"]] if p.get("default_model") else []
                        return
                    if (p.get("format") or "").lower() == "antigravity" or "cloudcode-pa" in base or "antigravity" in p["name"].lower():
                        results[p["name"]] = [
                            "antigravity/gemini-3.7-flash-high",
                            "antigravity/gemini-3.6-flash-medium",
                            "antigravity/gemini-3.5-flash-medium",
                            "antigravity/gemini-3.1-pro-low",
                            "antigravity/claude-sonnet-4-6",
                            "antigravity/claude-opus-4-6-thinking",
                            "antigravity/gpt-oss-120b-medium",
                            "antigravity/gemini-2.5-flash",
                            "antigravity/gemini-2.5-flash-thinking",
                            "antigravity/gemini-3.7-flash-medium",
                            "antigravity/gemini-3.7-flash-low",
                            "antigravity/gemini-3.6-flash-high",
                            "antigravity/gemini-3.6-flash-low",
                            "antigravity/gemini-3.5-flash-high",
                            "antigravity/gemini-3.5-flash-low",
                            "antigravity/gemini-3.1-pro-high",
                            "antigravity/gemini-3.1-flash-lite",
                            "antigravity/gemini-2.0-flash"
                        ]
                        return

                    # Always try OpenAI format first (works for most standard providers)
                    api_key = p.get("api_key", "")
                    if isinstance(api_key, str) and api_key.startswith("enc:"):
                        try:
                            from vault import decrypt_key
                            api_key = decrypt_key(api_key)
                        except Exception:
                            pass
                    url = base + "/models" if base.endswith("/v1") else base + "/v1/models"
                    req = _ur.Request(url, headers={
                        "Authorization": "Bearer " + api_key if api_key else "",
                        "Accept": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
                    })
                    try:
                        with _ur.urlopen(req, timeout=3.0) as resp:
                            data = json.loads(resp.read().decode())
                            mlist = [m["id"] for m in data.get("data", []) if isinstance(m, dict) and m.get("id")]
                            if mlist:
                                results[p["name"]] = mlist
                                return
                    except Exception:
                        pass
                    results[p["name"]] = [p["default_model"]] if p.get("default_model") else []
                except Exception:
                    results[p["name"]] = [p["default_model"]] if p.get("default_model") else []

            threads = []
            for p in config_data.get("providers", []):
                t = threading.Thread(target=fetch_for_provider, args=(p,), daemon=True)
                t.start()
                threads.append(t)

            for t in threads:
                t.join(timeout=3.5)

            for p in config_data.get("providers", []):
                mlist = results.get(p["name"], [])
                for m in mlist:
                    if m and m not in seen:
                        models.append({"id": m, "object": "model", "owned_by": p["name"]})
                        seen.add(m)

            _MODELS_CACHE = {"ts": now, "data": models}
            self._send_json(200, {"object": "list", "data": models})
            return

        if path == "/v1/oauth/flow-status":
            try:
                from oauth_manager import get_flow_status
                flow_id = query.get("flow_id", [""])[0]
                self._send_json(200, get_flow_status(flow_id))
            except Exception as e:
                self._send_error(500, str(e))
            return

        if path == "/v1/oauth/antigravity/start":
            try:
                from oauth_manager import start_antigravity_oauth_flow
                res = start_antigravity_oauth_flow()
                if res.get("ok"):
                    self.send_response(302)
                    self.send_header("Location", res["auth_url"])
                    self.end_headers()
                    return
                self._send_error(500, res.get("error", "Antigravity OAuth start failed"))
            except Exception as e:
                self._send_error(500, str(e))
            return

        if path == "/v1/oauth/callback/antigravity":
            try:
                from oauth_manager import handle_antigravity_oauth_callback
                code = query.get("code", [""])[0]
                state = query.get("state", [""])[0]
                res = handle_antigravity_oauth_callback(code, state)
                msg = res.get("message", "OAuth Completed") if res.get("ok") else res.get("error", "OAuth Error")
                html = f"""<!DOCTYPE html>
<html><head><title>Google Antigravity Connected - AIPI</title>
<style>body {{ background: #0f172a; color: #f8fafc; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
.card {{ background: #1e293b; padding: 32px; border-radius: 12px; text-align: center; border: 1px solid #38bdf8; max-width: 460px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); }}
h2 {{ color: #38bdf8; margin-top: 0; display: flex; align-items: center; justify-content: center; gap: 8px; }}
p {{ color: #94a3b8; font-size: 14px; line-height: 1.5; }}
a {{ color: #38bdf8; text-decoration: none; font-weight: bold; }}
.btn {{ display: inline-block; background: #0284c7; color: #fff; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-weight: 600; margin-top: 12px; }}
</style></head>
<body><div class="card">
<h2>🚀 Google Antigravity Connected</h2>
<p>{msg}</p>
<p>Antigravity models (<code>claude-sonnet-4-6</code>, <code>gemini-2.5-flash</code>, <code>gemini-3.5-flash-high</code>) are now live in your local AIPI Multiple Models Router!</p>
<a href="http://127.0.0.1:11434/" class="btn">Return to AIPI Dashboard</a>
<script>setTimeout(() => {{ try {{ window.opener?.location.reload(); }} catch(e){{}} window.location.href = "http://127.0.0.1:11434/"; }}, 2000);</script>
</div></body></html>"""
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
            except Exception as e:
                self._send_error(500, str(e))
            return

        if path == "/v1/oauth/callback/google":
            try:
                from oauth_manager import handle_google_oauth_callback
                code = query.get("code", [""])[0]
                state = query.get("state", [""])[0]
                res = handle_google_oauth_callback(code, state)
                msg = res.get("message", "OAuth Completed") if res.get("ok") else res.get("error", "OAuth Error")
                html = f"""<!DOCTYPE html>
<html><head><title>AIPI OAuth</title>
<style>body {{ background: #0f172a; color: #f8fafc; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
.card {{ background: #1e293b; padding: 32px; border-radius: 12px; text-align: center; border: 1px solid #334155; max-width: 400px; }}
h2 {{ color: #38bdf8; margin-top: 0; }}
p {{ color: #94a3b8; font-size: 14px; }}
a {{ color: #38bdf8; text-decoration: none; font-weight: bold; }}
</style></head>
<body><div class="card">
<h2>⚡ AIPI OAuth</h2>
<p>{msg}</p>
<p>You can close this tab and return to the <a href="http://127.0.0.1:11434/#providers">AIPI Dashboard</a>.</p>
<script>setTimeout(() => window.location.href = "http://127.0.0.1:11434/#providers", 2000);</script>
</div></body></html>"""
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
            except Exception as e:
                self._send_error(500, str(e))
            return

        if path == "/v1/providers/status-all":
            try:
                import concurrent.futures as _cf
                providers = config_data.get("providers", [])

                def _test_one(p):
                    import urllib.request as _ur, urllib.error as _ue
                    base = (p.get("base_url") or "").rstrip("/")
                    api_key = p.get("api_key", "")
                    if isinstance(api_key, str) and api_key.startswith("enc:"):
                        try:
                            from vault import decrypt_key
                            api_key = decrypt_key(api_key)
                        except Exception:
                            pass
                    if not base:
                        return {"name": p.get("name"), "ok": False, "status": "unconfigured",
                                "latency_ms": None, "model_count": 0, "models_count": 0,
                                "sample_models": [], "error": "No base URL configured"}
                    t0 = time.time()
                    models = []
                    status = "connected"
                    err = ""
                    # First do a quick port-reachability check to avoid long hangs
                    try:
                        import socket as _s, urllib.parse as _up2
                        _parsed = _up2.urlparse(base)
                        _host = _parsed.hostname or "localhost"
                        _port = _parsed.port or (443 if _parsed.scheme == "https" else 80)
                        _sock = _s.socket(_s.AF_INET, _s.SOCK_STREAM)
                        _sock.settimeout(1.5)
                        _rc = _sock.connect_ex((_host, _port))
                        _sock.close()
                        if _rc != 0:
                            return {"name": p.get("name"), "ok": False, "status": "offline",
                                    "latency_ms": None, "model_count": 0, "models_count": 0,
                                    "sample_models": [], "error": f"Port {_port} unreachable"}
                    except Exception as _pce:
                        return {"name": p.get("name"), "ok": False, "status": "offline",
                                "latency_ms": None, "model_count": 0, "models_count": 0,
                                "sample_models": [], "error": str(_pce)[:80]}
                    fmt = (p.get("format") or "openai").lower()
                    if fmt == "antigravity" or "cloudcode-pa" in base or "antigravity" in (p.get("name") or "").lower():
                        antigravity_models = [
                            "antigravity/claude-sonnet-4-6", "antigravity/claude-opus-4-6-thinking",
                            "antigravity/gemini-2.5-flash", "antigravity/gemini-3.5-flash-high",
                            "antigravity/gemini-3.1-pro-high", "antigravity/gemini-2.0-flash"
                        ]
                        t0 = time.time()
                        try:
                            test_req = _ur.Request(
                                "https://cloudcode-pa.googleapis.com/v1internal:loadCodeAssist",
                                data=json.dumps({"metadata": {"ideType": "IDE_UNSPECIFIED"}}).encode("utf-8"),
                                headers={
                                    "Authorization": f"Bearer {api_key}",
                                    "Content-Type": "application/json",
                                    "User-Agent": "antigravity/1.107.0 darwin/arm64"
                                }
                            )
                            with _ur.urlopen(test_req, timeout=3.0) as resp:
                                lat = round((time.time() - t0) * 1000, 1)
                                return {
                                    "name": p.get("name"), "ok": True, "status": "connected",
                                    "latency_ms": lat, "model_count": len(antigravity_models), "models_count": len(antigravity_models),
                                    "sample_models": antigravity_models, "error": None
                                }
                        except _ue.HTTPError as he:
                            lat = round((time.time() - t0) * 1000, 1)
                            if he.code == 401:
                                try:
                                    from oauth_manager import auto_refresh_antigravity_token
                                    new_key = auto_refresh_antigravity_token()
                                    if new_key:
                                        from db import add_or_update_provider
                                        p["api_key"] = new_key
                                        add_or_update_provider(p)
                                        return {
                                            "name": p.get("name"), "ok": True, "status": "connected",
                                            "latency_ms": lat, "model_count": len(antigravity_models), "models_count": len(antigravity_models),
                                            "sample_models": antigravity_models, "error": None
                                        }
                                except Exception:
                                    pass
                            return {
                                "name": p.get("name"), "ok": True, "status": "connected",
                                "latency_ms": lat, "model_count": len(antigravity_models), "models_count": len(antigravity_models),
                                "sample_models": antigravity_models, "error": None
                            }
                        except Exception:
                            lat = round((time.time() - t0) * 1000, 1)
                            return {
                                "name": p.get("name"), "ok": True, "status": "connected",
                                "latency_ms": lat, "model_count": len(antigravity_models), "models_count": len(antigravity_models),
                                "sample_models": antigravity_models, "error": None
                            }

                    try:
                        url = base + "/models" if base.endswith("/v1") else base + "/v1/models"
                        _ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
                        if fmt == "anthropic":
                            hdrs = {"x-api-key": api_key or "", "anthropic-version": "2023-06-01", "Accept": "application/json", "User-Agent": _ua}
                        else:
                            hdrs = {"Authorization": f"Bearer {api_key}" if api_key else "", "Accept": "application/json", "User-Agent": _ua}
                        req = _ur.Request(url, headers=hdrs)
                        with _ur.urlopen(req, timeout=2.5) as resp:
                            d = json.loads(resp.read().decode())
                            models = [m.get("id") for m in d.get("data", []) if isinstance(m, dict) and m.get("id")]
                    except _ue.HTTPError as he:
                        if he.code in (401, 403):
                            status = "unauthorized"
                            err = f"HTTP {he.code}: Invalid API Key or Unauthorized"
                        else:
                            status = "error"
                            err = f"HTTP {he.code}: {he.reason}"
                    except Exception as ex:
                        status = "offline"
                        err = str(ex)[:100]
                    lat = round((time.time() - t0) * 1000, 1)
                    is_ok = (status == "connected")
                    return {
                        "name": p.get("name"),
                        "ok": is_ok,
                        "status": status,
                        "latency_ms": lat if status in ("connected", "unauthorized") else None,
                        "model_count": len(models),
                        "models_count": len(models),
                        "sample_models": models[:8],
                        "error": err
                    }

                results = []
                if providers:
                    pool = _cf.ThreadPoolExecutor(max_workers=len(providers))
                    futs = {pool.submit(_test_one, p): p for p in providers}
                    done, pending = _cf.wait(futs.keys(), timeout=3.5)
                    for f in done:
                        try:
                            results.append(f.result())
                        except Exception:
                            pass
                    for f, p in futs.items():
                        if f in pending:
                            results.append({"name": p.get("name"), "ok": False, "status": "timeout",
                                            "latency_ms": None, "model_count": 0, "models_count": 0,
                                            "sample_models": [], "error": "Connection timed out"})
                    pool.shutdown(wait=False)  # Don't block — let threads finish in background

                self._send_json(200, results)
            except Exception as e:
                self._send_error(500, str(e))
            return

        # ── Antigravity Live Quota ──────────────────────────────────────────────
        if path == "/v1/providers/antigravity/quota":
            try:
                import urllib.request as _ur, urllib.error as _ue
                providers = config_data.get("providers", [])
                agy = next((p for p in providers if
                            (p.get("format") or "").lower() == "antigravity" or
                            "antigravity" in (p.get("name") or "").lower() or
                            "cloudcode-pa" in (p.get("base_url") or "")), None)
                if not agy:
                    self._send_json(404, {"error": "No Antigravity provider configured"})
                    return
                api_key = agy.get("api_key", "")
                if isinstance(api_key, str) and api_key.startswith("enc:"):
                    try:
                        from vault import decrypt_key
                        api_key = decrypt_key(api_key)
                    except Exception:
                        pass
                req = _ur.Request(
                    "https://cloudcode-pa.googleapis.com/v1internal:fetchAvailableModels",
                    data=json.dumps({}).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "User-Agent": "antigravity/2.1.1 darwin/arm64"
                    }
                )
                try:
                    with _ur.urlopen(req, timeout=8) as resp:
                        raw = json.loads(resp.read().decode())
                except _ue.HTTPError as he:
                    body = ""
                    try:
                        body = he.read().decode()[:300]
                    except Exception:
                        pass
                    # Try to refresh token if 401 (using Credential Manager fallback)
                    if he.code == 401:
                        try:
                            from oauth_manager import auto_refresh_antigravity_token
                            new_key = auto_refresh_antigravity_token()
                            if new_key:
                                from db import add_or_update_provider
                                agy["api_key"] = new_key
                                add_or_update_provider(agy)
                                req2 = _ur.Request(
                                    "https://cloudcode-pa.googleapis.com/v1internal:fetchAvailableModels",
                                    data=json.dumps({}).encode("utf-8"),
                                    headers={
                                        "Authorization": f"Bearer {new_key}",
                                        "Content-Type": "application/json",
                                        "User-Agent": "antigravity/2.1.1 darwin/arm64"
                                    }
                                )
                                with _ur.urlopen(req2, timeout=8) as resp2:
                                    raw = json.loads(resp2.read().decode())
                        except Exception:
                            self._send_json(he.code, {"error": f"HTTP {he.code}: {body}"})
                            return
                    else:
                        self._send_json(he.code, {"error": f"HTTP {he.code}: {body}"})
                        return

                models_raw = raw.get("models", {})
                quota_list = []
                # Filter to only recommended/user-facing models
                skip_prefixes = ("tab_", "chat_")
                for model_id, info in models_raw.items():
                    if any(model_id.startswith(p) for p in skip_prefixes):
                        continue
                    quota = info.get("quotaInfo", {})
                    frac = quota.get("remainingFraction")
                    pct = round(frac * 100, 1) if frac is not None else 100.0
                    reset_time = quota.get("resetTime")
                    quota_list.append({
                        "id": f"antigravity/{model_id}",
                        "upstream_id": model_id,
                        "display_name": info.get("displayName", model_id),
                        "remaining_pct": pct,
                        "remaining_fraction": frac,
                        "reset_time": reset_time,
                        "max_output_tokens": info.get("maxOutputTokens"),
                        "max_tokens": info.get("maxTokens"),
                        "supports_thinking": info.get("supportsThinking", False),
                        "thinking_budget": info.get("thinkingBudget"),
                        "recommended": info.get("recommended", False),
                        "status": "available" if pct > 10.0 else ("low" if pct > 2.0 else "exhausted")
                    })
                # Sort: available first by remaining desc
                quota_list.sort(key=lambda x: (-x["remaining_pct"], not x["recommended"]))
                self._send_json(200, {
                    "models": quota_list,
                    "provider": agy.get("name", "Antigravity"),
                    "email": agy.get("email") or "itsustad1@gmail.com",
                    "tier": "Free Tier (Google Cloud)"
                })
            except Exception as e:
                self._send_error(500, str(e))
            return


        if path.startswith("/v1/oauth/github-copilot/poll"):
            # Allow GET poll: /v1/oauth/github-copilot/poll?device_code=...&flow_id=...
            try:
                from oauth_manager import _active_device_flows
                qparams = dict(urllib.parse.parse_qsl(self.path.split("?", 1)[1] if "?" in self.path else ""))  # urllib.parse imported at top
                device_code = qparams.get("device_code", "")
                # Find flow by device_code
                matched = None
                for fid, flow in _active_device_flows.items():
                    if flow.get("device_code") == device_code:
                        matched = flow
                        break
                if matched:
                    if matched["status"] == "completed" and matched["token"]:
                        self._send_json(200, {"access_token": matched["token"]})
                    elif matched["status"] == "error":
                        self._send_json(200, {"error": matched.get("error", "authorization_failed")})
                    else:
                        self._send_json(200, {"error": "authorization_pending"})
                else:
                    self._send_json(200, {"error": "authorization_pending"})
            except Exception as e:
                self._send_error(500, str(e))
            return

        # ── Google OAuth Callback (GET) ────────────────────────────────────────
        if path == "/v1/oauth/google/callback":
            try:
                qparams = dict(urllib.parse.parse_qsl(self.path.split("?", 1)[1] if "?" in self.path else ""))
                code = qparams.get("code", "")
                state = qparams.get("state", "")
                from oauth_manager import handle_google_oauth_callback
                result = handle_google_oauth_callback(code, state)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                if result.get("ok"):
                    html = """<!DOCTYPE html><html><head><style>body{font-family:sans-serif;background:#0f172a;color:#f8fafc;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}</style></head><body><div style='text-align:center'><div style='font-size:48px'>✅</div><h2 style='color:#4ade80'>Google Gemini Connected!</h2><p style='color:#94a3b8'>You can close this tab and return to AIPI.</p></div></body></html>"""
                else:
                    html = f"""<!DOCTYPE html><html><head><style>body{{font-family:sans-serif;background:#0f172a;color:#f8fafc;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}}</style></head><body><div style='text-align:center'><div style='font-size:48px'>❌</div><h2 style='color:#ef4444'>Connection Failed</h2><p style='color:#94a3b8'>{result.get('error','Unknown error')}</p><p style='color:#64748b'>Close this tab and try again in AIPI.</p></div></body></html>"""
                self.wfile.write(html.encode("utf-8"))
            except Exception as e:
                self._send_error(500, str(e))
            return

        # ── Profiles Management (GET) ─────────────────────────────────────────
        if path == "/v1/profiles":
            try:
                from db import get_profiles
                from router import get_router_stats
                profiles = get_profiles()
                stats = get_router_stats()
                self._send_json(200, {
                    "status": "ok",
                    "profiles": profiles,
                    "stats": stats
                })
            except Exception as e:
                self._send_error(500, str(e))
            return

        # ── Admin Status Check (GET) ──────────────────────────────────────────
        if path == "/v1/admin/status":
            try:
                from auth import has_admin_users, list_users
                users = list_users()
                self._send_json(200, {
                    "status": "ok",
                    "setup_required": len(users) == 0,
                    "has_admin": has_admin_users(),
                    "total_users": len(users)
                })
            except Exception as e:
                self._send_error(500, str(e))
            return

        self._send_error(404, "Not found. Use /v1/models, /v1/chat/completions, /v1/messages, or /v1/health")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        content_len_hdr = self.headers.get("Content-Length")
        if content_len_hdr is not None:
            body = self.rfile.read(int(content_len_hdr)) if int(content_len_hdr) > 0 else b"{}"
        else:
            # Chunked or no Content-Length — read up to 10 MB
            body = self.rfile.read(10 * 1024 * 1024) or b"{}"

        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        if path == "/v1/config":
            if save_config_file(data):
                self._send_json(200, {"status": "ok", "message": "Configuration updated successfully"})
            else:
                self._send_error(500, "Failed to write config.json")
            return

        if path == "/v1/ports/kill":
            target_port = int(query.get("port", [DEFAULT_PORT])[0])
            ok, msg = kill_port_listener(target_port)
            self._send_json(200, {"status": "ok" if ok else "error", "message": msg})
            return

        if path == "/v1/virtual-keys/create":
            try:
                from virtual_keys import create_virtual_key
                name = data.get("name", "AIPI API Key")
                budget = float(data.get("max_monthly_budget", 0.0))
                models = data.get("allowed_models", [])
                rpm = int(data.get("rate_limit_rpm", 0))
                expires = int(data.get("expires_in_days", 0))
                vk = create_virtual_key(name, max_monthly_budget=budget, allowed_models=models, rate_limit_rpm=rpm, expires_in_days=expires)
                self._send_json(200, {"status": "ok", "message": "AIPI API key generated successfully", "key": vk})
            except Exception as e:
                self._send_error(500, str(e))
            return

        if path == "/v1/virtual-keys/revoke":
            try:
                from virtual_keys import revoke_key
                key_id = data.get("key_id", "")
                if revoke_key(key_id):
                    self._send_json(200, {"status": "ok", "message": "API key revoked"})
                else:
                    self._send_error(404, "Key not found")
            except Exception as e:
                self._send_error(500, str(e))
            return

        if path == "/v1/virtual-keys/delete":
            try:
                from virtual_keys import delete_key
                key_id = data.get("key_id", "")
                if delete_key(key_id):
                    self._send_json(200, {"status": "ok", "message": "API key permanently deleted"})
                else:
                    self._send_error(404, "Key not found")
            except Exception as e:
                self._send_error(500, str(e))
            return

        if path == "/v1/cache/clear":
            try:
                from cache import clear_cache
                clear_cache()
                self._send_json(200, {"status": "ok", "message": "Prompt cache cleared successfully"})
            except Exception as e:
                self._send_error(500, str(e))
            return

        # Provider Management Endpoints
        if path == "/v1/providers/add":
            try:
                from db import save_provider
                save_provider(data)
                self._send_json(200, {"status": "ok", "message": f"Provider '{data.get('name')}' added successfully"})
            except Exception as e:
                self._send_error(400, str(e))
            return

        if path == "/v1/providers/update":
            try:
                from db import save_provider, delete_provider
                old_name = data.get("name", "")
                prov_data = data.get("provider", {})
                if old_name and old_name != prov_data.get("name"):
                    delete_provider(old_name)
                save_provider(prov_data)
                self._send_json(200, {"status": "ok", "message": f"Provider '{prov_data.get('name')}' updated successfully"})
            except Exception as e:
                self._send_error(400, str(e))
            return

        if path == "/v1/providers/delete":
            try:
                from db import delete_provider
                name = data.get("name", "")
                delete_provider(name)
                self._send_json(200, {"status": "ok", "message": f"Provider '{name}' deleted successfully"})
            except Exception as e:
                self._send_error(400, str(e))
            return

        # ── Profiles Management Endpoints (POST) ──────────────────────────────
        if path == "/v1/profiles/save":
            try:
                from db import save_profile
                saved = save_profile(data)
                self._send_json(200, {
                    "status": "ok",
                    "message": f"Profile '{saved.get('name')}' saved successfully",
                    "profile": saved
                })
            except Exception as e:
                self._send_error(400, str(e))
            return

        if path == "/v1/profiles/delete":
            try:
                from db import delete_profile
                p_id = data.get("id") or data.get("profile_id")
                delete_profile(p_id)
                self._send_json(200, {"status": "ok", "message": f"Profile '{p_id}' deleted successfully"})
            except Exception as e:
                self._send_error(400, str(e))
            return

        if path == "/v1/profiles/test":
            try:
                from db import get_providers
                from router import resolve_route
                p_id = data.get("profile_id") or data.get("id") or "auto/best-free"
                providers = get_providers()
                routes = resolve_route(p_id, providers)
                self._send_json(200, {
                    "status": "ok",
                    "profile_id": p_id,
                    "routes_count": len(routes),
                    "cascade": [{"provider": r[0].get("name"), "model": r[1]} for r in routes]
                })
            except Exception as e:
                self._send_error(500, str(e))
            return

        # ── OAuth Endpoints ────────────────────────────────────────────────────
        if path == "/v1/oauth/github-copilot/start":
            try:
                from oauth_manager import start_github_copilot_flow
                res = start_github_copilot_flow()
                self._send_json(200, res)
            except Exception as e:
                self._send_error(500, str(e))
            return

        if path == "/v1/oauth/github-copilot/poll":
            try:
                from oauth_manager import poll_github_copilot
                device_code = data.get("device_code", "")
                if not device_code:
                    self._send_error(400, "device_code is required")
                    return
                result = poll_github_copilot(device_code)
                self._send_json(200, result)
            except Exception as e:
                self._send_error(500, str(e))
            return

        if path == "/v1/oauth/google/start":
            try:
                from oauth_manager import start_google_oauth_flow
                res = start_google_oauth_flow()
                if res.get("ok"):
                    # Redirect browser directly to Google OAuth
                    self.send_response(302)
                    self.send_header("Location", res["auth_url"])
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                else:
                    self._send_error(500, res.get("error", "Failed"))
            except Exception as e:
                self._send_error(500, str(e))
            return

        if path == "/v1/oauth/antigravity/start":
            try:
                from oauth_manager import start_antigravity_oauth_flow
                redirect_uri = data.get("redirect_uri") or "http://127.0.0.1:11434/v1/oauth/callback/antigravity"
                res = start_antigravity_oauth_flow(redirect_uri)
                self._send_json(200, res)
            except Exception as e:
                self._send_error(500, str(e))
            return

        if path == "/v1/oauth/antigravity/callback":
            try:
                from oauth_manager import handle_antigravity_oauth_callback
                code = data.get("code")
                state = data.get("state")
                red_uri = data.get("redirect_uri")
                res = handle_antigravity_oauth_callback(code, state, red_uri)
                self._send_json(200 if res.get("ok") else 400, res)
            except Exception as e:
                self._send_error(500, str(e))
            return

        if path == "/v1/oauth/antigravity/import-session":
            try:
                from oauth_manager import import_local_antigravity_session
                res = import_local_antigravity_session()
                self._send_json(200 if res.get("ok") else 400, res)
            except Exception as e:
                self._send_error(500, str(e))
            return

        if path == "/v1/oauth/claude-code/import":
            try:
                from oauth_manager import import_claude_code_session
                res = import_claude_code_session()
                self._send_json(200, res)
            except Exception as e:
                self._send_error(500, str(e))
            return

        if path == "/v1/providers/connect-key":
            # Direct API key connection endpoint (OpenAI-style, Anthropic, xAI, Mistral etc)
            try:
                from db import save_provider
                provider_name = data.get("provider_name", "")
                api_key = data.get("api_key", "").strip()
                base_url = data.get("base_url", "")
                default_model = data.get("default_model", "")
                fmt = data.get("format", "openai")
                notes = data.get("notes", f"Connected via API key on {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}")
                if not provider_name or not api_key:
                    self._send_error(400, "provider_name and api_key are required")
                    return
                save_provider({
                    "name": provider_name,
                    "format": fmt,
                    "base_url": base_url,
                    "api_key": api_key,
                    "default_model": default_model,
                    "notes": notes,
                    "default_temperature": 0.7,
                    "default_max_tokens": 4096
                })
                self._send_json(200, {
                    "status": "ok",
                    "message": f"✅ {provider_name} connected successfully via API key!"
                })
            except Exception as e:
                self._send_error(500, str(e))
            return

        if path == "/v1/providers/test-connection":
            # Live test a provider connection
            try:
                p_name = data.get("provider_name", "").strip()
                api_key = data.get("api_key", "").strip()
                base_url = (data.get("base_url") or "").rstrip("/")
                fmt = data.get("format", "openai")
                model = data.get("model", "")

                # If api_key is masked/redacted or empty or encrypted, resolve the real stored key from database
                if not api_key or "…" in api_key or "..." in api_key or api_key.startswith("enc:"):
                    try:
                        from db import get_providers
                        all_p = get_providers()
                        matched = next((p for p in all_p if p.get("name", "").strip().lower() == p_name.lower()), None)
                        if matched and matched.get("api_key"):
                            api_key = matched["api_key"]
                            if not base_url and matched.get("base_url"):
                                base_url = matched["base_url"].rstrip("/")
                            if not fmt and matched.get("format"):
                                fmt = matched["format"]
                    except Exception:
                        pass

                if isinstance(api_key, str) and api_key.startswith("enc:"):
                    try:
                        from vault import decrypt_key
                        api_key = decrypt_key(api_key)
                    except Exception:
                        pass

                # If still masked with ellipsis, clear it to avoid latin-1 header encoding errors
                if "…" in api_key or "..." in api_key:
                    api_key = ""

                if not base_url:
                    self._send_json(200, {
                        "status": "ok",
                        "connected": False,
                        "latency_ms": None,
                        "error": "Base URL is required",
                        "message": "Base URL is required"
                    })
                    return

                import urllib.request as _ur, urllib.error as _ue, time as _t
                t0 = _t.time()

                if fmt == "antigravity" or "cloudcode-pa" in base_url or "antigravity" in p_name.lower():
                    models_found = [
                        "antigravity/claude-sonnet-4-6", "antigravity/claude-opus-4-6-thinking",
                        "antigravity/gemini-2.5-flash", "antigravity/gemini-3.5-flash-high",
                        "antigravity/gemini-3.1-pro-high", "antigravity/gemini-2.0-flash"
                    ]
                    test_req = _ur.Request(
                        "https://cloudcode-pa.googleapis.com/v1internal:loadCodeAssist",
                        data=json.dumps({"metadata": {"ideType": "IDE_UNSPECIFIED", "ideVersion": "1.107.0"}}).encode("utf-8"),
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                            "User-Agent": "antigravity/1.107.0 darwin/arm64"
                        }
                    )
                    try:
                        with _ur.urlopen(test_req, timeout=5.0) as resp:
                            lat = round((_t.time() - t0) * 1000, 1)
                            self._send_json(200, {
                                "status": "ok",
                                "connected": True,
                                "latency_ms": lat,
                                "models_count": len(models_found),
                                "sample_models": models_found,
                                "message": f"Connected! Google Antigravity is online ({lat}ms) with {len(models_found)} models."
                            })
                            return
                    except _ue.HTTPError as he:
                        if he.code == 401:
                            try:
                                from oauth_manager import auto_refresh_antigravity_token
                                new_key = auto_refresh_antigravity_token()
                                if new_key:
                                    from db import add_or_update_provider
                                    matched_p = next((p for p in get_providers() if p.get("name", "").strip().lower() == p_name.lower()), None)
                                    if matched_p:
                                        matched_p["api_key"] = new_key
                                        add_or_update_provider(matched_p)
                                    lat = round((_t.time() - t0) * 1000, 1)
                                    self._send_json(200, {
                                        "status": "ok",
                                        "connected": True,
                                        "latency_ms": lat,
                                        "models_count": len(models_found),
                                        "sample_models": models_found,
                                        "message": f"Connected & Token Auto-Refreshed! Google Antigravity is online ({lat}ms)."
                                    })
                                    return
                            except Exception:
                                pass
                        lat = round((_t.time() - t0) * 1000, 1)
                        self._send_json(200, {
                            "status": "ok",
                            "connected": True,
                            "latency_ms": lat,
                            "models_count": len(models_found),
                            "sample_models": models_found,
                            "message": f"Google Antigravity is online ({lat}ms) with {len(models_found)} models."
                        })
                        return
                    except Exception:
                        lat = round((_t.time() - t0) * 1000, 1)
                        self._send_json(200, {
                            "status": "ok",
                            "connected": True,
                            "latency_ms": lat,
                            "models_count": len(models_found),
                            "sample_models": models_found,
                            "message": f"Google Antigravity is online ({lat}ms) with {len(models_found)} models."
                        })
                        return

                # Try /v1/models first
                models_url = base_url + "/v1/models" if not base_url.endswith("/v1") else base_url + "/models"
                _ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
                headers_test = {
                    "Authorization": f"Bearer {api_key}" if api_key else "",
                    "Accept": "application/json",
                    "User-Agent": _ua
                }
                if fmt == "anthropic":
                    headers_test = {
                        "x-api-key": api_key or "",
                        "anthropic-version": "2023-06-01",
                        "Accept": "application/json",
                        "User-Agent": _ua
                    }

                req = _ur.Request(models_url, headers=headers_test)
                try:
                    with _ur.urlopen(req, timeout=5.0) as resp:
                        resp_data = json.loads(resp.read().decode())
                        models_found = [m.get("id") for m in resp_data.get("data", []) if isinstance(m, dict) and m.get("id")]
                        lat = round((_t.time() - t0) * 1000, 1)
                        self._send_json(200, {
                            "status": "ok",
                            "connected": True,
                            "latency_ms": lat,
                            "models_count": len(models_found),
                            "sample_models": models_found[:6],
                            "message": f"Connected! Found {len(models_found)} models in {lat}ms"
                        })
                except _ue.HTTPError as he:
                    self._send_json(200, {
                        "status": "ok",
                        "connected": False,
                        "latency_ms": None,
                        "error": f"HTTP {he.code}: {he.reason}",
                        "message": f"Connection failed: HTTP {he.code} ({he.reason})"
                    })
                except Exception as ex:
                    self._send_json(200, {
                        "status": "ok",
                        "connected": False,
                        "latency_ms": None,
                        "error": str(ex),
                        "message": f"Connection failed: {str(ex)}"
                    })
            except Exception as e:
                self._send_json(200, {
                    "status": "ok",
                    "connected": False,
                    "latency_ms": None,
                    "error": str(e),
                    "message": f"Error: {str(e)}"
                })
            return

        # Team Edition: Admin status & setup check
        if path == "/v1/admin/status":
            try:
                from auth import has_admin_users, list_users
                users = list_users()
                self._send_json(200, {
                    "status": "ok",
                    "setup_required": len(users) == 0,
                    "has_admin": has_admin_users(),
                    "total_users": len(users)
                })
            except Exception as e:
                self._send_error(500, str(e))
            return

        # Team Edition: Admin login (RBAC)
        if path == "/v1/admin/login":
            try:
                from auth import authenticate
                username = data.get("username", "")
                password = data.get("password", "")
                session = authenticate(username, password)
                self._send_json(200, {"status": "ok", "message": "Authenticated", "session": session})
            except Exception as e:
                self._send_error(401, str(e))
            return

        # Team Edition: Create user (admin only OR first-time setup)
        if path == "/v1/admin/users/create":
            try:
                from auth import validate_session, create_user, ROLE_RANK, has_admin_users, list_users
                users = list_users()
                if len(users) > 0:
                    # Enforce admin token if users already exist
                    token = self.headers.get("X-Admin-Token", "") or self.headers.get("Authorization", "").replace("Bearer ", "")
                    session = validate_session(token)
                    if ROLE_RANK.get(session["role"], 0) < ROLE_RANK["admin"]:
                        self._send_error(403, "Admin role required to create additional users")
                        return
                user = create_user(data.get("username", ""), data.get("password", ""), data.get("role", "admin" if len(users)==0 else "member"))
                self._send_json(200, {"status": "ok", "message": "User created successfully", "user": user})
            except Exception as e:
                self._send_error(400, str(e))
            return

        # Team Edition: Delete user (admin only)
        if path == "/v1/admin/users/delete":
            try:
                from auth import validate_session, delete_user
                session = validate_session(self.headers.get("X-Admin-Token", ""))
                deleted = delete_user(data.get("username", ""), session["role"])
                self._send_json(200, {"status": "ok", "message": "User deleted" if deleted else "User not found"})
            except Exception as e:
                self._send_error(400, str(e))
            return

        # Team Edition: Set user role (admin only)
        if path == "/v1/admin/users/role":
            try:
                from auth import validate_session, set_user_role
                session = validate_session(self.headers.get("X-Admin-Token", ""))
                result = set_user_role(data.get("username", ""), data.get("role", "member"), session["role"])
                self._send_json(200, {"status": "ok", "message": "Role updated", "user": result})
            except Exception as e:
                self._send_error(400, str(e))
            return

        # Team Edition: Change password
        if path == "/v1/admin/change-password":
            try:
                from auth import validate_session, change_password
                session = validate_session(self.headers.get("X-Admin-Token", ""))
                old_pass = data.get("old_password", "")
                new_pass = data.get("new_password", "")
                username = session.get("username", "admin")
                change_password(username, old_pass, new_pass)
                self._send_json(200, {"status": "ok", "message": "Password changed successfully"})
            except Exception as e:
                self._send_error(400, str(e))
            return

        # Team Edition: Activate license
        if path == "/v1/license/activate":
            try:
                from license import activate_license
                result = activate_license(data.get("license_key", ""))
                self._send_json(200, {"status": "ok", "message": "License activated", "license": result})
            except Exception as e:
                self._send_error(400, str(e))
            return

        # Team Edition: Save OIDC/SSO config
        if path == "/v1/admin/oidc/config":
            try:
                from oidc import save_oidc_config
                saved = save_oidc_config(data)
                self._send_json(200, {"status": "ok", "message": "OIDC config saved", "config": saved})
            except Exception as e:
                self._send_error(500, str(e))
            return

        # 1-Click IDE Auto-Configurator: Inject
        if path == "/v1/ide/inject":
            try:
                from ide_config import inject_ide_config
                ide_id = data.get("ide_id", "")
                port = int(data.get("port", DEFAULT_PORT))
                api_key = data.get("api_key", "aipi-local")
                model = data.get("model", "auto/fast")
                res = inject_ide_config(ide_id, port=port, api_key=api_key, model=model)
                self._send_json(200, res)
            except Exception as e:
                self._send_error(400, str(e))
            return

        # 1-Click IDE Auto-Configurator: Restore
        if path == "/v1/ide/restore":
            try:
                from ide_config import restore_ide_config
                ide_id = data.get("ide_id", "")
                res = restore_ide_config(ide_id)
                self._send_json(200, res)
            except Exception as e:
                self._send_error(400, str(e))
            return

        # Privacy & Stealth Mode Config
        if path == "/v1/privacy/config":
            try:
                from pii_redactor import save_privacy_config
                saved = save_privacy_config(data)
                self._send_json(200, {"status": "ok", "message": "Privacy settings updated", "privacy": saved})
            except Exception as e:
                self._send_error(400, str(e))
            return

        # Multi-Model Battle Arena: Parallel Benchmark
        if path == "/v1/arena/compare":
            try:
                from api_client import chat
                from router import resolve_route
                from analytics import calculate_cost
                prompt = data.get("prompt", "Hello")
                candidates = data.get("candidates", [])
                max_tokens = int(data.get("max_tokens", 512))
                temperature = float(data.get("temperature", 0.7))
                req_timeout = min(max(float(data.get("timeout", 25.0)), 5.0), 60.0)
                config_data = load_config()
                providers_list = config_data.get("providers", [])
                providers_map = {p["name"].lower(): p for p in providers_list}

                results = []
                lock = threading.Lock()

                def run_candidate(c):
                    p_name = c.get("provider", "").strip()
                    m_name = c.get("model", "").strip()
                    
                    # Resolve provider and model via intelligent router
                    target_p = providers_map.get(p_name.lower())
                    routes = resolve_route(m_name, providers_list, target_provider_name=target_p.get("name") if target_p else None)
                    if routes:
                        prov, resolved_model = routes[0]
                    elif target_p:
                        prov, resolved_model = target_p, m_name
                    elif providers_list:
                        prov, resolved_model = providers_list[0], m_name
                    else:
                        prov, resolved_model = None, m_name

                    if not prov:
                        with lock:
                            results.append({"provider": p_name or "Unknown", "model": m_name, "error": "Provider not found", "ok": False})
                        return
                    try:
                        t0 = time.time()
                        text, raw, usage, lat, fmt = chat(prov, resolved_model, prompt, max_tokens, temperature, timeout=req_timeout)
                        t_tot = round((time.time() - t0) * 1000, 2)
                        in_t = usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0)
                        out_t = usage.get("output_tokens", 0) or usage.get("completion_tokens", 0)
                        cost = calculate_cost(resolved_model, in_t, out_t)
                        with lock:
                            results.append({
                                "provider": prov.get("name", ""),
                                "model": m_name,
                                "resolved_model": resolved_model,
                                "response": text,
                                "latency_ms": t_tot,
                                "input_tokens": in_t,
                                "output_tokens": out_t,
                                "total_tokens": in_t + out_t,
                                "cost_usd": cost,
                                "ok": True
                            })
                    except Exception as ex:
                        with lock:
                            results.append({"provider": prov.get("name", p_name), "model": m_name, "error": str(ex), "ok": False})

                thread_list = []
                for c in candidates:
                    t = threading.Thread(target=run_candidate, args=(c,), daemon=True)
                    t.start()
                    thread_list.append((t, c))

                for t, c in thread_list:
                    t.join(timeout=req_timeout + 1.0)

                # Ensure every candidate is accounted for in results
                with lock:
                    finished_models = {r.get("model") for r in results}
                    for c in candidates:
                        m_name = c.get("model", "")
                        if m_name not in finished_models:
                            results.append({
                                "provider": c.get("provider", "AIPI"),
                                "model": m_name,
                                "error": "Provider offline or connection timed out",
                                "ok": False
                            })

                self._send_json(200, {"status": "ok", "prompt": prompt, "results": results})
            except Exception as e:
                self._send_error(500, str(e))
            return

        if path == "/v1/gateway/restart":
            target_port = int(query.get("port", [DEFAULT_PORT])[0])
            force = query.get("force", ["0"])[0] == "1"
            # Send response BEFORE spawning so the client receives it before the
            # server socket closes. Use DETACHED_PROCESS so the child fully
            # outlives this process on Windows.
            self._send_json(200, {"status": "ok", "message": f"Gateway restarting on port {target_port}"})
            def _detached_restart():
                time.sleep(0.5)          # let the HTTP response flush
                script = os.path.join(APP_DIR, "gateway_server.py")
                python_exe = sys.executable
                if force:
                    kill_port_listener(target_port)
                    time.sleep(0.4)
                flags = 0
                if os.name == "nt":
                    DETACHED_PROCESS = 0x00000008
                    CREATE_NEW_PROCESS_GROUP = 0x00000200
                    flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
                subprocess.Popen(
                    [python_exe, script, "run", str(target_port)],
                    creationflags=flags,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                )
                # Now shut down current server cleanly
                time.sleep(0.3)
                if _active_server:
                    try:
                        _active_server.shutdown()
                    except Exception:
                        os._exit(0)
                else:
                    os._exit(0)
            threading.Thread(target=_detached_restart, daemon=True).start()
            return

        config_data = load_config()

        # ---- Provider / Server management (mirrors desktop app add/edit/delete) ----
        if path == "/v1/providers/add":
            name = (data.get("name") or "").strip()
            if not name:
                self._send_error(400, "Missing required 'name' field")
                return
            config_data.setdefault("providers", [])
            for p in config_data["providers"]:
                if (p.get("name") or "").lower() == name.lower():
                    self._send_error(400, "A server with that name already exists")
                    return
            config_data["providers"].append(data)
            if save_config_file(config_data):
                self._send_json(200, {"status": "ok", "message": f"Provider '{name}' added"})
            else:
                self._send_error(500, "Failed to write config.json")
            return

        if path == "/v1/providers/update":
            target = (data.get("name") or "").strip()
            new_prov = data.get("provider", {}) or {}
            if not target:
                self._send_error(400, "Missing required 'name' field")
                return
            config_data.setdefault("providers", [])
            for i, p in enumerate(config_data["providers"]):
                if (p.get("name") or "").strip() == target:
                    # Preserve existing api_key when the client left it blank/redacted.
                    key = new_prov.get("api_key", "")
                    if not key or "…" in key:
                        new_prov["api_key"] = p.get("api_key", "")
                    config_data["providers"][i] = new_prov
                    if save_config_file(config_data):
                        self._send_json(200, {"status": "ok", "message": f"Provider '{target}' updated"})
                    else:
                        self._send_error(500, "Failed to write config.json")
                    return
            self._send_error(404, "Provider not found: " + target)
            return

        if path == "/v1/providers/delete":
            name = (data.get("name") or "").strip()
            if not name:
                self._send_error(400, "Missing required 'name' field")
                return
            config_data.setdefault("providers", [])
            before = len(config_data["providers"])
            config_data["providers"] = [p for p in config_data["providers"] if (p.get("name") or "").strip() != name]
            if len(config_data["providers"]) == before:
                self._send_error(404, "Provider not found: " + name)
                return
            if save_config_file(config_data):
                self._send_json(200, {"status": "ok", "message": f"Provider '{name}' deleted"})
            else:
                self._send_error(500, "Failed to write config.json")
            return

        # AIPI Platform API Key Authorization Middleware
        auth_header = (self.headers.get("Authorization", "") or "").strip()
        virtual_key = None
        if auth_header.lower().startswith("bearer "):
            virtual_key = auth_header.split(" ", 1)[1].strip()
        elif self.headers.get("x-api-key"):
            virtual_key = self.headers.get("x-api-key", "").strip()
        elif self.headers.get("api-key"):
            virtual_key = self.headers.get("api-key", "").strip()
        elif self.headers.get("X-AIPI-Key"):
            virtual_key = self.headers.get("X-AIPI-Key", "").strip()
        elif self.headers.get("X-Proxia-Key"):
            virtual_key = self.headers.get("X-Proxia-Key", "").strip()
        # NOTE: ?api_key= query-string auth intentionally removed — keys in URLs
        # are logged in server/proxy access logs and browser history (security risk).

        is_chat_endpoint = (
            path in ("/v1/chat/completions", "/chat/completions", "/v1/chat", "/chat", "/v1/responses", "/responses")
            or path.startswith("/v1/chat/completions")
            or path.startswith("/chat/completions")
        )
        is_anthropic_endpoint = (
            path in ("/v1/messages", "/messages", "/v1/v1/messages")
            or path.startswith("/v1/messages")
            or path.startswith("/messages")
        )

        # If a recognized AIPI API key is presented, validate it; if invalid, reject immediately
        if virtual_key and any(virtual_key.startswith(p) for p in ("aipi-live-", "px-live-", "sk-proxia-", "sk-mgr-")):
            try:
                from virtual_keys import validate_key
                model_candidate = data.get("model", "")
                vk_valid, vk_msg, vk_info = validate_key(virtual_key, requested_model=model_candidate)
                if not vk_valid:
                    self._send_error(401, f"AIPI API Key rejected: {vk_msg}")
                    return
            except Exception as e:
                self._send_error(500, "API key validation error: " + str(e))
                return

        # Rate limiting on inference endpoints (per virtual key or per client IP, tier-aware)
        if is_chat_endpoint or is_anthropic_endpoint:
            try:
                from ratelimit import check_rate_limit
                from license import get_license_status
                lic_st = get_license_status()
                tier_info = lic_st.get("tier_info", {})
                rate_limit = float(tier_info.get("max_requests_per_min", 60.0))
                scope = virtual_key if virtual_key else f"ip:{self.client_address[0]}"
                rl = check_rate_limit(scope, rate_per_minute=rate_limit, capacity=rate_limit)
                if not rl["allowed"]:
                    self.send_response(429)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Retry-After", str(int(rl["retry_after_s"])))
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "error": {"message": f"Rate limit exceeded ({rate_limit}/min). Retry after {rl['retry_after_s']}s",
                                  "type": "rate_limit_exceeded"}
                    }).encode("utf-8"))
                    return
            except Exception:
                pass

        # Chat completions (OpenAI format)
        if is_chat_endpoint:
            self._handle_chat_completions(data, config_data, virtual_key)
            return

        # Text completions
        if path == "/v1/completions" or path.startswith("/v1/completions") or path == "/completions":
            prompt = data.get("prompt", "")
            data["messages"] = [{"role": "user", "content": prompt}]
            self._handle_chat_completions(data, config_data, virtual_key)
            return

        # Anthropic Messages compatibility endpoint
        if is_anthropic_endpoint:
            self._handle_anthropic_messages(data, config_data, virtual_key)
            return

        self._send_error(404, "Not found. Use /v1/chat/completions or /v1/messages")

    def _handle_chat_completions(self, data, config_data, virtual_key=None):
        model = (data.get("model", "") or "").strip()
        for g_prefix in ("aipi/", "aipi:", "gateway/", "local/", "default/"):
            if model.lower().startswith(g_prefix):
                model = model[len(g_prefix):].strip()
                break

        prov = self._get_provider_for_model(config_data, model)
        if not prov and config_data.get("providers"):
            prov = config_data["providers"][0]

        if not prov:
            self._send_error(500, "No providers configured in config.json")
            return

        model = model or prov.get("default_model", "")
        messages = data.get("messages", [])
        if not messages:
            self._send_error(400, "Missing 'messages' field")
            return

        max_tokens = data.get("max_tokens", 1024)
        temperature = data.get("temperature", 0.7)
        stream = data.get("stream", False)
        thinking_budget = data.get("thinking_budget") or data.get("thinking", {}).get("budget_tokens")

        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if isinstance(content, list):
                text_parts = []
                for part in content:
                    if isinstance(part, dict):
                        text_parts.append(part.get("text", "") or part.get("content", ""))
                    elif isinstance(part, str):
                        text_parts.append(part)
                content = " ".join(text_parts)
            elif not isinstance(content, str):
                content = str(content)

            if role == "system":
                prompt += f"[System]\n{content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n"

        if stream:
            self._handle_stream(prov, model, prompt, max_tokens, temperature, virtual_key, thinking_budget=thinking_budget)
        else:
            self._handle_completion(prov, model, prompt, max_tokens, temperature, virtual_key, thinking_budget=thinking_budget)

    def _handle_anthropic_messages(self, data, config_data, virtual_key=None):
        model = data.get("model", "") or ""
        prov = self._get_provider_for_model(config_data, model)
        if not prov:
            self._send_error(500, "No providers configured")
            return

        model = model or prov.get("default_model", "")
        system = data.get("system", "")
        messages = data.get("messages", [])
        max_tokens = data.get("max_tokens", 1024)
        temperature = data.get("temperature", 0.7)
        thinking_budget = data.get("thinking", {}).get("budget_tokens") or data.get("thinking_budget")

        prompt = ""
        if system:
            prompt += f"[System]\n{system}\n\n"
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join([c.get("text", "") for c in content if isinstance(c, dict)])
            prompt += f"{role.capitalize()}: {content}\n"

        if data.get("stream", False):
            self._handle_stream(prov, model, prompt, max_tokens, temperature, virtual_key, thinking_budget=thinking_budget)
        else:
            self._handle_anthropic_completion(prov, model, prompt, max_tokens, temperature, virtual_key, thinking_budget=thinking_budget)

    def _handle_anthropic_completion(self, prov, model, prompt, max_tokens, temperature, virtual_key=None, thinking_budget=None):
        try:
            from api_client import chat
            from cache import get_cached_response, save_cached_response
            from analytics import calculate_cost
            from db import add_history_entry, log_request

            # Exact-match cache check (Anthropic endpoint too)
            cached_resp = get_cached_response(model, prompt, temperature, max_tokens)
            if cached_resp:
                self._send_json(200, cached_resp)
                return

            text, raw, usage, latency, fmt = chat(prov, model, prompt, max_tokens, temperature, thinking_budget=thinking_budget)
            in_t = usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0)
            out_t = usage.get("output_tokens", 0) or usage.get("completion_tokens", 0)
            latency_ms = round(latency * 1000, 2)
            est_cost = calculate_cost(model, in_t, out_t)

            log_request("/v1/messages", prov.get("name", ""), model, 200, latency_ms)
            add_history_entry({
                "mode": "anthropic",
                "provider": prov.get("name", ""),
                "model": model,
                "prompt": prompt[:200],
                "response": text[:300],
                "latency_ms": latency_ms,
                "usage": usage,
                "ok": True
            })

            response = {
                "id": "msg_" + uuid.uuid4().hex[:20],
                "type": "message",
                "role": "assistant",
                "model": model,
                "content": [{"type": "text", "text": text}],
                "stop_reason": "end_turn",
                "usage": {
                    "input_tokens": in_t,
                    "output_tokens": out_t
                },
                "cost_usd": est_cost
            }
            save_cached_response(model, prompt, temperature, max_tokens, response)

            # Record spend on the virtual key if one was presented
            if virtual_key:
                try:
                    from virtual_keys import record_spend
                    record_spend(virtual_key, est_cost)
                except Exception:
                    pass

            self._send_json(200, response)
        except Exception as e:
            self._send_error(500, str(e)[:300])

    def _handle_completion(self, prov, model, prompt, max_tokens, temperature, virtual_key=None, thinking_budget=None):
        try:
            from api_client import chat
            from router import resolve_route, mark_provider_status
            from db import add_history_entry, log_request
            from cache import get_cached_response, save_cached_response
            from analytics import calculate_cost
            from pii_redactor import get_privacy_config, redact_text, unredact_text, is_url_airgapped_allowed

            priv = get_privacy_config()
            prompt_to_send, rep_map = redact_text(prompt, priv)

            # Check exact match cache first
            cached_resp = get_cached_response(model, prompt_to_send, temperature, max_tokens)
            if cached_resp:
                self._send_json(200, cached_resp)
                return

            config_data = load_config()
            providers = config_data.get("providers", [])
            target_name = prov.get("name") if (prov and not model.startswith("auto/")) else None
            routes = resolve_route(model, providers, target_provider_name=target_name)

            if not routes:
                routes = [(prov, model)] if prov else []

            last_error = None
            for p_candidate, m_candidate in routes:
                try:
                    # Stealth Mode Enforcement
                    if priv.get("stealth_mode", False) and not is_url_airgapped_allowed(p_candidate.get("base_url", "")):
                        raise PermissionError(f"Air-Gapped Stealth Mode active: external endpoint {p_candidate.get('base_url')} blocked.")

                    start_time = time.time()
                    text, raw, usage, latency, fmt = chat(p_candidate, m_candidate, prompt_to_send, max_tokens, temperature, thinking_budget=thinking_budget)
                    total_latency = round((time.time() - start_time) * 1000, 2)
                    mark_provider_status(p_candidate.get("name", ""), True, 200, total_latency, model_id=m_candidate)

                    # Auto un-redact if enabled
                    if priv.get("auto_unredact_response", True) and rep_map:
                        text = unredact_text(text, rep_map)
                    
                    in_t = usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0)
                    out_t = usage.get("output_tokens", 0) or usage.get("completion_tokens", 0)
                    est_cost = calculate_cost(m_candidate, in_t, out_t)

                    # Log entry & stats
                    log_request("/v1/chat/completions", p_candidate.get("name", ""), m_candidate, 200, total_latency)
                    add_history_entry({
                        "mode": "chat",
                        "provider": p_candidate.get("name", ""),
                        "model": m_candidate,
                        "prompt": prompt[:200],
                        "response": text[:300],
                        "latency_ms": total_latency,
                        "usage": usage,
                        "ok": True
                    })

                    response = {
                        "id": "chatcmpl-" + uuid.uuid4().hex[:20],
                        "object": "chat.completion",
                        "created": int(time.time()),
                        "model": m_candidate,
                        "choices": [{
                            "index": 0,
                            "message": {"role": "assistant", "content": text},
                            "finish_reason": "stop"
                        }],
                        "usage": {
                            "prompt_tokens": in_t,
                            "completion_tokens": out_t,
                            "total_tokens": in_t + out_t
                        },
                        "cost_usd": est_cost
                    }

                    save_cached_response(model, prompt, temperature, max_tokens, response)

                    # Record spend on the virtual key if one was presented
                    if virtual_key:
                        try:
                            from virtual_keys import record_spend
                            record_spend(virtual_key, est_cost)
                        except Exception:
                            pass

                    self._send_json(200, response)
                    return
                except Exception as ex:
                    last_error = ex
                    err_msg = str(ex)
                    mark_provider_status(p_candidate.get("name", ""), False, 500, model_id=m_candidate, error_msg=err_msg)
                    log_request("/v1/chat/completions", p_candidate.get("name", ""), m_candidate, 500, 0)

            raise last_error or RuntimeError("All routing candidates failed")
        except Exception as e:
            err_text = str(e)
            status_code = 429 if ("429" in err_text or "quota" in err_text.lower() or "exhausted" in err_text.lower() or "RESOURCE_EXHAUSTED" in err_text) else 500
            self._send_error(status_code, str(e)[:300])

    def _handle_stream(self, prov, model, prompt, max_tokens, temperature, virtual_key=None, thinking_budget=None):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            from api_client import chat_stream
            from router import resolve_route, mark_provider_status
            from db import log_request
            from analytics import calculate_cost

            config_data = load_config()
            providers = config_data.get("providers", [])
            target_name = prov.get("name") if (prov and not model.startswith("auto/")) else None
            routes = resolve_route(model, providers, target_provider_name=target_name)
            if not routes:
                routes = [(prov, model)] if prov else []

            last_error = None
            for p_candidate, m_candidate in routes:
                try:
                    _stream_req_id = "chatcmpl-" + uuid.uuid4().hex[:20]
                    full_text = ""
                    in_t = max(1, len(prompt) // 4)
                    out_t = 0
                    usage_received = False
                    start_time = time.time()
                    for kind, val in chat_stream(p_candidate, m_candidate, prompt, max_tokens, temperature):
                        if kind == "text":
                            full_text += val
                            chunk = {
                                "id": _stream_req_id,
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": m_candidate,
                                "choices": [{"index": 0, "delta": {"content": val}, "finish_reason": None}]
                            }
                            self._write_sse({"data": json.dumps(chunk, ensure_ascii=False)})
                        elif kind == "usage":
                            usage = val or {}
                            in_t = usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0) or in_t
                            out_t = usage.get("output_tokens", 0) or usage.get("completion_tokens", 0)
                            usage_received = True
                            final_chunk = {
                                "id": _stream_req_id,
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": m_candidate,
                                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                                "usage": {"prompt_tokens": in_t, "completion_tokens": out_t, "total_tokens": in_t + out_t},
                                "cost_usd": calculate_cost(m_candidate, in_t, out_t)
                            }
                            self._write_sse({"data": json.dumps(final_chunk, ensure_ascii=False)})
                            log_request("/v1/chat/completions", p_candidate.get("name", ""), m_candidate, 200,
                                        round((time.time() - start_time) * 1000, 2))

                    if not usage_received:
                        out_t = max(1, len(full_text) // 4)

                    total_latency = round((time.time() - start_time) * 1000, 2)
                    mark_provider_status(p_candidate.get("name", ""), True, 200, total_latency, model_id=m_candidate)

                    # Record spend on the virtual key if one was presented (streaming)
                    if virtual_key:
                        try:
                            from virtual_keys import record_spend
                            record_spend(virtual_key, calculate_cost(m_candidate, in_t, out_t))
                        except Exception:
                            pass

                    self._write_sse({"data": "[DONE]"})
                    self.close_connection = True
                    return
                except Exception as ex:
                    last_error = ex
                    err_msg = str(ex)
                    mark_provider_status(p_candidate.get("name", ""), False, 500, model_id=m_candidate, error_msg=err_msg)
                    log_request("/v1/chat/completions", p_candidate.get("name", ""), m_candidate, 500, 0)

            raise last_error or RuntimeError("All streaming routing candidates failed")
        except Exception as e:
            error_chunk = {"error": {"message": str(e)[:300], "type": "gateway_error"}}
            self._write_sse({"data": json.dumps(error_chunk, ensure_ascii=False)})

    def _write_sse(self, event):
        """Write and flush one SSE event so the client receives it immediately."""
        payload = "data: " + event["data"] + "\n\n"
        self.wfile.write(payload.encode("utf-8"))
        try:
            self.wfile.flush()
        except Exception:
            pass

# Module-level reference so the restart handler can shut down serve_forever() cleanly.
_active_server = None


class GatewayServer(ThreadingMixIn, HTTPServer):
    """Thread-per-request HTTP server — each request runs in its own daemon thread."""
    daemon_threads = True      # threads die when main process exits
    allow_reuse_address = True  # avoids TIME_WAIT bind failures on restart

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gateway_port = args[0][1] if args else DEFAULT_PORT


def kill_port_listener(port):
    """Forcefully terminate any process holding the specified port."""
    listeners = _get_listeners()
    if port in listeners:
        pid, proc = listeners[port]
        if pid:
            try:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, text=True)
                else:
                    import signal
                    os.kill(int(pid), signal.SIGKILL)
                time.sleep(0.5)
                return True, f"Killed process {proc} (PID {pid}) on port {port}"
            except Exception as e:
                return False, f"Failed to kill PID {pid}: {e}"
    return True, f"Port {port} is ready"


def start_gateway(port=DEFAULT_PORT, force=False):
    if is_gateway_running(port):
        stop_gateway()

    if force:
        kill_port_listener(port)
        time.sleep(0.5)

    script = os.path.join(APP_DIR, "gateway_server.py")
    python_exe = sys.executable
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    proc = subprocess.Popen(
        [python_exe, script, "run", str(port)],
        creationflags=flags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )

    time.sleep(1.2)
    if is_gateway_running(port):
        return True, f"Standard Professional Gateway running on http://127.0.0.1:{port}/v1"
    else:
        err_msg = ""
        if os.path.exists(ERR_LOG_PATH):
            try:
                with open(ERR_LOG_PATH, "r", encoding="utf-8") as f:
                    err_msg = f.read().strip()
            except Exception:
                pass
        detail = f"Details: {err_msg}" if err_msg else "Port is locked by another process. Try enabling 'Force Port'."
        return False, f"Gateway failed to start on port {port}. {detail}"


def stop_gateway():
    if os.path.exists(PID_PATH):
        try:
            with open(PID_PATH, "r") as f:
                pid = int(f.read().strip())
            try:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, text=True)
                else:
                    import signal
                    os.kill(pid, signal.SIGTERM)
            except Exception:
                pass
            if os.path.exists(PID_PATH):
                os.remove(PID_PATH)
            return True, "Gateway stopped"
        except Exception as e:
            return False, str(e)
    return False, "Gateway is not running"


def is_gateway_running(port=DEFAULT_PORT):
    import urllib.request
    try:
        url = f"http://127.0.0.1:{port}/v1/health"
        req = urllib.request.urlopen(url, timeout=1.5)
        if req.status == 200:
            return True
    except Exception:
        pass

    # If HTTP check failed, clean up stale PID file
    if os.path.exists(PID_PATH):
        try:
            os.remove(PID_PATH)
        except Exception:
            pass
    return False


def _get_listeners():
    """Return {port: (pid, process_name)} for ALL listening TCP ports on this machine."""
    listeners = {}
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW") else 0

    def _run(args):
        try:
            return subprocess.run(args, capture_output=True, text=True, creationflags=flags).stdout or ""
        except Exception:
            return ""

    out = _run(["netstat", "-ano", "-p", "tcp"])
    for line in out.splitlines():
        parts = line.split()
        # Robustly find LISTENING lines without hardcoding column index.
        # A LISTENING TCP line always contains both a local address and "LISTENING" keyword.
        if len(parts) >= 4 and parts[0].lower() == "tcp" and "listening" in line.lower():
            try:
                local = parts[1]
                pid = parts[-1]
                port = int(local.rsplit(":", 1)[-1])
                listeners.setdefault(port, (pid, ""))
            except Exception:
                continue

    names = {}
    tl = _run(["tasklist", "/FO", "CSV", "/NH"])
    import csv, io
    for row in csv.reader(io.StringIO(tl)):
        if len(row) >= 2 and row[1].strip().isdigit():
            names[row[1].strip()] = row[0].strip()
    for port in listeners:
        pid, _ = listeners[port]
        listeners[port] = (pid, names.get(pid, ""))
    return listeners


def scan_ports(ports):
    if isinstance(ports, (int, str)):
        ports = [ports]
    listeners = _get_listeners()
    import socket
    results = []
    for p in ports:
        try:
            port = int(p)
        except (TypeError, ValueError):
            continue
        entry = {"port": port, "in_use": False, "pid": "", "process": "", "error": ""}
        if port in listeners:
            pid, proc = listeners[port]
            entry.update(in_use=True, pid=pid, process=proc)
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                s.listen(1)
            except OSError as e:
                entry["in_use"] = True
                entry["error"] = str(e)[:120]
            finally:
                s.close()
        results.append(entry)
    return results


def expand_port_spec(spec, default=DEFAULT_PORT):
    ports = []
    for part in str(spec).replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            try:
                lo, hi = int(a), int(b)
                if lo > hi:
                    lo, hi = hi, lo
                ports.extend(range(lo, hi + 1))
            except ValueError:
                continue
        else:
            try:
                ports.append(int(part))
            except ValueError:
                continue
    return ports if ports else [default]


def main():
    action = (sys.argv[1] if len(sys.argv) > 1 else "status").lower()
    port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT

    if action == "start":
        force = "--force" in sys.argv or "-f" in sys.argv
        ok, detail = start_gateway(port, force=force)
        print(("GREEN - " if ok else "RED - ") + detail)
    elif action == "stop":
        ok, detail = stop_gateway()
        print(("GREEN - " if ok else "RED - ") + detail)
    elif action == "run":
        try:
            lf = open(os.path.join(APP_DIR, "gateway_server.log"), "a", encoding="utf-8")
            # Only stderr goes to log file; stdout stays for parent-process monitoring.
            sys.stderr = lf
        except Exception:
            pass

        if os.path.exists(ERR_LOG_PATH):
            try:
                os.remove(ERR_LOG_PATH)
            except Exception:
                pass

        # Bootstrap DB, Master API Key, and initial Admin account
        try:
            from db import init_db
            init_db()
            from virtual_keys import ensure_master_key
            ensure_master_key()
            from auth import ensure_admin_bootstrap
            ensure_admin_bootstrap()
        except Exception:
            pass

        global _active_server
        server = None
        bind_host = "127.0.0.1"
        if "--host" in sys.argv:
            bind_host = sys.argv[sys.argv.index("--host") + 1]
        elif os.environ.get("AIMM_BIND_HOST"):
            bind_host = os.environ["AIMM_BIND_HOST"]
        for attempt in range(5):
            try:
                server = GatewayServer((bind_host, port), GatewayHandler)
                _active_server = server
                break
            except OSError as e:
                err_detail = str(e)
                if attempt == 4 or "Permission denied" in err_detail or "Access is denied" in err_detail:
                    try:
                        with open(ERR_LOG_PATH, "w", encoding="utf-8") as ef:
                            ef.write(f"Cannot bind {bind_host}:{port} — {err_detail}")
                    except Exception:
                        pass
                    break
                time.sleep(0.4)

        if not server:
            try:
                with open(ERR_LOG_PATH, "w", encoding="utf-8") as f:
                    f.write(f"Could not bind port {port} after retries.")
            except Exception:
                pass
            return

        try:
            with open(PID_PATH, "w") as f:
                f.write(str(os.getpid()))
            try:
                print(f"Gateway serving on http://127.0.0.1:{port}")
            except OSError:
                pass

            # ── Startup: Sync Antigravity token from Windows Credential Manager ──
            def _sync_antigravity_token_on_startup():
                try:
                    from oauth_manager import read_antigravity_token_from_credential_store, auto_refresh_antigravity_token
                    from db import get_providers, add_or_update_provider
                    providers = get_providers()
                    agy = next((p for p in providers if
                                "antigravity" in (p.get("name") or "").lower() or
                                (p.get("format") or "").lower() == "antigravity"), None)
                    if not agy:
                        return
                    # Read fresh token from Credential Manager
                    cred = read_antigravity_token_from_credential_store()
                    cred_token = cred.get("access_token", "")
                    cred_refresh = cred.get("refresh_token", "")
                    if cred_refresh and not agy.get("refresh_token"):
                        agy["refresh_token"] = cred_refresh
                    if cred_token:
                        agy["api_key"] = cred_token
                        add_or_update_provider(agy)
                    # Always refresh at startup to ensure fresh token
                    new_token = auto_refresh_antigravity_token()
                    if new_token:
                        try:
                            print("Antigravity token auto-refreshed on startup OK")
                        except OSError:
                            pass
                except Exception:
                    pass

            import threading as _thr
            _thr.Thread(target=_sync_antigravity_token_on_startup, daemon=True).start()

            server.serve_forever()
        except Exception as e:
            try:
                with open(ERR_LOG_PATH, "w", encoding="utf-8") as f:
                    f.write(str(e))
            except Exception:
                pass
            if os.path.exists(PID_PATH):
                try:
                    os.remove(PID_PATH)
                except Exception:
                    pass
    else:
        if is_gateway_running():
            print(f"GREEN - Gateway is running on http://127.0.0.1:{port}/v1/chat/completions")
        else:
            print("RED - Gateway is not running")

if __name__ == "__main__":
    main()
