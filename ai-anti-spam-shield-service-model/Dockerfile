FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    portaudio19-dev \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY app/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium and its OS-level dependencies. Required for
# the dynamic URL analysis ("safe lab" detonation in intel/screenshot_analyzer.py)
# — opens the URL in a headless browser, screenshots it, and inspects DOM for
# login forms / brand impersonation.
RUN playwright install --with-deps chromium

# Download NLTK data
RUN python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('punkt_tab')"

# Copy application code
COPY app/ .

# Create model directory
RUN mkdir -p model models model/trained_models

# Build argument to control whether to train models
# Set to "true" to train during build (CD deployment)
# Set to "false" to skip training (CI builds, quick rebuilds)
ARG TRAIN_MODELS=true

# Train the spam classifier model during build
# This downloads datasets from HuggingFace and trains the model
RUN if [ "$TRAIN_MODELS" = "true" ]; then \
      echo "Training spam classifier model..." && \
      python model/train.py --unified && \
      echo "Model training completed!"; \
    else \
      echo "Skipping model training (TRAIN_MODELS=false)"; \
    fi

# Train the phishing detector model
RUN if [ "$TRAIN_MODELS" = "true" ]; then \
      echo "Training phishing detector model..." && \
      (python model/train_phishing.py || echo "Phishing model training skipped (optional)"); \
    else \
      echo "Skipping phishing model training (TRAIN_MODELS=false)"; \
    fi

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use entrypoint script
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
