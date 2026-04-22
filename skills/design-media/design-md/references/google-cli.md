# @google/design.md CLI Reference

Upstream CLI for the DESIGN.md 9-section format. Package: `@google/design.md` (alpha v0.1.1, Apache 2.0).

Source: [google-labs-code/design.md](https://github.com/google-labs-code/design.md)

## Commands

### lint

```bash
npx @google/design.md lint DESIGN.md      # File path
npx @google/design.md lint -              # Stdin
```

Validates against 8 rules. Outputs JSON array of diagnostics. Exit 0 = clean, exit 1 = errors.

| Rule | Severity | What it checks |
|------|----------|----------------|
| `broken-ref` | error | `{path.to.token}` references that don't resolve |
| `contrast-ratio` | warning | Component bg/text pairs below WCAG AA (4.5:1 normal, 3:1 large) |
| `missing-primary` | warning | Colors section exists but no `primary` defined |
| `orphaned-tokens` | warning | Color tokens defined but never referenced by components |
| `token-summary` | info | Agent Prompt Guide (section 9) missing key token summaries |
| `missing-sections` | info | One or more of the 9 canonical sections absent or empty |
| `missing-typography` | warning | Colors defined but typography hierarchy missing or < 3 roles |
| `section-order` | warning | Sections present but out of canonical order (auto-fixable) |

### diff

```bash
npx @google/design.md diff OLD.md NEW.md
```

Token-level diff. Exit 0 = no regressions. Exit 1 = regressions detected (removed tokens, contrast degradation). Output is JSON with added/removed/changed token lists.

### export

```bash
npx @google/design.md export --format tailwind DESIGN.md   # Tailwind theme config
npx @google/design.md export --format dtcg DESIGN.md       # W3C Design Token Format
```

JSON to stdout. Tailwind format maps directly to `theme.extend` keys. DTCG format follows the W3C Design Token Community Group spec.

### spec

```bash
npx @google/design.md spec                    # Full format spec (markdown)
npx @google/design.md spec --rules-only --format json  # Lint rules only
```

Dumps the canonical format specification. Equivalent to reading `design-md-format.md` but from the upstream source. Use to check for format drift between local reference and upstream.

## Lint Rules vs. Quality Checklist

The lint rules cover most of the quality checklist from `design-md-format.md`:

| Checklist item | Lint rule |
|---------------|-----------|
| All 9 sections present | `missing-sections` |
| Every color has semantic name + hex + role | `broken-ref`, `orphaned-tokens` |
| Typography hierarchy (lint threshold: 3+ roles; quality standard: 6+) | `missing-typography` |
| Agent prompt guide with color reference | `token-summary` |
| WCAG contrast requirements | `contrast-ratio` |

Items NOT covered by lint (require manual review):
- 2+ button variants with full CSS
- Spacing scale with named base unit
- 3+ elevation levels with use cases
- 4+ Do's and Don'ts each
- 3+ named breakpoints with key changes

## Token Format

Tokens in YAML frontmatter use `{path.to.token}` reference syntax (W3C Design Tokens-inspired):

| Type | Format |
|------|--------|
| Color | `#RGB` or `#RRGGBB` (sRGB) |
| Dimension | number + unit (`px`, `rem`) |
| Typography | object with up to 7 properties |
| Reference | `{colors.primary}` resolves to the referenced token's value |
