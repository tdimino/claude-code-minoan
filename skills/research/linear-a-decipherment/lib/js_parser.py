"""Parse JavaScript Map declarations into Python dicts.

Handles the specific format of LinearAInscriptions.js and semiticLexicon.js:
  var inscriptions = new Map([["KEY", { ... }], ...]);
  SEMITIC.gordon = new Map([["KEY", { ... }], ...]);

Uses regex + brace-depth tracking. No external dependencies.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class JSParseError(Exception):
    """Raised when JS Map extraction fails."""


EXPECTED_INSCRIPTION_COUNT = 1721


def parse_inscriptions(filepath: Path) -> dict[str, dict[str, Any]]:
    """Parse LinearAInscriptions.js into {name: {fields...}} dict."""
    text = filepath.read_text(encoding="utf-8")
    # Find the Map array start
    start = text.find("new Map([")
    if start == -1:
        raise JSParseError("No 'new Map([' found in inscription file")
    start = text.index("[", start + len("new Map")) + 1

    entries = _extract_map_entries(text, start)

    if len(entries) < EXPECTED_INSCRIPTION_COUNT * 0.95:
        raise JSParseError(
            f"Extracted only {len(entries)} inscriptions "
            f"(expected ~{EXPECTED_INSCRIPTION_COUNT})"
        )
    return entries


def parse_lexicon(filepath: Path, map_name: str = "gordon") -> dict[str, dict[str, Any]]:
    """Parse a SEMITIC.* Map from semiticLexicon.js.

    map_name: 'gordon' or 'yasharMana'
    """
    text = filepath.read_text(encoding="utf-8")

    # Find SEMITIC.{map_name} = new Map([
    pattern = rf"SEMITIC\.{re.escape(map_name)}\s*=\s*new\s+Map\(\["
    match = re.search(pattern, text)
    if not match:
        raise JSParseError(f"No SEMITIC.{map_name} Map found")

    start = match.end()
    return _extract_map_entries(text, start)


def _extract_map_entries(text: str, start: int) -> dict[str, dict[str, Any]]:
    """Extract all [key, value] entries from a Map array starting at position."""
    entries: dict[str, dict[str, Any]] = {}
    pos = start

    while pos < len(text):
        # Skip whitespace and comments
        pos = _skip_ws_comments(text, pos)
        if pos >= len(text):
            break

        ch = text[pos]
        if ch == "]":
            break  # End of Map array
        if ch == ",":
            pos += 1
            continue

        if ch != "[":
            pos += 1
            continue

        # Found an entry start: ["KEY", { ... }]
        pos += 1  # skip [

        # Extract the key string
        pos = _skip_ws_comments(text, pos)
        key, pos = _extract_js_string(text, pos)
        if key is None:
            pos += 1
            continue

        # Skip to the value object
        pos = _skip_ws_comments(text, pos)
        if pos < len(text) and text[pos] == ",":
            pos += 1
        pos = _skip_ws_comments(text, pos)

        # Extract the value object
        if pos < len(text) and text[pos] == "{":
            obj_str, pos = _extract_braced(text, pos)
            try:
                value = _parse_js_object(obj_str)
                entries[key] = value
            except (json.JSONDecodeError, ValueError):
                pass  # Skip malformed entries
        else:
            # Skip to end of this entry
            pos = _find_closing_bracket(text, pos)

        # Skip closing ]
        pos = _skip_ws_comments(text, pos)
        if pos < len(text) and text[pos] == "]":
            pos += 1

    return entries


def _skip_ws_comments(text: str, pos: int) -> int:
    """Skip whitespace and // or /* */ comments."""
    while pos < len(text):
        if text[pos] in " \t\n\r":
            pos += 1
        elif text[pos:pos + 2] == "//":
            nl = text.find("\n", pos)
            pos = nl + 1 if nl != -1 else len(text)
        elif text[pos:pos + 2] == "/*":
            end = text.find("*/", pos)
            pos = end + 2 if end != -1 else len(text)
        else:
            break
    return pos


def _extract_js_string(text: str, pos: int) -> tuple[str | None, int]:
    """Extract a quoted string starting at pos. Returns (string, new_pos)."""
    if pos >= len(text) or text[pos] not in '"\'':
        return None, pos

    quote = text[pos]
    pos += 1
    chars = []
    while pos < len(text):
        ch = text[pos]
        if ch == "\\":
            pos += 1
            if pos < len(text):
                chars.append(text[pos])
                pos += 1
        elif ch == quote:
            pos += 1
            return "".join(chars), pos
        else:
            chars.append(ch)
            pos += 1

    return "".join(chars), pos


def _extract_braced(text: str, pos: int) -> tuple[str, int]:
    """Extract a {...} block respecting nesting and strings."""
    if text[pos] != "{":
        return "", pos

    depth = 0
    start = pos
    in_string = False
    string_char = ""

    while pos < len(text):
        ch = text[pos]

        if in_string:
            if ch == "\\" and pos + 1 < len(text):
                pos += 2
                continue
            if ch == string_char:
                in_string = False
        else:
            if ch in '"\'':
                in_string = True
                string_char = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    pos += 1
                    return text[start:pos], pos

        pos += 1

    return text[start:pos], pos


def _find_closing_bracket(text: str, pos: int) -> int:
    """Find the next ] at depth 0."""
    depth = 0
    while pos < len(text):
        ch = text[pos]
        if ch == "[":
            depth += 1
        elif ch == "]":
            if depth == 0:
                return pos
            depth -= 1
        pos += 1
    return pos


def _parse_js_object(obj_str: str) -> dict[str, Any]:
    """Convert a JS object literal to a Python dict via JSON."""
    s = obj_str

    # Remove JS comments inside object
    s = re.sub(r"//[^\n]*", "", s)

    # Handle ES6 Unicode escapes: \u{XXXX} -> \uXXXX
    s = re.sub(r"\\u\\{([0-9a-fA-F]+)\\}", lambda m: f"\\u{m.group(1).zfill(4)}", s)

    # Fix invalid JSON escapes: \' -> ' (valid in JS, not in JSON)
    s = s.replace("\\'", "'")

    # Convert single-quoted strings to double-quoted
    s = _single_to_double_quotes(s)

    # Remove trailing commas before } or ]
    s = re.sub(r",\s*([}\\]])", r"\1", s)

    # Quote unquoted keys — must run AFTER single-to-double conversion
    # so all strings are double-quoted and we can skip them properly
    s = _quote_unquoted_keys(s)

    return json.loads(s)


def _quote_unquoted_keys(s: str) -> str:
    """Quote unquoted JS object keys, skipping over string contents."""
    result = []
    i = 0
    while i < len(s):
        if s[i] == '"':
            # Skip over double-quoted string verbatim
            result.append(s[i])
            i += 1
            while i < len(s) and s[i] != '"':
                if s[i] == "\\" and i + 1 < len(s):
                    result.append(s[i])
                    result.append(s[i + 1])
                    i += 2
                else:
                    result.append(s[i])
                    i += 1
            if i < len(s):
                result.append(s[i])  # closing "
                i += 1
        elif s[i].isalpha() or s[i] == '_':
            # Potential unquoted key — collect the word
            word_start = i
            while i < len(s) and (s[i].isalnum() or s[i] == '_'):
                i += 1
            word = s[word_start:i]
            # Check if followed by colon (skip whitespace)
            j = i
            while j < len(s) and s[j] in ' \t':
                j += 1
            if j < len(s) and s[j] == ':':
                # It's an unquoted key — quote it
                result.append('"')
                result.append(word)
                result.append('"')
            else:
                # Not a key (e.g. bare identifier like true/false/null)
                result.append(word)
        else:
            result.append(s[i])
            i += 1
    return "".join(result)


def _single_to_double_quotes(s: str) -> str:
    """Convert single-quoted string values to double-quoted for JSON.

    Skips over already-double-quoted strings so apostrophes inside them
    (e.g. d'Athènes) are not misinterpreted as single-quote delimiters.
    """
    result = []
    i = 0
    while i < len(s):
        if s[i] == '"':
            # Already double-quoted — pass through verbatim
            result.append(s[i])
            i += 1
            while i < len(s) and s[i] != '"':
                if s[i] == "\\" and i + 1 < len(s):
                    result.append(s[i])
                    result.append(s[i + 1])
                    i += 2
                else:
                    result.append(s[i])
                    i += 1
            if i < len(s):
                result.append(s[i])  # closing "
                i += 1
        elif s[i] == "'":
            # Single-quoted string — convert to double
            result.append('"')
            i += 1
            while i < len(s) and s[i] != "'":
                if s[i] == "\\":
                    result.append(s[i])
                    i += 1
                    if i < len(s):
                        result.append(s[i])
                        i += 1
                elif s[i] == '"':
                    result.append('\\"')
                    i += 1
                else:
                    result.append(s[i])
                    i += 1
            result.append('"')
            if i < len(s):
                i += 1  # skip closing '
        else:
            result.append(s[i])
            i += 1
    return "".join(result)
