#!/usr/bin/env python3
"""
Validate and audit AGENTS.md files for a project.

Usage:
    python3 validate_agents_md.py [project_path]

Checks: size limits, format compliance, consistency, secrets detection.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

MAX_BYTES = 32768  # 32 KiB default
WARN_LINES = 200
ERROR_LINES = 400

SECRET_PATTERNS = [
    r"(?i)(api[_-]?key|secret|token|password|credential)\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{16,}",
    r"(?i)(sk-|ghp_|gho_|github_pat_|xoxb-|xoxp-|Bearer\s+)[a-zA-Z0-9_\-]+",
    r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
]

IMPORT_PATTERN = re.compile(r"^\s*@\S+", re.MULTILINE)
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n", re.MULTILINE)


def validate_file(filepath: Path, project_path: Path) -> dict[str, Any]:
    """Validate a single AGENTS.md file."""
    result = {
        "file": str(filepath.relative_to(project_path)),
        "status": "pass",
        "errors": [],
        "warnings": [],
        "bytes": 0,
    }

    try:
        content = filepath.read_text(encoding="utf-8")
    except (IOError, UnicodeDecodeError) as e:
        result["status"] = "error"
        result["errors"].append(f"Cannot read file: {e}")
        return result

    lines = content.splitlines()
    byte_size = len(content.encode("utf-8"))
    result["bytes"] = byte_size

    # Size checks
    if byte_size > MAX_BYTES:
        result["errors"].append(
            f"File size {byte_size:,} bytes exceeds {MAX_BYTES:,} byte limit (project_doc_max_bytes)"
        )
    if len(lines) > ERROR_LINES:
        result["errors"].append(f"File has {len(lines)} lines (max recommended: {ERROR_LINES})")
    elif len(lines) > WARN_LINES:
        result["warnings"].append(f"File has {len(lines)} lines (target: under {WARN_LINES})")

    # Format compliance
    if IMPORT_PATTERN.search(content):
        import_lines = [i + 1 for i, line in enumerate(lines) if re.match(r"^\s*@\S+", line)]
        result["errors"].append(
            f"@import syntax detected on lines {import_lines[:5]}. AGENTS.md does not support imports."
        )

    if content.startswith("---"):
        result["warnings"].append(
            "YAML frontmatter detected. AGENTS.md does not use frontmatter—content may be ignored by some agents."
        )

    # Secrets detection
    for pattern in SECRET_PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            result["errors"].append(
                f"Potential secret/credential detected matching pattern: {pattern[:40]}..."
            )
            break

    # Command verification
    code_blocks = re.findall(r"```(?:bash|sh|shell)?\n(.*?)```", content, re.DOTALL)
    commands_found = []
    for block in code_blocks:
        for line in block.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                commands_found.append(stripped)
    if commands_found:
        result["info"] = {"commands_referenced": len(commands_found)}

    # Directory reference checks
    dir_refs = re.findall(r"`/?(\w+(?:/\w+)*)/`|`/(\w+(?:/\w+)*)`", content)
    if dir_refs:
        missing_dirs = []
        for ref_tuple in dir_refs:
            ref = ref_tuple[0] or ref_tuple[1]
            if ref and not (project_path / ref).exists():
                missing_dirs.append(ref)
        if missing_dirs:
            result["warnings"].append(f"Referenced directories not found: {missing_dirs[:5]}")

    # Empty file
    if not content.strip():
        result["warnings"].append("File is empty—Codex will skip it.")

    # Set final status
    if result["errors"]:
        result["status"] = "fail"
    elif result["warnings"]:
        result["status"] = "warn"

    return result


def check_hierarchy_consistency(files: list[dict], project_path: Path) -> list[str]:
    """Check for inconsistencies in nested AGENTS.md hierarchy."""
    issues = []

    # Check for override without base
    override_dirs = set()
    base_dirs = set()
    for f in files:
        fpath = Path(f["file"])
        parent = str(fpath.parent)
        if "override" in fpath.name.lower():
            override_dirs.add(parent)
        else:
            base_dirs.add(parent)

    orphan_overrides = override_dirs - base_dirs
    for d in orphan_overrides:
        issues.append(f"AGENTS.override.md in {d}/ has no corresponding AGENTS.md (intentional?)")

    # Check combined size
    total_bytes = sum(f.get("bytes", 0) for f in files if "bytes" in f)
    if total_bytes > MAX_BYTES:
        issues.append(
            f"Combined AGENTS.md files total {total_bytes:,} bytes, exceeding {MAX_BYTES:,} byte limit"
        )

    return issues


def validate_project(project_path: str | None = None) -> dict[str, Any]:
    """Validate all AGENTS.md files in a project."""
    path = Path(project_path) if project_path else Path.cwd()
    if not path.exists():
        return {"error": f"Path does not exist: {path}"}

    report = {"project": str(path.absolute()), "files": [], "hierarchy_issues": [],
              "summary": {"total": 0, "pass": 0, "warn": 0, "fail": 0}}

    # Find all AGENTS.md files
    agents_files = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in {"node_modules", ".git", "__pycache__", ".venv"}]
        for fname in files:
            if fname in ("AGENTS.md", "AGENTS.override.md"):
                fpath = Path(root) / fname
                agents_files.append(fpath)

    if not agents_files:
        report["summary"]["message"] = "No AGENTS.md files found in project."
        return report

    file_info = []
    for fpath in agents_files:
        result = validate_file(fpath, path)
        report["files"].append(result)
        report["summary"]["total"] += 1
        report["summary"][result["status"]] += 1
        file_info.append({
            "file": result["file"],
            "bytes": result.get("bytes", 0),
        })

    report["hierarchy_issues"] = check_hierarchy_consistency(file_info, path)

    return report


if __name__ == "__main__":
    project_path = sys.argv[1] if len(sys.argv) > 1 else None
    result = validate_project(project_path)
    print(json.dumps(result, indent=2))
