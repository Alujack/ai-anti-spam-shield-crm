const express = require('express');
const router = express.Router();
const threatController = require('../../controllers/threat.controller');
const authMiddleware = require('../../middlewares/auth');

// Statistics must be before /:id to avoid matching "statistics" as an ID
router.get('/statistics', authMiddleware, threatController.getThreatStatistics);
router.get('/', authMiddleware, threatController.listThreats);
router.get('/:id', authMiddleware, threatController.getThreatById);
router.post('/:id/resolve', authMiddleware, threatController.resolveThreat);

module.exports = router;
