"""The pair flow's argv: one function per script stage of `transitions.py pair`, in the shape of runner/argv_loop.py.

The relation: `transitions.py pair A B --out <root>/relation.part --max-long 480 --seconds 1`, the workbench's read of
the pair (scripts/research/director_ui.py:446), every other option at the CLI's default; a rerun replaces the folder.
The render: `transitions.py pair A B --out <root>/<pair>/<name>.part --max-long N` and the knobs' flags, where N is the
`draft` knob when it is above 0 (the render then goes under drafts/<pair>/) and the `max_long` knob otherwise; neither
knob carries a flag of its own, so the argv holds one --max-long. A and B are the job's links (raw/<pair>/A.<ext>,
which keep the extension transitions.py picks its reader by); the inputs are the originals with their sha256s. The
shared stages (Reveal's verdict) never reach this module: runner.argv.argv_for routes them to argv_common.py first.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, rel
from reveal_studio.jobs.store import job_root
from reveal_studio.registry.pair import RELATION_LONG, RELATION_SECONDS, RESERVED_NAMES
from reveal_studio.registry.schema import NAME_RE
from reveal_studio.runner.argv import Argv, ScriptFlags, flags_of, script_rel

RESERVED = RESERVED_NAMES
"""The job folder's own folders: a pair of one of these names would put its full renders inside a folder another
stage writes, and a rerun of the relation or the verdict replaces its folder whole."""


def photos(job: Json) -> tuple[Json, Json]:
    """The job's inputs A and B; 409 when either is missing (a job made by hand)."""
    by = {i.get("role"): i for i in job.get("inputs") or []}
    if "A" not in by or "B" not in by:
        raise StudioError("a pair job needs its two photos, A and B", 409)
    return by["A"], by["B"]


def _inputs(a: Json, b: Json) -> list[Json]:
    return [{"path": a["path"], "sha256": a["sha256"]}, {"path": b["path"], "sha256": b["sha256"]}]


def argv_relation(
    settings: Settings, flags: ScriptFlags, stage: Json, d: Path, job: Json, knobs: Json, rec_dir: Path
) -> Argv:
    a, b = photos(job)
    root = job_root(settings, job)
    out_final, out_part = root / "relation", root / "relation.part"
    argv = [
        str(settings.python),
        script_rel(settings, stage["script"]),
        "pair",
        a.get("link") or a["path"],
        b.get("link") or b["path"],
        "--out",
        rel(out_part, settings.root),
        "--max-long",
        str(RELATION_LONG),
        "--seconds",
        str(RELATION_SECONDS),
    ]
    return argv, out_final, out_part, _inputs(a, b)


def render_name(knobs: Json) -> str:
    """The knob `name`, else <preset>_<seconds>s with the seconds' point as p (1.5 s gives morph_1p5s)."""
    name = str(knobs.get("name") or "").strip()
    if name:
        return name
    return f"{knobs.get('preset') or 'morph'}_{float(knobs.get('seconds') or 1.0):g}s".replace(".", "p")


def argv_render(
    settings: Settings, flags: ScriptFlags, stage: Json, d: Path, job: Json, knobs: Json, rec_dir: Path
) -> Argv:
    a, b = photos(job)
    root, seq = job_root(settings, job), job["seq"]
    if seq in RESERVED:
        raise StudioError(
            f"the pair's name {seq!r} is a folder of the job itself, so its renders would sit inside another stage's "
            "folder: make the job again under another name",
            409,
        )
    name = render_name(knobs)
    if not NAME_RE.match(name):
        raise StudioError("a render name is letters, digits, dash and underscore (60 at most)", 400)
    draft, max_long = int(knobs.get("draft") or 0), int(knobs.get("max_long") or 0)
    if draft < 0 or max_long < 0:
        raise StudioError("draft and max_long are 0 or a long edge in px", 400)
    base = (root / "drafts" / seq) if draft else (root / seq)
    out_final, out_part = base / name, base / (name + ".part")
    argv = [
        str(settings.python),
        script_rel(settings, stage["script"]),
        "pair",
        a.get("link") or a["path"],
        b.get("link") or b["path"],
        "--out",
        rel(out_part, settings.root),
        "--max-long",
        str(draft or max_long),
        *flags_of(stage, knobs),
    ]
    return argv, out_final, out_part, _inputs(a, b)


PAIR_ARGV: dict[str, Callable[[Settings, ScriptFlags, Json, Path, Json, Json, Path], Argv]] = {
    "relation": argv_relation,
    "render": argv_render,
}


def argv_for(
    settings: Settings, flags: ScriptFlags, stage: Json, d: Path, job: Json, knobs: Json, rec_dir: Path
) -> Argv:
    """The pair stage's argv; a script stage without a builder here is refused as no process."""
    fn = PAIR_ARGV.get(stage["name"])
    if fn is None:
        raise StudioError(f"the {stage['name']} stage is not a process", 400)
    return fn(settings, flags, stage, d, job, knobs, rec_dir)
