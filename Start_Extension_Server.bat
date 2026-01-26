@echo off
cd /d "%~dp0"
title YTB Extension Server
echo ===================================================
echo Starting YTB Extension Server...
echo Minimize this window, but DO NOT CLOSE IT.
echo This server is required for the Chrome Extension.
echo ===================================================
echo.
python server.py
pause
