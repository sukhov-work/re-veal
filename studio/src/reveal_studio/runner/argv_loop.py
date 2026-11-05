"""The loop flow's argv: one function per script stage of `loop_seq.py`, moved verbatim from runner/argv.py's chain
(phase B's slice, 2026-11-05; tests/test_loop_snapshot.py pins the result on the fake job).

Each takes what runner.argv.argv_for takes and returns the argv, the final output path, its .part twin and the inputs.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, rel, sha256_file, write_json
from reveal_studio.jobs.candidates import candidate, candidates, rounds
from reveal_studio.jobs.plans import resolve_plan
from reveal_studio.jobs.store import job_root, prep_dir
from reveal_studio.registry.schema import NAME_RE
from reveal_studio.runner.argv import Argv, ScriptFlags, flags_of, script_arg

STILL_RE = re.compile(r"^k\d+\.png$")
"""A registered still of the prep folder: k<i>.png."""


def argv_registration(
    settings: Settings, flags: ScriptFlags, stage: Json, d: Path, job: Json, knobs: Json, rec_dir: Path
) -> Argv:
    seq = job["seq"]
    py, script = str(settings.python), script_arg(settings)
    prep = prep_dir(settings, job)
    src = d / "raw" / seq
    if not src.is_dir():
        raise StudioError("this job has no raw stills to register (an adopted job reads its prep in place)", 409)
    out_final, out_part = prep, prep.with_name(seq + ".part")
    argv = [
        py,
        script,
        "prep",
        rel(src, settings.root),
        "--out",
        rel(out_part, settings.root),
        *flags_of(stage, knobs),
    ]
    inputs = [{"path": i["path"], "sha256": i["sha256"]} for i in job["inputs"]]
    return argv, out_final, out_part, inputs


def argv_readers(
    settings: Settings, flags: ScriptFlags, stage: Json, d: Path, job: Json, knobs: Json, rec_dir: Path
) -> Argv:
    py, script = str(settings.python), script_arg(settings)
    prep = prep_dir(settings, job)
    if not flags.readers:
        raise StudioError(f"{script} has no readers command yet (its --help does not list it)", 501)
    if not (prep / "prep.json").exists():
        raise StudioError("registration first: no prep.json", 409)
    out_final, out_part = prep / "readers", prep / "readers.part"
    argv = [py, script, "readers", rel(prep, settings.root), "--out", rel(out_part, settings.root)]
    inputs = [{"path": rel(prep / "prep.json", settings.root), "sha256": sha256_file(prep / "prep.json")}]
    return argv, out_final, out_part, inputs


def argv_probe(
    settings: Settings, flags: ScriptFlags, stage: Json, d: Path, job: Json, knobs: Json, rec_dir: Path
) -> Argv:
    py, script = str(settings.python), script_arg(settings)
    prep = prep_dir(settings, job)
    if not (prep / "prep.json").exists():
        raise StudioError("registration first: no prep.json", 409)
    stills = sorted((p for p in prep.glob("k*.png") if STILL_RE.match(p.name)), key=lambda p: int(p.stem[1:]))
    if len(stills) < 2:
        raise StudioError("the probe needs two registered stills or more", 409)
    out_final, out_part = prep / "probe", prep / "probe.part"  # a rerun replaces the folder (the readers rule)
    argv = [
        py,
        script,
        "probe",
        rel(prep, settings.root),
        "--out",
        rel(out_part, settings.root),
        *flags_of(stage, knobs),
    ]
    inputs = [{"path": rel(prep / "prep.json", settings.root), "sha256": sha256_file(prep / "prep.json")}]
    inputs += [{"path": rel(k, settings.root), "sha256": sha256_file(k)} for k in stills]
    return argv, out_final, out_part, inputs


def argv_measure(
    settings: Settings, flags: ScriptFlags, stage: Json, d: Path, job: Json, knobs: Json, rec_dir: Path
) -> Argv:
    name = stage["name"]
    py, script = str(settings.python), script_arg(settings)
    kind, _, rname = str(knobs.get("render") or "").partition(":")
    if not rname:
        raise StudioError("choose the render to measure: full:<name> or draft:<name>", 400)
    c = candidate(settings, d, job, kind, rname)
    mp4 = c["dir"] / "loop.mp4"
    if not mp4.is_file():
        raise StudioError(f"{rel(mp4, settings.root)} is missing: nothing to measure", 409)
    # a new folder under the render per run, named by the record's stamp; the render's own files are never written
    tag = rec_dir.name.replace(f"_{name}", "", 1)
    out_final, out_part = c["dir"] / "measures" / tag, c["dir"] / "measures" / (tag + ".part")
    argv = [py, script, "measure", rel(mp4, settings.root), "--out", rel(out_part, settings.root)]
    inputs = [{"path": rel(mp4, settings.root), "md5": c["md5_mp4"]}]
    frames_json = c["dir"] / "frames.json"
    if frames_json.is_file():
        argv += ["--frames-json", rel(frames_json, settings.root)]
        inputs.append({"path": rel(frames_json, settings.root), "sha256": sha256_file(frames_json)})
    argv += flags_of(stage, knobs)
    return argv, out_final, out_part, inputs


def argv_render(
    settings: Settings, flags: ScriptFlags, stage: Json, d: Path, job: Json, knobs: Json, rec_dir: Path
) -> Argv:
    root, seq = job_root(settings, job), job["seq"]
    py, script = str(settings.python), script_arg(settings)
    prep = prep_dir(settings, job)
    if not (prep / "prep.json").exists():
        raise StudioError("registration first: no prep.json", 409)
    plan_path = resolve_plan(settings, d, knobs.get("plan"))
    rname = knobs.get("name") or plan_path.stem
    if not NAME_RE.match(rname):
        raise StudioError("a render name is letters, digits, dash and underscore", 400)
    draft, fps = int(knobs.get("draft", 0)), int(knobs.get("fps", 25))
    base = (root / "drafts" / seq) if draft else (root / seq)
    out_final, out_part = base / rname, base / (rname + ".part")
    argv = [
        py,
        script,
        "render",
        rel(plan_path, settings.root),
        "--out",
        rel(out_part, settings.root),
        "--fps",
        str(fps),
        "--draft",
        str(draft),
        "--set",
        f'in="{rel(prep, settings.root)}"',
    ]
    if flags.progress:
        argv.append("--progress")
    if flags.frames:
        argv.append("--frames")
    inputs = [
        {"path": rel(plan_path, settings.root), "sha256": sha256_file(plan_path)},
        {"path": rel(prep / "prep.json", settings.root), "sha256": sha256_file(prep / "prep.json")},
    ]
    return argv, out_final, out_part, inputs


def argv_page(
    settings: Settings, flags: ScriptFlags, stage: Json, d: Path, job: Json, knobs: Json, rec_dir: Path
) -> Argv:
    root, seq = job_root(settings, job), job["seq"]
    py, script = str(settings.python), script_arg(settings)
    out_final, out_part = root / "index.html", root / "index.part.html"
    notes: Any = knobs.get("notes") or {}
    if not isinstance(notes, dict):
        raise StudioError("notes is {candidate: text}", 400)
    write_json(rec_dir / "notes.json", {seq: notes})
    n = len(rounds(d)) + 1
    argv = [
        py,
        script,
        "page",
        "--root",
        rel(root, settings.root),
        "--out",
        rel(out_part, settings.root),
        "--order",
        seq,
        "--title",
        knobs.get("title") or f"{seq}: round {n}",
        "--intro",
        knobs.get("intro") or "",
        "--footer",
        knobs.get("footer") or "",
        "--notes",
        rel(rec_dir / "notes.json", settings.root),
    ]
    variants = list(knobs.get("variants") or [])
    if variants:  # backlog T76: only these full renders, in this order (views/page.py checked the names)
        argv += ["--variants", ",".join(variants)]
    full = {c["name"]: c for c in candidates(settings, d, job) if c["kind"] == "full"}
    listed = [full[v] for v in variants if v in full] if variants else list(full.values())
    inputs = [{"path": rel(c["dir"] / "loop.mp4", settings.root), "md5": c["md5_mp4"]} for c in listed]
    return argv, out_final, out_part, inputs


LOOP_ARGV: dict[str, Callable[[Settings, ScriptFlags, Json, Path, Json, Json, Path], Argv]] = {
    "registration": argv_registration,
    "readers": argv_readers,
    "probe": argv_probe,
    "measure": argv_measure,
    "render": argv_render,
    "page": argv_page,
}


def argv_for(
    settings: Settings, flags: ScriptFlags, stage: Json, d: Path, job: Json, knobs: Json, rec_dir: Path
) -> Argv:
    """The loop stage's argv; a script stage without a builder here is refused as no process."""
    fn = LOOP_ARGV.get(stage["name"])
    if fn is None:
        raise StudioError(f"the {stage['name']} stage is not a process", 400)
    return fn(settings, flags, stage, d, job, knobs, rec_dir)
