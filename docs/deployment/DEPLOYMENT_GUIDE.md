# Deployment Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Development Deployment](#development-deployment)
4. [Production Deployment](#production-deployment)
5. [Docker Deployment](#docker-deployment)
6. [Configuration](#configuration)
7. [Health Checks](#health-checks)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Software | Minimum Version | Recommended |
|----------|----------------|-------------|
| Node.js | 18.0.0 | 20.x LTS |
| Python | 3.9.0 | 3.11.x |
| PostgreSQL | 14.0 | 15.x |
| Flutter | 3.9.0 | Latest stable |
| Yarn | 1.22.0 | Latest |
| Docker | 20.10.0 | Latest |

### System Requirements

**Development Environment:**
- RAM: 8GB minimum, 16GB recommended
- Storage: 10GB free space
- OS: macOS, Linux, or Windows 10/11

**Production Environment:**
- RAM: 4GB minimum (Backend + AI Service)
- vCPU: 2 cores minimum, 4 recommended
- Storage: 20GB SSD
- OS: Ubuntu 20.04+ or similar Linux distribution

---

## Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd ai-anti-spam-shield
```

### 2. Backend Environment

Create `/ai-anti-spam-shield-backend/.env`:

```env
# Server
NODE_ENV=development
PORT=3000

# Database
DATABASE_URL="postgresql://user:password@localhost:5432/antispam_db"

# JWT
JWT_SECRET=your-super-secret-key-min-32-chars
JWT_EXPIRES_IN=7d
JWT_REFRESH_SECRET=your-refresh-secret-key-min-32-chars
JWT_REFRESH_EXPIRES_IN=30d

# AI Service
ML_SERVICE_URL=http://localhost:8000

# Security
BCRYPT_SALT_ROUNDS=12
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=100
```

### 3. AI Service Environment

Create `/ai-anti-spam-shield-service-model/.env`:

```env
# Server
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development

# Model
MODEL_PATH=app/model/model_files
CONFIDENCE_THRESHOLD=0.5

# Logging
LOG_LEVEL=INFO
```

---

## Development Deployment

### Step 1: Database Setup

```bash
# Create database
createdb antispam_db

# Navigate to backend
cd ai-anti-spam-shield-backend

# Install dependencies
yarn install

# Run migrations
yarn prisma:migrate

# Generate Prisma client
yarn prisma:generate
```

### Step 2: Train ML Model

```bash
# Navigate to AI service
cd ai-anti-spam-shield-service-model

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r app/requirements.txt

# Prepare dataset
python datasets/prepare_data.py

# Train model
python app/model/train.py
```

### Step 3: Start Services

**Terminal 1 - AI Service:**

```bash
cd ai-anti-spam-shield-service-model/app
python main.py
# Running on http://0.0.0.0:8000
```

**Terminal 2 - Backend API:**

```bash
cd ai-anti-spam-shield-backend
yarn dev
# Running on http://localhost:3000
```

**Terminal 3 - Mobile App:**

```bash
cd ai_anti_spam_shield_mobile
flutter pub get
flutter run
```

### Verify Installation

```bash
# Check AI Service
curl http://localhost:8000/health

# Check Backend
curl http://localhost:3000/api/v1/health

# Test prediction
curl -X POST http://localhost:3000/api/v1/messages/scan-text \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message"}'
```

---

## Production Deployment

### Option 1: PM2 (Recommended for VPS)

#### Install PM2

```bash
npm install -g pm2
```

#### Configure PM2

Create `ecosystem.config.js` in project root:

```javascript
module.exports = {
  apps: [
    {
      name: 'backend-api',
      cwd: './ai-anti-spam-shield-backend',
      script: 'src/app.js',
      instances: 'max',
      exec_mode: 'cluster',
      env: {
        NODE_ENV: 'production',
        PORT: 3000
      }
    },
    {
      name: 'ai-service',
      cwd: './ai-anti-spam-shield-service-model/app',
      script: 'main.py',
      interpreter: 'python3',
      env: {
        ENVIRONMENT: 'production',
        PORT: 8000
      }
    }
  ]
};
```

#### Start Services

```bash
# Start all services
pm2 start ecosystem.config.js

# Save process list
pm2 save

# Setup startup script
pm2 startup
```

#### PM2 Commands

```bash
pm2 status          # Check status
pm2 logs            # View logs
pm2 restart all     # Restart all
pm2 stop all        # Stop all
pm2 delete all      # Remove all
```

### Option 2: Systemd Services

#### Backend Service

Create `/etc/systemd/system/antispam-backend.service`:

```ini
[Unit]
Description=AI Anti-Spam Shield Backend
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/ai-anti-spam-shield/ai-anti-spam-shield-backend
ExecStart=/usr/bin/node src/app.js
Restart=on-failure
RestartSec=10
Environment=NODE_ENV=production
Environment=PORT=3000

[Install]
WantedBy=multi-user.target
```

#### AI Service

Create `/etc/systemd/system/antispam-ai.service`:

```ini
[Unit]
Description=AI Anti-Spam Shield ML Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/ai-anti-spam-shield/ai-anti-spam-shield-service-model/app
ExecStart=/usr/bin/python3 main.py
Restart=on-failure
RestartSec=10
Environment=ENVIRONMENT=production
Environment=PORT=8000

[Install]
WantedBy=multi-user.target
```

#### Enable Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable antispam-backend antispam-ai
sudo systemctl start antispam-backend antispam-ai
```

---

## Docker Deployment

### Build Images

```bash
# Build backend
cd ai-anti-spam-shield-backend
docker build -t antispam-backend:latest .

# Build AI service
cd ../ai-anti-spam-shield-service-model
docker build -t antispam-ai:latest .
```

### Docker Compose

Create `docker-compose.yml` in project root:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: antispam
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: antispam_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U antispam"]
      interval: 10s
      timeout: 5s
      retries: 5

  ai-service:
    build: ./ai-anti-spam-shield-service-model
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - PORT=8000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build: ./ai-anti-spam-shield-backend
    ports:
      - "3000:3000"
    depends_on:
      postgres:
        condition: service_healthy
      ai-service:
        condition: service_healthy
    environment:
      - NODE_ENV=production
      - PORT=3000
      - DATABASE_URL=postgresql://antispam:${DB_PASSWORD}@postgres:5432/antispam_db
      - ML_SERVICE_URL=http://ai-service:8000
      - JWT_SECRET=${JWT_SECRET}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
```

### Deploy with Docker Compose

```bash
# Create .env file with secrets
echo "DB_PASSWORD=your-secure-password" > .env
echo "JWT_SECRET=your-jwt-secret-min-32-chars" >> .env

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Configuration

### Environment Variables Reference

| Variable | Service | Description | Required |
|----------|---------|-------------|----------|
| NODE_ENV | Backend | Environment mode | Yes |
| PORT | Both | Service port | Yes |
| DATABASE_URL | Backend | PostgreSQL connection string | Yes |
| JWT_SECRET | Backend | JWT signing key (min 32 chars) | Yes |
| JWT_EXPIRES_IN | Backend | Token expiration | No |
| ML_SERVICE_URL | Backend | AI service URL | Yes |
| BCRYPT_SALT_ROUNDS | Backend | Password hashing rounds | No |
| MODEL_PATH | AI | Path to trained models | Yes |
| LOG_LEVEL | Both | Logging verbosity | No |

### Nginx Reverse Proxy

Create `/etc/nginx/sites-available/antispam`:

```nginx
upstream backend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name api.antispam.example.com;

    location / {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### SSL with Certbot

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.antispam.example.com
```

---

## Health Checks

### Endpoints

| Service | Endpoint | Expected Response |
|---------|----------|-------------------|
| Backend | GET /api/v1/health | `{"status": "ok"}` |
| AI Service | GET /health | `{"status": "healthy"}` |

### Monitoring Script

```bash
#!/bin/bash
# health-check.sh

BACKEND_URL="http://localhost:3000/api/v1/health"
AI_URL="http://localhost:8000/health"

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
check_service $AI_URL "AI Service"

echo "All services are healthy"
```

---

## Troubleshooting

### Common Issues

#### Database Connection Failed

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify connection string
psql "postgresql://user:password@localhost:5432/antispam_db"
```

#### AI Service Not Responding

```bash
# Check if model files exist
ls -la ai-anti-spam-shield-service-model/app/model/model_files/

# Retrain model if missing
python datasets/prepare_data.py
python app/model/train.py
```

#### Port Already in Use

```bash
# Find process using port
lsof -i :3000
lsof -i :8000

# Kill process
kill -9 <PID>
```

#### Permission Denied

```bash
# Fix file permissions
sudo chown -R $USER:$USER /opt/ai-anti-spam-shield
chmod -R 755 /opt/ai-anti-spam-shield
```

### Log Locations

| Service | Log Location |
|---------|--------------|
| Backend (PM2) | `~/.pm2/logs/backend-api-*.log` |
| AI Service (PM2) | `~/.pm2/logs/ai-service-*.log` |
| Docker | `docker-compose logs <service>` |
| Systemd | `journalctl -u antispam-backend` |

### Performance Tuning

```bash
# Increase Node.js memory limit
export NODE_OPTIONS="--max-old-space-size=4096"

# Increase Python process workers
uvicorn main:app --workers 4
```
