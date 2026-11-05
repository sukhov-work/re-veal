"""Stage records: stages/<stamp>_<name>/stage.json, its log, its outputs with md5s, and the record's pure view."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, md5_file, read_json, rel, tail_lines
from reveal_studio.registry.schema import ID_RE


def records(d: Path) -> list[Json]:
    """Every readable stage.json of the job, in start order."""
    out = []
    for sj in (d / "stages").glob("*/stage.json"):
        r = read_json(sj)
        if r:
            out.append(r)
    return sorted(out, key=lambda r: (r.get("started") or "", r["id"]))


def record_dir(d: Path, rid: str) -> Path:
    if not ID_RE.match(rid or ""):
        raise StudioError("bad record id", 400)
    p = d / "stages" / rid
    if not (p / "stage.json").exists():
        raise StudioError(f"no record {rid}", 404)
    return p


def outputs_of(settings: Settings, p: Path) -> list[Json]:
    """The file, or every visible file of the folder, with its md5 and size."""
    p = Path(p)
    if p.is_file():
        return [{"path": rel(p, settings.root), "md5": md5_file(p), "bytes": p.stat().st_size}]
    out = []
    for f in sorted(p.iterdir()):
        if f.is_file() and not f.name.startswith("."):
            out.append({"path": rel(f, settings.root), "md5": md5_file(f), "bytes": f.stat().st_size})
    return out


def progress_of(rec_dir: Path) -> Json | None:
    """The last `PROGRESS i n [phase]` line of the record's log, or None."""
    for line in reversed(tail_lines(rec_dir / "log.txt", 300)):
        if line.startswith("PROGRESS "):
            parts = line.split()
            try:
                return {"i": int(parts[1]), "n": int(parts[2]), "phase": parts[3] if len(parts) > 3 else ""}
            except (IndexError, ValueError):
                return None
    return None


def command_line(argv: list[Any]) -> str:
    """The argv as one shell line: an argument with a space or a double quote is single-quoted."""
    return " ".join(
        a if " " not in a and '"' not in a else "'" + a.replace("'", "'\\''") + "'" for a in (str(x) for x in argv)
    )


def elapsed_of(rec: Json) -> float | None:
    """Seconds since the record started, or None when its start time does not parse."""
    try:
        return round((dt.datetime.now() - dt.datetime.fromisoformat(rec["started"])).total_seconds(), 1)
    except (KeyError, TypeError, ValueError):
        return None


def record_detail(d: Path, rec: Json) -> Json:
    """The record as the inspector shows it: progress, the log's tail, the elapsed time, the reproducing command.

    The pure part of `views.job.record_view`, which reconciles the record first.
    """
    rec_dir = d / "stages" / rec["id"]
    v = dict(rec)
    v["progress"] = progress_of(rec_dir) if rec["state"] == "running" else None
    v["log_tail"] = tail_lines(rec_dir / "log.txt", 12)
    if rec["state"] == "running":
        v["elapsed_s"] = elapsed_of(rec)
    v["command"] = command_line(rec["argv"])
    return v
