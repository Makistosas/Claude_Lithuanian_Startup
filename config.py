"""
SąskaitaPro Configuration
Lithuanian Small Business Invoicing Platform
"""
import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration"""
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'saskaita.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Mail (for password reset, notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', '1', 'yes']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@saskaitapro.lt')

    # Stripe Payment Processing
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', '')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

    # Subscription Plans (prices in EUR cents)
    SUBSCRIPTION_PLANS = {
        'free': {
            'name': 'Nemokamas',
            'name_en': 'Free',
            'price': 0,
            'invoices_per_month': 5,
            'clients_limit': 10,
            'products_limit': 20,
            'features': ['Pagrindinės sąskaitos', 'PDF eksportas', 'El. pašto siuntimas']
        },
        'basic': {
            'name': 'Bazinis',
            'name_en': 'Basic',
            'price': 1900,  # €19
            'stripe_price_id': os.environ.get('STRIPE_BASIC_PRICE_ID', ''),
            'invoices_per_month': 50,
            'clients_limit': 100,
            'products_limit': 200,
            'features': ['Visos nemokamo funkcijos', '50 sąskaitų/mėn', 'Klientų valdymas', 'Produktų katalogas']
        },
        'pro': {
            'name': 'Profesionalus',
            'name_en': 'Professional',
            'price': 3900,  # €39
            'stripe_price_id': os.environ.get('STRIPE_PRO_PRICE_ID', ''),
            'invoices_per_month': -1,  # Unlimited
            'clients_limit': -1,
            'products_limit': -1,
            'features': ['Neribota sąskaitų', 'VMI ataskaitos', 'Išlaidų sekimas', 'Pirmenybinis palaikymas']
        },
        'enterprise': {
            'name': 'Įmonėms',
            'name_en': 'Enterprise',
            'price': 9900,  # €99
            'stripe_price_id': os.environ.get('STRIPE_ENTERPRISE_PRICE_ID', ''),
            'invoices_per_month': -1,
            'clients_limit': -1,
            'products_limit': -1,
            'features': ['Visos Pro funkcijos', 'Keli vartotojai', 'API prieiga', 'Dedikuotas palaikymas']
        }
    }

    # Lithuanian VAT rates
    VAT_RATES = {
        'standard': 21,      # Standard rate
        'reduced': 9,        # Reduced rate (books, periodicals)
        'super_reduced': 5,  # Super reduced (pharmaceuticals)
        'zero': 0            # Zero rate (exports, etc.)
    }

    # Company settings
    COMPANY_NAME = 'SąskaitaPro'
    COMPANY_TAGLINE = 'Profesionalios sąskaitos Lietuvos verslui'
    COMPANY_EMAIL = 'info@saskaitapro.lt'
    COMPANY_WEBSITE = 'https://saskaitapro.lt'

    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

    # Override with stronger security in production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class WindowsLocalConfig(Config):
    """Windows 11 Local Installation configuration"""
    DEBUG = True

    # Use SQLite for easy local setup (no PostgreSQL needed)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'saskaita_local.db')

    # Disable SQL echo for cleaner console output
    SQLALCHEMY_ECHO = False

    # Local development server settings
    SERVER_NAME = None  # Allow all hostnames

    # Relaxed session settings for local use
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Local upload folder (Windows-compatible paths handled by os.path)
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')

    # Disable mail by default for local use (can be enabled via env vars)
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', 'true').lower() in ['true', '1', 'yes']


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'windows': WindowsLocalConfig,
    'local': WindowsLocalConfig,
    'default': DevelopmentConfig
}
