# GSAP Timeline Patterns for SVG Mascot Animation

## Core Pattern: Infinite Loop Timeline

```js
const tl = gsap.timeline({ repeat: -1, repeatDelay: 1.5 });
```

## Easing Functions

| Ease | Use Case |
|------|----------|
| `power2.out` | Landing, settling into position |
| `power2.in` | Lifting off, acceleration |
| `power2.inOut` | Smooth oscillation (lean, sway) |
| `power3.in` | Hard landing (bounce down) |
| `sine.inOut` | Gentle breathing, idle bob |
| `linear` | Walking translation (constant speed) |

## Walk Cycle

The walk cycle alternates two leg pairs squashing while the body translates:

```js
// Dynamic walk distance from parent container
const svgRect = svg.getBoundingClientRect();
const parentRect = container.getBoundingClientRect();
const scale = viewBoxWidth / svgRect.width;
const walkDist = 0.55 * scale * (parentRect.width - svgRect.width);

// Alternating leg squash
tl.to([leg1, leg3], { scaleY: 0.45, duration: 0.1, ease: "power2.out" }, "walk")
  .to([leg1, leg3], { scaleY: 1, duration: 0.1, ease: "power2.in" }, "walk+=0.1")
  .to([leg2, leg4], { scaleY: 0.45, duration: 0.1, ease: "power2.out" }, "walk+=0.1")
  .to([leg2, leg4], { scaleY: 1, duration: 0.1, ease: "power2.in" }, "walk+=0.2");
```

Set `svgOrigin` on each leg to its bottom-center so it squashes from the ground up:
```js
gsap.set(leg, { svgOrigin: (legCenterX) + " " + (legBottomY) });
```

## Bounce

```js
tl.to(group, { y: -18, duration: 0.18, ease: "power2.out" })
  .to(group, { y: 0, duration: 0.15, ease: "power3.in" });
```

## Lean / Sway

Rotate body around its bottom-center:
```js
tl.to(body, { rotation: -3, svgOrigin: "53 65", duration: 0.4, ease: "power2.out" })
  .to(body, { rotation: 3, svgOrigin: "53 65", duration: 0.4, ease: "power2.out" }, "+=1.5");
```

While leaning, splay legs with individual rotation and scaleY:
```js
tl.to(legs, {
  rotation: i => [-7, -8, -8, -9][i],
  scaleY: i => [1.35, 1.3, 1.2, 1.15][i],
  duration: 0.4, ease: "power2.out"
}, "<");
```

## Wave

```js
tl.to(hand, { y: -12, duration: 0.3, ease: "power2.out" })
  .to(hand, { rotation: -15, svgOrigin: "center bottom", duration: 0.2 })
  .to(hand, { rotation: 15, duration: 0.15 })
  .to(hand, { rotation: -10, duration: 0.15 })
  .to(hand, { rotation: 0, y: 0, duration: 0.3, ease: "power2.in" });
```

## Label-Based Choreography

```js
tl.addLabel("walk")
  .to(group, { x: walkDist, duration: 2.2, ease: "linear" }, "walk")
  .addLabel("walkBack", "+=0.5")
  .to(group, { x: 0, duration: 2.2, ease: "linear" }, "walkBack");
```

## Simultaneous Animations

Use `"<"` to start at same time as previous tween:
```js
tl.to(body, { x: 4, duration: 0.4 })
  .to(head, { rotation: 3, duration: 0.4 }, "<");  // starts at same time
```

## Cleanup Pattern (React)

```js
useEffect(() => {
  const tl = gsap.timeline({ repeat: -1 });
  // ... setup
  return () => tl.kill();
}, []);
```
