const asyncHandler = require('../utils/asyncHandler');
const ApiError = require('../utils/apiError');
const prisma = require('../config/database');

/**
 * @desc    Get list of threats
 * @route   GET /api/v1/threats
 */
exports.listThreats = asyncHandler(async (req, res) => {
    const { threatType, severity, status, page = 1, limit = 20, startDate, endDate } = req.query;

    const where = {};
    if (threatType) where.threatType = threatType;
    if (severity) where.severity = severity;
    if (status) where.status = status;
    if (startDate || endDate) {
        where.detectedAt = {};
        if (startDate) where.detectedAt.gte = new Date(startDate);
        if (endDate) where.detectedAt.lte = new Date(endDate);
    }

    const skip = (parseInt(page) - 1) * parseInt(limit);
    const [threats, total] = await Promise.all([
        prisma.threat.findMany({
            where,
            skip,
            take: parseInt(limit),
            orderBy: { detectedAt: 'desc' },
            include: { incidents: true }
        }),
        prisma.threat.count({ where })
    ]);

    res.status(200).json({
        success: true,
        data: {
            threats,
            pagination: {
                page: parseInt(page),
                limit: parseInt(limit),
                total,
                pages: Math.ceil(total / parseInt(limit))
            }
        }
    });
});

/**
 * @desc    Get threat by ID
 * @route   GET /api/v1/threats/:id
 */
exports.getThreatById = asyncHandler(async (req, res) => {
    const threat = await prisma.threat.findUnique({
        where: { id: req.params.id },
        include: { incidents: true, fileScan: true }
    });

    if (!threat) {
        throw new ApiError(404, 'Threat not found');
    }

    res.status(200).json({ success: true, data: threat });
});

/**
 * @desc    Resolve a threat
 * @route   POST /api/v1/threats/:id/resolve
 */
exports.resolveThreat = asyncHandler(async (req, res) => {
    const { resolution } = req.body;

    const threat = await prisma.threat.findUnique({ where: { id: req.params.id } });
    if (!threat) {
        throw new ApiError(404, 'Threat not found');
    }

    const updatedThreat = await prisma.threat.update({
        where: { id: req.params.id },
        data: {
            status: 'RESOLVED',
            resolvedAt: new Date(),
            resolvedBy: req.user?.id || 'system',
            resolution
        }
    });

    res.status(200).json({
        success: true,
        message: 'Threat resolved successfully',
        data: updatedThreat
    });
});

/**
 * @desc    Get threat statistics
 * @route   GET /api/v1/threats/statistics
 */
exports.getThreatStatistics = asyncHandler(async (req, res) => {
    const { startDate, endDate } = req.query;

    const where = {};
    if (startDate || endDate) {
        where.detectedAt = {};
        if (startDate) where.detectedAt.gte = new Date(startDate);
        if (endDate) where.detectedAt.lte = new Date(endDate);
    }

    const [total, byType, bySeverity, byStatus, recentThreats] = await Promise.all([
        prisma.threat.count({ where }),
        prisma.threat.groupBy({ by: ['threatType'], _count: { threatType: true }, where }),
        prisma.threat.groupBy({ by: ['severity'], _count: { severity: true }, where }),
        prisma.threat.groupBy({ by: ['status'], _count: { status: true }, where }),
        prisma.threat.findMany({ where, take: 10, orderBy: { detectedAt: 'desc' } })
    ]);

    // Convert groupBy results to maps
    const typeMap = { SPAM: 0, PHISHING: 0, MALWARE: 0, INTRUSION: 0, OTHER: 0 };
    byType.forEach(t => { typeMap[t.threatType] = t._count.threatType; });

    const severityMap = { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 };
    bySeverity.forEach(s => { severityMap[s.severity] = s._count.severity; });

    const statusMap = { DETECTED: 0, INVESTIGATING: 0, CONTAINED: 0, RESOLVED: 0, FALSE_POSITIVE: 0 };
    byStatus.forEach(s => { statusMap[s.status] = s._count.status; });

    // Daily trends for last 7 days
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
    const dailyThreats = await prisma.threat.groupBy({
        by: ['detectedAt'],
        _count: { id: true },
        where: { detectedAt: { gte: sevenDaysAgo } },
        orderBy: { detectedAt: 'asc' }
    });

    res.status(200).json({
        success: true,
        data: {
            total,
            byType: typeMap,
            bySeverity: severityMap,
            byStatus: statusMap,
            recentThreats,
            trends: {
                daily: dailyThreats.map(d => ({ date: d.detectedAt, count: d._count.id })),
                weekly: []
            }
        }
    });
});
