@echo off
setlocal
title NexusLoop Ultimate
chcp 65001 >nul

echo =======================================================
echo          NEXUSLOOP ULTIMATE - INDUSTRIAL DECISION OS
echo =======================================================
echo.

if exist venv\Scripts\python.exe (
  set PY=venv\Scripts\python.exe
) else if exist .venv\Scripts\python.exe (
  set PY=.venv\Scripts\python.exe
) else (
  set PY=python
)

echo [1/2] Khoi dong NexusLoop Core + Ultimate UI...
start "NexusLoop Ultimate" cmd /k "%PY% -m uvicorn main:app --host 127.0.0.1 --port 8000"

timeout /t 2 /nobreak >nul
echo [2/2] Mo trinh duyet...
start "" http://localhost:8000

echo.
echo URL: http://localhost:8000
echo UI va API chay cung mot server, khong can Vite/Node.
echo.
pause
endlocal
