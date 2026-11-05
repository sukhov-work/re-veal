"""File helpers every layer shares: digests, JSON read and atomic write, repo-relative paths, log tails, timestamps."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

Json = dict[str, Any]
"""A record as the job folder stores it: job.json, stage.json, round.json, a request, a view."""


def log(msg: str) -> None:
    print(f"studio: {msg}", file=sys.stderr, flush=True)


def now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="milliseconds")


def stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def md5_file(p: str | Path) -> str:
    """The md5 of a file: an identity for outputs (never a security check)."""
    h = hashlib.md5(usedforsecurity=False)
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha256_file(p: str | Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_json(p: str | Path, default: Any = None) -> Any:
    """The parsed file, or `default` when it is missing or not JSON."""
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return default


def write_json(p: str | Path, obj: Any) -> None:
    """Writes to a .tmp twin and renames it, so a reader never sees half a record."""
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1))
    os.replace(tmp, p)


def rel(p: str | Path, root: Path) -> str:
    """A path as the repo-relative string the records carry; a path outside `root` stays as given."""
    p = Path(p)
    try:
        return str(p.resolve().relative_to(root))
    except ValueError:
        return str(p)


def inside(p: str | Path, base: str | Path) -> bool:
    try:
        Path(p).resolve().relative_to(Path(base).resolve())
        return True
    except ValueError:
        return False


def tail_lines(p: str | Path, n: int = 20) -> list[str]:
    """The last `n` lines of the file's last 16 KiB (an empty list when it cannot be read)."""
    try:
        data = Path(p).read_bytes()[-16384:]
    except OSError:
        return []
    lines = data.decode("utf-8", "replace").splitlines()
    return lines[-n:]
