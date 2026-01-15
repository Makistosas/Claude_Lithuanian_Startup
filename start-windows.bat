@echo off
REM SaskaitaPro - Windows Quick Start Launcher
REM Double-click this file to start the application

title SaskaitaPro - Lithuanian Invoicing Platform

echo.
echo =============================================
echo   SaskaitaPro - Starting Application...
echo   Lithuanian Small Business Invoicing
echo =============================================
echo.

REM Get script directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [!] Virtual environment not found!
    echo.
    echo Please run setup-windows.ps1 first:
    echo   Right-click setup-windows.ps1 and select "Run with PowerShell"
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Set environment variables
set FLASK_APP=run.py
set FLASK_CONFIG=windows
set FLASK_ENV=development

echo [*] Environment activated
echo [*] Starting Flask server...
echo.
echo =============================================
echo   Application running at:
echo   http://localhost:5000
echo.
echo   Demo Login:
echo   Email:    demo@saskaitapro.lt
echo   Password: demo123456
echo.
echo   Press Ctrl+C to stop the server
echo =============================================
echo.

REM Start the Flask development server
python run.py

REM If server stops, pause to show any error messages
pause
