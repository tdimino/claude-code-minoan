# Obscura ANE Extraction Patterns

Site-specific patterns for extracting metadata and content from academic sources relevant to Ancient Near Eastern research. Each pattern uses Obscura's stealth headless browser. Based on the academic-research skill's patterns, extended with ANE-specific domains.

## Verified Sites

### Google Scholar

Aggressive bot detection — Obscura's stealth passes. ANE-specific search queries:

```bash
# Minoan-Semitic research
obscura fetch --stealth --quiet \
  "https://scholar.google.com/scholar?q=minoan+semitic+etymology+Gordon" \
  --eval "JSON.stringify(Array.from(document.querySelectorAll('.gs_r.gs_or')).slice(0,5).map(r=>({
    title: r.querySelector('.gs_rt')?.textContent || '',
    snippet: r.querySelector('.gs_rs')?.textContent?.substring(0, 200) || '',
    authors: r.querySelector('.gs_a')?.textContent || '',
    cited_by: r.querySelector('.gs_fl a')?.textContent?.match(/Cited by (\d+)/)?.[1] || '0',
    pdf_url: r.querySelector('.gs_or_ggsm a')?.href || ''
  })))"
```

**ANE query patterns for Scholar URLs:**
- `minoan+semitic+etymology` — Astour, Gordon, Bernal
- `Tehom+Tiamat+cognate+primordial` — Cosmogonic connections
- `Ugaritic+Hebrew+Athirat+Asherah` — Goddess studies
- `Linear+A+Semitic+decipherment` — Script studies
- `Caphtor+Kaptaru+Crete+Philistine` — Geographic identifications
- `Moses+Minos+lawgiver+parallel` — Comparative religion

**Rate limiting:** Space requests 10+ seconds apart. CAPTCHA appears under heavy use.

### JSTOR

Fingerprints headless browsers. Obscura's stealth passes for metadata/abstracts.

```bash
obscura fetch --stealth --quiet \
  "https://www.jstor.org/stable/10.2307/25651204" \
  --eval "JSON.stringify({
    title: document.title,
    abstract: document.querySelector('.abstract')?.textContent?.trim() || '',
    hasContent: document.querySelectorAll('[data-testid]').length > 0
  })"
```

**Key ANE journals on JSTOR:**

| Journal | Abbreviation | JSTOR Collection |
|---------|--------------|-----------------|
| Bulletin of the American Schools of Oriental Research | BASOR | `basor` |
| Journal of Biblical Literature | JBL | `jbl` |
| Journal of Near Eastern Studies | JNES | `jnes` |
| Journal of the American Oriental Society | JAOS | `jaos` |
| Vetus Testamentum | VT | `vetustestamentum` |
| Israel Exploration Journal | IEJ | `israelexplorj` |
| Bulletin de Correspondance Hellénique | BCH | `bulcorrhell` |

**JSTOR search URL pattern:**
```
https://www.jstor.org/action/doBasicSearch?Query=ENCODED_QUERY&acc=on&wc=on
```

### Persée

French academic archive. BCH, Syria, Revue de l'histoire des religions — key for ANE archaeology.

```bash
obscura fetch --stealth --quiet \
  "https://www.persee.fr/doc/bch_0007-4217_1996_num_120_1_4584" \
  --eval "JSON.stringify({
    title: document.title,
    meta: document.querySelector('meta[name=description]')?.content || '',
    hasArticle: !!document.querySelector('article'),
    source_url: window.location.href
  })"
```

**Key ANE journals on Persée:**
- BCH (Bulletin de Correspondance Hellénique) — `bch_0007-4217`
- Syria — `syria_0039-7946`
- RHR (Revue de l'histoire des religions) — `rhr_0035-1423`

**Gotchas:** Some articles behind Altcha interactive captcha — metadata and first-page preview still extractable.

### Perseus Digital Library

Classical texts directly relevant to Minoan/Aegean research. Minimal anti-bot.

```bash
obscura fetch --stealth --quiet \
  "https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0134" \
  --eval "JSON.stringify({
    title: document.title,
    text: document.querySelector('.text_container')?.textContent?.substring(0, 2000) || '',
    hasText: !!document.querySelector('.text_container')
  })"
```

**ANE-relevant Perseus texts:**
- Herodotus, *Histories* — Minos, Crete, Phoenician origins
- Pindar, *Pythian 4* — Thera foundation myth, Euphemos
- Apollonius, *Argonautica* — Thera, Anaphe, Triton
- Homer, *Odyssey* 19 — Minos "companion of Zeus"
- Diodorus Siculus — Minoan thalassocracy

### Academia.edu

Author profiles and paper lists. Bot-detecting.

```bash
obscura fetch --stealth --quiet \
  "https://www.academia.edu/departments/Classics" \
  --eval "JSON.stringify({
    title: document.title,
    linkCount: document.querySelectorAll('a').length,
    isRichPage: document.querySelectorAll('a').length > 10
  })"
```

**Gotchas:** Individual paper download pages may require login. Focus on metadata and profile pages.

## Non-Ideal for Obscura

### Sefaria, CDLI, ORACC

Free APIs — browser rendering adds overhead for no benefit. Use the dedicated scripts:

```bash
python3 ~/.claude/skills/ancient-near-east-research/scripts/fetch_sefaria.py "Genesis 1:2"
python3 ~/.claude/skills/ancient-near-east-research/scripts/fetch_cuneiform.py cdli P480701
```

### Semantic Scholar

JSON API endpoint. Use curl:

```bash
curl -s "https://api.semanticscholar.org/graph/v1/paper/search?query=Minoan+Semitic&fields=title,authors,abstract,year"
```

## General Notes

- **Batch concurrency**: Use `--concurrency 3` (not 25) for academic sites to avoid rate limits.
- **Escalation**: See SKILL.md "Source Escalation Ladder" for the 6-tier decision matrix.
- **Not for paywalls**: Obscura extracts publicly visible metadata and abstracts, not gated full text.
