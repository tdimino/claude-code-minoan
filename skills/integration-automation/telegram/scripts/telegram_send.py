#!/usr/bin/env python3
"""
Send a Telegram message as Claudicle.

Wraps the Telegram Bot API (via HTTP/requests) with parse_mode, inline keyboards,
reply threading, and stdin support. Uses REST directly — no asyncio, no
python-telegram-bot runtime dependency. This matters because Python 3.9 has an
asyncio event loop bug that breaks the python-telegram-bot library in some
subprocess contexts; the REST approach sidesteps it entirely.

Messages longer than 4096 chars are split on newline boundaries via
`split_message` from the adapter's `_telegram_utils`.

Usage:
    python3 telegram_send.py CHAT_ID "text" [--reply-to MSG_ID]
                                            [--parse-mode Markdown|MarkdownV2|HTML]
                                            [--buttons JSON]
                                            [--stdin]
                                            [--silent]

Examples:
    # Plain text
    python3 telegram_send.py 633125581 "Dispatch sent."

    # Markdown
    python3 telegram_send.py 633125581 "*bold* _italic_" --parse-mode Markdown

    # Reply threading
    python3 telegram_send.py 633125581 "Acknowledged" --reply-to 42

    # Inline keyboard (one row, two buttons)
    python3 telegram_send.py 633125581 "Approve dispatch?" \\
        --buttons '[["Approve|approve_day42","Reject|reject_day42"]]'

    # Two stacked rows
    python3 telegram_send.py 633125581 "Choose:" \\
        --buttons '[["Option A|opt_a"],["Option B|opt_b"]]'

    # Stdin pipe
    echo "Daily report" | python3 telegram_send.py 633125581 --stdin

Requires:
    TELEGRAM_BOT_TOKEN in ~/.config/env/secrets.env
    pip install --break-system-packages requests
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests

def split_message(text: str, max_length: int = 4096) -> list[str]:
    """Split long messages for Telegram's 4096-char limit, breaking on newlines."""
    if len(text) <= max_length:
        return [text]
    chunks: list[str] = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break
        split_point = text.rfind("\n", 0, max_length)
        if split_point <= 0:
            split_point = max_length
        chunks.append(text[:split_point])
        text = text[split_point:].lstrip("\n")
    return chunks


TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def load_secrets():
    """Source ~/.config/env/secrets.env into os.environ (idempotent)."""
    secrets_path = Path.home() / ".config" / "env" / "secrets.env"
    if not secrets_path.exists():
        return
    for line in secrets_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key.startswith("export "):
            key = key[7:].strip()
        val = val.strip().strip("'\"")
        os.environ.setdefault(key, val)


def parse_buttons(buttons_json: str) -> dict:
    """
    Parse --buttons JSON into Telegram InlineKeyboardMarkup structure.

    Input format: list of rows, each row is a list of "Label|callback_data" strings.
        [["Approve|approve_day42","Reject|reject_day42"]]
        [["Option A|opt_a"],["Option B|opt_b"]]

    Button strings may also be "Label|url:https://..." to emit a URL button
    instead of a callback_data button.
    """
    try:
        rows = json.loads(buttons_json)
    except json.JSONDecodeError as e:
        print(f"Error: --buttons is not valid JSON: {e}", file=sys.stderr)
        sys.exit(2)

    if not isinstance(rows, list):
        print("Error: --buttons must be a list of rows", file=sys.stderr)
        sys.exit(2)

    keyboard = []
    for row in rows:
        if not isinstance(row, list):
            print("Error: each row in --buttons must be a list", file=sys.stderr)
            sys.exit(2)
        parsed_row = []
        for btn in row:
            if not isinstance(btn, str) or "|" not in btn:
                print(f"Error: button {btn!r} must be 'Label|callback_data'", file=sys.stderr)
                sys.exit(2)
            label, _, data = btn.partition("|")
            label = label.strip()
            data = data.strip()
            if data.startswith("url:"):
                parsed_row.append({"text": label, "url": data[4:]})
            else:
                parsed_row.append({"text": label, "callback_data": data})
        keyboard.append(parsed_row)

    return {"inline_keyboard": keyboard}


def send_message(
    chat_id: str,
    text: str,
    token: str,
    reply_to: int | None = None,
    parse_mode: str | None = None,
    reply_markup: dict | None = None,
    silent: bool = False,
) -> dict:
    """Send one message via the Telegram Bot API. Returns the response JSON."""
    url = TELEGRAM_API.format(token=token, method="sendMessage")
    payload: dict = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if silent:
        payload["disable_notification"] = True

    try:
        r = requests.post(url, json=payload, timeout=30)
        data = r.json()
    except requests.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    if not data.get("ok"):
        print(f"Error: Telegram API returned {data}", file=sys.stderr)
        sys.exit(1)
    return data


def main():
    parser = argparse.ArgumentParser(
        description="Send a Telegram message as Claudicle.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("chat_id", help="Telegram chat ID (numeric) or channel @name")
    parser.add_argument(
        "text",
        nargs="?",
        default=None,
        help="Message text (omit and use --stdin to pipe text from stdin)",
    )
    parser.add_argument("--reply-to", type=int, default=None, help="Message ID to reply to")
    parser.add_argument(
        "--parse-mode",
        choices=["Markdown", "MarkdownV2", "HTML"],
        default=None,
        help="Telegram parse mode (default: plain text)",
    )
    parser.add_argument(
        "--buttons",
        default=None,
        help='Inline keyboard as JSON: [["Label|callback_data",...],...]',
    )
    parser.add_argument("--stdin", action="store_true", help="Read text from stdin")
    parser.add_argument(
        "--silent", action="store_true", help="Send without notification sound"
    )
    args = parser.parse_args()

    load_secrets()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    # Resolve text
    if args.stdin:
        text = sys.stdin.read()
    elif args.text is not None:
        text = args.text
    else:
        parser.error("must provide text argument or --stdin")

    if not text.strip():
        print("Error: empty message", file=sys.stderr)
        sys.exit(1)

    reply_markup = parse_buttons(args.buttons) if args.buttons else None

    # Split long messages. Inline keyboard attaches only to the final chunk
    # so it's still tappable on the "most recent" message in the conversation.
    chunks = split_message(text)
    sent = []
    for i, chunk in enumerate(chunks):
        is_last = i == len(chunks) - 1
        resp = send_message(
            chat_id=args.chat_id,
            text=chunk,
            token=token,
            reply_to=args.reply_to if i == 0 else None,
            parse_mode=args.parse_mode,
            reply_markup=reply_markup if is_last else None,
            silent=args.silent,
        )
        sent.append(resp.get("result", {}).get("message_id"))

    # Print message IDs to stdout (one per line) so callers can capture them.
    for msg_id in sent:
        if msg_id is not None:
            print(msg_id)


if __name__ == "__main__":
    main()
