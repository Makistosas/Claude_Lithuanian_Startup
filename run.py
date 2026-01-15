#!/usr/bin/env python3
"""
SąskaitaPro - Lithuanian Small Business Invoicing Platform
Main Application Entry Point
"""
import os
from app import create_app, db
from app.models import User, Company, Client, Product, Invoice

# Create application instance
app = create_app(os.environ.get('FLASK_CONFIG', 'default'))


@app.shell_context_processor
def make_shell_context():
    """Add models to shell context for debugging"""
    return {
        'db': db,
        'User': User,
        'Company': Company,
        'Client': Client,
        'Product': Product,
        'Invoice': Invoice
    }


@app.cli.command()
def init_db():
    """Initialize the database with tables"""
    db.create_all()
    print('Database tables created.')


@app.cli.command()
def create_demo_user():
    """Create a demo user for testing"""
    from app.models import User, Company, Client, Product

    # Check if demo user exists
    if User.query.filter_by(email='demo@saskaitapro.lt').first():
        print('Demo user already exists.')
        return

    # Create demo user
    user = User(
        email='demo@saskaitapro.lt',
        first_name='Demo',
        last_name='Vartotojas',
        phone='+370 600 00000',
        is_verified=True,
        subscription_plan='pro'
    )
    user.set_password('demo123456')
    db.session.add(user)
    db.session.commit()

    # Create company
    company = Company(
        user_id=user.id,
        name='Demo UAB',
        legal_name='Demo UAB',
        company_code='123456789',
        vat_code='LT123456789',
        registration_address='Gedimino pr. 1',
        city='Vilnius',
        postal_code='LT-01103',
        country='Lietuva',
        email='info@demo.lt',
        phone='+370 5 123 4567',
        bank_name='Swedbank',
        bank_account='LT12 7300 0123 4567 8901',
        bank_swift='HABALT22',
        invoice_prefix='SF',
        payment_terms=14
    )
    db.session.add(company)
    db.session.commit()

    # Create sample clients
    clients = [
        Client(
            company_id=company.id,
            name='Klientas UAB',
            legal_name='Klientas UAB',
            client_type='company',
            company_code='987654321',
            vat_code='LT987654321',
            contact_person='Jonas Jonaitis',
            email='jonas@klientas.lt',
            phone='+370 600 11111',
            address='Konstitucijos pr. 20',
            city='Vilnius',
            postal_code='LT-09308'
        ),
        Client(
            company_id=company.id,
            name='Partneris AB',
            client_type='company',
            company_code='111222333',
            email='info@partneris.lt',
            address='Laisvės al. 100',
            city='Kaunas',
            postal_code='LT-44001'
        )
    ]
    for client in clients:
        db.session.add(client)

    # Create sample products
    products = [
        Product(
            company_id=company.id,
            name='IT konsultacijos',
            description='IT konsultacijos ir palaikymas',
            product_type='service',
            unit_price=75.00,
            unit='val.',
            vat_rate=21
        ),
        Product(
            company_id=company.id,
            name='Svetainės kūrimas',
            description='Interneto svetainės sukūrimas',
            product_type='service',
            unit_price=1500.00,
            unit='vnt.',
            vat_rate=21
        ),
        Product(
            company_id=company.id,
            name='Mėnesinis palaikymas',
            description='Techninė priežiūra ir palaikymas',
            product_type='service',
            unit_price=200.00,
            unit='mėn.',
            vat_rate=21
        )
    ]
    for product in products:
        db.session.add(product)

    db.session.commit()
    print('Demo user created successfully!')
    print('Email: demo@saskaitapro.lt')
    print('Password: demo123456')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
