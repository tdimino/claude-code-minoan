'use strict';
// The indexer fills the sessions row from the transcript (schema v5), with
// title/summary precedence enforced in SQL, and title_history accepting the
// ai-title and agent-name events Claude Code now writes.
// Run: node --test tests/   (from the suite directory)

const assert = require('node:assert/strict');
const { describe, it, before, after } = require('node:test');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const SCRIPTS = path.resolve(__dirname, '..', 'scripts');
const REPO_LIB = path.resolve(__dirname, '../../../../lib');
const FIXTURES = path.join(__dirname, 'fixtures');

const RICH = '11111111-1111-4111-8111-111111111111';
const OTHER = '22222222-2222-4222-8222-222222222222';
const PLAIN = '33333333-3333-4333-8333-333333333333';
const SYN = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
const PROJECT_DIR = '-tmp-fixture-project';

function makeHome() {
  const home = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'tracker-home-')));
  fs.mkdirSync(path.join(home, '.claude', 'projects', PROJECT_DIR), { recursive: true });
  fs.symlinkSync(REPO_LIB, path.join(home, '.claude', 'lib'));
  return home;
}

function runner(home) {
  const env = { ...process.env, HOME: home };
  const node = (code) => execFileSync('node', ['-e',
    `const db = require(${JSON.stringify(path.join(REPO_LIB, 'tracker-db.js'))}); ${code}`],
  { env, encoding: 'utf8' });
  // ensureTranscripts() is getDb() with the transcripts sidecar attached
  const query = (sql, ...args) => JSON.parse(node(
    `console.log(JSON.stringify(db.ensureTranscripts().prepare(${JSON.stringify(sql)}).all(...${JSON.stringify(args)})));`));
  const index = (...flags) => execFileSync('node', [path.join(SCRIPTS, 'index-transcripts.js'), '--quiet', ...flags],
    { env, encoding: 'utf8' });
  return { node, query, index };
}

const transcript = (home, name) => path.join(home, '.claude', 'projects', PROJECT_DIR, name);

describe('indexer writes session metadata', () => {
  let home, t;

  before(() => {
    home = makeHome();
    t = runner(home);
    fs.copyFileSync(path.join(FIXTURES, 'rich.jsonl'), transcript(home, RICH + '.jsonl'));
    fs.copyFileSync(path.join(FIXTURES, 'no-cost-state.jsonl'), transcript(home, PLAIN + '.jsonl'));
    // Only a <synthetic> assistant record: the transcript has no real model
    fs.writeFileSync(transcript(home, SYN + '.jsonl'), [
      { type: 'user', sessionId: SYN, timestamp: '2026-10-04T10:00:00.000Z', origin: { kind: 'human' }, message: { role: 'user', content: 'hello' } },
      { type: 'assistant', sessionId: SYN, timestamp: '2026-10-04T10:00:01.000Z', message: { id: 'msg_s', role: 'assistant', model: '<synthetic>', content: [{ type: 'text', text: 'No response requested.' }], usage: { input_tokens: 0, output_tokens: 0 } } },
    ].map(r => JSON.stringify(r)).join('\n') + '\n');
    // Claude Code's quarantined copies match a *.jsonl glob; they are not sessions
    fs.copyFileSync(path.join(FIXTURES, 'rich.jsonl'), transcript(home, RICH + '.orphaned-1730000000-ab12.jsonl'));
    t.node(`db.initSchema();
      // A Qwen title/summary, plus stale values the old parser wrote
      // ('<synthetic>' model, a caveat as first prompt), already on file
      db.getDb().prepare("INSERT INTO sessions (session_id, short_id, project_dir, project_path, project_name, created_at, modified_at, auto_title, title_source, summary, summary_source, model, first_prompt, num_turns) VALUES (?, ?, ?, '/tmp/fixture/project', 'project', '2026-10-01T00:00:00', '2026-10-01T00:00:00', 'Qwen guess', 'qwen-local', 'Qwen recap', 'qwen-local', '<synthetic>', '<local-command-caveat>stale', 99)").run(${JSON.stringify(RICH)}, '11111111', ${JSON.stringify(PROJECT_DIR)});
      db.getDb().prepare("INSERT INTO sessions (session_id, short_id, project_dir, project_path, project_name, created_at, modified_at, model, model_short, num_turns, last_prompt) VALUES (?, 'aaaaaaaa', 'p', '/p', 'p', '2026-10-04T10:00:00', '2026-10-04T10:00:00', '<synthetic>', 'synthetic', 99, 'old prompt')").run(${JSON.stringify(SYN)});
      db.close();`);
    t.index();
  });

  after(() => fs.rmSync(home, { recursive: true, force: true }));

  it('fills titles, summary, prompt, model, turns and new v5 columns from the records', () => {
    const [row] = t.query('SELECT * FROM sessions WHERE session_id = ?', RICH);
    assert.equal(row.auto_title, 'Login bug fix and tests');
    assert.equal(row.title_source, 'claude-code');
    assert.equal(row.custom_title, 'My name');
    assert.equal(row.summary_source, 'claude-code');
    assert.match(row.summary, /^You asked to fix the login bug/);
    assert.equal(row.first_prompt, 'Fix the login bug in auth.ts');
    assert.equal(row.model, 'claude-opus-5-5');
    assert.equal(row.num_turns, 2);
    assert.equal(row.cost_source, 'cost-state+computed');
    assert.equal(row.entrypoint, 'cli');
    assert.equal(row.pr_url, 'https://github.com/example/fixture/pull/7');
    assert.equal(row.last_prompt, 'add tests too');
    assert.equal(row.git_branch, 'main');
  });

  it('stores the deduped token totals, cost, duration and derived columns', () => {
    const [row] = t.query(`SELECT total_input_tokens i, total_output_tokens o, cache_read_tokens cr,
      cache_creation_tokens cw, duration_ms d, model_short ms, compact_count cc, version v,
      last_user_msg_at lu, transcript_path tp, total_cost_usd cost FROM sessions WHERE session_id = ?`, RICH);
    // cost-state 1.2345 + msg_D after it (sonnet-5-5: 1 in x $2, 10 out x $10)
    assert.ok(Math.abs(row.cost - 1.234602) < 1e-9, String(row.cost));
    delete row.cost;
    assert.deepEqual(row, { i: 16, o: 160, cr: 1000, cw: 500, d: 12000, ms: 'opus-5.5', cc: 1, v: '2.1.314',
      lu: row.lu, tp: transcript(home, RICH + '.jsonl') });
    assert.match(row.lu, /^2026-/);
  });

  it('replaces stale values from the old parser after a clean read', () => {
    const [row] = t.query('SELECT model, first_prompt, num_turns FROM sessions WHERE session_id = ?', RICH);
    assert.deepEqual(row, { model: 'claude-opus-5-5', first_prompt: 'Fix the login bug in auth.ts', num_turns: 2 });
  });

  it('clears a stale value the transcript no longer supports (no real model)', () => {
    const [row] = t.query('SELECT model, model_short, num_turns, last_prompt FROM sessions WHERE session_id = ?', SYN);
    assert.deepEqual(row, { model: null, model_short: null, num_turns: 1, last_prompt: null });
  });

  it('takes cwd and project path from the records, not the lossy decoded dir name', () => {
    const [row] = t.query('SELECT cwd, project_path, project_name FROM sessions WHERE session_id = ?', RICH);
    assert.deepEqual(row, { cwd: '/tmp/fixture-project', project_path: '/tmp/fixture-project', project_name: 'fixture-project' });
  });

  it('creates rows for sessions it has never seen', () => {
    const [row] = t.query('SELECT short_id, first_prompt, cost_source, created_at FROM sessions WHERE session_id = ?', PLAIN);
    assert.deepEqual(row, { short_id: '33333333', first_prompt: 'Summarize the README', cost_source: 'computed',
      created_at: '2026-10-02T09:00:00.000Z' });
  });

  it('records ai-title and agent-name events, and routes a foreign custom-title to its own session', () => {
    const rows = t.query('SELECT session_id, title, source FROM title_history ORDER BY first_seen_seq');
    const mine = rows.filter(r => r.session_id === RICH).map(r => `${r.source}:${r.title}`);
    assert.ok(mine.includes('ai-title:Login bug fix'), mine.join(', '));
    assert.ok(mine.includes('ai-title:Login bug fix and tests'), mine.join(', '));
    assert.ok(mine.includes('agent-name:login-fix'), mine.join(', '));
    assert.ok(mine.includes('user:My name'), mine.join(', '));
    assert.deepEqual(rows.filter(r => r.session_id === OTHER).map(r => r.title), ['Other session name']);
  });

  it('ignores .orphaned-* copies', () => {
    const states = t.query('SELECT file_path FROM transcripts.transcript_index_state').map(r => path.basename(r.file_path)).sort();
    assert.deepEqual(states, [RICH + '.jsonl', PLAIN + '.jsonl', SYN + '.jsonl'].sort());
  });
});

describe('upsertSessionMeta precedence', () => {
  let home, t;
  const SID = '66666666-6666-4666-8666-666666666666';

  before(() => {
    home = makeHome();
    t = runner(home);
    t.node(`db.initSchema();
      db.getDb().prepare("INSERT INTO sessions (session_id, short_id, project_dir, project_path, project_name, created_at, modified_at, custom_title, auto_title, title_source, summary, summary_source) VALUES (?, '66666666', 'p', '/p', 'p', '2026-10-01T00:00:00', '2026-10-01T00:00:00', 'Manual name', 'Claude title', 'claude-code', 'Claude recap', 'claude-code')").run(${JSON.stringify(SID)});
      db.close();`);
  });

  after(() => fs.rmSync(home, { recursive: true, force: true }));

  const upsert = (meta) => t.node(`db.upsertSessionMeta(${JSON.stringify(SID)}, ${JSON.stringify(meta)}, { projectDir: 'p' }); db.close();`);
  const row = () => t.query('SELECT custom_title, auto_title, title_source, summary, summary_source, model FROM sessions WHERE session_id = ?', SID)[0];

  it('an agent-name or compact fallback never replaces Claude Code\'s own title or recap', () => {
    upsert({ autoTitle: 'agent name', titleSource: 'agent-name', summary: 'compact text', summarySource: 'compact', model: 'claude-opus-5-5' });
    assert.deepEqual(row(), { custom_title: 'Manual name', auto_title: 'Claude title', title_source: 'claude-code',
      summary: 'Claude recap', summary_source: 'claude-code', model: 'claude-opus-5-5' });
  });

  it('a transcript without a custom-title keeps the stored one; a newer ai-title replaces the old', () => {
    upsert({ customTitle: null, autoTitle: 'Newer title', titleSource: 'claude-code' });
    const r = row();
    assert.equal(r.custom_title, 'Manual name');
    assert.equal(r.auto_title, 'Newer title');
  });

  it('missing fields never erase stored values', () => {
    upsert({});
    assert.equal(row().model, 'claude-opus-5-5');
  });
});

describe('schema v5 migration from a v4 database', () => {
  let home, t;

  before(() => {
    home = makeHome();
    t = runner(home);
    // A v4 title_history with the old CHECK and one existing row
    execFileSync('node', ['-e', `
      const { DatabaseSync } = require('node:sqlite');
      const d = new DatabaseSync(${JSON.stringify(path.join(home, '.claude', 'tracker.db'))});
      d.exec(\`CREATE TABLE schema_version (version INTEGER PRIMARY KEY, applied_at TEXT, description TEXT);
        INSERT INTO schema_version (version) VALUES (4);
        CREATE TABLE title_history (
          id INTEGER PRIMARY KEY, session_id TEXT NOT NULL, title TEXT NOT NULL,
          source TEXT NOT NULL CHECK (source IN ('user','slug','cache','summarizer')),
          observed_at TEXT, observed_in TEXT, first_seen_seq INTEGER,
          recorded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now')),
          UNIQUE(session_id, source, title, observed_in, first_seen_seq));
        INSERT INTO title_history (session_id, title, source, observed_in, first_seen_seq) VALUES ('s', 'kept', 'slug', 's', 1);\`);
      d.close();`]);
    t.node('db.initSchema(); db.close();');
  });

  after(() => fs.rmSync(home, { recursive: true, force: true }));

  it('keeps existing title rows and accepts the new sources', () => {
    t.node(`db.insertTitleEvent({ sessionId: 's', title: 'AI', source: 'ai-title', observedIn: 's', firstSeenSeq: 2 });
      db.insertTitleEvent({ sessionId: 's', title: 'agent', source: 'agent-name', observedIn: 's', firstSeenSeq: 3 }); db.close();`);
    assert.deepEqual(t.query('SELECT title, source FROM title_history ORDER BY first_seen_seq'),
      [{ title: 'kept', source: 'slug' }, { title: 'AI', source: 'ai-title' }, { title: 'agent', source: 'agent-name' }]);
  });

  it('adds the v5 columns and records the version', () => {
    const cols = t.query('PRAGMA table_info(sessions)').map(c => c.name);
    for (const c of ['entrypoint', 'pr_url', 'last_prompt', 'cost_source', 'compact_count', 'title_source']) {
      assert.ok(cols.includes(c), c);
    }
    assert.equal(t.query('SELECT MAX(version) AS v FROM schema_version')[0].v, 5);
  });
});

describe('indexer resilience', () => {
  let home, t;
  const BAD = '99999999-9999-4999-8999-999999999999';

  before(() => {
    home = makeHome();
    t = runner(home);
    fs.copyFileSync(path.join(FIXTURES, 'rich.jsonl'), transcript(home, RICH + '.jsonl'));
    fs.copyFileSync(path.join(FIXTURES, 'no-cost-state.jsonl'), transcript(home, PLAIN + '.jsonl'));
    fs.copyFileSync(path.join(FIXTURES, 'headless.jsonl'), transcript(home, BAD + '.jsonl'));
    // Newest first: the failing session sits between the other two
    const now = Date.now() / 1000;
    fs.utimesSync(transcript(home, RICH + '.jsonl'), now - 300, now - 300);
    fs.utimesSync(transcript(home, BAD + '.jsonl'), now - 200, now - 200);
    fs.utimesSync(transcript(home, PLAIN + '.jsonl'), now - 100, now - 100);
  });

  after(() => fs.rmSync(home, { recursive: true, force: true }));

  it('one session that throws is logged and skipped; older sessions still index', () => {
    const out = execFileSync('node', ['-e', `
      const db = require(${JSON.stringify(path.join(REPO_LIB, 'tracker-db.js'))});
      const ix = require(${JSON.stringify(path.join(SCRIPTS, 'index-transcripts.js'))});
      const real = db.indexTranscript;
      db.indexTranscript = (sid, args) => { if (sid === ${JSON.stringify(BAD)}) throw new TypeError('boom'); return real(sid, args); };
      ix.refreshTranscriptIndex({ quiet: true }).then(r => { console.log(JSON.stringify(r)); db.close(); });`],
    { env: { ...process.env, HOME: home }, encoding: 'utf8' });
    const r = JSON.parse(out.trim().split('\n').pop());
    assert.deepEqual([r.indexed, r.errored], [2, 1]);
    const ids = t.query('SELECT session_id FROM transcripts.transcript_index_state ORDER BY session_id').map(x => x.session_id);
    assert.deepEqual(ids, [RICH, PLAIN].sort());
    const log = fs.readFileSync(path.join(home, '.claude', 'logs', 'transcript-index-errors.log'), 'utf8');
    assert.match(log, new RegExp(BAD.slice(0, 8) + '.*boom'));
  });

  it('--file on an .orphaned copy is refused and creates no session row', () => {
    const orphan = transcript(home, RICH + '.orphaned-1730000000-ab12.jsonl');
    fs.copyFileSync(path.join(FIXTURES, 'rich.jsonl'), orphan);
    t.index('--file', orphan);
    const rows = t.query("SELECT session_id FROM sessions WHERE session_id LIKE '%orphaned%'");
    assert.deepEqual(rows, []);
  });
});

describe('migrate-to-sqlite.js', () => {
  let home, t;
  const MIGRATE = path.resolve(__dirname, '../../../../scripts/migrate-to-sqlite.js');

  before(() => {
    home = makeHome();
    t = runner(home);
    fs.copyFileSync(path.join(FIXTURES, 'rich.jsonl'), transcript(home, RICH + '.jsonl'));
    t.index();
    fs.writeFileSync(path.join(home, '.claude', 'session-summaries.json'),
      JSON.stringify({ [RICH]: { title: 'Stale cache title', summary: 'Stale cache summary' } }));
  });

  after(() => {
    try { fs.chmodSync(transcript(home, RICH + '.jsonl'), 0o644); } catch { /* already restored */ }
    fs.rmSync(home, { recursive: true, force: true });
  });

  const migrate = (...flags) => execFileSync('node', [MIGRATE, ...flags], { env: { ...process.env, HOME: home }, encoding: 'utf8' });

  it('--skip-enrich never puts stale cache text over Claude Code\'s own title and recap', () => {
    migrate('--skip-enrich');
    const [row] = t.query('SELECT auto_title, title_source, summary_source FROM sessions WHERE session_id = ?', RICH);
    assert.deepEqual(row, { auto_title: 'Login bug fix and tests', title_source: 'claude-code', summary_source: 'claude-code' });
  });

  it('an unreadable transcript leaves the stored counts alone', () => {
    fs.chmodSync(transcript(home, RICH + '.jsonl'), 0o000);
    migrate();
    fs.chmodSync(transcript(home, RICH + '.jsonl'), 0o644);
    const [row] = t.query('SELECT num_turns, total_output_tokens, duration_ms FROM sessions WHERE session_id = ?', RICH);
    assert.deepEqual(row, { num_turns: 2, total_output_tokens: 160, duration_ms: 12000 });
  });
});

describe('concurrent first open of a v4 database', () => {
  // A realistic v4 database: today's schema with the v5 changes stripped
  function makeV4(home) {
    fs.rmSync(path.join(home, '.claude', 'tracker.db'), { force: true });
    for (const ext of ['-wal', '-shm']) fs.rmSync(path.join(home, '.claude', 'tracker.db' + ext), { force: true });
    runner(home).node('db.initSchema(); db.close();');
    execFileSync('node', ['-e', `
      const { DatabaseSync } = require('node:sqlite');
      const d = new DatabaseSync(${JSON.stringify(path.join(home, '.claude', 'tracker.db'))});
      for (const c of ['entrypoint', 'pr_url', 'last_prompt', 'cost_source', 'compact_count']) d.exec('ALTER TABLE sessions DROP COLUMN ' + c);
      d.exec(\`DELETE FROM schema_version; INSERT INTO schema_version (version) VALUES (4);
        DROP TABLE title_history;
        CREATE TABLE title_history (
          id INTEGER PRIMARY KEY, session_id TEXT NOT NULL, title TEXT NOT NULL,
          source TEXT NOT NULL CHECK (source IN ('user','slug','cache','summarizer')),
          observed_at TEXT, observed_in TEXT, first_seen_seq INTEGER,
          recorded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now')),
          UNIQUE(session_id, source, title, observed_in, first_seen_seq));\`);
      d.close();`]);
  }

  it('eight processes migrating at once all succeed (4 rounds)', async () => {
    const { spawn } = require('node:child_process');
    const home = makeHome();
    const code = `require(${JSON.stringify(path.join(REPO_LIB, 'tracker-db.js'))}).initSchema();`;
    try {
      for (let round = 0; round < 4; round++) {
        makeV4(home);
        const results = await Promise.all(Array.from({ length: 8 }, () => new Promise((resolve) => {
          const c = spawn('node', ['-e', code], { env: { ...process.env, HOME: home } });
          let err = '';
          c.stderr.on('data', (b) => { err += b; });
          c.on('close', (status) => resolve({ status, err: err.split('\n').find(l => /Error/.test(l)) || '' }));
        })));
        assert.deepEqual(results.filter(r => r.status !== 0), [], `round ${round}`);
        const cols = runner(home).query('PRAGMA table_info(sessions)').map(c => c.name);
        for (const c of ['entrypoint', 'cost_source', 'title_source', 'summary_source']) assert.ok(cols.includes(c), c);
      }
    } finally {
      fs.rmSync(home, { recursive: true, force: true });
    }
  });
});
