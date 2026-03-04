"""
Claudicle Memory Adapter — soul-aware channel memory routing.

If ~/.claudicle/soul/soul.md exists (soul is active), routes all memory
operations through the canonical Claudicle daemon module at
~/.claudicle/daemon/memory/. Otherwise returns None so callers fall back
to their local per-skill databases.

This module is imported by both SMS and Slack skills as their unified
memory gateway. It never owns a database — it delegates to whichever
backend is appropriate.

Thread-safe: delegates to thread-safe canonical modules.
"""

import json
import logging
import os
import sys
import threading
import types
from typing import Any, Optional

log = logging.getLogger(__name__)

SOUL_PATH = os.path.expanduser("~/.claudicle/soul/soul.md")
DAEMON_DIR = os.path.expanduser("~/.claudicle/daemon")

# Cache the daemon modules after first successful import
_daemon: Optional[types.SimpleNamespace] = None
_daemon_checked = False
_init_lock = threading.Lock()


def is_soul_active() -> bool:
    """Check if the Claudicle soul is active (soul.md exists)."""
    return os.path.isfile(SOUL_PATH)


def get_daemon_modules() -> Optional[types.SimpleNamespace]:
    """Import and return canonical memory modules if soul is active.

    Returns a namespace with: working_memory, soul_memory, user_models, snapshot.
    Returns None if soul is not active or import fails.
    """
    global _daemon, _daemon_checked

    if not is_soul_active():
        return None

    if _daemon_checked:
        return _daemon

    with _init_lock:
        if _daemon_checked:
            return _daemon
        _daemon_checked = True
        try:
            if DAEMON_DIR not in sys.path:
                sys.path.insert(0, DAEMON_DIR)
            from memory import working_memory, soul_memory, user_models
            from memory.snapshot import (
                WorkingMemorySnapshot,
                CognitiveOutput,
                load_snapshot,
                apply_output,
            )
            _daemon = types.SimpleNamespace(
                working_memory=working_memory,
                soul_memory=soul_memory,
                user_models=user_models,
                load_snapshot=load_snapshot,
                apply_output=apply_output,
                WorkingMemorySnapshot=WorkingMemorySnapshot,
                CognitiveOutput=CognitiveOutput,
            )
            log.info("Claudicle daemon memory loaded from %s", DAEMON_DIR)
            return _daemon
        except Exception as e:
            log.warning("Failed to load Claudicle daemon memory: %s", e)
            _daemon = None
            return None


# ── Working Memory ──────────────────────────────────────────────────────


def log_memory(
    channel: str,
    thread_ts: str,
    user_id: str,
    entry_type: str,
    content: str,
    verb: Optional[str] = None,
    metadata: Optional[dict] = None,
    display_name: Optional[str] = None,
    region: str = "default",
) -> bool:
    """Route a working memory entry to canonical DB if soul active.

    Returns True if written to canonical, False if caller should use local DB.
    """
    dm = get_daemon_modules()
    if dm is None:
        return False
    try:
        dm.working_memory.add(
            channel=channel,
            thread_ts=thread_ts,
            user_id=user_id,
            entry_type=entry_type,
            content=content,
            verb=verb,
            metadata=metadata,
            display_name=display_name,
            region=region,
        )
        return True
    except Exception as e:
        log.error("Canonical working_memory.add failed for channel=%s: %s", channel, e)
        return False


def get_recent(
    channel: str,
    thread_ts: str,
    limit: int = 20,
) -> Optional[list[dict]]:
    """Get recent working memory entries from canonical DB.

    Returns list of dicts if soul active, None if caller should use local DB.
    """
    dm = get_daemon_modules()
    if dm is None:
        return None
    return dm.working_memory.get_recent(channel, thread_ts, limit=limit)


# ── Soul Memory ─────────────────────────────────────────────────────────


def get_soul(key: str) -> Optional[str]:
    """Get a soul memory value from canonical DB.

    Returns the value if soul active, None if caller should use local DB.
    Note: None is ambiguous (could mean 'key not found' or 'soul not active').
    Use is_soul_active() to disambiguate.
    """
    dm = get_daemon_modules()
    if dm is None:
        return None
    return dm.soul_memory.get(key)


def set_soul(key: str, value: str) -> bool:
    """Set a soul memory value in canonical DB.

    Returns True if written to canonical, False if caller should use local DB.
    """
    dm = get_daemon_modules()
    if dm is None:
        return False
    try:
        dm.soul_memory.set(key, value)
        return True
    except Exception as e:
        log.error("Canonical soul_memory.set failed for key=%s: %s", key, e)
        return False


def get_all_soul() -> Optional[dict[str, str]]:
    """Get all soul memory values from canonical DB.

    Returns dict if soul active, None if caller should use local DB.
    """
    dm = get_daemon_modules()
    if dm is None:
        return None
    return dm.soul_memory.get_all()


# ── User Models ─────────────────────────────────────────────────────────


def get_user_model(user_id: str) -> Optional[str]:
    """Get a user model from canonical DB.

    Returns model markdown if found and soul active, None otherwise.
    """
    dm = get_daemon_modules()
    if dm is None:
        return None
    return dm.user_models.get(user_id)


def save_user_model(
    user_id: str,
    model_md: str,
    display_name: Optional[str] = None,
    change_note: str = "",
) -> bool:
    """Save a user model to canonical DB.

    Returns True if written to canonical, False if caller should use local DB.
    """
    dm = get_daemon_modules()
    if dm is None:
        return False
    try:
        dm.user_models.save(user_id, model_md, display_name, change_note)
        return True
    except Exception as e:
        log.error("Canonical user_models.save failed for %s: %s", user_id, e)
        return False


def increment_interaction(user_id: str) -> bool:
    """Increment interaction count in canonical DB.

    Returns True if done in canonical, False if caller should use local DB.
    """
    dm = get_daemon_modules()
    if dm is None:
        return False
    try:
        dm.user_models.increment_interaction(user_id)
        return True
    except Exception as e:
        log.error("Canonical increment_interaction failed for %s: %s", user_id, e)
        return False


def should_check_user_model(user_id: str) -> Optional[bool]:
    """Check if user model should be updated based on interaction count.

    Returns True/False if soul active, None if caller should use local DB.
    """
    dm = get_daemon_modules()
    if dm is None:
        return None
    try:
        return dm.user_models.should_check_update(user_id)
    except Exception as e:
        log.error("Canonical should_check_update failed for %s: %s", user_id, e)
        return None


# ── Snapshot API (Open Souls pattern) ───────────────────────────────────


def load_snapshot(
    channel: str,
    thread_ts: str,
    limit: int = 40,
) -> Optional[Any]:
    """Load an immutable WorkingMemorySnapshot from canonical DB.

    Returns WorkingMemorySnapshot if soul active, None otherwise.
    """
    dm = get_daemon_modules()
    if dm is None:
        return None
    return dm.load_snapshot(channel, thread_ts, limit=limit)


def apply_cognitive_output(
    output: Any,
    channel: str,
    thread_ts: str,
    internal: bool = False,
) -> bool:
    """Apply a CognitiveOutput atomically to canonical DB.

    Returns True if applied to canonical, False if caller should handle locally.
    """
    dm = get_daemon_modules()
    if dm is None:
        return False
    dm.apply_output(output, channel, thread_ts, internal=internal)
    return True


# ── Helpers ─────────────────────────────────────────────────────────────


def sms_channel(phone: str) -> str:
    """Format an SMS phone number as a canonical channel ID."""
    return f"sms:{phone}"


def slack_channel(channel_id: str) -> str:
    """Format a Slack channel ID as a canonical channel ID."""
    return f"slack:{channel_id}"


def invalidate_cache():
    """Force re-check of soul status on next call. Useful for testing."""
    global _daemon, _daemon_checked
    _daemon = None
    _daemon_checked = False
