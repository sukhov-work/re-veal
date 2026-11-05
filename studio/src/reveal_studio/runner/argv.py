"""From a stage and its knobs to the argv of its script: knobs coerced, flags, the output and its .part twin.

argv_for dispatches: a shared stage (registry/common.py) to runner/argv_common.py, any other stage to its job's flow
module (argv_loop.py, argv_pair.py, argv_director.py), each holding one function per script stage. The loop's script
flags are probed from `loop_seq.py --help` at start (ScriptFlags).
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, log, rel

Argv = tuple[list[str], Path, Path, list[Json]]
"""What a stage's argv builder returns: the argv, the final output path, its .part twin, the inputs."""
SCRIPTS = ("loop_seq", "transitions", "reveal", "director_render", "director_page")
"""The Settings keys a stage's `script` may name."""
SET_KEY_RE = re.compile(r"^[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)?$")
"""A key of an object knob: one dotted segment at most (director_render.py routes `--set` on the first dot)."""


@dataclass(frozen=True)
class ScriptFlags:
    """Which of the studio's default-off flags the research script carries, read from its --help at start."""

    progress: bool = False
    frames: bool = False
    readers: bool = False

    def as_dict(self) -> dict[str, bool]:
        return {"progress": self.progress, "frames": self.frames, "readers": self.readers}


def script_arg(settings: Settings) -> str:
    """The loop script as the argv names it: repo-relative, run with the repo root as the working folder."""
    return rel(settings.loop_seq, settings.root)


def script_rel(settings: Settings, key: str) -> str:
    """The script a stage's `script` key names, as the argv names it (repo-relative)."""
    if key not in SCRIPTS:
        raise StudioError(f"a stage's script is one of {list(SCRIPTS)}, not {key!r}", 500)
    path: Path = getattr(settings, key)
    return rel(path, settings.root)


def probe_script_flags(settings: Settings) -> ScriptFlags:
    """Which of the studio's default-off flags the research script carries (its --help is the truth)."""
    script = script_arg(settings)
    progress = frames = readers = False
    try:
        h = subprocess.run(
            [str(settings.python), script, "render", "--help"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(settings.root),
        ).stdout
        progress = "--progress" in h
        frames = "--frames" in h
        h2 = subprocess.run(
            [str(settings.python), script, "--help"], capture_output=True, text=True, timeout=60, cwd=str(settings.root)
        ).stdout
        readers = "readers" in h2
    except (OSError, subprocess.SubprocessError) as e:
        log(f"could not probe {script} --help: {e}")
    flags = ScriptFlags(progress=progress, frames=frames, readers=readers)
    missing = [k for k, v in flags.as_dict().items() if not v]
    log(
        f"{script}: progress {flags.progress}, frames {flags.frames}, readers {flags.readers}"
        + (
            f" (missing: {', '.join(missing)}; "
            "the strip shows no progress number and the scrubber decodes the mp4 itself)"
            if missing
            else ""
        )
    )
    return flags


def coerce(stage: Json, knobs: Json | None) -> Json:
    """The knobs typed by the registry, every missing knob at its default; `override` and `notes` pass through."""
    out: Json = {}
    known = {k["key"]: k for k in stage["knobs"]}
    for key, v in (knobs or {}).items():
        if key in ("override", "notes"):
            out[key] = v
            continue
        if key not in known:
            raise StudioError(f"the {stage['name']} stage has no knob {key!r}; its knobs are {sorted(known)}", 400)
        k = known[key]
        try:
            if k["type"] == "int":
                out[key] = int(v)
            elif k["type"] == "float":
                out[key] = float(v)
            elif k["type"] == "bool":
                out[key] = bool(v) if not isinstance(v, str) else v.lower() in ("1", "true", "yes", "on")
            elif k["type"] == "list":
                out[key] = as_list(v)
            elif k["type"] == "object":
                out[key] = as_object(v)
            else:
                out[key] = str(v)
        except (TypeError, ValueError):
            raise StudioError(f"knob {key} takes a {k['type']}, not {v!r}", 400) from None
    for key, k in known.items():
        d = k["default"]
        out.setdefault(key, list(d) if isinstance(d, list) else dict(d) if isinstance(d, dict) else d)
    return out


def as_object(v: Any) -> Json:
    """An object knob: a JSON object (or its text) whose keys have one dotted segment at most; the values any JSON."""
    obj = json.loads(v) if isinstance(v, str) else v
    if not isinstance(obj, dict) or not all(isinstance(k, str) and SET_KEY_RE.match(k) for k in obj):
        raise TypeError("a JSON object whose keys are names with one dot at most")
    return dict(obj)


def as_list(v: Any) -> list[str]:
    """A list knob: a JSON list of names or one comma-separated string; each name stripped, empty names dropped."""
    items = v.split(",") if isinstance(v, str) else v
    if not isinstance(items, list) or not all(isinstance(x, str) for x in items):
        raise TypeError("a list of names")
    return [x.strip() for x in items if x.strip()]


def flags_of(stage: Json, knobs: Json) -> list[str]:
    """The script flags of the knobs that carry one: a true bool as the bare flag, an empty string left out."""
    out: list[str] = []
    for k in stage["knobs"]:
        if not k["flag"]:
            continue
        v = knobs.get(k["key"], k["default"])
        if k["type"] == "bool":
            if v:
                out.append(k["flag"])
        elif k["type"] == "str":
            if v != "":
                out += [k["flag"], str(v)]
        elif k["type"] == "list":
            if v:
                out += [k["flag"], ",".join(v)]
        elif k["type"] == "object":
            # one flag per key, keys in sorted order: the argv is the same for one dict whatever order the page sent
            # its keys in (the renderer keeps the last value of a repeated key, so the order cannot change a render)
            for key in sorted(v):
                out += [k["flag"], f"{key}={json.dumps(v[key])}"]
        else:
            out += [k["flag"], str(v)]
    return out


ArgvFn = Callable[[Settings, ScriptFlags, Json, Path, Json, Json, Path], Argv]


def builder_of(flow: str, name: str) -> ArgvFn:
    """The argv function of a stage: the shared stage's of that name, else the job's flow module's."""
    # imported here: each flow module imports ScriptFlags, flags_of and the script names from this module
    from reveal_studio.runner import argv_common, argv_director, argv_loop, argv_pair

    if name in argv_common.ARGV:
        return argv_common.ARGV[name]
    flows: dict[str, ArgvFn] = {
        "loop": argv_loop.argv_for,
        "pair": argv_pair.argv_for,
        "director": argv_director.argv_for,
    }
    if flow not in flows:
        raise StudioError(f"no argv for the {flow} flow", 501)
    return flows[flow]


def argv_for(
    settings: Settings, flags: ScriptFlags, stage: Json, d: Path, job: Json, knobs: Json, rec_dir: Path
) -> Argv:
    """The argv, the final output path, its .part twin and the inputs of one run of a stage."""
    return builder_of(job["flow"], stage["name"])(settings, flags, stage, d, job, knobs, rec_dir)
