#!/usr/bin/env python3
"""
View SMS conversation thread with a specific phone number.

Usage:
    python3 sms_conversation.py "+19175551234"
    python3 sms_conversation.py "+19175551234" -n 20
    python3 sms_conversation.py "+19175551234" --our-number "+18508058037"
    python3 sms_conversation.py "+19175551234" --provider twilio
    python3 sms_conversation.py "+19175551234" --all-providers
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sms_utils import (
    normalize_e164, resolve_from_and_provider, detect_provider, SMSError,
    telnyx_request, twilio_request, format_timestamp, read_message_log,
    TELNYX_NUMBERS, TWILIO_NUMBERS, DEFAULT_PROVIDER,
)


def conversation_twilio(their_number: str, our_number: str = None, limit: int = 20) -> list:
    """Fetch conversation with a number via Twilio — both directions."""
    messages = []

    # Messages FROM them TO us
    params_in = {"From": their_number, "PageSize": limit}
    if our_number:
        params_in["To"] = our_number
    try:
        result = twilio_request("GET", "/Messages.json", params=params_in)
        for msg in result.get("messages", []):
            messages.append({
                "timestamp": msg.get("date_sent") or msg.get("date_created", "?"),
                "direction": "inbound",
                "from": msg.get("from", "?"),
                "to": msg.get("to", "?"),
                "body": msg.get("body", ""),
                "status": msg.get("status", "?"),
                "provider": "twilio",
            })
    except SMSError:
        pass

    # Messages FROM us TO them
    params_out = {"To": their_number, "PageSize": limit}
    if our_number:
        params_out["From"] = our_number
    try:
        result = twilio_request("GET", "/Messages.json", params=params_out)
        for msg in result.get("messages", []):
            messages.append({
                "timestamp": msg.get("date_sent") or msg.get("date_created", "?"),
                "direction": "outbound",
                "from": msg.get("from", "?"),
                "to": msg.get("to", "?"),
                "body": msg.get("body", ""),
                "status": msg.get("status", "?"),
                "provider": "twilio",
            })
    except SMSError:
        pass

    return messages


def conversation_telnyx(their_number: str, our_number: str = None, limit: int = 20) -> list:
    """Fetch conversation with a number via Telnyx — both directions."""
    messages = []

    # Telnyx messages API doesn't filter by phone number directly in GET /messages
    # We fetch recent messages and filter client-side
    try:
        result = telnyx_request("GET", "/messages", params={"page[size]": min(limit * 4, 250)})
    except SMSError as e:
        if e.status == 404:
            # Telnyx has no GET /messages — fall back to local log
            local = read_message_log(
                their_number=their_number,
                our_number=our_number,
                provider="telnyx",
                limit=limit,
            )
            if local:
                print(f"  (Showing {len(local)} messages from local log — Telnyx is send-only)", file=sys.stderr)
            return local
        return []

    for msg in result.get("data", []):
        msg_to_list = msg.get("to", [{}])
        to_number = msg_to_list[0].get("phone_number", "?") if isinstance(msg_to_list, list) else str(msg_to_list)
        msg_from = msg.get("from", {})
        from_num = msg_from.get("phone_number", "?") if isinstance(msg_from, dict) else str(msg_from)

        their = normalize_e164(their_number)
        involves_them = (normalize_e164(from_num) == their or normalize_e164(to_number) == their)
        if not involves_them:
            continue

        if our_number:
            our = normalize_e164(our_number)
            involves_us = (normalize_e164(from_num) == our or normalize_e164(to_number) == our)
            if not involves_us:
                continue

        direction = msg.get("direction", "outbound")
        messages.append({
            "timestamp": msg.get("received_at") or msg.get("sent_at") or msg.get("created_at", "?"),
            "direction": direction,
            "from": from_num,
            "to": to_number,
            "body": msg.get("text", ""),
            "status": msg_to_list[0].get("status", "?") if isinstance(msg_to_list, list) else "?",
            "provider": "telnyx",
        })

    return messages


def print_conversation(messages: list, their_number: str):
    if not messages:
        print(f"No conversation found with {their_number}")
        return

    # Deduplicate by timestamp+body (both directions might return same msg)
    seen = set()
    unique = []
    for msg in messages:
        key = (msg["timestamp"], msg["body"], msg["direction"])
        if key not in seen:
            seen.add(key)
            unique.append(msg)

    # Sort chronologically (oldest first for conversation flow)
    unique.sort(key=lambda m: m["timestamp"])

    print(f"Conversation with {their_number} ({len(unique)} messages):")
    print("─" * 70)

    for msg in unique:
        ts = format_timestamp(msg["timestamp"])
        if msg["direction"] == "inbound":
            prefix = f"  {their_number} →"
        else:
            prefix = f"  {msg['from']} →"

        body = msg["body"].replace("\n", "\n    ") if msg["body"] else "(empty)"
        provider_tag = f"[{msg['provider'][:3]}]"
        print(f"  {ts}  {provider_tag} {prefix}")
        print(f"    {body}")
        print()


def main():
    parser = argparse.ArgumentParser(description="View SMS conversation with a phone number")
    parser.add_argument("number", help="Their phone number")
    parser.add_argument("-n", "--limit", type=int, default=20, help="Max messages per direction (default: 20)")
    parser.add_argument("--our-number", help="Filter to conversation from/to a specific one of our numbers")
    parser.add_argument("--provider", choices=["telnyx", "twilio"], help="Query specific provider")
    parser.add_argument("--all-providers", action="store_true", help="Query both providers")
    args = parser.parse_args()

    their_number = normalize_e164(args.number)
    our_number = normalize_e164(args.our_number) if args.our_number else None

    try:
        messages = []

        if args.all_providers:
            providers = ["telnyx", "twilio"]
        elif args.provider:
            providers = [args.provider]
        elif our_number:
            providers = [detect_provider(our_number)]
        else:
            providers = [DEFAULT_PROVIDER]

        for provider in providers:
            if provider == "telnyx":
                messages.extend(conversation_telnyx(their_number, our_number, args.limit))
            else:
                messages.extend(conversation_twilio(their_number, our_number, args.limit))

        print_conversation(messages, their_number)

    except SMSError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
