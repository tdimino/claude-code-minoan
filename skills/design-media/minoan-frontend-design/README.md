# minoan-frontend-design

Production-grade frontend interfaces that avoid generic AI aesthetics. Bold typography, committed color palettes, unexpected layouts, meticulous detail.

**Current version**: syncretic-v3 (947 words)
**Eval record**: 70.0% vs wetch baseline (14-6, p=0.058) across 20 blind A/B comparisons

## Lineage

This skill descends from Anthropic's built-in `frontend-design` skill for Claude Code, which ships with the CLI.

[Justin Wetch](https://www.linkedin.com/in/justinwetch/) rewrote it with clearer, more actionable instructions and validated the improvement with a 50-prompt blind A/B eval (75% win rate, p=0.006). His write-up: [Teaching Claude to Design Better](https://www.linkedin.com/pulse/teaching-claude-design-better-improving-anthropics-frontend-wetch-x45ec). His skill (`wetch.md`, 583 words) became our baseline—every win rate in this project is measured against it.

[Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) (2926 words) contributed ideas that were adapted into our reference files: design variance dials, a creative technique arsenal, and an anti-pattern catalog. The taste-skill itself scored 30.8% vs wetch in our eval (too long, too prescriptive), but its best ideas proved valuable when extracted into progressive disclosure files.

## Evolution

We ran 6 eval rounds totaling 93 blind A/B comparisons across two judges (Opus 4.6 and Gemini 3.1 Pro). Each round tested a skill variant against the wetch baseline, analyzed judge reasoning for every loss, and applied targeted fixes.

```
minoan.md (45.0%, 1196w)
  Original composite skill — creative direction + engineering standards in one
  file. Scored below baseline: too long, too many competing concerns.
    ↓
syncretic.md (64.3%, 767w)
  Rewrote as a single cohesive document merging creative philosophy with
  engineering awareness. Immediate 33-point jump.
    ↓
syncretic-v2.md (69.2%, 849w)
  Added completeness mandate ("completeness is the floor, not the ceiling"),
  warm palette guidance, expanded anti-pattern blacklist.
    ↓
syncretic-v3.md (70.0%, 907w) ← DEPLOYED
  Conceptual framing directive, statement typography (6xl-9xl), bold dark
  option, dashboard density, custom SVG illustration, taste-skill integration
  (design-dials and creative-arsenal as reference files).
```

### Key finding: word count matters

Creative skill performance correlates inversely with instruction length past ~900 words.

| Skill | Words | Win Rate |
|-------|-------|----------|
| wetch (baseline) | 583 | 50% |
| minoan (original) | 1196 | 45.0% |
| syncretic-v3 | 907 | 70.0% |

More constraints produce more mechanical output. The SKILL.md body should contain creative philosophy and aesthetic principles. Specific techniques belong in reference files.

## Architecture

```
minoan-frontend-design/
├── SKILL.md                          947 words — syncretic-v3 creative core
├── README.md                         This file
├── LICENSE.txt                       Apache 2.0
├── references/
│   ├── creative-arsenal.md           30+ named CSS techniques with code
│   ├── design-dials.md               3 calibration scales (variance, motion, density)
│   ├── editorial-patterns.md         Eval-derived patterns: grids, accents, photos, ghost text
│   ├── design-system-checklist.md    Accessibility, tokens, responsive, component states
│   └── vercel-web-interface-guidelines.md  Engineering standards from Vercel
└── eval/
    ├── run_eval.py                   Blind A/B eval pipeline (~1400 lines)
    ├── prompts.json                  50 test prompts across 8 categories
    ├── skills/                       All skill variants (wetch, syncretic v1-v3, taste-skill)
    │   └── INDEX.md                  Full lineage with win rates and descriptions
    └── results/                      Timestamped eval run outputs (gitignored)
```

### Progressive disclosure

The skill uses a three-level loading system:

| Level | When Loaded | Content |
|-------|-------------|---------|
| **Metadata** | Always | Name + description (~100 tokens) |
| **SKILL.md** | When triggered | Creative philosophy (~1200 tokens) |
| **References** | On demand | Specific techniques, engineering specs (unlimited) |

SKILL.md contains the philosophy—what to do and why. Reference files contain the specifics—how to do it, with code examples and concrete values. Claude loads reference files only when relevant to the current task.

## Eval Methodology

Adapted from [Justin Wetch's SkillEval](https://github.com/justinwetch/SkillEval):

1. **Generate**: Sonnet 4.6 produces HTML for each prompt, once per skill. Skill assignment is the only difference between the two generations.
2. **Screenshot**: Playwright captures each page at 1200x800. This is what the judge sees first.
3. **Judge**: Opus 4.6 receives both screenshots and both HTML sources with randomized A/B labels. Scores 5 criteria on a 1-5 scale.
4. **Stats**: One-sided binomial test (H0: win rate = 0.5). p < 0.05 = statistically significant.

### Judge criteria

1. **Prompt Adherence** — Does output match the request?
2. **Aesthetic Fit** — Does the aesthetic direction suit the brief?
3. **Visual Polish & Coherence** — Typography, spacing, color, detail quality
4. **UX & Usability** — Layout logic, hierarchy, interaction affordances
5. **Creative Distinction** — Memorable and distinctive vs generic?

### Prompts

50 prompts across 8 categories: landing pages (8), dashboards (6), components (8), forms (5), navigation (4), creative/edge (8), accessibility (5), animation (6).

### Cost

A full 50-prompt run costs ~$25-33 via OpenRouter (Sonnet 4.6 generation + Opus 4.6 judging). A 10-prompt smoke test costs ~$6-8.

## Usage

Install by copying to your skills directory:

```bash
cp -r minoan-frontend-design/ ~/.claude/skills/minoan-frontend-design/
```

Claude Code loads it automatically when building web interfaces.

To run evals:

```bash
cd ~/.claude/skills/minoan-frontend-design

# 10-prompt smoke test
uv run --with anthropic,playwright,scipy,httpx eval/run_eval.py --prompts 10 --provider openrouter

# Full 50-prompt run
uv run --with anthropic,playwright,scipy,httpx eval/run_eval.py --provider openrouter

# Custom skill vs baseline
uv run --with anthropic,playwright,scipy,httpx eval/run_eval.py \
  --skill-b path/to/your-skill.md --label-b my-skill --prompts 10
```

## Credits

- **[Anthropic](https://github.com/anthropics/claude-code)** — original `frontend-design` skill
- **[Justin Wetch](https://www.linkedin.com/in/justinwetch/)** — rewrite, eval methodology, and baseline skill
- **[Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill)** — design dials and creative arsenal concepts
- **[Vercel](https://vercel.com/design/guidelines)** — Web Interface Guidelines and Geist design system

## License

Apache 2.0 (inherited from Anthropic's original).
