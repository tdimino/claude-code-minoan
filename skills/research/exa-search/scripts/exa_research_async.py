#!/usr/bin/env python3
"""Retired: Exa shut down the Research API (/research/v0 and /research/v1 return 410).
Use exa_agent.py, which runs the same kind of async multi-step research."""

import shlex
import sys

AGENT = "python3 ~/.claude/skills/exa-search/scripts/exa_agent.py"
VALUE_FLAGS = {"--model", "--schema", "--output-schema", "--schema-file", "--timeout", "--poll-interval",
               "--limit", "-n", "--num", "--instructions"}


def main():
    args = sys.argv[1:]
    print("exa_research_async.py is retired: Exa's Research API returns 410 RESEARCH_RETIRED.", file=sys.stderr)
    if args and args[0] in ("status", "get", "list", "poll"):
        print(f"Old research job IDs do not carry over. Agent runs: {AGENT} list | {AGENT} status RUN_ID",
              file=sys.stderr)
        sys.exit(2)
    positionals, skip = [], False
    for a in args:
        if skip:
            skip = False
        elif a in VALUE_FLAGS:
            skip = True
        elif not a.startswith("-") and a != "create":
            positionals.append(a)
    query = shlex.quote(positionals[0]) if positionals else '"your question"'
    effort = "high" if "--pro" in args else "medium"
    print(f"Use: {AGENT} run {query} --effort {effort}", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
