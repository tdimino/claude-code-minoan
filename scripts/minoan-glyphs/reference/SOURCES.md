# Reference Sources

Photographic references used for glyph SVG design. All images are Wikimedia Commons, licensed CC BY-SA 4.0.

## Knossos Dolphin (U+E503)

- **Subject**: Queen's Megaron dolphin fresco, Palace of Knossos
- **Source**: https://commons.wikimedia.org/wiki/File:Dolphin_Mural.jpg
- **License**: CC BY-SA 4.0
- **Used for**: Body profile, dorsal fin proportions, snout-to-flukes silhouette

## Akrotiri Swallow (U+E504)

- **Subject**: Spring Fresco swallows, Building Delta (Room Delta 2), Akrotiri, Thera
- **Source**: https://commons.wikimedia.org/wiki/File:Fresco_of_the_Spring.jpg
- **License**: CC BY-SA 4.0
- **Used for**: Wing spread, forked tail streamer proportions, diving posture

## Processing Pipeline

Reference images were processed through this pipeline before hand-crafting the final SVGs:

1. `magick in.jpg -crop WxH+X+Y out.jpg` — isolate motif from fresco
2. `magick in.jpg -colorspace HSL -channel G -separate sat.png` — saturation channel extraction
3. `magick in.png -threshold 50% out.pbm` — binary mask for tracing
4. `vtracer` / `potrace` — automated vectorization (used as reference, not final output)
5. Manual SVG construction — 15-50 point silhouettes with 125-unit minimum features

The final SVGs are hand-crafted ideograms informed by the references, not direct traces.
