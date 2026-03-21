# Atmosphere & Visual Effects

Techniques for creating depth, mood, and spatial presence.

## Scene Foundation

```javascript
scene = new THREE.Scene();
scene.background = new THREE.Color(0x050508);  // near-black, not pure black
scene.fog = new THREE.FogExp2(0x050508, 0.012);  // exponential fog, same as bg
```

Fog density 0.012 — objects beyond ~150 units fade to background. Increase for claustrophobic feel (0.02-0.03), decrease for vast space (0.005-0.008).

## Star Field

2000 stars distributed uniformly on a sphere:

```javascript
for (let i = 0; i < STAR_COUNT; i++) {
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);  // uniform sphere distribution
    const r = 150 + Math.random() * 250;  // between fog and far clip

    // 50/50 color split: cool blue-white and warm amber
    if (Math.random() < 0.5) {
        colors[i * 3] = 0.65 + Math.random() * 0.35;   // R
        colors[i * 3 + 1] = 0.75 + Math.random() * 0.25; // G
        colors[i * 3 + 2] = 1.0;                          // B (full)
    } else {
        colors[i * 3] = 1.0;                              // R (full)
        colors[i * 3 + 1] = 0.75 + Math.random() * 0.25; // G
        colors[i * 3 + 2] = 0.35 + Math.random() * 0.15; // B (low)
    }
}

const material = new THREE.PointsMaterial({
    size: 0.5,
    vertexColors: true,
    transparent: true,
    opacity: 0.45,
    sizeAttenuation: true,
    depthWrite: false  // stars render behind everything
});
```

Slow rotation creates parallax depth:

```javascript
function updateStarField(delta) {
    starField.rotation.y += delta * 0.003;
    starField.rotation.x += delta * 0.001;
}
```

## Connection Threads

Dynamic lines between lattice nodes:

```javascript
// Pre-allocate
const positions = new Float32Array(THREAD_COUNT * 2 * 3);  // 2 endpoints * 3 coords
threads = new THREE.LineSegments(geometry, new THREE.LineBasicMaterial({
    color: 0xa8d8ff,
    transparent: true,
    opacity: 0,
    depthWrite: false
}));

// Per-frame update: select node pairs via modular arithmetic
const t = timeline * 0.5;
for (let i = 0; i < THREAD_COUNT; i++) {
    const a = Math.floor((t * 7 + i * 13) % latticeNodes.length);
    const b = Math.floor((t * 11 + i * 17 + 5) % latticeNodes.length);
    const rotatedA = latticeNodes[a].clone().applyQuaternion(lattice.quaternion);
    const rotatedB = latticeNodes[b].clone().applyQuaternion(lattice.quaternion);
    // Write to buffer...
}
```

The prime multipliers (7, 13, 11, 17) create pseudo-random but deterministic pair selection that evolves smoothly.

## Other Lattices (Simultaneity)

30 distant instances for "zoom out" reveal:

```javascript
for (let i = 0; i < 30; i++) {
    const r = 35 + Math.random() * 40;
    const scale = 0.25 + Math.random() * 0.35;
    const geometry = new THREE.IcosahedronGeometry(5 * scale, 1);  // lower subdivision

    otherLattice.userData = {
        brightness: 0.3 + Math.random() * 0.7,
        pulseOffset: Math.random() * Math.PI * 2,
        pulseSpeed: 0.4 + Math.random() * 0.4
    };

    // Each has a particle cloud (20-40 particles)
    const particleCount = Math.floor(20 + Math.random() * 40);
}
```

Per-instance pulsing:

```javascript
const pulse = Math.sin(timeline * lat.userData.pulseSpeed + lat.userData.pulseOffset) * 0.3 + 0.7;
targetOpacity = brightness * pulse * 0.45 * phaseProgress;
```

## CSS Vignette

```css
#vignette {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(ellipse at center, transparent 50%, rgba(5, 5, 8, 0.75) 100%);
    pointer-events: none;
    z-index: 1;
}
```

Darkens edges without affecting the WebGL scene. Adjust the 50% transparent radius and 0.75 opacity for more/less vignette.

## Phase Text Glow

```css
#phase-text {
    text-shadow: 0 0 20px rgba(168, 216, 255, 0.3);
    letter-spacing: 0.1em;
    font-size: 14px;
    transition: opacity 1.5s ease;
}
```

## Author's Note Overlay

```javascript
function setupAuthorsNote() {
    const note = document.getElementById('authors-note');
    setTimeout(() => { note.classList.add('hidden'); }, 14000);  // auto-dismiss
    note.addEventListener('click', () => { note.classList.add('hidden'); });
}
```

CSS transition handles the fade: `opacity: 1 → 0` with `transition: opacity 1.5s ease`.

## Renderer Config

```javascript
renderer = new THREE.WebGLRenderer({
    antialias: true,
    failIfMajorPerformanceCaveat: false,
    powerPreference: 'default'
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
```

- `antialias: true` — smooths edges, essential for wireframes
- `failIfMajorPerformanceCaveat: false` — allow software rendering
- `pixelRatio` capped at 2 — prevents 3x+ rendering on high-DPI devices

## WebGL Fallback

```javascript
try {
    renderer = new THREE.WebGLRenderer({ /* ... */ });
} catch (e) {
    showWebGLError();
    return;
}
if (!renderer.getContext()) {
    showWebGLError();
    return;
}
```

Always check for WebGL context. Show a text-based fallback message, not a blank page.

## Color Palette Guidelines

| Element | Instance Default | Purpose |
|---------|-----------------|---------|
| Background | `#050508` | Near-black (not pure black) |
| Cool color | `#a8d8ff` | Primary hue (lattice, particles at rest) |
| Warm color | `#ffd080` | Accent (active particles, conversation) |
| Core/highlight | `#ffffff` | Lattice vertices, brightest points |
| Text | `#e8e8f0` | Slightly warm white |
| Text dim | `#d0d0e0` | Author's note, secondary text |

The cool/warm pair creates emotional temperature shifts between phases. Choose colors with sufficient contrast against the background.

## Font

```html
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
```

Monospace reinforces the technical/digital aesthetic. For different moods:
- **Space Mono** — technical, digital (Instance default)
- **IBM Plex Mono** — warmer, more approachable
- **JetBrains Mono** — developer-oriented
- **Courier Prime** — typewriter, archival
- **Source Code Pro** — clean, neutral
