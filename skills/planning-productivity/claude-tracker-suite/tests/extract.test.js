'use strict';
// Session-metadata extraction against current (2.1.314) transcript shapes.
// Run: node --test tests/   (from the suite directory)
//
// Targets utils.extractSessionMeta(filePath), which is SYNCHRONOUS (chunked
// fs.readSync, the same reader Phase 3's byte-offset indexing needs). Until it
// exists, the legacy parseSessionEnriched is adapted to the same shape, so the
// assertions fail for the real reasons (dead `summary` records, duplicated
// usage, first-model pricing) rather than for a missing function.
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

function legacyAdapter(filePath) {
  const r = utils.parseSessionEnriched(filePath);
  return {
    sessionId: undefined,
    model: r.model || null,
    firstPrompt: r.firstPrompt || null,
    numTurns: r.numTurns,
    totalCostUsd: r.totalCostUsd,
    costSource: undefined,
    summary: r.summary || null,
    summarySource: undefined,
    autoTitle: undefined,
    customTitle: undefined,
    entrypoint: undefined,
    prUrl: undefined,
    lastPrompt: undefined,
    cwd: undefined,
    gitBranch: undefined,
  };
}

const extract = (filePath) => (utils.extractSessionMeta
  ? utils.extractSessionMeta(filePath)
  : legacyAdapter(filePath));

// Until Phase 2 lands extractSessionMeta, failures report as todo (expected),
// not as a red run; the assertions themselves are unchanged and become
// enforced the moment the function exists.
const PENDING = !utils.extractSessionMeta && 'Phase 2: extractSessionMeta not implemented yet';

const close = (actual, expected) =>
  assert.ok(Math.abs(actual - expected) < 1e-9, `${actual} ≉ ${expected}`);

const RICH_SUMMARY = 'You asked to fix the login bug; auth.ts now validates tokens and the tests pass.';
const richCost = () => 1.2345 + utils.calculateCostUsd('claude-sonnet-5-5', 1, 10, 0, 0);

function assertRich(meta) {
  assert.equal(meta.autoTitle, 'Login bug fix and tests');
  assert.equal(meta.firstPrompt, 'Fix the login bug in auth.ts');
  close(meta.totalCostUsd, richCost());
}

describe('rich session (ai-title, cost-state, away_summary, duplicates)', { todo: PENDING }, () => {
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

describe('session without cost-state (computed cost)', { todo: PENDING }, () => {
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

describe('headless sdk-cli session (no origin fields, session_id key)', { todo: PENDING }, () => {
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

// Opt-in; it is not marked todo, so with no extractor it fails red through
// the legacy adapter (which returns empty past the V8 string limit).
describe('very large transcript (> V8 string limit)', { skip: process.env.TRACKER_TEST_LARGE !== '1' && 'set TRACKER_TEST_LARGE=1 (writes ~600 MB to the OS temp dir)' }, () => {
  it('still extracts metadata that sits on both sides of 600 MB of filler', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'tracker-large-'));
    const file = path.join(dir, '55555555-5555-4555-8555-555555555555.jsonl');
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
