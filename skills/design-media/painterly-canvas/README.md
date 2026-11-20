# painterly-canvas

Painterly, hand-brushed 3D scenes and walkable worlds in a single HTML file, with Canvas 2D only: no WebGL, no libraries, no assets.

Distilled from [*Endless Painted World — Living Impressions*](https://endless-painted-world.georgekenwright.workers.dev/) by George Kenwright ([@GeokenAI](https://x.com/GeokenAI)), built with Google DeepMind's Gemini 4 Neon—the template the skill grew from.

## How it works

A software camera projects world points to the screen, and everything visible is laid down as layered brushstrokes. Each stroke's jitter is hashed from its stable id and a frame epoch, so the paint breathes at 12 fps without flickering.

| Mode | Output |
|------|--------|
| `still` | One composed view, breathing in place |
| `scene` | A bounded place with look and walk (default) |
| `world` | Endless terrain with regions and landmarks |
| `extend` | New content inside a copy of a finished world: SE-TO-I-JA (ours) or the genesis |

## Why it exists

Without the reference material Claude makes the same mistakes each time: `Math.random()` in the painter (the image boils), stroke ids taken from a per-frame list (strokes re-roll when the camera moves), ground paint angled in screen space (it floats like stickers), ground quads sorted on mean depth (strokes get sliced), and separate fog curves for near and far (a band where they meet). The full symptom-to-cause tables are in `references/stroke-engine.md` §9 and `references/world-pipeline.md` §12.

## Try it

Run from the skill directory. `agent-browser` is needed for the stills.

```bash
# The starter, live: drag to look, WASD or arrows to walk, Q/E to turn
open assets/painterly-starter.html

# One deterministic frame at dusk
agent-browser open "file://$PWD/assets/painterly-starter.html?frame=5&tod=0.74"
agent-browser screenshot "$PWD/dusk.png"

# The genesis at a named preset, after fetching it per assets/genesis/PROVENANCE.md
agent-browser open "file://$PWD/assets/genesis/endless-painted-world.html?at=lighthouse-top"
```

`?stats=1` on the starter reports canvas calls for the last painted frame in `window.__paintStats`. Budgets and the measurement method are in `references/world-pipeline.md` §11.

## First world from a Gemini 4 model

George built the genesis with Gemini 4 Neon. `scripts/first_world.py` asks Neon, or any model of its series, to paint the first draft of a new world through OpenRouter, then feeds Claude's critique and screenshots back for the next draft. It needs `OPENROUTER_API_KEY` and nothing beyond the Python standard library.

```bash
python3 scripts/first_world.py models                                   # the live series, with prices
python3 scripts/first_world.py paint "A fishing village on a tidal estuary" --model neon --session estuary
python3 scripts/first_world.py paint "Terraced olive hills" --only neon hydrogen carbon   # same brief, in parallel
python3 scripts/first_world.py revise estuary "Water needs moving strokes" --shots noon.png dusk.png
python3 scripts/check_world.py painted-worlds/estuary/001_neon.html     # static check, also run on every draft
python3 scripts/check_world.py painted-worlds/estuary/001_neon.html --browser   # then load each pose twice and compare pixels
python3 scripts/test_first_world.py                                     # offline tests, no key
```

Drafts land in `painted-worlds/<session>/NNN_<model>.html` beside a JSON sidecar with usage, cost and the check result. A revision comes back as search-and-replace edits, applied locally to the parent draft: an edit that does not match exactly one place is rejected and reported, and a draft that lost an edit is saved as `.partial.html`. Every call prints a cost ceiling and refuses to start above `--max-cost`. Generated pages are untrusted code, so each is saved with a no-network Content-Security-Policy.

## Structure

```
painterly-canvas/
├── SKILL.md                            Workflow, the rules the look depends on, dials. Start here
├── assets/
│   ├── painterly-starter.html          545-line kernel to copy, render-tested
│   ├── prompts/first-world.md          System brief sent to the model: rules and URL test contract
│   ├── worlds/se-to-i-ja.html          A finished bounded world on the starter: Minoan Zakros. Ours to extend and publish
│   └── genesis/
│       ├── PROVENANCE.md               Author, source URL, checksum, fetch command, rights
│       └── endless-painted-world.html  The source work. Gitignored: fetch it locally
├── scripts/
│   ├── first_world.py                  paint, revise, models, list: Gemini 4 drafts through OpenRouter
│   ├── check_world.py                  Static check of any painterly page, plus a twice-loaded pixel comparison (--browser)
│   └── test_first_world.py             Offline tests: edit application, token clamp, document extraction
├── references/
│   ├── stroke-engine.md                Read when changing how marks look
│   ├── world-pipeline.md               Read when changing what is drawn and in what order
│   ├── living-details.md               Read when adding weather, interiors, clicks or audio
│   ├── genesis-map.md                  Read before opening the genesis: name map and line index
│   └── se-to-i-ja-map.md               Read before opening the Zakros world: modules, functions and techniques by line
└── evals/
    ├── evals.json                      Three test prompts with verifiable expectations
    └── files/flicker-bug.html          A painted shoreline with two stroke-engine faults, for eval 2
```

## Known limitations and what to improve

| Limitation | Improve by |
|---|---|
| Far terrain still resamples as the walker moves (turning is fixed) | Give each ring its own world lattice, crossfaded |
| Close steep faces get one wash per quad, not a clipped grid of strokes | Port the third wash rule (`world-pipeline.md` §7) |
| Far cells at a waterline show vertical-edged blocks | Color each far cell from its four vertices, not its center |
| Objects float on the land | Add cast shadows and water reflections (`world-pipeline.md` §7) |
| No weather, buildings, landmarks, collision or audio | Port one system at a time from `living-details.md` |
| Paint can show over a steep ridge | Tune the `maxCz + 4.5` ground sort bias per scene |
| A model call stops at 65,536 output tokens, so one call paints one bounded scene | Build larger worlds by hand on the kernel, with model drafts as studies |
| `revise` still sends the whole file in, though only edits come back | Send the functions the critique names, not the document |
| Evals and trigger tests are written but unrun | Run `evals/evals.json` and the description-optimization loop |

## Origin & Attribution

- **Source work**: [*Endless Painted World — Living Impressions*](https://endless-painted-world.georgekenwright.workers.dev/) by **George Kenwright** ([@GeokenAI](https://x.com/GeokenAI)), released 2026-11-18—"an endless expressionist world, all in a single HTML file." Every technique this skill documents was learned from his file
- **Model**: **Gemini 4 Neon** by Google DeepMind, the model George built the work with
- **Starter kernel**: a simplified reimplementation of his method. Its brushstroke function is modeled on his `paintedStroke`
- **References**: prose written for this skill from a reading of his code
- **Pink noise**: Paul Kellet's refined filter, used in the genesis soundscape

---

*George Kenwright's file is unlicensed, so this repository does not carry it: fetch it into `assets/genesis/` with the checksummed command in `assets/genesis/PROVENANCE.md`.*
