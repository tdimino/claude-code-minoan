# Sprite Forge

Generate game-ready sprites, SVG characters, ASCII art, animated mascots, and isometric turnarounds from images or text descriptions.

## Output Modes

| Mode | What it produces | Key script |
|------|-----------------|------------|
| **Isometric Turnaround** | 8-way directional sprites from a single reference image | `isometric_pipeline.py` |
| **Sprite Sheet** | Game-ready sheets with JSON/XML atlas metadata from video | `video_to_spritesheet.py` |
| **SVG Character** | Clean vector SVGs (Gemini code-gen) or pixel-art rect SVGs | `pixel_art_generator.py` |
| **ASCII Art** | Static (image-to-ASCII) + animated (frame-based React TSX components) | `image_to_ascii.py` |
| **Animated Mascot** | GSAP-animated pixel-art characters (HTML/React/SVG) | `animation_builder.py` |

## Quick Start

```bash
# Isometric 8-way turnaround
python3 scripts/isometric_pipeline.py --reference character.png --output-dir ./iso/

# Video → sprite sheet with atlas
python3 scripts/video_to_spritesheet.py --input walk.mp4 --fps 12 --cell-size 64x64 --atlas json

# Image → ASCII art
python3 scripts/image_to_ascii.py photo.png --mode color --width 80

# Image → pixel-art SVG → GSAP animation
magick input.png -fuzz 15% -trim +repage /tmp/trimmed.png
python3 scripts/pixel_art_generator.py /tmp/trimmed.png --grid 20 --colors 4 --merge --remove-bg -o mascot.svg
python3 scripts/animation_builder.py --preset walk-and-bounce --svg-id mascot

# Stitch frames into sprite sheet
python3 scripts/stitch_spritesheet.py --input-dir frames/ --cols 8 --atlas json -o sheet.png

# Remove green screen
python3 scripts/chroma_key.py --input sprite.png --output sprite_alpha.png --despill
```

## Inventory

**9 scripts** | **11 references** | **1 template** | **1 asset**

### Scripts

| Script | Purpose |
|--------|---------|
| `isometric_pipeline.py` | Chongdashu 7-step isometric turnaround orchestrator |
| `video_to_spritesheet.py` | Video → ffmpeg frames → stitch → atlas |
| `stitch_spritesheet.py` | Combine images into sprite sheet with JSON/XML atlas |
| `chroma_key.py` | Green screen removal with despill and feather |
| `image_to_ascii.py` | Multi-mode ASCII/Unicode art converter |
| `pixel_art_generator.py` | Image → pixel-art SVG rects with body-part grouping |
| `animation_builder.py` | GSAP timeline presets (idle, bounce, wave, walk, typing) |
| `split_spritesheet.py` | Split sprite sheet into individual frames |
| `generate_walk_video.py` | HEVC walk cycle video for lil-agents dock companion |

### References

| File | Topic |
|------|-------|
| `isometric-turnaround.md` | Chongdashu 8-way pipeline, prompts, model comparison |
| `chroma-key-transparency.md` | Model transparency capabilities, #00FF00 vs alpha |
| `video-to-spritesheet.md` | Video-first animation, practitioner workflows, atlas formats |
| `gemini-svg-generation.md` | Gemini SVG-as-code prompt patterns |
| `ascii-art-techniques.md` | Density ramps, half-block Unicode, external tools |
| `sprite-generation-landscape.md` | March 2026 tool comparison (SEELE, Ludo, SpriteCook, etc.) |
| `pixel-art-svgs.md` | Rect grid conversion, run-length optimization |
| `gsap-timeline-patterns.md` | GSAP animation recipes and easing functions |
| `ayotomcs-deconstruction.md` | ayotomcs.me reference system reverse-engineering |
| `lil-agents-character-spec.md` | macOS dock companion video format spec |
| `ascii-animation-components.md` | Frame-based ASCII animation React components (shadcn pattern) |

## Dependencies

- **Pillow**: `uv pip install Pillow`
- **ImageMagick 7**: `magick -trim`, `-fuzz`
- **ffmpeg**: Video frame extraction
- **rembg** (optional): `uv pip install rembg`
- **jp2a** (optional): `brew install jp2a`
- **nano-banana-pro skill**: AI image generation/editing

## Research Sources

Built from research across Exa, Twitter/X, Firecrawl, and direct repo analysis (March 27, 2026):

- [chongdashu/vibe-isometric-sprites](https://github.com/chongdashu/vibe-isometric-sprites) — 7-step isometric pipeline
- [ayotomcs.me/claude-mascot](https://ayotomcs.me/claude-mascot) — original GSAP mascot reference
- SEELE, Ludo, SpriteCook, AutoSprite, FalSprite, TechHalla — landscape analysis
- Gemini SVG-as-code (houtini.com, glbgpt.com) — clean vector generation

## History

Expanded from `svg-mascot-animator` (Mar 25, 2026) which covered a single pipeline (image → pixel-art SVG → GSAP animation). Renamed to `sprite-forge` (Mar 27, 2026) with 5 output modes, 5 new scripts, and 6 new reference files incorporating the March 2026 state of the art in AI-assisted sprite generation.
