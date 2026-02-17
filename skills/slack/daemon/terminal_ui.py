"""
Terminal UI for the Claudius unified launcher.

Provides an async input loop and activity log for monitoring
Slack messages alongside terminal interactions.
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import Callable, Awaitable

log = logging.getLogger("claudius.terminal")


class TerminalUI:
    """Simple async terminal with input prompt and activity logging."""

    def __init__(self, on_input: Callable[[str], Awaitable[None]]):
        self._on_input = on_input
        self._running = False

    def log_activity(self, tag: str, text: str, color: str = ""):
        """Print a timestamped activity line."""
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{ts}] [{tag}]"
        # Truncate long messages for the log
        display = text[:200].replace("\n", " ")
        print(f"{prefix} {display}")

    def log_slack_in(self, user: str, channel: str, text: str):
        self.log_activity(f"Slack ← {channel}", f"{user}: {text}")

    def log_slack_out(self, channel: str, text: str):
        self.log_activity(f"Slack → {channel}", text)

    def log_terminal_response(self, text: str):
        """Display full Claude response for terminal messages."""
        print(f"\n{text}\n")

    def log_error(self, text: str):
        self.log_activity("ERROR", text)

    async def input_loop(self):
        """Read terminal input in an async loop."""
        self._running = True
        loop = asyncio.get_event_loop()

        while self._running:
            try:
                text = await loop.run_in_executor(None, self._read_input)
                if text is None:
                    # EOF (Ctrl+D)
                    break
                text = text.strip()
                if not text:
                    continue
                await self._on_input(text)
            except (EOFError, KeyboardInterrupt):
                break

        self._running = False

    def _read_input(self) -> str | None:
        """Blocking input read, run in executor."""
        try:
            return input("You > ")
        except EOFError:
            return None

    def stop(self):
        self._running = False
