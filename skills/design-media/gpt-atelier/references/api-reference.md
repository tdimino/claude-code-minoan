# GPT Atelier API Reference

## Models

| Model | ID | Strengths | Cost (1024x1024 high) |
|-------|----|-----------|-----------------------|
| GPT Image 2 | `gpt-image-2` | Reasoning-based gen, ~99% text rendering, up to 8 images, 4K, streaming | $0.211 |
| GPT Image 1.5 | `gpt-image-1.5` | Region-aware editing, 4x faster, good text rendering | $0.133 |
| GPT Image 1 | `gpt-image-1` | Stable, legacy | $0.167 |
| GPT Image 1 Mini | `gpt-image-1-mini` | Cheapest | $0.036 |

## Image API — Generate

`POST /v1/images/generations` via `client.images.generate()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | str | required | Text description |
| `model` | str | `gpt-image-2` | Model ID |
| `size` | str | `auto` | `WxH`, preset name, or `auto`. Both dims multiples of 16, max edge 3840px, aspect ≤3:1, total pixels 655K-8.3M |
| `quality` | str | `auto` (API); scripts default to `high` | `low`, `medium`, `high`, `auto` |
| `n` | int | 1 | Number of images (1-8) |
| `output_format` | str | `png` | `png`, `jpeg`, `webp` |
| `output_compression` | int | — | 0-100 for jpeg/webp |
| `background` | str | — | `opaque`, `transparent` (not gpt-image-2), `auto` |
| `moderation` | str | `auto` | `auto`, `low` |
| `partial_images` | int | 0 | 0-3 partials for streaming (use via `stream_image.py`) |
| `stream` | bool | false | Enable streaming |

## Image API — Edit

`POST /v1/images/edits` via `client.images.edit()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image` | file(s) | required | Input image(s) |
| `prompt` | str | required | Edit instruction |
| `mask` | file | — | Mask with alpha channel (transparent = edit region) |
| `model` | str | `gpt-image-2` | Model ID |
| `size` | str | — | Output size |
| `quality` | str | `auto` | Quality tier |
| `n` | int | 1 | Number of variations |
| `input_fidelity` | str | — | `high`, `low` (gpt-image-2 always high) |
| `output_format` | str | `png` | Output format |
| `output_compression` | int | — | 0-100 |

Mask must have alpha channel. B&W masks auto-converted by `edit_image.py`.

## Responses API — Image Generation Tool

`client.responses.create()` with `tools=[{"type": "image_generation"}]`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | str | `gpt-5.4` | Orchestrator model |
| `input` | list | required | Conversation input |
| `tools` | list | required | Must include `{"type": "image_generation"}` |
| `previous_response_id` | str | — | For multi-turn continuity |

Tool config options (inside the tool dict):
| Field | Values | Description |
|-------|--------|-------------|
| `action` | `auto`, `generate`, `edit` | Force generation or editing mode |
| `quality` | `low`, `medium`, `high` | Quality tier |
| `size` | str | Output size |
| `output_format` | `png`, `jpeg`, `webp` | Format |
| `partial_images` | 0-3 | Streaming partials |

## Size Presets

| Preset | Resolution | Use Case |
|--------|-----------|----------|
| `square` | 1024x1024 | Social media, avatars |
| `landscape` | 1536x1024 | Blog headers |
| `portrait` | 1024x1536 | Mobile, stories |
| `wide` | 2048x1152 | Desktop wallpaper |
| `2k` | 2048x2048 | High-res square |
| `4k` | 3840x2160 | Print, hero images |
| `4k-portrait` | 2160x3840 | Print posters |
| `auto` | model decides | Default |

Raw dimensions accepted: any `WxH` where both are multiples of 16, max edge 3840px, ratio ≤3:1, total pixels 655,360-8,294,400.

## Pricing (per output image)

| Model | Low | Medium | High |
|-------|-----|--------|------|
| gpt-image-2 (1024x1024) | $0.006 | $0.053 | $0.211 |
| gpt-image-2 (1536x1024) | $0.005 | $0.041 | $0.165 |
| gpt-image-1.5 (1024x1024) | $0.009 | $0.034 | $0.133 |
| gpt-image-1-mini (1024x1024) | $0.005 | $0.011 | $0.036 |

Plus input text tokens and input image tokens for edit requests.

## Rate Limits

Tier-dependent. Check your dashboard at `platform.openai.com/settings`.
Complex prompts may take up to 2 minutes. Use `jpeg` over `png` for lower latency.
