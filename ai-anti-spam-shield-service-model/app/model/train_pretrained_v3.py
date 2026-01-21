"""
Fine-tuning Script for Pre-trained HuggingFace Models (V3)

This script downloads pre-trained spam/phishing detection models from HuggingFace
and fine-tunes them on extended datasets for maximum accuracy.

Models:
- SMS: mrm8488/bert-tiny-finetuned-sms-spam-detection
- Phishing: cybersectony/phishing-email-detection-distilbert_v2.4.1

Extended Datasets:
- SMS: Deysi/spam-detection-dataset + mshenoda/spam-messages (~65K samples)
- Phishing: zefang-liu/phishing-email-dataset + pirocheto/phishing-url (~30K samples)
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict

import torch
import numpy as np
from datasets import load_dataset, concatenate_datasets, Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding,
    EarlyStoppingCallback,
    pipeline
)
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model configurations
PRETRAINED_MODELS = {
    'sms': {
        'model_name': 'mrm8488/bert-tiny-finetuned-sms-spam-detection',
        'backup_model': 'distilbert-base-uncased',
        'num_labels': 2,
        'max_length': 128,
    },
    'phishing': {
        'model_name': 'cybersectony/phishing-email-detection-distilbert_v2.4.1',
        'backup_model': 'ealvaradob/bert-finetuned-phishing',
        'num_labels': 2,
        'max_length': 256,
    },
    'voice': {
        'model_name': 'mrm8488/bert-tiny-finetuned-sms-spam-detection',  # Transfer from SMS
        'backup_model': 'distilbert-base-uncased',
        'num_labels': 2,
        'max_length': 256,
    }
}

# Dataset configurations
DATASET_CONFIGS = {
    'sms': [
        {'name': 'Deysi/spam-detection-dataset', 'text_col': 'text', 'label_col': 'label'},
        {'name': 'mshenoda/spam-messages', 'text_col': 'text', 'label_col': 'label'},
    ],
    'phishing': [
        {'name': 'zefang-liu/phishing-email-dataset', 'text_col': 'text', 'label_col': 'label'},
        {'name': 'ealvaradob/phishing-dataset', 'subset': 'combined_reduced', 'text_col': 'text', 'label_col': 'label'},
    ],
    'voice': [
        {'name': 'BothBosu/scam-dialogue', 'text_col': 'dialogue', 'label_col': 'label'},
    ]
}


@dataclass
class TrainingMetrics:
    """Training metrics storage"""
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    train_samples: int
    eval_samples: int
    test_samples: int
    training_time_seconds: float
    model_name: str
    model_type: str

    def to_dict(self) -> Dict:
        return asdict(self)


class PretrainedModelTrainer:
    """
    Fine-tunes pre-trained HuggingFace models on extended datasets
    for maximum spam/phishing detection accuracy.
    """

    def __init__(
        self,
        model_type: str,
        output_dir: str = "./trained_models_v3",
        use_gpu: bool = True,
        force_retrain: bool = False
    ):
        self.model_type = model_type
        self.output_dir = Path(output_dir) / model_type
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.config = PRETRAINED_MODELS.get(model_type)
        if not self.config:
            raise ValueError(f"Unknown model type: {model_type}. Choose from: {list(PRETRAINED_MODELS.keys())}")

        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        self.force_retrain = force_retrain

        logger.info(f"Initializing trainer for {model_type} on {self.device}")

        # Initialize model and tokenizer
        self.tokenizer = None
        self.model = None

    def load_pretrained_model(self) -> Tuple[AutoTokenizer, AutoModelForSequenceClassification]:
        """Load pre-trained model from HuggingFace"""
        model_name = self.config['model_name']

        try:
            logger.info(f"Loading pre-trained model: {model_name}")
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=self.config['num_labels']
            )
            logger.info(f"Successfully loaded {model_name}")

        except Exception as e:
            logger.warning(f"Failed to load {model_name}: {e}")
            logger.info(f"Falling back to: {self.config['backup_model']}")

            tokenizer = AutoTokenizer.from_pretrained(self.config['backup_model'])
            model = AutoModelForSequenceClassification.from_pretrained(
                self.config['backup_model'],
                num_labels=self.config['num_labels']
            )

        self.tokenizer = tokenizer
        self.model = model
        return tokenizer, model

    def load_datasets(self) -> Tuple[Dataset, Dataset, Dataset]:
        """Load and combine extended datasets"""
        datasets_config = DATASET_CONFIGS.get(self.model_type, [])
        all_texts = []
        all_labels = []

        for ds_config in datasets_config:
            try:
                logger.info(f"Loading dataset: {ds_config['name']}")

                if 'subset' in ds_config:
                    ds = load_dataset(ds_config['name'], ds_config['subset'], split='train')
                else:
                    ds = load_dataset(ds_config['name'], split='train')

                text_col = ds_config['text_col']
                label_col = ds_config['label_col']

                # Handle different label formats
                for item in ds:
                    text = item.get(text_col, '')
                    if not text or len(str(text).strip()) < 5:
                        continue

                    label = item.get(label_col)

                    # Normalize label to 0/1
                    if isinstance(label, str):
                        label = 1 if label.lower() in ['spam', 'phishing', '1', 'scam', 'yes', 'true'] else 0
                    elif isinstance(label, bool):
                        label = 1 if label else 0
                    else:
                        label = int(label) if label else 0

                    all_texts.append(str(text).strip())
                    all_labels.append(label)

                logger.info(f"Loaded {len(ds)} samples from {ds_config['name']}")

            except Exception as e:
                logger.warning(f"Failed to load {ds_config['name']}: {e}")
                continue

        if not all_texts:
            raise ValueError(f"No data loaded for {self.model_type}")

        # Remove duplicates
        seen = set()
        unique_texts = []
        unique_labels = []
        for text, label in zip(all_texts, all_labels):
            text_hash = hash(text.lower()[:100])
            if text_hash not in seen:
                seen.add(text_hash)
                unique_texts.append(text)
                unique_labels.append(label)

        logger.info(f"Total unique samples: {len(unique_texts)}")
        logger.info(f"Label distribution: spam={sum(unique_labels)}, ham={len(unique_labels)-sum(unique_labels)}")

        # Split into train/val/test (60/20/20)
        train_texts, temp_texts, train_labels, temp_labels = train_test_split(
            unique_texts, unique_labels, test_size=0.4, random_state=42, stratify=unique_labels
        )
        val_texts, test_texts, val_labels, test_labels = train_test_split(
            temp_texts, temp_labels, test_size=0.5, random_state=42, stratify=temp_labels
        )

        # Create HuggingFace datasets
        train_dataset = Dataset.from_dict({'text': train_texts, 'label': train_labels})
        val_dataset = Dataset.from_dict({'text': val_texts, 'label': val_labels})
        test_dataset = Dataset.from_dict({'text': test_texts, 'label': test_labels})

        logger.info(f"Train: {len(train_dataset)}, Val: {len(val_dataset)}, Test: {len(test_dataset)}")

        return train_dataset, val_dataset, test_dataset

    def tokenize_dataset(self, dataset: Dataset) -> Dataset:
        """Tokenize a dataset"""
        def tokenize_fn(examples):
            return self.tokenizer(
                examples['text'],
                truncation=True,
                padding='max_length',
                max_length=self.config['max_length']
            )

        return dataset.map(tokenize_fn, batched=True, remove_columns=['text'])

    def compute_metrics(self, eval_pred) -> Dict:
        """Compute evaluation metrics"""
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)

        accuracy = accuracy_score(labels, predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(
            labels, predictions, average='binary', zero_division=0
        )

        try:
            # Get probabilities for ROC-AUC
            probs = torch.softmax(torch.tensor(eval_pred.predictions), dim=1)[:, 1].numpy()
            roc_auc = roc_auc_score(labels, probs)
        except:
            roc_auc = 0.0

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'roc_auc': roc_auc
        }

    def train(
        self,
        epochs: int = 3,
        batch_size: int = 16,
        learning_rate: float = 2e-5,
        warmup_ratio: float = 0.1,
        weight_decay: float = 0.01
    ) -> TrainingMetrics:
        """
        Fine-tune the pre-trained model on extended datasets
        """
        import time
        start_time = time.time()

        # Load model and datasets
        self.load_pretrained_model()
        train_dataset, val_dataset, test_dataset = self.load_datasets()

        # Tokenize datasets
        logger.info("Tokenizing datasets...")
        train_tokenized = self.tokenize_dataset(train_dataset)
        val_tokenized = self.tokenize_dataset(val_dataset)
        test_tokenized = self.tokenize_dataset(test_dataset)

        # Training arguments
        training_args = TrainingArguments(
            output_dir=str(self.output_dir / "checkpoints"),
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size * 2,
            learning_rate=learning_rate,
            warmup_ratio=warmup_ratio,
            weight_decay=weight_decay,
            evaluation_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="f1",
            greater_is_better=True,
            logging_dir=str(self.output_dir / "logs"),
            logging_steps=100,
            report_to="none",  # Disable wandb/mlflow
            fp16=self.device == "cuda",
            dataloader_num_workers=0,
            remove_unused_columns=False,
        )

        # Data collator
        data_collator = DataCollatorWithPadding(tokenizer=self.tokenizer)

        # Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_tokenized,
            eval_dataset=val_tokenized,
            tokenizer=self.tokenizer,
            data_collator=data_collator,
            compute_metrics=self.compute_metrics,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
        )

        # Train
        logger.info(f"Starting training for {epochs} epochs...")
        trainer.train()

        # Evaluate on test set
        logger.info("Evaluating on test set...")
        test_results = trainer.evaluate(test_tokenized)

        training_time = time.time() - start_time

        # Save model
        self.save_model(trainer)

        # Create metrics
        metrics = TrainingMetrics(
            accuracy=test_results.get('eval_accuracy', 0),
            precision=test_results.get('eval_precision', 0),
            recall=test_results.get('eval_recall', 0),
            f1=test_results.get('eval_f1', 0),
            roc_auc=test_results.get('eval_roc_auc', 0),
            train_samples=len(train_dataset),
            eval_samples=len(val_dataset),
            test_samples=len(test_dataset),
            training_time_seconds=training_time,
            model_name=self.config['model_name'],
            model_type=self.model_type
        )

        # Save metrics
        self.save_metrics(metrics)

        logger.info(f"Training completed in {training_time:.2f}s")
        logger.info(f"Test Accuracy: {metrics.accuracy:.4f}")
        logger.info(f"Test F1: {metrics.f1:.4f}")
        logger.info(f"Test Recall: {metrics.recall:.4f}")

        return metrics

    def save_model(self, trainer: Trainer):
        """Save the fine-tuned model"""
        model_path = self.output_dir / "model"
        model_path.mkdir(exist_ok=True)

        trainer.save_model(str(model_path))
        self.tokenizer.save_pretrained(str(model_path))

        logger.info(f"Model saved to {model_path}")

    def save_metrics(self, metrics: TrainingMetrics):
        """Save training metrics"""
        metrics_path = self.output_dir / "metrics.json"

        metrics_dict = metrics.to_dict()
        metrics_dict['trained_at'] = datetime.now().isoformat()
        metrics_dict['version'] = 'v3.0.0'

        with open(metrics_path, 'w') as f:
            json.dump(metrics_dict, f, indent=2)

        logger.info(f"Metrics saved to {metrics_path}")

    def evaluate_pretrained_only(self) -> Dict:
        """
        Evaluate the pre-trained model WITHOUT fine-tuning
        to establish a baseline
        """
        logger.info("Evaluating pre-trained model (no fine-tuning)...")

        self.load_pretrained_model()
        _, _, test_dataset = self.load_datasets()

        # Create pipeline for prediction
        classifier = pipeline(
            "text-classification",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if self.device == "cuda" else -1
        )

        # Predict on test set
        predictions = []
        labels = test_dataset['label']

        for text in test_dataset['text']:
            result = classifier(text[:512])[0]
            # Map label to 0/1
            pred_label = result['label'].lower()
            if pred_label in ['spam', 'phishing', '1', 'label_1']:
                predictions.append(1)
            else:
                predictions.append(0)

        # Calculate metrics
        accuracy = accuracy_score(labels, predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(
            labels, predictions, average='binary', zero_division=0
        )

        results = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'test_samples': len(test_dataset),
            'model_name': self.config['model_name'],
            'fine_tuned': False
        }

        logger.info(f"Pre-trained model baseline - Accuracy: {accuracy:.4f}, F1: {f1:.4f}")

        return results


def train_all_models(
    output_dir: str = "./trained_models_v3",
    epochs: int = 3,
    batch_size: int = 16
):
    """Train all model types"""
    results = {}

    for model_type in ['sms', 'phishing', 'voice']:
        logger.info(f"\n{'='*50}")
        logger.info(f"Training {model_type.upper()} model")
        logger.info(f"{'='*50}\n")

        try:
            trainer = PretrainedModelTrainer(
                model_type=model_type,
                output_dir=output_dir
            )

            # First evaluate baseline
            baseline = trainer.evaluate_pretrained_only()

            # Then fine-tune
            metrics = trainer.train(epochs=epochs, batch_size=batch_size)

            results[model_type] = {
                'baseline': baseline,
                'finetuned': metrics.to_dict()
            }

            logger.info(f"\n{model_type.upper()} Results:")
            logger.info(f"  Baseline F1: {baseline['f1']:.4f}")
            logger.info(f"  Fine-tuned F1: {metrics.f1:.4f}")
            logger.info(f"  Improvement: {(metrics.f1 - baseline['f1'])*100:.2f}%")

        except Exception as e:
            logger.error(f"Failed to train {model_type}: {e}")
            results[model_type] = {'error': str(e)}

    # Save overall results
    results_path = Path(output_dir) / "training_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"\nAll results saved to {results_path}")
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fine-tune pre-trained spam/phishing models")
    parser.add_argument("--model", type=str, choices=['sms', 'phishing', 'voice', 'all'],
                        default='all', help="Model type to train")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Training batch size")
    parser.add_argument("--output-dir", type=str, default="./trained_models_v3",
                        help="Output directory for trained models")
    parser.add_argument("--evaluate-only", action="store_true",
                        help="Only evaluate pre-trained models without fine-tuning")

    args = parser.parse_args()

    if args.model == 'all':
        train_all_models(
            output_dir=args.output_dir,
            epochs=args.epochs,
            batch_size=args.batch_size
        )
    else:
        trainer = PretrainedModelTrainer(
            model_type=args.model,
            output_dir=args.output_dir
        )

        if args.evaluate_only:
            results = trainer.evaluate_pretrained_only()
            print(json.dumps(results, indent=2))
        else:
            metrics = trainer.train(epochs=args.epochs, batch_size=args.batch_size)
            print(json.dumps(metrics.to_dict(), indent=2))
