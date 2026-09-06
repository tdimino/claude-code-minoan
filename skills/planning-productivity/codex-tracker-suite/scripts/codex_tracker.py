#!/usr/bin/env python3
"""Thin, read-only wrapper around Codex App Server session APIs."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import selectors
import shlex
import shutil
import subprocess
import sys
import time
from collections import deque
from pathlib import Path
from typing import Any


VERSION = "0.1.0"
ALL_SOURCES = [
    "cli",
    "vscode",
    "exec",
    "appServer",
    "subAgent",
    "subAgentReview",
    "subAgentCompact",
    "subAgentThreadSpawn",
    "subAgentOther",
    "unknown",
]
NON_INTERACTIVE_SOURCES = ["cli", "vscode", "exec", "appServer"]


class TrackerError(RuntimeError):
    pass


class AppServer:
    def __init__(self, timeout: float, verbose: bool = False):
        self.timeout = timeout
        self.verbose = verbose
        self.proc: subprocess.Popen[str] | None = None
        self.next_id = 1
        self.stderr_tail: deque[str] = deque(maxlen=30)
        self.transport = "direct"

    def __enter__(self) -> "AppServer":
        if not shutil.which("codex"):
            raise TrackerError("codex executable not found on PATH")

        codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
        socket_path = codex_home / "app-server-control" / "app-server-control.sock"
        if socket_path.exists():
            command = ["codex", "app-server", "proxy", "--sock", str(socket_path)]
            self.transport = "managed daemon proxy"
        else:
            command = ["codex", "app-server", "--stdio"]

        try:
            self.proc = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            raise TrackerError(f"could not start {' '.join(command)}: {exc}") from exc

        initialize_id = self._allocate_id()
        self._send(
            {
                "method": "initialize",
                "id": initialize_id,
                "params": {
                    "clientInfo": {
                        "name": "codex_tracker_suite",
                        "title": "Codex Tracker Suite",
                        "version": VERSION,
                    },
                    "capabilities": {"experimentalApi": True},
                },
            }
        )
        # The reference client sends this immediately after initialize.
        self._send({"method": "initialized", "params": {}})
        self._wait(initialize_id, operation="App Server initialization")
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if not self.proc:
            return
        if self.proc.stdin:
            try:
                self.proc.stdin.close()
            except OSError:
                pass
        try:
            self.proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=2)

    def _allocate_id(self) -> int:
        request_id = self.next_id
        self.next_id += 1
        return request_id

    def _send(self, message: dict[str, Any]) -> None:
        assert self.proc and self.proc.stdin
        try:
            self.proc.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise TrackerError(self._failure_message("App Server closed its input", exc)) from exc

    def request(self, method: str, params: dict[str, Any], operation: str | None = None) -> Any:
        request_id = self._allocate_id()
        self._send({"method": method, "id": request_id, "params": params})
        return self._wait(request_id, operation=operation or method)

    def _wait(self, request_id: int, operation: str) -> Any:
        assert self.proc and self.proc.stdout and self.proc.stderr
        selector = selectors.DefaultSelector()
        selector.register(self.proc.stdout, selectors.EVENT_READ, "stdout")
        selector.register(self.proc.stderr, selectors.EVENT_READ, "stderr")
        started = time.monotonic()
        deadline = started + self.timeout
        next_progress = started + 5

        try:
            while True:
                now = time.monotonic()
                if now >= deadline:
                    raise TrackerError(
                        f"timed out after {self.timeout:g}s waiting for {operation}; "
                        "retry with --timeout SECONDS or use `codex resume --all`"
                    )
                if now >= next_progress:
                    print(
                        f"Waiting for native Codex {operation} ({int(now - started)}s)…",
                        file=sys.stderr,
                        flush=True,
                    )
                    next_progress = now + 10

                events = selector.select(min(1.0, deadline - now))
                for key, _ in events:
                    line = key.fileobj.readline()
                    if not line:
                        if key.data == "stdout":
                            raise TrackerError(self._failure_message("App Server exited before responding"))
                        selector.unregister(key.fileobj)
                        continue
                    if key.data == "stderr":
                        self.stderr_tail.append(line.rstrip())
                        if self.verbose:
                            print(f"app-server: {line.rstrip()}", file=sys.stderr)
                        continue

                    try:
                        message = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise TrackerError(f"invalid JSON from App Server: {line[:200]!r}") from exc
                    if message.get("id") != request_id:
                        continue
                    if "error" in message:
                        error = message["error"]
                        detail = error.get("message", json.dumps(error)) if isinstance(error, dict) else str(error)
                        raise TrackerError(f"{operation} failed: {detail}")
                    return message.get("result")
        finally:
            selector.close()

    def _failure_message(self, message: str, exc: Exception | None = None) -> str:
        details = "\n".join(self.stderr_tail)
        suffix = f": {exc}" if exc else ""
        if details:
            return f"{message}{suffix}\n{details}"
        return f"{message}{suffix}"


def source_kinds(args: argparse.Namespace) -> list[str] | None:
    if getattr(args, "source", None):
        return args.source
    if getattr(args, "all_sources", False):
        return ALL_SOURCES
    if getattr(args, "include_non_interactive", False):
        return NON_INTERACTIVE_SOURCES
    return None


def add_connection_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.environ.get("CODEX_TRACKER_TIMEOUT", "180")),
        help="seconds to wait for each native request (default: 180)",
    )
    parser.add_argument("--verbose", action="store_true", help="show App Server diagnostics")


def add_source_options(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--include-non-interactive",
        action="store_true",
        help="include CLI, IDE, exec, and App Server sessions",
    )
    group.add_argument("--all-sources", action="store_true", help="include subagents and unknown sources")
    group.add_argument(
        "--source",
        action="append",
        choices=ALL_SOURCES,
        help="restrict to a source kind; repeat for multiple kinds",
    )


def add_output_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")


def request_params(args: argparse.Namespace, *, limit: int | None = None) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    sources = source_kinds(args)
    if sources:
        params["sourceKinds"] = sources
    if getattr(args, "archived", False):
        params["archived"] = True
    return params


def source_label(source: Any) -> str:
    if isinstance(source, str):
        return source
    if isinstance(source, dict):
        if "custom" in source:
            return str(source["custom"])
        if "subAgent" in source:
            return "subAgent"
    return "unknown"


def status_label(status: Any) -> str:
    if not isinstance(status, dict):
        return "unknown"
    kind = str(status.get("type", "unknown"))
    flags = status.get("activeFlags")
    if kind == "active" and flags:
        return f"active ({', '.join(map(str, flags))})"
    return kind


def timestamp_label(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return "unknown"
    stamp = dt.datetime.fromtimestamp(value, tz=dt.timezone.utc).astimezone()
    return stamp.isoformat(timespec="seconds")


def resume_command(thread: dict[str, Any], here: bool = False) -> str:
    command = f"codex resume {shlex.quote(str(thread['id']))}"
    cwd = thread.get("cwd")
    if cwd and not here:
        return f"cd {shlex.quote(str(cwd))} && {command}"
    return command


def print_threads(items: list[Any], *, search_results: bool = False) -> None:
    if not items:
        print("No matching Codex sessions.")
        return
    for index, item in enumerate(items, start=1):
        if search_results:
            thread = item.get("thread", {})
            snippet = item.get("snippet")
        else:
            thread = item
            snippet = None
        title = thread.get("name") or thread.get("preview") or "Untitled session"
        print(f"{index}. {title}")
        print(f"   ID:      {thread.get('id', 'unknown')}")
        print(f"   Updated: {timestamp_label(thread.get('updatedAt'))}")
        print(f"   CWD:     {thread.get('cwd', 'unknown')}")
        print(f"   Source:  {source_label(thread.get('source'))}")
        print(f"   Status:  {status_label(thread.get('status'))}")
        if snippet:
            print(f"   Match:   {' '.join(str(snippet).split())}")
        if thread.get("id"):
            print(f"   Resume:  {resume_command(thread)}")
        if index != len(items):
            print()


def extract_visible_messages(thread: dict[str, Any]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for turn in thread.get("turns", []):
        for item in turn.get("items", []):
            item_type = item.get("type")
            if item_type == "userMessage":
                parts = [
                    part.get("text", "")
                    for part in item.get("content", [])
                    if part.get("type") == "text" and part.get("text")
                ]
                if parts:
                    messages.append({"role": "user", "text": "\n".join(parts)})
            elif item_type == "agentMessage" and item.get("text"):
                messages.append({"role": "assistant", "text": str(item["text"])})
    return messages


def run_search(args: argparse.Namespace, server: AppServer) -> int:
    params = request_params(args, limit=args.limit)
    params.update(
        {
            "searchTerm": args.query,
            "sortKey": args.sort,
            "sortDirection": args.direction,
        }
    )
    try:
        result = server.request("thread/search", params, operation="full-text session search")
    except TrackerError as exc:
        message = str(exc)
        if "experimental" in message.lower() or "unknown" in message.lower() or "unsupported" in message.lower():
            raise TrackerError(
                f"native full-text search is unavailable in this Codex version: {message}\n"
                "Upgrade Codex or use `codex resume --all` and type the query in the picker."
            ) from exc
        raise
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_threads(result.get("data", []), search_results=True)
    return 0


def run_occurrences(args: argparse.Namespace, server: AppServer) -> int:
    params = {"threadId": args.session_id, "searchTerm": args.query, "limit": args.limit}
    result = server.request("thread/searchOccurrences", params, operation="in-session occurrence search")
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    items = result.get("data", [])
    if not items:
        print("No matching occurrences.")
        return 0
    for index, item in enumerate(items, start=1):
        print(f"{index}. {' '.join(str(item.get('snippet', '')).split())}")
        print(f"   Turn: {item.get('turnId', 'unknown')}")
        print(f"   Item: {item.get('itemId', 'unknown')}")
    return 0


def run_recent(args: argparse.Namespace, server: AppServer) -> int:
    params = request_params(args, limit=args.limit)
    params.update({"sortKey": args.sort, "sortDirection": args.direction})
    params["useStateDbOnly"] = not args.scan_and_repair
    result = server.request("thread/list", params, operation="recent session listing")
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_threads(result.get("data", []))
    return 0


def run_show(args: argparse.Namespace, server: AppServer) -> int:
    result = server.request(
        "thread/read",
        {"threadId": args.session_id, "includeTurns": not args.metadata_only},
        operation="session read",
    )
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    thread = result.get("thread", {})
    print_threads([thread])
    if not args.metadata_only:
        messages = extract_visible_messages(thread)
        if args.limit:
            messages = messages[-args.limit :]
        if messages:
            print("\nVisible transcript:")
            for message in messages:
                text = message["text"]
                if len(text) > args.max_chars:
                    text = text[: args.max_chars - 1] + "…"
                print(f"\n[{message['role']}]\n{text}")
    return 0


def run_alive(args: argparse.Namespace, server: AppServer) -> int:
    if server.transport != "managed daemon proxy":
        raise TrackerError(
            "alive requires the shared managed App Server daemon; a short-lived direct "
            "server cannot observe sessions loaded in other processes"
        )
    listed = server.request("thread/loaded/list", {"limit": args.limit}, operation="loaded session listing")
    threads: list[dict[str, Any]] = []
    for thread_id in listed.get("data", []):
        result = server.request(
            "thread/read",
            {"threadId": thread_id, "includeTurns": False},
            operation=f"status read for {thread_id}",
        )
        threads.append(result.get("thread", {}))
    if args.json:
        print(json.dumps({"data": threads, "nextCursor": listed.get("nextCursor")}, indent=2, ensure_ascii=False))
    else:
        print_threads(threads)
    return 0


def run_resume(args: argparse.Namespace, server: AppServer) -> int:
    result = server.request(
        "thread/read",
        {"threadId": args.session_id, "includeTurns": False},
        operation="session lookup",
    )
    thread = result.get("thread", {})
    command = resume_command(thread, here=args.here)
    if args.json:
        print(json.dumps({"thread": thread, "command": command}, indent=2, ensure_ascii=False))
    else:
        print(command)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codex-tracker",
        description="Search and inspect local Codex sessions through native App Server APIs.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="full-text search across stored Codex sessions")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--archived", action="store_true", help="search archived sessions only")
    search.add_argument("--sort", choices=["created_at", "updated_at", "recency_at"], default="updated_at")
    search.add_argument("--direction", choices=["asc", "desc"], default="desc")
    add_source_options(search)
    add_output_options(search)
    add_connection_options(search)
    search.set_defaults(handler=run_search)

    occurrences = subparsers.add_parser("occurrences", help="find matches inside one session")
    occurrences.add_argument("session_id")
    occurrences.add_argument("query")
    occurrences.add_argument("--limit", type=int, default=20)
    add_output_options(occurrences)
    add_connection_options(occurrences)
    occurrences.set_defaults(handler=run_occurrences)

    recent = subparsers.add_parser("recent", help="list recent Codex sessions")
    recent.add_argument("--limit", type=int, default=10)
    recent.add_argument("--archived", action="store_true", help="list archived sessions only")
    recent.add_argument("--sort", choices=["created_at", "updated_at", "recency_at"], default="updated_at")
    recent.add_argument("--direction", choices=["asc", "desc"], default="desc")
    recent.add_argument(
        "--scan-and-repair",
        action="store_true",
        help="scan rollout logs to repair metadata instead of using the fast state-only view",
    )
    add_source_options(recent)
    add_output_options(recent)
    add_connection_options(recent)
    recent.set_defaults(handler=run_recent)

    show = subparsers.add_parser("show", help="read one session without resuming it")
    show.add_argument("session_id")
    show.add_argument("--metadata-only", action="store_true")
    show.add_argument("--limit", type=int, default=20, help="visible messages to print, newest last")
    show.add_argument("--max-chars", type=int, default=4000, help="maximum characters per printed message")
    add_output_options(show)
    add_connection_options(show)
    show.set_defaults(handler=run_show)

    alive = subparsers.add_parser("alive", help="list sessions loaded in the native runtime")
    alive.add_argument("--limit", type=int, default=100)
    add_output_options(alive)
    add_connection_options(alive)
    alive.set_defaults(handler=run_alive)

    resume = subparsers.add_parser("resume", help="print a shell-safe native resume command")
    resume.add_argument("session_id")
    resume.add_argument("--here", action="store_true", help="omit the saved working-directory change")
    add_output_options(resume)
    add_connection_options(resume)
    resume.set_defaults(handler=run_resume)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    limit = getattr(args, "limit", None)
    if limit is not None and limit < 1:
        parser.error("--limit must be at least 1")
    if getattr(args, "timeout", 1) <= 0:
        parser.error("--timeout must be positive")
    if getattr(args, "max_chars", 1) <= 0:
        parser.error("--max-chars must be positive")
    if hasattr(args, "query") and not args.query.strip():
        parser.error("query must not be empty")
    try:
        with AppServer(timeout=args.timeout, verbose=args.verbose) as server:
            return args.handler(args, server)
    except TrackerError as exc:
        print(f"codex-tracker: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("codex-tracker: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
