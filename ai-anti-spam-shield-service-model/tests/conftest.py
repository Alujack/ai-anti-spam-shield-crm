"""
Pytest configuration and fixtures for AI Anti-Spam Shield tests.
"""

import pytest
from unittest.mock import MagicMock, patch
import numpy as np
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


# Sample test messages
@pytest.fixture
def sample_spam_messages():
    """Sample spam messages for testing."""
    return [
        "URGENT: You've won $1,000,000! Click here to claim your prize NOW!",
        "Your account has been suspended. Verify immediately: http://fake-bank.com/verify",
        "Congratulations! You're the lucky winner! Call 1-800-SCAM now!",
        "FREE GIFT! Act now before it's too late! Limited time offer!",
        "You have been selected for a cash prize of $5000. Send your bank details.",
    ]


@pytest.fixture
def sample_ham_messages():
    """Sample legitimate messages for testing."""
    return [
        "Hi, how are you doing today?",
        "Meeting scheduled for tomorrow at 3pm",
        "Thanks for your help with the project!",
        "Can you send me the report when you get a chance?",
        "Happy birthday! Hope you have a great day.",
    ]


@pytest.fixture
def sample_safe_greetings():
    """Sample safe greetings that should not be flagged."""
    return [
        "Hi",
        "Hello",
        "Hey there",
        "Good morning",
        "How are you?",
        "What's up",
        "Hi there!",
    ]


@pytest.fixture
def sample_phishing_texts():
    """Sample phishing texts for testing."""
    return [
        "URGENT: Your PayPal account has been limited. Click here to restore: http://paypa1.tk/verify",
        "Your Bank of America account needs verification. Enter your SSN: http://boa-secure.xyz",
        "Apple ID locked! Verify immediately: http://apple-id-verify.ml/login",
        "Netflix payment failed. Update now: http://netflix-billing.tk",
    ]


@pytest.fixture
def sample_urls():
    """Sample URLs for testing."""
    return {
        'safe': [
            'https://www.google.com',
            'https://github.com/user/repo',
            'https://www.amazon.com/product',
        ],
        'suspicious': [
            'http://192.168.1.1/login',
            'http://paypa1-secure.tk/verify',
            'http://example.xyz/free-money',
            'http://bit.ly/suspicious123',
        ]
    }


@pytest.fixture
def mock_model():
    """Create a mock ML model."""
    model = MagicMock()
    model.predict.return_value = np.array([0])
    model.predict_proba.return_value = np.array([[0.9, 0.1]])
    return model


@pytest.fixture
def mock_vectorizer():
    """Create a mock vectorizer."""
    vectorizer = MagicMock()
    # Create a mock sparse matrix-like object with toarray method
    transform_result = MagicMock()
    transform_result.toarray.return_value = np.array([[0.1] * 100])
    vectorizer.transform.return_value = transform_result
    return vectorizer


@pytest.fixture
def mock_spam_predictor(mock_model, mock_vectorizer):
    """Create a mock SpamPredictor with mocked model."""
    with patch('joblib.load') as mock_load:
        mock_load.side_effect = [mock_model, mock_vectorizer]

        # Import here to apply the mock
        from app.model.predictor import SpamPredictor
        predictor = SpamPredictor(model_dir='test_model')
        predictor.model = mock_model
        predictor.vectorizer = mock_vectorizer
        predictor.model_loaded = True

        return predictor


@pytest.fixture
def mock_phishing_detector():
    """Create a PhishingDetector with ML disabled for testing."""
    with patch('joblib.load'):
        from app.detectors.phishing_detector import PhishingDetector
        detector = PhishingDetector(model_dir='test_models', use_ml=False)
        return detector


# API Test Client
@pytest.fixture
def api_client():
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient

    # Mock the predictors before importing the app
    with patch('app.main.predictor') as mock_pred, \
         patch('app.main.phishing_detector') as mock_phish:

        mock_pred.predict.return_value = {
            'is_spam': False,
            'confidence': 0.95,
            'prediction': 'ham',
            'probability': 0.05,
            'probabilities': {'ham': 0.95, 'spam': 0.05},
            'details': {}
        }

        mock_phish_result = MagicMock()
        mock_phish_result.to_dict.return_value = {
            'is_phishing': False,
            'confidence': 0.10,
            'threat_level': 'NONE',
            'indicators': [],
            'urls_analyzed': [],
            'brand_impersonation': None,
            'recommendation': 'Safe',
            'details': {}
        }
        mock_phish.detect.return_value = mock_phish_result

        from app.main import app
        yield TestClient(app)
