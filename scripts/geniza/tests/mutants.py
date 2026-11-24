"""Mutant check for geniza: each mutant breaks one behavior; the suite must fail on every one.

One copy of geniza.py at a fixed scratch path, rewritten for each mutant, deleted at the end. Never touches the
live module. Usage: uv run --python 3.14 python -I mutants.py SCRATCH_DIR
"""
import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent / "geniza.py"

# (name, exact text in geniza.py, replacement); each target must occur exactly once
MUTANTS = [
    ("no fork: every change counts as growth", 'return "fork"', 'return "growth"'),
    ("identical content rewritten", 'if old_key == new_key:\n        return "identical"', "if False:\n        pass"),
    ("unchanged manifest not recognised", "return key(stats) == key(stored)", "return False"),
    ("images kept", "def ref(source: dict) -> dict:\n", "def ref(source: dict) -> dict:\n    return source\n"),
    ("nothing cut", "    n = len(s.encode(\"utf-8\", \"surrogatepass\"))\n", "    return s\n"),
    ("structured results kept", 'if k != "toolUseResult"', 'if k != "kept"'),
    ("thinking signature kept", 'if k != "signature"', 'if k != "kept"'),
    ("dropped types kept", 'if obj.get("type") in DROP_TYPES:', "if False:"),
    ("read-back count unchecked", "foot.get(\"records\") != records or n != records:", "False:"),
    ("partial last line parsed as a record", "            if not raw.endswith(b\"\\n\"):\n", "            if False:\n"),
    ("no read-back", "        read_back(tmp, sid, generation, n)\n", ""),
    ("temp file left after a failure", "            tmp.unlink()\n        shutil.rmtree(work", "            pass\n        shutil.rmtree(work"),
    ("quiet window ignored", "> cfg.clock() - cfg.quiet_s:\n                    result[\"pending\"] += 1\n                    continue",
     "> 1e30:\n                    result[\"pending\"] += 1\n                    continue"),
    ("no lock", "            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)\n", ""),
    ("no free-space floor", "    if free < need:", "    if False:"),
    ("non-session entries enumerated", r'UUID_RE = re.compile(r"^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(?:$|\.)")',
     r'UUID_RE = re.compile(r"^([^.]+)(?:$|\.)")'),
    ("siblings ignored", "elif entry.name != sid and entry.is_file(follow_symlinks=False):", "elif False:"),
    ("fork not alerted", '            alert(cfg, "fork",', '            (lambda *a, **k: None)(cfg, "fork",'),
    ("verify trusts the index", "    head, foot, n = scan_slim(cfg.root / r[\"path\"])\n", "    return\n"),
    ("reindex loses verified_at", '"captured_at": head["created_at"], "verified_at": head["created_at"]})',
     '"captured_at": head["created_at"], "verified_at": None})'),
    ("managed pin unchecked", '(("settings.json", cfg.settings_path), ("managed settings", cfg.managed_path))',
     '(("settings.json", cfg.settings_path),)'),
    ("old sessions unchecked", "OLD_DAYS_CHECK = 75", "OLD_DAYS_CHECK = 10 ** 6"),
    ("header sha256 wrong", '"mtime_ns": pre[rel]["mtime_ns"], "sha256": sha}', '"mtime_ns": pre[rel]["mtime_ns"], "sha256": sha[::-1]}'),
    ("network import", "import argparse\n", "import argparse\nimport socket\n"),
    ("text member held whole", "first += s[: keep + 1 - len(first)]", "first += s"),
    ("truncated text member taken as text", "final=not chunk", "final=False"),
    ("read holds every record", 'for rec in read_slim(cfg.root / row["path"]):',
     'for rec in list(read_slim(cfg.root / row["path"])):'),
    ("lone surrogate written as invalid UTF-8", 'return SURROGATE_RE.sub(lambda m: f"\\\\u{ord(m.group()):04x}", s).encode()',
     'return s.encode("utf-8", "surrogatepass")'),
    ("files made with the default umask", "    os.umask(0o077)", "    pass"),
    ("daily work every hour", "if last_daily is None or cfg.clock() - last_daily >= DAILY_S:", "if True:"),
    ("brief check walks projects", "    return problems + (json.loads(row[0]) if row else [])",
     "    return problems + archive_problems(cfg)"),
    ("brief check reads the oldest stored check", "ORDER BY rowid DESC LIMIT 1", "ORDER BY rowid LIMIT 1"),
    ("brief check creates an archive", '    if not (cfg.root / "index.sqlite").exists():\n        return problems + ["no sweep has run"]\n', ""),
    ("no index backup", "        backup_index(cfg)\n", ""),
    ("live session retired", '        if sid in live:\n            blocked = "live', '        if False:\n            blocked = "live'),
    ("changed session retired", "        elif not same_manifest(stats, json.loads(row[\"members\"])):\n            blocked",
     "        elif False:\n            blocked"),
    ("unarchived session retired", '        elif row is None:\n            blocked = "no slim copy"',
     '        elif False:\n            blocked = "no slim copy"'),
    ("young session in the plan", "        if newest > now - RETIRE_DAYS * 86400:", "        if False:"),
    ("dry run moves", "    if not apply:\n        plan = retire_plan(cfg)\n    else:", "    if False:\n        pass\n    else:"),
    ("apply skips the slim re-read", "                    slim_ok(cfg, p[\"row\"])\n", "                    pass\n"),
    ("untrash overwrites", "        if clash:\n", "        if False:\n"),
    ("purge before 14 days", "if cfg.clock() - when >= TRASH_DAYS * 86400:", "if True:"),
    ("capture passes the project as a separate argument", 'f"--project={pathlib.Path(tp).parent.name}"]',
     '"--project", pathlib.Path(tp).parent.name]'),
    ("lone surrogate left in the Markdown", 'return SURROGATE_RE.sub("\\N{REPLACEMENT CHARACTER}", "\\n".join(top + out))',
     'return "\\n".join(top + out)'),
]


def main(scratch: str) -> int:
    work = pathlib.Path(scratch)
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    target = work / "geniza.py"
    src = SRC.read_text()
    survived = []
    try:
        for name, old, new in MUTANTS:
            if src.count(old) != 1:
                print(f"BAD MUTANT {name!r}: target occurs {src.count(old)} times")
                survived.append(name)
                continue
            target.write_text(src.replace(old, new))
            env = {**os.environ, "GENIZA_MODULE": str(target)}
            r = subprocess.run([sys.executable, "-I", "-m", "unittest", "discover", "-s", str(HERE)],
                               env=env, capture_output=True, text=True)
            killed = r.returncode != 0
            print(f"{'killed  ' if killed else 'SURVIVED'} {name}")
            if not killed:
                survived.append(name)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print(f"{len(MUTANTS) - len(survived)} of {len(MUTANTS)} mutants killed")
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
