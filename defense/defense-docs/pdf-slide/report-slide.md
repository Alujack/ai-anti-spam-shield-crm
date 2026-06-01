# Slide Review — `ai-scam-shield.pdf`

**Reviewed:** 2026-05-27 (updated) · **Deck:** 29 pages · **Checked against:** the real trained model files (`app/model/trained_models/*/`) and the running code.

> **Good news first.** Since the last review, most of the big problems are already fixed:
> page numbers are now correct (01–29), Voice and Phishing now correctly say **Random Forest**,
> SMS now shows **99.68%**, the fake "XGBoost / Ensemble" claim is gone, and the scope slide now
> shows the full system. The deck is in good shape.
>
> **What is left:** a few numbers still do not match the models your live app runs. The main one is
> the **dataset sizes** (slide 11 and 14). Fix those and a couple of small things, and you are safe in Q&A.

---

## The real numbers (use these everywhere)

These come straight from your trained model files (trained 2026-01-20):

| Model | Algorithm | Trained on | Accuracy | Precision | Recall | F1 | Features |
|---|---|---|---|---|---|---|---|
| SMS Spam | Logistic Regression | 10,900 (8,720 train / 2,180 test) | **99.68%** | 99.82% | 99.55% | 99.68% | 3,000 |
| Voice Scam | Random Forest | 1,600 (1,280 / 320) | **100%** | 100% | 100% | 100% | 5,000 |
| Phishing | Random Forest | 2,100 (1,680 / 420) | **80.95%** | 82.74% | 77.99% | 80.30% | 1,496 |

> **Important:** your live models were trained on these **small, balanced** datasets. The 99.68% and
> 80.95% numbers come from here. The big numbers (55,230 / 31,066) on slide 11 were from an earlier
> experiment on a larger dataset and **no longer match your real models.**

---

## 🔴 Must fix (a judge can catch these)

### 1. Dataset sizes are wrong — Slide 11 & Slide 14
Slide 11 still shows SMS **55,230** and Phishing **31,066** (total 87,896). Your real models were
trained on much smaller balanced sets. Because your accuracy numbers (99.68% / 80.95%) come from the
small sets, the slide and the results no longer agree.

**Fix Slide 11 table to:**

| Dataset | Source | Total | Train | Test | Distribution |
|---|---|---|---|---|---|
| SMS Spam | `Deysi/spam-detection-dataset` | **10,900** | 8,720 | 2,180 | Balanced (≈50/50) |
| Voice Scam | `BothBosu/scam-dialogue` | 1,600 | 1,280 | 320 | Balanced (50/50) |
| Phishing | `ealvaradob/phishing-dataset` (combined_reduced) | **2,100** | 1,680 | 420 | Balanced (≈50/50) |

Change **Total Training Data: 87,896** → **Total Training Data: 14,600**.

**Fix Slide 14 (Model Architecture) "Dataset Size" row:** SMS **55,230 → 10,900**, Phishing **31,066 → 2,100** (Voice 1,600 is correct).

**Also fix the phishing dataset NAME (confirmed by re-running your loader):**
Your slides/model file say the phishing dataset is `ealvaradob/phishing-dataset`. It is **not**.
Your deployed phishing model has exactly 2,100 samples (1,680 train / 420 test), which matches
**`shawhin/phishing-site-classification`** — a small **website-URL** dataset. The `ealvaradob` name is
a hard-coded label in the code; the real `ealvaradob` set is ~90,000 rows (521 MB) and never loaded.
- Slide 11 source: `ealvaradob/phishing-dataset` → **`shawhin/phishing-site-classification`**
- Slide 12 content type: "Emails & URLs" → **"Website URLs"** (the deployed phishing model is URL-only, no emails)

### 2. Phishing feature count is wrong — Slide 14
Slide 14 says phishing features = **5,051 total**. Your real model uses **1,496**.
**Fix:** "TF-IDF + URL Features + Text Features (**1,496 total**)".

### 3. "K-fold cross-validation" is not true — Slide 13
The slide says *"Validation: K-fold cross-validation during hyperparameter tuning."*
You did **not** do cross-validation — you used a single 80/20 split. If a judge asks to see your
folds, this becomes a problem.
**Fix:** change that line to *"Validation: held-out 20% test set (k-fold cross-validation planned as future work)."*

### 4. Voice pipeline still says "Naive Bayes" — Slide 19 (the picture)
The voice pipeline image, step 4, says **"Naive Bayes prediction."** Your deployed voice model is
**Random Forest.** This is inside an image, so you must re-make/re-export that picture.
**Fix:** change "Naive Bayes prediction" → **"Random Forest prediction."**
(Also note: your scope slide 7 says voice is *multi-modal* — speech-to-text + audio + prosody — but
this picture only shows the text path. If you have time, add the audio + prosody branch so slide 19
matches slide 7.)

---

## 🟠 Should fix (quick wins)

### 5. Voice "fastest training (0.015s)" reason is wrong — Slide 15
You chose **Random Forest** for voice, but **0.015s is the Naive Bayes training time**, not Random
Forest's (Random Forest was 0.16s). The reason you wrote belongs to a different algorithm.
**Fix:** *"100% accuracy (all algorithms tied); chose Random Forest for robustness on a small dataset."*

### 6. Algorithm comparison table mixes two datasets — Slide 22
In the SMS table you show Logistic Regression = **99.68%**, but Naive Bayes (92.09%) and Random
Forest (89.47%) next to it are from the **bigger** experiment set. On the same test set those numbers
cannot sit together. Same issue in the Phishing table (the Random Forest row uses 80.95% from the
small set, the other rows use big-set numbers), and the **Logistic Regression label is missing** in
the phishing table.

**Simple fix:** keep the comparison table as one consistent experiment, and add a short note for the
deployed result. Example for SMS:
- Logistic Regression 94.46% · Naive Bayes 92.09% · Random Forest 89.47%
- Note under the table: *"Deployed model retrained on the balanced dataset → 99.68%."*

And for Phishing, add back the missing **Logistic Regression** label on the 75.65% row, and a note:
*"Deployed Random Forest on the balanced dataset → 80.95%."*

### 7. "30+ feature extraction" — Slide 25
The Discussion says *"Our 30+ feature extraction approach."* Your real phishing model uses **24 URL
features**. **Fix:** change "30+" → **"24"**.

### 8. All Discussion cards numbered "01" — Slide 25
Every one of the 6 cards shows **01**. Number them **01–06**.

### 9. Database label — Slide 9
Tech stack says **"SQLite / PostgreSQL."** Production runs **PostgreSQL** (SQLite is only for local
dev). **Fix:** *"PostgreSQL (SQLite for local development)."*

---

## 🟡 Minor / cosmetic

- **Slide 1:** the logo text "INFORMATION TECHNOLOGY ENCOURAGING" wraps the last "G" onto its own line — widen the text box. Also check the school logo line reads the way you want.
- **Slide 8 (Literature Review):** "Naive Bayes,SVM," has a trailing comma and a missing space → "Naive Bayes, SVM".
- **Slide 3 (Introduction):** the paragraph breaks in the middle of sentences — let the text flow naturally.
- **Slide 23 (Key Features Implemented):** lists 6 features, while the scope slide (7) lists the full system. Optional: add a line like "+ email auto-scan, SOC dashboard, continuous learning" so the two slides agree.
- **Name consistency:** title says "AI SCAM SHIELD", the architecture badge says "AI Anti-Spam Shield CRM". Pick one name. (Either is fine — just be consistent.)

---

## ✅ Strong points (keep as-is)
- **Slide 10 — System architecture** (three-tier client → backend → AI). Your clearest slide.
- **Slide 21 — Results screenshot wall.** Shows the real, working multi-feature app. Great lead-in to the demo video (slide 28).
- **Slide 7 — Scope.** Now shows the full system (email IMAP auto-scan, SOC dashboard, network monitoring, homoglyph detection, continuous-learning loop). Impressive breadth.
- **Slide 22 — Algorithm comparison layout.** Good rigor once the numbers in point 6 are tidied.
- **Slide 24 & 27 — metrics and conclusion now use 99.68% / 80.95%.** Correct.

---

## Strong Q&A answer: "Why such a small dataset? Why not use more data?"

We actually **tested this** (2026-05-27). We re-trained on the larger datasets (SMS 55,230, phishing
31,066) and measured the real result. **Bigger data scored worse:**

| Model | Deployed (small, clean) | Extended (big, messy) | Result |
|---|---|---|---|
| SMS accuracy | **99.68%** | 94.46% | worse by 5.2 points |
| Phishing accuracy | **80.95%** | 75.59% | worse by 5.4 points |
| Phishing recall | **77.99%** | **44.52%** | **misses 55% of phishing** |

**Your answer to the panel:**
> "We deliberately ship smaller, clean, balanced datasets. We benchmarked the larger combined sets
> (55K SMS, 31K phishing) and accuracy actually dropped — phishing recall fell from 78% to 44%,
> meaning the bigger-data model misses more than half of real phishing. The larger sets are noisier
> and mix emails, SMS and URLs with inconsistent labels. For a security tool, a clean balanced
> dataset with high recall beats a big noisy one."

This turns "small dataset" from a weakness into a deliberate, evidence-based engineering decision.

---

## One honesty tip for Q&A (voice 100%)
100% accuracy always draws questions. Say it before they do:
> "That 100% is on a small, balanced 1,600-sample dataset where train and test come from the same
> source. We treat it as a best case — real-world accuracy will be lower, and we collect real voice
> samples through the feedback loop to test this."
This turns a red flag into a sign that you understand your own results.

---

### Priority order
1. **Slide 11 + 14 dataset numbers** (point 1) — the most important.
2. Slide 13 cross-validation wording (point 3).
3. Slide 19 voice picture "Naive Bayes → Random Forest" (point 4).
4. Everything else is polish.
