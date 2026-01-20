"""
Incremental Trainer

Fine-tunes existing models on new feedback data
without full retraining.
"""

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback,
)
from datasets import Dataset
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from typing import Dict, List, Optional
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class IncrementalTrainer:
    """
    Fine-tune existing models on new feedback.

    Key features:
    - Small learning rate (prevents catastrophic forgetting)
    - Few epochs (quick adaptation)
    - Validation on held-out set
    - Automatic rollback if metrics degrade
    """

    def __init__(
        self,
        model_path: str,
        model_type: str = "sms",
        output_dir: str = "./retrained_models",
    ):
        """
        Initialize the incremental trainer.

        Args:
            model_path: Path to existing model
            model_type: Type of model (sms, phishing, voice)
            output_dir: Directory for retrained models
        """
        self.model_path = model_path
        self.model_type = model_type
        self.output_dir = os.path.join(output_dir, model_type)
        os.makedirs(self.output_dir, exist_ok=True)

        # Load existing model
        logger.info(f"Loading model from {model_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)

        # Store original metrics for comparison
        self.original_metrics = None

    def train_on_feedback(
        self,
        texts: List[str],
        labels: List[int],
        validation_split: float = 0.2,
        epochs: int = 2,
        learning_rate: float = 1e-5,
        batch_size: int = 8,
    ) -> Dict:
        """
        Fine-tune model on feedback data.

        Args:
            texts: List of text samples
            labels: List of labels (0 or 1)
            validation_split: Fraction for validation
            epochs: Number of training epochs
            learning_rate: Learning rate (should be small)
            batch_size: Training batch size

        Returns:
            Training metrics and new model path
        """
        logger.info(f"Starting training with {len(texts)} samples")

        # Create dataset
        dataset = Dataset.from_dict({
            "text": texts,
            "label": labels,
        })

        # Tokenize
        def tokenize(examples):
            return self.tokenizer(
                examples["text"],
                padding="max_length",
                truncation=True,
                max_length=128,
            )

        dataset = dataset.map(tokenize, batched=True)

        # Split
        split = dataset.train_test_split(test_size=validation_split, seed=42)
        train_dataset = split["train"]
        val_dataset = split["test"]

        logger.info(f"Train: {len(train_dataset)}, Val: {len(val_dataset)}")

        # Training arguments
        version = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_output_dir = os.path.join(self.output_dir, f"v_{version}")

        training_args = TrainingArguments(
            output_dir=run_output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            learning_rate=learning_rate,
            warmup_ratio=0.1,
            weight_decay=0.01,
            evaluation_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="recall",
            greater_is_better=True,
            logging_steps=10,
            save_total_limit=1,
            fp16=torch.cuda.is_available(),
            report_to=[],  # Disable wandb/tensorboard
        )

        # Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            tokenizer=self.tokenizer,
            compute_metrics=self._compute_metrics,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
        )

        # Evaluate before training (baseline)
        logger.info("Evaluating baseline...")
        baseline_metrics = trainer.evaluate()
        self.original_metrics = baseline_metrics
        logger.info(f"Baseline metrics: {baseline_metrics}")

        # Train
        logger.info("Starting fine-tuning...")
        train_result = trainer.train()
        logger.info(f"Training completed: {train_result}")

        # Evaluate after training
        logger.info("Evaluating after training...")
        new_metrics = trainer.evaluate()
        logger.info(f"New metrics: {new_metrics}")

        # Compare metrics
        improved = self._compare_metrics(baseline_metrics, new_metrics)

        if improved:
            # Save new model
            final_path = os.path.join(self.output_dir, "latest")
            trainer.save_model(final_path)
            self.tokenizer.save_pretrained(final_path)
            logger.info(f"New model saved to {final_path}")

            return {
                "success": True,
                "version": version,
                "baseline_metrics": baseline_metrics,
                "new_metrics": new_metrics,
                "model_path": final_path,
                "improved": True,
            }
        else:
            logger.warning("Metrics degraded, not saving new model")
            return {
                "success": False,
                "version": version,
                "baseline_metrics": baseline_metrics,
                "new_metrics": new_metrics,
                "model_path": None,
                "improved": False,
            }

    def _compute_metrics(self, eval_pred) -> Dict:
        """Compute evaluation metrics."""
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)

        accuracy = accuracy_score(labels, predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(
            labels, predictions, average='binary', zero_division=0
        )

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

    def _compare_metrics(
        self,
        baseline: Dict,
        new: Dict,
        threshold: float = 0.02,
    ) -> bool:
        """
        Compare metrics to decide if new model is better.

        Primary metric: recall (we want to catch more spam)
        Secondary: f1 (balance)

        Degradation threshold: 2%
        """
        baseline_recall = baseline.get("eval_recall", 0)
        new_recall = new.get("eval_recall", 0)

        baseline_f1 = baseline.get("eval_f1", 0)
        new_f1 = new.get("eval_f1", 0)

        # Recall should not decrease significantly
        recall_ok = new_recall >= baseline_recall - threshold

        # F1 should not decrease significantly
        f1_ok = new_f1 >= baseline_f1 - threshold

        # At least one should improve
        improved = new_recall > baseline_recall or new_f1 > baseline_f1

        logger.info(
            f"Metric comparison: recall {baseline_recall:.4f}->{new_recall:.4f}, "
            f"f1 {baseline_f1:.4f}->{new_f1:.4f}"
        )

        return recall_ok and f1_ok and improved


class RetrainingScheduler:
    """
    Schedule and manage retraining jobs.
    """

    def __init__(
        self,
        feedback_collector,
        trainer: IncrementalTrainer,
        model_registry=None,
        min_samples: int = 50,
    ):
        """
        Initialize the retraining scheduler.

        Args:
            feedback_collector: FeedbackCollector instance
            trainer: IncrementalTrainer instance
            model_registry: Optional ModelRegistry instance
            min_samples: Minimum samples required for retraining
        """
        self.collector = feedback_collector
        self.trainer = trainer
        self.registry = model_registry
        self.min_samples = min_samples

    async def run_retraining_job(
        self,
        model_type: str = "sms",
    ) -> Dict:
        """
        Run a complete retraining job.

        Steps:
        1. Collect approved feedback
        2. Check if enough samples
        3. Train new model
        4. Compare with current
        5. Deploy if better
        """
        logger.info(f"Starting retraining job for {model_type}")

        # 1. Collect feedback
        scan_type = "text" if model_type == "sms" else model_type
        feedback = await self.collector.fetch_approved_feedback(
            scan_type=scan_type
        )

        if len(feedback) < self.min_samples:
            logger.warning(
                f"Not enough feedback: {len(feedback)} < {self.min_samples}"
            )
            return {
                "status": "skipped",
                "reason": "insufficient_feedback",
                "sample_count": len(feedback),
            }

        # 2. Prepare data
        texts = [f.text for f in feedback]
        labels = [f.label for f in feedback]

        # 3. Train
        result = self.trainer.train_on_feedback(texts, labels)

        if not result["success"]:
            return {
                "status": "failed",
                "reason": "metrics_degraded",
                "baseline": result["baseline_metrics"],
                "new": result["new_metrics"],
            }

        # 4. Register new version
        if self.registry:
            version_info = await self.registry.register_version(
                model_type=model_type,
                version=result["version"],
                model_path=result["model_path"],
                metrics=result["new_metrics"],
            )

            # 5. Deploy
            await self.registry.deploy_version(
                model_type=model_type,
                version=result["version"],
            )

        return {
            "status": "success",
            "version": result["version"],
            "metrics": result["new_metrics"],
            "improvement": {
                "recall": result["new_metrics"]["eval_recall"] - result["baseline_metrics"]["eval_recall"],
                "f1": result["new_metrics"]["eval_f1"] - result["baseline_metrics"]["eval_f1"],
            },
        }


def create_trainer_for_model(
    model_type: str,
    model_paths: Dict[str, str],
    output_dir: str = "./retrained_models",
) -> Optional[IncrementalTrainer]:
    """
    Create an IncrementalTrainer for a specific model type.

    Args:
        model_type: Type of model (sms, phishing, voice)
        model_paths: Dictionary mapping model types to paths
        output_dir: Output directory for retrained models

    Returns:
        IncrementalTrainer instance or None if model not found
    """
    model_path = model_paths.get(model_type)
    if not model_path or not os.path.exists(model_path):
        logger.warning(f"Model not found for type: {model_type}")
        return None

    return IncrementalTrainer(
        model_path=model_path,
        model_type=model_type,
        output_dir=output_dir,
    )
