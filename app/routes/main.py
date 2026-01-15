"""
Main/Public Routes
Landing page, pricing, about, etc.
"""
from flask import Blueprint, render_template, current_app

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Landing page"""
    return render_template('main/index.html')


@main_bp.route('/pricing')
def pricing():
    """Pricing page"""
    plans = current_app.config['SUBSCRIPTION_PLANS']
    return render_template('main/pricing.html', plans=plans)


@main_bp.route('/features')
def features():
    """Features page"""
    return render_template('main/features.html')


@main_bp.route('/about')
def about():
    """About page"""
    return render_template('main/about.html')


@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('main/contact.html')


@main_bp.route('/terms')
def terms():
    """Terms of service"""
    return render_template('main/terms.html')


@main_bp.route('/privacy')
def privacy():
    """Privacy policy"""
    return render_template('main/privacy.html')
