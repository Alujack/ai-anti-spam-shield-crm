# Defense Day — Screen Recording Flow

> **Use this while filming.** Hold it open on a second screen or print it.
> **Total target:** 14–15 minutes.
> **Companion doc:** [DEFENSE_DAY_FULL_REVIEW.md](DEFENSE_DAY_FULL_REVIEW.md) — read first.
>
> **Last updated:** 2026-05-25 — added safe-lab behavioral analyzer (Act 3c rewrite) and local Docker stack option.

---

## Pre-Flight (do BEFORE you press record)

### Device + room
- [ ] Phone fully charged, on Wi-Fi, Do-Not-Disturb ON, brightness at max.
- [ ] App reinstalled fresh OR signed out, so the Splash → Login flow works.
- [ ] Test user has: 5+ past scans, 1 connected email account, 1 active alert, 1 active incident, 1 enabled playbook. Seed if needed.
- [ ] Mic for voice-over working — test record 5 seconds, play back.
- [ ] Screen recorder running, mic enabled, microphone permission granted.
- [ ] Backup video on hand in case the live demo crashes.

### Backend the app talks to — pick ONE before filming
- **Option A — Production**: app stays pointed at `https://aiscamshield.codes`. Nothing to start. Use this if you want the panel to see a real live deployment.
- **Option B — Local Docker stack**: gives you control over data, can demo offline. Steps:
  1. `cd /opt/ai-anti-spam-shield-crm && docker compose up -d`
  2. Wait until `docker compose ps` shows all services healthy.
  3. Verify: `curl http://localhost:3000/health` returns 200.
  4. Point the app at your LAN IP (e.g. `http://192.168.50.88:3000`).

### Safe-Lab evil-twin demo URL (Act 3c — REQUIRED)
This is the killer demo. The fake-PayPal page needs HTTPS so iOS Safari/Chrome actually shows the camera prompt. Use a Cloudflare quick tunnel:

1. `brew install cloudflared` (one time).
2. `cloudflared tunnel --url http://localhost:3000` — keep this terminal open.
3. Copy the `https://*.trycloudflare.com` URL it prints.
4. Open `https://<that-url>/safe-lab-demo/` in your phone browser to verify it loads.
5. Paste the same URL into the AI Shield app's URL scanner — confirm you get the 17 behavior findings before you press record.

> **Why HTTPS matters:** iOS browsers refuse to expose `navigator.mediaDevices` over plain HTTP. Without HTTPS, the page can't even ask for the camera — the prompt won't render. The Cloudflare tunnel gives you a real Let's Encrypt cert in 5 seconds.

### Laptop tabs ready (for Act 7 — ML walk-through)
- `train_separate_models.py`
- `algorithm_comparison.csv`
- `trained_models/sms/sms_metadata.json`
- `voice_scam_detector.py`
- `app/intel/screenshot_analyzer.py` (safe-lab hooks — new)
- `app/detectors/phishing_detector.py` (free-hosting + trusted-domains — new)
- Production URL `https://aiscamshield.codes`

### Test phrases on phone clipboard
- Scam SMS: `"URGENT: Your account is locked. Verify now: bit.ly/3xR8sQp or your balance will be frozen in 24 hours."`
- Phishing URL: `http://paypa1-secure-login.com/verify`
- Evil-twin demo URL: `https://<your-cloudflared-host>/safe-lab-demo/`
- Free-hosting credential harvester: `https://newsbwebmail.weebly.com/`

---

## Recording Sequence

### ACT 1 — Intro & System Map (0:00 → 1:00)

| Shot | Capture | Voice-over | Time |
|------|---------|------------|------|
| 1.1 | Laptop screen showing `https://aiscamshield.codes` landing page hero. Slow scroll. | *"Good afternoon. My project is AI Anti-Spam Shield — a four-channel scam protection platform deployed live at aiscamshield.codes."* | 0:00 – 0:20 |
| 1.2 | Open the system map in `DEFENSE_DAY_FULL_REVIEW.md` § 2. Hold still. | *"Three components: a Flutter mobile app, a Node.js backend with PostgreSQL and Redis, and a Python FastAPI machine-learning service that includes a headless-Chromium safe lab for URL analysis. Everything runs on DigitalOcean Singapore — and the whole stack also runs locally in Docker."* | 0:20 – 0:45 |
| 1.3 | Cut to phone home screen, tap the AI Shield app icon. | *"Let me show it working end to end."* | 0:45 – 1:00 |

---

### ACT 2 — Onboarding & Home (1:00 → 2:00)

| Shot | Capture | Voice-over | Time |
|------|---------|------------|------|
| 2.1 | Splash screen — 2 sec animated shield. | *"On launch the app checks the cached JWT and routes to login if not signed in."* | 1:00 – 1:10 |
| 2.2 | Login screen — type email + password, tap Sign In. | *"JWT auth with bcrypt-hashed passwords. Seven-day access, thirty-day refresh."* | 1:10 – 1:30 |
| 2.3 | Home dashboard — show greeting and six quick-action cards. Slow pan. | *"Home dashboard: six entry points — email scan, URL check, analytics, threats, alerts, security dashboard — plus an inline text-and-voice box."* | 1:30 – 2:00 |

---

### ACT 3 — Core Scanning (2:00 → 6:30)

#### 3a. Text scan (2:00 → 3:00)

| Shot | Capture | Voice-over | Time |
|------|---------|------------|------|
| 3.1 | Paste the scam SMS into the home text field. Tap "Scan for Threats". | *"I'll paste a typical scam SMS — urgency plus a shortened URL. The request goes to a BullMQ queue. The text-scan worker calls the FastAPI service, which runs Logistic Regression on TF-IDF features."* | 2:00 – 2:25 |
| 3.2 | Result screen — red gradient, confidence %, threat indicators. | *"Spam, above the 0.80 threshold. The indicators tell the user *why* it was flagged."* | 2:25 – 2:40 |
| 3.3 | Tap "This is spam" feedback, toast confirms. Then tap "Report", scroll the pre-filled form, back out. | *"Feedback loop: users tag results, admins approve, the ML service pulls approved samples back into the next retraining run. Users can also file a formal scam report — that feeds the threats and incidents pipeline."* | 2:40 – 3:00 |

#### 3b. Voice scan (3:00 → 4:00)

| Shot | Capture | Voice-over | Time |
|------|---------|------------|------|
| 3.4 | Tap the mic icon on home. Permissions accepted. Record 5 sec: *"Hello, this is the bank. We need to verify your account immediately."* Stop. | *"Voice scanning is multi-modal. Three signals fused: speech-to-text classified by the SMS model at 40 percent, wav2vec2 audio embeddings at 35 percent, and prosody features — speaking rate, pauses, pitch — at 25 percent."* | 3:00 – 3:35 |
| 3.5 | Result screen with transcription and combined score. Tap back. | *"Result includes the transcription and the fused score. The prosody branch catches scam calls even when the words alone are ambiguous."* | 3:35 – 4:00 |

#### 3c. URL scan + Safe-Lab Behavioral Analysis (4:00 → 6:30) — **KILLER ACT**

| Shot | Capture | Voice-over | Time |
|------|---------|------------|------|
| 3.6 | Navigate to Phishing Scanner → URL tab. Paste the simple phishing URL `paypa1-secure-login.com`. Tap Scan. | *"For URLs the first layer is a hybrid pipeline — a Random Forest classifier on 24 hand-crafted features, plus rule heuristics for brand impersonation, free-hosting abuse, and credential-harvest tokens."* | 4:00 – 4:25 |
| 3.7 | Show the red result screen — threat level, indicators, "the digit 1 swap is a typosquat for paypal." | *"This domain — paypa1 with a digit one — gets flagged as critical brand impersonation."* | 4:25 – 4:40 |
| 3.8 | Back to URL scanner. Paste the **evil-twin demo URL** (`https://<cloudflared>/safe-lab-demo/`). Tap Scan. **Show the loading animation — ~7 seconds.** | *"But static URL patterns only get you so far. For deeper analysis we open the URL in an isolated headless Chromium sandbox — what we call the safe lab — and watch what the page actually does at runtime."* | 4:40 – 5:00 |
| 3.9 | Show the result card — verdict CRITICAL 90%, **screenshot of the rendered phishing page** displayed inline. | *"Within nine seconds we have a rendered screenshot, the page title, and a behavior log."* | 5:00 – 5:20 |
| 3.10 | Scroll the "Safe-Lab Behavior" section to the **"What the page tried to do"** bullets. Hold on the list for 5 seconds. | *"Seventeen distinct malicious behaviors caught in a single scan: the page asked for camera and microphone access, requested screen recording, asked for location, tried to read the clipboard, tried to overwrite the clipboard with an attacker's crypto wallet address, posted credit-card data in cleartext to an external collector, auto-triggered a fake PDF download, installed a service worker for persistence, read document.cookie for session theft, exfiltrated data via sendBeacon, opened a WebRTC peer connection — that's used to leak the user's real IP behind a VPN — probed for an installed crypto wallet, and fingerprinted the browser. None of that is visible to the user in their normal browser."* | 5:20 – 6:00 |
| 3.11 | Open the same evil-twin URL in the phone's regular browser. Show it looks like a normal PayPal login — countdown banner, neat form, trust badges. | *"This is what the user sees when they tap the link. A polished fake PayPal page. No warning. Maybe the auto-download offer slips through, but everything else is silent — iOS Safari hides it. Our safe lab is the only thing that sees the truth."* | 6:00 – 6:20 |
| 3.12 | Back to app result screen — point at the "PHISHING — CRITICAL — 90%" header. | *"That's our verdict. The user is told before they type a single character."* | 6:20 – 6:30 |

> **Calibration check on the day**: do a dry-run scan of `https://www.google.com` first — confidence should be 100% safe. Then `https://newsbwebmail.weebly.com/` — should be MEDIUM phishing 55%. Then the evil-twin — CRITICAL 90%. If any of those is wrong, restart the ml-service container.

---

### ACT 4 — Email Auto-Scan (6:30 → 8:00)

| Shot | Capture | Voice-over | Time |
|------|---------|------------|------|
| 4.1 | Open Email Scanner from the quick-action card. Show connected accounts list. | *"Email module. Users connect any IMAP mailbox — Gmail, Outlook, Yahoo, custom — using an app password, encrypted at rest."* | 6:30 – 6:50 |
| 4.2 | Tap the connected Gmail account. Show Email Results → tab All. | *"The backend has a cron-style scheduler that runs every minute. For each account it checks the auto-scan interval and, if due, enqueues a job."* | 6:50 – 7:15 |
| 4.3 | Tap "Scan Now". WebSocket fires — show toast / completion. | *"I'll trigger a manual scan. The worker connects via IMAP, fetches up to 100 emails, runs each through the same ML pipeline, and emits a WebSocket event back to the app."* | 7:15 – 7:40 |
| 4.4 | Switch to Flagged tab. Show flagged emails. Tap "Clean All Flagged" → confirm. | *"These are the ones the model classified as spam or phishing. One tap moves all flagged emails to trash on the mail server. The user is always in control."* | 7:40 – 8:00 |

---

### ACT 5 — SOC Dashboard Tour (8:00 → 10:00)

Quick 25-second tour each. **Don't linger.**

| Shot | Capture | Voice-over | Time |
|------|---------|------------|------|
| 5.1 | Threats screen — filter by severity, tap one. | *"Threats — every detection across the system. Filterable by severity. I can resolve one with notes."* | 8:00 – 8:25 |
| 5.2 | Incidents screen — status filters. | *"Incidents group related threats. Open → investigating → contained → resolved."* | 8:25 – 8:45 |
| 5.3 | Alerts screen — acknowledge one. | *"Alerts. I'll acknowledge this one."* | 8:45 – 9:00 |
| 5.4 | Playbooks screen — toggle one on, tap Execute on the Phishing Attack Response playbook. | *"Playbooks are automated incident-response runbooks. When a phishing threat is confirmed, this playbook blocks the sender, quarantines the message, alerts users, blocks the URLs, and opens an incident — six steps in seconds, no human in the loop."* | 9:00 – 9:30 |
| 5.5 | Network screen — start monitoring, show events feed. | *"Network monitoring captures HTTP requests, scans, auth attempts. Each event scored."* | 9:30 – 9:45 |
| 5.6 | Behavior screen — pick 24h, tap Analyze. | *"And behaviour analysis runs anomaly detection over the user's recent activity."* | 9:45 – 10:00 |

---

### ACT 6 — History & Settings (10:00 → 10:30)

| Shot | Capture | Voice-over | Time |
|------|---------|------------|------|
| 6.1 | Open History from top bar. Scroll past scans, filter spam-only. | *"Every scan stored encrypted in the user's history."* | 10:00 – 10:15 |
| 6.2 | Open Settings. Edit name → save. Toggle dark mode. Back. | *"Settings — profile edit, dark mode, change password, notifications, privacy, terms."* | 10:15 – 10:30 |

---

### ACT 7 — ML Pipeline + Safe-Lab Walk-through On Laptop (10:30 → 13:15)

**Switch the recording to the laptop screen.** This is where you win marks.

| Shot | Capture | Voice-over | Time |
|------|---------|------------|------|
| 7.1 | Open `train_separate_models.py`, scroll to preprocessing. | *"Training pipeline. Lowercase, strip URLs / emails / phone numbers, NLTK English stopwords, Porter stemmer. TF-IDF with one-to-three n-grams."* | 10:30 – 10:55 |
| 7.2 | Open `algorithm_comparison.csv`, highlight SMS rows. | *"We benchmarked Logistic Regression, Naive Bayes, and Random Forest on each dataset. SMS: Logistic Regression won on F1 and ROC-AUC."* | 10:55 – 11:20 |
| 7.3 | Open `trained_models/sms/sms_metadata.json`. | *"Production SMS model: 99.68 percent accuracy, ROC-AUC 0.9999, on a 2 180-sample test set."* | 11:20 – 11:40 |
| 7.4 | Open `voice_scam_detector.py`, jump to fusion weights. | *"Voice fusion: 40 percent text via STT, 35 percent wav2vec2 audio embeddings, 25 percent prosody. Weights are fixed — empirically chosen from scam-call literature — because the dataset is too small to learn them."* | 11:40 – 12:05 |
| 7.5 | Open `app/detectors/phishing_detector.py`. Scroll to `FREE_HOSTING_DOMAINS` + `TRUSTED_DOMAINS`. | *"URL detector. We maintain lists of free-hosting platforms commonly abused for phishing, and trusted domains for the brands attackers impersonate most. A subdomain like `newsbwebmail` on weebly.com hits the credential-harvest rule and gets a 0.6 score."* | 12:05 – 12:30 |
| 7.6 | Open `app/intel/screenshot_analyzer.py`. Scroll to `_SAFE_LAB_HOOKS`. | *"This is the safe lab. Before every page load we inject JavaScript that wraps the sensitive navigator APIs — getUserMedia, geolocation, clipboard, serviceWorker, sendBeacon, ethereum, RTCPeerConnection — so when a phishing page calls them, the call is recorded and silently rejected. Plus Playwright event listeners catch downloads, dialogs, redirect chains, and outbound script origins."* | 12:30 – 12:55 |
| 7.7 | Open `feedback_collector.py`, scroll to `/feedback/export`. | *"Continuous-learning loop: user feedback in the app → admin review → ML service exports approved samples → POST /retrain creates a new ModelVersion row, status training → testing → deployed."* | 12:55 – 13:15 |

---

### ACT 8 — Honest Gaps & Roadmap (13:15 → 14:15)

**Stay confident. Owning gaps is a strength.**

| Shot | Capture | Voice-over | Time |
|------|---------|------------|------|
| 8.1 | Cut to a simple slide or hold on the system map. | *"Three honest limitations. One — the text and voice pipelines are English-only; Khmer SMS would not classify well. We plan to swap in a multilingual transformer like XLM-R."* | 13:15 – 13:35 |
| 8.2 | (same) | *"Two — the safe-lab analysis adds about seven seconds of latency on first scan. We mitigate with Redis caching by URL hash, one-hour TTL, so re-scans of the same URL come back in under fifty milliseconds. Cold scans still take seven to ten seconds; that's the cost of opening the page in a real browser."* | 13:35 – 13:55 |
| 8.3 | (same) | *"Three — the voice classifier reports a hundred percent test accuracy on a small balanced dataset, which is almost certainly an overfit signal. We're collecting real-world voice samples through the feedback loop to validate."* | 13:55 – 14:15 |

---

### ACT 9 — Close (14:15 → 14:30)

| Shot | Capture | Voice-over | Time |
|------|---------|------------|------|
| 9.1 | End card / app icon. | *"AI Anti-Spam Shield. Live in production at aiscamshield.codes. Mobile, backend, ML, and safe lab — all containerized, all running. Thank you."* | 14:15 – 14:30 |

---

## Quick-Reference Cheat Sheet (carry while filming)

### Numbers you must recite cleanly
- **SMS:** Logistic Regression, 99.68% accuracy, ROC-AUC 0.9999, 10 900 samples.
- **Voice:** Random Forest, 100% (overfit caveat), 1 600 samples, multi-modal 40/35/25.
- **Phishing (static):** Random Forest, 80.95% accuracy, ROC-AUC 0.8908, 2 100 samples.
- **Confidence thresholds:** 0.80 (text v1) / 0.75–0.70 (text v3) / **0.55 (URL deep)**.
- **Safe lab:** ~9s cold scan, ~36ms cached, **17 behavior categories** detected.
- **Architecture:** Flutter + Node/Express + PostgreSQL + Redis + Python FastAPI + headless Chromium.
- **Queues:** 6 — text, voice, url, email, feedback, retraining.
- **API endpoints:** ~85 across 15 domains.
- **Mobile screens:** 29.
- **Playbooks:** 6 incident-response runbooks (malware, intrusion, phishing, DDoS, brute-force, data-exfil).

### Safe-Lab — 17 behavior categories (memorize these for Act 3c)
1. Camera / microphone request (getUserMedia)
2. Screen capture request (getDisplayMedia)
3. Geolocation request
4. Notification permission prompt
5. Clipboard read (steals copied 2FA/wallet addresses)
6. Clipboard write (crypto wallet address swap)
7. Cross-origin form POST (cleartext or different host)
8. Hidden iframes (1×1 / display:none)
9. Auto-triggered download (drive-by malware)
10. Popup dialogs (alert/confirm/prompt — scareware)
11. Service-worker registration (persistence after tab close)
12. Push subscription (delivers fake alerts later)
13. document.cookie read (session-token theft)
14. sendBeacon exfiltration (runs even after page unload)
15. WebRTC peer connection (leaks real IP behind VPN)
16. window.ethereum probe (crypto wallet drainer)
17. Browser fingerprinting (canvas / battery / audio)

### Phrases to use
- *"Safe lab"* / *"isolated headless Chromium sandbox"* / *"behavioral analysis"*
- *"Multi-modal fusion."*
- *"Static URL patterns plus runtime behavioral observation."*
- *"Continuous-learning loop with admin-approved feedback."*
- *"Production-deployed, not just a prototype."*
- *"Owned limitation, not hidden one."*

### Phrases to avoid
- *"Perfect"* — your voice metrics aren't perfect, they're overfit.
- *"AI"* used vaguely — say *"Logistic Regression on TF-IDF"* or *"Random Forest with TF-IDF"* or *"behavioral observation in headless Chromium"*.
- *"Real-time"* without qualifier — say *"queued asynchronously"* or *"WebSocket-pushed"* or *"under 50 milliseconds cached"*.
- *"Sandbox"* without explaining — always pair with *"isolated Chromium"* or *"headless browser"*.

---

## If Something Breaks Mid-Demo

| Problem | Recovery |
|---------|----------|
| Phone loses Wi-Fi | Cut to backup video, voice-over continues. |
| Scan returns wrong result | *"Interesting — this borderline case sits below the 0.55 threshold. This is exactly the kind of sample our retraining loop is designed to learn from."* |
| Email scan times out | Skip to manual results screen, narrate the WebSocket flow without the live event. |
| App crashes | *"This is why we have automatic crash reporting in production — let me restart and continue."* Restart, continue from last shot. |
| **Cloudflare tunnel URL is dead** | Switch to local LAN URL `http://<your-lan-ip>:3000/safe-lab-demo/`. Camera prompt won't fire on iOS but the scanner still catches all 17 behaviors — narrate that *"iOS Safari blocks auto-fired camera requests over HTTP, but our scanner catches the API call regardless. That's the whole point of the safe lab — it sees what Safari hides."* |
| **Safe-lab scan returns 0 behaviors** | The ml-service container probably needs a restart. `docker compose restart ml-service` and wait 15 seconds. While it warms up, narrate the static URL detection result instead. |
| **Playbook screen errors** | Already fixed (response-shape mismatch). If it re-appears, screenshot the bug and skip Act 5.4 — narrate from the slide instead. |

---

## After Recording

- [ ] Watch playback end-to-end at 1.0× speed. Check audio levels.
- [ ] Cut any awkward dead time at scene transitions (target 14:30 final).
- [ ] **Verify the evil-twin findings list is readable** — if the camera blurs it, re-shoot Act 3.10 with phone held steadier.
- [ ] Add captions in Khmer OR English depending on panel.
- [ ] Export at 1080p, H.264, < 200 MB so it plays on any defense-room laptop.
- [ ] Bring it on a USB drive AND host on Google Drive AND have the live URL ready.
- [ ] **Kill the cloudflared tunnel after recording** — `Ctrl-C` in that terminal — so the demo URL doesn't stay public.

Good luck, Yan.
