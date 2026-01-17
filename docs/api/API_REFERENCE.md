# API Reference

## Base URL

```
Production: https://api.antispam.example.com/api/v1
Development: http://localhost:3000/api/v1
```

## Authentication

All protected endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

---

## Authentication Endpoints

### Register User

Creates a new user account.

```http
POST /users/register
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | Valid email address |
| password | string | Yes | Min 8 characters |
| name | string | Yes | User's full name |
| phone | string | No | Phone number |

**Example Request:**

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "name": "John Doe",
  "phone": "+1234567890"
}
```

**Response (201 Created):**

```json
{
  "status": "success",
  "message": "User registered successfully",
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "name": "John Doe",
      "phone": "+1234567890",
      "role": "USER",
      "createdAt": "2025-12-05T10:00:00.000Z"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

---

### Login

Authenticates a user and returns tokens.

```http
POST /users/login
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | Registered email |
| password | string | Yes | User password |

**Example Request:**

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**

```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "name": "John Doe",
      "role": "USER"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

---

### Get Profile

Retrieves the authenticated user's profile.

```http
GET /users/profile
Authorization: Bearer <token>
```

**Response (200 OK):**

```json
{
  "status": "success",
  "message": "Profile retrieved successfully",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "John Doe",
    "phone": "+1234567890",
    "role": "USER",
    "createdAt": "2025-12-05T10:00:00.000Z",
    "updatedAt": "2025-12-05T10:00:00.000Z"
  }
}
```

---

### Update Profile

Updates the authenticated user's profile.

```http
PUT /users/profile
Authorization: Bearer <token>
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | No | Updated name |
| phone | string | No | Updated phone |

**Example Request:**

```json
{
  "name": "John Updated",
  "phone": "+0987654321"
}
```

**Response (200 OK):**

```json
{
  "status": "success",
  "message": "Profile updated successfully",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "John Updated",
    "phone": "+0987654321"
  }
}
```

---

## Message Scanning Endpoints

### Scan Text Message

Analyzes a text message for spam/phishing threats.

```http
POST /messages/scan-text
Authorization: Bearer <token>
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| message | string | Yes | Text to analyze |

**Example Request:**

```json
{
  "message": "Congratulations! You've won $1,000,000! Click here to claim now!"
}
```

**Response (200 OK):**

```json
{
  "status": "success",
  "message": "Message scanned successfully",
  "data": {
    "id": "scan-123",
    "isSpam": true,
    "confidence": 0.95,
    "prediction": "SPAM",
    "analysis": {
      "spamIndicators": [
        "Prize/lottery language",
        "Urgency indicators",
        "Call to action"
      ],
      "riskLevel": "HIGH",
      "details": "Message contains multiple spam indicators including lottery scam patterns."
    },
    "scannedAt": "2025-12-05T10:30:00.000Z"
  }
}
```

---

### Scan Voice Message

Analyzes a voice message by transcribing and scanning for threats.

```http
POST /messages/scan-voice
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Request Body (Form Data):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| audio | file | Yes | Audio file (WAV, MP3, OGG, FLAC, WEBM) |

**Response (200 OK):**

```json
{
  "status": "success",
  "message": "Voice message scanned successfully",
  "data": {
    "id": "scan-456",
    "transcribedText": "Hello, this is a call about your car warranty...",
    "isSpam": true,
    "confidence": 0.89,
    "prediction": "SPAM",
    "analysis": {
      "spamIndicators": [
        "Car warranty scam pattern",
        "Unsolicited call pattern"
      ],
      "riskLevel": "HIGH"
    },
    "audioInfo": {
      "duration": 15.5,
      "format": "audio/wav"
    },
    "scannedAt": "2025-12-05T10:35:00.000Z"
  }
}
```

---

### Get Scan History

Retrieves the user's scan history with pagination and filtering.

```http
GET /messages/history
Authorization: Bearer <token>
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | number | 1 | Page number |
| limit | number | 10 | Items per page |
| filter | string | all | Filter: all, spam, safe |
| startDate | string | - | Start date (ISO 8601) |
| endDate | string | - | End date (ISO 8601) |

**Example Request:**

```
GET /messages/history?page=1&limit=10&filter=spam
```

**Response (200 OK):**

```json
{
  "status": "success",
  "message": "History retrieved successfully",
  "data": {
    "scans": [
      {
        "id": "scan-123",
        "message": "You've won $1,000,000!",
        "isSpam": true,
        "confidence": 0.95,
        "prediction": "SPAM",
        "scannedAt": "2025-12-05T10:30:00.000Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 25,
      "totalPages": 3
    }
  }
}
```

---

### Get Scan Statistics

Retrieves scanning statistics for the user.

```http
GET /messages/stats
Authorization: Bearer <token>
```

**Response (200 OK):**

```json
{
  "status": "success",
  "message": "Statistics retrieved successfully",
  "data": {
    "totalScans": 150,
    "spamDetected": 45,
    "safeMessages": 105,
    "spamRate": 0.30,
    "averageConfidence": 0.87,
    "lastScanAt": "2025-12-05T10:35:00.000Z"
  }
}
```

---

## Phishing Detection Endpoints

### Scan for Phishing

Analyzes text for phishing indicators.

```http
POST /phishing/scan
Authorization: Bearer <token>
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| text | string | Yes | Text to analyze |

**Example Request:**

```json
{
  "text": "Your account has been suspended. Click here to verify: http://fake-bank.com/verify"
}
```

**Response (200 OK):**

```json
{
  "status": "success",
  "message": "Phishing scan completed",
  "data": {
    "isPhishing": true,
    "confidence": 0.92,
    "threatLevel": "HIGH",
    "indicators": [
      "Account suspension urgency",
      "Suspicious URL detected",
      "Brand impersonation attempt"
    ],
    "brandDetected": "banking",
    "recommendations": [
      "Do not click any links",
      "Contact your bank directly",
      "Report this message"
    ]
  }
}
```

---

### Scan URL

Analyzes a URL for malicious indicators.

```http
POST /phishing/scan-url
Authorization: Bearer <token>
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| url | string | Yes | URL to analyze |

**Example Request:**

```json
{
  "url": "http://paypa1-secure.com/login"
}
```

**Response (200 OK):**

```json
{
  "status": "success",
  "message": "URL scan completed",
  "data": {
    "isMalicious": true,
    "confidence": 0.94,
    "threatLevel": "CRITICAL",
    "analysis": {
      "domain": "paypa1-secure.com",
      "registrationAge": "2 days",
      "sslValid": false,
      "typosquatting": true,
      "impersonatedBrand": "PayPal"
    },
    "indicators": [
      "Domain registered recently",
      "Typosquatting detected (paypa1 vs paypal)",
      "No valid SSL certificate",
      "Known phishing pattern"
    ]
  }
}
```

---

## Report Endpoints

### Submit Report

Submits a report for a suspicious message.

```http
POST /reports
Authorization: Bearer <token>
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| messageText | string | Yes | Reported message |
| reportType | string | Yes | Type: SPAM, PHISHING, SCAM, OTHER |
| description | string | No | Additional details |

**Example Request:**

```json
{
  "messageText": "You won a free iPhone! Claim now!",
  "reportType": "SCAM",
  "description": "Received this via SMS from unknown number"
}
```

**Response (201 Created):**

```json
{
  "status": "success",
  "message": "Report submitted successfully",
  "data": {
    "id": "report-789",
    "status": "PENDING",
    "createdAt": "2025-12-05T11:00:00.000Z"
  }
}
```

---

### Get User Reports

Retrieves reports submitted by the user.

```http
GET /reports
Authorization: Bearer <token>
```

**Response (200 OK):**

```json
{
  "status": "success",
  "message": "Reports retrieved successfully",
  "data": {
    "reports": [
      {
        "id": "report-789",
        "messageText": "You won a free iPhone!",
        "reportType": "SCAM",
        "status": "PENDING",
        "createdAt": "2025-12-05T11:00:00.000Z"
      }
    ],
    "total": 5
  }
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "status": "error",
  "message": "Error description",
  "error": {
    "code": "ERROR_CODE",
    "details": "Additional details if available"
  }
}
```

### Common Error Codes

| HTTP Code | Error Code | Description |
|-----------|------------|-------------|
| 400 | BAD_REQUEST | Invalid request body |
| 401 | UNAUTHORIZED | Missing or invalid token |
| 403 | FORBIDDEN | Insufficient permissions |
| 404 | NOT_FOUND | Resource not found |
| 422 | VALIDATION_ERROR | Request validation failed |
| 429 | RATE_LIMITED | Too many requests |
| 500 | INTERNAL_ERROR | Server error |

---

## Rate Limiting

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Authentication | 10 requests | 1 minute |
| Scanning | 100 requests | 1 minute |
| Reports | 20 requests | 1 minute |
| General | 1000 requests | 1 hour |

---

## AI Service Endpoints

The AI service runs on port 8000 and is called internally by the backend.

### Health Check

```http
GET /health
```

### Predict Text

```http
POST /predict
Content-Type: application/json

{
  "message": "Text to analyze"
}
```

### Predict Voice

```http
POST /predict-voice
Content-Type: multipart/form-data

audio: <audio_file>
```

### Batch Predict

```http
POST /batch-predict
Content-Type: application/json

{
  "messages": ["text1", "text2", "text3"]
}
```
