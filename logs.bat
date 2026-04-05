@echo off
title GoldTrader AI Agent — Log Viewer
echo ============================================
echo   GoldTrader AI Agent — Log Viewer
echo ============================================
echo.
echo   1. Tail live log
echo   2. Show trades only
echo   3. Show errors only
echo   4. Show Claude decisions
echo   5. Show last 50 lines
echo   6. Open log folder
echo.

cd /d "%~dp0"

set /p choice="Choose (1-6): "

if "%choice%"=="1" (
    echo Tailing log... Press Ctrl+C to stop.
    powershell -Command "Get-Content agent\logs\agent.log -Wait -Tail 30"
)
if "%choice%"=="2" (
    findstr /i "PLACED CLOSED TP1.HIT" agent\logs\agent.log
    pause
)
if "%choice%"=="3" (
    findstr /i "ERROR CRITICAL" agent\logs\agent.log
    pause
)
if "%choice%"=="4" (
    findstr /i "Claude: A+\|B\|SKIP" agent\logs\agent.log
    pause
)
if "%choice%"=="5" (
    powershell -Command "Get-Content agent\logs\agent.log -Tail 50"
    pause
)
if "%choice%"=="6" (
    explorer agent\logs
)
