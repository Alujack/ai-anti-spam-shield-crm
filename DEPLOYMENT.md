# AI Anti-Spam Shield - DigitalOcean Deployment Guide

This guide walks you through deploying the AI Anti-Spam Shield to DigitalOcean.

## Prerequisites

- DigitalOcean account
- Domain name (optional but recommended for SSL)
- Git installed locally

## Recommended Droplet Specifications

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 vCPUs | 4 vCPUs |
| RAM | 4 GB | 8 GB |
| Storage | 50 GB SSD | 100 GB SSD |
| Region | Any | Closest to users |

**Recommended Droplet:** Basic Droplet with 4GB RAM ($24/month) or 8GB RAM ($48/month)

## Step-by-Step Deployment

### Step 1: Create DigitalOcean Droplet

1. Log in to [DigitalOcean](https://cloud.digitalocean.com)
2. Click **Create** → **Droplets**
3. Choose:
   - **Image:** Ubuntu 22.04 LTS
   - **Plan:** Basic (4GB RAM recommended)
   - **Datacenter:** Choose closest to your users
   - **Authentication:** SSH keys (recommended) or Password
   - **Hostname:** `ai-anti-spam-shield`
4. Click **Create Droplet**
5. Note the IP address

### Step 2: Connect to Your Droplet

```bash
ssh root@YOUR_DROPLET_IP
```

### Step 3: Initial Server Setup

```bash
# Download deployment script
curl -O https://raw.githubusercontent.com/YOUR_REPO/main/deploy.sh
chmod +x deploy.sh

# Run initial setup
./deploy.sh setup
```

This will:
- Update system packages
- Install Docker and Docker Compose
- Configure firewall (UFW)
- Set up fail2ban for security
- Create swap file (for smaller droplets)

### Step 4: Upload Project Files

**Option A: Using Git (Recommended)**
```bash
cd /opt/ai-anti-spam-shield
git clone https://github.com/YOUR_REPO/ai-anti-spam-shield-crm.git .
```

**Option B: Using SCP**
```bash
# From your local machine
scp -r ./ai-anti-spam-shield-crm/* root@YOUR_DROPLET_IP:/opt/ai-anti-spam-shield/
```

### Step 5: Configure Environment Variables

```bash
cd /opt/ai-anti-spam-shield

# Generate secure secrets
./deploy.sh secrets

# Copy and configure environment file
cp .env.production .env
nano .env
```

Update these values in `.env`:
```env
# Required - Update these with generated secrets
DB_PASSWORD=<generated_password>
JWT_SECRET=<generated_secret>
JWT_REFRESH_SECRET=<generated_secret>
ENCRYPTION_KEY=<generated_key>
GRAFANA_PASSWORD=<generated_password>

# Required - Update with your domain (or IP)
DOMAIN=your-domain.com

# Required for SSL
LETSENCRYPT_EMAIL=your-email@example.com

# Update CORS for production
CORS_ORIGIN=https://your-domain.com
```

### Step 6: Deploy Application

```bash
./deploy.sh deploy
```

This will:
- Build all Docker images
- Start all services
- Run database migrations
- Display service status

### Step 7: Verify Deployment

```bash
# Check all services are running
./deploy.sh status

# Test API health endpoint
curl http://YOUR_DROPLET_IP/health
```

### Step 8: Setup SSL (Optional but Recommended)

If you have a domain pointing to your droplet:

```bash
./deploy.sh ssl your-domain.com your-email@example.com
```

### Step 9: Configure DNS

Point your domain to the droplet IP:
```
Type: A
Name: @
Value: YOUR_DROPLET_IP
TTL: 300
```

## Service Architecture

```
                    ┌─────────────┐
                    │   Internet  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    Nginx    │ :80/:443
                    │  (SSL/Proxy)│
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    Kong     │ :8000
                    │  (Gateway)  │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐   ┌──────▼──────┐  ┌──────▼──────┐
    │  Backend  │   │  ML Service │  │   Workers   │
    │  (Node)   │   │  (FastAPI)  │  │  (Bull MQ)  │
    └─────┬─────┘   └─────────────┘  └──────┬──────┘
          │                                  │
          └──────────┬───────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
  ┌─────▼─────┐ ┌────▼────┐ ┌─────▼─────┐
  │ PostgreSQL│ │  Redis  │ │ Prometheus│
  │           │ │         │ │ /Grafana  │
  └───────────┘ └─────────┘ └───────────┘
```

## Management Commands

```bash
# View logs
./deploy.sh logs              # All services
./deploy.sh logs backend      # Specific service

# Check status
./deploy.sh status

# Update application
./deploy.sh update

# Backup database
./deploy.sh backup

# Restore database
./deploy.sh restore /opt/backups/backup_file.sql.gz

# Stop all services
./deploy.sh stop

# Clean up Docker resources
./deploy.sh cleanup
```

## API Endpoints

After deployment, your API will be available at:

| Endpoint | Description |
|----------|-------------|
| `https://your-domain.com/health` | Health check |
| `https://your-domain.com/api/v1/auth/*` | Authentication |
| `https://your-domain.com/api/v1/scan/*` | Spam scanning |
| `https://your-domain.com/api/v1/reports/*` | Reports |
| `https://your-domain.com/grafana` | Monitoring dashboard |

## Monitoring

### Grafana Dashboard

Access Grafana at `https://your-domain.com/grafana`
- Default username: `admin`
- Password: Set in `.env` file

### Useful Commands

```bash
# View real-time logs
docker-compose -f docker-compose.prod.yml logs -f

# Check container resources
docker stats

# Check disk usage
df -h
docker system df
```

## Troubleshooting

### Services not starting
```bash
# Check logs
./deploy.sh logs

# Check specific service
docker-compose -f docker-compose.prod.yml logs backend
```

### Database connection issues
```bash
# Check PostgreSQL logs
docker-compose -f docker-compose.prod.yml logs postgres

# Connect to database
docker-compose -f docker-compose.prod.yml exec postgres psql -U aishield aishield
```

### Out of memory
```bash
# Check memory usage
free -m

# Increase swap
fallocate -l 4G /swapfile2
chmod 600 /swapfile2
mkswap /swapfile2
swapon /swapfile2
```

### SSL certificate issues
```bash
# Renew certificate manually
docker-compose -f docker-compose.prod.yml run --rm certbot renew
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

## Security Checklist

- [ ] Changed all default passwords
- [ ] Generated secure JWT secrets
- [ ] SSL certificate installed
- [ ] Firewall enabled (only ports 22, 80, 443 open)
- [ ] fail2ban configured
- [ ] Regular backups scheduled
- [ ] CORS configured for production domains only

## Backup Strategy

### Automated Backups

Add to crontab (`crontab -e`):
```bash
# Daily backup at 2 AM
0 2 * * * /opt/ai-anti-spam-shield/deploy.sh backup >> /var/log/backup.log 2>&1
```

### Manual Backup
```bash
./deploy.sh backup
```

Backups are stored in `/opt/backups/` and automatically rotated (keeps last 7).

## Scaling

### Horizontal Scaling (Multiple Droplets)

For high traffic, consider:
1. **Load Balancer:** Use DigitalOcean Load Balancer
2. **Managed Database:** Use DigitalOcean Managed PostgreSQL
3. **Managed Redis:** Use DigitalOcean Managed Redis

### Vertical Scaling

Resize your droplet:
1. Power off the droplet
2. Resize to larger plan
3. Power on

## Cost Estimation

| Resource | Monthly Cost |
|----------|-------------|
| Droplet (4GB) | $24 |
| Droplet (8GB) | $48 |
| Managed DB (optional) | $15+ |
| Load Balancer (optional) | $12 |
| Backups (20%) | $5-10 |

**Recommended starting cost:** $24-48/month

## Support

For issues:
1. Check logs: `./deploy.sh logs`
2. Check status: `./deploy.sh status`
3. Review this documentation
4. Open an issue on GitHub
