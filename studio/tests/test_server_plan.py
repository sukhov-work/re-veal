"""The page's variants (backlog T76) and the plan editor's API: the argv order, the gate on the listed candidates only,
the 400 for a name that is not a full render, the round's record, the fake script's --variants, the registry's
plan_schema and rulings, and a plan saved from an edited copy with its one change.

Mutation applied once on 2026-11-05: building the gate over every full render again (`listed = full` in
views/page.py's build_page) turned test_the_gate_checks_the_listed_candidates_only red (c1 refused while excluded)."""

from __future__ import annotations

import copy
import time
from pathlib import Path

import pytest

from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, md5_file, read_json, write_json
from reveal_studio.registry.flows import stage_def
from reveal_studio.registry.rulings import RULINGS
from reveal_studio.registry.schema import PLAN_SCHEMA
from reveal_studio.runner.process import Runner
from reveal_studio.views.page import build_page

from .conftest import FROZEN_PLAN, Client, run, wait_for, wait_record

RENDER = {"plan": "frozen:tiny_a1", "draft": 0}


@pytest.fixture
def two(runner: Runner, registered: tuple[Path, Json]) -> tuple[Path, Json]:
    """Two full renders, c1 unjudged and c2 READY on its md5, and one draft d1."""
    d, j = registered
    for name in ("c1", "c2"):
        assert run(runner, d, j, "render", {**RENDER, "name": name})["state"] == "done"
    assert run(runner, d, j, "render", {**RENDER, "name": "d1", "draft": 480})["state"] == "done"
    write_json(
        d / "answers" / "skeptic_20261105-140000.json",
        {"at": "t", "candidates": {"c2": {"verdict": "READY", "judged_md5": md5_file(d / "tiny" / "c2" / "loop.mp4")}}},
    )
    return d, j


def test_the_argv_lists_the_variants_in_their_order(runner: Runner, two: tuple[Path, Json]) -> None:
    d, j = two
    rec = build_page(runner, d, j, {"variants": ["c2", "c1"], "override": True})
    argv = rec["argv"]
    assert argv[argv.index("--variants") + 1] == "c2,c1"
    assert [Path(i["path"]).parent.name for i in rec["inputs"]] == ["c2", "c1"]
    assert rec["knobs"]["variants"] == ["c2", "c1"]
    assert wait_record(d, rec["id"])["state"] == "done"
    r1 = wait_for(lambda: read_json(d / "rounds" / "1" / "round.json"))
    assert (r1["candidates"], r1["variants"]) == (["c2", "c1"], ["c2", "c1"])
    page = (d / "index.html").read_text()
    assert page.index("tiny/c2") < page.index("tiny/c1")  # the fake lists them in the given order


def test_no_variants_passes_no_flag_and_lists_every_full_render(runner: Runner, two: tuple[Path, Json]) -> None:
    d, j = two
    rec = build_page(runner, d, j, {"override": True})
    assert "--variants" not in rec["argv"] and rec["knobs"]["variants"] == []
    assert [Path(i["path"]).parent.name for i in rec["inputs"]] == ["c1", "c2"]
    wait_record(d, rec["id"])
    r1 = wait_for(lambda: read_json(d / "rounds" / "1" / "round.json"))
    assert (r1["candidates"], r1["variants"]) == (["c1", "c2"], [])


def test_the_gate_checks_the_listed_candidates_only(runner: Runner, two: tuple[Path, Json]) -> None:
    d, j = two
    with pytest.raises(StudioError) as e:  # every full render: c1 is unjudged
        build_page(runner, d, j, {})
    assert (e.value.code, e.value.extra) == (409, {"refused": ["c1"]})
    with pytest.raises(StudioError) as e:  # c1 listed: refused, and only c1 is named
        build_page(runner, d, j, {"variants": ["c2", "c1"]})
    assert e.value.extra == {"refused": ["c1"]}
    rec = build_page(runner, d, j, {"variants": ["c2"]})  # c1 excluded: no override needed
    assert "override" not in rec["knobs"]
    assert wait_record(d, rec["id"])["state"] == "done"


@pytest.mark.parametrize(
    ("variants", "text"),
    [
        (["zz"], "variants: zz is not a full render of this job (the full renders are ['c1', 'c2'])"),
        (["d1"], "variants: d1 is not a full render"),  # a draft is not a candidate
        (["c1", "c1"], "variants: c1 is named twice"),
        ({"c1": 1}, "variants is a list of full render names"),
        ([1, 2], "variants is a list of full render names"),
    ],
    ids=["unknown", "a-draft", "twice", "an-object", "numbers"],
)
def test_a_bad_variants_list_is_a_400_naming_it(
    runner: Runner, two: tuple[Path, Json], variants: object, text: str
) -> None:
    d, j = two
    n = len(list((d / "stages").iterdir()))
    with pytest.raises(StudioError) as e:
        build_page(runner, d, j, {"variants": variants, "override": True})
    assert e.value.code == 400 and str(e.value).startswith(text), str(e.value)
    assert len(list((d / "stages").iterdir())) == n  # no record was made


def test_a_comma_string_is_a_list(runner: Runner, two: tuple[Path, Json]) -> None:
    d, j = two
    rec = build_page(runner, d, j, {"variants": " c2 , ", "override": True})
    assert rec["knobs"]["variants"] == ["c2"]
    wait_record(d, rec["id"])


def test_the_fake_script_refuses_a_name_that_is_not_a_full_render(runner: Runner, two: tuple[Path, Json]) -> None:
    d, j = two  # past the studio's own check: the script's FAILED line makes the record refused
    rec = wait_record(d, runner.start_stage(d, j, stage_def("loop", "page"), {"variants": ["zz"]})["id"])
    assert rec["state"] == "refused" and rec["reason"] == "FAILED: page --variants: zz is not a full render of tiny"
    assert not (d / "index.html").exists()


def test_the_page_over_http_with_variants(client: Client, stills: Path) -> None:
    code, body, _ = client.post("/api/jobs", {"flow": "loop", "folder": str(stills), "seq": "tiny"})
    jid = body["id"]
    for stage, knobs in (("registration", {}), ("render", {**RENDER, "name": "c1"})):
        code, r, _ = client.post(f"/api/jobs/{jid}/stages/{stage}/run", {"knobs": knobs})
        assert code == 202
        deadline = time.time() + 30
        while client.get(f"/api/jobs/{jid}/stages/{r['record']}")[1]["state"] == "running" and time.time() < deadline:
            time.sleep(0.05)
    code, err, _ = client.post(f"/api/jobs/{jid}/page", {"variants": ["zz"], "override": True})
    assert (code, err["unknown"]) == (400, "zz") and err["error"].startswith("variants: zz is not a full render")
    code, ok, _ = client.post(f"/api/jobs/{jid}/page", {"variants": ["c1"], "override": True})
    assert code == 202 and ok["override"].startswith("Override: built on his word with c1")


def test_the_registry_serves_the_plan_schema_and_the_rulings(client: Client) -> None:
    code, reg, _ = client.get("/api/registry")
    assert code == 200
    assert len(reg["plan_schema"]["entries"]) == len(PLAN_SCHEMA) and reg["plan_schema"]["date"] == "2026-11-05"
    assert reg["rulings"] == RULINGS
    assert {e["path"]: e["default"] for e in reg["plan_schema"]["entries"]}["timeline[method=slide].mode"] == "fly"


def test_an_edited_copy_saves_its_one_change(client: Client, stills: Path) -> None:
    code, body, _ = client.post("/api/jobs", {"flow": "loop", "folder": str(stills), "seq": "tiny"})
    jid = body["id"]
    base = {**copy.deepcopy(FROZEN_PLAN), "effects": [{"kind": "breath", "z": 0.018, "cx": 0.374, "cy": 0.31}]}
    code, first, _ = client.post(
        f"/api/jobs/{jid}/plans", {"name": "base", "plan": base, "from": "frozen:tiny_a1", "words": "agent D"}
    )
    assert code == 201 and first["changes"] == [{"path": "/effects", "old": None, "new": base["effects"]}]
    code, same, _ = client.post(f"/api/jobs/{jid}/plans", {"name": "copy", "plan": base, "from": "job:base"})
    assert code == 201 and same["changes"] == []  # an unchanged copy records no change
    edited = copy.deepcopy(base)
    edited["effects"][0]["z"] = 0.02
    code, z, _ = client.post(f"/api/jobs/{jid}/plans", {"name": "z", "plan": edited, "from": "job:base", "words": "z"})
    assert code == 201 and z["changes"] == [{"path": "/effects/0/z", "old": 0.018, "new": 0.02}]
    code, saved, _ = client.get(f"/api/jobs/{jid}/plans/z")
    assert saved["provenance"]["from"].endswith("plans/base.json") and saved["provenance"]["author"] == "owner"
