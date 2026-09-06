# Architecture and compatibility

## Source of truth

The wrapper uses Codex App Server over its newline-delimited JSON stdio transport. It connects through `codex app-server proxy` when the managed daemon socket exists; otherwise it starts a short-lived `codex app-server --stdio` child.

It never queries these implementation details directly:

- `~/.codex/state_*.sqlite`
- `~/.codex/thread_history_*.sqlite`
- rollout JSONL files
- `session_index.jsonl`

Those files and schemas are not the public integration contract.

## API selection

Stable operations:

- `thread/list` for recent sessions and metadata
- `thread/read` for one stored thread without resuming it
- `thread/loaded/list` for runtime-loaded thread IDs when connected to the shared managed daemon

Experimental operations, enabled through `capabilities.experimentalApi`:

- `thread/search` for transcript full-text results and snippets
- `thread/searchOccurrences` for literal, case-insensitive matches in visible user messages and final assistant messages

The installed CLI can generate its exact protocol schema with:

```bash
codex app-server generate-json-schema --experimental --out /tmp/codex-app-server-schema
```

Do not vendor that generated schema into the skill. Compatibility should be detected from an App Server error so the wrapper stays version-matched.

## Scope

This is intentionally thinner than `claude-tracker-suite`. Codex already owns session persistence, titles, previews, archive state, transcript rendering, and resumption. The wrapper makes those native features scriptable.

Not included in the first version:

- a second transcript index
- synonym expansion or semantic search
- custom tags, checkpoints, or phase analytics
- cost reconstruction
- session mutation or deletion
- terminal/tab orchestration

Add a secondary index only after native search latency has been benchmarked on representative histories and a concrete workflow cannot tolerate it. Any cache must remain disposable and rebuildable from App Server responses.

## Acceptance checks

- A term present only in a user message finds the thread.
- A term present only in a final assistant message finds the thread.
- `occurrences` returns chronological snippets and turn/item identifiers.
- `recent --json` produces parseable JSON without ANSI codes.
- `show` does not resume or load the thread.
- `alive` uses native loaded-thread state.
- `alive` fails clearly rather than reporting a false empty set when only a short-lived direct App Server is available.
- Resume commands safely quote working directories and IDs.
- Unsupported experimental methods fail clearly without touching private stores.
