"""
Client Management Routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app import db
from app.models import Client, ActivityLog
from app.forms import ClientForm

clients_bp = Blueprint('clients', __name__)


@clients_bp.route('/')
@login_required
def index():
    """List all clients"""
    company = current_user.company
    if not company:
        flash('Prašome pirmiausia užpildyti įmonės informaciją.', 'warning')
        return redirect(url_for('settings.company'))

    # Search and filter
    search = request.args.get('search', '')
    show_inactive = request.args.get('show_inactive', '0') == '1'

    query = company.clients

    if search:
        query = query.filter(
            Client.name.ilike(f'%{search}%') |
            Client.company_code.ilike(f'%{search}%') |
            Client.email.ilike(f'%{search}%')
        )

    if not show_inactive:
        query = query.filter_by(is_active=True)

    # Pagination
    page = request.args.get('page', 1, type=int)
    clients = query.order_by(Client.name).paginate(
        page=page, per_page=20, error_out=False
    )

    return render_template(
        'clients/index.html',
        clients=clients,
        search=search,
        show_inactive=show_inactive
    )


@clients_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new client"""
    company = current_user.company
    if not company:
        flash('Prašome pirmiausia užpildyti įmonės informaciją.', 'warning')
        return redirect(url_for('settings.company'))

    # Check client limit
    plan = current_user.plan_config
    client_limit = plan.get('clients_limit', 10)
    current_count = company.clients.filter_by(is_active=True).count()

    if client_limit != -1 and current_count >= client_limit:
        flash('Pasiektas klientų limitas. Atnaujinkite planą.', 'warning')
        return redirect(url_for('payments.upgrade'))

    form = ClientForm()

    if form.validate_on_submit():
        client = Client(
            company_id=company.id,
            name=form.name.data,
            legal_name=form.legal_name.data,
            client_type=form.client_type.data,
            company_code=form.company_code.data,
            vat_code=form.vat_code.data,
            contact_person=form.contact_person.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            city=form.city.data,
            postal_code=form.postal_code.data,
            country=form.country.data,
            notes=form.notes.data
        )

        db.session.add(client)
        db.session.commit()

        ActivityLog.log(
            user_id=current_user.id,
            action='created',
            entity_type='client',
            entity_id=client.id,
            ip_address=request.remote_addr
        )

        flash(f'Klientas "{client.name}" sukurtas.', 'success')
        return redirect(url_for('clients.view', client_id=client.id))

    return render_template('clients/create.html', form=form)


@clients_bp.route('/<int:client_id>')
@login_required
def view(client_id):
    """View client details"""
    client = Client.query.get_or_404(client_id)

    if client.company_id != current_user.company.id:
        flash('Neturite prieigos prie šio kliento.', 'error')
        return redirect(url_for('clients.index'))

    # Get recent invoices for this client
    recent_invoices = client.invoices.order_by(
        db.desc('created_at')
    ).limit(10).all()

    return render_template(
        'clients/view.html',
        client=client,
        recent_invoices=recent_invoices
    )


@clients_bp.route('/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(client_id):
    """Edit client"""
    client = Client.query.get_or_404(client_id)

    if client.company_id != current_user.company.id:
        flash('Neturite prieigos prie šio kliento.', 'error')
        return redirect(url_for('clients.index'))

    form = ClientForm(obj=client)

    if form.validate_on_submit():
        form.populate_obj(client)
        db.session.commit()

        ActivityLog.log(
            user_id=current_user.id,
            action='updated',
            entity_type='client',
            entity_id=client.id,
            ip_address=request.remote_addr
        )

        flash('Kliento informacija atnaujinta.', 'success')
        return redirect(url_for('clients.view', client_id=client_id))

    return render_template('clients/edit.html', form=form, client=client)


@clients_bp.route('/<int:client_id>/delete', methods=['POST'])
@login_required
def delete(client_id):
    """Deactivate client (soft delete)"""
    client = Client.query.get_or_404(client_id)

    if client.company_id != current_user.company.id:
        flash('Neturite prieigos prie šio kliento.', 'error')
        return redirect(url_for('clients.index'))

    # Check if client has invoices
    if client.invoices.count() > 0:
        # Soft delete - just deactivate
        client.is_active = False
        flash('Klientas deaktyvuotas (turi sąskaitų istorijoje).', 'info')
    else:
        # Hard delete
        db.session.delete(client)
        flash('Klientas pašalintas.', 'success')

    db.session.commit()

    ActivityLog.log(
        user_id=current_user.id,
        action='deleted',
        entity_type='client',
        entity_id=client_id,
        ip_address=request.remote_addr
    )

    return redirect(url_for('clients.index'))


@clients_bp.route('/search')
@login_required
def search():
    """Search clients (AJAX)"""
    q = request.args.get('q', '')
    company = current_user.company

    clients = company.clients.filter(
        Client.is_active == True,
        Client.name.ilike(f'%{q}%')
    ).limit(10).all()

    return jsonify([{
        'id': c.id,
        'name': c.name,
        'company_code': c.company_code,
        'vat_code': c.vat_code,
        'email': c.email
    } for c in clients])
