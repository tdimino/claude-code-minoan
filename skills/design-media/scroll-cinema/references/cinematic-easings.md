# Cinematic Easings

Custom easing curves for scroll-driven cinematic animation. Default GSAP easings (`power2.out`, `ease`) feel robotic for cinematic scroll — film-inspired curves create rhythm through variable acceleration.

## Four Cinematic Curves

```js
CustomEase.create("cinematicSilk",   "0.45,0.05,0.55,0.95");
CustomEase.create("cinematicSmooth", "0.25,0.1,0.25,1");
CustomEase.create("cinematicFlow",   "0.33,0,0.2,1");
CustomEase.create("cinematicLinear", "0.4,0,0.6,1");
```

| Curve | Cubic-Bezier | Feel | Best For |
|-------|-------------|------|----------|
| `cinematicSilk` | `0.45,0.05,0.55,0.95` | Slow in, slow out — luxurious, deliberate | Hero text reveals, title entrances, signature moments |
| `cinematicSmooth` | `0.25,0.1,0.25,1` | Natural deceleration — settling into place | Section fade-ins, content block entrances, image reveals |
| `cinematicFlow` | `0.33,0,0.2,1` | Apple-like momentum — decisive, confident | Camera moves, parallax layers, typography stagger |
| `cinematicLinear` | `0.4,0,0.6,1` | Subtle ease — near-constant with soft edges | Background opacity, color transitions, shader uniform shifts |

## Timing by Content Type

| Animation | Duration | Easing | Notes |
|-----------|----------|--------|-------|
| Hero entrance | 1.2–1.8s | cinematicSilk | The first thing the reader sees — give it weight |
| Section reveal (fade up) | 0.8–1.2s | cinematicSmooth | Natural, unobtrusive |
| Section reveal (clip-path wipe) | 1.0–1.4s | cinematicFlow | Cinematic curtain effect |
| Typography stagger (per element) | 0.08–0.15s delay | cinematicFlow | Gap between each word/line entering |
| Color transition | scrub-linked | cinematicLinear | Tied to scroll, no fixed duration |
| Background opacity shift | 0.6–1.0s | cinematicLinear | Subtle, should not draw attention |
| Image scale reveal | 1.0–1.4s | cinematicSmooth | Immersive, builds anticipation |

## ScrollTrigger Scrub Values

The `scrub` property controls how closely the animation follows scroll position:

| Value | Behavior | Feel | When to Use |
|-------|----------|------|-------------|
| `scrub: true` | Instant follow | Harsh, mechanical | Never in scroll-cinema |
| `scrub: 0.5` | 0.5s catch-up | Responsive | Interactive elements, parallax |
| `scrub: 1` | 1s catch-up | **Cinematic — the default** | Color transitions, section reveals |
| `scrub: 2` | 2s catch-up | Dreamy, languid | Slow chapters, contemplative sections |
| `scrub: 3` | 3s catch-up | Very slow, atmospheric | Background-only effects, shader uniforms |

## ScrollTrigger `toggleActions`

For non-scrubbed animations (entrance effects):

```js
scrollTrigger: {
  trigger: element,
  start: 'top 80%',        // Trigger when top of element hits 80% of viewport
  toggleActions: 'play none none reverse'
  // onEnter  onLeave  onEnterBack  onLeaveBack
  // play     none     none         reverse
}
```

This plays on first enter and reverses when scrolling back up — the chapter "unwinds" as you retreat.

## CustomEase Note

`CustomEase.create()` with cubic-bezier strings works on GSAP's free tier. The visual curve editor requires GSAP Club, but the string-based API does not. Register curves once at initialization, reference by name everywhere:

```js
gsap.to(element, {
  opacity: 1,
  y: 0,
  duration: 1.2,
  ease: 'cinematicSilk'
});
```

## Pacing Multipliers

The `--pacing` parameter scales all durations:

| Pacing | Duration Multiplier | Stagger Multiplier | Chapter Height |
|--------|--------------------|--------------------|----------------|
| `slow` | 1.5× | 1.3× | 250vh |
| `medium` | 1.0× | 1.0× | 200vh |
| `fast` | 0.6× | 0.7× | 150vh |

Apply the multiplier to all timing values:
```js
const pacingMultiplier = { slow: 1.5, medium: 1.0, fast: 0.6 }[pacing];
const duration = baseDuration * pacingMultiplier;
```
