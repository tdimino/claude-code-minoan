# Fluid-DOM Pattern

Pointer-reactive Navier-Stokes stable fluid simulation applied as WebGL overlays to live DOM elements (images, headings, sections). Velocity persists after the pointer stops, producing organic flowing distortion.

## Source

- **URL**: https://codepen.io/editor/fand/pen/019d61f5-aadf-7e18-851c-0ebd317146c7
- **Library**: `@vfx-js/core` by amagi.dev (license UNVERIFIED)
- **Lineage**: Pavel DoGreat's WebGL-Fluid-Simulation (MIT)

## Technique

Full Navier-Stokes simulation: curl → vorticity → divergence → pressure solve → gradient subtract → advect. Six shader passes per frame with framebuffer ping-pong. Pointer delta splats velocity into a persistent field via Gaussian kernel.

## Tags

`shader`, `hover`, `fluid`, `editorial`, `WebGL`, `DOM-overlay`, `Navier-Stokes`, `interactive`

## Key Properties

| Property | Value |
|----------|-------|
| Effect family | Stable fluid simulation |
| Shader passes | 6+ per frame |
| GPU cost | Medium-High (~2-4ms at half-res) |
| Pointer input | `pointermove` (W3C Pointer Events) |
| Velocity state | Persistent (flows after pointer stops) |
| Pattern scope | Multiple sections (editorial page) |
| Reduced motion | Clear velocity texture + skip passes |

## Cross-References

- **Implementation skill**: `rocaille-shader --mode fluid-dom` (documentation-only, Scope A)
- **Shader reference**: `~/.claude/skills/rocaille-shader/references/fluid-dom.md`
- **Sibling pattern**: [Astryx Hero](astryx-hero-pattern.md) (depth-parallax on single hero)
- **MIT lineage**: https://github.com/PavelDoGreat/WebGL-Fluid-Simulation
- **Theory**: Jos Stam, "Real-Time Fluid Dynamics for Games" (GDC 2003)
