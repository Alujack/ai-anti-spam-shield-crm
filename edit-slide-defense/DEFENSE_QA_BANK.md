# AI Scam Shield — Defense Q&A Bank (likely questions + strong answers)

> Verified against your real code and saved model files. Keep answers short and confident.
> Deployed numbers (memorize): **SMS 99.68% · Voice 100% · Phishing 80.95% · API 45ms · False positives 3.8%**

---

## A. THE MODEL & TRAINING

**Q1. How did you train your models?**
> I trained three separate scikit-learn models, one per job. For each: load a clean balanced dataset from
> HuggingFace, clean the text, turn words into numbers with TF-IDF, split 80% train / 20% test with a fixed
> seed, then train and test. A compare mode tries Naive Bayes, Logistic Regression, and Random Forest and
> keeps the best by F1.

**Q2. Why three separate models instead of one?**
> Each job is different — SMS is short text, voice is long dialogue, phishing is URLs plus message text.
> A specialized model per job is more accurate than one model trying to do everything.

**Q3. Which algorithm did each model use, and why?**
> - **SMS → Logistic Regression** — highest accuracy (99.68%) and very fast on short text.
> - **Voice → Random Forest** — all algorithms tied near 100%, and Random Forest is the most robust on a small set.
> - **Phishing → Random Forest** — best accuracy (80.95%) and it handles the ~1,500 mixed features well.

**Q4. What is TF-IDF, in simple words?**
> It turns words into numbers. Rare but telling words like "verify account" score high; common words like
> "the" score low. The model learns which word-scores point to spam.

**Q5. What preprocessing did you do?**
> Lowercase the text, replace URLs/emails/phone numbers with tokens, remove symbols, remove English
> stopwords, and apply Porter stemming so "winning" and "wins" count as the same word.

**Q6. How big are your datasets?**
> SMS ~10,900, Voice 1,600, Phishing ~2,100 — about 14,600 total. All balanced 50/50. I chose small clean
> data over large noisy data, because clean data trained better in my experiments.

**Q7. How did you split train and test? Is it reproducible?**
> 80/20 split, stratified so both classes stay balanced, with random seed 42 — so anyone can repeat it and
> get the same result.

---

## B. THE RESULTS (the tricky ones)

**Q8. Why is voice 100%? Isn't that overfitting?** ⭐ (most likely hard question)
> The voice set is small — 1,600 dialogues — and balanced, and scam vs normal calls use very different words,
> so the classes are easy to separate. In fact all three algorithms hit 100%, which tells me the task is
> separable, not that one model is magic. Because I was suspicious, I ran 10-fold cross-validation and added
> regularization to confirm it wasn't just memorizing — and it held up. So I read it as promising, but on a
> small set. To truly prove it I need a bigger dataset and real recorded audio — that's future work.

**Q9. Why is phishing only 80.95%? That's much lower.**
> It's my hardest task and smallest useful dataset (~2,100 URLs). Phishing sites copy real ones, so it's
> genuinely hard. I chose clean balanced data over large messy data — bigger sets actually scored worse for me.
> It still beat my 78% target, and Random Forest won because it handles the mixed URL + text features best.

**Q10. What's the difference between precision, recall, and F1?**
> Precision = when I flag something as bad, how often I'm right. Recall = of all the bad messages, how many I
> catch. F1 balances both — it's only high when both are good. I pick my best algorithm by F1 because it's the
> fairest single score.

**Q11. Your false positive rate is 3.8% — why does that matter?**
> A false positive is a safe message wrongly flagged. Too many false alarms make users ignore the app. Under
> 4% means it rarely cries wolf, so people keep trusting it.

**Q12. Are all the numbers in your comparison table from the same dataset?** ⚠️ (be honest)
> The deployed models use the small clean default datasets — that's where 99.68%, 100%, and 80.95% come from.
> I also benchmarked on larger combined datasets, and those numbers are in my comparison logs. I kept the
> small-dataset models because clean data generalized better.

---

## C. DESIGN CHOICES

**Q13. Why classic ML and not deep learning / BERT?**
> On short messages, TF-IDF with Logistic Regression or Random Forest reached near transformer-level accuracy,
> but the model is tiny, fast, and explainable. For a mobile app, that's the right trade-off.

**Q14. How do you handle voice messages?**
> The app transcribes speech to text first, then runs the same scam text model on the transcript. So voice
> reuses the text pipeline — that's what made it feasible.

**Q15. How is phishing detection different from spam?**
> Besides the words, the phishing model also reads URL features — length, randomness, suspicious endings like
> .tk or .xyz, URL shorteners, IP-address links, fake brand names — and text signals like urgency, threats,
> and credential requests. That's why it can explain *why* a link is dangerous.

**Q16. What makes your system explainable / not a black box?**
> It returns the threat indicators that triggered the flag — for example "urgency language," "credential
> request," "suspicious URL" — so the user sees the reason, not just a yes/no.

**Q17. How does the app keep learning over time?**
> Users flag wrong results. That feedback is reviewed and approved, then after about 50 approved samples the
> system retrains automatically — but a new model only goes live if it tests *better*; otherwise it rolls back.
> So it can only improve, never get worse.

---

## D. ARCHITECTURE & DEPLOYMENT

**Q18. What's your tech stack?**
> Flutter mobile app, a Node.js / Express backend with a database, and a Python FastAPI service that runs the
> ML models with scikit-learn.

**Q19. Why does it need internet?**
> The models run on the server, not on the phone yet. On-device offline inference is future work.

**Q20. How fast is it?**
> About 45 milliseconds per text check and 1.2 seconds for voice — fast enough to feel instant.

**Q21. How do you serve the models?**
> The FastAPI service loads the saved models and exposes endpoints like /predict-sms, /predict-phishing, and
> an auto-detect route. Each returns a probability, a threat level, and the reasons.

---

## E. LIMITATIONS & FUTURE WORK (show maturity — don't be defensive)

**Q22. What are the main limitations?**
> English only for now, voice accuracy depends on audio quality, it needs internet, and I have little Khmer
> training data. I'm upfront about these.

**Q23. What about Khmer support?**
> It's on the roadmap. The main blocker is finding enough Khmer scam examples to train on.

**Q24. If you had more time, what would you improve?**
> Bigger, more realistic datasets — especially for phishing and real voice audio — Khmer support, on-device
> offline detection, and live SMS/call screening.

**Q25. What's the single biggest contribution of your work?**
> Showing that small, simple, explainable models can reach high accuracy and run behind a real phone app —
> and adding voice scam detection, which most prior work ignores.

---

## F. CURVEBALLS (stay calm, it's okay to say "good question")

**Q26. What if a scammer writes in a way your model never saw?**
> That's the hardest case. The threat-indicator features still catch common tricks like urgency and fake
> links, and the continuous-learning loop lets the model learn new patterns from user feedback over time.

**Q27. Could attackers fool your model on purpose (adversarial)?**
> Yes, that's a real risk for any ML filter. My layered indicators make it harder, and retraining on new
> feedback helps the model adapt. Stronger adversarial defense is future work.

**Q28. Why should we trust 99.68% — could the test data leak into training?**
> No — I split before training with a stratified 80/20 split and a fixed seed, and the test set is never seen
> during training. For the small voice set I also used 10-fold cross-validation to double-check.

**Q29. Is this better than existing apps like Truecaller / Gmail spam filter?**
> Those are strong but closed and text-only. My contribution is an open, explainable system that also handles
> voice and shows the reasons — more as a research prototype than a market competitor.

---

## ONE-LINE CLOSER FOR ANY ANSWER
> "Small clean data + the right simple model per task = accurate, fast, explainable, and it runs behind a real phone app."

## IF YOU DON'T KNOW AN ANSWER
> "That's a good question — I didn't test that directly, but my approach would be..." — then reason out loud.
> Never freeze or guess a fake number. Honesty + reasoning scores better than bluffing.
