"""
Integration tests for FastAPI endpoints.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

# Add app directory to path so that relative imports in main.py work
app_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)


def get_test_client_with_mocks(predictor_mock=None, phishing_mock=None, multi_mock=None):
    """Create test client with mocked dependencies."""
    # Import main after setting up path - this triggers internal imports
    # which use relative imports from the app directory
    from main import app, predictor, phishing_detector, multi_predictor

    # Set up default mocks
    if predictor_mock:
        for key, value in predictor_mock.items():
            setattr(predictor, key, value) if hasattr(predictor, key) else None

    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client with mocked predictors."""
        from main import app
        yield TestClient(app)

    def test_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert 'status' in data

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200


class TestPredictionEndpoints:
    """Tests for spam prediction endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client with mocked predictor."""
        with patch('main.predictor') as mock_pred:
            mock_pred.predict.return_value = {
                'is_spam': False,
                'confidence': 0.95,
                'prediction': 'ham',
                'probability': 0.05,
                'probabilities': {'ham': 0.95, 'spam': 0.05},
                'details': {},
                'is_safe': True,
                'risk_level': 'NONE',
                'danger_causes': []
            }
            mock_pred.batch_predict.return_value = [
                {'is_spam': False, 'confidence': 0.95},
                {'is_spam': True, 'confidence': 0.85}
            ]
            mock_pred.model_loaded = True

            from main import app
            yield TestClient(app)

    def test_predict_endpoint(self, client):
        """Test text prediction endpoint."""
        response = client.post("/predict", json={"message": "Hello world"})

        assert response.status_code == 200
        data = response.json()
        assert 'is_spam' in data
        assert 'confidence' in data

    def test_predict_empty_message_rejected(self, client):
        """Test that empty message is rejected."""
        response = client.post("/predict", json={"message": ""})

        # Should return validation error
        assert response.status_code in [400, 422]

    def test_predict_missing_message(self, client):
        """Test that missing message field is rejected."""
        response = client.post("/predict", json={})

        assert response.status_code == 422

    def test_batch_predict_endpoint(self, client):
        """Test batch prediction endpoint."""
        response = client.post("/batch-predict", json={
            "messages": ["Hello", "URGENT: Click here!"]
        })

        assert response.status_code == 200
        data = response.json()
        assert 'predictions' in data
        assert len(data['predictions']) == 2

    def test_batch_predict_empty_list(self, client):
        """Test batch prediction with empty list."""
        response = client.post("/batch-predict", json={"messages": []})

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]


class TestPhishingEndpoints:
    """Tests for phishing detection endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client with mocked phishing detector."""
        with patch('main.phishing_detector') as mock_phish:
            mock_result = MagicMock()
            mock_result.is_phishing = False
            mock_result.confidence = 0.10
            mock_result.threat_level = MagicMock()
            mock_result.threat_level.value = 'NONE'
            mock_result.phishing_type = MagicMock()
            mock_result.phishing_type.value = 'NONE'
            mock_result.indicators = []
            mock_result.urls_analyzed = []
            mock_result.brand_impersonation = None
            mock_result.recommendation = 'Safe message'
            mock_result.details = {}

            mock_result.to_dict.return_value = {
                'is_phishing': False,
                'confidence': 0.10,
                'threat_level': 'NONE',
                'phishing_type': 'NONE',
                'indicators': [],
                'urls_analyzed': [],
                'brand_impersonation': None,
                'recommendation': 'Safe message',
                'details': {}
            }

            mock_phish.detect.return_value = mock_result
            mock_phish.model_loaded = True

            from main import app
            yield TestClient(app)

    def test_phishing_scan_endpoint(self, client):
        """Test phishing detection endpoint."""
        response = client.post("/predict-phishing", json={
            "text": "Hello, how are you?",
            "scan_type": "auto"
        })

        assert response.status_code == 200
        data = response.json()
        assert 'is_phishing' in data

    def test_phishing_scan_with_type(self, client):
        """Test phishing detection with specific scan type."""
        response = client.post("/predict-phishing", json={
            "text": "Your account needs verification",
            "scan_type": "email"
        })

        assert response.status_code == 200

    def test_url_scan_endpoint(self, client):
        """Test URL scanning endpoint."""
        response = client.post("/scan-url", json={
            "url": "https://www.google.com"
        })

        # May return 200 or 503 depending on detector status
        assert response.status_code in [200, 503]


class TestModelVersionEndpoints:
    """Tests for model version endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        with patch('main.predictor') as mock_pred, \
             patch('main.multi_predictor') as mock_multi:

            mock_pred.model_loaded = True
            mock_multi.get_model_info.return_value = {
                'models': ['sms', 'voice', 'phishing']
            }

            from main import app
            yield TestClient(app)

    def test_model_versions_endpoint(self, client):
        """Test model versions endpoint."""
        response = client.get("/model/versions")

        assert response.status_code == 200
        data = response.json()
        assert 'versions' in data or 'models' in data


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def client(self):
        """Create test client with error-producing predictor."""
        with patch('main.predictor') as mock_pred:
            mock_pred.predict.side_effect = Exception("Model error")
            mock_pred.model_loaded = False

            from main import app
            yield TestClient(app)

    def test_prediction_error_handling(self, client):
        """Test that prediction errors are handled gracefully."""
        response = client.post("/predict", json={"message": "Test"})

        # Should return error status, not crash
        assert response.status_code in [500, 503]

    def test_invalid_json_handling(self, client):
        """Test invalid JSON handling."""
        response = client.post(
            "/predict",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422


class TestInputValidation:
    """Tests for input validation."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        with patch('main.predictor') as mock_pred:
            mock_pred.predict.return_value = {
                'is_spam': False,
                'confidence': 0.9,
                'prediction': 'ham',
                'probability': 0.1,
                'probabilities': {'ham': 0.9, 'spam': 0.1},
                'details': {},
                'is_safe': True,
                'risk_level': 'NONE',
                'danger_causes': []
            }
            mock_pred.model_loaded = True

            from main import app
            yield TestClient(app)

    def test_very_long_message(self, client):
        """Test handling of very long messages."""
        long_message = "test " * 10000
        response = client.post("/predict", json={"message": long_message})

        # Should handle gracefully (either process or reject)
        assert response.status_code in [200, 400, 413, 422]

    def test_special_characters(self, client):
        """Test handling of special characters."""
        response = client.post("/predict", json={
            "message": "Test with unicode: \u00e9\u00e8\u00ea"
        })

        assert response.status_code == 200

    def test_whitespace_only_message(self, client):
        """Test handling of whitespace-only message."""
        response = client.post("/predict", json={"message": "   "})

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]
