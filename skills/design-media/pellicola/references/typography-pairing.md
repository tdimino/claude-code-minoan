# Pellicola Typography Pairing

Font selection guide for cinematic case study pages. Two voices: dramatic display serif + precise geometric sans.

## Primary Pairing: Playfair Display + DM Sans

The default pairing. Playfair Display carries editorial weight — high contrast, ball terminals, dramatic thick/thin strokes. DM Sans is geometric, slightly humanist, clean without being generic.

### Playfair Display (Display Serif)

- **Role:** Headlines, film titles, credit names, pullquotes, hero title
- **Weights:** 400 (regular), 700 (bold), 400i (italic — for emphasis within headlines)
- **Character:** High contrast, transitional/didone classification, distinctive ball terminals
- **Why this font:** The thick/thin contrast reads as cinematic — it has the weight of a film title card. The ball terminals add personality without being decorative.
- **Google Fonts:** `family=Playfair+Display:ital,wght@0,400;0,700;1,400`

### DM Sans (Body/UI Sans)

- **Role:** Body text, navigation, labels, metadata, credit roles, section divider labels
- **Weights:** 400 (regular), 500 (medium — labels, nav), 700 (bold — emphasis)
- **Character:** Geometric but slightly humanist, open apertures, good small-size legibility
- **Why this font:** Geometric precision without the coldness of pure geometric faces. Open letterforms read well at small sizes (credit roles at 0.75rem). Not a default — DM Sans is specific enough to avoid the "generated" feeling.
- **Google Fonts:** `family=DM+Sans:ital,wght@0,400;0,500;0,700;1,400`

### Full Google Fonts URL

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500;0,700;1,400&family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
```

## Alternative Pairing 1: Cormorant Garamond + Outfit

More literary, less editorial. Cormorant Garamond has old-style proportions — longer ascenders, more calligraphic. Outfit is a clean geometric with no humanist softness.

- **When to use:** Documentary about literature, art, or history. Period pieces. Photography portfolios with a fine-art direction.
- **Display:** `family=Cormorant+Garamond:ital,wght@0,400;0,700;1,400`
- **Body:** `family=Outfit:wght@400;500;700`

## Alternative Pairing 2: Lora + Karla

Warmer, more approachable. Lora is a contemporary serif with moderate contrast — readable at body sizes too. Karla is a grotesque sans with quirky details.

- **When to use:** Independent films, personal projects, warmth over authority. When the display font also needs to work at body size.
- **Display:** `family=Lora:ital,wght@0,400;0,700;1,400`
- **Body:** `family=Karla:wght@400;500;700`

## Type Hierarchy

### Hero Title
```css
.pel-hero__title {
  font-family: var(--pel-font-display);
  font-size: clamp(3rem, 8vw, 7rem);
  font-weight: 400;
  line-height: 0.95;
  letter-spacing: -0.02em;
  color: var(--pel-ink);
}
```

### Section Heading
```css
.pel-section h2 {
  font-family: var(--pel-font-display);
  font-size: clamp(2rem, 4vw, 3.5rem);
  font-weight: 400;
  line-height: 1.1;
  color: var(--pel-ink);
}
```

### Credit Role (Tracked Small Caps)
```css
.pel-credits__role {
  font-family: var(--pel-font-body);
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--pel-ink-muted);
}
```

### Credit Name (Display)
```css
.pel-credits__name {
  font-family: var(--pel-font-display);
  font-size: clamp(1.25rem, 2vw, 1.75rem);
  font-weight: 400;
  line-height: 1.2;
  color: var(--pel-ink);
}
```

### Section Divider Label
```css
.pel-divider__label {
  font-family: var(--pel-font-body);
  font-size: 0.6875rem;
  font-weight: 500;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--pel-ink-muted);
}
```

### Body Text
```css
body {
  font-family: var(--pel-font-body);
  font-size: 1rem;
  font-weight: 400;
  line-height: 1.6;
  color: var(--pel-ink);
}
```

### Metadata / Widget
```css
.pel-widget__meta {
  font-family: var(--pel-font-body);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--pel-ink-muted);
}
```

## Font Reflex-Reject List

Never use these — they signal "generated, not designed":

| Font | Why reject |
|------|-----------|
| Inter | Model's first reflex — ubiquitous, no character |
| Roboto | Android system font — reads as default |
| Arial | Windows system font |
| Open Sans | Google Docs default |
| Lato | Overused sans-serif |
| Montserrat | Second-reflex geometric sans |
| Space Grotesk | Third-reflex — trending but overexposed |
| system-ui | No control over rendering |

## Anti-Aliasing

Always set on the body:

```css
body {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}
```

## Number Rendering

Credit years, runtimes, and other numeric data use tabular figures when available:

```css
.pel-meta__value {
  font-variant-numeric: tabular-nums;
}
```
