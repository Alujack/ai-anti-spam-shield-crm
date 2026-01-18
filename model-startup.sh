#!/bin/bash

# AI Anti-Spam Shield - ML Model Service Startup Script
# This script starts the Python FastAPI ML service

echo "=========================================="
echo "  AI Anti-Spam Shield - ML Model Service"
echo "=========================================="

# Configuration
PROJECT_ROOT="/opt/school-project/ai-anti-spam-shield"
SERVICE_DIR="$PROJECT_ROOT/ai-anti-spam-shield-service-model"
VENV_PATH="$PROJECT_ROOT/.venv"
HOST="0.0.0.0"
PORT=8000

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}Error: Virtual environment not found at $VENV_PATH${NC}"
    echo "Please create a virtual environment first:"
    echo "  python3 -m venv $VENV_PATH"
    echo "  source $VENV_PATH/bin/activate"
    echo "  pip install -r $SERVICE_DIR/app/requirements.txt"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Navigate to service directory
cd "$SERVICE_DIR/app" || {
    echo -e "${RED}Error: Could not navigate to $SERVICE_DIR/app${NC}"
    exit 1
}

# Check if model files exist, train if not
MODEL_FILE="$SERVICE_DIR/app/model/spam_classifier.pkl"
if [ ! -f "$MODEL_FILE" ]; then
    echo -e "${YELLOW}Model files not found. Training unified model with Hugging Face datasets...${NC}"
    echo "This will download and train with:"
    echo "  - Deysi/spam-detection-dataset (SMS spam)"
    echo "  - BothBosu/scam-dialogue (Voice call scams)"
    echo ""
    python model/train.py --unified
    echo ""
fi

# Kill any existing process on the port
if lsof -ti:$PORT > /dev/null 2>&1; then
    echo -e "${YELLOW}Killing existing process on port $PORT...${NC}"
    lsof -ti:$PORT | xargs kill -9 2>/dev/null
    sleep 1
fi

echo -e "${GREEN}Starting ML Model Service...${NC}"
echo "Host: $HOST"
echo "Port: $PORT"
echo "API Docs: http://localhost:$PORT/docs"
echo "Health Check: http://localhost:$PORT/health"
echo "=========================================="

# Start the server
python main.py
