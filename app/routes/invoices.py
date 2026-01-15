"""
Invoice Routes
Create, view, edit, send, and manage invoices
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from datetime import date, timedelta
import io

from app import db
from app.models import Invoice, InvoiceItem, Client, Product, ActivityLog
from app.forms import InvoiceForm, InvoiceItemForm
from app.services.pdf_generator import generate_invoice_pdf
from app.services.email_service import send_invoice_email

invoices_bp = Blueprint('invoices', __name__)


@invoices_bp.route('/')
@login_required
def index():
    """List all invoices"""
    company = current_user.company
    if not company:
        flash('Prašome pirmiausia užpildyti įmonės informaciją.', 'warning')
        return redirect(url_for('settings.company'))

    # Filters
    status = request.args.get('status', 'all')
    client_id = request.args.get('client_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    query = company.invoices

    if status != 'all':
        query = query.filter_by(status=status)
    if client_id:
        query = query.filter_by(client_id=client_id)
    if date_from:
        query = query.filter(Invoice.invoice_date >= date_from)
    if date_to:
        query = query.filter(Invoice.invoice_date <= date_to)

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    invoices = query.order_by(Invoice.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Get clients for filter dropdown
    clients = company.clients.filter_by(is_active=True).order_by(Client.name).all()

    return render_template(
        'invoices/index.html',
        invoices=invoices,
        clients=clients,
        current_status=status,
        current_client_id=client_id
    )


@invoices_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new invoice"""
    company = current_user.company
    if not company:
        flash('Prašome pirmiausia užpildyti įmonės informaciją.', 'warning')
        return redirect(url_for('settings.company'))

    # Check invoice limit
    if not current_user.can_create_invoice:
        flash('Pasiektas sąskaitų limitas šiam mėnesiui. Atnaujinkite planą.', 'warning')
        return redirect(url_for('payments.upgrade'))

    form = InvoiceForm()

    # Populate client choices
    clients = company.clients.filter_by(is_active=True).order_by(Client.name).all()
    form.client_id.choices = [(0, '-- Pasirinkite klientą --')] + [
        (c.id, c.name) for c in clients
    ]

    if form.validate_on_submit():
        # Generate invoice number
        invoice_number = company.get_next_invoice_number()

        # Calculate due date
        due_date = form.invoice_date.data + timedelta(days=company.payment_terms)

        invoice = Invoice(
            user_id=current_user.id,
            company_id=company.id,
            client_id=form.client_id.data,
            invoice_number=invoice_number,
            invoice_date=form.invoice_date.data,
            due_date=due_date,
            notes=form.notes.data,
            status='draft'
        )
        invoice.generate_payment_reference()

        db.session.add(invoice)
        db.session.commit()

        ActivityLog.log(
            user_id=current_user.id,
            action='created',
            entity_type='invoice',
            entity_id=invoice.id,
            ip_address=request.remote_addr
        )

        flash('Sąskaita sukurta. Pridėkite eilutes.', 'success')
        return redirect(url_for('invoices.edit', invoice_id=invoice.id))

    # Set default date
    form.invoice_date.data = date.today()

    return render_template(
        'invoices/create.html',
        form=form,
        clients=clients
    )


@invoices_bp.route('/<int:invoice_id>')
@login_required
def view(invoice_id):
    """View invoice details"""
    invoice = Invoice.query.get_or_404(invoice_id)

    # Security check
    if invoice.company_id != current_user.company.id:
        flash('Neturite prieigos prie šios sąskaitos.', 'error')
        return redirect(url_for('invoices.index'))

    return render_template('invoices/view.html', invoice=invoice)


@invoices_bp.route('/<int:invoice_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(invoice_id):
    """Edit invoice"""
    invoice = Invoice.query.get_or_404(invoice_id)
    company = current_user.company

    # Security check
    if invoice.company_id != company.id:
        flash('Neturite prieigos prie šios sąskaitos.', 'error')
        return redirect(url_for('invoices.index'))

    # Can only edit draft invoices
    if invoice.status != 'draft':
        flash('Galima redaguoti tik juodraščio būsenos sąskaitas.', 'warning')
        return redirect(url_for('invoices.view', invoice_id=invoice_id))

    form = InvoiceForm(obj=invoice)
    clients = company.clients.filter_by(is_active=True).order_by(Client.name).all()
    form.client_id.choices = [(c.id, c.name) for c in clients]

    products = company.products.filter_by(is_active=True).order_by(Product.name).all()

    if form.validate_on_submit():
        invoice.client_id = form.client_id.data
        invoice.invoice_date = form.invoice_date.data
        invoice.due_date = form.invoice_date.data + timedelta(days=company.payment_terms)
        invoice.notes = form.notes.data
        db.session.commit()

        flash('Sąskaita atnaujinta.', 'success')
        return redirect(url_for('invoices.edit', invoice_id=invoice_id))

    return render_template(
        'invoices/edit.html',
        invoice=invoice,
        form=form,
        products=products
    )


@invoices_bp.route('/<int:invoice_id>/items', methods=['POST'])
@login_required
def add_item(invoice_id):
    """Add item to invoice (AJAX)"""
    invoice = Invoice.query.get_or_404(invoice_id)

    if invoice.company_id != current_user.company.id:
        return jsonify({'error': 'Unauthorized'}), 403

    if invoice.status != 'draft':
        return jsonify({'error': 'Cannot modify sent invoice'}), 400

    data = request.get_json()

    item = InvoiceItem(
        invoice_id=invoice.id,
        product_id=data.get('product_id'),
        description=data['description'],
        quantity=data['quantity'],
        unit=data.get('unit', 'vnt.'),
        unit_price=data['unit_price'],
        vat_rate=data.get('vat_rate', 21),
        position=len(invoice.items)
    )
    item.calculate()

    db.session.add(item)
    invoice.calculate_totals()
    db.session.commit()

    return jsonify({
        'id': item.id,
        'description': item.description,
        'quantity': float(item.quantity),
        'unit': item.unit,
        'unit_price': float(item.unit_price),
        'vat_rate': item.vat_rate,
        'line_total': float(item.line_total),
        'vat_amount': float(item.vat_amount),
        'invoice_subtotal': float(invoice.subtotal),
        'invoice_vat': float(invoice.vat_amount),
        'invoice_total': float(invoice.total)
    })


@invoices_bp.route('/<int:invoice_id>/items/<int:item_id>', methods=['DELETE'])
@login_required
def delete_item(invoice_id, item_id):
    """Delete item from invoice (AJAX)"""
    invoice = Invoice.query.get_or_404(invoice_id)

    if invoice.company_id != current_user.company.id:
        return jsonify({'error': 'Unauthorized'}), 403

    if invoice.status != 'draft':
        return jsonify({'error': 'Cannot modify sent invoice'}), 400

    item = InvoiceItem.query.get_or_404(item_id)
    if item.invoice_id != invoice.id:
        return jsonify({'error': 'Item not found'}), 404

    db.session.delete(item)
    invoice.calculate_totals()
    db.session.commit()

    return jsonify({
        'success': True,
        'invoice_subtotal': float(invoice.subtotal),
        'invoice_vat': float(invoice.vat_amount),
        'invoice_total': float(invoice.total)
    })


@invoices_bp.route('/<int:invoice_id>/send', methods=['POST'])
@login_required
def send(invoice_id):
    """Send invoice to client via email"""
    invoice = Invoice.query.get_or_404(invoice_id)

    if invoice.company_id != current_user.company.id:
        flash('Neturite prieigos prie šios sąskaitos.', 'error')
        return redirect(url_for('invoices.index'))

    if not invoice.items:
        flash('Sąskaita neturi eilučių.', 'error')
        return redirect(url_for('invoices.edit', invoice_id=invoice_id))

    # Generate PDF
    pdf_buffer = generate_invoice_pdf(invoice)

    # Send email
    try:
        send_invoice_email(invoice, pdf_buffer)
        invoice.mark_as_sent()
        db.session.commit()

        ActivityLog.log(
            user_id=current_user.id,
            action='sent',
            entity_type='invoice',
            entity_id=invoice.id,
            ip_address=request.remote_addr
        )

        flash(f'Sąskaita {invoice.invoice_number} išsiųsta klientui.', 'success')
    except Exception as e:
        flash(f'Klaida siunčiant sąskaitą: {str(e)}', 'error')

    return redirect(url_for('invoices.view', invoice_id=invoice_id))


@invoices_bp.route('/<int:invoice_id>/pdf')
@login_required
def download_pdf(invoice_id):
    """Download invoice as PDF"""
    invoice = Invoice.query.get_or_404(invoice_id)

    if invoice.company_id != current_user.company.id:
        flash('Neturite prieigos prie šios sąskaitos.', 'error')
        return redirect(url_for('invoices.index'))

    pdf_buffer = generate_invoice_pdf(invoice)

    return send_file(
        io.BytesIO(pdf_buffer),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'{invoice.invoice_number}.pdf'
    )


@invoices_bp.route('/<int:invoice_id>/mark-paid', methods=['POST'])
@login_required
def mark_paid(invoice_id):
    """Mark invoice as paid"""
    invoice = Invoice.query.get_or_404(invoice_id)

    if invoice.company_id != current_user.company.id:
        flash('Neturite prieigos prie šios sąskaitos.', 'error')
        return redirect(url_for('invoices.index'))

    invoice.mark_as_paid()
    db.session.commit()

    ActivityLog.log(
        user_id=current_user.id,
        action='marked_paid',
        entity_type='invoice',
        entity_id=invoice.id,
        ip_address=request.remote_addr
    )

    flash(f'Sąskaita {invoice.invoice_number} pažymėta kaip apmokėta.', 'success')
    return redirect(url_for('invoices.view', invoice_id=invoice_id))


@invoices_bp.route('/<int:invoice_id>/cancel', methods=['POST'])
@login_required
def cancel(invoice_id):
    """Cancel invoice"""
    invoice = Invoice.query.get_or_404(invoice_id)

    if invoice.company_id != current_user.company.id:
        flash('Neturite prieigos prie šios sąskaitos.', 'error')
        return redirect(url_for('invoices.index'))

    if invoice.status == 'paid':
        flash('Negalima atšaukti apmokėtos sąskaitos.', 'error')
        return redirect(url_for('invoices.view', invoice_id=invoice_id))

    invoice.status = 'cancelled'
    db.session.commit()

    ActivityLog.log(
        user_id=current_user.id,
        action='cancelled',
        entity_type='invoice',
        entity_id=invoice.id,
        ip_address=request.remote_addr
    )

    flash(f'Sąskaita {invoice.invoice_number} atšaukta.', 'success')
    return redirect(url_for('invoices.view', invoice_id=invoice_id))


@invoices_bp.route('/<int:invoice_id>/duplicate', methods=['POST'])
@login_required
def duplicate(invoice_id):
    """Create a copy of an invoice"""
    original = Invoice.query.get_or_404(invoice_id)
    company = current_user.company

    if original.company_id != company.id:
        flash('Neturite prieigos prie šios sąskaitos.', 'error')
        return redirect(url_for('invoices.index'))

    # Check invoice limit
    if not current_user.can_create_invoice:
        flash('Pasiektas sąskaitų limitas. Atnaujinkite planą.', 'warning')
        return redirect(url_for('payments.upgrade'))

    # Create new invoice
    new_invoice = Invoice(
        user_id=current_user.id,
        company_id=company.id,
        client_id=original.client_id,
        invoice_number=company.get_next_invoice_number(),
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=company.payment_terms),
        notes=original.notes,
        status='draft'
    )
    new_invoice.generate_payment_reference()

    db.session.add(new_invoice)
    db.session.flush()  # Get the new ID

    # Copy items
    for item in original.items:
        new_item = InvoiceItem(
            invoice_id=new_invoice.id,
            product_id=item.product_id,
            description=item.description,
            quantity=item.quantity,
            unit=item.unit,
            unit_price=item.unit_price,
            vat_rate=item.vat_rate,
            position=item.position
        )
        new_item.calculate()
        db.session.add(new_item)

    new_invoice.calculate_totals()
    db.session.commit()

    flash(f'Sąskaitos kopija sukurta: {new_invoice.invoice_number}', 'success')
    return redirect(url_for('invoices.edit', invoice_id=new_invoice.id))
