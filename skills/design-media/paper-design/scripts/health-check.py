#!/usr/bin/env python3
"""
Purpose: Verify Paper Design MCP server is running and accessible
Usage: python3 ~/.claude/skills/paper-design/scripts/health-check.py
Outputs: Status for each check with fix instructions
"""

import subprocess
import sys
import urllib.request
import urllib.error

PAPER_MCP_URL = "http://127.0.0.1:29979/mcp"
checks_passed = 0
checks_total = 3

print("=== Paper Design Health Check ===\n")

# Check 1: Paper Desktop process running
print("1. Paper Desktop process...")
try:
    result = subprocess.run(
        ["pgrep", "-f", "Paper.app/Contents/MacOS"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("   [OK] Paper Desktop is running")
        checks_passed += 1
    else:
        print("   [FAIL] Paper Desktop is not running")
        print("   Fix: Open /Applications/Paper.app")
except Exception as e:
    print(f"   [FAIL] Could not check process: {e}")

# Check 2: MCP server reachable
print("2. MCP server reachable...")
try:
    req = urllib.request.Request(PAPER_MCP_URL, method="GET")
    with urllib.request.urlopen(req, timeout=5) as resp:
        print(f"   [OK] MCP server responded (HTTP {resp.status})")
        checks_passed += 1
except urllib.error.HTTPError as e:
    # HTTP 4xx/5xx means server is reachable — MCP uses POST, not GET
    print(f"   [OK] MCP server is reachable (HTTP {e.code} on GET — expected)")
    checks_passed += 1
except urllib.error.URLError as e:
    print(f"   [FAIL] Cannot reach {PAPER_MCP_URL}")
    print("   Fix: Open Paper Desktop — MCP server starts automatically")
    print(f"   Error: {e.reason}")
except Exception as e:
    print(f"   [FAIL] Unexpected error: {e}")
    print("   Fix: Open Paper Desktop and try again")

# Check 3: MCP registered in Claude Code
print("3. MCP registered in Claude Code...")
try:
    result = subprocess.run(
        ["claude", "mcp", "list"],
        capture_output=True, text=True, timeout=10
    )
    if "paper" in result.stdout.lower():
        print("   [OK] 'paper' found in claude mcp list")
        checks_passed += 1
    else:
        print("   [FAIL] 'paper' not registered")
        print("   Fix: bash ~/.claude/skills/paper-design/scripts/setup.sh")
except FileNotFoundError:
    print("   [SKIP] 'claude' CLI not found in PATH")
except Exception as e:
    print(f"   [FAIL] Could not check: {e}")

# Summary
print(f"\n=== Result: {checks_passed}/{checks_total} checks passed ===")
if checks_passed == checks_total:
    print("Paper Design MCP is ready.")
else:
    print("Fix the issues above and run this check again.")
    sys.exit(1)
