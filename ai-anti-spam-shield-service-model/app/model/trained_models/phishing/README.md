---
license: mit
library_name: sklearn
pipeline_tag: text-classification
tags:
  - phishing
  - text-classification
  - scikit-learn
  - spam-detection
metrics:
  - accuracy
  - f1
  - roc_auc
---

# Phishing Detection Model (URLs, Emails, SMS)

`random_forest` + `TfidfVectorizer`
(ngram (1, 2), max_features=5000).

## Metrics (held-out test set)

| Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|
| 0.8095 | 0.8274 | 0.7799 | 0.8030 | 0.8908 |

- **Dataset:** `ealvaradob/phishing-dataset` (combined_reduced)
- **Train / test samples:** 1680 / 420
- **Features:** 1496
- **Trained:** 2026-01-20T13:39:14.287339

## Files
- `phishing_classifier.pkl`
- `phishing_vectorizer.pkl`

## ⚠️ scikit-learn version

Trained with **scikit-learn 1.4.0**. Install the same version
to avoid `InconsistentVersionWarning` and possible silent breakage:

```bash
pip install scikit-learn==1.4.0 joblib huggingface_hub
```

## Usage

```python
import joblib
from huggingface_hub import hf_hub_download

repo = "yanyoeurn/phishing-detector"
clf = joblib.load(hf_hub_download(repo, "phishing_classifier.pkl"))
vec = joblib.load(hf_hub_download(repo, "phishing_vectorizer.pkl"))

X = vec.transform(["your text here"])
print(clf.predict(X), clf.predict_proba(X))
```
