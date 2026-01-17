# System Architecture

## Overview

AI Anti-Spam Shield is a microservices-based architecture consisting of three primary components that work together to provide comprehensive threat detection capabilities.

## System Components

### 1. Backend API Service

**Technology:** Node.js + Express.js + Prisma ORM

**Responsibilities:**
- User authentication and authorization
- Request routing and validation
- Business logic orchestration
- Database operations
- Integration with AI service

**Key Modules:**

| Module | Description |
|--------|-------------|
| `controllers/` | HTTP request handlers |
| `services/` | Business logic layer |
| `routes/` | API endpoint definitions |
| `middlewares/` | Auth, validation, error handling |
| `utils/` | Helper functions and utilities |

### 2. AI/ML Service

**Technology:** Python + FastAPI + scikit-learn + Transformers

**Responsibilities:**
- Text classification (spam/ham detection)
- Phishing detection and analysis
- Voice transcription and analysis
- URL reputation checking
- Advanced threat detection

**Key Modules:**

| Module | Description |
|--------|-------------|
| `detectors/` | Specialized threat detectors |
| `model/` | ML model training and inference |
| `api/` | FastAPI endpoints |
| `utils/` | Text processing utilities |

### 3. Mobile Application

**Technology:** Flutter + Riverpod + Dio

**Responsibilities:**
- User interface and experience
- Text and voice input handling
- Real-time result display
- Scan history management
- User settings and preferences

**Key Modules:**

| Module | Description |
|--------|-------------|
| `screens/` | UI screen widgets |
| `providers/` | State management |
| `services/` | API integration |
| `models/` | Data transfer objects |
| `widgets/` | Reusable UI components |

## Data Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER INPUT                                │
│              (Text Message / Voice Recording / URL)               │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      MOBILE APPLICATION                           │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  1. Capture input (text/voice)                              │ │
│  │  2. Validate and prepare request                            │ │
│  │  3. Send to Backend API                                     │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────┬────────────────────────────────────┘
                              │ HTTP POST
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                        BACKEND API                                │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  1. Authenticate request (JWT)                              │ │
│  │  2. Validate input data                                     │ │
│  │  3. Forward to AI Service                                   │ │
│  │  4. Store results in database                               │ │
│  │  5. Return response to client                               │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────┬────────────────────────────────────┘
                              │ HTTP POST
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                        AI SERVICE                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  1. Preprocess input (text normalization, feature extraction)│ │
│  │  2. Run ML model inference                                  │ │
│  │  3. Calculate confidence scores                             │ │
│  │  4. Generate detailed analysis                              │ │
│  │  5. Return prediction results                               │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                       RESPONSE FLOW                               │
│  AI Service → Backend API → Mobile App → User Display             │
└──────────────────────────────────────────────────────────────────┘
```

## Database Schema

```
┌─────────────────────────────────────────────────────────────────┐
│                           User                                   │
├─────────────────────────────────────────────────────────────────┤
│  id          : String (UUID, Primary Key)                       │
│  email       : String (Unique)                                  │
│  password    : String (Hashed)                                  │
│  name        : String                                           │
│  phone       : String (Optional)                                │
│  role        : Enum (USER, ADMIN)                               │
│  createdAt   : DateTime                                         │
│  updatedAt   : DateTime                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        ScanHistory                               │
├─────────────────────────────────────────────────────────────────┤
│  id          : String (UUID, Primary Key)                       │
│  userId      : String (Foreign Key → User)                      │
│  message     : String                                           │
│  isSpam      : Boolean                                          │
│  confidence  : Float                                            │
│  prediction  : String                                           │
│  details     : JSON (Optional)                                  │
│  scannedAt   : DateTime                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Report                                  │
├─────────────────────────────────────────────────────────────────┤
│  id          : String (UUID, Primary Key)                       │
│  userId      : String (Foreign Key → User)                      │
│  messageText : String                                           │
│  reportType  : String                                           │
│  description : String (Optional)                                │
│  status      : String (PENDING, REVIEWED, RESOLVED)             │
│  createdAt   : DateTime                                         │
│  updatedAt   : DateTime                                         │
└─────────────────────────────────────────────────────────────────┘
```

## ML Model Architecture

### Text Classification Pipeline

```
Input Text
    │
    ▼
┌─────────────────┐
│ Preprocessing   │
│ - Lowercase     │
│ - Remove noise  │
│ - Tokenization  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Feature Extract │
│ - TF-IDF        │
│ - N-grams       │
│ - Word vectors  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ML Models       │
│ - Random Forest │
│ - XGBoost       │
│ - BERT (adv.)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Output          │
│ - is_spam       │
│ - confidence    │
│ - indicators    │
└─────────────────┘
```

### Phishing Detection Pipeline

```
Input (Text/URL)
    │
    ▼
┌─────────────────┐
│ URL Analysis    │
│ - Domain check  │
│ - Structure     │
│ - Reputation    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Content Analysis│
│ - Brand detect  │
│ - Urgency score │
│ - Social eng.   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Combined Model  │
│ - Ensemble      │
│ - Transformers  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Output          │
│ - is_phishing   │
│ - threat_level  │
│ - indicators[]  │
└─────────────────┘
```

## Security Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      Security Layers                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Layer 1: Transport Security                                      │
│  ├── HTTPS/TLS encryption                                        │
│  └── Certificate validation                                      │
│                                                                   │
│  Layer 2: Application Security                                    │
│  ├── JWT authentication                                          │
│  ├── Role-based access control                                   │
│  ├── Input validation                                            │
│  └── Rate limiting                                               │
│                                                                   │
│  Layer 3: API Security                                            │
│  ├── CORS configuration                                          │
│  ├── Helmet.js headers                                           │
│  └── Request sanitization                                        │
│                                                                   │
│  Layer 4: Data Security                                           │
│  ├── Password hashing (bcrypt)                                   │
│  ├── Encrypted storage                                           │
│  └── Audit logging                                               │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Scalability Considerations

### Horizontal Scaling

- Backend API: Stateless design allows multiple instances behind load balancer
- AI Service: Model serving can be distributed across multiple workers
- Database: PostgreSQL supports read replicas for scaling reads

### Performance Optimization

- Model caching in AI service
- Connection pooling for database
- Response caching for repeated queries
- Batch processing for bulk operations

## Integration Points

| Service A | Service B | Protocol | Purpose |
|-----------|-----------|----------|---------|
| Mobile | Backend | REST/HTTPS | All user operations |
| Backend | AI Service | REST/HTTP | ML predictions |
| Backend | Database | Prisma/TCP | Data persistence |
| Mobile | Backend | WebSocket | Real-time updates |
