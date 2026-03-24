const Stripe = require('stripe');
const logger = require('../utils/logger');

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

/**
 * Create a Stripe Checkout session for subscription
 */
const createCheckoutSession = async ({ plan, billing, successUrl, cancelUrl, customerEmail }) => {
  const priceId = getPriceId(plan, billing);
  if (!priceId) {
    throw new Error(`Invalid plan: ${plan}`);
  }

  const sessionParams = {
    mode: 'subscription',
    payment_method_types: ['card'],
    line_items: [{ price: priceId, quantity: 1 }],
    success_url: successUrl || `${process.env.LANDING_PAGE_URL || 'https://aiscamshield.codes'}/success.html?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: cancelUrl || `${process.env.LANDING_PAGE_URL || 'https://aiscamshield.codes'}/cancel.html`,
    allow_promotion_codes: true,
  };

  if (customerEmail) {
    sessionParams.customer_email = customerEmail;
  }

  const session = await stripe.checkout.sessions.create(sessionParams);
  logger.info('Stripe checkout session created', { sessionId: session.id, plan, billing });
  return session;
};

/**
 * Get Stripe Price ID for a plan
 */
const getPriceId = (plan, billing = 'monthly') => {
  const prices = {
    pro: {
      monthly: process.env.STRIPE_PRICE_PRO_MONTHLY,
      yearly: process.env.STRIPE_PRICE_PRO_YEARLY,
    },
    enterprise: {
      monthly: process.env.STRIPE_PRICE_ENTERPRISE_MONTHLY,
      yearly: process.env.STRIPE_PRICE_ENTERPRISE_YEARLY,
    },
  };

  return prices[plan]?.[billing] || null;
};

/**
 * Handle Stripe webhook event
 */
const handleWebhookEvent = async (rawBody, signature) => {
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
  const event = stripe.webhooks.constructEvent(rawBody, signature, webhookSecret);

  logger.info('Stripe webhook received', { type: event.type });

  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object;
      logger.info('Checkout completed', {
        sessionId: session.id,
        customerEmail: session.customer_email,
        subscriptionId: session.subscription,
      });
      break;
    }
    case 'customer.subscription.updated':
    case 'customer.subscription.deleted': {
      const subscription = event.data.object;
      logger.info('Subscription updated', {
        subscriptionId: subscription.id,
        status: subscription.status,
      });
      break;
    }
    case 'invoice.payment_failed': {
      const invoice = event.data.object;
      logger.warn('Payment failed', { invoiceId: invoice.id, customerId: invoice.customer });
      break;
    }
    default:
      logger.info('Unhandled webhook event', { type: event.type });
  }

  return { received: true };
};

/**
 * Get available plans for display
 */
const getPlans = () => {
  return [
    {
      id: 'free',
      name: 'Free',
      description: 'Basic protection to get started',
      price: { monthly: 0, yearly: 0 },
      features: [
        '10 message scans/day',
        '5 URL checks/day',
        'Basic threat alerts',
        'Community protection',
      ],
    },
    {
      id: 'pro',
      name: 'Pro',
      description: 'Complete protection for individuals',
      price: { monthly: 9.99, yearly: 7.99 },
      popular: true,
      features: [
        'Unlimited message scans',
        'Unlimited URL checks',
        'Email inbox scanning',
        'Voice call analysis',
        'Real-time alerts',
        'Scan history & reports',
        'Priority support',
      ],
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      description: 'For teams and organizations',
      price: { monthly: 29.99, yearly: 23.99 },
      features: [
        'Everything in Pro',
        'Up to 50 team members',
        'Admin dashboard',
        'API access',
        'Custom threat rules',
        'Dedicated account manager',
        'SLA guarantee',
      ],
    },
  ];
};

module.exports = {
  createCheckoutSession,
  handleWebhookEvent,
  getPlans,
};
