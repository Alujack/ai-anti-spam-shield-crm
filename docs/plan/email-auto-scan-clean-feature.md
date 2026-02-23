# Email Auto-Scan & Clean Feature - Implementation Plan

## Context

The client wants the AI Anti-Spam Shield system to automatically scan user emails from **any email provider** (Gmail, Outlook, Yahoo, etc.) using IMAP protocol, flag spam/phishing emails, and allow users to clean (trash) all flagged emails at once. Currently, the system only scans text/voice/URL content submitted manually — it has no direct mailbox integration.

---

## Architecture Overview

```
Mobile App                    Backend (Node.js)                 Email Server
┌──────────┐    REST API     ┌────────────────┐    IMAP        ┌──────────┐
│ Email     │ ──────────────>│ Email Routes   │ ──────────────>│ Gmail    │
│ Scan      │                │ Email Service  │                │ Outlook  │
│ Screen    │<──────────────│ Email Worker   │<──────────────│ Yahoo    │
│           │  WebSocket     │ (BullMQ)       │                │ Any IMAP │
└──────────┘                └────────────────┘                └──────────┘
                                    │
                                    ▼
                            ┌────────────────┐
                            │ AI/ML Service  │
                            │ /predict       │
                            │ /predict-phish │
                            └────────────────┘
```

**Key Decisions:**
- **IMAP protocol** for universal email provider support (not Gmail-only OAuth2)
- **Move to Trash** for clean action (recoverable for 30 days)
- **Both** auto-scheduled scanning (configurable interval) and manual trigger
- Credentials stored encrypted in DB (email, app password, IMAP server/port)

---

## Step 1: Database Schema Changes

**File:** `ai-anti-spam-shield-backend/prisma/schema.prisma`

Add two new models:

### `EmailAccount` — stores user's connected email accounts
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| userId | String | FK to User |
| email | String | IMAP email address |
| imapHost | String | e.g. imap.gmail.com |
| imapPort | Int | e.g. 993 |
| password | String | Encrypted app password |
| provider | String | gmail, outlook, yahoo, other |
| isActive | Boolean | Enable/disable scanning |
| autoScanInterval | Int | Minutes between scans (0 = disabled) |
| lastScanAt | DateTime? | Last successful scan time |
| lastScanStatus | String? | success, failed, scanning |
| totalScanned | Int | Cumulative emails scanned |
| totalFlagged | Int | Cumulative emails flagged |
| createdAt | DateTime | |
| updatedAt | DateTime | |

### `EmailScanResult` — stores scan results for individual emails
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| emailAccountId | String | FK to EmailAccount |
| userId | String | FK to User |
| messageId | String | IMAP message UID (for trash action) |
| subject | String | Email subject |
| sender | String | From address |
| receivedAt | DateTime | Email date |
| snippet | String | First ~200 chars of body |
| isSpam | Boolean | Spam detection result |
| spamConfidence | Float | Spam confidence score |
| isPhishing | Boolean | Phishing detection result |
| phishingConfidence | Float | Phishing confidence score |
| threatLevel | String | CRITICAL, HIGH, MEDIUM, LOW, NONE |
| isFlagged | Boolean | Combined flag (spam OR phishing) |
| isCleaned | Boolean | Whether user has trashed this |
| cleanedAt | DateTime? | When it was trashed |
| scannedAt | DateTime | |

Add relations to `User` model: `emailAccounts EmailAccount[]`, `emailScanResults EmailScanResult[]`

Run: `npx prisma migrate dev --name add_email_scan`

---

## Step 2: Backend - Email Service (Core Logic)

**New file:** `ai-anti-spam-shield-backend/src/services/email.service.js`

Uses `imapflow` npm package for IMAP operations.

### Key methods:
1. **`connectAccount(userId, { email, password, imapHost, imapPort, provider })`**
   - Validate IMAP credentials by attempting connection
   - Encrypt password before storing (using `crypto` AES-256)
   - Save to `EmailAccount` table
   - Return success/failure

2. **`scanEmails(emailAccountId)`**
   - Decrypt credentials, connect via IMAP
   - Fetch emails since `lastScanAt` (or last 7 days for first scan)
   - For each email: extract subject, sender, body snippet
   - Call existing AI service (`/predict` for spam, `/predict-phishing` for phishing)
   - Save results to `EmailScanResult`
   - Update `EmailAccount.lastScanAt`, `totalScanned`, `totalFlagged`
   - Emit WebSocket event for real-time progress

3. **`cleanFlaggedEmails(emailAccountId, emailIds?)`**
   - Decrypt credentials, connect via IMAP
   - Move flagged (or specified) emails to Trash folder
   - Update `EmailScanResult.isCleaned = true, cleanedAt = now()`
   - Return count of cleaned emails

4. **`disconnectAccount(emailAccountId)`**
   - Remove email account and all associated scan results

5. **`getAccountStatus(emailAccountId)`**
   - Return account info, scan stats, flagged count

### IMAP Provider Presets:
```js
const PROVIDER_PRESETS = {
  gmail: { host: 'imap.gmail.com', port: 993 },
  outlook: { host: 'outlook.office365.com', port: 993 },
  yahoo: { host: 'imap.mail.yahoo.com', port: 993 },
  other: null // user provides manually
};
```

---

## Step 3: Backend - Email Worker (BullMQ)

**File to modify:** `ai-anti-spam-shield-backend/src/config/queue.js`
- Add `EMAIL_SCAN: 'email-scan'` to QUEUES constant

**New file:** `ai-anti-spam-shield-backend/src/workers/email.worker.js`
- Processes email scan jobs from the queue
- Handles both manual trigger and scheduled scans
- Pattern follows existing `text.worker.js`

**New file:** `ai-anti-spam-shield-backend/src/workers/email.scheduler.js`
- Runs on a fixed interval (e.g., every minute)
- Checks `EmailAccount` for accounts due for auto-scan (`isActive && autoScanInterval > 0 && lastScanAt + interval < now`)
- Enqueues scan jobs into the EMAIL_SCAN queue

---

## Step 4: Backend - Routes & Controller

**New file:** `ai-anti-spam-shield-backend/src/routes/email.routes.js`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/emails/connect` | Required | Connect an email account |
| GET | `/api/v1/emails/accounts` | Required | List connected accounts |
| GET | `/api/v1/emails/accounts/:id` | Required | Get account details + stats |
| DELETE | `/api/v1/emails/accounts/:id` | Required | Disconnect email account |
| PUT | `/api/v1/emails/accounts/:id/settings` | Required | Update auto-scan interval |
| POST | `/api/v1/emails/accounts/:id/scan` | Required | Trigger manual scan |
| GET | `/api/v1/emails/accounts/:id/results` | Required | Get scan results (paginated, filterable) |
| GET | `/api/v1/emails/accounts/:id/flagged` | Required | Get flagged emails only |
| POST | `/api/v1/emails/accounts/:id/clean` | Required | Clean (trash) flagged emails |
| GET | `/api/v1/emails/statistics` | Required | Get overall email scan statistics |

**New file:** `ai-anti-spam-shield-backend/src/controllers/email.controller.js`
- Follows existing controller patterns (try/catch, response formatting)

**File to modify:** `ai-anti-spam-shield-backend/src/app.js`
- Register new email routes: `app.use('/api/v1/emails', emailRoutes)`

---

## Step 5: Backend - Encryption Utility

**New file:** `ai-anti-spam-shield-backend/src/utils/encryption.js`
- AES-256-GCM encryption/decryption for IMAP passwords
- Uses `ENCRYPTION_KEY` from environment variables
- Functions: `encrypt(text)`, `decrypt(encryptedData)`

**File to modify:** `ai-anti-spam-shield-backend/.env.example`
- Add `ENCRYPTION_KEY=` placeholder

---

## Step 6: Kong Gateway

**File to modify:** `gateway/kong/kong.yml`
- Add route for `/api/v1/emails` → backend service

---

## Step 7: Docker Compose

**File to modify:** `docker-compose.yml` and `docker-compose.dev.yml`
- Add `email-worker` service (same pattern as text-worker, voice-worker)
- Add `email-scheduler` service
- Add `ENCRYPTION_KEY` environment variable

---

## Step 8: Mobile App - Data Model

**New file:** `ai_anti_spam_shield_mobile/lib/models/email_account.dart`
```dart
class EmailAccount {
  final String id;
  final String email;
  final String provider; // gmail, outlook, yahoo, other
  final bool isActive;
  final int autoScanInterval; // minutes
  final DateTime? lastScanAt;
  final String? lastScanStatus;
  final int totalScanned;
  final int totalFlagged;
}
```

**New file:** `ai_anti_spam_shield_mobile/lib/models/email_scan_result.dart`
```dart
class EmailScanResult {
  final String id;
  final String messageId;
  final String subject;
  final String sender;
  final DateTime receivedAt;
  final String snippet;
  final bool isSpam;
  final double spamConfidence;
  final bool isPhishing;
  final double phishingConfidence;
  final String threatLevel;
  final bool isFlagged;
  final bool isCleaned;
}
```

---

## Step 9: Mobile App - API Methods

**File to modify:** `ai_anti_spam_shield_mobile/lib/services/api_service.dart`

Add new methods in an `EMAIL SCANNING ENDPOINTS` section:
- `connectEmailAccount({email, password, provider, imapHost?, imapPort?})`
- `getEmailAccounts()`
- `getEmailAccountById(id)`
- `disconnectEmailAccount(id)`
- `updateEmailAccountSettings(id, {autoScanInterval, isActive})`
- `triggerEmailScan(id)`
- `getEmailScanResults(accountId, {page, limit, flaggedOnly})`
- `cleanFlaggedEmails(accountId, {emailIds?})`
- `getEmailStatistics()`

---

## Step 10: Mobile App - Provider (State Management)

**New file:** `ai_anti_spam_shield_mobile/lib/providers/email_scan_provider.dart`

Follows the pattern from `phishing_provider.dart`:
- `EmailScanState` class (accounts list, scan results, loading states, error)
- `EmailScanNotifier` extends `StateNotifier<EmailScanState>`
- Methods: connectAccount, fetchAccounts, triggerScan, fetchResults, cleanEmails, updateSettings, disconnect

---

## Step 11: Mobile App - Screens

### Screen 1: Email Accounts Screen
**New file:** `ai_anti_spam_shield_mobile/lib/screens/email/email_accounts_screen.dart`
- Lists connected email accounts with status indicators
- "Connect Email" button → opens connect dialog
- Per-account: last scan time, flagged count, auto-scan toggle
- Tap account → navigates to Email Scan Results screen

### Screen 2: Connect Email Dialog/Screen
**New file:** `ai_anti_spam_shield_mobile/lib/screens/email/connect_email_screen.dart`
- Provider selection (Gmail, Outlook, Yahoo, Other)
- Auto-fills IMAP host/port for known providers
- Email + App Password input fields
- "Test Connection" button before saving
- Instructions/link for generating app passwords

### Screen 3: Email Scan Results Screen
**New file:** `ai_anti_spam_shield_mobile/lib/screens/email/email_results_screen.dart`
- Shows all scanned emails for an account
- Filter tabs: All | Flagged | Clean
- Each email card: subject, sender, date, threat badge (spam/phishing/safe)
- "Scan Now" button (manual trigger)
- "Clean All Flagged" button with confirmation dialog
- Pull-to-refresh

### Screen 4: Email Settings Screen
**New file:** `ai_anti_spam_shield_mobile/lib/screens/email/email_settings_screen.dart`
- Auto-scan interval selector (Off, 15min, 30min, 1hr, 4hr, 12hr, 24hr)
- Enable/disable auto-scan toggle
- Disconnect account button

### Navigation
**File to modify:** `ai_anti_spam_shield_mobile/lib/screens/home/home_screen.dart`
- Add "Email Scan" card/button to the home dashboard

**File to modify:** `ai_anti_spam_shield_mobile/lib/main.dart`
- Add routes for new email screens

---

## Step 12: NPM Dependencies

**File to modify:** `ai-anti-spam-shield-backend/package.json`
- Add `imapflow` (modern IMAP client for Node.js)
- Add `mailparser` (for parsing email content from IMAP)

---

## File Change Summary

### New Files (13)
| # | File | Description |
|---|------|-------------|
| 1 | `backend/src/services/email.service.js` | IMAP connection, scan, clean logic |
| 2 | `backend/src/controllers/email.controller.js` | Request handling |
| 3 | `backend/src/routes/email.routes.js` | API endpoint definitions |
| 4 | `backend/src/workers/email.worker.js` | BullMQ worker for email scanning |
| 5 | `backend/src/workers/email.scheduler.js` | Auto-scan scheduler |
| 6 | `backend/src/utils/encryption.js` | AES-256 encrypt/decrypt for passwords |
| 7 | `mobile/lib/models/email_account.dart` | EmailAccount model |
| 8 | `mobile/lib/models/email_scan_result.dart` | EmailScanResult model |
| 9 | `mobile/lib/providers/email_scan_provider.dart` | Riverpod state management |
| 10 | `mobile/lib/screens/email/email_accounts_screen.dart` | Account list screen |
| 11 | `mobile/lib/screens/email/connect_email_screen.dart` | Connect email flow |
| 12 | `mobile/lib/screens/email/email_results_screen.dart` | Scan results + clean |
| 13 | `mobile/lib/screens/email/email_settings_screen.dart` | Per-account settings |

### Modified Files (8)
| # | File | Change |
|---|------|--------|
| 1 | `backend/prisma/schema.prisma` | Add EmailAccount + EmailScanResult models |
| 2 | `backend/src/config/queue.js` | Add EMAIL_SCAN queue |
| 3 | `backend/src/app.js` | Register email routes |
| 4 | `backend/.env.example` | Add ENCRYPTION_KEY |
| 5 | `backend/package.json` | Add imapflow, mailparser |
| 6 | `gateway/kong/kong.yml` | Add email route |
| 7 | `docker-compose.yml` | Add email-worker + email-scheduler services |
| 8 | `mobile/lib/services/api_service.dart` | Add email API methods |
| 9 | `mobile/lib/screens/home/home_screen.dart` | Add Email Scan entry point |
| 10 | `mobile/lib/main.dart` | Add email screen routes |

---

## Security Considerations

1. **Password Encryption**: IMAP passwords encrypted at rest with AES-256-GCM; encryption key in env vars only
2. **No plain-text logging**: Never log email passwords or email content in full
3. **Rate limiting**: Limit scan frequency to prevent IMAP server abuse
4. **Token scoping**: Email endpoints require authenticated user; users can only access their own accounts
5. **App Passwords**: Guide users to use app-specific passwords (not main passwords) for Gmail/Outlook
6. **Connection validation**: Test IMAP connection before saving credentials

---

## Verification / Testing Plan

1. **Unit tests**: Email service methods (mock IMAP), controller endpoints (supertest)
2. **Integration test**: Connect a test Gmail account (app password), trigger scan, verify results saved
3. **Manual testing flow**:
   - Connect Gmail account with app password → verify success
   - Trigger manual scan → verify emails appear in results
   - Check flagged emails → verify spam/phishing detection
   - Clean flagged → verify emails moved to Gmail Trash
   - Set auto-scan interval → verify scheduled scans trigger
   - Disconnect account → verify data cleaned up
4. **Mobile app**: Test all screens render, API calls work, loading/error states

---

## Implementation Order

1. Database schema + migration
2. Encryption utility
3. Email service (IMAP core logic)
4. Email worker + scheduler
5. Routes + controller
6. Register in app.js + queue config
7. Kong gateway + Docker Compose
8. Mobile models
9. Mobile API methods
10. Mobile provider
11. Mobile screens
12. Integration testing
