# VELVET CATALOGUE — Web App Reference

Local-only web interface hosted on Mac Mini via launchd (`com.minoan.crypt-librarian`). Accessible at `http://kothar.local:4200`.

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) — `web/server.py` |
| Frontend | Next.js 16 static export |
| Styling | Tailwind v4 + CSS custom properties |
| Animation | Framer Motion |
| 3D | React Three Fiber + drei |
| Chat | `claude -p` subprocess via `web/claude_handler.py` |
| Sessions | SQLite — `web/sessions.db` |

## Design Direction

Conceptual direction: **candlelit rare-book room**. Leather, foxed parchment, amber lamplight, wine-dark velvet.

| Dial | Value |
|------|-------|
| VARIANCE | 6 (editorial asymmetry) |
| MOTION | 4 (subtle hover warmth) |
| DENSITY | 5 (comfortable reading) |

## Color Tokens

Surface hierarchy (physical book layers):
- `--binding` (#1a1612) → `--endpaper` (#241f1a) → `--page` (#2e2822) → `--crease` (#3d352d) → `--spine` (#4a4038)

Accents:
- `--amber` (#d4a017) — primary, lamplight
- `--amber-dim` (#a07b10)
- `--amber-rgb` (212, 160, 23) — for rgba()
- `--oxblood` (#8b2232) — secondary, velvet
- `--oxblood-dim` (#6b1a27)
- `--oxblood-text` (#e06070) — WCAG AA on dark surfaces

Text:
- `--parchment` (#f4efe6) — cream, primary
- `--vellum` (#c4b9a7) — aged, secondary
- `--foxing` (#9a8d7b) — muted, tertiary

All tokens registered as Tailwind utilities via `@theme inline` in `globals.css`.

## Typography

| Role | Font | Weight |
|------|------|--------|
| Display / Film Titles | Cormorant Garamond | 400/600/700 |
| Body / Commentary | Source Serif 4 | 400/600 |
| Labels / Metadata | JetBrains Mono | 400/500 |
| Navigation / UI | Figtree | 400/500/600 |

## Pages

| Route | Tab | Content |
|-------|-----|---------|
| `/` | Archive | Watched films grid, sort by rating/year/A-Z, TiltCard hover |
| `/queue` | To Watch | Screening Programme — single or columns view, group by source/genre |
| `/taste` | Taste | Lane calibration, SVG radar + decade timeline side-by-side, Tom/Mary comparison |
| `/genres` | Genres | Bestiary — 16 genre medallion gallery |
| `/claudius` | Claudius | Oracle chat with Oracle Smoke particle background, dev mode (Ctrl+Shift+D), connection status |

## API Endpoints

| Method | Route | Returns |
|--------|-------|---------|
| GET | `/api/films` | Full `FilmsData` from films.json |
| GET | `/api/films/:id` | Single film by kebab-case ID |
| GET | `/api/taste` | Computed taste profile + lane averages |
| GET | `/api/profiles` | Tom/Mary stats, bios, agreement metrics |
| POST | `/api/claudius/stream` | SSE endpoint — spawns `claude -p` with `stream-json`, pipes events |
| GET | `/api/sessions` | List chat sessions (limit 30) |
| GET | `/api/sessions/:id/messages` | Messages for a session |

## Three.js Components

| Component | File | Description |
|-----------|------|-------------|
| ProjectorDust | `atmosphere/ProjectorDust.tsx` | 400 golden dust motes (150 mobile), scroll-responsive |
| OracleSmoke | `claudius/OracleSmoke.tsx` | 600-particle system orbiting octahedron lattice, dormant/active states, custom GLSL |
| DevPanel | `claudius/DevPanel.tsx` | Toggleable dev panel (Ctrl+Shift+D) showing SSE events, connection status, active tools |
| TasteRadar3D | `taste/TasteRadar3D.tsx` | SVG radar of lane averages with viewBox padding fix |
| DecadeTimeline | `taste/DecadeTimeline.tsx` | Horizontal bar chart of films by decade |
| TiltCard | `archive/TiltCard.tsx` | Parallax 3D tilt, 5deg max, spring physics |
| ToolUseCard | `claudius/ToolUseCard.tsx` | Renders tool invocations during/after streaming |

SSR wrappers: `DustWrapper.tsx`, `OracleSmokeWrapper.tsx`, `TasteRadar3DWrapper.tsx`.

## Key UI Components

| Component | Purpose |
|-----------|---------|
| FilmDetail | 780px side panel (desktop) / bottom sheet (mobile), poster column + detail column |
| ScreeningCard | Poster-forward horizontal card for queue (120px poster, Claude teaser, trailer indicator) |
| CandleRating | 1–5 candle flame SVGs with graduated amber tones |
| KotharAvatar | Daimonic avatar with Forge Pulse (4s amber ring breathing) |
| KotharPersonaModal | Persona modal: mythology, soul architecture, soul.md quote |
| SideNav / BottomNav | Desktop sidebar / mobile bottom tabs |
| SessionSidebar | Chat session list for Claudius page |

## Build Commands

```bash
# Development
cd web/frontend && npm run dev          # :3000
cd web && uv run python3 server.py      # :4200

# Production
cd web/frontend && npm run build        # Static export → out/
portless crypt-librarian uv run python3 web/server.py --production
```

## Cloudflare Deployment

Deployed to Cloudflare Pages at `buttia-cinema.pages.dev` (basic auth via `functions/_middleware.ts`, password: "hoodrats").

```bash
cd web/frontend && npm run build
wrangler pages deploy out --project-name buttia-cinema
```

## Assets

| Asset | Directory | Count | Source |
|-------|-----------|-------|--------|
| Movie posters | `public/posters/` | 49 JPG + SVG fallback | TMDB API |
| Genre badges | `public/badges/` | 16 PNG | Nano Banana Pro |
| Avatars | `public/avatars/` | 5 | Real photos + AI portraits + daimon |
