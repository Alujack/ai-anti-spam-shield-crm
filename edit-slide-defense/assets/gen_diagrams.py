#!/usr/bin/env python3
"""Generate clean dark-navy / indigo->purple pipeline diagrams for the defense deck.
Matches the style of defense/system-architecture.svg. Render with rsvg-convert."""
import html

# ---- brand tokens (mobile app palette) ----
BG0, BG1   = "#0f172a", "#1e293b"   # slate-900 -> slate-800
CARD       = "#1e293b"              # panel
CARD2      = "#273449"
STROKE     = "#334155"
INDIGO     = "#4f46e5"
INDIGO_L   = "#818cf8"
PURPLE     = "#7c3aed"
PURPLE_L   = "#a78bfa"
TXT        = "#f8fafc"
SUB        = "#94a3b8"
MONO       = "#cbd5e1"
GREEN      = "#10b981"
RED        = "#ef4444"
ARROW      = "#64748b"

def esc(s): return html.escape(s, quote=False)

DEFS = f"""
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{BG0}"/><stop offset="1" stop-color="{BG1}"/>
    </linearGradient>
    <linearGradient id="chip" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{INDIGO}"/><stop offset="1" stop-color="{PURPLE}"/>
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{INDIGO}"/><stop offset="1" stop-color="{PURPLE}"/>
    </linearGradient>
    <marker id="arrow" markerWidth="14" markerHeight="14" refX="5" refY="6" orient="auto" markerUnits="userSpaceOnUse">
      <path d="M0,0 L11,6 L0,12 Z" fill="{ARROW}"/>
    </marker>
    <filter id="sh" x="-30%" y="-30%" width="160%" height="160%">
      <feDropShadow dx="0" dy="6" stdDeviation="10" flood-color="#000000" flood-opacity="0.45"/>
    </filter>
  </defs>
"""

def header(w, title, sub):
    return (f'<text x="60" y="84" fill="{TXT}" font-size="50" font-weight="800">{esc(title)}</text>'
            f'<text x="62" y="128" fill="{SUB}" font-size="26">{esc(sub)}</text>'
            f'<rect x="60" y="150" width="120" height="6" rx="3" fill="url(#accent)"/>')

def vchevron(cx, y):
    return f'<path d="M{cx-16},{y} L{cx},{y+18} L{cx+16},{y}" fill="none" stroke="{ARROW}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'

def step_card(x, y, w, h, num, title, example, accent=INDIGO):
    out = f'<g filter="url(#sh)"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{CARD}" stroke="{STROKE}" stroke-width="1.5"/></g>'
    # left accent stripe
    out += f'<rect x="{x}" y="{y}" width="8" height="{h}" rx="4" fill="{accent}"/>'
    # number chip
    cx, cy = x+62, y+h//2
    out += f'<circle cx="{cx}" cy="{cy}" r="34" fill="url(#chip)"/>'
    out += f'<text x="{cx}" y="{cy+13}" fill="#ffffff" font-size="36" font-weight="800" text-anchor="middle">{num}</text>'
    tx = x+120
    out += f'<text x="{tx}" y="{y+(h//2)-8 if example else y+h//2+12}" fill="{TXT}" font-size="32" font-weight="700">{esc(title)}</text>'
    if example:
        out += f'<text x="{tx}" y="{y+(h//2)+34}" fill="{SUB}" font-size="23" font-family="DejaVu Sans Mono, monospace">{esc(example)}</text>'
    return out

def pill(x, y, w, h, label, fill, txt="#ffffff", fs=30):
    return (f'<g filter="url(#sh)"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h//2}" fill="{fill}"/></g>'
            f'<text x="{x+w//2}" y="{y+h//2+fs//3}" fill="{txt}" font-size="{fs}" font-weight="700" text-anchor="middle">{esc(label)}</text>')

def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'font-family="Segoe UI, Helvetica, Arial, sans-serif">{DEFS}'
            f'<rect width="{w}" height="{h}" fill="url(#bg)"/>{body}</svg>')

# ============================================================
# 1) TEXT PREPROCESSING  (portrait, slot ratio 0.547)
# ============================================================
W, H = 820, 1500
b = header(W, "Text Preprocessing", "Same clean-up for every model, step by step")
steps = [
    ("1", "Lowercase everything", '"URGENT! Click" → "urgent! click"'),
    ("2", "Strip out web links", 'http://spam.link → (removed)'),
    ("3", "Strip out emails", 'name@scam.com → (removed)'),
    ("4", "Strip out phone numbers", '+855 12 345 678 → (removed)'),
    ("5", "Remove symbols & emojis", 'keep plain letters only'),
    ("6", "Drop common words", 'the, is, at, which ... gone'),
    ("7", "Stem words to the root", '"running", "ran" → "run"'),
]
y0, ch, gap = 196, 150, 14
cw, cx = 700, 60
for i,(n,t,e) in enumerate(steps):
    y = y0 + i*(ch+gap)
    b += step_card(cx, y, cw, ch, n, t, e)
    if i < len(steps):
        b += vchevron(cx+cw//2, y+ch+ (gap-18)//2 +1)
yout = y0 + len(steps)*(ch+gap)
b += f'<g filter="url(#sh)"><rect x="{cx}" y="{yout}" width="{cw}" height="120" rx="18" fill="{GREEN}"/></g>'
b += f'<text x="{cx+cw//2}" y="{yout+52}" fill="#06281d" font-size="34" font-weight="800" text-anchor="middle">Clean text, ready for the model</text>'
b += f'<text x="{cx+cw//2}" y="{yout+92}" fill="#06281d" font-size="24" text-anchor="middle">fewer noisy tokens -> sharper signal</text>'
open("preprocessing.svg","w").write(svg(W,H,b))

# ============================================================
# 2) MODEL TRAINING PIPELINE  (slot ratio 0.798)
# ============================================================
W, H = 1120, 1404
b = header(W, "How We Train Each Model", "From raw dataset to a saved, ready-to-use model")
def big_card(x,y,w,h,num,title,sub,accent=INDIGO):
    out = f'<g filter="url(#sh)"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="20" fill="{CARD}" stroke="{STROKE}" stroke-width="1.5"/></g>'
    out += f'<rect x="{x}" y="{y}" width="{w}" height="8" rx="4" fill="{accent}"/>'
    out += f'<circle cx="{x+50}" cy="{y+54}" r="28" fill="url(#chip)"/>'
    out += f'<text x="{x+50}" y="{y+65}" fill="#fff" font-size="30" font-weight="800" text-anchor="middle">{num}</text>'
    out += f'<text x="{x+96}" y="{y+62}" fill="{TXT}" font-size="30" font-weight="700">{esc(title)}</text>'
    out += f'<text x="{x+28}" y="{y+112}" fill="{SUB}" font-size="24">{esc(sub)}</text>'
    return out
cw, ch = 320, 158
xs = [60, 400, 740]
r1y, r2y = 250, 600
r1 = [("1","Load dataset","from HuggingFace"),
      ("2","Clean the text","7-step preprocessing"),
      ("3","Split the data","80% train / 20% test")]
r2 = [("4","Build TF-IDF","turn words into numbers"),
      ("5","Train classifier","LogReg / Random Forest"),
      ("6","Evaluate","score on the held-out 20%")]
for i,(n,t,s) in enumerate(r1):
    b += big_card(xs[i], r1y, cw, ch, n, t, s)
    if i<2: b += f'<line x1="{xs[i]+cw}" y1="{r1y+ch//2}" x2="{xs[i+1]}" y2="{r1y+ch//2}" stroke="{ARROW}" stroke-width="5" marker-end="url(#arrow)"/>'
# down arrow from card3 to card6 (serpentine)
b += f'<line x1="{xs[2]+cw//2}" y1="{r1y+ch}" x2="{xs[2]+cw//2}" y2="{r2y}" stroke="{ARROW}" stroke-width="5" marker-end="url(#arrow)"/>'
for i,(n,t,s) in enumerate(r2):
    b += big_card(xs[i], r2y, cw, ch, n, t, s, accent=PURPLE)
    if i<2: b += f'<line x1="{xs[i+1]}" y1="{r2y+ch//2}" x2="{xs[i]+cw}" y2="{r2y+ch//2}" stroke="{ARROW}" stroke-width="5" marker-end="url(#arrow)"/>'
# down from card4 (leftmost of r2) to save bar
savey = 960
b += f'<line x1="{xs[0]+cw//2}" y1="{r2y+ch}" x2="{xs[0]+cw//2}" y2="{savey}" stroke="{ARROW}" stroke-width="5" marker-end="url(#arrow)"/>'
# save artifacts bar
b += f'<g filter="url(#sh)"><rect x="60" y="{savey}" width="1000" height="250" rx="20" fill="url(#chip)"/></g>'
b += f'<text x="560" y="{savey+58}" fill="#fff" font-size="34" font-weight="800" text-anchor="middle">Save the trained model</text>'
files = [("classifier.pkl","the model itself"),("vectorizer.pkl","word → number map"),("metadata.json","scores & settings")]
fx=[110,440,770]
for i,(f,d) in enumerate(files):
    b += f'<g filter="url(#sh)"><rect x="{fx[i]}" y="{savey+96}" width="280" height="116" rx="14" fill="#ffffff"/></g>'
    b += f'<text x="{fx[i]+140}" y="{savey+146}" fill="{INDIGO}" font-size="26" font-weight="800" text-anchor="middle" font-family="DejaVu Sans Mono, monospace">{esc(f)}</text>'
    b += f'<text x="{fx[i]+140}" y="{savey+184}" fill="#475569" font-size="22" text-anchor="middle">{esc(d)}</text>'
# footnote
b += f'<text x="60" y="{savey+312}" fill="{SUB}" font-size="24">Same recipe for all three models — only the algorithm and dataset change.</text>'
open("training.svg","w").write(svg(W,H,b))

# ============================================================
# 3) VOICE PROCESSING PIPELINE  (portrait, slot ratio 0.535)
# ============================================================
W, H = 800, 1496
b = header(W, "Voice Message Check", "From an audio clip to a scam / safe answer")
cx, cw = 60, 680
# audio input pill
b += pill(cx, 196, cw, 92, "Audio in  (WAV / MP3 / OGG)", INDIGO, fs=30)
y0, ch, gap = 340, 184, 26
vsteps = [
    ("1","Load the audio","PyDub - convert, 16 kHz, mono"),
    ("2","Speech to text","Google Speech Recognition -> words"),
    ("3","Clean the text","same 7-step preprocessing"),
    ("4","Classify the voice","TF-IDF + Random Forest"),
]
for i,(n,t,e) in enumerate(vsteps):
    y = y0 + i*(ch+gap)
    acc = PURPLE if i==3 else INDIGO
    b += step_card(cx, y, cw, ch, n, t, e, accent=acc)
    b += vchevron(cx+cw//2, y+ch+ (gap-18)//2)
# multi-modal note under step 4
y4 = y0 + 3*(ch+gap)
b += f'<text x="{cx+120}" y="{y4+ch-18}" fill="{PURPLE_L}" font-size="21">+ audio tone &amp; prosody signals</text>'
yout = y0 + len(vsteps)*(ch+gap)
b += f'<g filter="url(#sh)"><rect x="{cx}" y="{yout}" width="{cw}" height="196" rx="18" fill="{CARD2}" stroke="{STROKE}" stroke-width="1.5"/></g>'
b += f'<rect x="{cx}" y="{yout}" width="8" height="196" rx="4" fill="{GREEN}"/>'
b += f'<text x="{cx+34}" y="{yout+46}" fill="{TXT}" font-size="28" font-weight="800">Result</text>'
lines = ['transcription: "..."', 'is_scam: true / false', 'confidence: 0.95', 'threat_indicators: [ ... ]']
for i,l in enumerate(lines):
    b += f'<text x="{cx+34}" y="{yout+86+i*30}" fill="{MONO}" font-size="23" font-family="DejaVu Sans Mono, monospace">{esc(l)}</text>'
open("voice.svg","w").write(svg(W,H,b))

print("wrote preprocessing.svg, training.svg, voice.svg")
