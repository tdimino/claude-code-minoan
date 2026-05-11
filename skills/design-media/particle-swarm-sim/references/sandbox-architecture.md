# Sandbox Architecture

The host runtime handles all rendering, input, and security. The behavior function body handles only particle positioning and coloring.

## Scene Graph

```
Scene (background: #050508, FogExp2 density 0.008)
  └── Points (BufferGeometry)
        ├── position: Float32Array(count * 3)
        └── color: Float32Array(count * 3)
```

Single Points mesh. No additional objects, no lights (particles use additive blending, self-luminous).

## BufferGeometry Setup

```javascript
const positions = new Float32Array(CONFIG.particleCount * 3);
const colors = new Float32Array(CONFIG.particleCount * 3);

geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
```

Material: `PointsMaterial` with `vertexColors: true`, `AdditiveBlending`, `depthWrite: false`, `sizeAttenuation: true`.

Initial positions: random uniform on sphere surface (radius 5-15).

## Frame Loop

```
requestAnimationFrame(animate)
  │
  ├── clock.getDelta() → delta
  ├── clock.getElapsedTime() * simSpeed → elapsed
  │
  ├── if (!isPaused && simFunction):
  │     try {
  │       for (idx = 0; idx < count; idx++):
  │         reusableTarget.set(positions[idx*3], ...)
  │         reusableColor.setRGB(colors[idx*3], ...)
  │         simFunction(idx, count, elapsed, SAFE_THREE, target, color, addControl, setInfo, annotate)
  │         if (isFinite(target.x/y/z)) → write positions
  │         if (isFinite(color.r/g/b)) → write colors
  │     } catch (e) {
  │       simFunction = null
  │       show error
  │     }
  │     geometry.attributes.position.needsUpdate = true
  │     geometry.attributes.color.needsUpdate = true
  │
  ├── updateCamera(delta)
  │     auto-orbit if no interaction for 4s
  │     lerp radius toward target
  │     compute spherical → cartesian position
  │     lookAt(0, 0, 0)
  │
  ├── FPS counter (update every 0.5s)
  │
  └── renderer.render(scene, camera)
```

The try/catch wraps the entire loop (not per-particle) to allow V8 JIT optimization of the inner loop body.

## Code Injection Pipeline

```
User types in textarea
  │
  ├── Click "Run" or Cmd+Enter
  │
  ├── validateCode(code)
  │     ├── Stage 1: Forbidden pattern regex scan
  │     ├── Stage 2: new Function(...) syntax check
  │     └── Stage 3: Dry-run with mock values (3 frames × 10 particles, 500ms budget)
  │
  ├── if invalid: show error in error-bar, return
  │
  ├── Clear existing controls, annotations
  ├── Reset simSpeed to 1.0
  │
  └── simFunction = new Function('i', 'count', 'time', 'THREE', 'target', 'color', 'addControl', 'setInfo', 'annotate', code)
```

## Camera System

Spherical coordinates with auto-orbit:

- `cameraTheta` — azimuthal angle (horizontal rotation)
- `cameraPhi` — polar angle (vertical rotation, clamped to [0.1, PI-0.1])
- `cameraTargetRadius` — desired distance (scroll/pinch adjustable)
- `cameraCurrentRadius` — actual distance (lerped toward target at 0.05 rate)
- `autoOrbitSpeed` — rotation speed when no interaction (0.1 rad/sec default)
- `INTERACTION_COOLDOWN` — 4000ms before auto-orbit resumes

## Dynamic Controls System

`addControl(id, label, min, max, initial)`:
1. First call: creates a DOM row with label, range input, and value display
2. Stores in `controlElements[id]` (DOM reference) and `controlValues[id]` (float)
3. Input event listener updates `controlValues[id]`
4. Subsequent calls: returns `controlValues[id]` (O(1) hash lookup)
5. On code re-injection: all controls are removed and recreated by the new sim

## HUD System

- **Title**: `#hud-title` — 14px, uppercase, `#a8d8ff`
- **Description**: `#hud-description` — 11px, `#888`, max-width 300px
- **FPS**: `#hud-fps` — 10px, top-right, updates every 0.5s

## Annotation System

`annotate(id, x, y, z, labelText)`:
1. First call with `id`: creates a `div.annotation-label` appended to body
2. Sets `textContent` to `labelText`
3. Projects `(x, y, z)` through camera using a pre-allocated scratch vector
4. Positions the div at the projected screen coordinates
5. Hides if the point is behind the camera (`projected.z > 1`)
6. On code re-injection: all annotation elements are removed

## Templates

| Template | Features | Use Case |
|----------|----------|----------|
| `sandbox-runtime.html` | Gesture OS, code editor, security validator, HUD, annotations, error bar | Full interactive sandbox |
| `sandbox-minimal.html` | Mouse/touch camera, HUD, controls. No code editor, no gesture, no annotations | Embedding, presentations |

The minimal template includes a `SIM_INJECTION_POINT` sentinel where the default sim string can be replaced with custom behavior code.
