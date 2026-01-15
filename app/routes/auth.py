"""
Authentication Routes
Login, register, password reset, etc.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

from app import db
from app.models import User, Company, ActivityLog
from app.forms import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()

        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Jūsų paskyra yra deaktyvuota. Susisiekite su palaikymu.', 'error')
                return render_template('auth/login.html', form=form)

            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()

            ActivityLog.log(
                user_id=user.id,
                action='login',
                ip_address=request.remote_addr
            )

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))

        flash('Neteisingas el. paštas arba slaptažodis.', 'error')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if email already exists
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash('Šis el. pašto adresas jau užregistruotas.', 'error')
            return render_template('auth/register.html', form=form)

        # Create new user
        user = User(
            email=form.email.data.lower(),
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data
        )
        user.set_password(form.password.data)
        user.generate_verification_token()

        db.session.add(user)
        db.session.commit()

        # Create default company profile
        company = Company(
            user_id=user.id,
            name=f"{user.first_name} {user.last_name}",
            email=user.email
        )
        db.session.add(company)
        db.session.commit()

        ActivityLog.log(
            user_id=user.id,
            action='register',
            ip_address=request.remote_addr
        )

        # Auto login after registration
        login_user(user)

        flash('Sveiki prisijungę! Prašome užpildyti įmonės informaciją.', 'success')
        return redirect(url_for('settings.company'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    ActivityLog.log(
        user_id=current_user.id,
        action='logout',
        ip_address=request.remote_addr
    )
    logout_user()
    flash('Jūs sėkmingai atsijungėte.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password - request reset link"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            user.generate_reset_token()
            db.session.commit()
            # In production, send email with reset link
            # send_password_reset_email(user)
            flash('Slaptažodžio atkūrimo nuoroda išsiųsta į jūsų el. paštą.', 'info')
        else:
            # Don't reveal if email exists
            flash('Jei šis el. paštas egzistuoja, gausite atkūrimo nuorodą.', 'info')

        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    user = User.query.filter_by(reset_token=token).first()
    if not user:
        flash('Netinkama arba pasibaigusi atkūrimo nuoroda.', 'error')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()

        flash('Jūsų slaptažodis sėkmingai pakeistas.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form)


@auth_bp.route('/verify/<token>')
def verify_email(token):
    """Verify email address"""
    user = User.query.filter_by(verification_token=token).first()
    if user:
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        flash('Jūsų el. paštas sėkmingai patvirtintas.', 'success')
    else:
        flash('Netinkama patvirtinimo nuoroda.', 'error')

    return redirect(url_for('auth.login'))
