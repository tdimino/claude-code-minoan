# Meshy API v2 Reference

Base URL: `https://api.meshy.ai/openapi/v2`

## Authentication

All requests require a Bearer token:
```
Authorization: Bearer {MESHY_API_KEY}
Content-Type: application/json
```

## Endpoints

### POST /text-to-3d

Create a text-to-3D generation task.

**Preview mode:**
```json
{
  "mode": "preview",
  "prompt": "description (max 600 chars)",
  "negative_prompt": "what to avoid",
  "model_type": "standard|lowpoly|ai_model",
  "art_style": "photorealistic|...",
  "topology": "triangle|quad",
  "target_polycount": 50000,
  "should_remesh": false,
  "symmetry_mode": false
}
```

**Refine mode:**
```json
{
  "mode": "refine",
  "preview_task_id": "{UUID}",
  "enable_pbr": true,
  "texture_prompt": "texturing guidance (max 600 chars)",
  "remove_lighting": true
}
```

**Response:** `{ "result": "task_id" }`

### GET /text-to-3d/{task_id}

Get task status and results.

**Response:**
```json
{
  "id": "018a210d-...",
  "status": "PENDING|IN_PROGRESS|SUCCEEDED|FAILED|CANCELED",
  "mode": "preview|refine",
  "progress": 65,
  "prompt": "...",
  "created_at": "2024-01-15T10:30:00Z",
  "model_urls": {
    "glb": "https://cdn.meshy.ai/...",
    "gltf": "https://...",
    "usdz": "https://...",
    "fbx": "https://..."
  },
  "thumbnail_url": "https://...",
  "task_error": {
    "message": "error description"
  }
}
```

### GET /text-to-3d

List tasks with pagination.

**Parameters:** `page_num`, `page_size`, `sort_by` (-created_at)

### POST /image-to-3d

Generate 3D model from image.

```json
{
  "image_url": "https://... or data:image/png;base64,...",
  "model_type": "standard|lowpoly",
  "topology": "triangle|quad",
  "target_polycount": 50000,
  "should_remesh": false
}
```

### GET /image-to-3d/{task_id}

Same response format as text-to-3d tasks.

### POST /text-to-texture

Apply texture to existing model.

```json
{
  "model_url": "https://...",
  "prompt": "texture description",
  "negative_prompt": "what to avoid",
  "art_style": "...",
  "enable_pbr": true
}
```

### GET /balance

Get account credit balance.

**Response:** `{ "credit_balance": 500 }`

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 401 | Unauthorized (invalid API key) |
| 422 | Validation error |
| 429 | Rate limit exceeded |

## Task Statuses

| Status | Meaning |
|--------|---------|
| `PENDING` | Queued, not yet started |
| `IN_PROGRESS` | Currently generating |
| `SUCCEEDED` | Complete, model_urls available |
| `FAILED` | Error occurred (see task_error) |
| `CANCELED` | Manually canceled |

## Documentation

- API docs: https://docs.meshy.ai/en/api/text-to-3d
- Authentication: https://docs.meshy.ai/en/getting-started/authentication
- Pricing: https://docs.meshy.ai/en/getting-started/pricing
- Webhooks: https://docs.meshy.ai/en/getting-started/webhooks
