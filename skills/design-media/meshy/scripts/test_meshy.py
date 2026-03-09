#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""
Test Meshy API connectivity and validate credentials.

Usage:
    uv run test_meshy.py           # Full suite (0 credits)
    uv run test_meshy.py --quick   # API key + balance only
    uv run test_meshy.py --live    # Submit a real preview (~5 credits)
    uv run test_meshy.py --json    # Machine-readable output
"""

import argparse
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from _meshy_utils import MeshyClient, MeshyError, get_api_key


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.details: list[dict] = []

    def record_pass(self, name: str, info: str = ""):
        self.passed += 1
        self.details.append({"name": name, "status": "PASS", "info": info})

    def record_fail(self, name: str, error: str):
        self.failed += 1
        self.details.append({"name": name, "status": "FAIL", "error": error})

    def record_skip(self, name: str, reason: str):
        self.skipped += 1
        self.details.append({"name": name, "status": "SKIP", "reason": reason})

    def summary(self, as_json: bool = False) -> str:
        if as_json:
            return json.dumps({
                "passed": self.passed,
                "failed": self.failed,
                "skipped": self.skipped,
                "success": self.failed == 0,
                "tests": self.details,
            }, indent=2)

        lines = ["\nMeshy API Test Results", "=" * 40]
        for d in self.details:
            status = d["status"]
            name = d["name"]
            extra = d.get("info") or d.get("error") or d.get("reason") or ""
            lines.append(f"  {status:4s}  {name:30s}  {extra}")
        lines.append("=" * 40)
        lines.append(f"  Passed: {self.passed}  Failed: {self.failed}  Skipped: {self.skipped}")
        return "\n".join(lines)


def test_api_key(results: TestResults):
    try:
        key = get_api_key()
        if key and len(key) > 8:
            results.record_pass("api_key", f"Set ({key[:6]}...{key[-4:]})")
        else:
            results.record_fail("api_key", "Key too short or empty")
    except SystemExit:
        results.record_fail("api_key", "MESHY_API_KEY not found")


def test_balance(results: TestResults, client: MeshyClient):
    try:
        balance = client.get_balance()
        credits = balance.get("credit_balance", balance.get("credits", "?"))
        results.record_pass("balance", f"Credits: {credits}")
    except MeshyError as e:
        results.record_fail("balance", str(e))
    except Exception as e:
        results.record_fail("balance", str(e))


def test_list_tasks(results: TestResults, client: MeshyClient, endpoint: str):
    try:
        tasks = client.list_tasks(endpoint=endpoint, page_size=5)
        count = len(tasks) if isinstance(tasks, list) else "?"
        results.record_pass(f"list_{endpoint}", f"Found {count} recent tasks")
    except MeshyError as e:
        results.record_fail(f"list_{endpoint}", str(e))
    except Exception as e:
        results.record_fail(f"list_{endpoint}", str(e))


def test_live_preview(results: TestResults, client: MeshyClient):
    try:
        task_id = client.create_text_to_3d(
            "a simple red cube, low poly, game ready",
            mode="preview",
            model_type="lowpoly",
        )
        if task_id:
            results.record_pass("live_preview", f"Task created: {task_id}")
        else:
            results.record_fail("live_preview", "No task_id returned")
    except MeshyError as e:
        results.record_fail("live_preview", str(e))
    except Exception as e:
        results.record_fail("live_preview", str(e))


def main():
    parser = argparse.ArgumentParser(description="Test Meshy API connectivity")
    parser.add_argument("--quick", action="store_true", help="API key + balance only")
    parser.add_argument("--live", action="store_true", help="Submit a real preview (~5 credits)")
    parser.add_argument("--api-key", help="Override MESHY_API_KEY")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    args = parser.parse_args()

    results = TestResults()

    # Always test API key
    test_api_key(results)
    if results.failed > 0:
        print(results.summary(as_json=args.json))
        sys.exit(1)

    client = MeshyClient(api_key=args.api_key)

    # Balance
    test_balance(results, client)

    if not args.quick:
        # List tasks (only text-to-3d is guaranteed to have a list endpoint)
        test_list_tasks(results, client, "text-to-3d")

    if args.live:
        test_live_preview(results, client)

    print(results.summary(as_json=args.json))
    sys.exit(0 if results.failed == 0 else 1)


if __name__ == "__main__":
    main()
