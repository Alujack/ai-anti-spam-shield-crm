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
            dataset = load_dataset("ealvaradob/phishing-dataset", "combined_reduced")
        except Exception:
            # Fallback to local data or another source
            logger.warning("Could not load phishing dataset from HuggingFace")
            return self._create_synthetic_phishing_data()

        def preprocess(example):
            text = example.get("text", example.get("email", ""))
            label = example.get("label", 0)
            # Handle string labels
            if isinstance(label, str):
                label = 1 if label.lower() in ["phishing", "spam", "1"] else 0
            return {
                "text": self.clean_text(text),
                "label": int(label),
            }

        dataset = dataset.map(preprocess)

        # Split
        if "train" in dataset:
            train_data = dataset["train"]
        else:
            train_data = dataset

        train_val = train_data.train_test_split(test_size=0.2, seed=42)
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
            "Your Netflix subscription is expiring. Update payment: [URL]",
            "Bank security notification: Please verify your identity",
            "Amazon order confirmation - Track your package: [URL]",
            "Your Apple ID has been locked. Verify now: [URL]",
            "IRS refund notification: Claim your $500 tax refund now",
        ]

        safe_templates = [
            "Meeting scheduled for tomorrow at 3pm",
            "Thanks for your order. Shipping confirmation attached.",
            "Reminder: Doctor appointment on Friday",
            "Happy birthday! Hope you have a great day.",
            "Project update: All tasks completed on schedule",
            "Your monthly statement is ready to view",
            "Team lunch this Thursday at noon",
            "Conference call rescheduled to 2pm",
            "Weekly report attached for your review",
            "Looking forward to our meeting next week",
        ]

        data = {
            "text": phishing_templates * 100 + safe_templates * 100,
            "label": [1] * 1000 + [0] * 1000,
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
