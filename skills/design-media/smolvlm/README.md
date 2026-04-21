# SmolVLM

Local image analysis using SmolVLM2-2.2B-Instruct, a compact vision-language model optimized for Apple Silicon via mlx-vlm. Describe images, extract text (OCR), analyze UI screenshots, and answer visual questions—all offline, no API key required. SmolVLM2 also supports video understanding via the transformers pipeline (this skill's script handles image-only via mlx-vlm).

**Last updated:** 2026-04-21

---

## Why This Skill Exists

Claude can read images natively, but sending every screenshot to the API costs tokens. SmolVLM2 runs locally on Apple Silicon at ~94 tok/s with ~5GB RAM, making it useful for high-volume image triage, OCR extraction, and UI analysis without API costs.

---

## Structure

```
smolvlm/
  SKILL.md              # Full usage guide with prompt examples
  README.md             # This file
  scripts/
    view_image.py       # Image analysis CLI
```

---

## Usage

```bash
# Describe an image
python3 view_image.py /path/to/image.png

# Ask a specific question
python3 view_image.py /path/to/image.png "What text is visible?"

# Detailed description
python3 view_image.py photo.jpg --detailed
```

Supports PNG, JPG, JPEG, GIF, and WebP.

---

## Model Specs

| Spec | Value |
|------|-------|
| Model | SmolVLM2-2.2B-Instruct |
| HuggingFace ID | `HuggingFaceTB/SmolVLM2-2.2B-Instruct` |
| Size | ~4.5GB (downloaded on first run) |
| Peak Memory | ~5.2GB (bfloat16) |
| Speed | ~94 tok/s (M-series) |

---

## Setup

### Prerequisites

- macOS with Apple Silicon (M1/M2/M3/M4)
- Python 3.10+
- `uv pip install mlx-vlm --system`

First run downloads the model (~4GB).

---

## Related Skills

- **`parakeet`**: Local speech-to-text---same philosophy (offline, Apple Silicon, no API key).
- **`nano-banana-pro`**: AI image generation/editing (cloud-based, complementary to local vision).

---

## Requirements

- macOS Apple Silicon
- Python 3.10+
- `mlx-vlm`

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/design-media/smolvlm ~/.claude/skills/
```
