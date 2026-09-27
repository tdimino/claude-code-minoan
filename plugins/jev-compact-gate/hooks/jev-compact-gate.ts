/**
 * Claude Code function hook: Jev decides when the session compacts.
 *
 * A thin adapter from the engine's `$` onto `src/run.ts`'s `Io`. Verdicts
 * log to ~/.claude/jev-compact-gate/<session>[.N].jsonl in every mode.
 */

import type { Register } from 'claude-code';

import type { Message } from '../src/decide.ts';
import {
  appendRow,
  buildJevRequest,
  newMemo,
  onTurn,
  parseJevResponse,
  resolveSettings,
  withTimeout,
  type LogRow,
} from '../src/run.ts';

export const register: Register = (on, options) => {
  const cfg = resolveSettings(options);
  const memo = newMemo();
  const logCursor = { chunk: 0 };

  on('turn.complete', async ($, event, next) => {
    await onTurn(
      event,
      {
        usage: async () => {
          const { context } = await $.session.usage();
          return { tokens: context.tokens, window: context.window, percent: context.percent };
        },
        messages: async () => (await $.session.messages()) as readonly Message[],
        ask: async (state, questions) => {
          const apiKey = await $.env.get('OPENROUTER_API_KEY');
          if (!apiKey) throw new Error('OPENROUTER_API_KEY is unset');
          const { url, init } = buildJevRequest(apiKey, cfg.model, state, questions);
          const response = await withTimeout($.http.fetch(url, init), cfg.timeoutMs, (ms, signal) =>
            $.clock.sleep(ms, { signal: AbortSignal.any([signal, next.signal]) }),
          );
          return parseJevResponse(response.status, response.text);
        },
        compact: async (instructions) => {
          if (next.signal.aborted) return { skip: 'turn.complete dispatch abandoned' };
          const result = await $.session.compact(instructions ? { instructions } : undefined);
          return { skip: result.skip };
        },
        log: async (row: LogRow) => {
          const home = await $.env.get('HOME');
          if (!home) return;
          await appendRow(
            { exists: (p) => $.fs.exists(p), read: (p) => $.fs.read(p), write: (p, text) => $.fs.write(p, text) },
            `${home}/.claude/jev-compact-gate`,
            await $.session.id(),
            row,
            logCursor,
          );
          if (row.acted) {
            $.ui.toast(
              `jev-compact-gate: compacting at ${Math.round((row.tokens ?? 0) / 1000)}k (${row.gate === 'ceiling' ? 'ceiling' : `seam ${row.pBoundary?.toFixed(2)} ≥ ${row.threshold?.toFixed(2)}`})`,
            );
          }
          if (row.error) $.ui.log(`jev-compact-gate: ${row.error}`);
        },
        now: () => Date.now(),
      },
      cfg,
      memo,
    ).catch((error: unknown) => {
      $.ui.log(`jev-compact-gate: skipped (${error instanceof Error ? error.message : String(error)})`);
    });
    return next(event);
  });

  // Compactions the gate did not start (native threshold, /compact) restart its turn count too.
  on('session.compact', async ($, event, next) => {
    const result = await next(event);
    if (event.agentId === undefined && event.trigger !== 'precompute' && !result.skip) {
      memo.lastCompactTurn = memo.turn;
    }
    return result;
  });
};
