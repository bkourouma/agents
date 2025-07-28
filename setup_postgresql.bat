@echo off
REM PostgreSQL Setup Script for AI Agent Platform
REM This script helps set up PostgreSQL and migrate from SQLite

echo ========================================
echo PostgreSQL Setup for AI Agent Platform
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ and try again
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Installing PostgreSQL dependencies...
pip install psycopg2-binary pandas asyncpg
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo Creating .env file from PostgreSQL template...
    copy .env.postgresql .env
    echo.
    echo IMPORTANT: Please edit .env file with your PostgreSQL credentials
    echo Default connection: postgresql+asyncpg://postgres:postgres@localhost:5432/ai_agent_platform
    echo.
    echo Press any key after updating .env file...
    pause
)

REM Check PostgreSQL connection
echo Testing PostgreSQL connection...
python -c "
import asyncio
import sys
sys.path.append('src')
from src.core.database import test_connection
success = asyncio.run(test_connection())
if not success:
    print('ERROR: Cannot connect to PostgreSQL')
    print('Please check:')
    print('1. PostgreSQL is installed and running')
    print('2. Database credentials in .env file are correct')
    print('3. Database ai_agent_platform exists')
    exit(1)
else:
    print('✅ PostgreSQL connection successful!')
"
if errorlevel 1 (
    echo.
    echo PostgreSQL connection failed. Please check the setup guide:
    echo POSTGRESQL_SETUP_GUIDE.md
    pause
    exit /b 1
)

REM Run PostgreSQL setup
echo.
echo Running PostgreSQL setup and migration...
python setup_postgresql.py
if errorlevel 1 (
    echo ERROR: PostgreSQL setup failed
    pause
    exit /b 1
)

REM Run tests
echo.
echo Running PostgreSQL tests...
python test_postgresql_setup.py
if errorlevel 1 (
    echo WARNING: Some tests failed, but setup might still work
    echo Check the logs above for details
)

echo.
echo ========================================
echo PostgreSQL Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Start the backend: python main.py
echo 2. Start the frontend: cd frontend && npm run dev
echo 3. Access the application at http://localhost:3003
echo.
echo For troubleshooting, see: POSTGRESQL_SETUP_GUIDE.md
echo.
pause
