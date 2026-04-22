# Frontend Design Pipeline

Every frontend project follows this pipeline. No UI implementation begins until the three gate artifacts exist.

## The Three Artifacts

| # | Artifact | Skill | What it captures |
|---|----------|-------|-----------------|
| 1 | Plan | Manual / SPEC.md / `~/.claude/plans/` | Approved approach, scope, architecture decisions |
| 2 | `.design-context.md` | `/shape` | Intent: audience, mood, design dials, anti-goals, key states |
| 3 | `DESIGN.md` | `/design-md` | Tokens: hex colors, font stacks, spacing scale, shadows, component specs |

`.design-context.md` says *who* and *why*. `DESIGN.md` says *what exactly*. Both live in project root. Both are consumed by `/minoan-frontend-design` during implementation.

## Pipeline Sequence

```
1. Plan          -> approved scope + architecture
2. /shape        -> .design-context.md (discovery interview -> design brief)
3. /design-md    -> DESIGN.md (tokens from CSS scan or brand library fetch)
4. Validate      -> npx @google/design.md lint DESIGN.md
5. Implement     -> /minoan-frontend-design (reads both artifacts)
6. QA            -> /design-audit -> /design-critique -> /design-polish
```

## Decision Points

### Step 2 — When to use /shape

- **New project**: Always run `/shape`. The discovery interview produces a `.design-context.md` covering audience, mood, design dials (DESIGN_VARIANCE, MOTION_INTENSITY, VISUAL_DENSITY), anti-goals, key states, and interaction model.
- **Existing `.design-context.md`**: Skip `/shape` if the file exists and covers the current scope. If it's stale (new features, changed audience), update it via `/shape` rather than starting fresh.
- **Trivial UI addition**: Write `.design-context.md` manually if the addition is small and the design direction is already established.

### Step 3 — Which /design-md workflow

- **Workflow A** (fetch reference): `npx getdesign@latest add <brand>` to fetch a brand's token system. 68 brands available. Use when "make it look like Stripe/Linear/etc."
- **Workflow B** (generate from CSS): `python3 ~/.claude/skills/design-md/scripts/generate_design_md.py <project-path>` to extract tokens from existing CSS. Use when the project already has design tokens in code but no DESIGN.md artifact.
- **Workflow C** (validate/export): `npx @google/design.md lint DESIGN.md` to validate, `export --format tailwind` to produce a Tailwind config. Use after Workflow A or B, or after manual edits.
- **Manual**: Write DESIGN.md by hand following the 9-section format in `~/.claude/skills/design-md/references/design-md-format.md`.

### Step 4 — Validation

Always lint before implementation. The Google CLI checks 8 rules: broken token references, WCAG contrast, missing primary color, orphaned tokens, token summary completeness, section completeness, typography presence, and section ordering. Fix errors before proceeding. See `~/.claude/skills/design-md/references/google-cli.md` for the full rule reference.

Additional CLI commands:
- `npx @google/design.md diff OLD.md NEW.md` — token-level diff between revisions (exits 1 on regressions)
- `npx @google/design.md export --format tailwind DESIGN.md` — Tailwind theme JSON
- `npx @google/design.md export --format dtcg DESIGN.md` — W3C Design Token Format JSON

### Step 5 — Implementation

`/minoan-frontend-design` consumes both artifacts. `.design-context.md` provides creative direction; `DESIGN.md` provides exact values. If either artifact contradicts the other, `.design-context.md` wins on intent, `DESIGN.md` wins on specific values. Tokens are materials, not recipes — creative direction still leads.

### Step 6 — QA sequence

Run in order. Each skill is report-only except `/design-polish` which executes fixes.

| Skill | What it does | Output |
|-------|-------------|--------|
| `/design-audit` | 5 dimensions scored /20 (a11y, performance, responsive, theming, anti-patterns). P0-P3 severity. | Report |
| `/design-critique` | Nielsen heuristics /40, cognitive load checklist, persona testing, AI slop test. | Report |
| `/design-polish` | Alignment, spacing, 8 interaction states, transitions, tinted neutrals, WCAG contrast, touch targets. | Executed fixes |

## Skill Quick Reference

| Skill | Triggers on | Produces |
|-------|-------------|----------|
| `/shape` | "plan the design", "design brief", "before we build" | `.design-context.md` |
| `/design-md` | "DESIGN.md", "create design system", "extract tokens", "lint design" | `DESIGN.md` |
| `/minoan-frontend-design` | "web UI", "frontend design", "dashboard", "landing page" | Implementation |
| `/design-audit` | "audit the design", "check accessibility", "a11y check" | Scored report |
| `/design-critique` | "critique", "UX review", "design feedback" | Scored report |
| `/design-polish` | "polish", "finishing touches", "final pass" | Executed fixes |

## The 9-Section Format (Quick Reference)

1. Visual Theme & Atmosphere (prose: mood, philosophy)
2. Color Palette & Roles (semantic name + hex + role)
3. Typography Rules (families, hierarchy table)
4. Component Stylings (buttons, cards, inputs with states)
5. Layout Principles (spacing scale, grid, whitespace)
6. Depth & Elevation (shadow system, surface hierarchy)
7. Do's and Don'ts (design guardrails)
8. Responsive Behavior (breakpoints, touch targets)
9. Agent Prompt Guide (quick color reference for copy-paste)

Full spec: `~/.claude/skills/design-md/references/design-md-format.md`

## Exemplar: Zimrah

Zimrah (`~/Desktop/Programming/zimrah/`) demonstrates the pipeline:

- **`.design-context.md`** (230 lines): "Frescoed Listening Room" direction from `/shape` — OKLCH palette, 3 typeface specimens, 10 key states, DESIGN_VARIANCE: 9
- **Pipeline gate held**: No implementation began without both artifacts in place
- **What it shows**: High-variance projects (DESIGN_VARIANCE 8-10) produce longer design briefs. Simpler projects produce shorter ones. The pipeline scales with ambition, not complexity.
