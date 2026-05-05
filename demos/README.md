# Demos

Complete projects built with claude-code-minoan skills---showcasing what the configuration produces end-to-end.

## Project Thorn

**Imperial Intelligence terminal intercepting a Bothan transmission.**

Single HTML file, no build step. Aurebesh decryption animation, cue-scored audio, holographic dossier modal, interactive terminal with 25+ commands. Built from a 2003-era Star Wars Galaxies character bio.

![Project Thorn terminal](project-thorn/screenshot-default.png)

- **Stack**: Single HTML file, vanilla JS, Departure Mono + Aurebesh fonts, Web Audio API
- **Skills used**: `threejs-particle-canvas`, `minoan-frontend-design`, `nano-banana-pro`
- **Docs**: [ARCHITECTURE.md](project-thorn/ARCHITECTURE.md), [audio-choreography](project-thorn/docs/audio-choreography.md), [animation-pipeline](project-thorn/docs/animation-pipeline.md), [terminal-commands](project-thorn/docs/terminal-commands.md), [design-system](project-thorn/docs/design-system.md)

```bash
open project-thorn/index.html
```

---

## Crypt Librarian --- VELVET CATALOGUE

**Film curation archive with an ensouled oracle and autonomous discovery agent.**

Three.js-atmospheric web interface for pre-2016 cinema---tilt cards, golden dust motes, an oracle chat backed by `claude -p` subprocess streaming, and a 5-subagent discovery pipeline that compounds taste over time. 49 films, multi-voice commentary, candle-flame ratings.

![VELVET CATALOGUE archive](crypt-librarian/screenshots/archive.png)

- **Stack**: FastAPI + Next.js 16 + Tailwind v4 + React Three Fiber + Claude Agent SDK + SQLite
- **Skills used**: `crypt-librarian`, `minoan-frontend-design`, `exa-search`, `firecrawl`, `nano-banana-pro`, `cloudflare`
- **Docs**: [ARCHITECTURE.md](crypt-librarian/ARCHITECTURE.md), [design-system](crypt-librarian/docs/design-system.md), [three-js-components](crypt-librarian/docs/three-js-components.md), [claude-integration](crypt-librarian/docs/claude-integration.md), [agent-architecture](crypt-librarian/docs/agent-architecture.md)
- **Live**: Included as a [git submodule](crypt-librarian/repo/) pointing to the source repo

```bash
cd crypt-librarian/repo/web/frontend/out && python3 -m http.server 4200
```

---

## Adding a demo

A demo in this folder should be a self-contained project (or submodule) with:

1. **README.md** --- what it is, how to run it, screenshots
2. **ARCHITECTURE.md** --- system anatomy, state machines, extension points
3. **docs/** --- design system, component docs, integration guides
4. **screenshots/** --- key views captured from the running application

Each demo should reference the claude-code-minoan skills it was built with.
