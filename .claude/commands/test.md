# Test Command

Run tests for the AI Anti-Spam Shield project.

## Arguments

- `--unit` - Run only unit tests
- `--integration` - Run only integration tests
- `--ui` - Run only UI/widget tests (Flutter)
- `--backend` - Run only backend tests
- `--model` - Run only AI model service tests
- `--mobile` - Run only mobile app tests
- `--coverage` - Generate coverage reports
- (no args) - Run all tests

## Instructions

Parse the arguments provided: $ARGUMENTS

### Setup Check

Before running tests, ensure dependencies are installed:

**Backend:**
```bash
cd /opt/school-project/ai-anti-spam-shield/ai-anti-spam-shield-backend
npm install --save-dev jest supertest jest-mock-extended nock 2>/dev/null || true
```

**AI Model Service:**
```bash
source /opt/school-project/ai-anti-spam-shield/.venv/bin/activate 2>/dev/null || true
pip install pytest pytest-asyncio pytest-cov pytest-mock -q 2>/dev/null || true
```

**Mobile:**
```bash
cd /opt/school-project/ai-anti-spam-shield/ai_anti_spam_shield_mobile
flutter pub get 2>/dev/null || true
```

### Test Execution Logic

Based on the arguments, run the appropriate tests:

---

## If `--unit` is specified (or no specific type):

### Backend Unit Tests
```bash
cd /opt/school-project/ai-anti-spam-shield/ai-anti-spam-shield-backend
npm run test:unit 2>/dev/null || npm test -- --testPathPattern=tests/unit
```

### AI Model Service Unit Tests
```bash
cd /opt/school-project/ai-anti-spam-shield/ai-anti-spam-shield-service-model
source /opt/school-project/ai-anti-spam-shield/.venv/bin/activate
pytest tests/unit/ -v
```

### Mobile Unit Tests
```bash
cd /opt/school-project/ai-anti-spam-shield/ai_anti_spam_shield_mobile
flutter test test/unit/
```

---

## If `--integration` is specified (or no specific type):

### Backend Integration Tests
```bash
cd /opt/school-project/ai-anti-spam-shield/ai-anti-spam-shield-backend
npm run test:integration 2>/dev/null || npm test -- --testPathPattern=tests/integration
```

### AI Model Service Integration Tests
```bash
cd /opt/school-project/ai-anti-spam-shield/ai-anti-spam-shield-service-model
source /opt/school-project/ai-anti-spam-shield/.venv/bin/activate
pytest tests/integration/ -v
```

### Mobile Integration Tests
```bash
cd /opt/school-project/ai-anti-spam-shield/ai_anti_spam_shield_mobile
flutter test test/integration/
```

---

## If `--ui` is specified (or no specific type):

### Mobile Widget/UI Tests
```bash
cd /opt/school-project/ai-anti-spam-shield/ai_anti_spam_shield_mobile
flutter test test/widget/
flutter test test/widget_test.dart
```

---

## If `--backend` is specified:

Run all backend tests:
```bash
cd /opt/school-project/ai-anti-spam-shield/ai-anti-spam-shield-backend
npm test
```

---

## If `--model` is specified:

Run all AI model service tests:
```bash
cd /opt/school-project/ai-anti-spam-shield/ai-anti-spam-shield-service-model
source /opt/school-project/ai-anti-spam-shield/.venv/bin/activate
pytest tests/ -v
```

---

## If `--mobile` is specified:

Run all mobile app tests:
```bash
cd /opt/school-project/ai-anti-spam-shield/ai_anti_spam_shield_mobile
flutter test
```

---

## If `--coverage` is specified:

### Backend with Coverage
```bash
cd /opt/school-project/ai-anti-spam-shield/ai-anti-spam-shield-backend
npm run test:coverage 2>/dev/null || npm test -- --coverage
```

### AI Model Service with Coverage
```bash
cd /opt/school-project/ai-anti-spam-shield/ai-anti-spam-shield-service-model
source /opt/school-project/ai-anti-spam-shield/.venv/bin/activate
pytest tests/ --cov=app --cov-report=term-missing --cov-report=html
```

### Mobile with Coverage
```bash
cd /opt/school-project/ai-anti-spam-shield/ai_anti_spam_shield_mobile
flutter test --coverage
```

---

## If no arguments are provided:

Run ALL tests across all components:

1. **Backend Tests:**
```bash
cd /opt/school-project/ai-anti-spam-shield/ai-anti-spam-shield-backend
npm test
```

2. **AI Model Service Tests:**
```bash
cd /opt/school-project/ai-anti-spam-shield/ai-anti-spam-shield-service-model
source /opt/school-project/ai-anti-spam-shield/.venv/bin/activate
pytest tests/ -v
```

3. **Mobile Tests:**
```bash
cd /opt/school-project/ai-anti-spam-shield/ai_anti_spam_shield_mobile
flutter test
```

---

## Test Summary

After running tests, provide a summary:

| Component | Unit | Integration | UI/Widget | Status |
|-----------|------|-------------|-----------|--------|
| Backend   | ✓/✗  | ✓/✗         | N/A       | Pass/Fail |
| AI Model  | ✓/✗  | ✓/✗         | N/A       | Pass/Fail |
| Mobile    | ✓/✗  | ✓/✗         | ✓/✗       | Pass/Fail |

## Test File Locations

**Backend:**
- Unit: `ai-anti-spam-shield-backend/tests/unit/`
- Integration: `ai-anti-spam-shield-backend/tests/integration/`

**AI Model Service:**
- Unit: `ai-anti-spam-shield-service-model/tests/unit/`
- Integration: `ai-anti-spam-shield-service-model/tests/integration/`

**Mobile:**
- Unit: `ai_anti_spam_shield_mobile/test/unit/`
- Widget: `ai_anti_spam_shield_mobile/test/widget/`
- Integration: `ai_anti_spam_shield_mobile/test/integration/`

## Notes

- Backend tests use Jest with Supertest for HTTP testing
- AI Model tests use pytest with pytest-asyncio for async support
- Mobile tests use Flutter's built-in test framework with mocktail for mocking
- Coverage reports are generated in each component's directory
- Some tests may require services to be running (check test mocks)
