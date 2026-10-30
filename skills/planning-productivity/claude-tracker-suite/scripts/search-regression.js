#!/usr/bin/env node
/**
 * search-regression.js — Recall regression suite for tracker search
 *
 * Usage: node search-regression.js [--json]
 *
 * Each fixture asserts that a query surfaces a known session within the top N
 * results of the transcript/metadata FTS search, or (maxResults) that it
 * matches at most that many sessions. Run after any change to
 * tracker-db.js search functions, the indexer, or synonyms.json.
 * Exit code 1 on any failure.
 */

const os = require('os');
const path = require('path');
const db = require(path.join(os.homedir(), '.claude', 'lib', 'tracker-db.js'));

// expect: session UUID; topN: rank ceiling; via: which searcher must find it
const FIXTURES = [
  {
    // EXPECTED FAILURE since extractor v7. "twitter" occurs in the target
    // session only inside a loaded skill body (Firecrawl/Jina docs, isMeta),
    // never in the conversation; this passed only while skill bodies were
    // indexed. Same gap as the "semantic recall gap" fixture below.
    name: 'vocabulary-mismatch recall (2026-07-13 live failure) [expected fail]',
    query: 'twitter background subquadratic imagemagick',
    expect: '0a13a63b-8402-488e-94e0-48dc6a4821a7',
    topN: 3, via: 'transcript', expectFail: true,
  },
  {
    // The words of that query actually typed in the session
    name: 'typed-vocabulary recall',
    query: 'background subquadratic imagemagick',
    expect: '0a13a63b-8402-488e-94e0-48dc6a4821a7',
    topN: 3, via: 'transcript',
  },
  {
    name: 'exact vocabulary recall',
    query: 'subquadratic porthole symbol',
    expect: '0a13a63b-8402-488e-94e0-48dc6a4821a7',
    topN: 3, via: 'transcript',
  },
  {
    // Ordinary-word recall with synonym expansion (logo→symbol). No rare
    // token like "porthole" to lean on — ranking must do the work.
    name: 'ordinary-vocabulary recall + synonyms (logo→symbol)',
    query: 'subquadratic logo background',
    expect: '0a13a63b-8402-488e-94e0-48dc6a4821a7',
    topN: 5, via: 'combined',
  },
  {
    // EXPECTED FAILURE — the motivating semantic-recall gap, kept visible.
    // The word "twitter" was never typed in the target session; no lexical
    // engine can bridge that. Passes the suite while failing; if it ever
    // PASSES, the semantic layer landed (or the corpus changed) — revisit.
    name: 'semantic recall gap (destination word never typed) [expected fail]',
    query: 'twitter banner logo',
    expect: '0a13a63b-8402-488e-94e0-48dc6a4821a7',
    topN: 5, via: 'combined', expectFail: true,
  },
  {
    name: 'metadata recall via auto title',
    query: 'image editing',
    expect: '0a13a63b-8402-488e-94e0-48dc6a4821a7',
    topN: 10, via: 'metadata',
  },
  {
    name: 'AND→OR fallback returns ranked partials, not nothing',
    query: 'subquadratic porthole zzzznonexistentterm',
    expect: '0a13a63b-8402-488e-94e0-48dc6a4821a7',
    topN: 5, via: 'transcript', expectMode: 'OR',
  },
  {
    // Retired slug of a session since renamed to "utility plugin" — findable
    // only through title_history
    name: 'former-nickname recall via title history',
    query: 'peppy-nest',
    expect: 'dfb5613a-9104-42b8-b8be-e18c00d30839',
    topN: 5, via: 'title-history',
  },
  {
    // Named only by Claude Code's own ai-title (no rename)
    name: 'metadata recall via ai-title',
    query: 'statusline chevron color',
    expect: 'cb48e97d-cbf9-4d51-82ff-e7234e601774',
    topN: 5, via: 'metadata',
  },
  {
    // A former agent-name, since replaced by an ai-title
    name: 'former agent-name recall via title history',
    query: 'ancient near eastern updates',
    expect: 'c769eaa1-6166-4f11-9309-451635888b1c',
    topN: 5, via: 'title-history',
  },
  {
    // Before v7, compact summaries (which restate CLAUDE.md rules) were
    // indexed: this exact phrase matched 11 sessions, all through them. It
    // guards that exclusion. If the rule is ever reworded in CLAUDE.md the
    // fixture passes vacuously; re-pick the phrase then.
    name: 'CLAUDE.md text does not match unrelated sessions',
    query: 'Goldens change only for a named cause',
    maxResults: 3, via: 'phrase',
  },
  {
    // Typed slash-command arguments are the user's words; the skill body
    // they expand into is not indexed. Before the fix this session was not
    // in the top 5: its only mention of the claim was the arguments.
    name: 'typed slash-command arguments are searchable',
    query: 'lost bag british airways claim',
    expect: '853667ce-3850-48cc-a904-5b8b894e6c88',
    topN: 3, via: 'transcript',
  },
  {
    // Quarantined copies (<uuid>.orphaned-*.jsonl) are never sessions
    name: 'no orphaned or superseded copies in the index',
    query: '(non-UUID session ids)',
    via: 'orphans',
  },
  {
    // Timeline depth: slug birth + rename + slug change + rename + cache era.
    // Guards the indexer's title extraction and the cache import.
    name: 'title timeline holds full rename history',
    query: '(getTitleHistory)',
    expect: 'dfb5613a-9104-42b8-b8be-e18c00d30839',
    topN: 4, via: 'timeline-depth',
  },
];

const jsonMode = process.argv.includes('--json');
const results = [];
let failures = 0;

for (const fx of FIXTURES) {
  const t0 = Date.now();
  let rows = [];
  try {
    if (fx.via === 'metadata') {
      rows = db.searchSessions(fx.query, { limit: fx.topN });
    } else if (fx.via === 'title-history') {
      rows = db.searchTitleHistory(fx.query, fx.topN);
    } else if (fx.via === 'timeline-depth') {
      // topN doubles as the minimum event count; rank 1 = pass
      const events = db.getTitleHistory(fx.expect);
      rows = events.length >= fx.topN ? [{ session_id: fx.expect }] : [];
      fx.topN = 1;
    } else if (fx.via === 'orphans') {
      const d = db.ensureTranscripts();
      const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
      const bad = [
        ...d.prepare('SELECT session_id FROM transcripts.transcript_index_state').all(),
        ...d.prepare('SELECT session_id FROM sessions').all(),
      ].filter(r => !uuid.test(r.session_id));
      rows = bad;
      fx.maxResults = 0;
    } else if (fx.via === 'phrase') {
      // Exact FTS5 phrase, one row per session: searchTranscripts drops quotes
      rows = db.ensureTranscripts().prepare(`
        SELECT DISTINCT m.session_id FROM transcripts.transcript_fts f
        JOIN transcripts.transcript_messages m ON m.rowid = f.rowid
        WHERE transcript_fts MATCH ?`).all(`"${fx.query.replace(/"/g, '""')}"`);
    } else if (fx.via === 'combined') {
      // Mirrors search-sessions.js: transcript hits first, metadata appended
      const body = db.searchTranscripts(fx.query, { limit: fx.topN });
      const seen = new Set(body.map(r => r.session_id));
      const meta = db.searchSessions(fx.query, { limit: fx.topN })
        .filter(r => !seen.has(r.session_id));
      rows = [...body, ...meta].slice(0, fx.topN * 2);
    } else {
      rows = db.searchTranscripts(fx.query, { limit: fx.maxResults !== undefined ? fx.maxResults + 1 : fx.topN });
    }
  } catch (e) {
    results.push({ ...fx, pass: false, error: e.message });
    failures++;
    continue;
  }
  const ms = Date.now() - t0;
  const rank = rows.findIndex(r => r.session_id === fx.expect) + 1;
  const modeOk = !fx.expectMode || (rows[0] && rows[0].mode === fx.expectMode);
  // maxResults fixtures assert ABSENCE: at most that many sessions match
  const found = fx.maxResults !== undefined
    ? rows.length <= fx.maxResults && ms < 2000
    : rank > 0 && rank <= fx.topN && modeOk && ms < 2000;
  // expectFail fixtures document known recall gaps: suite passes when they
  // fail; an unexpected pass is surfaced (not failed) as a signal to revisit
  const pass = fx.expectFail ? true : found;
  const surprise = fx.expectFail && found;
  if (!pass) failures++;
  results.push({ ...fx, pass, surprise, rank: rank || null, matched: rows.length, mode: rows[0] ? rows[0].mode : null, ms });
}

db.close();

if (jsonMode) {
  console.log(JSON.stringify(results, null, 2));
} else {
  for (const r of results) {
    const status = r.surprise ? '\x1b[33m!\x1b[0m' : r.pass ? '\x1b[32m✓\x1b[0m' : '\x1b[31m✗\x1b[0m';
    const detail = r.error
      ? `error: ${r.error}`
      : r.maxResults !== undefined
        ? `${r.matched} match(es), at most ${r.maxResults} allowed · ${r.ms}ms`
        : `rank ${r.rank ?? '—'}/${r.topN} · ${r.mode ?? '?'} · ${r.ms}ms`;
    console.log(`${status} ${r.name}\n    "${r.query}" → ${detail}`);
    if (r.surprise) console.log('    \x1b[33m^ expected-fail fixture PASSED — semantic gap may be closed, revisit\x1b[0m');
  }
  console.log(failures === 0
    ? `\n\x1b[32mAll ${results.length} fixtures pass.\x1b[0m`
    : `\n\x1b[31m${failures}/${results.length} fixtures FAILED.\x1b[0m`);
}

process.exit(failures === 0 ? 0 : 1);
