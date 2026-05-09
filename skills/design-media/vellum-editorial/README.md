# Vellum Editorial

Static editorial documentation sites with zero build step. OKLCH color science, three-font typographic hierarchy, 35 semantic components.

## Features

- **Two themes** — warm parchment (default) and dark space, switchable via CSS custom properties
- **Two styles** — editorial (Bodoni Moda / Source Serif 4) and instrument (Manrope) typography
- **Two templates** — landing page and one-pager technical overview
- **35 components** — state cards, dossiers, matrices, phase timelines, audio player, lightbox galleries, glossaries, ring visualizations, and more
- **Auth gate** — optional client-side FNV-1a courtesy gate with sessionStorage
- **Deploy-ready** — `_headers` (CF Pages security), `robots.txt`, OG/Twitter social meta tags
- **Light/dark toggle** — runtime theme switching with FOUC prevention

## Quick Start

```bash
python3 scripts/init_project.py my-docs --style editorial --theme warm --auth --deploy-ready
```

Open `my-docs/index.html` in a browser. Fonts load from Google Fonts, icons from Phosphor Icons CDN.

## Structure

```
vellum-editorial/
├── SKILL.md              # Full skill instructions
├── assets/               # Templates, CSS, JS
│   ├── _shared.css       # Core palette + typography
│   ├── _components.css   # 35 component styles
│   ├── _auth.js          # Optional auth gate
│   ├── _audio-player.js  # Optional ambient audio (Web Audio API)
│   ├── template.html     # Landing page template
│   ├── template-subpage.html
│   └── template-one-pager.html
├── references/           # Design tokens, component catalog, patterns
│   ├── component-catalog.md
│   ├── design-tokens.md
│   ├── page-architecture.md
│   └── advanced-patterns.md
└── scripts/
    └── init_project.py   # Project scaffolder
```

## Design System

Three fonts: **Bodoni Moda** (display), **Source Serif 4** (body), **Inconsolata** (mono). 50+ OKLCH custom properties organized as `base / bg / border` triples. Full token reference in `references/design-tokens.md`.

## Dependencies

None. Static HTML + CSS + vanilla JS. Fonts and icons load from CDN.
