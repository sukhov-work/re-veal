"""The director plan flow (builder D, phase B): the registry's stages and `--set` table, the argv of the resolve, the
render and the page through the Runner with the fake director_render.py and director_page.py, the tiles, the job
view's keys, the plan view's knob map and the render view's measures, series and frame tags.

The fixture pair is the conftest's tiny_1 with a round-12 plan of its own (a quad container, one keyframe_chain and an
end effect), full layer tables with their layers.npz and a matte folder with mattes.json (`dpair`). Every assertion
names the mutation that turns it red.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, md5_file, read_json, rel, sha256_file, write_json
from reveal_studio.jobs.candidates import candidate
from reveal_studio.jobs.plans import save_plan
from reveal_studio.jobs.store import create_director_job
from reveal_studio.registry import director
from reveal_studio.registry.common import VERDICT_STAGE
from reveal_studio.registry.flows import ALL_FLOWS, FLOWS, identity_of, stage_def, stage_order
from reveal_studio.registry.hints import HINTS
from reveal_studio.registry.hints_director import HINTS as DIRECTOR_HINTS
from reveal_studio.runner.argv_director import set_flags
from reveal_studio.runner.process import Runner
from reveal_studio.views import director as dviews
from reveal_studio.views.job import job_view, stage_views
from reveal_studio.views.page import build_page
from reveal_studio.views.render import render_view

from .conftest import HELPER, PAIR, wait_record, write_fixture_pair

ORDER = ["import", "verdict", "resolve", "plan", "render", "skeptic", "page", "grades"]
R12 = f"{PAIR}_r12"
TOP_LEVEL_2026_11_05 = [
    "motion", "guard", "end_scale", "front_ids", "cont_feather", "parallax_sources", "parallax_gain",
    "parallax_gain_A", "parallax_blur", "parallax_A_elements", "parallax_push", "push_floor", "front_in",
    "front_margin", "front_hole_max", "plate_fill", "front_per_element", "plate", "sky", "key_end",
    "hole_reveal_from", "hole_reveal_over", "reflect", "end_window", "end_kind", "end_band", "end_radius_px",
    "vacated_first",
]  # fmt: skip
"""The 28 top-level keys director_render.py reads (`grep knobs director_render.py`, 2026-11-05: 26 by knobs.get, guard
at line 447 and end_window at line 1811), in the order of the file."""
PLAN_R12: Json = {
    "pair": PAIR,
    "planner": {"model": "a test planner", "date": "2026-11-05", "brief": "the test", "prompt_sha256": "0" * 64},
    "reading": {"a": "a grey square", "b": "a lighter square"},
    "relation": "themed",
    "concepts": [
        {
            "id": "c1",
            "rank": 1,
            "idea": "the grey square becomes the lighter one through a pane",
            "motion": {"kind": "continuous", "edge": 0.35, "overlap": 0.1},
            "reveal": {"guard": True},
            "container": {
                "in": "B",
                "kind": "quad",
                "spec": {"points": [[10, 5], [63, 0], [63, 40], [10, 30]], "front_ids": [1]},
                "rim": "glass",
                "params": {"reflect": 0.18},
            },
            "pullback": {"ease": "smootherstep", "parallax": {"kind": "depth", "gain": 0.4, "gain_A": 0.8}},
            "transforms": [
                {
                    "name": "pane",
                    "a": {"kind": "all"},
                    "b": None,
                    "by": "keyframe_chain",
                    "window": [0.3, 0.92],
                    "mix": "none",
                    "params": {"keyframes": [HELPER], "frame": "A", "times": [0.4], "guide": True},
                }
            ],
            "end_effect": {"kind": "b_luma_reveal", "window": [0.92, 1.0], "params": {"band": 0.4}},
            "helper": {"keyframes": [HELPER]},
            "knobs": [
                {"name": "front_per_element", "range": [False, True], "default": True, "what": "one layer each"},
                {"name": "pane.params.times[0]", "range": [0.3, 0.5], "default": 0.4, "what": "the keyframe's time"},
                {"name": "pane.window[1]", "range": [0.88, 0.95], "default": 0.92, "what": "the chain's end"},
                {"name": "pane.ot_weight", "range": [0, 1], "default": 1.0, "what": "the key form of a param"},
                {"name": "container.spec.box", "range": None, "default": None, "what": "geometry"},
                {"name": "pane.params.edge", "range": [0.1, 0.5], "default": 0.35, "what": "table D"},
            ],
            "risk": "the pane's dissolve can read as a smear",
        },
        {
            "id": "c2",
            "rank": 2,
            "idea": "a disc concept for the sky rows",
            "container": {"in": "B", "kind": "disc", "params": {"sky": {"shape": "radial_out", "stars": True}}},
            "transforms": [{"name": "sun", "a": {"kind": "circle_fit"}, "b": {"kind": "bright_disc"}, "by": "recede"}],
        },
    ],
}


def write_director_pair(root: Path) -> str:
    """The conftest's tiny_1 pair, then the round-12 plan, full layer tables with layers.npz (elements 1 to 3 in three
    bands) and mattes.json beside the first photo's two mattes."""
    import numpy as np

    pair = write_fixture_pair(root)
    (root / f"scripts/research/plans/{R12}.json").write_text(json.dumps(PLAN_R12, indent=1))
    groups = {1: "ceiling", 2: "person", 3: "luminary"}
    for side in ("S", "F"):
        t = root / f"benchmarks/runs/2026-09-28/layers_v3/{pair}_{side}"
        elements = [
            {
                "id": i,
                "label": f"{groups[i]} {i}" if i != 2 else "person",
                "group": groups[i],
                "area_share": round(1 / 3, 4),
                "depth_rank": i,
                "median_disparity": 0.2 * i,
            }
            for i in (1, 2, 3)
        ]
        (t / "layers.json").write_text(
            json.dumps({"canvas": [64, 48], "elements": elements, "photo": f"{pair}_{side}"})
        )
        el = np.zeros((48, 64), np.uint16)
        el[:16], el[16:32], el[32:] = 1, 2, 3
        disparity = np.tile(np.linspace(0, 1, 64, dtype=np.float32), (48, 1))
        np.savez(t / "layers.npz", element=el, disparity=disparity)
    mattes = root / f"benchmarks/runs/2026-10-17/mattes/{pair}_S"
    (mattes / "mattes.json").write_text(json.dumps({"model": "a test matting model", "elements": {"1": "x", "2": "y"}}))
    return pair


@pytest.fixture
def dpair(root: Path) -> str:
    return write_director_pair(root)


@pytest.fixture
def djob(settings: Settings, dpair: str) -> tuple[Path, Json]:
    j = create_director_job(settings, dpair)
    return settings.runs / "2026-11-05" / "studio" / j["id"], j


def run(runner: Runner, d: Path, j: Json, stage: str, knobs: Json) -> Json:
    rec = runner.start_stage(d, j, stage_def("director", stage), knobs)
    return wait_record(d, rec["id"])


DRAFT: Json = {"plan": f"frozen:{R12}", "concept": "c1", "draft": 480}


# ---------------------------------------------------------------- the registry


def test_the_director_flow_is_enabled_with_its_eight_stages() -> None:
    """Mutation: the verdict copied into the flow (two definitions of one shared stage), the flow left disabled, or
    the drafts folder put under run/ (director_page.py then lists them beside the full renders) turns this red."""
    assert ALL_FLOWS["director"] is director.FLOW and FLOWS["director"] is director.FLOW
    assert stage_order("director") == ORDER and director.DIRECTOR_STAGES[1] is VERDICT_STAGE
    spec = director.FLOW["candidates"]
    assert (spec["full"], spec["draft"], spec["terminal"], spec["mp4"]) == (
        ["{root}"],
        ["{job}/drafts"],
        "info.json",
        "transition.mp4",
    )
    scripts = {s["name"]: (s["script"], s["terminal"]) for s in director.DIRECTOR_STAGES if s["kind"] == "script"}
    assert scripts == {
        "verdict": ("reveal", "metrics.json"),
        "resolve": ("director_render", "anchors.json"),
        "render": ("director_render", "info.json"),
        "page": ("director_page", "index.html"),
    }
    assert (identity_of("director", "resolve"), identity_of("director", "render")) == (
        ["anchors.json"],
        ["transition.mp4"],
    )
    assert identity_of("director", "page") == []
    # a resolve writes beside run/ and no render reads it; the page's upstream is the render alone
    assert (stage_def("director", "render")["stale_after"], stage_def("director", "page")["stale_after"]) == (
        [],
        ["render"],
    )


def test_the_render_and_resolve_knobs_carry_the_renderers_defaults_and_flags() -> None:
    """The CLI's defaults (director_render.py:2077-2087). Mutation: fps 25 (the viewer then plays 20 % slow) or a
    `set` knob of another type (one flag for the whole dict) turns this red."""
    render = {k["key"]: (k["type"], k["default"], k["flag"]) for k in stage_def("director", "render")["knobs"]}
    assert render == {
        "plan": ("plan", "", None),
        "concept": ("str", "", "--concept"),
        "name": ("str", "", None),
        "draft": ("int", 0, None),
        "max_long": ("int", 1920, None),
        "seconds": ("float", 3.0, "--seconds"),
        "fps": ("int", 30, "--fps"),
        "set": ("object", {}, "--set"),
    }
    resolve = {k["key"]: k["flag"] for k in stage_def("director", "resolve")["knobs"]}
    assert resolve == {"plan": None, "concept": "--concept", "max_long": "--max-long", "set": "--set"}
    page = [k["key"] for k in stage_def("director", "page")["knobs"]]
    assert page == ["title", "key", "head", "keyframes"]  # director_page.py takes no list of renders (Fable F8)
    assert all(k["range"] is None for s in director.DIRECTOR_STAGES for k in s["knobs"])  # none is stated


def test_every_director_measure_hint_names_the_line_it_reads() -> None:
    """The hints of the resolve's and the render's numbers (anchors.json, info.json, the resolve panel) each name the
    renderer's line they read (Fable review F9: info.step_second, info.step_last and resolve.front_elements had none).
    Mutation: a measure row without its source turns this red."""
    rows = {k: h for k, h in DIRECTOR_HINTS.items() if k.split(".")[0] in ("info", "resolve", "anchors")}
    assert len(rows) > 40 and [k for k, h in rows.items() if not h.get("source")] == []
    assert DIRECTOR_HINTS["info.step_second"]["source"] == "director_render.py:2014, 2052"
    assert DIRECTOR_HINTS["resolve.front_elements"]["source"] == "director_render.py:713-731"


def test_the_set_table_has_the_four_tables_of_the_research() -> None:
    """26 top-level keys that change a render, 18 sky keys, 60 transform keys, 8 without effect: 104 + 8. Mutation: a
    row dropped or two rows of one key turn the counts red; a key the renderer never reads among the top-level rows
    turns the literal list red."""
    tables = {t: [r for r in director.SET_KEYS if r["table"] == t] for t in "ABCD"}
    assert {t: len(rows) for t, rows in tables.items()} == {"A": 26, "B": 18, "C": 60, "D": 8}
    assert [r["key"] for r in director.SET_KEYS if r["scope"] == "global"] == [
        k for k in TOP_LEVEL_2026_11_05 if k not in ("hole_reveal_from", "hole_reveal_over")
    ] + ["hole_reveal_from", "hole_reveal_over"]
    assert sorted(director.GLOBAL_KEYS) == sorted(TOP_LEVEL_2026_11_05)
    assert all(r["readonly"] for r in tables["D"]) and not any(r["readonly"] for t in "ABC" for r in tables[t])
    assert {r["scope"] for r in tables["D"]} == {"global", "sky", "transform"}
    hints = [r["hint"] for r in director.SET_KEYS]
    assert len(hints) == len(set(hints)) == 112
    for r in director.SET_KEYS:
        assert r["hint"] in HINTS and r["source"] and r["what"].strip() and r["when"], r["key"]
        assert r["read_at"].startswith("director_render.py:"), r["key"]
        if r["table"] == "C":
            assert r["kinds"] and set(r["kinds"]) <= set(director.TRANSFORM_KINDS), r["key"]
    assert director.TRANSFORM_KEYS["feather"]["kinds"]["exit"] == 1.5  # director_render.py:1164


def test_the_director_hints_use_the_flows_prefixes() -> None:
    """Mutation: a director hint under the loop's prefixes (a collision with a future loop key) turns this red."""
    prefixes = ("control.director_", "director.", "resolve.", "anchors.", "info.", "set.")
    assert all(k.startswith(prefixes) for k in DIRECTOR_HINTS), [
        k for k in DIRECTOR_HINTS if not k.startswith(prefixes)
    ]
    assert all(HINTS[k] is DIRECTOR_HINTS[k] for k in DIRECTOR_HINTS)
    assert len(DIRECTOR_HINTS) == 196  # four rows of the phase B fix round: plans, next_knobs, planner_notes, set_group
    keys = {"pair", "concept", "canvas", "frames", "anchors", "layers", "info", "camera", "renderer_md5"}
    assert {k.split(".", 1)[1] for k in DIRECTOR_HINTS if k.startswith("anchors.")} == keys
    ro = DIRECTOR_HINTS["set.tr.edge"]["what"]
    assert "Read-only" in ro and "SCHEMA.md:221" in ro  # table D names the SCHEMA.md line it corrects


@pytest.mark.parametrize(
    ("key", "why"),
    [
        ("parallax_push", None),
        ("pane.window", None),
        ("pane.times", None),
        ("pane.new_param", None),  # a transform's params stay open: the renderer passes any key to the transform
        ("sky.shape", None),
        ("pane.ease", "reaches no frame: the renderer reads a layer's ease"),
        ("pane.edge", "SCHEMA.md:221"),
        ("pane.rate", "SCHEMA.md:222"),
        ("hole_reveal_from", "a fallback that never fires"),
        ("sky.key_end", "no key_end reader"),
        ("parallax_pussh", "never reads"),
        ("sky.radius", "a sky key director_render.py never reads"),
        ("pain.window", "names no transform of the concept"),
    ],
)
def test_a_set_key_that_reaches_no_frame_is_named(key: str, why: str | None) -> None:
    """The renderer's routing (director_render.py:881-889, 1439-1441). Mutation: dropping the table D check (a
    pane.edge sent and recorded while it changes nothing) turns the read-only rows red."""
    got = director.set_key_problem(key, ["pane"])
    assert (got is None) if why is None else (got is not None and why in got), got


# ---------------------------------------------------------------- the argv through the Runner


def test_the_resolve_runs_outside_run_with_the_settings_roots(
    settings: Settings, runner: Runner, djob: tuple[Path, Json]
) -> None:
    """Mutation: --layers-dir dropped (the renderer then reads its own default root, and a job made under another
    root renders the wrong tables), or the resolve written under run/ (director_page.py then lists a folder without
    measures and raises), turns this red."""
    d, j = djob
    rec = run(runner, d, j, "resolve", {"plan": f"frozen:{R12}", "concept": "c1"})
    assert rec["state"] == "done", rec.get("reason")
    stamp = rec["id"].replace("_resolve", "")
    root = rel(d, settings.root)
    assert rec["argv"] == [
        str(settings.python),
        "scripts/research/director_render.py",
        f"scripts/research/plans/{R12}.json",
        f"{root}/resolve/{stamp}.part",
        "--resolve-only",
        "--concept",
        "c1",
        "--max-long",
        "1920",
        "--layers-dir",
        "benchmarks/runs/2026-09-28/layers_v3",
        "--mattes-dir",
        "benchmarks/runs/2026-10-17/mattes",
    ]
    assert rec["out_final"] == f"{root}/resolve/{stamp}" and not (d / "run" / stamp).exists()
    names = sorted(Path(o["path"]).name for o in rec["outputs"])
    assert names == ["anchors.json", "canvas_A.png", "canvas_B.png", "info.json"]
    assert rec["script_md5"] == md5_file(settings.director_render)
    assert rec["inputs"][0] == {
        "path": f"scripts/research/plans/{R12}.json",
        "sha256": sha256_file(settings.director_plans / f"{R12}.json"),
    }
    assert {i["path"] for i in rec["inputs"] if i.get("helper")} == {HELPER}  # the keyframe the concept names
    again = run(runner, d, j, "resolve", {"plan": f"frozen:{R12}", "concept": "c1"})
    assert again["unchanged_from"] == rec["id"]  # anchors.json is the resolve's identity file


def test_a_draft_renders_under_drafts_with_progress_and_one_set_flag_per_key(
    settings: Settings, runner: Runner, djob: tuple[Path, Json]
) -> None:
    """Mutation: --progress dropped (the strip shows no number), the keys sent in the page's order (two equal dicts,
    two argv), or a draft written under run/ (the page lists it) turns this red."""
    d, j = djob
    knobs = {**DRAFT, "set": {"parallax_push": 2, "pane.window": [0.35, 0.97]}}
    rec = run(runner, d, j, "render", knobs)
    assert rec["state"] == "done", rec.get("reason")
    root = rel(d, settings.root)
    assert rec["argv"][2:] == [
        f"scripts/research/plans/{R12}.json",
        f"{root}/drafts/{R12}_c1.part",
        "--concept",
        "c1",
        "--max-long",
        "480",
        "--seconds",
        "3.0",
        "--fps",
        "30",
        "--set",
        "pane.window=[0.35, 0.97]",
        "--set",
        "parallax_push=2",
        "--progress",
        "--layers-dir",
        "benchmarks/runs/2026-09-28/layers_v3",
        "--mattes-dir",
        "benchmarks/runs/2026-10-17/mattes",
    ]
    out = d / "drafts" / f"{R12}_c1"
    assert rec["out_final"] == rel(out, settings.root) and not (d / "run" / f"{R12}_c1").exists()
    assert sorted(Path(o["path"]).name for o in rec["outputs"]) == ["info.json", "montage.jpg", "transition.mp4"]
    log = (d / "stages" / rec["id"] / "log.txt").read_text()
    assert "PROGRESS 0 90" in log and "PROGRESS 89 90" in log
    info = read_json(out / "info.json")
    assert info["knobs"] == {"parallax_push": 2, "pane.window": [0.35, 0.97]}
    plan_in = rec["inputs"][0]
    assert plan_in["sha256"] == sha256_file(settings.director_plans / f"{R12}.json") and len(plan_in["sha256"]) == 64
    assert info["plan_sha256"] == plan_in["sha256"][:16]  # info.json keeps 16 characters, the record the whole
    tr = next(i for i in rec["inputs"] if i["path"] == "transitions.py")
    assert tr["md5"] == md5_file(settings.transitions) == info["transitions_md5"]


def test_set_flags_follow_the_object_knobs_sorted_order() -> None:
    """Mutation: a value written with str() ("True", a Python list's repr) instead of JSON turns this red."""
    stage = stage_def("director", "render")
    assert set_flags(stage, {"set": {"plate": False, "end_window": [0.9, 1.0]}}) == [
        "--set",
        "end_window=[0.9, 1.0]",
        "--set",
        "plate=false",
    ]


def test_a_full_render_goes_under_run_and_the_same_tag_again_is_409(
    settings: Settings, runner: Runner, djob: tuple[Path, Json]
) -> None:
    """Mutation: a finished render overwritten by a rerun of its tag, or a full render put under drafts/, turns this
    red."""
    d, j = djob
    rec = run(runner, d, j, "render", {**DRAFT, "draft": 0, "name": "full"})
    assert rec["state"] == "done" and rec["argv"][7] == "1920"  # --max-long from max_long
    folder = d / "run" / f"{R12}_c1-full"
    before = {p.name: md5_file(p) for p in folder.iterdir()}
    with pytest.raises(StudioError, match="exists: choose another name") as e:
        runner.start_stage(d, j, stage_def("director", "render"), {**DRAFT, "draft": 0, "name": "full"})
    assert e.value.code == 409 and {p.name: md5_file(p) for p in folder.iterdir()} == before


@pytest.mark.parametrize(
    ("knobs", "code", "text"),
    [
        ({"concept": "c9"}, 400, "has no concept 'c9'"),
        ({"seconds": 0.05}, 400, "the renderer's measures need 3 or more"),
        ({"name": "with_underscore"}, 400, "no underscore"),
        ({"set": {"pane.edge": 0.2}}, 400, "SCHEMA.md:221"),
        ({"set": {"pain.window": [0, 1]}}, 400, "names no transform"),
        ({"plan": "frozen:nope"}, 404, "no plan scripts/research/plans/nope.json"),
        ({"plan": "frozen:tiny_a1"}, 404, "no plan scripts/research/plans/tiny_a1.json"),  # the loop's folder is apart
    ],
)
def test_a_render_the_renderer_would_get_wrong_is_refused_before_a_record(
    settings: Settings, runner: Runner, djob: tuple[Path, Json], knobs: Json, code: int, text: str
) -> None:
    """An unknown concept renders the first one without a message (director_render.py:2095); fewer than 3 frames crash
    the measures (line 2052). Mutation: the concept check dropped turns the first row red."""
    d, j = djob
    with pytest.raises(StudioError, match=text) as e:
        runner.start_stage(d, j, stage_def("director", "render"), {**DRAFT, **knobs})
    assert e.value.code == code and list((d / "stages").glob("*")) == []


def test_a_plan_saved_in_the_job_renders_under_its_sources_frozen_stem(
    settings: Settings, runner: Runner, djob: tuple[Path, Json]
) -> None:
    """director_page.py reads a folder's plan by its stem from scripts/research/plans/ only. Mutation: the folder
    named for the saved plan (the page then raises FileNotFoundError) turns this red."""
    d, j = djob
    plan = json.loads(json.dumps(PLAN_R12))
    plan["concepts"][0]["transforms"][0]["window"] = [0.2, 0.9]
    save_plan(settings, d, j, "mine", plan, f"frozen:{R12}", "a test")
    rec = run(runner, d, j, "render", {**DRAFT, "plan": "job:mine", "name": "mine"})
    assert rec["state"] == "done" and rec["out_final"].endswith(f"drafts/{R12}_c1-mine")
    save_plan(settings, d, j, "orphan", plan, None, "no source")
    with pytest.raises(StudioError, match="names no frozen director plan"):
        runner.start_stage(d, j, stage_def("director", "render"), {**DRAFT, "plan": "job:orphan", "name": "o"})


def answer(d: Path, name: str, md5: str, **extra: str) -> None:
    write_json(
        d / "answers" / "skeptic_20261105-000001.json",
        {"at": "2026-11-05", "candidates": {name: {"verdict": "READY", "judged_md5": md5, "note": "fine", **extra}}},
    )


def test_the_page_runs_in_place_behind_the_gate_and_keeps_the_previous_page(
    settings: Settings, runner: Runner, djob: tuple[Path, Json]
) -> None:
    """Mutation: the page given a .part path (director_page.py writes RUN/index.html in place, so nothing is renamed
    and the record would be lost), the notes written without the skeptic's look and faults, or the override left off
    the page, turns this red."""
    d, j = djob
    assert run(runner, d, j, "render", {**DRAFT, "draft": 0})["state"] == "done"
    name = f"{R12}_c1"
    with pytest.raises(StudioError, match="the page is refused") as e:
        build_page(runner, d, j, {})
    assert e.value.code == 409
    rec = wait_record(d, build_page(runner, d, j, {"override": True})["id"])
    assert rec["state"] == "done", rec.get("reason")
    root = rel(d / "run", settings.root)
    rec_dir = rel(d / "stages" / rec["id"], settings.root)
    assert rec["argv"][1:] == [
        "scripts/research/director_page.py",
        root,
        "--notes",
        f"{rec_dir}/notes.json",
        "--title",
        f"{PAIR}: round 1",
        "--key",
        f"{j['id']}_r1",
        "--head",
        f"{rec_dir}/head.html",
    ]
    assert rec["out_part"] == rec["out_final"] == f"{root}/index.html" and rec["in_place"] is True
    assert rec["previous"] is None  # no page before the first
    page = (d / "run" / "index.html").read_text()
    assert rec["knobs"]["override"] in page and name in page
    assert read_json(d / "rounds" / "1" / "round.json")["candidates"] == [name]
    assert (d / "run" / "page.md5").read_text().strip() == md5_file(d / "run" / "index.html")
    first = md5_file(d / "run" / "index.html")
    md5 = candidate(settings, d, j, "full", name)["md5_mp4"]
    answer(d, name, md5, look="the pane at t 0.6", faults="a smear over the forest")
    write_json(
        d / "rounds" / "1" / "round.json", {**read_json(d / "rounds" / "1" / "round.json"), "grade": {"text": "ok"}}
    )
    rec2 = wait_record(d, build_page(runner, d, j, {"title": "round two"})["id"])
    assert rec2["state"] == "done" and rec2["previous"] == "previous_index.html"
    assert md5_file(d / "stages" / rec2["id"] / "previous_index.html") == first  # the copy was made before the run
    assert read_json(d / "stages" / rec2["id"] / "notes.json") == {
        name: {"look": "the pane at t 0.6", "faults": "a smear over the forest"}
    }
    assert "--head" not in rec2["argv"] and "round two" in (d / "run" / "index.html").read_text()
    assert "variants" not in rec["knobs"] and "variants" not in rec2["knobs"]  # build_page passes none (Fable F8)


# ---------------------------------------------------------------- the views


def test_a_director_jobs_view_carries_its_keys_and_tiles(
    settings: Settings, runner: Runner, djob: tuple[Path, Json]
) -> None:
    """Mutation: the inspector's plan select left empty for a director job (frozen_plans of the loop), the element
    tables dropped, or the import tile's thumbnail read from a HEIC with cv2, turns this red."""
    d, j = djob
    v = job_view(runner, d, j)
    assert [p["ref"] for p in v["frozen_plans"]] == [f"frozen:{PAIR}_r1", f"frozen:{R12}"]
    dv = v["director"]
    assert [e["id"] for e in dv["elements"]["A"]] == [1, 2, 3]
    assert [e["matte"] for e in dv["elements"]["A"]] == [True, True, False]
    assert [(o["label"], o["A"]) for o in dv["overlap"]] == [(x, 0.3333) for x in ("ceiling 1", "luminary 3", "person")]
    assert (v["resolve"], v["verdict"]) == (None, None)
    tiles = {t["name"]: t for t in v["stages"]}
    assert tiles["import"]["thumb"] == f"/api/jobs/{j['id']}/thumb/raw/0"
    assert tiles["import"]["detail"] == "A 3 el. · 2 mattes; B 3 el. · 0 mattes"
    assert (tiles["resolve"]["detail"], tiles["verdict"]["detail"]) == ("not run", "optional, not run")
    # the plan tile's chip counts the plans the panel offers, with its own hint key (critique B, minor 13: it read
    # "none" beside five frozen plans). Mutation: the old "saved"/"none" state turns this red.
    assert (tiles["plan"]["state"], tiles["plan"]["chip_key"]) == ("2 plans", "director.plans")
    assert tiles["plan"]["detail"] == "2 frozen plans; 0 saved in this job"
    rec = run(runner, d, j, "resolve", {"plan": f"frozen:{R12}", "concept": "c1"})
    run(runner, d, j, "render", DRAFT)
    v = job_view(runner, d, j)
    tiles = {t["name"]: t for t in v["stages"]}
    assert tiles["import"]["thumb"] == f"/api/jobs/{j['id']}/thumb/canvas/A?r={rec['id']}"
    assert tiles["resolve"]["detail"] == "c1 · 64×48 · camera homog · 1 layer"
    assert tiles["render"]["detail"] == "0 full, 1 drafts" and tiles["render"]["generated"] is True
    rv = v["resolve"]
    assert rv["keys"] == ["anchors", "camera", "canvas", "concept", "frames", "info", "layers", "pair", "renderer_md5"]
    assert rv["layers"] == [{"name": "pane", "by": "keyframe_chain", "window": [0.3, 0.92], "depth": "inside"}]
    assert rv["urls"]["canvas_A"].endswith(f"/file/resolve/{rec['id'].replace('_resolve', '')}/canvas_A.png")
    assert [s["name"] for s in stage_views(runner, d, j)] == ORDER


def test_the_render_view_has_the_measures_series_bars_and_frame_tags(
    settings: Settings, runner: Runner, djob: tuple[Path, Json]
) -> None:
    """Mutation: the view reading measure.json (the loop's), the series given one shared index, the residual bar
    dropped, or the step series decoded from loop.mp4, turns this red."""
    d, j = djob
    run(runner, d, j, "render", {**DRAFT, "set": {"pane.window": [0.35, 0.97]}})
    name = f"{R12}_c1"
    v = render_view(settings, d, j, "draft", name)
    info = read_json(d / "drafts" / name / "info.json")
    assert (v["fps"], v["frames"], v["frames_available"]) == (30, 90, 90)
    s = v["series"]
    assert len(s["motion_px"]["points"]) == 89 and s["motion_px"]["pairwise"] is True
    assert len(s["b_inside"]["points"]) == 31 and s["b_inside"]["points"][1][0] == 3  # its own frame index
    assert len(s["residual_edges"]["points"]) == 29 and s["residual_edges"]["bar"] == 0.002
    assert s["halo"] is None  # a quad: no luminary
    steps = [p[1] for p in s["steps"]["points"]]
    assert len(steps) == 89 and round(steps[0], 2) == info["step_first"] and round(max(steps), 2) == info["step_max"]
    m = {x["key"]: x for x in v["measures"]}
    assert m["residual_edge_max"]["bar"]["max"] == 0.002 and m["residual_edge_max"]["past"] is False
    assert m["b_inside_first"]["bar"]["at_or_after"] == 31  # round(0.35 * 89): the moved window's start
    assert m["b_inside_first"]["past"] is (info["b_inside_first"] < 31)
    tags = v["frames_tags"]
    assert (tags[0]["tag"], tags[89]["tag"], tags[10]["tag"]) == ("photo", "photo", "camera")
    assert tags[40]["beats"] == ["pane"] and tags[40]["generated"] is True and tags[10]["generated"] is False
    # the end effect's window [0.92, 1.0] of the plan, and the chain moved to [0.35, 0.97] by the set dict
    assert (tags[85]["tag"], tags[88]["tag"]) == ("pane + end", "end")
    assert v["provenance"]["plan_sha256"] == sha256_file(settings.director_plans / f"{R12}.json")
    assert v["provenance"]["renderer_md5"] == v["provenance"]["script_md5"] == md5_file(settings.director_render)
    assert v["mp4_url"] == f"/api/jobs/{j['id']}/file/drafts/{name}/transition.mp4"


def test_the_motion_marks_follow_the_renderers_rule() -> None:
    """director_render.py:2047-2051. Mutation: the pauses counted over the whole list (the ends of a clip are slow by
    design) or the jumps without the 1 px floor turns this red."""
    mp = [0.0] * 2 + [2.0] * 16 + [0.1] + [2.0] * 16 + [5.0] + [0.0] * 3
    pauses, jumps = dviews.motion_marks(mp)
    assert pauses == [18] and jumps == [2, 18, 19, 35, 36]
    assert dviews.motion_marks([]) == ([], [])


def test_the_plan_view_maps_the_concepts_knobs_in_both_name_forms(settings: Settings, dpair: str) -> None:
    """Mutation: the key form (pane.ot_weight) read as no renderer key, the quad's parallax_push shown as 0.0, or the
    end effect missing from the bars, turns this red."""
    pv = dviews.plan_view(settings, None, f"frozen:{R12}")
    assert (pv["stem"], pv["pair"], pv["relation"]) == (R12, PAIR, "themed")
    c1 = pv["concepts"][0]
    knobs = {k["name"]: k for k in c1["knobs"]}
    assert (knobs["front_per_element"]["set_key"], knobs["front_per_element"]["path"]) == ("front_per_element", [])
    assert (knobs["pane.params.times[0]"]["set_key"], knobs["pane.params.times[0]"]["path"]) == ("pane.times", [0])
    assert knobs["pane.params.times[0]"]["base"] == [0.4]
    assert (knobs["pane.window[1]"]["set_key"], knobs["pane.window[1]"]["base"]) == ("pane.window", [0.3, 0.92])
    assert knobs["pane.ot_weight"]["set_key"] == "pane.ot_weight"
    assert "no --set key" in knobs["container.spec.box"]["readonly"]
    assert "SCHEMA.md:221" in knobs["pane.params.edge"]["readonly"]
    g = {r["key"]: r for r in c1["globals"]}
    assert len(g) == 28 and g["parallax_push"]["default"] == 2.5 and g["parallax_push"]["applies"] is True
    assert (g["end_window"]["default"], g["end_kind"]["default"], g["reflect"]["applies"]) == (
        [0.92, 1.0],
        "b_luma_reveal",
        True,
    )
    assert g["parallax_gain_A"]["default"] == 0.8 and "follows" not in g["parallax_gain_A"]
    assert g["hole_reveal_from"]["readonly"] and g["end_scale"]["applies"] is False  # a disc's key on a quad
    assert [b["key"] for b in c1["beats"]] == ["pane.window"] and c1["end"]["window"] == [0.92, 1.0]
    rows = {r["key"]: r for r in c1["transforms"][0]["rows"]}
    assert rows["times"]["default"] == [0.4] and rows["window"]["default"] == [0.3, 0.92]
    assert "feather" not in rows and rows["edge"]["readonly"]  # a chain reads no feather; table D is shown read-only
    c2 = {r["key"]: r for r in pv["concepts"][1]["sky"]}
    assert c2["shape"]["default"] == "radial_out" and c2["out_at"]["applies"] is True
    assert c2["band"]["applies"] is False and c2["star_window"]["applies"] is True
    assert {r["key"]: r for r in pv["concepts"][1]["globals"]}["parallax_gain_A"]["follows"] == "parallax_gain"
    assert c1["last_round"] is None  # no director_r* round of this pair


def test_the_last_round_button_reads_the_newest_round_render(settings: Settings, dpair: str) -> None:
    """b_design.md decision 2: the button loads them; nothing pre-fills them. Mutation: the oldest round read turns this
    red."""
    for day, knobs in (("2026-10-17", {"a": 1}), ("2026-10-20", {"cont_feather": 14, "parallax_push": 1.5})):
        p = settings.runs / day / "director_r12" / f"{R12}_c1" / "info.json"
        write_json(p, {"knobs": knobs, "wall_s": 63.1, "canvas": [1920, 1440]})
    import os

    os.utime(settings.runs / "2026-10-17" / "director_r12" / f"{R12}_c1" / "info.json", (1, 1))
    lr = dviews.plan_view(settings, None, f"frozen:{R12}")["concepts"][0]["last_round"]
    assert lr["knobs"] == {"cont_feather": 14, "parallax_push": 1.5}
    assert lr["from"] == f"benchmarks/runs/2026-10-20/director_r12/{R12}_c1/info.json"


def test_the_pairs_view_lists_the_pairs_a_plan_names(settings: Settings, dpair: str) -> None:
    """Mutation: the matte count read from every file of the folder (mattes.json counted) turns this red."""
    rows = dviews.pairs_view(settings)
    assert [r["pair"] for r in rows] == [PAIR]
    r = rows[0]
    assert r["plans"] == [f"{PAIR}_r1", R12]
    assert r["photos"]["A"] == {"file": f"{PAIR}_S.jpg", "layers": True, "elements": 3, "mattes": 2, "missing": [3]}
    assert r["photos"]["B"]["missing"] == [1, 2, 3]


def test_the_overlays_draw_each_kind_and_cache_it(settings: Settings, djob: tuple[Path, Json]) -> None:
    """Mutation: an overlay rewritten on every request (no cache), the matte of a missing file left blank instead of
    the hard mask, or an unknown element drawn empty, turns this red."""
    import cv2

    from reveal_studio.media.overlays import GROUP_COLOURS, overlay_png

    d, j = djob
    sizes = {}
    for kind in ("base", "elements", "disparity", "matte_1", "matte_3"):
        p = overlay_png(settings, d, j, "A", kind)
        im = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
        sizes[kind] = (im.shape[1], im.shape[0], im.shape[2] if im.ndim == 3 else 1)
        assert p.parent == d / "cache" / "overlays"
        assert overlay_png(settings, d, j, "A", kind).stat().st_mtime_ns == p.stat().st_mtime_ns  # cached
    assert sizes == {"base": (64, 48, 3), "elements": (64, 48, 4), "disparity": (64, 48, 4), "matte_1": (64, 48, 4),
                     "matte_3": (64, 48, 4)}  # fmt: skip
    hard = cv2.imread(str(overlay_png(settings, d, j, "A", "matte_3")), cv2.IMREAD_UNCHANGED)
    assert hard[40, 30, 3] > 150 and hard[5, 30, 3] == 0  # element 3's band, from the id map (no el_3.png)
    for kind, code in (("matte_9", 404), ("nope", 404)):
        with pytest.raises(StudioError) as e:
            overlay_png(settings, d, j, "A", kind)
        assert e.value.code == code
    groups = {"animal", "appliance", "building", "ceiling", "cloud", "floor", "furniture", "ground", "light",
              "luminary", "object", "opening", "person", "picture", "sky", "star", "structure", "tree",
              "vegetation", "vehicle", "wall", "water"}  # fmt: skip
    assert set(GROUP_COLOURS) == groups  # the 22 groups of the layer tables (2026-11-05)


def test_the_step_series_is_decoded_once_into_the_cache(
    settings: Settings, runner: Runner, djob: tuple[Path, Json]
) -> None:
    """Mutation: the steps written into the render's own folder (a finished render is never written) turns this red."""
    from reveal_studio.media.overlays import step_series

    d, j = djob
    run(runner, d, j, "render", DRAFT)
    c = candidate(settings, d, j, "draft", f"{R12}_c1")
    before = sorted(p.name for p in c["dir"].iterdir())
    steps = step_series(d, c)
    assert len(steps) == 89 and sorted(p.name for p in c["dir"].iterdir()) == before
    (cache,) = (d / "cache" / "steps").iterdir()
    assert json.loads(cache.read_text()) == steps and step_series(d, c) == steps


def test_a_director_draft_marks_a_frame_and_bounds_it_by_its_frames(
    settings: Settings, runner: Runner, djob: tuple[Path, Json]
) -> None:
    """Mutation: the frame bound read from the mp4's decode instead of info.json's frames turns this red."""
    from reveal_studio.jobs.grades import mark_frame

    d, j = djob
    run(runner, d, j, "render", DRAFT)
    name = f"{R12}_c1"
    got = mark_frame(settings, d, j, {"kind": "draft", "name": name, "frame": 47, "note": "the pane"})
    assert (got["frame"], got["note"]) == (47, "the pane") and (
        d / "owner_frames" / f"draft_{name}_f0047.json"
    ).is_file()
    with pytest.raises(StudioError, match=r"outside 0\.\.89"):
        mark_frame(settings, d, j, {"kind": "draft", "name": name, "frame": 90})


def test_a_refused_verdict_shows_its_reason_once_and_keeps_no_part_folder(
    settings: Settings, runner: Runner, djob: tuple[Path, Json], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The shared verdict on a director job, refused: the tile's detail names the refusal, the tile carries no reason
    for the panel head (the panel's box prints it: critique B, minor 5), and the work folder goes (the drive's defect
    7). Mutation: the tile keeping the record's reason turns this red."""
    d, j = djob
    monkeypatch.setenv("FAKE_REFUSE", "align")
    rec = wait_record(d, runner.start_stage(d, j, stage_def("director", "verdict"), {})["id"])
    assert rec["state"] == "refused" and not (d / "verdict.part").exists()
    t = {t["name"]: t for t in job_view(runner, d, j)["stages"]}["verdict"]
    assert (t["state"], t["reason"]) == ("refused", None)
    assert t["detail"] == "refused: the photos share too little detail to align"
