# AI/ML Service

Python FastAPI machine learning service for spam and phishing detection.

## Technology Stack

| Technology | Purpose |
|------------|---------|
| Python 3.9+ | Runtime |
| FastAPI | Web framework |
| scikit-learn | ML algorithms |
| Transformers | BERT models |
| SpeechRecognition | Voice processing |

## Quick Start

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r app/requirements.txt

# Prepare training data
python datasets/prepare_data.py

# Train model
python app/model/train.py

# Start server
python app/main.py
```

Server runs at `http://localhost:8000`

## Project Structure

```
app/
├── main.py               # FastAPI application entry
├── requirements.txt      # Python dependencies
├── api/                  # API endpoints
├── detectors/            # Threat detection modules
│   ├── phishing_detector.py
│   ├── advanced_threat_detector.py
│   ├── malware_detector.py
│   ├── intrusion_detector.py
│   └── voice_biometrics.py
├── model/                # ML models
│   ├── train.py          # Training pipeline
│   ├── predictor.py      # Inference logic
│   └── model_files/      # Trained model artifacts
├── models/               # Pydantic schemas
└── utils/                # Utility functions

datasets/
├── prepare_data.py       # Data preparation script
└── data_files/           # Training datasets
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/predict` | Predict spam for text |
| POST | `/predict-voice` | Analyze voice message |
| POST | `/batch-predict` | Batch text prediction |
| POST | `/phishing/detect` | Detect phishing |

## Usage Examples

### Text Prediction

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"message": "You won $1000000! Click here!"}'
```

Response:
```json
{
  "is_spam": true,
  "confidence": 0.95,
  "prediction": "SPAM",
  "features": {
    "urgency_score": 0.8,
    "suspicious_patterns": ["lottery", "click"]
  }
}
```

### Voice Analysis

```bash
curl -X POST http://localhost:8000/predict-voice \
  -F "audio=@message.wav"
```

### Batch Prediction

```bash
curl -X POST http://localhost:8000/batch-predict \
  -H "Content-Type: application/json" \
  -d '{"messages": ["Hello", "Win money now!", "Meeting at 3pm"]}'
```

## ML Models

| Model | Algorithm | Purpose |
|-------|-----------|---------|
| Text Classifier | Random Forest | Spam detection |
| Phishing Detector | BERT | Advanced phishing |
| URL Analyzer | Gradient Boosting | URL classification |

## Training

```bash
# Prepare dataset
python datasets/prepare_data.py

# Train models
python app/model/train.py

# Evaluate performance
python app/model/evaluate.py
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | 0.0.0.0 | Server host |
| `PORT` | 8000 | Server port |
| `MODEL_PATH` | app/model/model_files | Model directory |
| `LOG_LEVEL` | INFO | Logging level |

## Docker

```bash
# Build image
docker build -t antispam-ai .

# Run container
docker run -p 8000:8000 antispam-ai
```

## Documentation

- [System Architecture](../docs/architecture/SYSTEM_ARCHITECTURE.md)
- [Development Guide](../docs/development/DEVELOPMENT_GUIDE.md)
- [API Reference](../docs/api/API_REFERENCE.md)
