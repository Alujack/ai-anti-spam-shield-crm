#!/usr/bin/env python3
"""Publish trained sklearn models to the Hugging Face Hub.

Generates a model card (README.md) from each model's *_metadata.json and
uploads the whole folder as a Hub model repo. Set HF_TOKEN in the env.

Usage:
    HF_TOKEN=hf_xxx python scripts/publish_to_hf.py            # all models
    HF_TOKEN=hf_xxx python scripts/publish_to_hf.py phishing   # one model
    HF_TOKEN=hf_xxx python scripts/publish_to_hf.py --private  # make private
"""
import json
import os
import sys
from pathlib import Path

from huggingface_hub import HfApi

USER = "yanyoeurn"
MODELS_DIR = Path(__file__).resolve().parent.parent / "app" / "model" / "trained_models"
SKLEARN_TRAINED_VERSION = "1.4.0"

# model_type -> (hub repo slug)
REPOS = {
    "phishing": "phishing-detector",
    "sms": "sms-spam-detector",
    "voice": "voice-scam-detector",
}


def make_card(meta: dict) -> str:
    m = meta["metrics"]
    files = "\n".join(f"- `{v}`" for v in meta["files"].values())
    return f"""---
license: mit
library_name: sklearn
pipeline_tag: text-classification
tags:
  - {meta['model_type']}
  - text-classification
  - scikit-learn
  - spam-detection
metrics:
  - accuracy
  - f1
  - roc_auc
---

# {meta['description']}

`{meta['algorithm']}` + `{meta['vectorizer']['type']}`
(ngram {tuple(meta['vectorizer']['ngram_range'])}, max_features={meta['vectorizer']['max_features']}).

## Metrics (held-out test set)

| Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|
| {m['accuracy']:.4f} | {m['precision']:.4f} | {m['recall']:.4f} | {m['f1']:.4f} | {m['roc_auc']:.4f} |

- **Dataset:** `{meta['dataset']}`{f" ({meta['dataset_variant']})" if meta.get('dataset_variant') else ""}
- **Train / test samples:** {m['train_samples']} / {m['test_samples']}
- **Features:** {m['feature_count']}
- **Trained:** {meta['trained_at']}

## Files
{files}

## ⚠️ scikit-learn version

Trained with **scikit-learn {SKLEARN_TRAINED_VERSION}**. Install the same version
to avoid `InconsistentVersionWarning` and possible silent breakage:

```bash
pip install scikit-learn=={SKLEARN_TRAINED_VERSION} joblib huggingface_hub
```

## Usage

```python
import joblib
from huggingface_hub import hf_hub_download

repo = "{USER}/{REPOS[meta['model_type']]}"
clf = joblib.load(hf_hub_download(repo, "{meta['files']['model']}"))
vec = joblib.load(hf_hub_download(repo, "{meta['files']['vectorizer']}"))

X = vec.transform(["your text here"])
print(clf.predict(X), clf.predict_proba(X))
```
"""


def main() -> None:
    token = os.environ.get("HF_TOKEN")
    if not token:
        sys.exit("Set HF_TOKEN in the environment.")

    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    private = "--private" in sys.argv
    targets = args or list(REPOS)

    api = HfApi(token=token)
    for model_type in targets:
        folder = MODELS_DIR / model_type
        meta_path = folder / f"{model_type}_metadata.json"
        if not meta_path.exists():
            print(f"skip {model_type}: no metadata at {meta_path}")
            continue

        meta = json.loads(meta_path.read_text())
        (folder / "README.md").write_text(make_card(meta))

        repo_id = f"{USER}/{REPOS[model_type]}"
        api.create_repo(repo_id, repo_type="model", exist_ok=True, private=private)
        api.upload_folder(folder_path=str(folder), repo_id=repo_id, repo_type="model")
        print(f"published https://huggingface.co/{repo_id}")


if __name__ == "__main__":
    main()
