# Cylindrix Carousel

Scroll-driven image carousel where cards deform through a cylindrical
arc at the viewport center and flatten tangentially at the edges. CPU
vertex deformation per frame, infinite modulo belt positioning.
Source: thebuggeddev/Cylindrix (Three.js + GSAP + React, ~300 LOC).

## Cylinder Math

Parameters: R (radius=9), L (arc length=5), spacing, card dimensions.

```javascript
// Within arc: wrap onto cylinder surface
x = R * Math.sin(theta);
z = R * Math.cos(theta) - R;

// Outside arc: extend tangentially (flat continuation)
// Seamless transition at arc boundary
```

- CPU vertex deformation (no geometry shader needed)
- ~15 lines for the core math

## Infinite Belt

```javascript
rawU = i * spacing + scrollOffset;
// Modulo wrap: (-totalLength/2, totalLength/2) — seamless loop
wrappedU = ((rawU + half) % total + total) % total - half;
```

## ShaderMaterial

- **Vertex**: pass-through UVs
- **Fragment**: horizontal flip (inside-cylinder illusion), 25% zoom-in
  for parallax headroom, `uParallax` shifts `uv.x` ±12% by belt position
- `uBrightness` lerped on hover (15% lift)

## Interaction

- Drag/scroll: `targetScroll += delta`
- Inertia: `scrollOffset += (targetScroll - scrollOffset) * 5 * dt`
- Click-to-center: GSAP `power3.out`, 1.2s, shortest-path wrap

## Architecture

- Single `useEffect` (~300 LOC), clone `PlaneGeometry` per card
- Per-frame vertex mutation loop (all cards, all vertices)
- Exponential smoothing only — no spring physics

## Parameterization

`R`, `L`, `spacing`, `cardWidth`, `cardHeight`, `inertiaFactor`, `hoverBrightness`
