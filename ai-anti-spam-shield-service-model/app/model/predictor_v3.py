"""
V3 Predictor using Pre-trained HuggingFace Models

This module provides production-ready prediction using:
1. Fine-tuned pre-trained models (if available)
2. Fallback to HuggingFace pre-trained models
3. Rule-based boosting for edge cases

Features:
- Automatic model selection (fine-tuned > pre-trained)
- Confidence calibration
- Risk level classification
- Scam category detection
- Human-readable explanations
- Elder-friendly warnings
"""

import os
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

import numpy as np

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

logging.basicConfig(level=logging.INFO)
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
    DELIVERY = "DELIVERY_SCAM"


@dataclass
class PredictionResultV3:
    """Structured prediction result for V3"""
    is_spam: bool
    confidence: float
    prediction: str
    risk_level: str
    category: Optional[str]
    explanation: str
    indicators: List[Dict]
    model_version: str
    model_source: str  # 'finetuned', 'pretrained', or 'fallback'

    def to_dict(self) -> Dict:
        return asdict(self)


# Pre-trained model configurations
PRETRAINED_MODELS = {
    'sms': {
        'model_name': 'mrm8488/bert-tiny-finetuned-sms-spam-detection',
        'backup_models': [
            'mariagrandury/roberta-base-finetuned-sms-spam-detection',
            'distilbert-base-uncased-finetuned-sst-2-english'
        ],
        'spam_labels': ['LABEL_1', 'spam', 'SPAM', '1'],
        'confidence_threshold': 0.75,
    },
    'phishing': {
        'model_name': 'cybersectony/phishing-email-detection-distilbert_v2.4.1',
        'backup_models': [
            'ealvaradob/bert-finetuned-phishing',
        ],
        'spam_labels': ['phishing', 'LABEL_1', 'spam', '1'],
        'confidence_threshold': 0.70,
    },
    'voice': {
        'model_name': 'mrm8488/bert-tiny-finetuned-sms-spam-detection',  # Transfer from SMS
        'backup_models': [],
        'spam_labels': ['LABEL_1', 'spam', 'SPAM', '1'],
        'confidence_threshold': 0.75,
    }
}


# Scam indicator patterns for rule-based boosting
SCAM_PATTERNS = {
    ScamCategory.PRIZE: [
        r'\bwon\b', r'\bwinner\b', r'\bprize\b', r'\blottery\b', r'\bcongratulations\b',
        r'\bclaim\b', r'\breward\b', r'\$\d+', r'\bmillion\b', r'\bfree\s+gift\b',
    ],
    ScamCategory.BANK: [
        r'\bbank\b', r'\baccount\s+(suspended|locked|compromised)\b', r'\bverify\b',
        r'\btransaction\b', r'\bunauthorized\b', r'\bfraud\b', r'\bsecurity\s+alert\b',
    ],
    ScamCategory.CRYPTO: [
        r'\bbitcoin\b', r'\bbtc\b', r'\bcrypto\b', r'\binvest\b', r'\btrading\b',
        r'\bwallet\b', r'\bblockchain\b', r'\bprofit\b', r'\bethereum\b',
    ],
    ScamCategory.PHISHING: [
        r'\bpassword\b', r'\blogin\b', r'\bcredential\b', r'\bexpire\b',
        r'\bclick\s+here\b', r'\bverify\s+(your)?\s*account\b', r'\bupdate.*account\b',
    ],
    ScamCategory.URGENCY: [
        r'\burgent\b', r'\bimmediate(ly)?\b', r'\bnow\b', r'\bexpire\b', r'\blimited\b',
        r'\bact\s+fast\b', r"\bdon't\s+miss\b", r'\blast\s+chance\b', r'\b24\s+hours?\b',
    ],
    ScamCategory.IMPERSONATION: [
        r'\bamazon\b', r'\bpaypal\b', r'\bapple\b', r'\bmicrosoft\b', r'\bgoogle\b',
        r'\bnetflix\b', r'\bfacebook\b', r'\binstagram\b', r'\bwhatsapp\b',
    ],
    ScamCategory.DELIVERY: [
        r'\bpackage\b', r'\bdelivery\b', r'\bshipment\b', r'\btracking\b',
        r'\bups\b', r'\bfedex\b', r'\busps\b', r'\bdhl\b',
    ],
    ScamCategory.TECH_SUPPORT: [
        r'\bvirus\b', r'\bmalware\b', r'\btech\s+support\b', r'\bcomputer\b',
        r'\bwindows\b', r'\bmicrosoft\s+support\b', r'\bcall\s+(us|now)\b',
    ],
}

# Safe greeting patterns - should not be flagged as spam
SAFE_PATTERNS = [
    r'^(hi|hello|hey|good\s+(morning|afternoon|evening))[\s,!.]*$',
    r'^(thanks|thank\s+you|thx)[\s,!.]*$',
    r'^(ok|okay|sure|yes|no|yep|nope)[\s,!.]*$',
    r'^(bye|goodbye|see\s+you|talk\s+later)[\s,!.]*$',
]


class PretrainedSpamPredictor:
    """
    V3 Predictor using fine-tuned or pre-trained HuggingFace models

    Features:
    - Automatically uses fine-tuned model if available
    - Falls back to pre-trained HuggingFace model
    - Rule-based boosting for edge cases
    - Confidence calibration
    """

    def __init__(
        self,
        model_type: str = "sms",
        model_dir: str = "./trained_models_v3",
        use_gpu: bool = False,
        confidence_threshold: Optional[float] = None
    ):
        if not HAS_TRANSFORMERS or not HAS_TORCH:
            raise ImportError("transformers and torch libraries required. Install with: pip install transformers torch")

        self.model_type = model_type
        self.model_dir = Path(model_dir) / model_type / "model"
        self.config = PRETRAINED_MODELS.get(model_type)

        if not self.config:
            raise ValueError(f"Unknown model type: {model_type}")

        self.confidence_threshold = confidence_threshold or self.config['confidence_threshold']
        self.device = 0 if use_gpu and HAS_TORCH and torch.cuda.is_available() else -1

        # Compile patterns
        self.scam_patterns = {
            cat: [re.compile(p, re.IGNORECASE) for p in patterns]
            for cat, patterns in SCAM_PATTERNS.items()
        }
        self.safe_patterns = [re.compile(p, re.IGNORECASE) for p in SAFE_PATTERNS]

        # Load model
        self.classifier = None
        self.model_source = None
        self._load_model()

        logger.info(f"V3 Predictor initialized: {model_type} (source: {self.model_source})")

    def _load_model(self):
        """Load the best available model"""
        # Try fine-tuned model first
        if self.model_dir.exists():
            try:
                logger.info(f"Loading fine-tuned model from {self.model_dir}")
                self.classifier = pipeline(
                    "text-classification",
                    model=str(self.model_dir),
                    device=self.device,
                    truncation=True
                )
                self.model_source = "finetuned"
                self.model_version = f"{self.model_type}-v3.0.0-finetuned"
                return
            except Exception as e:
                logger.warning(f"Failed to load fine-tuned model: {e}")

        # Try pre-trained model
        try:
            logger.info(f"Loading pre-trained model: {self.config['model_name']}")
            self.classifier = pipeline(
                "text-classification",
                model=self.config['model_name'],
                device=self.device,
                truncation=True
            )
            self.model_source = "pretrained"
            self.model_version = f"{self.model_type}-v3.0.0-pretrained"
            return
        except Exception as e:
            logger.warning(f"Failed to load pre-trained model: {e}")

        # Try backup models
        for backup_model in self.config.get('backup_models', []):
            try:
                logger.info(f"Trying backup model: {backup_model}")
                self.classifier = pipeline(
                    "text-classification",
                    model=backup_model,
                    device=self.device,
                    truncation=True
                )
                self.model_source = "fallback"
                self.model_version = f"{self.model_type}-v3.0.0-fallback"
                return
            except Exception as e:
                logger.warning(f"Failed to load backup model {backup_model}: {e}")

        raise RuntimeError(f"Failed to load any model for {self.model_type}")

    def predict(self, text: str) -> PredictionResultV3:
        """
        Predict spam/phishing for a single text

        Args:
            text: Input text to classify

        Returns:
            Structured prediction result
        """
        if not text or len(text.strip()) < 2:
            return self._empty_result()

        text = text.strip()

        # Check for safe greetings (bypass spam detection)
        if self._is_safe_greeting(text):
            return self._safe_result(text)

        # Get model prediction
        try:
            result = self.classifier(text[:512])[0]
            label = result['label']
            raw_confidence = result['score']

            # Determine if it's spam based on label
            is_spam_label = label.lower() in [l.lower() for l in self.config['spam_labels']]

            if is_spam_label:
                spam_confidence = raw_confidence
            else:
                spam_confidence = 1.0 - raw_confidence

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return self._error_result(str(e))

        # Apply rule-based boosting
        rule_boost, indicators = self._calculate_rule_boost(text)

        # Combine ML and rule-based scores
        final_confidence = min(spam_confidence + rule_boost * 0.3, 0.99)

        # Apply short message penalty (reduce false positives)
        if len(text) < 20 and final_confidence < 0.9:
            final_confidence *= 0.7

        # Determine if it's spam
        is_spam = final_confidence >= self.confidence_threshold

        # Determine risk level and category
        risk_level = self._get_risk_level(final_confidence)
        category, category_indicators = self._detect_category(text, is_spam)

        # Combine indicators
        all_indicators = indicators + category_indicators

        # Generate explanation
        explanation = self._generate_explanation(is_spam, final_confidence, category, all_indicators)

        return PredictionResultV3(
            is_spam=is_spam,
            confidence=round(final_confidence, 4),
            prediction="spam" if is_spam else "ham",
            risk_level=risk_level.value,
            category=category.value if category != ScamCategory.NONE else None,
            explanation=explanation,
            indicators=all_indicators,
            model_version=self.model_version,
            model_source=self.model_source
        )

    def predict_batch(self, texts: List[str]) -> List[PredictionResultV3]:
        """Predict for multiple texts"""
        return [self.predict(text) for text in texts]

    def _is_safe_greeting(self, text: str) -> bool:
        """Check if text is a safe greeting"""
        text_clean = text.strip().lower()
        if len(text_clean) > 50:
            return False
        return any(p.match(text_clean) for p in self.safe_patterns)

    def _calculate_rule_boost(self, text: str) -> Tuple[float, List[Dict]]:
        """Calculate rule-based spam boost"""
        indicators = []
        total_boost = 0.0

        text_lower = text.lower()

        for category, patterns in self.scam_patterns.items():
            matches = []
            for pattern in patterns:
                found = pattern.findall(text_lower)
                if found:
                    matches.extend(found)

            if matches:
                category_boost = min(len(matches) * 0.05, 0.2)
                total_boost += category_boost

                indicators.append({
                    "type": category.value.lower(),
                    "matches": matches[:3],
                    "boost": round(category_boost, 3)
                })

        return min(total_boost, 0.4), indicators

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

    def _detect_category(self, text: str, is_spam: bool) -> Tuple[ScamCategory, List[Dict]]:
        """Detect scam category"""
        if not is_spam:
            return ScamCategory.NONE, []

        text_lower = text.lower()
        category_scores = {}
        indicators = []

        for category, patterns in self.scam_patterns.items():
            matches = []
            for pattern in patterns:
                found = pattern.findall(text_lower)
                if found:
                    matches.extend(found)

            if matches:
                category_scores[category] = len(matches)
                indicators.append({
                    "category": category.value,
                    "matched_terms": list(set(matches))[:3]
                })

        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            return best_category, indicators

        return ScamCategory.NONE, []

    def _generate_explanation(
        self,
        is_spam: bool,
        confidence: float,
        category: ScamCategory,
        indicators: List[Dict]
    ) -> str:
        """Generate human-readable explanation"""
        if not is_spam:
            if confidence < 0.3:
                return "This message appears to be legitimate and safe."
            else:
                return "This message shows some characteristics that could be suspicious, but is likely safe."

        explanations = {
            ScamCategory.PRIZE: "This message contains prize/lottery claims commonly used in scams.",
            ScamCategory.BANK: "This message mimics bank communications and may attempt to steal financial information.",
            ScamCategory.CRYPTO: "This message promotes cryptocurrency investments which are often scams.",
            ScamCategory.PHISHING: "This message attempts to steal login credentials or personal information.",
            ScamCategory.URGENCY: "This message uses urgency tactics to pressure you into acting quickly.",
            ScamCategory.IMPERSONATION: "This message impersonates a known brand or company.",
            ScamCategory.DELIVERY: "This message falsely claims to be about a package delivery.",
            ScamCategory.TECH_SUPPORT: "This message pretends to be technical support to gain access to your device.",
            ScamCategory.NONE: "This message shows characteristics typical of spam or scam messages.",
        }

        base = explanations.get(category, explanations[ScamCategory.NONE])

        if confidence >= 0.9:
            qualifier = "This is highly likely to be a scam. Do not respond."
        elif confidence >= 0.75:
            qualifier = "This is likely a scam. Exercise extreme caution."
        else:
            qualifier = "This message is suspicious. Verify before taking any action."

        return f"{base} {qualifier}"

    def _empty_result(self) -> PredictionResultV3:
        """Return empty/safe result for empty input"""
        return PredictionResultV3(
            is_spam=False,
            confidence=0.0,
            prediction="ham",
            risk_level=RiskLevel.NONE.value,
            category=None,
            explanation="No text provided for analysis.",
            indicators=[],
            model_version=self.model_version if hasattr(self, 'model_version') else "unknown",
            model_source=self.model_source if hasattr(self, 'model_source') else "unknown"
        )

    def _safe_result(self, text: str) -> PredictionResultV3:
        """Return safe result for greetings"""
        return PredictionResultV3(
            is_spam=False,
            confidence=0.05,
            prediction="ham",
            risk_level=RiskLevel.NONE.value,
            category=None,
            explanation="This appears to be a normal greeting or response.",
            indicators=[],
            model_version=self.model_version,
            model_source=self.model_source
        )

    def _error_result(self, error: str) -> PredictionResultV3:
        """Return error result"""
        return PredictionResultV3(
            is_spam=False,
            confidence=0.5,
            prediction="unknown",
            risk_level=RiskLevel.LOW.value,
            category=None,
            explanation=f"Prediction error: {error}. Please try again.",
            indicators=[{"error": error}],
            model_version=self.model_version,
            model_source=self.model_source
        )

    def get_elder_warnings(self, result: PredictionResultV3) -> List[str]:
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
                "Banks will never ask for your full password via text or email.",
                "Call your bank directly if you're concerned about your account.",
            ],
            ScamCategory.URGENCY.value: [
                "Scammers create false urgency to prevent you from thinking clearly.",
                "It's always okay to wait and verify before responding.",
            ],
            ScamCategory.DELIVERY.value: [
                "Check your orders directly on the retailer's website.",
                "Delivery companies won't ask for payment via text links.",
            ],
            ScamCategory.TECH_SUPPORT.value: [
                "Microsoft, Apple, and Google will never call you about viruses.",
                "Never give remote access to someone who contacts you first.",
            ],
        }

        if result.category in category_warnings:
            warnings.extend(category_warnings[result.category])

        return warnings[:5]


class MultiModelPredictorV3:
    """
    Unified V3 predictor supporting multiple model types
    """

    def __init__(self, model_dir: str = "./trained_models_v3", use_gpu: bool = False):
        self.predictors: Dict[str, PretrainedSpamPredictor] = {}
        self.model_dir = model_dir
        self.use_gpu = use_gpu

        # Lazy load models on first use
        self._initialized_models = set()

    def _get_predictor(self, model_type: str) -> PretrainedSpamPredictor:
        """Get or create predictor for model type"""
        if model_type not in self.predictors:
            try:
                self.predictors[model_type] = PretrainedSpamPredictor(
                    model_type=model_type,
                    model_dir=self.model_dir,
                    use_gpu=self.use_gpu
                )
                self._initialized_models.add(model_type)
            except Exception as e:
                logger.error(f"Failed to initialize {model_type} predictor: {e}")
                raise

        return self.predictors[model_type]

    def predict_sms(self, text: str) -> Dict:
        """Predict SMS spam"""
        predictor = self._get_predictor('sms')
        return predictor.predict(text).to_dict()

    def predict_phishing(self, text: str) -> Dict:
        """Predict phishing"""
        predictor = self._get_predictor('phishing')
        return predictor.predict(text).to_dict()

    def predict_voice(self, text: str) -> Dict:
        """Predict voice scam (from transcript)"""
        predictor = self._get_predictor('voice')
        return predictor.predict(text).to_dict()

    def predict_auto(self, text: str) -> Dict:
        """Auto-detect content type and predict"""
        # Heuristic to determine content type
        text_lower = text.lower()

        # Check for phishing indicators
        phishing_indicators = ['http', 'https', 'click', 'verify', 'password', 'login', 'account']
        phishing_score = sum(1 for ind in phishing_indicators if ind in text_lower)

        if phishing_score >= 2 or 'http' in text_lower:
            return self.predict_phishing(text)

        # Default to SMS
        return self.predict_sms(text)

    def predict_with_elder_mode(self, text: str, model_type: str = "sms") -> Dict:
        """Predict with elder-friendly warnings"""
        predictor = self._get_predictor(model_type)
        result = predictor.predict(text)

        return {
            **result.to_dict(),
            "elder_warnings": predictor.get_elder_warnings(result)
        }

    def is_loaded(self, model_type: str = None) -> bool:
        """Check if models are loaded"""
        if model_type:
            return model_type in self._initialized_models
        return len(self._initialized_models) > 0

    def get_available_models(self) -> List[str]:
        """Get list of available model types"""
        return list(PRETRAINED_MODELS.keys())

    def get_loaded_models(self) -> List[str]:
        """Get list of currently loaded models"""
        return list(self._initialized_models)


# Singleton instance for easy import
_predictor_instance: Optional[MultiModelPredictorV3] = None


def get_predictor(model_dir: str = "./trained_models_v3", use_gpu: bool = False) -> MultiModelPredictorV3:
    """Get or create singleton predictor instance"""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = MultiModelPredictorV3(model_dir=model_dir, use_gpu=use_gpu)
    return _predictor_instance


if __name__ == "__main__":
    # Test the predictor
    predictor = MultiModelPredictorV3()

    test_messages = [
        # Spam
        "Congratulations! You've won $1,000,000! Click here to claim your prize now!",
        "URGENT: Your bank account has been suspended. Verify immediately: http://fake-bank.com",
        "You have a package waiting. Track it here: bit.ly/fake123",

        # Ham
        "Hey, are you coming to the meeting tomorrow?",
        "Thanks for your help yesterday!",
        "Hi",
    ]

    print("\n" + "="*60)
    print("V3 Predictor Test Results")
    print("="*60)

    for msg in test_messages:
        result = predictor.predict_auto(msg)
        print(f"\nText: {msg[:50]}...")
        print(f"  Spam: {result['is_spam']}")
        print(f"  Confidence: {result['confidence']:.2%}")
        print(f"  Risk: {result['risk_level']}")
        print(f"  Category: {result.get('category', 'N/A')}")
        print(f"  Model: {result['model_source']}")
