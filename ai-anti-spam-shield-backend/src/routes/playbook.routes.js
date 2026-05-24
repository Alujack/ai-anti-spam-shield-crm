const express = require('express');
const router = express.Router();
const playbookController = require('../controllers/playbook.controller');
const playbookEngine = require('../services/incidentResponse/playbooks');
const { authenticate } = require('../middlewares/auth');

router.get('/', authenticate, playbookController.getAllPlaybooks);
router.get('/executions/statistics', authenticate, playbookController.getStatistics);
router.get('/executions/history', authenticate, playbookController.getExecutionHistory);
router.get('/:id', authenticate, playbookController.getPlaybook);
router.get('/:id/history', authenticate, playbookController.getPlaybookHistory);
router.post('/:id/execute', authenticate, playbookController.executePlaybook);
router.post('/auto-execute', authenticate, playbookController.autoExecutePlaybook);

// Toggle: flip the current enabled state if no body is provided (mobile sends an
// empty POST). When the client provides { enabled }, honor it explicitly.
router.post('/:id/toggle', authenticate, async (req, res, next) => {
    try {
        if (typeof req.body?.enabled !== 'boolean') {
            const current = playbookEngine.getPlaybook(req.params.id);
            if (!current) {
                return res.status(404).json({ success: false, error: 'Playbook not found' });
            }
            req.body = { enabled: !current.enabled };
        }
        return playbookController.togglePlaybook(req, res);
    } catch (err) {
        next(err);
    }
});

module.exports = router;
