# AI Anti-Spam Shield
## Project Practicum Presentation

**Royal University of Phnom Penh**

Lecturer: Mr. Chhim Bunchhun

---

## Slide 1: Title Slide

**ROYAL UNIVERSITY OF PHNOM PENH**

**PROJECT PRACTICUM**

# AI Anti-Spam Shield
### Intelligent Spam and Phishing Detection System

**Group Members:** [Add your names here]

**Lecturer:** Mr. Chhim Bunchhun

---

## Slide 2: Content

- Introduction
- Literature Review
- Methodology
- Result
- Discussion
- Conclusion

---

## Slide 3: INTRODUCTION

### Background and Motivation

In the digital age, spam and phishing attacks have become increasingly sophisticated, posing significant threats to individuals and organizations. Cambodia has seen a rise in SMS scams, fraudulent messages, and phishing attempts targeting mobile users. Traditional rule-based spam filters are no longer sufficient to combat these evolving threats, creating a need for intelligent, AI-powered detection systems.

### Problem Statements

- Increasing volume of spam messages and phishing attacks targeting mobile users
- Traditional spam filters fail to detect sophisticated social engineering attacks
- Lack of accessible, user-friendly tools for Cambodian users to verify suspicious messages
- Voice-based scams are emerging but few solutions address voice message analysis
- Users often fall victim to brand impersonation and URL-based phishing attacks

### Aim and Objectives

**Aim:** To develop an AI-powered mobile application that detects spam, phishing, and social engineering threats in text and voice messages with high accuracy.

**Objectives:**
- Provide real-time spam detection with 95%+ accuracy
- Detect phishing attempts including URL analysis and brand impersonation
- Support both text and voice message scanning
- Offer user-friendly mobile interface for easy threat verification
- Maintain scan history for user awareness and learning

### Limitation and Scopes

**Limitations:**
- Platform: Mobile application (iOS and Android via Flutter)
- Target: Individual users (not enterprise-level deployment)
- Language: Primarily English text analysis

**Scopes (Features):**

*Core scam detection (ML-powered):*
- Text message spam detection (TF-IDF + Logistic Regression)
- Voice message transcription & analysis (multi-modal: speech-to-text + audio embeddings + prosody)
- Phishing URL & content detection, including brand impersonation & homoglyph/lookalike detection
- Email auto-scan over IMAP (Gmail / Outlook / Yahoo / custom), with scheduled background scanning

*Security operations (SOC dashboard):*
- Threat, incident & alert management
- Automated response playbooks
- Network activity monitoring
- User behavior anomaly analysis
- File scanning (scan-by-ID & statistics; file upload + VirusTotal lookup planned)

*Platform & data:*
- Scan history management
- User threat reporting system
- Statistics & analytics dashboard
- Continuous learning: user feedback → model retraining loop

---

## Slide 4: LITERATURE REVIEW

### Previous Research Summary

| Author (Year, Topic) | Method | Description | Result |
|---------------------|--------|-------------|--------|
| Almeida et al. (2011) - SMS Spam Collection | Naive Bayes, SVM | Created UCI SMS Spam dataset with 5,574 messages | 97.5% accuracy with SVM |
| Sahami et al. (1998) - Bayesian Spam Filtering | Naive Bayes | Probabilistic approach to email spam classification | Foundation for modern spam filters |
| Mohammad et al. (2014) - Phishing Detection | Machine Learning + URL Features | Feature extraction from URLs for phishing detection | 92% detection rate |
| Gupta et al. (2021) - Deep Learning Spam | LSTM, BERT | Transformer-based text classification for spam | 98.2% accuracy on benchmark |
| Vaswani et al. (2017) - Transformers | Attention Mechanism | Self-attention for NLP tasks | State-of-the-art in text classification |

### Remaining Issues

- Most solutions focus only on email spam, not SMS or voice
- Limited research on multi-modal (text + voice) threat detection
- Lack of mobile-first solutions for end users
- Need for real-time detection with low latency
- Brand impersonation detection remains challenging

---

## Slide 5: METHODOLOGY

### Research Design & Timeline

| Phase | Activities | Duration |
|-------|-----------|----------|
| Phase 1 | Research & Planning | Week 1-2 |
| Phase 2 | Backend & ML Development | Week 3-6 |
| Phase 3 | Mobile App Development | Week 7-10 |
| Phase 4 | Integration & Testing | Week 11-12 |
| Phase 5 | Deployment & Documentation | Week 13-14 |

### Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend API** | Node.js, Express.js, Prisma ORM, JWT |
| **AI/ML Service** | Python 3.11, FastAPI 0.109, scikit-learn 1.4 |
| **Mobile App** | Flutter 3.x, Riverpod, Dio |
| **Database** | SQLite / PostgreSQL with Prisma ORM |
| **ML Libraries** | NLTK 3.8, Pandas 2.2, NumPy 1.26 |
| **Voice Processing** | SpeechRecognition 3.10, PyDub 0.25 |

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Mobile App (Flutter)                      │
│              iOS / Android / Web / Desktop                   │
└─────────────────────┬───────────────────────────────────────┘
                      │ REST API (JSON)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                Backend API (Node.js/Express)                 │
│     Authentication │ Business Logic │ Database Operations    │
│         JWT Auth   │  Scan History  │   User Management      │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP Internal API
                      ▼
┌─────────────────────────────────────────────────────────────┐
│               AI/ML Service (Python/FastAPI)                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ SMS Spam    │  │ Voice Scam  │  │ Phishing Detection  │  │
│  │ Classifier  │  │ Classifier  │  │ (URL + Text)        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Slide 5.1: DATASETS

### Dataset Sources & Statistics

We utilized three specialized datasets from HuggingFace for training our models:

| Dataset | Source | Total Samples | Train Set | Test Set | Distribution |
|---------|--------|---------------|-----------|----------|--------------|
| **SMS Spam** | `Deysi/spam-detection-dataset` | 10,900 | 8,720 | 2,180 | Balanced (≈50% spam / 50% ham) |
| **Voice Scam** | `BothBosu/scam-dialogue` | 1,600 | 1,280 | 320 | Balanced (50% scam / 50% legitimate) |
| **Phishing** | `shawhin/phishing-site-classification` | 2,100 | 1,680 | 420 | Balanced (≈50% phishing / 50% legitimate) |

**Total Training Data: 14,600 samples** (balanced datasets used to train the deployed models)

### Dataset Features

| Dataset | Input Feature | Label Feature | Content Type |
|---------|---------------|---------------|--------------|
| SMS Spam | `message` (text) | `label` (0=ham, 1=spam) | SMS messages |
| Voice Scam | `dialogue` (text) | `label` (0=non-scam, 1=scam) | Transcribed calls |
| Phishing | `text` (URL) | `label` (0=legitimate, 1=phishing) | Website URLs |

### Data Split Strategy

- **Train/Test Split Ratio:** 80% / 20%
- **Stratification:** Enabled to maintain class distribution
- **Random State:** 42 (for reproducibility)
- **Validation:** K-fold cross-validation during hyperparameter tuning

---

## Slide 5.2: MODEL ARCHITECTURE

### Three Specialized Detection Models

```
┌─────────────────────────────────────────────────────────────────��────┐
│                        AI/ML Detection System                         │
├──────────────────┬──────────────────┬────────────────────────────────┤
│   SMS SPAM       │   VOICE SCAM     │      PHISHING DETECTION        │
│   CLASSIFIER     │   CLASSIFIER     │         CLASSIFIER             │
├──────────────────┼──────────────────┼────────────────────────────────┤
│ Logistic         │ Random Forest    │ Random Forest                  │
│ Regression       │ (100 trees)      │ + Custom Feature Extractors    │
├──────────────────┼──────────────────┼────────────────────────────────┤
│ TF-IDF           │ TF-IDF           │ TF-IDF + URL Features +        │
│ (3,000 features) │ (5,000 features) │ Text Features (1,496 total)    │
├──────────────────┼──────────────────┼────────────────────────────────┤
│ 10,900 samples   │ 1,600 samples    │ 2,100 samples                  │
└──────────────────┴──────────────────┴────────────────────────────────┘
```

### Model Selection Rationale

| Model | Algorithm Selected | Why This Algorithm? |
|-------|-------------------|---------------------|
| SMS Spam | Logistic Regression | Highest accuracy, fast inference, best for sparse TF-IDF text |
| Voice Scam | Random Forest | All algorithms tied at 100%; chose Random Forest for robustness on a small dataset |
| Phishing | Random Forest | Highest precision (fewest false phishing alarms); pairs well with custom URL features |

### Algorithm Comparison Results

> Note: these comparisons were run during model selection on a larger combined corpus.
> The **deployed** models were then trained on the balanced datasets in Slide 5.1 — their final metrics are on the Results slide.

**SMS Spam Detection:**
| Algorithm | Accuracy | Precision | Recall | F1-Score | Training Time |
|-----------|----------|-----------|--------|----------|---------------|
| **Logistic Regression** | **94.46%** | **95.16%** | **90.96%** | **93.01%** | 18.30s |
| Naive Bayes | 92.09% | 89.43% | 91.27% | 90.34% | 0.40s |
| Random Forest | 89.47% | 98.11% | 75.48% | 85.32% | 9.62s |

**Voice Scam Detection:** (all algorithms tied — Random Forest deployed)
| Algorithm | Accuracy | Precision | Recall | F1-Score | Training Time |
|-----------|----------|-----------|--------|----------|---------------|
| **Random Forest** | **100%** | **100%** | **100%** | **100%** | 0.16s |
| Logistic Regression | 100% | 100% | 100% | 100% | 2.67s |
| Naive Bayes | 100% | 100% | 100% | 100% | 0.015s |

**Phishing Detection:** (Random Forest deployed — highest precision)
| Algorithm | Accuracy | Precision | Recall | F1-Score | Training Time |
|-----------|----------|-----------|--------|----------|---------------|
| **Random Forest** | 75.65% | **96.45%** | 44.86% | 61.23% | 7.41s |
| Logistic Regression | 77.74% | 93.90% | 51.43% | 66.46% | 116.29s |
| Naive Bayes | 57.05% | 49.95% | 92.34% | 64.83% | 0.23s |

---

## Slide 5.3: TEXT PREPROCESSING PIPELINE

### Preprocessing Steps (Applied to All Models)

```
Raw Text Input
      │
      ▼
┌─────────────────────────────────────┐
│  1. Convert to Lowercase            │
│     "URGENT! Click HERE" → "urgent! click here"
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  2. Remove URLs                     │
│     Regex: http[s]?://\S+           │
│     "visit http://spam.com" → "visit"
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  3. Remove Email Addresses          │
│     Regex: \S+@\S+\.\S+             │
│     "email test@spam.com" → "email" │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  4. Remove Phone Numbers            │
│     Regex: \d{10,}                  │
│     "call 1234567890" → "call"      │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  5. Remove Special Characters       │
│     Keep only letters and spaces    │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  6. Stopword Removal                │
│     NLTK English Stopwords          │
│     Remove: the, is, at, which...   │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  7. Porter Stemming                 │
│     "running" → "run"               │
│     "urgently" → "urgent"           │
└─────────────────────────────────────┘
      │
      ▼
    Clean Text Output
```

---

## Slide 5.4: FEATURE EXTRACTION

### TF-IDF Vectorization Configuration

| Parameter | SMS Model | Voice Model | Phishing Model |
|-----------|-----------|-------------|----------------|
| **max_features** | 3,000 | 5,000 | 5,000 |
| **ngram_range** | (1, 2) | (1, 3) | (1, 2) |
| **min_df** | 2 | 2 | 2 |
| **max_df** | 0.85 | 0.80 | 0.85 |

**TF-IDF Formula:**
```
TF-IDF(t,d) = TF(t,d) × IDF(t)

Where:
- TF(t,d) = (Number of times term t appears in document d) / (Total terms in d)
- IDF(t) = log(Total documents / Documents containing term t)
```

### Phishing Model: Custom Feature Extractors

**URL Feature Extractor (24 Features):**

| Category | Features Extracted |
|----------|-------------------|
| **Length Features** | URL length, domain length, path length, query length |
| **Structure Features** | Number of subdomains, path depth, query parameters count |
| **Character Analysis** | Digit count, special character count, entropy score |
| **Security Indicators** | HTTPS presence, HTTP presence, IP address in URL |
| **Suspicious Patterns** | @ symbol, double slashes, hexadecimal encoding |
| **TLD Analysis** | Suspicious TLDs (tk, ml, ga, cf, gq, xyz - 19 TLDs) |
| **Brand Detection** | Impersonation of 24 brands (PayPal, Amazon, Netflix, etc.) |
| **URL Shorteners** | Detection of 15 shorteners (bit.ly, tinyurl, t.co, etc.) |

**Text Feature Extractor (24 Features):**

| Category | Pattern Examples |
|----------|-----------------|
| **Urgency Patterns** | "urgent", "immediately", "expires", "limited time", "act now" |
| **Threat Patterns** | "account suspended", "unauthorized access", "security breach" |
| **Credential Requests** | "verify your", "confirm your", "update password", "login" |
| **Financial Patterns** | "bank", "credit card", "prize", "refund", "payment" |
| **Action Requests** | "click here", "download", "open attachment", "visit link" |
| **Impersonation** | "dear customer", "support team", "official notice" |

**Total Phishing Features (deployed model): 1,496** (custom URL/text features + TF-IDF vocabulary, after pruning rare terms on the balanced dataset; `max_features` cap is 5,000)

---

## Slide 5.5: MODEL TRAINING PROCESS

### Training Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    MODEL TRAINING PIPELINE                       │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Step 1: Load  │    │ Step 2: Pre-  │    │ Step 3: Split │
│ Dataset from  │───▶│ process Text  │───▶│ Train/Test    │
│ HuggingFace   │    │ (Clean+Stem)  │    │ (80/20)       │
└───────────────┘    └───────────────┘    └───────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Step 4: Fit   │    │ Step 5: Train │    │ Step 6:       │
│ TF-IDF        │───▶│ Classifier    │───▶│ Evaluate on   │
│ Vectorizer    │    │ Model         │    │ Test Set      │
└───────────────┘    └───────────────┘    └───────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 7: Save Model Artifacts                                     │
│   - {model}_classifier.pkl (trained model)                       │
│   - {model}_vectorizer.pkl (TF-IDF vectorizer)                   │
│   - {model}_metadata.json (metrics & configuration)              │
└─────────────────────────────────────────────────────────────────┘
```

### Hyperparameter Configuration

**Logistic Regression (SMS):**
```python
LogisticRegression(
    max_iter=1000,      # Maximum iterations for convergence
    random_state=42,    # Reproducibility
    n_jobs=-1           # Use all CPU cores
)
```

**Random Forest (Voice Scam & Phishing):**
```python
RandomForestClassifier(
    n_estimators=100,   # Number of decision trees
    max_depth=20,       # Maximum tree depth
    random_state=42,    # Reproducibility
    n_jobs=-1           # Use all CPU cores
)
```

### Confidence Thresholds

| Model | Threshold | Rationale |
|-------|-----------|-----------|
| SMS Spam | 80% | Raised to reduce false positives on friendly messages |
| Voice Scam | 80% | Raised to reduce false positives |
| Phishing | 75% | Conservative to reduce false positives |

### Model Output Artifacts

```json
// Example: sms_metadata.json
{
  "model_type": "sms",
  "version": "1.0.0",
  "trained_at": "2026-01-20T13:38:58.040754",
  "algorithm": "logistic_regression",
  "metrics": {
    "accuracy": 0.9968,
    "precision": 0.9982,
    "recall": 0.9955,
    "f1": 0.9968,
    "roc_auc": 0.9999,
    "train_samples": 8720,
    "test_samples": 2180,
    "feature_count": 3000
  }
}
```

---

## Slide 5.6: VOICE PROCESSING PIPELINE

### Audio-to-Prediction Flow

```
┌──────────────────┐
│  Audio Input     │
│  (WAV/MP3/OGG)   │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  1. Audio Loading (PyDub)            │
│     - Convert to WAV format          │
│     - Normalize audio levels         │
│     - Sample rate: 16kHz             │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  2. Speech-to-Text (SpeechRecognition)│
│     - Google Speech Recognition API   │
│     - Noise reduction preprocessing   │
│     - Language: English               │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  3. Text Preprocessing               │
│     - Same pipeline as text models   │
│     - Lowercase, stemming, etc.      │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  4. Voice Scam Classification        │
│     - TF-IDF vectorization           │
│     - Random Forest prediction       │
│     - Confidence score calculation   │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  Output: {                           │
│    "transcription": "...",           │
│    "is_scam": true/false,            │
│    "confidence": 0.95,               │
│    "threat_indicators": [...]        │
│  }                                   │
└──────────────────────────────────────┘
```

---

## Slide 5.7: API ENDPOINTS

### FastAPI ML Service Endpoints

| Endpoint | Method | Model | Input | Output |
|----------|--------|-------|-------|--------|
| `/predict` | POST | Unified | `{"text": "..."}` | Spam probability |
| `/predict-sms` | POST | SMS | `{"text": "..."}` | SMS spam classification |
| `/predict-voice-scam` | POST | Voice | `{"text": "..."}` | Scam classification |
| `/predict-phishing-v2` | POST | Phishing | `{"text": "...", "url": "..."}` | Phishing classification |
| `/predict-auto` | POST | Auto-detect | `{"text": "..."}` | Auto-selects best model |
| `/batch-predict` | POST | Any | `{"messages": [...]}` | Batch predictions (max 100) |
| `/predict-voice` | POST | Audio | Audio file (multipart) | Transcription + analysis |

### Response Format Example

```json
{
  "is_spam": true,
  "confidence": 0.9234,
  "threat_level": "high",
  "threat_indicators": [
    "urgency_language",
    "suspicious_url",
    "credential_request"
  ],
  "model_used": "sms_classifier",
  "processing_time_ms": 45
}
```

---

## Slide 6: RESULT

### System Demo / Visualization

**Mobile App Screenshots:**
- Home Screen: Main scanning interface
- Scan Screen: Text input and voice recording
- Result Screen: Spam/Safe classification with confidence score
- History Screen: Past scans with filtering options
- Phishing Screen: URL and text phishing analysis

**Key Features Implemented:**
- Real-time text spam detection
- Voice message transcription and analysis
- Phishing URL detection with threat level
- Brand impersonation detection
- User authentication and profile management
- Scan history with statistics

### Deployed Model Performance (test-set metrics)

| Model | Algorithm | Accuracy | Precision | Recall | F1-Score | ROC-AUC |
|-------|-----------|----------|-----------|--------|----------|---------|
| **SMS Spam** | Logistic Regression | 99.68% | 99.82% | 99.55% | 99.68% | 0.9999 |
| **Voice Scam** | Random Forest | 100%* | 100% | 100% | 100% | 1.000 |
| **Phishing** | Random Forest | 80.95% | 82.74% | 77.99% | 80.30% | 0.8908 |

\* Voice accuracy is 100% on a small, balanced 1,600-sample dataset — likely optimistic; see Limitations.

### System Performance (approximate)

| Metric | Target | Observed |
|--------|--------|----------|
| Spam Detection Accuracy | > 95% | **99.68%** ✅ |
| Phishing Detection Accuracy | > 80% | **80.95%** ✅ (shipped knowingly; improving via feedback) |
| API Response Time | < 100ms | ~45ms |
| Voice Processing Time | < 2s | ~1.2s |

---

## Slide 7: DISCUSSION

### Key Findings

1. **Specialized per-channel models work well** - Using a dedicated classifier for each channel (SMS, voice, phishing) lets us tune the algorithm and features per problem, rather than forcing one model to do everything.

2. **TF-IDF remains effective for SMS spam** - Despite advances in deep learning, TF-IDF with traditional ML achieves strong results for short text classification, similar to Almeida et al. (2011) — our SMS model reaches 99.68% accuracy.

3. **URL feature extraction is critical for phishing** - Our custom URL + text feature extractors align with Mohammad et al. (2014). Phishing is the hardest channel; our deployed model reaches 80.95% accuracy and we improve it through the user feedback loop.

4. **Hybrid rule-based + ML improves explainability** - Unlike pure deep learning approaches, our hybrid method provides interpretable threat indicators to users.

5. **Voice transcription adds value** - Extending spam detection to voice messages addresses a gap in existing research, as most studies focus only on text.

### Comparison with Previous Research

| Aspect | Previous Work | Our System |
|--------|---------------|------------|
| Modality | Text only | Text + Voice |
| Platform | Desktop/Server | Mobile-first |
| Detection | Spam only | Spam + Phishing |
| Explainability | Black box | Interpretable indicators |
| Real-time | Batch processing | Real-time API |

---

## Slide 8: CONCLUSION

### Strengths of the Study

- Achieved 99.68% SMS spam detection accuracy, exceeding the 95% target
- Multi-modal support (text + voice) addresses market gap
- Mobile-first design provides accessible user experience
- Hybrid ML approach balances accuracy and explainability
- Comprehensive phishing detection with brand impersonation

### Limitations of the Study

- Currently optimized for English language only
- Voice transcription accuracy depends on audio quality
- Requires internet connection for ML inference
- Limited training data for Khmer language spam

### Significance of the Study

- Provides accessible cybersecurity tool for general users
- Demonstrates practical application of ML in mobile security
- Contributes to spam/phishing detection research with multi-modal approach
- Offers framework for future development and research

### Future Research

- Extend support for Khmer language detection
- Implement on-device ML for offline functionality
- Add real-time SMS/call screening integration
- Develop browser extension for web-based phishing protection
- Explore federated learning for privacy-preserving model updates

---

## References

1. Almeida, T. A., et al. (2011). Contributions to the study of SMS spam filtering. UCI Machine Learning Repository.

2. Sahami, M., et al. (1998). A Bayesian approach to filtering junk e-mail. AAAI Workshop on Learning for Text Categorization.

3. Mohammad, R. M., et al. (2014). Predicting phishing websites based on self-structuring neural network. Neural Computing and Applications.

4. Gupta, S., et al. (2021). Deep learning based spam detection using BERT. International Conference on Computing.

5. Vaswani, A., et al. (2017). Attention is all you need. Advances in Neural Information Processing Systems.

---

## Thank You

### Q&A

**Contact:**
- [Add team member emails]
- GitHub: [Add repository link]

---
