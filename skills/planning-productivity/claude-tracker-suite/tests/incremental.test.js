'use strict';
// Byte-offset incremental indexing: indexing a transcript in pieces, as it
// grows, must leave exactly what one full pass over the final file leaves:
// the same FTS rows, title events and session row.
// Run: node --test tests/   (from the suite directory)

const assert = require('node:assert/strict');
const { describe, it, before, after } = require('node:test');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const SCRIPTS = path.resolve(__dirname, '..', 'scripts');
const REPO_LIB = path.resolve(__dirname, '../../../../lib');
const RICH = '11111111-1111-4111-8111-111111111111';
const PROJECT_DIR = '-tmp-fixture-project';
const FIXTURE = fs.readFileSync(path.join(__dirname, 'fixtures', 'rich.jsonl'));
// The fixture ends in a truncated line; cut at the last newline so "the
// whole file" is a clean transcript
const FULL = FIXTURE.subarray(0, FIXTURE.lastIndexOf(0x0a) + 1);

function makeHome() {
  const home = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'tracker-home-')));
  fs.mkdirSync(path.join(home, '.claude', 'projects', PROJECT_DIR), { recursive: true });
  fs.symlinkSync(REPO_LIB, path.join(home, '.claude', 'lib'));
  return home;
}

function harness(home) {
  const env = { ...process.env, HOME: home };
  const file = path.join(home, '.claude', 'projects', PROJECT_DIR, RICH + '.jsonl');
  // One pass through the module, returning its result counters
  const index = (opts = {}) => JSON.parse(execFileSync('node', ['-e', `
    const db = require(${JSON.stringify(path.join(REPO_LIB, 'tracker-db.js'))});
    const ix = require(${JSON.stringify(path.join(SCRIPTS, 'index-transcripts.js'))});
    ix.refreshTranscriptIndex({ quiet: true, prune: false, ...${JSON.stringify(opts)} }).then(r => { console.log(JSON.stringify(r)); db.close(); });`],
  { env, encoding: 'utf8' }).trim().split('\n').pop());
  const query = (sql) => JSON.parse(execFileSync('node', ['-e', `
    const db = require(${JSON.stringify(path.join(REPO_LIB, 'tracker-db.js'))});
    console.log(JSON.stringify(db.ensureTranscripts().prepare(${JSON.stringify(sql)}).all()));`],
  { env, encoding: 'utf8' }));
  const snapshot = () => ({
    messages: query('SELECT session_id, role, seq, text FROM transcripts.transcript_messages ORDER BY session_id, seq'),
    fts: query("SELECT rowid FROM transcripts.transcript_fts WHERE transcript_fts MATCH 'login OR tests OR auth'").length,
    titles: query('SELECT session_id, title, source, observed_at, observed_in, first_seen_seq FROM title_history ORDER BY session_id, source, first_seen_seq, title'),
    // indexed_at is wall-clock; transcript_path names the per-test home
    session: query('SELECT * FROM sessions').map(({ indexed_at, transcript_path, ...rest }) => rest),
  });
  // Write bytes keeping the file's identity (inode), as Claude Code appends
  const write = (buf) => fs.writeFileSync(file, buf);
  const append = (buf) => fs.appendFileSync(file, buf);
  const touch = (s) => fs.utimesSync(file, s, s);
  return { home, file, index, query, snapshot, write, append, touch };
}

// Byte offset of the end of the Nth line
const cut = (n) => {
  let at = -1;
  for (let i = 0; i < n; i++) at = FULL.indexOf(0x0a, at + 1);
  return at + 1;
};

describe('incremental indexing', () => {
  let reference;
  const homes = [];
  const fresh = () => { const h = harness(makeHome()); homes.push(h.home); return h; };

  before(() => {
    const ref = fresh();
    ref.write(FULL);
    ref.index();
    reference = ref.snapshot();
  });
  after(() => { for (const h of homes) fs.rmSync(h, { recursive: true, force: true }); });

  it('reference pass indexed the fixture', () => {
    assert.ok(reference.messages.length > 3);
    assert.equal(reference.session.length, 1);
  });

  it('three appends equal one full pass; the later passes are increments', () => {
    const h = fresh();
    h.write(FULL.subarray(0, cut(5)));
    assert.equal(h.index().indexed, 1);
    h.append(FULL.subarray(cut(5), cut(17)));
    h.touch(Date.now() / 1000 + 10);
    const second = h.index();
    h.append(FULL.subarray(cut(17)));
    h.touch(Date.now() / 1000 + 20);
    const third = h.index();
    assert.deepEqual([second.appended, third.appended], [1, 1]);
    assert.deepEqual(h.snapshot(), reference);
  });

  it('a pass that ends mid-line resumes at that line, not after it', () => {
    const h = fresh();
    const mid = cut(12) + 40;           // 40 bytes into line 13
    h.write(FULL.subarray(0, mid));
    h.index();
    const [state] = h.query('SELECT byte_offset, line_no FROM transcripts.transcript_index_state');
    assert.deepEqual(state, { byte_offset: cut(12), line_no: 12 });
    h.append(FULL.subarray(mid));
    h.touch(Date.now() / 1000 + 10);
    assert.equal(h.index().appended, 1);
    assert.deepEqual(h.snapshot(), reference);
  });

  it('a file that shrank is rebuilt from scratch', () => {
    const h = fresh();
    h.write(FULL);
    h.index();
    h.write(FULL.subarray(0, cut(10)));
    h.touch(Date.now() / 1000 + 10);
    const r = h.index();
    assert.deepEqual([r.indexed, r.appended], [1, 0]);
    const shrunk = fresh();
    shrunk.write(FULL.subarray(0, cut(10)));
    shrunk.index();
    assert.deepEqual(h.snapshot().messages, shrunk.snapshot().messages);
  });

  it('a replaced file (new inode) is rebuilt, even if it grew', () => {
    const h = fresh();
    h.write(FULL.subarray(0, cut(10)));
    h.index();
    const tmp = h.file + '.tmp';
    fs.writeFileSync(tmp, FULL);
    fs.renameSync(tmp, h.file);
    h.touch(Date.now() / 1000 + 10);
    const r = h.index();
    assert.deepEqual([r.indexed, r.appended], [1, 0]);
    assert.deepEqual(h.snapshot(), reference);
  });

  it('a pass working from an outdated state snapshot neither double-counts nor fails', () => {
    // The hourly pass snapshots every state row at its start; a Stop hook may
    // index the same session before the hourly pass reaches it. The middle
    // span is tool-only (no searchable text), so no UNIQUE clash can save it,
    // and holds two messages, so the first is already counted, not pending.
    const h = fresh();
    const rec = (o) => JSON.stringify({ sessionId: RICH, timestamp: '2026-10-30T12:00:00.000Z', ...o }) + '\n';
    const tool = (id, out) => rec({ type: 'assistant', message: { id, role: 'assistant', model: 'claude-opus-5-5',
      content: [{ type: 'tool_use', id: 't' + id, name: 'Bash', input: {} }], usage: { input_tokens: 1, output_tokens: out } } });
    const head = rec({ type: 'user', origin: { kind: 'human' }, message: { role: 'user', content: 'start' } })
      + rec({ type: 'assistant', message: { id: 'a1', role: 'assistant', model: 'claude-opus-5-5',
        content: [{ type: 'text', text: 'ok' }], usage: { input_tokens: 1, output_tokens: 10 } } });
    h.write(head);
    const stale = `const ix = require(${JSON.stringify(path.join(SCRIPTS, 'index-transcripts.js'))});
      const db = require(${JSON.stringify(path.join(REPO_LIB, 'tracker-db.js'))});
      const file = { filePath: ${JSON.stringify(h.file)}, projectDir: ${JSON.stringify(PROJECT_DIR)} };`;
    execFileSync('node', ['-e', `${stale}
      db.initSchema();
      (async () => {
        await ix.indexOne(file, db.getTranscriptIndexStates());
        const snapshot = db.getTranscriptIndexStates();          // the hourly pass starts here
        require('fs').appendFileSync(file.filePath, ${JSON.stringify(tool('a2', 100) + tool('a2b', 200))});
        await ix.indexOne(file, db.getTranscriptIndexStates());  // a Stop hook gets in first
        require('fs').appendFileSync(file.filePath, ${JSON.stringify(tool('a3', 1000))});
        const r = await ix.indexOne(file, snapshot);             // the hourly pass, on its old snapshot
        if (r.status === 'errored') throw new Error('errored');
        db.close();
      })().catch(e => { console.error(e); process.exit(1); });`], { env: { ...process.env, HOME: h.home } });
    const once = fresh();
    once.write(head + tool('a2', 100) + tool('a2b', 200) + tool('a3', 1000));
    once.index();
    const tokens = (x) => x.query('SELECT total_output_tokens, num_turns FROM sessions');
    assert.deepEqual(tokens(h), tokens(once));
    assert.deepEqual(tokens(h), [{ total_output_tokens: 1310, num_turns: 1 }]);
  });

  it('a writer that moves the state between read and commit forces a whole-file pass', () => {
    const h = fresh();
    h.write(FULL.subarray(0, cut(10)));
    h.index();
    h.append(FULL.subarray(cut(10)));
    h.touch(Date.now() / 1000 + 10);
    const out = execFileSync('node', ['-e', `
      const db = require(${JSON.stringify(path.join(REPO_LIB, 'tracker-db.js'))});
      const ix = require(${JSON.stringify(path.join(SCRIPTS, 'index-transcripts.js'))});
      const real = db.indexTranscript;
      let calls = 0, stale = 0;
      db.indexTranscript = (id, args) => {
        // Another writer commits first, the first time only
        if (calls++ === 0) db.ensureTranscripts().prepare('UPDATE transcript_index_state SET message_count = message_count + 1').run();
        try { return real(id, args); } catch (e) { if (e.code === 'STALE_RESUME') stale++; throw e; }
      };
      ix.indexOne({ filePath: ${JSON.stringify(h.file)}, projectDir: ${JSON.stringify(PROJECT_DIR)} }, new Map())
        .then(r => { console.log(JSON.stringify({ status: r.status, calls, stale })); db.close(); });`],
    { env: { ...process.env, HOME: h.home }, encoding: 'utf8' });
    assert.deepEqual(JSON.parse(out.trim().split('\n').pop()), { status: 'indexed', calls: 2, stale: 1 });
    assert.deepEqual(h.snapshot(), reference);
  });

  describe('a saved state the increment cannot trust is re-read whole', () => {
    // Index the first 10 lines, damage the saved state, append the rest
    const damaged = (sql) => {
      const h = fresh();
      h.write(FULL.subarray(0, cut(10)));
      h.index();
      execFileSync('node', ['-e', `const db = require(${JSON.stringify(path.join(REPO_LIB, 'tracker-db.js'))});
        db.ensureTranscripts().prepare(${JSON.stringify(sql)}).run(); db.close();`], { env: { ...process.env, HOME: h.home } });
      h.append(FULL.subarray(cut(10)));
      h.touch(Date.now() / 1000 + 10);
      const r = h.index();
      const logPath = path.join(h.home, '.claude', 'logs', 'transcript-index-errors.log');
      return { h, r, log: fs.existsSync(logPath) ? fs.readFileSync(logPath, 'utf8') : '' };
    };

    it('unparseable accumulator: full pass, logged, and the session heals', () => {
      const { h, r, log } = damaged("UPDATE transcript_index_state SET acc_json = '{not json'");
      assert.deepEqual([r.indexed, r.appended, r.errored], [1, 0, 0]);
      assert.match(log, /resume state/);
      assert.deepEqual(h.snapshot(), reference);
    });

    it('an empty accumulator is not a fresh start for the tail', () => {
      const { h, r } = damaged("UPDATE transcript_index_state SET acc_json = '{}'");
      assert.deepEqual([r.indexed, r.appended], [1, 0]);
      assert.deepEqual(h.snapshot(), reference);
    });

    it('state saved under other extraction rules: full pass, not logged', () => {
      const { h, r, log } = damaged("UPDATE transcript_index_state SET acc_json = json_set(acc_json, '$.rules', 'older')");
      assert.deepEqual([r.indexed, r.appended], [1, 0]);
      assert.equal(log, '');
      assert.deepEqual(h.snapshot(), reference);
    });
  });

  it('a file rewritten in place (same inode, grew) is re-read whole', () => {
    // A leading byte shifts every line: the old offset no longer ends a line
    const h = fresh();
    h.write(FULL.subarray(0, cut(10)));
    h.index();
    const shifted = Buffer.concat([Buffer.from(' '), FULL]);
    const fd = fs.openSync(h.file, 'r+');
    fs.writeSync(fd, shifted, 0, shifted.length, 0);
    fs.closeSync(fd);
    h.touch(Date.now() / 1000 + 10);
    assert.deepEqual([h.index().indexed], [1]);
    const whole = fresh();
    whole.write(shifted);
    whole.index();
    assert.deepEqual(h.snapshot().messages, whole.snapshot().messages);
  });

  it('an increment replaces the live rename row the Stop hook wrote', () => {
    // session-sync-db.py records a /rename at once with first_seen_seq -1;
    // the indexer's seq-anchored row for the same title supersedes it
    const h = fresh();
    h.write(FULL.subarray(0, cut(10)));
    h.index();
    execFileSync('node', ['-e', `const db = require(${JSON.stringify(path.join(REPO_LIB, 'tracker-db.js'))});
      db.getDb().prepare("INSERT INTO title_history (session_id, title, source, observed_at, observed_in, first_seen_seq) VALUES (?, 'Live rename', 'user', '2026-10-30T12:00:00.000Z', ?, -1)").run(${JSON.stringify(RICH)}, ${JSON.stringify(RICH)});
      db.close();`], { env: { ...process.env, HOME: h.home } });
    h.append(FULL.subarray(cut(10)) + JSON.stringify({ type: 'custom-title', sessionId: RICH, customTitle: 'Live rename' }) + '\n');
    h.touch(Date.now() / 1000 + 10);
    assert.equal(h.index().appended, 1);
    const rows = h.query("SELECT first_seen_seq FROM title_history WHERE title = 'Live rename'");
    assert.equal(rows.length, 1, JSON.stringify(rows));
    assert.ok(rows[0].first_seen_seq >= 0);
  });

  it('an unchanged file is skipped', () => {
    const h = fresh();
    h.write(FULL);
    h.index();
    const r = h.index();
    assert.deepEqual([r.indexed, r.appended, r.skipped], [0, 0, 1]);
  });

  it('--rebuild re-reads an unchanged file whole', () => {
    const h = fresh();
    h.write(FULL);
    h.index();
    const r = h.index({ rebuild: true });
    assert.deepEqual([r.indexed, r.appended, r.skipped], [1, 0, 0]);
  });
});
