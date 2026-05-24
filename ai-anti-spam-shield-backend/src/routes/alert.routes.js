const express = require('express');
const router = express.Router();
const alertController = require('../controllers/alert.controller');
const { authenticate } = require('../middlewares/auth');

router.get('/statistics/summary', authenticate, alertController.getAlertStatistics);
router.get('/', authenticate, alertController.listAlerts);
router.get('/:id', authenticate, alertController.getAlertById);
router.post('/:id/acknowledge', authenticate, alertController.acknowledgeAlert);
router.post('/:id/resolve', authenticate, alertController.resolveAlert);

module.exports = router;
