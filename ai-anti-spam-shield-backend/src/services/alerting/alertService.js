const EventEmitter = require('events');
const prisma = require('../../config/database');

/**
 * Alerting Service
 * Manages security alerts and notifications with database persistence
 */

class AlertingService extends EventEmitter {
    constructor() {
        super();
        this.subscribers = new Map();

        // Alert severity levels
        this.SEVERITY = {
            LOW: 'LOW',
            MEDIUM: 'MEDIUM',
            HIGH: 'HIGH',
            CRITICAL: 'CRITICAL'
        };

        // Alert categories
        this.CATEGORY = {
            THREAT_DETECTED: 'THREAT_DETECTED',
            INTRUSION_ATTEMPT: 'INTRUSION_ATTEMPT',
            MALWARE_FOUND: 'MALWARE_FOUND',
            SUSPICIOUS_ACTIVITY: 'SUSPICIOUS_ACTIVITY',
            SYSTEM_ERROR: 'SYSTEM_ERROR',
            DATA_BREACH: 'DATA_BREACH',
            POLICY_VIOLATION: 'POLICY_VIOLATION'
        };

        // Initialize event listeners
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.on('alert', (alert) => {
            console.log(`[ALERT] ${alert.severity} - ${alert.title}`);
            this.notifySubscribers(alert);
        });
    }

    /**
     * Create and trigger a new alert (persisted to DB)
     */
    createAlert({
        title,
        description,
        severity = this.SEVERITY.MEDIUM,
        category,
        source,
        metadata = {},
        autoResolve = false,
        resolveAfter = 3600000
    }) {
        const alertData = {
            title: title || 'Untitled Alert',
            description,
            severity,
            category: category || 'SUSPICIOUS_ACTIVITY',
            source,
            metadata: metadata || {},
            status: 'ACTIVE',
            createdAt: new Date()
        };

        // Persist to database (fire-and-forget to keep method sync-compatible)
        prisma.alert.create({ data: alertData }).then(dbAlert => {
            alertData.id = dbAlert.id;

            // Emit alert event
            this.emit('alert', alertData);

            // Auto-resolve if configured
            if (autoResolve) {
                setTimeout(() => {
                    this.resolveAlert(dbAlert.id, 'system', 'Auto-resolved after timeout');
                }, resolveAfter);
            }
        }).catch(err => {
            console.error('Failed to persist alert:', err.message);
            // Still emit the event even if DB fails
            alertData.id = `alert-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            this.emit('alert', alertData);
        });

        return alertData;
    }

    /**
     * Create threat detection alert
     */
    alertThreatDetected({ threatType, severity, confidence, source, details }) {
        return this.createAlert({
            title: `${threatType} Threat Detected`,
            description: `A ${threatType.toLowerCase()} threat was detected with ${(confidence * 100).toFixed(1)}% confidence.`,
            severity,
            category: this.CATEGORY.THREAT_DETECTED,
            source,
            metadata: { threatType, confidence, details }
        });
    }

    /**
     * Create malware detection alert
     */
    alertMalwareFound({ fileName, fileHash, severity, scanResult, virusTotalScore }) {
        return this.createAlert({
            title: 'Malware Detected',
            description: `File "${fileName}" was flagged as malicious.`,
            severity: severity || this.SEVERITY.HIGH,
            category: this.CATEGORY.MALWARE_FOUND,
            source: 'file_scanner',
            metadata: { fileName, fileHash, scanResult, virusTotalScore }
        });
    }

    /**
     * Create intrusion attempt alert
     */
    alertIntrusionAttempt({ sourceIp, attackType, severity, details }) {
        return this.createAlert({
            title: `${attackType || 'Network'} Intrusion Attempt`,
            description: `Intrusion attempt detected from IP ${sourceIp}`,
            severity: severity || this.SEVERITY.HIGH,
            category: this.CATEGORY.INTRUSION_ATTEMPT,
            source: 'network_monitor',
            metadata: { sourceIp, attackType, details }
        });
    }

    /**
     * Create suspicious activity alert
     */
    alertSuspiciousActivity({ userId, activity, riskScore, details }) {
        return this.createAlert({
            title: 'Suspicious User Activity',
            description: `Unusual activity detected for user ${userId}`,
            severity: riskScore > 0.7 ? this.SEVERITY.HIGH : this.SEVERITY.MEDIUM,
            category: this.CATEGORY.SUSPICIOUS_ACTIVITY,
            source: 'behavior_analyzer',
            metadata: { userId, activity, riskScore, details }
        });
    }

    /**
     * Get active alerts from database
     */
    async getActiveAlerts(filters = {}) {
        const where = { status: 'ACTIVE' };
        if (filters.severity) where.severity = filters.severity;
        if (filters.category) where.category = filters.category;
        if (filters.source) where.source = filters.source;

        return prisma.alert.findMany({
            where,
            orderBy: { createdAt: 'desc' },
            take: 100
        });
    }

    /**
     * Get all alerts with optional filters
     */
    async getAllAlerts(filters = {}) {
        const where = {};
        if (filters.status) where.status = filters.status;
        if (filters.severity) where.severity = filters.severity;
        if (filters.category) where.category = filters.category;

        return prisma.alert.findMany({
            where,
            orderBy: { createdAt: 'desc' },
            take: 200
        });
    }

    /**
     * Get alert by ID
     */
    async getAlertById(alertId) {
        return prisma.alert.findUnique({ where: { id: alertId } });
    }

    /**
     * Acknowledge alert
     */
    async acknowledgeAlert(alertId, userId) {
        try {
            const alert = await prisma.alert.update({
                where: { id: alertId },
                data: {
                    acknowledgedAt: new Date(),
                    acknowledgedBy: userId
                }
            });
            this.emit('alert_acknowledged', alert);
            return alert;
        } catch (err) {
            return null;
        }
    }

    /**
     * Resolve alert
     */
    async resolveAlert(alertId, userId, resolution) {
        try {
            const alert = await prisma.alert.update({
                where: { id: alertId },
                data: {
                    status: 'RESOLVED',
                    resolvedAt: new Date(),
                    resolvedBy: userId,
                    resolution
                }
            });
            this.emit('alert_resolved', alert);
            return alert;
        } catch (err) {
            return null;
        }
    }

    /**
     * Subscribe to alerts
     */
    subscribe(subscriberId, callback) {
        this.subscribers.set(subscriberId, callback);
        return () => this.unsubscribe(subscriberId);
    }

    unsubscribe(subscriberId) {
        return this.subscribers.delete(subscriberId);
    }

    notifySubscribers(alert) {
        this.subscribers.forEach((callback, subscriberId) => {
            try {
                callback(alert);
            } catch (error) {
                console.error(`Error notifying subscriber ${subscriberId}:`, error);
            }
        });
    }

    /**
     * Get alert statistics from database
     */
    async getStatistics() {
        const [total, active, resolved, bySeverity, byCategory, recent] = await Promise.all([
            prisma.alert.count(),
            prisma.alert.count({ where: { status: 'ACTIVE' } }),
            prisma.alert.count({ where: { status: 'RESOLVED' } }),
            prisma.alert.groupBy({ by: ['severity'], _count: { severity: true } }),
            prisma.alert.groupBy({ by: ['category'], _count: { category: true } }),
            prisma.alert.findMany({ orderBy: { createdAt: 'desc' }, take: 10 })
        ]);

        const severityMap = { low: 0, medium: 0, high: 0, critical: 0 };
        bySeverity.forEach(s => { severityMap[s.severity.toLowerCase()] = s._count.severity; });

        const categoryMap = {};
        byCategory.forEach(c => { categoryMap[c.category.toLowerCase()] = c._count.category; });

        return {
            total,
            active,
            resolved,
            bySeverity: severityMap,
            byCategory: categoryMap,
            recent
        };
    }

    /**
     * Clear resolved alerts from database
     */
    async clearResolvedAlerts() {
        const result = await prisma.alert.deleteMany({ where: { status: 'RESOLVED' } });
        return {
            message: `Cleared ${result.count} resolved alerts`,
            cleared: result.count
        };
    }
}

module.exports = new AlertingService();
