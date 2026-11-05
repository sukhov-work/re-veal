"""The views: job_view's shape, the strip's tiles and the stale rule, the rail's row, record_view, render_view's frame
tags and decode path, the models, the open requests, the registry payload, and the review gate."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import pytest

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, md5_file, read_json, write_json
from reveal_studio.jobs.grades import mark_frame, save_grade, write_request
from reveal_studio.jobs.records import records
from reveal_studio.registry.hints import HINTS
from reveal_studio.registry.loop import FLOWS, stage_def
from reveal_studio.runner.argv import ScriptFlags
from reveal_studio.runner.process import Runner
from reveal_studio.views.job import job_row, job_view, record_view, stage_views
from reveal_studio.views.models import models_view, open_requests, registry_view
from reveal_studio.views.page import build_page
from reveal_studio.views.render import frame_tag, render_view

from .conftest import FLAGS, run, wait_for, wait_record

RENDER = {"plan": "frozen:tiny_a1", "name": "c1", "draft": 0}


@pytest.fixture
def rendered(runner: Runner, registered: tuple[Path, Json]) -> tuple[Path, Json]:
    d, j = registered
    assert run(runner, d, j, "render", RENDER)["state"] == "done"
    return d, j


def tiles(runner: Runner, d: Path, j: Json) -> dict[str, Json]:
    return {v["name"]: v for v in stage_views(runner, d, j)}


def test_job_view_has_every_key_the_page_reads(runner: Runner, rendered: tuple[Path, Json]) -> None:
    d, j = rendered
    v = job_view(runner, d, j)
    assert set(v) == {
        "job",
        "stages",
        "candidates",
        "plans",
        "frozen_plans",
        "requests",
        "rounds",
        "prep",
        "readers",
        "probe",
        "graph",
        "page",
        "owner_frames",
        "script_flags",
    }
    assert v["job"] == j
    assert [s["name"] for s in v["stages"]] == [s["name"] for s in FLOWS["loop"]["stages"]]
    (c,) = v["candidates"]
    assert "dir" not in c and c["name"] == "c1" and c["kind"] == "full" and c["has_frames"] is True
    assert v["prep"]["canvas"] == [64, 48] and v["prep"]["n"] == 2
    assert v["prep"]["depth_maps"] == ["depth_k0.npy", "depth_k1.npy"]
    assert v["prep"]["sources"][0]["name"] == "01.jpg"
    assert v["page"] == {"exists": False, "md5": None, "url": f"/api/jobs/{j['id']}/file/index.html"}
    assert v["script_flags"] == {"progress": True, "frames": True, "readers": True}
    assert v["frozen_plans"][0]["ref"] == "frozen:tiny_a1"
    assert (v["plans"], v["requests"], v["rounds"], v["owner_frames"], v["readers"]) == ([], [], [], [], None)


def test_the_strip_tiles_say_what_each_stage_holds(runner: Runner, rendered: tuple[Path, Json]) -> None:
    d, j = rendered
    t = tiles(runner, d, j)
    assert (t["import"]["state"], t["import"]["detail"]) == ("done", "2 stills")
    assert t["import"]["thumb"] == f"/api/jobs/{j['id']}/thumb/still/0"
    assert t["registration"]["state"] == "done"
    assert t["registration"]["detail"] == "k1 sift+magsac 121 inl. · 64×48"
    assert (t["readers"]["state"], t["readers"]["detail"]) == ("none", "optional, not run")
    assert (t["plan"]["state"], t["plan"]["detail"]) == ("none", "none saved; frozen plans available")
    assert (t["render"]["state"], t["render"]["detail"]) == ("done", "1 full, 0 drafts; unjudged: c1")
    assert t["render"]["thumb"] == f"/api/jobs/{j['id']}/thumb/render/full/c1"
    assert t["render"]["generated"] is True  # the rife leg's frames
    assert t["render"]["latest_knobs"]["name"] == "c1"
    assert (t["skeptic"]["state"], t["skeptic"]["detail"], t["skeptic"]["verdicts"]) == ("none", "no request yet", {})
    assert (t["page"]["state"], t["page"]["detail"]) == ("none", "not built")
    assert (t["grades"]["state"], t["grades"]["detail"]) == ("none", "no round yet")
    assert all(not v["stale"] for v in t.values())


def test_a_later_registration_makes_the_render_stale(runner: Runner, rendered: tuple[Path, Json]) -> None:
    d, j = rendered
    time.sleep(0.01)
    run(runner, d, j, "registration", {"depth_maps": True})
    t = tiles(runner, d, j)
    assert (t["render"]["stale"], t["render"]["stale_after"]) == (True, "registration")
    assert t["registration"]["stale"] is False


def test_a_branch_makes_no_stage_stale_and_goes_stale_after_its_own_stages(
    runner: Runner, rendered: tuple[Path, Json]
) -> None:
    d, j = rendered
    time.sleep(0.01)
    assert run(runner, d, j, "probe", {})["state"] == "done"
    assert run(runner, d, j, "measure", {"render": "full:c1"})["state"] == "done"
    t = tiles(runner, d, j)
    # The probe and the measure write into folders no stage reads. Mutation: dropping the branch filter of the stale
    # rule marks the render "stale after probe" and turns this red.
    assert [n for n, v in t.items() if v["stale"]] == []
    assert (t["probe"]["state"], t["measure"]["state"]) == ("done", "done")
    time.sleep(0.01)
    assert run(runner, d, j, "render", {**RENDER, "name": "c2"})["state"] == "done"
    t = tiles(runner, d, j)
    # A new render leaves the probe alone (its stale_after is the registration) and the measure of c1 too (a measure
    # of a finished mp4 never goes stale). Mutation: the positional rule for branches marks both stale.
    assert (t["probe"]["stale"], t["measure"]["stale"]) == (False, False)
    time.sleep(0.01)
    run(runner, d, j, "registration", {"depth_maps": True})
    t = tiles(runner, d, j)
    assert (t["probe"]["stale"], t["probe"].get("stale_after")) == (True, "registration")
    assert t["measure"]["stale"] is False and t["render"]["stale"] is True


def test_a_failed_attempt_beside_finished_renders_keeps_the_tile_done(
    runner: Runner, rendered: tuple[Path, Json], monkeypatch: pytest.MonkeyPatch
) -> None:
    d, j = rendered
    monkeypatch.setenv("FAKE_FAIL", "render")
    run(runner, d, j, "render", {**RENDER, "name": "c2"})
    t = tiles(runner, d, j)["render"]
    assert (t["state"], t["last_attempt"]) == ("done", "failed: c2")
    assert t["detail"].endswith("· last attempt failed: c2")
    # The panel head prints the reason beside the chip "done": it names the attempt, so the head never reads "done"
    # beside a bare failure line. Mutation: dropping `v["reason"] = attempt_note(latest)` leaves the log's last line.
    assert t["reason"] == "last attempt failed: RuntimeError: the fake render failed"
    row = job_row(runner.settings, d)
    assert row is not None and (row["last_render"], row["last_attempt"]) == ("done", "failed")


def test_the_rail_row_says_done_when_only_a_draft_stands_beside_a_failed_render(
    settings: Settings, runner: Runner, registered: tuple[Path, Json], monkeypatch: pytest.MonkeyPatch
) -> None:
    d, j = registered
    assert run(runner, d, j, "render", {**RENDER, "name": "d1", "draft": 480})["state"] == "done"
    monkeypatch.setenv("FAKE_FAIL", "render")
    assert run(runner, d, j, "render", {**RENDER, "name": "d2", "draft": 480})["state"] == "failed"
    assert tiles(runner, d, j)["render"]["state"] == "done"
    row = job_row(settings, d)
    # The rail row follows the tile: a job that holds a render says done. Mutation: overriding only when a full
    # render exists (`if full and ...`) leaves "failed" in the rail beside the tile's "done".
    assert row is not None and (row["last_render"], row["last_attempt"]) == ("done", "failed")


def test_the_rail_row_names_a_running_record(
    settings: Settings, runner: Runner, registered: tuple[Path, Json], monkeypatch: pytest.MonkeyPatch
) -> None:
    d, j = registered
    monkeypatch.setenv("FAKE_SLOW", "render=2")
    rec = runner.start_stage(d, j, stage_def("loop", "render"), RENDER)
    wait_for(lambda: (d / "stages" / rec["id"] / "log.txt").read_text().count("PROGRESS") > 0, timeout=10)
    row = job_row(settings, d, runner)
    assert row is not None
    (r,) = row["running"]
    # Mutation: listing the record ids alone (the rail then printed "20261105-030817_render" and nothing else).
    assert (r["id"], r["stage"], r["name"], r["progress"]["n"]) == (rec["id"], "render", "c1", 9)
    assert isinstance(r["elapsed_s"], float) and r["elapsed_s"] >= 0
    wait_record(d, rec["id"])


def test_the_rail_row_reconciles_a_record_whose_process_is_gone(
    settings: Settings, runner: Runner, rendered: tuple[Path, Json]
) -> None:
    d, _j = rendered
    (done,) = [r for r in records(d) if r["stage"] == "render"]
    gone = subprocess.Popen(["true"])
    gone.wait()  # a pid that no longer runs: the record's wait thread died before it wrote the terminal state
    rid = "29991231-235959_render"
    (d / "stages" / rid).mkdir()
    write_json(d / "stages" / rid / "stage.json", {**done, "id": rid, "state": "running", "pid": gone.pid})
    before = job_row(settings, d)
    assert before is not None and [r["id"] for r in before["running"]] == [rid]  # the read without the Runner
    row = job_row(settings, d, runner)
    # Mutation: dropping the reconcile in job_row lists the gone record as running until the job is opened.
    assert row is not None and row["running"] == []
    assert read_json(d / "stages" / rid / "stage.json")["state"] == "lost"


def test_a_draft_leaves_the_page_fresh_and_a_full_render_makes_it_stale(
    settings: Settings, runner: Runner, rendered: tuple[Path, Json]
) -> None:
    d, j = rendered
    rec = build_page(runner, d, j, {"override": True})
    assert wait_record(d, rec["id"])["state"] == "done"
    time.sleep(0.01)
    assert run(runner, d, j, "render", {**RENDER, "name": "d1", "draft": 480})["state"] == "done"
    t = tiles(runner, d, j)
    # A page lists full renders only. Mutation: taking the latest render record, a draft, as the page's upstream
    # marks the page "stale after render" (backlog T98).
    assert (t["page"]["state"], t["page"]["stale"]) == ("done", False)
    save_grade(d, {"round": 1, "text": "the grade text"})  # the round gate: round 1's words before the next full one
    time.sleep(0.01)
    assert run(runner, d, j, "render", {**RENDER, "name": "c2"})["state"] == "done"
    t = tiles(runner, d, j)
    assert (t["page"]["stale"], t["page"]["stale_after"]) == (True, "render")


def test_the_readers_tile_names_the_folder_a_later_registration_moved(
    runner: Runner, registered: tuple[Path, Json]
) -> None:
    d, j = registered
    assert run(runner, d, j, "readers", {})["state"] == "done"
    time.sleep(0.01)
    assert run(runner, d, j, "registration", {"depth_maps": True})["state"] == "done"
    t = tiles(runner, d, j)["readers"]
    (prev,) = sorted(p.name for p in (d / "in").glob("tiny_prev_*"))
    # The panel printed "Not run." under the stale message while the inspector showed the done record. Mutation:
    # dropping the lookup of the moved folder leaves the tile without the path the panel prints.
    assert (t["state"], t["stale"], t["stale_after"]) == ("done", True, "registration")
    assert (t["moved_to"], t["detail"]) == (f"in/{prev}/readers", "moved with the previous prep")


def test_the_rail_row(settings: Settings, runner: Runner, rendered: tuple[Path, Json]) -> None:
    d, j = rendered
    row = job_row(settings, d)
    assert row == {
        "id": j["id"],
        "flow": "loop",
        "seq": "tiny",
        "created": j["created"],
        "adopted": False,
        "root": j["root"],
        "source": "Tiny Stills",
        "stills": 2,
        "candidates": 1,
        "unjudged": 1,
        "round": 0,
        "graded": False,
        "ungraded_by_his_word": False,
        "last_render": "done",
        "last_attempt": None,
        "running": [],
    }
    assert job_row(settings, d, runner) == row  # with the Runner: nothing runs, nothing to reconcile
    (d / "job.json").write_text("")
    assert job_row(settings, d) is None


def test_record_view_adds_progress_log_and_the_command(
    runner: Runner, registered: tuple[Path, Json], monkeypatch: pytest.MonkeyPatch
) -> None:
    d, j = registered
    monkeypatch.setenv("FAKE_SLOW", "render=2")
    rec = runner.start_stage(d, j, stage_def("loop", "render"), RENDER)
    wait_for(lambda: (d / "stages" / rec["id"] / "log.txt").read_text().count("PROGRESS") > 0, timeout=10)
    live = record_view(runner, d, read_json(d / "stages" / rec["id"] / "stage.json"))
    assert live["state"] == "running" and live["progress"]["n"] == 9 and isinstance(live["elapsed_s"], float)
    assert live["command"].endswith(f"--set 'in=\"{j['root']}/in/tiny\"' --progress --frames")
    assert live["command"].startswith(f"{runner.settings.python} scripts/research/loop_seq.py render ")
    done = wait_record(d, rec["id"])
    v = record_view(runner, d, done)
    assert v["progress"] is None and "elapsed_s" not in v
    assert any(line.startswith("render: 9 frames") for line in v["log_tail"])


def test_render_view_tags_every_frame(settings: Settings, runner: Runner, rendered: tuple[Path, Json]) -> None:
    d, j = rendered
    mark_frame(settings, d, j, {"kind": "full", "name": "c1", "frame": 4, "note": "a halo"})
    v = render_view(settings, d, j, "full", "c1")
    tags = [t["tag"] for t in v["frames_tags"]]
    assert tags == ["photo"] * 3 + ["generated"] * 2 + ["photo"] * 2 + ["blend"] * 2
    assert [t["generated"] for t in v["frames_tags"]].count(True) == 2
    assert v["frames_tags"][3]["t"] == 0.3333 and v["frames_tags"][3]["method"] == "rife"
    assert v["frames_available"] == 9
    assert v["frame_url"] == f"/api/jobs/{j['id']}/render/full/c1/frame/"
    assert v["mp4_url"] == f"/api/jobs/{j['id']}/file/tiny/c1/loop.mp4"
    assert v["measure"]["frames"] == 9 and v["plan"]["seq"] == "tiny"
    assert [o["frame"] for o in v["owner_frames"]] == [4]
    assert "dir" not in v


def test_render_view_decodes_the_mp4_when_the_script_wrote_no_frames(
    settings: Settings, registered: tuple[Path, Json]
) -> None:
    d, j = registered
    plain = Runner(settings, ScriptFlags(progress=True, frames=False, readers=True))
    rec = run(plain, d, j, "render", {**RENDER, "name": "nf"})
    assert "--frames" not in rec["argv"]
    v = render_view(settings, d, j, "full", "nf")
    assert v["has_frames"] is False and v["frames_available"] == 9
    (cache,) = (d / "cache" / "frames").iterdir()
    assert cache.name == f"full_nf_{v['md5_mp4'][:8]}" and (cache / "done").read_text() == "9"


@pytest.mark.parametrize(
    ("generated", "tag"),
    [
        ("none (photo)", "photo"),
        ("none (blend + motion blur)", "snap"),
        ("none (blend)", "blend"),
        ("none (rewind of step 2)", "rewind"),
        ("none (slices)", "slices"),
        ("none-ish", "ish"),
        ("rife", "generated"),
    ],
)
def test_frame_tag(generated: str, tag: str) -> None:
    assert frame_tag(generated) == tag


def test_models_view_reads_the_manifests(settings: Settings) -> None:
    write_json(settings.root / "models" / "MANIFEST.json", {"matcher": "disk+lightglue", "verified": "2026-09-13"})
    rows = {m["name"]: m for m in models_view(settings)}
    assert rows["reveal matcher"] == {
        "name": "reveal matcher",
        "manifest": "models/MANIFEST.json",
        "ready": True,
        "version": "disk+lightglue",
        "verified": "2026-09-13",
    }
    assert rows["RIFE"]["ready"] is False and rows["RIFE"]["version"] is None
    assert len(rows) == 4


def test_open_requests_lists_the_unanswered_ones_across_jobs(settings: Settings, rendered: tuple[Path, Json]) -> None:
    d, j = rendered
    r1 = write_request(settings, d, j, "skeptic", {"brief": "the halo at mid-leg"})
    req = read_json(d / "requests" / r1["name"])
    assert req["candidates"][0]["md5_mp4"] == md5_file(d / "tiny" / "c1" / "loop.mp4")
    assert req["answer"]["file"] == f"answers/{r1['name']}"
    rows = open_requests(settings)
    assert [(r["job"], r["name"], r["kind"], r["brief"], r["candidates"]) for r in rows] == [
        (j["id"], r1["name"], "skeptic", "the halo at mid-leg", ["c1"])
    ]
    (d / "answers").mkdir()
    write_json(d / "answers" / r1["name"], {"at": "now", "candidates": {}})
    assert open_requests(settings) == []
    with pytest.raises(StudioError, match="a request kind is"):
        write_request(settings, d, j, "evil", {})
    with pytest.raises(StudioError, match="no full render zz"):
        write_request(settings, d, j, "skeptic", {"candidates": ["zz"]})


def test_registry_view_is_what_the_page_builds_from(settings: Settings) -> None:
    v = registry_view(settings, FLAGS, FLOWS)
    assert set(v) == {
        "flows",
        "stage_order",
        "hints",
        "methods",
        "eases",
        "effects",
        "plan_keys",
        "plan_schema",
        "rulings",
        "verdicts",
        "ui_version",
        "script_flags",
        "frozen_plans",
        "runs_date",
        "port",
    }
    assert (v["ui_version"], v["port"], v["runs_date"]) == ("reveal-studio 0.2.0", settings.port, "2026-11-05")
    assert v["hints"] is HINTS


def test_the_page_gate_refuses_unjudged_and_not_ready_candidates(
    settings: Settings, runner: Runner, rendered: tuple[Path, Json]
) -> None:
    d, j = rendered
    with pytest.raises(StudioError) as e:
        build_page(runner, d, j, {})
    assert e.value.code == 409 and e.value.extra == {"refused": ["c1"]}
    assert str(e.value) == (
        "the page is refused: c1 (unjudged: no skeptic verdict for this candidate). "
        "Request the skeptic, or override (the page prints the override)."
    )
    md5 = md5_file(d / "tiny" / "c1" / "loop.mp4")
    write_json(
        d / "answers" / "skeptic_20261105-120000.json",
        {"at": "t", "candidates": {"c1": {"verdict": "NOT READY", "judged_md5": md5, "note": "the ring doubles"}}},
    )
    with pytest.raises(StudioError, match=r"c1 \(NOT READY: the ring doubles\)"):
        build_page(runner, d, j, {})
    assert not (d / "index.html").exists() and not (d / "rounds").exists()
    write_json(
        d / "answers" / "skeptic_20261105-130000.json",
        {"at": "t2", "candidates": {"c1": {"verdict": "READY", "judged_md5": md5}}},
    )
    rec = build_page(runner, d, j, {"title": "judged"})
    assert "override" not in rec["knobs"]
    assert wait_record(d, rec["id"])["state"] == "done"


def test_the_page_override_is_printed_and_kept_in_the_round(
    settings: Settings, runner: Runner, rendered: tuple[Path, Json]
) -> None:
    d, j = rendered
    rec = build_page(runner, d, j, {"override": True, "footer": "his footer", "notes": {"c1": "look at the ring"}})
    text = rec["knobs"]["override"]
    assert text.startswith("Override: built on his word with c1 (unjudged: no skeptic verdict for this candidate) (")
    assert rec["knobs"]["footer"] == "his footer " + text
    assert wait_record(d, rec["id"])["state"] == "done"
    r1 = wait_for(lambda: read_json(d / "rounds" / "1" / "round.json"))
    assert r1["override"] == text
    page = (d / "index.html").read_text()
    assert text in page and "look at the ring" in page
    assert read_json(d / "stages" / rec["id"] / "notes.json") == {"tiny": {"c1": "look at the ring"}}


def test_the_page_needs_a_full_render(runner: Runner, registered: tuple[Path, Json]) -> None:
    d, j = registered
    with pytest.raises(StudioError, match="no full render to put on a page") as e:
        build_page(runner, d, j, {"override": True})
    assert e.value.code == 409
