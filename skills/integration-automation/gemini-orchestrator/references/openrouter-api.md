# OpenRouter and Gemini 4: what was checked, and when

Facts here were read from the live API or measured in the pilot of 2026-11-20 (13 calls, $0.73). Prices, context
sizes and effort lists are not repeated here: `gemini_exec.py models` prints today's.

## Measured in the pilot

| Question | Finding |
|---|---|
| Does `usage.cost` match price × tokens? | Yes, to the cent, on all 13 calls. No surcharge above 200,000 input tokens: 217,492 input tokens on Hydrogen cost $0.3367, the flat rate. |
| Bytes per token (pack as sent, numbered lines included) | English Markdown 3.01; indented JSON 2.06 and 2.00; pointed Hebrew 2.08; JSON with transliteration 2.20. One or two samples each. |
| PDF, native engine | A three-page text PDF cost about 1,010 tokens a page. Hydrogen transcribed the heading and counted the pages correctly. |
| Image | A 612×792 PNG cost about 1,125 tokens. |
| Strict JSON schema | Held on Hydrogen. The schema is billed as input (a 206-byte schema added about 180 tokens). |
| Which provider serves? | Both Google routes, unprompted: 11 calls came back `Google` (Vertex), 2 `Google AI Studio`, with `data_collection: "deny"` set throughout. |
| Served model | Always the one requested. |

## Reasoning: an effort is a level, not a share

OpenRouter's reasoning guide says an effort gives reasoning a share of `max_tokens` (20% at low, 80% at high). On
Gemini 4 that did not hold. With a small logic puzzle on Neon:

| Effort | `max_tokens` | Reasoning tokens | Answer |
|---|---|---|---|
| low | 625 | 622 | none (`finish_reason: "length"`), $0.0097 |
| high | 2,500 | 2,497 | none, $0.0378 |
| xhigh | 10,000 | 6,329 | complete, $0.0968 |

Hydrogen at low spent 1,397 of 1,400 tokens reasoning over a 217,000-token pack and returned nothing ($0.34).

First real uses, the same day:

| Call | Input | Budget | Reasoning | Answer |
|---|---|---|---|---|
| Hydrogen, high, `architect` over 11 source files | 35,267 | 24,000 | 15,262 | complete, $0.21 |
| Neon, high, `reviewer` cross-checking 12 files against a plan | 76,592 | 24,000 | 23,997 | none, $0.59 |
| Neon, high, `reviewer`, a second project | 120,509 | 56,000 | 34,471 | complete, $0.99, first text at 4 m 24 s |
| Neon, medium, `reviewer`, the second project | 123,535 | 24,000 | 18,873 | complete, $0.73, 4 m 26 s |
| Neon, medium, `reviewer`, the first project again | 76,592 | 24,000 | 23,997 | none, $0.59, 4 m 55 s |
| Neon, high, `reviewer`, four more calls across both projects | — | 56,000–60,000 | — | no answer: the stream ended or carried "A Timeout Occurred" after 6 to 7 minutes |

So: reasoning takes what it wants up to the whole budget, it is billed at the output rate, and a budget that is too
small buys an empty reply at full price. The model list gives Gemini 4 no token-budget control
(`supports_max_tokens` is absent), so nothing caps it. `gemini_exec.py` sets `max_tokens` to the answer plus an
allowance per effort: low 8,000, medium 32,000, high 48,000, xhigh 64,000 (high tripled and medium doubled after the
failed reviews). How much Neon wanted for the first project's review is unknown, only that 24,000 was not enough at
either effort. Simple reads at low on Hydrogen used 85 to 240 reasoning tokens.

One more call on the first project's pack, at high with 56,000 tokens and `--stream-reasoning`, spent all 56,000
reasoning (55,997) in 6 m 24 s and answered nothing ($1.07). That pack, seven source files checked against a plan,
has now exhausted 24,000, 24,000 and 56,000: the remedy is a narrower task, not a larger budget. The stream stayed
open to its end through Vertex, with 92 reasoning chunks and a longest gap of 173 s between chunks, so streamed
reasoning still leaves minutes of silence, and the call neither confirms nor rules out that it prevents the cut-off
below.

A second limit sits above the budget: time. Neon reasons at roughly 80 to 125 tokens a second and, with reasoning
excluded, the stream carries only keep-alives until the answer starts. Of five reviews at high, one answered; the
other four ended without an answer between 6 and 7 minutes in. `failures.jsonl` records each with its timings.

## Input estimates

The quote counts each packed file by its own content class, in bytes per token: prose 2.9, source code 2.5, indented
JSON and tables 1.95, text over 5% non-ASCII 2.0, plus a 20% margin. Source code measured 2.66 (JavaScript) and 2.80
(Python) in the two calls above. Before code had its own class, and with the whole pack classed as one text, the
failed review was quoted at 134,020 input tokens and used 76,592.

## Caching: not observed

Two identical 17,000-token packs marked with `cache_control`, sent three seconds apart to the same provider, both
reported `cached_tokens: 0` and cost the same. Until a later test shows a cache read, plan costs as if there is no
caching. `--cache` stays available for that test.

## Request shapes that are in use

```json
{
  "model": "google/gemini-4-neon",
  "messages": [{"role": "system", "content": "<persona>"},
               {"role": "user", "content": "<context_pack>…</context_pack>\n\n<task>…</task>"}],
  "max_tokens": 24000,
  "stream": true,
  "reasoning": {"effort": "high", "exclude": true},
  "provider": {"data_collection": "deny", "require_parameters": true}
}
```

- PDF: a content part `{"type": "file", "file": {"filename": "…", "file_data": "data:application/pdf;base64,…"}}`
  with `"plugins": [{"id": "file-parser", "pdf": {"engine": "native"}}]`. The pin keeps a PDF off the paid OCR engine
  ($2 per 1,000 pages).
- Image: `{"type": "image_url", "image_url": {"url": "data:image/png;base64,…"}}`.
- Schema: `"response_format": {"type": "json_schema", "json_schema": {"name": "answer", "strict": true, "schema": {…}}}`.
- Cost and token counts arrive in the stream's last chunk under `usage`. `usage: {"include": true}` is deprecated
  and does nothing.

## Gotchas

- Reasoning is mandatory on Gemini 4; `effort: "none"` is rejected. `xhigh` exists on Neon and Hydrogen only.
- A PNG with a transparent background reaches the model as a black image (the pilot's page image did). Flatten onto
  white before attaching.
- Estimating tokens at "four characters each" is wrong by half for JSON and for Hebrew.
- Since 2026-10-18 Google applies Safety Retention to models served through Vertex; `--zdr` excludes AI Studio and
  may leave no endpoint.
- The Batch API is about half price, cannot be cancelled, keeps data 30 days and takes no base64 images. Not built
  yet.

## Not yet checked

Audio and video request shapes and size limits; the largest PDF accepted; whether Carbon and Argon behave like Neon
on reasoning; whether a cache read ever appears; the Batch API end to end.
