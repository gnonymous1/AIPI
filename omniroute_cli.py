"""
omniroute_cli.py - Command-line front-end for Omniroute status/start/fix.

Usage:
    python omniroute_cli.py status
    python omniroute_cli.py start
    python omniroute_cli.py fix
    python omniroute_cli.py auto        # status; start if down
"""
import sys

from omniroute_service import status, start, fix


def main():
    action = (sys.argv[1] if len(sys.argv) > 1 else "auto").lower()
    if action == "status":
        ok, detail = status()
        print(("GREEN - " if ok else "RED - ") + detail)
    elif action == "start":
        ok, detail = start()
        print(("GREEN - " if ok else "RED - ") + detail)
    elif action == "fix":
        ok, detail = fix()
        print(("GREEN - " if ok else "RED - ") + detail)
    else:  # auto
        ok, detail = status()
        print(detail)
        if not ok:
            print("\nLaunching Omniroute...")
            ok2, detail2 = start()
            print(("GREEN - " if ok2 else "RED - ") + detail2)


if __name__ == "__main__":
    main()
