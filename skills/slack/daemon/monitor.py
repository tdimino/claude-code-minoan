#!/usr/bin/env python3
"""
Claudius Soul Monitor — Real-Time TUI Dashboard

Standalone Textual app that observes the daemon's SQLite databases and log
file, rendering Claudius's full inner life in real-time: cognitive stream,
soul state, user models, active sessions, and raw daemon logs.

Inspired by the Open Souls Engine's soul debugger.

Usage:
    uv run python monitor.py              # Normal mode
    textual run monitor.py --dev          # CSS hot-reload for development
"""

import json
import os
import time
from pathlib import Path

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.theme import Theme
from textual.widgets import DataTable, Footer, Header, RichLog, Static

from watcher import SQLiteWatcher

# ---------------------------------------------------------------------------
# Custom themes — soul engine emotional spectrum
# ---------------------------------------------------------------------------

_DARK_THEME = Theme(
    name="claudius-dark",
    primary="#bb86fc",      # Violet — primary branding
    secondary="#bb86fc",    # Violet — section headers
    accent="#03dac6",       # Teal — secondary sections
    foreground="#e0e0e0",
    background="#0a0a1a",   # Deep navy — cognitive stream bg
    surface="#16213e",      # Dark blue — panel bg
    panel="#1a1a2e",        # Slightly lighter — alternating rows
    success="#00ff88",      # Daemon running
    error="#ff4444",        # Daemon stopped / errors
    warning="#ffab40",      # Warnings
    dark=True,
)

_LIGHT_THEME = Theme(
    name="claudius-light",
    primary="#6200ee",      # Deep purple — primary branding
    secondary="#6200ee",    # Deep purple — section headers
    accent="#018786",       # Dark teal — secondary sections
    foreground="#1a1a1a",
    background="#ffffff",   # White — cognitive stream bg
    surface="#f5f5f5",      # Light grey — panel bg
    panel="#eeeeee",        # Slightly darker — alternating rows
    success="#00c853",      # Daemon running
    error="#d50000",        # Daemon stopped / errors
    warning="#ff6d00",      # Warnings
    dark=False,
)

# ---------------------------------------------------------------------------
# Paths — resolve relative to this script (the daemon directory)
# ---------------------------------------------------------------------------

_DAEMON_DIR = Path(__file__).parent
_MEMORY_DB = str(_DAEMON_DIR / "memory.db")
_SESSIONS_DB = str(_DAEMON_DIR / "sessions.db")
_LOG_FILE = str(_DAEMON_DIR / "logs" / "daemon.log")

# Soul memory defaults (for initial display before first poll)
_SOUL_KEYS = [
    "emotionalState",
    "currentProject",
    "currentTask",
    "currentTopic",
    "conversationSummary",
]


def _format_age(seconds: float) -> str:
    """Human-readable age string: '2m ago', '1h ago', '3d ago'."""
    if seconds < 60:
        return f"{int(seconds)}s ago"
    if seconds < 3600:
        return f"{int(seconds / 60)}m ago"
    if seconds < 86400:
        return f"{int(seconds / 3600)}h ago"
    return f"{int(seconds / 86400)}d ago"


def _format_uptime(seconds: float) -> str:
    """Format uptime: '2h14m', '5m', '1d3h'."""
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds / 60)}m"
    hours = int(seconds / 3600)
    mins = int((seconds % 3600) / 60)
    if hours < 24:
        return f"{hours}h{mins:02d}m"
    days = hours // 24
    hours = hours % 24
    return f"{days}d{hours}h"


def _truncate(text: str, max_len: int = 80) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "\u2026"


# ---------------------------------------------------------------------------
# Textual App
# ---------------------------------------------------------------------------


class SoulMonitor(App):
    """Claudius Soul Monitor — real-time TUI dashboard."""

    CSS_PATH = "monitor.css"
    TITLE = "Claudius, Artifex Maximus"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("m", "toggle_mode", "Light/Dark"),
        Binding("t", "toggle_scroll", "Auto-scroll"),
        Binding("c", "clear_stream", "Clear stream"),
        Binding("l", "clear_log", "Clear log"),
    ]

    def __init__(self):
        super().__init__()
        self.register_theme(_DARK_THEME)
        self.register_theme(_LIGHT_THEME)
        self.theme = "claudius-dark"
        self._watcher = SQLiteWatcher(_MEMORY_DB, _SESSIONS_DB)
        self._auto_scroll = True
        self._log_pos = 0  # file position for daemon.log tailing
        self._prev_soul_state: dict[str, str] = {}  # track state for diff detection

    # ── Layout ──────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="main-area"):
            # Top-left: Soul State
            with Vertical(id="soul-state-panel", classes="panel"):
                yield Static("Soul State")
                yield DataTable(id="soul-state-table")

            # Top-right: Cognitive Stream
            with Vertical(id="cognitive-panel", classes="panel"):
                yield Static("Cognitive Stream")
                yield RichLog(id="cognitive-stream", highlight=True, markup=True)

            # Bottom-left: Users
            with Vertical(id="users-panel", classes="panel"):
                yield Static("Users")
                yield DataTable(id="users-table")

            # Bottom-right: Sessions
            with Vertical(id="sessions-panel", classes="panel"):
                yield Static("Sessions")
                yield DataTable(id="sessions-table")

        # Raw log
        with Vertical(id="raw-log-panel", classes="panel"):
            yield Static("Daemon Log")
            yield RichLog(id="raw-log", highlight=True, markup=True)

        yield Footer()

    # ── Initialization ──────────────────────────────────────────────────

    def on_mount(self) -> None:
        # Soul state table — key/value pairs, no header
        soul_table = self.query_one("#soul-state-table", DataTable)
        soul_table.show_header = False
        soul_table.add_columns("Key", "Value")
        for key in _SOUL_KEYS:
            label = _camel_to_label(key)
            soul_table.add_row(label, "-", key=key)

        # Users table
        users_table = self.query_one("#users-table", DataTable)
        users_table.add_columns("User", "#", "Last Seen")

        # Sessions table
        sessions_table = self.query_one("#sessions-table", DataTable)
        sessions_table.add_columns("Channel", "Thread", "Session", "Age")

        # Start polling timers
        self.set_interval(0.5, self._poll_working_memory)
        self.set_interval(1.0, self._poll_soul_state)
        self.set_interval(1.0, self._poll_user_models)
        self.set_interval(1.0, self._poll_sessions)
        self.set_interval(1.0, self._tail_log)
        self.set_interval(2.0, self._update_status)

        # Initial status check
        self._update_status()

    # ── Polling: Working Memory → Cognitive Stream ──────────────────────

    def _poll_working_memory(self) -> None:
        entries = self._watcher.poll_working_memory()
        if not entries:
            return

        stream = self.query_one("#cognitive-stream", RichLog)
        now = time.time()

        for entry in entries:
            entry_type = entry.get("entry_type", "")
            verb = entry.get("verb", "")
            content = entry.get("content", "")
            user_id = entry.get("user_id", "")
            metadata = entry.get("metadata")
            created = entry.get("created_at", now)

            ts = time.strftime("%H:%M", time.localtime(created))
            display_name = self._watcher.resolve_user(user_id)

            line = self._format_cognitive_entry(
                ts, entry_type, verb, content, display_name, metadata
            )
            stream.write(line)

        if self._auto_scroll:
            stream.scroll_end(animate=False)

    @property
    def _is_dark(self) -> bool:
        return self.theme == "claudius-dark"

    def _format_cognitive_entry(
        self,
        ts: str,
        entry_type: str,
        verb: str,
        content: str,
        display_name: str,
        metadata: str | None,
    ) -> Text:
        """Build a Rich Text line for the cognitive stream, color-coded by type.

        Colors adapt to current theme for readability in both dark and light modes.
        """
        dark = self._is_dark
        text = Text()
        text.append(f"{ts} ", style="dim")

        if entry_type == "userMessage":
            c = "green" if dark else "#1b5e20"
            text.append(f"{display_name}: ", style=f"bold {c}")
            text.append(f'"{_truncate(content)}"', style=c)

        elif entry_type == "internalMonologue":
            v = verb or "thought"
            c = "magenta" if dark else "#7b1fa2"
            text.append(f"Claudius {v}: ", style=f"dim italic {c}")
            text.append(f'"{_truncate(content)}"', style=f"dim italic {c}")

        elif entry_type == "externalDialog":
            v = verb or "said"
            c = "cyan" if dark else "#006064"
            text.append(f"Claudius {v}: ", style=f"bold {c}")
            text.append(f'"{_truncate(content)}"', style=c)

        elif entry_type == "mentalQuery":
            result = ""
            if metadata:
                try:
                    m = json.loads(metadata) if isinstance(metadata, str) else metadata
                    result = str(m.get("result", ""))
                except (json.JSONDecodeError, TypeError):
                    pass
            q_color = "yellow" if dark else "#e65100"
            text.append("? ", style=f"dim {q_color}")
            text.append(_truncate(content, 60), style="dim")
            if result:
                text.append(" \u2192 ", style="dim")
                if result.lower() == "true":
                    style = "bold green" if dark else "bold #1b5e20"
                else:
                    style = "dim red" if dark else "dim #b71c1c"
                text.append(result, style=style)

        elif entry_type == "toolAction":
            c = "yellow" if dark else "#e65100"
            text.append("> ", style=c)
            text.append(_truncate(content), style=c)

        elif entry_type == "soulStateUpdate":
            label_style = "bold white on dark_green" if dark else "bold white on #00c853"
            text.append("> ", style=label_style)
            text.append(_truncate(content), style=label_style)

        elif entry_type == "userModelUpdate":
            label_style = "bold white on dark_blue" if dark else "bold white on #1565c0"
            text.append("> ", style=label_style)
            text.append(f"updated model for {display_name}", style=label_style)

        elif entry_type == "error":
            text.append("ERROR ", style="bold red")
            text.append(_truncate(content), style="red")

        else:
            text.append(_truncate(content), style="dim")

        return text

    # ── Polling: Soul State ─────────────────────────────────────────────

    def _poll_soul_state(self) -> None:
        state = self._watcher.poll_soul_state()
        if state is None:
            return

        table = self.query_one("#soul-state-table", DataTable)
        for key in _SOUL_KEYS:
            value = state.get(key, "")
            if not value:
                value = "-"
            try:
                table.update_cell(key, "Value", _truncate(value, 40))
            except KeyError:
                pass

        # Only push to cognitive stream if values actually changed
        diffs = {
            k: v for k, v in state.items()
            if v and self._prev_soul_state.get(k) != v
        }
        self._prev_soul_state = {k: v for k, v in state.items() if v}

        if diffs:
            stream = self.query_one("#cognitive-stream", RichLog)
            ts = time.strftime("%H:%M")
            text = Text()
            text.append(f"{ts} ", style="dim")
            dark = self.theme == "claudius-dark"
            label_style = "bold white on dark_green" if dark else "bold white on #00c853"
            value_style = "white on dark_green" if dark else "black on #b9f6ca"
            text.append("> soul state: ", style=label_style)
            parts = [f"{k}={v}" for k, v in diffs.items()]
            text.append(", ".join(parts), style=value_style)
            stream.write(text)
            if self._auto_scroll:
                stream.scroll_end(animate=False)

    # ── Polling: User Models ────────────────────────────────────────────

    def _poll_user_models(self) -> None:
        users = self._watcher.poll_user_models()
        if users is None:
            return

        table = self.query_one("#users-table", DataTable)
        table.clear()
        now = time.time()
        for u in users:
            name = u.get("display_name") or u.get("user_id", "?")
            count = str(u.get("interaction_count", 0))
            updated = u.get("updated_at", 0)
            age = _format_age(now - updated) if updated else "-"
            table.add_row(name, count, age)

    # ── Polling: Sessions ───────────────────────────────────────────────

    def _poll_sessions(self) -> None:
        sessions = self._watcher.poll_sessions()
        if sessions is None:
            return

        table = self.query_one("#sessions-table", DataTable)
        table.clear()
        now = time.time()
        for s in sessions:
            channel = s.get("channel", "?")
            thread = s.get("thread_ts", "")
            if len(thread) > 10:
                thread = thread[:10] + "\u2026"
            session_id = s.get("session_id", "")
            if len(session_id) > 8:
                session_id = session_id[:8] + "\u2026"
            last_used = s.get("last_used", 0)
            age = _format_age(now - last_used) if last_used else "-"
            table.add_row(channel, thread, session_id, age)

    # ── Log Tailing ─────────────────────────────────────────────────────

    def _tail_log(self) -> None:
        """Read new lines from daemon.log since last position."""
        if not os.path.exists(_LOG_FILE):
            return

        log_widget = self.query_one("#raw-log", RichLog)
        try:
            with open(_LOG_FILE, "r") as f:
                f.seek(self._log_pos)
                new_lines = f.readlines()
                self._log_pos = f.tell()
        except OSError:
            return

        for line in new_lines:
            line = line.rstrip()
            if not line:
                continue
            text = _colorize_log_line(line, dark=self._is_dark)
            log_widget.write(text)

        if new_lines and self._auto_scroll:
            log_widget.scroll_end(animate=False)

    # ── Status Bar ──────────────────────────────────────────────────────

    def _update_status(self) -> None:
        running, pid = self._watcher.is_daemon_running()
        uptime = self._watcher.get_daemon_uptime()

        if running:
            uptime_str = _format_uptime(uptime) if uptime else "?"
            status = f"RUNNING (pid {pid})  Uptime: {uptime_str}"
            self.sub_title = f"[{status}]"
        else:
            self.sub_title = "[STOPPED]"

    # ── Key Bindings ────────────────────────────────────────────────────

    def action_toggle_mode(self) -> None:
        if self.theme == "claudius-dark":
            self.theme = "claudius-light"
            self.notify("Light mode")
        else:
            self.theme = "claudius-dark"
            self.notify("Dark mode")

    def action_toggle_scroll(self) -> None:
        self._auto_scroll = not self._auto_scroll
        state = "ON" if self._auto_scroll else "OFF"
        self.notify(f"Auto-scroll: {state}")

    def action_clear_stream(self) -> None:
        self.query_one("#cognitive-stream", RichLog).clear()

    def action_clear_log(self) -> None:
        self.query_one("#raw-log", RichLog).clear()

    def on_unmount(self) -> None:
        self._watcher.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _camel_to_label(key: str) -> str:
    """Convert camelCase to Title Case: 'emotionalState' → 'Emotional State'."""
    import re
    words = re.sub(r"([A-Z])", r" \1", key).split()
    return " ".join(w.capitalize() for w in words)


def _colorize_log_line(line: str, dark: bool = True) -> Text:
    """Apply basic color coding to daemon log lines."""
    text = Text()
    lower = line.lower()

    if " error " in lower or "error:" in lower:
        text.append(line, style="bold red")
    elif " warning " in lower or "warn " in lower:
        c = "yellow" if dark else "#e65100"
        text.append(line, style=c)
    elif " info " in lower:
        parts = line.split(" ", 3)
        if len(parts) >= 4:
            text.append(f"{parts[0]} {parts[1]} ", style="dim")
            c = "cyan" if dark else "#006064"
            text.append(f"{parts[2]} ", style=f"dim {c}")
            text.append(parts[3], style="")
        else:
            text.append(line, style="")
    elif "soul" in lower or "pondered" in lower or "monologue" in lower:
        c = "magenta" if dark else "#7b1fa2"
        text.append(line, style=f"dim {c}")
    else:
        text.append(line, style="dim")

    return text


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = SoulMonitor()
    app.run()
