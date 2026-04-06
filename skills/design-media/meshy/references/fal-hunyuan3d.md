# fal.ai Hunyuan3D v3.1 Pro — Reference

High-fidelity image-to-3D and text-to-3D via fal.ai's hosted Hunyuan3D model. Produces .glb with PBR textures, 500K faces default.

**Cost:** ~$0.225-$0.375 per model.

## Credential

`FAL_KEY` environment variable. Auth header: `Authorization: Key <key>` (not Bearer).

## Usage

```bash
# Image-to-3D (primary use case)
uv run ~/.claude/skills/meshy/scripts/fal_hunyuan3d.py ./photo.png --output ./models --filename tank

# Text-to-3D (rapid mode, max 195 chars)
uv run ~/.claude/skills/meshy/scripts/fal_hunyuan3d.py --text "a golden microphone" --output ./models

# Lower poly count
uv run ~/.claude/skills/meshy/scripts/fal_hunyuan3d.py ./photo.png --face-count 100000

# JSON output (URLs only, no download)
uv run ~/.claude/skills/meshy/scripts/fal_hunyuan3d.py ./photo.png --json
```

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `IMAGE` | — | Image file path or URL |
| `--text` | — | Text prompt (text-to-3D mode, max 195 chars) |
| `--face-count` | `500000` | Target face count |
| `--no-pbr` | — | Disable PBR textures |
| `--seed` | — | Seed (text-to-3D only) |
| `--output` | `./output` | Output directory |
| `--filename` | `model` | Output filename |
| `--api-key` | env | Override FAL_KEY |
| `--poll-interval` | `4` | Seconds between polls |
| `--timeout` | `300` | Max wait seconds |
| `--quiet` | — | Minimal output |
| `--json` | — | Output URLs as JSON |

## API Endpoints

| Mode | Endpoint ID |
|------|------------|
| Image-to-3D Pro | `fal-ai/hunyuan-3d/v3.1/pro/image-to-3d` |
| Text-to-3D Rapid | `fal-ai/hunyuan-3d/v3.1/rapid/text-to-3d` |

### Queue Pattern

1. `POST https://queue.fal.run/<endpoint>` → `request_id`, `status_url`, `response_url`
2. Poll `GET <status_url>` every 4s → `IN_QUEUE` / `IN_PROGRESS` / `COMPLETED` / `FAILED`
3. On COMPLETED: `GET <response_url>` → result with model URLs

### Image-to-3D Payload

```json
{
  "input_image_url": "<base64 data URI or HTTPS URL>",
  "generate_type": "Normal",
  "face_count": 500000,
  "enable_pbr": true
}
```

### Text-to-3D Payload

```json
{
  "prompt": "<text, max 195 chars>",
  "seed": 42
}
```

### Response Schema

```json
{
  "model_glb": { "url": "https://..." },
  "model_urls": {
    "glb": { "url": "https://..." },
    "obj": { "url": "https://..." },
    "texture": { "url": "https://..." }
  },
  "thumbnail": { "url": "https://..." },
  "seed": 42
}
```

GLB extraction: `result.model_glb.url || result.model_urls.glb.url`
