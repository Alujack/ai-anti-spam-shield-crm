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
                try:
                    self.predictors[model_type] = TransformerPredictor(
                        model_type=model_type,
                        model_dir=model_dir,
                    )
                    logger.info(f"Loaded v2 {model_type} predictor")
                except Exception as e:
                    logger.warning(f"Could not load v2 {model_type} predictor: {e}")

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

    def is_loaded(self) -> bool:
        """Check if any models are loaded"""
        return len(self.predictors) > 0

    def get_available_models(self) -> List[str]:
        """Get list of available model types"""
        return list(self.predictors.keys())
