"""
Slack daemon configuration.

All settings can be overridden via environment variables prefixed with SLACK_DAEMON_.
"""

import os

# Channel filtering
ALLOWED_CHANNELS = None  # None = all channels bot is in
BLOCKED_CHANNELS: set = set()  # Channel IDs to never respond in

# Response limits
MAX_RESPONSE_LENGTH = 3000  # Slack message limit ~4000 chars; leave headroom

# Claude Code invocation
CLAUDE_TIMEOUT = int(os.environ.get("SLACK_DAEMON_TIMEOUT", "120"))
CLAUDE_CWD = os.path.expanduser(
    os.environ.get("SLACK_DAEMON_CWD", "~/Desktop/Programming")
)
CLAUDE_ALLOWED_TOOLS = os.environ.get(
    "SLACK_DAEMON_TOOLS", "Read,Glob,Grep,Bash,WebFetch"
)

# Session expiry
SESSION_TTL_HOURS = int(os.environ.get("SLACK_DAEMON_SESSION_TTL", "24"))

# Soul engine
SOUL_ENGINE_ENABLED = os.environ.get("SLACK_DAEMON_SOUL_ENGINE", "true").lower() == "true"
WORKING_MEMORY_WINDOW = int(os.environ.get("SLACK_DAEMON_MEMORY_WINDOW", "20"))
USER_MODEL_UPDATE_INTERVAL = int(os.environ.get("SLACK_DAEMON_USER_MODEL_INTERVAL", "5"))
WORKING_MEMORY_TTL_HOURS = int(os.environ.get("SLACK_DAEMON_MEMORY_TTL", "72"))
SOUL_STATE_UPDATE_INTERVAL = int(os.environ.get("SLACK_DAEMON_SOUL_STATE_INTERVAL", "3"))

# Terminal session (unified launcher)
TERMINAL_SESSION_TOOLS = os.environ.get(
    "SLACK_DAEMON_TERMINAL_TOOLS",
    "Read,Glob,Grep,Bash,WebFetch,Edit,Write",
)
TERMINAL_SOUL_ENABLED = os.environ.get(
    "SLACK_DAEMON_TERMINAL_SOUL", "false"
).lower() == "true"

# Logging
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
