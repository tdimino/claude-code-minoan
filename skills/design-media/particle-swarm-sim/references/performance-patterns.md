# Performance Patterns

The behavior function runs 20,000 times per frame at 60fps = **1,200,000 calls per second**. Every allocation, branch, or string operation is multiplied by that factor.

## The Allocation Budget

At 60fps with 20K particles, the frame budget is 16.6ms. The particle loop alone should target **< 8ms** to leave headroom for camera updates, buffer uploads, and rendering.

A single `new THREE.Vector3()` per particle = 20,000 allocations per frame = **1.2M allocations per second**. V8's garbage collector will pause for ~5-10ms collections, eating half the frame budget.

### Rule: Zero Allocations in the Function Body

**Wrong:**
```javascript
const pos = new THREE.Vector3(x, y, z);
target.copy(pos);
```

**Right:**
```javascript
target.set(x, y, z);
```

**Wrong:**
```javascript
const palette = [0.0, 0.33, 0.15, 0.75];
color.setHSL(palette[i % 4], 1, 0.5);
```

**Right:**
```javascript
const basePair = i % 4;
const hue = basePair === 0 ? 0.0 : basePair === 1 ? 0.33 : basePair === 2 ? 0.15 : 0.75;
color.setHSL(hue, 1, 0.5);
```

## Math Over Logic

V8's branch predictor fails when the branch outcome varies per-iteration. With 20K particles, branches based on `i` are effectively random.

**Wrong:**
```javascript
if (i < count / 2) {
  target.set(Math.cos(angle) * 10, 0, Math.sin(angle) * 10);
} else {
  target.set(Math.cos(angle) * 20, 5, Math.sin(angle) * 20);
}
```

**Right:**
```javascript
const t = i / count;
const r = 10 + t * 10;
const y = t * 5;
target.set(Math.cos(angle) * r, y, Math.sin(angle) * r);
```

The continuous function eliminates the branch and produces a smooth transition instead of a hard boundary.

## Epsilon Guards

Division by zero produces `Infinity`, which poisons the entire Float32Array when written to the position buffer. Every division needs a guard.

**Wrong:**
```javascript
const r = 1 / distance;
```

**Right:**
```javascript
const r = 1 / (distance + 0.0001);
```

For `Math.log`:
```javascript
const logR = Math.log(r + 0.001);
```

For `Math.acos` (domain [-1, 1]):
```javascript
const theta = Math.acos(Math.max(-1, Math.min(1, value)));
```

## Constants at the Top

`addControl()` creates a DOM slider on first call but returns the current float value on subsequent calls. The DOM creation is a one-time cost, but the function call overhead (hash lookup + return) happens 20K times per frame per control.

This is acceptable — the hash lookup is O(1) and V8 inlines it after a few frames. But pre-computing derived values from controls at the function body's top avoids redundant math:

```javascript
const arms = addControl('arms', 'Arms', 2, 8, 4);
const armCount = Math.floor(arms);
const armAngle = Math.PI * 2 / armCount;
```

## Spherical Coordinate Distribution

Uniform distribution on a sphere surface (avoids pole clustering):

```javascript
const phi = Math.acos(1 - 2 * (i / count));
const theta = i * 2.399963; // golden angle
```

Using `Math.random()` for `theta` creates different distributions each frame. Use deterministic functions of `i` for stable structures.

## Profiling

To check frame timing, inject this at the start of a sim:

```javascript
if (i === 0 && Math.floor(time) !== Math.floor(time - 0.016)) {
  const label = 'Frame ' + Math.floor(time);
}
```

The host displays FPS in the top-right corner. If it drops below 45, reduce `particleCount` or simplify the math.

## Pattern Library

### Logarithmic Spiral
```javascript
const angle = armIndex * armAngle + t * 12 + time * spin;
const r = Math.pow(t, 0.5) * scale;
const spiralAngle = angle + Math.log(r + 0.001) * spread;
```

### Torus
```javascript
const u = t * Math.PI * 2;
const v = (i % rings) / rings * Math.PI * 2;
const x = (R + r * Math.cos(v)) * Math.cos(u);
const y = r * Math.sin(v);
const z = (R + r * Math.cos(v)) * Math.sin(u);
```

### Lorenz Attractor (time-stepped)
```javascript
const dt = 0.005;
const offset = i * dt;
let lx = 0.1, ly = 0, lz = 0;
const steps = Math.floor(offset / dt);
for (let s = 0; s < Math.min(steps, 200); s++) {
  lx += (sigma * (ly - lx)) * dt;
  ly += (lx * (rho - lz) - ly) * dt;
  lz += (lx * ly - beta * lz) * dt;
}
```
Note: The inner loop's iteration count is bounded (`Math.min(steps, 200)`) to prevent excessive computation for high particle indices.
