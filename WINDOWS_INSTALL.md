# SąskaitaPro - Windows 11 Local Installation Guide

This guide explains how to install and run SąskaitaPro locally on your Windows 11 PC.

## Prerequisites

### 1. Python 3.8 or higher

Download Python from [python.org](https://www.python.org/downloads/windows/)

**Important during installation:**
- Check **"Add Python to PATH"** at the bottom of the first installer screen
- Click "Install Now" or customize as needed

To verify installation, open Command Prompt or PowerShell and run:
```
python --version
```

You should see something like `Python 3.11.x` or higher.

## Quick Installation

### Option 1: Double-Click Setup (Easiest)

1. Download or clone this repository
2. Double-click `setup-windows.bat`
3. Wait for the setup to complete
4. Double-click `start-windows.bat` to run the application
5. Open your browser to [http://localhost:5000](http://localhost:5000)

### Option 2: PowerShell Setup

1. Open PowerShell in the project folder
2. Run the setup script:
   ```powershell
   .\setup-windows.ps1
   ```
3. Start the application:
   ```powershell
   .\start-windows.bat
   ```

### Option 3: Manual Installation

1. Open Command Prompt or PowerShell in the project folder

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   ```
   # PowerShell:
   .\venv\Scripts\Activate.ps1

   # Command Prompt:
   venv\Scripts\activate.bat
   ```

4. Install dependencies:
   ```
   pip install -r requirements-windows.txt
   ```

5. Set environment variables:
   ```
   # PowerShell:
   $env:FLASK_APP = "run.py"
   $env:FLASK_CONFIG = "windows"

   # Command Prompt:
   set FLASK_APP=run.py
   set FLASK_CONFIG=windows
   ```

6. Initialize the database:
   ```
   flask init_db
   ```

7. Create demo user (optional but recommended):
   ```
   flask create_demo_user
   ```

8. Run the application:
   ```
   python run.py
   ```

9. Open your browser to [http://localhost:5000](http://localhost:5000)

## Demo Credentials

After setup, you can log in with the demo account:

- **Email:** demo@saskaitapro.lt
- **Password:** demo123456

## Project Structure

```
SaskaitaPro/
├── setup-windows.bat      # Double-click to run setup
├── setup-windows.ps1      # PowerShell setup script
├── start-windows.bat      # Double-click to start app
├── requirements-windows.txt # Windows-compatible dependencies
├── .env                   # Configuration (created by setup)
├── instance/              # Database files
│   └── saskaita_local.db  # SQLite database
├── uploads/               # Uploaded files (logos, receipts)
├── venv/                  # Python virtual environment
├── app/                   # Application code
├── config.py              # Configuration settings
└── run.py                 # Application entry point
```

## Configuration

After installation, you can edit the `.env` file to customize settings:

```env
# Basic configuration
FLASK_CONFIG=windows
SECRET_KEY=your-secret-key

# Email settings (optional)
MAIL_SUPPRESS_SEND=true    # Set to 'false' to enable email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Stripe payments (optional)
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
```

## Database

The Windows installation uses SQLite for simplicity. Your database is stored in:
```
instance/saskaita_local.db
```

### Reset Database

To reset the database and start fresh:

1. Stop the application (Ctrl+C in the terminal)
2. Delete `instance/saskaita_local.db`
3. Run:
   ```
   flask init_db
   flask create_demo_user
   ```

## Troubleshooting

### "Python is not recognized"

Python is not in your PATH. Either:
- Reinstall Python and check "Add Python to PATH"
- Or add Python manually to your system PATH

### PowerShell Script Execution Error

If you see "cannot be loaded because running scripts is disabled":

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try running the setup again.

### Port 5000 Already in Use

Another application is using port 5000. Either:
- Close the other application
- Or edit `run.py` to use a different port:
  ```python
  app.run(host='0.0.0.0', port=5001)
  ```

### Missing Dependencies Error

Try installing dependencies manually:
```
pip install -r requirements-windows.txt
```

If specific packages fail, install them individually:
```
pip install Flask Flask-SQLAlchemy reportlab
```

### WeasyPrint / GTK Errors

The Windows version uses ReportLab instead of WeasyPrint for PDF generation, which doesn't require GTK. If you see WeasyPrint errors, ensure you're using `requirements-windows.txt` instead of `requirements.txt`.

## Features in Local Mode

The local Windows version includes all core features:

- Create and manage invoices
- Client management
- Product catalog
- PDF invoice generation (via ReportLab)
- VMI-compliant invoice numbering
- VAT calculation (21%, 9%, 5%, 0%)
- Dashboard with statistics

**Note:** Email sending is disabled by default in local mode. Enable it by setting `MAIL_SUPPRESS_SEND=false` in `.env` and configuring your SMTP settings.

## Updating

To update to a new version:

1. Pull or download the latest code
2. Activate the virtual environment:
   ```
   .\venv\Scripts\Activate.ps1
   ```
3. Update dependencies:
   ```
   pip install -r requirements-windows.txt --upgrade
   ```
4. Run migrations if needed:
   ```
   flask db upgrade
   ```

## Support

For issues or questions:
- Check the project's GitHub Issues page
- Review the main README.md for additional documentation
