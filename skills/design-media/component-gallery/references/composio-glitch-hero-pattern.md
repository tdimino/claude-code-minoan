# Composio Glitch Hero Pattern

Generative pixel-glitch canvas backdrop behind hero typography. Rectangular blocks of blue/cyan/pink/white animate like corrupted bitmap data or a paused video signal, framing centered display type on a near-black ground.

> Not yet in the RLAMA semantic collection (built from `.staging/` scrapes)—discoverable via Read/Grep only, same status as the Astryx pattern.

## Source

- **URL**: https://composio.dev/
- **Engine**: Custom `<canvas>` on a Next.js site (context type not externally inspectable; the block-fill aesthetic needs only a 2D context)
- **Platform**: Custom React / Tailwind v4 / shadcn tokens

## Technique

A single full-width canvas (viewport-width × ~644px; the canvas itself is static inside an absolutely-positioned `inset-y-0 z-0` wrapper behind the hero content) paints clusters of axis-aligned rectangles in the brand palette, concentrated toward the top corners and thinning toward center, leaving a calm zone for the headline. Blocks appear, shift, and decay in stepped (non-eased) jumps—the glitch reads because motion is *quantized*, not smooth. The same visual language is exported as static PNGs for section art and echoed in ASCII display type, giving the motif three cost tiers (live canvas → static image → text).

## Tags

`hero`, `canvas`, `generative`, `glitch`, `pixel`, `dark`, `developer-tool`, `bitmap`

## Key Properties

| Property | Value |
|----------|-------|
| Effect family | Generative block-glitch (2D canvas fill) |
| Render loop | Stepped/quantized updates; ~12–24fps reads best |
| GPU cost | Minimal (axis-aligned block fills; no shader work required) |
| Pointer input | None—time-driven, not pointer-reactive |
| DPR strategy | Scale canvas by `devicePixelRatio`, blocks stay axis-aligned |
| Reduced motion | Freeze to a single painted frame, or swap static PNG of same composition |
| No-JS fallback | Static PNG (site uses this approach for section art) |
| Palette | Brand blues + cyan + pink + white on `#0f0f0f`; never rainbow |
| Typography over it | Large grotesk (64px at desktop), white, centered in the calm zone |

## Cross-References

- **Design reference**: `~/.claude/skills/minoan-frontend-design/references/composio-signature-techniques.md` (art-direction rules, three fidelity tiers)
- **Tokens**: `~/.claude/skills/minoan-frontend-design/references/composio-design-tokens.md`
- **Sibling pattern**: [Astryx Hero](astryx-hero-pattern.md) (pointer-reactive depth-parallax—the opposite input model: Astryx responds to cursor, this responds to time)
- **Implementation skills**: `threejs-particle-canvas` (canvas scaffolding), `grainient` (gradient/noise textures)
