# 🚀 AI Anti-Scam Shield - Production Deployment Guide

**Version:** 1.0.0  
**Last Updated:** December 5, 2025  
**Status:** ✅ PRODUCTION READY

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running the Services](#running-the-services)
6. [Testing](#testing)
7. [Deployment](#deployment)
8. [API Documentation](#api-documentation)
9. [Troubleshooting](#troubleshooting)
10. [Security](#security)

---

## 🎯 Quick Start

### Development Mode (5 Minutes)

```bash
# 1. Clone the repository
git clone <repository-url>
cd ai-anti-spam-shield

# 2. Install dependencies
cd ai-anti-spam-shield-backend && yarn install
cd ../ai-anti-spam-shield-service-model && pip install -r app/requirements.txt
cd ../ai_anti_spam_shield_mobile && flutter pub get

# 3. Setup database
cd ../ai-anti-spam-shield-backend
createdb antispam_db
yarn prisma:migrate

# 4. Train AI model
cd ../ai-anti-spam-shield-service-model
python datasets/prepare_data.py
python app/model/train.py

# 5. Start services
# Terminal 1 - AI Service
cd ai-anti-spam-shield-service-model/app
python main.py

# Terminal 2 - Backend
cd ai-anti-spam-shield-backend
yarn dev

# Terminal 3 - Mobile App
cd ai_anti_spam_shield_mobile
flutter run
```

---

## 📦 Prerequisites

### Required Software

| Software | Version | Installation |
|----------|---------|--------------|
| Node.js | ≥ 18.0.0 | https://nodejs.org/ |
| Python | ≥ 3.9.0 | https://python.org/ |
| PostgreSQL | ≥ 14.0 | https://postgresql.org/ |
| Flutter | ≥ 3.9.0 | https://flutter.dev/ |
| Yarn | ≥ 1.22.0 | `npm install -g yarn` |

### Optional Tools

- **Docker** (≥ 20.10.0) - For containerized deployment
- **Git** (≥ 2.30.0) - Version control
- **Postman** - API testing
- **Android Studio** / **Xcode** - Mobile development

### System Requirements

**Development:**
- **RAM:** 8GB minimum, 16GB recommended
- **Storage:** 10GB free space
- **OS:** macOS, Linux, or Windows 10/11

**Production:**
- **RAM:** 4GB minimum (backend + AI service)
- **Storage:** 20GB free space
- **CPU:** 2 cores minimum, 4 cores recommended

---

## 🔧 Installation

### 1. Backend Setup

```bash
cd ai-anti-spam-shield-backend

# Install dependencies
yarn install

# or npm install

# Setup environment variables
cp .env.example .env

# Edit .env with your configuration
nano .env
```

**Required Environment Variables:**

```env
# Server Configuration
PORT=3000
NODE_ENV=development

# Database
DATABASE_URL="postgresql://username:password@localhost:5432/antispam_db"

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_EXPIRES_IN=7d
REFRESH_TOKEN_SECRET=your-super-secret-refresh-token-key
REFRESH_TOKEN_EXPIRES_IN=30d

# AI Service
AI_SERVICE_URL=http://localhost:8000
AI_API_KEY=optional-api-key-for-ai-service

# CORS
CORS_ORIGIN=http://localhost:3000,http://localhost:8080
```

### 2. Database Setup

```bash
# Create database
createdb antispam_db

# Generate Prisma Client
yarn prisma:generate

# Run migrations
yarn prisma:migrate

# Optional: Open Prisma Studio to view data
yarn prisma:studio
```

### 3. AI Service Setup

```bash
cd ai-anti-spam-shield-service-model

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r app/requirements.txt

# Prepare dataset
python datasets/prepare_data.py

# Train model
python app/model/train.py
```

### 4. Mobile App Setup

```bash
cd ai_anti_spam_shield_mobile

# Install dependencies
flutter pub get

# Update API base URL in lib/utils/constants.dart
# Android Emulator: http://10.0.2.2:3000/api/v1
# iOS Simulator: http://localhost:3000/api/v1
# Physical Device: http://YOUR_IP:3000/api/v1
```

---

## ⚙️ Configuration

### Backend Configuration

**File:** `ai-anti-spam-shield-backend/src/config/index.js`

```javascript
module.exports = {
  port: process.env.PORT || 3000,
  nodeEnv: process.env.NODE_ENV || 'development',
  jwt: {
    secret: process.env.JWT_SECRET,
    expiresIn: process.env.JWT_EXPIRES_IN || '7d',
    refreshSecret: process.env.REFRESH_TOKEN_SECRET,
    refreshExpiresIn: process.env.REFRESH_TOKEN_EXPIRES_IN || '30d'
  },
  ai: {
    serviceUrl: process.env.AI_SERVICE_URL || 'http://localhost:8000',
    apiKey: process.env.AI_API_KEY || null
  },
  cors: {
    origin: process.env.CORS_ORIGIN?.split(',') || ['*']
  }
};
```

### AI Service Configuration

**File:** `ai-anti-spam-shield-service-model/app/main.py`

```python
# Port configuration
PORT = int(os.getenv("PORT", 8000))

# CORS configuration (update for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Mobile App Configuration

**File:** `ai_anti_spam_shield_mobile/lib/utils/constants.dart`

```dart
class AppConstants {
  // Update based on platform and environment
  static const String baseUrl = 'http://10.0.2.2:3000/api/v1'; // Android Emulator
  // static const String baseUrl = 'http://localhost:3000/api/v1'; // iOS Simulator
  // static const String baseUrl = 'http://192.168.1.100:3000/api/v1'; // Physical Device
  
  static const int timeout = 30000; // 30 seconds
}
```

---

## 🚀 Running the Services

### Development Mode

**1. Start AI Service:**

```bash
cd ai-anti-spam-shield-service-model/app
source ../venv/bin/activate  # On Windows: ..\venv\Scripts\activate
python main.py
```

✅ Service will be available at: http://localhost:8000  
📖 API Documentation: http://localhost:8000/docs

**2. Start Backend:**

```bash
cd ai-anti-spam-shield-backend
yarn dev
```

✅ API will be available at: http://localhost:3000  
🏥 Health Check: http://localhost:3000/health

**3. Start Mobile App:**

```bash
cd ai_anti_spam_shield_mobile

# For Android
flutter run

# For iOS
flutter run

# For specific device
flutter devices
flutter run -d <device-id>
```

### Production Mode

**Using PM2 (Node.js):**

```bash
# Install PM2
npm install -g pm2

# Start backend
cd ai-anti-spam-shield-backend
pm2 start src/app.js --name anti-spam-backend

# Start AI service
cd ../ai-anti-spam-shield-service-model/app
pm2 start "python main.py" --name anti-spam-ai --interpreter python3

# View logs
pm2 logs

# Monitor
pm2 monit

# Save process list
pm2 save

# Setup startup script
pm2 startup
```

**Using Docker:**

See [Docker Deployment](#docker-deployment) section below.

---

## 🧪 Testing

### Backend API Testing

**Using cURL:**

```bash
# Health Check
curl http://localhost:3000/health

# Register User
curl -X POST http://localhost:3000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "name": "Test User"
  }'

# Login
curl -X POST http://localhost:3000/api/v1/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# Scan Text (save token from login response)
curl -X POST http://localhost:3000/api/v1/messages/scan-text \
  -H "Content-Type: application/json" \
  -d '{
    "message": "URGENT! You have won $1000. Click here to claim your prize!"
  }'
```

### AI Service Testing

```bash
# Health Check
curl http://localhost:8000/health

# Predict Spam
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Congratulations! You won a free iPhone. Click here!"
  }'

# Voice Prediction (with audio file)
curl -X POST http://localhost:8000/predict-voice \
  -F "audio=@/path/to/audio.wav"
```

### Mobile App Testing

```bash
# Run tests
flutter test

# Integration tests
flutter drive --target=test_driver/app.dart

# Build and test release version
flutter build apk --release
flutter build ios --release
```

---

## 🌐 Deployment

### Docker Deployment

**1. Create `docker-compose.yml` (Root directory):**

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: antispam-postgres
    environment:
      POSTGRES_DB: antispam_db
      POSTGRES_USER: antispam_user
      POSTGRES_PASSWORD: change-this-password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - antispam-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U antispam_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  ai-service:
    build:
      context: ./ai-anti-spam-shield-service-model
      dockerfile: Dockerfile
    container_name: antispam-ai
    ports:
      - "8000:8000"
    networks:
      - antispam-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  backend:
    build:
      context: ./ai-anti-spam-shield-backend
      dockerfile: Dockerfile
    container_name: antispam-backend
    environment:
      DATABASE_URL: postgresql://antispam_user:change-this-password@postgres:5432/antispam_db
      AI_SERVICE_URL: http://ai-service:8000
      JWT_SECRET: your-production-jwt-secret
      REFRESH_TOKEN_SECRET: your-production-refresh-secret
      NODE_ENV: production
    ports:
      - "3000:3000"
    depends_on:
      postgres:
        condition: service_healthy
      ai-service:
        condition: service_healthy
    networks:
      - antispam-network
    restart: unless-stopped

volumes:
  postgres_data:

networks:
  antispam-network:
    driver: bridge
```

**2. Create Backend Dockerfile:**

```dockerfile
# ai-anti-spam-shield-backend/Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package.json yarn.lock ./

# Install dependencies
RUN yarn install --production

# Copy source code
COPY . .

# Generate Prisma Client
RUN npx prisma generate

# Expose port
EXPOSE 3000

# Start app
CMD ["node", "src/app.js"]
```

**3. Deploy:**

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Cloud Deployment

**Heroku:**

```bash
# Install Heroku CLI
# Create Heroku apps
heroku create antispam-backend
heroku create antispam-ai

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev -a antispam-backend

# Set environment variables
heroku config:set JWT_SECRET=your-secret -a antispam-backend
heroku config:set AI_SERVICE_URL=https://antispam-ai.herokuapp.com -a antispam-backend

# Deploy
git push heroku main
```

**AWS / DigitalOcean / VPS:**

1. Setup server (Ubuntu 20.04+)
2. Install Docker and Docker Compose
3. Clone repository
4. Configure environment variables
5. Run `docker-compose up -d`
6. Setup Nginx reverse proxy
7. Configure SSL with Let's Encrypt

---

## 📚 API Documentation

### Base URLs

- **Backend:** `http://localhost:3000/api/v1`
- **AI Service:** `http://localhost:8000`

### Authentication

All protected endpoints require JWT token in header:

```
Authorization: Bearer <your-jwt-token>
```

### Key Endpoints

#### 1. User Registration
```http
POST /api/v1/users/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe",
  "phone": "+1234567890"
}
```

#### 2. User Login
```http
POST /api/v1/users/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

#### 3. Scan Text
```http
POST /api/v1/messages/scan-text
Content-Type: application/json

{
  "message": "Your message to scan for spam"
}
```

#### 4. Scan Voice
```http
POST /api/v1/messages/scan-voice
Content-Type: multipart/form-data

audio: <audio-file.wav>
```

#### 5. Get Scan History
```http
GET /api/v1/messages/history?page=1&limit=20&isSpam=true
Authorization: Bearer <token>
```

Full API documentation available at:
- Backend: See `API_DOCUMENTATION.md`
- AI Service: http://localhost:8000/docs

---

## 🔧 Troubleshooting

### Common Issues

**1. Database Connection Error**

```
Error: P1001: Can't reach database server
```

**Solution:**
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Verify DATABASE_URL in `.env`
- Test connection: `psql -U username -d antispam_db`

**2. AI Service Not Loading Model**

```
Warning: Could not initialize predictor
```

**Solution:**
```bash
cd ai-anti-spam-shield-service-model
python datasets/prepare_data.py
python app/model/train.py
```

**3. Mobile App Can't Connect**

```
DioException: Connection refused
```

**Solution:**
- Android Emulator: Use `10.0.2.2` instead of `localhost`
- iOS Simulator: Use `localhost`
- Physical Device: Use your machine's IP address
- Check firewall settings

**4. Port Already in Use**

```
Error: listen EADDRINUSE: address already in use :::3000
```

**Solution:**
```bash
# Find process using port
lsof -ti:3000

# Kill process
kill -9 $(lsof -ti:3000)
```

**5. Prisma Migration Issues**

```
Error: Migration failed
```

**Solution:**
```bash
# Reset database
yarn prisma migrate reset

# Or manually drop and recreate
dropdb antispam_db
createdb antispam_db
yarn prisma migrate dev
```

---

## 🔒 Security

### Production Security Checklist

- [ ] Change all default passwords and secrets
- [ ] Use strong JWT_SECRET (minimum 32 characters)
- [ ] Enable HTTPS/SSL in production
- [ ] Configure CORS for specific origins only
- [ ] Implement rate limiting
- [ ] Enable Helmet.js security headers
- [ ] Regular security audits: `yarn audit` / `pip check`
- [ ] Keep dependencies updated
- [ ] Use environment variables for all secrets
- [ ] Setup database backups
- [ ] Implement logging and monitoring
- [ ] Configure firewall rules
- [ ] Use secure password hashing (bcrypt with salt rounds ≥ 10)
- [ ] Implement API key authentication for AI service
- [ ] Enable PostgreSQL SSL connections

### Recommended Security Enhancements

**1. Rate Limiting (Backend):**

```bash
yarn add express-rate-limit
```

```javascript
// src/middlewares/rateLimiter.js
const rateLimit = require('express-rate-limit');

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP'
});

module.exports = limiter;
```

**2. API Key Authentication (AI Service):**

```python
# app/main.py
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

@app.post("/predict", dependencies=[Depends(verify_api_key)])
async def predict(request: PredictionRequest):
    # ...
```

**3. HTTPS Configuration (Nginx):**

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

## 📊 Monitoring & Logging

### Application Logs

**Backend:**
- Location: `logs/app.log`
- Format: JSON with timestamp, level, message

**AI Service:**
- Output: Console (stdout/stderr)
- Capture with: `python main.py > logs/ai-service.log 2>&1`

### Health Checks

```bash
# Backend
curl http://localhost:3000/health

# AI Service
curl http://localhost:8000/health

# Database
psql -U username -d antispam_db -c "SELECT 1"
```

### Monitoring Tools

- **PM2:** Built-in monitoring with `pm2 monit`
- **Docker:** `docker stats`
- **Application:** Consider Sentry, New Relic, or Datadog

---

## 🎓 Support & Resources

### Documentation

- **Backend:** `ai-anti-spam-shield-backend/README.md`
- **AI Service:** `ai-anti-spam-shield-service-model/README.md`
- **Mobile:** `ai_anti_spam_shield_mobile/README.md`

### Useful Commands

```bash
# Backend
yarn dev                  # Development
yarn start               # Production
yarn prisma:studio       # Database GUI

# AI Service
python main.py           # Start service
python model/train.py    # Train model

# Mobile
flutter run              # Run app
flutter build apk        # Build Android
flutter build ios        # Build iOS
```

### Contact & Support

- **Issues:** GitHub Issues
- **Documentation:** Project README files
- **Updates:** Check CHANGELOG.md

---

## ✅ Production Readiness Checklist

### Before Deployment

- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] AI model trained with production data
- [ ] Security measures implemented
- [ ] HTTPS/SSL configured
- [ ] Backups configured
- [ ] Monitoring setup
- [ ] Error tracking enabled
- [ ] Load testing completed
- [ ] Documentation updated
- [ ] API rate limiting enabled
- [ ] CORS properly configured
- [ ] Secrets rotated and secured

### Post-Deployment

- [ ] Health checks passing
- [ ] Logs being collected
- [ ] Monitoring alerts configured
- [ ] Backup restoration tested
- [ ] Performance metrics baseline established
- [ ] User acceptance testing completed

---

**🎉 Congratulations! Your AI Anti-Scam Shield is ready for production!**

For questions or issues, please refer to the documentation or create an issue in the repository.

