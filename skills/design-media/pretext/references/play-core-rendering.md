# play.core Character Grid Rendering Model

## Overview

[play.core](https://github.com/ertdfgcvb/play.core) (Apache 2.0) is a browser framework where every monospaced character cell is a pixel. You write a `main()` function that runs once per cell per frame—exactly like a GLSL fragment shader, but the output is a character with optional color. Pure CPU JavaScript, no GPU.

Use this model instead of the existing typographic-ascii approach when the effect requires **per-frame simulation** (fire, plasma, 3D wireframes, particle systems, interactive pointer effects). For static or layout-driven effects (calligrams, obstacle routing, editorial), the existing pretext approach is better.

## Fragment Shader Model

The core concept: `main(coord, context, cursor, buffer)` is called once per character cell per frame.

```js
// coord: {x, y, index} — integer grid position, 0-based from top-left
// Return: character string OR {char, color, backgroundColor} cell object
export function main(coord, context, cursor, buffer) {
  const v = someComputation(coord, context)
  const idx = Math.floor(map(v, 0, 1, 0, density.length))
  return density[idx]
}
```

Returning a falsy value produces a space. Partial cell objects are merged (spread) into the existing buffer cell.

## Program Lifecycle

All hooks are optional. At least one must exist.

| Hook | Called | Use For |
|------|--------|---------|
| `boot(context, buffer, userData)` | Once, pre-first-frame | Simulation init, palette building, one-time setup |
| `pre(context, cursor, buffer, userData)` | Once per frame, before cells | Per-frame values (projection matrices, time constants), buffer clearing |
| `main(coord, context, cursor, buffer, userData)` | Once per cell per frame | Character + color computation |
| `post(context, cursor, buffer, userData)` | Once per frame, after cells | HUD overlays, debug info, UI boxes |
| `pointerMove/Down/Up(context, cursor, buffer)` | On pointer events | Interactive effects |

**Separation of concerns**: Compute expensive shared state in `pre()` (3D projections, physics), evaluate per-cell in `main()`, overlay UI in `post()`.

## Density Strings

The fundamental mapping from float values to characters by visual weight:

```js
// Heavy → light (play.core convention)
const density = 'Ñ@#W$9876543210?!abc;:+=-,._ '

// Usage: map a float to a character
const idx = Math.floor(map(v, minVal, maxVal, 0, 1) * density.length)
return density[Math.min(idx, density.length - 1)]
```

Common density strings:
- Standard (30): `'Ñ@#W$9876543210?!abc;:+=-,._ '`
- Dense (70): `'$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,"^. '`
- Blocks (5): `'█▓▒░ '`

**With pretext**: Replace density-string indexing with the proportional palette lookup from `typographic-ascii.md`. Pretext's dual-scoring (brightness × 2.5 + width match) produces better results than monospace density strings because characters match both visual density AND spatial width.

## Aspect Ratio Correction

Character cells are taller than wide (~2:1). Without correction, circles appear as vertical ellipses.

```js
// Measure from live DOM (play.core's calcMetrics approach)
// For monospace: cellWidth / lineHeight ≈ 0.47–0.55
const aspect = cellWidth / lineHeight

// For pretext proportional fonts: use average palette width
const avgCharW = palette.reduce((s, p) => s + p.width, 0) / palette.length
const aspect = avgCharW / LINE_HEIGHT
```

**All geometry must compensate**: multiply X coordinates by `aspect`.

## Normalized Coordinates

Map grid positions to `[-1, 1]` with correct proportions (equivalent to Shadertoy's UV):

```js
const m = Math.min(cols * aspect, rows)
const st = {
  x: 2.0 * (coord.x - cols / 2) / m * aspect,
  y: 2.0 * (coord.y - rows / 2) / m
}
// st is now in [-1, 1], aspect-corrected
```

## SDF Primitives

Signed distance functions from play.core's `sdf.js` (port of Inigo Quilez). Negative = inside shape, positive = outside, zero = boundary.

```js
// Circle
function sdCircle(p, r) {
  return Math.sqrt(p.x * p.x + p.y * p.y) - r
}

// Axis-aligned box
function sdBox(p, b) {
  const dx = Math.abs(p.x) - b.x
  const dy = Math.abs(p.y) - b.y
  return Math.sqrt(Math.max(dx, 0) ** 2 + Math.max(dy, 0) ** 2) +
         Math.min(Math.max(dx, dy), 0)
}

// Thick line segment
function sdSegment(p, a, b, th) {
  const pa = { x: p.x - a.x, y: p.y - a.y }
  const ba = { x: b.x - a.x, y: b.y - a.y }
  const h = Math.max(0, Math.min(1, (pa.x * ba.x + pa.y * ba.y) /
            (ba.x * ba.x + ba.y * ba.y)))
  const dx = pa.x - ba.x * h, dy = pa.y - ba.y * h
  return Math.sqrt(dx * dx + dy * dy) - th
}

// Smooth boolean operations
function opSmoothUnion(d1, d2, k) {
  const h = Math.max(0, Math.min(1, 0.5 + 0.5 * (d2 - d1) / k))
  return d2 * (1 - h) + d1 * h - k * h * (1 - h)
}
```

**Glow pattern**: `brightness = Math.exp(-k * Math.abs(dist))` — exponential falloff from shape boundary. Higher `k` = tighter glow.

## Color Pipeline

Per-cell RGB via phase-offset sines (play.core convention):

```js
function css(r, g, b) {
  return `rgb(${Math.floor(r)},${Math.floor(g)},${Math.floor(b)})`
}

// Phase-offset rainbow from a float value v and time t
const r = map(Math.sin(v * Math.PI + t), -1, 1, 0, 255)
const g = map(Math.sin(v * Math.PI * 2/3 + t), -1, 1, 0, 255)
const b = map(Math.sin(v * Math.PI * 4/3 - t), -1, 1, 0, 255)

return { char: density[idx], color: '#fff', backgroundColor: css(r, g, b) }
```

Each cell carries independent `color` and `backgroundColor`—full per-cell color is first-class.

**Palette color schemes** (from play.core's `color.js`): CSS4, CSS3, CSS1 named colors, C64 palette (16), CGA palette (16). Each entry: `{name, r, g, b, hex, css}`.

## Buffer Persistence

Flat 1D array, length = `cols × rows`, indexed by `x + y * cols`. Persists across frames (reset only on resize). Enables stateful simulations:

```js
// Cellular automaton fire (doom_flame pattern)
function pre(context, cursor, buffer) {
  // Propagate heat upward with decay
  for (let y = 0; y < context.rows - 1; y++) {
    for (let x = 0; x < context.cols; x++) {
      const below = buffer[x + (y + 1) * context.cols]
      const jitter = (Math.random() - 0.5) * 0.1
      buffer[x + y * context.cols].heat = (below.heat || 0) * 0.85 + jitter
    }
  }
  // Inject heat at bottom
  for (let x = 0; x < context.cols; x++) {
    buffer[x + (context.rows - 1) * context.cols].heat = Math.random()
  }
}
```

## Context Object

Rebuilt each frame, frozen:

```js
{
  frame,    // int — frame counter
  time,     // ms — DOMHighResTimeStamp
  cols,     // int — grid columns
  rows,     // int — grid rows
  metrics,  // {cellWidth, lineHeight, aspect}
  width,    // px — element width
  height,   // px — element height
}
```

## Cursor Object

```js
{
  x, y,     // float — pointer position in cell-space
  pressed,  // boolean
  p: { x, y, pressed }  // previous frame values
}
```

## Utility Functions

```js
function map(v, a, b, c, d) { return c + (d - c) * (v - a) / (b - a) }
function clamp(v, min, max) { return Math.max(min, Math.min(max, v)) }
function fract(v) { return v - Math.floor(v) }
function mix(a, b, t) { return a + (b - a) * t }
function length(v) { return Math.sqrt(v.x * v.x + v.y * v.y) }
function sub(a, b) { return { x: a.x - b.x, y: a.y - b.y } }
function norm(v) { const l = length(v); return { x: v.x / l, y: v.y / l } }
```

## Bridging play.core to Pretext

The key integration: pretext's `prepareWithSegments()` builds a proportional brightness palette (per `typographic-ascii.md`), then the play.core `main()` loop drives the per-cell render cycle.

1. **`boot()`**: Build proportional palette via pretext (existing approach from `typographic-ascii.md`)
2. **`pre()`**: Update simulation state (physics, fluid advection, SDF parameters)
3. **`main()`**: For each cell—compute visual value from simulation, look up palette character via dual-scoring, compute per-cell color
4. **`post()`**: Overlay HUD (fps, grid dims) via `drawBox` or direct buffer writes

**When to use this model**:
- Animated effects with per-frame simulation: fire, plasma, 3D wireframes, particles
- Interactive pointer effects: cursor glow, repulsion fields, click bursts
- Cellular automata: Conway's Life, fire, electricity, dissolve

**When to use existing pretext model**:
- Static or layout-driven effects: calligrams, obstacle routing, editorial
- Effects driven by text content rather than simulation
- Single-frame renders (no animation loop)

## Inline vs Import

play.core has no npm package. For single-file HTML (pretext convention):

- **Inline the specific functions needed** (~50-100 lines for SDF + vec2 + num + color helpers)
- **CDN fallback**: `https://cdn.jsdelivr.net/gh/ertdfgcvb/play.core@master/src/modules/sdf.js` (works but pinned to `master`—fragile)
- **Recommended**: Copy the 6-8 functions you need directly into the `<script>` block. The modules are pure functions with no dependencies.

## html-in-canvas (Future Watch)

The [WICG html-in-canvas proposal](https://github.com/WICG/html-in-canvas) would enable pretext-laid-out text as WebGL textures on 3D surfaces. Chrome Canary prototype behind `#canvas-draw-element` flag. Mozilla formally opposed. WebKit reviewing.

**What it would unlock**: Pretext typographic effects mapped onto curved 3D geometry (illuminated manuscripts on scrolls, editorial typography on architectural surfaces). Reference implementation: [jakearchibald/curved-markup](https://github.com/jakearchibald/random-stuff/tree/main/apps/curved-markup).

**When to act**: When Chrome ships to stable, or when a polyfill with acceptable quality emerges.
