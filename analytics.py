"""
analytics.py - Cost Estimation, Financial Analytics & Performance Tracking for AI Model Manager.
"""
from db import get_connection, init_db, get_stats

# Model Pricing Table per 1,000,000 Tokens (USD) — updated 2025-08
PRICING_TABLE = {
    # OpenAI
    "gpt-4.1":              {"input": 2.00,  "output": 8.00},
    "gpt-4.1-mini":         {"input": 0.40,  "output": 1.60},
    "gpt-4.1-nano":         {"input": 0.10,  "output": 0.40},
    "gpt-4o":               {"input": 2.50,  "output": 10.00},
    "gpt-4o-mini":          {"input": 0.15,  "output": 0.60},
    "gpt-4-turbo":          {"input": 10.00, "output": 30.00},
    "o3-mini":              {"input": 1.10,  "output": 4.40},
    "o3":                   {"input": 10.00, "output": 40.00},
    "o1":                   {"input": 15.00, "output": 60.00},
    "o1-mini":              {"input": 1.10,  "output": 4.40},
    # Anthropic
    "claude-3-7-sonnet":    {"input": 3.00,  "output": 15.00},
    "claude-3-5-sonnet":    {"input": 3.00,  "output": 15.00},
    "claude-3-5-haiku":     {"input": 0.80,  "output": 4.00},
    "claude-3-opus":        {"input": 15.00, "output": 75.00},
    "claude-3-haiku":       {"input": 0.25,  "output": 1.25},
    # Google
    "gemini-2.5-pro":       {"input": 1.25,  "output": 10.00},
    "gemini-2.0-flash":     {"input": 0.10,  "output": 0.40},
    "gemini-2.0-pro":       {"input": 1.25,  "output": 5.00},
    "gemini-1.5-pro":       {"input": 1.25,  "output": 5.00},
    "gemini-1.5-flash":     {"input": 0.075, "output": 0.30},
    # DeepSeek
    "deepseek-v3":          {"input": 0.27,  "output": 1.10},
    "deepseek-chat":        {"input": 0.27,  "output": 1.10},
    "deepseek-reasoner":    {"input": 0.55,  "output": 2.19},
    "deepseek-r1":          {"input": 0.55,  "output": 2.19},
    "deepseek-coder":       {"input": 0.14,  "output": 0.28},
    # Meta Llama
    "llama-4-scout":        {"input": 0.18,  "output": 0.59},
    "llama-4-maverick":     {"input": 0.27,  "output": 0.85},
    "llama-3.3-70b":        {"input": 0.59,  "output": 0.79},
    "llama-3.1-405b":       {"input": 3.00,  "output": 3.00},
    # Mistral
    "mistral-large":        {"input": 2.00,  "output": 6.00},
    "mistral-medium":       {"input": 0.40,  "output": 2.00},
    "mistral-small":        {"input": 0.20,  "output": 0.60},
    "codestral":            {"input": 0.30,  "output": 0.90},
    # xAI
    "grok-3":               {"input": 3.00,  "output": 15.00},
    "grok-2":               {"input": 2.00,  "output": 10.00},
    # Other
    "command-r-plus":       {"input": 2.50,  "output": 10.00},
    "command-r":            {"input": 0.15,  "output": 0.60},
    "sonar-pro":            {"input": 3.00,  "output": 15.00},
    "sonar":                {"input": 1.00,  "output": 1.00},
    "qwen-max":             {"input": 0.40,  "output": 1.20},
    "qwen-plus":            {"input": 0.07,  "output": 0.21},
}

def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    if not model or (input_tokens <= 0 and output_tokens <= 0):
        return 0.0

    model_low = model.lower().strip()
    rate = None
    for key, pr in PRICING_TABLE.items():
        if key in model_low:
            rate = pr
            break

    if not rate:
        # Default average rate for unlisted cloud models
        rate = {"input": 0.50, "output": 1.50}

    cost_in = (input_tokens / 1000000.0) * rate["input"]
    cost_out = (output_tokens / 1000000.0) * rate["output"]
    return round(cost_in + cost_out, 6)

def get_model_performance_summary() -> list:
    """Per-model performance: request count, avg latency, error rate, est cost."""
    init_db()
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT model, provider, COUNT(*) as reqs, AVG(latency_ms) as avg_lat, 
                   SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as errors,
                   SUM(input_tokens) as in_tok, SUM(output_tokens) as out_tok
            FROM run_history GROUP BY model ORDER BY reqs DESC
        """).fetchall()

        summary = []
        for r in rows:
            m = r["model"] or "unknown"
            in_t = r["in_tok"] or 0
            out_t = r["out_tok"] or 0
            reqs = r["reqs"] or 0
            errs = r["errors"] or 0
            summary.append({
                "model": m,
                "provider": r["provider"] or "unknown",
                "requests": reqs,
                "avg_latency_ms": round(r["avg_lat"] or 0.0, 1),
                "error_rate_pct": round((errs / reqs * 100.0), 1) if reqs else 0.0,
                "total_tokens": in_t + out_t,
                "est_cost_usd": round(calculate_cost(m, in_t, out_t), 4)
            })
        return summary

def get_dashboard_analytics() -> dict:
    init_db()
    db_stats = get_stats()

    with get_connection() as conn:
        rows = conn.execute("SELECT model, input_tokens, output_tokens, latency_ms, success FROM run_history").fetchall()
        total_cost = 0.0
        provider_breakdown = {}
        for r in rows:
            m = r["model"] or "unknown"
            in_t = r["input_tokens"] or 0
            out_t = r["output_tokens"] or 0
            cost = calculate_cost(m, in_t, out_t)
            total_cost += cost

        # Request logs breakdown
        p_rows = conn.execute("SELECT provider, COUNT(*), AVG(latency_ms) FROM request_logs GROUP BY provider").fetchall()
        for pr in p_rows:
            provider_breakdown[pr[0] or "unknown"] = {
                "count": pr[1],
                "avg_latency_ms": round(pr[2] or 0.0, 1)
            }

    from cache import get_cache_stats
    cache_stats = get_cache_stats()

    return {
        "total_requests": db_stats["total_requests"],
        "total_runs": db_stats["total_runs"],
        "total_tokens": db_stats["total_tokens"],
        "estimated_total_cost_usd": round(total_cost, 4),
        "avg_latency_ms": db_stats["avg_latency_ms"],
        "provider_breakdown": provider_breakdown,
        "cache": cache_stats
    }
