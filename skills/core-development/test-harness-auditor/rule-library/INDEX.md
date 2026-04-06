# Rule Library

Domain-specific rule packs auto-loaded by `generate.py` based on detected frameworks and stack. Each rule targets a grep-detectable anti-pattern sourced from named practitioners' published opinions.

## Packs

| Pack | File | Rules | Matched by | Stack |
|------|------|-------|------------|-------|
| Python CLI | `python-cli.json` | 13 | `_stack: "python"` | Python 3.10+ |
| Rust Workspace | `rust-workspace.json` | 7 | `_stack: "rust"` | Rust (all editions) |
| React | `react.json` | 10 | `_frameworks: ["react", "next"]` | React/Next.js |
| Functional TS | `functional-ts.json` | 21 | `_frameworks: ["react", "next"]`, `_stack: "typescript"` | TypeScript + React |

**Total: 51 rules across 4 packs**

## Sources

Rules are attributed via per-rule `_source` fields in each JSON file. The following practitioners' published opinions informed the rule packs.

### Python (8 practitioners)

| Name | URL | Rules informed |
|------|-----|---------------|
| Dagster Engineering | [dagster.io/blog](https://dagster.io/blog) | swallowed-exception, untyped-dict, unverified-cast |
| Seth Michael Larson | [sethmlarson.dev](https://sethmlarson.dev) | shell-true, insecure-deserialization, match-not-fullmatch, commonprefix |
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

### React (5 practitioners)

| Name | URL | Rules informed |
|------|-----|---------------|
| TkDodo (Dominik Dorfmeister) | [tkdodo.eu](https://tkdodo.eu) | disabled-exhaustive-deps |
| Kent C. Dodds | [kentcdodds.com](https://kentcdodds.com) | unnecessary-cleanup, test-query-selector |
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
      "_tag": "pack:my-pack:rule-name",
      "_source": "Author Name (url)"
    }
  ]
}
```

Tags use `pack:<pack-name>:<rule-slug>` format for dedup. Categories must be registered in `lint-on-write.py` SEVERITY_TIERS: security (BLOCKING), error-boundary (BLOCKING), observability (HIGH), debugging-residue (HIGH), async-misuse (HIGH), architecture (MEDIUM), testability (MEDIUM), grep-ability (MEDIUM), convention (MEDIUM).
