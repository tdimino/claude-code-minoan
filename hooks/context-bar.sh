#!/usr/bin/env python3
"""Dynamic context bar for ccstatusline — gradient + appended percentage."""
import sys, json

data = json.load(sys.stdin)
cw = data.get("context_window", {})
pct = cw.get("used_percentage")
pct = int(float(pct)) if pct is not None else 0

WIDTH = 10
filled = max(0, min(WIDTH, pct * WIDTH // 100))

# Gradient stops: position% → (r, g, b)
STOPS = [
    (0,   (46, 204, 113)),   # green
    (40,  (162, 195, 80)),   # yellow-green
    (65,  (241, 196, 15)),   # gold
    (80,  (230, 126, 34)),   # orange
    (100, (231, 76, 60)),    # red
]

def gradient_color(pos_pct):
    for i in range(len(STOPS) - 1):
        p1, c1 = STOPS[i]
        p2, c2 = STOPS[i + 1]
        if pos_pct <= p2:
            t = (pos_pct - p1) / (p2 - p1) if p2 != p1 else 0
            return tuple(int(c1[j] + t * (c2[j] - c1[j])) for j in range(3))
    return STOPS[-1][1]

def fg(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

RESET = "\033[0m"
DIM = "\033[2m"

# Build gradient bar
out = ""
for i in range(WIDTH):
    pos_pct = (i / (WIDTH - 1)) * 100 if WIDTH > 1 else 0
    color = gradient_color(pos_pct)
    if i < filled:
        out += fg(*color) + "█" + RESET
    else:
        out += DIM + fg(*color) + "░" + RESET

# Append percentage after bar
danger = gradient_color(min(pct, 100))
out += " " + fg(*danger) + f"{pct}%" + RESET

# Append token count after separator
used_tokens = cw.get("context_window_size", 0) * pct // 100 if pct else 0
if used_tokens >= 1000:
    token_str = f"{used_tokens // 1000}k"
else:
    token_str = str(used_tokens)
MUTED = fg(184, 184, 184)  # #b8b8b8 — site's --color-text-muted
out += DIM + " | " + RESET + MUTED + token_str + RESET

sys.stdout.write(out)
