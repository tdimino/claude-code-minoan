#!/usr/bin/env python3
"""PostToolUse hook: run linters after Write/Edit and feed violations back.

Matcher: Write, Edit
Detects project and language from file path, dispatches to appropriate linter,
runs custom grep-based checks for project conventions, returns violations as
additionalContext for agent self-correction.

Inspired by Factory.ai's "Using Linters to Direct Agents" (Sep 2025) and
"Lint Against the Machine" (Mar 2026). Agents self-correct faster against
lint output than prose instructions.
"""

import json
import os
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

CUSTOM_LINT_SCRIPT = os.path.join(os.path.dirname(__file__), "custom-lint.sh")

# File extensions to skip entirely (no linting value)
SKIP_EXTENSIONS = {
    ".md", ".json", ".yaml", ".yml", ".toml", ".html", ".svg", ".png",
    ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".ttf", ".eot",
    ".map", ".lock", ".env", ".gitignore", ".prettierrc",
}

# Extension → linter type mapping
EXTENSION_LINTERS = {
    ".ts": "eslint",
    ".tsx": "eslint",
    ".js": "eslint",
    ".jsx": "eslint",
    ".mjs": "eslint",
    ".rs": "clippy",
    ".py": "ruff",
    ".css": "custom_only",
    ".scss": "custom_only",
    ".astro": "custom_only",
}

# Project detection: walk up from file looking for these markers
# Each project has a name, root markers, and optional config
PROJECTS = {
    "worldwarwatcher": {
        "markers": {"next.config.ts", "next.config.mjs"},
        "identify_file": "next.config.ts",  # unique to this project
    },
    "open-rebellion": {
        "markers": {"Cargo.toml"},
        "identify_dir": "open-rebellion",  # dirname check
    },
    "minoanmystery-astro": {
        "markers": {"astro.config.mjs", "astro.config.ts"},
        "identify_dir": "minoanmystery-astro",
    },
}


def check_cooldown(file_path: str) -> bool:
    """Return True if file should be linted (not in cooldown)."""
    now = time.time()
    cooldowns = {}

    try:
        with open(COOLDOWN_FILE, "r") as f:
            cooldowns = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass

    # Prune stale entries
    cooldowns = {k: v for k, v in cooldowns.items() if now - v < PRUNE_AGE_SECONDS}

    last_lint = cooldowns.get(file_path, 0)
    if now - last_lint < COOLDOWN_SECONDS:
        return False

    # Update cooldown
    cooldowns[file_path] = now
    try:
        tmp = COOLDOWN_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(cooldowns, f)
        os.replace(tmp, COOLDOWN_FILE)
    except OSError:
        pass

    return True


def detect_project(file_path: str) -> tuple[str | None, str | None]:
    """Walk up from file_path to find project root and name.

    Returns (project_name, project_root) or (None, None).
    """
    current = os.path.dirname(os.path.abspath(file_path))

    for _ in range(20):  # max depth
        dirname = os.path.basename(current)

        for project_name, config in PROJECTS.items():
            # Check directory name match
            if config.get("identify_dir") and dirname == config["identify_dir"]:
                return project_name, current

            # Check marker files
            for marker in config.get("markers", set()):
                if os.path.exists(os.path.join(current, marker)):
                    # For generic markers like Cargo.toml, verify by dirname
                    if config.get("identify_dir"):
                        if dirname == config["identify_dir"]:
                            return project_name, current
                    elif config.get("identify_file"):
                        if os.path.exists(os.path.join(current, config["identify_file"])):
                            return project_name, current
                    else:
                        return project_name, current

        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    return None, None


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
                            # Parse: name = "rebellion-core"
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
                    content = f.read()
                    if "[workspace]" in content:
                        return current
            except OSError:
                pass

        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    return None


def run_eslint(file_path: str, project_root: str) -> list[str]:
    """Run ESLint on a single file and return violation strings."""
    violations = []

    try:
        result = subprocess.run(
            ["npx", "eslint", "--no-warn-ignored", "--format", "json", file_path],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT,
            cwd=project_root,
        )

        # ESLint exits 1 when there are violations
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


def run_clippy(file_path: str, project_root: str) -> list[str]:
    """Run Clippy on the crate containing file_path, filter to that file."""
    violations = []

    crate_name = find_crate_name(file_path)
    workspace_root = find_workspace_root(file_path)
    if not crate_name or not workspace_root:
        return violations

    env = os.environ.copy()
    env["PATH"] = "/usr/bin:" + env.get("PATH", "")

    try:
        result = subprocess.run(
            [
                "cargo", "clippy",
                "-p", crate_name,
                "--message-format=json",
                "--quiet",
            ],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT,
            cwd=workspace_root,
            env=env,
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

            # Filter to our file
            spans = compiler_msg.get("spans", [])
            for span in spans:
                span_file = span.get("file_name", "")
                # Span paths are relative to workspace root
                span_abs = os.path.join(workspace_root, span_file)
                if os.path.abspath(span_abs) == abs_file:
                    text = compiler_msg.get("message", "")
                    code = compiler_msg.get("code", {})
                    rule = code.get("code", "") if code else ""
                    line_num = span.get("line_start", 0)
                    prefix = rule if rule else "clippy"
                    violations.append(
                        f"[{prefix}] {text} (line {line_num})"
                    )
                    break  # one violation per message

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
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT,
        )

        if result.stdout:
            data = json.loads(result.stdout)
            for msg in data:
                code = msg.get("code", "unknown")
                message = msg.get("message", "")
                line = msg.get("location", {}).get("row", 0)
                violations.append(
                    f"[ruff] {code}: {message} (line {line})"
                )

    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError, OSError):
        pass

    return violations


def run_custom_lint(file_path: str, project_name: str) -> list[str]:
    """Run custom-lint.sh and return violation strings."""
    violations = []

    if not os.path.exists(CUSTOM_LINT_SCRIPT):
        return violations

    try:
        result = subprocess.run(
            ["bash", CUSTOM_LINT_SCRIPT, file_path, project_name],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT,
        )

        for line in result.stdout.strip().splitlines():
            if line.strip():
                violations.append(line.strip())

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return violations


def format_output(file_path: str, violations: list[str]) -> str:
    """Format violations into additionalContext string."""
    basename = os.path.basename(file_path)
    total = len(violations)
    shown = violations[:MAX_VIOLATIONS]

    lines = [f"Lint violations in {basename} ({total} issues):"]
    for i, v in enumerate(shown, 1):
        lines.append(f"  {i}. {v}")

    if total > MAX_VIOLATIONS:
        lines.append(f"  ...and {total - MAX_VIOLATIONS} more. Fix the above first.")

    lines.append("")
    lines.append("Fix these violations before proceeding.")

    return "\n".join(lines)


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
    if not file_path:
        return

    # Check file exists
    if not os.path.isfile(file_path):
        return

    # Check extension
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    if ext in SKIP_EXTENSIONS:
        return

    # Check cooldown
    if not check_cooldown(file_path):
        return

    # Detect project
    project_name, project_root = detect_project(file_path)

    # Determine linter type
    linter_type = EXTENSION_LINTERS.get(ext)
    if not linter_type and not project_name:
        return  # Unknown extension and unknown project — nothing to do

    # Collect violations from standard linter
    violations = []

    if linter_type == "eslint" and project_root:
        violations.extend(run_eslint(file_path, project_root))
    elif linter_type == "clippy" and project_root:
        violations.extend(run_clippy(file_path, project_root))
    elif linter_type == "ruff":
        violations.extend(run_ruff(file_path))

    # Always run custom lint if project is known
    if project_name:
        violations.extend(run_custom_lint(file_path, project_name))

    # Output
    if violations:
        output = {
            "additionalContext": format_output(file_path, violations),
        }
        print(json.dumps(output))


if __name__ == "__main__":
    main()
