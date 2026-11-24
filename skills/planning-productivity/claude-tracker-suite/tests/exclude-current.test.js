'use strict';
// --exclude-current drops the session the search runs in. Inside Claude Code that session always matches, because
// it holds the query just typed; CLAUDE_CODE_SESSION_ID names it. There is no newest-transcript guess here: a wrong
// guess would hide a real result, so with the variable unset or malformed nothing is omitted.
// Run: node --test tests/   (from the suite directory)

const assert = require('node:assert/strict');
const { describe, it, after } = require('node:test');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const SCRIPTS = path.resolve(__dirname, '..', 'scripts');
const REPO_LIB = path.resolve(__dirname, '../../../../lib');
const PROJECT_DIR = '-tmp-fixture-project';
const CURRENT = '66666666-6666-4666-8666-666666666666';
const OTHER = '77777777-7777-4777-8777-777777777777';
const FIXTURE = fs.readFileSync(path.join(__dirname, 'fixtures', 'rich.jsonl'));
const FULL = FIXTURE.subarray(0, FIXTURE.lastIndexOf(0x0a) + 1);
const homes = [];
after(() => { for (const h of homes) fs.rmSync(h, { recursive: true, force: true }); });

describe('--exclude-current', () => {
  const h = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'tracker-home-')));
  homes.push(h);
  const proj = path.join(h, '.claude', 'projects', PROJECT_DIR);
  fs.mkdirSync(proj, { recursive: true });
  fs.symlinkSync(REPO_LIB, path.join(h, '.claude', 'lib'));
  const env = { ...process.env, HOME: h, CLAUDE_CODE_SESSION_ID: CURRENT };
  delete env.GENIZA_ROOT;
  for (const sid of [CURRENT, OTHER]) fs.writeFileSync(path.join(proj, sid + '.jsonl'), FULL);
  execFileSync('node', ['-e', `
    const db = require(${JSON.stringify(path.join(REPO_LIB, 'tracker-db.js'))});
    // --name reads the sessions table, which the transcript indexer does not fill: give both a title
    db.initSchema();
    const d = db.getDb();
    for (const id of ${JSON.stringify([CURRENT, OTHER])}) {
      d.prepare("INSERT INTO sessions (session_id, short_id, project_dir, project_path, project_name, custom_title, created_at, modified_at) VALUES (?, ?, 'p', '/p', 'p', 'Quince nickname', '2026-10-30T00:00:00', '2026-10-30T00:00:00')").run(id, id.slice(0, 8));
    }
    require(${JSON.stringify(path.join(SCRIPTS, 'index-transcripts.js'))})
      .refreshTranscriptIndex({ quiet: true, prune: false }).then(() => db.close());`], { env });

  const searchWith = (extraEnv, ...args) =>
    execFileSync('node', [path.join(SCRIPTS, 'search-sessions.js'), ...args, '--no-refresh'],
      { env: { ...env, ...extraEnv }, encoding: 'utf8' }).replace(/\x1b\[[0-9;]*m/g, '');
  const search = (...args) => searchWith({}, ...args);
  const ID = (sid) => new RegExp(`ID: ${sid}`);

  it('without the flag both sessions are listed', () => {
    const out = search('auth');
    assert.match(out, ID(CURRENT));
    assert.match(out, ID(OTHER));
    assert.doesNotMatch(out, /Omitted the current session/);
  });

  it('with the flag the current session is omitted and the other stays', () => {
    const out = search('auth', '--exclude-current');
    assert.doesNotMatch(out, ID(CURRENT));
    assert.match(out, ID(OTHER));
    assert.match(out, new RegExp(`Omitted the current session \\(${CURRENT.slice(0, 8)}\\)`));
  });

  it('--limit 1 returns the other session, not the current one', () => {
    const out = search('auth', '--exclude-current', '--limit', '1');
    assert.doesNotMatch(out, ID(CURRENT));
    assert.match(out, ID(OTHER));
  });

  it('--deep honours the flag', () => {
    const out = search('auth', '--deep', '--exclude-current');
    assert.doesNotMatch(out, ID(CURRENT));
    assert.match(out, ID(OTHER));
  });

  it('--name honours the flag', () => {
    const both = search('quince', '--name');
    assert.match(both, ID(CURRENT));
    assert.match(both, ID(OTHER));
    const out = search('quince', '--name', '--exclude-current');
    assert.doesNotMatch(out, ID(CURRENT));
    assert.match(out, ID(OTHER));
  });

  it('an unset session id omits nothing and says so', () => {
    const out = searchWith({ CLAUDE_CODE_SESSION_ID: '' }, 'auth', '--exclude-current');
    assert.match(out, ID(CURRENT));
    assert.match(out, ID(OTHER));
    assert.match(out, /CLAUDE_CODE_SESSION_ID is not set/);
  });

  it('a malformed session id omits nothing', () => {
    const out = searchWith({ CLAUDE_CODE_SESSION_ID: '../../escape' }, 'auth', '--exclude-current');
    assert.match(out, ID(CURRENT));
    assert.match(out, ID(OTHER));
  });

  it('an explicit --id lookup still finds the current session', () => {
    const out = search('--id', CURRENT.slice(0, 8), '--exclude-current');
    assert.match(out, ID(CURRENT));
  });
});
