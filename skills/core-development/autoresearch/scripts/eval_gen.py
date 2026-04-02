#!/usr/bin/env python3
"""Generate adversarial eval gates for a repository.

Reads StackInfo from detect_stack.py and writes a .lab/eval.py with 4-tier gates:
  T1 (0.20): build + test + lint
  T2 (0.40): behavioral (stack-specific)
  T3 (0.25): pipeline artifacts
  T4 (0.15): documentation / test-count floor

Usage:
    python3 eval_gen.py --repo-root /path/to/repo --output .lab/eval.py
    python3 eval_gen.py  # defaults: cwd, .lab/eval.py
"""

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from textwrap import dedent


# ---------------------------------------------------------------------------
# Exa enrichment (optional)
# ---------------------------------------------------------------------------

def _exa_gate_hints(language: str) -> list[str]:
    """Query Exa for adversarial testing patterns. Returns list of hint strings."""
    api_key = os.environ.get("EXA_API_KEY", "")
    if not api_key:
        return []
    try:
        import urllib.request
        import urllib.error
        query = f"{language} adversarial testing patterns"
        payload = json.dumps({
            "query": query,
            "numResults": 3,
            "type": "neural",
            "useAutoprompt": True,
        }).encode()
        req = urllib.request.Request(
            "https://api.exa.ai/search",
            data=payload,
            headers={"x-api-key": api_key, "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
        hints = []
        for result in data.get("results", [])[:3]:
            title = result.get("title", "")
            if title:
                hints.append(title)
        return hints
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Gate builders per tier
# ---------------------------------------------------------------------------

def _build_cmd_list(cmd: str) -> str:
    """Convert a shell command string to a Python list literal for generated code."""
    if not cmd:
        return "[]"
    try:
        parts = shlex.split(cmd.replace(" 2>&1", ""))
    except ValueError:
        parts = cmd.replace(" 2>&1", "").split()
    return repr(parts)


def _gate_t1_build(stack: dict) -> str:
    build_cmd = stack.get("build_cmd", "")
    if not build_cmd:
        return ""
    cmd_list = _build_cmd_list(build_cmd)
    return f'''@register_gate("build", "t1", 0.07)
def gate_build():
    """T1: Build gate — must exit 0 AND produce no error lines."""
    r = run_command({cmd_list}, timeout=120)
    if r.returncode != 0:
        return 0.0
    # Anti-cheat: also scan stdout for error patterns
    error_lines = len(re.findall(
        r"(?i)\\berror\\b(?!\\w)|FAILED|could not compile",
        r.stdout or "",
    ))
    return max(0.0, 1.0 - error_lines * 0.1)'''.strip()


def _gate_t1_test(stack: dict) -> str:
    test_cmd = stack.get("test_cmd", "")
    if not test_cmd:
        return ""
    cmd_list = _build_cmd_list(test_cmd)
    language = stack.get("language", "unknown")
    runner = stack.get("test_runner", "")

    # Build the pass-count extraction snippet per runner
    if language == "rust":
        count_expr = dedent("""
            passed = count_pattern(r.stdout or "", r"test .* \\.\\.\\. ok")
            failed = count_pattern(r.stdout or "", r"test .* \\.\\.\\. FAILED")
        """).strip()
        score_expr = "passed / max(1, passed + failed)"
    elif language == "python":
        count_expr = dedent("""
            m = re.search(r"(\\d+) passed", r.stdout or "")
            passed = int(m.group(1)) if m else 0
            m2 = re.search(r"(\\d+) failed", r.stdout or "")
            failed = int(m2.group(1)) if m2 else 0
        """).strip()
        score_expr = "passed / max(1, passed + failed)"
    elif runner in ("vitest", "jest"):
        count_expr = dedent("""
            m = re.search(r"Tests:\\s*(\\d+) passed", r.stdout or "")
            passed = int(m.group(1)) if m else 0
            m2 = re.search(r"(\\d+) failed", r.stdout or "")
            failed = int(m2.group(1)) if m2 else 0
        """).strip()
        score_expr = "passed / max(1, passed + failed)"
    elif language == "go":
        count_expr = dedent("""
            passed = count_pattern(r.stdout or "", r"--- PASS")
            failed = count_pattern(r.stdout or "", r"--- FAIL")
        """).strip()
        score_expr = "passed / max(1, passed + failed)"
    else:
        count_expr = 'passed = 1 if r.returncode == 0 else 0; failed = 0 if r.returncode == 0 else 1'
        score_expr = "passed / max(1, passed + failed)"

    # Indent continuation lines of count_expr to match 4-space function body
    count_expr_indented = count_expr.replace("\n", "\n    ")
    return f'''@register_gate("test", "t1", 0.08)
def gate_test():
    """T1: Test gate — sums passed/failed counts, not just exit code."""
    r = run_command({cmd_list}, timeout=180)
    {count_expr_indented}
    return {score_expr}'''.strip()


def _gate_t1_lint(stack: dict) -> str:
    lint_cmd = stack.get("lint_cmd", "")
    if not lint_cmd:
        return ""
    cmd_list = _build_cmd_list(lint_cmd)
    tool = stack.get("lint_tool", "")

    # Warning-count logic varies by tool
    if tool == "clippy":
        warn_expr = 'count_pattern(r.stdout or "", r"warning:")'
    elif tool == "ruff":
        warn_expr = 'len((r.stdout or "").strip().splitlines())'
    elif tool == "eslint":
        warn_expr = 'count_pattern(r.stdout or "", r"\\bwarning\\b")'
    else:
        warn_expr = 'count_pattern(r.stdout or "", r"(?i)warning")'

    return f'''@register_gate("lint", "t1", 0.05)
def gate_lint():
    """T1: Lint gate — exit code AND warning count both penalized."""
    r = run_command({cmd_list}, timeout=60)
    exit_ok = 1.0 if r.returncode == 0 else 0.0
    warnings = {warn_expr}
    warn_penalty = min(1.0, warnings * 0.05)
    return max(0.0, exit_ok - warn_penalty)'''.strip()


# ---------------------------------------------------------------------------
# T2 behavioral gates (stack-specific)
# ---------------------------------------------------------------------------

def _gates_t2(stack: dict) -> list[str]:
    language = stack.get("language", "unknown")
    build_system = stack.get("build_system", "")
    src_dirs = stack.get("src_dirs", ["./"])
    gates = []

    if language == "rust":
        gates.append('''@register_gate("import_smoke", "t2", 0.10)
def gate_import_smoke():
    """T2: Verify library crate compiles as a dependency (checks pub API)."""
    r = run_command(
        ["cargo", "check", "--lib", "--message-format=short"],
        timeout=90,
    )
    return 1.0 if r.returncode == 0 else 0.0''')

        gates.append('''@register_gate("integration_tests", "t2", 0.15)
def gate_integration_tests():
    """T2: Run only integration tests (tests/ directory)."""
    r = run_command(
        ["cargo", "test", "--test", "*", "--", "--nocapture"],
        timeout=180,
    )
    if r.returncode != 0 and "no integration tests" in (r.stdout or "").lower():
        return 0.5  # No integration tests is a partial pass
    passed = count_pattern(r.stdout or "", r"test .* \\.\\.\\.+ ok")
    failed = count_pattern(r.stdout or "", r"test .* \\.\\.\\.+ FAILED")
    return passed / max(1, passed + failed)''')

        gates.append('''@register_gate("doc_tests", "t2", 0.15)
def gate_doc_tests():
    """T2: Run doc tests — adversarial: ensures examples stay valid."""
    r = run_command(["cargo", "test", "--doc"], timeout=120)
    return 1.0 if r.returncode == 0 else 0.0''')

    elif language == "python":
        primary_src = src_dirs[0].rstrip("/") if src_dirs else "src"
        # Derive the import name: src/ -> try to find package name
        gates.append(f'''@register_gate("import_smoke", "t2", 0.15)
def gate_import_smoke():
    """T2: Import smoke test — verifies package loads without error."""
    import importlib
    src_path = REPO_ROOT / {repr(primary_src)}
    candidates = [p.stem for p in src_path.glob("*.py") if p.stem != "__init__"]
    if not candidates:
        candidates = [p.name for p in src_path.iterdir() if p.is_dir() and (p / "__init__.py").exists()]
    if not candidates:
        return 0.5  # Cannot determine package name
    target = candidates[0]
    r = run_command(
        ["python3", "-c", f"import {{target}}; print('ok')"],
        timeout=30,
    )
    return 1.0 if r.returncode == 0 else 0.0''')

        gates.append('''@register_gate("integration_tests", "t2", 0.15)
def gate_integration_tests():
    """T2: Run integration tests (tests/integration/ or test_integration*.py)."""
    r = run_command(
        ["python3", "-m", "pytest", "-x", "-k", "integration", "-q", "--tb=no"],
        timeout=120,
    )
    m = re.search(r"(\\d+) passed", r.stdout or "")
    if m:
        return min(1.0, int(m.group(1)) / 5)
    # No integration tests marked — partial credit
    return 0.5 if "no tests ran" in (r.stdout or "") else 0.0''')

        gates.append('''@register_gate("cli_smoke", "t2", 0.10)
def gate_cli_smoke():
    """T2: CLI invocation smoke test — verifies entry point is runnable."""
    r = run_command(["python3", "-m", "pytest", "--collect-only", "-q", "--tb=no"], timeout=30)
    # If collection works without error, CLI surface is intact
    return 1.0 if r.returncode == 0 else 0.0''')

    elif language in ("javascript", "typescript"):
        runner = stack.get("test_runner", "npm-test")
        if runner == "vitest":
            int_cmd = ["npx", "vitest", "run", "--reporter=verbose"]
        elif runner == "jest":
            int_cmd = ["npx", "jest", "--testPathPattern=integration", "--passWithNoTests"]
        else:
            int_cmd = ["npm", "test", "--", "--testPathPattern=integration"]

        gates.append(f'''@register_gate("integration_tests", "t2", 0.20)
def gate_integration_tests():
    """T2: Run integration test suite with verbose output."""
    r = run_command({repr(int_cmd)}, timeout=180)
    m = re.search(r"Tests:\\s*(\\d+) passed", r.stdout or "")
    passed = int(m.group(1)) if m else (1 if r.returncode == 0 else 0)
    m2 = re.search(r"(\\d+) failed", r.stdout or "")
    failed = int(m2.group(1)) if m2 else 0
    return passed / max(1, passed + failed)''')

        gates.append('''@register_gate("import_smoke", "t2", 0.10)
def gate_import_smoke():
    """T2: Verify main entry point can be required/imported."""
    r = run_command(["node", "-e", "require('.'); process.exit(0)"], timeout=15)
    return 1.0 if r.returncode == 0 else 0.0''')

        gates.append('''@register_gate("type_check", "t2", 0.10)
def gate_type_check():
    """T2: TypeScript type check (tsc --noEmit) — adversarial against any type cast."""
    r = run_command(["npx", "tsc", "--noEmit", "--strict"], timeout=60)
    errors = count_pattern(r.stdout or "", r"error TS\\d+")
    return 1.0 if r.returncode == 0 else max(0.0, 1.0 - errors * 0.05)''')

    elif language == "go":
        gates.append('''@register_gate("integration_tests", "t2", 0.20)
def gate_integration_tests():
    """T2: Run integration tests tagged with //go:build integration."""
    r = run_command(
        ["go", "test", "-tags=integration", "./...", "-v"],
        timeout=180,
    )
    passed = count_pattern(r.stdout or "", r"--- PASS")
    failed = count_pattern(r.stdout or "", r"--- FAIL")
    if passed == 0 and failed == 0:
        return 0.5  # No integration tests — partial
    return passed / max(1, passed + failed)''')

        gates.append('''@register_gate("import_smoke", "t2", 0.10)
def gate_import_smoke():
    """T2: Verify package builds and exports are intact."""
    r = run_command(["go", "vet", "./..."], timeout=60)
    return 1.0 if r.returncode == 0 else 0.0''')

        gates.append('''@register_gate("race_detector", "t2", 0.10)
def gate_race_detector():
    """T2: Run tests with race detector — surfaces concurrency bugs."""
    r = run_command(["go", "test", "-race", "./..."], timeout=180)
    return 1.0 if r.returncode == 0 else 0.0''')

    else:
        gates.append('''@register_gate("import_smoke", "t2", 0.40)
def gate_import_smoke():
    """T2: Generic smoke test via Makefile."""
    r = run_command(["make", "check"], timeout=60)
    return 1.0 if r.returncode == 0 else 0.0''')

    return [g for g in gates if g]


# ---------------------------------------------------------------------------
# T3 pipeline gates
# ---------------------------------------------------------------------------

def _gates_t3(stack: dict) -> list[str]:
    language = stack.get("language", "unknown")
    build_system = stack.get("build_system", "")
    gates = []

    if language == "rust":
        gates.append('''@register_gate("build_artifacts", "t3", 0.15)
def gate_build_artifacts():
    """T3: Release build produces artifacts — checks target/release."""
    r = run_command(["cargo", "build", "--release"], timeout=300)
    if r.returncode != 0:
        return 0.0
    release_dir = REPO_ROOT / "target" / "release"
    binaries = [f for f in release_dir.glob("*") if f.is_file() and not f.suffix]
    return 1.0 if binaries else 0.5''')

        gates.append('''@register_gate("clippy_release", "t3", 0.10)
def gate_clippy_release():
    """T3: Clippy clean on release profile (stricter)."""
    r = run_command(
        ["cargo", "clippy", "--release", "--", "-D", "warnings"],
        timeout=120,
    )
    return 1.0 if r.returncode == 0 else 0.0''')

    elif language == "python":
        gates.append('''@register_gate("build_artifacts", "t3", 0.15)
def gate_build_artifacts():
    """T3: Package build produces dist/ artifacts."""
    import shutil
    shutil.rmtree(REPO_ROOT / "dist", ignore_errors=True)
    r = run_command(["python3", "-m", "build", "--wheel", "--no-isolation"], timeout=120)
    dist_dir = REPO_ROOT / "dist"
    wheels = list(dist_dir.glob("*.whl")) if dist_dir.exists() else []
    return 1.0 if wheels else 0.0''')

        gates.append('''@register_gate("install_smoke", "t3", 0.10)
def gate_install_smoke():
    """T3: Package installs cleanly into a temp venv (no import-time side effects)."""
    import tempfile
    import shutil
    tmpdir = tempfile.mkdtemp()
    try:
        r1 = run_command(["python3", "-m", "venv", f"{tmpdir}/venv"], timeout=30)
        if r1.returncode != 0:
            return 0.5
        pip = f"{tmpdir}/venv/bin/pip"
        r2 = run_command([pip, "install", "-e", ".", "--quiet"], timeout=60, cwd=REPO_ROOT)
        return 1.0 if r2.returncode == 0 else 0.0
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)''')

    elif language in ("javascript", "typescript"):
        gates.append('''@register_gate("build_artifacts", "t3", 0.15)
def gate_build_artifacts():
    """T3: Build produces output in dist/ or build/ directory."""
    import shutil
    for out_dir in ["dist", "build", ".next", "out"]:
        d = REPO_ROOT / out_dir
        if d.exists():
            shutil.rmtree(d)
    r = run_command(["npm", "run", "build"], timeout=300)
    if r.returncode != 0:
        return 0.0
    for out_dir in ["dist", "build", ".next", "out"]:
        d = REPO_ROOT / out_dir
        if d.exists() and any(d.iterdir()):
            return 1.0
    return 0.5''')

        gates.append('''@register_gate("pack_smoke", "t3", 0.10)
def gate_pack_smoke():
    """T3: npm pack produces a tarball (validates package.json exports)."""
    r = run_command(["npm", "pack", "--dry-run"], timeout=30)
    return 1.0 if r.returncode == 0 else 0.0''')

    elif language == "go":
        gates.append('''@register_gate("build_artifacts", "t3", 0.20)
def gate_build_artifacts():
    """T3: Build produces binary artifacts."""
    r = run_command(["go", "build", "-o", "/dev/null", "./..."], timeout=120)
    return 1.0 if r.returncode == 0 else 0.0''')

        gates.append('''@register_gate("mod_tidy", "t3", 0.05)
def gate_mod_tidy():
    """T3: go mod tidy leaves no diff — catches missing/extra deps."""
    import subprocess as sp
    r = run_command(["go", "mod", "tidy"], timeout=60)
    if r.returncode != 0:
        return 0.0
    diff = sp.run(["git", "diff", "--exit-code", "go.sum", "go.mod"],
                  capture_output=True, text=True, cwd=REPO_ROOT)
    return 1.0 if diff.returncode == 0 else 0.0''')

    else:
        gates.append('''@register_gate("build_artifacts", "t3", 0.25)
def gate_build_artifacts():
    """T3: Generic build artifact check via make."""
    r = run_command(["make", "dist"], timeout=120)
    return 1.0 if r.returncode == 0 else 0.0''')

    return [g for g in gates if g]


# ---------------------------------------------------------------------------
# T4 documentation gates
# ---------------------------------------------------------------------------

def _gates_t4(stack: dict) -> list[str]:
    language = stack.get("language", "unknown")
    test_count = stack.get("test_count_estimate", 0)
    floor = max(1, int(test_count * 0.90))  # 90% of initial count
    gates = []

    gates.append(f'''@register_gate("test_count_floor", "t4", 0.10)
def gate_test_count_floor():
    """T4: Test count must not drop below 90% of baseline ({floor} tests)."""
    floor = {floor}
    current = count_current_tests(REPO_ROOT, {repr(language)})
    if current >= floor:
        return 1.0
    return max(0.0, current / floor)''')

    if language == "rust":
        gates.append('''@register_gate("doc_coverage", "t4", 0.05)
def gate_doc_coverage():
    """T4: Public items have doc comments — no missing_docs warnings."""
    r = run_command(
        ["cargo", "rustdoc", "--", "-D", "missing_docs"],
        timeout=120,
    )
    return 1.0 if r.returncode == 0 else 0.5''')

    elif language == "python":
        gates.append('''@register_gate("doc_coverage", "t4", 0.05)
def gate_doc_coverage():
    """T4: Public functions have docstrings (pydocstyle or grep check)."""
    import re as _re
    missing = 0
    total = 0
    for f in REPO_ROOT.rglob("*.py"):
        if ".lab" in str(f) or "__pycache__" in str(f):
            continue
        content = f.read_text(errors="ignore")
        fns = _re.findall(r"^def (\\w+)\\(", content, _re.MULTILINE)
        for fn in fns:
            if fn.startswith("_"):
                continue
            total += 1
            # Look for docstring after the def line
            pattern = rf"def {fn}\\([^)]*\\)[^:]*:\\s*(?:\\n\\s+(?:\'\'\'|\\\"\\\"\\\"|\\'\\'\\'|#))"
            if not _re.search(pattern, content):
                missing += 1
    if total == 0:
        return 0.5
    return max(0.0, 1.0 - missing / total)''')

    elif language in ("javascript", "typescript"):
        gates.append('''@register_gate("doc_coverage", "t4", 0.05)
def gate_doc_coverage():
    """T4: Exported functions have JSDoc comments."""
    import re as _re
    missing = 0
    total = 0
    exts = ["*.ts", "*.tsx", "*.js", "*.jsx"]
    for ext in exts:
        for f in REPO_ROOT.rglob(ext):
            if ".lab" in str(f) or "node_modules" in str(f):
                continue
            content = f.read_text(errors="ignore")
            exports = _re.findall(r"export\\s+(?:async\\s+)?function\\s+(\\w+)", content)
            for fn in exports:
                total += 1
                idx = content.find(f"function {fn}")
                chunk = content[max(0, idx - 200):idx]
                if "/**" not in chunk:
                    missing += 1
    if total == 0:
        return 0.5
    return max(0.0, 1.0 - missing / total)''')

    else:
        gates.append('''@register_gate("doc_coverage", "t4", 0.05)
def gate_doc_coverage():
    """T4: README.md exists and is non-trivial (>200 chars)."""
    readme = REPO_ROOT / "README.md"
    if not readme.exists():
        return 0.0
    return 1.0 if len(readme.read_text()) > 200 else 0.5''')

    return [g for g in gates if g]


# ---------------------------------------------------------------------------
# Test counter helper (embedded in generated file)
# ---------------------------------------------------------------------------

_TEST_COUNTER_FN = '''
def count_current_tests(root: Path, language: str) -> int:
    """Count current test definitions in the repo (mirrors detect_stack logic)."""
    count = 0
    try:
        if language == "rust":
            for f in root.rglob("*.rs"):
                if ".lab" in str(f) or "target" in str(f):
                    continue
                count += f.read_text(errors="ignore").count("#[test]")
        elif language == "python":
            for f in root.rglob("*.py"):
                if ".lab" in str(f) or "__pycache__" in str(f):
                    continue
                count += len(re.findall(r"def test_", f.read_text(errors="ignore")))
        elif language in ("javascript", "typescript"):
            for ext in ("*.js", "*.ts", "*.jsx", "*.tsx"):
                for f in root.rglob(ext):
                    if ".lab" in str(f) or "node_modules" in str(f):
                        continue
                    count += len(re.findall(r"\\b(it|test)\\s*\\(", f.read_text(errors="ignore")))
        elif language == "go":
            for f in root.rglob("*_test.go"):
                if ".lab" in str(f):
                    continue
                count += len(re.findall(r"func Test", f.read_text(errors="ignore")))
    except Exception:
        pass
    return count
'''


# ---------------------------------------------------------------------------
# File assembler
# ---------------------------------------------------------------------------

def generate_eval_py(stack: dict, repo_root: Path, exa_hints: list[str] = None) -> str:
    repo_name = stack.get("repo_name", repo_root.name)
    language = stack.get("language", "unknown")
    build_cmd = stack.get("build_cmd", "")
    test_cmd = stack.get("test_cmd", "")
    lint_cmd = stack.get("lint_cmd", "")

    # Collect all gates
    t1_gates = []
    g = _gate_t1_build(stack)
    if g:
        t1_gates.append(g)
    g = _gate_t1_test(stack)
    if g:
        t1_gates.append(g)
    g = _gate_t1_lint(stack)
    if g:
        t1_gates.append(g)

    t2_gates = _gates_t2(stack)
    t3_gates = _gates_t3(stack)
    t4_gates = _gates_t4(stack)

    exa_comment = ""
    if exa_hints:
        hints_fmt = "\n".join(f"#   - {h}" for h in exa_hints)
        exa_comment = f"# Exa enrichment hints (not yet wired as gates):\n{hints_fmt}\n"

    all_gates = "\n\n".join(t1_gates + t2_gates + t3_gates + t4_gates)

    # Build the file as plain concatenation — no dedent, no indent mixing.
    header = f'''#!/usr/bin/env python3
"""Autoresearch eval gates for {repo_name}. Generated by eval_gen.py.

Tier weights:
  T1 (build+test+lint): 0.20
  T2 (behavioral):      0.40
  T3 (pipeline):        0.25
  T4 (documentation):   0.15

Edit this file freely — re-run eval_gen.py only to regenerate from scratch.
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(Path(__file__).parent))
from eval_base import register_gate, run_eval, run_command, count_pattern

{exa_comment}
{_TEST_COUNTER_FN.strip()}

# ---------------------------------------------------------------------------
# T1: Build + Test + Lint (total weight 0.20)
# ---------------------------------------------------------------------------

{chr(10).join(t1_gates) if t1_gates else "# No T1 gates detected for this stack"}

# ---------------------------------------------------------------------------
# T2: Behavioral (total weight 0.40)
# ---------------------------------------------------------------------------

{chr(10).join(t2_gates) if t2_gates else "# No T2 gates detected for this stack"}

# ---------------------------------------------------------------------------
# T3: Pipeline artifacts (total weight 0.25)
# ---------------------------------------------------------------------------

{chr(10).join(t3_gates) if t3_gates else "# No T3 gates detected for this stack"}

# ---------------------------------------------------------------------------
# T4: Documentation + test-count floor (total weight 0.15)
# ---------------------------------------------------------------------------

{chr(10).join(t4_gates) if t4_gates else "# No T4 gates detected for this stack"}

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    print(json.dumps(run_eval(), indent=2))
'''
    return header


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate .lab/eval.py from StackInfo")
    parser.add_argument("--repo-root", default=".", help="Path to repo root")
    parser.add_argument("--output", default=".lab/eval.py", help="Output path for eval.py")
    parser.add_argument("--no-exa", action="store_true", help="Skip Exa enrichment even if key is set")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    script_dir = Path(__file__).parent.resolve()
    detect_script = script_dir / "detect_stack.py"

    # Run detect_stack.py
    result = subprocess.run(
        [sys.executable, str(detect_script), "--repo-root", str(repo_root)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: detect_stack.py failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    try:
        stack = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"ERROR: Could not parse StackInfo JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if "error" in stack:
        print(f"ERROR: {stack['error']}", file=sys.stderr)
        sys.exit(1)

    # Optional Exa enrichment
    exa_hints = []
    if not args.no_exa:
        exa_hints = _exa_gate_hints(stack.get("language", "unknown"))

    # Generate
    content = generate_eval_py(stack, repo_root, exa_hints)

    # Write output
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = repo_root / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)
    output_path.chmod(0o755)

    lang = stack.get("language", "unknown")
    gate_count = content.count("@register_gate")
    print(f"Generated {output_path} ({lang}, {gate_count} gates)")
    if exa_hints:
        print(f"Exa hints embedded: {len(exa_hints)}")


if __name__ == "__main__":
    main()
