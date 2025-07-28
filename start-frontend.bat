@echo off
echo Starting AI Agent Platform Frontend...
echo.

REM Navigate to frontend directory
cd frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing frontend dependencies...
    npm install
)

REM Start the development server
echo Starting React development server on port 3003...
npm run dev -- --port 3003

pause
