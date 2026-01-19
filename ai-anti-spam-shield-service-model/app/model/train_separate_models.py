"""
Separate Model Training Pipeline for AI Anti-Spam Shield
Trains specialized models for SMS spam, voice scam, and phishing detection

Usage:
    python train_separate_models.py --model sms                    # Train SMS model only
    python train_separate_models.py --model voice                  # Train voice model only
    python train_separate_models.py --model phishing               # Train phishing model only
    python train_separate_models.py --all                          # Train all models
    python train_separate_models.py --model sms --compare          # Compare algorithms for SMS
    python train_separate_models.py --all --compare                # Train all with comparison
    python train_separate_models.py --model sms --extended         # Use extended datasets
    python train_separate_models.py --model phishing --extended    # Use larger phishing datasets

Datasets (HuggingFace):
    SMS (Default): Deysi/spam-detection-dataset (10,900 samples)
    SMS (Extended): + mshenoda/spam-messages (59,241 samples)

    Voice: BothBosu/scam-dialogue (1,600 samples)

    Phishing (Default): shawhin/phishing-site-classification (2,100 samples)
    Phishing (Extended): + zefang-liu/phishing-email-dataset (18,650 samples)
                         + pirocheto/phishing-url (URL phishing)
"""

import os
import sys
import json
import argparse
import warnings
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score
)
import joblib
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# Suppress warnings
warnings.filterwarnings('ignore')

# Download NLTK data
try:
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
except:
    pass

# Try to import XGBoost
try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("Warning: XGBoost not installed, using Random Forest as fallback")

# Try to import feature extractors for phishing
try:
    from feature_extractors import URLFeatureExtractor, TextFeatureExtractor, CombinedFeatureExtractor
    HAS_FEATURE_EXTRACTORS = True
except ImportError:
    HAS_FEATURE_EXTRACTORS = False
    print("Warning: Feature extractors not available, phishing model will use TF-IDF only")


@dataclass
class ModelConfig:
    """Configuration for a specific model type"""
    name: str
    dataset_name: str
    dataset_variant: Optional[str]
    text_column: str
    label_column: str
    label_mapping: Optional[Dict[str, int]]
    model_file: str
    vectorizer_file: str
    tfidf_max_features: int
    tfidf_ngram_range: Tuple[int, int]
    use_custom_features: bool = False
    description: str = ""


# Model configurations
SMS_CONFIG = ModelConfig(
    name="sms",
    dataset_name="Deysi/spam-detection-dataset",
    dataset_variant=None,
    text_column="text",
    label_column="label",
    label_mapping={"spam": 1, "not_spam": 0},
    model_file="sms_classifier.pkl",
    vectorizer_file="sms_vectorizer.pkl",
    tfidf_max_features=3000,
    tfidf_ngram_range=(1, 2),
    description="SMS Spam Detection Model"
)

VOICE_CONFIG = ModelConfig(
    name="voice",
    dataset_name="BothBosu/scam-dialogue",
    dataset_variant=None,
    text_column="dialogue",
    label_column="label",
    label_mapping=None,  # Already binary
    model_file="voice_classifier.pkl",
    vectorizer_file="voice_vectorizer.pkl",
    tfidf_max_features=5000,
    tfidf_ngram_range=(1, 3),  # Higher n-grams for dialogues
    description="Voice Call Scam Detection Model"
)

PHISHING_CONFIG = ModelConfig(
    name="phishing",
    dataset_name="ealvaradob/phishing-dataset",
    dataset_variant="combined_reduced",
    text_column="text",
    label_column="label",
    label_mapping=None,  # Already binary
    model_file="phishing_classifier.pkl",
    vectorizer_file="phishing_vectorizer.pkl",
    tfidf_max_features=5000,
    tfidf_ngram_range=(1, 2),
    use_custom_features=True,
    description="Phishing Detection Model (URLs, Emails, SMS)"
)

CONFIGS = {
    "sms": SMS_CONFIG,
    "voice": VOICE_CONFIG,
    "phishing": PHISHING_CONFIG
}


class TextPreprocessor:
    """Text preprocessing utilities"""

    def __init__(self):
        self.stemmer = PorterStemmer()
        try:
            self.stop_words = set(stopwords.words('english'))
        except:
            self.stop_words = set()

    def preprocess(self, text: str, preserve_urls: bool = False) -> str:
        """Clean and preprocess text"""
        if not isinstance(text, str):
            text = str(text)

        # Convert to lowercase
        text = text.lower()

        if not preserve_urls:
            # Remove URLs
            text = re.sub(r'http\S+|www\S+|https\S+', ' url ', text, flags=re.MULTILINE)

        # Remove email addresses
        text = re.sub(r'\S+@\S+', ' email ', text)

        # Remove phone numbers
        text = re.sub(r'\b\d{10,}\b', ' phone ', text)

        # Remove special characters but keep spaces
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)

        # Remove extra whitespace
        text = ' '.join(text.split())

        # Remove stopwords and apply stemming
        if self.stop_words:
            words = text.split()
            words = [self.stemmer.stem(word) for word in words if word not in self.stop_words and len(word) > 1]
            text = ' '.join(words)

        return text

    def preprocess_dialogue(self, text: str) -> str:
        """Special preprocessing for dialogue format"""
        if not isinstance(text, str):
            text = str(text)

        # Remove caller/receiver markers
        text = re.sub(r'(caller|receiver|agent|customer|scammer|victim):', '', text, flags=re.IGNORECASE)

        # Standard preprocessing
        return self.preprocess(text)


class DataLoader:
    """Load datasets from HuggingFace"""

    @staticmethod
    def load_sms_dataset() -> pd.DataFrame:
        """Load SMS spam detection dataset"""
        from datasets import load_dataset

        print("Loading SMS spam dataset from HuggingFace: Deysi/spam-detection-dataset")
        dataset = load_dataset("Deysi/spam-detection-dataset")

        # Combine train and test
        train_df = dataset['train'].to_pandas()
        test_df = dataset['test'].to_pandas()
        df = pd.concat([train_df, test_df], ignore_index=True)

        # Convert labels
        df['label'] = df['label'].apply(lambda x: 1 if x == 'spam' else 0)

        # Drop split column if exists
        if 'split' in df.columns:
            df = df.drop(columns=['split'])

        print(f"  Loaded {len(df)} samples (Spam: {df['label'].sum()}, Ham: {len(df) - df['label'].sum()})")
        return df[['text', 'label']]

    @staticmethod
    def load_voice_dataset() -> pd.DataFrame:
        """Load voice scam dialogue dataset"""
        from datasets import load_dataset

        print("Loading voice scam dataset from HuggingFace: BothBosu/scam-dialogue")
        dataset = load_dataset("BothBosu/scam-dialogue")

        # Combine train and test
        train_df = dataset['train'].to_pandas()
        test_df = dataset['test'].to_pandas()
        df = pd.concat([train_df, test_df], ignore_index=True)

        # Rename dialogue to text for consistency
        df = df.rename(columns={'dialogue': 'text'})

        print(f"  Loaded {len(df)} samples (Scam: {df['label'].sum()}, Legitimate: {len(df) - df['label'].sum()})")
        return df[['text', 'label']]

    @staticmethod
    def load_phishing_dataset() -> pd.DataFrame:
        """Load phishing dataset (combined_reduced variant)"""
        from datasets import load_dataset

        print("Loading phishing dataset from HuggingFace: ealvaradob/phishing-dataset")

        # Try different loading methods
        try:
            # Method 1: Try loading without variant (default split)
            dataset = load_dataset("ealvaradob/phishing-dataset", split="train")
            df = dataset.to_pandas()
        except Exception as e1:
            print(f"  Method 1 failed: {e1}")
            try:
                # Method 2: Try loading with data_files pattern
                dataset = load_dataset("ealvaradob/phishing-dataset", data_files="*.parquet", split="train")
                df = dataset.to_pandas()
            except Exception as e2:
                print(f"  Method 2 failed: {e2}")
                # Method 3: Use alternative phishing dataset
                print("  Trying alternative dataset: shawhin/phishing-site-classification")
                try:
                    dataset = load_dataset("shawhin/phishing-site-classification", split="train")
                    df = dataset.to_pandas()
                    # Rename columns if needed
                    if 'url' in df.columns and 'text' not in df.columns:
                        df = df.rename(columns={'url': 'text'})
                    if 'status' in df.columns and 'label' not in df.columns:
                        df['label'] = df['status'].apply(lambda x: 1 if x == 'phishing' else 0)
                except Exception as e3:
                    print(f"  Method 3 failed: {e3}")
                    # Method 4: Use talby/phishing-emails dataset as fallback
                    print("  Trying fallback dataset: talby/phishing-emails")
                    dataset = load_dataset("talby/phishing-emails")
                    train_df = dataset['train'].to_pandas()
                    if 'test' in dataset:
                        test_df = dataset['test'].to_pandas()
                        df = pd.concat([train_df, test_df], ignore_index=True)
                    else:
                        df = train_df
                    # Adjust column names
                    if 'Email Text' in df.columns:
                        df = df.rename(columns={'Email Text': 'text', 'Email Type': 'label'})
                    if df['label'].dtype == object:
                        df['label'] = df['label'].apply(lambda x: 1 if 'phish' in str(x).lower() else 0)

        # Ensure we have text and label columns
        if 'text' not in df.columns:
            # Find the text column
            text_cols = [c for c in df.columns if 'text' in c.lower() or 'content' in c.lower() or 'body' in c.lower()]
            if text_cols:
                df = df.rename(columns={text_cols[0]: 'text'})
            elif 'url' in df.columns:
                df = df.rename(columns={'url': 'text'})

        # Handle 'labels' column (shawhin/phishing-site-classification uses 'labels')
        if 'labels' in df.columns and 'label' not in df.columns:
            df = df.rename(columns={'labels': 'label'})

        # Clean up
        df = df[['text', 'label']].dropna()
        df['label'] = df['label'].astype(int)

        print(f"  Loaded {len(df)} samples (Phishing: {df['label'].sum()}, Legitimate: {len(df) - df['label'].sum()})")
        return df

    @staticmethod
    def load_extended_sms_dataset() -> pd.DataFrame:
        """Load combined SMS spam datasets for better coverage

        Combines:
        - Deysi/spam-detection-dataset (10,900 samples)
        - mshenoda/spam-messages (59,241 samples)

        Expected: ~65,000+ unique samples
        """
        from datasets import load_dataset

        all_dfs = []

        # 1. Load original dataset
        print("Loading SMS dataset 1/2: Deysi/spam-detection-dataset")
        try:
            dataset = load_dataset("Deysi/spam-detection-dataset")
            train_df = dataset['train'].to_pandas()
            test_df = dataset['test'].to_pandas()
            df1 = pd.concat([train_df, test_df], ignore_index=True)
            df1['label'] = df1['label'].apply(lambda x: 1 if x == 'spam' else 0)
            if 'split' in df1.columns:
                df1 = df1.drop(columns=['split'])
            df1 = df1[['text', 'label']]
            print(f"  Loaded {len(df1)} samples")
            all_dfs.append(df1)
        except Exception as e:
            print(f"  Failed to load Deysi dataset: {e}")

        # 2. Load mshenoda/spam-messages (larger dataset)
        print("Loading SMS dataset 2/2: mshenoda/spam-messages")
        try:
            dataset = load_dataset("mshenoda/spam-messages")
            # This dataset may have different splits
            if 'train' in dataset:
                df2 = dataset['train'].to_pandas()
            else:
                df2 = dataset[list(dataset.keys())[0]].to_pandas()

            # Find text column
            text_col = None
            for col in ['text', 'message', 'sms', 'content']:
                if col in df2.columns:
                    text_col = col
                    break
            if text_col and text_col != 'text':
                df2 = df2.rename(columns={text_col: 'text'})

            # Find label column
            label_col = None
            for col in ['label', 'spam', 'is_spam', 'class']:
                if col in df2.columns:
                    label_col = col
                    break
            if label_col and label_col != 'label':
                df2 = df2.rename(columns={label_col: 'label'})

            # Convert label to binary if needed
            if df2['label'].dtype == object:
                df2['label'] = df2['label'].apply(lambda x: 1 if str(x).lower() in ['spam', '1', 'true'] else 0)

            df2 = df2[['text', 'label']]
            print(f"  Loaded {len(df2)} samples")
            all_dfs.append(df2)
        except Exception as e:
            print(f"  Failed to load mshenoda dataset: {e}")

        # Combine all datasets
        if not all_dfs:
            raise ValueError("Failed to load any SMS datasets")

        combined_df = pd.concat(all_dfs, ignore_index=True)

        # Remove duplicates based on text
        original_len = len(combined_df)
        combined_df = combined_df.drop_duplicates(subset=['text'], keep='first')
        print(f"\nCombined SMS dataset: {len(combined_df)} unique samples (removed {original_len - len(combined_df)} duplicates)")
        print(f"  Spam: {combined_df['label'].sum()}, Ham: {len(combined_df) - combined_df['label'].sum()}")

        return combined_df

    @staticmethod
    def load_extended_phishing_dataset() -> pd.DataFrame:
        """Load combined phishing datasets for improved accuracy

        Combines:
        - zefang-liu/phishing-email-dataset (18,650 email samples)
        - pirocheto/phishing-url (~11K URL samples with train+test)
        - shawhin/phishing-site-classification (2,100 URL samples)

        Expected: ~30,000+ samples
        """
        from datasets import load_dataset

        all_dfs = []

        # 1. Load zefang-liu/phishing-email-dataset (EMAILS - best for text classification)
        print("Loading phishing dataset 1/3: zefang-liu/phishing-email-dataset")
        try:
            dataset = load_dataset("zefang-liu/phishing-email-dataset")
            df1 = dataset['train'].to_pandas()

            # This dataset uses 'Email Text' and 'Email Type' columns
            if 'Email Text' in df1.columns:
                df1 = df1.rename(columns={'Email Text': 'text'})
            if 'Email Type' in df1.columns:
                df1 = df1.rename(columns={'Email Type': 'label'})

            # Convert label: 'Phishing Email' -> 1, 'Safe Email' -> 0
            if df1['label'].dtype == object:
                df1['label'] = df1['label'].apply(lambda x: 1 if 'phish' in str(x).lower() else 0)

            df1 = df1[['text', 'label']].dropna()
            df1['label'] = df1['label'].astype(int)
            print(f"  Loaded {len(df1)} email samples (Phishing: {df1['label'].sum()}, Safe: {len(df1) - df1['label'].sum()})")
            all_dfs.append(df1)
        except Exception as e:
            print(f"  Failed to load zefang-liu dataset: {e}")

        # 2. Load pirocheto/phishing-url (URLs with extracted features)
        print("Loading phishing dataset 2/3: pirocheto/phishing-url")
        try:
            dataset = load_dataset("pirocheto/phishing-url")
            # Combine train and test splits
            train_df = dataset['train'].to_pandas()
            test_df = dataset['test'].to_pandas()
            df2 = pd.concat([train_df, test_df], ignore_index=True)

            # Use URL as text
            if 'url' in df2.columns:
                df2 = df2.rename(columns={'url': 'text'})

            # Status column: 'phishing' or 'legitimate'
            if 'status' in df2.columns:
                df2['label'] = df2['status'].apply(lambda x: 1 if x == 'phishing' else 0)

            df2 = df2[['text', 'label']].dropna()
            df2['label'] = df2['label'].astype(int)
            print(f"  Loaded {len(df2)} URL samples (Phishing: {df2['label'].sum()}, Legitimate: {len(df2) - df2['label'].sum()})")
            all_dfs.append(df2)
        except Exception as e:
            print(f"  Failed to load pirocheto dataset: {e}")

        # 3. Load shawhin/phishing-site-classification as additional data
        print("Loading phishing dataset 3/3: shawhin/phishing-site-classification")
        try:
            dataset = load_dataset("shawhin/phishing-site-classification", split="train")
            df3 = dataset.to_pandas()

            if 'url' in df3.columns and 'text' not in df3.columns:
                df3 = df3.rename(columns={'url': 'text'})
            if 'labels' in df3.columns and 'label' not in df3.columns:
                df3 = df3.rename(columns={'labels': 'label'})

            df3 = df3[['text', 'label']].dropna()
            df3['label'] = df3['label'].astype(int)
            print(f"  Loaded {len(df3)} URL samples (Phishing: {df3['label'].sum()}, Legitimate: {len(df3) - df3['label'].sum()})")
            all_dfs.append(df3)
        except Exception as e:
            print(f"  Failed to load shawhin dataset: {e}")

        # Combine all datasets
        if not all_dfs:
            raise ValueError("Failed to load any phishing datasets")

        combined_df = pd.concat(all_dfs, ignore_index=True)

        # Remove duplicates
        original_len = len(combined_df)
        combined_df = combined_df.drop_duplicates(subset=['text'], keep='first')
        print(f"\nCombined phishing dataset: {len(combined_df)} unique samples (removed {original_len - len(combined_df)} duplicates)")
        print(f"  Phishing: {combined_df['label'].sum()}, Legitimate: {len(combined_df) - combined_df['label'].sum()}")

        return combined_df


class ModelTrainer:
    """Train and evaluate models"""

    ALGORITHMS = {
        'naive_bayes': lambda: MultinomialNB(),
        'logistic_regression': lambda: LogisticRegression(max_iter=1000, random_state=42, n_jobs=-1),
        'random_forest': lambda: RandomForestClassifier(n_estimators=100, max_depth=20, random_state=42, n_jobs=-1),
    }

    def __init__(self, config: ModelConfig, output_dir: str = "trained_models"):
        self.config = config
        self.output_dir = Path(output_dir) / config.name
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.preprocessor = TextPreprocessor()
        self.vectorizer = None
        self.model = None
        self.feature_extractor = None

        # Initialize feature extractor for phishing
        if config.use_custom_features and HAS_FEATURE_EXTRACTORS:
            self.feature_extractor = CombinedFeatureExtractor()

    def _create_vectorizer(self) -> TfidfVectorizer:
        """Create TF-IDF vectorizer based on config"""
        return TfidfVectorizer(
            max_features=self.config.tfidf_max_features,
            ngram_range=self.config.tfidf_ngram_range,
            min_df=2,
            max_df=0.85,
            strip_accents='unicode',
            lowercase=True
        )

    def _create_model(self, algorithm: str):
        """Create model based on algorithm name"""
        if algorithm == 'xgboost':
            if HAS_XGBOOST:
                return XGBClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42,
                    n_jobs=-1,
                    use_label_encoder=False,
                    eval_metric='logloss'
                )
            else:
                print("  XGBoost not available, using Random Forest")
                algorithm = 'random_forest'

        if algorithm not in self.ALGORITHMS:
            raise ValueError(f"Unknown algorithm: {algorithm}. Choose from {list(self.ALGORITHMS.keys())}")

        return self.ALGORITHMS[algorithm]()

    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess text data"""
        print("  Preprocessing text...")

        if self.config.name == 'voice':
            df['processed_text'] = df['text'].apply(self.preprocessor.preprocess_dialogue)
        elif self.config.name == 'phishing':
            # For phishing, preserve URLs for feature extraction
            df['processed_text'] = df['text'].apply(lambda x: self.preprocessor.preprocess(x, preserve_urls=False))
        else:
            df['processed_text'] = df['text'].apply(self.preprocessor.preprocess)

        return df

    def _extract_features(self, texts: List[str], fit: bool = False) -> np.ndarray:
        """Extract features from texts"""
        # TF-IDF features
        if fit:
            self.vectorizer = self._create_vectorizer()
            tfidf_features = self.vectorizer.fit_transform(texts).toarray()
        else:
            tfidf_features = self.vectorizer.transform(texts).toarray()

        # Add custom features for phishing
        if self.config.use_custom_features and self.feature_extractor:
            print("  Extracting custom features...")
            custom_features = []
            for text in texts:
                features = self.feature_extractor.extract(text)
                custom_features.append(list(features.values()))
            custom_array = np.array(custom_features)

            # Combine TF-IDF and custom features
            return np.hstack([tfidf_features, custom_array])

        return tfidf_features

    def train(self, df: pd.DataFrame, algorithm: str = 'logistic_regression') -> Dict:
        """Train model on dataset"""
        print(f"\n{'='*60}")
        print(f"Training {self.config.description}")
        print(f"Algorithm: {algorithm}")
        print(f"{'='*60}")

        # Preprocess
        df = self._preprocess_data(df)

        # Split data
        print("  Splitting data (80% train, 20% test)...")
        X_train, X_test, y_train, y_test = train_test_split(
            df['processed_text'].tolist(),
            df['label'].tolist(),
            test_size=0.2,
            random_state=42,
            stratify=df['label']
        )

        # Extract features
        print("  Extracting features...")
        X_train_features = self._extract_features(X_train, fit=True)
        X_test_features = self._extract_features(X_test, fit=False)
        print(f"  Feature dimensions: {X_train_features.shape[1]}")

        # Train model
        print(f"  Training {algorithm} model...")
        self.model = self._create_model(algorithm)

        start_time = datetime.now()
        self.model.fit(X_train_features, y_train)
        train_time = (datetime.now() - start_time).total_seconds()

        # Evaluate
        print("  Evaluating model...")
        y_pred = self.model.predict(X_test_features)
        y_prob = self.model.predict_proba(X_test_features)[:, 1]

        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1': f1_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_prob),
            'train_time_seconds': train_time,
            'train_samples': len(y_train),
            'test_samples': len(y_test),
            'feature_count': X_train_features.shape[1]
        }

        # Print results
        print(f"\n  Results:")
        print(f"    Accuracy:  {metrics['accuracy']:.4f}")
        print(f"    Precision: {metrics['precision']:.4f}")
        print(f"    Recall:    {metrics['recall']:.4f}")
        print(f"    F1 Score:  {metrics['f1']:.4f}")
        print(f"    ROC AUC:   {metrics['roc_auc']:.4f}")
        print(f"    Train Time: {train_time:.2f}s")

        # Classification report
        print(f"\n  Classification Report:")
        target_names = ['Legitimate', 'Spam/Scam/Phishing']
        print(classification_report(y_test, y_pred, target_names=target_names))

        return metrics

    def compare_algorithms(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compare multiple algorithms"""
        print(f"\n{'='*60}")
        print(f"Comparing Algorithms for {self.config.description}")
        print(f"{'='*60}")

        algorithms = ['naive_bayes', 'logistic_regression', 'random_forest']
        if HAS_XGBOOST:
            algorithms.append('xgboost')

        results = []
        best_f1 = 0
        best_algo = None

        for algo in algorithms:
            print(f"\n--- {algo.upper()} ---")
            metrics = self.train(df.copy(), algorithm=algo)
            metrics['algorithm'] = algo
            results.append(metrics)

            if metrics['f1'] > best_f1:
                best_f1 = metrics['f1']
                best_algo = algo

        # Create comparison DataFrame
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('f1', ascending=False)

        print(f"\n{'='*60}")
        print("Algorithm Comparison Summary")
        print(f"{'='*60}")
        print(results_df[['algorithm', 'accuracy', 'precision', 'recall', 'f1', 'roc_auc', 'train_time_seconds']].to_string(index=False))
        print(f"\nBest Algorithm: {best_algo} (F1: {best_f1:.4f})")

        return results_df

    def save(self, algorithm: str, metrics: Dict):
        """Save trained model and metadata"""
        print(f"\n  Saving model to {self.output_dir}/")

        # Save model
        model_path = self.output_dir / self.config.model_file
        joblib.dump(self.model, model_path)

        # Save vectorizer
        vectorizer_path = self.output_dir / self.config.vectorizer_file
        joblib.dump(self.vectorizer, vectorizer_path)

        # Save feature extractor info if used
        if self.config.use_custom_features and self.feature_extractor:
            features_path = self.output_dir / "custom_features.json"
            with open(features_path, 'w') as f:
                json.dump({
                    'feature_names': self.feature_extractor.get_feature_names(),
                    'enabled': True
                }, f, indent=2)

        # Save metadata
        metadata = {
            'model_type': self.config.name,
            'description': self.config.description,
            'version': '1.0.0',
            'trained_at': datetime.now().isoformat(),
            'dataset': self.config.dataset_name,
            'dataset_variant': self.config.dataset_variant,
            'algorithm': algorithm,
            'metrics': metrics,
            'preprocessing': {
                'lowercase': True,
                'remove_urls': True,
                'remove_emails': True,
                'stemming': True,
                'stopwords': 'english'
            },
            'vectorizer': {
                'type': 'TfidfVectorizer',
                'max_features': self.config.tfidf_max_features,
                'ngram_range': list(self.config.tfidf_ngram_range)
            },
            'use_custom_features': self.config.use_custom_features,
            'files': {
                'model': self.config.model_file,
                'vectorizer': self.config.vectorizer_file
            }
        }

        metadata_path = self.output_dir / f"{self.config.name}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)

        print(f"    Model: {model_path}")
        print(f"    Vectorizer: {vectorizer_path}")
        print(f"    Metadata: {metadata_path}")


def train_model(model_type: str, algorithm: str = None, compare: bool = False, output_dir: str = "trained_models", extended: bool = False):
    """Train a specific model type

    Args:
        model_type: Type of model ('sms', 'voice', 'phishing')
        algorithm: Algorithm to use (default depends on model type)
        compare: Whether to compare multiple algorithms
        output_dir: Directory for saved models
        extended: Use extended datasets (larger, combined datasets)
    """
    if model_type not in CONFIGS:
        raise ValueError(f"Unknown model type: {model_type}. Choose from {list(CONFIGS.keys())}")

    config = CONFIGS[model_type]

    # Load data
    if extended:
        print(f"\nLoading EXTENDED {model_type} dataset...")
    else:
        print(f"\nLoading {model_type} dataset...")

    if model_type == 'sms':
        if extended:
            df = DataLoader.load_extended_sms_dataset()
        else:
            df = DataLoader.load_sms_dataset()
    elif model_type == 'voice':
        df = DataLoader.load_voice_dataset()  # No extended version for voice
        if extended:
            print("  Note: No extended dataset available for voice model")
    elif model_type == 'phishing':
        if extended:
            df = DataLoader.load_extended_phishing_dataset()
        else:
            df = DataLoader.load_phishing_dataset()

    # Create trainer
    trainer = ModelTrainer(config, output_dir)

    if compare:
        # Compare algorithms
        results_df = trainer.compare_algorithms(df)

        # Save comparison results
        results_path = Path(output_dir) / config.name / "algorithm_comparison.csv"
        results_df.to_csv(results_path, index=False)
        print(f"\nComparison results saved to: {results_path}")

        # Train with best algorithm
        best_algo = results_df.iloc[0]['algorithm']
        print(f"\nRetraining with best algorithm: {best_algo}")
        metrics = trainer.train(df.copy(), algorithm=best_algo)
        trainer.save(best_algo, metrics)
    else:
        # Use specified or default algorithm
        if algorithm is None:
            # Default algorithms per model type
            defaults = {
                'sms': 'logistic_regression',
                'voice': 'random_forest',
                'phishing': 'xgboost' if HAS_XGBOOST else 'random_forest'
            }
            algorithm = defaults[model_type]

        metrics = trainer.train(df, algorithm=algorithm)
        trainer.save(algorithm, metrics)

    return trainer


def train_all(compare: bool = False, output_dir: str = "trained_models", extended: bool = False):
    """Train all models

    Args:
        compare: Whether to compare multiple algorithms
        output_dir: Directory for saved models
        extended: Use extended datasets (larger, combined datasets)
    """
    print("\n" + "="*60)
    if extended:
        print("TRAINING ALL MODELS (EXTENDED DATASETS)")
    else:
        print("TRAINING ALL MODELS")
    print("="*60)

    results = {}

    for model_type in ['sms', 'voice', 'phishing']:
        try:
            trainer = train_model(model_type, compare=compare, output_dir=output_dir, extended=extended)
            results[model_type] = "Success"
        except Exception as e:
            print(f"\nError training {model_type}: {e}")
            results[model_type] = f"Failed: {e}"

    # Summary
    print("\n" + "="*60)
    print("TRAINING SUMMARY")
    print("="*60)
    for model_type, status in results.items():
        print(f"  {model_type}: {status}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Train separate ML models for SMS spam, voice scam, and phishing detection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python train_separate_models.py --model sms                    # Train SMS model
  python train_separate_models.py --model voice --algorithm random_forest
  python train_separate_models.py --model phishing --compare     # Compare algorithms
  python train_separate_models.py --all                          # Train all models
  python train_separate_models.py --all --compare                # Train all with comparison
  python train_separate_models.py --model phishing --extended    # Train with extended datasets
  python train_separate_models.py --all --extended --compare     # Full training with extended data

Extended Datasets:
  SMS:      Deysi/spam-detection-dataset + mshenoda/spam-messages (~65K samples)
  Phishing: zefang-liu/phishing-email-dataset + pirocheto/phishing-url + shawhin (~50K samples)
        """
    )

    parser.add_argument(
        '--model', '-m',
        choices=['sms', 'voice', 'phishing'],
        help='Model type to train'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Train all models'
    )
    parser.add_argument(
        '--algorithm', '-alg',
        choices=['naive_bayes', 'logistic_regression', 'random_forest', 'xgboost'],
        help='Algorithm to use (default depends on model type)'
    )
    parser.add_argument(
        '--compare', '-c',
        action='store_true',
        help='Compare multiple algorithms and select best'
    )
    parser.add_argument(
        '--extended', '-e',
        action='store_true',
        help='Use extended datasets (larger, combined datasets for better accuracy)'
    )
    parser.add_argument(
        '--output', '-o',
        default='trained_models',
        help='Output directory for trained models (default: trained_models)'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.model and not args.all:
        parser.print_help()
        print("\nError: Please specify --model or --all")
        sys.exit(1)

    # Run training
    if args.all:
        train_all(compare=args.compare, output_dir=args.output, extended=args.extended)
    else:
        train_model(
            model_type=args.model,
            algorithm=args.algorithm,
            compare=args.compare,
            output_dir=args.output,
            extended=args.extended
        )

    print("\n" + "="*60)
    print("Training complete!")
    print("="*60)


if __name__ == '__main__':
    main()
