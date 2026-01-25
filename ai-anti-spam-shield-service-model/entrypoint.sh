#!/bin/bash
set -e

echo "🚀 Starting AI Anti-Spam Shield ML Service..."

# Check if spam classifier model exists
if [ ! -f "/app/model/spam_classifier.pkl" ]; then
    echo "⚠️  Spam classifier model not found. Training model..."
    cd /app
    python model/train.py --unified
    echo "✅ Spam classifier model trained successfully!"
else
    echo "✅ Spam classifier model found."
fi

# Check if phishing detector model exists (optional)
if [ ! -f "/app/models/phishing_detector.pkl" ]; then
    echo "⚠️  Phishing detector model not found. Training model..."
    cd /app
    python model/train_phishing.py || echo "⚠️  Phishing model training skipped (non-critical)"
else
    echo "✅ Phishing detector model found."
fi

echo "🎯 All models ready. Starting FastAPI server..."

# Execute the main command
exec "$@"
