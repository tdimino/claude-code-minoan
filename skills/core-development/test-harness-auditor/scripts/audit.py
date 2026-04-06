#!/usr/bin/env python3
"""Test Harness Auditor — Phase 1: Read-only audit of repo feedback infrastructure.

Scans the current working directory for test, lint, type-check, static analysis,
build, and debug tooling. Produces a structured Markdown report with per-layer
scores (0-3) and prioritized recommendations.

No file writes. No installs. No commands beyond tool detection (which, command -v).
"""

import glob
import json
import os
import shutil
import sys

# ---------------------------------------------------------------------------
# Scoring: 0=absent, 1=minimal, 2=adequate, 3=excellent
# ---------------------------------------------------------------------------

SCORE_LABELS = {0: "Absent", 1: "Minimal", 2: "Adequate", 3: "Excellent"}


# ---------------------------------------------------------------------------
# Stack Detection
# ---------------------------------------------------------------------------

MANIFEST_FILES = {
    "package.json": "javascript",
    "tsconfig.json": "typescript",
    "Cargo.toml": "rust",
    "pyproject.toml": "python",
    "setup.py": "python",
    "requirements.txt": "python",
    "go.mod": "go",
    "Gemfile": "ruby",
}


def detect_stack(root: str) -> dict:
    """Detect primary stack, frameworks, and package manager."""
    stack = {"primary": "unknown", "languages": set(), "frameworks": [], "root": root}

    for manifest, lang in MANIFEST_FILES.items():
        if os.path.exists(os.path.join(root, manifest)):
            stack["languages"].add(lang)

    # Promote typescript over javascript
    if "typescript" in stack["languages"]:
        stack["primary"] = "typescript"
    elif "javascript" in stack["languages"]:
        stack["primary"] = "javascript"
    elif "rust" in stack["languages"]:
        stack["primary"] = "rust"
    elif "python" in stack["languages"]:
        stack["primary"] = "python"
    elif "go" in stack["languages"]:
        stack["primary"] = "go"
    elif "ruby" in stack["languages"]:
        stack["primary"] = "ruby"

    # Detect package manager from lockfiles
    pkg_mgr = "npm"  # default
    if os.path.exists(os.path.join(root, "bun.lockb")) or os.path.exists(os.path.join(root, "bun.lock")):
        pkg_mgr = "bun"
    elif os.path.exists(os.path.join(root, "pnpm-lock.yaml")):
        pkg_mgr = "pnpm"
    elif os.path.exists(os.path.join(root, "yarn.lock")):
        pkg_mgr = "yarn"
    stack["package_manager"] = pkg_mgr

    # Detect JS/TS frameworks from package.json
    pkg_path = os.path.join(root, "package.json")
    if os.path.exists(pkg_path):
        try:
            with open(pkg_path) as f:
                pkg = json.load(f)
            all_deps = {}
            all_deps.update(pkg.get("dependencies", {}))
            all_deps.update(pkg.get("devDependencies", {}))
            stack["_deps"] = all_deps
            stack["_scripts"] = pkg.get("scripts", {})

            for fw in ["react", "vue", "svelte", "next", "express", "fastify", "@nestjs/core"]:
                if fw in all_deps:
                    stack["frameworks"].append(fw)
        except (json.JSONDecodeError, OSError):
            stack["_deps"] = {}
            stack["_scripts"] = {}
    else:
        stack["_deps"] = {}
        stack["_scripts"] = {}

    # Detect Ruby framework
    gemfile_path = os.path.join(root, "Gemfile")
    if os.path.exists(gemfile_path):
        try:
            with open(gemfile_path) as f:
                content = f.read()
            if "rails" in content or "railties" in content:
                stack["frameworks"].append("rails")
            stack["_gemfile"] = content
        except OSError:
            stack["_gemfile"] = ""
    else:
        stack["_gemfile"] = ""

    stack["languages"] = sorted(stack["languages"])
    return stack


# ---------------------------------------------------------------------------
# Config Discovery
# ---------------------------------------------------------------------------

def discover_configs(root: str) -> dict:
    """Find existing agent and tool configs."""
    configs = {}

    checks = {
        "lint_rules_json": ".claude/lint-rules.json",
        "claude_md": "CLAUDE.md",
        "agents_md": "AGENTS.md",
        "eslintrc": None,  # special handling
        "tsconfig": "tsconfig.json",
        "clippy_toml": "clippy.toml",
        "ruff_toml": "ruff.toml",
        "mypy_ini": "mypy.ini",
        "pyrightconfig": "pyrightconfig.json",
        "golangci": ".golangci.yml",
        "rubocop": ".rubocop.yml",
    }

    for key, path in checks.items():
        if path:
            full = os.path.join(root, path)
            configs[key] = os.path.exists(full)
        else:
            configs[key] = False

    # ESLint: multiple possible filenames
    eslint_patterns = [".eslintrc", ".eslintrc.js", ".eslintrc.json", ".eslintrc.yml",
                       "eslint.config.js", "eslint.config.mjs", "eslint.config.ts"]
    for p in eslint_patterns:
        if os.path.exists(os.path.join(root, p)):
            configs["eslintrc"] = True
            break

    # CI detection
    ci_paths = [".github/workflows", ".gitlab-ci.yml", ".circleci", "Jenkinsfile"]
    configs["has_ci"] = any(
        os.path.exists(os.path.join(root, p)) for p in ci_paths
    )

    # Biome detection (ESLint alternative)
    biome_patterns = ["biome.json", "biome.jsonc"]
    for p in biome_patterns:
        if os.path.exists(os.path.join(root, p)):
            configs["biome"] = True
            break
    else:
        configs["biome"] = False

    # CLAUDE.md completeness — check for Commands section, not just existence
    claude_md_path = os.path.join(root, "CLAUDE.md")
    configs["claude_md_has_commands"] = False
    if configs["claude_md"]:
        try:
            with open(claude_md_path) as f:
                content = f.read().lower()
            cmd_markers = ["## commands", "# commands", "npm test", "cargo test", "pytest",
                           "go test", "bundle exec", "npm run", "pnpm", "bun test", "vitest"]
            configs["claude_md_has_commands"] = any(m in content for m in cmd_markers)
        except OSError:
            pass

    # Ruff in pyproject.toml (Python projects without standalone ruff.toml)
    pyproject_path = os.path.join(root, "pyproject.toml")
    if os.path.exists(pyproject_path) and not configs.get("ruff_toml"):
        try:
            with open(pyproject_path) as f:
                content = f.read()
            if "[tool.ruff]" in content:
                configs["ruff_toml"] = True  # treat as equivalent
        except OSError:
            pass

    # Hook detection
    hook_path = os.path.expanduser("~/.claude/hooks/lint-on-write.py")
    configs["lint_on_write_hook"] = os.path.exists(hook_path)

    return configs


# ---------------------------------------------------------------------------
# Six-Layer Assessment
# ---------------------------------------------------------------------------

def assess_test(stack: dict, configs: dict, root: str) -> dict:
    """Assess test suite layer."""
    findings = []
    score = 0

    primary = stack["primary"]
    deps = stack.get("_deps", {})
    scripts = stack.get("_scripts", {})

    # Check for test framework
    test_framework = None
    test_cmd = None

    if primary in ("javascript", "typescript"):
        pkg_mgr = stack.get("package_manager", "npm")
        run_prefix = f"{pkg_mgr} run" if pkg_mgr != "bun" else "bun"
        for fw in ["vitest", "jest", "mocha", "ava", "@playwright/test"]:
            if fw in deps:
                test_framework = fw
                break
        if "test" in scripts:
            test_cmd = f"{run_prefix} test"
            score = max(score, 1)

    elif primary == "rust":
        # Rust has built-in test framework — scan all .rs files (workspace crates too)
        test_files = glob.glob(os.path.join(root, "**/*.rs"), recursive=True)
        test_files = [f for f in test_files if "/target/" not in f and "/.git/" not in f]
        has_tests = False
        for tf in test_files[:50]:
            try:
                with open(tf) as f:
                    content = f.read()
                if "#[test]" in content or "#[cfg(test)]" in content:
                    has_tests = True
                    break
            except OSError:
                pass
        if has_tests:
            test_framework = "cargo test"
            test_cmd = "cargo test"
            score = max(score, 1)

    elif primary == "python":
        # Check pyproject.toml deps in addition to package.json deps
        py_deps = set(deps.keys())
        pyproject_path = os.path.join(root, "pyproject.toml")
        if os.path.exists(pyproject_path):
            try:
                with open(pyproject_path) as f:
                    pyproject_content = f.read()
                # Simple detection: look for pytest/ruff/mypy in dep sections
                for tool in ["pytest", "ruff", "mypy", "pyright", "bandit", "mutmut"]:
                    if tool in pyproject_content:
                        py_deps.add(tool)
            except OSError:
                pass
        if "pytest" in py_deps or os.path.exists(os.path.join(root, "tests")) or os.path.exists(os.path.join(root, "test")):
            test_framework = "pytest"
            test_cmd = "pytest"
            score = max(score, 1)

    elif primary == "go":
        test_files = glob.glob(os.path.join(root, "**/*_test.go"), recursive=True)
        if test_files:
            test_framework = "go test"
            test_cmd = "go test ./..."
            score = max(score, 1)

    elif primary == "ruby":
        gemfile = stack.get("_gemfile", "")
        if "rspec" in gemfile or os.path.exists(os.path.join(root, "spec")):
            test_framework = "rspec"
            test_cmd = "bundle exec rspec"
            score = max(score, 1)
        elif os.path.exists(os.path.join(root, "test")):
            test_framework = "minitest"
            test_cmd = "bundle exec rails test" if "rails" in stack["frameworks"] else "ruby -Itest test/"
            score = max(score, 1)

    if test_framework:
        findings.append(f"Test framework: {test_framework}")
        # Only score 2 if we also have a runnable test command
        if test_cmd:
            score = max(score, 2)
        else:
            score = max(score, 1)
    else:
        findings.append("No test framework detected")

    if test_cmd:
        findings.append(f"Test command: `{test_cmd}`")

    # Check for mutation testing
    mutation_tools = {
        "javascript": "@stryker-mutator/core",
        "typescript": "@stryker-mutator/core",
        "rust": "cargo-mutants",
        "python": "mutmut",
        "go": "go-mutesting",
        "ruby": "mutant",
    }
    mut_tool = mutation_tools.get(primary, "")
    has_mutation = False
    if mut_tool:
        if primary in ("javascript", "typescript") and mut_tool in deps:
            has_mutation = True
        elif primary == "ruby" and mut_tool in stack.get("_gemfile", ""):
            has_mutation = True
        elif shutil.which(mut_tool):
            has_mutation = True

    if has_mutation:
        findings.append(f"Mutation testing: {mut_tool}")
        score = 3
    else:
        findings.append(f"No mutation testing ({mut_tool} not found)")

    return {"score": score, "findings": findings, "test_cmd": test_cmd, "framework": test_framework}


def assess_lint(stack: dict, configs: dict, root: str) -> dict:
    """Assess linting layer."""
    findings = []
    score = 0
    primary = stack["primary"]

    linter = None
    if primary in ("javascript", "typescript") and (configs.get("eslintrc") or configs.get("biome")):
        linter = "biome" if configs.get("biome") and not configs.get("eslintrc") else "eslint"
        score = max(score, 2)
    elif primary == "rust":
        if shutil.which("cargo"):
            linter = "clippy"
            score = max(score, 2)
    elif primary == "python":
        if configs.get("ruff_toml") or shutil.which("ruff"):
            linter = "ruff"
            score = max(score, 2)
        elif shutil.which("flake8"):
            linter = "flake8"
            score = max(score, 1)
    elif primary == "go":
        if configs.get("golangci") or shutil.which("golangci-lint"):
            linter = "golangci-lint"
            score = max(score, 2)
    elif primary == "ruby":
        if configs.get("rubocop"):
            linter = "rubocop"
            score = max(score, 2)

    if linter:
        findings.append(f"Standard linter: {linter}")
    else:
        findings.append("No standard linter detected")

    # Custom agent rules
    if configs.get("lint_rules_json"):
        findings.append("Custom agent lint rules: .claude/lint-rules.json present")
        score = min(score + 1, 3)
    else:
        findings.append("No custom agent lint rules (.claude/lint-rules.json)")

    # Lint-on-write hook
    if configs.get("lint_on_write_hook"):
        findings.append("Lint-on-write hook: active")
    else:
        findings.append("Lint-on-write hook: not found")

    return {"score": score, "findings": findings, "linter": linter}


def assess_typecheck(stack: dict, configs: dict, root: str) -> dict:
    """Assess type checking layer."""
    findings = []
    score = 0
    primary = stack["primary"]

    if primary in ("javascript", "typescript"):
        if configs.get("tsconfig"):
            findings.append("TypeScript: tsconfig.json present")
            score = max(score, 2)

            # Check strict mode
            try:
                with open(os.path.join(root, "tsconfig.json")) as f:
                    ts_config = json.load(f)
                strict = ts_config.get("compilerOptions", {}).get("strict", False)
                if strict:
                    findings.append("Strict mode: enabled")
                    score = 3
                else:
                    findings.append("Strict mode: disabled")
            except (json.JSONDecodeError, OSError):
                findings.append("Strict mode: could not parse tsconfig.json")
        else:
            findings.append("No TypeScript configuration")

    elif primary == "rust":
        # Rust is always strongly typed
        findings.append("Rust: strong static typing built-in")
        score = 3

    elif primary == "python":
        if configs.get("mypy_ini") or configs.get("pyrightconfig"):
            checker = "mypy" if configs.get("mypy_ini") else "pyright"
            findings.append(f"Type checker: {checker}")
            score = max(score, 2)

            # Check mypy strict
            mypy_path = os.path.join(root, "mypy.ini")
            if os.path.exists(mypy_path):
                try:
                    with open(mypy_path) as f:
                        content = f.read()
                    if "strict = True" in content or "strict = true" in content:
                        findings.append("Strict mode: enabled")
                        score = 3
                except OSError:
                    pass
            # Also check pyproject.toml for mypy config
            pyproject = os.path.join(root, "pyproject.toml")
            if os.path.exists(pyproject):
                try:
                    with open(pyproject) as f:
                        content = f.read()
                    if "[tool.mypy]" in content and "strict = true" in content.lower():
                        findings.append("Strict mode: enabled (pyproject.toml)")
                        score = 3
                except OSError:
                    pass
        else:
            findings.append("No type checker configured")

    elif primary == "go":
        findings.append("Go: strong static typing built-in")
        score = 3

    elif primary == "ruby":
        if os.path.exists(os.path.join(root, "sorbet")):
            findings.append("Type checker: Sorbet")
            score = max(score, 2)
        else:
            findings.append("No type checker (Sorbet not found)")

    return {"score": score, "findings": findings}


def assess_static_analysis(stack: dict, configs: dict, root: str) -> dict:
    """Assess static analysis / security scanning layer."""
    findings = []
    score = 0
    primary = stack["primary"]

    # Security scanners
    scanners = {
        "javascript": [("npm", "npm audit")],
        "typescript": [("npm", "npm audit")],
        "rust": [("cargo-audit", "cargo audit")],
        "python": [("bandit", "bandit -r ."), ("safety", "safety check")],
        "go": [("govulncheck", "govulncheck ./...")],
        "ruby": [("bundler-audit", "bundler-audit"), ("brakeman", "brakeman")],
    }

    found_scanners = []
    for tool_name, cmd in scanners.get(primary, []):
        if shutil.which(tool_name) or (tool_name == "npm" and shutil.which("npm")):
            found_scanners.append(cmd)
            score = max(score, 1)

    if found_scanners:
        findings.append(f"Security scanners: {', '.join(found_scanners)}")
        score = max(score, 2)
    else:
        findings.append("No security scanner available")

    # Dependency audit in CI
    if configs.get("has_ci"):
        findings.append("CI pipeline detected — check for security scan step")
        score = max(score, 1)

    return {"score": score, "findings": findings}


def assess_build(stack: dict, configs: dict, root: str) -> dict:
    """Assess build/compilation layer."""
    findings = []
    score = 0
    primary = stack["primary"]
    scripts = stack.get("_scripts", {})

    if primary in ("javascript", "typescript"):
        pkg_mgr = stack.get("package_manager", "npm")
        run_prefix = f"{pkg_mgr} run" if pkg_mgr != "bun" else "bun"
        if "build" in scripts:
            findings.append(f"Build command: `{run_prefix} build`")
            score = max(score, 2)
        elif configs.get("tsconfig"):
            npx = "bunx" if pkg_mgr == "bun" else "npx"
            findings.append(f"Build command: `{npx} tsc --noEmit` (type check only)")
            score = max(score, 1)
        else:
            findings.append("No build command in package.json scripts")

    elif primary == "rust":
        findings.append("Build command: `cargo build`")
        score = max(score, 2)
        # Check for workspace
        cargo_path = os.path.join(root, "Cargo.toml")
        if os.path.exists(cargo_path):
            try:
                with open(cargo_path) as f:
                    if "[workspace]" in f.read():
                        findings.append("Cargo workspace detected")
                        score = 3
            except OSError:
                pass

    elif primary == "python":
        pyproject = os.path.join(root, "pyproject.toml")
        if os.path.exists(pyproject):
            try:
                with open(pyproject) as f:
                    if "build-system" in f.read():
                        findings.append("Build system configured in pyproject.toml")
                        score = max(score, 2)
            except OSError:
                pass
        else:
            findings.append("No build system (interpreted language)")
            score = max(score, 1)

    elif primary == "go":
        findings.append("Build command: `go build ./...`")
        score = max(score, 2)

    elif primary == "ruby":
        if os.path.exists(os.path.join(root, "Rakefile")):
            findings.append("Build: Rakefile present")
            score = max(score, 1)
        else:
            findings.append("No build system (interpreted language)")
            score = max(score, 1)

    # CI build validation
    if configs.get("has_ci"):
        findings.append("CI present — verify build step is included")

    return {"score": score, "findings": findings}


def assess_debug(stack: dict, configs: dict, root: str) -> dict:
    """Assess debugger/REPL access layer."""
    findings = []
    score = 0
    primary = stack["primary"]

    debug_tools = {
        "javascript": [("node", "node --inspect")],
        "typescript": [("node", "node --inspect"), ("tsx", "tsx --inspect")],
        "rust": [("rust-gdb", "rust-gdb"), ("lldb", "lldb")],
        "python": [("python3", "python3 -m pdb"), ("ipdb", "ipdb")],
        "go": [("dlv", "dlv debug")],
        "ruby": [("irb", "irb"), ("pry", "pry")],
    }

    available = []
    for tool_name, cmd in debug_tools.get(primary, []):
        if shutil.which(tool_name):
            available.append(cmd)

    if available:
        findings.append(f"Debug tools: {', '.join(available)}")
        score = max(score, 2)
    else:
        findings.append("No debugger/REPL detected")

    # REPL available?
    repls = {"python": "python3", "ruby": "irb", "javascript": "node", "typescript": "node"}
    repl = repls.get(primary)
    if repl and shutil.which(repl):
        findings.append(f"REPL: {repl}")
        score = max(score, 2)

    return {"score": score, "findings": findings}


# ---------------------------------------------------------------------------
# Debugging Residue File Scan
# ---------------------------------------------------------------------------

RESIDUE_PATTERNS = [
    "*_v2.*", "*_v3.*", "*_backup.*", "*_fixed.*", "*_old.*",
    "*_new.*", "*_copy.*", "*_temp.*", "*.bak", "*.orig",
]


def compute_drift(current: dict, previous: dict) -> dict | None:
    """Compare current audit snapshot against a previous one. Returns drift report or None."""
    drift = {"score_changes": [], "config_changes": [], "residue_changes": [], "has_regressions": False}

    # Score changes per layer
    for layer in ("test", "lint", "typecheck", "static_analysis", "build", "debug"):
        cur_score = current.get("scores", {}).get(layer, {}).get("score", 0)
        prev_score = previous.get("scores", {}).get(layer, {}).get("score", 0)
        if cur_score != prev_score:
            delta = cur_score - prev_score
            direction = "improved" if delta > 0 else "regressed"
            drift["score_changes"].append({
                "layer": layer, "previous": prev_score, "current": cur_score,
                "delta": delta, "direction": direction,
            })
            if delta < 0:
                drift["has_regressions"] = True

    # Total score change
    cur_total = current.get("total_score", 0)
    prev_total = previous.get("total_score", 0)
    drift["total_previous"] = prev_total
    drift["total_current"] = cur_total
    drift["total_delta"] = cur_total - prev_total

    # Config changes
    cur_configs = current.get("configs", {})
    prev_configs = previous.get("configs", {})
    all_keys = sorted(set(list(cur_configs.keys()) + list(prev_configs.keys())))
    for key in all_keys:
        cur_val = cur_configs.get(key, False)
        prev_val = prev_configs.get(key, False)
        if cur_val != prev_val:
            drift["config_changes"].append({
                "config": key,
                "previous": prev_val,
                "current": cur_val,
                "direction": "added" if cur_val and not prev_val else "removed",
            })

    # Residue file changes
    cur_residue = set(current.get("residue", []))
    prev_residue = set(previous.get("residue", []))
    new_residue = sorted(cur_residue - prev_residue)
    removed_residue = sorted(prev_residue - cur_residue)
    if new_residue:
        drift["residue_changes"].append({"type": "new", "files": new_residue})
    if removed_residue:
        drift["residue_changes"].append({"type": "cleaned", "files": removed_residue})

    # Only return drift if something actually changed
    if drift["score_changes"] or drift["config_changes"] or drift["residue_changes"]:
        return drift
    return None


def format_drift_report(drift: dict) -> str:
    """Format drift report as Markdown."""
    lines = ["## Audit Drift (vs. previous snapshot)", ""]

    # Total score
    delta = drift["total_delta"]
    arrow = "+" if delta > 0 else ""
    lines.append(f"**Total score**: {drift['total_previous']}/18 → {drift['total_current']}/18 ({arrow}{delta})")
    if drift["has_regressions"]:
        lines.append("**⚠ Regressions detected**")
    lines.append("")

    # Per-layer changes
    if drift["score_changes"]:
        lines.append("### Score Changes")
        lines.append("| Layer | Previous | Current | Delta |")
        lines.append("|-------|----------|---------|-------|")
        for sc in drift["score_changes"]:
            d = sc["delta"]
            indicator = f"+{d}" if d > 0 else str(d)
            lines.append(f"| {sc['layer']} | {sc['previous']}/3 | {sc['current']}/3 | {indicator} |")
        lines.append("")

    # Config changes
    if drift["config_changes"]:
        lines.append("### Configuration Changes")
        for cc in drift["config_changes"]:
            direction = "added" if cc["direction"] == "added" else "removed"
            lines.append(f"- `{cc['config']}`: {direction}")
        lines.append("")

    # Residue changes
    if drift["residue_changes"]:
        lines.append("### Residue File Changes")
        for rc in drift["residue_changes"]:
            label = "New residue" if rc["type"] == "new" else "Cleaned up"
            for f in rc["files"]:
                lines.append(f"- {label}: `{f}`")
        lines.append("")

    return "\n".join(lines)


def scan_residue_files(root: str) -> list[str]:
    """Find debugging residue files in the repo."""
    residue = []
    for pattern in RESIDUE_PATTERNS:
        matches = glob.glob(os.path.join(root, "**", pattern), recursive=True)
        for m in matches:
            rel = os.path.relpath(m, root)
            if not any(skip in rel for skip in ["node_modules/", ".git/", "target/", "__pycache__/"]):
                residue.append(rel)
    return sorted(set(residue))[:20]  # cap at 20


# ---------------------------------------------------------------------------
# Gap Analysis
# ---------------------------------------------------------------------------

def gap_analysis(scores: dict, stack: dict, configs: dict) -> list[dict]:
    """Produce prioritized recommendations sorted by impact on agent feedback quality."""
    recs = []

    # Priority 1: Test suite (highest impact on agent feedback)
    if scores["test"]["score"] < 2:
        recs.append({
            "priority": "P0",
            "layer": "Test",
            "action": "Configure test runner and add test command to CLAUDE.md",
            "impact": "Agent cannot validate its own changes without tests",
        })
    elif scores["test"]["score"] < 3:
        recs.append({
            "priority": "P2",
            "layer": "Test",
            "action": "Add mutation testing for test quality validation",
            "impact": "Tests exist but may have dead-weight assertions",
        })

    # Priority 1: Linting
    if scores["lint"]["score"] == 0:
        recs.append({
            "priority": "P0",
            "layer": "Lint",
            "action": "Install and configure standard linter for the stack",
            "impact": "Agent has no style or correctness feedback",
        })
    if not configs.get("lint_rules_json"):
        recs.append({
            "priority": "P1",
            "layer": "Lint",
            "action": "Generate .claude/lint-rules.json with agent-specific rules",
            "impact": "No custom rules catching AI anti-patterns (debugging residue, security, architecture)",
        })

    # Priority 2: Type checking
    if scores["typecheck"]["score"] == 0:
        lang = stack["primary"]
        if lang in ("javascript", "typescript", "python"):
            recs.append({
                "priority": "P1",
                "layer": "Type",
                "action": "Enable type checking (TypeScript strict mode / mypy / pyright)",
                "impact": "Hallucinated imports and type errors not caught until runtime",
            })

    # Priority 2: Static analysis
    if scores["static_analysis"]["score"] == 0:
        recs.append({
            "priority": "P2",
            "layer": "SA",
            "action": "Add security scanner (npm-audit / cargo-audit / bandit / govulncheck)",
            "impact": "Dependency vulnerabilities not detected",
        })

    # Priority 3: Build
    if scores["build"]["score"] == 0:
        recs.append({
            "priority": "P2",
            "layer": "Build",
            "action": "Configure build command",
            "impact": "No compilation validation before commit",
        })

    # Priority 3: Debug
    if scores["debug"]["score"] == 0:
        recs.append({
            "priority": "P3",
            "layer": "Debug",
            "action": "Install debugger or REPL for the stack",
            "impact": "Agent cannot inspect runtime state",
        })

    # CLAUDE.md completeness
    if not configs.get("claude_md"):
        recs.append({
            "priority": "P1",
            "layer": "Config",
            "action": "Create CLAUDE.md with test, lint, type-check, and build commands",
            "impact": "Agent has no project-specific instructions",
        })
    elif not configs.get("claude_md_has_commands"):
        recs.append({
            "priority": "P1",
            "layer": "Config",
            "action": "Add Commands section to CLAUDE.md with test, lint, and build commands",
            "impact": "CLAUDE.md exists but has no runnable commands — agent cannot self-correct",
        })

    # agnix: validate agent config files (complementary to our infrastructure audit)
    if configs.get("claude_md") or configs.get("agents_md"):
        recs.append({
            "priority": "P3",
            "layer": "Config",
            "action": "Run agnix to validate agent configuration files (385 rules for CLAUDE.md/AGENTS.md/SKILL.md)",
            "impact": "Catches stale paths, dead commands, and context rot in agent configs",
        })

    return sorted(recs, key=lambda r: r["priority"])


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_report(stack: dict, configs: dict, scores: dict, recs: list, residue: list) -> str:
    """Generate structured Markdown audit report."""
    lines = ["# Test Harness Audit Report", ""]

    # Stack Summary
    lines.append("## Stack Summary")
    lines.append(f"- **Primary**: {stack['primary']}")
    lines.append(f"- **Languages**: {', '.join(stack['languages']) if stack['languages'] else 'unknown'}")
    if stack["frameworks"]:
        lines.append(f"- **Frameworks**: {', '.join(stack['frameworks'])}")
    if stack.get("package_manager") and stack["primary"] in ("javascript", "typescript"):
        lines.append(f"- **Package manager**: {stack['package_manager']}")
    lines.append("")

    # Scorecard
    lines.append("## Scorecard")
    lines.append("")
    lines.append("| Layer | Score | Status |")
    lines.append("|-------|-------|--------|")
    total = 0
    for layer_key, label in [
        ("test", "Test Suite"),
        ("lint", "Linting"),
        ("typecheck", "Type Checking"),
        ("static_analysis", "Static Analysis"),
        ("build", "Build/Compile"),
        ("debug", "Debugger/REPL"),
    ]:
        s = scores[layer_key]["score"]
        total += s
        lines.append(f"| {label} | {s}/3 | {SCORE_LABELS[s]} |")
    lines.append(f"| **Total** | **{total}/18** | |")
    lines.append("")

    # Per-layer Findings
    lines.append("## Findings")
    lines.append("")
    for layer_key, label in [
        ("test", "Test Suite"),
        ("lint", "Linting"),
        ("typecheck", "Type Checking"),
        ("static_analysis", "Static Analysis"),
        ("build", "Build/Compile"),
        ("debug", "Debugger/REPL"),
    ]:
        lines.append(f"### {label} ({scores[layer_key]['score']}/3)")
        for f in scores[layer_key]["findings"]:
            lines.append(f"- {f}")
        lines.append("")

    # Existing Configs
    lines.append("## Existing Configuration")
    config_items = [
        ("lint_rules_json", ".claude/lint-rules.json"),
        ("claude_md", "CLAUDE.md"),
        ("agents_md", "AGENTS.md"),
        ("eslintrc", "ESLint config"),
        ("tsconfig", "tsconfig.json"),
        ("rubocop", ".rubocop.yml"),
        ("ruff_toml", "ruff.toml"),
        ("golangci", ".golangci.yml"),
        ("has_ci", "CI pipeline"),
        ("lint_on_write_hook", "lint-on-write hook"),
    ]
    for key, label in config_items:
        status = "present" if configs.get(key) else "not found"
        lines.append(f"- {label}: {status}")
    lines.append("")

    # Debugging Residue
    if residue:
        lines.append("## Debugging Residue Files")
        lines.append(f"Found {len(residue)} potential residue files:")
        for r in residue:
            lines.append(f"- `{r}`")
        lines.append("")

    # Recommendations
    lines.append("## Recommendations")
    lines.append("")
    if recs:
        lines.append("| Priority | Layer | Action | Impact |")
        lines.append("|----------|-------|--------|--------|")
        for r in recs:
            lines.append(f"| {r['priority']} | {r['layer']} | {r['action']} | {r['impact']} |")
    else:
        lines.append("No recommendations — all layers are well-configured.")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

SNAPSHOT_FILENAME = ".claude/audit-snapshot.json"


def load_snapshot(root: str) -> dict | None:
    """Load previous audit snapshot if it exists."""
    path = os.path.join(root, SNAPSHOT_FILENAME)
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
    return None


def save_snapshot(root: str, data: dict) -> str:
    """Write audit snapshot to .claude/audit-snapshot.json. Returns the path."""
    path = os.path.join(root, SNAPSHOT_FILENAME)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    return path


def main():
    root = os.getcwd()
    json_mode = "--json" in sys.argv
    save_mode = "--save" in sys.argv

    # Allow passing a directory as argument
    args = [a for a in sys.argv[1:] if a not in ("--json", "--save")]
    if args and os.path.isdir(args[0]):
        root = os.path.abspath(args[0])

    # Phase 1: Detect
    stack = detect_stack(root)
    configs = discover_configs(root)

    # Phase 2: Assess each layer
    scores = {
        "test": assess_test(stack, configs, root),
        "lint": assess_lint(stack, configs, root),
        "typecheck": assess_typecheck(stack, configs, root),
        "static_analysis": assess_static_analysis(stack, configs, root),
        "build": assess_build(stack, configs, root),
        "debug": assess_debug(stack, configs, root),
    }

    # Phase 3: Scan for residue
    residue = scan_residue_files(root)

    # Phase 4: Gap analysis
    recs = gap_analysis(scores, stack, configs)

    # Build canonical data dict (used by both JSON and save modes)
    data = {
        "root": root,
        "stack": {
            "primary": stack["primary"],
            "languages": stack["languages"],
            "frameworks": stack["frameworks"],
            "package_manager": stack.get("package_manager", "npm"),
            "scripts": stack.get("_scripts", {}),
            "deps": {k: str(v) for k, v in stack.get("_deps", {}).items()},
        },
        "configs": configs,
        "scores": {
            layer: {"score": layer_data["score"], "findings": layer_data["findings"]}
            for layer, layer_data in scores.items()
        },
        "residue": residue,
        "recommendations": recs,
        "total_score": sum(s["score"] for s in scores.values()),
    }
    # Add test/lint details for generate.py consumption
    if scores["test"].get("test_cmd"):
        data["stack"]["test_cmd"] = scores["test"]["test_cmd"]
    if scores["test"].get("framework"):
        data["stack"]["test_framework"] = scores["test"]["framework"]
    if scores["lint"].get("linter"):
        data["stack"]["linter"] = scores["lint"]["linter"]

    # Drift detection: compare against previous snapshot
    drift = None
    had_previous = False
    if save_mode:
        previous = load_snapshot(root)
        had_previous = previous is not None
        if previous:
            drift = compute_drift(data, previous)
        snapshot_path = save_snapshot(root, data)

    if json_mode:
        # Machine-readable output for generate.py --audit
        if drift:
            data["drift"] = drift
        if save_mode:
            data["snapshot_path"] = snapshot_path
        print(json.dumps(data, indent=2))
    else:
        # Phase 5: Generate Markdown report
        report = generate_report(stack, configs, scores, recs, residue)
        if drift:
            report += "\n" + format_drift_report(drift)
        elif save_mode and not had_previous:
            report += "\n## Audit Drift\n\nFirst snapshot saved — no previous data to compare against.\n"
            report += f"Snapshot: `{snapshot_path}`\n"
        elif save_mode and had_previous:
            report += "\n## Audit Drift\n\nNo changes since previous snapshot.\n"
            report += f"Snapshot: `{snapshot_path}`\n"
        print(report)


if __name__ == "__main__":
    main()
