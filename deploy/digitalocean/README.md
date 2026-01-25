# DigitalOcean Deployment Guide

## Prerequisites
- DigitalOcean account with GitHub Student Pack ($200 credit)
- Domain name (optional but recommended)
- SSH key pair

## Step 1: Create Droplet

1. Go to [DigitalOcean Console](https://cloud.digitalocean.com/)
2. Click **Create** → **Droplets**
3. Configure:
   - **Region**: Choose closest to your users (Singapore for Cambodia)
   - **Image**: Ubuntu 22.04 LTS
   - **Size**: Basic → Regular → **$24/mo** (4GB RAM, 2 vCPU)
   - **Authentication**: SSH Key (recommended)
   - **Hostname**: `ai-shield-prod`

4. Click **Create Droplet**
5. Note down the IP address

## Step 2: Initial Server Setup

SSH into your droplet:
```bash
ssh root@YOUR_DROPLET_IP
```

Run the setup script:
```bash
curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/deploy/digitalocean/setup-droplet.sh | bash
```

Or manually:
```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
usermod -aG docker $USER

# Install Docker Compose
apt install -y docker-compose-plugin

# Configure firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Log out and back in
exit
```

## Step 3: Deploy Application

```bash
# SSH back in
ssh root@YOUR_DROPLET_IP

# Clone repository
git clone https://github.com/YOUR_USERNAME/ai-anti-spam-shield-crm.git
cd ai-anti-spam-shield-crm

# Create environment file
cp .env.production .env

# Generate secure secrets
echo "DB_PASSWORD=$(openssl rand -base64 32)" >> .env
echo "JWT_SECRET=$(openssl rand -base64 64)" >> .env
echo "JWT_REFRESH_SECRET=$(openssl rand -base64 64)" >> .env
echo "ENCRYPTION_KEY=$(openssl rand -base64 32)" >> .env

# Edit .env to update domain and other settings
nano .env

# Deploy
chmod +x deploy/digitalocean/deploy.sh
./deploy/digitalocean/deploy.sh
```

## Step 4: Verify Deployment

```bash
# Check container status
docker compose -f docker-compose.prod.yml ps

# Check logs
docker compose -f docker-compose.prod.yml logs -f

# Test health endpoint
curl http://localhost/health
```

## Step 5: Setup Domain & SSL

### 5.1 Configure DNS

1. In DigitalOcean, go to **Networking** → **Domains**
2. Add your domain (e.g., `aiscamshield.codes`)
3. Create these DNS records:
   | Type | Hostname | Value |
   |------|----------|-------|
   | A | @ | YOUR_DROPLET_IP |
   | A | www | YOUR_DROPLET_IP |

4. Wait for DNS propagation (5-30 minutes)
5. Verify: `dig +short aiscamshield.codes`

### 5.2 Setup SSL with Let's Encrypt

```bash
# SSH into your droplet
ssh root@YOUR_DROPLET_IP

# Navigate to deploy directory
cd /root/ai-anti-spam-shield-crm/deploy/digitalocean

# Pull latest changes (includes SSL script)
git pull origin main

# Make SSL script executable
chmod +x setup-ssl.sh

# Run SSL setup (replace with your domain and email)
./setup-ssl.sh aiscamshield.codes your@email.com

# Restart services with SSL
docker compose -f docker-compose.prod.yml up -d
```

### 5.3 Verify SSL

```bash
# Test HTTPS endpoint
curl https://aiscamshield.codes/health

# Check certificate
openssl s_client -connect aiscamshield.codes:443 -servername aiscamshield.codes
```

### 5.4 Certificate Renewal

Certificates auto-renew via cron job. To manually renew:
```bash
certbot renew --dry-run  # Test renewal
certbot renew            # Actually renew
```

## Memory Usage Estimate

| Service | Memory Limit |
|---------|--------------|
| Kong Gateway | 128 MB |
| Backend | 512 MB |
| Worker | 384 MB |
| ML Service | 1024 MB |
| PostgreSQL | 512 MB |
| Redis | 160 MB |
| **Total** | **~2.7 GB** |

Leaves ~1.3 GB for OS and buffer on a 4GB droplet.

## Useful Commands

```bash
# View all logs
docker compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker compose -f docker-compose.prod.yml logs -f backend

# Restart a service
docker compose -f docker-compose.prod.yml restart backend

# Stop all services
docker compose -f docker-compose.prod.yml down

# Update and redeploy
git pull && ./deploy/digitalocean/deploy.sh

# Check disk usage
df -h

# Check memory usage
htop

# Clean up Docker resources
docker system prune -a
```

## Cost Breakdown

| Resource | Monthly | Yearly |
|----------|---------|--------|
| Droplet (4GB) | $24 | $288 |
| **With $200 credit** | - | **$88 out of pocket** |

## Troubleshooting

### Services won't start
```bash
# Check which service is failing
docker compose -f docker-compose.prod.yml ps

# Check specific service logs
docker compose -f docker-compose.prod.yml logs ml-service
```

### Out of memory
```bash
# Check memory usage
free -h

# Reduce Redis memory in docker-compose.prod.yml
# Or upgrade to $48/mo droplet
```

### Database connection issues
```bash
# Check if postgres is healthy
docker compose -f docker-compose.prod.yml exec postgres pg_isready

# View postgres logs
docker compose -f docker-compose.prod.yml logs postgres
```
