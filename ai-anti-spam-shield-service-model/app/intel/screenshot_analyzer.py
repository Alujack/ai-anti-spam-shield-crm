"""
Safe-Lab Behavioral Analyzer

Opens a URL in a headless Chromium sandbox and observes everything the page
actually DOES at runtime:

  - Permission requests: camera, microphone, geolocation, notifications
  - Clipboard access: read/write attempts
  - Forms: action URLs, cross-origin POSTs, http (cleartext) submission,
    password fields, credit-card fields
  - Network: redirect chain, third-party script origins, known
    cryptominer scripts
  - Auto-downloads / dialogs / hidden iframes
  - Page DOM: title, login-form indicators, brand keywords

We never grant any permissions to the page — instead we hook the navigator
APIs so the call is recorded but rejected. That way phishing pages reveal
their intent without the safe lab actually exposing anything.
"""

import asyncio
import base64
import hashlib
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from PIL import Image  # noqa: F401 — kept for future visual-hashing work
from playwright.async_api import (
    TimeoutError as PlaywrightTimeout,
    async_playwright,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Init script injected into every page BEFORE navigation. Wraps the sensitive
# navigator APIs with monitors that record the call and immediately reject —
# we want to see the *intent* without granting the page anything.
# ---------------------------------------------------------------------------
_SAFE_LAB_HOOKS = r"""
(() => {
  if (window.__safeLabInitialized) return;
  window.__safeLabInitialized = true;
  window.__safeLab = {
    permissions: [],
    clipboard: [],
    crypto: [],
    storage: [],          // document.cookie read, localStorage / sessionStorage access
    serviceWorker: [],    // service worker registrations (persistence)
    push: [],             // PushManager.subscribe (delivers fake alerts later)
    fingerprint: [],      // canvas/audio/battery/screen fingerprinting attempts
    webrtc: [],           // RTCPeerConnection — used for IP leak behind VPN
    wallet: [],           // window.ethereum / wallet extension probing
    beacon: [],           // navigator.sendBeacon — exfil on page unload
    antiDebug: [],        // debugger statement loops, right-click block, etc.
  };

  const log = (bucket, entry) => {
    try { window.__safeLab[bucket].push({ ...entry, ts: Date.now() }); }
    catch (_) {}
  };
  const denied = (msg) =>
    Promise.reject(new DOMException(msg, 'NotAllowedError'));

  // --- Camera / microphone / screen capture ---
  // navigator.mediaDevices is normally only exposed in secure (HTTPS/localhost)
  // contexts. Install a shadow object so phishing pages that try to use it on
  // plain HTTP still get caught (real phishing kits today usually run on
  // HTTPS via Let's Encrypt, but the test demo and any HTTP victim site need
  // these hooks too).
  try {
    if (!navigator.mediaDevices) {
      Object.defineProperty(navigator, 'mediaDevices', {
        value: {},
        configurable: true,
      });
    }
    navigator.mediaDevices.getUserMedia = function (c) {
      log('permissions', {
        api: 'getUserMedia',
        args: JSON.stringify(c || {}).slice(0, 200),
      });
      return denied('Permission denied (safe lab)');
    };
    navigator.mediaDevices.getDisplayMedia = function (c) {
      log('permissions', {
        api: 'getDisplayMedia',
        args: JSON.stringify(c || {}).slice(0, 200),
      });
      return denied('Permission denied (safe lab)');
    };
  } catch (_) {}

  // --- Geolocation ---
  if (navigator.geolocation) {
    const errStub = { code: 1, message: 'Permission denied (safe lab)' };
    const gcp = navigator.geolocation.getCurrentPosition.bind(navigator.geolocation);
    navigator.geolocation.getCurrentPosition = function (s, e, o) {
      log('permissions', { api: 'geolocation.getCurrentPosition', args: '' });
      if (e) try { e(errStub); } catch (_) {}
    };
    const wp = navigator.geolocation.watchPosition.bind(navigator.geolocation);
    navigator.geolocation.watchPosition = function (s, e, o) {
      log('permissions', { api: 'geolocation.watchPosition', args: '' });
      if (e) try { e(errStub); } catch (_) {}
      return 0;
    };
  }

  // --- Notifications ---
  if (window.Notification) {
    const orp = Notification.requestPermission;
    Notification.requestPermission = function (cb) {
      log('permissions', { api: 'Notification.requestPermission', args: '' });
      if (cb) try { cb('denied'); } catch (_) {}
      return Promise.resolve('denied');
    };
  }

  // --- Clipboard ---
  // Same secure-context issue as mediaDevices — install a shadow object so
  // calls get caught even on plain HTTP.
  try {
    if (!navigator.clipboard) {
      Object.defineProperty(navigator, 'clipboard', {
        value: {},
        configurable: true,
      });
    }
    const wrap = (name, sampleArg) => {
      navigator.clipboard[name] = function (arg) {
        const sample =
          sampleArg && typeof arg === 'string' ? String(arg).slice(0, 80) : '';
        log('clipboard', { op: name, sample });
        return denied('Clipboard blocked (safe lab)');
      };
    };
    wrap('read', false);
    wrap('readText', false);
    wrap('write', false);
    wrap('writeText', true);
  } catch (_) {}

  // --- crypto.subtle is sometimes abused by miners; record bulk calls ---
  if (window.crypto && window.crypto.subtle) {
    const oh = window.crypto.subtle.digest;
    let digestCount = 0;
    window.crypto.subtle.digest = function (...args) {
      digestCount++;
      if (digestCount === 1 || digestCount % 100 === 0) {
        log('crypto', { api: 'subtle.digest', count: digestCount });
      }
      return oh.apply(this, args);
    };
  }

  // --- Service worker registration (persistence) ---
  // ServiceWorkerContainer is normally a secure-context-only API; install
  // a shadow object so calls get caught on plain HTTP too.
  try {
    if (!navigator.serviceWorker) {
      Object.defineProperty(navigator, 'serviceWorker', {
        configurable: true,
        value: { ready: Promise.resolve({ pushManager: {} }) },
      });
    }
    navigator.serviceWorker.register = function (script, opts) {
      log('serviceWorker', {
        script: String(script).slice(0, 200),
        scope: opts && opts.scope ? String(opts.scope) : '/',
      });
      return Promise.reject(new DOMException('SW blocked (safe lab)', 'NotAllowedError'));
    };
    // Hook ready so .ready.then(reg => reg.pushManager.subscribe(...)) catches subscribes too
    const fakeReg = {
      pushManager: {
        subscribe: function (opts) {
          log('push', { opts: JSON.stringify(opts || {}).slice(0, 200) });
          return denied('Push blocked (safe lab)');
        },
      },
      unregister: () => Promise.resolve(true),
    };
    Object.defineProperty(navigator.serviceWorker, 'ready', {
      configurable: true,
      get: () => Promise.resolve(fakeReg),
    });
  } catch (_) {}

  // --- Push notification subscription ---
  try {
    if (window.PushManager && PushManager.prototype && PushManager.prototype.subscribe) {
      const oSub = PushManager.prototype.subscribe;
      PushManager.prototype.subscribe = function (opts) {
        log('push', { opts: JSON.stringify(opts || {}).slice(0, 200) });
        return denied('Push blocked (safe lab)');
      };
    }
  } catch (_) {}

  // --- Cookie / storage read interception ---
  try {
    // Intercept document.cookie reads (only if there are existing cookies — empty is normal).
    // Setting cookies is fine; READING them on a phishing page is exfil prep.
    const cookieDesc = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie');
    if (cookieDesc && cookieDesc.get) {
      const origGet = cookieDesc.get;
      Object.defineProperty(Document.prototype, 'cookie', {
        configurable: true,
        get: function () {
          const v = origGet.call(this);
          log('storage', { op: 'cookie.read', sample: (v || '').slice(0, 80) });
          return v;
        },
        set: cookieDesc.set,
      });
    }
    // Wrap localStorage / sessionStorage getItem + Object.entries(localStorage) usage.
    // We can't easily hook the iterator, but we can hook getItem + key(), which
    // catches the common "loop through all keys and exfil" pattern.
    const wrapStorage = (storageName) => {
      try {
        const storage = window[storageName];
        if (!storage) return;
        const oGet = storage.getItem.bind(storage);
        storage.getItem = function (k) {
          log('storage', { op: storageName + '.getItem', key: String(k) });
          return oGet(k);
        };
        const oKey = storage.key.bind(storage);
        storage.key = function (i) {
          log('storage', { op: storageName + '.key', index: i });
          return oKey(i);
        };
      } catch (_) {}
    };
    wrapStorage('localStorage');
    wrapStorage('sessionStorage');
  } catch (_) {}

  // --- sendBeacon (exfil via beacon API, runs even after page unload) ---
  try {
    if (navigator.sendBeacon) {
      const oBeacon = navigator.sendBeacon.bind(navigator);
      navigator.sendBeacon = function (url, data) {
        let preview = '';
        try {
          if (typeof data === 'string') preview = data.slice(0, 120);
          else if (data instanceof Blob) preview = `<Blob size=${data.size}>`;
          else preview = '<binary>';
        } catch (_) {}
        log('beacon', { url: String(url).slice(0, 200), sample: preview });
        // Block the actual exfil — return true so the page thinks it worked
        return true;
      };
    }
  } catch (_) {}

  // --- WebRTC IP leak: hook RTCPeerConnection construction ---
  try {
    if (window.RTCPeerConnection) {
      const ORTC = window.RTCPeerConnection;
      function WrappedRTC(...args) {
        log('webrtc', { api: 'RTCPeerConnection', config: JSON.stringify(args[0] || {}).slice(0, 200) });
        return new ORTC(...args);
      }
      WrappedRTC.prototype = ORTC.prototype;
      window.RTCPeerConnection = WrappedRTC;
    }
  } catch (_) {}

  // --- Crypto wallet probe: log every access to window.ethereum ---
  try {
    let walletAccessed = false;
    Object.defineProperty(window, 'ethereum', {
      configurable: true,
      get() {
        if (!walletAccessed) {
          walletAccessed = true;
          log('wallet', { api: 'window.ethereum' });
        }
        // Return a stub object so the page's check `if (window.ethereum)` is true,
        // exposing intent. Any .request() call would also be logged below.
        return {
          request: (args) => {
            log('wallet', {
              api: 'ethereum.request',
              method: (args && args.method) || 'unknown',
            });
            return denied('Wallet blocked (safe lab)');
          },
          isMetaMask: true,
        };
      },
    });
  } catch (_) {}

  // --- Fingerprinting: hook canvas.toDataURL + AudioContext + getBattery ---
  try {
    const oToData = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function (...args) {
      log('fingerprint', { api: 'canvas.toDataURL' });
      return oToData.apply(this, args);
    };
    if (navigator.getBattery) {
      const oBat = navigator.getBattery.bind(navigator);
      navigator.getBattery = function () {
        log('fingerprint', { api: 'getBattery' });
        return oBat();
      };
    }
    if (window.AudioContext || window.webkitAudioContext) {
      const OAudio = window.AudioContext || window.webkitAudioContext;
      function WrappedAudio(...args) {
        log('fingerprint', { api: 'AudioContext' });
        return new OAudio(...args);
      }
      WrappedAudio.prototype = OAudio.prototype;
      if (window.AudioContext) window.AudioContext = WrappedAudio;
    }
  } catch (_) {}

  // --- Anti-debug detection: right-click block, debugger loops ---
  try {
    document.addEventListener('contextmenu', (e) => {
      if (e.defaultPrevented) {
        log('antiDebug', { signal: 'contextmenu blocked' });
      }
    }, true);
  } catch (_) {}
})();
"""


# Substrings that strongly imply a script is a cryptominer loader.
_MINER_SIGNATURES = [
    'coinhive', 'cryptoloot', 'coinimp', 'webminerpool', 'webminer.io',
    'minero.cc', 'authedmine', 'crypto-loot', 'jsecoin', 'monerise',
    'monero-pool', 'cryptonight', 'webmine.cz',
]


@dataclass
class VisualAnalysisResult:
    """Combined visual + behavioral analysis of a URL."""

    # DOM / visual
    screenshot_taken: bool = False
    screenshot_base64: Optional[str] = None
    page_title: Optional[str] = None
    has_login_form: bool = False
    has_password_field: bool = False
    brand_indicators: List[str] = field(default_factory=list)
    visual_risk_score: float = 0.0
    error: Optional[str] = None

    # Behavioral signals (NEW)
    permission_requests: List[Dict[str, Any]] = field(default_factory=list)
    clipboard_attempts: List[Dict[str, Any]] = field(default_factory=list)
    forms: List[Dict[str, Any]] = field(default_factory=list)
    cross_origin_form_posts: List[Dict[str, Any]] = field(default_factory=list)
    iframes: List[Dict[str, Any]] = field(default_factory=list)
    hidden_iframes: List[Dict[str, Any]] = field(default_factory=list)
    redirect_chain: List[str] = field(default_factory=list)
    final_url: Optional[str] = None
    downloads: List[Dict[str, Any]] = field(default_factory=list)
    dialogs: List[Dict[str, Any]] = field(default_factory=list)
    third_party_script_origins: List[str] = field(default_factory=list)
    miner_scripts: List[str] = field(default_factory=list)
    # Advanced phishing-kit behaviors (added to catch what real kits do)
    service_worker_registrations: List[Dict[str, Any]] = field(default_factory=list)
    push_subscriptions: List[Dict[str, Any]] = field(default_factory=list)
    storage_access: List[Dict[str, Any]] = field(default_factory=list)
    beacon_exfils: List[Dict[str, Any]] = field(default_factory=list)
    webrtc_connections: List[Dict[str, Any]] = field(default_factory=list)
    wallet_probes: List[Dict[str, Any]] = field(default_factory=list)
    fingerprinting: List[Dict[str, Any]] = field(default_factory=list)
    anti_debug: List[Dict[str, Any]] = field(default_factory=list)
    behavior_findings: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "screenshot_taken": self.screenshot_taken,
            "screenshot_base64": self.screenshot_base64,
            "page_title": self.page_title,
            "has_login_form": self.has_login_form,
            "has_password_field": self.has_password_field,
            "brand_indicators": self.brand_indicators,
            "visual_risk_score": self.visual_risk_score,
            "error": self.error,
            "permission_requests": self.permission_requests,
            "clipboard_attempts": self.clipboard_attempts,
            "forms": self.forms,
            "cross_origin_form_posts": self.cross_origin_form_posts,
            "iframes": self.iframes,
            "hidden_iframes": self.hidden_iframes,
            "redirect_chain": self.redirect_chain,
            "final_url": self.final_url,
            "downloads": self.downloads,
            "dialogs": self.dialogs,
            "third_party_script_origins": self.third_party_script_origins,
            "miner_scripts": self.miner_scripts,
            "service_worker_registrations": self.service_worker_registrations,
            "push_subscriptions": self.push_subscriptions,
            "storage_access": self.storage_access,
            "beacon_exfils": self.beacon_exfils,
            "webrtc_connections": self.webrtc_connections,
            "wallet_probes": self.wallet_probes,
            "fingerprinting": self.fingerprinting,
            "anti_debug": self.anti_debug,
            "behavior_findings": self.behavior_findings,
        }


class ScreenshotAnalyzer:
    """Headless-Chromium-based safe-lab analyzer."""

    BRAND_KEYWORDS = {
        "paypal": ["paypal", "pay pal"],
        "amazon": ["amazon", "prime"],
        "apple": ["apple", "icloud", "itunes"],
        "microsoft": ["microsoft", "outlook", "office", "onedrive"],
        "google": ["google", "gmail", "youtube"],
        "facebook": ["facebook", "meta", "instagram"],
        "netflix": ["netflix"],
        "bank": ["bank", "banking", "account", "secure"],
        "dropbox": ["dropbox"],
        "linkedin": ["linkedin"],
    }

    def __init__(self, timeout: int = 10000):
        self.timeout = timeout
        self._playwright = None
        self._browser = None

    async def initialize(self):
        if self._browser:
            return
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                # navigator.mediaDevices and navigator.clipboard are only
                # exposed in secure contexts (HTTPS / localhost). Real phishing
                # kits use HTTPS via Let's Encrypt so this doesn't normally
                # matter. But our local evil-twin demo (and any plain-http
                # phishing URL we want to inspect) needs the APIs visible so
                # our wrappers can record the attempts. Treating all origins
                # as secure inside the sandbox is safe — we never grant
                # permissions, we only watch what gets asked.
                '--unsafely-treat-insecure-origin-as-secure=http://backend:3000,http://localhost:3000',
            ],
        )
        logger.info("Safe-lab analyzer initialized")

    async def close(self):
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def analyze(
        self, url: str, capture_screenshot: bool = True
    ) -> VisualAnalysisResult:
        await self.initialize()

        # All findings get collected on the result object as we go so a mid-run
        # exception still returns whatever we managed to observe.
        result = VisualAnalysisResult()

        try:
            # Brand-new context per scan — no cookie / storage carryover.
            # Don't grant any permissions; we want the page's request to fail.
            context = await self._browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent=(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/120.0.0.0 Safari/537.36'
                ),
                permissions=[],  # deny everything
            )
            await context.add_init_script(_SAFE_LAB_HOOKS)

            page = await context.new_page()

            # --- Event hookups (must be registered BEFORE goto) ---
            redirect_chain: List[str] = []
            downloads: List[Dict[str, Any]] = []
            dialogs: List[Dict[str, Any]] = []
            request_origins: List[str] = []

            def on_response(resp):
                # Track every navigation hop. If we got here from a redirect,
                # response.request.redirected_from gives the previous request.
                try:
                    req = resp.request
                    if req.is_navigation_request():
                        chain = []
                        r = req
                        # Walk back through the redirect chain.
                        while r is not None:
                            chain.append(r.url)
                            r = r.redirected_from
                        for u in reversed(chain):
                            if u not in redirect_chain:
                                redirect_chain.append(u)
                except Exception:
                    pass

            def on_request(req):
                try:
                    # Record outbound third-party script origins.
                    if req.resource_type == 'script':
                        origin = urlparse(req.url).netloc
                        if origin and origin not in request_origins:
                            request_origins.append(origin)
                except Exception:
                    pass

            async def on_download(dl):
                # Drive-by download attempt. Cancel it — we don't want to actually
                # save phishing payloads to disk.
                downloads.append({
                    'suggested_filename': dl.suggested_filename,
                    'url': dl.url,
                })
                try:
                    await dl.cancel()
                except Exception:
                    pass

            async def on_dialog(dialog):
                dialogs.append({
                    'type': dialog.type,
                    'message': (dialog.message or '')[:200],
                })
                try:
                    await dialog.dismiss()
                except Exception:
                    pass

            page.on('response', on_response)
            page.on('request', on_request)
            page.on('download', lambda dl: asyncio.create_task(on_download(dl)))
            page.on('dialog', lambda d: asyncio.create_task(on_dialog(d)))

            # --- Navigate ---
            try:
                await page.goto(
                    url, wait_until='networkidle', timeout=self.timeout
                )
            except PlaywrightTimeout:
                logger.warning(f"Timeout loading {url}")
                result.error = "Page load timeout"
                # Continue with whatever we captured before timeout — partial
                # data is still useful for a phishing report.

            # Small grace period for late-firing scripts (geo prompts often
            # appear a beat after page load).
            try:
                await page.wait_for_timeout(800)
            except Exception:
                pass

            # --- Pull behavior log from the page ---
            try:
                safe_lab = await page.evaluate("window.__safeLab || {}")
            except Exception:
                safe_lab = {}
            result.permission_requests = safe_lab.get('permissions', [])[:20]
            result.clipboard_attempts = safe_lab.get('clipboard', [])[:20]
            result.service_worker_registrations = safe_lab.get('serviceWorker', [])[:10]
            result.push_subscriptions = safe_lab.get('push', [])[:10]
            result.storage_access = safe_lab.get('storage', [])[:40]
            result.beacon_exfils = safe_lab.get('beacon', [])[:20]
            result.webrtc_connections = safe_lab.get('webrtc', [])[:10]
            result.wallet_probes = safe_lab.get('wallet', [])[:10]
            result.fingerprinting = safe_lab.get('fingerprint', [])[:20]
            result.anti_debug = safe_lab.get('antiDebug', [])[:10]

            # --- Page metadata ---
            try:
                result.page_title = await page.title()
            except Exception:
                result.page_title = None

            try:
                result.has_login_form = await self._detect_login_form(page)
                result.has_password_field = await self._detect_password_field(page)
            except Exception:
                pass

            # --- Inspect forms + iframes ---
            try:
                form_iframe_info = await page.evaluate(
                    """() => {
                        const norm = (u) => { try { return new URL(u, location.href).href; } catch(_) { return u || ''; } };
                        return {
                            forms: Array.from(document.querySelectorAll('form')).slice(0, 20).map(f => ({
                                action: norm(f.getAttribute('action') || location.href),
                                method: (f.method || 'get').toUpperCase(),
                                has_password: !!f.querySelector('input[type="password"]'),
                                has_card: !!f.querySelector('input[autocomplete*="cc-"], input[name*="card" i], input[name*="cvv" i]'),
                                input_count: f.querySelectorAll('input').length,
                            })),
                            iframes: Array.from(document.querySelectorAll('iframe')).slice(0, 20).map(f => {
                                const cs = getComputedStyle(f);
                                const hidden =
                                    cs.display === 'none' ||
                                    cs.visibility === 'hidden' ||
                                    parseFloat(cs.opacity) === 0 ||
                                    (f.offsetWidth <= 2 && f.offsetHeight <= 2);
                                return {
                                    src: f.src || '',
                                    hidden,
                                    width: f.offsetWidth,
                                    height: f.offsetHeight,
                                };
                            }),
                        };
                    }"""
                )
            except Exception:
                form_iframe_info = {'forms': [], 'iframes': []}

            page_origin = urlparse(page.url).netloc

            forms = form_iframe_info.get('forms', [])
            result.forms = forms
            for f in forms:
                action_origin = urlparse(f.get('action', '')).netloc
                is_cross_origin = (
                    bool(action_origin) and action_origin != page_origin
                )
                action_is_http = (f.get('action', '') or '').startswith('http://')
                if (
                    (is_cross_origin or action_is_http)
                    and (f.get('has_password') or f.get('has_card'))
                ):
                    result.cross_origin_form_posts.append({
                        **f,
                        'page_origin': page_origin,
                        'action_origin': action_origin,
                        'is_cross_origin': is_cross_origin,
                        'cleartext': action_is_http,
                    })

            iframes = form_iframe_info.get('iframes', [])
            result.iframes = iframes
            for fr in iframes:
                if fr.get('hidden'):
                    result.hidden_iframes.append(fr)

            # --- Network-derived signals ---
            result.redirect_chain = redirect_chain[:30]
            result.final_url = page.url
            result.downloads = downloads
            result.dialogs = dialogs
            result.third_party_script_origins = [
                o for o in request_origins if o and o != page_origin
            ][:30]
            result.miner_scripts = [
                o for o in result.third_party_script_origins
                if any(sig in o.lower() for sig in _MINER_SIGNATURES)
            ]
            # Also scan ALL request URLs for miner patterns, not just origins
            # (some loaders use innocuous-looking origins but obvious paths).
            try:
                # Re-evaluate script src list from the DOM as a fallback.
                src_list = await page.evaluate(
                    "Array.from(document.querySelectorAll('script[src]')).slice(0, 50).map(s => s.src)"
                )
                for src in src_list:
                    if any(sig in src.lower() for sig in _MINER_SIGNATURES):
                        if src not in result.miner_scripts:
                            result.miner_scripts.append(src)
            except Exception:
                pass

            # --- Brand keywords in rendered HTML ---
            try:
                page_content = (await page.content()).lower()
                result.brand_indicators = self._detect_brands(
                    page_content, (result.page_title or '').lower()
                )
            except Exception:
                pass

            # --- Screenshot ---
            if capture_screenshot:
                try:
                    screenshot_bytes = await page.screenshot(
                        type='png', full_page=False
                    )
                    result.screenshot_base64 = base64.b64encode(
                        screenshot_bytes
                    ).decode()
                    result.screenshot_taken = True
                except Exception as e:
                    logger.warning(f"Screenshot capture failed: {e}")

            # --- Build human-readable findings list (drives UI bullets) ---
            result.behavior_findings = self._summarize_findings(result)

            # --- Visual risk score (kept for back-compat with risk_scorer) ---
            result.visual_risk_score = self._calculate_visual_risk(result)

            await context.close()
            return result

        except Exception as e:
            logger.error(f"Safe-lab analysis failed for {url}: {e}", exc_info=True)
            result.error = str(e)
            return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _detect_login_form(self, page) -> bool:
        login_selectors = [
            'form[action*="login"]',
            'form[action*="signin"]',
            'form[action*="auth"]',
            'input[name="username"]',
            'input[name="email"][type="email"]',
            'input[name="user"]',
        ]
        for selector in login_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    return True
            except Exception:
                pass
        return False

    async def _detect_password_field(self, page) -> bool:
        try:
            f = await page.query_selector('input[type="password"]')
            return f is not None
        except Exception:
            return False

    def _detect_brands(self, content: str, title: str) -> List[str]:
        detected: List[str] = []
        combined = content + ' ' + title
        for brand, keywords in self.BRAND_KEYWORDS.items():
            for kw in keywords:
                if kw in combined:
                    if brand not in detected:
                        detected.append(brand)
                    break
        return detected

    def _summarize_findings(
        self, r: VisualAnalysisResult
    ) -> List[Dict[str, str]]:
        """Turn raw observations into short, severity-tagged bullets the
        mobile UI can render directly."""
        findings: List[Dict[str, str]] = []

        # Permission requests
        for p in r.permission_requests:
            api = p.get('api', '')
            label = {
                'getUserMedia': 'Asked for camera or microphone access',
                'getDisplayMedia': 'Asked to record your screen',
                'geolocation.getCurrentPosition': 'Asked for your location',
                'geolocation.watchPosition': 'Asked to track your location',
                'Notification.requestPermission': 'Asked to send notifications',
            }.get(api, f"Called sensitive API: {api}")
            severity = 'critical' if api.startswith('getUser') or api.startswith('getDisplay') else 'high'
            findings.append({'severity': severity, 'text': label})

        # Clipboard
        for c in r.clipboard_attempts:
            op = c.get('op', '')
            if op in ('readText', 'read'):
                findings.append({
                    'severity': 'critical',
                    'text': 'Tried to read your clipboard',
                })
            elif op in ('writeText', 'write'):
                findings.append({
                    'severity': 'high',
                    'text': 'Tried to overwrite your clipboard '
                            '(common in crypto-wallet address swap attacks)',
                })

        # Cross-origin / cleartext form POSTs
        for f in r.cross_origin_form_posts:
            target = f.get('action_origin') or '(empty)'
            if f.get('cleartext'):
                findings.append({
                    'severity': 'critical',
                    'text': f"Password/card form posts over HTTP (cleartext) to {target}",
                })
            else:
                findings.append({
                    'severity': 'critical',
                    'text': f"Password/card form posts to unrelated site: {target}",
                })

        # Hidden iframes
        for fr in r.hidden_iframes:
            src = fr.get('src') or '(about:blank)'
            findings.append({
                'severity': 'high',
                'text': f"Hidden iframe loading: {src}",
            })

        # Redirect chain — only worth flagging if there are 3+ hops or the
        # final hostname differs significantly from the original.
        if len(r.redirect_chain) >= 3:
            findings.append({
                'severity': 'medium',
                'text': f"Bounced through {len(r.redirect_chain)} URLs before landing",
            })

        # Auto-downloads
        for dl in r.downloads:
            findings.append({
                'severity': 'critical',
                'text': f"Auto-triggered download: {dl.get('suggested_filename') or dl.get('url')}",
            })

        # Dialogs (alert/confirm/prompt) — often used in tech-support scams
        for d in r.dialogs:
            findings.append({
                'severity': 'medium',
                'text': f"Popup dialog ({d.get('type')}): {d.get('message')}",
            })

        # Miner scripts
        for ms in r.miner_scripts:
            findings.append({
                'severity': 'critical',
                'text': f"Cryptominer script loaded: {ms}",
            })

        # Many third-party scripts
        if len(r.third_party_script_origins) >= 8:
            findings.append({
                'severity': 'low',
                'text': f"Loads scripts from {len(r.third_party_script_origins)} third-party sources",
            })

        # Service worker registration (persistence)
        for sw in r.service_worker_registrations:
            findings.append({
                'severity': 'critical',
                'text': f"Installed a service worker (persists after tab close): {sw.get('script', '')}",
            })

        # Push subscription
        if r.push_subscriptions:
            findings.append({
                'severity': 'high',
                'text': 'Subscribed for push notifications '
                        '(real kits use this to deliver fake transaction alerts later)',
            })

        # Storage access (cookies, localStorage)
        cookie_reads = [s for s in r.storage_access if s.get('op') == 'cookie.read']
        ls_reads = [
            s for s in r.storage_access
            if 'getItem' in s.get('op', '') or s.get('op', '').endswith('.key')
        ]
        if cookie_reads:
            findings.append({
                'severity': 'critical',
                'text': f"Read document.cookie ({len(cookie_reads)} times) — session-token theft attempt",
            })
        if ls_reads:
            findings.append({
                'severity': 'high',
                'text': f"Scraped local/session storage ({len(ls_reads)} reads)",
            })

        # Beacon exfil
        for b in r.beacon_exfils:
            target = b.get('url', '')
            try:
                target_host = urlparse(target).netloc
            except Exception:
                target_host = target
            findings.append({
                'severity': 'critical',
                'text': f"Tried to exfiltrate data via sendBeacon to {target_host}",
            })

        # WebRTC
        if r.webrtc_connections:
            findings.append({
                'severity': 'high',
                'text': 'Opened a WebRTC peer connection '
                        '(commonly used to leak the real IP behind a VPN)',
            })

        # Crypto wallet probe
        wallet_calls = [w for w in r.wallet_probes if w.get('api') == 'ethereum.request']
        wallet_accesses = [w for w in r.wallet_probes if w.get('api') == 'window.ethereum']
        if wallet_calls:
            for w in wallet_calls:
                findings.append({
                    'severity': 'critical',
                    'text': f"Tried to invoke crypto wallet: {w.get('method')} (wallet drainer)",
                })
        elif wallet_accesses:
            findings.append({
                'severity': 'high',
                'text': 'Probed for an installed crypto wallet (window.ethereum)',
            })

        # Fingerprinting — flag even a single technique as suspicious on a
        # phishing-looking page; legitimate sites don't typically read canvas
        # toDataURL for sub-resource use.
        fp_apis = {f.get('api') for f in r.fingerprinting}
        if fp_apis:
            severity = 'high' if len(fp_apis) >= 2 else 'medium'
            findings.append({
                'severity': severity,
                'text': f"Browser fingerprinting attempt "
                        f"({', '.join(sorted(fp_apis))})",
            })

        # Anti-debug signals
        if any(a.get('signal') == 'contextmenu blocked' for a in r.anti_debug):
            findings.append({
                'severity': 'medium',
                'text': 'Right-click / inspect blocked (anti-analysis)',
            })

        # Dedupe: same (severity, text) collapses to one entry, appending (×N)
        # when there were multiple occurrences.
        from collections import OrderedDict
        counts: 'OrderedDict[tuple, int]' = OrderedDict()
        for f in findings:
            key = (f.get('severity', ''), f.get('text', ''))
            counts[key] = counts.get(key, 0) + 1
        return [
            {'severity': sev, 'text': txt + (f' (×{n})' if n > 1 else '')}
            for (sev, txt), n in counts.items()
        ]

    def _calculate_visual_risk(self, r: VisualAnalysisResult) -> float:
        """Score 0–100 combining DOM + behavioral signals."""
        score = 0
        if r.has_login_form:
            score += 15
        if r.has_password_field:
            score += 15
        if r.brand_indicators:
            score += 10 * min(len(r.brand_indicators), 3)
        # Behavioral bumps
        critical_findings = sum(
            1 for f in r.behavior_findings if f.get('severity') == 'critical'
        )
        high_findings = sum(
            1 for f in r.behavior_findings if f.get('severity') == 'high'
        )
        score += critical_findings * 25
        score += high_findings * 12
        return min(100, score)


# Singleton accessor used by main.py
_analyzer: Optional[ScreenshotAnalyzer] = None


async def get_analyzer() -> ScreenshotAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = ScreenshotAnalyzer()
        await _analyzer.initialize()
    return _analyzer
