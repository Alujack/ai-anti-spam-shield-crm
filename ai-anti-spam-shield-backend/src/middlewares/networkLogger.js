const prisma = require('../config/database');

/**
 * Network Logger Middleware
 * Logs HTTP requests as network events for monitoring (Scope 14)
 */

// Track request counts per IP for suspicious activity detection
const ipRequestCounts = new Map();
const RATE_WINDOW_MS = 60000; // 1 minute
const RATE_THRESHOLD = 50; // requests per minute to flag as suspicious

// Track failed auth attempts per IP
const failedAuthCounts = new Map();
const FAILED_AUTH_THRESHOLD = 10;

// Enabled flag (controlled by network monitor start/stop)
let monitoringEnabled = true;

function setMonitoringEnabled(enabled) {
    monitoringEnabled = enabled;
}

function isMonitoringEnabled() {
    return monitoringEnabled;
}

/**
 * Express middleware that logs requests to NetworkEvent table
 */
function networkLoggerMiddleware(req, res, next) {
    if (!monitoringEnabled) return next();

    const startTime = Date.now();

    res.on('finish', () => {
        // Fire-and-forget: don't block the response
        logNetworkEvent(req, res, startTime).catch(err => {
            // Silently fail to avoid breaking requests
            if (process.env.NODE_ENV === 'development') {
                console.error('Network logger error:', err.message);
            }
        });
    });

    next();
}

async function logNetworkEvent(req, res, startTime) {
    const sourceIp = req.ip || req.headers['x-forwarded-for'] || req.connection?.remoteAddress || 'unknown';
    const statusCode = res.statusCode;
    const method = req.method;
    const reqPath = req.originalUrl || req.url;
    const userAgent = req.get('user-agent') || '';
    const userId = req.user?.id || null;

    // Skip health check and static asset requests
    if (reqPath === '/health' || reqPath.startsWith('/static')) return;

    // Determine if suspicious
    let isSuspicious = false;
    let riskScore = 0;
    const metadata = {};

    // Check 1: Rate-based detection
    const now = Date.now();
    const ipKey = `${sourceIp}`;
    if (!ipRequestCounts.has(ipKey)) {
        ipRequestCounts.set(ipKey, []);
    }
    const timestamps = ipRequestCounts.get(ipKey);
    timestamps.push(now);
    // Clean old entries
    while (timestamps.length > 0 && timestamps[0] < now - RATE_WINDOW_MS) {
        timestamps.shift();
    }
    if (timestamps.length > RATE_THRESHOLD) {
        isSuspicious = true;
        riskScore = Math.min(1, timestamps.length / (RATE_THRESHOLD * 2));
        metadata.reason = 'High request rate';
        metadata.requestsPerMinute = timestamps.length;
    }

    // Check 2: Failed auth attempts (401/403)
    if (statusCode === 401 || statusCode === 403) {
        if (!failedAuthCounts.has(ipKey)) {
            failedAuthCounts.set(ipKey, []);
        }
        const failedTimestamps = failedAuthCounts.get(ipKey);
        failedTimestamps.push(now);
        while (failedTimestamps.length > 0 && failedTimestamps[0] < now - RATE_WINDOW_MS) {
            failedTimestamps.shift();
        }
        if (failedTimestamps.length > FAILED_AUTH_THRESHOLD) {
            isSuspicious = true;
            riskScore = Math.max(riskScore, 0.8);
            metadata.reason = 'Brute force attempt';
            metadata.failedAttempts = failedTimestamps.length;
        }
    }

    // Check 3: Suspicious user agents
    const suspiciousAgents = ['sqlmap', 'nikto', 'nmap', 'masscan', 'dirbuster', 'gobuster'];
    const lowerAgent = userAgent.toLowerCase();
    if (suspiciousAgents.some(agent => lowerAgent.includes(agent))) {
        isSuspicious = true;
        riskScore = Math.max(riskScore, 0.9);
        metadata.reason = 'Suspicious user agent';
        metadata.userAgent = userAgent;
    }

    // Determine event type
    let eventType = 'HTTP_REQUEST';
    if (reqPath.includes('/scan') || reqPath.includes('/predict')) {
        eventType = 'SCAN_ACTIVITY';
    } else if (reqPath.includes('/login') || reqPath.includes('/register')) {
        eventType = 'AUTH_ATTEMPT';
    }
    if (isSuspicious) eventType = 'SUSPICIOUS_PATTERN';

    await prisma.networkEvent.create({
        data: {
            eventType,
            sourceIp,
            protocol: req.protocol?.toUpperCase() || 'HTTP',
            method,
            path: reqPath,
            statusCode,
            userAgent: userAgent.substring(0, 500),
            userId,
            isSuspicious,
            riskScore,
            metadata: Object.keys(metadata).length > 0 ? metadata : undefined
        }
    });
}

// Clean up in-memory maps periodically (every 5 minutes)
setInterval(() => {
    const now = Date.now();
    for (const [key, timestamps] of ipRequestCounts) {
        while (timestamps.length > 0 && timestamps[0] < now - RATE_WINDOW_MS) {
            timestamps.shift();
        }
        if (timestamps.length === 0) ipRequestCounts.delete(key);
    }
    for (const [key, timestamps] of failedAuthCounts) {
        while (timestamps.length > 0 && timestamps[0] < now - RATE_WINDOW_MS) {
            timestamps.shift();
        }
        if (timestamps.length === 0) failedAuthCounts.delete(key);
    }
}, 300000);

module.exports = { networkLoggerMiddleware, setMonitoringEnabled, isMonitoringEnabled };
