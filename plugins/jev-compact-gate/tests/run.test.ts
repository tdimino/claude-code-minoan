import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import type { Message } from '../src/decide.ts';
import {
  buildJevRequest,
  newMemo,
  onTurn,
  parseJevResponse,
  SETTINGS,
  withTimeout,
  type Io,
  type LogRow,
  type Settings,
  type TurnEvent,
} from '../src/run.ts';

const SEAM = {
  at_boundary: { type: 'noul', noul: 0.96 },
  needs_verbatim_recent: { type: 'noul', noul: 0.13 },
  phase: { type: 'choice', choice: 'wrapping_up', confidence: 0.95 },
};
const MID_DEBUG = {
  at_boundary: { type: 'noul', noul: 0.05 },
  needs_verbatim_recent: { type: 'noul', noul: 0.66 },
  phase: { type: 'choice', choice: 'debugging', confidence: 0.99 },
};

const MESSAGES: Message[] = [
  { role: 'user', text: 'Add retry to the fetch client', toolUses: [] },
  {
    role: 'assistant',
    text: 'Committed.',
    toolUses: [{ tool_use_id: 't1', tool: 'Bash', input: { command: 'git commit' }, text: 'ok' }],
  },
];

type Calls = { ask: number; compact: string[]; rows: LogRow[] };

function fakeIo(opts: {
  tokens?: number;
  window?: number;
  answers?: unknown;
  askError?: Error;
  compactResult?: { skip?: string };
  compactError?: Error;
}): { io: Io; calls: Calls } {
  const calls: Calls = { ask: 0, compact: [], rows: [] };
  const io: Io = {
    usage: async () => ({ tokens: opts.tokens, window: opts.window ?? 1_000_000, percent: 30 }),
    messages: async () => MESSAGES,
    ask: async () => {
      calls.ask++;
      if (opts.askError) throw opts.askError;
      return { answers: opts.answers, inputTokens: 1200, cost: 0.00005 };
    },
    compact: async (instructions) => {
      calls.compact.push(instructions);
      if (opts.compactError) throw opts.compactError;
      return opts.compactResult ?? {};
    },
    log: async (row) => {
      calls.rows.push(row);
    },
    now: () => 1_000,
  };
  return { io, calls };
}

const turn = (over: Partial<TurnEvent> = {}): TurnEvent => ({
  turnId: 'turn-1',
  answer: 'All tests pass; committed a3f9c1e.',
  reason: 'answer',
  isAborted: false,
  ...over,
});

const live: Settings = { ...SETTINGS, mode: 'live' };

describe('onTurn skips', () => {
  for (const [name, event] of [
    ['a subagent turn', turn({ agentId: 'agent-7' })],
    ['an aborted turn', turn({ isAborted: true, reason: 'aborted' })],
    ['an errored turn', turn({ reason: 'error' })],
  ] as const) {
    it(name, async () => {
      const { io, calls } = fakeIo({ tokens: 350_000, answers: SEAM });
      await onTurn(event, io, live, newMemo());
      assert.equal(calls.ask, 0);
      assert.deepEqual(calls.compact, []);
    });
  }

  it('a turn while a compaction is in flight', async () => {
    const { io, calls } = fakeIo({ tokens: 350_000, answers: SEAM });
    const memo = newMemo();
    memo.busy = true;
    await onTurn(turn(), io, live, memo);
    assert.equal(calls.ask, 0);
  });

  it('below the floor, silently', async () => {
    const { io, calls } = fakeIo({ tokens: 150_000, answers: SEAM });
    await onTurn(turn(), io, live, newMemo());
    assert.equal(calls.ask, 0);
    assert.deepEqual(calls.rows, []);
  });

  it('a small window, logging it once', async () => {
    const { io, calls } = fakeIo({ tokens: 190_000, window: 200_000, answers: SEAM });
    const memo = newMemo();
    await onTurn(turn(), io, live, memo);
    await onTurn(turn(), io, live, memo);
    assert.equal(calls.rows.length, 1);
    assert.equal(calls.rows[0].gate, 'small-window');
  });
});

describe('onTurn in the band', () => {
  it('shadow mode logs a compact verdict without compacting', async () => {
    const { io, calls } = fakeIo({ tokens: 300_000, answers: SEAM });
    await onTurn(turn(), io, SETTINGS, newMemo());
    assert.equal(calls.ask, 1);
    assert.deepEqual(calls.compact, []);
    assert.equal(calls.rows[0].verdict, 'compact');
    assert.equal(calls.rows[0].acted, false);
    assert.equal(calls.rows[0].inputTokens, 1200);
    assert.equal(calls.rows[0].cost, 0.00005);
  });

  it('live mode compacts with instructions and starts the cooldown', async () => {
    const { io, calls } = fakeIo({ tokens: 300_000, answers: SEAM });
    const memo = newMemo();
    await onTurn(turn(), io, live, memo);
    assert.deepEqual(calls.compact, [
      'Preserve the active goal: Add retry to the fetch client. Current phase: wrapping_up.',
    ]);
    assert.equal(calls.rows[0].acted, true);
    assert.equal(memo.lastCompactTurn, memo.turn);
    assert.equal(memo.busy, false);
  });

  it('live mode holds mid-debug', async () => {
    const { io, calls } = fakeIo({ tokens: 390_000, answers: MID_DEBUG });
    await onTurn(turn(), io, live, newMemo());
    assert.deepEqual(calls.compact, []);
    assert.equal(calls.rows[0].verdict, 'hold');
  });

  it('holds and logs when Jev fails', async () => {
    const { io, calls } = fakeIo({ tokens: 390_000, askError: new Error('HTTP 503') });
    await onTurn(turn(), io, live, newMemo());
    assert.deepEqual(calls.compact, []);
    assert.equal(calls.rows[0].verdict, 'hold');
    assert.equal(calls.rows[0].error, 'HTTP 503');
  });
});

describe('onTurn at the ceiling', () => {
  it('live mode compacts without asking Jev', async () => {
    const { io, calls } = fakeIo({ tokens: 410_000, answers: MID_DEBUG });
    await onTurn(turn(), io, live, newMemo());
    assert.equal(calls.ask, 0);
    assert.equal(calls.compact.length, 1);
    assert.equal(calls.rows[0].gate, 'ceiling');
  });

  it('shadow mode only logs', async () => {
    const { io, calls } = fakeIo({ tokens: 410_000 });
    await onTurn(turn(), io, SETTINGS, newMemo());
    assert.deepEqual(calls.compact, []);
    assert.equal(calls.rows[0].acted, false);
  });

  it('respects the cooldown after its own compaction', async () => {
    const { io, calls } = fakeIo({ tokens: 410_000 });
    const memo = newMemo();
    await onTurn(turn(), io, live, memo);
    await onTurn(turn(), io, live, memo);
    assert.equal(calls.compact.length, 1);
    assert.equal(calls.rows.at(-1)?.gate, 'cooldown');
  });

  it('records a vetoed compaction without starting the cooldown', async () => {
    const { io, calls } = fakeIo({ tokens: 410_000, compactResult: { skip: 'PreCompact blocked' } });
    const memo = newMemo();
    await onTurn(turn(), io, live, memo);
    assert.equal(calls.rows[0].skipped, 'PreCompact blocked');
    assert.equal(calls.rows[0].acted, false);
    assert.equal(memo.lastCompactTurn, undefined);
  });

  it('releases the in-flight guard when compaction rejects', async () => {
    const { io, calls } = fakeIo({ tokens: 410_000, compactError: new Error('a turn is running') });
    const memo = newMemo();
    await onTurn(turn(), io, live, memo);
    assert.equal(memo.busy, false);
    assert.equal(calls.rows[0].error, 'a turn is running');
  });
});

describe('Jev transport', () => {
  it('builds a Decisions API request', () => {
    const { url, init } = buildJevRequest('sk-or-x', 'typesafe/jev-1.13', { a: 1 }, { q: { type: 'noul' } });
    assert.equal(url, 'https://openrouter.ai/api/v1/systemone');
    assert.equal(init.method, 'POST');
    assert.equal(init.headers.Authorization, 'Bearer sk-or-x');
    assert.deepEqual(JSON.parse(init.body), {
      model: 'typesafe/jev-1.13',
      state: { a: 1 },
      questions: { q: { type: 'noul' } },
    });
  });

  it('returns the answers and usage of a good response', () => {
    const body = { answers: SEAM, usage: { input_tokens: 852, output_tokens: 70, cost: 0.000036 } };
    assert.deepEqual(parseJevResponse(200, JSON.stringify(body)), {
      answers: SEAM,
      inputTokens: 852,
      cost: 0.000036,
    });
  });

  it('tolerates a response without usage', () => {
    assert.deepEqual(parseJevResponse(200, JSON.stringify({ answers: SEAM })), { answers: SEAM });
  });

  it('throws on an HTTP error, bad JSON, or missing answers', () => {
    assert.throws(() => parseJevResponse(401, '{"error":"no key"}'), /HTTP 401/);
    assert.throws(() => parseJevResponse(200, 'not json'), /JSON/);
    assert.throws(() => parseJevResponse(200, '{"usage":{}}'), /no answers/);
  });

  const sleep = (ms: number, signal: AbortSignal) =>
    new Promise<void>((resolve, reject) => {
      const timer = setTimeout(resolve, ms);
      signal.addEventListener('abort', () => {
        clearTimeout(timer);
        reject(new Error('aborted'));
      });
    });

  it('times out a slow call', async () => {
    const slow = new Promise((resolve) => setTimeout(resolve, 200, 'late'));
    await assert.rejects(withTimeout(slow, 20, sleep), /timeout after 20ms/);
  });

  it('passes a fast call through and cancels its wait', async () => {
    let aborted = false;
    const watched = (ms: number, signal: AbortSignal) => {
      signal.addEventListener('abort', () => (aborted = true));
      return sleep(ms, signal);
    };
    assert.equal(await withTimeout(Promise.resolve('fast'), 1000, watched), 'fast');
    assert.ok(aborted);
  });
});
