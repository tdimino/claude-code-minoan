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
├── scripts/
│   ├── well.py                    # Main CLI (argparse, async orchestrator)
│   ├── _well_utils.py             # ImageResult, credentials, cache, license normalizer
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

# Check source status
uv run scripts/well.py sources

# Cache management
uv run scripts/well.py cache stats
uv run scripts/well.py cache clear
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
```

The skill is model-invocable and triggers automatically on image search, stock photo, museum image, or CC-licensed image intents.
