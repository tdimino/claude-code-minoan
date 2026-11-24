'use strict';
// Search points a retired session at its slim copy (plan 2026-11-21-001, Task 3e). geniza retires sessions older
// than 90 days out of ~/.claude/projects; with no transcript left, `claude --resume` cannot open one, so search
// prints `geniza read <id>` for it, and the usual resume command for a session whose transcript is still there.
// Run: node --test tests/   (from the suite directory)

const assert = require('node:assert/strict');
const { describe, it, after } = require('node:test');
const { execFileSync, spawnSync } = require('node:child_process');
const { DatabaseSync } = require('node:sqlite');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const SCRIPTS = path.resolve(__dirname, '..', 'scripts');
const REPO_LIB = path.resolve(__dirname, '../../../../lib');
const LAUNCHER = path.resolve(__dirname, '../../../../scripts/ghostty-resume.sh');
const PROJECT_DIR = '-tmp-fixture-project';
const RETIRED = '44444444-4444-4444-8444-444444444444';
const PRESENT = '55555555-5555-4555-8555-555555555555';
const FIXTURE = fs.readFileSync(path.join(__dirname, 'fixtures', 'rich.jsonl'));
const FULL = FIXTURE.subarray(0, FIXTURE.lastIndexOf(0x0a) + 1);
const homes = [];
after(() => { for (const h of homes) fs.rmSync(h, { recursive: true, force: true }); });

describe('retired sessions in search', () => {
  const h = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'tracker-home-')));
  homes.push(h);
  const proj = path.join(h, '.claude', 'projects', PROJECT_DIR);
  fs.mkdirSync(proj, { recursive: true });
  fs.symlinkSync(REPO_LIB, path.join(h, '.claude', 'lib'));
  const env = { ...process.env, HOME: h };
  delete env.GENIZA_ROOT;
  for (const sid of [RETIRED, PRESENT]) fs.writeFileSync(path.join(proj, sid + '.jsonl'), FULL);
  execFileSync('node', ['-e', `
    const db = require(${JSON.stringify(path.join(REPO_LIB, 'tracker-db.js'))});
    require(${JSON.stringify(path.join(SCRIPTS, 'index-transcripts.js'))})
      .refreshTranscriptIndex({ quiet: true, prune: false }).then(() => db.close());`], { env });
  // geniza holds verified copies of both; only RETIRED has left projects/
  const index = path.join(h, '.local', 'share', 'geniza', 'index.sqlite');
  fs.mkdirSync(path.dirname(index), { recursive: true });
  const g = new DatabaseSync(index);
  g.exec(`CREATE TABLE slim (project TEXT NOT NULL, sid TEXT NOT NULL, generation INTEGER NOT NULL, path TEXT NOT NULL,
    members TEXT NOT NULL, records INTEGER NOT NULL, raw_bytes INTEGER NOT NULL, slim_bytes INTEGER NOT NULL,
    newest_mtime_ns INTEGER NOT NULL, captured_at REAL NOT NULL, verified_at REAL, PRIMARY KEY (project, sid, generation))`);
  for (const sid of [RETIRED, PRESENT]) {
    g.prepare('INSERT INTO slim VALUES (?,?,1,?,?,1,1,1,1,1,1795316000)').run(PROJECT_DIR, sid, `slim/${sid}`, '[]');
  }
  g.close();
  fs.unlinkSync(path.join(proj, RETIRED + '.jsonl'));
  const search = (...args) => execFileSync('node', [path.join(SCRIPTS, 'search-sessions.js'), ...args, '--no-refresh'],
    { env, encoding: 'utf8' }).replace(/\x1b\[[0-9;]*m/g, '');

  it('prints geniza read for the retired session and resume for the present one', () => {
    const out = search('auth');
    assert.match(out, new RegExp(`Read \\(retired\\): geniza read ${RETIRED}`));
    assert.match(out, new RegExp(`Resume: cd .* && claude --resume ${PRESENT}`));
    assert.doesNotMatch(out, new RegExp(`claude --resume ${RETIRED}`));
  });

  it('--id lookup of the retired session points at geniza read', () => {
    const out = search('--id', RETIRED.slice(0, 8));
    assert.match(out, new RegExp(`geniza read ${RETIRED}`));
  });

  // The launcher every opener goes through (Task 3b): a retired session opens no tab and names its slim copy
  const launch = (sid) => spawnSync('bash', [LAUNCHER, sid, '--project', h, '--print'], { env, encoding: 'utf8' });

  it('the launcher refuses a retired session and names geniza read', () => {
    const r = launch(RETIRED);
    assert.equal(r.status, 1);
    assert.match(r.stderr, new RegExp(`geniza read ${RETIRED}`));
    assert.equal(fs.existsSync(path.join(h, '.claude', 'run', 'launch', `r-${RETIRED.slice(0, 8)}.sh`)), false);
  });

  it('the launcher still resumes a session whose transcript is there', () => {
    const r = launch(PRESENT);
    assert.equal(r.status, 0, r.stderr);
    assert.match(fs.readFileSync(r.stdout.trim(), 'utf8'), new RegExp(`exec claude --resume ${PRESENT}`));
  });
});
