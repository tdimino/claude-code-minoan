"""
Claude Code invocation handler.

Two modes:
  1. process()       — subprocess `claude -p` (legacy, used by bot.py)
  2. async_process() — Claude Agent SDK `query()` (used by claudius.py)

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
    # Remove all Claude Code session vars so claude -p doesn't detect a nested session
    for key in list(env):
        if key.startswith("CLAUDE_CODE_") or key == "CLAUDECODE":
            env.pop(key)

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

    # Parse JSON output (Claude CLI returns JSON even on error)
    try:
        data = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        if result.returncode != 0:
            stderr = result.stderr.strip()
            log.error("Claude failed (rc=%d) stderr: %s", result.returncode, stderr[:500])
            return f"Error running Claude (exit {result.returncode}): {stderr[:200] or 'unknown error'}"
        log.error("Failed to parse Claude output: %s", result.stdout[:200])
        return result.stdout.strip()[:MAX_RESPONSE_LENGTH] or "No response from Claude."

    # Handle structured errors (e.g. credit balance, auth failures)
    if data.get("is_error"):
        error_msg = data.get("result", "Unknown error")
        log.error("Claude returned error: %s", error_msg)
        return f"Claude error: {error_msg}"

    if result.returncode != 0:
        log.error("Claude failed (rc=%d): %s", result.returncode, data.get("result", "")[:500])
        return f"Error running Claude (exit {result.returncode}). Check daemon logs."

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


# ------------------------------------------------------------------
# SDK-based async handler (used by unified launcher)
# ------------------------------------------------------------------

async def async_process(
    text: str,
    channel: str,
    thread_ts: str,
    user_id: Optional[str] = None,
    soul_enabled: bool = True,
    allowed_tools: Optional[str] = None,
) -> str:
    """
    Process via Claude Agent SDK query() instead of subprocess.

    Uses resume= for session continuity. Soul engine wrapping is optional.
    """
    from claude_agent_sdk import (
        query,
        ClaudeAgentOptions,
        AssistantMessage,
        ResultMessage,
        TextBlock,
    )

    session_id = session_store.get(channel, thread_ts)
    tools = allowed_tools or CLAUDE_ALLOWED_TOOLS

    # Build the prompt
    use_soul = soul_enabled and SOUL_ENGINE_ENABLED and user_id
    if use_soul:
        prompt = soul_engine.build_prompt(
            text, user_id=user_id, channel=channel, thread_ts=thread_ts
        )
        soul_engine.store_user_message(text, user_id, channel, thread_ts)
    else:
        prompt = text

    log.info(
        "SDK query: channel=%s thread=%s resume=%s len=%d soul=%s",
        channel, thread_ts, session_id or "new", len(prompt),
        "on" if use_soul else "off",
    )

    # Override env vars that trigger nested-session detection.
    # SDK merges: {**os.environ, **options.env}, so we blank them out.
    env_overrides = {
        "CLAUDECODE": "",
        "CLAUDE_CODE_SSE_PORT": "",
        "CLAUDE_CODE_ENTRYPOINT": "",
        "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "",
        "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:" + os.environ.get("PATH", ""),
    }

    options = ClaudeAgentOptions(
        allowed_tools=tools.split(","),
        cwd=str(CLAUDE_CWD),
        permission_mode="bypassPermissions",
        env=env_overrides,
    )
    if session_id:
        options.resume = session_id

    full_response = ""
    new_session_id = None

    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        full_response += block.text
            elif isinstance(message, ResultMessage):
                new_session_id = message.session_id
                if message.is_error:
                    log.error("SDK query error: %s", message.result)
                    return f"Claude error: {message.result}"
                if message.result and not full_response:
                    full_response = message.result
    except Exception as e:
        log.error("SDK query failed: %s", e)
        return f"Error invoking Claude: {e}"

    # Persist session
    if new_session_id:
        session_store.save(channel, thread_ts, new_session_id)
    elif session_id:
        session_store.touch(channel, thread_ts)

    if not full_response:
        return "Claude returned an empty response."

    # Parse through soul engine or return raw
    if use_soul:
        response = soul_engine.parse_response(
            full_response, user_id=user_id, channel=channel, thread_ts=thread_ts
        )
    else:
        response = full_response

    if len(response) > MAX_RESPONSE_LENGTH:
        response = response[:MAX_RESPONSE_LENGTH] + "\n\n_(truncated)_"

    return response
