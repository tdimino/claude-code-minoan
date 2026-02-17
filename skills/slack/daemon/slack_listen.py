#!/usr/bin/env python3
"""
Background Slack listener — writes incoming messages to inbox.jsonl.

Runs as a standalone process alongside any Claude Code session.
Catches @mentions and DMs via Socket Mode, appends to inbox.jsonl,
and adds an hourglass reaction for visual feedback.

Usage:
    python3 slack_listen.py           # foreground (for testing)
    python3 slack_listen.py --bg      # daemonize, write PID file
    python3 slack_listen.py --stop    # kill running listener
    python3 slack_listen.py --status  # check if running

Requires:
    SLACK_BOT_TOKEN (xoxb-) and SLACK_APP_TOKEN (xapp-)
    pip install slack-bolt
"""

import argparse
import json
import os
import re
import signal
import sys
import time

DAEMON_DIR = os.path.dirname(os.path.abspath(__file__))
INBOX = os.path.join(DAEMON_DIR, "inbox.jsonl")
PID_FILE = os.path.join(DAEMON_DIR, "listener.pid")


def _read_pid():
    """Read PID from file, return int or None."""
    try:
        with open(PID_FILE) as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None


def _is_running(pid):
    """Check if a process with the given PID is running."""
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def cmd_stop():
    """Kill the running listener via PID file."""
    pid = _read_pid()
    if not _is_running(pid):
        print("Listener is not running.")
        try:
            os.remove(PID_FILE)
        except FileNotFoundError:
            pass
        return
    os.kill(pid, signal.SIGTERM)
    # Wait up to 3s for process to exit
    for _ in range(30):
        if not _is_running(pid):
            break
        time.sleep(0.1)
    try:
        os.remove(PID_FILE)
    except FileNotFoundError:
        pass
    print(f"Listener (PID {pid}) stopped.")


def cmd_status():
    """Check if listener is running."""
    pid = _read_pid()
    if _is_running(pid):
        print(f"Listener running (PID {pid})")
    else:
        print("Listener is not running.")
        if pid is not None:
            try:
                os.remove(PID_FILE)
            except FileNotFoundError:
                pass


def run_listener(background=False):
    """Start the Socket Mode listener."""
    # Check if already running
    pid = _read_pid()
    if _is_running(pid):
        print(f"Listener already running (PID {pid}). Use --stop first.")
        sys.exit(1)

    # Validate tokens
    bot_token = os.environ.get("SLACK_BOT_TOKEN")
    app_token = os.environ.get("SLACK_APP_TOKEN")
    if not bot_token:
        print("Error: SLACK_BOT_TOKEN not set", file=sys.stderr)
        sys.exit(1)
    if not app_token:
        print("Error: SLACK_APP_TOKEN not set (needed for Socket Mode)", file=sys.stderr)
        sys.exit(1)

    if background:
        # Fork to background
        pid = os.fork()
        if pid > 0:
            # Parent — write PID and exit
            with open(PID_FILE, "w") as f:
                f.write(str(pid))
            print(f"Listener started in background (PID {pid})")
            print(f"Inbox: {INBOX}")
            return
        # Child — detach
        os.setsid()
        # Redirect stdout/stderr to log file
        log_path = os.path.join(DAEMON_DIR, "logs", "listener.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        log_fd = open(log_path, "a")
        os.dup2(log_fd.fileno(), sys.stdout.fileno())
        os.dup2(log_fd.fileno(), sys.stderr.fileno())
    else:
        # Foreground — write PID file anyway for status checks
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))

    # Now import slack-bolt (only when actually running)
    from slack_bolt import App
    from slack_bolt.adapter.socket_mode import SocketModeHandler

    app = App(token=bot_token)
    _bot_user_id = ""

    def get_bot_id():
        nonlocal _bot_user_id
        if not _bot_user_id:
            _bot_user_id = app.client.auth_test().get("user_id", "")
        return _bot_user_id

    def strip_mention(text):
        bid = get_bot_id()
        if bid:
            return re.sub(rf"<@{bid}>\s*", "", text).strip()
        return re.sub(r"<@\w+>\s*", "", text, count=1).strip()

    def resolve_name(user_id):
        try:
            info = app.client.users_info(user=user_id)
            p = info["user"]["profile"]
            return p.get("display_name") or p.get("real_name", user_id)
        except Exception:
            return user_id

    def write_inbox(channel, thread_ts, user_id, text):
        entry = {
            "ts": time.time(),
            "channel": channel,
            "thread_ts": thread_ts,
            "user_id": user_id,
            "display_name": resolve_name(user_id),
            "text": text,
            "handled": False,
        }
        with open(INBOX, "a") as f:
            f.write(json.dumps(entry) + "\n")

        # Add hourglass reaction for visual feedback
        try:
            app.client.reactions_add(
                channel=channel, timestamp=thread_ts,
                name="hourglass_flowing_sand"
            )
        except Exception:
            pass  # Duplicate reaction or permissions — harmless

        ts_str = time.strftime("%H:%M:%S")
        name = entry["display_name"]
        print(f"[{ts_str}] Inbox: {name} in {channel}: {text[:80]}", flush=True)

    @app.event("app_mention")
    def on_mention(event, client):
        if event.get("user") == get_bot_id():
            return
        text = strip_mention(event.get("text", ""))
        if not text:
            return
        ts = event.get("ts", "")
        thread_ts = event.get("thread_ts", ts)
        write_inbox(event["channel"], thread_ts, event["user"], text)

    @app.event("message")
    def on_dm(event, client):
        if event.get("channel_type") != "im":
            return
        if event.get("subtype"):
            return
        if event.get("user") == get_bot_id():
            return
        text = event.get("text", "").strip()
        if not text:
            return
        write_inbox(event["channel"], event.get("ts"), event["user"], text)

    # Graceful shutdown
    def _cleanup(signum, frame):
        print("\nListener shutting down...", flush=True)
        try:
            os.remove(PID_FILE)
        except FileNotFoundError:
            pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, _cleanup)
    signal.signal(signal.SIGINT, _cleanup)

    print(f"Slack listener started (PID {os.getpid()})", flush=True)
    print(f"Inbox: {INBOX}", flush=True)

    handler = SocketModeHandler(app, app_token)
    handler.start()


def main():
    parser = argparse.ArgumentParser(description="Slack inbox listener")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--bg", action="store_true", help="Run in background")
    group.add_argument("--stop", action="store_true", help="Stop running listener")
    group.add_argument("--status", action="store_true", help="Check if running")
    args = parser.parse_args()

    if args.stop:
        cmd_stop()
    elif args.status:
        cmd_status()
    else:
        run_listener(background=args.bg)


if __name__ == "__main__":
    main()
