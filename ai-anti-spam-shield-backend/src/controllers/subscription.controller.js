const stripeService = require('../services/stripe.service');
const logger = require('../utils/logger');

/**
 * Create a Stripe Checkout session
 */
const createCheckout = async (req, res, next) => {
  try {
    const { plan, billing, successUrl, cancelUrl } = req.body;

    if (!plan || !['pro', 'enterprise'].includes(plan)) {
      return res.status(400).json({
        status: 'error',
        message: 'Valid plan is required (pro or enterprise)',
      });
    }

    const session = await stripeService.createCheckoutSession({
      plan,
      billing: billing || 'monthly',
      successUrl,
      cancelUrl,
      customerEmail: req.body.email || undefined,
    });

    res.json({
      status: 'success',
      url: session.url,
      sessionId: session.id,
    });
  } catch (error) {
    logger.error('Checkout error', { error: error.message });
    next(error);
  }
};

/**
 * Stripe webhook handler
 */
const handleWebhook = async (req, res) => {
  try {
    const signature = req.headers['stripe-signature'];
    const result = await stripeService.handleWebhookEvent(req.body, signature);
    res.json(result);
  } catch (error) {
    logger.error('Webhook error', { error: error.message });
    res.status(400).json({ error: error.message });
  }
};

/**
 * Get available plans
 */
const getPlans = async (req, res) => {
  const plans = stripeService.getPlans();
  res.json({ status: 'success', data: plans });
};

module.exports = {
  createCheckout,
  handleWebhook,
  getPlans,
};
