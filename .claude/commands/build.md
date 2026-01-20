# Build Command

Build and start the AI Anti-Spam Shield services (ML model and backend server).

## Instructions

Follow these steps to build and run the project:

### Step 1: Check and Setup Python Virtual Environment

Check if the Python virtual environment exists at `/opt/school-project/ai-anti-spam-shield/.venv`. If not, create it and install dependencies:

```bash
# Create venv if needed
python3 -m venv /opt/school-project/ai-anti-spam-shield/.venv

# Activate and install dependencies
source /opt/school-project/ai-anti-spam-shield/.venv/bin/activate
pip install -r /opt/school-project/ai-anti-spam-shield/ai-anti-spam-shield-service-model/app/requirements.txt
```

### Step 2: Train the ML Model (if needed)

Check if the model file exists at `/opt/school-project/ai-anti-spam-shield/ai-anti-spam-shield-service-model/app/model/spam_classifier.pkl`.

If the model doesn't exist, train it using the unified training mode:

```bash
cd /opt/school-project/ai-anti-spam-shield/ai-anti-spam-shield-service-model/app
source /opt/school-project/ai-anti-spam-shield/.venv/bin/activate
python model/train.py --unified
```

This downloads and trains with:
- Deysi/spam-detection-dataset (SMS spam)
- BothBosu/scam-dialogue (Voice call scams)

### Step 3: Start the ML Model Service

Kill any existing process on port 8000, then start the FastAPI ML service:

```bash
# Kill existing process on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start ML service
cd /opt/school-project/ai-anti-spam-shield/ai-anti-spam-shield-service-model/app
source /opt/school-project/ai-anti-spam-shield/.venv/bin/activate
python main.py
```

Run this in the background so we can continue with the backend.

### Step 4: Setup Backend Dependencies

Check if `node_modules` exists in the backend directory. If not, install dependencies:

```bash
cd /opt/school-project/ai-anti-spam-shield/ai-anti-spam-shield-backend
yarn install
```

### Step 5: Setup Environment File

Check if `.env` exists. If not, copy from `.env.example`:

```bash
cd /opt/school-project/ai-anti-spam-shield/ai-anti-spam-shield-backend
cp .env.example .env
```

### Step 6: Start the Backend Server

Kill any existing process on port 3000, then start the Express backend:

```bash
# Kill existing process on port 3000
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Start backend
cd /opt/school-project/ai-anti-spam-shield/ai-anti-spam-shield-backend
yarn dev
```

### Step 7: Setup Flutter Mobile App (Optional)

If building the mobile app, ensure Flutter dependencies are installed:

```bash
cd /opt/school-project/ai-anti-spam-shield/ai_anti_spam_shield_mobile
flutter pub get
```

For iOS builds, set up the correct Xcode environment:

```bash
export DEVELOPER_DIR=/Applications/Xcode26.app/Contents/Developer
```

Run the app:

```bash
cd /opt/school-project/ai-anti-spam-shield/ai_anti_spam_shield_mobile
flutter run
```

Or use the startup script:

```bash
source /opt/school-project/ai-anti-spam-shield/ai_anti_spam_shield_mobile/mobile-startup.sh
flutter run
```

## Service Endpoints

After successful build:

**ML Model Service (Port 8000):**
- Health Check: http://localhost:8000/health
- API Docs: http://localhost:8000/docs
- Predict: POST http://localhost:8000/predict
- Phishing: POST http://localhost:8000/predict-phishing

**Backend Server (Port 3000):**
- Health Check: http://localhost:3000/health
- API Docs: http://localhost:3000/api-docs
- API Base: http://localhost:3000/api/v1
- WebSocket: ws://localhost:3000/ws

**Mobile App:**
- Connects to backend at configured API endpoint
- Uses WebSocket for real-time updates

## Notes

- The ML model training may take a few minutes on first run as it downloads datasets from Hugging Face
- Both services should be running for full functionality
- The backend connects to the ML service for spam/phishing predictions
- The mobile app requires the backend server to be running
- For iOS development, ensure Xcode 26 is properly configured
