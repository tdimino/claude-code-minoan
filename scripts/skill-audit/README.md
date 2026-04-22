# skill-audit

Skill freshness audit pipeline—local inventory + external upstream validation.

Two scripts, zero external dependencies (Python 3.10+ stdlib only). `skill-freshness.py` shells out to Exa and Firecrawl for upstream checks but doesn't import them.

## Components

| File | Purpose |
|------|---------|
| `skill-audit.py` | Local inventory—discovers skills, parses SKILL.md + README.md metadata, classifies upstream/internal, flags staleness |
| `skill-freshness.py` | External validation—queries Exa and Firecrawl to check upstream versions against registry |
| `freshness-registry.yaml` | Curated mapping of skills to upstream sources, versions, and search queries |

## skill-audit.py

Scans `~/Desktop/claude-code-minoan/skills/` for directories containing `SKILL.md`. For each skill: parses frontmatter (name, description), extracts README metadata (last_updated, reflects), gets git last-modified date, classifies as `has_upstream` or `internal`, and flags issues.

**Flags:**
| Flag | Meaning |
|------|---------|
| `no_readme` | No README.md in skill directory |
| `no_readme_date` | README exists but has no `Last updated:` date |
| `no_reflects` | README has no `Reflects:` metadata |
| `readme_stale` | Git date is >7 days newer than README date |

```bash
skill-audit.py                          # ANSI table of all 80 skills
skill-audit.py --flagged-only           # Only skills with issues
skill-audit.py --category integration-automation
skill-audit.py --json                   # JSON to stdout
skill-audit.py --json | jq '.[] | select(.classification == "has_upstream")'

skill-audit.py --generate-registry-skeleton > freshness-registry.yaml
```

## skill-freshness.py

Reads `freshness-registry.yaml`, runs Exa searches for each upstream skill, optionally scrapes changelogs with Firecrawl, and compares found versions against the registry's `current_version`.

**Requires:** `exa_search.py` at `~/.claude/skills/exa-search/scripts/exa_search.py`, `firecrawl` CLI (optional, skippable with `--skip-scrape`).

```bash
skill-freshness.py --dry-run            # Show plan without API calls
skill-freshness.py --skill codex-orchestrator
skill-freshness.py --category integration-automation
skill-freshness.py --skip-scrape        # Exa only, no Firecrawl
skill-freshness.py --deep               # Exa deep search (slower)
skill-freshness.py --max-skills 5 -v    # Cap + verbose progress
skill-freshness.py --json               # JSON output
```

## freshness-registry.yaml

Auto-generated skeleton via `skill-audit.py --generate-registry-skeleton`, then hand-curated. Each upstream skill entry has:

```yaml
skill-name:
  type: has_upstream
  category: integration-automation
  upstreams:
    - name: "Library Name"
      url: "https://github.com/org/repo"
      search_query: "library name release changelog"
      version_pattern: "v\\d+\\.\\d+(\\.\\d+)?"
      current_version: "v1.2.3"
```

Entries marked `# CURATE` still need manual verification of URLs and search queries.

## Typical Workflow

```bash
# 1. Audit local state
python3 skill-audit.py --flagged-only

# 2. Fix flagged skills (add README dates, update reflects metadata)

# 3. Check upstream freshness for a category
python3 skill-freshness.py --category integration-automation -v

# 4. Update skills flagged as stale

# 5. Regenerate registry after adding new skills
python3 skill-audit.py --generate-registry-skeleton > freshness-registry.yaml
```
