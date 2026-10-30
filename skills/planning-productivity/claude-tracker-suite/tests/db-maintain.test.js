'use strict';
// Weekly maintenance must give back the space full reindexes leave behind
// ('optimize' alone merges FTS segments but the freed pages stay in the
// file), leave a compact database alone, and never fail silently: launchd
// runs it --quiet, so its log lines are the only trace it leaves.
// Run: node --test tests/   (from the suite directory)

const assert = require('node:assert/strict');
const { describe, it, after } = require('node:test');
const { execFileSync, spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const SCRIPTS = path.resolve(__dirname, '..', 'scripts');
const REPO_LIB = path.resolve(__dirname, '../../../../lib');
const homes = [];
after(() => { for (const h of homes) fs.rmSync(h, { recursive: true, force: true }); });

// A home whose sidecar holds ~8 MB of indexed text; `prune` drops it all,
// leaving the pages free
function makeHome({ prune }) {
  const home = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'tracker-home-')));
  homes.push(home);
  fs.mkdirSync(path.join(home, '.claude', 'projects'), { recursive: true });
  fs.symlinkSync(REPO_LIB, path.join(home, '.claude', 'lib'));
  // pgrep stub: "an indexer is running" exactly when RUNNING=1
  const bin = path.join(home, 'bin');
  fs.mkdirSync(bin);
  fs.writeFileSync(path.join(bin, 'pgrep'), '#!/bin/sh\n[ "$RUNNING" = 1 ]\n', { mode: 0o755 });
  const env = { ...process.env, HOME: home, PATH: `${bin}:${process.env.PATH}`, RUNNING: '0' };
  execFileSync('node', ['-e', `
    const db = require(${JSON.stringify(path.join(REPO_LIB, 'tracker-db.js'))});
    db.initSchema();
    const text = 'lorem ipsum dolor sit amet '.repeat(40);
    for (let s = 0; s < 40; s++) {
      const id = String(s).padStart(8, '0') + '-0000-4000-8000-000000000000';
      db.indexTranscript(id, { filePath: '/x/' + id + '.jsonl', transcriptSize: 1, mtimeMs: 1,
        messages: Array.from({ length: 200 }, () => ({ role: 'user', text })) });
    }
    ${prune ? 'db.pruneTranscriptIndex([]);' : ''}
    db.ensureTranscripts().pragma('transcripts.wal_checkpoint(TRUNCATE)');
    db.close();`], { env });
  const sidecar = path.join(home, '.claude', 'tracker-transcripts.db');
  const run = (...args) => spawnSync('node', [path.join(SCRIPTS, 'db-maintain.js'), '--quiet', ...args], { env, encoding: 'utf8' });
  return { home, env, sidecar, run };
}

describe('db-maintain', () => {
  it('vacuums the transcript sidecar when most of it is free pages', () => {
    const h = makeHome({ prune: true });
    const before = fs.statSync(h.sidecar).size;
    const r = h.run();
    const afterSize = fs.statSync(h.sidecar).size;
    assert.equal(r.status, 0, r.stderr);
    assert.ok(before > 4e6, `fixture too small: ${before}`);
    assert.ok(afterSize < before / 4, `${before} → ${afterSize}`);
    assert.match(r.stdout, /vacuumed transcripts/);
  });

  it('leaves a database with few free pages alone', () => {
    const h = makeHome({ prune: false });
    const r = h.run();
    assert.equal(r.status, 0, r.stderr);
    assert.doesNotMatch(r.stdout, /vacuumed/);
    assert.match(r.stdout, /^Done in/m);
  });

  it('skips, and says so even when quiet, while an indexer runs; --force runs anyway', () => {
    const h = makeHome({ prune: true });
    const before = fs.statSync(h.sidecar).size;
    const skipped = spawnSync('node', [path.join(SCRIPTS, 'db-maintain.js'), '--quiet'],
      { env: { ...h.env, RUNNING: '1' }, encoding: 'utf8' });
    assert.equal(skipped.status, 0);
    assert.match(skipped.stdout, /skipping maintenance/);
    assert.equal(fs.statSync(h.sidecar).size, before);
    const forced = spawnSync('node', [path.join(SCRIPTS, 'db-maintain.js'), '--quiet', '--force'],
      { env: { ...h.env, RUNNING: '1' }, encoding: 'utf8' });
    assert.match(forced.stdout, /vacuumed transcripts/);
  });

  it('a failure reaches stderr and the exit code, even when quiet', () => {
    const h = makeHome({ prune: true });
    fs.chmodSync(h.sidecar, 0o444);
    try {
      const r = h.run();
      assert.notEqual(r.status, 0);
      assert.match(r.stderr, /readonly|read-only|unable to open/i);
    } finally { fs.chmodSync(h.sidecar, 0o644); }
  });
});
