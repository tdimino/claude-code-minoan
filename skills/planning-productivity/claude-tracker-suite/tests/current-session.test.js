'use strict';
// "Current session" for /tag, /checkpoint, /quote: CLAUDE_CODE_SESSION_ID wins
// over the newest-transcript-in-cwd guess, which picks the wrong session when
// several live sessions share a directory.
// Run: node --test tests/   (from the suite directory)

const assert = require('node:assert/strict');
const { describe, it, before, after } = require('node:test');
const { execFileSync, spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const SCRIPTS = path.resolve(__dirname, '..', 'scripts');
const REPO_LIB = path.resolve(__dirname, '../../../../lib');

const OLDER = 'aaaaaaaa-0000-4000-8000-000000000001';
const NEWER = 'bbbbbbbb-0000-4000-8000-000000000002';
const UNROWED = 'cccccccc-0000-4000-8000-000000000003';

describe('current-session detection with two live sessions in one cwd', () => {
  let home, cwd, env;

  before(() => {
    home = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'tracker-home-')));
    cwd = path.join(home, 'work');
    fs.mkdirSync(cwd);
    const claude = path.join(home, '.claude');
    const proj = path.join(claude, 'projects', cwd.replace(/\//g, '-'));
    fs.mkdirSync(proj, { recursive: true });
    fs.symlinkSync(REPO_LIB, path.join(claude, 'lib'));
    for (const id of [OLDER, NEWER]) {
      fs.writeFileSync(path.join(proj, `${id}.jsonl`),
        JSON.stringify({ type: 'user', sessionId: id, cwd, message: { role: 'user', content: 'hi' } }) + '\n');
    }
    const now = Date.now() / 1000;
    fs.utimesSync(path.join(proj, `${OLDER}.jsonl`), now - 60, now - 60);
    fs.utimesSync(path.join(proj, `${NEWER}.jsonl`), now, now);

    env = { ...process.env, HOME: home, CLAUDE_CODE_SESSION_ID: OLDER };
    execFileSync('node', ['-e',
      `const db = require(${JSON.stringify(path.join(REPO_LIB, 'tracker-db.js'))});
       db.initSchema();
       const d = db.getDb();
       for (const id of ${JSON.stringify([OLDER, NEWER])}) {
         d.prepare("INSERT INTO sessions (session_id, short_id, project_dir, project_path, project_name, created_at, modified_at) VALUES (?, ?, 'p', '/p', 'p', '2026-10-30T00:00:00', '2026-10-30T00:00:00')").run(id, id.slice(0, 8));
       }
       db.close();`], { env });
  });

  after(() => fs.rmSync(home, { recursive: true, force: true }));

  const run = (script, ...args) =>
    execFileSync('node', [path.join(SCRIPTS, script), ...args], { cwd, env, encoding: 'utf8', stdio: 'pipe' });
  const runWith = (script, extraEnv, ...args) =>
    spawnSync('node', [path.join(SCRIPTS, script), ...args], { cwd, env: { ...env, ...extraEnv }, encoding: 'utf8' });

  const query = (sql) => execFileSync('node', ['-e',
    `const db = require(${JSON.stringify(path.join(REPO_LIB, 'tracker-db.js'))});
     console.log(JSON.stringify(db.getDb().prepare(${JSON.stringify(sql)}).all()));`],
    { env, encoding: 'utf8' });

  it('tag-session writes the breadcrumb for the env session', () => {
    run('tag-session.js', 'add', 'fixture-tag');
    const crumbs = fs.readdirSync(path.join(home, '.claude', 'session-tags'));
    assert.deepEqual(crumbs, [`${OLDER}.pending-tags`]);
  });

  it('checkpoint-session checkpoints the env session', () => {
    run('checkpoint-session.js', 'create', 'fixture checkpoint');
    assert.deepEqual(JSON.parse(query("SELECT session_id FROM checkpoints WHERE label = 'fixture checkpoint'")),
      [{ session_id: OLDER }]);
  });

  it('quote-session captures into the env session', () => {
    run('quote-session.js', 'capture', 'fixture phrase');
    assert.deepEqual(JSON.parse(query("SELECT session_id FROM tagged_phrases WHERE phrase = 'fixture phrase'")),
      [{ session_id: OLDER }]);
  });

  it('a malformed env id is ignored: falls back to the newest transcript, with a note', () => {
    const crumbs = path.join(home, '.claude', 'session-tags');
    fs.rmSync(crumbs, { recursive: true, force: true });
    const r = runWith('tag-session.js', { CLAUDE_CODE_SESSION_ID: '../../escape' }, 'add', 'fallback-tag');
    assert.equal(r.status, 0, r.stderr);
    assert.deepEqual(fs.readdirSync(crumbs), [`${NEWER}.pending-tags`]);
    assert.match(r.stderr, /guessed the newest session/);
  });

  it('an unset env id falls back to the newest transcript (plain terminal)', () => {
    const r = runWith('quote-session.js', { CLAUDE_CODE_SESSION_ID: '' }, 'capture', 'terminal phrase');
    assert.equal(r.status, 0, r.stderr);
    assert.deepEqual(JSON.parse(query("SELECT session_id FROM tagged_phrases WHERE phrase = 'terminal phrase'")),
      [{ session_id: NEWER }]);
  });

  it('an explicit --session beats the env id', () => {
    const r = runWith('checkpoint-session.js', {}, 'create', 'explicit cp', '--session', NEWER);
    assert.equal(r.status, 0, r.stderr);
    assert.deepEqual(JSON.parse(query("SELECT session_id FROM checkpoints WHERE label = 'explicit cp'")),
      [{ session_id: NEWER }]);
  });

  // The env session has no sessions row until its first Stop hook runs
  it('first-turn checkpoint and quote do not trip the foreign key', () => {
    const c = runWith('checkpoint-session.js', { CLAUDE_CODE_SESSION_ID: UNROWED }, 'create', 'first turn');
    assert.equal(c.status, 0, c.stderr);
    const q = runWith('quote-session.js', { CLAUDE_CODE_SESSION_ID: UNROWED }, 'capture', 'first phrase');
    assert.equal(q.status, 0, q.stderr);
    assert.deepEqual(JSON.parse(query("SELECT session_id FROM checkpoints WHERE label = 'first turn'")),
      [{ session_id: UNROWED }]);
    assert.deepEqual(JSON.parse(query("SELECT session_id FROM tagged_phrases WHERE phrase = 'first phrase'")),
      [{ session_id: UNROWED }]);
  });
});
