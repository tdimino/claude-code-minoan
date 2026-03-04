"""
Phone/ID → userModel bridge.

Scans ~/.claude/userModels/*/ for YAML frontmatter phone: fields and builds a
lookup index. Resolves E.164 phone numbers (SMS) or Slack user IDs to the rich
persona markdown files maintained by the user-model-builder skill.

Index is cached per-process. Thread-safe (immutable dict after init).
"""

import os
import re
from pathlib import Path
from typing import Optional

USER_MODELS_DIR = Path(os.path.expanduser("~/.claude/userModels"))

# Module-level cache — built once per process
_phone_index: Optional[dict[str, Path]] = None
_email_index: Optional[dict[str, Path]] = None


def _parse_frontmatter_field(content: str, field: str) -> Optional[str]:
    """Extract a single field from YAML frontmatter (between --- markers)."""
    if not content.startswith("---"):
        return None
    end = content.find("\n---", 3)
    if end == -1:
        return None
    raw = content[3:end]
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith(f"{field}:"):
            value = line[len(field) + 1:].strip().strip('"').strip("'")
            if value and value != "~":
                return value
    return None


def _normalize_phone(phone: str) -> str:
    """Strip non-digit chars except leading +, ensure E.164-ish format."""
    if not phone:
        return ""
    # Keep leading +, strip everything else that isn't a digit
    if phone.startswith("+"):
        return "+" + re.sub(r"[^\d]", "", phone[1:])
    return re.sub(r"[^\d]", "", phone)


def build_phone_index() -> dict[str, Path]:
    """Scan ~/.claude/userModels/*/ for phone: fields in frontmatter.

    Returns: {"+17327595647": Path("~/.claude/userModels/tom/tomModel.md"), ...}
    """
    index: dict[str, Path] = {}
    if not USER_MODELS_DIR.is_dir():
        return index

    for model_dir in USER_MODELS_DIR.iterdir():
        if not model_dir.is_dir() or model_dir.name.startswith("."):
            continue
        # Look for *Model.md files (convention: tomModel.md, maryModel.md, etc.)
        for md_file in model_dir.glob("*Model.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            phone = _parse_frontmatter_field(content, "phone")
            if phone:
                normalized = _normalize_phone(phone)
                if normalized:
                    index[normalized] = md_file
    return index


def build_email_index() -> dict[str, Path]:
    """Scan ~/.claude/userModels/*/ for email: fields in frontmatter."""
    index: dict[str, Path] = {}
    if not USER_MODELS_DIR.is_dir():
        return index

    for model_dir in USER_MODELS_DIR.iterdir():
        if not model_dir.is_dir() or model_dir.name.startswith("."):
            continue
        for md_file in model_dir.glob("*Model.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            email = _parse_frontmatter_field(content, "email")
            if email:
                index[email.lower()] = md_file
    return index


def _ensure_indexes():
    """Build indexes on first access."""
    global _phone_index, _email_index
    if _phone_index is None:
        _phone_index = build_phone_index()
    if _email_index is None:
        _email_index = build_email_index()


def resolve_by_phone(phone: str) -> Optional[str]:
    """Return the full userModel markdown for a phone number, or None.

    Phone number should be E.164 format (e.g. +17327595647).
    """
    _ensure_indexes()
    normalized = _normalize_phone(phone)
    path = _phone_index.get(normalized)
    if path is None:
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def resolve_by_email(email: str) -> Optional[str]:
    """Return the full userModel markdown by email, or None."""
    _ensure_indexes()
    path = _email_index.get(email.lower())
    if path is None:
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def resolve_by_slack_id(slack_id: str) -> Optional[str]:
    """Return userModel markdown by matching userId in frontmatter, or None.

    Falls back to email-based lookup if userId not found.
    """
    _ensure_indexes()
    # Direct scan for userId match (small N, fast enough)
    if not USER_MODELS_DIR.is_dir():
        return None

    for model_dir in USER_MODELS_DIR.iterdir():
        if not model_dir.is_dir() or model_dir.name.startswith("."):
            continue
        for md_file in model_dir.glob("*Model.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            user_id = _parse_frontmatter_field(content, "slackId")
            if user_id and user_id == slack_id:
                return content
    return None


def get_display_name_for_phone(phone: str) -> Optional[str]:
    """Return the display name from a phone-matched userModel's frontmatter."""
    _ensure_indexes()
    normalized = _normalize_phone(phone)
    path = _phone_index.get(normalized)
    if path is None:
        return None
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return _parse_frontmatter_field(content, "subject") or _parse_frontmatter_field(content, "title")


def invalidate_cache():
    """Force rebuild of indexes on next access. Useful after adding new userModels."""
    global _phone_index, _email_index
    _phone_index = None
    _email_index = None
