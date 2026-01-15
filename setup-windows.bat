@echo off
REM SaskaitaPro - Windows Setup Launcher
REM Double-click this file to install dependencies

title SaskaitaPro - Setup

echo.
echo =============================================
echo   SaskaitaPro - Windows 11 Setup
echo   Lithuanian Small Business Invoicing
echo =============================================
echo.

REM Get script directory
cd /d "%~dp0"

REM Check if Python is available
echo [*] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.8+ from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

echo [+] Python found
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv\Scripts\python.exe" (
    echo [*] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [!] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [+] Virtual environment created
) else (
    echo [*] Virtual environment already exists
)

REM Install dependencies
echo [*] Installing dependencies (this may take a few minutes)...
venv\Scripts\python.exe -m pip install --upgrade pip --quiet
venv\Scripts\python.exe -m pip install -r requirements-windows.txt --quiet
if %errorlevel% neq 0 (
    echo [!] Failed to install dependencies
    echo Trying verbose install...
    venv\Scripts\python.exe -m pip install -r requirements-windows.txt
    pause
    exit /b 1
)
echo [+] Dependencies installed

REM Create necessary directories
echo [*] Creating directories...
if not exist "instance" mkdir instance
if not exist "uploads" mkdir uploads
if not exist "uploads\logos" mkdir uploads\logos
if not exist "uploads\receipts" mkdir uploads\receipts
echo [+] Directories created

REM Initialize database
echo [*] Initializing database...
set FLASK_APP=run.py
set FLASK_CONFIG=windows
venv\Scripts\python.exe -c "from run import app; from app import db; app.app_context().push(); db.create_all(); print('[+] Database initialized')"

REM Create demo user
echo [*] Creating demo user...
venv\Scripts\python.exe -c "from run import app; from app import db; from app.models import User, Company; app.app_context().push(); u=User.query.filter_by(email='demo@saskaitapro.lt').first(); print('[*] Demo user already exists' if u else ''); exit(0 if u else 1)" 2>nul
if %errorlevel% neq 0 (
    venv\Scripts\python.exe -c "from run import app; from app import db; from app.models import User, Company; import bcrypt; app.app_context().push(); u=User(email='demo@saskaitapro.lt', password_hash=bcrypt.hashpw(b'demo123456', bcrypt.gensalt()).decode('utf-8'), first_name='Demo', last_name='User', is_verified=True); db.session.add(u); db.session.commit(); c=Company(user_id=u.id, name='Demo Company', company_code='123456789', vat_code='LT123456789'); db.session.add(c); db.session.commit(); print('[+] Demo user created')"
)

echo.
echo =============================================
echo   Setup Complete!
echo =============================================
echo.
echo To start the application:
echo   Double-click start-windows.bat
echo.
echo Then open: http://localhost:5000
echo.
echo Demo Login:
echo   Email:    demo@saskaitapro.lt
echo   Password: demo123456
echo.
pause
