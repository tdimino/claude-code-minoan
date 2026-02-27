# Custom Asset Generation Workflow

Generate custom icons, illustrations, and graphics matching Aldea's blueprint aesthetic using AI image generation, vectorization, and post-processing.

## Pipeline Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌────────────────┐    ┌──────────────┐
│ Nano Banana Pro │ -> │ ImageMagick      │ -> │ Potrace/       │ -> │ SVG Cleanup  │
│ (Gemini 3 Pro)  │    │ (Preprocessing)  │    │ Vectorization  │    │ & Styling    │
└─────────────────┘    └──────────────────┘    └────────────────┘    └──────────────┘
        ↓
   Raster PNG           Posterize/Crop         Trace to SVG         Apply Blueprint
   (512x512+)           Reduce Colors          Clean Paths          Colors
```

## Method 1: AI Image → SVG Pipeline

### Step 1: Generate with Nano Banana Pro

Use the `nano-banana-pro` skill with icon-optimized prompts:

```bash
# Prompt template for blueprint-style icons
"A minimalist icon of [SUBJECT], flat design, 3-4 solid colors only,
dark blue background (#0a0f1a), cyan accent (#00d4ff),
clean geometric shapes, no gradients, no texture,
centered composition, high contrast, vector art style"
```

**Key prompt modifiers for vectorization:**
- "flat design" or "flat illustration"
- "3-4 solid colors only"
- "no gradients, no texture"
- "clean geometric shapes"
- "vector art style"
- "minimalist icon"

### Step 2: Preprocess with ImageMagick

```bash
# Posterize to reduce colors (makes cleaner vectors)
magick input.png -posterize 6 -colors 6 posterized.png

# Optional: Increase contrast for sharper edges
magick posterized.png -contrast-stretch 2%x1% high-contrast.png

# Resize to optimal tracing size (larger = more detail)
magick high-contrast.png -resize 1024x1024 prepared.png

# Remove background if needed (make transparent)
magick prepared.png -fuzz 10% -transparent "#0a0f1a" no-bg.png
```

### Step 3: Vectorize with Potrace

```bash
# Install potrace (if not present)
brew install potrace

# Convert PNG to PBM (potrace input format)
magick prepared.png -threshold 50% input.pbm

# Trace to SVG
potrace input.pbm -s -o output.svg

# For color images, use autotrace or Inkscape CLI:
inkscape --export-type=svg --actions="select-all;object-to-path" input.png
```

### Step 4: Apply Blueprint Styling

Post-process SVG to apply Aldea color tokens:

```bash
# Replace colors with blueprint palette using sed
sed -i '' \
  -e 's/#000000/#0a0f1a/g' \
  -e 's/#ffffff/#00d4ff/g' \
  -e 's/#808080/#1e3a5f/g' \
  output.svg
```

---

## Method 2: Direct SVG Generation (SVGMaker MCP)

The SVGMaker MCP Server enables direct text-to-SVG without raster intermediaries.

### Setup

```bash
# Add to Claude Code MCP config
# In ~/.claude/mcp_servers.json:
{
  "svgmaker": {
    "command": "npx",
    "args": ["-y", "@GenWaveLLC/svgmaker-mcp"]
  }
}
```

### Usage

```
Generate an SVG icon: "A brain with neural network connections,
minimalist line art, single stroke weight, cyan color (#00d4ff)
on transparent background"
```

**Advantages:**
- Direct vector output (no tracing artifacts)
- Cleaner paths, smaller file size
- Instant integration with Claude Code

---

## Method 3: Hybrid Workflow (Best Quality)

For highest-quality custom assets:

### 1. Generate Reference with Nano Banana Pro
```
"Blueprint schematic of a transformer neural network,
technical diagram style, cyan lines on dark blue background,
geometric nodes and connections, engineering drawing aesthetic"
```

### 2. Convert to SVG with SVGMaker
Use the raster as a reference, describe the icon to SVGMaker for clean vector recreation.

### 3. Manual Refinement (Optional)
Open in Inkscape/Figma for final adjustments:
- Align to pixel grid
- Reduce node count
- Apply consistent stroke widths

---

## Blueprint Color Application

Apply these transformations to any generated SVG:

```css
/* Primary icon colors */
--icon-stroke: #00d4ff;      /* Cyan lines */
--icon-fill: #0d1420;        /* Dark fill */
--icon-accent: #60a5fa;      /* Blue accent */
--icon-muted: #1e3a5f;       /* Subtle elements */

/* Optional glow effect for hero icons */
filter: drop-shadow(0 0 8px rgba(0, 212, 255, 0.5));
```

---

## Automation Script

Create custom icons in batch:

```bash
#!/bin/bash
# generate-icon.sh - Generate blueprint-styled icon

SUBJECT="$1"
OUTPUT="$2"

# Step 1: Generate with Gemini (requires API key)
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateImage" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Minimalist icon of '"$SUBJECT"', flat design, 3 solid colors, dark blue #0a0f1a background, cyan #00d4ff accent, clean geometric shapes, no gradients, centered"
  }' > temp.png

# Step 2: Preprocess
magick temp.png -posterize 4 -colors 4 -resize 512x512 processed.png

# Step 3: Vectorize
potrace processed.pbm -s -o "$OUTPUT"

# Step 4: Apply blueprint colors
sed -i '' 's/#000000/#00d4ff/g' "$OUTPUT"

echo "Generated: $OUTPUT"
```

---

## Icon Generation Prompts by Domain

### AI/ML Research
```
"Neural network node icon, geometric brain shape,
connected dots and lines, blueprint technical style"

"Transformer attention head, abstract geometric,
flowing connections between nodes, minimal"

"Audio waveform icon, sound wave visualization,
smooth sine curves, technical diagram style"
```

### Healthcare
```
"Heartbeat monitor icon, ECG line pattern,
medical device aesthetic, clean geometric"

"DNA helix icon, double spiral,
molecular biology style, simplified"
```

### Business
```
"Growth chart icon, ascending bars,
arrow pointing up, financial dashboard style"

"Network hub icon, central node with connections,
organizational chart style"
```

### Wellness
```
"Meditation pose icon, seated figure silhouette,
peaceful balance, minimal lines"

"Sunrise over mountain icon, horizon line,
journey/transformation symbol"
```

---

## Quality Metrics

Track these for generated icons:

| Metric | Target | Tool |
|--------|--------|------|
| Node count | < 500 | Inkscape |
| File size | < 50KB | `ls -la` |
| Color count | 3-5 | ImageMagick `identify` |
| Viewbox | 24x24 or 48x48 | SVG source |

---

## Integration with Aldea Slidedeck

Place generated icons in:
```
assets/scaffold/public/images/custom-icons/
```

Use in components:
```tsx
<img
  src="/images/custom-icons/neural-network.svg"
  alt="Neural Network"
  className="w-8 h-8"
  style={{ filter: 'drop-shadow(0 0 4px rgba(0, 212, 255, 0.4))' }}
/>
```

Or inline for color control:
```tsx
import NeuralNetworkIcon from '../public/images/custom-icons/neural-network.svg';

<NeuralNetworkIcon className="w-8 h-8 text-blueprint-cyan" />
```

---

## Tools Required

| Tool | Purpose | Install |
|------|---------|---------|
| **Nano Banana Pro** | AI image generation | `nano-banana-pro` skill |
| **ImageMagick** | Image preprocessing | `brew install imagemagick` |
| **Potrace** | Bitmap vectorization | `brew install potrace` |
| **Inkscape** | SVG editing (CLI) | `brew install --cask inkscape` |
| **SVGMaker MCP** | Direct SVG generation | MCP server config |
| **SVGO** | SVG optimization | `npm install -g svgo` |

---

## Example: Generate "Soul Engine" Icon

```bash
# 1. Generate with optimized prompt
nano-banana-pro generate \
  "Minimalist icon of a glowing orb with concentric rings,
   representing consciousness and AI soul,
   blueprint technical style, cyan #00d4ff glow,
   dark navy #0a0f1a background,
   clean geometric circles, ethereal yet precise"

# 2. Preprocess
magick soul-engine-raw.png \
  -posterize 4 \
  -colors 4 \
  -fuzz 5% -transparent "#0a0f1a" \
  -resize 512x512 \
  soul-engine-processed.png

# 3. Vectorize
potrace soul-engine-processed.pbm -s -o soul-engine.svg

# 4. Optimize
svgo soul-engine.svg -o soul-engine-optimized.svg

# 5. Move to assets
mv soul-engine-optimized.svg assets/scaffold/public/images/custom-icons/
```

This workflow enables fully custom, on-brand icon generation without relying on generic icon libraries.
