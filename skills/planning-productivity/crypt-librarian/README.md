# Crypt Librarian

Curate film recommendations with a gothic/occult sensibility---literary texture, historical grandeur, pre-2016 craftsmanship. Search via Exa and Firecrawl; validate against content filters; build watchlists with provenance tracking; run autonomous weekly discovery. Includes a flexible mode for requests outside the default taste profile.

**Last updated:** 2026-04-21

---

## Why This Skill Exists

Finding films that match a specific curatorial sensibility---occult ritual, literary DNA, sensuality without exploitation, grand scale with personal stakes---requires cross-referencing multiple sources (Letterboxd, Criterion, MUBI, critical essays) against a calibrated taste profile. This skill systematizes that curation with research tools, content filters, and an archive of rated films.

---

## Structure

```
crypt-librarian/
  SKILL.md                          # Full workflow with research methodology
  README.md                         # This file
  references/
    calibrated-taste-profile.md     # Taste calibration from rated films
    directors-and-themes.md         # Director lists by sensibility
    sources.md                      # Curated URLs for scraping
  scripts/
    exa_film_search.py              # Exa API: search, contents, similar, research
    flexible_discovery.py           # Discovery outside default filters
    log_discovery.sh                # Log discovery session
    validate_year.sh                # Verify pre-2016 release
  workflows/
    archive-manager.md              # films.json schema and operations
    content-validator.md            # Exclusion checklist
    film-researcher.md              # Discovery search patterns
    taste-analyzer.md               # Pattern extraction workflow
```

---

## Workflow

1. **Check the archive** --- Search `films.json` for existing matches before external search
2. **Search** --- Exa research for critical discourse, Exa search for web discovery
3. **Filter** --- Pre-2016, content warnings, taste calibration
4. **Validate** --- DoesTheDogDie.com, IMDb Parents Guide
5. **Present** --- Title, year, director, sensibility match, trailer link

---

## Scripts

| Script | Purpose |
|--------|---------|
| `exa_film_search.py` | 4 Exa endpoints: search, contents, similar, research |
| `flexible_discovery.py` | Discovery outside default filters (post-2016, different genres) |
| `validate_year.sh` | Verify pre-2016 release date |
| `log_discovery.sh` | Log a discovery session |

### Flexible Discovery

For requests outside the default taste profile:

```bash
python3 flexible_discovery.py "Korean revenge thrillers" --region asian --mood thriller
python3 flexible_discovery.py "cozy mysteries" --era 90s --region british
python3 flexible_discovery.py "films like Drive" --mood noir --limit 20
```

---

## Touchstone Films

Films that define the taste profile:

- **Pasolini's Medieval Trilogy** --- Earthy, literary, folkloric
- **Eyes Wide Shut** --- Occult ritual, dreamlike precision
- **The Long Goodbye** --- Revisionist noir, 70s cynicism
- **Alexander** --- Historical epic with tortured psyche
- **Interview with the Vampire** --- Gothic romance, melancholy immortality
- **300 Years of Longing** --- Romantic fantasy, storytelling about storytelling

---

## Autonomous Curation

The Crypt Librarian includes an autonomous agent (Claude Agent SDK) for weekly discovery:

```bash
python3 ~/Desktop/Programming/crypt-librarian/agent/crypt_librarian.py   # Run discovery
python3 ~/Desktop/Programming/crypt-librarian/agent/approve.py           # Review candidates
```

Uses 5 subagents (taste learner, film discoverer, content validator, database manager, subtitle hunter) with SQLite-backed provenance tracking. Both the interactive skill and autonomous agent share the same `films.json` archive, enabling taste compounding over time.

---

## Setup

### Prerequisites

- Python 3.9+
- `pip install requests`
- `EXA_API_KEY` env var (for Exa searches)
- `FIRECRAWL_API_KEY` env var (optional, for deep scraping of Criterion/MUBI/Letterboxd)

---

## Related Skills

- **`exa-search`**: Neural web search used by the film discovery scripts.
- **`firecrawl`**: Web scraping for Criterion collections and Letterboxd lists.

---

## Requirements

- Python 3.9+
- `requests`
- Exa API key

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/planning-productivity/crypt-librarian ~/.claude/skills/
```
