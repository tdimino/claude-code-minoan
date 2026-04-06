# Social Dossier Template

Use this section skeleton when creating platform-specific dossiers. Each dossier analyzes one platform's content for voice, worldview, and biographical signals.

## Frontmatter

See `frontmatter-schema.md` for the full `type: social-dossier` spec. The `corpus` field documents the size and date range of analyzed content.

## Required Sections

### Source
Provenance block establishing how content was obtained and verified.

```markdown
## Source

- **URL**: `https://...`
- **Handle**: `@handle`
- **Legal entity**: © Name or Pen Name
- **Tagline**: "..."
- **Verification**: Firecrawl scrape, YYYY-MM-DD
- **Archive**: `archive/{platform}/` (N files)
```

For Wayback-sourced content, add: domain status, CDX API discovery method, snapshot dates.

### Platform Profile
Table of platform-specific metadata: launch date, posting cadence, pricing, engagement metrics (likes, comments), monetization links.

### Post/Content Index
Complete table of all content analyzed:

```markdown
| # | Date | Title | Type | Themes |
|---|------|-------|------|--------|
| 1 | YYYY-MM-DD | Title | Essay/Travelogue/Manifesto | theme1, theme2 |
```

Include content type classification (essay, travelogue, manifesto, listicle, thread, etc.) and 3-5 theme keywords per entry.

### Voice Analysis
The core analytical section. See `voice-analysis-guide.md` for detailed methodology.

**Subsections:**
- **Writing Registers** — Table: `Register | Frequency | Trigger | Markers`. Identify 2-5 distinct modes of expression.
- **Sentence Mechanics** — Signature punctuation patterns (bold, parenthetical, em dash, italics), structural devices
- **Tonal Range** — Emotional spectrum: earnest, campy, elegiac, angry, observational, etc.
- **Characteristic Phrases & Patterns** — Recurring verbal tics, self-identifying phrases, habitual constructions

### Worldview Markers
5-10 recurring themes extracted across the corpus. Each as a named subsection with 2-3 sentences of evidence.

> Example themes: "Medievalism as Antidote", "Class Consciousness", "Food as Ritual & Texture", "Body & Health", "Career Ambivalence"

### Biographical Signals
Per-post or per-content table of factual details revealed:

```markdown
| Post | Signal |
|------|--------|
| Title | Key facts: career moves, health updates, addresses, names, dates |
```

Separate distinct events. Do not conflate things that happened in different locations or timeframes.

### Calibration Quotes
10-15 verbatim quotes capturing the subject's voice at its most characteristic.

**Selection criteria:**
- Variety of registers (at least one quote per identified register)
- Emotional range (not all earnest or all angry)
- Stylistic distinctiveness (the quote couldn't be by anyone else)

**Format:**
```markdown
> "Exact verbatim text, character-by-character."
> — Source Title
```

**Verbatim accuracy is non-negotiable.** Verify every quote against the archived source before including it. Check: opening words (don't drop "But", "And", "So"), punctuation (single vs double quotes), emphasis (bold/italic).

## Optional Sections

### Voice Evolution
Include when the corpus spans a significant time period (e.g., pre-MFA vs post-MFA, early career vs current). Use a comparison table:

```markdown
| Dimension | Period A (Year) | Period B (Year) |
|-----------|-----------------|-----------------|
| Register | Instructional | Immersive |
| Tone | Earnest | Tonal range |
| Vocabulary | Elevated | Colloquial with academic |
```

### Author Bio
Verbatim bio text from the platform. Useful for voice calibration and self-description analysis.

### Thematic Connections
For subjects with content across multiple platforms or periods: map how themes evolved, persisted, or transformed.

### Cross-References
Links to other dossiers, the core model, and related data collections.

### RAG Tags
Comprehensive flat tag list for semantic search indexing. Include: platform names, subject name variants, key themes, publication names, scholar names referenced.
