@echo off
title GoldTrader AI Agent — Setup
echo ============================================
echo   GoldTrader AI Agent — First Time Setup
echo ============================================
echo.

cd /d "%~dp0"

:: Step 1: Create venv
echo [1/4] Creating virtual environment...
if exist venv (
    echo       venv already exists, skipping.
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv. Is Python 3.11+ installed?
        pause
        exit /b 1
    )
    echo       Done.
)

:: Step 2: Activate and install
echo [2/4] Installing dependencies...
call venv\Scripts\activate
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)
echo       Done.

:: Step 3: Create .env if missing
echo [3/4] Checking .env...
if exist .env (
    echo       .env already exists, skipping.
) else (
    copy .env.example .env >nul
    echo       Created .env from template.
    echo       !! EDIT .env WITH YOUR API KEYS AND MT5 CREDENTIALS !!
)

:: Step 4: Create data/logs directories
echo [4/4] Creating directories...
if not exist agent\data mkdir agent\data
if not exist agent\logs mkdir agent\logs
echo       Done.

echo.
echo ============================================
echo   Setup complete!
echo.
echo   Next steps:
echo   1. Edit .env with your credentials
echo   2. Open MetaTrader 5 and log in
echo   3. Run start_dry.bat for first test
echo ============================================
pause
