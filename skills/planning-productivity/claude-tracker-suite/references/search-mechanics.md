# Search Mechanics

Detailed reference for the tracker search pipeline: indexing, query resolution, ranking, and fallback behavior.

## Transcript FTS Indexing

`index-transcripts.js` walks all top-level session JSONL files (subagent/tool-result payloads in session subdirectories are never enumerated), extracts user+assistant text, and writes to `transcript_messages` / `transcript_fts` in `tracker.db`.

**Incremental skip logic**: each session's file size, mtime, and extractor version are stored in `transcript_index_state`. A file is re-indexed only when any of these three values change. Bumping `EXTRACTOR_VERSION` (currently 4) forces a full reindex under new extraction rules.

**Error handling**: read errors (I/O failures, truncated files) are never recorded in `transcript_index_state`. The session stays eligible for the next run, preventing a partial read from permanently masking content from search.

**Noise filtering**: system-injected turns are skipped via prefix matching (`<command-`, `<local-command`, `<task-notification`, `<system-reminder`) and the shared `isTranscriptNoise()` utility. Individual messages are capped at 20,000 characters.

**Pruning**: on full (unlimited) runs, sessions whose transcript files no longer exist on disk are pruned from the index.

**Title event extraction** (v4+): the indexer extracts `/rename` custom-title lines (source `user`) and slug changes (source `slug`) into the `title_history` table. Custom-title lines route by the line's own `sessionId` field, not the containing file. Consecutive duplicate title values within a file collapse to a single event.

## Default Search Path

`search-sessions.js` without `--deep` or `--name` runs the default path, which merges three result sets:

1. **Transcript FTS** (`db.searchTranscripts`): FTS5 over `transcript_fts` (session-level full text). Multi-word queries match per-term at the session level—terms may appear in different messages. Ranking: IDF-weighted saturated match-density with a short-session damp. Returns highlighted snippet excerpts.

2. **Metadata FTS** (`db.searchSessions`): FTS5 over `sessions_fts` (custom_title, auto_title, slug, summary, first_prompt). Column weights: custom_title 3x, auto_title 2x, summary 2x, first_prompt 1.5x, slug 1x. Sessions already in the transcript result set are deduplicated.

3. **Former-title fallback** (`db.searchTitleHistory`): LIKE search over `title_history` for sessions whose past titles match the query but whose current title does not. High-precision results (the user remembered a specific name) that surface under a "former-title matches" heading. Capped to avoid crowding body results.

## Synonym Expansion

Defined in `references/synonyms.json`. Every token in a synonym group expands to the whole group bidirectionally. Porter stemming already covers plural/verb forms—groups list distinct vocabulary, not inflections.

Example: searching "repo" also matches "repository" and "codebase". Searching "ghostty" also matches "terminal", "shell", and "tty".

## AND-to-OR Fallback

When no session matches every search term (AND mode), the query automatically falls back to OR mode with a labeled partial-match notice in the output. The `search-regression.js` suite includes a fixture (`zzzznonexistentterm`) that validates this fallback returns ranked partial matches rather than nothing.

## --deep Mode

Bypasses the transcript index entirely and performs a streaming raw JSONL scan across all session files. Useful for finding content in new/unindexed sessions or for whole-phrase matching that the tokenized FTS index cannot provide.

## --name Mode

Metadata-only search via `sessions_fts`. No JSONL body scan—fastest mode. Matches against custom_title, auto_title, slug, summary, and tags.

## titles Subcommand

`search-sessions.js titles <id-prefix>` prints the chronological title/nickname timeline for a session. Shows all recorded events from the `title_history` table: timestamp, source (user/slug/cache/summarizer, color-coded), title value, and cross-session rename provenance (when a rename observed in a different session's file targeted this one).

## Regression Suite

`search-regression.js` validates search recall with fixtures that assert a known session appears within the top N results for a given query. Includes an `[expected fail]` fixture documenting a known semantic-recall gap (the word "twitter" was never typed in the target session—no lexical engine can bridge that). The suite passes when expected-fail fixtures fail; an unexpected pass signals the semantic layer has landed and warrants investigation. Exit code 1 on any real failure.
