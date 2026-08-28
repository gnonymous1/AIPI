"""
reports.py - Usage Reports, CSV/JSON Export & Invoice Generation for AI Model Manager.
"""
import os
import csv
import json
import time
from db import get_connection, init_db
from analytics import calculate_cost

APP_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(APP_DIR, "reports")
MAX_REPORTS = 50  # Maximum number of report files to keep

def _ensure_dir():
    os.makedirs(REPORTS_DIR, exist_ok=True)

def _rotate_reports(max_files: int = MAX_REPORTS):
    """Delete the oldest report files if total count exceeds max_files."""
    try:
        files = sorted(
            [os.path.join(REPORTS_DIR, f) for f in os.listdir(REPORTS_DIR)
             if os.path.isfile(os.path.join(REPORTS_DIR, f))],
            key=os.path.getmtime
        )
        excess = len(files) - max_files
        for f in files[:excess]:
            try:
                os.remove(f)
            except Exception:
                pass
    except Exception:
        pass

def export_history_csv(limit: int = 1000) -> str:
    """Export run_history to a CSV file; returns the file path."""
    _ensure_dir()
    init_db()
    path = os.path.join(REPORTS_DIR, f"usage_report_{time.strftime('%Y%m%d_%H%M%S')}.csv")
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT timestamp, mode, provider, model, input_tokens, output_tokens, latency_ms, success
            FROM run_history ORDER BY id DESC LIMIT ?
        """, (limit,)).fetchall()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "mode", "provider", "model", "input_tokens",
                         "output_tokens", "latency_ms", "success", "cost_usd"])
        for r in rows:
            in_t = r["input_tokens"] or 0
            out_t = r["output_tokens"] or 0
            writer.writerow([r["timestamp"], r["mode"], r["provider"], r["model"],
                             in_t, out_t, r["latency_ms"], r["success"],
                             calculate_cost(r["model"] or "", in_t, out_t)])
    _rotate_reports()
    return path

def export_usage_json() -> str:
    """Export aggregated usage to a JSON file; returns the file path."""
    _ensure_dir()
    init_db()
    path = os.path.join(REPORTS_DIR, f"usage_summary_{time.strftime('%Y%m%d_%H%M%S')}.json")
    with get_connection() as conn:
        rows = conn.execute("SELECT model, provider, input_tokens, output_tokens, latency_ms, success FROM run_history").fetchall()
    total_cost = 0.0
    model_map = {}
    for r in rows:
        m = r["model"] or "unknown"
        in_t = r["input_tokens"] or 0
        out_t = r["output_tokens"] or 0
        cost = calculate_cost(m, in_t, out_t)
        total_cost += cost
        if m not in model_map:
            model_map[m] = {"requests": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
        model_map[m]["requests"] += 1
        model_map[m]["input_tokens"] += in_t
        model_map[m]["output_tokens"] += out_t
        model_map[m]["cost_usd"] += cost
    summary = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_requests": len(rows),
        "estimated_total_cost_usd": round(total_cost, 4),
        "by_model": model_map,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    _rotate_reports()
    return path

def generate_invoice(owner: str, billing_email: str = "") -> dict:
    """Generate an invoice summary for the current billing month."""
    _ensure_dir()
    init_db()
    month = time.strftime("%Y-%m")
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT model, provider, input_tokens, output_tokens, timestamp
            FROM run_history WHERE strftime('%Y-%m', timestamp) = ?
        """, (month,)).fetchall()
    total_cost = 0.0
    line_items = {}
    for r in rows:
        m = r["model"] or "unknown"
        in_t = r["input_tokens"] or 0
        out_t = r["output_tokens"] or 0
        cost = calculate_cost(m, in_t, out_t)
        total_cost += cost
        if m not in line_items:
            line_items[m] = {"provider": r["provider"] or "unknown", "requests": 0,
                             "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
        line_items[m]["requests"] += 1
        line_items[m]["input_tokens"] += in_t
        line_items[m]["output_tokens"] += out_t
        line_items[m]["cost_usd"] += cost
    invoice = {
        "invoice_number": f"INV-{month.replace('-', '')}-{len(rows)}",
        "owner": owner,
        "billing_email": billing_email,
        "billing_month": month,
        "total_requests": len(rows),
        "total_amount_usd": round(total_cost, 4),
        "line_items": line_items,
    }
    path = os.path.join(REPORTS_DIR, f"invoice_{month}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(invoice, f, indent=2)
    return {**invoice, "path": path}
