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
| Display / Film Titles | Playfair Display | 700 |
| Body / Commentary | Source Serif 4 | 400/600 |
| Labels / Metadata | IBM Plex Mono | 400 |
| Navigation / UI | IBM Plex Sans | 400/500 |

## Pages

| Route | Tab | Content |
|-------|-----|---------|
| `/` | Archive | Watched films grid, sort by rating/year/A-Z, TiltCard hover |
| `/queue` | To Watch | Screening Programme — single or columns view, group by source/genre |
| `/taste` | Taste | Lane calibration, 3D radar, Tom/Mary comparison |
| `/genres` | Genres | Bestiary — 16 genre medallion gallery |
| `/claudius` | Claudius | Oracle chat with procedural GLSL candle flame |

## API Endpoints

| Method | Route | Returns |
|--------|-------|---------|
| GET | `/api/films` | Full `FilmsData` from films.json |
| GET | `/api/films/:id` | Single film by kebab-case ID |
| GET | `/api/taste` | Computed taste profile + lane averages |
| GET | `/api/profiles` | Tom/Mary stats, bios, agreement metrics |
| POST | `/api/claudius` | Spawns `claude -p` subprocess, returns response |

## Three.js Components

| Component | File | Description |
|-----------|------|-------------|
| ProjectorDust | `atmosphere/ProjectorDust.tsx` | 400 golden dust motes (150 mobile), scroll-responsive |
| OracleFlame | `claudius/OracleFlame.tsx` | Procedural GLSL candle shader, loading-reactive |
| TasteRadar3D | `taste/TasteRadar3D.tsx` | 3D radar of lane averages, auto-rotation |
| TiltCard | `archive/TiltCard.tsx` | Parallax 3D tilt, 5deg max, spring physics |

SSR wrappers: `DustWrapper.tsx`, `OracleFlameWrapper.tsx`, `TasteRadar3DWrapper.tsx`.

## Key UI Components

| Component | Purpose |
|-----------|---------|
| FilmDetail | 780px side panel (desktop) / bottom sheet (mobile), poster column + detail column |
| ScreeningCard | Poster-forward horizontal card for queue |
| CandleRating | 1–5 candle flame SVGs with graduated amber tones |
| KotharAvatar | Daimonic avatar with Forge Pulse breathing ring |
| SideNav / BottomNav | Desktop sidebar / mobile bottom tabs |

## Build Commands

```bash
# Development
cd web/frontend && npm run dev          # :3000
cd web && uv run python3 server.py      # :4200

# Production
cd web/frontend && npm run build        # Static export → out/
portless crypt-librarian uv run python3 web/server.py --production
```

## Assets

| Asset | Directory | Count | Source |
|-------|-----------|-------|--------|
| Movie posters | `public/posters/` | 73 JPG + SVG fallback | TMDB API |
| Genre badges | `public/badges/` | 16 PNG | Nano Banana Pro |
| Avatars | `public/avatars/` | 5 | Real photos + AI portraits |
