"""
SąskaitaPro - Lithuanian Small Business Invoicing Platform
Main Application Factory
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

from config import config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
migrate = Migrate()

login_manager.login_view = 'auth.login'
login_manager.login_message = 'Prašome prisijungti, kad galėtumėte pasiekti šį puslapį.'
login_manager.login_message_category = 'info'


def create_app(config_name=None):
    """Application factory"""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Ensure upload folder exists
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'])
    except OSError:
        pass

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.invoices import invoices_bp
    from app.routes.clients import clients_bp
    from app.routes.products import products_bp
    from app.routes.settings import settings_bp
    from app.routes.reports import reports_bp
    from app.routes.payments import payments_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(invoices_bp, url_prefix='/invoices')
    app.register_blueprint(clients_bp, url_prefix='/clients')
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(payments_bp, url_prefix='/payments')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Register error handlers
    register_error_handlers(app)

    # Register template context processors
    register_context_processors(app)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app


def register_error_handlers(app):
    """Register error handlers"""
    from flask import render_template

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403


def register_context_processors(app):
    """Register template context processors"""
    from datetime import datetime

    @app.context_processor
    def inject_globals():
        return {
            'current_year': datetime.now().year,
            'company_name': app.config['COMPANY_NAME'],
            'company_tagline': app.config['COMPANY_TAGLINE'],
            'vat_rates': app.config['VAT_RATES'],
            'subscription_plans': app.config['SUBSCRIPTION_PLANS']
        }

    @app.template_filter('currency')
    def currency_filter(value):
        """Format value as EUR currency"""
        if value is None:
            return '€0.00'
        return f'€{value:,.2f}'

    @app.template_filter('date_lt')
    def date_lt_filter(value):
        """Format date in Lithuanian format"""
        if value is None:
            return ''
        return value.strftime('%Y-%m-%d')
