# ARCHITECTURE — CRYPT LIBRARIAN

This document describes the structure of the Crypt Librarian project and the reasoning behind it. It follows [matklad's ARCHITECTURE.md guidelines](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html): it tells you where to look, not what the code does.

The full source is in the `repo/` submodule.

---

## Bird's Eye View

Three systems share the project:

| System | Directory | Role |
|--------|-----------|------|
| Data layer | `films.json`, `candidates.json`, `crypt-librarian.db` | Source of truth: 49 films, ratings, multi-voice commentary, provenance |
| Backend | `web/server.py` | FastAPI — serves API, static frontend, Claude subprocess SSE streaming |
| Frontend | `web/frontend/` | Next.js 16 static export — 6 pages, Three.js atmosphere, Tailwind v4 |
| Agent | `agent/` | Claude Agent SDK — 5-subagent autonomous discovery pipeline |
| CLI | `scripts/` | Database operations, taste seed generation, poster/trailer fetching |

The systems are coupled at `films.json`: the agent writes candidates into it, the backend reads it for API responses, the frontend renders it, and the CLI tools query/mutate it.

---

## Data Flow

```
                    ┌──────────────┐
                    │  films.json  │ ◄──── Source of truth
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
     ┌────────────┐  ┌──────────┐  ┌────────────┐
     │ FastAPI     │  │ Agent    │  │ CLI tools  │
     │ server.py   │  │ 5 subs  │  │ crypt_db   │
     └─────┬──────┘  └──────────┘  └────────────┘
           │
    ┌──────┴──────┐
    │  Next.js    │
    │  6 pages    │
    │  Three.js   │
    └─────────────┘
```

---

## Backend — `web/server.py`

FastAPI application with CORS middleware. Lifespan hook initializes SQLite session store.

### Endpoints

| Method | Route | Handler | Returns |
|--------|-------|---------|---------|
| GET | `/api/films` | `load_films()` | Full archive from `films.json` |
| GET | `/api/films/{id}` | kebab-case lookup | Single film |
| GET | `/api/taste` | `compute_taste()` | Lane averages, decade distribution |
| GET | `/api/profiles` | `compute_profile_stats()` | Tom/Mary stats, agreement metrics |
| POST | `/api/claudius/stream` | `stream_claudius()` | SSE stream from `claude -p` subprocess |
| GET | `/api/sessions` | session list | Last 30 chat sessions |
| GET | `/api/sessions/{id}/messages` | message history | Messages for a session |

### Claude Subprocess

`stream_claudius()` spawns `claude -p` with `--output-format stream-json` and pipes stdout as SSE events. Environment stripped of `CLAUDE_CODE_*` vars, `CLAUDICLE_SOUL=1` injected for ensouled mode. Session continuity via `--resume`. See [docs/claude-integration.md](docs/claude-integration.md).

### Static Serving

In production mode, serves the pre-built `web/frontend/out/` directory at `/`. The `com.minoan.crypt-librarian` launchd daemon runs the server on the Mac Mini at port 4200.

---

## Frontend — `web/frontend/`

Next.js 16 with `output: 'export'` (static HTML). Tailwind v4 with `@theme inline` for design tokens. Framer Motion for page transitions. React Three Fiber for particle atmospheres.

### Page Structure

| Route | File | Content |
|-------|------|---------|
| `/` | `app/page.tsx` | Archive — watched films grid, TiltCard hover, poster thumbnails, sort/filter |
| `/queue` | `app/queue/page.tsx` | Screening Programme — single-card or columns view, group by source/genre |
| `/taste` | `app/taste/page.tsx` | SVG radar chart + decade timeline, Tom/Mary comparison |
| `/genres` | `app/genres/page.tsx` | Bestiary — 16 genre medallion gallery |
| `/claudius` | `app/claudius/page.tsx` | Oracle chat with OracleSmoke background, SSE streaming, dev mode |

### Component Organization

Components grouped by feature domain:

| Directory | Components |
|-----------|-----------|
| `archive/` | FilmCard, FilmDetail (780px side panel), TiltCard (parallax hover), ConstellationMap (force-directed SVG) |
| `atmosphere/` | ProjectorDust (400 golden motes, global), DustWrapper (SSR-safe import) |
| `claudius/` | OracleSmoke (600-particle system), OracleSmokeWrapper, DevPanel, ToolUseCard, SessionSidebar, KotharPersonaModal, ClaudiusMarkdown |
| `queue/` | ScreeningCard (poster-forward horizontal card), EmptyQueue |
| `shared/` | SideNav (desktop), BottomNav (mobile), CandleRating (SVG flames), AvatarPill, PageTransition (amber flash), KotharAvatar (Forge Pulse), YouTubeEmbed |
| `taste/` | TasteRadar3D (SVG radar), TasteRadar3DWrapper, DecadeTimeline |
| `genres/` | BestiaryCard |

### Design Token System

All tokens defined as CSS custom properties in `app/globals.css` `:root` block, then registered as Tailwind utilities via `@theme inline`. Surface names reference physical book layers: `binding` (darkest) through `spine` (lightest). See [docs/design-system.md](docs/design-system.md).

### Three.js Components

Two WebGL canvases:

1. **ProjectorDust** — global, in `layout.tsx`. 400 particles (150 mobile), scroll-responsive drift, additive blending.
2. **OracleSmoke** — Claudius page only. 600-particle octahedron lattice system with custom GLSL shaders, dormant/active state driven by streaming status.

Both use `dpr={1}`, `powerPreference: "low-power"`, `pointerEvents: "none"`. Both have SSR-safe dynamic import wrappers. Both respect `prefers-reduced-motion`. See [docs/three-js-components.md](docs/three-js-components.md).

---

## Agent — `agent/`

Claude Agent SDK orchestration with 5 specialized subagents. Lead agent in `crypt_librarian.py` runs a discovery workflow: learn taste → discover films → validate content → track provenance → find subtitles. See [docs/agent-architecture.md](docs/agent-architecture.md).

---

## CLI — `scripts/`

| Script | Purpose |
|--------|---------|
| `crypt_db.py` | Database operations: check, save-candidate, pending, decline |
| `generate_taste_seeds.py` | Extract taste patterns from films.json → taste_seeds.json |
| `fetch_trailers.py` | YouTube trailer URL lookup |
| `flexible_discovery.py` | Discovery outside default filters (post-2016, different regions) |

---

## State Machines

### Connection Status (Claudius page)

```
idle ──► connecting ──► streaming ──► idle
  │                                    ▲
  └──────────► error ─────────────────┘
                 │                (only if no error)
                 └─── persists through finally block
```

### Film Detail Panel

```
closed ──► opening (selected film set) ──► open (side panel visible)
  ▲                                           │
  └───────────── close button / overlay ──────┘
```

---

## Extension Points

### Adding Films

1. Add entry to `films.json` (schema: `id`, `title`, `year`, `director`, `status`, `rating`, `commentary`, `categories`, `themes`, `connections`, `content_warnings`, `available_on`, `trailer_url`)
2. Run `fetch_posters.py` with `TMDB_API_KEY` to download poster JPG + generate SVG fallback
3. Film appears automatically on next page load

### Adding Pages

1. Create `app/newpage/page.tsx`
2. Add route to `SideNav.tsx` and `BottomNav.tsx`
3. Next.js static export picks it up automatically

### Modifying Three.js Atmosphere

ProjectorDust: adjust `count`, drift speeds, or colors in `ProjectorDust.tsx`. OracleSmoke: modify `COUNT`, `LATTICE_R`, `SCATTER_R`, shader code, or add new states. See [docs/three-js-components.md](docs/three-js-components.md).

### Extending Claudius

Add prompt templates in `app/claudius/page.tsx` `PROMPT_TEMPLATES` array. Each template has an `id`, `label`, `glyph`, and `prompt` string that activates skills on the backend.

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `films.json` | Source of truth — all films, ratings, commentary |
| `web/server.py` | FastAPI backend — API + static serving + Claude SSE |
| `web/frontend/app/globals.css` | Design tokens (all color/typography custom properties) |
| `web/frontend/app/layout.tsx` | Root layout — fonts, DustWrapper, skip-to-content |
| `web/frontend/app/claudius/page.tsx` | Oracle chat — SSE consumer, connection state, dev mode |
| `web/frontend/components/claudius/OracleSmoke.tsx` | 600-particle GLSL system |
| `web/frontend/components/atmosphere/ProjectorDust.tsx` | Global ambient dust |
| `agent/crypt_librarian.py` | Autonomous discovery agent |
| `agent/subagents.py` | 5 subagent definitions |
| `scripts/crypt_db.py` | Database CLI |

---

## Where to Start

- **Understand the data**: read `films.json` — it's the spine of everything
- **See the design**: open `web/frontend/app/globals.css` (tokens) and `app/layout.tsx` (structure)
- **Trace the streaming**: `app/claudius/page.tsx` `sendMessage()` → `server.py` `stream_claudius()`
- **Read the particles**: `OracleSmoke.tsx` (custom shaders) and `ProjectorDust.tsx` (ambient)
- **Follow the taste loop**: `generate_taste_seeds.py` → `agent/crypt_librarian.py` → `films.json`
