"""
Payment Routes
Stripe subscription management
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
import stripe

from app import db
from app.models import ActivityLog

payments_bp = Blueprint('payments', __name__)


@payments_bp.route('/upgrade')
@login_required
def upgrade():
    """Upgrade subscription page"""
    plans = current_app.config['SUBSCRIPTION_PLANS']
    current_plan = current_user.subscription_plan

    return render_template(
        'payments/upgrade.html',
        plans=plans,
        current_plan=current_plan
    )


@payments_bp.route('/checkout/<plan>')
@login_required
def checkout(plan):
    """Create Stripe checkout session"""
    plans = current_app.config['SUBSCRIPTION_PLANS']

    if plan not in plans or plan == 'free':
        flash('Netinkamas planas.', 'error')
        return redirect(url_for('payments.upgrade'))

    plan_config = plans[plan]
    stripe_price_id = plan_config.get('stripe_price_id')

    if not stripe_price_id:
        flash('Mokėjimų sistema dar nekonfigūruota.', 'warning')
        return redirect(url_for('payments.upgrade'))

    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

    try:
        # Create or get Stripe customer
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.full_name,
                metadata={'user_id': current_user.id}
            )
            current_user.stripe_customer_id = customer.id
            db.session.commit()

        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': stripe_price_id,
                'quantity': 1
            }],
            mode='subscription',
            success_url=url_for('payments.success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('payments.upgrade', _external=True),
            metadata={
                'user_id': current_user.id,
                'plan': plan
            }
        )

        return redirect(checkout_session.url)

    except stripe.error.StripeError as e:
        flash(f'Klaida: {str(e)}', 'error')
        return redirect(url_for('payments.upgrade'))


@payments_bp.route('/success')
@login_required
def success():
    """Payment success page"""
    session_id = request.args.get('session_id')

    if session_id:
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

        try:
            session = stripe.checkout.Session.retrieve(session_id)

            if session.payment_status == 'paid':
                # Update user subscription
                plan = session.metadata.get('plan', 'basic')
                current_user.subscription_plan = plan
                current_user.stripe_subscription_id = session.subscription
                db.session.commit()

                ActivityLog.log(
                    user_id=current_user.id,
                    action='subscription_upgraded',
                    details=f'Plan: {plan}',
                    ip_address=request.remote_addr
                )

                flash(f'Sveikiname! Jūsų planas atnaujintas.', 'success')

        except stripe.error.StripeError as e:
            flash(f'Klaida tikrinant mokėjimą: {str(e)}', 'error')

    return render_template('payments/success.html')


@payments_bp.route('/cancel-subscription', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel subscription"""
    if not current_user.stripe_subscription_id:
        flash('Neturite aktyvios prenumeratos.', 'info')
        return redirect(url_for('settings.billing'))

    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

    try:
        # Cancel at period end (not immediately)
        stripe.Subscription.modify(
            current_user.stripe_subscription_id,
            cancel_at_period_end=True
        )

        flash('Prenumerata bus atšaukta periodo pabaigoje.', 'info')

        ActivityLog.log(
            user_id=current_user.id,
            action='subscription_cancelled',
            ip_address=request.remote_addr
        )

    except stripe.error.StripeError as e:
        flash(f'Klaida: {str(e)}', 'error')

    return redirect(url_for('settings.billing'))


@payments_bp.route('/webhook', methods=['POST'])
def webhook():
    """Stripe webhook handler"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = current_app.config['STRIPE_WEBHOOK_SECRET']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_completed(session)

    elif event['type'] == 'invoice.paid':
        invoice = event['data']['object']
        handle_invoice_paid(invoice)

    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        handle_payment_failed(invoice)

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_deleted(subscription)

    return jsonify({'status': 'success'})


def handle_checkout_completed(session):
    """Handle successful checkout"""
    from app.models import User

    user_id = session['metadata'].get('user_id')
    plan = session['metadata'].get('plan', 'basic')

    if user_id:
        user = User.query.get(int(user_id))
        if user:
            user.subscription_plan = plan
            user.stripe_subscription_id = session.get('subscription')
            db.session.commit()


def handle_invoice_paid(invoice):
    """Handle paid invoice (recurring payment)"""
    from app.models import User

    customer_id = invoice['customer']
    user = User.query.filter_by(stripe_customer_id=customer_id).first()

    if user:
        # Subscription renewed
        ActivityLog.log(
            user_id=user.id,
            action='subscription_renewed',
            details=f'Amount: {invoice["amount_paid"] / 100}'
        )


def handle_payment_failed(invoice):
    """Handle failed payment"""
    from app.models import User

    customer_id = invoice['customer']
    user = User.query.filter_by(stripe_customer_id=customer_id).first()

    if user:
        ActivityLog.log(
            user_id=user.id,
            action='payment_failed',
            details=f'Amount: {invoice["amount_due"] / 100}'
        )
        # Could send email notification here


def handle_subscription_deleted(subscription):
    """Handle cancelled subscription"""
    from app.models import User

    customer_id = subscription['customer']
    user = User.query.filter_by(stripe_customer_id=customer_id).first()

    if user:
        user.subscription_plan = 'free'
        user.stripe_subscription_id = None
        db.session.commit()

        ActivityLog.log(
            user_id=user.id,
            action='subscription_ended'
        )


@payments_bp.route('/portal')
@login_required
def customer_portal():
    """Redirect to Stripe customer portal"""
    if not current_user.stripe_customer_id:
        flash('Neturite mokėjimo istorijos.', 'info')
        return redirect(url_for('settings.billing'))

    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

    try:
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=url_for('settings.billing', _external=True)
        )
        return redirect(session.url)

    except stripe.error.StripeError as e:
        flash(f'Klaida: {str(e)}', 'error')
        return redirect(url_for('settings.billing'))
