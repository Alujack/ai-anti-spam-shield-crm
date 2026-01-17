# Development Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Project Structure](#project-structure)
3. [Backend Development](#backend-development)
4. [AI Service Development](#ai-service-development)
5. [Mobile App Development](#mobile-app-development)
6. [Testing](#testing)
7. [Code Style](#code-style)
8. [Git Workflow](#git-workflow)

---

## Getting Started

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd ai-anti-spam-shield

# Install all dependencies
./scripts/setup.sh
# Or manually:
cd ai-anti-spam-shield-backend && yarn install
cd ../ai-anti-spam-shield-service-model && pip install -r app/requirements.txt
cd ../ai_anti_spam_shield_mobile && flutter pub get
```

### IDE Setup

**Recommended Extensions:**

| IDE | Extensions |
|-----|------------|
| VS Code | ESLint, Prettier, Python, Flutter, Prisma |
| IntelliJ | Node.js, Python, Flutter, Database Tools |

---

## Project Structure

```
ai-anti-spam-shield/
├── ai-anti-spam-shield-backend/     # Node.js Backend
│   ├── src/
│   │   ├── app.js                   # Entry point
│   │   ├── api/                     # API version routing
│   │   ├── config/                  # Configuration
│   │   ├── controllers/             # Request handlers
│   │   ├── middlewares/             # Express middlewares
│   │   ├── routes/                  # Route definitions
│   │   ├── services/                # Business logic
│   │   └── utils/                   # Utilities
│   ├── prisma/                      # Database schema
│   └── tests/                       # Test files
│
├── ai-anti-spam-shield-service-model/  # Python ML Service
│   ├── app/
│   │   ├── main.py                  # FastAPI entry
│   │   ├── api/                     # API endpoints
│   │   ├── detectors/               # Threat detectors
│   │   ├── model/                   # ML models
│   │   ├── models/                  # Pydantic schemas
│   │   └── utils/                   # Utilities
│   ├── datasets/                    # Training data
│   └── tests/                       # Test files
│
├── ai_anti_spam_shield_mobile/      # Flutter App
│   ├── lib/
│   │   ├── main.dart                # Entry point
│   │   ├── screens/                 # UI screens
│   │   ├── providers/               # State management
│   │   ├── services/                # API services
│   │   ├── models/                  # Data models
│   │   ├── widgets/                 # UI components
│   │   └── utils/                   # Utilities
│   └── test/                        # Test files
│
└── docs/                            # Documentation
```

---

## Backend Development

### Adding a New Endpoint

#### 1. Create Controller

```javascript
// src/controllers/example.controller.js
const asyncHandler = require('../utils/asyncHandler');
const exampleService = require('../services/example.service');

exports.getExample = asyncHandler(async (req, res) => {
  const result = await exampleService.getExample(req.params.id);

  res.status(200).json({
    status: 'success',
    message: 'Example retrieved',
    data: result
  });
});

exports.createExample = asyncHandler(async (req, res) => {
  const result = await exampleService.createExample(req.body);

  res.status(201).json({
    status: 'success',
    message: 'Example created',
    data: result
  });
});
```

#### 2. Create Service

```javascript
// src/services/example.service.js
const { PrismaClient } = require('@prisma/client');
const ApiError = require('../utils/apiError');

const prisma = new PrismaClient();

exports.getExample = async (id) => {
  const example = await prisma.example.findUnique({
    where: { id }
  });

  if (!example) {
    throw new ApiError(404, 'Example not found');
  }

  return example;
};

exports.createExample = async (data) => {
  return await prisma.example.create({
    data
  });
};
```

#### 3. Create Routes

```javascript
// src/routes/example.routes.js
const express = require('express');
const router = express.Router();
const exampleController = require('../controllers/example.controller');
const { authenticate } = require('../middlewares/auth');

router.get('/:id', authenticate, exampleController.getExample);
router.post('/', authenticate, exampleController.createExample);

module.exports = router;
```

#### 4. Register Routes

```javascript
// src/routes/index.js
const exampleRoutes = require('./example.routes');

router.use('/examples', exampleRoutes);
```

### Database Migrations

```bash
# Create migration
yarn prisma migrate dev --name add_example_table

# Apply migrations
yarn prisma migrate deploy

# Reset database
yarn prisma migrate reset

# Open Prisma Studio
yarn prisma studio
```

### Middleware Pattern

```javascript
// src/middlewares/validate.js
const ApiError = require('../utils/apiError');

const validate = (schema) => (req, res, next) => {
  const { error } = schema.validate(req.body);

  if (error) {
    throw new ApiError(400, error.details[0].message);
  }

  next();
};

module.exports = validate;
```

---

## AI Service Development

### Adding a New Detector

#### 1. Create Detector Class

```python
# app/detectors/new_detector.py
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class NewDetector:
    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the detection model."""
        # Load model logic here
        logger.info("NewDetector model loaded")

    def detect(self, text: str) -> Dict[str, Any]:
        """
        Detect threats in text.

        Args:
            text: Input text to analyze

        Returns:
            Detection result with confidence and indicators
        """
        # Detection logic here
        return {
            "detected": False,
            "confidence": 0.0,
            "indicators": []
        }
```

#### 2. Create API Endpoint

```python
# app/api/new_endpoint.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..detectors.new_detector import NewDetector

router = APIRouter()
detector = NewDetector()

class DetectionRequest(BaseModel):
    text: str

class DetectionResponse(BaseModel):
    detected: bool
    confidence: float
    indicators: list

@router.post("/detect-new", response_model=DetectionResponse)
async def detect_new(request: DetectionRequest):
    """Detect new threat type."""
    try:
        result = detector.detect(request.text)
        return DetectionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### 3. Register Router

```python
# app/main.py
from .api.new_endpoint import router as new_router

app.include_router(new_router, prefix="/api", tags=["new-detection"])
```

### Training New Models

```python
# datasets/train_new_model.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib

def train_model():
    # Load data
    df = pd.read_csv('data/training_data.csv')

    # Prepare features
    X = df['features']
    y = df['label']

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Train model
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X_train, y_train)

    # Evaluate
    accuracy = model.score(X_test, y_test)
    print(f"Model accuracy: {accuracy:.2f}")

    # Save model
    joblib.dump(model, 'app/model/model_files/new_model.joblib')

if __name__ == "__main__":
    train_model()
```

---

## Mobile App Development

### Adding a New Screen

#### 1. Create Screen Widget

```dart
// lib/screens/new_feature/new_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class NewScreen extends ConsumerStatefulWidget {
  const NewScreen({super.key});

  @override
  ConsumerState<NewScreen> createState() => _NewScreenState();
}

class _NewScreenState extends ConsumerState<NewScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('New Feature'),
      ),
      body: Center(
        child: const Text('New Screen Content'),
      ),
    );
  }
}
```

#### 2. Add Route

```dart
// lib/main.dart
import 'screens/new_feature/new_screen.dart';

// Add to routes
'/new-feature': (context) => const NewScreen(),
```

### State Management with Riverpod

```dart
// lib/providers/new_provider.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';

class NewState {
  final bool isLoading;
  final String? data;
  final String? error;

  NewState({
    this.isLoading = false,
    this.data,
    this.error,
  });

  NewState copyWith({
    bool? isLoading,
    String? data,
    String? error,
  }) {
    return NewState(
      isLoading: isLoading ?? this.isLoading,
      data: data ?? this.data,
      error: error ?? this.error,
    );
  }
}

class NewNotifier extends StateNotifier<NewState> {
  NewNotifier() : super(NewState());

  Future<void> fetchData() async {
    state = state.copyWith(isLoading: true);
    try {
      // Fetch data logic
      state = state.copyWith(isLoading: false, data: 'Result');
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }
}

final newProvider = StateNotifierProvider<NewNotifier, NewState>((ref) {
  return NewNotifier();
});
```

### API Service Pattern

```dart
// lib/services/new_service.dart
import 'package:dio/dio.dart';
import '../utils/constants.dart';

class NewService {
  final Dio _dio;

  NewService() : _dio = Dio(BaseOptions(
    baseUrl: ApiConstants.baseUrl,
    connectTimeout: const Duration(seconds: 30),
    receiveTimeout: const Duration(seconds: 30),
  ));

  Future<Map<String, dynamic>> fetchData(String id) async {
    try {
      final response = await _dio.get('/new-endpoint/$id');
      return response.data;
    } on DioException catch (e) {
      throw Exception('Failed to fetch data: ${e.message}');
    }
  }
}
```

---

## Testing

### Backend Tests

```bash
# Run all tests
yarn test

# Run with coverage
yarn test:coverage

# Run specific test
yarn test -- --grep "should create user"
```

```javascript
// tests/user.test.js
const request = require('supertest');
const app = require('../src/app');

describe('User API', () => {
  describe('POST /api/v1/users/register', () => {
    it('should register a new user', async () => {
      const response = await request(app)
        .post('/api/v1/users/register')
        .send({
          email: 'test@example.com',
          password: 'password123',
          name: 'Test User'
        });

      expect(response.status).toBe(201);
      expect(response.body.status).toBe('success');
    });
  });
});
```

### AI Service Tests

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test
pytest tests/test_predictor.py
```

```python
# tests/test_predictor.py
import pytest
from app.model.predictor import SpamPredictor

class TestSpamPredictor:
    @pytest.fixture
    def predictor(self):
        return SpamPredictor()

    def test_predict_spam(self, predictor):
        result = predictor.predict("You won $1000000!")
        assert result['is_spam'] is True
        assert result['confidence'] > 0.5

    def test_predict_ham(self, predictor):
        result = predictor.predict("Hello, how are you?")
        assert result['is_spam'] is False
```

### Mobile Tests

```bash
# Run unit tests
flutter test

# Run widget tests
flutter test test/widget_test.dart

# Run integration tests
flutter test integration_test/
```

```dart
// test/providers/scan_provider_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_anti_spam_shield_mobile/providers/scan_provider.dart';

void main() {
  group('ScanProvider', () {
    test('initial state should be idle', () {
      final notifier = ScanNotifier();
      expect(notifier.state.isScanning, false);
    });
  });
}
```

---

## Code Style

### JavaScript/TypeScript

```javascript
// Use const/let, not var
const data = fetchData();

// Use async/await
async function getData() {
  const result = await fetch('/api/data');
  return result.json();
}

// Use destructuring
const { name, email } = user;

// Use template literals
const message = `Hello, ${name}!`;
```

### Python

```python
# Follow PEP 8
def calculate_score(text: str) -> float:
    """Calculate spam score for text."""
    pass

# Use type hints
from typing import List, Dict, Optional

def process_items(items: List[str]) -> Dict[str, int]:
    pass

# Use f-strings
name = "World"
message = f"Hello, {name}!"
```

### Dart/Flutter

```dart
// Use const constructors
const Widget myWidget = Text('Hello');

// Use named parameters
void createUser({
  required String name,
  required String email,
  String? phone,
}) {}

// Use null safety
String? maybeNull;
String definitelyNotNull = maybeNull ?? 'default';
```

---

## Git Workflow

### Branch Naming

```
feature/add-voice-scanning
bugfix/fix-login-error
hotfix/security-patch
refactor/improve-performance
docs/update-readme
```

### Commit Messages

```
feat: add voice message scanning
fix: resolve login authentication issue
docs: update API documentation
refactor: improve error handling
test: add unit tests for predictor
chore: update dependencies
```

### Pull Request Process

1. Create feature branch from `main`
2. Make changes and commit
3. Push branch and create PR
4. Request review
5. Address feedback
6. Merge after approval

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/new-feature
```
