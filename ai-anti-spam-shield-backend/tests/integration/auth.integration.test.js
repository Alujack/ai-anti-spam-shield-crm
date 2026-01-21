/**
 * Authentication Integration Tests
 */

const request = require('supertest');
const prismaMock = require('../mocks/prisma.mock');
const { validUser, newUserData, loginCredentials } = require('../fixtures/users.fixture');

// Mock dependencies before requiring app
jest.mock('../../src/config/database', () => require('../mocks/prisma.mock'));

jest.mock('../../src/utils/auth', () => ({
  hashPassword: jest.fn().mockResolvedValue('$2a$10$hashedpassword'),
  comparePassword: jest.fn(),
  generateToken: jest.fn().mockReturnValue('mock-jwt-token'),
  generateRefreshToken: jest.fn().mockReturnValue('mock-refresh-token'),
  verifyToken: jest.fn()
}));

jest.mock('../../src/utils/logger', () => ({
  info: jest.fn(),
  error: jest.fn(),
  warn: jest.fn(),
  stream: { write: jest.fn() }
}));

// Mock Redis/Queue dependencies
jest.mock('../../src/config/redis', () => ({
  createClient: jest.fn().mockReturnValue({
    connect: jest.fn(),
    on: jest.fn(),
    get: jest.fn(),
    set: jest.fn(),
    del: jest.fn()
  })
}));

jest.mock('../../src/config/queue', () => ({
  textQueue: { add: jest.fn() },
  voiceQueue: { add: jest.fn() },
  urlQueue: { add: jest.fn() }
}));

const { comparePassword, verifyToken } = require('../../src/utils/auth');

// Create a minimal express app for testing
const express = require('express');
const userController = require('../../src/controllers/user.controller');

const createTestApp = () => {
  const app = express();
  app.use(express.json());

  // Register routes
  app.post('/api/v1/users/register', userController.register);
  app.post('/api/v1/users/login', userController.login);
  app.get('/api/v1/users/profile', (req, res, next) => {
    // Mock auth middleware
    if (req.headers.authorization) {
      req.user = { userId: validUser.id };
      next();
    } else {
      res.status(401).json({ error: 'Unauthorized' });
    }
  }, userController.getProfile);

  // Error handler
  app.use((err, req, res, next) => {
    res.status(err.statusCode || 500).json({
      success: false,
      message: err.message || 'Internal Server Error'
    });
  });

  return app;
};

describe('Auth Integration Tests', () => {
  let app;

  beforeAll(() => {
    app = createTestApp();
  });

  beforeEach(() => {
    prismaMock.$reset();
    jest.clearAllMocks();
  });

  describe('POST /api/v1/users/register', () => {
    it('should register a new user and return tokens', async () => {
      prismaMock.user.findUnique.mockResolvedValue(null);
      prismaMock.user.create.mockResolvedValue({
        id: 'new-user-uuid',
        email: newUserData.email,
        name: newUserData.name,
        phone: newUserData.phone,
        role: 'USER',
        createdAt: new Date()
      });

      const res = await request(app)
        .post('/api/v1/users/register')
        .send(newUserData);

      expect(res.status).toBe(201);
      expect(res.body.success).toBe(true);
      expect(res.body.data.token).toBe('mock-jwt-token');
      expect(res.body.data.refreshToken).toBe('mock-refresh-token');
      expect(res.body.data.user.email).toBe(newUserData.email);
    });

    it('should reject registration with existing email', async () => {
      prismaMock.user.findUnique.mockResolvedValue(validUser);

      const res = await request(app)
        .post('/api/v1/users/register')
        .send(newUserData);

      expect(res.status).toBe(409);
      expect(res.body.message).toContain('already registered');
    });

    it('should validate required fields', async () => {
      const res = await request(app)
        .post('/api/v1/users/register')
        .send({ email: 'test@test.com' }); // Missing password

      expect(res.status).toBe(400);
    });
  });

  describe('POST /api/v1/users/login', () => {
    it('should authenticate valid credentials', async () => {
      prismaMock.user.findUnique.mockResolvedValue(validUser);
      comparePassword.mockResolvedValue(true);

      const res = await request(app)
        .post('/api/v1/users/login')
        .send(loginCredentials);

      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(res.body.data.token).toBe('mock-jwt-token');
    });

    it('should reject invalid credentials', async () => {
      prismaMock.user.findUnique.mockResolvedValue(validUser);
      comparePassword.mockResolvedValue(false);

      const res = await request(app)
        .post('/api/v1/users/login')
        .send(loginCredentials);

      expect(res.status).toBe(401);
    });

    it('should reject non-existent user', async () => {
      prismaMock.user.findUnique.mockResolvedValue(null);

      const res = await request(app)
        .post('/api/v1/users/login')
        .send({ email: 'nonexistent@test.com', password: 'password' });

      expect(res.status).toBe(401);
    });
  });

  describe('GET /api/v1/users/profile', () => {
    it('should return user profile with valid token', async () => {
      const { password, ...userWithoutPass } = validUser;
      prismaMock.user.findUnique.mockResolvedValue(userWithoutPass);

      const res = await request(app)
        .get('/api/v1/users/profile')
        .set('Authorization', 'Bearer mock-jwt-token');

      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(res.body.data.email).toBe(validUser.email);
    });

    it('should reject request without token', async () => {
      const res = await request(app)
        .get('/api/v1/users/profile');

      expect(res.status).toBe(401);
    });
  });
});
