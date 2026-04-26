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
  ├── MinoanGlyphs.ttf   # Built artifact
  └── README.md
```

## Design Notes

Glyphs are designed for monospace terminal rendering at 1024 units-per-em. SVG paths are simple geometric outlines — stylized silhouettes, not archaeological reproductions. The Y-axis is flipped during build to convert SVG coordinate space (top-left origin) to font coordinate space (bottom-left origin).

Each glyph references a specific artifact or fresco from Minoan Crete. The dolphin traces the Queen's Megaron profile. The bull captures the leaping pose. The goddess raises her arms in the Palaikastro stance. The crocus blooms as it does in the Saffron Gatherer fresco at Xeste 3.
