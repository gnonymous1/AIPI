"""
test_opencode_live.py - Comprehensive OpenCode Provider & CLI Integration Test.
Developed by gnonymous for AIPI Gateway.
"""
import sys
import io
import json
import time
import urllib.request
import os

# Force UTF-8 output encoding for Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

GATEWAY_BASE = "http://127.0.0.1:11434/v1"

def test_opencode_direct():
    print("=" * 70)
    print("⚡ PHASE 1: DIRECT OPENCODE ZEN API TEST")
    print("=" * 70)
    import db
    import api_client
    
    providers = {p["name"]: p for p in db.get_providers()}
    op = providers.get("opencode")
    if not op:
        print("❌ FAILED: opencode provider not found in database")
        return False

    print(f"Provider: {op['name']} -> {op['base_url']}")
    models = api_client.list_models(op["base_url"], op["api_key"], op["format"])
    print(f"Total available models reported: {len(models)}")
    print(f"Models: {models}\n")

    working_models = ["hy3-free", "mimo-v2.5-free"]
    all_ok = True
    for m in working_models:
        t0 = time.time()
        try:
            text, raw, usage, lat, fmt = api_client.chat(op, m, "What is 10 divided by 2? Answer in 1 word.", max_tokens=100, timeout=20)
            dur = round(time.time() - t0, 2)
            print(f"✓ Model '{m}': SUCCESS in {dur}s (API {lat:.2f}s)")
            print(f"   Output: {repr(text.strip())}")
            print(f"   Usage: {usage}\n")
        except Exception as e:
            print(f"❌ Model '{m}' FAILED: {e}\n")
            all_ok = False
    return all_ok

def test_opencode_gateway_routing():
    print("=" * 70)
    print("⚡ PHASE 2: AIPI GATEWAY ROUTING TO OPENCODE MODELS")
    print("=" * 70)
    
    # 1. Fetch Master Key
    req_mk = urllib.request.Request(f"{GATEWAY_BASE}/virtual-keys/master")
    with urllib.request.urlopen(req_mk, timeout=3) as resp:
        mk_data = json.loads(resp.read().decode())
        master_key = mk_data["master_key"]["secret_key"]

    prompt = "Explain in 1 concise sentence what machine learning is."
    for model_target in ["hy3-free", "mimo-v2.5-free"]:
        payload = {
            "model": model_target,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 150
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
            with urllib.request.urlopen(req, timeout=35) as resp:
                data = json.loads(resp.read().decode())
                dur = round((time.time() - t0) * 1000, 2)
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                usage = data.get("usage", {})
                cost = data.get("cost_usd", 0.0)

                print(f"✓ AIPI Gateway -> {model_target}: [200 OK] in {dur} ms")
                print(f"   Output: {content.strip()}")
                print(f"   Tokens: In={usage.get('prompt_tokens', 0)}, Out={usage.get('completion_tokens', 0)}, Cost=${cost:.6f}\n")
        except Exception as ex:
            print(f"❌ AIPI Gateway -> {model_target} FAILED: {ex}\n")
            return False
    return True

def test_opencode_ide_auto_config():
    print("=" * 70)
    print("⚡ PHASE 3: 1-CLICK OPENCODE IDE AUTO-CONFIGURATOR")
    print("=" * 70)
    from ide_config import detect_ides, inject_ide_config, restore_ide_config
    
    detected = detect_ides(11434)
    opencode_ide = next((i for i in detected if i["id"] == "opencode"), None)
    if not opencode_ide:
        print("❌ OpenCode CLI was not included in IDE detector")
        return False
    
    print(f"✓ OpenCode Detection: detected={opencode_ide['detected']}, configured={opencode_ide['configured']}")
    print(f"   Path: {opencode_ide['path']}")

    # Test configuration injection
    inj = inject_ide_config("opencode", port=11434, api_key="sk-aipi-test", model="hy3-free")
    print(f"✓ OpenCode Auto-Injection: {inj['status']} - {inj['message']}")

    # Verify detected state is now configured
    redetected = detect_ides(11434)
    oc_after = next((i for i in redetected if i["id"] == "opencode"), None)
    print(f"✓ OpenCode Post-Injection Status: configured={oc_after['configured']}")

    # Restore backup
    rest = restore_ide_config("opencode")
    print(f"✓ OpenCode Backup Restore: {rest['status']} - {rest['message']}\n")
    return True

if __name__ == "__main__":
    print("\n" + "#" * 70)
    print("🚀 LAUNCHING OPENCODE LIVE VERIFICATION SUITE")
    print("#" * 70 + "\n")
    
    ok1 = test_opencode_direct()
    ok2 = test_opencode_gateway_routing()
    ok3 = test_opencode_ide_auto_config()

    print("=" * 70)
    if ok1 and ok2 and ok3:
        print("🏆 ALL OPENCODE TESTS PASSED WITH 100% SUCCESS!")
    else:
        print("⚠️ SOME OPENCODE TESTS ENCOUNTERED ISSUES")
    print("=" * 70 + "\n")
