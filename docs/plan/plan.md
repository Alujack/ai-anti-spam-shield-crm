# AI Anti-Spam Shield - Scalable System Upgrade Plan

> **Version:** 2.0
> **Last Updated:** January 2026
> **Status:** Planning Phase
> **Estimated Duration:** 10 weeks

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current Architecture Analysis](#2-current-architecture-analysis)
3. [Target Architecture](#3-target-architecture)
4. [Phase Implementation Details](#4-phase-implementation-details)
5. [Technical Specifications](#5-technical-specifications)
6. [Risk Assessment](#6-risk-assessment)
7. [Success Metrics](#7-success-metrics)

---

## 1. Executive Summary

### 1.1 Project Goal

Transform the AI Anti-Spam Shield from a prototype with synchronous processing into a **production-ready, scalable system** capable of:

- Processing 1000+ requests per minute
- Real-time threat detection with <100ms latency
- Continuous model improvement through user feedback
- Multi-language support (English + Khmer)

### 1.2 Current Limitations

| Issue | Impact | Priority |
|-------|--------|----------|
| Synchronous processing | Blocks on ML inference (2-5s) | Critical |
| TF-IDF models only | Low phishing recall (51%) | Critical |
| No queue system | Cannot handle traffic spikes | High |
| SQLite database | Not production-ready | High |
| No audio analysis | Voice detection relies only on transcription | Medium |
| No feedback loop | Models cannot improve over time | Medium |

### 1.3 Implementation Priority

```
┌─────────────────────────────────────────────────────────────────┐
│  MINIMUM TO BE IMPRESSIVE (Phases 1-3)                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                           │
│  Phase 1: Architecture Hardening (Week 1)                       │
│  Phase 2: Model Upgrade - DistilBERT (Week 2-3)                │
│  Phase 3: Phishing Intelligence Engine (Week 4)                 │
├─────────────────────────────────────────────────────────────────┤
│  TO DOMINATE (Phases 4-5)                                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━                                       │
│  Phase 4: Voice Scam Real Detection (Week 5)                    │
│  Phase 5: Continuous Learning System (Week 6)                   │
├─────────────────────────────────────────────────────────────────┤
│  BONUS (Phases 6-9)                                             │
│  ━━━━━━━━━━━━━━━━━━                                             │
│  Phase 6: Khmer Language Support (Week 7)                       │
│  Phase 7: User-Level Features (Week 8)                          │
│  Phase 8: Performance & Security (Week 9)                       │
│  Phase 9: Final Presentation (Week 10)                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Current Architecture Analysis

### 2.1 System Overview

```
┌──────────────────┐      HTTP       ┌──────────────────┐
│   Flutter App    │ ──────────────> │  Node.js Backend │
│   (Mobile)       │                 │  (Express)       │
└──────────────────┘                 └────────┬─────────┘
                                              │
                                              │ HTTP (sync)
                                              ▼
                                     ┌──────────────────┐
                                     │  FastAPI ML      │
                                     │  Service         │
                                     └────────┬─────────┘
                                              │
                                              ▼
                                     ┌──────────────────┐
                                     │  TF-IDF Models   │
                                     │  (SMS, Voice,    │
                                     │   Phishing)      │
                                     └──────────────────┘
```

### 2.2 Current File Structure

```
ai-anti-spam-shield/
├── ai-anti-spam-shield-backend/           # Node.js Backend
│   ├── src/
│   │   ├── app.js                         # Express entry point
│   │   ├── config/
│   │   │   ├── index.js                   # Environment config
│   │   │   └── database.js                # Prisma client
│   │   ├── controllers/
│   │   │   ├── message.controller.js      # Scan endpoints
│   │   │   ├── phishing.controller.js     # Phishing endpoints
│   │   │   └── user.controller.js         # Auth endpoints
│   │   ├── services/
│   │   │   ├── message.service.js         # Core scan logic
│   │   │   ├── phishing.service.js        # Phishing detection
│   │   │   └── report.service.js          # User reports
│   │   ├── middlewares/
│   │   │   ├── auth.js                    # JWT authentication
│   │   │   └── rateLimiter.js             # In-memory rate limit
│   │   └── routes/
│   │       ├── message.routes.js
│   │       ├── phishing.routes.js
│   │       └── user.routes.js
│   └── prisma/
│       ├── schema.prisma                  # Database schema
│       └── dev.db                         # SQLite database
│
├── ai-anti-spam-shield-service-model/     # Python ML Service
│   ├── app/
│   │   ├── main.py                        # FastAPI entry point
│   │   ├── model/
│   │   │   ├── predictor.py               # TF-IDF predictor
│   │   │   ├── multi_model_predictor.py   # Ensemble predictor
│   │   │   └── train_separate_models.py   # Training script
│   │   └── detectors/
│   │       └── phishing_detector.py       # Rule + ML phishing
│   ├── Dockerfile
│   └── requirements.txt
│
└── ai_anti_spam_shield_mobile/            # Flutter Mobile App
    └── lib/
        ├── services/
        │   └── api_service.dart           # API client
        ├── providers/                     # Riverpod state
        └── screens/                       # UI screens
```

### 2.3 Current Model Performance

| Model | Accuracy | Precision | Recall | F1 | Issue |
|-------|----------|-----------|--------|-----|-------|
| SMS Spam (TF-IDF + LR) | 94% | 93% | 89% | 91% | Acceptable |
| Voice Spam (TF-IDF + NB) | 100%* | 100%* | 100%* | 100%* | *Overfitted on small dataset |
| Phishing (TF-IDF + RF) | 77% | 85% | 51% | 64% | **Critical: Low recall** |

**Problem:** 51% phishing recall means we miss half of all phishing attempts.

### 2.4 Current API Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/v1/messages/scan-text` | POST | Scan text for spam | Optional |
| `/api/v1/messages/scan-voice` | POST | Scan audio file | Optional |
| `/api/v1/phishing/scan-text` | POST | Check text for phishing | Optional |
| `/api/v1/phishing/scan-url` | POST | Check URL for phishing | Optional |
| `/api/v1/users/register` | POST | User registration | No |
| `/api/v1/users/login` | POST | User login | No |
| `/api/v1/reports` | POST | Submit report | Required |

---

## 3. Target Architecture

### 3.1 High-Level Architecture

```
                                    ┌─────────────────┐
                                    │   Prometheus    │
                                    │   + Grafana     │
                                    └────────┬────────┘
                                             │ metrics
                                             ▼
┌──────────────┐     ┌──────────────┐    ┌──────────────────────────┐
│ Flutter App  │────>│ Kong Gateway │───>│     Node.js Backend      │
│   (Mobile)   │     │              │    │  ┌──────────────────┐   │
└──────────────┘     │ - Rate Limit │    │  │ Text Service     │   │
                     │ - JWT Valid  │    │  │ Voice Service    │   │
                     │ - Routing    │    │  │ URL Intel Service│   │
                     └──────────────┘    │  └────────┬─────────┘   │
                                         │           │              │
                                         │  ┌────────▼─────────┐   │
                                         │  │   BullMQ Queue   │   │
                                         │  │   (Redis)        │   │
                                         │  └────────┬─────────┘   │
                                         └───────────┼─────────────┘
                                                     │
                           ┌─────────────────────────┼─────────────────────────┐
                           │                         │                         │
                           ▼                         ▼                         ▼
                  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
                  │  Text Worker    │     │  Voice Worker   │     │  URL Worker     │
                  │  (DistilBERT)   │     │  (wav2vec2)     │     │  (Intel Engine) │
                  └────────┬────────┘     └────────┬────────┘     └────────┬────────┘
                           │                       │                       │
                           └───────────────────────┴───────────────────────┘
                                                   │
                                                   ▼
                                         ┌─────────────────┐
                                         │   PostgreSQL    │
                                         │   + Redis Cache │
                                         └─────────────────┘
```

### 3.2 New File Structure

```
ai-anti-spam-shield/
├── docker-compose.yml                     # NEW: Orchestrate all services
├── docker-compose.dev.yml                 # NEW: Development overrides
├── docker-compose.prod.yml                # NEW: Production overrides
│
├── gateway/                               # NEW: API Gateway
│   └── kong/
│       ├── Dockerfile
│       └── kong.yml                       # Declarative config
│
├── monitoring/                            # NEW: Observability
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       └── dashboards/
│           └── ai-shield.json
│
├── ai-anti-spam-shield-backend/
│   ├── Dockerfile                         # NEW: Containerization
│   ├── src/
│   │   ├── config/
│   │   │   ├── redis.js                   # NEW: Redis connection
│   │   │   └── queue.js                   # NEW: Queue config
│   │   ├── services/
│   │   │   ├── text/                      # NEW: Separated services
│   │   │   │   ├── text.service.js
│   │   │   │   └── text.queue.js
│   │   │   ├── voice/
│   │   │   │   ├── voice.service.js
│   │   │   │   └── voice.queue.js
│   │   │   ├── url-intel/
│   │   │   │   ├── url.service.js
│   │   │   │   └── url.queue.js
│   │   │   ├── queue/                     # NEW: Queue management
│   │   │   │   ├── queue.manager.js
│   │   │   │   └── workers/
│   │   │   │       ├── text.worker.js
│   │   │   │       ├── voice.worker.js
│   │   │   │       └── url.worker.js
│   │   │   ├── feedback/                  # NEW: Phase 5
│   │   │   │   └── feedback.service.js
│   │   │   └── common/
│   │   │       ├── ai.client.js           # NEW: Unified AI client
│   │   │       └── cache.service.js       # NEW: Redis cache
│   │   └── routes/
│   │       └── feedback.routes.js         # NEW: Phase 5
│   └── prisma/
│       └── schema.prisma                  # MODIFIED: PostgreSQL + new tables
│
├── ai-anti-spam-shield-service-model/
│   ├── Dockerfile                         # MODIFIED: GPU support
│   └── app/
│       ├── model/
│       │   ├── transformer_trainer.py     # NEW: DistilBERT training
│       │   ├── onnx_exporter.py           # NEW: ONNX export
│       │   └── predictor_v2.py            # NEW: Transformer predictor
│       ├── intel/                         # NEW: Phase 3
│       │   ├── domain_intel.py
│       │   ├── screenshot_analyzer.py
│       │   └── risk_scorer.py
│       ├── audio/                         # NEW: Phase 4
│       │   ├── audio_embeddings.py
│       │   ├── prosody_analyzer.py
│       │   └── voice_scam_detector.py
│       ├── retraining/                    # NEW: Phase 5
│       │   ├── feedback_collector.py
│       │   ├── incremental_trainer.py
│       │   └── scheduler.py
│       └── registry/                      # NEW: Phase 5
│           └── model_registry.py
│
└── docs/
    └── plan/
        ├── plan.md                        # This document
        ├── phase1-architecture.md
        ├── phase2-model-upgrade.md
        ├── phase3-phishing-intel.md
        ├── phase4-voice-detection.md
        └── phase5-continuous-learning.md
```

### 3.3 Database Schema Changes

```prisma
// prisma/schema.prisma

datasource db {
  provider = "postgresql"  // Changed from sqlite
  url      = env("DATABASE_URL")
}

// NEW: Async job tracking
model ScanJob {
  id          String    @id @default(uuid())
  userId      String?
  type        String    // text, voice, url
  status      String    // pending, processing, completed, failed
  priority    Int       @default(0)
  input       String    // Encrypted message/URL
  inputHash   String    // For cache lookup
  result      Json?
  error       String?
  attempts    Int       @default(0)
  createdAt   DateTime  @default(now())
  startedAt   DateTime?
  completedAt DateTime?

  user User? @relation(fields: [userId], references: [id])

  @@index([status])
  @@index([userId])
  @@index([inputHash])
}

// NEW: User feedback for continuous learning
model UserFeedback {
  id                 String    @id @default(uuid())
  userId             String
  scanHistoryId      String?
  phishingHistoryId  String?
  originalPrediction String
  actualLabel        String    // spam, ham, phishing, safe
  feedbackType       String    // false_positive, false_negative, confirmed
  userComment        String?
  status             String    @default("pending")
  reviewedBy         String?
  reviewedAt         DateTime?
  createdAt          DateTime  @default(now())

  // For retraining pipeline
  includedInTraining Boolean   @default(false)
  trainingBatch      String?

  user User @relation(fields: [userId], references: [id])

  @@index([status])
  @@index([includedInTraining])
  @@index([feedbackType])
}

// NEW: Model version tracking
model ModelVersion {
  id            String    @id @default(uuid())
  modelType     String    // sms, voice, phishing
  version       String    // e.g., "v2.1.0"
  modelPath     String    // Path to model file
  metrics       Json      // {accuracy, recall, precision, f1}
  trainedAt     DateTime
  deployedAt    DateTime?
  status        String    // training, testing, deployed, rolled_back
  feedbackBatch String?
  changelog     String?

  @@unique([modelType, version])
  @@index([modelType, status])
}

// EXISTING: Enhanced with encryption
model ScanHistory {
  id              String   @id @default(uuid())
  userId          String
  messageEncrypted String  // CHANGED: Encrypted message
  messageHash     String   // NEW: For deduplication
  isSpam          Boolean
  confidence      Float
  prediction      String
  scanType        String
  details         String?
  modelVersion    String?  // NEW: Track which model was used
  scannedAt       DateTime @default(now())

  user User @relation(fields: [userId], references: [id])

  @@index([userId])
  @@index([scannedAt])
  @@index([messageHash])
}
```

---

## 4. Phase Implementation Details

> **Detailed implementation for each phase is in separate documents:**
> - [Phase 1: Architecture Hardening](./phase1-architecture.md)
> - [Phase 2: Model Upgrade](./phase2-model-upgrade.md)
> - [Phase 3: Phishing Intelligence](./phase3-phishing-intel.md)
> - [Phase 4: Voice Detection](./phase4-voice-detection.md)
> - [Phase 5: Continuous Learning](./phase5-continuous-learning.md)

### 4.1 Phase Summary

| Phase | Duration | Key Deliverables | Dependencies |
|-------|----------|------------------|--------------|
| 1 | 1 week | Docker, PostgreSQL, Redis/BullMQ, Kong Gateway | None |
| 2 | 2 weeks | DistilBERT model, ONNX export, `/predict-v2` endpoint | Phase 1 |
| 3 | 1 week | Domain intelligence, risk scoring, `/analyze-url-deep` | Phase 1 |
| 4 | 1 week | wav2vec2 embeddings, prosody analysis, `/predict-voice-v2` | Phase 1, 2 |
| 5 | 1 week | Feedback API, retraining pipeline, model registry | Phase 1, 2 |

### 4.2 Dependency Graph

```
Phase 1 (Infrastructure)
    │
    ├──────────────────┬──────────────────┐
    ▼                  ▼                  ▼
Phase 2            Phase 3            Phase 4
(Models)           (Phishing)         (Voice)
    │                  │                  │
    └──────────────────┴──────────────────┘
                       │
                       ▼
                   Phase 5
              (Continuous Learning)
                       │
    ┌──────────────────┼──────────────────┐
    ▼                  ▼                  ▼
Phase 6            Phase 7            Phase 8
(Khmer)            (Features)         (Security)
    │                  │                  │
    └──────────────────┴──────────────────┘
                       │
                       ▼
                   Phase 9
               (Presentation)
```

---

## 5. Technical Specifications

### 5.1 Technology Stack

| Layer | Current | Target | Reason |
|-------|---------|--------|--------|
| **Gateway** | None | Kong 3.4 | Rate limiting, JWT validation, routing |
| **Backend** | Express 5.x | Express 5.x | No change needed |
| **Queue** | None | BullMQ 5.x + Redis 7 | Async processing, job retry |
| **Database** | SQLite | PostgreSQL 15 | Production-ready, concurrent writes |
| **Cache** | None | Redis 7 | Prediction caching, session store |
| **ML Framework** | scikit-learn | HuggingFace Transformers | DistilBERT, wav2vec2 |
| **Inference** | Python | ONNX Runtime | 10x faster inference |
| **Monitoring** | Winston logs | Prometheus + Grafana | Metrics, dashboards |
| **Container** | Docker (ML only) | Docker Compose (all) | Full containerization |

### 5.2 New Dependencies

**Backend (package.json):**
```json
{
  "dependencies": {
    "bullmq": "^5.0.0",
    "ioredis": "^5.3.0",
    "socket.io": "^4.7.0",
    "prom-client": "^15.0.0",
    "crypto-js": "^4.2.0"
  }
}
```

**ML Service (requirements.txt):**
```
# Phase 2: Transformer models
transformers>=4.40.0
onnxruntime>=1.17.0
onnx>=1.15.0
torch>=2.2.0

# Phase 3: Domain intelligence
python-whois>=0.8.0
playwright>=1.40.0
aiohttp>=3.9.0
dnspython>=2.5.0

# Phase 4: Audio analysis
librosa>=0.10.0
soundfile>=0.12.0

# Phase 5: MLOps
mlflow>=2.10.0

# Phase 6: Multilingual
fasttext>=0.9.2
langdetect>=1.0.9
```

### 5.3 API Changes

**New Endpoints:**

| Endpoint | Method | Description | Phase |
|----------|--------|-------------|-------|
| `/api/v2/messages/scan-text` | POST | Async text scan (returns job ID) | 1 |
| `/api/v2/messages/scan-voice` | POST | Async voice scan (returns job ID) | 1 |
| `/api/v2/jobs/:id` | GET | Get job status/result | 1 |
| `/api/v2/jobs/:id/cancel` | POST | Cancel pending job | 1 |
| `/api/v2/predict` | POST | Transformer model prediction | 2 |
| `/api/v2/phishing/analyze-deep` | POST | Full URL analysis with domain intel | 3 |
| `/api/v2/voice/analyze` | POST | Enhanced voice analysis | 4 |
| `/api/v2/feedback` | POST | Submit user feedback | 5 |
| `/api/v2/feedback/pending` | GET | Admin: Get pending reviews | 5 |
| `/api/v2/feedback/:id` | PUT | Admin: Approve/reject feedback | 5 |

**Response Format Changes:**

```json
// V1 Response (current)
{
  "is_spam": true,
  "confidence": 0.92,
  "prediction": "spam"
}

// V2 Response (new)
{
  "is_spam": true,
  "confidence": 0.92,
  "prediction": "spam",
  "risk_level": "HIGH",           // NEW: LOW, MEDIUM, HIGH, CRITICAL
  "category": "PRIZE_SCAM",       // NEW: Scam type classification
  "explanation": "Message contains prize claim and urgency indicators",
  "model_version": "sms-v2.1.0",  // NEW: Model traceability
  "indicators": [                 // NEW: Detailed breakdown
    {"type": "urgency", "text": "ACT NOW", "weight": 0.3},
    {"type": "prize_claim", "text": "You won $1000", "weight": 0.4}
  ],
  "elder_warnings": [             // NEW: Optional elder mode
    "This message asks you to act immediately - take your time",
    "Real prizes don't require payment to claim"
  ]
}
```

### 5.4 Performance Targets

| Metric | Current | Target | Phase |
|--------|---------|--------|-------|
| **Text scan latency** | 2-5s | <200ms | 1, 2 |
| **Voice scan latency** | 10-30s | <5s | 1, 4 |
| **URL scan latency** | 1-3s | <500ms | 1, 3 |
| **Throughput** | ~10 req/s | 1000+ req/s | 1 |
| **SMS spam recall** | 89% | >95% | 2 |
| **Phishing recall** | 51% | >90% | 2, 3 |
| **Model update frequency** | Never | Weekly | 5 |

---

## 6. Risk Assessment

### 6.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| PostgreSQL migration breaks existing data | High | Medium | Create migration scripts, backup SQLite |
| DistilBERT increases latency | Medium | Low | Use ONNX, batch processing |
| Redis queue loses jobs | High | Low | Enable persistence, job retry |
| Domain intel APIs rate limited | Medium | Medium | Caching, multiple providers |
| wav2vec2 requires GPU | Medium | Medium | CPU fallback, optimize batch size |

### 6.2 Mitigation Strategies

1. **Database Migration**
   - Create full SQLite backup before migration
   - Write reversible migration scripts
   - Test on copy of production data

2. **Model Latency**
   - Export to ONNX for 10x speedup
   - Implement prediction caching (same message = same result)
   - Use distilled models (DistilBERT vs BERT)

3. **Queue Reliability**
   - Enable Redis persistence (AOF)
   - Implement job retry with exponential backoff
   - Dead letter queue for failed jobs
   - Job TTL to prevent queue buildup

---

## 7. Success Metrics

### 7.1 Phase Completion Criteria

| Phase | Completion Criteria |
|-------|---------------------|
| **1** | `docker-compose up` starts all services; async scan returns job ID within 100ms |
| **2** | `/predict-v2` achieves >95% recall on test set; ONNX inference <100ms |
| **3** | `/analyze-deep` returns domain age, SSL info, risk score for any URL |
| **4** | `/predict-voice-v2` includes prosody metrics and audio confidence score |
| **5** | Feedback submitted via API; weekly retrain job runs successfully |

### 7.2 Key Performance Indicators

```
┌─────────────────────────────────────────────────────────────┐
│                    DETECTION QUALITY                        │
├─────────────────────────────────────────────────────────────┤
│  SMS Spam Recall:     ████████████████████░░░░  89% → 95%   │
│  Phishing Recall:     ██████████░░░░░░░░░░░░░░  51% → 90%   │
│  Voice Scam Recall:   ████████░░░░░░░░░░░░░░░░  40%* → 85%  │
│  False Positive Rate: ████░░░░░░░░░░░░░░░░░░░░  <5%         │
└─────────────────────────────────────────────────────────────┘
* Voice recall estimated, no current audio-based detection

┌─────────────────────────────────────────────────────────────┐
│                    SYSTEM PERFORMANCE                       │
├─────────────────────────────────────────────────────────────┤
│  Text Scan Latency:   █████░░░░░░░░░░░░░░░░░░░  2s → 200ms  │
│  Voice Scan Latency:  █████████████████░░░░░░░  30s → 5s    │
│  Throughput:          █░░░░░░░░░░░░░░░░░░░░░░░  10 → 1000/s │
│  Uptime:              ████████████████████████  99.9%       │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 Monitoring Dashboard Panels

1. **Real-time Metrics**
   - Requests per second (by endpoint)
   - Prediction latency (p50, p95, p99)
   - Queue depth and processing rate
   - Error rate by service

2. **Detection Quality**
   - Spam/ham distribution over time
   - Confidence score distribution
   - User feedback rate (false positive/negative)
   - Model version performance comparison

3. **Infrastructure Health**
   - Service availability
   - Database connection pool
   - Redis memory usage
   - Container CPU/memory

---

## Appendix A: Quick Start Commands

### Development Setup

```bash
# Clone and setup
cd /opt/school-project/ai-anti-spam-shield

# Start infrastructure (after Phase 1)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Run migrations
cd ai-anti-spam-shield-backend
npx prisma migrate dev

# Start backend in dev mode
npm run dev

# Start ML service
cd ../ai-anti-spam-shield-service-model
uvicorn app.main:app --reload --port 8000
```

### Production Deployment

```bash
# Build and deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Check service health
docker-compose ps
curl http://localhost:8080/health

# View logs
docker-compose logs -f backend ml-service

# Scale workers
docker-compose up -d --scale text-worker=3 --scale voice-worker=2
```

---

## Appendix B: References

- [BullMQ Documentation](https://docs.bullmq.io/)
- [DistilBERT Paper](https://arxiv.org/abs/1910.01108)
- [ONNX Runtime](https://onnxruntime.ai/)
- [wav2vec2 Paper](https://arxiv.org/abs/2006.11477)
- [Kong Gateway](https://docs.konghq.com/)
- [Prometheus + Grafana](https://prometheus.io/docs/)

---

**Next Steps:**
1. Review this plan with team/advisor
2. Begin Phase 1 implementation
3. Create detailed documentation for each phase (see `docs/plan/phase*.md`)
