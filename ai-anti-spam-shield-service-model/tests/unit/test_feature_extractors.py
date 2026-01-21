"""
Unit tests for Feature Extractors.
"""

import pytest
from unittest.mock import patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'app'))


class TestURLFeatureExtractor:
    """Tests for the URLFeatureExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create a URLFeatureExtractor instance."""
        from app.model.feature_extractors import URLFeatureExtractor
        return URLFeatureExtractor()

    def test_extract_basic_features(self, extractor):
        """Test basic feature extraction from URL."""
        url = "https://www.example.com/path/to/page"
        features = extractor.extract(url)

        assert 'url_length' in features
        assert 'domain_length' in features
        assert 'has_https' in features
        assert features['has_https'] == 1.0

    def test_extract_http_url(self, extractor):
        """Test HTTP URL feature extraction."""
        url = "http://example.com"
        features = extractor.extract(url)

        assert features['has_http'] == 1.0
        assert features['has_https'] == 0.0

    def test_extract_ip_address_url(self, extractor):
        """Test IP address URL detection."""
        url = "http://192.168.1.1/login"
        features = extractor.extract(url)

        assert features['has_ip_address'] == 1.0

    def test_extract_subdomain_count(self, extractor):
        """Test subdomain counting."""
        url = "https://sub1.sub2.example.com/path"
        features = extractor.extract(url)

        # With tldextract, "www" counts as subdomain
        assert features['subdomain_count'] >= 1

    def test_extract_path_depth(self, extractor):
        """Test path depth calculation."""
        url = "https://example.com/a/b/c/d"
        features = extractor.extract(url)

        assert features['path_depth'] == 4

    def test_extract_query_params(self, extractor):
        """Test query parameter counting."""
        url = "https://example.com/page?param1=a&param2=b&param3=c"
        features = extractor.extract(url)

        assert features['query_param_count'] == 3

    def test_extract_shortened_url(self, extractor):
        """Test shortened URL detection."""
        url = "https://bit.ly/abc123"
        features = extractor.extract(url)

        assert features['is_shortened'] == 1.0

    def test_extract_normal_url_not_shortened(self, extractor):
        """Test that normal URLs are not marked as shortened."""
        url = "https://www.google.com/search"
        features = extractor.extract(url)

        assert features['is_shortened'] == 0.0

    def test_extract_suspicious_tld(self, extractor):
        """Test suspicious TLD detection."""
        url = "http://example.tk/login"
        features = extractor.extract(url)

        assert features['suspicious_tld'] == 1.0

    def test_extract_safe_tld(self, extractor):
        """Test safe TLD detection."""
        url = "https://example.com"
        features = extractor.extract(url)

        assert features['suspicious_tld'] == 0.0

    def test_extract_hex_encoding(self, extractor):
        """Test hex encoding detection."""
        url = "https://example.com/%2F%2Ftest"
        features = extractor.extract(url)

        assert features['has_hexadecimal'] == 1.0

    def test_get_feature_names(self, extractor):
        """Test feature names retrieval."""
        names = extractor.get_feature_names()

        assert isinstance(names, list)
        assert len(names) > 0
        assert 'url_length' in names

    def test_calculate_entropy(self, extractor):
        """Test entropy calculation."""
        # High entropy string (random-like)
        high_entropy = "a1b2c3d4e5f6g7h8"
        # Low entropy string (repetitive)
        low_entropy = "aaaaaaaaaaaaaaaa"

        high_val = extractor._calculate_entropy(high_entropy)
        low_val = extractor._calculate_entropy(low_entropy)

        assert high_val > low_val


class TestTextFeatureExtractor:
    """Tests for the TextFeatureExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create a TextFeatureExtractor instance."""
        from app.model.feature_extractors import TextFeatureExtractor
        return TextFeatureExtractor()

    def test_extract_basic_features(self, extractor):
        """Test basic feature extraction from text."""
        text = "Hello, this is a test message."
        features = extractor.extract(text)

        assert 'text_length' in features
        assert 'word_count' in features
        assert features['text_length'] == len(text)

    def test_extract_url_detection(self, extractor):
        """Test URL detection in text."""
        text = "Check out http://example.com for more info"
        features = extractor.extract(text)

        assert features['url_count'] >= 1

    def test_extract_email_detection(self, extractor):
        """Test email detection in text."""
        text = "Contact me at test@example.com"
        features = extractor.extract(text)

        assert features['email_count'] >= 1

    def test_extract_phone_detection(self, extractor):
        """Test phone number detection in text."""
        text = "Call me at 123-456-7890"
        features = extractor.extract(text)

        assert features['phone_count'] >= 1

    def test_extract_urgency_patterns(self, extractor):
        """Test urgency pattern detection."""
        text = "URGENT: Act immediately before it's too late!"
        features = extractor.extract(text)

        assert features['urgency_score'] > 0

    def test_extract_threat_patterns(self, extractor):
        """Test threat pattern detection."""
        text = "Your account will be suspended unless you verify now"
        features = extractor.extract(text)

        assert features['threat_score'] > 0

    def test_extract_credential_patterns(self, extractor):
        """Test credential request pattern detection."""
        text = "Please enter your password and SSN"
        features = extractor.extract(text)

        assert features['credential_score'] > 0

    def test_extract_financial_patterns(self, extractor):
        """Test financial pattern detection."""
        text = "Your bank account needs verification. Enter your card number."
        features = extractor.extract(text)

        assert features['financial_score'] > 0

    def test_extract_caps_ratio(self, extractor):
        """Test capitalization ratio calculation."""
        text = "THIS IS ALL CAPS"
        features = extractor.extract(text)

        assert features['uppercase_ratio'] > 0.5

    def test_extract_exclamation_count(self, extractor):
        """Test exclamation mark counting."""
        text = "Amazing! Incredible! Don't miss out!"
        features = extractor.extract(text)

        assert features['exclamation_count'] == 3

    def test_extract_safe_message(self, extractor):
        """Test safe message has low scores."""
        text = "Hi, how are you doing?"
        features = extractor.extract(text)

        assert features['urgency_score'] == 0
        assert features['threat_score'] == 0
        assert features['credential_score'] == 0

    def test_extract_currency_detection(self, extractor):
        """Test currency symbol detection."""
        text = "Win $1000 or 500 today!"
        features = extractor.extract(text)

        assert features['has_currency'] == 1.0

    def test_get_feature_names(self, extractor):
        """Test feature names retrieval."""
        names = extractor.get_feature_names()

        assert isinstance(names, list)
        assert len(names) > 0


class TestCombinedFeatureExtractor:
    """Tests for the CombinedFeatureExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create a CombinedFeatureExtractor instance."""
        from app.model.feature_extractors import CombinedFeatureExtractor
        return CombinedFeatureExtractor()

    def test_extract_combined_features(self, extractor):
        """Test combined feature extraction."""
        text = "Click here: http://example.com to win $1000"
        url = "http://example.com"
        features = extractor.extract(text, url)

        # Should have both text and URL features (prefixed)
        assert 'text_text_length' in features
        assert 'url_url_length' in features

    def test_get_feature_names_combined(self, extractor):
        """Test combined feature names."""
        names = extractor.get_feature_names()

        # Should have more features than individual extractors
        assert len(names) > 20


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_extract_url_features(self):
        """Test extract_url_features convenience function."""
        from app.model.feature_extractors import extract_url_features

        features = extract_url_features("https://example.com")
        assert 'url_length' in features

    def test_extract_text_features(self):
        """Test extract_text_features convenience function."""
        from app.model.feature_extractors import extract_text_features

        features = extract_text_features("Hello world")
        assert 'text_length' in features

    def test_extract_combined_features(self):
        """Test extract_combined_features convenience function."""
        from app.model.feature_extractors import extract_combined_features

        features = extract_combined_features("Check http://example.com", "http://example.com")
        assert 'text_text_length' in features
        assert 'url_url_length' in features
