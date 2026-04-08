# Astryx Hero Pattern

Depth-map parallax displacement hero technique: a static image (bust, statue, product) appears to shift in 3D space as the cursor moves, creating a hover-reactive editorial hero without real 3D geometry. Source: https://indigo-type-231733.framer.app/astryx (Framer + Unicorn Studio v2.1.6).

This reference documents the pattern anatomy for reproduction via `rocaille-shader --mode astryx-statue` (Scope B). The CLI flag uses `astryx-statue` (the effect subject) while filenames use `astryx-hero` (the layout placement)—both refer to the same pattern. For the shader math, see `~/.claude/skills/rocaille-shader/references/liquid-logo.md` (shared Gaussian falloff + chromatic aberration primitives).

---

## Layer Stack

| Layer | Content | Implementation |
|-------|---------|----------------|
| Background | Pure black `rgb(0,0,0)` | CSS |
| WebGL canvas (back) | Ambient background particles/gradient | Secondary `<canvas>` at 1920x1080 |
| WebGL canvas (front) | Statue + depth-displacement shader | Unicorn Studio scene, ~679x1080, center-right |
| Typography overlay | Editorial type stack (Instrument Sans) | HTML/CSS over canvas |
| Motion chrome | Fade-up on load (opacity + translateY) | Framer `appear-id` or CSS `@keyframes` / `motion` library |

## Typography

- **Font**: Instrument Sans 500 (Google Fonts, SIL OFL 1.1, commercial-safe)
- **H1**: 36px desktop / 29px mobile
- **Letter-spacing**: -0.03em
- **Line-height**: 1.1em
- **OpenType features**: `blwf`, `cv03`, `cv04`, `cv09`, `cv11` (stylistic alternates)
- **Color**: pure white `rgb(255,255,255)` on black

## Palette

| Role | Value |
|------|-------|
| Background | `rgb(0,0,0)` pure black |
| Text | `rgb(255,255,255)` |
| Accent | `rgb(0,192,71)` green (pulse indicator) |
| CTA | `rgb(247,247,247)` off-white on dark, 16px stacked box-shadow (5 cascaded offsets) |

## Depth-Parallax Shader (the core technique)

The canonical single-tap inverse displacement, descended from Robin Delaporte's CodePen (https://codepen.io/robin-dela/pen/vaQQNL):

```glsl
vec4 depthSample  = texture2D(u_depthMap, v_texcoord);
float parallaxMul = depthSample.r;                       // white=near in astryx-depth-1.0
vec2 parallax     = u_mouse * parallaxMul * u_strength;   // u_strength ~0.05
vec4 color        = texture2D(u_colorImage, v_texcoord + parallax);
```

**Critical: depth polarity is not universal.** The shader must expose a `uDepthInvert` uniform (default false = white-near, matching DepthFlow/ControlNet convention). MiDaS-style inverse-depth maps need `--invert`. Hardcoding either breaks ~50% of inputs.

**Pointer smoothing**: `mouse += (target - mouse) * 0.05` per frame prevents snap. The Lissajous idle breathing from liquid-logo mode applies here too.

## DPR Strategy

Clamp device pixel ratio to **1.5** (matching Astryx's own `data-us-dpi="1.5"`). The quality difference above 1.5 is imperceptible at these effect frequencies, and 2.0 DPR costs 1.78x more fragments.

## Accessibility

- `prefers-reduced-motion`: static `<img>` fallback, zero GPU, zero RAF callbacks
- `(hover: none)` / viewport < 640px: static fallback (no pointer parallax on touch)
- `touch-action: pan-y` on the hero container to preserve native scroll on touch devices
- `visibilitychange`: pause RAF when tab is hidden (already in liquid-logo baseline)

## Performance Budget

| Target | Metric | Budget |
|--------|--------|--------|
| Desktop (M4 Max) | Frame time | < 4ms (250fps headroom) |
| Desktop (M4 Max) | GPU memory delta | < 15MB |
| Mobile (iPhone 13+) | Frame time | < 8ms or static fallback |
| `prefers-reduced-motion` | CPU | 0 (no RAF, no shader) |

## License Posture

- **Unicorn Studio runtime**: `"license": null` on GitHub (verified 2026-04-06 via `gh api`). jsDelivr tags are NOT immutable. Any embed recipe MUST pin by commit SHA + SRI hash + `crossorigin="anonymous"` + `referrerpolicy="no-referrer"`. **This is a human-only reference path** — agents and commercial work use the native `rocaille-shader` reproduction.
- **Robin Delaporte CodePen**: the pattern ancestor — we describe the technique, not redistribute code.
- **DepthFlow** (BrokenSource): AGPL — reference only, not a dependency.
- **Instrument Sans**: SIL OFL 1.1 via Google Fonts CDN — commercial-safe.

## Sibling Patterns

| Pattern | Technique | Skill | Reference |
|---------|-----------|-------|-----------|
| **Fluid-DOM** | Navier-Stokes stable fluid over live DOM | `rocaille-shader --mode fluid-dom` | `~/.claude/skills/rocaille-shader/references/fluid-dom.md` |
| **Liquid Logo** | Chromatic aberration + Gaussian falloff on texture | `rocaille-shader --mode liquid-logo` | `~/.claude/skills/rocaille-shader/references/liquid-logo.md` |

Choose Astryx when: the hero needs a 3D-look depth effect on a single subject (bust, product, statue).
Choose Fluid-DOM when: the effect should wrap multiple live DOM elements with flowing, persistent velocity.
Choose Liquid Logo when: a logo or hero image needs a pointer-reactive ripple/refraction without depth.

## External References

- Robin Delaporte CodePen (universal ancestor): https://codepen.io/robin-dela/pen/vaQQNL
- bozzin gist (full source): https://gist.github.com/bozzin/5895d97130e148e66b88ff4c92535b59
- DepthFlow (production reference, AGPL): https://github.com/BrokenSource/DepthFlow
- Depth-seam contract (`astryx-depth-1.0`): see plan `~/.claude/plans/2026-04-06-001-feat-astryx-pattern-skill-integration-plan.md` § Depth-Seam Contract
