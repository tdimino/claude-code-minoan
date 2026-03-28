# Gemini SVG-as-Code Generation

Gemini 3.1 Pro generates clean, hand-editable SVG XML — not traced raster "node soup." The output is structured vector code with named `<g>` groups, proper accessibility attributes, and CSS animations.

## Core Principle

Gemini writes SVG as XML code, leveraging its code generation strength. This produces 1-3KB files with logical groupings, proper viewBox, and CSS custom properties — fundamentally different from auto-tracing a raster image into thousands of unstructured path nodes.

## Prompt Patterns

### Request SVG Code, Not an Image
```
Generate SVG XML code for a [description]. Output raw SVG markup with:
- Proper viewBox and dimensions
- Named <g> groups for logical sections
- CSS custom properties for colors (fill="var(--primary)")
- Clean, human-readable structure
```

### Specify Constraints
```
Create an SVG icon of [subject]:
- viewBox="0 0 24 24"
- Stroke width: 2px
- Colors: only use var(--fg) and var(--bg)
- Group related paths in named <g> elements
- Include title and desc for accessibility
```

### With CSS Animation
```
Generate an SVG loading spinner with inline CSS animation:
- 24x24 viewBox
- Rotating circle with dash animation
- @keyframes defined within <style> block
- prefers-reduced-motion media query
```

## What Works Well

| Category | Quality | Notes |
|----------|---------|-------|
| Icons and logos | Excellent | Clean paths, consistent stroke weight |
| UI components (spinners, progress) | Excellent | CSS animations inline |
| Data visualization | Good | Bar/line charts without JS libraries |
| Technical diagrams | Good | Properly routed arrows, labels |
| Simple characters | Good | Requires explicit structure guidance |
| Complex illustrations | Fair | May need iteration |

## Conversational Iteration

Gemini supports refining SVGs through dialogue:
- "Make the lines thicker"
- "Change the primary color to #3B82F6"
- "Simplify the shape — reduce path complexity"
- "Add a hover state that scales up 1.1x"
- "Make it responsive to dark mode via CSS custom properties"

## Design System Integration

Request CSS custom properties for theming:
```svg
<svg viewBox="0 0 24 24">
  <style>
    :root { --primary: #3B82F6; --secondary: #64748B; }
    @media (prefers-color-scheme: dark) {
      :root { --primary: #60A5FA; --secondary: #94A3B8; }
    }
  </style>
  <circle fill="var(--primary)" cx="12" cy="12" r="10"/>
</svg>
```

## How to Invoke

SVG-as-code requires Gemini's **text generation** API (chat completions), not the image generation endpoint. The image endpoint produces raster PNG/JPEG — it cannot output raw SVG XML.

```bash
# Option 1: Direct Gemini text API (generates SVG XML as text output)
# Use the Gemini API or context7 MCP to prompt for SVG code generation

# Option 2: Claude itself can write SVG XML when given specific constraints
# Describe the desired SVG with viewBox, colors, grouping structure

# NOT this — nano-banana-pro generates raster images, not SVG code:
# python3 ~/.claude/skills/nano-banana-pro/scripts/generate_image.py "..." --output robot.svg  # WRONG
```

For pixel-art SVGs from raster images, use Pipeline 3's rect conversion approach instead:
```bash
python3 scripts/pixel_art_generator.py input.png --grid 20 --colors 4 --merge --remove-bg -o char.svg
```

## Model Comparison

| Model | SVG Quality | Notes |
|-------|------------|-------|
| Gemini 3.1 Pro | Best | Three-tier reasoning, interactive SVGs |
| Gemini 2.5 Pro | Great | Complex scenes, good structure |
| Gemini 2.5 Flash | Good | Fast, simpler output |
| Claude (direct) | Fair | Can write SVG but less geometric precision |
| DALL-E/Midjourney | N/A | Raster only, no SVG output |

## Anti-Patterns

- Do NOT auto-trace raster images to SVG — produces "node soup" (thousands of unstructured paths)
- Do NOT ask for "an SVG image" — ask for "SVG XML code"
- Do NOT use generic image generators for vector output — they rasterize everything
