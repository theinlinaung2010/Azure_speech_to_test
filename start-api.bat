@echo off
echo Starting Azure Speech-to-Text Flask API...
echo.

cd /d "%~dp0api"

if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and configure your Azure credentials.
    pause
    exit /b 1
)

if not exist "uploads" mkdir uploads
if not exist "out" mkdir out

echo Checking Python environment...
python --version

echo.
echo Starting Flask server on http://localhost:5000
echo Press Ctrl+C to stop
echo.

python app.py
