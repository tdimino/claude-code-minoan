#!/usr/bin/env python3
"""Base eval framework for autoresearch experiments.

Provides gate registration, composite scoring, and three-tier output protocol.
Copy this to .lab/eval.py during scaffold, then add project-specific gates.

Usage:
    python3 .lab/eval.py           # run eval, print JSON to stdout
    python3 eval_base.py           # same (standalone test)

Output (stdout): JSON object with composite, per-gate, tier scores.
Diagnostics (stderr): GATE/METRIC/TRACE lines for the runner to parse.
"""

import json
import logging
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------------------
# Safe identifier regex — used to validate gate names before emitting to stderr
# ---------------------------------------------------------------------------
_IDENT_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

# ---------------------------------------------------------------------------
# Gate registry
# ---------------------------------------------------------------------------
# Each entry: (name: str, tier: int, weight: float, fn: Callable[[], float])
GATES: list[tuple[str, int, float, Callable]] = []

# ---------------------------------------------------------------------------
# Logging — diagnostics always go to stderr so stdout stays clean JSON
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stderr,
)
log = logging.getLogger("eval")


# ---------------------------------------------------------------------------
# Three-tier output protocol helpers
# ---------------------------------------------------------------------------

def _emit_gate(name: str, passed: bool) -> None:
    """Emit GATE line to stderr: GATE name=PASS|FAIL"""
    if not _IDENT_RE.match(name):
        _emit_trace(name, f"invalid gate name: {name!r}")
        return
    status = "PASS" if passed else "FAIL"
    print(f"GATE {name}={status}", file=sys.stderr)


def _emit_metric(name: str, score: float) -> None:
    """Emit METRIC line to stderr: METRIC name_score=X.XXXX"""
    if not _IDENT_RE.match(name):
        _emit_trace(name, f"invalid metric name: {name!r}")
        return
    print(f"METRIC {name}_score={score:.4f}", file=sys.stderr)


def _emit_trace(name: str, error: str) -> None:
    """Emit TRACE line to stderr: TRACE name_crashed=<error summary>"""
    # Sanitize: strip newlines so the TRACE stays on one line
    safe = error.replace("\n", " | ")[:200]
    print(f"TRACE {name}_crashed={safe}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Subprocess helper
# ---------------------------------------------------------------------------

def run_command(
    args: list[str],
    timeout: int = 60,
    cwd: str | None = None,
) -> subprocess.CompletedProcess:
    """Run a command and return CompletedProcess.

    Never raises on non-zero exit — caller checks returncode.
    Raises subprocess.TimeoutExpired only if timeout is exceeded.
    """
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd,
    )


# ---------------------------------------------------------------------------
# Code analysis helper
# ---------------------------------------------------------------------------

def count_pattern(text: str, pattern: str) -> int:
    """Count occurrences of a regex pattern in a text string.

    Primary usage: count matches in subprocess output.
        count_pattern(result.stdout, r"(\d+) passed")

    Args:
        text: The text to search in (e.g. subprocess stdout).
        pattern: Regular expression to search for.

    Returns:
        Total count of non-overlapping matches.
    """
    if not text:
        return 0
    return len(re.findall(pattern, text))


def count_pattern_in_files(pattern: str, path: str | Path, glob_pat: str = "**/*") -> int:
    """Count occurrences of a regex pattern across files matching glob.

    Args:
        pattern: Regular expression to search for.
        path: Root directory to search in.
        glob_pat: Glob pattern for files to include (default: all files).

    Returns:
        Total count of non-overlapping matches across all matched files.
    """
    root = Path(path)
    if not root.exists():
        return 0
    compiled = re.compile(pattern)
    total = 0
    for f in root.glob(glob_pat):
        if not f.is_file():
            continue
        try:
            content = f.read_text(errors="ignore")
            total += len(compiled.findall(content))
        except (OSError, PermissionError):
            pass
    return total


# ---------------------------------------------------------------------------
# Gate decorator
# ---------------------------------------------------------------------------

def register_gate(name: str, tier: int, weight: float):
    """Decorator to register a function as an eval gate.

    The decorated function must return a float in [0.0, 1.0].
    1.0 = fully passing. 0.0 = fully failing. Partial credit allowed.

    Args:
        name: Identifier for this gate (must match ^[a-zA-Z_][a-zA-Z0-9_]*$).
        tier: Tier number (1–4). Used for tier-normalized scoring.
        weight: Weight of this gate in the composite. Weights across all gates
                are normalized automatically—they don't have to sum to 1.

    Example:
        @register_gate("build_passes", tier=1, weight=1.0)
        def gate_build():
            result = run_command(["cargo", "build"], timeout=120)
            return 1.0 if result.returncode == 0 else 0.0
    """
    if not _IDENT_RE.match(name):
        raise ValueError(
            f"Gate name {name!r} is not a valid identifier. "
            "Must match ^[a-zA-Z_][a-zA-Z0-9_]*$"
        )
    # Accept both integer (1-4) and string ("t1"-"t4") tier values
    _tier_map = {"t1": 1, "t2": 2, "t3": 3, "t4": 4}
    if isinstance(tier, str):
        tier = _tier_map.get(tier, tier)
    if tier not in (1, 2, 3, 4):
        raise ValueError(f"Gate tier must be 1–4 or 't1'–'t4', got {tier}")
    if not (0.0 < weight <= 1.0):
        raise ValueError(f"Gate weight must be in (0, 1], got {weight}")

    def decorator(fn: Callable) -> Callable:
        GATES.append((name, tier, weight, fn))
        return fn

    return decorator


# ---------------------------------------------------------------------------
# Core eval runner
# ---------------------------------------------------------------------------

def run_eval() -> dict:
    """Run all registered gates and return a composite result dict.

    Returns a dict with:
        composite         float   Weighted composite score in [0, 1].
        gates_at_1        int     Number of gates returning exactly 1.0.
        gates_total       int     Total number of gates registered.
        crashed_gates     list    Names of gates that raised exceptions.
        per_gate          dict    {name: score} for every gate.
        tier1_normalized  float   Normalized score for tier-1 gates only.
        tier2_normalized  float   Normalized score for tier-2 gates only.
        tier3_normalized  float   Normalized score for tier-3 gates only.
        tier4_normalized  float   Normalized score for tier-4 gates only.
    """
    if not GATES:
        log.warning("No gates registered. Did you forget @register_gate decorators?")
        return _empty_result()

    per_gate: dict[str, float] = {}
    crashed: list[str] = []

    # Tier accumulators: {tier: (weighted_sum, total_weight)}
    tier_acc: dict[int, list[float]] = {1: [0.0, 0.0], 2: [0.0, 0.0], 3: [0.0, 0.0], 4: [0.0, 0.0]}

    total_weight = 0.0
    weighted_sum = 0.0

    for name, tier, weight, fn in GATES:
        log.info(f"Running gate: {name} (tier={tier}, weight={weight})")
        t0 = time.monotonic()
        try:
            score = float(fn())
            # Clamp to [0, 1]
            score = max(0.0, min(1.0, score))
            elapsed = time.monotonic() - t0
            log.info(f"  {name}: {score:.4f} ({elapsed:.1f}s)")
            _emit_gate(name, score >= 1.0)
            _emit_metric(name, score)
        except subprocess.TimeoutExpired as e:
            elapsed = time.monotonic() - t0
            err = f"timeout after {elapsed:.0f}s"
            log.error(f"  {name}: CRASHED — {err}")
            _emit_trace(name, err)
            score = 0.0
            crashed.append(name)
        except Exception as e:
            elapsed = time.monotonic() - t0
            err = f"{type(e).__name__}: {e}"
            log.error(f"  {name}: CRASHED — {err}")
            _emit_trace(name, err)
            score = 0.0
            crashed.append(name)

        per_gate[name] = score
        tier_acc[tier][0] += score * weight
        tier_acc[tier][1] += weight
        weighted_sum += score * weight
        total_weight += weight

    # Composite: normalize by total weight so weights don't have to sum to 1
    composite = weighted_sum / total_weight if total_weight > 0 else 0.0

    # Tier-normalized: per-tier weighted average
    def tier_score(tier: int) -> float:
        ws, tw = tier_acc[tier]
        return ws / tw if tw > 0 else 0.0

    gates_at_1 = sum(1 for s in per_gate.values() if s >= 1.0)

    result = {
        "composite": round(composite, 4),
        "gates_at_1": gates_at_1,
        "gates_total": len(GATES),
        "crashed_gates": crashed,
        "per_gate": {k: round(v, 4) for k, v in per_gate.items()},
        "tier1_normalized": round(tier_score(1), 4),
        "tier2_normalized": round(tier_score(2), 4),
        "tier3_normalized": round(tier_score(3), 4),
        "tier4_normalized": round(tier_score(4), 4),
    }

    # Emit composite metric to stderr for runner to parse
    _emit_metric("composite", composite)
    log.info(
        f"Eval complete: composite={composite:.4f}, "
        f"gates_at_1={gates_at_1}/{len(GATES)}, "
        f"crashed={crashed}"
    )
    return result


def _empty_result() -> dict:
    return {
        "composite": 0.0,
        "gates_at_1": 0,
        "gates_total": 0,
        "crashed_gates": [],
        "per_gate": {},
        "tier1_normalized": 0.0,
        "tier2_normalized": 0.0,
        "tier3_normalized": 0.0,
        "tier4_normalized": 0.0,
    }


# ---------------------------------------------------------------------------
# Example gates (remove or replace in your project's eval.py)
# ---------------------------------------------------------------------------

@register_gate("example_always_passes", tier=1, weight=0.5)
def _gate_example_pass() -> float:
    """Placeholder: always returns 1.0. Replace with real gates."""
    return 1.0


@register_gate("example_always_fails", tier=1, weight=0.5)
def _gate_example_fail() -> float:
    """Placeholder: always returns 0.0. Replace with real gates."""
    return 0.0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    result = run_eval()
    # Print JSON to stdout for the runner to parse
    print(json.dumps(result, indent=2))
    # Human-readable summary line (also to stdout, after JSON)
    print(
        f"\nComposite: {result['composite']:.4f} "
        f"({result['gates_at_1']}/{result['gates_total']} gates at 1.0)"
    )
