const express = require('express');
const router = express.Router();
const threatController = require('../controllers/threat.controller');
const { authenticate } = require('../middlewares/auth');

router.get('/statistics', authenticate, threatController.getThreatStatistics);
router.get('/', authenticate, threatController.listThreats);
router.get('/:id', authenticate, threatController.getThreatById);
router.post('/:id/resolve', authenticate, threatController.resolveThreat);

module.exports = router;
