"""
PDF Invoice Generator
Creates professional Lithuanian invoices using ReportLab
"""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
import os
import qrcode


def generate_invoice_pdf(invoice):
    """
    Generate a professional PDF invoice.

    Args:
        invoice: Invoice model instance

    Returns:
        bytes: PDF file content
    """
    buffer = BytesIO()

    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    # Styles
    styles = getSampleStyleSheet()

    # Custom styles for Lithuanian characters
    styles.add(ParagraphStyle(
        name='InvoiceTitle',
        fontSize=24,
        leading=28,
        alignment=TA_CENTER,
        spaceAfter=10*mm,
        textColor=colors.HexColor('#1e40af')
    ))

    styles.add(ParagraphStyle(
        name='CompanyName',
        fontSize=14,
        leading=18,
        alignment=TA_LEFT,
        spaceAfter=2*mm,
        textColor=colors.HexColor('#111827')
    ))

    styles.add(ParagraphStyle(
        name='CompanyInfo',
        fontSize=9,
        leading=12,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#4b5563')
    ))

    styles.add(ParagraphStyle(
        name='SectionHeader',
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        spaceAfter=3*mm,
        spaceBefore=5*mm,
        textColor=colors.HexColor('#374151'),
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='TableHeader',
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.white
    ))

    styles.add(ParagraphStyle(
        name='TableCell',
        fontSize=9,
        leading=12,
        alignment=TA_LEFT
    ))

    styles.add(ParagraphStyle(
        name='TotalLabel',
        fontSize=10,
        leading=12,
        alignment=TA_RIGHT,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='GrandTotal',
        fontSize=14,
        leading=18,
        alignment=TA_RIGHT,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1e40af')
    ))

    styles.add(ParagraphStyle(
        name='Footer',
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#6b7280')
    ))

    # Build document elements
    elements = []

    company = invoice.company
    client = invoice.client

    # Header with company info and invoice number
    header_data = [
        [
            # Left column - Company info
            Paragraph(f"<b>{company.name}</b>", styles['CompanyName']),
            # Right column - Invoice number
            Paragraph(f"<b>SĄSKAITA FAKTŪRA</b><br/>{invoice.invoice_number}", styles['InvoiceTitle'])
        ]
    ]

    header_table = Table(header_data, colWidths=[90*mm, 80*mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(header_table)

    # Company details
    company_info = []
    if company.registration_address:
        company_info.append(company.registration_address)
    if company.city and company.postal_code:
        company_info.append(f"{company.postal_code} {company.city}")
    if company.company_code:
        company_info.append(f"Įmonės kodas: {company.company_code}")
    if company.vat_code:
        company_info.append(f"PVM mokėtojo kodas: {company.vat_code}")
    if company.phone:
        company_info.append(f"Tel.: {company.phone}")
    if company.email:
        company_info.append(f"El. paštas: {company.email}")

    elements.append(Paragraph("<br/>".join(company_info), styles['CompanyInfo']))
    elements.append(Spacer(1, 8*mm))

    # Invoice dates
    dates_data = [
        ['Sąskaitos data:', invoice.invoice_date.strftime('%Y-%m-%d'),
         'Apmokėti iki:', invoice.due_date.strftime('%Y-%m-%d')]
    ]

    dates_table = Table(dates_data, colWidths=[35*mm, 40*mm, 35*mm, 40*mm])
    dates_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
    ]))
    elements.append(dates_table)
    elements.append(Spacer(1, 5*mm))

    # Client section
    elements.append(Paragraph("PIRKĖJAS", styles['SectionHeader']))

    client_info = [f"<b>{client.name}</b>"]
    if client.address:
        client_info.append(client.address)
    if client.city and client.postal_code:
        client_info.append(f"{client.postal_code} {client.city}")
    if client.company_code:
        client_info.append(f"Įmonės kodas: {client.company_code}")
    if client.vat_code:
        client_info.append(f"PVM mokėtojo kodas: {client.vat_code}")

    elements.append(Paragraph("<br/>".join(client_info), styles['CompanyInfo']))
    elements.append(Spacer(1, 8*mm))

    # Items table
    # Header row
    items_header = ['Nr.', 'Aprašymas', 'Kiekis', 'Vnt.', 'Kaina', 'PVM %', 'Suma']

    items_data = [items_header]

    for idx, item in enumerate(invoice.items, 1):
        items_data.append([
            str(idx),
            item.description[:60] + ('...' if len(item.description) > 60 else ''),
            f"{float(item.quantity):.2f}",
            item.unit,
            f"€{float(item.unit_price):.2f}",
            f"{item.vat_rate}%",
            f"€{float(item.line_total):.2f}"
        ])

    items_table = Table(
        items_data,
        colWidths=[10*mm, 65*mm, 18*mm, 15*mm, 22*mm, 18*mm, 22*mm],
        repeatRows=1
    )

    items_table.setStyle(TableStyle([
        # Header style
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 3*mm),
        ('TOPPADDING', (0, 0), (-1, 0), 3*mm),

        # Data rows style
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Nr.
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),   # Kiekis
        ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Vnt.
        ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),  # Kaina, PVM, Suma

        # Row padding
        ('BOTTOMPADDING', (0, 1), (-1, -1), 2*mm),
        ('TOPPADDING', (0, 1), (-1, -1), 2*mm),

        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),

        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#1e40af')),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#1e40af')),
    ]))

    elements.append(items_table)
    elements.append(Spacer(1, 5*mm))

    # Totals section
    totals_data = [
        ['Suma be PVM:', f"€{float(invoice.subtotal):.2f}"],
        ['PVM suma:', f"€{float(invoice.vat_amount):.2f}"],
        ['VISO MOKĖTI:', f"€{float(invoice.total):.2f}"]
    ]

    totals_table = Table(totals_data, colWidths=[130*mm, 40*mm])
    totals_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1e40af')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ('LINEABOVE', (1, -1), (1, -1), 1, colors.HexColor('#1e40af')),
    ]))

    elements.append(totals_table)
    elements.append(Spacer(1, 10*mm))

    # Payment information
    if company.bank_account:
        elements.append(Paragraph("MOKĖJIMO INFORMACIJA", styles['SectionHeader']))

        payment_info = []
        if company.bank_name:
            payment_info.append(f"Bankas: {company.bank_name}")
        payment_info.append(f"Sąskaita: {company.bank_account}")
        if company.bank_swift:
            payment_info.append(f"SWIFT/BIC: {company.bank_swift}")
        if invoice.payment_reference:
            payment_info.append(f"Mokėjimo paskirtis: {invoice.payment_reference}")

        elements.append(Paragraph("<br/>".join(payment_info), styles['CompanyInfo']))
        elements.append(Spacer(1, 5*mm))

    # Notes
    if invoice.notes:
        elements.append(Paragraph("PASTABOS", styles['SectionHeader']))
        elements.append(Paragraph(invoice.notes, styles['CompanyInfo']))
        elements.append(Spacer(1, 5*mm))

    # Footer
    elements.append(Spacer(1, 10*mm))
    footer_text = (
        "Šis dokumentas yra sąskaita faktūra ir galioja be parašo.<br/>"
        f"Sugeneruota: SąskaitaPro | saskaitapro.lt"
    )
    elements.append(Paragraph(footer_text, styles['Footer']))

    # Build PDF
    doc.build(elements)

    pdf_content = buffer.getvalue()
    buffer.close()

    return pdf_content


def generate_invoice_qr(invoice):
    """
    Generate QR code for invoice payment.

    Args:
        invoice: Invoice model instance

    Returns:
        BytesIO: QR code image
    """
    # Lithuanian payment QR format
    company = invoice.company

    qr_data = f"""BCD
002
1
SCT
{company.bank_swift or ''}
{company.name}
{company.bank_account or ''}
EUR{float(invoice.total):.2f}

{invoice.payment_reference}
Sąskaita {invoice.invoice_number}"""

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return buffer
