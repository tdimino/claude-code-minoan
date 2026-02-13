#!/usr/bin/env python3
"""
Slack Socket Mode daemon—listens for @mentions and DMs, routes to Claude Code.

Requires:
    SLACK_BOT_TOKEN  — Bot User OAuth Token (xoxb-)
    SLACK_APP_TOKEN  — App-Level Token (xapp-) with connections:write scope

Usage:
    python3 bot.py              # Run in foreground
    python3 bot.py --verbose    # Debug logging
"""

import argparse
import logging
import os
import re
import shutil
import signal
import sys
import time

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import claude_handler
import session_store
import soul_memory
import user_models
import working_memory
from config import BLOCKED_CHANNELS, LOG_DIR

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, "daemon.log")),
    ],
)
log = logging.getLogger("slack-daemon")

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")

if not SLACK_BOT_TOKEN:
    log.fatal("SLACK_BOT_TOKEN not set")
    sys.exit(1)
if not SLACK_APP_TOKEN:
    log.fatal("SLACK_APP_TOKEN not set (needed for Socket Mode)")
    sys.exit(1)

app = App(token=SLACK_BOT_TOKEN)

# Cache bot's own user ID so we can strip self-mentions
_bot_user_id: str = ""


def _get_bot_user_id() -> str:
    global _bot_user_id
    if not _bot_user_id:
        resp = app.client.auth_test()
        _bot_user_id = resp.get("user_id", "")
        log.info("Bot user ID: %s", _bot_user_id)
    return _bot_user_id


def _strip_mention(text: str) -> str:
    """Remove only the bot's own <@BOT_ID> from the message text."""
    bot_id = _get_bot_user_id()
    if bot_id:
        return re.sub(rf"<@{bot_id}>\s*", "", text).strip()
    return re.sub(r"<@\w+>\s*", "", text, count=1).strip()


def _is_blocked(channel: str) -> bool:
    return channel in BLOCKED_CHANNELS


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

@app.event("app_mention")
def handle_mention(event, say, client):
    """Respond to @Claude Code mentions in channels."""
    channel = event.get("channel", "")
    ts = event.get("ts", "")
    thread_ts = event.get("thread_ts", ts)  # reply in thread; default to msg itself
    text = _strip_mention(event.get("text", ""))
    user = event.get("user")  # None if missing — guards soul engine

    # Ignore bot's own messages to prevent infinite loops
    if event.get("user") == _get_bot_user_id():
        return

    if _is_blocked(channel):
        log.info("Ignoring mention in blocked channel %s", channel)
        return

    if not text:
        say(text="Mention me with a question or task and I'll help out.", thread_ts=thread_ts)
        return

    log.info("@mention from %s in %s: %s", user, channel, text[:80])

    # Thinking indicator
    try:
        client.reactions_add(channel=channel, timestamp=ts, name="hourglass_flowing_sand")
    except Exception:
        pass  # non-critical

    response = claude_handler.process(text, channel=channel, thread_ts=thread_ts, user_id=user)
    try:
        say(text=response, thread_ts=thread_ts)
    except Exception as e:
        log.error("Failed to post response in %s: %s", channel, e)

    # Remove thinking indicator
    try:
        client.reactions_remove(channel=channel, timestamp=ts, name="hourglass_flowing_sand")
    except Exception:
        pass


@app.event("message")
def handle_dm(event, say, client):
    """Respond to direct messages (DMs) to the bot."""
    # Only handle DMs (channel type "im"), skip subtypes like bot_message
    if event.get("channel_type") != "im":
        return
    if event.get("subtype"):
        return
    # Don't respond to own messages
    if event.get("user") == _get_bot_user_id():
        return

    text = event.get("text", "").strip()
    channel = event.get("channel", "")
    ts = event.get("ts", "")
    user = event.get("user")  # None if missing — guards soul engine

    if not text:
        try:
            say(text="Send me a question or task and I'll help out.", channel=channel)
        except Exception:
            pass
        return

    log.info("DM from %s: %s", user, text[:80])

    try:
        client.reactions_add(channel=channel, timestamp=ts, name="hourglass_flowing_sand")
    except Exception:
        pass

    response = claude_handler.process(text, channel=channel, thread_ts=ts, user_id=user)
    try:
        say(text=response, channel=channel)
    except Exception as e:
        log.error("Failed to post DM response: %s", e)

    try:
        client.reactions_remove(channel=channel, timestamp=ts, name="hourglass_flowing_sand")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Startup with retry
# ---------------------------------------------------------------------------

_handler = None  # module-level ref for signal cleanup


def run_with_retry(max_retries: int = 10, base_delay: float = 5.0):
    """Start Socket Mode with exponential backoff on transient failures."""
    global _handler
    _handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    attempt = 0

    while attempt < max_retries:
        try:
            log.info("Starting Socket Mode (attempt %d/%d)...", attempt + 1, max_retries)
            start_time = time.time()
            _handler.start()
            break  # clean exit
        except KeyboardInterrupt:
            log.info("Shutting down (KeyboardInterrupt)")
            break
        except Exception as e:
            elapsed = time.time() - start_time
            # Reset backoff if we ran for >60s (was a healthy connection)
            if elapsed > 60:
                attempt = 0
                log.info("Ran %.0fs before error, resetting backoff", elapsed)
            delay = min(base_delay * (2 ** attempt), 300)  # cap at 5 min
            log.error("Socket Mode error: %s. Retrying in %.0fs...", e, delay)
            time.sleep(delay)
            attempt += 1
    else:
        log.fatal("Exhausted %d retries. Exiting.", max_retries)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------------------------

def _shutdown(signum, frame):
    log.info("Received signal %d, cleaning up...", signum)
    if _handler:
        try:
            _handler.close()
        except Exception:
            pass
    # Cleanup BEFORE close to avoid reopening connections
    for store, name in [(session_store, "sessions"), (working_memory, "working_memory")]:
        try:
            expired = store.cleanup()
            if expired:
                log.info("Cleaned up %d expired %s", expired, name)
        except Exception:
            pass
    # Close all DB connections
    for mod in [session_store, working_memory, user_models, soul_memory]:
        try:
            mod.close()
        except Exception:
            pass
    sys.exit(0)


signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Slack Socket Mode daemon for Claude Code")
    parser.add_argument("--verbose", "-v", action="store_true", help="Debug logging")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate claude CLI is available
    if not shutil.which("claude"):
        log.fatal("claude CLI not found in PATH — cannot process requests")
        sys.exit(1)

    _get_bot_user_id()
    log.info("Slack daemon starting. Listening for @mentions and DMs...")
    run_with_retry()


if __name__ == "__main__":
    main()
