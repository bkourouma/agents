@echo off
title AI Agent Platform with Vanna AI
color 0A

echo ========================================
echo    AI Agent Platform with Vanna AI
echo ========================================
echo.

REM Kill any existing processes on ports 3003 and 3006
echo Cleaning up existing processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3003') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3006') do taskkill /f /pid %%a >nul 2>&1

echo.
echo [1/4] Setting up Backend...
echo ========================================

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing backend dependencies (this may take a few minutes)...
echo - Installing core requirements...
pip install -r requirements.txt
echo - Installing Vanna AI...
pip install vanna
echo - Installing ChromaDB...
pip install chromadb
echo - Installing OpenAI...
pip install openai
echo Backend dependencies installed!

echo.
echo [2/4] Setting up Frontend...
echo ========================================

REM Navigate to frontend directory and install dependencies
cd frontend
if not exist "node_modules" (
    echo Installing frontend dependencies (this may take a few minutes)...
    npm install
) else (
    echo Frontend dependencies already installed.
)
cd ..

echo.
echo [3/4] Starting Backend Server...
echo ========================================
echo Backend will start on: http://localhost:3006
echo API Documentation: http://localhost:3006/docs

REM Start backend in a new window
start "AI Agent Backend" cmd /k "call venv\Scripts\activate.bat && python main.py"

REM Wait for backend to start
timeout /t 5 /nobreak >nul

echo.
echo [4/4] Starting Frontend Server...
echo ========================================
echo Frontend will start on: http://localhost:3003

REM Start frontend in a new window
start "AI Agent Frontend" cmd /k "cd frontend && npm run dev -- --port 3003"

echo.
echo ========================================
echo    Platform Started Successfully!
echo ========================================
echo.
echo Backend:  http://localhost:3006
echo Frontend: http://localhost:3003
echo API Docs: http://localhost:3006/docs
echo.
echo Features Available:
echo - User Authentication
echo - AI Agent Management  
echo - Knowledge Base Upload
echo - Database Chat with Vanna AI
echo - Natural Language to SQL
echo - Orchestrator Routing
echo.
echo Demo Credentials:
echo Username: alice
echo Password: alicepassword123
echo.
echo Press any key to open the application...
pause >nul

REM Open the application in default browser
start http://localhost:3003

echo.
echo Application opened in browser!
echo Keep this window open to monitor the platform.
echo.
echo To stop the platform:
echo 1. Close both server windows, OR
echo 2. Press Ctrl+C in each server window
echo.
pause
