"""From a stage and its knobs to the argv of `loop_seq.py`: knobs coerced, flags, the output and its .part twin."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, log, rel, sha256_file, write_json
from reveal_studio.jobs.candidates import candidate, candidates, rounds
from reveal_studio.jobs.plans import resolve_plan
from reveal_studio.jobs.store import job_root, prep_dir
from reveal_studio.registry.schema import NAME_RE

STILL_RE = re.compile(r"^k\d+\.png$")
"""A registered still of the prep folder: k<i>.png."""


@dataclass(frozen=True)
class ScriptFlags:
    """Which of the studio's default-off flags the research script carries, read from its --help at start."""

    progress: bool = False
    frames: bool = False
    readers: bool = False

    def as_dict(self) -> dict[str, bool]:
        return {"progress": self.progress, "frames": self.frames, "readers": self.readers}


def script_arg(settings: Settings) -> str:
    """The script as the argv names it: repo-relative, run with the repo root as the working folder."""
    return rel(settings.loop_seq, settings.root)


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
            else:
                out[key] = str(v)
        except (TypeError, ValueError):
            raise StudioError(f"knob {key} takes a {k['type']}, not {v!r}", 400) from None
    for key, k in known.items():
        out.setdefault(key, list(k["default"]) if isinstance(k["default"], list) else k["default"])
    return out


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
        else:
            out += [k["flag"], str(v)]
    return out


def argv_for(
    settings: Settings, flags: ScriptFlags, stage: Json, d: Path, job: Json, knobs: Json, rec_dir: Path
) -> tuple[list[str], Path, Path, list[Json]]:
    """The argv, the final output path, its .part twin and the inputs of one run of a stage."""
    root, seq, name = job_root(settings, job), job["seq"], stage["name"]
    py, script = str(settings.python), script_arg(settings)
    prep = prep_dir(settings, job)
    argv: list[str]
    inputs: list[Json]
    if name == "registration":
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
    elif name == "readers":
        if not flags.readers:
            raise StudioError(f"{script} has no readers command yet (its --help does not list it)", 501)
        if not (prep / "prep.json").exists():
            raise StudioError("registration first: no prep.json", 409)
        out_final, out_part = prep / "readers", prep / "readers.part"
        argv = [py, script, "readers", rel(prep, settings.root), "--out", rel(out_part, settings.root)]
        inputs = [{"path": rel(prep / "prep.json", settings.root), "sha256": sha256_file(prep / "prep.json")}]
    elif name == "probe":
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
    elif name == "measure":
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
    elif name == "render":
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
    elif name == "page":
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
    else:
        raise StudioError(f"the {name} stage is not a process", 400)
    return argv, out_final, out_part, inputs
