import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import {
  buildInstructions,
  buildState,
  DEFAULTS,
  decide,
  estimateTokens,
  gate,
  threshold,
  redact,
  toolLine,
  type Message,
} from '../src/decide.ts';

const approx = (actual: number, expected: number) =>
  assert.ok(Math.abs(actual - expected) < 1e-9, `${actual} ≉ ${expected}`);

const answers = (
  atBoundary: unknown,
  needsVerbatim: unknown,
  phase: unknown = 'implementing',
  pDebugging: unknown = phase === 'debugging' ? 0.9 : 0.02,
) => ({
  at_boundary: { type: 'noul', noul: atBoundary },
  needs_verbatim_recent: { type: 'noul', noul: needsVerbatim },
  phase: { type: 'choice', choice: phase, confidence: 0.9, probabilities: { debugging: pDebugging } },
});

describe('gate', () => {
  const window = 1_000_000;

  it('skips before the first response of a live window', () => {
    assert.deepEqual(gate(undefined, window, DEFAULTS), { action: 'skip', reason: 'no-usage' });
  });

  it('stands aside on a window smaller than the ceiling', () => {
    assert.deepEqual(gate(190_000, 200_000, DEFAULTS), { action: 'skip', reason: 'small-window' });
  });

  it('skips just below the floor', () => {
    assert.deepEqual(gate(279_999, window, DEFAULTS), { action: 'skip', reason: 'below-floor' });
  });

  it('asks at the floor with zero urgency', () => {
    assert.deepEqual(gate(280_000, window, DEFAULTS), { action: 'ask', urgency: 0 });
  });

  it('interpolates urgency across the band', () => {
    const g = gate(340_000, window, DEFAULTS);
    assert.equal(g.action, 'ask');
    approx(g.action === 'ask' ? g.urgency : NaN, 0.5);
  });

  it('forces compaction at the ceiling without asking', () => {
    assert.deepEqual(gate(400_000, window, DEFAULTS), { action: 'ceiling' });
    assert.deepEqual(gate(650_000, window, DEFAULTS), { action: 'ceiling' });
  });
});

describe('threshold', () => {
  it('runs from boundaryMax at the floor to boundaryMin at the ceiling', () => {
    approx(threshold(0, 0, DEFAULTS), 0.7);
    approx(threshold(0.5, 0, DEFAULTS), 0.5);
    approx(threshold(1, 0, DEFAULTS), 0.3);
  });

  it('raises the bar in proportion to P(debugging)', () => {
    approx(threshold(0.5, 1, DEFAULTS), 0.65);
    approx(threshold(0.5, 0.4, DEFAULTS), 0.56);
  });

  it('never exceeds 1', () => {
    assert.equal(threshold(0, 1, { ...DEFAULTS, boundaryMax: 0.95 }), 1);
  });
});

describe('decide', () => {
  it('compacts a clean seam at the floor', () => {
    const v = decide(answers(0.96, 0.13, 'wrapping_up'), 0, DEFAULTS);
    assert.equal(v.action, 'compact');
    assert.equal(v.reason, 'seam');
    approx(v.threshold!, 0.7 + 0.15 * 0.02);
  });

  it('vetoes when exact recent output is still needed, even at a seam near the ceiling', () => {
    const v = decide(answers(0.99, 0.5, 'verifying'), 0.99, DEFAULTS);
    assert.equal(v.action, 'hold');
    assert.equal(v.reason, 'needs-verbatim');
  });

  it('holds mid-work below the boundary threshold', () => {
    const v = decide(answers(0.6, 0.1, 'implementing'), 0, DEFAULTS);
    assert.equal(v.action, 'hold');
    assert.equal(v.reason, 'mid-work');
  });

  it('holds mid-debug even near the ceiling', () => {
    assert.equal(decide(answers(0.05, 0.66, 'debugging'), 0.95, DEFAULTS).action, 'hold');
  });

  it('lets a likely-debugging phase flip a borderline verdict, and an unlikely one not', () => {
    assert.equal(decide(answers(0.6, 0.2, 'implementing'), 0.5, DEFAULTS).action, 'compact');
    assert.equal(decide(answers(0.6, 0.2, 'debugging', 0.9), 0.5, DEFAULTS).action, 'hold');
    assert.equal(decide(answers(0.6, 0.2, 'debugging', 0.3), 0.5, DEFAULTS).action, 'compact');
  });

  it('falls back to the chosen phase when probabilities are absent', () => {
    const bare = answers(0.6, 0.2, 'debugging');
    delete (bare.phase as { probabilities?: unknown }).probabilities;
    const v = decide(bare, 0.5, DEFAULTS);
    assert.equal(v.pDebugging, 1);
    assert.equal(v.action, 'hold');
  });

  it('holds on malformed answers', () => {
    const cases: unknown[] = [
      null,
      {},
      answers(undefined, 0.1),
      answers(0.9, 'high'),
      answers(Number.NaN, 0.1),
      answers(1.4, 0.1),
      answers(0.9, -0.1),
      answers(0.9, 0.1, 42),
      answers(0.9, 0.1, 'debugging', 7),
    ];
    for (const c of cases) {
      const v = decide(c, 0.5, DEFAULTS);
      assert.equal(v.action, 'hold', JSON.stringify(c));
      assert.equal(v.reason, 'malformed');
    }
  });
});

describe('toolLine', () => {
  it('summarizes a Bash call by its command', () => {
    assert.equal(
      toolLine({ tool_use_id: 't1', tool: 'Bash', input: { command: 'cargo test' }, text: '42 passed' }),
      'Bash command="cargo test" → ok 9ch',
    );
  });

  it('marks errors with their first line', () => {
    assert.equal(
      toolLine({
        tool_use_id: 't2',
        tool: 'Bash',
        input: { command: 'cargo run' },
        text: 'thread main panicked at src/load.rs:214\nnote: backtrace',
        isError: true,
      }),
      'Bash command="cargo run" → error: thread main panicked at src/load.rs:214',
    );
  });

  it('summarizes file tools by path and flags calls still in flight', () => {
    assert.equal(
      toolLine({ tool_use_id: 't3', tool: 'Edit', input: { file_path: 'src/a.rs', old_string: 'x' } }),
      'Edit file_path=src/a.rs → pending',
    );
  });
});

describe('redact', () => {
  const cases: [string, string][] = [
    ['curl -H "Authorization: Bearer abc.def-123" x', 'curl -H "Authorization: Bearer [redacted]" x'],
    ['key sk-or-v1-0123456789abcdef0123 here', 'key [redacted] here'],
    ['export OPENROUTER_API_KEY=sk-or-xyz', 'export OPENROUTER_API_KEY=[redacted]'],
    ['GITHUB_TOKEN="ghp_abc123" gh api', 'GITHUB_TOKEN=[redacted] gh api'],
    ['mysql --password=hunter2 -u root', 'mysql --password=[redacted] -u root'],
    ['{"api_key": "abc123", "n": 1}', '{"api_key": [redacted], "n": 1}'],
    ['token ghp_0123456789abcdefghijABCDEFGHIJ012345', 'token [redacted]'],
    ['AKIAIOSFODNN7EXAMPLE is aws', '[redacted] is aws'],
  ];
  for (const [input, expected] of cases) {
    it(`redacts ${input.slice(0, 28)}`, () => assert.equal(redact(input), expected));
  }

  it('leaves ordinary text alone', () => {
    const text = 'git commit -m "fix token parsing" && cargo test --release';
    assert.equal(redact(text), text);
  });
});

describe('buildState', () => {
  const user = (text: string): Message => ({ role: 'user', text, toolUses: [] });
  const toolResultOnly: Message = {
    role: 'user',
    text: '',
    toolUses: [],
    toolResults: [{ tool_use_id: 'x', text: 'ok', isError: false }],
  };
  const assistant = (n: number): Message => ({
    role: 'assistant',
    text: `step ${n}`,
    toolUses: [{ tool_use_id: `t${n}`, tool: 'Read', input: { file_path: `f${n}.ts` }, text: 'body' }],
  });

  it('takes the last three typed prompts, skipping tool-result turns and reminders', () => {
    const messages = [
      user('first'),
      user('second'),
      user('third <system-reminder>noise</system-reminder>'),
      toolResultOnly,
      user('fourth'),
      toolResultOnly,
    ];
    const s = buildState({ messages, answer: 'done' });
    assert.deepEqual(s.recent_prompts, ['second', 'third', 'fourth']);
    assert.deepEqual(Object.keys(s).sort(), ['last_answer', 'recent_activity', 'recent_prompts']);
  });

  it('strips reminder tags that carry attributes', () => {
    const s = buildState({
      messages: [user('ask <system-reminder id="r1" kind="x">secret noise</system-reminder> now')],
      answer: '',
    });
    assert.deepEqual(s.recent_prompts, ['ask  now']);
  });

  it('redacts secrets in prompts, the answer, and tool arguments before they leave', () => {
    const s = buildState({
      messages: [
        user('use key sk-or-v1-0123456789abcdef0123'),
        {
          role: 'assistant',
          text: '',
          toolUses: [
            {
              tool_use_id: 't1',
              tool: 'Bash',
              input: { command: 'curl -H "Authorization: Bearer abc.def" api' },
              text: 'error: 401 for token=abc123',
              isError: true,
            },
          ],
        },
      ],
      answer: 'set GITHUB_TOKEN=ghp_secret first',
    });
    const sent = JSON.stringify(s);
    for (const secret of ['sk-or-v1', 'abc.def', 'abc123', 'ghp_secret']) {
      assert.ok(!sent.includes(secret), `${secret} leaked: ${sent}`);
    }
  });

  it('keeps only the newest fifteen tool calls, oldest first', () => {
    const messages = Array.from({ length: 40 }, (_, i) => assistant(i));
    const s = buildState({ messages, answer: '' });
    assert.equal(s.recent_activity.length, 15);
    assert.ok(s.recent_activity[0].includes('f25.ts'));
    assert.ok(s.recent_activity[14].includes('f39.ts'));
  });

  it('caps tool calls when one message alone carries more than the quota', () => {
    const burst: Message = {
      role: 'assistant',
      text: 'parallel reads',
      toolUses: Array.from({ length: 20 }, (_, i) => ({
        tool_use_id: `b${i}`,
        tool: 'Read',
        input: { file_path: `burst${i}.ts` },
        text: 'x',
      })),
    };
    const newest = buildState({
      messages: [assistant(0), assistant(1), burst, toolResultOnly],
      answer: '',
    });
    assert.equal(newest.recent_activity.length, 15);
    assert.ok(newest.recent_activity[0]!.includes('burst5.ts'));
    assert.ok(newest.recent_activity[14]!.includes('burst19.ts'));

    const older = buildState({
      messages: [burst, ...Array.from({ length: 15 }, (_, i) => assistant(i))],
      answer: '',
    });
    assert.equal(older.recent_activity.length, 15);
    assert.ok(older.recent_activity.every((line) => !line.includes('burst')));
  });

  it('truncates prompts and the answer', () => {
    const s = buildState({
      messages: [user('p'.repeat(5000))],
      answer: 'a'.repeat(5000),
    });
    assert.ok(s.recent_prompts[0]!.length <= 601);
    assert.ok(s.last_answer.length <= 1501);
  });

  it('stays under the state budget on a capped 4096-message transcript', () => {
    const huge = 'lorem ipsum dolor sit amet '.repeat(4000);
    const messages: Message[] = Array.from({ length: 4096 }, (_, i) =>
      i % 2 === 0
        ? user(huge)
        : {
            role: 'assistant',
            text: huge,
            toolUses: [{ tool_use_id: `t${i}`, tool: 'Bash', input: { command: huge }, text: huge }],
          },
    );
    const s = buildState({ messages, answer: huge });
    assert.ok(estimateTokens(s) <= 8000, `state is ${estimateTokens(s)} tokens`);
  });
});

describe('buildInstructions', () => {
  it('names the active goal and phase', () => {
    const text = buildInstructions(['older ask', 'Fix the loader panic on v3 saves'], 'wrapping_up');
    assert.equal(
      text,
      'Preserve the active goal: Fix the loader panic on v3 saves. Current phase: wrapping_up.',
    );
  });

  it('truncates a long goal and omits an unknown phase', () => {
    const text = buildInstructions(['g'.repeat(1000)], undefined);
    assert.ok(text.startsWith('Preserve the active goal: ggg'));
    assert.ok(!text.includes('phase'));
    assert.ok(text.length <= 'Preserve the active goal: '.length + 301 + 1);
  });

  it('is empty when no prompt is known', () => {
    assert.equal(buildInstructions([], 'debugging'), '');
  });
});
