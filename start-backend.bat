@echo off
echo Starting AI Agent Platform Backend...
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt
pip install vanna chromadb openai

REM Load environment variables and start server
echo Starting FastAPI server on port 3006...
python main.py

pause
