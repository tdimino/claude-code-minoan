#!/usr/bin/env python3
"""Generate GSAP timeline animations and frame-switching state machines for pixel-art SVG mascots.

Two animation systems (reverse-engineered from ayotomcs.me/claude-mascot):
1. GSAP Timeline: Continuous motion (walking, bouncing, waving)
2. Frame Switcher: setTimeout-based sprite sheet cycling with variable timing

Usage:
  python3 animation_builder.py --preset walk-and-bounce
  python3 animation_builder.py --list
  python3 animation_builder.py --preset bounce --svg mascot.svg --render -o demo.html
"""

import argparse
import json
import sys
from pathlib import Path
from string import Template

SKILL_DIR = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# GSAP Animation Presets
# ---------------------------------------------------------------------------

PRESETS = {}


def preset(name):
    """Decorator to register an animation preset."""
    def wrapper(fn):
        PRESETS[name] = fn
        return fn
    return wrapper


@preset("idle")
def _idle(svg_id, speed=1.0, **kw):
    d = 0.8 / speed
    return f"""
(function() {{
  const svg = document.getElementById("{svg_id}");
  if (!svg) return;
  const eyes = svg.querySelector("#eyes") || svg.querySelector("[id*=eye]");
  const tl = gsap.timeline({{ repeat: -1, repeatDelay: {2.0/speed} }});
  if (eyes) {{
    tl.to(eyes, {{ scaleY: 0.1, duration: {0.08/speed}, ease: "power2.in" }})
      .to(eyes, {{ scaleY: 1, duration: {0.08/speed}, ease: "power2.out" }});
  }}
  tl.to(svg, {{ y: -3, duration: {d}, ease: "sine.inOut" }})
    .to(svg, {{ y: 0, duration: {d}, ease: "sine.inOut" }});
}})();
"""


@preset("bounce")
def _bounce(svg_id, speed=1.0, height=18, **kw):
    return f"""
(function() {{
  const svg = document.getElementById("{svg_id}");
  if (!svg) return;
  const body = svg.querySelector("#body") || svg;
  const tl = gsap.timeline({{ repeat: -1, repeatDelay: {1.5/speed} }});
  tl.to(body, {{ y: -{height}, duration: {0.18/speed}, ease: "power2.out" }})
    .to(body, {{ y: 0, duration: {0.15/speed}, ease: "power3.in" }});
}})();
"""


@preset("wave")
def _wave(svg_id, speed=1.0, **kw):
    d = 0.3 / speed
    return f"""
(function() {{
  const svg = document.getElementById("{svg_id}");
  if (!svg) return;
  const hand = svg.querySelector("#right-hand") || svg.querySelector("[id*=hand]");
  if (!hand) return;
  const tl = gsap.timeline({{ repeat: -1, repeatDelay: {2.0/speed} }});
  tl.to(hand, {{ y: -12, duration: {d}, ease: "power2.out" }})
    .to(hand, {{ rotation: -15, svgOrigin: "center bottom", duration: {d*0.7}, ease: "power2.out" }})
    .to(hand, {{ rotation: 15, duration: {d*0.5}, ease: "power2.inOut" }})
    .to(hand, {{ rotation: -10, duration: {d*0.5}, ease: "power2.inOut" }})
    .to(hand, {{ rotation: 0, y: 0, duration: {d}, ease: "power2.in" }});
}})();
"""


@preset("walk")
def _walk(svg_id, speed=1.0, direction="right", **kw):
    sign = 1 if direction == "right" else -1
    step_d = 0.1 / speed
    # Pre-compute the offset for the second tween in each step pair
    step_d2 = step_d * 2
    return f"""
(function() {{
  const svg = document.getElementById("{svg_id}");
  if (!svg) return;
  const container = svg.parentElement;
  if (!container) return;

  const svgRect = svg.getBoundingClientRect();
  const parentRect = container.getBoundingClientRect();
  const scale = 107 / svgRect.width;
  const totalDist = scale * (parentRect.width - svgRect.width);
  const walkDist = {sign} * 0.55 * totalDist;

  // Target individual rect elements inside the #legs group
  const legRects = svg.querySelectorAll("#legs rect");
  const leg1 = legRects[0], leg2 = legRects[1], leg3 = legRects[2], leg4 = legRects[3];
  const group = svg.querySelector("g") || svg;

  legRects.forEach(leg => {{
    if (leg) {{
      const b = leg.getBBox ? leg.getBBox() : {{ x: 0, y: 0, width: 11, height: 26 }};
      gsap.set(leg, {{ svgOrigin: (b.x + b.width/2) + " " + (b.y + b.height) }});
    }}
  }});

  const tl = gsap.timeline({{ repeat: -1 }});
  tl.addLabel("walk")
    .to(group, {{ x: walkDist, duration: {2.2/speed}, ease: "linear" }}, "walk");

  // Alternating leg squash cycle
  const pairs = [[leg1, leg3], [leg2, leg4]];
  const steps = Math.floor({2.2/speed} / {step_d2});
  for (let i = 0; i < steps; i++) {{
    const pair = pairs[i % 2];
    const t1 = (i * {step_d2}).toFixed(3);
    const t2 = (i * {step_d2} + {step_d}).toFixed(3);
    if (pair[0]) {{
      tl.to(pair, {{ scaleY: 0.45, duration: {step_d}, ease: "power2.out" }}, "walk+=" + t1)
        .to(pair, {{ scaleY: 1, duration: {step_d}, ease: "power2.in" }}, "walk+=" + t2);
    }}
  }}

  // Walk back
  tl.addLabel("walkBack", "+=0.5")
    .to(group, {{ x: 0, duration: {2.2/speed}, ease: "linear" }}, "walkBack");

  for (let i = 0; i < steps; i++) {{
    const pair = pairs[i % 2];
    const t1 = (i * {step_d2}).toFixed(3);
    const t2 = (i * {step_d2} + {step_d}).toFixed(3);
    if (pair[0]) {{
      tl.to(pair, {{ scaleY: 0.45, duration: {step_d}, ease: "power2.out" }}, "walkBack+=" + t1)
        .to(pair, {{ scaleY: 1, duration: {step_d}, ease: "power2.in" }}, "walkBack+=" + t2);
    }}
  }}
}})();
"""


@preset("walk-and-bounce")
def _walk_bounce(svg_id, speed=1.0, **kw):
    # Build a single timeline that bounces then walks, sharing the same element refs
    step_d = 0.1 / speed
    step_d2 = step_d * 2
    return f"""
(function() {{
  const svg = document.getElementById("{svg_id}");
  if (!svg) return;
  const container = svg.parentElement;
  if (!container) return;
  const group = svg.querySelector("g") || svg;

  const svgRect = svg.getBoundingClientRect();
  const parentRect = container.getBoundingClientRect();
  const scale = 107 / svgRect.width;
  const totalDist = scale * (parentRect.width - svgRect.width);
  const walkDist = 0.55 * totalDist;

  const legRects = svg.querySelectorAll("#legs rect");
  const leg1 = legRects[0], leg2 = legRects[1], leg3 = legRects[2], leg4 = legRects[3];

  legRects.forEach(leg => {{
    if (leg) {{
      const b = leg.getBBox ? leg.getBBox() : {{ x: 0, y: 0, width: 11, height: 26 }};
      gsap.set(leg, {{ svgOrigin: (b.x + b.width/2) + " " + (b.y + b.height) }});
    }}
  }});

  const tl = gsap.timeline({{ repeat: -1 }});

  // Bounce
  tl.to(group, {{ y: -18, duration: {0.18/speed}, ease: "power2.out" }})
    .to(group, {{ y: 0, duration: {0.15/speed}, ease: "power3.in" }});

  // Walk forward
  tl.addLabel("walk", "+=0.3")
    .to(group, {{ x: walkDist, duration: {2.2/speed}, ease: "linear" }}, "walk");

  const pairs = [[leg1, leg3], [leg2, leg4]];
  const steps = Math.floor({2.2/speed} / {step_d2});
  for (let i = 0; i < steps; i++) {{
    const pair = pairs[i % 2];
    const t1 = (i * {step_d2}).toFixed(3);
    const t2 = (i * {step_d2} + {step_d}).toFixed(3);
    if (pair[0]) {{
      tl.to(pair, {{ scaleY: 0.45, duration: {step_d}, ease: "power2.out" }}, "walk+=" + t1)
        .to(pair, {{ scaleY: 1, duration: {step_d}, ease: "power2.in" }}, "walk+=" + t2);
    }}
  }}

  // Walk back
  tl.addLabel("walkBack", "+=0.5")
    .to(group, {{ x: 0, duration: {2.2/speed}, ease: "linear" }}, "walkBack");

  for (let i = 0; i < steps; i++) {{
    const pair = pairs[i % 2];
    const t1 = (i * {step_d2}).toFixed(3);
    const t2 = (i * {step_d2} + {step_d}).toFixed(3);
    if (pair[0]) {{
      tl.to(pair, {{ scaleY: 0.45, duration: {step_d}, ease: "power2.out" }}, "walkBack+=" + t1)
        .to(pair, {{ scaleY: 1, duration: {step_d}, ease: "power2.in" }}, "walkBack+=" + t2);
    }}
  }}
}})();
"""


# ---------------------------------------------------------------------------
# Frame Switching State Machine
# ---------------------------------------------------------------------------

def generate_frame_switcher(
    num_frames: int,
    timing: dict | None = None,
    sequence: list | None = None,
    svg_id: str = "mascot",
    speed: float = 1.0,
    default_ms: int = 85,
) -> str:
    """Generate vanilla JS for frame-by-frame sprite animation."""
    if sequence is None:
        sequence = list(range(num_frames))

    timing = timing or {}
    timing_js_entries = []
    for i, frame_idx in enumerate(sequence):
        ms = timing.get(frame_idx, default_ms)
        if i == len(sequence) - 1 and frame_idx not in timing:
            ms = 1500
        timing_js_entries.append(str(round(ms / speed)))

    seq_js = json.dumps(sequence)
    timing_js = f"[{','.join(timing_js_entries)}]"

    return f"""
(function() {{
  const svg = document.getElementById("{svg_id}");
  if (!svg) return;

  const sequence = {seq_js};
  const timing = {timing_js};
  const frames = svg.querySelectorAll(":scope > g, :scope > g > g");
  let seqIdx = 0;

  frames.forEach((f, i) => f.style.display = "none");
  if (frames[sequence[0]]) frames[sequence[0]].style.display = "inline";

  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (prefersReduced) return;

  function advance() {{
    if (frames[sequence[seqIdx]]) frames[sequence[seqIdx]].style.display = "none";
    seqIdx = (seqIdx + 1) % sequence.length;
    if (frames[sequence[seqIdx]]) frames[sequence[seqIdx]].style.display = "inline";
    setTimeout(advance, timing[seqIdx]);
  }}

  setTimeout(advance, timing[0]);
}})();
"""


# ---------------------------------------------------------------------------
# Standalone HTML Renderer (merged from template_renderer.py)
# ---------------------------------------------------------------------------

def render_standalone(
    svg_markup: str,
    animation_js: str,
    title: str = "Pixel Mascot",
    bg_color: str = "#1a1a2e",
) -> str:
    """Render SVG + animation into a self-contained HTML file with GSAP CDN."""
    tpl_path = SKILL_DIR / "templates" / "mascot-standalone.html"
    if tpl_path.exists():
        tpl = tpl_path.read_text()
    else:
        tpl = _FALLBACK_TEMPLATE

    return Template(tpl).safe_substitute(
        TITLE=title,
        BG_COLOR=bg_color,
        SVG_CONTENT=svg_markup,
        ANIMATION_JS=animation_js,
    )


_FALLBACK_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>$TITLE</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: $BG_COLOR; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
  .mascot-container { width: 80vw; max-width: 600px; display: flex; align-items: flex-end; padding: 2rem; }
  .mascot-container svg { width: 84px; height: 68px; overflow: visible; }
  @media (max-width: 768px) { .mascot-container svg { width: 58px; height: 42px; } }
  @media (prefers-reduced-motion: reduce) { .mascot-container svg * { animation: none !important; transition: none !important; } }
</style>
</head>
<body>
<div class="mascot-container">$SVG_CONTENT</div>
<script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>
<script>$ANIMATION_JS</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_gsap_timeline(preset_name: str, svg_id: str = "mascot", **kwargs) -> str:
    """Generate GSAP animation JS code for a named preset."""
    if preset_name not in PRESETS:
        raise ValueError(f"Unknown preset '{preset_name}'. Available: {list_presets()}")
    return PRESETS[preset_name](svg_id, **kwargs)


def list_presets() -> list:
    """Return list of available animation preset names."""
    return sorted(PRESETS.keys())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate GSAP animation code for SVG mascots")
    parser.add_argument("--preset", help="Animation preset name")
    parser.add_argument("--svg-id", default="mascot", help="SVG element ID")
    parser.add_argument("--speed", type=float, default=1.0, help="Speed multiplier")
    parser.add_argument("--list", action="store_true", help="List available presets")
    parser.add_argument("--svg", help="SVG file to render with (enables --render)")
    parser.add_argument("--render", action="store_true", help="Render standalone HTML instead of raw JS")
    parser.add_argument("--title", default="Pixel Mascot", help="HTML page title")
    parser.add_argument("--bg-color", default="#1a1a2e", help="Background color")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")

    args = parser.parse_args()

    if args.list:
        for name in list_presets():
            print(f"  {name}")
        return

    if not args.preset:
        parser.error("--preset required (or --list to see options)")

    js = generate_gsap_timeline(args.preset, svg_id=args.svg_id, speed=args.speed)

    if args.render or args.svg:
        if not args.svg:
            parser.error("--svg required when using --render")
        svg_markup = Path(args.svg).read_text()
        result = render_standalone(svg_markup, js, args.title, args.bg_color)
    else:
        result = js

    if args.output:
        Path(args.output).write_text(result)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
