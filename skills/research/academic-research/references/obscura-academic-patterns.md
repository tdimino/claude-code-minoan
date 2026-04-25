# Obscura Academic Extraction Patterns

Site-specific patterns for extracting metadata and content from academic sources using Obscura's stealth headless browser. Each pattern was validated against live sites (2026-04-24).

## Verified Sites (6/7 pass rate)

### Perseus Digital Library

Minimal anti-bot. Good baseline for classical texts.

```bash
obscura fetch --stealth --quiet \
  "https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0134" \
  --eval "JSON.stringify({
    title: document.title,
    text: document.querySelector('.text_container')?.textContent?.substring(0, 500) || '',
    hasText: !!document.querySelector('.text_container')
  })"
```

**Gotchas**: Title contains text reference (e.g. "Homer, Iliad, Book 1, line 1"), not "Perseus."

### PubMed / NCBI

Free but bot-detecting. Abstracts and metadata are publicly visible.

```bash
obscura fetch --stealth --quiet \
  "https://pubmed.ncbi.nlm.nih.gov/25418537/" \
  --eval "JSON.stringify({
    title: document.querySelector('.heading-title')?.textContent?.trim() || document.title,
    authors: Array.from(document.querySelectorAll('.authors-list .full-name')).map(e => e.textContent),
    abstract: document.querySelector('.abstract-content')?.textContent?.trim()?.substring(0, 1000) || '',
    doi: document.querySelector('.id-link[data-ga-action=DOI]')?.textContent?.trim() || '',
    year: document.querySelector('.cit')?.textContent?.match(/\\d{4}/)?.[0] || ''
  })"
```

### Google Scholar

Aggressive bot detection — Obscura's stealth passes it. Extract search results with titles, authors, citation counts, and PDF links.

```bash
obscura fetch --stealth --quiet \
  "https://scholar.google.com/scholar?q=minoan+trade+routes+bronze+age" \
  --eval "JSON.stringify(Array.from(document.querySelectorAll('.gs_r.gs_or')).slice(0, 5).map(r => ({
    title: r.querySelector('.gs_rt')?.textContent || '',
    snippet: r.querySelector('.gs_rs')?.textContent?.substring(0, 200) || '',
    authors: r.querySelector('.gs_a')?.textContent || '',
    cited_by: r.querySelector('.gs_fl a')?.textContent?.match(/Cited by (\\d+)/)?.[1] || '0',
    pdf_url: r.querySelector('.gs_or_ggsm a')?.href || ''
  })))"
```

**Gotchas**: Rate-limited per IP. Space requests 10+ seconds apart for batch queries. Can serve CAPTCHA under heavy use — if output contains "unusual traffic," back off.

### Persée

French academic archive. Altcha captcha loads dynamically but doesn't block initial page load.

```bash
obscura fetch --stealth --quiet \
  "https://www.persee.fr/doc/bch_0007-4217_1996_num_120_1_4584" \
  --eval "JSON.stringify({
    title: document.title,
    hasArticle: !!document.querySelector('article'),
    hasContent: !!document.querySelector('.content'),
    meta: document.querySelector('meta[name=description]')?.content || ''
  })"
```

**Gotchas**: Some articles behind Altcha interactive captcha — metadata and first-page preview still extractable.

### JSTOR

Fingerprints headless browsers (canvas, WebGL). Obscura's stealth passes. Preview pages show abstracts and metadata without login.

```bash
obscura fetch --stealth --quiet \
  "https://www.jstor.org/stable/10.2307/25651204" \
  --eval "JSON.stringify({
    title: document.title,
    abstract: document.querySelector('.abstract')?.textContent?.trim() || '',
    hasContent: document.querySelectorAll('[data-testid]').length > 0
  })"
```

**Gotchas**: Full text requires institutional login. Extraction is limited to publicly visible metadata, abstracts, and preview pages.

### Academia.edu

Bot-detecting. Author profiles and paper lists extractable.

```bash
obscura fetch --stealth --quiet \
  "https://www.academia.edu/departments/Classics" \
  --eval "JSON.stringify({
    title: document.title,
    linkCount: document.querySelectorAll('a').length,
    isRichPage: document.querySelectorAll('a').length > 10
  })"
```

**Gotchas**: Individual paper download pages may require login. Focus on metadata and profile pages.

## Non-Ideal for Obscura

### Semantic Scholar API

JSON API endpoint — browser rendering adds overhead for no benefit. Use curl or Exa instead.

```bash
# Prefer this over Obscura for Semantic Scholar:
curl -s "https://api.semanticscholar.org/graph/v1/paper/PAPER_ID?fields=title,authors,abstract,year"
```

## General Notes

- **Batch concurrency**: Use `--concurrency 3` (not 25) for academic sites to avoid triggering rate limits.
- **Escalation ladder**: See `SKILL.md` → "Source Extraction Escalation" for the 5-tier decision matrix.
