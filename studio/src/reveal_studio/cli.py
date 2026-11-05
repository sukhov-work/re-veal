"""reveal-studio: serve the studio, list the open requests, or check the resolved settings.

  reveal-studio serve [--port 8380] [--no-browser] [--root PATH] [--runs-date YYYY-MM-DD] [--lock PATH] [--second]
                      [--layers-dir PATH] [--mattes-dir PATH]
  reveal-studio requests [--root PATH]      the open requests across every job, with their age
  reveal-studio check [--root PATH]         the resolved settings; exit 1 when the root, the python or the
                                            loop script is missing (any other missing path prints MISSING)

With no command, `serve` runs (as the research script did). Settings come from the flags, then the environment
(REVEAL_STUDIO_ROOT, REVEAL_STUDIO_PY, REVEAL_STUDIO_PORT, REVEAL_STUDIO_LOCK, REVEAL_STUDIO_RUNS_DATE,
REVEAL_STUDIO_LAYERS_DIR, REVEAL_STUDIO_MATTES_DIR), then discovery (the first folder at or above the working folder
holding reveal.py and AGENTS.md).
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from pathlib import Path

from reveal_studio import __version__
from reveal_studio.config import ConfigError, Settings, resolve_settings
from reveal_studio.fs import md5_file, rel
from reveal_studio.jobs.store import job_dirs
from reveal_studio.runner.argv import probe_script_flags
from reveal_studio.runner.lock import LockHeld
from reveal_studio.server.app import HOST, serve
from reveal_studio.views.models import open_requests

COMMANDS = ("serve", "requests", "check")


def _parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", help="the repo root (default: discovered from the working folder)")
    common.add_argument("--port", type=int, default=None, help="the port on 127.0.0.1 (default 8380)")
    common.add_argument(
        "--runs-date",
        default=None,
        help="the benchmarks/runs/<date>/studio/ folder new jobs are made in (default: today)",
    )
    common.add_argument("--lock", default=None, help="the lock file (default benchmarks/runs/studio.lock)")
    common.add_argument(
        "--layers-dir",
        default=None,
        help="the layer tables' root the director flow passes on (default benchmarks/runs/2026-09-28/layers_v3)",
    )
    common.add_argument(
        "--mattes-dir",
        default=None,
        help="the mattes' root the director flow passes on (default benchmarks/runs/2026-10-17/mattes)",
    )
    ap = argparse.ArgumentParser(
        prog="reveal-studio", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--version", action="version", version=f"reveal-studio {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sv = sub.add_parser("serve", parents=[common], help="serve the page on 127.0.0.1")
    sv.add_argument("--no-browser", action="store_true", help="do not open the browser")
    sv.add_argument(
        "--second",
        action="store_true",
        help="allow a second server on this tree (a review); two servers may reconcile the same record",
    )
    sub.add_parser("requests", parents=[common], help="list the open requests across every job")
    sub.add_parser("check", parents=[common], help="print the resolved settings and the script's flags")
    return ap


def _settings(a: argparse.Namespace) -> Settings:
    return resolve_settings(
        root=a.root,
        port=a.port,
        lock=a.lock,
        runs_date=a.runs_date,
        layers_dir=a.layers_dir,
        mattes_dir=a.mattes_dir,
        open_browser=not getattr(a, "no_browser", False),
    )


def cmd_requests(settings: Settings) -> int:
    rows = open_requests(settings)
    if not rows:
        print("no open requests")
        return 0
    for r in rows:
        age = r["age_s"]
        age_t = (
            f"{age // 3600} h {age % 3600 // 60} min"
            if age >= 3600
            else f"{age // 60} min"
            if age >= 60
            else f"{age} s"
        )
        print(
            f"{age_t:>12}  {r['job']}  {r['file']}  {r['kind']}: {r['brief'][:90]}"
            + (f"  [{', '.join(r['candidates'])}]" if r["candidates"] else "")
        )
    print(f"{len(rows)} open request(s); the oldest {rows[0]['age_s'] // 60} min")
    return 0


PAIR_RE = re.compile(r"^(.+)_S\.[^.]+$")
"""A fixture pair's first photo, <group>_<N>_S.<ext>; its second is <group>_<N>_F.<ext>."""


def fixture_pairs(folder: Path) -> list[str]:
    """The fixture pairs of a folder: every <name>_S.<ext> beside a <name>_F.<ext>, in name order."""
    names = sorted({m.group(1) for p in folder.glob("*_S.*") if (m := PAIR_RE.match(p.name))})
    return [n for n in names if any(folder.glob(f"{n}_F.*"))]


def photo_folders(folder: Path, pattern: str) -> int:
    """The child folders that hold a file matching `pattern`; a folder whose name starts with _ is skipped."""
    return sum(1 for c in folder.iterdir() if c.is_dir() and not c.name.startswith("_") and any(c.glob(pattern)))


def _script_row(label: str, p: Path, root: Path) -> str:
    return f"{label:<13} " + (f"{rel(p, root)} md5 {md5_file(p)}" if p.is_file() else f"{p} (MISSING)")


def _folder_row(label: str, p: Path, root: Path, what: str) -> str:
    return f"{label:<13} " + (f"{rel(p, root)} ({what})" if p.is_dir() else f"{p} (MISSING)")


def flow_rows(settings: Settings) -> list[str]:
    """The pair and director flows' paths, each with its md5 or a count, or MISSING; none changes the exit code."""
    s, root = settings, settings.root
    rows = [
        _script_row("transitions", s.transitions, root),
        _script_row("reveal", s.reveal, root),
        _script_row("director", s.director_render, root),
        _script_row("director page", s.director_page, root),
    ]
    plans = len(list(s.director_plans.glob("*.json"))) if s.director_plans.is_dir() else 0
    rows.append(_folder_row("director plans", s.director_plans, root, f"{plans} plans"))
    pairs = len(fixture_pairs(s.fixtures)) if s.fixtures.is_dir() else 0
    rows.append(_folder_row("fixtures", s.fixtures, root, f"{pairs} pairs"))
    layers = photo_folders(s.layers_dir, "layers.json") if s.layers_dir.is_dir() else 0
    rows.append(_folder_row("layers", s.layers_dir, root, f"{layers} photo folders with layers.json"))
    mattes = photo_folders(s.mattes_dir, "el_*.png") if s.mattes_dir.is_dir() else 0
    rows.append(_folder_row("mattes", s.mattes_dir, root, f"{mattes} photo folders with el_<id>.png"))
    return rows


def cmd_check(settings: Settings) -> int:
    """Prints the resolved settings; 1 when the main venv's python or the loop script is missing. A missing path of
    the pair or director flows prints MISSING and leaves the exit code alone."""
    py_ok = settings.python.exists()
    script_ok = settings.loop_seq.is_file()
    root = settings.root
    print(f"reveal-studio {__version__}")
    print(f"root          {root}")
    print(
        f"python        {settings.python} "
        f"({'exists' if py_ok else 'MISSING: the main venv; run ./setup.sh at the root'})"
    )
    if script_ok:
        print(f"loop_seq      {rel(settings.loop_seq, root)} md5 {md5_file(settings.loop_seq)}")
    else:
        print(f"loop_seq      {settings.loop_seq} (MISSING)")
    print(f"runs          {rel(settings.runs, root)} ({len(job_dirs(settings))} job(s) under */studio/)")
    print(f"frozen plans  {rel(settings.frozen_plans, root)} ({len(list(settings.frozen_plans.glob('*.json')))} plans)")
    for row in flow_rows(settings):
        print(row)
    print(f"serves        http://{HOST}:{settings.port}/ (lock {settings.lock_path})")
    print(f"runs date     {settings.runs_date}")
    print(f"ui version    {settings.ui_version}")
    if py_ok and script_ok:
        flags = probe_script_flags(settings)
        print("script flags  " + ", ".join(f"{k} {'yes' if v else 'no'}" for k, v in flags.as_dict().items()))
    else:
        print("script flags  not probed (the python or the script is missing)")
    return 0 if py_ok and script_ok else 1


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or (args[0] not in COMMANDS and args[0] not in ("-h", "--help", "--version")):
        args = ["serve", *args]
    a = _parser().parse_args(args)
    try:
        settings = _settings(a)
    except ConfigError as e:
        print(f"reveal-studio: {e}", file=sys.stderr)
        return 1
    if a.cmd == "requests":
        return cmd_requests(settings)
    if a.cmd == "check":
        return cmd_check(settings)
    try:
        return serve(settings, second=a.second)
    except LockHeld as e:
        print(f"reveal-studio: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"reveal-studio: cannot serve on {HOST}:{settings.port}: {e}", file=sys.stderr)
        return 1
