@echo off
title GoldTrader AI Agent — LIVE
color 4F
echo ============================================
echo   GoldTrader AI Agent — LIVE ACCOUNT
echo   !! REAL MONEY — REAL TRADES !!
echo ============================================
echo.

cd /d "%~dp0"
call venv\Scripts\activate 2>nul || (
    echo [ERROR] Virtual environment not found.
    pause
    exit /b 1
)

:: Safety checks
findstr /i "ACTIVE_ACCOUNT=live" .env >nul 2>&1
if errorlevel 1 (
    echo [ERROR] ACTIVE_ACCOUNT is not set to "live" in .env
    echo Change ACTIVE_ACCOUNT=live in .env first.
    pause
    exit /b 1
)

echo WARNING: This will execute real trades with real money.
echo.
set /p confirm="Type LIVE to confirm: "
if not "%confirm%"=="LIVE" (
    echo Aborted.
    pause
    exit /b 1
)

python -m agent.main
pause
