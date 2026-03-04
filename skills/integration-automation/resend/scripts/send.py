#!/usr/bin/env python3
"""
Send email via the Resend API.

Usage:
    send.py --to recipient@example.com --subject "Hello" --body "World"
    send.py --to a@x.com b@x.com --subject "Report" --html report.html
    echo "content" | send.py --to recipient@example.com --subject "Piped"
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _resend_utils import resend_request, ResendError, DEFAULT_FROM, FROM_ALIASES


def _resolve_html(html_arg: str) -> str:
    """If arg is a path to an existing .html/.htm file, read it. Otherwise treat as inline HTML."""
    path = Path(html_arg)
    if path.exists() and path.suffix.lower() in (".html", ".htm"):
        return path.read_text()
    return html_arg


def _encode_attachment(filepath: str) -> dict:
    """Read a file and return a Resend attachment dict with base64 content."""
    path = Path(filepath)
    if not path.exists():
        print(f"Error: Attachment not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    content = base64.b64encode(path.read_bytes()).decode("ascii")
    return {
        "filename": path.name,
        "content": content,
    }


def _read_stdin() -> str:
    """Read stdin if piped (not a TTY)."""
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


def main():
    parser = argparse.ArgumentParser(
        description="Send email via Resend API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Body resolution: --body > --html > stdin\nTest address: delivered@resend.dev",
    )
    parser.add_argument("--to", nargs="+", required=True, help="Recipient(s)")
    parser.add_argument("--subject", required=True, help="Subject line")
    parser.add_argument("--body", help="Plain text body")
    parser.add_argument("--html", help="HTML body: file path or inline string")
    parser.add_argument(
        "--from", dest="from_addr", default=DEFAULT_FROM,
        help=f"Sender address (default: {DEFAULT_FROM})",
    )
    parser.add_argument("--cc", nargs="+", help="CC recipient(s)")
    parser.add_argument("--bcc", nargs="+", help="BCC recipient(s)")
    parser.add_argument("--reply-to", dest="reply_to", help="Reply-to address")
    parser.add_argument("--attachments", nargs="+", help="File(s) to attach")
    parser.add_argument("--dry-run", action="store_true", help="Print payload without sending")
    args = parser.parse_args()

    # Resolve --from alias
    if args.from_addr in FROM_ALIASES:
        args.from_addr = FROM_ALIASES[args.from_addr]

    # Resolve body content
    html_content = None
    text_content = None

    if args.body is not None:
        text_content = args.body
    if args.html:
        html_content = _resolve_html(args.html)
    if text_content is None and html_content is None:
        stdin_content = _read_stdin()
        if stdin_content:
            text_content = stdin_content
        else:
            print("Error: No body content. Provide --body, --html, or pipe via stdin.", file=sys.stderr)
            sys.exit(1)

    # Build payload
    payload = {
        "from": args.from_addr,
        "to": args.to,
        "subject": args.subject,
    }

    if html_content:
        payload["html"] = html_content
    if text_content:
        payload["text"] = text_content
    if args.cc:
        payload["cc"] = args.cc
    if args.bcc:
        payload["bcc"] = args.bcc
    if args.reply_to:
        payload["reply_to"] = args.reply_to
    if args.attachments:
        payload["attachments"] = [_encode_attachment(f) for f in args.attachments]

    # Dry run
    if args.dry_run:
        display = dict(payload)
        if "attachments" in display:
            display["attachments"] = [
                {"filename": a["filename"], "content": f"<{len(a['content'])} chars base64>"}
                for a in display["attachments"]
            ]
        print(json.dumps(display, indent=2))
        return

    # Send
    try:
        result = resend_request("POST", "/emails", json=payload)
        email_id = result.get("id", "unknown")
        print(f"Sent successfully")
        print(f"  ID:      {email_id}")
        print(f"  From:    {args.from_addr}")
        print(f"  To:      {', '.join(args.to)}")
        print(f"  Subject: {args.subject}")
        if args.cc:
            print(f"  CC:      {', '.join(args.cc)}")
        if args.bcc:
            print(f"  BCC:     {', '.join(args.bcc)}")
        if args.attachments:
            print(f"  Attach:  {', '.join(Path(f).name for f in args.attachments)}")
    except ResendError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
