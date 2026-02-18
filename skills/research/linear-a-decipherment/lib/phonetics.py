"""Weighted Levenshtein distance with Semitic-specific sound shift costs.

Semitic languages exhibit systematic sound correspondences (e.g., voicing pairs
t/d, emphatic shifts k/q, liquid interchange l/r). Standard Levenshtein treats
all substitutions equally; this module weights known sound shifts lower.
"""
from __future__ import annotations

# Substitution costs for known Semitic sound correspondences.
# Default substitution cost is 1.0; these override for phonetically close pairs.
SEMITIC_DISTANCES: dict[tuple[str, str], float] = {
    # Voicing pairs (minimal distance)
    ("t", "d"): 0.1,
    ("k", "g"): 0.1,
    ("p", "b"): 0.1,
    ("s", "z"): 0.1,
    # Manner shifts
    ("s", "sh"): 0.15,
    ("l", "r"): 0.15,
    # Emphatic correspondences
    ("t", "T"): 0.3,
    ("k", "q"): 0.3,
    ("d", "T"): 0.35,
    ("s", "S"): 0.3,
    # Guttural / laryngeal
    ("h", "x"): 0.3,
    # Semivowel interchange
    ("w", "y"): 0.25,
}


def _get_sub_cost(a: str, b: str, distances: dict[tuple[str, str], float]) -> float:
    """Look up substitution cost (symmetric)."""
    if a == b:
        return 0.0
    return distances.get((a, b), distances.get((b, a), 1.0))


def weighted_levenshtein(
    s1: str,
    s2: str,
    distances: dict[tuple[str, str], float] | None = None,
) -> float:
    """Weighted Levenshtein with custom Semitic substitution costs.

    Returns raw edit distance (not normalized). For skeletons of 2-4 chars,
    distances < 0.5 indicate strong matches.
    """
    costs = distances or SEMITIC_DISTANCES
    n, m = len(s1), len(s2)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = float(i)
    for j in range(m + 1):
        dp[0][j] = float(j)

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            sub_cost = _get_sub_cost(s1[i - 1], s2[j - 1], costs)
            dp[i][j] = min(
                dp[i - 1][j] + 1.0,       # deletion
                dp[i][j - 1] + 1.0,       # insertion
                dp[i - 1][j - 1] + sub_cost,  # substitution
            )

    return dp[n][m]
