const express = require('express');
const router = express.Router();
const analyticsController = require('../controllers/analytics.controller');
const { authenticate } = require('../middlewares/auth');

router.get('/dashboard', authenticate, analyticsController.getDashboard);
router.get('/export', authenticate, analyticsController.exportAnalytics);

module.exports = router;
