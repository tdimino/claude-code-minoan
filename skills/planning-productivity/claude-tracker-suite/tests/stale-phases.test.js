'use strict';
// Open phases of sessions that ended without a SessionEnd hook (crash, kill,
// purge) are closed by the hourly indexer run instead of staying open forever.
// Run: node --test tests/   (from the suite directory)

const assert = require('node:assert/strict');
const { describe, it, before, after } = require('node:test');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const SCRIPTS = path.resolve(__dirname, '..', 'scripts');
const REPO_LIB = path.resolve(__dirname, '../../../../lib');

const DEAD = 'dddddddd-0000-4000-8000-000000000001';
const LIVE = 'eeeeeeee-0000-4000-8000-000000000002';
const RECENT = 'ffffffff-0000-4000-8000-000000000003';

describe('stale open phases', () => {
  let home, env;

  const db = (code) => execFileSync('node', ['-e',
    `const db = require(${JSON.stringify(path.join(REPO_LIB, 'tracker-db.js'))}); ${code}`],
    { env, encoding: 'utf8' });

  before(() => {
    home = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'tracker-home-')));
    fs.mkdirSync(path.join(home, '.claude', 'projects'), { recursive: true });
    fs.symlinkSync(REPO_LIB, path.join(home, '.claude', 'lib'));
    env = { ...process.env, HOME: home };
    db(`db.initSchema(); const d = db.getDb();
      const ins = d.prepare("INSERT INTO sessions (session_id, short_id, project_dir, project_path, project_name, created_at, modified_at) VALUES (?, ?, 'p', '/p', 'p', ?, ?)");
      const ph = d.prepare("INSERT INTO phases (session_id, phase, turn_start, started_at, trigger) VALUES (?, 'implementing', 1, ?, 'auto')");
      ins.run(${JSON.stringify(DEAD)}, 'dddddddd', '2026-10-01T09:00:00', '2026-10-01T10:00:00');
      ph.run(${JSON.stringify(DEAD)}, '2026-10-01T09:30:00');
      ins.run(${JSON.stringify(LIVE)}, 'eeeeeeee', '2026-10-01T09:00:00', '2026-10-01T10:00:00');
      ph.run(${JSON.stringify(LIVE)}, '2026-10-01T09:30:00');
      const now = new Date().toISOString().slice(0, 19);
      ins.run(${JSON.stringify(RECENT)}, 'ffffffff', now, now);
      ph.run(${JSON.stringify(RECENT)}, now);
      db.close();`);
  });

  after(() => fs.rmSync(home, { recursive: true, force: true }));

  const phases = () => JSON.parse(db(
    `console.log(JSON.stringify(db.getDb().prepare("SELECT session_id, ended_at FROM phases ORDER BY session_id").all()));`));

  it('closes idle, non-live sessions at their last activity; keeps live and recent ones open', () => {
    const closed = JSON.parse(db(`console.log(JSON.stringify(db.closeStalePhases(new Set([${JSON.stringify(LIVE)}]))));`));
    assert.equal(closed, 1);
    assert.deepEqual(phases(), [
      { session_id: DEAD, ended_at: '2026-10-01T10:00:00' },
      { session_id: LIVE, ended_at: null },
      { session_id: RECENT, ended_at: null },
    ]);
  });

  it('runs as part of the full (hourly) indexer pass', () => {
    db(`db.getDb().prepare("UPDATE phases SET ended_at = NULL WHERE session_id = ?").run(${JSON.stringify(DEAD)});`);
    execFileSync('node', [path.join(SCRIPTS, 'index-transcripts.js'), '--quiet'], { env, encoding: 'utf8' });
    assert.equal(phases().find(p => p.session_id === DEAD).ended_at, '2026-10-01T10:00:00');
  });
});
