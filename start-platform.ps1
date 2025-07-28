# AI Agent Platform Startup Script
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   AI Agent Platform - Starting..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\activate.bat")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    Write-Host "Then: venv\Scripts\activate && pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if frontend dependencies are installed
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location ..
}

# Check backend dependencies
Write-Host "Checking backend dependencies..." -ForegroundColor Yellow
& "venv\Scripts\python.exe" -c "import fastapi" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing backend dependencies..." -ForegroundColor Yellow
    & "venv\Scripts\activate.bat"
    & "venv\Scripts\pip.exe" install -r requirements.txt
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   AI Agent Platform - Ready to Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend will start on: " -NoNewline
Write-Host "http://127.0.0.1:3006" -ForegroundColor Green
Write-Host "Frontend will start on: " -NoNewline
Write-Host "http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "Demo credentials:" -ForegroundColor Cyan
Write-Host "  Username: alice" -ForegroundColor White
Write-Host "  Password: alicepassword123" -ForegroundColor White
Write-Host ""
Write-Host "Features available:" -ForegroundColor Cyan
Write-Host "  - Intelligent chat with AI orchestration" -ForegroundColor White
Write-Host "  - Agent management and templates" -ForegroundColor White
Write-Host "  - Conversation history and analytics" -ForegroundColor White
Write-Host "  - Real-time intent analysis and routing" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C in any server window to stop" -ForegroundColor Yellow
Write-Host ""

# Start backend in a new PowerShell window
Write-Host "Starting backend server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { Set-Location '$PWD'; Write-Host 'Starting backend...' -ForegroundColor Green; .\venv\Scripts\Activate.ps1; python main.py }" -WindowStyle Normal

# Wait a moment for backend to start
Write-Host "Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start frontend in a new PowerShell window
Write-Host "Starting frontend server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { Set-Location '$PWD\frontend'; Write-Host 'Starting frontend...' -ForegroundColor Green; npm run dev }" -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Both servers are starting..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend API: " -NoNewline
Write-Host "http://127.0.0.1:3006" -ForegroundColor Green
Write-Host "Frontend UI: " -NoNewline
Write-Host "http://localhost:5173" -ForegroundColor Green
Write-Host "API Documentation: " -NoNewline
Write-Host "http://127.0.0.1:3006/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Waiting for servers to fully initialize..." -ForegroundColor Yellow
Write-Host "The platform will open automatically in your browser in 15 seconds..." -ForegroundColor Cyan
Write-Host ""

# Wait for servers to fully start
Start-Sleep -Seconds 15

# Test backend connection
Write-Host "Testing backend connection..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:3006/api/v1/status" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "Backend is responding!" -ForegroundColor Green
} catch {
    Write-Host "Warning: Backend may still be starting up..." -ForegroundColor Yellow
    Write-Host "Please wait a moment and refresh the browser if needed." -ForegroundColor Yellow
}

# Open the frontend in default browser
Write-Host "Opening platform in your browser..." -ForegroundColor Green
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Platform is ready!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend: " -NoNewline
Write-Host "http://localhost:5173" -ForegroundColor Green
Write-Host "Backend: " -NoNewline
Write-Host "http://127.0.0.1:3006" -ForegroundColor Green
Write-Host ""
Write-Host "Quick Start Guide:" -ForegroundColor Cyan
Write-Host "1. Login with: alice / alicepassword123" -ForegroundColor White
Write-Host "2. Go to Chat page for intelligent conversations" -ForegroundColor White
Write-Host "3. Try different message types to see AI routing:" -ForegroundColor White
Write-Host "   - 'I need billing help' (Customer Service)" -ForegroundColor Gray
Write-Host "   - 'Research AI trends' (Research Agent)" -ForegroundColor Gray
Write-Host "   - 'Analyze our finances' (Financial Analysis)" -ForegroundColor Gray
Write-Host "4. Check Agents page to manage AI agents" -ForegroundColor White
Write-Host "5. View Conversations for chat history" -ForegroundColor White
Write-Host ""
Write-Host "To stop the platform:" -ForegroundColor Yellow
Write-Host "1. Close both server windows, OR" -ForegroundColor White
Write-Host "2. Press Ctrl+C in each server window" -ForegroundColor White
Write-Host ""
Write-Host "Troubleshooting:" -ForegroundColor Yellow
Write-Host "- If styling looks broken, refresh the browser" -ForegroundColor White
Write-Host "- If login fails, check backend server window for errors" -ForegroundColor White
Write-Host "- If frontend won't load, check frontend server window" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit this window"
