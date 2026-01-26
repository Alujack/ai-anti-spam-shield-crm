# AI Anti-Spam Shield - DigitalOcean Deployment Guide

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Prerequisites](#prerequisites)
4. [Step 1: Create DigitalOcean Droplet](#step-1-create-digitalocean-droplet)
5. [Step 2: Initial Server Setup](#step-2-initial-server-setup)
6. [Step 3: Clone Repository](#step-3-clone-repository)
7. [Step 4: Configure Environment](#step-4-configure-environment)
8. [Step 5: Train ML Models](#step-5-train-ml-models)
9. [Step 6: Deploy with Docker](#step-6-deploy-with-docker)
10. [Step 7: Setup SSL Certificate](#step-7-setup-ssl-certificate)
11. [Step 8: Verify Deployment](#step-8-verify-deployment)
12. [Troubleshooting](#troubleshooting)
13. [Maintenance](#maintenance)

---

## Overview

This guide covers deploying the AI Anti-Spam Shield application to DigitalOcean. The application consists of:

| Service | Description | Port |
|---------|-------------|------|
| **Kong Gateway** | API Gateway with rate limiting | 80, 443 |
| **Node.js Backend** | REST API server | 3000 |
| **Worker** | Background job processor | - |
| **ML Service** | FastAPI spam/phishing detection | 8000 |
| **PostgreSQL** | Database | 5432 |
| **Redis** | Cache & job queue | 6379 |

### Three Scanning Systems

| System | Backend Endpoint | ML Endpoint | Purpose |
|--------|-----------------|-------------|---------|
| Message Scan | `/api/v1/messages/scan-text` | `/predict` | SMS/text spam detection |
| Voice Scan | `/api/v1/messages/scan-voice` | `/predict-voice` | Voice message spam detection |
| Phishing Scan | `/api/v1/phishing/scan-text` | `/predict-phishing` | Phishing/scam detection |

---

## System Architecture

```
                    ┌─────────────────┐
                    │   Mobile App    │
                    │   (Flutter)     │
                    └────────┬────────┘
                             │ HTTPS
                             ▼
                    ┌─────────────────┐
                    │  Kong Gateway   │
                    │  (Port 80/443)  │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
    ┌───────────┐    ┌───────────┐    ┌───────────┐
    │  Backend  │    │  Worker   │    │ ML Service│
    │ (Node.js) │    │ (BullMQ)  │    │ (FastAPI) │
    │ Port 3000 │    │           │    │ Port 8000 │
    └─────┬─────┘    └─────┬─────┘    └───────────┘
          │                │
          ▼                ▼
    ┌───────────┐    ┌───────────┐
    │ PostgreSQL│    │   Redis   │
    │ Port 5432 │    │ Port 6379 │
    └───────────┘    └───────────┘
```

---

## Prerequisites

- DigitalOcean account with $200 GitHub Student Pack credits
- Domain name (e.g., `aiscamshield.codes`)
- SSH key pair for server access
- Git repository with the project code

---

## Step 1: Create DigitalOcean Droplet

### 1.1 Login to DigitalOcean
Go to [cloud.digitalocean.com](https://cloud.digitalocean.com)

### 1.2 Create Droplet
1. Click **Create** → **Droplets**
2. Choose settings:

| Setting | Value |
|---------|-------|
| Region | Singapore (SGP1) or nearest |
| Image | Ubuntu 24.04 LTS |
| Size | **$24/month** (2 vCPU, 4GB RAM, 80GB SSD) |
| Authentication | SSH Key (recommended) |

### 1.3 Add SSH Key
```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# Copy public key
cat ~/.ssh/id_rsa.pub
```

Paste the public key in DigitalOcean.

### 1.4 Create Droplet
Click **Create Droplet** and note the IP address (e.g., `165.245.182.155`)

---

## Step 2: Initial Server Setup

### 2.1 SSH into Server
```bash
ssh root@YOUR_DROPLET_IP
```

### 2.2 Update System
```bash
apt update && apt upgrade -y
```

### 2.3 Install Docker
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version
```

### 2.4 Install Additional Tools
```bash
apt install -y git curl certbot
```

### 2.5 Configure Firewall
```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

---

## Step 3: Clone Repository

### 3.1 Clone the Project
```bash
cd /root
git clone https://github.com/YOUR_USERNAME/ai-anti-spam-shield-crm.git
cd ai-anti-spam-shield-crm
```

### 3.2 Navigate to Deploy Directory
```bash
cd deploy/digitalocean
```

---

## Step 4: Configure Environment

### 4.1 Create Environment File
```bash
cp .env.example .env
nano .env
```

### 4.2 Generate Secure Secrets
```bash
# Generate secrets
echo "DB_PASSWORD=$(openssl rand -base64 32)"
echo "JWT_SECRET=$(openssl rand -base64 64)"
echo "JWT_REFRESH_SECRET=$(openssl rand -base64 64)"
echo "ENCRYPTION_KEY=$(openssl rand -base64 32)"
```

### 4.3 Edit .env File
```env
# Database
DB_PASSWORD=YOUR_GENERATED_PASSWORD

# JWT Secrets
JWT_SECRET=YOUR_GENERATED_JWT_SECRET
JWT_REFRESH_SECRET=YOUR_GENERATED_REFRESH_SECRET

# Encryption
ENCRYPTION_KEY=YOUR_GENERATED_ENCRYPTION_KEY

# Domain (optional)
DOMAIN=aiscamshield.codes
```

### 4.4 Verify Configuration
```bash
# Check for placeholder values
grep "CHANGE_ME" .env
# Should return nothing if properly configured
```

---

## Step 5: Train ML Models

The ML service requires trained models for spam detection.

### 5.1 Build ML Service First
```bash
docker compose -f docker-compose.prod.yml build ml-service
```

### 5.2 Run Training
```bash
# Start ML service container temporarily
docker compose -f docker-compose.prod.yml run --rm ml-service bash

# Inside container, train the model
cd /app/model
python train.py --unified

# Exit container
exit
```

### 5.3 Verify Model Files
The training creates these files in `/app/model/`:
- `spam_classifier.pkl` - Trained classifier
- `vectorizer.pkl` - Text vectorizer

---

## Step 6: Deploy with Docker

### 6.1 Build All Services
```bash
docker compose -f docker-compose.prod.yml build
```

### 6.2 Start Services
```bash
docker compose -f docker-compose.prod.yml up -d
```

### 6.3 Check Service Status
```bash
docker compose -f docker-compose.prod.yml ps
```

Expected output:
```
NAME                    STATUS              PORTS
ai-shield-backend       Up (healthy)        3000/tcp
ai-shield-gateway       Up                  0.0.0.0:80->8000/tcp, 0.0.0.0:443->8443/tcp
ai-shield-ml-service    Up (healthy)        8000/tcp
ai-shield-postgres      Up (healthy)        5432/tcp
ai-shield-redis         Up (healthy)        6379/tcp
ai-shield-worker        Up
```

### 6.4 View Logs
```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f ml-service
```

---

## Step 7: Setup SSL Certificate

### 7.1 Configure DNS
In your domain registrar, add these DNS records:

| Type | Name | Value |
|------|------|-------|
| A | @ | YOUR_DROPLET_IP |
| A | www | YOUR_DROPLET_IP |

Wait 5-30 minutes for DNS propagation.

### 7.2 Verify DNS
```bash
dig +short yourdomain.com
# Should return your droplet IP
```

### 7.3 Generate SSL Certificate
```bash
# Make script executable
chmod +x setup-ssl.sh

# Run SSL setup
./setup-ssl.sh yourdomain.com your-email@example.com
```

### 7.4 Restart Services
```bash
docker compose -f docker-compose.prod.yml up -d
```

---

## Step 8: Verify Deployment

### 8.1 Test Health Endpoint
```bash
# HTTP
curl http://YOUR_DROPLET_IP/health

# HTTPS (after SSL setup)
curl https://yourdomain.com/health
```

Expected response:
```json
{
  "status": "success",
  "message": "Server is running",
  "timestamp": "2026-01-25T07:00:00.000Z",
  "services": {
    "api": "healthy",
    "redis": "healthy"
  }
}
```

### 8.2 Test API Info
```bash
curl https://yourdomain.com/api/v1
```

### 8.3 Test Message Scanning
```bash
curl -X POST https://yourdomain.com/api/v1/messages/scan-text \
  -H "Content-Type: application/json" \
  -d '{"message": "Congratulations! You won $5000!"}'
```

### 8.4 Test Phishing Scanning
```bash
curl -X POST https://yourdomain.com/api/v1/phishing/scan-text \
  -H "Content-Type: application/json" \
  -d '{"text": "Click here to verify your bank account: http://fake-bank.com"}'
```

### 8.5 Test ML Service Directly
```bash
# Inside the server
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"message": "You won a free iPhone!"}'
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs SERVICE_NAME

# Restart specific service
docker compose -f docker-compose.prod.yml restart SERVICE_NAME
```

### Database Connection Issues

```bash
# Check PostgreSQL
docker exec -it ai-shield-postgres psql -U aishield -d aishield -c "\dt"

# Reset database (WARNING: deletes all data)
docker compose -f docker-compose.prod.yml down -v
docker compose -f docker-compose.prod.yml up -d
```

### ML Model Not Loaded

```bash
# Check ML service logs
docker logs ai-shield-ml-service

# Re-train model
docker exec -it ai-shield-ml-service bash
cd /app/model
python train.py --unified
exit
docker restart ai-shield-ml-service
```

### Redis Connection Issues

```bash
# Check Redis
docker exec -it ai-shield-redis redis-cli ping
# Should return: PONG
```

### Kong Gateway Issues

```bash
# Check Kong config
docker logs ai-shield-gateway

# Validate Kong config
docker exec ai-shield-gateway kong config parse /etc/kong/kong.yml
```

### SSL Certificate Issues

```bash
# Check certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Renew certificate
certbot renew --dry-run
```

### Out of Memory

```bash
# Check memory usage
docker stats

# Increase swap (if needed)
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

---

## Maintenance

### Update Application

```bash
cd /root/ai-anti-spam-shield-crm/deploy/digitalocean

# Pull latest code
git pull origin main

# Rebuild and restart
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### Backup Database

```bash
# Create backup
docker exec ai-shield-postgres pg_dump -U aishield aishield > backup_$(date +%Y%m%d).sql

# Restore backup
docker exec -i ai-shield-postgres psql -U aishield aishield < backup_20260125.sql
```

### View Resource Usage

```bash
# Container stats
docker stats

# Disk usage
df -h

# Memory usage
free -m
```

### Renew SSL Certificate

Certificates auto-renew via cron. Manual renewal:
```bash
certbot renew
docker compose -f docker-compose.prod.yml restart gateway
```

### Clean Up Docker

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes (WARNING: may delete data)
docker volume prune
```

---

## Configuration Files Reference

### docker-compose.prod.yml

| Service | Image | Memory Limit | Health Check |
|---------|-------|--------------|--------------|
| gateway | kong/kong:3.4 | 256M | - |
| backend | custom build | 512M | curl /health |
| worker | custom build | 384M | - |
| ml-service | custom build | 1.5G | curl /health |
| postgres | postgres:15-alpine | 512M | pg_isready |
| redis | redis:7-alpine | 160M | redis-cli ping |

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| DB_PASSWORD | PostgreSQL password | (generated) |
| JWT_SECRET | JWT signing key | (generated) |
| JWT_REFRESH_SECRET | Refresh token key | (generated) |
| ENCRYPTION_KEY | Data encryption key | (generated) |
| DATABASE_URL | Full database URL | postgresql://... |
| REDIS_URL | Redis connection | redis://redis:6379 |
| AI_SERVICE_URL | ML service URL | http://ml-service:8000 |

### Ports

| Port | Service | Protocol |
|------|---------|----------|
| 80 | Kong Gateway | HTTP |
| 443 | Kong Gateway | HTTPS |
| 3000 | Backend (internal) | HTTP |
| 8000 | ML Service (internal) | HTTP |
| 5432 | PostgreSQL (internal) | TCP |
| 6379 | Redis (internal) | TCP |

---

## API Endpoints Summary

### Public Endpoints (No Auth Required)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1` | GET | API info |
| `/api/v1/phishing/scan-text` | POST | Scan text for phishing |
| `/api/v1/phishing/scan-url` | POST | Scan URL for phishing |
| `/api/v1/phishing/batch-scan` | POST | Batch scan |

### Protected Endpoints (Auth Required)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/messages/scan-text` | POST | Scan message for spam |
| `/api/v1/messages/scan-voice` | POST | Scan voice for spam |
| `/api/v1/messages/history` | GET | Get scan history |
| `/api/v1/messages/statistics` | GET | Get statistics |
| `/api/v1/users/register` | POST | Register user |
| `/api/v1/users/login` | POST | Login user |

---

## Cost Estimation

### DigitalOcean Droplet: $24/month

| Resource | Specification |
|----------|--------------|
| vCPUs | 2 |
| RAM | 4 GB |
| Storage | 80 GB SSD |
| Transfer | 4 TB |

### With GitHub Student Pack: $200 credit = ~8 months free

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/YOUR_USERNAME/ai-anti-spam-shield-crm/issues
- Documentation: See `docs/` folder in repository

---

*Last updated: January 2026*
