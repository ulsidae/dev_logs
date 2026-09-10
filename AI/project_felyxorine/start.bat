@echo off
title VRM Server

cd /d "%~dp0"

echo ========================================
echo        project FELYXORINE
echo ========================================
echo.
echo Starting Flask...
echo.

start "" /b python server.py

timeout /t 2 /nobreak >nul

start "" http://127.0.0.1:8079

echo.
echo Server is running.
echo.
pause
