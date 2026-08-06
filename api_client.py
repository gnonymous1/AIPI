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
    headers = {"Content-Type": "application/json"}
    if api_key:
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


def _http_get(url, headers, timeout=12):
    try:
        return requests.get(url, headers=headers, timeout=timeout)
    except requests.exceptions.RequestException as e:
        raise APIError("Network error: %s" % _friendly_request_error(e))


def _http_post(url, headers, payload, timeout=120):
    try:
        return requests.post(url, headers=headers, json=payload, timeout=timeout)
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


def detect_format(base, api_key):
    """Try to auto-detect whether an endpoint speaks OpenAI or Anthropic."""
    base = normalize_base(base)
    for fmt in ("openai", "anthropic"):
        try:
            r = _http_get(_api(base, "/models"), _auth_headers(api_key, fmt))
            if r.status_code < 400:
                return fmt
        except Exception:
            continue
    return "openai"


def resolve_format(provider):
    fmt = (provider.get("format") or "auto").strip().lower()
    if fmt == "auto":
        fmt = detect_format(provider.get("base_url", ""), provider.get("api_key", ""))
    if fmt not in ("openai", "anthropic"):
        fmt = "openai"
    return fmt


def test_connection(base, api_key, fmt):
    """
    Return (ok, resolved_format, models_list, error_message).
    Raises APIError only on network errors; HTTP failures are returned as ok=False.
    """
    base = normalize_base(base)
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


def chat(provider, model, prompt, max_tokens=1024, temperature=0.7, timeout=120):
    """
    Send a single chat message to the model and return
    (text, raw_data, usage_dict, latency_seconds, used_format).
    Raises APIError on failure.
    """
    fmt = resolve_format(provider)
    base = normalize_base(provider.get("base_url", ""))
    api_key = provider.get("api_key", "")
    headers = _auth_headers(api_key, fmt)

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
    }
    r = _http_post(url, headers, payload, timeout)
    if r.status_code >= 400:
        raise APIError("HTTP %s: %s" % (r.status_code, _extract_error(r)))
    data = r.json()
    try:
        text = data["choices"][0]["message"]["content"]
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


def chat_stream(provider, model, prompt, max_tokens=1024, temperature=0.7, timeout=120):
    """
    Streaming variant of chat(). Yields ("text", delta) tuples as tokens arrive,
    then ("usage", usage_dict). The resolved format is yielded first as
    ("fmt", fmt). Raises APIError on network/HTTP failure.
    """
    fmt = resolve_format(provider)
    base = normalize_base(provider.get("base_url", ""))
    api_key = provider.get("api_key", "")
    headers = _auth_headers(api_key, fmt)
    yield ("fmt", fmt)

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
        raise APIError("Network error: %s" % e)

    if r.status_code >= 400:
        raise APIError("HTTP %s: %s" % (r.status_code, _stream_error(r)))

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
                c = delta.get("content")
                if c:
                    yield ("text", c)
            u = obj.get("usage")
            if u:
                usage = u
    yield ("usage", usage)

