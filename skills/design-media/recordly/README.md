# Recordly

Screen recording polish and 3D perspective rendering for product demos, walkthroughs, and social media clips.

Two modes:

- **Recordly GUI** — 2D recording polish with auto-zoom, cursor animations, webcam overlays, styled backgrounds, and timeline editing. Fork of [OpenScreen](https://github.com/siddharthvaddem/openscreen) (10.6K stars, MIT). AGPL 3.0.
- **Slant** — Browser-based 3D perspective renderer. Drop a flat screen recording, pick an animation preset, export as MP4 or GIF. Self-contained HTML file, no build step, no server.

## Quick Start

```bash
# Install Recordly GUI (clone, build, macOS quarantine fix)
bash scripts/install_recordly.sh

# Launch Recordly GUI
bash scripts/launch_recordly.sh
bash scripts/launch_recordly.sh path/to/recording.mp4

# Open 3D perspective renderer in browser
open scripts/slant.html
```

## Slant — 3D Perspective Renderer

Open `scripts/slant.html` in any modern browser. Drop a screen recording onto the viewport or use the file picker.

### Animation Presets

| # | Preset | Motion | Use Case |
|---|--------|--------|----------|
| 1 | Hero Float | Subtle floating drift | Landing pages |
| 2 | Dramatic Tilt | Flat to angled reveal | Intros |
| 3 | Orbit Right | 45 degree clockwise sweep | Showcases |
| 4 | Orbit Left | 45 degree counter-clockwise | Showcases |
| 5 | Slide In | Screen enters from right | Transitions |
| 6 | Pull Back | Camera dollies out | Context reveals |
| 7 | Push In | Camera dollies forward | Detail focus |
| 8 | Top Down | Overhead to angled | App overviews |
| 9 | Isometric | Fixed isometric angle | Technical |
| 10 | Carousel | Full 360 degree orbit | Product views |
| 11 | Breathing | Subtle in/out pulse | Ambient loops |
| 12 | Cinematic Pan | Lateral pan with shallow DOF | Film-grade |

### Export Formats

| Format | Codec | Best For | Browser Support |
|--------|-------|----------|----------------|
| **MP4** | H.264 via MediaRecorder | Twitter, social media | Safari, Chrome (where supported) |
| **WebM** | VP9/VP8 via MediaRecorder | General web use | Chrome, Edge, Firefox |
| **GIF** | gifenc (256 colors, 640px wide) | GitHub PRs (inline rendering) | All browsers |

### Controls

- **Sidebar** — Preset selector, background (gradient/solid/HDRI), screen style (corners, clearcoat, shadow), camera FOV, depth of field, bloom
- **Viewport** — Orbit controls for free camera exploration; locks to preset path during export
- **Keyboard** — Space: play/pause, E: export, R: reset camera, 1-9: select preset

### How It Works

Three.js r183 renders the video as a `VideoTexture` on a `PlaneGeometry` with `MeshPhysicalMaterial` (clearcoat for glass-like reflections). HDRI environment maps from Poly Haven provide realistic lighting. Post-processing chain: RenderPass, UnrealBloomPass, BokehPass (depth of field), OutputPass.

### Dependencies

All loaded from CDN at runtime — zero local dependencies:

- [Three.js r183](https://threejs.org/) — 3D rendering
- [gifenc](https://github.com/mattdesl/gifenc) — GIF encoding (loaded on demand)
- [Poly Haven](https://polyhaven.com/) — HDRI environment maps (CC0, loaded on demand)

## Feature Comparison

| Feature | Recordly GUI | Slant | Screen Studio | Slant it |
|---------|-------------|-------|---------------|----------|
| 2D auto-zoom | Yes | — | Yes | — |
| Cursor effects | Yes | — | Yes | — |
| Webcam overlay | Yes | — | Yes | — |
| 3D perspective | — | Yes | — | Yes |
| HDRI reflections | — | Yes | — | Yes |
| Depth of field | — | Yes | — | Yes |
| Animation presets | — | 12 | — | 35+ |
| Export MP4 | Yes | Yes | Yes | Yes |
| Export GIF | — | Yes | Yes | — |
| Price | Free (AGPL) | Free | $89 | $69 |
| Runs locally | Yes | Yes (browser) | Yes | Yes (browser) |
| Build step | npm install | None | Installer | None |

## Limitations

- Slant does not add device frames (phone/laptop bezels) — it renders the 3D perspective effect only
- No audio mixing — source video audio is not included in exports
- No batch processing — one video at a time
- Desktop browsers only — mobile WebGL works but export quality varies
- GIF export limited to 640px wide / 256 colors (inherent format constraint)
- Large videos (>2 min) may hit memory limits during encoding

## Links

- **Recordly repo**: [github.com/webadderall/Recordly](https://github.com/webadderall/Recordly)
- **Upstream (OpenScreen)**: [github.com/siddharthvaddem/openscreen](https://github.com/siddharthvaddem/openscreen)
- **Three.js**: [threejs.org](https://threejs.org/)
- **Poly Haven HDRIs**: [polyhaven.com](https://polyhaven.com/)
