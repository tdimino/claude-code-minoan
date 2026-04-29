# Pellicola Component Catalog

Copy-paste HTML snippets for all 9 components. Each component reads from `--pel-*` tokens.

---

## pel-hero

Film-frame image with title overlay, genre label, and play button.

```html
<section class="pel-hero" aria-label="Film hero">
  <div class="pel-hero__frame pel-frame" data-pel="alpha">
    <img src="hero.jpg" alt="Scene from Film Title" data-pel="parallax">
  </div>
  <div class="pel-hero__content" data-pel="y">
    <p class="pel-hero__label">DOCUMENTARY</p>
    <h1 class="pel-hero__title" data-pel="title">Film Title</h1>
  </div>
  <div class="pel-hero__actions" data-pel="alpha">
    <button class="pel-play" aria-label="Watch trailer">
      <span class="pel-play__circle">
        <svg class="pel-play__icon" viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
          <polygon points="8,5 20,12 8,19" fill="currentColor"/>
        </svg>
      </span>
      <span class="pel-play__text">Watch Trailer</span>
    </button>
  </div>
  <a href="#credits" class="pel-hero__scroll" aria-label="Scroll to credits">
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
      <path d="M12 5v14M5 12l7 7 7-7" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
    </svg>
  </a>
</section>
```

### CSS

```css
.pel-hero {
  position: relative;
  min-height: 90vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--pel-content-pad);
  text-align: center;
}

.pel-hero__frame {
  max-width: 900px;
  width: 100%;
  margin-bottom: 2rem;
}

.pel-hero__label {
  font-family: var(--pel-font-body);
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--pel-ink-muted);
  margin-bottom: 0.75rem;
}

.pel-hero__title {
  font-family: var(--pel-font-display);
  font-size: clamp(3rem, 8vw, 7rem);
  font-weight: 400;
  line-height: 0.95;
  letter-spacing: -0.02em;
  color: var(--pel-ink);
  margin: 0;
}

.pel-hero__actions {
  margin-top: 2rem;
}

.pel-hero__scroll {
  position: absolute;
  bottom: 2rem;
  color: var(--pel-ink-muted);
  text-decoration: none;
  transition: color var(--pel-duration-short) var(--pel-ease);
}
.pel-hero__scroll:hover { color: var(--pel-ink); }
```

---

## pel-credit-grid

Role/name pairs in bordered grid. 2-3 columns. Roles in tracked small caps, names in display serif.

```html
<section class="pel-section" id="credits" aria-label="Credits">
  <div class="pel-divider" data-pel="line">
    <span class="pel-divider__label">Credits</span>
  </div>

  <div class="pel-credits" data-pel="stagger">
    <div class="pel-credits__cell">
      <p class="pel-credits__role">Director</p>
      <p class="pel-credits__name">Shauly Melamed</p>
    </div>
    <div class="pel-credits__cell">
      <p class="pel-credits__role">Executive Producer</p>
      <p class="pel-credits__name">Jane Smith</p>
    </div>
    <div class="pel-credits__cell">
      <p class="pel-credits__role">Producer</p>
      <p class="pel-credits__name">John Doe</p>
    </div>
    <div class="pel-credits__cell">
      <p class="pel-credits__role">Editor</p>
      <p class="pel-credits__name">Alex Rivera</p>
    </div>
    <div class="pel-credits__cell">
      <p class="pel-credits__role">Cinematographer</p>
      <p class="pel-credits__name">Maria Chen</p>
    </div>
    <div class="pel-credits__cell">
      <p class="pel-credits__role">Music</p>
      <p class="pel-credits__name">David Park</p>
    </div>
  </div>
</section>
```

### CSS

```css
.pel-credits {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border-top: 1px solid var(--pel-border);
  border-left: 1px solid var(--pel-border);
}

.pel-credits__cell {
  padding: clamp(1rem, 2vw, 1.5rem);
  border-right: 1px solid var(--pel-border);
  border-bottom: 1px solid var(--pel-border);
}

.pel-credits__role {
  font-family: var(--pel-font-body);
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--pel-ink-muted);
  margin: 0 0 0.5rem;
}

.pel-credits__name {
  font-family: var(--pel-font-display);
  font-size: clamp(1.25rem, 2vw, 1.75rem);
  font-weight: 400;
  line-height: 1.2;
  color: var(--pel-ink);
  margin: 0;
}

/* 2-column variant */
.pel-credits--2col {
  grid-template-columns: repeat(2, 1fr);
}

/* Responsive */
@media (max-width: 1024px) {
  .pel-credits { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 480px) {
  .pel-credits { grid-template-columns: 1fr; }
}
```

---

## pel-director-card

Left-aligned cropped portrait with dark overlay, display serif name, small caps role.

```html
<div class="pel-director" data-pel="y">
  <div class="pel-director__image">
    <img src="director.jpg" alt="Portrait of Director Name">
    <div class="pel-director__overlay">
      <p class="pel-director__role">Director</p>
      <h3 class="pel-director__name">Shauly Melamed</h3>
    </div>
  </div>
</div>
```

### CSS

```css
.pel-director {
  max-width: 500px;
  margin-bottom: 2rem;
}

.pel-director__image {
  position: relative;
  overflow: hidden;
  border-radius: var(--pel-frame-radius);
}

.pel-director__image img {
  width: 100%;
  display: block;
  aspect-ratio: 3 / 4;
  object-fit: cover;
}

.pel-director__overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: clamp(1.5rem, 3vw, 2.5rem);
  background: linear-gradient(to top, oklch(0% 0 0 / 0.7) 0%, transparent 60%);
  z-index: 10;
}

.pel-director__role {
  font-family: var(--pel-font-body);
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: oklch(90% 0 0);
  margin: 0 0 0.25rem;
}

.pel-director__name {
  font-family: var(--pel-font-display);
  font-size: clamp(1.5rem, 3vw, 2.5rem);
  font-weight: 400;
  color: var(--pel-ink-light);
  margin: 0;
}
```

---

## pel-context-widget

Sticky top-right navigation panel with film thumbnail, title, metadata tags.

```html
<aside class="pel-widget" aria-label="Film context">
  <div class="pel-widget__header">
    <img src="thumb.jpg" alt="" class="pel-widget__thumb">
    <span class="pel-widget__title">Film Title</span>
    <button class="pel-widget__toggle" aria-expanded="false" aria-controls="pel-widget-dropdown">
      <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
        <path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
      </svg>
    </button>
  </div>
  <div class="pel-widget__meta">
    <span class="pel-widget__tag">Documentary</span>
    <span class="pel-widget__tag">2024</span>
    <span class="pel-widget__tag">93 min</span>
  </div>
  <div class="pel-widget__dropdown" id="pel-widget-dropdown">
    <a href="film-1.html" class="pel-widget__link">Another Film</a>
    <a href="film-2.html" class="pel-widget__link">Third Film</a>
  </div>
</aside>
```

### CSS

```css
.pel-widget {
  position: fixed;
  top: 1.5rem;
  right: 1.5rem;
  z-index: 50;
  background: var(--pel-cream);
  border: 1px solid var(--pel-border);
  border-radius: var(--pel-frame-radius);
  padding: 0.75rem 1rem;
  min-width: 200px;
  box-shadow:
    0 1px 2px oklch(15% 0 0 / 0.04),
    0 4px 12px oklch(15% 0 0 / 0.06);
}

.pel-widget__header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.pel-widget__thumb {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
}

.pel-widget__title {
  font-family: var(--pel-font-body);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--pel-ink);
  flex: 1;
}

.pel-widget__toggle {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--pel-ink-muted);
  padding: 0.25rem;
  display: flex;
  align-items: center;
}

.pel-widget__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  margin-top: 0.5rem;
}

.pel-widget__tag {
  font-family: var(--pel-font-body);
  font-size: 0.6875rem;
  font-weight: 500;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--pel-ink-muted);
  background: var(--pel-cream-deep);
  padding: 0.125rem 0.5rem;
  border-radius: 100px;
}

.pel-widget__dropdown {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows var(--pel-duration) var(--pel-ease);
  overflow: hidden;
}

.pel-widget__dropdown[aria-hidden="false"],
.pel-widget__dropdown.is-open {
  grid-template-rows: 1fr;
}

.pel-widget__dropdown > * {
  overflow: hidden;
}

.pel-widget__link {
  display: block;
  font-family: var(--pel-font-body);
  font-size: 0.8125rem;
  color: var(--pel-ink-muted);
  text-decoration: none;
  padding: 0.375rem 0;
  border-top: 1px solid var(--pel-border);
  transition: color var(--pel-duration-short) var(--pel-ease);
}
.pel-widget__link:hover { color: var(--pel-ink); }

@media (max-width: 768px) {
  .pel-widget { display: none; }
}
```

---

## pel-play-button

Red circle with play triangle icon and text reveal on hover.

```html
<button class="pel-play" aria-label="Watch trailer">
  <span class="pel-play__circle">
    <svg class="pel-play__icon" viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
      <polygon points="8,5 20,12 8,19" fill="currentColor"/>
    </svg>
  </span>
  <span class="pel-play__text">Watch Trailer</span>
</button>
```

### CSS

```css
.pel-play {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  color: var(--pel-ink);
}

.pel-play__circle {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--pel-red);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--pel-ink-light);
  transition: transform var(--pel-duration-short) var(--pel-ease);
  flex-shrink: 0;
}

.pel-play__icon {
  margin-left: 2px; /* optical center for play triangle */
}

.pel-play__text {
  font-family: var(--pel-font-body);
  font-size: 0.875rem;
  font-weight: 500;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  opacity: 0;
  transform: translateX(-8px);
  transition:
    opacity var(--pel-duration-short) var(--pel-ease),
    transform var(--pel-duration-short) var(--pel-ease);
}

.pel-play:hover .pel-play__circle {
  transform: scale(1.08);
}

.pel-play:hover .pel-play__text {
  opacity: 1;
  transform: translateX(0);
}

.pel-play:focus-visible .pel-play__circle {
  outline: 2px solid var(--pel-ink);
  outline-offset: 3px;
}
```

---

## pel-gallery

Dark-background image grid with hover effects. Full-bleed section.

```html
<section class="pel-gallery" aria-label="Gallery">
  <div class="pel-divider pel-divider--dark" data-pel="line">
    <span class="pel-divider__label">Gallery</span>
  </div>

  <div class="pel-gallery__grid" data-pel="stagger">
    <figure class="pel-gallery__item">
      <img src="still-1.jpg" alt="Scene description" loading="lazy">
    </figure>
    <figure class="pel-gallery__item">
      <img src="still-2.jpg" alt="Scene description" loading="lazy">
    </figure>
    <figure class="pel-gallery__item">
      <img src="still-3.jpg" alt="Scene description" loading="lazy">
    </figure>
    <figure class="pel-gallery__item">
      <img src="still-4.jpg" alt="Scene description" loading="lazy">
    </figure>
    <figure class="pel-gallery__item">
      <img src="still-5.jpg" alt="Scene description" loading="lazy">
    </figure>
    <figure class="pel-gallery__item">
      <img src="still-6.jpg" alt="Scene description" loading="lazy">
    </figure>
  </div>
</section>
```

### CSS

```css
.pel-gallery {
  background: var(--pel-black);
  color: var(--pel-ink-light);
  padding: var(--pel-section-gap) var(--pel-content-pad);
  margin-left: calc(-1 * var(--pel-content-pad));
  margin-right: calc(-1 * var(--pel-content-pad));
  width: calc(100% + 2 * var(--pel-content-pad));
}

.pel-gallery__grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: clamp(0.5rem, 1vw, 1rem);
  max-width: var(--pel-max-width);
  margin: 0 auto;
}

.pel-gallery__item {
  margin: 0;
  overflow: hidden;
  border-radius: 4px;
}

.pel-gallery__item img {
  width: 100%;
  display: block;
  aspect-ratio: 16 / 10;
  object-fit: cover;
  transition:
    transform var(--pel-duration) var(--pel-ease),
    filter var(--pel-duration) var(--pel-ease);
}

.pel-gallery__item:hover img {
  transform: scale(1.03);
  filter: brightness(1.08);
}

@media (max-width: 768px) {
  .pel-gallery__grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 480px) {
  .pel-gallery__grid { grid-template-columns: 1fr; }
}
```

---

## pel-prizes

Festival awards and selections grid.

```html
<section class="pel-section" aria-label="Awards">
  <div class="pel-divider" data-pel="line">
    <span class="pel-divider__label">Awards & Festivals</span>
  </div>

  <div class="pel-prizes" data-pel="stagger">
    <div class="pel-prizes__item">
      <img src="festival-logo.svg" alt="Festival Name" class="pel-prizes__logo">
      <p class="pel-prizes__name">Sundance Film Festival</p>
      <p class="pel-prizes__award">Official Selection 2024</p>
    </div>
    <div class="pel-prizes__item">
      <img src="festival-logo-2.svg" alt="Festival Name" class="pel-prizes__logo">
      <p class="pel-prizes__name">Toronto International</p>
      <p class="pel-prizes__award">Best Documentary</p>
    </div>
  </div>
</section>
```

### CSS

```css
.pel-prizes {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: clamp(1.5rem, 3vw, 2.5rem);
  text-align: center;
}

.pel-prizes__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.pel-prizes__logo {
  width: 64px;
  height: 64px;
  object-fit: contain;
  opacity: 0.7;
  filter: grayscale(100%);
  transition: opacity var(--pel-duration-short) var(--pel-ease);
}
.pel-prizes__item:hover .pel-prizes__logo {
  opacity: 1;
  filter: none;
}

.pel-prizes__name {
  font-family: var(--pel-font-body);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--pel-ink);
  margin: 0;
}

.pel-prizes__award {
  font-family: var(--pel-font-body);
  font-size: 0.75rem;
  font-weight: 400;
  color: var(--pel-ink-muted);
  margin: 0;
}
```

---

## pel-next-project

Large typography with image preview for case study navigation.

```html
<section class="pel-next" aria-label="Next project">
  <div class="pel-divider" data-pel="line">
    <span class="pel-divider__label">Next</span>
  </div>

  <a href="next-film.html" class="pel-next__link" data-pel="y">
    <div class="pel-next__text">
      <p class="pel-next__label">Next Project</p>
      <h2 class="pel-next__title">Ana Maxim</h2>
    </div>
    <div class="pel-next__preview pel-frame">
      <img src="next-thumb.jpg" alt="Scene from Ana Maxim">
    </div>
  </a>
</section>
```

### CSS

```css
.pel-next__link {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: clamp(2rem, 4vw, 4rem);
  align-items: center;
  text-decoration: none;
  color: inherit;
  padding: 2rem 0;
}

.pel-next__label {
  font-family: var(--pel-font-body);
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--pel-ink-muted);
  margin: 0 0 0.5rem;
}

.pel-next__title {
  font-family: var(--pel-font-display);
  font-size: clamp(2.5rem, 5vw, 4rem);
  font-weight: 400;
  line-height: 1.05;
  color: var(--pel-ink);
  margin: 0;
  transition: color var(--pel-duration-short) var(--pel-ease);
}

.pel-next__preview {
  max-width: 400px;
  transition: transform var(--pel-duration) var(--pel-ease);
}

.pel-next__link:hover .pel-next__title {
  color: var(--pel-ink-muted);
}
.pel-next__link:hover .pel-next__preview {
  transform: scale(1.02);
}

@media (max-width: 768px) {
  .pel-next__link {
    grid-template-columns: 1fr;
    text-align: center;
  }
  .pel-next__preview {
    max-width: 300px;
    margin: 0 auto;
  }
}
```

---

## pel-section-divider

Labeled line divider between content sections.

```html
<div class="pel-divider" data-pel="line">
  <span class="pel-divider__label">Section Name</span>
</div>
```

### CSS

```css
.pel-divider {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: clamp(1.5rem, 3vw, 2.5rem);
}

.pel-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--pel-border);
  transform-origin: left center;
}

.pel-divider__label {
  font-family: var(--pel-font-body);
  font-size: 0.6875rem;
  font-weight: 500;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--pel-ink-muted);
  flex-shrink: 0;
}

/* Dark variant for gallery section */
.pel-divider--dark::after {
  background: var(--pel-border-dark);
}
.pel-divider--dark .pel-divider__label {
  color: oklch(70% 0 0);
}
```
