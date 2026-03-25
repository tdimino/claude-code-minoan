# ayotomcs.me Deconstruction

Full reverse-engineering of the animated SVG mascot system built by Ayotomi Adewuyi (@tomiwadoesux).

## Creator Profile

- **Name**: Wale-Durojaye Ayotomiwa
- **Title**: Design Engineer / AI Engineer
- **Site**: ayotomcs.me
- **GitHub**: tomiwadoesux (25 public repos, versioned portfolio: v121→v127)
- **Stack**: Next.js, Tailwind, GSAP, Framer Motion

## Characters Found

### 1. Claude Mascot (ayotomcs.js)

The only character component across all repo versions. Present in:
- `v127/components/ui/ayotomcs.js` (canonical, 256 lines)
- `v126/app/components/ayotomcs.js`
- `v124/components/ayotomcs.js` (older, black fill, 211x210)

**Anatomy** (v127):
- ViewBox: `374 x 320`
- Rendered: `21 x 20` px (tiny — "Built by" signature widget)
- Color: single `#71717a` (zinc-500)
- Elements:
  - `#Hat` — Two `<path>` elements tracing Claude's top-hat silhouette
  - `#code` (Groups 67/68/69) — Left bracket, right bracket, diagonal slash built from stacked `<rect>` elements
- Total elements: ~30 rects + 2 paths

**Animation** (GSAP):
```js
// 5-step rotation shake, infinite loop, 2s pause between
shakeTimeline.current = gsap.timeline({ repeat: -1, repeatDelay: 2 });
shakeTimeline.current
  .to(svgRef.current, { rotation: -8, duration: 0.2, ease: "power1.inOut" })
  .to(svgRef.current, { rotation: 12, duration: 0.12, ease: "power1.inOut" })
  .to(svgRef.current, { rotation: -8, duration: 0.1, ease: "power1.inOut" })
  .to(svgRef.current, { rotation: 8, duration: 0.1, ease: "power1.inOut" })
  .to(svgRef.current, { rotation: 0, duration: 0.1, ease: "power1.inOut" });
```

**Hover interaction**:
- Enter: Shake pauses, code group slides up 250px (`y: -250`)
- Leave: Shake resumes, code group returns

### 2. EDH Series Characters (separate project)

From the homepage description: "Characters are animated through sprite sheets for that frame-by-frame cartoon feel, generated across expressions and angles with Nano Banana because assets were limited."

**Key insight**: The creator uses Nano Banana Pro (Gemini) to generate character poses matching an existing illustration style, then converts them to sprite sheets. This is exactly our pipeline.

**Stack**: Next.js, Tailwind, GSAP ScrollTrigger, Framer Motion, Spritesheet Animation, Nano Banana Pro.

## Design Origin: Figma

Evidence the Claude mascot was designed in Figma:
1. **Rect IDs**: `Rectangle 117`, `Rectangle 123`, etc. — Figma's auto-naming convention
2. **Group IDs**: `Group 67`, `Group 68`, `Group 69`, `Group 70` — Figma layer groups
3. **Non-integer coordinates**: `x="92.9004"`, `y="38.373"` — Figma exports at 1x with sub-pixel precision
4. **Mixed elements**: `<path>` for complex shapes (hat silhouette) alongside `<rect>` for simple blocks (code brackets)
5. **No `shapeRendering="crispEdges"`** — Figma SVG export doesn't add this

**Workflow**: Design in Figma → Export SVG → Paste into React JSX → Add GSAP animation code.

## Architecture Patterns

### React Component Pattern
```jsx
"use client";
import { useRef, useEffect } from "react";
import gsap from "gsap";

export default function Character() {
  const svgRef = useRef(null);
  const partRef = useRef(null);
  const timelineRef = useRef(null);

  useEffect(() => {
    gsap.set(svgRef.current, { transformOrigin: "50% 50%" });
    timelineRef.current = gsap.timeline({ repeat: -1, repeatDelay: 2 });
    // ... animation setup
    return () => timelineRef.current?.kill();
  }, []);

  return <svg ref={svgRef} viewBox="0 0 W H">...</svg>;
}
```

### Two Animation Paradigms

| Feature | GSAP Timeline | Frame Switcher |
|---------|--------------|----------------|
| Use case | Simple continuous motion | Complex choreography |
| Example | Shake, walk, bounce | Typing sequence (36 frames) |
| Targeting | CSS selectors via refs | `<g>` display toggle |
| Timing | Duration + ease per tween | Variable ms array per frame |
| Loop | `repeat: -1` on timeline | setTimeout recursive |
| Cleanup | `timeline.kill()` | Clear timeout |

### The dither.js Component (v127)

A `DitherEffect` component (360 lines) that creates a dithered image effect using canvas. Not a character — it's a visual treatment for photos. Uses a separate rendering pipeline (canvas 2D) rather than SVG.

## How to Replicate with Our Pipeline

### Path 1: AI-Generated Characters (EDH approach)

1. Use `nano-banana-pro` to generate character in target style
2. Trim with `magick -fuzz 15% -trim`
3. Convert with `pixel_art_generator.py --grid 20 --colors 4 --merge --remove-bg`
4. Add `id="mascot"` to SVG root
5. Apply animation preset via `animation_builder.py`
6. Assemble with `template_renderer.py`

### Path 2: Hand-Designed Characters (Claude mascot approach)

1. Design character in Figma using only rectangles
2. Export as SVG
3. Name groups: `#body`, `#legs`, `#eyes`, `#left-hand`, `#right-hand`, `#code`, etc.
4. Embed as JSX in React component
5. Write GSAP timeline directly in useEffect
6. Add hover interactions if needed

### Path 3: Hybrid (highest quality)

1. Generate base character with `nano-banana-pro`
2. Import into Figma, trace/refine manually
3. Export clean SVG with proper group naming
4. Animate with our GSAP presets
