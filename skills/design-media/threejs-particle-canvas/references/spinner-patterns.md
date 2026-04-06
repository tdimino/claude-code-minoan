# Spinner / Loader Patterns — Three.js WebGPU + TSL

Reference for generating parametric particle-trail spinner animations. Based on analysis of Bandinopla's Three.js WebGPU Spinners (threejs-spinners.web.app).

## Architecture

A spinner consists of three parts:

1. **Spinner class** (shared) — extends `THREE.Points`, manages geometry + material
2. **plotFunction** (per-spinner) — maps `progress` (0-1) to `vec3` via parametric curve
3. **config** (per-spinner) — `strokeWidth`, `particleCount`, plus curve-specific params

### Core Pattern

```javascript
import { attribute, float, PI2, time, vec3, mix, select, hash, PI } from "three/tsl";
import * as THREE from "three/webgpu";

class Spinner extends THREE.Points {
  constructor(config, plotFunction) {
    const geometry = new THREE.BufferGeometry();
    const material = new THREE.PointsNodeMaterial({
      blending: THREE.AdditiveBlending,
    });
    super(geometry, material);
    this.rebuild(config, plotFunction);
  }

  rebuild(config, plotFunction) {
    const pointsPerParticle = config.strokeWidth;
    const totalParticles = pointsPerParticle * config.particleCount;

    // Index attribute for GPU-side per-particle logic
    const indices = new Float32Array(totalParticles);
    for (let i = 0; i < totalParticles; i++) indices[i] = i;
    this.geometry.setAttribute("indexAttr", new THREE.BufferAttribute(indices, 1));
    this.geometry.setAttribute("position", new THREE.BufferAttribute(new Float32Array(totalParticles * 3), 3));

    // TSL node graph
    const pointIndex = attribute("indexAttr");
    const particleIndex = pointIndex.toFloat().div(pointsPerParticle).floor();
    const progress = particleIndex.div(config.particleCount);

    // Curve position from plotFunction
    const origin = plotFunction(progress, float(0.7).add(time.mul(3).sin().mul(0.02)), config);

    // Trail animation — traveling bright section
    const animatedProgress = time.div(4).mod(1);
    const trailLength = float(0.3);
    const animationGradient = progress.sub(animatedProgress).add(1).mod(1);
    const insideTrail = animationGradient.lessThanEqual(trailLength);
    const gradient = select(insideTrail, animationGradient.add(0.1), float(config.strokeWidth * 0.7));

    // Particle scatter for stroke width
    const rand = hash(particleIndex);
    const length = float(config.strokeWidth).mul(gradient).mul(pointIndex.toFloat().mod(14).div(14)).mul(0.3);
    const ang = PI2.mul(rand);

    // Final position + color
    this.material.positionNode = origin.add(vec3(ang.cos(), ang.sin(), 0).mul(length));
    this.material.colorNode = mix(vec3(0.01, 0.01, 0.01), vec3(1, 1, 1), insideTrail.toFloat()).mul(3);
    this.material.opacityNode = gradient.add(0.2).mul(animationGradient.div(2));
    this.material.needsUpdate = true;
  }
}
```

### Key Techniques

**TSL (Three Shading Language)**: Node-based shader graph for WebGPU. All particle position/color computation runs on GPU — no CPU-side animation loop updating positions per frame. The `time` node provides built-in animation.

**Trail animation**: The bright "head" of the spinner travels along the curve via modular arithmetic: `progress.sub(time.div(4).mod(1)).add(1).mod(1)`. Particles behind the head fade via gradient multiplication. This creates the comet-tail appearance.

**Stroke width**: Each point in the curve spawns multiple particles at random angles around the curve position, creating a thick stroke. `hash(particleIndex)` generates deterministic randomness on the GPU.

**Additive blending**: `THREE.AdditiveBlending` on `PointsNodeMaterial` creates the white-on-dark glow. Overlapping particles brighten rather than occlude.

**Particle count**: 100,000 is the default. Because computation is GPU-driven via TSL, this is performant. For smaller/simpler spinners, 50,000 works. For particle sphere effects, 200,000+.

## Config Schema

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `strokeWidth` | float | 0.2-0.3 | Trail thickness (also controls scatter) |
| `particleCount` | int | 100000 | Total particles distributed along curve |
| *curve-specific* | varies | varies | See parametric-curves.md |

## Output Formats

**ES Module** (primary): Exports `Spinner` class + `plotFunction` + instantiated `spinner`. Designed for import into existing Three.js WebGPU projects.

**Self-contained HTML** (alternative): Full HTML page with WebGPU renderer, import map for Three.js, and the spinner centered on a dark background. Use for demos, loading screens, or standalone use.

### Import Map for HTML Output

```html
<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.175.0/build/three.webgpu.js",
    "three/tsl": "https://cdn.jsdelivr.net/npm/three@0.175.0/build/three.tsl.js",
    "three/webgpu": "https://cdn.jsdelivr.net/npm/three@0.175.0/build/three.webgpu.js"
  }
}
</script>
```

### Minimal HTML Scaffold

```html
<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>body { margin: 0; background: #060508; overflow: hidden; }</style>
<!-- import map here -->
</head><body>
<script type="module">
import * as THREE from "three/webgpu";
// Spinner class + plotFunction here
const renderer = new THREE.WebGPURenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x060508);
const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 100);
camera.position.z = 1;
scene.add(spinner);
function animate() { renderer.renderAsync(scene, camera); requestAnimationFrame(animate); }
animate();
window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
</script></body></html>
```

## Anti-Patterns

- Never use WebGL renderer (`THREE.WebGLRenderer`) — spinners require WebGPU for TSL node materials
- Never update particle positions on CPU per frame — TSL handles this on GPU via `time` node
- Never use `ShaderMaterial` with GLSL — use `PointsNodeMaterial` with TSL nodes
- Never omit `AdditiveBlending` — the glow effect depends on it
- Never use fewer than 10,000 particles — the trail loses definition
- Never omit the WebGPU capability check — fall back to a CSS spinner if unavailable
