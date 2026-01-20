"""
Fine-tune DistilBERT for spam/phishing detection
with class-weighted loss for handling imbalance
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from transformers import (
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
            eval_strategy="epoch",
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

        device = next(self.model.parameters()).device

        for example in self.dataset[split]:
            inputs = self.tokenizer(
                example["text"],
                return_tensors="pt",
                truncation=True,
                max_length=self.max_length,
            )

            # Move inputs to same device as model
            inputs = {k: v.to(device) for k, v in inputs.items()}

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
