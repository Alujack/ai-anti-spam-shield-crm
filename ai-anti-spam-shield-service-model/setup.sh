#!/bin/bash

echo "🚀 Setting up AI Anti-Spam Shield Service..."
echo "============================================="

# Configuration
PROJECT_ROOT="/opt/school-project/ai-anti-spam-shield"
VENV_PATH="$PROJECT_ROOT/.venv"
SERVICE_DIR="$PROJECT_ROOT/ai-anti-spam-shield-service-model"

# Create virtual environment in project root
if [ ! -d "$VENV_PATH" ]; then
    echo "📦 Creating virtual environment at $VENV_PATH..."
    python3 -m venv "$VENV_PATH"
else
    echo "📦 Virtual environment already exists at $VENV_PATH"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r "$SERVICE_DIR/app/requirements.txt"

# Train unified model with Hugging Face datasets
echo ""
echo "🎯 Training unified spam classification model..."
echo "   Using Hugging Face datasets:"
echo "   - Deysi/spam-detection-dataset (SMS spam)"
echo "   - BothBosu/scam-dialogue (Voice call scams)"
echo ""
cd "$SERVICE_DIR/app"
python3 model/train.py --unified

echo ""
echo "============================================="
echo "✅ Setup complete!"
echo ""
echo "To start the ML service:"
echo "  source $VENV_PATH/bin/activate"
echo "  cd $SERVICE_DIR/app"
echo "  python main.py"
echo ""
echo "Or use the startup script:"
echo "  ./model-startup.sh"
echo ""
echo "Training options:"
echo "  python model/train.py --unified              # Both SMS + Voice (recommended)"
echo "  python model/train.py --huggingface          # SMS spam only"
echo "  python model/train.py --scam-dialogue        # Voice scams only"
echo "  python model/train.py --unified random_forest # With different model"
echo "============================================="

