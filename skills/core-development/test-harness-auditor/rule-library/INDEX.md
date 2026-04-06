# Rule Library

Domain-specific rule packs loaded by `generate.py` based on detected frameworks and stack. Each rule targets a single-line `grep -En` detectable anti-pattern sourced from named practitioners' published opinions.

## Packs

| Pack | File | Rules | Matched by | Stack |
|------|------|-------|------------|-------|
| Python CLI | `python-cli.json` | 13 | `_stack: "python"` | Python 3.10+ |
| Rust Workspace | `rust-workspace.json` | 8 | `_stack: "rust"` | Rust (all editions) |
| React | `react.json` | 10 | `_frameworks: ["react", "next"]` | React/Next.js |
| Functional TS | `functional-ts.json` | 13 | **Opt-in only** (`_opt_in: true`) | TypeScript + React |

**Total: 44 rules across 4 packs**

### Opt-in Packs

Packs with `_opt_in: true` are never auto-loaded by `generate.py`. To use them, manually copy their rules into your project's `.claude/lint-rules.json`. The **Functional TS** pack enforces strict-FP patterns (immutability, no mutation, declarative style) inspired by the Open Souls paradigm. It is appropriate for Open Souls projects and similar strict-FP TypeScript codebases, but too opinionated for general React/Next.js work.

## Exclusion Fields

Rules support two exclusion mechanisms — don't confuse them:

| Field | Matches against | Use for |
|-------|----------------|---------|
| `exclude_paths` | File path (glob via `_path_matches`) | Skipping directories: `"*/bin/*"`, `"*/cli/*"`, `"*/main.rs"` |
| `exclude_patterns` | Grep output line text (regex via `re.search`) | Skipping line content: `"test"`, `"spec"`, `"// nosec"`, `".test."` |

`exclude_paths` runs before grep (skips the file entirely). `exclude_patterns` runs after grep (filters matched lines).

## Sources

Rules are attributed via per-rule `_source` fields in each JSON file.

### Python (8 practitioners)

| Name | URL | Rules informed |
|------|-----|---------------|
| Dagster Engineering | [dagster.io/blog](https://dagster.io/blog) | swallowed-exception, untyped-dict |
| Seth Michael Larson | [sethmlarson.dev](https://sethmlarson.dev) | shell-true, insecure-deserialization, match-not-fullmatch, commonprefix, requests-no-timeout |
| Trey Hunner | [treyhunner.com](https://treyhunner.com) | inherit-builtin |
| Hynek Schlawack | [hynek.me](https://hynek.me) | inherit-builtin, insecure-deserialization |
| Brett Cannon | [snarky.ca](https://snarky.ca) | untyped-dict |
| Glyph Lefkowitz | [blog.glyph.im](https://blog.glyph.im) | swallowed-exception, shell-true |
| Ned Batchelder | [nedbatchelder.com](https://nedbatchelder.com) | meaningless-assert |
| Hilmar Gustafsson | [hilmargustafs.com](https://hilmargustafs.com) | untyped-dict |

### Rust (5 practitioners)

| Name | URL | Rules informed |
|------|-----|---------------|
| Andrew Gallant (BurntSushi) | [blog.burntsushi.net](https://blog.burntsushi.net) | expect-empty-msg, anyhow-in-lib |
| Alex Kladov (matklad) | [matklad.github.io](https://matklad.github.io) | todo-macro (FIXME/HACK expansion) |
| David Tolnay (dtolnay) | [docs.rs/dtolnay](https://docs.rs/dtolnay) | anyhow-in-lib |
| Amos (fasterthanlime) | [fasterthanli.me](https://fasterthanli.me) | (informed research, rules cut for Clippy overlap) |
| Mara Bos | [mara.nl](https://mara.nl) | (informed research, rules cut for noise) |

### React (6 practitioners)

| Name | URL | Rules informed |
|------|-----|---------------|
| TkDodo (Dominik Dorfmeister) | [tkdodo.eu](https://tkdodo.eu) | disabled-exhaustive-deps |
| Kent C. Dodds | [kentcdodds.com](https://kentcdodds.com) | unnecessary-cleanup, test-query-selector, key-index |
| Dan Abramov | [overreacted.io](https://overreacted.io) | key-index, async-use-effect, disabled-hooks-rule |
| Mark Erikson | [blog.isquaredsoftware.com](https://blog.isquaredsoftware.com) | context-object-literal, legacy-redux |
| Nadia Makarevich | [developerway.com](https://developerway.com) | context-object-literal |
| Sandor Farkas (Wolf-Tech) | [wolf-tech.io](https://wolf-tech.io) | disabled-exhaustive-deps |

### Functional TypeScript (3 practitioners)

| Name | URL | Rules informed |
|------|-----|---------------|
| Matt Pocock | [totaltypescript.com](https://totaltypescript.com) | enum-declaration |
| Christian Rackerseder | [echooff.dev](https://echooff.dev) | enum-declaration, namespace-declaration |
| Marek Honzal | [marekhonzal.com](https://marekhonzal.com) | enum-declaration |

## Adding Custom Packs

Create a JSON file in this directory with:

```json
{
  "_pack": "my-pack",
  "_description": "What it enforces",
  "_frameworks": ["react"],
  "_stack": "typescript",
  "rules": [
    {
      "extensions": ["ts", "tsx"],
      "pattern": "your-grep-E-pattern",
      "message": "[category] Description — recommendation",
      "exclude_patterns": ["test", "spec"],
      "exclude_paths": ["*/scripts/*"],
      "_tag": "pack:my-pack:rule-name",
      "_source": "Author Name (url)"
    }
  ]
}
```

Set `"_opt_in": true` to prevent auto-loading. All patterns must work with single-line `grep -En` — no multiline matching.

Tags use `pack:<pack-name>:<rule-slug>` format for dedup. Categories must be registered in `lint-on-write.py` SEVERITY_TIERS: security (BLOCKING), error-boundary (BLOCKING), observability (HIGH), debugging-residue (HIGH), async-misuse (HIGH), architecture (MEDIUM), testability (MEDIUM), grep-ability (MEDIUM), convention (MEDIUM).
