# image-forge

Precision image editing skill for Claude Code. Three-tier routing architecture: deterministic tools (ImageMagick 7, sips, rembg, Pillow), AI semantic editing (Gemini/nano-banana-pro), and vision analysis (Claude Read).

## When to Use

Any image manipulation task: resize, crop, composite, color adjust, format convert, batch process, contact sheets, watermarks, background removal, text overlay.

**Core principle:** Use ImageMagick when you know exactly what to do to the pixels. Use AI when the edit requires understanding what is in the image.

## Dependencies

- **ImageMagick 7** (`brew install imagemagick`)
- **Python 3** with Pillow (`uv pip install pillow`)
- **rembg** for background removal (`uv pip install rembg`)
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

## Scripts

### image_pipeline.py (core)

Converts a declarative JSON spec into a single chained `magick` command. No intermediate files, no fragile shell pipelines.

```bash
# From file
python3 scripts/image_pipeline.py spec.json

# From stdin
echo '{"input":"in.jpg","output":"out.jpg","steps":[{"op":"resize","width":800}]}' | python3 scripts/image_pipeline.py -

# Dry run (print command only)
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
python3 scripts/smart_crop.py photo.jpg --target 1200x630 --gravity north --output cropped/
```

### batch_ops.py

```bash
python3 scripts/batch_ops.py *.jpg --op resize --width 800 --output resized/ --parallel 4
python3 scripts/batch_ops.py *.png --op format --to webp --quality 80
python3 scripts/batch_ops.py *.jpg --op thumbnail --width 200 --height 200
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

# Add watermark at 25% opacity
magick photo.jpg wm.png -gravity SouthEast -geometry +10+10 -compose Dissolve -define compose:args=25 -composite out.jpg

# Remove background
rembg i input.png output.png

# Convert to WebP at quality 80
magick in.jpg -quality 80 out.webp
```

## Installation

```bash
# Copy to Claude Code skills
cp -R image-forge/ ~/.claude/skills/image-forge/

# Verify ImageMagick
magick --version
```

The skill is model-invocable and triggers automatically on any image editing intent.
