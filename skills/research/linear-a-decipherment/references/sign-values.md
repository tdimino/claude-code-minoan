# Linear A Sign Values

Sign-to-phoneme mappings used in the decipherment pipeline. Based on projection from Linear B values (Ventris 1952), validated against Steele & Meissner 2017.

## Methodology

Linear A sign values are projected from Linear B where sign forms are shared. This is the standard approach in Aegean epigraphy, but carries uncertainty:

- **HIGH confidence**: Signs with identical form and well-established Linear B value
- **MEDIUM confidence**: Signs with similar but not identical form, or less common Linear B usage
- **LOW confidence**: Signs with disputed values, polyphony, or no Linear B parallel

---

## Sign Value Table

### Pure Vowels (HIGH confidence)

| Sign | Value | Linear B | Notes |
|------|-------|----------|-------|
| A | /a/ | AB08 | Identical form |
| E | /e/ | AB38 | Identical form |
| I | /i/ | AB28 | Identical form |
| O | /o/ | AB61 | Less common in Linear A |
| U | /u/ | AB10 | Identical form |

### Labials (HIGH confidence)

| Sign | Value | Linear B | Notes |
|------|-------|----------|-------|
| PA | /pa/ | AB03 | Identical form |
| PE | /pe/ | AB72 | |
| PI | /pi/ | AB39 | |
| PO | /po/ | AB11 | |
| PU | /pu/ | AB29 | |

### Dentals — voiceless (HIGH confidence)

| Sign | Value | Linear B | Notes |
|------|-------|----------|-------|
| TA | /ta/ | AB59 | |
| TE | /te/ | AB04 | |
| TI | /ti/ | AB37 | |
| TO | /to/ | AB05 | |
| TU | /tu/ | AB69 | |

### Dentals — voiced (HIGH confidence)

| Sign | Value | Linear B | Notes |
|------|-------|----------|-------|
| DA | /da/ | AB01 | |
| DE | /de/ | AB45 | |
| DI | /di/ | AB07 | |
| DO | /do/ | AB14 | |
| DU | /du/ | AB51 | |

### Velars (HIGH confidence)

| Sign | Value | Linear B | Notes |
|------|-------|----------|-------|
| KA | /ka/ | AB77 | |
| KE | /ke/ | AB44 | |
| KI | /ki/ | AB67 | Gordon reads AB67 as KU — disputed |
| KO | /ko/ | AB70 | Less common in corpus |
| KU | /ku/ | AB81 | |

### Sibilants (HIGH-MEDIUM confidence)

| Sign | Value | Linear B | Notes |
|------|-------|----------|-------|
| SA | /sa/ | AB31 | HIGH |
| SE | /se/ | AB09 | HIGH |
| SI | /si/ | AB41 | MEDIUM — less frequent |
| SO | /so/ | AB12 | MEDIUM — rare in Linear A |
| SU | /su/ | AB58 | HIGH |
| ZA | /za/ | AB16 | MEDIUM |
| ZE | /ze/ | AB74 | MEDIUM |

### Liquids (HIGH confidence)

| Sign | Value | Linear B | Notes |
|------|-------|----------|-------|
| RA | /ra/ | AB60 | |
| RE | /re/ | AB27 | |
| RI | /ri/ | AB53 | |
| RO | /ro/ | AB02 | |
| RU | /ru/ | AB26 | |

### Nasals (HIGH confidence)

| Sign | Value | Linear B | Notes |
|------|-------|----------|-------|
| MA | /ma/ | AB80 | |
| ME | /me/ | AB13 | |
| MI | /mi/ | AB73 | |
| MO | /mo/ | AB15 | Less common |
| MU | /mu/ | AB23 | |
| NA | /na/ | AB06 | |
| NE | /ne/ | AB24 | |
| NI | /ni/ | AB30 | |
| NO | /no/ | AB52 | |
| NU | /nu/ | AB55 | |

### Uvulars / Emphatics (MEDIUM confidence)

| Sign | Value | Linear B | Notes |
|------|-------|----------|-------|
| QA | /qa/ | AB16 | Shared with ZA in some analyses |
| QE | /qe/ | AB78 | |

### Semivowels (HIGH confidence)

| Sign | Value | Linear B | Notes |
|------|-------|----------|-------|
| JA | /ya/ | AB57 | GORILA convention; Gordon writes YA |
| JE | /ye/ | AB46 | |
| WA | /wa/ | AB54 | |
| WE | /we/ | AB75 | |
| WI | /wi/ | AB40 | |

### Polyphonous Signs (LOW confidence)

| Sign | Value | Linear B | Notes |
|------|-------|----------|-------|
| RA2 | /la/ | AB76 | Distinct from RA = /ra/; the l/r distinction |

---

## The O-Vowel Problem

Linear A has significantly fewer O-vowel signs than Linear B. This distributional difference is one of the strongest arguments that Linear A encodes a different language family than Greek:

| Vowel | Linear A frequency | Linear B frequency |
|-------|-------------------|-------------------|
| A | Very high | High |
| E | High | High |
| I | High | Moderate |
| O | **Low** | **High** |
| U | Moderate | Moderate |

Semitic languages are also poor in /o/, which Gordon cited as supporting evidence. However, this could also support Anatolian hypotheses (Luwian also lacks /o/).

---

## Undeciphered Signs

Signs marked with asterisks (*301, *302, etc.) have no accepted Linear B parallel. The pipeline treats these as opaque—they contribute no consonant to the skeleton extraction.

Notable undeciphered signs in the corpus:
- *301 — appears in A-TA-I-*301-WA-JA (libation formula)
- *302, *303 — various contexts
- Numeric signs and ideograms are handled separately

---

## Steele & Meissner 2017 Validation

Philippa Steele and Torsten Meissner's *Writing and Society in Ancient Crete* (2017) provides the most recent comprehensive review of Linear A sign values:

- Confirmed core CV grid projections from Linear B
- Identified additional potential signs not in the standard grid
- Raised questions about specific s-series and z-series distinctions
- Documented regional sign variants across Cretan sites

Their work validates the sign value table used in this pipeline while noting inherent uncertainty in any Linear B → Linear A projection.

---

## Implementation in Pipeline

The `lib/skeleton.py` module implements sign decomposition:

```python
SIGN_DECOMPOSITION: dict[str, tuple[str | None, str]] = {
    "KI": ("k", "i"),    # → consonant k
    "RE": ("r", "e"),    # → consonant r
    "TA": ("t", "a"),    # → consonant t
    "A":  (None, "a"),   # → no consonant (pure vowel)
    "RA2": ("l", "a"),   # → consonant l (polyphonous)
}
```

Signs not in the decomposition table are skipped during skeleton extraction. Run `validate_decomposition_coverage()` to identify corpus signs missing from the table.
