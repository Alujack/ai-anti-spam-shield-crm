# Mobile Application

Cross-platform Flutter mobile app for AI Anti-Spam Shield.

## Technology Stack

| Technology | Purpose |
|------------|---------|
| Flutter 3.9+ | UI framework |
| Riverpod | State management |
| Dio | HTTP client |
| Record | Audio recording |

## Quick Start

```bash
# Install dependencies
flutter pub get

# Run on connected device
flutter run

# Build for specific platform
flutter build apk      # Android
flutter build ios      # iOS
flutter build web      # Web
```

## Project Structure

```
lib/
├── main.dart              # Application entry point
├── screens/               # UI screens
│   ├── auth/
│   │   ├── login_screen.dart
│   │   └── register_screen.dart
│   ├── home/
│   │   └── home_screen.dart
│   ├── result/
│   │   └── result_screen.dart
│   ├── history/
│   │   └── history_screen.dart
│   ├── settings/
│   │   └── settings_screen.dart
│   ├── phishing/
│   │   └── phishing_screen.dart
│   └── dashboard/
│       └── dashboard_screen.dart
├── providers/             # State management
│   ├── auth_provider.dart
│   ├── scan_provider.dart
│   └── history_provider.dart
├── services/              # API integration
│   └── api_service.dart
├── models/                # Data models
│   ├── user.dart
│   ├── scan_result.dart
│   └── history_item.dart
├── widgets/               # Reusable components
│   ├── scan_button.dart
│   ├── result_card.dart
│   └── history_tile.dart
└── utils/                 # Utilities
    ├── constants.dart
    ├── colors.dart
    └── helpers.dart
```

## Features

### Authentication
- User registration
- Login with email/password
- Profile management
- Secure token storage

### Message Scanning
- Text message input
- Voice recording
- Real-time analysis
- Confidence scores

### Scan History
- View past scans
- Filter by status
- Search functionality
- Detailed results

### Settings
- User preferences
- Notification settings
- Account management

## Screens

| Screen | Route | Description |
|--------|-------|-------------|
| Login | `/login` | User authentication |
| Register | `/register` | New user signup |
| Home | `/home` | Main scanning interface |
| Result | `/result` | Scan result display |
| History | `/history` | Past scans list |
| Settings | `/settings` | User preferences |
| Phishing | `/phishing` | Phishing detection |

## State Management

Using Riverpod for reactive state management:

```dart
// Provider definition
final scanProvider = StateNotifierProvider<ScanNotifier, ScanState>((ref) {
  return ScanNotifier();
});

// Usage in widget
class HomeScreen extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final scanState = ref.watch(scanProvider);
    // ...
  }
}
```

## API Integration

```dart
// API Service usage
final apiService = ApiService();

// Scan text
final result = await apiService.scanText('message to scan');

// Scan voice
final result = await apiService.scanVoice(audioFile);

// Get history
final history = await apiService.getHistory(page: 1);
```

## Configuration

Update API base URL in `lib/utils/constants.dart`:

```dart
class ApiConstants {
  static const String baseUrl = 'http://localhost:3000/api/v1';
}
```

## Build Commands

```bash
# Development
flutter run

# Release APK
flutter build apk --release

# iOS release
flutter build ios --release

# Web release
flutter build web --release

# Run tests
flutter test
```

## Permissions

### Android (`android/app/src/main/AndroidManifest.xml`)
```xml
<uses-permission android:name="android.permission.INTERNET"/>
<uses-permission android:name="android.permission.RECORD_AUDIO"/>
```

### iOS (`ios/Runner/Info.plist`)
```xml
<key>NSMicrophoneUsageDescription</key>
<string>Required for voice message scanning</string>
```

## Documentation

- [Development Guide](../docs/development/DEVELOPMENT_GUIDE.md)
- [Testing Guide](../docs/guides/TESTING_GUIDE.md)
