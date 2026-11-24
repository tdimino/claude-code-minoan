#!/usr/bin/env python3
"""geniza: a slim, verified archive of Claude Code transcripts (plan 2026-11-21-001).

Every session in ~/.claude/projects (a <uuid>.jsonl, its <uuid>/ folder, and any <uuid>.* sibling) gets one slim
copy: the transcript's own records with the heavy payloads cut (images become sha256 references, tool output and
tool input keep their first 4 KB and last 1 KB, file-history snapshots, api-request records and attachments are
dropped), zstd-compressed under ~/.local/share/geniza/slim/. A copy is never replaced by one built from less: growth
replaces it, any other change writes a new generation and keeps the old. geniza only reads ~/.claude/projects.

Usage (stdlib only, Python 3.14 for compression.zstd):
  uv run --python 3.14 python -I geniza.py sweep [--dry-run] [--session SID]
  uv run --python 3.14 python -I geniza.py capture --stdin        # SessionEnd hook; detaches
  uv run --python 3.14 python -I geniza.py verify [--all | --sample N]
  uv run --python 3.14 python -I geniza.py check [--brief]
  uv run --python 3.14 python -I geniza.py read SID [--thinking] [--subagents]
  uv run --python 3.14 python -I geniza.py stats | reindex
Environment: GENIZA_ROOT, GENIZA_PROJECTS, GENIZA_LOG_DIR, GENIZA_NOW (epoch seconds), GENIZA_FREE_FLOOR_GB.
"""
from __future__ import annotations

import argparse
import codecs
import contextlib
import ctypes
import ctypes.util
import dataclasses
import fcntl
import hashlib
import json
import os
import pathlib
import random
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from collections import Counter
from compression import zstd

HOME = pathlib.Path.home()
UUID_RE = re.compile(r"^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(?:$|\.)")
DROP_TYPES = {"file-history-snapshot", "api-request", "api-request-blob", "api-request-shape", "attachment",
              "queue-operation"}
TOOL_HEAD, TOOL_TAIL = 4096, 1024          # tool output and tool input strings
TEXT_HEAD, TEXT_TAIL = 49152, 8192         # message text and thinking
GENERIC_CAP = 65536                        # any other string
TEXT_MEMBER_HEAD, TEXT_MEMBER_TAIL = 4096, 1024
LEVEL = 10
OLD_DAYS_CHECK = 75
DAILY_S = 86400
RETIRE_DAYS = 90    # a session leaves projects/ once its newest file is this old
TRASH_DAYS = 14     # and stays in geniza's trash this long before purge-trash may delete it
SURROGATE_RE = re.compile("[\ud800-\udfff]")  # half of a character, left by a JavaScript cut by UTF-16 unit
CHUNK = 1 << 20


class Locked(Exception):
    """Another geniza process holds the lock."""


@dataclasses.dataclass
class Config:
    root: pathlib.Path
    projects: pathlib.Path
    now: float | None = None
    settings_path: pathlib.Path = HOME / ".claude" / "settings.json"
    managed_path: pathlib.Path = pathlib.Path("/Library/Application Support/ClaudeCode/managed-settings.json")
    free_floor_bytes: int = 20 * 10 ** 9
    lock_timeout: float = 600.0
    quiet_s: float = 600.0
    expect_cleanup: int = 99999
    log_dir: pathlib.Path | None = None
    sessions_dir: pathlib.Path = HOME / ".claude" / "sessions"  # Claude Code's <pid>.json files: the live sessions

    def __post_init__(self):
        self.root = pathlib.Path(self.root)
        self.projects = pathlib.Path(self.projects)
        self.sessions_dir = pathlib.Path(self.sessions_dir)
        self.log_dir = pathlib.Path(self.log_dir) if self.log_dir else self.root

    def clock(self) -> float:
        return self.now if self.now is not None else time.time()


# --------------------------------------------------------------------------------------------- store and lock

SCHEMA = """
CREATE TABLE IF NOT EXISTS slim (
  project TEXT NOT NULL, sid TEXT NOT NULL, generation INTEGER NOT NULL, path TEXT NOT NULL,
  members TEXT NOT NULL, records INTEGER NOT NULL, raw_bytes INTEGER NOT NULL, slim_bytes INTEGER NOT NULL,
  newest_mtime_ns INTEGER NOT NULL, captured_at REAL NOT NULL, verified_at REAL,
  PRIMARY KEY (project, sid, generation));
CREATE TABLE IF NOT EXISTS events (at REAL NOT NULL, kind TEXT NOT NULL, project TEXT, sid TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS runs (started REAL NOT NULL, finished REAL, cmd TEXT NOT NULL, result TEXT);
"""
ROW_COLS = ("project", "sid", "generation", "path", "members", "records", "raw_bytes", "slim_bytes",
            "newest_mtime_ns", "captured_at", "verified_at")


@contextlib.contextmanager
def db(cfg: Config):
    cfg.root.mkdir(parents=True, exist_ok=True, mode=0o700)
    con = sqlite3.connect(cfg.root / "index.sqlite", timeout=30)
    con.row_factory = sqlite3.Row
    try:
        con.executescript(SCHEMA)
        yield con
        con.commit()
    finally:
        con.close()


@contextlib.contextmanager
def locked(cfg: Config):
    cfg.root.mkdir(parents=True, exist_ok=True, mode=0o700)
    f = open(cfg.root / "geniza.lock", "a")
    deadline = time.monotonic() + cfg.lock_timeout
    while True:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                f.close()
                raise Locked(f"{cfg.root / 'geniza.lock'} is held by another geniza process")
            time.sleep(0.1)
    try:
        yield
    finally:
        fcntl.flock(f, fcntl.LOCK_UN)
        f.close()


def alert(cfg: Config, kind: str, detail: str, project: str | None = None, sid: str | None = None) -> None:
    cfg.log_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(cfg.clock()))
    with open(cfg.log_dir / "alerts.log", "a") as f:
        f.write(f"{stamp} {kind}: {detail}\n")
    with db(cfg) as con:
        con.execute("INSERT INTO events VALUES (?,?,?,?,?)", (cfg.clock(), kind, project, sid, detail))


def current_row(cfg: Config, project: str, sid: str) -> dict | None:
    with db(cfg) as con:
        r = con.execute("SELECT * FROM slim WHERE project=? AND sid=? ORDER BY generation DESC LIMIT 1",
                        (project, sid)).fetchone()
    return dict(r) if r else None


def index_rows(cfg: Config) -> list[tuple]:
    with db(cfg) as con:
        return [tuple(r) for r in con.execute(f"SELECT {','.join(ROW_COLS)} FROM slim ORDER BY project, sid, generation")]


def put_row(con: sqlite3.Connection, row: dict) -> None:
    con.execute(f"INSERT OR REPLACE INTO slim ({','.join(ROW_COLS)}) VALUES ({','.join('?' * len(ROW_COLS))})",
                tuple(row[c] for c in ROW_COLS))


# --------------------------------------------------------------------------------------------- sessions

def enumerate_sessions(projects: pathlib.Path) -> dict[tuple[str, str], list[str]]:
    """(project dir, session id) -> member paths relative to the project dir, main transcript first.

    A session is any UUID seen as <uuid>.jsonl, a <uuid>/ folder, or a <uuid>.* sibling; nothing else in a project
    folder (memory/, memory.bak-*, sessions-index.json) is touched."""
    out: dict[tuple[str, str], list[str]] = {}
    if not projects.is_dir():
        return out
    for pdir in sorted(p for p in projects.iterdir() if p.is_dir() and not p.is_symlink()):
        for entry in os.scandir(pdir):
            m = UUID_RE.match(entry.name)
            if not m:
                continue
            sid = m.group(1)
            members = out.setdefault((pdir.name, sid), [])
            if entry.name == sid and entry.is_dir(follow_symlinks=False):
                for dirpath, dirnames, filenames in os.walk(entry.path):
                    dirnames[:] = [d for d in dirnames if not os.path.islink(os.path.join(dirpath, d))]
                    for fn in filenames:
                        full = os.path.join(dirpath, fn)
                        if os.path.isfile(full) and not os.path.islink(full):
                            members.append(os.path.relpath(full, pdir))
            elif entry.name != sid and entry.is_file(follow_symlinks=False):
                members.append(entry.name)
    for (project, sid), members in list(out.items()):
        if not members:
            del out[(project, sid)]
            continue
        main = f"{sid}.jsonl"
        members.sort(key=lambda p: (p != main, p))
    return out


def stat_manifest(pdir: pathlib.Path, members: list[str]) -> list[dict]:
    rows = []
    for rel in members:
        try:
            st = os.lstat(pdir / rel)
        except FileNotFoundError:
            continue
        rows.append({"path": rel, "size": st.st_size, "mtime_ns": st.st_mtime_ns})
    return rows


def same_manifest(stats: list[dict], stored: list[dict]) -> bool:
    key = lambda rows: sorted((r["path"], r["size"], r["mtime_ns"]) for r in rows)
    return key(stats) == key(stored)


_libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
_clonefile = getattr(_libc, "clonefile", None)


def clone(src: pathlib.Path, dst: pathlib.Path) -> None:
    """APFS clonefile (instant, point-in-time); a plain copy where cloning is not possible."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if _clonefile is not None and _clonefile(os.fsencode(src), os.fsencode(dst), 0) == 0:
        return
    shutil.copy2(src, dst)


def hash_file(path: pathlib.Path, prefix_size: int | None) -> tuple[str, int, str | None]:
    """sha256 of the whole file, its size, and the sha256 of its first prefix_size bytes (one pass)."""
    h = hashlib.sha256()
    prefix = None
    seen = 0
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK):
            if prefix_size is not None and prefix is None and seen + len(chunk) >= prefix_size:
                cut = prefix_size - seen
                h.update(chunk[:cut])
                prefix = h.hexdigest()
                h.update(chunk[cut:])
            else:
                h.update(chunk)
            seen += len(chunk)
    if prefix_size is not None and prefix is None and seen == prefix_size:
        prefix = h.hexdigest()
    return h.hexdigest(), seen, prefix


# --------------------------------------------------------------------------------------------- the slim form

def _cut_note(n: int, head: int, tail: int) -> str:
    return f"\n…[geniza: {n} bytes, cut to the first {head} and last {tail} characters]…\n"


def cut(s: str, head: int, tail: int) -> str:
    if len(s) <= head + tail + 256:
        return s
    n = len(s.encode("utf-8", "surrogatepass"))
    return s[:head] + _cut_note(n, head, tail) + s[-tail:]


def cut_file(path: pathlib.Path, head: int, tail: int) -> str | None:
    """cut() of a file's text, read in chunks so a 64 MiB file is never held whole; None when it is not UTF-8."""
    keep = head + tail + 256
    dec = codecs.getincrementaldecoder("utf-8")()
    first, last, chars, size = "", "", 0, 0
    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(CHUNK)
                s = dec.decode(chunk, final=not chunk)
                size += len(chunk)
                chars += len(s)
                if len(first) <= keep:
                    first += s[: keep + 1 - len(first)]
                last = (last + s)[-tail:]
                if not chunk:
                    break
    except UnicodeDecodeError:
        return None
    return first if chars <= keep else first[:head] + _cut_note(size, head, tail) + last


def ref(source: dict) -> dict:
    data = source.get("data") or ""
    return {"type": "geniza-ref", "media_type": source.get("media_type"),
            "sha256": hashlib.sha256(data.encode()).hexdigest(), "bytes": len(data) * 3 // 4}


def generic(v, cap: int = GENERIC_CAP):
    if isinstance(v, str):
        return cut(v, cap - 8192, 4096) if len(v) > cap else v
    if isinstance(v, list):
        return [generic(x, cap) for x in v]
    if isinstance(v, dict):
        if v.get("type") == "base64" and isinstance(v.get("data"), str):
            return ref(v)
        return {k: generic(x, cap) for k, x in v.items()}
    return v


def cut_strings(v):
    """Tool input: every long string keeps its first 4 KB and last 1 KB."""
    if isinstance(v, str):
        return cut(v, TOOL_HEAD, TOOL_TAIL)
    if isinstance(v, list):
        return [cut_strings(x) for x in v]
    if isinstance(v, dict):
        return {k: cut_strings(x) for k, x in v.items()}
    return v


def slim_block(b):
    if not isinstance(b, dict):
        return generic(b)
    t = b.get("type")
    if t == "text":
        return {**b, "text": cut(b.get("text") or "", TEXT_HEAD, TEXT_TAIL)}
    if t == "thinking":
        out = {k: v for k, v in b.items() if k != "signature"}
        out["thinking"] = cut(b.get("thinking") or "", TEXT_HEAD, TEXT_TAIL)
        return out
    if t == "redacted_thinking":
        return {"type": "redacted_thinking", "bytes": len(b.get("data") or "")}
    if t == "tool_use":
        return {**b, "input": cut_strings(b.get("input"))}
    if t == "tool_result":
        c = b.get("content")
        if isinstance(c, str):
            c = cut(c, TOOL_HEAD, TOOL_TAIL)
        elif isinstance(c, list):
            c = [{**x, "text": cut(x.get("text") or "", TOOL_HEAD, TOOL_TAIL)}
                 if isinstance(x, dict) and x.get("type") == "text" else generic(x) for x in c]
        return {**b, "content": c}
    if t in ("image", "document") and isinstance(b.get("source"), dict) and b["source"].get("type") == "base64":
        return {**b, "source": ref(b["source"])}
    return generic(b)


def slim_record(obj: dict) -> dict:
    out = {k: v for k, v in obj.items() if k != "toolUseResult"}
    msg = out.get("message")
    if isinstance(msg, dict):
        msg = dict(msg)
        c = msg.get("content")
        if isinstance(c, list):
            msg["content"] = [slim_block(b) for b in c]
        elif isinstance(c, str):
            msg["content"] = cut(c, TEXT_HEAD, TEXT_TAIL)
        out["message"] = msg
    return generic(out)


def slim_jsonl(path: pathlib.Path, counts: Counter):
    """Yield slim records of one JSONL file, streamed; an unfinished last line (no newline) is skipped and counted,
    a broken middle line is noted."""
    with open(path, "rb") as f:
        for raw in f:
            if not raw.endswith(b"\n"):
                if raw.strip():
                    counts["partial_tail_bytes"] += len(raw)
                break
            yield from _slim_line(raw, counts)


def _slim_line(raw: bytes, counts: Counter):
    if not raw.strip():
        return
    try:
        obj = json.loads(raw)
    except ValueError:
        counts["unparsed_lines"] += 1
        yield {"type": "geniza-unparsed", "bytes": len(raw), "head": raw[:200].decode("utf-8", "replace")}
        return
    if not isinstance(obj, dict):
        return
    if obj.get("type") in DROP_TYPES:
        counts[obj["type"]] += 1
        return
    if "toolUseResult" in obj:
        counts["structured_results_dropped"] += 1
    yield slim_record(obj)


def member_record(rel: str, clone_path: pathlib.Path, meta: dict) -> dict:
    rec = {"type": "geniza-member", "path": rel, "size": meta["size"], "sha256": meta["sha256"]}
    if rel.endswith(".jsonl") or ".jsonl." in rel:
        rec["kind"] = "jsonl"
        return rec
    text = cut_file(clone_path, TEXT_MEMBER_HEAD, TEXT_MEMBER_TAIL)
    if text is None:
        rec["kind"] = "binary"
        return rec
    rec["kind"] = "text"
    rec["text"] = text
    return rec


def dump_line(obj) -> bytes:
    """One JSONL line in UTF-8. A lone surrogate stays a \\udXXX escape, as in the source, so it reads back exactly."""
    s = json.dumps(obj, ensure_ascii=False) + "\n"
    try:
        return s.encode()
    except UnicodeEncodeError:
        return SURROGATE_RE.sub(lambda m: f"\\u{ord(m.group()):04x}", s).encode()


def write_slim(tmp: pathlib.Path, header: dict, body, counts: Counter) -> int:
    opts = {zstd.CompressionParameter.compression_level: LEVEL, zstd.CompressionParameter.checksum_flag: 1}
    n = 0
    with open(tmp, "wb") as raw:
        with zstd.ZstdFile(raw, "wb", options=opts) as z:
            z.write(dump_line(header))
            for rec in body:
                z.write(dump_line(rec))
                n += 1
            z.write(dump_line({"type": "geniza-end", "records": n, "dropped": dict(counts)}))
        raw.flush()
        os.fsync(raw.fileno())
    os.chmod(tmp, 0o600)
    return n


def read_slim(path: pathlib.Path):
    with zstd.open(path, "rb") as f:
        for line in f:
            yield json.loads(line)


def scan_slim(path: pathlib.Path) -> tuple[dict, dict, int]:
    """Stream a slim file: its header, its footer and the number of records between them; every line must parse."""
    head = last = None
    lines = 0
    for rec in read_slim(path):
        if head is None:
            head = rec
        last = rec
        lines += 1
    return head or {}, last or {}, max(lines - 2, 0)


def read_back(path: pathlib.Path, sid: str, generation: int, records: int) -> None:
    """The definition of verified: every line parses, the header names this generation, the footer's count holds."""
    head, foot, n = scan_slim(path)
    if head.get("type") != "geniza-header":
        raise ValueError("no header")
    if head.get("session_id") != sid or head.get("generation") != generation:
        raise ValueError("header does not name this generation")
    if foot.get("type") != "geniza-end" or foot.get("records") != records or n != records:
        raise ValueError("record count does not match the footer")


# --------------------------------------------------------------------------------------------- sweep

def classify(old_members: list[dict], new_members: list[dict], prefixes: dict[str, str | None]) -> str:
    """identical | growth | fork. Growth: every old member is still present and a byte-prefix of its new version."""
    new = {m["path"]: m for m in new_members}
    old_key = sorted((m["path"], m["size"], m["sha256"]) for m in old_members)
    new_key = sorted((m["path"], m["size"], m["sha256"]) for m in new_members)
    if old_key == new_key:
        return "identical"
    for m in old_members:
        n = new.get(m["path"])
        if n is None or n["size"] < m["size"] or prefixes.get(m["path"]) != m["sha256"]:
            return "fork"
    return "growth"


def archive_one(cfg: Config, con: sqlite3.Connection, project: str, sid: str, members: list[str],
                stats: list[dict], old: dict | None, result: Counter) -> None:
    pdir = cfg.projects / project
    raw_bytes = sum(s["size"] for s in stats)
    need = cfg.free_floor_bytes + 2 * (raw_bytes // 10 + (1 << 20))
    free = shutil.disk_usage(cfg.root).free
    if free < need:
        result["errors"] += 1
        alert(cfg, "free space", f"{free} bytes free, below the floor of {need}; {project}/{sid} not archived",
              project, sid)
        return
    work = cfg.root / "work" / f"{sid}-{os.getpid()}-{random.randrange(1 << 30)}"
    slim_dir = cfg.root / "slim" / project
    slim_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    old_members = json.loads(old["members"]) if old else []
    old_size = {m["path"]: m["size"] for m in old_members}
    tmp = None
    try:
        new_members, prefixes, clones = [], {}, {}
        pre = {s["path"]: s for s in stats}
        for rel in members:
            if rel not in pre:
                continue
            dst = work / rel
            clone(pdir / rel, dst)
            sha, size, prefix = hash_file(dst, old_size.get(rel))
            new_members.append({"path": rel, "size": size, "mtime_ns": pre[rel]["mtime_ns"], "sha256": sha})
            prefixes[rel] = prefix
            clones[rel] = dst
        kind = "new" if old is None else classify(old_members, new_members, prefixes)
        if kind == "identical":
            old["members"] = json.dumps(new_members, sort_keys=True, separators=(",", ":"))
            old["newest_mtime_ns"] = max(m["mtime_ns"] for m in new_members)
            put_row(con, old)
            result["unchanged"] += 1
            return
        generation = 1 if old is None else old["generation"] + (1 if kind == "fork" else 0)
        final = slim_dir / f"{sid}.g{generation}.jsonl.zst"
        tmp = final.with_name(final.name + f".tmp-{os.getpid()}")
        captured_at = cfg.clock()
        header = {"type": "geniza-header", "v": 1, "session_id": sid, "project": project, "generation": generation,
                  "created_at": captured_at, "members": new_members}
        counts: Counter = Counter()

        def body():
            for m in new_members:
                rel = m["path"]
                rec = member_record(rel, clones[rel], m)
                yield rec
                if rec["kind"] == "jsonl":
                    yield from slim_jsonl(clones[rel], counts)

        n = write_slim(tmp, header, body(), counts)
        read_back(tmp, sid, generation, n)
        os.replace(tmp, final)
        tmp = None
        dfd = os.open(slim_dir, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
        put_row(con, {"project": project, "sid": sid, "generation": generation,
                      "path": str(final.relative_to(cfg.root)),
                      "members": json.dumps(new_members, sort_keys=True, separators=(",", ":")),
                      "records": n, "raw_bytes": sum(m["size"] for m in new_members),
                      "slim_bytes": final.stat().st_size,
                      "newest_mtime_ns": max(m["mtime_ns"] for m in new_members),
                      "captured_at": captured_at, "verified_at": captured_at})
        con.commit()
        if kind == "fork":
            result["forked"] += 1
            alert(cfg, "fork", f"{project}/{sid}: a member vanished, shrank or changed in place; "
                               f"wrote g{generation}, kept g{generation - 1}", project, sid)
        elif kind == "growth":
            result["grown"] += 1
        else:
            result["archived"] += 1
    except Exception as e:  # one session's failure never stops the run
        result["errors"] += 1
        alert(cfg, "error", f"{project}/{sid}: {type(e).__name__}: {e}", project, sid)
    finally:
        if tmp is not None and tmp.exists():
            tmp.unlink()
        shutil.rmtree(work, ignore_errors=True)


def sweep(cfg: Config, only: set[tuple[str, str]] | None = None, dry_run: bool = False) -> dict:
    result: Counter = Counter({k: 0 for k in ("archived", "grown", "forked", "unchanged", "pending", "errors")})
    sessions = enumerate_sessions(cfg.projects)
    if only is not None:
        sessions = {k: v for k, v in sessions.items() if k in only}
    if dry_run:
        stored = {}
        if (cfg.root / "index.sqlite").exists():
            stored = {(r[0], r[1]): r for r in index_rows(cfg)}
        for (project, sid), members in sessions.items():
            stats = stat_manifest(cfg.projects / project, members)
            row = stored.get((project, sid))
            if row and same_manifest(stats, json.loads(row[4])):
                result["unchanged"] += 1
            elif stats and max(s["mtime_ns"] for s in stats) / 1e9 > cfg.clock() - cfg.quiet_s:
                result["pending"] += 1
            else:
                result["would_archive"] += 1
        return dict(result)
    with locked(cfg):
        for stale in (cfg.root / "slim").glob("*/*.tmp-*") if (cfg.root / "slim").exists() else []:
            stale.unlink(missing_ok=True)
        shutil.rmtree(cfg.root / "work", ignore_errors=True)
        started = cfg.clock()
        with db(cfg) as con:
            for (project, sid), members in sessions.items():
                stats = stat_manifest(cfg.projects / project, members)
                if not stats:
                    continue
                row = con.execute("SELECT * FROM slim WHERE project=? AND sid=? ORDER BY generation DESC LIMIT 1",
                                  (project, sid)).fetchone()
                old = dict(row) if row else None
                if old and same_manifest(stats, json.loads(old["members"])):
                    result["unchanged"] += 1
                    continue
                if max(s["mtime_ns"] for s in stats) / 1e9 > cfg.clock() - cfg.quiet_s:
                    result["pending"] += 1
                    continue
                archive_one(cfg, con, project, sid, members, stats, old, result)
            con.execute("INSERT INTO runs VALUES (?,?,?,?)", (started, cfg.clock(), "sweep", json.dumps(result)))
    return dict(result)


# --------------------------------------------------------------------------------------------- verify, reindex, check

def slim_ok(cfg: Config, r: dict) -> None:
    """Raise unless r's slim file reads whole (every line, zstd's checksum) and agrees with its index row."""
    head, foot, n = scan_slim(cfg.root / r["path"])
    ok = (head.get("type") == "geniza-header" and head.get("generation") == r["generation"]
          and json.dumps(head.get("members"), sort_keys=True, separators=(",", ":")) == r["members"]
          and foot.get("type") == "geniza-end" and foot.get("records") == r["records"] == n)
    if not ok:
        raise ValueError("header, members or record count disagree with the index")


def verify(cfg: Config, all_: bool = False, sample: int | None = None, sid: str | None = None) -> dict:
    with db(cfg) as con:
        rows = [dict(r) for r in con.execute("SELECT * FROM slim ORDER BY verified_at IS NOT NULL, verified_at")]
    if sid:
        rows = [r for r in rows if r["sid"].startswith(sid)]
    elif not all_:
        rows = rows[: sample or 20]
    failed = 0
    with locked(cfg), db(cfg) as con:
        for r in rows:
            try:
                slim_ok(cfg, r)
                con.execute("UPDATE slim SET verified_at=? WHERE project=? AND sid=? AND generation=?",
                            (cfg.clock(), r["project"], r["sid"], r["generation"]))
            except Exception as e:
                failed += 1
                alert(cfg, "verify failed", f"{r['path']}: {type(e).__name__}: {e}", r["project"], r["sid"])
    return {"checked": len(rows), "failed": failed}


def reindex(cfg: Config) -> int:
    """Rebuild the slim table from the headers and footers of the slim files themselves."""
    rows = []
    for path in sorted((cfg.root / "slim").glob("*/*.jsonl.zst")):
        head, foot, _ = scan_slim(path)
        members = head["members"]
        rows.append({"project": head["project"], "sid": head["session_id"], "generation": head["generation"],
                     "path": str(path.relative_to(cfg.root)),
                     "members": json.dumps(members, sort_keys=True, separators=(",", ":")),
                     "records": foot["records"], "raw_bytes": sum(m["size"] for m in members),
                     "slim_bytes": path.stat().st_size,
                     "newest_mtime_ns": max(m["mtime_ns"] for m in members) if members else 0,
                     "captured_at": head["created_at"], "verified_at": head["created_at"]})
    with locked(cfg), db(cfg) as con:
        con.execute("DELETE FROM slim")
        for r in rows:
            put_row(con, r)
    return len(rows)


def _cleanup_value(path: pathlib.Path):
    try:
        return json.loads(path.read_text()).get("cleanupPeriodDays")
    except (OSError, ValueError):
        return None


def _pin_problems(cfg: Config) -> list[str]:
    problems = []
    for label, path in (("settings.json", cfg.settings_path), ("managed settings", cfg.managed_path)):
        v = _cleanup_value(path)
        if v != cfg.expect_cleanup:
            problems.append(f"{label} ({path}): cleanupPeriodDays is {v!r}, expected {cfg.expect_cleanup}")
    return problems


def _sweep_age_problems(con: sqlite3.Connection, now: float) -> list[str]:
    last = con.execute("SELECT MAX(finished) FROM runs WHERE cmd='sweep'").fetchone()[0]
    if last is None or now - last > 3 * 3600:
        return ["the last sweep is more than 3 hours old" if last else "no sweep has run"]
    return []


def check(cfg: Config) -> list[str]:
    """Every problem: the cleanup pins, the sweep's age, and the archive's own (see archive_problems)."""
    with db(cfg) as con:
        age = _sweep_age_problems(con, cfg.clock())
    return _pin_problems(cfg) + age + archive_problems(cfg)


def archive_problems(cfg: Config) -> list[str]:
    """The index's integrity, recent forks, and sessions past OLD_DAYS_CHECK without a current verified copy."""
    problems = []
    now = cfg.clock()
    with db(cfg) as con:
        if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            problems.append("index.sqlite fails its integrity check; run `geniza reindex`")
        stored = {}
        for r in con.execute("SELECT * FROM slim ORDER BY generation"):
            stored[(r["project"], r["sid"])] = dict(r)
        forks = con.execute("SELECT COUNT(*) FROM events WHERE kind='fork' AND at > ?", (now - 7 * 86400,)).fetchone()[0]
    if forks:
        problems.append(f"{forks} forked generation(s) in the last 7 days; see alerts.log")
    for (project, sid), members in enumerate_sessions(cfg.projects).items():
        stats = stat_manifest(cfg.projects / project, members)
        if not stats or max(s["mtime_ns"] for s in stats) / 1e9 > now - OLD_DAYS_CHECK * 86400:
            continue
        row = stored.get((project, sid))
        if row is None or row["verified_at"] is None or not same_manifest(stats, json.loads(row["members"])):
            problems.append(f"{project}/{sid}: older than {OLD_DAYS_CHECK} days without a current verified slim copy")
    return problems


def backup_index(cfg: Config) -> pathlib.Path:
    """A consistent copy of index.sqlite beside it (sqlite's online backup), replaced atomically."""
    dst = cfg.root / "index.sqlite.bak"
    tmp = dst.with_name(dst.name + f".tmp-{os.getpid()}")
    with db(cfg) as con:
        bak = sqlite3.connect(tmp)
        try:
            con.backup(bak)
        finally:
            bak.close()
    os.replace(tmp, dst)
    return dst


def hourly(cfg: Config) -> dict:
    """The launchd job: sweep; once a day (by the age of the last daily run, so a sleeping Mac catches up on waking)
    verify the 20 least recently verified copies and back up the index; then store archive_problems for
    `check --brief`."""
    out = {"sweep": sweep(cfg)}
    with db(cfg) as con:
        last_daily = con.execute("SELECT MAX(finished) FROM runs WHERE cmd='daily'").fetchone()[0]
    if last_daily is None or cfg.clock() - last_daily >= DAILY_S:
        started = cfg.clock()
        out["verify"] = verify(cfg, sample=20)
        backup_index(cfg)
        with db(cfg) as con:
            con.execute("INSERT INTO runs VALUES (?,?,?,?)", (started, cfg.clock(), "daily", json.dumps(out["verify"])))
    out["problems"] = archive_problems(cfg)
    with db(cfg) as con:
        con.execute("INSERT INTO runs VALUES (?,?,?,?)", (cfg.clock(), cfg.clock(), "check", json.dumps(out["problems"])))
    return out


def brief_problems(cfg: Config) -> list[str]:
    """SessionStart's check, in milliseconds: the pins and the sweep's age, read fresh, plus the archive problems the
    last hourly run stored. It walks nothing in projects/ and creates nothing where no archive exists yet."""
    problems = _pin_problems(cfg)
    if not (cfg.root / "index.sqlite").exists():
        return problems + ["no sweep has run"]
    with db(cfg) as con:
        problems += _sweep_age_problems(con, cfg.clock())
        row = con.execute("SELECT result FROM runs WHERE cmd='check' ORDER BY rowid DESC LIMIT 1").fetchone()
    return problems + (json.loads(row[0]) if row else [])


# --------------------------------------------------------------------------------------------- retire

def live_session_ids(cfg: Config) -> set[str]:
    """Sessions a running Claude Code process holds, from its ~/.claude/sessions/<pid>.json."""
    out = set()
    for f in cfg.sessions_dir.glob("*.json"):
        try:
            info = json.loads(f.read_text())
            os.kill(int(info["pid"]), 0)
        except PermissionError:
            pass  # alive, another user's
        except (OSError, ValueError, KeyError, TypeError):
            continue
        out.add(info.get("sessionId"))
    return out


def retire_plan(cfg: Config) -> list[dict]:
    """Every session whose newest file is more than RETIRE_DAYS old: eligible (blocked None) or blocked, and why."""
    now = cfg.clock()
    live = live_session_ids(cfg)
    rows = {}
    with db(cfg) as con:
        for r in con.execute("SELECT * FROM slim ORDER BY generation"):
            rows[(r["project"], r["sid"])] = dict(r)
    plan = []
    for (project, sid), members in enumerate_sessions(cfg.projects).items():
        stats = stat_manifest(cfg.projects / project, members)
        if not stats:
            continue
        newest = max(s["mtime_ns"] for s in stats) / 1e9
        if newest > now - RETIRE_DAYS * 86400:
            continue
        row = rows.get((project, sid))
        if sid in live:
            blocked = "live: a running Claude Code process holds it"
        elif row is None:
            blocked = "no slim copy"
        elif row["verified_at"] is None:
            blocked = "slim copy not verified"
        elif not same_manifest(stats, json.loads(row["members"])):
            blocked = "changed since its slim copy"
        else:
            blocked = None
        plan.append({"project": project, "sid": sid, "bytes": sum(s["size"] for s in stats),
                     "age_days": round((now - newest) / 86400), "blocked": blocked, "row": row})
    return plan


def retire(cfg: Config, apply: bool = False) -> dict:
    """Dry run unless apply. Applied, under the lock: plan again, re-read each eligible session's slim copy, then
    rename its top-level entries (<id>.jsonl, <id>/, <id>.*) into trash/<day>/<project>/ on the same volume."""
    day = time.strftime("%Y-%m-%d", time.localtime(cfg.clock()))
    moved = []
    if not apply:
        plan = retire_plan(cfg)
    else:
        with locked(cfg):
            plan = retire_plan(cfg)
            for p in plan:
                if p["blocked"]:
                    continue
                try:
                    slim_ok(cfg, p["row"])
                except Exception as e:
                    p["blocked"] = f"slim copy fails its re-read: {type(e).__name__}: {e}"
                    alert(cfg, "retire refused", f"{p['project']}/{p['sid']}: {p['blocked']}", p["project"], p["sid"])
                    continue
                pdir = cfg.projects / p["project"]
                dst = cfg.root / "trash" / day / p["project"]
                names = sorted(e.name for e in os.scandir(pdir) if (m := UUID_RE.match(e.name)) and m.group(1) == p["sid"])
                if any((dst / n).exists() for n in names):
                    p["blocked"] = "already in today's trash"
                    continue
                dst.mkdir(parents=True, exist_ok=True)
                for n in names:
                    os.rename(pdir / n, dst / n)
                with db(cfg) as con:
                    con.execute("INSERT INTO events VALUES (?,?,?,?,?)",
                                (cfg.clock(), "retired", p["project"], p["sid"],
                                 f"trash/{day}/{p['project']}: {len(names)} entries, {p['bytes']} bytes"))
                moved.append(p)
    blocked = [p for p in plan if p["blocked"]]
    return {"day": day if apply else None, "eligible": len(plan) - len(blocked), "blocked": len(blocked),
            "moved": len(moved), "moved_bytes": sum(p["bytes"] for p in moved),
            "eligible_bytes": sum(p["bytes"] for p in plan if not p["blocked"]),
            "reasons": dict(Counter(p["blocked"].split(":")[0] for p in blocked))}


def untrash(cfg: Config, day: str) -> int:
    """Move a day's retired sessions back into projects/; refuses, moving nothing, if anything would be overwritten."""
    src = cfg.root / "trash" / day
    with locked(cfg):
        moves = [(e, cfg.projects / pdir.name / e.name) for pdir in sorted(src.iterdir()) if pdir.is_dir()
                 for e in sorted(pdir.iterdir())]
        clash = [str(t) for _, t in moves if os.path.lexists(t)]
        if clash:
            raise FileExistsError(f"untrash {day}: {len(clash)} entries would be overwritten, first {clash[0]}")
        for s, t in moves:
            t.parent.mkdir(parents=True, exist_ok=True)
            os.rename(s, t)
        for pdir in src.iterdir():
            pdir.rmdir()
        src.rmdir()
        with db(cfg) as con:
            for project, sid in sorted({(t.parent.name, UUID_RE.match(t.name).group(1)) for _, t in moves}):
                con.execute("INSERT INTO events VALUES (?,?,?,?,?)", (cfg.clock(), "untrashed", project, sid, day))
    return len(moves)


def purge_trash(cfg: Config) -> list[str]:
    """Delete the trash folders at least TRASH_DAYS old. Run by hand only."""
    trash = cfg.root / "trash"
    removed = []
    if not trash.is_dir():
        return removed
    with locked(cfg):
        for d in sorted(trash.iterdir()):
            try:
                when = time.mktime(time.strptime(d.name, "%Y-%m-%d"))
            except ValueError:
                continue
            if cfg.clock() - when >= TRASH_DAYS * 86400:
                shutil.rmtree(d)
                removed.append(d.name)
        with db(cfg) as con:
            for name in removed:
                con.execute("INSERT INTO events VALUES (?,?,?,?,?)", (cfg.clock(), "trash purged", None, None, name))
    return removed


# --------------------------------------------------------------------------------------------- read and stats

def _text_of(content) -> list[tuple[str, str]]:
    if isinstance(content, str):
        return [("text", content)]
    out = []
    for b in content or []:
        if not isinstance(b, dict):
            continue
        t = b.get("type")
        if t == "text":
            out.append(("text", b.get("text") or ""))
        elif t == "thinking":
            out.append(("thinking", b.get("thinking") or ""))
        elif t == "tool_use":
            out.append(("tool_use", f"`{b.get('name')}` {json.dumps(b.get('input'), ensure_ascii=False)[:400]}"))
        elif t == "tool_result":
            c = b.get("content")
            parts = [c] if isinstance(c, str) else [x.get("text", "[image]" if x.get("type") == "image" else "")
                                                    for x in c or [] if isinstance(x, dict)]
            out.append(("tool_result", " ".join(p for p in parts if p)[:400]))
    return out


def render(cfg: Config, sid_prefix: str, thinking: bool = False, subagents: bool = False) -> str:
    with db(cfg) as con:
        rows = [dict(r) for r in con.execute(
            "SELECT * FROM slim WHERE sid LIKE ? ORDER BY generation DESC", (sid_prefix + "%",))]
    sids = {r["sid"] for r in rows}
    if len(sids) != 1:
        raise SystemExit(f"geniza: {len(sids)} sessions match {sid_prefix!r}")
    row = rows[0]
    sid = row["sid"]
    main = f"{sid}.jsonl"
    head, title, out, member = None, None, [], None
    for rec in read_slim(cfg.root / row["path"]):  # streamed: a 1.4 GB session is 288k records
        t = rec.get("type")
        if head is None:
            head = rec
            continue
        if t == "geniza-end":
            continue
        if t == "geniza-member":
            member = rec["path"]
            if subagents and member != main and rec.get("kind") == "jsonl":
                out.append(f"\n## {member}\n")
            continue
        if member != main and not subagents:
            continue
        if t == "custom-title":
            title = rec.get("customTitle") or title
        elif t == "ai-title" and not title:
            title = rec.get("aiTitle")
        elif t in ("user", "assistant") and not rec.get("isMeta"):
            stamp = (rec.get("timestamp") or "")[:19].replace("T", " ")
            for kind, text in _text_of((rec.get("message") or {}).get("content")):
                if kind == "thinking" and not thinking:
                    continue
                if not text.strip():
                    continue
                if kind == "text":
                    out.append(f"**{t}** {stamp}\n\n{text}\n")
                elif kind == "thinking":
                    out.append("> " + text.replace("\n", "\n> ") + "\n")
                elif kind == "tool_use":
                    out.append(f"→ {text}\n")
                else:
                    out.append(f"← {text}\n")
    top = [f"# {title or sid}", "",
           f"`{sid}` · {head['project']} · generation {row['generation']} · {row['records']} records", ""]
    return SURROGATE_RE.sub("\N{REPLACEMENT CHARACTER}", "\n".join(top + out))


def stats(cfg: Config) -> dict:
    with db(cfg) as con:
        r = con.execute("SELECT COUNT(DISTINCT project||'/'||sid), COUNT(*), COALESCE(SUM(raw_bytes),0), "
                        "COALESCE(SUM(slim_bytes),0) FROM slim").fetchone()
        last = con.execute("SELECT finished, result FROM runs WHERE cmd='sweep' ORDER BY finished DESC LIMIT 1").fetchone()
    return {"sessions": r[0], "generations": r[1], "raw_bytes": r[2], "slim_bytes": r[3],
            "free_bytes": shutil.disk_usage(cfg.root).free if cfg.root.exists() else None,
            "last_sweep": dict(last) if last else None}


# --------------------------------------------------------------------------------------------- CLI

def config_from_env(**kw) -> Config:
    env = os.environ
    return Config(root=pathlib.Path(env.get("GENIZA_ROOT", HOME / ".local" / "share" / "geniza")),
                  projects=pathlib.Path(env.get("GENIZA_PROJECTS", HOME / ".claude" / "projects")),
                  now=float(env["GENIZA_NOW"]) if env.get("GENIZA_NOW") else None,
                  free_floor_bytes=int(float(env.get("GENIZA_FREE_FLOOR_GB", "20")) * 10 ** 9),
                  log_dir=pathlib.Path(env.get("GENIZA_LOG_DIR", HOME / "Library" / "Logs" / "geniza")), **kw)


def _capture(args) -> int:
    if args.stdin:
        try:
            payload = json.loads(sys.stdin.read() or "{}")
        except ValueError:
            return 0
        tp = payload.get("transcript_path") or ""
        sid = payload.get("session_id") or ""
        if not (tp and UUID_RE.match(sid)):
            return 0
        cfg = config_from_env()
        cfg.log_dir.mkdir(parents=True, exist_ok=True)
        log = open(cfg.log_dir / "capture.log", "a")
        # --flag=value: project folders start with "-" (-Users-…), which argparse would read as an option
        subprocess.Popen([sys.executable, "-I", os.path.abspath(__file__), "capture", f"--session={sid}",
                          f"--project={pathlib.Path(tp).parent.name}"], stdin=subprocess.DEVNULL, stdout=log,
                         stderr=log, start_new_session=True)
        return 0
    cfg = config_from_env(quiet_s=30.0, lock_timeout=900.0)
    key = (args.project, args.session)
    deadline = time.time() + 900
    while time.time() < deadline:  # wait for the transcript to settle: the hook payload may lag the last turn
        members = enumerate_sessions(cfg.projects).get(key, [])
        st = stat_manifest(cfg.projects / args.project, members)
        if st and time.time() - max(s["mtime_ns"] for s in st) / 1e9 >= cfg.quiet_s:
            break
        time.sleep(5)
    r = sweep(cfg, only={key})
    print(time.strftime("%Y-%m-%dT%H:%M:%S"), "capture", args.session, json.dumps(r), flush=True)
    return 0


def main(argv=None) -> int:
    os.umask(0o077)  # transcripts carry secrets: every file and folder geniza makes is the owner's alone
    p = argparse.ArgumentParser(prog="geniza", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sweep")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--session")
    c = sub.add_parser("capture")
    c.add_argument("--stdin", action="store_true")
    c.add_argument("--session")
    c.add_argument("--project")
    v = sub.add_parser("verify")
    v.add_argument("--all", action="store_true")
    v.add_argument("--sample", type=int)
    v.add_argument("--session")
    k = sub.add_parser("check")
    k.add_argument("--brief", action="store_true")
    r = sub.add_parser("read")
    r.add_argument("sid")
    r.add_argument("--thinking", action="store_true")
    r.add_argument("--subagents", action="store_true")
    sub.add_parser("hourly")
    t = sub.add_parser("retire")
    t.add_argument("--apply", action="store_true")
    t.add_argument("--list", action="store_true", help="every session past 90 days, eligible or blocked")
    u = sub.add_parser("untrash")
    u.add_argument("day")
    sub.add_parser("purge-trash")
    sub.add_parser("stats")
    sub.add_parser("reindex")
    a = p.parse_args(argv)
    if a.cmd == "capture":
        return _capture(a)
    cfg = config_from_env()
    if a.cmd == "sweep":
        only = None
        if a.session:
            only = {k for k in enumerate_sessions(cfg.projects) if k[1].startswith(a.session)}
        try:
            res = sweep(cfg, only=only, dry_run=a.dry_run)
        except Locked as e:
            print(f"geniza: {e}", file=sys.stderr)
            return 0
        print(time.strftime("%Y-%m-%dT%H:%M:%S"), "sweep", json.dumps(res), flush=True)
        return 1 if res.get("errors") else 0
    if a.cmd == "verify":
        res = verify(cfg, all_=a.all, sample=a.sample, sid=a.session)
        print(json.dumps(res))
        return 1 if res["failed"] else 0
    if a.cmd == "check":
        if a.brief:  # SessionStart: one line, only when something is wrong; never fails the session's start
            problems = brief_problems(cfg)
            if problems:
                print(f"geniza: {len(problems)} problem(s): {problems[0]}" + (" …" if len(problems) > 1 else ""))
            return 0
        problems = check(cfg)
        print("\n".join(problems) if problems else "geniza: all checks pass")
        return 1 if problems else 0
    if a.cmd == "retire":
        if a.list:
            for p in sorted(retire_plan(cfg), key=lambda p: (p["blocked"] is not None, p["project"], p["sid"])):
                print(f"{'eligible' if p['blocked'] is None else 'blocked '}\t{p['sid']}\t{p['project']}\t"
                      f"{p['age_days']} d\t{p['bytes']}\t{p['blocked'] or ''}")
            return 0
        print(time.strftime("%Y-%m-%dT%H:%M:%S"), "retire" + (" --apply" if a.apply else " (dry run)"),
              json.dumps(retire(cfg, apply=a.apply)), flush=True)
        return 0
    if a.cmd == "untrash":
        print(f"geniza: moved {untrash(cfg, a.day)} entries back from trash/{a.day}")
        return 0
    if a.cmd == "purge-trash":
        print(f"geniza: purged {purge_trash(cfg) or 'nothing'}")
        return 0
    if a.cmd == "hourly":
        try:
            out = hourly(cfg)
        except Locked as e:
            print(time.strftime("%Y-%m-%dT%H:%M:%S"), f"hourly: {e}", flush=True)
            return 0
        print(time.strftime("%Y-%m-%dT%H:%M:%S"), "hourly", json.dumps(out), flush=True)
        return 0
    if a.cmd == "read":
        print(render(cfg, a.sid, thinking=a.thinking, subagents=a.subagents))
        return 0
    if a.cmd == "stats":
        print(json.dumps(stats(cfg), indent=2))
        return 0
    if a.cmd == "reindex":
        print(f"geniza: reindexed {reindex(cfg)} slim files")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
