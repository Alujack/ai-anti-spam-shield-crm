# Backend API Service

Node.js REST API server for AI Anti-Spam Shield.

## Technology Stack

| Technology | Purpose |
|------------|---------|
| Node.js 18+ | Runtime environment |
| Express.js | Web framework |
| Prisma | ORM & database migrations |
| PostgreSQL | Database |
| JWT | Authentication |
| Bcrypt | Password hashing |

## Quick Start

```bash
# Install dependencies
yarn install

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Setup database
yarn prisma:migrate
yarn prisma:generate

# Start development server
yarn dev
```

Server runs at `http://localhost:3000`

## Project Structure

```
src/
├── app.js                 # Application entry point
├── api/                   # API versioning
│   └── v1/               # Version 1 routes
├── config/               # Configuration
│   └── index.js          # Environment config
├── controllers/          # Request handlers
│   ├── message.controller.js
│   ├── phishing.controller.js
│   ├── user.controller.js
│   └── report.controller.js
├── middlewares/          # Express middlewares
│   ├── auth.js           # JWT authentication
│   ├── errorHandler.js   # Error handling
│   └── validate.js       # Request validation
├── routes/               # Route definitions
│   ├── index.js          # Route aggregator
│   ├── message.routes.js
│   ├── phishing.routes.js
│   ├── user.routes.js
│   └── report.routes.js
├── services/             # Business logic
│   ├── message.service.js
│   ├── phishing.service.js
│   ├── user.service.js
│   └── report.service.js
└── utils/                # Utilities
    ├── apiError.js       # Error class
    ├── asyncHandler.js   # Async wrapper
    └── logger.js         # Logging
```

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/users/register` | Register new user |
| POST | `/api/v1/users/login` | User login |
| GET | `/api/v1/users/profile` | Get user profile |
| PUT | `/api/v1/users/profile` | Update profile |

### Message Scanning

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/messages/scan-text` | Scan text message |
| POST | `/api/v1/messages/scan-voice` | Scan voice message |
| GET | `/api/v1/messages/history` | Get scan history |
| GET | `/api/v1/messages/stats` | Get statistics |

### Phishing Detection

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/phishing/scan` | Scan for phishing |
| POST | `/api/v1/phishing/scan-url` | Analyze URL |

### Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/reports` | Submit report |
| GET | `/api/v1/reports` | Get user reports |

## Scripts

```bash
yarn dev              # Development server with hot reload
yarn start            # Production server
yarn test             # Run tests
yarn prisma:migrate   # Run database migrations
yarn prisma:generate  # Generate Prisma client
yarn prisma:studio    # Open Prisma Studio GUI
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PORT` | No | Server port (default: 3000) |
| `NODE_ENV` | No | Environment (development/production) |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `JWT_SECRET` | Yes | JWT signing key (min 32 chars) |
| `JWT_EXPIRES_IN` | No | Token expiration (default: 7d) |
| `ML_SERVICE_URL` | Yes | AI service URL |
| `BCRYPT_SALT_ROUNDS` | No | Password hash rounds (default: 12) |

## Database Schema

```prisma
model User {
  id        String   @id @default(uuid())
  email     String   @unique
  password  String
  name      String
  phone     String?
  role      Role     @default(USER)
  scans     ScanHistory[]
  reports   Report[]
}

model ScanHistory {
  id         String   @id @default(uuid())
  userId     String
  message    String
  isSpam     Boolean
  confidence Float
  prediction String
  scannedAt  DateTime @default(now())
}

model Report {
  id          String @id @default(uuid())
  userId      String
  messageText String
  reportType  String
  status      String @default("PENDING")
}
```

## Documentation

- [API Reference](../docs/api/API_REFERENCE.md)
- [Development Guide](../docs/development/DEVELOPMENT_GUIDE.md)
- [Deployment Guide](../docs/deployment/DEPLOYMENT_GUIDE.md)
