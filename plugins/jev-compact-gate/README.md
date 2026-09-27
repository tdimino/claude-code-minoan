# jev-compact-gate

A Claude Code plugin that picks *when* a session compacts. Inside a 280k–400k token band, TypeSafe's **Jev** judges each finished turn: has a unit of work just closed, and does the next step still need exact recent tool output? It compacts at a seam, holds while detail matters, and never lets the context pass 400k. Claude's own `/compact` summary does the compacting. Jev never rewrites the transcript.

**Last updated:** 2026-09-27

---

## Why This Plugin Exists

Native auto-compaction fires at a fixed fill percentage, blind to where the work stands, so it compacts mid-debug as readily as after a clean commit. Earlier Jev integrations such as `fast-jev-compaction` point Jev at *how* to compact: they prune tool calls line by line. That breaks the prompt cache, strips reasoning payloads, and lets the agent repeat failures it no longer remembers. This plugin points Jev at *when* instead. It asks one cheap question per turn and leaves the summary to Claude.

Jev is not an LLM. It is a System One decision model: it takes typed questions over a `state` object and returns calibrated probabilities, with no text. On OpenRouter it costs **$0.042 per million input tokens, with output free**. A gate call here sends about 700–900 input tokens, roughly **$0.00003**, and returns in 0.3–0.8s once the connection is warm.

---

## How It Works

```
turn.complete ─┬─ subagent / aborted / errored / in flight / cooldown → pass
               ├─ context window < ceiling (a 200k model)       → pass; native compaction governs
               ├─ tokens < 280k                                  → pass
               ├─ tokens ≥ 400k                                  → compact, no Jev call
               └─ 280k ≤ tokens < 400k → ask Jev → veto? threshold? → compact | hold
```

One request to `POST https://openrouter.ai/api/v1/systemone` carries three questions over a bounded, redacted state. The state holds the last three typed prompts, the final answer, and the last 15 tool calls as one-liners. Token counts stay in code, where the band is decided, because they tell Jev nothing about whether work just closed.

| Question | Type | Judges |
|---|---|---|
| `at_boundary` | Noul | A deliverable just closed (commit, green tests, finished answer, approved plan) and the next request is likely new work |
| `needs_verbatim_recent` | Noul | The next step depends on exact recent error text, file contents, diffs, or command output |
| `phase` | Choice | exploring · implementing · debugging · verifying · wrapping_up · conversing |

The policy lives in code, per TypeSafe's guidance: separate conditions for hard violations, and weighted thresholds for preferences.

- **Veto.** `P(needs_verbatim_recent) ≥ 0.5` holds, whatever the boundary says.
- **Threshold.** Compact when `P(at_boundary) ≥ T`. `T` falls linearly from **0.70** at 280k to **0.30** at 400k, and rises by `0.15 × P(debugging)`, using Jev's own phase distribution rather than its top pick.
- **Faults hold.** A timeout, HTTP error, missing key, or malformed answer holds, and the reason is logged. The 400k ceiling never depends on Jev, so a dead Jev degrades to "compact at 400k."
- **Cooldown.** After a compaction, the gate waits three main-loop turns before it can act again. Native and manual compactions reset its count too.

Compaction runs as `$.session.compact({ instructions })`, which is the same path as `/compact <instructions>`. The instructions name the latest prompt and the phase, because Jev writes no text.

---

## Install

Requires Claude Code **2.1.274+** (function hooks are early access) and an OpenRouter key.

**What leaves the machine.** Each gate call sends OpenRouter (and TypeSafe behind it) your last three prompts, up to 600 characters each, the last answer, up to 1,500 characters, and the key argument of the last 15 tool calls: a bash command, file path, URL, or search query, up to 120 characters each. Tool output is never sent. Before sending, `redact()` in `src/decide.ts` masks credential-shaped text:

- named secret assignments (`*_KEY=`, `*TOKEN=`, `--password=`, `"api_key": "…"`)
- `Bearer` headers
- `sk-…`, `ghp_…` and `AKIA…` key shapes

Redaction is pattern-based and biased toward over-redacting. It is not a guarantee, so don't install this where prompts must not reach a third party. Shadow mode sends the same state as live mode.

```sh
# 1. Enable function hooks wherever Claude Code runs (~/.claude/settings.json)
#    { "env": { "CLAUDE_CODE_ENABLE_FUNCTION_HOOKS": "1" } }

# 2. Key in the shell environment, never in settings or the repo
export OPENROUTER_API_KEY=sk-or-...

# 3. Install from this folder as a local marketplace
claude plugin marketplace add ./plugins/jev-compact-gate
claude plugin install jev-compact-gate@jev-compact-gate

# Or load it for one session without installing
CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1 claude --plugin-dir ./plugins/jev-compact-gate
```

An installed plugin is a snapshot in `~/.claude/plugins/cache/`. After editing the source, bump `version` in `.claude-plugin/plugin.json` and `marketplace.json`, then run `claude plugin marketplace update jev-compact-gate && claude plugin update jev-compact-gate@jev-compact-gate`. An unchanged version skips the update.

---

## Configuration

Set values with `/plugin configure jev-compact-gate@jev-compact-gate`, or under `pluginConfigs["jev-compact-gate@jev-compact-gate"].options` in settings (`jev-compact-gate@inline` when loaded with `--plugin-dir`). Unset options take these defaults:

| Option | Default | Meaning |
|---|---:|---|
| `mode` | `shadow` | `shadow` logs every verdict and never compacts; `live` acts |
| `floorTokens` | `280000` | Below this, the gate never asks |
| `ceilingTokens` | `400000` | At or above this, it compacts without asking |
| `boundaryMax` | `0.7` | `P(at_boundary)` required at the floor |
| `boundaryMin` | `0.3` | `P(at_boundary)` required just below the ceiling |
| `verbatimVeto` | `0.5` | `P(needs_verbatim_recent)` at which the gate holds |
| `debugPenalty` | `0.15` | Threshold raise, weighted by `P(debugging)` |
| `cooldownTurns` | `3` | Turns after a compaction before the gate may act again |
| `timeoutMs` | `5000` | A slower Jev call holds |
| `model` | `typesafe/jev-1.13` | Pinned release; `~typesafe/jev-latest` tracks the newest |

The band only means something on a model with a window above `ceilingTokens` (a 1M-context model). On a 200k window the gate logs once and stands aside.

---

## Shadow Mode and Tuning

Every in-band turn writes one row to `~/.claude/jev-compact-gate/<session-id>.jsonl`, rotating to `<session-id>.1.jsonl`, `.2`, … every 200 rows. `$.fs.write` rewrites whole files, so rotation bounds each write:

```json
{"tokens":312000,"urgency":0.27,"verdict":"compact","reason":"seam","pBoundary":0.96,"pVerbatim":0.13,
 "phase":"wrapping_up","pDebugging":0.01,"threshold":0.59,"jevMs":736,"inputTokens":852,"cost":0.000036,"acted":false}
```

The rows keep Jev's raw judgments, so a threshold change is a re-read of the log, not another Jev call. Run in `shadow` for a week of normal sessions, then read the rows and ask, at each `compact`: would you have compacted there? Tune `boundaryMax`, `boundaryMin`, `verbatimVeto` and `debugPenalty` from those answers, then switch `mode` to `live`. Jev's probabilities are calibrated in aggregate, not certified per call, so fit the thresholds to your own sessions rather than taking round numbers on faith.

---

## Verification

```sh
npm test                   # 67 node:test cases: band edges, veto, thresholds, malformed answers,
                           # redaction, cooldown, vetoed and rejected compactions, transport,
                           # timeout, settings parsing, log rotation
npm run typecheck          # against the engine's declarations (run /plugin-types first)
uv run scripts/smoke.py    # live Jev probe: "just committed" vs "mid-debug"
claude plugin validate .claude-plugin/plugin.json --strict
```

The live probe separates the two canned states cleanly:

| State | `at_boundary` | `needs_verbatim_recent` | `phase` |
|---|---:|---:|---|
| Just committed | 0.96 | 0.13 | wrapping_up (0.94) |
| Mid-debug | 0.05 | 0.67 | debugging (0.99) |

For a hermetic end-to-end run that keeps your user hooks and installed plugins out and writes no transcript, use this. Pass a `--settings` file that sets `pluginConfigs["jev-compact-gate@inline"].options` with a low `floorTokens`:

```sh
env -u ANTHROPIC_API_KEY CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1 claude -p "Reply: ready" \
  --setting-sources project,local --no-session-persistence --debug \
  --plugin-dir ./plugins/jev-compact-gate --settings ./gate-smoke-settings.json
```

---

## Function-Hook Notes

These were learned building against 2.1.283. Early access means they may move.

- **Registration.** A plugin's hooks module is found only through `hooks/hooks.json` → `{ "modules": ["./<file>.ts"] }`, with one module per plugin. Without it the plugin loads and its hooks silently never do.
- **Sandbox.** The module runs with no Node and no DOM, and there is no `setTimeout`. Waits go through `$.clock.sleep(ms, { signal })`. `AbortController` and `AbortSignal.any` exist.
- **Budget.** A hook gets 10s of its own time. Calls in flight on `$` (fetch, compact) do not count, but `$.clock` waits do. Honor `next.signal`, which aborts when the dispatch is abandoned.
- **Compaction from `turn.complete`.** `$.session.compact()` works in interactive sessions. It was verified: the summary ran inside the dispatch in about 12s, and the transcript showed "Conversation compacted". Headless sessions (`-p`, SDK) refuse it with "not available in a headless session yet"; the gate catches that, logs it, and holds.
- **Safe mode.** `--safe-mode` disables every non-builtin hooks module, so use `--setting-sources` to isolate a test run instead.
- **Environment variables.** `$.env.get` takes string literals only. `claude plugin validate` lists every variable the module reads.
- **Imports.** Relative imports resolve with or without the `.ts` extension. The only bare import allowed is `'claude-code'`.
- **Types.** `/plugin-types` writes the engine's declarations to `.claude/types/`. Regenerate them after every Claude Code upgrade and re-check the `session.usage`, `session.compact` and `turn.complete` shapes.

---

## Structure

```
jev-compact-gate/
  .claude-plugin/
    plugin.json          # Manifest and userConfig
    marketplace.json     # Local marketplace (source "./")
  hooks/
    hooks.json           # Names the hooks module
    jev-compact-gate.ts  # Adapter: the engine's $ → src/run.ts Io
  src/
    decide.ts            # Band gate, thresholds, verdict, Jev state + questions (pure)
    run.ts               # Turn loop, System One request/response, timeout
  tests/
    decide.test.ts       # Policy and state construction
    run.test.ts          # Turn loop over a fake Io, transport, timeout
  scripts/
    smoke.py             # Live Jev probe
  INDEX.md               # Folder holdings
  README.md              # This file
```

---

## References

- Jev on OpenRouter: https://openrouter.ai/docs/guides/community/jev
- System One API via OpenRouter: https://openrouter.ai/docs/guides/community/typesafe-sdk
- TypeSafe docs: https://docs.typesafe.ai/ (index at `/llms.txt`)
- Official TypeSafe skill: https://github.com/typesafe-ai/skills
- Prior art (pruning, not timing): https://github.com/tamaratran/fast-jev-compaction
