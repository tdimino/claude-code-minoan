# Animated ASCII Sprites: play.core Canvas Pipeline

## Concept

Define sprite animations as play.core-style programs rendering to a `<canvas>` at fixed pixel dimensions. Capture frames via `canvas.toBlob()`. Stitch into sprite sheets with existing `stitch_spritesheet.py`.

This enables procedural ASCII art game assets—fire effects, status overlays, SDF silhouettes—exported as standard sprite sheets with atlas metadata.

## Canvas Renderer Settings

Fixed dimensions ensure consistent frame sizes for sprite sheet stitching:

```js
const CONFIG = {
  canvasWidth: 128,      // px — sprite cell width
  canvasHeight: 128,     // px — sprite cell height
  cols: 16,              // character grid columns
  rows: 16,              // character grid rows
  fps: 12,               // standard sprite frame rate
  font: '8px "Courier New", monospace',
  bgColor: '#000000',    // or 'transparent' for alpha export
}
```

Common sizes: 64x64 (small icons), 128x128 (standard), 256x256 (detail).

## Frame Capture Pattern

```js
const frames = []
let capturing = false
let captureCount = 0
const TOTAL_FRAMES = 8

function render() {
  requestAnimationFrame(render)
  pre(performance.now())
  renderGrid(ctx)  // draw all cells to canvas

  if (capturing && captureCount < TOTAL_FRAMES) {
    canvas.toBlob(blob => {
      frames.push(blob)
      captureCount++
      if (captureCount >= TOTAL_FRAMES) {
        bundleAndDownload(frames)
      }
    }, 'image/png')
  }
}

// Start capture on button click
captureBtn.onclick = () => { capturing = true; captureCount = 0; frames.length = 0 }
```

Use `canvas.toBlob()` (async, no base64 overhead) over `toDataURL()`. Frame counter tracks capture progress.

## Density Strings

Same convention as play.core:

| Name | Length | String | Use |
|------|--------|--------|-----|
| Standard | 30 | `'Ñ@#W$9876543210?!abc;:+=-,._ '` | General purpose |
| Dense | 70 | `'$@B%8&WM#*oahkbdpqwmZO0QLCJUYXz...'` | Photographic detail |
| Blocks | 5 | `'█▓▒░ '` | Retro pixel feel |
| Fire | 11 | `'  .:-=+*#%@'` | Heat maps (light=cold, heavy=hot) |

## SDF Primitives

```js
function sdCircle(p, r) {
  return Math.sqrt(p.x * p.x + p.y * p.y) - r
}
function sdBox(p, b) {
  const dx = Math.abs(p.x) - b.x, dy = Math.abs(p.y) - b.y
  return Math.sqrt(Math.max(dx,0)**2 + Math.max(dy,0)**2) + Math.min(Math.max(dx,dy), 0)
}
function sdSegment(p, a, b, th) {
  const pa = {x:p.x-a.x, y:p.y-a.y}, ba = {x:b.x-a.x, y:b.y-a.y}
  const h = Math.max(0, Math.min(1, (pa.x*ba.x+pa.y*ba.y)/(ba.x*ba.x+ba.y*ba.y)))
  return Math.sqrt((pa.x-ba.x*h)**2 + (pa.y-ba.y*h)**2) - th
}
function opSmoothUnion(d1, d2, k) {
  const h = Math.max(0, Math.min(1, 0.5 + 0.5*(d2-d1)/k))
  return d2*(1-h) + d1*h - k*h*(1-h)
}
```

Glow: `Math.exp(-k * Math.abs(dist))` — higher `k` = tighter glow.

## Procedural Sprite Types

### SDF Silhouettes

Define character outline via SDF composition, fill with density characters:

```js
function main(x, y, time) {
  const st = normalize(x, y)  // [-1, 1] aspect-corrected
  const body = sdCircle(st, 0.4)
  const head = sdCircle({x: st.x, y: st.y - 0.5}, 0.25)
  const dist = opSmoothUnion(body, head, 0.15)

  // Pulse animation
  const pulse = Math.sin(time * 3) * 0.02
  const d = dist + pulse

  if (d < 0) {
    const brightness = Math.exp(-2 * Math.abs(d))
    return { char: density[Math.floor(brightness * density.length)], color: '#fff' }
  }
  return { char: ' ', color: 'transparent' }
}
```

### Cellular Automaton Fire

```js
// Buffer: flat array of heat values 0-1
function pre(buffer, cols, rows) {
  // Propagate heat upward with decay
  for (let y = 0; y < rows - 1; y++)
    for (let x = 0; x < cols; x++)
      buffer[x + y * cols] = (buffer[x + (y+1) * cols] || 0) * 0.85
                              + (Math.random() - 0.5) * 0.1
  // Inject at bottom
  for (let x = 0; x < cols; x++)
    buffer[x + (rows-1) * cols] = 0.5 + Math.random() * 0.5
}

function main(x, y, buffer, cols) {
  const heat = Math.max(0, Math.min(1, buffer[x + y * cols]))
  const r = Math.min(255, heat * 510)
  const g = Math.max(0, heat * 255 - 80)
  const b = Math.max(0, heat * 200 - 160)
  return { char: fireDensity[Math.floor(heat * 10)], color: css(r, g, b) }
}
```

### Status Effects

- **Poison**: Green sine distortion — offset each row's x by `sin(y*0.5 + time*3) * 0.5`. Color: `rgb(0, 200+random*55, 0)`.
- **Shield**: SDF ring glow — `sdCircle(st, 0.6) - sdCircle(st, 0.55)`. Rotating brightness via `sin(atan2(st.y, st.x) * 4 + time * 2)`. Color: cyan.
- **Damage Flash**: Global brightness spike (1.0) → exponential decay (`exp(-elapsed * 5)`). Red tint.

### UI Elements

- **Health Bar**: `sdBox` fill based on HP%. Green → yellow → red color interpolation.
- **Damage Numbers**: Floating text positioned via `y_offset = -time * 30`. Fade alpha over 500ms.

## Export Pipeline

```bash
# 1. Open ascii-sprite-capture.html in browser
# 2. Click "Capture Frames" — downloads frames.zip

# 3. Unzip and stitch
unzip frames.zip -d frames/
python3 ~/.claude/skills/sprite-forge/scripts/stitch_spritesheet.py \
  --input-dir frames/ \
  --cols 8 \
  --cell-size 128x128 \
  --atlas json \
  -o fire_sprite.png

# Output: fire_sprite.png + fire_sprite.json (Phaser-compatible atlas)
```

## Performance

Canvas renderer at 16x16 cells is trivial (<1ms/frame on any hardware). Can generate hundreds of frames in seconds. No GPU needed—entire pipeline is CPU-side `ctx.fillText()`.

## html-in-canvas (Future Watch)

The [WICG html-in-canvas](https://github.com/WICG/html-in-canvas) proposal would enable HTML UI elements textured onto game geometry (in-world terminal screens, inventory panels). Chrome Canary flag `#canvas-draw-element` only. Not actionable yet. Reference: [jakearchibald/curved-markup](https://github.com/jakearchibald/random-stuff/tree/main/apps/curved-markup).

## Source

Architecture adapted from [play.core](https://github.com/ertdfgcvb/play.core) (Apache 2.0) by Andreas Gysin.
