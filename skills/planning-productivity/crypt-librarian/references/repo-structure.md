# Crypt Librarian — Repository Structure

Repo root: `~/Desktop/Programming/crypt-librarian/`

```
films.json                  # Source of truth: 73 films, ratings, multi-voice commentary
candidates.json             # Pending candidates from autonomous agent
crypt-librarian.db          # SQLite: declined films, searched sources, candidates
watchlist.md                # Human-readable viewing log
to-watch.md                 # Queue prose
recommendations.md          # Curated recs by theme

scripts/
  crypt_db.py               # CLI: check/save-candidate/pending/decline
  generate_taste_seeds.py   # Extract taste patterns → JSON for Exa seeds
  fetch_trailers.py         # YouTube trailer lookup
  flexible_discovery.py     # Discovery outside normal filters

agent/                      # Autonomous curation (Claude Agent SDK)
  crypt_librarian.py        # Lead agent — 5-phase orchestration
  subagents.py              # taste_learner, film_discoverer, content_validator, etc.
  approve.py                # Review pending candidates
  tools/database.py         # SQLite provenance tools
  init_db.py                # Schema setup

web/
  server.py                 # FastAPI backend (API + static serving + Claude subprocess)
  session_store.py          # SQLite session management
  config.py                 # Port, paths, environment
  frontend/                 # Next.js 16 + Tailwind v4 + Three.js
    app/
      globals.css           # Design tokens (Velvet Catalogue)
      layout.tsx            # Root layout with fonts
      page.tsx              # Archive (watched films grid)
      queue/page.tsx        # To Watch (screening programme)
      taste/page.tsx        # Taste profiles + 3D radar
      genres/page.tsx       # Bestiary (genre medallions)
      claudius/page.tsx     # Oracle chat + flame shader
    components/
      archive/              # FilmCard, FilmDetail, TiltCard, ConstellationMap
      atmosphere/           # ProjectorDust (golden motes), DustWrapper (SSR)
      claudius/             # OracleFlame (GLSL), ClaudiusMarkdown, SessionSidebar
      queue/                # ScreeningCard, EmptyQueue
      shared/               # SideNav, BottomNav, CandleRating, AvatarPill, YouTubeEmbed
      taste/                # TasteRadar3D + wrapper
      genres/               # BestiaryCard (if present)
    lib/
      api.ts                # fetch wrappers for /api/* endpoints
      types.ts              # Film, FilmsData, TasteData, ProfilesData, ClaudiusResponse
      badges.ts             # Category → badge mapping
      sources.ts            # Discovery source label cleanup
      youtube.ts            # extractVideoId()
    public/
      posters/              # 73 JPG + SVG fallbacks + fetch_posters.py + manifest.json
      badges/               # 16 genre medallion PNGs
      avatars/              # Tom, Mary (real + Baroque), Kothar (daimon)

agent_docs/                 # CLAUDE.md @-referenced docs
  web-app.md                # Stack, tokens, API, Three.js components
  taste-profile.md          # Calibrated taste, lane averages
  autonomous-agent.md       # Agent SDK architecture
  deep-research.md          # Exa/Firecrawl patterns, curated URLs
```

## Key Relationships

- `films.json` is read by both the FastAPI backend (`/api/films`) and the autonomous agent
- `crypt_db.py` writes to both `films.json` (via save-candidate) and `crypt-librarian.db` (provenance)
- `fetch_posters.py` reads `films.json` for the film list, writes JPGs + SVGs + `manifest.json` to `public/posters/`
- The web frontend is a static export (`next build` → `out/`) served by FastAPI in production
- `server.py` spawns `claude -p` subprocesses for the Claudius chat endpoint
- Design tokens in `globals.css` use CSS custom properties registered as Tailwind utilities via `@theme inline`
