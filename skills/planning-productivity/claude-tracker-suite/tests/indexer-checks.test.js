'use strict';
// Indexer-side checks: worktree detection from a session's cwd, and the
// sanity line a full (hourly) pass prints for recent sessions whose
// metadata looks wrong.
// Run: node --test tests/   (from the suite directory)

const assert = require('node:assert/strict');
const { describe, it, after } = require('node:test');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const SCRIPTS = path.resolve(__dirname, '..', 'scripts');
const REPO_LIB = path.resolve(__dirname, '../../../../lib');
const tmp = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'tracker-checks-')));
after(() => fs.rmSync(tmp, { recursive: true, force: true }));
// The indexer resolves tracker-db.js under $HOME at load time: never the live one
const home = path.join(tmp, 'home');
fs.mkdirSync(path.join(home, '.claude', 'projects'), { recursive: true });
fs.symlinkSync(REPO_LIB, path.join(home, '.claude', 'lib'));
process.env.HOME = home;
const { isWorktree } = require(path.join(SCRIPTS, 'index-transcripts.js'));

describe('isWorktree', () => {
  const mk = (...p) => { const d = path.join(tmp, ...p); fs.mkdirSync(d, { recursive: true }); return d; };
  const main = mk('main', 'src', 'deep');
  fs.mkdirSync(path.join(tmp, 'main', '.git'));
  const wt = mk('wt', 'pkg');
  fs.writeFileSync(path.join(tmp, 'wt', '.git'), `gitdir: ${path.join(tmp, 'main', '.git', 'worktrees', 'wt')}\n`);
  const sub = mk('main', 'vendor', 'lib', 'inner');
  fs.writeFileSync(path.join(tmp, 'main', 'vendor', 'lib', '.git'), 'gitdir: ../../.git/modules/vendor/lib\n');

  it('a linked worktree is one from any subdirectory', () => {
    assert.equal(isWorktree(path.join(tmp, 'wt')), true);
    assert.equal(isWorktree(wt), true);
  });

  it('a main checkout is not, from any subdirectory', () => {
    assert.equal(isWorktree(path.join(tmp, 'main')), false);
    assert.equal(isWorktree(main), false);
  });

  it('a submodule (a .git file pointing into modules/) is not', () => {
    assert.equal(isWorktree(sub), false);
  });

  it('unknown, not "main checkout", when the answer cannot be read', () => {
    // A .git file without a gitdir line, and a .git the walk cannot stat
    const odd = mk('odd', 'src');
    fs.writeFileSync(path.join(tmp, 'odd', '.git'), 'not a gitdir pointer\n');
    assert.equal(isWorktree(odd), null);
    const locked = mk('locked-parent', 'repo', 'src');
    fs.mkdirSync(path.join(tmp, 'locked-parent', 'repo', '.git'));
    fs.chmodSync(path.join(tmp, 'locked-parent', 'repo'), 0o311);   // traversable, unreadable
    try {
      fs.chmodSync(path.join(tmp, 'locked-parent', 'repo', 'src'), 0o000);
      assert.equal(isWorktree(path.join(tmp, 'locked-parent', 'repo', 'src')), null);
    } finally {
      fs.chmodSync(path.join(tmp, 'locked-parent', 'repo', 'src'), 0o755);
      fs.chmodSync(path.join(tmp, 'locked-parent', 'repo'), 0o755);
    }
  });

  it('unknown when the cwd is gone or outside any repository', () => {
    assert.equal(isWorktree(path.join(tmp, 'gone')), null);
    assert.equal(isWorktree(mk('loose')), null);
    assert.equal(isWorktree(null), null);
  });
});

describe('sanity line on a full pass', () => {
  const proj = path.join(home, '.claude', 'projects', '-tmp-checks');
  fs.mkdirSync(proj, { recursive: true });
  const now = Date.now();
  const ts = (i) => new Date(now - 3600e3 + i * 1000).toISOString();
  const write = (id, records) =>
    fs.writeFileSync(path.join(proj, id + '.jsonl'), records.map(r => JSON.stringify({ sessionId: id, ...r })).join('\n') + '\n');

  const GUESSED = 'aaaaaaaa-0000-4000-8000-000000000001';
  const SILENT = 'aaaaaaaa-0000-4000-8000-000000000002';
  const FINE = 'aaaaaaaa-0000-4000-8000-000000000003';
  write(GUESSED, [
    { type: 'user', timestamp: ts(0), origin: { kind: 'human' }, message: { role: 'user', content: 'hello' } },
    { type: 'assistant', timestamp: ts(1), message: { id: 'm1', role: 'assistant', model: 'claude-nova-1',
      content: [{ type: 'text', text: 'hi' }], usage: { input_tokens: 1, output_tokens: 5 } } },
  ]);
  // 150 KB of assistant output and no prompt the extractor can see
  write(SILENT, Array.from({ length: 30 }, (_, i) => ({ type: 'assistant', timestamp: ts(i),
    message: { id: 'n' + i, role: 'assistant', model: 'claude-opus-5-5',
      content: [{ type: 'text', text: 'x'.repeat(5000) }], usage: { input_tokens: 1, output_tokens: 1 } } })));
  write(FINE, [
    { type: 'user', timestamp: ts(0), origin: { kind: 'human' }, message: { role: 'user', content: 'hello' } },
    { type: 'assistant', timestamp: ts(1), message: { id: 'f1', role: 'assistant', model: 'claude-opus-5-5',
      content: [{ type: 'text', text: 'hi' }], usage: { input_tokens: 1, output_tokens: 5 } } },
  ]);

  const out = execFileSync('node', [path.join(SCRIPTS, 'index-transcripts.js'), '--quiet'],
    { env: { ...process.env, HOME: home }, encoding: 'utf8' });
  const line = out.split('\n').find(l => l.startsWith('Sanity:')) || '';

  it('names the session priced by guess and the large zero-turn one, and nothing else', () => {
    assert.match(line, /1 estimated cost \(aaaaaaaa\b/);
    assert.match(line, /1 zero-turn transcript over 100 KB/);
    assert.match(line, /^Sanity: 2 recent session/);
  });

  it('a no-op pass over the same healthy files repeats the warning, and a clean index prints none', () => {
    const again = execFileSync('node', [path.join(SCRIPTS, 'index-transcripts.js'), '--quiet'],
      { env: { ...process.env, HOME: home }, encoding: 'utf8' });
    assert.match(again, /^Sanity: 2 recent session/m);
    fs.rmSync(path.join(proj, GUESSED + '.jsonl'));
    fs.rmSync(path.join(proj, SILENT + '.jsonl'));
    const clean = execFileSync('node', [path.join(SCRIPTS, 'index-transcripts.js'), '--quiet'],
      { env: { ...process.env, HOME: home }, encoding: 'utf8' });
    assert.doesNotMatch(clean, /Sanity/);
  });
});
