# WaveSpeedAI Rapid — Reference

Budget Hunyuan3D v3.1 image-to-3D at $0.0225/model (16x cheaper than fal.ai Pro). Single parameter: image URL or local file path.

**Cost:** $0.0225 flat per model.

## Credential

`WAVESPEED_API_KEY` environment variable. Auth header: `Authorization: Bearer <key>`.

Keys managed at https://wavespeed.ai/accesskey. A credit top-up is required to activate API access.

## Usage

```bash
uv run ~/.claude/skills/meshy/scripts/wavespeed_rapid.py ./photo.png --output ./models
uv run ~/.claude/skills/meshy/scripts/wavespeed_rapid.py https://example.com/image.jpg --filename tank
uv run ~/.claude/skills/meshy/scripts/wavespeed_rapid.py ./photo.png --json
```

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `IMAGE` | required | Image file path or URL |
| `--output` | `./output` | Output directory |
| `--filename` | `model` | Output filename |
| `--api-key` | env | Override WAVESPEED_API_KEY |
| `--poll-interval` | `5` | Seconds between polls |
| `--timeout` | `300` | Max wait seconds |
| `--quiet` | — | Minimal output |
| `--json` | — | Output GLB URL as JSON |

## API Contract

### Submit

```
POST https://api.wavespeed.ai/api/v3/wavespeed-ai/hunyuan-3d-v3.1/image-to-3d-rapid
Authorization: Bearer ${WAVESPEED_API_KEY}
Content-Type: application/json

{"image": "<URL or base64 data URI>"}
```

Image constraints: 128-5000px, max 8MB, JPG/PNG/WEBP.

### Submit Response

```json
{
  "code": 200,
  "data": {
    "id": "<task_id>",
    "status": "created",
    "urls": { "get": "https://api.wavespeed.ai/api/v3/predictions/<task_id>/result" }
  }
}
```

### Poll

```
GET https://api.wavespeed.ai/api/v3/predictions/{task_id}/result
```

Status values: `created` → `processing` → `completed` / `failed`.

On completed: `data.outputs[0]` is the GLB download URL (CDN-hosted, no auth needed).
