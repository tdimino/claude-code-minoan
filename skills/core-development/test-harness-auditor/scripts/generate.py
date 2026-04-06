#!/usr/bin/env python3
"""Test Harness Auditor — Phase 2: Config generation.

Generates .claude/lint-rules.json and CLAUDE.md testing sections based on
the audit results. Merges with existing configs when present.

Prints generated configs to stdout for Claude to present to the user.
"""

import json
import os
import re
import sys


# ---------------------------------------------------------------------------
# Stack → Lint Rules Templates
# ---------------------------------------------------------------------------

COMMON_RULES = [
    {
        "extensions": ["ts", "tsx", "js", "jsx", "py", "rs", "rb", "go"],
        "pattern": "console\\.log\\(|debugger;|binding\\.pry|import pdb|println!\\(\"DEBUG",
        "message": "[debugging-residue] Debug statement left in code",
        "exclude_patterns": ["test", "spec", "debug\\."],
        "_tag": "auto:debugging-residue",
    },
    {
        "extensions": ["ts", "tsx", "js", "jsx", "py", "rs", "rb", "go"],
        "pattern": "TODO.*HACK|FIXME.*temp|XXX|DELETEME",
        "message": "[debugging-residue] Temporary marker left in code",
        "exclude_patterns": [],
        "_tag": "auto:temp-markers",
    },
    {
        "extensions": ["ts", "tsx", "js", "jsx", "py", "rb"],
        "pattern": "(password|secret|api_key|token)\\s*=\\s*['\"][^'\"]+['\"]",
        "message": "[security] Hardcoded secret — use environment variables",
        "exclude_patterns": ["test", "spec", "mock", "fixture", "example", "\\.env\\.example"],
        "_tag": "auto:hardcoded-secrets",
    },
]

JS_TS_RULES = [
    {
        "extensions": ["ts", "tsx", "js", "jsx"],
        "pattern": "catch\\s*\\([^)]*\\)\\s*\\{\\s*\\}",
        "message": "[observability] Empty catch block swallows errors",
        "exclude_patterns": ["// intentionally empty"],
        "_tag": "auto:empty-catch",
    },
    {
        "extensions": ["ts", "tsx", "js", "jsx"],
        "pattern": "dangerouslySetInnerHTML",
        "message": "[security] dangerouslySetInnerHTML — XSS risk, sanitize input",
        "exclude_patterns": ["// sanitized"],
        "_tag": "auto:xss-risk",
    },
    {
        "extensions": ["ts", "tsx", "js", "jsx"],
        "pattern": "\\.(map|forEach)\\(async",
        "message": "[async-misuse] Async callback in .map/.forEach — use Promise.all() with .map() or for...of loop",
        "exclude_patterns": ["Promise\\.all"],
        "_tag": "auto:async-array-callback",
    },
    {
        "extensions": ["ts", "tsx", "js", "jsx"],
        "pattern": "new Function\\(|vm\\.runInNewContext|vm\\.createContext",
        "message": "[security] Code execution via Function constructor or vm — potential injection vector",
        "exclude_patterns": ["// nosec", "test"],
        "_tag": "auto:eval-variants",
    },
]

RUST_RULES = [
    {
        "extensions": ["rs"],
        "pattern": "unwrap\\(\\)",
        "message": "[error-boundary] .unwrap() can panic — use ? or handle the error",
        "exclude_patterns": ["test", "#\\[cfg\\(test"],
        "_tag": "auto:unwrap-panic",
    },
    {
        "extensions": ["rs"],
        "pattern": "unsafe\\s*\\{",
        "message": "[security] Unsafe block — document safety invariants",
        "exclude_patterns": ["// SAFETY:"],
        "_tag": "auto:unsafe-block",
    },
]

PYTHON_RULES = [
    {
        "extensions": ["py"],
        "pattern": "except:\\s*$|except Exception:\\s*$",
        "message": "[observability] Bare except or broad Exception catch — be specific and log",
        "exclude_patterns": ["# nosec", "pass  #"],
        "_tag": "auto:bare-except",
    },
    {
        "extensions": ["py"],
        "pattern": "eval\\(|exec\\(",
        "message": "[security] eval/exec usage — potential code injection",
        "exclude_patterns": ["# nosec", "test_"],
        "_tag": "auto:eval-exec",
    },
]

GO_RULES = [
    {
        "extensions": ["go"],
        "pattern": "err\\s*=.*[^{]$",
        "message": "[error-boundary] Error assigned but possibly not checked on next line",
        "exclude_patterns": ["_test\\.go", "if err"],
        "_tag": "auto:unchecked-error",
    },
]

RUBY_RULES = [
    {
        "extensions": ["rb"],
        "pattern": "rescue\\s*$|rescue Exception",
        "message": "[observability] Bare rescue or rescue Exception — be specific",
        "exclude_patterns": ["# rubocop:disable"],
        "_tag": "auto:bare-rescue",
    },
]

STACK_RULES = {
    "javascript": JS_TS_RULES,
    "typescript": JS_TS_RULES,
    "rust": RUST_RULES,
    "python": PYTHON_RULES,
    "go": GO_RULES,
    "ruby": RUBY_RULES,
}

STACK_LINTERS = {
    "javascript": "eslint",
    "typescript": "eslint",
    "rust": "clippy",
    "python": "ruff",
    "go": "",
    "ruby": "",
}


RULE_LIBRARY_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rule-library")


def load_rule_packs(stack: str, frameworks: list[str]) -> list[dict]:
    """Load matching rule packs from rule-library/ based on stack and frameworks."""
    pack_rules = []
    if not os.path.isdir(RULE_LIBRARY_DIR):
        return pack_rules

    for filename in sorted(os.listdir(RULE_LIBRARY_DIR)):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(RULE_LIBRARY_DIR, filename)
        try:
            with open(path) as f:
                pack = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        # Match by framework or stack
        pack_frameworks = pack.get("_frameworks", [])
        pack_stack = pack.get("_stack", "")

        # Skip opt-in packs — they must be added to lint-rules.json manually
        if pack.get("_opt_in"):
            continue

        matches = False
        if pack_frameworks and any(fw in frameworks for fw in pack_frameworks):
            matches = True
        if pack_stack and pack_stack == stack:
            matches = True

        if matches:
            for rule in pack.get("rules", []):
                pack_rules.append(rule)

    return pack_rules


def generate_lint_rules(stack: str, existing_path: str | None = None, frameworks: list[str] | None = None) -> dict:
    """Generate lint-rules.json, merging with existing if present."""
    rules = list(COMMON_RULES) + list(STACK_RULES.get(stack, []))

    # Add rules from matching rule packs
    pack_rules = load_rule_packs(stack, frameworks or [])
    rules.extend(pack_rules)

    existing_config = {}
    existing_rules = []
    if existing_path and os.path.exists(existing_path):
        try:
            with open(existing_path) as f:
                existing_config = json.load(f)
            existing_rules = existing_config.get("rules", [])
        except (json.JSONDecodeError, OSError):
            pass

    # Merge: keep existing rules, add new ones that don't have matching tags
    existing_tags = {r.get("_tag") for r in existing_rules if r.get("_tag")}
    merged_rules = list(existing_rules)
    for rule in rules:
        if rule["_tag"] not in existing_tags:
            merged_rules.append(rule)

    # Determine linter
    linter = existing_config.get("linter", STACK_LINTERS.get(stack, ""))
    linter_options = existing_config.get("linter_options", {})

    config = {"linter": linter, "rules": merged_rules}
    if linter_options:
        config["linter_options"] = linter_options

    # Special case: Rust needs PATH prefix for cc workaround
    if stack == "rust" and "linter_options" not in config:
        config["linter_options"] = {"path_prefix": "/usr/bin"}

    return config


# ---------------------------------------------------------------------------
# CLAUDE.md Testing Section
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# CLAUDE.md Section-Aware Merge
# ---------------------------------------------------------------------------

# Sections that generate.py can replace surgically.
# Must match headers in CLAUDE_MD_TEMPLATE below.
MANAGED_SECTIONS = {"## Commands", "## Testing"}


def parse_claude_md_sections(content: str) -> list[tuple[str, str]]:
    """Split CLAUDE.md into (header, body) sections.

    Sections start at lines matching `## Header` outside of fenced code blocks.
    Content before any ## header is stored with header="".
    Returns list of (header_line, section_body) tuples.
    """
    sections: list[tuple[str, str]] = []
    current_header = ""
    current_lines: list[str] = []
    in_code_fence = False

    for line in content.split("\n"):
        # Track fenced code blocks to avoid splitting on ## inside them
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence

        if not in_code_fence and re.match(r"^## \S", line):
            # Save previous section
            sections.append((current_header, "\n".join(current_lines)))
            current_header = line
            current_lines = []
        else:
            current_lines.append(line)

    # Save last section
    sections.append((current_header, "\n".join(current_lines)))
    return sections


def merge_claude_md(existing_content: str, new_section: str) -> str:
    """Surgically replace ## Commands and ## Testing in existing CLAUDE.md.

    Preserves all other sections. If the target sections don't exist,
    appends the new content at the end.
    """
    existing_sections = parse_claude_md_sections(existing_content)
    new_sections = parse_claude_md_sections(new_section)

    # Build lookup of new sections by header
    new_by_header = {h: body for h, body in new_sections if h in MANAGED_SECTIONS}

    # Replace matching sections in existing content
    replaced = set()
    result_sections = []
    for header, body in existing_sections:
        if header in new_by_header:
            result_sections.append((header, new_by_header[header]))
            replaced.add(header)
        else:
            result_sections.append((header, body))

    # Append any new managed sections that weren't in the existing file
    for header in MANAGED_SECTIONS:
        if header in new_by_header and header not in replaced:
            result_sections.append((header, new_by_header[header]))

    # Reconstruct content
    parts = []
    for header, body in result_sections:
        if header:
            parts.append(header + "\n" + body)
        else:
            parts.append(body)

    return "\n".join(parts)


CLAUDE_MD_TEMPLATE = """## Commands

```bash
# Test
{test_cmd}

# Lint
{lint_cmd}

# Type check
{typecheck_cmd}

# Build
{build_cmd}

# Security scan
{sa_cmd}
```

## Testing

- Run the test command after every code change
- Fix lint violations before committing
- Ensure type checking passes before pushing
- Before writing any helper function, search the codebase for its verb — if it exists, use it
- Write tests from the specification, not from reading the implementation
"""


def generate_claude_md_section(stack: str, audit_data: dict | None = None) -> str:
    """Generate CLAUDE.md testing section following claude-md-manager conventions.

    When audit_data is provided (via --audit), uses actual detected commands
    and package manager instead of generic templates.
    """
    cmds = {
        "javascript": {
            "test_cmd": "npm test",
            "lint_cmd": "npx eslint .",
            "typecheck_cmd": "# No type checking configured",
            "build_cmd": "npm run build",
            "sa_cmd": "npm audit",
        },
        "typescript": {
            "test_cmd": "npm test",
            "lint_cmd": "npx eslint .",
            "typecheck_cmd": "npx tsc --noEmit",
            "build_cmd": "npm run build",
            "sa_cmd": "npm audit",
        },
        "rust": {
            "test_cmd": "PATH=\"/usr/bin:$PATH\" cargo test",
            "lint_cmd": "PATH=\"/usr/bin:$PATH\" cargo clippy",
            "typecheck_cmd": "PATH=\"/usr/bin:$PATH\" cargo check",
            "build_cmd": "PATH=\"/usr/bin:$PATH\" cargo build",
            "sa_cmd": "cargo audit",
        },
        "python": {
            "test_cmd": "pytest",
            "lint_cmd": "ruff check .",
            "typecheck_cmd": "mypy .",
            "build_cmd": "# Interpreted — no build step",
            "sa_cmd": "bandit -r .",
        },
        "go": {
            "test_cmd": "go test ./...",
            "lint_cmd": "golangci-lint run",
            "typecheck_cmd": "go vet ./...",
            "build_cmd": "go build ./...",
            "sa_cmd": "govulncheck ./...",
        },
        "ruby": {
            "test_cmd": "bundle exec rspec",
            "lint_cmd": "bundle exec rubocop",
            "typecheck_cmd": "# No type checking configured",
            "build_cmd": "# Interpreted — no build step",
            "sa_cmd": "bundle exec bundler-audit",
        },
    }

    stack_cmds = cmds.get(stack, cmds["javascript"])

    # Override with actual commands from audit data when available
    if audit_data:
        audit_stack = audit_data.get("stack", {})
        scripts = audit_stack.get("scripts", {})
        pkg_mgr = audit_stack.get("package_manager", "npm")
        run_prefix = f"{pkg_mgr} run" if pkg_mgr != "bun" else "bun"

        # Use actual test command from audit
        if audit_stack.get("test_cmd"):
            stack_cmds["test_cmd"] = audit_stack["test_cmd"]
        elif "test" in scripts:
            stack_cmds["test_cmd"] = f"{run_prefix} test"

        # Detect E2E test runner separately
        e2e_cmd = None
        if scripts:
            for key in ["test:e2e", "e2e", "test:playwright", "test:integration"]:
                if key in scripts:
                    e2e_cmd = f"{run_prefix} {key}"
                    break
            # Also detect if test script invokes playwright
            test_script = scripts.get("test", "")
            if "playwright" in test_script and "vitest" not in test_script:
                e2e_cmd = stack_cmds["test_cmd"]
                # Check for a unit test script
                for key in ["test:unit", "test:vitest"]:
                    if key in scripts:
                        stack_cmds["test_cmd"] = f"{run_prefix} {key}"
                        break

        # Build command
        if "build" in scripts:
            stack_cmds["build_cmd"] = f"{run_prefix} build"

        # Lint command — use actual linter from audit
        linter = audit_stack.get("linter")
        if linter == "biome":
            npx = "bunx" if pkg_mgr == "bun" else "npx"
            stack_cmds["lint_cmd"] = f"{npx} biome check ."
        elif "lint" in scripts:
            stack_cmds["lint_cmd"] = f"{run_prefix} lint"

        # Emit E2E as a separate section if detected
        if e2e_cmd:
            e2e_section = f"\n# E2E tests\n{e2e_cmd}\n"
            # Insert after test command in template
            stack_cmds["test_cmd"] = stack_cmds["test_cmd"] + e2e_section

    return CLAUDE_MD_TEMPLATE.format(**stack_cmds)


# ---------------------------------------------------------------------------
# Hook Recommendations
# ---------------------------------------------------------------------------

def generate_hook_recommendations(stack: str, configs: dict | None = None) -> str:
    """Generate hook setup recommendations."""
    lines = ["## Hook Recommendations", ""]

    lines.append("### lint-on-write (PostToolUse)")
    lines.append("- Status: " + ("Active" if configs and configs.get("lint_on_write_hook") else "Not installed"))
    lines.append("- Install: `~/.claude/hooks/lint-on-write.py` (already exists in this setup)")
    lines.append("- Fires on: Write, Edit tools")
    lines.append("- Runs: standard linter + custom grep rules from `.claude/lint-rules.json`")
    lines.append("")

    lines.append("### Recommended Additional Hooks")
    lines.append("")
    lines.append("**test-on-fix** (PostToolUse → Write/Edit on test files)")
    lines.append("- Run the test suite when test files are modified")
    lines.append("- Catches broken tests immediately")
    lines.append("")
    lines.append("**type-check-on-write** (PostToolUse → Write/Edit)")

    if stack in ("typescript", "rust", "go"):
        lines.append(f"- Run type checker after edits (already fast for {stack})")
    elif stack == "python":
        lines.append("- Run mypy/pyright incrementally after edits")
    else:
        lines.append("- Consider adding if a type checker is configured")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_audit_data(path: str) -> dict | None:
    """Load audit JSON from --audit flag."""
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: could not load audit data from {path}: {e}", file=sys.stderr)
        return None


def main():
    root = os.getcwd()
    audit_data = None

    # Parse arguments
    args = list(sys.argv[1:])
    if "--audit" in args:
        idx = args.index("--audit")
        if idx + 1 < len(args):
            audit_data = load_audit_data(args[idx + 1])
            args = args[:idx] + args[idx + 2:]
        else:
            print("Error: --audit requires a path argument", file=sys.stderr)
            sys.exit(1)

    if args and os.path.isdir(args[0]):
        root = os.path.abspath(args[0])

    # Use audit data if available, otherwise detect stack
    if audit_data:
        stack = audit_data.get("stack", {}).get("primary", "unknown")
        root = audit_data.get("root", root)
        scripts = audit_data.get("stack", {}).get("scripts", {})
        pkg_mgr = audit_data.get("stack", {}).get("package_manager", "npm")
    else:
        scripts = {}
        pkg_mgr = "npm"
        stack = "unknown"
        if os.path.exists(os.path.join(root, "tsconfig.json")):
            stack = "typescript"
        elif os.path.exists(os.path.join(root, "package.json")):
            stack = "javascript"
        elif os.path.exists(os.path.join(root, "Cargo.toml")):
            stack = "rust"
        elif os.path.exists(os.path.join(root, "pyproject.toml")) or os.path.exists(os.path.join(root, "setup.py")):
            stack = "python"
        elif os.path.exists(os.path.join(root, "go.mod")):
            stack = "go"
        elif os.path.exists(os.path.join(root, "Gemfile")):
            stack = "ruby"

    # Check for existing configs
    lint_rules_path = os.path.join(root, ".claude/lint-rules.json")
    has_lint_rules = os.path.exists(lint_rules_path)
    has_lint_hook = os.path.exists(os.path.expanduser("~/.claude/hooks/lint-on-write.py"))

    configs = {"lint_on_write_hook": has_lint_hook}

    # Generate
    print(f"# Generated Configs for {stack} project")
    print(f"# Root: {root}")
    if audit_data:
        print(f"# Source: audit JSON (score {audit_data.get('total_score', '?')}/18)")
    print()

    # 1. lint-rules.json
    print("## .claude/lint-rules.json")
    print()
    if has_lint_rules:
        print(f"*Merging with existing config at `{lint_rules_path}`*")
        print()

    # Get frameworks for rule pack matching
    frameworks = []
    if audit_data:
        frameworks = audit_data.get("stack", {}).get("frameworks", [])
    else:
        # Basic framework detection when no audit data
        pkg_path = os.path.join(root, "package.json")
        if os.path.exists(pkg_path):
            try:
                with open(pkg_path) as f:
                    pkg = json.load(f)
                all_deps = {}
                all_deps.update(pkg.get("dependencies", {}))
                all_deps.update(pkg.get("devDependencies", {}))
                for fw in ["react", "vue", "svelte", "next", "express", "fastify"]:
                    if fw in all_deps:
                        frameworks.append(fw)
            except (json.JSONDecodeError, OSError):
                pass

    lint_config = generate_lint_rules(stack, lint_rules_path if has_lint_rules else None, frameworks)

    # Preserve _tag fields — they enable idempotent re-runs by preventing duplicate rules
    print("```json")
    print(json.dumps(lint_config, indent=2))
    print("```")
    print()
    print(f"Write to: `{root}/.claude/lint-rules.json`")
    print()

    # 2. CLAUDE.md section — use actual commands from audit data when available
    claude_section = generate_claude_md_section(stack, audit_data)
    claude_md_path = os.path.join(root, "CLAUDE.md")
    has_claude_md = os.path.exists(claude_md_path)

    print("## CLAUDE.md Testing Section")
    print()
    if has_claude_md:
        try:
            with open(claude_md_path) as f:
                existing_content = f.read()
            merged = merge_claude_md(existing_content, claude_section)
            print("*Section-aware merge with existing CLAUDE.md*")
            print("*Only `## Commands` and `## Testing` sections will be replaced; all other content preserved.*")
            print()
            print("```markdown")
            print(merged)
            print("```")
        except OSError:
            print(claude_section)
    else:
        print(claude_section)
    print()

    # 3. Hook recommendations
    hook_recs = generate_hook_recommendations(stack, configs)
    print(hook_recs)


if __name__ == "__main__":
    main()
