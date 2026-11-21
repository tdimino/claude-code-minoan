#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""gemini-orchestrator CLI: hand one bounded task to a Gemini model through OpenRouter, with no agent harness.

  gemini_exec.py run <profile> "<brief>" [--context PATH ...] [--attach FILE ...] [--model neon] [--reasoning high]
  gemini_exec.py estimate <same arguments>     the quote; nothing is sent
  gemini_exec.py models [--all]                today's ids, prices and efforts
  gemini_exec.py spend                         totals from the ledger

`run` goes: resolve model -> pack -> egress guard -> quote -> cost gate -> send -> check reply -> write output with
a trailer -> ledger. Exit codes: 0 done, 1 API or transport failure, 2 usage, 3 cost gate, 4 empty or truncated
answer, 5 egress guard, 6 served by a different model.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import context_pack as cp  # noqa: E402
import citations as ct  # noqa: E402
import or_client as oc  # noqa: E402

SKILL_DIR = Path(__file__).resolve().parent.parent
EXIT_OK, EXIT_API, EXIT_USAGE, EXIT_GATE, EXIT_EMPTY, EXIT_EGRESS, EXIT_MODEL = 0, 1, 2, 3, 4, 5, 6

DEFAULTS = {
    "gate_usd": 0.50,            # worst-case dollars per call above which --approved-usd is required
    "daily_ceiling_usd": 10.00,  # ledger total for the day above which nothing more is sent
    "input_margin": 1.2,         # the input estimate is from bytes, so the quote adds a margin until calibrated
    "data_collection": "deny",
    "egress_denylist": [],
    "answer_tokens": 8000,
    "profiles": {
        "raw": {"model": "neon", "effort": "medium"},
        "reader": {"model": "neon", "effort": "medium"},
        "reviewer": {"model": "neon", "effort": "high"},
        "adjudicator": {"model": "neon", "effort": "high"},
        "architect": {"model": "neon", "effort": "high"},
        "builder": {"model": "neon", "effort": "medium"},
        "extractor": {"model": "hydrogen", "effort": "low"},
        "seer": {"model": "neon", "effort": "medium"},
        "chat": {"model": "hydrogen", "effort": "low"},
    },
}


def load_config() -> dict:
    config = json.loads(json.dumps(DEFAULTS))
    path = Path(os.environ.get("GEMINI_ORCH_CONFIG", SKILL_DIR / "config.json"))
    if path.exists():
        user = json.loads(path.read_text(encoding="utf-8"))
        config["profiles"].update(user.pop("profiles", {}))
        config.update(user)
    return config


def agents_dir() -> Path:
    return Path(os.environ.get("GEMINI_ORCH_AGENTS", SKILL_DIR / "agents"))


def find_spend_rule(start: Path) -> Path | None:
    """A project's paid-API rule, in the working directory or above it. Where one exists, every call needs a number."""
    for d in (start, *start.parents):
        rule = d / ".claude/rules/paid-api-spend.md"
        if rule.exists():
            return rule
    return None


# --- ledger -----------------------------------------------------------------------------------------------------

def ledger_path() -> Path:
    return oc.data_dir() / "ledger.jsonl"


def append_ledger(entry: dict) -> None:
    line = (json.dumps(entry, ensure_ascii=False) + "\n").encode("utf-8")
    fd = os.open(ledger_path(), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(fd, line)  # one O_APPEND write per entry, so concurrent runs cannot interleave
    finally:
        os.close(fd)


def failures_path() -> Path:
    return oc.data_dir() / "failures.jsonl"


def append_failure(entry: dict) -> None:
    """One line for every call that was sent and did not return a usable answer, with what is needed to say why."""
    line = json.dumps(entry, ensure_ascii=False) + "\n"
    fd = os.open(failures_path(), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(fd, line.encode("utf-8"))
    finally:
        os.close(fd)


def read_failures() -> list[dict]:
    try:
        lines = failures_path().read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def read_ledger() -> list[dict]:
    try:
        lines = ledger_path().read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    entries = []
    for line in lines:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # a malformed line does not hide the others
    return entries


def spent(entries: list[dict], prefix: str) -> float:
    return sum(float(e.get("cost") or 0) for e in entries if str(e.get("time", "")).startswith(prefix))


# --- one request, prepared ---------------------------------------------------------------------------------------

class Usage(Exception):
    """A mistake in how the command was called; exit 2."""


class Egress(Exception):
    def __init__(self, findings):
        super().__init__("egress guard")
        self.findings = findings


def prepare(args, config: dict) -> dict:
    """Everything `estimate` and `run` share: the model, the messages, the quote. Sends nothing but the model list."""
    profile = config["profiles"].get(args.profile)
    if profile is None:
        raise Usage(f"unknown profile '{args.profile}'; profiles: {', '.join(config['profiles'])}")
    system = ""
    if args.profile != "raw":
        persona = agents_dir() / f"{args.profile}.md"
        if not persona.exists():
            raise Usage(f"profile '{args.profile}' has no persona file yet ({persona}); use 'raw' until Phase 3")
        system = persona.read_text(encoding="utf-8")
        shared = agents_dir() / "_shared.md"  # the no-tools rules every persona starts from
        if shared.exists():
            system = f"{shared.read_text(encoding='utf-8')}\n\n{system}"

    model = oc.resolve_model(args.model or profile["model"], oc.fetch_models())
    if args.reasoning:
        effort = oc.check_effort(model, args.reasoning)  # an effort asked for by name is checked strictly
    else:
        try:
            effort = oc.check_effort(model, profile.get("effort"))
        except oc.ClientError:
            effort = oc.check_effort(model, None)  # the profile's default does not suit this model: use the model's
    answer_tokens = args.answer_tokens or config["answer_tokens"]
    max_tokens = oc.max_tokens_for(answer_tokens, effort, model, args.reasoning_tokens)

    try:
        files, skipped = cp.collect(args.context or [], allow_large=args.allow_large)
        attachments = [cp.attachment(a) for a in args.attach or []]
    except (FileNotFoundError, PermissionError, ValueError) as e:
        raise Usage(str(e)) from e
    pack = cp.render(files)
    brief = args.brief

    addresses = cp.deny_addresses(config.get("egress_denylist"))
    texts = [("<brief>", brief), ("<persona>", system)] + [(f.path, f.text) for f in files]
    findings = cp.scan(texts, addresses, exempt=set(args.allow or []))
    if args.redact:
        pack, brief = cp.redact(pack, addresses), cp.redact(brief, addresses)
        findings = [f for f in findings if f.kind != "denied email address"]
    if findings:
        raise Egress(findings)

    history: list[dict] = []
    if args.session and Path(args.session).exists():
        history = json.loads(Path(args.session).read_text(encoding="utf-8"))
    messages = list(history)
    if system and not any(m.get("role") == "system" for m in messages):
        messages.insert(0, {"role": "system", "content": system})
    task = f"<task>\n{brief}\n</task>"
    if attachments or args.cache:
        content: list[dict] = []
        if pack:
            block = {"type": "text", "text": pack}
            if args.cache:
                block["cache_control"] = {"type": "ephemeral"}
            content.append(block)
        content.extend(part for part, _, _ in attachments)
        content.append({"type": "text", "text": task})
        messages.append({"role": "user", "content": content})
    else:
        messages.append({"role": "user", "content": f"{pack}\n\n{task}" if pack else task})

    history_text = "\n".join(m["content"] if isinstance(m.get("content"), str) else json.dumps(m.get("content"))
                             for m in history)
    # Each file is classed by its own content: one class for a whole mixed pack overstated a real run by 46%.
    text_tokens = sum(cp.estimate_tokens(t) for t in (system, task, history_text))
    text_tokens += sum(cp.estimate_tokens(cp.render([f])) for f in files)
    attachment_tokens = sum(tokens for _, tokens, _ in attachments)
    # A schema is sent with the request and billed as input: in the pilot a 206-byte schema added about 180 tokens.
    schema_tokens = Path(args.schema).stat().st_size if args.schema and Path(args.schema).exists() else 0
    input_tokens = math.ceil((text_tokens + attachment_tokens + schema_tokens) * config["input_margin"])

    window = int(model.get("context_length") or 0)
    if window and input_tokens + max_tokens > window:
        sizes = sorted(((cp.estimate_tokens(f.text), f.path) for f in files), reverse=True)[:10]
        listing = "\n".join(f"  {tokens:>10,}  {path}" for tokens, path in sizes)
        raise Usage(f"about {input_tokens:,} input tokens plus max_tokens {max_tokens:,} exceeds {model['id']}'s "
                    f"{window:,}-token window. Largest files:\n{listing}")

    price_in, price_out = oc.prices(model)
    ceiling = input_tokens * price_in + max_tokens * price_out
    rule = find_spend_rule(Path.cwd())
    gate = 0.0 if rule else float(config["gate_usd"])
    return {
        "model": model, "effort": effort, "max_tokens": max_tokens, "messages": messages, "files": files,
        "skipped": skipped, "has_pdf": any(kind == "pdf" for _, _, kind in attachments),
        "input_tokens": input_tokens, "ceiling": ceiling, "gate": gate, "rule": rule, "history": history,
        "quote": (f"1 call, about {input_tokens:,} input tokens (bytes-based, +{round((config['input_margin'] - 1) * 100)}%"
                  f" margin), max_tokens {max_tokens:,} at {effort or 'no'} effort, ceiling ${ceiling:.2f} on "
                  f"{model['id']}"),
    }


def approval_needed(prep: dict, approved: float | None) -> str | None:
    """Why this call may not be sent yet, or None."""
    need = math.ceil(prep["ceiling"] * 100) / 100
    if prep["ceiling"] > prep["gate"] and (approved is None or approved + 1e-9 < need):
        why = f"spend rule at {prep['rule']}" if prep["rule"] else f"gate ${prep['gate']:.2f}"
        return f"{prep['quote']}. Needs --approved-usd {need:.2f} ({why})."
    return None


# --- commands ---------------------------------------------------------------------------------------------------

def cmd_estimate(args, config) -> int:
    prep = prepare(args, config)
    for path, why in prep["skipped"]:
        print(f"left out: {path} ({why})")
    blocked = approval_needed(prep, args.approved_usd)
    print(blocked if blocked else f"{prep['quote']}. Within the gate (${prep['gate']:.2f}); would be sent.")
    return EXIT_OK


def cmd_run(args, config) -> int:
    prep = prepare(args, config)
    blocked = approval_needed(prep, args.approved_usd)
    if blocked:
        print(blocked, file=sys.stderr)
        return EXIT_GATE
    now = dt.datetime.now()
    today = spent(read_ledger(), now.strftime("%Y-%m-%d"))
    if today + prep["ceiling"] > float(config["daily_ceiling_usd"]):
        print(f"Daily ceiling: ${today:.2f} spent today plus this call's ceiling ${prep['ceiling']:.2f} exceeds "
              f"${float(config['daily_ceiling_usd']):.2f} (daily_ceiling_usd in config.json).", file=sys.stderr)
        return EXIT_GATE

    schema = json.loads(Path(args.schema).read_text(encoding="utf-8")) if args.schema else None
    model = prep["model"]
    body = oc.build_body(model["id"], prep["messages"], effort=prep["effort"], max_tokens=prep["max_tokens"],
                         schema=schema, has_pdf=prep["has_pdf"], data_collection=config["data_collection"],
                         zdr=args.zdr)
    for path, why in prep["skipped"]:
        print(f"left out: {path} ({why})", file=sys.stderr)
    print(f"Sending: {prep['quote']}", file=sys.stderr)
    api_key = oc.load_api_key()
    request = {
        "time": now.isoformat(timespec="seconds"), "cwd": str(Path.cwd()), "profile": args.profile,
        "model": model["id"], "effort": prep["effort"], "max_tokens": prep["max_tokens"],
        "estimated_input_tokens": prep["input_tokens"], "ceiling": round(prep["ceiling"], 4),
        "timeout": args.timeout, "attachments": bool(prep["has_pdf"]), "schema": bool(schema), "zdr": bool(args.zdr),
    }
    sent_at = time.monotonic()
    try:
        result = oc.chat(body, api_key, timeout=args.timeout)
    except oc.ClientError as e:
        # Refused or unreachable before any stream opened: nothing was generated, so nothing is billed.
        append_failure({**request, "stage": "before the stream", "status": str(e), "http_status": e.status,
                        "exit_code": EXIT_API, "timing": {"total_s": round(time.monotonic() - sent_at, 1)}})
        print(f"FAILURE_LOG={failures_path()}", file=sys.stderr)
        raise

    usage = result.usage
    cost = oc.cost_of(usage)
    details = usage.get("completion_tokens_details") or {}
    cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
    served = result.model
    family_ok = (not served) or served.startswith(model["id"]) or served == model.get("canonical_slug")

    if result.partial:
        status, code = f"partial ({result.error})", EXIT_API
    elif not family_ok:
        status, code = "served by a different model", EXIT_MODEL
    elif not result.content.strip() or result.finish_reason == "length":
        status, code = f"empty or truncated (finish={result.finish_reason})", EXIT_EMPTY
    else:
        status, code = "ok", EXIT_OK

    stamp = now.strftime("%Y%m%d-%H%M%S")
    out = Path(args.out) if args.out else Path.cwd() / ".subdaimon-output" / f"gemini-{args.profile}-{stamp}-{os.getpid()}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = out.with_suffix(".manifest.json")
    manifest = cp.manifest(prep["files"])
    manifest_path.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    # Every quoted citation in the answer is compared with the packed file it names.
    cited, problems = ct.summarise(ct.check_answer(result.content, manifest))
    cost_text = f"${cost:.4f}" if cost is not None else "unreported"
    trailer = (f"<!-- gemini-exec: status={status} requested={model['id']} served={served or 'unreported'} "
               f"provider={result.provider or 'unreported'} effort={prep['effort']} "
               f"in={usage.get('prompt_tokens', '?')} out={usage.get('completion_tokens', '?')} "
               f"reasoning={details.get('reasoning_tokens', '?')} cached={cached} cost={cost_text} "
               f"finish={result.finish_reason or 'none'} citations={cited} manifest={manifest_path.name} -->")
    out.write_text(f"{result.content}\n\n{trailer}\n", encoding="utf-8")

    append_ledger({
        "time": now.isoformat(timespec="seconds"), "cwd": str(Path.cwd()), "profile": args.profile,
        "model": model["id"], "served": served, "provider": result.provider, "effort": prep["effort"],
        "status": status, "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"), "reasoning_tokens": details.get("reasoning_tokens"),
        "cached_tokens": cached, "cost": cost, "ceiling": round(prep["ceiling"], 4),
        "estimated_input_tokens": prep["input_tokens"], "generation_id": result.generation_id, "output": str(out),
        "citations": cited, "seconds": result.timing.get("total_s"),
        "first_text_seconds": result.timing.get("first_text_s"),
    })
    if code != EXIT_OK:
        # OpenRouter's record says what a broken call cost; a call with no record was most likely not billed.
        record = oc.generation(result.generation_id, api_key)
        append_failure({
            **request, "stage": "during the stream" if result.partial else "after the stream", "status": status,
            "exit_code": code, "error": result.error, "finish": result.finish_reason, "served": served,
            "provider": result.provider, "generation_id": result.generation_id, "timing": result.timing,
            "answer_chars": len(result.content), "usage": usage, "cost": cost, "openrouter_record": record,
            "output": str(out),
        })

    if code == EXIT_OK and args.session:
        history = prep["messages"] + [{"role": "assistant", "content": result.content}]
        Path(args.session).write_text(json.dumps(history, ensure_ascii=False, indent=1), encoding="utf-8")
    if not args.quiet and result.content:
        print(result.content)
    print(f"{trailer}\nOUTPUT_FILE={out}", file=sys.stderr)
    if code != EXIT_OK:
        t = result.timing
        print(f"FAILURE_LOG={failures_path()}\n"
              f"Timing: {t.get('total_s')} s in all; first line at {t.get('first_line_s')} s, first answer text at "
              f"{t.get('first_text_s')} s, last line at {t.get('last_line_s')} s; {t.get('keepalives')} keep-alives, "
              f"{t.get('data_chunks')} data chunks. OpenRouter's record of the generation: "
              f"{'$' + format(record['total_cost'], '.4f') + ' charged' if record and record.get('total_cost') is not None else 'none found'}.",
              file=sys.stderr)
    if problems:
        print(f"Citations that did not verify ({len(problems)}):", file=sys.stderr)
        for line in problems:
            print(f"  {line}", file=sys.stderr)
    if code == EXIT_EMPTY:
        used = details.get("reasoning_tokens") or prep["max_tokens"]
        print(f"The answer is empty or cut off and {cost_text} was spent. Reasoning is billed as output and shares "
              f"max_tokens ({prep['max_tokens']:,}) with the answer; it used {used:,}. To run again, quote "
              f"--reasoning-tokens {2 * used:,} (how much it wants is unknown, only that {used:,} was not enough), "
              f"or lower --reasoning. Not retried automatically: a second call is a new spend.", file=sys.stderr)
    return code


def cmd_verify(args, config) -> int:
    """Re-check an output file's citations against its manifest, for instance after reading the answer."""
    output = Path(args.output)
    try:
        answer, manifest = output.read_text(encoding="utf-8"), ct.manifest_for(output)
    except OSError as e:
        raise Usage(f"cannot read the output or its manifest: {e}") from e
    cited, problems = ct.summarise(ct.check_answer(answer, manifest))
    print(f"citations verified: {cited}")
    for line in problems:
        print(f"  {line}")
    return EXIT_OK if not problems else EXIT_API


def cmd_models(args, config) -> int:
    models = oc.fetch_models(force=args.refresh)
    alias_of = {v: k for k, v in oc.ALIASES.items()}
    rows = []
    for m in models:
        if not m["id"].startswith("google/"):
            continue
        if not args.all and (m["id"] not in alias_of):
            continue
        price_in, price_out = oc.prices(m)
        efforts = ",".join((m.get("reasoning") or {}).get("supported_efforts") or []) or "-"
        rows.append((alias_of.get(m["id"], ""), m["id"], f"${price_in * 1e6:.3f}", f"${price_out * 1e6:.3f}",
                     f"{int(m.get('context_length') or 0):,}", efforts))
    print(f"{'alias':<9} {'model':<40} {'in/M':>8} {'out/M':>8} {'context':>10}  efforts")
    for row in rows:
        print(f"{row[0]:<9} {row[1]:<40} {row[2]:>8} {row[3]:>8} {row[4]:>10}  {row[5]}")
    return EXIT_OK


def cmd_spend(args, config) -> int:
    entries = read_ledger()
    now = dt.datetime.now()
    print(f"today  ${spent(entries, now.strftime('%Y-%m-%d')):.4f}")
    print(f"month  ${spent(entries, now.strftime('%Y-%m')):.4f}")
    print(f"all    ${spent(entries, ''):.4f}  ({len(entries)} calls; ledger {ledger_path()})")
    return EXIT_OK


def cmd_failures(args, config) -> int:
    """The last failed calls, newest last, each with its timings. --json prints the full records."""
    entries = read_failures()[-args.last:]
    if args.json:
        for e in entries:
            print(json.dumps(e, ensure_ascii=False))
        return EXIT_OK
    if not entries:
        print(f"no failures recorded ({failures_path()})")
        return EXIT_OK
    for e in entries:
        t = e.get("timing") or {}
        record = e.get("openrouter_record") or {}
        cost = e.get("cost") if e.get("cost") is not None else record.get("total_cost")
        print(f"{e.get('time')}  {e.get('profile')}  {e.get('model')}  effort={e.get('effort')}  "
              f"max_tokens={e.get('max_tokens')}  in≈{e.get('estimated_input_tokens')}")
        print(f"    {e.get('stage')}: {e.get('status')}")
        print(f"    {t.get('total_s')} s in all; first line {t.get('first_line_s')} s, first text "
              f"{t.get('first_text_s')} s, last line {t.get('last_line_s')} s; {t.get('keepalives')} keep-alives, "
              f"{t.get('data_chunks')} chunks; provider {e.get('provider') or 'unreported'}; "
              f"cost {'$' + format(cost, '.4f') if cost is not None else 'no record'}")
    print(f"{len(entries)} shown; log {failures_path()}")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gemini_exec.py", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "estimate"):
        p = sub.add_parser(name)
        p.add_argument("profile")
        p.add_argument("brief")
        p.add_argument("--model", help="alias (neon, hydrogen, carbon, argon, flash) or any OpenRouter id")
        p.add_argument("--reasoning", help="effort; checked against the model's own list")
        p.add_argument("--answer-tokens", type=int, help="tokens to leave for the visible answer")
        p.add_argument("--reasoning-tokens", type=int, help="tokens set aside for reasoning (default by effort)")
        p.add_argument("--context", nargs="+", action="extend", help="files, folders or globs to pack")
        p.add_argument("--attach", nargs="+", action="extend", help="images or PDFs sent natively")
        p.add_argument("--schema", help="JSON schema file for a structured answer")
        p.add_argument("--session", help="JSON file carrying the conversation between calls")
        p.add_argument("--cache", action="store_true", help="mark the pack as a cache breakpoint")
        p.add_argument("--approved-usd", type=float, help="the ceiling Tom agreed to, in dollars")
        p.add_argument("--allow", nargs="+", action="extend", help="packed paths exempt from the secret patterns")
        p.add_argument("--redact", action="store_true", help="replace denied addresses with [email]")
        p.add_argument("--allow-large", action="store_true", help="pack files over 2 MB")
        p.add_argument("--zdr", action="store_true", help="zero-data-retention endpoints only")
        p.add_argument("--out", help="output file (default .subdaimon-output/gemini-<profile>-<time>.md)")
        p.add_argument("--quiet", action="store_true", help="print only the trailer and the path")
        p.add_argument("--timeout", type=float, default=900)
    m = sub.add_parser("models")
    m.add_argument("--all", action="store_true", help="every Google model, not only the aliased ones")
    m.add_argument("--refresh", action="store_true", help="ignore the day-old cache")
    sub.add_parser("spend")
    f = sub.add_parser("failures")
    f.add_argument("--last", type=int, default=10, help="how many to show (default 10)")
    f.add_argument("--json", action="store_true", help="the full records, one per line")
    v = sub.add_parser("verify")
    v.add_argument("output", help="an output file written by run")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config()
        commands = {"run": cmd_run, "estimate": cmd_estimate, "models": cmd_models, "spend": cmd_spend,
                    "verify": cmd_verify, "failures": cmd_failures}
        return commands[args.command](args, config)
    except Usage as e:
        print(f"Usage: {e}", file=sys.stderr)
        return EXIT_USAGE
    except Egress as e:
        print("Egress guard: this request would carry material that may not leave the machine.", file=sys.stderr)
        for f in e.findings:
            print(f"  {f.path}:{f.line}  {f.kind}", file=sys.stderr)
        print("Remove the file from --context, use --redact for addresses, or --allow <path> for a false alarm on "
              "a secret pattern.", file=sys.stderr)
        return EXIT_EGRESS
    except oc.ClientError as e:
        print(f"OpenRouter: {e}", file=sys.stderr)
        return EXIT_USAGE if e.usage else EXIT_API


if __name__ == "__main__":
    sys.exit(main())
