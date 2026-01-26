# AI Anti-Spam Shield - DigitalOcean Deployment

> For comprehensive documentation, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

## Quick Start

### 1. Create Droplet
- **Image**: Ubuntu 24.04 LTS
- **Size**: $24/month (2 vCPU, 4GB RAM)
- **Region**: Singapore (SGP1)

### 2. Server Setup
```bash
ssh root@YOUR_DROPLET_IP

# Install Docker
curl -fsSL https://get.docker.com | sh
apt install -y docker-compose-plugin git curl certbot

# Configure firewall
ufw allow OpenSSH && ufw allow 80/tcp && ufw allow 443/tcp && ufw enable
```

### 3. Deploy
```bash
# Clone and configure
git clone https://github.com/YOUR_USERNAME/ai-anti-spam-shield-crm.git
cd ai-anti-spam-shield-crm/deploy/digitalocean
cp .env.example .env

# Generate secrets
cat >> .env << EOF
DB_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 64)
JWT_REFRESH_SECRET=$(openssl rand -base64 64)
ENCRYPTION_KEY=$(openssl rand -base64 32)
EOF

# Train ML model
docker compose -f docker-compose.prod.yml build ml-service
docker compose -f docker-compose.prod.yml run --rm ml-service bash -c "cd /app/model && python train.py --unified"

# Deploy
docker compose -f docker-compose.prod.yml up -d
```

### 4. Setup SSL
```bash
chmod +x setup-ssl.sh
./setup-ssl.sh yourdomain.com your@email.com
docker compose -f docker-compose.prod.yml up -d
```

### 5. Verify
```bash
curl https://yourdomain.com/health
```

---

## Services

| Service | Port | Memory | Health Check |
|---------|------|--------|--------------|
| Kong Gateway | 80, 443 | 256M | - |
| Backend | 3000 | 512M | `/health` |
| Worker | - | 384M | - |
| ML Service | 8000 | 1.5G | `/health` |
| PostgreSQL | 5432 | 512M | `pg_isready` |
| Redis | 6379 | 160M | `redis-cli ping` |

## API Endpoints

### Scanning Systems
| System | Endpoint | ML Endpoint |
|--------|----------|-------------|
| Message Scan | `POST /api/v1/messages/scan-text` | `/predict` |
| Voice Scan | `POST /api/v1/messages/scan-voice` | `/predict-voice` |
| Phishing Scan | `POST /api/v1/phishing/scan-text` | `/predict-phishing` |

### Test Commands
```bash
# Health check
curl https://yourdomain.com/health

# Spam detection
curl -X POST https://yourdomain.com/api/v1/messages/scan-text \
  -H "Content-Type: application/json" \
  -d '{"message": "You won $5000!"}'

# Phishing detection
curl -X POST https://yourdomain.com/api/v1/phishing/scan-text \
  -H "Content-Type: application/json" \
  -d '{"text": "Click here to verify your account"}'
```

## Common Commands

```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f

# Restart service
docker compose -f docker-compose.prod.yml restart backend

# Update deployment
git pull origin main
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Check status
docker compose -f docker-compose.prod.yml ps
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| ML model not loaded | `docker exec -it ai-shield-ml-service bash -c "cd /app/model && python train.py --unified"` then `docker restart ai-shield-ml-service` |
| Database error | Check `docker logs ai-shield-postgres` |
| Out of memory | Check `docker stats`, consider upgrading droplet |
| SSL error | Run `certbot renew` and restart gateway |

## Cost

| With GitHub Student Pack ($200 credit) |
|----------------------------------------|
| ~8 months free on $24/month droplet |

---

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.
