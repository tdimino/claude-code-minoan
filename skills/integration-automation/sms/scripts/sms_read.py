#!/usr/bin/env python3
"""
Read SMS inbox — recent messages to/from your numbers.

Usage:
    python3 sms_read.py                           # Last 10 messages, default provider
    python3 sms_read.py -n 20                     # Last 20 messages
    python3 sms_read.py --to "+18508058037"        # Messages to a specific number
    python3 sms_read.py --from-number "+19175551234"  # Messages from a specific sender
    python3 sms_read.py --direction inbound        # Only incoming
    python3 sms_read.py --provider twilio          # Force Twilio
    python3 sms_read.py --all-providers            # Query both providers
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sms_utils import (
    normalize_e164, resolve_from_and_provider, SMSError,
    telnyx_request, twilio_request, format_timestamp, truncate,
    DEFAULT_PROVIDER, read_message_log, log_message,
)


def read_telnyx(to: str = None, from_number: str = None, direction: str = None, limit: int = 10) -> list:
    params = {"page[size]": min(limit, 250)}
    if direction == "inbound":
        params["direction"] = "inbound"
    elif direction == "outbound":
        params["direction"] = "outbound"

    try:
        result = telnyx_request("GET", "/messages", params=params)
    except SMSError as e:
        if e.status == 404:
            # Telnyx has no GET /messages endpoint — fall back to local log
            local = read_message_log(
                their_number=from_number or to,
                our_number=to if from_number else None,
                direction=direction,
                provider="telnyx",
                limit=limit,
            )
            if local:
                print(f"  (Showing {len(local)} messages from local log — Telnyx is send-only)", file=sys.stderr)
            return local
        raise
    messages = []
    for msg in result.get("data", []):
        msg_to = msg.get("to", [{}])
        to_number = msg_to[0].get("phone_number", "?") if isinstance(msg_to, list) else str(msg_to)
        msg_from = msg.get("from", {})
        from_num = msg_from.get("phone_number", "?") if isinstance(msg_from, dict) else str(msg_from)
        msg_dir = msg.get("direction", "?")

        # Apply filters
        if to and normalize_e164(to) not in (normalize_e164(to_number),):
            continue
        if from_number and normalize_e164(from_number) != normalize_e164(from_num):
            continue

        messages.append({
            "timestamp": msg.get("received_at") or msg.get("sent_at") or msg.get("created_at", "?"),
            "direction": msg_dir,
            "from": from_num,
            "to": to_number,
            "body": msg.get("text", ""),
            "status": msg.get("to", [{}])[0].get("status", "?") if isinstance(msg.get("to"), list) else "?",
            "provider": "telnyx",
            "id": msg.get("id", "?"),
        })

    return messages[:limit]


def read_twilio(to: str = None, from_number: str = None, direction: str = None, limit: int = 10) -> list:
    params = {"PageSize": min(limit, 100)}
    if to:
        params["To"] = normalize_e164(to)
    if from_number:
        params["From"] = normalize_e164(from_number)

    result = twilio_request("GET", "/Messages.json", params=params)
    messages = []
    for msg in result.get("messages", []):
        msg_dir = msg.get("direction", "")
        if direction == "inbound" and "inbound" not in msg_dir:
            continue
        if direction == "outbound" and "outbound" not in msg_dir:
            continue

        messages.append({
            "timestamp": msg.get("date_sent") or msg.get("date_created", "?"),
            "direction": "inbound" if "inbound" in msg_dir else "outbound",
            "from": msg.get("from", "?"),
            "to": msg.get("to", "?"),
            "body": msg.get("body", ""),
            "status": msg.get("status", "?"),
            "provider": "twilio",
            "id": msg.get("sid", "?"),
        })

    return messages[:limit]


def print_messages(messages: list):
    if not messages:
        print("No messages found.")
        return

    for msg in messages:
        arrow = "←" if msg["direction"] == "inbound" else "→"
        ts = format_timestamp(msg["timestamp"])
        body = truncate(msg["body"], 100)
        provider_tag = f"[{msg['provider'][:3]}]"
        print(f"  {ts}  {provider_tag} {msg['from']} {arrow} {msg['to']}  {body}")
        if msg["status"] not in ("?", "delivered", "sent", "received"):
            print(f"                          Status: {msg['status']}")


def main():
    parser = argparse.ArgumentParser(description="Read SMS inbox")
    parser.add_argument("--to", help="Filter: messages to this number")
    parser.add_argument("--from-number", help="Filter: messages from this number")
    parser.add_argument("--direction", choices=["inbound", "outbound"], help="Filter by direction")
    parser.add_argument("-n", "--limit", type=int, default=10, help="Number of messages (default: 10)")
    parser.add_argument("--provider", choices=["telnyx", "twilio"], help="Query specific provider")
    parser.add_argument("--all-providers", action="store_true", help="Query both providers")
    args = parser.parse_args()

    try:
        messages = []

        if args.all_providers:
            providers = ["telnyx", "twilio"]
        elif args.provider:
            providers = [args.provider]
        else:
            providers = [DEFAULT_PROVIDER]

        for provider in providers:
            if provider == "telnyx":
                messages.extend(read_telnyx(args.to, args.from_number, args.direction, args.limit))
            else:
                messages.extend(read_twilio(args.to, args.from_number, args.direction, args.limit))

        # Sort by timestamp (newest first)
        messages.sort(key=lambda m: m["timestamp"], reverse=True)
        messages = messages[:args.limit]

        print(f"Messages ({len(messages)}):")
        print_messages(messages)

    except SMSError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
