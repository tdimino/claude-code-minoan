"""
Thin proxy to the canonical unified soul state.

Previously this was a standalone SQLite key-value store in the Slack daemon.
Now it delegates all reads and writes to the canonical soul_state module
at ~/.claudicle/daemon/memory/soul_state.py, which is shared across all
channels (Slack, SMS, terminal).

The API surface (get, set, get_all, format_for_prompt, close, SOUL_MEMORY_DEFAULTS)
is preserved for backward compatibility with soul_engine.py, bot.py,
claudicle.py, and slack_adapter.py.
"""

import os
import sys

# Add canonical daemon to path so we can import memory.soul_state
_CANONICAL_DAEMON = os.path.expanduser("~/.claudicle/daemon")
if _CANONICAL_DAEMON not in sys.path:
    sys.path.insert(0, _CANONICAL_DAEMON)

from memory import soul_state  # noqa: E402
from memory import soul_memory as _canonical  # noqa: E402

SOUL_MEMORY_DEFAULTS = {
    "currentProject": "",
    "currentTask": "",
    "currentTopic": "",
    "emotionalState": "neutral",
    "conversationSummary": "",
}


def get(key: str) -> str | None:
    """Get a soul state value via the canonical module."""
    return soul_state.get_state_key(key)


def set(key: str, value: str, channel: str = "slack", thread_info: dict | None = None) -> None:
    """Set a soul state value, delegating to the unified soul_state module.

    The channel and thread_info params are new — callers that only pass
    (key, value) still work via defaults.
    """
    soul_state.set_state_key(key, value, channel=channel, thread_info=thread_info)


def get_all() -> dict[str, str]:
    """Get all soul state values, merged with defaults for missing keys."""
    state = soul_state.get_state()
    result = dict(SOUL_MEMORY_DEFAULTS)
    if state.emotional_state:
        result["emotionalState"] = state.emotional_state
    if state.primary_topic:
        result["currentTopic"] = state.primary_topic.label
    if state.current_project:
        result["currentProject"] = state.current_project
    if state.current_task:
        result["currentTask"] = state.current_task
    if state.conversation_summary:
        result["conversationSummary"] = state.conversation_summary
    return result


def format_for_prompt() -> str:
    """Format soul state for prompt injection, using the unified renderer."""
    return soul_state.format_for_prompt()


def close() -> None:
    """Close connections."""
    soul_state.close()
