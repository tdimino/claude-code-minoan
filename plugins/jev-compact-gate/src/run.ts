/**
 * The gate's turn loop, over an injected `Io` so it runs without the engine.
 * `hooks/jev-compact-gate.ts` maps Claude Code's `$` onto `Io`.
 */

import {
  buildInstructions,
  buildState,
  decide,
  DEFAULTS,
  gate,
  QUESTIONS,
  type Config,
  type Message,
  type Verdict,
} from './decide.ts';

/** Jev's typed answers, with the usage OpenRouter reports beside them. */
export type JevReply = { answers: unknown; inputTokens?: number; cost?: number };

export type Settings = Config & {
  /** `shadow` logs every verdict and never compacts; `live` acts on them. */
  mode: 'shadow' | 'live';
  /** Main-loop turns after the gate's own compaction before it may act again. */
  cooldownTurns: number;
  timeoutMs: number;
  model: string;
};

export const SETTINGS: Settings = {
  ...DEFAULTS,
  mode: 'shadow',
  cooldownTurns: 3,
  timeoutMs: 5000,
  model: 'typesafe/jev-1.13',
};

export type TurnEvent = {
  turnId: string;
  answer: string;
  reason: string;
  isAborted: boolean;
  agentId?: string;
};

export type Io = {
  usage: () => Promise<{ tokens?: number; window: number; percent?: number }>;
  messages: () => Promise<readonly Message[]>;
  /** Resolves with Jev's `answers`; rejects on any transport or protocol fault. */
  ask: (state: unknown, questions: unknown) => Promise<JevReply>;
  compact: (instructions: string) => Promise<{ skip?: string }>;
  log: (row: LogRow) => Promise<void>;
  now: () => number;
};

/** What the gate remembers across one session's turns. */
export type Memo = {
  busy: boolean;
  turn: number;
  lastCompactTurn?: number;
  smallWindowLogged: boolean;
};

export const newMemo = (): Memo => ({ busy: false, turn: 0, smallWindowLogged: false });

export type LogRow = {
  ts: number;
  turnId: string;
  mode: Settings['mode'];
  tokens?: number;
  window: number;
  gate: 'small-window' | 'cooldown' | 'ceiling' | 'band';
  urgency?: number;
  verdict?: 'compact' | 'hold';
  pBoundary?: number;
  pVerbatim?: number;
  phase?: string;
  reason?: Verdict['reason'];
  pDebugging?: number;
  inputTokens?: number;
  cost?: number;
  threshold?: number;
  jevMs?: number;
  acted: boolean;
  skipped?: string;
  error?: string;
};

const message = (error: unknown): string => (error instanceof Error ? error.message : String(error));

/** One main-loop turn: place it in the band, ask Jev inside it, compact when the verdict and mode say so. */
export async function onTurn(event: TurnEvent, io: Io, cfg: Settings, memo: Memo): Promise<void> {
  if (event.agentId !== undefined || event.isAborted || event.reason !== 'answer' || memo.busy) return;
  memo.turn++;
  memo.busy = true;
  try {
    const usage = await io.usage();
    const g = gate(usage.tokens, usage.window, cfg);
    const base = { ts: io.now(), turnId: event.turnId, mode: cfg.mode, tokens: usage.tokens, window: usage.window };

    if (g.action === 'skip') {
      if (g.reason === 'small-window' && !memo.smallWindowLogged) {
        memo.smallWindowLogged = true;
        await io.log({ ...base, gate: 'small-window', acted: false });
      }
      return;
    }
    if (memo.lastCompactTurn !== undefined && memo.turn - memo.lastCompactTurn < cfg.cooldownTurns) {
      await io.log({ ...base, gate: 'cooldown', acted: false });
      return;
    }

    const messages = await io.messages();
    const state = buildState({
      messages,
      answer: event.answer,
      usage: { tokens: usage.tokens!, window: usage.window, percent: usage.percent },
      turnsSinceCompaction: memo.turn - (memo.lastCompactTurn ?? 0),
    });

    let row: LogRow;
    if (g.action === 'ceiling') {
      row = { ...base, gate: 'ceiling', verdict: 'compact', acted: false };
    } else {
      const started = io.now();
      try {
        const reply = await io.ask(state, QUESTIONS);
        const verdict = decide(reply.answers, g.urgency, cfg);
        row = {
          ...base,
          gate: 'band',
          urgency: g.urgency,
          verdict: verdict.action,
          reason: verdict.reason,
          pBoundary: verdict.pBoundary,
          pVerbatim: verdict.pVerbatim,
          phase: verdict.phase,
          pDebugging: verdict.pDebugging,
          threshold: verdict.threshold,
          jevMs: io.now() - started,
          inputTokens: reply.inputTokens,
          cost: reply.cost,
          acted: false,
          error: verdict.reason === 'malformed' ? 'malformed answers' : undefined,
        };
      } catch (error) {
        row = { ...base, gate: 'band', urgency: g.urgency, verdict: 'hold', jevMs: io.now() - started, acted: false, error: message(error) };
      }
    }

    if (row.verdict === 'compact' && cfg.mode === 'live') {
      try {
        const result = await io.compact(buildInstructions(state.recent_prompts, row.phase));
        if (result.skip) row.skipped = result.skip;
        else {
          row.acted = true;
          memo.lastCompactTurn = memo.turn;
        }
      } catch (error) {
        row.error = message(error);
      }
    }
    await io.log(row);
  } finally {
    memo.busy = false;
  }
}

/** OpenRouter's System One API: TypeSafe's own request and response contract, billed to the OpenRouter key. */
const SYSTEM_ONE_URL = 'https://openrouter.ai/api/v1/systemone';

export function buildJevRequest(apiKey: string, model: string, state: unknown, questions: unknown) {
  return {
    url: SYSTEM_ONE_URL,
    init: {
      method: 'POST',
      headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model, state, questions }),
    },
  };
}

export function parseJevResponse(status: number, text: string): JevReply {
  if (status < 200 || status >= 300) throw new Error(`Jev HTTP ${status}: ${text.slice(0, 200)}`);
  let body: { answers?: unknown; usage?: { input_tokens?: unknown; cost?: unknown } };
  try {
    body = JSON.parse(text);
  } catch {
    throw new Error(`Jev returned invalid JSON: ${text.slice(0, 200)}`);
  }
  if (!body || typeof body !== 'object' || !body.answers || typeof body.answers !== 'object') {
    throw new Error('Jev response has no answers');
  }
  const reply: JevReply = { answers: body.answers };
  if (typeof body.usage?.input_tokens === 'number') reply.inputTokens = body.usage.input_tokens;
  if (typeof body.usage?.cost === 'number') reply.cost = body.usage.cost;
  return reply;
}

export type Sleep = (ms: number, signal: AbortSignal) => Promise<void>;

/**
 * Rejects when `promise` has not settled within `ms`. The hook sandbox has no
 * `setTimeout`, so the wait is injected: `$.clock.sleep` there, a timer in tests.
 */
export async function withTimeout<T>(promise: Promise<T>, ms: number, sleep: Sleep): Promise<T> {
  const controller = new AbortController();
  const timeout = sleep(ms, controller.signal).then((): never => {
    throw new Error(`Jev timeout after ${ms}ms`);
  });
  timeout.catch(() => {});
  try {
    return await Promise.race([promise, timeout]);
  } finally {
    controller.abort();
  }
}
