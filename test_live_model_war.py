"""
test_live_model_war.py - Live Execution of Single Model Testing & Multi-Model War via AIPI Multiple Models Router.
Developed by gnonymous.
"""
import sys
import io
import json
import time
import urllib.request

# Force UTF-8 output encoding for Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

GATEWAY_BASE = "http://127.0.0.1:11434/v1"

def run_single_model_test(model_id, prompt):
    print("=" * 70)
    print(f"🥊 PHASE 1: LIVE SINGLE MODEL TEST (AIPI GATEWAY -> MULTI-MODEL ROUTER)")
    print(f"   Model Target: {model_id}")
    print(f"   Prompt: \"{prompt}\"")
    print("=" * 70)

    # 1. Fetch Master Key
    req_mk = urllib.request.Request(f"{GATEWAY_BASE}/virtual-keys/master")
    with urllib.request.urlopen(req_mk, timeout=3) as resp:
        mk_data = json.loads(resp.read().decode())
        master_key = mk_data["master_key"]["secret_key"]

    payload = {
        "model": model_id,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }

    t0 = time.time()
    req = urllib.request.Request(
        f"{GATEWAY_BASE}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {master_key}"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            dur = round((time.time() - t0) * 1000, 2)
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
            cost = data.get("cost_usd", 0.0)

            print(f"\n[STATUS 200 OK] Received response in {dur} ms")
            print(f"Resolved Model: {data.get('model')}")
            print(f"Input Tokens:   {usage.get('prompt_tokens', 0)}")
            print(f"Output Tokens:  {usage.get('completion_tokens', 0)}")
            print(f"Cost USD:       ${cost:.6f}")
            print("-" * 70)
            print("Response Output:\n")
            print(content)
            print("-" * 70)
            return True
    except urllib.error.HTTPError as e:
        print(f"\n[HTTP ERROR {e.code}]: {e.read().decode()}")
        return False
    except Exception as ex:
        print(f"\n[ERROR]: {ex}")
        return False


def run_model_war_test(prompt, candidate_models):
    print("\n" + "=" * 70)
    print(f"⚔️  PHASE 2: LIVE MULTI-MODEL BATTLE ARENA (MODEL WAR)")
    print(f"   Prompt: \"{prompt}\"")
    print(f"   Contestants: {', '.join(candidate_models)}")
    print("=" * 70)

    arena_payload = {
        "prompt": prompt,
        "candidates": [
            {"provider": "AIPI Antigravity", "model": m} if any(m.startswith(pre) for pre in ("antigravity/", "claude/", "nvidia/"))
            else ({"provider": "opencode", "model": m} if "free" in m
            else {"provider": "AIPI", "model": m})
            for m in candidate_models
        ],
        "max_tokens": 150,
        "temperature": 0.7,
        "timeout": 30.0
    }

    t0 = time.time()
    req = urllib.request.Request(
        f"{GATEWAY_BASE}/arena/compare",
        data=json.dumps(arena_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=50) as resp:
            data = json.loads(resp.read().decode())
            tot_dur = round((time.time() - t0) * 1000, 2)
            results = data.get("results", [])

            print(f"\n[ARENA COMPLETED in {tot_dur} ms] — {len(results)} Models Evaluated in Parallel\n")
            
            for idx, r in enumerate(results, 1):
                status_symbol = "🏆" if r.get("ok") else "❌"
                print(f"Contestant #{idx}: {status_symbol} {r.get('model')} ({r.get('provider')})")
                if r.get("ok"):
                    print(f"  • Latency:     {r.get('latency_ms')} ms")
                    print(f"  • Output Size: {r.get('output_tokens')} tokens (Total: {r.get('total_tokens')})")
                    print(f"  • Cost:        ${r.get('cost_usd', 0.0):.6f}")
                    print(f"  • Response:\n    \"{r.get('response', '').strip()}\"\n")
                else:
                    print(f"  • Error:       {r.get('error')}\n")
            print("=" * 70)
            return True
    except Exception as ex:
        print(f"\n[ARENA ERROR]: {ex}")
        return False


if __name__ == "__main__":
    test_prompt = "Explain in 2 sentences why asynchronous non-blocking I/O is faster than synchronous I/O."
    
    # 1. Single Model Test with Antigravity live model
    run_single_model_test("antigravity/claude-sonnet-4-6", test_prompt)
    
    # 2. Single Model Test with OpenCode live model
    run_single_model_test("hy3-free", "State the core benefit of concurrency in 1 sentence.")
    
    # 3. Battle Arena / Model War between real live models in parallel
    candidates = ["antigravity/claude-sonnet-4-6", "hy3-free", "mimo-v2.5-free", "auto/best-fast"]
    run_model_war_test(test_prompt, candidates)
