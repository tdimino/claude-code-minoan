# geniza

A slim, verified archive of every Claude Code session, kept forever, so that `~/.claude/projects` need hold only the
last 90 days. geniza only reads `~/.claude/projects`, except `retire --apply`: that moves sessions older than 90
days, each with a verified slim copy, into `trash/`.

It is optional. `claude-tracker-suite` works without it; with it, search keeps finding a retired session and prints
`geniza read <id>` where it would print a resume command (`lib/tracker-db.js` `archivedSessionIds`).

## Install

```bash
mkdir -p ~/.claude/scripts && cp -R scripts/geniza ~/.claude/scripts/
cp bin/geniza ~/.local/bin/ && chmod +x ~/.local/bin/geniza        # expects Homebrew python@3.14 (zstd is in its stdlib)
# the hourly job: put your own home folder in the plist's four paths first
cp scripts/geniza/com.claude.geniza.plist ~/Library/LaunchAgents/ && launchctl load ~/Library/LaunchAgents/com.claude.geniza.plist
```

Then the two hooks under Automation below, and `cleanupPeriodDays: 99999` in Claude Code's settings so its own sweep
never deletes a transcript geniza has not copied. Run `geniza sweep --dry-run` before the first real sweep.

| File | Role |
|------|------|
| `geniza.py` | The tool: `sweep`, `capture`, `hourly`, `verify`, `check`, `read`, `retire`, `untrash`, `purge-trash`, `stats`, `reindex` (stdlib only, Python 3.14) |
| `com.claude.geniza.plist` | The hourly launchd job (`hourly` at minute 17); installed copy in `~/Library/LaunchAgents/` |
| `tests/test_geniza.py` | 35 tests on synthetic sessions in a temp dir; never touch `~/.claude` |
| `tests/mutants.py` | 44 mutants, one behavior broken each; the suite must fail on every one |

## Run

`~/.local/bin/geniza` runs it with the fixed Homebrew interpreter (`/opt/homebrew/opt/python@3.14/bin/python3.14 -I`),
from any folder.

```bash
geniza sweep --dry-run      # what would be archived; writes nothing
geniza sweep                # archive every new or changed session quiet for 10 min
geniza check                # every problem, or "all checks pass" (walks projects/, about 1 s)
geniza check --brief        # SessionStart: one line when something is wrong (pins, sweep age, last hourly check)
geniza read 999c2dc8        # a session as Markdown (--thinking, --subagents); works after it is retired
geniza verify --sample 20   # re-read the 20 least recently verified slim files
geniza retire [--list]      # dry run: sessions past 90 days, eligible or blocked, and why
geniza retire --apply       # move the eligible ones into trash/<day>/<project>/ (read the dry run first)
geniza untrash 2026-11-21   # bring a day's retired sessions back; refuses to overwrite
geniza purge-trash          # delete trash folders at least 14 days old; by hand only
uv run --no-project --python 3.14 python -I -m unittest discover -s ~/.claude/scripts/geniza/tests -v
uv run --no-project --python 3.14 python -I ~/.claude/scripts/geniza/tests/mutants.py <scratch dir>
```

Automation: `com.claude.geniza` runs `hourly` at minute 17 (sweep; once a day verify 20 copies and back up the
index; then store the check), logging to `~/Library/Logs/geniza/hourly.log`. `~/.claude/settings.json` runs
`geniza capture --stdin` at SessionEnd (detaches; logs to `capture.log`) and `geniza check --brief` at SessionStart.

Environment: `GENIZA_ROOT` (default `~/.local/share/geniza`), `GENIZA_PROJECTS` (`~/.claude/projects`),
`GENIZA_LOG_DIR` (`~/Library/Logs/geniza`), `GENIZA_NOW` (epoch seconds, for tests and dry runs),
`GENIZA_FREE_FLOOR_GB` (20).

## Layout

```
~/.local/share/geniza/
  index.sqlite                               slim (one row per generation), events, runs
  index.sqlite.bak                           the daily backup
  slim/<project-dir>/<session-id>.g<N>.jsonl.zst
  trash/<day>/<project-dir>/<session entries> retired originals, until purge-trash (14 days)
  geniza.lock                                fcntl lock, freed when its holder dies
~/Library/Logs/geniza/alerts.log, capture.log, hourly.log
```

## The slim form

A slim file is JSONL in zstd (level 10, with a content checksum):

- **Header:** `geniza-header`, holding the session's members (path, size, mtime, sha256 of each source file).
- **Body:** for each member, a `geniza-member` record and then that member's records, in the transcript's own shape:
  - images become `geniza-ref` (sha256, media type, bytes);
  - tool output and tool input strings keep their first 4 KB and last 1 KB, with the byte count noted;
  - thinking signatures and `toolUseResult` are dropped;
  - `file-history-snapshot`, `api-request*`, `attachment` and `queue-operation` records are dropped and counted;
  - a member that is not JSONL (`tool-results/*.txt` and the like, up to 64 MiB) keeps its first 4 KB and last 1 KB if
    it is UTF-8, otherwise only its hash, and is read in 1 MiB chunks, never whole;
  - a lone surrogate (half a character, left where Claude Code cut a string by UTF-16 unit) stays the `\udXXX`
    escape it was in the source, so the file is strict UTF-8; `read` shows it as `�`.
- **Permissions:** everything geniza makes, archive and logs alike, is `0700`/`0600`.
- **Footer:** `geniza-end`, giving the record count and the dropped counts.

Because the records keep their shape, the tracker's extractor can read them.

- **What counts as a session:** any UUID seen as `<uuid>.jsonl`, a `<uuid>/` folder, or a `<uuid>.*` sibling.
  `memory/`, `memory.bak-*` and `sessions-index.json` are left alone.
- **Verified:** read back at write (every line parses, the footer's count holds), or a later `verify`.
- **Generations:** growth (every old member a byte-prefix of its new version) replaces the slim file. Any other change
  (a member vanished, shrank or changed in place) writes `g<N+1>`, keeps `g<N>`, and writes an `alerts.log` line.

## Recovery

- **Lost or corrupt `index.sqlite`:** `geniza reindex` rebuilds it from the slim files' headers and footers. Each
  row's `verified_at` falls back to its capture time, so the next `verify --sample` takes the rebuilt rows first; the
  `events` and `runs` history is not in the slim files and starts again.
- **Reading a slim file by hand:** `zstdcat <file> | head`. No `--long` flag is needed, since slim files use the
  default window.
