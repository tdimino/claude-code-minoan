# SkillEval CLI

Blind A/B evaluation of frontend design skills. Methodology adapted from [Justin Wetch's SkillEval](https://github.com/justinwetch/SkillEval).

## Pipeline

```
prompts.json (50 prompts)
        |
        v
  Generate (parallel)     Sonnet 4.6 x 2 per prompt
  Skill A -> HTML         = 100 API calls
  Skill B -> HTML
        |
        v
  Screenshot              Playwright headless
  A.png, B.png            1200x800 viewport
        |
        v
  Judge (parallel)        Opus 4.6, blind A/B
  5 criteria, 1-5         multimodal (PNG + HTML)
  JSON structured         50 API calls
        |
        v
  Stats & Report          Binomial test (scipy)
  results.json            Markdown summary
  report.md
```

## Usage

```bash
cd ~/.claude/skills/minoan-frontend-design

# Full 50-prompt run
uv run --with anthropic,playwright,scipy,httpx eval/run_eval.py --provider openrouter

# Smoke test (first 5 prompts)
uv run --with anthropic,playwright,scipy,httpx eval/run_eval.py --provider openrouter --prompts 5

# Resume interrupted run (reuses completed generations/screenshots/judgments)
uv run --with anthropic,playwright,scipy,httpx eval/run_eval.py --provider openrouter --resume

# Use Anthropic API directly (requires ANTHROPIC_API_KEY)
uv run --with anthropic,playwright,scipy,httpx eval/run_eval.py

# Override models
uv run --with anthropic,playwright,scipy,httpx eval/run_eval.py --gen-model claude-sonnet-4-6-20260220 --judge-model claude-opus-4-6-20260220
```

## Prerequisites

- **Python 3.11+** via `uv`
- **Playwright browsers**: `uv run --with playwright python -m playwright install chromium`
- **API key**: `OPENROUTER_API_KEY` in `~/.config/env/global.env` (or `ANTHROPIC_API_KEY` for direct)

## Cost Estimate

| Phase | Calls | Model | Est. Cost |
|-------|-------|-------|-----------|
| Generation | 100 | Sonnet 4.6 | ~$20-25 (16K output tokens/call) |
| Judging | 50 | Opus 4.6 | ~$5-8 (multimodal input + 800 output tokens/call) |
| **Total** | **150** | | **~$25-33** |

**Warning**: Both skills produce max-length output (~16K tokens). Do not estimate based on typical output length. Budget for max_tokens output.

## Directory Structure

```
eval/
  run_eval.py              # Main CLI script (~1000 lines)
  prompts.json             # 50 test prompts
  README.md                # This file
  skills/
    wetch.md               # Justin Wetch's FRONTEND SKILL.md (baseline)
    minoan.md              # Symlink -> ../../SKILL.md
  results/                 # Output (gitignored)
    generations/           # Raw HTML: {id}_{A|B}.html
    screenshots/           # PNG screenshots: {id}_{A|B}.png
    results.json           # Full structured results
    report.md              # Human-readable summary
```

## Judge Criteria (same 5 as Wetch)

1. **Prompt Adherence** (1-5): Does output match the request?
2. **Aesthetic Fit** (1-5): Does the aesthetic direction suit the brief?
3. **Visual Polish & Coherence** (1-5): Typography, spacing, color, detail quality
4. **UX & Usability** (1-5): Layout logic, hierarchy, interaction affordances
5. **Creative Distinction** (1-5): Memorable and distinctive vs generic?

## Blind A/B

Which skill is "A" vs "B" is randomized per prompt (seeded, deterministic with `--seed`). The judge sees generic labels only ("Result A", "Result B"). Both screenshots and HTML source are provided to the judge (multimodal).

## Statistical Test

One-sided binomial test via scipy: H0: win rate = 0.5, H1: Minoan > 0.5. A p-value < 0.05 means the Minoan skill wins significantly more than chance.

## Resume Behavior

`--resume` loads `results/results.json` and skips completed work:

- **Generation**: Retries prompts where either side has an error or missing content
- **Screenshots**: Retries prompts where PNG files are missing on disk
- **Judging**: Retries prompts where judge status is not "complete", reloading base64 screenshots from saved PNGs

## Known Issues & Fixes (v2)

### Screenshot serialization on resume
Screenshots are stored as booleans in `results.json` to save space. On resume, the script reloads base64 data from the PNG files on disk before judging. Fixed in v2.

### Pre-flight credit check
For OpenRouter, the script now tests API access before starting. A 402 (insufficient credits) aborts immediately with a link to the credits page.

### Partial generation failures
If one side of a prompt fails (e.g., 402 mid-run), `--resume` detects and retries only the failed side. The `_needs_regen` helper checks for None, error, or empty content.

## Prompts

50 prompts across 8 categories:

| Category | Count | Examples |
|----------|-------|---------|
| Landing pages | 8 | SaaS, agency, restaurant, nonprofit, portfolio, event, app launch, crypto |
| Dashboards | 6 | Analytics, project management, social media, health, finance, IoT |
| Components | 8 | Pricing table, testimonials, feature grid, FAQ, timeline, stats, team grid, notifications |
| Forms | 5 | Multi-step signup, contact, survey, checkout, settings |
| Navigation | 4 | Mega menu, mobile drawer, sidebar, breadcrumbs |
| Creative/Edge | 8 | Band page, art gallery, recipe app, podcast, weather, code editor, 404, loading |
| Accessibility | 5 | Screen reader dashboard, high-contrast, keyboard gallery, reduced-motion, WCAG AAA |
| Animation | 6 | Scroll-triggered, parallax, counters, page transitions, hover cards, staggered grid |

## First Run Results (2026-02-21)

| Metric | Value |
|--------|-------|
| Minoan wins | 18 |
| Wetch wins | 21 |
| Ties/Errors | 11 |
| Win rate (Minoan) | 46.2% |
| p-value | 0.739 |
| Decisive comparisons | 39 of 50 |

**Not statistically significant.** The skills are essentially equivalent in single-shot generation. See `~/daimones/kothar/designReflections.md` for full analysis.
