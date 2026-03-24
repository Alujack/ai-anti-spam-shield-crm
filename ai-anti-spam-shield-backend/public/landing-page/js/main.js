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

// ===== Stripe Subscription =====
const API_BASE = window.location.origin + '/api/v1';

async function subscribe(plan) {
  const btn = document.querySelector(`[data-plan="${plan}"]`);
  const originalText = btn.textContent;
  btn.textContent = 'Loading...';
  btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE}/subscriptions/checkout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        plan,
        billing: isYearly ? 'yearly' : 'monthly',
        successUrl: window.location.origin + '/success.html',
        cancelUrl: window.location.origin + '/cancel.html',
      }),
    });

    const data = await response.json();

    if (data.url) {
      window.location.href = data.url;
    } else {
      alert(data.message || 'Something went wrong. Please try again.');
    }
  } catch (err) {
    alert('Unable to connect. Please try again later.');
  } finally {
    btn.textContent = originalText;
    btn.disabled = false;
  }
}

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
