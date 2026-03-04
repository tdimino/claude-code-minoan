"""
Shared Resend utilities — credential loading and HTTP helper.

Requires: requests (pip install requests)
Credentials: RESEND_API_KEY env var
             Falls back to ~/.config/env/secrets.env, then ~/.claude.json
"""

import os
import sys
import json
import requests
from typing import Any, Dict, Optional
from pathlib import Path

RESEND_API_URL = "https://api.resend.com"
DEFAULT_FROM = "Tom di Mino <tom@send.minoanmystery.org>"

# Named sender aliases — use with --from alias
FROM_ALIASES = {
    "tom": "Tom di Mino <tom@send.minoanmystery.org>",
    "kothar": "Kothar wa Khasis <kothar@send.minoanmystery.org>",
    "claudius": "Claudius, Artifex Maximus <claudius@send.minoanmystery.org>",
    "minoan": "Minoan Mystery <contact@send.minoanmystery.org>",
}

_SECRETS_ENV = Path.home() / ".config" / "env" / "secrets.env"


def _load_secrets_env() -> Dict[str, str]:
    """Load key=value pairs from ~/.config/env/secrets.env."""
    if not _SECRETS_ENV.exists():
        return {}
    env = {}
    for line in _SECRETS_ENV.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:]
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip("'\"")
    return env


def _load_claude_json() -> Dict[str, Any]:
    """Load ~/.claude.json for fallback credentials."""
    path = Path.home() / ".claude.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def get_api_key() -> str:
    """
    Get Resend API key via 3-tier fallback:
    1. RESEND_API_KEY environment variable
    2. ~/.config/env/secrets.env
    3. ~/.claude.json (under mcpServers.resend.env.RESEND_API_KEY)
    """
    key = os.environ.get("RESEND_API_KEY")
    if key:
        return key

    secrets = _load_secrets_env()
    key = secrets.get("RESEND_API_KEY")
    if key:
        return key

    config = _load_claude_json()
    key = (config.get("mcpServers", {})
           .get("resend", {})
           .get("env", {})
           .get("RESEND_API_KEY"))
    if key:
        return key

    print(
        "Error: RESEND_API_KEY not found.\n"
        "Set it in one of:\n"
        "  1. Environment variable: export RESEND_API_KEY=re_xxx\n"
        "  2. ~/.config/env/secrets.env: export RESEND_API_KEY=re_xxx\n"
        "  3. ~/.claude.json under mcpServers.resend.env",
        file=sys.stderr,
    )
    sys.exit(1)


class ResendError(Exception):
    """Raised when the Resend API returns an error."""
    def __init__(self, status: int, error_name: str, message: str):
        self.status = status
        self.error_name = error_name
        self.message = message
        super().__init__(f"[{status}] {error_name}: {message}")


def resend_request(method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
    """Make an authenticated request to the Resend API."""
    key = get_api_key()
    url = f"{RESEND_API_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    resp = requests.request(method, url, headers=headers, **kwargs)

    if resp.status_code >= 400:
        try:
            err = resp.json()
            name = err.get("name", "unknown_error")
            msg = err.get("message", resp.text)
        except json.JSONDecodeError:
            name, msg = "http_error", resp.text
        raise ResendError(resp.status_code, name, msg)

    if resp.status_code == 204 or not resp.text:
        return {}
    return resp.json()
