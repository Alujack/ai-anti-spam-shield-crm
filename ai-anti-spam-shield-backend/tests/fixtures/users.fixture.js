/**
 * User Test Fixtures
 */

const validUser = {
  id: 'user-uuid-123',
  email: 'test@example.com',
  password: '$2a$10$hashedpasswordhere123456789',
  name: 'Test User',
  phone: '+1234567890',
  role: 'USER',
  createdAt: new Date('2024-01-01'),
  updatedAt: new Date('2024-01-01')
};

const adminUser = {
  id: 'admin-uuid-456',
  email: 'admin@example.com',
  password: '$2a$10$hashedpasswordhere123456789',
  name: 'Admin User',
  phone: '+1987654321',
  role: 'ADMIN',
  createdAt: new Date('2024-01-01'),
  updatedAt: new Date('2024-01-01')
};

const newUserData = {
  email: 'newuser@example.com',
  password: 'SecurePassword123!',
  name: 'New User',
  phone: '+1555555555'
};

const loginCredentials = {
  email: 'test@example.com',
  password: 'TestPassword123!'
};

const invalidCredentials = {
  email: 'test@example.com',
  password: 'wrongpassword'
};

const userWithoutPassword = {
  id: 'user-uuid-123',
  email: 'test@example.com',
  name: 'Test User',
  phone: '+1234567890',
  role: 'USER',
  createdAt: new Date('2024-01-01'),
  updatedAt: new Date('2024-01-01')
};

module.exports = {
  validUser,
  adminUser,
  newUserData,
  loginCredentials,
  invalidCredentials,
  userWithoutPassword
};
