# DEFENSE PREPARATION CHECKLIST
## AI Anti-Spam Shield — Year 4 Project Practicum

This document is your **defense-day prep checklist**. It covers three things:
1. The exact screenshots you need to capture from your app
2. The video demo flows to record
3. An honest review of your project — strengths, weaknesses, and risks

Read it once, do the action items at the bottom, and you're defense-ready.

---

# TABLE OF CONTENTS

1. Screenshots You Need to Capture
2. Video Demo Capture Plan
3. Honest Project Review
4. Final Action Items

---

# SECTION 1 — SCREENSHOTS YOU NEED TO CAPTURE

Your report has **7 placeholder boxes** that need real screenshots. You can also add 2-3 extras to make the report stronger.

## 1.1 Required (must replace these 7 placeholders)

| # | Screen | What must be visible | Mobile app route |
|---|---|---|---|
| **Fig 6** | Home Screen | Greeting, scan-count widget, threat-distribution chart, recent activity list | `dashboard/` or `home/` |
| **Fig 7** | Scan Screen | Text input field with sample suspicious message **OR** voice-record button | `scan/` |
| **Fig 8** | Result Screen | Big red SPAM verdict, confidence %, threat-level chip (HIGH), list of triggered indicators | `result/` |
| **Fig 9** | Phishing URL Scan | URL input + result card with threat indicators, URL features (HTTPS, suspicious TLD, etc.) | `phishing/` |
| **Fig 10** | Email Accounts | List of connected IMAP accounts with scan status, last-scan time | `email/email_accounts_screen.dart` |
| **Fig 11** | Flagged Emails | List of detected phishing emails with subject/sender, **bulk-clean button visible** | `email/email_results_screen.dart` |
| **Fig 12** | Settings / Subscription | Pro/Enterprise paywall, plan comparison, Stripe-checkout button | `settings/` |

## 1.2 Recommended Extras (optional but impressive)

| Screen | Why it matters | Source |
|---|---|---|
| Login + Register | Proves auth works | `auth/` |
| History with Filter | Shows persistent storage | `history/` |
| Behavior Analytics | Shows admin features | `behavior/` |
| Safe-Link Warning | Shows your interception feature | `safe_link/safe_link_warning_screen.dart` |
| Network Monitor | Shows real-time WebSocket | `network/network_screen.dart` |
| Playbook / Incidents | Shows admin layer | `playbooks/` or `incidents/` |

## 1.3 How to Take Good Screenshots

- **Use a real device**, not the emulator (judges spot emulator chrome)
- **Portrait orientation** for phone screens
- **Pre-fill realistic test data** before screenshotting — never show empty states
- **Light theme** for printing in the docx — dark theme prints muddy
- **PNG format**, named clearly: `home_screen.png`, `result_spam.png`, etc.
- Save them to `defense/defense-docs/report/figures/` then drag-drop directly over the placeholders in Word
  - OR send them to me and I'll wire them in

## 1.4 Test Data to Pre-Fill Before Screenshotting

| Screen | Sample input |
|---|---|
| Scan SMS | `URGENT: Your ABA account is suspended. Verify now at http://bit.ly/aba-verify or your account will be locked in 24 hours.` |
| Phishing URL | `http://login-aba-mobile.tk/verify` |
| Result Screen | Use the SMS above to produce the result — show HIGH threat |
| Email Results | Pre-seed 3-4 fake flagged emails with subjects like "Your bank account verification required" |

---

# SECTION 2 — VIDEO DEMO CAPTURE PLAN

Judges typically expect a **2–3 minute demo video** showing the system in action. Don't try to show everything — pick the 5 flows that prove your accuracy claims and feature breadth.

## 2.1 Recommended Demo Script (~2:30 total)

### Flow 1 — SMS Spam Detection ⭐ your hero metric (30 sec)

```
1. Open app → Home screen (2s)
2. Tap "Scan Text"
3. Paste pre-prepared spam SMS:
   "URGENT: Your ABA account is suspended.
    Verify now at http://bit.ly/aba-verify or
    your account will be locked in 24 hours."
4. Tap Scan
5. Result appears: SPAM, 99.2% confidence, HIGH threat
6. Show triggered indicators:
   - urgency_language
   - suspicious_url
   - credential_request
   - brand_impersonation
```

**This is your strongest demo** — show it first, linger on the 99% confidence number.

### Flow 2 — Voice Scam Detection ⭐ unique feature (40 sec)

```
1. Tap Voice Scan
2. Hit record button
3. Speak (or play pre-recorded audio):
   "Hello sir, this is from ACLEDA security department.
    We detected suspicious activity. Please verify your
    PIN immediately to prevent your account from being closed."
4. Show real-time transcription appearing
5. Result: SCAM, 98.7% confidence, list of indicators
```

**Pre-record this audio** so you don't have to perform live during defense.

### Flow 3 — Phishing URL (20 sec)

```
1. Tap Phishing Scan
2. Paste: "http://login-aba-mobile.tk/verify"
3. Result: PHISHING, threat indicators:
   - suspicious_tld (.tk)
   - brand_impersonation (ABA)
   - credential_keyword
   - no_https
```

### Flow 4 — Email Inbox Scanning ⭐ the impressive one (40 sec)

```
1. Tap Email → Email Accounts
2. Show one connected Gmail account
3. Tap "Trigger Scan" — show progress indicator
4. Navigate to Flagged Emails list
5. Show 3-4 detected phishing emails with subjects
6. Tap "Clean Flagged" → bulk delete to trash
7. Confirmation toast
```

### Flow 5 — Real-Time WebSocket Alert (20 sec)

```
1. Have a second device / web tester submit a spam scan
2. Show your demo phone receiving the push notification
3. Tap notification → opens straight to result screen
```

## 2.2 Recording Tools

| Tool | Best for |
|---|---|
| **Android**: built-in screen recorder (Quick Settings) | Pixel / Samsung phones |
| **iOS**: Control Center → Screen Recording | iPhone |
| **scrcpy** (Mac/Linux) | High-quality Android mirroring + recording |
| **OBS Studio** | Final editing, adding captions, splicing flows together |

## 2.3 Demo Tips

- **Don't talk over the video** — just play silently and narrate in person
- **Add subtle text overlays** ("Step 1: User enters suspicious SMS")
- **Total length under 3 minutes** — judges will stop watching after that
- **Test playback on the projector** before defense day (laptops sometimes don't push audio)
- **Have backup**: PDF screenshots of each flow on a USB stick in case video fails
- **Disable notifications** on the demo device — incoming messages mid-demo are awkward
- **Pre-stage data**: have the spam SMS already copied to clipboard, accounts already connected

## 2.4 What NOT to Show in the Demo

- Real Cambodian phone numbers (privacy)
- Your actual email password (use a test account)
- Empty states (always pre-fill)
- Debug menus or developer overlays
- Slow loading screens (cut these out in editing)

---

# SECTION 3 — HONEST PROJECT REVIEW

This is my honest assessment after reading your full codebase, report, and defense materials.

## 3.1 Strengths (lead with these)

1. **Real production architecture** — not a notebook script. Microservices, queue, gateway, WebSocket, Docker — this is rare at undergraduate level and judges will notice.

2. **Three modalities under one app** — SMS + voice + phishing is genuinely novel for a Cambodian-context project.

3. **99.68% SMS accuracy** — exceeds the literature baseline (Almeida 2011 = 97.5%, Gupta 2021 = 98.2%).

4. **Explainability layer** — surfacing threat indicators per scan is a strong UX choice and academically defensible (Egelman & Peer 2015).

5. **Broad feature set** — IMAP email scanning + bulk cleanup + safe-link warning + Stripe + admin playbooks is unusually broad for a 9-month undergraduate project.

6. **Reproducible** — public HuggingFace datasets, fixed `random_state=42`, versioned model artifacts.

## 3.2 Weaknesses (be honest about these)

1. **Phishing accuracy 80.95% is below your stated 90% target.** Don't hide it. Own it: *"Feature engineering, not algorithm choice, is the remaining gap. DistilBERT integration is sketched in `predictor_v2.py`."*

2. **Voice 100% is suspicious.** Explicitly call it an **upper bound** before judges call it out. The dataset is only 1,600 scripted samples.

3. **English-only training.** You'll deploy to Cambodia but train on English. This will be the #1 question. Have your Khmer-future-work answer ready.

4. **No on-device inference.** Judges may ask *"why does my phone need internet to detect a scam?"* Answer ready: latency vs deploy-cost tradeoff.

5. **Small voice corpus.** Judges may say overfitting. Counter: ablation + held-out partition.

## 3.3 Defense Day Risks (prepare for these)

### Risk 1 — "Did you really build all these features?"
**Mitigation**: Have your laptop ready to open VS Code and show actual source files for any feature they pick. Don't claim a feature you can't open the code for in 10 seconds.

### Risk 2 — Slide 27 vs reality mismatch (96.2% vs 99.68%)
**Mitigation**: Pick ONE number and stick to it. Recommended: **99.68%** with the line: *"Slide 27 was an earlier run on a noisier dataset; the 99.68% is the latest reproducible value with metadata in `trained_models/sms/`."*

### Risk 3 — Slide 29 "ensemble" claim
**Mitigation**: Your SMS model is Logistic Regression only, not an ensemble. Either fix the slide before defense day, or have ready: *"We tested ensembles; Logistic Regression alone matched their accuracy at lower deployment cost."*

### Risk 4 — "Why isn't your dataset Cambodian?"
**Mitigation**: *"Because labeled Cambodian SMS data doesn't exist publicly. We preprocessed Unicode, so the pipeline IS ready — only labeled data is missing. Khmer corpus is our top future-work item."*

### Risk 5 — "How is your contribution different from existing tools?"
**Mitigation**: *"Existing tools are text-only and desktop-first. We added voice + URL + IMAP under one mobile UX, in <100ms, with explainable indicators."*

### Risk 6 — "Show me the model training code"
**Mitigation**: Make sure you can navigate to `ai-anti-spam-shield-service-model/app/model/train_separate_models.py` instantly. **Practice this 5 times.**

## 3.4 If I Were Grading You

| Criterion | Grade | Notes |
|---|---|---|
| Technical depth | A | Production-grade architecture, three trained models, real metrics |
| Originality | B+ | Cross-modality + Cambodian context is novel; algorithms are classical |
| Engineering quality | A | Docker Compose, tests, CI, monitoring — exceptional for undergraduate |
| Academic rigor | B+ | Good methodology, but small voice dataset and English-only limits external validity |
| Documentation | A− | Comprehensive report, defense script, restructured docx |
| Demo readiness | TBD | Depends on whether you capture the 5 flows above |

**Overall: solid A−/A territory** if you nail the Q&A on phishing-accuracy gap and the Khmer limitation.

---

# SECTION 4 — FINAL ACTION ITEMS

In priority order. Numbers in parens are time estimates.

## Must-do before defense

| Priority | Task | Time | Done? |
|---|---|---|---|
| 🔴 1 | Capture **7 required app screenshots** (Section 1.1) | 30 min | ☐ |
| 🔴 2 | Record **5 demo flows** (Section 2.1) | 1-2 hr | ☐ |
| 🔴 3 | Fix slide 27 ("96.2%" → "99.68%") | 5 min | ☐ |
| 🔴 4 | Fix slide 29 (remove "ensemble" claim) | 5 min | ☐ |
| 🔴 5 | Pre-write Q&A for the 6 risk questions (Section 3.3) | 30 min | ☐ |

## Should-do before defense

| Priority | Task | Time | Done? |
|---|---|---|---|
| 🟡 6 | Open `train_separate_models.py` 5 times so you can find it instantly | 5 min | ☐ |
| 🟡 7 | Drop screenshots into Word over the placeholder boxes | 15 min | ☐ |
| 🟡 8 | Press F9 in Word to update TOC page numbers | 1 min | ☐ |
| 🟡 9 | Print Section 1 of `THESIS_DEFENSE_SCRIPT.md` (cheat sheet) | 2 min | ☐ |
| 🟡 10 | Export PDF backup of the slides to USB stick | 5 min | ☐ |

## Nice-to-do extras

| Priority | Task | Time | Done? |
|---|---|---|---|
| 🟢 11 | Capture 3-6 recommended extra screenshots (Section 1.2) | 20 min | ☐ |
| 🟢 12 | Test demo video on projector | 10 min | ☐ |
| 🟢 13 | Rehearse 15-minute presentation script twice | 30 min | ☐ |
| 🟢 14 | Print 3 copies of restructured `.docx` report for committee | 10 min | ☐ |

---

# REMINDERS FOR DEFENSE DAY

## Three golden rules

1. **Confidence over perfection.** A confident *"I don't know but I'd investigate X"* beats a panicked wrong answer.
2. **Slow down.** Every time you feel rushed, take a 2-second pause and breathe.
3. **You know this project better than the judges.** They've seen it for 15 minutes. You've built it for 9 months.

## Bring with you

- [ ] Laptop, charger
- [ ] Phone with screenshots saved
- [ ] USB stick with: PDF slides, demo video, full project source code
- [ ] Printed cheat sheet (Section 1 of `THESIS_DEFENSE_SCRIPT.md`)
- [ ] Bottle of water
- [ ] 3 printed copies of the report (one per committee member)

## During Q&A

- **Listen to the entire question** before starting to answer
- **Repeat the question** in your own words if you need thinking time
- If you don't know the answer: *"That's a great question. We did not study that specifically, but my best understanding is..."*
- **Never bluff.** Saying *"I don't know but here's how I'd find out"* is respected.
- **Don't argue with judges.** If they push back, say *"That is a fair point — let me think about that"* and adapt.

---

# RELATED DOCUMENTS

- **[THESIS_DEFENSE_SCRIPT.md](THESIS_DEFENSE_SCRIPT.md)** — full slide-by-slide narration + 30-question Q&A bank
- **[DEFENSE_WALKTHROUGH_15MIN.md](DEFENSE_WALKTHROUGH_15MIN.md)** — 15-minute timing plan for the deck
- **[report/AI_Anti_Spam_Shield_Report.docx](report/AI_Anti_Spam_Shield_Report.docx)** — your final report (with 7 placeholder figures to replace)
- **[report/figures/](report/figures/)** — folder for screenshots and generated diagrams

---

**Document version**: 1.0
**Last updated**: 2026-05-20
**Author**: Defense preparation pack for the AI Shield Inc. team

🚀 *Capture the screenshots, record the demo, rehearse the answers. The rest is showing up confident on the day.*
