/**
 * Prisma Client Mock
 * Provides mock implementations of Prisma operations for testing
 */

const prismaMock = {
  user: {
    findUnique: jest.fn(),
    findFirst: jest.fn(),
    findMany: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
    count: jest.fn()
  },
  scanHistory: {
    findUnique: jest.fn(),
    findFirst: jest.fn(),
    findMany: jest.fn(),
    create: jest.fn(),
    createManyAndReturn: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
    count: jest.fn(),
    groupBy: jest.fn()
  },
  phishingScanHistory: {
    findUnique: jest.fn(),
    findFirst: jest.fn(),
    findMany: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
    count: jest.fn(),
    groupBy: jest.fn()
  },
  report: {
    findUnique: jest.fn(),
    findFirst: jest.fn(),
    findMany: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
    count: jest.fn(),
    groupBy: jest.fn()
  },
  userFeedback: {
    findUnique: jest.fn(),
    findFirst: jest.fn(),
    findMany: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
    count: jest.fn()
  },
  scanJob: {
    findUnique: jest.fn(),
    findFirst: jest.fn(),
    findMany: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
    count: jest.fn()
  },
  $connect: jest.fn(),
  $disconnect: jest.fn(),
  $transaction: jest.fn((callback) => callback(prismaMock)),
  // $queryRaw is used as a tagged template literal, so it needs to be a function that returns a Promise
  $queryRaw: Object.assign(jest.fn(() => Promise.resolve([])), {
    mockResolvedValue: function(val) {
      this.mockImplementation(() => Promise.resolve(val));
      return this;
    }
  }),
  $executeRaw: Object.assign(jest.fn(() => Promise.resolve(0)), {
    mockResolvedValue: function(val) {
      this.mockImplementation(() => Promise.resolve(val));
      return this;
    }
  })
};

// Reset all mocks helper
prismaMock.$reset = () => {
  Object.keys(prismaMock).forEach(key => {
    if (typeof prismaMock[key] === 'object' && prismaMock[key] !== null) {
      Object.keys(prismaMock[key]).forEach(method => {
        if (typeof prismaMock[key][method] === 'function' && prismaMock[key][method].mockReset) {
          prismaMock[key][method].mockReset();
        }
      });
    }
  });
};

module.exports = prismaMock;
