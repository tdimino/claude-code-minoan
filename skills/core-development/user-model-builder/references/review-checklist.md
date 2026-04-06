# UserModel Review Checklist

Run this checklist after completing a userModel build. Launch a code-reviewer subagent to audit all files, or use `scripts/validate_usermodel.py` for automated structural checks.

## Verbatim Accuracy

- [ ] Every calibration quote matches the archived source character-by-character
- [ ] Opening words are preserved (don't drop "But", "And", "So", "Or")
- [ ] Quote mark style matches source (single quotes vs double quotes)
- [ ] Emphasis preserved (bold, italic) where present in source
- [ ] Author bios are verbatim, not paraphrased from memory

## Biographical Facts

- [ ] Names are spelled correctly (check against source)
- [ ] Dates match source text (career tenure, graduation years, move dates)
- [ ] Locations are correct—don't conflate events in different cities
- [ ] Separate incidents are not merged (e.g., a shooting and a robbery are two events)
- [ ] Self-reported facts (e.g., "first 5 years") noted when they diverge from inferred data (e.g., LinkedIn says 6+)

## Platform & Organization Names

- [ ] Conference names are correct (ASSA vs AEA, full name + acronym)
- [ ] Organization names match official usage
- [ ] Social handles verified against primary source (not assumed from secondary references)
- [ ] Post titles are complete (not truncated)

## Frontmatter Schema

- [ ] All required fields present per file type (see `frontmatter-schema.md`)
- [ ] `type` field is valid: `user-model`, `social-dossier`, `voice-model`, `index`, `archive-index`
- [ ] `category` field matches content: `persona`, `twitter-analysis`, `substack-analysis`, `blog-archive`, `pet-model`
- [ ] `corpus` field present on all dossiers with format: "N posts, date range, ~N words"
- [ ] `status` field is valid: `active`, `archived`, `verified`, `draft`
- [ ] `created` and `updated` dates are accurate

## INDEX Consistency

- [ ] Master INDEX.md (`~/.claude/userModels/INDEX.md`) lists the subject's folder
- [ ] Files table in INDEX.md matches actual files on disk
- [ ] Data Collections table lists all archive directories
- [ ] Related links are accurate and complete
- [ ] `archive/INDEX.md` inventory matches actual archived files
- [ ] Word counts in archive INDEX are approximate but reasonable

## Cross-References

- [ ] Core model references all dossiers in its Supplementary Dossiers section
- [ ] All file paths in dossier cross-references resolve to real files
- [ ] No orphaned files (files in folder not referenced anywhere)
- [ ] No stale references (references to files that don't exist)

## Content Quality

- [ ] Voice analysis identifies at least 2 distinct registers
- [ ] Worldview markers include at least 5 themes with evidence
- [ ] Calibration quotes span the full tonal range (not all one register)
- [ ] Biographical signals table covers every post/content item
- [ ] Voice evolution section included if corpus spans 3+ years or a major life transition
