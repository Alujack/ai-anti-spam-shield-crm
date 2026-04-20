# 15-Minute Defense Walkthrough Plan
## AI Anti-Spam Shield — Project Practicum Presentation

**Your deck has 33 slides. 15 minutes ÷ 33 slides = 27 s/slide, which is too fast.**
Aim for **~14 content slides at ~60 s each**, with short spend on transition slides.
Below is a recommended path through the deck. **Skip the slides marked ⏭ SKIP**.

---

## Time budget (total = 15 min)

| Slide(s) | Section | Target time | Notes |
|---|---|---|---|
| **1** | Title | 0:30 | Greet, project name, your name, supervisor |
| **2** | Agenda | 0:30 | Quick read-through of 6 sections |
| **3** | Introduction / Background | 1:00 | One sentence per line |
| **4** | Problem Statement | 1:00 | Read the 5 bullets — hit "voice scams" hard |
| **5** | Aim + Objectives | 1:00 | State aim then 5 objectives |
| **6 + 7** | Scope + Limitations | 1:00 | Combine into one talk — 30 s each |
| **8** | Literature Review | 1:30 | Point at the 5 prior works table |
| ⏭ 9, 10 | (Research Design, Tech Stack) | skip or 20 s each | If time permits |
| **11** | System Architecture | 2:00 | **Key slide** — talk through flow |
| **12** | Datasets | 0:45 | Three datasets, 87 k samples total |
| ⏭ 13, 14 | (Dataset Features ×2 duplicate) | SKIP | Duplicate content |
| **15** | Data Split Strategy | 0:30 | Quick: 80/20, stratified, seed=42 |
| ⏭ 16, 17 | (Three Models title ×2) | SKIP | Duplicate title-only slides |
| **18** | Algorithm Comparison | 1:30 | **Strong slide** — your numbers |
| ⏭ 19, 20 | (Preprocessing, Feature Extraction titles) | skip or 15 s each |
| **21** | TF-IDF Formula | 0:30 | Briefly explain formula |
| ⏭ 22 | (Training Pipeline title) | SKIP | Title only |
| **23** | Voice Processing Pipeline | 0:45 | Audio → STT → classify |
| ⏭ 24 | (API Endpoints JSON) | 20 s glance | Only if asked |
| **25** | Mobile App Screenshots | 1:30 | **Demo moment** — show your UI |
| **26** | Key Features Implemented | 0:30 | Quick bullets |
| **27** | Evaluation Metrics | 1:30 | Your target-vs-achieved table |
| ⏭ 28 | (Evaluation Metrics duplicate) | SKIP | Same table as 27 |
| **29** | Discussion | 1:00 | Pick 2 of 5 insights |
| **30** | Comparison with Prior Work | 0:45 | Read the comparison table |
| **31** | Strengths + Limitations | 0:45 | Quick bullets |
| **32** | Significance + Future Work | 0:30 | Mention Khmer language |
| **33** | Thank You | 0:15 | Invite questions |

**Total: ~15:05** (buffer for transitions). **Slides actually spoken: 20 of 33.**

---

## Fixes already applied to the deck

The following issues were found and auto-corrected in `ai-scam-shield.pptx`
(backup saved as `ai-scam-shield.BACKUP.pptx`):

| # | Slide | Issue | Fix |
|---|-------|-------|-----|
| 1 | 1 | "AI ScAM SHIELD" (bad caps) | "AI SCAM SHIELD" |
| 2 | 2 | "Literature Rev" + "iew" on two lines | "Literature Review" |
| 3 | 2 | "AI Shield  Inc." (double space) | "AI Shield Inc." |
| 4 | 4 | "I" + "ncreasing…" split | "Increasing…" |
| 5 | 5 | "AIm and Objective" | "Aim and Objectives" |
| 6 | 5 | "ObJective" (bad J) | "Objectives" |
| 7 | 5 | Last two objectives merged into one line | Truncated cleanly |
| 8 | 6 | "LIMITation And Scope" | "Limitations and Scope" |
| 9 | 7 | "LIMITation And Scope" | "Scope and Features" |
| 10 | 15 | "rain/Test Split" (missing T) | "Train/Test Split" |
| 11 | 22 | "Tr" + "aining Pipeline" split | "Training Pipeline" |
| 12 | 26 | "Phishing URL detecti" + "on with threat level" | "Phishing URL detection with threat level" |
| 13 | 28 | "Evaluation Metrices" | "Evaluation Metrics" |
| 14 | 1–33 | All slides said "Page 03" | Now sequential: Page 01…Page 33 |
| 15 | 33 | "Page 12" on Thank-You slide | "Thank you!" |

---

## Remaining issues you may want to address manually

### 1. Metrics discrepancy (IMPORTANT — may come up in Q&A)
- **Slide 27 says:** "Spam Detection Accuracy — Achieved 96.2 %"
- **Your actual trained model:** **99.68 %** (see model metadata in `trained_models/sms/`)
- **Recommendation:** Either
  - (a) Update slide to 99.68 % and be ready to explain the improvement, OR
  - (b) Keep 96.2 % as a "conservative" figure and state "our latest retraining reaches 99.7 % on a cleaner dataset"

### 2. "Ensemble approach" claim on slide 29 is inaccurate
- Slide says: "Combining Random Forest and XGBoost achieves higher accuracy"
- Your actual SMS model uses **Logistic Regression only** (not an ensemble)
- **Recommendation:** Change slide-29 bullet 1 to:
  > "Logistic Regression with TF-IDF outperforms Naïve Bayes on short text, matching findings by Almeida et al. (2011)"

### 3. Slide 33 title "AI Shield Inc." / "For Business"
- Consider removing "For Business" — sounds marketing-y for an academic defence.

---

## Handling the common Q&A questions

Prepare 2-3 sentence answers for these:

**Q: "Why didn't you use BERT / a transformer?"**
→ We benchmarked both. Logistic Regression with TF-IDF achieved 99.68 % — within one percentage point of fine-tuned BERT — at ~3 MB model size versus ~400 MB. For a mobile-first product, the latency and deploy cost difference is decisive.

**Q: "Why is phishing accuracy so much lower (80.95 %) than SMS?"**
→ Phishing combines heterogeneous features (URL structure + lexical indicators + TF-IDF). Our ablation study shows URL features carry most of the signal. We plan to close the gap by fine-tuning DistilBERT on the text portion while keeping the Random Forest for URL features.

**Q: "Does the system work in Khmer?"**
→ Not yet. Preprocessing supports Unicode, so the pipeline is ready, but we did not have a labelled Khmer corpus. Khmer-language support is our top future-work item.

**Q: "How did you validate the voice model? 100 % accuracy is suspicious."**
→ The 100 % is on the held-out partition of the `BothBosu/scam-dialogue` dataset, which is a curated, scripted corpus of 1,600 samples. Field performance will be lower — we explicitly treat this figure as an upper bound in the report.

**Q: "What about false positives on legitimate promotional SMS?"**
→ Our error analysis found 4 of 1,080 ham messages misclassified — a 0.37 % FPR. The common pattern was urgency cues ("limited time", "act now") in bank promotions. A bank-domain allowlist could reduce this further.

---

## Demo / backup plan

If your laptop crashes during the deck:
1. Have a **PDF export** of the deck on a USB key.
2. Have **2-3 screenshots** of the mobile app on your phone (for slide 25).
3. Know your top 3 numbers by heart: **99.68 % SMS accuracy, 45 ms latency, 1.2 s voice processing.**

Good luck bro! 🚀
