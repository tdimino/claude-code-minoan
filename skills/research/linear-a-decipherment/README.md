# Linear A Decipherment

The epigrapher's workbench. A computational pipeline for analyzing Linear A inscriptions using Cyrus H. Gordon's Semitic hypothesis---transliteration, segmentation, consonantal skeleton extraction, cognate search, and coverage analysis across the GORILA corpus.

**Last updated:** 2026-02-18

**Reflects:** Cyrus H. Gordon's *Evidence for the Minoan Language* (1966), the GORILA corpus (~1,701 inscriptions), Proto-Semitic root databases (~2,871 roots), and the [lashon-ha-kretan](https://github.com/tdimino/lashon-ha-kretan) LinearAExplorer.

---

## Why This Skill Exists

Linear A remains undeciphered. The most productive hypothesis---that the underlying language belongs to the Semitic family---was advanced by Cyrus H. Gordon in 1966 and has never been formally refuted, only sidelined by disciplinary inertia. Testing this hypothesis computationally requires tools that don't exist in the academic mainstream: a pipeline that can extract consonantal skeletons from Linear A transliterations, search them against Proto-Semitic roots, and track confidence levels across the corpus.

This skill provides those tools. Five scripts implement Gordon's methodology as a reproducible pipeline. A library of phonetic utilities handles the messy realities of Bronze Age syllabary-to-consonantal mapping. Reference docs encode Gordon's 6 methods, the sign value tables, and ML approaches for training data generation.

---

## Structure

```
linear-a-decipherment/
  SKILL.md                                 # Pipeline overview and usage guide
  README.md                                # This file
  lib/
    __init__.py                            # Package init
    js_parser.py                           # Parse lashon-ha-kretan JSON data
    skeleton.py                            # Consonantal skeleton extraction
    phonetics.py                           # Phonetic mapping and normalization
    normalization.py                       # Transliteration normalization
    types.py                               # Type definitions
  scripts/
    analyze.py                             # Full 5-step analysis pipeline
    cognate_search.py                      # Search Proto-Semitic cognates
    corpus_extract.py                      # Extract inscriptions from lashon-ha-kretan
    sign_analysis.py                       # Sign frequency and co-occurrence analysis
    finetune_prep.py                       # Generate training data for ML models
  references/
    gordon-lexicon.md                      # Gordon's 60 confirmed readings
    methodology.md                         # Gordon's 6 analytical methods
    sign-values.md                         # Linear A sign value tables
    ml-approaches.md                       # Machine learning approaches and LoRA fine-tuning
    knossos-scepter-2024.md                # Case study: Knossos scepter inscription
```

---

## What It Covers

### Gordon's 6 Methods

| Method | Description | Example |
|--------|-------------|---------|
| **Ideographic context** | Commodity ideograms constrain meaning of adjacent phonetic text | WHEAT ideogram + KU-NI-SU = Akkadian *kunashu* |
| **Bilingual/biscriptal** | Same text in Linear A and another script | Hagia Triada tablets with Akkadian loanwords |
| **Structural analysis** | Morphological patterns match Semitic grammar | Prefix/suffix patterns, construct chains |
| **Onomastic evidence** | Personal and place names with Semitic cognates | Theophoric names with *-el*, *-baal* |
| **Formula analysis** | Recurring formulae match known Semitic patterns | Libation formula parallels |
| **Cross-cultural parallels** | Material culture confirms linguistic connections | Trade goods, religious practices |

### The 5-Step Pipeline

```
1. Transliterate    Extract phonetic values from GORILA corpus
       |
2. Segment          Break continuous text into morpheme candidates
       |
3. Skeleton         Extract consonantal skeleton (KI-RE-TA → k-r-t)
       |
4. Cognate Search   Match against ~2,871 Proto-Semitic roots
       |
5. Coverage         Summarize hit rate, confidence, semantic fit
```

### Confidence Taxonomy

Every proposed reading carries a confidence level:

| Level | Criteria | Count in Gordon |
|-------|----------|----------------|
| **CONFIRMED** | Multiple independent lines of evidence | ~12 |
| **PROBABLE** | Strong single-method evidence with supporting context | ~20 |
| **CANDIDATE** | Plausible phonetic match, limited context | ~20 |
| **SPECULATIVE** | Possible but unverifiable with current data | ~8 |

### Virtual Bilinguals

The Hagia Triada tablets are the closest thing to a Rosetta Stone for Linear A. Commodity ideograms (WHEAT, WINE, FIGS, OIL) appear alongside phonetic words, creating *virtual bilinguals*---the ideogram constrains the semantic field, narrowing cognate candidates from thousands to dozens.

---

## Scripts

All scripts pull data from the [lashon-ha-kretan](https://github.com/tdimino/lashon-ha-kretan) repository.

| Script | Purpose | Usage |
|--------|---------|-------|
| `analyze.py` | Run full 5-step pipeline on a transliteration | `python3 analyze.py "KU-NI-SU"` |
| `cognate_search.py` | Search Proto-Semitic roots for a consonantal skeleton | `python3 cognate_search.py k-r-t` |
| `corpus_extract.py` | Extract inscriptions from lashon-ha-kretan JSON | `python3 corpus_extract.py --site HT` |
| `sign_analysis.py` | Frequency and co-occurrence statistics | `python3 sign_analysis.py --top 50` |
| `finetune_prep.py` | Generate training data for ML fine-tuning | `python3 finetune_prep.py --format jsonl` |

### Library Modules

| Module | Purpose |
|--------|---------|
| `js_parser.py` | Parse lashon-ha-kretan's LinearAExplorer JSON data |
| `skeleton.py` | Extract consonantal skeletons from syllabic transliterations |
| `phonetics.py` | Phonetic mapping between Linear A sign values and Semitic consonants |
| `normalization.py` | Normalize variant transliteration conventions |
| `types.py` | Shared type definitions |

---

## ML Approaches

`finetune_prep.py` generates training data for fine-tuning language models on Linear A material. Designed for LoRA adapters on small models via llama.cpp. See `references/ml-approaches.md` for architecture choices, training data format, and evaluation strategies.

---

## Scholarly Disclaimer

Linear A remains undeciphered. The Semitic hypothesis is one of several competing proposals. This skill implements Gordon's methodology as a computational tool for systematic testing---it does not claim the question is settled. All proposed readings include confidence levels to prevent overstating claims.

---

## Requirements

- Python 3.9+
- [lashon-ha-kretan](https://github.com/tdimino/lashon-ha-kretan) repository cloned locally (for corpus data)
- No external Python dependencies

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/research/linear-a-decipherment ~/.claude/skills/
```
