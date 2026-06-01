#!/usr/bin/env python3
"""Recolor the two landscape SVGs from sky-blue to the app's indigo palette."""
import re

def recolor(src, dst, app_text_white=True):
    t = open(src).read()
    # 1) sky-blue gradient stops -> indigo (mid-dark so white text reads)
    t = t.replace('<stop offset="0" stop-color="#38bdf8"/><stop offset="1" stop-color="#0ea5e9"/>',
                  '<stop offset="0" stop-color="#6366f1"/><stop offset="1" stop-color="#4f46e5"/>')
    # 2) dark navy text that sat on the sky tier -> white (like the app's indigo header)
    if app_text_white:
        t = t.replace('fill="#082f49"', 'fill="#ffffff"')
    # 3) cyan info badges -> indigo
    t = t.replace('fill="#0c4a6e" stroke="#38bdf8"', 'fill="#312e81" stroke="#818cf8"')
    t = t.replace('fill="#bae6fd"', 'fill="#c7d2fe"')
    # 4) any remaining sky accents (strokes, side labels, loop arrow) -> indigo
    t = t.replace('#38bdf8', '#818cf8').replace('#0ea5e9', '#4f46e5')
    open(dst, 'w').write(t)
    print("wrote", dst)

recolor('/opt/ai-anti-spam-shield-crm/defense/system-architecture.svg',
        'system-architecture-indigo.svg')
recolor('/opt/ai-anti-spam-shield-crm/defense/continuous-learning-architecture.svg',
        'continuous-learning-indigo.svg')
