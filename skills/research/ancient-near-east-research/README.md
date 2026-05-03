# Ancient Near East Research

Domain-specific academic research toolkit for Biblical Hebrew, Semitic linguistics, cuneiform studies, Minoan/Aegean archaeology, and comparative ANE mythology. Combines primary source APIs (Sefaria, CDLI, ORACC) with web discovery (Omnisearch, Exa, Firecrawl, Obscura) for scholarly literature search and extraction.

**Last updated:** 2026-05-02

**Reflects:** Sefaria API v3, CDLI/ORACC JSON endpoints, Omnisearch meta-router (`--academic` flag), Exa neural search (`research_paper` category), Firecrawl v2.9 (Fire-PDF parsing), Obscura stealth browser for 10 academic site types.

---

## Why This Skill Exists

ANE research requires a different toolchain than typical academic search. The primary sources are in Hebrew, Akkadian, Ugaritic, and Greek---served by specialized APIs (Sefaria, CDLI, ORACC, Perseus) that general-purpose search tools don't know about. The secondary literature lives behind JSTOR, Persee, and Google Scholar paywalls that block headless browsers.

This skill provides the domain knowledge (which APIs to query, which domains to search, which query patterns work) and a 6-tier escalation ladder from free domain APIs through neural search to stealth browser extraction, tailored to the specific domains and sites where ANE scholarship lives.

---

## Structure

```
ancient-near-east-research/
  SKILL.md                                 # Tool selection guide and workflows
  README.md                                # This file
  scripts/
    fetch_sefaria.py                       # Sefaria API client (Hebrew Bible)
    fetch_cuneiform.py                     # CDLI/ORACC API client
    compile_quotations.py                  # Themed quotation compilation
    mistral_ocr_pdf.py                     # Mistral Pixtral OCR for PDFs
    ane_stealth_fetch.sh                   # Stealth fetch for 10 academic site types
  references/
    sefaria_api.md                         # Sefaria API endpoints and usage
    hebrew-passages.md                     # Key Hebrew Bible passages for ANE research
    akkadian-terms.md                      # Akkadian terminology and Enuma Elish
    cuneiform-databases.md                 # CDLI/ORACC API reference
    categorization-keywords.md             # 5-theme auto-categorization keywords
    obscura-ane-patterns.md                # Obscura extraction patterns for academic sites
    gordon-papers/
      gordon-findings.md                   # Gordon's Minoan-Semitic key findings
```

---

## What It Covers

### Primary Source APIs (Tier 0)

| API | Content | Script |
|-----|---------|--------|
| Sefaria | Hebrew Bible with vocalization, translations, commentaries | `fetch_sefaria.py` |
| CDLI | Cuneiform Digital Library (P-numbers, ATF) | `fetch_cuneiform.py` |
| ORACC | Open Richly Annotated Cuneiform Corpus | `fetch_cuneiform.py` |

### Web Discovery (Tiers 1--2)

| Tool | When | Command |
|------|------|---------|
| Omnisearch | Broad discovery, unknown sources | `omnisearch.py "query" --academic` |
| Exa | Domain-filtered neural search | `exa_search.py "query" --category "research paper" --domains jstor.org persee.fr` |

### Source Extraction (Tiers 3--4)

| Tool | When | Command |
|------|------|---------|
| Firecrawl | Known URL, PDF parsing | `firecrawl scrape URL --only-main-content` |
| Obscura | Bot-protected sites (JSTOR, Scholar, Persee) | `ane_stealth_fetch.sh URL` |

### ANE Escalation Ladder

| Tier | Tool | When |
|------|------|------|
| 0 | Sefaria / CDLI / ORACC | Known reference, free structured data |
| 1 | Omnisearch `--academic` | Broad discovery |
| 2 | Exa `--category "research paper"` | Domain-filtered search |
| 3 | Firecrawl `scrape` / `parse` | Page extraction, PDF-to-markdown |
| 4 | Obscura `ane_stealth_fetch.sh` | Bot-protected sites |
| 5 | Scrapling | Cloudflare Turnstile (last resort) |

### Translation Philosophy

Literal translation preserving etymological connections:
- תְּהוֹם → Tehom (not "the deep") --- preserves Tehom ↔ Tiamat cognate
- אֱלֹהִים → Elohim (not "God")
- Pre-begadkephat pronunciation for etymological analysis (פ as /p/ not /f/)

---

## Requirements

- Python 3.10+
- `MISTRAL_API_KEY` for PDF OCR (optional)
- Omnisearch, Exa-search, and Firecrawl skills for web discovery (optional, graceful degradation)
- Obscura binary for stealth extraction (optional)

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/research/ancient-near-east-research ~/.claude/skills/
```
