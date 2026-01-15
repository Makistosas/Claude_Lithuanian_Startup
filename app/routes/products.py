"""
Product/Service Management Routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app import db
from app.models import Product, ActivityLog
from app.forms import ProductForm

products_bp = Blueprint('products', __name__)


@products_bp.route('/')
@login_required
def index():
    """List all products/services"""
    company = current_user.company
    if not company:
        flash('Prašome pirmiausia užpildyti įmonės informaciją.', 'warning')
        return redirect(url_for('settings.company'))

    # Search and filter
    search = request.args.get('search', '')
    product_type = request.args.get('type', 'all')
    show_inactive = request.args.get('show_inactive', '0') == '1'

    query = company.products

    if search:
        query = query.filter(
            Product.name.ilike(f'%{search}%') |
            Product.sku.ilike(f'%{search}%') |
            Product.description.ilike(f'%{search}%')
        )

    if product_type != 'all':
        query = query.filter_by(product_type=product_type)

    if not show_inactive:
        query = query.filter_by(is_active=True)

    # Pagination
    page = request.args.get('page', 1, type=int)
    products = query.order_by(Product.name).paginate(
        page=page, per_page=20, error_out=False
    )

    return render_template(
        'products/index.html',
        products=products,
        search=search,
        product_type=product_type,
        show_inactive=show_inactive
    )


@products_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new product/service"""
    company = current_user.company
    if not company:
        flash('Prašome pirmiausia užpildyti įmonės informaciją.', 'warning')
        return redirect(url_for('settings.company'))

    # Check product limit
    plan = current_user.plan_config
    product_limit = plan.get('products_limit', 20)
    current_count = company.products.filter_by(is_active=True).count()

    if product_limit != -1 and current_count >= product_limit:
        flash('Pasiektas produktų limitas. Atnaujinkite planą.', 'warning')
        return redirect(url_for('payments.upgrade'))

    form = ProductForm()

    if form.validate_on_submit():
        product = Product(
            company_id=company.id,
            name=form.name.data,
            description=form.description.data,
            sku=form.sku.data,
            product_type=form.product_type.data,
            unit_price=form.unit_price.data,
            unit=form.unit.data,
            vat_rate=form.vat_rate.data
        )

        db.session.add(product)
        db.session.commit()

        ActivityLog.log(
            user_id=current_user.id,
            action='created',
            entity_type='product',
            entity_id=product.id,
            ip_address=request.remote_addr
        )

        flash(f'Produktas/paslauga "{product.name}" sukurtas.', 'success')
        return redirect(url_for('products.index'))

    return render_template('products/create.html', form=form)


@products_bp.route('/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(product_id):
    """Edit product/service"""
    product = Product.query.get_or_404(product_id)

    if product.company_id != current_user.company.id:
        flash('Neturite prieigos prie šio produkto.', 'error')
        return redirect(url_for('products.index'))

    form = ProductForm(obj=product)

    if form.validate_on_submit():
        form.populate_obj(product)
        db.session.commit()

        ActivityLog.log(
            user_id=current_user.id,
            action='updated',
            entity_type='product',
            entity_id=product.id,
            ip_address=request.remote_addr
        )

        flash('Produkto informacija atnaujinta.', 'success')
        return redirect(url_for('products.index'))

    return render_template('products/edit.html', form=form, product=product)


@products_bp.route('/<int:product_id>/delete', methods=['POST'])
@login_required
def delete(product_id):
    """Deactivate product (soft delete)"""
    product = Product.query.get_or_404(product_id)

    if product.company_id != current_user.company.id:
        flash('Neturite prieigos prie šio produkto.', 'error')
        return redirect(url_for('products.index'))

    product.is_active = False
    db.session.commit()

    ActivityLog.log(
        user_id=current_user.id,
        action='deleted',
        entity_type='product',
        entity_id=product_id,
        ip_address=request.remote_addr
    )

    flash('Produktas deaktyvuotas.', 'success')
    return redirect(url_for('products.index'))


@products_bp.route('/search')
@login_required
def search():
    """Search products (AJAX)"""
    q = request.args.get('q', '')
    company = current_user.company

    products = company.products.filter(
        Product.is_active == True,
        Product.name.ilike(f'%{q}%')
    ).limit(10).all()

    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'unit_price': float(p.unit_price),
        'unit': p.unit,
        'vat_rate': p.vat_rate
    } for p in products])


@products_bp.route('/<int:product_id>/json')
@login_required
def get_product(product_id):
    """Get product details (AJAX)"""
    product = Product.query.get_or_404(product_id)

    if product.company_id != current_user.company.id:
        return jsonify({'error': 'Unauthorized'}), 403

    return jsonify({
        'id': product.id,
        'name': product.name,
        'description': product.description or '',
        'unit_price': float(product.unit_price),
        'unit': product.unit,
        'vat_rate': product.vat_rate
    })
