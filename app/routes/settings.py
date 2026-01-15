"""
Settings Routes
Company settings, user profile, preferences
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os

from app import db
from app.models import Company, ActivityLog
from app.forms import CompanyForm, UserProfileForm, ChangePasswordForm

settings_bp = Blueprint('settings', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@settings_bp.route('/')
@login_required
def index():
    """Settings overview"""
    return render_template('settings/index.html')


@settings_bp.route('/company', methods=['GET', 'POST'])
@login_required
def company():
    """Company settings"""
    company = current_user.company

    if not company:
        company = Company(
            user_id=current_user.id,
            name=current_user.full_name,
            email=current_user.email
        )
        db.session.add(company)
        db.session.commit()

    form = CompanyForm(obj=company)

    if form.validate_on_submit():
        form.populate_obj(company)

        # Handle logo upload
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"logo_{company.id}_{file.filename}")
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                company.logo = filename

        db.session.commit()

        ActivityLog.log(
            user_id=current_user.id,
            action='updated',
            entity_type='company',
            entity_id=company.id,
            ip_address=request.remote_addr
        )

        flash('Įmonės informacija atnaujinta.', 'success')
        return redirect(url_for('settings.company'))

    return render_template('settings/company.html', form=form, company=company)


@settings_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile settings"""
    form = UserProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data

        # Check if email changed
        if form.email.data.lower() != current_user.email:
            # Verify email doesn't exist
            from app.models import User
            if User.query.filter_by(email=form.email.data.lower()).first():
                flash('Šis el. pašto adresas jau naudojamas.', 'error')
                return render_template('settings/profile.html', form=form)
            current_user.email = form.email.data.lower()
            current_user.is_verified = False
            current_user.generate_verification_token()
            flash('El. paštas pakeistas. Prašome patvirtinti naują adresą.', 'info')

        db.session.commit()
        flash('Profilis atnaujintas.', 'success')
        return redirect(url_for('settings.profile'))

    return render_template('settings/profile.html', form=form)


@settings_bp.route('/password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password"""
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Neteisingas dabartinis slaptažodis.', 'error')
            return render_template('settings/password.html', form=form)

        current_user.set_password(form.new_password.data)
        db.session.commit()

        ActivityLog.log(
            user_id=current_user.id,
            action='password_changed',
            ip_address=request.remote_addr
        )

        flash('Slaptažodis pakeistas.', 'success')
        return redirect(url_for('settings.index'))

    return render_template('settings/password.html', form=form)


@settings_bp.route('/invoice', methods=['GET', 'POST'])
@login_required
def invoice_settings():
    """Invoice-specific settings"""
    company = current_user.company

    if request.method == 'POST':
        company.invoice_prefix = request.form.get('invoice_prefix', 'SF')[:10]
        company.payment_terms = int(request.form.get('payment_terms', 14))
        company.invoice_notes = request.form.get('invoice_notes', '')
        company.primary_color = request.form.get('primary_color', '#2563eb')

        db.session.commit()
        flash('Sąskaitų nustatymai išsaugoti.', 'success')
        return redirect(url_for('settings.invoice_settings'))

    return render_template('settings/invoice.html', company=company)


@settings_bp.route('/billing')
@login_required
def billing():
    """Subscription and billing info"""
    return render_template(
        'settings/billing.html',
        plan=current_user.plan_config,
        plan_name=current_user.subscription_plan
    )


@settings_bp.route('/export')
@login_required
def export_data():
    """Export user data (GDPR compliance)"""
    return render_template('settings/export.html')


@settings_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account"""
    # This would require additional confirmation in production
    flash('Paskyros ištrynimas nėra įjungtas šiuo metu.', 'warning')
    return redirect(url_for('settings.index'))
