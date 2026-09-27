/**
 * Pure decision core for the Jev compaction gate: no I/O, no engine types.
 *
 * The hook asks `gate()` where the session sits in the token band, sends
 * `buildState()` + `QUESTIONS` to Jev inside it, and acts on `decide()`.
 */

export type ToolUse = {
  tool_use_id: string;
  tool: string;
  input: Record<string, unknown>;
  text?: string;
  isError?: true;
};

/** The subset of Claude Code's `SessionMessage` the gate reads. */
export type Message = {
  role: 'user' | 'assistant';
  text: string;
  toolUses: ToolUse[];
  toolResults?: { tool_use_id: string; text: string; isError: boolean }[];
};

export type Config = {
  floorTokens: number;
  ceilingTokens: number;
  /** P(at_boundary) required to compact at the floor. */
  boundaryMax: number;
  /** P(at_boundary) required to compact just below the ceiling. */
  boundaryMin: number;
  /** P(needs_verbatim_recent) at or above which the gate holds, whatever the boundary. */
  verbatimVeto: number;
  /** Added to the boundary threshold, weighted by P(phase = debugging). */
  debugPenalty: number;
};

export const DEFAULTS: Config = {
  floorTokens: 280_000,
  ceilingTokens: 400_000,
  boundaryMax: 0.7,
  boundaryMin: 0.3,
  verbatimVeto: 0.5,
  debugPenalty: 0.15,
};

export type Phase =
  | 'exploring'
  | 'implementing'
  | 'debugging'
  | 'verifying'
  | 'wrapping_up'
  | 'conversing';

export const QUESTIONS = {
  at_boundary: {
    type: 'noul',
    instructions: 'Has a unit of work just closed in this coding-agent session?',
    criteria: {
      true: 'The last turn completed a deliverable—a commit, passing tests, a finished answer or report, or an approved plan—and the next request is likely to start new work.',
      false:
        'Work is mid-flight: a bug is still being chased, an edit series is incomplete, tests are failing, or the assistant just asked a question whose answer depends on recent detail.',
    },
  },
  needs_verbatim_recent: {
    type: 'noul',
    instructions:
      "Would the agent's next step need exact text from recent tool output that a summary would likely lose?",
    criteria: {
      true: 'The next step depends on exact error messages, file contents, diffs, stack traces, or command output from the last few tool calls.',
      false:
        'The next step can proceed from a summary of what was done; exact recent tool output is no longer needed.',
    },
  },
  phase: {
    type: 'choice',
    instructions: 'Which phase is the session in right now?',
    criteria: {
      exploring: 'Reading code or docs to understand a problem.',
      implementing: 'Writing or editing code toward a known design.',
      debugging: 'Chasing a failure whose cause is not yet known.',
      verifying: 'Running tests or checks on finished work.',
      wrapping_up: 'Committing, documenting, or summarizing finished work.',
      conversing: 'Discussing ideas with the user; no active code work.',
    } satisfies Record<Phase, string>,
  },
} as const;

export type Gate =
  | { action: 'skip'; reason: 'no-usage' | 'small-window' | 'below-floor' }
  | { action: 'ceiling' }
  | { action: 'ask'; urgency: number };

/** Where the session sits relative to the band; `urgency` runs 0 at the floor to 1 at the ceiling. */
export function gate(tokens: number | undefined, window: number, cfg: Config): Gate {
  if (tokens === undefined) return { action: 'skip', reason: 'no-usage' };
  if (window < cfg.ceilingTokens) return { action: 'skip', reason: 'small-window' };
  if (tokens < cfg.floorTokens) return { action: 'skip', reason: 'below-floor' };
  if (tokens >= cfg.ceilingTokens) return { action: 'ceiling' };
  return { action: 'ask', urgency: (tokens - cfg.floorTokens) / (cfg.ceilingTokens - cfg.floorTokens) };
}

/**
 * The P(at_boundary) a compaction must reach: strict near the floor, lenient
 * near the ceiling, raised in proportion to how likely the session is debugging.
 */
export function threshold(urgency: number, pDebugging: number, cfg: Config): number {
  const base = cfg.boundaryMax - (cfg.boundaryMax - cfg.boundaryMin) * urgency;
  return Math.min(1, base + cfg.debugPenalty * pDebugging);
}

export type Verdict = {
  action: 'compact' | 'hold';
  reason: 'seam' | 'needs-verbatim' | 'mid-work' | 'malformed';
  pBoundary?: number;
  pVerbatim?: number;
  phase?: string;
  pDebugging?: number;
  threshold?: number;
};

const probability = (value: unknown): number | undefined =>
  typeof value === 'number' && value >= 0 && value <= 1 ? value : undefined;

function field(answers: unknown, key: string, prop: string): unknown {
  if (!answers || typeof answers !== 'object') return undefined;
  const answer = (answers as Record<string, unknown>)[key];
  return answer && typeof answer === 'object' ? (answer as Record<string, unknown>)[prop] : undefined;
}

/**
 * P(phase = debugging) from the Choice's distribution; when the distribution
 * is absent, 1 or 0 by the chosen option. `null` when present but unreadable.
 */
function debuggingProbability(answers: unknown, phase: string): number | null {
  const probabilities = field(answers, 'phase', 'probabilities');
  if (!probabilities || typeof probabilities !== 'object') return phase === 'debugging' ? 1 : 0;
  const value = (probabilities as Record<string, unknown>).debugging;
  if (value === undefined) return phase === 'debugging' ? 1 : 0;
  return probability(value) ?? null;
}

/**
 * Turns Jev's `answers` into a verdict; anything unreadable holds.
 *
 * Needing exact recent output is a hard condition (a veto); being at a seam
 * is the preference urgency relaxes. Each Noul keeps its own threshold.
 */
export function decide(answers: unknown, urgency: number, cfg: Config): Verdict {
  const pBoundary = probability(field(answers, 'at_boundary', 'noul'));
  const pVerbatim = probability(field(answers, 'needs_verbatim_recent', 'noul'));
  const phase = field(answers, 'phase', 'choice');
  if (pBoundary === undefined || pVerbatim === undefined || typeof phase !== 'string') {
    return { action: 'hold', reason: 'malformed' };
  }
  const pDebugging = debuggingProbability(answers, phase);
  if (pDebugging === null) return { action: 'hold', reason: 'malformed' };
  const t = threshold(urgency, pDebugging, cfg);
  const judged = { pBoundary, pVerbatim, phase, pDebugging, threshold: t };
  if (pVerbatim >= cfg.verbatimVeto) return { action: 'hold', reason: 'needs-verbatim', ...judged };
  if (pBoundary < t) return { action: 'hold', reason: 'mid-work', ...judged };
  return { action: 'compact', reason: 'seam', ...judged };
}

const PROMPTS = 3;
const PROMPT_CHARS = 600;
const ANSWER_CHARS = 1500;
const TOOL_CALLS = 15;
const ARG_CHARS = 120;
const KEY_ARGS = ['command', 'file_path', 'path', 'pattern', 'url', 'query', 'description', 'prompt'];

const clip = (text: string, max: number): string =>
  text.length > max ? `${text.slice(0, max)}…` : text;

const stripReminders = (text: string): string =>
  text.replace(/<system-reminder\b[^>]*>[\s\S]*?<\/system-reminder>/g, '').trim();

const REDACTED = '[redacted]';
const SECRET_NAME = String.raw`[A-Za-z0-9_]*(?:key|token|secret|passw(?:or)?d|pwd)[A-Za-z0-9_]*`;
const SECRET_PATTERNS: [RegExp, string][] = [
  [new RegExp(String.raw`("${SECRET_NAME}"\s*:\s*)"[^"]*"`, 'gi'), `$1${REDACTED}`],
  [new RegExp(String.raw`\b(${SECRET_NAME})=("[^"]*"|'[^']*'|\S+)`, 'gi'), `$1=${REDACTED}`],
  [/\b(Bearer)\s+[A-Za-z0-9._~+/=-]+/gi, `$1 ${REDACTED}`],
  [/\bsk-[A-Za-z0-9_-]{16,}/g, REDACTED],
  [/\bgh[pousr]_[A-Za-z0-9]{20,}/g, REDACTED],
  [/\bAKIA[0-9A-Z]{16}\b/g, REDACTED],
];

/**
 * Masks credential-shaped text before the state leaves the machine: named
 * secret assignments (`*_KEY=`, `--password=`, `"token": "…"`), bearer
 * headers, and OpenAI/OpenRouter, GitHub and AWS key shapes. Best effort,
 * biased to over-redact; Jev judges work boundaries, not values.
 */
export function redact(text: string): string {
  return SECRET_PATTERNS.reduce((acc, [pattern, replacement]) => acc.replace(pattern, replacement), text);
}

/** One line per tool call: its key argument and outcome, never its output. */
export function toolLine(use: ToolUse): string {
  const key = KEY_ARGS.find((k) => typeof use.input[k] === 'string');
  const value = key ? clip(redact(String(use.input[key]).replace(/\s+/g, ' ')), ARG_CHARS) : '';
  const arg = key ? ` ${key}=${value.includes(' ') ? JSON.stringify(value) : value}` : '';
  const outcome =
    use.text === undefined
      ? 'pending'
      : use.isError
        ? `error: ${clip(redact(use.text.split('\n', 1)[0] ?? ''), ARG_CHARS)}`
        : `ok ${use.text.length}ch`;
  return `${use.tool}${arg} → ${outcome}`;
}

export type JevState = {
  recent_prompts: string[];
  last_answer: string;
  recent_activity: string[];
};

/**
 * The bounded, redacted view of the session Jev judges: recent prompts, the
 * last answer, recent tool calls. Token counts stay in code, where the band is
 * decided; they tell Jev nothing about whether work just closed.
 */
export function buildState(input: { messages: readonly Message[]; answer: string }): JevState {
  const prompts: string[] = [];
  const calls: ToolUse[] = [];
  for (const message of input.messages.toReversed()) {
    if (prompts.length === PROMPTS && calls.length === TOOL_CALLS) break;
    if (message.role === 'user' && prompts.length < PROMPTS) {
      const text = stripReminders(message.text);
      if (text) prompts.unshift(clip(redact(text), PROMPT_CHARS));
    }
    const room = TOOL_CALLS - calls.length;
    if (room > 0) calls.unshift(...(message.toolUses ?? []).slice(-room));
  }
  return {
    recent_prompts: prompts,
    last_answer: clip(redact(input.answer), ANSWER_CHARS),
    recent_activity: calls.map(toolLine),
  };
}

/** Rough token count, the chars/3.2 heuristic `hooks/precompact-handoff.py` uses. */
export function estimateTokens(value: unknown): number {
  return Math.ceil(JSON.stringify(value).length / 3.2);
}

const GOAL_CHARS = 300;

/** `/compact` instructions from what the gate knows; Jev itself writes no text. */
export function buildInstructions(recentPrompts: readonly string[], phase: string | undefined): string {
  const last = recentPrompts.at(-1);
  if (!last) return '';
  const phaseNote = phase ? ` Current phase: ${phase}.` : '';
  return `Preserve the active goal: ${clip(last, GOAL_CHARS)}.${phaseNote}`;
}
