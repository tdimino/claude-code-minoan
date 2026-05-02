#!/usr/bin/env python3
"""
Direct OpenAI API chat completions — bypasses Codex CLI for API-billed models.

Supports one-shot queries, multi-turn sessions, streaming, system prompts,
and reasoning effort. Conversation state persisted to JSON session files.

Env: OPENAI_API_KEY
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai library not installed. Run: pip install openai", file=sys.stderr)
    sys.exit(1)

DEFAULT_MODEL = "gpt-5.4"
KNOWN_MODELS = {
    "gpt-5.5", "gpt-5.5-pro", "gpt-5.4", "gpt-5-mini",
    "o3", "o4-mini", "o3-mini",
    "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano",
    "gpt-4o", "gpt-4o-mini", "gpt-4-turbo",
}


def load_session(path: Path) -> list[dict]:
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            print(f"Warning: corrupt session file {path}, starting fresh", file=sys.stderr)
    return []


def save_session(path: Path, messages: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(messages, f, indent=2)


def chat(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system: str | None = None,
    session_path: Path | None = None,
    stream: bool = False,
    reasoning: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    output_json: bool = False,
) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    messages = []
    if session_path:
        messages = load_session(session_path)

    if system and not any(m["role"] == "system" for m in messages):
        messages.insert(0, {"role": "system", "content": system})

    messages.append({"role": "user", "content": prompt})

    kwargs: dict = {"model": model, "messages": messages}

    if stream:
        kwargs["stream"] = True
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_tokens:
        kwargs["max_completion_tokens"] = max_tokens

    is_reasoning = model.startswith("o")
    if reasoning and not is_reasoning:
        kwargs["temperature"] = 1.0 if temperature is None else temperature

    if reasoning:
        effort_map = {"low": "low", "medium": "medium", "high": "high"}
        if reasoning in effort_map:
            kwargs["reasoning"] = {"effort": effort_map[reasoning]}

    t0 = time.time()

    if stream:
        response_text = _stream_response(client, kwargs)
    else:
        response = client.chat.completions.create(**kwargs)
        response_text = response.choices[0].message.content or ""
        print(response_text)

    elapsed = time.time() - t0

    messages.append({"role": "assistant", "content": response_text})

    if session_path:
        save_session(session_path, messages)

    if output_json:
        meta = {
            "model": model,
            "elapsed_seconds": round(elapsed, 2),
            "session_turns": len([m for m in messages if m["role"] == "user"]),
        }
        if not stream and hasattr(response, "usage") and response.usage:
            meta["usage"] = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        if session_path:
            meta["session_file"] = str(session_path)
        print(json.dumps(meta, indent=2), file=sys.stderr)

    return response_text


def _stream_response(client: OpenAI, kwargs: dict) -> str:
    chunks = []
    stream = client.chat.completions.create(**kwargs)
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            chunks.append(text)
            print(text, end="", flush=True)
    print()
    return "".join(chunks)


def main():
    parser = argparse.ArgumentParser(
        description="OpenAI API chat completions (direct billing, not Codex subscription)"
    )
    parser.add_argument("prompt", help="User message")
    parser.add_argument(
        "--model", "-m", default=DEFAULT_MODEL,
        help=f"Model name (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--system", "-s", default=None,
        help="System prompt (injected once at conversation start)"
    )
    parser.add_argument(
        "--session", default=None, type=Path,
        help="Path to JSON session file for multi-turn conversation"
    )
    parser.add_argument(
        "--stream", action="store_true",
        help="Stream tokens as they arrive"
    )
    parser.add_argument(
        "--reasoning", choices=["minimal", "low", "medium", "high", "xhigh"], default=None,
        help="Reasoning effort (API supports low/medium/high; minimal/xhigh silently ignored)"
    )
    parser.add_argument(
        "--temperature", "-t", type=float, default=None,
        help="Sampling temperature (0.0-2.0)"
    )
    parser.add_argument(
        "--max-tokens", type=int, default=None,
        help="Maximum completion tokens"
    )
    parser.add_argument(
        "--json", dest="output_json", action="store_true",
        help="Output usage metadata as JSON to stderr"
    )

    args = parser.parse_args()

    if args.model not in KNOWN_MODELS:
        print(f"Warning: '{args.model}' not in known models, proceeding anyway", file=sys.stderr)

    chat(
        prompt=args.prompt,
        model=args.model,
        system=args.system,
        session_path=args.session,
        stream=args.stream,
        reasoning=args.reasoning,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        output_json=args.output_json,
    )


if __name__ == "__main__":
    main()
