'use strict';
// Gaps found by mutation testing in the Phase 3 review: each test here
// fails under a specific mutation of the code it guards (named in the
// title) that the rest of the suite let through.
// Run: node --test tests/   (from the suite directory)

const assert = require('node:assert/strict');
const { describe, it, after } = require('node:test');
const { execFileSync, spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const SUITE = path.resolve(__dirname, '..');
const LIB = path.resolve(SUITE, '../../../lib');
const HOOKS = path.resolve(SUITE, '../../../hooks');
const SCRIPTS = path.join(SUITE, 'scripts');
const utils = require(path.join(LIB, 'tracker-utils.js'));

const tmp = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'phase3-gaps-')));
after(() => fs.rmSync(tmp, { recursive: true, force: true }));

const SID = 'cccccccc-0000-4000-8000-000000000001';
const T = (s) => `2026-10-30T12:00:${String(s).padStart(2, '0')}.000Z`;
const human = (text, s) => ({ type: 'user', sessionId: SID, timestamp: T(s), origin: { kind: 'human' }, message: { role: 'user', content: text } });
const asst = (id, model, out, s, text = 'ok') => ({ type: 'assistant', sessionId: SID, timestamp: T(s),
  message: { id, role: 'assistant', model, content: [{ type: 'text', text }], usage: { input_tokens: 1, output_tokens: out } } });
const jsonl = (records) => Buffer.from(records.map(r => JSON.stringify(r)).join('\n') + '\n');

// Claude Code re-appends title records on every resume; a cost-state lands
// mid-session; one message streams across two records; one model is unpriced
const RESUMED = jsonl([
  human('fix the parser', 0),
  { type: 'custom-title', customTitle: 'Parser fix', sessionId: SID },
  { type: 'ai-title', aiTitle: 'Parser bug', sessionId: SID },
  asst('m1', 'claude-opus-5-5', 50, 1),
  { type: 'cost-state', sessionId: SID, totalCostUSD: 0.5 },
  asst('m2', 'claude-sonnet-5-5', 5, 2, 'part one'),
  asst('m2', 'claude-sonnet-5-5', 40, 3, 'part two'),
  { type: 'custom-title', customTitle: 'Parser fix', sessionId: SID },
  { type: 'ai-title', aiTitle: 'Parser bug', sessionId: SID },
  human('and the tests', 4),
  asst('m3', 'claude-sonnet-5-5', 30, 5),
]);
const RICH = fs.readFileSync(path.join(SUITE, 'tests/fixtures/rich.jsonl'));
const RICH_FULL = RICH.subarray(0, RICH.lastIndexOf(0x0a) + 1);

function splitAt(buf, k, name) {
  const f = path.join(tmp, name + '.jsonl');
  fs.writeFileSync(f, buf.subarray(0, k));
  const a = utils.extractTranscript(f);
  fs.writeFileSync(f, buf);
  const b = utils.extractTranscript(f, { resume: { acc: a.acc, start: a.end, startLine: a.lines } });
  return { messages: [...a.messages, ...b.messages], titleEvents: [...a.titleEvents, ...b.titleEvents], meta: b.meta };
}

function wholePass(buf, name) {
  const f = path.join(tmp, name + '.jsonl');
  fs.writeFileSync(f, buf);
  const r = utils.extractTranscript(f);
  return { messages: r.messages, titleEvents: r.titleEvents, meta: r.meta };
}

describe('resume at EVERY byte boundary equals one pass (kills M08, M13)', () => {
  for (const [label, buf, id] of [['rich.jsonl', RICH_FULL, '11111111-1111-4111-8111-111111111111'], ['resumed session', RESUMED, SID]]) {
    it(label, () => {
      const whole = wholePass(buf, id);
      for (let k = 1; k < buf.length; k++) {
        assert.deepEqual(splitAt(buf, k, id), whole, `split at byte ${k}`);
      }
    });
  }
});

describe('+estimated across two cost-states (kills M41)', () => {
  it('an unpriced message covered by the NEXT cost-state does not flag the total', () => {
    const f = path.join(tmp, SID + '.jsonl');
    fs.writeFileSync(f, jsonl([
      { type: 'cost-state', sessionId: SID, totalCostUSD: 0.5 },
      asst('n1', 'claude-nova-1', 10, 1),
      // a later message flushes n1's usage BEFORE the next cost-state lands
      asst('p0', 'claude-sonnet-5-5', 10, 2),
      { type: 'cost-state', sessionId: SID, totalCostUSD: 0.6 },
      asst('p1', 'claude-sonnet-5-5', 10, 2),
    ]));
    assert.equal(utils.extractTranscript(f).meta.costSource, 'cost-state+computed');
  });
});

// ---- DB-level harness (same shape as tests/incremental.test.js) ----------
function home() {
  const h = fs.mkdtempSync(path.join(tmp, 'home-'));
  fs.mkdirSync(path.join(h, '.claude', 'projects', '-tmp-gap'), { recursive: true });
  fs.symlinkSync(LIB, path.join(h, '.claude', 'lib'));
  const env = { ...process.env, HOME: h };
  const file = path.join(h, '.claude', 'projects', '-tmp-gap', SID + '.jsonl');
  const node = (code) => execFileSync('node', ['-e', `const db = require(${JSON.stringify(path.join(LIB, 'tracker-db.js'))});
    const ix = require(${JSON.stringify(path.join(SCRIPTS, 'index-transcripts.js'))}); ${code}`], { env, encoding: 'utf8' });
  const index = () => JSON.parse(node(`ix.refreshTranscriptIndex({ quiet: true, prune: false }).then(r => { console.log(JSON.stringify(r)); db.close(); });`).trim().split('\n').pop());
  const sql = (q) => JSON.parse(node(`console.log(JSON.stringify(db.ensureTranscripts().prepare(${JSON.stringify(q)}).all())); db.close();`));
  const bump = (s) => fs.utimesSync(file, s, s);
  return { h, env, file, node, index, sql, bump };
}

describe('resume guards', () => {
  it('rows indexed under an older extractor version get a full pass, not an increment (kills M10)', () => {
    const x = home();
    fs.writeFileSync(x.file, RESUMED.subarray(0, RESUMED.indexOf(0x0a) + 1));
    x.index();
    x.sql('UPDATE transcripts.transcript_index_state SET extractor_version = extractor_version - 1');
    fs.appendFileSync(x.file, RESUMED.subarray(RESUMED.indexOf(0x0a) + 1));
    x.bump(Date.now() / 1000 + 10);
    const r = x.index();
    assert.deepEqual([r.indexed, r.appended], [1, 0]);
  });

  it('a sidecar from before resume state gains the columns and indexes (kills M17)', () => {
    const x = home();
    fs.writeFileSync(x.file, RESUMED);
    // The pre-Phase-3 table: no byte_offset / line_no / inode / acc_json
    execFileSync('sqlite3', [path.join(x.h, '.claude', 'tracker-transcripts.db'), `CREATE TABLE transcript_index_state (
      session_id TEXT PRIMARY KEY, file_path TEXT NOT NULL, project_dir TEXT, transcript_size INTEGER NOT NULL,
      mtime_ms INTEGER NOT NULL, message_count INTEGER DEFAULT 0, extractor_version INTEGER DEFAULT 1,
      indexed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now')));`]);
    const r = x.index();
    assert.equal(r.indexed, 1);
    assert.equal(x.sql('SELECT byte_offset FROM transcripts.transcript_index_state')[0].byte_offset, RESUMED.length);
  });
});

describe('live title rows from the real Stop hook do not survive an increment', () => {
  it('the next pass replaces the hook\'s first_seen_seq -1 row, increment or not', () => {
    const x = home();
    fs.writeFileSync(x.file, jsonl([human('go', 0)]));
    x.index();
    fs.appendFileSync(x.file, jsonl([{ type: 'custom-title', customTitle: 'Renamed', sessionId: SID }]));
    const r = spawnSync('python3', [path.join(HOOKS, 'session-sync-db.py')], { env: x.env, encoding: 'utf8',
      input: JSON.stringify({ session_id: SID, transcript_path: x.file, hook_event_name: 'Stop' }) });
    assert.equal(r.status, 0, r.stderr);
    x.bump(Date.now() / 1000 + 10);
    assert.equal(x.index().appended, 1);
    const rows = x.sql(`SELECT title, first_seen_seq FROM title_history WHERE session_id = '${SID}' AND title = 'Renamed'`);
    assert.deepEqual(rows.map(r => r.first_seen_seq), [2]);
  });
});

describe('worktree flag reaches the session row (kills M53) and a gone cwd is unknown (kills M51)', () => {
  const wt = path.join(tmp, 'wt-repo');
  fs.mkdirSync(path.join(wt, 'pkg'), { recursive: true });
  fs.writeFileSync(path.join(wt, '.git'), `gitdir: ${path.join(tmp, 'main-repo', '.git', 'worktrees', 'wt')}\n`);

  it('is_worktree = 1 for a session whose cwd is inside a linked worktree', () => {
    const x = home();
    fs.writeFileSync(x.file, jsonl([{ ...human('go', 0), cwd: path.join(wt, 'pkg') }, asst('w1', 'claude-opus-5-5', 5, 1)]));
    x.index();
    assert.equal(x.sql(`SELECT is_worktree FROM sessions WHERE session_id = '${SID}'`)[0].is_worktree, 1);
  });

  it('a deleted directory inside a living worktree is unknown, not "worktree"', () => {
    process.env.HOME = home().h;
    const { isWorktree } = require(path.join(SCRIPTS, 'index-transcripts.js'));
    assert.equal(isWorktree(path.join(wt, 'deleted-subdir')), null);
  });
});

describe('sanity line semantics (kills M60, M61, M62)', () => {
  // Rows written directly: these states are exactly what a correct extraction
  // never produces, so they cannot come from a transcript
  it('flags output-without-model and output-without-cost-source, ignores old sessions', () => {
    const x = home();
    const recent = new Date(Date.now() - 3600e3).toISOString();
    const old = new Date(Date.now() - 30 * 86400e3).toISOString();
    const rows = [['d1000000', recent, null, 'computed'], ['d2000000', recent, 'claude-opus-5-5', null],
      ['d3000000', recent, null, null], ['d4000000', old, null, null]];
    x.node(`db.initSchema(); const d = db.ensureTranscripts();
      for (const [p, at, model, src] of ${JSON.stringify(rows)}) {
        const id = p + '-0000-4000-8000-000000000000';
        d.prepare("INSERT INTO sessions (session_id, short_id, project_dir, project_path, project_name, created_at, modified_at, model, cost_source, total_output_tokens, num_turns) VALUES (?, ?, '-x', '/x', 'x', ?, ?, ?, ?, 10, 1)").run(id, p, at, at, model, src);
        d.prepare("INSERT INTO transcripts.transcript_index_state (session_id, file_path, transcript_size, mtime_ms) VALUES (?, '/x', 1, 1)").run(id);
      }
      db.close();`);
    const found = JSON.parse(x.node(`console.log(JSON.stringify(ix.sanityCheck())); db.close();`));
    const byLabel = Object.fromEntries(found.map(([l, ids]) => [l, ids.map(i => i.slice(0, 8)).sort()]));
    assert.deepEqual(byLabel['output with no model'], ['d1000000', 'd3000000']);
    assert.deepEqual(byLabel['output with no cost source'], ['d2000000', 'd3000000']);
  });
});

describe('listings: a hook-inserted row (no entrypoint yet) is not headless (kills M80)', () => {
  it('NULL entrypoint is listed by default', () => {
    const x = home();
    x.node(`db.initSchema(); db.getDb().prepare("INSERT INTO sessions (session_id, short_id, project_dir, project_path, project_name, created_at, modified_at) VALUES ('${SID}', 'cccccccc', '-x', '/x', 'x', '2026-10-30T12:00:00Z', '2026-10-30T12:00:00Z')").run(); db.close();`);
    const ids = JSON.parse(x.node(`console.log(JSON.stringify(db.getRecentSessions({ limit: 50 }).map(r => r.session_id))); db.close();`));
    assert.ok(ids.includes(SID));
  });
});

describe('db-maintain threshold (kills M20; the rest is in db-maintain.test.js)', () => {
  const run = (pruneKeepFrom, args, extraEnv = {}) => {
    const x = home();
    x.node(`db.initSchema(); const text = 'lorem ipsum dolor sit amet '.repeat(40); const ids = [];
      for (let s = 0; s < 40; s++) { const id = String(s).padStart(8, '0') + '-0000-4000-8000-000000000000'; ids.push(id);
        db.indexTranscript(id, { filePath: '/x/' + id + '.jsonl', transcriptSize: 1, mtimeMs: 1,
          messages: Array.from({ length: 200 }, () => ({ role: 'user', text })) }); }
      db.pruneTranscriptIndex(ids.slice(${pruneKeepFrom})); db.close();`);
    return execFileSync('node', [path.join(SCRIPTS, 'db-maintain.js'), ...args], { env: { ...x.env, ...extraEnv }, encoding: 'utf8' });
  };
  it('half the sidecar free: vacuumed', () => assert.match(run(20, ['--force']), /vacuumed transcripts/));
});
