# Mode 5: Vinyl Showcase — Technical Patterns

Distilled from OMMA's 3D Vinyl with Camera Reflection demo. Source preserved at `references/vinyl-bundle-annotated.js` (81KB, unminified).

## System 1: Camera-as-Environment Mapping

The hero technique. A webcam feed becomes the scene's environment map, making the vinyl record reflect the viewer's face and surroundings.

### Pipeline

```
getUserMedia (640x480, 60fps)
  → THREE.VideoTexture (SRGBColorSpace, LinearFilter)
  → 256x256 blur canvas (CSS filter: blur + brightness)
  → THREE.CanvasTexture → BackSide SphereGeometry(50, 24, 16) ("envSphere")
  → THREE.CubeCamera(0.1, 100, CubeRenderTarget(128, HalfFloat))
  → PMREMGenerator.fromCubemap() → scene.environment + per-material envMap
```

### Key Details

- **Blur canvas**: 256x256 intermediate canvas applies CSS `filter: blur(${blur*20}px) brightness(${brightness})` before drawing video frame. Prevents harsh reflections.
- **Texture zoom**: `videoTexture.repeat.x = zoom; repeat.y = -zoom` with matching offset calculations. Default zoom 6x crops the webcam to center on the face.
- **CubeCamera update interval**: Every 2 frames during interaction, every 4 frames idle. Hide the vinyl group before capturing to avoid self-reflection.
- **PMREM regeneration**: `pmremGenerator.fromCubemap(cubeRenderTarget.texture)` produces filtered envMap. Dispose previous envMap each cycle.
- **envSphere layer**: Set to layer 1 (`envSphere.layers.set(1)`), CubeCamera enables layer 1 (`cubeCamera.layers.enable(1)`). This ensures the environment sphere is only visible to the CubeCamera, not the main render.
- **Fallback**: If `getUserMedia` fails, paint a gradient canvas (512x512, blue tones with white dots) as the envSphere texture.

### Adaptive Lighting from Luminance

An 8x8 canvas samples the video feed to compute average luminance. The luminance drives:
- `ambientLight.intensity = 1.2 * (0.5 + luminance)`
- `directionalLight.intensity = 3 * (0.7 + (1-luminance)*0.5)`
- `renderer.toneMappingExposure = 1.8 * (0.7 + luminance*0.6)`

This makes the scene naturally brighter in bright rooms and moodier in dark ones.

## System 2: Procedural Canvas Textures

Four texture generators produce normal maps and roughness maps at 1024px resolution. All draw in **normal-map color space** where RGB(128, 128, 255) is a flat surface normal.

### Groove Normal Map

`generateGrooveNormalMap(count, depth, width)` — concentric arcs from inner radius (14% of canvas) to outer radius (49%). Each groove is two strokes:
1. Primary: `rgb(128+intensity, 128, 255)` at full width
2. Shadow: `rgb(128-intensity, 128, 255)` at 60% width, offset by half-width

Intensity = `floor(60 * depth)`. Creates the characteristic vinyl groove ridges.

### Groove Roughness Map

`generateGrooveRoughnessMap(count)` — matching roughness variation. Base fill `#333`, groove strokes `#666` at 1.5px width.

### Scratch Normal Map

`generateScratchNormalMap(density, depth, length, params)` — three scratch layer types (the OMMA source has 7 types in the settings panel, but the core generator uses 3):

| Type | Count | Arc Length | Line Width | Alpha |
|------|-------|-----------|------------|-------|
| Arcs | `density * arcMul` | `(rand*0.15 + 0.02) * length * 8` | `rand*0.5 + 0.1` | `rand * arcAlpha + arcAlpha*0.33` |
| Hairlines | `density * hairMul` | `(rand*0.08 + 0.01) * length * 6` | `0.15 + rand*0.2` | `rand * hairAlpha + hairAlpha*0.2` |
| Nicks | `density * nickMul` | linear, `(rand*0.2+0.05)*length*S*0.08` | `rand*0.35 + 0.1` | `rand * nickAlpha + nickAlpha*0.33` |

All constrained between inner radius (14%) and outer radius (49%) of the disc.

### Scratch Roughness Map

`generateScratchRoughnessMap(density, length, params)` — same geometry as normal map but drawn in white-on-black with low alpha values (0.02-0.15).

## System 3: Material Stack

### Base Disc

```javascript
MeshPhysicalMaterial({
  color: 0x080808,          // near-black vinyl
  metalness: 1,              // scroll-interpolated
  roughness: 1,              // scroll-interpolated
  envMapIntensity: 3.5,      // scroll-interpolated
  clearcoat: 0.91,           // scroll-interpolated
  clearcoatRoughness: 1,     // maps to feedRoughness
  reflectivity: 1,
  ior: 1.8,
  specularIntensity: 1,
  specularColor: 0xffffff,
  normalMap: grooveNormalTex,
  normalScale: Vector2(0.8, 0.8),
  roughnessMap: grooveRoughTex,
  side: DoubleSide
})
```

Geometry: `CylinderGeometry(2, 2, 0.012, 128)` — thin disc, high segment count for smooth edge.

### Scratch Overlay

A second cylinder (0.013 thick, 64 segments) with:
- `transparent: true, opacity: 0.35`
- `depthWrite: false`
- `metalness: 0.9, roughness: 0.1` (shinier than base)
- Scratch normal + roughness maps

The slight thickness difference and `depthWrite: false` prevent z-fighting.

### Labels (A-side / B-side)

`CircleGeometry(0.5, 64)` with `MeshPhysicalMaterial`:
- `iridescence: 0.35-0.4`
- `iridescenceIOR: 1.8-1.9`
- `iridescenceThicknessRange: [100, 400]` (animated in render loop)
- `polygonOffset: true, polygonOffsetFactor: -1` (prevents z-fighting with disc)
- Procedural 2048px canvas texture with seeded random label art

### Spindle Hole

`CylinderGeometry(0.04, 0.04, 0.02, 16)` — black standard material.

### Group Hierarchy

```
vinylGroup (position, scale, rotation.x/z)
  └─ spinPivot (rotation.y = spin + scratch)
       ├─ disc
       ├─ scratchDisc
       ├─ label (A-side, y=+0.0065, rotation.x=-PI/2)
       ├─ bSideLabel (y=-0.0065, rotation.x=+PI/2)
       └─ spindleHole
```

The two-group hierarchy separates scroll-driven transforms (vinylGroup) from spin rotation (spinPivot).

## System 4: Scroll-Driven Keyframe Interpolation

### Property Bag

40+ properties interpolated per frame: position (posX/Y/Z), offset (offsetX/Y/Z), rotation (rotX/Y/Z), scale, spinSpeed, material properties (roughness, metalness, clearcoat, envIntensity), camera feed (reflZoom, feedRoughness, feedBlur, feedBrightness), HDR orientation (hdrRotX/Y/Z), groove parameters, scratch parameters.

### Interpolation

```javascript
function getScrollProgress() {
  const scrollY = window.scrollY;
  const docH = document.documentElement.scrollHeight - window.innerHeight;
  if (docH <= 0) return 0;
  return (scrollY / docH) * (keyframes.length - 1);
}

function applyScrollKeyframe(progress) {
  const idx = Math.floor(progress);
  const t = progress - idx;
  const kfA = keyframes[Math.min(idx, keyframes.length - 1)];
  const kfB = keyframes[Math.min(idx + 1, keyframes.length - 1)];
  const ease = t * t * (3 - 2 * t);  // smoothstep
  for (const k of KF_PROPS) {
    settings[k] = lerp(kfA[k], kfB[k], ease);
  }
  // Apply to materials, transforms, textures...
}
```

Each section (`min-height: 100vh`) maps to one keyframe. Scrolling between sections smoothly interpolates all properties.

## System 5: Drag-to-Scratch Interaction

### Hit Test

Raycaster against `[disc, label, bSideLabel, scratchDisc]`. On hit, capture pointer.

### Angular Delta

Project vinyl group world position to screen space. Compute angle from projected center to pointer: `Math.atan2(clientY - center.y, clientX - center.x)`. Delta between frames drives `scratchVelocity`.

### Velocity with Friction

```
scratchVelocity = -delta * SCRATCH_SENSITIVITY  (2x)
scratchOffset += scratchVelocity
// On release:
scratchVelocity *= SCRATCH_FRICTION  (0.92 per frame)
// Settles when |velocity| < 0.0003
```

### Drag Freeze

During drag, all scroll-driven transforms freeze at their values when drag started. Position, rotation, scale, camera lookAt all lock to `dragFrozen*` snapshots.

## System 6: Vinyl Audio Engine

### Architecture

```
AudioContext
  ├─ Music Source (BufferSource, looped)
  │   → scratchMidEQ (peaking, 1800Hz)
  │   → musicLPF (lowpass, 180-22kHz)
  │   → musicGain (0.04-0.5)
  │   → masterGain → destination
  ├─ Crackle Source (noise buffer, looped)
  │   → crackleFilter (bandpass, 3kHz)
  │   → crackleGain (0-0.3)
  │   → masterGain
  └─ Needle Hiss (pink noise, looped)
      → needleFilter (highpass, 4kHz)
      → needleGain (0-0.025)
      → masterGain
```

### Turntable Physics

- **Base rate**: 33⅓ RPM = `33.333/60 * 2π` rad/sec
- **Smoothed rate**: Inertia-based blending. Drag: 0.22, brake: 0.035, motor: 0.07
- **Wow**: `sin(phase) * 0.0015 * min(|rate|, 1)` at 0.4 Hz
- **Flutter**: `sin(phase) * 0.0004 * min(|rate|, 1)` at 6.5 Hz
- **Reverse playback**: Pre-computed reversed buffer, direction flip when rate crosses zero

### Crackle Generation

Noise buffer (4 seconds) with three probability tiers:
- 0.3% chance: click transient (0.3-1.0 amplitude, 0.2-1.2ms decay)
- 0.7% chance: pop (0.15 amplitude, single sample)
- 99% chance: floor noise (0.008 amplitude)

### Lowpass Sweep

During scratching, the lowpass filter frequency drops proportionally to how far the rate deviates from normal: `LPF_MIN * (LPF_MAX/LPF_MIN)^ratio`. This produces the characteristic "underwater" sound when the record slows.

## Page Layout Pattern

```css
#three-canvas { position: fixed; inset: 0; z-index: 0; pointer-events: auto; }
.page-section { position: relative; min-height: 100vh; z-index: 1; pointer-events: none; }
.page-section .content { pointer-events: auto; }
```

The Three.js canvas fills the viewport as a fixed background. Content sections scroll over it, with pointer events selectively re-enabled for interactive content. The canvas retains `pointer-events: auto` for drag interaction.

## 5-Light Rig

| Light | Type | Color | Intensity | Position |
|-------|------|-------|-----------|----------|
| Ambient | AmbientLight | white | 0.6 (adaptive) | — |
| Main | DirectionalLight | white | 2.0 (adaptive) | (5, 8, 5) |
| Fill | DirectionalLight | #889AAB | 0.6 | (-5, 3, -5) |
| Rim | PointLight | #AAAAFF | 0.8 (pulsing) | (0, -3, 3) |
| Top | PointLight | white | 0.5 | (0, 5, 0) |

Rim light pulses: `0.8 * (0.8 + sin(time*2) * 0.2)`.

## Label Art Generation

Procedural on 2048x2048 canvas with seeded random (`seed * 16807 % 2147483647`). Elements:
- Radial gradient base (warm A-side: FFD166→D63031, cool B-side: 6C5CE7→1B1464)
- Color splash overlays (pink/blue for A, cyan/magenta for B)
- 12,000 grain particles
- Concentric border rings (960px, 945px, 930px)
- 72 tick marks around edge (major every 6th)
- 60-bar waveform visualization
- Geometric motifs (play triangle, diamond, ellipse)
- Radial lines (32 spokes, major every 4th)
- Dot pattern ring (36 dots at r=550)
- Cross markers at 6 positions
- Arc text (top and bottom) via character-by-character rotation
- Spindle hole with metallic gradient
- Edge wear via `destination-out` composite (250 elliptical chips)
