const asyncHandler = require('../utils/asyncHandler');
const networkMonitor = require('../services/networkMonitor/monitor');

exports.startMonitoring = asyncHandler(async (req, res) => {
    const result = await networkMonitor.startMonitoring();
    res.status(200).json({ success: true, data: result });
});

exports.stopMonitoring = asyncHandler(async (req, res) => {
    const result = await networkMonitor.stopMonitoring();
    res.status(200).json({ success: true, data: result });
});

exports.getStatus = asyncHandler(async (req, res) => {
    const status = networkMonitor.getStatus();
    res.status(200).json({ success: true, data: status });
});

exports.getEvents = asyncHandler(async (req, res) => {
    const { suspicious, eventType, sourceIp, page, limit, startDate, endDate } = req.query;
    const events = await networkMonitor.getEvents({
        isSuspicious: suspicious,
        eventType,
        sourceIp,
        page,
        limit,
        startDate,
        endDate
    });
    res.status(200).json({ success: true, data: events });
});

exports.getStatistics = asyncHandler(async (req, res) => {
    const stats = await networkMonitor.getStatistics();
    res.status(200).json({ success: true, data: stats });
});
