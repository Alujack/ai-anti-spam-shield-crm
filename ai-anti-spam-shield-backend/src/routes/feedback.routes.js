const express = require('express');
const router = express.Router();
const feedbackController = require('../controllers/feedback.controller');
const { authenticate, authorize } = require('../middlewares/auth');

/**
 * @swagger
 * components:
 *   schemas:
 *     Feedback:
 *       type: object
 *       properties:
 *         id:
 *           type: string
 *         userId:
 *           type: string
 *         scanHistoryId:
 *           type: string
 *         phishingHistoryId:
 *           type: string
 *         originalPrediction:
 *           type: string
 *         actualLabel:
 *           type: string
 *         feedbackType:
 *           type: string
 *           enum: [false_positive, false_negative, confirmed]
 *         userComment:
 *           type: string
 *         status:
 *           type: string
 *           enum: [pending, approved, rejected]
 *         createdAt:
 *           type: string
 *           format: date-time
 */

/**
 * @swagger
 * /api/v1/feedback:
 *   post:
 *     summary: Submit feedback on a scan result
 *     tags: [Feedback]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - scanId
 *               - feedbackType
 *             properties:
 *               scanId:
 *                 type: string
 *                 description: ID of the scan to provide feedback on
 *               scanType:
 *                 type: string
 *                 enum: [text, voice, phishing]
 *                 default: text
 *               feedbackType:
 *                 type: string
 *                 enum: [false_positive, false_negative, confirmed]
 *               actualLabel:
 *                 type: string
 *                 description: Optional override for actual label
 *               comment:
 *                 type: string
 *                 description: User comment about the feedback
 *     responses:
 *       201:
 *         description: Feedback submitted successfully
 *       400:
 *         description: Invalid input
 *       401:
 *         description: Unauthorized
 */
router.post('/',
  authenticate,
  feedbackController.submitFeedback
);

/**
 * @swagger
 * /api/v1/feedback/pending:
 *   get:
 *     summary: Get pending feedback for admin review
 *     tags: [Feedback]
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
 *           default: 20
 *       - in: query
 *         name: type
 *         schema:
 *           type: string
 *           enum: [false_positive, false_negative, confirmed]
 *     responses:
 *       200:
 *         description: List of pending feedback
 *       401:
 *         description: Unauthorized
 *       403:
 *         description: Forbidden - Admin only
 */
router.get('/pending',
  authenticate,
  authorize('ADMIN'),
  feedbackController.getPendingFeedback
);

/**
 * @swagger
 * /api/v1/feedback/stats:
 *   get:
 *     summary: Get feedback statistics
 *     tags: [Feedback]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Feedback statistics
 *       401:
 *         description: Unauthorized
 */
router.get('/stats',
  authenticate,
  feedbackController.getFeedbackStats
);

/**
 * @swagger
 * /api/v1/feedback/export:
 *   get:
 *     summary: Export approved feedback for training
 *     tags: [Feedback]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: format
 *         schema:
 *           type: string
 *           enum: [json, csv]
 *           default: json
 *       - in: query
 *         name: since
 *         schema:
 *           type: string
 *           format: date-time
 *     responses:
 *       200:
 *         description: Exported feedback data
 *       401:
 *         description: Unauthorized
 *       403:
 *         description: Forbidden - Admin only
 */
router.get('/export',
  authenticate,
  authorize('ADMIN'),
  feedbackController.exportForTraining
);

/**
 * @swagger
 * /api/v1/feedback/my:
 *   get:
 *     summary: Get current user's feedback history
 *     tags: [Feedback]
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
 *           default: 20
 *     responses:
 *       200:
 *         description: User's feedback history
 *       401:
 *         description: Unauthorized
 */
router.get('/my',
  authenticate,
  feedbackController.getMyFeedback
);

/**
 * @swagger
 * /api/v1/feedback/{id}:
 *   put:
 *     summary: Review feedback (approve/reject) - Admin only
 *     tags: [Feedback]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - action
 *             properties:
 *               action:
 *                 type: string
 *                 enum: [approve, reject]
 *               notes:
 *                 type: string
 *     responses:
 *       200:
 *         description: Feedback reviewed successfully
 *       400:
 *         description: Invalid action
 *       401:
 *         description: Unauthorized
 *       403:
 *         description: Forbidden - Admin only
 *       404:
 *         description: Feedback not found
 */
router.put('/:id',
  authenticate,
  authorize('ADMIN'),
  feedbackController.reviewFeedback
);

/**
 * @swagger
 * /api/v1/feedback/{id}:
 *   get:
 *     summary: Get feedback by ID
 *     tags: [Feedback]
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
 *         description: Feedback details
 *       401:
 *         description: Unauthorized
 *       404:
 *         description: Feedback not found
 */
router.get('/:id',
  authenticate,
  feedbackController.getFeedbackById
);

module.exports = router;
