# Pellicola Page Architecture

Section sequence, z-index stack, scroll rhythm, and structural patterns for cinematic case study pages.

## Section Sequence (Canonical)

Case study pages follow this order. Sections can be omitted but the order is fixed.

```
┌─────────────────────────────────────────┐
│ Skip Link (hidden until focus)          │
│ Context Widget (fixed, top-right)       │
├─────────────────────────────────────────┤
│                                         │
│  1. HERO                                │
│  ┌─────────────────────────────┐        │
│  │  Film-frame image           │        │
│  │  (parallax scroll)          │        │
│  └─────────────────────────────┘        │
│  DOCUMENTARY                            │
│  TABOO                                  │
│  [▶ Watch Trailer]                      │
│  ↓                                      │
│                                         │
├── Credits ──────────────────────────────┤
│                                         │
│  2. CREDITS                             │
│  ┌──────────┐                           │
│  │ Director │  Director portrait        │
│  │ portrait │  with dark overlay        │
│  └──────────┘                           │
│  ┌──────┬──────┬──────┐                 │
│  │Role  │Role  │Role  │  Credit grid    │
│  │Name  │Name  │Name  │  (3-col)        │
│  ├──────┼──────┼──────┤                 │
│  │Role  │Role  │Role  │                 │
│  │Name  │Name  │Name  │                 │
│  └──────┴──────┴──────┘                 │
│                                         │
├── Gallery ──────────────────────────────┤
│                                         │
│  3. GALLERY (dark background)           │  ← Full-bleed black
│  ┌────┬────┬────┐                       │
│  │img │img │img │  Film stills grid     │
│  ├────┼────┼────┤  (hover: scale+bright)│
│  │img │img │img │                       │
│  └────┴────┴────┘                       │
│                                         │
├── Awards & Festivals ───────────────────┤
│                                         │
│  4. PRIZES                              │
│  [logo] [logo] [logo] [logo]           │
│  Name   Name   Name   Name             │
│  Award  Award  Award  Award            │
│                                         │
├── Partners ─────────────────────────────┤
│                                         │
│  5. INVESTORS / PARTNERS                │
│  Acknowledgment text or logo grid       │
│                                         │
├── Next ─────────────────────────────────┤
│                                         │
│  6. NEXT PROJECT                        │
│  Next Project         ┌──────────┐      │
│  ANA MAXIM            │ Preview  │      │
│                       │ image    │      │
│                       └──────────┘      │
│                                         │
├─────────────────────────────────────────┤
│ Footer                                  │
└─────────────────────────────────────────┘
```

## Semantic Structure

```html
<body>
  <a href="#main" class="pel-skip-link">Skip to content</a>
  <aside class="pel-widget">...</aside>

  <main id="main">
    <article class="pel-container">
      <section class="pel-hero" aria-label="Film hero">...</section>
      <section class="pel-section" id="credits" aria-label="Credits">...</section>
      <section class="pel-gallery" aria-label="Gallery">...</section>
      <section class="pel-section" aria-label="Awards">...</section>
      <section class="pel-section" aria-label="Partners">...</section>
      <section class="pel-section" aria-label="Next project">...</section>
    </article>
    <footer class="pel-footer">...</footer>
  </main>
</body>
```

- `<article>` wraps the case study as a self-contained composition
- Each content section is a `<section>` with `aria-label`
- Gallery section breaks out of `pel-container` for full-bleed dark background
- Widget is an `<aside>` — supplementary navigation, not part of main content flow

## Z-Index Stack

```
Layer 0   z-index: 0     Body background (--pel-cream)
Layer 1   z-index: 1     Content sections (position: relative)
Layer 2   z-index: 10    Director card overlay (gradient)
Layer 3   z-index: 50    Context widget (position: fixed)
Layer 4   z-index: 100   Skip link (position: fixed)
```

No z-index conflicts. Gallery section uses `position: relative` with no explicit z-index (stacks in document flow).

## Scroll Rhythm

The page alternates between cream and dark sections, creating visual breathing:

```
CREAM  │  Hero, title, play button
CREAM  │  Credits section
───────┤  
BLACK  │  Gallery (dark section)
───────┤
CREAM  │  Prizes
CREAM  │  Partners
CREAM  │  Next project
CREAM  │  Footer
```

The single dark section (gallery) creates a "lights off in the theater" moment. Never add multiple dark sections — the rhythm is cream-dark-cream, once.

## Gallery Full-Bleed Technique

The gallery section breaks out of the `pel-container` max-width:

```css
.pel-gallery {
  margin-left: calc(-1 * var(--pel-content-pad));
  margin-right: calc(-1 * var(--pel-content-pad));
  width: calc(100% + 2 * var(--pel-content-pad));
  padding: var(--pel-section-gap) var(--pel-content-pad);
}

.pel-gallery__inner {
  max-width: var(--pel-max-width);
  margin: 0 auto;
}
```

Content inside uses `.pel-gallery__inner` to re-establish max-width.

## Section Divider Pattern

Every section opens with a labeled divider:

```html
<div class="pel-divider" data-pel="line">
  <span class="pel-divider__label">Credits</span>
</div>
```

The label sits left, the line extends right (`flex: 1`). Line animates via `scaleX(0 → 1)` from left origin.

Dark variant for gallery section: `.pel-divider--dark`.

## Responsive Behavior

| Breakpoint | Changes |
|------------|---------|
| `1024px` | Credit grid: 3-col → 2-col. Section gap reduces. |
| `768px` | Widget hides. Gallery: 3-col → 2-col. Next project: 2-col → 1-col stack. Hero title scales down. |
| `480px` | Credit grid → 1-col. Gallery → 1-col. Content padding narrows. |

## Scroll Choreography Timeline

Order of reveals as user scrolls a full page:

```
0vh    Hero frame fades in (data-pel="alpha")
       Hero title + label slide up (data-pel="y")
       Play button fades in (data-pel="alpha")

~90vh  Credits divider line grows (data-pel="line")
       Director card slides up (data-pel="y")
       Credit cells cascade in (data-pel="stagger", 0.1s each)

~180vh Gallery divider line grows (data-pel="line")
       Gallery images cascade in (data-pel="stagger", 0.1s each)
       [Hover: images scale + brighten]

~270vh Prizes divider line grows
       Prize items cascade in (data-pel="stagger")

~340vh Partners divider line grows
       Partners text slides up (data-pel="y")

~400vh Next divider line grows
       Next project link slides up (data-pel="y")
```

## Widget Interaction

The context widget is fixed top-right with a dropdown film list:

1. **Default state:** Collapsed. Shows thumbnail, title, metadata tags.
2. **Click toggle:** Dropdown opens via `grid-template-rows: 0fr → 1fr`.
3. **Expanded state:** Shows links to other films.
4. **Mobile:** Widget hidden entirely (768px breakpoint).

Toggle JS:

```js
toggle.addEventListener('click', () => {
  const expanded = toggle.getAttribute('aria-expanded') === 'true';
  toggle.setAttribute('aria-expanded', !expanded);
  dropdown.classList.toggle('is-open');
});
```

## Image Strategy

| Element | Aspect Ratio | Sizing | Loading |
|---------|-------------|--------|---------|
| Hero image | Free (original) | `max-width: 900px` | Eager |
| Director portrait | 3:4 | `max-width: 500px` | Eager |
| Gallery stills | 16:10 | Grid fill | `loading="lazy"` |
| Next project preview | Free (original) | `max-width: 400px` | `loading="lazy"` |
| Widget thumbnail | 1:1 | `28px` circle | Eager |

Gallery stills use `loading="lazy"` since they're below the fold. Hero and director images load eagerly for fast first paint.
