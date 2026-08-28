"""
ide_config.py - AIPI One-Click IDE Auto-Configurator.
Developed by gnonymous.

Auto-detects and automatically configures Cursor, Windsurf, Claude Code,
Continue.dev, and other AI-assisted developer tools to use AIPI Gateway.
"""
import os
import sys
import json
import shutil
from pathlib import Path

APP_DIR = os.path.dirname(os.path.abspath(__file__))


def _get_claude_settings_path():
    home = Path.home()
    return home / ".claude" / "settings.json"


def _get_cursor_settings_path():
    home = Path.home()
    if os.name == "nt":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            p = Path(appdata) / "Cursor" / "User" / "settings.json"
            if p.parent.exists() or p.exists():
                return p
    # Unix / fallback
    p = home / ".cursor" / "User" / "settings.json"
    if p.parent.exists() or p.exists():
        return p
    return home / ".cursor" / "settings.json"


def _get_windsurf_settings_path():
    home = Path.home()
    if os.name == "nt":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            p = Path(appdata) / "Windsurf" / "User" / "settings.json"
            if p.parent.exists() or p.exists():
                return p
    return home / ".windsurf" / "settings.json"


def _get_continue_config_path():
    home = Path.home()
    return home / ".continue" / "config.json"


def _get_opencode_config_path():
    home = Path.home()
    p = home / ".config" / "opencode" / "opencode.json"
    if p.parent.exists():
        return p
    return home / ".opencode" / "opencode.json"


def _get_opencode_auth_path():
    home = Path.home()
    return home / ".local" / "share" / "opencode" / "auth.json"


def detect_ides(port=11434):
    """
    Detect all supported IDEs and their current configuration status.
    """
    expected_base_url = f"http://127.0.0.1:{port}/v1"
    ides = []

    # 1. Claude Code
    claude_p = _get_claude_settings_path()
    claude_detected = claude_p.parent.exists() or claude_p.exists()
    claude_configured = False
    claude_details = {}
    if claude_p.exists():
        try:
            with open(claude_p, "r", encoding="utf-8") as f:
                data = json.load(f)
                env = data.get("env", {})
                base = env.get("ANTHROPIC_BASE_URL", "")
                if f":{port}" in base or base.startswith("http://127.0.0.1:"):
                    claude_configured = True
                claude_details = {"base_url": base, "has_key": bool(env.get("ANTHROPIC_API_KEY"))}
        except Exception:
            pass

    ides.append({
        "id": "claude",
        "name": "Claude Code CLI",
        "detected": claude_detected,
        "path": str(claude_p),
        "configured": claude_configured,
        "has_backup": os.path.exists(str(claude_p) + ".bak"),
        "details": claude_details,
        "format": "anthropic"
    })

    # 2. Cursor IDE
    cursor_p = _get_cursor_settings_path()
    cursor_detected = cursor_p.parent.exists() or cursor_p.exists()
    cursor_configured = False
    cursor_details = {}
    if cursor_p.exists():
        try:
            with open(cursor_p, "r", encoding="utf-8") as f:
                data = json.load(f)
                base = data.get("cursor.general.openaiBaseUrl", "") or data.get("openai.baseUrl", "")
                if f":{port}" in base or base.startswith("http://127.0.0.1:"):
                    cursor_configured = True
                cursor_details = {"base_url": base}
        except Exception:
            pass

    ides.append({
        "id": "cursor",
        "name": "Cursor IDE",
        "detected": cursor_detected,
        "path": str(cursor_p),
        "configured": cursor_configured,
        "has_backup": os.path.exists(str(cursor_p) + ".bak"),
        "details": cursor_details,
        "format": "openai"
    })

    # 3. Windsurf IDE
    windsurf_p = _get_windsurf_settings_path()
    windsurf_detected = windsurf_p.parent.exists() or windsurf_p.exists()
    windsurf_configured = False
    windsurf_details = {}
    if windsurf_p.exists():
        try:
            with open(windsurf_p, "r", encoding="utf-8") as f:
                data = json.load(f)
                base = data.get("windsurf.openai.baseUrl", "") or data.get("openai.baseUrl", "")
                if f":{port}" in base or base.startswith("http://127.0.0.1:"):
                    windsurf_configured = True
                windsurf_details = {"base_url": base}
        except Exception:
            pass

    ides.append({
        "id": "windsurf",
        "name": "Windsurf IDE",
        "detected": windsurf_detected,
        "path": str(windsurf_p),
        "configured": windsurf_configured,
        "has_backup": os.path.exists(str(windsurf_p) + ".bak"),
        "details": windsurf_details,
        "format": "openai"
    })

    # 4. Continue.dev
    continue_p = _get_continue_config_path()
    continue_detected = continue_p.parent.exists() or continue_p.exists()
    continue_configured = False
    continue_details = {}
    if continue_p.exists():
        try:
            with open(continue_p, "r", encoding="utf-8") as f:
                data = json.load(f)
                models = data.get("models", [])
                for m in models:
                    if f":{port}" in m.get("apiBase", ""):
                        continue_configured = True
                        break
        except Exception:
            pass

    ides.append({
        "id": "continue",
        "name": "Continue.dev",
        "detected": continue_detected,
        "path": str(continue_p),
        "configured": continue_configured,
        "has_backup": os.path.exists(str(continue_p) + ".bak"),
        "details": continue_details,
        "format": "openai"
    })

    # 5. OpenCode CLI
    opencode_p = _get_opencode_config_path()
    opencode_auth_p = _get_opencode_auth_path()
    opencode_cli_bin = any(shutil.which(cmd) for cmd in ("opencode", "opencode.cmd", "opencode.ps1"))
    opencode_detected = opencode_cli_bin or opencode_p.exists() or opencode_p.parent.exists() or opencode_auth_p.exists()
    opencode_configured = False
    opencode_details = {}
    if opencode_p.exists():
        try:
            with open(opencode_p, "r", encoding="utf-8") as f:
                oc_data = json.load(f)
                prov = oc_data.get("provider", {}).get("aipi", {})
                oc_base = prov.get("options", {}).get("baseURL", "")
                if f":{port}" in oc_base or oc_base.startswith("http://127.0.0.1:"):
                    opencode_configured = True
                opencode_details = {"base_url": oc_base}
        except Exception:
            pass

    ides.append({
        "id": "opencode",
        "name": "OpenCode CLI",
        "detected": opencode_detected,
        "path": str(opencode_p),
        "configured": opencode_configured,
        "has_backup": os.path.exists(str(opencode_p) + ".bak"),
        "details": opencode_details,
        "format": "openai"
    })

    return ides


def inject_ide_config(ide_id, port=11434, api_key="aipi-local", model="auto/fast"):
    """
    Inject AIPI gateway configuration into the specified IDE.
    Automatically creates a .bak backup file first.
    """
    base_url = f"http://127.0.0.1:{port}/v1"
    ide_id = ide_id.lower().strip()

    if ide_id == "claude":
        p = _get_claude_settings_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        # Create backup
        if p.exists() and not os.path.exists(str(p) + ".bak"):
            shutil.copy2(p, str(p) + ".bak")

        data = {}
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}

        if "env" not in data or not isinstance(data["env"], dict):
            data["env"] = {}

        data["env"]["ANTHROPIC_BASE_URL"] = base_url
        data["env"]["ANTHROPIC_API_KEY"] = api_key
        data["activeModel"] = model

        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return {"status": "ok", "ide": "claude", "path": str(p), "message": "Claude Code configured for AIPI."}

    elif ide_id == "cursor":
        p = _get_cursor_settings_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists() and not os.path.exists(str(p) + ".bak"):
            shutil.copy2(p, str(p) + ".bak")

        data = {}
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}

        data["cursor.general.openaiBaseUrl"] = base_url
        data["openai.baseUrl"] = base_url
        data["openai.apiKey"] = api_key

        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return {"status": "ok", "ide": "cursor", "path": str(p), "message": "Cursor IDE configured for AIPI."}

    elif ide_id == "windsurf":
        p = _get_windsurf_settings_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists() and not os.path.exists(str(p) + ".bak"):
            shutil.copy2(p, str(p) + ".bak")

        data = {}
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}

        data["windsurf.openai.baseUrl"] = base_url
        data["openai.baseUrl"] = base_url
        data["openai.apiKey"] = api_key

        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return {"status": "ok", "ide": "windsurf", "path": str(p), "message": "Windsurf IDE configured for AIPI."}

    elif ide_id == "continue":
        p = _get_continue_config_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists() and not os.path.exists(str(p) + ".bak"):
            shutil.copy2(p, str(p) + ".bak")

        data = {"models": []}
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {"models": []}

        if "models" not in data or not isinstance(data["models"], list):
            data["models"] = []

        # Remove previous AIPI entries
        data["models"] = [m for m in data["models"] if "AIPI" not in m.get("title", "") and "PROXIA" not in m.get("title", "")]

        # Insert Auto-Profiles at top
        preset_profiles = [
            (model or "auto/best-free", f"AIPI ({model or 'auto/best-free'})"),
            ("auto/best-free", "AIPI Auto Best Free"),
            ("auto/best-coding", "AIPI Auto Best Coding"),
            ("auto/best-fast", "AIPI Auto Best Fast"),
            ("auto/best-reasoning", "AIPI Auto Best Reasoning"),
            ("auto/best-vision", "AIPI Auto Best Vision"),
        ]
        inserted = set()
        for prof_id, prof_title in reversed(preset_profiles):
            if prof_id not in inserted:
                inserted.add(prof_id)
                data["models"].insert(0, {
                    "title": prof_title,
                    "provider": "openai",
                    "model": prof_id,
                    "apiBase": base_url,
                    "apiKey": api_key
                })

        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return {"status": "ok", "ide": "continue", "path": str(p), "message": "Continue.dev configured for AIPI Auto-Profiles."}

    elif ide_id == "opencode":
        p = _get_opencode_config_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists() and not os.path.exists(str(p) + ".bak"):
            shutil.copy2(p, str(p) + ".bak")
        elif not p.exists() and not os.path.exists(str(p) + ".bak"):
            with open(str(p) + ".bak", "w", encoding="utf-8") as bf:
                bf.write("{}")

        data = {}
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}

        if "provider" not in data or not isinstance(data["provider"], dict):
            data["provider"] = {}

        models_dict = {
            "auto/best-free": {"name": "AIPI Auto Best-Free (Hunyuan 3 / Mimo / Laguna)"},
            "auto/free": {"name": "AIPI Auto Free"},
            "auto/best-coding": {"name": "AIPI Auto Best Coding"},
            "auto/coding": {"name": "AIPI Auto Coding"},
            "auto/best-fast": {"name": "AIPI Auto Best-Fast (Gemini Flash)"},
            "auto/fast": {"name": "AIPI Auto Fast"},
            "auto/best-reasoning": {"name": "AIPI Auto Best Reasoning"},
            "auto/best-vision": {"name": "AIPI Auto Best Vision"},
            "auto/best-chat": {"name": "AIPI Auto Best Chat"},
            "auto/smart": {"name": "AIPI Auto Smart (Claude Sonnet 4.6)"},
            "auto/cheap": {"name": "AIPI Auto Cost-Saver"},
            "hy3-free": {"name": "Hunyuan 3 Free (OpenCode)"},
            "mimo-v2.5-free": {"name": "Mimo v2.5 Free (OpenCode)"},
            "laguna-s-2.1-free": {"name": "Laguna 2.1 Free (OpenCode)"},
            "deepseek-v4-flash-free": {"name": "DeepSeek V4 Flash Free"},
            "antigravity/claude-sonnet-4-6": {"name": "Claude Sonnet 4.6 (AIPI Antigravity)"},
            "antigravity/gemini-2.5-flash": {"name": "Gemini 2.5 Flash (AIPI Antigravity)"}
        }
        if model and model not in models_dict:
            models_dict[model] = {"name": f"AIPI ({model})"}

        data["$schema"] = "https://opencode.ai/config.json"
        data["model"] = f"aipi/{model}" if not model.startswith("aipi/") else model
        data["provider"]["aipi"] = {
            "name": "AIPI Local Gateway",
            "npm": "@ai-sdk/openai",
            "options": {
                "baseURL": base_url,
                "apiKey": api_key
            },
            "models": models_dict
        }

        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        # Also ensure auth.json has local gateway credentials
        auth_p = _get_opencode_auth_path()
        try:
            auth_p.parent.mkdir(parents=True, exist_ok=True)
            auth_data = {}
            if auth_p.exists():
                try:
                    with open(auth_p, "r", encoding="utf-8") as af:
                        auth_data = json.load(af)
                except Exception:
                    auth_data = {}
            auth_data["gnonymous"] = {"type": "api", "key": api_key}
            with open(auth_p, "w", encoding="utf-8") as af:
                json.dump(auth_data, af, indent=2)
        except Exception:
            pass

        return {"status": "ok", "ide": "opencode", "path": str(p), "message": "OpenCode CLI configured for AIPI Gateway."}

    else:
        raise ValueError(f"Unsupported IDE: {ide_id}")


def restore_ide_config(ide_id):
    """
    Restore an IDE's configuration from its .bak backup file.
    """
    path_map = {
        "claude": _get_claude_settings_path(),
        "cursor": _get_cursor_settings_path(),
        "windsurf": _get_windsurf_settings_path(),
        "continue": _get_continue_config_path(),
        "opencode": _get_opencode_config_path()
    }
    if ide_id not in path_map:
        raise ValueError(f"Unsupported IDE: {ide_id}")

    p = path_map[ide_id]
    bak = str(p) + ".bak"
    if not os.path.exists(bak):
        if p.exists():
            try:
                os.remove(p)
                return {"status": "ok", "ide": ide_id, "message": f"Cleaned up configuration for {ide_id}."}
            except Exception:
                pass
        return {"status": "error", "message": f"No backup file found for {ide_id}."}

    shutil.copy2(bak, p)
    os.remove(bak)
    return {"status": "ok", "ide": ide_id, "message": f"Restored {ide_id} configuration from backup."}
