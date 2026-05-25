// ===== Mobile Nav Toggle =====
const navToggle = document.getElementById('navToggle');
const navLinks = document.getElementById('navLinks');

navToggle.addEventListener('click', () => {
  navLinks.classList.toggle('open');
  navToggle.classList.toggle('active');
});

// Close nav on link click
navLinks.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', () => {
    navLinks.classList.remove('open');
    navToggle.classList.remove('active');
  });
});

// ===== Billing Toggle =====
const billingToggle = document.getElementById('billingToggle');
const toggleLabels = document.querySelectorAll('.toggle-label');
let isYearly = false;

billingToggle.addEventListener('click', () => {
  isYearly = !isYearly;
  billingToggle.classList.toggle('active', isYearly);

  toggleLabels.forEach(label => {
    const period = label.dataset.period;
    label.classList.toggle('active', (isYearly && period === 'yearly') || (!isYearly && period === 'monthly'));
  });

  // Update prices
  document.querySelectorAll('.price-value[data-monthly]').forEach(el => {
    el.textContent = isYearly ? el.dataset.yearly : el.dataset.monthly;
  });
});

// ===== FAQ Accordion =====
document.querySelectorAll('.faq-item').forEach(item => {
  const question = item.querySelector('.faq-question');
  const answer = item.querySelector('.faq-answer');

  question.addEventListener('click', () => {
    const isOpen = item.classList.contains('open');

    // Close all
    document.querySelectorAll('.faq-item').forEach(i => {
      i.classList.remove('open');
      i.querySelector('.faq-answer').style.maxHeight = null;
    });

    // Open clicked (if wasn't open)
    if (!isOpen) {
      item.classList.add('open');
      answer.style.maxHeight = answer.scrollHeight + 'px';
    }
  });
});

// ===== Smooth Scroll for anchor links =====
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', (e) => {
    const target = document.querySelector(anchor.getAttribute('href'));
    if (target) {
      e.preventDefault();
      const offset = 80;
      const top = target.getBoundingClientRect().top + window.pageYOffset - offset;
      window.scrollTo({ top, behavior: 'smooth' });
    }
  });
});

// ===== Subscribe (static demo — opens Stripe-style modal) =====
const PLAN_DETAILS = {
  pro:        { name: 'Pro',        monthly: 9.99,  yearly: 95.88 },
  enterprise: { name: 'Enterprise', monthly: 29.99, yearly: 287.88 },
};

document.querySelectorAll('[data-plan]').forEach(btn => {
  btn.addEventListener('click', (e) => {
    e.preventDefault();
    const plan = btn.dataset.plan;
    if (plan === 'free') {
      window.location.href = 'success.html?plan=free';
      return;
    }
    openCheckout(plan, isYearly ? 'yearly' : 'monthly');
  });
});

// "Start Free Trial" CTAs scroll to pricing — already handled by smooth scroll.

function fmt(n) {
  return n.toFixed(2);
}

function openCheckout(plan, billing) {
  const details = PLAN_DETAILS[plan];
  if (!details) return;
  const amount = billing === 'yearly' ? details.yearly : details.monthly;

  // Populate summary
  document.getElementById('checkoutPlanName').textContent = details.name;
  document.getElementById('checkoutPriceBig').textContent = fmt(billing === 'yearly' ? amount / 12 : amount);
  document.getElementById('checkoutBillingMeta').textContent = billing === 'yearly' ? 'Per month, billed yearly' : 'Per month';
  document.getElementById('checkoutLineTitle').textContent = `AI Scam Shield ${details.name}`;
  document.getElementById('checkoutLineSub').textContent = billing === 'yearly' ? 'Billed annually' : 'Billed monthly';
  document.getElementById('checkoutLineAmt').textContent = fmt(amount);
  document.getElementById('checkoutSubtotal').textContent = fmt(amount);
  document.getElementById('checkoutTotal').textContent = fmt(amount);
  document.getElementById('payBtnAmount').textContent = fmt(amount);

  // Reset promo state
  document.getElementById('checkoutDiscountRow').hidden = true;
  document.getElementById('promoInput').hidden = true;
  document.getElementById('promoCode').value = '';
  document.getElementById('promoToggle').textContent = 'Add promotion code';

  // Stash current selection on the form so the submit handler can read it
  const form = document.getElementById('checkoutForm');
  form.dataset.plan = plan;
  form.dataset.billing = billing;
  form.dataset.amount = String(amount);
  form.dataset.discount = '0';

  const overlay = document.getElementById('checkoutOverlay');
  overlay.classList.add('open');
  overlay.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';
  setTimeout(() => document.getElementById('cardEmail').focus(), 200);
}

function closeCheckout() {
  const overlay = document.getElementById('checkoutOverlay');
  overlay.classList.remove('open');
  overlay.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
}

document.getElementById('checkoutClose').addEventListener('click', closeCheckout);
document.getElementById('checkoutOverlay').addEventListener('click', (e) => {
  if (e.target === e.currentTarget) closeCheckout();
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeCheckout();
});

// ===== Card input formatting =====
const cardNumberInput = document.getElementById('cardNumber');
const cardExpInput = document.getElementById('cardExp');
const cardCvcInput = document.getElementById('cardCvc');

function detectBrand(num) {
  const n = num.replace(/\s+/g, '');
  if (/^4/.test(n)) return 'visa';
  if (/^(5[1-5]|2[2-7])/.test(n)) return 'mc';
  if (/^3[47]/.test(n)) return 'amex';
  return null;
}

cardNumberInput.addEventListener('input', (e) => {
  let v = e.target.value.replace(/\D/g, '').slice(0, 16);
  v = v.replace(/(.{4})/g, '$1 ').trim();
  e.target.value = v;
  const brand = detectBrand(v);
  document.querySelectorAll('.card-brand').forEach(el => {
    el.classList.toggle('active', el.dataset.brand === brand);
    el.classList.toggle('dim', brand && el.dataset.brand !== brand);
  });
});

cardExpInput.addEventListener('input', (e) => {
  let v = e.target.value.replace(/\D/g, '').slice(0, 4);
  if (v.length >= 3) v = v.slice(0, 2) + ' / ' + v.slice(2);
  e.target.value = v;
});

cardCvcInput.addEventListener('input', (e) => {
  e.target.value = e.target.value.replace(/\D/g, '').slice(0, 4);
});

document.getElementById('demoCardBtn').addEventListener('click', () => {
  document.getElementById('cardEmail').value = document.getElementById('cardEmail').value || 'demo@aiscamshield.codes';
  cardNumberInput.value = '4242 4242 4242 4242';
  cardNumberInput.dispatchEvent(new Event('input'));
  cardExpInput.value = '12 / 34';
  cardCvcInput.value = '123';
  document.getElementById('cardName').value = document.getElementById('cardName').value || 'Demo User';
});

// ===== Promotion code =====
const PROMO_CODES = {
  'DEMO20': 0.20,
  'SHIELD50': 0.50,
  'LAUNCH10': 0.10,
};

document.getElementById('promoToggle').addEventListener('click', (e) => {
  e.preventDefault();
  const input = document.getElementById('promoInput');
  input.hidden = !input.hidden;
  if (!input.hidden) document.getElementById('promoCode').focus();
});

document.getElementById('promoApply').addEventListener('click', (e) => {
  e.preventDefault();
  const code = document.getElementById('promoCode').value.trim().toUpperCase();
  const form = document.getElementById('checkoutForm');
  const amount = parseFloat(form.dataset.amount);
  const pct = PROMO_CODES[code];
  if (!pct) {
    document.getElementById('promoCode').classList.add('invalid');
    setTimeout(() => document.getElementById('promoCode').classList.remove('invalid'), 800);
    return;
  }
  const discount = +(amount * pct).toFixed(2);
  form.dataset.discount = String(discount);
  document.getElementById('promoCodeLabel').textContent = code;
  document.getElementById('checkoutDiscount').textContent = fmt(discount);
  document.getElementById('checkoutDiscountRow').hidden = false;
  document.getElementById('checkoutTotal').textContent = fmt(amount - discount);
  document.getElementById('payBtnAmount').textContent = fmt(amount - discount);
});

// ===== Submit (fake processing) =====
document.getElementById('checkoutForm').addEventListener('submit', (e) => {
  e.preventDefault();
  const form = e.target;
  const email = document.getElementById('cardEmail').value.trim();
  const number = cardNumberInput.value.replace(/\s+/g, '');
  const exp = cardExpInput.value.replace(/\s+/g, '');
  const cvc = cardCvcInput.value;
  const name = document.getElementById('cardName').value.trim();

  // Light validation
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return flashError('cardEmail');
  if (number.length < 13) return flashError('cardNumber');
  if (!/^\d{2}\/\d{2}$/.test(exp)) return flashError('cardExp');
  if (cvc.length < 3) return flashError('cardCvc');
  if (!name) return flashError('cardName');

  const btn = document.getElementById('checkoutPayBtn');
  btn.classList.add('loading');
  btn.disabled = true;

  // Simulate Stripe round-trip
  setTimeout(() => {
    const amount = parseFloat(form.dataset.amount);
    const discount = parseFloat(form.dataset.discount || '0');
    const total = (amount - discount).toFixed(2);
    const brand = detectBrand(number) || 'card';
    const last4 = number.slice(-4);
    const params = new URLSearchParams({
      plan: form.dataset.plan,
      billing: form.dataset.billing,
      amount: total,
      brand,
      last4,
      email,
      session_id: 'cs_demo_' + Math.random().toString(36).slice(2, 12),
    });
    window.location.href = 'success.html?' + params.toString();
  }, 1800);
});

function flashError(id) {
  const el = document.getElementById(id);
  el.classList.add('invalid');
  el.focus();
  setTimeout(() => el.classList.remove('invalid'), 800);
}

// ===== Interactive Scanner Demo =====
const EXAMPLES = {
  phishing: 'URGENT: Your Bank of America account has been temporarily locked due to suspicious activity. Click here to verify your identity immediately: http://bofa-secure-login.tk/verify?id=8829',
  lottery:  'CONGRATULATIONS! You have WON $1,000,000 in our international lottery! To claim your prize, send your bank details and a $250 processing fee to claims@megalottery-intl.win',
  delivery: 'USPS: Your package #US98421 could not be delivered due to incomplete address. Please update your details within 24 hours or it will be returned: https://usps-redelivery.info/track',
  safe:     "Hey, just confirming our 3pm meeting tomorrow. I'll send the doc over after lunch. Thanks!",
};

const VERDICTS = {
  phishing: {
    verdict: 'dangerous',
    score: 97,
    label: 'High-Risk Phishing Attempt',
    summary: 'This message impersonates a major bank and uses urgency to drive you to a fake login page on a suspicious .tk domain.',
    signals: [
      { type: 'danger',  text: 'Spoofed sender impersonating Bank of America' },
      { type: 'danger',  text: 'Suspicious domain: bofa-secure-login.tk' },
      { type: 'warning', text: 'High-urgency language ("URGENT", "immediately")' },
      { type: 'warning', text: 'Asks for sensitive credentials via link' },
    ],
  },
  lottery: {
    verdict: 'dangerous',
    score: 94,
    label: 'Advance-Fee Lottery Scam',
    summary: 'Classic 419-style scam — you "won" a lottery you never entered, and must pay a fee to release imaginary funds.',
    signals: [
      { type: 'danger',  text: 'Requests upfront payment ($250 fee)' },
      { type: 'danger',  text: 'Asks for bank details over email' },
      { type: 'warning', text: 'Unverifiable prize claim' },
      { type: 'warning', text: 'Domain registered <30 days ago (.win TLD)' },
    ],
  },
  delivery: {
    verdict: 'suspicious',
    score: 78,
    label: 'Likely Smishing / Package Scam',
    summary: 'USPS does not send tracking SMS from random URLs. This pattern matches active smishing campaigns harvesting personal info.',
    signals: [
      { type: 'warning', text: 'Domain mismatch: USPS uses usps.com, not usps-redelivery.info' },
      { type: 'warning', text: 'Artificial 24-hour deadline' },
      { type: 'warning', text: 'Tracking number format does not match real USPS' },
      { type: 'safe',    text: 'Sender number not flagged in spam DB (yet)' },
    ],
  },
  safe: {
    verdict: 'safe',
    score: 6,
    label: 'No Threats Detected',
    summary: 'Normal conversational text with no suspicious links, urgency markers, or credential-harvesting patterns.',
    signals: [
      { type: 'safe', text: 'No URLs present' },
      { type: 'safe', text: 'No requests for sensitive info' },
      { type: 'safe', text: 'No urgency / pressure language' },
      { type: 'safe', text: 'Conversational tone consistent with known contacts' },
    ],
  },
};

function classifyAdHoc(text) {
  // Heuristic classifier so custom text also produces a believable verdict.
  const t = text.toLowerCase();
  let score = 5;
  const signals = [];
  const urls = (t.match(/https?:\/\/\S+|\b\S+\.(tk|info|win|click|xyz|top|link)\b/g) || []);
  if (urls.length) { score += 30; signals.push({ type: 'warning', text: `Contains link${urls.length>1?'s':''}: ${urls[0]}` }); }
  if (/(urgent|immediately|within \d+ ?(hours?|hrs?|minutes?)|act now|expires)/i.test(text)) {
    score += 25; signals.push({ type: 'warning', text: 'High-urgency language detected' });
  }
  if (/(won|winner|prize|lottery|congratulations|claim your)/i.test(text)) {
    score += 25; signals.push({ type: 'danger', text: 'Prize / lottery scam pattern' });
  }
  if (/(verify|confirm|update).{0,30}(account|identity|password|details)/i.test(text)) {
    score += 25; signals.push({ type: 'danger', text: 'Credential-harvesting pattern detected' });
  }
  if (/(bank|paypal|amazon|apple|microsoft|usps|fedex|netflix)/i.test(text) && urls.length) {
    score += 20; signals.push({ type: 'danger', text: 'Impersonates a trusted brand with external link' });
  }
  if (/(fee|wire|bitcoin|gift card|western union|moneygram)/i.test(text)) {
    score += 20; signals.push({ type: 'danger', text: 'Payment / wire request' });
  }
  score = Math.min(99, score);

  let verdict, label, summary;
  if (score >= 75) {
    verdict = 'dangerous';
    label = 'High-Risk Threat Detected';
    summary = 'Multiple signals match known scam patterns. Do not click, reply, or share information.';
  } else if (score >= 40) {
    verdict = 'suspicious';
    label = 'Suspicious Content';
    summary = 'Some warning signs are present. Treat with caution and verify the sender independently.';
  } else {
    verdict = 'safe';
    label = 'No Threats Detected';
    summary = 'No obvious scam indicators. Always stay alert for context that AI cannot see.';
    if (signals.length === 0) {
      signals.push({ type: 'safe', text: 'No URLs present' });
      signals.push({ type: 'safe', text: 'No requests for sensitive info' });
      signals.push({ type: 'safe', text: 'No urgency / pressure language' });
    }
  }
  return { verdict, score, label, summary, signals };
}

const scannerInput = document.getElementById('scannerInput');
const scanBtn = document.getElementById('scanBtn');
const scannerResult = document.getElementById('scannerResult');

document.querySelectorAll('.example-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    const key = chip.dataset.example;
    scannerInput.value = EXAMPLES[key];
    scanBtn.dataset.exampleKey = key;
    scannerInput.focus();
  });
});

scannerInput.addEventListener('input', () => { delete scanBtn.dataset.exampleKey; });

document.querySelectorAll('.scanner-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.scanner-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    const placeholders = {
      message: 'Paste a suspicious SMS or message here, or try one of the examples below...',
      email:   'Paste a suspicious email (subject + body) here...',
      url:     'Paste a URL here to check its safety, e.g. https://bofa-secure-login.tk/verify',
    };
    scannerInput.placeholder = placeholders[tab.dataset.tab];
  });
});

scanBtn.addEventListener('click', () => {
  const text = scannerInput.value.trim();
  if (!text) {
    scannerInput.focus();
    scannerInput.classList.add('invalid');
    setTimeout(() => scannerInput.classList.remove('invalid'), 600);
    return;
  }

  // Loading state
  scannerResult.innerHTML = `
    <div class="scanner-loading">
      <div class="scanner-loading-orb"></div>
      <div class="scanner-loading-text">
        <span class="loading-step">Tokenizing input…</span>
        <span class="loading-step">Querying threat model…</span>
        <span class="loading-step">Cross-checking known scam DB…</span>
        <span class="loading-step">Computing risk score…</span>
      </div>
    </div>`;
  scanBtn.disabled = true;
  scanBtn.classList.add('loading');

  const exampleKey = scanBtn.dataset.exampleKey;
  const result = exampleKey ? VERDICTS[exampleKey] : classifyAdHoc(text);

  setTimeout(() => {
    renderScannerResult(result);
    scanBtn.disabled = false;
    scanBtn.classList.remove('loading');
  }, 1600);
});

function renderScannerResult(r) {
  const colorByVerdict = {
    safe:       { bg: '#E8FFF6', text: '#00A578', icon: '&#10003;', title: 'Safe' },
    suspicious: { bg: '#FFF6E0', text: '#C77700', icon: '?',        title: 'Suspicious' },
    dangerous:  { bg: '#FFE8E8', text: '#D63030', icon: '!',        title: 'Dangerous' },
  };
  const c = colorByVerdict[r.verdict];
  const signalsHtml = r.signals.map(s => `
    <li class="signal signal-${s.type}">
      <span class="signal-dot"></span>
      <span>${escapeHtml(s.text)}</span>
    </li>`).join('');

  scannerResult.innerHTML = `
    <div class="result-card result-${r.verdict}" style="--result-bg:${c.bg};--result-text:${c.text}">
      <div class="result-header">
        <div class="result-icon">${c.icon}</div>
        <div>
          <div class="result-verdict">${c.title}</div>
          <div class="result-label">${escapeHtml(r.label)}</div>
        </div>
        <div class="result-score">
          <div class="result-score-num" data-target="${r.score}">0</div>
          <div class="result-score-lbl">Risk score</div>
        </div>
      </div>
      <p class="result-summary">${escapeHtml(r.summary)}</p>
      <div class="result-meter"><div class="result-meter-fill" style="width:${r.score}%"></div></div>
      <ul class="result-signals">${signalsHtml}</ul>
      <div class="result-actions">
        <a href="#pricing" class="btn btn-primary btn-sm">Get full protection</a>
        <button class="btn btn-outline btn-sm" id="scanAgainBtn">Scan another</button>
      </div>
    </div>`;

  // Animate score
  const scoreEl = scannerResult.querySelector('.result-score-num');
  animateCount(scoreEl, r.score, 900);

  document.getElementById('scanAgainBtn').addEventListener('click', () => {
    scannerInput.value = '';
    delete scanBtn.dataset.exampleKey;
    scannerResult.innerHTML = `
      <div class="scanner-empty">
        <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="#A29BFE" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        <p>Results will appear here</p>
      </div>`;
    scannerInput.focus();
  });
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]);
}

// ===== Animated stats (count-up) =====
function animateCount(el, target, duration = 1200) {
  const isPercent = String(target).indexOf('.') !== -1;
  const start = performance.now();
  const startVal = 0;
  function tick(now) {
    const t = Math.min(1, (now - start) / duration);
    const eased = 1 - Math.pow(1 - t, 3);
    const val = startVal + (target - startVal) * eased;
    el.textContent = isPercent ? val.toFixed(1) + '%' : Math.round(val).toString();
    if (t < 1) requestAnimationFrame(tick);
    else el.textContent = isPercent ? target + '%' : target;
  }
  requestAnimationFrame(tick);
}

// Replace hero stat numbers with data-target so we can animate them on view.
(function prepareHeroStats() {
  const stats = document.querySelectorAll('.hero-stats .stat-number');
  if (stats.length >= 3) {
    stats[0].dataset.target = '99.2';
    stats[0].textContent = '0.0%';
    stats[1].dataset.skip = '1'; // "<1s" — leave as-is
    stats[2].dataset.skip = '1'; // "24/7" — leave as-is
  }
})();

const heroObserver = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (!e.isIntersecting) return;
    const el = e.target;
    if (el.dataset.skip) return;
    animateCount(el, parseFloat(el.dataset.target), 1400);
    heroObserver.unobserve(el);
  });
}, { threshold: 0.6 });
document.querySelectorAll('.hero-stats .stat-number').forEach(el => heroObserver.observe(el));

// ===== Scroll reveal =====
const revealTargets = document.querySelectorAll(
  '.section-header, .feature-card, .step, .price-card, .testimonial-card, .faq-item, .scanner-card'
);
revealTargets.forEach(el => el.classList.add('reveal'));
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((e, i) => {
    if (e.isIntersecting) {
      setTimeout(() => e.target.classList.add('revealed'), (i % 6) * 60);
      revealObserver.unobserve(e.target);
    }
  });
}, { threshold: 0.12 });
revealTargets.forEach(el => revealObserver.observe(el));

// ===== Phone mockup alert cycle =====
(function cycleMockAlerts() {
  const alerts = document.querySelectorAll('.phone-screen .mock-alert');
  if (alerts.length < 2) return;
  let active = 0;
  alerts.forEach((a, i) => a.classList.toggle('mock-active', i === active));
  setInterval(() => {
    alerts[active].classList.remove('mock-active');
    active = (active + 1) % alerts.length;
    alerts[active].classList.add('mock-active');
  }, 2400);
})();

// ===== Open mobile app (deep link with graceful fallback) =====
// When the stores go live, fill these in. Leave empty string to disable the store fallback.
const STORE_URLS = {
  ios: '',     // e.g. 'https://apps.apple.com/app/id0000000000'
  android: '', // e.g. 'https://play.google.com/store/apps/details?id=com.example.ai_anti_spam_shield_mobile'
};
const APP_SCHEME_URL = 'aishield://open';
const FALLBACK_TIMEOUT_MS = 1500;

function detectPlatform() {
  const ua = navigator.userAgent || '';
  if (/iPhone|iPad|iPod/.test(ua)) return 'ios';
  if (/Android/.test(ua)) return 'android';
  return 'desktop';
}

function showAppToast(message) {
  let toast = document.getElementById('appToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'appToast';
    toast.className = 'app-toast';
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(showAppToast._t);
  showAppToast._t = setTimeout(() => toast.classList.remove('show'), 4000);
}

function showQrModal() {
  let modal = document.getElementById('appQrModal');
  if (!modal) {
    const qrSrc = 'https://api.qrserver.com/v1/create-qr-code/?size=260x260&margin=8&data=' +
      encodeURIComponent(APP_SCHEME_URL);
    modal = document.createElement('div');
    modal.id = 'appQrModal';
    modal.className = 'app-qr-modal';
    modal.innerHTML =
      '<div class="app-qr-card" role="dialog" aria-modal="true" aria-labelledby="appQrTitle">' +
        '<button class="app-qr-close" aria-label="Close">&times;</button>' +
        '<h3 id="appQrTitle">Open on your phone</h3>' +
        '<p>Scan this QR code with your phone\'s camera. If AI Scam Shield is installed, it will open the app.</p>' +
        '<img alt="QR code linking to ' + APP_SCHEME_URL + '" src="' + qrSrc + '" width="220" height="220">' +
        '<p class="app-qr-hint">App not yet on the App Store or Google Play — listings coming soon.</p>' +
      '</div>';
    document.body.appendChild(modal);
    const close = () => modal.classList.remove('show');
    modal.querySelector('.app-qr-close').addEventListener('click', close);
    modal.addEventListener('click', (e) => { if (e.target === modal) close(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });
  }
  modal.classList.add('show');
}

function openApp(preferredStore) {
  const platform = detectPlatform();

  if (platform === 'desktop') {
    const url = STORE_URLS[preferredStore] || STORE_URLS.ios || STORE_URLS.android;
    if (url) {
      window.open(url, '_blank', 'noopener');
    } else {
      // No store listing yet — show a QR modal so the user can scan with their phone.
      showQrModal();
    }
    return;
  }

  // Mobile path: native <a href="aishield://open"> handles the navigation
  // (we don't preventDefault on mobile). We only schedule a fallback.
  const storeUrl = STORE_URLS[platform];
  const start = Date.now();

  const onVisibilityChange = () => {
    if (document.hidden) {
      document.removeEventListener('visibilitychange', onVisibilityChange);
    }
  };
  document.addEventListener('visibilitychange', onVisibilityChange);

  setTimeout(() => {
    document.removeEventListener('visibilitychange', onVisibilityChange);
    if (!document.hidden && Date.now() - start < FALLBACK_TIMEOUT_MS + 500) {
      if (storeUrl) {
        window.location.href = storeUrl;
      } else {
        showAppToast("Looks like AI Scam Shield isn't installed on this device. Install it from the App Store or Google Play (coming soon).");
      }
    }
  }, FALLBACK_TIMEOUT_MS);
}

let lastAppOpen = 0;
document.querySelectorAll('[data-app-link]').forEach(el => {
  // Make sure the anchor has a real deep-link href so the browser treats it
  // as a user-initiated navigation (iOS Safari needs this for custom schemes).
  if (!el.getAttribute('href') || el.getAttribute('href') === '#') {
    el.setAttribute('href', APP_SCHEME_URL);
  }
  el.addEventListener('click', (e) => {
    const platform = detectPlatform();
    if (platform === 'desktop') {
      // On desktop the href can't open the app — take over and show the QR modal.
      e.preventDefault();
      openApp(el.dataset.appLink);
      return;
    }
    // Mobile: debounce rapid re-taps so iOS Safari's anti-redirect-loop
    // guard doesn't show the "repeatedly trying to open another
    // application" prompt. First click navigates natively via href.
    const now = Date.now();
    if (now - lastAppOpen < 3000) {
      e.preventDefault();
      return;
    }
    lastAppOpen = now;
    openApp(el.dataset.appLink);
  });
});

// ===== Nav scroll effect =====
let lastScroll = 0;
window.addEventListener('scroll', () => {
  const nav = document.getElementById('nav');
  const scrollY = window.scrollY;

  if (scrollY > 100) {
    nav.style.boxShadow = '0 2px 20px rgba(0,0,0,0.08)';
  } else {
    nav.style.boxShadow = 'none';
  }
  lastScroll = scrollY;
});
