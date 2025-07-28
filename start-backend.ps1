# PowerShell script to start the AI Agent Platform Backend
Write-Host "Starting AI Agent Platform Backend..." -ForegroundColor Green
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install/update dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
pip install vanna chromadb openai

# Load environment variables and start server
Write-Host "Starting FastAPI server on port 3006..." -ForegroundColor Green
python main.py

Read-Host "Press Enter to exit"
