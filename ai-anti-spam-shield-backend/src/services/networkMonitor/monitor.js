const prisma = require('../../config/database');
const { setMonitoringEnabled, isMonitoringEnabled } = require('../../middlewares/networkLogger');

/**
 * Network Monitoring Service
 * Monitors network traffic via HTTP request logging (Scope 14)
 */

class NetworkMonitor {
    async startMonitoring() {
        setMonitoringEnabled(true);
        console.log('Network monitoring started');
        return { success: true, message: 'Monitoring started' };
    }

    async stopMonitoring() {
        setMonitoringEnabled(false);
        console.log('Network monitoring stopped');
        return { success: true, message: 'Monitoring stopped' };
    }

    getStatus() {
        return {
            isMonitoring: isMonitoringEnabled(),
            startedAt: isMonitoringEnabled() ? new Date() : null
        };
    }

    async getEvents(filters = {}) {
        const where = {};
        if (filters.isSuspicious !== undefined) {
            where.isSuspicious = filters.isSuspicious === 'true' || filters.isSuspicious === true;
        }
        if (filters.eventType) where.eventType = filters.eventType;
        if (filters.sourceIp) where.sourceIp = filters.sourceIp;
        if (filters.startDate || filters.endDate) {
            where.createdAt = {};
            if (filters.startDate) where.createdAt.gte = new Date(filters.startDate);
            if (filters.endDate) where.createdAt.lte = new Date(filters.endDate);
        }

        const page = parseInt(filters.page) || 1;
        const limit = parseInt(filters.limit) || 50;

        const [events, total, suspicious] = await Promise.all([
            prisma.networkEvent.findMany({
                where,
                orderBy: { createdAt: 'desc' },
                skip: (page - 1) * limit,
                take: limit
            }),
            prisma.networkEvent.count({ where }),
            prisma.networkEvent.count({ where: { ...where, isSuspicious: true } })
        ]);

        return { events, total, suspicious };
    }

    async getStatistics() {
        const [totalEvents, suspiciousEvents, byEventType, byProtocol, topSources] = await Promise.all([
            prisma.networkEvent.count(),
            prisma.networkEvent.count({ where: { isSuspicious: true } }),
            prisma.networkEvent.groupBy({ by: ['eventType'], _count: { eventType: true } }),
            prisma.networkEvent.groupBy({ by: ['protocol'], _count: { protocol: true } }),
            prisma.$queryRaw`
                SELECT "sourceIp" as ip, COUNT(*)::int as count
                FROM network_events
                GROUP BY "sourceIp"
                ORDER BY count DESC
                LIMIT 10
            `
        ]);

        const protocols = {};
        byProtocol.forEach(p => { if (p.protocol) protocols[p.protocol] = p._count.protocol; });

        const eventTypes = {};
        byEventType.forEach(e => { eventTypes[e.eventType] = e._count.eventType; });

        return {
            totalEvents,
            suspiciousEvents,
            protocols,
            eventTypes,
            topSources: topSources || [],
            isMonitoring: isMonitoringEnabled()
        };
    }
}

module.exports = new NetworkMonitor();
