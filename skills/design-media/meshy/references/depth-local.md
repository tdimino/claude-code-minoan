# Local Depth — Reference

Free, offline depth estimation and mesh generation via ONNX Runtime. No API key required. Runs on-device.

Ported from [waydeeper](https://github.com/EdenQwQ/waydeeper) (MIT License).

**Cost:** Free (local inference).

## Credential

None. This is a local provider — no API key needed.

## Dependencies

```bash
# Installed automatically by uv run
onnxruntime numpy Pillow requests

# Optional (for GLB conversion)
uv pip install trimesh
```

## Usage

```bash
# Generate depth map (grayscale PNG)
uv run ~/.claude/skills/meshy/scripts/depth_local.py depth ./photo.png --output ./output

# Generate PLY mesh
uv run ~/.claude/skills/meshy/scripts/depth_local.py mesh ./photo.png --output ./output

# Generate GLB mesh (requires trimesh)
uv run ~/.claude/skills/meshy/scripts/depth_local.py mesh ./photo.png --format glb --output ./output

# Download a model (auto-downloads on first use)
uv run ~/.claude/skills/meshy/scripts/depth_local.py download depth-anything-v3-base

# List models and install status
uv run ~/.claude/skills/meshy/scripts/depth_local.py models
```

## Subcommands

### `depth IMAGE`

Generate a depth map as grayscale PNG. Closer objects = brighter.

| Flag | Default | Description |
|------|---------|-------------|
| `IMAGE` | required | Input image path |
| `--model` | `depth-anything-v3-base` | Depth model name or path |
| `--output` | `./output` | Output directory |
| `--filename` | input stem | Output filename stem |
| `--no-cache` | — | Skip depth cache |
| `--json` | — | JSON output |

### `mesh IMAGE`

Generate a 3D mesh (PLY or GLB) from depth estimation.

| Flag | Default | Description |
|------|---------|-------------|
| `IMAGE` | required | Input image path |
| `--model` | `depth-anything-v3-base` | Depth model name or path |
| `--output` | `./output` | Output directory |
| `--filename` | input stem | Output filename stem |
| `--format` | `ply` | `ply` or `glb` |
| `--fov` | `60.0` | Vertical FoV in degrees |
| `--edge-threshold` | `0.08` | Depth discontinuity threshold for face culling |
| `--no-cache` | — | Skip depth cache |
| `--json` | — | JSON output |

### `download [MODEL]`

Download an ONNX depth model from HuggingFace.

| Flag | Default | Description |
|------|---------|-------------|
| `MODEL` | `depth-anything-v3-base` | Model name |
| `--force` | — | Re-download even if installed |

### `models`

List available models and install status. No flags.

## Available Models

| Model | Size | Quality | Speed |
|-------|------|---------|-------|
| `depth-anything-v3-base` | ~100 MB | Good | Fast |
| `midas-small` | ~16 MB | Lower | Fastest |
| `depth-pro-q4` | ~500 MB | Highest | Slow |

Models stored at `~/.local/share/depth-local/models/`.
Depth cache at `~/.cache/depth-local/depth/`.

## Mesh Details

The mesh subcommand projects image pixels to 3D using a pinhole camera model:
- FoV determines the projection angle (default 60 degrees)
- Each pixel with depth `d` maps to 3D coordinates using focal length derived from FoV
- Triangles spanning large depth discontinuities are culled (configurable threshold)
- Output is binary PLY with per-vertex RGB color

The PLY includes a `fov_y_deg` comment header for renderer compatibility.

## Future: Neural Inpainting

The `networks.py` file contains PyTorch definitions for the 3D Photo Inpainting pipeline
(edge/depth/color networks). A future `--mode inpaint` will synthesize occluded background
geometry for true parallax — requires PyTorch and ~300 MB of model weights.

## Pipeline Composability

Depth maps from this provider can feed into other meshy providers:
- Generate depth map locally → use as reference for Meshy text-to-texture
- Generate PLY mesh → convert to GLB → view in `glb-viewer.html`
- Depth map as preprocessing for fal.ai Hunyuan3D or Trellis 2
