@echo off
setlocal

rem Determine repository root relative to this script
set "ROOT=%~dp0"

rem Choose Python: prefer venv if present, else system
set "VENV_PY=%ROOT%.venv\Scripts\python.exe"
if exist "%VENV_PY%" (
  set "PY=%VENV_PY%"
) else (
  set "PY=python"
)

rem Quick check: ensure Flask is available, install if missing
"%PY%" -c "import flask" >nul 2>&1
if errorlevel 1 (
  echo Installing Flask backend requirements...
  "%PY%" -m pip install -r "%ROOT%backend\requirements.txt"
)

rem Start backend (Flask)
start "backend" "%PY%" "%ROOT%backend\app.py"

rem Start frontend (Vite dev server)
start "frontend" /D "%ROOT%frontend" cmd /k npm run dev

echo.
echo Servers starting...
echo - Backend: http://127.0.0.1:5000
echo - Frontend: http://localhost:5173

endlocal
