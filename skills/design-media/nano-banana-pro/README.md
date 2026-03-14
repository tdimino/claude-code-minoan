# Nano Banana Pro

The image generation skill. Generate and edit professional-quality images using Google's Gemini 3 Pro Image model---text-to-image, image editing, multi-turn refinement, batch workflows, and a cinematic style guide for documentary-quality output.

**Last updated:** 2026-02-27

**Reflects:** Google Gemini 3 Pro Image API, Gemini 3.1 Flash for fast iteration, and production image generation patterns from Aldea Soul Engine avatar creation.

---

## Why This Skill Exists

AI image generation is easy to start and hard to do well. Default prompts produce generic results. Temperature, aspect ratio, and resolution interact in non-obvious ways. Editing an existing image requires different API patterns than generating from scratch. Batch workflows need rate limiting. And getting a consistent visual identity across multiple images---for avatars, product shots, or a design system---requires reference-based generation with careful prompt engineering.

This skill encodes all of it: 6 Python scripts covering every generation mode, a prompting guide with tested techniques, a cinematic style formula for documentary-quality results, Aldea avatar templates for soul engine personas, and troubleshooting for content policy violations and rate limits.

---

## Structure

```
nano-banana-pro/
  SKILL.md                                 # Complete workflow and API patterns
  README.md                                # This file
  cinematic-style.md                       # Documentary-style painting formula
  assets/
    example-prompts.md                     # Ready-to-use prompts by category
  references/
    api-reference.md                       # Complete API docs, pricing, rate limits
    prompting-guide.md                     # Best practices and techniques
    troubleshooting.md                     # Common issues and solutions
    aldea-avatars.md                       # Character templates for Soul Engine personas
  scripts/
    README.md                              # Script overview
    generate_image.py                      # Text-to-image generation
    edit_image.py                          # Edit existing images with instructions
    compose_images.py                      # Compose from multiple reference images
    generate_with_references.py            # Style-consistent generation with references
    multi_turn_chat.py                     # Iterative refinement via conversation
    gemini_images.py                       # Shared API client library
    test_connection.py                     # Verify API key and connectivity
```

---

## What It Covers

### Two Models

| Model | Speed | Quality | Best For |
|-------|-------|---------|----------|
| **Gemini 3 Pro Image** | Slower | Highest | Final assets, hero images, avatars |
| **Gemini 3.1 Flash** | Fast | Good | Iteration, drafts, batch thumbnails |

### Generation Modes

| Mode | Script | Description |
|------|--------|-------------|
| Text-to-image | `generate_image.py` | Generate from text prompt |
| Image editing | `edit_image.py` | Modify existing image with natural language |
| Reference-based | `generate_with_references.py` | Maintain style consistency across images |
| Composition | `compose_images.py` | Combine elements from multiple source images |
| Multi-turn | `multi_turn_chat.py` | Iterative refinement via conversation |

### Prompting Guide

Key techniques from `references/prompting-guide.md`:

| Parameter | Range | Effect |
|-----------|-------|--------|
| Temperature | 0.3--1.0 | Lower = more consistent, higher = more creative |
| Aspect ratio | 1:1, 16:9, 9:16, 4:3, 3:4 | Match intended use (social, hero, portrait) |
| Resolution | Up to 4K | Higher = more detail, slower generation |

Effective prompts follow a structure: **subject + setting + lighting + style + mood + technical specs**. The prompting guide includes tested formulas for portraiture, product shots, landscapes, and abstract art.

### Cinematic Style Formula

`cinematic-style.md` documents a specific visual style for documentary-quality digital paintings: warm color grading, shallow depth of field, rim lighting, film grain texture. Used for Aldea soul avatars and portfolio imagery.

### Aldea Avatar Templates

`references/aldea-avatars.md` provides character templates for Soul Engine personas---consistent style prompts for generating avatar imagery that maintains identity across sessions and channels.

---

## Scripts

All scripts use `GEMINI_API_KEY` from environment.

| Script | Usage |
|--------|-------|
| `generate_image.py` | `python3 generate_image.py "A bronze-age craftsman at a forge"` |
| `edit_image.py` | `python3 edit_image.py input.png "Add dramatic rim lighting"` |
| `generate_with_references.py` | `python3 generate_with_references.py "Same style" --ref style.png` |
| `compose_images.py` | `python3 compose_images.py --images a.png b.png --prompt "Merge"` |
| `multi_turn_chat.py` | `python3 multi_turn_chat.py` (interactive) |
| `test_connection.py` | `python3 test_connection.py` (verify API key) |

---

## Requirements

- Python 3.9+
- `google-genai` (`pip install google-genai`)
- `GEMINI_API_KEY` environment variable
- `Pillow` for image manipulation (`pip install Pillow`)

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/design-media/nano-banana-pro ~/.claude/skills/
```
