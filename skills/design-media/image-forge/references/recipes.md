# Image Forge Recipes

## Borders and Frames

```bash
# Solid color border (10px)
magick input.jpg -bordercolor '#333333' -border 10 output.jpg

# Border with different sizes (top/bottom x left/right)
magick input.jpg -bordercolor white -border 20x40 output.jpg

# Inner border (outline effect)
magick input.jpg -shave 5x5 -bordercolor red -border 5 output.jpg

# Rounded corners
magick input.png \
  \( +clone -alpha extract \
     -draw 'fill black polygon 0,0 0,15 15,0 fill white circle 15,15 15,0' \
     \( +clone -flip \) -compose Multiply -composite \
     \( +clone -flop \) -compose Multiply -composite \
  \) -alpha off -compose CopyOpacity -composite rounded.png

# Photo frame with mat
magick input.jpg \
  -bordercolor '#f5f0e8' -border 40 \
  -bordercolor '#2c2c2c' -border 3 \
  output.jpg
```

## Shadows

```bash
# Drop shadow
magick input.png \
  \( +clone -background black -shadow 60x5+5+5 \) \
  +swap -background none -layers merge +repage shadow.png

# Inner shadow (inset)
magick input.png \
  \( +clone -alpha extract -negate -blur 0x5 -shade 120x45 -normalize \
     +clone -alpha extract -compose Multiply -composite \
  \) -compose In -composite inner_shadow.png
```

## Watermarks

```bash
# Text watermark, bottom-right, semi-transparent
magick photo.jpg \
  -fill 'rgba(255,255,255,0.3)' -gravity SouthEast \
  -font Helvetica -pointsize 24 -annotate +10+10 '© 2026 Tom di Mino' \
  output.jpg

# Image watermark at 25% opacity
magick photo.jpg watermark.png \
  -gravity SouthEast -geometry +10+10 \
  -compose Dissolve -define compose:args=25 \
  -composite output.jpg

# Tiled/repeating watermark
magick photo.jpg \
  \( watermark.png -resize 200x -alpha set -channel A -evaluate set 25% +channel \
     -write mpr:tile +delete \) \
  \( -size 4000x4000 tile:mpr:tile \) \
  -compose Over -composite output.jpg
```

## Social Media Sizing

```bash
# Instagram square (1080x1080) — fill and center crop
magick input.jpg -resize 1080x1080^ -gravity center -extent 1080x1080 instagram.jpg

# Instagram story (1080x1920) — fill and center crop
magick input.jpg -resize 1080x1920^ -gravity center -extent 1080x1920 story.jpg

# Twitter/X header (1500x500) — fill and center crop
magick input.jpg -resize 1500x500^ -gravity center -extent 1500x500 twitter_header.jpg

# OG image (1200x630) — fill and center crop
magick input.jpg -resize 1200x630^ -gravity center -extent 1200x630 og_image.jpg

# Favicon multi-size ICO
magick input.png -resize 256x256 -define icon:auto-resize=256,128,64,48,32,16 favicon.ico

# Pad to size (letterbox with background color)
magick input.jpg -resize 1080x1080 -gravity center -background '#1a1a2e' -extent 1080x1080 padded.jpg
```

## Thumbnails and Grids

```bash
# Thumbnail strip
magick input.jpg -thumbnail 150x150^ -gravity center -extent 150x150 thumb.jpg

# Contact sheet from directory
magick montage *.jpg -geometry 200x200+5+5 -tile 4x -background white contact.jpg

# Labeled contact sheet
magick montage *.jpg -geometry 200x200+5+5 -tile 4x \
  -label '%f' -font Helvetica -pointsize 10 contact.jpg

# Filmstrip (horizontal strip)
magick montage *.jpg -geometry 200x150+2+2 -tile x1 -background black filmstrip.jpg
```

## Color Effects

```bash
# Sepia tone
magick input.jpg -sepia-tone 80% sepia.jpg

# Black and white (proper luminance)
magick input.jpg -colorspace Gray output.jpg

# High contrast B&W
magick input.jpg -colorspace Gray -sigmoidal-contrast 10x50% output.jpg

# Duotone (grayscale + tint)
magick input.jpg -colorspace Gray -fill '#4a90d9' -tint 100 duotone.jpg

# Vintage/faded look
magick input.jpg \
  -modulate 105,80,100 \
  -fill '#704214' -colorize 15% \
  -sigmoidal-contrast 3x60% \
  vintage.jpg

# Cross-process look
magick input.jpg \
  -channel R -level 10%,90% +channel \
  -channel G -level 0%,80% +channel \
  -channel B -level 20%,100% +channel \
  cross_process.jpg

# Color splash (keep one color, rest B&W)
# Step 1: Extract red channel mask
magick input.jpg -colorspace HSL -channel R -separate +channel \
  -threshold 15% -negate mask.png
# Step 2: Apply (example — adjust mask for target color)
magick input.jpg \( +clone -colorspace Gray \) mask.png -compose Over -composite splash.jpg
```

## Text Effects

```bash
# Text with shadow
magick input.jpg \
  -font Helvetica-Bold -pointsize 48 \
  -fill 'rgba(0,0,0,0.5)' -annotate +22+62 'Title' \
  -fill white -annotate +20+60 'Title' \
  output.jpg

# Outlined text
magick input.jpg -font Helvetica-Bold -pointsize 48 \
  -stroke black -strokewidth 3 -fill none -annotate +20+60 'Text' \
  -stroke none -fill white -annotate +20+60 'Text' output.jpg

# Text on semi-transparent bar
magick input.jpg \
  -fill 'rgba(0,0,0,0.6)' -draw 'rectangle 0,440 800,500' \
  -fill white -font Helvetica -pointsize 24 \
  -gravity South -annotate +0+15 'Caption text here' \
  output.jpg

# Curved text (requires SVG path)
magick -size 500x500 xc:none \
  -font Helvetica -pointsize 24 -fill white \
  -draw "text 0,0 'Curved text around arc'" \
  -distort Arc 180 curved.png
```

## Image Comparison

```bash
# Side by side
magick input1.jpg input2.jpg +append sidebyside.jpg

# Top and bottom
magick input1.jpg input2.jpg -append topbottom.jpg

# Difference highlight
magick input1.jpg input2.jpg -compose Difference -composite diff.jpg

# Animated comparison (toggle between two)
magick -delay 100 input1.jpg input2.jpg -loop 0 comparison.gif
```

## Sprites and Icons

```bash
# Horizontal sprite sheet
magick icon1.png icon2.png icon3.png icon4.png +append sprite.png

# Grid sprite sheet (4 columns)
magick montage icon*.png -geometry 64x64+0+0 -tile 4x -background none sprite.png

# Extract single sprite from sheet (column 2, row 1, 64x64 grid)
magick sprite.png -crop 64x64+64+0 +repage single.png

# Resize all icons to uniform size
magick mogrify -resize 64x64 -gravity center -background none -extent 64x64 icons/*.png
```

## Background Operations

```bash
# Remove background (rembg)
rembg i input.jpg output.png

# Remove background with alpha matting
rembg i -a input.jpg output.png

# Replace background color
magick input.png -background '#1a1a2e' -alpha remove -alpha off output.jpg

# Transparent to white
magick input.png -background white -alpha remove output.jpg

# Make specific color transparent
magick input.png -fuzz 15% -transparent white output.png
```

## Batch Patterns

```bash
# Resize all to max 1200px wide
magick mogrify -path output/ -resize '1200x>' *.jpg

# Convert all PNG to JPEG at 85%
magick mogrify -path output/ -format jpg -quality 85 *.png

# Strip metadata from all
magick mogrify -strip *.jpg

# Auto-orient all (fix phone rotation)
magick mogrify -auto-orient *.jpg

# Parallel batch (4 workers)
ls *.jpg | xargs -P 4 -I {} magick {} -resize 800x600 -quality 85 output/{}

# Add watermark to all
for f in *.jpg; do
  magick "$f" watermark.png \
    -gravity SouthEast -geometry +10+10 \
    -compose Dissolve -define compose:args=25 \
    -composite "watermarked/$f"
done
```

## Format Optimization

```bash
# JPEG: progressive, stripped, 85% quality
magick input.png -interlace Plane -strip -quality 85 output.jpg

# PNG: maximum compression
magick input.jpg -quality 95 -strip output.png

# WebP: lossy at 80%
magick input.jpg -quality 80 output.webp

# WebP: lossless
magick input.png -define webp:lossless=true output.webp

# AVIF: high quality
magick input.jpg -quality 50 output.avif

# PDF from images
magick page1.jpg page2.jpg page3.jpg -quality 85 document.pdf

# GIF from frames
magick -delay 10 frame_*.png -loop 0 animation.gif

# Animated GIF optimization
magick animation.gif -layers Optimize optimized.gif
```

## Canvas Creation

```bash
# Solid color canvas
magick -size 800x600 xc:'#1a1a2e' canvas.png

# Gradient (vertical)
magick -size 800x600 gradient:'#1a1a2e'-'#4a90d9' gradient.png

# Radial gradient
magick -size 800x600 radial-gradient:'#ffffff'-'#000000' radial.png

# Transparent canvas
magick -size 800x600 xc:none canvas.png

# Checkerboard (transparency indicator)
magick -size 800x600 pattern:checkerboard checkerboard.png

# Noise texture
magick -size 800x600 xc: +noise Gaussian noise.png
```

## Metadata

```bash
# Strip all metadata
magick input.jpg -strip output.jpg

# Set DPI
magick input.jpg -density 300 -units PixelsPerInch output.jpg

# Set comment
magick input.jpg -set comment 'Processed by image-forge' output.jpg

# Read dimensions
magick identify -format "%wx%h" input.jpg

# Full info dump
magick identify -format "Size: %wx%h\nFormat: %m\nColorspace: %r\nDepth: %z-bit\nFilesize: %b\n" input.jpg
```
