"""The director flow over HTTP on the live test server: its five routes (each hit, the route list counted), a job by
pair name, the resolve, a draft and a full render through the stage runner, the page behind the gate, a grade in the
picks shape and a marked frame. The fakes of tests/fakes/ play director_render.py and director_page.py.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import pytest

from reveal_studio.config import Settings
from reveal_studio.fs import Json, read_json
from reveal_studio.server import routes, routes_director

from .conftest import PAIR, Client
from .test_director_flow import R12, write_director_pair

HITS: set[str] = set()
TERMINAL = ("done", "failed", "refused", "lost", "cancelled")


@pytest.fixture(autouse=True)
def record_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every route the dispatcher matches is recorded, so the walk can assert the flow's list is covered."""
    real = routes.match

    def spy(method: str, path: str) -> tuple[routes.Route, re.Match[str]] | None:
        found = real(method, path)
        if found:
            HITS.add(found[0].name)
        return found

    monkeypatch.setattr(routes, "match", spy)


@pytest.fixture
def dpair(root: Path) -> str:
    return write_director_pair(root)


def poll(client: Client, jid: str, rid: str, timeout: float = 30) -> Json:
    deadline = time.time() + timeout
    while time.time() < deadline:
        code, rec, _ = client.get(f"/api/jobs/{jid}/stages/{rid}")
        assert code == 200, rec
        if rec["state"] in TERMINAL and (rec["state"] != "done" or rec["outputs"]):
            return dict(rec)
        time.sleep(0.1)
    raise AssertionError(f"{rid} did not finish in {timeout} s")


def run(client: Client, jid: str, stage: str, knobs: Json) -> Json:
    code, body, _ = client.post(f"/api/jobs/{jid}/stages/{stage}/run", {"knobs": knobs})
    assert code == 202, body
    return poll(client, jid, str(body["record"]))


def new_job(client: Client) -> str:
    code, body, _ = client.post("/api/jobs", {"flow": "director", "pair": PAIR})
    assert code == 201, body
    return str(body["id"])


def test_a_director_job_by_pair_name_and_its_refusals(client: Client, dpair: str) -> None:
    """Mutation: the flow left disabled (POST answers 400 "registered but not built yet"), or a pair without a plan
    making a folder, turns this red."""
    jid = new_job(client)
    code, v, _ = client.get(f"/api/jobs/{jid}")
    assert code == 200 and v["job"]["flow"] == "director" and [i["role"] for i in v["job"]["inputs"]] == ["A", "B"]
    code, body, _ = client.post("/api/jobs", {"flow": "director", "pair": "mismatch_7"})
    assert code == 400 and "no plan under scripts/research/plans/ names the pair mismatch_7" in body["error"]
    code, reg, _ = client.get("/api/registry")
    assert "director" in reg["flows"] and "resolve" in reg["stage_order"]
    assert reg["hints"]["control.director_new_job"]["what"].startswith("Makes a director job")


def test_the_pairs_and_plan_routes(client: Client, dpair: str) -> None:
    """Mutation: the plan route reading the loop's folder (scripts/research/plans/loops/) turns this red."""
    code, pairs, _ = client.get("/api/pairs")
    assert code == 200 and [p["pair"] for p in pairs] == [PAIR] and pairs[0]["plans"] == [f"{PAIR}_r1", R12]
    code, pv, _ = client.get(f"/api/plans/director/{R12}")
    assert code == 200 and pv["stem"] == R12 and [c["id"] for c in pv["concepts"]] == ["c1", "c2"]
    assert client.get("/api/plans/director/tiny_a1")[0] == 404  # a loop plan is no director plan
    assert client.get("/api/plans/director/..%2Fx")[0] == 400


def test_a_saved_plan_opens_through_the_job_and_a_loop_job_is_refused(
    client: Client, settings: Settings, dpair: str, stills: Path
) -> None:
    """Mutation: the job's plan route answering for a loop job (a director view of a loop plan) turns this red."""
    jid = new_job(client)
    raw = read_json(settings.director_plans / f"{R12}.json")
    code, saved, _ = client.post(f"/api/jobs/{jid}/plans", {"name": "mine", "plan": raw, "from": f"frozen:{R12}"})
    assert code == 201, saved
    code, pv, _ = client.get(f"/api/jobs/{jid}/director/plans/mine")
    assert (
        code == 200
        and pv["ref"] == "job:mine"
        and pv["stem"] == R12
        and pv["provenance"]["from"].endswith(R12 + ".json")
    )
    code, body, _ = client.post("/api/jobs", {"flow": "loop", "folder": str(stills), "seq": "tiny"})
    assert client.get(f"/api/jobs/{body['id']}/director/plans/mine")[0] == 400


def test_the_overlay_and_canvas_routes(client: Client, dpair: str) -> None:
    """Mutation: the overlay served without its PNG type, or the canvas thumbnail read before any resolve, turns this
    red."""
    jid = new_job(client)
    for kind in ("base", "elements", "disparity", "matte_1", "matte_3"):
        code, png, h = client.get(f"/api/jobs/{jid}/overlay/A/{kind}.png")
        assert (code, h["content-type"], png[:4]) == (200, "image/png", b"\x89PNG"), kind
    assert client.get(f"/api/jobs/{jid}/overlay/A/matte_9.png")[0] == 404
    assert client.get(f"/api/jobs/{jid}/overlay/A/nope.png")[0] == 404
    assert client.get(f"/api/jobs/{jid}/overlay/C/base.png")[0] == 404  # the job's fallback: no such route
    assert client.get(f"/api/jobs/{jid}/thumb/canvas/A")[0] == 404  # no resolve yet
    rec = run(client, jid, "resolve", {"plan": f"frozen:{R12}", "concept": "c1"})
    assert rec["state"] == "done", rec.get("reason")
    code, jpg, h = client.get(f"/api/jobs/{jid}/thumb/canvas/A?r={rec['id']}")
    assert (code, h["content-type"], jpg[:2]) == (200, "image/jpeg", b"\xff\xd8")
    v = client.get(f"/api/jobs/{jid}")[1]
    code, png, _ = client.get(v["resolve"]["urls"]["canvas_B"])
    assert code == 200 and png[:4] == b"\x89PNG"


def test_a_draft_a_full_render_the_page_a_grade_and_a_mark_over_http(client: Client, dpair: str) -> None:
    """The flow's API end to end on the fakes. Mutation: the picks check dropped (an extra top-level key saved), the
    page run through the stage runner (no gate), or the frame bound ignoring info.json's frames, turns this red."""
    jid = new_job(client)
    d = run(client, jid, "render", {"plan": f"frozen:{R12}", "concept": "c1", "draft": 480})
    assert d["state"] == "done", d.get("reason")
    name = f"{R12}_c1"
    code, rv, _ = client.get(f"/api/jobs/{jid}/render/draft/{name}")
    assert code == 200 and rv["fps"] == 30 and len(rv["series"]["steps"]["points"]) == 89
    code, body, _ = client.post(
        f"/api/jobs/{jid}/frames/mark", {"kind": "draft", "name": name, "frame": 47, "note": "x"}
    )
    assert code == 201 and body["frame"] == 47
    assert client.post(f"/api/jobs/{jid}/frames/mark", {"kind": "draft", "name": name, "frame": 90})[0] == 400
    f = run(client, jid, "render", {"plan": f"frozen:{R12}", "concept": "c1", "draft": 0})
    assert f["state"] == "done" and f["out_final"].endswith(f"/run/{name}")
    assert client.post(f"/api/jobs/{jid}/stages/page/run", {"knobs": {}})[0] == 409  # the gate's route only
    code, body, _ = client.post(f"/api/jobs/{jid}/page", {})
    assert code == 409 and body["refused"] == [name]
    code, body, _ = client.post(f"/api/jobs/{jid}/page", {"override": True, "title": "the test page"})
    assert code == 202, body
    page = poll(client, jid, str(body["record"]))
    assert page["state"] == "done", page.get("reason")
    code, html, _ = client.get(f"/api/jobs/{jid}/file/index.html")
    assert code == 200 and b"the test page" in html and body["override"].encode() in html
    clip = {
        "acceptable": True,
        "note": "his words",
        "props": dict.fromkeys(("one_picture", "transforms", "not_invented"), True),
    }
    picks = {
        "date": "2026-11-05",
        "page": f"{jid}_r1",
        "best": {R12: "c1"},
        "clips": {name: {**clip, "render": f["id"]}},
    }
    assert client.post(f"/api/jobs/{jid}/picks", {"round": 1, "picks": {**picks, "extra": 1}})[0] == 400
    bad = {**picks, "clips": {name: {**clip, "props": {"one_picture": True, "transforms": True}}}}
    assert client.post(f"/api/jobs/{jid}/picks", {"round": 1, "picks": bad})[0] == 400
    code, r, _ = client.post(f"/api/jobs/{jid}/picks", {"round": 1, "picks": picks, "text": "his words"})
    assert code == 200 and r["grade"]["picks"].startswith("picks/director_picks_")
    tiles = {t["name"]: t for t in client.get(f"/api/jobs/{jid}")[1]["stages"]}
    assert tiles["grades"]["state"] == "graded" and tiles["page"]["detail"].endswith("round 1")


def test_every_director_route_is_hit(client: Client, settings: Settings, dpair: str) -> None:
    """One walk over the flow's list, so the coverage holds when this test runs alone. Mutation: a row added to
    routes_director.ROUTES without a test that reaches it turns this red."""
    jid = new_job(client)
    rec = run(client, jid, "resolve", {"plan": f"frozen:{R12}", "concept": "c1"})
    raw = read_json(settings.director_plans / f"{R12}.json")
    assert client.post(f"/api/jobs/{jid}/plans", {"name": "walk", "plan": raw, "from": f"frozen:{R12}"})[0] == 201
    for path in (
        "/api/pairs",
        f"/api/plans/director/{R12}",
        f"/api/jobs/{jid}/director/plans/walk",
        f"/api/jobs/{jid}/overlay/B/elements.png",
        f"/api/jobs/{jid}/thumb/canvas/B?r={rec['id']}",
    ):
        assert client.get(path)[0] == 200, path
    missing = sorted(r.name for r in routes_director.ROUTES if r.name not in HITS)
    assert not missing, f"director routes no test reaches: {missing}"
    assert len(routes_director.ROUTES) == 5
    assert all(r in routes.ROUTES for r in routes_director.ROUTES) and routes.ROUTES[-2:] == routes.FALLBACKS
