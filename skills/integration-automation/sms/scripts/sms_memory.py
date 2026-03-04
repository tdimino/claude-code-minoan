"""
Three-tier SQLite memory for SMS conversations.

Adapted from the Slack daemon's split modules (soul_memory.py, working_memory.py,
user_models.py) into a single file for the SMS channel.

Tier 1: Working memory — per-conversation message history + cognitive outputs
Tier 2: User models — per-phone-number personality profiles
Tier 3: Soul memory — cross-conversation soul state (emotional state, topic, etc.)

Thread-safe via threading.local() for SQLite connections.
"""

import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional

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


# ── User Models ──────────────────────────────────────────────────────────

def get_user_model(phone_number: str) -> Optional[str]:
    conn = _get_conn()
    row = conn.execute(
        "SELECT model_md FROM user_models WHERE phone_number = ?", (phone_number,)
    ).fetchone()
    return row["model_md"] if row else None


def get_display_name(phone_number: str) -> Optional[str]:
    conn = _get_conn()
    row = conn.execute(
        "SELECT display_name FROM user_models WHERE phone_number = ?", (phone_number,)
    ).fetchone()
    return row["display_name"] if row else None


def ensure_user_model(phone_number: str, display_name: Optional[str] = None) -> str:
    model = get_user_model(phone_number)
    if model is not None:
        return model
    name = display_name or phone_number
    model = USER_MODEL_TEMPLATE.replace("{display_name}", name)
    save_user_model(phone_number, model, display_name)
    return model


def save_user_model(phone_number: str, model_md: str, display_name: Optional[str] = None) -> None:
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
    conn = _get_conn()
    conn.execute(
        "UPDATE user_models SET interaction_count = interaction_count + 1, updated_at = ? WHERE phone_number = ?",
        (time.time(), phone_number),
    )
    conn.commit()


def should_check_user_model(phone_number: str) -> bool:
    conn = _get_conn()
    row = conn.execute(
        "SELECT interaction_count FROM user_models WHERE phone_number = ?", (phone_number,)
    ).fetchone()
    if row is None:
        return False
    return row["interaction_count"] % USER_MODEL_UPDATE_INTERVAL == 0


# ── Soul Memory ──────────────────────────────────────────────────────────

def get_soul(key: str) -> Optional[str]:
    conn = _get_conn()
    row = conn.execute("SELECT value FROM soul_memory WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else SOUL_MEMORY_DEFAULTS.get(key)


def set_soul(key: str, value: str) -> None:
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
    conn = _get_conn()
    rows = conn.execute("SELECT key, value FROM soul_memory").fetchall()
    result = dict(SOUL_MEMORY_DEFAULTS)
    for row in rows:
        result[row["key"]] = row["value"]
    return result


def format_soul_state() -> str:
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
