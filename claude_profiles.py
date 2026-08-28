"""
claude_profiles.py - Read / write Claude Code profiles.

Claude Code stores switchable profiles under ~/.claude/profiles/<name>/settings.json.
This module lists the models already configured in Claude and lets you install a
custom profile from any provider configured in the app.

Profile settings.json format (matches existing profiles on this machine):
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "model": "<model>",
  "env": {
    "ANTHROPIC_BASE_URL": "<base_url>",
    "ANTHROPIC_MODEL": "<model>",
    "ANTHROPIC_API_KEY": "<api_key>",
    "CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY": "1",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "190000"
  }
}
"""
import json
import os
import re

HOME = os.path.expanduser("~")
PROFILES_DIR = os.path.join(HOME, ".claude", "profiles")
SCHEMA = "https://json.schemastore.org/claude-code-settings.json"


def profiles_dir():
    return PROFILES_DIR


def sanitize_name(name):
    """Turn a display name into a safe folder name (lowercased, dashes)."""
    s = re.sub(r"[^A-Za-z0-9]+", "-", name.strip()).strip("-").lower()
    return s or "custom-profile"


def list_profiles():
    """Return a list of dicts for each profile folder that has a settings.json."""
    profiles = []
    if not os.path.isdir(PROFILES_DIR):
        return profiles
    for entry in sorted(os.listdir(PROFILES_DIR)):
        folder = os.path.join(PROFILES_DIR, entry)
        settings_path = os.path.join(folder, "settings.json")
        if not os.path.isdir(folder) or not os.path.isfile(settings_path):
            continue
        info = {"name": entry, "path": folder, "model": "", "base_url": "",
                "api_key": "", "has_settings": True, "notes": ""}
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            info["model"] = data.get("model", "")
            env = data.get("env", {})
            info["base_url"] = env.get("ANTHROPIC_BASE_URL", "")
            info["model_env"] = env.get("ANTHROPIC_MODEL", "")
            info["api_key"] = env.get("ANTHROPIC_API_KEY", "")
        except Exception:
            pass
        info["notes"] = profile_notes(entry)
        profiles.append(info)
    return profiles


def create_profile(name, model, base_url, api_key="", description=""):
    """
    Create a Claude Code profile folder + settings.json from the given values.
    Returns the absolute path to the created settings.json.
    Optional description is stored in a sidecar notes.txt.
    Raises ValueError for bad input; OSError for filesystem problems.
    """
    name = (name or "").strip()
    model = (model or "").strip()
    base_url = (base_url or "").strip()
    if not name:
        raise ValueError("Profile name is required.")
    if not model:
        raise ValueError("Model is required.")
    if not base_url:
        raise ValueError("Base URL is required.")

    folder = os.path.join(PROFILES_DIR, sanitize_name(name))
    os.makedirs(folder, exist_ok=True)

    env = {
        "ANTHROPIC_BASE_URL": base_url,
        "ANTHROPIC_MODEL": model,
        "ANTHROPIC_API_KEY": api_key,
        "CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY": "1",
        "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "190000",
    }
    settings = {
        "$schema": SCHEMA,
        "model": model,
        "env": env,
    }
    path = os.path.join(folder, "settings.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
    if description:
        set_profile_notes(sanitize_name(name), description)
    return path


def profile_notes(name):
    """Return the sidecar notes text for a profile ('' if none)."""
    p = os.path.join(PROFILES_DIR, name, "notes.txt")
    try:
        with open(p, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def set_profile_notes(name, text):
    """Write sidecar notes for a profile."""
    folder = os.path.join(PROFILES_DIR, name)
    os.makedirs(folder, exist_ok=True)
    p = os.path.join(folder, "notes.txt")
    with open(p, "w", encoding="utf-8") as f:
        f.write(text or "")


def rename_profile(old_name, new_name):
    """Rename a profile folder (returns new name, or None if not found)."""
    if not old_name or not new_name:
        return None
    src = os.path.join(PROFILES_DIR, old_name)
    if not os.path.isdir(src):
        return None
    new_name = sanitize_name(new_name) or sanitize_name(old_name)
    dst = os.path.join(PROFILES_DIR, new_name)
    if os.path.exists(dst):
        raise ValueError("A profile named '%s' already exists." % new_name)
    os.rename(src, dst)
    return new_name


def parse_settings_file(path):
    """Parse a raw Claude settings.json into a dict usable by the import wizard."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Not a JSON object.")
    model = (data.get("model") or "").strip()
    env = data.get("env", {}) or {}
    base_url = (env.get("ANTHROPIC_BASE_URL") or "").strip()
    api_key = (env.get("ANTHROPIC_API_KEY") or "").strip()
    if not base_url:
        base_url = (data.get("api_base") or env.get("ANTHROPIC_BASE_URL") or "").strip()
    return {
        "name": os.path.basename(os.path.dirname(os.path.abspath(path))),
        "model": model,
        "base_url": base_url,
        "api_key": api_key,
        "notes": "Imported from %s" % path,
    }



def delete_profile(name):
    """Delete a profile folder. Returns True on success."""
    if not name:
        return False
    folder = os.path.join(PROFILES_DIR, name)
    if not os.path.isdir(folder):
        return False
    import shutil
    shutil.rmtree(folder)
    return True


# ---------------------------------------------------------------------------
# Active-model switching (~/.claude/settings.json)
# ---------------------------------------------------------------------------
def user_settings_path():
    """Path to the global Claude Code settings that selects the active model."""
    return os.path.join(HOME, ".claude", "settings.json")


def load_user_settings():
    try:
        with open(user_settings_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def get_active_model():
    """Return the model id currently active in Claude Code ('' if none)."""
    return load_user_settings().get("model", "")


def set_active_profile(profile_name):
    """
    Make the named profile the active Claude Code model by writing its
    model + env (ANTHROPIC_BASE_URL / ANTHROPIC_MODEL / ANTHROPIC_API_KEY /
    CLAUDE_CODE_MODEL) into ~/.claude/settings.json, preserving other keys
    (e.g. theme). Returns the applied model id.
    """
    profiles = {p["name"]: p for p in list_profiles()}
    if profile_name not in profiles:
        raise ValueError("Claude profile not found: %s" % profile_name)
    p = profiles[profile_name]
    model = (p.get("model") or p.get("model_env") or "").strip()
    if not model:
        raise ValueError("Profile '%s' has no model set." % profile_name)

    data = load_user_settings()
    data.setdefault("env", {})
    env = data["env"]
    data["model"] = model
    env["ANTHROPIC_MODEL"] = model
    env["CLAUDE_CODE_MODEL"] = model
    if p.get("base_url"):
        env["ANTHROPIC_BASE_URL"] = p["base_url"]
    if p.get("api_key"):
        env["ANTHROPIC_API_KEY"] = p["api_key"]

    path = user_settings_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return model

