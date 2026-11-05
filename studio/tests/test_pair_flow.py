"""The pair transition flow (builder P, phase B) on the fake transitions.py and the fake reveal.py of tests/fakes/: the
registry entries, the argv of the relation and the render, the runs and their records, the relation and verdict
views, the render view, the tiles with the stale rule, the page the studio writes behind the gate, the grades in the
picks shape, a restart, and the hint keys the page script asks for. Every assertion names the mutation that turns it
red."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, md5_file, read_json, write_json
from reveal_studio.jobs.grades import save_grade, write_request
from reveal_studio.jobs.store import create_job, create_pair_job
from reveal_studio.registry import pair
from reveal_studio.registry.common import VERDICT_STAGE
from reveal_studio.registry.flows import ALL_FLOWS, FLOWS, identity_of, stage_def
from reveal_studio.registry.hints import HINTS
from reveal_studio.registry.hints_pair import HINTS as PAIR_HINTS
from reveal_studio.runner.argv import argv_for
from reveal_studio.runner.argv_pair import render_name
from reveal_studio.runner.process import Runner
from reveal_studio.views import pair as pv
from reveal_studio.views.job import job_view, stage_views
from reveal_studio.views.page import build_page

from .conftest import FAKES, FLAGS, wait_record

WEB = Path(__file__).resolve().parents[1] / "src/reveal_studio/web"
ORDER = ["import", "verdict", "relation", "render", "skeptic", "page", "grades"]
RANGES = {"seconds": [0.1, 10.0], "color": [0.0, 1.0], "warp": [0.0, 1.0], "anchor_falloff": [0.0, 0.5]}
RANGES["zoom"] = [0.02, 0.5]
"""The ranges TransitionSpec.clamp states (transitions.py:205-216); every other render knob has none."""


def pair_job(settings: Settings, fixture: str) -> tuple[Path, Json]:
    j = create_pair_job(settings, fixture=fixture)
    return settings.root / j["root"], j


def run_pair(runner: Runner, d: Path, j: Json, stage: str, knobs: Json | None = None) -> Json:
    rec = runner.start_stage(d, j, stage_def("pair", stage), knobs or {})
    return wait_record(d, rec["id"])


def tiles(runner: Runner, d: Path, j: Json) -> dict[str, Json]:
    return {t["name"]: t for t in stage_views(runner, d, j)}


def judge(d: Path, name: str, md5: str, verdict: str = "READY") -> None:
    """A skeptic's answer file for one candidate, as the session writes it (answers/skeptic_<n>.json)."""
    n = len(list((d / "answers").glob("skeptic_*.json"))) if (d / "answers").is_dir() else 0
    write_json(
        d / "answers" / f"skeptic_{n:04d}.json",
        {"at": "2026-11-05T12:00:00", "candidates": {name: {"verdict": verdict, "judged_md5": md5, "note": "ok"}}},
    )


def mp4_md5(rec: Json) -> str:
    return str(next(o["md5"] for o in rec["outputs"] if o["path"].endswith("/transition.mp4")))


# ---------------------------------------------------------------- the registry


def test_the_pair_flow_is_enabled_with_its_seven_stages_in_order() -> None:
    """Mutation: the verdict listed as a copy of the shared stage, a stage dropped or moved, or the flow disabled
    (the page then offers no new pair job) turns this red."""
    assert ALL_FLOWS["pair"] is pair.FLOW and FLOWS["pair"] is pair.FLOW and pair.FLOW["enabled"] is True
    assert [s["name"] for s in pair.PAIR_STAGES] == ORDER
    assert pair.PAIR_STAGES[1] is VERDICT_STAGE
    kinds = {s["name"]: s["kind"] for s in pair.PAIR_STAGES}
    assert kinds == {
        "import": "builtin",
        "verdict": "script",
        "relation": "script",
        "render": "script",
        "skeptic": "request",
        "page": "builtin",
        "grades": "builtin",
    }
    rel_, ren = stage_def("pair", "relation"), stage_def("pair", "render")
    assert (rel_["script"], rel_["terminal"], ren["script"], ren["terminal"]) == (
        "transitions",
        "report.json",
        "transitions",
        "report.json",
    )
    assert rel_["knobs"] == [] and stage_def("pair", "page")["stale_after"] == ["render"] and ren["stale_after"] == []


def test_the_identity_files_leave_out_the_report_and_its_clock_keys() -> None:
    """report.json holds correspondence_s, render_s and total_s, so it changes on every run. Mutation: the relation's
    identity naming report.json (a rerun then never says unchanged) turns this red."""
    assert identity_of("pair", "relation") == ["transition.mp4", "strip.jpg"]
    assert identity_of("pair", "render") == ["transition.mp4"]
    assert identity_of("pair", "verdict") == ["metrics.json"]


def test_the_render_knobs_carry_the_ranges_clamp_states_and_no_other() -> None:
    """Mutation: a range the CLI never states (fps [1, 60]) or a flag on draft or max_long (two --max-long flags then
    reach one argv) turns this red."""
    knobs = {k["key"]: k for k in stage_def("pair", "render")["knobs"]}
    assert list(knobs) == [
        "name",
        "draft",
        "max_long",
        "seconds",
        "fps",
        "preset",
        "color",
        "warp",
        "canvas",
        "anchors",
        "anchor_falloff",
        "force_class",
        "camera",
        "zoom",
    ]
    assert {k: v["range"] for k, v in knobs.items() if v["range"] is not None} == RANGES
    assert [k for k, v in knobs.items() if v["flag"] is None] == ["name", "draft", "max_long"]
    assert knobs["preset"]["choices"] == pair.PRESETS and knobs["force_class"]["choices"] == ["", "A", "B"]
    assert knobs["max_long"]["default"] == 1920 and "fixture sweep" in knobs["max_long"]["what"]
    # the sentence states the override; its backlog row (T108) stays in the registry's comment (critique B, copy pass)
    assert "overrides every preset's own value" in knobs["warp"]["what"] and "T108" not in knobs["warp"]["what"]
    assert [k["key"] for k in stage_def("pair", "page")["knobs"]] == ["title", "intro", "footer", "variants"]


def help_flags(text: str) -> dict[str, str]:
    """{flag: the help's sentence} for every option of an argparse --help (the metavar or the {choices} dropped)."""
    out: dict[str, str] = {}
    for m in re.finditer(r"^\s{2}(--[a-z-]+)(.*?)(?=^\s{2}-|\Z)", text, re.M | re.S):
        said = re.sub(r"^\s*(?:[A-Z][A-Z_]*|\{[^}]*\})", "", m.group(2), count=1)
        out[m.group(1)] = " ".join(said.split())
    return out


def test_the_fake_clis_flags_are_the_registrys(tmp_path: Path) -> None:
    """The fake carries the real CLI's flags (tests/integration/test_transitions_help.py checks the real one).
    Mutation: a knob's flag renamed in the registry, or a flag the argv writes that the CLI lacks, turns this red."""
    h = subprocess.run(
        [sys.executable, str(FAKES / "transitions.py"), "pair", "--help"], capture_output=True, text=True, timeout=60
    ).stdout
    flags = help_flags(h)
    knob_flags = {k["flag"] for k in stage_def("pair", "render")["knobs"] if k["flag"]}
    assert knob_flags | {"--out", "--max-long"} == set(flags) - {"--help"}


# ---------------------------------------------------------------- the argv


def test_the_relation_argv_fixes_480_px_and_one_second(settings: Settings, fixture_pair: str) -> None:
    """Mutation: the relation reading a render knob, or naming the originals instead of the job's links, turns this
    red."""
    d, j = pair_job(settings, fixture_pair)
    argv, final, part, inputs = argv_for(settings, FLAGS, stage_def("pair", "relation"), d, j, {}, d / "stages/x")
    root = j["root"]
    assert argv == [
        str(settings.python),
        "transitions.py",
        "pair",
        f"{root}/raw/tiny_1/A.jpg",
        f"{root}/raw/tiny_1/B.jpg",
        "--out",
        f"{root}/relation.part",
        "--max-long",
        "480",
        "--seconds",
        "1",
    ]
    assert (final, part) == (d / "relation", d / "relation.part")
    assert [i["sha256"] for i in inputs] == [i["sha256"] for i in j["inputs"]]


def test_a_render_argv_holds_one_max_long_from_draft_or_max_long(settings: Settings, fixture_pair: str) -> None:
    """Mutation: max_long given its own flag (two --max-long, the CLI keeps the last) or a draft written under the full
    renders' folder turns this red."""
    d, j = pair_job(settings, fixture_pair)
    stage = stage_def("pair", "render")
    from reveal_studio.runner.argv import coerce

    argv, final, part, _ = argv_for(settings, FLAGS, stage, d, j, coerce(stage, {"name": "d1", "draft": 480}), d)
    assert argv.count("--max-long") == 1 and argv[argv.index("--max-long") + 1] == "480"
    assert (final, part) == (d / "drafts/tiny_1/d1", d / "drafts/tiny_1/d1.part")
    argv, final, _, _ = argv_for(settings, FLAGS, stage, d, j, coerce(stage, {"name": "f1"}), d)
    assert argv.count("--max-long") == 1 and argv[argv.index("--max-long") + 1] == "1920"
    assert final == d / "tiny_1/f1"
    tail = argv[argv.index("--max-long") + 2 :]
    assert tail == [
        "--seconds",
        "1.0",
        "--fps",
        "30.0",
        "--preset",
        "morph",
        "--color",
        "0.7",
        "--warp",
        "1.0",
        "--canvas",
        "finish",
        "--anchor-falloff",
        "0.45",
        "--camera",
        "flat",
        "--zoom",
        "0.1",
    ]  # an empty anchors or class passes no flag, so the CLI's own default holds


@pytest.mark.parametrize(
    ("knobs", "name"),
    [({}, "morph_1s"), ({"preset": "flow-dissolve", "seconds": 1.5}, "flow-dissolve_1p5s"), ({"name": "x"}, "x")],
)
def test_an_empty_render_name_becomes_the_preset_and_the_seconds(knobs: Json, name: str) -> None:
    """Mutation: the seconds' point kept in the name (NAME_RE then refuses it) turns this red."""
    assert render_name(knobs) == name


def test_a_render_refuses_a_bad_name_and_a_reserved_pair_name(settings: Settings, fixture_pair: str) -> None:
    """A pair named like the job's own folders would put its renders inside relation/ or verdict/, which a rerun
    replaces whole. Mutation: dropping the reserved-name check turns this red."""
    d, j = pair_job(settings, fixture_pair)
    stage = stage_def("pair", "render")
    with pytest.raises(StudioError, match="letters, digits") as e:
        argv_for(settings, FLAGS, stage, d, j, {"name": "a b"}, d)
    assert e.value.code == 400
    j2 = dict(j, seq="relation")  # a job.json written by hand: the creator refuses the name before any folder exists
    with pytest.raises(StudioError, match="a folder of the job itself") as e:
        argv_for(settings, FLAGS, stage, d, j2, {"name": "r1"}, d)
    assert e.value.code == 409


# ---------------------------------------------------------------- the runs


def test_the_relation_runs_and_a_rerun_says_unchanged(settings: Settings, runner: Runner, fixture_pair: str) -> None:
    """Mutation: the relation's identity naming report.json (whose clock keys differ run to run) turns the second
    run's unchanged_from red; a relation writing outside relation/ turns the folder check red."""
    d, j = pair_job(settings, fixture_pair)
    r1 = run_pair(runner, d, j, "relation")
    assert r1["state"] == "done", r1.get("reason")
    files = sorted(p.name for p in (d / "relation").iterdir())
    assert files == ["report.json", "strip.jpg", "transition.mp4"] and not (d / "relation.part").exists()
    rep1 = md5_file(d / "relation" / "report.json")
    r2 = run_pair(runner, d, j, "relation")
    assert r2["state"] == "done" and r2.get("unchanged_from") == r1["id"]
    assert md5_file(d / "relation" / "report.json") != rep1  # the clock keys moved; the mp4 and the strip did not
    assert r2["script_md5"] == md5_file(settings.transitions)


def test_the_relation_view_reads_the_report_the_bars_and_the_frame_urls(
    settings: Settings, runner: Runner, fixture_pair: str
) -> None:
    """Mutation: the class read from the render instead of the relation's report, a bar's verdict inverted, or the
    frame URLs without the mp4's md5 (a browser then keeps a replaced relation's frames) turns this red."""
    d, j = pair_job(settings, fixture_pair)
    assert pv.relation_view(settings, d, j)["exists"] is False
    rec = run_pair(runner, d, j, "relation")
    v = pv.relation_view(settings, d, j)
    rep = v["report"]
    assert (v["exists"], v["state"], v["record"], v["long"]) == (True, "done", rec["id"], 480)
    assert (rep["class"], rep["method"], rep["sparse_inliers"], rep["median_disp_px"]) == (
        "B",
        "saliency-panzoom",
        0,
        24.71,
    )
    assert (rep["canvas"], v["n_frames"]) == ([64, 48], 30) and "outputs" not in rep
    md5 = {o["path"].rsplit("/", 1)[1]: o["md5"] for o in rec["outputs"]}
    assert (v["md5_mp4"], v["md5_strip"]) == (md5["transition.mp4"], md5["strip.jpg"])
    assert v["a_url"] == f"/api/jobs/{j['id']}/relation/frame/0?m={md5['transition.mp4'][:8]}"
    assert v["b_url"].startswith(f"/api/jobs/{j['id']}/relation/frame/29?m=")
    verdicts = {b["key"]: b["verdict"] for b in v["bars"]}
    assert verdicts["endpoint.first_vs_A"] == verdicts["flicker.max"] == verdicts["flicker.edge_ratio"] == "within"
    assert verdicts["warping_error"] is None and verdicts["goal.feat_floor"] is None  # no bar recorded
    frames = pv.relation_frames(settings, d, j)
    assert frames is not None and len(list(frames.glob("f*.jpg"))) == 30


def test_bars_judge_against_the_recorded_bars_only() -> None:
    """Mutation: an endpoint above 0 read as within, or edge_ratio judged against 1.0 instead of the 1.5 every preset
    keeps, turns this red."""
    q = {"quality": {"endpoint": {"first_vs_A": 0.4, "last_vs_B": 0.0}, "flicker": {"edge_ratio": 1.2, "max": 0.2}}}
    by = {b["key"]: b for b in pv.bars(q)}
    assert by["endpoint.first_vs_A"]["verdict"] == "past bar" and by["endpoint.last_vs_B"]["verdict"] == "within"
    assert by["flicker.edge_ratio"]["verdict"] == "within" and by["flicker.edge_ratio"]["bar"] == "below 1.5"
    assert by["flicker.max"]["verdict"] == "past bar" and by["flicker.mean"]["verdict"] is None
    assert all(b["hint"] in PAIR_HINTS for b in by.values())


def test_a_full_render_and_a_draft_become_candidates(settings: Settings, runner: Runner, fixture_pair: str) -> None:
    """Mutation: the spec reader losing the preset (the report keeps the expanded style only), the md5 taken from a
    hash instead of the record, or a draft listed as a full render turns this red."""
    d, j = pair_job(settings, fixture_pair)
    full = run_pair(runner, d, j, "render", {"name": "f1", "preset": "dissolve"})
    draft = run_pair(runner, d, j, "render", {"name": "d1", "draft": 480})
    assert full["state"] == draft["state"] == "done"
    view = job_view(runner, d, j)
    by = {(c["kind"], c["name"]): c for c in view["candidates"]}
    f1, d1 = by[("full", "f1")], by[("draft", "d1")]
    md5 = {o["path"].rsplit("/", 1)[1]: o["md5"] for o in full["outputs"]}
    assert (f1["preset"], f1["md5_mp4"], f1["fps"], f1["frames"], f1["class"]) == (
        "dissolve",
        md5["transition.mp4"],
        30.0,
        30,
        "B",
    )
    assert (d1["draft"], d1["preset"], f1["unjudged"], d1["unjudged"]) == (480, "morph", True, False)
    assert f1["record"] == full["id"] and f1["quality"]["flicker"]["edge_ratio"] is not None


def test_a_finished_render_is_never_overwritten(settings: Settings, runner: Runner, fixture_pair: str) -> None:
    """Mutation: start_stage's existence check skipped for the pair's render turns this red."""
    d, j = pair_job(settings, fixture_pair)
    run_pair(runner, d, j, "render", {"name": "f1"})
    before = md5_file(d / "tiny_1/f1/transition.mp4")
    with pytest.raises(StudioError, match="never overwritten") as e:
        runner.start_stage(d, j, stage_def("pair", "render"), {"name": "f1"})
    assert e.value.code == 409 and md5_file(d / "tiny_1/f1/transition.mp4") == before


def test_a_refused_render_keeps_the_cli_failed_line(
    settings: Settings, runner: Runner, fixture_pair: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """transitions.py prints FAILED: on stderr and exits 2. Mutation: the runner reading stdout only, or a refusal
    renamed onto the final folder, turns this red."""
    d, j = pair_job(settings, fixture_pair)
    monkeypatch.setenv("FAKE_REFUSE", "pair")
    rec = run_pair(runner, d, j, "render", {"name": "r1"})
    assert rec["state"] == "refused" and rec["reason"] == "FAILED: the fake transitions.py refuses this pair"
    assert not (d / "tiny_1/r1").exists()
    monkeypatch.delenv("FAKE_REFUSE")
    rec = run_pair(runner, d, j, "render", {"name": "r2", "anchors": "1,2,3,4"})
    assert rec["state"] == "refused" and "three anchor pairs" in rec["reason"]


# ---------------------------------------------------------------- Reveal's verdict


def test_the_verdict_view_shows_the_refusal_and_its_reason(
    settings: Settings, runner: Runner, fixture_pair: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mutation: a refused verdict shown with metrics, or its reason dropped, turns this red; so does the tile keeping
    the reason, which the panel head then prints beside the panel's own box (critique B, minor 5: three times)."""
    d, j = pair_job(settings, fixture_pair)
    assert pv.verdict_view(settings, d, j)["state"] == "none"
    monkeypatch.setenv("FAKE_REFUSE", "align")
    rec = run_pair(runner, d, j, "verdict")
    v = pv.verdict_view(settings, d, j)
    assert (v["state"], v["record"], v["metrics"], v["stills"]) == ("refused", rec["id"], None, None)
    assert v["reason"] == "FAILED: the photos share too little detail"
    t = tiles(runner, d, j)["verdict"]
    assert t["state"] == "refused" and t["detail"] == v["reason"] and t["branch"] and t["parent"] == "import"
    assert t["reason"] is None  # the panel's box prints it once


def test_the_verdict_view_shows_the_metrics_and_the_stills(
    settings: Settings, runner: Runner, fixture_pair: str
) -> None:
    """Mutation: the metrics read from the top of metrics.json (Reveal nests them under `metrics`) turns this red."""
    d, j = pair_job(settings, fixture_pair)
    rec = run_pair(runner, d, j, "verdict")
    v = pv.verdict_view(settings, d, j)
    assert v["state"] == "done" and v["done_record"] == rec["id"]
    assert v["metrics"] == {"method": "sift", "inliers": 481, "rmse_px": 0.79, "confidence": 94, "passed": True}
    assert v["stills"] == {
        "before": f"/api/jobs/{j['id']}/file/verdict/before.jpg",
        "after_aligned": f"/api/jobs/{j['id']}/file/verdict/after_aligned.jpg",
    }
    assert tiles(runner, d, j)["verdict"]["detail"] == "sift · 481 inliers · rmse 0.79 px · confidence 94"


# ---------------------------------------------------------------- the render view and the tiles


def test_the_render_view_carries_the_spec_fps_tags_steps_bars_and_decode(
    settings: Settings, runner: Runner, fixture_pair: str
) -> None:
    """Mutation: fps from the loop's 25, a frame tag off by one at the ends, the decoded series with one value per frame
    instead of per step, or a decode check that passes a wrong frame count turns this red."""
    d, j = pair_job(settings, fixture_pair)
    run_pair(runner, d, j, "render", {"name": "f1", "fps": 24.0, "seconds": 0.5})
    r = pv.render_view(settings, d, j, "full", "f1")
    assert (r["fps"], r["frames"], r["frames_available"]) == (24.0, 12, 12)
    tags = r["frames_tags"]
    assert [t["tag"] for t in tags] == ["photo"] + ["blend"] * 10 + ["photo"]
    assert tags[0]["t"] is None and tags[1]["t"] == 0.091 and not any(t["generated"] for t in tags)
    assert len(r["steps"]) == 11 and all(isinstance(x, float) for x in r["steps"])
    assert {c["key"]: c["verdict"] for c in r["decode"]} == {
        "frames": "within",
        "size": "within",
        "fps": "within",
        "darkest": "within",
    }
    assert set(r["flicker"]) == {"mean", "max", "spikiness", "edge_ratio"} and r["report"]["class"] == "B"
    assert r["strip_url"] == f"/api/jobs/{j['id']}/file/tiny_1/f1/strip.jpg" and r["class_differs"] is False
    assert r["mp4_url"] == f"/api/jobs/{j['id']}/file/tiny_1/f1/transition.mp4"


def test_a_render_of_another_class_than_the_relation_warns(
    settings: Settings, runner: Runner, fixture_pair: str
) -> None:
    """Mutation: the class comparison dropped from the relation view or the render tile turns this red."""
    d, j = pair_job(settings, fixture_pair)
    run_pair(runner, d, j, "relation")
    run_pair(runner, d, j, "render", {"name": "fa", "force_class": "A"})
    v = pv.relation_view(settings, d, j)
    assert v["differs"] == [{"name": "fa", "kind": "full", "class": "A"}]
    t = tiles(runner, d, j)
    want = [{"key": "relation.class_differs", "text": "class differs from B: fa"}]
    assert t["render"]["warnings"] == want and t["relation"]["warnings"] == want
    assert pv.render_view(settings, d, j, "full", "fa")["class_differs"] is True


def test_the_tiles_of_a_pair_job_and_the_stale_rule(settings: Settings, runner: Runner, fixture_pair: str) -> None:
    """Mutation: a relation rerun marking the renders stale (a render reads A and B only), the page not going stale
    after a later full render, or the import tile pointing a HEIC original at cv2 turns this red."""
    d, j = pair_job(settings, fixture_pair)
    t = tiles(runner, d, j)
    assert [x["name"] for x in stage_views(runner, d, j)] == ORDER
    assert (t["import"]["detail"], t["import"]["thumb"]) == (
        "A tiny_1_S.jpg · B tiny_1_F.jpg",
        f"/api/jobs/{j['id']}/thumb/raw/0",
    )
    assert (t["relation"]["detail"], t["verdict"]["detail"], t["page"]["detail"]) == (
        "not run",
        "optional, not run",
        "not built",
    )
    run_pair(runner, d, j, "relation")
    run_pair(runner, d, j, "render", {"name": "f1"})
    run_pair(runner, d, j, "relation")
    t = tiles(runner, d, j)
    assert t["relation"]["detail"] == "class B at 480 px · saliency-panzoom · 0 inliers · 24.71 px"
    assert t["import"]["thumb"] == pv.relation_view(settings, d, j)["a_url"]
    assert t["render"]["stale"] is False and t["render"]["detail"] == "1 full, 0 drafts; unjudged: f1"
    judge(d, "f1", mp4_md5(read_json(next((d / "stages").glob("*_render/stage.json")))))
    rec = build_page(runner, d, j, {})
    assert tiles(runner, d, j)["page"]["stale"] is False and rec["state"] == "done"
    run_pair(runner, d, j, "render", {"name": "d1", "draft": 480})
    assert tiles(runner, d, j)["page"]["stale"] is False  # a draft is no upstream of the page
    save_grade(d, {"round": 1, "text": "fine"})
    run_pair(runner, d, j, "render", {"name": "f2"})
    page = tiles(runner, d, j)["page"]
    assert page["stale"] is True and page["stale_after"] == "render"


# ---------------------------------------------------------------- the page and the grades


def test_a_heic_original_gets_no_cv2_thumbnail_before_the_relation(
    settings: Settings, runner: Runner, fixture_pair: str
) -> None:
    """cv2 reads no HEIC, so /thumb/raw/0 would answer 500. Mutation: the import tile pointing every original at the
    raw thumbnail turns this red."""
    d, j = pair_job(settings, fixture_pair)
    heic = dict(j, inputs=[dict(j["inputs"][0], name="match_1_S.HEIC"), j["inputs"][1]])
    assert tiles(runner, d, heic)["import"]["thumb"] is None
    run_pair(runner, d, j, "relation")
    assert tiles(runner, d, heic)["import"]["thumb"] == pv.relation_view(settings, d, j)["a_url"]


def two_renders(settings: Settings, runner: Runner, fixture_pair: str) -> tuple[Path, Json, dict[str, str]]:
    d, j = pair_job(settings, fixture_pair)
    run_pair(runner, d, j, "relation")
    md5 = {}
    for n in ("f1", "f2"):
        rec = run_pair(runner, d, j, "render", {"name": n})
        md5[n] = mp4_md5(rec)
    return d, j, md5


def test_the_page_is_refused_behind_the_gate_then_written_on_an_override(
    settings: Settings, runner: Runner, fixture_pair: str
) -> None:
    """Mutation: the builtin page written before the gate ran, the override left out of the footer and the round, or
    the round opened on another file than the page turns this red."""
    d, j, md5 = two_renders(settings, runner, fixture_pair)
    with pytest.raises(StudioError, match="the page is refused") as e:
        build_page(runner, d, j, {})
    assert e.value.code == 409 and not (d / "index.html").exists() and not list(d.glob("stages/*_page"))
    rec = build_page(runner, d, j, {"override": True, "footer": "P test", "notes": {"f1": "the mid frame"}})
    page = d / "index.html"
    assert (rec["state"], rec["builtin"], rec["argv"], rec["stage"]) == ("done", True, [], "page")
    assert (d / "stages" / rec["id"] / "done").is_file() and (d / "stages" / rec["id"] / "log.txt").is_file()
    rnd = read_json(d / "rounds/1/round.json")
    assert (rnd["record"], rnd["candidates"], rnd["page_md5"]) == (rec["id"], ["f1", "f2"], md5_file(page))
    assert rnd["override"] == rec["knobs"]["override"] and rnd["override"].startswith("Override: built on his word")
    assert (d / "page.md5").read_text().strip() == md5_file(page) == rec["outputs"][0]["md5"]
    html = page.read_text()
    assert "P test" in html and rnd["override"] in html and "the mid frame" in html
    assert "tiny_1/f1/transition.mp4" in html and "tiny_1/f2/strip.jpg" in html and "frame 29<br>1.00 s" in html
    assert (d / pv.PAGE_A).is_file() and (d / pv.PAGE_B).is_file() and f"src='{pv.PAGE_A}'" in html
    assert [o["path"].rsplit("/", 1)[1] for o in rec["outputs"]] == ["index.html", pv.PAGE_A, pv.PAGE_B]
    assert [i["md5"] for i in rec["inputs"]] == [md5["f1"], md5["f2"]]
    assert md5_file(d / "rounds/1/index.html") == md5_file(page)


def test_a_second_page_keeps_the_first_and_lists_the_variants_in_order(
    settings: Settings, runner: Runner, fixture_pair: str
) -> None:
    """Mutation: the previous page overwritten without its copy beside the record, or the variants' order lost,
    turns this red; an unknown variant refused only after a file was written turns the last check red."""
    d, j, md5 = two_renders(settings, runner, fixture_pair)
    for n in ("f1", "f2"):
        judge(d, n, md5[n])
    first = build_page(runner, d, j, {})
    before = md5_file(d / "index.html")
    save_grade(d, {"round": 1, "text": "again"})
    with pytest.raises(StudioError, match="variants: nope") as e:
        build_page(runner, d, j, {"variants": ["nope"]})
    assert e.value.code == 400 and md5_file(d / "index.html") == before
    second = build_page(runner, d, j, {"variants": ["f2", "f1"]})
    assert md5_file(d / "stages" / second["id"] / "previous_index.html") == before != md5_file(d / "index.html")
    html = (d / "index.html").read_text()
    assert html.index("id='f2'") < html.index("id='f1'") and second["knobs"]["variants"] == ["f2", "f1"]
    assert read_json(d / "rounds/2/round.json")["variants"] == ["f2", "f1"] and first["id"] != second["id"]


def test_a_grade_in_the_picks_shape_and_the_grades_tile(settings: Settings, runner: Runner, fixture_pair: str) -> None:
    """Mutation: the picks written without the shape check (an extra key passes), or the tile reading the text only,
    turns this red."""
    d, j, _ = two_renders(settings, runner, fixture_pair)
    build_page(runner, d, j, {"override": True})
    props = {"one_picture": True, "transforms": False, "not_invented": True}
    picks = {
        "date": "2026-11-05T18:00:00Z",
        "page": f"{j['id']} round 1",
        "best": {"tiny_1": "f2"},
        "clips": {"f1": {"acceptable": False, "note": "a seam", "props": props}},
    }
    with pytest.raises(StudioError):
        save_grade(d, {"round": 1, "picks": dict(picks, extra=1), "text": "x"})
    r = save_grade(d, {"round": 1, "picks": picks, "text": "his words"})
    assert read_json(d / r["grade"]["picks"]) == picks and r["grade"]["text"] == "his words"
    t = tiles(runner, d, j)["grades"]
    assert (t["state"], t["detail"]) == ("graded", "round 1: best f2; his words")


def test_the_skeptic_request_carries_the_pairs_crops(settings: Settings, runner: Runner, fixture_pair: str) -> None:
    """Mutation: the request dropping the body's crops turns this red."""
    d, j, md5 = two_renders(settings, runner, fixture_pair)
    crops = [{"candidate": "f1", "frames": [1, 28, 14], "pairs": [[0, 1], [28, 29]]}]
    r = write_request(settings, d, j, "skeptic", {"brief": "the mid frame", "candidates": ["f1"], "crops": crops})
    req = read_json(settings.root / r["file"])
    assert req["crops"] == crops and [c["md5_mp4"] for c in req["candidates"]] == [md5["f1"]]
    assert tiles(runner, d, j)["skeptic"]["state"] == "waiting"
    # an answer naming no verdict leaves f1 unjudged: the tile says so, in a muted chip with chip.answered's hint
    # (critique B, minor 12: a green "answered" sat over three unjudged renders). Mutation: the tile reading any
    # answer as "answered" turns this red.
    ans = d / "answers" / Path(r["file"]).name
    write_json(ans, {"at": "2026-11-05T22:00:00", "candidates": {}})
    t = tiles(runner, d, j)["skeptic"]
    assert (t["state"], t["detail"]) == ("answered (0 verdicts)", f"{ans.name} answered with no verdict")
    write_json(ans, {"at": "2026-11-05T22:00:00", "candidates": {"f1": {"verdict": "READY", "judged_md5": md5["f1"]}}})
    assert tiles(runner, d, j)["skeptic"]["state"] == "answered"


# ---------------------------------------------------------------- a restart, the job view, the fixtures


def test_a_restart_reattaches_a_running_pair_render(
    settings: Settings, runner: Runner, fixture_pair: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The record names transitions.py as its argv[1]. Mutation: pid_alive looking for loop_seq.py, or the render's
    .part path missing from its argv, marks the live child lost and turns this red."""
    d, j = pair_job(settings, fixture_pair)
    monkeypatch.setenv("FAKE_SLOW", "pair=2")
    rec = runner.start_stage(d, j, stage_def("pair", "render"), {"name": "slow", "draft": 480})
    runner.finalize = lambda *a, **k: None  # type: ignore[method-assign]  # the first server is gone (2026-11-05)
    r2 = Runner(settings, FLAGS)
    assert r2.reconcile(d, read_json(d / "stages" / rec["id"] / "stage.json"))["state"] == "running"
    assert rec["id"] in r2.watching
    done = wait_record(d, rec["id"], timeout=30)
    assert done["state"] == "done" and "finished after a restart" in done["note"]
    assert (d / "drafts/tiny_1/slow/transition.mp4").is_file() and not (d / "drafts/tiny_1/slow.part").exists()


def test_the_job_view_carries_the_relation_and_the_verdict(
    settings: Settings, runner: Runner, fixture_pair: str
) -> None:
    """Mutation: extras dropping a key turns this red; the loop's keys stay as every flow's job view has them."""
    d, j = pair_job(settings, fixture_pair)
    v = job_view(runner, d, j)
    assert v["relation"]["exists"] is False and v["verdict"]["state"] == "none"
    assert (v["prep"], v["readers"], v["probe"], v["frozen_plans"]) == (None, None, None, [])


def test_create_job_makes_a_pair_job_now_the_flow_is_enabled(settings: Settings, fixture_pair: str) -> None:
    """Mutation: create_job's flow gate refusing an enabled pair flow turns this red."""
    j = create_job(settings, "pair", fixture=fixture_pair)
    assert (j["flow"], j["seq"], j["fixture"]) == ("pair", "tiny_1", "tiny_1")


def test_fixture_pairs_lists_every_pair_with_both_photos(settings: Settings, fixture_pair: str) -> None:
    """Mutation: a pair listed without its F photo, or the S photo's extension forced to .jpg, turns this red."""
    fx = settings.fixtures
    (fx / "odd_2_S.HEIC").write_bytes(b"heic")
    (fx / "odd_2_F.png").write_bytes(b"png")
    (fx / "alone_3_S.jpg").write_bytes(b"jpg")
    got = pv.fixture_pairs(settings)
    assert [p["name"] for p in got] == ["odd_2", "tiny_1"]
    assert got[0]["A"] == {"name": "odd_2_S.HEIC", "bytes": 4} and got[0]["B"]["name"] == "odd_2_F.png"


def test_strip_labels_follow_the_strips_eight_tiles() -> None:
    """transitions.py picks np.linspace(0, n - 1, min(8, n)).round(). Mutation: k fixed at 8 for a short clip turns
    this red."""
    assert pv.strip_labels(30, 1.0) == [
        (0, 0.0),
        (4, 0.14),
        (8, 0.28),
        (12, 0.41),
        (17, 0.59),
        (21, 0.72),
        (25, 0.86),
        (29, 1.0),
    ]
    assert [i for i, _ in pv.strip_labels(3, 0.1)] == [0, 1, 2]


# ---------------------------------------------------------------- the hints the page asks for


def page_keys(text: str) -> set[str]:
    keys = set(re.findall(r'data-hint="([^"+]+)"', text))
    keys |= set(re.findall(r"'((?:control\.pair_|report\.|relation\.|verdict\.)[^']+)'", text))
    return keys


def test_every_hint_key_of_pair_js_is_in_the_table() -> None:
    """test_registry.py scans the loop's prefixes only; this scan adds report., relation. and verdict. Mutation: a key
    in pair.js without its row in hints_pair.py turns this red."""
    keys = page_keys((WEB / "js" / "pair.js").read_text())
    assert len(keys) >= 40, sorted(keys)
    assert sorted(k for k in keys if k not in HINTS) == []


def test_the_pair_hints_keep_their_prefixes_and_their_sources() -> None:
    """Mutation: a pair hint under the loop's chip. prefix (two flows then share one key space) turns this red."""
    prefixes = ("control.pair_", "report.", "relation.", "verdict.")
    assert [k for k in PAIR_HINTS if not k.startswith(prefixes)] == []
    assert all(HINTS[k] is PAIR_HINTS[k] for k in PAIR_HINTS)
    for k, h in PAIR_HINTS.items():
        assert max(len(s.split()) for s in re.split(r"(?<=[.!?])\s+", h["what"])) <= 60, k


def test_the_new_pair_job_button_has_its_hint() -> None:
    """rail.js draws btnNew_pair with the key control.pair_new_job. Mutation: the row removed turns this red."""
    assert "control.pair_new_job" in HINTS and "newJob" in (WEB / "js" / "pair.js").read_text()


def test_a_pair_named_like_a_job_folder_is_refused_at_creation(settings: Settings, fixture_pair: str) -> None:
    """A pair named "relation" would put its full renders inside relation/, which a relation rerun replaces: the
    creator refuses it (400) before any folder exists. Red if create_pair_job stops reading RESERVED_NAMES."""
    from reveal_studio.jobs.store import create_pair_job, studio_dir
    from reveal_studio.registry.pair import RESERVED_NAMES

    before = sorted(p.name for p in studio_dir(settings).glob("*")) if studio_dir(settings).is_dir() else []
    for name in sorted(RESERVED_NAMES)[:3]:
        with pytest.raises(StudioError, match="folder of the job itself") as e:
            create_pair_job(settings, fixture=fixture_pair, seq=name)
        assert e.value.code == 400
    after = sorted(p.name for p in studio_dir(settings).glob("*")) if studio_dir(settings).is_dir() else []
    assert after == before
