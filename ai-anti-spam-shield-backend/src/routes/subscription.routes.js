const express = require('express');
const router = express.Router();
const subscriptionController = require('../controllers/subscription.controller');

// Public routes (no auth required for landing page)
router.get('/plans', subscriptionController.getPlans);
router.post('/checkout', subscriptionController.createCheckout);

// Stripe webhook - uses raw body (registered separately in app.js)
// router.post('/webhook', subscriptionController.handleWebhook);

module.exports = router;
