# Defense Walkthrough — AI Anti-Spam Shield
## Project Practicum Presentation · 15-minute slot

**Updated 2026-05-27 for the new format and the 29-slide deck (`pdf-slide/ai-scam-shield.pdf`).**

### The new time budget
```
15 min total
├── 10 min presentation
│     ├── ~7 min  live slides
│     └──  3 min  video demo (slide 28)
└──  5 min  Q&A
```
You have **~7 minutes of talking over slides**, not 15. That's the big change. With 29 slides you must
**skip most methodology-detail slides** and spend your time on the architecture, the results, and the demo.
Keep the skipped slides in the deck — they are your Q&A backup.

---

## Recommended path (~7 min of slides + 3 min video)

| Slide(s) | Section | Time | What to say |
|---|---|---|---|
| **1** | Title | 0:15 | Project name, your name, advisor (Mr. Chhim Bunchhun) |
| ⏭ 2 | Table of contents | skip | Don't read it aloud |
| **3 + 4** | Intro + Problem | 0:45 | One line of context, then hit the 5 problems — stress **voice scams** and **Cambodian users** |
| **5** | Aim & Objectives | 0:30 | State the aim, then the 4 objectives |
| ⏭ 6, 7 | Limitations + Scope | 0:20 | One sentence: "mobile-first, English, individual users — but a broad feature set (show, don't read)" |
| ⏭ 8 | Literature Review | 0:20 | Point at the table: "we build on Almeida, Mohammad, and the transformer line of work" |
| ⏭ 9 | Tech stack | skip | Backup only |
| **10** | System Architecture | **1:00** | ⭐ Your best slide. Walk the 3 tiers: Flutter → Node/Express → Python/FastAPI ML |
| **11** | Datasets | 0:30 | 3 HuggingFace datasets, **87,896 samples total** |
| ⏭ 12, 13 | Dataset features / split | skip | Backup |
| **14 + 15** | Model architecture + why | 0:45 | Three specialized models; one line each on algorithm choice |
| ⏭ 16–20 | Preprocessing / TF-IDF / training / voice pipeline / API | skip | Backup for Q&A — do **not** speak these |
| **21** | App screenshots (Results) | 0:30 | "Here's the working app across SMS, voice, phishing, email, network & SOC" → lead into video |
| **22** | Algorithm Comparison | **0:45** | ⭐ Your numbers — **see the corrected figures below** |
| ⏭ 23 | Key features | 0:10 | Glance |
| **24** | Evaluation Metrics | 0:30 | Target-vs-achieved table |
| **25** | Discussion | 0:20 | Pick **one** insight (URL features critical for phishing) |
| ⏭ 26 | Comparison w/ prior work | skip | Backup |
| **27** | Conclusion | 0:30 | Strengths + name Khmer as #1 future work |
| **28** | **Video demo** | **3:00** | Play it; narrate only if it needs context |
| **29** | Thank you | 0:10 | Invite questions |

**Live-slide total ≈ 7:00 + 3:00 video = 10:00.** Leaves the full 5:00 for Q&A.

> If you're running long, the first things to drop are slides 11, 25, and 14/15 detail. Never cut 10, 22, or the video.

---

## ⚠️ Use these numbers (they match the deployed models your demo runs)

The deck currently shows **inconsistent** accuracies (e.g. SMS as both 94.46% and 96.2%). Your trained-model
metadata is the source of truth. State these and only these:

| Model | Algorithm (deployed) | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|---|
| **SMS spam** | Logistic Regression | **99.68%** | 99.82% | 99.55% | 99.68% |
| **Voice scam** | Random Forest | **100%** ⚠️ | 100% | 100% | 100% |
| **Phishing** | Random Forest | **80.95%** | 82.74% | 77.99% | 80.30% |

⚠️ **Always caveat the voice 100%:** "on the held-out split of a small (1,600-sample) scripted corpus — we treat it as an upper bound."

> See `pdf-slide/report-slide.md` for the full slide-by-slide list of number/label fixes (Voice & Phishing
> are labelled with the wrong algorithm on slides 14/15/22; phishing "92.5%" is unsupported).

### Three numbers to know cold
**99.68% SMS accuracy · 45 ms API latency · 1.2 s voice processing.**

---

## Q&A prep (5 minutes — this is half your grade)

**Q: "Why Logistic Regression / Random Forest instead of BERT or a transformer?"**
> We benchmarked classic ML against the cost of a transformer. LR with TF-IDF hits 99.68% on SMS — within ~1 point of fine-tuned BERT — at ~3 MB vs ~400 MB. For a mobile-first product, the latency and deploy cost make classic ML the right call.

**Q: "Voice accuracy is 100% — isn't that overfitting?"**
> It's 100% on the held-out split of `BothBosu/scam-dialogue`, a curated, scripted 1,600-sample corpus. We explicitly treat it as an upper bound; field performance will be lower. Expanding to a larger, noisier voice dataset is future work.

**Q: "Why is phishing accuracy lower (≈81%) than SMS?"**
> Phishing mixes heterogeneous signals — URL structure, lexical cues, and TF-IDF text. Our ablation shows URL features carry most of the signal. Recall is our weak point (~78%); closing it (e.g. fine-tuning a text model on the content portion) is our main next step.

**Q: "Does it work in Khmer?"**
> Not yet. The preprocessing pipeline is Unicode-ready, but we lacked a labelled Khmer corpus. Khmer support is our #1 future-work item.

**Q: "What stops false positives on legitimate promo SMS / trusted brands?"**
> Two things: error analysis showed urgency cues drive most false positives, and we recently added a **trusted-domains allowlist** in the risk scorer so brands like google.com / paypal.com aren't flagged, plus homoglyph/typosquat detection (e.g. `paypa1.com`) to catch the lookalikes.

**Q: "What's actually 'AI' here vs rule-based?"**
> The core classifiers are ML (TF-IDF + LR/RF). On top we add interpretable rule-based threat indicators (urgency language, suspicious URL, credential request) so the user sees *why* something was flagged — a hybrid ML + rules design.

**Q: "Beyond detection, what does the product do?"** (the scope slide breadth)
> Email auto-scan over IMAP (Gmail/Outlook/Yahoo) with scheduled background scanning, a SOC dashboard (threats/incidents/alerts, response playbooks), network activity monitoring, behavior anomaly analysis, scan history, and a continuous-learning loop where user feedback feeds model retraining.

---

## Demo / backup plan
1. Have the **PDF on a USB key** in case your laptop or projector fails.
2. The video demo (slide 28) is on YouTube — also keep a **local copy of `ScreenRecording_05-26-2026 ....MP4`** offline in case there's no internet.
3. Keep 2–3 app screenshots on your phone (slide 21 content) as a last resort.
4. Memorize the three numbers above.

Good luck — the project is strong; just keep the numbers consistent. 🚀
