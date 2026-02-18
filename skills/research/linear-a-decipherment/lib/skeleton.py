"""Consonantal skeleton extraction from Linear A transliterations.

Linear A is written in a CV (consonant-vowel) syllabary projected from Linear B.
Each sign encodes one syllable. To compare with Semitic roots (which are consonantal),
strip the vowels to produce a "skeleton": KI-RE-TA -> k-r-t.
"""
from __future__ import annotations

# (consonant | None, vowel) — None consonant means pure vowel sign
SignDecomposition = tuple[str | None, str]

SIGN_DECOMPOSITION: dict[str, SignDecomposition] = {
    # Pure vowels
    "A": (None, "a"), "E": (None, "e"), "I": (None, "i"),
    "O": (None, "o"), "U": (None, "u"),
    # Labials
    "PA": ("p", "a"), "PE": ("p", "e"), "PI": ("p", "i"),
    "PO": ("p", "o"), "PU": ("p", "u"),
    # Dentals (voiceless)
    "TA": ("t", "a"), "TE": ("t", "e"), "TI": ("t", "i"),
    "TO": ("t", "o"), "TU": ("t", "u"),
    # Dentals (voiced)
    "DA": ("d", "a"), "DE": ("d", "e"), "DI": ("d", "i"),
    "DO": ("d", "o"), "DU": ("d", "u"),
    # Velars
    "KA": ("k", "a"), "KE": ("k", "e"), "KI": ("k", "i"),
    "KO": ("k", "o"), "KU": ("k", "u"),
    # Sibilants
    "SA": ("s", "a"), "SE": ("s", "e"), "SI": ("s", "i"),
    "SO": ("s", "o"), "SU": ("s", "u"),
    "ZA": ("z", "a"), "ZE": ("z", "e"),
    # Liquids
    "RA": ("r", "a"), "RE": ("r", "e"), "RI": ("r", "i"),
    "RO": ("r", "o"), "RU": ("r", "u"),
    # Nasals
    "MA": ("m", "a"), "ME": ("m", "e"), "MI": ("m", "i"),
    "MO": ("m", "o"), "MU": ("m", "u"),
    "NA": ("n", "a"), "NE": ("n", "e"), "NI": ("n", "i"),
    "NO": ("n", "o"), "NU": ("n", "u"),
    # Uvulars / emphatics
    "QA": ("q", "a"), "QE": ("q", "e"),
    # Semivowels
    "JA": ("y", "a"), "JE": ("y", "e"),
    "WA": ("w", "a"), "WE": ("w", "e"), "WI": ("w", "i"),
    # Known polyphonous: RA2 = /la/ (distinct from RA = /ra/)
    "RA2": ("l", "a"),
}


_SUBSCRIPT_MAP = str.maketrans("₂₃₄₅", "2345")


def _lookup_sign(sign: str) -> SignDecomposition | None:
    """Look up a sign, falling back to base form for subscript variants.

    PA₃ → PA3 → PA (found). RA2 stays RA2 (already in table).
    """
    import re
    # Normalize Unicode subscripts to ASCII digits first
    upper = sign.upper().translate(_SUBSCRIPT_MAP)
    decomp = SIGN_DECOMPOSITION.get(upper)
    if decomp:
        return decomp
    # Strip trailing digits (subscript variants like PA3, KI2)
    base = re.sub(r"\d+$", "", upper)
    if base and base != upper:
        return SIGN_DECOMPOSITION.get(base)
    return None


def extract_skeleton(transliteration: str) -> str:
    """Extract consonantal skeleton from a transliteration.

    Example: KI-RE-TA -> k-r-t, JA-SA-SA-RA-ME -> y-s-s-r-m
    Handles subscript variants: KU-PA₃-NU -> k-p-n (PA₃ treated as PA)
    """
    syllables = transliteration.split("-")
    consonants = []
    for syl in syllables:
        decomp = _lookup_sign(syl)
        if decomp and decomp[0]:
            consonants.append(decomp[0])
    return "".join(consonants)


def extract_full(transliteration: str) -> list[SignDecomposition]:
    """Extract full CV decomposition (consonant, vowel) for each syllable."""
    result = []
    for syl in transliteration.split("-"):
        decomp = _lookup_sign(syl)
        if decomp:
            result.append(decomp)
    return result


def validate_decomposition_coverage(corpus_signs: set[str]) -> list[str]:
    """Return signs present in corpus but missing from SIGN_DECOMPOSITION."""
    return sorted(corpus_signs - set(SIGN_DECOMPOSITION.keys()))
