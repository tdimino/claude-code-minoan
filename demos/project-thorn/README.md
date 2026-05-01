# PROJECT THORN

Imperial Intelligence terminal intercepting an encrypted transmission from a Bothan informant named Ora on Tatooine. Built from a 2003-era Star Wars Galaxies character bio (Vorian Ducal / Jiff Gorda)—animated with Aurebesh decryption, cue-scored audio, and a holographic dossier modal. Single HTML file, no build step.

![Default state — Aurebesh decryption in progress](screenshot-default.png)

![Decoded transcript with SIGNAL LOST](screenshot-burst.png)

![Interactive terminal — status command](screenshot-terminal.png)

![Holographic dossier modal](screenshot-dossier.png)

## Open it

```bash
open index.html
```

No build, no server, no dependencies.

## Design

Bloomberg Terminal meets Imperial CRT. Edge-to-edge data, single-pixel borders, monospace, amber phosphor with red for classified.

The original bio was written ~2003–2005 on the SWG forums as in-character roleplay. Chat-log structure: dialogue, emotes, system messages, narrative monologue, the player tipping 6,000 Imperial credits to a Bothan spy. This page performs that text live—character by character, encrypted in Aurebesh glyphs, then decrypted into Latin script with a three-phase animation.

## Controls

| Key | Button | Action |
|-----|--------|--------|
| `R` | RE-DECRYPT | Re-encrypt and replay the full intercept |
| `V` | DEGRADE | Chromatic aberration + heavy scanlines |
| `Space` | BURST | Burst-decode everything, jump to SIGNAL LOST |
| `L` | TRACE | Signal-trace diagnostic log overlay |
| `M` | AUDIO | Mute/unmute (persists via localStorage) |
| `Up` / `Down` | — | Cycle through terminal command history |
| `Tab` | — | Autocomplete command or argument |
| `Ctrl+U` | — | Clear terminal input line |

Portrait click opens the holographic dossier modal. Type `auth alderaan` in the terminal to unlock clickable dossier cross-links on all marked names in the transcript.

## Assets

| File | Size | License |
|------|------|---------|
| `DepartureMono-Regular.woff2` | 22 KB | SIL OFL (Helena Zhang) |
| `Aurebesh.woff2` | 12 KB | Fan-made glyph font |
| `bothan-ora_image_0_0.jpg` | 650 KB | AI-generated portrait (Gemini 3 Pro Image) |
| `bothan-ora-seal.png` | 20 KB | AI-generated seal |
| `jiff-gorda-nar-shaddaa.jpg` | ~200 KB | AI-generated portrait (Gemini 3 Pro Image) |
| `sfx-base.mp3` | 505 KB | Freesound (CC0/CC-BY) |
| `sfx-accent-a.mp3` | 307 KB | Freesound (CC0/CC-BY) |
| `sfx-accent-b.mp3` | 280 KB | Freesound (CC0/CC-BY) |
| `audio-candidates/01-scifi-computer-terminal-unfa.mp3` | 72 KB | Freesound (CC0) |

Major Mono Display loaded via Google Fonts for the ORA name display.

## Documentation

| File | Contents |
|------|----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Single-file anatomy, codemap with line ranges, state machine, extension points |
| [docs/audio-choreography.md](docs/audio-choreography.md) | 19-cue table, volume arc, 3-track engine |
| [docs/animation-pipeline.md](docs/animation-pipeline.md) | Aurebesh 3-phase decrypt, block transitions, state machine |
| [docs/terminal-commands.md](docs/terminal-commands.md) | 25+ commands, auth system, history, autocomplete |
| [docs/line-types-tokens.md](docs/line-types-tokens.md) | 7 line types, inline markers (§, ¤, ¶), tooltips |
| [docs/design-system.md](docs/design-system.md) | CSS variables, color hierarchy, layer model, responsive tiers |
| [docs/soul-integration.md](docs/soul-integration.md) | Open Souls / Bazaar integration guide |
| [docs/portrait-generation.md](docs/portrait-generation.md) | Nano Banana Pro prompts, style-lock technique, iteration log |
| [gen/compare.html](gen/compare.html) | Portrait gallery — all generated characters, side-by-side comparison |
| [docs/roadmap.md](docs/roadmap.md) | Multiplayer channel vision |

## Built with

Designed and built using [claude-code-minoan](https://github.com/tdimino/claude-code-minoan) skills.
