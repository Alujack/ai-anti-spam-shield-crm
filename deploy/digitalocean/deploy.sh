#!/bin/bash
# ===========================================
# Deploy Script for DigitalOcean
# ===========================================
# Usage: ./deploy.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=========================================="
echo "AI Anti-Spam Shield - Deploy"
echo -e "==========================================${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Copy .env.production to .env and update the values:"
    echo "  cp .env.production .env"
    echo "  nano .env"
    exit 1
fi

# Check for placeholder values
if grep -q "CHANGE_ME" .env; then
    echo -e "${RED}Error: .env contains placeholder values!${NC}"
    echo "Update all CHANGE_ME values with secure secrets."
    echo ""
    echo "Generate secrets with:"
    echo "  openssl rand -base64 32  # For DB_PASSWORD, ENCRYPTION_KEY"
    echo "  openssl rand -base64 64  # For JWT_SECRET, JWT_REFRESH_SECRET"
    exit 1
fi

# Pull latest changes
echo -e "${YELLOW}[1/4] Pulling latest changes...${NC}"
git pull origin main

# Build images
echo -e "${YELLOW}[2/4] Building Docker images...${NC}"
docker compose -f docker-compose.prod.yml build

# Stop existing containers
echo -e "${YELLOW}[3/4] Stopping existing containers...${NC}"
docker compose -f docker-compose.prod.yml down

# Start containers
echo -e "${YELLOW}[4/4] Starting containers...${NC}"
docker compose -f docker-compose.prod.yml up -d

# Wait for services
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Check status
echo -e "${GREEN}=========================================="
echo "Deployment complete!"
echo -e "==========================================${NC}"
docker compose -f docker-compose.prod.yml ps

echo ""
echo "Check logs with:"
echo "  docker compose -f docker-compose.prod.yml logs -f"
echo ""
echo "API available at: http://$(curl -s ifconfig.me):80"
