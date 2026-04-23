# Text Animation Catalog

24 named text animation effects with portable motion contracts. Each spec defines enter/exit timing, easing, stagger, and keyframe endpoints translatable to CSS, WAAPI, Motion, Framer Motion, or GSAP.

Source: [Pixel Point animate-text](https://github.com/pixel-point/animate-text) (MIT).

## Selection Guide

| Use Case | Recommended Effect | Target |
|----------|-------------------|--------|
| Hero title first-load reveal | `soft-blur-in`, `per-character-rise` | per-character |
| Short label or badge | `micro-scale-fade`, `spring-scale-in` | whole, per-word |
| Text replacement in same slot | `fade-through`, `per-word-crossfade` | whole, per-word |
| Editorial paragraph reveal | `mask-reveal-up`, `line-by-line-slide` | per-line |
| Typewriter / terminal aesthetic | `typewriter` | per-character |
| Kinetic phrase build | `kinetic-center-build` | per-word (layout-aware) |
| State transition (tab, nav) | `shared-axis-y`, `shared-axis-z` | per-word, whole |
| Premium cinematic focus | `focus-blur-resolve` | whole |
| Airy lightweight exit | `blur-out-up` | per-word |
| Center-weighted keyword emphasis | `stagger-from-center` | per-character |

## Spec Format

Each effect defines `enter` and `exit` phases:

```
{ duration_ms, stagger_ms, easing, from: { ...keys }, to: { ...keys } }
```

**Frame keys**: `opacity`, `x_px`, `y_px`, `scale`, `rotate_deg`, `blur_px`

**Swap modes**: `crossfade` (overlap old/new), `sequential` (exit then enter), `morph`

**Stagger modes**: `normal`, `center-out`, `edges-in`, `reverse`

---

## Per-Character Emphasis

### `soft-blur-in`

Blur + upward drift. Apple keynote hero-title reveal. Best on 48px+ against solid backgrounds.

| Phase | Duration | Stagger | Easing |
|-------|----------|---------|--------|
| Enter | 900ms | 25ms | `cubic-bezier(0.22, 1, 0.36, 1)` |
| Exit | 600ms | 15ms | `cubic-bezier(0.64, 0, 0.78, 0)` |

Enter: `opacity: 0 → 1, y: 16px → 0, blur: 12px → 0`
Exit: `opacity: 1 → 0, y: 0 → -16px, blur: 0 → 12px`
Swap: crossfade, overlap 300ms. On body text (<24px), reduce blur to 6px and stagger to 15ms. On long strings (>40 chars), switch to per-word.

### `per-character-rise`

Crisp letter slide-up, zero blur. tvOS-style. Works on 40px+ headlines.

| Phase | Duration | Stagger | Easing |
|-------|----------|---------|--------|
| Enter | 700ms | 24ms | `cubic-bezier(0.2, 0.8, 0.2, 1)` |
| Exit | 420ms | 14ms | `cubic-bezier(0.7, 0, 0.84, 0)` |

Enter: `opacity: 0 → 1, y: 32px → 0`
Exit: `opacity: 1 → 0, y: 0 → -24px`
Swap: crossfade, overlap 210ms. Key distinction from soft-blur-in: zero blur keeps it sharp.

### `typewriter`

Stepped reveal with editorial typing rhythm. Good for short copy.

| Phase | Duration | Stagger | Easing |
|-------|----------|---------|--------|
| Enter | 240ms | 46ms | `steps(1, end)` |
| Exit | 260ms | 10ms | `cubic-bezier(0.7, 0, 0.84, 0)` |

Enter: `opacity: 0 → 1`
Exit: `opacity: 1 → 0, y: 0 → -4px`
Swap: crossfade, no overlap, micro-delay 85ms. Exception: exit intentionally longer than enter — the stepped enter needs a softer exit to avoid an abrupt cut.

### `bottom-up-letters`

Pronounced staircase rise, zero blur. Best for short single words at 40px+.

| Phase | Duration | Stagger | Easing |
|-------|----------|---------|--------|
| Enter | 400ms | 88ms | `cubic-bezier(0.18, 1, 0.32, 1)` |
| Exit | 280ms | 28ms | `cubic-bezier(0.7, 0, 0.84, 0)` |

Enter: `opacity: 0 → 1, y: 46px → 0`
Exit: `opacity: 1 → 0, y: 0 → -14px`
Swap: sequential (exit fully, then enter). High stagger (88ms) creates deliberate per-symbol staging.

### `top-down-letters`

Descend from above, zero blur. Mirror of bottom-up-letters.

| Phase | Duration | Stagger | Easing |
|-------|----------|---------|--------|
| Enter | 400ms | 88ms | `cubic-bezier(0.18, 1, 0.32, 1)` |
| Exit | 280ms | 28ms | `cubic-bezier(0.7, 0, 0.84, 0)` |

Enter: `opacity: 0 → 1, y: -46px → 0`
Exit: `opacity: 1 → 0, y: 0 → 14px`
Swap: sequential, micro-delay 35ms.

---

## Per-Word Phrasing

### `per-word-crossfade`

Gentle word-by-word fade with vertical drift. Calm keynote rhythm.

| Phase | Duration | Stagger | Easing |
|-------|----------|---------|--------|
| Enter | 700ms | 70ms | `cubic-bezier(0.16, 1, 0.3, 1)` |
| Exit | 500ms | 40ms | `cubic-bezier(0.7, 0, 0.84, 0)` |

Enter: `opacity: 0 → 1, y: 8px → 0`
Exit: `opacity: 1 → 0, y: 0 → -6px`
Swap: crossfade, overlap 170ms, micro-delay 70ms. Best up to 16-18 words.

### `spring-scale-in`

Words pop with soft overshoot scale, physical spring settle.

| Phase | Duration | Stagger | Easing |
|-------|----------|---------|--------|
| Enter | 360ms | 95ms | `cubic-bezier(0.34, 1.56, 0.64, 1)` |
| Exit | 200ms | 80ms | `cubic-bezier(0.7, 0, 0.84, 0)` |

Enter: `opacity: 0 → 1, scale: 0.7 → 1.0`
Exit: `opacity: 1 → 0, scale: 1.0 → 0.8`
Overshoot from y2 > 1 (1.56). Per-word is the sweet spot — per-character feels too bouncy.

### `shared-axis-y`

Hard-cut staircase timing for sharp editorial word swaps.

| Phase | Duration | Stagger | Easing |
|-------|----------|---------|--------|
| Enter | 180ms | 78ms | `steps(1, end)` |
| Exit | 140ms | 78ms | `steps(1, end)` |

Enter: `opacity: 0 → 1`
Exit: `opacity: 1 → 0`
Swap: crossfade, no overlap, micro-delay 28ms. Bold word-by-word hard cuts.

### `blur-out-up`

Clean arrival, airy blur-out exit. Exit has more character than entry.

| Phase | Duration | Stagger | Easing |
|-------|----------|---------|--------|
| Enter | 560ms | 28ms | `cubic-bezier(0.22, 1, 0.36, 1)` |
| Exit | 480ms | 24ms | `cubic-bezier(0.64, 0, 0.78, 0)` |

Enter: `opacity: 0 → 1, y: 10px → 0, blur: 6px → 0`
Exit: `opacity: 1 → 0, y: 0 → -14px, blur: 0 → 8px`
Swap: crossfade, overlap 170ms. Best on short phrases.

### `kinetic-center-build` (layout-aware)

Word appears center; each new word enters from right, pushes existing line until phrase locks centered. Requires measuring word widths and animating positions.

| Phase | Duration | Easing |
|-------|----------|--------|
| Enter | 360ms | `cubic-bezier(0.2, 0.8, 0.2, 1)` |
| Exit | 260ms | `cubic-bezier(0.4, 0, 0.2, 1)` |

Enter: `opacity: 0 → 1, y: 6px → 0, scale: 0.992 → 1, blur: 3.5px → 0`
Build params: `entry_direction: from-right, push_duration: 430ms, entry_offset: 88px, word_gap: 10px, reflow_blur: 0.8px`
Best for 3-word phrases. Each incoming word physically re-centers the line.

### `short-slide-right` (layout-aware)

Whole phrase glides left-to-right as one move; words revealed only through opacity stagger.

| Phase | Duration | Stagger | Easing |
|-------|----------|---------|--------|
| Enter | 520ms | 92ms | `cubic-bezier(0.2, 0.8, 0.2, 1)` |
| Exit | 320ms | 0 | `cubic-bezier(0.4, 0, 0.2, 1)` |

Enter: `x: -24px → 0, blur: 1.2px → 0` (opacity on phrase stays 1; individual word opacity staggers 0 → 1 over 210ms)
Swap: sequential, micro-delay 70ms. Best on 3-word headings.

### `short-slide-down` (layout-aware)

Each word drops from above into its own line, pushing stack downward. Centered 3-line composition.

| Phase | Duration | Easing |
|-------|----------|--------|
| Enter | 520ms | `cubic-bezier(0.2, 0.8, 0.2, 1)` |
| Exit | 320ms | `cubic-bezier(0.4, 0, 0.2, 1)` |

Enter: `opacity: 0 → 1, y: -24px → 0, blur: 2.4px → 0, scale: 0.992 → 1`
Build params: `push_duration: 500ms, entry_offset_y: -28px, line_gap: 12px, hold: 1100ms, between_phrases: 180ms`
Best on 3-word headings where each word lives on its own line.

---

## Per-Line Editorial

### `mask-reveal-up`

Lines reveal upward with masked feel. Best for 2-3 line headings.

| Phase | Duration | Stagger | Easing |
|-------|----------|---------|--------|
| Enter | 760ms | 90ms | `cubic-bezier(0.22, 1, 0.36, 1)` |
| Exit | 520ms | 70ms | `cubic-bezier(0.64, 0, 0.78, 0)` |

Enter: `opacity: 0 → 1, y: 30px → 0, blur: 6px → 0`
Exit: `opacity: 1 → 0, y: 0 → -22px, blur: 0 → 6px`
Swap: crossfade, overlap 210ms.

### `line-by-line-slide`

Each line enters from left, exits to right. Flowing paragraph reveal.

| Phase | Duration | Stagger | Easing |
|-------|----------|---------|--------|
| Enter | 900ms | 120ms | `cubic-bezier(0.22, 1, 0.36, 1)` |
| Exit | 600ms | 80ms | `cubic-bezier(0.64, 0, 0.78, 0)` |

Enter: `opacity: 0 → 1, x: -48px → 0`
Exit: `opacity: 1 → 0, x: 0 → 48px`
Swap: no overlap. Reduce x-distance on narrow/mobile layouts.

---

## Whole-Phrase Transitions

### `micro-scale-fade`

Tiny scale pop for labels and headings. Subtle premium polish.

| Phase | Duration | Easing |
|-------|----------|--------|
| Enter | 600ms | `cubic-bezier(0.32, 0.72, 0, 1)` |
| Exit | 400ms | `cubic-bezier(0.7, 0, 0.84, 0)` |

Enter: `opacity: 0 → 1, scale: 0.96 → 1.0`
Exit: `opacity: 1 → 0, scale: 1.0 → 0.96`
For paragraphs, switch to per-word.

### `shimmer-sweep`

Subtle left-to-center sweep with blur. Premium title swap.

| Phase | Duration | Easing |
|-------|----------|--------|
| Enter | 850ms | `cubic-bezier(0.22, 1, 0.36, 1)` |
| Exit | 650ms | `cubic-bezier(0.7, 0, 0.84, 0)` |

Enter: `opacity: 0 → 1, x: -22px → 0, blur: 8px → 0`
Exit: `opacity: 1 → 0, x: 0 → 22px, blur: 0 → 8px`

### `fade-through`

Material-style content transition. Old fades out, new fades in with delay.

| Phase | Duration | Easing |
|-------|----------|--------|
| Enter | 420ms | `cubic-bezier(0.2, 0, 0, 1)` |
| Exit | 260ms | `cubic-bezier(0.4, 0, 1, 1)` |

Enter: `opacity: 0 → 1, y: 6px → 0, scale: 0.99 → 1, blur: 2px → 0`
Exit: `opacity: 1 → 0, y: 0 → -4px`
Swap: crossfade, overlap 20ms, micro-delay 60ms. Best for same-slot replacement without directional meaning.

### `shared-axis-z`

Scale-based focus shift for depth transitions.

| Phase | Duration | Easing |
|-------|----------|--------|
| Enter | 520ms | `cubic-bezier(0.2, 0, 0, 1)` |
| Exit | 360ms | `cubic-bezier(0.4, 0, 1, 1)` |

Enter: `opacity: 0 → 1, scale: 0.9 → 1, blur: 2px → 0`
Exit: `opacity: 1 → 0, scale: 1 → 1.06, blur: 0 → 1px`
Swap: crossfade, overlap 100ms.

### `scale-down-fade`

Restrained premium settle-in. Safe default for polished product UI.

| Phase | Duration | Easing |
|-------|----------|--------|
| Enter | 520ms | `cubic-bezier(0.22, 1, 0.36, 1)` |
| Exit | 380ms | `cubic-bezier(0.64, 0, 0.78, 0)` |

Enter: `opacity: 0 → 1, y: 8px → 0, scale: 1.04 → 1`
Exit: `opacity: 1 → 0, y: 0 → -8px, scale: 1 → 0.94`

### `focus-blur-resolve`

Premium focus pull from heavy blur to crisp text. Cinematic restraint.

| Phase | Duration | Easing |
|-------|----------|--------|
| Enter | 760ms | `cubic-bezier(0.22, 1, 0.36, 1)` |
| Exit | 520ms | `cubic-bezier(0.64, 0, 0.78, 0)` |

Enter: `opacity: 0 → 1, y: 14px → 0, blur: 14px → 0, scale: 1.01 → 1`
Exit: `opacity: 1 → 0, y: 0 → -10px, blur: 0 → 10px`
Best on large headlines where blur distance reads as intentional.

---

## Extended Effects (not in showcase)

### `depth-parallax-words`

Per-word depth motion with scale and vertical drift. Target: per-word.
Enter 700ms/70ms stagger: `opacity: 0 → 1, y: 18px → 0, scale: 0.92 → 1, blur: 3px → 0`
Exit 500ms/45ms stagger: `opacity: 1 → 0, y: 0 → -10px, scale: 1 → 1.05, blur: 0 → 2px`
Easing: `cubic-bezier(0.22, 1, 0.36, 1)` / `cubic-bezier(0.64, 0, 0.78, 0)`

### `shared-axis-x`

Horizontal shared-axis transition for sibling navigation. Target: whole.
Enter 500ms: `opacity: 0 → 1, x: 24px → 0, scale: 0.98 → 1`
Exit 360ms: `opacity: 1 → 0, x: 0 → -20px, scale: 1 → 0.98`
Easing: `cubic-bezier(0.2, 0, 0, 1)` / `cubic-bezier(0.4, 0, 1, 1)`

### `stagger-from-center`

Characters reveal center-outward to emphasize keyword core. Target: per-character. Stagger mode: `center-out`.
Enter 620ms/22ms stagger: `opacity: 0 → 1, y: 12px → 0, blur: 3px → 0`
Exit 420ms/16ms stagger: `opacity: 1 → 0, y: 0 → -8px, blur: 0 → 3px`
Easing: `cubic-bezier(0.22, 1, 0.36, 1)` / `cubic-bezier(0.64, 0, 0.78, 0)`

### `stagger-from-edges`

Characters converge from both edges toward center. Target: per-character. Stagger mode: `edges-in`.
Enter 620ms/22ms stagger: `opacity: 0 → 1, y: 12px → 0, blur: 3px → 0`
Exit 420ms/16ms stagger: `opacity: 1 → 0, y: 0 → -8px, blur: 0 → 3px`
Easing: `cubic-bezier(0.22, 1, 0.36, 1)` / `cubic-bezier(0.64, 0, 0.78, 0)`

---

## Stack Translation

**CSS-only**: Generate `@keyframes` with `animation-delay: calc(var(--i) * <stagger_ms>ms)`. Set `--i` per element via `style`. Animate only `transform`, `opacity`, and `filter: blur()`. Avoid flattening layout-aware effects into pure CSS.

**WAAPI**: Build explicit keyframe arrays. Apply per-unit `delay` via `animation.startTime` offset or `AnimationEffect.delay`.

**Motion / Framer Motion**: Map `duration_ms` → `transition.duration` (seconds), `easing` → `transition.ease` (array form), `stagger_ms` → `transition.staggerChildren`. Use `variants` for enter/exit states.

**GSAP**: Map `from`/`to` to `gsap.fromTo()` or timeline `.to()` segments. Use `stagger` property directly. Layout-aware effects need timeline sequencing with `position` parameters.

### Translation Rules

- Preserve `target` splitting exactly: `whole`, `per-character`, `per-word`, `per-line`.
- Map `enter`/`exit` duration, easing, and stagger directly.
- Preserve all frame keys the target stack supports.
- For layout-aware effects (`kinetic-center-build`, `short-slide-right`, `short-slide-down`), use the `build` block to preserve choreography — do not flatten to generic stagger.
- Exit animations are typically 55-85% of enter duration, clustering around 65-75%. Faster exits feel natural; equal-or-longer exits feel sluggish (exception: `typewriter`).
