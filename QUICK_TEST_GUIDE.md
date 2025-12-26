# 🚀 Quick Testing Guide

## iOS Issue - FIXED! ✅

The iOS deployment target issue has been resolved. Your iOS pods are now properly configured with iOS 13.0 as the minimum deployment target.

## Testing the Backend & AI Model

### Step 1: Install & Run AI Service

Open a **new terminal** and run:

```bash
cd /opt/school-project/ai-anti-spam-shield/ai-anti-spam-shield-service-model

# Activate virtual environment
source venv/bin/activate

# Install dependencies (this will take 5-10 minutes)
pip install fastapi uvicorn pydantic python-multipart scikit-learn pandas numpy joblib nltk SpeechRecognition pydub

# Prepare dataset
python datasets/prepare_data.py

# Train model
python app/model/train.py

# Run AI service
python app/main.py
```

Expected output:
```
✅ Spam predictor initialized successfully!
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Run Backend API

Open **another terminal** and run:

```bash
cd /opt/school-project/ai-anti-spam-shield/ai-anti-spam-shield-backend

# Install dependencies (if not done yet)
yarn install

# OR if yarn not installed
npm install

# Start backend
yarn dev
# OR
npm run dev
```

Expected output:
```
[INFO] Server running on port 3000
```

### Step 3: Test the APIs

Open a **third terminal** and test:

```bash
# Test AI Service Health
curl http://localhost:8000/health

# Test Backend Health
curl http://localhost:3000/health

# Test Text Scanning
curl -X POST http://localhost:3000/api/v1/messages/scan-text \
  -H "Content-Type: application/json" \
  -d '{
    "message": "URGENT! You have won $1000. Click here to claim your prize immediately!"
  }'

# Expected Response:
# {
#   "status": "success",
#   "message": "Message scanned successfully",
#   "data": {
#     "is_spam": true,
#     "confidence": 0.95,
#     "prediction": "spam",
#     ...
#   }
# }
```

### Step 4: Run Mobile App

Once both services are running:

```bash
cd /opt/school-project/ai-anti-spam-shield/ai_anti_spam_shield_mobile

# Get dependencies
flutter pub get

# Run on iOS
flutter run

# OR run on Android
flutter run
```

**Before running the mobile app**, update the API base URL in:
`lib/utils/constants.dart`:

```dart
// For iOS Simulator
static const String baseUrl = 'http://localhost:3000/api/v1';

// For Android Emulator
static const String baseUrl = 'http://10.0.2.2:3000/api/v1';

// For Physical Device (replace with your computer's IP)
static const String baseUrl = 'http://192.168.1.XXX:3000/api/v1';
```

## Quick Alternative (Skip Heavy ML Libraries)

If the ML libraries take too long to install, you can create a simple mock AI service for testing:

Create `ai-anti-spam-shield-service-model/app/mock_main.py`:

```python
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI()

class PredictionRequest(BaseModel):
    message: str

@app.get("/health")
async def health():
    return {"status": "healthy", "model_loaded": True}

@app.post("/predict")
async def predict(request: PredictionRequest):
    # Simple keyword-based mock
    spam_keywords = ['urgent', 'win', 'prize', 'click', 'free', '$', 'claim']
    is_spam = any(keyword in request.message.lower() for keyword in spam_keywords)
    
    return {
        "is_spam": is_spam,
        "prediction": "spam" if is_spam else "ham",
        "confidence": 0.95 if is_spam else 0.85,
        "probability": 0.95 if is_spam else 0.15,
        "probabilities": {
            "ham": 0.05 if is_spam else 0.85,
            "spam": 0.95 if is_spam else 0.15
        },
        "details": {"features": {}},
        "timestamp": "2025-12-05T00:00:00"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Then run:
```bash
cd ai-anti-spam-shield-service-model
pip install fastapi uvicorn pydantic
python app/mock_main.py
```

This will let you test the full system without waiting for heavy ML libraries!

## Troubleshooting

**Port already in use:**
```bash
# Find and kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

**Database connection error:**
```bash
# Create database
createdb antispam_db

# Run migrations
cd ai-anti-spam-shield-backend
yarn prisma:migrate
```

**Flutter can't connect:**
- Make sure backend is running on port 3000
- Check firewall settings
- Use correct IP address for physical devices

## Next Steps

Once everything is running:
1. ✅ Register a user in the mobile app
2. ✅ Login
3. ✅ Scan a test message
4. ✅ View results
5. ✅ Check scan history
6. ✅ Test settings

**Everything is ready to go!** 🎉

