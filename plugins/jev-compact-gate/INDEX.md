# jev-compact-gate

Claude Code function-hook plugin. On each main-loop `turn.complete` it places the session in a 280k–400k token band. Inside the band it asks TypeSafe's Jev (`typesafe/jev-1.13` via OpenRouter's System One API) whether a unit of work just closed and whether exact recent tool output is still needed, then compacts through Claude's own `/compact`. At 400k it compacts without asking. Shadow mode logs verdicts without acting.

| Path | Holds |
|---|---|
| `.claude-plugin/plugin.json` | Manifest and `userConfig` (mode, band, thresholds, veto, timeout, model) |
| `.claude-plugin/marketplace.json` | Local marketplace (`source: "./"`) |
| `hooks/hooks.json` | Names the hooks module |
| `hooks/jev-compact-gate.ts` | Adapter from the engine's `$` onto `src/run.ts`'s `Io` |
| `src/decide.ts` | Band gate, thresholds, verdict, Jev state and questions (pure) |
| `src/run.ts` | Turn loop, Jev request/response, timeout |
| `tests/` | `node --test` suites for `decide.ts` and `run.ts` |
| `scripts/smoke.py` | Live Jev probe on two canned states |
| `README.md` | Design, install, configuration, tuning, function-hook notes |
| `.claude/types/` | Engine declarations from `/plugin-types` (git-ignored; regenerate after upgrades) |

- Logs: `~/.claude/jev-compact-gate/<session>.jsonl`
- Configure: `/plugin configure jev-compact-gate@jev-compact-gate`
- Requires: `CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1` and `OPENROUTER_API_KEY`
