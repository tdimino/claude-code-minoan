#!/usr/bin/env python3
"""Keenable setup — validate API key and configure MCP server."""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error

API_BASE = "https://api.keenable.ai"


def validate_key():
    api_key = os.environ.get("KEENABLE_API_KEY")
    if not api_key:
        print("FAIL: KEENABLE_API_KEY not set")
        print("Add to ~/.config/env/secrets.env:")
        print('  export KEENABLE_API_KEY="keen_..."')
        return False

    if not api_key.startswith("keen_"):
        print(f"WARN: Key doesn't start with 'keen_' — got '{api_key[:8]}...'")

    req = urllib.request.Request(
        f"{API_BASE}/v1/search",
        data=json.dumps({"query": "test", "max_results": 1}).encode(),
        headers={
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
            print(f"OK: API key valid (HTTP {resp.status})")
            return True
    except urllib.error.HTTPError as e:
        print(f"FAIL: HTTP {e.code} — {e.reason}")
        if e.code == 401:
            print("Key is invalid or expired. Get a new one at https://app.keenable.ai")
        return False
    except urllib.error.URLError as e:
        print(f"FAIL: Connection error — {e.reason}")
        return False


def setup_mcp():
    api_key = os.environ.get("KEENABLE_API_KEY", "")
    if not api_key:
        print("Error: KEENABLE_API_KEY must be set before MCP setup", file=sys.stderr)
        return False

    cmd = [
        "claude", "mcp", "add", "keenable",
        "--transport", "http", f"{API_BASE}/mcp",
        "--scope", "user",
        "--header", f"X-API-Key: {api_key}",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("OK: Keenable MCP server added to Claude Code")
            print("Restart Claude Code for the MCP server to be available")
            return True
        else:
            print(f"FAIL: {result.stderr.strip()}")
            print("\nManual setup:")
            print(f'  claude mcp add keenable --transport http {API_BASE}/mcp --scope user --header "X-API-Key: $KEENABLE_API_KEY"')
            return False
    except FileNotFoundError:
        print("FAIL: 'claude' CLI not found")
        print("\nManual setup:")
        print(f'  claude mcp add keenable --transport http {API_BASE}/mcp --scope user --header "X-API-Key: $KEENABLE_API_KEY"')
        return False


def main():
    parser = argparse.ArgumentParser(description="Setup and validate Keenable AI")
    parser.add_argument("--validate", action="store_true", help="Test API key")
    parser.add_argument("--setup-mcp", action="store_true", dest="setup_mcp",
                        help="Add Keenable MCP server to Claude Code")

    args = parser.parse_args()

    if not args.validate and not args.setup_mcp:
        parser.print_help()
        sys.exit(1)

    ok = True
    if args.validate:
        ok = validate_key() and ok
    if args.setup_mcp:
        ok = setup_mcp() and ok

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
