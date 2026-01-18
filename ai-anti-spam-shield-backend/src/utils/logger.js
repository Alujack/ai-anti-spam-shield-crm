/**
 * Professional Logging Service
 * Centralized logging with Winston - file rotation, multiple transports, and formatting
 */

const winston = require('winston');
const DailyRotateFile = require('winston-daily-rotate-file');
const path = require('path');
const fs = require('fs');

// Log directory configuration
const LOG_DIR = process.env.LOG_DIR || path.join(__dirname, '../../../logs/backend');
const LOG_LEVEL = process.env.LOG_LEVEL || (process.env.NODE_ENV === 'production' ? 'info' : 'debug');
const LOG_MAX_SIZE = process.env.LOG_MAX_SIZE || '20m';
const LOG_MAX_FILES = process.env.LOG_MAX_FILES || '14d';

// Ensure log directory exists
if (!fs.existsSync(LOG_DIR)) {
    fs.mkdirSync(LOG_DIR, { recursive: true });
}

// Custom log format
const customFormat = winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss.SSS' }),
    winston.format.errors({ stack: true }),
    winston.format.printf(({ timestamp, level, message, stack, ...meta }) => {
        let log = `[${timestamp}] [${level.toUpperCase().padEnd(5)}]`;

        // Add request ID if present
        if (meta.requestId) {
            log += ` [${meta.requestId}]`;
            delete meta.requestId;
        }

        log += ` ${message}`;

        // Add metadata if present
        if (Object.keys(meta).length > 0) {
            log += ` ${JSON.stringify(meta)}`;
        }

        // Add stack trace for errors
        if (stack) {
            log += `\n${stack}`;
        }

        return log;
    })
);

// Console format with colors
const consoleFormat = winston.format.combine(
    winston.format.colorize({ all: true }),
    winston.format.timestamp({ format: 'HH:mm:ss' }),
    winston.format.printf(({ timestamp, level, message, ...meta }) => {
        let log = `[${timestamp}] ${level}: ${message}`;
        if (Object.keys(meta).length > 0 && !meta.stack) {
            const metaStr = JSON.stringify(meta);
            if (metaStr !== '{}') {
                log += ` ${metaStr}`;
            }
        }
        return log;
    })
);

// Create transports
const transports = [
    // Console transport
    new winston.transports.Console({
        format: consoleFormat,
        level: LOG_LEVEL
    }),

    // Combined log file - all levels
    new DailyRotateFile({
        filename: path.join(LOG_DIR, 'combined-%DATE%.log'),
        datePattern: 'YYYY-MM-DD',
        maxSize: LOG_MAX_SIZE,
        maxFiles: LOG_MAX_FILES,
        format: customFormat,
        level: 'debug'
    }),

    // Error log file - errors only
    new DailyRotateFile({
        filename: path.join(LOG_DIR, 'error-%DATE%.log'),
        datePattern: 'YYYY-MM-DD',
        maxSize: LOG_MAX_SIZE,
        maxFiles: LOG_MAX_FILES,
        format: customFormat,
        level: 'error'
    }),

    // HTTP access log
    new DailyRotateFile({
        filename: path.join(LOG_DIR, 'access-%DATE%.log'),
        datePattern: 'YYYY-MM-DD',
        maxSize: LOG_MAX_SIZE,
        maxFiles: LOG_MAX_FILES,
        format: customFormat,
        level: 'http'
    })
];

// Create logger instance
const logger = winston.createLogger({
    level: LOG_LEVEL,
    levels: {
        error: 0,
        warn: 1,
        info: 2,
        http: 3,
        debug: 4,
        trace: 5
    },
    format: customFormat,
    transports,
    exitOnError: false
});

// Add custom colors
winston.addColors({
    error: 'red bold',
    warn: 'yellow',
    info: 'green',
    http: 'magenta',
    debug: 'blue',
    trace: 'gray'
});

/**
 * Security event logger - writes to separate security log
 */
const securityTransport = new DailyRotateFile({
    filename: path.join(LOG_DIR, 'security-%DATE%.log'),
    datePattern: 'YYYY-MM-DD',
    maxSize: LOG_MAX_SIZE,
    maxFiles: '30d', // Keep security logs longer
    format: customFormat
});

logger.security = (message, meta = {}) => {
    const securityMeta = {
        ...meta,
        type: 'SECURITY',
        timestamp: new Date().toISOString()
    };
    logger.warn(`[SECURITY] ${message}`, securityMeta);
    securityTransport.log({ level: 'warn', message: `[SECURITY] ${message}`, ...securityMeta });
};

/**
 * Audit event logger - writes to separate audit log
 */
const auditTransport = new DailyRotateFile({
    filename: path.join(LOG_DIR, 'audit-%DATE%.log'),
    datePattern: 'YYYY-MM-DD',
    maxSize: LOG_MAX_SIZE,
    maxFiles: '90d', // Keep audit logs for 90 days
    format: customFormat
});

logger.audit = (action, userId, resource, meta = {}) => {
    const auditMeta = {
        action,
        userId,
        resource,
        ...meta,
        type: 'AUDIT',
        timestamp: new Date().toISOString()
    };
    const message = `User ${userId} performed ${action} on ${resource}`;
    logger.info(`[AUDIT] ${message}`, auditMeta);
    auditTransport.log({ level: 'info', message: `[AUDIT] ${message}`, ...auditMeta });
};

/**
 * HTTP request logger middleware
 */
logger.httpLogger = (req, res, next) => {
    const startTime = Date.now();

    res.on('finish', () => {
        const duration = Date.now() - startTime;
        const logData = {
            method: req.method,
            url: req.originalUrl || req.url,
            status: res.statusCode,
            duration: `${duration}ms`,
            ip: req.ip || req.connection?.remoteAddress,
            userAgent: req.get('user-agent'),
            contentLength: res.get('content-length') || 0
        };

        // Add user ID if authenticated
        if (req.user?.id) {
            logData.userId = req.user.id;
        }

        const message = `${req.method} ${req.originalUrl || req.url} ${res.statusCode} ${duration}ms`;

        if (res.statusCode >= 500) {
            logger.error(message, logData);
        } else if (res.statusCode >= 400) {
            logger.warn(message, logData);
        } else {
            logger.http(message, logData);
        }
    });

    next();
};

/**
 * Create child logger with request context
 */
logger.child = (meta) => {
    return {
        error: (msg, m = {}) => logger.error(msg, { ...meta, ...m }),
        warn: (msg, m = {}) => logger.warn(msg, { ...meta, ...m }),
        info: (msg, m = {}) => logger.info(msg, { ...meta, ...m }),
        http: (msg, m = {}) => logger.http(msg, { ...meta, ...m }),
        debug: (msg, m = {}) => logger.debug(msg, { ...meta, ...m }),
        trace: (msg, m = {}) => logger.log('trace', msg, { ...meta, ...m })
    };
};

/**
 * Stream for Morgan integration
 */
logger.stream = {
    write: (message) => {
        logger.http(message.trim());
    }
};

/**
 * Get log statistics
 */
logger.getStats = () => {
    const files = fs.readdirSync(LOG_DIR).filter(f => f.endsWith('.log'));
    const stats = files.map(file => {
        const filePath = path.join(LOG_DIR, file);
        const stat = fs.statSync(filePath);
        return {
            name: file,
            size: stat.size,
            sizeFormatted: formatBytes(stat.size),
            modified: stat.mtime
        };
    });

    return {
        logDirectory: LOG_DIR,
        totalFiles: files.length,
        totalSize: formatBytes(stats.reduce((sum, s) => sum + s.size, 0)),
        files: stats.sort((a, b) => b.modified - a.modified)
    };
};

/**
 * Format bytes to human readable
 */
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
}

module.exports = logger;
