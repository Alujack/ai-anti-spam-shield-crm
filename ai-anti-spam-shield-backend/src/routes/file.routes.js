const express = require('express');
const router = express.Router();
const fileController = require('../controllers/file.controller');
const { authenticate } = require('../middlewares/auth');
const fileUpload = require('../middlewares/fileUpload');

router.post('/scan', authenticate, fileUpload.single('file'), fileController.scanFile);
router.get('/statistics', authenticate, fileController.getFileStatistics);
router.get('/scan/:id', authenticate, fileController.getScanResult);
router.post('/quarantine', authenticate, fileController.quarantineFile);

module.exports = router;
