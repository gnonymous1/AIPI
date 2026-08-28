"""
build_app.py - Production Builder & PyInstaller Standalone Executable Bundler.
"""
import os
import sys
import subprocess

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ENTRY_POINT = os.path.join(APP_DIR, "ai_model_manager.py")
WEB_DIR = os.path.join(APP_DIR, "web")

def build_nim():
    """Builds native Nim binary launcher if Nim compiler is available."""
    nim_cmd = "nim"
    try:
        res = subprocess.run([nim_cmd, "--version"], capture_output=True, text=True)
        if res.returncode == 0:
            print("Compiling native Nim launcher (aipi.nim -> aipi.exe)...")
            cmd = [nim_cmd, "c", "-d:release", "--opt:size", "aipi.nim"]
            subprocess.run(cmd, check=True)
            print("✅ Nim binary compiled successfully: aipi.exe")
            return True
    except Exception:
        pass
    print("ℹ️ Nim compiler not detected — skipping Nim binary compilation.")
    return False

def build():
    print("=== AIPI — AI Protocol Interface Production Multi-Target Builder ===")
    
    # 1. Nim binary check
    build_nim()

    # 2. PyInstaller standalone executable
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    add_data_sep = ";" if os.name == "nt" else ":"
    web_add_data = f"{WEB_DIR}{add_data_sep}web"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=AIPI",
        f"--add-data={web_add_data}",
        "--hidden-import=sqlite3",
        "--hidden-import=vault",
        "--hidden-import=db",
        "--hidden-import=router",
        "--hidden-import=cache",
        "--hidden-import=virtual_keys",
        "--hidden-import=analytics",
        "--hidden-import=providers_preset",
        "--hidden-import=auth",
        "--hidden-import=license",
        "--hidden-import=ratelimit",
        "--hidden-import=oidc",
        "--hidden-import=reports",
        "--hidden-import=oauth_manager",
        ENTRY_POINT
    ]
    
    print("\nRunning PyInstaller build:")
    print(" ".join(cmd))
    res = subprocess.run(cmd)
    if res.returncode == 0:
        dist_dir = os.path.join(APP_DIR, "dist", "AIPI")
        exe_path = os.path.join(dist_dir, "AIPI.exe" if os.name == "nt" else "AIPI")
        print("\n=======================================================")
        print(f"✅ BUILD SUCCESSFUL! Dist folder: {dist_dir}")
        print(f"Executable path: {exe_path}")
        print("=======================================================\n")
    else:
        print("\nBuild failed with exit code:", res.returncode)

if __name__ == "__main__":
    build()

