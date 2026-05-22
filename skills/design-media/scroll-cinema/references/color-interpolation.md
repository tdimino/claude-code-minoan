# Scroll-Driven Color Interpolation

Fluid color transitions between chapters using OKLCH color space. sRGB interpolation produces muddy brown midpoints when transitioning between hues (blue→orange goes through grey). OKLCH maintains perceptual uniformity — midpoints stay vibrant.

## CSS @property Registration

Register custom properties for GPU-accelerated color animation. Without `@property`, CSS custom properties are strings — the browser cannot interpolate them.

```js
if (typeof CSS !== 'undefined' && CSS.registerProperty) {
  CSS.registerProperty({
    name: '--sc-hue',
    syntax: '<angle>',
    inherits: true,
    initialValue: '0deg'
  });
  CSS.registerProperty({
    name: '--sc-chroma',
    syntax: '<number>',
    inherits: true,
    initialValue: '0.15'
  });
  CSS.registerProperty({
    name: '--sc-lightness',
    syntax: '<number>',
    inherits: true,
    initialValue: '0.25'
  });
}
```

## Chapter Color System

Each chapter defines its color via data attributes on the section element:

```html
<section class="chapter" data-chapter="0" data-hue="250" data-chroma="0.15" data-lightness="0.25">
<section class="chapter" data-chapter="1" data-hue="30"  data-chroma="0.18" data-lightness="0.45">
<section class="chapter" data-chapter="2" data-hue="160" data-chroma="0.12" data-lightness="0.35">
<section class="chapter" data-chapter="3" data-hue="340" data-chroma="0.20" data-lightness="0.30">
<section class="chapter" data-chapter="4" data-hue="60"  data-chroma="0.08" data-lightness="0.55">
```

## Example Palettes

| Narrative | Ch 1 | Ch 2 | Ch 3 | Ch 4 | Ch 5 |
|-----------|------|------|------|------|------|
| Dawn to dusk | H250 deep indigo | H30 warm amber | H160 teal | H340 rose | H60 pale gold |
| Ocean descent | H200 surface blue | H210 mid blue | H220 deep blue | H190 bioluminescent | H180 abyss teal |
| Forest walk | H120 spring green | H90 moss | H60 sunlight | H30 amber canopy | H150 twilight green |
| Desert crossing | H40 sand | H20 rust | H50 gold noon | H10 sunset crimson | H260 night indigo |

## GSAP ScrollTrigger Color Tween

```js
const sections = document.querySelectorAll('.chapter');

sections.forEach((section, i) => {
  if (i === 0) return; // First chapter sets initial values

  const hue = section.dataset.hue;
  const chroma = section.dataset.chroma;
  const lightness = section.dataset.lightness;

  gsap.to(':root', {
    '--sc-hue': `${hue}deg`,
    '--sc-chroma': parseFloat(chroma),
    '--sc-lightness': parseFloat(lightness),
    ease: 'cinematicLinear',
    scrollTrigger: {
      trigger: section,
      start: 'top center',
      end: 'top top',
      scrub: 1
    }
  });
});
```

## CSS Application

```css
body {
  background-color: oklch(var(--sc-lightness) var(--sc-chroma) var(--sc-hue));
}
```

No `transition` on `background-color` — GSAP handles the interpolation frame-by-frame via custom properties.

## Fallback for Unsupported Browsers

```js
const supportsOKLCH = CSS.supports && CSS.supports('color', 'oklch(0.5 0.1 250)');
const supportsRegisterProperty = typeof CSS !== 'undefined' && !!CSS.registerProperty;

if (!supportsOKLCH || !supportsRegisterProperty) {
  // Fall back to HSL via direct background-color tween
  sections.forEach((section, i) => {
    if (i === 0) return;
    const h = section.dataset.hue;
    const s = Math.round(parseFloat(section.dataset.chroma) * 500);
    const l = Math.round(parseFloat(section.dataset.lightness) * 100);

    gsap.to('body', {
      backgroundColor: `hsl(${h}, ${s}%, ${l}%)`,
      ease: 'cinematicLinear',
      scrollTrigger: {
        trigger: section,
        start: 'top center',
        end: 'top top',
        scrub: 1
      }
    });
  });
}
```

HSL is better than sRGB for hue interpolation but not as perceptually uniform as OKLCH. Acceptable fallback.

## Text Contrast

Maintain WCAG 2.1 AA contrast at all intermediate states:

| Lightness Range | Text Color | Token |
|-----------------|-----------|-------|
| < 0.4 | White / light | `--sc-text: #E8ECF4` |
| 0.4–0.6 | Test both, prefer white | Check contrast ratio |
| > 0.6 | Dark | `--sc-text: #1a1a2e` |

For transitional states, cross-fade text color alongside the background:

```js
gsap.to(':root', {
  '--sc-text': lightness > 0.5 ? '#1a1a2e' : '#E8ECF4',
  scrollTrigger: { trigger: section, start: 'top center', end: 'top top', scrub: 1 }
});
```

## Shader Uniform Sync

Feed the current chapter color to the Three.js shader for background harmony:

```js
// In the GSAP ticker callback
const style = getComputedStyle(document.documentElement);
const hue = parseFloat(style.getPropertyValue('--sc-hue')) || 0;
const lightness = parseFloat(style.getPropertyValue('--sc-lightness')) || 0.25;

material.uniforms.uChapterHue.value += (hue / 360.0 - material.uniforms.uChapterHue.value) * 0.03;
material.uniforms.uChapterLightness.value += (lightness - material.uniforms.uChapterLightness.value) * 0.03;
```

The shader can use these to tint its output, creating a unified color field between the WebGL background and the HTML content layer.

## Browser Support

| Feature | Chrome | Firefox | Safari |
|---------|--------|---------|--------|
| OKLCH colors | 111+ | 113+ | 15.4+ |
| `CSS.registerProperty` | 85+ | 128+ | 16.4+ |
| `CSS.supports()` | 28+ | 22+ | 9+ |

The fallback path (HSL via direct `backgroundColor` tween) works in all browsers GSAP supports.
