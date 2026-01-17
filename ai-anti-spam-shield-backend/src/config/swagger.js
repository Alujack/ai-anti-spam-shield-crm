const swaggerJsdoc = require('swagger-jsdoc');

const options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'AI Anti-Spam Shield API',
      version: '1.0.0',
      description: 'AI-powered anti-spam and phishing detection API for message scanning and protection',
      contact: {
        name: 'API Support'
      }
    },
    servers: [
      {
        url: '/api/v1',
        description: 'API v1'
      }
    ],
    components: {
      securitySchemes: {
        bearerAuth: {
          type: 'http',
          scheme: 'bearer',
          bearerFormat: 'JWT',
          description: 'Enter JWT token'
        }
      },
      schemas: {
        // User schemas
        UserRegister: {
          type: 'object',
          required: ['email', 'password', 'name'],
          properties: {
            email: { type: 'string', format: 'email', example: 'user@example.com' },
            password: { type: 'string', minLength: 6, example: 'password123' },
            name: { type: 'string', example: 'John Doe' }
          }
        },
        UserLogin: {
          type: 'object',
          required: ['email', 'password'],
          properties: {
            email: { type: 'string', format: 'email', example: 'user@example.com' },
            password: { type: 'string', example: 'password123' }
          }
        },
        UserProfile: {
          type: 'object',
          properties: {
            id: { type: 'string' },
            email: { type: 'string' },
            name: { type: 'string' },
            role: { type: 'string', enum: ['USER', 'ADMIN'] },
            createdAt: { type: 'string', format: 'date-time' }
          }
        },
        ChangePassword: {
          type: 'object',
          required: ['currentPassword', 'newPassword'],
          properties: {
            currentPassword: { type: 'string' },
            newPassword: { type: 'string', minLength: 6 }
          }
        },
        // Message schemas
        ScanTextRequest: {
          type: 'object',
          required: ['text'],
          properties: {
            text: { type: 'string', example: 'Congratulations! You won $1000000!' }
          }
        },
        ScanResult: {
          type: 'object',
          properties: {
            status: { type: 'string', example: 'success' },
            data: {
              type: 'object',
              properties: {
                isSpam: { type: 'boolean' },
                confidence: { type: 'number', format: 'float' },
                message: { type: 'string' }
              }
            }
          }
        },
        // Phishing schemas
        PhishingScanText: {
          type: 'object',
          required: ['text'],
          properties: {
            text: { type: 'string', example: 'Click here to verify your account: http://suspicious-link.com' }
          }
        },
        PhishingScanUrl: {
          type: 'object',
          required: ['url'],
          properties: {
            url: { type: 'string', format: 'uri', example: 'http://suspicious-link.com' }
          }
        },
        PhishingResult: {
          type: 'object',
          properties: {
            status: { type: 'string' },
            data: {
              type: 'object',
              properties: {
                isPhishing: { type: 'boolean' },
                confidence: { type: 'number' },
                threatLevel: { type: 'string', enum: ['low', 'medium', 'high'] }
              }
            }
          }
        },
        // Report schemas
        CreateReport: {
          type: 'object',
          required: ['type', 'content'],
          properties: {
            type: { type: 'string', enum: ['SPAM', 'PHISHING', 'SCAM', 'OTHER'] },
            content: { type: 'string' },
            description: { type: 'string' }
          }
        },
        Report: {
          type: 'object',
          properties: {
            id: { type: 'string' },
            type: { type: 'string' },
            content: { type: 'string' },
            status: { type: 'string', enum: ['PENDING', 'REVIEWED', 'RESOLVED'] },
            createdAt: { type: 'string', format: 'date-time' }
          }
        },
        // Common schemas
        SuccessResponse: {
          type: 'object',
          properties: {
            status: { type: 'string', example: 'success' },
            message: { type: 'string' },
            data: { type: 'object' }
          }
        },
        ErrorResponse: {
          type: 'object',
          properties: {
            status: { type: 'string', example: 'error' },
            message: { type: 'string' }
          }
        }
      }
    },
    tags: [
      { name: 'Users', description: 'User authentication and profile management' },
      { name: 'Messages', description: 'Spam detection and message scanning' },
      { name: 'Phishing', description: 'Phishing detection and URL scanning' },
      { name: 'Reports', description: 'User reports management' }
    ]
  },
  apis: ['./src/routes/*.js']
};

const swaggerSpec = swaggerJsdoc(options);

module.exports = swaggerSpec;
