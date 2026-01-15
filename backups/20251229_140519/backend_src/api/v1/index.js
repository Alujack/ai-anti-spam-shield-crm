const express = require('express');
const router = express.Router();

// Import route modules
const threatRoutes = require('./threat.routes');
const networkRoutes = require('./network.routes');
const fileRoutes = require('./file.routes');
const behaviorRoutes = require('./behavior.routes');
const incidentRoutes = require('./incident.routes');
const analyticsRoutes = require('./analytics.routes');

// Register routes
router.use('/threats', threatRoutes);
router.use('/network', networkRoutes);
router.use('/files', fileRoutes);
router.use('/behavior', behaviorRoutes);
router.use('/incidents', incidentRoutes);
router.use('/analytics', analyticsRoutes);

module.exports = router;
