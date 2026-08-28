"""
pii_redactor.py - AIPI Local PII & Secret Redaction Middleware.
Developed by gnonymous.

Detects, masks, and scrubs sensitive API keys, credentials, database URIs,
passwords, and personal identifiable information (PII) on localhost before
prompts are dispatched to external cloud LLM providers.
"""
import os
import re
import json

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PRIVACY_CONFIG_PATH = os.path.join(APP_DIR, "privacy.json")

DEFAULT_PRIVACY_CONFIG = {
    "pii_enabled": True,
    "stealth_mode": False,  # If True, only allow localhost/LAN providers
    "redact_api_keys": True,
    "redact_passwords": True,
    "redact_private_keys": True,
    "redact_db_uris": True,
    "redact_emails": True,
    "redact_credit_cards": True,
    "redact_ips": False,
    "auto_unredact_response": True
}

# Regex compilation
RE_PRIVATE_KEY = re.compile(r"-----BEGIN [A-Z0-9 _-]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z0-9 _-]+ PRIVATE KEY-----", re.IGNORECASE)
RE_OPENAI_KEY = re.compile(r"\b(sk-[a-zA-Z0-9_\-]{20,})\b")
RE_ANTHROPIC_KEY = re.compile(r"\b(sk-ant-[a-zA-Z0-9_\-]{20,})\b")
RE_AWS_KEY = re.compile(r"\b(AKIA[0-9A-Z]{16})\b")
RE_BEARER_TOKEN = re.compile(r"(Bearer\s+)([a-zA-Z0-9_\-\.]{25,})", re.IGNORECASE)
RE_DB_URI = re.compile(r"\b(postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://([^\s\"']+)\b", re.IGNORECASE)
RE_PASSWORD_PAIR = re.compile(r"""\b(password|passwd|pwd|secret|api_secret)\s*[:=]\s*["']?([^ \n\r\t"']+)["']?""", re.IGNORECASE)
RE_EMAIL = re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b")
RE_CREDIT_CARD = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")
RE_IPV4 = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")


def get_privacy_config():
    if os.path.exists(PRIVACY_CONFIG_PATH):
        try:
            with open(PRIVACY_CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                res = dict(DEFAULT_PRIVACY_CONFIG)
                res.update(cfg)
                return res
        except Exception:
            pass
    return dict(DEFAULT_PRIVACY_CONFIG)


def save_privacy_config(config):
    merged = dict(DEFAULT_PRIVACY_CONFIG)
    merged.update(config)
    with open(PRIVACY_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)
    return merged


def redact_text(text, config=None):
    """
    Redact secrets and PII from prompt text according to active privacy configuration.
    Returns (redacted_text, replacement_map).
    """
    if not text or not isinstance(text, str):
        return text, {}

    if config is None:
        config = get_privacy_config()

    if not config.get("pii_enabled", True):
        return text, {}

    replacements = {}
    counter = 1

    def make_placeholder(label, original):
        nonlocal counter
        ph = f"[REDACTED_{label}_{counter}]"
        replacements[ph] = original
        counter += 1
        return ph

    # 1. Private RSA / SSH Keys
    if config.get("redact_private_keys", True):
        for m in RE_PRIVATE_KEY.finditer(text):
            val = m.group(0)
            ph = make_placeholder("PRIVATE_KEY", val)
            text = text.replace(val, ph)

    # 2. Database URIs
    if config.get("redact_db_uris", True):
        for m in RE_DB_URI.finditer(text):
            val = m.group(0)
            ph = make_placeholder("DB_URI", val)
            text = text.replace(val, ph)

    # 3. Passwords
    if config.get("redact_passwords", True):
        for m in RE_PASSWORD_PAIR.finditer(text):
            k, v = m.group(1), m.group(2)
            ph = make_placeholder("PASSWORD", v)
            text = text.replace(v, ph)

    # 4. API Keys
    if config.get("redact_api_keys", True):
        for m in RE_OPENAI_KEY.finditer(text):
            val = m.group(1)
            ph = make_placeholder("API_KEY", val)
            text = text.replace(val, ph)

        for m in RE_ANTHROPIC_KEY.finditer(text):
            val = m.group(1)
            ph = make_placeholder("API_KEY", val)
            text = text.replace(val, ph)

        for m in RE_AWS_KEY.finditer(text):
            val = m.group(1)
            ph = make_placeholder("AWS_KEY", val)
            text = text.replace(val, ph)

        for m in RE_BEARER_TOKEN.finditer(text):
            prefix, token = m.group(1), m.group(2)
            ph = make_placeholder("BEARER_TOKEN", token)
            text = text.replace(f"{prefix}{token}", f"{prefix}{ph}")

    # 5. Credit Cards
    if config.get("redact_credit_cards", True):
        for m in RE_CREDIT_CARD.finditer(text):
            val = m.group(0)
            ph = make_placeholder("CREDIT_CARD", val)
            text = text.replace(val, ph)

    # 6. Emails
    if config.get("redact_emails", True):
        for m in RE_EMAIL.finditer(text):
            val = m.group(0)
            ph = make_placeholder("EMAIL", val)
            text = text.replace(val, ph)

    # 7. IP Addresses (excluding localhost / standard masks)
    if config.get("redact_ips", False):
        for m in RE_IPV4.finditer(text):
            val = m.group(0)
            if val not in ("127.0.0.1", "0.0.0.0", "255.255.255.0"):
                ph = make_placeholder("IP_ADDRESS", val)
                text = text.replace(val, ph)

    return text, replacements


def unredact_text(text, replacement_map):
    """
    Restore original values in model responses if replacement map is provided.
    """
    if not text or not replacement_map:
        return text
    result = text
    for ph, orig in replacement_map.items():
        result = result.replace(ph, orig)
    return result


def is_url_airgapped_allowed(url):
    """
    Check if a target URL is strictly local (localhost / private network) for Stealth Mode.
    """
    url_lower = str(url).lower().strip()
    allowed_hosts = [
        "127.0.0.1", "localhost", "::1", "0.0.0.0",
        "192.168.", "10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.20."
    ]
    for h in allowed_hosts:
        if h in url_lower:
            return True
    return False
