# Component Gallery

UI pattern research skill backed by a local RAG collection of [component.gallery](https://component.gallery/)—60 component types, 95 design systems, 2,676+ real-world examples.

Pairs with **minoan-frontend-design**: Component Gallery provides the *what* (pattern research, implementation precedent, accessibility requirements), minoan-frontend-design provides the *how* (creative direction, typography, color, spatial composition).

## Data

| Layer | Contents |
|-------|----------|
| **Static indexes** | 3 markdown reference files for instant lookup (no RAG needed) |
| **RAG collection** | 8,692 semantic chunks via RLAMA + nomic-embed-text |
| **Deep dives** | 12 long-form component analyses fetched from GitHub |

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

# Compare sidebar navigation across design systems
python3 scripts/query.py "compare sidebar navigation patterns"

# Broader queries benefit from more chunks
python3 scripts/query.py "responsive table patterns" -k 20
```

### Ingestion

```bash
# Full pipeline: crawl site + fetch deep-dives + build RLAMA collection
python3 scripts/ingest.py --full

# Rebuild RAG from existing scraped files
python3 scripts/ingest.py --rebuild-rag

# Regenerate static indexes from scraped data
python3 scripts/build_indexes.py
```

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
│   ├── astryx-hero-pattern.md        Depth-parallax editorial hero pattern
│   └── fluid-dom-pattern.md          Stable fluid simulation over live DOM
└── scripts/
    ├── ingest.py          # Crawl + build RAG collection
    ├── build_indexes.py   # Generate static reference files
    └── query.py           # Semantic search wrapper
```

`.staging/` (not committed) holds raw crawl output and per-page markdown files used by `build_indexes.py` and RLAMA ingestion.
