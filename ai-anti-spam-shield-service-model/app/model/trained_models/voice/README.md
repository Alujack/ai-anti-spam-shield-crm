---
license: mit
library_name: sklearn
pipeline_tag: text-classification
tags:
  - voice
  - text-classification
  - scikit-learn
  - spam-detection
metrics:
  - accuracy
  - f1
  - roc_auc
---

# Voice Call Scam Detection Model

`random_forest` + `TfidfVectorizer`
(ngram (1, 3), max_features=5000).

## Metrics (held-out test set)

| Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|
| 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

- **Dataset:** `BothBosu/scam-dialogue`
- **Train / test samples:** 1280 / 320
- **Features:** 5000
- **Trained:** 2026-01-20T13:39:06.270933

## Files
- `voice_classifier.pkl`
- `voice_vectorizer.pkl`

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

repo = "yanyoeurn/voice-scam-detector"
clf = joblib.load(hf_hub_download(repo, "voice_classifier.pkl"))
vec = joblib.load(hf_hub_download(repo, "voice_vectorizer.pkl"))

X = vec.transform(["your text here"])
print(clf.predict(X), clf.predict_proba(X))
```
