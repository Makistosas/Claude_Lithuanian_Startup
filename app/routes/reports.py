"""
Reports Routes
Financial reports, VMI reports, analytics
"""
from flask import Blueprint, render_template, request, send_file, current_app
from flask_login import login_required, current_user
from datetime import date, datetime, timedelta
from sqlalchemy import func
import io
import csv

from app import db
from app.models import Invoice, Client, Expense

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/')
@login_required
def index():
    """Reports overview"""
    # Check if user has access to reports
    plan = current_user.plan_config
    if current_user.subscription_plan not in ['pro', 'enterprise']:
        return render_template('reports/upgrade_required.html')

    return render_template('reports/index.html')


@reports_bp.route('/revenue')
@login_required
def revenue():
    """Revenue report"""
    company = current_user.company

    # Date range
    date_from = request.args.get('from')
    date_to = request.args.get('to')

    if not date_from:
        date_from = date(date.today().year, 1, 1)
    else:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()

    if not date_to:
        date_to = date.today()
    else:
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()

    # Get paid invoices in range
    invoices = company.invoices.filter(
        Invoice.status == 'paid',
        Invoice.paid_date >= date_from,
        Invoice.paid_date <= date_to
    ).order_by(Invoice.paid_date).all()

    # Calculate totals
    total_revenue = sum(float(inv.total) for inv in invoices)
    total_vat = sum(float(inv.vat_amount) for inv in invoices)
    total_net = sum(float(inv.subtotal) for inv in invoices)

    # Monthly breakdown
    monthly_data = {}
    for inv in invoices:
        month_key = inv.paid_date.strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = {'revenue': 0, 'vat': 0, 'count': 0}
        monthly_data[month_key]['revenue'] += float(inv.total)
        monthly_data[month_key]['vat'] += float(inv.vat_amount)
        monthly_data[month_key]['count'] += 1

    # Top clients by revenue
    client_revenue = db.session.query(
        Client.id,
        Client.name,
        func.sum(Invoice.total).label('total')
    ).join(Invoice).filter(
        Invoice.company_id == company.id,
        Invoice.status == 'paid',
        Invoice.paid_date >= date_from,
        Invoice.paid_date <= date_to
    ).group_by(Client.id, Client.name).order_by(
        func.sum(Invoice.total).desc()
    ).limit(10).all()

    return render_template(
        'reports/revenue.html',
        invoices=invoices,
        total_revenue=total_revenue,
        total_vat=total_vat,
        total_net=total_net,
        monthly_data=monthly_data,
        client_revenue=client_revenue,
        date_from=date_from,
        date_to=date_to
    )


@reports_bp.route('/vat')
@login_required
def vat_report():
    """VAT (PVM) report for VMI"""
    company = current_user.company

    # Get quarter and year
    year = int(request.args.get('year', date.today().year))
    quarter = int(request.args.get('quarter', (date.today().month - 1) // 3 + 1))

    # Calculate date range for quarter
    quarter_start = date(year, (quarter - 1) * 3 + 1, 1)
    if quarter == 4:
        quarter_end = date(year, 12, 31)
    else:
        quarter_end = date(year, quarter * 3 + 1, 1) - timedelta(days=1)

    # Get invoices for the quarter
    invoices = company.invoices.filter(
        Invoice.invoice_date >= quarter_start,
        Invoice.invoice_date <= quarter_end,
        Invoice.status.in_(['sent', 'paid', 'overdue'])
    ).order_by(Invoice.invoice_date).all()

    # Group by VAT rate
    vat_breakdown = {}
    for inv in invoices:
        for item in inv.items:
            rate = item.vat_rate
            if rate not in vat_breakdown:
                vat_breakdown[rate] = {'base': 0, 'vat': 0}
            vat_breakdown[rate]['base'] += float(item.line_total)
            vat_breakdown[rate]['vat'] += float(item.vat_amount)

    total_vat = sum(v['vat'] for v in vat_breakdown.values())
    total_base = sum(v['base'] for v in vat_breakdown.values())

    return render_template(
        'reports/vat.html',
        invoices=invoices,
        vat_breakdown=vat_breakdown,
        total_vat=total_vat,
        total_base=total_base,
        year=year,
        quarter=quarter,
        quarter_start=quarter_start,
        quarter_end=quarter_end
    )


@reports_bp.route('/clients')
@login_required
def clients_report():
    """Clients analysis report"""
    company = current_user.company

    # Get all clients with their invoice stats
    clients_data = db.session.query(
        Client,
        func.count(Invoice.id).label('invoice_count'),
        func.sum(Invoice.total).label('total_invoiced'),
        func.sum(
            db.case(
                (Invoice.status == 'paid', Invoice.total),
                else_=0
            )
        ).label('total_paid'),
        func.sum(
            db.case(
                (Invoice.status.in_(['sent', 'overdue']), Invoice.total),
                else_=0
            )
        ).label('outstanding')
    ).outerjoin(Invoice).filter(
        Client.company_id == company.id
    ).group_by(Client.id).order_by(
        func.sum(Invoice.total).desc().nullslast()
    ).all()

    return render_template('reports/clients.html', clients_data=clients_data)


@reports_bp.route('/export/invoices')
@login_required
def export_invoices():
    """Export invoices to CSV"""
    company = current_user.company

    # Date range
    date_from = request.args.get('from')
    date_to = request.args.get('to')

    query = company.invoices

    if date_from:
        query = query.filter(Invoice.invoice_date >= date_from)
    if date_to:
        query = query.filter(Invoice.invoice_date <= date_to)

    invoices = query.order_by(Invoice.invoice_date).all()

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        'Sąskaitos Nr.', 'Data', 'Terminas', 'Klientas',
        'Suma be PVM', 'PVM', 'Viso', 'Būsena', 'Apmokėta'
    ])

    # Data
    for inv in invoices:
        writer.writerow([
            inv.invoice_number,
            inv.invoice_date.strftime('%Y-%m-%d'),
            inv.due_date.strftime('%Y-%m-%d'),
            inv.client.name,
            float(inv.subtotal),
            float(inv.vat_amount),
            float(inv.total),
            inv.status,
            inv.paid_date.strftime('%Y-%m-%d') if inv.paid_date else ''
        ])

    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'saskaitos_{date.today().strftime("%Y%m%d")}.csv'
    )


@reports_bp.route('/export/vat')
@login_required
def export_vat():
    """Export VAT report for VMI (SAF-T lite format)"""
    company = current_user.company

    year = int(request.args.get('year', date.today().year))
    quarter = int(request.args.get('quarter', (date.today().month - 1) // 3 + 1))

    quarter_start = date(year, (quarter - 1) * 3 + 1, 1)
    if quarter == 4:
        quarter_end = date(year, 12, 31)
    else:
        quarter_end = date(year, quarter * 3 + 1, 1) - timedelta(days=1)

    invoices = company.invoices.filter(
        Invoice.invoice_date >= quarter_start,
        Invoice.invoice_date <= quarter_end,
        Invoice.status.in_(['sent', 'paid', 'overdue'])
    ).order_by(Invoice.invoice_date).all()

    # Create CSV for VMI
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')

    # SAF-T lite header
    writer.writerow([
        'Dokumento tipas', 'Dokumento numeris', 'Dokumento data',
        'Pirkėjo kodas', 'Pirkėjo PVM kodas', 'Pirkėjo pavadinimas',
        'Apmokestinama vertė', 'PVM suma', 'PVM tarifas'
    ])

    for inv in invoices:
        for item in inv.items:
            writer.writerow([
                'SF',  # Sąskaita faktūra
                inv.invoice_number,
                inv.invoice_date.strftime('%Y-%m-%d'),
                inv.client.company_code or '',
                inv.client.vat_code or '',
                inv.client.name,
                float(item.line_total),
                float(item.vat_amount),
                item.vat_rate
            ])

    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'pvm_ataskaita_{year}Q{quarter}.csv'
    )
