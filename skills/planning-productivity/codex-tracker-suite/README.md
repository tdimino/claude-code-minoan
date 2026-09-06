# Codex Tracker Suite

A thin, read-only wrapper around Codex's native App Server session APIs. It makes local Codex history searchable from Claude Code, Codex, shell scripts, and other automation without maintaining a second transcript database.

## What it provides

| Command | Purpose | Native API |
|---|---|---|
| `search QUERY` | Search visible transcript text and return matching sessions with snippets | `thread/search` |
| `occurrences ID QUERY` | Find chronological matches inside one session | `thread/searchOccurrences` |
| `recent` | List recent sessions and metadata | `thread/list` |
| `show ID` | Read a session without resuming it | `thread/read` |
| `alive` | List sessions loaded in a shared managed daemon | `thread/loaded/list` |
| `resume ID` | Print a shell-safe native resume command | `thread/read` + `codex resume` |

The wrapper does not read Codex's private SQLite schemas or rollout files directly. Codex remains the source of truth.

## Requirements

- Python 3.10 or newer; only the standard library is used.
- Codex CLI on `PATH`.
- A Codex build whose generated App Server schema exposes the requested methods. Full-text search is experimental and was tested with Codex CLI `0.153.4`.

The official [Codex App Server documentation](https://learn.chatgpt.com/docs/app-server) describes the JSONL transport, initialization handshake, stable thread APIs, experimental opt-in, and version-matched schema generation.

## Installation

Install for Claude Code:

```bash
cp -R skills/planning-productivity/codex-tracker-suite ~/.claude/skills/
```

Expose the same installation to Codex:

```bash
mkdir -p ~/.codex/skills
ln -s ~/.claude/skills/codex-tracker-suite ~/.codex/skills/codex-tracker-suite
```

Optionally add the convenient shell command:

```bash
ln -s ~/.claude/skills/codex-tracker-suite/scripts/codex_tracker.py ~/.local/bin/codex-tracker
```

The repository's normal setup also installs the `bin/codex-tracker` launcher, which resolves either the Claude or Codex skill location.

## Usage

Search interactive CLI and IDE sessions:

```bash
codex-tracker search "permission profile"
```

Include `codex exec` and App Server sessions:

```bash
codex-tracker search "migration failure" --include-non-interactive
```

Include subagents and unknown source types:

```bash
codex-tracker search "schema mismatch" --all-sources
```

Return machine-readable output:

```bash
codex-tracker recent --limit 10 --json
codex-tracker occurrences <session-id> "search phrase" --json
```

Inspect a session without resuming it:

```bash
codex-tracker show <session-id>
codex-tracker show <session-id> --metadata-only
```

Generate a command that resumes in the saved working directory:

```bash
codex-tracker resume <session-id>
```

Every subcommand has its own help:

```bash
codex-tracker search --help
```

## How it works

The client connects to the managed App Server daemon through `codex app-server proxy` when the daemon socket is present. Otherwise, it starts a short-lived `codex app-server --stdio` process, performs the required `initialize`/`initialized` handshake, runs the request, and closes the process.

Search and occurrence matching use experimental native methods. Recent-session listing and session reads use stable methods. The wrapper asks Codex for version-matched data instead of copying an App Server schema into the repository.

## Operational notes

- Full-text search may take tens of seconds on a large history. Progress is written to stderr; increase the request limit with `--timeout 300` or `CODEX_TRACKER_TIMEOUT=300`.
- `alive` requires the shared managed daemon. A short-lived process cannot observe threads loaded by other Codex processes, so the command fails clearly instead of returning a misleading empty list.
- App Server can repair or refresh its own metadata during otherwise read-only operations. A restricted Codex sandbox may therefore request permission to write under `~/.codex`.
- Session output can contain private prompt and response text. Treat JSON output and logs accordingly.
- The wrapper intentionally has no archive, delete, or rename commands.
- If experimental full-text search is unavailable, upgrade Codex or use `codex resume --all` and type the query in the native picker.

## Validation

Run the deterministic regression tests:

```bash
python3 skills/planning-productivity/codex-tracker-suite/scripts/test_codex_tracker.py
```

Validate Python syntax:

```bash
python3 -m py_compile skills/planning-productivity/codex-tracker-suite/scripts/codex_tracker.py
```

The skill also includes `evals/evals.json` with realistic agent-facing trigger and behavior cases.

## Design boundary

This is deliberately smaller than `claude-tracker-suite`. It does not implement tags, checkpoints, summaries, cost reconstruction, synonym expansion, terminal orchestration, or a duplicate full-text index. See [`references/architecture.md`](references/architecture.md) for compatibility and extension guidance.
