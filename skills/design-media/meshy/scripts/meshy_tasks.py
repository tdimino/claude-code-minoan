#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""
Meshy task management — list, get, download, and balance.

Usage:
    uv run meshy_tasks.py list                              # recent text-to-3d tasks
    uv run meshy_tasks.py list --endpoint image-to-3d       # recent image-to-3d tasks
    uv run meshy_tasks.py get TASK_ID                       # task detail
    uv run meshy_tasks.py get TASK_ID --watch               # poll until done
    uv run meshy_tasks.py download TASK_ID --format glb     # download model
    uv run meshy_tasks.py balance                           # credit balance
"""

import argparse
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from _meshy_utils import MeshyClient, MeshyError


def cmd_list(client: MeshyClient, args):
    tasks = client.list_tasks(
        endpoint=args.endpoint,
        page_num=args.page,
        page_size=args.page_size,
    )
    if args.json:
        print(json.dumps(tasks, indent=2))
        return

    if not tasks:
        print("No tasks found.")
        return

    print(f"Recent {args.endpoint} tasks (page {args.page}):\n")
    for t in tasks:
        tid = t.get("id", t.get("task_id", "?"))
        status = t.get("status", "?")
        progress = t.get("progress") or "?"
        prompt = t.get("prompt", "")[:50]
        created_raw = t.get("created_at", "?")
        if isinstance(created_raw, (int, float)):
            from datetime import datetime, timezone
            created = datetime.fromtimestamp(created_raw / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        else:
            created = str(created_raw)[:19]
        print(f"  {tid}  {status:12s}  {progress:>3}%  {created}  {prompt}")


def cmd_get(client: MeshyClient, args):
    if args.watch:
        task = client.poll_task(
            args.task_id,
            endpoint=args.endpoint,
            quiet=args.json,
            label=args.task_id[:12],
        )
    else:
        task = client.get_task(args.task_id, endpoint=args.endpoint)

    if args.json:
        print(json.dumps(task, indent=2))
        return

    status = task.get("status", "?")
    progress = task.get("progress", "?")
    prompt = task.get("prompt", "")[:80]
    model_urls = task.get("model_urls", {})
    created = task.get("created_at", "?")

    print(f"Task: {args.task_id}")
    print(f"  Status:   {status} ({progress}%)")
    print(f"  Created:  {created}")
    if prompt:
        print(f"  Prompt:   {prompt}")
    if model_urls:
        print(f"  Models:")
        for fmt, url in model_urls.items():
            print(f"    {fmt}: {url[:80]}...")


def cmd_download(client: MeshyClient, args):
    task = client.get_task(args.task_id, endpoint=args.endpoint)
    status = task.get("status", "?")

    if status != "SUCCEEDED":
        print(f"Task {args.task_id} is {status}, cannot download.", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output)
    path = client.download_model(
        task,
        output_dir=output_dir,
        filename=args.filename or args.task_id[:12],
        format=args.format,
    )

    if args.json:
        print(json.dumps({"path": str(path), "format": args.format}))
    elif path:
        size_kb = path.stat().st_size / 1024
        print(f"Downloaded: {path} ({size_kb:.0f} KB)")
    else:
        print("Download failed.", file=sys.stderr)
        sys.exit(1)


def cmd_balance(client: MeshyClient, args):
    balance = client.get_balance()
    if args.json:
        print(json.dumps(balance, indent=2))
    else:
        credits = balance.get("credit_balance", balance.get("credits", "?"))
        print(f"Credit balance: {credits}")


def main():
    parser = argparse.ArgumentParser(description="Meshy task management")
    parser.add_argument("--api-key", help="Override MESHY_API_KEY")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")

    sub = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = sub.add_parser("list", help="List recent tasks")
    p_list.add_argument("--endpoint", default="text-to-3d",
                        choices=["text-to-3d", "image-to-3d", "text-to-texture"],
                        help="API endpoint (default: text-to-3d)")
    p_list.add_argument("--page", type=int, default=1, help="Page number")
    p_list.add_argument("--page-size", type=int, default=20, help="Results per page")

    # get
    p_get = sub.add_parser("get", help="Get task details")
    p_get.add_argument("task_id", help="Task ID")
    p_get.add_argument("--endpoint", default="text-to-3d",
                       choices=["text-to-3d", "image-to-3d", "text-to-texture"])
    p_get.add_argument("--watch", action="store_true", help="Poll until done")

    # download
    p_dl = sub.add_parser("download", help="Download model from completed task")
    p_dl.add_argument("task_id", help="Task ID")
    p_dl.add_argument("--endpoint", default="text-to-3d",
                      choices=["text-to-3d", "image-to-3d", "text-to-texture"])
    p_dl.add_argument("--format", default="glb", choices=["glb", "gltf", "usdz", "fbx"])
    p_dl.add_argument("--output", default="./output", help="Output directory")
    p_dl.add_argument("--filename", default="", help="Output filename (no extension)")

    # balance
    sub.add_parser("balance", help="Check credit balance")

    args = parser.parse_args()
    client = MeshyClient(api_key=args.api_key)

    commands = {
        "list": cmd_list,
        "get": cmd_get,
        "download": cmd_download,
        "balance": cmd_balance,
    }
    commands[args.command](client, args)


if __name__ == "__main__":
    main()
