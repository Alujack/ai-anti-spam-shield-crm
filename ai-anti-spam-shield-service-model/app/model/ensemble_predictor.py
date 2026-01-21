"""
Ensemble Predictor V3

Combines multiple prediction sources for maximum accuracy:
1. Pre-trained transformer model (60% weight)
2. Rule-based pattern matching (25% weight)
3. URL/Feature analysis (15% weight)

This ensemble approach ensures:
- High accuracy from transformer models
- Explainability from rule-based detection
- Robustness through multiple signal sources
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

try:
    import tldextract
    HAS_TLDEXTRACT = True
except ImportError:
    HAS_TLDEXTRACT = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    SAFE = "SAFE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class EnsembleResult:
    """Ensemble prediction result with full explainability"""
    is_threat: bool
    confidence: float
    threat_level: str
    prediction: str

    # Component scores
    transformer_score: float
    rule_score: float
    url_score: float

    # Explainability
    indicators: List[Dict]
    urls_analyzed: List[Dict]
    explanation: str
    recommendation: str

    # Metadata
    model_version: str
    ensemble_weights: Dict[str, float]

    def to_dict(self) -> Dict:
        return asdict(self)


class RuleBasedDetector:
    """Rule-based spam/phishing detection for explainability"""

    # Urgency patterns
    URGENCY_PATTERNS = [
        (r'\b(urgent|immediately|asap|right now|today only)\b', 0.15, "Urgency language"),
        (r'\b(act now|hurry|don\'t wait|final notice|last chance)\b', 0.15, "Pressure tactics"),
        (r'\b(within \d+ (hours?|days?|minutes?))\b', 0.10, "Time pressure"),
        (r'\b(expires?|expiring|deadline)\b', 0.10, "Expiration warning"),
    ]

    # Credential request patterns
    CREDENTIAL_PATTERNS = [
        (r'\b(enter|provide|confirm) (your )?(password|pin|ssn)\b', 0.20, "Credential request"),
        (r'\b(verify|update|confirm) (your )?(account|identity|details)\b', 0.15, "Account verification request"),
        (r'\b(login|sign.?in|authenticate)\b', 0.10, "Login request"),
    ]

    # Financial patterns
    FINANCIAL_PATTERNS = [
        (r'\b(bank|credit card|debit card|payment)\b', 0.10, "Financial reference"),
        (r'\b(wire transfer|bitcoin|cryptocurrency|btc|eth)\b', 0.15, "Cryptocurrency/wire transfer"),
        (r'[$£€¥]\s?\d+[,\d]*', 0.10, "Money amount mentioned"),
        (r'\b(free|won|winner|prize|lottery|reward)\b', 0.15, "Prize/reward claim"),
    ]

    # Threat patterns
    THREAT_PATTERNS = [
        (r'\b(suspend|suspended|locked|compromised|unauthorized)\b', 0.15, "Account threat"),
        (r'\b(security alert|security warning|fraud alert)\b', 0.15, "Security warning"),
        (r'\b(legal action|arrest|police|court)\b', 0.15, "Legal threat"),
    ]

    # Brand impersonation
    KNOWN_BRANDS = [
        'paypal', 'amazon', 'netflix', 'apple', 'microsoft', 'google',
        'facebook', 'instagram', 'whatsapp', 'chase', 'wellsfargo',
        'bankofamerica', 'citibank', 'usps', 'fedex', 'ups', 'dhl',
        'irs', 'ssa', 'walmart', 'ebay', 'linkedin', 'dropbox'
    ]

    def __init__(self):
        # Compile all patterns
        self.compiled_patterns = []

        for pattern, weight, desc in self.URGENCY_PATTERNS:
            self.compiled_patterns.append((re.compile(pattern, re.IGNORECASE), weight, desc, "urgency"))

        for pattern, weight, desc in self.CREDENTIAL_PATTERNS:
            self.compiled_patterns.append((re.compile(pattern, re.IGNORECASE), weight, desc, "credential"))

        for pattern, weight, desc in self.FINANCIAL_PATTERNS:
            self.compiled_patterns.append((re.compile(pattern, re.IGNORECASE), weight, desc, "financial"))

        for pattern, weight, desc in self.THREAT_PATTERNS:
            self.compiled_patterns.append((re.compile(pattern, re.IGNORECASE), weight, desc, "threat"))

        # Brand pattern
        self.brand_pattern = re.compile(
            r'\b(' + '|'.join(self.KNOWN_BRANDS) + r')\b',
            re.IGNORECASE
        )

    def analyze(self, text: str) -> Tuple[float, List[Dict]]:
        """
        Analyze text using rule-based patterns

        Returns:
            Tuple of (score, indicators)
        """
        if not text:
            return 0.0, []

        indicators = []
        total_score = 0.0
        text_lower = text.lower()

        # Check all patterns
        for pattern, weight, description, category in self.compiled_patterns:
            matches = pattern.findall(text_lower)
            if matches:
                total_score += weight
                indicators.append({
                    "type": category,
                    "description": description,
                    "matches": list(set(matches))[:3],
                    "weight": weight
                })

        # Check brand impersonation
        brand_matches = self.brand_pattern.findall(text_lower)
        if brand_matches:
            total_score += 0.10
            indicators.append({
                "type": "impersonation",
                "description": "Brand name mentioned",
                "matches": list(set(brand_matches)),
                "weight": 0.10
            })

        # Cap at 1.0
        return min(total_score, 1.0), indicators


class URLAnalyzer:
    """Analyzes URLs for phishing indicators"""

    SUSPICIOUS_TLDS = [
        'tk', 'ml', 'ga', 'cf', 'gq', 'xyz', 'top', 'work', 'click',
        'link', 'info', 'online', 'site', 'website', 'space', 'pw'
    ]

    URL_SHORTENERS = [
        'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly', 'is.gd',
        'buff.ly', 'adf.ly', 'j.mp', 'tr.im', 'cutt.ly', 'rb.gy', 'short.link'
    ]

    SUSPICIOUS_KEYWORDS = [
        'login', 'signin', 'verify', 'secure', 'account', 'update',
        'confirm', 'password', 'bank', 'paypal', 'amazon'
    ]

    def __init__(self):
        self.url_pattern = re.compile(
            r'https?://[^\s<>"\'{}|\\^`\[\]]+',
            re.IGNORECASE
        )

    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        return self.url_pattern.findall(text)

    def analyze_url(self, url: str) -> Tuple[float, Dict]:
        """Analyze a single URL for phishing indicators"""
        score = 0.0
        reasons = []
        url_lower = url.lower()

        # Check for IP address
        if re.match(r'https?://\d+\.\d+\.\d+\.\d+', url):
            score += 0.35
            reasons.append("URL uses IP address instead of domain")

        # Check for @ symbol (URL obfuscation)
        if '@' in url:
            score += 0.30
            reasons.append("URL contains @ symbol (possible obfuscation)")

        # Check TLD
        if HAS_TLDEXTRACT:
            try:
                extracted = tldextract.extract(url)
                if extracted.suffix.lower() in self.SUSPICIOUS_TLDS:
                    score += 0.25
                    reasons.append(f"Suspicious TLD: .{extracted.suffix}")

                # Check for brand in subdomain (typosquatting)
                subdomain = extracted.subdomain.lower()
                for brand in RuleBasedDetector.KNOWN_BRANDS:
                    if brand in subdomain and brand not in extracted.domain.lower():
                        score += 0.30
                        reasons.append(f"Brand '{brand}' in subdomain (possible typosquatting)")
                        break
            except:
                pass

        # Check for URL shortener
        if any(shortener in url_lower for shortener in self.URL_SHORTENERS):
            score += 0.20
            reasons.append("URL shortener detected (may hide destination)")

        # Check for excessive subdomains
        if url.count('.') > 4:
            score += 0.15
            reasons.append("Excessive subdomains")

        # Check for suspicious keywords in URL
        keyword_count = sum(1 for kw in self.SUSPICIOUS_KEYWORDS if kw in url_lower)
        if keyword_count >= 2:
            score += 0.15
            reasons.append(f"Suspicious keywords in URL ({keyword_count} found)")

        # Check for common phishing patterns
        if re.search(r'(verify|secure|update|confirm).*login', url_lower):
            score += 0.20
            reasons.append("Phishing URL pattern detected")

        return min(score, 1.0), {
            "url": url,
            "score": round(min(score, 1.0), 3),
            "is_suspicious": score >= 0.3,
            "reasons": reasons
        }

    def analyze(self, text: str) -> Tuple[float, List[Dict]]:
        """
        Analyze all URLs in text

        Returns:
            Tuple of (max_score, url_analyses)
        """
        urls = self.extract_urls(text)
        if not urls:
            return 0.0, []

        analyses = []
        max_score = 0.0

        for url in urls[:5]:  # Limit to 5 URLs
            score, analysis = self.analyze_url(url)
            analyses.append(analysis)
            max_score = max(max_score, score)

        return max_score, analyses


class EnsemblePredictor:
    """
    Ensemble predictor combining multiple detection methods

    Weights:
    - Transformer: 60% (primary signal)
    - Rule-based: 25% (explainability)
    - URL analysis: 15% (phishing-specific)
    """

    DEFAULT_WEIGHTS = {
        'transformer': 0.60,
        'rules': 0.25,
        'urls': 0.15
    }

    def __init__(
        self,
        model_dir: str = "./trained_models_v3",
        weights: Optional[Dict[str, float]] = None,
        use_gpu: bool = False
    ):
        self.weights = weights or self.DEFAULT_WEIGHTS
        self.model_dir = Path(model_dir)

        # Initialize components
        self.rule_detector = RuleBasedDetector()
        self.url_analyzer = URLAnalyzer()

        # Initialize transformer predictor (lazy load)
        self._transformer_predictor = None
        self._use_gpu = use_gpu

        self.model_version = "ensemble-v3.0.0"

        logger.info(f"Ensemble predictor initialized with weights: {self.weights}")

    def _get_transformer(self):
        """Lazy load transformer predictor"""
        if self._transformer_predictor is None:
            from .predictor_v3 import MultiModelPredictorV3
            self._transformer_predictor = MultiModelPredictorV3(
                model_dir=str(self.model_dir),
                use_gpu=self._use_gpu
            )
        return self._transformer_predictor

    def predict(
        self,
        text: str,
        model_type: str = "auto"
    ) -> EnsembleResult:
        """
        Make ensemble prediction

        Args:
            text: Input text to analyze
            model_type: 'sms', 'phishing', 'voice', or 'auto'

        Returns:
            EnsembleResult with full explainability
        """
        if not text or len(text.strip()) < 2:
            return self._empty_result()

        text = text.strip()

        # Get transformer prediction
        transformer = self._get_transformer()
        if model_type == "auto":
            transformer_result = transformer.predict_auto(text)
        elif model_type == "sms":
            transformer_result = transformer.predict_sms(text)
        elif model_type == "phishing":
            transformer_result = transformer.predict_phishing(text)
        elif model_type == "voice":
            transformer_result = transformer.predict_voice(text)
        else:
            transformer_result = transformer.predict_auto(text)

        transformer_score = transformer_result['confidence'] if transformer_result['is_spam'] else 1 - transformer_result['confidence']

        # Get rule-based score
        rule_score, rule_indicators = self.rule_detector.analyze(text)

        # Get URL score
        url_score, url_analyses = self.url_analyzer.analyze(text)

        # Calculate ensemble score
        ensemble_score = (
            self.weights['transformer'] * transformer_score +
            self.weights['rules'] * rule_score +
            self.weights['urls'] * url_score
        )

        # Apply boosting if multiple sources agree
        agreement_count = sum([
            transformer_score > 0.5,
            rule_score > 0.3,
            url_score > 0.3
        ])
        if agreement_count >= 2:
            ensemble_score = min(ensemble_score * 1.15, 0.99)

        # Determine threat level
        threat_level = self._get_threat_level(ensemble_score)

        # Determine if it's a threat
        is_threat = ensemble_score >= 0.5

        # Combine all indicators
        all_indicators = rule_indicators.copy()
        if transformer_result.get('indicators'):
            all_indicators.extend(transformer_result['indicators'])

        # Generate explanation and recommendation
        explanation = self._generate_explanation(
            is_threat, ensemble_score, transformer_result, rule_indicators, url_analyses
        )
        recommendation = self._generate_recommendation(is_threat, threat_level, url_analyses)

        return EnsembleResult(
            is_threat=is_threat,
            confidence=round(ensemble_score, 4),
            threat_level=threat_level.value,
            prediction="threat" if is_threat else "safe",
            transformer_score=round(transformer_score, 4),
            rule_score=round(rule_score, 4),
            url_score=round(url_score, 4),
            indicators=all_indicators,
            urls_analyzed=url_analyses,
            explanation=explanation,
            recommendation=recommendation,
            model_version=self.model_version,
            ensemble_weights=self.weights
        )

    def predict_batch(self, texts: List[str], model_type: str = "auto") -> List[EnsembleResult]:
        """Predict for multiple texts"""
        return [self.predict(text, model_type) for text in texts]

    def _get_threat_level(self, score: float) -> ThreatLevel:
        """Map score to threat level"""
        if score < 0.3:
            return ThreatLevel.SAFE
        elif score < 0.5:
            return ThreatLevel.LOW
        elif score < 0.7:
            return ThreatLevel.MEDIUM
        elif score < 0.9:
            return ThreatLevel.HIGH
        else:
            return ThreatLevel.CRITICAL

    def _generate_explanation(
        self,
        is_threat: bool,
        score: float,
        transformer_result: Dict,
        rule_indicators: List[Dict],
        url_analyses: List[Dict]
    ) -> str:
        """Generate explanation combining all sources"""
        if not is_threat:
            if score < 0.2:
                return "This message appears to be legitimate. No suspicious patterns detected."
            else:
                return "This message shows minor suspicious characteristics but is likely safe."

        parts = []

        # Transformer insight
        if transformer_result.get('explanation'):
            parts.append(transformer_result['explanation'])

        # Rule-based insights
        if rule_indicators:
            categories = set(ind['type'] for ind in rule_indicators)
            if 'urgency' in categories:
                parts.append("Uses pressure tactics to rush your decision.")
            if 'credential' in categories:
                parts.append("Requests sensitive account information.")
            if 'financial' in categories:
                parts.append("References financial transactions or rewards.")
            if 'threat' in categories:
                parts.append("Contains threatening language about your account.")

        # URL insights
        suspicious_urls = [u for u in url_analyses if u.get('is_suspicious')]
        if suspicious_urls:
            parts.append(f"Contains {len(suspicious_urls)} suspicious URL(s).")

        return " ".join(parts) if parts else "This message has characteristics of spam/phishing."

    def _generate_recommendation(
        self,
        is_threat: bool,
        threat_level: ThreatLevel,
        url_analyses: List[Dict]
    ) -> str:
        """Generate actionable recommendation"""
        if not is_threat:
            return "This message appears safe, but always verify sender identity for sensitive requests."

        if threat_level == ThreatLevel.CRITICAL:
            return "DANGER: Do not interact with this message. Delete immediately and report if possible."
        elif threat_level == ThreatLevel.HIGH:
            return "Do not click any links or respond. Verify the sender through official channels."
        elif threat_level == ThreatLevel.MEDIUM:
            return "Exercise caution. Do not provide personal information without verification."
        else:
            return "Some suspicious elements detected. Verify before taking any action."

    def _empty_result(self) -> EnsembleResult:
        """Return empty/safe result"""
        return EnsembleResult(
            is_threat=False,
            confidence=0.0,
            threat_level=ThreatLevel.SAFE.value,
            prediction="safe",
            transformer_score=0.0,
            rule_score=0.0,
            url_score=0.0,
            indicators=[],
            urls_analyzed=[],
            explanation="No text provided for analysis.",
            recommendation="Provide text to analyze.",
            model_version=self.model_version,
            ensemble_weights=self.weights
        )


# Singleton instance
_ensemble_instance: Optional[EnsemblePredictor] = None


def get_ensemble_predictor(
    model_dir: str = "./trained_models_v3",
    use_gpu: bool = False
) -> EnsemblePredictor:
    """Get or create singleton ensemble predictor"""
    global _ensemble_instance
    if _ensemble_instance is None:
        _ensemble_instance = EnsemblePredictor(model_dir=model_dir, use_gpu=use_gpu)
    return _ensemble_instance


if __name__ == "__main__":
    # Test the ensemble predictor
    predictor = EnsemblePredictor()

    test_messages = [
        "URGENT: Your bank account has been suspended! Click here to verify: http://fake-bank.xyz/verify",
        "Congratulations! You've won $1,000,000 in our lottery! Claim now at bit.ly/claim123",
        "Hey, are you coming to the meeting tomorrow?",
        "Your Amazon order #12345 is ready for delivery. Track: http://amaz0n-delivery.tk/track",
    ]

    print("\n" + "="*70)
    print("Ensemble Predictor V3 Test Results")
    print("="*70)

    for msg in test_messages:
        result = predictor.predict(msg)
        print(f"\nText: {msg[:60]}...")
        print(f"  Threat: {result.is_threat}")
        print(f"  Confidence: {result.confidence:.2%}")
        print(f"  Level: {result.threat_level}")
        print(f"  Scores - Transformer: {result.transformer_score:.2f}, "
              f"Rules: {result.rule_score:.2f}, URLs: {result.url_score:.2f}")
        print(f"  Recommendation: {result.recommendation[:70]}...")
