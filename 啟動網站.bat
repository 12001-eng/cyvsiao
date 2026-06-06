@echo off
title CYVS International Server
cd /d "%~dp0"

echo [1/2] Checking environment...
set PY=venv\Scripts\python.exe
if not exist venv\Scripts\python.exe set PY=python

echo [2/2] Starting server...
echo ------------------------------------------
echo   URL: http://127.0.0.1:8510
echo ------------------------------------------
echo (Close this window to stop the server)

:: Delay open browser
start "" cmd /c "timeout /t 3 >nul && start http://127.0.0.1:8510"

:: Start App
"%PY%" app.py

echo.
echo Server stopped.
pause
