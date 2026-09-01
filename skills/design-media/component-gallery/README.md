# Component Gallery

UI pattern research skill backed by a local RAG collection of [component.gallery](https://component.gallery/)—60 component types, 95 design systems, 2,671 real-world examples (counts derived from the crawl; regenerated 2026-09-01).

Pairs with **minoan-frontend-design**: Component Gallery provides the *what* (pattern research, implementation precedent, accessibility requirements), minoan-frontend-design provides the *how* (creative direction, typography, color, spatial composition).

## Data

| Layer | Contents |
|-------|----------|
| **Static indexes** | 3 markdown reference files + index.json for instant lookup (no RAG needed) |
| **RAG collection** | 1,285 coherent ~1KB chunks via RLAMA + nomic-embed-text (fixed 1000/200 chunking) |
| **Deep dives** | 12 long-form component analyses fetched from GitHub with commit-SHA provenance |
| **Curated patterns** | 7 reference files (AI overlay, composites, site-specific patterns) ingested alongside the crawl |

### Static References

| File | Contents |
|------|----------|
| `references/component-index.md` | All 60 components with alt names, example counts, descriptions |
| `references/design-system-index.md` | All 95 design systems with tech stack and features |
| `references/component-taxonomy.md` | Components grouped by category (Forms, Navigation, Feedback, Layout, Data Display, Actions) |
| `references/index.json` | Machine-readable JSON of all components and design systems |

## Usage

### Quick Lookup

Read the static index files directly—no query needed.

```bash
# "What's a flyout called?" → check alt names
cat references/component-index.md | grep -i flyout

# "Which design systems use Vue?"
cat references/design-system-index.md | grep -i vue
```

### Semantic Search

```bash
# How do production systems implement date picker accessibility?
python3 scripts/query.py "date picker accessibility patterns"

# Filter by component, system, or source (mesh3d, component.gallery, curated, pages, deep-dives)
python3 scripts/query.py "tool call states" --source curated
python3 scripts/query.py "focus management" --component modal

# Force the lexical fallback (also automatic when Ollama is down)
python3 scripts/query.py "empty state guidance" --lexical

# Broader queries benefit from more chunks
python3 scripts/query.py "responsive table patterns" -k 20
```

### Ingestion

```bash
# Full transactional pipeline: crawl → deep-dives → curated → validate → RAG → swap
python3 scripts/ingest.py --full

# Rebuild RAG from existing .staging/ (fixed chunking, ~1000 char chunks)
python3 scripts/ingest.py --rebuild-rag

# Dry-run: staging swap + provenance + deep-dive discovery, no crawl or RAG
python3 scripts/ingest.py --skip-crawl --skip-rag

# Regenerate static indexes from scraped data
python3 scripts/build_indexes.py
```

The pipeline is transactional: crawl output lands in `.staging-next/`, passes validation (page count sanity, frontmatter integrity, components/design-systems presence), then the RLAMA collection is rebuilt and `.staging-next/` swaps to `.staging/` (previous kept as `.staging-prev/`). RLAMA has no rename, so the embedding step itself is the remaining failure window after validation. Provenance is recorded in `.staging/crawl-meta.json` (crawl timestamp, page count, GitHub commit SHA per deep-dive file). Deep-dive files are auto-discovered from the GitHub repo tree, not hardcoded. Curated pattern references from `references/` are included in the RAG build via `curated/`.

## Components Covered

Forms (17): Checkbox, Combobox, Color picker, Date input, Datepicker, Fieldset, File upload, Form, Label, Radio button, Search input, Select, Slider, Stepper, Text input, Textarea, Toggle

Navigation (9): Breadcrumbs, Dropdown menu, Footer, Header, Link, Navigation, Pagination, Skip link, Tabs

Feedback (7): Alert, Empty state, Progress bar, Progress indicator, Skeleton, Spinner, Toast

Layout (9): Accordion, Card, Carousel, Drawer, Hero, Modal, Popover, Separator, Stack

Data Display (12): Avatar, Badge, Heading, Icon, Image, List, Quote, Rating, Table, Tree view, Video, Visually hidden

Actions (6): Button, Button group, File, Rich text editor, Segmented control, Tooltip

## Design Systems Covered

95 systems including Ant Design, Atlassian, Bootstrap, Carbon (IBM), Chakra UI, Fluent UI (Microsoft), Gestalt (Pinterest), GOV.UK, Material Design (Google), Paste (Twilio), Polaris (Shopify), Primer (GitHub), Radix, Spectrum (Adobe), shadcn/ui, and 80 more.

## Dependencies

- [RLAMA](https://github.com/dontizi/rlama) with Ollama + nomic-embed-text (for RAG queries)
- [Firecrawl](https://www.firecrawl.dev/) (for re-crawling—not needed for static index usage)
- Python 3.10+

## File Structure

```
component-gallery/
├── SKILL.md              # Claude Code skill definition
├── README.md
├── references/
│   ├── component-index.md
│   ├── component-taxonomy.md
│   ├── design-system-index.md
│   ├── index.json
│   ├── ai-components.md                AI-era interface pattern overlay
│   ├── composite-patterns.md           Multi-component composition patterns
│   ├── mesh3d-gallery.md               3D mesh gallery patterns
│   ├── astryx-hero-pattern.md          Depth-parallax editorial hero pattern
│   ├── fluid-dom-pattern.md            Stable fluid simulation over live DOM
│   ├── composio-glitch-hero-pattern.md Generative pixel-glitch canvas hero
│   └── composio-agent-console-pattern.md Product diorama of tool-call panels
├── evals/evals.json       # 6 skill evals
└── scripts/
    ├── ingest.py          # Transactional crawl + validate + RAG build
    ├── build_indexes.py   # Generate static reference files (derived counts)
    ├── test_build_indexes.py  # Parser fixtures (15 tests)
    ├── query.py           # Semantic search + filters + lexical fallback
    ├── fetch_mesh3d.py    # mesh3d.gallery directory (24h cache in .staging/)
    └── validate_links.py  # Link health check over index.json
```

`.staging/` (not committed) holds raw crawl output and per-page markdown files used by `build_indexes.py` and RLAMA ingestion.
