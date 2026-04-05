@echo off
title GoldTrader AI Agent — Dry Run
echo ============================================
echo   GoldTrader AI Agent — DRY RUN MODE
echo   No trades will be executed
echo ============================================
echo.

cd /d "%~dp0"
call venv\Scripts\activate 2>nul || (
    echo [ERROR] Virtual environment not found.
    echo Run: python -m venv venv
    echo Then: venv\Scripts\activate
    echo Then: pip install -r requirements.txt
    pause
    exit /b 1
)

python -m agent.main --dry-run --debug
pause
