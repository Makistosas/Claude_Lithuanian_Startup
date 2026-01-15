@echo off
REM SaskaitaPro - Windows Setup Launcher
REM Double-click this file to run the PowerShell setup script

title SaskaitaPro - Setup

echo.
echo =============================================
echo   SaskaitaPro - Windows 11 Setup
echo   Lithuanian Small Business Invoicing
echo =============================================
echo.
echo Starting PowerShell setup script...
echo.

REM Get script directory and run PowerShell setup
cd /d "%~dp0"

REM Check if PowerShell is available
where powershell >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] PowerShell is not available on this system.
    echo Please run setup-windows.ps1 manually.
    pause
    exit /b 1
)

REM Run the PowerShell setup script with execution policy bypass for this script
powershell -ExecutionPolicy Bypass -File "%~dp0setup-windows.ps1"

echo.
echo Setup complete! You can now run start-windows.bat to start the application.
echo.
pause
