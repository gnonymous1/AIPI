"""
cache.py - Zero-Latency Exact Match Prompt Cache Engine for AI Model Manager.
"""
import hashlib
import json
import time
from db import get_connection, init_db

_cache_stats = {"hits": 0, "misses": 0, "saved_latency_ms": 0.0}

def _init_cache_table():
    init_db()
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prompt_cache (
                cache_key TEXT PRIMARY KEY,
                model TEXT,
                prompt_hash TEXT,
                response_json TEXT,
                created_at REAL,
                ttl_seconds INTEGER DEFAULT 86400
            )
        """)
        conn.commit()

def _make_key(model: str, prompt: str, temperature: float, max_tokens: int) -> str:
    try:
        norm_temp = round(float(temperature), 4)
    except Exception:
        norm_temp = 0.7
    try:
        norm_tokens = int(max_tokens)
    except Exception:
        norm_tokens = 1024
    raw = f"{(model or '').strip().lower()}:{(prompt or '').strip()}:{norm_temp}:{norm_tokens}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def get_cached_response(model: str, prompt: str, temperature: float = 0.7, max_tokens: int = 1024) -> dict:
    _init_cache_table()
    key = _make_key(model, prompt, temperature, max_tokens)
    now = time.time()

    with get_connection() as conn:
        row = conn.execute("SELECT response_json, created_at, ttl_seconds FROM prompt_cache WHERE cache_key = ?", (key,)).fetchone()
        if row:
            created_at, ttl = row[1], row[2]
            if now - created_at < ttl:
                _cache_stats["hits"] += 1
                try:
                    data = json.loads(row[0])
                    data["cached"] = True
                    return data
                except Exception:
                    pass
            else:
                conn.execute("DELETE FROM prompt_cache WHERE cache_key = ?", (key,))
                conn.commit()

    _cache_stats["misses"] += 1
    return None

def save_cached_response(model: str, prompt: str, temperature: float, max_tokens: int, response_dict: dict, ttl_seconds: int = 86400):
    _init_cache_table()
    key = _make_key(model, prompt, temperature, max_tokens)
    now = time.time()
    resp_str = json.dumps(response_dict, ensure_ascii=False)

    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO prompt_cache (cache_key, model, prompt_hash, response_json, created_at, ttl_seconds)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (key, model, hashlib.md5(prompt.encode("utf-8")).hexdigest(), resp_str, now, ttl_seconds))
        conn.commit()

def clear_cache():
    _init_cache_table()
    with get_connection() as conn:
        conn.execute("DELETE FROM prompt_cache")
        conn.commit()

def get_cache_stats() -> dict:
    _init_cache_table()
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM prompt_cache").fetchone()[0]
        total_queries = _cache_stats["hits"] + _cache_stats["misses"]
        hit_rate = round((_cache_stats["hits"] / total_queries * 100.0), 1) if total_queries > 0 else 0.0
        return {
            "cached_entries": count,
            "hits": _cache_stats["hits"],
            "misses": _cache_stats["misses"],
            "hit_rate_pct": hit_rate
        }
