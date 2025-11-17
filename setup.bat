@echo off
REM Professional Sales Automation System - Setup Script (Windows)
REM This script sets up a Python virtual environment and installs all dependencies

echo ==========================================
echo 🚀 PROFESSIONAL SALESMAN - SETUP
echo ==========================================
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Create virtual environment
echo.
echo 📦 Creating virtual environment...
if exist venv (
    echo ⚠️  Virtual environment already exists. Skipping creation.
) else (
    python -m venv venv
    echo ✅ Virtual environment created
)

REM Activate virtual environment
echo.
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo 📦 Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo 📦 Installing dependencies...
if exist requirements.txt (
    pip install -r requirements.txt
    echo ✅ Dependencies installed
) else (
    echo ❌ requirements.txt not found!
    pause
    exit /b 1
)

REM Create data directory if it doesn't exist
echo.
echo 📁 Setting up data directory...
if not exist data mkdir data
echo ✅ Data directory ready

REM Check for .env file
echo.
if exist .env (
    echo ✅ .env file found
) else (
    echo ⚠️  .env file not found
    echo 📝 Creating .env from template...
    if exist .env.example (
        copy .env.example .env
        echo ✅ Created .env file - PLEASE EDIT IT WITH YOUR CREDENTIALS!
    ) else (
        echo ❌ .env.example not found
    )
)

REM Summary
echo.
echo ==========================================
echo ✅ SETUP COMPLETE!
echo ==========================================
echo.
echo Next steps:
echo 1. Edit .env file with your credentials
echo.
echo 2. Activate virtual environment (if not already active):
echo    venv\Scripts\activate
echo.
echo 3. Run the system:
echo    python main.py
echo.
echo To deactivate virtual environment later:
echo    deactivate
echo.
echo ==========================================
pause
