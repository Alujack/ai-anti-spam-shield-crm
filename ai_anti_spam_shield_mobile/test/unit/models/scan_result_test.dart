import 'package:flutter_test/flutter_test.dart';
import 'package:ai_anti_spam_shield_mobile/models/scan_result.dart';

void main() {
  group('ScanResult', () {
    group('fromJson', () {
      test('creates correct instance from JSON', () {
        final json = {
          'is_spam': true,
          'confidence': 0.85,
          'prediction': 'spam',
          'message': 'Test message',
          'timestamp': '2024-01-01T00:00:00Z',
          'is_safe': false,
          'risk_level': 'HIGH',
          'danger_causes': [
            {
              'type': 'urgency',
              'title': 'Urgency Detected',
              'description': 'Message contains urgent language',
              'severity': 'high',
            }
          ],
        };

        final result = ScanResult.fromJson(json);

        expect(result.isSpam, true);
        expect(result.confidence, 0.85);
        expect(result.prediction, 'spam');
        expect(result.isSafe, false);
        expect(result.riskLevel, 'HIGH');
        expect(result.dangerCauses.length, 1);
      });

      test('handles missing optional fields', () {
        final json = {
          'is_spam': false,
          'confidence': 0.9,
          'prediction': 'ham',
          'message': 'Hello',
          'timestamp': '2024-01-01T00:00:00Z',
        };

        final result = ScanResult.fromJson(json);

        expect(result.isSpam, false);
        expect(result.isSafe, true);
        expect(result.dangerCauses, isEmpty);
      });

      test('parses voice scan correctly', () {
        final json = {
          'is_spam': false,
          'confidence': 0.88,
          'prediction': 'ham',
          'message': '',
          'timestamp': '2024-01-01T00:00:00Z',
          'transcribed_text': 'Hello, this is a voice message',
        };

        final result = ScanResult.fromJson(json);

        expect(result.isVoiceScan, true);
        expect(result.transcribedText, 'Hello, this is a voice message');
      });

      test('handles null confidence', () {
        final json = {
          'is_spam': false,
          'prediction': 'ham',
          'message': 'Test',
          'timestamp': '2024-01-01T00:00:00Z',
        };

        final result = ScanResult.fromJson(json);

        expect(result.confidence, 0.0);
      });
    });

    group('toJson', () {
      test('serializes correctly', () {
        final result = ScanResult(
          isSpam: true,
          confidence: 0.9,
          prediction: 'spam',
          message: 'test message',
          timestamp: '2024-01-01T00:00:00Z',
        );

        final json = result.toJson();

        expect(json['is_spam'], true);
        expect(json['confidence'], 0.9);
        expect(json['message'], 'test message');
      });

      test('includes danger causes in JSON', () {
        final result = ScanResult(
          isSpam: true,
          confidence: 0.9,
          prediction: 'spam',
          message: 'test',
          timestamp: '2024-01-01T00:00:00Z',
          dangerCauses: [
            DangerCause(
              type: 'test',
              title: 'Test',
              description: 'Test desc',
              severity: 'high',
            ),
          ],
        );

        final json = result.toJson();

        expect(json['danger_causes'], isA<List>());
        expect((json['danger_causes'] as List).length, 1);
      });
    });

    group('confidencePercentage', () {
      test('returns formatted percentage string', () {
        final result = ScanResult(
          isSpam: false,
          confidence: 0.856,
          prediction: 'ham',
          message: 'test',
          timestamp: '',
        );

        expect(result.confidencePercentage, '85.6%');
      });

      test('handles zero confidence', () {
        final result = ScanResult(
          isSpam: false,
          confidence: 0.0,
          prediction: 'ham',
          message: 'test',
          timestamp: '',
        );

        expect(result.confidencePercentage, '0.0%');
      });

      test('handles full confidence', () {
        final result = ScanResult(
          isSpam: true,
          confidence: 1.0,
          prediction: 'spam',
          message: 'test',
          timestamp: '',
        );

        expect(result.confidencePercentage, '100.0%');
      });
    });

    group('isHighRisk', () {
      test('returns true for CRITICAL risk level', () {
        final result = ScanResult(
          isSpam: true,
          confidence: 0.95,
          prediction: 'spam',
          message: 'test',
          timestamp: '',
          riskLevel: 'CRITICAL',
        );

        expect(result.isHighRisk, true);
      });

      test('returns true for HIGH risk level', () {
        final result = ScanResult(
          isSpam: true,
          confidence: 0.85,
          prediction: 'spam',
          message: 'test',
          timestamp: '',
          riskLevel: 'HIGH',
        );

        expect(result.isHighRisk, true);
      });

      test('returns false for MEDIUM risk level', () {
        final result = ScanResult(
          isSpam: true,
          confidence: 0.70,
          prediction: 'spam',
          message: 'test',
          timestamp: '',
          riskLevel: 'MEDIUM',
        );

        expect(result.isHighRisk, false);
      });

      test('returns false for NONE risk level', () {
        final result = ScanResult(
          isSpam: false,
          confidence: 0.90,
          prediction: 'ham',
          message: 'test',
          timestamp: '',
          riskLevel: 'NONE',
        );

        expect(result.isHighRisk, false);
      });
    });

    group('hasCriticalDanger', () {
      test('returns true when has critical danger cause', () {
        final result = ScanResult(
          isSpam: true,
          confidence: 0.9,
          prediction: 'spam',
          message: 'test',
          timestamp: '',
          dangerCauses: [
            DangerCause(
              type: 'critical',
              title: 'Critical Issue',
              description: 'Very dangerous',
              severity: 'critical',
            ),
          ],
        );

        expect(result.hasCriticalDanger, true);
      });

      test('returns false when no critical danger cause', () {
        final result = ScanResult(
          isSpam: true,
          confidence: 0.9,
          prediction: 'spam',
          message: 'test',
          timestamp: '',
          dangerCauses: [
            DangerCause(
              type: 'warning',
              title: 'Warning',
              description: 'Be careful',
              severity: 'high',
            ),
          ],
        );

        expect(result.hasCriticalDanger, false);
      });
    });

    group('hasHighDanger', () {
      test('returns true when has high severity danger cause', () {
        final result = ScanResult(
          isSpam: true,
          confidence: 0.85,
          prediction: 'spam',
          message: 'test',
          timestamp: '',
          dangerCauses: [
            DangerCause(
              type: 'urgency',
              title: 'Urgency',
              description: 'Urgent language',
              severity: 'high',
            ),
          ],
        );

        expect(result.hasHighDanger, true);
      });
    });

    group('dangerCount', () {
      test('returns correct count', () {
        final result = ScanResult(
          isSpam: true,
          confidence: 0.9,
          prediction: 'spam',
          message: 'test',
          timestamp: '',
          dangerCauses: [
            DangerCause(type: 'a', title: 'A', description: '', severity: 'high'),
            DangerCause(type: 'b', title: 'B', description: '', severity: 'medium'),
            DangerCause(type: 'c', title: 'C', description: '', severity: 'low'),
          ],
        );

        expect(result.dangerCount, 3);
      });

      test('returns zero for no danger causes', () {
        final result = ScanResult(
          isSpam: false,
          confidence: 0.9,
          prediction: 'ham',
          message: 'test',
          timestamp: '',
        );

        expect(result.dangerCount, 0);
      });
    });
  });

  group('DangerCause', () {
    group('fromJson', () {
      test('creates correct instance', () {
        final json = {
          'type': 'urgency',
          'title': 'Urgency Detected',
          'description': 'Contains urgent language',
          'severity': 'high',
        };

        final cause = DangerCause.fromJson(json);

        expect(cause.type, 'urgency');
        expect(cause.title, 'Urgency Detected');
        expect(cause.description, 'Contains urgent language');
        expect(cause.severity, 'high');
      });

      test('handles missing fields with defaults', () {
        final json = <String, dynamic>{};

        final cause = DangerCause.fromJson(json);

        expect(cause.type, '');
        expect(cause.severity, 'medium');
      });
    });

    group('toJson', () {
      test('serializes correctly', () {
        final cause = DangerCause(
          type: 'test',
          title: 'Test Title',
          description: 'Test description',
          severity: 'critical',
        );

        final json = cause.toJson();

        expect(json['type'], 'test');
        expect(json['title'], 'Test Title');
        expect(json['severity'], 'critical');
      });
    });

    group('isCritical', () {
      test('returns true for critical severity', () {
        final cause = DangerCause(
          type: 'test',
          title: 'Test',
          description: 'Test',
          severity: 'critical',
        );

        expect(cause.isCritical, true);
        expect(cause.isHigh, false);
      });

      test('returns false for non-critical severity', () {
        final cause = DangerCause(
          type: 'test',
          title: 'Test',
          description: 'Test',
          severity: 'high',
        );

        expect(cause.isCritical, false);
      });
    });

    group('isHigh', () {
      test('returns true for high severity', () {
        final cause = DangerCause(
          type: 'test',
          title: 'Test',
          description: 'Test',
          severity: 'high',
        );

        expect(cause.isHigh, true);
      });

      test('returns false for non-high severity', () {
        final cause = DangerCause(
          type: 'test',
          title: 'Test',
          description: 'Test',
          severity: 'medium',
        );

        expect(cause.isHigh, false);
      });
    });
  });
}
