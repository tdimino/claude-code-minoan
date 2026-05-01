#!/usr/bin/env python3
"""
Stream messages to Slack using chat.startStream/appendStream/stopStream.

Usage:
    slack_stream.py "#channel" "Hello streaming world"
    slack_stream.py "#channel" "Long message" --chunk-size 50
    slack_stream.py "#channel" --stdin                   # stream stdin
    slack_stream.py "#channel" "reply" --thread 1234.5678

Requires: SLACK_BOT_TOKEN environment variable
Requires: chat:write scope
"""

import argparse
import sys
import time

sys.path.insert(0, __import__("os").path.dirname(__file__))
from _slack_utils import slack_api, resolve_channel, SlackError


def start_stream(channel_id: str, thread_ts: str = None) -> dict:
    """Start a streaming message. Returns response with stream_id."""
    params = {"channel": channel_id}
    if thread_ts:
        params["thread_ts"] = thread_ts
    return slack_api("chat.startStream", **params)


def append_stream(stream_id: str, text: str) -> dict:
    """Append markdown text to an active stream."""
    return slack_api("chat.appendStream", stream_id=stream_id, text=text)


def stop_stream(stream_id: str) -> dict:
    """Finalize a streaming message."""
    return slack_api("chat.stopStream", stream_id=stream_id)


class SlackStream:
    """Context manager for streaming messages.

    Usage:
        with SlackStream(channel_id, thread_ts) as stream:
            stream.append("Processing...")
            stream.append(" Done!")
            print(f"Message ts: {stream.ts}")
    """
    def __init__(self, channel_id: str, thread_ts: str = None,
                 chunk_delay: float = 0.05):
        self.channel_id = channel_id
        self.thread_ts = thread_ts
        self.chunk_delay = chunk_delay
        self._stream_id = None
        self._ts = None

    def __enter__(self):
        result = start_stream(self.channel_id, self.thread_ts)
        self._stream_id = result.get("stream_id")
        self._ts = result.get("ts")
        return self

    def append(self, text: str):
        if self._stream_id:
            append_stream(self._stream_id, text)
            if self.chunk_delay > 0:
                time.sleep(self.chunk_delay)

    def __exit__(self, *args):
        if self._stream_id:
            stop_stream(self._stream_id)

    @property
    def ts(self):
        return self._ts

    @property
    def stream_id(self):
        return self._stream_id


def main():
    parser = argparse.ArgumentParser(description="Stream messages to Slack")
    parser.add_argument("channel", help="Channel (#name or ID)")
    parser.add_argument("text", nargs="?", help="Message text to stream")
    parser.add_argument("--thread", help="Thread timestamp for replies")
    parser.add_argument("--chunk-size", type=int, default=80,
                        help="Characters per chunk (default: 80)")
    parser.add_argument("--delay", type=float, default=0.05,
                        help="Delay between chunks in seconds (default: 0.05)")
    parser.add_argument("--stdin", action="store_true",
                        help="Stream stdin line by line")
    args = parser.parse_args()

    if not args.text and not args.stdin:
        parser.error("Provide text or use --stdin")

    try:
        channel_id = resolve_channel(args.channel)

        with SlackStream(channel_id, args.thread, args.delay) as stream:
            if not stream.stream_id:
                print("Error: Failed to start stream (missing scope or API unavailable)",
                      file=sys.stderr)
                sys.exit(1)

            if args.stdin:
                for line in sys.stdin:
                    stream.append(line)
            else:
                text = args.text
                for i in range(0, len(text), args.chunk_size):
                    chunk = text[i:i + args.chunk_size]
                    stream.append(chunk)

        print(f"Streamed to {args.channel} (ts: {stream.ts})")

    except SlackError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
