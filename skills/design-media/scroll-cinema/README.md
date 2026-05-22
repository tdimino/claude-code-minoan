# Scroll Cinema

Cinematic scrolltelling websites where scroll drives the narrative. Three libraries coordinate as a unified system: **Lenis** provides buttery smooth locomotion, **GSAP ScrollTrigger** orchestrates cinematic section reveals with fluid OKLCH color transitions, and **Three.js** renders a living painted-texture background reactive to cursor, scroll velocity, and chapter progress.

## Modes

| Mode | Output | Libraries |
|------|--------|-----------|
| `chapter-reveal` | Multi-section storytelling with cinematic entrances and OKLCH color transitions | Lenis + GSAP ScrollTrigger |
| `painted-backdrop` | Three.js shader canvas reactive to cursor + scroll, standalone or embeddable | Three.js + GLSL + scroll-fed uniforms |
| `full-cinema` | Complete cinematic scrolltelling site — all systems integrated | Lenis + GSAP + Three.js |
| `catalog` | All three shader presets side by side with one WebGL context (scissor test) | Lenis + GSAP + Three.js |

## Quick Start

```bash
# Full cinematic storytelling site
python3 ~/.claude/skills/scroll-cinema/scripts/scroll_cinema_generator.py \
  --mode full-cinema --shader painted-dots --entrance fade-up \
  --chapters 5 --pacing medium -o story.html

# Chapter reveals with split-text entrance
python3 ~/.claude/skills/scroll-cinema/scripts/scroll_cinema_generator.py \
  --mode chapter-reveal --entrance split-text --chapters 4 -o chapters.html

# Standalone reactive shader background
python3 ~/.claude/skills/scroll-cinema/scripts/scroll_cinema_generator.py \
  --mode painted-backdrop --shader watercolor -o backdrop.html

# All shader presets side by side
python3 ~/.claude/skills/scroll-cinema/scripts/scroll_cinema_generator.py \
  --mode catalog -o catalog.html
```

Or invoke via Claude: `/scroll-cinema a story about the Mediterranean told in five chapters`

## Shader Presets

| Preset | Technique | Performance | Feel |
|--------|-----------|-------------|------|
| `painted-dots` | Dot-grid with mouse-reactive ripple, scroll-driven density | Lightest | Subtle, editorial |
| `watercolor` | Kuwahara-style edge-preserving filter + simplex noise, dFdx/dFdy edge detection | Medium | Organic, painterly |
| `domain-warp` | Progressive sinusoidal domain warping | Lightest | Flowing, abstract |

All shaders receive lerped uniforms: `uTime`, `uMouse` (0.08), `uScroll` (0.05), `uVelocity` (0.10), `uChapter` (0.03), `uMobile`, `uResolution`, `uChapterHue` (0.03), `uChapterLightness` (0.03).

## Entrance Patterns

| Pattern | Easing | Effect | Mobile Fallback |
|---------|--------|--------|-----------------|
| `fade-up` (default) | `cinematicSilk` | Title + body slide up with staggered delay | Same |
| `split-text` | `cinematicFlow` | Per-word stagger on titles, fade-up on body | Falls back to fade-up |
| `clip-path-wipe` | `cinematicFlow` | Cinematic curtain reveal via `inset()` clip-path | Falls back to simple fade |
| `scale-reveal` | `cinematicSmooth` | Content scales from 0.85 with opacity fade | Same |

## Parameters

| Parameter | Range | Default |
|-----------|-------|---------|
| `--mode` | `chapter-reveal\|painted-backdrop\|full-cinema\|catalog` | `full-cinema` |
| `--shader` | `painted-dots\|watercolor\|domain-warp` | `painted-dots` |
| `--entrance` | `fade-up\|split-text\|scale-reveal\|clip-path-wipe` | `fade-up` |
| `--chapters` | `2–8` | `5` |
| `--pacing` | `slow\|medium\|fast` | `medium` |
| `--color-scheme` | `dark\|light` | `dark` |
| `--font` | font name | `Geist` |
| `--accent` | hex color | — |
| `--output` | path | `output.html` |

## Architecture

Single animation loop — GSAP ticker drives Lenis, ScrollTrigger, and Three.js render. No separate `requestAnimationFrame`. Lenis must use `autoRaf: false` with `gsap.ticker.add((time) => lenis.raf(time * 1000))`.

OKLCH color interpolation between chapters via `@property`-registered CSS custom properties with HSL fallback. `shaderState` JS bridge feeds chapter colors to Three.js uniforms without per-frame `getComputedStyle`.

## Validation

```bash
python3 ~/.claude/skills/scroll-cinema/scripts/validate_scroll_cinema.py output.html
```

27 checks covering CDN imports, Lenis+GSAP integration, accessibility, performance anti-patterns, SRI integrity, entrance patterns, design tokens, and cleanup.

## Structure

```
scroll-cinema/
├── SKILL.md                          # Full skill reference (256 lines)
├── scripts/
│   ├── scroll_cinema_generator.py    # HTML generator (all modes)
│   └── validate_scroll_cinema.py     # Output validator (27 checks)
├── references/
│   ├── lenis-gsap-integration.md     # Init sequence, cleanup, SPA lifecycle
│   ├── cinematic-easings.md          # 4 custom easing curves
│   ├── painted-shader-patterns.md    # GLSL code, uniform pipeline, lerp rates
│   ├── color-interpolation.md        # OKLCH system, @property, fallbacks
│   ├── chapter-structure.md          # Sticky sections, scroll pacing, entrance patterns
│   ├── design-tokens.md              # CSS custom properties, typography, responsive
│   └── anti-patterns.md              # 13 gotchas with wrong/right code
└── assets/
    └── templates/
```

## Cross-Skill Relationships

- **`threejs-particle-canvas`**: scroll-cinema = background canvas; particle-canvas = the experience itself
- **`conductor-motion`**: conductor-motion = behavioral simulations within sections; scroll-cinema = cinematic section choreography
- **`rocaille-shader`**: rocaille-shader's domain warping serves as the `domain-warp` preset upstream
- **`grainient`**: grainient = 2D CSS surface effects; scroll-cinema = 3D+scroll orchestration layer
- **`shape` / `design-md`**: Upstream — `.design-context.md` feeds palette and typography into scroll-cinema

## CDN Versions

Lenis 1.2.3, GSAP 3.12.7 (+ ScrollTrigger + CustomEase), Three.js r170. All with SRI integrity hashes.
