# Project Thorn

Single-file HTML terminal (`index.html`). No build step, no dependencies.

## Architecture

See ARCHITECTURE.md — codemap with verified line ranges, state machine, extension points.

## Conventions

- All code lives in `index.html` (CSS, HTML, JS in that order)
- CSS variables in `:root` (lines 36–64) — never hardcode colors
- Sounds use Web Audio API, never `<audio>` elements
- Terminal commands: add to `TERMINAL_CMDS` (line 2464) or future `TERMINAL_FNS`
- `AudioContext` created lazily on first user gesture — never call `audio.init()` automatically
- `prefers-reduced-motion: reduce` disables all animation and audio
- Test changes by opening `index.html` locally — no server needed
- Deploy: `wrangler pages deploy . --project-name jiff-gorda-star-wars-galaxies`

## File Discipline

- Keep everything in `index.html` until a framework migration (see `docs/soul-integration.md`)
- Assets are siblings of `index.html` — relative paths only, no CDN
- Development screenshots (`_*.png`, `preview-*.png`) are not served — don't delete them
- `screenshots/` contains responsive testing artifacts

## Responsive

Three breakpoints: 1024px (tablet), 768px (phone landscape), 480px (phone portrait). See ARCHITECTURE.md § Responsive for details. `.line--break` must preserve `grid-template-columns: 1fr` at all breakpoints.

## Audio

Three-track Web Audio engine. `AUDIO_CUES` table (line 1959) scores accent tracks to narrative moments. Terminal commands use `01-scifi-computer-terminal-unfa.mp3` for ACK and a square-wave oscillator for DENY. Mute state persists via `localStorage('thorn-muted')`.

## Reference

- `docs/audio-choreography.md` — cue timing, volume arc
- `docs/animation-pipeline.md` — Aurebesh decrypt, state machine, controls
- `docs/terminal-commands.md` — all commands and responses
- `docs/line-types-tokens.md` — 7 line types, inline markers
- `docs/design-system.md` — CSS variables, colors, layers
- `docs/soul-integration.md` — Open Souls template patterns
- `docs/roadmap.md` — multiplayer channel vision
