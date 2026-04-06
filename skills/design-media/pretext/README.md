# Pretext

Text effects impossible with CSS alone — powered by [@chenglou/pretext](https://github.com/nicklockwood/pretext) and [opentype.js](https://opentype.js.org/).

Single-file HTML output. No build step. No framework.

## Effects

- **Height prediction** — accordion, masonry, virtualized lists
- **Shrinkwrap** — chat bubbles tighter than CSS can achieve
- **Obstacle routing** — text flows around draggable objects at 60fps
- **Typographic ASCII** — fluid simulations rendered as proportional characters
- **Calligrams** — words shaped as hearts, stars, spirals (SDF-based)
- **Glyph-mask calligrams** — any font glyph as calligram shape via pixel-mask technique
- **Letterbox gallery** — per-letter canvas grid with text fill and cursor displacement
- **Glyph path art** — SVG letterforms with stroke animation
- **Text on path** — per-glyph placement along Bezier curves
- **Variable font animation** — per-character weight/width waves
- **Glyph morphing** — letterform interpolation with contour-aware morphing
- **Illuminated manuscript** — living medieval pages with wet ink and vine reflow

## Acknowledgments

The **glyph-mask calligram** and **letterbox gallery** techniques were inspired by [Letterbox](https://www.letterbox.sh/) by [Charlie Clark](https://charlieclark.co/) — an interactive typography tool where each character is shaped entirely from smaller text. The pixel-mask rendering pipeline (canvas `fillText()` + `getImageData()` row scanning) and per-character cursor displacement physics were reverse-engineered from the Letterbox demo.
