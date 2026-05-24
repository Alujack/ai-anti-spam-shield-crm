const express = require('express');
const router = express.Router();

const messageRoutes = require('./message.routes');
const userRoutes = require('./user.routes');
const reportRoutes = require('./report.routes');
const phishingRoutes = require('./phishing.routes');
const jobRoutes = require('./job.routes');
const feedbackRoutes = require('./feedback.routes');
const emailRoutes = require('./email.routes');
const subscriptionRoutes = require('./subscription.routes');
const threatRoutes = require('./threat.routes');
const incidentRoutes = require('./incident.routes');
const alertRoutes = require('./alert.routes');
const playbookRoutes = require('./playbook.routes');
const networkRoutes = require('./network.routes');
const fileRoutes = require('./file.routes');
const behaviorRoutes = require('./behavior.routes');
const analyticsRoutes = require('./analytics.routes');

// Mount routes
router.use('/messages', messageRoutes);
router.use('/users', userRoutes);
router.use('/reports', reportRoutes);
router.use('/phishing', phishingRoutes);
router.use('/jobs', jobRoutes);
router.use('/feedback', feedbackRoutes);
router.use('/emails', emailRoutes);
router.use('/subscriptions', subscriptionRoutes);
router.use('/threats', threatRoutes);
router.use('/incidents', incidentRoutes);
router.use('/alerts', alertRoutes);
router.use('/playbooks', playbookRoutes);
router.use('/network', networkRoutes);
router.use('/files', fileRoutes);
router.use('/behavior', behaviorRoutes);
router.use('/analytics', analyticsRoutes);

// API info endpoint
router.get('/', (req, res) => {
  res.json({
    status: 'success',
    message: 'AI Anti-Spam Shield API',
    version: '1.0.0',
    endpoints: {
      messages: '/api/v1/messages',
      users: '/api/v1/users',
      reports: '/api/v1/reports',
      phishing: '/api/v1/phishing',
      jobs: '/api/v1/jobs',
      feedback: '/api/v1/feedback',
      emails: '/api/v1/emails',
      subscriptions: '/api/v1/subscriptions',
      threats: '/api/v1/threats',
      incidents: '/api/v1/incidents',
      alerts: '/api/v1/alerts',
      playbooks: '/api/v1/playbooks',
      network: '/api/v1/network',
      files: '/api/v1/files',
      behavior: '/api/v1/behavior',
      analytics: '/api/v1/analytics'
    }
  });
});

module.exports = router;
