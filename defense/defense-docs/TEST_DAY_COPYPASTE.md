# Test Day — Copy-Paste Sheet

> Open this on your laptop while running the demo on your phone.
> Backend: **production** — `https://aiscamshield.codes`. Nothing to start locally.
> Mobile build: `constants.dart` already points at prod (verified 2026-05-25).

---

## 0. Pre-flight (60 seconds)

- [ ] Phone on Wi-Fi, Do-Not-Disturb ON, brightness max.
- [ ] App reinstalled OR signed out, so the Splash → Login flow shows.
- [ ] Production reachable: open `https://aiscamshield.codes/` in your laptop browser → should load.
- [ ] Safe-lab page reachable: open `https://aiscamshield.codes/safe-lab-demo/` in your **phone's** browser → fake PayPal page loads. (No Cloudflare tunnel needed — already hosted on prod.)
- [ ] Mic permission for the screen recorder is ON.

---

## 1. Landing page (laptop browser)

**URL to open:**
```
https://aiscamshield.codes/
```

What to show on camera:
1. Hero section — slow scroll top → bottom.
2. Click the **Download** button (debounced 3s, so don't double-tap) → confirm it opens the app deep-link / store page.
3. Back to top before cutting to phone.

---

## 2. Login on mobile

Use **your own existing credentials** (the account already seeded on prod).
After login you should land on the Home dashboard with the 6 quick-action cards.

---

## 3. Text scan — paste this into the home text field

```
URGENT: Your account is locked. Verify now: bit.ly/3xR8sQp or your balance will be frozen in 24 hours.
```

Expected: **SPAM**, confidence above 0.80, red gradient screen.
Then tap **"This is spam"** → toast → tap **Report** → scroll the pre-filled form → back.

---

## 4. Voice scan — say this into the mic

Tap the mic icon on Home. Record ~5 seconds:

```
Hello, this is the bank. We need to verify your account immediately.
```

Expected: SCAM result with transcription + fused score.

---

## 5. URL scans — paste in order

### 5a. Calibration warm-up (do this BEFORE you press record)
| # | URL | Expected verdict |
|---|-----|------------------|
| A | `https://www.google.com` | SAFE 100% |
| B | `https://newsbwebmail.weebly.com/` | PHISHING — MEDIUM ~55% |
| C | `https://aiscamshield.codes/safe-lab-demo/` | PHISHING — CRITICAL ~90%, 17 behaviors |

If any of A/B/C is wrong → the ml-service container needs a kick. Stop and fix before recording.

### 5b. On-camera URL scans (in this order)

**Scan 1 — simple typosquat:**
```
http://paypa1-secure-login.com/verify
```
Expected: CRITICAL — brand impersonation, "digit 1 swap" indicator.

**Scan 2 — safe-lab evil twin (the killer demo):**
```
https://aiscamshield.codes/safe-lab-demo/
```
Expected after ~7-9 second loading animation:
- Verdict: **PHISHING — CRITICAL — 90%**
- Inline screenshot of the fake PayPal page
- "Safe-Lab Behavior" section with **17 findings** — scroll slowly, hold ~5 seconds.

**After the scan, open the same URL in the phone's regular browser** to show the fake PayPal page looks normal to a real user.

---

## 6. Optional — free-hosting credential harvester (skip if running long)

```
https://newsbwebmail.weebly.com/
```
Expected: PHISHING — MEDIUM ~55%, free-hosting + credential-harvest indicators.

---

## 7. The 17 safe-lab behaviors (memorize, recite on camera)

1. Camera / microphone (getUserMedia)
2. Screen capture (getDisplayMedia)
3. Geolocation
4. Notification prompt
5. Clipboard read (steals 2FA / wallet)
6. Clipboard write (wallet-address swap)
7. Cross-origin form POST (cleartext credit card)
8. Hidden iframes (1×1 / display:none)
9. Auto-triggered download (drive-by)
10. Popup dialogs (scareware)
11. Service-worker registration (persistence)
12. Push subscription (fake alerts later)
13. document.cookie read (session theft)
14. sendBeacon exfiltration
15. WebRTC peer connection (real IP leak behind VPN)
16. window.ethereum probe (wallet drainer)
17. Browser fingerprinting (canvas / battery / audio)

---

## 8. If something breaks

| Problem | Recovery line |
|---------|---------------|
| Scan returns wrong result | *"Interesting — this borderline case sits below the 0.55 threshold. Exactly the kind of sample our retraining loop is built for."* |
| Safe-lab returns 0 behaviors | The ml-service is cold. Restart it server-side, narrate the static URL detection instead. |
| Phone loses Wi-Fi | Cut to backup video, voice-over continues. |
| App crashes | *"This is why we have automatic crash reporting in production."* Restart, continue from last shot. |

---

## 9. After the test

- [ ] Confirm scans show up in History.
- [ ] Confirm one threat / incident / alert was created and is visible on the SOC dashboard.
- [ ] If you used the safe-lab URL, the cached re-scan should return in <50ms — try scanning it a second time to demo cache speed (optional).
