@echo off
title AI Agent Platform - Quick Start
color 0A

echo ========================================
echo    AI Agent Platform - Quick Start
echo ========================================
echo.
echo This assumes dependencies are already installed.
echo If not, run START_PLATFORM.bat first.
echo.

REM Kill any existing processes
echo Cleaning up existing processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3003') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3006') do taskkill /f /pid %%a >nul 2>&1

echo.
echo Starting Backend Server...
start "AI Agent Backend" cmd /k "call venv\Scripts\activate.bat && python main.py"

echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

echo.
echo Starting Frontend Server...
start "AI Agent Frontend" cmd /k "cd frontend && npm run dev -- --port 3003"

echo.
echo ========================================
echo    Platform Started!
echo ========================================
echo.
echo Backend:  http://localhost:3006
echo Frontend: http://localhost:3003
echo.
echo Opening application in 5 seconds...
timeout /t 5 /nobreak >nul
start http://localhost:3003

echo.
echo Platform is ready!
pause
