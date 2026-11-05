"""The repaint leg of phase B in the studio (scripts/research/loop_seq.py's `repaint` method, its SCHEMA.md section of
2026-11-05): the method and its four schema entries as the plan editor reads them, the step's groups, the frame kind
the step rules read, and a repaint plan saved in a seven-still job and drafted through the fake script."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, read_json
from reveal_studio.jobs.plans import save_plan
from reveal_studio.jobs.store import create_job
from reveal_studio.registry.hints import HINTS
from reveal_studio.registry.schema import (
    CHAIN_METHODS,
    METHODS,
    element_groups,
    resolve,
    schema_view,
    validate_plan,
)
from reveal_studio.runner.process import Runner
from reveal_studio.views.measures import frame_kinds, stalls_and_jumps
from reveal_studio.views.render import render_view

from .conftest import run, write_stills

# The four entries and the defaults SCHEMA.md states (chain_luma.py's --front, --overlap and --zone-erode); `through`
# has no default: without it the leg repaints one pair.
REPAINT_DEFAULTS: dict[str, object] = {
    "timeline[method=repaint].through": None,
    "timeline[method=repaint].front": 0.35,
    "timeline[method=repaint].overlap": 0.35,
    "timeline[method=repaint].zone_erode": 15,
}
PLAN: Json = {
    "seq": "seven",
    "in": "benchmarks/runs/2026-11-05/somewhere/in/seven",
    "title": "one repaint leg over seven stills",
    "gag": "a test plan",
    "timeline": [
        {"key": 0, "hold": 3},
        {"to": 6, "method": "repaint", "through": [1, 2, 3, 4, 5], "n": 12, "ease": "smooth", "front": 0.3},
        {"key": 6, "hold": 2},
        {"to": 0, "method": "cut", "n": 0},
    ],
}


def test_the_plan_editor_sees_the_repaint_entries_through_the_schema_view() -> None:
    """The editor reads GET /api/registry's plan_schema (schema_view) and fills a step's absent keys with `resolve`.
    Mutation: a repaint entry dropped, a default changed, the repaint group missing from GROUPS, or an entry under the
    chain group (the step would not resolve it) turns this red."""
    v = schema_view()
    entries = {e["path"]: e for e in v["entries"]}
    for path, default in REPAINT_DEFAULTS.items():
        e = entries[path]
        assert (e["group"], e["default"], e["range"]) == ("repaint", default, None), path
        assert e["default_from"] == (None if default is None else "SCHEMA.md"), path
        assert e["hint"] in HINTS and HINTS[e["hint"]].get("default") == default, path
    assert {
        "group": "repaint",
        "path": "timeline[method=repaint].",
        "hint": "plan.timeline.repaint.",
        "title": "repaint",
    } in v["groups"]
    assert resolve(PLAN, "timeline[method=repaint].front") == [("/timeline/1/front", 0.3, True)]
    assert resolve(PLAN, "timeline[method=repaint].overlap") == [("/timeline/1/overlap", 0.35, False)]
    assert resolve(PLAN, "timeline[method=repaint].zone_erode") == [("/timeline/1/zone_erode", 15, False)]
    assert resolve(PLAN, "timeline[method=repaint].through") == [("/timeline/1/through", [1, 2, 3, 4, 5], True)]
    assert resolve(PLAN, "timeline[*].method") == [
        ("/timeline/1/method", "repaint", True),
        ("/timeline/3/method", "cut", True),
    ]


def test_a_repaint_step_validates_and_takes_no_chain_key() -> None:
    """loop_seq.py dispatches the leg before its `through` branch, so the step reads its own group and the transition's
    keys, never the chain's weights, soft and knot_margin. Mutation: repaint added to CHAIN_METHODS, or dropped from
    METHODS (validate_plan then refuses the step), turns this red."""
    assert METHODS[-1] == "repaint" and "repaint" not in CHAIN_METHODS
    assert element_groups("timeline", PLAN["timeline"][1], ["plan"]) == ["repaint", "transition"]
    validate_plan(PLAN)
    with pytest.raises(StudioError, match="method 'draw' is not one of"):
        validate_plan({**PLAN, "timeline": [{"key": 0}, {"to": 1, "method": "draw"}]})


def test_the_method_sentence_names_every_method() -> None:
    """The plan.timeline.method hint lists what each method does. Mutation: a method added to METHODS without its
    clause in that sentence (repaint before phase B's leg) turns this red."""
    what = HINTS["plan.timeline.method"]["what"]
    assert [m for m in METHODS if not re.search(rf"\b{m}\b", what)] == []


def test_a_repaint_frame_reads_as_a_blend_for_the_step_rules() -> None:
    """A repaint frame is a per-pixel blend of the stills, nothing generated: the stall and jump rules treat it as an
    in-between, neither a hold nor a cut. Mutation: _kind returning the word repaint, or generated, turns the first
    assert red; a repaint frame read as a hold drops the stall."""
    leg: list[Json] = [
        {"generated": "none (repaint)", "u": u, "segment": [0, 1], "t": u, "step": 1, "from": 0, "to": 1}
        for u in (0.2, 0.4, 0.6, 0.8)
    ]
    rows: list[Json] = [{"step": 0, "key": 0, "generated": "none (photo)"}, *leg]
    rows.append({"step": 2, "key": 1, "generated": "none (photo)"})
    kinds = frame_kinds(rows)
    assert kinds == ["hold", "blend", "blend", "blend", "blend", "hold"]
    assert stalls_and_jumps([1.0, 0.1, 0.1, 1.0, 1.0], kinds)["stalls"] == [[1, 2]]


def test_a_saved_repaint_plan_drafts_through_the_fake_in_a_seven_still_job(
    settings: Settings, runner: Runner, tmp_path: Path
) -> None:
    """Seven stills (the boxes' count), a repaint plan saved in the job with its provenance block, a 480 draft through
    the Runner: frames.json carries the leg's rows in the real script's shape, the render view tags them with the
    script's word and the kind blend, and nothing counts as generated. Mutation: the fake writing the leg as plain
    blends, frame_kinds reading the word, or the leg's frames counted as generated turns this red."""
    j = create_job(settings, "loop", folder=str(write_stills(tmp_path / "seven", 7)), seq="seven")
    d = settings.root / j["root"]
    assert run(runner, d, j, "registration")["state"] == "done"
    saved = save_plan(settings, d, j, "repaint7", PLAN, words="one repaint leg over the seven stills")
    assert saved["ref"] == "job:repaint7" and saved["changes"] == []
    prov = read_json(d / "plans" / "repaint7.json")["provenance"]
    assert (prov["from"], prov["words"]) == (None, "one repaint leg over the seven stills")
    rec = run(runner, d, j, "render", {"plan": "job:repaint7", "name": "r7", "draft": 480})
    assert rec["state"] == "done", rec.get("reason")
    rows = read_json(d / "drafts" / "seven" / "r7" / "frames.json")
    leg = [r for r in rows if r.get("method") == "repaint"]
    assert len(leg) == 12 and {r["generated"] for r in leg} == {"none (repaint)"}
    assert (leg[0]["segment"], leg[-1]["segment"]) == ([0, 1], [5, 6])
    assert all(set(r) >= {"u", "segment", "t"} for r in leg)
    v = render_view(settings, d, j, "draft", "r7")
    assert [t["tag"] for t in v["frames_tags"]] == ["photo"] * 3 + ["repaint"] * 12 + ["photo"] * 2
    assert v["frame_kinds"] == ["hold"] * 3 + ["blend"] * 12 + ["hold"] * 2
    assert not any(t["generated"] for t in v["frames_tags"]) and v["measure"]["generated_frames"] == 0
