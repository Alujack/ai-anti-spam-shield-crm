#!/bin/bash
# ===========================================
# DigitalOcean Droplet Setup Script
# AI Anti-Spam Shield
# ===========================================
# Run this script on a fresh Ubuntu 22.04 Droplet
# Usage: curl -sSL https://raw.githubusercontent.com/YOUR_REPO/main/deploy/digitalocean/setup-droplet.sh | bash

set -e

echo "=========================================="
echo "AI Anti-Spam Shield - Droplet Setup"
echo "=========================================="

# Update system
echo "[1/6] Updating system..."
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
echo "[2/6] Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
rm get-docker.sh

# Install Docker Compose
echo "[3/6] Installing Docker Compose..."
sudo apt-get install -y docker-compose-plugin

# Install useful tools
echo "[4/6] Installing utilities..."
sudo apt-get install -y git curl htop ncdu ufw fail2ban

# Configure firewall
echo "[5/6] Configuring firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8080/tcp  # Kong Gateway (temporary, remove after setting up reverse proxy)
sudo ufw --force enable

# Configure fail2ban for SSH protection
echo "[6/6] Configuring fail2ban..."
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Log out and log back in (for docker group)"
echo "2. Clone your repository"
echo "3. Copy .env.production to .env and update values"
echo "4. Run: docker compose up -d"
echo ""
echo "Generate secrets with:"
echo "  openssl rand -base64 32  # DB_PASSWORD, ENCRYPTION_KEY"
echo "  openssl rand -base64 64  # JWT_SECRET, JWT_REFRESH_SECRET"
