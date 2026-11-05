"""The director flow's argv (builder D): one function per script stage, in the shape of runner/argv_loop.py. The shared
stages (Reveal's verdict) never reach this module: runner.argv.argv_for routes them to argv_common.py first.

- resolve: `director_render.py PLAN <job>/resolve/<stamp>.part --resolve-only --concept C --max-long N [--set k=v ...]
  --layers-dir L --mattes-dir M`, renamed to `<job>/resolve/<stamp>`: outside run/, since director_page.py lists every
  child of run/ that holds an info.json and a resolve's info.json has no measures (director_page.py:41, 87-91).
- render: `director_render.py PLAN <out>.part --concept C --max-long N --seconds S --fps F [--set k=v ...] --progress
  --layers-dir L --mattes-dir M`; a full render into `<job>/run/<stem>_<concept>[-<tag>]`, a draft (knob `draft` above
  0, its long edge) into `<job>/drafts/<stem>_<concept>[-<tag>]`.
- page: `director_page.py <job>/run --notes <record>/notes.json --title T --key K [--head H] [--keyframes J]`, written
  in place (out_final == out_part == run/index.html): the Runner copies the previous page beside the record first.

Before the script starts: the concept is checked against the plan (director_render.py renders the first concept for an
unknown name, D:2095), a `--set` key that reaches no frame is refused (registry/director.set_key_problem), and fewer
than 3 frames are refused (the measures index steps[1], D:2052). The layer and matte roots come from the settings on
every resolve and render. The record keeps the plan's full sha256 (info.json keeps 16 characters) and the md5 of
transitions.py, which the renderer imports.
"""

from __future__ import annotations

import html
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, inside, md5_file, read_json, rel, sha256_file, write_json
from reveal_studio.jobs.candidates import candidates, rounds
from reveal_studio.jobs.plans import resolve_plan
from reveal_studio.jobs.store import job_root
from reveal_studio.registry.director import set_key_problem
from reveal_studio.registry.schema import NAME_RE
from reveal_studio.runner.argv import Argv, ScriptFlags, flags_of, script_rel

TAG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*$")
"""A render's tag: letters, digits and dashes, no underscore (director_page.py:44 splits the folder at its last
underscore, :71 keeps the concept before the first dash)."""
CONCEPT_RE = re.compile(r"^[A-Za-z0-9]+$")
"""A concept id a render folder can carry: the page reads it back between the last underscore and the first dash."""
MIN_FRAMES = 3


def director_plan(settings: Settings, d: Path, ref: Any) -> tuple[Path, Json]:
    """The plan a director stage names (job:<name> or frozen:<stem>) and its JSON, with one concept or more."""
    path = resolve_plan(settings, d, ref, "director")
    plan = read_json(path)
    if not isinstance(plan, dict) or not isinstance(plan.get("concepts"), list) or not plan["concepts"]:
        raise StudioError(f"{rel(path, settings.root)} holds no concepts", 400)
    return path, plan


def concept_of(plan: Json, path: Path, name: Any) -> Json:
    """The named concept, or the plan's first for an empty name; an unknown name is refused (400)."""
    concepts = [c for c in plan["concepts"] if isinstance(c, dict)]
    if not name:
        return concepts[0]
    for c in concepts:
        if c.get("id") == name:
            return c
    ids = [c.get("id") for c in concepts]
    raise StudioError(
        f"the plan {path.stem} has no concept {name!r} (its concepts: {ids}); director_render.py would render the "
        "first one without a word",
        400,
        {"concepts": ids},
    )


def check_set(knobs: Json, concept: Json) -> None:
    """Refuses (400) the `set` keys that reach no frame for this concept, every reason in one message."""
    names = [str(t.get("name")) for t in concept.get("transforms") or [] if isinstance(t, dict)]
    problems = {k: p for k in sorted(knobs.get("set") or {}) if (p := set_key_problem(k, names))}
    if problems:
        raise StudioError("; ".join(problems.values()), 400, {"refused_keys": sorted(problems)})


def frozen_stem(settings: Settings, path: Path) -> str:
    """The frozen stem a render folder carries: a frozen plan's own; a plan saved in the job, its source's, because
    director_page.py reads the plan by the folder's stem from scripts/research/plans/ only (P:18, P:58-65)."""
    frozen = settings.director_plans.resolve()
    if path.resolve().parent == frozen:
        return path.stem
    src = ((read_json(path) or {}).get("provenance") or {}).get("from")
    if isinstance(src, str) and src:
        p = settings.root / src
        if p.resolve().parent == frozen and p.is_file():
            return p.stem
    raise StudioError(
        "a plan saved in this job renders under its source's frozen stem (director_page.py reads "
        "scripts/research/plans/<stem>.json); this plan's provenance names no frozen director plan",
        400,
    )


def roots_flags(settings: Settings) -> list[str]:
    """--layers-dir and --mattes-dir from the settings, on every resolve and render (D:2089-2092)."""
    return [
        "--layers-dir",
        rel(settings.layers_dir, settings.root),
        "--mattes-dir",
        rel(settings.mattes_dir, settings.root),
    ]


def set_flags(stage: Json, knobs: Json) -> list[str]:
    """One `--set k=<json>` per key of the stage's object knob `set`, keys in sorted order (runner/argv.flags_of)."""
    knob = next(k for k in stage["knobs"] if k["key"] == "set")
    return flags_of({"knobs": [knob]}, knobs)


def _photo(job: Json, role: str) -> Json | None:
    return next((i for i in job.get("inputs") or [] if i.get("role") == role), None)


def read_inputs(settings: Settings, job: Json, plan_path: Path, concept: Json) -> list[Json]:
    """What a resolve or a render reads: the plan (full sha256), transitions.py (md5), the two photos as the renderer
    finds them under fixtures/ and the helper pictures the concept names."""
    out: list[Json] = [{"path": rel(plan_path, settings.root), "sha256": sha256_file(plan_path)}]
    if settings.transitions.is_file():
        out.append({"path": rel(settings.transitions, settings.root), "md5": md5_file(settings.transitions)})
    for role in ("A", "B"):
        i = _photo(job, role)
        if i and Path(i["path"]).is_file():
            out.append({"path": rel(i["path"], settings.root), "sha256": sha256_file(i["path"]), "role": role})
    for h in _keyframes(concept, []):
        p = settings.root / h
        if p.is_file():
            out.append({"path": h, "sha256": sha256_file(p), "helper": True})
    return out


def _keyframes(o: Any, out: list[str]) -> list[str]:
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "keyframes" and isinstance(v, list):
                out += [x for x in v if isinstance(x, str) and x not in out]
            else:
                _keyframes(v, out)
    elif isinstance(o, list):
        for v in o:
            _keyframes(v, out)
    return out


def argv_resolve(
    settings: Settings, flags: ScriptFlags, stage: Json, d: Path, job: Json, knobs: Json, rec_dir: Path
) -> Argv:
    plan_path, plan = director_plan(settings, d, knobs.get("plan"))
    concept = concept_of(plan, plan_path, knobs.get("concept"))
    check_set(knobs, concept)
    tag = rec_dir.name.replace(f"_{stage['name']}", "", 1)
    out_final, out_part = d / "resolve" / tag, d / "resolve" / (tag + ".part")
    argv = [
        str(settings.python),
        script_rel(settings, stage["script"]),
        rel(plan_path, settings.root),
        rel(out_part, settings.root),
        "--resolve-only",
        "--concept",
        str(concept["id"]),
        "--max-long",
        str(int(knobs.get("max_long") or 1920)),
        *set_flags(stage, knobs),
        *roots_flags(settings),
    ]
    return argv, out_final, out_part, read_inputs(settings, job, plan_path, concept)


def render_folder(settings: Settings, plan_path: Path, concept: Json, tag: Any) -> str:
    """<frozen stem>_<concept>[-<tag>]: the name director_page.py reads the plan and the concept back from."""
    cid = str(concept.get("id"))
    if not CONCEPT_RE.match(cid):
        raise StudioError(
            f"the concept id {cid!r} has an underscore or a dash: director_page.py cannot read it back", 400
        )
    tag = str(tag or "")
    if tag and not TAG_RE.match(tag):
        raise StudioError(
            "a render's tag is letters, digits and dashes (no underscore: director_page.py splits there)", 400
        )
    name = f"{frozen_stem(settings, plan_path)}_{cid}" + (f"-{tag}" if tag else "")
    if not NAME_RE.match(name):
        raise StudioError(f"the folder name {name} is over 60 characters or holds a character a name cannot", 400)
    return name


def argv_render(
    settings: Settings, flags: ScriptFlags, stage: Json, d: Path, job: Json, knobs: Json, rec_dir: Path
) -> Argv:
    plan_path, plan = director_plan(settings, d, knobs.get("plan"))
    concept = concept_of(plan, plan_path, knobs.get("concept"))
    check_set(knobs, concept)
    seconds, fps = float(knobs.get("seconds", 3.0)), int(knobs.get("fps", 30))
    frames = round(seconds * fps)
    if frames < MIN_FRAMES:
        raise StudioError(
            f"{seconds:g} s at {fps} fps is {frames} frames; the renderer's measures need {MIN_FRAMES} or more", 400
        )
    draft = int(knobs.get("draft") or 0)
    long_side = draft if draft > 0 else int(knobs.get("max_long") or 1920)
    name = render_folder(settings, plan_path, concept, knobs.get("name"))
    base = (d / "drafts") if draft > 0 else job_root(settings, job)
    out_final, out_part = base / name, base / (name + ".part")
    argv = [
        str(settings.python),
        script_rel(settings, stage["script"]),
        rel(plan_path, settings.root),
        rel(out_part, settings.root),
        "--concept",
        str(concept["id"]),
        "--max-long",
        str(long_side),
        "--seconds",
        str(seconds),
        "--fps",
        str(fps),
        *set_flags(stage, knobs),
        "--progress",
        *roots_flags(settings),
    ]
    return argv, out_final, out_part, read_inputs(settings, job, plan_path, concept)


def page_notes(d: Path, names: list[str], given: Any) -> Json:
    """notes.json for director_page.py, {<render folder>: {look, faults}}: the skeptic's answers in time order (the
    look and faults it wrote per candidate), then the page's own notes, a text as `look` or an object of the two."""
    out: Json = {}
    for a in sorted((d / "answers").glob("skeptic_*.json")):
        for name, v in ((read_json(a) or {}).get("candidates") or {}).items():
            if name in names and isinstance(v, dict):
                out.setdefault(name, {}).update({k: str(v[k]) for k in ("look", "faults") if v.get(k)})
    if not isinstance(given, dict):
        raise StudioError("notes is {render: text} or {render: {look, faults}}", 400)
    for name, v in given.items():
        if name not in names:
            continue
        if isinstance(v, str) and v.strip():
            out.setdefault(name, {})["look"] = v.strip()
        elif isinstance(v, dict):
            out.setdefault(name, {}).update({k: str(v[k]) for k in ("look", "faults") if v.get(k)})
    return out


def _repo_file(settings: Settings, given: str, what: str) -> Path:
    p = Path(given).expanduser()
    p = p if p.is_absolute() else settings.root / p
    if not p.is_file() or not inside(p, settings.root):
        raise StudioError(f"{what} {given} is not a file inside the repo", 400)
    return p


def argv_page(
    settings: Settings, flags: ScriptFlags, stage: Json, d: Path, job: Json, knobs: Json, rec_dir: Path
) -> Argv:
    if knobs.get("variants"):
        raise StudioError("director_page.py lists every full render of run/ and takes no list of variants", 400)
    root = job_root(settings, job)
    full = [c for c in candidates(settings, d, job) if c["kind"] == "full"]
    names = [c["name"] for c in full]
    write_json(rec_dir / "notes.json", page_notes(d, names, knobs.get("notes") or {}))
    n = len(rounds(d)) + 1
    argv = [
        str(settings.python),
        script_rel(settings, stage["script"]),
        rel(root, settings.root),
        "--notes",
        rel(rec_dir / "notes.json", settings.root),
        "--title",
        str(knobs.get("title") or f"{job['seq']}: round {n}"),
        "--key",
        str(knobs.get("key") or f"{job['id']}_r{n}"),
    ]
    head = _repo_file(settings, str(knobs["head"]), "the head file").read_text() if knobs.get("head") else ""
    if knobs.get("override"):  # the gate's override is printed on the page, as the loop prints it in its footer
        head += f"\n<p class=override><b>{html.escape(str(knobs['override']))}</b></p>\n"
    if head:
        (rec_dir / "head.html").write_text(head)
        argv += ["--head", rel(rec_dir / "head.html", settings.root)]
    if knobs.get("keyframes"):
        argv += ["--keyframes", rel(_repo_file(settings, str(knobs["keyframes"]), "the keyframes file"), settings.root)]
    page = root / "index.html"
    inputs = [{"path": rel(c["dir"] / c["mp4"], settings.root), "md5": c["md5_mp4"]} for c in full]
    return argv, page, page, inputs


DIRECTOR_ARGV: dict[str, Callable[[Settings, ScriptFlags, Json, Path, Json, Json, Path], Argv]] = {
    "resolve": argv_resolve,
    "render": argv_render,
    "page": argv_page,
}


def argv_for(
    settings: Settings, flags: ScriptFlags, stage: Json, d: Path, job: Json, knobs: Json, rec_dir: Path
) -> Argv:
    """The director stage's argv; a stage without a builder here is refused as no process."""
    fn = DIRECTOR_ARGV.get(stage["name"])
    if fn is None:
        raise StudioError(f"the director flow's {stage['name']} stage is not a process", 400)
    return fn(settings, flags, stage, d, job, knobs, rec_dir)
