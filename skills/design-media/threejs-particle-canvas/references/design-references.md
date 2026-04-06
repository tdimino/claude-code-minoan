# Design References — Interactive Canvas Experiences

Exemplary interactive canvas experiences for aesthetic calibration. Study these before generating canvases or spinners. Each demonstrates specific design principles worth extracting.

## Instance (bryhaw.com/instance)

The primary reference for `threejs-particle-canvas`. Six-phase narrative particle canvas exploring AI consciousness.

**What makes it effective:**
- **Typography**: Space Mono (monospace) for phase text — technical without being cold
- **Color strategy**: Cool `#a8d8ff` / warm `#ffd080` — genuine temperature contrast drives emotional arc
- **Interaction model**: Observe and explore, never control. Auto-camera with 4s cooldown after user input
- **Signature moment**: Simultaneity reveal — camera crane-shot pulls back to show 30 parallel instances. The "moment you'd describe to someone"
- **Background**: Rich off-black `#050508` (never pure black), subtle fog, star field

**Principles to extract:**
- Every design decision derives from the concept
- Unequal phase durations create rhythm; equal durations create monotony
- The final phase prepares the first (cycle is a breath, not a loop)

## Vellum v2 (vellum.linxule.com)

Interactive generative canvas by Xule Lin. Full-screen, dark, typographically refined.

**What makes it effective:**
- **Typography**: Cormorant (display serif) + Noto Serif JP (CJK) + IBM Plex Mono (UI metadata) — three fonts, three registers, zero conflict
- **Color strategy**: Near-black background `#060508`, content emerges from darkness
- **Interaction model**: Minimal chrome, hidden cursor, sound toggle — the canvas IS the interface
- **Spatial composition**: Metadata pushed to corners (bottom-left, bottom-right), content claims the center

**Principles to extract:**
- Cormorant is an excellent display serif for contemplative experiences (free, variable weight)
- IBM Plex Mono reads well at small sizes for ambient metadata
- Zero-chrome design: when the experience is the interface, every UI element is a distraction
- Sound integration adds dimension without requiring visual complexity

**Font stack recommendation**: For canvases that need both narrative elegance and technical grounding:
```css
--font-display: 'Cormorant', Georgia, serif;
--font-mono: 'IBM Plex Mono', 'Space Mono', monospace;
--font-cjk: 'Noto Serif JP', serif; /* if multilingual */
```

## Common Aesthetic Principles

Across both references (and the best interactive canvas work generally):

1. **Dark backgrounds are never pure black.** Use `#050508`, `#060508`, `#0a0a12` — rich off-blacks with subtle color temperature
2. **Typography is structural, not decorative.** Font choice encodes the experience's register: monospace = technical/observational, serif = contemplative/narrative
3. **Interaction respects the viewer.** The viewer discovers, they don't configure. Auto-pilot with gentle override capability
4. **Sound is optional but significant.** When present, it transforms a visual experience into an environment. Always toggleable, never autoplay
5. **Performance is aesthetic.** Smooth 60fps is part of the design — dropped frames break the illusion faster than a wrong color
