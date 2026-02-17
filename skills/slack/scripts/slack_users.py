#!/usr/bin/env python3
"""
List and lookup Slack workspace users.

Usage:
    slack_users.py                          # List all users
    slack_users.py --active                 # Active humans only (no bots)
    slack_users.py --info U12345678         # Get user details
    slack_users.py --email tom@aldea.ai     # Lookup by email

Requires: SLACK_BOT_TOKEN environment variable
"""

import argparse
import json
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
from _slack_utils import slack_api, paginate, SlackError


def list_users() -> list:
    return paginate("users.list", "members")


def get_user_info(user_id: str) -> dict:
    data = slack_api("users.info", user=user_id)
    return data.get("user", {})


def lookup_by_email(email: str) -> dict:
    data = slack_api("users.lookupByEmail", email=email)
    return data.get("user", {})


def format_user(user: dict) -> str:
    profile = user.get("profile", {})
    name = profile.get("display_name") or profile.get("real_name", "unnamed")
    uid = user.get("id", "")
    email = profile.get("email", "")
    title = profile.get("title", "")
    is_bot = user.get("is_bot", False)
    deleted = user.get("deleted", False)

    status = []
    if is_bot:
        status.append("bot")
    if deleted:
        status.append("deactivated")
    if user.get("is_admin"):
        status.append("admin")
    if user.get("is_owner"):
        status.append("owner")

    tags = f" [{', '.join(status)}]" if status else ""
    line = f"  {name:<25} {uid}{tags}"
    if email:
        line += f"\n    {email}"
    if title:
        line += f" — {title}"
    return line


def main():
    parser = argparse.ArgumentParser(description="List and lookup Slack users")
    parser.add_argument("--info", help="Get details for a user ID")
    parser.add_argument("--email", help="Lookup user by email address")
    parser.add_argument("--active", action="store_true", help="Only active human users (exclude bots/deactivated)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    try:
        if args.info:
            user = get_user_info(args.info)
            if args.json:
                print(json.dumps(user, indent=2))
            else:
                profile = user.get("profile", {})
                print(f"Name: {profile.get('real_name', '')}")
                print(f"Display: {profile.get('display_name', '')}")
                print(f"ID: {user.get('id', '')}")
                print(f"Email: {profile.get('email', '')}")
                print(f"Title: {profile.get('title', '')}")
                print(f"Timezone: {user.get('tz', '')}")
                print(f"Admin: {user.get('is_admin', False)}")
                print(f"Bot: {user.get('is_bot', False)}")
                print(f"Deleted: {user.get('deleted', False)}")

        elif args.email:
            user = lookup_by_email(args.email)
            if args.json:
                print(json.dumps(user, indent=2))
            else:
                profile = user.get("profile", {})
                name = profile.get("real_name", "")
                print(f"{name} ({user.get('id', '')}) — {args.email}")

        else:
            users = list_users()

            if args.active:
                users = [u for u in users
                         if not u.get("is_bot") and not u.get("deleted")
                         and u.get("id") != "USLACKBOT"]

            users.sort(key=lambda u: (u.get("profile", {}).get("real_name", "") or "").lower())

            if args.json:
                print(json.dumps(users, indent=2))
            else:
                print(f"{'='*60}")
                print(f"Users ({len(users)})")
                print(f"{'='*60}")
                for u in users:
                    print(format_user(u))

    except SlackError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
