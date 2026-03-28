# Sprite Generation Tool Landscape (March 2026)

## Tool Comparison

| Tool | Approach | Strengths | Weaknesses | Cost |
|------|----------|-----------|------------|------|
| **SEELE** (seeles.ai) | Own SEELE-V2-SPRITE model | 98% style consistency, temporal coherence, character identity vector, 15-30s generation | Closed platform | Free tier |
| **Ludo** (ludo.ai) | Full platform | Pose editor, VFX, animation presets, variation chaining, final frame control for loops | Platform lock-in | ~$50/1K credits |
| **SpriteCook** (spritecook.ai) | Prompt to playable | 4-direction isometric, Unity export, 4-step flow | Early stage | Beta |
| **AutoSprite** (autosprite.io) | One image → full set | MCP server for Claude Code, batch processing, isometric mode | Very early (21 followers) | Credits |
| **FalSprite** (@OdinLovis) | Nano Banana 2 via fal.ai | Fast, text to game-ready, went viral (1,150 likes) | Inherits NB2 walk cycle weakness | Pay-per-use |
| **TechHalla** workflow | Video → frame select → sheet | Most viral approach (1,815 likes, 2,716 bookmarks, 261K views) | Manual frame selection | Free (Freepik) |
| **BitArt** (Rust CLI) | OpenAI iterative edits | Frame-aware GIF, terminal preview, multi-model | Limited animation | API costs |
| **Rosebud** (lab.rosebud.ai) | AI game dev platform | Free, meta-approach (generates its own prompts) | Less sprite-focused | Free |
| **PixelLab** (pixellab.ai) | Dedicated pixel art AI | Skeleton-based controls, 4/8 directional, MCP server | Pixel art only | Paid |
| **Retro Diffusion** (Scenario.com) | 3 specialized models | Native 256x256, palette control, RD Plus/Tile/Animation | Platform-specific | Paid |

## Key Gaps (TernSprites Analysis)

| Need | Current State |
|------|---------------|
| Consistent walk cycles from image alone | No tool nails this |
| End-to-end automated pipeline | 3-4 tools stitched manually |
| Engine-ready output with atlas metadata | Most output raw PNGs |
| Automated video-to-spritesheet | Still mostly manual |
| Style consistency across animations | Hit or miss |

## The Emerging Consensus Pipeline (March 2026)

1. **Reference image** via Nano Banana Pro / GPT Image for art direction
2. **Static poses** (4 cardinals) via image model, derive diagonals
3. **Walk cycles and animations** via video model (Veo 3.1, Kling v3)
4. **Frame extraction** (ffmpeg) + **alignment** (OpenCV) + **stitching**
5. **Atlas generation** (JSON/XML for engine import)

This is exactly what sprite-forge's Pipelines 1 + 2 automate.

## Model Rankings for Pixel Art

Per Promptomania (Jan 2026): DALL-E 3 > GPT Image 1 > Midjourney v6.1 > FLUX 1.1 Pro > SDXL 1.0 > Nano Banana Pro

Per chongdashu (Mar 2026): Nano Banana 2 surprisingly good at pixel art, better than NBP for isometric sheets. GPT Image 1.5 best for identity preservation and transparency.

## MCP Integration Options

- **AutoSprite**: Has MCP server for Claude Code integration
- **PixelLab**: Has MCP server for vibe coding
- **pixel-plugin** (93 stars): Claude Code plugin for Aseprite control via natural language

## Standard Sprite Specifications

- **Dimensions**: Power of 2 (16, 32, 64, 128, 256px)
- **Color palettes**: 4-16 colors for retro, full RGBA for modern
- **Frame counts**: Walk 6-8, Run 6-8, Idle 4-6, Attack 5-8
- **Timing**: Walk 60-120ms, Idle 100-200ms per frame
- **Formats**: 8-bit indexed PNG or 32-bit RGBA PNG

## Sources

- TernSprites comparative review: tern.papermascot.com/blog/ai-spritesheet-tools-2026
- chongdashu pipeline: github.com/chongdashu/vibe-isometric-sprites
- SEELE docs: seeles.ai
- Retro Diffusion: scenario.com
