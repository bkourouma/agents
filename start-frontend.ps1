# PowerShell script to start the AI Agent Platform Frontend
Write-Host "Starting AI Agent Platform Frontend..." -ForegroundColor Green
Write-Host ""

# Navigate to frontend directory
Set-Location frontend

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm install
}

# Start the development server
Write-Host "Starting React development server on port 3003..." -ForegroundColor Green
npm run dev -- --port 3003

Read-Host "Press Enter to exit"
