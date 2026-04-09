# Eval Skill Variants

Index of all frontend design skill files used in the blind A/B evaluation pipeline.

## Our Skills

| File | Words | Description | Lineage | Best Result |
|------|-------|-------------|---------|-------------|
| `syncretic-v4.md` | 1042 | **REGRESSION.** V3 + brand identity directive, photo/SVG distinction, asymmetric grid examples, ghost text opacity clamping, compressed anti-patterns, procedural resist directive. Over-constrained: 135 more words caused truncation and mechanical output. | syncretic-v3.md + 6 surgical edits from 14-loss analysis across all rounds | 44.4% vs wetch (8-10, p=0.760) |
| `syncretic-v3.md` | 907 | **Current best.** V2 + conceptual framing directive, statement typography, bold dark option, dashboard density, custom SVG illustration, completeness-as-floor. New reference files: design-dials, creative-arsenal. | syncretic-v2.md + 6 surgical edits from judge analysis + taste-skill integration | 70.0% vs wetch (14-6, p=0.058) |
| `syncretic-v2.md` | 849 | Previous best. Completeness mandate, warm palette guidance, expanded anti-patterns. | syncretic.md + targeted fixes from judge analysis | 69.2% vs wetch (9-4, p=0.133) |
| `syncretic.md` | 767 | Syncretic v1. Merged creative philosophy into a single cohesive document. | creative.md rewritten | 64.3% vs wetch (9-5, p=0.212) |
| `creative.md` | 557 | Creative-only skill (symlink to `minoan-frontend-creative/SKILL.md`). | Original extraction from minoan.md | 31.6% vs wetch (6-13) |
| `engineering.md` | 764 | Engineering standards only (symlink to `minoan-frontend-engineering/SKILL.md`). | Extracted from minoan.md | Used as supplement, not standalone |
| `minoan.md` | 1196 | Full production skill (symlink to `minoan-frontend-design/SKILL.md`). Creative + engineering combined. | Original composite | 45.0% vs wetch (9-11) |

## External Skills

| File | Words | Description | Source |
|------|-------|-------------|--------|
| `wetch.md` | 583 | **Baseline.** Justin Wetch's SkillEval skill. All win rates are measured against this. | [justinwetch/SkillEval](https://github.com/justinwetch/SkillEval) |
| `taste-skill.md` | 2926 | "High-Agency Frontend Skill" with design dials, 100 AI tells, creative arsenal, motion-engine bento paradigm. | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) |

## Evolution

```
creative.md (31.6%)
    ↓ rewrite as single cohesive doc
syncretic.md (64.3%)
    ↓ targeted fixes: completeness mandate, warm palettes, anti-placeholders
syncretic-v2.md (69.2%)
    ↓ conceptual framing, statement typography, dashboard density, custom SVG, taste-skill integration
syncretic-v3.md (70.0%) ← CURRENT BEST / DEPLOYED TO PRODUCTION SKILL
    ↓ brand identity, photo handling, asymmetric grids, ghost text fix, anti-pattern compression, resist procedure
syncretic-v4.md (44.4% — REGRESSION, over-constrained)
```

## Production Mapping

The production skill `minoan-frontend-design/SKILL.md` uses **syncretic-v3** as its creative core (minor inline edits for Claude 4.6 alignment). The inline engineering section was removed in favor of a `## References` pointer block (~30 words) linking to 5 progressive disclosure files: vercel-web-interface-guidelines, design-system-checklist, creative-arsenal, design-dials, and editorial-patterns. Total SKILL.md: ~956 words — within the proven sweet spot, under the 1042-word regression threshold.

## Usage

```bash
# Pairwise eval
python3 run_eval.py --skill-b skills/syncretic-v3.md --label-b syncretic-v3 --prompts 5

# Three-way comparison (after running pairwise evals)
python3 run_eval.py compare results/dir1 results/dir2 --baseline wetch
```
