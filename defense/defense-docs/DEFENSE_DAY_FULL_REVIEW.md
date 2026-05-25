# AI Anti-Spam Shield — Defense Day Full Review

> **Owner:** Yan Yoeurn — `yan@tarantulalabs.io`
> **Date:** 2026-05-25
> **Purpose:** Complete code-level inventory of every feature, the backend, the ML training pipeline, and a Q&A bank for the defense panel.
> **Scope of review:** Live state of code as of commit `aab26ea` on `main`.

---

## 0. How To Use This Document

1. **Section 2 — System Map** is your one-slide answer to "what did you build?"
2. **Section 3 — Mobile App Feature Inventory** is your demo script. Walk every screen in this order.
3. **Section 5 — ML Pipeline Deep Dive** is what judges will grill you on. Memorise the numbers; don't memorise the marketing.
4. **Section 7 — Judge Q&A Bank** has the 30 hardest questions and your honest answers.
5. **Section 8 — Known Gaps** is what you say *before* a judge says it. Owning a gap defuses it.

---

## 1. Elevator Pitch (30 seconds)

**AI Anti-Spam Shield** is a multi-channel scam protection platform. It scans **text messages, voice calls/recordings, URLs, and emails** in real time using machine-learning models, and gives users a SOC-style dashboard with **threats, incidents, alerts, playbooks, network monitoring, file scanning, and behavior anomaly detection**.

- **Mobile:** Flutter app (29 screens, Riverpod state).
- **Backend:** Node.js / Express + PostgreSQL + Redis + BullMQ queue workers.
- **ML Service:** FastAPI (Python) with TF-IDF + Logistic Regression / Random Forest classifiers, plus an in-progress v3 pipeline using HuggingFace transformers (DistilBERT, BERT-tiny).
- **Voice:** Multi-modal — speech-to-text (40%) + wav2vec2 audio embeddings (35%) + prosody features (25%).
- **Deployed:** DigitalOcean droplet (Singapore), HTTPS via Let's Encrypt at `aiscamshield.codes`, Docker Compose multi-service stack.

---

## 2. System Map

```
┌─────────────────────────┐   HTTPS/REST + WebSocket   ┌─────────────────────────┐
│   Flutter Mobile App    │ ◄────────────────────────► │   Node.js Backend       │
│   (Riverpod + Dio)      │      aiscamshield.codes    │   Express 5 / Socket.IO │
│   29 screens            │                            │   JWT auth, BullMQ      │
└─────────────────────────┘                            └────────┬────────┬───────┘
                                                                │        │
                                                       ┌────────▼──┐ ┌──▼─────────┐
                                                       │ PostgreSQL│ │   Redis    │
                                                       │  (Prisma) │ │ (queues +  │
                                                       │ 18 models │ │  cache)    │
                                                       └───────────┘ └────────────┘
                                                                │
                                                       ┌────────▼────────────────┐
                                                       │   ML Service (Python)   │
                                                       │   FastAPI               │
                                                       │   SMS / Voice / Phishing│
                                                       │   v1 (sklearn) +        │
                                                       │   v3 (HuggingFace)      │
                                                       └─────────────────────────┘
                                                                │
                                  ┌─────────────────────────────┴────────────────┐
                                  │ External: IMAP (Gmail/Outlook/Yahoo),        │
                                  │ Stripe, HuggingFace model hub                │
                                  └──────────────────────────────────────────────┘
```

### Production deploy
- Droplet `ubuntu-s-2vcpu-4gb-sgp1-01`, 4 GB RAM, 2 vCPU
- Nginx reverse proxy → Kong gateway → backend / model
- Let's Encrypt SSL, auto-renew
- 14 Docker services orchestrated via `docker-compose.prod.yml`
- 2 GB swap added after OOM cascade during initial deploy

---

## 3. Mobile App — Complete Feature Inventory

**Framework:** Flutter, Material 3, Riverpod 3.x, Dio, English UI.
**Base URL:** `https://aiscamshield.codes/api/v1`
**Theme:** Light + Dark with system toggle, persisted via `settings_provider`.
**Navigation:** Named routes + Navigator push for nested flows.

### 3.1 Authentication Flow (4 screens)

| # | Screen | Route | What it does |
|---|--------|-------|--------------|
| 1 | Splash | `/` | Checks stored JWT; routes to home or login. 2 s minimum. |
| 2 | Login | `/login` | Email + password → `POST /users/login`. |
| 3 | Register | `/register` | Name, email, phone, password → `POST /users/register`. |
| 4 | Change-password modal | (in settings) | `POST /users/change-password`. |

### 3.2 Main Dashboards (3 screens)

| # | Screen | Route | What user sees |
|---|--------|-------|----------------|
| 5 | Home | `/home` | Greeting, 6 quick-action cards, inline text-scan box, mic button, security tips. |
| 6 | Dashboard | `/dashboard` | Message-scan stats, phishing stats, report stats. Pulls from `GET /dashboard/statistics`. |
| 7 | Advanced Dashboard | `/advanced-dashboard` | 24h / 7d / 30d filters, export JSON. `GET /dashboard/advanced`. |

### 3.3 Core Scanning (5 screens)

| # | Screen | Route | What it does |
|---|--------|-------|--------------|
| 8 | Scanning (intermediate) | (pushed) | Animated shield + progress while scan runs. |
| 9 | Result (text/voice) | `/result` | Spam/safe verdict, confidence, indicators, feedback buttons, copy + report. |
| 10 | Phishing Scanner | `/phishing-scanner` | Tabs for Text and URL → `POST /phishing/scan-text` or `/phishing/scan-url`. |
| 11 | Phishing Result | `/phishing-result` | Threat level, indicators, recommendation, feedback. |
| 12 | Scan History | `/history` | Paginated list, filter by spam/safe, delete. `GET /messages/history`. |

### 3.4 Email Auto-Scan (4 screens)

| # | Screen | Route | What it does |
|---|--------|-------|--------------|
| 13 | Email Accounts | `/email-scanner` | List of connected mailboxes (Gmail / Outlook / Yahoo / custom IMAP). |
| 14 | Connect Email | (pushed) | Provider picker + IMAP credentials → `POST /email/connect`. |
| 15 | Email Results | (pushed) | Tabs: All / Flagged / Stats. Manual scan + clean-all-flagged. |
| 16 | Email Settings | (pushed) | Active toggle, auto-scan interval (off / 15m / 30m / 1h / 4h / 12h / 24h), disconnect. |

### 3.5 Reports (2 screens)

| # | Screen | Route | What it does |
|---|--------|-------|--------------|
| 17 | Create Report | `/create-report` | Type (spam/phishing/scam/fraud/other), content, URL, phone, sender. `POST /reports/create`. |
| 18 | My Reports | `/my-reports` | List of user's submissions with status, delete action. |

### 3.6 SOC Operations (6 screens)

| # | Screen | Route | What it does |
|---|--------|-------|--------------|
| 19 | Threats | `/threats` | Severity filters, statistics, resolve with notes. |
| 20 | Incidents | `/incidents` | Status filters (Open / Investigating / Resolved / Closed). |
| 21 | Alerts | `/alerts` | Active / Acknowledged / Resolved; acknowledge + resolve actions. |
| 22 | Playbooks | `/playbooks` | Toggle on/off, execute with parameters. |
| 23 | Network Monitor | `/network` | Start/stop monitoring, events feed, suspicious filter. |
| 24 | File Scan | `/file-scan` | Statistics, scan-ID lookup, upload (button labelled "Coming Soon"). |
| 25 | Behavior Analysis | `/behavior` | Anomaly list, timeframe selector, analyze trigger. |

### 3.7 Settings & Special (5 screens)

| # | Screen | Route | What it does |
|---|--------|-------|--------------|
| 26 | Settings | `/settings` | Profile edit, change password, theme, notifications, legal links, logout. |
| 27 | Privacy Policy | (pushed) | Static legal text. |
| 28 | Terms of Service | (pushed) | Static legal text. |
| 29 | Telegram Auto-Scan | (pushed) | Notification-access listener; scans incoming Telegram messages locally. |
| — | Safe Link Warning | (overlay) | Full-screen interstitial for suspicious URLs before opening in browser. |

### 3.8 Key Mobile Capabilities
- **Voice recording** via `record` package (AAC/MP3/WAV/FLAC).
- **Microphone permissions** with graceful fall-back to system settings.
- **iOS Home Screen widgets** via `WidgetService`.
- **Deep linking** — `aishield://open` from the landing page launches the app.
- **Telegram interception** — Android `NotificationListenerService` style; no backend call, fully on-device.
- **Safe-link interception** — every URL is checked against the phishing classifier before opening.
- **Haptic feedback** on threat alerts and record start/stop.
- **WebSocket** subscribes to `user:{userId}` room for live email-scan completion and job progress.

---

## 4. Backend — Architecture & APIs

### 4.1 Stack
- **Framework:** Express 5.2.1
- **DB:** PostgreSQL via Prisma 5.7.0 (18 models)
- **Cache & Queues:** Redis + BullMQ 5.66.5
- **Real-time:** Socket.IO 4.7.2
- **Auth:** JWT (7-day access, 30-day refresh), bcryptjs (10 salt rounds)
- **Validation:** Multer for uploads; placeholder for Joi
- **Docs:** Swagger UI at `/api-docs`
- **Logging:** Winston with daily-rotate, 6 log streams (combined / error / access / security / audit), retention 14–90 days.

### 4.2 API Surface (~85 endpoints across 15 domains)

**Auth (6):** register, login, profile, update profile, change password, admin delete user.
**Messages (10):** scan-text, scan-voice, history (list / get / delete), statistics, analyze, plus legacy CRUD.
**Phishing (7):** scan-text, scan-url, batch-scan, history (list / get / delete), statistics.
**Email (10):** connect, list accounts, statistics, account detail, disconnect, update settings, manual scan, results, flagged-only, clean.
**Files (4):** scan, statistics, get-by-id, quarantine.
**Reports (7):** create, my-reports, statistics, get / update / delete, admin list-all.
**Threats (4):** statistics, list, get, resolve.
**Incidents (5):** create, list, get, update, close.
**Alerts (5):** statistics, list, get, acknowledge, resolve.
**Playbooks (8):** list, execution stats, execution history, get, history-for, execute, auto-execute, toggle.
**Network (5):** start, stop, status, events, statistics.
**Behavior (3):** analyze, anomalies, history.
**Analytics (2):** dashboard, export.
**Feedback (7):** submit, pending (admin), stats, export-for-training (admin), my, review (admin), get.
**Subscriptions (3):** plans, checkout, webhook (Stripe).
**Jobs (4):** get job status, cancel job, all-queue stats, queue stats.

### 4.3 Database Schema — 18 Prisma Models

`User`, `ScanHistory`, `PhishingScanHistory`, `Report`, `ScanJob`, `UserFeedback`, `ModelVersion`, `EmailAccount`, `EmailScanResult`, `Threat`, `Incident`, `Alert`, `NetworkEvent`, `BehaviorLog`, `FileScan`, plus subscription / Stripe customer tables.

Critical fields:
- `ScanHistory.message` — encrypted before storage.
- `EmailAccount.password` — encrypted IMAP app password.
- `UserFeedback.includedInTraining` — flag for retraining pipeline.
- `ModelVersion.metrics` — JSON snapshot of {accuracy, precision, recall, F1} per deployed model.

### 4.4 Queue Workers (BullMQ)

| Queue | Concurrency | Limiter | Attempts | Notes |
|-------|-------------|---------|----------|-------|
| `text-scan` | 5 | 100/s | 3 | Cached by message hash. |
| `voice-scan` | 2 | 20/s | 2 | Heavy; base64 audio. |
| `url-scan` | 5 | — | 3 | Phishing URL classification. |
| `email-scan` | 2 | 10/s | 2 | IMAP IO-bound. |
| `feedback-processing` | — | — | — | Approved feedback → retraining bucket. |
| `model-retraining` | 1 | — | 1 | 10-min lock, min 50 approved samples. |

Plus a **`email.scheduler`** loop running every 60 s that enqueues jobs for any account whose `lastScanAt + autoScanInterval` is in the past.

### 4.5 Real-Time Events
- `user:{userId}` room — `email-scan:complete`, generic notifications.
- `job:{jobId}` room — `scan:progress` 10% → 30% → 70% → 100%.
- Authenticated via JWT in `socket.handshake.auth.token`.

### 4.6 External Integrations
- **IMAP** via `imapflow` for Gmail/Outlook/Yahoo/custom.
- **Stripe** for `Pro Monthly` / `Pro Yearly` checkout + webhook.
- **ML service** via Axios with `X-API-Key` header, 30 s timeout.
- **VirusTotal field** present on `FileScan` model (integration stub).

### 4.7 Security
- Helmet headers, CORS with credentials, in-memory rate limiter (5 tiers — auth 10/15min, api 100/15min, scan 50/hr, upload 20/hr, strict 5/15min).
- Audit log retains 90 days; security log retains 30 days.
- All passwords bcrypt-hashed; IMAP creds encrypted at rest.

---

## 5. ML Pipeline — Deep Dive (Defense-Critical)

This is the section judges will dig into. Memorise the **numbers**, the **algorithms**, and the **honest caveats**.

### 5.1 Three Specialised Classifiers

| Domain | Algorithm | Vectorizer | Features | Train time |
|--------|-----------|------------|----------|-----------|
| SMS / Text | **Logistic Regression** | TF-IDF (1-2 grams) | 3 000 | 3.01 s |
| Voice (dialogue text) | **Random Forest** | TF-IDF (1-3 grams) | 5 000 | 0.14 s |
| Phishing (URL+text) | **Random Forest** | TF-IDF (1-2 grams) | 1 496 | 0.11 s |

All three are pickled and loaded by `app/model/predictor.py` at FastAPI startup. Each has a `metadata.json` next to it with reported metrics.

### 5.2 Datasets (HuggingFace public corpora)

| Domain | Dataset | Total | Train | Test | Source |
|--------|---------|-------|-------|------|--------|
| SMS | `Deysi/spam-detection-dataset` | 10 900 | 8 720 | 2 180 | UCI + HF |
| Voice | `BothBosu/scam-dialogue` | 1 600 | 1 280 | 320 | HF (~50/50 balanced) |
| Phishing | `ealvaradob/phishing-dataset` (combined_reduced) | 2 100 | 1 680 | 420 | HF |

Optional extended pipeline can combine in `mshenoda/spam-messages` (~59 k) for SMS and three phishing sources (~30 k) — code path exists but production uses the small balanced sets.

### 5.3 Preprocessing Pipeline
Applied in `train_separate_models.py`:
1. Lowercase
2. Strip URLs, emails, phone numbers (replaced with tokens)
3. Strip special characters
4. NLTK English stopwords removed
5. Porter stemmer
6. Drop words ≤ 1 char

**Important caveat:** stopwords and stemmer are English-only. There is **no Khmer pipeline, no language detection, no multilingual tokenizer**. Khmer-language scam SMS would not be reliably classified.

### 5.4 Reported Test-Set Metrics

#### SMS — Logistic Regression
```
Accuracy:  0.9968   F1: 0.9968
Precision: 0.9982   Recall: 0.9955
ROC-AUC:   0.9999
```

#### Voice (dialogue) — Random Forest
```
Accuracy:  1.0000   F1: 1.0000
Precision: 1.0000   Recall: 1.0000
ROC-AUC:   1.0000
```
**Honest read:** 100% on a 320-sample test set drawn from the same HuggingFace split almost certainly indicates **dataset simplicity / train-test similarity**, not real-world capability. Be the first to say this; don't let a judge corner you.

#### Phishing — Random Forest
```
Accuracy:  0.8095   F1: 0.8030
Precision: 0.8274   Recall: 0.7799
ROC-AUC:   0.8908
```

#### Algorithm comparison (excerpt from `algorithm_comparison.csv`)

SMS:
| Algorithm | Acc | F1 | ROC-AUC | Train |
|-----------|------|------|---------|-------|
| Logistic Regression | 0.9446 | 0.9301 | 0.9867 | 18.3 s |
| Naive Bayes | 0.9209 | 0.9034 | 0.9797 | 0.40 s |
| Random Forest | 0.8947 | 0.8532 | 0.9716 | 9.62 s |

Phishing:
| Algorithm | Acc | F1 | ROC-AUC |
|-----------|------|------|---------|
| Logistic Regression | 0.7774 | 0.6646 | 0.8937 |
| Random Forest | 0.7565 | 0.6123 | 0.8792 |
| Naive Bayes | 0.5705 | 0.6483 | 0.7793 |

> The differences between "production" metrics (Section 5.4) and the comparison-table metrics come from feature-extraction tweaks (n-gram range, max_features). Be ready to explain this.

### 5.5 Confidence Thresholds
- v1 (`predictor.py`): single threshold **0.80**.
- v3 (`predictor_v3.py`): SMS **0.75**, Phishing **0.70**, Voice **0.75**.

### 5.6 Voice Pipeline — Multi-Modal

This is one of the most defensible / interesting parts of the project. Use it in the demo.

`voice_scam_detector.py` combines three signals:

| Signal | Weight | Module | What it captures |
|--------|--------|--------|------------------|
| Speech-to-text → classifier | 40% | Google Speech Recognition + SMS model | Words / phrases ("verify your account", "OTP", "urgent") |
| Audio embeddings | 35% | `audio_embeddings.py` — wav2vec2 | Raw acoustic patterns regardless of language |
| Prosody features | 25% | `prosody_analyzer.py` — librosa | Speaking rate, pause structure, pitch range — proven scam-call markers |

Final score = `0.40·text + 0.35·audio + 0.25·prosody`. Weights are **hardcoded**, not learned — be ready to explain why (justification: small dataset, picked empirically from literature on scam-call prosody).

### 5.7 URL / Phishing Pipeline
Hybrid:
1. **Rule-based heuristics** — regex patterns for urgency, credential bait, financial keywords.
2. **24-feature vector** per URL (length, TLD, IP-in-host, brand impersonation distance, presence of `@`, hyphens, suspicious subdomains, etc.).
3. **Random Forest** classifier on TF-IDF + the 24 features.

No third-party threat intel (no VirusTotal API call wired up; field exists on the model but isn't populated).

### 5.8 v3 (HuggingFace Transformer) Models
Loaded conditionally in `predictor_v3.py` when transformer weights are available:

| Domain | Primary Model | Backup |
|--------|---------------|--------|
| SMS | `mrm8488/bert-tiny-finetuned-sms-spam-detection` | `mariagrandury/roberta-base-finetuned-sms-spam-detection` |
| Phishing | `cybersectony/phishing-email-detection-distilbert_v2.4.1` | `ealvaradob/bert-finetuned-phishing` |
| Voice | Transfers from SMS model |  |

These are **pre-trained**, not trained from scratch in your project. Frame this honestly: "We benchmarked our scikit-learn models against state-of-the-art transformer baselines."

### 5.9 Continuous Learning Loop
`app/retraining/feedback_collector.py` + `scheduler.py`:

1. User taps "This is spam / This is safe" in the mobile result screen → `POST /feedback`.
2. Admin reviews via `PUT /feedback/{id}` → status = approved.
3. ML service pulls `GET /feedback/export?status=approved&includedInTraining=false`.
4. On `POST /retrain` (manual or weekly scheduler), the service:
   - Combines new approved feedback with base dataset.
   - Retrains the chosen model type.
   - Writes a `ModelVersion` row with new metrics.
   - Status: `training` → `testing` → `deployed` (with rollback path).

**Honest caveats** (volunteer these):
- No automatic A/B canary deployment.
- No model-drift detection.
- No hold-out validation before promoting.
- Retraining is **mostly manual** today.

---

## 6. Demo Day — Video Script (12–15 minutes)

A clean recording flow. Practice once end-to-end before recording.

### Act 1 — The Problem (1 min)
> "Scam SMS, phishing emails, and voice scam calls cost Cambodian users millions every year. Existing tools are siloed: telco SMS filters can't read your email, and email spam folders don't know about your phone calls. We built AI Anti-Spam Shield as a single, AI-first defence layer across all four channels."

Show: a screenshot of a real scam SMS, a phishing email, a fraudulent URL.

### Act 2 — Architecture (1 min)
Show the diagram from Section 2. Talk for 30 seconds:
> "Flutter mobile, Node.js backend with PostgreSQL and Redis, Python FastAPI service for the ML models, all deployed on DigitalOcean."

### Act 3 — Live App Walkthrough (8 min)

Recommended order (don't skip):

1. **Login** — 30 s
2. **Home dashboard** — point at the 6 quick-action cards.
3. **Text scan** — type a real scam line ("Your account is locked. Click here: bit.ly/abc to verify"). Show:
   - The progress animation.
   - The red Result screen with confidence percentage.
   - Tap "Report" → fill the form → submit.
   - Tap "This is spam" feedback button.
4. **Voice scan** — record a 5-second audio of a scam-style request. Show transcription + score.
5. **URL scan** — paste a known-phishing URL. Show the red Safe Link Warning interstitial.
6. **Email connect & scan** — connect a Gmail account (use app password). Wait for scheduler to fire OR trigger manual scan. Show Flagged tab with results.
7. **Threats / Incidents / Alerts** — quick tour of the SOC screens. Resolve one alert.
8. **Playbook** — toggle one on, execute against a fake threat.
9. **Network monitor** — start, show events feed.
10. **Behavior anomalies** — run an analysis on 24h window.
11. **History** — show paginated past scans.
12. **Settings** — theme toggle (light → dark), logout.

### Act 4 — ML / Training (3 min)
This is where you earn marks. Open your laptop and show:

1. `train_separate_models.py` — preprocessing pipeline.
2. `algorithm_comparison.csv` — open it, point to the chosen winners.
3. `sms_metadata.json` — read off the metrics.
4. `voice_scam_detector.py` — explain the 40/35/25 weighting.
5. `feedback_collector.py` + the `/feedback/export` endpoint — show the continuous-learning loop is wired end-to-end.

### Act 5 — Honest Limitations & Roadmap (1 min)
> "Three areas we're actively improving: (1) Khmer-language support — current pipeline is English-only; (2) automated A/B testing before promoting retrained models; (3) larger phishing dataset — current 80% accuracy isn't where we want to ship."

End on confidence: "The system is live in production right now at aiscamshield.codes."

---

## 7. Judge Q&A Bank — Top 30 Questions

### Architecture & engineering (Q1–Q10)

**Q1. Why Flutter and not native?**
A. Single codebase for iOS + Android halves engineering time. Performance is adequate — heavy work is offloaded to the backend. Riverpod gives strong compile-time-checked state.

**Q2. Why Express in 2026? Why not NestJS or Go?**
A. Team familiarity, mature ecosystem (Prisma, BullMQ, Socket.IO all first-class), and the bottleneck is the ML service not the API layer. Express handles tens of thousands of req/s; we are nowhere near that.

**Q3. Why PostgreSQL over MongoDB?**
A. Relational integrity matters here: a `Report` references a `User`, an `Incident` references a `Threat`, a `ScanHistory` belongs to a `User`. Joins are the natural query shape. JSON columns cover the few semi-structured fields.

**Q4. How do you handle scale?**
A. BullMQ workers are stateless and horizontally scalable. Postgres connection pooling via Prisma. Redis is the single bottleneck for queues but can be clustered. Currently single-node deploy; the architecture is ready to shard.

**Q5. What happens if the ML service is down?**
A. The Axios client errors out and the queue job retries with exponential backoff. The mobile app receives an error response, not a wrong answer. We chose to fail closed.

**Q6. Where are passwords stored?**
A. User passwords: bcrypt with 10 salt rounds. IMAP credentials: AES-encrypted at rest using an env-var key. Stripe handles all card data — we never see it.

**Q7. How does the user authenticate?**
A. JWT issued by `POST /users/login`. Access token 7 days, refresh 30 days. Token is sent in `Authorization: Bearer …` header and used on the WebSocket handshake.

**Q8. What's your CI/CD?**
A. Manual deploy script — pull on the droplet, `docker compose up -d`. We have a `.github/` folder ready for GitHub Actions; that's a Phase-2 item.

**Q9. How do you monitor production?**
A. Winston logs with 6 streams (combined, error, access, security, audit) on daily rotation. Health endpoint at `/health`. Prometheus / Grafana folders exist but aren't wired live. Honest answer.

**Q10. Why a 4 GB droplet? Wasn't there an OOM?**
A. Yes, on first deploy. Root cause was Prisma generate starting up under tight cgroup limits. We added 2 GB swap and bumped worker memory to 512 MB. Production has been stable since. We have monitoring on memory now.

### ML / data science (Q11–Q22) — **this is where you earn the marks**

**Q11. Why TF-IDF + Logistic Regression and not a transformer?**
A. Three reasons: (1) 100× smaller and faster, (2) on a 10 k-sample dataset the marginal accuracy gain from a transformer is tiny — we benchmarked, see `algorithm_comparison.csv`, (3) inference latency matters when the mobile UX expects sub-second scans. v3 transformer support is wired but used as a benchmark, not the primary path.

**Q12. 100% accuracy on voice — that's suspicious.**
A. Agree. Two factors: the BothBosu scam-dialogue dataset is small (1 600 rows) and balanced, and the train/test split is from the same source, so distributional shift is minimal. Production behaviour will be lower. We're collecting real-world voice samples through the feedback loop to validate.

**Q13. Why is phishing only 80%?**
A. Phishing is genuinely harder: emails, SMS, and URLs are heterogeneous and adversarial. The dataset combines three sources with different label semantics. We chose to ship at 80% and improve via user feedback rather than wait for a perfect model.

**Q14. Did you do cross-validation?**
A. No, single train/test split from the HuggingFace defaults. K-fold is on the roadmap. For a thesis-day answer: "we treat the public split as our hold-out; future work includes 5-fold CV to get tighter confidence intervals on the metrics."

**Q15. How do you handle class imbalance?**
A. Today: no explicit reweighting; we rely on the dataset being roughly balanced. Phishing is the most imbalanced and that's reflected in the lower accuracy. Adding class weights to Logistic Regression is a one-line fix on the roadmap.

**Q16. What features did you engineer?**
A. For text: TF-IDF n-grams 1–2 or 1–3, plus stopword removal and Porter stemming. For URLs: 24 hand-crafted features — length, TLD, IP-in-hostname, brand impersonation via Levenshtein distance, suspicious characters (`@`, multiple hyphens), suspicious subdomains.

**Q17. How does the voice classifier work end-to-end?**
A. Three parallel branches: (a) STT via Google Speech Recognition → SMS model; (b) wav2vec2 audio embeddings classifying acoustic patterns; (c) librosa prosody features — speaking rate, pause distribution, pitch range. Weighted 40/35/25, weights set empirically from scam-call prosody literature.

**Q18. Why those weights and not learn them?**
A. With 1 600 voice samples we'd overfit a learned weighting layer. Fixed weights from prior literature give a stronger inductive bias. Once we have ~10 k samples we can train an end-to-end fusion head.

**Q19. Does the model support Khmer?**
A. Honest answer: no. Stopwords and stemmer are English-only. Khmer SMS would score poorly. This is our biggest gap and is on the roadmap — likely via a multilingual transformer like XLM-R rather than re-engineering the English pipeline.

**Q20. How do you prevent the model from being gamed by adversaries?**
A. We don't have adversarial robustness testing. The feedback loop gives us a way to catch adversarial samples once users flag them. Open research problem; we're being honest about the gap.

**Q21. What's your false-positive rate? What about a legit GitHub email being flagged as spam?**
A. We hit this in production. Fix shipped: a `TRUSTED_SENDER_DOMAINS` allowlist in `email.service.js` bypasses the classifier for github.com, jobnet, etc. The classifier itself wasn't retrained; we added a safety net. Better long-term fix is a sender-reputation feature.

**Q22. How does retraining work? Who decides?**
A. Users submit feedback in-app → admin reviews and approves → ML service exports approved batch via `/feedback/export` → `POST /retrain` triggers a new model version with status `training`. A `ModelVersion` row is created. Today the promotion to `deployed` is manual. Automated promotion with shadow testing is in the design.

### Product / UX (Q23–Q27)

**Q23. Why a SOC dashboard for end users? Isn't that overkill?**
A. The threat / incident / alert / playbook screens are primarily for power users and organisations. For consumers, the Home + Result + Email tabs cover the use case. Selling to SMEs is the Pro-tier upsell.

**Q24. Why Telegram and not WhatsApp / Signal?**
A. Telegram exposes message text via Android `NotificationListenerService`; WhatsApp encrypts it more aggressively. We picked the channel where on-device interception was feasible.

**Q25. What happens if the user opens a flagged link anyway?**
A. We show a full-screen Safe Link Warning interstitial. User can tap "Open Anyway" — that's logged but allowed. We're a safety layer, not a jailer.

**Q26. How is user data protected?**
A. JWT for transport; scan messages encrypted before storing in `ScanHistory.message`; IMAP passwords encrypted. The audit log retains 90 days for compliance. There's no GDPR DSR endpoint yet — gap.

**Q27. What's the business model?**
A. Freemium. Free tier: text scans, basic phishing detection. Pro (Stripe checkout already wired): email auto-scan, file scanning, advanced analytics, playbooks. Pricing is `Pro Monthly` and `Pro Yearly` price IDs in env.

### Demonstration / robustness (Q28–Q30)

**Q28. Show me a failing case in the live demo.**
A. Pre-stage one. Pick a borderline message ("Your delivery is delayed, click here") — the model often returns 0.6–0.7 confidence which sits below the 0.80 threshold and is classified safe. Show that, then show what the v3 transformer would have done. It's honest and impressive.

**Q29. What did you learn building this?**
A. The biggest lesson was that **production reliability matters more than model accuracy**. We lost a day to an OOM crash on the droplet; we lost half a day to Kong image naming; we lost time to a detached git HEAD silently failing a deploy. The model was the easy part.

**Q30. What's next?**
A. (1) Khmer-language pipeline via multilingual transformers. (2) Automated A/B canary deploys for retrained models. (3) Real-world voice dataset collection. (4) Adversarial robustness testing. (5) Mobile app store submission (currently distributed via direct download from `aiscamshield.codes`).

---

## 8. Known Gaps — Volunteer These Before Judges Ask

| # | Gap | Why it exists | Mitigation / roadmap |
|---|-----|---------------|----------------------|
| 1 | **Voice 100% accuracy is suspicious** | Small balanced dataset, same-source train/test split. | Cross-validation; real-world voice samples via feedback. |
| 2 | **English-only NLP pipeline** | Stopwords + Porter stemmer are English. | Switch to multilingual transformer (XLM-R) for Khmer. |
| 3 | **Phishing accuracy only 80%** | Heterogeneous dataset (emails + URLs + SMS). | Domain-specific features; larger combined dataset. |
| 4 | **No cross-validation** | Used HuggingFace default splits. | Add 5-fold CV to the training script. |
| 5 | **No class-weight handling** | Datasets are mostly balanced; not critical for SMS / voice. | One-line `class_weight='balanced'` fix; do for phishing. |
| 6 | **Retraining promotion is manual** | Safe default; we didn't want auto-deploys yet. | Shadow / canary deployment. |
| 7 | **No model-drift monitoring** | Not yet built. | Add metric: rolling false-positive rate from feedback. |
| 8 | **No adversarial robustness testing** | Open research problem. | Generate adversarial samples (typos, character substitution) and benchmark. |
| 9 | **No A/B testing of model versions** | Tied to gap #6. | Wire `ModelVersion.status='testing'` to a shadow inference path. |
| 10 | **File scan upload not implemented** | UI button says "Coming Soon" — backend route exists. | One sprint to wire multipart upload → VirusTotal field. |
| 11 | **VirusTotal integration is a stub** | Field exists in schema, API call not wired. | Sprint task. |
| 12 | **CI/CD is manual** | Time. | GitHub Actions workflow. |
| 13 | **Prometheus / Grafana folders unused** | Time. | Wire metrics scraping; add basic dashboard. |
| 14 | **Health checks on workers fail** | They report "unhealthy" because compose does `curl :3000` but workers are queue consumers, not HTTP servers. Cosmetic only. | Fix healthcheck command per worker. |
| 15 | **No localised UI** | Khmer / English toggle not built. | Flutter `intl` package. |

---

## 9. Numbers You Should Be Able To Recite

> Memorise the rows in **bold** — they're the ones judges quote back at you.

- Codebase size: **3 sub-projects** (Flutter mobile, Node backend, Python ML service)
- Mobile screens: **29**
- Backend API endpoints: **~85**
- Prisma models: **18**
- BullMQ queues: **6** (text, voice, url, email, feedback, retraining)
- Production model accuracy — SMS: **99.68%**, Voice: 100% (caveat), Phishing: **80.95%**
- ROC-AUC — SMS: **0.9999**, Phishing: **0.8908**
- Datasets — SMS: **10 900** rows, Voice: **1 600**, Phishing: **2 100**
- Confidence threshold (v1): **0.80**
- Voice multi-modal weights: **text 40% / audio 35% / prosody 25%**
- TF-IDF feature counts: SMS **3 000**, Voice **5 000**, Phishing **1 496**
- JWT lifetime: **7 days access / 30 days refresh**
- Rate limits: auth **10 / 15 min**, scans **50 / hour**, API **100 / 15 min**
- Server: DigitalOcean **4 GB / 2 vCPU**, Singapore region
- Production URL: **https://aiscamshield.codes**

---

## 10. Demo-Day Pre-Flight Checklist

- [ ] Server is up — visit https://aiscamshield.codes in browser.
- [ ] `GET /api/v1/health` returns 200 from the droplet.
- [ ] A test user account is logged in on the demo phone.
- [ ] At least 5 historical scans are in the user's history (visible variety).
- [ ] An email account is connected and has done at least one successful auto-scan.
- [ ] At least one Threat, one Incident, one Alert exists in the DB (seed or run real data).
- [ ] At least one Playbook is enabled.
- [ ] Phone is charged, on Wi-Fi, in airplane-mode-off, brightness up.
- [ ] Screen-record app installed (iOS native or Android Scrcpy).
- [ ] Backup video pre-recorded in case live demo fails.
- [ ] Laptop has the codebase open in VS Code with these tabs pinned:
  - `train_separate_models.py`
  - `voice_scam_detector.py`
  - `algorithm_comparison.csv`
  - `sms_metadata.json`
  - `email.service.js`
  - The Prisma schema
- [ ] This document open on a second screen as a cue card.

---

## 11. One-Sentence Summary For The Panel

> **"AI Anti-Spam Shield is a four-channel — SMS, voice, URL, and email — AI scam protection platform with a Flutter mobile app, a Node.js backend, and a Python ML service running three specialised classifiers, all live in production at aiscamshield.codes."**

End of document.
