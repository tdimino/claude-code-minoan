# Pre-Compact Handoff System

Session continuity for Claude Code. Fires on `Stop`, `PreCompact`, and `SessionEnd` events to summarize the current session transcript into a structured YAML handoff that the next session can read to recover context.

## Architecture

```
Stop event ──► stop-handoff.py (throttle: 3-min cooldown, 10-min idle gate)
                    │
PreCompact ─────────┤
SessionEnd ─────────┤
                    ▼
             precompact-handoff.py
                    │
              ┌─────┴─────┐
              │  Filter    │  Drop noise types (progress, file-history-snapshot,
              │  transcript│  queue-operation, custom-title, agent-name, last-prompt)
              │            │  Truncate tool_result content to 500 chars
              └─────┬──────┘
                    │
              ┌─────┴─────┐
              │  Estimate  │  chars / 3.2 = tokens
              │  tokens    │  (JSONL averages 3.0-3.3 chars/token, not 4.0)
              └─────┬──────┘
                    │
            ┌───────┴───────┐
            │               │
     < 800K tokens    ≥ 800K tokens
            │               │
      Single-pass      Map-reduce
      (one API call)   (chunk → parallel map → reduce)
            │               │
            └───────┬───────┘
                    │
              ┌─────┴─────┐
              │   Write    │  ~/.claude/handoffs/{session_id}.yaml
              │   YAML     │  + update INDEX.md (last 50 entries)
              └────────────┘
```

## Model

**Qwen Plus 0728** (`qwen/qwen-plus-2025-07-28`) via OpenRouter.

| Spec | Value |
|------|-------|
| Context window | 1,000,000 tokens |
| Input cost | $0.26/M tokens |
| Output cost | $0.78/M tokens |
| Temperature | 0.2 |
| Max output | 2,000 tokens |

Previously: Qwen 3 235B (262K context, $0.07/M). Upgraded 2026-03-18 to handle Opus 4.6's 1M token sessions.

## Output Format

```yaml
session_id: "abc12345-..."
session_short: "abc12345"
timestamp: "2026-03-18T20:35:01"
trigger: "stop"
cwd: "/Users/tom/project"
project: "project"
handoff_count: 3

objective: What the user was trying to accomplish (1-3 sentences)
completed:
  - Item 1
  - Item 2
decisions:
  - Key choice and rationale
blockers: []
next_steps:
  - What should happen next
```

`handoff_count` is a vitality marker—incremented each time the session checkpoints.

## Noise Filtering

The transcript contains 7 JSONL entry types. Only 3 carry signal:

| Type | Signal | Action |
|------|--------|--------|
| `user` (text) | High | Keep |
| `assistant` | High | Keep |
| `system` | Medium | Keep |
| `user` (tool_result) | Mixed | **Truncate** content to 500 chars |
| `progress` | None | **Drop** (17% of chars) |
| `file-history-snapshot` | None | **Drop** (6% of chars) |
| `queue-operation` | None | **Drop** (1% of chars) |
| `custom-title`, `agent-name`, `last-prompt` | None | **Drop** |

Tool result truncation: first 250 chars + `\n...[truncated]...\n` + last 250 chars.

## Map-Reduce

When the filtered transcript exceeds 800K tokens (~2.56M chars):

1. **Chunk** at conversation turn boundaries (user messages with string content). Hard-split fallback if no boundary found within 2x budget.
2. **Map** each chunk independently via `ThreadPoolExecutor(max_workers=3)`. Each chunk gets: "Summarize part {i}/{N} of this session..."
3. **Reduce** all chunk summaries into one YAML: "Merge these {N} partial summaries..."

Typical chunk size: ~200K tokens (~640K chars).

## Throttling (stop-handoff.py)

Three gates prevent excessive firing:

1. **Loop guard**: Skip if `stop_hook_active` is true (prevents infinite loops)
2. **3-minute cooldown**: Per-session, tracked in `.last-stop-handoff`
3. **10-minute idle gate**: Skip if transcript hasn't been modified in 10 minutes

Timeout: 120 seconds (up from 45s to accommodate map-reduce).

## Dry Run

Test without making API calls:

```bash
echo '{"session_id":"test","transcript_path":"/path/to/session.jsonl","cwd":"/tmp","trigger":"test"}' \
  | python3 ~/.claude/hooks/precompact-handoff.py --dry-run
```

Output:
```
Lines read: 45395
Lines after filter: 16680
Chars: 132,172,228
Estimated tokens: 41,303,821
Route: map-reduce (105 chunks @ ~640,000 chars)
Model: qwen/qwen-plus-2025-07-28
```

## Cost

| Session Size | After Filtering | Route | Cost |
|-------------|----------------|-------|------|
| Small (<5K lines) | ~50K tokens | Single-pass | ~$0.01 |
| Medium (5-30K lines) | ~500K tokens | Single-pass | ~$0.13 |
| Large (30-50K lines) | ~1.5M tokens | Map-reduce (3 chunks) | ~$0.42 |
| Very large (50K+ lines) | ~3M tokens | Map-reduce (5 chunks) | ~$0.80 |

## Files

| File | Purpose |
|------|---------|
| `hooks/precompact-handoff.py` | Main summarization logic |
| `hooks/stop-handoff.py` | Throttling + soul registry heartbeat |
| `hooks/HANDOFF-MODEL-EVAL.md` | Model comparison evaluation (2026-03-09) |
| `~/.claude/handoffs/` | Output directory (YAML files + INDEX.md) |

## History

- **2026-03-18**: Upgraded for 1M token context. Qwen Plus 0728 (1M ctx), noise filtering, map-reduce, --dry-run, correct 3.2 chars/token ratio
- **2026-03-09**: Model eval. Switched from Gemini Flash Lite to Qwen 3 235B (262K ctx)
- **2026-02**: Initial implementation with last-200-lines tail window
