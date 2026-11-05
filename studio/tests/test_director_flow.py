"""The director plan flow (builder D's file from wave 2 on). The slice of 2026-11-05 left the flow registered,
disabled and empty; these tests pin that state, and builder D replaces them with the flow's own."""

from __future__ import annotations

import pytest

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.jobs.store import create_director_job
from reveal_studio.registry import director
from reveal_studio.registry.flows import ALL_FLOWS, FLOWS
from reveal_studio.registry.hints_director import HINTS as DIRECTOR_HINTS
from reveal_studio.runner.process import Runner


def test_the_director_flow_is_registered_disabled_and_empty() -> None:
    """Mutation: the drafts folder put under run/ (director_page.py then lists them beside the full renders) or the
    flow enabled before it has stages turns this red."""
    assert ALL_FLOWS["director"] is director.FLOW and "director" not in FLOWS
    assert (director.FLOW["enabled"], director.FLOW["stages"], DIRECTOR_HINTS) == (False, [], {})
    spec = director.FLOW["candidates"]
    assert (spec["full"], spec["draft"], spec["terminal"], spec["mp4"]) == (
        ["{root}"],
        ["{job}/drafts"],
        "info.json",
        "transition.mp4",
    )


def test_the_director_flows_modules_are_empty_stubs() -> None:
    """The slice's stubs for builder D: no route, no tile function, no extra key on the job view. Mutation: a row in
    the flow's route list before the flow is built turns this red (the route walk of test_server.py then misses it)."""
    from reveal_studio.server import routes_director
    from reveal_studio.views import director as director_views

    assert (routes_director.ROUTES, director_views.TILES, director_views.DEFAULT_FPS) == ([], {}, 30)


def test_a_director_stage_answers_501_before_a_record_exists(
    settings: Settings, runner: Runner, fixture_pair: str
) -> None:
    """runner/argv_director.py is a stub in the slice. Mutation: the dispatcher sending a director stage to the
    loop's chain turns this red."""
    j = create_director_job(settings, fixture_pair)
    d = settings.runs / "2026-11-05" / "studio" / j["id"]
    stage = {"name": "render", "kind": "script", "terminal": "info.json", "knobs": []}
    with pytest.raises(StudioError, match="the director flow's render stage is not built yet") as e:
        runner.start_stage(d, j, stage, {})
    assert e.value.code == 501 and not list((d / "stages").glob("*"))
