"""
API Routes
RESTful API for enterprise customers
"""
from flask import Blueprint, jsonify, request, current_app
from functools import wraps
import jwt
from datetime import datetime, timedelta

from app import db
from app.models import User, Invoice, Client, Product, InvoiceItem

api_bp = Blueprint('api', __name__)


def token_required(f):
    """Decorator to require valid API token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            data = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            current_user = User.query.get(data['user_id'])

            if not current_user:
                return jsonify({'error': 'User not found'}), 401

            # Check if user has API access (enterprise plan)
            if current_user.subscription_plan != 'enterprise':
                return jsonify({'error': 'API access requires Enterprise plan'}), 403

        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


@api_bp.route('/token', methods=['POST'])
def get_token():
    """Get API token"""
    data = request.get_json()

    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email and password required'}), 400

    user = User.query.filter_by(email=data['email'].lower()).first()

    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    if user.subscription_plan != 'enterprise':
        return jsonify({'error': 'API access requires Enterprise plan'}), 403

    # Generate token
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, current_app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({
        'token': token,
        'expires_in': 86400  # 24 hours
    })


@api_bp.route('/invoices', methods=['GET'])
@token_required
def list_invoices(current_user):
    """List all invoices"""
    company = current_user.company

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    # Filters
    status = request.args.get('status')
    client_id = request.args.get('client_id', type=int)

    query = company.invoices

    if status:
        query = query.filter_by(status=status)
    if client_id:
        query = query.filter_by(client_id=client_id)

    pagination = query.order_by(Invoice.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'invoices': [invoice_to_dict(inv) for inv in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@api_bp.route('/invoices/<int:invoice_id>', methods=['GET'])
@token_required
def get_invoice(current_user, invoice_id):
    """Get single invoice"""
    invoice = Invoice.query.get_or_404(invoice_id)

    if invoice.company_id != current_user.company.id:
        return jsonify({'error': 'Not found'}), 404

    return jsonify(invoice_to_dict(invoice, include_items=True))


@api_bp.route('/invoices', methods=['POST'])
@token_required
def create_invoice(current_user):
    """Create new invoice"""
    data = request.get_json()
    company = current_user.company

    # Validate required fields
    if 'client_id' not in data:
        return jsonify({'error': 'client_id is required'}), 400

    # Verify client belongs to company
    client = Client.query.get(data['client_id'])
    if not client or client.company_id != company.id:
        return jsonify({'error': 'Client not found'}), 404

    # Create invoice
    invoice = Invoice(
        user_id=current_user.id,
        company_id=company.id,
        client_id=data['client_id'],
        invoice_number=company.get_next_invoice_number(),
        invoice_date=datetime.strptime(data.get('invoice_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date(),
        due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date() if 'due_date' in data else None,
        notes=data.get('notes', ''),
        status='draft'
    )

    if not invoice.due_date:
        invoice.due_date = invoice.invoice_date + timedelta(days=company.payment_terms)

    invoice.generate_payment_reference()

    db.session.add(invoice)
    db.session.flush()

    # Add items if provided
    if 'items' in data:
        for idx, item_data in enumerate(data['items']):
            item = InvoiceItem(
                invoice_id=invoice.id,
                product_id=item_data.get('product_id'),
                description=item_data['description'],
                quantity=item_data.get('quantity', 1),
                unit=item_data.get('unit', 'vnt.'),
                unit_price=item_data['unit_price'],
                vat_rate=item_data.get('vat_rate', 21),
                position=idx
            )
            item.calculate()
            db.session.add(item)

    invoice.calculate_totals()
    db.session.commit()

    return jsonify(invoice_to_dict(invoice, include_items=True)), 201


@api_bp.route('/clients', methods=['GET'])
@token_required
def list_clients(current_user):
    """List all clients"""
    company = current_user.company

    clients = company.clients.filter_by(is_active=True).order_by(Client.name).all()

    return jsonify({
        'clients': [client_to_dict(c) for c in clients]
    })


@api_bp.route('/clients', methods=['POST'])
@token_required
def create_client(current_user):
    """Create new client"""
    data = request.get_json()
    company = current_user.company

    if 'name' not in data:
        return jsonify({'error': 'name is required'}), 400

    client = Client(
        company_id=company.id,
        name=data['name'],
        legal_name=data.get('legal_name'),
        client_type=data.get('client_type', 'company'),
        company_code=data.get('company_code'),
        vat_code=data.get('vat_code'),
        contact_person=data.get('contact_person'),
        email=data.get('email'),
        phone=data.get('phone'),
        address=data.get('address'),
        city=data.get('city'),
        postal_code=data.get('postal_code'),
        country=data.get('country', 'Lietuva')
    )

    db.session.add(client)
    db.session.commit()

    return jsonify(client_to_dict(client)), 201


@api_bp.route('/products', methods=['GET'])
@token_required
def list_products(current_user):
    """List all products"""
    company = current_user.company

    products = company.products.filter_by(is_active=True).order_by(Product.name).all()

    return jsonify({
        'products': [product_to_dict(p) for p in products]
    })


# Helper functions
def invoice_to_dict(invoice, include_items=False):
    """Convert invoice to dictionary"""
    result = {
        'id': invoice.id,
        'invoice_number': invoice.invoice_number,
        'invoice_date': invoice.invoice_date.isoformat(),
        'due_date': invoice.due_date.isoformat(),
        'status': invoice.status,
        'client_id': invoice.client_id,
        'client_name': invoice.client.name,
        'subtotal': float(invoice.subtotal),
        'vat_amount': float(invoice.vat_amount),
        'total': float(invoice.total),
        'payment_reference': invoice.payment_reference,
        'created_at': invoice.created_at.isoformat(),
        'updated_at': invoice.updated_at.isoformat()
    }

    if include_items:
        result['items'] = [{
            'id': item.id,
            'description': item.description,
            'quantity': float(item.quantity),
            'unit': item.unit,
            'unit_price': float(item.unit_price),
            'vat_rate': item.vat_rate,
            'line_total': float(item.line_total),
            'vat_amount': float(item.vat_amount)
        } for item in invoice.items]

    return result


def client_to_dict(client):
    """Convert client to dictionary"""
    return {
        'id': client.id,
        'name': client.name,
        'legal_name': client.legal_name,
        'client_type': client.client_type,
        'company_code': client.company_code,
        'vat_code': client.vat_code,
        'contact_person': client.contact_person,
        'email': client.email,
        'phone': client.phone,
        'address': client.address,
        'city': client.city,
        'postal_code': client.postal_code,
        'country': client.country
    }


def product_to_dict(product):
    """Convert product to dictionary"""
    return {
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'sku': product.sku,
        'product_type': product.product_type,
        'unit_price': float(product.unit_price),
        'unit': product.unit,
        'vat_rate': product.vat_rate
    }
