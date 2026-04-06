#!/usr/bin/env python3
"""Test Harness Auditor — Convention Extractor.

Parses CLAUDE.md (and optionally AGENTS.md) for constraint patterns like
"never X", "always Y", "use X instead of Y", "do not X", "prefer X over Y"
and generates candidate lint-rules.json entries from them.

Prints candidates as JSON to stdout. Claude presents them to the user for
approval before merging into .claude/lint-rules.json.
"""

import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Constraint patterns — ordered by specificity (most specific first)
# ---------------------------------------------------------------------------

# Each pattern extracts a named group "constraint" with the actionable text
CONSTRAINT_PATTERNS = [
    # "use X instead of Y" / "prefer X over Y"
    (re.compile(r"(?:^|\s)(?:use|prefer)\s+(.+?)\s+(?:instead of|over|rather than)\s+(.+?)(?:\.|$)", re.IGNORECASE | re.MULTILINE),
     "substitution"),
    # "never X" / "do not X" / "don't X" / "avoid X"
    (re.compile(r"(?:^[-*]\s*|^|\s)(?:never|do not|don't|don\u2019t|avoid|must not|must never|shall not)\s+(.+?)(?:\.|$)", re.IGNORECASE | re.MULTILINE),
     "prohibition"),
    # "always X" / "must X" / "shall X"
    (re.compile(r"(?:^[-*]\s*|^|\s)(?:always|must|shall|require)\s+(.+?)(?:\.|$)", re.IGNORECASE | re.MULTILINE),
     "requirement"),
]

# Words that signal the constraint is about code patterns (worth making a lint rule)
CODE_SIGNALS = [
    "import", "function", "class", "method", "variable", "const ", "let ",
    "return", "throw", "catch", "try", "async", "await", "console",
    "require", "export", "type ", "interface", "enum", "struct",
    "unwrap", "unsafe", "eval", "exec", "print", "debug", "log",
    "mock", "test", "spec", "assert", "expect",
    "file", "path", "dir", "folder",
    "api", "endpoint", "route", "handler",
    "sql", "query", "database", "migration",
    "env", "secret", "key", "token", "password",
    "todo", "fixme", "hack", "xxx",
]


def extract_constraints(text: str) -> list[dict]:
    """Extract constraint statements from markdown text."""
    constraints = []
    seen = set()

    for pattern, kind in CONSTRAINT_PATTERNS:
        for match in pattern.finditer(text):
            full = match.group(0).strip().rstrip(".")
            # Deduplicate by normalized text
            key = full.lower().strip("- *")
            if key in seen or len(key) < 10:
                continue
            seen.add(key)

            groups = match.groups()
            constraint = {
                "kind": kind,
                "raw": full,
                "groups": list(groups),
            }
            constraints.append(constraint)

    return constraints


def is_code_related(constraint: dict) -> bool:
    """Check if a constraint is about code patterns (vs process/workflow)."""
    text = constraint["raw"].lower()
    return any(signal in text for signal in CODE_SIGNALS)


def constraint_to_lint_rule(constraint: dict, extensions: list[str]) -> dict | None:
    """Attempt to convert a constraint into a lint-rules.json entry.

    Returns None if the constraint can't be mechanically converted to a grep pattern.
    """
    kind = constraint["kind"]
    raw = constraint["raw"]
    groups = constraint["groups"]

    if kind == "substitution" and len(groups) >= 2:
        # "use X instead of Y" -> grep for Y, message says use X
        preferred, deprecated = groups[0].strip(), groups[1].strip()
        # Only convert if the deprecated term looks greppable (short, concrete)
        if len(deprecated.split()) <= 4 and len(deprecated) < 60:
            # Build a simple pattern from the deprecated term
            pattern = re.escape(deprecated)
            return {
                "extensions": extensions,
                "pattern": pattern,
                "message": f"[convention] {raw.strip()}",
                "exclude_patterns": [],
                "_tag": f"auto:convention:{_slugify(deprecated[:30])}",
            }

    elif kind == "prohibition":
        # "never X" -> try to extract a greppable term from X
        text = groups[0].strip() if groups else ""
        greppable = _extract_greppable_term(text)
        if greppable:
            return {
                "extensions": extensions,
                "pattern": re.escape(greppable),
                "message": f"[convention] {raw.strip()}",
                "exclude_patterns": [],
                "_tag": f"auto:convention:{_slugify(greppable[:30])}",
            }

    # Requirements ("always X") are harder to enforce via grep — skip
    return None


def _extract_greppable_term(text: str) -> str | None:
    """Try to find a concrete, greppable code term in a constraint phrase."""
    # Look for backtick-quoted terms first
    backtick = re.findall(r"`([^`]+)`", text)
    if backtick:
        return backtick[0]

    # Look for quoted terms
    quoted = re.findall(r'"([^"]+)"', text) + re.findall(r"'([^']+)'", text)
    if quoted:
        return quoted[0]

    # Look for known code patterns
    for signal in CODE_SIGNALS:
        if signal in text.lower():
            # Extract the phrase around the signal
            words = text.split()
            for i, w in enumerate(words):
                if signal.strip() in w.lower():
                    # Return 1-3 word phrase around the match
                    start = max(0, i)
                    end = min(len(words), i + 2)
                    candidate = " ".join(words[start:end])
                    if len(candidate) >= 3:
                        return candidate

    return None


def _slugify(text: str) -> str:
    """Convert text to a slug for tag naming."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]


def detect_extensions(root: str) -> list[str]:
    """Detect file extensions to apply rules to, based on project stack."""
    extensions = []
    if os.path.exists(os.path.join(root, "tsconfig.json")):
        extensions = ["ts", "tsx", "js", "jsx"]
    elif os.path.exists(os.path.join(root, "package.json")):
        extensions = ["js", "jsx", "ts", "tsx"]
    elif os.path.exists(os.path.join(root, "Cargo.toml")):
        extensions = ["rs"]
    elif os.path.exists(os.path.join(root, "pyproject.toml")) or os.path.exists(os.path.join(root, "setup.py")):
        extensions = ["py"]
    elif os.path.exists(os.path.join(root, "go.mod")):
        extensions = ["go"]
    elif os.path.exists(os.path.join(root, "Gemfile")):
        extensions = ["rb"]
    else:
        extensions = ["ts", "tsx", "js", "jsx", "py", "rs", "rb", "go"]
    return extensions


def main():
    root = os.getcwd()
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        root = os.path.abspath(sys.argv[1])

    # Collect text from CLAUDE.md and AGENTS.md
    sources = []
    for filename in ["CLAUDE.md", "AGENTS.md"]:
        path = os.path.join(root, filename)
        if os.path.exists(path):
            try:
                with open(path) as f:
                    sources.append((filename, f.read()))
            except OSError:
                pass

    if not sources:
        print(json.dumps({"error": "No CLAUDE.md or AGENTS.md found", "candidates": []}))
        return

    extensions = detect_extensions(root)

    # Extract and convert
    all_candidates = []
    for filename, text in sources:
        constraints = extract_constraints(text)
        for c in constraints:
            if not is_code_related(c):
                continue
            rule = constraint_to_lint_rule(c, extensions)
            if rule:
                rule["_source"] = filename
                all_candidates.append(rule)

    # Deduplicate by tag
    seen_tags = set()
    unique = []
    for c in all_candidates:
        if c["_tag"] not in seen_tags:
            seen_tags.add(c["_tag"])
            unique.append(c)

    output = {
        "source_files": [s[0] for s in sources],
        "constraints_found": sum(len(extract_constraints(t)) for _, t in sources),
        "code_related": len(all_candidates),
        "candidates": unique,
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
