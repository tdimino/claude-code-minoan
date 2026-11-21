---
name: gemini-orchestrator
description: "This skill should be used to delegate a bounded task to a Gemini model (Gemini 4 Neon, Hydrogen, Carbon, Argon, or Flash) through one direct OpenRouter call with no agent harness: whole-corpus reads in a 1M-token window, a second model family's review or adjudication, PDF and image reading, structured extraction. Quotes the cost before sending and checks quoted citations afterwards. Triggers on 'delegate to Gemini', 'ask Gemini', 'have Neon read', 'Gemini Hydrogen', 'have Gemini weigh this', 'second opinion from Gemini', 'send this to OpenRouter'."
argument-hint: "<profile> <task> [--model neon|hydrogen|carbon|argon|flash]"
---

# Gemini Orchestrator

Hand one bounded task to a Gemini model with a single OpenRouter call. The delegate has no shell, no file access and no tools: it sees the request and nothing else. The orchestrator therefore does what a harness would do: choose the files, write a brief that stands alone, and check the answer.

```
G=~/.claude/skills/gemini-orchestrator/scripts/gemini_exec.py
uv run $G estimate <profile> "<brief>" --context <paths> [--attach <pdf|image>]   # the quote; nothing sent
uv run $G run      <profile> "<brief>" --context <paths> [--model neon] [--reasoning high] [--approved-usd N]
uv run $G models | spend | failures | verify <output.md>
```

## When to delegate, and when not to

Delegate when the user asks for Gemini or a second model, and the task is one of these:

- **A large read.** A question over more material than is sensible to read directly: dozens of files, a whole folder, a long corpus. One request holds about a million tokens.
- **An independent judgement.** A review or an adjudication from a different model family, alongside or instead of `codex-orchestrator`.
- **A PDF or an image.** Sent natively with `--attach`.
- **Structured extraction** from text, with `--schema`.
- **Code returned as text**, when the user wants Gemini's draft of a file.

Work directly instead when the task takes a few minutes, or when it needs running code, exploring files nobody has identified yet, or writing to disk: the delegate can do none of those. Use `codex-orchestrator` or the Agent tool for that. Do not delegate uninvited: each call spends the user's money and sends their files to a third party.

## Procedure

1. **Choose the profile** from the table below.
2. **Choose the pack.** Pass every file the delegate needs with `--context` (files, folders, globs; `.gitignore` is honoured). It cannot fetch anything else. Read `references/briefing.md` before the first delegation in a session: it covers what to pack and how to write a brief for a reader with no context.
3. **Run `estimate` and tell the user the ceiling** in one line, with the model and effort. The ceiling is input plus the whole of `max_tokens` at the output price.
4. **Respect the gate.** In a project with `.claude/rules/paid-api-spend.md` the gate is $0: send only after the user answers that number with a go, then pass it as `--approved-usd`. Elsewhere, a call the user asked for goes ahead under the gate ($0.50); above it, wait for a go on the number. Never raise `--approved-usd` beyond what the user agreed.
5. **Run it** in the foreground. The answer is printed and saved under `.subdaimon-output/`, with a trailer naming the served model, provider, tokens, cost and citation count.
6. **Read the trailer before the answer.** Exit codes: 0 done, 1 API or transport failure, 2 usage, 3 cost gate, 4 empty or truncated, 5 egress guard, 6 served by a different model.
7. **Check the answer** (next section), then report it to the user as Gemini's reading, with the cost.

## Profiles

| Profile | Use for | Default model, effort | Returns |
|---|---|---|---|
| `reader` | a question over a large pack | neon, medium | answer, cited evidence, coverage |
| `reviewer` | defects in code or a document | neon, high | ranked findings, each cited |
| `adjudicator` | rival hypotheses, ambiguous evidence | neon, high | ranking, evidence matrix, decision |
| `architect` | a design from existing code | neon, high | one design, build order, rejected alternatives |
| `builder` | code from a spec | neon, medium | whole files under `### FILE: path` headings |
| `extractor` | records to JSON | hydrogen, low | JSON only (pair with `--schema`) |
| `seer` | PDFs and images | neon, medium | transcription with doubt marked in place |
| `chat` | open questions | hydrogen, low | a direct answer |
| `raw` | no persona | neon, medium | whatever the brief asks |

Override with `--model` and `--reasoning`. `uv run $G models` shows today's prices and which efforts each model accepts (`xhigh` exists on Neon and Hydrogen only). Hydrogen costs half of Neon; choose it for bulk and simple reads. Model defaults are provisional: no comparison between the Gemini 4 models has been run yet.

## Checking the answer

The delegate's answer is testimony, not a finding.

- **Citations.** Personas cite as `[path:L12-L14] "exact words"`. The run compares every quotation with the packed file and reports `citations=verified/total` in the trailer, listing each failure: `not_found` (the words are not in the file), `misplaced` (in the file, not at those lines), `unknown_file`, `out_of_range`, `file_changed`. Treat a `not_found` as a fabricated quotation and discount the claim that rests on it. `uv run $G verify <output.md>` repeats the check.
- **Reasoning.** The script checks that the words exist, not that they support the claim. Open the cited lines for any finding that matters before repeating it.
- **`MISSING:`** If the answer ends with a `MISSING:` list, decide which of those files may be sent, and run again with `--session <file>` on both calls so the delegate keeps its first reading. This is the only loop: the orchestrator decides what leaves the machine.
- **Independence.** When Gemini is one of several judges, keep its brief free of the others' conclusions and of your own, and settle a split by the project's tie-break practice.
- **Images.** A `seer` reading is one witness. Project rules on who confirms an image reading still apply.
- **`builder` output** is unrun code. Apply the files with Write or Edit, then run the project's tests.

## Gotchas

- **Reasoning can eat the whole budget.** On Gemini 4 an effort is a level, not a share: reasoning is billed as output and shares `max_tokens` with the answer. A budget that is too small returns nothing at full price (exit 4): Neon at high spent all of 24,000 tokens reasoning over a 76,000-token review and answered nothing, for $0.59. Nothing caps reasoning. The script now allows 8,000 (low), 16,000 (medium), 48,000 (high) and 64,000 (xhigh) on top of the answer; an unused allowance costs nothing, so the ceiling is higher than the likely cost. For cross-checking several files against a specification, or a very large pack, raise `--reasoning-tokens` further or drop to `medium`. Reasoning is mandatory; `--reasoning none` is rejected.
- **Exit 4 is not retried.** The message gives the reasoning tokens used and a doubled allowance to quote. A second call is a new spend and needs the user's go on its own number.
- **Exit 1 mid-stream is not retried either, and is usually not the user's network.** Every failed call is recorded in `~/.claude/data/gemini-orchestrator/failures.jsonl` with its timings and OpenRouter's own record of the charge; `uv run $G failures` lists them. Read that entry before naming a cause. Seen on 2026-11-20: Neon at high sends nothing but keep-alives while it reasons (about 125 tokens a second), and two calls ended at 6 m 10 s and 6 m 48 s with no answer, one with the provider's own "A Timeout Occurred"; a third answered after 4 m 24 s of silence. A call whose reasoning may pass about five minutes (some 40,000 tokens) is at risk: prefer `medium`, or a smaller pack. A failed call with no record at OpenRouter was most likely not billed.
- **The egress guard refuses** a request holding an API key, a credentials file or a denied email address, naming the file and line (exit 5). Remove the file, or use `--redact` for addresses. `--allow <path>` exempts one file from the secret patterns after a false alarm; it never exempts addresses.
- **Tokens are not characters ÷ 4.** JSON and pointed Hebrew run about 2 bytes per token, English prose about 3. Trust `estimate`, not a guess.
- **PDFs** cost about 1,000 tokens a page. A PNG with a transparent background arrives black: flatten it onto white first. Audio and video are not supported yet.
- **No caching was observed**, so a second call over the same pack costs the same as the first.
- **Both Google routes serve requests** (Vertex and AI Studio) under `data_collection: "deny"`. Pass `--zdr` only if the user asks; it may leave no endpoint.
- **Many items in a loop** is not built. For more than a handful of calls, stop and quote the whole job first.

## References

- `references/briefing.md` — packing and briefing a delegate that has no tools; the second round; reading results.
- `references/openrouter-api.md` — request shapes and what the 2026-11-20 pilot measured.
- `README.md` — options, configuration, tests.
