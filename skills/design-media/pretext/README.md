# pretext

Generate self-contained HTML pages using [Pretext](https://github.com/chenglou/pretext)—a pure-arithmetic text measurement library by **Cheng Lou** that bypasses DOM layout reflow entirely. Enables text effects impossible with CSS alone.

## Credit

**Library**: [`@chenglou/pretext`](https://github.com/chenglou/pretext) by [Cheng Lou](https://github.com/chenglou) (MIT License, v0.0.2)

**Creative demos**: [somnai-dreams/pretext-demos](https://github.com/somnai-dreams/pretext-demos) by [@somnai_dreams](https://x.com/somnai_dreams)—the editorial engine, fluid smoke, wireframe torus, calligram engine, and shrinkwrap showdown demos that informed the patterns in this skill.

## What Pretext Does

Pretext measures text height and line breaks without touching the DOM. It uses canvas `measureText` as ground truth, then does all layout via pure arithmetic. The result: `layout()` runs in ~0.0002ms per text block. 100% accuracy across Chrome, Safari, Firefox.

## Effect Categories

| Category | What it does |
|----------|-------------|
| **Height Prediction** | Instant text height for accordions, masonry, virtualized lists |
| **Shrinkwrap** | Exact tightest width for chat bubbles—tighter than CSS `fit-content` |
| **Obstacle Routing** | Text flowing around draggable circles, logos, arbitrary shapes |
| **Typographic ASCII** | Fluid smoke, 3D wireframes, particles rendered as proportional characters |
| **Calligrams** | Words rendered as shapes (heart, star, spiral) using their own letters |
| **Multi-column Editorial** | Magazine layouts with headline fitting, pull quotes, drop caps |

## Usage

```
/pretext fluid smoke ASCII art with gold characters on black
/pretext chat bubbles that shrinkwrap tighter than CSS
/pretext calligram — the word "ocean" shaped like a wave
/pretext editorial layout with text flowing around draggable circles
```

Output is always a single self-contained HTML file. No build step, no framework.

## Templates

Working standalone pages in `assets/templates/`:

| Template | Effect | Size |
|----------|--------|------|
| `height-prediction.html` | Accordion with Pretext height prediction | 144 lines |
| `shrinkwrap-bubbles.html` | Chat bubbles with exact minimum width | 179 lines |
| `editorial-engine.html` | Multi-column flow around draggable orbs | 276 lines |
| `typographic-ascii.html` | Fluid smoke as proportional ASCII | 205 lines |
| `calligram.html` | Words rendered as shapes with spring animation | 227 lines |

## References

| Document | Content |
|----------|---------|
| `references/api-reference.md` | Full API surface with types and caveats |
| `references/typographic-ascii.md` | Palette building, brightness estimation, grid rendering |
| `references/obstacle-routing.md` | Column flow, circle intervals, orb physics, headline fitting |
| `references/calligram-shapes.md` | SDF functions, character measurement, spring animation |

## Validation

```bash
python3 scripts/validate_pretext.py output.html
```

Checks for: ESM import, module script, named fonts (no `system-ui`), viewport meta, resize handler, `document.fonts.ready`, `requestAnimationFrame`, touch handlers, no `setInterval` for animation, no framework imports.
