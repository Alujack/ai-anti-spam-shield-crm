#!/bin/bash
# ===========================================
# SSL Setup Script for DigitalOcean Droplet
# Uses Let's Encrypt with Certbot
# ===========================================
# Usage: ./setup-ssl.sh yourdomain.com your@email.com

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check arguments
if [ -z "$1" ] || [ -z "$2" ]; then
    echo -e "${RED}Usage: ./setup-ssl.sh <domain> <email>${NC}"
    echo "Example: ./setup-ssl.sh aiscamshield.codes admin@aiscamshield.codes"
    exit 1
fi

DOMAIN=$1
EMAIL=$2

echo -e "${GREEN}=========================================="
echo "SSL Setup for $DOMAIN"
echo -e "==========================================${NC}"

# Step 1: Install Certbot
echo -e "${YELLOW}[1/5] Installing Certbot...${NC}"
apt update
apt install -y certbot

# Step 2: Stop containers to free port 80
echo -e "${YELLOW}[2/5] Temporarily stopping services...${NC}"
cd /root/ai-anti-spam-shield-crm/deploy/digitalocean
docker compose -f docker-compose.prod.yml down || true

# Step 3: Generate certificate
echo -e "${YELLOW}[3/5] Generating SSL certificate...${NC}"
certbot certonly --standalone \
    -d $DOMAIN \
    -d www.$DOMAIN \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --non-interactive

# Step 4: Create certificate directory for Kong
echo -e "${YELLOW}[4/5] Setting up certificates for Kong...${NC}"
mkdir -p /etc/kong/ssl
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /etc/kong/ssl/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /etc/kong/ssl/
chmod 644 /etc/kong/ssl/*.pem

# Step 5: Setup auto-renewal
echo -e "${YELLOW}[5/5] Setting up auto-renewal...${NC}"
cat > /etc/cron.d/certbot-renewal << 'EOF'
# Renew certificates twice daily
0 0,12 * * * root certbot renew --pre-hook "docker compose -f /root/ai-anti-spam-shield-crm/deploy/digitalocean/docker-compose.prod.yml down" --post-hook "cp /etc/letsencrypt/live/*/fullchain.pem /etc/kong/ssl/ && cp /etc/letsencrypt/live/*/privkey.pem /etc/kong/ssl/ && docker compose -f /root/ai-anti-spam-shield-crm/deploy/digitalocean/docker-compose.prod.yml up -d" --quiet
EOF

echo -e "${GREEN}=========================================="
echo "SSL Certificate Generated!"
echo -e "==========================================${NC}"
echo ""
echo "Certificate files:"
echo "  - /etc/kong/ssl/fullchain.pem"
echo "  - /etc/kong/ssl/privkey.pem"
echo ""
echo "Now restart the services:"
echo "  cd /root/ai-anti-spam-shield-crm/deploy/digitalocean"
echo "  docker compose -f docker-compose.prod.yml up -d"
echo ""
echo -e "${YELLOW}Your API will be available at: https://$DOMAIN${NC}"
