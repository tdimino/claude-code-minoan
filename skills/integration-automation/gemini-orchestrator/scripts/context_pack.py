"""Context packing for gemini-orchestrator. Standard library only; knows files and nothing about the network.

A delegate with no tools sees only what the request carries, so this module gathers the files, numbers their lines
(so answers can cite path:line), hashes them into a manifest (so citations can be checked later), estimates tokens
from bytes, and scans the outgoing text for secrets and for addresses that may not leave the machine.
"""
from __future__ import annotations

import base64
import glob
import hashlib
import importlib.util
import json
import math
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

MAX_FILE_BYTES = 2 * 1024 * 1024
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".subdaimon-output", ".beans"}
EGRESS_HOOK = Path.home() / ".claude/hooks/block-email-egress.py"

FORBIDDEN_NAME = re.compile(
    r"(^|/)(\.env(\..+)?|[^/]*\.env|secrets\.[^/]+|id_(rsa|dsa|ecdsa|ed25519)|[^/]*\.(pem|p12|pfx|key)|"
    r"credentials\.json|\.netrc|\.npmrc|\.pypirc)$")

SECRET_PATTERNS = [
    ("OpenRouter key", re.compile(r"sk-or-v1-[A-Za-z0-9]{20,}")),
    ("Anthropic key", re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")),
    ("API key (sk-)", re.compile(r"\bsk-[A-Za-z0-9_-]{32,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("assigned secret", re.compile(
        r"\b[A-Za-z0-9_]*(API_KEY|SECRET|TOKEN|PASSWORD)\b\s*[=:]\s*['\"]?[A-Za-z0-9_\-/+]{16,}", re.I)),
]

IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
               ".gif": "image/gif"}
# Pilot, 2026-11-20, Hydrogen: a 612x792 page image cost about 1,125 tokens and a three-page text PDF about 1,010 a
# page with the native engine. One sample each, so both constants sit above the measurement.
TOKENS_PER_IMAGE = 1300
TOKENS_PER_PDF_PAGE = 1100
# Bytes per token by content class, set just under what the pilot measured on Gemini 4 Hydrogen (2026-11-20, one
# sample each, numbered lines included): English prose 3.01, indented JSON 2.06, pointed Hebrew 2.08, JSON with
# transliteration 2.20. calibration.json in the data folder overrides these.
# Source code, from two real runs the same day (JavaScript, then Python), measured 2.66 and 2.80.
BYTES_PER_TOKEN = {"prose": 2.9, "code": 2.5, "dense": 1.95, "mixed": 2.0}


@dataclass
class PackedFile:
    path: str      # as shown to the delegate and cited back: relative to the working directory when inside it
    abs: Path
    text: str
    sha256: str
    bytes: int
    lines: int


@dataclass
class Finding:
    path: str
    line: int
    kind: str      # what was found; never the matched text itself


# --- gathering --------------------------------------------------------------------------------------------------

def _display(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(p.resolve())


def _files_under(d: Path) -> list[Path]:
    """Files of a directory, honouring .gitignore when the directory is inside a git repository."""
    try:
        out = subprocess.run(["git", "-C", str(d), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                             capture_output=True, timeout=60)
        if out.returncode == 0:
            return sorted(d / name for name in out.stdout.decode("utf-8", "replace").split("\0") if name)
    except (OSError, subprocess.SubprocessError):
        pass
    found = []
    for root, dirs, names in os.walk(d):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS and not x.startswith("."))
        found.extend(Path(root) / n for n in sorted(names))
    return found


def collect(paths: list[str], *, allow_large: bool = False) -> tuple[list[PackedFile], list[tuple[str, str]]]:
    """Paths, directories and globs -> (files to pack, [(path, why it was left out)]).

    A forbidden name (.env, a private key) given explicitly raises; one met inside a directory is left out and listed.
    """
    explicit: list[Path] = []
    walked: list[Path] = []
    for raw in paths:
        matches = [Path(m) for m in sorted(glob.glob(raw, recursive=True))] if glob.has_magic(raw) else [Path(raw)]
        for p in matches:
            if not p.exists():
                raise FileNotFoundError(f"no such file or directory: {raw}")
            if p.is_dir():
                walked.extend(_files_under(p))
            else:
                explicit.append(p)

    files: list[PackedFile] = []
    skipped: list[tuple[str, str]] = []
    seen: set[Path] = set()
    for p, was_explicit in [(p, True) for p in explicit] + [(p, False) for p in walked]:
        real = p.resolve()
        if real in seen or not p.is_file():
            continue
        seen.add(real)
        shown = _display(p)
        if any(part in SKIP_DIRS for part in p.parts):
            skipped.append((shown, "inside a skipped folder"))
            continue
        if FORBIDDEN_NAME.search(shown.replace(os.sep, "/")):
            if was_explicit:
                raise PermissionError(f"{shown} looks like a credentials file and is never packed")
            skipped.append((shown, "credentials file"))
            continue
        size = p.stat().st_size
        if size > MAX_FILE_BYTES and not allow_large:
            skipped.append((shown, f"{size:,} bytes, over the 2 MB limit (--allow-large)"))
            continue
        data = p.read_bytes()
        if b"\0" in data[:8192]:
            skipped.append((shown, "binary"))
            continue
        text = data.decode("utf-8", "replace")
        files.append(PackedFile(shown, real, text, hashlib.sha256(data).hexdigest(), size,
                                text.count("\n") + (0 if text.endswith("\n") or not text else 1)))
    files.sort(key=lambda f: f.path)  # a stable order keeps a cached prefix stable between calls
    return files, skipped


def render(files: list[PackedFile]) -> str:
    """The pack as the delegate reads it: each file under its path, every line numbered."""
    if not files:
        return ""
    out = [f'<context_pack files="{len(files)}">']
    for f in files:
        out.append(f'<file path="{f.path}" lines="{f.lines}">')
        out.extend(f"{n}| {line}" for n, line in enumerate(f.text.splitlines(), 1))
        out.append("</file>")
    out.append("</context_pack>")
    return "\n".join(out)


def manifest(files: list[PackedFile]) -> dict:
    return {"cwd": str(Path.cwd()),
            "files": [{"path": f.path, "abs": str(f.abs), "sha256": f.sha256, "bytes": f.bytes, "lines": f.lines}
                      for f in files]}


# --- egress guard -----------------------------------------------------------------------------------------------

def deny_addresses(extra: list[str] | None = None) -> list[str]:
    """Addresses that may not leave this machine: the egress hook's list, git's user.email, and config extras.

    Read at run time, so no address is written into this skill.
    """
    found: set[str] = set(a.lower() for a in (extra or []) if a)
    if EGRESS_HOOK.exists():
        try:
            spec = importlib.util.spec_from_file_location("block_email_egress", EGRESS_HOOK)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            found.update(a.lower() for a in getattr(module, "ADDRESSES", ()))
        except Exception:  # a broken hook must not disable the guard's other sources
            pass
    for scope in (["--global"], []):
        try:
            out = subprocess.run(["git", "config", *scope, "--get", "user.email"], capture_output=True, text=True,
                                 timeout=10)
            if out.returncode == 0 and "@" in out.stdout:
                found.add(out.stdout.strip().lower())
        except (OSError, subprocess.SubprocessError):
            pass
    return sorted(found)


def scan(texts: list[tuple[str, str]], addresses: list[str], *, exempt: set[str] | None = None) -> list[Finding]:
    """Secrets and denied addresses in the outgoing text. `exempt` paths skip the secret patterns only."""
    exempt = exempt or set()
    needles = [a for a in addresses] + [a.replace("@", "%40") for a in addresses]
    findings: list[Finding] = []
    for label, text in texts:
        for n, line in enumerate(text.splitlines(), 1):
            low = line.lower()
            if any(needle in low for needle in needles):
                findings.append(Finding(label, n, "denied email address"))
            if label in exempt:
                continue
            for kind, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(Finding(label, n, kind))
                    break
    return findings


def redact(text: str, addresses: list[str]) -> str:
    for a in addresses:
        for needle in (a, a.replace("@", "%40")):
            text = re.sub(re.escape(needle), "[email]", text, flags=re.I)
    return text


# --- estimates --------------------------------------------------------------------------------------------------

def _ratios() -> dict:
    ratios = dict(BYTES_PER_TOKEN)
    calibration = Path(os.environ.get("GEMINI_ORCH_DATA_DIR", Path.home() / ".claude/data/gemini-orchestrator"))
    try:
        ratios.update(json.loads((calibration / "calibration.json").read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        pass
    return ratios


def estimate_tokens(text: str) -> int:
    """Tokens from bytes, by content class.

    mixed: over 5% non-ASCII bytes (Hebrew, diacritics). prose: ASCII that is at least 80% letters and spaces (the
    pilot's Markdown sample, 84%, measured 3.01 bytes per token). code: 62% to 80% (source files ran 71% to 79%).
    dense: the rest (indented JSON, tables), where digits and punctuation make tokens short.
    """
    if not text:
        return 0
    data = text.encode("utf-8")
    non_ascii = sum(1 for b in data if b > 127)
    if non_ascii / len(data) > 0.05:
        kind = "mixed"
    else:
        wordy = sum(1 for ch in text if ch.isalpha() or ch == " ")
        share = wordy / len(text)
        kind = "prose" if share >= 0.80 else "code" if share >= 0.62 else "dense"
    return math.ceil(len(data) / _ratios()[kind])


def attachment(path: str) -> tuple[dict, int, str]:
    """A local image or PDF -> (content part, estimated tokens, kind)."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"no such attachment: {path}")
    data = p.read_bytes()
    encoded = base64.b64encode(data).decode("ascii")
    suffix = p.suffix.lower()
    if suffix in IMAGE_TYPES:
        part = {"type": "image_url", "image_url": {"url": f"data:{IMAGE_TYPES[suffix]};base64,{encoded}"}}
        return part, TOKENS_PER_IMAGE, "image"
    if suffix == ".pdf":
        pages = max(len(re.findall(rb"/Type\s*/Page(?![s\w])", data)), 1)
        part = {"type": "file", "file": {"filename": p.name, "file_data": f"data:application/pdf;base64,{encoded}"}}
        return part, pages * TOKENS_PER_PDF_PAGE, "pdf"
    raise ValueError(f"{p.name}: only images and PDFs can be attached so far; audio and video wait on pilot "
                     f"question P8")
