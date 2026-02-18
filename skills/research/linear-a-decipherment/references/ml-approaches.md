# Computational Decipherment Approaches

Survey of ML approaches for Linear A, documenting viable strategies for v2 implementation.

## Current State (v1)

v1 uses rule-based methods only:
- Consonantal skeleton extraction (deterministic)
- Weighted Levenshtein distance (configurable substitution costs)
- Precomputed cognate cache (308KB, all corpus words × Proto-Semitic roots)
- 63 known readings from Gordon + YasharMana lexicons

These are sufficient for systematic exploration but cannot discover new readings or validate hypotheses statistically.

---

## Published Approaches

### NeuroDecipher (Luo et al., MIT 2019)

**Paper**: "Neural Decipherment via Minimum-Cost Flow"

**Method**: Frames decipherment as minimum-cost flow in a bipartite graph between source (undeciphered) and target (known language) vocabularies. Uses neural language models for both source and target.

**Applicability to Linear A**: Limited.
- Requires a known target language (they used Ugaritic → Hebrew)
- Requires word-segmented texts
- Assumes the target language is closely related
- Linear A's target language is disputed (Semitic? Anatolian? Pre-Greek?)

**Transferable insights**:
- Bipartite matching framework could work if we commit to Semitic as target
- Their phonological constraint model is relevant to our skeleton matching

### Tamburini 2025 — Combinatorial Optimisation for Script Decipherment

**Paper**: "On automatic decipherment of lost ancient scripts relying on combinatorial optimisation and coupled simulated annealing"
**Author**: Fabio Tamburini, University of Bologna
**Journal**: *Frontiers in Artificial Intelligence*, Vol. 8, May 2025
**DOI**: https://doi.org/10.3389/frai.2025.1581129

**Method**: Combinatorial optimization + coupled simulated annealing; encodes solutions via k-permutations allowing null, one-to-many, and many-to-one sign mappings.

**Scripts covered**: Linear A, Cretan Hieroglyphs, Cypro-Minoan

**Applicability**: High methodological interest. Introduces 3 new benchmarks. The 2025 Frontiers paper is a journal expansion of the 2023 CAWL workshop paper (ACL 2023, pp. 82-91). No specific lexical proposals—purely computational approach to sign mapping.

### Deep Aramaic Paradigm

**Method**: Extension of NeuroDecipher using Aramaic as bridge language for decipherment of closely related scripts. Minimum-cost flow with related language constraints.

**Applicability**: Highly relevant if we accept Gordon's NWS hypothesis.
- Could use Hebrew/Ugaritic/Aramaic as target languages
- The triconsonantal root structure of Semitic is ideal for flow matching
- Our skeleton extraction provides the source representation

---

## Recommended v2 Strategy

### Base Model: Qwen 2.5 7B

Selected for:
- Best multilingual tokenizer for Semitic transliterations among open models
- 7B parameters suitable for LoRA fine-tuning on consumer hardware
- Strong performance on structured extraction tasks

### 3-Stage QLoRA Curriculum

#### Stage 1: Semitic Foundation
**Purpose**: Teach the model Semitic phonology and morphology.
**Data**: ~2,000 pairs from existing Semitic linguistic resources.
**Examples**:
- Hebrew root triconsonants → meanings
- Ugaritic vocabulary → translations
- Akkadian loanwords in NWS languages

#### Stage 2: Syllabographic Bridge
**Purpose**: Train on the Linear A sign value system.
**Data**: ~800 pairs mapping CV syllables to phonemes.
**Examples**:
- Linear B readings (known) as proxy for Linear A
- Sign decomposition rules
- Syllable → consonantal skeleton transformations

#### Stage 3: Gordon Injection
**Purpose**: Fine-tune on the actual Gordon readings.
**Data**: ~800 augmented pairs (from 63 base readings).
**Examples**:
- Direct gordon-pairs (63)
- Sound shift augmentations (~250)
- Context-constrained variants (~150)
- Back-formation pairs (~100)

**Total estimated pairs**: ~3,600

### Why 63 Pairs Is Insufficient

Standard fine-tuning requires thousands of examples for generalization. With 63 base pairs:
- High risk of memorization rather than learning
- No capacity for novel predictions
- Evaluation impossible (no held-out set)

The 3-stage curriculum addresses this by:
1. Building a Semitic knowledge base first (Stage 1)
2. Teaching the script system (Stage 2)
3. Only then injecting the small Gordon dataset (Stage 3)

---

## Augmentation Techniques

### 1. Sound Shift Augmentation (~250 pairs)
Apply known Semitic sound correspondences to generate plausible variants:
```
KI-RE-TA (k-r-t) → {g-r-t, k-r-d, k-l-t, q-r-t}
```
Each variant paired with the original reading creates a training signal for sound flexibility.

### 2. Back-Formation (~100 pairs)
Given a Semitic reading, generate plausible Linear A spellings:
```
Hebrew kol → KI-RO, KU-RO, KO-RO (all plausible CV representations)
```

### 3. Linear B Bridge (~200 pairs)
Use known Linear B words as training data, since the script is shared:
```
Linear B pa-i-to = Phaistos → pa-i-to in Linear A (confirmed overlap)
```

### 4. Paradigm Expansion (~150 pairs)
Expand morphological paradigms from known forms:
```
JA-TA-NO (ya-tan-o, "he gave") →
  A-TA-NO (a-tan-o, "he gave" variant)
  TA-NU-A-TI (tanu-at-i, "I set up")
  TE-TE-PI (te-tep-i, "she may thrive")
```

### 5. Context Constraints (~100 pairs)
Pair readings with their archaeological context:
```
{"context": "libation table", "word": "JA-SA-SA-RA-ME"} → "votive offering"
{"context": "accounting tablet + WHEAT", "word": "KU-NI-SU"} → "emmer wheat"
```

---

## Evaluation Strategy

### Leave-One-Out Cross-Validation
With only 63 readings, LOO-CV is the only viable approach:
- Train on 62 readings, predict the 63rd
- Repeat for each reading
- Measure: exact match rate, skeleton match rate, semantic category accuracy

### Sign-Value Consistency
Generated readings should not contradict established sign values:
- If model reads KI as /gi/, flag as inconsistent
- Track consistency score across all predictions

### Morphological Plausibility
Check that predicted readings follow Semitic morphological rules:
- Triconsonantal root structure
- Valid prefix/suffix patterns
- Known morpheme boundaries

### Human Expert Review
No automated metric replaces expert judgment for undeciphered scripts. All model outputs should be reviewed by a domain expert (Tom) before being added to the lexicon.

---

## Infrastructure Requirements

| Component | v1 (Current) | v2 (Planned) |
|-----------|-------------|--------------|
| Model | None (rule-based) | Qwen 2.5 7B + LoRA |
| Training data | 63 JSONL pairs | ~3,600 augmented pairs |
| Hardware | Any CPU | Mac Mini M4 (32GB) or equivalent |
| Framework | stdlib Python | PyTorch + PEFT + TRL |
| Inference | N/A | llama.cpp (GGUF export) |
| Evaluation | Manual | LOO-CV + consistency checks |

---

## Timeline

| Phase | Deliverable | Depends On |
|-------|-------------|------------|
| v1 (current) | `finetune_prep.py gordon-pairs` | Done |
| v2.1 | Augmentation pipeline | Sound shift rules validated |
| v2.2 | Semitic foundation dataset | Curated Hebrew/Ugaritic/Akkadian pairs |
| v2.3 | 3-stage QLoRA training | v2.1 + v2.2 + Mac Mini M4 |
| v2.4 | LOO-CV evaluation | v2.3 |
| v2.5 | GGUF export + llama.cpp integration | v2.4 passing evaluation |
