"""Settings: the repo root, the main venv's python, the research script and the job folders, resolved once.

Resolution order for every setting: an explicit argument (the CLI's flag) > the environment (REVEAL_STUDIO_ROOT,
REVEAL_STUDIO_PY, REVEAL_STUDIO_PORT, REVEAL_STUDIO_LOCK, REVEAL_STUDIO_RUNS_DATE) > discovery > an error that
names what is missing. Discovery of the root walks up from the working folder for a folder holding both
`reveal.py` and `AGENTS.md`, then up from this package's own location (the last resort; nothing else in the
package reads its own path to find the repo).
"""

from __future__ import annotations

import datetime as dt
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from reveal_studio import __version__

DEFAULT_PORT = 8380
BODY_CAP = 2 * 1024 * 1024
ROOT_MARKERS = ("reveal.py", "AGENTS.md")
ENV_ROOT = "REVEAL_STUDIO_ROOT"
ENV_PY = "REVEAL_STUDIO_PY"
ENV_PORT = "REVEAL_STUDIO_PORT"
ENV_LOCK = "REVEAL_STUDIO_LOCK"
ENV_RUNS_DATE = "REVEAL_STUDIO_RUNS_DATE"
LOOP_SEQ = Path("scripts/research/loop_seq.py")
RUNS = Path("benchmarks/runs")
FROZEN_PLANS = Path("scripts/research/plans/loops")
LOCK_NAME = "studio.lock"


class ConfigError(Exception):
    """The settings cannot be resolved; the message names the missing file, folder or value."""


@dataclass(frozen=True)
class Settings:
    """Where everything is. Every module takes this (or the App that holds it) explicitly."""

    root: Path
    python: Path
    loop_seq: Path
    runs: Path
    frozen_plans: Path
    port: int
    lock_path: Path
    runs_date: str
    ui_version: str
    body_cap: int
    open_browser: bool


def missing_markers(folder: Path) -> list[str]:
    """The marker files of a Reveal repo root that `folder` lacks (empty for a root)."""
    return [m for m in ROOT_MARKERS if not (folder / m).is_file()]


def discover_root(cwd: Path, package_file: Path | None = None) -> Path | None:
    """The first folder at or above `cwd`, then above `package_file`, that holds reveal.py and AGENTS.md."""
    cwd = cwd.resolve()
    for d in (cwd, *cwd.parents):
        if not missing_markers(d):
            return d
    if package_file is not None:
        for d in package_file.resolve().parents:
            if not missing_markers(d):
                return d
    return None


def _port(value: str | int, source: str) -> int:
    try:
        port = int(value)
    except (TypeError, ValueError):
        raise ConfigError(f"the port from {source} is not a number: {value!r}") from None
    if not 0 < port < 65536:
        raise ConfigError(f"the port from {source} is outside 1..65535: {port}")
    return port


def _absolute(p: str | Path, cwd: Path) -> Path:
    q = Path(p).expanduser()
    return q if q.is_absolute() else cwd / q


def resolve_settings(
    *,
    root: str | Path | None = None,
    python: str | Path | None = None,
    port: int | None = None,
    lock: str | Path | None = None,
    runs_date: str | None = None,
    open_browser: bool = True,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
    package_file: Path | None = None,
) -> Settings:
    """Settings from the arguments, then the environment, then discovery; ConfigError names what is missing."""
    env = os.environ if env is None else env
    cwd = Path.cwd() if cwd is None else cwd
    if package_file is None:
        package_file = Path(__file__)
    if root is not None:
        source, found = "--root", _absolute(root, cwd)
    elif env.get(ENV_ROOT):
        source, found = ENV_ROOT, _absolute(env[ENV_ROOT], cwd)
    else:
        source = "discovery"
        discovered = discover_root(cwd, package_file)
        if discovered is None:
            raise ConfigError(
                f"no repo root: no folder at or above {cwd}, or above the package, holds both "
                f"{' and '.join(ROOT_MARKERS)}; pass --root PATH or set {ENV_ROOT}"
            )
        found = discovered
    if not found.is_dir():
        raise ConfigError(f"the root {found} (from {source}) is not a folder")
    missing = missing_markers(found)
    if missing:
        raise ConfigError(
            f"the root {found} (from {source}) has no {' and no '.join(missing)}: "
            f"a Reveal repo root holds {' and '.join(ROOT_MARKERS)}"
        )
    found = found.resolve()
    if python is not None:
        py = _absolute(python, cwd)
    elif env.get(ENV_PY):
        py = _absolute(env[ENV_PY], cwd)
    else:
        py = found / ".venv/bin/python"
    if port is not None:
        the_port = _port(port, "--port")
    elif env.get(ENV_PORT):
        the_port = _port(env[ENV_PORT], ENV_PORT)
    else:
        the_port = DEFAULT_PORT
    if lock is not None:
        lock_path = _absolute(lock, cwd)
    elif env.get(ENV_LOCK):
        lock_path = _absolute(env[ENV_LOCK], cwd)
    else:
        lock_path = found / RUNS / LOCK_NAME
    date = runs_date or env.get(ENV_RUNS_DATE) or dt.date.today().isoformat()
    return Settings(
        root=found,
        python=py,
        loop_seq=found / LOOP_SEQ,
        runs=found / RUNS,
        frozen_plans=found / FROZEN_PLANS,
        port=the_port,
        lock_path=lock_path,
        runs_date=date,
        ui_version=f"reveal-studio {__version__}",
        body_cap=BODY_CAP,
        open_browser=open_browser,
    )
