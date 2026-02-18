#!/usr/bin/env python3
"""
Analyze a project directory for AGENTS.md generation and Codex CLI configuration.

Usage:
    python3 analyze_project.py [project_path]

Output: JSON report with tech stack, commands, structure, and Codex artifact inventory.
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

    pkg_json = project_path / "package.json"
    if pkg_json.exists():
        try:
            with open(pkg_json) as f:
                pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                stack["language"] = "typescript" if "typescript" in deps else "javascript"
                for fw, name in [("next", "next.js"), ("react", "react"), ("vue", "vue"),
                                 ("express", "express"), ("fastify", "fastify"), ("hono", "hono"),
                                 ("astro", "astro"), ("svelte", "svelte")]:
                    if fw in deps:
                        stack["framework"] = name
                        break
                for db, name in [("prisma", "prisma"), ("drizzle-orm", "drizzle"), ("mongoose", "mongodb")]:
                    if db in deps:
                        stack["database"] = name
                        break
                for test, name in [("vitest", "vitest"), ("jest", "jest"), ("mocha", "mocha")]:
                    if test in deps:
                        stack["testing"] = name
                        break
                notable = ["tailwindcss", "shadcn", "tanstack", "zustand", "redux", "trpc"]
                stack["other"] = [d for d in notable if d in deps or any(d in k for k in deps)]
        except (json.JSONDecodeError, IOError):
            pass

    cargo_toml = project_path / "Cargo.toml"
    if cargo_toml.exists():
        stack["language"] = "rust"
        try:
            content = cargo_toml.read_text()
            for fw, name in [("axum", "axum"), ("actix", "actix"), ("rocket", "rocket")]:
                if fw in content:
                    stack["framework"] = name
                    break
        except IOError:
            pass

    pyproject = project_path / "pyproject.toml"
    if pyproject.exists():
        stack["language"] = "python"
        try:
            content = pyproject.read_text().lower()
            for fw, name in [("fastapi", "fastapi"), ("django", "django"), ("flask", "flask")]:
                if fw in content:
                    stack["framework"] = name
                    break
            if "pytest" in content:
                stack["testing"] = "pytest"
        except IOError:
            pass

    gemfile = project_path / "Gemfile"
    if gemfile.exists():
        stack["language"] = "ruby"
        try:
            content = gemfile.read_text().lower()
            if "rails" in content:
                stack["framework"] = "rails"
            elif "sinatra" in content:
                stack["framework"] = "sinatra"
            if "rspec" in content:
                stack["testing"] = "rspec"
            elif "minitest" in content:
                stack["testing"] = "minitest"
        except IOError:
            pass

    go_mod = project_path / "go.mod"
    if go_mod.exists():
        stack["language"] = "go"
        try:
            content = go_mod.read_text()
            for fw, name in [("chi", "chi"), ("gin", "gin"), ("echo", "echo")]:
                if fw in content:
                    stack["framework"] = name
                    break
        except IOError:
            pass

    return stack


def analyze_structure(project_path: Path) -> dict[str, list[str]]:
    """Analyze project directory structure."""
    structure = {"directories": [], "key_files": [], "config_files": []}
    important_dirs = {"src", "app", "lib", "components", "pages", "api", "routes",
                      "services", "models", "tests", "test", "spec", "docs", "scripts",
                      "cmd", "internal", "pkg", "public", "static", "assets", "packages"}
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

    key_files = ["README.md", "CONTRIBUTING.md", "CHANGELOG.md", "LICENSE"]
    for kf in key_files:
        if (project_path / kf).exists():
            structure["key_files"].append(kf)

    return structure


def detect_commands(project_path: Path) -> dict[str, str | None]:
    """Detect common development commands from config files."""
    commands = {"dev": None, "build": None, "test": None, "lint": None}

    pkg_json = project_path / "package.json"
    if pkg_json.exists():
        try:
            with open(pkg_json) as f:
                pkg = json.load(f)
                scripts = pkg.get("scripts", {})
                pm = detect_package_manager(project_path)
                prefix = pm["manager"] if pm["manager"] else "npm"
                if prefix == "npm":
                    prefix = "npm run"
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

    if (project_path / "Cargo.toml").exists():
        if not commands["dev"]:
            commands["dev"] = "cargo run"
        if not commands["build"]:
            commands["build"] = "cargo build --release"
        if not commands["test"]:
            commands["test"] = "cargo test"
        if not commands["lint"]:
            commands["lint"] = "cargo clippy"

    if (project_path / "go.mod").exists():
        if not commands["dev"]:
            commands["dev"] = "go run ./cmd/..." if (project_path / "cmd").exists() else "go run ."
        if not commands["build"]:
            commands["build"] = "go build"
        if not commands["test"]:
            commands["test"] = "go test ./..."

    return commands


# --- Codex-specific detection (extends claude-md-manager) ---

def detect_agents_md(project_path: Path) -> list[dict[str, Any]]:
    """Walk directory tree for AGENTS.md and AGENTS.override.md files."""
    found = []
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in {"node_modules", ".git", "__pycache__", ".venv"}]
        for fname in ["AGENTS.override.md", "AGENTS.md"]:
            fpath = Path(root) / fname
            if fpath.exists():
                try:
                    content = fpath.read_text()
                    found.append({
                        "path": str(fpath),
                        "relative": str(fpath.relative_to(project_path)),
                        "type": "override" if "override" in fname.lower() else "base",
                        "lines": len(content.splitlines()),
                        "bytes": len(content.encode("utf-8")),
                    })
                except IOError:
                    found.append({"path": str(fpath), "relative": str(fpath.relative_to(project_path)),
                                  "type": "override" if "override" in fname.lower() else "base",
                                  "lines": 0, "bytes": 0})
    return found


def detect_codex_config(project_path: Path) -> dict[str, Any]:
    """Check for Codex config.toml files."""
    result = {"global": None, "project": None}
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    global_config = codex_home / "config.toml"
    if global_config.exists():
        result["global"] = str(global_config)
    project_config = project_path / ".codex" / "config.toml"
    if project_config.exists():
        result["project"] = str(project_config)
    return result


def detect_codex_skills(project_path: Path) -> list[str]:
    """Check for .agents/skills/ directories."""
    skills = []
    agents_skills = project_path / ".agents" / "skills"
    if agents_skills.exists():
        for item in agents_skills.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                skills.append(item.name)
    return skills


def detect_rules_files(project_path: Path) -> list[str]:
    """Check for .rules files in Codex directories."""
    found = []
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    for rules_dir in [codex_home / "rules", project_path / ".codex" / "rules"]:
        if rules_dir.exists():
            for f in rules_dir.iterdir():
                if f.suffix == ".rules":
                    found.append(str(f))
    return found


def detect_claude_md(project_path: Path) -> dict[str, Any]:
    """Check for CLAUDE.md (conversion candidate)."""
    result = {"exists": False, "path": None, "line_count": 0, "has_agent_docs": False, "has_imports": False}
    claude_md = project_path / "CLAUDE.md"
    if claude_md.exists():
        result["exists"] = True
        result["path"] = str(claude_md)
        try:
            content = claude_md.read_text()
            result["line_count"] = len(content.splitlines())
            result["has_imports"] = "@" in content and any(
                line.strip().startswith("@") for line in content.splitlines()
            )
        except IOError:
            pass
    result["has_agent_docs"] = (project_path / "agent_docs").is_dir()
    return result


def detect_global_agents_md() -> dict[str, Any]:
    """Check for global ~/.codex/AGENTS.md."""
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    result = {"exists": False, "path": None}
    for fname in ["AGENTS.override.md", "AGENTS.md"]:
        fpath = codex_home / fname
        if fpath.exists():
            result["exists"] = True
            result["path"] = str(fpath)
            break
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
        "agents_md_files": detect_agents_md(path),
        "codex_config": detect_codex_config(path),
        "codex_skills": detect_codex_skills(path),
        "rules_files": detect_rules_files(path),
        "claude_md": detect_claude_md(path),
        "global_agents_md": detect_global_agents_md(),
    }


if __name__ == "__main__":
    project_path = sys.argv[1] if len(sys.argv) > 1 else None
    result = analyze_project(project_path)
    print(json.dumps(result, indent=2))
