# SąskaitaPro - Lithuanian Small Business Invoicing Platform

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0-green.svg)

A complete SaaS platform for Lithuanian small businesses to create, send, and manage professional invoices with VAT compliance and VMI reporting.

## 🎯 Business Model

**Target Market:** 100,000+ small businesses in Lithuania

**Revenue Model:**
| Plan | Price | Target Customers |
|------|-------|-----------------|
| Nemokamas (Free) | €0/mėn. | 5 invoices/month - trials & micro businesses |
| Bazinis (Basic) | €19/mėn. | 50 invoices/month - freelancers |
| Profesionalus (Pro) | €39/mėn. | Unlimited invoices + VMI reports |
| Įmonėms (Enterprise) | €99/mėn. | Multi-user + API access |

**Revenue Target:** 100 customers × €30 avg = **€3,000/month** (~$3,200 USD)

## ✨ Features

### Core Features (All Plans)
- 📄 Professional Lithuanian invoices with your branding
- 📊 Automatic VAT (PVM) calculation (21%, 9%, 5%, 0%)
- 📧 Send invoices directly via email
- 📱 Mobile-responsive design
- 🔐 Secure authentication
- 📥 PDF export

### Pro Features
- 📈 VMI-compatible reports (SAF-T lite format)
- 📊 Revenue analytics and charts
- 💰 Expense tracking
- ⚡ Unlimited invoices and clients
- 🔔 Payment reminders

### Enterprise Features
- 👥 Multiple users
- 🔌 RESTful API access
- 🎯 Dedicated support

## 🚀 Quick Start (One Click Deployment)

### Prerequisites
- Linux server (Ubuntu 20.04+ recommended) or Mac
- Docker and Docker Compose installed
- Port 80 available

### Deploy in One Command

```bash
# Clone the repository
git clone <repository-url> saskaitapro
cd saskaitapro

# Run the deployment script
./deploy.sh
```

That's it! The script will:
1. Check system requirements
2. Generate secure secrets
3. Build the application
4. Start all services (app, database, nginx)
5. Initialize the database
6. Optionally create a demo user

### Access Your Platform

After deployment:
- **URL:** http://your-server-ip
- **Demo Login:** demo@saskaitapro.lt / demo123456

## 📋 Configuration

### Environment Variables

Edit the `.env` file created during deployment:

```env
# Required: Generate a secure key
SECRET_KEY=your-secure-secret-key

# Database (auto-configured)
DB_PASSWORD=auto-generated

# Stripe Payments (get from dashboard.stripe.com)
STRIPE_PUBLIC_KEY=pk_live_xxx
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Email (for sending invoices)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### Setting Up Stripe

1. Create account at [stripe.com](https://stripe.com)
2. Go to Dashboard → Products
3. Create products for each plan:
   - Bazinis: €19/month recurring
   - Profesionalus: €39/month recurring
   - Įmonėms: €99/month recurring
4. Copy the Price IDs to `.env`
5. Set up webhook endpoint: `https://yourdomain.lt/payments/webhook`

### Setting Up Email

For Gmail:
1. Enable 2-factor authentication
2. Create App Password (Security → App passwords)
3. Use the app password in `MAIL_PASSWORD`

## 🏗️ Project Structure

```
saskaitapro/
├── app/
│   ├── __init__.py          # Application factory
│   ├── models.py            # Database models
│   ├── forms.py             # WTForms definitions
│   ├── routes/              # Blueprint routes
│   │   ├── auth.py          # Authentication
│   │   ├── dashboard.py     # Main dashboard
│   │   ├── invoices.py      # Invoice management
│   │   ├── clients.py       # Client management
│   │   ├── products.py      # Product catalog
│   │   ├── reports.py       # VMI reports
│   │   ├── payments.py      # Stripe integration
│   │   └── api.py           # REST API
│   ├── services/
│   │   ├── pdf_generator.py # Invoice PDF creation
│   │   └── email_service.py # Email sending
│   └── templates/           # Jinja2 templates
├── config.py                # Configuration
├── run.py                   # Application entry
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker image
├── docker-compose.yml       # Service orchestration
├── nginx.conf               # Nginx configuration
├── deploy.sh                # One-click deployment
└── README.md                # This file
```

## 💻 Development

### Local Development Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_APP=run.py
export FLASK_ENV=development
export FLASK_DEBUG=1

# Initialize database
flask init_db
flask create_demo_user

# Run development server
flask run
```

### Database Migrations

```bash
# Create migration
flask db migrate -m "Description"

# Apply migrations
flask db upgrade
```

## 📈 Marketing Strategy

### Customer Acquisition Channels

1. **Google Ads (Lithuanian)**
   - Keywords: "sąskaitos faktūros programa", "buhalterija smulkiam verslui"
   - Budget: €200-500/month initially

2. **Facebook/Instagram Ads**
   - Target: Lithuanian entrepreneurs, freelancers
   - Lookalike audiences from sign-ups

3. **SEO**
   - Content: "Kaip išrašyti sąskaitą faktūrą", "PVM skaičiuoklė"
   - Local SEO for "sąskaitų programa Vilnius/Kaunas"

4. **Partnerships**
   - Accounting firms
   - Business incubators
   - Coworking spaces

5. **Content Marketing**
   - Blog about Lithuanian tax compliance
   - VMI regulation updates
   - Invoicing best practices

### Pricing Strategy

- **Free tier** → Attract users, build trust
- **Basic** → Convert active free users
- **Pro** → Upsell with VMI reports (compliance requirement)
- **Enterprise** → Target growing companies

## 🛡️ Security

- All passwords hashed with bcrypt
- CSRF protection on all forms
- Rate limiting on API endpoints
- SQL injection prevention via SQLAlchemy ORM
- XSS prevention via Jinja2 auto-escaping
- HTTPS enforced in production
- GDPR compliant (EU data storage)

## 📊 Database Schema

```
Users
├── id, email, password_hash
├── subscription_plan
└── stripe_customer_id

Companies
├── id, user_id, name
├── company_code, vat_code
├── bank_account, bank_swift
└── invoice_prefix, next_number

Clients
├── id, company_id, name
├── company_code, vat_code
└── email, address

Products
├── id, company_id, name
├── unit_price, unit
└── vat_rate

Invoices
├── id, company_id, client_id
├── invoice_number, status
├── subtotal, vat_amount, total
└── items[]
```

## 🔧 Useful Commands

```bash
# View logs
docker-compose logs -f app

# Access database
docker-compose exec db psql -U saskaitapro

# Restart services
docker-compose restart

# Update application
git pull
docker-compose build
docker-compose up -d

# Backup database
docker-compose exec db pg_dump -U saskaitapro saskaitapro > backup.sql

# Check container status
docker-compose ps
```

## 📞 Support

For issues and questions:
- Email: info@saskaitapro.lt
- GitHub Issues: [Create Issue](../../issues)

## 📄 License

MIT License - Free for commercial use

---

**Built with ❤️ for Lithuanian entrepreneurs**

*SąskaitaPro - Profesionalios sąskaitos Lietuvos verslui*
