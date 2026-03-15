@echo off
echo Installing Azure Speech-to-Text API dependencies...
echo.

cd /d "%~dp0"

REM Check Python version
echo Checking Python version...
python --version

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create directories
if not exist "uploads" mkdir uploads
if not exist "out" mkdir out

REM Setup environment file
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo WARNING: Edit .env and add your Azure credentials before running the server!
)

echo.
echo Installation complete!
echo.
echo Next steps:
echo 1. Edit .env and add your Azure Speech credentials
echo 2. Run: venv\Scripts\activate.bat
echo 3. Run: python app.py
echo.
pause
