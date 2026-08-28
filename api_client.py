"""
api_client.py - Networking layer for the AI Model Manager.

Supports both OpenAI-compatible endpoints (e.g. Ollama, OpenRouter, Together)
and Anthropic-compatible endpoints (e.g. Claude, routed gateways).
"""
import json
import requests


class APIError(Exception):
    """Raised when a request to the model API fails."""


def normalize_base(url):
    """Ensure the base URL has a scheme and no trailing slash."""
    url = (url or "").strip()
    if url and not url.startswith(("http://", "https://")):
        url = "http://" + url
    return url.rstrip("/")


def _api(base, suffix):
    """
    Build an API route. Some providers give a base that already ends in /v1
    (e.g. https://host/v1); others don't. Avoid doubling the /v1 segment.
    """
    base = normalize_base(base)
    if base.endswith("/v1"):
        return base + suffix
    return base + "/v1" + suffix


def _auth_headers(api_key, fmt):
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }
    if api_key:
        if isinstance(api_key, str) and api_key.startswith("enc:"):
            try:
                from vault import decrypt_key
                api_key = decrypt_key(api_key)
            except Exception:
                pass
        if fmt == "anthropic":
            headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"
        else:
            headers["Authorization"] = "Bearer " + api_key
    return headers


def _friendly_request_error(e):
    """Turn a requests exception into a human-readable, actionable message."""
    msg = str(e)
    low = msg.lower()
    if "winerror 10061" in low or "connection refused" in low:
        return ("Connection refused - is the server running and is the port "
                "correct? (nothing is listening there)")
    if "winerror 10060" in low or "timed out" in low:
        return "Request timed out - the host did not respond."
    if "name or service not known" in low or "getaddrinfo" in low:
        return "Could not resolve the host name - check the base URL."
    if "ssl" in low or "cipher" in low or "certificate" in low:
        return "TLS/SSL error - check the URL scheme (https vs http)."
    if "max retries" in low:
        return ("No connection could be made - server unreachable (is it running? "
                "check the base URL and port).")
    return msg[:200]


# Persistent session with connection pooling and keep-alive for sub-millisecond connection reuse
_SESSION = requests.Session()
try:
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    _adapter = HTTPAdapter(pool_connections=30, pool_maxsize=100, max_retries=Retry(total=1, connect=1, read=0))
    _SESSION.mount("https://", _adapter)
    _SESSION.mount("http://", _adapter)
except Exception:
    pass

def _http_get(url, headers, timeout=12):
    try:
        t_conn = min(1.5, float(timeout if isinstance(timeout, (int, float)) else 12))
        t_read = float(timeout if isinstance(timeout, (int, float)) else 12)
        return _SESSION.get(url, headers=headers, timeout=(t_conn, t_read))
    except requests.exceptions.RequestException as e:
        raise APIError("Network error: %s" % _friendly_request_error(e))


def _http_post(url, headers, payload, timeout=120):
    try:
        t_conn = min(2.0, float(timeout if isinstance(timeout, (int, float)) else 120))
        t_read = float(timeout if isinstance(timeout, (int, float)) else 120)
        return _SESSION.post(url, headers=headers, json=payload, timeout=(t_conn, t_read))
    except requests.exceptions.RequestException as e:
        raise APIError("Network error: %s" % _friendly_request_error(e))


def _extract_error(r):
    try:
        j = r.json()
        if isinstance(j, dict):
            err = j.get("error")
            if isinstance(err, dict):
                msg = err.get("message") or err
                return str(msg)
            return json.dumps(j)[:300]
    except Exception:
        pass
    return (r.text or "")[:300]


def detect_format(base, api_key, timeout=1.0):
    """Try to auto-detect whether an endpoint speaks OpenAI or Anthropic."""
    base = normalize_base(base)
    t = float(timeout if isinstance(timeout, (int, float)) else 1.0)
    for fmt in ("openai", "anthropic"):
        try:
            r = _http_get(_api(base, "/models"), _auth_headers(api_key, fmt), timeout=t)
            if r.status_code < 400:
                return fmt
        except Exception:
            continue
    return "openai"


def resolve_format(provider, timeout=2.0):
    fmt = (provider.get("format") or "auto").strip().lower()
    base = (provider.get("base_url") or "").lower()
    name = (provider.get("name") or "").lower()
    if fmt == "antigravity" or "cloudcode-pa" in base or "antigravity" in name:
        return "antigravity"
    if fmt == "auto":
        fmt = detect_format(provider.get("base_url", ""), provider.get("api_key", ""), timeout=timeout)
    if fmt not in ("openai", "anthropic", "antigravity"):
        fmt = "openai"
    return fmt


# These are the real upstream model IDs returned by fetchAvailableModels,
# directly sent to v1internal:generateContent. The display names map here:
# "Gemini 3.7 Flash (High)"   -> gemini-3.6-flash-high   (tiered high)
# "Gemini 3.6 Flash (Medium)" -> gemini-3.6-flash-medium
# "Gemini 3.5 Flash (Medium)" -> gemini-3.5-flash-low
# "Gemini 3.1 Pro (Low)"      -> gemini-3.1-pro-low
# "Claude Sonnet 4.6"          -> claude-sonnet-4-6  (77.6% quota)
# "Claude Opus 4.6 Thinking"   -> claude-opus-4-6-thinking (77.6% quota)
# "GPT-OSS 120B (Medium)"      -> gpt-oss-120b-medium (77.6% quota)
ANTIGRAVITY_MODELS = [
    "antigravity/claude-sonnet-4-6",        # 77.6% quota - AVAILABLE
    "antigravity/claude-opus-4-6-thinking", # 77.6% quota - AVAILABLE
    "antigravity/gpt-oss-120b-medium",      # 77.6% quota - AVAILABLE
    "antigravity/gemini-3.6-flash-high",    # 5.5% quota - limited
    "antigravity/gemini-3.6-flash-medium",
    "antigravity/gemini-3.6-flash-low",
    "antigravity/gemini-3.5-flash-high",    # real ID: gemini-3-flash-agent
    "antigravity/gemini-3.5-flash-medium",  # real ID: gemini-3.5-flash-low
    "antigravity/gemini-3.5-flash-low",     # real ID: gemini-3.5-flash-extra-low
    "antigravity/gemini-3.1-pro-high",      # real ID: gemini-pro-agent
    "antigravity/gemini-3.1-pro-low",
    "antigravity/gemini-3.1-flash-lite",
    "antigravity/gemini-2.5-flash",
    "antigravity/gemini-2.5-pro",
]

# Maps from AIPI model ID (without prefix) -> real upstream ID for cloudcode-pa API
# These are the exact IDs required in the generateContent payload.
ANTIGRAVITY_ALIASES = {
    # Gemini 3.7 display tier -> actual tiered IDs
    "gemini-3.7-flash-high": "gemini-3.6-flash-high",
    "gemini-3.7-flash-medium": "gemini-3.6-flash-medium",
    "gemini-3.7-flash-low": "gemini-3.6-flash-low",
    "gemini-3.7-flash": "gemini-3.6-flash-high",
    # Gemini 3.6 passthrough (correct IDs)
    "gemini-3.6-flash": "gemini-3.6-flash-medium",
    # Gemini 3.5 -> real upstream IDs
    "gemini-3.5-flash": "gemini-3-flash-agent",
    "gemini-3.5-flash-high": "gemini-3-flash-agent",
    "gemini-3.5-flash-medium": "gemini-3.5-flash-low",
    "gemini-3.5-flash-low": "gemini-3.5-flash-extra-low",
    # Gemini 3.1 Pro -> real upstream IDs
    "gemini-3.1-pro": "gemini-pro-agent",
    "gemini-3.1-pro-high": "gemini-pro-agent",
    # Claude & GPT-OSS mapping
    "gemini-claude-sonnet-4-5": "claude-sonnet-4-6",
    "gemini-claude-sonnet-4-5-thinking": "claude-sonnet-4-6",
    "gemini-claude-opus-4-5-thinking": "claude-sonnet-4-6",
    "claude-opus-4-6": "claude-sonnet-4-6",
    "claude-opus-4-6-thinking": "claude-sonnet-4-6",
    "gpt-oss-120b": "gpt-oss-120b-medium"
}


def test_connection(base, api_key, fmt):
    """
    Return (ok, resolved_format, models_list, error_message).
    Raises APIError only on network errors; HTTP failures are returned as ok=False.
    """
    base = normalize_base(base)
    if fmt == "antigravity" or "cloudcode-pa" in base:
        return True, "antigravity", list(ANTIGRAVITY_MODELS), None
    if fmt == "auto":
        fmt = detect_format(base, api_key)
    headers = _auth_headers(api_key, fmt)
    r = _http_get(_api(base, "/models"), headers)
    if r.status_code < 400:
        data = r.json()
        models = [m.get("id") for m in data.get("data", []) if isinstance(m, dict) and m.get("id")]
        return True, fmt, models, None
    return False, fmt, [], "HTTP %s: %s" % (r.status_code, _extract_error(r))


def list_models(base, api_key, fmt):
    base = normalize_base(base)
    if fmt == "antigravity" or "cloudcode-pa" in base:
        return list(ANTIGRAVITY_MODELS)
    if fmt == "auto":
        fmt = detect_format(base, api_key)
    headers = _auth_headers(api_key, fmt)
    r = _http_get(_api(base, "/models"), headers)
    if r.status_code >= 400:
        raise APIError("HTTP %s: %s" % (r.status_code, _extract_error(r)))
    data = r.json()
    models = []
    for m in data.get("data", []):
        if isinstance(m, dict) and m.get("id"):
            models.append(m.get("id"))
    return models


def chat(provider, model, prompt, max_tokens=1024, temperature=0.7, timeout=120, thinking_budget=None):
    """
    Send a single chat message to the model and return
    (text, raw_data, usage_dict, latency_seconds, used_format).
    Raises APIError on failure.
    """
    fmt = resolve_format(provider, timeout=min(float(timeout or 1.0), 0.8))
    base = normalize_base(provider.get("base_url", ""))
    api_key = provider.get("api_key", "")
    headers = _auth_headers(api_key, fmt)

    if fmt == "antigravity":
        import uuid
        clean_model = model.replace("antigravity/", "").replace("claude/", "")
        clean_model = ANTIGRAVITY_ALIASES.get(clean_model, clean_model)
        project_id = provider.get("project_id") or "massive-snowfall-w2tjw"
        if isinstance(api_key, str) and api_key.startswith("enc:"):
            from vault import decrypt_key
            api_key = decrypt_key(api_key)

        endpoints = [
            "https://daily-cloudcode-pa.googleapis.com",
            "https://daily-cloudcode-pa.sandbox.googleapis.com",
            "https://cloudcode-pa.googleapis.com"
        ]
        ag_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Antigravity/4.2.0 (darwin/arm64) vscode/1.96.0"
        }
        gen_config = {
            "temperature": temperature,
            "maxOutputTokens": int(max_tokens)
        }
        # Support Thinking Levels / Reasoning Budget
        if thinking_budget and int(thinking_budget) > 0:
            gen_config["thinkingConfig"] = {
                "thinkingBudget": int(thinking_budget),
                "includeThoughts": True
            }
        elif "thinking" in clean_model or "-high" in clean_model:
            gen_config["thinkingConfig"] = {
                "thinkingBudget": 4096,
                "includeThoughts": True
            }

        payload = {
            "project": project_id,
            "model": clean_model,
            "userAgent": "antigravity",
            "requestType": "agent",
            "requestId": f"agent-req-{uuid.uuid4().hex[:12]}",
            "enabledCreditTypes": ["GOOGLE_ONE_AI"],
            "request": {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": gen_config
            }
        }

        r = None
        last_err = None
        for ep in endpoints:
            url = f"{ep}/v1internal:generateContent"
            r = _http_post(url, ag_headers, payload, timeout)
            if r.status_code == 401:
                try:
                    from oauth_manager import auto_refresh_antigravity_token
                    new_key = auto_refresh_antigravity_token()
                    if new_key:
                        provider["api_key"] = new_key
                        ag_headers["Authorization"] = f"Bearer {new_key}"
                        r = _http_post(url, ag_headers, payload, timeout)
                except Exception:
                    pass
            if r.status_code < 400:
                break
            last_err = r

        if r is None or r.status_code >= 400:
            err_src = r if r is not None else last_err
            raise APIError("HTTP %s: %s" % (err_src.status_code if err_src else 500, _extract_error(err_src) if err_src else "All endpoints failed"))

        data = r.json()
        resp_obj = data.get("response", {})
        candidates = resp_obj.get("candidates", [])
        text = ""
        thought_text = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            for p in parts:
                if isinstance(p, dict):
                    if p.get("text"):
                        text += p["text"]
                    if p.get("thought"):
                        thought_text += str(p.get("thought"))
                elif isinstance(p, str):
                    text += p
        
        if not text and thought_text:
            text = thought_text

        usage_meta = resp_obj.get("usageMetadata", {})
        usage = {
            "prompt_tokens": usage_meta.get("promptTokenCount", max(1, len(prompt) // 4)),
            "completion_tokens": usage_meta.get("candidatesTokenCount", max(1, len(text) // 4)),
            "total_tokens": usage_meta.get("totalTokenCount", max(2, (len(prompt) + len(text)) // 4))
        }
        return text, data, usage, r.elapsed.total_seconds(), "antigravity"

    if fmt == "anthropic":
        url = _api(base, "/messages")
        payload = {
            "model": model,
            "max_tokens": int(max_tokens),
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        r = _http_post(url, headers, payload, timeout)
        if r.status_code >= 400:
            raise APIError("HTTP %s: %s" % (r.status_code, _extract_error(r)))
        data = r.json()
        text = ""
        for blk in data.get("content", []):
            if isinstance(blk, dict) and blk.get("type") == "text":
                text += blk.get("text", "")
        usage = data.get("usage", {})
        return text, data, usage, r.elapsed.total_seconds(), fmt

    # OpenAI-compatible
    url = _api(base, "/chat/completions")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": int(max_tokens),
        "stream": False,
    }
    r = _http_post(url, headers, payload, timeout)
    if r.status_code >= 400:
        raise APIError("HTTP %s: %s" % (r.status_code, _extract_error(r)))

    raw_text = r.text.strip()
    content_type = r.headers.get("content-type", "")

    # If the provider returned an SSE stream instead of raw JSON
    if raw_text.startswith("data:") or "text/event-stream" in content_type:
        text = ""
        usage = {}
        for line in raw_text.splitlines():
            line = line.strip()
            if line.startswith("data:") and not line.endswith("[DONE]"):
                chunk_str = line[5:].strip()
                if chunk_str:
                    try:
                        cjson = json.loads(chunk_str)
                        choices = cjson.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            d_text = delta.get("content") or delta.get("reasoning_content") or delta.get("reasoning") or delta.get("thinking") or ""
                            text += d_text
                        if "usage" in cjson and cjson["usage"]:
                            usage = cjson["usage"]
                    except Exception:
                        pass
        return text, {"choices": [{"message": {"role": "assistant", "content": text}}]}, usage, r.elapsed.total_seconds(), fmt

    data = r.json()
    try:
        msg = data["choices"][0]["message"]
        text = msg.get("content")
        if not text and (msg.get("reasoning_content") or msg.get("reasoning") or msg.get("thinking")):
            text = msg.get("reasoning_content") or msg.get("reasoning") or msg.get("thinking") or ""
        if text is None:
            text = ""
    except (KeyError, IndexError, TypeError):
        text = json.dumps(data, indent=2)[:4000]
    usage = data.get("usage", {})
    return text, data, usage, r.elapsed.total_seconds(), fmt


def _stream_error(r):
    try:
        chunk = next(r.iter_content(2048), b"").decode(errors="replace")
        return (chunk or "")[:300]
    except Exception:
        return ""


def chat_stream(provider, model, prompt, max_tokens=1024, temperature=0.7, timeout=120, thinking_budget=None):
    """
    Streaming variant of chat(). Yields ("text", delta) tuples as tokens arrive,
    then ("usage", usage_dict). The resolved format is yielded first as
    ("fmt", fmt). Raises APIError on network/HTTP failure.
    """
    fmt = resolve_format(provider, timeout=min(float(timeout or 2.0), 2.0))
    base = normalize_base(provider.get("base_url", ""))
    api_key = provider.get("api_key", "")
    headers = _auth_headers(api_key, fmt)
    yield ("fmt", fmt)

    if fmt == "antigravity":
        import uuid
        clean_model = model.replace("antigravity/", "").replace("claude/", "")
        clean_model = ANTIGRAVITY_ALIASES.get(clean_model, clean_model)
        project_id = provider.get("project_id") or "massive-snowfall-w2tjw"
        if isinstance(api_key, str) and api_key.startswith("enc:"):
            from vault import decrypt_key
            api_key = decrypt_key(api_key)

        endpoints = [
            "https://daily-cloudcode-pa.googleapis.com",
            "https://daily-cloudcode-pa.sandbox.googleapis.com",
            "https://cloudcode-pa.googleapis.com"
        ]
        ag_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Antigravity/4.2.0 (darwin/arm64) vscode/1.96.0"
        }
        gen_config = {
            "temperature": temperature,
            "maxOutputTokens": int(max_tokens)
        }
        if thinking_budget and int(thinking_budget) > 0:
            gen_config["thinkingConfig"] = {
                "thinkingBudget": int(thinking_budget),
                "includeThoughts": True
            }
        elif "thinking" in clean_model or "-high" in clean_model:
            gen_config["thinkingConfig"] = {
                "thinkingBudget": 4096,
                "includeThoughts": True
            }

        payload = {
            "project": project_id,
            "model": clean_model,
            "userAgent": "antigravity",
            "requestType": "agent",
            "requestId": f"agent-req-{uuid.uuid4().hex[:12]}",
            "enabledCreditTypes": ["GOOGLE_ONE_AI"],
            "request": {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": gen_config
            }
        }

        r = None
        last_err = None
        for ep in endpoints:
            url = f"{ep}/v1internal:streamGenerateContent?alt=sse"
            try:
                r = requests.post(url, headers=ag_headers, json=payload, timeout=timeout, stream=True)
            except requests.exceptions.RequestException as e:
                last_err = e
                continue
            if r.status_code == 401:
                try:
                    from oauth_manager import auto_refresh_antigravity_token
                    new_key = auto_refresh_antigravity_token()
                    if new_key:
                        provider["api_key"] = new_key
                        ag_headers["Authorization"] = f"Bearer {new_key}"
                        r = requests.post(url, headers=ag_headers, json=payload, timeout=timeout, stream=True)
                except Exception:
                    pass
            if r.status_code < 400:
                break
            last_err = r

        if r is None or r.status_code >= 400:
            err_detail = _stream_error(r) if (r is not None and hasattr(r, 'iter_lines')) else ""
            raise APIError("HTTP %s: %s" % (r.status_code if r is not None else 500, err_detail or (_extract_error(r) if r is not None else str(last_err))))

        usage = {}
        for line in r.iter_lines(decode_unicode=True):
            if not line:
                continue
            line = line.strip()
            if not line.startswith("data:"):
                continue
            data_str = line[5:].strip()
            if data_str == "[DONE]":
                break
            try:
                obj = json.loads(data_str)
            except Exception:
                continue
            resp_obj = obj.get("response", {})
            candidates = resp_obj.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                for p in parts:
                    if isinstance(p, dict) and p.get("text"):
                        yield ("text", p["text"])
                    elif isinstance(p, str):
                        yield ("text", p)
            usage_meta = resp_obj.get("usageMetadata")
            if usage_meta:
                usage = {
                    "prompt_tokens": usage_meta.get("promptTokenCount", 0),
                    "completion_tokens": usage_meta.get("candidatesTokenCount", 0),
                    "total_tokens": usage_meta.get("totalTokenCount", 0)
                }
        yield ("usage", usage)
        return

    if fmt == "anthropic":
        url = _api(base, "/messages")
        payload = {
            "model": model,
            "max_tokens": int(max_tokens),
            "temperature": temperature,
            "stream": True,
            "messages": [{"role": "user", "content": prompt}],
        }
    else:
        url = _api(base, "/chat/completions")
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": int(max_tokens),
            "stream": True,
        }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=timeout, stream=True)
    except requests.exceptions.RequestException as e:
        raise APIError("Network error: %s" % _friendly_request_error(e))

    if r.status_code >= 400:
        err_detail = _stream_error(r)
        raise APIError("HTTP %s: %s" % (r.status_code, err_detail or _extract_error(r)))

    usage = {}
    if fmt == "anthropic":
        for line in r.iter_lines(decode_unicode=True):
            if not line:
                continue
            line = line.strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                obj = json.loads(data)
            except Exception:
                continue
            if obj.get("type") == "content_block_delta":
                d = obj.get("delta", {})
                if d.get("type") == "text_delta" and d.get("text"):
                    yield ("text", d["text"])
            elif obj.get("type") == "message_delta":
                du = obj.get("usage", {})
                if du:
                    usage = du
    else:
        for line in r.iter_lines(decode_unicode=True):
            if not line:
                continue
            line = line.strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                obj = json.loads(data)
            except Exception:
                continue
            choices = obj.get("choices") or []
            if choices:
                delta = choices[0].get("delta") or {}
                c = delta.get("content") or delta.get("reasoning_content") or delta.get("reasoning") or delta.get("thinking")
                if c:
                    yield ("text", str(c))
            u = obj.get("usage")
            if u:
                usage = u
    yield ("usage", usage)

