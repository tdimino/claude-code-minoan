# API Contract

The behavior function body receives these variables as named parameters. The host calls the function once per particle per frame inside a `for` loop.

## Read-Only Variables

### `i` — Particle Index
- **Type**: `number` (integer)
- **Range**: `0` to `count - 1`
- **Usage**: Derive per-particle properties (position, color, phase offset)
- **Pattern**: `i / count` gives normalized 0-1 progress through the swarm

### `count` — Total Particles
- **Type**: `number` (integer)
- **Range**: 5,000 to 50,000 (configured by host)
- **Usage**: Normalize `i` for even distributions: `const t = i / count;`

### `time` — Simulation Time
- **Type**: `number` (float)
- **Units**: Seconds since simulation start
- **Usage**: Animate positions and colors: `Math.sin(time * speed + i * offset)`
- **Note**: Affected by `simSpeed` (gesture-controllable). Not wall-clock time.

### `THREE` — Safe Three.js Subset
- **Type**: Frozen object with `Vector3`, `Color`, `MathUtils`
- **NOT the full Three.js library** — FileLoader, ImageLoader, and other I/O classes are excluded
- **Available**:
  - `THREE.Vector3` — constructor (use sparingly, prefer `target.set()`)
  - `THREE.Color` — constructor (use sparingly, prefer `color.setHSL()`)
  - `THREE.MathUtils.lerp(a, b, t)` — linear interpolation
  - `THREE.MathUtils.clamp(v, min, max)` — clamping
  - `THREE.MathUtils.mapLinear(v, a1, a2, b1, b2)` — range remapping

## Write-Only Variables

### `target` — Particle Position
- **Type**: `THREE.Vector3` (pre-allocated, reused across particles)
- **Mutation**: `target.set(x, y, z)` — sets all three components
- **Pre-loaded**: Contains the particle's current position from the previous frame
- **Constraint**: All values must be finite. NaN/Infinity causes the position write to be skipped.

### `color` — Particle Color
- **Type**: `THREE.Color` (pre-allocated, reused across particles)
- **Mutation**: `color.setHSL(h, s, l)` or `color.set(hex)` or `color.setRGB(r, g, b)`
- **Pre-loaded**: Contains the particle's current color from the previous frame
- **Constraint**: All values must be finite. NaN/Infinity causes the color write to be skipped.
- **HSL ranges**: h: 0-1 (wraps), s: 0-1, l: 0-1

## Helper Functions

### `addControl(id, label, min, max, initial) => float`
- **First call**: Creates a UI slider with the given label and range. Returns `initial`.
- **Subsequent calls**: Returns the slider's current value (user-adjustable).
- **`id`**: Unique string identifier. Duplicate IDs return the existing control's value.
- **Performance**: Safe to call per-particle. The DOM creation happens only once per unique ID; subsequent calls are a hash lookup returning a float.

### `setInfo(title, description)`
- **Guard**: Call only when `i === 0`. Calling per-particle hammers the DOM.
- **Updates**: HUD title and description overlay in the top-left.
- **Pattern**: `if (i === 0) setInfo('My Sim', 'Description here');`

### `annotate(id, x, y, z, labelText)`
- **Guard**: Call only when `i === 0`.
- **Creates**: A floating label projected from 3D coordinates to screen position.
- **Parameters**: Numeric `x, y, z` coordinates (not a Vector3 — avoids per-frame allocation).
- **`id`**: Unique string. Reuses the existing DOM element on subsequent calls.
- **Visibility**: Hidden when the 3D point is behind the camera.
- **Pattern**: `if (i === 0) annotate('center', 0, 0, 0, 'Origin');`

## Edge Cases

- **NaN positions**: The host silently skips the position write. The particle retains its previous position.
- **NaN colors**: The host silently skips the color write. The particle retains its previous color.
- **Runtime exceptions**: The host catches at the frame level (not per-particle). A single throw disables the entire sim and displays the error. Fix your code and re-inject.
- **Duplicate control IDs**: Returns the existing control's current value. Does not create a second slider.
- **Count changes**: If the host changes `particleCount` between injections, your function body sees the new `count` automatically.

## Minimal Valid Function Body

```javascript
if (i === 0) setInfo('Dot', 'One point at the origin');
target.set(0, 0, 0);
color.setHSL(0, 0, 1);
```

## Complete Function Body

```javascript
const speed = addControl('speed', 'Speed', 0.1, 5.0, 1.0);
const scale = addControl('scale', 'Scale', 5, 40, 15);
const hueShift = addControl('hue', 'Hue Shift', 0, 1, 0);

if (i === 0) {
  setInfo('Breathing Sphere', 'Pulsing distribution on sphere surface');
  annotate('north', 0, scale + 3, 0, 'North Pole');
  annotate('south', 0, -(scale + 3), 0, 'South Pole');
}

const phi = (i / count) * Math.PI * 2 * 10;
const theta = Math.acos(1 - 2 * (i / count));
const r = scale + Math.sin(time * speed + i * 0.01) * 3;

target.set(
  r * Math.sin(theta) * Math.cos(phi),
  r * Math.sin(theta) * Math.sin(phi),
  r * Math.cos(theta)
);
color.setHSL((i / count + hueShift) % 1, 0.8, 0.5 + 0.2 * Math.sin(time + i * 0.1));
```
