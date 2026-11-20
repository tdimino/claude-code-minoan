"""Check an answer's quoted citations against the files that were packed. Standard library only.

A delegate with no tools can still misquote. Personas that cite write

    [path/to/file.md:L12-L14] "the words exactly as they stand in the file"

and this module compares each quotation with those lines of the file named in the run's manifest. It checks that
the words are there; whether they support the claim is for the reader to judge.

Verdicts: verified (in the cited lines), misplaced (elsewhere in that file), not_found, unknown_file (not in the
pack), out_of_range (no such lines), file_changed (the file's hash differs from the manifest's, so nothing is judged).
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

LINE_SLACK = 1  # a quotation one line off its cited span still counts as verified

CITATION = re.compile(
    r"\[(?P<path>[^\[\]\n]+?):L(?P<start>\d+)(?:\s*[-–]\s*L?(?P<end>\d+))?\]"
    r"(?:\s*(?:[\"“](?P<quote>[^\"”\n]+)[\"”]))?")
ELLIPSIS = re.compile(r"\s*(?:\.\.\.|…|\[\.\.\.\]|\[…\])\s*")


@dataclass
class Check:
    path: str
    start: int
    end: int
    quote: str | None
    verdict: str


def normalise(text: str) -> str:
    """NFC, straight quotes, single spaces: differences a copyist introduces without changing the words."""
    text = unicodedata.normalize("NFC", text)
    text = text.translate({0x2018: "'", 0x2019: "'", 0x201C: '"', 0x201D: '"', 0x00A0: " "})
    return re.sub(r"\s+", " ", text).strip()


def _contains(haystack: str, quote: str) -> bool:
    """The quotation's pieces, split at any ellipsis, occur in order."""
    position = 0
    for piece in (p for p in ELLIPSIS.split(quote) if p.strip()):
        found = haystack.find(piece.strip(), position)
        if found < 0:
            return False
        position = found + len(piece.strip())
    return True


def check_answer(answer: str, manifest: dict) -> list[Check]:
    files = {f["path"]: f for f in manifest.get("files", [])}
    cache: dict[str, list[str] | None] = {}

    def lines_of(path: str) -> list[str] | None:
        if path not in cache:
            entry = files[path]
            try:
                data = Path(entry["abs"]).read_bytes()
            except OSError:
                cache[path] = None
            else:
                same = hashlib.sha256(data).hexdigest() == entry["sha256"]
                cache[path] = data.decode("utf-8", "replace").splitlines() if same else None
        return cache[path]

    checks: list[Check] = []
    for m in CITATION.finditer(answer):
        path = m["path"].strip().strip("`")
        start = int(m["start"])
        end = int(m["end"] or start)
        quote = m["quote"]
        if path not in files:
            checks.append(Check(path, start, end, quote, "unknown_file"))
            continue
        lines = lines_of(path)
        if lines is None:
            checks.append(Check(path, start, end, quote, "file_changed"))
            continue
        if start < 1 or end < start or start > len(lines):
            checks.append(Check(path, start, end, quote, "out_of_range"))
            continue
        if quote is None:
            checks.append(Check(path, start, end, None, "located"))
            continue
        wanted = normalise(quote)
        span = normalise("\n".join(lines[max(start - 1 - LINE_SLACK, 0):end + LINE_SLACK]))
        if _contains(span, wanted):
            verdict = "verified"
        elif _contains(normalise("\n".join(lines)), wanted):
            verdict = "misplaced"
        else:
            verdict = "not_found"
        checks.append(Check(path, start, end, quote, verdict))
    return checks


def summarise(checks: list[Check]) -> tuple[str, list[str]]:
    """('14/15', one line per citation that did not verify). Citations without a quotation are not counted."""
    quoted = [c for c in checks if c.quote is not None or c.verdict in ("unknown_file", "out_of_range")]
    good = sum(1 for c in quoted if c.verdict == "verified")
    problems = []
    for c in checks:
        if c.verdict in ("verified", "located"):
            continue
        span = f"L{c.start}" if c.end == c.start else f"L{c.start}-L{c.end}"
        words = f' "{c.quote[:70]}"' if c.quote else ""
        problems.append(f"{c.verdict:<13} [{c.path}:{span}]{words}")
    return f"{good}/{len(quoted)}", problems


def manifest_for(output: Path) -> dict:
    """The manifest written beside an output file by gemini_exec.py."""
    return json.loads(output.with_suffix(".manifest.json").read_text(encoding="utf-8"))
