const express = require('express');
const router = express.Router();
const incidentController = require('../controllers/incident.controller');
const { authenticate } = require('../middlewares/auth');

router.post('/', authenticate, incidentController.createIncident);
router.get('/', authenticate, incidentController.listIncidents);
router.get('/:id', authenticate, incidentController.getIncidentById);
router.put('/:id', authenticate, incidentController.updateIncident);
router.post('/:id/close', authenticate, incidentController.closeIncident);

module.exports = router;
