"""
history.py - Lightweight JSON-backed history + stats for model test runs.

Stores every tester / benchmark run so the dashboard can show latency and
token-usage aggregates over time. Requires only the stdlib.
"""
import json
import os
import time

APP_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_PATH = os.path.join(APP_DIR, "history.json")
MAX_ENTRIES = 2000


def load():
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def save(entries):
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


def add(provider, model, prompt, latency, usage, format_used,
        ok=True, error=None, source="tester"):
    """Append a run and persist. Returns the updated entry list."""
    entries = load()
    usage = usage or {}
    entries.append({
        "ts": time.time(),
        "time_str": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": source,
        "provider": provider,
        "model": model,
        "prompt_preview": (prompt or "")[:80],
        "latency": latency,
        "format": format_used,
        "ok": ok,
        "error": error,
        "usage": usage,
    })
    if len(entries) > MAX_ENTRIES:
        entries = entries[-MAX_ENTRIES:]
    save(entries)
    return entries


def stats(entries=None):
    """Return aggregate stats over the given (or persisted) entries."""
    entries = entries if entries is not None else load()
    ok = [e for e in entries if e.get("ok")]
    lat = [e.get("latency") for e in ok
           if isinstance(e.get("latency"), (int, float))]
    total_in = sum(
        (e.get("usage") or {}).get("input_tokens")
        or (e.get("usage") or {}).get("prompt_tokens") or 0
        for e in ok)
    total_out = sum(
        (e.get("usage") or {}).get("output_tokens")
        or (e.get("usage") or {}).get("completion_tokens") or 0
        for e in ok)
    best = None
    if lat:
        best = min(lat)
    return {
        "total": len(entries),
        "ok": len(ok),
        "failed": len(entries) - len(ok),
        "runs": len(lat),
        "avg_latency": (sum(lat) / len(lat)) if lat else 0.0,
        "min_latency": min(lat) if lat else 0.0,
        "max_latency": max(lat) if lat else 0.0,
        "best_latency": best,
        "input_tokens": total_in,
        "output_tokens": total_out,
    }
