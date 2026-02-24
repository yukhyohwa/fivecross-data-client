@echo off
echo ======================================================
echo    FiveCross Data Client - One-Click Setup (Windows)
echo ======================================================
echo.

:: Move to project root
cd /d "%~dp0.."

:: 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

:: 2. Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [1/5] Creating virtual environment...
    python -m venv venv
) else (
    echo [1/5] Virtual environment already exists.
)

:: 3. Install/Update dependencies
echo [2/5] Installing dependencies...
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

:: 4. Install Playwright browsers
echo [3/5] Installing Playwright Chromium...
playwright install chromium

:: 5. Initialize Git Submodules
echo [4/5] Initializing Git Submodules (SQL Lib)...
git submodule update --init --recursive

:: 6. Check for .env file
if not exist ".env" (
    echo [5/5] Creating .env from template...
    copy .env.example .env
    echo.
    echo [ATTENTION] .env file created. PLEASE EDIT IT with your credentials before running!
) else (
    echo [5/5] .env file already exists.
)

echo.
echo ======================================================
echo    Setup Complete! 
echo    Run your tasks using: python main.py --task ...
echo ======================================================
pause
