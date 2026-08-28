"""
router.py - Intelligent Profile Router, Virtual Aliasing & Dynamic Token/Quota Failover Engine for AIPI.
"""
import time
import threading

# Cooldown tracking
_cooldowns = {}         # {provider_name: cooldown_until_timestamp}
_model_cooldowns = {}   # {(provider_name, model_id): cooldown_until_timestamp}
_stats = {"total_routed": 0, "fallbacks_triggered": 0, "cooldown_hits": 0, "quota_failovers": 0}
_lock = threading.Lock()

# Fallback virtual aliases if DB is unavailable
VIRTUAL_ALIASES = {
    "auto/best-free":      ["hy3-free", "mimo-v2.5-free", "laguna-s-2.1-free", "deepseek-v4-flash-free", "muse-spark-1.2-contributor-free"],
    "auto/free":           ["hy3-free", "mimo-v2.5-free", "laguna-s-2.1-free", "deepseek-v4-flash-free"],
    "auto/best-fast":      ["antigravity/gemini-2.5-flash", "gemini-2.0-flash", "hy3-free", "mimo-v2.5-free", "gpt-4o-mini"],
    "auto/fast":           ["antigravity/gemini-2.5-flash", "hy3-free", "mimo-v2.5-free", "gemini-2.0-flash", "gpt-4o-mini"],
    "auto/best-coding":    ["antigravity/claude-sonnet-4-6", "claude-3-7-sonnet-20250219", "deepseek-coder", "antigravity/gemini-2.5-flash", "hy3-free"],
    "auto/coding":         ["antigravity/claude-sonnet-4-6", "deepseek-coder", "codestral-latest", "antigravity/gemini-2.5-flash", "hy3-free"],
    "auto/best-reasoning": ["claude-3-7-sonnet-20250219", "antigravity/claude-sonnet-4-6", "grok-4.6", "hy3-free", "mimo-v2.5-free"],
    "auto/best-vision":    ["antigravity/gemini-2.5-flash", "antigravity/claude-sonnet-4-6", "gemini-2.0-flash", "gpt-4o"],
    "auto/best-chat":      ["antigravity/claude-sonnet-4-6", "antigravity/gemini-2.5-flash", "hy3-free", "mimo-v2.5-free"],
    "auto/cheap":          ["hy3-free", "mimo-v2.5-free", "antigravity/gemini-2.5-flash", "gpt-4o-mini"],
    "auto/smart":          ["antigravity/claude-sonnet-4-6", "claude-3-7-sonnet-20250219", "hy3-free", "gpt-4o"],
    "auto/best":           ["antigravity/claude-sonnet-4-6", "claude-3-7-sonnet-20250219", "hy3-free", "gpt-4o"],
    "auto/offline":        ["llama3.3", "qwen2.5", "mistral", "local-model"]
}

# Known model patterns for automatic provider affinity
OPENCODE_KNOWN_MODELS = {
    "hy3-free", "mimo-v2.5-free", "laguna-s-2.1-free", "grok-4.6", "muse-spark-1.2",
    "muse-spark-1.2-contributor-free", "nemotron-3-ultra-free", "nemotron-3.5-lightning-free",
    "deepseek-v4-flash-free"
}

def is_quota_or_rate_limit_error(err_msg: str, status_code: int = 0) -> bool:
    """Identify if an error is due to rate limiting, token exhaustion, or quota limit."""
    if status_code in (429, 402):
        return True
    low = (str(err_msg) or "").lower()
    keywords = [
        "quota", "rate limit", "rate_limit", "too many requests", "insufficient_quota",
        "out of credits", "token limit", "exceeded", "balance", "billing", "credit exhausted",
        "resource has been exhausted", "overloaded", "capacity", "usage limit"
    ]
    return any(k in low for k in keywords)

def is_provider_cooling(provider_name: str) -> bool:
    with _lock:
        until = _cooldowns.get(provider_name, 0)
        if time.time() < until:
            return True
        elif provider_name in _cooldowns:
            del _cooldowns[provider_name]
    return False

def is_model_cooling(provider_name: str, model_id: str) -> bool:
    with _lock:
        key = (provider_name, model_id)
        until = _model_cooldowns.get(key, 0)
        if time.time() < until:
            return True
        elif key in _model_cooldowns:
            del _model_cooldowns[key]
    return False

def mark_provider_status(provider_name: str, success: bool, status_code: int = 200, latency_ms: float = 0.0, model_id: str = None, error_msg: str = None):
    with _lock:
        now = time.time()
        if success:
            if provider_name in _cooldowns:
                del _cooldowns[provider_name]
            if model_id and (provider_name, model_id) in _model_cooldowns:
                del _model_cooldowns[(provider_name, model_id)]
        else:
            is_quota = is_quota_or_rate_limit_error(error_msg or "", status_code)
            if is_quota:
                _stats["quota_failovers"] += 1
                _stats["fallbacks_triggered"] += 1
                # Put specific model on 90s cooldown
                if model_id:
                    _model_cooldowns[(provider_name, model_id)] = now + 90.0
            elif status_code in (500, 502, 503, 504):
                # Put entire provider on 45s cooldown for general server outages
                _cooldowns[provider_name] = now + 45.0
                _stats["cooldown_hits"] += 1

def _match_provider_for_model(model_name: str, providers: list):
    """Find the most appropriate provider for a given model name."""
    low_m = model_name.lower()
    
    # 1. Opencode specific models
    if low_m in OPENCODE_KNOWN_MODELS or low_m.startswith("opencode/"):
        for p in providers:
            if p.get("name", "").strip().lower() == "opencode":
                return p
                
    # 2. Antigravity / Claude / Native AIPI prefixes
    if any(low_m.startswith(pre) for pre in ("antigravity/", "claude/", "kilocode/", "kc/", "nvidia/", "agy/", "jules/")):
        for p in providers:
            if "anti" in p.get("name", "").strip().lower() or "google" in p.get("name", "").strip().lower():
                return p

    # 3. Match by default_model or provider name in model string
    for p in providers:
        p_name = p.get("name", "").strip().lower()
        if p_name and p_name in low_m:
            return p
        if (p.get("default_model") or "").lower() == low_m:
            return p

    return None

def resolve_route(requested_model: str, providers: list, target_provider_name: str = None) -> list:
    """
    Resolve requested_model or profile into a prioritized list of candidate tuples:
    [(provider_dict, actual_model_id), ...]
    """
    with _lock:
        _stats["total_routed"] += 1

    if not providers:
        return []

    # Filter out cooling providers if healthy ones are available
    healthy_providers = [p for p in providers if not is_provider_cooling(p.get("name", ""))]
    candidates_providers = healthy_providers if healthy_providers else providers

    req = (requested_model or "").strip()

    # Strip custom gateway/client prefixes like aipi/auto/fast or aipi:auto/fast
    for g_prefix in ("aipi/", "aipi:", "gateway/", "local/", "default/"):
        if req.lower().startswith(g_prefix):
            req = req[len(g_prefix):].strip()
            break

    # 1. Look up in Dynamic DB Profiles
    try:
        from db import get_profiles
        db_profiles = get_profiles(active_only=True)
        matched_profile = next((p for p in db_profiles if p.get("id") == req or p.get("name", "").lower() == req.lower()), None)
        if matched_profile and matched_profile.get("models"):
            candidate_models = matched_profile["models"]
            routes = []
            for target_m in candidate_models:
                best_p = _match_provider_for_model(target_m, candidates_providers)
                if best_p:
                    # If this specific model is currently on cooldown, push to tail
                    if not is_model_cooling(best_p.get("name", ""), target_m):
                        routes.append((best_p, target_m))
                else:
                    for p in candidates_providers:
                        if not is_model_cooling(p.get("name", ""), target_m):
                            routes.append((p, target_m))
            
            # If all candidates were cooling, append all to try anyway
            if not routes:
                for target_m in candidate_models:
                    best_p = _match_provider_for_model(target_m, candidates_providers)
                    routes.append((best_p or candidates_providers[0], target_m))

            if routes:
                return routes
    except Exception:
        pass

    # 2. Check Static Virtual Aliases
    if req in VIRTUAL_ALIASES:
        model_candidates = VIRTUAL_ALIASES[req]
        routes = []
        for target_m in model_candidates:
            best_p = _match_provider_for_model(target_m, candidates_providers)
            if best_p:
                routes.append((best_p, target_m))
            else:
                for p in candidates_providers:
                    routes.append((p, target_m))
        if routes:
            return routes

    # 3. Specific target provider requested?
    if target_provider_name:
        for p in candidates_providers:
            if (p.get("name") or "").strip().lower() == target_provider_name.strip().lower():
                model_id = req or p.get("default_model") or "gpt-4o"
                return [(p, model_id)]

    # 4. Handle explicit provider prefix e.g. "opencode/hy3-free" or "antigravity/claude-sonnet-4-6"
    if "/" in req:
        prefix, rest = req.split("/", 1)
        for p in candidates_providers:
            if p.get("name", "").strip().lower() == prefix.lower():
                return [(p, rest)]

    # 5. Check if this model is known to belong to a specific provider
    preferred_p = _match_provider_for_model(req, candidates_providers)
    routes = []
    if preferred_p:
        routes.append((preferred_p, req))
        for p in candidates_providers:
            if p != preferred_p:
                routes.append((p, req))
        return routes

    # 6. Direct match or fallback chain across configured providers
    primary_p = candidates_providers[0]
    primary_model = req if req else (primary_p.get("default_model") or "gpt-4o")
    routes.append((primary_p, primary_model))

    for p in candidates_providers[1:]:
        fallback_model = req if req else (p.get("default_model") or "gpt-4o")
        routes.append((p, fallback_model))

    return routes

def get_router_stats() -> dict:
    with _lock:
        now = time.time()
        active_cooldowns = {p: round(until - now, 1) for p, until in _cooldowns.items() if now < until}
        active_model_cooldowns = {f"{k[0]}/{k[1]}": round(until - now, 1) for k, until in _model_cooldowns.items() if now < until}
        return {
            "total_routed": _stats["total_routed"],
            "fallbacks_triggered": _stats["fallbacks_triggered"],
            "quota_failovers": _stats["quota_failovers"],
            "cooldown_hits": _stats["cooldown_hits"],
            "active_provider_cooldowns": active_cooldowns,
            "active_model_cooldowns": active_model_cooldowns,
            "virtual_aliases_count": len(VIRTUAL_ALIASES)
        }
