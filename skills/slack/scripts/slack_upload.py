#!/usr/bin/env python3
"""
Upload files to Slack using the new 2-step external upload API.
(files.upload was deprecated March 2025)

Usage:
    slack_upload.py "#general" ./report.pdf
    slack_upload.py "#general" ./chart.png --title "Q1 Results" --message "Here's the chart"
    slack_upload.py "#general" ./data.csv --thread 1234567890.123456
    slack_upload.py "#general" --snippet "print('hello')" --filetype python

Requires: SLACK_BOT_TOKEN environment variable
"""

import argparse
import json
import os
import sys
import tempfile

import requests

sys.path.insert(0, os.path.dirname(__file__))
from _slack_utils import slack_api, resolve_channel, SlackError, SLACK_BOT_TOKEN


def upload_file(channel_id: str, filepath: str, title: str = None,
                message: str = None, thread_ts: str = None) -> dict:
    """
    Upload a file using the 2-step external upload API.

    Step 1: files.getUploadURLExternal — get a presigned upload URL
    Step 2: POST the file content to the presigned URL
    Step 3: files.completeUploadExternal — finalize and share to channel
    """
    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)
    title = title or filename

    # Step 1: Get upload URL
    url_resp = slack_api("files.getUploadURLExternal",
                         filename=filename, length=filesize)
    upload_url = url_resp["upload_url"]
    file_id = url_resp["file_id"]

    # Step 2: POST file content to presigned URL (official docs: POST with multipart form)
    try:
        with open(filepath, "rb") as f:
            post_resp = requests.post(upload_url, files={"file": (filename, f)})
            post_resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise SlackError("files.upload", "upload_failed",
                         f"POST to presigned URL failed: {e}")

    # Step 3: Complete upload
    files_param = [{"id": file_id, "title": title}]
    complete_params = {"files": files_param}

    if channel_id:
        complete_params["channel_id"] = channel_id
    if message:
        complete_params["initial_comment"] = message
    if thread_ts:
        complete_params["thread_ts"] = thread_ts

    return slack_api("files.completeUploadExternal", **complete_params)


def upload_snippet(channel_id: str, content: str, filetype: str = "text",
                   title: str = "snippet", message: str = None,
                   thread_ts: str = None) -> dict:
    """Upload a text snippet as a file."""
    ext_map = {
        "python": ".py", "javascript": ".js", "typescript": ".ts",
        "ruby": ".rb", "go": ".go", "rust": ".rs", "bash": ".sh",
        "json": ".json", "yaml": ".yaml", "markdown": ".md",
        "text": ".txt", "html": ".html", "css": ".css", "sql": ".sql",
    }
    ext = ext_map.get(filetype, ".txt")

    with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False, prefix="slack_") as f:
        f.write(content)
        tmppath = f.name

    try:
        return upload_file(channel_id, tmppath, title=title,
                          message=message, thread_ts=thread_ts)
    finally:
        os.unlink(tmppath)


def main():
    parser = argparse.ArgumentParser(description="Upload files to Slack")
    parser.add_argument("channel", help="Channel name (#general) or ID")
    parser.add_argument("file", nargs="?", help="File path to upload")
    parser.add_argument("--title", help="File title")
    parser.add_argument("--message", help="Message to accompany the file")
    parser.add_argument("--thread", help="Thread timestamp")
    parser.add_argument("--snippet", help="Upload text content as a snippet (instead of file)")
    parser.add_argument("--filetype", default="text",
                        help="Snippet language (python, javascript, json, etc.)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    try:
        channel_id = resolve_channel(args.channel)

        if args.snippet:
            result = upload_snippet(channel_id, args.snippet, args.filetype,
                                   args.title or "snippet", args.message, args.thread)
        elif args.file:
            if not os.path.exists(args.file):
                print(f"Error: File not found: {args.file}", file=sys.stderr)
                sys.exit(1)
            result = upload_file(channel_id, args.file, args.title,
                               args.message, args.thread)
        else:
            print("Error: Provide a file path or --snippet content", file=sys.stderr)
            sys.exit(1)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            files = result.get("files", [])
            if files:
                f = files[0]
                print(f"Uploaded: {f.get('title', 'file')} (id: {f.get('id', '')})")
            else:
                print("Upload completed.")

    except SlackError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
