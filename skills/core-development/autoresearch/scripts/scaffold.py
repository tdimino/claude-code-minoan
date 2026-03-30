#!/usr/bin/env python3
"""Scaffold a new autoresearch lab in a repository.

This is the /autoresearch init command. It:
  1. Verifies .git/ exists
  2. Detects the stack via detect_stack.py
  3. Creates .lab/ with all necessary files
  4. Runs baseline eval as experiment #0

Usage:
    python3 scaffold.py [--repo-root /path/to/repo] [--yes]
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from string import Template

SKILL_DIR = Path(__file__).parent.parent.resolve()
SCRIPTS_DIR = SKILL_DIR / "scripts"
ASSETS_DIR = SKILL_DIR / "assets"


def run(cmd: list, cwd: Path = None, capture: bool = True):
    """Run a subprocess, returning CompletedProcess."""
    return subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        cwd=cwd,
    )


def detect_stack(repo_root: Path) -> dict:
    """Run detect_stack.py and return parsed StackInfo."""
    result = run(
        [sys.executable, str(SCRIPTS_DIR / "detect_stack.py"), "--repo-root", str(repo_root)],
    )
    if result.returncode != 0:
        print(f"ERROR: detect_stack.py failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    try:
        stack = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"ERROR: Could not parse StackInfo: {e}", file=sys.stderr)
        sys.exit(1)
    if "error" in stack:
        print(f"ERROR: {stack['error']}", file=sys.stderr)
        sys.exit(1)
    return stack


def substitute_template(tmpl_path: Path, replacements: dict) -> str:
    """Read a template file and replace ${VAR} placeholders."""
    content = tmpl_path.read_text()
    # Use string.Template with safe_substitute to avoid KeyError on partial matches
    return Template(content).safe_substitute(replacements)


def build_replacements(stack: dict, repo_root: Path) -> dict:
    """Build substitution dict from StackInfo for template rendering."""
    src_dirs = stack.get("src_dirs", ["./"])
    # Format scope include as JSON array
    scope_include_json = json.dumps(src_dirs)

    conventions = stack.get("conventions", [])
    description = f"{stack.get('language', 'unknown').title()} project"
    if conventions:
        description = ", ".join(conventions[:3])

    return {
        "REPO_NAME": stack.get("repo_name", repo_root.name),
        "REPO_DESCRIPTION": description,
        "LANGUAGE": stack.get("language", "unknown"),
        "BUILD_CMD": stack.get("build_cmd", ""),
        "TEST_CMD": stack.get("test_cmd", ""),
        "LINT_CMD": stack.get("lint_cmd", ""),
        "SCOPE_INCLUDE": scope_include_json,
        "TEST_RUNNER": stack.get("test_runner", ""),
        "LINT_TOOL": stack.get("lint_tool", ""),
        "TEST_COUNT": str(stack.get("test_count_estimate", 0)),
        "DATE": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


def ensure_gitignore(repo_root: Path, entry: str = ".lab/") -> None:
    """Add entry to .gitignore if not already present."""
    gitignore = repo_root / ".gitignore"
    if gitignore.exists():
        lines = gitignore.read_text().splitlines()
        if any(line.strip() == entry.strip("/") or line.strip() == entry for line in lines):
            return
        with gitignore.open("a") as f:
            f.write(f"\n# autoresearch lab\n{entry}\n")
    else:
        gitignore.write_text(f"# autoresearch lab\n{entry}\n")
    print(f"  .gitignore: added {entry}")


def run_baseline_eval(repo_root: Path, lab_dir: Path) -> dict | None:
    """Run eval.py as experiment #0 and return results dict."""
    eval_script = lab_dir / "eval.py"
    if not eval_script.exists():
        return None

    print("\nRunning baseline eval (experiment #0)...")
    result = run([sys.executable, str(eval_script)], cwd=repo_root)
    if result.returncode != 0:
        print(f"  WARNING: eval.py exited non-zero:\n{result.stderr}")
        return None

    try:
        results = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        print(f"  WARNING: Could not parse eval output: {result.stdout[:200]}")
        return None

    return results


def write_results_row(results_tsv: Path, exp_id: int, results: dict, branch: str = "main") -> None:
    """Append a row to results.tsv."""
    composite = results.get("composite", 0.0)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # TSV columns: id, timestamp, branch, parent, composite, disposition, note
    row = f"{exp_id}\t{ts}\t{branch}\t-\t{composite:.4f}\tbaseline\tInitial scaffold\n"
    with results_tsv.open("a") as f:
        f.write(row)


def print_config_summary(stack: dict, lab_dir: Path) -> None:
    """Print a human-readable summary of what will be created."""
    lang = stack.get("language", "unknown")
    conventions = ", ".join(stack.get("conventions", []))
    tests = stack.get("test_count_estimate", 0)
    build_cmd = stack.get("build_cmd", "(none)")
    test_cmd = stack.get("test_cmd", "(none)")
    lint_cmd = stack.get("lint_cmd", "(none)")

    print(f"""
Autoresearch scaffold summary
─────────────────────────────
Lab directory : {lab_dir}
Language      : {lang}  ({conventions})
Build cmd     : {build_cmd}
Test cmd      : {test_cmd}
Lint cmd      : {lint_cmd}
Test count    : ~{tests} (floor set at 90%)
─────────────────────────────
Files to create:
  .lab/runner.py       — experiment runner loop
  .lab/eval_base.py    — gate infrastructure
  .lab/eval.py         — generated gates (4-tier)
  .lab/program.md      — improvement roadmap
  .lab/config.json     — autoresearch config
  .lab/results.tsv     — experiment log
  .lab/log.md          — session narrative log
  .lab/branches.md     — branch genealogy
  .lab/dead-ends.md    — approaches that failed
  .lab/parking-lot.md  — deferred ideas
""")


def main():
    parser = argparse.ArgumentParser(description="Initialize autoresearch lab in a repo")
    parser.add_argument("--repo-root", default=".", help="Path to repo root")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()

    # Verify git repo
    if not (repo_root / ".git").exists():
        print(f"ERROR: {repo_root} is not a git repository (.git not found)", file=sys.stderr)
        sys.exit(1)

    print(f"Detecting stack in {repo_root}...")
    stack = detect_stack(repo_root)
    lab_dir = repo_root / ".lab"

    # Check for existing lab
    if lab_dir.exists():
        print(f"WARNING: .lab/ already exists at {lab_dir}")
        if not args.yes:
            resp = input("Overwrite existing lab? [y/N] ").strip().lower()
            if resp not in ("y", "yes"):
                print("Aborted.")
                sys.exit(0)

    print_config_summary(stack, lab_dir)

    if not args.yes:
        resp = input("Proceed with scaffold? [Y/n] ").strip().lower()
        if resp in ("n", "no"):
            print("Aborted.")
            sys.exit(0)

    # Create .lab/ directory
    lab_dir.mkdir(exist_ok=True)
    print(f"\nCreating lab at {lab_dir}")

    # Build template substitutions
    replacements = build_replacements(stack, repo_root)

    # ---- Copy runner_template.py → .lab/runner.py ----
    runner_tmpl = SCRIPTS_DIR / "runner_template.py"
    runner_dest = lab_dir / "runner.py"
    if runner_tmpl.exists():
        shutil.copy2(runner_tmpl, runner_dest)
        runner_dest.chmod(0o755)
        print("  Created .lab/runner.py")
    else:
        # Phase 1 not yet present — write a placeholder
        runner_dest.write_text(
            "# runner.py — autoresearch experiment runner\n"
            "# This file will be populated by Phase 1 (runner_template.py)\n"
        )
        print("  Created .lab/runner.py (placeholder — Phase 1 pending)")

    # ---- Copy eval_base.py → .lab/eval_base.py ----
    eval_base_src = ASSETS_DIR / "eval_base.py"
    eval_base_dest = lab_dir / "eval_base.py"
    if eval_base_src.exists():
        shutil.copy2(eval_base_src, eval_base_dest)
        print("  Created .lab/eval_base.py")
    else:
        # Minimal stub so eval.py doesn't hard-fail before Phase 1 lands
        eval_base_dest.write_text(
            "# eval_base.py — gate infrastructure (Phase 1 pending)\n"
            "import subprocess, re\n"
            "from pathlib import Path\n"
            "_gates = []\n\n"
            "def register_gate(name, tier, weight):\n"
            "    def decorator(fn):\n"
            "        _gates.append((name, tier, weight, fn))\n"
            "        return fn\n"
            "    return decorator\n\n"
            "def run_command(cmd, timeout=60, cwd=None):\n"
            "    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)\n\n"
            "def count_pattern(text, pattern):\n"
            "    return len(re.findall(pattern, text))\n\n"
            "def run_eval():\n"
            "    results = []\n"
            "    for name, tier, weight, fn in _gates:\n"
            "        try:\n"
            "            score = fn()\n"
            "        except Exception as e:\n"
            "            score = 0.0\n"
            "        results.append({'gate': name, 'tier': tier, 'weight': weight, 'score': score})\n"
            "    composite = sum(r['weight'] * r['score'] for r in results)\n"
            "    return {'gates': results, 'composite': composite}\n"
        )
        print("  Created .lab/eval_base.py (stub — Phase 1 pending)")

    # ---- Run eval_gen.py → .lab/eval.py ----
    eval_gen_script = SCRIPTS_DIR / "eval_gen.py"
    eval_dest = lab_dir / "eval.py"
    result = run(
        [
            sys.executable,
            str(eval_gen_script),
            "--repo-root", str(repo_root),
            "--output", str(eval_dest),
        ],
    )
    if result.returncode == 0:
        print(f"  Created .lab/eval.py  ({result.stdout.strip()})")
    else:
        print(f"  WARNING: eval_gen.py failed:\n{result.stderr}")
        eval_dest.write_text(
            "#!/usr/bin/env python3\n"
            "# eval.py — gate generation failed; inspect with eval_gen.py manually\n"
            "import json\n"
            "if __name__ == '__main__':\n"
            "    print(json.dumps({'gates': [], 'composite': 0.0}))\n"
        )

    # ---- Generate .lab/program.md ----
    program_tmpl = ASSETS_DIR / "program.md.tmpl"
    program_dest = lab_dir / "program.md"
    if program_tmpl.exists():
        program_dest.write_text(substitute_template(program_tmpl, replacements))
    else:
        # Minimal fallback
        program_dest.write_text(
            f"# Autoresearch Program: {replacements['REPO_NAME']}\n\n"
            f"Language: {replacements['LANGUAGE']}\n"
            f"Generated: {replacements['DATE']}\n\n"
            "## Objective\n\n[Define your improvement objective here]\n\n"
            "## Hypotheses\n\n- [ ] Hypothesis 1\n\n"
            "## Dead Ends\n\n*(none yet)*\n"
        )
    print("  Created .lab/program.md")

    # ---- Generate .lab/config.json ----
    config_tmpl = ASSETS_DIR / "config.json.tmpl"
    config_dest = lab_dir / "config.json"
    if config_tmpl.exists():
        config_dest.write_text(substitute_template(config_tmpl, replacements))
    else:
        # Minimal fallback
        config = {
            "version": 1,
            "repo_name": replacements["REPO_NAME"],
            "language": replacements["LANGUAGE"],
            "build_cmd": replacements["BUILD_CMD"],
            "test_cmd": replacements["TEST_CMD"],
            "lint_cmd": replacements["LINT_CMD"],
            "eval_script": ".lab/eval.py",
            "branch_prefix": "autoresearch",
            "keep_threshold": 0.005,
            "max_iterations": 50,
        }
        config_dest.write_text(json.dumps(config, indent=2))
    print("  Created .lab/config.json")

    # ---- Create empty log files ----
    results_tsv = lab_dir / "results.tsv"
    if not results_tsv.exists():
        results_tsv.write_text("timestamp\texperiment_id\tbranch\tparent\tcommit\tcomposite\tstatus\tduration_s\tdescription\n")
    print("  Created .lab/results.tsv")

    for fname, header in [
        ("log.md", f"# Autoresearch Log: {replacements['REPO_NAME']}\n\n"),
        ("branches.md", "# Branch Genealogy\n\n| Branch | Parent | Composite | Disposition |\n|--------|--------|-----------|-------------|\n"),
        ("dead-ends.md", "# Dead Ends\n\nApproaches tried and abandoned.\n\n"),
        ("parking-lot.md", "# Parking Lot\n\nDeferred ideas for future experiments.\n\n"),
    ]:
        dest = lab_dir / fname
        if not dest.exists():
            dest.write_text(header)
        print(f"  Created .lab/{fname}")

    # ---- Update .gitignore ----
    ensure_gitignore(repo_root, ".lab/")

    # ---- Run baseline eval ----
    results = run_baseline_eval(repo_root, lab_dir)
    if results:
        composite = results.get("composite", 0.0)
        write_results_row(results_tsv, 0, results)
        gate_count = len(results.get("gates", []))
        print(f"\nBaseline eval complete:")
        print(f"  Composite score : {composite:.4f}")
        print(f"  Gates evaluated : {gate_count}")
        print(f"\n  Gate breakdown:")
        for gate in results.get("gates", []):
            bar = "█" * int(gate["score"] * 10) + "░" * (10 - int(gate["score"] * 10))
            print(f"    [{gate['tier']}] {gate['gate']:<22} {bar} {gate['score']:.2f}  (w={gate['weight']:.2f})")
    else:
        print("\nBaseline eval skipped (eval.py not runnable yet).")

    print(f"\nScaffold complete. Lab at: {lab_dir}")
    print("Next steps:")
    print("  1. Edit .lab/program.md — define your improvement objective")
    print("  2. Run: python3 .lab/runner.py  (or /autoresearch run)")
    print("  3. Monitor: python3 scripts/report.py  (or /autoresearch status)")


if __name__ == "__main__":
    main()
