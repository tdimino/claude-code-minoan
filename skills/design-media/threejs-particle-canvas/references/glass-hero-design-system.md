# Glass Hero Design System

Design system reference for Mode 6 (Glass Hero) — physically-accurate 3D glass panes with refraction, dispersion, and iridescence over hero content. Deconstructed from kaolti's glass-hero experiment (thisiswhitespace.com). All parameters map to Three.js MeshPhysicalMaterial properties.

## Conceptual Framework

Five physics terms define the glass vocabulary:

| Term | Definition | Visual Signature |
|------|-----------|------------------|
| **Iridescence** | Thin-film interference between close surfaces splits light by wavelength | Rainbow color shift at viewing angle |
| **Index of Refraction (IOR)** | How strongly light bends crossing a boundary (vacuum 1.0, water 1.33, glass ~1.5, diamond 2.42) | Distortion of content behind glass |
| **Dispersion** | IOR varies by wavelength — red/green/blue refract at different angles | Chromatic fringe at glass edges |
| **Transmission** | Fraction of light that passes through | See-through clarity vs opacity |
| **Roughness** | Surface micro-bumpiness (0 = mirror, 1 = matte) | Sharp vs frosted see-through |

## Glass Material Parameters

Three.js MeshPhysicalMaterial properties in four groups.

### Core Glass

| Parameter | Prop | Default | Range | Purpose |
|-----------|------|---------|-------|---------|
| IOR | `ior` | 2.14 | 1.0–2.5+ | Refraction bend strength |
| Thickness | `thickness` | 1.35 | 0–5+ | Volume for absorption |
| Dispersion | `dispersion` | 0.415 | 0–1 | Chromatic fringe intensity |
| Roughness | `roughness` | 0.41 | 0–1 | Surface blur |
| Metalness | `metalness` | 0.00 | 0–1 | Metal vs dielectric |
| Transmission | `transmission` | 1.00 | 0–1 | See-through amount |

### Surface Finish

| Parameter | Prop | Default | Range | Purpose |
|-----------|------|---------|-------|---------|
| Clearcoat | `clearcoat` | 1.00 | 0–1 | Extra glossy layer |
| Clearcoat Roughness | `clearcoatRoughness` | 0.59 | 0–1 | Clearcoat blur |
| Env Map Intensity | `envMapIntensity` | 0.00 | 0–5+ | Environment reflection |

### Iridescence

| Parameter | Prop | Default | Range | Purpose |
|-----------|------|---------|-------|---------|
| Iridescence | `iridescence` | 1.00 | 0–1 | Film effect strength |
| Iridescence IOR | `iridescenceIOR` | 2.34 | 1.0–3.0 | Film refractive index |
| Iridescence Thickness Min | `iridescenceThicknessRange[0]` | 80 | nm | Thin-film min |
| Iridescence Thickness Max | `iridescenceThicknessRange[1]` | 500 | nm | Thin-film max |

### Attenuation

| Parameter | Prop | Default | Range | Purpose |
|-----------|------|---------|-------|---------|
| Attenuation Distance | `attenuationDistance` | 4.7 | 0–20+ | Color absorption depth |
| Attenuation Tint | `attenuationColor` | `0xffffff` | color | Volume tint color |

## Three.js Version Requirement

`MeshPhysicalMaterial.dispersion` requires Three.js r162+. The existing skill baseline is r134+ — Mode 6 must specify a higher CDN version:

```
https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js
```

Import addons (EffectComposer, UnrealBloomPass, RGBELoader) from the matching version path.

## Pane Geometry System (Voronoi Fracture)

Glass Hero uses Voronoi tessellation to fracture a rectangular hero area into N glass shards. Each shard is an independent MeshPhysicalMaterial mesh.

| Parameter | Default | Purpose |
|-----------|---------|---------|
| Piece Count | 5 | Number of glass fragments |
| Relax Iterations | 4 | Lloyd relaxation smoothness |
| Min Edge Length | 0.355 | Smallest fragment edge |
| Gap | 0.045 | Space between panes |
| Corner Radius | 0.045 | Fragment rounding |
| Corner Smoothness | 0.000 | Squircle factor |
| Chamfer Enabled | Off | Edge bevel toggle |
| Chamfer Angle | 16 | Bevel angle degrees |
| Pane Depth | 0.040 | Glass thickness (geometry) |
| Cell Smooth Passes | 0 | Mesh subdivision |
| Vertex Smoothing | 0.20 | Post-subdivision smoothing |
| Pane Padding | 0.26 | Glass inset from edge |
| Hero Padding X/Y | 126/115 | Content inset in pixels |
| Top Bar Height | 0.20 | Header strip ratio |
| Top Bar Gap | 0.025 | Header-body gap |
| Back Pane Scale | 1.00 | Background pane sizing |
| Back Pane Corners | 3 | Background rounding |

For vanilla Three.js: generate Voronoi cells via Fortune's algorithm (or simplified random-point relaxation), clip to the hero rectangle, extrude each cell to `paneDepth`, apply corner radius via rounded-rect extrusion or ChamferGeometry.

## Interaction Model

| Parameter | Default | Purpose |
|-----------|---------|---------|
| Hover Tilt | 0.36 | Rotation response to cursor |
| Hover Radius | 1.95 | Influence zone size |
| Hover Cell Push | 1.04 | Z-displacement on hover |
| Hover Ease | 4.0 | Animation smoothing |
| Push Mode | Focus | "Focus" = only hovered cell grows; "Spread" = neighbors displace |
| Topology Lock | Off | Lock fragment positions |

Track mouse in NDC. For each pane, compute distance from mouse ray to pane center. If within `hoverRadius`, apply tilt rotation (quaternion slerp toward mouse-direction tilt) and Z-push (`lerp` pane `position.z` toward `hoverCellPush`). Use `hoverEase` as the lerp rate.

## Color System

| Token | Value | Usage |
|-------|-------|-------|
| Base | `#0a0a0c` | Canvas/scene background |
| Link Hover | `#57FFA8` | Mint — anchor hover |
| CTA Hover | `#57FFA8` | Mint — button hover |
| Secondary Hover | `#A78BFA` | Violet — secondary actions |
| Warm accent | `rgb(254, 128, 64)` | Orange (panel/UI) |
| Glass edge light | `rgba(255,255,255,0.11)` | Subtle border glow |
| Glass edge bright | `rgba(255,255,255,0.9)` | Strong border highlight |
| Text primary | `white` | Headings |
| Text body | `white/60` | Body paragraphs |
| Text banner | `white/70` | Notice text |
| Text code | `white/90` | Inline code |
| Overlay | `rgba(0,0,0,0.5)` | Dimming layer |
| Panel bg | `rgb(22,22,22)` | Sidebar background |

CSS custom properties: `--hero-link-hover`, `--hero-cta-hover`, `--hero-secondary-hover`, `--font-space-grotesk`.

## Typography

| Role | Family | Size | Tracking | Weight |
|------|--------|------|----------|--------|
| Display heading | Geist, ui-sans-serif, system-ui | 28px | -0.02em | 600 |
| Body | Geist | 15px | -0.005em | 400 |
| Banner | system-ui | 12px | normal | 400 |
| Code inline | Geist Mono | inherit | normal | 400 |
| Controls | Space Grotesk | 11–12px | normal | 400–500 |

Line height: 1.6 for body. Load Geist + Geist Mono + Space Grotesk via CDN or `@font-face`.

## Post-Processing Pipeline

| Effect | Parameter | Default | Purpose |
|--------|-----------|---------|---------|
| Bloom | `strength` | 0.05 | Glow intensity |
| Bloom | `radius` | 1.80 | Glow spread |
| Bloom | `threshold` | 1.10 | Brightness cutoff |
| Chromatic Aberration | `strength` | 0.000 | RGB fringe (off by default) |
| Vignette | `darkness` | 0.00 | Edge darkening (off by default) |

Use `EffectComposer` with `UnrealBloomPass`. Chromatic aberration and vignette via custom `ShaderPass` or Phosphor Vigil FX if integrated.

## Motion System

| Parameter | Default | Purpose |
|-----------|---------|---------|
| Parallax | 1.90 | Depth response to cursor |
| Env Rotation Speed | 0.30 | Background HDRI rotation rate |
| Fly Direction Deg | 60 | Entry animation angle |
| Fly Distance | 12.0 | Entry animation travel distance |
| Fly Duration | 0.90 | Entry animation time (seconds) |

**Fly-in:** On load, position all panes at `(cos(flyDir) * flyDist, sin(flyDir) * flyDist, 0)` offset from rest, then lerp to rest over `flyDuration`. **Parallax:** Offset `camera.position.x/y` by `normalizedMouse * parallaxFactor`.

## Material Presets

Three presets spanning the parameter space:

### Clear Crystal
Maximum clarity, minimal distortion.
```js
{ ior: 1.5, thickness: 0.5, dispersion: 0.1, roughness: 0.05,
  transmission: 1.0, iridescence: 0.0 }
```

### Frosted Opal
Soft, diffused, iridescent.
```js
{ ior: 1.8, thickness: 2.0, dispersion: 0.3, roughness: 0.7,
  transmission: 0.9, iridescence: 1.0, iridescenceIOR: 2.0,
  iridescenceThicknessRange: [100, 400] }
```

### Chromatic Prism (Glass Hero default)
Maximum visual drama — the reference preset.
```js
{ ior: 2.14, thickness: 1.35, dispersion: 0.415, roughness: 0.41,
  transmission: 1.0, clearcoat: 1.0, clearcoatRoughness: 0.59,
  iridescence: 1.0, iridescenceIOR: 2.34,
  iridescenceThicknessRange: [80, 500],
  attenuationDistance: 4.7, attenuationColor: 0xffffff }
```

## Vanilla Three.js Translation

The original uses React Three Fiber + drei. Mode 6 translates to vanilla:

| R3F / drei | Vanilla Three.js |
|------------|-----------------|
| `<Canvas>` | `new THREE.WebGLRenderer()` + `new THREE.Scene()` |
| `<meshPhysicalMaterial>` | `new THREE.MeshPhysicalMaterial({...})` |
| `useFrame(cb)` | `requestAnimationFrame` loop calling `cb` |
| `<EffectComposer>` | `EffectComposer` from `three/addons/postprocessing` |
| `<Bloom>` | `UnrealBloomPass` |
| `<Environment>` | `RGBELoader` + `PMREMGenerator` |
| `useThree()` | Direct `renderer` / `scene` / `camera` references |

Renderer must enable: `toneMapping: THREE.ACESFilmicToneMapping`, `outputColorSpace: THREE.SRGBColorSpace`, and `transmissionFramebuffer` (automatic when any material uses `transmission > 0`).

## Attribution

Deconstructed from [Glass Hero](https://experiments.thisiswhitespace.com/glass-hero) by kaolti (thisiswhitespace.com), May 2026. Part of a 21-experiment R3F lab including shader-deck, code-slice-hero, dot-form, and html-in-canvas.
