# Character Grid Background

A `<pre>` element positioned behind content, running a character grid animation as atmospheric texture. Each character cell is a "pixel"—a `main(x, y, time)` function returns a character + color per cell per frame, like a GLSL fragment shader for text.

## Integration Pattern

Layer behind glassmorphism panels, bento grids, or split-screen layouts:

```html
<div class="page">
  <pre id="grid-bg" aria-hidden="true"></pre>
  <main class="content"><!-- UI here --></main>
</div>
```

```css
.page { position: relative; min-height: 100vh; }
#grid-bg {
  position: absolute; inset: 0; z-index: 0;
  pointer-events: none; user-select: none;
  font: 14px/17px 'Courier New', monospace;
  overflow: hidden; margin: 0;
}
.content { position: relative; z-index: 1; }
```

## Aesthetic Directions

### 1. CRT Terminal

Green-on-black density oscillation with random character flicker.

```js
const BG = '#0a0a0a', FG = 'rgba(0,255,65,'
const chars = ' .,:;!+-=*#@%&'

function main(x, y, t) {
  const v = Math.sin(x * 0.1 + t * 0.5) * Math.sin(y * 0.15 - t * 0.3)
  const brightness = (v + 1) * 0.5
  const flicker = Math.random() < 0.05 ? chars[Math.floor(Math.random() * chars.length)] : null
  const idx = Math.floor(brightness * (chars.length - 1))
  return { char: flicker || chars[idx], color: FG + brightness.toFixed(2) + ')' }
}
```

Add scanline overlay via CSS:
```css
#grid-bg::after {
  content: ''; position: absolute; inset: 0; pointer-events: none;
  background: repeating-linear-gradient(
    transparent, transparent 16px, rgba(0,0,0,0.15) 17px
  );
}
```

### 2. Plasma

Phase-offset sine RGB per cell. Four layered interference patterns:

```js
function main(x, y, t, cols, rows) {
  const sx = x / cols * 6, sy = y / rows * 6
  let v = Math.sin(sx * 3 + t * 1.2)
       + Math.sin(sy * 4 - t * 0.8)
       + Math.sin((sx + sy) * 2.5 + t * 0.6)
       + Math.sin(Math.sqrt(sx*sx*4 + sy*sy*4) * 3 - t * 1.5)
  v = (v + 4) / 8  // normalize 0-1

  const r = Math.floor(Math.sin(v * Math.PI) * 127 + 128)
  const g = Math.floor(Math.sin(v * Math.PI * 2/3) * 127 + 128)
  const b = Math.floor(Math.sin(v * Math.PI * 4/3) * 127 + 128)
  const blocks = '█▓▒░ '
  return { char: blocks[Math.floor((1-v) * 4)], bg: `rgb(${r},${g},${b})` }
}
```

### 3. Matrix Rain

Column-based character cascade with brightness trail:

```js
const KATAKANA = 'アイウエオカキクケコサシスセソタチツテト'
const TRAIL = 12

// State: per-column head position and speed
const columns = Array.from({length: cols}, () => ({
  y: Math.random() * rows, speed: 0.3 + Math.random() * 0.7
}))

function main(x, y, t) {
  const col = columns[x]
  const head = col.y
  const dist = (head - y + rows) % rows
  if (dist > TRAIL) return { char: ' ' }

  const brightness = 1 - dist / TRAIL
  const char = dist === 0
    ? KATAKANA[Math.floor(Math.random() * KATAKANA.length)]
    : String.fromCharCode(33 + Math.floor(Math.random() * 93))
  const g = dist === 0 ? 255 : Math.floor(brightness * 180)
  return { char, color: `rgb(0,${g},0)` }
}

function pre(t) {
  columns.forEach(c => { c.y = (c.y + c.speed) % rows })
}
```

### 4. PHOSPHOR VIGIL

Amber/green monochrome with three flicker modes and CRT vignette:

```js
const AMBER = [255, 176, 0]  // or GREEN = [0, 255, 65]
const density = ' .:-=+*#%@'

function main(x, y, t, cols, rows, flickerMode) {
  // Base value from noise
  let v = Math.sin(x * 0.3 + y * 0.2) * 0.5 + 0.5

  // Flicker modes
  if (flickerMode === 'breathing')
    v *= Math.sin(t * 0.5) * 0.15 + 0.85
  else if (flickerMode === 'interference')
    v *= 1 - 0.3 * Math.abs(Math.sin(y * 0.1 + t * 2))

  // CRT vignette: darken edges
  const dx = (x / cols - 0.5) * 2, dy = (y / rows - 0.5) * 2
  v *= 1 - 0.3 * (dx*dx + dy*dy)

  v = Math.max(0, Math.min(1, v))
  const [r, g, b] = AMBER
  return {
    char: density[Math.floor(v * (density.length - 1))],
    color: `rgba(${r},${g},${b},${v.toFixed(2)})`
  }
}
```

### 5. Data Stream

Scrolling hex/binary with highlight bursts:

```js
const HEX = '0123456789ABCDEF'
const speeds = Array.from({length: cols}, () => 0.5 + Math.random() * 2)
const bursts = []  // [{x, y, ttl}]

function main(x, y, t) {
  // Scrolling hex
  const scrollY = Math.floor(y + t * speeds[x]) % 16
  const char = HEX[scrollY]

  // Check for active burst at this cell
  const burst = bursts.find(b => Math.abs(b.x - x) <= 2 && Math.abs(b.y - y) <= 1 && b.ttl > 0)
  if (burst) {
    const fade = burst.ttl / 10
    return { char, color: `rgba(0,220,255,${fade.toFixed(2)})` }
  }

  return { char, color: 'rgba(100,140,180,0.4)' }
}

function pre(t) {
  // Spawn random bursts
  if (Math.random() < 0.02)
    bursts.push({ x: Math.floor(Math.random() * cols), y: Math.floor(Math.random() * rows), ttl: 10 })
  bursts.forEach(b => b.ttl--)
  while (bursts.length && bursts[0].ttl <= 0) bursts.shift()
}
```

## Performance

- Text renderer at ~80x40 (3,200 cells) at 30fps is lightweight
- Use `will-change: contents` on the `<pre>` element
- Reduce FPS to 15-20 for subtle atmospheric effects:
  ```js
  let last = 0; const interval = 1000 / 20  // 20fps
  function loop(now) {
    requestAnimationFrame(loop)
    if (now - last < interval) return
    last = now
    render()
  }
  ```
- `innerHTML` batch per row, not per-character DOM operations
- For content-heavy pages, consider `<canvas>` renderer instead of DOM spans

## Accessibility

```js
// Required attributes on the grid element
gridEl.setAttribute('aria-hidden', 'true')
gridEl.style.pointerEvents = 'none'
gridEl.style.userSelect = 'none'

// Respect reduced motion
const prefersReduced = matchMedia('(prefers-reduced-motion: reduce)').matches
if (prefersReduced) { renderOnce(); return }  // single static frame
```

## When to Use

- "Bloomberg Terminal", "command center", "retro-futuristic" creative directions
- Hero sections needing atmospheric depth without images
- Background behind glassmorphism panels (characters show through blur)
- Loading states and transition screens
- The "generative pattern background" listed in Atmosphere & Texture (SKILL.md)

## When NOT to Use

- Clean/minimal designs where noise distracts
- Mobile-first layouts where performance matters
- Light-mode / editorial designs (character grids read as "dark/techy")
- Pages with dense content where background competes for attention

## Source

Architecture adapted from [play.core](https://github.com/ertdfgcvb/play.core) (Apache 2.0) by Andreas Gysin.

## html-in-canvas (Future Watch)

The [WICG html-in-canvas](https://github.com/WICG/html-in-canvas) proposal would enable live HTML content as WebGL textures on 3D surfaces—interactive UI wrapped around product geometry, dashboard widgets with perspective distortion. Chrome Canary prototype behind `#canvas-draw-element` flag. Mozilla formally opposed. Not production-ready. Reference: [jakearchibald/curved-markup](https://github.com/jakearchibald/random-stuff/tree/main/apps/curved-markup).
