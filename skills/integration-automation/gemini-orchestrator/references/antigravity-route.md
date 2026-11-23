# The Antigravity route

How a run through `agy` (Antigravity CLI 1.5.14) is confined, what was measured on 2026-11-22, and what is still untested. The code is `scripts/agy_client.py` and the agy half of `scripts/gemini_exec.py`.

## The command

```
agy --print <prompt> --model <slug> --sandbox --disable-slash-commands
    --output-format stream-json --print-timeout <N>s
    --settings '<json>' --agent orch-<profile> [--mode accept-edits]
```

- `<slug>` joins model and effort: `gemini-4-neon-high`, `gemini-4-hydrogen-medium`, `gemini-3.8-flash-low`. `agy models` lists them. Argon has no `xhigh`.
- `--settings` applies to the one run and is never saved:
  `{"agentMode": "", "toolPermission": "proceed-in-sandbox", "enableTerminalSandbox": true, "useG1Credits": false, "permissions": {"deny": [...]}}`.
- `--dangerously-skip-permissions` is never passed.
- `--mode accept-edits` is passed for `builder` only.

## What confines the delegate

| Measure | What it stops | Shown live |
|---|---|---|
| Persona `tools` list (`view_file`, `run_command`; plus the three write tools for `builder`) | every other `agy` tool, among them `search_web`, `read_url_content` and the browser | yes: under a persona the model reported only `read_file`, `run_command`, `manage_task` and could not call `search_web` |
| Sandbox (`--sandbox`, `enableTerminalSandbox`) | network from the shell; shell writes outside the folder | yes: `curl` exit 6; `echo x > <outside>` "operation not permitted" |
| `read_file(<absolute path>)` deny rules | reading a withheld file, by the viewer and by the shell | yes: viewer "Matches user-configured deny rule"; `cat .env` "Operation not permitted" |
| `write_file(<folder>)` (read-only profiles) | every write in the folder | yes |
| `write_file(...)` on `.git`, withheld and untracked paths, submodules and control files (`builder`) | writes git could not restore, and files that steer an agent outside the sandbox | `.git` yes, by tool and by shell; the rest in tests only |

Without a persona none of the first row holds: `agy`'s stock agent ran `search_web` outside the sandbox, and `permissions.deny` entries `search_web` and `search_web(*)` did not stop it. That is why `default` is a persona too.

A deny rule must name an absolute path. A relative one breaks every shell command in the sandbox. A path that needs a rule and holds `()[]*?` or a control character stops the run (exit 2), since how `agy` reads such a rule is untested.

The sandbox alone, probed without rules: the shell could not read `~/.ssh/config`, a `secrets.env` outside the folder, `~/.zshrc` or another project, and could read `~/.gitconfig` and `/etc/hosts`. The rules on git's configs rest on that.

## Files `agy` loads by itself

No tool step loads these, so no deny rule is known to stop them and the audit never sees them. `prepare_agy` handles them before the run:

- **Agent folders.** `agy` reads agents from `~/.gemini/config/agents/` and from `.agents/agents/` in a repository. A folder `.agents/agents/orch-*` in the working folder or any folder above it stops the run (exit 2): it could be loaded in place of the persona checked and installed here, with any tool list. Which of the two `agy` prefers is untested.
- **Rules files.** `AGENTS.md` and `GEMINI.md` from the working folder upward, and `~/.gemini/GEMINI.md`, are scanned for denied addresses and secret patterns like the brief (exit 5 on a finding) and listed in the manifest under `rules_files`.

## The `builder` profile's limits

- The write rules cover: everything denied to reading, every path git does not track (ignored ones included, a wholly untracked folder as one rule), every submodule, and `.claude`, `.agents`, `.gemini`, `AGENTS.md`, `GEMINI.md`, `CLAUDE.md` and `.envrc` at the top of the folder, present or not.
- The rules name paths. A run that renamed a parent folder would carry a file out from under its rule, so the launcher hashes every withheld and untracked file before the run and compares after it; one missing or altered is listed under `disturbed` and the run exits 1. A folder is checked for presence only.
- After the run `git status --ignored` is read before the launcher writes anything. A new file under a folder that was already ignored is not listed (that folder is write-denied as a whole). A change to a control file at any depth is named and the run exits 1.
- The prompt tells `builder` it may write; the read-only profiles are told they cannot.

## What is withheld

`deny_rules()` walks the folder before every run (limits: 20,000 files, 50 MB a file) and writes one `read_file` rule per path:

- a credentials file by name (`.env`, `*.p12`, `id_rsa` and the like, without regard to case), judged by its own name and its link target's;
- a file holding a denied address or a secret pattern, read as UTF-8 and again with NUL bytes removed, so UTF-16 is caught;
- a file too large to scan, or one that cannot be read;
- `.git`, `.subdaimon-output` and `.beans` at any depth, linked folders, and a `.git` that is a file (a worktree's or a submodule's pointer);
- `~/.gitconfig`, git's XDG config, `GIT_CONFIG_GLOBAL` (unless it names a device such as `/dev/null`), every file those include with `include.path` or `includeIf`, and the repository's own git folders when the run starts in a subfolder or a worktree.

In the folders `context_pack.SKIP_DIRS` skips (`node_modules`, `.venv`, `venv`, `__pycache__`) a credentials file is withheld by name; nothing else there is scanned or denied.

`--allow <path>` exempts a file from the secret patterns, never from the addresses, in the scan before the run and in the audit after it.

The quote gives the number of denied addresses. With none the launcher warns, since then no file is withheld for holding one. Not seen by any scan: an address or key inside an archive, a compressed PDF stream, base64 or a file name.

## After the run

- **Outcome.** `SUCCESS` with text is ok (0). An empty answer with `denied_actions` or "auto-denied" on stderr is a permission stop (4). A result followed by a non-zero exit is an error (1). A served model other than the one asked is exit 6; a run whose `init` event names no model passes that check and shows `served=unreported` in the trailer.
- **Audit.** Every tool output and every file read is scanned again. A read that ended in state `ERROR` with an error and no output was refused and is listed under `refused`, not scanned. A step cut off while running is scanned. A read of a file with a credentials name is a finding whatever it holds. Findings give exit 5.
- **Files beside the output:** `<name>.stream.jsonl` (the raw events, written first) and `<name>.manifest.json` (files read with hashes, files cited, commands, refused reads, deny rules, rules files, and `changed` and `disturbed` for a write run).
- **Process.** `agy` runs in its own session and process group. The group is killed when the run ends, on Ctrl-C, and on SIGTERM or SIGHUP to the launcher; in each case the launcher still writes the output, the ledger and the change list, and exits 1. SIGKILL to the launcher leaves `agy` running to its own time limit. The launcher stops at the result event, after 5 minutes of silence, or 30 seconds past `agy`'s own limit.

## Measurements, 2026-11-22

| Run | Model | Time | Steps | Result | Quota reading |
|---|---|---|---|---|---|
| Review of this skill's agy code | Neon high | 633 s, first text at 575 s, longest gap 160 s | 36 | 12 findings, 26 of 26 citations | week 91% to 70%, five-hour 70% to 0% |
| The same brief on the fixed code | Hydrogen high | about 10 min | 51 | 5 findings, citations uncounted (backticks) | week 67% to 62% at once, 42% forty minutes later; five-hour 84% to 69%, then 1% |
| Deny-rule and tool probes | Flash low | 5 to 30 s each | 6 to 18 | as in the table above | too small to read against the lag |

The second row is why the review profiles stayed on Neon: once the reading caught up, Hydrogen at high had cost about as much as Neon at high. A quota refusal reads `ERROR: Individual quota reached ... Resets in 45m14s`, exits 1 and is logged in `failures.jsonl`.

## Untested

- The `builder` exit check on a real spec (refused for quota when first tried).
- Whether `--mode accept-edits` is needed: the write probe ran with it and `init` still reported `proceed-in-sandbox`.
- Which agent file `agy` loads when the repository and the home folder both hold one of the same name.
- Whether a `read_file` rule stops `agy` from loading an `AGENTS.md` or `GEMINI.md`.
- Whether a rule follows a file through a renamed parent folder or a hard link.
- How `agy` reads `()[]*?` or a line break inside a rule.
- Whether write rules bind for untracked, ignored and control paths, and for a path that does not exist yet.
- Whether the sandboxed shell can read or write `/tmp` and `$TMPDIR`.
- Whether the read tool's parameter is always `Path`; if not, `files_read` undercounts, though tool outputs are still scanned.
- Whether `init` always names the served model.
- Whether `denied_actions` can arrive beside a non-empty answer.
- Whether per-run deny rules replace or merge with a saved `permissions.allow`.
- Whether `agy` matches rule paths without regard to case on APFS.
- Whether Antigravity's telemetry is on: read **Enable Telemetry** under `/config` in the `agy` TUI.
- Quota use at medium effort, and for the same brief over a smaller folder.
