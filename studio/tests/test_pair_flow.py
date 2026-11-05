"""The pair transition flow (builder P's file from wave 2 on). The slice of 2026-11-05 left the flow registered,
disabled and empty; these tests pin that state, and builder P replaces them with the flow's own."""

from __future__ import annotations

from reveal_studio.registry import pair
from reveal_studio.registry.flows import ALL_FLOWS, FLOWS
from reveal_studio.registry.hints_pair import HINTS as PAIR_HINTS


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
