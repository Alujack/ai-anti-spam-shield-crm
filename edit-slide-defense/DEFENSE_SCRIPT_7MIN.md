# AI Scam Shield — 7-Minute Defense Script

**Presenter:** Yoeurn Yan · **Advisor:** Mr. Chhim Bunchhun · **RUPP**
**Total target:** 7:00 (≈4 min slides + ~2.5 min demo + buffer)

**Pacing rule:** Skip / click straight through the section-divider slides — **2, 6, 10, 13, 15, 16, 17, 18**. Talk only on the content slides below.

---

## [0:00–0:30] Slides 1–2 — Title
> Good morning. I'm Yoeurn Yan, and my thesis is **AI Scam Shield** — an AI mobile app that catches spam, phishing, and voice scams in real time. My advisor is Mr. Chhim Bunchhun. Let me show you the problem, how I built it, and what the results say.

*(Click through the Table of Contents — don't read it.)*

## [0:30–1:15] Slides 3–4 — Problem
> Spam and phishing are rising fast. In Cambodia, people get scam SMS and fake links every single day. Old rule-based filters can't keep up — they miss smart social-engineering tricks. And almost no tool checks **voice** scams. Ordinary people have no easy way to check if a message is safe. That's the gap I'm closing.

## [1:15–1:45] Slide 5 — Aim & Objective
> My aim: build an AI app that spots scams in **both text and voice**, with high accuracy. The objectives — real-time detection above 95%, catch phishing URLs and fake brands, scan text and voice, keep it simple on mobile, and save scan history.

## [1:45–2:15] Slide 7 — What It Does
> The app does six things: spam check on SMS, voice check that transcribes then analyzes, phishing-link check, auto-scan of Gmail and Outlook inboxes, a security dashboard, and it **gets smarter** — user feedback retrains the model.

## [2:15–2:40] Slide 8 — Literature Review
> Prior work shows classic models go far: Almeida reached 97.5% on SMS spam with SVM, Mohammad hit 92% on phishing with URL features, and transformers like BERT push 98%. My question: can lightweight classic ML match this — on mobile?

## [2:40–3:40] Slides 9, 11, 14 — Methodology
*(Click past 10, 13, 15, 16, 17, 18.)*
> Stack: Flutter app, Node backend, and a Python FastAPI service running the models.
> I trained on **three small, clean, balanced datasets** — 14,600 samples total — quality over size. 80/20 split, stratified, fixed seed so results repeat.
> Three specialized models: **Logistic Regression** for SMS, **Random Forest** for voice and phishing, all on TF-IDF features. I picked each by accuracy and speed on its data.

## [3:40–4:30] Slides 20, 22 — Results
> Results. **SMS: 99.68% accuracy** with Logistic Regression. **Voice: 100%** — but on a small set, so I read that as promising, not final. **Phishing: 80.95%** with Random Forest — my hardest task, limited by dataset size, and I'm honest about that.
> Against my targets: spam beat 95%, phishing beat 78%, API responds in **45 milliseconds**, voice in 1.2 seconds, false positives just **3.8%**. Every target met.

## [4:30–5:00] Slides 23–24 — Discussion
> The key finding: **classic ML matches deep learning** on short text — near transformer-level accuracy at a fraction of the size, which is what makes it work on a phone. Versus prior work: they were text-only, desktop, black-box. Mine is **text plus voice, mobile-first, real-time, and explainable** — it tells you *why* a message is flagged.

## [5:00–5:20] Slide 25 — Conclusion
> Strengths: high accuracy, text and voice, explainable, mobile. Honest limits: English-only for now, voice depends on audio quality, needs internet. Future work: Khmer support, on-device offline AI, and live SMS screening.

## [5:20–6:50] Slide 26 — Live Demo
> Let me show it live.
- Scan a scam SMS → **flagged 99%, CRITICAL**
- Check a phishing link → **blocked, very high risk**
- *(if time)* Report the threat → **saved to history**

*(Keep it to 2–3 actions. If the demo runs long, drop the email auto-scan.)*

## [6:50–7:00] Slide 27 — Thank You
> That's AI Scam Shield — accurate, explainable, and built for everyday people. Thank you. I'm happy to take your questions.

---

## Tips to Hit 7:00 Exactly
- **Rehearse the demo cold** — it's your biggest time risk. Have the scam SMS and phishing link **pre-typed / ready** so you don't fumble.
- If running over at slide 20, cut Discussion (23–24) to one line: *"Classic ML matched deep learning, and mine adds voice and explainability."*
- Speak the numbers slowly — **99.68 · 80.95 · 45ms · 3.8%** are what the panel remembers.

## Likely Panel Questions — Quick Answers
- **Why is phishing only 80.95%?** Small 2,100-URL dataset; I chose clean/balanced over large. Bigger sets benchmarked worse. It still beat my 78% target.
- **Voice 100% — too perfect?** Small 1,600-sample set, so promising but not proven at scale. Honest about that.
- **Why classic ML, not BERT/transformers?** Near-equal accuracy on short text, tiny model, fast on mobile, and **explainable**.
- **Khmer?** On the roadmap — main blocker is the lack of Khmer training data.
- **Why needs internet?** AI runs on the server today; on-device offline inference is future work.
