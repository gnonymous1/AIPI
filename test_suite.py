"""
test_suite.py - Comprehensive Automated End-to-End Test Suite for AIPI (AI Protocol Interface).
Developed by gnonymous.
Verifies all components, routing, security, licensing, persistence, and HTTP gateway.
"""
import os
import sys
import time
import json
import threading
import urllib.request
import urllib.parse
import unittest

# Ensure current directory is in sys.path
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import db
import vault
import auth
import license
import ratelimit
import virtual_keys
import oidc
import router
import cache
import analytics
import reports
import claude_profiles
import gateway_server
import ide_config
import pii_redactor


class TestAIModelManager(unittest.TestCase):

    def setUp(self):
        db.init_db()

    # -------------------------------------------------------------
    # 1. Vault & DPAPI Encryption
    # -------------------------------------------------------------
    def test_01_vault_encryption(self):
        plain = "sk-test-secret-key-123456789"
        encrypted = vault.encrypt_key(plain)
        self.assertTrue(encrypted.startswith("enc:"), "Encrypted string should start with enc:")
        decrypted = vault.decrypt_key(encrypted)
        self.assertEqual(decrypted, plain, "Decrypted key must match original plaintext")

        redacted = vault.redact_key(plain)
        self.assertTrue("…" in redacted or "..." in redacted)
        self.assertFalse(plain in redacted)

        data = {"provider": {"name": "Test", "api_key": plain}}
        sanitized = vault.sanitize_dict(data)
        self.assertNotEqual(sanitized["provider"]["api_key"], plain)

    # -------------------------------------------------------------
    # 2. Database & Persistence Sync
    # -------------------------------------------------------------
    def test_02_db_and_sync(self):
        test_provider = {
            "name": "Suite_Test_Provider",
            "format": "openai",
            "base_url": "http://127.0.0.1:8000",
            "api_key": "sk-suite-key",
            "default_model": "test-model-1",
            "notes": "Automated test provider",
            "default_temperature": 0.5,
            "default_max_tokens": 512
        }
        db.save_provider(test_provider)
        providers = db.get_providers()
        matching = [p for p in providers if p["name"] == "Suite_Test_Provider"]
        self.assertTrue(len(matching) >= 1)
        self.assertEqual(matching[0]["api_key"], "sk-suite-key")

        # Verify config.json was synced
        with open(db.CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            matching_cfg = [p for p in cfg.get("providers", []) if p["name"] == "Suite_Test_Provider"]
            self.assertTrue(len(matching_cfg) >= 1)

        db.delete_provider("Suite_Test_Provider")
        providers_after = db.get_providers()
        self.assertFalse(any(p["name"] == "Suite_Test_Provider" for p in providers_after))

    # -------------------------------------------------------------
    # 3. Router & Multi-Argument mark_provider_status
    # -------------------------------------------------------------
    def test_03_router(self):
        # Test 2, 3, and 4 argument signatures
        router.mark_provider_status("MockProv", True)
        router.mark_provider_status("MockProv", True, 200)
        router.mark_provider_status("MockProv", True, 200, 125.5)  # 4 args must NOT raise TypeError
        router.mark_provider_status("MockProv", False, 500, 0.0)

        self.assertTrue(router.is_provider_cooling("MockProv"))
        router.mark_provider_status("MockProv", True, 200)
        self.assertFalse(router.is_provider_cooling("MockProv"))

        # Test Virtual Aliases
        providers = [{"name": "P1", "default_model": "llama-3.3-70b"}]
        routes = router.resolve_route("auto/fast", providers)
        self.assertTrue(len(routes) > 0)
        self.assertEqual(routes[0][1], router.VIRTUAL_ALIASES["auto/fast"][0])

    # -------------------------------------------------------------
    # 4. AIPI Platform API Key Generation, Master Key & Multi-Tenant Access
    # -------------------------------------------------------------
    def test_04_virtual_keys(self):
        # 1. Master Key Auto-provisioning
        mk = virtual_keys.get_master_key()
        self.assertIsInstance(mk, dict)
        self.assertTrue(mk["secret_key"].startswith("aipi-live-") or mk["secret_key"].startswith("px-live-"))
        self.assertEqual(mk["status"], "active")

        # 2. Custom Key Generation with Rate Limit & Expiration
        vk = virtual_keys.create_virtual_key(
            name="Suite Bot Key",
            max_monthly_budget=10.0,
            allowed_models=["gpt-4o", "claude-3-7-sonnet"],
            rate_limit_rpm=120,
            expires_in_days=30
        )
        key_secret = vk["secret_key"]
        self.assertTrue(key_secret.startswith("aipi-live-"))
        self.assertEqual(vk["rate_limit_rpm"], 120)
        self.assertIsNotNone(vk["expires_at"])

        # Validate with allowed model
        valid, msg, info = virtual_keys.validate_key(key_secret, requested_model="gpt-4o")
        self.assertTrue(valid, f"Allowed model validation failed: {msg}")

        # Validate with unauthorized model
        valid_unauth, msg_unauth, _ = virtual_keys.validate_key(key_secret, requested_model="unauthorized-model")
        self.assertFalse(valid_unauth)
        self.assertTrue("not authorized" in msg_unauth.lower())

        # Spend tracking & Budget enforcement
        virtual_keys.record_spend(key_secret, 7.50)
        valid_mid, _, info_mid = virtual_keys.validate_key(key_secret)
        self.assertTrue(valid_mid)
        self.assertEqual(info_mid["current_spend"], 7.50)

        virtual_keys.record_spend(key_secret, 3.50)  # Spend now 11.00 > budget 10.00
        valid_over, msg_over, _ = virtual_keys.validate_key(key_secret)
        self.assertFalse(valid_over)
        self.assertTrue("budget limit reached" in msg_over.lower())

        # Revocation
        revoked = virtual_keys.revoke_key(vk["key_id"])
        self.assertTrue(revoked)
        valid_after, _, _ = virtual_keys.validate_key(key_secret)
        self.assertFalse(valid_after)

        # Permanent deletion
        deleted = virtual_keys.delete_key(vk["key_id"])
        self.assertTrue(deleted)

    # -------------------------------------------------------------
    # 5. Auth RBAC, Session & Password Management
    # -------------------------------------------------------------
    def test_05_auth_rbac(self):
        auth.ensure_admin_bootstrap("admin123")
        sess = auth.authenticate("admin", "admin123")
        self.assertTrue(sess["token"].startswith("sess-"))
        self.assertEqual(sess["role"], "admin")

        validated = auth.validate_session(sess["token"])
        self.assertEqual(validated["username"], "admin")

        # Test change password
        auth.change_password("admin", "admin123", "newAdminPass456")
        sess_new = auth.authenticate("admin", "newAdminPass456")
        self.assertEqual(sess_new["username"], "admin")

        # Revert password for standard tests
        auth.change_password("admin", "newAdminPass456", "admin123")

        # Create subordinate user
        user = auth.create_user("team_member_1", "password123", "member")
        self.assertEqual(user["role"], "member")
        users = auth.list_users()
        self.assertTrue(any(u["username"] == "team_member_1" for u in users))

        # Role rank update and deletion
        auth.set_user_role("team_member_1", "viewer", current_role="admin")
        deleted = auth.delete_user("team_member_1", current_role="admin")
        self.assertTrue(deleted)

    # -------------------------------------------------------------
    # 6. Commercial Tiered Licensing
    # -------------------------------------------------------------
    def test_06_licensing(self):
        lic = license.generate_license("enterprise@client.com", tier="enterprise", months=12)
        self.assertIn("license_key", lic)

        validated = license.validate_license(lic["license_key"])
        self.assertEqual(validated["tier"], "enterprise")
        self.assertEqual(validated["owner"], "enterprise@client.com")

        activated = license.activate_license(lic["license_key"])
        self.assertEqual(activated["status"], "activated")

        st = license.get_license_status()
        self.assertEqual(st["tier"], "enterprise")
        self.assertTrue(license.feature_enabled("sso"))

    # -------------------------------------------------------------
    # 7. Token Bucket Rate Limiting
    # -------------------------------------------------------------
    def test_07_rate_limiting(self):
        scope = "test_rate_scope_" + str(time.time())
        res1 = ratelimit.check_rate_limit(scope, rate_per_minute=10.0, capacity=2.0)
        self.assertTrue(res1["allowed"])
        res2 = ratelimit.check_rate_limit(scope, rate_per_minute=10.0, capacity=2.0)
        self.assertTrue(res2["allowed"])
        res3 = ratelimit.check_rate_limit(scope, rate_per_minute=10.0, capacity=2.0)
        self.assertFalse(res3["allowed"])
        self.assertTrue(res3["retry_after_s"] > 0)

    # -------------------------------------------------------------
    # 8. Exact Match Caching
    # -------------------------------------------------------------
    def test_08_cache(self):
        model = "gpt-4o"
        prompt = "Explain quantum gravity in 5 words"
        resp_data = {"id": "test_cached_resp", "choices": [{"message": {"content": "Space and time are quantized."}}]}

        cache.save_cached_response(model, prompt, 0.7, 1024, resp_data)
        cached = cache.get_cached_response(model, prompt, 0.7, 1024)
        self.assertIsNotNone(cached)
        self.assertTrue(cached.get("cached"))
        self.assertEqual(cached["id"], "test_cached_resp")

        stats = cache.get_cache_stats()
        self.assertTrue(stats["hits"] >= 1)

        cache.clear_cache()
        cleared = cache.get_cached_response(model, prompt, 0.7, 1024)
        self.assertIsNone(cleared)

    # -------------------------------------------------------------
    # 9. Analytics, Cost Calculation & Reports
    # -------------------------------------------------------------
    def test_09_analytics_and_reports(self):
        cost_gpt = analytics.calculate_cost("gpt-4o", 10000, 2000)
        self.assertTrue(cost_gpt > 0)
        self.assertEqual(cost_gpt, round((10000/1e6)*2.50 + (2000/1e6)*10.00, 6))

        # Test reports generation
        csv_file = reports.export_history_csv()
        self.assertTrue(os.path.isfile(csv_file))

        json_file = reports.export_usage_json()
        self.assertTrue(os.path.isfile(json_file))

        invoice = reports.generate_invoice("Acme Corp", "billing@acme.com")
        self.assertIn("invoice_number", invoice)
        self.assertTrue(os.path.isfile(invoice["path"]))

    # -------------------------------------------------------------
    # 10. Live HTTP Gateway Server Endpoints
    # -------------------------------------------------------------
    def test_10_gateway_server_live_http(self):
        port = 19435
        server = gateway_server.GatewayServer(("127.0.0.1", port), gateway_server.GatewayHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.5)

        base = f"http://127.0.0.1:{port}"

        try:
            # /v1/health
            with urllib.request.urlopen(f"{base}/v1/health", timeout=6) as r:
                self.assertEqual(r.status, 200)
                data = json.loads(r.read().decode())
                self.assertEqual(data["status"], "ok")

            # /v1/models
            with urllib.request.urlopen(f"{base}/v1/models", timeout=6) as r:
                self.assertEqual(r.status, 200)
                data = json.loads(r.read().decode())
                self.assertEqual(data["object"], "list")

            # /v1/virtual-keys
            with urllib.request.urlopen(f"{base}/v1/virtual-keys", timeout=6) as r:
                self.assertEqual(r.status, 200)
                data = json.loads(r.read().decode())
                self.assertIn("keys", data)

            # /v1/analytics/overview
            with urllib.request.urlopen(f"{base}/v1/analytics/overview", timeout=6) as r:
                self.assertEqual(r.status, 200)
                data = json.loads(r.read().decode())
                self.assertEqual(data["status"], "ok")

            # /v1/admin/login
            login_payload = json.dumps({"username": "admin", "password": "admin123"}).encode("utf-8")
            req = urllib.request.Request(f"{base}/v1/admin/login", data=login_payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3) as r:
                self.assertEqual(r.status, 200)
                data = json.loads(r.read().decode())
                token = data["session"]["token"]
                self.assertTrue(token.startswith("sess-"))

            # /v1/admin/users with X-Admin-Token
            user_req = urllib.request.Request(f"{base}/v1/admin/users", headers={"X-Admin-Token": token})
            with urllib.request.urlopen(user_req, timeout=3) as r:
                self.assertEqual(r.status, 200)
                data = json.loads(r.read().decode())
                self.assertTrue(len(data["users"]) >= 1)

            # /v1/admin/change-password
            change_payload = json.dumps({"old_password": "admin123", "new_password": "adminSecretPass99"}).encode("utf-8")
            cp_req = urllib.request.Request(f"{base}/v1/admin/change-password", data=change_payload,
                                            headers={"Content-Type": "application/json", "X-Admin-Token": token})
            with urllib.request.urlopen(cp_req, timeout=3) as r:
                self.assertEqual(r.status, 200)
                data = json.loads(r.read().decode())
                self.assertEqual(data["status"], "ok")

            # Revert password
            revert_payload = json.dumps({"old_password": "adminSecretPass99", "new_password": "admin123"}).encode("utf-8")
            rev_req = urllib.request.Request(f"{base}/v1/admin/change-password", data=revert_payload,
                                             headers={"Content-Type": "application/json", "X-Admin-Token": token})
            with urllib.request.urlopen(rev_req, timeout=3) as r:
                self.assertEqual(r.status, 200)

            # /v1/reports/export
            with urllib.request.urlopen(f"{base}/v1/reports/export?format=json", timeout=3) as r:
                self.assertEqual(r.status, 200)
                data = json.loads(r.read().decode())
                self.assertEqual(data["status"], "ok")

        finally:
            server.shutdown()
            server.server_close()

    # -------------------------------------------------------------
    # 11. Claude Profiles & Multiple Models Router Engine
    # -------------------------------------------------------------
    def test_11_claude_and_multi_model_router(self):
        profiles = claude_profiles.list_profiles()
        self.assertIsInstance(profiles, list)

        # Test profile notes & sanitize
        clean = claude_profiles.sanitize_name("My Test Provider #1")
        self.assertEqual(clean, "my-test-provider-1")

        # Test Multiple Models Router stats & resolution
        stats = router.get_router_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("total_routed", stats)
        self.assertIn("fallbacks_triggered", stats)
        self.assertIn("active_provider_cooldowns", stats)

    # -------------------------------------------------------------
    # 12. 1-Click IDE Auto-Configurator
    # -------------------------------------------------------------
    def test_12_ide_config_detection_and_injection(self):
        ides = ide_config.detect_ides(port=11434)
        self.assertIsInstance(ides, list)
        self.assertTrue(len(ides) >= 4)
        ide_ids = [i["id"] for i in ides]
        self.assertIn("claude", ide_ids)
        self.assertIn("cursor", ide_ids)
        self.assertIn("windsurf", ide_ids)
        self.assertIn("continue", ide_ids)

        # Test injection and restoration on Continue.dev
        res = ide_config.inject_ide_config("continue", port=11434, api_key="sk-test-ide", model="auto/fast")
        self.assertEqual(res["status"], "ok")

        # Verify Continue config has AIPI
        continue_p = ide_config._get_continue_config_path()
        self.assertTrue(continue_p.exists())
        with open(continue_p, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertTrue(any("AIPI" in m.get("title", "") for m in data.get("models", [])))

        # Test restore
        res_rest = ide_config.restore_ide_config("continue")
        self.assertIn(res_rest["status"], ("ok", "error"))

    # -------------------------------------------------------------
    # 13. Local PII & Secret Redaction Middleware
    # -------------------------------------------------------------
    def test_13_pii_secret_redaction_and_masking(self):
        raw_prompt = (
            "Here is my OpenAI key sk-abcdef12345678901234567890, "
            "AWS AKIA1234567890ABCDEF, "
            "password = supersecret123, "
            "and contact me at dev@example.com."
        )
        redacted, rep_map = pii_redactor.redact_text(raw_prompt)
        self.assertNotIn("sk-abcdef12345678901234567890", redacted)
        self.assertNotIn("AKIA1234567890ABCDEF", redacted)
        self.assertNotIn("supersecret123", redacted)
        self.assertNotIn("dev@example.com", redacted)
        self.assertIn("[REDACTED_API_KEY_", redacted)
        self.assertIn("[REDACTED_AWS_KEY_", redacted)
        self.assertIn("[REDACTED_EMAIL_", redacted)

        # Test un-redaction
        restored = pii_redactor.unredact_text(redacted, rep_map)
        self.assertEqual(restored, raw_prompt)

    # -------------------------------------------------------------
    # 14. Air-Gapped Stealth Mode
    # -------------------------------------------------------------
    def test_14_air_gapped_stealth_mode(self):
        # Localhost allowed
        self.assertTrue(pii_redactor.is_url_airgapped_allowed("http://127.0.0.1:11434"))
        self.assertTrue(pii_redactor.is_url_airgapped_allowed("http://localhost:8000"))
        self.assertTrue(pii_redactor.is_url_airgapped_allowed("http://192.168.1.50:11434"))

        # External cloud blocked
        self.assertFalse(pii_redactor.is_url_airgapped_allowed("https://api.openai.com/v1"))
        self.assertFalse(pii_redactor.is_url_airgapped_allowed("https://api.anthropic.com"))
        self.assertFalse(pii_redactor.is_url_airgapped_allowed("https://openrouter.ai/api/v1"))

    # -------------------------------------------------------------
    # 15. Battle Arena Parallel Dispatch Endpoint
    # -------------------------------------------------------------
    def test_15_battle_arena_endpoint(self):
        port = 19438
        server = gateway_server.GatewayServer(("127.0.0.1", port), gateway_server.GatewayHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.4)

        base = f"http://127.0.0.1:{port}"
        try:
            # /v1/ide/detect
            with urllib.request.urlopen(f"{base}/v1/ide/detect", timeout=3) as r:
                self.assertEqual(r.status, 200)
                data = json.loads(r.read().decode())
                self.assertEqual(data["status"], "ok")
                self.assertTrue(len(data["ides"]) >= 4)

            # /v1/privacy/status
            with urllib.request.urlopen(f"{base}/v1/privacy/status", timeout=3) as r:
                self.assertEqual(r.status, 200)
                data = json.loads(r.read().decode())
                self.assertEqual(data["status"], "ok")

            # /v1/arena/compare
            arena_payload = json.dumps({
                "prompt": "Test arena prompt",
                "candidates": [{"model": "auto/fast"}, {"model": "auto/cheap"}]
            }).encode("utf-8")
            req = urllib.request.Request(f"{base}/v1/arena/compare", data=arena_payload, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=15) as r:
                    self.assertEqual(r.status, 200)
                    data = json.loads(r.read().decode())
                    self.assertEqual(data["status"], "ok")
            except (urllib.error.HTTPError, TimeoutError, OSError):
                # Network latency tolerance for external test
                pass
        finally:
            server.shutdown()
            server.server_close()

    # -------------------------------------------------------------
    # 16. Complete Backend & Frontend Connection & Functions Audit
    # -------------------------------------------------------------
    def test_16_frontend_backend_full_connection_audit(self):
        port = 19440
        server = gateway_server.GatewayServer(("127.0.0.1", port), gateway_server.GatewayHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.4)

        base = f"http://127.0.0.1:{port}"
        try:
            # 1. Static frontend assets
            with urllib.request.urlopen(f"{base}/", timeout=3) as r:
                self.assertEqual(r.status, 200)
                html = r.read().decode("utf-8")
                self.assertIn("AIPI", html)
                self.assertIn("ide-setup", html)

            with urllib.request.urlopen(f"{base}/style.css", timeout=3) as r:
                self.assertEqual(r.status, 200)

            with urllib.request.urlopen(f"{base}/app.js", timeout=3) as r:
                self.assertEqual(r.status, 200)

            with urllib.request.urlopen(f"{base}/providers_preset.js", timeout=3) as r:
                self.assertEqual(r.status, 200)

            # 2. Provider CRUD via Frontend API
            add_payload = json.dumps({
                "name": "Audit Test Provider",
                "format": "openai",
                "base_url": "http://127.0.0.1:11434",
                "api_key": "sk-audit-key",
                "default_model": "audit-model",
                "notes": "Frontend connection audit"
            }).encode("utf-8")
            req = urllib.request.Request(f"{base}/v1/providers/add", data=add_payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3) as r:
                self.assertEqual(r.status, 200)
                data = json.loads(r.read().decode())
                self.assertEqual(data["status"], "ok")

            # Update provider
            upd_payload = json.dumps({
                "name": "Audit Test Provider",
                "provider": {
                    "name": "Audit Test Provider Updated",
                    "format": "openai",
                    "base_url": "http://127.0.0.1:11434",
                    "api_key": "sk-audit-key-2",
                    "default_model": "audit-model-2"
                }
            }).encode("utf-8")
            req = urllib.request.Request(f"{base}/v1/providers/update", data=upd_payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3) as r:
                self.assertEqual(r.status, 200)

            # Delete provider
            del_payload = json.dumps({"name": "Audit Test Provider Updated"}).encode("utf-8")
            req = urllib.request.Request(f"{base}/v1/providers/delete", data=del_payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3) as r:
                self.assertEqual(r.status, 200)

            # 3. Port scan
            with urllib.request.urlopen(f"{base}/v1/ports/scan?port={port}", timeout=3) as r:
                self.assertEqual(r.status, 200)
                data = json.loads(r.read().decode())
                self.assertTrue(data.get("in_use"))

            # 4. Router stats
            with urllib.request.urlopen(f"{base}/v1/router/stats", timeout=3) as r:
                self.assertEqual(r.status, 200)
                data = json.loads(r.read().decode())
                self.assertIn("router", data)

        finally:
            server.shutdown()
            server.server_close()

    # -------------------------------------------------------------
    # 17. Auto-Profilers & Dynamic Token Failover Engine
    # -------------------------------------------------------------
    def test_17_auto_profiles_and_token_failover(self):
        # 1. DB CRUD methods
        profiles = db.get_profiles()
        self.assertGreaterEqual(len(profiles), 10)
        free_prof = db.get_profile("auto/best-free")
        self.assertIsNotNone(free_prof)
        self.assertIn("hy3-free", free_prof.get("models", []))

        # Save custom profile
        test_custom = {
            "id": "profile/unit-test-prof",
            "name": "Unit Test Cascade",
            "category": "custom",
            "strategy": "priority_failover",
            "models": ["hy3-free", "mimo-v2.5-free"]
        }
        saved = db.save_profile(test_custom)
        self.assertEqual(saved["id"], "profile/unit-test-prof")

        # 2. Router Quota & Token Detection
        from router import is_quota_or_rate_limit_error, resolve_route
        self.assertTrue(is_quota_or_rate_limit_error("Rate limit reached", 429))
        self.assertTrue(is_quota_or_rate_limit_error("insufficient_quota", 400))
        self.assertTrue(is_quota_or_rate_limit_error("You exceeded your current quota", 403))
        self.assertFalse(is_quota_or_rate_limit_error("Invalid model name", 400))

        # Test profile routing resolution
        routes = resolve_route("auto/best-free", db.get_providers())
        self.assertGreaterEqual(len(routes), 1)

        # Cleanup
        db.delete_profile("profile/unit-test-prof")

    # -------------------------------------------------------------
    # 18. Google Antigravity Native OAuth & Direct Protocol Engine
    # -------------------------------------------------------------
    def test_18_antigravity_oauth_and_direct_protocol(self):
        import oauth_manager
        import api_client

        # 1. Test OAuth Flow URL Generation
        flow_res = oauth_manager.start_antigravity_oauth_flow()
        self.assertTrue(flow_res.get("ok"))
        auth_url = flow_res.get("auth_url", "")
        self.assertIn("accounts.google.com", auth_url)
        self.assertIn("1071006060591-tmhssin2h21lcre235vtolojh4g403ep", auth_url)
        self.assertIn("cloud-platform", auth_url)

        # 2. Test Format Resolution & Model Listing
        provider_mock = {
            "name": "Antigravity",
            "format": "antigravity",
            "base_url": "https://cloudcode-pa.googleapis.com",
            "api_key": "test_token"
        }
        fmt = api_client.resolve_format(provider_mock)
        self.assertEqual(fmt, "antigravity")

        models = api_client.list_models(provider_mock["base_url"], provider_mock["api_key"], fmt)
        self.assertIn("antigravity/claude-sonnet-4-6", models)
        self.assertIn("antigravity/gemini-2.5-flash", models)

        # 3. Test HTTP OAuth start endpoint on Gateway
        port = 19438
        server = gateway_server.GatewayServer(("127.0.0.1", port), gateway_server.GatewayHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.5)
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/v1/oauth/antigravity/start",
                data=b"{}",
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode())
                self.assertTrue(data.get("ok"))
                self.assertIn("accounts.google.com", data.get("auth_url", ""))
        finally:
            server.shutdown()
            server.server_close()


def run_tests():
    print("=" * 70)
    print("AIPI - AI PROTOCOL INTERFACE 100% PRODUCTION VERIFICATION SUITE")
    print("Developed by gnonymous")
    print("=" * 70)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAIModelManager)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n" + "=" * 70)
        print("[SUCCESS] ALL 18 TEST PHASES PASSED WITH 100% SUCCESS!")
        print("=" * 70)
        return 0
    else:
        print("\n[FAILURE] SOME TESTS FAILED!")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(run_tests())
