"""
db.py - SQLite WAL Persistence Engine with Auto-Migration for AI Model Manager.
"""
import os
import sqlite3
import json
import time

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("AIMM_DATA_DIR", APP_DIR)
DB_PATH = os.path.join(DATA_DIR, "ai_model_manager.db")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
HISTORY_PATH = os.path.join(DATA_DIR, "history.json")

_db_initialized = False  # Guard: only run full init once per process

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def init_db():
    global _db_initialized
    if _db_initialized:
        return
    _db_initialized = True
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS providers (
                name TEXT PRIMARY KEY,
                format TEXT DEFAULT 'auto',
                base_url TEXT,
                api_key TEXT,
                default_model TEXT,
                notes TEXT,
                default_temperature REAL DEFAULT 0.7,
                default_max_tokens INTEGER DEFAULT 1024,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS run_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                mode TEXT,
                provider TEXT,
                model TEXT,
                prompt TEXT,
                response TEXT,
                latency_ms REAL,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                success INTEGER DEFAULT 1,
                error TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS virtual_keys (
                key_id TEXT PRIMARY KEY,
                name TEXT,
                secret_key TEXT,
                max_monthly_budget REAL DEFAULT 0.0,
                current_spend REAL DEFAULT 0.0,
                allowed_models TEXT DEFAULT '[]',
                rate_limit_rpm INTEGER DEFAULT 0,
                expires_at TEXT DEFAULT NULL,
                last_used_at TEXT DEFAULT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Ensure new columns exist if table was previously created
        for col, typedef in [
            ("allowed_models", "TEXT DEFAULT '[]'"),
            ("rate_limit_rpm", "INTEGER DEFAULT 0"),
            ("expires_at", "TEXT DEFAULT NULL"),
            ("last_used_at", "TEXT DEFAULT NULL"),
            ("status", "TEXT DEFAULT 'active'")
        ]:
            try:
                cursor.execute(f"ALTER TABLE virtual_keys ADD COLUMN {col} {typedef}")
            except Exception:
                pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS request_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                endpoint TEXT,
                provider TEXT,
                model TEXT,
                status_code INTEGER,
                latency_ms REAL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auto_profiles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT DEFAULT 'general',
                models TEXT NOT NULL,
                strategy TEXT DEFAULT 'priority_failover',
                max_tokens_budget INTEGER DEFAULT 0,
                max_cost_budget REAL DEFAULT 0.0,
                failover_on_rate_limit INTEGER DEFAULT 1,
                failover_on_token_exhaustion INTEGER DEFAULT 1,
                failover_on_error INTEGER DEFAULT 1,
                failover_on_timeout INTEGER DEFAULT 1,
                timeout_seconds REAL DEFAULT 25.0,
                is_system_preset INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

    _seed_default_profiles_if_empty()
    _migrate_from_json()

def _sync_config_file():
    """Write current providers from DB into config.json to maintain consistency."""
    try:
        raw_cfg = get_raw_config()
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(raw_cfg, f, indent=2)
    except Exception:
        pass

def _migrate_from_json():
    # Migrate config.json -> SQLite
    if os.path.exists(CONFIG_PATH):
        try:
            with get_connection() as conn:
                count = conn.execute("SELECT COUNT(*) FROM providers").fetchone()[0]
                if count == 0:
                    from vault import encrypt_key
                    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    for p in data.get("providers", []):
                        raw_key = p.get("api_key", "")
                        enc_key = encrypt_key(raw_key) if raw_key else ""
                        conn.execute("""
                            INSERT OR REPLACE INTO providers 
                            (name, format, base_url, api_key, default_model, notes, default_temperature, default_max_tokens)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            p.get("name", "").strip(),
                            p.get("format", "auto"),
                            p.get("base_url", "").strip(),
                            enc_key,
                            p.get("default_model", "").strip(),
                            p.get("notes", "").strip(),
                            float(p.get("default_temperature", 0.7)),
                            int(p.get("default_max_tokens", 1024))
                        ))
                    conn.commit()
        except Exception:
            pass

    # Migrate history.json -> SQLite
    if os.path.exists(HISTORY_PATH):
        try:
            with get_connection() as conn:
                count = conn.execute("SELECT COUNT(*) FROM run_history").fetchone()[0]
                if count == 0:
                    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                        hlist = json.load(f)
                    if isinstance(hlist, list):
                        for entry in hlist[:500]:
                            usage = entry.get("usage", {}) or {}
                            conn.execute("""
                                INSERT INTO run_history 
                                (timestamp, mode, provider, model, prompt, response, latency_ms, input_tokens, output_tokens, success, error)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                entry.get("timestamp", ""),
                                entry.get("mode", "chat"),
                                entry.get("provider", ""),
                                entry.get("model", ""),
                                entry.get("prompt", ""),
                                entry.get("response", ""),
                                float(entry.get("latency_ms", 0.0)),
                                int(usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0)),
                                int(usage.get("output_tokens", 0) or usage.get("completion_tokens", 0)),
                                1 if entry.get("ok", True) else 0,
                                entry.get("error", "")
                            ))
                        conn.commit()
        except Exception:
            pass

def get_providers():
    init_db()
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM providers ORDER BY created_at ASC").fetchall()
        from vault import decrypt_key
        result = []
        for r in rows:
            d = dict(r)
            d["api_key"] = decrypt_key(d.get("api_key", ""))
            result.append(d)
        return result

def get_raw_config():
    providers = get_providers()
    return {"providers": providers}

def save_provider(provider):
    init_db()
    name = (provider.get("name") or "").strip()
    if not name:
        raise ValueError("Provider name is required")
    from vault import encrypt_key
    enc_key = encrypt_key(provider.get("api_key", ""))
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO providers 
            (name, format, base_url, api_key, default_model, notes, default_temperature, default_max_tokens)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            provider.get("format", "auto"),
            (provider.get("base_url") or "").strip(),
            enc_key,
            (provider.get("default_model") or "").strip(),
            (provider.get("notes") or "").strip(),
            float(provider.get("default_temperature", 0.7)),
            int(provider.get("default_max_tokens", 1024))
        ))
        conn.commit()
    _sync_config_file()

add_or_update_provider = save_provider

def delete_provider(name):
    init_db()
    with get_connection() as conn:
        conn.execute("DELETE FROM providers WHERE LOWER(name) = LOWER(?)", (name.strip(),))
        conn.commit()
    _sync_config_file()

def save_all_config(config_data):
    init_db()
    providers = config_data.get("providers", [])
    from vault import encrypt_key
    with get_connection() as conn:
        conn.execute("DELETE FROM providers")
        for p in providers:
            name = (p.get("name") or "").strip()
            if not name:
                continue
            enc_key = encrypt_key(p.get("api_key", ""))
            conn.execute("""
                INSERT OR REPLACE INTO providers 
                (name, format, base_url, api_key, default_model, notes, default_temperature, default_max_tokens)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name,
                p.get("format", "auto"),
                (p.get("base_url") or "").strip(),
                enc_key,
                (p.get("default_model") or "").strip(),
                (p.get("notes") or "").strip(),
                float(p.get("default_temperature", 0.7)),
                int(p.get("default_max_tokens", 1024))
            ))
        conn.commit()
    _sync_config_file()

_log_insert_counter = 0

def _prune_logs_if_needed(conn, force=False):
    global _log_insert_counter
    _log_insert_counter += 1
    if not force and (_log_insert_counter % 500 != 0):
        return
    try:
        # Cap request_logs to last 100,000 entries
        conn.execute("""
            DELETE FROM request_logs WHERE id IN (
                SELECT id FROM request_logs ORDER BY id DESC LIMIT -1 OFFSET 100000
            )
        """)
        # Cap run_history to last 10,000 entries
        conn.execute("""
            DELETE FROM run_history WHERE id IN (
                SELECT id FROM run_history ORDER BY id DESC LIMIT -1 OFFSET 10000
            )
        """)
    except Exception:
        pass

def add_history_entry(entry):
    init_db()
    usage = entry.get("usage", {}) or {}
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO run_history 
            (timestamp, mode, provider, model, prompt, response, latency_ms, input_tokens, output_tokens, success, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S")),
            entry.get("mode", "chat"),
            entry.get("provider", ""),
            entry.get("model", ""),
            entry.get("prompt", ""),
            entry.get("response", ""),
            float(entry.get("latency_ms", 0.0)),
            int(usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0)),
            int(usage.get("output_tokens", 0) or usage.get("completion_tokens", 0)),
            1 if entry.get("ok", True) else 0,
            entry.get("error", "")
        ))
        _prune_logs_if_needed(conn)
        conn.commit()

def log_request(endpoint, provider, model, status_code, latency_ms):
    init_db()
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO request_logs (timestamp, endpoint, provider, model, status_code, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            time.strftime("%Y-%m-%d %H:%M:%S"),
            endpoint,
            provider,
            model,
            status_code,
            latency_ms
        ))
        _prune_logs_if_needed(conn)
        conn.commit()

def get_stats():
    init_db()
    with get_connection() as conn:
        total_requests = conn.execute("SELECT COUNT(*) FROM request_logs").fetchone()[0]
        total_runs = conn.execute("SELECT COUNT(*) FROM run_history").fetchone()[0]
        total_tokens = conn.execute("SELECT SUM(input_tokens + output_tokens) FROM run_history").fetchone()[0] or 0
        avg_latency = conn.execute("SELECT AVG(latency_ms) FROM run_history WHERE success = 1").fetchone()[0] or 0.0
        return {
            "total_requests": total_requests,
            "total_runs": total_runs,
            "total_tokens": total_tokens,
            "avg_latency_ms": round(avg_latency, 2)
        }


DEFAULT_SYSTEM_PROFILES = [
    {
        "id": "auto/best-free",
        "name": "Auto Best Free",
        "description": "100% Free models that automatically switch when rate limits or quotas are reached.",
        "category": "free",
        "models": ["hy3-free", "mimo-v2.5-free", "laguna-s-2.1-free", "deepseek-v4-flash-free", "muse-spark-1.2-contributor-free", "nemotron-3-ultra-free"],
        "strategy": "priority_failover",
        "failover_on_rate_limit": 1,
        "failover_on_token_exhaustion": 1,
        "failover_on_error": 1,
        "failover_on_timeout": 1,
        "timeout_seconds": 25.0,
        "is_system_preset": 1,
        "is_active": 1
    },
    {
        "id": "auto/free",
        "name": "Auto Free",
        "description": "Zero-cost rapid failover cascade across verified free models.",
        "category": "free",
        "models": ["hy3-free", "mimo-v2.5-free", "laguna-s-2.1-free", "deepseek-v4-flash-free"],
        "strategy": "priority_failover",
        "failover_on_rate_limit": 1,
        "failover_on_token_exhaustion": 1,
        "failover_on_error": 1,
        "failover_on_timeout": 1,
        "timeout_seconds": 25.0,
        "is_system_preset": 1,
        "is_active": 1
    },
    {
        "id": "auto/best-coding",
        "name": "Auto Best Coding",
        "description": "Top-tier coding models with automatic fallback across providers.",
        "category": "coding",
        "models": ["antigravity/claude-sonnet-4-6", "claude-3-7-sonnet-20250219", "deepseek-coder", "antigravity/gemini-2.5-flash", "hy3-free"],
        "strategy": "priority_failover",
        "failover_on_rate_limit": 1,
        "failover_on_token_exhaustion": 1,
        "failover_on_error": 1,
        "failover_on_timeout": 1,
        "timeout_seconds": 30.0,
        "is_system_preset": 1,
        "is_active": 1
    },
    {
        "id": "auto/coding",
        "name": "Auto Coding",
        "description": "High-efficiency coding agent sequence.",
        "category": "coding",
        "models": ["antigravity/claude-sonnet-4-6", "deepseek-coder", "codestral-latest", "antigravity/gemini-2.5-flash", "hy3-free"],
        "strategy": "priority_failover",
        "failover_on_rate_limit": 1,
        "failover_on_token_exhaustion": 1,
        "failover_on_error": 1,
        "failover_on_timeout": 1,
        "timeout_seconds": 30.0,
        "is_system_preset": 1,
        "is_active": 1
    },
    {
        "id": "auto/best-reasoning",
        "name": "Auto Best Reasoning",
        "description": "Complex logic, architecture, and step-by-step reasoning cascade.",
        "category": "reasoning",
        "models": ["claude-3-7-sonnet-20250219", "antigravity/claude-sonnet-4-6", "grok-4.6", "hy3-free", "mimo-v2.5-free"],
        "strategy": "priority_failover",
        "failover_on_rate_limit": 1,
        "failover_on_token_exhaustion": 1,
        "failover_on_error": 1,
        "failover_on_timeout": 1,
        "timeout_seconds": 35.0,
        "is_system_preset": 1,
        "is_active": 1
    },
    {
        "id": "auto/best-fast",
        "name": "Auto Best Fast",
        "description": "Lowest latency streaming models for instant interactive completions.",
        "category": "fast",
        "models": ["antigravity/gemini-2.5-flash", "gemini-2.0-flash", "hy3-free", "mimo-v2.5-free", "gpt-4o-mini"],
        "strategy": "priority_failover",
        "failover_on_rate_limit": 1,
        "failover_on_token_exhaustion": 1,
        "failover_on_error": 1,
        "failover_on_timeout": 1,
        "timeout_seconds": 20.0,
        "is_system_preset": 1,
        "is_active": 1
    },
    {
        "id": "auto/fast",
        "name": "Auto Fast",
        "description": "Rapid response generation cascade.",
        "category": "fast",
        "models": ["antigravity/gemini-2.5-flash", "hy3-free", "mimo-v2.5-free", "gemini-2.0-flash", "gpt-4o-mini"],
        "strategy": "priority_failover",
        "failover_on_rate_limit": 1,
        "failover_on_token_exhaustion": 1,
        "failover_on_error": 1,
        "failover_on_timeout": 1,
        "timeout_seconds": 20.0,
        "is_system_preset": 1,
        "is_active": 1
    },
    {
        "id": "auto/best-vision",
        "name": "Auto Best Vision",
        "description": "Multimodal visual reasoning and OCR models.",
        "category": "vision",
        "models": ["antigravity/gemini-2.5-flash", "antigravity/claude-sonnet-4-6", "gemini-2.0-flash", "gpt-4o"],
        "strategy": "priority_failover",
        "failover_on_rate_limit": 1,
        "failover_on_token_exhaustion": 1,
        "failover_on_error": 1,
        "failover_on_timeout": 1,
        "timeout_seconds": 30.0,
        "is_system_preset": 1,
        "is_active": 1
    },
    {
        "id": "auto/best-chat",
        "name": "Auto Best Chat",
        "description": "Natural conversational and helpful dialogue flow.",
        "category": "general",
        "models": ["antigravity/claude-sonnet-4-6", "antigravity/gemini-2.5-flash", "hy3-free", "mimo-v2.5-free"],
        "strategy": "priority_failover",
        "failover_on_rate_limit": 1,
        "failover_on_token_exhaustion": 1,
        "failover_on_error": 1,
        "failover_on_timeout": 1,
        "timeout_seconds": 25.0,
        "is_system_preset": 1,
        "is_active": 1
    },
    {
        "id": "auto/cheap",
        "name": "Auto Cost-Saver",
        "description": "Ultra low cost and free tier routing.",
        "category": "general",
        "models": ["hy3-free", "mimo-v2.5-free", "antigravity/gemini-2.5-flash", "gpt-4o-mini"],
        "strategy": "priority_failover",
        "failover_on_rate_limit": 1,
        "failover_on_token_exhaustion": 1,
        "failover_on_error": 1,
        "failover_on_timeout": 1,
        "timeout_seconds": 20.0,
        "is_system_preset": 1,
        "is_active": 1
    },
    {
        "id": "auto/smart",
        "name": "Auto Smart",
        "description": "Flagship intelligence model cascade.",
        "category": "general",
        "models": ["antigravity/claude-sonnet-4-6", "claude-3-7-sonnet-20250219", "hy3-free", "gpt-4o"],
        "strategy": "priority_failover",
        "failover_on_rate_limit": 1,
        "failover_on_token_exhaustion": 1,
        "failover_on_error": 1,
        "failover_on_timeout": 1,
        "timeout_seconds": 30.0,
        "is_system_preset": 1,
        "is_active": 1
    },
    {
        "id": "auto/offline",
        "name": "Auto Local/Airgapped",
        "description": "Local offline models (Ollama / LM Studio).",
        "category": "custom",
        "models": ["llama3.3", "qwen2.5", "mistral", "local-model"],
        "strategy": "priority_failover",
        "failover_on_rate_limit": 1,
        "failover_on_token_exhaustion": 1,
        "failover_on_error": 1,
        "failover_on_timeout": 1,
        "timeout_seconds": 30.0,
        "is_system_preset": 1,
        "is_active": 1
    }
]


def _seed_default_profiles_if_empty():
    """Ensure default system profiles are populated in auto_profiles table."""
    try:
        with get_connection() as conn:
            cnt = conn.execute("SELECT COUNT(*) FROM auto_profiles").fetchone()[0]
            if cnt == 0:
                for p in DEFAULT_SYSTEM_PROFILES:
                    conn.execute("""
                        INSERT OR IGNORE INTO auto_profiles (
                            id, name, description, category, models, strategy,
                            max_tokens_budget, max_cost_budget, failover_on_rate_limit,
                            failover_on_token_exhaustion, failover_on_error, failover_on_timeout,
                            timeout_seconds, is_system_preset, is_active
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        p["id"],
                        p["name"],
                        p["description"],
                        p.get("category", "general"),
                        json.dumps(p["models"]),
                        p.get("strategy", "priority_failover"),
                        p.get("max_tokens_budget", 0),
                        p.get("max_cost_budget", 0.0),
                        p.get("failover_on_rate_limit", 1),
                        p.get("failover_on_token_exhaustion", 1),
                        p.get("failover_on_error", 1),
                        p.get("failover_on_timeout", 1),
                        p.get("timeout_seconds", 25.0),
                        p.get("is_system_preset", 1),
                        p.get("is_active", 1)
                    ))
                conn.commit()
    except Exception:
        pass


def get_profiles(active_only=False):
    """Return all configured Auto-Profiles as a list of dictionaries."""
    init_db()
    with get_connection() as conn:
        query = "SELECT * FROM auto_profiles WHERE is_active = 1 ORDER BY is_system_preset DESC, name ASC" if active_only else "SELECT * FROM auto_profiles ORDER BY is_system_preset DESC, name ASC"
        rows = conn.execute(query).fetchall()
        profiles = []
        for r in rows:
            d = dict(r)
            try:
                d["models"] = json.loads(d["models"]) if isinstance(d["models"], str) else (d["models"] or [])
            except Exception:
                d["models"] = []
            profiles.append(d)
        return profiles


def get_profile(profile_id):
    """Retrieve a single profile by ID."""
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM auto_profiles WHERE id = ?", (profile_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        try:
            d["models"] = json.loads(d["models"]) if isinstance(d["models"], str) else (d["models"] or [])
        except Exception:
            d["models"] = []
        return d


def save_profile(p_data):
    """Insert or update a profile."""
    init_db()
    p_id = (p_data.get("id") or "").strip()
    if not p_id:
        p_id = "profile/" + (p_data.get("name", "custom")).lower().replace(" ", "-")

    models = p_data.get("models", [])
    if isinstance(models, str):
        try:
            models = json.loads(models)
        except Exception:
            models = [m.strip() for m in models.split(",") if m.strip()]

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO auto_profiles (
                id, name, description, category, models, strategy,
                max_tokens_budget, max_cost_budget, failover_on_rate_limit,
                failover_on_token_exhaustion, failover_on_error, failover_on_timeout,
                timeout_seconds, is_system_preset, is_active, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                description = excluded.description,
                category = excluded.category,
                models = excluded.models,
                strategy = excluded.strategy,
                max_tokens_budget = excluded.max_tokens_budget,
                max_cost_budget = excluded.max_cost_budget,
                failover_on_rate_limit = excluded.failover_on_rate_limit,
                failover_on_token_exhaustion = excluded.failover_on_token_exhaustion,
                failover_on_error = excluded.failover_on_error,
                failover_on_timeout = excluded.failover_on_timeout,
                timeout_seconds = excluded.timeout_seconds,
                is_active = excluded.is_active,
                updated_at = CURRENT_TIMESTAMP
        """, (
            p_id,
            p_data.get("name", p_id),
            p_data.get("description", ""),
            p_data.get("category", "custom"),
            json.dumps(models),
            p_data.get("strategy", "priority_failover"),
            int(p_data.get("max_tokens_budget", 0)),
            float(p_data.get("max_cost_budget", 0.0)),
            1 if p_data.get("failover_on_rate_limit", 1) else 0,
            1 if p_data.get("failover_on_token_exhaustion", 1) else 0,
            1 if p_data.get("failover_on_error", 1) else 0,
            1 if p_data.get("failover_on_timeout", 1) else 0,
            float(p_data.get("timeout_seconds", 25.0)),
            1 if p_data.get("is_system_preset", 0) else 0,
            1 if p_data.get("is_active", 1) else 0
        ))
        conn.commit()
    return get_profile(p_id)


def delete_profile(profile_id):
    """Delete a custom profile."""
    init_db()
    with get_connection() as conn:
        conn.execute("DELETE FROM auto_profiles WHERE id = ?", (profile_id,))
        conn.commit()
        return True
