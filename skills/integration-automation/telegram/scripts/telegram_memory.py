#!/usr/bin/env python3
"""
Thin CLI wrapper for Claudicle three-tier memory, scoped to Telegram channels.

Usage:
    python3 telegram_memory.py load-context CHAT_ID
    python3 telegram_memory.py user-model USER_ID
    python3 telegram_memory.py soul-state
"""

import argparse
import json
import os
import sys

# Import shared memory module
SHARED_DIR = os.path.expanduser("~/.claudicle/adapters/shared")
sys.path.insert(0, SHARED_DIR)

# Import canonical daemon memory
DAEMON_MEMORY_DIR = os.path.expanduser("~/.claudicle/daemon/memory")
sys.path.insert(0, os.path.expanduser("~/.claudicle/daemon"))


def load_context(chat_id: str):
    channel = f"telegram:{chat_id}"
    # Try shared claudicle_memory wrapper first (designed for out-of-daemon use)
    try:
        import claudicle_memory as cm
        entries = cm.get_recent(channel, thread_ts="", limit=20)
        if entries:
            for e in entries:
                d = dict(e) if not isinstance(e, dict) else e
                print(f"  [{d.get('entry_type', '?')}] {d.get('content', '')[:100]}")
            return
    except (ImportError, Exception):
        pass

    # Fallback: try daemon memory directly
    try:
        from memory import working_memory as wm
        entries = wm.get_recent(channel, thread_ts="", limit=20)
        if not entries:
            print(f"No working memory for {channel}")
            return
        for e in entries:
            d = dict(e)
            print(f"  [{d.get('entry_type', '?')}] {d.get('content', '')[:100]}")
    except ImportError:
        print(f"No working memory for {channel} (daemon memory not accessible)")
        return


def user_model(user_id: str):
    # Try usermodel_resolver first
    resolver_dir = os.path.expanduser("~/.claude/skills/shared")
    sys.path.insert(0, resolver_dir)
    try:
        import usermodel_resolver as ur
        # Try telegramId resolution
        if hasattr(ur, "resolve_by_telegram_id"):
            model = ur.resolve_by_telegram_id(user_id.replace("tg:", ""))
            if model:
                print(model[:500])
                return
        # Try phone resolution as fallback
        if hasattr(ur, "resolve_by_phone"):
            model = ur.resolve_by_phone(user_id)
            if model:
                print(model[:500])
                return
    except ImportError:
        pass

    # Try canonical DB
    try:
        from memory import user_models as um
        uid = user_id if user_id.startswith("tg:") else f"tg:{user_id}"
        model = um.get(uid)
        if model:
            print(json.dumps(dict(model), indent=2, default=str))
            return
    except ImportError:
        pass

    print(f"No user model found for {user_id}")


def soul_state():
    try:
        from memory import soul_memory as sm
        state = sm.get_all()
        if not state:
            print("No soul state stored.")
            return
        for key, value in state.items():
            print(f"  {key}: {value}")
    except ImportError:
        print("Soul memory not available.", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Telegram memory CLI")
    sub = parser.add_subparsers(dest="command")

    ctx = sub.add_parser("load-context", help="Load working memory for a chat")
    ctx.add_argument("chat_id", help="Telegram chat ID")

    um_parser = sub.add_parser("user-model", help="Show user model")
    um_parser.add_argument("user_id", help="User ID (numeric or tg:prefixed)")

    sub.add_parser("soul-state", help="Show soul state")

    args = parser.parse_args()

    if args.command == "load-context":
        load_context(args.chat_id)
    elif args.command == "user-model":
        user_model(args.user_id)
    elif args.command == "soul-state":
        soul_state()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
