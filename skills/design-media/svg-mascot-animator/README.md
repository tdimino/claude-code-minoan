# SVG Mascot Animator

Generate animated pixel-art SVG mascots from images or text descriptions. Characters are built entirely from `<rect>` elements and animated via GSAP timelines — reverse-engineered from [ayotomcs.me/claude-mascot](https://ayotomcs.me/claude-mascot).

## Pipeline

```
Image → ImageMagick trim → pixel_art_generator.py → SVG rects → animation_builder.py → Standalone HTML
```

### From a description

```bash
# 1. Generate pixel art with nano-banana-pro
python3 ~/.claude/skills/nano-banana-pro/scripts/generate_image.py \
  "16-bit pixel art fox standing, side view, white background, 4 colors" \
  --output /tmp/fox.png

# 2. Trim whitespace (mandatory — AI images have large borders)
magick /tmp/fox.png/generated_image_0_0.jpg -fuzz 15% -trim +repage /tmp/fox-trimmed.png

# 3. Convert to SVG rects with body-part grouping
python3 scripts/pixel_art_generator.py /tmp/fox-trimmed.png \
  --grid 20 --colors 4 --merge --remove-bg -o mascot.svg

# 4. Add id and animate → standalone HTML
sed -i '' 's/<svg /<svg id="mascot" /' mascot.svg
python3 scripts/animation_builder.py --preset bounce --svg mascot.svg --render -o demo.html
```

### From an existing image

```bash
magick character.png -fuzz 15% -trim +repage /tmp/trimmed.png
python3 scripts/pixel_art_generator.py /tmp/trimmed.png --grid 24 --colors 6 --merge --remove-bg -o mascot.svg
sed -i '' 's/<svg /<svg id="mascot" /' mascot.svg
python3 scripts/animation_builder.py --preset walk --svg mascot.svg --render -o mascot.html
```

## Animation Presets

| Preset | Motion | Best For |
|--------|--------|----------|
| `idle` | Eye blink + gentle bob | Any pose |
| `bounce` | Jump up and land | Any pose |
| `wave` | Right hand wave gesture | Characters with hands |
| `walk` | Leg squash + body translate | Standing characters |
| `walk-and-bounce` | Bounce then walk cycle | Standing characters |

```bash
python3 scripts/animation_builder.py --list
python3 scripts/animation_builder.py --preset idle --svg-id my-character
```

## Key Techniques

- **Rects only** — every pixel maps to one `<rect>`. `shapeRendering="crispEdges"` prevents anti-aliasing
- **Auto body-part grouping** — position heuristics assign `id` attributes (head, body, legs, eyes, hands) for GSAP targeting
- **Run-length merging** — adjacent same-color pixels merge into wider rects (~40-60% file size reduction)
- **Walk targets `#legs rect`** — individual rect elements inside the legs group, not the group itself
- **Variable frame timing** — frame switcher supports per-frame ms durations for natural rhythm

## Dependencies

- Python 3.10+ with Pillow (`uv pip install Pillow`)
- ImageMagick 7 (`brew install imagemagick`)
- GSAP 3 via CDN (included in standalone HTML template)
- Optional: `nano-banana-pro` skill for AI character generation

## Structure

```
svg-mascot-animator/
├── SKILL.md
├── scripts/
│   ├── pixel_art_generator.py   # Image → quantized pixel grid → SVG <rect> elements
│   └── animation_builder.py     # GSAP presets + frame switcher + HTML renderer
├── templates/
│   └── mascot-standalone.html   # Self-contained HTML template with GSAP CDN
└── references/
    ├── gsap-timeline-patterns.md     # Walk cycle, bounce, wave recipes
    ├── pixel-art-svgs.md             # Rect grid technique, color quantization
    └── ayotomcs-deconstruction.md    # Full reverse-engineering of the reference
```

## Credits

Reverse-engineered from [Ayotomi Adewuyi's Claude mascot animation](https://ayotomcs.me/claude-mascot) ([@ayotomcs](https://x.com/ayotomcs)).
