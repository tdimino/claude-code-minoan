# Trellis 2 (3D AI Studio) — Reference

Image-to-3D with precise polygon count control via `decimation_target`. Set ~5,000 for low-poly game assets.

**Cost:** 15-55 credits depending on resolution + textures.

## Credential

`THREEDAI_API_KEY` environment variable. Auth header: `Authorization: Bearer <key>`.

## Usage

```bash
# Low-poly geometry only (fastest, cheapest — 15 credits)
uv run ~/.claude/skills/meshy/scripts/trellis2.py ./photo.png --resolution 512 --decimation 5000

# Production with textures (30 credits)
uv run ~/.claude/skills/meshy/scripts/trellis2.py ./photo.png --textures --texture-size 2048 --decimation 50000

# Max quality (55 credits)
uv run ~/.claude/skills/meshy/scripts/trellis2.py ./photo.png --resolution 1536 --textures --texture-size 4096
```

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `IMAGE` | required | Image file path or URL |
| `--resolution` | `1024` | Voxel grid: `512` / `1024` / `1536` |
| `--textures` | off | Generate PBR textures (base color, roughness, metallic, opacity) |
| `--texture-size` | `2048` | Texture map: `1024` / `2048` / `4096` |
| `--decimation` | `1000000` | Target face count (1K-16M) |
| `--seed` | random | Reproducibility seed |
| `--output` | `./output` | Output directory |
| `--filename` | `model` | Output filename |
| `--api-key` | env | Override THREEDAI_API_KEY |
| `--poll-interval` | `10` | Seconds between polls |
| `--timeout` | `300` | Max wait seconds |
| `--quiet` | — | Minimal output |
| `--json` | — | Output GLB URL as JSON |

## Credit Costs

| Resolution | Geometry Only | Textured 1024px | Textured 2048px | Textured 4096px |
|------------|--------------|-----------------|-----------------|-----------------|
| 512 | 15 credits | 25 credits | 25 credits | 30 credits |
| 1024 | 20 credits | 30 credits | 30 credits | 40 credits |
| 1536 | 25 credits | 40 credits | 40 credits | 55 credits |

`generate_thumbnail: true` adds +2 credits.

## Processing Times

| Config | Approx. Time |
|--------|-------------|
| 512 resolution | ~20-25s |
| 1024 (recommended) | ~30-50s |
| 1536 (max) | ~70-130s |
| With textures | +40-70s |
| Cold start | +30-60s additional |

## API Contract

### Submit

```
POST https://api.3daistudio.com/v1/3d-models/trellis2/generate/
Authorization: Bearer ${THREEDAI_API_KEY}
Content-Type: application/json

{
  "image_url": "https://...",
  "resolution": "1024",
  "textures": true,
  "texture_size": 2048,
  "decimation_target": 5000,
  "seed": null,
  "generate_thumbnail": false
}
```

Use `image_url` for URLs, `image` for base64 data URIs.

### Poll

```
GET https://api.3daistudio.com/v1/generation-request/{task_id}/status/
```

Status values: `PROCESSING` → `FINISHED` / `FAILED`. Progress reported as 0-100%.

On FINISHED: `results[0]["asset"]` is the GLB download URL. **Results expire after 24 hours.** Credits auto-refunded on failure.

### Error Codes

| Code | Meaning |
|------|---------|
| 400 | Missing/invalid params |
| 401 | Invalid API key |
| 402 | Insufficient credits |
| 429 | Rate limit exceeded |
| 500 | GPU error (credits refunded) |
