# glossary

Build or update a `CONTEXT.md` domain glossary for any project.

## What it does

Creates a shared vocabulary document at the project root with term definitions, avoid-aliases, relationships, and flagged ambiguities. Agents that read this file use consistent, concise domain language instead of inventing synonyms or being verbose.

## Usage

```
/glossary
```

On first run, the skill explores the codebase, identifies domain-specific naming patterns, and interviews the user to resolve canonical terms. On subsequent runs, it reads the existing glossary and appends new terms.

## Provenance

Adapted from [Matt Pocock's](https://github.com/mattpocock/skills) `/grill-with-docs` skill and `CONTEXT.md` convention (from the `mattpocock/skills` repo, ~41K stars). Pocock's approach uses DDD-style ubiquitous language to reduce agent verbosity by ~75% and enforce naming consistency across sessions.

## Optimization Process

This skill went through a structured optimization pipeline:

1. **Research** — Full catalog of Pocock's 12 skills compared against our existing 90-skill setup. `/grill-with-docs` + `CONTEXT.md` was identified as the highest-value convention we lacked (we had principles about naming but no invocable glossary builder).

2. **Initialization** — Scaffolded via `/skill-optimizer`'s `init_skill.py` template.

3. **Drafting** — SKILL.md written following skill-optimizer guidelines: imperative voice, progressive disclosure (lean SKILL.md + reference doc), WHY rationale behind directives.

4. **Review** — Bohen verification agent ran a 13-criterion audit. Findings:
   - **Critical (fixed):** Original name `/context` collided with Claude Code's built-in `/context` command (checks skill character budget). Renamed to `/glossary`.
   - **Medium (fixed):** Added WHY rationale to key directives (why four fields per term, why append-don't-rewrite, why consistent terminology matters).
   - **Medium (fixed):** Removed second-person voice from "Consuming" section — recast as imperative.
   - **Medium (fixed):** Generalized provenance rule examples from domain-specific ("a Ugaritic tablet") to universal ("a domain spec, an industry standard, a legacy system's naming").
   - **Low (noted):** No `evals/` directory yet. Deferred to first real-world usage.

5. **Post-review edits** — All critical and medium findings addressed before publishing.

## Files

```
glossary/
├── SKILL.md                       # Main instructions (36 lines)
├── references/
│   └── context-format.md          # CONTEXT.md format spec with template
└── README.md                      # This file
```

## CONTEXT.md Format (summary)

Each term gets four fields:

- **Canonical name** (bold heading)
- **Definition** (one sentence — what it IS, not what it does)
- **Avoid** (synonyms to reject)
- **Relationships** (cardinality with other terms)

Plus a dialogue example showing terms in use, and a "Flagged ambiguities" section for resolved naming conflicts.

See `references/context-format.md` for the full template.

## Credits

- [Matt Pocock](https://github.com/mattpocock/skills) — `CONTEXT.md` convention and `/grill-with-docs` skill
- [Eric Evans](https://www.domainlanguage.com/) — ubiquitous language concept (Domain-Driven Design)
- [John Ousterhout](https://web.stanford.edu/~ouster/cgi-bin/book.php) — deep modules philosophy informing interface-level vocabulary
