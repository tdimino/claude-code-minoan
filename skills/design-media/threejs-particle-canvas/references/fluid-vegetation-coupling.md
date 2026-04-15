# Fluid-Vegetation Coupling

Interactive botanical scene where a 2D Navier-Stokes fluid simulation on
the GPU drives three vegetation deformation systems and a particle field
simultaneously. Source: botanics.sujen.co (Astro + Three.js + GSAP + Lenis).

## GPU Navier-Stokes Fluid Simulation

- Pipeline: advection → divergence → pressure → curl/vorticity
- Mouse/touch velocity injection via splat function
- 2D texture-based solver on GPU
- Fluid velocity field feeds into 3 deformation systems + particles

## Fluid → Vegetation Deformation (3 systems)

### Grass Wind (Cascaded Bezier)

- 5-control-point rotation cascade
- Progressive angle dampening: 100% → 80% → 30%
- Baked noise offsets prevent uniform motion
- Fluid velocity injection for interactive responsiveness
- Function: `grassWindPointsOffsetBakedWithFluid()`

### Tree Wind (Pseudo3D Noise)

- Pseudo3dNoise-driven deformation
- Y-threshold gating with power-curve falloff
- Function: `applyTreeWind()`

### Flower Wind (Single-Pivot)

- Simpler deformation with fluid velocity
- Function: `flowerWindOffsetWithFluid()`

## FBO Ping-Pong GPU Particles

- 500 particles, position/velocity float render targets
- Radial spawn distribution
- Drift forces: swirl (sinusoidal orbital) + gravity + fluid velocity
- PCF shadow sampling on point sprites (rare — most skip shadows)
- Fade by age, height, and lateral drift

```javascript
// FBO ping-pong pattern
const rtA = new THREE.WebGLRenderTarget(size, size, { type: THREE.FloatType });
const rtB = new THREE.WebGLRenderTarget(size, size, { type: THREE.FloatType });
// Swap each frame: read from A, write to B, then flip
```

## 4-Pass Postprocessing Pipeline

1. **Bloom**: luminance threshold → 5-tap Gaussian blur → screen blend
2. **Light Trails**: temporal accumulation, 0.94 decay, additive composite
3. **Screen Paint**: fluid velocity → 4-color gradient shimmer, ACES tone mapping
4. **Standard render pass** (base)

## Asset Pipeline

- KTX2 compressed textures, DRACO compressed geometry
- Astro islands for progressive hydration
