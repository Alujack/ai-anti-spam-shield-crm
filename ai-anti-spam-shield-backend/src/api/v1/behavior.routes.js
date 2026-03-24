const express = require('express');
const router = express.Router();
const authMiddleware = require('../../middlewares/auth');
const behaviorService = require('../../services/behavior/behaviorService');

/**
 * Behavior Analysis Routes (Scope 16)
 */

// POST /api/v1/behavior/analyze
router.post('/analyze', authMiddleware, async (req, res) => {
    try {
        const { userId, timeframe = '24h' } = req.body;
        const targetUserId = userId || req.user?.id;

        const analysis = await behaviorService.analyzeUser(targetUserId, timeframe);

        res.status(200).json({ success: true, data: analysis });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// GET /api/v1/behavior/history/:userId
router.get('/history/:userId', authMiddleware, async (req, res) => {
    try {
        const { userId } = req.params;
        const { startDate, endDate, limit = 50 } = req.query;

        const history = await behaviorService.getHistory(userId, startDate, endDate, limit);

        res.status(200).json({
            success: true,
            data: { userId, history, total: history.length }
        });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// GET /api/v1/behavior/anomalies
router.get('/anomalies', authMiddleware, async (req, res) => {
    try {
        const { severity, userId, limit = 20 } = req.query;

        const anomalies = await behaviorService.getAnomalies({ severity, userId, limit });

        res.status(200).json({
            success: true,
            data: { anomalies, total: anomalies.length }
        });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

module.exports = router;
