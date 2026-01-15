"""
Dashboard Routes
Main dashboard, overview, statistics
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from datetime import date, timedelta
from sqlalchemy import func

from app import db
from app.models import Invoice, Client, Product, Expense

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard"""
    company = current_user.company
    if not company:
        return render_template('dashboard/setup_required.html')

    # Get date ranges
    today = date.today()
    start_of_month = date(today.year, today.month, 1)
    start_of_year = date(today.year, 1, 1)

    # Calculate statistics
    stats = {
        'total_clients': company.clients.filter_by(is_active=True).count(),
        'total_products': company.products.filter_by(is_active=True).count(),
        'invoices_this_month': company.invoices.filter(
            Invoice.invoice_date >= start_of_month
        ).count(),
        'invoices_this_year': company.invoices.filter(
            Invoice.invoice_date >= start_of_year
        ).count()
    }

    # Revenue calculations
    revenue_this_month = db.session.query(
        func.sum(Invoice.total)
    ).filter(
        Invoice.company_id == company.id,
        Invoice.status == 'paid',
        Invoice.paid_date >= start_of_month
    ).scalar() or 0

    revenue_this_year = db.session.query(
        func.sum(Invoice.total)
    ).filter(
        Invoice.company_id == company.id,
        Invoice.status == 'paid',
        Invoice.paid_date >= start_of_year
    ).scalar() or 0

    outstanding = db.session.query(
        func.sum(Invoice.total)
    ).filter(
        Invoice.company_id == company.id,
        Invoice.status.in_(['sent', 'overdue'])
    ).scalar() or 0

    stats['revenue_this_month'] = float(revenue_this_month)
    stats['revenue_this_year'] = float(revenue_this_year)
    stats['outstanding'] = float(outstanding)

    # Recent invoices
    recent_invoices = company.invoices.order_by(
        Invoice.created_at.desc()
    ).limit(5).all()

    # Overdue invoices
    overdue_invoices = company.invoices.filter(
        Invoice.status == 'sent',
        Invoice.due_date < today
    ).order_by(Invoice.due_date).limit(5).all()

    # Update overdue status
    for inv in overdue_invoices:
        if inv.status == 'sent':
            inv.status = 'overdue'
    db.session.commit()

    # Recent activity (last 10 items)
    from app.models import ActivityLog
    recent_activity = ActivityLog.query.filter_by(
        user_id=current_user.id
    ).order_by(ActivityLog.created_at.desc()).limit(10).all()

    # Monthly revenue chart data (last 6 months)
    chart_data = []
    for i in range(5, -1, -1):
        month_start = date(today.year, today.month, 1) - timedelta(days=30 * i)
        if month_start.month == 12:
            month_end = date(month_start.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(month_start.year, month_start.month + 1, 1) - timedelta(days=1)

        month_revenue = db.session.query(
            func.sum(Invoice.total)
        ).filter(
            Invoice.company_id == company.id,
            Invoice.status == 'paid',
            Invoice.paid_date >= month_start,
            Invoice.paid_date <= month_end
        ).scalar() or 0

        chart_data.append({
            'month': month_start.strftime('%Y-%m'),
            'revenue': float(month_revenue)
        })

    # Plan usage
    plan = current_user.plan_config
    usage = {
        'invoices_used': current_user.invoices_this_month,
        'invoices_limit': plan.get('invoices_per_month', 5),
        'clients_used': stats['total_clients'],
        'clients_limit': plan.get('clients_limit', 10),
        'products_used': stats['total_products'],
        'products_limit': plan.get('products_limit', 20)
    }

    return render_template(
        'dashboard/index.html',
        stats=stats,
        recent_invoices=recent_invoices,
        overdue_invoices=overdue_invoices,
        recent_activity=recent_activity,
        chart_data=chart_data,
        usage=usage
    )


@dashboard_bp.route('/quick-stats')
@login_required
def quick_stats():
    """AJAX endpoint for quick stats refresh"""
    company = current_user.company
    today = date.today()
    start_of_month = date(today.year, today.month, 1)

    revenue = db.session.query(
        func.sum(Invoice.total)
    ).filter(
        Invoice.company_id == company.id,
        Invoice.status == 'paid',
        Invoice.paid_date >= start_of_month
    ).scalar() or 0

    pending = company.invoices.filter(
        Invoice.status.in_(['sent', 'overdue'])
    ).count()

    return {
        'revenue': float(revenue),
        'pending_invoices': pending,
        'invoices_this_month': current_user.invoices_this_month
    }
