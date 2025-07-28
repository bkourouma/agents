@echo off
title AI Agent Platform - Development Environment Setup
color 0A

REM AI Agent Platform - Development Environment Setup Script for Windows
REM This script sets up the development environment for the AI Agent Platform

setlocal enabledelayedexpansion

echo ==========================================
echo   AI Agent Platform - Development Setup
echo ==========================================
echo.

REM Check Python installation
echo [1/8] Checking Python installation...
echo ==========================================

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.11 or higher from https://python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo SUCCESS: Python %PYTHON_VERSION% found
echo.

REM Check Node.js installation
echo [2/8] Checking Node.js installation...
echo ==========================================

node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH.
    echo Please install Node.js 18 or higher from https://nodejs.org
    pause
    exit /b 1
)

for /f "tokens=1" %%i in ('node --version 2^>^&1') do set NODE_VERSION=%%i
echo SUCCESS: Node.js %NODE_VERSION% found
echo.

REM Check npm installation
npm --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm is not installed or not in PATH.
    pause
    exit /b 1
)

echo SUCCESS: npm found
echo.

REM Create directories
echo [3/8] Creating necessary directories...
echo ==========================================

if not exist "data" mkdir data
if not exist "agent_documents" mkdir agent_documents
if not exist "agent_vectors" mkdir agent_vectors
if not exist "vanna_cache" mkdir vanna_cache
if not exist "logs" mkdir logs

echo SUCCESS: Directories created
echo.

REM Setup Python virtual environment
echo [4/8] Setting up Python virtual environment...
echo ==========================================

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo SUCCESS: Python environment setup completed
echo.

REM Setup frontend environment
echo [5/8] Setting up frontend environment...
echo ==========================================

cd frontend

echo Installing Node.js dependencies...
npm install
if errorlevel 1 (
    echo ERROR: Failed to install Node.js dependencies
    cd ..
    pause
    exit /b 1
)

cd ..

echo SUCCESS: Frontend environment setup completed
echo.

REM Setup environment configuration
echo [6/8] Setting up environment configuration...
echo ==========================================

if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env >nul
    echo SUCCESS: .env file created
    echo.
    echo WARNING: Please edit .env file and add your API keys:
    echo   - OPENAI_API_KEY
    echo   - ANTHROPIC_API_KEY (optional)
    echo   - Other configuration as needed
) else (
    echo .env file already exists
)

echo SUCCESS: Environment configuration ready
echo.

REM Check optional services
echo [7/8] Checking optional services...
echo ==========================================

REM Check PostgreSQL
pg_isready >nul 2>&1
if not errorlevel 1 (
    echo SUCCESS: PostgreSQL found and running
) else (
    echo WARNING: PostgreSQL not found. Using SQLite for development.
    echo To use PostgreSQL, install it and configure DATABASE_URL in .env
)

REM Check Redis
redis-cli ping >nul 2>&1
if not errorlevel 1 (
    echo SUCCESS: Redis found and running
) else (
    echo WARNING: Redis not found. Some features may not work optimally.
    echo To install Redis, download from https://redis.io/download
)

echo.

REM Run basic tests
echo [8/8] Running basic tests...
echo ==========================================

echo Testing backend imports...
call venv\Scripts\activate.bat
python -c "import src.main; print('Backend imports successful')" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Backend import test failed
    pause
    exit /b 1
)

echo Testing frontend build...
cd frontend
npm run build >nul 2>&1
if errorlevel 1 (
    echo ERROR: Frontend build test failed
    cd ..
    pause
    exit /b 1
)
cd ..

echo SUCCESS: Basic tests passed
echo.

REM Show next steps
echo ==========================================
echo   Development Environment Ready!
echo ==========================================
echo.
echo Next steps:
echo   1. Edit .env file with your API keys
echo   2. Start the development servers:
echo.
echo      Backend (in one terminal):
echo      venv\Scripts\activate.bat
echo      python main.py
echo.
echo      Frontend (in another terminal):
echo      cd frontend
echo      npm run dev
echo.
echo   3. Access the application:
echo      Frontend: http://localhost:3003
echo      Backend API: http://localhost:3006
echo      API Docs: http://localhost:3006/docs
echo.
echo   Alternative: Use Docker for development:
echo      docker-compose up
echo.
echo ==========================================
echo   Development environment setup completed!
echo ==========================================
echo.

pause
