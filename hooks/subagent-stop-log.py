#!/usr/bin/env python3
"""SubagentStop logger with failure detection.

Logs every subagent completion to ~/.claude/agent-spawn.log with an `issues`
array flagging problems:

  - empty_output         : last_assistant_message is empty
  - tiny_output          : last_assistant_message < 100 chars
  - no_assistant_message : field missing entirely
  - max_tokens_truncation: subagent transcript ended with stop_reason=max_tokens
  - output_at_cap        : aggregate output_tokens >= 30000 (near 32K cap)
  - high_tool_error_rate : >50% of tool calls returned is_error (≥4 calls)
  - transcript_unreadable: couldn't open agent_transcript_path

Each entry also gets `n_tool_calls` and `n_tool_errors` for raw counts.

No blocking, no context injection. Triage with:
  jq 'select(.issues | length > 0)' ~/.claude/agent-spawn.log
"""

import json
import os
import sys
import time

LOG = os.path.expanduser("~/.claude/agent-spawn.log")
NEAR_CAP = 30000  # Near the 32K subagent output cap


def inspect_transcript(path: str) -> tuple[list[str], int, int, int]:
    """Read subagent JSONL. Returns (issues, total_output_tokens, n_tool_calls, n_tool_errors).

    Tool errors live in user messages with content blocks of type 'tool_result'
    where 'is_error' is true. Common causes: file-not-found, parameter validation,
    sibling-tool-errored cascades. Audit found 40% of subagents have ≥1 such error.
    """
    issues = []
    total_output = 0
    n_tool_calls = 0
    n_tool_errors = 0
    if not path:
        return ["transcript_unreadable"], 0, 0, 0

    expanded = os.path.expanduser(path)
    if not os.path.exists(expanded):
        return ["transcript_unreadable"], 0, 0, 0

    try:
        last_stop_reason = None
        seen_msg_ids = {}  # last-wins dedup for streaming chunks
        with open(expanded) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                etype = entry.get("type")
                if etype == "assistant" and "message" in entry:
                    msg = entry["message"]
                    usage = msg.get("usage", {})
                    msg_id = msg.get("id", "")
                    out_tok = usage.get("output_tokens", 0)
                    # Streaming dedup: only count the final chunk per message id
                    if msg_id:
                        if msg_id in seen_msg_ids and out_tok <= seen_msg_ids[msg_id]:
                            continue
                        seen_msg_ids[msg_id] = out_tok
                    total_output += out_tok
                    sr = msg.get("stop_reason")
                    if sr:
                        last_stop_reason = sr

                elif etype == "user" and "message" in entry:
                    # Tool results arrive as user messages with content blocks
                    content = entry["message"].get("content", [])
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "tool_result":
                                n_tool_calls += 1
                                if block.get("is_error"):
                                    n_tool_errors += 1

        if last_stop_reason == "max_tokens":
            issues.append("max_tokens_truncation")
        if total_output >= NEAR_CAP:
            issues.append("output_at_cap")
        # Flag if more than half of tool calls errored
        if n_tool_calls >= 4 and n_tool_errors / n_tool_calls > 0.5:
            issues.append("high_tool_error_rate")
    except OSError:
        return ["transcript_unreadable"], 0, 0, 0

    return issues, total_output, n_tool_calls, n_tool_errors


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, OSError):
        sys.exit(0)

    # Loop-prevention guard
    if event.get("stop_hook_active"):
        sys.exit(0)

    session_id = event.get("session_id", "")
    if not session_id:
        sys.exit(0)

    # Defensive field reads for the same version-drift reason as the start hook
    agent_type = (
        event.get("agent_type")
        or event.get("subagent_type")
        or event.get("subagent_name")
        or ""
    )
    agent_id = event.get("agent_id") or event.get("subagent_id") or ""

    last_msg = event.get("last_assistant_message")
    issues = []

    if last_msg is None:
        issues.append("no_assistant_message")
    elif len(last_msg) == 0:
        issues.append("empty_output")
    elif len(last_msg) < 100:
        issues.append("tiny_output")

    transcript_issues, total_output, n_tool_calls, n_tool_errors = inspect_transcript(
        event.get("agent_transcript_path", "")
    )
    issues.extend(transcript_issues)

    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "event": "stop",
        "session_id": session_id,
        "agent_id": agent_id,
        "agent_type": agent_type,
        "last_message_chars": len(last_msg) if last_msg else 0,
        "last_message_preview": (last_msg or "")[:120],
        "total_output_tokens": total_output,
        "n_tool_calls": n_tool_calls,
        "n_tool_errors": n_tool_errors,
        "issues": issues,
        "agent_transcript_path": event.get("agent_transcript_path"),
    }

    try:
        with open(LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
