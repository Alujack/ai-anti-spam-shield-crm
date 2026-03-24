const express = require('express');
const router = express.Router();
const authMiddleware = require('../../middlewares/auth');
const alertingService = require('../../services/alerting/alertService');

/**
 * Alerting Routes
 * Handles security alerts and notifications
 */

// GET /api/v1/alerts/statistics/summary - MUST be before /:id
router.get('/statistics/summary', authMiddleware, async (req, res) => {
    try {
        const statistics = await alertingService.getStatistics();
        res.status(200).json({ success: true, data: statistics });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// POST /api/v1/alerts/clear-resolved - MUST be before /:id
router.post('/clear-resolved', authMiddleware, async (req, res) => {
    try {
        const result = await alertingService.clearResolvedAlerts();
        res.status(200).json({ success: true, data: result });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// GET /api/v1/alerts
router.get('/', authMiddleware, async (req, res) => {
    try {
        const { status, severity, category, source } = req.query;
        const filters = {};
        if (status) filters.status = status.toUpperCase();
        if (severity) filters.severity = severity;
        if (category) filters.category = category;
        if (source) filters.source = source;

        const alerts = filters.status === 'ACTIVE'
            ? await alertingService.getActiveAlerts(filters)
            : await alertingService.getAllAlerts(filters);

        res.status(200).json({
            success: true,
            data: { alerts, total: alerts.length }
        });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// GET /api/v1/alerts/:id
router.get('/:id', authMiddleware, async (req, res) => {
    try {
        const alert = await alertingService.getAlertById(req.params.id);
        if (!alert) {
            return res.status(404).json({ success: false, message: 'Alert not found' });
        }
        res.status(200).json({ success: true, data: alert });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// POST /api/v1/alerts/:id/acknowledge
router.post('/:id/acknowledge', authMiddleware, async (req, res) => {
    try {
        const userId = req.user?.id || 'system';
        const alert = await alertingService.acknowledgeAlert(req.params.id, userId);
        if (!alert) {
            return res.status(404).json({ success: false, message: 'Alert not found' });
        }
        res.status(200).json({ success: true, message: 'Alert acknowledged', data: alert });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// POST /api/v1/alerts/:id/resolve
router.post('/:id/resolve', authMiddleware, async (req, res) => {
    try {
        const { resolution } = req.body;
        const userId = req.user?.id || 'system';
        const alert = await alertingService.resolveAlert(req.params.id, userId, resolution);
        if (!alert) {
            return res.status(404).json({ success: false, message: 'Alert not found' });
        }
        res.status(200).json({ success: true, message: 'Alert resolved', data: alert });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

module.exports = router;
