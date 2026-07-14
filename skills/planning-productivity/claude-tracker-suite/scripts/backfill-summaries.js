#!/usr/bin/env node
/**
 * backfill-summaries.js — Generate missing session summaries via an LLM
 *
 * DISABLED BY DEFAULT: every mode that calls a model requires --enable
 * (or TRACKER_SUMMARIZER=1). --dry-run works without it (no LLM calls).
 *
 * Usage: node backfill-summaries.js --enable [--limit N] [--concurrency N]
 *        node backfill-summaries.js --enable --provider openrouter [--model <id>]
 *        node backfill-summaries.js --enable --session <id-prefix>   (force one)
 *        node backfill-summaries.js --dry-run                        (no gate needed)
 *
 * Providers:
 *   claude      (default) hermetic `claude -p --model <id>`, default model haiku
 *   openrouter  chat/completions API, default model moonshotai/kimi-k2;
 *               key from OPENROUTER_API_KEY or ~/.config/env/secrets.env
 *
 * Pulls representative text from transcript_messages (indexed by
 * index-transcripts.js), asks the model for a title and a one-sentence
 * summary that names concrete subjects, tools, and deliverables, then
 * updates sessions.summary/auto_title. sessions_fts stays in sync via
 * triggers, so backfilled summaries are immediately searchable.
 */

const os = require('os');
const path = require('path');
const { spawn } = require('child_process');
const db = require(path.join(os.homedir(), '.claude', 'lib', 'tracker-db.js'));

const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run');
const limitIdx = args.indexOf('--limit');
const limit = limitIdx !== -1 && args[limitIdx + 1] ? parseInt(args[limitIdx + 1], 10) : Infinity;
const concIdx = args.indexOf('--concurrency');
const concurrency = concIdx !== -1 && args[concIdx + 1] ? parseInt(args[concIdx + 1], 10) : 4;
const sessIdx = args.indexOf('--session');
const forceSession = sessIdx !== -1 && args[sessIdx + 1] ? args[sessIdx + 1] : null;
const enabled = args.includes('--enable') || process.env.TRACKER_SUMMARIZER === '1';
const provIdx = args.indexOf('--provider');
const provider = provIdx !== -1 && args[provIdx + 1] ? args[provIdx + 1] : 'claude';
const modelIdx = args.indexOf('--model');
const model = modelIdx !== -1 && args[modelIdx + 1] ? args[modelIdx + 1]
  : (provider === 'openrouter' ? 'moonshotai/kimi-k2' : 'haiku');

if (!['claude', 'openrouter'].includes(provider)) {
  console.error(`Unknown provider: ${provider} (expected claude or openrouter)`);
  process.exit(1);
}
if (!enabled && !dryRun) {
  console.error('Summarizer is disabled by default. Pass --enable (or set TRACKER_SUMMARIZER=1) to run, or --dry-run to preview excerpts without LLM calls.');
  process.exit(1);
}

const PROMPT_HEADER = `Summarize this Claude Code session. Name the CONCRETE subjects, tools, file types, and deliverables — the specific nouns someone would search for later (project names, commands, technologies, artifacts). Always include the destination or platform the work was FOR when stated anywhere (Twitter profile, GitHub README, a client site). Never write vague gerunds like "adjusted the image"; write "composited Subquadratic logo into Twitter background porthole using ImageMagick".

Reply in EXACTLY this format (no other text):
TITLE: <3-6 word title>
SUMMARY: <one sentence, max 35 words, starting with a verb>

Session excerpts:
`;

/** Build a compact evidence block: first prompt + sampled user asks + final assistant text. */
function buildExcerpts(sessionId) {
  const d = db.ensureTranscripts(); // transcript tables live in the sidecar DB
  // Sample from the whole session, not just the opening — the detail a user
  // later remembers (destination, final pivot) often lands mid-conversation
  const head = d.prepare(
    "SELECT seq, text FROM transcript_messages WHERE session_id = ? AND role = 'user' ORDER BY seq LIMIT 8"
  ).all(sessionId);
  const tail = d.prepare(
    "SELECT seq, text FROM transcript_messages WHERE session_id = ? AND role = 'user' ORDER BY seq DESC LIMIT 4"
  ).all(sessionId).reverse();
  const seen = new Set(head.map(r => r.seq));
  const users = [...head, ...tail.filter(r => !seen.has(r.seq))].map(r => r.text);
  const lastAssistant = d.prepare(
    "SELECT text FROM transcript_messages WHERE session_id = ? AND role = 'assistant' ORDER BY seq DESC LIMIT 1"
  ).get(sessionId);

  const parts = [];
  let budget = 3500;
  for (const t of users) {
    const chunk = t.slice(0, 400);
    if (budget - chunk.length < 0) break;
    const clean = chunk.replace(/\s+/g, ' ').trim();
    if (clean) { parts.push('USER: ' + clean); budget -= chunk.length; }
  }
  // Assistant-only sessions (continuation stubs, agent transcripts): without
  // this fallback the prompt carries no content and haiku replies "I'm ready
  // to help!" — unparseable, deterministically, forever
  if (parts.length === 0) {
    const assistants = d.prepare(
      "SELECT text FROM transcript_messages WHERE session_id = ? AND role = 'assistant' ORDER BY seq LIMIT 6"
    ).all(sessionId);
    for (const a of assistants) {
      const clean = a.text.slice(0, 400).replace(/\s+/g, ' ').trim();
      if (clean && budget - clean.length > 0) { parts.push('ASSISTANT: ' + clean); budget -= clean.length; }
    }
  }
  if (lastAssistant && budget > 300) {
    const clean = lastAssistant.text.slice(0, 500).replace(/\s+/g, ' ').trim();
    if (clean) parts.push('FINAL ASSISTANT: ' + clean);
  }
  const excerpt = parts.join('\n');
  // Too little signal to summarize honestly — let the caller skip it
  return excerpt.length >= 40 ? excerpt : '';
}

let lastCallError = '';

/** OPENROUTER_API_KEY from the environment, else ~/.config/env/secrets.env. */
function loadOpenRouterKey() {
  if (process.env.OPENROUTER_API_KEY) return process.env.OPENROUTER_API_KEY;
  try {
    const fs = require('fs');
    const secrets = fs.readFileSync(path.join(os.homedir(), '.config', 'env', 'secrets.env'), 'utf8');
    const m = secrets.match(/^(?:export\s+)?OPENROUTER_API_KEY=["']?([^"'\n]+)/m);
    if (m) return m[1].trim();
  } catch { /* fall through */ }
  return null;
}

async function callOpenRouter(prompt, modelId) {
  const key = loadOpenRouterKey();
  if (!key) {
    lastCallError = 'OPENROUTER_API_KEY not found in env or ~/.config/env/secrets.env';
    return null;
  }
  try {
    const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: modelId,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 200,
        temperature: 0.3,
      }),
      signal: AbortSignal.timeout(60000),
    });
    if (!res.ok) {
      lastCallError = `openrouter HTTP ${res.status}: ${(await res.text()).slice(0, 200)}`;
      return null;
    }
    const data = await res.json();
    const text = data.choices && data.choices[0] && data.choices[0].message
      && data.choices[0].message.content;
    if (!text) {
      lastCallError = `openrouter empty reply: ${JSON.stringify(data).slice(0, 200)}`;
      return null;
    }
    return text.trim();
  } catch (e) {
    lastCallError = e.message;
    return null;
  }
}

function callClaude(prompt, modelId) {
  return new Promise((resolve) => {
    // Hermetic invocation — this ran non-hermetically once and (a) fired the
    // user's Stop-hook notification per call (macOS spam storm), (b) persisted
    // 160 synthetic sessions that poisoned the search corpus:
    //   --safe-mode              skips all hooks and customizations
    //   --no-session-persistence no synthetic session transcripts
    //   env strip                exhausted ANTHROPIC_API_KEY would override the
    //                            claude.ai login; CLAUDECODE/CLAUDE_CODE_* make
    //                            the CLI detect a nested session and bail
    const env = { ...process.env };
    delete env.ANTHROPIC_API_KEY;
    delete env.ANTHROPIC_AUTH_TOKEN;
    for (const k of Object.keys(env)) {
      if (k === 'CLAUDECODE' || k.startsWith('CLAUDE_CODE_')) delete env[k];
    }
    const child = spawn('claude',
      ['-p', prompt, '--model', modelId, '--safe-mode', '--no-session-persistence'],
      { env, timeout: 60000, stdio: ['ignore', 'pipe', 'pipe'] });
    let out = '', err = '';
    child.stdout.on('data', d => { out += d; });
    child.stderr.on('data', d => { err += d; });
    child.on('close', code => {
      if (code === 0) return resolve(out.trim());
      lastCallError = (err || `exit code ${code}`).trim().slice(0, 200);
      resolve(null);
    });
    child.on('error', e => { lastCallError = e.message; resolve(null); });
  });
}

function parseReply(reply) {
  if (!reply) return null;
  const title = (reply.match(/^TITLE:\s*(.+)$/m) || [])[1];
  const summary = (reply.match(/^SUMMARY:\s*(.+)$/m) || [])[1];
  if (!summary) return null;
  return { title: (title || '').trim().slice(0, 80), summary: summary.trim().slice(0, 250) };
}

async function main() {
  const d = db.ensureTranscripts(); // transcript tables live in the sidecar DB

  let targets;
  if (forceSession) {
    targets = d.prepare(
      "SELECT session_id FROM sessions WHERE session_id LIKE ? OR short_id = ?"
    ).all(`${forceSession}%`, forceSession);
  } else {
    targets = d.prepare(`
      SELECT s.session_id FROM sessions s
      JOIN transcript_index_state st ON st.session_id = s.session_id
      WHERE (s.summary IS NULL OR s.summary = '') AND st.message_count > 0
      ORDER BY s.modified_at DESC
    `).all();
  }
  targets = targets.slice(0, limit === Infinity ? targets.length : limit);
  console.log(`${targets.length} session(s) to summarize via ${provider}/${model} (concurrency ${concurrency}${dryRun ? ', dry-run' : ''})`);

  const updateStmt = d.prepare(`
    UPDATE sessions SET
      summary = @summary,
      auto_title = COALESCE(NULLIF(auto_title, ''), @title)
    WHERE session_id = @session_id
  `);

  let done = 0, failed = 0;
  const queue = [...targets];

  async function worker() {
    while (queue.length > 0) {
      const { session_id } = queue.shift();
      const excerpts = buildExcerpts(session_id);
      if (!excerpts) { failed++; continue; }
      if (dryRun) {
        console.log(`--- ${session_id.slice(0, 8)}\n${excerpts.slice(0, 300)}\n`);
        done++;
        continue;
      }
      const reply = provider === 'openrouter'
        ? await callOpenRouter(PROMPT_HEADER + excerpts, model)
        : await callClaude(PROMPT_HEADER + excerpts, model);
      const parsed = parseReply(reply);
      if (!parsed) {
        failed++;
        console.log(`  ✗ ${session_id.slice(0, 8)} — ` +
          (reply === null ? `call failed: ${lastCallError || 'unknown'}` : 'unparseable reply'));
        continue;
      }
      const hadTitle = d.prepare('SELECT auto_title FROM sessions WHERE session_id = ?').get(session_id);
      updateStmt.run({ session_id, summary: parsed.summary, title: parsed.title || null });
      // Provenance: model-written titles are erasable by source — the lesson
      // of the 2026-07-13 haiku purge, which required registry archaeology
      if (parsed.title && (!hadTitle || !hadTitle.auto_title)) {
        db.insertTitleEvent({ sessionId: session_id, title: parsed.title, source: 'summarizer',
          observedIn: `backfill:${provider}/${model}`, firstSeenSeq: 0 });
      }
      done++;
      if (done % 25 === 0) console.log(`  ${done}/${targets.length} …`);
    }
  }

  await Promise.all(Array.from({ length: Math.min(concurrency, targets.length) }, worker));

  const cov = d.prepare("SELECT COUNT(*) t, SUM(CASE WHEN summary IS NOT NULL AND summary != '' THEN 1 ELSE 0 END) s FROM sessions").get();
  console.log(`Done: ${done} summarized, ${failed} failed. Coverage: ${cov.s}/${cov.t} (${Math.round(100 * cov.s / cov.t)}%).`);
  db.close();
}

main().catch(err => { console.error(err); process.exit(1); });
