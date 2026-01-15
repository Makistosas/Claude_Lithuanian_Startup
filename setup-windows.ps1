# SaskaitaPro - Windows 11 Local Installation Setup Script
# PowerShell Script for setting up the Lithuanian Invoicing Platform
#
# USAGE: Right-click and "Run with PowerShell" or run: .\setup-windows.ps1

param(
    [switch]$SkipVenv,
    [switch]$SkipDemo,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Header {
    Write-Host ""
    Write-Host "=============================================" -ForegroundColor Cyan
    Write-Host "  SaskaitaPro - Windows 11 Local Setup" -ForegroundColor Cyan
    Write-Host "  Lithuanian Small Business Invoicing" -ForegroundColor Cyan
    Write-Host "=============================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step($message) {
    Write-Host "[*] $message" -ForegroundColor Yellow
}

function Write-Success($message) {
    Write-Host "[+] $message" -ForegroundColor Green
}

function Write-Error($message) {
    Write-Host "[!] $message" -ForegroundColor Red
}

function Write-Info($message) {
    Write-Host "    $message" -ForegroundColor Gray
}

# Check if running as Administrator (not required, just informational)
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

Write-Header

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Step "Checking Python installation..."

# Check for Python
$pythonCmd = $null
$pythonPaths = @("python", "python3", "py")

foreach ($cmd in $pythonPaths) {
    try {
        $version = & $cmd --version 2>&1
        if ($version -match "Python 3\.([89]|1[0-9])") {
            $pythonCmd = $cmd
            Write-Success "Found $version"
            break
        }
    } catch {
        continue
    }
}

if (-not $pythonCmd) {
    Write-Error "Python 3.8+ is required but not found!"
    Write-Host ""
    Write-Host "Please install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation!" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# Check for pip
Write-Step "Checking pip installation..."
try {
    $pipVersion = & $pythonCmd -m pip --version 2>&1
    Write-Success "pip is available"
} catch {
    Write-Error "pip is not available. Please reinstall Python with pip enabled."
    exit 1
}

# Create virtual environment
$venvPath = Join-Path $scriptDir "venv"

if (-not $SkipVenv) {
    if (Test-Path $venvPath) {
        if ($Force) {
            Write-Step "Removing existing virtual environment..."
            Remove-Item -Recurse -Force $venvPath
        } else {
            Write-Info "Virtual environment already exists. Use -Force to recreate."
        }
    }

    if (-not (Test-Path $venvPath)) {
        Write-Step "Creating virtual environment..."
        & $pythonCmd -m venv $venvPath
        Write-Success "Virtual environment created"
    }
}

# Activate virtual environment
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Step "Activating virtual environment..."
    . $activateScript
    Write-Success "Virtual environment activated"
} else {
    Write-Error "Could not find virtual environment activation script"
    exit 1
}

# Upgrade pip
Write-Step "Upgrading pip..."
python -m pip install --upgrade pip --quiet
Write-Success "pip upgraded"

# Install dependencies
Write-Step "Installing dependencies (this may take a few minutes)..."
Write-Info "Installing core Flask dependencies..."

# Create a simplified requirements file for Windows (without WeasyPrint which needs GTK)
$windowsRequirements = @"
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.1
Flask-Mail==0.9.1
Flask-Migrate==4.0.5
Werkzeug==3.0.1
SQLAlchemy==2.0.23
reportlab==4.0.7
stripe==7.8.0
python-dotenv==1.0.0
email-validator==2.1.0
Pillow==10.1.0
babel==2.14.0
qrcode==7.4.2
bcrypt==4.1.2
PyJWT==2.8.0
"@

$windowsReqPath = Join-Path $scriptDir "requirements-windows.txt"
$windowsRequirements | Out-File -FilePath $windowsReqPath -Encoding UTF8

pip install -r $windowsReqPath --quiet
Write-Success "Dependencies installed"

# Create necessary directories
Write-Step "Creating application directories..."
$directories = @("instance", "uploads", "uploads\logos", "uploads\receipts")
foreach ($dir in $directories) {
    $dirPath = Join-Path $scriptDir $dir
    if (-not (Test-Path $dirPath)) {
        New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
    }
}
Write-Success "Directories created"

# Set environment variables for this session
Write-Step "Setting environment variables..."
$env:FLASK_APP = "run.py"
$env:FLASK_CONFIG = "windows"
$env:FLASK_ENV = "development"
Write-Success "Environment configured"

# Initialize database
Write-Step "Initializing database..."
python -c "from run import app, db; app.app_context().push(); db.create_all(); print('Database initialized')"
Write-Success "Database initialized (SQLite)"

# Create demo user
if (-not $SkipDemo) {
    Write-Step "Creating demo user..."
    flask create_demo_user 2>$null
    Write-Success "Demo user created"
}

# Create .env file for convenience
$envPath = Join-Path $scriptDir ".env"
if (-not (Test-Path $envPath)) {
    Write-Step "Creating .env configuration file..."
    $envContent = @"
# SaskaitaPro Local Configuration
# Edit these values as needed

FLASK_APP=run.py
FLASK_CONFIG=windows
FLASK_ENV=development
SECRET_KEY=local-dev-secret-key-$(Get-Random -Maximum 99999999)

# Email settings (optional - disabled by default for local use)
MAIL_SUPPRESS_SEND=true
# MAIL_SERVER=smtp.gmail.com
# MAIL_PORT=587
# MAIL_USERNAME=your-email@gmail.com
# MAIL_PASSWORD=your-app-password

# Stripe settings (optional - for payment testing)
# STRIPE_PUBLIC_KEY=pk_test_...
# STRIPE_SECRET_KEY=sk_test_...
"@
    $envContent | Out-File -FilePath $envPath -Encoding UTF8
    Write-Success ".env file created"
}

# Final output
Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start the application:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Option 1: Double-click 'start-windows.bat'" -ForegroundColor White
Write-Host ""
Write-Host "  Option 2: Run in PowerShell:" -ForegroundColor White
Write-Host "    .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host "    python run.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "Then open your browser to: http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Demo Login Credentials:" -ForegroundColor Cyan
Write-Host "  Email:    demo@saskaitapro.lt" -ForegroundColor White
Write-Host "  Password: demo123456" -ForegroundColor White
Write-Host ""
Write-Host "For help, see: WINDOWS_INSTALL.md" -ForegroundColor Gray
Write-Host ""
