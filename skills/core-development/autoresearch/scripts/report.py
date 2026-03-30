#!/usr/bin/env python3
"""Autoresearch status report.

This is the /autoresearch status command. It reads .lab/config.json and
.lab/results.tsv, runs the live eval, and renders a structured markdown
summary with convergence signals, experiment timeline, and dead-ends.

Usage:
    python3 report.py [--repo-root /path/to/repo] [--no-live-eval]
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Convergence signal definitions
# 9 signals — flag when ≥6 are active
# ---------------------------------------------------------------------------

CONVERGENCE_SIGNALS = [
    (
        "plateau_5",
        "Last 5 experiments show <0.005 composite change",
        lambda rows: _plateau_check(rows, n=5, threshold=0.005),
    ),
    (
        "plateau_10",
        "Last 10 experiments show <0.002 composite change",
        lambda rows: _plateau_check(rows, n=10, threshold=0.002),
    ),
    (
        "keep_rate_low",
        "Keep rate <20% in last 10 experiments",
        lambda rows: _keep_rate(rows, n=10) < 0.20,
    ),
    (
        "keep_rate_very_low",
        "Keep rate <10% in last 20 experiments",
        lambda rows: _keep_rate(rows, n=20) < 0.10,
    ),
    (
        "crash_rate_high",
        "Crash rate >30% in last 10 experiments",
        lambda rows: _crash_rate(rows, n=10) > 0.30,
    ),
    (
        "timeout_rate_high",
        "Timeout rate >20% in last 10 experiments",
        lambda rows: _timeout_rate(rows, n=10) > 0.20,
    ),
    (
        "high_composite",
        "Current composite ≥ 0.95",
        lambda rows: _latest_composite(rows) >= 0.95,
    ),
    (
        "many_experiments",
        "≥ 40 experiments completed",
        lambda rows: len([r for r in rows if r["id"] != "0"]) >= 40,
    ),
    (
        "no_improvement_20",
        "No keep in last 20 experiments",
        lambda rows: _no_keep_streak(rows, n=20),
    ),
]


# ---------------------------------------------------------------------------
# Signal helpers
# ---------------------------------------------------------------------------

def _latest_composite(rows: list) -> float:
    non_base = [r for r in rows if r.get("status") != "baseline"]
    if not non_base:
        base = [r for r in rows if r.get("status") == "baseline"]
        return float(base[-1]["composite"]) if base else 0.0
    return float(non_base[-1]["composite"])


def _plateau_check(rows: list, n: int, threshold: float) -> bool:
    """True if last n composites are within threshold of each other."""
    recent = [float(r["composite"]) for r in rows[-n:] if r.get("composite")]
    if len(recent) < n:
        return False
    return (max(recent) - min(recent)) < threshold


def _keep_rate(rows: list, n: int) -> float:
    recent = rows[-n:]
    if not recent:
        return 1.0
    keeps = sum(1 for r in recent if r.get("status") == "keep")
    return keeps / len(recent)


def _crash_rate(rows: list, n: int) -> float:
    recent = rows[-n:]
    if not recent:
        return 0.0
    crashes = sum(1 for r in recent if r.get("status") == "crash")
    return crashes / len(recent)


def _timeout_rate(rows: list, n: int) -> float:
    recent = rows[-n:]
    if not recent:
        return 0.0
    timeouts = sum(1 for r in recent if r.get("status") == "timeout")
    return timeouts / len(recent)


def _no_keep_streak(rows: list, n: int) -> bool:
    recent = [r for r in rows[-n:] if r.get("status") not in ("baseline",)]
    if len(recent) < n:
        return False
    return all(r.get("status") != "keep" for r in recent)


# ---------------------------------------------------------------------------
# TSV parser
# ---------------------------------------------------------------------------

def parse_results_tsv(path: Path) -> list:
    """Parse results.tsv into list of dicts."""
    if not path.exists():
        return []
    rows = []
    lines = path.read_text().splitlines()
    if not lines:
        return []
    header = [h.strip() for h in lines[0].split("\t")]
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        row = {}
        for i, col in enumerate(header):
            row[col] = parts[i].strip() if i < len(parts) else ""
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Branch genealogy from rows
# ---------------------------------------------------------------------------

def build_branch_tree(rows: list) -> str:
    """Render branch genealogy as ASCII tree."""
    branches = {}
    for row in rows:
        b = row.get("branch", "main")
        parent = row.get("parent", "-")
        if b not in branches:
            branches[b] = {"parent": parent, "experiments": []}
        branches[b]["experiments"].append(row.get("id", "?"))

    if not branches:
        return "  (no branches yet)"

    lines = []
    for branch, info in branches.items():
        parent = info["parent"]
        exp_ids = ", ".join(info["experiments"][:5])
        if len(info["experiments"]) > 5:
            exp_ids += f" … (+{len(info['experiments']) - 5} more)"
        parent_str = f" (from {parent})" if parent != "-" else ""
        lines.append(f"  {branch}{parent_str}: [{exp_ids}]")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Live eval
# ---------------------------------------------------------------------------

def run_live_eval(repo_root: Path) -> dict | None:
    """Run .lab/eval.py and return results dict."""
    eval_script = repo_root / ".lab" / "eval.py"
    if not eval_script.exists():
        return None
    try:
        result = subprocess.run(
            [sys.executable, str(eval_script)],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=repo_root,
        )
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        return None


# ---------------------------------------------------------------------------
# Main report renderer
# ---------------------------------------------------------------------------

def render_report(repo_root: Path, no_live_eval: bool = False) -> str:
    lab_dir = repo_root / ".lab"

    # Load config
    config_path = lab_dir / "config.json"
    if not config_path.exists():
        return f"ERROR: No .lab/config.json found at {lab_dir}\nRun /autoresearch init first."
    config = json.loads(config_path.read_text())

    repo_name = config.get("repo_name", repo_root.name)
    language = config.get("language", "unknown")

    # Parse results
    rows = parse_results_tsv(lab_dir / "results.tsv")

    # Stats
    all_exps = [r for r in rows if r.get("status") != "baseline"]
    total = len(all_exps)
    keeps = sum(1 for r in all_exps if r.get("status") == "keep")
    discards = sum(1 for r in all_exps if r.get("status") == "discard")
    interesting = sum(1 for r in all_exps if r.get("status") == "interesting")
    crashes = sum(1 for r in all_exps if r.get("status") == "crash")
    timeouts = sum(1 for r in all_exps if r.get("status") == "timeout")

    baseline_row = next((r for r in rows if r.get("status") == "baseline"), None)
    baseline_composite = float(baseline_row["composite"]) if baseline_row else 0.0

    # Live eval
    live_composite = None
    live_gates = []
    if not no_live_eval:
        print("Running live eval...", end=" ", flush=True)
        live_results = run_live_eval(repo_root)
        if live_results:
            live_composite = live_results.get("composite", 0.0)
            live_gates = live_results.get("gates", [])
            print(f"composite={live_composite:.4f}")
        else:
            print("skipped (eval.py not runnable)")
    else:
        # Use latest row composite
        if rows:
            live_composite = float(rows[-1]["composite"])

    delta = (live_composite - baseline_composite) if live_composite is not None else None

    # Convergence signals
    active_signals = []
    inactive_signals = []
    for name, description, check_fn in CONVERGENCE_SIGNALS:
        try:
            active = check_fn(rows)
        except Exception:
            active = False
        if active:
            active_signals.append((name, description))
        else:
            inactive_signals.append((name, description))

    convergence_warning = len(active_signals) >= 6

    # Dead ends
    dead_ends_path = lab_dir / "dead-ends.md"
    dead_ends_content = ""
    if dead_ends_path.exists():
        content = dead_ends_path.read_text()
        # Extract just the list items
        items = re.findall(r"^[-*]\s+.+", content, re.MULTILINE)
        if items:
            dead_ends_content = "\n".join(f"  {item}" for item in items[:10])
        else:
            dead_ends_content = "  (none recorded)"
    else:
        dead_ends_content = "  (dead-ends.md not found)"

    # Timestamp
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Build report sections
    lines = []
    lines.append(f"# Autoresearch Status: {repo_name}")
    lines.append(f"\n*Generated: {now} | Language: {language}*\n")

    # Summary stats
    lines.append("## Summary\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total experiments | {total} |")
    lines.append(f"| Keeps | {keeps} ({keeps/max(1,total)*100:.0f}%) |")
    lines.append(f"| Discards | {discards} |")
    lines.append(f"| Interesting | {interesting} |")
    lines.append(f"| Crashes | {crashes} |")
    lines.append(f"| Timeouts | {timeouts} |")
    lines.append(f"| Baseline composite | {baseline_composite:.4f} |")
    if live_composite is not None:
        lines.append(f"| Current composite | {live_composite:.4f} |")
        if delta is not None:
            sign = "+" if delta >= 0 else ""
            lines.append(f"| Delta vs baseline | {sign}{delta:.4f} ({sign}{delta/max(0.0001,baseline_composite)*100:.1f}%) |")

    # Gate breakdown
    if live_gates:
        lines.append("\n## Live Gate Scores\n")
        lines.append("| Gate | Tier | Weight | Score | Bar |")
        lines.append("|------|------|--------|-------|-----|")
        for gate in sorted(live_gates, key=lambda g: (g.get("tier", ""), g.get("gate", ""))):
            score = gate.get("score", 0.0)
            filled = int(score * 10)
            bar = "█" * filled + "░" * (10 - filled)
            lines.append(
                f"| {gate['gate']} | {gate['tier']} | {gate['weight']:.2f} | {score:.2f} | {bar} |"
            )

    # Convergence signals
    lines.append("\n## Convergence Signals\n")
    if convergence_warning:
        lines.append(f"> **WARNING: {len(active_signals)}/9 convergence signals active — consider stopping**\n")
    else:
        lines.append(f"{len(active_signals)}/9 signals active (threshold: 6)\n")

    if active_signals:
        lines.append("**Active:**")
        for name, desc in active_signals:
            lines.append(f"  - [x] `{name}`: {desc}")
    if inactive_signals:
        lines.append("\n**Inactive:**")
        for name, desc in inactive_signals:
            lines.append(f"  - [ ] `{name}`: {desc}")

    # Experiment timeline
    if rows:
        lines.append("\n## Experiment Timeline\n")
        lines.append("| # | Timestamp | Branch | Composite | Delta | Disposition | Note |")
        lines.append("|---|-----------|--------|-----------|-------|-------------|------|")
        prev_composite = None
        for row in rows[-25:]:  # Show last 25
            exp_id = row.get("id", "?")
            ts = row.get("timestamp", "")[:16].replace("T", " ")
            branch = row.get("branch", "")[:20]
            comp = float(row.get("composite", 0))
            status = row.get("status", "")
            note = row.get("note", "")[:40]
            if prev_composite is not None:
                delta_val = comp - prev_composite
                delta_str = f"{'+' if delta_val >= 0 else ''}{delta_val:.4f}"
            else:
                delta_str = "—"
            prev_composite = comp
            disp_icon = {
                "keep": "✓",
                "discard": "✗",
                "baseline": "◇",
                "interesting": "★",
                "crash": "⚡",
                "timeout": "⏱",
            }.get(status, status)
            lines.append(f"| {exp_id} | {ts} | {branch} | {comp:.4f} | {delta_str} | {disp_icon} {status} | {note} |")
        if len(rows) > 25:
            lines.append(f"\n*Showing last 25 of {len(rows)} rows. See `.lab/results.tsv` for full history.*")

    # Branch genealogy
    lines.append("\n## Branch Genealogy\n")
    lines.append("```")
    lines.append(build_branch_tree(rows))
    lines.append("```")

    # Dead ends
    lines.append("\n## Dead Ends\n")
    lines.append(dead_ends_content)

    # Parking lot summary
    parking_lot_path = lab_dir / "parking-lot.md"
    if parking_lot_path.exists():
        content = parking_lot_path.read_text()
        items = re.findall(r"^[-*]\s+.+", content, re.MULTILINE)
        if items:
            lines.append("\n## Parking Lot (Deferred Ideas)\n")
            for item in items[:5]:
                lines.append(f"  {item}")
            if len(items) > 5:
                lines.append(f"  *(+{len(items) - 5} more in .lab/parking-lot.md)*")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Show autoresearch status report")
    parser.add_argument("--repo-root", default=".", help="Path to repo root")
    parser.add_argument(
        "--no-live-eval",
        action="store_true",
        help="Skip running eval.py live (use last recorded composite)",
    )
    parser.add_argument(
        "--output",
        default="-",
        help="Output path (default: stdout)",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()

    if not (repo_root / ".lab").exists():
        print(f"ERROR: No .lab/ directory found at {repo_root}", file=sys.stderr)
        print("Run /autoresearch init first.", file=sys.stderr)
        sys.exit(1)

    report = render_report(repo_root, no_live_eval=args.no_live_eval)

    if args.output == "-":
        print(report)
    else:
        out = Path(args.output)
        out.write_text(report)
        print(f"Report written to {out}")


if __name__ == "__main__":
    main()
