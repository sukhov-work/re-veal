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
from reveal_studio.jobs.plans import save_plan
from reveal_studio.jobs.records import progress_of, records
from reveal_studio.jobs.store import create_job, job_root
from reveal_studio.registry.loop import stage_def
from reveal_studio.runner.argv import ScriptFlags, probe_script_flags
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
