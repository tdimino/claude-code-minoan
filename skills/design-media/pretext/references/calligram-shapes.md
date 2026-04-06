# Calligram Shapes with Pretext

## Overview

A calligram fills a shape's interior with repeated characters from a word, using Pretext's `prepareWithSegments()` for precise proportional character spacing. Two techniques are available:

1. **SDF (Signed Distance Function)** — mathematical shapes (heart, circle, star, wave, spiral). Best for geometric and custom combined shapes.
2. **Pixel-Mask (Glyph-Mask)** — any font glyph as the calligram shape, using native canvas `fillText()` + `getImageData()` to create the mask. Best for letter-shaped calligrams, "letters made of letters," and alphabet galleries. Inspired by [Letterbox](https://www.letterbox.sh/) by Charlie Clark.

---

## Signed Distance Functions

SDFs return negative values inside the shape, positive outside. The boundary is at 0.

### Heart

```js
function heartSDF(nx, ny) {
  const x = nx * 1.2
  const y = -ny * 1.1 + 0.3
  const d = Math.sqrt(x * x + y * y)
  const angle = Math.atan2(y, x)
  const heartR = 0.5 + 0.15 * Math.cos(angle * 2) + 0.1 * Math.cos(angle) + 0.02 * Math.sin(angle * 3)
  return d - heartR
}
```

### Circle

```js
function circleSDF(nx, ny) {
  return Math.sqrt(nx * nx + ny * ny) - 0.75
}
```

### Star (5-pointed)

```js
function starSDF(nx, ny) {
  const angle = Math.atan2(ny, nx)
  const d = Math.sqrt(nx * nx + ny * ny)
  const points = 5
  const innerR = 0.35
  const outerR = 0.8
  const a = ((angle / Math.PI + 1) / 2 * points) % 1
  const r = a < 0.5
    ? innerR + (outerR - innerR) * (1 - Math.abs(a - 0.25) * 4)
    : innerR + (outerR - innerR) * (1 - Math.abs(a - 0.75) * 4)
  return d - r
}
```

### Wave

```js
function waveSDF(nx, ny) {
  const waveY = Math.sin(nx * 4) * 0.25
  const thickness = 0.2 + Math.cos(nx * 2) * 0.05
  return Math.abs(ny - waveY) - thickness
}
```

### Spiral

```js
function spiralSDF(nx, ny) {
  const d = Math.sqrt(nx * nx + ny * ny)
  const angle = Math.atan2(ny, nx)
  const spiralR = ((angle / Math.PI + 1) / 2) * 0.6 + d * 0.15
  const armDist = Math.abs((d - spiralR * 0.5) % 0.25 - 0.125)
  return d > 0.85 ? d - 0.85 : armDist - 0.06
}
```

### Creating Custom SDFs

Combine primitives with boolean operations:

- **Union**: `Math.min(sdf1(x,y), sdf2(x,y))`
- **Intersection**: `Math.max(sdf1(x,y), sdf2(x,y))`
- **Subtraction**: `Math.max(sdf1(x,y), -sdf2(x,y))`
- **Smooth union**: `let h = Math.max(k - Math.abs(a-b), 0) / k; return Math.min(a,b) - h*h*k*0.25`

Common primitives:

- **Rectangle**: `Math.max(Math.abs(nx) - w, Math.abs(ny) - h)`
- **Ring**: `Math.abs(Math.sqrt(nx*nx + ny*ny) - radius) - thickness`
- **Diamond**: `Math.abs(nx) + Math.abs(ny) - size`
- **Triangle**: Use barycentric coordinates or half-plane intersection

---

## Character Measurement

Use `prepareWithSegments()` for precise proportional width. CSS `measureText` is unreliable at small sizes—this is Pretext's core value here.

```js
import { prepareWithSegments, layoutWithLines } from 'https://esm.sh/@chenglou/pretext@0.0.2'

const charWidthCache = new Map()

function measureChar(ch, fontSize) {
  const key = `${ch}:${fontSize}`
  const cached = charWidthCache.get(key)
  if (cached !== undefined) return cached

  const font = `${fontSize}px "Helvetica Neue", Helvetica, sans-serif`
  const prepared = prepareWithSegments(ch, font)
  const result = layoutWithLines(prepared, 10000, fontSize * 1.2)
  const width = result.lines.length > 0 ? result.lines[0].width : fontSize * 0.5
  charWidthCache.set(key, width)
  return width
}
```

Cache character widths—they're constant per font/size combination. Measuring the full word on each placement call is expensive; cache per `ch:fontSize` key instead.

---

## Filling Algorithm

Scan line by line. For each candidate x position, test the SDF. Step size varies with distance—this gives clean edges without over-sampling the interior.

```js
function generateCalligram(word, sdf, canvasSize, fontSize) {
  const positions = []
  const padding = canvasSize * 0.08
  const drawArea = canvasSize - padding * 2
  const lineHeight = fontSize * 1.3
  let charCounter = 0

  for (let py = padding; py < canvasSize - padding; py += lineHeight) {
    let px = padding
    while (px < canvasSize - padding) {
      // Convert pixel coords to normalized [-1, 1]
      const nx = (px - canvasSize / 2) / (drawArea / 2)
      const ny = (py - canvasSize / 2) / (drawArea / 2)
      const dist = sdf(nx, ny)

      if (dist < -0.02) {
        // Inside shape: place a character
        const idx = charCounter % word.length
        const ch = word[idx]
        const w = measureChar(ch, fontSize)
        positions.push({ ch, x: px, y: py, width: w, charIdx: idx, dist: Math.abs(dist), globalIdx: charCounter })
        px += w + fontSize * 0.05 // character width + small gap
        charCounter++
      } else if (dist < 0.05) {
        px += fontSize * 0.3  // near boundary: smaller steps
      } else {
        px += fontSize * 0.5  // far outside: larger steps
      }
    }
  }
  return positions
}
```

**Step size logic**: Far outside the shape, skip in large increments. Near the boundary (`dist < 0.05`), slow down to avoid missing interior characters. Inside (`dist < -0.02`), step by actual character width so characters pack tightly without overlap.

The `-0.02` inset threshold prevents characters from straddling the boundary. Increase the magnitude for a tighter inset (border gap), decrease toward 0 for characters flush with the edge.

---

## Spring Animation

Characters fly in from random scatter positions to their calligram targets. Staggered delays create a cascade.

```js
function animateEntrance(positions, canvasSize) {
  return positions.map(p => ({
    ...p,
    targetX: p.x,
    targetY: p.y,
    currentX: canvasSize / 2 + (Math.random() - 0.5) * canvasSize * 0.3,
    currentY: canvasSize / 2 + (Math.random() - 0.5) * canvasSize * 0.3,
    velX: 0, velY: 0,
    currentAlpha: 0, targetAlpha: 1,
    delay: p.globalIdx * 0.015 + Math.random() * 0.1
  }))
}

// In animation loop (called each rAF frame):
for (const ch of animChars) {
  const t = Math.max(0, animTime - ch.delay)
  if (t <= 0) continue

  const springK = 0.08
  const damping = 0.75
  ch.velX = (ch.velX + (ch.targetX - ch.currentX) * springK) * damping
  ch.velY = (ch.velY + (ch.targetY - ch.currentY) * springK) * damping
  ch.currentX += ch.velX
  ch.currentY += ch.velY
  ch.currentAlpha += (ch.targetAlpha - ch.currentAlpha) * 0.06
}
```

`springK` controls stiffness—higher values snap faster. `damping` below 1.0 bleeds velocity each frame. At `0.75` you get a slight overshoot and settle; increase toward `0.9` for a stiffer, less bouncy feel.

`delay: p.globalIdx * 0.015` staggers characters by their scan order (top-left first). Add `Math.random() * 0.1` for organic variation.

---

## Color Generation

Derive a gradient from the word itself so color is deterministic but unique per word.

```js
function wordColor(word, charIdx, total) {
  const hue = (word.charCodeAt(0) * 37 + word.length * 73) % 360
  const t = charIdx / Math.max(1, total - 1)
  const h = (hue + t * 60) % 360
  const s = 60 + Math.sin(t * Math.PI) * 20
  const l = 55 + Math.sin(t * Math.PI * 2) * 15
  return `hsl(${h}, ${s}%, ${l}%)`
}
```

Base hue from `charCodeAt(0) * 37 + word.length * 73`—the prime multipliers spread short words across the full hue wheel. Each character shifts hue by up to 60° across the shape. Saturation and lightness ride sine waves over the full character range, producing smooth oscillation rather than linear fade.

To vary the palette range: change the `60` in `t * 60` (wider = more hue shift across the shape).

---

## Canvas Rendering

Always scale by `devicePixelRatio` for crisp rendering on high-DPI displays. Measure and generate at logical pixel coordinates; multiply only at draw time.

```js
const dpr = devicePixelRatio
canvas.width = canvasSize * dpr
canvas.height = canvasSize * dpr
canvas.style.width = canvasSize + 'px'
canvas.style.height = canvasSize + 'px'
```

```js
// Per-frame render:
ctx.clearRect(0, 0, canvas.width, canvas.height)
const fontSize = charSize * dpr
ctx.font = `${fontSize}px "Helvetica Neue", Helvetica, sans-serif`
ctx.textBaseline = 'top'

const total = animChars.length
for (const ch of animChars) {
  if (ch.currentAlpha < 0.01) continue
  ctx.globalAlpha = ch.currentAlpha
  ctx.fillStyle = wordColor(word, ch.charIdx, total)
  ctx.fillText(ch.ch, ch.currentX * dpr, ch.currentY * dpr)
}

ctx.globalAlpha = 1
```

**Important**: `measureChar` runs at logical pixel `fontSize` (before DPR multiplication). Apply DPR only when setting `canvas.font` and calling `fillText`. If you measure at DPR-scaled sizes, the layout coordinates will be off by a factor of `dpr`.

---

## Full Integration Example

```js
import { prepareWithSegments, layoutWithLines } from 'https://esm.sh/@chenglou/pretext@0.0.2'

const CANVAS_SIZE = 500
const CHAR_SIZE = 11

const canvas = document.createElement('canvas')
const ctx = canvas.getContext('2d')
document.body.appendChild(canvas)

const dpr = devicePixelRatio
canvas.width = CANVAS_SIZE * dpr
canvas.height = CANVAS_SIZE * dpr
canvas.style.width = CANVAS_SIZE + 'px'
canvas.style.height = CANVAS_SIZE + 'px'

// --- Measurement ---
const charWidthCache = new Map()
function measureChar(ch, fontSize) {
  const key = `${ch}:${fontSize}`
  if (charWidthCache.has(key)) return charWidthCache.get(key)
  const prepared = prepareWithSegments(ch, `${fontSize}px "Helvetica Neue", Helvetica, sans-serif`)
  const result = layoutWithLines(prepared, 10000, fontSize * 1.2)
  const w = result.lines.length > 0 ? result.lines[0].width : fontSize * 0.5
  charWidthCache.set(key, w)
  return w
}

// --- SDF ---
function heartSDF(nx, ny) {
  const x = nx * 1.2
  const y = -ny * 1.1 + 0.3
  const d = Math.sqrt(x * x + y * y)
  const angle = Math.atan2(y, x)
  const r = 0.5 + 0.15 * Math.cos(angle * 2) + 0.1 * Math.cos(angle) + 0.02 * Math.sin(angle * 3)
  return d - r
}

// --- Layout ---
function generateCalligram(word, sdf) {
  const positions = []
  const padding = CANVAS_SIZE * 0.08
  const drawArea = CANVAS_SIZE - padding * 2
  const lineHeight = CHAR_SIZE * 1.3
  let counter = 0
  for (let py = padding; py < CANVAS_SIZE - padding; py += lineHeight) {
    let px = padding
    while (px < CANVAS_SIZE - padding) {
      const nx = (px - CANVAS_SIZE / 2) / (drawArea / 2)
      const ny = (py - CANVAS_SIZE / 2) / (drawArea / 2)
      const dist = sdf(nx, ny)
      if (dist < -0.02) {
        const ch = word[counter % word.length]
        const w = measureChar(ch, CHAR_SIZE)
        positions.push({ ch, x: px, y: py, width: w, charIdx: counter % word.length, globalIdx: counter })
        px += w + CHAR_SIZE * 0.05
        counter++
      } else if (dist < 0.05) {
        px += CHAR_SIZE * 0.3
      } else {
        px += CHAR_SIZE * 0.5
      }
    }
  }
  return positions
}

// --- Animation state ---
const word = 'LOVE'
const positions = generateCalligram(word, heartSDF)
const animChars = positions.map((p, i) => ({
  ...p,
  targetX: p.x, targetY: p.y,
  currentX: CANVAS_SIZE / 2 + (Math.random() - 0.5) * CANVAS_SIZE * 0.3,
  currentY: CANVAS_SIZE / 2 + (Math.random() - 0.5) * CANVAS_SIZE * 0.3,
  velX: 0, velY: 0,
  currentAlpha: 0, targetAlpha: 1,
  delay: i * 0.015 + Math.random() * 0.1
}))

function wordColor(word, charIdx, total) {
  const hue = (word.charCodeAt(0) * 37 + word.length * 73) % 360
  const t = charIdx / Math.max(1, total - 1)
  return `hsl(${(hue + t * 60) % 360}, ${60 + Math.sin(t * Math.PI) * 20}%, ${55 + Math.sin(t * Math.PI * 2) * 15}%)`
}

// --- Loop ---
let animTime = 0
const fontSize = CHAR_SIZE * dpr
ctx.font = `${fontSize}px "Helvetica Neue", Helvetica, sans-serif`
ctx.textBaseline = 'top'

function frame() {
  animTime += 1 / 60
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  for (const ch of animChars) {
    const t = Math.max(0, animTime - ch.delay)
    if (t > 0) {
      ch.velX = (ch.velX + (ch.targetX - ch.currentX) * 0.08) * 0.75
      ch.velY = (ch.velY + (ch.targetY - ch.currentY) * 0.08) * 0.75
      ch.currentX += ch.velX
      ch.currentY += ch.velY
      ch.currentAlpha += (1 - ch.currentAlpha) * 0.06
    }
    if (ch.currentAlpha < 0.01) continue
    ctx.globalAlpha = ch.currentAlpha
    ctx.fillStyle = wordColor(word, ch.charIdx, animChars.length)
    ctx.fillText(ch.ch, ch.currentX * dpr, ch.currentY * dpr)
  }
  ctx.globalAlpha = 1
  requestAnimationFrame(frame)
}

requestAnimationFrame(frame)
```

---

## Pixel-Mask Technique (Glyph-Mask Calligrams)

An alternative to SDF calligrams that works with **any font glyph** as the shape. Instead of defining a mathematical distance function, draw the large letter on an off-screen canvas and read the pixel data back as a binary mask. This technique was reverse-engineered from [Letterbox](https://www.letterbox.sh/) by Charlie Clark.

**When to use pixel-mask instead of SDF:**
- The shape is a font glyph (any character in any font)
- Complex contours that resist SDF approximation (serifs, swashes, ligatures)
- "Letters made of letters" / alphabet gallery effects
- The shape needs to change dynamically (user-typed text)

### Mask Creation Pipeline

```js
const MASK_SIZE = 500
const maskCanvas = document.createElement('canvas')
maskCanvas.width = MASK_SIZE
maskCanvas.height = MASK_SIZE
const maskCtx = maskCanvas.getContext('2d')

function createGlyphMask(letter, font, fillLineHeight) {
  maskCtx.clearRect(0, 0, MASK_SIZE, MASK_SIZE)
  maskCtx.font = font  // e.g. 'italic bold 400px "Playfair Display"'
  maskCtx.fillStyle = '#fff'
  maskCtx.textBaseline = 'alphabetic'

  // Center the letter horizontally
  const metrics = maskCtx.measureText(letter)
  const x = (MASK_SIZE - (metrics.actualBoundingBoxLeft + metrics.actualBoundingBoxRight)) / 2
        + metrics.actualBoundingBoxLeft
  // Center vertically using ascent/descent
  const ascent = metrics.actualBoundingBoxAscent
  const descent = metrics.actualBoundingBoxDescent
  const y = (MASK_SIZE - (ascent + descent)) / 2 + ascent

  maskCtx.fillText(letter, x, y)

  // Read pixel data and build row masks
  const imageData = maskCtx.getImageData(0, 0, MASK_SIZE, MASK_SIZE).data
  const rows = []

  for (let rowY = 0; rowY < MASK_SIZE; rowY += fillLineHeight) {
    const rowMask = new Uint8Array(MASK_SIZE)
    const bandEnd = Math.min(rowY + fillLineHeight, MASK_SIZE)

    // Mark columns where ANY pixel in this row band has alpha > 128
    for (let scanY = rowY; scanY < bandEnd; scanY++) {
      for (let col = 0; col < MASK_SIZE; col++) {
        if (imageData[(scanY * MASK_SIZE + col) * 4 + 3] > 128) {
          rowMask[col] = 1
        }
      }
    }

    // Extract contiguous fill regions (runs of 1s)
    const regions = []
    let start = -1
    for (let col = 0; col <= MASK_SIZE; col++) {
      if (col < MASK_SIZE && rowMask[col]) {
        if (start === -1) start = col
      } else if (start !== -1) {
        if (col - start > 10) { // minimum region width
          regions.push({ x: start, width: col - start })
        }
        start = -1
      }
    }

    if (regions.length > 0) {
      rows.push({ y: rowY, regions })
    }
  }

  return rows
}
```

### Fill Text Layout Within Mask

```js
function layoutFillText(maskRows, fillText, fillFont, ctx) {
  const characters = []
  let textIdx = 0
  ctx.font = fillFont  // e.g. 'italic bold 11px "Playfair Display"'

  for (const row of maskRows) {
    for (const region of row.regions) {
      let px = region.x
      const regionEnd = region.x + region.width

      while (px < regionEnd) {
        const ch = fillText[textIdx % fillText.length]
        const charWidth = ctx.measureText(ch).width
        if (px + charWidth > regionEnd) break

        characters.push({
          char: ch,
          hx: px,
          hy: row.y,
          dx: 0,
          dy: 0
        })

        px += charWidth
        textIdx++
      }
    }
  }

  return characters
}
```

### Cursor Displacement

Per-character spring physics driven by cursor proximity. Characters within a radius receive a radial push force that decays with distance. Damping bleeds velocity each frame so characters return to rest.

```js
function updateDisplacement(characters, pointer, config) {
  const { radius = 100, force = 35, damping = 0.94 } = config
  let needsFrame = false

  for (const ch of characters) {
    if (pointer) {
      const rx = (ch.hx + ch.dx) - pointer.x
      const ry = (ch.hy + ch.dy) - pointer.y
      const dist = Math.sqrt(rx * rx + ry * ry)

      if (dist < radius && dist > 0) {
        const strength = (1 - dist / radius) * force
        ch.dx += (rx / dist) * strength * 0.3
        ch.dy += (ry / dist) * strength * 0.3
      }
    }

    ch.dx *= damping
    ch.dy *= damping

    if (Math.abs(ch.dx) > 0.01 || Math.abs(ch.dy) > 0.01) {
      needsFrame = true
    }
  }

  return needsFrame
}
```

Only run the rAF loop when `needsFrame` is true — this avoids burning CPU when the canvas is at rest.

### Fill Text Models

| Model | Fill text source |
|-------|-----------------|
| `self` | The word itself repeated (existing calligram behavior) |
| `lorem` | Lorem ipsum dolor sit amet... (typographic poster effect) |
| `alphabet` | ABCDEFGHIJKLMNOPQRSTUVWXYZ repeated (recursive "letters made of letters") |
| `custom` | User-provided text string |

Generate lorem fill text long enough to fill the mask — repeat the source if shorter than 2000 characters.

### Letterbox Gallery Layout

For "alphabet gallery" effects where each character gets its own canvas in a CSS grid:

```html
<div class="grid" style="
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 3px;
  background: #1a1a1a;
">
  <!-- One per letter -->
  <div style="position: relative; aspect-ratio: 1; background: #0a0a0a;">
    <canvas width="1000" height="1000"
            style="display: block; width: 100%; height: 100%;"></canvas>
    <span style="position: absolute; bottom: 8px; right: 10px;
                 font-size: 10px; color: rgba(255,255,255,0.15);
                 pointer-events: none;">A</span>
  </div>
</div>
```

Each canvas is 1000x1000 physical pixels (500x500 logical at 2x DPR). The mask and fill layout run independently per canvas, so each letter has its own character array and mousemove handler.

### SDF vs Pixel-Mask Decision

| Criterion | SDF | Pixel-Mask |
|-----------|-----|------------|
| Shape source | Mathematical function | Any font glyph |
| Custom shapes | Composable primitives (union, intersect) | Requires a rasterized image |
| Edge quality | Infinite resolution | Limited by mask canvas size |
| Setup cost | Define SDF function | Off-screen canvas + getImageData |
| Font flexibility | None (shape is math) | Any installed/loaded font |
| Best for | Hearts, stars, waves, spirals | Letter calligrams, alphabet galleries |
