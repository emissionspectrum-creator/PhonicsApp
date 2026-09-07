@echo off
cd /d "%~dp0"
start "" python server.py
timeout /t 1 >nul
start "" "http://127.0.0.1:5001"
