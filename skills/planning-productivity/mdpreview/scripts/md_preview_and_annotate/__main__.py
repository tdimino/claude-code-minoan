#!/usr/bin/env python3
"""CLI entry point for md_preview_and_annotate.

Usage:
  python3 md_preview_and_annotate <file.md> [file2.md ...] [--port PORT] [--author NAME]
  python3 md_preview_and_annotate --add <file.md> [--port PORT]
  python3 md_preview_and_annotate --annotate <file.md> --text "..." --comment "..." [--author NAME]
"""

import datetime
import json
import os
import sys
import uuid

from . import annotations
from .server import PreviewHandler, start

DEFAULT_PORT = 3031


def _flag_value(argv, flag, default=""):
    """Safely get the value following a --flag, or return default."""
    if flag in argv:
        idx = argv.index(flag)
        if idx + 1 < len(argv):
            return argv[idx + 1]
    return default


def cmd_annotate(argv):
    """Write an annotation directly to the sidecar JSON (no server needed)."""
    idx = argv.index("--annotate")
    if idx + 1 >= len(argv):
        print("Error: --annotate requires a filepath")
        sys.exit(1)
    filepath = os.path.abspath(argv[idx + 1])

    text = _flag_value(argv, "--text")
    comment = _flag_value(argv, "--comment")
    author_name = _flag_value(argv, "--author", "Claude")

    data, _ = annotations.read(filepath)

    ann = {
        "id": uuid.uuid4().hex[:6],
        "anchor": {"text": text, "heading": "", "offset": 0},
        "author": {
            "name": author_name,
            "type": "ai" if author_name.lower() in ("claude", "ai", "assistant") else "human",
        },
        "created": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "body": comment,
        "resolved": False,
        "replies": [],
    }
    data["annotations"].append(ann)
    annotations.write(filepath, data)

    print(f"\033[38;2;166;227;161m\u2713\033[0m Annotation by {author_name} on \"{text}\"")


def cmd_add(argv):
    """POST a file to a running server, then exit."""
    import urllib.request

    idx = argv.index("--add")
    if idx + 1 >= len(argv):
        print("Error: --add requires a filepath")
        sys.exit(1)
    filepath = os.path.abspath(argv[idx + 1])
    port = int(_flag_value(argv, "--port", str(DEFAULT_PORT)))

    req_data = json.dumps({"filepath": filepath}).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/add",
        data=req_data,
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        print(f"\033[38;2;166;227;161m\u2713\033[0m Added: {result['filename']}")
    except Exception as e:
        print(f"\033[38;2;243;139;168m\u2717\033[0m Failed to add: {e}")
        sys.exit(1)


def cmd_serve(argv):
    """Start the preview server with one or more files."""
    import subprocess
    import webbrowser

    port = int(_flag_value(argv, "--port", str(DEFAULT_PORT)))
    default_author = _flag_value(argv, "--author", "Tom")

    # Collect file paths
    files = []
    skip_next = False
    for i, arg in enumerate(argv[1:], 1):
        if skip_next:
            skip_next = False
            continue
        if arg.startswith("--"):
            if arg in ("--port", "--author"):
                skip_next = True
            continue
        files.append(os.path.abspath(arg))

    if not files:
        print("Error: no files specified")
        sys.exit(1)

    PreviewHandler.default_author = default_author
    for fp in files:
        if os.path.isfile(fp):
            PreviewHandler.add_tab(fp)
        else:
            print(f"Warning: {fp} not found, skipping")

    if not PreviewHandler._tabs:
        print("Error: no valid files to open")
        sys.exit(1)

    server = start(port)

    filenames = [os.path.basename(t["filepath"]) for t in PreviewHandler._tabs.values()]
    print(f"\033[38;2;137;180;250m\U0001f4c4 {', '.join(filenames)}\033[0m")
    print(f"\033[38;2;166;227;161m\U0001f310 http://127.0.0.1:{port}\033[0m")
    features = "Live reload \u00b7 Catppuccin \u00b7 Tabs \u00b7 Annotations"
    print(f"\033[38;2;88;91;112m\u26a1 {features}\033[0m")
    print("\nCtrl+C to stop")

    # Launch in Chrome --app mode
    url = f"http://127.0.0.1:{port}"
    chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    ]
    chrome = next((p for p in chrome_paths if os.path.exists(p)), None)
    if chrome:
        subprocess.Popen(
            [chrome, f"--app={url}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\033[38;2;88;91;112mStopped.\033[0m")
        server.server_close()


def main():
    if "--annotate" in sys.argv:
        cmd_annotate(sys.argv)
        sys.exit(0)

    if "--add" in sys.argv:
        cmd_add(sys.argv)
        sys.exit(0)

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 md_preview_and_annotate <file.md> [file2.md ...] [--port PORT] [--author NAME]")
        print("  python3 md_preview_and_annotate --add <file.md> [--port PORT]")
        print('  python3 md_preview_and_annotate --annotate <file.md> --text "..." --comment "..." [--author NAME]')
        sys.exit(1)

    cmd_serve(sys.argv)


if __name__ == "__main__":
    main()
