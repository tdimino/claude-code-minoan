#!/usr/bin/env python3
"""
Analyze a project directory to gather information for CLAUDE.md generation.

Usage:
    python analyze_project.py [project_path]

If no path provided, analyzes current directory.

Output: JSON report with tech stack, structure, commands, and conventions.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any


def detect_package_manager(project_path: Path) -> dict[str, Any]:
    """Detect the package manager and runtime."""
    result = {"manager": None, "runtime": None, "lockfile": None}

    lockfiles = {
        "pnpm-lock.yaml": ("pnpm", "node"),
        "bun.lockb": ("bun", "bun"),
        "yarn.lock": ("yarn", "node"),
        "package-lock.json": ("npm", "node"),
        "Cargo.lock": ("cargo", "rust"),
        "go.sum": ("go", "go"),
        "Gemfile.lock": ("bundler", "ruby"),
        "poetry.lock": ("poetry", "python"),
        "uv.lock": ("uv", "python"),
        "Pipfile.lock": ("pipenv", "python"),
        "requirements.txt": ("pip", "python"),
    }

    for lockfile, (manager, runtime) in lockfiles.items():
        if (project_path / lockfile).exists():
            result["manager"] = manager
            result["runtime"] = runtime
            result["lockfile"] = lockfile
            break

    return result


def detect_tech_stack(project_path: Path) -> dict[str, Any]:
    """Detect frameworks and major dependencies."""
    stack = {"language": None, "framework": None, "database": None, "testing": None, "other": []}

    # Check package.json for Node.js projects
    pkg_json = project_path / "package.json"
    if pkg_json.exists():
        try:
            with open(pkg_json) as f:
                pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

                stack["language"] = "typescript" if "typescript" in deps else "javascript"

                # Frameworks
                if "next" in deps:
                    stack["framework"] = "next.js"
                elif "react" in deps:
                    stack["framework"] = "react"
                elif "vue" in deps:
                    stack["framework"] = "vue"
                elif "express" in deps:
                    stack["framework"] = "express"
                elif "fastify" in deps:
                    stack["framework"] = "fastify"
                elif "hono" in deps:
                    stack["framework"] = "hono"

                # Database
                if "prisma" in deps:
                    stack["database"] = "prisma"
                elif "drizzle-orm" in deps:
                    stack["database"] = "drizzle"
                elif "mongoose" in deps:
                    stack["database"] = "mongodb"

                # Testing
                if "vitest" in deps:
                    stack["testing"] = "vitest"
                elif "jest" in deps:
                    stack["testing"] = "jest"
                elif "mocha" in deps:
                    stack["testing"] = "mocha"

                # Other notable deps
                notable = ["tailwindcss", "shadcn", "tanstack", "zustand", "redux", "trpc"]
                stack["other"] = [d for d in notable if d in deps or any(d in k for k in deps)]
        except (json.JSONDecodeError, IOError):
            pass

    # Check Cargo.toml for Rust
    cargo_toml = project_path / "Cargo.toml"
    if cargo_toml.exists():
        stack["language"] = "rust"
        try:
            content = cargo_toml.read_text()
            if "axum" in content:
                stack["framework"] = "axum"
            elif "actix" in content:
                stack["framework"] = "actix"
            elif "rocket" in content:
                stack["framework"] = "rocket"
        except IOError:
            pass

    # Check pyproject.toml for Python
    pyproject = project_path / "pyproject.toml"
    if pyproject.exists():
        stack["language"] = "python"
        try:
            content = pyproject.read_text()
            if "fastapi" in content.lower():
                stack["framework"] = "fastapi"
            elif "django" in content.lower():
                stack["framework"] = "django"
            elif "flask" in content.lower():
                stack["framework"] = "flask"
            if "pytest" in content.lower():
                stack["testing"] = "pytest"
        except IOError:
            pass

    # Check Gemfile for Ruby
    gemfile = project_path / "Gemfile"
    if gemfile.exists():
        stack["language"] = "ruby"
        try:
            content = gemfile.read_text()
            if "rails" in content.lower():
                stack["framework"] = "rails"
            elif "sinatra" in content.lower():
                stack["framework"] = "sinatra"
            if "rspec" in content.lower():
                stack["testing"] = "rspec"
            elif "minitest" in content.lower():
                stack["testing"] = "minitest"
        except IOError:
            pass

    # Check go.mod for Go
    go_mod = project_path / "go.mod"
    if go_mod.exists():
        stack["language"] = "go"
        try:
            content = go_mod.read_text()
            if "chi" in content:
                stack["framework"] = "chi"
            elif "gin" in content:
                stack["framework"] = "gin"
            elif "echo" in content:
                stack["framework"] = "echo"
        except IOError:
            pass

    return stack


def analyze_structure(project_path: Path) -> dict[str, list[str]]:
    """Analyze project directory structure."""
    structure = {"directories": [], "key_files": [], "config_files": []}

    # Important directories to note
    important_dirs = ["src", "app", "lib", "components", "pages", "api", "routes",
                     "services", "models", "tests", "test", "spec", "docs", "scripts",
                     "cmd", "internal", "pkg", "public", "static", "assets"]

    # Important config files
    config_patterns = [".env.example", "tsconfig.json", "next.config", "vite.config",
                      "tailwind.config", "eslint", "prettier", "Makefile", "Dockerfile",
                      "docker-compose", ".github"]

    for item in project_path.iterdir():
        if item.is_dir() and not item.name.startswith(".") and item.name != "node_modules":
            if item.name in important_dirs:
                structure["directories"].append(item.name)
        elif item.is_file():
            for pattern in config_patterns:
                if pattern in item.name.lower():
                    structure["config_files"].append(item.name)
                    break

    # Check for key files
    key_files = ["README.md", "CONTRIBUTING.md", "CHANGELOG.md", "LICENSE"]
    for kf in key_files:
        if (project_path / kf).exists():
            structure["key_files"].append(kf)

    return structure


def detect_commands(project_path: Path) -> dict[str, str | None]:
    """Detect common development commands from config files."""
    commands = {"dev": None, "build": None, "test": None, "lint": None}

    # Check package.json scripts
    pkg_json = project_path / "package.json"
    if pkg_json.exists():
        try:
            with open(pkg_json) as f:
                pkg = json.load(f)
                scripts = pkg.get("scripts", {})

                # Detect package manager for prefix
                pm = detect_package_manager(project_path)
                prefix = pm["manager"] if pm["manager"] else "npm"
                if prefix in ("npm", "bun"):
                    prefix = f"{prefix} run"

                if "dev" in scripts:
                    commands["dev"] = f"{prefix} dev"
                elif "start" in scripts:
                    commands["dev"] = f"{prefix} start"

                if "build" in scripts:
                    commands["build"] = f"{prefix} build"

                if "test" in scripts:
                    commands["test"] = f"{prefix} test"

                if "lint" in scripts:
                    commands["lint"] = f"{prefix} lint"
        except (json.JSONDecodeError, IOError):
            pass

    # Check Makefile
    makefile = project_path / "Makefile"
    if makefile.exists():
        try:
            content = makefile.read_text()
            if "dev:" in content and not commands["dev"]:
                commands["dev"] = "make dev"
            if "build:" in content and not commands["build"]:
                commands["build"] = "make build"
            if "test:" in content and not commands["test"]:
                commands["test"] = "make test"
        except IOError:
            pass

    # Cargo commands for Rust
    if (project_path / "Cargo.toml").exists():
        commands["dev"] = "cargo run"
        commands["build"] = "cargo build --release"
        commands["test"] = "cargo test"
        commands["lint"] = "cargo clippy"

    # Go commands
    if (project_path / "go.mod").exists():
        if (project_path / "cmd").exists():
            commands["dev"] = "go run ./cmd/..."
        else:
            commands["dev"] = "go run ."
        commands["build"] = "go build"
        commands["test"] = "go test ./..."

    return commands


def check_existing_claude_md(project_path: Path) -> dict[str, Any]:
    """Check for existing CLAUDE.md and related Claude Code infrastructure."""
    result = {
        "exists": False,
        "path": None,
        "line_count": 0,
        "has_agent_docs": False,
        "has_rules_dir": False,
        "rules_count": 0,
        "has_local_md": False,
        "has_agents_dir": False,
        "agents_count": 0,
        "has_hooks": False,
    }

    claude_md = project_path / "CLAUDE.md"
    if claude_md.exists():
        result["exists"] = True
        result["path"] = str(claude_md)
        try:
            content = claude_md.read_text()
            result["line_count"] = len(content.splitlines())
        except IOError:
            pass

    agent_docs = project_path / "agent_docs"
    result["has_agent_docs"] = agent_docs.exists() and agent_docs.is_dir()

    # Check for CLAUDE.local.md (personal project overrides)
    result["has_local_md"] = (project_path / "CLAUDE.local.md").exists()

    # Check .claude/ infrastructure
    claude_dir = project_path / ".claude"
    if claude_dir.exists() and claude_dir.is_dir():
        # Rules directory
        rules_dir = claude_dir / "rules"
        if rules_dir.exists() and rules_dir.is_dir():
            result["has_rules_dir"] = True
            result["rules_count"] = len(list(rules_dir.rglob("*.md")))

        # Agents directory
        agents_dir = claude_dir / "agents"
        if agents_dir.exists() and agents_dir.is_dir():
            result["has_agents_dir"] = True
            result["agents_count"] = len(list(agents_dir.rglob("*.md")))

        # Hooks directory
        hooks_dir = claude_dir / "hooks"
        result["has_hooks"] = hooks_dir.exists() and hooks_dir.is_dir()

    return result


def analyze_project(project_path: str | None = None) -> dict[str, Any]:
    """Main analysis function."""
    path = Path(project_path) if project_path else Path.cwd()

    if not path.exists():
        return {"error": f"Path does not exist: {path}"}

    if not path.is_dir():
        return {"error": f"Path is not a directory: {path}"}

    return {
        "project_path": str(path.absolute()),
        "project_name": path.name,
        "package_manager": detect_package_manager(path),
        "tech_stack": detect_tech_stack(path),
        "structure": analyze_structure(path),
        "commands": detect_commands(path),
        "existing_claude_md": check_existing_claude_md(path),
    }


if __name__ == "__main__":
    project_path = sys.argv[1] if len(sys.argv) > 1 else None
    result = analyze_project(project_path)
    print(json.dumps(result, indent=2))
