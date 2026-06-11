@echo off
REM GyuTron Workspace one-click launcher: backend (8000) + frontend (5173).
REM Double-click this file, wait ~5 seconds, then open http://127.0.0.1:5173
cd /d "%~dp0"

REM backend (skip if already running)
netstat -ano | findstr ":8000 " | findstr LISTENING >nul
if errorlevel 1 (
  start "GyuTron API" cmd /k "cd /d %~dp0apps\api && ..\..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
) else (
  echo Backend already running on 8000.
)

REM frontend (skip if already running)
netstat -ano | findstr ":5173 " | findstr LISTENING >nul
if errorlevel 1 (
  start "GyuTron Web" cmd /k "cd /d %~dp0apps\web && npm.cmd run dev -- --host 127.0.0.1 --port 5173"
) else (
  echo Frontend already running on 5173.
)

timeout /t 5 >nul
start http://127.0.0.1:5173
