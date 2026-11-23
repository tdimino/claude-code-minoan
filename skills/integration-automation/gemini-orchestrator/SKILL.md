---
name: gemini-orchestrator
description: "This skill should be used to delegate a bounded task to a Gemini model (Gemini 4 Neon, Hydrogen, Carbon, Argon, or Flash) by one of two routes: the Antigravity CLI (`agy`), where the delegate reads the working folder itself in a sandbox on the plan's quota, or one direct OpenRouter call with no agent harness. Covers a second model family's review, adjudication, debugging or research over a folder, code built from a spec, whole-corpus reads in a 1M-token window, PDF and image reading, and structured extraction. States the quota or quotes the cost before sending and checks quoted citations afterwards. Triggers on 'delegate to Gemini', 'ask Gemini', 'Antigravity', 'agy', 'have Neon read', 'Gemini Hydrogen', 'have Gemini weigh this', 'second opinion from Gemini', 'send this to OpenRouter'."
argument-hint: "<profile> <task> [--direct] [--model neon|hydrogen|carbon|argon|flash]"
---

# Gemini Orchestrator

Hand one bounded task to a Gemini model. There are two routes, and the profile and the folder decide which one a call takes:

- **`agy` (the default where a profile has it).** The Antigravity CLI runs the persona as an agent in the current folder. It opens files and runs shell commands itself, in a sandbox with no network and no write access (`builder` alone may write). It draws on the Antigravity plan's quota, not dollars. Every file in the folder that is not withheld can reach Google.
- **Direct (`--direct`).** One OpenRouter call. The delegate has no shell, no file access and no tools: it sees the packed files and nothing else, and the call is billed in dollars.

```
G=~/.claude/skills/gemini-orchestrator/scripts/gemini_exec.py
uv run $G estimate <profile> "<brief>" [--direct] [--context <paths>]   # what would run and what is withheld; nothing sent
uv run $G run      <profile> "<brief>" [--model neon] [--reasoning high]                # agy, from the folder to work in
uv run $G run      <profile> "<brief>" --direct --context <paths> [--attach <pdf|image>] [--approved-usd N]
uv run $G models | spend | failures | verify <output.md>
```

A folder listed under `direct_only_paths` in `config.json` (the Linear A projects), and any folder above or below one, never goes through `agy`: a profile with both routes falls back to direct there, and an `agy`-only profile is refused.

## When to delegate, and when not to

Delegate when the user asks for Gemini or a second model, and the task is one of these:

- **A large read.** A question over more material than is sensible to read directly: dozens of files, a whole folder, a long corpus. One request holds about a million tokens.
- **An independent judgement.** A review or an adjudication from a different model family, alongside or instead of `codex-orchestrator`.
- **A PDF or an image.** Sent natively with `--attach`.
- **Structured extraction** from text, with `--schema`.
- **Code from a spec**, when the user wants Gemini to build it (`builder`).
- **A question that needs looking around a folder** or running its tests (`researcher`, `debugger`, `reviewer` on the `agy` route).

Work directly instead when the task takes a few minutes or needs the network. Do not delegate uninvited: each call spends the user's quota or money and sends their files to a third party.

## Procedure on the `agy` route

1. **Choose the profile** from the table below, and `cd` to the narrowest folder that holds the work: the delegate can read everything under it that is not withheld, and a folder of more than 20,000 files is refused.
2. **Run `estimate`.** It lists each withheld file with the reason (a credentials file by name, a file holding a denied address or a secret pattern) and the number of deny rules. Nothing is sent.
3. **Say before running that it draws on the plan's quota**, with the model and effort. No go is needed for a quota call. If `useG1Credits` is on in the Antigravity settings the run is refused (exit 3) until the user gives a go and you pass `--approved-credits`, because a run past the quota is then charged.
4. **Mind the quota.** One review at high effort took about a quarter of the week's Gemini quota and most of a five-hour window. `agy -p /usage` shows both, free of charge, but lags a run by some minutes. A run refused for quota exits 1 with the reset time and is not retried.
5. **Run it** from that folder, in the background for anything at high effort: a review ran ten minutes with its first words at nine and a half. Limits: 20 minutes in all, 5 minutes of silence.
6. **Read the trailer before the answer**: `status`, `served`, `steps`, `files_read`, `refused` (reads the deny rules stopped), `denied`, `egress`, `changed` (write runs), `citations`. Beside the output are a manifest (files read, commands run, deny rules) and the raw stream.
7. **Check the answer** (below), then report it as Gemini's reading.

`builder` is the one profile that writes. It needs a git repository with no uncommitted edits to tracked files (exit 2 otherwise). It can edit tracked files and create new ones. Write-denied: files git ignores or does not track, `.git`, withheld files, a repository recorded inside this one (a submodule), and the files that steer an agent or a shell (`.claude`, `.agents`, `.gemini`, `AGENTS.md`, `GEMINI.md`, `CLAUDE.md`, `.envrc`). Afterwards the launcher runs `git status --ignored` itself and lists the changed files, also when the run failed half-way or was interrupted. Three results make the run exit 1 even with a good answer: `control files changed` (read those files before anything else runs in the folder), a protected file `missing` or `altered`, and `changed=unknown` (git failed; run `git status --ignored` yourself). A new file inside a folder git already ignored is not listed. Read the diff before running the tests: the tests run outside the sandbox, and the delegate's own test report is testimony.

## Procedure on the direct route

1. **Choose the profile** from the table below.
2. **Choose the pack.** Pass every file the delegate needs with `--context` (files, folders, globs; `.gitignore` is honoured). It cannot fetch anything else. Read `references/briefing.md` before the first delegation in a session: it covers what to pack and how to write a brief for a reader with no context.
3. **Run `estimate` and tell the user the ceiling** in one line, with the model and effort. The ceiling is input plus the whole of `max_tokens` at the output price.
4. **Respect the gate.** In a project with `.claude/rules/paid-api-spend.md` the gate is $0: send only after the user answers that number with a go, then pass it as `--approved-usd`. Elsewhere, a call the user asked for goes ahead under the gate ($0.50); above it, wait for a go on the number. A Neon call at medium or above has a ceiling over the gate on its allowance alone. Never raise `--approved-usd` beyond what the user agreed.
5. **Run it** in the foreground. The answer is printed and saved under `.subdaimon-output/`, with a trailer naming the served model, provider, tokens, cost and citation count.
6. **Read the trailer before the answer.**
7. **Check the answer** (below), then report it to the user as Gemini's reading, with the cost.

Exit codes on both routes: 0 done, 1 API, `agy` or quota failure, 2 usage, 3 cost or credits gate, 4 empty, truncated or stopped at a permission request, 5 egress, 6 served by a different model.

## Profiles

| Profile | Routes | Use for | Default model, effort | Returns |
|---|---|---|---|---|
| `default` | agy | a task with no special role | neon, medium | whatever the brief asks |
| `researcher` | agy | a question answered by looking through a folder | neon, medium | answer, cited evidence, how it was found |
| `debugger` | agy | the root cause of a failure, with a reproduction | neon, high | cause, reproduction, proposed fix (not applied) |
| `reviewer` | agy, direct | defects in code or a document | neon, high | ranked findings, each cited |
| `adjudicator` | agy, direct | rival hypotheses, ambiguous evidence | neon, high | ranking, evidence matrix, decision |
| `architect` | agy, direct | a design from existing code | neon, high | one design, build order, rejected alternatives |
| `builder` | agy, direct | code from a spec | neon, medium | agy: files written in the folder; direct: whole files as text |
| `chat` | agy, direct | open questions | hydrogen, low | a direct answer |
| `reader` | direct | a question over a large pack | neon, medium | answer, cited evidence, coverage |
| `extractor` | direct | records to JSON | hydrogen, low | JSON only (pair with `--schema`) |
| `seer` | direct | PDFs and images | neon, medium | transcription with doubt marked in place |
| `raw` | direct | no persona | neon, medium | whatever the brief asks |

Where a profile has both routes, `default_route` in `config.json` decides (shipped: `agy`); `--direct` or `--via agy|openrouter` overrides it. `--attach`, `--schema`, `--session`, `--approved-usd` and the token options belong to the direct route and are refused on `agy`. Every `agy` profile runs as a persona installed under `~/.gemini/config/agents/orch-<profile>/`; none runs as `agy`'s stock agent, which can search the web past the sandbox.

Override with `--model` and `--reasoning`. `uv run $G models` shows today's prices and which efforts each model accepts (`xhigh` exists on Neon and Hydrogen only). Hydrogen costs half of Neon; choose it for bulk and simple reads. Model defaults are provisional: no comparison between the Gemini 4 models has been run yet.

## Checking the answer

The delegate's answer is testimony, not a finding.

- **Citations.** Personas cite as `[path:L12-L14] "exact words"`. The run compares every quotation with the packed file (on `agy`, with the cited file as it stands after the run) and reports `citations=verified/total` in the trailer, listing each failure: `not_found` (the words are not in the file), `misplaced` (in the file, not at those lines), `unknown_file`, `out_of_range`, `file_changed`. Treat a `not_found` as a fabricated quotation and discount the claim that rests on it. `uv run $G verify <output.md>` repeats the check.
- **Reasoning.** The script checks that the words exist, not that they support the claim. Open the cited lines for any finding that matters before repeating it.
- **`MISSING:`** If the answer ends with a `MISSING:` list, decide which of those files may be sent, and run again with `--session <file>` on both calls so the delegate keeps its first reading. This is the only loop: the orchestrator decides what leaves the machine.
- **Independence.** When Gemini is one of several judges, keep its brief free of the others' conclusions and of your own, and settle a split by the project's tie-break practice.
- **Images.** A `seer` reading is one witness. Project rules on who confirms an image reading still apply.
- **`builder` output.** On the direct route it is unrun code: apply the files with Write or Edit, then run the project's tests. On `agy` the files are already written: read `git diff`, run the tests, and undo with git if the work is wrong.
- **A zero citation count on `agy` is not a clean bill.** A Hydrogen review wrote its quotations inside backticks and the checker counted none of them. Open the cited lines yourself.

## Gotchas on the `agy` route

- **An egress finding (exit 5) cannot be unsent.** After the run the launcher scans what the machine showed the model, each tool output and each file read, for denied addresses and secret patterns. A finding means that material reached Google: tell the user at once, with the file and line.
- **What is withheld, and what is not.** Withheld: credentials files by name, files holding a denied address or a secret pattern, files too large to scan, `.git`, earlier outputs under `.subdaimon-output`, `~/.gitconfig` and the configs it includes. In dependency folders such as `node_modules` and virtual environments only credentials files by name are withheld; their contents are not scanned and stay readable so tests can run. An output written elsewhere with `--out` is scanned like any other file.
- **Refused before the run (exit 2 or 5).** `agy` loads some files by itself, past the deny rules: an agent folder `.agents/agents/orch-*` in or above the folder stops the run (exit 2), and `AGENTS.md`, `GEMINI.md` and `~/.gemini/GEMINI.md` are scanned like the brief (exit 5 on a finding). A withheld or untracked path whose name holds `()[]*?` or a line break also stops the run (exit 2): how `agy` reads such a rule is untested.
- **Stopping a run.** Ctrl-C, SIGTERM and SIGHUP end `agy` and its helpers; the launcher still writes the output, the ledger line and, for `builder`, the list of changed files, and exits 1. SIGKILL leaves `agy` running to its own time limit.
- **A request outside the limits ends the run with no answer (exit 4).** A read outside the folder or a write by a read-only persona is not answered with an error the model can recover from: `agy` stops. Narrow the brief, or name the files with `--context` (on this route the paths are hints in the prompt, not a pack). Not retried.
- **`git` does not run in the sandbox**, so a delegate cannot read history or blame. Give it what it needs from git in the brief.
- **The quota figure lags.** A reading taken straight after a run understated it by twenty points of the week. Read `/usage` before a run, not after, to decide whether there is room.
- **Telemetry.** Whether Antigravity's telemetry is on is a setting in the `agy` TUI (`/config`). The Linear A folders stay direct-only regardless.

## Gotchas on the direct route

- **Reasoning can eat the whole budget.** On Gemini 4 an effort is a level, not a share: reasoning is billed as output and shares `max_tokens` with the answer. A budget that is too small returns nothing at full price (exit 4), and nothing caps reasoning. The script allows 8,000 (low), 32,000 (medium), 48,000 (high) and 64,000 (xhigh) tokens on top of the answer; an unused allowance costs nothing, so the ceiling is higher than the likely cost. Reasoning is mandatory; `--reasoning none` is rejected.
- **Do not send a many-file cross-check as one call, to any model.** Asked to check seven source files against a specification, Neon spent 24,000, 24,000 and 56,000 reasoning tokens at medium and at high, and Hydrogen 56,000 at high, and none answered. Split the work: one file, or one question, against the specification per call.
- **Exit 4 is not retried, and a bigger budget is the last remedy.** After an empty answer, narrow the pack or the brief before raising `--reasoning-tokens`. A second call is a new spend and needs the user's go on its own number.
- **Exit 1 mid-stream is not retried either, and is usually not the user's network.** Every failed call is recorded in `~/.claude/data/gemini-orchestrator/failures.jsonl` with its timings and OpenRouter's own record of the charge; `uv run $G failures` lists them. Read that entry before naming a cause. Neon reasons at 80 to 125 tokens a second and the stream carries only keep-alives meanwhile; calls at high have ended without an answer between 6 and 7 minutes in, so one whose reasoning may pass about five minutes is at risk. A failed call with no record at OpenRouter was most likely not billed. `--stream-reasoning` makes the reasoning text flow (timed, never kept) at the same price; whether it prevents the cut-off is not established. The measurements are in `references/openrouter-api.md`.
- **HTTP 402 with calls in flight costs nothing.** OpenRouter reserves each running call's ceiling against the balance, so a second call sent while others run can be refused although credits remain. `uv run $G spend` shows the balance; wait for the running calls, then send again under the same go.
- **The egress guard refuses** a request holding an API key, a credentials file or a denied email address, naming the file and line (exit 5). Remove the file, or use `--redact` for addresses. `--allow <path>` exempts one file from the secret patterns after a false alarm; it never exempts addresses.
- **Tokens are not characters ÷ 4.** JSON and pointed Hebrew run about 2 bytes per token, English prose about 3. Trust `estimate`, not a guess.
- **PDFs** cost about 1,000 tokens a page. A PNG with a transparent background arrives black: flatten it onto white first. Audio and video are not supported yet.
- **No caching was observed**, so a second call over the same pack costs the same as the first.
- **Both Google routes serve requests** (Vertex and AI Studio) under `data_collection: "deny"`. Pass `--zdr` only if the user asks; it may leave no endpoint.
- **Many items in a loop** is not built. For more than a handful of calls, stop and quote the whole job first.

## References

- `references/briefing.md` — packing and briefing a delegate that has no tools; the second round; reading results.
- `references/openrouter-api.md` — request shapes and what the 2026-11-20 pilot measured.
- `references/antigravity-route.md` — how an `agy` run is confined, what the live probes of 2026-11-22 showed, and what is still untested.
- `README.md` — options, configuration, tests.
