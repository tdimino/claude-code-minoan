# Three.js and 3D Components — VELVET CATALOGUE

Two WebGL canvases (React Three Fiber), one CSS-transform tilt effect (Framer Motion), and two SVG chart components.

## Component Summary

| Component | Renderer | Location | Pages |
|-----------|----------|----------|-------|
| ProjectorDust | R3F / WebGL | `components/atmosphere/` | All (global in `layout.tsx`) |
| OracleSmoke | R3F / WebGL | `components/claudius/` | Claudius only |
| TiltCard | CSS transform | `components/archive/` | Archive |
| TasteRadar3D | SVG | `components/taste/` | Taste |
| DecadeTimeline | SVG | `components/taste/` | Taste |

---

## ProjectorDust

**File:** `components/atmosphere/ProjectorDust.tsx`
**Wrapper:** `components/atmosphere/DustWrapper.tsx` (dynamic import, `ssr: false`)
**Mounted in:** `app/layout.tsx` — renders on every page as a fixed overlay at `z-[1]`

400 particles (150 on mobile). Single `<points>` with `Float32Array` positions. `pointsMaterial` with `AdditiveBlending`, `size=0.03`, `opacity=0.15`.

### Animation

`useFrame` updates positions directly on the typed array each frame:
- X/Z: sinusoidal drift
- Y: constant upward drift + scroll velocity contribution
- Wraps vertically at ±5

### Scroll Responsiveness

`scroll` event listener (passive) computes `|delta| * 0.01`, clamped to 1.5. Decays at 0.92 per 50ms tick — brief velocity burst on fast scrolls that fades exponentially.

### Performance

| Setting | Value | Rationale |
|---------|-------|-----------|
| `dpr` | 1 | Retina doubling wastes GPU for invisible particle quality |
| `powerPreference` | `"low-power"` | Requests integrated GPU |
| `antialias` | false | Irrelevant for point sprites |
| `alpha` | true | Canvas composites transparently over HTML |
| Pointer events | Disabled via CSS `pointerEvents: "none"` | Canvas must never intercept clicks |

---

## OracleSmoke

**File:** `components/claudius/OracleSmoke.tsx`
**Wrapper:** `components/claudius/OracleSmokeWrapper.tsx` (dynamic import, `ssr: false`)
**Prop:** `streaming: boolean`

600-particle system orbiting an octahedron lattice with custom GLSL shaders. Two states driven by `streaming` prop.

### States

| Parameter | Dormant (`streaming=false`) | Active (`streaming=true`) |
|-----------|---------------------------|--------------------------|
| Particle target | Scattered sphere (r=5) | Octahedron vertices (r=3) with jitter |
| Color | `#6b5d4a` (foxing) | `#d4a017` (amber) |
| Alpha | 0.12 | Up to 0.57 |
| Wander amplitude | 0.4 | 0.16 |
| Rotation speed | 0.06 rad/s | 0.10 rad/s |
| Lattice wireframe | Invisible (opacity 0) | Visible (opacity 0.12) |
| Thread connections | Invisible | Visible (opacity 0.18) |

### Activation

First-order IIR low-pass filter on `activation.current` ref:
- Activating rate: 0.02 (~2.5s to 95% at 60fps)
- Deactivating rate: 0.008 (~6s)
- Intentionally asymmetric — response fast, decay slow

### Custom Shaders

Vertex shader: per-particle size attenuation (`aSize * (200.0 / -mv.z)`), passes vertex color and `aAlpha` to fragment.

Fragment shader: soft circular particle via `smoothstep(1.0, 0.15, d)` on `gl_PointCoord`. Inner threshold of 0.15 creates a slightly harder core than a pure Gaussian.

### Geometry

- **Particle targets:** `OctahedronGeometry(3, 2)` — deduplicated vertices, particles assigned to random vertices with ±0.4 jitter
- **Lattice wireframe:** `EdgesGeometry(OctahedronGeometry(3, 1))` — lower subdivision for visual clarity
- **Threads:** 50 line segments between random vertex pairs (distance > `LATTICE_R * 0.5`)
- **Disposal:** `useEffect` cleanup disposes `threadGeo` and `latticeGeo`

### Buffer Updates

Three `useRef<BufferAttribute>` refs for position, color, alpha. Written directly to typed arrays each frame with `needsUpdate = true`. Avoids React re-renders for per-frame geometry mutations.

### Seeded PRNG

Park-Miller LCG (`seeded(42)`) for deterministic particle positions across renders.

### Reduced-Motion Fallback

Checks `window.matchMedia("(prefers-reduced-motion: reduce)")` on mount. If true, renders a static `<div>` with radial gradient amber glow. No WebGL canvas.

---

## TiltCard

**File:** `components/archive/TiltCard.tsx`
**Renderer:** Framer Motion CSS transforms — no WebGL

Parallax 3D tilt on hover. `motion.div` with `perspective: 800px`, `rotateX`/`rotateY` driven by mouse position.

| Parameter | Value |
|-----------|-------|
| Max rotation | 5 degrees |
| Spring stiffness | 300 |
| Spring damping | 30 |
| Spring mass | 0.5 |
| Hover scale | 1.02x |

Disabled when `useReducedMotion()` returns true or `window.innerWidth < 480`.

---

## TasteRadar3D

**File:** `components/taste/TasteRadar3D.tsx`
**Wrapper:** `components/taste/TasteRadar3DWrapper.tsx`
**Renderer:** SVG (despite the "3D" name)

Radar chart of genre lane averages (up to 8 lanes, minimum 3). `viewBox` uses asymmetric padding (`PAD_X=70`, `PAD_Y=10`) to prevent label clipping.

Rendered layers: grid polygons at r=1..5, axis lines, filled data polygon (`fillOpacity=0.1`, amber stroke), vertex dots, labels (lane name + average).

---

## DecadeTimeline

**File:** `components/taste/DecadeTimeline.tsx`
**Renderer:** SVG

Horizontal bar chart showing film count by decade. Two-layer opacity encodes watched/total ratio: total bar at 15% amber, watched portion at 55% amber. Shown side-by-side with TasteRadar3D in 60/40 split.

---

## GPU Considerations

- **Two WebGL contexts** on the Claudius page (ProjectorDust + OracleSmoke). Modern browsers support 8-16 contexts; two is well within range.
- **Additive blending** on both canvases — fragments accumulate light, depth buffer stays clean.
- **`dpr={1}`** and **`powerPreference: "low-power"`** on both canvases — prevents retina GPU cost and selects integrated GPU on dual-GPU machines.
- **No raycasting** — pointer events disabled via CSS on both canvas containers.
