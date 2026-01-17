const express = require('express');
const router = express.Router();
const messageController = require('../controllers/message.controller');
const { authenticate, optionalAuthenticate } = require('../middlewares/auth');
const upload = require('../middlewares/upload');

/**
 * @swagger
 * /messages/scan-text:
 *   post:
 *     summary: Scan text message for spam
 *     tags: [Messages]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/ScanTextRequest'
 *     responses:
 *       200:
 *         description: Scan result
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/ScanResult'
 */
router.post('/scan-text', optionalAuthenticate, messageController.scanText);

/**
 * @swagger
 * /messages/scan-voice:
 *   post:
 *     summary: Scan voice message for spam
 *     tags: [Messages]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         multipart/form-data:
 *           schema:
 *             type: object
 *             properties:
 *               audio:
 *                 type: string
 *                 format: binary
 *                 description: Audio file to scan
 *     responses:
 *       200:
 *         description: Scan result
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/ScanResult'
 */
router.post('/scan-voice', optionalAuthenticate, upload.single('audio'), messageController.scanVoice);

/**
 * @swagger
 * /messages/history:
 *   get:
 *     summary: Get scan history
 *     tags: [Messages]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: page
 *         schema:
 *           type: integer
 *           default: 1
 *       - in: query
 *         name: limit
 *         schema:
 *           type: integer
 *           default: 10
 *     responses:
 *       200:
 *         description: Scan history list
 *       401:
 *         description: Unauthorized
 */
router.get('/history', authenticate, messageController.getScanHistory);

/**
 * @swagger
 * /messages/history/{id}:
 *   get:
 *     summary: Get scan history by ID
 *     tags: [Messages]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Scan history detail
 *       401:
 *         description: Unauthorized
 *       404:
 *         description: Not found
 */
router.get('/history/:id', authenticate, messageController.getScanHistoryById);

/**
 * @swagger
 * /messages/history/{id}:
 *   delete:
 *     summary: Delete scan history
 *     tags: [Messages]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Deleted successfully
 *       401:
 *         description: Unauthorized
 */
router.delete('/history/:id', authenticate, messageController.deleteScanHistory);

/**
 * @swagger
 * /messages/statistics:
 *   get:
 *     summary: Get scan statistics
 *     tags: [Messages]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Scan statistics
 *       401:
 *         description: Unauthorized
 */
router.get('/statistics', authenticate, messageController.getScanStatistics);

/**
 * @swagger
 * /messages/analyze:
 *   post:
 *     summary: Analyze message (Legacy)
 *     tags: [Messages]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/ScanTextRequest'
 *     responses:
 *       200:
 *         description: Analysis result
 */
router.post('/analyze', authenticate, messageController.analyzeMessage);

/**
 * @swagger
 * /messages:
 *   get:
 *     summary: Get all messages
 *     tags: [Messages]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: List of messages
 */
router.get('/', authenticate, messageController.getAllMessages);

/**
 * @swagger
 * /messages/{id}:
 *   get:
 *     summary: Get message by ID
 *     tags: [Messages]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Message detail
 */
router.get('/:id', authenticate, messageController.getMessageById);

/**
 * @swagger
 * /messages/{id}:
 *   delete:
 *     summary: Delete message
 *     tags: [Messages]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Deleted successfully
 */
router.delete('/:id', authenticate, messageController.deleteMessage);

module.exports = router;

