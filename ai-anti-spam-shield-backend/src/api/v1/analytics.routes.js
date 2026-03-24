const express = require('express');
const router = express.Router();
const authMiddleware = require('../../middlewares/auth');
const prisma = require('../../config/database');

/**
 * Analytics Routes (Scope 8)
 * Real aggregation queries across all tables
 */

// GET /api/v1/analytics/dashboard
router.get('/dashboard', authMiddleware, async (req, res) => {
    try {
        const { timeframe = '7d' } = req.query;
        const since = parseTimeframe(timeframe);

        const [
            totalThreats, activeIncidents, filesScanned, networkEvents,
            bySeverity, recentScans, recentThreats,
            totalScans, totalPhishing, totalReports
        ] = await Promise.all([
            prisma.threat.count({ where: { detectedAt: { gte: since } } }),
            prisma.incident.count({ where: { status: { in: ['OPEN', 'INVESTIGATING'] } } }),
            prisma.fileScan.count({ where: { scannedAt: { gte: since } } }),
            prisma.networkEvent.count({ where: { createdAt: { gte: since } } }),
            prisma.threat.groupBy({ by: ['severity'], _count: { severity: true }, where: { detectedAt: { gte: since } } }),
            prisma.scanHistory.findMany({ orderBy: { scannedAt: 'desc' }, take: 10, select: { id: true, isSpam: true, scanType: true, confidence: true, scannedAt: true } }),
            prisma.threat.findMany({ orderBy: { detectedAt: 'desc' }, take: 5, select: { id: true, threatType: true, severity: true, status: true, confidenceScore: true, detectedAt: true } }),
            prisma.scanHistory.count({ where: { scannedAt: { gte: since } } }),
            prisma.phishingScanHistory.count({ where: { scannedAt: { gte: since } } }),
            prisma.report.count({ where: { createdAt: { gte: since } } })
        ]);

        const severityMap = { low: 0, medium: 0, high: 0, critical: 0 };
        bySeverity.forEach(s => { severityMap[s.severity.toLowerCase()] = s._count.severity; });

        // Build recent activity combining scans and threats
        const recentActivity = [
            ...recentScans.map(s => ({ type: 'scan', ...s })),
            ...recentThreats.map(t => ({ type: 'threat', ...t }))
        ].sort((a, b) => new Date(b.scannedAt || b.detectedAt) - new Date(a.scannedAt || a.detectedAt)).slice(0, 10);

        res.status(200).json({
            success: true,
            data: {
                overview: { totalThreats, activeIncidents, filesScanned, networkEvents, totalScans, totalPhishing, totalReports },
                severityDistribution: severityMap,
                topThreats: recentThreats,
                recentActivity
            }
        });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// GET /api/v1/analytics/threats
router.get('/threats', authMiddleware, async (req, res) => {
    try {
        const { startDate, endDate } = req.query;
        const where = {};
        if (startDate || endDate) {
            where.detectedAt = {};
            if (startDate) where.detectedAt.gte = new Date(startDate);
            if (endDate) where.detectedAt.lte = new Date(endDate);
        }

        const [totalDetected, byType, bySeverity, bySource, avgConf] = await Promise.all([
            prisma.threat.count({ where }),
            prisma.threat.groupBy({ by: ['threatType'], _count: { threatType: true }, where }),
            prisma.threat.groupBy({ by: ['severity'], _count: { severity: true }, where }),
            prisma.threat.groupBy({ by: ['source'], _count: { source: true }, where }),
            prisma.threat.aggregate({ _avg: { confidenceScore: true }, where })
        ]);

        const typeMap = {};
        byType.forEach(t => { typeMap[t.threatType] = t._count.threatType; });
        const sevMap = {};
        bySeverity.forEach(s => { sevMap[s.severity] = s._count.severity; });
        const srcMap = {};
        bySource.forEach(s => { if (s.source) srcMap[s.source] = s._count.source; });

        res.status(200).json({
            success: true,
            data: {
                totalDetected,
                byType: typeMap,
                bySeverity: sevMap,
                bySource: srcMap,
                avgConfidenceScore: avgConf._avg.confidenceScore || 0
            }
        });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// GET /api/v1/analytics/users
router.get('/users', authMiddleware, async (req, res) => {
    try {
        const thirtyDaysAgo = new Date(Date.now() - 30 * 86400000);

        const [totalUsers, newUsers, activeUserResult] = await Promise.all([
            prisma.user.count(),
            prisma.user.count({ where: { createdAt: { gte: thirtyDaysAgo } } }),
            prisma.scanHistory.groupBy({
                by: ['userId'],
                where: { scannedAt: { gte: thirtyDaysAgo } }
            })
        ]);

        // Top users by scan count
        const topUsers = await prisma.scanHistory.groupBy({
            by: ['userId'],
            _count: { id: true },
            orderBy: { _count: { id: 'desc' } },
            take: 10
        });

        res.status(200).json({
            success: true,
            data: {
                totalUsers,
                activeUsers: activeUserResult.length,
                newUsers,
                topUsers: topUsers.map(u => ({ userId: u.userId, scanCount: u._count.id }))
            }
        });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// POST /api/v1/analytics/report
router.post('/report', authMiddleware, async (req, res) => {
    try {
        const { reportType = 'general', startDate, endDate } = req.body;
        const where = {};
        if (startDate || endDate) {
            where.detectedAt = {};
            if (startDate) where.detectedAt.gte = new Date(startDate);
            if (endDate) where.detectedAt.lte = new Date(endDate);
        }

        let data = {};

        if (reportType === 'threats' || reportType === 'general') {
            const [total, byType, bySeverity] = await Promise.all([
                prisma.threat.count({ where }),
                prisma.threat.groupBy({ by: ['threatType'], _count: { threatType: true }, where }),
                prisma.threat.groupBy({ by: ['severity'], _count: { severity: true }, where })
            ]);
            data.threats = { total, byType, bySeverity };
        }

        if (reportType === 'scans' || reportType === 'general') {
            const scanWhere = {};
            if (startDate) scanWhere.scannedAt = { gte: new Date(startDate) };
            const [totalScans, spamCount] = await Promise.all([
                prisma.scanHistory.count({ where: scanWhere }),
                prisma.scanHistory.count({ where: { ...scanWhere, isSpam: true } })
            ]);
            data.scans = { totalScans, spamCount, safeCount: totalScans - spamCount };
        }

        if (reportType === 'incidents' || reportType === 'general') {
            const [totalIncidents, byStatus] = await Promise.all([
                prisma.incident.count(),
                prisma.incident.groupBy({ by: ['status'], _count: { status: true } })
            ]);
            data.incidents = { totalIncidents, byStatus };
        }

        res.status(200).json({
            success: true,
            message: 'Report generated successfully',
            data: {
                id: 'report-' + Date.now(),
                type: reportType,
                startDate, endDate,
                generatedAt: new Date(),
                data,
                summary: `Report generated with ${Object.keys(data).length} sections`
            }
        });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// GET /api/v1/analytics/export
router.get('/export', authMiddleware, async (req, res) => {
    try {
        const { format = 'json', dataType = 'threats' } = req.query;

        let rows = [];
        if (dataType === 'threats') {
            rows = await prisma.threat.findMany({ orderBy: { detectedAt: 'desc' }, take: 1000 });
        } else if (dataType === 'scans') {
            rows = await prisma.scanHistory.findMany({ orderBy: { scannedAt: 'desc' }, take: 1000 });
        } else if (dataType === 'incidents') {
            rows = await prisma.incident.findMany({ orderBy: { createdAt: 'desc' }, take: 1000 });
        } else if (dataType === 'alerts') {
            rows = await prisma.alert.findMany({ orderBy: { createdAt: 'desc' }, take: 1000 });
        }

        if (format === 'csv') {
            if (rows.length === 0) {
                res.setHeader('Content-Type', 'text/csv');
                return res.send('No data');
            }
            const headers = Object.keys(rows[0]);
            const csvLines = [
                headers.join(','),
                ...rows.map(row => headers.map(h => {
                    const val = row[h];
                    if (val === null || val === undefined) return '';
                    const str = typeof val === 'object' ? JSON.stringify(val) : String(val);
                    return `"${str.replace(/"/g, '""')}"`;
                }).join(','))
            ];
            res.setHeader('Content-Type', 'text/csv');
            res.setHeader('Content-Disposition', `attachment; filename=${dataType}-export.csv`);
            return res.send(csvLines.join('\n'));
        }

        // Default: JSON
        res.status(200).json({
            success: true,
            data: { format: 'json', dataType, count: rows.length, rows }
        });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

function parseTimeframe(timeframe) {
    const match = timeframe.match(/^(\d+)(h|d|w|m)$/);
    if (!match) return new Date(Date.now() - 7 * 86400000);
    const value = parseInt(match[1]);
    const unit = match[2];
    const ms = { h: 3600000, d: 86400000, w: 604800000, m: 2592000000 };
    return new Date(Date.now() - value * (ms[unit] || 86400000));
}

module.exports = router;
