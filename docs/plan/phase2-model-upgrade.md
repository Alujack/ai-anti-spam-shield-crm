# Phase 2: Model Upgrade - DistilBERT Implementation

> **Duration:** 2 Weeks
> **Priority:** Critical
> **Dependencies:** Phase 1 (Infrastructure)

---

## Overview

Replace the TF-IDF + Logistic Regression models with transformer-based models (DistilBERT/MiniLM) for significantly improved accuracy and recall, especially for phishing detection.

### Goals

1. Train DistilBERT model for SMS spam detection
2. Implement class-weighted loss to reduce false negatives
3. Export models to ONNX format for fast inference
4. Maintain backward compatibility with v1 endpoints
5. Achieve target metrics: Recall > 95%, F1 > 92%

### Deliverables

- [ ] DistilBERT training pipeline
- [ ] ONNX model exporter
- [ ] Transformer-based predictor class
- [ ] `/predict-v2` endpoint
- [ ] Model comparison report

---

## 1. Model Architecture

### 1.1 Current vs Target

| Aspect | Current (v1) | Target (v2) |
|--------|--------------|-------------|
| **Model** | TF-IDF + Logistic Regression | DistilBERT + Classification Head |
| **Parameters** | ~50K | ~66M (DistilBERT) |
| **Inference** | CPU, ~10ms | ONNX, ~50ms (CPU) / ~10ms (GPU) |
| **SMS Recall** | 89% | >95% |
| **Phishing Recall** | 51% | >90% |
| **Context Window** | Bag of words | 512 tokens with attention |

### 1.2 Model Selection

```
┌─────────────────────────────────────────────────────────────┐
│                    MODEL COMPARISON                         │
├─────────────────────────────────────────────────────────────┤
│  Model          │ Size   │ Speed  │ Quality │ Recommended  │
├─────────────────────────────────────────────────────────────┤
│  BERT-base      │ 440MB  │ Slow   │ Best    │ No (too big) │
│  DistilBERT     │ 260MB  │ Medium │ Great   │ Yes (SMS)    │
│  MiniLM-L6      │ 80MB   │ Fast   │ Good    │ Yes (backup) │
│  TinyBERT       │ 60MB   │ Fastest│ OK      │ No           │
└─────────────────────────────────────────────────────────────┘

Decision: Use DistilBERT for quality, fallback to MiniLM if latency is critical
```

---

## 2. Training Pipeline

### 2.1 Data Preparation

**Create:** `/ai-anti-spam-shield-service-model/app/model/data_loader.py`

```python
"""
Data loader for SMS spam and phishing datasets
Handles class imbalance and data augmentation
"""

import pandas as pd
import numpy as np
from datasets import load_dataset, Dataset, DatasetDict
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from typing import Tuple, Dict, List
import re
import logging

logger = logging.getLogger(__name__)


class SpamDataLoader:
    """Load and preprocess spam detection datasets"""

    def __init__(self, max_length: int = 128):
        self.max_length = max_length
        self.label_map = {"ham": 0, "spam": 1}

    def load_sms_dataset(self) -> DatasetDict:
        """
        Load SMS Spam Collection dataset from HuggingFace
        """
        logger.info("Loading SMS Spam Collection dataset...")

        # Load the dataset
        dataset = load_dataset("sms_spam")

        # Rename columns for consistency
        def preprocess(example):
            return {
                "text": self.clean_text(example["sms"]),
                "label": example["label"],  # 0 = ham, 1 = spam
            }

        dataset = dataset.map(preprocess, remove_columns=["sms"])

        # Split into train/val/test
        train_val = dataset["train"].train_test_split(test_size=0.2, seed=42)
        val_test = train_val["test"].train_test_split(test_size=0.5, seed=42)

        return DatasetDict({
            "train": train_val["train"],
            "validation": val_test["train"],
            "test": val_test["test"],
        })

    def load_phishing_dataset(self) -> DatasetDict:
        """
        Load phishing email dataset
        """
        logger.info("Loading phishing dataset...")

        # Try multiple sources
        try:
            dataset = load_dataset("ealvaradob/phishing-dataset")
        except:
            # Fallback to local data or another source
            logger.warning("Could not load phishing dataset from HuggingFace")
            return self._create_synthetic_phishing_data()

        def preprocess(example):
            return {
                "text": self.clean_text(example["text"]),
                "label": 1 if example["label"] == "phishing" else 0,
            }

        dataset = dataset.map(preprocess)

        # Split
        train_val = dataset["train"].train_test_split(test_size=0.2, seed=42)
        val_test = train_val["test"].train_test_split(test_size=0.5, seed=42)

        return DatasetDict({
            "train": train_val["train"],
            "validation": val_test["train"],
            "test": val_test["test"],
        })

    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove URLs (but keep indicator that URL was present)
        text = re.sub(r'http\S+|www\.\S+', ' [URL] ', text)

        # Remove phone numbers (but keep indicator)
        text = re.sub(r'\b\d{10,}\b', ' [PHONE] ', text)
        text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', ' [PHONE] ', text)

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def compute_class_weights(self, labels: List[int]) -> Dict[int, float]:
        """
        Compute class weights for imbalanced datasets
        """
        unique_labels = np.unique(labels)
        weights = compute_class_weight(
            class_weight='balanced',
            classes=unique_labels,
            y=labels
        )

        weight_dict = {int(label): float(weight)
                       for label, weight in zip(unique_labels, weights)}

        logger.info(f"Class weights: {weight_dict}")
        return weight_dict

    def augment_minority_class(self, dataset: Dataset,
                               target_ratio: float = 0.4) -> Dataset:
        """
        Augment minority class (spam) using simple techniques
        """
        labels = dataset["label"]
        spam_count = sum(labels)
        ham_count = len(labels) - spam_count

        current_ratio = spam_count / len(labels)
        logger.info(f"Current spam ratio: {current_ratio:.2%}")

        if current_ratio >= target_ratio:
            return dataset

        # Calculate how many spam samples to add
        target_spam = int(ham_count * target_ratio / (1 - target_ratio))
        samples_to_add = target_spam - spam_count

        logger.info(f"Augmenting {samples_to_add} spam samples...")

        # Get spam samples
        spam_indices = [i for i, l in enumerate(labels) if l == 1]
        spam_samples = dataset.select(spam_indices)

        # Simple augmentation: random sampling with replacement
        augmented_indices = np.random.choice(
            len(spam_samples),
            size=samples_to_add,
            replace=True
        )
        augmented = spam_samples.select(augmented_indices)

        # Concatenate
        from datasets import concatenate_datasets
        return concatenate_datasets([dataset, augmented])

    def _create_synthetic_phishing_data(self) -> DatasetDict:
        """Create synthetic phishing data for testing"""
        phishing_templates = [
            "Your account has been compromised. Click here to verify: [URL]",
            "Urgent: Update your payment information immediately",
            "You have won $1,000,000! Claim now at [URL]",
            "Your package is waiting. Confirm delivery: [URL]",
            "Security alert: Unusual activity detected on your account",
        ]

        safe_templates = [
            "Meeting scheduled for tomorrow at 3pm",
            "Thanks for your order. Shipping confirmation attached.",
            "Reminder: Doctor appointment on Friday",
            "Happy birthday! Hope you have a great day.",
            "Project update: All tasks completed on schedule",
        ]

        data = {
            "text": phishing_templates * 100 + safe_templates * 100,
            "label": [1] * 500 + [0] * 500,
        }

        dataset = Dataset.from_dict(data)
        splits = dataset.train_test_split(test_size=0.3, seed=42)
        val_test = splits["test"].train_test_split(test_size=0.5, seed=42)

        return DatasetDict({
            "train": splits["train"],
            "validation": val_test["train"],
            "test": val_test["test"],
        })


class DataCollator:
    """Custom data collator for training"""

    def __init__(self, tokenizer, max_length: int = 128):
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __call__(self, features: List[Dict]) -> Dict:
        texts = [f["text"] for f in features]
        labels = [f["label"] for f in features]

        # Tokenize
        encoding = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )

        import torch
        encoding["labels"] = torch.tensor(labels)

        return encoding
```

### 2.2 Transformer Trainer

**Create:** `/ai-anti-spam-shield-service-model/app/model/transformer_trainer.py`

```python
"""
Fine-tune DistilBERT for spam/phishing detection
with class-weighted loss for handling imbalance
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from transformers import (
    DistilBertTokenizer,
    DistilBertForSequenceClassification,
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback,
)
from datasets import DatasetDict
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report,
)
from typing import Dict, Optional, Tuple
import logging
import os
from datetime import datetime

from .data_loader import SpamDataLoader, DataCollator

logger = logging.getLogger(__name__)


class WeightedLossTrainer(Trainer):
    """Custom Trainer with class-weighted loss"""

    def __init__(self, class_weights: Dict[int, float] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if class_weights:
            weights = torch.tensor([class_weights[0], class_weights[1]])
            self.class_weights = weights.to(self.args.device)
        else:
            self.class_weights = None

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits

        if self.class_weights is not None:
            loss_fn = nn.CrossEntropyLoss(weight=self.class_weights)
        else:
            loss_fn = nn.CrossEntropyLoss()

        loss = loss_fn(logits, labels)

        return (loss, outputs) if return_outputs else loss


class TransformerTrainer:
    """
    Train transformer models for spam/phishing detection

    Usage:
        trainer = TransformerTrainer(model_type="sms")
        trainer.train(epochs=3)
        trainer.export_onnx("model.onnx")
    """

    SUPPORTED_MODELS = {
        "distilbert": "distilbert-base-uncased",
        "minilm": "microsoft/MiniLM-L6-H384-uncased",
        "roberta": "distilroberta-base",
    }

    def __init__(
        self,
        model_type: str = "sms",  # sms, phishing, voice
        base_model: str = "distilbert",
        output_dir: str = "./trained_models",
        max_length: int = 128,
    ):
        self.model_type = model_type
        self.base_model_name = self.SUPPORTED_MODELS.get(base_model, base_model)
        self.output_dir = os.path.join(output_dir, model_type)
        self.max_length = max_length

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)

        # Initialize tokenizer and model
        logger.info(f"Loading {self.base_model_name}...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.base_model_name,
            num_labels=2,
            problem_type="single_label_classification",
        )

        # Data loader
        self.data_loader = SpamDataLoader(max_length=max_length)
        self.dataset = None
        self.class_weights = None

    def load_data(self, augment: bool = True) -> DatasetDict:
        """Load and prepare dataset"""
        logger.info(f"Loading {self.model_type} dataset...")

        if self.model_type == "sms":
            self.dataset = self.data_loader.load_sms_dataset()
        elif self.model_type == "phishing":
            self.dataset = self.data_loader.load_phishing_dataset()
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        # Augment minority class if needed
        if augment:
            self.dataset["train"] = self.data_loader.augment_minority_class(
                self.dataset["train"]
            )

        # Compute class weights
        labels = self.dataset["train"]["label"]
        self.class_weights = self.data_loader.compute_class_weights(labels)

        # Log dataset stats
        for split in ["train", "validation", "test"]:
            total = len(self.dataset[split])
            spam = sum(self.dataset[split]["label"])
            logger.info(f"{split}: {total} samples ({spam} spam, {total-spam} ham)")

        return self.dataset

    def tokenize_dataset(self) -> DatasetDict:
        """Tokenize the dataset"""
        def tokenize(examples):
            return self.tokenizer(
                examples["text"],
                padding="max_length",
                truncation=True,
                max_length=self.max_length,
            )

        self.dataset = self.dataset.map(tokenize, batched=True)
        self.dataset.set_format("torch", columns=["input_ids", "attention_mask", "label"])

        return self.dataset

    def compute_metrics(self, eval_pred) -> Dict:
        """Compute metrics for evaluation"""
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)

        accuracy = accuracy_score(labels, predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(
            labels, predictions, average="binary"
        )

        # Confusion matrix
        cm = confusion_matrix(labels, predictions)
        tn, fp, fn, tp = cm.ravel()

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        }

    def train(
        self,
        epochs: int = 3,
        batch_size: int = 16,
        learning_rate: float = 2e-5,
        warmup_steps: int = 500,
        weight_decay: float = 0.01,
        early_stopping_patience: int = 3,
    ) -> Dict:
        """
        Fine-tune the model

        Returns:
            Training metrics
        """
        if self.dataset is None:
            self.load_data()
            self.tokenize_dataset()

        # Training arguments
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size * 2,
            learning_rate=learning_rate,
            warmup_steps=warmup_steps,
            weight_decay=weight_decay,
            evaluation_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="recall",  # Optimize for recall
            greater_is_better=True,
            logging_dir=os.path.join(self.output_dir, "logs"),
            logging_steps=100,
            save_total_limit=2,
            push_to_hub=False,
            fp16=torch.cuda.is_available(),  # Mixed precision if GPU available
        )

        # Create trainer with class weights
        trainer = WeightedLossTrainer(
            class_weights=self.class_weights,
            model=self.model,
            args=training_args,
            train_dataset=self.dataset["train"],
            eval_dataset=self.dataset["validation"],
            tokenizer=self.tokenizer,
            compute_metrics=self.compute_metrics,
            callbacks=[
                EarlyStoppingCallback(early_stopping_patience=early_stopping_patience)
            ],
        )

        # Train
        logger.info("Starting training...")
        train_result = trainer.train()

        # Evaluate on test set
        logger.info("Evaluating on test set...")
        test_results = trainer.evaluate(self.dataset["test"])

        # Save model
        trainer.save_model(os.path.join(self.output_dir, "best_model"))
        self.tokenizer.save_pretrained(os.path.join(self.output_dir, "best_model"))

        # Save metrics
        metrics = {
            "train": train_result.metrics,
            "test": test_results,
            "model_type": self.model_type,
            "base_model": self.base_model_name,
            "trained_at": datetime.now().isoformat(),
            "class_weights": self.class_weights,
        }

        import json
        with open(os.path.join(self.output_dir, "metrics.json"), "w") as f:
            json.dump(metrics, f, indent=2, default=str)

        logger.info(f"Training complete. Test metrics: {test_results}")

        return metrics

    def evaluate_detailed(self, split: str = "test") -> str:
        """Get detailed classification report"""
        if self.dataset is None:
            raise ValueError("No dataset loaded. Call load_data() first.")

        # Get predictions
        self.model.eval()
        predictions = []
        labels = []

        for example in self.dataset[split]:
            inputs = self.tokenizer(
                example["text"],
                return_tensors="pt",
                truncation=True,
                max_length=self.max_length,
            )

            with torch.no_grad():
                outputs = self.model(**inputs)
                pred = torch.argmax(outputs.logits, dim=-1).item()

            predictions.append(pred)
            labels.append(example["label"])

        # Classification report
        report = classification_report(
            labels,
            predictions,
            target_names=["ham/safe", "spam/phishing"],
            digits=4,
        )

        return report


def train_all_models():
    """Train all model types"""
    model_types = ["sms", "phishing"]
    results = {}

    for model_type in model_types:
        logger.info(f"\n{'='*50}")
        logger.info(f"Training {model_type} model")
        logger.info('='*50)

        trainer = TransformerTrainer(
            model_type=model_type,
            base_model="distilbert",
        )

        metrics = trainer.train(epochs=3)
        results[model_type] = metrics

        # Print detailed report
        print(f"\n{model_type.upper()} Classification Report:")
        print(trainer.evaluate_detailed())

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_all_models()
```

### 2.3 ONNX Exporter

**Create:** `/ai-anti-spam-shield-service-model/app/model/onnx_exporter.py`

```python
"""
Export trained models to ONNX format for fast inference
"""

import torch
import onnx
import onnxruntime as ort
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from typing import Tuple, Dict, Optional
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class ONNXExporter:
    """
    Export PyTorch transformer models to ONNX format

    Benefits of ONNX:
    - 2-10x faster inference
    - Smaller memory footprint
    - Cross-platform compatibility
    - No PyTorch dependency at runtime
    """

    def __init__(self, model_path: str, output_dir: str = "./onnx_models"):
        self.model_path = model_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Load model and tokenizer
        logger.info(f"Loading model from {model_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.eval()

    def export(
        self,
        output_name: str = "model.onnx",
        max_length: int = 128,
        opset_version: int = 14,
        optimize: bool = True,
    ) -> str:
        """
        Export model to ONNX format

        Args:
            output_name: Output filename
            max_length: Maximum sequence length
            opset_version: ONNX opset version
            optimize: Whether to optimize the model

        Returns:
            Path to exported model
        """
        output_path = os.path.join(self.output_dir, output_name)

        # Create dummy input
        dummy_text = "This is a sample text for export"
        dummy_input = self.tokenizer(
            dummy_text,
            return_tensors="pt",
            padding="max_length",
            truncation=True,
            max_length=max_length,
        )

        # Dynamic axes for variable batch size and sequence length
        dynamic_axes = {
            "input_ids": {0: "batch_size", 1: "sequence_length"},
            "attention_mask": {0: "batch_size", 1: "sequence_length"},
            "output": {0: "batch_size"},
        }

        logger.info(f"Exporting to ONNX (opset {opset_version})...")

        # Export
        torch.onnx.export(
            self.model,
            (dummy_input["input_ids"], dummy_input["attention_mask"]),
            output_path,
            input_names=["input_ids", "attention_mask"],
            output_names=["output"],
            dynamic_axes=dynamic_axes,
            opset_version=opset_version,
            do_constant_folding=True,
        )

        # Verify export
        logger.info("Verifying ONNX model...")
        onnx_model = onnx.load(output_path)
        onnx.checker.check_model(onnx_model)

        # Optimize if requested
        if optimize:
            output_path = self._optimize_model(output_path)

        # Save tokenizer alongside
        self.tokenizer.save_pretrained(self.output_dir)

        # Verify inference
        self._verify_inference(output_path, max_length)

        logger.info(f"Model exported to {output_path}")
        return output_path

    def _optimize_model(self, model_path: str) -> str:
        """Optimize ONNX model for inference"""
        from onnxruntime.transformers import optimizer

        optimized_path = model_path.replace(".onnx", "_optimized.onnx")

        logger.info("Optimizing ONNX model...")

        optimized_model = optimizer.optimize_model(
            model_path,
            model_type="bert",
            num_heads=12,  # DistilBERT has 12 heads
            hidden_size=768,  # DistilBERT hidden size
            optimization_options=None,
        )

        optimized_model.save_model_to_file(optimized_path)

        # Compare sizes
        original_size = os.path.getsize(model_path) / (1024 * 1024)
        optimized_size = os.path.getsize(optimized_path) / (1024 * 1024)
        logger.info(f"Size: {original_size:.1f}MB -> {optimized_size:.1f}MB")

        return optimized_path

    def _verify_inference(self, model_path: str, max_length: int):
        """Verify ONNX model produces correct output"""
        # Create ONNX session
        session = ort.InferenceSession(model_path)

        # Test inputs
        test_texts = [
            "Hello, how are you today?",
            "URGENT: You won $1000! Click here now!",
            "Your Amazon order has shipped",
        ]

        logger.info("Verifying inference...")

        for text in test_texts:
            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="np",
                padding="max_length",
                truncation=True,
                max_length=max_length,
            )

            # Run inference
            onnx_output = session.run(
                None,
                {
                    "input_ids": inputs["input_ids"],
                    "attention_mask": inputs["attention_mask"],
                }
            )[0]

            # Compare with PyTorch
            with torch.no_grad():
                torch_output = self.model(
                    torch.tensor(inputs["input_ids"]),
                    torch.tensor(inputs["attention_mask"]),
                ).logits.numpy()

            # Check similarity
            diff = np.abs(onnx_output - torch_output).max()
            logger.info(f"Max diff for '{text[:30]}...': {diff:.6f}")

            if diff > 0.01:
                logger.warning(f"Large difference detected!")

        logger.info("Inference verification complete")

    def benchmark(self, model_path: str, num_runs: int = 100) -> Dict:
        """Benchmark ONNX vs PyTorch inference speed"""
        import time

        session = ort.InferenceSession(model_path)

        # Prepare input
        test_text = "This is a sample text for benchmarking inference speed."
        inputs = self.tokenizer(
            test_text,
            return_tensors="np",
            padding="max_length",
            truncation=True,
            max_length=128,
        )

        # Warmup
        for _ in range(10):
            session.run(None, {
                "input_ids": inputs["input_ids"],
                "attention_mask": inputs["attention_mask"],
            })

        # ONNX benchmark
        start = time.time()
        for _ in range(num_runs):
            session.run(None, {
                "input_ids": inputs["input_ids"],
                "attention_mask": inputs["attention_mask"],
            })
        onnx_time = (time.time() - start) / num_runs * 1000  # ms

        # PyTorch benchmark
        torch_inputs = {
            "input_ids": torch.tensor(inputs["input_ids"]),
            "attention_mask": torch.tensor(inputs["attention_mask"]),
        }

        # Warmup
        for _ in range(10):
            with torch.no_grad():
                self.model(**torch_inputs)

        start = time.time()
        for _ in range(num_runs):
            with torch.no_grad():
                self.model(**torch_inputs)
        pytorch_time = (time.time() - start) / num_runs * 1000  # ms

        results = {
            "onnx_ms": round(onnx_time, 2),
            "pytorch_ms": round(pytorch_time, 2),
            "speedup": round(pytorch_time / onnx_time, 2),
        }

        logger.info(f"Benchmark results: {results}")
        return results


def export_all_models():
    """Export all trained models to ONNX"""
    model_types = ["sms", "phishing"]

    for model_type in model_types:
        model_path = f"./trained_models/{model_type}/best_model"

        if not os.path.exists(model_path):
            logger.warning(f"Model not found: {model_path}")
            continue

        logger.info(f"\n{'='*50}")
        logger.info(f"Exporting {model_type} model")
        logger.info('='*50)

        exporter = ONNXExporter(
            model_path=model_path,
            output_dir=f"./onnx_models/{model_type}",
        )

        output_path = exporter.export(
            output_name=f"{model_type}_model.onnx",
            optimize=True,
        )

        # Benchmark
        benchmark = exporter.benchmark(output_path)
        logger.info(f"Speedup: {benchmark['speedup']}x")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    export_all_models()
```

### 2.4 Transformer Predictor (v2)

**Create:** `/ai-anti-spam-shield-service-model/app/model/predictor_v2.py`

```python
"""
Transformer-based spam/phishing predictor using ONNX
for fast inference in production
"""

import onnxruntime as ort
from transformers import AutoTokenizer
import numpy as np
from typing import Dict, Optional, List, Tuple
import logging
import os
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ScamCategory(Enum):
    NONE = "NONE"
    PRIZE = "PRIZE_SCAM"
    BANK = "BANK_FRAUD"
    CRYPTO = "CRYPTO_SCAM"
    PHISHING = "CREDENTIAL_THEFT"
    IMPERSONATION = "IMPERSONATION"
    URGENCY = "URGENCY_SCAM"
    ROMANCE = "ROMANCE_SCAM"
    TECH_SUPPORT = "TECH_SUPPORT_SCAM"


@dataclass
class PredictionResult:
    """Structured prediction result"""
    is_spam: bool
    confidence: float
    prediction: str
    risk_level: str
    category: Optional[str]
    explanation: str
    indicators: List[Dict]
    model_version: str

    def to_dict(self) -> Dict:
        return {
            "is_spam": self.is_spam,
            "confidence": self.confidence,
            "prediction": self.prediction,
            "risk_level": self.risk_level,
            "category": self.category,
            "explanation": self.explanation,
            "indicators": self.indicators,
            "model_version": self.model_version,
        }


class TransformerPredictor:
    """
    Production predictor using ONNX models

    Features:
    - Fast inference with ONNX Runtime
    - Confidence calibration
    - Risk level classification
    - Scam category detection
    - Human-readable explanations
    """

    # Scam indicator patterns
    SCAM_PATTERNS = {
        ScamCategory.PRIZE: [
            r"won", r"winner", r"prize", r"lottery", r"congratulations",
            r"claim", r"reward", r"\$\d+", r"million",
        ],
        ScamCategory.BANK: [
            r"bank", r"account", r"suspend", r"verify", r"confirm",
            r"transaction", r"unauthorized", r"fraud",
        ],
        ScamCategory.CRYPTO: [
            r"bitcoin", r"btc", r"crypto", r"invest", r"trading",
            r"wallet", r"blockchain", r"profit",
        ],
        ScamCategory.PHISHING: [
            r"password", r"login", r"credential", r"expire",
            r"click here", r"verify", r"update.*account",
        ],
        ScamCategory.URGENCY: [
            r"urgent", r"immediate", r"now", r"expire", r"limited",
            r"act fast", r"don't miss", r"last chance",
        ],
        ScamCategory.IMPERSONATION: [
            r"amazon", r"paypal", r"apple", r"microsoft", r"google",
            r"netflix", r"facebook", r"instagram",
        ],
    }

    def __init__(
        self,
        model_type: str = "sms",
        model_dir: str = "./onnx_models",
        use_gpu: bool = False,
        confidence_threshold: float = 0.5,
    ):
        self.model_type = model_type
        self.model_dir = os.path.join(model_dir, model_type)
        self.confidence_threshold = confidence_threshold

        # Load ONNX model
        model_path = os.path.join(self.model_dir, f"{model_type}_model_optimized.onnx")
        if not os.path.exists(model_path):
            model_path = os.path.join(self.model_dir, f"{model_type}_model.onnx")

        logger.info(f"Loading ONNX model from {model_path}")

        # Configure session
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if use_gpu else ['CPUExecutionProvider']

        self.session = ort.InferenceSession(model_path, providers=providers)

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)

        # Model version
        self.model_version = f"{model_type}-v2.0.0"

        logger.info(f"Predictor initialized: {self.model_version}")

    def predict(self, text: str) -> PredictionResult:
        """
        Predict spam/phishing for a single text

        Args:
            text: Input text to classify

        Returns:
            Structured prediction result
        """
        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="np",
            padding="max_length",
            truncation=True,
            max_length=128,
        )

        # Run inference
        outputs = self.session.run(
            None,
            {
                "input_ids": inputs["input_ids"],
                "attention_mask": inputs["attention_mask"],
            }
        )[0]

        # Apply softmax
        probs = self._softmax(outputs[0])
        confidence = float(probs[1])  # Spam/phishing probability

        is_spam = confidence >= self.confidence_threshold

        # Determine risk level
        risk_level = self._get_risk_level(confidence)

        # Detect scam category
        category, indicators = self._detect_category(text, is_spam)

        # Generate explanation
        explanation = self._generate_explanation(
            is_spam, confidence, category, indicators
        )

        return PredictionResult(
            is_spam=is_spam,
            confidence=round(confidence, 4),
            prediction="spam" if is_spam else "ham",
            risk_level=risk_level.value,
            category=category.value if category else None,
            explanation=explanation,
            indicators=indicators,
            model_version=self.model_version,
        )

    def predict_batch(self, texts: List[str]) -> List[PredictionResult]:
        """Predict for multiple texts"""
        return [self.predict(text) for text in texts]

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Apply softmax to logits"""
        exp_x = np.exp(x - np.max(x))
        return exp_x / exp_x.sum()

    def _get_risk_level(self, confidence: float) -> RiskLevel:
        """Map confidence to risk level"""
        if confidence < 0.3:
            return RiskLevel.NONE
        elif confidence < 0.5:
            return RiskLevel.LOW
        elif confidence < 0.7:
            return RiskLevel.MEDIUM
        elif confidence < 0.9:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def _detect_category(
        self, text: str, is_spam: bool
    ) -> Tuple[Optional[ScamCategory], List[Dict]]:
        """Detect scam category based on patterns"""
        import re

        if not is_spam:
            return None, []

        text_lower = text.lower()
        indicators = []
        category_scores = {}

        for category, patterns in self.SCAM_PATTERNS.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, text_lower)
                if found:
                    matches.extend(found)

            if matches:
                category_scores[category] = len(matches)
                for match in matches[:3]:  # Limit to 3 indicators per category
                    indicators.append({
                        "type": category.value.lower(),
                        "text": match,
                        "weight": 0.1 * len(matches),
                    })

        # Return highest scoring category
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            return best_category, indicators

        return ScamCategory.NONE, []

    def _generate_explanation(
        self,
        is_spam: bool,
        confidence: float,
        category: Optional[ScamCategory],
        indicators: List[Dict],
    ) -> str:
        """Generate human-readable explanation"""
        if not is_spam:
            return "This message appears to be legitimate."

        explanations = {
            ScamCategory.PRIZE: "This message contains prize/lottery claims which are commonly used in scams.",
            ScamCategory.BANK: "This message mimics bank communications and may be attempting to steal financial information.",
            ScamCategory.CRYPTO: "This message promotes cryptocurrency investments which are often scams.",
            ScamCategory.PHISHING: "This message is attempting to steal login credentials or personal information.",
            ScamCategory.URGENCY: "This message uses urgency tactics to pressure you into acting quickly.",
            ScamCategory.IMPERSONATION: "This message impersonates a known brand or company.",
            ScamCategory.NONE: "This message shows characteristics typical of spam or scam messages.",
        }

        base_explanation = explanations.get(category, explanations[ScamCategory.NONE])

        # Add confidence qualifier
        if confidence > 0.9:
            qualifier = "This is highly likely to be a scam."
        elif confidence > 0.7:
            qualifier = "This is likely a scam. Exercise caution."
        else:
            qualifier = "This message shows some suspicious characteristics."

        return f"{base_explanation} {qualifier}"

    def get_elder_warnings(
        self, result: PredictionResult
    ) -> List[str]:
        """
        Generate elder-friendly warnings

        Designed for users who may be more vulnerable to scams
        """
        if not result.is_spam:
            return []

        warnings = [
            "Take your time - real businesses never pressure you to act immediately.",
            "Never share passwords, PINs, or bank details over text or phone.",
            "If unsure, call the company directly using a number from their official website.",
        ]

        category_warnings = {
            ScamCategory.PRIZE.value: [
                "Real prizes never require payment to claim.",
                "You cannot win a lottery you didn't enter.",
            ],
            ScamCategory.BANK.value: [
                "Banks will never ask for your full password.",
                "Call your bank directly if you're concerned about your account.",
            ],
            ScamCategory.URGENCY.value: [
                "Scammers create false urgency to prevent you from thinking clearly.",
                "It's always okay to wait and verify before responding.",
            ],
        }

        if result.category in category_warnings:
            warnings.extend(category_warnings[result.category])

        return warnings[:5]  # Limit to 5 warnings


class MultiModelPredictor:
    """
    Unified predictor for all model types
    """

    def __init__(self, model_dir: str = "./onnx_models"):
        self.predictors = {}

        for model_type in ["sms", "phishing"]:
            model_path = os.path.join(model_dir, model_type)
            if os.path.exists(model_path):
                self.predictors[model_type] = TransformerPredictor(
                    model_type=model_type,
                    model_dir=model_dir,
                )

    def predict_sms(self, text: str) -> Dict:
        if "sms" not in self.predictors:
            raise ValueError("SMS model not loaded")
        return self.predictors["sms"].predict(text).to_dict()

    def predict_phishing(self, text: str) -> Dict:
        if "phishing" not in self.predictors:
            raise ValueError("Phishing model not loaded")
        return self.predictors["phishing"].predict(text).to_dict()

    def predict_with_elder_mode(self, text: str, model_type: str = "sms") -> Dict:
        if model_type not in self.predictors:
            raise ValueError(f"Model {model_type} not loaded")

        predictor = self.predictors[model_type]
        result = predictor.predict(text)

        return {
            **result.to_dict(),
            "elder_warnings": predictor.get_elder_warnings(result),
        }
```

---

## 3. FastAPI Integration

### 3.1 New Endpoints

**Modify:** `/ai-anti-spam-shield-service-model/app/main.py`

Add the following endpoints:

```python
from app.model.predictor_v2 import TransformerPredictor, MultiModelPredictor

# Initialize v2 predictors (add near the top)
try:
    multi_predictor_v2 = MultiModelPredictor(model_dir="./onnx_models")
    v2_available = True
except Exception as e:
    logger.warning(f"V2 models not available: {e}")
    v2_available = False


@app.post("/predict-v2")
async def predict_v2(request: MessageRequest):
    """
    Predict spam using transformer model (v2)

    Returns enhanced response with:
    - Risk level
    - Scam category
    - Human-readable explanation
    - Indicator breakdown
    """
    if not v2_available:
        raise HTTPException(
            status_code=503,
            detail="V2 model not available. Use /predict for v1."
        )

    try:
        result = multi_predictor_v2.predict_sms(request.message)
        return result
    except Exception as e:
        logger.error(f"V2 prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict-v2/elder-mode")
async def predict_v2_elder(request: MessageRequest):
    """
    Predict with elder-friendly warnings

    Includes additional safety warnings for vulnerable users
    """
    if not v2_available:
        raise HTTPException(
            status_code=503,
            detail="V2 model not available."
        )

    try:
        result = multi_predictor_v2.predict_with_elder_mode(
            request.message,
            model_type="sms"
        )
        return result
    except Exception as e:
        logger.error(f"V2 elder mode error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict-phishing-v2")
async def predict_phishing_v2(request: PhishingRequest):
    """
    Predict phishing using transformer model (v2)
    """
    if not v2_available:
        raise HTTPException(
            status_code=503,
            detail="V2 model not available."
        )

    try:
        result = multi_predictor_v2.predict_phishing(request.text)
        return {
            **result,
            "is_phishing": result["is_spam"],
            "phishing_type": result.get("category", "NONE"),
            "threat_level": result["risk_level"],
        }
    except Exception as e:
        logger.error(f"V2 phishing prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/model/versions")
async def get_model_versions():
    """Get available model versions"""
    versions = {
        "v1": {
            "sms": "TF-IDF + Logistic Regression",
            "phishing": "TF-IDF + Random Forest",
            "status": "available",
        }
    }

    if v2_available:
        versions["v2"] = {
            "sms": "DistilBERT (ONNX)",
            "phishing": "DistilBERT (ONNX)",
            "status": "available",
        }

    return {"versions": versions}
```

---

## 4. Dependencies

### 4.1 Update requirements.txt

**Modify:** `/ai-anti-spam-shield-service-model/requirements.txt`

```
# Core ML
torch>=2.2.0
transformers>=4.40.0
datasets>=2.18.0
scikit-learn>=1.4.0

# ONNX
onnx>=1.15.0
onnxruntime>=1.17.0
# onnxruntime-gpu>=1.17.0  # Uncomment for GPU support

# Data processing
numpy>=1.26.0
pandas>=2.2.0

# API
fastapi>=0.110.0
uvicorn>=0.27.0
python-multipart>=0.0.9

# Existing dependencies
nltk>=3.8.0
speech_recognition>=3.10.0
pydub>=0.25.0
requests>=2.31.0

# Metrics and logging
mlflow>=2.10.0
tensorboard>=2.16.0

# Utilities
python-dotenv>=1.0.0
tqdm>=4.66.0
```

---

## 5. Training Commands

### 5.1 Train Models

```bash
# Navigate to ML service directory
cd /opt/school-project/ai-anti-spam-shield/ai-anti-spam-shield-service-model

# Install dependencies
pip install -r requirements.txt

# Train SMS model
python -m app.model.transformer_trainer

# Export to ONNX
python -m app.model.onnx_exporter

# Verify models
python -c "from app.model.predictor_v2 import MultiModelPredictor; p = MultiModelPredictor(); print(p.predict_sms('You won a prize!'))"
```

### 5.2 Expected Output

```
Training SMS model...
Loading distilbert-base-uncased...
Loading SMS Spam Collection dataset...
train: 4457 samples (600 spam, 3857 ham)
validation: 557 samples (75 spam, 482 ham)
test: 558 samples (72 spam, 486 ham)
Class weights: {0: 0.58, 1: 4.29}
Starting training...
Epoch 1/3: loss=0.234, recall=0.89
Epoch 2/3: loss=0.112, recall=0.94
Epoch 3/3: loss=0.067, recall=0.96
Evaluating on test set...
Test metrics: {'accuracy': 0.987, 'precision': 0.953, 'recall': 0.958, 'f1': 0.955}
Training complete.

Exporting to ONNX...
Size: 260.4MB -> 180.2MB
Benchmark: ONNX 42ms, PyTorch 156ms, Speedup: 3.7x
```

---

## 6. Verification Checklist

### 6.1 Model Quality

- [ ] SMS Recall > 95%
- [ ] SMS F1 > 92%
- [ ] Phishing Recall > 90%
- [ ] False Positive Rate < 5%

### 6.2 Performance

- [ ] ONNX inference < 100ms (CPU)
- [ ] ONNX inference < 20ms (GPU)
- [ ] Batch processing supports 100+ texts

### 6.3 API

- [ ] `/predict-v2` returns enhanced response
- [ ] `/predict-v2/elder-mode` includes warnings
- [ ] `/model/versions` shows v1 and v2
- [ ] V1 endpoints still work (backward compatibility)

---

## 7. Rollback Plan

If v2 models underperform:

1. Keep v2 endpoint disabled
2. Route all traffic to v1
3. Collect more training data
4. Retrain with adjusted hyperparameters

```python
# In main.py, disable v2:
v2_available = False  # Force disable

# Or in environment:
# V2_MODELS_ENABLED=false
```

---

## Next Steps

After completing Phase 2:
1. Run A/B test between v1 and v2
2. Monitor false positive/negative rates
3. Proceed to [Phase 3: Phishing Intelligence](./phase3-phishing-intel.md)
