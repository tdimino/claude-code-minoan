# Sunny Mode: Multi-Mode Theme Switching with CSS @property

Reference implementation from [dany.works](https://dany.works/) by @danywander. Vanilla HTML/CSS/JS, no framework.

## Core Technique: CSS `@property` for Animated Custom Properties

Standard CSS custom properties cannot be animated — the browser treats them as opaque strings. Registering them as typed `<color>` values via `@property` enables smooth 400ms cross-fades between palettes:

```css
@property --bg   { syntax: '<color>'; inherits: true; initial-value: #080808; }
@property --text { syntax: '<color>'; inherits: true; initial-value: #b4b4b4; }
@property --mid  { syntax: '<color>'; inherits: true; initial-value: #404040; }
@property --line { syntax: '<color>'; inherits: true; initial-value: #181818; }

body {
  transition: --bg 400ms ease, --text 400ms ease, --mid 400ms ease, --line 400ms ease;
  background: var(--bg);
  color: var(--text);
}
```

This is the key insight: **`@property` registration + `transition` on custom properties = smooth palette morphing** that vanilla `var()` cannot achieve.

## Four Modes via Class Toggling

The site uses four modes, each activated by tapping a letter in the logo SVG or pressing a keyboard shortcut:

| Letter | Mode | Key | Palette | Special Effect |
|--------|------|-----|---------|----------------|
| D | Day | `D` | Warm cream (#f2efe9) | None — clean light mode |
| A | Summer | `S` | Warm cream + overlay | Leaves video + forest audio |
| N | Night | `N` | Rich off-black (#080808) | Default |
| Y | Chaos | `C` | Inherited | Matter.js physics — everything falls |

### Light Mode ("Day" / "Sunny")

```css
body.light {
  --bg:   #f2efe9;     /* warm paper cream */
  --text: #1a1a1a;     /* near-black */
  --mid:  #888;
  --line: #d8d5cf;     /* warm light gray */
}
body.light .logo { filter: none; }
body.light a { text-decoration-color: #b0b0b0; }
body.light a:hover { color: #000; text-decoration-color: #606060; }
```

Logo uses `filter: invert(1)` by default (dark mode), removed in light mode. This avoids maintaining two SVG variants.

### JavaScript: Simple Class Toggle

```javascript
document.addEventListener('keydown', e => {
  if (e.key === 'd' || e.key === 'D') {
    document.body.classList.add('light');
    document.body.classList.remove('leaves');
    stopSummer();
  }
  if (e.key === 'n' || e.key === 'N') {
    document.body.classList.remove('light', 'leaves');
    stopSummer();
  }
  if (e.key === 's' || e.key === 'S') {
    if (!document.body.classList.contains('leaves')) {
      document.body.classList.add('light', 'leaves');
      video.play(); audio.play();
    }
  }
});
```

Mobile: `touchend` on logo letters with `data-mode` attributes. `e.preventDefault()` to avoid ghost clicks.

## Summer Mode: Video Overlay + Audio

A full-viewport `<video>` with `mix-blend-mode: multiply` creates dappled sunlight over the warm cream background:

```html
<video id="leaves-overlay" src="/leaves.mp4" loop muted playsinline preload="auto"></video>
<audio id="forest-audio" src="/forest.mp3" loop preload="auto"></audio>
```

```css
#leaves-overlay {
  position: fixed;
  inset: 0;
  width: 100%; height: 100%;
  object-fit: cover;
  mix-blend-mode: multiply;   /* blends with light background */
  pointer-events: none;
  z-index: 999;
  opacity: 0;
  transition: opacity 700ms var(--ease-out);
}
body.leaves #leaves-overlay { opacity: 1; }
```

The `multiply` blend mode on a light background is the key — dark leaf shapes darken the cream, creating naturalistic shadow patterns. `pointer-events: none` ensures the overlay doesn't intercept clicks.

## Chaos Mode: Matter.js Physics

Dynamically loads Matter.js from CDN, then:
1. Splits all visible text into individual word `<span>` elements
2. Creates physics bodies for each element (different friction/restitution per type)
3. World gravity: `y: 3.5` with floor + side walls
4. All elements become draggable (mouse + touch)
5. Pressing `C` again reverses with 750ms eased animation back to original positions

## Image Shader Overlay

Uses `@paper-design/shaders-react` (HalftoneDots component) loaded as ES module from esm.sh:

```javascript
const shaderProps = {
  contrast: 0.4, grid: 'hex', radius: 1, size: 0.2,
  colorFront: '#2B2B2B', colorBack: '#00000000',
  style: { backgroundColor: '#F2F1E8' },
};
createRoot(overlay).render(React.createElement(HalftoneDots, { ...shaderProps, image: img.src }));
```

Shader overlay fades to `opacity: 0` on hover (desktop) or touch-and-hold (mobile), revealing the original image.

## Design Tokens & Easing

```css
--ease-out: cubic-bezier(0.23, 1, 0.32, 1);
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
```

Font: Fragment Mono (Google Fonts). Analytics: GoatCounter. Hosting: Vercel.

## Patterns Worth Stealing

1. **`@property` for palette transitions** — the most transferable technique. Works in all modern browsers (Chrome 85+, Firefox 128+, Safari 15.4+).
2. **Logo as mode selector** — each letter is a discoverable, interactive entry point. No visible toggle cluttering the UI.
3. **Blend mode overlays for atmosphere** — `mix-blend-mode: multiply` with video/canvas layers creates ambient effects that feel organic, not computed.
4. **Audio as spatial design** — ambient audio reinforces the mode's emotional texture. Autoplay on user interaction (not page load) respects browser policies.
5. **Physics as Easter egg** — the chaos mode is pure delight. Reversible, playful, zero functional purpose. This is the kind of thing that makes someone describe a site to a friend.
