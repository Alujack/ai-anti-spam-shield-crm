# Deployment Guide

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Development Deployment](#development-deployment)
5. [Production Deployment](#production-deployment)
6. [Docker Deployment](#docker-deployment)
7. [Configuration Reference](#configuration-reference)
8. [Health Checks](#health-checks)
9. [Monitoring](#monitoring)
10. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

AI Anti-Spam Shield uses a distributed microservices architecture with the following components:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Kong API Gateway                         │
│                    (Rate Limiting, CORS, Routing)               │
│                         :8080 (proxy)                           │
└─────────────────────────────┬───────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│    Backend    │    │   ML Service  │    │   Workers     │
│   (Node.js)   │◄──►│   (FastAPI)   │    │ (Text/Voice/  │
│    :3000      │    │    :8000      │    │     URL)      │
└───────┬───────┘    └───────────────┘    └───────┬───────┘
        │                                         │
        │            ┌───────────────┐            │
        └───────────►│     Redis     │◄───────────┘
                     │  (Queue/Cache)│
                     │    :6379      │
                     └───────────────┘
                              │
                     ┌───────────────┐
                     │  PostgreSQL   │
                     │   (Database)  │
                     │    :5432      │
                     └───────────────┘
```

### Service Components

| Service | Technology | Port | Description |
|---------|------------|------|-------------|
| Gateway | Kong 3.4 | 8080 | API gateway with rate limiting and routing |
| Backend | Node.js/Express 5 | 3000 | Main REST API server |
| ML Service | Python/FastAPI | 8000 | AI spam detection models |
| Text Worker | Node.js | - | Processes text scan queue |
| Voice Worker | Node.js | - | Processes voice scan queue |
| URL Worker | Node.js | - | Processes URL scan queue |
| PostgreSQL | PostgreSQL 15 | 5432 | Primary database |
| Redis | Redis 7 | 6379 | Job queue and caching |

---

## Prerequisites

### Required Software

| Software | Minimum Version | Recommended |
|----------|-----------------|-------------|
| Docker | 20.10.0 | Latest |
| Docker Compose | 2.0.0 | Latest |
| Node.js | 18.0.0 | 20.x LTS |
| Python | 3.9.0 | 3.11.x |
| Yarn | 1.22.0 | Latest |

### System Requirements

**Development Environment:**
- RAM: 8GB minimum, 16GB recommended
- Storage: 10GB free space
- OS: macOS, Linux, or Windows 10/11 with WSL2

**Production Environment:**
- RAM: 8GB minimum (for all services)
- vCPU: 4 cores minimum
- Storage: 50GB SSD
- OS: Ubuntu 20.04+ or similar Linux distribution

---

## Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd ai-anti-spam-shield
```

### 2. Configure Environment Variables

Create `.env` file in project root:

```env
# Database
DB_PASSWORD=your-secure-db-password

# JWT Authentication
JWT_SECRET=your-super-secret-jwt-key-min-32-chars
JWT_REFRESH_SECRET=your-refresh-secret-key-min-32-chars

# Encryption
ENCRYPTION_KEY=your-32-byte-encryption-key-here

# Monitoring (optional)
GRAFANA_PASSWORD=admin
```

### 3. Backend Environment (for local development)

Create `/ai-anti-spam-shield-backend/.env`:

```env
# Server
NODE_ENV=development
PORT=3000
API_VERSION=v1

# Database
DATABASE_URL="postgresql://aishield:secretpassword@localhost:5432/aishield"

# Redis
REDIS_URL=redis://localhost:6379

# AI Service
AI_SERVICE_URL=http://localhost:8000

# JWT
JWT_SECRET=your-super-secret-jwt-key-min-32-chars
JWT_EXPIRES_IN=7d
JWT_REFRESH_SECRET=your-refresh-secret-key-min-32-chars
JWT_REFRESH_EXPIRES_IN=30d

# Security
ENCRYPTION_KEY=your-32-byte-encryption-key-here

# Logging
LOG_LEVEL=debug
```

---

## Development Deployment

### Option 1: Docker Compose (Recommended)

The easiest way to run the full stack locally:

```bash
# Start all services with development configuration
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or run in detached mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f ml-service
```

### Option 2: Local Development with Scripts

#### Step 1: Start PostgreSQL and Redis

```bash
# Using Docker for databases only
docker-compose up -d postgres redis
```

#### Step 2: Start ML Service

```bash
# Navigate to ML service directory
cd ai-anti-spam-shield-service-model

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.\.venv\Scripts\activate   # Windows

# Install dependencies
pip install -r app/requirements.txt

# Train models (first time only)
python app/model/train_unified_model.py

# Start service
cd app && python main.py
# Running on http://0.0.0.0:8000
```

Or use the startup script:

```bash
./model-startup.sh
```

#### Step 3: Start Backend

```bash
# Navigate to backend directory
cd ai-anti-spam-shield-backend

# Install dependencies
yarn install

# Generate Prisma client
yarn prisma:generate

# Run migrations
yarn prisma:migrate:deploy

# Start development server
yarn dev
# Running on http://localhost:3000
```

Or use the startup script:

```bash
./server-startup.sh
```

### Verify Installation

```bash
# Check Backend health
curl http://localhost:3000/health

# Check ML Service health
curl http://localhost:8000/health

# Check API documentation
open http://localhost:3000/api-docs
```

---

## Production Deployment

### Docker Compose Production

#### 1. Configure Production Environment

Create `.env` file with strong credentials:

```env
DB_PASSWORD=<generate-strong-password>
JWT_SECRET=<generate-32-char-secret>
JWT_REFRESH_SECRET=<generate-32-char-secret>
ENCRYPTION_KEY=<generate-32-byte-key>
GRAFANA_PASSWORD=<grafana-admin-password>
```

Generate secure secrets:

```bash
# Generate random secrets
openssl rand -base64 32
```

#### 2. Deploy Services

```bash
# Build and start all services
docker-compose up -d --build

# Verify all services are running
docker-compose ps

# Check service health
docker-compose exec backend curl http://localhost:3000/health
```

#### 3. Run Database Migrations

```bash
# Execute migrations inside container
docker-compose exec backend npx prisma migrate deploy
```

#### 4. Enable Monitoring (Optional)

```bash
# Start with monitoring profile
docker-compose --profile monitoring up -d

# Access Grafana
open http://localhost:3001
```

### Service Scaling

Scale workers horizontally for high load:

```bash
# Scale text workers
docker-compose up -d --scale text-worker=4

# Scale voice workers
docker-compose up -d --scale voice-worker=2
```

---

## Docker Deployment

### Container Architecture

| Container | Image | Build Context |
|-----------|-------|---------------|
| ai-shield-gateway | kong:3.4-alpine | ./gateway/kong |
| ai-shield-backend | Custom | ./ai-anti-spam-shield-backend |
| ai-shield-ml-service | Custom | ./ai-anti-spam-shield-service-model |
| ai-shield-text-worker | Custom | ./ai-anti-spam-shield-backend |
| ai-shield-voice-worker | Custom | ./ai-anti-spam-shield-backend |
| ai-shield-url-worker | Custom | ./ai-anti-spam-shield-backend |
| ai-shield-postgres | postgres:15-alpine | - |
| ai-shield-redis | redis:7-alpine | - |

### Build Individual Images

```bash
# Build backend image
docker build -t ai-shield-backend:latest ./ai-anti-spam-shield-backend

# Build ML service image
docker build -t ai-shield-ml-service:latest ./ai-anti-spam-shield-service-model
```

### Docker Compose Profiles

| Profile | Description |
|---------|-------------|
| default | Core services (backend, ml-service, postgres, redis, gateway) |
| monitoring | Adds Prometheus and Grafana |

```bash
# Run with monitoring
docker-compose --profile monitoring up -d
```

### Volume Management

| Volume | Purpose |
|--------|---------|
| postgres-data | PostgreSQL database files |
| redis-data | Redis persistence |
| ml-models | Trained ML model files |
| backend-logs | Application logs |
| prometheus-data | Metrics history |
| grafana-data | Dashboards and config |

```bash
# Backup volumes
docker run --rm -v ai-anti-spam-shield_postgres-data:/data -v $(pwd):/backup alpine tar cvf /backup/postgres-backup.tar /data

# List volumes
docker volume ls | grep ai-shield
```

---

## Configuration Reference

### Environment Variables

#### Backend Service

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| NODE_ENV | Yes | development | Environment mode |
| PORT | Yes | 3000 | Server port |
| DATABASE_URL | Yes | - | PostgreSQL connection string |
| REDIS_URL | Yes | - | Redis connection string |
| AI_SERVICE_URL | Yes | - | ML service URL |
| JWT_SECRET | Yes | - | JWT signing key (min 32 chars) |
| JWT_EXPIRES_IN | No | 7d | Access token expiry |
| JWT_REFRESH_SECRET | Yes | - | Refresh token key |
| JWT_REFRESH_EXPIRES_IN | No | 30d | Refresh token expiry |
| ENCRYPTION_KEY | Yes | - | Data encryption key |
| LOG_LEVEL | No | info | Logging verbosity |

#### ML Service

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| MODEL_DIR | Yes | /app/model | Model files directory |
| PYTHONUNBUFFERED | No | 1 | Disable output buffering |

#### Kong Gateway

Kong is configured declaratively via `gateway/kong/kong.yml`:

- Rate limiting: 100 requests/minute, 1000 requests/hour
- Request size limit: 10MB (for voice files)
- CORS: Configured with allowed origins
- Health checks: Active and passive monitoring

### Network Configuration

All services communicate over the `ai-shield-network` bridge network:

| Service | Internal Hostname | Port |
|---------|-------------------|------|
| Backend | backend | 3000 |
| ML Service | ml-service | 8000 |
| PostgreSQL | postgres | 5432 |
| Redis | redis | 6379 |

---

## Health Checks

### Endpoints

| Service | Endpoint | Expected Response |
|---------|----------|-------------------|
| Backend | GET /health | `{"status": "ok", ...}` |
| ML Service | GET /health | `{"status": "healthy", ...}` |
| Gateway | GET :8001/status | Kong admin status |

### Docker Health Check Configuration

All services include health checks with appropriate intervals:

```yaml
# Backend
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s

# ML Service
healthcheck:
  test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

### Health Check Script

```bash
#!/bin/bash
# health-check.sh

BACKEND_URL="http://localhost:3000/health"
ML_URL="http://localhost:8000/health"
GATEWAY_URL="http://localhost:8080/api/v1/health"

check_service() {
    response=$(curl -s -o /dev/null -w "%{http_code}" $1)
    if [ $response -eq 200 ]; then
        echo "✓ $2 is healthy"
    else
        echo "✗ $2 is down (HTTP $response)"
        exit 1
    fi
}

check_service $BACKEND_URL "Backend API"
check_service $ML_URL "ML Service"
check_service $GATEWAY_URL "API Gateway"

echo "All services are healthy"
```

---

## Monitoring

### Prometheus Metrics

Enable monitoring profile to collect metrics:

```bash
docker-compose --profile monitoring up -d
```

Access Prometheus: http://localhost:9090

**Scrape Targets:**
- Backend API: `/metrics`
- ML Service: `/metrics`
- Redis: port 6379
- Kong Gateway: port 8001

### Grafana Dashboards

Access Grafana: http://localhost:3001

Default credentials:
- Username: `admin`
- Password: Value of `GRAFANA_PASSWORD` env var (default: `admin`)

### Log Locations

| Service | Container Logs | Volume Logs |
|---------|----------------|-------------|
| Backend | `docker-compose logs backend` | `/app/logs` |
| ML Service | `docker-compose logs ml-service` | stdout |
| Workers | `docker-compose logs text-worker` | stdout |
| PostgreSQL | `docker-compose logs postgres` | - |
| Redis | `docker-compose logs redis` | - |

---

## Troubleshooting

### Common Issues

#### Services Not Starting

```bash
# Check container status
docker-compose ps

# View logs for specific service
docker-compose logs -f backend

# Check for port conflicts
lsof -i :3000
lsof -i :8000
```

#### Database Connection Failed

```bash
# Verify PostgreSQL is healthy
docker-compose exec postgres pg_isready -U aishield

# Check connection string
docker-compose exec backend printenv DATABASE_URL

# Access PostgreSQL directly
docker-compose exec postgres psql -U aishield -d aishield
```

#### ML Service Not Responding

```bash
# Check if models are trained
docker-compose exec ml-service ls -la /app/model/

# View ML service logs
docker-compose logs -f ml-service

# Restart ML service
docker-compose restart ml-service
```

#### Redis Connection Issues

```bash
# Check Redis health
docker-compose exec redis redis-cli ping

# View Redis info
docker-compose exec redis redis-cli info
```

#### Kong Gateway Issues

```bash
# Check Kong configuration
docker-compose exec gateway kong config parse /etc/kong/kong.yml

# View Kong admin API
curl http://localhost:8001/status

# Check routes
curl http://localhost:8001/routes
```

### Container Management

```bash
# Restart all services
docker-compose restart

# Rebuild and restart
docker-compose up -d --build

# Stop all services
docker-compose down

# Stop and remove volumes (CAUTION: deletes data)
docker-compose down -v

# Remove unused images
docker image prune -a
```

### Performance Tuning

#### Backend

```bash
# Increase Node.js memory (in docker-compose.yml)
environment:
  NODE_OPTIONS: "--max-old-space-size=4096"
```

#### ML Service

```bash
# Enable GPU support (uncomment in docker-compose.yml)
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

#### Worker Scaling

```bash
# Scale workers for higher throughput
docker-compose up -d --scale text-worker=4 --scale voice-worker=2 --scale url-worker=2
```

### Backup and Recovery

#### Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U aishield aishield > backup.sql

# Restore backup
cat backup.sql | docker-compose exec -T postgres psql -U aishield aishield
```

#### Volume Backup

```bash
# Backup all volumes
docker run --rm \
  -v ai-anti-spam-shield_postgres-data:/postgres \
  -v ai-anti-spam-shield_redis-data:/redis \
  -v ai-anti-spam-shield_ml-models:/models \
  -v $(pwd)/backups:/backup \
  alpine tar cvf /backup/volumes-$(date +%Y%m%d).tar /postgres /redis /models
```

---

## Quick Reference

### Development Commands

```bash
# Start development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Run backend tests
docker-compose exec backend yarn test

# Run database migrations
docker-compose exec backend yarn prisma:migrate:deploy

# Access Prisma Studio
docker-compose exec backend yarn prisma:studio
```

### Production Commands

```bash
# Deploy production
docker-compose up -d --build

# View all logs
docker-compose logs -f

# Check service health
docker-compose ps

# Scale workers
docker-compose up -d --scale text-worker=4

# Enable monitoring
docker-compose --profile monitoring up -d
```

### Useful Endpoints

| Endpoint | Description |
|----------|-------------|
| http://localhost:8080 | API Gateway (production entry point) |
| http://localhost:3000 | Backend direct access |
| http://localhost:3000/api-docs | Swagger API documentation |
| http://localhost:3000/health | Backend health check |
| http://localhost:8000 | ML Service direct access |
| http://localhost:8000/health | ML Service health check |
| http://localhost:8001 | Kong Admin API |
| http://localhost:9090 | Prometheus (with monitoring profile) |
| http://localhost:3001 | Grafana (with monitoring profile) |
