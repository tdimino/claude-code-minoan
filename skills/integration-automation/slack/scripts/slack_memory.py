#!/usr/bin/env python3
"""
CLI wrapper for Claudicle's three-tier memory system.

Exposes user_models, soul_memory, and working_memory operations as subcommands
so the Session Bridge (/slack-respond SKILL.md) can call them via bash.

Imports the daemon modules directly — zero duplication of SQLite logic.

Usage:
    slack_memory.py load-context <user_id> [--display-name NAME] [--channel CH] [--thread-ts TS]
    slack_memory.py update-user-model <user_id> <update_text> [--display-name NAME]
    slack_memory.py update-soul-state <key> <value>
    slack_memory.py log-working <channel> <thread_ts> <user_id> <entry_type> [--verb V] [--content C] [--metadata JSON]
    slack_memory.py show-user-model <user_id>
    slack_memory.py increment <user_id>
"""

import argparse
import json
import os
import sys

# Add daemon directory to path so we can import its modules directly
DAEMON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "daemon")
sys.path.insert(0, DAEMON_DIR)

import soul_memory
import user_models
import working_memory


def _should_inject_user_model(entries: list[dict]) -> bool:
    """Samantha-Dreams pattern: inject user model on first turn or when last
    user_model_check returned true.

    Mirrors soul_engine.py:358-383.
    """
    if not entries:
        return True

    for entry in reversed(entries):
        if (
            entry.get("entry_type") == "mentalQuery"
            and "user model" in entry.get("content", "").lower()
        ):
            meta = entry.get("metadata")
            if meta:
                try:
                    m = json.loads(meta) if isinstance(meta, str) else meta
                    return bool(m.get("result", False))
                except (json.JSONDecodeError, TypeError, AttributeError):
                    pass
            break

    return False


def cmd_load_context(args):
    """Load memory context for prompt injection.

    Outputs user model (conditional) + soul state formatted for the prompt.
    """
    parts = []

    # User model — conditional injection (Samantha-Dreams pattern)
    entries = []
    if args.channel and args.thread_ts:
        entries = working_memory.get_recent(args.channel, args.thread_ts, limit=5)

    model = user_models.ensure_exists(args.user_id, args.display_name)
    if _should_inject_user_model(entries):
        parts.append(f"## User Model\n\n{model}")

    # Soul state — always inject when non-default
    soul_state_text = soul_memory.format_for_prompt()
    if soul_state_text:
        parts.append(soul_state_text)

    if parts:
        print("\n\n".join(parts))


def cmd_update_user_model(args):
    """Save or update a user's model markdown."""
    # Read update text from argument or stdin
    if args.update_text:
        text = args.update_text
    else:
        text = sys.stdin.read().strip()

    if not text:
        print("Error: no update text provided", file=sys.stderr)
        sys.exit(1)

    user_models.save(args.user_id, text, args.display_name)
    print(f"Updated user model for {args.user_id}")


def cmd_update_soul_state(args):
    """Set a soul memory key."""
    valid_keys = set(soul_memory.SOUL_MEMORY_DEFAULTS.keys())
    if args.key not in valid_keys:
        print(f"Error: invalid key '{args.key}'. Valid: {', '.join(sorted(valid_keys))}", file=sys.stderr)
        sys.exit(1)

    soul_memory.set(args.key, args.value)
    print(f"Soul state: {args.key} = {args.value}")


def cmd_log_working(args):
    """Add a working memory entry."""
    metadata = None
    if args.metadata:
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError:
            print(f"Error: invalid JSON metadata: {args.metadata}", file=sys.stderr)
            sys.exit(1)

    # Read content from argument or stdin
    content = args.content
    if not content:
        content = sys.stdin.read().strip()

    if not content:
        print("Error: no content provided", file=sys.stderr)
        sys.exit(1)

    working_memory.add(
        channel=args.channel,
        thread_ts=args.thread_ts,
        user_id=args.user_id,
        entry_type=args.entry_type,
        content=content,
        verb=args.verb,
        metadata=metadata,
    )
    print(f"Logged {args.entry_type} to working memory")


def cmd_show_user_model(args):
    """Print the raw user model markdown."""
    model = user_models.get(args.user_id)
    if model is None:
        print(f"No user model found for {args.user_id}", file=sys.stderr)
        sys.exit(1)
    print(model)


def cmd_increment(args):
    """Bump the interaction counter for a user."""
    user_models.increment_interaction(args.user_id)
    count = user_models.get_interaction_count(args.user_id)
    print(f"Interaction count for {args.user_id}: {count}")


def main():
    parser = argparse.ArgumentParser(
        description="CLI wrapper for Claudicle's three-tier memory system"
    )
    sub = parser.add_subparsers(dest="command")

    # load-context
    p_load = sub.add_parser("load-context", help="Load memory context for prompt injection")
    p_load.add_argument("user_id", help="Slack user ID")
    p_load.add_argument("--display-name", dest="display_name", help="User's display name")
    p_load.add_argument("--channel", help="Channel ID (for Samantha-Dreams gating)")
    p_load.add_argument("--thread-ts", dest="thread_ts", help="Thread timestamp")

    # update-user-model
    p_update = sub.add_parser("update-user-model", help="Save/update a user model")
    p_update.add_argument("user_id", help="Slack user ID")
    p_update.add_argument("update_text", nargs="?", help="Updated model markdown (or stdin)")
    p_update.add_argument("--display-name", dest="display_name", help="User's display name")

    # update-soul-state
    p_soul = sub.add_parser("update-soul-state", help="Set a soul memory key")
    p_soul.add_argument("key", help="Key (currentProject, currentTask, currentTopic, emotionalState, conversationSummary)")
    p_soul.add_argument("value", help="Value to set")

    # log-working
    p_log = sub.add_parser("log-working", help="Add a working memory entry")
    p_log.add_argument("channel", help="Channel ID")
    p_log.add_argument("thread_ts", help="Thread timestamp")
    p_log.add_argument("user_id", help="User ID")
    p_log.add_argument("entry_type", help="Entry type (userMessage, internalMonologue, externalDialog, mentalQuery, toolAction)")
    p_log.add_argument("--verb", help="Verb for the entry")
    p_log.add_argument("--content", help="Content text (or stdin)")
    p_log.add_argument("--metadata", help="JSON metadata string")

    # show-user-model
    p_show = sub.add_parser("show-user-model", help="Print raw user model markdown")
    p_show.add_argument("user_id", help="Slack user ID")

    # increment
    p_inc = sub.add_parser("increment", help="Bump interaction counter")
    p_inc.add_argument("user_id", help="Slack user ID")

    args = parser.parse_args()

    if args.command == "load-context":
        cmd_load_context(args)
    elif args.command == "update-user-model":
        cmd_update_user_model(args)
    elif args.command == "update-soul-state":
        cmd_update_soul_state(args)
    elif args.command == "log-working":
        cmd_log_working(args)
    elif args.command == "show-user-model":
        cmd_show_user_model(args)
    elif args.command == "increment":
        cmd_increment(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
