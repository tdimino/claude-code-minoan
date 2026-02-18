#!/usr/bin/env python3
"""
Scaffold a Codex-format skill in .agents/skills/<name>/.

Usage:
    python3 scaffold_codex_skill.py <name> [options]

Options:
    --path PATH          Project path (default: current directory)
    --description DESC   Skill description
    --display-name NAME  Display name for UI (agents/openai.yaml)
    --no-yaml            Skip generating agents/openai.yaml
    --mcp NAME URL       Add MCP dependency (repeatable)

Output: .agents/skills/<name>/ directory with SKILL.md and optional openai.yaml.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def validate_skill_name(name: str) -> str | None:
    """Validate skill name follows conventions."""
    if not re.match(r"^[a-z][a-z0-9-]*$", name):
        return "Name must be lowercase, start with a letter, and contain only a-z, 0-9, hyphens"
    if len(name) > 64:
        return "Name must be 64 characters or fewer"
    if name.startswith("-") or name.endswith("-"):
        return "Name must not start or end with a hyphen"
    if "--" in name:
        return "Name must not contain consecutive hyphens"
    return None


def generate_skill_md(name: str, description: str) -> str:
    """Generate SKILL.md content."""
    title = name.replace("-", " ").title()
    return f"""---
name: {name}
description: >-
  {description}
---

# {title}

## Overview

<!-- Describe what this skill does and when to use it -->

## Usage

<!-- Add instructions for the agent -->

## Commands

```bash
# Add executable commands here
```
"""


def generate_openai_yaml(name: str, display_name: str | None, description: str,
                          mcp_deps: list[dict] | None) -> str:
    """Generate agents/openai.yaml content."""
    display = display_name or name.replace("-", " ").title()
    lines = [
        "interface:",
        f'  display_name: "{display}"',
        f'  short_description: "{description[:80]}"',
        "",
        "policy:",
        "  allow_implicit_invocation: true",
    ]

    if mcp_deps:
        lines.extend(["", "dependencies:", "  tools:"])
        for dep in mcp_deps:
            lines.append(f'    - type: "mcp"')
            lines.append(f'      value: "{dep["name"]}"')
            if "url" in dep:
                lines.append(f'      transport: "streamable_http"')
                lines.append(f'      url: "{dep["url"]}"')
            else:
                lines.append(f'      transport: "stdio"')

    return "\n".join(lines) + "\n"


def scaffold_skill(name: str, project_path: Path, description: str,
                    display_name: str | None, no_yaml: bool,
                    mcp_deps: list[dict] | None) -> dict[str, Any]:
    """Create the skill directory structure."""
    report = {"name": name, "path": None, "files_created": [], "errors": []}

    # Validate name
    error = validate_skill_name(name)
    if error:
        report["errors"].append(error)
        return report

    # Create directory structure
    skill_dir = project_path / ".agents" / "skills" / name
    if skill_dir.exists():
        report["errors"].append(f"Skill directory already exists: {skill_dir}")
        return report

    dirs = [
        skill_dir,
        skill_dir / "scripts",
        skill_dir / "references",
        skill_dir / "assets",
    ]
    if not no_yaml:
        dirs.append(skill_dir / "agents")

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    report["path"] = str(skill_dir)

    # Write SKILL.md
    skill_md = generate_skill_md(name, description)
    skill_md_path = skill_dir / "SKILL.md"
    skill_md_path.write_text(skill_md)
    report["files_created"].append("SKILL.md")

    # Write agents/openai.yaml
    if not no_yaml:
        yaml_content = generate_openai_yaml(name, display_name, description, mcp_deps)
        yaml_path = skill_dir / "agents" / "openai.yaml"
        yaml_path.write_text(yaml_content)
        report["files_created"].append("agents/openai.yaml")

    # Write placeholder files
    (skill_dir / "scripts" / ".gitkeep").touch()
    (skill_dir / "references" / ".gitkeep").touch()
    (skill_dir / "assets" / ".gitkeep").touch()

    return report


def main():
    parser = argparse.ArgumentParser(description="Scaffold a Codex-format skill")
    parser.add_argument("name", help="Skill name (lowercase, hyphens only)")
    parser.add_argument("--path", default=".", help="Project path (default: cwd)")
    parser.add_argument("--description", default="TODO: Add skill description",
                        help="Skill description")
    parser.add_argument("--display-name", help="Display name for UI")
    parser.add_argument("--no-yaml", action="store_true",
                        help="Skip agents/openai.yaml generation")
    parser.add_argument("--mcp", action="append", nargs=2, metavar=("NAME", "URL"),
                        help="MCP dependency: name url (repeatable)")

    args = parser.parse_args()
    project_path = Path(args.path).resolve()

    mcp_deps = None
    if args.mcp:
        mcp_deps = [{"name": name, "url": url} for name, url in args.mcp]

    report = scaffold_skill(
        name=args.name,
        project_path=project_path,
        description=args.description,
        display_name=args.display_name,
        no_yaml=args.no_yaml,
        mcp_deps=mcp_deps,
    )

    print(json.dumps(report, indent=2))
    if report["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
