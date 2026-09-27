/**
 * Claude Code function hook: Jev decides when the session compacts.
 *
 * A thin adapter from the engine's `$` onto `src/run.ts`'s `Io`. Verdicts
 * log to ~/.claude/jev-compact-gate/<session>.jsonl in every mode.
 */

import type { PluginOptions, Register } from 'claude-code';

import type { Message } from '../src/decide.ts';
import {
  buildJevRequest,
  newMemo,
  onTurn,
  parseJevResponse,
  SETTINGS,
  withTimeout,
  type LogRow,
  type Settings,
} from '../src/run.ts';

function resolveSettings(options: PluginOptions): Settings {
  const num = (key: keyof Settings): number => {
    const value = options[key];
    return typeof value === 'number' && Number.isFinite(value) ? value : (SETTINGS[key] as number);
  };
  const mode = options.mode === 'live' ? 'live' : 'shadow';
  const model = typeof options.model === 'string' && options.model ? options.model : SETTINGS.model;
  return {
    mode,
    model,
    floorTokens: num('floorTokens'),
    ceilingTokens: num('ceilingTokens'),
    boundaryMax: num('boundaryMax'),
    boundaryMin: num('boundaryMin'),
    verbatimVeto: num('verbatimVeto'),
    debugPenalty: num('debugPenalty'),
    cooldownTurns: num('cooldownTurns'),
    timeoutMs: num('timeoutMs'),
  };
}

export const register: Register = (on, options) => {
  const cfg = resolveSettings(options);
  const memo = newMemo();

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
          const path = `${home}/.claude/jev-compact-gate/${await $.session.id()}.jsonl`;
          const prior = (await $.fs.exists(path)) ? await $.fs.read(path) : '';
          await $.fs.write(path, `${prior}${JSON.stringify(row)}\n`);
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
