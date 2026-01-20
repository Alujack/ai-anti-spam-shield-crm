import joblib
import os
import re
import json
import nltk
from pathlib import Path
from typing import Dict, Optional, Any
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import numpy as np

# Download NLTK data
try:
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
except:
    pass

# Try to import feature extractors for phishing
try:
    from .feature_extractors import CombinedFeatureExtractor
    HAS_FEATURE_EXTRACTORS = True
except ImportError:
    try:
        from feature_extractors import CombinedFeatureExtractor
        HAS_FEATURE_EXTRACTORS = True
    except ImportError:
        HAS_FEATURE_EXTRACTORS = False

class SpamPredictor:
    # Minimum confidence threshold to classify as spam
    # Messages below this threshold are considered "ham" even if model predicts spam
    # This reduces false positives for ambiguous messages
    # Increased from 0.75 to 0.80 to reduce false positives on friendly messages
    SPAM_CONFIDENCE_THRESHOLD = 0.80  # 80%

    # Common safe greeting patterns that should not be flagged as spam
    SAFE_GREETING_PATTERNS = [
        r'^hi+\s*$',
        r'^hello+\s*$',
        r'^hey+\s*$',
        r'^hi+\s+(there|friend|friends|everyone|all|guys?|buddy|mate)?\s*[!?.]*$',
        r'^hello+\s+(there|friend|friends|everyone|all|guys?|buddy|mate)?\s*[!?.]*$',
        r'^hey+\s+(there|friend|friends|everyone|all|guys?|buddy|mate)?\s*[!?.]*$',
        r'^how\s+are\s+you(\s+today)?(\s+my\s+friend)?\s*[?!.]*$',
        r'^how(\'s|\s+is)\s+(it\s+going|everything|life|your\s+day)\s*[?!.]*$',
        r'^what(\'s|\s+is)\s+up\s*[?!.]*$',
        r'^good\s+(morning|afternoon|evening|night)\s*[!.]*$',
        r'^greetings?\s*[!.]*$',
        r'^yo+\s*[!.]*$',
        r'^sup\s*[?!.]*$',
        r'^howdy\s*[!.]*$',
        r'^nice\s+to\s+(meet|see)\s+you\s*[!.]*$',
        r'^how\s+have\s+you\s+been\s*[?!.]*$',
        r'^long\s+time\s+no\s+see\s*[!.]*$',
        r'^(how\s+are\s+you\s+)?(doing|going)\s*(today|my\s+friend)?\s*[?!.]*$',
    ]

    # Minimum word count for reliable spam detection
    MIN_WORDS_FOR_SPAM_CHECK = 3

    def __init__(self, model_dir='model'):
        """Initialize the predictor with trained model"""
        self.model_dir = model_dir
        self.model = None
        self.vectorizer = None
        self.stemmer = PorterStemmer()
        
        try:
            self.stop_words = set(stopwords.words('english'))
        except:
            self.stop_words = set()
        
        self.load_model()
    
    def load_model(self):
        """Load the trained model and vectorizer"""
        model_path = os.path.join(self.model_dir, 'spam_classifier.pkl')
        vectorizer_path = os.path.join(self.model_dir, 'vectorizer.pkl')
        
        if not os.path.exists(model_path) or not os.path.exists(vectorizer_path):
            raise FileNotFoundError(
                f"Model files not found in {self.model_dir}. "
                "Please train the model first using train.py"
            )
        
        self.model = joblib.load(model_path)
        self.vectorizer = joblib.load(vectorizer_path)
        
        print("✅ Model loaded successfully!")
    
    def is_safe_greeting(self, text):
        """Check if text is a common safe greeting that should not be flagged as spam"""
        trimmed = text.strip()
        for pattern in self.SAFE_GREETING_PATTERNS:
            if re.match(pattern, trimmed, re.IGNORECASE):
                return True
        return False

    def is_too_short(self, text):
        """Check if text is too short for reliable spam detection"""
        words = text.strip().split()
        return len(words) < self.MIN_WORDS_FOR_SPAM_CHECK

    def preprocess_text(self, text):
        """Clean and preprocess text"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove phone numbers
        text = re.sub(r'\b\d{10,}\b', '', text)
        
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove stopwords and apply stemming
        if self.stop_words:
            words = text.split()
            words = [self.stemmer.stem(word) for word in words if word not in self.stop_words]
            text = ' '.join(words)
        
        return text
    
    def extract_features(self, text):
        """Extract features from text for explainability"""
        features = {
            'length': len(text),
            'word_count': len(text.split()),
            'has_url': bool(re.search(r'http\S+|www\S+', text, re.IGNORECASE)),
            'has_email': bool(re.search(r'\S+@\S+', text)),
            'has_phone': bool(re.search(r'\b\d{10,}\b', text)),
            'uppercase_ratio': sum(1 for c in text if c.isupper()) / len(text) if text else 0,
            'exclamation_count': text.count('!'),
            'question_count': text.count('?'),
            'currency_symbols': bool(re.search(r'[$£€¥]', text)),
            'urgency_words': bool(re.search(r'\b(urgent|urgently|asap|now|immediately|hurry|quick|fast)\b', text, re.IGNORECASE)),
            'spam_keywords': bool(re.search(r'\b(free|win|won|winner|prize|claim|click|buy|offer|deal|congratulations|selected|lucky)\b', text, re.IGNORECASE)),
            'money_reference': bool(re.search(r'(\$|£|€|¥)\s*\d+|\d+\s*(dollar|pound|euro|usd|gbp)', text, re.IGNORECASE)),
            'scam_patterns': bool(re.search(r'\b(claim\s+(your|the)|you\s+(won|have\s+won)|verify\s+(your|now)|act\s+now|limited\s+time|expir(e|ing|es))\b', text, re.IGNORECASE)),
        }
        return features

    def calculate_spam_boost(self, features):
        """
        Calculate a spam probability boost based on rule-based features.
        This helps catch obvious spam that the ML model might miss.

        Only boost when there are CLEAR scam indicators, not just money mentions.
        """
        boost = 0.0
        indicators = []

        # Scam patterns are the strongest indicator (e.g., "you won", "claim your")
        has_scam_patterns = features.get('scam_patterns')
        has_spam_keywords = features.get('spam_keywords')
        has_money = features.get('money_reference') or features.get('currency_symbols')
        has_urgency = features.get('urgency_words')

        # Very strong: scam patterns + money = almost certainly spam
        if has_scam_patterns and has_money:
            boost += 0.45
            indicators.append('scam_patterns+money')
        elif has_scam_patterns:
            # Scam patterns alone are still strong indicators
            boost += 0.35
            indicators.append('scam_patterns')

        # Strong: spam keywords (win, prize, claim) + money reference
        if has_spam_keywords and has_money and not has_scam_patterns:
            boost += 0.30
            indicators.append('spam_keywords+money')

        # Moderate: urgency + spam keywords
        if has_urgency and has_spam_keywords:
            boost += 0.15
            indicators.append('urgency+spam_keywords')

        # Note: Money reference alone does NOT boost - people legitimately discuss money
        # Only boost when combined with scam/spam indicators

        # Cap the boost at 0.50 to avoid overriding the model completely
        return min(boost, 0.50), indicators
    
    def predict(self, text):
        """Predict if text is spam or not"""
        # Extract features for explainability (before any processing)
        features = self.extract_features(text)

        # Check if this is a safe greeting - bypass spam detection
        if self.is_safe_greeting(text):
            return {
                'is_spam': False,
                'prediction': 'ham',
                'confidence': 0.95,  # High confidence it's safe
                'probability': 0.05,  # Very low spam probability
                'probabilities': {
                    'ham': 0.95,
                    'spam': 0.05
                },
                'details': {
                    'features': features,
                    'processed_text_length': 0,
                    'original_text_length': len(text),
                    'threshold_applied': self.SPAM_CONFIDENCE_THRESHOLD,
                    'raw_prediction': 'ham',
                    'bypass_reason': 'safe_greeting_pattern',
                    'is_greeting': True
                }
            }

        # Preprocess
        processed_text = self.preprocess_text(text)

        # Vectorize
        text_vectorized = self.vectorizer.transform([processed_text])

        # Predict
        raw_prediction = self.model.predict(text_vectorized)[0]
        probabilities = self.model.predict_proba(text_vectorized)[0]

        # Apply confidence threshold to reduce false positives
        # Only classify as spam if confidence exceeds threshold
        spam_probability = float(probabilities[1])
        original_spam_probability = spam_probability

        # Apply penalty for very short messages to reduce false positives
        too_short = self.is_too_short(text)
        if too_short and spam_probability < 0.90:
            # Reduce spam probability for short messages (they're often greetings)
            spam_probability = spam_probability * 0.6

        # Apply rule-based boost for obvious spam patterns the ML model might miss
        spam_boost, boost_indicators = self.calculate_spam_boost(features)
        if spam_boost > 0:
            # Boost spam probability but cap at 0.99
            spam_probability = min(spam_probability + spam_boost, 0.99)

        is_spam = spam_probability >= self.SPAM_CONFIDENCE_THRESHOLD

        # Prepare result
        result = {
            'is_spam': is_spam,
            'prediction': 'spam' if is_spam else 'ham',
            'confidence': spam_probability if is_spam else float(probabilities[0]),
            'probability': spam_probability,  # Spam probability
            'probabilities': {
                'ham': 1 - spam_probability,
                'spam': spam_probability
            },
            'details': {
                'features': features,
                'processed_text_length': len(processed_text),
                'original_text_length': len(text),
                'threshold_applied': self.SPAM_CONFIDENCE_THRESHOLD,
                'raw_prediction': 'spam' if raw_prediction else 'ham',
                'short_message_penalty_applied': too_short,
                'rule_based_boost': spam_boost,
                'boost_indicators': boost_indicators,
                'ml_spam_probability': original_spam_probability
            }
        }

        return result
    
    def batch_predict(self, texts):
        """Predict multiple texts at once"""
        results = []
        for text in texts:
            try:
                result = self.predict(text)
                results.append(result)
            except Exception as e:
                results.append({
                    'error': str(e),
                    'is_spam': False,
                    'prediction': 'error'
                })
        return results


class MultiModelPredictor:
    """
    Multi-model predictor that loads and uses specialized models for:
    - SMS spam detection
    - Voice call scam detection
    - Phishing detection (URLs, emails, SMS)
    """

    # Confidence thresholds per model type
    # Increased thresholds to reduce false positives on friendly messages
    THRESHOLDS = {
        'sms': 0.80,    # Increased from 0.75
        'voice': 0.80,  # Increased from 0.70
        'phishing': 0.75  # Increased from 0.65
    }

    # Common safe greeting patterns
    SAFE_GREETING_PATTERNS = [
        r'^hi+\s*$',
        r'^hello+\s*$',
        r'^hey+\s*$',
        r'^hi+\s+(there|friend|friends|everyone|all|guys?|buddy|mate)?\s*[!?.]*$',
        r'^hello+\s+(there|friend|friends|everyone|all|guys?|buddy|mate)?\s*[!?.]*$',
        r'^hey+\s+(there|friend|friends|everyone|all|guys?|buddy|mate)?\s*[!?.]*$',
        r'^how\s+are\s+you(\s+today)?(\s+my\s+friend)?\s*[?!.]*$',
        r'^how(\'s|\s+is)\s+(it\s+going|everything|life|your\s+day)\s*[?!.]*$',
        r'^what(\'s|\s+is)\s+up\s*[?!.]*$',
        r'^good\s+(morning|afternoon|evening|night)\s*[!.]*$',
        r'^greetings?\s*[!.]*$',
        r'^yo+\s*[!.]*$',
        r'^sup\s*[?!.]*$',
        r'^howdy\s*[!.]*$',
        r'^nice\s+to\s+(meet|see)\s+you\s*[!.]*$',
        r'^how\s+have\s+you\s+been\s*[?!.]*$',
        r'^long\s+time\s+no\s+see\s*[!.]*$',
        r'^(how\s+are\s+you\s+)?(doing|going)\s*(today|my\s+friend)?\s*[?!.]*$',
    ]

    # Minimum word count for reliable spam detection
    MIN_WORDS_FOR_SPAM_CHECK = 3

    def __init__(self, models_dir: str = 'trained_models'):
        """
        Initialize the multi-model predictor

        Args:
            models_dir: Directory containing trained model subdirectories
        """
        self.models_dir = Path(models_dir)
        self.models = {}
        self.vectorizers = {}
        self.metadata = {}
        self.feature_extractors = {}

        self.stemmer = PorterStemmer()
        try:
            self.stop_words = set(stopwords.words('english'))
        except:
            self.stop_words = set()

        # Load all available models
        self._load_all_models()

    def _load_all_models(self):
        """Load all available models from the models directory"""
        model_types = ['sms', 'voice', 'phishing']

        for model_type in model_types:
            model_dir = self.models_dir / model_type
            if model_dir.exists():
                try:
                    self._load_model(model_type)
                    print(f"  Loaded {model_type} model")
                except Exception as e:
                    print(f"  Warning: Could not load {model_type} model: {e}")

        print(f"MultiModelPredictor initialized with {len(self.models)} models")

    def _load_model(self, model_type: str):
        """Load a specific model type"""
        model_dir = self.models_dir / model_type

        # Load metadata first to get file names
        metadata_path = model_dir / f"{model_type}_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                self.metadata[model_type] = json.load(f)
        else:
            # Default file names
            self.metadata[model_type] = {
                'files': {
                    'model': f'{model_type}_classifier.pkl',
                    'vectorizer': f'{model_type}_vectorizer.pkl'
                }
            }

        # Load model
        model_file = self.metadata[model_type]['files']['model']
        model_path = model_dir / model_file
        if model_path.exists():
            self.models[model_type] = joblib.load(model_path)
        else:
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # Load vectorizer
        vectorizer_file = self.metadata[model_type]['files']['vectorizer']
        vectorizer_path = model_dir / vectorizer_file
        if vectorizer_path.exists():
            self.vectorizers[model_type] = joblib.load(vectorizer_path)
        else:
            raise FileNotFoundError(f"Vectorizer file not found: {vectorizer_path}")

        # Load feature extractor for phishing if available
        if model_type == 'phishing' and HAS_FEATURE_EXTRACTORS:
            custom_features_path = model_dir / "custom_features.json"
            if custom_features_path.exists():
                self.feature_extractors[model_type] = CombinedFeatureExtractor()

    def _is_safe_greeting(self, text: str) -> bool:
        """Check if text is a common safe greeting that should not be flagged as spam"""
        trimmed = text.strip()
        for pattern in self.SAFE_GREETING_PATTERNS:
            if re.match(pattern, trimmed, re.IGNORECASE):
                return True
        return False

    def _is_too_short(self, text: str) -> bool:
        """Check if text is too short for reliable spam detection"""
        words = text.strip().split()
        return len(words) < self.MIN_WORDS_FOR_SPAM_CHECK

    def _preprocess_text(self, text: str, model_type: str = 'sms') -> str:
        """Preprocess text based on model type"""
        if not isinstance(text, str):
            text = str(text)

        # Convert to lowercase
        text = text.lower()

        # Model-specific preprocessing
        if model_type == 'voice':
            # Remove caller/receiver markers for dialogue
            text = re.sub(r'(caller|receiver|agent|customer|scammer|victim):', '', text, flags=re.IGNORECASE)

        # Remove URLs (replace with token)
        text = re.sub(r'http\S+|www\S+|https\S+', ' url ', text, flags=re.MULTILINE)

        # Remove email addresses
        text = re.sub(r'\S+@\S+', ' email ', text)

        # Remove phone numbers
        text = re.sub(r'\b\d{10,}\b', ' phone ', text)

        # Remove special characters
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)

        # Remove extra whitespace
        text = ' '.join(text.split())

        # Remove stopwords and apply stemming
        if self.stop_words:
            words = text.split()
            words = [self.stemmer.stem(word) for word in words if word not in self.stop_words and len(word) > 1]
            text = ' '.join(words)

        return text

    def _extract_features(self, text: str, model_type: str) -> np.ndarray:
        """Extract features for prediction"""
        processed_text = self._preprocess_text(text, model_type)

        # TF-IDF features
        tfidf_features = self.vectorizers[model_type].transform([processed_text]).toarray()

        # Add custom features for phishing
        if model_type == 'phishing' and model_type in self.feature_extractors:
            custom_features = self.feature_extractors[model_type].extract(text)
            custom_array = np.array([list(custom_features.values())])
            return np.hstack([tfidf_features, custom_array])

        return tfidf_features

    def _extract_text_features(self, text: str) -> Dict:
        """Extract human-readable features for explainability"""
        return {
            'length': len(text),
            'word_count': len(text.split()),
            'has_url': bool(re.search(r'http\S+|www\S+', text, re.IGNORECASE)),
            'has_email': bool(re.search(r'\S+@\S+', text)),
            'has_phone': bool(re.search(r'\b\d{10,}\b', text)),
            'uppercase_ratio': sum(1 for c in text if c.isupper()) / len(text) if text else 0,
            'exclamation_count': text.count('!'),
            'question_count': text.count('?'),
            'currency_symbols': bool(re.search(r'[$£€¥]', text)),
            'urgency_words': bool(re.search(r'\b(urgent|asap|now|immediately|hurry|warning|alert)\b', text, re.IGNORECASE)),
            'threat_words': bool(re.search(r'\b(suspend|terminate|block|arrest|legal|police|irs|lawsuit)\b', text, re.IGNORECASE)),
        }

    def _predict(self, text: str, model_type: str) -> Dict:
        """Internal prediction method"""
        if model_type not in self.models:
            raise ValueError(f"Model '{model_type}' not loaded. Available: {list(self.models.keys())}")

        # Label mapping
        labels = {
            'sms': ('ham', 'spam'),
            'voice': ('legitimate', 'scam'),
            'phishing': ('legitimate', 'phishing')
        }
        negative_label, positive_label = labels.get(model_type, ('negative', 'positive'))
        threshold = self.THRESHOLDS.get(model_type, 0.80)

        # Check if this is a safe greeting - bypass spam detection
        if self._is_safe_greeting(text):
            return {
                'is_threat': False,
                'prediction': negative_label,
                'confidence': 0.95,  # High confidence it's safe
                'threat_probability': 0.05,
                'probabilities': {
                    negative_label: 0.95,
                    positive_label: 0.05
                },
                'model_type': model_type,
                'threshold': threshold,
                'details': {
                    'features': self._extract_text_features(text),
                    'raw_prediction': negative_label,
                    'bypass_reason': 'safe_greeting_pattern',
                    'is_greeting': True
                }
            }

        # Extract features
        features = self._extract_features(text, model_type)

        # Predict
        raw_prediction = self.models[model_type].predict(features)[0]
        probabilities = self.models[model_type].predict_proba(features)[0]

        # Apply threshold
        positive_prob = float(probabilities[1])

        # Apply penalty for very short messages to reduce false positives
        too_short = self._is_too_short(text)
        if too_short and positive_prob < 0.90:
            # Reduce threat probability for short messages
            positive_prob = positive_prob * 0.6

        is_positive = positive_prob >= threshold

        return {
            'is_threat': is_positive,
            'prediction': positive_label if is_positive else negative_label,
            'confidence': positive_prob if is_positive else float(probabilities[0]),
            'threat_probability': positive_prob,
            'probabilities': {
                negative_label: float(probabilities[0]),
                positive_label: positive_prob
            },
            'model_type': model_type,
            'threshold': threshold,
            'details': {
                'features': self._extract_text_features(text),
                'raw_prediction': positive_label if raw_prediction else negative_label,
                'short_message_penalty_applied': too_short
            }
        }

    def predict_sms(self, text: str) -> Dict:
        """
        Predict if SMS message is spam

        Args:
            text: SMS message text

        Returns:
            Prediction result with confidence and features
        """
        result = self._predict(text, 'sms')
        result['is_spam'] = result['is_threat']
        return result

    def predict_voice(self, dialogue: str) -> Dict:
        """
        Predict if voice call dialogue is a scam

        Args:
            dialogue: Transcribed voice call dialogue

        Returns:
            Prediction result with confidence and features
        """
        result = self._predict(dialogue, 'voice')
        result['is_scam'] = result['is_threat']
        return result

    def predict_phishing(self, text: str) -> Dict:
        """
        Predict if text/URL is phishing

        Args:
            text: Text content or URL to analyze

        Returns:
            Prediction result with confidence and features
        """
        result = self._predict(text, 'phishing')
        result['is_phishing'] = result['is_threat']
        return result

    def predict_auto(self, text: str) -> Dict:
        """
        Automatically detect content type and predict using appropriate model

        Args:
            text: Any text content (SMS, email, URL, dialogue)

        Returns:
            Prediction result with detected content type
        """
        # Detect content type
        content_type = self._detect_content_type(text)

        # Map content type to model
        model_map = {
            'url': 'phishing',
            'email': 'phishing',
            'dialogue': 'voice',
            'sms': 'sms'
        }
        model_type = model_map.get(content_type, 'sms')

        # Fall back to available model
        if model_type not in self.models:
            model_type = list(self.models.keys())[0] if self.models else None
            if not model_type:
                raise ValueError("No models loaded")

        result = self._predict(text, model_type)
        result['detected_content_type'] = content_type
        result['auto_selected_model'] = model_type

        return result

    def _detect_content_type(self, text: str) -> str:
        """Detect the type of content"""
        # Check for URL-like content
        if re.search(r'^https?://|^www\.', text.strip(), re.IGNORECASE):
            return 'url'

        # Check for email-like content (has email headers or structure)
        if re.search(r'(from:|to:|subject:|dear\s+\w+,)', text, re.IGNORECASE):
            return 'email'

        # Check for dialogue format (caller/receiver markers)
        if re.search(r'(caller:|receiver:|agent:|customer:)', text, re.IGNORECASE):
            return 'dialogue'

        # Check for URL presence in text
        if re.search(r'https?://|www\.', text, re.IGNORECASE):
            return 'url'

        # Default to SMS
        return 'sms'

    def batch_predict(self, texts: list, model_type: str = 'auto') -> list:
        """
        Predict multiple texts

        Args:
            texts: List of text strings
            model_type: Model to use ('sms', 'voice', 'phishing', 'auto')

        Returns:
            List of prediction results
        """
        results = []
        for text in texts:
            try:
                if model_type == 'auto':
                    result = self.predict_auto(text)
                elif model_type == 'sms':
                    result = self.predict_sms(text)
                elif model_type == 'voice':
                    result = self.predict_voice(text)
                elif model_type == 'phishing':
                    result = self.predict_phishing(text)
                else:
                    result = self._predict(text, model_type)
                results.append(result)
            except Exception as e:
                results.append({
                    'error': str(e),
                    'is_threat': False,
                    'prediction': 'error'
                })
        return results

    def get_model_info(self) -> Dict:
        """Get information about loaded models"""
        info = {
            'loaded_models': list(self.models.keys()),
            'models_dir': str(self.models_dir),
            'models': {}
        }

        for model_type in self.models.keys():
            meta = self.metadata.get(model_type, {})
            info['models'][model_type] = {
                'algorithm': meta.get('algorithm', 'unknown'),
                'trained_at': meta.get('trained_at', 'unknown'),
                'metrics': meta.get('metrics', {}),
                'threshold': self.THRESHOLDS.get(model_type, 0.75)
            }

        return info

    def is_model_loaded(self, model_type: str) -> bool:
        """Check if a specific model is loaded"""
        return model_type in self.models

