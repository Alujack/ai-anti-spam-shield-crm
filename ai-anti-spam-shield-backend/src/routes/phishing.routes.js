const express = require('express');
const router = express.Router();
const phishingController = require('../controllers/phishing.controller');
const { authenticate, optionalAuthenticate } = require('../middlewares/auth');

/**
 * @swagger
 * /phishing/scan-text:
 *   post:
 *     summary: Scan text for phishing
 *     tags: [Phishing]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/PhishingScanText'
 *     responses:
 *       200:
 *         description: Phishing scan result
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/PhishingResult'
 */
router.post('/scan-text', optionalAuthenticate, phishingController.scanText);

/**
 * @swagger
 * /phishing/scan-url:
 *   post:
 *     summary: Scan URL for phishing
 *     tags: [Phishing]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/PhishingScanUrl'
 *     responses:
 *       200:
 *         description: URL phishing scan result
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/PhishingResult'
 */
router.post('/scan-url', optionalAuthenticate, phishingController.scanUrl);

/**
 * @swagger
 * /phishing/batch-scan:
 *   post:
 *     summary: Batch scan multiple items for phishing
 *     tags: [Phishing]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               items:
 *                 type: array
 *                 items:
 *                   type: object
 *                   properties:
 *                     text:
 *                       type: string
 *                     url:
 *                       type: string
 *     responses:
 *       200:
 *         description: Batch scan results
 */
router.post('/batch-scan', optionalAuthenticate, phishingController.batchScan);

/**
 * @swagger
 * /phishing/history:
 *   get:
 *     summary: Get phishing scan history
 *     tags: [Phishing]
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
 *         description: Phishing scan history
 *       401:
 *         description: Unauthorized
 */
router.get('/history', authenticate, phishingController.getHistory);

/**
 * @swagger
 * /phishing/history/{id}:
 *   get:
 *     summary: Get phishing scan by ID
 *     tags: [Phishing]
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
 *         description: Phishing scan detail
 *       401:
 *         description: Unauthorized
 *       404:
 *         description: Not found
 */
router.get('/history/:id', authenticate, phishingController.getHistoryById);

/**
 * @swagger
 * /phishing/history/{id}:
 *   delete:
 *     summary: Delete phishing scan from history
 *     tags: [Phishing]
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
router.delete('/history/:id', authenticate, phishingController.deleteHistory);

/**
 * @swagger
 * /phishing/statistics:
 *   get:
 *     summary: Get phishing detection statistics
 *     tags: [Phishing]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Phishing statistics
 *       401:
 *         description: Unauthorized
 */
router.get('/statistics', authenticate, phishingController.getStatistics);

module.exports = router;
