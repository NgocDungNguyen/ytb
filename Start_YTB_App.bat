@echo off
cd /d "%~dp0"
title YTB Desktop App
echo Starting YTB Application...
python ytb.py
if %errorlevel% neq 0 (
    echo.
    echo Application crashed or exited with an error.
    pause
)
