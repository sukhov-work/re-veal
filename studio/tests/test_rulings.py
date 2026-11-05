"""The rulings table: a ruled value warns, an unruled one does not, an absent key at a ruled default warns, the ranges,
a stage knob, the 202 body and the record carry the warnings, the plan rows carry theirs, and the why sentences pass
the no-slop checker.

Mutation applied once on 2026-11-05: deleting the `slices` row from RULINGS turned four tests red (4 failed, 211
passed): test_a_ruled_method_warns_with_its_date_and_source, test_a_stage_knob_warns (the render's plan hit is gone),
test_the_record_stores_the_warnings_and_a_run_is_never_refused, and test_registry.py's row count. Restored, 18 pass."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from reveal_studio.config import Settings
from reveal_studio.fs import Json
from reveal_studio.jobs.plans import frozen_plans, plans_of, save_plan
from reveal_studio.registry.flows import stage_def
from reveal_studio.registry.rulings import RULINGS, knob_hits, plan_hits, ruled, stage_warnings
from reveal_studio.runner.process import Runner

from .conftest import FROZEN_PLAN, REPO, Client, wait_record

CHECKER = REPO / ".claude/skills/no-slop/scripts/slop-check.py"


def plan_with(step: Json) -> Json:
    """The test plan with its rife leg replaced by `step`."""
    p = copy.deepcopy(FROZEN_PLAN)
    p["timeline"][1] = step
    return p


def test_a_ruled_method_warns_with_its_date_and_source() -> None:
    hits = plan_hits(plan_with({"to": 1, "n": 6, "method": "slices"}))
    assert [(h["knob"], h["path"], h["value"], h["since"], h["absent"]) for h in hits] == [
        ("timeline[*].method", "/timeline/1/method", "slices", "2026-11-01", False)
    ]
    assert hits[0]["source"] == "DECISIONS 2026-11-01; loops.md §3" and "junky" in hits[0]["why"]
    assert plan_hits(plan_with({"to": 1, "n": 6, "method": "rise", "ghoul_box": [0, 0, 1, 1]}))[0]["since"] == (
        "2026-10-30"
    )


def test_an_unruled_plan_does_not_warn() -> None:
    assert plan_hits(FROZEN_PLAN) == []
    a2_shape = plan_with(
        {"to": 1, "n": 12, "method": "rife", "ease": "sine", "margin": 0.04, "local": [{"box": [0.2, 0.5, 0.4, 0.6]}]}
    )
    a2_shape["matte"] = {"all": True}
    a2_shape["effects"] = [{"kind": "breath", "z": 0.018}, {"kind": "parallax", "amp": 0.014, "ref": 0.15}]
    assert plan_hits(a2_shape) == []


@pytest.mark.parametrize(
    ("step", "path", "value"),
    [
        ({"to": 1, "n": 9, "method": "slide", "box_a": [0, 0, 1, 1], "box_b": [0, 0, 1, 1]}, "/timeline/1/mode", "fly"),
        ({"to": 1, "n": 9, "method": "teleport", "out_box": [0.7, 0.1, 0.9, 0.9]}, "/timeline/1/mode", "squeeze"),
        ({"to": 0, "n": 90, "method": "sheets", "sheets": [{"key": 1}]}, "/timeline/1/sheets/0/carry", 1.0),
    ],
    ids=["slide-flies-by-default", "teleport-squeezes-by-default", "a-sheet-carries-by-default"],
)
def test_an_absent_key_whose_code_default_is_ruled_warns(step: Json, path: str, value: Any) -> None:
    (hit,) = plan_hits(plan_with(step))
    assert (hit["path"], hit["value"], hit["absent"]) == (path, value, True)


@pytest.mark.parametrize(
    ("step", "n_hits"),
    [
        ({"to": 1, "n": 9, "method": "slide", "box_a": [0, 0, 1, 1], "box_b": [0, 0, 1, 1], "mode": "dissolve"}, 0),
        ({"to": 1, "n": 9, "method": "teleport", "mode": "fade"}, 0),
        ({"to": 1, "n": 9, "method": "teleport", "mode": "fade", "flash": 2}, 1),
        ({"to": 1, "n": 9, "method": "teleport", "mode": "fade", "flash": 0}, 0),
        ({"to": 0, "n": 90, "method": "sheets", "sheets": [{"key": 1, "carry": 0}, {"key": 2, "carry": 0.0}]}, 0),
        ({"to": 0, "n": 90, "method": "sheets", "sheets": [{"key": 1, "carry": 0}, {"key": 2, "carry": 0.12}]}, 1),
        ({"to": 1, "n": 9, "method": "dissolve", "mode": "fly"}, 0),  # mode means nothing on a dissolve
    ],
    ids=["slide-dissolve", "teleport-fade", "flash-2", "flash-0", "carry-0", "carry-0.12", "fly-off-a-slide"],
)
def test_the_ranges_and_the_method_condition(step: Json, n_hits: int) -> None:
    assert len(plan_hits(plan_with(step))) == n_hits


def test_ruled_compares_types_and_ranges() -> None:
    assert ruled(True, True) and not ruled(True, 1) and not ruled(True, False)
    assert ruled({"min": 1}, 1) and ruled({"min": 1}, 3.5) and not ruled({"min": 1}, 0.99)
    assert ruled({"above": 0}, 0.001) and not ruled({"above": 0}, 0) and not ruled({"above": 0}, True)
    assert not ruled({"min": 1}, "2") and ruled("slices", "slices") and not ruled("slices", "sheets")


def test_a_stage_knob_warns() -> None:
    (hit,) = knob_hits("registration", {"ecc_refine": True, "bg_depth": 0.15})
    assert (hit["knob"], hit["path"], hit["value"], hit["since"]) == (
        "registration.ecc_refine",
        "registration.ecc_refine",
        True,
        "2026-11-04",
    )
    assert knob_hits("registration", {"ecc_refine": False}) == []
    assert stage_warnings("render", {"plan": "frozen:x"}, plan_with({"to": 1, "n": 6, "method": "slices"}))[0][
        "path"
    ] == ("/timeline/1/method")


def test_the_record_stores_the_warnings_and_a_run_is_never_refused(
    runner: Runner, registered: tuple[Path, Json], settings: Settings
) -> None:
    d, j = registered
    rec = runner.start_stage(d, j, stage_def("loop", "registration"), {"ecc_refine": True, "bg_depth": 0.15})
    assert [w["knob"] for w in rec["warnings"]] == ["registration.ecc_refine"]
    done = wait_record(d, rec["id"])
    assert done["state"] == "done" and done["warnings"] == rec["warnings"]
    save_plan(settings, d, j, "ruled", plan_with({"to": 1, "n": 2, "method": "slices"}), "frozen:tiny_a1", "x")
    r2 = runner.start_stage(d, j, stage_def("loop", "render"), {"plan": "job:ruled", "name": "r1", "draft": 480})
    assert [(w["path"], w["value"]) for w in r2["warnings"]] == [("/timeline/1/method", "slices")]
    clean = runner.start_stage(d, j, stage_def("loop", "render"), {"plan": "frozen:tiny_a1", "name": "c", "draft": 480})
    assert clean["warnings"] == []
    for r in (r2, clean):
        wait_record(d, r["id"])


def test_the_plan_rows_carry_their_warnings(settings: Settings, job: tuple[Path, Json]) -> None:
    d, j = job
    save_plan(settings, d, j, "squeeze", plan_with({"to": 1, "n": 4, "method": "teleport"}), "frozen:tiny_a1", "x")
    (row,) = plans_of(settings, d)
    assert [(w["path"], w["value"], w["absent"]) for w in row["warnings"]] == [("/timeline/1/mode", "squeeze", True)]
    assert frozen_plans(settings)[0]["warnings"] == []


def _poll(client: Client, jid: str, rid: str) -> Json:
    deadline = time.time() + 30
    while time.time() < deadline:
        rec: Json = client.get(f"/api/jobs/{jid}/stages/{rid}")[1]
        if rec["state"] in ("done", "failed", "refused", "lost", "cancelled") and (
            rec["state"] != "done" or rec["outputs"]
        ):
            return rec
        time.sleep(0.1)
    raise AssertionError(f"{rid} did not finish")


def test_the_202_body_carries_the_warnings(client: Client, stills: Path) -> None:
    code, body, _ = client.post("/api/jobs", {"flow": "loop", "folder": str(stills), "seq": "tiny"})
    jid = body["id"]
    code, run, _ = client.post(
        f"/api/jobs/{jid}/stages/registration/run", {"knobs": {"ecc_refine": True, "bg_depth": 0.15}}
    )
    assert code == 202 and run["state"] == "running"
    assert [(w["knob"], w["value"], w["since"]) for w in run["warnings"]] == [
        ("registration.ecc_refine", True, "2026-11-04")
    ]
    assert set(run["warnings"][0]) == {"knob", "value", "since", "why", "source", "path", "absent"}
    done = _poll(client, jid, run["record"])
    assert done["state"] == "done" and done["warnings"] == run["warnings"]  # the record keeps them
    code, run2, _ = client.post(f"/api/jobs/{jid}/stages/registration/run", {"knobs": {}})
    assert code == 202 and run2["warnings"] == []
    _poll(client, jid, run2["record"])


@pytest.mark.skipif(not CHECKER.is_file(), reason=f"the no-slop checker is absent at {CHECKER}")
def test_the_why_sentences_pass_the_prose_checker(tmp_path: Path) -> None:
    text = tmp_path / "rulings_why.md"
    text.write_text("\n\n".join(r["why"] for r in RULINGS) + "\n")
    p = subprocess.run(
        [sys.executable, "-I", str(CHECKER), "--json", "--profile", "file", str(text)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    blocks = [f for f in json.loads(p.stdout or "[]") if f["severity"] == "BLOCK"]
    assert not blocks, blocks
