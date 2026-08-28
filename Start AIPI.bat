@echo off
title AIPI - AI Protocol Interface Gateway
cd /d "%~dp0"

echo ======================================================================
echo   🌐 AIPI — AI Protocol Interface Gateway & Web Portal
echo   Universal Local AI Gateway, Router & Modern Web Dashboard
echo ======================================================================
echo.
echo Launching AIPI Application & Auto-Opening Web Portal...

python ai_model_manager.py
if errorlevel 1 (
    echo.
    echo AIPI exited with an error.
    pause
)

