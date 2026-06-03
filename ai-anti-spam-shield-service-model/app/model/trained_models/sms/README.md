---
license: mit
library_name: sklearn
pipeline_tag: text-classification
tags:
  - sms
  - text-classification
  - scikit-learn
  - spam-detection
metrics:
  - accuracy
  - f1
  - roc_auc
---

# SMS Spam Detection Model

`logistic_regression` + `TfidfVectorizer`
(ngram (1, 2), max_features=3000).

## Metrics (held-out test set)

| Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|
| 0.9968 | 0.9982 | 0.9955 | 0.9968 | 1.0000 |

- **Dataset:** `Deysi/spam-detection-dataset`
- **Train / test samples:** 8720 / 2180
- **Features:** 3000
- **Trained:** 2026-01-20T13:38:58.040754

## Files
- `sms_classifier.pkl`
- `sms_vectorizer.pkl`

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

repo = "yanyoeurn/sms-spam-detector"
clf = joblib.load(hf_hub_download(repo, "sms_classifier.pkl"))
vec = joblib.load(hf_hub_download(repo, "sms_vectorizer.pkl"))

X = vec.transform(["your text here"])
print(clf.predict(X), clf.predict_proba(X))
```
