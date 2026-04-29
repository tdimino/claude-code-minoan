# Minoan Glyphs — Custom PUA Font

14 Minoan pictographic glyphs mapped to Unicode Private Use Area codepoints (U+E500–U+E50D) for terminal rendering. SVG outlines built into TTF via fonttools.

## Glyph Registry

| Codepoint | Name | Design Source |
|-----------|------|---------------|
| U+E500 | HORNS OF CONSECRATION | Knossos architectural fragments |
| U+E501 | LABRYS | Palace labrys motifs, Arkalochori axe |
| U+E502 | MINOAN BULL | Bull-Leaping Fresco |
| U+E503 | KNOSSOS DOLPHIN | Queen's Megaron dolphin fresco |
| U+E504 | AKROTIRI SWALLOW | Spring Fresco, Akrotiri |
| U+E505 | SEATED CAT | Phaistos Disc CAT refined |
| U+E506 | SACRAL KNOT | Minoan ritual iconography |
| U+E507 | MINOAN LILY | Knossos lily fresco |
| U+E508 | RUNNING SPIRAL | Pottery and architectural motif |
| U+E509 | OCTOPUS | Marine Style pottery (LM IB) |
| U+E50A | WAVE BAND | Architectural frieze element |
| U+E50B | FIGURE-EIGHT SHIELD | Warrior iconography |
| U+E50C | MINOAN GODDESS | Palaikastro goddess figurines |
| U+E50D | CROCUS | Saffron Gatherer fresco |

## Build

```bash
python3 build.py            # Build MinoanGlyphs.ttf
python3 build.py --install  # Build + install to ~/Library/Fonts/
```

Requires `fonttools` (`uv pip install fonttools`).

## Ghostty Integration

Add to Ghostty config's font cascade:

```
font-family = Minoan Glyphs
```

Place after the primary font but before system fallbacks. Ghostty's cascade finds PUA characters in this font when standard fonts don't cover them.

## Test

```bash
# After installing, test in terminal:
printf ''  # Should render Horns of Consecration
printf ''  # Should render Knossos Dolphin
```

## Structure

```
scripts/minoan-glyphs/
  ├── build.py           # fonttools TTF builder (1024 UPM, monospace metrics)
  ├── svgs/              # Individual SVG outlines per glyph
  │   ├── horns.svg
  │   ├── labrys.svg
  │   ├── bull.svg
  │   ├── dolphin.svg
  │   ├── swallow.svg
  │   ├── cat.svg
  │   ├── sacral-knot.svg
  │   ├── lily.svg
  │   ├── spiral.svg
  │   ├── octopus.svg
  │   ├── wave.svg
  │   ├── shield.svg
  │   ├── goddess.svg
  │   └── crocus.svg
  ├── reference/         # Source fresco images + processing intermediates (gitignored)
  │   └── SOURCES.md     # Provenance and attribution (tracked)
  ├── MinoanGlyphs.ttf   # Built artifact
  └── README.md
```

## Design Notes

Glyphs are designed for monospace terminal rendering at 1024 units-per-em. SVG paths are simple geometric outlines — stylized silhouettes, not archaeological reproductions. The Y-axis is flipped during build to convert SVG coordinate space (top-left origin) to font coordinate space (bottom-left origin).

Each glyph references a specific artifact or fresco from Minoan Crete. The dolphin traces the Queen's Megaron profile. The bull captures the leaping pose. The goddess raises her arms in the Palaikastro stance. The crocus blooms as it does in the Saffron Gatherer fresco at Xeste 3.

## SVG Design Methodology

Bold silhouettes optimized for terminal rendering at 14–18px. Not archaeological reproductions—stylized ideograms that read at a glance.

- **15–50 anchor points** per glyph. Fewer = cleaner rasterization at small sizes.
- **Single contour preferred.** Compound shapes (body + eye) collapse to noise below 16px.
- **Minimum 125-unit features** (~12% of 1024 UPM em-square). Anything narrower than 1/8 em renders as a single antialiased pixel and disappears.
- **Squint test at 16px.** If you can't identify the animal at arm's length, the silhouette needs simplification.
- **Exaggerate diagnostic features.** The dolphin's dorsal fin is proportionally larger than life. The swallow's forked tail streamers are wider than anatomically correct. These are the features that distinguish the glyph from a generic blob.

## Vectorization Pipeline

For glyphs derived from photographic references:

1. **Crop** — `magick in.jpg -crop WxH+X+Y out.jpg` to isolate the motif
2. **Color isolation** — `magick in.jpg -colorspace HSL -channel G -separate sat.png` to extract by saturation/hue
3. **Threshold to B&W** — `magick in.png -threshold 50% out.pbm` for a 1-bit mask
4. **Vectorize** — `vtracer --input in.png --output out.svg --colormode binary` (preferred for grayscale) or `potrace input.pbm -s -o output.svg` (for clean B&W)
5. **Manual cleanup** — Reduce anchor points, merge paths, enforce 125-unit minimums
6. **Build font** — `python3 build.py --install`

Automated tracing works well for high-contrast motifs. Fresco subjects with color bleed (e.g., the dolphin's blue merging with patina) require hand-crafted SVGs informed by the reference.

## Reference Sources

Source images are in `reference/` (gitignored, ~34MB). See `reference/SOURCES.md` for provenance and attribution. All source photographs are Wikimedia Commons CC BY-SA 4.0.
