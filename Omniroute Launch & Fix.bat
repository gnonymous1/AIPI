@echo off
title Omniroute Launch &amp; Fix
cd /d "%~dp0"

where python >nul 2>&1
if not %errorlevel%==0 (
    echo Python 3 was not found on PATH.
    pause
    exit /b
)

echo ==============================================
echo   Omniroute - status, and launch if it is down
echo ==============================================
python -X utf8 omniroute_cli.py auto
echo.
echo Dashboard: http://127.0.0.1:20128/dashboard/api-manager
echo Press any key to close when done. You can re-run this any time.
pause >nul
