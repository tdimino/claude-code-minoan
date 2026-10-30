'use strict';
// Session-metadata extraction against current (2.1.314) transcript shapes.
// Run: node --test tests/   (from the suite directory)
//
// Targets utils.extractSessionMeta(filePath), which is SYNCHRONOUS (chunked
// fs.readSync, the same reader Phase 3's byte-offset indexing needs).
//
// Rules pinned here (plan "Field sources"):
//   - session id: first record carrying sessionId ?? session_id
//   - turns / first prompt: user records with origin.kind === 'human' only
//     (task-notification and peer prompts are not turns); a file with no
//     origin fields at all falls back to non-meta user text
//   - cost: last cost-state total, plus deduped usage AFTER it (cost-state is
//     written where a session resumes, not where it ends)
//   - "last" wins for ai-title, away_summary, last-prompt (non-empty), pr-link

const assert = require('node:assert/strict');
const { describe, it } = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const REPO_LIB = path.resolve(__dirname, '../../../../lib');
const LIB_DIR = process.env.TRACKER_LIB_DIR || REPO_LIB;
const utils = require(path.join(LIB_DIR, 'tracker-utils.js'));

const fixture = (name) => path.join(__dirname, 'fixtures', name);

const extract = (filePath) => utils.extractSessionMeta(filePath);

const close = (actual, expected) =>
  assert.ok(Math.abs(actual - expected) < 1e-9, `${actual} ≉ ${expected}`);

const RICH_SUMMARY = 'You asked to fix the login bug; auth.ts now validates tokens and the tests pass.';
const richCost = () => 1.2345 + utils.calculateCostUsd('claude-sonnet-5-5', 1, 10, 0, 0);

function assertRich(meta) {
  assert.equal(meta.autoTitle, 'Login bug fix and tests');
  assert.equal(meta.firstPrompt, 'Fix the login bug in auth.ts');
  close(meta.totalCostUsd, richCost());
}

// Per-million-token prices from the /claude-api skill (2026-10-06 table);
// a 5-minute cache write is 1.25x input on every model.
describe('pricing', () => {
  const M = 1_000_000;
  const cases = [
    // model, [input, output, cacheRead, cacheWrite] $/M
    ['claude-fable-5-1', [10, 50, 0.25, 12.5]],
    ['claude-fable-5', [10, 50, 1.0, 12.5]],
    ['claude-opus-5-5', [4, 20, 0.2, 5]],
    ['claude-opus-5', [5, 25, 0.5, 6.25]],
    ['claude-opus-4-6', [5, 25, 0.5, 6.25]],
    ['claude-opus-4-1-20250805', [15, 75, 1.5, 18.75]],
    ['claude-sonnet-5-5', [2, 10, 0.2, 2.5]],
    ['claude-sonnet-5', [2, 10, 0.2, 2.5]],
    ['claude-sonnet-4-6', [3, 15, 0.3, 3.75]],
    ['claude-haiku-5-5', [0.1, 0.5, 0.01, 0.125]],
  ];
  for (const [model, [inp, out, read, write]] of cases) {
    it(model, () => {
      close(utils.calculateCostUsd(model, M, 0, 0, 0), inp);
      close(utils.calculateCostUsd(model, 0, M, 0, 0), out);
      close(utils.calculateCostUsd(model, 0, 0, M, 0), read);
      close(utils.calculateCostUsd(model, 0, 0, 0, M), write);
    });
  }
});

describe('rich session (ai-title, cost-state, away_summary, duplicates)', () => {
  const meta = extract(fixture('rich.jsonl'));

  it('reads the session id from the records', () => {
    assert.equal(meta.sessionId, '11111111-1111-4111-8111-111111111111');
  });

  it('takes the last ai-title as auto title', () => {
    assert.equal(meta.autoTitle, 'Login bug fix and tests');
  });

  it('keeps its own custom-title and ignores one that targets another session', () => {
    assert.equal(meta.customTitle, 'My name');
  });

  it('uses the last away_summary verbatim (U+2028 intact), sourced to claude-code', () => {
    assert.equal(meta.summary, RICH_SUMMARY);
    assert.equal(meta.summarySource, 'claude-code');
  });

  it('first prompt is the first human-origin prompt, not a caveat or meta record', () => {
    assert.equal(meta.firstPrompt, 'Fix the login bug in auth.ts');
  });

  it('counts human-origin turns only (not task-notification, peer, meta, compact)', () => {
    assert.equal(meta.numTurns, 2);
  });

  it('model is the output-token majority; <synthetic> and a truncated final line are ignored', () => {
    assert.equal(meta.model, 'claude-opus-5-5');
  });

  it('cost is the cost-state total plus deduped usage written after it', () => {
    close(meta.totalCostUsd, richCost());
    assert.equal(meta.costSource, 'cost-state+computed');
  });

  it('last non-empty last-prompt wins over a later explicit marker', () => {
    assert.equal(meta.lastPrompt, 'add tests too');
  });

  it('carries entrypoint, PR link, cwd and branch', () => {
    assert.equal(meta.entrypoint, 'cli');
    assert.equal(meta.prUrl, 'https://github.com/example/fixture/pull/7');
    assert.equal(meta.cwd, '/tmp/fixture-project');
    assert.equal(meta.gitBranch, 'main');
  });
});

describe('session without cost-state (computed cost)', () => {
  const meta = extract(fixture('no-cost-state.jsonl'));

  it('dedupes usage by message.id and prices each message at its own model', () => {
    const expected =
      utils.calculateCostUsd('claude-sonnet-5-5', 5, 50, 0, 0) +
      utils.calculateCostUsd('claude-opus-5-5', 10, 100, 1000, 500);
    close(meta.totalCostUsd, expected);
    assert.equal(meta.costSource, 'computed');
  });

  it('model is the output-token majority, not the first model seen', () => {
    assert.equal(meta.model, 'claude-opus-5-5');
  });

  it('text block of a [text, image] prompt is the first prompt', () => {
    assert.equal(meta.firstPrompt, 'Summarize the README');
  });

  it('has no titles to invent', () => {
    assert.equal(meta.autoTitle, null);
    assert.equal(meta.customTitle, null);
  });
});

describe('headless sdk-cli session (no origin fields, session_id key)', () => {
  const meta = extract(fixture('headless.jsonl'));

  it('reads the session id from session_id', () => {
    assert.equal(meta.sessionId, '44444444-4444-4444-8444-444444444444');
  });

  it('flags the entrypoint', () => {
    assert.equal(meta.entrypoint, 'sdk-cli');
  });

  it('falls back to the first non-meta user text for prompt and turns', () => {
    assert.equal(meta.firstPrompt, 'Reply OK');
    assert.equal(meta.numTurns, 1);
  });
});

// Opt-in: the legacy whole-file parser returned empty past the V8 string limit.
describe('very large transcript (> V8 string limit)', { skip: process.env.TRACKER_TEST_LARGE !== '1' && 'set TRACKER_TEST_LARGE=1 (writes ~600 MB to the OS temp dir)' }, () => {
  it('still extracts metadata that sits on both sides of 600 MB of filler', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'tracker-large-'));
    // Named after the fixture's own session: titles route by session id
    const file = path.join(dir, '11111111-1111-4111-8111-111111111111.jsonl');
    try {
      const lines = fs.readFileSync(fixture('rich.jsonl'), 'utf8').split('\n').slice(0, -1);
      // Head: the first human prompt; tail: titles, summaries, cost-state.
      // A reader that only parses the head (or only the tail) fails.
      const firstHuman = lines.findIndex(l => l.includes('"origin":{"kind":"human"}'));
      const head = lines.slice(0, firstHuman + 1);
      const tail = lines.slice(firstHuman + 1);
      const filler = JSON.stringify({ type: 'attachment', attachment: { type: 'hook_success', content: 'x'.repeat(1 << 20) } }) + '\n';
      const fd = fs.openSync(file, 'w');
      fs.writeSync(fd, head.join('\n') + '\n');
      for (let i = 0; i < 600; i++) fs.writeSync(fd, filler);
      fs.writeSync(fd, tail.join('\n') + '\n');
      fs.closeSync(fd);
      assertRich(extract(file));
    } finally {
      fs.rmSync(dir, { recursive: true, force: true });
    }
  });
});
