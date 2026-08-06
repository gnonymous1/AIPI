"""
omniroute_service.py - Start, check, and fix the Omniroute local gateway.

Omniroute is an npm global package whose server exposes a dashboard + API at
http://127.0.0.1:20128 (API base http://127.0.0.1:20128/v1). This module lets the
app (and the desktop launch scripts) bring it up, verify it, and report a fix
path if it won't start.
"""
import os
import shutil
import subprocess
import time

import requests

PORT = 20128
BASE = "http://127.0.0.1:%d" % PORT
HEARTBEAT = BASE + "/"
LAUNCH_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "omniroute_launch.log")


def omniroute_cmd():
    """Return the path to the omniroute launch command, or None."""
    for candidate in ("omniroute.cmd", "omniroute"):
        p = shutil.which(candidate)
        if p:
            return p
    return None


def is_up(timeout=2.0):
    try:
        r = requests.get(HEARTBEAT, timeout=timeout)
        return r.status_code < 500
    except Exception:
        return False


def status():
    """Return (running:bool, detail:str)."""
    if is_up():
        return True, ("Omniroute is RUNNING — dashboard %s/dashboard "
                      "(API base %s/v1)." % (BASE, BASE))
    cmd = omniroute_cmd()
    where = cmd if cmd else "not found on PATH (install: npm install -g omniroute)"
    return False, ("Omniroute is NOT running (nothing on port %d).\n"
                   "Launch command resolves to: %s" % (PORT, where))


def start():
    """
    Launch the Omniroute server and wait for it to come up.
    Returns (running:bool, detail:str).
    """
    if is_up():
        return True, "Omniroute is already running — nothing to do."
    cmd = omniroute_cmd()
    if not cmd:
        return False, ("Could not find 'omniroute' on PATH.\n"
                       "Fix: open a terminal and run:\n  npm install -g omniroute")

    log = open(LAUNCH_LOG, "w", encoding="utf-8", errors="replace")
    try:
        subprocess.Popen([cmd], stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                         creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        log.close()
        return False, "Failed to launch omniroute: %s" % e

    for _ in range(40):  # up to ~20s
        time.sleep(0.5)
        if is_up():
            log.close()
            return True, ("Omniroute started successfully — dashboard %s/dashboard "
                          "(API base %s/v1)." % (BASE, BASE))

    log.close()
    tail = ""
    try:
        with open(LAUNCH_LOG, "r", encoding="utf-8", errors="replace") as f:
            tail = f.read()[-900:]
    except Exception:
        pass
    return False, ("Omniroute did not come up on port %d within 20s.\n\n"
                   "Log tail:\n%s" % (PORT, tail or "(no log output)"))


def fix():
    """
    Diagnose and try to fix Omniroute: if up, done. Otherwise clear stale pid,
    relaunch, and report the result with guidance if still failing.
    Returns (ok:bool, detail:str).
    """
    running, detail = status()
    if running:
        return True, detail

    # Clear stale pid so a fresh launch can own it.
    pid_file = os.path.join(os.path.expanduser("~"), ".omniroute", "server", ".pid")
    try:
        if os.path.exists(pid_file):
            os.remove(pid_file)
    except Exception:
        pass

    ok, msg = start()
    if ok:
        return True, msg

    guidance = (
        "\n\nFix checklist:\n"
        "  1. The DB has a storage-encryption warning — check that "
        "~/.omniroute/.env sets STORAGE_ENCRYPTION_KEY as it did originally.\n"
        "  2. Check ~/.omniroute\\logs\\application for the full error.\n"
        "  3. Reinstall with: npm install -g omniroute\n"
        "  4. If a port conflict exists on 20128, stop the other process first.")
    return False, msg + guidance
