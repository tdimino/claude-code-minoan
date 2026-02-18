#!/usr/bin/env python3
"""
Convert CLAUDE.md to AGENTS.md format.

Usage:
    python3 convert_claude_to_agents.py <claude_md_path> [output_path]

Output: AGENTS.md file + conversion_report.json
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

MAX_INLINE_LINES = 50
MAX_BYTES = 32768


def parse_claude_md(content: str) -> dict[str, Any]:
    """Parse CLAUDE.md and catalog features."""
    result = {
        "imports": [],
        "claude_specific": [],
        "sections": [],
        "has_frontmatter": content.startswith("---"),
    }

    lines = content.splitlines()

    # Detect @imports (single-pass with running parity flag)
    in_code_block = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if stripped.startswith("@") and not stripped.startswith("@@") and not in_code_block:
            result["imports"].append({"line": i + 1, "ref": stripped})

    # Detect Claude-specific features
    claude_patterns = [
        (r"/\w[\w-]*", "skill_invocation"),
        (r"\.claude/hooks/", "hooks_reference"),
        (r"\.claude/settings", "settings_reference"),
        (r"\.claude/skills/", "skills_reference"),
        (r"\.claude/commands/", "commands_reference"),
        (r"/init\b|/context\b|/compact\b|/clear\b", "claude_command"),
    ]
    for i, line in enumerate(lines):
        for pattern, feature_type in claude_patterns:
            if re.search(pattern, line):
                result["claude_specific"].append({
                    "line": i + 1,
                    "type": feature_type,
                    "content": line.strip(),
                })

    # Parse sections by headings
    current_section = {"heading": None, "level": 0, "start": 0, "lines": []}
    for i, line in enumerate(lines):
        heading_match = re.match(r"^(#{1,6})\s+(.+)", line)
        if heading_match:
            if current_section["heading"] or current_section["lines"]:
                result["sections"].append(current_section)
            current_section = {
                "heading": heading_match.group(2),
                "level": len(heading_match.group(1)),
                "start": i + 1,
                "lines": [],
            }
        else:
            current_section["lines"].append(line)

    if current_section["heading"] or current_section["lines"]:
        result["sections"].append(current_section)

    return result


def resolve_import(ref: str, source_dir: Path) -> dict[str, Any]:
    """Resolve an @import reference."""
    result = {"ref": ref, "action": "remove", "content": None, "suggestion": None}

    # Strip @ prefix
    path_str = ref.lstrip("@").strip()

    # Handle home directory references
    if path_str.startswith("~"):
        resolved = Path(path_str).expanduser()
    else:
        resolved = source_dir / path_str

    if not resolved.exists():
        result["action"] = "remove"
        result["suggestion"] = f"Referenced file not found: {path_str}"
        return result

    try:
        content = resolved.read_text()
        line_count = len(content.splitlines())
    except IOError:
        result["action"] = "remove"
        result["suggestion"] = f"Cannot read: {path_str}"
        return result

    # Personal/global files
    if "~/.claude/" in path_str or path_str.startswith("~"):
        result["action"] = "global"
        result["suggestion"] = f"Move to ~/.codex/AGENTS.md (personal defaults)"
        result["content"] = content
        return result

    # Small files: inline
    if line_count <= MAX_INLINE_LINES:
        result["action"] = "inline"
        result["content"] = content
        return result

    # Large files: suggest nested AGENTS.md
    result["action"] = "nested"
    result["suggestion"] = f"Create nested AGENTS.md in {resolved.parent.name}/ ({line_count} lines)"
    result["content"] = content
    return result


def transform_content(content: str, parsed: dict, source_dir: Path) -> tuple[str, list[dict]]:
    """Transform CLAUDE.md content to AGENTS.md format."""
    report_items = []
    lines = content.splitlines()
    output_lines = []
    in_frontmatter = False
    in_code_block = False
    max_frontmatter_lines = 50

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip YAML frontmatter (with safety limit)
        if i == 0 and stripped == "---":
            in_frontmatter = True
            report_items.append({"type": "auto", "action": "Stripped YAML frontmatter"})
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            elif i > max_frontmatter_lines:
                in_frontmatter = False
                report_items.append({"type": "manual", "action": "Unclosed frontmatter",
                                     "suggestion": f"No closing --- found within {max_frontmatter_lines} lines"})
            continue

        # Track code blocks
        if stripped.startswith("```"):
            in_code_block = not in_code_block

        # Handle @imports (not in code blocks)
        if stripped.startswith("@") and not stripped.startswith("@@"):
            if not in_code_block:
                resolution = resolve_import(stripped, source_dir)
                if resolution["action"] == "inline" and resolution["content"]:
                    output_lines.append("")
                    output_lines.extend(resolution["content"].splitlines())
                    output_lines.append("")
                    report_items.append({
                        "type": "auto",
                        "action": f"Inlined {stripped} ({len(resolution['content'].splitlines())} lines)",
                    })
                else:
                    report_items.append({
                        "type": "manual",
                        "action": f"Removed {stripped}",
                        "suggestion": resolution.get("suggestion", "Review and manually migrate"),
                    })
                continue

        # Strip Claude-specific slash commands in prose
        if re.match(r"^-\s+`/(?:init|context|compact|clear|help)`", stripped):
            report_items.append({"type": "auto", "action": f"Removed Claude command: {stripped}"})
            continue

        # Convert hooks references to rules suggestions
        if ".claude/hooks/" in line:
            report_items.append({
                "type": "manual",
                "action": f"Hooks reference on line {i+1}",
                "suggestion": "Convert to .rules file (Starlark). See references/starlark-rules-spec.md",
            })
            output_lines.append(f"<!-- TODO: Convert hook to .rules file: {stripped} -->")
            continue

        # Pass through everything else
        output_lines.append(line)

    return "\n".join(output_lines), report_items


def validate_output(content: str) -> list[str]:
    """Validate the converted output."""
    warnings = []
    byte_size = len(content.encode("utf-8"))
    line_count = len(content.splitlines())

    if byte_size > MAX_BYTES:
        warnings.append(f"Output is {byte_size:,} bytes, exceeds 32 KiB limit. Split into nested files.")
    if line_count > 200:
        warnings.append(f"Output is {line_count} lines. Target under 200.")
    if re.search(r"^\s*@\S+", content, re.MULTILINE):
        warnings.append("Output still contains @import syntax. Remove manually.")
    if content.startswith("---"):
        warnings.append("Output starts with YAML frontmatter. Remove it.")

    return warnings


def convert(claude_md_path: str, output_path: str | None = None) -> dict[str, Any]:
    """Main conversion function."""
    source = Path(claude_md_path)
    if not source.exists():
        return {"error": f"File not found: {claude_md_path}"}

    content = source.read_text()
    source_dir = source.parent

    # Parse
    parsed = parse_claude_md(content)

    # Transform
    output_content, report_items = transform_content(content, parsed, source_dir)

    # Validate
    warnings = validate_output(output_content)

    # Write output
    if output_path:
        out = Path(output_path)
    else:
        out = source_dir / "AGENTS.md"

    out.write_text(output_content)

    # Write report
    report = {
        "source": str(source),
        "output": str(out),
        "auto_converted": [r for r in report_items if r["type"] == "auto"],
        "manual_review": [r for r in report_items if r["type"] == "manual"],
        "warnings": warnings,
        "stats": {
            "input_lines": len(content.splitlines()),
            "output_lines": len(output_content.splitlines()),
            "input_bytes": len(content.encode("utf-8")),
            "output_bytes": len(output_content.encode("utf-8")),
            "imports_found": len(parsed["imports"]),
            "claude_features_found": len(parsed["claude_specific"]),
        },
    }

    report_path = source_dir / "conversion_report.json"
    report_path.write_text(json.dumps(report, indent=2))

    return report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 convert_claude_to_agents.py <claude_md_path> [output_path]")
        sys.exit(1)

    claude_md = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else None
    result = convert(claude_md, output)
    print(json.dumps(result, indent=2))
