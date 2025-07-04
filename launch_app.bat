@echo off
echo ========================================
echo   Unified Language App Launcher
echo ========================================
echo.
echo Initializing application...
echo.

cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or later
    pause
    exit /b 1
)

REM Check if virtual environment exists, create if not
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade requirements
echo Installing required packages...
pip install -r requirements.txt --quiet

REM Check if installation was successful
if %errorlevel% neq 0 (
    echo WARNING: Some packages may not have installed correctly
    echo The application may not work properly
    pause
)

REM Launch the application
echo.
echo ========================================
echo   Starting Unified Language App...
echo ========================================
echo.

cd src
python main.py

REM Keep window open if there's an error
if %errorlevel% neq 0 (
    echo.
    echo Application closed with error code: %errorlevel%
    pause
)

REM Deactivate virtual environment
deactivate
