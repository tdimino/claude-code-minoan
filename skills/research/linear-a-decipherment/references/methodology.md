# Gordon's Decipherment Methodology

Cyrus H. Gordon's approach to Linear A, formalized as a computational pipeline.

## The Virtual Bilingual Method

Gordon's core insight: Linear A administrative tablets from Hagia Triada function as "virtual bilinguals." When a tablet lists commodities with WHEAT ideograms alongside phonetic words, and those words correspond to Semitic grain terms, the ideograms serve as translation anchors.

**The KU-NI-SU equation**:
- HT 86: `KU-NI-SU` + WHEAT ideogram
- Akkadian *kunāšu* = "emmer wheat"
- Phonetic match + semantic match + ideographic confirmation = high confidence

**The KI-RO totals**:
- KI-RO appears at the end of accounting tablets, followed by a sum
- Hebrew *kol* (כֹּל) = "all, total"
- The preceding itemized quantities sum to the KI-RO number
- Mathematical verification provides independent confirmation

**The HT 31 pot names**:
- Tablet HT 31 lists five words alongside vessel ideograms
- Gordon reads all five as Semitic vessel terms: KA-RO-PA (karpu), QA-PA (kap), SU-PA-RA (sēpel), SU-PU (sap), A-KA-NU (aggan)
- Multiple independent matches on a single tablet reduce probability of coincidence

---

## Gordon's Six Methods (1975 JRAS)

From "The Decipherment of Minoan and Eteocretan," *Journal of the Royal Asiatic Society* (1975):

### 1. Ideographic Context
Words accompanied by ideograms (WHEAT, WINE, OLIVE, vessel shapes) constrain possible meanings. If the phonetic reading also matches a Semitic term for that commodity, the identification is strengthened.

### 2. Bilingual / Biscriptal Evidence
Texts where the same content appears in both Linear A and another known script or language. The closest examples are Linear A/B overlaps (PA-I-TO = Phaistos) and the Cypro-Minoan connections.

### 3. Structural Analysis
Morphological patterns (prefixes, suffixes, plurals) that match NWS grammar:
- -NA demonstrative suffix (JA-SA-SA-RA-MA-NA)
- -AN onomastic suffix (MI-NA-NE, KI-RE-TA-NA, DA-NA-NE)
- -TI feminine marker (PA-DA-SU-TI, DA-KU-SE-NE-TI)
- A-/YA- prefix alternation on verbs (A-TA-NO / JA-TA-NO)

### 4. Onomastic Evidence
Personal and divine names recognizable from other ANE sources:
- DA-KU-SE-NE = Daku-šenni (attested at Nuzi and Ugarit)
- KU-PA-NU = Gupanu (*gpn* in Ugaritic, Baal's messenger)
- Egyptian theophoric names with -RE (Re) element

### 5. Formula Analysis
Recurring textual formulas, especially on libation tables:
- JA-SA-SA-RA-ME (votive offering formula)
- A-TA-I-*301-WA-JA
- I-DA-MA-TE

### 6. Cross-Cultural Parallels
Comparison with known Bronze Age Mediterranean practices:
- Minoan-Ugaritic deity parallels (A-DU/Addu, JA-MU/Yamm, PU-RA/Baal)
- Egyptian presence indicated by Re-compound names
- Hurrian element shared with Nuzi and Ugarit

---

## Computational Pipeline: 5-Step Formalization

Gordon's implicit methodology, formalized for systematic corpus analysis:

### Step 1: Transliteration
Extract the phonetic reading from GORILA corpus notation. Handle undeciphered signs (*301, *302), word boundaries, and variant readings.

**Script**: `corpus_extract.py`

### Step 2: Segmentation
Parse word boundaries (already segmented in GORILA) and identify morpheme breaks where possible. Recognize formulaic sequences.

### Step 3: Consonantal Skeleton
Strip vowels from CV syllables to produce a consonantal root for Semitic comparison:
```
KI-RE-TA → k-r-t (cf. Hebrew כרת "Kret/Crete")
KU-NI-SU → k-n-s (cf. Akkadian kunāšu)
JA-TA-NO → y-t-n (cf. Hebrew/Ugaritic ytn "give")
```

**Script**: `cognate_search.py --skeleton`

### Step 4: Cognate Search
Search against three tiers of comparative material:

| Tier | Source | Method | Confidence |
|------|--------|--------|------------|
| 1 | Gordon's 60 readings | Direct lookup | CONFIRMED (if supported) |
| 2 | YasharMana readings | Direct lookup | CANDIDATE |
| 3 | Proto-Semitic roots | Weighted Levenshtein | SPECULATIVE |

Sound correspondences weighted by known Semitic shifts:
- Voicing pairs (t/d, k/g, p/b, s/z): 0.1
- Liquid alternation (l/r): 0.15
- Emphasis (t/T, k/q, s/S): 0.3

**Script**: `cognate_search.py`, `analyze.py`

### Step 5: Semantic Validation (optional)
Cross-check proposed readings against:
- Archaeological context (findspot, object type)
- Ideographic context (accompanying logograms)
- Formula position (is this word in expected slot?)
- Parallel texts (same formula on other tablets)

This step requires human judgment in v1; automated in v2 via LLM.

---

## Key Evidence Summary

| Evidence | Strength | Details |
|----------|----------|---------|
| KU-NI-SU + WHEAT | Strong | Akkadian loanword + ideographic confirmation |
| KI-RO = totals | Strong | Mathematical verification across many tablets |
| HT 31 pot names | Moderate-Strong | 5 Semitic vessel terms on single tablet |
| JA-TA-NO = ytn | Moderate | Cognate with widespread NWS root |
| DA-KU-SE-NE | Moderate | Externally attested Hurrian name |
| KU-PA-NU = gpn | Moderate | Attested Ugaritic divine messenger |
| DA-WE-DA = David | Weak-Contested | Anachronism concerns; heavily debated |
| Libation formula | Moderate | Consistent across many tablets; reading disputed |

---

## Scholarly Critique

### Supporters
- **Gordon** (1957–1999): Originated and defended the hypothesis across four decades
- **Astour** (1965): Independent Greco-Semitic etymological work supporting connections

### Critics
- **Pope** (1964): Questioned statistical significance of cognate matches
- **Finkelberg** (1990s): Argued for Anatolian (Luwian) substrate instead
- **Younger** (2000s): Methodological concerns about confirmation bias
- **Consensus**: Mainstream epigraphy considers Linear A undeciphered; Gordon's readings are "one of several competing frameworks"

### Methodological Concerns
1. **Cherry-picking**: With ~3,000 Semitic roots, some matches are expected by chance
2. **Vowel freedom**: Stripping vowels increases false positive rate
3. **Sign value assumptions**: Projecting Linear B values onto Linear A is uncertain
4. **Small sample**: 60 readings out of ~4,000 unique words (1.5% coverage)
5. **Anachronism**: Some proposed names (David) raise chronological concerns

### Counterarguments
1. **Clustering**: Multiple matches on single tablets (HT 31) reduce chance probability
2. **External validation**: Names attested at Ugarit/Nuzi are independently confirmed
3. **Mathematical confirmation**: KI-RO totals provide non-linguistic verification
4. **Ideographic anchoring**: Commodity words confirmed by accompanying ideograms

---

## Disclaimer

All readings presented here are hypothetical. Linear A remains officially undeciphered. Gordon's Semitic hypothesis is one of several competing frameworks. The computational pipeline is designed for systematic exploration, not definitive decipherment.
