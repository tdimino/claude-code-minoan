"""
Claude Code invocation handler.

Routes Slack messages to `claude -p` subprocess with session continuity.
Thread-level sessions are stored in SQLite so multi-turn conversations
resume the same Claude context.

When the soul engine is enabled, prompts are wrapped with cognitive
instructions and responses are parsed for structured output.
"""

import json
import logging
import os
import subprocess
from typing import Optional

import session_store
import soul_engine
import working_memory
from config import (
    CLAUDE_ALLOWED_TOOLS,
    CLAUDE_CWD,
    CLAUDE_TIMEOUT,
    MAX_RESPONSE_LENGTH,
    SOUL_ENGINE_ENABLED,
)

log = logging.getLogger("slack-daemon.handler")


def process(
    text: str,
    channel: str,
    thread_ts: str,
    user_id: Optional[str] = None,
) -> str:
    """
    Send text to Claude Code and return the response.

    Resumes a prior session if one exists for this thread.
    Saves the new session ID for future turns.
    When soul engine is enabled, wraps prompt with cognitive steps
    and parses structured output.
    """
    session_id = session_store.get(channel, thread_ts)

    # Build the prompt
    if SOUL_ENGINE_ENABLED and user_id:
        prompt = soul_engine.build_prompt(
            text, user_id=user_id, channel=channel, thread_ts=thread_ts
        )
        soul_engine.store_user_message(text, user_id, channel, thread_ts)
    else:
        prompt = text

    cmd = [
        "claude",
        "-p", prompt,
        "--output-format", "json",
        "--allowedTools", CLAUDE_ALLOWED_TOOLS,
    ]
    if session_id:
        cmd.extend(["--resume", session_id])

    log.info(
        "Invoking claude: channel=%s thread=%s resume=%s len=%d soul=%s",
        channel, thread_ts, session_id or "new", len(prompt),
        "on" if SOUL_ENGINE_ENABLED else "off",
    )

    # Build env with guaranteed PATH for launchd contexts
    env = os.environ.copy()
    env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:" + env.get("PATH", "")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT,
            cwd=CLAUDE_CWD,
            env=env,
        )
    except subprocess.TimeoutExpired:
        log.warning("Claude timed out after %ds", CLAUDE_TIMEOUT)
        return f"Timed out after {CLAUDE_TIMEOUT}s. Try a simpler question or break it into steps."

    if result.returncode != 0:
        stderr = result.stderr.strip()
        log.error("Claude failed (rc=%d): %s", result.returncode, stderr[:200])
        return f"Error running Claude (exit {result.returncode}). Check daemon logs for details."

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        log.error("Failed to parse Claude output: %s", result.stdout[:200])
        return result.stdout.strip()[:MAX_RESPONSE_LENGTH] or "No response from Claude."

    # Persist session for thread continuity (only on success)
    new_session_id = data.get("session_id")
    if new_session_id:
        session_store.save(channel, thread_ts, new_session_id)
    elif session_id and result.returncode == 0:
        session_store.touch(channel, thread_ts)

    raw_response = data.get("result", "")
    if not raw_response:
        return "Claude returned an empty response."

    # Parse through soul engine or return raw
    if SOUL_ENGINE_ENABLED and user_id:
        response = soul_engine.parse_response(
            raw_response, user_id=user_id, channel=channel, thread_ts=thread_ts
        )
    else:
        response = raw_response

    if len(response) > MAX_RESPONSE_LENGTH:
        response = response[:MAX_RESPONSE_LENGTH] + "\n\n_(truncated)_"

    return response
