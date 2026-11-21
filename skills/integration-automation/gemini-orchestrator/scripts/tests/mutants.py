"""Mutation check: break one line at a time in a copy of the scripts and confirm the test suite fails.

A test that cannot fail proves nothing. Each mutant below removes or inverts one behaviour; a mutant the suite
still passes ("survived") names a behaviour no test covers. The live scripts are never touched: every mutant is
applied to a fresh copy in a temporary folder.

    uv run python ~/.claude/skills/gemini-orchestrator/scripts/tests/mutants.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent

MUTANTS = [
    # (file, original text, replacement, behaviour removed)
    ("or_client.py", '"exclude": True}', '"exclude": False}', "reasoning text excluded from the reply"),
    ("or_client.py", 't["keepalives"] += 1', "pass", "keep-alives counted"),
    ("or_client.py", 't["data_chunks"] += 1', "pass", "data chunks counted"),
    ("or_client.py", 't["first_text_s"] = elapsed', "pass", "time to first answer text recorded"),
    ("or_client.py", "return {k: data.get(k) for k in keep}", "return data", "generation record trimmed to known fields"),
    ("gemini_exec.py", "if code != EXIT_OK:\n        # OpenRouter's record", "if False:\n        # OpenRouter's record",
     "failed call written to the failure log"),
    ("gemini_exec.py", 'append_failure({**request, "stage": "before the stream"', 'dict({**request, "stage": "before the stream"',
     "refusal before the stream written to the failure log"),
    ("gemini_exec.py", '"citations": cited, "seconds": result.timing.get("total_s"),', '"citations": cited,',
     "duration written to the ledger"),
    ("gemini_exec.py", "entries = read_failures()[-args.last:]", "entries = read_failures()", "failures --last"),
    ("or_client.py", '{"data_collection": data_collection,', '{"data_collection": "allow",', "data-collection deny"),
    ("or_client.py", '"pdf": {"engine": "native"}', '"pdf": {"engine": "mistral-ocr"}', "native PDF engine pinned"),
    ("or_client.py", "if e.code in RETRYABLE and attempt < retries:", "if False:", "retry before any text"),
    ("or_client.py", "return min(answer_tokens + allowance,", "return min(answer_tokens,",
     "reasoning allowance added to max_tokens"),
    ("or_client.py", "allowance = reasoning_tokens if reasoning_tokens is not None else", "allowance =",
     "--reasoning-tokens overrides the allowance"),
    ("or_client.py", 'if effort == "none" and r.get("mandatory"):', "if False:", "mandatory-reasoning message"),
    ("or_client.py", "if supported and effort not in supported:", "if False:", "effort checked against the model"),
    ("or_client.py", "< MODELS_MAX_AGE:", "< 0:", "model list cache"),
    ("or_client.py", "if not result.finish_reason and not result.error:", "if False:", "stream without a finish"),
    ("or_client.py", 'result.error = str(err.get("message") if isinstance(err, dict) else err)\n                    result.partial = True',
     'result.error = str(err.get("message") if isinstance(err, dict) else err)', "mid-stream error marks partial"),
    ("or_client.py", 'USER_AGENT = "gemini-orchestrator/0.1"', 'USER_AGENT = "gemini-orchestrator/0.1 (x@y.z)"',
     "user agent without contact detail"),
    ("or_client.py", "max_completion(model))", "10**9)", "max_tokens capped at the model's maximum"),
    ("context_pack.py", "    files.sort(key=lambda f: f.path)", "    pass", "stable pack order"),
    ("context_pack.py", "if real in seen or not p.is_file():", "if not p.is_file():", "duplicate files dropped"),
    ("context_pack.py", "            if was_explicit:\n                raise PermissionError",
     "            if False:\n                raise PermissionError", "explicit credentials file refused"),
    ("context_pack.py", 'if FORBIDDEN_NAME.search(shown.replace(os.sep, "/")):', "if False:",
     "credentials files left out"),
    ("context_pack.py", 'if b"\\0" in data[:8192]:', "if False:", "binary files left out"),
    ("context_pack.py", "if size > MAX_FILE_BYTES and not allow_large:", "if False:", "2 MB limit"),
    ("context_pack.py", '+ [a.replace("@", "%40") for a in addresses]\n    findings', "+ []\n    findings",
     "URL-encoded address caught"),
    ("context_pack.py", "    exempt = exempt or set()", "    exempt = set()", "--allow exemption"),
    ("context_pack.py", "            if label in exempt:\n                continue\n            for kind",
     "            if label in exempt:\n                break\n            for kind", "exempt file still scanned for addresses"),
    ("context_pack.py", "if non_ascii / len(data) > 0.05:", "if False:", "non-ASCII text counted at its own ratio"),
    ("context_pack.py", 'kind = "prose" if share >= 0.80 else "code" if share >= 0.62 else "dense"', 'kind = "prose"',
     "JSON and code counted denser than prose"),
    ("context_pack.py", 'else "code" if share >= 0.62 else "dense"', 'else "dense"', "code counted apart from JSON"),
    ("gemini_exec.py", "text_tokens += sum(cp.estimate_tokens(cp.render([f])) for f in files)",
     "text_tokens += cp.estimate_tokens(pack)", "each file estimated by its own class"),
    ("gemini_exec.py", "--reasoning-tokens {2 * used:,}", "--reasoning-tokens {used:,}",
     "empty answer suggests twice the reasoning used"),
    ("context_pack.py", 'text = re.sub(re.escape(needle), "[email]", text, flags=re.I)',
     'text = re.sub(re.escape(needle), "[email]", text)', "redaction ignores case"),
    ("context_pack.py", 'if any(needle in low for needle in needles):', "if False:", "denied address caught"),
    ("context_pack.py", 'out.extend(f"{n}| {line}" for n, line in enumerate(f.text.splitlines(), 1))',
     "out.extend(f.text.splitlines())", "line numbers in the pack"),
    ("citations.py", "LINE_SLACK = 1 ", "LINE_SLACK = 5 ", "a quotation far from its cited lines is misplaced"),
    ("citations.py", 'text = unicodedata.normalize("NFC", text)', "text = text", "NFD and NFC compare equal"),
    ("citations.py", 'elif _contains(normalise("\\n".join(lines)), wanted):', "elif False:",
     "misplaced told apart from not found"),
    ("citations.py", "if start < 1 or end < start or start > len(lines):", "if False:", "out-of-range lines"),
    ("citations.py", 'same = hashlib.sha256(data).hexdigest() == entry["sha256"]', "same = True",
     "changed file not judged"),
    ("citations.py", "found = haystack.find(piece.strip(), position)", "found = haystack.find(piece.strip())",
     "ellipsis pieces must come in order"),
    ("citations.py", '        if quote is None:\n            checks.append(Check(path, start, end, None, "located"))\n            continue',
     "        if False:\n            continue", "bare citation located"),
    ("citations.py", 'good = sum(1 for c in quoted if c.verdict == "verified")', "good = len(quoted)",
     "only verified quotations counted as good"),
    ("gemini_exec.py", "    if problems:\n        print(f\"Citations that did not verify", "    if False:\n        print(f\"Citations that did not verify",
     "unverified citations listed"),
    ("gemini_exec.py", "        if shared.exists():", "        if False:", "shared rules prepended to the persona"),
    ("gemini_exec.py", "(text_tokens + attachment_tokens + schema_tokens)", "(text_tokens + attachment_tokens)",
     "schema counted in the quote"),
    ("gemini_exec.py", 'gate = 0.0 if rule else float(config["gate_usd"])', 'gate = float(config["gate_usd"])',
     "project spend rule sets the gate to zero"),
    ("gemini_exec.py", "(approved is None or approved + 1e-9 < need)", "(approved is None)",
     "approval below the ceiling refused"),
    ("gemini_exec.py", 'if prep["ceiling"] > prep["gate"] and', "if False and", "cost gate"),
    ("gemini_exec.py", 'if today + prep["ceiling"] > float(config["daily_ceiling_usd"]):', "if False:",
     "daily ceiling"),
    ("gemini_exec.py", "family_ok = (not served) or", "family_ok = True or", "served-model check"),
    ("gemini_exec.py", 'elif not result.content.strip() or result.finish_reason == "length":', "elif False:",
     "empty answer detected"),
    ("gemini_exec.py", 'findings = [f for f in findings if f.kind != "denied email address"]', "findings = []",
     "--redact does not excuse secrets"),
    ("gemini_exec.py", "    if findings:\n        raise Egress(findings)", "    if False:\n        raise Egress(findings)",
     "egress guard"),
    ("gemini_exec.py", "if window and input_tokens + max_tokens > window:", "if False:", "context window check"),
    ("gemini_exec.py", '"cached_tokens": cached, "cost": cost,', '"cached_tokens": cached, "cost": None,',
     "cost in the ledger"),
    ("gemini_exec.py", "if code == EXIT_OK and args.session:", "if False:", "session saved"),
    ("gemini_exec.py", 'f"{pack}\\n\\n{task}" if pack else task', 'f"{task}\\n\\n{pack}" if pack else task',
     "pack first, brief last"),
    ("gemini_exec.py", 'block["cache_control"] = {"type": "ephemeral"}', "pass", "cache breakpoint on the pack"),
    ("gemini_exec.py", 'messages.insert(0, {"role": "system", "content": system})', "pass", "persona sent as system"),
    ("gemini_exec.py", "effort = oc.check_effort(model, None)  # the profile's", "raise  # the profile's",
     "profile default falls back to the model's effort"),
    ("gemini_exec.py", "if result.partial:\n        status, code = f\"partial ({result.error})\", EXIT_API",
     "if False:\n        status, code = f\"partial ({result.error})\", EXIT_API", "partial reply is a failure"),
    ("gemini_exec.py", "pack, brief = cp.redact(pack, addresses), cp.redact(brief, addresses)", "pass",
     "--redact rewrites the text"),
]


def run_suite(scripts: Path) -> bool:
    out = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=scripts,
                         capture_output=True, text=True)
    return out.returncode == 0


def main() -> int:
    survived, broken = [], []
    with tempfile.TemporaryDirectory() as tmp:
        def fresh_copy(label: str) -> Path:
            """A copy of scripts/ with agents/ beside it, as in the skill (one test reads the shipped personas)."""
            root = Path(tmp) / label
            shutil.copytree(SCRIPTS, root / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(SCRIPTS.parent / "agents", root / "agents")
            return root / "scripts"

        if not run_suite(fresh_copy("baseline")):
            print("The unmutated copy fails its tests; fix that first.")
            return 2
        for i, (name, old, new, what) in enumerate(MUTANTS, 1):
            copy = fresh_copy(f"m{i}")
            target = copy / name
            text = target.read_text(encoding="utf-8")
            if text.count(old) != 1:
                broken.append((name, what, text.count(old)))
                continue
            target.write_text(text.replace(old, new), encoding="utf-8")
            if run_suite(copy):
                survived.append((name, what))
            shutil.rmtree(copy.parent)
    killed = len(MUTANTS) - len(survived) - len(broken)
    print(f"{len(MUTANTS)} mutants: {killed} killed, {len(survived)} survived, {len(broken)} not applied")
    for name, what in survived:
        print(f"  SURVIVED  {name}: {what}")
    for name, what, count in broken:
        print(f"  NOT APPLIED  {name}: {what} (original text found {count} times, need exactly 1)")
    return 0 if not survived and not broken else 1


if __name__ == "__main__":
    sys.exit(main())
