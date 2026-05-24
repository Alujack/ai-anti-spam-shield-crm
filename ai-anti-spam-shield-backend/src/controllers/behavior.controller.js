const asyncHandler = require('../utils/asyncHandler');
const behaviorService = require('../services/behavior/behaviorService');

exports.analyzeBehavior = asyncHandler(async (req, res) => {
    const userId = req.body.userId || req.user?.id;
    const timeframe = req.body.timeframe || '24h';

    if (!userId) {
        return res.status(400).json({ success: false, message: 'userId is required' });
    }

    const result = await behaviorService.analyzeUser(userId, timeframe);
    res.status(200).json({ success: true, data: result });
});

exports.getHistory = asyncHandler(async (req, res) => {
    const { userId } = req.params;
    const { startDate, endDate, limit } = req.query;

    const history = await behaviorService.getHistory(userId, startDate, endDate, limit);
    res.status(200).json({
        success: true,
        data: { history, total: history.length }
    });
});

exports.getAnomalies = asyncHandler(async (req, res) => {
    const { userId, limit } = req.query;
    const anomalies = await behaviorService.getAnomalies({ userId, limit });
    res.status(200).json({
        success: true,
        data: { anomalies, total: anomalies.length }
    });
});
