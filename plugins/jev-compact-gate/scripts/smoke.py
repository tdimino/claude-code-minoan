#!/usr/bin/env python3
"""Live Jev smoke test: does at_boundary separate a finished seam from mid-debug work?

Usage: uv run scripts/smoke.py   (needs OPENROUTER_API_KEY)
"""

import json
import os
import sys
import time
import urllib.request

URL = "https://openrouter.ai/api/v1/systemone"
MODEL = "typesafe/jev-1.13"

QUESTIONS = {
    "at_boundary": {
        "type": "noul",
        "instructions": "Has a unit of work just closed in this coding-agent session?",
        "criteria": {
            "true": "The last turn completed a deliverable—a commit, passing tests, a finished answer or report, or an approved plan—and the next request is likely to start new work.",
            "false": "Work is mid-flight: a bug is still being chased, an edit series is incomplete, tests are failing, or the assistant just asked a question whose answer depends on recent detail.",
        },
    },
    "needs_verbatim_recent": {
        "type": "noul",
        "instructions": "Would the agent's next step need exact text from recent tool output that a summary would likely lose?",
        "criteria": {
            "true": "The next step depends on exact error messages, file contents, diffs, stack traces, or command output from the last few tool calls.",
            "false": "The next step can proceed from a summary of what was done; exact recent tool output is no longer needed.",
        },
    },
    "phase": {
        "type": "choice",
        "instructions": "Which phase is the session in right now?",
        "criteria": {
            "exploring": "Reading code or docs to understand a problem.",
            "implementing": "Writing or editing code toward a known design.",
            "debugging": "Chasing a failure whose cause is not yet known.",
            "verifying": "Running tests or checks on finished work.",
            "wrapping_up": "Committing, documenting, or summarizing finished work.",
            "conversing": "Discussing ideas with the user; no active code work.",
        },
    },
}

STATES = {
    "seam (just committed)": {
        "recent_prompts": [
            "Add retry with exponential backoff to the fetch client in src/net.rs",
            "Tests pass? then commit it",
        ],
        "last_answer": "All 42 tests pass. Committed as a3f9c1e \"net: retry with exponential backoff (max 5, jittered)\". The retry logic lives in src/net.rs:88-131 and is covered by tests/net_retry.rs. Anything else?",
        "recent_activity": [
            "Edit file_path=src/net.rs → ok",
            "Write file_path=tests/net_retry.rs → ok",
            'Bash cmd="cargo test" → ok: 42 passed',
            'Bash cmd="git add -A && git commit -m ..." → ok: a3f9c1e',
        ],
    },
    "mid-debug": {
        "recent_prompts": [
            "The save loader panics on old saves, find out why",
            "still panicking, keep going",
        ],
        "last_answer": "The panic moved: it now fails at src/save/load.rs:214 with `index out of bounds: the len is 12 but the index is 12`. That suggests the fleet table has an off-by-one when the version byte is 3. Let me check how read_fleets computes the count.",
        "recent_activity": [
            'Bash cmd="cargo run -- load old.sav" → error: thread main panicked at src/save/load.rs:198',
            "Edit file_path=src/save/load.rs → ok",
            'Bash cmd="cargo run -- load old.sav" → error: index out of bounds: the len is 12 but the index is 12 at src/save/load.rs:214',
            "Read file_path=src/save/fleets.rs → ok 3120ch",
        ],
    },
}


def ask(state: dict) -> tuple[dict, float]:
    body = json.dumps({"model": MODEL, "state": state, "questions": QUESTIONS}).encode()
    req = urllib.request.Request(
        URL,
        data=body,
        headers={
            "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
            "Content-Type": "application/json",
        },
    )
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    return data, (time.monotonic() - t0) * 1000


def main() -> int:
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("OPENROUTER_API_KEY missing", file=sys.stderr)
        return 1
    for name, state in STATES.items():
        data, ms = ask(state)
        a = data["answers"]
        pb = a["at_boundary"]["noul"]
        pv = a["needs_verbatim_recent"]["noul"]
        print(
            f"{name:24s} at_boundary={pb:.2f} needs_verbatim={pv:.2f} "
            f"score={pb * (1 - pv):.2f} phase={a['phase']['choice']} "
            f"({a['phase']['confidence']:.2f}) {ms:.0f}ms "
            f"in={data['usage']['input_tokens']} ${data['usage']['cost']:.6f}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
