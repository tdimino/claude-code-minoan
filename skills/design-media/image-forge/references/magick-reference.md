# ImageMagick 7 Reference

## Command Structure

```
magick [input...] [settings] [operators] [output]
```

**Settings** persist until changed (`-font`, `-fill`, `-gravity`, `-compose`, `-quality`, `-background`, `-channel`, `-colorspace`, `-density`, `-depth`, `-fuzz`).
**Operators** execute immediately then are forgotten (`-resize`, `-crop`, `-blur`, `-rotate`, `-annotate`, `-draw`, `-composite`).

```bash
magick input.jpg -resize 800x600 -quality 85 -strip output.jpg
```

## Geometry Strings

| Syntax | Meaning |
|--------|---------|
| `WxH` | Fit within box, preserve aspect ratio |
| `WxH!` | Force exact dimensions (distort if needed) |
| `WxH>` | Shrink only if larger |
| `WxH<` | Enlarge only if smaller |
| `WxH^` | Fill box (minimum dimension matches, may overflow) |
| `W%` or `W%xH%` | Percentage scale |
| `@N` | Total pixel area limit |
| `+X+Y` | Offset from origin or gravity anchor |
| `x:y` | Aspect ratio target |
| `x:y^` | Crop to aspect ratio |
| `x:y#` | Pad to aspect ratio |

Inline read-time shortcuts:
```bash
magick 'image.jpg[800x600]'       # resize on read
magick 'image.jpg[600x400+100+50]' # crop on read
magick 'animation.gif[0]'          # single frame
magick 'animation.gif[0-3]'        # frame range
```

**Shell escaping**: `>`, `<`, `^` need quoting or escaping:
```bash
magick input.jpg -resize '800x600>' output.jpg
```

## Resize

```bash
# Fit within 800x600, preserve aspect ratio
magick input.jpg -resize 800x600 output.jpg

# Force exact dimensions
magick input.jpg -resize 800x600! output.jpg

# Shrink only if larger
magick input.jpg -resize '800x600>' output.jpg

# Fill then center-crop to exact size
magick input.jpg -resize 800x600^ -gravity center -extent 800x600 output.jpg

# Percentage
magick input.jpg -resize 50% output.jpg

# Thumbnail (strips metadata, optimized for small output)
magick input.jpg -thumbnail 200x200 output.jpg

# Scale (fast, no interpolation -- pixel art)
magick input.jpg -scale 200% output.png

# With specific filter
magick input.jpg -filter Lanczos -resize 800x600 output.jpg
```

## Crop

```bash
# Crop WxH at offset +X+Y from top-left
magick input.jpg -crop 600x400+100+50 +repage output.jpg

# Center crop
magick input.jpg -gravity center -crop 600x400+0+0 +repage output.jpg

# Auto-trim whitespace/border
magick input.jpg -trim +repage output.jpg

# Trim with fuzz tolerance
magick input.jpg -fuzz 10% -trim +repage output.jpg

# Pad to exact size (extend canvas)
magick input.jpg -gravity center -background white -extent 1000x1000 output.jpg

# Shave equal border from all sides
magick input.jpg -shave 20x20 output.jpg
```

**Always use `+repage` after `-crop`** to reset virtual canvas offset.

## Compositing

```bash
# Overlay at position
magick background.png foreground.png -geometry +50+100 -composite output.png

# With blend mode
magick background.png overlay.png -compose Multiply -composite output.png

# With opacity (70% overlay)
magick background.png overlay.png -compose Blend -define compose:args=70 -composite output.png

# Multi-layer (parenthesized sub-expressions)
magick background.png \
  \( overlay1.png -geometry +10+20 \) -compose Over -composite \
  \( overlay2.png -geometry +200+50 \) -compose Over -composite \
  output.png
```

See `compositing.md` for the full operator reference.

## Alpha Channel

```bash
# Activate alpha (set to opaque if new)
magick input.jpg -alpha set output.png

# Remove alpha (flatten onto color)
magick input.png -background white -alpha remove output.jpg

# Make color transparent
magick input.png -fuzz 15% -transparent white output.png

# Apply grayscale mask (white=visible, black=transparent)
magick source.png mask.png -alpha off -compose CopyOpacity -composite masked.png

# Extract alpha as grayscale
magick input.png -alpha extract alpha_mask.png

# Flatten transparency onto color
magick input.png -background "#ff6600" -flatten output.jpg
```

**IM7 gotcha**: `-alpha off` permanently removes alpha data. Use `-alpha deactivate`/`-alpha activate` for temporary toggle.

## Color Space

```bash
# Convert to CMYK (print)
magick input.jpg -colorspace CMYK output.tiff

# Convert to grayscale
magick input.jpg -colorspace Gray output.jpg

# Separate HSL channels
magick input.jpg -colorspace HSL -separate hsl_%d.png

# Recombine channels
magick hsl_0.png hsl_1.png hsl_2.png -set colorspace HSL -combine -colorspace sRGB output.jpg
```

**`-colorspace`** converts pixel data. **`-set colorspace`** relabels metadata without transforming values.

## Color Adjustment

```bash
# Modulate: Brightness, Saturation, Hue (100 = no change)
magick input.jpg -modulate 110,130,100 output.jpg  # +10% bright, +30% sat

# Brightness-contrast
magick input.jpg -brightness-contrast 10x20 output.jpg

# Levels (black-point, white-point, gamma)
magick input.jpg -level 5%,95% output.jpg

# Auto-level / normalize
magick input.jpg -auto-level output.jpg
magick input.jpg -normalize output.jpg

# Gamma correction
magick input.jpg -gamma 1.2 output.jpg

# Sigmoidal contrast (strength x midpoint%)
magick input.jpg -sigmoidal-contrast 5x50% output.jpg

# Tint/colorize
magick input.jpg -fill "#ff6600" -colorize 30% output.jpg

# Sepia
magick input.jpg -sepia-tone 80% output.jpg

# Negate (invert)
magick input.jpg -negate output.jpg
```

**`-modulate` arg order is B,S,H** -- not H,S,L.

## Channel Operations

```bash
# Process single channel
magick input.jpg -channel R -negate +channel output.jpg

# Per-channel levels
magick input.jpg -channel R -level 10%,90% +channel output.jpg

# Swap channels
magick input.jpg -channel red,blue -separate -swap 0,1 -combine output.jpg

# IM7 channel syntax:
# red<=>blue   swap
# red=>green   copy red to green
# red=50%      set red to constant
```

## Text and Annotation

```bash
# Simple text
magick input.jpg -fill white -pointsize 36 -annotate +10+50 'Hello World' output.jpg

# With font and gravity
magick input.jpg -font Helvetica-Bold -fill white -pointsize 48 \
  -gravity south -annotate +0+10 'Caption' output.jpg

# Outlined text (draw twice: outline then fill)
magick input.jpg -font Helvetica-Bold -pointsize 48 \
  -stroke black -strokewidth 3 -fill none -annotate +20+60 'Text' \
  -stroke none -fill white -annotate +20+60 'Text' output.jpg

# Auto-sized label
magick -background none -fill white -font Helvetica -size 400x label:'Title' label.png

# Word-wrapped caption
magick -background none -fill white -font Helvetica -size 400x200 \
  caption:'Long text that wraps automatically.' caption.png
```

**Gravity values**: `NorthWest`, `North`, `NorthEast`, `West`, `Center`, `East`, `SouthWest`, `South`, `SouthEast`. Reset with `+gravity`.

## Drawing

```bash
# Filled rectangle
magick input.jpg -fill "rgba(0,0,0,0.5)" -draw "rectangle 10,10 200,100" output.jpg

# Outline rectangle
magick input.jpg -fill none -stroke red -strokewidth 2 -draw "rectangle 10,10 200,100" output.jpg

# Rounded rectangle
magick input.jpg -fill blue -draw "roundrectangle 10,10 200,100 15,15" output.jpg

# Circle (center_x,center_y edge_x,edge_y)
magick input.jpg -fill "rgba(255,0,0,0.5)" -draw "circle 250,250 250,50" output.jpg

# Line
magick input.jpg -stroke red -strokewidth 3 -draw "line 0,0 500,500" output.jpg

# Create canvas from scratch
magick -size 500x500 xc:white \
  -fill none -stroke black -strokewidth 2 \
  -draw "rectangle 50,50 450,450" output.png
```

## Blur and Sharpen

```bash
# Gaussian blur (radius x sigma -- sigma is the key parameter)
magick input.jpg -blur 0x3 output.jpg

# Sharpen
magick input.jpg -sharpen 0x1 output.jpg

# Unsharp mask (radius x sigma + amount + threshold)
magick input.jpg -unsharp 0x0.5+1+0.05 output.jpg

# Motion blur (radius x sigma + angle)
magick input.jpg -motion-blur 0x5+45 output.jpg
```

## Format Conversion and I/O

```bash
# Convert format
magick input.png output.jpg

# JPEG quality (1-100)
magick input.png -quality 85 output.jpg

# PNG compression (0-9 mapped to quality 0-90)
magick input.jpg -quality 95 output.png

# Strip all metadata
magick input.jpg -strip output.jpg

# Set DPI
magick input.jpg -density 300 output.jpg

# WebP conversion
magick input.jpg -quality 80 output.webp

# AVIF conversion
magick input.jpg -quality 50 output.avif

# Pipe support
magick logo: gif:- | magick - -resize 200% output.jpg
```

## Batch Processing

```bash
# mogrify: in-place batch (use -path for non-destructive)
magick mogrify -path output/ -resize 800x600 *.jpg
magick mogrify -path output/ -format png -resize 50% *.jpg
magick mogrify -path output/ -quality 85 -strip -auto-orient *.jpg

# Shell loop with custom naming
for f in *.jpg; do
  magick "$f" -resize 800x600 -quality 85 "thumb_${f}"
done

# Parallel processing
ls *.jpg | xargs -P 4 -I {} magick {} -resize 800x600 output/{}
```

**`mogrify` without `-path` overwrites originals.**

## Identify (Inspection)

```bash
# Dimensions
magick identify -format "%wx%h" input.jpg

# Detailed info
magick identify -format "Size: %wx%h\nFormat: %m\nColorspace: %r\nDepth: %z-bit\n" input.jpg

# Verbose (full dump)
magick identify -verbose input.jpg
```

## Image Stacks

Parentheses create sub-image-lists for isolated processing:

```bash
magick input.jpg \( +clone -blur 0x8 \) -compose Overlay -composite output.jpg

# Key operators:
# +clone       duplicate last image
# -clone N     duplicate image at index N
# -delete N    remove image at index N
# +swap        swap last two images
```

## Color Specification Formats

```
#rgb, #rrggbb, #rrggbbaa     Hex (fastest)
rgb(255,0,0)                  Functional
rgba(255,0,0,0.5)             With alpha
hsl(120,100%,50%)             HSL
hsla(120,100%,50%,0.5)        HSL with alpha
cmyk(0,0,0,100%)              CMYK
gray(50%)                     Grayscale
none / transparent             Fully transparent
```

Named colors: `red`, `green`, `blue`, `cyan`, `magenta`, `yellow`, `black`, `white`, `gray`, `orange`, `gold`, `navy`, `teal`, plus 700+ X11/SVG names.

## Montage

```bash
# Thumbnail grid
magick montage *.jpg -geometry 200x200+5+5 -tile 4x -background white contact.jpg

# With labels
magick montage *.jpg -geometry 200x200+5+5 -tile 4x -label '%f' -font Helvetica -pointsize 10 contact.jpg
```

## Common Gotchas

1. **`+repage` after `-crop`** -- Virtual canvas offset persists without it
2. **`-modulate` order is B,S,H** -- Not H,S,L
3. **`-alpha off` is permanent in IM7** -- Use `-alpha deactivate`/`-alpha activate` instead
4. **Shell escaping for `>`, `<`, `^`** -- Quote geometry: `-resize '800x600>'`
5. **sRGB vs linear RGB** -- Resize works in linear RGB by default; can cause darkening
6. **HDRI builds** -- Pixel values are floating point; affects threshold ops
7. **HEIC odd-width corruption** -- Use `-define heic:even-size=true`
8. **`%` in text** -- Special in `-annotate`/`-label` (property escape); use `%%` for literal
9. **`+` vs `-` prefix** -- `+` resets/disables, `-` enables (e.g., `+antialias` disables)
10. **Order matters** -- Settings persist, operators execute immediately
