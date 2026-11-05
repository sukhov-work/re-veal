"""The flow table every layer dispatches by (phase B's generalization slice, 2026-11-05): the flow entries' shape, the
enabled flows, the union of stage names, the shared stages and the identity patterns the Runner reads.

What one flow holds (its stages, hints, routes, argv, views and page entries) is pinned in that flow's own test file:
tests/test_registry.py and tests/test_loop_snapshot.py for the loop, tests/test_pair_flow.py and
tests/test_director_flow.py for the other two.
"""

from __future__ import annotations

from reveal_studio.registry.common import COMMON_STAGES, VERDICT_STAGE
from reveal_studio.registry.flows import ALL_FLOWS, FLOWS, STAGE_NAMES, identity_of

FLOW_KEYS = {"title", "what", "enabled", "stages"}
SPEC_KEYS = {"full", "draft", "terminal", "mp4"}
"""The keys the spec reader needs; `record_knobs` and `fields` are optional."""


def test_every_flow_entry_has_the_shared_shape() -> None:
    """Mutation: a flow entry without `enabled` (the page then offers it) or a candidates spec missing its mp4 name
    (the frames decode then opens nothing) turns this red."""
    assert list(ALL_FLOWS) == ["loop", "pair", "director"]
    for name, f in ALL_FLOWS.items():
        assert set(f) >= FLOW_KEYS, name
        assert isinstance(f["enabled"], bool) and isinstance(f["stages"], list), name
        assert isinstance(f["title"], str) and f["title"] and len(f["what"]) > 20, name
        if f.get("candidates") is not None:
            assert set(f["candidates"]) >= SPEC_KEYS, name
    assert "candidates" not in ALL_FLOWS["loop"]  # the loop keeps its own reader of measure.json


def test_the_enabled_flows_are_the_ones_whose_flag_is_set() -> None:
    """Mutation: FLOWS built from every flow (a disabled flow then reaches POST /api/jobs) turns this red."""
    assert {k: f for k, f in ALL_FLOWS.items() if f["enabled"]} == FLOWS
    assert all(f["stages"] for f in FLOWS.values())  # an enabled flow has stages to run


def test_the_stage_names_are_the_union_in_flow_order() -> None:
    """Mutation: STAGE_NAMES built from the enabled flows only (a disabled flow's job then reads its stages as plan
    paths in the rulings) turns this red once a disabled flow has a stage; today it is the loop's ten."""
    union = [s["name"] for f in ALL_FLOWS.values() for s in f["stages"]]
    assert list(dict.fromkeys(union)) == STAGE_NAMES
    assert len(STAGE_NAMES) == len(set(STAGE_NAMES))


def test_a_shared_stage_is_one_definition_wherever_a_flow_lists_it() -> None:
    """Reveal's verdict is defined once (registry/common.py). Mutation: a flow listing its own copy of `verdict`
    (two argv rules for one name) turns this red."""
    assert COMMON_STAGES == {"verdict": VERDICT_STAGE}
    for f in ALL_FLOWS.values():
        for s in f["stages"]:
            if s["name"] in COMMON_STAGES:
                assert s is COMMON_STAGES[s["name"]], s["name"]
    assert (VERDICT_STAGE["script"], VERDICT_STAGE["terminal"], VERDICT_STAGE["parent"]) == (
        "reveal",
        "metrics.json",
        "import",
    )
    assert VERDICT_STAGE["branch"] is True and VERDICT_STAGE["stale_after"] == [] and VERDICT_STAGE["knobs"] == []


def test_identity_of_reads_the_flow_then_the_shared_stage() -> None:
    """The Runner's "unchanged" files come from the stage definition. Mutation: identity_of reading the loop's
    patterns for every flow (a pair's verdict compared by loop.mp4) turns this red."""
    assert identity_of("loop", "render") == ["loop.mp4"]
    assert identity_of("loop", "registration") == ["*.png", "*.npy"]
    assert identity_of("loop", "page") == [] and identity_of("loop", "probe") == []
    assert identity_of("pair", "verdict") == ["metrics.json"]  # in no stage list yet: the shared definition
    assert identity_of("director", "verdict") == ["metrics.json"]
    assert identity_of("pair", "no-such-stage") == [] and identity_of(None, "render") == []
