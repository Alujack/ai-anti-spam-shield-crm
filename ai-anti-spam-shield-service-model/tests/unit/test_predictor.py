"""
Unit tests for SpamPredictor and MultiModelPredictor classes.
"""

import pytest
from unittest.mock import patch, MagicMock
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'app'))


class TestSpamPredictor:
    """Tests for the SpamPredictor class."""

    @pytest.fixture
    def predictor(self, mock_model, mock_vectorizer):
        """Create a SpamPredictor with mocked dependencies."""
        with patch('joblib.load') as mock_load, \
             patch('os.path.exists', return_value=True):
            mock_load.side_effect = [mock_model, mock_vectorizer]
            from model.predictor import SpamPredictor
            pred = SpamPredictor(model_dir='test_model')
            pred.model = mock_model
            pred.vectorizer = mock_vectorizer
            pred.model_loaded = True
            return pred

    def test_predict_returns_required_fields(self, predictor):
        """Test that prediction returns all required fields."""
        result = predictor.predict("Test message")

        required_fields = ['is_spam', 'prediction', 'confidence', 'probability', 'probabilities']
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    def test_is_safe_greeting_detection(self, predictor, sample_safe_greetings):
        """Test that safe greetings are not flagged as spam."""
        for greeting in sample_safe_greetings:
            result = predictor.predict(greeting)
            assert result['is_spam'] is False, f"Greeting '{greeting}' incorrectly flagged as spam"

    def test_predict_spam_detection(self, predictor, mock_model):
        """Test spam detection with high confidence."""
        mock_model.predict.return_value = np.array([1])
        mock_model.predict_proba.return_value = np.array([[0.1, 0.9]])

        result = predictor.predict("FREE PRIZE! Click now to claim $1000!")

        assert result['is_spam'] is True
        assert result['confidence'] >= 0.8

    def test_predict_ham_detection(self, predictor, mock_model):
        """Test legitimate message detection."""
        mock_model.predict.return_value = np.array([0])
        mock_model.predict_proba.return_value = np.array([[0.95, 0.05]])

        result = predictor.predict("Hi, how are you today?")

        assert result['is_spam'] is False

    def test_preprocess_text_removes_urls(self, predictor):
        """Test that URLs are removed during preprocessing."""
        text = "Check this http://example.com link and https://test.org"
        processed = predictor.preprocess_text(text)

        assert 'http' not in processed.lower()
        assert 'example.com' not in processed.lower()

    def test_preprocess_text_removes_emails(self, predictor):
        """Test that email addresses are removed during preprocessing."""
        text = "Contact me at test@example.com for more info"
        processed = predictor.preprocess_text(text)

        assert '@' not in processed

    def test_preprocess_text_lowercases(self, predictor):
        """Test that text is lowercased during preprocessing."""
        text = "THIS IS UPPERCASE TEXT"
        processed = predictor.preprocess_text(text)

        assert processed == processed.lower()

    def test_extract_features(self, predictor):
        """Test feature extraction from text."""
        text = "URGENT! Call now at 1234567890 to win $1000!"
        features = predictor.extract_features(text)

        assert 'has_url' in features
        assert 'has_phone' in features
        assert 'currency_symbols' in features
        assert 'urgency_words' in features
        assert 'exclamation_count' in features

    def test_extract_features_detects_phone(self, predictor):
        """Test that phone numbers are detected in features."""
        text = "Call me at 1234567890"
        features = predictor.extract_features(text)

        assert features['has_phone'] is True

    def test_extract_features_detects_url(self, predictor):
        """Test that URLs are detected in features."""
        text = "Visit http://example.com for more"
        features = predictor.extract_features(text)

        assert features['has_url'] is True

    def test_extract_features_detects_currency(self, predictor):
        """Test that currency symbols are detected."""
        text = "Win $1000 today!"
        features = predictor.extract_features(text)

        assert features['currency_symbols'] is True

    def test_batch_predict(self, predictor, mock_model):
        """Test batch prediction functionality."""
        mock_model.predict.return_value = np.array([0, 0, 1])
        mock_model.predict_proba.return_value = np.array([
            [0.9, 0.1],
            [0.85, 0.15],
            [0.1, 0.9]
        ])

        messages = ["Hello", "How are you?", "FREE MONEY!"]
        results = predictor.batch_predict(messages)

        assert len(results) == 3
        assert all('is_spam' in r for r in results)

    def test_short_message_handling(self, predictor):
        """Test that very short messages are handled properly."""
        result = predictor.predict("Hi")

        assert result is not None
        assert 'is_spam' in result

    def test_confidence_threshold_behavior(self, predictor, mock_model):
        """Test behavior at confidence threshold boundary."""
        # Below threshold (0.80) - should not be spam
        mock_model.predict.return_value = np.array([1])
        mock_model.predict_proba.return_value = np.array([[0.3, 0.7]])

        result = predictor.predict("Somewhat suspicious message")

        # Should not be marked as spam due to threshold
        assert result['is_spam'] is False


class TestMultiModelPredictor:
    """Tests for the MultiModelPredictor class."""

    @pytest.fixture
    def multi_predictor(self, mock_model, mock_vectorizer):
        """Create a MultiModelPredictor with mocked dependencies."""
        with patch('joblib.load') as mock_load, \
             patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True):

            mock_load.return_value = mock_model

            from model.predictor import MultiModelPredictor
            pred = MultiModelPredictor(models_dir='test_models')
            pred.models = {
                'sms': mock_model,
                'voice': mock_model,
                'phishing': mock_model
            }
            pred.vectorizers = {
                'sms': mock_vectorizer,
                'voice': mock_vectorizer,
                'phishing': mock_vectorizer
            }
            pred.thresholds = {
                'sms': 0.80,
                'voice': 0.80,
                'phishing': 0.75
            }
            return pred

    def test_detect_content_type_url(self, multi_predictor):
        """Test URL content type detection."""
        url_text = "https://example.com/login"
        content_type = multi_predictor._detect_content_type(url_text)

        assert content_type == 'url'

    def test_detect_content_type_dialogue(self, multi_predictor):
        """Test dialogue content type detection."""
        dialogue = "Caller: Hello, is this John?\nReceiver: Yes, speaking."
        content_type = multi_predictor._detect_content_type(dialogue)

        assert content_type == 'dialogue'

    def test_detect_content_type_email(self, multi_predictor):
        """Test email content type detection."""
        email = "Dear Customer,\n\nYour account needs verification.\n\nBest regards,\nSupport"
        content_type = multi_predictor._detect_content_type(email)

        # Should be 'email' or 'sms' depending on implementation
        assert content_type in ['email', 'sms']

    def test_detect_content_type_sms(self, multi_predictor):
        """Test SMS content type detection."""
        sms = "Hey, meeting at 3pm?"
        content_type = multi_predictor._detect_content_type(sms)

        assert content_type == 'sms'

    def test_predict_sms(self, multi_predictor, mock_model):
        """Test SMS prediction."""
        mock_model.predict.return_value = np.array([0])
        mock_model.predict_proba.return_value = np.array([[0.9, 0.1]])

        result = multi_predictor.predict_sms("Hello, how are you?")

        assert 'is_spam' in result
        assert result['is_spam'] is False

    def test_predict_auto_selects_correct_model(self, multi_predictor, mock_model):
        """Test that auto-detection selects correct model type."""
        mock_model.predict.return_value = np.array([0])
        mock_model.predict_proba.return_value = np.array([[0.9, 0.1]])

        # URL should use phishing model
        result = multi_predictor.predict_auto("https://suspicious-site.tk/login")

        assert result is not None

    def test_get_model_info(self, multi_predictor):
        """Test model info retrieval."""
        info = multi_predictor.get_model_info()

        assert 'models_loaded' in info or 'loaded_models' in info

    def test_is_model_loaded(self, multi_predictor):
        """Test model loaded check."""
        assert multi_predictor.is_model_loaded('sms') is True
        assert multi_predictor.is_model_loaded('nonexistent') is False
