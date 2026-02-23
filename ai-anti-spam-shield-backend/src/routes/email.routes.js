const express = require('express');
const router = express.Router();
const emailController = require('../controllers/email.controller');
const { authenticate } = require('../middlewares/auth');

/**
 * @swagger
 * /emails/connect:
 *   post:
 *     summary: Connect an email account for auto-scanning
 *     tags: [Emails]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required: [email, password, provider]
 *             properties:
 *               email:
 *                 type: string
 *                 description: Email address
 *               password:
 *                 type: string
 *                 description: App password for IMAP access
 *               provider:
 *                 type: string
 *                 enum: [gmail, outlook, yahoo, other]
 *               imapHost:
 *                 type: string
 *                 description: IMAP server host (required for 'other' provider)
 *               imapPort:
 *                 type: integer
 *                 description: IMAP server port (default 993)
 *     responses:
 *       201:
 *         description: Email account connected
 *       400:
 *         description: Invalid credentials or account already connected
 */
router.post('/connect', authenticate, emailController.connectAccount);

/**
 * @swagger
 * /emails/accounts:
 *   get:
 *     summary: List connected email accounts
 *     tags: [Emails]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: List of email accounts
 */
router.get('/accounts', authenticate, emailController.getAccounts);

/**
 * @swagger
 * /emails/statistics:
 *   get:
 *     summary: Get overall email scan statistics
 *     tags: [Emails]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Email scan statistics
 */
router.get('/statistics', authenticate, emailController.getStatistics);

/**
 * @swagger
 * /emails/accounts/{id}:
 *   get:
 *     summary: Get email account details
 *     tags: [Emails]
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
 *         description: Email account details
 *       404:
 *         description: Not found
 */
router.get('/accounts/:id', authenticate, emailController.getAccountById);

/**
 * @swagger
 * /emails/accounts/{id}:
 *   delete:
 *     summary: Disconnect an email account
 *     tags: [Emails]
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
 *         description: Account disconnected
 */
router.delete('/accounts/:id', authenticate, emailController.disconnectAccount);

/**
 * @swagger
 * /emails/accounts/{id}/settings:
 *   put:
 *     summary: Update email account settings
 *     tags: [Emails]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *     requestBody:
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               autoScanInterval:
 *                 type: integer
 *                 description: Minutes between auto-scans (0 to disable)
 *               isActive:
 *                 type: boolean
 *     responses:
 *       200:
 *         description: Settings updated
 */
router.put('/accounts/:id/settings', authenticate, emailController.updateSettings);

/**
 * @swagger
 * /emails/accounts/{id}/scan:
 *   post:
 *     summary: Trigger manual email scan
 *     tags: [Emails]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *     responses:
 *       202:
 *         description: Scan queued
 *       200:
 *         description: Scan completed (if queue unavailable)
 */
router.post('/accounts/:id/scan', authenticate, emailController.triggerScan);

/**
 * @swagger
 * /emails/accounts/{id}/results:
 *   get:
 *     summary: Get scan results for an account
 *     tags: [Emails]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *       - in: query
 *         name: page
 *         schema:
 *           type: integer
 *           default: 1
 *       - in: query
 *         name: limit
 *         schema:
 *           type: integer
 *           default: 20
 *       - in: query
 *         name: flaggedOnly
 *         schema:
 *           type: boolean
 *     responses:
 *       200:
 *         description: Scan results
 */
router.get('/accounts/:id/results', authenticate, emailController.getScanResults);

/**
 * @swagger
 * /emails/accounts/{id}/flagged:
 *   get:
 *     summary: Get flagged emails for an account
 *     tags: [Emails]
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
 *         description: Flagged emails
 */
router.get('/accounts/:id/flagged', authenticate, emailController.getFlaggedEmails);

/**
 * @swagger
 * /emails/accounts/{id}/clean:
 *   post:
 *     summary: Clean (trash) flagged emails
 *     tags: [Emails]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *     requestBody:
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               emailIds:
 *                 type: array
 *                 items:
 *                   type: string
 *                 description: Optional specific email IDs to clean. If omitted, all flagged emails are cleaned.
 *     responses:
 *       200:
 *         description: Emails cleaned
 */
router.post('/accounts/:id/clean', authenticate, emailController.cleanFlaggedEmails);

module.exports = router;
