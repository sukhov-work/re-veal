"""The runner's rules: a run to done (outputs, md5s, the `done` marker), progress, failed and refused, cancel, the
reconciliation after a restart, the never-overwrite rule for renders, the registration's rerun and busy rules, the
readers' replacement, the page's rounds, the round gate, the "unchanged" rule, the script probe and the lock."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, md5_file, now_iso, read_json, rel, sha256_file, write_json
from reveal_studio.jobs.grades import save_grade
from reveal_studio.jobs.plans import run_warnings, save_plan
from reveal_studio.jobs.records import progress_of, records
from reveal_studio.jobs.store import create_director_job, create_job, create_pair_job, job_root
from reveal_studio.registry.common import VERDICT_STAGE
from reveal_studio.registry.entries import K
from reveal_studio.registry.flows import stage_def
from reveal_studio.runner import argv_common, argv_director, argv_loop, argv_pair
from reveal_studio.runner.argv import ScriptFlags, builder_of, coerce, flags_of, probe_script_flags
from reveal_studio.runner.lock import LockHeld, take_lock
from reveal_studio.runner.process import Runner

from .conftest import FLAGS, FROZEN_PLAN, run, wait_for, wait_record

RENDER = {"plan": "frozen:tiny_a1", "name": "c1", "draft": 0}


def dead_pid() -> int:
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    p.wait()
    return p.pid


def hand_record(
    d: Path,
    rid: str,
    stage: str,
    pid: int,
    out_part: Path,
    out_final: Path,
    terminal: str,
    settings: Settings,
    state: str = "running",
) -> Json:
    """A record as a server that died would have left it."""
    rec: Json = {
        "id": rid,
        "stage": stage,
        "state": state,
        "argv": [str(settings.python), "scripts/research/loop_seq.py"],
        "pid": pid,
        "started": now_iso(),
        "ended": None,
        "wall_s": None,
        "exit_code": None,
        "knobs": {"name": out_final.name},
        "inputs": [],
        "outputs": [],
        "script_md5": "x",
        "out_part": rel(out_part, settings.root),
        "out_final": rel(out_final, settings.root),
        "terminal": terminal,
        "log": "log.txt",
        "ui_version": "studio A1 2026-11-04",
    }
    (d / "stages" / rid).mkdir(parents=True)
    (d / "stages" / rid / "log.txt").write_text("PROGRESS 3 9 frames\n")
    write_json(d / "stages" / rid / "stage.json", rec)
    return rec


def test_a_registration_runs_to_done_with_md5s_and_the_done_marker(
    settings: Settings, runner: Runner, job: tuple[Path, Json]
) -> None:
    d, j = job
    rec = run(runner, d, j, "registration", {"ref": 0, "depth_maps": True, "lock_window": "1,2,10,12;3,4,20,22"})
    rec_dir = d / "stages" / rec["id"]
    assert (rec["state"], rec["exit_code"]) == ("done", 0)
    assert (rec_dir / "done").exists()
    prep = d / "in" / "tiny"
    assert not (d / "in" / "tiny.part").exists()
    names = sorted(Path(o["path"]).name for o in rec["outputs"])
    assert names == ["depth_k0.npy", "depth_k1.npy", "k0.png", "k1.png", "prep.json"]
    for o in rec["outputs"]:
        assert o["md5"] == md5_file(settings.root / o["path"])
    assert rec["argv"][:4] == [str(settings.python), "scripts/research/loop_seq.py", "prep", f"{j['root']}/raw/tiny"]
    assert rec["argv"][4:] == [
        "--out",
        rel(d / "in" / "tiny.part", settings.root),
        "--long",
        "1920",
        "--ref",
        "0",
        "--bg-depth",
        "0.0",
        "--min-inliers",
        "40",
        "--depth-maps",
        "--lock-window",
        "1,2,10,12;3,4,20,22",
    ]
    assert rec["script_md5"] == md5_file(settings.loop_seq)
    assert rec["inputs"] == [{"path": i["path"], "sha256": i["sha256"]} for i in j["inputs"]]
    assert (rec["terminal"], rec["ui_version"], rec["out_final"]) == (
        "prep.json",
        "reveal-studio 0.2.0",
        rel(prep, settings.root),
    )
    assert isinstance(rec["wall_s"], float)
    assert read_json(prep / "prep.json")["frames"][1]["lock"]["shift_px"] == [-1.0, 2.0]


def test_progress_is_read_from_the_log_while_a_render_runs(
    settings: Settings, runner: Runner, registered: tuple[Path, Json], monkeypatch: pytest.MonkeyPatch
) -> None:
    d, j = registered
    monkeypatch.setenv("FAKE_SLOW", "render=1.5")
    rec = runner.start_stage(d, j, stage_def("loop", "render"), RENDER)
    prog = wait_for(lambda: progress_of(d / "stages" / rec["id"]), timeout=10)
    assert prog["phase"] == "frames" and prog["n"] == 9 and 0 <= prog["i"] <= 9
    assert rec["argv"][-4:] == ["--set", f'in="{j["root"]}/in/tiny"', "--progress", "--frames"]
    done = wait_record(d, rec["id"])
    assert done["state"] == "done"
    out = job_root(settings, j) / "tiny" / "c1"
    m = read_json(out / "measure.json")
    mp4 = next(o for o in done["outputs"] if o["path"].endswith("/loop.mp4"))
    assert mp4["md5"] == m["md5_mp4"] == md5_file(out / "loop.mp4")
    assert read_json(out / "plan.json")["in"] == f"{j['root']}/in/tiny"  # --set in= is this job's prep
    assert [i["path"] for i in done["inputs"]] == [
        "scripts/research/plans/loops/tiny_a1.json",
        f"{j['root']}/in/tiny/prep.json",
    ]
    assert done["inputs"][0]["sha256"] == sha256_file(settings.frozen_plans / "tiny_a1.json")
    assert progress_of(d / "stages" / rec["id"]) == {"i": 9, "n": 9, "phase": "measure"}


def test_a_failing_stage_is_failed_with_the_logs_last_line(
    runner: Runner, registered: tuple[Path, Json], monkeypatch: pytest.MonkeyPatch
) -> None:
    d, j = registered
    monkeypatch.setenv("FAKE_FAIL", "render")
    rec = run(runner, d, j, "render", RENDER)
    assert (rec["state"], rec["exit_code"], rec["reason"]) == ("failed", 1, "RuntimeError: the fake render failed")
    assert not (d / "stages" / rec["id"] / "done").exists()
    assert not (d / "tiny" / "c1").exists()


def test_a_refusal_is_refused_with_the_failed_line(
    runner: Runner, job: tuple[Path, Json], monkeypatch: pytest.MonkeyPatch
) -> None:
    d, j = job
    monkeypatch.setenv("FAKE_REFUSE", "prep")
    rec = run(runner, d, j, "registration")
    assert (rec["state"], rec["exit_code"]) == ("refused", 2)
    assert rec["reason"] == "FAILED: the fake prep refuses this input"


def test_cancel_signals_the_group_and_removes_the_part(
    settings: Settings, runner: Runner, registered: tuple[Path, Json], monkeypatch: pytest.MonkeyPatch
) -> None:
    d, j = registered
    monkeypatch.setenv("FAKE_SLOW", "render=30")
    rec = runner.start_stage(d, j, stage_def("loop", "render"), RENDER)
    wait_for(lambda: progress_of(d / "stages" / rec["id"]), timeout=10)
    part = settings.root / rec["out_part"]
    assert part.is_dir()
    t0 = time.time()
    out = runner.cancel(d, rec["id"])
    assert time.time() - t0 < 5
    assert (out["state"], out["reason"]) == ("cancelled", "cancelled by you")
    # the note depends on which of cancel and the wait thread removes the .part first (the research script's race,
    # kept): the folder is gone either way
    assert out.get("note") in (None, "the .part folder was removed")
    assert not part.exists()
    assert not runner.pid_alive(rec["pid"])
    assert read_json(d / "stages" / rec["id"] / "stage.json")["state"] == "cancelled"
    with pytest.raises(StudioError, match="is cancelled, not running") as e:
        runner.cancel(d, rec["id"])
    assert e.value.code == 409


def test_cancel_never_signals_a_stranger_reusing_the_pid(
    settings: Settings, runner: Runner, registered: tuple[Path, Json]
) -> None:
    d, _ = registered
    stranger = subprocess.Popen(["sleep", "30"], start_new_session=True)
    try:
        part = d / "tiny" / "s1.part"
        hand_record(
            d, "20261105-000000_render", "render", stranger.pid, part, d / "tiny" / "s1", "measure.json", settings
        )
        out = runner.cancel(d, "20261105-000000_render")
        assert out["state"] == "lost"
        assert stranger.poll() is None  # still running: no signal reached it
    finally:
        stranger.kill()
        stranger.wait()


def test_reconcile_after_a_restart_marks_a_dead_record_lost(
    settings: Settings, runner: Runner, registered: tuple[Path, Json]
) -> None:
    d, _ = registered
    part = d / "tiny" / "r1.part"
    part.mkdir(parents=True)
    (part / "loop.mp4").write_bytes(b"half")
    rec = hand_record(
        d, "20261105-000001_render", "render", dead_pid(), part, d / "tiny" / "r1", "measure.json", settings
    )
    out = Runner(settings, FLAGS).reconcile(d, rec)
    assert out["state"] == "lost"
    assert out["reason"].startswith("the server restarted while the stage ran")
    assert out["note"] == "the partial .part folder was removed"
    assert not part.exists()
    assert out["exit_code"] is None


def test_reconcile_after_a_restart_finishes_a_complete_part(settings: Settings, registered: tuple[Path, Json]) -> None:
    d, _ = registered
    part = d / "tiny" / "r2.part"
    part.mkdir(parents=True)
    (part / "loop.mp4").write_bytes(b"whole")
    write_json(part / "measure.json", {"md5_mp4": md5_file(part / "loop.mp4"), "frames": 9})
    rec = hand_record(
        d, "20261105-000002_render", "render", dead_pid(), part, d / "tiny" / "r2", "measure.json", settings
    )
    out = Runner(settings, FLAGS).reconcile(d, rec)
    assert out["state"] == "done"
    assert out["note"] == "finished after a restart: the exit code is unknown; the terminal file was present"
    assert (d / "tiny" / "r2" / "measure.json").exists() and not part.exists()
    assert (d / "stages" / rec["id"] / "done").exists()
    assert sorted(Path(o["path"]).name for o in out["outputs"]) == ["loop.mp4", "measure.json"]


def test_reconcile_reads_a_refusal_and_a_cancel_from_the_files(
    settings: Settings, registered: tuple[Path, Json]
) -> None:
    d, _ = registered
    r = Runner(settings, FLAGS)
    rec = hand_record(
        d,
        "20261105-000003_render",
        "render",
        dead_pid(),
        d / "tiny" / "r3.part",
        d / "tiny" / "r3",
        "measure.json",
        settings,
    )
    (d / "stages" / rec["id"] / "log.txt").write_text("PROGRESS 1 9 frames\nFAILED: no prep for this plan\n")
    assert r.reconcile(d, rec)["state"] == "refused"
    part = d / "tiny" / "r4.part"
    part.mkdir(parents=True)
    rec2 = hand_record(
        d,
        "20261105-000004_render",
        "render",
        dead_pid(),
        part,
        d / "tiny" / "r4",
        "measure.json",
        settings,
        state="cancelling",
    )
    out = r.reconcile(d, rec2)
    assert (out["state"], out["reason"]) == (
        "cancelled",
        "cancelled; the server restarted before the record was written",
    )
    assert not part.exists()


def test_reconcile_reattaches_a_live_child_and_finishes_it(settings: Settings, registered: tuple[Path, Json]) -> None:
    d, j = registered
    part = d / "tiny" / "live.part"
    rid = "20261105-000005_render"
    rec = hand_record(d, rid, "render", 0, part, d / "tiny" / "live", "measure.json", settings)
    with open(d / "stages" / rid / "log.txt", "ab") as logf:
        child = subprocess.Popen(
            [
                str(settings.python),
                "scripts/research/loop_seq.py",
                "render",
                "scripts/research/plans/loops/tiny_a1.json",
                "--out",
                rec["out_part"],
                "--set",
                f'in="{j["root"]}/in/tiny"',
                "--progress",
            ],
            cwd=str(settings.root),
            stdout=logf,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env={**os.environ, "FAKE_SLOW": "render=1.5"},
        )
    threading.Thread(target=child.wait, daemon=True).start()  # the dead server's child is reaped by launchd, not us
    rec["pid"] = child.pid
    write_json(d / "stages" / rid / "stage.json", rec)
    r = Runner(settings, FLAGS)
    assert r.reconcile(d, rec)["state"] == "running"
    assert rid in r.watching
    assert r.reconcile_all() == 1  # counted again, not re-attached twice
    out = wait_record(d, rid, timeout=20)
    assert out["state"] == "done"
    assert "finished after a restart" in out["note"]
    assert rid not in r.watching


def test_a_finished_render_is_never_overwritten(
    settings: Settings, runner: Runner, registered: tuple[Path, Json]
) -> None:
    d, j = registered
    assert run(runner, d, j, "render", RENDER)["state"] == "done"
    n = len(records(d))
    with pytest.raises(StudioError, match=r"/tiny/c1 exists: choose another name") as e:
        runner.start_stage(d, j, stage_def("loop", "render"), RENDER)
    assert e.value.code == 409
    assert len(records(d)) == n  # the refused run left no record folder
    assert (
        run(runner, d, j, "render", {**RENDER, "draft": 480})["state"] == "done"
    )  # a draft of the same name is elsewhere
    assert (d / "drafts" / "tiny" / "c1" / "measure.json").exists()


def test_a_registration_rerun_moves_the_prep_aside_and_says_unchanged(
    settings: Settings, runner: Runner, registered: tuple[Path, Json]
) -> None:
    d, j = registered
    first = records(d)[0]
    (d / "in" / "tiny" / "keys.jpg").write_bytes(b"the strip the pages link")
    again = run(runner, d, j, "registration", {"depth_maps": True})
    assert again["state"] == "done"
    prev = [p for p in (d / "in").iterdir() if p.name.startswith("tiny_prev_")]
    assert len(prev) == 1 and (prev[0] / "k0.png").exists()
    assert (d / "in" / "tiny" / "keys.jpg").read_bytes() == b"the strip the pages link"  # copied forward
    assert again["note"].startswith(f"the previous prep moved to {rel(prev[0], settings.root)}")
    assert again["unchanged_from"] == first["id"]  # k*.png and depth maps equal; prep.json's date differs


def test_the_registration_waits_while_another_record_runs(
    settings: Settings, runner: Runner, registered: tuple[Path, Json], monkeypatch: pytest.MonkeyPatch
) -> None:
    d, j = registered
    monkeypatch.setenv("FAKE_SLOW", "render=30")
    rec = runner.start_stage(d, j, stage_def("loop", "render"), RENDER)
    try:
        with pytest.raises(StudioError, match=f"the registration waits: {rec['id']} still read the prep") as e:
            runner.start_stage(d, j, stage_def("loop", "registration"), {})
        assert e.value.code == 409
    finally:
        runner.cancel(d, rec["id"])


def test_a_readers_rerun_replaces_its_folder_and_lists_the_depth_maps(
    settings: Settings, runner: Runner, job: tuple[Path, Json]
) -> None:
    d, j = job
    assert run(runner, d, j, "registration")["state"] == "done"  # no depth maps: readers writes them beside the prep
    first = run(runner, d, j, "readers")
    assert first["state"] == "done"
    assert (d / "in" / "tiny" / "depth_k0.npy").exists()
    notes = [o for o in first["outputs"] if o.get("note")]
    assert sorted(Path(o["path"]).name for o in notes) == ["depth_k0.npy", "depth_k1.npy"]
    (d / "in" / "tiny" / "readers" / "stale.txt").write_text("from the previous run")
    second = run(runner, d, j, "readers")
    assert second["state"] == "done"
    assert not (d / "in" / "tiny" / "readers" / "stale.txt").exists()
    assert second["unchanged_from"] == first["id"]


def test_readers_is_refused_when_the_script_lacks_the_command(
    settings: Settings, registered: tuple[Path, Json]
) -> None:
    d, j = registered
    with pytest.raises(StudioError, match="has no readers command yet") as e:
        Runner(settings, ScriptFlags()).start_stage(d, j, stage_def("loop", "readers"), {})
    assert e.value.code == 501


def test_a_page_opens_a_round_and_keeps_the_previous_page(
    settings: Settings, runner: Runner, registered: tuple[Path, Json]
) -> None:
    d, j = registered
    run(runner, d, j, "render", RENDER)
    p1 = run(runner, d, j, "page", {"title": "first"})
    assert p1["state"] == "done"
    r1 = wait_for(lambda: read_json(d / "rounds" / "1" / "round.json"))
    page = d / "index.html"
    assert r1["page_md5"] == md5_file(page) == (d / "page.md5").read_text().strip()
    assert (r1["candidates"], r1["record"], r1["grade"]) == (["c1"], p1["id"], None)
    assert (d / "rounds" / "1" / "index.html").read_bytes() == page.read_bytes()
    assert "<title>first</title>" in page.read_text()
    save_grade(d, {"round": 1, "text": "c1 is fine"})
    p2 = run(runner, d, j, "page", {})
    r2 = wait_for(lambda: read_json(d / "rounds" / "2" / "round.json"))
    assert (d / "stages" / p2["id"] / "previous_index.html").read_bytes() == (
        d / "rounds" / "1" / "index.html"
    ).read_bytes()
    assert p2["note"] == "the previous page is kept under its round and beside this record"
    assert "<title>tiny: round 2</title>" in page.read_text()  # the default title names the round
    assert r2["page_md5"] == md5_file(page)


def test_the_round_gate_holds_the_first_full_render_until_the_grade(
    settings: Settings, runner: Runner, registered: tuple[Path, Json]
) -> None:
    d, j = registered
    write_json(
        d / "rounds" / "1" / "round.json",
        {"n": 1, "page_md5": "p", "candidates": [], "grade": None, "ungraded_by_his_word": None},
    )
    with pytest.raises(StudioError, match="round 1 has no grade text") as e:
        runner.start_stage(d, j, stage_def("loop", "render"), RENDER)
    assert (e.value.code, e.value.extra) == (409, {"round": 1})
    assert run(runner, d, j, "render", {**RENDER, "draft": 480})["state"] == "done"  # a draft is never gated
    save_grade(d, {"round": 1, "ungraded_by_his_word": True, "words": "skip it"})
    assert run(runner, d, j, "render", RENDER)["state"] == "done"


def test_a_render_with_the_same_mp4_says_unchanged(
    settings: Settings, runner: Runner, registered: tuple[Path, Json]
) -> None:
    d, j = registered
    c1 = run(runner, d, j, "render", RENDER)
    c2 = run(runner, d, j, "render", {**RENDER, "name": "c2"})
    assert c2["unchanged_from"] == c1["id"]
    plan = {**FROZEN_PLAN, "timeline": [{"key": 0, "hold": 5}, {"to": 1, "n": 3, "method": "rife"}]}
    save_plan(settings, d, j, "longer", plan, "frozen:tiny_a1")
    c3 = run(runner, d, j, "render", {"plan": "job:longer", "name": "c3"})
    assert c3["state"] == "done" and "unchanged_from" not in c3


@pytest.mark.parametrize(
    ("stage", "knobs", "code", "text"),
    [
        ("render", {"plan": "frozen:tiny_a1", "zoom": 2}, 400, "the render stage has no knob 'zoom'"),
        ("render", {"plan": "frozen:tiny_a1", "draft": "big"}, 400, "knob draft takes a int, not 'big'"),
        ("render", {"plan": "frozen:tiny_a1", "name": "a b"}, 400, "a render name is letters"),
        ("render", {"plan": "nothing"}, 400, "the plan is job:<name>"),
        ("plan", {}, 400, "the plan stage is not a process"),
    ],
)
def test_bad_knobs_are_refused_before_a_record_exists(
    runner: Runner, registered: tuple[Path, Json], stage: str, knobs: Json, code: int, text: str
) -> None:
    d, j = registered
    n = len(records(d))
    with pytest.raises(StudioError) as e:
        runner.start_stage(d, j, stage_def("loop", stage), knobs)
    assert (e.value.code, text in str(e.value)) == (code, True), str(e.value)
    assert len(records(d)) == n
    assert sorted(p.name for p in (d / "stages").iterdir()) == [r["id"] for r in records(d)]


def test_render_and_readers_need_a_prep_and_an_adopted_job_cannot_register(
    settings: Settings, runner: Runner, job: tuple[Path, Json]
) -> None:
    d, j = job
    for stage, knobs in (("render", RENDER), ("readers", {})):
        with pytest.raises(StudioError, match=r"registration first: no prep\.json") as e:
            runner.start_stage(d, j, stage_def("loop", stage), knobs)
        assert e.value.code == 409
    run_dir = settings.runs / "2026-11-04" / "old"
    write_json(run_dir / "in" / "older" / "prep.json", {"sources": []})
    # another sequence's name: two jobs of one sequence made in the same second share an id (kept from the script)
    adopted = create_job(settings, "loop", adopt="benchmarks/runs/2026-11-04/old", seq="older")
    ad = settings.runs / "2026-11-05" / "studio" / adopted["id"]
    with pytest.raises(StudioError, match="no raw stills to register") as e2:
        runner.start_stage(ad, adopted, stage_def("loop", "registration"), {})
    assert e2.value.code == 409


def test_coerce_types_bools_from_strings(
    runner: Runner, job: tuple[Path, Json], monkeypatch: pytest.MonkeyPatch
) -> None:
    d, j = job
    rec = run(
        runner, d, j, "registration", {"depth_maps": "yes", "ecc_refine": "0", "min_inliers": "33", "bg_depth": "0.2"}
    )
    assert rec["knobs"]["depth_maps"] is True and rec["knobs"]["ecc_refine"] is False
    assert (rec["knobs"]["min_inliers"], rec["knobs"]["bg_depth"]) == (33, 0.2)
    assert "--ecc-refine" not in rec["argv"] and "--depth-maps" in rec["argv"]


def test_the_probe_reads_the_scripts_help(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    assert probe_script_flags(settings) == ScriptFlags(progress=True, frames=True, readers=True)
    monkeypatch.setenv("FAKE_NO_FLAGS", "1")
    assert probe_script_flags(settings) == ScriptFlags()
    monkeypatch.delenv("FAKE_NO_FLAGS")
    gone = Settings(**{**settings.__dict__, "python": settings.root / "no" / "python"})
    assert probe_script_flags(gone) == ScriptFlags()


def test_the_lock_admits_one_server_and_a_knowing_second(settings: Settings) -> None:
    fh = take_lock(settings, second=False)
    text = settings.lock_path.read_text()
    assert text.startswith(f"port {settings.port} pid {os.getpid()} since ")
    with pytest.raises(
        LockHeld, match=r"another studio holds .*\(port \d+ pid \d+ since .*\); stop it, or pass --second"
    ):
        take_lock(settings, second=False)
    fh2 = take_lock(settings, second=True)
    assert settings.lock_path.read_text() == text  # the second server keeps the first one's text
    fh2.close()
    fh.close()  # closing the handle drops the flock, as `serve` does at its end
    fh3 = take_lock(settings, second=False)
    fh3.close()


def test_two_starts_in_one_second_get_distinct_record_ids(runner: Runner, registered: tuple[Path, Json]) -> None:
    d, j = registered
    a = runner.start_stage(d, j, stage_def("loop", "render"), {**RENDER, "name": "x1", "draft": 480})
    b = runner.start_stage(d, j, stage_def("loop", "render"), {**RENDER, "name": "x2", "draft": 480})
    assert a["id"] != b["id"]
    for r in (a, b):
        assert wait_record(d, r["id"])["state"] == "done"


# ---------------------------------------------------------------- phase B's slice: any flow's script, the verdict

SET = K("set", "object", {}, "knob=value (JSON value); 'name.param' targets a transform's params", "--set")
OBJECT_STAGE: Json = {"name": "render", "knobs": [SET]}


def test_an_object_knob_becomes_one_set_flag_per_key_in_sorted_order() -> None:
    """The director's --set table rides one knob of type object. Mutation: the keys in the order the page sent them
    (two equal dicts then give two argv), or a value written with str() instead of JSON ("True", "[0.35, 0.97]" as a
    Python repr), turns this red."""
    knobs = coerce(
        OBJECT_STAGE, {"set": {"parallax_push": 2, "pane_becomes_view.window": [0.35, 0.97], "plate": False}}
    )
    assert flags_of(OBJECT_STAGE, knobs) == [
        "--set",
        "pane_becomes_view.window=[0.35, 0.97]",
        "--set",
        "parallax_push=2",
        "--set",
        "plate=false",
    ]
    assert coerce(OBJECT_STAGE, {"set": '{"sky.shape": "radial"}'})["set"] == {"sky.shape": "radial"}  # JSON text
    assert flags_of(OBJECT_STAGE, coerce(OBJECT_STAGE, {})) == []  # the empty default passes no flag
    a, b = coerce(OBJECT_STAGE, {}), coerce(OBJECT_STAGE, {})
    a["set"]["x"] = 1
    assert b["set"] == {} and SET["default"] == {}  # the default is copied, never shared between runs


@pytest.mark.parametrize("bad", [{"a.b.c": 1}, {"has space": 1}, [1, 2], "not json", '"text"', {"": 1}])
def test_an_object_knob_refuses_a_key_with_two_dots_or_a_non_object(bad: object) -> None:
    """director_render.py routes a --set key on its first dot; a second dot lands on a key nothing reads. Mutation:
    dropping the key check turns the first row red."""
    with pytest.raises(StudioError, match="knob set takes a object") as e:
        coerce(OBJECT_STAGE, {"set": bad})
    assert e.value.code == 400


def pair_job(settings: Settings, fixture_pair: str) -> tuple[Path, Json]:
    j = create_pair_job(settings, fixture=fixture_pair)
    return settings.root / j["root"], j


def test_the_verdict_runs_reveal_align_on_a_pair_job(settings: Settings, runner: Runner, fixture_pair: str) -> None:
    """The shared branch through the Runner on a pair job, its stage passed directly (the pair's stage list is empty
    in the slice; its argv is pinned in tests/test_pair_flow.py). Mutation: the record stamping loop_seq.py's md5, the
    verdict folder put under the run folder's renders, or the identity looked up in the loop's table (no "unchanged"
    on the rerun), turns this red."""
    d, j = pair_job(settings, fixture_pair)
    rec = wait_record(d, runner.start_stage(d, j, VERDICT_STAGE, {})["id"])
    assert (rec["state"], rec["exit_code"], rec["stage"], rec["argv"][1]) == ("done", 0, "verdict", "reveal.py")
    root = j["root"]
    assert rec["script_md5"] == md5_file(settings.reveal) != md5_file(settings.loop_seq)
    assert rec["inputs"] == [{"path": i["path"], "sha256": i["sha256"]} for i in j["inputs"]]
    assert (rec["out_final"], rec["terminal"]) == (f"{root}/verdict", "metrics.json")
    assert "metrics.json" in [Path(o["path"]).name for o in rec["outputs"]]
    assert (d / "verdict" / "metrics.json").is_file() and not (d / "verdict.part").exists()
    assert (d / "stages" / rec["id"] / "done").exists()
    again = wait_record(d, runner.start_stage(d, j, VERDICT_STAGE, {})["id"])
    # the identity pattern metrics.json comes from the shared stage: the rerun replaced the folder and says so
    assert again["unchanged_from"] == rec["id"] and (d / "verdict" / "metrics.json").is_file()


def test_a_verdict_refusal_is_refused_with_reveals_failed_line(
    settings: Settings, runner: Runner, fixture_pair: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exit 2 with a FAILED: line is a refusal: the photos share too little detail. Mutation: reading exit 2 as a
    failure turns this red."""
    d, j = pair_job(settings, fixture_pair)
    monkeypatch.setenv("FAKE_REFUSE", "align")
    rec = wait_record(d, runner.start_stage(d, j, VERDICT_STAGE, {})["id"])
    assert (rec["state"], rec["exit_code"], rec["reason"]) == (
        "refused",
        2,
        "FAILED: the photos share too little detail",
    )
    assert not (d / "verdict").exists()
    monkeypatch.setenv("FAKE_REFUSE", "")
    monkeypatch.setenv("FAKE_FAIL", "align")
    rec2 = wait_record(d, runner.start_stage(d, j, VERDICT_STAGE, {})["id"])
    assert rec2["state"] == "failed" and rec2["exit_code"] == 1


def test_a_stage_whose_script_is_missing_is_refused_before_it_starts(
    settings: Settings, runner: Runner, job: tuple[Path, Json]
) -> None:
    """The record stamps the md5 of the script its own argv names. Mutation: hashing the script after the child
    started (a 500 and an orphan record folder) turns this red."""
    d, j = job
    settings.loop_seq.unlink()
    with pytest.raises(StudioError, match=r"^scripts/research/loop_seq\.py is missing: the registration stage") as e:
        runner.start_stage(d, j, stage_def("loop", "registration"), {})
    assert e.value.code == 409 and list((d / "stages").glob("*")) == []


TOOL = """import pathlib, sys, time
out = pathlib.Path(sys.argv[sys.argv.index("--out") + 1])
time.sleep(1.5)
out.mkdir(parents=True, exist_ok=True)
(out / "result.json").write_text("{}")
"""
"""A script of no flow (the record's argv[1] is tool.py): it sleeps, then writes its terminal file."""


def test_reconcile_reattaches_a_live_child_of_another_flows_script(
    settings: Settings, runner: Runner, fixture_pair: str
) -> None:
    """After a restart a live child of any script, not only loop_seq.py, is watched; before the slice it was marked
    lost and its .part folder removed while it still wrote (b_seams_research.md, key fact 2). Mutation: pid_alive
    looking for the loop script in the process's arguments marks this record lost and turns this red."""
    d, _j = pair_job(settings, fixture_pair)
    (settings.root / "tool.py").write_text(TOOL)
    rid = "20261105-000006_verdict"
    part = d / "tool.part"
    rec = hand_record(d, rid, "verdict", 0, part, d / "tool", "result.json", settings)
    rec["argv"] = [str(settings.python), "tool.py", "--out", rec["out_part"]]
    with open(d / "stages" / rid / "log.txt", "ab") as logf:
        child = subprocess.Popen(
            rec["argv"], cwd=str(settings.root), stdout=logf, stderr=subprocess.STDOUT, start_new_session=True
        )
    threading.Thread(target=child.wait, daemon=True).start()
    rec["pid"] = child.pid
    write_json(d / "stages" / rid / "stage.json", rec)
    r = Runner(settings, FLAGS)
    assert r.reconcile(d, rec)["state"] == "running" and rid in r.watching
    out = wait_record(d, rid, timeout=20)
    assert out["state"] == "done" and "finished after a restart" in out["note"]
    assert (d / "tool" / "result.json").is_file() and not part.exists()


def test_a_non_loop_flows_render_names_no_loop_plan_for_the_rulings(settings: Settings, fixture_pair: str) -> None:
    """Mutation: run_warnings resolving every render's plan in the loop's folder (a director plan then 404s before
    its script starts) turns this red."""
    j = create_director_job(settings, fixture_pair)
    d = settings.root / "benchmarks/runs/2026-11-05/studio" / j["id"]
    assert run_warnings(settings, d, "render", {"plan": "frozen:tiny_1_r1"}, "director") == []
    with pytest.raises(StudioError, match=r"no plan scripts/research/plans/loops/tiny_1_r1\.json"):
        run_warnings(settings, d, "render", {"plan": "frozen:tiny_1_r1"}, "loop")


def test_argv_for_routes_a_shared_stage_before_the_flow_module() -> None:
    """Mutation: the dispatcher asking the flow module first (the pair module then answers for the verdict) or a flow
    sent to another flow's module turns this red."""
    assert builder_of("pair", "verdict") is argv_common.ARGV["verdict"] is builder_of("director", "verdict")
    assert builder_of("loop", "render") is argv_loop.argv_for
    assert builder_of("pair", "render") is argv_pair.argv_for
    assert builder_of("director", "render") is argv_director.argv_for
    with pytest.raises(StudioError, match="no argv for the align flow") as e:
        builder_of("align", "render")
    assert e.value.code == 501


def test_a_stage_written_in_place_keeps_the_previous_file_beside_the_record(
    settings: Settings, job: tuple[Path, Json], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A script that writes its output in place (director_page.py writes run/index.html): the runner copies the
    existing file to <record>/previous_<name> before the run, removes and renames nothing, and the record says so.
    Red if start_stage removes an out_part that is the out_final, or if finalize copies the NEW file as the previous
    one (the copy must happen before the child runs)."""
    import reveal_studio.runner.process as process_mod

    d, j = job
    script = settings.root / "scripts/research/inplace.py"
    script.write_text("import sys, pathlib\npathlib.Path(sys.argv[1]).write_text('new page ' + sys.argv[2])\n")
    page = settings.root / j["root"] / "index.html"
    page.write_text("old page")

    def fake_argv(
        settings_: Settings, flags: ScriptFlags, stage: Json, d_: Path, job_: Json, knobs: Json, rec_dir: Path
    ):  # type: ignore[no-untyped-def]  # 2026-11-05: a test double of argv_for
        return (
            [str(settings_.python), "scripts/research/inplace.py", rel(page, settings_.root), rec_dir.name],
            page,
            page,
            [],
        )

    monkeypatch.setattr(process_mod, "argv_for", fake_argv)
    stage = {
        "name": "page",
        "title": "page",
        "kind": "script",
        "optional": False,
        "terminal": "index.html",
        "knobs": [],
        "what": "x",
    }
    runner = Runner(settings, FLAGS)
    rec = runner.start_stage(d, j, stage, {})
    rec = wait_record(d, rec["id"])
    assert rec["state"] == "done", rec
    assert rec["in_place"] is True and rec["previous"] == "previous_index.html"
    assert (d / "stages" / rec["id"] / "previous_index.html").read_text() == "old page"
    assert page.read_text() == "new page " + rec["id"]
    assert [o["path"] for o in rec["outputs"]] == [rel(page, settings.root)]
    # a second run keeps the first run's page as its previous copy
    rec2 = wait_record(d, runner.start_stage(d, j, stage, {})["id"])
    assert (d / "stages" / rec2["id"] / "previous_index.html").read_text() == "new page " + rec["id"]
    # after a restart an in-place record cannot tell whether the run finished: it is lost, and the file stays
    rec3 = runner.start_stage(d, j, stage, {})
    wait_record(d, rec3["id"])
    r = read_json(d / "stages" / rec3["id"] / "stage.json")
    r["state"] = "running"
    r["pid"] = dead_pid()
    write_json(d / "stages" / rec3["id"] / "stage.json", r)
    out = Runner(settings, FLAGS).reconcile(d, r)
    assert out["state"] == "lost" and page.exists()
