# GPT Atelier

OpenAI GPT Image generation and editing---text-to-image, mask-based inpainting, multi-reference composition, multi-turn conversational editing via Responses API, and streaming with partial images.

**Last updated:** 2026-04-22

**Reflects:** OpenAI GPT Image 2 (April 2026), GPT Image 1.5, GPT Image 1 Mini, and both Image API and Responses API surfaces.

---

## Why This Skill Exists

OpenAI's GPT Image models have capabilities that no other provider matches: ~99% text rendering accuracy (including non-Latin scripts), native mask-based inpainting with near-zero drift, multi-turn editing with true conversation state, and streaming partial images for progressive delivery. This skill wraps both API surfaces with 6 scripts, a prompting guide, and full parameter reference---the OpenAI counterpart to `nano-banana-pro` (Gemini).

---

## Structure

```
gpt-atelier/
  SKILL.md                                 # Complete workflow and API patterns
  README.md                                # This file
  references/
    api-reference.md                       # Full parameter reference, pricing, size constraints
    prompting-guide.md                     # Prompt engineering patterns, text rendering, style keywords
    troubleshooting.md                     # Error codes, content policy, rate limits
  scripts/
    openai_images.py                       # Shared API client library (GPTAtelierClient + GPTAtelierChat)
    generate_image.py                      # Text-to-image generation
    edit_image.py                          # Edit with mask and reference images
    compose_images.py                      # Multi-reference composition
    converse_image.py                      # Multi-turn editing via Responses API
    stream_image.py                        # Streaming with partial images
    test_connection.py                     # API key and connectivity validation
```

---

## What It Covers

### Three Models

| Flag | Model | Strengths | Cost (1024x1024 high) |
|------|-------|-----------|-----------------------|
| (default) | `gpt-image-2` | Reasoning-based, ~99% text rendering, up to 8 images, 4K, streaming | $0.211 |
| `--fast` | `gpt-image-1.5` | Region-aware editing, 4x faster | $0.133 |
| `--mini` | `gpt-image-1-mini` | Cheapest ($0.006/image low quality) | $0.036 |

### Generation Modes

| Mode | Script | API |
|------|--------|-----|
| Text-to-image | `generate_image.py` | Image API |
| Image editing | `edit_image.py` | Image API |
| Multi-reference composition | `compose_images.py` | Image API |
| Multi-turn conversational editing | `converse_image.py` | Responses API |
| Streaming with partials | `stream_image.py` | Image API |

### Two API Surfaces

**Image API** (`client.images.generate()` / `client.images.edit()`)---one-shot generation and editing with full parameter control: arbitrary resolution (multiples of 16px, up to 3840px edge), quality tiers, mask-based inpainting, multiple output images.

**Responses API** (`client.responses.create()` with image_generation tool)---multi-turn conversational editing via `previous_response_id`. The orchestrator model (GPT-5.4) reasons about the editing intent and delegates to the image model. True conversation state---the model remembers the full editing history.

### Unique Capabilities (vs Nano Banana Pro)

| Capability | GPT Atelier | Nano Banana Pro |
|------------|-------------|-----------------|
| Text rendering (complex, non-Latin) | ~99% accuracy | Good |
| Mask-based inpainting | Native, near-zero drift | ~40% pixel drift |
| Multi-turn with state | Responses API | Multi-turn chat |
| Streaming partial images | Native | Not available |
| Arbitrary resolution | Any (16px multiples, up to 4K) | 10 presets |
| Dark/artistic themes | Stricter policy | More permissive |
| Photorealism | Excellent | Excellent |

---

## Scripts

All scripts use `OPENAI_API_KEY` from environment.

| Script | Usage |
|--------|-------|
| `generate_image.py` | `python3 generate_image.py "A Minoan bull-leaper under golden light"` |
| `edit_image.py` | `python3 edit_image.py "Replace sky with sunset" photo.png --mask sky_mask.png` |
| `compose_images.py` | `python3 compose_images.py "Gift basket with these items" a.png b.png c.png` |
| `converse_image.py` | `python3 converse_image.py` (interactive REPL) |
| `stream_image.py` | `python3 stream_image.py "An ancient fresco being restored" --partials 3` |
| `test_connection.py` | `python3 test_connection.py --check-models` |

Image API scripts share: `--output DIR`, `--filename NAME`, `--quality low|medium|high`, `--format png|jpeg|webp`, `--fast`, `--mini`.

---

## Requirements

- Python 3.9+
- `openai` (`pip install openai`)
- `OPENAI_API_KEY` environment variable
- `Pillow` for mask auto-conversion (`pip install Pillow`)
- OpenAI organization verification (required for GPT Image models)

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/design-media/gpt-atelier ~/.claude/skills/
```
