# Astryx Hero Pattern

Hover-reactive editorial hero using depth-map parallax displacement. A static image (bust, statue, product) appears to shift in 3D space as the cursor moves.

## Source

- **URL**: https://indigo-type-231733.framer.app/astryx
- **Engine**: Unicorn Studio v2.1.6 (no-code WebGL shader tool, runtime license: null)
- **Platform**: Framer

## Technique

Single-tap inverse displacement shader (Robin Delaporte lineage). Two textures: color image + grayscale depth map. The depth value at each pixel modulates a pointer-relative UV offset, creating the illusion of 3D parallax without real geometry.

## Tags

`hero`, `shader`, `hover`, `dark`, `editorial`, `depth-parallax`, `WebGL`, `statue`

## Key Properties

| Property | Value |
|----------|-------|
| Effect family | Depth-map displacement |
| Shader passes | 1 (single-tap) |
| GPU cost | Low (~0.5ms/frame) |
| Pointer input | `pointermove` (W3C Pointer Events) |
| DPR strategy | Clamped to 1.5 |
| Reduced motion | Static `<img>` fallback |
| Typography | Instrument Sans 500, -0.03em, SIL OFL 1.1 |

## Cross-References

- **Implementation skill**: `rocaille-shader --mode astryx-statue` (Scope B)
- **Design reference**: `~/.claude/skills/minoan-frontend-design/references/astryx-hero.md`
- **Depth contract**: `astryx-depth-1.0` (see plan)
- **Sibling pattern**: [Fluid-DOM](fluid-dom-pattern.md) (stable fluid over live DOM)
- **Shader ancestor**: https://codepen.io/robin-dela/pen/vaQQNL
