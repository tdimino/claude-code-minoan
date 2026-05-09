# image-forge

Precision image editing skill for Claude Code. Three-tier routing architecture: deterministic tools (ImageMagick 7, sips, Pillow), AI background removal (transparent-background), AI semantic editing (Gemini/nano-banana-pro), and vision analysis (Claude Read).

## When to Use

Any image manipulation task: resize, crop, composite, color adjust, format convert, batch process, contact sheets, watermarks, background removal, text overlay.

**Core principle:** Use ImageMagick when you know exactly what to do to the pixels. Use AI when the edit requires understanding what is in the image.

## Dependencies

- **ImageMagick 7** (`brew install imagemagick`)
- **Python 3** with Pillow (`uv pip install pillow`)
- **transparent-background** for AI background removal (`uv pip install transparent-background`)
- **sips** (macOS built-in)

## Structure

```
image-forge/
├── SKILL.md                  # Main skill file (routing table, script docs, recipes)
├── scripts/
│   ├── image_pipeline.py     # JSON spec -> single magick command (core)
│   ├── image_info.py         # Image metadata as JSON
│   ├── smart_crop.py         # Gravity-based fill+crop
│   ├── batch_ops.py          # Parallel batch processing
│   └── montage_builder.py    # Contact sheets and thumbnail grids
└── references/
    ├── magick-reference.md   # Complete ImageMagick 7 CLI reference
    ├── compositing.md        # 70+ compositing operators
    └── recipes.md            # 30+ ready-to-use recipes
```

## Background Removal

Three methods, routed by quality needs:

| Method | When | Quality |
|--------|------|---------|
| `transparent-background` | Complex foreground (hair, translucent edges, concave regions) | Smooth alpha, no fringing |
| `magick -transparent white -fuzz N%` | Simple shapes on pure white, quick-and-dirty | Fast but aliased edges |
| `magick floodfill` | Remove background from corners only | Only hits connected regions |

```python
from transparent_background import Remover
from PIL import Image

remover = Remover()
img = Image.open("input.jpg").convert("RGB")
out = remover.process(img, type="rgba")
out.save("output.png")
```

Then trim: `magick output.png -trim +repage final.png`

## Scripts

### image_pipeline.py (core)

Converts a declarative JSON spec into a single chained `magick` command. No intermediate files, no fragile shell pipelines.

```bash
python3 scripts/image_pipeline.py spec.json
python3 scripts/image_pipeline.py spec.json --dry-run
```

Supports 30+ operations: resize, crop, trim, annotate, composite, rotate, blur, sharpen, modulate, levels, gamma, colorize, sepia, grayscale, border, shadow, transparent, and more.

### image_info.py

```bash
python3 scripts/image_info.py photo.jpg                # Full JSON metadata
python3 scripts/image_info.py photo.jpg --field width   # Single field
```

### smart_crop.py

```bash
python3 scripts/smart_crop.py photo.jpg --target 800x600 --gravity center
```

### batch_ops.py

```bash
python3 scripts/batch_ops.py *.jpg --op resize --width 800 --output resized/ --parallel 4
```

### montage_builder.py

```bash
python3 scripts/montage_builder.py *.jpg --cols 4 --thumb 200x200 --label --output grid.jpg
```

## Quick Examples

```bash
# Resize to fit within 800px width
magick in.jpg -resize 800 out.jpg

# Center crop to exact dimensions
magick in.jpg -resize 800x600^ -gravity Center -extent 800x600 out.jpg

# Remove background (AI)
python3 -c "
from transparent_background import Remover
from PIL import Image
Remover().process(Image.open('in.jpg').convert('RGB'), type='rgba').save('out.png')
"

# Convert to WebP at quality 80
magick in.jpg -quality 80 out.webp
```

## Installation

```bash
# Copy to Claude Code skills
cp -R image-forge/ ~/.claude/skills/image-forge/

# Install dependencies
brew install imagemagick
uv pip install --system pillow transparent-background

# Verify
magick --version
python3 -c "from transparent_background import Remover; print('ok')"
```

The skill is model-invocable and triggers automatically on any image editing intent.
