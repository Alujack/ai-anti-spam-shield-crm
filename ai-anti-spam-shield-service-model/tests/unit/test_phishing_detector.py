"""
Unit tests for PhishingDetector class.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'app'))


class TestPhishingDetector:
    """Tests for the PhishingDetector class."""

    @pytest.fixture
    def detector(self):
        """Create a PhishingDetector with ML disabled for testing."""
        with patch('joblib.load'):
            from app.detectors.phishing_detector import PhishingDetector
            return PhishingDetector(model_dir='test_models', use_ml=False)

    def test_extract_urls_single(self, detector):
        """Test URL extraction with single URL."""
        text = "Visit http://example.com for more info"
        urls = detector.extract_urls(text)

        assert len(urls) == 1
        assert 'http://example.com' in urls

    def test_extract_urls_multiple(self, detector):
        """Test URL extraction with multiple URLs."""
        text = "Check http://example.com and https://test.org for details"
        urls = detector.extract_urls(text)

        assert len(urls) == 2
        assert 'http://example.com' in urls
        assert 'https://test.org' in urls

    def test_extract_urls_no_urls(self, detector):
        """Test URL extraction with no URLs."""
        text = "This is a message without any URLs"
        urls = detector.extract_urls(text)

        assert len(urls) == 0

    def test_rule_based_detection_urgency(self, detector):
        """Test urgency pattern detection."""
        text = "URGENT: Act immediately or your account will be closed!"
        score, indicators = detector._rule_based_detection(text)

        assert score > 0
        assert any('urgency' in i.lower() for i in indicators)

    def test_rule_based_detection_credentials(self, detector):
        """Test credential request pattern detection."""
        text = "Please enter your password and SSN to verify your identity"
        score, indicators = detector._rule_based_detection(text)

        assert score > 0
        assert len(indicators) > 0

    def test_rule_based_detection_financial(self, detector):
        """Test financial pattern detection."""
        text = "Your bank account requires immediate verification. Enter your card number."
        score, indicators = detector._rule_based_detection(text)

        assert score > 0

    def test_rule_based_detection_safe_message(self, detector):
        """Test that safe messages have low scores."""
        text = "Hi, how are you doing?"
        score, indicators = detector._rule_based_detection(text)

        assert score < 0.3
        assert len(indicators) == 0

    def test_analyze_urls_ip_address(self, detector):
        """Test IP address URL detection."""
        urls = ["http://192.168.1.1/login"]
        results = detector._analyze_urls(urls)

        assert len(results) == 1
        assert results[0].is_suspicious is True
        assert any('IP' in r for r in results[0].reasons)

    def test_analyze_urls_suspicious_tld(self, detector):
        """Test suspicious TLD detection."""
        urls = ["http://example.tk/verify"]
        results = detector._analyze_urls(urls)

        assert results[0].is_suspicious is True

    def test_analyze_urls_safe_url(self, detector):
        """Test safe URL analysis."""
        urls = ["https://www.google.com"]
        results = detector._analyze_urls(urls)

        # Google should not be suspicious
        assert results[0].is_suspicious is False

    def test_detect_brand_impersonation_paypal(self, detector):
        """Test PayPal brand impersonation detection."""
        text = "Your PayPal account has been limited"
        urls = ["http://paypa1-verify.tk/login"]

        result = detector._detect_brand_impersonation(text, urls)

        assert result.detected is True
        assert 'paypal' in result.brand.lower()

    def test_detect_brand_impersonation_none(self, detector):
        """Test no brand impersonation for clean message."""
        text = "Hello, how are you today?"
        urls = []

        result = detector._detect_brand_impersonation(text, urls)

        assert result.detected is False

    def test_determine_threat_level_critical(self, detector):
        """Test CRITICAL threat level determination."""
        from app.detectors.phishing_detector import ThreatLevel
        threat = detector._determine_threat_level(0.92, ['a', 'b', 'c', 'd', 'e'])

        assert threat == ThreatLevel.CRITICAL

    def test_determine_threat_level_high(self, detector):
        """Test HIGH threat level determination."""
        from app.detectors.phishing_detector import ThreatLevel
        threat = detector._determine_threat_level(0.78, ['a', 'b', 'c'])

        assert threat == ThreatLevel.HIGH

    def test_determine_threat_level_medium(self, detector):
        """Test MEDIUM threat level determination."""
        from app.detectors.phishing_detector import ThreatLevel
        threat = detector._determine_threat_level(0.55, ['a', 'b'])

        assert threat == ThreatLevel.MEDIUM

    def test_determine_threat_level_low(self, detector):
        """Test LOW threat level determination."""
        from app.detectors.phishing_detector import ThreatLevel
        threat = detector._determine_threat_level(0.35, ['a'])

        assert threat == ThreatLevel.LOW

    def test_determine_threat_level_none(self, detector):
        """Test NONE threat level determination."""
        from app.detectors.phishing_detector import ThreatLevel
        threat = detector._determine_threat_level(0.15, [])

        assert threat == ThreatLevel.NONE

    def test_detect_full_pipeline_phishing(self, detector, sample_phishing_texts):
        """Test complete detection pipeline with phishing text."""
        result = detector.detect(sample_phishing_texts[0], scan_type='email')

        # Without ML, result may not reach phishing threshold, but should have indicators
        assert len(result.indicators) > 0
        assert result.recommendation != ''

    def test_detect_full_pipeline_safe(self, detector, sample_ham_messages):
        """Test complete detection pipeline with safe text."""
        result = detector.detect(sample_ham_messages[0], scan_type='auto')

        assert result.is_phishing is False
        assert result.threat_level in ['NONE', 'LOW']

    def test_detect_auto_scan_type(self, detector):
        """Test auto scan type detection."""
        # URL should be detected as URL type
        result = detector.detect("http://suspicious-site.tk/login", scan_type='auto')

        assert result is not None

    def test_detect_returns_recommendation(self, detector, sample_phishing_texts):
        """Test that detection returns a recommendation."""
        result = detector.detect(sample_phishing_texts[0])

        assert result.recommendation is not None
        assert len(result.recommendation) > 0

    def test_is_suspicious_domain(self, detector):
        """Test suspicious domain check."""
        assert detector.is_suspicious_domain("http://example.tk") is True
        assert detector.is_suspicious_domain("https://google.com") is False

    def test_check_brand_impersonation(self, detector):
        """Test brand impersonation check."""
        # Text with PayPal mention and suspicious URL
        result = detector.check_brand_impersonation(
            "Your PayPal account at http://paypa1.tk"
        )

        assert result is True


class TestPhishingResult:
    """Tests for PhishingResult data class."""

    def test_to_dict(self, mock_phishing_detector, sample_phishing_texts):
        """Test PhishingResult to_dict conversion."""
        result = mock_phishing_detector.detect(sample_phishing_texts[0])
        result_dict = result.to_dict()

        assert 'is_phishing' in result_dict
        assert 'confidence' in result_dict
        assert 'threat_level' in result_dict
        assert 'indicators' in result_dict
        assert 'recommendation' in result_dict


class TestURLAnalysisResult:
    """Tests for URLAnalysisResult data class."""

    def test_url_analysis_result(self, mock_phishing_detector):
        """Test URL analysis result structure."""
        urls = ["http://192.168.1.1/phish"]
        results = mock_phishing_detector._analyze_urls(urls)

        assert len(results) == 1
        assert hasattr(results[0], 'url')
        assert hasattr(results[0], 'is_suspicious')
        assert hasattr(results[0], 'reasons')
        assert hasattr(results[0], 'score')
