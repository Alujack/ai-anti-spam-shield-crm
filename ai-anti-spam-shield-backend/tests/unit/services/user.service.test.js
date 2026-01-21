/**
 * User Service Unit Tests
 */

const prismaMock = require('../../mocks/prisma.mock');
const { validUser, newUserData, loginCredentials } = require('../../fixtures/users.fixture');

// Mock the database module
jest.mock('../../../src/config/database', () => require('../../mocks/prisma.mock'));

// Mock the auth utils
jest.mock('../../../src/utils/auth', () => ({
  hashPassword: jest.fn().mockResolvedValue('$2a$10$hashedpassword'),
  comparePassword: jest.fn(),
  generateToken: jest.fn().mockReturnValue('mock-jwt-token'),
  generateRefreshToken: jest.fn().mockReturnValue('mock-refresh-token')
}));

// Mock the logger
jest.mock('../../../src/utils/logger', () => ({
  info: jest.fn(),
  error: jest.fn(),
  warn: jest.fn()
}));

const { hashPassword, comparePassword, generateToken, generateRefreshToken } = require('../../../src/utils/auth');
const userService = require('../../../src/services/user.service');

describe('UserService', () => {
  beforeEach(() => {
    prismaMock.$reset();
    jest.clearAllMocks();
    // Reset mock implementations
    generateToken.mockReturnValue('mock-jwt-token');
    generateRefreshToken.mockReturnValue('mock-refresh-token');
  });

  describe('register', () => {
    it('should register a new user successfully', async () => {
      prismaMock.user.findUnique.mockResolvedValue(null);
      prismaMock.user.create.mockResolvedValue({
        id: 'new-user-uuid',
        email: newUserData.email,
        name: newUserData.name,
        phone: newUserData.phone,
        role: 'USER',
        createdAt: new Date()
      });

      const result = await userService.register(newUserData);

      expect(result.user.email).toBe(newUserData.email);
      expect(result.token).toBe('mock-jwt-token');
      expect(result.refreshToken).toBe('mock-refresh-token');
      expect(prismaMock.user.findUnique).toHaveBeenCalledWith({
        where: { email: newUserData.email }
      });
      expect(prismaMock.user.create).toHaveBeenCalled();
    });

    it('should throw error if email already exists', async () => {
      prismaMock.user.findUnique.mockResolvedValue(validUser);

      await expect(userService.register(newUserData))
        .rejects.toThrow('Email already registered');
    });

    it('should hash the password before storing', async () => {
      prismaMock.user.findUnique.mockResolvedValue(null);
      prismaMock.user.create.mockResolvedValue({
        id: 'new-user-uuid',
        email: newUserData.email,
        name: newUserData.name,
        role: 'USER'
      });

      await userService.register(newUserData);

      expect(hashPassword).toHaveBeenCalledWith(newUserData.password);
    });
  });

  describe('login', () => {
    it('should authenticate valid credentials', async () => {
      prismaMock.user.findUnique.mockResolvedValue(validUser);
      comparePassword.mockResolvedValue(true);

      const result = await userService.login(loginCredentials);

      expect(result.token).toBe('mock-jwt-token');
      expect(result.refreshToken).toBe('mock-refresh-token');
      expect(result.user.email).toBe(validUser.email);
      expect(result.user.password).toBeUndefined();
    });

    it('should reject non-existent user', async () => {
      prismaMock.user.findUnique.mockResolvedValue(null);

      await expect(userService.login(loginCredentials))
        .rejects.toThrow('Invalid email or password');
    });

    it('should reject invalid password', async () => {
      prismaMock.user.findUnique.mockResolvedValue(validUser);
      comparePassword.mockResolvedValue(false);

      await expect(userService.login(loginCredentials))
        .rejects.toThrow('Invalid email or password');
    });
  });

  describe('getProfile', () => {
    it('should return user profile', async () => {
      const { password, ...userWithoutPass } = validUser;
      prismaMock.user.findUnique.mockResolvedValue(userWithoutPass);

      const result = await userService.getProfile(validUser.id);

      expect(result.id).toBe(validUser.id);
      expect(result.email).toBe(validUser.email);
      expect(prismaMock.user.findUnique).toHaveBeenCalledWith({
        where: { id: validUser.id },
        select: expect.objectContaining({
          id: true,
          email: true,
          name: true
        })
      });
    });

    it('should throw error if user not found', async () => {
      prismaMock.user.findUnique.mockResolvedValue(null);

      await expect(userService.getProfile('non-existent-id'))
        .rejects.toThrow('User not found');
    });
  });

  describe('updateProfile', () => {
    it('should update user profile', async () => {
      const updateData = { name: 'Updated Name', phone: '+1999999999' };
      const updatedUser = { ...validUser, ...updateData };
      prismaMock.user.update.mockResolvedValue(updatedUser);

      const result = await userService.updateProfile(validUser.id, updateData);

      expect(result.name).toBe(updateData.name);
      expect(result.phone).toBe(updateData.phone);
    });

    it('should only update provided fields', async () => {
      const updateData = { name: 'Only Name Updated' };
      prismaMock.user.update.mockResolvedValue({ ...validUser, name: updateData.name });

      await userService.updateProfile(validUser.id, updateData);

      expect(prismaMock.user.update).toHaveBeenCalledWith({
        where: { id: validUser.id },
        data: { name: updateData.name },
        select: expect.any(Object)
      });
    });
  });

  describe('deleteUser', () => {
    it('should delete user successfully', async () => {
      prismaMock.user.delete.mockResolvedValue(validUser);

      const result = await userService.deleteUser(validUser.id);

      expect(result.message).toBe('User deleted successfully');
      expect(prismaMock.user.delete).toHaveBeenCalledWith({
        where: { id: validUser.id }
      });
    });
  });

  describe('changePassword', () => {
    it('should change password successfully', async () => {
      prismaMock.user.findUnique.mockResolvedValue(validUser);
      comparePassword.mockResolvedValue(true);
      prismaMock.user.update.mockResolvedValue(validUser);

      const result = await userService.changePassword(
        validUser.id,
        'oldPassword',
        'newPassword123!'
      );

      expect(result.message).toBe('Password changed successfully');
      expect(hashPassword).toHaveBeenCalledWith('newPassword123!');
    });

    it('should reject incorrect current password', async () => {
      prismaMock.user.findUnique.mockResolvedValue(validUser);
      comparePassword.mockResolvedValue(false);

      await expect(
        userService.changePassword(validUser.id, 'wrongPassword', 'newPassword')
      ).rejects.toThrow('Current password is incorrect');
    });

    it('should throw error if user not found', async () => {
      prismaMock.user.findUnique.mockResolvedValue(null);

      await expect(
        userService.changePassword('non-existent', 'old', 'new')
      ).rejects.toThrow('User not found');
    });
  });
});
