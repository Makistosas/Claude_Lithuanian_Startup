#!/bin/bash
#
# SąskaitaPro - One-Click Deployment Script
# Lithuanian Small Business Invoicing Platform
#
# This script will:
# 1. Check system requirements
# 2. Generate secure secrets
# 3. Build and start the application
# 4. Initialize the database
# 5. Create a demo user (optional)
#
# Usage: ./deploy.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   ███████╗ █████╗ ███████╗██╗  ██╗ █████╗ ██╗████████╗ █████╗ ║"
echo "║   ██╔════╝██╔══██╗██╔════╝██║ ██╔╝██╔══██╗██║╚══██╔══╝██╔══██╗║"
echo "║   ███████╗███████║███████╗█████╔╝ ███████║██║   ██║   ███████║║"
echo "║   ╚════██║██╔══██║╚════██║██╔═██╗ ██╔══██║██║   ██║   ██╔══██║║"
echo "║   ███████║██║  ██║███████║██║  ██╗██║  ██║██║   ██║   ██║  ██║║"
echo "║   ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝   ╚═╝   ╚═╝  ╚═╝║"
echo "║                         PRO                                   ║"
echo "║                                                               ║"
echo "║   Lithuanian Small Business Invoicing Platform                ║"
echo "║   Version 1.0.0                                               ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo -e "${GREEN}Starting deployment...${NC}"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system requirements
echo -e "${YELLOW}[1/6] Checking system requirements...${NC}"

if ! command_exists docker; then
    echo -e "${RED}Error: Docker is not installed.${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    echo -e "${RED}Error: Docker Compose is not installed.${NC}"
    echo "Please install Docker Compose first: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"

# Check if Docker daemon is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}Error: Docker daemon is not running.${NC}"
    echo "Please start Docker and try again."
    exit 1
fi

echo -e "${GREEN}✓ Docker daemon is running${NC}"

# Generate secure secrets
echo ""
echo -e "${YELLOW}[2/6] Generating secure configuration...${NC}"

ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
    # Generate random secrets
    SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1)
    DB_PASSWORD=$(openssl rand -hex 16 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

    cat > "$ENV_FILE" << EOF
# SąskaitaPro Configuration
# Generated on $(date)

# Application Secret Key (DO NOT SHARE)
SECRET_KEY=${SECRET_KEY}

# Database Password
DB_PASSWORD=${DB_PASSWORD}

# Stripe Configuration (Get keys from https://dashboard.stripe.com/apikeys)
STRIPE_PUBLIC_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

# Email Configuration (for sending invoices)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=noreply@saskaitapro.lt

# Optional: Stripe Price IDs (create products in Stripe Dashboard)
STRIPE_BASIC_PRICE_ID=
STRIPE_PRO_PRICE_ID=
STRIPE_ENTERPRISE_PRICE_ID=
EOF

    echo -e "${GREEN}✓ Configuration file created: .env${NC}"
    echo -e "${YELLOW}  Note: Edit .env to add your Stripe and email credentials${NC}"
else
    echo -e "${GREEN}✓ Configuration file already exists${NC}"
fi

# Create SSL directory (for future HTTPS)
mkdir -p ssl

# Build and start containers
echo ""
echo -e "${YELLOW}[3/6] Building application...${NC}"

# Use docker-compose or docker compose depending on what's available
if command_exists docker-compose; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

$COMPOSE_CMD build --no-cache

echo -e "${GREEN}✓ Application built successfully${NC}"

echo ""
echo -e "${YELLOW}[4/6] Starting services...${NC}"

$COMPOSE_CMD up -d

echo -e "${GREEN}✓ Services started${NC}"

# Wait for database to be ready
echo ""
echo -e "${YELLOW}[5/6] Waiting for database...${NC}"

sleep 10

# Initialize database
echo ""
echo -e "${YELLOW}[6/6] Initializing database...${NC}"

$COMPOSE_CMD exec -T app python -c "
from app import create_app, db
app = create_app('production')
with app.app_context():
    db.create_all()
    print('Database tables created successfully!')
"

# Ask about demo user
echo ""
echo -e "${YELLOW}Would you like to create a demo user for testing? (y/n)${NC}"
read -r CREATE_DEMO

if [ "$CREATE_DEMO" = "y" ] || [ "$CREATE_DEMO" = "Y" ]; then
    $COMPOSE_CMD exec -T app flask create_demo_user
fi

# Get local IP for display
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")

echo ""
echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   🎉 DEPLOYMENT SUCCESSFUL! 🎉                                ║"
echo "║                                                               ║"
echo "╠═══════════════════════════════════════════════════════════════╣"
echo "║                                                               ║"
echo "║   Your SąskaitaPro instance is now running!                   ║"
echo "║                                                               ║"
echo "║   Access URL: http://${LOCAL_IP}                              ║"
echo "║   Local URL:  http://localhost                                ║"
echo "║                                                               ║"
if [ "$CREATE_DEMO" = "y" ] || [ "$CREATE_DEMO" = "Y" ]; then
echo "║   Demo Login:                                                 ║"
echo "║     Email:    demo@saskaitapro.lt                             ║"
echo "║     Password: demo123456                                      ║"
echo "║                                                               ║"
fi
echo "╠═══════════════════════════════════════════════════════════════╣"
echo "║                                                               ║"
echo "║   NEXT STEPS:                                                 ║"
echo "║                                                               ║"
echo "║   1. Edit .env file with your Stripe and email credentials    ║"
echo "║   2. Set up a domain name pointing to this server             ║"
echo "║   3. Configure SSL certificate for HTTPS                      ║"
echo "║   4. Start acquiring customers!                               ║"
echo "║                                                               ║"
echo "╠═══════════════════════════════════════════════════════════════╣"
echo "║                                                               ║"
echo "║   USEFUL COMMANDS:                                            ║"
echo "║                                                               ║"
echo "║   View logs:      $COMPOSE_CMD logs -f                        ║"
echo "║   Stop services:  $COMPOSE_CMD down                           ║"
echo "║   Restart:        $COMPOSE_CMD restart                        ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo -e "${BLUE}Startup process completed. Good luck with your business! 💼${NC}"
echo ""
