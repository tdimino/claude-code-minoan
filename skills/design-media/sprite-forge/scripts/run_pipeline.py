#!/usr/bin/env python3
"""Execute a sprite-forge pipeline profile (pipelines/schema.json) stage by stage.

  run_pipeline.py profile.json                 # run every stage; paid stages stay in dry-run and
                                               # stages that need their outputs are held back
  run_pipeline.py profile.json --yes           # paid stages spend credits
  run_pipeline.py profile.json --dry-run       # print the resolved commands only, execute nothing
  run_pipeline.py profile.json --stage walk-clip [--force]
  run_pipeline.py profile.json --from rotate8
  run_pipeline.py profile.json --validate      # schema check only

Each run writes <output_root>/run/<timestamp>/manifest.json with per-stage command, input/output
sha256 digests, duration and status, and updates <output_root>/run/latest.json. A stage whose
inputs+args digest matches the last successful run and whose outputs exist is skipped (like the
matching_record rule in open-rebellion's faithful_hd_pipeline.py); --force reruns it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL_DIR / "scripts"
SCHEMA_PATH = SKILL_DIR / "pipelines" / "schema.json"
VAR_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


# ------------------------------------------------------------------ hashing

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str | None:
    """File digest, or a digest over (relative name, digest) of every file under a directory."""
    if path.is_file():
        return sha256_bytes(path.read_bytes())
    if path.is_dir():
        h = hashlib.sha256()
        for f in sorted(p for p in path.rglob("*") if p.is_file()):
            h.update(str(f.relative_to(path)).encode())
            h.update(sha256_bytes(f.read_bytes()).encode())
        return h.hexdigest()
    return None


# ------------------------------------------------------------- resolution

def resolve(value, vars_: dict):
    if isinstance(value, str):
        def sub(m):
            k = m.group(1)
            if k not in vars_:
                sys.exit(f"undefined variable ${{{k}}}")
            return str(vars_[k])
        prev = None
        while prev != value:
            prev, value = value, VAR_RE.sub(sub, value)
        return value
    if isinstance(value, list):
        return [resolve(v, vars_) for v in value]
    if isinstance(value, dict):
        return {k: resolve(v, vars_) for k, v in value.items()}
    return value


def validate(profile: dict) -> list[str]:
    """Schema validation via jsonschema when installed; structural fallback otherwise."""
    try:
        import jsonschema  # type: ignore
        schema = json.loads(SCHEMA_PATH.read_text())
        return [f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}"
                for e in jsonschema.Draft202012Validator(schema).iter_errors(profile)]
    except ImportError:
        pass
    errors = []
    for k in ("name", "stages"):
        if k not in profile:
            errors.append(f"missing '{k}'")
    if not isinstance(profile.get("stages"), list) or not profile.get("stages"):
        errors.append("'stages' must be a non-empty list")
        return errors
    names = set()
    for i, st in enumerate(profile["stages"]):
        for k in ("name", "stage"):
            if k not in st:
                errors.append(f"stages[{i}]: missing '{k}'")
        if st.get("name") in names:
            errors.append(f"stages[{i}]: duplicate name {st['name']}")
        names.add(st.get("name"))
        if st.get("stage") == "shell" and not st.get("cmd"):
            errors.append(f"stages[{i}]: shell stage needs 'cmd'")
        if "args" in st and not isinstance(st["args"], dict):
            errors.append(f"stages[{i}]: 'args' must be an object")
    return errors


def args_to_argv(args: dict) -> list[str]:
    argv: list[str] = []
    for k, v in args.items():
        flag = "--" + k.replace("_", "-")
        if v is None or v is False:
            continue
        if v is True:
            argv.append(flag)
        elif isinstance(v, list):
            for item in v:
                argv += [flag, str(item)]
        else:
            argv += [flag, str(v)]
    return argv


def build_command(stage: dict, yes: bool) -> list[str]:
    if stage["stage"] == "shell":
        return list(stage["cmd"])
    target = stage["stage"]
    script = SCRIPTS / f"{target}.py" if not target.endswith(".py") and "/" not in target else Path(target)
    if not script.exists():
        sys.exit(f"stage {stage['name']}: script not found: {script}")
    interp = stage.get("python", "python3")
    cmd = [interp]
    if interp == "blender":
        cmd += ["--background", "--python", str(script), "--"]
    else:
        cmd.append(str(script))
    cmd += [str(p) for p in stage.get("positional", [])]
    cmd += args_to_argv(stage.get("args", {}))
    if stage.get("paid") and yes:
        cmd.append("--yes")
    return cmd


# -------------------------------------------------------------------- run

def load_latest(output_root: Path) -> dict:
    p = output_root / "run" / "latest.json"
    if p.exists():
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def stage_digest(stage: dict, cmd: list[str], base: Path) -> str:
    h = hashlib.sha256(json.dumps(cmd).encode())
    for inp in stage.get("inputs", []):
        d = sha256_path(base / inp if not os.path.isabs(inp) else Path(inp))
        h.update(f"{inp}={d}".encode())
    return h.hexdigest()


def outputs_present(stage: dict, base: Path) -> bool:
    return all((base / o if not os.path.isabs(o) else Path(o)).exists() for o in stage.get("outputs", []))


def abs_path(p: str, base: Path) -> Path:
    return Path(p) if os.path.isabs(p) else base / p


def depends_on_unavailable(stage: dict, unavailable: set[Path], base: Path) -> list[str]:
    """Inputs of `stage` that an upstream dry-run stage declared but never wrote (or files under them)."""
    hits = []
    for inp in stage.get("inputs", []):
        ip = abs_path(inp, base)
        if any(ip == u or u in ip.parents or ip in u.parents for u in unavailable):
            hits.append(inp)
    return hits


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("profile")
    p.add_argument("--stage", action="append", help="run only these stage names")
    p.add_argument("--from", dest="from_stage", help="run from this stage onwards")
    p.add_argument("--dry-run", action="store_true", help="print resolved commands; execute nothing")
    p.add_argument("--yes", action="store_true", help="let paid stages spend credits")
    p.add_argument("--force", action="store_true", help="rerun stages even when digests match")
    p.add_argument("--validate", action="store_true", help="schema-check the profile and exit")
    p.add_argument("--var", action="append", help="override vars: key=value")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    profile_path = Path(a.profile).resolve()
    raw = json.loads(profile_path.read_text())
    errors = validate(raw)
    if errors:
        for e in errors:
            print(f"profile error: {e}", file=sys.stderr)
        sys.exit(2)
    if a.validate:
        print(f"{profile_path.name}: valid ({len(raw['stages'])} stages)")
        return

    vars_ = {"profile_dir": str(profile_path.parent), "skill_dir": str(SKILL_DIR), "profile_name": raw["name"]}
    vars_.update(raw.get("vars", {}))
    for kv in a.var or []:
        k, _, v = kv.partition("=")
        vars_[k] = v
    # vars may reference each other
    for _ in range(3):
        vars_ = {k: resolve(v, vars_) if isinstance(v, str) else v for k, v in vars_.items()}
    profile = resolve(raw, vars_)
    base = Path.cwd()
    output_root = Path(profile.get("output_root", f"./sprite-out/{profile['name']}"))
    if not output_root.is_absolute():
        output_root = base / output_root

    stages = profile["stages"]
    if a.from_stage:
        names = [s["name"] for s in stages]
        if a.from_stage not in names:
            sys.exit(f"unknown stage {a.from_stage}")
        stages = stages[names.index(a.from_stage):]
    if a.stage:
        unknown = set(a.stage) - {s["name"] for s in stages}
        if unknown:
            sys.exit(f"unknown stage(s): {sorted(unknown)}")
        stages = [s for s in stages if s["name"] in a.stage]

    latest = {} if a.force else load_latest(output_root)
    now = datetime.now(timezone.utc)
    run_id = now.strftime("%Y%m%dT%H%M%S") + f"{now.microsecond // 1000:03d}Z"
    manifest = {"schema": "sprite-forge/pipeline-run-v1", "profile": str(profile_path), "name": profile["name"],
                "run_id": run_id, "dry_run": a.dry_run, "yes": a.yes, "vars": vars_, "stages": []}

    # Outputs a paid stage declared but did not write because it stayed a provider dry-run.
    # Any later stage that reads them is skipped too instead of failing on a missing file.
    unavailable: set[Path] = set()
    for st in stages:
        cmd = build_command(st, a.yes)
        rec = {"name": st["name"], "command": cmd, "status": None, "paid": bool(st.get("paid"))}
        printable = " ".join(shlex.quote(c) for c in cmd)
        if st.get("skip"):
            rec["status"] = "skipped:profile"
            manifest["stages"].append(rec)
            print(f"[{st['name']}] skipped (profile)")
            continue
        blocked = depends_on_unavailable(st, unavailable, base)
        if blocked and not a.dry_run:
            rec["status"] = "skipped:upstream-dry-run"
            rec["blocked_by"] = blocked
            unavailable.update(abs_path(o, base) for o in st.get("outputs", []))
            manifest["stages"].append(rec)
            print(f"[{st['name']}] skipped: inputs come from a paid stage that stayed a dry-run "
                  f"({', '.join(blocked)}); rerun with --yes")
            continue
        digest = stage_digest(st, cmd, base)
        rec["digest"] = digest
        if a.dry_run:
            rec["status"] = "dry-run"
            manifest["stages"].append(rec)
            tag = " (paid; stays a provider dry-run without --yes)" if st.get("paid") and not a.yes else \
                  " (PAID; will spend credits)" if st.get("paid") else ""
            print(f"[{st['name']}]{tag}\n  {printable}")
            continue
        prev = latest.get("stages_by_name", {}).get(st["name"])
        if prev and prev.get("digest") == digest and prev.get("status") == "ok" and outputs_present(st, base) \
                and not (st.get("paid") and a.yes and not prev.get("yes")):
            rec["status"] = "skipped:unchanged"
            rec["outputs"] = prev.get("outputs")
            manifest["stages"].append(rec)
            print(f"[{st['name']}] unchanged, skipped")
            continue
        print(f"[{st['name']}] $ {printable}")
        t0 = time.time()
        r = subprocess.run(cmd, cwd=st.get("cwd") or None)
        rec["seconds"] = round(time.time() - t0, 2)
        if r.returncode != 0:
            rec["status"] = f"failed:{r.returncode}"
            manifest["stages"].append(rec)
            if st.get("optional"):
                print(f"[{st['name']}] failed (optional), continuing", file=sys.stderr)
                continue
            _write(output_root, run_id, manifest)
            sys.exit(f"[{st['name']}] failed with exit {r.returncode}")
        missing = [o for o in st.get("outputs", []) if not (base / o if not os.path.isabs(o) else Path(o)).exists()]
        if missing and (st.get("paid") and not a.yes):
            rec["status"] = "ok:dry-run"   # paid stage did its own cost check; outputs are not expected
            unavailable.update(abs_path(o, base) for o in missing)
        elif missing:
            rec["status"] = "failed:missing-outputs"
            rec["missing"] = missing
            manifest["stages"].append(rec)
            _write(output_root, run_id, manifest)
            sys.exit(f"[{st['name']}] declared outputs missing: {missing}")
        else:
            rec["status"] = "ok"
        rec["yes"] = a.yes
        rec["outputs"] = {o: sha256_path(base / o if not os.path.isabs(o) else Path(o)) for o in st.get("outputs", [])}
        manifest["stages"].append(rec)

    if not a.dry_run:
        _write(output_root, run_id, manifest)
    if a.json:
        print(json.dumps(manifest, indent=2))
    else:
        done = sum(1 for s in manifest["stages"] if s["status"] == "ok")
        held = sum(1 for s in manifest["stages"] if s["status"] in ("ok:dry-run", "skipped:upstream-dry-run"))
        print(f"{profile['name']}: {len(manifest['stages'])} stage(s), {done} executed"
              + (f", {held} held back without --yes" if held else "")
              + ("" if a.dry_run else f", manifest {output_root / 'run' / run_id / 'manifest.json'}"))


def _write(output_root: Path, run_id: str, manifest: dict) -> None:
    run_dir = output_root / "run" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    latest_path = output_root / "run" / "latest.json"
    latest = load_latest(output_root)
    by_name = latest.get("stages_by_name", {})
    for s in manifest["stages"]:
        if s["status"] in ("ok", "skipped:unchanged"):
            by_name[s["name"]] = {"digest": s.get("digest"), "status": "ok", "outputs": s.get("outputs"),
                                  "run_id": run_id, "yes": s.get("yes", False)}
    latest_path.write_text(json.dumps({"run_id": run_id, "stages_by_name": by_name}, indent=2))


if __name__ == "__main__":
    main()
