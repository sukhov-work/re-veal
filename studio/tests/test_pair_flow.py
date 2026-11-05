"""The pair transition flow (builder P's file from wave 2 on). The slice of 2026-11-05 left the flow registered,
disabled and empty; these tests pin that state, and builder P replaces them with the flow's own."""

from __future__ import annotations

from pathlib import Path

import pytest

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.jobs.store import create_pair_job
from reveal_studio.registry import pair
from reveal_studio.registry.common import VERDICT_STAGE
from reveal_studio.registry.flows import ALL_FLOWS, FLOWS
from reveal_studio.registry.hints_pair import HINTS as PAIR_HINTS
from reveal_studio.runner.process import Runner

from .conftest import wait_record


def test_the_pair_flow_is_registered_disabled_and_empty() -> None:
    """Mutation: enabling the flow before it has stages (the page then offers a job no stage runs) turns this red."""
    assert ALL_FLOWS["pair"] is pair.FLOW and "pair" not in FLOWS
    assert (pair.FLOW["enabled"], pair.FLOW["stages"], PAIR_HINTS) == (False, [], {})
    assert pair.FLOW["candidates"] == {
        "full": ["{root}/{seq}"],
        "draft": ["{root}/drafts/{seq}"],
        "terminal": "report.json",
        "mp4": "transition.mp4",
        "record_knobs": ["preset"],
        "fields": ["class", "method", "sparse_inliers", "median_disp_px", "mean_certainty", "n_frames", "quality"],
    }


def test_the_pair_flows_modules_are_empty_stubs() -> None:
    """The slice's stubs for builder P: no route, no tile function, no extra key on the job view. Mutation: a row in
    the flow's route list before the flow is built turns this red (the route walk of test_server.py then misses it)."""
    from reveal_studio.server import routes_pair
    from reveal_studio.views import pair as pair_views

    assert (routes_pair.ROUTES, pair_views.TILES, pair_views.DEFAULT_FPS) == ([], {}, 30)


def test_a_pair_stage_answers_501_before_a_record_exists(settings: Settings, runner: Runner, fixture_pair: str) -> None:
    """runner/argv_pair.py is a stub in the slice. Mutation: the dispatcher sending a pair stage to the loop's chain
    (a pair "render" then runs loop_seq.py) turns this red."""
    j = create_pair_job(settings, fixture=fixture_pair)
    d = settings.root / j["root"]
    stage = {"name": "render", "kind": "script", "terminal": "report.json", "knobs": []}
    with pytest.raises(StudioError, match="the pair flow's render stage is not built yet") as e:
        runner.start_stage(d, j, stage, {})
    assert e.value.code == 501 and not list((d / "stages").glob("*"))


def test_the_verdicts_argv_as_the_slice_left_it(settings: Settings, runner: Runner, fixture_pair: str) -> None:
    """Reveal's verdict (registry/common.py, runner/argv_common.py, builder P's from wave 2 on): reveal.py align on
    the job's two links, into <job>/verdict.part. Mutation: the argv naming the originals instead of the job's links
    turns this red."""
    j = create_pair_job(settings, fixture=fixture_pair)
    d = settings.root / j["root"]
    rec = wait_record(d, runner.start_stage(d, j, VERDICT_STAGE, {})["id"])
    root = j["root"]
    assert rec["argv"] == [
        str(settings.python),
        "reveal.py",
        "align",
        f"{root}/raw/tiny_1/A.jpg",
        f"{root}/raw/tiny_1/B.jpg",
        "--out",
        f"{root}/verdict.part",
    ]
    names = sorted(Path(o["path"]).name for o in rec["outputs"])
    assert names == ["after_aligned.jpg", "before.jpg", "metrics.json"]  # the fake reveal.py's three files
