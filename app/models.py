"""
SąskaitaPro Database Models
Lithuanian Small Business Invoicing Platform
"""
from datetime import datetime, date
from decimal import Decimal
import secrets
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    """User account model"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100))
    reset_token = db.Column(db.String(100))
    reset_token_expiry = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Subscription
    subscription_plan = db.Column(db.String(20), default='free')
    stripe_customer_id = db.Column(db.String(100))
    stripe_subscription_id = db.Column(db.String(100))
    subscription_expires = db.Column(db.DateTime)

    # Relationships
    company = db.relationship('Company', backref='owner', uselist=False, lazy=True)
    invoices = db.relationship('Invoice', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_verification_token(self):
        self.verification_token = secrets.token_urlsafe(32)
        return self.verification_token

    def generate_reset_token(self):
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.utcnow()
        return self.reset_token

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def plan_config(self):
        from flask import current_app
        return current_app.config['SUBSCRIPTION_PLANS'].get(self.subscription_plan, {})

    @property
    def invoices_this_month(self):
        """Count invoices created this month"""
        today = date.today()
        start_of_month = date(today.year, today.month, 1)
        return self.invoices.filter(Invoice.created_at >= start_of_month).count()

    @property
    def can_create_invoice(self):
        """Check if user can create more invoices"""
        limit = self.plan_config.get('invoices_per_month', 5)
        if limit == -1:  # Unlimited
            return True
        return self.invoices_this_month < limit

    def __repr__(self):
        return f'<User {self.email}>'


class Company(db.Model):
    """Company/Business profile model"""
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Company details
    name = db.Column(db.String(200), nullable=False)
    legal_name = db.Column(db.String(200))  # Official registered name
    company_code = db.Column(db.String(20))  # Įmonės kodas
    vat_code = db.Column(db.String(20))  # PVM mokėtojo kodas (LT + 9-12 digits)
    registration_address = db.Column(db.String(300))
    business_address = db.Column(db.String(300))
    city = db.Column(db.String(100))
    postal_code = db.Column(db.String(10))
    country = db.Column(db.String(50), default='Lietuva')

    # Contact
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    website = db.Column(db.String(200))

    # Banking
    bank_name = db.Column(db.String(100))
    bank_account = db.Column(db.String(30))  # IBAN
    bank_swift = db.Column(db.String(11))  # BIC/SWIFT

    # Branding
    logo = db.Column(db.String(200))  # Path to logo file
    primary_color = db.Column(db.String(7), default='#2563eb')

    # Invoice settings
    invoice_prefix = db.Column(db.String(10), default='SF')
    next_invoice_number = db.Column(db.Integer, default=1)
    invoice_notes = db.Column(db.Text)  # Default notes on invoices
    payment_terms = db.Column(db.Integer, default=14)  # Days

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    clients = db.relationship('Client', backref='company', lazy='dynamic')
    products = db.relationship('Product', backref='company', lazy='dynamic')
    invoices = db.relationship('Invoice', backref='company', lazy='dynamic')

    def get_next_invoice_number(self):
        """Get and increment invoice number"""
        number = self.next_invoice_number
        self.next_invoice_number += 1
        db.session.commit()
        return f"{self.invoice_prefix}{number:06d}"

    def __repr__(self):
        return f'<Company {self.name}>'


class Client(db.Model):
    """Client/Customer model"""
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    # Client details
    name = db.Column(db.String(200), nullable=False)
    legal_name = db.Column(db.String(200))
    client_type = db.Column(db.String(20), default='company')  # company or individual
    company_code = db.Column(db.String(20))
    vat_code = db.Column(db.String(20))

    # Contact
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))

    # Address
    address = db.Column(db.String(300))
    city = db.Column(db.String(100))
    postal_code = db.Column(db.String(10))
    country = db.Column(db.String(50), default='Lietuva')

    # Notes
    notes = db.Column(db.Text)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    invoices = db.relationship('Invoice', backref='client', lazy='dynamic')

    @property
    def total_invoiced(self):
        """Total amount invoiced to this client"""
        return sum(inv.total for inv in self.invoices.filter_by(status='paid').all())

    @property
    def outstanding_balance(self):
        """Outstanding balance for this client"""
        return sum(inv.total for inv in self.invoices.filter(
            Invoice.status.in_(['sent', 'overdue'])
        ).all())

    def __repr__(self):
        return f'<Client {self.name}>'


class Product(db.Model):
    """Product/Service model"""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    # Product details
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    sku = db.Column(db.String(50))  # Stock keeping unit
    product_type = db.Column(db.String(20), default='service')  # product or service

    # Pricing
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(db.String(20), default='vnt.')  # vnt., val., mėn., etc.
    vat_rate = db.Column(db.Integer, default=21)  # VAT percentage

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Product {self.name}>'


class Invoice(db.Model):
    """Invoice model"""
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)

    # Invoice details
    invoice_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    invoice_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, sent, paid, overdue, cancelled

    # Amounts (stored in EUR)
    subtotal = db.Column(db.Numeric(10, 2), default=0)
    vat_amount = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), default=0)

    # Additional info
    notes = db.Column(db.Text)
    internal_notes = db.Column(db.Text)
    payment_reference = db.Column(db.String(50))  # For bank transfers

    # Payment tracking
    paid_date = db.Column(db.Date)
    paid_amount = db.Column(db.Numeric(10, 2))

    # Email tracking
    sent_at = db.Column(db.DateTime)
    viewed_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = db.relationship('InvoiceItem', backref='invoice', lazy=True,
                            cascade='all, delete-orphan')

    def calculate_totals(self):
        """Calculate invoice totals from items"""
        self.subtotal = sum(Decimal(str(item.line_total)) for item in self.items)
        self.vat_amount = sum(Decimal(str(item.vat_amount)) for item in self.items)
        self.total = self.subtotal + self.vat_amount

    def generate_payment_reference(self):
        """Generate unique payment reference for bank transfer"""
        self.payment_reference = f"SF{self.id:08d}"
        return self.payment_reference

    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        if self.status in ['paid', 'cancelled', 'draft']:
            return False
        return date.today() > self.due_date

    def mark_as_sent(self):
        """Mark invoice as sent"""
        self.status = 'sent'
        self.sent_at = datetime.utcnow()

    def mark_as_paid(self, paid_date=None, amount=None):
        """Mark invoice as paid"""
        self.status = 'paid'
        self.paid_date = paid_date or date.today()
        self.paid_amount = amount or self.total

    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'


class InvoiceItem(db.Model):
    """Invoice line item model"""
    __tablename__ = 'invoice_items'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))

    # Item details
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False, default=1)
    unit = db.Column(db.String(20), default='vnt.')
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    vat_rate = db.Column(db.Integer, default=21)

    # Calculated fields (stored for historical accuracy)
    line_total = db.Column(db.Numeric(10, 2))  # quantity * unit_price
    vat_amount = db.Column(db.Numeric(10, 2))  # line_total * vat_rate / 100

    position = db.Column(db.Integer, default=0)  # Order in invoice

    def calculate(self):
        """Calculate line totals"""
        self.line_total = Decimal(str(self.quantity)) * Decimal(str(self.unit_price))
        self.vat_amount = self.line_total * Decimal(str(self.vat_rate)) / Decimal('100')

    def __repr__(self):
        return f'<InvoiceItem {self.description[:30]}>'


class Expense(db.Model):
    """Expense tracking model"""
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    # Expense details
    description = db.Column(db.String(300), nullable=False)
    category = db.Column(db.String(50))  # office, travel, supplies, etc.
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    vat_amount = db.Column(db.Numeric(10, 2), default=0)
    expense_date = db.Column(db.Date, nullable=False, default=date.today)

    # Vendor info
    vendor_name = db.Column(db.String(200))
    vendor_vat_code = db.Column(db.String(20))

    # Receipt/document
    receipt_number = db.Column(db.String(50))
    receipt_file = db.Column(db.String(200))

    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    company_rel = db.relationship('Company', backref='expenses')

    def __repr__(self):
        return f'<Expense {self.description[:30]}>'


class ActivityLog(db.Model):
    """Activity logging for audit trail"""
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(50), nullable=False)  # created, updated, deleted, sent, etc.
    entity_type = db.Column(db.String(50))  # invoice, client, product, etc.
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)  # JSON with additional details
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref='activities')

    @classmethod
    def log(cls, user_id, action, entity_type=None, entity_id=None, details=None, ip_address=None):
        """Create a new activity log entry"""
        log = cls(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address
        )
        db.session.add(log)
        db.session.commit()
        return log

    def __repr__(self):
        return f'<ActivityLog {self.action} {self.entity_type}>'
