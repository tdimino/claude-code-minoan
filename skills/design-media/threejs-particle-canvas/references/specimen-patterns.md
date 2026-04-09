# Specimen Patterns — Mode 4 Anatomy

Architectural map of `assets/butterfly-specimen-source.html`. The source is a vanilla port of [celescript.dev/experiments/3d-butterfly](https://celescript.dev/experiments/3d-butterfly). React Three Fiber and drei stripped; the flight physics, lighting, animation pipeline, and post-FX are preserved with every constant from the original bundle (`ButterflyScene`, chunk `128.64bb229c36552b0d`). Default model is Three.js's `Parrot.glb` — stable jsdelivr URL, CC0, animated rig.

## 1. HTML/CSS Structure

**What it does**: Minimal canvas with three chrome elements — instructions (top-left), loading indicator (center, fades out after first frame with specimens), WebGL fallback (hidden unless triggered).

**Pattern**: Uses `100svh` (small viewport height) instead of `100vh` so mobile browsers with dynamic chrome don't crop the scene. Loading element auto-hides via `.hidden` class once `loadModelAndSpawn` resolves.

**Adaptation**: Replace the instructions text for your species. If you add any permanent UI, keep it under `z-index: 3` so specimens always appear to be "in front" of the HTML layer.

## 2. Config Block

**What it does**: Single top-level `CONFIG` object defines model URL, count, behaviors, scales, color shifts, lighting, camera, mobile downscale, release decay time, and FX mode.

**Pattern**: `modelUrl` is a CDN URL. `scales` array is per-instance with different values because the original celescript butterflies use slightly different sizes (0.0104, 0.0096, 0.0112) — randomization via constants rather than `Math.random()` so the scene is deterministic. `colorShifts` array sets per-instance HSL tints; 0 = no tint, 0.6 = cool, 0.05 = warm.

**Adaptation**: Swap `modelUrl` for any rigged glTF/glb. Adjust `scales` by model size — parrots need larger values than butterflies. For stationary meditative scenes, set all `behaviors` to `'wander'`; for kinetic scenes, make them all `'followMouse'`.

## 3. Lights

**What it does**: Four-light cinematic setup — ambient (even base illumination), warm key, cool fill, warm rim.

**Pattern**: Copies celescript exactly:
- `ambientLight` intensity 2 (high base — the model is small so it needs lots of ambient to stay visible)
- Key directional from `[3, 5, 5]` intensity 3, pure white
- Fill directional from `[-3, -2, -5]` intensity 1.5, color `0x889bff` (cool blue)
- Rim directional from `[0, -3, 3]` intensity 1, color `0xff8844` (warm orange)

The warm/cool tension in the lighting complements the phosphor-vigil's warm/cool shader tints — both layers reinforce each other.

**Adaptation**: Don't cut lights to "simplify". Each one does distinct work: ambient keeps shadows readable, key gives form, fill prevents silhouetting, rim gives separation against the dark background.

## 4. Model Loading

**What it does**: `loadModelAndSpawn()` uses `GLTFLoader` (from `three/addons/loaders/GLTFLoader.js`) to fetch the model, then clones it `specimenCount` times with `SkeletonUtils.clone` (from `three/addons/utils/SkeletonUtils.js`) to preserve skeleton bindings.

**Pattern**:
1. Load the glTF once
2. Extract `gltf.scene` and `gltf.animations`
3. For each specimen: clone via SkeletonUtils, apply per-instance emissive tint by traversing meshes and cloning materials, apply per-instance scale (downsized by `mobileScale` on small screens), construct a `Specimen` with the cloned root and the shared animation clips

**Why SkeletonUtils.clone**: Plain `THREE.Object3D.clone()` doesn't properly rebind the skeleton for skinned meshes — each cloned instance would share the same bone matrices and all flap in lockstep. `SkeletonUtils.clone` creates independent skeletons, which is what lets each specimen have its own `timeScale`.

**Adaptation**: For un-rigged models (no animations), skip the AnimationMixer — the specimens will still move but won't flap. For models with multiple animation clips, edit the clip-selection line in `Specimen.constructor`.

## 5. Specimen Physics Class

**What it does**: Self-contained class handling flight behavior. Each specimen owns position, velocity, target, wander baseline, follow-blend state, and animation mixer.

**The update loop** (order matters):

1. **Compute viewport extent at z=0**: `halfW = tan(fov/2) * |cameraZ| * aspect` — what's the world-space rectangle the camera can see at the specimen's plane
2. **Follow blend**: In `followMouse` mode, blend transitions from 1 (chasing) to 0 (wandering) over `releaseDecayTime` seconds when the mouse leaves. Wander specimens keep blend at 0
3. **Target point**: Project NDC pointer to 3D via `unproject`, compute ray-plane intersection at z=0, clamp to 90% of viewport in X / 70% in Y. For wander specimens, use a baseline position + low-frequency sine/cosine jitter (`0.3*sin(0.7*t+17*i) + ...`) that regenerates every 2–5 seconds
4. **Acceleration**: Toward target, magnitude `(5+3m) + dist*(2+m)`. Blend factor `m` makes chasing stronger when following mouse
5. **Soft-wall repulsion**: When `|x| > 0.6*halfW`, a quadratic push-back force. Prevents specimens from flying offscreen
6. **Velocity integration**: Apply accel * dt, then damp with `exp(-(5-m)*dt)` — more damping in wander mode
7. **Clamp velocity**: `maxV = 5 + 3m` (faster when chasing)
8. **Position integration**: `position += velocity * dt`
9. **Face direction of motion**: Yaw-only rotation via `atan2(vx, vy) - PI/2`
10. **Modulate flap speed**: Smooth velocity magnitude into `action.timeScale`. Faster flight = faster wing flap, matching celescript's behavior
11. **Contribute to shared velocity**: `sharedVelocity += 0.012 * velocity * smoothedSpeed` — feeds the phosphor-vigil feedback pass

**Key constants** (all from celescript, don't change without reason):
- `0.8s` release decay — the "let go" time
- `5 + 3m` base acceleration and max velocity — the `m` multiplier makes chasing feel responsive
- `60% inner / 90% outer` wall repulsion zones — soft falloff
- `-25 * sign * r^2` repulsion magnitude — strong enough to deflect but not bounce

**Adaptation**: To add a third behavior (e.g., `'formation'`), extend the target-computation block with a new branch. Keep the acceleration/integration math identical so the scene remains stable.

## 6. Mouse Projection to z=0

**What it does**: Converts NDC pointer coordinates (-1 to +1) to world-space coordinates on the z=0 plane, so specimens fly to exactly where the cursor points.

**Pattern**:
```javascript
const mouseWorld = new THREE.Vector3(pointer.x, pointer.y, 0.5);
mouseWorld.unproject(camera);
const rayDir = mouseWorld.sub(camera.position).normalize();
const tOnPlane = -camera.position.z / rayDir.z;
const target = camera.position.clone().add(rayDir.multiplyScalar(tOnPlane));
```

This is the standard "ray from camera through pointer, intersect z=0 plane" formula. The `unproject` call uses the camera's projection matrix, so it works under any FOV or aspect.

**Adaptation**: For a scene anchored at a different depth, replace `-camera.position.z / rayDir.z` with `(planeZ - camera.position.z) / rayDir.z`. For scenes using an orthographic camera, skip the ray math entirely — the unprojected point is already the target.

## 7. Animation Mixer

**What it does**: Per-specimen `AnimationMixer` drives the wing/wing-equivalent animation at a velocity-modulated speed.

**Pattern**: `this.mixer = new THREE.AnimationMixer(root); this.action = this.mixer.clipAction(clip); this.action.setLoop(LoopRepeat, Infinity); this.action.play();` — standard three.js animation setup. The twist is `timeScale`: instead of a fixed value, it's recalculated every frame from the specimen's speed:

```javascript
this.action.timeScale = (2 + 0.3 * this.index) + this.smoothedSpeed * 0.3;
```

`smoothedSpeed` is the velocity magnitude low-pass-filtered at 0.1/frame, so sudden direction changes don't cause flap jitter.

**Adaptation**: For models with multiple clips (idle, walk, fly), add a clip-selection layer that crossfades based on speed. For un-animated models, don't construct the mixer — the specimen will still move.

## 8. Shared Velocity Channel

**What it does**: A single `THREE.Vector2` that all specimens write to each frame. The phosphor-vigil `setVelocity()` reads it, which makes the feedback trails align with the average flight direction.

**Pattern**: Global `sharedVelocity` vector, zeroed + decayed each frame (`multiplyScalar(0.85)`), then each specimen's `update()` adds its weighted contribution. The decay prevents runaway accumulation; the weighting (`0.012 * velocity * smoothedSpeed`) matches celescript's `h.addVelocity(...)` formula.

**Adaptation**: For a single-specimen scene, just copy its velocity directly. For many specimens, the averaging is automatic — more specimens = more smoothing.

## 9. Phosphor Vigil FX Integration

**What it does**: The default for Mode 4. When `CONFIG.fx === 'phosphor-vigil'`, a `PhosphorVigil` is constructed after renderer setup and used as the render entry point in `animate()`.

**Pattern**: Single branch in `animate()`:
```javascript
if (fx) {
    fx.setVelocity(sharedVelocity);
    fx.render(scene, camera, elapsed);
} else {
    renderer.render(scene, camera);
}
```

Unlike Mode 3 where FX is optional, Mode 4's trails ARE the aesthetic. Disabling FX gives you bare specimens in a void — scientific but not cinematic.

**Adaptation**: If you need the plain scene for debugging, set `CONFIG.fx = 'none'`. For even more dramatic trails, pass `{ feedbackStrength: 0.95 }` to the constructor — but don't exceed 0.98 or trails go unstable.

## 10. Mobile Handling

**What it does**: On screens ≤ 768px, all specimen scales are multiplied by `CONFIG.mobileScale` (0.65) so they don't fill the whole screen. Touch events mimic mouse events; `touchend` fires the release behavior the same way mouse leave does.

**Pattern**: `window.matchMedia('(max-width: 768px)')` checked at init and on resize. All touch handlers use `passive: true` for smooth scroll.

**Adaptation**: For tablet-first scenes, raise the breakpoint to 1024px. For phone-only content, set `mobileScale` to 0.5 and increase specimen count for a busier field of view.

## Validator Contract

`scripts/validate_specimen.py` enforces the imports (GLTFLoader, SkeletonUtils, AnimationMixer, PhosphorVigil), the Specimen class, the mouse unproject, soft-wall repulsion, velocity clamping, animation timeScale modulation, shared velocity channel, resize handling, and anti-patterns (no React, no drei, no pure-black background). Any major structural removal will fail a check.

## Anti-Patterns

- Never use drei (`useGLTF`, `useAnimations`) — import directly from `three/addons/`
- Never clone skinned meshes with plain `.clone()` — use `SkeletonUtils.clone`
- Never hardcode flap speed — derive from velocity magnitude via `smoothedSpeed`
- Never skip the soft-wall repulsion — specimens will fly offscreen and the scene looks broken
- Never exceed `0.012 * velocity * smoothedSpeed` per-specimen shared-velocity contribution — the feedback trail becomes a whiteout
- Never construct specimens before `gltf.scene` loads — the skeleton won't exist yet
- Never use pure black background — `#050508` only
- Never inline the phosphor-vigil shaders — import from `phosphor-vigil.js`
