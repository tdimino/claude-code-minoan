#!/usr/bin/env node
/**
 * db-maintain.js — Periodic tracker.db maintenance
 *
 * Usage: node db-maintain.js [--quiet] [--force]
 *
 * Merges FTS index segments ('optimize') for all three FTS tables, truncates
 * the WAL, and VACUUMs either database when more than VACUUM_FREE_RATIO of
 * its pages are free. Incremental indexer runs fragment the FTS b-trees and
 * grow the WAL between checkpoints; full reindexes (extractor version bumps)
 * leave most of the sidecar as free pages (observed: 1.7 GB → 204 MB). A
 * weekly pass keeps query latency and file size flat. Scheduled via
 * com.claude.db-maintain.plist, logging to ~/.claude/logs/db-maintain.{log,err}.
 *
 * Skips (exit 0, one line) when an indexer or backfill pass is running —
 * optimize and VACUUM take locks that would stall it. --force skips that
 * check. --quiet drops the per-step lines but keeps the summary; failures
 * always go to stderr and exit 1.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execSync } = require('child_process');
const db = require(path.join(os.homedir(), '.claude', 'lib', 'tracker-db.js'));

const quiet = process.argv.includes('--quiet');
const force = process.argv.includes('--force');
// VACUUM rewrites the whole file; only worth it once a quarter is free
const VACUUM_FREE_RATIO = 0.25;
const log = (m) => { if (!quiet) console.log(m); };
let failures = 0;
const fail = (m) => { failures++; console.error(`db-maintain: ${m}`); };

function writerActive() {
  try {
    execSync('pgrep -f "index-transcripts.js|backfill-summaries.js|migrate-to-sqlite.js"',
      { stdio: 'pipe' });
    return true;
  } catch {
    return false; // pgrep exits 1 when nothing matches
  }
}

// Database files plus their WALs: a checkpoint a reader blocked leaves the
// rewritten pages in the -wal file
function size() {
  let bytes = 0;
  for (const f of [db.DB_PATH, db.TRANSCRIPTS_DB_PATH]) {
    for (const p of [f, `${f}-wal`]) {
      try { bytes += fs.statSync(p).size; } catch { /* no WAL yet */ }
    }
  }
  return bytes / 1e6;
}

/** TRUNCATE checkpoint; false when a reader kept it from finishing. */
function checkpoint(d, schema) {
  const [r] = d.pragma(`${schema}.wal_checkpoint(TRUNCATE)`);
  if (r && r.busy) {
    console.error(`db-maintain: ${schema} WAL not truncated (a reader was active); the next checkpoint will finish it`);
    return false;
  }
  return true;
}

function main() {
  if (!force && writerActive()) {
    console.log('An indexer/backfill process is running — skipping maintenance.');
    return;
  }
  const t0 = Date.now();
  const before = size();
  const d = db.ensureTranscripts(); // transcript_fts lives in the sidecar DB

  for (const table of ['transcript_fts', 'sessions_fts', 'phrases_fts']) {
    try {
      d.prepare(`INSERT INTO ${table}(${table}) VALUES('optimize')`).run();
      log(`  optimized ${table}`);
    } catch (e) {
      fail(`optimize ${table}: ${e.message}`);
    }
  }
  let truncated = checkpoint(d, 'main') & checkpoint(d, 'transcripts');

  const vacuumed = [];
  for (const schema of ['main', 'transcripts']) {
    const pages = d.pragma(`${schema}.page_count`)[0].page_count;
    const free = d.pragma(`${schema}.freelist_count`)[0].freelist_count;
    if (!pages || free / pages <= VACUUM_FREE_RATIO) continue;
    try {
      d.exec(`VACUUM ${schema}`);
      // VACUUM may renumber rowids in tables without an INTEGER PRIMARY KEY
      // (sessions); sessions_fts is keyed on them
      if (schema === 'main') d.prepare("INSERT INTO sessions_fts(sessions_fts) VALUES('rebuild')").run();
      truncated &= checkpoint(d, schema);
      vacuumed.push(schema);
      console.log(`  vacuumed ${schema} (${free} of ${pages} pages were free)`);
    } catch (e) {
      fail(`VACUUM ${schema}: ${e.message}`);
    }
  }

  console.log(`Done in ${((Date.now() - t0) / 1000).toFixed(1)}s — ` +
    `${before.toFixed(1)} MB → ${size().toFixed(1)} MB across both DBs and WALs` +
    (truncated ? '' : ' (a WAL is still pending a checkpoint)') +
    (failures ? `, ${failures} step(s) failed` : '') + '.');
  db.close();
}

try {
  main();
} catch (e) {
  fail(e.message);
}
process.exitCode = failures ? 1 : 0;
