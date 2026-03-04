#!/usr/bin/env python3
"""
Send SMS/MMS to any number via Telnyx or Twilio.

Usage:
    python3 sms_send.py TO "MESSAGE"
    python3 sms_send.py TO "MESSAGE" --from "+18334843851"
    python3 sms_send.py TO "MESSAGE" --provider twilio
    python3 sms_send.py TO "MESSAGE" --media "https://example.com/image.jpg"
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sms_utils import (
    normalize_e164, resolve_from_and_provider, SMSError,
    telnyx_request, twilio_request, TELNYX_MESSAGING_PROFILE_ID,
    log_message,
)


def send_telnyx(to: str, body: str, from_number: str, media_url: str = None) -> dict:
    payload = {
        "from": from_number,
        "to": to,
        "text": body,
        "messaging_profile_id": TELNYX_MESSAGING_PROFILE_ID,
    }
    if media_url:
        payload["media_urls"] = [media_url]
        payload["type"] = "MMS"
    result = telnyx_request("POST", "/messages", json=payload)
    data = result.get("data", {})
    return {
        "id": data.get("id", "unknown"),
        "status": data.get("to", [{}])[0].get("status", "unknown") if isinstance(data.get("to"), list) else "queued",
        "provider": "telnyx",
        "from": from_number,
        "to": to,
    }


def send_twilio(to: str, body: str, from_number: str, media_url: str = None) -> dict:
    payload = {
        "From": from_number,
        "To": to,
        "Body": body,
    }
    if media_url:
        payload["MediaUrl"] = media_url
    result = twilio_request("POST", "/Messages.json", data=payload)
    return {
        "id": result.get("sid", "unknown"),
        "status": result.get("status", "unknown"),
        "provider": "twilio",
        "from": from_number,
        "to": to,
    }


def main():
    parser = argparse.ArgumentParser(description="Send SMS/MMS via Telnyx or Twilio")
    parser.add_argument("to", help="Destination phone number")
    parser.add_argument("message", help="Message body")
    parser.add_argument("--from", dest="from_number", help="From phone number (auto-detects provider)")
    parser.add_argument("--provider", choices=["telnyx", "twilio"], help="Force provider")
    parser.add_argument("--media", help="Media URL for MMS")
    args = parser.parse_args()

    to = normalize_e164(args.to)
    from_number, provider = resolve_from_and_provider(args.from_number, args.provider)

    try:
        if provider == "telnyx":
            result = send_telnyx(to, args.message, from_number, args.media)
        else:
            result = send_twilio(to, args.message, from_number, args.media)

        # Log to local message history
        log_message({
            "direction": "outbound",
            "from": result["from"],
            "to": result["to"],
            "body": args.message,
            "status": result["status"],
            "provider": result["provider"],
            "id": result["id"],
        })

        print(f"Sent via {result['provider']}")
        print(f"  From: {result['from']}")
        print(f"  To:   {result['to']}")
        print(f"  ID:   {result['id']}")
        print(f"  Status: {result['status']}")

    except SMSError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
