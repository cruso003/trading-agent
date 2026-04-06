@echo off
title GoldTrader API Server
echo ============================================
echo   GoldTrader AI Agent — API Server
echo   http://localhost:8000
echo   Docs: http://localhost:8000/docs
echo ============================================
echo.

cd /d "%~dp0"
call venv\Scripts\activate 2>nul || (
    echo [ERROR] Virtual environment not found.
    pause
    exit /b 1
)

python -m api.main
pause
