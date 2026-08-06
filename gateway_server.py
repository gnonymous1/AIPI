"""
gateway_server.py - Standard Professional Local API Gateway & Python Web Server for AI Model Manager.

Runs an OpenAI & Anthropic-compatible HTTP server and full Browser Dashboard on localhost so third-party software
(Claude Code, Cursor, Windsurf, LangChain, custom apps) and your browser can use your configured providers.
"""
import json
import os
import subprocess
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Config
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
PID_PATH = os.path.join(APP_DIR, "gateway.pid")
ERR_LOG_PATH = os.path.join(APP_DIR, "gateway_error.log")
WEB_DIR = os.path.join(APP_DIR, "web")
DEFAULT_PORT = 11434

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"providers": []}

def save_config_file(data):
    try:
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

class GatewayHandler(BaseHTTPRequestHandler):
    """OpenAI & Anthropic compatible API gateway and Web Dashboard handler."""

    def log_message(self, format, *args):
        pass

    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

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

        # Web Dashboard static files
        if path == "/" or path == "/index.html" or path == "/dashboard":
            if not self._serve_file("index.html", "text/html"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Standard Professional Gateway Running</h1><p>API: /v1/models | /v1/chat/completions</p>")
            return

        if path == "/style.css":
            if self._serve_file("style.css", "text/css"):
                return

        if path == "/app.js":
            if self._serve_file("app.js", "application/javascript"):
                return

        # Professional API Endpoints
        if path == "/v1/health":
            port = getattr(self.server, "gateway_port", DEFAULT_PORT)
            self._send_json(200, {
                "status": "ok",
                "service": "Standard Professional AI Gateway (Python Server)",
                "port": port,
                "providers_count": len(config_data.get("providers", [])),
                "providers": config_data.get("providers", [])
            })
            return

        if path == "/v1/openapi.json":
            port = getattr(self.server, "gateway_port", DEFAULT_PORT)
            spec = {
                "openapi": "3.0.0",
                "info": {
                    "title": "Standard Professional AI Model Gateway",
                    "version": "1.0.0",
                    "description": "Unified OpenAI & Anthropic Compatible Local AI Model Gateway"
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
            self._send_json(200, config_data)
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
            models = []
            seen = set()
            results = {}

            def fetch_for_provider(p):
                try:
                    from api_client import list_models, resolve_format
                    fmt = resolve_format(p)
                    mlist = list_models(p.get("base_url", ""), p.get("api_key", ""), fmt)
                    results[p["name"]] = mlist
                except Exception:
                    results[p["name"]] = []

            threads = []
            for p in config_data.get("providers", []):
                t = threading.Thread(target=fetch_for_provider, args=(p,), daemon=True)
                t.start()
                threads.append(t)

            for t in threads:
                t.join(timeout=3)

            for p in config_data.get("providers", []):
                mlist = results.get(p["name"], [])
                for m in mlist:
                    if m not in seen:
                        models.append({"id": m, "object": "model", "owned_by": p["name"]})
                        seen.add(m)
            self._send_json(200, {"object": "list", "data": models})
            return

        self._send_error(404, "Not found. Use /v1/models, /v1/chat/completions, /v1/messages, or /v1/health")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len) if content_len > 0 else b"{}"

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

        if path == "/v1/gateway/restart":
            target_port = int(query.get("port", [DEFAULT_PORT])[0])
            force = query.get("force", ["0"])[0] == "1"
            threading.Thread(target=lambda: start_gateway(target_port, force=force), daemon=True).start()
            self._send_json(200, {"status": "ok", "message": f"Gateway restart initiated on port {target_port}"})
            return

        config_data = load_config()

        # Chat completions (OpenAI format)
        if path == "/v1/chat/completions" or path.startswith("/v1/chat/completions"):
            self._handle_chat_completions(data, config_data)
            return

        # Text completions
        if path == "/v1/completions" or path.startswith("/v1/completions"):
            prompt = data.get("prompt", "")
            data["messages"] = [{"role": "user", "content": prompt}]
            self._handle_chat_completions(data, config_data)
            return

        # Anthropic Messages compatibility endpoint
        if path == "/v1/messages" or path.startswith("/v1/messages"):
            self._handle_anthropic_messages(data, config_data)
            return

        self._send_error(404, "Not found. Use /v1/chat/completions or /v1/messages")

    def _handle_chat_completions(self, data, config_data):
        prov = self._get_provider_from_query(config_data)
        if not prov:
            self._send_error(500, "No providers configured in config.json")
            return

        model = data.get("model", "") or prov.get("default_model", "")
        messages = data.get("messages", [])
        if not messages:
            self._send_error(400, "Missing 'messages' field")
            return

        max_tokens = data.get("max_tokens", 1024)
        temperature = data.get("temperature", 0.7)
        stream = data.get("stream", False)

        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt += f"[System]\n{content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n"

        if stream:
            self._handle_stream(prov, model, prompt, max_tokens, temperature)
        else:
            self._handle_completion(prov, model, prompt, max_tokens, temperature)

    def _handle_anthropic_messages(self, data, config_data):
        prov = self._get_provider_from_query(config_data)
        if not prov:
            self._send_error(500, "No providers configured")
            return

        model = data.get("model", "") or prov.get("default_model", "")
        system = data.get("system", "")
        messages = data.get("messages", [])
        max_tokens = data.get("max_tokens", 1024)
        temperature = data.get("temperature", 0.7)

        prompt = ""
        if system:
            prompt += f"[System]\n{system}\n\n"
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join([c.get("text", "") for c in content if isinstance(c, dict)])
            prompt += f"{role.capitalize()}: {content}\n"

        try:
            from api_client import chat
            text, raw, usage, latency, fmt = chat(prov, model, prompt, max_tokens, temperature)
            response = {
                "id": "msg_gateway_pro",
                "type": "message",
                "role": "assistant",
                "model": model,
                "content": [{"type": "text", "text": text}],
                "stop_reason": "end_turn",
                "usage": {
                    "input_tokens": usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0) or usage.get("completion_tokens", 0)
                }
            }
            self._send_json(200, response)
        except Exception as e:
            self._send_error(500, str(e)[:300])

    def _handle_completion(self, prov, model, prompt, max_tokens, temperature):
        try:
            from api_client import chat
            text, raw, usage, latency, fmt = chat(prov, model, prompt, max_tokens, temperature)
            response = {
                "id": "chatcmpl-gateway-pro",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("output_tokens", 0) or usage.get("completion_tokens", 0),
                    "total_tokens": (usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0)) +
                                    (usage.get("output_tokens", 0) or usage.get("completion_tokens", 0))
                }
            }
            self._send_json(200, response)
        except Exception as e:
            self._send_error(500, str(e)[:300])

    def _handle_stream(self, prov, model, prompt, max_tokens, temperature):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        try:
            from api_client import chat_stream
            for kind, val in chat_stream(prov, model, prompt, max_tokens, temperature):
                if kind == "text":
                    chunk = {
                        "id": "chatcmpl-gateway-pro",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [{"index": 0, "delta": {"content": val}, "finish_reason": None}]
                    }
                    self.wfile.write(("data: " + json.dumps(chunk) + "\n\n").encode("utf-8"))
            final_chunk = {
                "id": "chatcmpl-gateway-pro",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
            }
            self.wfile.write(("data: " + json.dumps(final_chunk) + "\n\n").encode("utf-8"))
            self.wfile.write(b"data: [DONE]\n\n")
        except Exception as e:
            error_chunk = {"error": {"message": str(e)[:300], "type": "gateway_error"}}
            self.wfile.write(("data: " + json.dumps(error_chunk) + "\n\n").encode("utf-8"))

class GatewayServer(HTTPServer):
    allow_reuse_address = True

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
        req = urllib.request.urlopen(url, timeout=1.0)
        if req.status == 200:
            return True
    except Exception:
        pass

    if not os.path.exists(PID_PATH):
        return False
    try:
        with open(PID_PATH, "r") as f:
            pid = int(f.read().strip())
        if os.name == "nt":
            res = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
            return str(pid) in res.stdout
        else:
            import signal
            os.kill(pid, 0)
            return True
    except Exception:
        if os.path.exists(PID_PATH):
            try: os.remove(PID_PATH)
            except: pass
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
        if len(parts) >= 5 and parts[0].lower() in ("tcp",):
            local, state, pid = parts[1], parts[3], parts[-1]
            if state.upper() != "LISTENING":
                continue
            try:
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
            sys.stdout = lf
            sys.stderr = lf
        except Exception:
            pass

        if os.path.exists(ERR_LOG_PATH):
            try: os.remove(ERR_LOG_PATH)
            except: pass

        server = None
        for attempt in range(5):
            try:
                server = GatewayServer(("127.0.0.1", port), GatewayHandler)
                break
            except OSError as e:
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
