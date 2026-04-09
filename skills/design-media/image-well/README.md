# image-well

Multi-source image search and download aggregator for Claude Code. Searches 12 image APIs in parallel through a single CLI, with unified result format, license filtering, domain presets, caching, and bulk download with metadata sidecars.

## When to Use

Any time a project needs images: stock photography, museum art, NASA space imagery, CC-licensed photos, SVG icons, or AI-generated fallbacks. Fills the gap between having image *processing* tools (image-forge, nano-banana-pro) and having no image *sourcing* tool beyond Wikimedia Commons.

## Sources

| Tier | Source | Corpus | Key Required | License |
|------|--------|--------|-------------|---------|
| 1 | Openverse | 800M+ CC items | No | CC variants |
| 1 | Wikimedia Commons | Millions | No | CC variants |
| 1 | Met Museum | 375k objects | No | CC0 |
| 1 | NASA Images | 140k assets | No | Public Domain |
| 2 | Pexels | Large | `PEXELS_API_KEY` | Pexels License |
| 2 | Pixabay | Large | `PIXABAY_API_KEY` | Pixabay License |
| 2 | Unsplash | Large | `UNSPLASH_ACCESS_KEY` | Unsplash License |
| 3 | Smithsonian | Millions | No | CC0 |
| 3 | Europeana | 50M+ items | `EUROPEANA_API_KEY` | Mixed |
| 3 | Iconify | 275k icons | No | Various |
| 3 | Pollinations AI | AI gen | No | Free Use |

**Rijksmuseum** (700k CC0 objects) is listed but unavailable—their REST API returned HTTP 410 Gone as of March 2026. The collection is still browsable at rijksmuseum.nl; sourcing images would require a Playwright or agentic browser-based search against the web UI.

Tier 1 sources work with zero API keys. Tier 2/3 keys are optional and go in `~/.config/env/secrets.env`.

## Structure

```
image-well/
├── SKILL.md                       # Skill definition and workflows
├── README.md                      # This file
├── scripts/
│   ├── well.py                    # Main CLI (argparse, async orchestrator)
│   ├── _well_utils.py             # ImageResult, credentials, cache, license normalizer, formatters
│   └── sources/
│       ├── __init__.py            # Registry, presets, tier lists
│       ├── base.py                # Abstract ImageSource class
│       ├── openverse.py           # api.openverse.org
│       ├── wikimedia.py           # commons.wikimedia.org
│       ├── met_museum.py          # collectionapi.metmuseum.org (two-step: IDs → details)
│       ├── nasa.py                # images-api.nasa.gov
│       ├── pexels.py              # api.pexels.com
│       ├── pixabay.py             # pixabay.com/api
│       ├── rijksmuseum.py         # API defunct (410 Gone)
│       ├── unsplash.py            # api.unsplash.com
│       ├── smithsonian.py         # api.si.edu (category/art_design endpoint)
│       ├── europeana.py           # api.europeana.eu
│       ├── iconify.py             # api.iconify.design (SVG icons)
│       └── pollinations.py        # image.pollinations.ai (AI gen fallback)
└── references/
    └── api-reference.md           # Per-source endpoint docs
```

## Usage

```bash
# Search across default sources (Tier 1: Openverse, Wikimedia, Met, NASA)
uv run scripts/well.py search "ancient Minoan fresco"

# Use a preset
uv run scripts/well.py search "F-35 fighter jet" --preset military
uv run scripts/well.py search "Rembrandt portrait" --preset museum
uv run scripts/well.py search "sunset beach" --preset stock

# Specific sources
uv run scripts/well.py search "Mars rover" --sources nasa --limit 5

# License filter
uv run scripts/well.py search "pottery" --license cc0

# Download with metadata sidecars
uv run scripts/well.py search "landscape" --format download --output ./images/

# JSON output for piping
uv run scripts/well.py search "cat" --format json

# HTML preview gallery (auto-opens on macOS)
uv run scripts/well.py search "bronze statue" --format html

# 3D scrollable tunnel gallery (auto-opens, copies FX module sibling)
uv run scripts/well.py search "Aegean fresco" --preset museum \
    --format tunnel --output ~/Desktop/aegean-corridor.html

# Check source status
uv run scripts/well.py sources

# Cache management
uv run scripts/well.py cache stats
uv run scripts/well.py cache clear
```

## Output Formats

| `--format` | What it does | Notes |
|---|---|---|
| `table` (default) | ASCII table to stdout | Source, title, dimensions, license, URL |
| `json` | JSON array to stdout | Pipeable into other tools |
| `urls` | One URL per line | Pipeable into `xargs curl` etc. |
| `download` | Download files + metadata sidecars | Uses `--output` as the directory |
| `html` | Preview gallery in `~/.cache/image-well/preview.html` | Auto-opens on macOS |
| `tunnel` | 3D scrollable corridor with images on the walls | See bridge section below |

## threejs-particle-canvas Bridge

`--format tunnel` injects the search-result URLs into the **Mode 3 (Infinite Gallery Tunnel)** template from the `threejs-particle-canvas` skill, producing a self-contained scrollable 3D corridor where each image is embedded on one of four walls.

**How the bridge works:**

1. Reads `~/.claude/skills/threejs-particle-canvas/assets/tunnel-gallery-source.html`
2. Replaces the `IMAGES_INJECTION_POINT` sentinel (`const IMAGE_MANIFEST = null;`) with a JS array of the URLs
3. Updates the HTML `<title>` to include the search query
4. **Copies `assets/phosphor-vigil.js` as a sibling of the output HTML.** The template imports the FX module as a static ES module — the import resolves regardless of `CONFIG.fx`, so the file must exist next to the HTML even when the CRT effect is disabled.

If `--output` is the default download directory (`./well-images`), the tunnel writes to `~/.cache/image-well/tunnel.html`. Pass an explicit `--output some-name.html` to control the location.

**Requirements:**

- The `threejs-particle-canvas` skill must be installed (the bridge raises a clear `FileNotFoundError` with install instructions otherwise)
- A modern browser with WebGL support (Chrome, Safari, Firefox, Edge — all recent versions)

**Workflow example:**

```bash
# Search the museum preset, get a CC0-only filter, open the result as a 3D corridor
uv run ~/.claude/skills/image-well/scripts/well.py search "Minoan pottery" \
    --preset museum --license cc0 --limit 30 \
    --format tunnel --output ~/Desktop/minoan.html
# (auto-opens in default browser)
```

## Presets

| Preset | Sources | Use Case |
|--------|---------|----------|
| `military` | nasa, wikimedia, smithsonian | Defense/military imagery (CC0 only) |
| `museum` | met, rijksmuseum, smithsonian | Art, antiquities, historical (CC0 only) |
| `texture` | wikimedia, pollinations | Game dev, 3D materials |
| `stock` | pexels, pixabay, unsplash | Editorial photography |
| `all-free` | openverse, wikimedia, met, nasa, smithsonian | All no-key sources |

## Key Design Decisions

- **Parallel async search** via `aiohttp` + `asyncio.gather()` with per-source timeouts
- **Results interleaved** round-robin across sources, not grouped—best images first regardless of origin
- **Graceful degradation**—missing API keys skip the source with a stderr warning, never crash
- **PEP 723** inline script metadata—`uv run` auto-resolves dependencies
- **24-hour file cache** at `~/.cache/image-well/` keyed on query+sources+license
- **No auto-integration** with image-forge—search and download only (Unix philosophy)
- **Cross-skill bridge for tunnel format** — single one-directional dependency on `threejs-particle-canvas`. Bridge reads template files only; canvas skill has zero knowledge of image-well.

## API Key Registration

| Service | URL | Free Tier |
|---------|-----|-----------|
| Pexels | https://www.pexels.com/api/ | 200/hr, no attribution |
| Pixabay | https://pixabay.com/api/docs/ | 5k/day, no attribution |
| Unsplash | https://unsplash.com/developers | 50/hr demo, attribution required |
| Europeana | https://pro.europeana.eu/page/get-api | Free, 50M+ items |

## Installation

```bash
cp -R image-well/ ~/.claude/skills/image-well/

# Optional: add API keys for Tier 2/3 sources
echo 'export PEXELS_API_KEY="your_key"' >> ~/.config/env/secrets.env
echo 'export PIXABAY_API_KEY="your_key"' >> ~/.config/env/secrets.env
echo 'export UNSPLASH_ACCESS_KEY="your_key"' >> ~/.config/env/secrets.env
echo 'export EUROPEANA_API_KEY="your_key"' >> ~/.config/env/secrets.env

# For --format tunnel, also install the threejs-particle-canvas skill
cp -R threejs-particle-canvas/ ~/.claude/skills/threejs-particle-canvas/
```

The skill is model-invocable and triggers automatically on image search, stock photo, museum image, or CC-licensed image intents.
