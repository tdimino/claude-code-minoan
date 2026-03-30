#!/usr/bin/env python3
"""Autoresearch runner template.

Copied to .lab/runner.py during `autoresearch init`. All paths read from
.lab/config.json — nothing is hardcoded to a specific project.

Drives a Karpathy-style loop:
    hypothesis (via claude -p) → implement (via claude -p) → eval → keep/discard

Usage:
    python3 .lab/runner.py
    python3 .lab/runner.py --dry-run --max-iterations 1
    python3 .lab/runner.py --max-iterations 50

The runner always operates on an autoresearch/ branch. It will create one if
the current branch is not prefixed with the configured branch_prefix.

Lock file at .lab/.runner.lock prevents concurrent runs.
Results appended to .lab/results.tsv.
Eval report auto-regenerated at .lab/eval-report.md after every iteration.
Dead ends logged to .lab/dead-ends.md when an experiment is marked INTERESTING.
"""

import argparse
import atexit
import csv
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration — loaded from .lab/config.json
# ---------------------------------------------------------------------------

_LAB_DIR = Path(".lab")
_CONFIG_PATH = _LAB_DIR / "config.json"


def _load_config() -> dict:
    if not _CONFIG_PATH.exists():
        print(
            f"ERROR: {_CONFIG_PATH} not found. "
            "Run `autoresearch init` first or create .lab/config.json manually.",
            file=sys.stderr,
        )
        sys.exit(1)
    return json.loads(_CONFIG_PATH.read_text())


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def _setup_logging(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"runner-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stderr),
        ],
    )
    return logging.getLogger("autoresearch"), log_file


# ---------------------------------------------------------------------------
# Environment — strip ANTHROPIC_API_KEY so claude -p uses subscription auth
# ---------------------------------------------------------------------------

def claude_env() -> dict:
    """Return env dict with ANTHROPIC_API_KEY removed for subscription auth."""
    return {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}


# ---------------------------------------------------------------------------
# Lock file management
# ---------------------------------------------------------------------------

def acquire_lock(lock_path: Path, log: logging.Logger) -> None:
    """Acquire the runner lock. Exits on failure (existing live process)."""
    if lock_path.exists():
        pid_str = lock_path.read_text().strip()
        try:
            pid = int(pid_str)
            os.kill(pid, 0)  # Signal 0: check if process is alive
            log.error(f"Lock held by active PID {pid}. Aborting.")
            sys.exit(1)
        except (ValueError, ProcessLookupError, PermissionError):
            log.info(f"Stale lock (PID {pid_str}). Removing.")
            lock_path.unlink(missing_ok=True)

    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
    except FileExistsError:
        log.error("Lock race lost. Another runner started simultaneously.")
        sys.exit(1)


def release_lock(lock_path: Path) -> None:
    lock_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Eval runner
# ---------------------------------------------------------------------------

def run_eval(eval_script: Path, repo_root: Path, timeout: int, log: logging.Logger) -> dict:
    """Run .lab/eval.py and parse JSON from stdout.

    Returns a result dict (see eval_base.py for schema).
    On failure, returns a safe fallback with composite=0.
    """
    fallback = {
        "composite": 0.0,
        "gates_at_1": 0,
        "gates_total": 0,
        "crashed_gates": ["__eval_runner_failed__"],
        "per_gate": {},
        "tier1_normalized": 0.0,
        "tier2_normalized": 0.0,
        "tier3_normalized": 0.0,
        "tier4_normalized": 0.0,
    }
    try:
        result = subprocess.run(
            [sys.executable, str(eval_script)],
            capture_output=True, text=True,
            cwd=str(repo_root), timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        log.error(f"Eval timed out after {timeout}s.")
        return fallback

    if result.returncode != 0:
        log.error(f"Eval failed (exit {result.returncode}): {result.stderr[:300]}")
        return fallback

    try:
        # stdout may have JSON followed by a human-readable summary line
        json_part = result.stdout.split("\nComposite:")[0].strip()
        return json.loads(json_part)
    except (json.JSONDecodeError, ValueError):
        log.error(f"Eval JSON parse failed:\n{result.stdout[:500]}")
        return fallback


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def git_current_branch(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True, text=True, cwd=str(repo_root),
    )
    return result.stdout.strip()


def git_ensure_branch(repo_root: Path, branch_prefix: str, log: logging.Logger) -> str:
    """Ensure we're on a branch prefixed with branch_prefix. Create if needed."""
    current = git_current_branch(repo_root)
    if current.startswith(branch_prefix + "/"):
        log.info(f"Already on branch: {current}")
        return current

    new_branch = f"{branch_prefix}/{datetime.now().strftime('%Y%m%d')}"
    log.info(f"Creating branch: {new_branch}")
    result = subprocess.run(
        ["git", "checkout", "-b", new_branch],
        capture_output=True, text=True, cwd=str(repo_root),
    )
    if result.returncode != 0:
        # Branch may already exist from a prior run — try checking it out
        result = subprocess.run(
            ["git", "checkout", new_branch],
            capture_output=True, text=True, cwd=str(repo_root),
        )
        if result.returncode != 0:
            log.error(f"Cannot switch to branch {new_branch}: {result.stderr}")
            sys.exit(1)

    verify = git_current_branch(repo_root)
    if not verify.startswith(branch_prefix + "/"):
        log.error(f"FATAL: still on {verify}, not a {branch_prefix}/ branch.")
        sys.exit(1)
    return new_branch


def git_log_recent(repo_root: Path, n: int = 20) -> str:
    result = subprocess.run(
        ["git", "log", "--oneline", f"-{n}"],
        capture_output=True, text=True, cwd=str(repo_root),
    )
    return result.stdout.strip()


def git_commit(repo_root: Path, description: str, log: logging.Logger) -> str | None:
    """Stage all changes and commit. Returns short hash or None on failure."""
    subprocess.run(["git", "add", "-A"], cwd=str(repo_root))
    result = subprocess.run(
        ["git", "commit", "-m", f"autoresearch: {description}"],
        capture_output=True, text=True, cwd=str(repo_root),
    )
    if result.returncode != 0:
        log.error(f"git commit failed: {result.stderr[:200]}")
        return None
    hash_result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True, cwd=str(repo_root),
    )
    return hash_result.stdout.strip()


def git_revert(repo_root: Path, log: logging.Logger) -> None:
    """Revert the last commit (discard experiment)."""
    result = subprocess.run(
        ["git", "reset", "--hard", "HEAD~1"],
        capture_output=True, text=True, cwd=str(repo_root),
    )
    if result.returncode != 0:
        log.error(f"git reset failed: {result.stderr[:200]}")


def git_revert_uncommitted(repo_root: Path) -> None:
    """Discard uncommitted changes without removing a commit."""
    subprocess.run(["git", "checkout", "."], cwd=str(repo_root))
    subprocess.run(["git", "clean", "-fd", "--", "."], cwd=str(repo_root))


# ---------------------------------------------------------------------------
# Hypothesis generation
# ---------------------------------------------------------------------------

def build_hypothesis_prompt(
    program: str,
    eval_report: str,
    results_tail: str,
    git_recent: str,
    baseline: dict,
    repo_description: str,
) -> str:
    """Build the prompt for hypothesis generation via claude -p.

    Generic—uses config.repo_description instead of project-specific text.
    """
    return f"""You are the hypothesis generator for an autoresearch loop improving: {repo_description}

Read the program constraints, recent results, and git history below.
Propose ONE focused implementation task that will improve the composite eval score.

Current baseline:
  composite={baseline['composite']:.4f}
  gates_at_1={baseline.get('gates_at_1', '?')}/{baseline.get('gates_total', '?')}
  tier2={baseline.get('tier2_normalized', 0.0):.4f}

RULES:
- Propose exactly ONE change completable in a single claude -p session (~50 turns)
- Output valid JSON with "description" and "implementation_prompt" keys
- "implementation_prompt" must be a complete prompt for claude -p to execute
- Prioritize items from program.md hypothesis list
- Never retry items listed in Dead Ends

## program.md
{program}

## Eval report (cumulative progress from prior runs)
{eval_report}

## Recent results (last 20)
{results_tail}

## Git log (last 20 commits)
{git_recent}

IMPORTANT: Study the eval report. Do NOT re-implement what is already marked as "keep".
Do NOT retry "discard" descriptions unless you have a fundamentally different approach.
Learn from what worked and what failed.

Respond with JSON only:
{{"description": "short description of what to implement", "implementation_prompt": "full prompt for claude -p to execute"}}"""


def generate_hypothesis(
    baseline: dict,
    program_md: Path,
    eval_report_path: Path,
    results_tsv: Path,
    repo_root: Path,
    repo_description: str,
    log: logging.Logger,
) -> dict | None:
    """Generate a hypothesis via claude -p. Returns dict or None on failure."""
    program = program_md.read_text() if program_md.exists() else "(no program.md)"
    eval_report = eval_report_path.read_text() if eval_report_path.exists() else "(no prior runs)"
    results_tail = _read_results_tail(results_tsv)
    git_recent = git_log_recent(repo_root)
    prompt = build_hypothesis_prompt(
        program, eval_report, results_tail, git_recent, baseline, repo_description
    )

    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose"],
            capture_output=True, text=True,
            cwd=str(repo_root), timeout=600,
            env=claude_env(),
        )
    except subprocess.TimeoutExpired:
        log.error("Hypothesis generation timed out after 10 min.")
        return None

    # Extract assistant text from stream-json output
    full_text = ""
    for line in result.stdout.strip().splitlines():
        try:
            event = json.loads(line)
            if event.get("type") == "assistant":
                for block in event.get("message", {}).get("content", []):
                    if block.get("type") == "text":
                        full_text += block.get("text", "")
        except json.JSONDecodeError:
            continue

    if not full_text.strip():
        log.error("Hypothesis generation: no assistant text in stream output.")
        return None

    # Parse JSON from assistant text
    try:
        return json.loads(full_text.strip())
    except json.JSONDecodeError:
        pass

    # Fallback: extract JSON object from text
    try:
        start = full_text.find("{")
        end = full_text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(full_text[start:end])
    except json.JSONDecodeError:
        pass

    log.error(f"Hypothesis parse failed:\n{full_text[:500]}")
    return None


# ---------------------------------------------------------------------------
# Implementation
# ---------------------------------------------------------------------------

def implement(
    hypothesis: dict,
    repo_root: Path,
    timeout: int,
    log: logging.Logger,
) -> bool:
    """Run claude -p with the implementation prompt. Returns True on clean exit."""
    prompt = hypothesis.get("implementation_prompt", "")
    if not prompt:
        log.error("Hypothesis missing implementation_prompt.")
        return False
    try:
        result = subprocess.run(
            ["claude", "-p", prompt,
             "--dangerously-skip-permissions",
             "--max-turns", "80"],
            capture_output=True, text=True,
            cwd=str(repo_root), timeout=timeout,
            env=claude_env(),
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        log.error(f"Implementation timed out after {timeout}s.")
        return False


# ---------------------------------------------------------------------------
# TSV logging and eval report
# ---------------------------------------------------------------------------

def _read_results_tail(results_tsv: Path, n: int = 20) -> str:
    if not results_tsv.exists():
        return "(no results yet)"
    lines = results_tsv.read_text().splitlines()
    return "\n".join(lines[-n:])


def log_result(
    results_tsv: Path,
    commit: str,
    parent: str,
    composite: float,
    status: str,
    description: str,
    duration_s: float,
    log: logging.Logger,
) -> None:
    """Append one row to results.tsv and regenerate eval-report.md."""
    write_header = not results_tsv.exists()
    with open(results_tsv, "a", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        if write_header:
            writer.writerow([
                "timestamp", "experiment_id", "branch", "parent",
                "commit", "composite", "status", "duration_s", "description",
            ])
        experiment_id = f"exp{sum(1 for _ in results_tsv.read_text().splitlines()) if results_tsv.exists() else 1:04d}"
        branch = git_current_branch(results_tsv.parent.parent)
        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            experiment_id,
            branch,
            parent or "—",
            commit or "—",
            f"{composite:.4f}",
            status,
            f"{duration_s:.1f}",
            description,
        ])


def update_eval_report(results_tsv: Path, eval_report: Path, log_file: Path) -> None:
    """Regenerate eval-report.md from results.tsv after every iteration."""
    if not results_tsv.exists():
        return

    rows = []
    with open(results_tsv) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows.append(row)

    keeps = [r for r in rows if r.get("status", "").startswith("keep")]
    discards = [r for r in rows if r.get("status") == "discard"]
    crashes = [r for r in rows if r.get("status") in ("crash", "timeout")]

    latest = rows[-1] if rows else {}
    best = max(rows, key=lambda r: float(r.get("composite", 0))) if rows else {}

    lines = [
        "# Autoresearch Eval Report",
        "",
        f"*Auto-updated: {datetime.now().isoformat(timespec='seconds')}*",
        "",
        "## Current State",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Iterations | {len(rows)} |",
        f"| Keeps | {len(keeps)} |",
        f"| Discards | {len(discards)} |",
        f"| Crashes/Timeouts | {len(crashes)} |",
        f"| Latest composite | {latest.get('composite', '?')} |",
        f"| Best composite | {best.get('composite', '?')} |",
        "",
        "## Timeline",
        "",
        "| Time | Commit | Score | Delta | Status | Description |",
        "|------|--------|-------|-------|--------|-------------|",
    ]

    prev_composite = 0.0
    for r in rows:
        c = float(r.get("composite", 0))
        delta = c - prev_composite
        delta_str = f"+{delta:.4f}" if delta >= 0 else f"{delta:.4f}"
        if r.get("status") == "baseline":
            delta_str = "—"
        lines.append(
            f"| {r.get('timestamp', '?')} "
            f"| {r.get('commit', '?')[:7]} "
            f"| {c:.4f} "
            f"| {delta_str} "
            f"| **{r.get('status', '?')}** "
            f"| {r.get('description', '')} |"
        )
        if r.get("status") in ("keep", "keep*", "baseline"):
            prev_composite = c

    lines.append("")
    if log_file.exists():
        lines.append(f"*Log file: `{log_file.name}`*")
    lines.append("")

    eval_report.write_text("\n".join(lines) + "\n")


def log_dead_end(dead_ends_path: Path, description: str, reason: str) -> None:
    """Append a dead-end entry to .lab/dead-ends.md."""
    timestamp = datetime.now().isoformat(timespec="seconds")
    entry = f"\n## {timestamp}\n\n**Description**: {description}\n\n**Reason**: {reason}\n"
    if not dead_ends_path.exists():
        dead_ends_path.write_text("# Dead Ends\n\nExperiments that should not be retried.\n")
    with open(dead_ends_path, "a") as f:
        f.write(entry)


# ---------------------------------------------------------------------------
# Re-validation (every 10 experiments)
# ---------------------------------------------------------------------------

def re_validate(
    baseline: dict,
    eval_script: Path,
    repo_root: Path,
    eval_timeout: int,
    log: logging.Logger,
) -> dict:
    """Re-run eval to confirm baseline hasn't drifted. Returns updated baseline."""
    log.info("Re-validation: confirming baseline...")
    fresh = run_eval(eval_script, repo_root, eval_timeout, log)
    delta = fresh["composite"] - baseline["composite"]
    if abs(delta) > 0.01:
        log.warning(
            f"Re-validation drift: baseline was {baseline['composite']:.4f}, "
            f"now {fresh['composite']:.4f} (Δ{delta:+.4f}). Updating baseline."
        )
    else:
        log.info(f"Re-validation stable: {fresh['composite']:.4f}")
    return fresh


# ---------------------------------------------------------------------------
# Convergence signal checks
# ---------------------------------------------------------------------------

def check_convergence_signals(
    rows: list[dict],
    baseline: dict,
    log: logging.Logger,
) -> str | None:
    """Return a convergence signal name if one is detected, else None.

    Checks 9 signals after each iteration:
        1. composite >= 0.99 (near-perfect)
        2. composite >= 0.95 (excellent)
        3. 10 consecutive discards
        4. 20 consecutive discards
        5. 5 consecutive crashes
        6. composite unchanged for 10 experiments (plateau)
        7. composite unchanged for 20 experiments (deep plateau)
        8. gates_at_1 == gates_total (all gates passing)
        9. composite delta < 0.001 for last 10 keeps
    """
    if not rows:
        return None

    recent = rows[-20:]  # last 20 rows for windowed checks

    # 1. Near-perfect
    if baseline["composite"] >= 0.99:
        return "near_perfect"

    # 2. Excellent
    if baseline["composite"] >= 0.95:
        return "excellent"

    # 3. 10 consecutive discards
    if len(recent) >= 10 and all(r.get("status") == "discard" for r in recent[-10:]):
        return "ten_consecutive_discards"

    # 4. 20 consecutive discards
    if len(recent) >= 20 and all(r.get("status") == "discard" for r in recent[-20:]):
        return "twenty_consecutive_discards"

    # 5. 5 consecutive crashes
    if len(recent) >= 5 and all(
        r.get("status") in ("crash", "timeout") for r in recent[-5:]
    ):
        return "five_consecutive_crashes"

    # 6. Composite plateau: last 10 rows all same composite
    if len(recent) >= 10:
        composites = [float(r.get("composite", 0)) for r in recent[-10:]]
        if max(composites) - min(composites) < 0.001:
            return "plateau_10"

    # 7. Deep plateau: last 20
    if len(recent) >= 20:
        composites = [float(r.get("composite", 0)) for r in recent[-20:]]
        if max(composites) - min(composites) < 0.001:
            return "plateau_20"

    # 8. All gates passing
    if baseline.get("gates_at_1", 0) == baseline.get("gates_total", -1) > 0:
        return "all_gates_passing"

    # 9. Keep deltas < 0.001
    keeps = [r for r in rows if r.get("status", "").startswith("keep")]
    if len(keeps) >= 10:
        composites = [float(r.get("composite", 0)) for r in keeps[-10:]]
        deltas = [abs(composites[i+1] - composites[i]) for i in range(len(composites)-1)]
        if all(d < 0.001 for d in deltas):
            return "keep_delta_ceiling"

    return None


# ---------------------------------------------------------------------------
# Crash recovery via atexit
# ---------------------------------------------------------------------------

def _make_crash_handler(repo_root: Path, lock_path: Path, log_fn) -> None:
    """Register an atexit handler to restore git state on crash."""
    def handler():
        log_fn("Crash handler: checking for uncommitted changes...")
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=str(repo_root),
        )
        if result.stdout.strip():
            log_fn("Crash handler: discarding uncommitted changes.")
            subprocess.run(["git", "checkout", "."], cwd=str(repo_root))
            subprocess.run(["git", "clean", "-fd", "--", "."], cwd=str(repo_root))
        release_lock(lock_path)

    atexit.register(handler)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Autoresearch runner (from template)")
    parser.add_argument("--max-iterations", type=int, default=None,
                        help="Override max_iterations from config.json")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate hypothesis only, create no git commits")
    args = parser.parse_args()

    # --- Load config ---
    cfg = _load_config()
    repo_root = Path(cfg.get("repo_root", ".")).resolve()
    branch_prefix = cfg.get("branch_prefix", "autoresearch")
    keep_threshold = float(cfg.get("keep_threshold", 0.005))
    max_iterations = args.max_iterations or int(cfg.get("max_iterations", 50))
    experiment_timeout = int(cfg.get("experiment_timeout_s", 300))
    eval_script = repo_root / cfg.get("eval_script", ".lab/eval.py")
    program_md = repo_root / cfg.get("program_md", ".lab/program.md")
    repo_description = cfg.get("repo_description", "this codebase")

    # Derived paths
    lab_dir = repo_root / ".lab"
    results_tsv = lab_dir / "results.tsv"
    eval_report = lab_dir / "eval-report.md"
    dead_ends = lab_dir / "dead-ends.md"
    lock_path = lab_dir / ".runner.lock"

    # --- Setup logging ---
    log, log_file = _setup_logging(lab_dir)
    log.info(f"Autoresearch runner starting. repo={repo_root}, max_iterations={max_iterations}")

    # --- Lock ---
    acquire_lock(lock_path, log)
    _make_crash_handler(repo_root, lock_path, lambda msg: log.warning(msg))
    atexit.register(release_lock, lock_path)

    # --- Branch ---
    if not args.dry_run:
        branch = git_ensure_branch(repo_root, branch_prefix, log)
        log.info(f"On branch: {branch}")

    # --- Baseline eval ---
    log.info("Running baseline eval...")
    t0 = time.monotonic()
    baseline = run_eval(eval_script, repo_root, experiment_timeout, log)
    baseline_duration = time.monotonic() - t0
    log.info(
        f"Baseline: composite={baseline['composite']:.4f}, "
        f"gates_at_1={baseline.get('gates_at_1', '?')}/{baseline.get('gates_total', '?')}"
    )

    if not args.dry_run:
        log_result(
            results_tsv, "baseline", "", baseline["composite"],
            "baseline", "initial state", baseline_duration, log
        )
        update_eval_report(results_tsv, eval_report, log_file)

    # --- Accumulate all rows for convergence checks ---
    all_rows: list[dict] = []

    keeps = 0
    discards = 0
    crashes = 0
    timeouts = 0

    for iteration in range(1, max_iterations + 1):
        log.info("=" * 60)
        log.info(f"Iteration {iteration}/{max_iterations}")
        log.info("=" * 60)

        iter_start = time.monotonic()

        # 1. Generate hypothesis
        log.info("Generating hypothesis...")
        hypothesis = generate_hypothesis(
            baseline, program_md, eval_report, results_tsv,
            repo_root, repo_description, log
        )
        if not hypothesis:
            log.error("Hypothesis generation failed. Skipping iteration.")
            crashes += 1
            all_rows.append({"status": "crash", "composite": str(baseline["composite"])})
            continue

        description = hypothesis.get("description", "unknown")
        log.info(f"Hypothesis: {description}")

        if args.dry_run:
            prompt_preview = hypothesis.get("implementation_prompt", "")[:200]
            log.info(f"DRY RUN — would implement: {description}")
            log.info(f"Prompt preview: {prompt_preview}...")
            continue

        # 2. Implement
        log.info("Implementing...")
        impl_start = time.monotonic()
        success = implement(hypothesis, repo_root, 1800, log)
        impl_duration = time.monotonic() - impl_start

        if not success:
            log.error(f"Implementation failed (non-zero exit, {impl_duration:.0f}s). Cleaning up.")
            git_revert_uncommitted(repo_root)
            crashes += 1
            all_rows.append({"status": "crash", "composite": str(baseline["composite"])})
            log_result(
                results_tsv, "—", "", baseline["composite"],
                "crash", description, impl_duration, log
            )
            update_eval_report(results_tsv, eval_report, log_file)
            continue

        # 3. Commit
        commit_hash = git_commit(repo_root, description, log)
        if not commit_hash:
            log.error("Git commit failed (no changes?). Cleaning up.")
            git_revert_uncommitted(repo_root)
            crashes += 1
            all_rows.append({"status": "crash", "composite": str(baseline["composite"])})
            log_result(
                results_tsv, "—", "", baseline["composite"],
                "crash", description, impl_duration, log
            )
            update_eval_report(results_tsv, eval_report, log_file)
            continue

        log.info(f"Committed: {commit_hash}")

        # 4. Eval
        log.info("Evaluating...")
        eval_start = time.monotonic()
        score = run_eval(eval_script, repo_root, experiment_timeout, log)
        eval_duration = time.monotonic() - eval_start
        total_duration = time.monotonic() - iter_start

        # 4a. Crash check: any eval infrastructure failures
        crashed_gates = score.get("crashed_gates", [])
        if crashed_gates and crashed_gates != ["__eval_runner_failed__"]:
            log.error(
                f"Eval infrastructure crashed — gates: {crashed_gates}. Discarding."
            )
            git_revert(repo_root, log)
            crashes += 1
            status = "crash"
            all_rows.append({"status": "crash", "composite": str(baseline["composite"])})
            log_result(
                results_tsv, commit_hash, "", baseline["composite"],
                status, description, total_duration, log
            )
            update_eval_report(results_tsv, eval_report, log_file)
            continue

        delta = score["composite"] - baseline["composite"]
        log.info(f"Score: composite={score['composite']:.4f} (delta={delta:+.4f})")

        # 5. Keep or discard
        if delta >= keep_threshold:
            # Distinguish significant improvements (KEEP*) from marginal ones (KEEP)
            status = "keep*" if delta >= keep_threshold * 5 else "keep"
            log.info(f"{status.upper()} (delta {delta:+.4f} >= threshold {keep_threshold})")
            baseline = score
            keeps += 1
        elif delta >= 0:
            log.info(f"DISCARD (delta {delta:+.4f} < threshold {keep_threshold})")
            git_revert(repo_root, log)
            discards += 1
            status = "discard"
        else:
            log.info(f"DISCARD (regression {delta:+.4f})")
            git_revert(repo_root, log)
            discards += 1
            status = "discard"

        # Mark INTERESTING if score improved but not enough to keep
        # (useful for finding near-miss approaches to document)
        if 0 < delta < keep_threshold * 0.5:
            log.info(f"Marking as INTERESTING (small improvement: {delta:+.4f})")
            log_dead_end(dead_ends, description, f"Small improvement ({delta:+.4f}) — not enough to keep, but worth noting.")

        all_rows.append({"status": status, "composite": str(score["composite"])})
        log_result(
            results_tsv, commit_hash, "", score["composite"],
            status, description, total_duration, log
        )
        update_eval_report(results_tsv, eval_report, log_file)

        # 6. Convergence checks
        signal = check_convergence_signals(all_rows, baseline, log)
        if signal:
            log.info(f"Convergence signal detected: {signal}")
            if signal in ("near_perfect", "all_gates_passing"):
                log.info("Stopping early — convergence reached.")
                break
            elif signal in ("twenty_consecutive_discards", "five_consecutive_crashes", "plateau_20"):
                log.warning(f"Stopping — {signal}. Check program.md for new hypotheses.")
                break
            # Other signals: log and continue

        # 7. Re-validate every 10 experiments
        if iteration % 10 == 0:
            baseline = re_validate(
                baseline, eval_script, repo_root, experiment_timeout, log
            )
            update_eval_report(results_tsv, eval_report, log_file)

    # --- Summary ---
    log.info("=" * 60)
    log.info(
        f"Complete. {keeps} keeps, {discards} discards, "
        f"{crashes} crashes, {timeouts} timeouts"
    )
    log.info(
        f"Final: composite={baseline['composite']:.4f}, "
        f"gates_at_1={baseline.get('gates_at_1', '?')}/{baseline.get('gates_total', '?')}"
    )
    update_eval_report(results_tsv, eval_report, log_file)
    release_lock(lock_path)


if __name__ == "__main__":
    main()
