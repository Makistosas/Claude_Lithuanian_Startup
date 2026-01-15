"""
Email Service
Handles sending invoices and notifications
"""
from flask import current_app, render_template_string
from flask_mail import Message
from app import mail
import logging

logger = logging.getLogger(__name__)


# Email templates
INVOICE_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #1e40af; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9fafb; }
        .invoice-details { background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }
        .total { font-size: 24px; color: #1e40af; font-weight: bold; }
        .footer { text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }
        .btn { display: inline-block; background: #1e40af; color: white; padding: 12px 24px;
               text-decoration: none; border-radius: 6px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ company_name }}</h1>
        </div>
        <div class="content">
            <p>Sveiki,</p>
            <p>Siunčiame jums sąskaitą faktūrą <strong>{{ invoice_number }}</strong>.</p>

            <div class="invoice-details">
                <p><strong>Sąskaitos numeris:</strong> {{ invoice_number }}</p>
                <p><strong>Sąskaitos data:</strong> {{ invoice_date }}</p>
                <p><strong>Apmokėti iki:</strong> {{ due_date }}</p>
                <p class="total">Suma: €{{ total }}</p>
            </div>

            {% if bank_account %}
            <div class="invoice-details">
                <p><strong>Mokėjimo informacija:</strong></p>
                <p>Bankas: {{ bank_name }}</p>
                <p>Sąskaita: {{ bank_account }}</p>
                <p>Mokėjimo paskirtis: {{ payment_reference }}</p>
            </div>
            {% endif %}

            <p>Sąskaita faktūra PDF formatu pridėta prie šio laiško.</p>

            <p>Jei turite klausimų, susisiekite su mumis.</p>

            <p>Pagarbiai,<br>{{ company_name }}</p>
        </div>
        <div class="footer">
            <p>Šis laiškas sugeneruotas automatiškai per SąskaitaPro sistemą.</p>
        </div>
    </div>
</body>
</html>
"""

INVOICE_EMAIL_SUBJECT = "Sąskaita faktūra {{ invoice_number }} - {{ company_name }}"


def send_invoice_email(invoice, pdf_content):
    """
    Send invoice to client via email.

    Args:
        invoice: Invoice model instance
        pdf_content: bytes of PDF file

    Returns:
        bool: True if sent successfully
    """
    client = invoice.client
    company = invoice.company

    if not client.email:
        raise ValueError("Klientas neturi el. pašto adreso")

    # Render email content
    subject = render_template_string(INVOICE_EMAIL_SUBJECT,
        invoice_number=invoice.invoice_number,
        company_name=company.name
    )

    html_content = render_template_string(INVOICE_EMAIL_TEMPLATE,
        company_name=company.name,
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date.strftime('%Y-%m-%d'),
        due_date=invoice.due_date.strftime('%Y-%m-%d'),
        total=f"{float(invoice.total):.2f}",
        bank_name=company.bank_name,
        bank_account=company.bank_account,
        payment_reference=invoice.payment_reference
    )

    try:
        msg = Message(
            subject=subject,
            recipients=[client.email],
            html=html_content,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )

        # Attach PDF
        msg.attach(
            f"{invoice.invoice_number}.pdf",
            "application/pdf",
            pdf_content
        )

        mail.send(msg)
        logger.info(f"Invoice {invoice.invoice_number} sent to {client.email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send invoice email: {str(e)}")
        raise


def send_password_reset_email(user, reset_url):
    """
    Send password reset email.

    Args:
        user: User model instance
        reset_url: Password reset URL
    """
    subject = "Slaptažodžio atkūrimas - SąskaitaPro"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .btn {{ display: inline-block; background: #1e40af; color: white;
                   padding: 12px 24px; text-decoration: none; border-radius: 6px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Slaptažodžio atkūrimas</h2>
            <p>Sveiki {user.first_name},</p>
            <p>Gavome prašymą atkurti jūsų SąskaitaPro paskyros slaptažodį.</p>
            <p>Spauskite žemiau esantį mygtuką, kad nustatytumėte naują slaptažodį:</p>
            <p><a href="{reset_url}" class="btn">Atkurti slaptažodį</a></p>
            <p>Jei neprašėte slaptažodžio atkūrimo, galite ignoruoti šį laišką.</p>
            <p>Nuoroda galioja 24 valandas.</p>
            <p>Pagarbiai,<br>SąskaitaPro komanda</p>
        </div>
    </body>
    </html>
    """

    try:
        msg = Message(
            subject=subject,
            recipients=[user.email],
            html=html_content
        )
        mail.send(msg)
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email: {str(e)}")
        return False


def send_welcome_email(user):
    """
    Send welcome email to new user.

    Args:
        user: User model instance
    """
    subject = "Sveiki atvykę į SąskaitaPro!"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #1e40af; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .feature {{ margin: 10px 0; padding: 10px; background: #f3f4f6; border-radius: 6px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Sveiki atvykę į SąskaitaPro!</h1>
            </div>
            <div class="content">
                <p>Sveiki {user.first_name},</p>
                <p>Džiaugiamės, kad prisijungėte prie SąskaitaPro - profesionalios sąskaitų faktūrų
                   sistemos Lietuvos verslui.</p>

                <h3>Ką galite daryti:</h3>
                <div class="feature">✅ Kurti profesionalias sąskaitas faktūras</div>
                <div class="feature">✅ Valdyti klientų bazę</div>
                <div class="feature">✅ Sekti mokėjimus</div>
                <div class="feature">✅ Generuoti VMI ataskaitas</div>

                <p>Pradėkite nuo įmonės informacijos užpildymo nustatymuose.</p>

                <p>Jei turite klausimų, rašykite mums: info@saskaitapro.lt</p>

                <p>Sėkmės verslui!<br>SąskaitaPro komanda</p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        msg = Message(
            subject=subject,
            recipients=[user.email],
            html=html_content
        )
        mail.send(msg)
        return True
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        return False


def send_payment_reminder(invoice):
    """
    Send payment reminder for overdue invoice.

    Args:
        invoice: Invoice model instance
    """
    client = invoice.client
    company = invoice.company

    if not client.email:
        return False

    days_overdue = (invoice.due_date - invoice.invoice_date).days

    subject = f"Priminimas: Sąskaita {invoice.invoice_number} - {company.name}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .alert {{ background: #fef2f2; border: 1px solid #fecaca;
                     padding: 15px; border-radius: 8px; margin: 15px 0; }}
            .total {{ font-size: 24px; color: #dc2626; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Priminimas apie neapmokėtą sąskaitą</h2>
            <p>Sveiki,</p>

            <div class="alert">
                <p>Norime priminti, kad sąskaita faktūra <strong>{invoice.invoice_number}</strong>
                   yra neapmokėta.</p>
                <p><strong>Terminas buvo:</strong> {invoice.due_date.strftime('%Y-%m-%d')}</p>
                <p class="total">Mokėtina suma: €{float(invoice.total):.2f}</p>
            </div>

            <p><strong>Mokėjimo informacija:</strong></p>
            <p>Sąskaita: {company.bank_account or 'Nenurodyta'}</p>
            <p>Mokėjimo paskirtis: {invoice.payment_reference}</p>

            <p>Prašome apmokėti sąskaitą artimiausiu metu.</p>
            <p>Jei jau atlikote mokėjimą, prašome nekreipti dėmesio į šį laišką.</p>

            <p>Pagarbiai,<br>{company.name}</p>
        </div>
    </body>
    </html>
    """

    try:
        msg = Message(
            subject=subject,
            recipients=[client.email],
            html=html_content
        )
        mail.send(msg)
        return True
    except Exception as e:
        logger.error(f"Failed to send payment reminder: {str(e)}")
        return False
