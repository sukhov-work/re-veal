"""views/measures.py: stalls and jumps on the step series (the bars of loops.md §6), the frame kinds they read, a
render's measure runs and the latest stability series, and the probe's table read from probe.json."""

from __future__ import annotations

from pathlib import Path

import pytest

from reveal_studio.config import Settings
from reveal_studio.fs import Json, rel, write_json
from reveal_studio.runner.process import Runner
from reveal_studio.views.measures import (
    JUMP_RATIO,
    STALL_BAR,
    frame_kinds,
    latest_stability,
    measure_runs,
    probe_view,
    stalls_and_jumps,
)

from .conftest import run

OPEN = ["generated"] * 8


def test_the_bars_are_the_playbooks() -> None:
    # loops.md §6: "no run of steps below 0.3 while motion is open", "no step above 3× its neighbours".
    # Mutation: either constant changed turns this red, and the series tests below pin the comparison.
    assert (STALL_BAR, JUMP_RATIO) == (0.3, 3.0)


def test_two_open_steps_below_the_bar_are_a_stall() -> None:
    # 0.29 sits under 0.3. Mutation: STALL_BAR 0.3 -> 0.25 drops the run and turns this red.
    assert stalls_and_jumps([1.0, 0.29, 0.29, 1.0, 1.0], OPEN)["stalls"] == [[1, 2]]


def test_steps_just_over_the_bar_are_no_stall() -> None:
    # 0.31 sits over 0.3. Mutation: STALL_BAR 0.3 -> 0.35 makes a run of them and turns this red.
    assert stalls_and_jumps([1.0, 0.31, 0.31, 1.0, 1.0], OPEN)["stalls"] == []


def test_one_step_below_the_bar_is_no_stall_and_a_run_ends_at_the_series_end() -> None:
    # A stall is a run of two or more. Mutation: `run[1] > run[0]` -> `>=` lists [1, 1] and turns this red.
    assert stalls_and_jumps([1.0, 0.1, 1.0, 1.0, 1.0], OPEN)["stalls"] == []
    # A run still open at the last step is kept. Mutation: dropping the after-loop append turns this red.
    assert stalls_and_jumps([1.0, 1.0, 1.0, 0.1, 0.1], OPEN)["stalls"] == [[3, 4]]


def test_a_hold_or_a_cut_closes_motion() -> None:
    # Steps 1 and 2 touch hold frames: a still is meant to stand. Mutation: dropping the CLOSED test turns this red.
    tags = ["generated", "hold", "hold", "hold", "generated", "generated"]
    assert stalls_and_jumps([1.0, 0.0, 0.0, 1.0, 1.0], tags)["stalls"] == []
    # The same values between in-betweens are a stall, so the test above is the hold, not the values.
    assert stalls_and_jumps([1.0, 0.0, 0.0, 1.0, 1.0], OPEN)["stalls"] == [[1, 2]]
    cut = ["generated", "generated", "cut", "generated", "generated", "generated"]
    assert stalls_and_jumps([1.0, 0.0, 0.0, 1.0, 1.0], cut)["stalls"] == []


def test_a_step_above_three_times_its_neighbours_is_a_jump() -> None:
    # 3.1 > 3 × mean(1.0, 1.0). Mutation: JUMP_RATIO 3 -> 3.5 drops it and turns this red.
    assert stalls_and_jumps([1.0, 1.0, 3.1, 1.0, 1.0], OPEN)["jumps"] == [2]


def test_a_step_under_three_times_its_neighbours_is_no_jump() -> None:
    # 2.9 < 3 × 1.0. Mutation: JUMP_RATIO 3 -> 2.5 lists it and turns this red.
    assert stalls_and_jumps([1.0, 1.0, 2.9, 1.0, 1.0], OPEN)["jumps"] == []


def test_the_reference_is_the_mean_of_the_two_neighbours() -> None:
    # Neighbours 0.5 and 1.5: their mean 1.0 makes 3.1 a jump, their max 1.5 would not.
    # Mutation: the mean replaced by the max (A1's inspector heuristic) turns this red.
    assert stalls_and_jumps([1.0, 0.5, 3.1, 1.5, 1.0], OPEN)["jumps"] == [2]


def test_the_first_and_the_last_step_are_judged_against_their_one_neighbour() -> None:
    # Mutation: skipping the ends (requiring two neighbours) turns this red.
    assert stalls_and_jumps([3.1, 1.0, 1.0, 1.0, 3.1], OPEN)["jumps"] == [0, 4]
    assert stalls_and_jumps([5.0], OPEN) == {"stalls": [], "jumps": []}  # no neighbour: no verdict
    assert stalls_and_jumps([], []) == {"stalls": [], "jumps": []}


def test_a_step_under_the_stall_bar_is_never_a_jump() -> None:
    # Step 0 of the Halloween renders of 2026-10-30 (evgen-thug/c1 and 109 others listed it): 0.01 against 0.0 inside
    # a hold, the encoder's noise. Mutation: dropping the STALL_BAR floor lists step 0 and turns this red.
    assert stalls_and_jumps([0.01, 0.0, 0.0, 0.0], ["hold"] * 5)["jumps"] == []
    # The floor is the stall bar itself: 0.3 over neighbours of 0.05 is a jump. Mutation: `>=` -> `>` drops it.
    assert stalls_and_jumps([0.05, 0.3, 0.05, 0.05], OPEN)["jumps"] == [1]


def test_a_declared_cut_or_snap_is_no_jump() -> None:
    # The step into a cut's first frame. Mutation: dropping the cut test lists step 1 and turns this red.
    tags = ["hold", "hold", "cut", "hold", "hold"]
    assert stalls_and_jumps([0.1, 9.0, 0.1, 0.1], tags)["jumps"] == []
    # The same series without the cut is a jump, so the test above is the cut, not the values.
    assert stalls_and_jumps([0.1, 9.0, 0.1, 0.1], ["hold"] * 5)["jumps"] == [1]
    # A step with a snap frame at either end. Mutation: dropping the snap test turns this red.
    snap = ["generated", "generated", "snap", "generated", "generated", "generated"]
    assert stalls_and_jumps([1.0, 9.0, 9.0, 1.0, 1.0], snap)["jumps"] == []
    assert stalls_and_jumps([1.0, 9.0, 1.0, 1.0, 1.0], OPEN)["jumps"] == [1]


def test_frame_kinds_reads_the_words_of_frames_json_and_finds_a_cut() -> None:
    rows: list[Json] = [
        {"step": 0, "key": 0, "generated": "none (photo)"},
        {"t": 0.5, "generated": "rife", "step": 1, "from": 0, "to": 1, "method": "rife"},
        {"step": 2, "key": 1, "generated": "none (photo)"},
        {"step": 4, "key": 0, "generated": "none (photo)"},  # step 3 cut to k0: it wrote no frame
        {"t": 0.5, "generated": "none (blend + motion blur)", "step": 5, "from": 0, "to": 1, "method": "snap"},
        {"t": 0.5, "generated": "none (blend)", "step": 6, "from": 1, "to": 0, "method": "dissolve"},
        {"t": 0.5, "generated": "rife (the base)", "step": 7, "from": 0, "to": 1, "method": "slide"},
        {"t": 0.5, "generated": "none (morph)", "step": 9, "from": 1, "to": 0, "method": "morph"},  # step 8: hold 0
        {"generated": "none (rewind)", "step": 10, "from": 0, "to": 0, "method": "rewind"},
    ]
    # Mutation: the cut rule comparing keys within one step, or `!=` -> `==`, turns this red.
    assert frame_kinds(rows) == ["hold", "generated", "hold", "cut", "snap", "blend", "generated", "morph", "rewind"]
    # A hold of zero frames between two legs is no cut: the first leg ends on the still the next starts from.
    legs: list[Json] = [
        {"generated": "rife", "step": 1, "from": 0, "to": 1},
        {"generated": "rife", "step": 3, "from": 1, "to": 0},
    ]
    assert frame_kinds(legs) == ["generated", "generated"]


def test_the_angel_draft_steps_have_neither_a_stall_nor_a_jump() -> None:
    # The 480 px draft port_check_20261105-010146 of angel_a2 (measure.json, 2026-11-05): 49 steps, 24 RIFE frames.
    steps = [0.48, 0.54, 0.54, 0.59, 0.74, 0.73, 0.72, 0.76, 0.87, 0.85, 0.88, 0.89, 0.93, 0.95, 1.05, 2.26, 2.73]
    steps += [2.3, 3.43, 3.05, 3.27, 2.18, 3.02, 1.89, 0.71, 0.64, 0.65, 0.64, 0.8, 0.74, 0.76, 0.81, 0.88, 0.89]
    steps += [0.87, 0.88, 0.92, 0.97, 1.05, 2.27, 2.72, 2.45, 3.06, 3.57, 3.1, 2.24, 2.6, 2.09, 0.42]
    tags = ["hold"] * 14 + ["generated"] * 12 + ["hold"] * 12 + ["generated"] * 12
    assert len(steps) == 49 and len(tags) == 50
    assert stalls_and_jumps(steps, tags) == {"stalls": [], "jumps": []}


def _measure(stability: bool) -> Json:
    m: Json = {"frames": 3, "steps": [1.0, 1.0], "md5_mp4": "x"}
    if stability:
        m |= {
            "stability_ref": 0,
            "stability_margin": 30,
            "stability": {"ring_top": [[0.0, 0.0, 1.0], [0.5, -2.0, 0.99], [0.1, -0.5, 0.995]]},
            "stability_max": {
                "ring_top": {
                    "box": [1, 2, 30, 20],
                    "dx_max": 0.5,
                    "dx_max_at": 1,
                    "dy_max": 2.0,
                    "dy_max_at": 1,
                    "corr_min": 0.99,
                    "edge_frames": [],
                }
            },
        }
    return m


def test_measure_runs_lists_the_folders_skips_part_and_names_the_record(settings: Settings, tmp_path: Path) -> None:
    d = settings.runs / "2026-11-05" / "studio" / "j"
    render = d / "tiny" / "c1"
    base = render / "measures"
    write_json(base / "20261105-010101" / "measure.json", _measure(True))
    write_json(base / "20261105-010102.part" / "measure.json", _measure(True))  # still running
    write_json(base / "shell" / "measure.json", _measure(False))  # a run made from the shell, no record
    (base / "empty").mkdir()
    write_json(
        d / "stages" / "20261105-010101_measure" / "stage.json",
        {
            "id": "20261105-010101_measure",
            "stage": "measure",
            "state": "done",
            "started": "2026-11-05T01:01:01",
            "ended": "2026-11-05T01:01:03",
            "out_final": rel(base / "20261105-010101", settings.root),
        },
    )
    runs = measure_runs(settings, d, {"dir": render})
    # Mutation: dropping the `.part` skip lists three runs; matching records by id instead of path loses the record.
    assert [Path(r["folder"]).name for r in runs] == ["20261105-010101", "shell"]
    assert [r["record"] for r in runs] == ["20261105-010101_measure", None]
    assert runs[0]["at"] == "2026-11-05T01:01:03" and runs[0]["windows"] == {"ring_top": [1, 2, 30, 20]}
    assert runs[1]["stability_max"] == {} and runs[1]["windows"] == {}
    # The latest run without windows does not hide the series: the latest run that measured windows is drawn.
    # Mutation: taking runs[-1] blindly returns None and turns this red.
    st = latest_stability(runs)
    assert st is not None and st["record"] == "20261105-010101_measure" and st["ref"] == 0 and st["margin"] == 30
    assert st["series"]["ring_top"][1] == [0.5, -2.0, 0.99] and st["max"]["ring_top"]["dy_max_at"] == 1
    assert measure_runs(settings, d, {"dir": d / "tiny" / "none"}) == [] and latest_stability([]) is None


def test_probe_view_reads_the_fakes_probe_in_the_real_shape(runner: Runner, registered: tuple[Path, Json]) -> None:
    d, j = registered
    assert probe_view(runner.settings, j) is None  # before a probe ran
    rec = run(runner, d, j, "probe", {"long": 480})
    assert rec["state"] == "done", rec
    pv = probe_view(runner.settings, j)
    assert pv is not None and pv["long"] == 480 and pv["rife_skipped"] is None
    (pair,) = pv["pairs"]
    assert (pair["a"], pair["b"], pair["faces"]) == (0, 1, 1)
    # Mutation: dict order instead of PROBE_METHODS puts the methods in the file's order; the panel's columns move.
    assert [m["method"] for m in pair["methods"]] == ["rife", "morph", "dissolve"]
    rife = pair["methods"][0]
    assert [f["dexp"] for f in rife["frames"]] == [0.0413, 0.0611, 0.0341]  # the angel's locked probe, the fake's
    assert rife["strip"] == f"/api/jobs/{j['id']}/file/in/tiny/probe/probe_0_1_rife.jpg"
    assert pair["methods"][1]["flow"] == "homography+dis" and "seconds" in rife["frames"][0]
    row = pair["crops"][0]
    assert (row["face"], row["method"]) == (0, "rife")
    assert row["a"].endswith("/probe/crops/0_1_k0_face0.jpg") and row["b"].endswith("/probe/crops/0_1_k1_face0.jpg")
    assert [u.rsplit("/", 1)[1] for u in row["mid"]] == [f"0_1_rife_t{t}_face0.jpg" for t in (0.25, 0.5, 0.75)]


def test_probe_view_says_why_rife_was_skipped(
    runner: Runner, registered: tuple[Path, Json], monkeypatch: pytest.MonkeyPatch
) -> None:
    d, j = registered
    monkeypatch.setenv("FAKE_NO_RIFE", "1")
    assert run(runner, d, j, "probe", {})["state"] == "done"
    pv = probe_view(runner.settings, j)
    assert pv is not None and pv["rife_skipped"].startswith("no RIFE_MANIFEST.json")
    assert [m["method"] for m in pv["pairs"][0]["methods"]] == ["morph", "dissolve"]
