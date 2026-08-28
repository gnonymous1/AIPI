"""
install_service.py - Windows Auto-Start Service Installer for AIPI (AI Protocol Interface).
Developed by gnonymous.
Uses pywin32 if available, otherwise falls back to a Startup-folder shortcut (task scheduler).
"""
import os
import sys
import subprocess

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable
ENTRY = os.path.join(APP_DIR, "gateway_server.py")
PORT = "11434"

def install_with_pywin32():
    try:
        import win32serviceutil
        import win32service
        import win32event
        import servicemanager
    except ImportError:
        return False

    class AIPIService(win32serviceutil.ServiceFramework):
        _svc_name_ = "AIPIGateway"
        _svc_display_name_ = "AIPI — AI Protocol Interface Gateway"
        _svc_description_ = "Universal OpenAI/Anthropic compatible AI model gateway with routing, caching, virtual keys, RBAC developed by gnonymous."

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.hWaitStop)

        def SvcDoRun(self):
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                                  servicemanager.PYS_SERVICE_STARTED,
                                  (self._svc_name_, ""))
            os.chdir(APP_DIR)
            os.execv(PYTHON, [PYTHON, ENTRY, "run", PORT, "--host", "127.0.0.1"])

    win32serviceutil.HandleCommandLine(AIPIService)
    return True

def install_via_startup_folder():
    """Fallback: create a .vbs launcher in the user Startup folder (no admin needed)."""
    startup = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu",
                           "Programs", "Startup")
    if not os.path.isdir(startup):
        print("Startup folder not found:", startup)
        return False
    vbs = os.path.join(startup, "AIPI_Gateway.vbs")
    content = (
        'Set WshShell = CreateObject("WScript.Shell")\n'
        'WshShell.CurrentDirectory = "' + APP_DIR.replace('"', '""') + '"\n'
        f'WshShell.Run """{PYTHON}"" "{ENTRY}" run {PORT}", 0, False\n'
    )
    with open(vbs, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created startup launcher: {vbs}")
    return True

def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "install"
    if action == "install":
        print("Installing AIPI Gateway as Windows service...")
        if install_with_pywin32():
            print("Service installed via pywin32. Start with: net start AIPIGateway")
        else:
            print("pywin32 not available — falling back to Startup folder launcher.")
            install_via_startup_folder()
        print("Done.")
    elif action == "uninstall":
        try:
            import win32serviceutil
            win32serviceutil.RemoveService("AIPIGateway")
            print("Service removed.")
        except Exception:
            print("No pywin32 service found. Remove the VBS launcher from the Startup folder manually.")
    else:
        print("Usage: python install_service.py [install|uninstall]")

if __name__ == "__main__":
    main()
