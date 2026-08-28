"""
ratelimit.py - Token Bucket Rate Limiting for AI Model Manager (per key / per IP).
"""
import time
import threading

_buckets = {}  # {scope: {"tokens": float, "last_refill": float, "capacity": float, "rate": float}}
_lock = threading.Lock()
_default_rate = 60.0   # tokens per minute
_default_capacity = 60.0

def _refill(scope):
    b = _buckets[scope]
    now = time.time()
    elapsed = now - b["last_refill"]
    b["tokens"] = min(b["capacity"], b["tokens"] + elapsed * (b["rate"] / 60.0))
    b["last_refill"] = now

def check_rate_limit(scope: str, rate_per_minute: float = None, capacity: float = None) -> dict:
    """
    Token-bucket check. Returns {"allowed": bool, "retry_after_s": float, "remaining": float}.
    """
    now = time.time()
    with _lock:
        # cleanup stale buckets older than 10 min
        stale = [s for s, b in _buckets.items() if now - b["last_refill"] > 600]
        for s in stale:
            del _buckets[s]

        if scope not in _buckets:
            cap = capacity if capacity is not None else _default_capacity
            _buckets[scope] = {
                "tokens": min(cap, max(5.0, cap * 0.25)) if capacity is None else cap,
                "last_refill": now,
                "capacity": cap,
                "rate": rate_per_minute if rate_per_minute is not None else _default_rate,
            }
        _refill(scope)
        b = _buckets[scope]
        if b["tokens"] >= 1:
            b["tokens"] -= 1
            return {"allowed": True, "retry_after_s": 0.0, "remaining": round(b["tokens"], 2)}
        # need to wait for one token
        wait = ((1 - b["tokens"]) / (b["rate"] / 60.0)) if b["rate"] > 0 else 60.0
        return {"allowed": False, "retry_after_s": round(wait, 1), "remaining": 0.0}

def get_rate_limit_status() -> dict:
    with _lock:
        return {
            "tracked_scopes": len(_buckets),
            "scopes": {s: {"remaining": round(b["tokens"], 2), "rate_per_min": b["rate"]} for s, b in _buckets.items()}
        }
