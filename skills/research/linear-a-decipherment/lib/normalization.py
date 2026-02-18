"""Port of SEMITIC._normalize() and SEMITIC._lookupIn() from semiticLexicon.js."""
from __future__ import annotations

import re
from typing import TypeVar

T = TypeVar("T")

SUBSCRIPT_MAP = str.maketrans("₂₃₄₅", "2345")
WORD_SEPARATORS: frozenset[str] = frozenset({"\n", "\u10101"})


def normalize(word: str) -> str:
    """Strip subscripts and logogram prefixes (*NNN- or *NNN-VS-).

    Matches the JS SEMITIC._normalize(): subscript chars (₂₃₄₅) are removed
    entirely, not converted to digits. This ensures KU-PA₃-NU → KU-PA-NU
    (matching the Gordon lexicon key), not KU-PA3-NU.
    """
    # Strip Unicode subscript digits (₂₃₄₅) entirely — matches JS behavior
    result = re.sub(r"[₂₃₄₅]", "", word)
    # Strip logogram prefix: *NNN- or *NNN-VS-
    return re.sub(r"^\*\d+(-VS)?-", "", result)


def lookup_in(entries: dict[str, T], word: str) -> T | None:
    """Look up with normalization cascade: exact -> normalized -> J/Y swap."""
    if not word or word in WORD_SEPARATORS:
        return None
    if word in entries:
        return entries[word]
    norm = normalize(word)
    if norm != word and norm in entries:
        return entries[norm]
    for variant in _jy_variants(norm):
        if variant in entries:
            return entries[variant]
    return None


def _jy_variants(word: str) -> list[str]:
    """Generate J/Y substitution variants for GORILA/Gordon convention mismatch."""
    variants = []
    ja_to_ya = re.sub(r"\bJA", "YA", word).replace("-JA-", "-YA-").replace("-JA", "-YA")
    if ja_to_ya != word:
        variants.append(ja_to_ya)
    ya_to_ja = re.sub(r"\bYA", "JA", word).replace("-YA-", "-JA-").replace("-YA", "-JA")
    if ya_to_ja != word:
        variants.append(ya_to_ja)
    return variants
