# User Model Builder

Build complete user models---core persona files, social dossiers with voice analysis, content archives, and INDEX registration---for people you collaborate with. A 7-phase workflow from discovery through review.

**Last updated:** 2026-04-21

---

## Why This Skill Exists

When Claude Code works with someone regularly, a rich model of their voice, worldview, and working style makes the collaboration dramatically better. This skill formalizes the process of building that model: scrape published content, analyze voice and worldview, create structured persona files, and register everything for retrieval. The output lives at `~/.claude/userModels/{name}/`.

---

## Structure

```
user-model-builder/
  SKILL.md                                     # Full 7-phase workflow
  README.md                                    # This file
  references/
    persona-model-template.md                  # Core persona section skeleton
    social-dossier-template.md                 # Social dossier section skeleton
    frontmatter-schema.md                      # YAML frontmatter spec for all file types
    voice-analysis-guide.md                    # Open Souls voice analysis methodology
    review-checklist.md                        # Post-build verification checklist
  scripts/
    validate_usermodel.py                      # Structural + quote accuracy validation
```

---

## Workflow

| Phase | What | Output |
|-------|------|--------|
| 1. Discovery | Gather identity, platforms, scrapeable content | Scope and direction |
| 2. Folder & Core Persona | Create directory and `{name}Model.md` | Core persona file |
| 3. Content Scraping | Archive all published content by platform | `archive/` with INDEX |
| 4. Voice Analysis | Analyze corpus for voice, worldview, biography | Platform dossiers |
| 5. Cross-References | Wire dossiers into persona, register in INDEX | Linked model |
| 6. Review | Audit quotes, facts, schema, cross-refs | Validated model |
| 7. Summary | Report corpus stats, key findings, next steps | Completion report |

---

## Usage

```bash
# Invoke the skill with a person's name
/user-model-builder Alice Chen

# Validate an existing model
uv run ~/.claude/skills/user-model-builder/scripts/validate_usermodel.py ~/.claude/userModels/alice/
```

---

## Scraping Tools

| Platform | Tool |
|----------|------|
| Substack | Firecrawl |
| Twitter | Jina (Firecrawl blocks Twitter) |
| Dead domains | Wayback CDX API → Firecrawl |
| LinkedIn | GDPR export via `linkedin-export` skill |

---

## Requirements

- Python 3.9+ (for validation script)
- Firecrawl and/or Jina for content scraping
- No additional dependencies for the workflow itself

---

## Related Skills

- **`linkedin-export`**: GDPR data export for LinkedIn content archiving.
- **`firecrawl`**: Web scraping for Substack and general content.

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/core-development/user-model-builder ~/.claude/skills/
```
