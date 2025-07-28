@echo off
title AI Agent Platform - Production Deployment
color 0A

REM AI Agent Platform - Production Deployment Script for Windows
REM This script deploys the AI Agent Platform to a Windows server using Docker Compose

setlocal enabledelayedexpansion

REM Configuration
set PROJECT_NAME=ai-agent-platform
set COMPOSE_FILE=docker-compose.production.yml
set ENV_FILE=.env
set BACKUP_DIR=backup\%PROJECT_NAME%

echo ==========================================
echo   AI Agent Platform - Production Deploy
echo ==========================================
echo.

REM Check requirements
echo [1/6] Checking system requirements...
echo ==========================================

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist "%ENV_FILE%" (
    echo ERROR: .env file not found. Please copy .env.production to .env and configure it.
    pause
    exit /b 1
)

echo SUCCESS: System requirements check passed
echo.

REM Create directories
echo [2/6] Creating necessary directories...
echo ==========================================

if not exist "data" mkdir data
if not exist "agent_documents" mkdir agent_documents
if not exist "agent_vectors" mkdir agent_vectors
if not exist "vanna_cache" mkdir vanna_cache
if not exist "logs" mkdir logs
if not exist "nginx\ssl" mkdir nginx\ssl
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

echo SUCCESS: Directories created
echo.

REM Backup existing deployment
echo [3/6] Creating backup of existing deployment...
echo ==========================================

REM Check if services are running
docker-compose -f "%COMPOSE_FILE%" ps | findstr "Up" >nul 2>&1
if not errorlevel 1 (
    echo Creating backup...
    
    REM Create backup directory with timestamp
    for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
    set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
    set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
    set "TIMESTAMP=%YYYY%%MM%%DD%_%HH%%Min%%Sec%"
    set "BACKUP_PATH=%BACKUP_DIR%\backup_%TIMESTAMP%"
    mkdir "%BACKUP_PATH%"
    
    REM Backup database
    echo Backing up PostgreSQL database...
    docker-compose -f "%COMPOSE_FILE%" exec -T postgres pg_dump -U ai_agents_user ai_agents_db > "%BACKUP_PATH%\database.sql"
    
    REM Backup data directories
    echo Backing up data directories...
    tar -czf "%BACKUP_PATH%\data.tar.gz" data agent_documents agent_vectors vanna_cache 2>nul
    
    REM Backup configuration
    copy "%ENV_FILE%" "%BACKUP_PATH%\env.backup" >nul
    
    echo SUCCESS: Backup created at %BACKUP_PATH%
) else (
    echo No existing deployment found, skipping backup
)
echo.

REM Build and deploy
echo [4/6] Building and deploying application...
echo ==========================================

echo Pulling latest Docker images...
docker-compose -f "%COMPOSE_FILE%" pull

echo Building application images...
docker-compose -f "%COMPOSE_FILE%" build --no-cache

echo Stopping existing services...
docker-compose -f "%COMPOSE_FILE%" down

echo Starting services...
docker-compose -f "%COMPOSE_FILE%" up -d

echo Waiting for services to start...
timeout /t 30 /nobreak >nul

echo SUCCESS: Application deployed
echo.

REM Health checks
echo [5/6] Checking service health...
echo ==========================================

REM Check if all services are running
docker-compose -f "%COMPOSE_FILE%" ps | findstr "Exit" >nul 2>&1
if not errorlevel 1 (
    echo ERROR: Some services failed to start. Check logs with: docker-compose -f %COMPOSE_FILE% logs
    pause
    exit /b 1
)

REM Check backend health
echo Checking backend health...
set /a counter=0
:backend_check
curl -f http://localhost:3006/health >nul 2>&1
if not errorlevel 1 (
    echo SUCCESS: Backend is healthy
    goto frontend_check
)
set /a counter+=1
if %counter% geq 30 (
    echo ERROR: Backend health check failed
    pause
    exit /b 1
)
timeout /t 2 /nobreak >nul
goto backend_check

:frontend_check
REM Check frontend
echo Checking frontend health...
set /a counter=0
:frontend_check_loop
curl -f http://localhost:3003 >nul 2>&1
if not errorlevel 1 (
    echo SUCCESS: Frontend is healthy
    goto health_complete
)
set /a counter+=1
if %counter% geq 30 (
    echo ERROR: Frontend health check failed
    pause
    exit /b 1
)
timeout /t 2 /nobreak >nul
goto frontend_check_loop

:health_complete
echo SUCCESS: All services are healthy
echo.

REM Cleanup
echo [6/6] Cleaning up unused Docker resources...
echo ==========================================

docker system prune -f >nul 2>&1
docker volume prune -f >nul 2>&1

echo SUCCESS: Cleanup completed
echo.

REM Show status
echo ==========================================
echo   Deployment Status
echo ==========================================
echo.
docker-compose -f "%COMPOSE_FILE%" ps
echo.
echo Application URLs:
echo   Frontend: http://localhost:3003
echo   Backend API: http://localhost:3006
echo   API Documentation: http://localhost:3006/docs
echo.
echo Useful commands:
echo   View logs: docker-compose -f %COMPOSE_FILE% logs -f
echo   Stop services: docker-compose -f %COMPOSE_FILE% down
echo   Restart services: docker-compose -f %COMPOSE_FILE% restart
echo.
echo ==========================================
echo   Deployment completed successfully!
echo ==========================================
echo.

pause
