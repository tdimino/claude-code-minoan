#!/usr/bin/env python3
"""
List all available phone numbers across Telnyx and Twilio.

Usage:
    python3 sms_numbers.py                  # All numbers, both providers
    python3 sms_numbers.py --provider telnyx   # Telnyx only
    python3 sms_numbers.py --provider twilio   # Twilio only
    python3 sms_numbers.py --live              # Query APIs for live status (slower)
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sms_utils import (
    SMSError, telnyx_request, twilio_request,
    TELNYX_NUMBERS, TWILIO_NUMBERS,
    DEFAULT_TELNYX_FROM, DEFAULT_TWILIO_FROM,
)


def list_static():
    """Return known numbers from the hardcoded registry."""
    numbers = []
    for num, info in TELNYX_NUMBERS.items():
        default = " (default)" if num == DEFAULT_TELNYX_FROM else ""
        numbers.append({
            "number": num,
            "provider": "telnyx",
            "type": info["type"],
            "label": info["label"] + default,
            "sms": True,
            "voice": True,
        })
    for num, info in TWILIO_NUMBERS.items():
        default = " (default)" if num == DEFAULT_TWILIO_FROM else ""
        numbers.append({
            "number": num,
            "provider": "twilio",
            "type": info["type"],
            "label": info["label"] + default,
            "sms": True,
            "voice": True,
        })
    return numbers


def list_live_telnyx() -> list:
    """Query Telnyx API for live phone number status."""
    numbers = []
    try:
        result = telnyx_request("GET", "/messaging_phone_numbers", params={"page[size]": 50})
        for n in result.get("data", []):
            features = n.get("features", {})
            sms = features.get("sms", {})
            mms = features.get("mms", {})
            default = " (default)" if n.get("phone_number") == DEFAULT_TELNYX_FROM else ""
            numbers.append({
                "number": n.get("phone_number", "?"),
                "provider": "telnyx",
                "type": n.get("type", "?"),
                "label": f"profile:{n.get('messaging_profile_id', '?')[:8]}{default}",
                "sms": sms.get("domestic_two_way", False),
                "mms": mms.get("domestic_two_way", False),
                "voice": True,
            })
    except SMSError as e:
        print(f"  Warning: Telnyx API error: {e}", file=sys.stderr)
    return numbers


def list_live_twilio() -> list:
    """Query Twilio API for live phone number status."""
    numbers = []
    try:
        result = twilio_request("GET", "/IncomingPhoneNumbers.json")
        for n in result.get("incoming_phone_numbers", []):
            caps = n.get("capabilities", {})
            default = " (default)" if n.get("phone_number") == DEFAULT_TWILIO_FROM else ""
            numbers.append({
                "number": n.get("phone_number", "?"),
                "provider": "twilio",
                "type": "tollfree" if n.get("phone_number", "").startswith("+1855") else "local",
                "label": f"{n.get('friendly_name', '?')}{default}",
                "sms": caps.get("sms", False),
                "mms": caps.get("mms", False),
                "voice": caps.get("voice", False),
            })
    except SMSError as e:
        print(f"  Warning: Twilio API error: {e}", file=sys.stderr)
    return numbers


def print_numbers(numbers: list):
    if not numbers:
        print("No numbers found.")
        return

    # Header
    print(f"  {'Number':<17} {'Provider':<9} {'Type':<10} {'SMS':<5} {'Voice':<6} {'Label'}")
    print(f"  {'─'*17} {'─'*9} {'─'*10} {'─'*5} {'─'*6} {'─'*30}")

    for n in numbers:
        sms = "yes" if n.get("sms") else "no"
        voice = "yes" if n.get("voice") else "no"
        print(f"  {n['number']:<17} {n['provider']:<9} {n['type']:<10} {sms:<5} {voice:<6} {n['label']}")

    print(f"\n  Total: {len(numbers)} numbers")


def main():
    parser = argparse.ArgumentParser(description="List available SMS phone numbers")
    parser.add_argument("--provider", choices=["telnyx", "twilio"], help="Filter by provider")
    parser.add_argument("--live", action="store_true", help="Query APIs for live status")
    args = parser.parse_args()

    try:
        if args.live:
            numbers = []
            if not args.provider or args.provider == "telnyx":
                numbers.extend(list_live_telnyx())
            if not args.provider or args.provider == "twilio":
                numbers.extend(list_live_twilio())
        else:
            numbers = list_static()
            if args.provider:
                numbers = [n for n in numbers if n["provider"] == args.provider]

        print_numbers(numbers)

    except SMSError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
