#!/usr/bin/env python3
"""Detect repository language, build system, test runner, and lint tools.

Outputs a JSON StackInfo object to stdout for consumption by scaffold.py and eval_gen.py.

Usage:
    python3 detect_stack.py [--repo-root /path/to/repo]
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def detect_language(root: Path) -> dict:
    """Detect primary language and toolchain from build files."""
    # Priority order: Cargo.toml > pyproject.toml > setup.py > package.json > go.mod > Makefile
    cargo = root / "Cargo.toml"
    if cargo.exists():
        content = cargo.read_text()
        crates = list(root.glob("crates/*/Cargo.toml"))
        workspace_note = f"workspace with {len(crates)} crates" if crates else "single crate"
        edition = "2021"
        m = re.search(r'edition\s*=\s*"(\d+)"', content)
        if m:
            edition = m.group(1)
        return {
            "language": "rust",
            "build_system": "cargo",
            "build_cmd": "cargo build 2>&1",
            "test_cmd": "cargo test 2>&1",
            "test_runner": "cargo-test",
            "lint_cmd": "cargo clippy -- -D warnings 2>&1",
            "lint_tool": "clippy",
            "conventions": [f"Rust {edition} edition", workspace_note],
        }

    pyproject = root / "pyproject.toml"
    setup_py = root / "setup.py"
    if pyproject.exists() or setup_py.exists():
        # Detect test runner
        test_cmd = "python3 -m pytest 2>&1"
        test_runner = "pytest"
        if pyproject.exists():
            content = pyproject.read_text()
            if "unittest" in content and "pytest" not in content:
                test_cmd = "python3 -m unittest discover 2>&1"
                test_runner = "unittest"
        # Detect lint tool
        lint_cmd = ""
        lint_tool = ""
        if (root / "ruff.toml").exists() or (pyproject.exists() and "ruff" in pyproject.read_text()):
            lint_cmd = "ruff check . 2>&1"
            lint_tool = "ruff"
        elif (root / ".flake8").exists() or (root / "setup.cfg").exists():
            lint_cmd = "flake8 . 2>&1"
            lint_tool = "flake8"
        build_cmd = "python3 -m py_compile $(find . -name '*.py' -not -path './.lab/*') 2>&1"
        conventions = ["Python project"]
        if pyproject.exists():
            content = pyproject.read_text()
            if "[tool.poetry]" in content:
                conventions.append("Poetry")
            elif "[build-system]" in content and "hatchling" in content:
                conventions.append("Hatch")
            elif "[build-system]" in content and "setuptools" in content:
                conventions.append("setuptools")
        return {
            "language": "python",
            "build_system": "pip" if setup_py.exists() else "pyproject",
            "build_cmd": build_cmd,
            "test_cmd": test_cmd,
            "test_runner": test_runner,
            "lint_cmd": lint_cmd,
            "lint_tool": lint_tool,
            "conventions": conventions,
        }

    pkg_json = root / "package.json"
    if pkg_json.exists():
        content = json.loads(pkg_json.read_text())
        scripts = content.get("scripts", {})
        # Detect test runner from scripts
        test_cmd = "npm test 2>&1"
        test_runner = "npm-test"
        if "test" in scripts:
            test_script = scripts["test"]
            if "vitest" in test_script:
                test_runner = "vitest"
            elif "jest" in test_script:
                test_runner = "jest"
            elif "mocha" in test_script:
                test_runner = "mocha"
        # Detect build
        build_cmd = "npm run build 2>&1" if "build" in scripts else "npx tsc --noEmit 2>&1"
        # Detect lint
        lint_cmd = ""
        lint_tool = ""
        if "lint" in scripts:
            lint_cmd = "npm run lint 2>&1"
            lint_tool = "eslint"  # most common
        deps = {**content.get("dependencies", {}), **content.get("devDependencies", {})}
        conventions = []
        if "typescript" in deps:
            conventions.append("TypeScript")
        if "next" in deps:
            conventions.append("Next.js")
        elif "react" in deps:
            conventions.append("React")
        elif "vue" in deps:
            conventions.append("Vue")
        if not conventions:
            conventions.append("Node.js")
        return {
            "language": "typescript" if "typescript" in deps else "javascript",
            "build_system": "npm",
            "build_cmd": build_cmd,
            "test_cmd": test_cmd,
            "test_runner": test_runner,
            "lint_cmd": lint_cmd,
            "lint_tool": lint_tool,
            "conventions": conventions,
        }

    go_mod = root / "go.mod"
    if go_mod.exists():
        return {
            "language": "go",
            "build_system": "go",
            "build_cmd": "go build ./... 2>&1",
            "test_cmd": "go test ./... 2>&1",
            "test_runner": "go-test",
            "lint_cmd": "go vet ./... 2>&1",
            "lint_tool": "go-vet",
            "conventions": ["Go modules"],
        }

    makefile = root / "Makefile"
    if makefile.exists():
        content = makefile.read_text()
        lang = "unknown"
        if "gcc" in content or "g++" in content:
            lang = "c/c++"
        return {
            "language": lang,
            "build_system": "make",
            "build_cmd": "make 2>&1",
            "test_cmd": "make test 2>&1" if "test:" in content else "",
            "test_runner": "make-test",
            "lint_cmd": "",
            "lint_tool": "",
            "conventions": ["Makefile"],
        }

    return {
        "language": "unknown",
        "build_system": "unknown",
        "build_cmd": "",
        "test_cmd": "",
        "test_runner": "",
        "lint_cmd": "",
        "lint_tool": "",
        "conventions": [],
    }


def estimate_test_count(root: Path, language: str) -> int:
    """Estimate the number of tests in the repo."""
    count = 0
    try:
        if language == "rust":
            for f in root.rglob("*.rs"):
                if ".lab" in str(f) or "target" in str(f):
                    continue
                content = f.read_text(errors="ignore")
                count += content.count("#[test]")
        elif language == "python":
            for f in root.rglob("*.py"):
                if ".lab" in str(f) or "__pycache__" in str(f):
                    continue
                content = f.read_text(errors="ignore")
                count += len(re.findall(r"def test_", content))
        elif language in ("javascript", "typescript"):
            for ext in ("*.js", "*.ts", "*.jsx", "*.tsx"):
                for f in root.rglob(ext):
                    if ".lab" in str(f) or "node_modules" in str(f):
                        continue
                    content = f.read_text(errors="ignore")
                    count += len(re.findall(r"\b(it|test)\s*\(", content))
        elif language == "go":
            for f in root.rglob("*_test.go"):
                if ".lab" in str(f):
                    continue
                content = f.read_text(errors="ignore")
                count += len(re.findall(r"func Test", content))
    except Exception:
        pass
    return count


def find_src_dirs(root: Path, language: str) -> list:
    """Find primary source directories."""
    candidates = []
    for name in ("src", "lib", "crates", "pkg", "cmd", "internal", "app", "packages"):
        d = root / name
        if d.is_dir():
            candidates.append(f"{name}/")
    if not candidates:
        candidates.append("./")
    return candidates


def main():
    parser = argparse.ArgumentParser(description="Detect repo stack for autoresearch")
    parser.add_argument("--repo-root", default=".", help="Path to repo root")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    if not (root / ".git").exists():
        print(json.dumps({"error": "Not a git repository", "path": str(root)}))
        sys.exit(1)

    stack = detect_language(root)
    stack["has_claude_md"] = (root / "CLAUDE.md").exists()
    stack["has_agents_md"] = (root / "AGENTS.md").exists()
    stack["test_count_estimate"] = estimate_test_count(root, stack["language"])
    stack["src_dirs"] = find_src_dirs(root, stack["language"])
    stack["repo_root"] = str(root)
    stack["repo_name"] = root.name

    print(json.dumps(stack, indent=2))


if __name__ == "__main__":
    main()
