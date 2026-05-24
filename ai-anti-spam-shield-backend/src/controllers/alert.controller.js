const asyncHandler = require('../utils/asyncHandler');
const ApiError = require('../utils/apiError');
const alertService = require('../services/alerting/alertService');

exports.listAlerts = asyncHandler(async (req, res) => {
    const { status, severity, category } = req.query;
    const alerts = await alertService.getAllAlerts({ status, severity, category });
    res.status(200).json({
        success: true,
        data: { alerts, total: alerts.length }
    });
});

exports.getAlertById = asyncHandler(async (req, res) => {
    const alert = await alertService.getAlertById(req.params.id);
    if (!alert) throw new ApiError(404, 'Alert not found');
    res.status(200).json({ success: true, data: alert });
});

exports.acknowledgeAlert = asyncHandler(async (req, res) => {
    const alert = await alertService.acknowledgeAlert(req.params.id, req.user?.id || 'system');
    if (!alert) throw new ApiError(404, 'Alert not found');
    res.status(200).json({ success: true, data: alert });
});

exports.resolveAlert = asyncHandler(async (req, res) => {
    const { resolution } = req.body;
    const alert = await alertService.resolveAlert(
        req.params.id,
        req.user?.id || 'system',
        resolution
    );
    if (!alert) throw new ApiError(404, 'Alert not found');
    res.status(200).json({ success: true, data: alert });
});

exports.getAlertStatistics = asyncHandler(async (req, res) => {
    const stats = await alertService.getStatistics();
    res.status(200).json({ success: true, data: stats });
});
