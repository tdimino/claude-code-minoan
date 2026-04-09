#!/usr/bin/env python3
"""
Build and publish the Claudicle App Home tab via Block Kit.

Usage:
    slack_app_home.py USER_ID              # publish for one user
    slack_app_home.py --all                # publish for all known users
    slack_app_home.py --debug              # print block JSON + count, no publish

Design: Terminal-brutalist with ancient undertones. rich_text blocks
for lists, rich_text_quote for the Claudicle value, section fields for
2-column status grids, context blocks for metadata. No emoji vomit.

Requires: SLACK_BOT_TOKEN environment variable
"""

import argparse
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _slack_utils import slack_api, SlackError

DAEMON_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "daemon")
DB_PATH = os.path.join(DAEMON_DIR, "memory.db")
PID_FILE = os.path.join(DAEMON_DIR, "listener.pid")


# ---------------------------------------------------------------------------
# Dynamic data
# ---------------------------------------------------------------------------

def _listener_status() -> tuple[bool, int | None]:
    """Check if the Session Bridge listener is running. Returns (alive, pid)."""
    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return True, pid
    except (FileNotFoundError, ValueError, OSError):
        return False, None


def _soul_state() -> dict:
    """Read soul memory from memory.db. Returns dict with defaults."""
    defaults = {
        "currentProject": "",
        "currentTask": "",
        "currentTopic": "",
        "emotionalState": "neutral",
        "conversationSummary": "",
    }
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT key, value FROM soul_memory").fetchall()
        conn.close()
        for row in rows:
            defaults[row["key"]] = row["value"]
    except Exception:
        pass
    return defaults


def _total_interactions() -> int:
    """Sum all interaction counts across users."""
    try:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT COALESCE(SUM(interaction_count), 0) as total FROM user_models"
        ).fetchone()
        conn.close()
        return row[0] if row else 0
    except Exception:
        return 0


def _known_user_ids() -> list[str]:
    """Get all user IDs from user_models table."""
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT user_id FROM user_models").fetchall()
        conn.close()
        return [r[0] for r in rows]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Block builders
# ---------------------------------------------------------------------------

def _header_blocks() -> list:
    """Identity: header + context subtitle."""
    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Claudicle, Artifex Maximus", "emoji": True},
        },
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": "\u2301 Session Bridge \u00b7 Socket Mode \u00b7 memory.db"},
            ],
        },
    ]


def _quote_block() -> list:
    """Signature value — rich_text_quote with italic text."""
    return [
        {"type": "divider"},
        {
            "type": "rich_text",
            "elements": [{
                "type": "rich_text_quote",
                "elements": [
                    {
                        "type": "text",
                        "text": "Assumptions are the enemy. Benchmark, don\u2019t estimate.",
                        "style": {"italic": True},
                    },
                ],
            }],
        },
    ]


def _status_blocks() -> list:
    """Dynamic status: listener, interactions, soul state."""
    alive, pid = _listener_status()
    state = _soul_state()
    interactions = _total_interactions()

    # Listener status field
    if alive:
        listener_text = f"\U0001f7e2 running ({pid})"
    else:
        listener_text = "\U0001f534 not running"

    # Build fields (always show listener + interactions, conditionally show soul state)
    fields = [
        {"type": "mrkdwn", "text": f"*Listener*\n{listener_text}"},
        {"type": "mrkdwn", "text": f"*Interactions*\n{interactions} total"},
    ]

    emotion = state.get("emotionalState", "neutral")
    if emotion and emotion != "neutral":
        fields.append({"type": "mrkdwn", "text": f"*Emotional State*\n{emotion}"})

    project = state.get("currentProject", "")
    if project:
        fields.append({"type": "mrkdwn", "text": f"*Current Project*\n{project}"})

    task = state.get("currentTask", "")
    if task:
        fields.append({"type": "mrkdwn", "text": f"*Current Task*\n{task}"})

    topic = state.get("currentTopic", "")
    if topic:
        fields.append({"type": "mrkdwn", "text": f"*Current Topic*\n{topic}"})

    blocks = [
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*Status*"},
        },
        {
            "type": "section",
            "fields": fields[:10],  # Block Kit max 10 fields
        },
    ]

    # Recent context as small context block
    summary = state.get("conversationSummary", "")
    if summary:
        blocks.append({
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"Recent: {summary[:280]}"},
            ],
        })

    return blocks


def _toolkit_blocks() -> list:
    """8 scripts as a rich_text bullet list with bold names."""
    scripts = [
        ("post", "messages, threads, scheduling"),
        ("read", "channel history, thread replies"),
        ("delete", "single, batch, thread cleanup"),
        ("search", "messages and files"),
        ("react", "add/remove emoji reactions"),
        ("upload", "files and code snippets"),
        ("channels", "list, join, info"),
        ("users", "lookup by name, email, ID"),
    ]

    list_elements = []
    for name, desc in scripts:
        list_elements.append({
            "type": "rich_text_section",
            "elements": [
                {"type": "text", "text": name, "style": {"bold": True}},
                {"type": "text", "text": f" \u2014 {desc}"},
            ],
        })

    return [
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*Toolkit*"},
        },
        {
            "type": "rich_text",
            "elements": [{
                "type": "rich_text_list",
                "style": "bullet",
                "elements": list_elements,
            }],
        },
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": "+ format \u00b7 memory \u00b7 check \u00b7 app_home"},
            ],
        },
    ]


def _cognitive_blocks() -> list:
    """Cognitive architecture as a rich_text bullet list."""
    steps = [
        [
            {"type": "text", "text": "perception", "style": {"bold": True}},
            {"type": "text", "text": " \u2192 "},
            {"type": "text", "text": "internalMonologue", "style": {"bold": True}},
            {"type": "text", "text": " \u2192 "},
            {"type": "text", "text": "externalDialog", "style": {"bold": True}},
            {"type": "text", "text": " \u2192 "},
            {"type": "text", "text": "reaction_check", "style": {"bold": True}},
        ],
        [
            {"type": "text", "text": "user_model_check", "style": {"bold": True}},
            {"type": "text", "text": " \u2192 conditional update per person"},
        ],
        [
            {"type": "text", "text": "soul_state_check", "style": {"bold": True}},
            {"type": "text", "text": " \u2192 cross-thread global state"},
        ],
    ]

    list_elements = [
        {"type": "rich_text_section", "elements": step}
        for step in steps
    ]

    return [
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*Cognitive Architecture*"},
        },
        {
            "type": "rich_text",
            "elements": [{
                "type": "rich_text_list",
                "style": "bullet",
                "elements": list_elements,
            }],
        },
    ]


def _memory_blocks() -> list:
    """Three-tier memory as a 2x2 section field grid."""
    return [
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*Memory*"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": "*User Models*\nper-person, permanent"},
                {"type": "mrkdwn", "text": "*Soul State*\ncross-thread, global"},
                {"type": "mrkdwn", "text": "*Working Memory*\nper-thread, 72h TTL"},
                {"type": "mrkdwn", "text": "*Interaction History*\nper-user counters"},
            ],
        },
    ]


def _interaction_blocks() -> list:
    """How to interact — rich_text bullet list."""
    items = [
        [
            {"type": "text", "text": "DM", "style": {"bold": True}},
            {"type": "text", "text": " \u2014 type directly, no @ needed"},
        ],
        [
            {"type": "text", "text": "Channel", "style": {"bold": True}},
            {"type": "text", "text": " \u2014 mention "},
            {"type": "text", "text": "@Claude Code", "style": {"code": True}},
        ],
        [
            {"type": "text", "text": "Threads", "style": {"bold": True}},
            {"type": "text", "text": " \u2014 each one is a separate session"},
        ],
        [
            {"type": "text", "text": "\u2301 thinking", "style": {"bold": True}},
            {"type": "text", "text": " \u2014 live status during processing"},
        ],
    ]

    list_elements = [
        {"type": "rich_text_section", "elements": item}
        for item in items
    ]

    return [
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*How to Interact*"},
        },
        {
            "type": "rich_text",
            "elements": [{
                "type": "rich_text_list",
                "style": "bullet",
                "elements": list_elements,
            }],
        },
    ]


def _footer_blocks() -> list:
    """Footer with repo links."""
    return [
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": (
                    "<https://github.com/aldea-ai/Claude-Code-Aldea|Claude-Code-Aldea>"
                    " \u00b7 <https://github.com/aldea-ai/Claude-Code-Aldea/tree/main/skills/open-souls-paradigm|Open Souls paradigm>"
                )},
            ],
        },
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_blocks() -> list:
    """Build the complete App Home block array."""
    blocks = []
    blocks.extend(_header_blocks())
    blocks.extend(_quote_block())
    blocks.extend(_status_blocks())
    blocks.extend(_toolkit_blocks())
    blocks.extend(_cognitive_blocks())
    blocks.extend(_memory_blocks())
    blocks.extend(_interaction_blocks())
    blocks.extend(_footer_blocks())
    return blocks


def build_home_view() -> dict:
    """Build the complete views.publish payload."""
    return {
        "type": "home",
        "blocks": build_blocks(),
    }


def publish(user_id: str) -> None:
    """Publish the App Home for a specific user."""
    # Slack requires view as a JSON string even with application/json content type
    slack_api("views.publish", user_id=user_id, view=json.dumps(build_home_view()))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Publish Claudicle App Home tab")
    parser.add_argument("user_id", nargs="?", help="Slack user ID to publish for")
    parser.add_argument("--all", action="store_true",
                        help="Publish for all known users in user_models")
    parser.add_argument("--debug", action="store_true",
                        help="Print block JSON and count, don't publish")
    args = parser.parse_args()

    if args.debug:
        blocks = build_blocks()
        print(json.dumps(blocks, indent=2))
        print(f"\n{len(blocks)} blocks", file=sys.stderr)
        return

    if not args.user_id and not args.all:
        parser.error("Provide USER_ID or --all")

    try:
        if args.all:
            user_ids = _known_user_ids()
            if not user_ids:
                print("No known users in user_models table.")
                return
            for uid in user_ids:
                publish(uid)
                print(f"Published for {uid}")
        else:
            publish(args.user_id)
            print(f"Published App Home for {args.user_id}")

    except SlackError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
