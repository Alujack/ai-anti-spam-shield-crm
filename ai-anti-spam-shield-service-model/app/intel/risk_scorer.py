"""
Combined Risk Scorer for Phishing Detection

Combines all analysis components:
- Text analysis (40%)
- URL features (25%)
- Domain intelligence (20%)
- Visual analysis (15%)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class RiskScore:
    """Combined risk assessment"""
    total_score: float
    threat_level: ThreatLevel
    text_score: float
    url_score: float
    domain_score: float
    visual_score: float
    indicators: List[Dict]
    recommendation: str
    confidence: float

    def to_dict(self) -> Dict:
        return {
            "total_score": round(self.total_score, 2),
            "threat_level": self.threat_level.value,
            "text_score": round(self.text_score, 2),
            "url_score": round(self.url_score, 2),
            "domain_score": round(self.domain_score, 2),
            "visual_score": round(self.visual_score, 2),
            "indicators": self.indicators,
            "recommendation": self.recommendation,
            "confidence": round(self.confidence, 2),
        }


class PhishingRiskScorer:
    """
    Combined risk scoring for phishing detection

    Weights:
    - Text analysis: 40%
    - URL features: 25%
    - Domain intelligence: 20%
    - Visual analysis: 15%
    """

    # Suspicious URL patterns
    URL_PATTERNS = {
        'ip_address': (r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', 25),
        'long_url': (r'.{100,}', 10),
        'many_subdomains': (r'([a-z0-9-]+\.){4,}', 15),
        'suspicious_keywords': (r'(login|signin|verify|secure|account|update|confirm)', 10),
        'encoded_chars': (r'%[0-9a-fA-F]{2}', 5),
        'at_symbol': (r'@', 20),
        'double_slash': (r'https?://[^/]*//+', 15),
        'suspicious_tld': (r'\.(tk|ml|ga|cf|gq|xyz|top|work|click)$', 15),
    }

    # Recommendations based on threat level
    RECOMMENDATIONS = {
        ThreatLevel.NONE: "This appears to be safe. No phishing indicators detected.",
        ThreatLevel.LOW: "Low risk detected. Proceed with normal caution.",
        ThreatLevel.MEDIUM: "Some suspicious indicators found. Verify the source before proceeding.",
        ThreatLevel.HIGH: "High risk of phishing. Do not enter any personal information.",
        ThreatLevel.CRITICAL: "DANGER: This is very likely a phishing attempt. Do not interact with this site.",
    }

    def __init__(
        self,
        text_weight: float = 0.40,
        url_weight: float = 0.25,
        domain_weight: float = 0.20,
        visual_weight: float = 0.15,
    ):
        self.text_weight = text_weight
        self.url_weight = url_weight
        self.domain_weight = domain_weight
        self.visual_weight = visual_weight

    def calculate_risk(
        self,
        url: str,
        text_result: Optional[Dict] = None,
        domain_intel: Optional[Dict] = None,
        visual_result: Optional[Dict] = None,
    ) -> RiskScore:
        """
        Calculate combined phishing risk score

        Args:
            url: The URL being analyzed
            text_result: Result from text/ML analysis
            domain_intel: Result from domain intelligence
            visual_result: Result from screenshot analysis

        Returns:
            Combined risk score
        """
        indicators = []

        # Calculate text score (from ML model)
        text_score = 0
        if text_result:
            text_score = text_result.get('confidence', 0) * 100
            if text_result.get('is_phishing') or text_result.get('is_spam'):
                indicators.append({
                    'source': 'text_analysis',
                    'description': 'ML model detected phishing patterns',
                    'severity': 'high',
                    'score': text_score,
                })

        # Calculate URL score
        url_score, url_indicators = self._analyze_url(url)
        indicators.extend(url_indicators)

        # Calculate domain score
        domain_score = 0
        if domain_intel:
            domain_score = domain_intel.get('risk_score', 0)
            for indicator in domain_intel.get('risk_indicators', []):
                indicators.append({
                    'source': 'domain_intelligence',
                    'description': indicator,
                    'severity': 'medium',
                    'score': domain_score / len(domain_intel.get('risk_indicators', [1])),
                })

        # Calculate visual score
        visual_score = 0
        if visual_result:
            visual_score = visual_result.get('visual_risk_score', 0)
            if visual_result.get('has_login_form'):
                indicators.append({
                    'source': 'visual_analysis',
                    'description': 'Login form detected',
                    'severity': 'medium',
                    'score': 20,
                })
            if visual_result.get('brand_indicators'):
                brands = ', '.join(visual_result['brand_indicators'])
                indicators.append({
                    'source': 'visual_analysis',
                    'description': f'Brand impersonation detected: {brands}',
                    'severity': 'high',
                    'score': 30,
                })

        # Calculate weighted total
        total_score = (
            text_score * self.text_weight +
            url_score * self.url_weight +
            domain_score * self.domain_weight +
            visual_score * self.visual_weight
        )

        # Boost score if multiple high-severity indicators
        high_severity_count = sum(1 for i in indicators if i.get('severity') == 'high')
        if high_severity_count >= 2:
            total_score = min(100, total_score * 1.3)

        # Determine threat level
        threat_level = self._get_threat_level(total_score)

        # Calculate confidence based on data completeness
        confidence = self._calculate_confidence(
            text_result is not None,
            domain_intel is not None,
            visual_result is not None,
        )

        return RiskScore(
            total_score=total_score,
            threat_level=threat_level,
            text_score=text_score,
            url_score=url_score,
            domain_score=domain_score,
            visual_score=visual_score,
            indicators=indicators,
            recommendation=self.RECOMMENDATIONS[threat_level],
            confidence=confidence,
        )

    def _analyze_url(self, url: str) -> tuple:
        """Analyze URL for phishing patterns"""
        score = 0
        indicators = []

        url_lower = url.lower()

        for pattern_name, (pattern, points) in self.URL_PATTERNS.items():
            if re.search(pattern, url_lower):
                score += points
                indicators.append({
                    'source': 'url_analysis',
                    'description': f'Suspicious URL pattern: {pattern_name}',
                    'severity': 'medium' if points < 15 else 'high',
                    'score': points,
                })

        return min(100, score), indicators

    def _get_threat_level(self, score: float) -> ThreatLevel:
        """Map score to threat level"""
        if score < 20:
            return ThreatLevel.NONE
        elif score < 40:
            return ThreatLevel.LOW
        elif score < 60:
            return ThreatLevel.MEDIUM
        elif score < 80:
            return ThreatLevel.HIGH
        else:
            return ThreatLevel.CRITICAL

    def _calculate_confidence(
        self,
        has_text: bool,
        has_domain: bool,
        has_visual: bool,
    ) -> float:
        """Calculate confidence based on available data"""
        base_confidence = 0.5  # URL analysis always available

        if has_text:
            base_confidence += 0.25
        if has_domain:
            base_confidence += 0.15
        if has_visual:
            base_confidence += 0.10

        return base_confidence


# Usage example
def analyze_phishing_risk(
    url: str,
    text_confidence: float = 0,
    domain_age_days: int = 365,
    has_valid_ssl: bool = True,
) -> Dict:
    """Quick phishing risk analysis"""
    scorer = PhishingRiskScorer()

    # Simulate component results
    text_result = {
        'is_phishing': text_confidence > 0.5,
        'confidence': text_confidence,
    }

    domain_intel = {
        'risk_score': max(0, 50 - domain_age_days / 10),
        'risk_indicators': [],
    }
    if domain_age_days < 30:
        domain_intel['risk_indicators'].append('Domain is less than 30 days old')

    if not has_valid_ssl:
        domain_intel['risk_score'] += 25
        domain_intel['risk_indicators'].append('Invalid SSL certificate')

    result = scorer.calculate_risk(
        url=url,
        text_result=text_result,
        domain_intel=domain_intel,
    )

    return result.to_dict()
