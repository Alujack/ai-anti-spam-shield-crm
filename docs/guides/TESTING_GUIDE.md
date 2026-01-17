# Testing Guide

## Overview

This guide covers testing procedures for all components of the AI Anti-Spam Shield system.

---

## Quick Start Testing

### Verify All Services

```bash
# 1. Start AI Service
cd ai-anti-spam-shield-service-model/app
python main.py &

# 2. Start Backend
cd ai-anti-spam-shield-backend
yarn dev &

# 3. Test health endpoints
curl http://localhost:8000/health
curl http://localhost:3000/api/v1/health
```

### Test Spam Detection

```bash
# Test with spam message
curl -X POST http://localhost:3000/api/v1/messages/scan-text \
  -H "Content-Type: application/json" \
  -d '{"message": "Congratulations! You won $1,000,000! Click here now!"}'

# Expected: isSpam: true, high confidence

# Test with legitimate message
curl -X POST http://localhost:3000/api/v1/messages/scan-text \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi, the meeting is scheduled for tomorrow at 3 PM."}'

# Expected: isSpam: false
```

---

## Backend API Testing

### Authentication Tests

```bash
# Register new user
curl -X POST http://localhost:3000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "name": "Test User"
  }'

# Login
curl -X POST http://localhost:3000/api/v1/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'

# Save the token from login response
TOKEN="<jwt_token_from_response>"

# Get profile (authenticated)
curl http://localhost:3000/api/v1/users/profile \
  -H "Authorization: Bearer $TOKEN"
```

### Message Scanning Tests

```bash
# Scan text message (authenticated)
curl -X POST http://localhost:3000/api/v1/messages/scan-text \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message": "This is a test message"}'

# Get scan history
curl http://localhost:3000/api/v1/messages/history \
  -H "Authorization: Bearer $TOKEN"

# Get statistics
curl http://localhost:3000/api/v1/messages/stats \
  -H "Authorization: Bearer $TOKEN"
```

### Phishing Detection Tests

```bash
# Scan for phishing
curl -X POST http://localhost:3000/api/v1/phishing/scan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"text": "Your account has been suspended. Click here to verify: http://fake-bank.com"}'

# Scan URL
curl -X POST http://localhost:3000/api/v1/phishing/scan-url \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url": "http://paypa1-secure.com/login"}'
```

---

## AI Service Testing

### Direct API Tests

```bash
# Health check
curl http://localhost:8000/health

# Predict spam
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"message": "Win free money now! Click here!"}'

# Batch predict
curl -X POST http://localhost:8000/batch-predict \
  -H "Content-Type: application/json" \
  -d '{"messages": ["Hello friend", "You won lottery!", "Meeting at 5pm"]}'
```

### Voice Processing Test

```bash
# Test voice transcription (requires audio file)
curl -X POST http://localhost:8000/predict-voice \
  -F "audio=@test_audio.wav"
```

### Python Unit Tests

```bash
cd ai-anti-spam-shield-service-model

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_predictor.py

# Run with coverage report
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

---

## Mobile App Testing

### Unit Tests

```bash
cd ai_anti_spam_shield_mobile

# Run all tests
flutter test

# Run specific test file
flutter test test/unit/scan_provider_test.dart

# Run with coverage
flutter test --coverage
genhtml coverage/lcov.info -o coverage/html
```

### Widget Tests

```bash
# Run widget tests
flutter test test/widget/

# Run specific widget test
flutter test test/widget/home_screen_test.dart
```

### Integration Tests

```bash
# Run integration tests (requires emulator/device)
flutter test integration_test/app_test.dart
```

### Manual Testing Checklist

#### Authentication Flow

- [ ] Register new account
- [ ] Login with credentials
- [ ] View profile
- [ ] Update profile
- [ ] Logout

#### Scanning Flow

- [ ] Enter text message
- [ ] Tap scan button
- [ ] View scan result
- [ ] Check spam indicators
- [ ] View confidence score

#### History Flow

- [ ] View scan history list
- [ ] Filter by spam/safe
- [ ] Search history
- [ ] View scan details

#### Voice Scanning

- [ ] Grant microphone permission
- [ ] Record voice message
- [ ] Submit for analysis
- [ ] View transcription
- [ ] View spam result

---

## Test Data

### Spam Examples

```
1. "Congratulations! You've won $1,000,000! Claim now!"
2. "URGENT: Your account will be closed. Verify now!"
3. "Free iPhone 15! Click here: bit.ly/free-phone"
4. "You are selected for a prize. Send bank details."
5. "Make $5000/day working from home! No experience!"
```

### Legitimate Examples

```
1. "Hi, can we schedule a meeting for tomorrow?"
2. "The project deadline has been moved to Friday."
3. "Please review the attached document."
4. "Thank you for your email. I'll get back to you soon."
5. "Happy birthday! Hope you have a great day."
```

### Phishing Examples

```
1. "Your PayPal account has been limited. Click to verify: http://paypa1.com"
2. "Amazon: Your order cannot be delivered. Update address: http://amaz0n-verify.com"
3. "Bank Alert: Suspicious activity detected. Confirm identity now."
4. "Netflix: Payment failed. Update billing: http://netf1ix-billing.com"
5. "Apple ID locked! Verify at: http://app1e-id-verify.com"
```

---

## Automated Testing

### CI/CD Pipeline Tests

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd ai-anti-spam-shield-backend && yarn install
      - run: cd ai-anti-spam-shield-backend && yarn test

  ai-service:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: cd ai-anti-spam-shield-service-model && pip install -r app/requirements.txt
      - run: cd ai-anti-spam-shield-service-model && pytest

  mobile:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.16.0'
      - run: cd ai_anti_spam_shield_mobile && flutter pub get
      - run: cd ai_anti_spam_shield_mobile && flutter test
```

### Load Testing

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test endpoint performance (100 requests, 10 concurrent)
ab -n 100 -c 10 -T application/json \
  -p payload.json \
  http://localhost:3000/api/v1/messages/scan-text

# payload.json content:
# {"message": "Test message for load testing"}
```

---

## Performance Benchmarks

### Expected Response Times

| Endpoint | Target | Acceptable |
|----------|--------|------------|
| /health | < 50ms | < 100ms |
| /scan-text | < 100ms | < 200ms |
| /scan-voice | < 2s | < 5s |
| /phishing/scan | < 150ms | < 300ms |

### Throughput Targets

| Metric | Target |
|--------|--------|
| Requests/second (scan-text) | > 100 |
| Concurrent users | > 50 |
| Uptime | > 99.9% |

---

## Troubleshooting Tests

### Common Test Failures

**Database Connection Error:**
```bash
# Ensure PostgreSQL is running
sudo systemctl start postgresql

# Check connection
psql "postgresql://user:password@localhost:5432/antispam_db"
```

**Model Not Found:**
```bash
# Ensure model is trained
cd ai-anti-spam-shield-service-model
python datasets/prepare_data.py
python app/model/train.py
```

**Port Already in Use:**
```bash
# Kill existing processes
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```

**Flutter Test Failures:**
```bash
# Clean and rebuild
flutter clean
flutter pub get
flutter test
```
