#!/usr/bin/env node
/**
 * db-maintain.js — Periodic tracker.db maintenance
 *
 * Usage: node db-maintain.js [--quiet]
 *
 * Merges FTS index segments ('optimize') for all three FTS tables and
 * truncates the WAL. Incremental indexer runs fragment the FTS b-trees and
 * grow the WAL unbounded between manual checkpoints; a weekly pass keeps
 * query latency and file size flat. Scheduled via com.claude.db-maintain.plist.
 *
 * Skips (exit 0) when an indexer or backfill pass is running — optimize takes
 * table locks that would stall it.
 */

const os = require('os');
const path = require('path');
const { execSync } = require('child_process');
const db = require(path.join(os.homedir(), '.claude', 'lib', 'tracker-db.js'));

const quiet = process.argv.includes('--quiet');
const log = (m) => { if (!quiet) console.log(m); };

function writerActive() {
  try {
    execSync('pgrep -f "index-transcripts.js|backfill-summaries.js|migrate-to-sqlite.js"',
      { stdio: 'pipe' });
    return true;
  } catch {
    return false; // pgrep exits 1 when nothing matches
  }
}

function main() {
  if (writerActive()) {
    log('An indexer/backfill process is running — skipping maintenance.');
    return;
  }
  const t0 = Date.now();
  const d = db.ensureTranscripts(); // transcript_fts lives in the sidecar DB
  const fs = require('fs');
  const size = () => (fs.statSync(db.DB_PATH).size + fs.statSync(db.TRANSCRIPTS_DB_PATH).size) / 1e6;
  const before = size();

  for (const table of ['transcript_fts', 'sessions_fts', 'phrases_fts']) {
    try {
      d.prepare(`INSERT INTO ${table}(${table}) VALUES('optimize')`).run();
      log(`  optimized ${table}`);
    } catch (e) {
      log(`  ! ${table}: ${e.message}`);
    }
  }
  d.pragma('main.wal_checkpoint(TRUNCATE)');
  d.pragma('transcripts.wal_checkpoint(TRUNCATE)');

  log(`Done in ${((Date.now() - t0) / 1000).toFixed(1)}s — ` +
    `${before.toFixed(1)} MB → ${size().toFixed(1)} MB across both DBs (+WAL truncated).`);
  db.close();
}

main();
