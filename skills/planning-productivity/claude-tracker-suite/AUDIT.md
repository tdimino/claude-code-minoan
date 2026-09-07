# claude-tracker-suite Audit

Generated 2026-09-07 15:33 by `scripts/audit-suite.js`.

## Summary

| Priority | Count |
|----------|-------|
| P0 | 0 |
| P1 | 1 |
| P2 | 0 |
| P3 | 0 |

## Findings

### P1

- **[coverage]** Summary coverage 35% (528/1515)
  Sessions without summaries are invisible to metadata-weighted search ranking. Summarizer is disabled by default (2026-07-13); when re-enabled: backfill-summaries.js --enable --provider openrouter.

## Data

### Engine

- Node 26.8.1, node:sqlite → SQLite 3.53.4
- tracker.db opens: true
- Scripts still requiring better-sqlite3: 0

### Coverage

| Metric | Value |
|--------|-------|
| Main session transcripts on disk | 1515 |
| Nested JSONL (tool-results, excluded) | 17888 |
| Sessions in tracker.db | 1515 |
| Unmigrated transcripts | 0 |
| With summary | 528 |
| With auto_title | 385 |
| With first_prompt | 1487 |
| Sessions in transcript FTS | 1416 |
| Transcripts unindexed/changed since indexing | 4 |

### Daemons

- Transcript-index launchd loaded: true; indexer hooks in settings.json: 2/2
- Snapshot launchd loaded: true
- Watcher (claude-tracker-watch, dormant by design): false
- workspace-state.json: present (3 min old)

### Search self-test

| Query | Kind | Metadata | Transcript | Pass |
|-------|------|----------|------------|------|
| twitter background subquadratic imagemagick | transcript recall (vocabulary mismatch) | ✓ | ✓ | ✅ |
| subquadratic porthole symbol | transcript recall (exact vocabulary) | ✓ | ✓ | ✅ |
| image editing | metadata recall (auto title) | ✓ | ✓ | ✅ |

### Inventory (22 scripts)

22 clean, 0 with findings (detailed above).
