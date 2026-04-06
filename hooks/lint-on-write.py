#!/usr/bin/env python3
"""PostToolUse hook: run linters after Write/Edit and feed violations back.

Matcher: Write, Edit
Auto-discovers .claude/lint-rules.json at the project root, dispatches to the
configured linter (ESLint/Clippy/Ruff), and runs custom grep-based convention
rules from the config. Any repo can opt in by dropping a config file.

Inspired by Factory.ai's "Using Linters to Direct Agents" (Sep 2025) and
"Lint Against the Machine" (Mar 2026). Agents self-correct faster against
lint output than prose instructions.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time

# --- Configuration ---

COOLDOWN_FILE = "/tmp/lint-on-write-cooldown.json"
COOLDOWN_SECONDS = 5.0
PRUNE_AGE_SECONDS = 60.0
MAX_VIOLATIONS = 10
SUBPROCESS_TIMEOUT = 8  # seconds (clippy needs ~3-5s with incremental cache)

CONFIG_FILENAME = ".claude/lint-rules.json"

# Legacy fallback script (used when no .claude/lint-rules.json exists)
CUSTOM_LINT_SCRIPT = os.path.join(os.path.dirname(__file__), "custom-lint.sh")

# File extensions to skip entirely (no linting value)
SKIP_EXTENSIONS = {
    ".md", ".json", ".yaml", ".yml", ".toml", ".html", ".svg", ".png",
    ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".ttf", ".eot",
    ".map", ".lock", ".env", ".gitignore", ".prettierrc",
}

# Default extension → linter mapping (used when no config file exists)
DEFAULT_LINTERS = {
    ".ts": "eslint",
    ".tsx": "eslint",
    ".js": "eslint",
    ".jsx": "eslint",
    ".mjs": "eslint",
    ".rs": "clippy",
    ".py": "ruff",
}


# --- Config Discovery ---

def find_config(file_path: str) -> tuple[dict | None, str | None]:
    """Walk up from file_path looking for .claude/lint-rules.json.

    Returns (config_dict, project_root) or (None, None).
    """
    current = os.path.dirname(os.path.abspath(file_path))

    for _ in range(20):
        config_path = os.path.join(current, CONFIG_FILENAME)
        if os.path.isfile(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                return config, current
            except (json.JSONDecodeError, OSError):
                return None, None

        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    return None, None


# --- Cooldown ---

def check_cooldown(file_path: str) -> bool:
    """Return True if file should be linted (not in cooldown)."""
    now = time.time()
    cooldowns = {}

    try:
        with open(COOLDOWN_FILE, "r") as f:
            cooldowns = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass

    cooldowns = {k: v for k, v in cooldowns.items() if now - v < PRUNE_AGE_SECONDS}

    last_lint = cooldowns.get(file_path, 0)
    if now - last_lint < COOLDOWN_SECONDS:
        return False

    cooldowns[file_path] = now
    try:
        tmp = COOLDOWN_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(cooldowns, f)
        os.replace(tmp, COOLDOWN_FILE)
    except OSError:
        pass

    return True


# --- Standard Linter Runners ---

def run_eslint(file_path: str, project_root: str) -> list[str]:
    """Run ESLint on a single file and return violation strings."""
    violations = []
    try:
        result = subprocess.run(
            ["npx", "eslint", "--no-warn-ignored", "--format", "json", file_path],
            capture_output=True, text=True,
            timeout=SUBPROCESS_TIMEOUT, cwd=project_root,
        )
        if result.stdout:
            data = json.loads(result.stdout)
            for file_result in data:
                for msg in file_result.get("messages", []):
                    severity = "error" if msg.get("severity", 0) == 2 else "warn"
                    rule = msg.get("ruleId", "unknown")
                    message = msg.get("message", "")
                    line = msg.get("line", 0)
                    violations.append(
                        f"[eslint/{severity}] {rule}: {message} (line {line})"
                    )
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return violations


def find_crate_name(file_path: str) -> str | None:
    """For Rust files, find the crate name by walking up to nearest Cargo.toml."""
    current = os.path.dirname(os.path.abspath(file_path))
    for _ in range(10):
        cargo_path = os.path.join(current, "Cargo.toml")
        if os.path.exists(cargo_path):
            try:
                with open(cargo_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("name"):
                            parts = line.split("=", 1)
                            if len(parts) == 2:
                                return parts[1].strip().strip('"').strip("'")
            except OSError:
                pass
            return None
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def find_workspace_root(file_path: str) -> str | None:
    """For Rust files, find the workspace root (has [workspace] in Cargo.toml)."""
    current = os.path.dirname(os.path.abspath(file_path))
    for _ in range(10):
        cargo_path = os.path.join(current, "Cargo.toml")
        if os.path.exists(cargo_path):
            try:
                with open(cargo_path, "r") as f:
                    if "[workspace]" in f.read():
                        return current
            except OSError:
                pass
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def run_clippy(file_path: str, project_root: str, linter_options: dict | None = None) -> list[str]:
    """Run Clippy on the crate containing file_path, filter to that file."""
    violations = []
    crate_name = find_crate_name(file_path)
    workspace_root = find_workspace_root(file_path)
    if not crate_name or not workspace_root:
        return violations

    env = os.environ.copy()
    path_prefix = (linter_options or {}).get("path_prefix", "/usr/bin")
    if path_prefix:
        env["PATH"] = path_prefix + ":" + env.get("PATH", "")

    try:
        result = subprocess.run(
            ["cargo", "clippy", "-p", crate_name, "--message-format=json", "--quiet"],
            capture_output=True, text=True,
            timeout=SUBPROCESS_TIMEOUT, cwd=workspace_root, env=env,
        )
        abs_file = os.path.abspath(file_path)
        for line in result.stdout.splitlines():
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if msg.get("reason") != "compiler-message":
                continue
            compiler_msg = msg.get("message", {})
            level = compiler_msg.get("level", "")
            if level not in ("warning", "error"):
                continue
            for span in compiler_msg.get("spans", []):
                span_abs = os.path.join(workspace_root, span.get("file_name", ""))
                if os.path.abspath(span_abs) == abs_file:
                    text = compiler_msg.get("message", "")
                    code = compiler_msg.get("code", {})
                    rule = code.get("code", "") if code else ""
                    line_num = span.get("line_start", 0)
                    prefix = rule if rule else "clippy"
                    violations.append(f"[{prefix}] {text} (line {line_num})")
                    break
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return violations


def run_ruff(file_path: str) -> list[str]:
    """Run Ruff on a single file, if available."""
    violations = []
    if not shutil.which("ruff"):
        return violations
    try:
        result = subprocess.run(
            ["ruff", "check", file_path, "--output-format", "json"],
            capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
        )
        if result.stdout:
            data = json.loads(result.stdout)
            for msg in data:
                code = msg.get("code", "unknown")
                message = msg.get("message", "")
                line = msg.get("location", {}).get("row", 0)
                violations.append(f"[ruff] {code}: {message} (line {line})")
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return violations


# --- Config-Driven Custom Rules ---

def run_custom_rules(file_path: str, rules: list[dict]) -> list[str]:
    """Run grep-based custom rules from .claude/lint-rules.json against a file."""
    violations = []
    _, ext = os.path.splitext(file_path)
    ext_bare = ext.lstrip(".").lower()
    abs_path = os.path.abspath(file_path)

    for rule in rules:
        # Check extension filter
        extensions = rule.get("extensions", [])
        if extensions and ext_bare not in extensions:
            continue

        # Check path exclusion
        exclude_paths = rule.get("exclude_paths", [])
        skip = False
        for ep in exclude_paths:
            # Support simple glob patterns like "*/dat/*"
            if _path_matches(abs_path, ep):
                skip = True
                break
        if skip:
            continue

        pattern = rule.get("pattern", "")
        message = rule.get("message", "Custom lint violation")
        exclude_patterns = rule.get("exclude_patterns", [])
        require_absent = rule.get("require_absent")

        if not pattern:
            continue

        # require_absent: only fire if this pattern is NOT in the file
        if require_absent:
            try:
                with open(file_path, "r", errors="replace") as f:
                    content = f.read()
                if require_absent in content:
                    continue
            except OSError:
                continue

        # Run grep
        try:
            result = subprocess.run(
                ["grep", "-En", pattern, file_path],
                capture_output=True, text=True, timeout=3,
            )
            for line in result.stdout.strip().splitlines():
                if not line.strip():
                    continue

                # Apply exclude_patterns
                excluded = False
                for ep in exclude_patterns:
                    if re.search(ep, line):
                        excluded = True
                        break
                if excluded:
                    continue

                # Extract line number
                colon_idx = line.find(":")
                if colon_idx > 0:
                    line_num = line[:colon_idx]
                    violations.append(f"{line_num}: [custom] {message}")
                else:
                    violations.append(f"[custom] {message}")

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

    return violations


def _path_matches(path: str, glob_pattern: str) -> bool:
    """Simple glob match: supports * as wildcard segment."""
    # Convert glob to regex: * matches anything except /
    # */ matches any directory segment
    regex = glob_pattern.replace("*", "[^/]*")
    # But */ at start means any prefix
    if glob_pattern.startswith("*/"):
        regex = ".*/" + regex[len("[^/]*/"):]
    return bool(re.search(regex, path))


# --- Legacy Fallback ---

def run_legacy_custom_lint(file_path: str, project_name: str) -> list[str]:
    """Run legacy custom-lint.sh for projects without .claude/lint-rules.json."""
    violations = []
    if not os.path.exists(CUSTOM_LINT_SCRIPT):
        return violations
    try:
        result = subprocess.run(
            ["bash", CUSTOM_LINT_SCRIPT, file_path, project_name],
            capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
        )
        for line in result.stdout.strip().splitlines():
            if line.strip():
                violations.append(line.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return violations


# --- Output ---

# Severity tiers for custom rule categories (extracted from [category] prefix).
# Tier 1 = fix first (blocking), Tier 2 = fix next, Tier 3 = when convenient.
# Based on CodeRabbit data: I/O perf issues 8x, security 2.74x more in AI PRs.
SEVERITY_TIERS = {
    1: {"security", "error-boundary"},
    2: {"observability", "debugging-residue", "async-misuse"},
    3: {"architecture", "testability", "grep-ability", "convention"},
}
_CATEGORY_TO_TIER = {}
for _tier, _cats in SEVERITY_TIERS.items():
    for _cat in _cats:
        _CATEGORY_TO_TIER[_cat] = _tier
TIER_LABELS = {1: "BLOCKING", 2: "HIGH", 3: "MEDIUM"}


def _extract_category(violation: str) -> str:
    """Extract [category] from a violation message like '42: [custom] [security] ...'"""
    m = re.search(r"\[([a-z][\w-]*)\]", violation)
    return m.group(1) if m else ""


def format_output(file_path: str, violations: list[str]) -> str:
    """Format violations into additionalContext string, grouped by severity tier."""
    basename = os.path.basename(file_path)
    total = len(violations)
    shown = violations[:MAX_VIOLATIONS]

    # Group by severity tier
    tiered: dict[int, list[str]] = {1: [], 2: [], 3: [], 4: []}
    for v in shown:
        cat = _extract_category(v)
        tier = _CATEGORY_TO_TIER.get(cat, 4)
        tiered[tier].append(v)

    # If all violations are in the same tier (or no categories), skip tier headers
    non_empty_tiers = [t for t in tiered if tiered[t]]
    use_tiers = len(non_empty_tiers) > 1

    lines = [f"Lint violations in {basename} ({total} issues):"]

    if use_tiers:
        idx = 1
        for tier in [1, 2, 3, 4]:
            if not tiered[tier]:
                continue
            label = TIER_LABELS.get(tier, "LOW")
            lines.append(f"  --- {label} ---")
            for v in tiered[tier]:
                lines.append(f"  {idx}. {v}")
                idx += 1
    else:
        for i, v in enumerate(shown, 1):
            lines.append(f"  {i}. {v}")

    if total > MAX_VIOLATIONS:
        lines.append(f"  ...and {total - MAX_VIOLATIONS} more. Fix the above first.")

    lines.append("")
    lines.append("Fix these violations before proceeding.")
    return "\n".join(lines)


# --- Main ---

def main():
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit"):
        return

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path or not os.path.isfile(file_path):
        return

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    if ext in SKIP_EXTENSIONS:
        return

    if not check_cooldown(file_path):
        return

    # --- Discover config ---
    config, project_root = find_config(file_path)

    violations = []

    if config:
        # Config-driven mode
        linter = config.get("linter", "")
        linter_options = config.get("linter_options", {})

        if linter == "eslint" and project_root:
            violations.extend(run_eslint(file_path, project_root))
        elif linter == "clippy" and project_root:
            violations.extend(run_clippy(file_path, project_root, linter_options))
        elif linter == "ruff":
            violations.extend(run_ruff(file_path))

        # Run custom rules from config
        rules = config.get("rules", [])
        if rules:
            violations.extend(run_custom_rules(file_path, rules))

    else:
        # No config — fallback to extension-based linter detection
        linter_type = DEFAULT_LINTERS.get(ext)
        if not linter_type:
            return

        # Need a project root for ESLint/Clippy — find it by walking up
        project_root = _find_project_root(file_path)

        if linter_type == "eslint" and project_root:
            violations.extend(run_eslint(file_path, project_root))
        elif linter_type == "clippy" and project_root:
            violations.extend(run_clippy(file_path, project_root))
        elif linter_type == "ruff":
            violations.extend(run_ruff(file_path))

    if violations:
        output = {"additionalContext": format_output(file_path, violations)}
        print(json.dumps(output))


def _find_project_root(file_path: str) -> str | None:
    """Find project root by looking for common markers (package.json, Cargo.toml, etc.)."""
    markers = {"package.json", "Cargo.toml", "pyproject.toml", "go.mod", "Gemfile"}
    current = os.path.dirname(os.path.abspath(file_path))
    for _ in range(20):
        for marker in markers:
            if os.path.exists(os.path.join(current, marker)):
                return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


if __name__ == "__main__":
    main()
