"""
Three-tier SQLite memory for SMS conversations.

Adapted from the Slack daemon's split modules (soul_memory.py, working_memory.py,
user_models.py) into a single file for the SMS channel.

Tier 1: Working memory — per-conversation message history + cognitive outputs
Tier 2: User models — per-phone-number personality profiles
Tier 3: Soul memory — cross-conversation soul state (emotional state, topic, etc.)

Soul-aware routing: if ~/.claudicle/soul/soul.md exists, cognitive memory
(working memory, user models, soul memory) routes through the canonical
Claudicle daemon module. Channel-specific tables (replied_messages, sms_sessions)
always stay local.

Thread-safe via threading.local() for SQLite connections.
"""

import json
import os
import sqlite3
import sys
import threading
import time
from pathlib import Path
from typing import Optional

# Add shared skills directory to path for imports
_SHARED_DIR = str(Path(__file__).parent.parent.parent / "shared")
if _SHARED_DIR not in sys.path:
    sys.path.insert(0, _SHARED_DIR)

import claudicle_memory as _cm
import usermodel_resolver as _ur

DB_PATH = Path(__file__).parent.parent / "data" / "sms_memory.db"

# ── Defaults ─────────────────────────────────────────────────────────────

SOUL_MEMORY_DEFAULTS = {
    "currentProject": "",
    "currentTask": "",
    "currentTopic": "",
    "emotionalState": "neutral",
    "conversationSummary": "",
}

USER_MODEL_TEMPLATE = """# {display_name}

## Persona
{{Unknown — first SMS interaction.}}

## Communication Style
{{Not yet observed.}}

## Interests & Domains
{{Not yet observed.}}

## Notes
{{No observations yet.}}
"""

WORKING_MEMORY_TTL_HOURS = 72
USER_MODEL_UPDATE_INTERVAL = 5

# ── Schema ───────────────────────────────────────────────────────────────

_SCHEMA = """
    CREATE TABLE IF NOT EXISTS working_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone_number TEXT NOT NULL,
        our_number TEXT NOT NULL,
        entry_type TEXT NOT NULL,
        verb TEXT,
        content TEXT NOT NULL,
        metadata TEXT,
        created_at REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS user_models (
        phone_number TEXT PRIMARY KEY,
        display_name TEXT,
        model_md TEXT NOT NULL,
        interaction_count INTEGER DEFAULT 0,
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS soul_memory (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS replied_messages (
        message_id TEXT PRIMARY KEY,
        replied_at REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS sms_sessions (
        phone_number TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        updated_at REAL NOT NULL
    );
"""

_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _local.conn = sqlite3.connect(str(DB_PATH))
        _local.conn.row_factory = sqlite3.Row
        _local.conn.executescript(_SCHEMA)
        _local.conn.commit()
    return _local.conn


def close():
    if hasattr(_local, "conn") and _local.conn is not None:
        _local.conn.close()
        _local.conn = None


# ── Working Memory ───────────────────────────────────────────────────────

def add_working_memory(
    phone_number: str,
    our_number: str,
    entry_type: str,
    content: str,
    verb: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> None:
    # Try canonical daemon first
    display_name = _ur.get_display_name_for_phone(phone_number)
    if _cm.log_memory(
        channel=_cm.sms_channel(phone_number),
        thread_ts=phone_number,
        user_id=phone_number,
        entry_type=entry_type,
        content=content,
        verb=verb,
        metadata=metadata,
        display_name=display_name,
    ):
        return
    # Fallback to local DB
    conn = _get_conn()
    conn.execute(
        """INSERT INTO working_memory
           (phone_number, our_number, entry_type, verb, content, metadata, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (phone_number, our_number, entry_type, verb, content,
         json.dumps(metadata) if metadata else None, time.time()),
    )
    conn.commit()


def get_recent_memory(phone_number: str, limit: int = 20) -> list[dict]:
    # Try canonical daemon first
    canonical = _cm.get_recent(
        channel=_cm.sms_channel(phone_number),
        thread_ts=phone_number,
        limit=limit,
    )
    if canonical is not None:
        return canonical
    # Fallback to local DB
    conn = _get_conn()
    rows = conn.execute(
        """SELECT entry_type, verb, content, metadata, created_at
           FROM working_memory
           WHERE phone_number = ?
           ORDER BY created_at DESC
           LIMIT ?""",
        (phone_number, limit),
    ).fetchall()
    return [dict(r) for r in reversed(rows)]


def format_working_memory(entries: list[dict], soul_name: str = "Claudius") -> str:
    if not entries:
        return ""
    lines = []
    for entry in entries:
        et = entry["entry_type"]
        verb = entry.get("verb")
        content = entry["content"]
        meta = entry.get("metadata")

        if et == "userMessage":
            lines.append(f'They said: "{content}"')
        elif et == "internalMonologue":
            lines.append(f'{soul_name} {verb or "thought"}: "{content}"')
        elif et == "externalDialog":
            lines.append(f'{soul_name} {verb or "said"}: "{content}"')
        elif et == "mentalQuery":
            if meta:
                try:
                    m = json.loads(meta) if isinstance(meta, str) else meta
                    lines.append(f'{soul_name} evaluated: "{content}" -> {m.get("result", "")}')
                except (json.JSONDecodeError, TypeError):
                    lines.append(f'{soul_name} evaluated: "{content}"')
            else:
                lines.append(f'{soul_name} evaluated: "{content}"')
        elif et == "link":
            if meta:
                try:
                    m_parsed = json.loads(meta) if isinstance(meta, str) else meta
                    domain = m_parsed.get("domain", "")
                    lines.append(f'They shared a link: {content} ({domain})')
                except (json.JSONDecodeError, TypeError):
                    lines.append(f'They shared a link: {content}')
            else:
                lines.append(f'They shared a link: {content}')
        else:
            lines.append(content)
    return "\n".join(lines)


def cleanup_working_memory(max_age_hours: Optional[int] = None) -> int:
    hours = max_age_hours or WORKING_MEMORY_TTL_HOURS
    conn = _get_conn()
    cutoff = time.time() - hours * 3600
    cursor = conn.execute("DELETE FROM working_memory WHERE created_at < ?", (cutoff,))
    conn.commit()
    return cursor.rowcount


def prune_working_memory(
    phone_number: str,
    entry_types: Optional[list[str]] = None,
    content_pattern: Optional[str] = None,
    date: Optional[str] = None,
    dry_run: bool = False,
) -> int:
    """Selectively prune working memory entries by type, content pattern, or date.

    Args:
        phone_number: E.164 phone number (e.g. '+17327595647')
        entry_types: List of entry types to match (e.g. ['mentalQuery', 'decision'])
        content_pattern: SQL LIKE pattern to match content (e.g. '%twitter%')
        date: ISO date string (YYYY-MM-DD) to restrict to a single day
        dry_run: If True, return count without deleting

    Returns:
        Number of entries deleted (or would be deleted if dry_run)

    Usage:
        # Preview what would be pruned
        prune_working_memory('+17327595647', entry_types=['mentalQuery'], dry_run=True)
        # Delete all decision entries from a specific date
        prune_working_memory('+17327595647', entry_types=['decision'], date='2026-03-18')
        # Delete entries matching a content pattern
        prune_working_memory('+17327595647', content_pattern='%can\\'t fetch%')
    """
    # Build query for both local and canonical DBs
    conditions = ["phone_number = ?"]
    params: list = [phone_number]

    if entry_types:
        placeholders = ",".join("?" for _ in entry_types)
        conditions.append(f"entry_type IN ({placeholders})")
        params.extend(entry_types)

    if content_pattern:
        conditions.append("content LIKE ?")
        params.append(content_pattern)

    if date:
        # Convert date to epoch range
        import datetime as _dt
        day_start = _dt.datetime.strptime(date, "%Y-%m-%d").timestamp()
        day_end = day_start + 86400
        conditions.append("created_at >= ? AND created_at < ?")
        params.extend([day_start, day_end])

    where = " AND ".join(conditions)

    # Prune from local DB
    conn = _get_conn()
    if dry_run:
        row = conn.execute(f"SELECT COUNT(*) as cnt FROM working_memory WHERE {where}", params).fetchone()
        count = row["cnt"] if row else 0
    else:
        cursor = conn.execute(f"DELETE FROM working_memory WHERE {where}", params)
        conn.commit()
        count = cursor.rowcount

    # Also prune from canonical DB if available
    canonical_count = _cm.prune_working_memory(phone_number, entry_types, content_pattern, date, dry_run)
    return count + canonical_count


# ── User Models ──────────────────────────────────────────────────────────

def get_user_model(phone_number: str) -> Optional[str]:
    # 1. Rich userModel from ~/.claude/userModels/ (by phone)
    rich = _ur.resolve_by_phone(phone_number)
    if rich is not None:
        return rich
    # 2. Canonical daemon DB (if soul active)
    canonical = _cm.get_user_model(phone_number)
    if canonical is not None:
        return canonical
    # 3. Local DB fallback
    conn = _get_conn()
    row = conn.execute(
        "SELECT model_md FROM user_models WHERE phone_number = ?", (phone_number,)
    ).fetchone()
    return row["model_md"] if row else None


def get_display_name(phone_number: str) -> Optional[str]:
    # Try rich userModel first
    name = _ur.get_display_name_for_phone(phone_number)
    if name is not None:
        return name
    # Then local DB
    conn = _get_conn()
    row = conn.execute(
        "SELECT display_name FROM user_models WHERE phone_number = ?", (phone_number,)
    ).fetchone()
    return row["display_name"] if row else None


def ensure_user_model(
    phone_number: str,
    display_name: Optional[str] = None,
    max_chars: Optional[int] = None,
) -> str:
    """Ensure a user model exists, creating a blank template if needed.

    Args:
        max_chars: If set, truncate the returned model to approximately this many
            characters. Keeps complete lines up to the budget. Useful for SMS
            context where a 6,500-char model would dominate the prompt.
    """
    model = get_user_model(phone_number)
    if model is None:
        name = display_name or phone_number
        model = USER_MODEL_TEMPLATE.replace("{display_name}", name)
        save_user_model(phone_number, model, display_name)
    if max_chars and len(model) > max_chars:
        # Truncate to complete lines within budget
        lines = model.split("\n")
        kept = []
        total = 0
        for line in lines:
            if total + len(line) + 1 > max_chars:
                break
            kept.append(line)
            total += len(line) + 1
        model = "\n".join(kept)
    return model


def save_user_model(phone_number: str, model_md: str, display_name: Optional[str] = None) -> None:
    # Try canonical daemon first
    if _cm.save_user_model(phone_number, model_md, display_name):
        return
    # Fallback to local DB
    conn = _get_conn()
    now = time.time()
    conn.execute(
        """INSERT INTO user_models (phone_number, display_name, model_md, interaction_count, created_at, updated_at)
           VALUES (?, ?, ?, 1, ?, ?)
           ON CONFLICT(phone_number)
           DO UPDATE SET
               model_md = excluded.model_md,
               display_name = COALESCE(excluded.display_name, user_models.display_name),
               updated_at = excluded.updated_at""",
        (phone_number, display_name, model_md, now, now),
    )
    conn.commit()


def increment_interaction(phone_number: str) -> None:
    # Try canonical daemon first
    if _cm.increment_interaction(phone_number):
        return
    # Fallback to local DB
    conn = _get_conn()
    now = time.time()
    # Ensure row exists (INSERT OR IGNORE), then increment
    conn.execute(
        """INSERT OR IGNORE INTO user_models
           (phone_number, model_md, interaction_count, created_at, updated_at)
           VALUES (?, '', 0, ?, ?)""",
        (phone_number, now, now),
    )
    conn.execute(
        "UPDATE user_models SET interaction_count = interaction_count + 1, updated_at = ? WHERE phone_number = ?",
        (now, phone_number),
    )
    conn.commit()


def should_check_user_model(phone_number: str) -> bool:
    # Try canonical daemon first
    result = _cm.should_check_user_model(phone_number)
    if result is not None:
        return result
    # Fallback to local DB
    conn = _get_conn()
    row = conn.execute(
        "SELECT interaction_count FROM user_models WHERE phone_number = ?", (phone_number,)
    ).fetchone()
    if row is None:
        return False
    return row["interaction_count"] % USER_MODEL_UPDATE_INTERVAL == 0


# ── Soul Memory ──────────────────────────────────────────────────────────

def get_soul(key: str) -> Optional[str]:
    # Try canonical daemon first
    canonical = _cm.get_soul(key)
    if canonical is not None:
        return canonical
    if _cm.is_soul_active():
        # Soul is active but key not found — return default
        return SOUL_MEMORY_DEFAULTS.get(key)
    # Fallback to local DB
    conn = _get_conn()
    row = conn.execute("SELECT value FROM soul_memory WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else SOUL_MEMORY_DEFAULTS.get(key)


def set_soul(key: str, value: str) -> None:
    # Try canonical daemon first
    if _cm.set_soul(key, value):
        return
    # Fallback to local DB
    conn = _get_conn()
    conn.execute(
        """INSERT INTO soul_memory (key, value, updated_at)
           VALUES (?, ?, ?)
           ON CONFLICT(key)
           DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at""",
        (key, value, time.time()),
    )
    conn.commit()


def get_all_soul() -> dict[str, str]:
    # Try canonical daemon first
    canonical = _cm.get_all_soul()
    if canonical is not None:
        result = dict(SOUL_MEMORY_DEFAULTS)
        result.update(canonical)
        return result
    # Fallback to local DB
    conn = _get_conn()
    rows = conn.execute("SELECT key, value FROM soul_memory").fetchall()
    result = dict(SOUL_MEMORY_DEFAULTS)
    for row in rows:
        result[row["key"]] = row["value"]
    return result


def format_soul_state() -> str:
    # Try unified soul_state renderer first (includes topic stack, relative times)
    canonical = _cm.format_soul_state()
    if canonical is not None:
        return canonical
    # Fallback to local DB rendering
    state = get_all_soul()
    has_content = any(
        state.get(k) and state.get(k) != SOUL_MEMORY_DEFAULTS.get(k)
        for k in SOUL_MEMORY_DEFAULTS
    )
    if not has_content:
        return ""
    lines = ["## Soul State", ""]
    if state.get("currentTopic"):
        lines.append(f"- **Current Topic**: {state['currentTopic']}")
    if state.get("emotionalState") and state["emotionalState"] != "neutral":
        lines.append(f"- **Emotional State**: {state['emotionalState']}")
    if state.get("conversationSummary"):
        lines.append(f"- **Recent Context**: {state['conversationSummary']}")
    return "\n".join(lines)


# ── Reply Dedup ──────────────────────────────────────────────────────────

def was_replied(message_id: str) -> bool:
    conn = _get_conn()
    row = conn.execute(
        "SELECT 1 FROM replied_messages WHERE message_id = ?", (message_id,)
    ).fetchone()
    return row is not None


def mark_replied(message_id: str) -> None:
    conn = _get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO replied_messages (message_id, replied_at) VALUES (?, ?)",
        (message_id, time.time()),
    )
    conn.commit()


def get_session(phone_number: str) -> Optional[str]:
    """Get the Claude session ID for a phone number."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT session_id FROM sms_sessions WHERE phone_number = ?", (phone_number,)
    ).fetchone()
    return row["session_id"] if row else None


def save_session(phone_number: str, session_id: str) -> None:
    """Save a Claude session ID for a phone number."""
    conn = _get_conn()
    conn.execute(
        """INSERT INTO sms_sessions (phone_number, session_id, updated_at)
           VALUES (?, ?, ?)
           ON CONFLICT(phone_number)
           DO UPDATE SET session_id = excluded.session_id, updated_at = excluded.updated_at""",
        (phone_number, session_id, time.time()),
    )
    conn.commit()


def cleanup_replied(max_age_hours: int = 168) -> int:
    """Remove old reply dedup records (default: 7 days)."""
    conn = _get_conn()
    cutoff = time.time() - max_age_hours * 3600
    cursor = conn.execute("DELETE FROM replied_messages WHERE replied_at < ?", (cutoff,))
    conn.commit()
    return cursor.rowcount
