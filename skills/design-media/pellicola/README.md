# pellicola

Cinematic case study pages for films, documentaries, and creative projects. Warm cream palette, film-frame image treatment, credit grids, dark footage galleries, scroll-choreographed reveals — all via `--pel-*` CSS custom properties. No framework dependencies, no build step.

"Pellicola" is Italian for film — literally "little skin," the celluloid stock.

## Components

| Component | Class | What it renders |
|-----------|-------|-----------------|
| Hero | `.pel-hero` | Film-frame image, title overlay, genre label, play button, scroll arrow |
| Credit Grid | `.pel-credits` | Role/name pairs in bordered grid, tracked small caps roles |
| Director Card | `.pel-director` | Cropped 3:4 portrait, dark gradient overlay, display serif name |
| Context Widget | `.pel-widget` | Sticky top-right nav: thumbnail, metadata tags, dropdown |
| Play Button | `.pel-play` | Red circle + play icon + text reveal on hover |
| Gallery | `.pel-gallery` | Full-bleed dark section, image grid with hover scale + brightness |
| Prizes | `.pel-prizes` | Festival logos (grayscale→color on hover), award names |
| Next Project | `.pel-next` | Large typography + film-frame preview for adjacent case study |
| Section Divider | `.pel-divider` | Labeled horizontal rule, dark variant for gallery |

## Modes

| Mode | Template | Composition |
|------|----------|-------------|
| `case-study` | `case-study.html` | Hero + credits + gallery + prizes + partners + next-project (~600 lines) |
| `hero` | `hero-section.html` | Film-frame hero + title + play button only (~165 lines) |
| `credits` | `credits-grid.html` | Director card + credit grid only (~215 lines) |
| `gallery` | `footage-gallery.html` | Dark gallery section only (~175 lines) |

## Architecture

```
pellicola/
├── SKILL.md                              Skill definition (triggers, rules, anti-patterns)
├── README.md                             This file
├── scripts/
│   ├── pellicola_generator.py            Generator: --mode case-study|hero|credits|gallery
│   └── validate_pellicola.py             Structural validator (34 checks)
├── assets/templates/
│   ├── case-study.html                   Full page with all 6 sections (~600 lines)
│   ├── hero-section.html                 Film-frame hero + play button (~165 lines)
│   ├── credits-grid.html                 Director card + credit grid (~215 lines)
│   └── footage-gallery.html              Dark gallery section (~175 lines)
└── references/
    ├── design-tokens.md                  Full --pel-* CSS custom property reference
    ├── color-system.md                   OKLCH palette rationale, contrast table
    ├── typography-pairing.md             3 font pairings, type scale, reflex-reject list
    ├── component-catalog.md              HTML + CSS snippets for all 9 components
    ├── animation-system.md               data-pel attributes, IntersectionObserver, parallax
    ├── page-architecture.md              Section sequence, z-index stack, scroll rhythm
    └── anti-patterns.md                  10 anti-patterns with wrong/right code examples
```

## Usage

```bash
# Generate a full case study page
python3 scripts/pellicola_generator.py --mode case-study --title "Taboo" --output taboo.html

# Generate just the hero section
python3 scripts/pellicola_generator.py --mode hero --title "Ana Maxim" --output hero.html

# Custom metadata
python3 scripts/pellicola_generator.py --mode case-study \
  --title "Taboo" --director "Shauly Melamed" \
  --genre "Documentary" --year "2024" --runtime "93 min" \
  --output taboo.html

# Validate output
python3 scripts/validate_pellicola.py output.html
python3 scripts/validate_pellicola.py --strict output.html
```

### Generator Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--mode` | (required) | `case-study`, `hero`, `credits`, `gallery` |
| `--title` | template placeholder | Film title |
| `--director` | template placeholder | Director name |
| `--genre` | `Documentary` | Genre label |
| `--year` | `2024` | Release year |
| `--runtime` | `93 min` | Runtime string |
| `--output` | stdout | Output file path |

### Validator

Runs 34 checks (10 required, 12 optional, 12 anti-pattern scans):

**Required:** viewport meta, `--pel-*` tokens, no framework imports, cream background, `prefers-reduced-motion`, Google Fonts, `data-pel` attributes, skip link, `<main>`, `<section>`.

**Optional:** IntersectionObserver, `requestAnimationFrame`, pel-frame, pel-credits, pel-gallery, pel-divider, pel-play, OKLCH colors, `var(--pel-*)`, `aria-label`, passive scroll, `loading="lazy"`.

**Anti-patterns:** white background, Inter/Roboto/system-ui fonts, border-left accent, background-clip:text, framework imports, `setInterval`, height transitions, bare `ease` timing.

`--strict` promotes anti-pattern matches from warnings to failures.

## Color System

All components read from `--pel-*` CSS custom properties. Override at `:root` to re-theme:

| Token | Default | Role |
|-------|---------|------|
| `--pel-cream` | `oklch(97.5% 0.012 85)` | Body background |
| `--pel-cream-deep` | `oklch(95% 0.015 80)` | Film-frame background |
| `--pel-black` | `oklch(10% 0 0)` | Gallery background |
| `--pel-ink` | `oklch(15% 0.005 80)` | Primary text |
| `--pel-ink-muted` | `oklch(40% 0.01 80)` | Secondary text |
| `--pel-ink-light` | `oklch(98% 0 0)` | Text on dark backgrounds |
| `--pel-red` | `oklch(55% 0.22 25)` | Play button only |
| `--pel-border` | `oklch(85% 0.01 80)` | Grid lines, dividers |
| `--pel-border-dark` | `oklch(25% 0 0)` | Dividers on dark backgrounds |

## Section Sequence

Sections can be omitted, but order is fixed:

```
hero → credits → gallery → prizes → investors → next-project
```

This matches film industry convention: title, then who made it, then what it looks like, then who recognized it.

## Scroll Animation

Declarative reveals via `data-pel` attributes:

| Attribute | Effect |
|-----------|--------|
| `data-pel="y"` | Slide up 40px + fade |
| `data-pel="alpha"` | Fade only |
| `data-pel="line"` | Horizontal line reveal (dividers) |
| `data-pel="parallax"` | Continuous parallax scroll offset |
| `data-pel="stagger"` | Children cascade with 0.1s delay |
| `data-pel="title"` | Per-line split text reveal |

All animations respect `prefers-reduced-motion: reduce`.

## Key Constraints

- **Vanilla only.** No React, Vue, Svelte. Plain HTML + CSS + JS.
- **Single-file output.** Everything in one `.html` file. CDN for Google Fonts only.
- **Cream palette.** Body is `--pel-cream`, never white. Dark gallery is one section, not the whole page.
- **`requestAnimationFrame` only.** Never `setInterval` for animation.
- **`prefers-reduced-motion` required.** Every animated effect needs a fallback.
- **Red is for play only.** `--pel-red` on the play button circle and nowhere else.
- **`grid-template-rows` for panels.** Never use height transitions.
- **Spring easing only.** Always `--pel-ease`, never bare `ease`.

## Cross-Skill Relationships

- **grainient** — All-dark pages. Pellicola is cream-first with one dark section; grainient is dark-first throughout.
- **minoan-frontend-design** — Broader creative direction. Pellicola encodes those principles for the cinematic genre.
- **vellum-editorial** — Editorial documentation. Similar single-file HTML architecture, different domain and palette.

## Attribution

Design language drawn from [Siena Film](https://siena.film) case study pages. Underlying patterns reimplemented from first principles:

- **Film-frame image treatment** — Cream padding wrapper with rounded corners and multi-layer box shadow
- **Credit grid** — Bordered CSS Grid with tracked small caps (not card-based team layouts)
- **Dark gallery** — Full-bleed palette inversion via negative margins and calc() width
- **Scroll choreography** — IntersectionObserver with declarative `data-pel` attribute system
- **Typography pairing** — Playfair Display (display serif) + DM Sans (geometric sans)
