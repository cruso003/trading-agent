@echo off
title GoldTrader Dashboard
echo ============================================
echo   GoldTrader AI Agent — Dashboard
echo   http://localhost:5173
echo ============================================
echo.

cd /d "%~dp0\dashboard"

:: Check if node_modules exists
if not exist node_modules (
    echo [1/2] Installing dependencies...
    npm install
    echo       Done.
) else (
    echo [1/2] Dependencies already installed.
)

echo [2/2] Starting dev server...
echo.
npm run dev
pause
