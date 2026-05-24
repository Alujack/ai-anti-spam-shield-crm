const express = require('express');
const router = express.Router();
const behaviorController = require('../controllers/behavior.controller');
const { authenticate } = require('../middlewares/auth');

router.post('/analyze', authenticate, behaviorController.analyzeBehavior);
router.get('/anomalies', authenticate, behaviorController.getAnomalies);
router.get('/history/:userId', authenticate, behaviorController.getHistory);

module.exports = router;
