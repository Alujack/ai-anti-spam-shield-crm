# Defense Day — Screen Recording Flow

> **Use this while filming.** Hold this open on a second screen or print it.
> **Total target:** 14–15 minutes.
> **Companion doc:** [DEFENSE_DAY_FULL_REVIEW.md](DEFENSE_DAY_FULL_REVIEW.md) — read it first.

---

## Pre-Flight (do BEFORE you press record)

- [ ] Phone fully charged, on Wi-Fi, Do-Not-Disturb ON, brightness at max.
- [ ] App reinstalled fresh OR signed out, so the Splash → Login flow works.
- [ ] Test user logged in elsewhere has: 5+ past scans, 1 connected email account, 1 active alert, 1 active incident, 1 enabled playbook. Seed data if needed.
- [ ] Laptop tabs ready (for Act 5 ML walk-through):
  - `train_separate_models.py`
  - `algorithm_comparison.csv` (open in a viewer)
  - `trained_models/sms/sms_metadata.json`
  - `voice_scam_detector.py`
  - Production URL `https://aiscamshield.codes` in a browser tab
- [ ] Test phrases copied to phone clipboard, ready to paste:
  - Scam SMS: `"URGENT: Your account is locked. Verify now: bit.ly/3xR8sQp or your balance will be frozen in 24 hours."`
  - Phishing URL: `http://paypa1-secure-login.com/verify`
- [ ] Mic for voice-over working — test record 5 seconds, play back.
- [ ] Screen recorder running, mic enabled, microphone permission granted.
- [ ] Backup video on hand in case the live demo crashes.

---

## Recording Sequence

### ACT 1 — Intro & System Map (0:00 → 1:00)

| Shot | Capture | Voice-over | Time |
|------|---------|------------|------|
| 1.1 | Laptop screen showing `https://aiscamshield.codes` landing page hero. Slow scroll down. | *"Good afternoon. My project is AI Anti-Spam Shield — a four-channel scam protection platform deployed live at aiscamshield.codes."* | 0:00 – 0:20 |
| 1.2 | Open `DEFENSE_DAY_FULL_REVIEW.md` Section 2 system map. Hold still. | *"It has three components: a Flutter mobile app, a Node.js backend with PostgreSQL and Redis, and a Python FastAPI machine-learning service. Everything runs on DigitalOcean in Singapore."* | 0:20 – 0:45 |
| 1.3 | Cut to phone home screen, tap the AI Shield app icon. | *"Let me show it working end to end."* | 0:45 – 1:00 |

---

### ACT 2 — Onboarding & Home (1:00 → 2:00)

| Shot | Capture | Voice-over | Time |
|------|---------|------------|------|
| 2.1 | Splash screen — 2 sec animated shield. | *"On launch the app checks the cached JWT and routes you to login if you're not signed in."* | 1:00 – 1:10 |
| 2.2 | Login screen — type email + password, tap Sign In. | *"Authentication is JWT with bcrypt-hashed passwords, seven-day access token, thirty-day refresh."* | 1:10 – 1:30 |
| 2.3 | Home dashboard — show the personalised greeting and the six quick-action cards. Slow pan. | *"This is the home dashboard. Six entry points: email scan, URL check, analytics, threats, alerts, security dashboard — plus an inline text-and-voice scan box."* | 1:30 – 2:00 |

---

### ACT 3 — Core Scanning (2:00 → 6:00)

#### 3a. Text scan (2:00 → 3:30)

| Shot | Capture | Voice-over | Time |
|------|---------|------------|------|
| 3.1 | Paste the scam SMS into the home text field. | *"I'll paste a typical scam SMS — urgency language plus a shortened URL."* | 2:00 – 2:15 |
| 3.2 | Tap "Scan for Threats". Show the scanning animation. | *"The request goes to a BullMQ queue. The text-scan worker calls the FastAPI service, which runs a Logistic Regression on TF-IDF features."* | 2:15 – 2:35 |
| 3.3 | Result screen — red gradient, confidence percentage, threat indicators. | *"Result: spam, confidence above the 0.80 threshold. The indicators tell the user *why* it was flagged."* | 2:35 – 2:55 |
| 3.4 | Tap "This is spam" feedback. Toast confirms submission. | *"This is the feedback loop. Users tag results — admins approve them — and the ML service pulls approved samples back into the next retraining run."* | 2:55 – 3:15 |
| 3.5 | Tap "Report" — quick view of the pre-filled form, scroll. Back out. | *"Users can also file a formal scam report, which feeds the threats and incidents pipeline."* | 3:15 – 3:30 |

#### 3b. Voice scan (3:30 → 5:00)

| Shot | Capture | Voice-over | Time |
|------|---------|------------|------|
| 3.6 | Tap the microphone icon on the home screen. Permissions accepted. | *"Voice scanning is multi-modal."* | 3:30 – 3:40 |
| 3.7 | Record 5 seconds saying something scam-style — *"Hello, this is the bank. We need to verify your account immediately."* Stop recording. | *"Three signals combined: speech-to-text classified by the SMS model — that's 40 percent — wav2vec2 audio embeddings at 35 percent, and prosody features — speaking rate, pause structure, pitch range — at 25 percent."* | 3:40 – 4:15 |
| 3.8 | Scanning animation, then Result screen with transcription. | *"Result includes the transcription and the combined score."* | 4:15 – 4:40 |
| 3.9 | Tap back to home. | *"This is one of the unique pieces of the system — the prosody branch catches scam calls even when the words alone are ambiguous."* | 4:40 – 5:00 |

#### 3c. URL scan + Safe Link Warning (5:00 → 6:00)

| Shot | Capture | Voice-over | Time |
|------|---------|------------|------|
| 3.10 | Navigate to Phishing Scanner → URL tab. Paste the phishing URL. | *"For URLs we use a hybrid pipeline — a Random Forest classifier on 24 hand-crafted features plus rule-based heuristics for brand impersonation."* | 5:00 – 5:20 |
| 3.11 | Tap Scan. Show the red phishing-result screen, threat level, indicators. | *"This domain — paypa1 with a digit one — triggers the brand-impersonation heuristic and gets flagged as critical."* | 5:20 – 5:40 |
| 3.12 | Show the Safe Link Warning interstitial as it would appear in another context, or trigger it from a deep-link. | *"Whenever the app is about to open a flagged URL, the user sees this interstitial. They can cancel or proceed — we're a safety layer, not a jailer."* | 5:40 – 6:00 |

---

### ACT 4 — Email Auto-Scan (6:00 → 8:00)

| Shot | Capture | Voice-over | Time |
|------|---------|------------|------|
| 4.1 | Open Email Scanner from quick-action card. Show the list of connected accounts. | *"This is the email module. Users connect any IMAP mailbox — Gmail, Outlook, Yahoo, or custom — using an app password, which we encrypt at rest."* | 6:00 – 6:20 |
| 4.2 | Tap the connected Gmail account. Show Email Results screen → tab All. | *"The backend has a cron-style scheduler that runs every minute. For each account it checks the auto-scan interval and, if due, enqueues a job."* | 6:20 – 6:50 |
| 4.3 | Tap "Scan Now" to trigger a manual scan. WebSocket fires — show a toast / completion notification. | *"I'll trigger a manual scan. The worker connects via IMAP, fetches up to 100 emails, scans each one through the same ML pipeline, and emits a WebSocket event back to the app."* | 6:50 – 7:20 |
| 4.4 | Switch to Flagged tab. Show flagged emails. | *"These are the emails the model classified as spam or phishing — with the sender, subject, threat level, and confidence."* | 7:20 – 7:45 |
| 4.5 | Tap "Clean All Flagged" → confirm. Show success. | *"One tap moves all flagged emails to trash on the mail server itself. Optional — the user is always in control."* | 7:45 – 8:00 |

---

### ACT 5 — SOC Dashboard Tour (8:00 → 10:30)

Quick 30-second tour each. **Don't linger.**

| Shot | Capture | Voice-over | Time |
|------|---------|------------|------|
| 5.1 | Threats screen — filter by severity, tap one threat. | *"Threats — every detection across the system. Filterable by severity. I can resolve one with notes."* | 8:00 – 8:30 |
| 5.2 | Incidents screen — status filters. | *"Incidents group related threats. Status moves from open → investigating → contained → resolved."* | 8:30 – 8:55 |
| 5.3 | Alerts screen — acknowledge one. | *"Alerts. I'll acknowledge this one."* | 8:55 – 9:15 |
| 5.4 | Playbooks screen — toggle one on, tap Execute. | *"Playbooks are incident-response automations. Toggle to enable, execute manually with parameters, or auto-execute on a trigger."* | 9:15 – 9:45 |
| 5.5 | Network screen — start monitoring, show events feed. | *"Network monitoring captures HTTP requests, scans, auth attempts. Each event has a risk score."* | 9:45 – 10:10 |
| 5.6 | Behavior screen — pick 24h, tap Analyze. | *"And behaviour analysis runs anomaly detection over the user's recent activity."* | 10:10 – 10:30 |

---

### ACT 6 — History & Settings (10:30 → 11:30)

| Shot | Capture | Voice-over | Time |
|------|---------|------------|------|
| 6.1 | Open History from the top bar. Scroll through past scans. Filter spam-only. | *"Every scan is stored encrypted in the user's history. They can filter, view details, or delete."* | 10:30 – 11:00 |
| 6.2 | Open Settings. Edit name → save. Toggle dark mode. Tap About. Back. | *"Settings — profile edit, dark mode, change password, notifications, privacy policy, terms. Everything you'd expect."* | 11:00 – 11:30 |

---

### ACT 7 — ML Walk-through On Laptop (11:30 → 14:00)

**Switch the recording to the laptop screen.** This is where you win marks.

| Shot | Capture | Voice-over | Time |
|------|---------|------------|------|
| 7.1 | Open `train_separate_models.py`. Scroll to the preprocessing function. | *"Here's the training pipeline. Lowercase, strip URLs / emails / phone numbers, NLTK English stopwords, Porter stemmer. TF-IDF with one-to-three n-grams."* | 11:30 – 11:55 |
| 7.2 | Open `algorithm_comparison.csv`. Highlight the SMS rows. | *"We benchmarked Logistic Regression, Naive Bayes, and Random Forest on each dataset. For SMS, Logistic Regression won on F1 and ROC-AUC."* | 11:55 – 12:25 |
| 7.3 | Open `trained_models/sms/sms_metadata.json`. | *"Production SMS model: accuracy 99.68 percent, precision 99.82, recall 99.55, F1 99.68, ROC-AUC 0.9999 — on a 2 180-sample test set."* | 12:25 – 12:50 |
| 7.4 | Open `voice_scam_detector.py`, jump to line 61. Highlight the weights. | *"This is the voice fusion logic. Forty percent text via STT, thirty-five percent audio embeddings from wav2vec2, twenty-five percent prosody features. Weights are fixed — empirically chosen from scam-call literature — because the dataset is too small to learn them."* | 12:50 – 13:20 |
| 7.5 | Open `feedback_collector.py`. Scroll to the `/feedback/export` call. | *"And the continuous-learning loop: user feedback in the app → admin review → ML service exports approved samples → POST /retrain creates a new ModelVersion row with status training, then testing, then deployed."* | 13:20 – 13:55 |
| 7.6 | Back to slide / system map. | *"That closes the loop. The model gets better the more the system is used."* | 13:55 – 14:00 |

---

### ACT 8 — Honest Gaps & Roadmap (14:00 → 15:00)

**Stay confident. Owning gaps is a strength.**

| Shot | Capture | Voice-over | Time |
|------|---------|------------|------|
| 8.1 | Cut to a simple slide or hold on the system map. | *"Three honest limitations. One — the pipeline is English-only; Khmer SMS would not classify well. We plan to swap in a multilingual transformer like XLM-R."* | 14:00 – 14:20 |
| 8.2 | (same) | *"Two — model promotion after retraining is manual. We have the infrastructure but we don't yet run an automated A-B canary. That's the next sprint."* | 14:20 – 14:40 |
| 8.3 | (same) | *"Three — the voice classifier reports a hundred percent test accuracy on a small balanced dataset, which is almost certainly an overfit signal. We're collecting real-world voice samples through the feedback loop to validate."* | 14:40 – 15:00 |
| 8.4 | End card / app icon. | *"AI Anti-Spam Shield. Live in production at aiscamshield.codes. Thank you."* | 15:00 |

---

## Quick-Reference Cheat Sheet (carry while filming)

### Numbers you must recite cleanly
- **SMS:** Logistic Regression, 99.68% accuracy, ROC-AUC 0.9999, 10 900 samples.
- **Voice:** Random Forest, 100% (caveat), 1 600 samples, multi-modal 40/35/25.
- **Phishing:** Random Forest, 80.95% accuracy, ROC-AUC 0.8908, 2 100 samples.
- **Confidence threshold:** 0.80 (v1) / 0.75–0.70 (v3).
- **Architecture:** Flutter + Node/Express + PostgreSQL + Redis + Python FastAPI.
- **Queues:** 6 — text, voice, url, email, feedback, retraining.
- **API endpoints:** ~85 across 15 domains.
- **Mobile screens:** 29.

### Phrases to use
- *"Multi-modal fusion."*
- *"Continuous-learning loop with admin-approved feedback."*
- *"Production-deployed, not just a prototype."*
- *"Owned limitation, not hidden one."*

### Phrases to avoid
- *"Perfect"* — your voice metrics aren't perfect, they're overfit.
- *"AI"* used vaguely — say *"Logistic Regression on TF-IDF"* or *"Random Forest with TF-IDF"*.
- *"Real-time"* without qualifier — say *"queued asynchronously"* or *"WebSocket-pushed"*.

---

## If Something Breaks Mid-Demo

| Problem | Recovery |
|---------|----------|
| Phone loses Wi-Fi | Cut to backup video, voice-over continues. |
| Scan returns wrong result | *"Interesting — this borderline case sits below the 0.80 threshold. This is exactly the kind of sample our retraining loop is designed to learn from."* |
| Email scan times out | Skip to manual results screen, narrate the WebSocket flow without the live event. |
| App crashes | *"This is why we have automatic crash reporting in production — let me restart and continue."* Restart, continue from last shot. |

---

## After Recording

- [ ] Watch playback end-to-end at 1.0× speed. Check audio levels.
- [ ] Cut any awkward dead time at scene transitions (target 14:00 final).
- [ ] Add captions in Khmer OR English depending on panel.
- [ ] Export at 1080p, H.264, < 200 MB so it plays on any defense-room laptop.
- [ ] Bring it on a USB drive AND host on Google Drive AND have the live URL ready.

Good luck, Yan.
