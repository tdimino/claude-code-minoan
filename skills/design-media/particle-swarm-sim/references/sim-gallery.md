# Sim Gallery

Annotated behavior patterns with full math breakdowns. Each pattern is a complete function body that can be pasted into the sandbox code editor.

## 1. Galaxy Spiral

Logarithmic spiral arms with density wave theory.

**Math**: Particles are assigned to arms via `i % armCount`. The spiral angle combines a linear sweep (`t * 12`) with a logarithmic winding (`Math.log(r) * spread`). The radius follows a square-root curve (`Math.pow(t, 0.5) * scale`) to concentrate particles near the core.

**Controls**: arm count, spin rate, thickness, arm spread.

**Reference**: `assets/sims/galaxy-spiral.js`

## 2. DNA Double Helix

Two intertwined helices with base pair connections.

**Math**: Particles split into three groups via `i % 3`: strand A, strand B, and rungs. Strands trace a helix at angle `t * 2π * turns + time * speed` with π offset between A and B. Rung particles interpolate between strand positions at periodic intervals controlled by a sine-wave density gate.

**Controls**: helix radius, pitch (turn spacing), rung density, rotation speed.

**Reference**: `assets/sims/dna-helix.js`

## 3. Flocking Murmuration

Boids-like collective behavior via phase-shifted oscillators.

**Math**: Particles are grouped (`i % groupSize`). Each group orbits its own center, which itself orbits the origin. Individual particles combine group center position + local circular motion + sinusoidal noise + global flow field. No neighbor search, no arrays — all emergent motion comes from overlapping sine waves with incommensurate frequencies.

**Controls**: flock radius, speed, coherence (local orbit size), turbulence.

**Reference**: `assets/sims/flocking-murmuration.js`

## 4. Torus Knot Flow

Particles trace a (p,q) torus knot with index-based phase offset.

```javascript
const p = addControl('p', 'P', 1, 7, 2);
const q = addControl('q', 'Q', 1, 7, 3);
const speed = addControl('speed', 'Flow Speed', 0.1, 3.0, 0.8);
const tubeR = addControl('tube', 'Tube Radius', 0.5, 3.0, 1.0);

if (i === 0) setInfo('Torus Knot', 'p=' + Math.floor(p) + ' q=' + Math.floor(q));

const pInt = Math.floor(p);
const qInt = Math.floor(q);
const t = (i / count) * Math.PI * 2 * pInt + time * speed;
const R = 10;

const cx = (R + tubeR * Math.cos(qInt * t / pInt)) * Math.cos(t);
const cy = tubeR * Math.sin(qInt * t / pInt);
const cz = (R + tubeR * Math.cos(qInt * t / pInt)) * Math.sin(t);

target.set(cx, cy, cz);
color.setHSL((i / count + time * 0.05) % 1, 0.7, 0.5);
```

## 5. Lorenz Attractor

Time-stepped Lorenz system with particle index as time offset.

```javascript
const sigma = addControl('sigma', 'Sigma', 5, 15, 10);
const rho = addControl('rho', 'Rho', 20, 35, 28);
const beta = addControl('beta', 'Beta', 1, 5, 2.667);

if (i === 0) setInfo('Lorenz Attractor', 'Chaotic flow in phase space');

const dt = 0.005;
const steps = Math.min(Math.floor(i * 0.2), 300);
let lx = 0.1, ly = 0, lz = 0;

for (let s = 0; s < steps; s++) {
  const dx = sigma * (ly - lx);
  const dy = lx * (rho - lz) - ly;
  const dz = lx * ly - beta * lz;
  lx += dx * dt;
  ly += dy * dt;
  lz += dz * dt;
}

const breathe = Math.sin(time * 0.5) * 0.3 + 1.0;
target.set(lx * breathe, ly * breathe, (lz - 25) * breathe);
color.setHSL(0.6 + lz * 0.005, 0.7, 0.3 + Math.abs(lx) * 0.01);
```

Note: The inner `for` loop is bounded by `Math.min(steps, 300)` to prevent excessive computation at high particle indices.

## 6. Wave Interference

Two point sources creating interference pattern on a plane.

```javascript
const freq = addControl('freq', 'Frequency', 1, 10, 4);
const amp = addControl('amp', 'Amplitude', 1, 8, 3);
const sep = addControl('sep', 'Source Separation', 2, 20, 10);

if (i === 0) {
  setInfo('Wave Interference', 'Two point sources, constructive and destructive');
  annotate('src1', -sep * 0.5, 0, 0, 'Source 1');
  annotate('src2', sep * 0.5, 0, 0, 'Source 2');
}

const gridSize = Math.ceil(Math.sqrt(count));
const gx = (i % gridSize) / gridSize - 0.5;
const gz = Math.floor(i / gridSize) / gridSize - 0.5;
const wx = gx * 40;
const wz = gz * 40;

const d1 = Math.sqrt((wx + sep * 0.5) * (wx + sep * 0.5) + wz * wz) + 0.0001;
const d2 = Math.sqrt((wx - sep * 0.5) * (wx - sep * 0.5) + wz * wz) + 0.0001;

const wave1 = Math.sin(d1 * freq - time * 3) / (d1 * 0.1 + 1);
const wave2 = Math.sin(d2 * freq - time * 3) / (d2 * 0.1 + 1);
const combined = (wave1 + wave2) * amp;

target.set(wx, combined, wz);

const intensity = Math.abs(combined) / (amp * 2);
color.setHSL(0.6 - intensity * 0.3, 0.8, 0.3 + intensity * 0.4);
```

## 7. Lissajous Orbit

3D Lissajous figure with harmonic ratios.

```javascript
const a = addControl('a', 'X Frequency', 1, 7, 3);
const b = addControl('b', 'Y Frequency', 1, 7, 2);
const c = addControl('c', 'Z Frequency', 1, 7, 5);

if (i === 0) setInfo('Lissajous', Math.floor(a) + ':' + Math.floor(b) + ':' + Math.floor(c));

const t = (i / count) * Math.PI * 2 + time * 0.3;
const scale = 12;

target.set(
  Math.sin(a * t) * scale,
  Math.sin(b * t + Math.PI * 0.5) * scale,
  Math.sin(c * t) * scale
);
color.setHSL(i / count, 0.9, 0.55);
```

## 8. Shell Growth

Logarithmic spiral shell with Turing-like stripe pattern.

```javascript
const aperture = addControl('aperture', 'Aperture', 0.1, 0.5, 0.25);
const wavelength = addControl('wave', 'Stripe Wavelength', 2, 20, 8);
const growth = addControl('growth', 'Growth Rate', 0.05, 0.3, 0.12);

if (i === 0) setInfo('Shell Growth', 'Logarithmic spiral with reaction-diffusion stripes');

const t = i / count;
const theta = t * Math.PI * 2 * 6;
const r = Math.exp(growth * theta);
const coneAngle = aperture * Math.sin(i * 37.7) + aperture;

const cx = r * Math.cos(theta);
const cy = r * Math.sin(theta);
const cz = r * coneAngle * Math.cos(i * 13.3);

const breathe = 1 + Math.sin(time * 0.3) * 0.05;
target.set(cx * breathe, cy * breathe, cz * breathe);

const stripe = Math.sin(theta * wavelength + time * 0.5);
const hue = stripe > 0 ? 0.08 : 0.05;
const lum = 0.35 + Math.abs(stripe) * 0.3;
color.setHSL(hue, 0.7, lum);
```

## 9. Magnetic Field Lines

Dipole magnetic field visualization.

```javascript
const strength = addControl('strength', 'Field Strength', 5, 30, 15);
const lineCount = addControl('lines', 'Field Lines', 4, 24, 12);

if (i === 0) {
  setInfo('Magnetic Dipole', 'Field lines from north to south pole');
  annotate('north', 0, strength * 0.3, 0, 'N');
  annotate('south', 0, -strength * 0.3, 0, 'S');
}

const linesInt = Math.floor(lineCount);
const lineIdx = i % linesInt;
const pointOnLine = Math.floor(i / linesInt) / (count / linesInt + 0.0001);

const lineAngle = lineIdx * Math.PI * 2 / linesInt + time * 0.1;
const theta = pointOnLine * Math.PI;

const r = strength * Math.sin(theta) * Math.sin(theta);
const fieldX = r * Math.cos(lineAngle) * Math.sin(theta);
const fieldY = r * Math.cos(theta);
const fieldZ = r * Math.sin(lineAngle) * Math.sin(theta);

target.set(fieldX, fieldY, fieldZ);

const polarity = Math.cos(theta) > 0 ? 0.0 : 0.6;
color.setHSL(polarity, 0.8, 0.4 + pointOnLine * 0.3);
```

## 10. Fractal Tree

Recursive branching approximated via modular arithmetic.

```javascript
const depth = addControl('depth', 'Branch Depth', 3, 8, 5);
const spread = addControl('spread', 'Spread Angle', 0.2, 1.2, 0.5);

if (i === 0) setInfo('Fractal Tree', 'Binary branching via modular arithmetic');

const maxDepth = Math.floor(depth);
let px = 0, py = -15, pz = 0;
let angle = Math.PI * 0.5;
let len = 8;

const branchBits = i % (1 << maxDepth);
for (let d = 0; d < maxDepth; d++) {
  const bit = (branchBits >> d) & 1;
  const dir = bit === 0 ? -1 : 1;
  const sway = Math.sin(time * 0.5 + d * 0.7) * 0.05;

  angle += dir * spread + sway;
  px += Math.cos(angle) * len;
  py += Math.sin(angle) * len;
  pz += Math.sin(angle * 0.7 + i * 0.001) * len * 0.3;
  len *= 0.65;
}

const leafiness = (i / count);
target.set(px, py, pz);
color.setHSL(0.25 + leafiness * 0.1, 0.6 + leafiness * 0.3, 0.25 + leafiness * 0.35);
```
