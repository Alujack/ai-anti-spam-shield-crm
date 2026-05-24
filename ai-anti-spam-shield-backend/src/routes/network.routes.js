const express = require('express');
const router = express.Router();
const networkController = require('../controllers/network.controller');
const { authenticate } = require('../middlewares/auth');

router.post('/start', authenticate, networkController.startMonitoring);
router.post('/stop', authenticate, networkController.stopMonitoring);
router.get('/status', authenticate, networkController.getStatus);
router.get('/events', authenticate, networkController.getEvents);
router.get('/statistics', authenticate, networkController.getStatistics);

module.exports = router;
