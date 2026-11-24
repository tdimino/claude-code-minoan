'use strict';
// The transcript prune is archive-aware and fails closed (plan 2026-11-21-001, Task 3a). geniza retires sessions
// older than 90 days out of ~/.claude/projects and keeps a verified slim copy of each in
// ~/.local/share/geniza/index.sqlite. A vanished transcript keeps its search rows while geniza holds a verified copy,
// and where geniza is in use but its index cannot be read the prune does nothing at all. With no geniza root the
// prune is unchanged.
// Run: node --test tests/   (from the suite directory)

const assert = require('node:assert/strict');
const { describe, it, after } = require('node:test');
const { execFileSync } = require('node:child_process');
const { DatabaseSync } = require('node:sqlite');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const SCRIPTS = path.resolve(__dirname, '..', 'scripts');
const REPO_LIB = path.resolve(__dirname, '../../../../lib');
const PROJECT_DIR = '-tmp-fixture-project';
const ARCHIVED = '22222222-2222-4222-8222-222222222222';
const GONE = '33333333-3333-4333-8333-333333333333';
const FIXTURE = fs.readFileSync(path.join(__dirname, 'fixtures', 'rich.jsonl'));
const FULL = FIXTURE.subarray(0, FIXTURE.lastIndexOf(0x0a) + 1);
const homes = [];
after(() => { for (const h of homes) fs.rmSync(h, { recursive: true, force: true }); });

// geniza's slim table, as geniza.py creates it
const SLIM_SCHEMA = `CREATE TABLE slim (
  project TEXT NOT NULL, sid TEXT NOT NULL, generation INTEGER NOT NULL, path TEXT NOT NULL,
  members TEXT NOT NULL, records INTEGER NOT NULL, raw_bytes INTEGER NOT NULL, slim_bytes INTEGER NOT NULL,
  newest_mtime_ns INTEGER NOT NULL, captured_at REAL NOT NULL, verified_at REAL,
  PRIMARY KEY (project, sid, generation))`;

// A home with both sessions indexed, then both transcripts deleted from projects/
function home() {
  const h = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'tracker-home-')));
  homes.push(h);
  const proj = path.join(h, '.claude', 'projects', PROJECT_DIR);
  fs.mkdirSync(proj, { recursive: true });
  fs.symlinkSync(REPO_LIB, path.join(h, '.claude', 'lib'));
  const env = { ...process.env, HOME: h };
  delete env.GENIZA_ROOT;
  const node = (code) => execFileSync('node', ['-e', `
    const db = require(${JSON.stringify(path.join(REPO_LIB, 'tracker-db.js'))});
    const ix = require(${JSON.stringify(path.join(SCRIPTS, 'index-transcripts.js'))});
    ${code}`], { env, encoding: 'utf8' });
  const refresh = (opts) => JSON.parse(node(`ix.refreshTranscriptIndex({ quiet: true, ...${JSON.stringify(opts)} })
    .then(r => { console.log(JSON.stringify(r)); db.close(); });`).trim().split('\n').pop());
  const indexed = () => JSON.parse(node(`console.log(JSON.stringify(db.ensureTranscripts()
    .prepare('SELECT DISTINCT session_id FROM transcripts.transcript_messages ORDER BY session_id').all()
    .map(r => r.session_id))); db.close();`));
  for (const sid of [ARCHIVED, GONE]) fs.writeFileSync(path.join(proj, sid + '.jsonl'), FULL);
  refresh({ prune: false });
  assert.deepEqual(indexed(), [ARCHIVED, GONE]);
  for (const sid of [ARCHIVED, GONE]) fs.unlinkSync(path.join(proj, sid + '.jsonl'));
  const genizaIndex = path.join(h, '.local', 'share', 'geniza', 'index.sqlite');
  const archive = (rows) => {
    fs.mkdirSync(path.dirname(genizaIndex), { recursive: true });
    const g = new DatabaseSync(genizaIndex);
    g.exec(SLIM_SCHEMA);
    const ins = g.prepare('INSERT INTO slim VALUES (?,?,1,?,?,1,1,1,1,1,?)');
    for (const [sid, verifiedAt] of rows) ins.run(PROJECT_DIR, sid, `slim/${PROJECT_DIR}/${sid}.g1.jsonl.zst`, '[]', verifiedAt);
    g.close();
  };
  return { refresh, indexed, archive, genizaIndex };
}

describe('archive-aware prune', () => {
  it('keeps the search rows of a session geniza holds and prunes one it does not', () => {
    const x = home();
    x.archive([[ARCHIVED, 1795316000]]);
    const r = x.refresh({});
    assert.equal(r.pruned, 1);
    assert.deepEqual(x.indexed(), [ARCHIVED]);
  });

  it('an unverified slim row does not count as archived', () => {
    const x = home();
    x.archive([[ARCHIVED, null]]);
    x.refresh({});
    assert.deepEqual(x.indexed(), []);
  });

  it('with no geniza root at all (geniza not in use) the prune works as before', () => {
    const x = home();
    const r = x.refresh({});
    assert.equal(r.pruned, 2);
    assert.deepEqual(x.indexed(), []);
  });

  it('with a geniza root but no index the prune does nothing', () => {
    const x = home();
    fs.mkdirSync(path.dirname(x.genizaIndex), { recursive: true });
    const r = x.refresh({});
    assert.equal(r.pruned, 0);
    assert.equal(r.pruneSkipped, 'no readable geniza index');
    assert.deepEqual(x.indexed(), [ARCHIVED, GONE]);
  });

  it('with an unreadable geniza index the prune does nothing', () => {
    const x = home();
    fs.mkdirSync(path.dirname(x.genizaIndex), { recursive: true });
    fs.writeFileSync(x.genizaIndex, 'not a database, just bytes '.repeat(200));
    const r = x.refresh({});
    assert.equal(r.pruned, 0);
    assert.deepEqual(x.indexed(), [ARCHIVED, GONE]);
  });
});
