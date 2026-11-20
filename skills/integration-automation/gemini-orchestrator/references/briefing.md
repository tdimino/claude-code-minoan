# Briefing a delegate that has no tools

A Codex or Claude subagent can open a file it was not given. This delegate cannot. Whatever is absent from the request does not exist for it, and a capable model that is missing a file tends to describe the file it expects. Most bad results trace back to the pack or the brief, not the model.

## Choosing the pack

Pack what the answer depends on, and say what you left out.

| Task | Pack |
|---|---|
| Review a change | The changed files in full, not the diff alone; their direct callers; the tests; the convention file (`CLAUDE.md`, a style guide) the change must follow. |
| Question over a corpus | The whole folder. Do not pre-filter to the files you expect to matter: the point of the large window is that the delegate finds what you did not expect. |
| Adjudicate rival readings | The primary rows for every rival, the rules or method document, and each side's dossier. Give the rivals equal material. |
| Design a change | The modules the design touches, one existing example of the pattern to follow, and the constraints. |
| Write code | The spec, the files to change in full, one neighbouring file as a model of style, and the signatures of anything to be called. |
| Read a scan | The pages as a PDF or images with `--attach`, and in the brief the edition's sigla or transcription conventions. |

- Run `estimate` first. It shows the token count and what was left out (binary files, credentials files, anything over 2 MB).
- Over-packing costs money more than accuracy at these prices. A whole folder on Hydrogen is often cheaper than the time spent choosing.
- Data that derives from a query (a count, a join, the rows matching a pattern) should be computed locally and packed as a small file. The delegate reasons poorly over raw data it must count by eye, and counting is where reasoning tokens go.
- Never pack what may not leave the machine. The egress guard catches keys and denied addresses; it does not know what is confidential. Unpublished material of a third party, private correspondence and anything under an embargo are the orchestrator's call, and when in doubt the user's.

## Writing the brief

The brief is the `<task>` the delegate reads after the pack. Write it for someone intelligent who has never seen the project.

1. **The goal, and what the answer is for.** "Find dossiers whose Sources section lists a work the body never cites, so they can be fixed before publication."
2. **Definitions the pack does not give.** What counts as a citation; which column is the reading; what "confirmed" means here.
3. **What is already settled or ruled out**, so it is not rediscovered. For an independent judgement, leave this out (see below).
4. **What a complete answer contains**: every file accounted for, a ranked list, a decision from a fixed set.
5. **Limits**: length, the one thing not to do.

The persona already sets the output format and the citation rule. Do not repeat them; add only what is particular to this task.

Weak: "Review the auth module."

Better: "Review `src/auth/` for defects that would let a request act as another user. The session format is in `docs/session.md`. Tokens are meant to expire after 15 minutes of inactivity. Rate limiting is handled upstream and is out of scope. Report only findings a reader can confirm from the cited lines."

## Keeping an independent reading independent

When the point is a second opinion, the brief must not carry the first.

- State the rivals symmetrically, in neutral order, each in its proponent's best form.
- Leave out which one you, the user or another model prefers, and any earlier verdict.
- Ask for a ranking and for what would change it, not for confirmation.
- If the delegate's answer will be compared with Codex's or your own, write your own view down before reading its answer.

## The second round

If the answer ends with `MISSING:`, the delegate is asking for files.

```bash
uv run $G run reader "…" --context docs/ --session /path/to/session.json
# reads MISSING: src/parser.py — to confirm how the header is tokenised
uv run $G run reader "Here is the parser you asked for. Complete the answer." \
    --context src/parser.py --session /path/to/session.json
```

The session file carries the first request and answer, so the second call is billed for both again. For a large first pack, it is often cheaper to start over with the complete pack. Decide for each requested item whether it may be sent; say so in the brief if one is withheld.

## Choosing model and effort

- Hydrogen (half Neon's price): extraction, simple questions over a pack, transcription of clean pages, anything in bulk.
- Neon: review, adjudication, design, code.
- Carbon and Argon: available by alias; untried here.
- Effort `low` for lookups and extraction, `medium` for most reading, `high` for review and adjudication, `xhigh` (Neon and Hydrogen) when the task is a hard chain of reasoning and the user has agreed to the cost.
- Raise `--reasoning-tokens` when the delegate must count, cross-check many files against each other, or work over several hundred thousand tokens. In the pilot, Hydrogen at `low` used under 250 reasoning tokens for simple reads and more than 1,400 to count records in a 217,000-token file.

## Reading the result

1. Trailer first: `status`, `served`, `citations`.
2. Unverified citations next. A `not_found` quotation means the claim it supports is unsupported until you find the real passage yourself.
3. Then the answer. For anything you will repeat to the user or write into a file, open the cited lines.
4. Report with attribution and cost: "Gemini 4 Neon (high, $0.21) found three dossiers…; I confirmed two against the files; the third rests on a quotation that is not in the file."
