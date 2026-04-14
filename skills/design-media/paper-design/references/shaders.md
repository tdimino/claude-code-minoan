# Paper Shaders

Catalog current as of Paper build log entry **2026-03-10**. Last external verification: **2026-04-14**. Re-check `paper.design/build-log` and `shaders.paper.design/` when shader drift is suspected (new shaders added, props renamed).

## What it is

Standalone zero-dependency React component library of 30+ curated GPU shaders, shipped by the Paper team. Lives independently of the Paper desktop app and its MCP server — install the npm package and use the components anywhere React runs. The same shaders are also editable inside Paper-the-tool, where each shader's sliders map 1:1 onto the React props.

Install:

```bash
npm i @paper-design/shaders-react
```

Import named components:

```js
import { PaperTexture, MeshGradient, LiquidMetal } from '@paper-design/shaders-react';
```

## When to reach for Paper Shaders vs other shader skills

- **Paper Shaders** — finished, designer-tuned effects consumed as React components with named props. Zero GPU code to write. Best when the goal is to *use* a shader (mesh gradient background, liquid-metal logo animation, halftone texture) rather than author a new one.
- **`threejs-particle-canvas`** — narrative particle canvases and parametric curve spinners. Reach for this when the effect is particle-driven or needs WebGPU/TSL.
- **`grainient`** — grainient.supply-style gradient and layout effects. Reach for this when the goal is a full gradient/bento/marquee page aesthetic, not a single isolated effect.
- **`rocaille-shader`** — hover-reactive domain-warping, depth-parallax, and stable-fluid simulations over live DOM. Reach for this when the effect needs to react to cursor motion over real page content.

## Image Filters (6)

Operate on an input image via the `image` prop. Upload image, apply shader effect.

| Component | URL slug | Typical use |
|---|---|---|
| `PaperTexture` | `paper-texture` | Paper, cardboard, or fabric texture overlay on photos or illustrations |
| `FlutedGlass` | `fluted-glass` | Vertical glass distortion — frosted-glass, ribbed-panel hero treatments |
| `Water` | `water` | Rippling water distortion on imagery |
| `ImageDithering` | `image-dithering` | Floyd-Steinberg / ordered dithering — retro/print aesthetics |
| `HalftoneDots` | `halftone-dots` | Monochrome halftone — vintage pop-art, abstract shapes, editorial |
| `HalftoneCMYK` | `halftone-cmyk` | 4-plate CMYK halftone — print-style color separation |

## Logo Animations (3)

Feed a logo (usually a PNG with transparency) through the `image` prop, or choose a built-in silhouette via the separate `shape` enum (`none`, `circle`, `daisy`, `diamond`, `metaballs` — the exact set varies per shader). Produces motion treatments around the logo silhouette.

| Component | URL slug | Typical use |
|---|---|---|
| `Heatmap` | `heatmap` | Glowing heat-halo treatment around a logo |
| `LiquidMetal` | `liquid-metal` | Chrome / mercury surface — premium brand reveals |
| `GemSmoke` | `gem-smoke` | Iridescent smoke drift around a mark |

## Effects (21)

Procedural — no image input required.

| Component | URL slug | Typical use |
|---|---|---|
| `MeshGradient` | `mesh-gradient` | Animated multi-point gradient — hero backgrounds, cards |
| `StaticMeshGradient` | `static-mesh-gradient` | Same look as mesh gradient, non-animated |
| `StaticRadialGradient` | `static-radial-gradient` | Non-animated radial with grain overlay |
| `Dithering` | `dithering` | Procedural Bayer / blue-noise dithering |
| `GrainGradient` | `grain-gradient` | Film-grain gradient — editorial, photographic feel |
| `DotOrbit` | `dot-orbit` | Orbiting dot field |
| `DotGrid` | `dot-grid` | Regular dot grid with subtle motion |
| `Warp` | `warp` | Domain-warped noise flow |
| `Spiral` | `spiral` | Rotating spiral with center/proportion controls |
| `Swirl` | `swirl` | Cursor-independent swirl flow |
| `Waves` | `waves` | Layered wave bands |
| `NeuroNoise` | `neuro-noise` | Organic dendritic / neural noise pattern |
| `Perlin` | `perlin-noise` | Classic Perlin noise field |
| `SimplexNoise` | `simplex-noise` | Simplex noise field (sharper, less directional than Perlin) |
| `Voronoi` | `voronoi` | Voronoi cellular pattern |
| `PulsingBorder` | `pulsing-border` | "Thinking orb" / AI-loading border pulse |
| `Metaballs` | `metaballs` | Soft-merging blobs |
| `ColorPanels` | `color-panels` | Sliding color panels / Mondrian-esque blocks |
| `SmokeRing` | `smoke-ring` | Ring of drifting smoke |
| `GodRays` | `god-rays` | Volumetric light-ray effect |

## Common props

Every shader accepts these in addition to its shader-specific props:

| Prop | Type | Range | Meaning |
|---|---|---|---|
| `scale` | `number` | 0.01 to 4 | Overall zoom of the graphic |
| `rotation` | `number` | 0 to 360 | Rotation angle in degrees |
| `offsetX` | `number` | -1 to 1 | Horizontal offset of center |
| `offsetY` | `number` | -1 to 1 | Vertical offset of center |
| `originX` | `number` | 0 to 1 | Transform origin X (pivot for scale/rotation) |
| `originY` | `number` | 0 to 1 | Transform origin Y |
| `speed` | `number` | — | Animation playback speed (1 is default; 0 freezes) |
| `frame` | `number` | — | Manual animation clock for deterministic capture |
| `fit` | `"contain" \| "cover"` | — | How the shader fills its element box |
| `width` | `number \| string` | — | CSS width of the shader element |
| `height` | `number \| string` | — | CSS height of the shader element |
| `worldWidth` | `number` | — | Override world-space width (advanced) |
| `worldHeight` | `number` | — | Override world-space height (advanced) |
| `minPixelRatio` | `number` | — | Lower bound for DPR; clamps crispness on retina |
| `maxPixelCount` | `number` | — | Upper bound on total rasterized pixels (perf) |

Shader-specific props (color values, effect intensities, pattern-size knobs) are named consistently across the library. Color props accept hex, RGB, or HSL strings. Numeric intensity props typically range 0 to 1. Integer count props (e.g. `foldCount`) have their own bounds — check the shader's page at `shaders.paper.design/<slug>` for the authoritative prop table and a live preview.

## Worked example — Paper Texture

```tsx
import { PaperTexture } from '@paper-design/shaders-react';

<PaperTexture
  width={1280}
  height={720}
  image="https://paper.design/flowers.webp"
  colorBack="#ffffff"
  colorFront="#9fadbc"
  contrast={0.3}
  roughness={0.4}
  fiber={0.3}
  fiberSize={0.2}
  crumples={0.3}
  crumpleSize={0.35}
  folds={0.65}
  foldCount={5}
  drops={0.2}
  fade={0}
  seed={5.8}
  scale={0.6}
  fit="cover"
/>
```

The `contrast`, `roughness`, `fiber`, `crumples`, `folds`, and `drops` props correspond directly to sliders in the Paper app's Paper Texture panel. Tweak visually in Paper, read the resulting values back, and paste the props into code — or skip the manual copy by using `get_jsx` on a shader frame.

## Integration with the Paper MCP skill

When a Paper artboard contains a shader element, `get_jsx` returns the matching `@paper-design/shaders-react` component with the current prop values — not a raw HTML element. The consuming project must have the npm package installed for the exported code to run. See `workflow-patterns.md` for the shader-to-code recipe.

Build-log evolution worth knowing about:

- **2026-03-10** — drag-and-drop reordering for shader colors inside Paper
- **2026-01-19** — `HalftoneCMYK` added
- **2025-12-03** — `FlutedGlass`, `HalftoneDots`, `ImageDithering` improved transparent-image handling; mesh gradients gained monochromatic grain
- **2025-11-19** — `HalftoneDots` added
- **2025-11-06** — `FlutedGlass` major rework (added `Stretch`, `Highlights`, `Shadows`, and `Grain` controls; angle direction flipped to clockwise)
- **2025-10-22** — `LiquidMetal` fully reworked with new contour detection, `Shape` and `Angle` panels; video export from any frame

When reading legacy `get_jsx` output or older copied snippets, expect prop names and directions to drift — re-check the shader's page if props do not behave as documented.

## Authoritative source

The live prop tables and interactive previews at `shaders.paper.design/<slug>` are the source of truth. This reference catalogs *what exists* and *when to use each*; it intentionally does not duplicate per-prop docs that rot with every release.
