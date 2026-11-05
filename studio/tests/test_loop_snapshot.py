"""The loop path as literals, pinned on the tree of 2026-11-05 before phase B's generalization slice and held after it.

Pinned: the argv, the output paths and the inputs of every loop run on the fake job (registration, readers, probe,
measure with and without frames.json, render full and draft, page with and without variants), the stage tiles of
two jobs (a new one and one that went through every stage), their rail rows and the rounds, and digests of the loop's
registry rows (the stages without the slice's two new keys, the hints without its two chip keys, the plan schema and
the rulings). A value that holds a time, a stamp or a digest of a time-dependent file is replaced by a token first.

The argv come from argv_for itself on a fixed record folder, after coerce, as start_stage builds them; the tiles from
stage_views after real runs of the fake script through the Runner.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from reveal_studio.config import Settings, resolve_settings
from reveal_studio.fs import Json, md5_file, write_json
from reveal_studio.jobs.candidates import candidates, rounds
from reveal_studio.jobs.grades import save_grade, write_request
from reveal_studio.jobs.store import create_job
from reveal_studio.registry.hints import HINTS
from reveal_studio.registry.loop import LOOP_STAGES
from reveal_studio.registry.rulings import RULINGS
from reveal_studio.registry.schema import PLAN_SCHEMA
from reveal_studio.runner.argv import argv_for, coerce
from reveal_studio.runner.process import Runner
from reveal_studio.views.job import job_row, stage_views
from reveal_studio.views.page import build_page

from .conftest import FLAGS, free_port, make_root, wait_for, wait_record, write_stills

try:  # the slice moves stage_def from registry.loop to registry.flows; this file runs on both trees unchanged
    from reveal_studio.registry.flows import stage_def
except ImportError:  # the tree before the slice
    from reveal_studio.registry.loop import stage_def

SLICE_STAGE_KEYS = ("script", "identity")
"""The keys the slice adds to a stage definition; the digest of the loop's stages leaves them out."""
SLICE_HINT_KEYS = ("chip.above_6", "chip.above_10")
"""The hint rows the slice adds (the still-count chips); the digest of the loop's 290 rows leaves them out."""

STAMP = re.compile(r"\d{8}-\d{6}")
SUFFIX = re.compile(r"(<stamp>_[a-z]+)_\d+\b")
"""A record started in the same second as another of its stage takes a _2, _3 suffix: timing, not the loop path."""
ISO = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?")
HEX64 = re.compile(r"\b[0-9a-f]{64}\b")
HEX32 = re.compile(r"\b[0-9a-f]{32}\b")
SHORT_MD5 = re.compile(r"md5 [0-9a-f]{8}…")
TIMED = ("wall_s", "elapsed_s", "age_s")


def scrub(x: Any, swaps: list[tuple[str, str]]) -> Any:
    """Every string with the swaps applied (the tmp folder, the python), then stamps, ISO times and hex digests as
    tokens; a time in seconds as '<s>'."""
    if isinstance(x, dict):
        return {k: ("<s>" if k in TIMED and v is not None else scrub(v, swaps)) for k, v in x.items()}
    if isinstance(x, list):
        return [scrub(v, swaps) for v in x]
    if isinstance(x, str):
        s = x
        for old, new in swaps:
            s = s.replace(old, new)
        s = ISO.sub("<iso>", s)
        s = SUFFIX.sub(r"\1", STAMP.sub("<stamp>", s))
        s = HEX64.sub("<sha256>", s)
        s = HEX32.sub("<md5>", s)
        return SHORT_MD5.sub("md5 <md5>…", s)
    return x


def digest(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:16]


@contextmanager
def env(**kv: str) -> Iterator[None]:
    """The fake script's steering variables for the runs inside the block (the Runner passes os.environ on)."""
    old = {k: os.environ.get(k) for k in kv}
    os.environ.update(kv)
    try:
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def run(runner: Runner, d: Path, job: Json, stage: str, knobs: Json | None = None) -> Json:
    rec = runner.start_stage(d, job, stage_def("loop", stage), knobs or {})
    time.sleep(0.01)  # the stale rule compares start times at millisecond resolution
    return wait_record(d, rec["id"])


def argv_of(settings: Settings, d: Path, job: Json, stage: str, knobs: Json) -> Json:
    """argv_for on a fixed record folder after coerce, as start_stage calls it; the paths as the record keeps them."""
    sdef = stage_def("loop", stage)
    rec_dir = d / "stages" / f"20261105-000000_{stage}"
    rec_dir.mkdir(parents=True, exist_ok=True)
    argv, out_final, out_part, inputs = argv_for(settings, FLAGS, sdef, d, job, coerce(sdef, knobs), rec_dir)
    root = str(settings.root) + "/"
    return {
        "argv": argv,
        "out_final": str(out_final).replace(root, ""),
        "out_part": str(out_part).replace(root, ""),
        "inputs": inputs,
    }


def views_of(runner: Runner, d: Path, job: Json) -> Json:
    """The job's tiles (each tile's sentence and knobs, the registry's own, as a digest), rail row and rounds."""
    tiles = stage_views(runner, d, job)
    return {
        "tiles": [{k: v for k, v in t.items() if k not in ("what", "knobs")} for t in tiles],
        "registry": [digest([t["what"], t["knobs"]]) for t in tiles],
        "row": job_row(runner.settings, d, runner),
        "rounds": rounds(d),
    }


def build(tmp: Path) -> Json:
    """On a fresh tmp root: the argv of every loop run; the views of a new job, of a job through every stage, and of
    that job after a later registration (the stale rule); all scrubbed."""
    root = make_root(tmp)
    settings = resolve_settings(
        root=root, port=free_port(), lock=tmp / "studio.lock", runs_date="2026-11-05", open_browser=False, env={}
    )
    runner = Runner(settings, FLAGS)
    fresh = create_job(settings, "loop", folder=str(write_stills(tmp / "Fresh Stills")), seq="fresh")
    j = create_job(settings, "loop", folder=str(write_stills(tmp / "Tiny Stills", 3)), seq="tiny")
    d = settings.root / j["root"]
    argv: Json = {"registration": argv_of(settings, d, j, "registration", {"ref": 0, "lock_window": "1,2,10,12"})}
    assert run(runner, d, j, "registration", {"depth_maps": True})["state"] == "done"
    argv["readers"] = argv_of(settings, d, j, "readers", {})
    assert run(runner, d, j, "readers", {})["state"] == "done"
    argv["probe"] = argv_of(settings, d, j, "probe", {"long": 480, "pairs": "0,1;1,2"})
    assert run(runner, d, j, "probe", {})["state"] == "done"
    argv["render_full"] = argv_of(settings, d, j, "render", {"plan": "frozen:tiny_a1", "name": "c1"})
    c1 = run(runner, d, j, "render", {"plan": "frozen:tiny_a1", "name": "c1"})
    assert c1["state"] == "done" and c1["script_md5"] == md5_file(settings.loop_seq)
    draft = {"plan": "frozen:tiny_a1", "name": "d1", "draft": 480, "fps": 30}
    argv["render_draft"] = argv_of(settings, d, j, "render", draft)
    assert run(runner, d, j, "render", draft)["state"] == "done"
    assert run(runner, d, j, "render", {"plan": "frozen:tiny_a1", "name": "c2"})["state"] == "done"
    (d / "drafts" / "tiny" / "d1" / "frames.json").unlink()  # a render without frames.json: the measure's other argv
    argv["measure_frames"] = argv_of(settings, d, j, "measure", {"render": "full:c1", "windows": "w:1,1,9,9"})
    argv["measure_no_frames"] = argv_of(settings, d, j, "measure", {"render": "draft:d1", "ref": 2})
    assert run(runner, d, j, "measure", {"render": "full:c1", "windows": "w:1,1,9,9"})["state"] == "done"
    with env(FAKE_FAIL="render"):
        assert run(runner, d, j, "render", {"plan": "frozen:tiny_a1", "name": "c3"})["state"] == "failed"
    req = write_request(settings, d, j, "skeptic", {"brief": "the halo at mid-leg", "candidates": ["c1", "c2"]})
    md5 = {c["name"]: c["md5_mp4"] for c in candidates(settings, d, j)}
    write_json(
        d / "answers" / req["name"],
        {"at": "t", "candidates": {"c1": {"verdict": "READY", "judged_md5": md5["c1"], "note": "clean"}}},
    )
    argv["page_all"] = argv_of(settings, d, j, "page", {"title": "", "notes": {"c1": "look at the ring"}})
    argv["page_variants"] = argv_of(settings, d, j, "page", {"variants": ["c2", "c1"], "intro": "two"})
    page = build_page(runner, d, j, {"override": True, "notes": {"c1": "the ring"}})
    assert wait_record(d, page["id"])["state"] == "done"
    wait_for(lambda: (d / "rounds" / "1" / "round.json").is_file())  # the round opens after the record's outputs
    save_grade(d, {"round": 1, "text": "c1 is fine, c2 drifts"})
    time.sleep(0.01)
    page2 = runner.start_stage(d, j, stage_def("loop", "page"), {"variants": ["c1"], "title": "the second round"})
    assert wait_record(d, page2["id"])["state"] == "done"
    wait_for(lambda: (d / "rounds" / "2" / "round.json").is_file())
    out: Json = {"argv": argv, "fresh": views_of(runner, settings.root / fresh["root"], fresh)}
    out["full"] = views_of(runner, d, j)
    out["page_md5_beside_the_page"] = (d / "page.md5").read_text() == md5_file(d / "index.html") + "\n"
    out["round_files"] = sorted(str(p.relative_to(d / "rounds")) for p in (d / "rounds").glob("*/*"))
    time.sleep(0.01)
    assert run(runner, d, j, "registration", {"depth_maps": True})["state"] == "done"
    out["stale"] = views_of(runner, d, j)
    swaps = [(str(tmp.resolve()), "<tmp>"), (str(tmp), "<tmp>"), (str(settings.python), "<py>")]
    return dict(scrub(out, swaps))


def registry_digests() -> Json:
    return {
        "stages": digest([{k: v for k, v in s.items() if k not in SLICE_STAGE_KEYS} for s in LOOP_STAGES]),
        "hints": digest({k: v for k, v in HINTS.items() if k not in SLICE_HINT_KEYS}),
        "hint_count": len([k for k in HINTS if k not in SLICE_HINT_KEYS]),
        "schema": digest(PLAN_SCHEMA),
        "schema_rows": len(PLAN_SCHEMA),
        "rulings": digest(RULINGS),
        "rulings_rows": len(RULINGS),
    }


@pytest.fixture(scope="module")
def snap(tmp_path_factory: pytest.TempPathFactory) -> Json:
    return build(tmp_path_factory.mktemp("snapshot"))


def test_the_argv_of_every_loop_run_is_the_snapshot(snap: Json) -> None:
    """Mutation: a flag dropped, added or moved in the loop's argv chain (argv_for, then argv_loop.py after the slice),
    an output path or an input changed, turns this red; e.g. `--frames-json` emitted after the knob flags."""
    assert sorted(snap["argv"]) == sorted(EXPECTED["argv"])
    for name, expected in EXPECTED["argv"].items():
        assert snap["argv"][name] == expected, name


def _tiles_match(got: Json, want: Json) -> None:
    assert [t["name"] for t in got["tiles"]] == [t["name"] for t in want["tiles"]]
    for g, w in zip(got["tiles"], want["tiles"], strict=True):
        assert g == w, g["name"]
    assert got["registry"] == want["registry"]  # each tile's sentence and knobs as the registry holds them


def test_the_tiles_of_a_new_job_are_the_snapshot(snap: Json) -> None:
    """Mutation: a tile function's empty branch changed (the readers' "optional, not run", the import's raw thumb)."""
    _tiles_match(snap["fresh"], EXPECTED["fresh"])


def test_the_tiles_of_a_job_through_every_stage_are_the_snapshot(snap: Json) -> None:
    """Mutation: a tile reading another source (the probe's dexp line, the measure's peak, the render's last attempt,
    the skeptic's verdicts, the page's round) or a key added to a loop tile turns this red."""
    _tiles_match(snap["full"], EXPECTED["full"])


def test_the_tiles_after_a_later_registration_are_the_snapshot(snap: Json) -> None:
    """Mutation: the stale rule moved without its branch filter or its draft rule (the page's upstream render), or the
    readers' moved folder not looked up, turns this red."""
    _tiles_match(snap["stale"], EXPECTED["stale"])


def test_the_rail_rows_and_the_rounds_are_the_snapshot(snap: Json) -> None:
    """Mutation: open_round writing another key or order into round.json, page.md5 elsewhere than beside the page, or
    the rail row reading another field, turns this red."""
    for job in ("fresh", "full", "stale"):
        assert snap[job]["row"] == EXPECTED[job]["row"], job
        assert snap[job]["rounds"] == EXPECTED[job]["rounds"], job
    assert snap["page_md5_beside_the_page"] is True
    assert snap["round_files"] == EXPECTED["round_files"]


def test_the_loop_registry_rows_keep_their_digests() -> None:
    """Mutation: a sentence, a knob or a default of the loop's stages, hints, schema or rulings edited while the
    registry is split, e.g. one character of a knob's sentence, turns this red."""
    assert registry_digests() == EXPECTED["registry"]


# Generated on 2026-11-05 from build() on tree 4f564b5 before the slice's first edit, then never regenerated.
EXPECTED: Json = {
    "argv": {
        "registration": {
            "argv": [
                "<tmp>/repo/.venv/bin/python",
                "scripts/research/loop_seq.py",
                "prep",
                "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/raw/tiny",
                "--out",
                "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/in/tiny.part",
                "--long",
                "1920",
                "--ref",
                "0",
                "--bg-depth",
                "0.0",
                "--min-inliers",
                "40",
                "--lock-window",
                "1,2,10,12",
            ],
            "out_final": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/in/tiny",
            "out_part": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/in/tiny.part",
            "inputs": [
                {"path": "<tmp>/Tiny Stills/IMG_0001.jpg", "sha256": "<sha256>"},
                {"path": "<tmp>/Tiny Stills/IMG_0002.jpg", "sha256": "<sha256>"},
                {"path": "<tmp>/Tiny Stills/IMG_0003.jpg", "sha256": "<sha256>"},
            ],
        },
        "readers": {
            "argv": [
                "<tmp>/repo/.venv/bin/python",
                "scripts/research/loop_seq.py",
                "readers",
                "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/in/tiny",
                "--out",
                "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/in/tiny/readers.part",
            ],
            "out_final": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/in/tiny/readers",
            "out_part": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/in/tiny/readers.part",
            "inputs": [
                {"path": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/in/tiny/prep.json", "sha256": "<sha256>"}
            ],
        },
        "probe": {
            "argv": [
                "<tmp>/repo/.venv/bin/python",
                "scripts/research/loop_seq.py",
                "probe",
                "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/in/tiny",
                "--out",
                "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/in/tiny/probe.part",
                "--long",
                "480",
                "--pairs",
                "0,1;1,2",
            ],
            "out_final": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/in/tiny/probe",
            "out_part": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/in/tiny/probe.part",
            "inputs": [
                {"path": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/in/tiny/prep.json", "sha256": "<sha256>"},
                {"path": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/in/tiny/k0.png", "sha256": "<sha256>"},
                {"path": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/in/tiny/k1.png", "sha256": "<sha256>"},
                {"path": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/in/tiny/k2.png", "sha256": "<sha256>"},
            ],
        },
        "render_full": {
            "argv": [
                "<tmp>/repo/.venv/bin/python",
                "scripts/research/loop_seq.py",
                "render",
                "scripts/research/plans/loops/tiny_a1.json",
                "--out",
                "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/tiny/c1.part",
                "--fps",
                "25",
                "--draft",
                "0",
                "--set",
                'in="benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/in/tiny"',
                "--progress",
                "--frames",
            ],
            "out_final": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/tiny/c1",
            "out_part": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/tiny/c1.part",
            "inputs": [
                {"path": "scripts/research/plans/loops/tiny_a1.json", "sha256": "<sha256>"},
                {"path": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/in/tiny/prep.json", "sha256": "<sha256>"},
            ],
        },
        "render_draft": {
            "argv": [
                "<tmp>/repo/.venv/bin/python",
                "scripts/research/loop_seq.py",
                "render",
                "scripts/research/plans/loops/tiny_a1.json",
                "--out",
                "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/drafts/tiny/d1.part",
                "--fps",
                "30",
                "--draft",
                "480",
                "--set",
                'in="benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/in/tiny"',
                "--progress",
                "--frames",
            ],
            "out_final": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/drafts/tiny/d1",
            "out_part": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/drafts/tiny/d1.part",
            "inputs": [
                {"path": "scripts/research/plans/loops/tiny_a1.json", "sha256": "<sha256>"},
                {"path": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/in/tiny/prep.json", "sha256": "<sha256>"},
            ],
        },
        "measure_frames": {
            "argv": [
                "<tmp>/repo/.venv/bin/python",
                "scripts/research/loop_seq.py",
                "measure",
                "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/tiny/c1/loop.mp4",
                "--out",
                "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/tiny/c1/measures/<stamp>.part",
                "--frames-json",
                "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/tiny/c1/frames.json",
                "--window",
                "w:1,1,9,9",
                "--ref",
                "0",
            ],
            "out_final": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/tiny/c1/measures/<stamp>",
            "out_part": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/tiny/c1/measures/<stamp>.part",
            "inputs": [
                {"path": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/tiny/c1/loop.mp4", "md5": "<md5>"},
                {
                    "path": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/tiny/c1/frames.json",
                    "sha256": "<sha256>",
                },
            ],
        },
        "measure_no_frames": {
            "argv": [
                "<tmp>/repo/.venv/bin/python",
                "scripts/research/loop_seq.py",
                "measure",
                "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/drafts/tiny/d1/loop.mp4",
                "--out",
                "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/drafts/tiny/d1/measures/<stamp>.part",
                "--ref",
                "2",
            ],
            "out_final": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/drafts/tiny/d1/measures/<stamp>",
            "out_part": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/drafts/tiny/d1/measures/<stamp>.part",
            "inputs": [
                {"path": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/drafts/tiny/d1/loop.mp4", "md5": "<md5>"}
            ],
        },
        "page_all": {
            "argv": [
                "<tmp>/repo/.venv/bin/python",
                "scripts/research/loop_seq.py",
                "page",
                "--root",
                "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>",
                "--out",
                "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/index.part.html",
                "--order",
                "tiny",
                "--title",
                "tiny: round 1",
                "--intro",
                "",
                "--footer",
                "",
                "--notes",
                "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/stages/<stamp>_page/notes.json",
            ],
            "out_final": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/index.html",
            "out_part": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/index.part.html",
            "inputs": [
                {"path": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/tiny/c1/loop.mp4", "md5": "<md5>"},
                {"path": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/tiny/c2/loop.mp4", "md5": "<md5>"},
            ],
        },
        "page_variants": {
            "argv": [
                "<tmp>/repo/.venv/bin/python",
                "scripts/research/loop_seq.py",
                "page",
                "--root",
                "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>",
                "--out",
                "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/index.part.html",
                "--order",
                "tiny",
                "--title",
                "tiny: round 1",
                "--intro",
                "two",
                "--footer",
                "",
                "--notes",
                "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/stages/<stamp>_page/notes.json",
                "--variants",
                "c2,c1",
            ],
            "out_final": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/index.html",
            "out_part": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/index.part.html",
            "inputs": [
                {"path": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/tiny/c2/loop.mp4", "md5": "<md5>"},
                {"path": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>/tiny/c1/loop.mp4", "md5": "<md5>"},
            ],
        },
    },
    "fresh": {
        "tiles": [
            {
                "name": "import",
                "title": "import",
                "kind": "builtin",
                "optional": False,
                "parent": None,
                "branch": False,
                "backend": None,
                "state": "done",
                "detail": "2 stills",
                "wall_s": None,
                "thumb": "/api/jobs/loop_fresh_<stamp>/thumb/raw/0",
                "latest": None,
                "history": [],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
            },
            {
                "name": "registration",
                "title": "registration",
                "kind": "script",
                "optional": False,
                "parent": None,
                "branch": False,
                "backend": "loop_seq.py prep",
                "state": "none",
                "detail": "not run",
                "wall_s": None,
                "thumb": None,
                "latest": None,
                "history": [],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
            },
            {
                "name": "readers",
                "title": "readers",
                "kind": "script",
                "optional": True,
                "parent": "registration",
                "branch": False,
                "backend": "loop_seq.py readers",
                "state": "none",
                "detail": "optional, not run",
                "wall_s": None,
                "thumb": None,
                "latest": None,
                "history": [],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
            },
            {
                "name": "probe",
                "title": "probe",
                "kind": "script",
                "optional": True,
                "parent": "registration",
                "branch": True,
                "backend": "loop_seq.py probe",
                "state": "none",
                "detail": "optional, not run",
                "wall_s": None,
                "thumb": None,
                "latest": None,
                "history": [],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
            },
            {
                "name": "plan",
                "title": "plan",
                "kind": "builtin",
                "optional": False,
                "parent": None,
                "branch": False,
                "backend": None,
                "state": "none",
                "detail": "none saved; frozen plans available",
                "wall_s": None,
                "thumb": None,
                "latest": None,
                "history": [],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
            },
            {
                "name": "render",
                "title": "render",
                "kind": "script",
                "optional": False,
                "parent": None,
                "branch": False,
                "backend": "loop_seq.py render",
                "state": "none",
                "detail": "0 full, 0 drafts",
                "wall_s": None,
                "thumb": None,
                "latest": None,
                "history": [],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
            },
            {
                "name": "measure",
                "title": "measure",
                "kind": "script",
                "optional": True,
                "parent": "render",
                "branch": True,
                "backend": "loop_seq.py measure",
                "state": "none",
                "detail": "optional, not run",
                "wall_s": None,
                "thumb": None,
                "latest": None,
                "history": [],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
            },
            {
                "name": "skeptic",
                "title": "skeptic",
                "kind": "request",
                "optional": False,
                "parent": None,
                "branch": False,
                "backend": None,
                "state": "none",
                "detail": "no request yet",
                "wall_s": None,
                "thumb": None,
                "latest": None,
                "history": [],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
                "verdicts": {},
            },
            {
                "name": "page",
                "title": "page",
                "kind": "script",
                "optional": False,
                "parent": None,
                "branch": False,
                "backend": "loop_seq.py page",
                "state": "none",
                "detail": "not built",
                "wall_s": None,
                "thumb": None,
                "latest": None,
                "history": [],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
            },
            {
                "name": "grades",
                "title": "grades",
                "kind": "builtin",
                "optional": False,
                "parent": None,
                "branch": False,
                "backend": None,
                "state": "none",
                "detail": "no round yet",
                "wall_s": None,
                "thumb": None,
                "latest": None,
                "history": [],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
            },
        ],
        "registry": [
            "b5f764ef16a07d46",
            "13d179cbdf8fa6ad",
            "e680fe0ee5ed9ba7",
            "54a64900b7bd074d",
            "b70c3606e13d3ab8",
            "d5a4abf0d3399430",
            "5b042f522f741d93",
            "82fde4229a120ddc",
            "f0008b0ceb58fca5",
            "54324428ce4e16c3",
        ],
        "row": {
            "id": "loop_fresh_<stamp>",
            "flow": "loop",
            "seq": "fresh",
            "created": "<iso>",
            "adopted": False,
            "root": "benchmarks/runs/2026-11-05/studio/loop_fresh_<stamp>",
            "source": "Fresh Stills",
            "stills": 2,
            "candidates": 0,
            "unjudged": 0,
            "round": 0,
            "graded": False,
            "ungraded_by_his_word": False,
            "last_render": "none",
            "last_attempt": None,
            "running": [],
        },
        "rounds": [],
    },
    "full": {
        "tiles": [
            {
                "name": "import",
                "title": "import",
                "kind": "builtin",
                "optional": False,
                "parent": None,
                "branch": False,
                "backend": None,
                "state": "done",
                "detail": "3 stills",
                "wall_s": None,
                "thumb": "/api/jobs/loop_tiny_<stamp>/thumb/still/0",
                "latest": None,
                "history": [],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
            },
            {
                "name": "registration",
                "title": "registration",
                "kind": "script",
                "optional": False,
                "parent": None,
                "branch": False,
                "backend": "loop_seq.py prep",
                "state": "done",
                "detail": "k1 sift+magsac 121 inl.; k2 sift+magsac 122 inl. · 64×48",
                "wall_s": "<s>",
                "thumb": "/api/jobs/loop_tiny_<stamp>/thumb/still/0",
                "latest": "<stamp>_registration",
                "history": [
                    {"id": "<stamp>_registration", "state": "done", "started": "<iso>", "wall_s": "<s>", "reason": None}
                ],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
                "unchanged_from": None,
                "latest_knobs": {
                    "depth_maps": True,
                    "long": 1920,
                    "ref": -1,
                    "cut": "",
                    "bg_depth": 0.0,
                    "min_inliers": 40,
                    "ecc_refine": False,
                    "lock_window": "",
                    "windows": "",
                },
            },
            {
                "name": "readers",
                "title": "readers",
                "kind": "script",
                "optional": True,
                "parent": "registration",
                "branch": False,
                "backend": "loop_seq.py readers",
                "state": "done",
                "detail": "Lab>14 25.0%, 25.0%",
                "wall_s": "<s>",
                "thumb": None,
                "latest": "<stamp>_readers",
                "history": [
                    {"id": "<stamp>_readers", "state": "done", "started": "<iso>", "wall_s": "<s>", "reason": None}
                ],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
                "unchanged_from": None,
                "latest_knobs": {},
            },
            {
                "name": "probe",
                "title": "probe",
                "kind": "script",
                "optional": True,
                "parent": "registration",
                "branch": True,
                "backend": "loop_seq.py probe",
                "state": "done",
                "detail": "rife dexp 0.041 / 0.061 / 0.034 · 2 pairs",
                "wall_s": "<s>",
                "thumb": "/api/jobs/loop_tiny_<stamp>/file/in/tiny/probe/probe_0_1_rife.jpg",
                "latest": "<stamp>_probe",
                "history": [
                    {"id": "<stamp>_probe", "state": "done", "started": "<iso>", "wall_s": "<s>", "reason": None}
                ],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
                "unchanged_from": None,
                "latest_knobs": {"long": 960, "pairs": ""},
            },
            {
                "name": "plan",
                "title": "plan",
                "kind": "builtin",
                "optional": False,
                "parent": None,
                "branch": False,
                "backend": None,
                "state": "none",
                "detail": "none saved; frozen plans available",
                "wall_s": None,
                "thumb": None,
                "latest": None,
                "history": [],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
            },
            {
                "name": "render",
                "title": "render",
                "kind": "script",
                "optional": False,
                "parent": None,
                "branch": False,
                "backend": "loop_seq.py render",
                "state": "done",
                "detail": "2 full, 1 drafts; unjudged: c2 · last attempt failed: c3",
                "wall_s": "<s>",
                "thumb": "/api/jobs/loop_tiny_<stamp>/thumb/render/full/c2",
                "latest": "<stamp>_render",
                "history": [
                    {"id": "<stamp>_render", "state": "done", "started": "<iso>", "wall_s": "<s>", "reason": None},
                    {"id": "<stamp>_render", "state": "done", "started": "<iso>", "wall_s": "<s>", "reason": None},
                    {"id": "<stamp>_render", "state": "done", "started": "<iso>", "wall_s": "<s>", "reason": None},
                    {
                        "id": "<stamp>_render",
                        "state": "failed",
                        "started": "<iso>",
                        "wall_s": "<s>",
                        "reason": "RuntimeError: the fake render failed",
                    },
                ],
                "stale": False,
                "generated": True,
                "progress": None,
                "reason": "last attempt failed: RuntimeError: the fake render failed",
                "unchanged_from": None,
                "latest_knobs": {"plan": "frozen:tiny_a1", "name": "c3", "draft": 0, "fps": 25},
                "last_attempt": "failed: c3",
            },
            {
                "name": "measure",
                "title": "measure",
                "kind": "script",
                "optional": True,
                "parent": "render",
                "branch": True,
                "backend": "loop_seq.py measure",
                "state": "done",
                "detail": "1 run; latest on c1: w dx 0.3 dy 4.0 px",
                "wall_s": "<s>",
                "thumb": "/api/jobs/loop_tiny_<stamp>/thumb/render/full/c1",
                "latest": "<stamp>_measure",
                "history": [
                    {"id": "<stamp>_measure", "state": "done", "started": "<iso>", "wall_s": "<s>", "reason": None}
                ],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
                "unchanged_from": None,
                "latest_knobs": {"render": "full:c1", "windows": "w:1,1,9,9", "ref": 0},
            },
            {
                "name": "skeptic",
                "title": "skeptic",
                "kind": "request",
                "optional": False,
                "parent": None,
                "branch": False,
                "backend": None,
                "state": "answered",
                "detail": "skeptic_<stamp>.json answered",
                "wall_s": None,
                "thumb": None,
                "latest": None,
                "history": [],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
                "verdicts": {
                    "c1": {
                        "verdict": "READY",
                        "judged_md5": "<md5>",
                        "note": "clean",
                        "from": "skeptic_<stamp>.json",
                        "at": "t",
                    }
                },
            },
            {
                "name": "page",
                "title": "page",
                "kind": "script",
                "optional": False,
                "parent": None,
                "branch": False,
                "backend": "loop_seq.py page",
                "state": "done",
                "detail": "md5 <md5>… · round 2",
                "wall_s": "<s>",
                "thumb": None,
                "latest": "<stamp>_page",
                "history": [
                    {"id": "<stamp>_page", "state": "done", "started": "<iso>", "wall_s": "<s>", "reason": None},
                    {"id": "<stamp>_page", "state": "done", "started": "<iso>", "wall_s": "<s>", "reason": None},
                ],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
                "unchanged_from": None,
                "latest_knobs": {"variants": ["c1"], "title": "the second round", "intro": "", "footer": ""},
                "page": "/api/jobs/loop_tiny_<stamp>/file/index.html",
            },
            {
                "name": "grades",
                "title": "grades",
                "kind": "builtin",
                "optional": False,
                "parent": None,
                "branch": False,
                "backend": None,
                "state": "ungraded",
                "detail": "round 2: ungraded",
                "wall_s": None,
                "thumb": None,
                "latest": None,
                "history": [],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
            },
        ],
        "registry": [
            "b5f764ef16a07d46",
            "13d179cbdf8fa6ad",
            "e680fe0ee5ed9ba7",
            "54a64900b7bd074d",
            "b70c3606e13d3ab8",
            "d5a4abf0d3399430",
            "5b042f522f741d93",
            "82fde4229a120ddc",
            "f0008b0ceb58fca5",
            "54324428ce4e16c3",
        ],
        "row": {
            "id": "loop_tiny_<stamp>",
            "flow": "loop",
            "seq": "tiny",
            "created": "<iso>",
            "adopted": False,
            "root": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>",
            "source": "Tiny Stills",
            "stills": 3,
            "candidates": 2,
            "unjudged": 1,
            "round": 2,
            "graded": False,
            "ungraded_by_his_word": False,
            "last_render": "done",
            "last_attempt": "failed",
            "running": [],
        },
        "rounds": [
            {
                "n": 1,
                "at": "<iso>",
                "candidates": ["c1", "c2"],
                "variants": [],
                "page_md5": "<md5>",
                "page": "index.html",
                "record": "<stamp>_page",
                "override": "Override: built on his word with c2 (unjudged: no skeptic verdict for "
                "this candidate) (<iso>).",
                "grade": {"text": "c1 is fine, c2 drifts", "at": "<iso>", "page_md5": "<md5>"},
                "ungraded_by_his_word": None,
            },
            {
                "n": 2,
                "at": "<iso>",
                "candidates": ["c1"],
                "variants": ["c1"],
                "page_md5": "<md5>",
                "page": "index.html",
                "record": "<stamp>_page",
                "override": None,
                "grade": None,
                "ungraded_by_his_word": None,
            },
        ],
    },
    "page_md5_beside_the_page": True,
    "round_files": ["1/index.html", "1/round.json", "2/index.html", "2/round.json"],
    "stale": {
        "tiles": [
            {
                "name": "import",
                "title": "import",
                "kind": "builtin",
                "optional": False,
                "parent": None,
                "branch": False,
                "backend": None,
                "state": "done",
                "detail": "3 stills",
                "wall_s": None,
                "thumb": "/api/jobs/loop_tiny_<stamp>/thumb/still/0",
                "latest": None,
                "history": [],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
            },
            {
                "name": "registration",
                "title": "registration",
                "kind": "script",
                "optional": False,
                "parent": None,
                "branch": False,
                "backend": "loop_seq.py prep",
                "state": "done",
                "detail": "k1 sift+magsac 121 inl.; k2 sift+magsac 122 inl. · 64×48",
                "wall_s": "<s>",
                "thumb": "/api/jobs/loop_tiny_<stamp>/thumb/still/0",
                "latest": "<stamp>_registration",
                "history": [
                    {
                        "id": "<stamp>_registration",
                        "state": "done",
                        "started": "<iso>",
                        "wall_s": "<s>",
                        "reason": None,
                    },
                    {
                        "id": "<stamp>_registration",
                        "state": "done",
                        "started": "<iso>",
                        "wall_s": "<s>",
                        "reason": None,
                    },
                ],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
                "unchanged_from": "<stamp>_registration",
                "latest_knobs": {
                    "depth_maps": True,
                    "long": 1920,
                    "ref": -1,
                    "cut": "",
                    "bg_depth": 0.0,
                    "min_inliers": 40,
                    "ecc_refine": False,
                    "lock_window": "",
                    "windows": "",
                },
            },
            {
                "name": "readers",
                "title": "readers",
                "kind": "script",
                "optional": True,
                "parent": "registration",
                "branch": False,
                "backend": "loop_seq.py readers",
                "state": "done",
                "detail": "moved with the previous prep",
                "wall_s": "<s>",
                "thumb": None,
                "latest": "<stamp>_readers",
                "history": [
                    {"id": "<stamp>_readers", "state": "done", "started": "<iso>", "wall_s": "<s>", "reason": None}
                ],
                "stale": True,
                "generated": False,
                "progress": None,
                "reason": None,
                "unchanged_from": None,
                "latest_knobs": {},
                "moved_to": "in/tiny_prev_<stamp>/readers",
                "stale_after": "registration",
            },
            {
                "name": "probe",
                "title": "probe",
                "kind": "script",
                "optional": True,
                "parent": "registration",
                "branch": True,
                "backend": "loop_seq.py probe",
                "state": "done",
                "detail": "",
                "wall_s": "<s>",
                "thumb": None,
                "latest": "<stamp>_probe",
                "history": [
                    {"id": "<stamp>_probe", "state": "done", "started": "<iso>", "wall_s": "<s>", "reason": None}
                ],
                "stale": True,
                "generated": False,
                "progress": None,
                "reason": None,
                "unchanged_from": None,
                "latest_knobs": {"long": 960, "pairs": ""},
                "stale_after": "registration",
            },
            {
                "name": "plan",
                "title": "plan",
                "kind": "builtin",
                "optional": False,
                "parent": None,
                "branch": False,
                "backend": None,
                "state": "none",
                "detail": "none saved; frozen plans available",
                "wall_s": None,
                "thumb": None,
                "latest": None,
                "history": [],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
            },
            {
                "name": "render",
                "title": "render",
                "kind": "script",
                "optional": False,
                "parent": None,
                "branch": False,
                "backend": "loop_seq.py render",
                "state": "done",
                "detail": "2 full, 1 drafts; unjudged: c2 · last attempt failed: c3",
                "wall_s": "<s>",
                "thumb": "/api/jobs/loop_tiny_<stamp>/thumb/render/full/c2",
                "latest": "<stamp>_render",
                "history": [
                    {"id": "<stamp>_render", "state": "done", "started": "<iso>", "wall_s": "<s>", "reason": None},
                    {"id": "<stamp>_render", "state": "done", "started": "<iso>", "wall_s": "<s>", "reason": None},
                    {"id": "<stamp>_render", "state": "done", "started": "<iso>", "wall_s": "<s>", "reason": None},
                    {
                        "id": "<stamp>_render",
                        "state": "failed",
                        "started": "<iso>",
                        "wall_s": "<s>",
                        "reason": "RuntimeError: the fake render failed",
                    },
                ],
                "stale": True,
                "generated": True,
                "progress": None,
                "reason": "last attempt failed: RuntimeError: the fake render failed",
                "unchanged_from": None,
                "latest_knobs": {"plan": "frozen:tiny_a1", "name": "c3", "draft": 0, "fps": 25},
                "last_attempt": "failed: c3",
                "stale_after": "registration",
            },
            {
                "name": "measure",
                "title": "measure",
                "kind": "script",
                "optional": True,
                "parent": "render",
                "branch": True,
                "backend": "loop_seq.py measure",
                "state": "done",
                "detail": "1 run; latest on c1: w dx 0.3 dy 4.0 px",
                "wall_s": "<s>",
                "thumb": "/api/jobs/loop_tiny_<stamp>/thumb/render/full/c1",
                "latest": "<stamp>_measure",
                "history": [
                    {"id": "<stamp>_measure", "state": "done", "started": "<iso>", "wall_s": "<s>", "reason": None}
                ],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
                "unchanged_from": None,
                "latest_knobs": {"render": "full:c1", "windows": "w:1,1,9,9", "ref": 0},
            },
            {
                "name": "skeptic",
                "title": "skeptic",
                "kind": "request",
                "optional": False,
                "parent": None,
                "branch": False,
                "backend": None,
                "state": "answered",
                "detail": "skeptic_<stamp>.json answered",
                "wall_s": None,
                "thumb": None,
                "latest": None,
                "history": [],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
                "verdicts": {
                    "c1": {
                        "verdict": "READY",
                        "judged_md5": "<md5>",
                        "note": "clean",
                        "from": "skeptic_<stamp>.json",
                        "at": "t",
                    }
                },
            },
            {
                "name": "page",
                "title": "page",
                "kind": "script",
                "optional": False,
                "parent": None,
                "branch": False,
                "backend": "loop_seq.py page",
                "state": "done",
                "detail": "md5 <md5>… · round 2",
                "wall_s": "<s>",
                "thumb": None,
                "latest": "<stamp>_page",
                "history": [
                    {"id": "<stamp>_page", "state": "done", "started": "<iso>", "wall_s": "<s>", "reason": None},
                    {"id": "<stamp>_page", "state": "done", "started": "<iso>", "wall_s": "<s>", "reason": None},
                ],
                "stale": True,
                "generated": False,
                "progress": None,
                "reason": None,
                "unchanged_from": None,
                "latest_knobs": {"variants": ["c1"], "title": "the second round", "intro": "", "footer": ""},
                "page": "/api/jobs/loop_tiny_<stamp>/file/index.html",
                "stale_after": "registration",
            },
            {
                "name": "grades",
                "title": "grades",
                "kind": "builtin",
                "optional": False,
                "parent": None,
                "branch": False,
                "backend": None,
                "state": "ungraded",
                "detail": "round 2: ungraded",
                "wall_s": None,
                "thumb": None,
                "latest": None,
                "history": [],
                "stale": False,
                "generated": False,
                "progress": None,
                "reason": None,
            },
        ],
        "registry": [
            "b5f764ef16a07d46",
            "13d179cbdf8fa6ad",
            "e680fe0ee5ed9ba7",
            "54a64900b7bd074d",
            "b70c3606e13d3ab8",
            "d5a4abf0d3399430",
            "5b042f522f741d93",
            "82fde4229a120ddc",
            "f0008b0ceb58fca5",
            "54324428ce4e16c3",
        ],
        "row": {
            "id": "loop_tiny_<stamp>",
            "flow": "loop",
            "seq": "tiny",
            "created": "<iso>",
            "adopted": False,
            "root": "benchmarks/runs/2026-11-05/studio/loop_tiny_<stamp>",
            "source": "Tiny Stills",
            "stills": 3,
            "candidates": 2,
            "unjudged": 1,
            "round": 2,
            "graded": False,
            "ungraded_by_his_word": False,
            "last_render": "done",
            "last_attempt": "failed",
            "running": [],
        },
        "rounds": [
            {
                "n": 1,
                "at": "<iso>",
                "candidates": ["c1", "c2"],
                "variants": [],
                "page_md5": "<md5>",
                "page": "index.html",
                "record": "<stamp>_page",
                "override": "Override: built on his word with c2 (unjudged: no skeptic verdict for "
                "this candidate) (<iso>).",
                "grade": {"text": "c1 is fine, c2 drifts", "at": "<iso>", "page_md5": "<md5>"},
                "ungraded_by_his_word": None,
            },
            {
                "n": 2,
                "at": "<iso>",
                "candidates": ["c1"],
                "variants": ["c1"],
                "page_md5": "<md5>",
                "page": "index.html",
                "record": "<stamp>_page",
                "override": None,
                "grade": None,
                "ungraded_by_his_word": None,
            },
        ],
    },
    "registry": {
        "stages": "83b7f497d40f9380",
        "hints": "ceca97b5111fc312",
        "hint_count": 290,
        "schema": "d9bdc86dd439f099",
        "schema_rows": 151,
        "rulings": "b533b58ecedcb25e",
        "rulings_rows": 7,
    },
}
