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
if not exist "venv\Scripts\python.exe" (
    echo [!] Virtual environment not found!
    echo.
    echo Please run setup first:
    echo   Double-click setup-windows.bat
    echo   OR right-click setup-windows.ps1 and select "Run with PowerShell"
    echo.
    pause
    exit /b 1
)

REM Check if Flask is installed
venv\Scripts\python.exe -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo [!] Dependencies not installed!
    echo.
    echo Please run setup first:
    echo   Double-click setup-windows.bat
    echo.
    pause
    exit /b 1
)

REM Set environment variables
set FLASK_APP=run.py
set FLASK_CONFIG=windows
set FLASK_ENV=development

echo [*] Environment ready
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

REM Start the Flask development server using venv Python directly
venv\Scripts\python.exe run.py

REM If server stops, pause to show any error messages
echo.
echo Server stopped.
pause
