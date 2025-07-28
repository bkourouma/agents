@echo off
echo Starting AI Agents Development Environment...

echo.
echo Starting Backend on port 3006...
start "Backend" cmd /k "cd /d d:\ONEDRIVE\APPS\AI_AGENTS && python -m uvicorn main:app --reload --port 3006"

echo.
echo Waiting 5 seconds before starting frontend...
timeout /t 5 /nobreak > nul

echo.
echo Starting Frontend on port 3003...
start "Frontend" cmd /k "cd /d d:\ONEDRIVE\APPS\AI_AGENTS\frontend && npm run dev -- --port 3003"

echo.
echo Both servers are starting...
echo Backend: http://localhost:3006
echo Frontend: http://localhost:3003
echo.
pause