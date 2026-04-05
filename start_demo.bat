@echo off
title GoldTrader AI Agent — Demo
echo ============================================
echo   GoldTrader AI Agent — DEMO ACCOUNT
echo   Trades will execute on demo account
echo ============================================
echo.

cd /d "%~dp0"
call venv\Scripts\activate 2>nul || (
    echo [ERROR] Virtual environment not found.
    pause
    exit /b 1
)

:: Safety check
findstr /i "ACTIVE_ACCOUNT=demo" .env >nul 2>&1
if errorlevel 1 (
    echo [WARNING] ACTIVE_ACCOUNT is not set to "demo" in .env
    echo Please verify your .env before continuing.
    echo.
    set /p confirm="Continue anyway? (y/N): "
    if /i not "%confirm%"=="y" exit /b 1
)

python -m agent.main
pause
