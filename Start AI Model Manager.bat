@echo off
title AI Model Manager
cd /d "%~dp0"

where pythonw >nul 2>&1
if %errorlevel%==0 (
    start "" pythonw ai_model_manager.py
    exit /b
)

python ai_model_manager.py
if errorlevel 1 (
    echo.
    echo Failed to launch. Make sure Python 3 is installed and on your PATH.
    pause
)
