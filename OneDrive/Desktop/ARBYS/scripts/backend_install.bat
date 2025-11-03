@echo off
setlocal enabledelayedexpansion

REM Backend Installer for ARBYS Flask API (Windows)
REM This script sets up a Python virtual environment, installs real dependencies,
REM and starts the backend API server that the desktop client and mobile web app use.

REM Detect script directory
set SCRIPT_DIR=%~dp0
set BACKEND_ROOT=%SCRIPT_DIR%..
pushd "%BACKEND_ROOT%"

echo =============================================================
echo ARBYS Backend Setup (Real Data Only)
echo =============================================================
echo Location: %BACKEND_ROOT%
echo.

REM Enforce Real-Data-Only policy by default unless user overrides
if not defined REAL_DATA_ONLY (
  set REAL_DATA_ONLY=true
)
echo Policy: REAL_DATA_ONLY=%REAL_DATA_ONLY%
echo Synthetic generation is disabled when REAL_DATA_ONLY is true.
echo.

REM Check for Python 3.10+
for /f "tokens=*" %%P in ('python -c "import sys; print(sys.version_info.major, sys.version_info.minor)" 2^>nul') do set PYV=%%P
if not defined PYV (
  echo Python not found on PATH. Please install Python 3.10+ from https://www.python.org/downloads/windows/ and re-run this script.
  goto :end
)

REM Create virtual environment for backend
set VENV_DIR=.venv_backend
if not exist "%VENV_DIR%" (
  echo Creating virtual environment at %VENV_DIR% ...
  python -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo Failed to create virtual environment. Please ensure Python 3.10+ is installed.
    goto :end
  )
)

REM Activate venv in this shell
call "%VENV_DIR%\Scripts\activate" || (
  echo Failed to activate virtual environment.
  goto :end
)

echo Installing backend dependencies (this may take a minute)...
pip install --upgrade pip
pip install -r requirements.txt
pip install Flask Flask-Cors

REM Verify critical config files exist
if not exist "config\bot_config.json" (
  echo WARNING: Missing config\bot_config.json (API provider configuration).
  echo The backend requires real API keys/providers. Opening a template for editing...
  mkdir config 2>nul
  (
    echo {
    echo   "providers": {
    echo     "sofascore_scraper": {"enabled": true, "priority": 2},
    echo     "the_odds_api": {"enabled": true, "priority": 1, "api_key": "REPLACE_WITH_YOUR_THEODDSAPI_KEY"},
    echo     "api_sports": {"enabled": false, "priority": 3, "api_key": "REPLACE_WITH_YOUR_API_SPORTS_KEY"}
    echo   }
    echo }
  ) > "config\bot_config.json"
  start notepad.exe "config\bot_config.json"
  echo Please update real API keys. Save and close Notepad, then re-run this script.
  goto :end
)

REM Start the backend Flask API server
echo Starting backend API server (real data only). A console window will open.
echo Endpoint: http://localhost:5000/api/opportunities
echo Health:   http://localhost:5000/api/health
echo.
start "ARBYS Backend" cmd /c "%VENV_DIR%\Scripts\python.exe" "backend\api_server.py"

echo Backend launch initiated. If a firewall prompt appears, allow local access.
echo To stop the server, close the backend console window or press Ctrl+C in it.
echo.
echo Done.

:end
popd
exit /b 0