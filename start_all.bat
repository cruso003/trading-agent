@echo off
title GoldTrader — Full Stack
echo ============================================
echo   GoldTrader AI Agent — Full Stack Launch
echo   Agent  : demo account (real execution)
echo   API    : http://localhost:8000
echo   Dashboard: http://localhost:5173
echo ============================================
echo.

cd /d "%~dp0"

:: Safety check — confirm demo account
findstr /i "ACTIVE_ACCOUNT=demo" .env >nul 2>&1
if errorlevel 1 (
    echo [WARNING] ACTIVE_ACCOUNT is not set to "demo" in .env
    echo.
    set /p confirm="Continue anyway? (y/N): "
    if /i not "%confirm%"=="y" exit /b 1
)

echo [1/3] Starting API server...
start "GoldTrader API" cmd /k "cd /d "%~dp0" && call venv\Scripts\activate && python -m api.main"

echo [2/3] Starting Agent (demo)...
start "GoldTrader Agent" cmd /k "cd /d "%~dp0" && call venv\Scripts\activate && python -m agent.main"

echo [3/3] Starting Dashboard...
start "GoldTrader Dashboard" cmd /k "cd /d "%~dp0\dashboard" && npm run dev"

echo.
echo All three windows launched.
echo Close each window individually to stop.
echo.
pause
