# Compositing Operators Reference

## Syntax

```bash
magick background.png overlay.png -compose <Operator> -composite output.png
```

With positioning:
```bash
magick background.png overlay.png -geometry +X+Y -compose <Operator> -composite output.png
```

Multi-layer:
```bash
magick background.png \
  \( overlay1.png -geometry +10+20 \) -compose Over -composite \
  \( overlay2.png -geometry +200+50 \) -compose Over -composite \
  output.png
```

## Duff-Porter Alpha Compositing

| Operator | Result | Use Case |
|----------|--------|----------|
| `Over` | **Default.** Overlay on top, respecting alpha | Standard compositing, watermarks, overlays |
| `In` | Only where both exist (intersection) | Masking: clip overlay to background shape |
| `Out` | Only where overlay exists but background doesn't | Cookie-cutter: punch shape from overlay |
| `Atop` | Overlay on top, but only where background exists | Texture onto shaped region |
| `Xor` | Where either exists but not both | Exclude overlap region |
| `DstOver` | Background on top of overlay | Place behind existing content |
| `DstIn` | Background only where overlay exists | Use overlay as mask for background |
| `DstOut` | Background only where overlay doesn't exist | Punch overlay shape out of background |
| `DstAtop` | Background on top, only where overlay exists | Reverse Atop |
| `Clear` | Transparent everywhere | Erase regions |
| `Src` | Replace entirely with overlay | Full replacement |
| `Dst` | Keep background, ignore overlay | No-op (testing) |

## Mathematical Blend Operators

| Operator | Formula | Use Case |
|----------|---------|----------|
| `Multiply` | A * B | Darken, shadow effects, texture blending |
| `Screen` | 1 - (1-A)(1-B) | Lighten, glow effects |
| `Plus` | A + B (clamped) | Additive light, lens flares |
| `Minus` | A - B (clamped) | Subtract colors |
| `Add` | A + B (no clamp in HDRI) | Raw additive |
| `Subtract` | A - B (no clamp in HDRI) | Raw subtractive |
| `Difference` | \|A - B\| | Edge detection, change detection |
| `Exclusion` | A + B - 2AB | Softer Difference |
| `Divide` | A / B | Color correction, normalizing |
| `ModulusAdd` | (A + B) mod 1 | Wrapping addition |
| `ModulusSubtract` | (A - B) mod 1 | Wrapping subtraction |

## Lighting / Contrast Operators

| Operator | Effect | Use Case |
|----------|--------|----------|
| `Overlay` | Multiply darks, Screen lights | Contrast enhancement, texture overlay |
| `HardLight` | Like Overlay but swap layers | Dramatic contrast |
| `SoftLight` | Gentle dodge/burn | Subtle lighting adjustments |
| `PegtopLight` | Smoother SoftLight variant | Even softer lighting |
| `LinearLight` | Linear dodge/burn | Strong lighting |
| `VividLight` | Color dodge/burn | Extreme contrast |
| `PinLight` | Replace darks/lights selectively | Selective replacement |
| `HardMix` | Posterize by threshold | Graphic effects |

## Lighten / Darken

| Operator | Effect |
|----------|--------|
| `Lighten` | Keep brighter pixel |
| `Darken` | Keep darker pixel |
| `LightenIntensity` | Keep pixel with higher intensity (all channels) |
| `DarkenIntensity` | Keep pixel with lower intensity (all channels) |
| `ColorDodge` | Brighten background by overlay |
| `ColorBurn` | Darken background by overlay |
| `LinearDodge` | Additive brightening |
| `LinearBurn` | Subtractive darkening |

## HSL Component Operators

| Operator | Transfers | Use Case |
|----------|-----------|----------|
| `Hue` | Hue from overlay | Recolor without changing brightness |
| `Saturate` | Saturation from overlay | Adjust vibrancy |
| `Luminize` | Luminosity from overlay | Match brightness levels |
| `Colorize` | Hue + Saturation from overlay | Full color transfer |

## Special Operators

| Operator | Effect | Use Case |
|----------|--------|----------|
| `CopyOpacity` | Copy overlay as alpha mask | Apply grayscale mask (white=visible) |
| `CopyRed/Green/Blue` | Copy single channel | Channel manipulation |
| `Blend` | Weighted mix (needs `-define compose:args=X`) | Opacity control |
| `Dissolve` | Like Blend with alpha (needs `-define compose:args=X`) | Fade transitions |
| `Displace` | Use overlay as displacement map | Distortion effects |
| `ChangeMask` | Make matching pixels transparent | Chroma key |
| `Stereo` | Red-cyan anaglyph | 3D stereo pairs |
| `Mathematics` | Custom: `Ax*y + Bx + Cy + D` | Any custom blend |

## Argumented Operators

These require `-define compose:args=...`:

```bash
# Blend at 70% overlay opacity
magick bg.png fg.png -compose Blend -define compose:args=70 -composite out.png

# Dissolve at 50%
magick bg.png fg.png -compose Dissolve -define compose:args=50 -composite out.png

# Displace with X,Y amount
magick bg.png map.png -compose Displace -define compose:args=10x10 -composite out.png

# Custom Mathematics: A*Sc*Dc + B*Sc + C*Dc + D
magick bg.png fg.png -compose Mathematics -define compose:args='0,0.5,0.5,0' -composite out.png
```

## Common Recipes

```bash
# Simple overlay (default Over)
magick background.png overlay.png -geometry +50+100 -composite output.png

# Watermark at 30% opacity, bottom-right
magick photo.jpg watermark.png \
  -gravity SouthEast -geometry +10+10 \
  -compose Dissolve -define compose:args=30 \
  -composite output.jpg

# Multiply blend (darken/texture)
magick photo.jpg texture.png -compose Multiply -composite output.jpg

# Screen blend (lighten/glow)
magick photo.jpg glow.png -compose Screen -composite output.jpg

# Apply grayscale mask
magick source.png mask.png -alpha off -compose CopyOpacity -composite masked.png

# Soft light for subtle adjustments
magick photo.jpg adjustment.png -compose SoftLight -composite output.jpg

# Color transfer (keep luminosity, take color)
magick target.jpg color_source.jpg -compose Colorize -composite output.jpg

# Vignette via radial gradient mask
magick photo.jpg \
  \( +clone -fill black -colorize 100% \
     -fill white -draw "circle 400,300 400,10" \
     -blur 0x40 \) \
  -compose Multiply -composite vignette.jpg
```

## Gotchas

1. **Default is `Over`** — Reset with `-compose Over` between operations
2. **`-geometry` before `-composite`** — Order matters
3. **Alpha required** — Many operators need alpha channel; use `-alpha set` first
4. **Blend/Dissolve need args** — Will silently default to 100% without `-define compose:args=`
5. **Layer order** — First image is background, second is foreground
6. **CopyOpacity expects grayscale** — White = opaque, black = transparent
