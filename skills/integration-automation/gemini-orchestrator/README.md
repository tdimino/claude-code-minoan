# Gemini Orchestrator

> Last updated: 2026-11-20 | Status: client, packer, CLI, eight personas and citation checking built; piloted live on the `raw` profile only | Models: Gemini 4 Neon, Hydrogen, Carbon, Argon, Gemini 3.8 Flash, or any OpenRouter id

Hand one bounded task to a Gemini model with a single call to OpenRouter. There is no agent CLI in between: the
model has no shell, no file access and no tools. It sees what the request carries and nothing else.

```
Claude Code (chooses the files, writes the brief, checks the answer)
    ↓
gemini_exec.py   pack → egress guard → quote → cost gate → send → check → output + ledger
    ↓
openrouter.ai/api/v1/chat/completions
    ↓
Gemini 4 (reads the pack, answers once)
```

## How it differs from codex-orchestrator

| | codex-orchestrator | gemini-orchestrator |
|---|---|---|
| Delegate | Codex CLI, with a shell | One chat completion, no tools |
| Finds its material | By exploring the repository | Receives a pack Claude chose |
| Billing | Codex subscription or OpenAI API | OpenRouter credits, quoted before sending |
| Good for | Work that needs running code or writing files | Large reads (1M-token window), a second model family's judgement, PDFs and images, many small identical items |

## Prerequisites

- `OPENROUTER_API_KEY` in the environment or in `~/.config/env/secrets.env`. An ordinary inference key; a
  management key cannot run models.
- [uv](https://docs.astral.sh/uv/). The scripts use the Python standard library only.

## Use

```bash
G=~/.claude/skills/gemini-orchestrator/scripts/gemini_exec.py

uv run $G models                                    # today's ids, prices and efforts
uv run $G estimate raw "<brief>" --context src/     # the quote; nothing is sent
uv run $G run raw "<brief>" --context src/ docs/spec.md --model neon --reasoning high
uv run $G run raw "Transcribe this page." --attach scan.pdf --model hydrogen
uv run $G run reviewer "<brief>" --context src/auth/ tests/ docs/session.md
uv run $G verify .subdaimon-output/gemini-reviewer-….md   # re-check the answer's quotations
uv run $G spend                                     # totals from the ledger
uv run $G failures                                  # the last failed calls, with timings and charges
```

Aliases: `neon`, `hydrogen`, `carbon`, `argon`, `flash`.

## Profiles

Each profile is a persona in `agents/`, written for a model with no tools and sent as the system message after a
shared preamble (`agents/_shared.md`): use only what is in the request, list what is missing under `MISSING:`
instead of guessing, and cite as `[path:L12-L14] "exact words"`.

| Profile | Use for | Default | Returns |
|---|---|---|---|
| `reader` | a question over a large pack | neon, medium | answer, cited evidence, coverage |
| `reviewer` | defects in code or a document | neon, high | ranked findings, each cited |
| `adjudicator` | rival hypotheses, ambiguous evidence | neon, high | ranking, evidence matrix, decision |
| `architect` | a design from existing code | neon, high | one design, build order, rejected alternatives |
| `builder` | code from a spec | neon, medium | whole files as text |
| `extractor` | records to JSON | hydrogen, low | JSON only |
| `seer` | PDFs and images | neon, medium | transcription with doubt marked in place |
| `chat` | open questions | hydrogen, low | a direct answer |
| `raw` | no persona | neon, medium | whatever the brief asks |

## Citation check

After every run, each quotation in the answer is compared with the packed file it names, after Unicode (NFC/NFD)
and whitespace normalisation. The trailer reports `citations=verified/total`, and each failure is listed:
`not_found` (the words are not in the file), `misplaced` (in the file, at other lines), `unknown_file`,
`out_of_range`, `file_changed`. The check shows the words exist; whether they support the claim is for the reader.

| Option | Meaning |
|---|---|
| `--context PATH ...` | Files, folders or globs to pack. Lines are numbered; `.gitignore` is honoured. |
| `--attach FILE ...` | Images and PDFs, sent natively. |
| `--model`, `--reasoning` | Checked against the model's own effort list before anything is sent. |
| `--answer-tokens`, `--reasoning-tokens` | The answer's size and the allowance for reasoning. Together they are `max_tokens`. |
| `--approved-usd N` | The ceiling agreed for this call. Required above the gate. |
| `--schema FILE` | Strict JSON-schema output. |
| `--session FILE` | Carries the conversation to a second call. |
| `--redact` | Replaces denied email addresses with `[email]`. |
| `--zdr` | Zero-data-retention endpoints only. |
| `--stream-reasoning` | Has the reasoning text streamed while the model thinks; it is timed and counted, never kept. Same price. |
| `--out FILE`, `--quiet` | Where the answer goes; print only the trailer. |

## Safeguards

- **Cost gate.** Each call is quoted at its ceiling: estimated input plus the whole of `max_tokens` at the output
  price. Above the gate ($0.50 by default) the call is refused without `--approved-usd`. In a project that has
  `.claude/rules/paid-api-spend.md`, the gate is $0. A daily ceiling ($10) stops everything.
- **Egress guard.** A request holding an API key, a private key, a credentials file or a denied email address is
  refused, with the file and line named. Denied addresses are read from `~/.claude/hooks/block-email-egress.py`,
  from `git config user.email` and from `egress_denylist` in `config.json`.
- **Privacy.** Every request sets `data_collection: "deny"`. The trailer names the provider that served it.
- **Checks on the reply.** An empty or truncated answer, a broken stream and a reply from a different model each
  have their own exit code. A failed call is never retried once text or cost may have been incurred.
- **Ledger.** Every call sent is recorded with its cost and duration in
  `~/.claude/data/gemini-orchestrator/ledger.jsonl`.
- **Failure log.** Every call that was sent and returned no usable answer adds a record to `failures.jsonl` beside
  the ledger: the stage (before, during or after the stream), the error, seconds to the first line, to the first
  answer text and to the last line, counts of keep-alives and data chunks, the usage reported, and OpenRouter's own
  record of the generation with what it charged. It holds neither the key nor the brief. `failures` lists the last
  ten; `failures --json` prints the full records.

Each answer is written to `.subdaimon-output/gemini-<profile>-<time>.md` with a trailer:

```
<!-- gemini-exec: status=ok requested=google/gemini-4-neon served=google/gemini-4-neon provider=Google effort=xhigh
     in=116 out=6427 reasoning=6329 cached=0 cost=$0.0968 finish=stop manifest=… -->
```

Exit codes: 0 done, 1 API or transport failure, 2 usage, 3 cost gate, 4 empty or truncated answer, 5 egress guard,
6 served by a different model.

## What the pilot found (2026-11-20, 13 calls, $0.73)

- Cost equals price × tokens to the cent, with no surcharge above 200,000 input tokens.
- An effort is a level, not a share of the budget. Neon at low and at high spent the entire budget reasoning and
  returned nothing; reasoning is billed as output. Give reasoning room with `--reasoning-tokens`.
- In first real use, Neon at high spent a whole 24,000-token budget reasoning over a 76,000-token review and
  returned nothing ($0.59). The allowance at high is now 48,000 tokens on top of the answer.
- JSON and pointed Hebrew run about 2 bytes per token, source code about 2.7, English prose about 3.
- A text PDF costs about 1,000 tokens a page, a page image about 1,100.
- Prompt caching was not observed.
- Later the same day, two Neon reviews at high ended with no answer after 6 m 10 s and 6 m 48 s of a stream that
  carried only keep-alives; one carried the provider's "A Timeout Occurred", and OpenRouter holds no record of it. A
  third answered after 4 m 24 s of silence (34,471 reasoning tokens, $0.99). Neon reasons at about 125 tokens a
  second, so the 48,000-token allowance at high permits more silence than the route appears to tolerate. The cause
  is not established; the failure log exists to settle it.
- One pack, seven source files checked against a plan, exhausted 24,000, 24,000 and 56,000 reasoning tokens at
  medium and high on Neon, and 56,000 on Hydrogen, and never produced an answer ($2.78 in all). A many-file
  cross-check is not one call. The allowance at medium is now 32,000.

Details and request shapes: `references/openrouter-api.md`.

## Configuration

Optional `config.json` in the skill folder:

```json
{"gate_usd": 0.50, "daily_ceiling_usd": 10.0, "egress_denylist": [], "answer_tokens": 8000,
 "profiles": {"raw": {"model": "neon", "effort": "medium"}}}
```

## Tests

```bash
cd ~/.claude/skills/gemini-orchestrator/scripts
uv run python -m unittest discover -s tests    # 70 tests against a local stub server; nothing is spent
uv run python tests/mutants.py                 # breaks 66 lines one at a time and confirms the suite fails
```

## Not built or not tried yet

- Two personas have met a live model once each: `architect` on Hydrogen answered; `reviewer` on Neon ran out of
  budget. Whether Gemini keeps the citation format is still unobserved (neither answer carried a citation).
- No comparison between Neon, Hydrogen, Carbon and Argon has been run, so the default models are provisional.
- Many-item runs and the Batch API; audio and video attachments; trigger evals for the skill's description.
