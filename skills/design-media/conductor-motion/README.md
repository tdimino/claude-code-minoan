# conductor-motion

Behavioral animation patterns that simulate live software—typewriter/rotator effects, progress bar simulations, file review state machines, staggered reveals, terminal status displays, streaming AI text, top-layer chrome (popover/dialog/toast), Lottie orchestration, and scroll-driven sequences. Single-file HTML output, vanilla JS, zero frameworks.

Distilled from [ConductorAI.com](https://www.conductorai.com/) (Webflow, GSAP 3.15, Lottie, vanilla JS).

## Quick Start

```bash
# Typewriter hero with word cycling
python3 scripts/conductor_motion_generator.py --mode typewriter \
  --base-text "Accelerating" \
  --words "complex approvals,investigations,e-discovery,FOIA review" \
  --output typewriter.html

# Progress bar simulation
python3 scripts/conductor_motion_generator.py --mode progress \
  --title "search initialization" --doc-count 1324 \
  --output progress.html

# File review state machine
python3 scripts/conductor_motion_generator.py --mode file-review \
  --files "Report_Q4.xlsx,Contract_Draft.pdf,Audit_Log.csv" \
  --output file-review.html

# Full landing page with all patterns
python3 scripts/conductor_motion_generator.py --mode full-page \
  --output landing.html

# Effects catalog
python3 scripts/conductor_motion_generator.py --mode catalog \
  --output catalog.html
```

## Modes

| Mode | Output |
|------|--------|
| `typewriter` | Hero rotator + type-on + blinking cursor |
| `progress` | Progress bar + counter + dot-leaders + processing dots + staggered rows |
| `file-review` | File list + state machine (unreviewed→processing→reviewed) + status indicators |
| `stagger-reveal` | Hero cascade + section reveals + IntersectionObserver scroll triggers |
| `terminal` | Timestamps + status typing + search result counters + progress sync |
| `streaming-text` | Chat panel + chunk-buffered token streaming + pinned scroll + stop/regenerate |
| `top-layer` | Popover/dialog/toast entry+exit via `@starting-style` + `allow-discrete` |
| `lottie-compose` | Lottie player + responsive variants + scroll-synced playback |
| `full-page` | Composed landing section (typewriter, progress, stagger, rotator) |
| `catalog` | Visual reference with live demos of six core patterns |

## Validation

```bash
python3 scripts/validate_conductor_motion.py output.html
```

21 checks: viewport meta, `--cm-*` tokens, no framework imports, `requestAnimationFrame`, `prefers-reduced-motion`, `performance.now()`, font-smoothing, `aria-hidden` on cursors, visibility API, no `transition: all`, no width/left animation (scaleX/translate only), `aria-valuenow` synced to visible progress, paused flags actually consulted, no-JS static fallback.

```bash
python3 scripts/test_generator.py
```

Smoke test: every mode generates, every documented flag changes the output bytes.

## Structure

```
conductor-motion/
├── SKILL.md                          # Full instructions + implementation rules
├── evals/evals.json                  # 5 skill evals
├── scripts/
│   ├── conductor_motion_generator.py # Generator (10 modes, all params)
│   ├── validate_conductor_motion.py  # Validator (21 checks)
│   └── test_generator.py             # Flag-effectiveness smoke test
├── assets/templates/                 # 10 HTML templates (one per mode)
└── references/                       # 12 pattern references
    ├── design-tokens.md              # --cm-* token system, easing, timing
    ├── typewriter-patterns.md
    ├── progress-simulation-patterns.md
    ├── stagger-reveal-patterns.md
    ├── file-review-patterns.md
    ├── terminal-display-patterns.md
    ├── streaming-text-patterns.md    # Chunk buffering, scroll pinning, aria-live
    ├── top-layer-patterns.md         # @starting-style, allow-discrete, overlay
    ├── lottie-orchestration.md
    ├── scroll-driven-animations.md
    ├── anti-patterns.md
    └── advanced-compositions.md      # Workflow graphs, multi-agent review, comparison bars
```

## Design Principles

- **Vanilla only.** No React, Vue, or jQuery. Plain HTML + CSS + JS.
- **Single-file output.** Everything in one HTML file. CDN imports for fonts only.
- **`--cm-*` tokens everywhere.** Never hardcode colors or timing.
- **`prefers-reduced-motion` required.** Every effect shows final state under reduced motion.
- **Visibility API integration.** Pause animation loops when tab is hidden.
- **Accessible by default.** `aria-hidden` on decorative elements, `role="progressbar"` with `aria-valuenow`.

## Cross-Skill Boundaries

- **grainient** owns CSS surface effects (shadows, aurora, glass). **conductor-motion** owns behavioral animations (typing, progress, state machines). If it simulates software behavior, it's conductor-motion.
- **minoan-frontend-design** provides creative direction; conductor-motion implements the motion layer.
- Output must pass **design-audit** (a11y, contrast) and **design-polish** (150–300ms transitions, ease-out-quart).
