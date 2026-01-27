import 'package:flutter_test/flutter_test.dart';
import 'package:ai_anti_spam_shield_mobile/models/report.dart';

void main() {
  group('Report', () {
    test('fromJson creates correct instance with all fields', () {
      final json = {
        'id': 'report-123',
        'visitorId': 'user-456',
        'type': 'phishing',
        'content': 'Suspicious email claiming to be from bank',
        'url': 'http://fake-bank.com',
        'phoneNumber': '+1234567890',
        'senderInfo': 'fake@bank.com',
        'description': 'Received this suspicious email',
        'status': 'pending',
        'createdAt': '2024-01-15T10:30:00Z',
        'updatedAt': '2024-01-16T14:00:00Z',
      };

      final report = Report.fromJson(json);

      expect(report.id, 'report-123');
      expect(report.visitorId, 'user-456');
      expect(report.type, 'phishing');
      expect(report.content, 'Suspicious email claiming to be from bank');
      expect(report.url, 'http://fake-bank.com');
      expect(report.phoneNumber, '+1234567890');
      expect(report.senderInfo, 'fake@bank.com');
      expect(report.description, 'Received this suspicious email');
      expect(report.status, 'pending');
      expect(report.createdAt, DateTime.parse('2024-01-15T10:30:00Z'));
      expect(report.updatedAt, DateTime.parse('2024-01-16T14:00:00Z'));
    });

    test('fromJson handles alternative id key (_id)', () {
      final json = {
        '_id': 'mongo-id-123',
        'userId': 'user-789',
        'type': 'spam',
        'content': 'Test content',
        'description': 'Test description',
        'status': 'reviewed',
        'createdAt': '2024-01-15T10:30:00Z',
      };

      final report = Report.fromJson(json);

      expect(report.id, 'mongo-id-123');
      expect(report.visitorId, 'user-789');
    });

    test('fromJson handles missing optional fields', () {
      final json = {
        'id': 'report-1',
        'visitorId': 'user-1',
        'type': 'scam',
        'content': 'Scam content',
        'description': 'Scam description',
        'status': 'resolved',
        'createdAt': '2024-01-15T10:30:00Z',
      };

      final report = Report.fromJson(json);

      expect(report.url, isNull);
      expect(report.phoneNumber, isNull);
      expect(report.senderInfo, isNull);
      expect(report.updatedAt, isNull);
    });

    test('fromJson handles missing fields with defaults', () {
      final json = <String, dynamic>{
        'createdAt': '2024-01-15T10:30:00Z',
      };

      final report = Report.fromJson(json);

      expect(report.id, '');
      expect(report.visitorId, '');
      expect(report.type, 'other');
      expect(report.content, '');
      expect(report.description, '');
      expect(report.status, 'pending');
    });

    test('fromJson handles null createdAt with current time', () {
      final json = {
        'id': 'report-1',
        'visitorId': 'user-1',
        'type': 'spam',
        'content': 'Test',
        'description': 'Test',
        'status': 'pending',
      };

      final beforeCreation = DateTime.now();
      final report = Report.fromJson(json);
      final afterCreation = DateTime.now();

      expect(report.createdAt.isAfter(beforeCreation.subtract(const Duration(seconds: 1))), true);
      expect(report.createdAt.isBefore(afterCreation.add(const Duration(seconds: 1))), true);
    });

    test('toJson creates correct map', () {
      final report = Report(
        id: 'report-abc',
        visitorId: 'user-xyz',
        type: 'phishing',
        content: 'Test phishing content',
        url: 'http://malicious.com',
        phoneNumber: '+1987654321',
        senderInfo: 'attacker@evil.com',
        description: 'Test description',
        status: 'pending',
        createdAt: DateTime.parse('2024-01-15T10:30:00Z'),
        updatedAt: DateTime.parse('2024-01-16T12:00:00Z'),
      );

      final json = report.toJson();

      expect(json['id'], 'report-abc');
      expect(json['visitorId'], 'user-xyz');
      expect(json['type'], 'phishing');
      expect(json['content'], 'Test phishing content');
      expect(json['url'], 'http://malicious.com');
      expect(json['phoneNumber'], '+1987654321');
      expect(json['senderInfo'], 'attacker@evil.com');
      expect(json['description'], 'Test description');
      expect(json['status'], 'pending');
      expect(json['createdAt'], '2024-01-15T10:30:00.000Z');
      expect(json['updatedAt'], '2024-01-16T12:00:00.000Z');
    });

    test('toJson handles null optional fields', () {
      final report = Report(
        id: 'report-1',
        visitorId: 'user-1',
        type: 'spam',
        content: 'Test',
        description: 'Test',
        status: 'pending',
        createdAt: DateTime.now(),
      );

      final json = report.toJson();

      expect(json['url'], isNull);
      expect(json['phoneNumber'], isNull);
      expect(json['senderInfo'], isNull);
      expect(json['updatedAt'], isNull);
    });
  });

  group('Report statusDisplayName', () {
    test('pending returns "Pending Review"', () {
      final report = _createReportWithStatus('pending');
      expect(report.statusDisplayName, 'Pending Review');
    });

    test('reviewed returns "Under Review"', () {
      final report = _createReportWithStatus('reviewed');
      expect(report.statusDisplayName, 'Under Review');
    });

    test('resolved returns "Resolved"', () {
      final report = _createReportWithStatus('resolved');
      expect(report.statusDisplayName, 'Resolved');
    });

    test('rejected returns "Rejected"', () {
      final report = _createReportWithStatus('rejected');
      expect(report.statusDisplayName, 'Rejected');
    });

    test('unknown status returns the status itself', () {
      final report = _createReportWithStatus('custom_status');
      expect(report.statusDisplayName, 'custom_status');
    });
  });

  group('Report typeDisplayName', () {
    test('spam returns "Spam"', () {
      final report = _createReportWithType('spam');
      expect(report.typeDisplayName, 'Spam');
    });

    test('phishing returns "Phishing"', () {
      final report = _createReportWithType('phishing');
      expect(report.typeDisplayName, 'Phishing');
    });

    test('scam returns "Scam"', () {
      final report = _createReportWithType('scam');
      expect(report.typeDisplayName, 'Scam');
    });

    test('other returns "Other"', () {
      final report = _createReportWithType('other');
      expect(report.typeDisplayName, 'Other');
    });

    test('unknown type returns the type itself', () {
      final report = _createReportWithType('custom_type');
      expect(report.typeDisplayName, 'custom_type');
    });
  });

  group('ReportStatistics', () {
    test('fromJson creates correct instance', () {
      final json = {
        'totalReports': 100,
        'pendingReports': 40,
        'resolvedReports': 50,
        'reportsByType': {
          'spam': 45,
          'phishing': 30,
          'scam': 20,
          'other': 5,
        },
      };

      final stats = ReportStatistics.fromJson(json);

      expect(stats.totalReports, 100);
      expect(stats.pendingReports, 40);
      expect(stats.resolvedReports, 50);
      expect(stats.reportsByType['spam'], 45);
      expect(stats.reportsByType['phishing'], 30);
      expect(stats.reportsByType['scam'], 20);
      expect(stats.reportsByType['other'], 5);
    });

    test('fromJson handles missing fields with defaults', () {
      final json = <String, dynamic>{};

      final stats = ReportStatistics.fromJson(json);

      expect(stats.totalReports, 0);
      expect(stats.pendingReports, 0);
      expect(stats.resolvedReports, 0);
      expect(stats.reportsByType, isEmpty);
    });

    test('fromJson handles partial reportsByType', () {
      final json = {
        'totalReports': 10,
        'pendingReports': 5,
        'resolvedReports': 5,
        'reportsByType': {
          'spam': 10,
        },
      };

      final stats = ReportStatistics.fromJson(json);

      expect(stats.reportsByType['spam'], 10);
      expect(stats.reportsByType['phishing'], isNull);
    });
  });

  group('Report types', () {
    test('all standard types are handled', () {
      final types = ['spam', 'phishing', 'scam', 'other'];

      for (final type in types) {
        final report = _createReportWithType(type);
        expect(report.type, type);
        expect(report.typeDisplayName, isNotEmpty);
      }
    });

    test('all standard statuses are handled', () {
      final statuses = ['pending', 'reviewed', 'resolved', 'rejected'];

      for (final status in statuses) {
        final report = _createReportWithStatus(status);
        expect(report.status, status);
        expect(report.statusDisplayName, isNotEmpty);
      }
    });
  });

  group('Report edge cases', () {
    test('handles very long content', () {
      final longContent = 'A' * 10000;
      final json = {
        'id': 'report-1',
        'visitorId': 'user-1',
        'type': 'spam',
        'content': longContent,
        'description': 'Long content test',
        'status': 'pending',
        'createdAt': '2024-01-15T10:30:00Z',
      };

      final report = Report.fromJson(json);

      expect(report.content.length, 10000);
    });

    test('handles special characters in content', () {
      final specialContent = 'Test <script>alert("xss")</script> & "quotes" \'apostrophes\'';
      final json = {
        'id': 'report-1',
        'visitorId': 'user-1',
        'type': 'phishing',
        'content': specialContent,
        'description': 'Special chars test',
        'status': 'pending',
        'createdAt': '2024-01-15T10:30:00Z',
      };

      final report = Report.fromJson(json);

      expect(report.content, specialContent);
    });

    test('handles unicode content', () {
      final unicodeContent = '测试内容 🚨 محتوى الاختبار';
      final json = {
        'id': 'report-1',
        'visitorId': 'user-1',
        'type': 'spam',
        'content': unicodeContent,
        'description': 'Unicode test',
        'status': 'pending',
        'createdAt': '2024-01-15T10:30:00Z',
      };

      final report = Report.fromJson(json);

      expect(report.content, unicodeContent);
    });

    test('handles international phone numbers', () {
      final phoneNumbers = [
        '+1-800-555-1234',
        '+44 20 7946 0958',
        '+86 10 1234 5678',
        '+66 2 123 4567',
      ];

      for (final phone in phoneNumbers) {
        final json = {
          'id': 'report-1',
          'visitorId': 'user-1',
          'type': 'scam',
          'content': 'Test',
          'phoneNumber': phone,
          'description': 'Test',
          'status': 'pending',
          'createdAt': '2024-01-15T10:30:00Z',
        };

        final report = Report.fromJson(json);
        expect(report.phoneNumber, phone);
      }
    });

    test('handles various URL formats', () {
      final urls = [
        'http://example.com',
        'https://secure.example.com/path?query=value',
        'http://192.168.1.1:8080',
        'https://subdomain.domain.co.uk/path/to/resource',
      ];

      for (final url in urls) {
        final json = {
          'id': 'report-1',
          'visitorId': 'user-1',
          'type': 'phishing',
          'content': 'Test',
          'url': url,
          'description': 'Test',
          'status': 'pending',
          'createdAt': '2024-01-15T10:30:00Z',
        };

        final report = Report.fromJson(json);
        expect(report.url, url);
      }
    });
  });
}

// Helper functions
Report _createReportWithStatus(String status) {
  return Report(
    id: 'test-id',
    visitorId: 'test-user',
    type: 'spam',
    content: 'Test content',
    description: 'Test description',
    status: status,
    createdAt: DateTime.now(),
  );
}

Report _createReportWithType(String type) {
  return Report(
    id: 'test-id',
    visitorId: 'test-user',
    type: type,
    content: 'Test content',
    description: 'Test description',
    status: 'pending',
    createdAt: DateTime.now(),
  );
}
