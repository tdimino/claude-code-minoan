"""
Shared SMS utilities — config, provider abstraction, HTTP helpers.

All sms_*.py scripts import from this module.

Requires: requests (pip install requests)
Credentials: TELNYX_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN env vars
             Falls back to ~/.config/env/secrets.env, then ~/.claude.json
"""

import os
import sys
import json
import re
import requests
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

# ── Provider Phone Number Registry ──────────────────────────────────────────

TELNYX_NUMBERS = {
    "+18628026208": {"type": "longcode", "label": "Telnyx primary"},
    "+18334843851": {"type": "tollfree", "label": "Telnyx toll-free"},
}

TWILIO_NUMBERS = {
    "+18776882519": {"type": "local", "label": "877 number"},
    "+18665517616": {"type": "local", "label": "866 number"},
    "+18778377603": {"type": "local", "label": "877-837 number"},
    "+18665650327": {"type": "local", "label": "866-565 number"},
    "+18667056747": {"type": "local", "label": "866-705 number"},
    "+18557066006": {"type": "tollfree", "label": "Claudius 855"},
    "+18559149834": {"type": "tollfree", "label": "855 number"},
    "+18445491928": {"type": "local", "label": "844 number"},
    "+13205950420": {"type": "local", "label": "Claudius 320 (needs 10DLC)"},
}

# Defaults — override with --from flag
DEFAULT_TELNYX_FROM = "+18628026208"
DEFAULT_TWILIO_FROM = "+18557066006"
DEFAULT_PROVIDER = "telnyx"

TELNYX_MESSAGING_PROFILE_ID = "40019a09-498f-45b1-98e4-ca1339a3babc"


# ── Credential Loading ──────────────────────────────────────────────────────

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
        # Strip optional 'export ' prefix
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


def _get_credential(name: str) -> Optional[str]:
    """Look up a credential from env vars, then secrets.env."""
    val = os.environ.get(name)
    if val:
        return val
    secrets = _load_secrets_env()
    return secrets.get(name)


def get_telnyx_api_key() -> str:
    """Get Telnyx API key from env vars, secrets.env, or ~/.claude.json."""
    key = _get_credential("TELNYX_API_KEY")
    if key:
        return key
    config = _load_claude_json()
    key = config.get("mcpServers", {}).get("telnyx", {}).get("env", {}).get("TELNYX_API_KEY")
    if key:
        return key
    print("Error: TELNYX_API_KEY not found in env vars, ~/.config/env/secrets.env, or ~/.claude.json", file=sys.stderr)
    sys.exit(1)


def get_twilio_credentials() -> Tuple[str, str]:
    """Get Twilio Account SID and Auth Token from env vars, secrets.env, or hardcoded fallback."""
    sid = _get_credential("TWILIO_ACCOUNT_SID")
    token = _get_credential("TWILIO_AUTH_TOKEN")
    if sid and token:
        return sid, token
    if not sid or not token:
        print("Error: TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in env or ~/.config/env/secrets.env.", file=sys.stderr)
    return sid or "", token or ""


# ── Phone Number Utilities ──────────────────────────────────────────────────

def normalize_e164(number: str) -> str:
    """Normalize a phone number to E.164 format (+1XXXXXXXXXX for US)."""
    digits = re.sub(r"[^\d+]", "", number)
    if digits.startswith("+"):
        return digits
    if digits.startswith("1") and len(digits) == 11:
        return f"+{digits}"
    if len(digits) == 10:
        return f"+1{digits}"
    return f"+{digits}"


def detect_provider(from_number: str) -> str:
    """Detect provider from a from-number by checking known registries."""
    if from_number in TELNYX_NUMBERS:
        return "telnyx"
    if from_number in TWILIO_NUMBERS:
        return "twilio"
    return DEFAULT_PROVIDER


def get_default_from(provider: str) -> str:
    """Get the default from-number for a provider."""
    if provider == "telnyx":
        return DEFAULT_TELNYX_FROM
    return DEFAULT_TWILIO_FROM


def resolve_from_and_provider(from_number: Optional[str], provider: Optional[str]) -> Tuple[str, str]:
    """
    Resolve the from-number and provider from user flags.

    Priority:
    1. If --from given, detect provider from number (unless --provider also given)
    2. If --provider given without --from, use that provider's default number
    3. If neither, use DEFAULT_PROVIDER and its default number
    """
    if from_number:
        from_number = normalize_e164(from_number)
        if not provider:
            provider = detect_provider(from_number)
        return from_number, provider

    if provider:
        return get_default_from(provider), provider

    return get_default_from(DEFAULT_PROVIDER), DEFAULT_PROVIDER


# ── HTTP Helpers ────────────────────────────────────────────────────────────

class SMSError(Exception):
    """Raised when an SMS API call fails."""
    def __init__(self, provider: str, status: int, detail: str):
        self.provider = provider
        self.status = status
        self.detail = detail
        super().__init__(f"[{provider}] HTTP {status}: {detail}")


def telnyx_request(method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
    """Make a request to the Telnyx API."""
    key = get_telnyx_api_key()
    url = f"https://api.telnyx.com/v2{endpoint}"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    resp = requests.request(method, url, headers=headers, **kwargs)
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("errors", [{}])[0].get("detail", resp.text)
        except (json.JSONDecodeError, IndexError, KeyError):
            detail = resp.text
        raise SMSError("telnyx", resp.status_code, detail)
    if resp.status_code == 204 or not resp.text:
        return {}
    return resp.json()


def twilio_request(method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
    """Make a request to the Twilio API."""
    sid, token = get_twilio_credentials()
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}{endpoint}"
    resp = requests.request(method, url, auth=(sid, token), **kwargs)
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("message", resp.text)
        except (json.JSONDecodeError, KeyError):
            detail = resp.text
        raise SMSError("twilio", resp.status_code, detail)
    return resp.json()


# ── Local Message Log ──────────────────────────────────────────────────────

MESSAGE_LOG_PATH = Path(__file__).parent.parent / "data" / "messages.jsonl"


def log_message(msg: Dict[str, Any]) -> None:
    """Append a message record to the local JSONL log."""
    MESSAGE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": msg.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        "direction": msg.get("direction", "outbound"),
        "from": msg.get("from", "?"),
        "to": msg.get("to", "?"),
        "body": msg.get("body", ""),
        "status": msg.get("status", "?"),
        "provider": msg.get("provider", "?"),
        "id": msg.get("id", "?"),
    }
    with open(MESSAGE_LOG_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")


def read_message_log(
    their_number: str = None,
    our_number: str = None,
    direction: str = None,
    provider: str = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Read messages from the local JSONL log, with optional filters."""
    if not MESSAGE_LOG_PATH.exists():
        return []

    messages = []
    for line in MESSAGE_LOG_PATH.read_text().strip().split("\n"):
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        if direction and msg.get("direction") != direction:
            continue
        if provider and msg.get("provider") != provider:
            continue
        if their_number:
            their = normalize_e164(their_number)
            involves = normalize_e164(msg.get("from", "")) == their or normalize_e164(msg.get("to", "")) == their
            if not involves:
                continue
        if our_number:
            our = normalize_e164(our_number)
            involves = normalize_e164(msg.get("from", "")) == our or normalize_e164(msg.get("to", "")) == our
            if not involves:
                continue

        messages.append(msg)

    # Most recent first
    messages.sort(key=lambda m: m.get("timestamp", ""), reverse=True)
    return messages[:limit]


# ── Inbound Inbox ─────────────────────────────────────────────────────────

INBOX_PATH = Path(__file__).parent.parent / "data" / "inbox.jsonl"
LISTENER_PID_PATH = Path(__file__).parent.parent / "data" / "listener.pid"
LISTENER_STATE_PATH = Path(__file__).parent.parent / "data" / "listener_state.json"


def append_inbox(entry: Dict[str, Any]) -> None:
    """Append an inbound message to the inbox JSONL file."""
    INBOX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INBOX_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def read_inbox(
    filter_handled: bool = True,
    from_number: Optional[str] = None,
    provider: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Read messages from the inbound inbox JSONL file."""
    if not INBOX_PATH.exists():
        return []

    messages = []
    for line in INBOX_PATH.read_text().strip().split("\n"):
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        if filter_handled and msg.get("handled"):
            continue
        if provider and msg.get("provider") != provider:
            continue
        if from_number:
            if normalize_e164(msg.get("from", "")) != normalize_e164(from_number):
                continue

        messages.append(msg)

    # Most recent first
    messages.sort(key=lambda m: m.get("ts", 0), reverse=True)
    if limit:
        messages = messages[:limit]
    return messages


def mark_inbox_handled(message_id: str) -> bool:
    """Mark a specific inbox message as handled by its ID. Returns True if found."""
    if not INBOX_PATH.exists():
        return False
    lines = INBOX_PATH.read_text().strip().split("\n")
    found = False
    new_lines = []
    for line in lines:
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            new_lines.append(line)
            continue
        if msg.get("id") == message_id:
            msg["handled"] = True
            found = True
        new_lines.append(json.dumps(msg))
    if found:
        INBOX_PATH.write_text("\n".join(new_lines) + "\n")
    return found


def mark_all_inbox_handled() -> int:
    """Mark all inbox messages as handled. Returns count marked."""
    if not INBOX_PATH.exists():
        return 0
    lines = INBOX_PATH.read_text().strip().split("\n")
    count = 0
    new_lines = []
    for line in lines:
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            new_lines.append(line)
            continue
        if not msg.get("handled"):
            msg["handled"] = True
            count += 1
        new_lines.append(json.dumps(msg))
    if count:
        INBOX_PATH.write_text("\n".join(new_lines) + "\n")
    return count


def get_listener_pid() -> Optional[int]:
    """Read listener PID file and check if the process is alive. Returns PID or None."""
    try:
        pid = int(LISTENER_PID_PATH.read_text().strip())
        os.kill(pid, 0)  # Check liveness
        return pid
    except (FileNotFoundError, ValueError, OSError):
        return None


# ── Formatting ──────────────────────────────────────────────────────────────

def format_timestamp(ts: str) -> str:
    """Parse ISO 8601 or RFC 2822 timestamp to readable local time."""
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z"):
        try:
            dt = datetime.strptime(ts, fmt)
            return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    # Twilio uses RFC 2822
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(ts)
        return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        pass
    return ts


def truncate(text: str, max_len: int = 80) -> str:
    """Truncate text with ellipsis."""
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    if len(text) <= max_len:
        return text
    return text[:max_len - 1] + "…"
