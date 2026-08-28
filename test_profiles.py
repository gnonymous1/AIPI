import urllib.request
import json

print("=" * 60)
print("  AIPI AUTO-PROFILERS & DYNAMIC TOKEN FAILOVER TEST SUITE")
print("=" * 60)

# 1. Test GET /v1/profiles
print("\n[1] Testing GET /v1/profiles...")
req = urllib.request.urlopen("http://127.0.0.1:11434/v1/profiles")
data = json.loads(req.read().decode())
profiles = data.get("profiles", [])
print(f"  -> SUCCESS! Found {len(profiles)} active profiles in SQLite database.")
for p in profiles[:4]:
    print(f"     * [{p['id']}] {p['name']} ({p['category']}) -> {p['models'][:3]}")

# 2. Test POST /v1/profiles/test
print("\n[2] Testing Cascade Resolution for 'auto/best-free'...")
payload = json.dumps({"profile_id": "auto/best-free"}).encode("utf-8")
req = urllib.request.Request("http://127.0.0.1:11434/v1/profiles/test", data=payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode())
    print(f"  -> SUCCESS! Resolved {res.get('routes_count')} fallback nodes:")
    for item in res.get("cascade", []):
        print(f"     - Provider: [{item['provider']}] Model: {item['model']}")

# 3. Test Live Chat with 'auto/best-free'
print("\n[3] Testing Live Chat Completion via 'auto/best-free'...")
chat_payload = json.dumps({
    "model": "auto/best-free",
    "messages": [{"role": "user", "content": "Respond with 'AIPI Profile Online'."}],
    "max_tokens": 30
}).encode("utf-8")
chat_req = urllib.request.Request("http://127.0.0.1:11434/v1/chat/completions", data=chat_payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(chat_req) as resp:
    chat_res = json.loads(resp.read().decode())
    selected_model = chat_res.get("model")
    content = chat_res["choices"][0]["message"]["content"]
    print(f"  -> SUCCESS! Routed model: {selected_model}")
    print(f"  -> Response: {content.strip()}")

# 4. Test Live Chat with 'auto/best-fast'
print("\n[4] Testing Live Chat Completion via 'auto/best-fast'...")
fast_payload = json.dumps({
    "model": "auto/best-fast",
    "messages": [{"role": "user", "content": "Respond with 'Fast Profile Online'."}],
    "max_tokens": 30
}).encode("utf-8")
fast_req = urllib.request.Request("http://127.0.0.1:11434/v1/chat/completions", data=fast_payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(fast_req) as resp:
    fast_res = json.loads(resp.read().decode())
    selected_model = fast_res.get("model")
    content = fast_res["choices"][0]["message"]["content"]
    print(f"  -> SUCCESS! Routed model: {selected_model}")
    print(f"  -> Response: {content.strip()}")

# 5. Test Custom Profile Creation
print("\n[5] Testing Custom Profile Creation via POST /v1/profiles/save...")
custom_prof = {
    "id": "profile/my-custom-cascade",
    "name": "My Custom Team Cascade",
    "category": "custom",
    "strategy": "priority_failover",
    "description": "Test custom profile cascade",
    "models": ["hy3-free", "mimo-v2.5-free", "laguna-s-2.1-free"]
}
save_payload = json.dumps(custom_prof).encode("utf-8")
save_req = urllib.request.Request("http://127.0.0.1:11434/v1/profiles/save", data=save_payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(save_req) as resp:
    save_res = json.loads(resp.read().decode())
    print(f"  -> SUCCESS! {save_res.get('message')}")

print("\n" + "=" * 60)
print("  ALL AUTO-PROFILERS TESTS PASSED CLEANLY!")
print("=" * 60)
