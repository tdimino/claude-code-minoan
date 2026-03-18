# Skill Distribution Strategy

Source: Thariq (Anthropic), "Lessons from Building Claude Code: How We Use Skills" (March 2026).

## Three Distribution Tiers

Skills can be distributed at three scopes, each suited to different audiences:

### 1. Project Skills (`.claude/skills/` in repo)

Check skills into your repository's `.claude/skills/` directory.

**Best for**: Small teams working across relatively few repos. Domain-specific workflows, internal tool wrappers, project-specific conventions.

**Trade-off**: Every skill checked into a repo adds to the model's context. As you scale, this can become a constraint.

### 2. Marketplace Plugins (plugin `skills/` directory)

Package skills as plugins and distribute via a marketplace.

**Best for**: Generic capabilities useful across organizations. Skills that have been tested and refined beyond a single team's needs.

**Trade-off**: Requires curation. Bad or redundant skills dilute the marketplace and waste context budget.

### 3. Managed Settings (enterprise)

Deploy skills organization-wide through managed settings.

**Best for**: Compliance requirements, org-wide standards, security guardrails that every engineer should have active.

## Organic Skill Promotion

Skills often start at one tier and graduate upward:

1. **Personal** (`~/.claude/skills/`) -- engineer builds a skill for themselves
2. **Project** (`.claude/skills/` in repo) -- teammates find it useful, it gets committed
3. **Plugin** -- the skill gets copy-pasted across repos (signal for promotion)
4. **Managed** -- org mandates it for compliance or consistency

**From Thariq**: "We don't have a centralized team that decides; instead we try and find the most useful skills organically. If you have a skill that you want people to try out, upload it to a sandbox folder in GitHub and point people to it in Slack. Once it has gotten traction, put in a PR to move it into the marketplace."

## Skill Portfolio Hygiene

### Context Budget

Skill descriptions are loaded into context at session start. The default budget is 15,000 characters for all skill descriptions combined.

- Many skills may exceed this budget, causing some to be invisible
- Set `SLASH_COMMAND_TOOL_CHAR_BUDGET` environment variable to increase the limit
- Use `skill-toggle` to enable/disable skills as needed
- Use `cplugins` to manage plugin profiles and stay under the ~40 agent ceiling

### Curation

"It can be quite easy to create bad or redundant skills, so making sure you have some method of curation before release is important." -- Thariq

**Monthly review checklist**:
- [ ] Are any skills never used? (Check usage analytics from `advanced-patterns.md`)
- [ ] Are any skills doing the same thing? Consolidate
- [ ] Have any skills' descriptions drifted from their actual behavior?
- [ ] Are any skills undertriggering? Optimize descriptions (Step 7 in the creation process)
- [ ] Is the total agent count approaching the ~40 ceiling? Prune or use plugin profiles

### Skill Dependencies

Skills can reference other skills by name. If Skill A depends on Skill B, Claude will invoke Skill B if it's installed. This sort of dependency management is not natively built into marketplaces yet -- document dependencies explicitly in the skill's SKILL.md so users know what to install.
