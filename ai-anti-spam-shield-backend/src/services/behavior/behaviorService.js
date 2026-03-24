const prisma = require('../../config/database');
const alertService = require('../alerting/alertService');

/**
 * Behavior Analysis Service (Scope 16)
 * Tracks user actions and detects anomalous behavior patterns
 */

class BehaviorService {
    /**
     * Log a user action
     */
    async logAction(userId, action, details = {}, ipAddress = null) {
        try {
            await prisma.behaviorLog.create({
                data: {
                    userId,
                    action,
                    details: details || {},
                    ipAddress,
                    riskScore: 0,
                    isAnomaly: false
                }
            });
        } catch (err) {
            console.error('Behavior log error:', err.message);
        }
    }

    /**
     * Analyze user behavior for anomalies
     */
    async analyzeUser(userId, timeframe = '24h') {
        const since = this._parseTimeframe(timeframe);

        // Get recent actions for this user
        const recentLogs = await prisma.behaviorLog.findMany({
            where: { userId, createdAt: { gte: since } },
            orderBy: { createdAt: 'desc' }
        });

        const anomalies = [];
        let riskScore = 0;

        // Check 1: Scan frequency — more than 20 scans per hour is unusual
        const scanLogs = recentLogs.filter(l => l.action === 'SCAN');
        const hourAgo = new Date(Date.now() - 3600000);
        const scansLastHour = scanLogs.filter(l => l.createdAt >= hourAgo).length;
        if (scansLastHour > 20) {
            riskScore += 0.3;
            anomalies.push({
                type: 'HIGH_SCAN_FREQUENCY',
                severity: 'MEDIUM',
                message: `${scansLastHour} scans in the last hour (threshold: 20)`,
                value: scansLastHour
            });
        }

        // Check 2: Login from new IP addresses
        const loginLogs = recentLogs.filter(l => l.action === 'LOGIN');
        const uniqueIPs = [...new Set(loginLogs.map(l => l.ipAddress).filter(Boolean))];
        // Get historical IPs (last 30 days)
        const thirtyDaysAgo = new Date(Date.now() - 30 * 86400000);
        const historicalLogins = await prisma.behaviorLog.findMany({
            where: { userId, action: 'LOGIN', createdAt: { gte: thirtyDaysAgo } },
            select: { ipAddress: true },
            distinct: ['ipAddress']
        });
        const knownIPs = new Set(historicalLogins.map(l => l.ipAddress).filter(Boolean));
        const newIPs = uniqueIPs.filter(ip => !knownIPs.has(ip));
        if (newIPs.length > 0) {
            riskScore += 0.2 * newIPs.length;
            anomalies.push({
                type: 'NEW_IP_LOGIN',
                severity: 'LOW',
                message: `Login from ${newIPs.length} new IP address(es)`,
                value: newIPs
            });
        }

        // Check 3: Unusual hours (activity between midnight and 5am)
        const unusualHourLogs = recentLogs.filter(l => {
            const hour = l.createdAt.getHours();
            return hour >= 0 && hour < 5;
        });
        if (unusualHourLogs.length > 5) {
            riskScore += 0.15;
            anomalies.push({
                type: 'UNUSUAL_HOURS',
                severity: 'LOW',
                message: `${unusualHourLogs.length} actions during unusual hours (00:00-05:00)`,
                value: unusualHourLogs.length
            });
        }

        // Check 4: Rapid file uploads
        const fileUploads = recentLogs.filter(l => l.action === 'FILE_UPLOAD');
        const uploadsLastHour = fileUploads.filter(l => l.createdAt >= hourAgo).length;
        if (uploadsLastHour > 10) {
            riskScore += 0.35;
            anomalies.push({
                type: 'RAPID_FILE_UPLOADS',
                severity: 'HIGH',
                message: `${uploadsLastHour} file uploads in the last hour`,
                value: uploadsLastHour
            });
        }

        riskScore = Math.min(1, riskScore);

        // Determine pattern summary
        const patterns = {
            loginFrequency: loginLogs.length > 10 ? 'high' : 'normal',
            dataAccessPatterns: scansLastHour > 20 ? 'abnormal' : 'normal',
            timeBasedPatterns: unusualHourLogs.length > 5 ? 'unusual' : 'normal'
        };

        // If risk is high, mark recent logs as anomalies and create an alert
        if (riskScore > 0.5) {
            await prisma.behaviorLog.updateMany({
                where: { userId, createdAt: { gte: since }, isAnomaly: false },
                data: { isAnomaly: true, riskScore }
            });

            alertService.alertSuspiciousActivity({
                userId,
                activity: anomalies.map(a => a.type).join(', '),
                riskScore,
                details: anomalies
            });
        }

        return {
            userId,
            riskScore,
            anomalies,
            patterns,
            totalActions: recentLogs.length,
            analyzedAt: new Date()
        };
    }

    /**
     * Get behavior anomalies
     */
    async getAnomalies(filters = {}) {
        const where = { isAnomaly: true };
        if (filters.userId) where.userId = filters.userId;

        const limit = parseInt(filters.limit) || 50;

        const anomalies = await prisma.behaviorLog.findMany({
            where,
            orderBy: { createdAt: 'desc' },
            take: limit
        });

        return anomalies;
    }

    /**
     * Get behavior history for a user
     */
    async getHistory(userId, startDate, endDate, limit = 50) {
        const where = { userId };
        if (startDate || endDate) {
            where.createdAt = {};
            if (startDate) where.createdAt.gte = new Date(startDate);
            if (endDate) where.createdAt.lte = new Date(endDate);
        }

        const history = await prisma.behaviorLog.findMany({
            where,
            orderBy: { createdAt: 'desc' },
            take: parseInt(limit)
        });

        return history;
    }

    /**
     * Parse timeframe string to Date
     */
    _parseTimeframe(timeframe) {
        const now = Date.now();
        const match = timeframe.match(/^(\d+)(h|d|m)$/);
        if (!match) return new Date(now - 86400000); // default 24h

        const value = parseInt(match[1]);
        const unit = match[2];
        const ms = { h: 3600000, d: 86400000, m: 60000 };
        return new Date(now - value * (ms[unit] || 86400000));
    }
}

module.exports = new BehaviorService();
