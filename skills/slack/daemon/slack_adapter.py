"""
Slack Socket Mode adapter.

Receives @mentions and DMs via Socket Mode, routes them to an async callback.
Extracted from bot.py for use by the unified Claudius launcher.
"""

import asyncio
import logging
import os
import re
import threading
from typing import Callable, Optional

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import soul_memory
from config import BLOCKED_CHANNELS

log = logging.getLogger("claudius.slack")

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")


class SlackAdapter:
    """Receives Slack events and routes them to async callbacks."""

    def __init__(
        self,
        on_message: Callable,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        if not SLACK_BOT_TOKEN:
            raise RuntimeError("SLACK_BOT_TOKEN not set")
        if not SLACK_APP_TOKEN:
            raise RuntimeError("SLACK_APP_TOKEN not set (needed for Socket Mode)")

        self.app = App(token=SLACK_BOT_TOKEN)
        self._on_message = on_message
        self._loop = loop
        self._bot_user_id = ""
        self._handler: Optional[SocketModeHandler] = None
        self._setup_handlers()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_bot_user_id(self) -> str:
        if not self._bot_user_id:
            resp = self.app.client.auth_test()
            self._bot_user_id = resp.get("user_id", "")
            log.info("Bot user ID: %s", self._bot_user_id)
        return self._bot_user_id

    def _strip_mention(self, text: str) -> str:
        bot_id = self._get_bot_user_id()
        if bot_id:
            return re.sub(rf"<@{bot_id}>\s*", "", text).strip()
        return re.sub(r"<@\w+>\s*", "", text, count=1).strip()

    def _is_blocked(self, channel: str) -> bool:
        return channel in BLOCKED_CHANNELS

    def _resolve_display_name(self, user_id: str) -> str:
        try:
            resp = self.app.client.users_info(user=user_id)
            profile = resp.get("user", {}).get("profile", {})
            return (
                profile.get("display_name")
                or profile.get("real_name")
                or user_id
            )
        except Exception:
            return user_id

    def _dispatch(self, text, channel, thread_ts, user_id, display_name=None):
        """Schedule the async callback from the Slack bolt thread."""
        if not display_name:
            display_name = self._resolve_display_name(user_id)

        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._on_message(text, channel, thread_ts, user_id, display_name),
                self._loop,
            )
        else:
            log.warning("Event loop not running, dropping message from %s", user_id)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _setup_handlers(self):
        @self.app.event("app_mention")
        def handle_mention(event, client):
            channel = event.get("channel", "")
            ts = event.get("ts", "")
            thread_ts = event.get("thread_ts", ts)
            text = self._strip_mention(event.get("text", ""))
            user = event.get("user")

            if event.get("user") == self._get_bot_user_id():
                return
            if self._is_blocked(channel):
                return
            if not text:
                return

            log.info("@mention from %s in %s: %s", user, channel, text[:80])
            self._dispatch(text, channel, thread_ts, user)

        @self.app.event("message")
        def handle_dm(event, client):
            if event.get("channel_type") != "im":
                return
            if event.get("subtype"):
                return
            if event.get("user") == self._get_bot_user_id():
                return

            text = event.get("text", "").strip()
            channel = event.get("channel", "")
            ts = event.get("ts", "")
            user = event.get("user")

            if not text:
                return

            log.info("DM from %s: %s", user, text[:80])
            self._dispatch(text, channel, ts, user)

        @self.app.event("app_home_opened")
        def handle_app_home(event, client):
            user_id = event.get("user", "")
            try:
                state = soul_memory.get_all()
                blocks = self._build_app_home_blocks(state)
                client.views_publish(
                    user_id=user_id,
                    view={"type": "home", "blocks": blocks},
                )
            except Exception as e:
                log.error("Failed to publish App Home for %s: %s", user_id, e)

    def _build_app_home_blocks(self, state: dict) -> list:
        """Build Block Kit blocks for the App Home tab."""
        emotion = state.get("emotionalState", "neutral")
        project = state.get("currentProject", "")
        task = state.get("currentTask", "")
        topic = state.get("currentTopic", "")
        summary = state.get("conversationSummary", "")

        soul_fields = [
            {"type": "mrkdwn", "text": f"*Emotional State:*\n{emotion}"},
        ]
        if project:
            soul_fields.append({"type": "mrkdwn", "text": f"*Current Project:*\n{project}"})
        if task:
            soul_fields.append({"type": "mrkdwn", "text": f"*Current Task:*\n{task}"})
        if topic:
            soul_fields.append({"type": "mrkdwn", "text": f"*Current Topic:*\n{topic}"})

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Claudius, Artifex Maximus", "emoji": True},
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "Unified launcher \u2022 Claude Agent SDK \u2022 Socket Mode"},
                ],
            },
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": "*Soul State*"}},
            {"type": "section", "fields": soul_fields[:10]},
        ]

        if summary:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Recent Context:*\n{summary[:300]}"},
            })

        blocks.extend([
            {"type": "divider"},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": (
                    "*How to interact:*\n"
                    "\u2022 *DM* \u2014 just type, no @ needed\n"
                    "\u2022 *Channel* \u2014 mention me with `@Claude Code`\n"
                    "\u2022 Each thread maintains a separate session"
                )},
            },
        ])

        return blocks

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        """Start Socket Mode in a background daemon thread."""
        if loop:
            self._loop = loop
        self._get_bot_user_id()

        # Set presence
        try:
            self.app.client.users_setPresence(presence="auto")
            log.info("Set bot presence to auto")
        except Exception as e:
            log.warning("Could not set presence: %s", e)

        self._handler = SocketModeHandler(self.app, SLACK_APP_TOKEN)
        thread = threading.Thread(target=self._handler.start, daemon=True, name="slack-socket")
        thread.start()
        log.info("Slack Socket Mode started in background thread")

    def stop(self):
        """Stop Socket Mode handler."""
        if self._handler:
            try:
                self._handler.close()
            except Exception:
                pass

    def post(self, channel: str, text: str, thread_ts: Optional[str] = None):
        """Post a message to Slack."""
        kwargs = {"channel": channel, "text": text}
        if thread_ts:
            kwargs["thread_ts"] = thread_ts
        try:
            self.app.client.chat_postMessage(**kwargs)
        except Exception as e:
            log.error("Failed to post to %s: %s", channel, e)

    def react(self, channel: str, ts: str, emoji: str, remove: bool = False):
        """Add or remove a reaction."""
        try:
            if remove:
                self.app.client.reactions_remove(channel=channel, timestamp=ts, name=emoji)
            else:
                self.app.client.reactions_add(channel=channel, timestamp=ts, name=emoji)
        except Exception:
            pass
