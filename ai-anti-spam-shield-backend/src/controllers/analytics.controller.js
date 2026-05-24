const asyncHandler = require('../utils/asyncHandler');
const prisma = require('../config/database');

function parseTimeframe(timeframe) {
    const match = /^(\d+)([hdm])$/.exec(timeframe || '7d');
    if (!match) return new Date(Date.now() - 7 * 86400000);
    const value = parseInt(match[1]);
    const unit = match[2];
    const ms = { h: 3600000, d: 86400000, m: 60000 }[unit] || 86400000;
    return new Date(Date.now() - value * ms);
}

exports.getDashboard = asyncHandler(async (req, res) => {
    const timeframe = req.query.timeframe || '7d';
    const since = parseTimeframe(timeframe);

    const [
        totalScans,
        totalThreatsDetected,
        spamCount,
        phishingScans,
        voiceScans,
        threatsByType,
        scansByDay,
        threatsByDay
    ] = await Promise.all([
        prisma.scanHistory.count({ where: { scannedAt: { gte: since } } }),
        prisma.threat.count({ where: { detectedAt: { gte: since } } }),
        prisma.scanHistory.count({ where: { scannedAt: { gte: since }, isSpam: true } }),
        prisma.phishingScanHistory.count({ where: { scannedAt: { gte: since } } }),
        prisma.scanHistory.count({ where: { scannedAt: { gte: since }, scanType: 'voice' } }).catch(() => 0),
        prisma.threat.groupBy({
            by: ['threatType'],
            _count: { threatType: true },
            where: { detectedAt: { gte: since } }
        }),
        prisma.scanHistory.findMany({
            where: { scannedAt: { gte: since } },
            select: { scannedAt: true, isSpam: true }
        }),
        prisma.threat.findMany({
            where: { detectedAt: { gte: since } },
            select: { detectedAt: true }
        })
    ]);

    // Build daily aggregations
    const dailyMap = new Map();
    scansByDay.forEach(s => {
        const day = s.scannedAt.toISOString().slice(0, 10);
        if (!dailyMap.has(day)) dailyMap.set(day, { date: day, scans: 0, threats: 0 });
        dailyMap.get(day).scans++;
    });
    threatsByDay.forEach(t => {
        const day = t.detectedAt.toISOString().slice(0, 10);
        if (!dailyMap.has(day)) dailyMap.set(day, { date: day, scans: 0, threats: 0 });
        dailyMap.get(day).threats++;
    });
    const recentActivity = Array.from(dailyMap.values()).sort((a, b) =>
        a.date.localeCompare(b.date)
    );

    const topThreatTypes = threatsByType
        .map(t => ({ type: t.threatType, count: t._count.threatType }))
        .sort((a, b) => b.count - a.count);

    res.status(200).json({
        success: true,
        data: {
            timeframe,
            totalScans,
            totalThreatsDetected,
            spamCaught: spamCount,
            phishingCaught: phishingScans,
            voiceScamsCaught: voiceScans,
            falsePositiveRate: 0,
            avgLatencyMs: 0,
            voiceLatencyMs: 0,
            modelAccuracy: { sms: 0, voice: 0, phishing: 0 },
            topThreatTypes,
            recentActivity
        }
    });
});

exports.exportAnalytics = asyncHandler(async (req, res) => {
    const format = req.query.format || 'json';
    const dataType = req.query.dataType || 'threats';

    let rows = [];
    if (dataType === 'threats') {
        rows = await prisma.threat.findMany({ orderBy: { detectedAt: 'desc' }, take: 1000 });
    } else if (dataType === 'scans') {
        rows = await prisma.scanHistory.findMany({ orderBy: { scannedAt: 'desc' }, take: 1000 });
    } else if (dataType === 'alerts') {
        rows = await prisma.alert.findMany({ orderBy: { createdAt: 'desc' }, take: 1000 });
    } else if (dataType === 'incidents') {
        rows = await prisma.incident.findMany({ orderBy: { createdAt: 'desc' }, take: 1000 });
    }

    res.status(200).json({
        success: true,
        data: { rows, count: rows.length, format, dataType }
    });
});
