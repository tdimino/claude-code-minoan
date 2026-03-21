# Particle System Patterns

Patterns for BufferGeometry particle systems extracted from the Instance visualization.

## BufferGeometry Setup

Three attributes define each particle:

```javascript
const positions = new Float32Array(PARTICLE_COUNT * 3);  // x,y,z per particle
const colors = new Float32Array(PARTICLE_COUNT * 3);     // r,g,b per particle
const sizes = new Float32Array(PARTICLE_COUNT);           // size per particle

particleGeometry = new THREE.BufferGeometry();
particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
particleGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
particleGeometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
```

## Parallel State Arrays

Per-particle state stored in parallel arrays (not in BufferGeometry):

```javascript
let particlePositions = [];   // THREE.Vector3 — working position
let particleVelocities = [];  // THREE.Vector3 — drift velocity
let particleTargets = [];     // THREE.Vector3 — orbital target
let particleStates = [];      // int — current state (0-3)
let particleWords = [];       // string — label for click-inspect
```

Position is maintained in both the Vector3 array (for math) and the Float32Array buffer (for GPU). Each frame: compute in Vector3, copy to buffer, set `needsUpdate = true`.

## Material Configuration

```javascript
particleMaterial = new THREE.PointsMaterial({
    size: 0.12,
    vertexColors: true,           // use per-particle color attribute
    transparent: true,
    opacity: 0,                   // controlled per-phase
    blending: THREE.AdditiveBlending,  // glow effect
    sizeAttenuation: true         // size scales with distance
});
```

**AdditiveBlending** makes overlapping particles brighter, creating a natural glow. Essential for the ethereal look.

## Particle State Machine

Four states, transitions driven by phase:

| State | Name | Behavior | Phase |
|-------|------|----------|-------|
| 0 | Void | Drift far from center (r>60) | Lattice, Void |
| 1 | Assembling | Move toward orbital target | Awakening |
| 2 | Orbiting | Rotate around lattice center | Conversation, Simultaneity |
| 3 | Dissolving | Drift outward and fade | Dissolution |

### State 0: Void Drift

```javascript
pos.add(vel.clone().multiplyScalar(delta * 8));
if (pos.length() < 60) {
    pos.normalize().multiplyScalar(70);  // push back out
}
```

### State 1: Target-Seeking Assembly

```javascript
const toTarget = target.clone().sub(pos);
const dist = toTarget.length();
if (dist > 0.3) {
    const speed = Math.min(dist * 0.03, 0.4);  // proportional, capped
    pos.add(toTarget.normalize().multiplyScalar(speed));
}
```

The `dist * 0.03` gives natural easing — fast approach, gradual arrival.

### State 2: Orbital Motion

```javascript
const angle = delta * (0.25 + Math.sin(i * 0.1) * 0.1);
const rotY = new THREE.Matrix4().makeRotationY(angle);
const rotX = new THREE.Matrix4().makeRotationX(angle * 0.3);
pos.applyMatrix4(rotY);
pos.applyMatrix4(rotX);

// Maintain orbital distance with oscillation
const orbitDist = 6 + Math.sin(timeline + i) * 2;
const currentDist = pos.length();
if (Math.abs(currentDist - orbitDist) > 0.3) {
    pos.normalize().multiplyScalar(THREE.MathUtils.lerp(currentDist, orbitDist, 0.03));
}

// Vertical oscillation
pos.y += Math.sin(timeline * 2 + i * 0.5) * 0.008;
```

Per-particle angle variation (`Math.sin(i * 0.1)`) prevents uniform rotation.

### State 3: Dissolution

```javascript
const outward = pos.clone().normalize();
pos.add(outward.multiplyScalar(delta * 2.5));
pos.add(vel.clone().multiplyScalar(delta * 15));
```

Combines radial expansion with random drift for organic scattering.

## Progressive Activation

Particles activate/deactivate progressively during transitions:

```javascript
// Awakening: activate in order
if (i < PARTICLE_COUNT * phaseProgress) {
    state = 1;  // assembling
}

// Dissolution: dissolve in order
if (i < PARTICLE_COUNT * phaseProgress) {
    state = 3;  // dissolving
}
```

Creates a wave-like activation/dissolution effect rather than all-at-once.

## Color Lerping

```javascript
if (state === 2) {
    const mix = Math.sin(timeline + i * 0.1) * 0.5 + 0.5;
    color = warmColor.clone().lerp(coolColor, mix);
} else {
    color = coolColor;
}
colors[i * 3] = color.r;
colors[i * 3 + 1] = color.g;
colors[i * 3 + 2] = color.b;
```

The `sin(timeline + i * 0.1)` creates a rolling wave of warm/cool through the particle field. Each particle oscillates between colors at a slightly different phase.

## Buffer Update

After modifying all particles:

```javascript
particleGeometry.attributes.position.needsUpdate = true;
particleGeometry.attributes.color.needsUpdate = true;
```

**Critical**: Without `needsUpdate = true`, changes to Float32Array data are not sent to GPU.

## Click-to-Inspect

```javascript
raycaster.setFromCamera(mouse, camera);
raycaster.params.Points.threshold = 0.5;  // hit radius in world units
const intersects = raycaster.intersectObject(particles);
if (intersects.length > 0) {
    showParticleLabel(intersects[0].index, event.clientX, event.clientY);
}
```

On hit: show word label at click position, temporarily scale particle 3x, fade label after 2s.

## Sphere Distribution

Uniform random distribution on a sphere:

```javascript
const theta = Math.random() * Math.PI * 2;       // azimuth [0, 2pi]
const phi = Math.acos(2 * Math.random() - 1);     // polar [0, pi] — uniform
const r = minRadius + Math.random() * (maxRadius - minRadius);
const x = r * Math.sin(phi) * Math.cos(theta);
const y = r * Math.sin(phi) * Math.sin(theta);
const z = r * Math.cos(phi);
```

The `Math.acos(2 * Math.random() - 1)` ensures uniform distribution (naive `Math.random() * PI` clusters at poles).
