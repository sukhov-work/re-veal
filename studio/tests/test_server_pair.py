"""The pair flow over HTTP (builder P, phase B): a new pair job by POST /api/jobs, the four rows of
server/routes_pair.ROUTES, the shared rows a pair job uses (the stage run, the page behind the gate, the picks, the
render view and its frames), and a walk that hits every row of the flow's list with this file's own spy. Every
assertion names the mutation that turns it red."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

import pytest

from reveal_studio.fs import Json, md5_file, read_json
from reveal_studio.server import routes, routes_pair

from .conftest import Client

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


def poll(client: Client, jid: str, rid: str, timeout: float = 30) -> Json:
    deadline = time.time() + timeout
    while time.time() < deadline:
        code, rec, _ = client.get(f"/api/jobs/{jid}/stages/{rid}")
        assert code == 200, rec
        if rec["state"] in TERMINAL and (rec["state"] != "done" or rec.get("outputs")):
            return dict(rec)
        time.sleep(0.05)
    raise AssertionError(f"{rid} did not finish in {timeout} s")


def run(client: Client, jid: str, stage: str, knobs: Json | None = None) -> Json:
    code, body, _ = client.post(f"/api/jobs/{jid}/stages/{stage}/run", {"knobs": knobs or {}})
    assert code == 202, body
    return poll(client, jid, str(body["record"]))


def new_pair(client: Client, fixture: str) -> tuple[str, Path, Json]:
    code, body, _ = client.post("/api/jobs", {"flow": "pair", "fixture": fixture})
    assert code == 201, body
    return str(body["id"]), Path(body["job"]["root"]), body["job"]


def test_post_jobs_makes_a_pair_job_from_a_fixture_or_two_paths(client: Client, fixture_pair: str) -> None:
    """Mutation: POST /api/jobs dropping `a`, `b` or `fixture`, or the pair flow disabled, turns this red."""
    jid, _, job = new_pair(client, fixture_pair)
    assert (job["flow"], job["seq"], job["fixture"], [i["role"] for i in job["inputs"]]) == (
        "pair",
        "tiny_1",
        "tiny_1",
        ["A", "B"],
    )
    code, body, _ = client.post(
        "/api/jobs",
        {"flow": "pair", "a": "fixtures/tiny_1_S.jpg", "b": "fixtures/tiny_1_F.jpg", "seq": "two_paths"},
    )
    assert code == 201 and (body["job"]["seq"], body["job"]["fixture"]) == ("two_paths", None)
    code, body, _ = client.post("/api/jobs", {"flow": "pair"})
    assert code == 400 and body["error"] == "a pair job needs a fixture pair's name, or two photos a and b"
    rows = {r["id"]: r for r in client.get("/api/jobs")[1]}
    assert (rows[jid]["flow"], rows[jid]["stills"]) == ("pair", 2)
    code, reg, _ = client.get("/api/registry")
    assert "pair" in reg["flows"] and "relation" in reg["stage_order"] and "control.pair_new_job" in reg["hints"]


def test_the_fixtures_route_lists_the_pairs(client: Client, fixture_pair: str) -> None:
    """Mutation: the route listing the director's planned pairs only, or a photo without its size, turns this red."""
    code, body, _ = client.get("/api/fixtures")
    assert code == 200 and body == [
        {"name": "tiny_1", "A": {"name": "tiny_1_S.jpg", "bytes": body[0]["A"]["bytes"]}, "B": body[0]["B"]}
    ]
    assert body[0]["A"]["bytes"] > 0 and body[0]["B"]["name"] == "tiny_1_F.jpg"


def test_the_relation_routes_before_and_after_a_run(client: Client, fixture_pair: str) -> None:
    """Mutation: the frame route decoding the relation's mp4 before it exists (a 500), or a frame index off by one,
    turns this red."""
    jid, _, _ = new_pair(client, fixture_pair)
    code, v, _ = client.get(f"/api/jobs/{jid}/relation")
    assert code == 200 and (v["exists"], v["state"]) == (False, "none")
    code, body, _ = client.get(f"/api/jobs/{jid}/relation/frame/0")
    assert code == 404 and body["error"] == "no relation yet: run the relation first"
    rec = run(client, jid, "relation")
    assert rec["state"] == "done" and rec["argv"][-4:] == ["--max-long", "480", "--seconds", "1"]
    code, v, _ = client.get(f"/api/jobs/{jid}/relation")
    assert code == 200 and v["report"]["class"] == "B" and v["n_frames"] == 30
    code, jpg, h = client.get(v["a_url"])
    assert (code, jpg[:2], h["content-type"]) == (200, b"\xff\xd8", "image/jpeg")
    assert client.get(f"/api/jobs/{jid}/relation/frame/29")[0] == 200
    assert client.get(f"/api/jobs/{jid}/relation/frame/30")[0] == 404
    code, strip, _ = client.get(v["strip_url"])
    assert code == 200 and strip[:2] == b"\xff\xd8"
    assert client.get(f"/api/jobs/{jid}")[1]["relation"]["md5_mp4"] == v["md5_mp4"]


def test_the_relation_route_refuses_a_job_of_another_flow(client: Client, stills: Path) -> None:
    """Mutation: _require_pair dropped (a loop job then reads as a pair without a relation) turns this red."""
    code, body, _ = client.post("/api/jobs", {"flow": "loop", "folder": str(stills), "seq": "tiny"})
    assert code == 201
    code, err, _ = client.get(f"/api/jobs/{body['id']}/relation")
    assert code == 404 and "is a loop job" in err["error"]


def test_the_verdict_route_refused_then_done(
    client: Client, fixture_pair: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mutation: the verdict view reading metrics.json left by an earlier run as the latest result, or the stills'
    URLs pointing outside the job folder, turns this red."""
    jid, _, _ = new_pair(client, fixture_pair)
    monkeypatch.setenv("FAKE_REFUSE", "align")
    rec = run(client, jid, "verdict")
    code, v, _ = client.get(f"/api/jobs/{jid}/verdict")
    assert code == 200 and (v["state"], v["reason"], v["metrics"]) == (
        "refused",
        "FAILED: the photos share too little detail",
        None,
    )
    assert rec["argv"][2] == "align" and rec["argv"][-2] == "--out"
    monkeypatch.delenv("FAKE_REFUSE")
    run(client, jid, "verdict")
    code, v, _ = client.get(f"/api/jobs/{jid}/verdict")
    assert v["state"] == "done" and v["metrics"]["inliers"] == 481
    code, jpg, _ = client.get(v["stills"]["after_aligned"])
    assert code == 200 and jpg[:2] == b"\xff\xd8"


def test_a_render_its_view_frames_and_thumbnail(client: Client, fixture_pair: str) -> None:
    """Mutation: the render view by flow falling back to the loop's (no frames_tags for a pair, fps 25) or the frame
    decode opening loop.mp4 turns this red."""
    jid, _, _ = new_pair(client, fixture_pair)
    rec = run(client, jid, "render", {"name": "f1", "fps": 30, "seconds": 1})
    assert rec["state"] == "done", rec.get("reason")
    code, r, _ = client.get(f"/api/jobs/{jid}/render/full/f1")
    assert code == 200 and (r["fps"], len(r["frames_tags"]), len(r["steps"]), r["frames_available"]) == (
        30.0,
        30,
        29,
        30,
    )
    code, jpg, _ = client.get(r["frame_url"] + "29")
    assert code == 200 and jpg[:2] == b"\xff\xd8"
    assert client.get(f"/api/jobs/{jid}/thumb/render/full/f1")[0] == 200
    code, mp4, _ = client.get(r["mp4_url"])
    assert code == 200 and len(mp4) > 100


def test_the_page_through_the_shared_route_behind_the_gate(client: Client, fixture_pair: str) -> None:
    """Mutation: the shared page route sending a builtin page to the Runner (a 400 "not a process") or skipping the
    gate turns this red; the page served at the job's file route closes it."""
    jid, _, _ = new_pair(client, fixture_pair)
    run(client, jid, "render", {"name": "f1"})
    code, body, _ = client.post(f"/api/jobs/{jid}/page", {})
    assert code == 409 and body["refused"] == ["f1"]
    code, body, _ = client.post(f"/api/jobs/{jid}/page", {"override": True, "footer": "a test"})
    assert code == 202 and body["state"] == "done" and body["override"].startswith("Override: built on his word")
    code, rec, _ = client.get(f"/api/jobs/{jid}/stages/{body['record']}")
    assert code == 200 and rec["builtin"] is True and rec["command"] == "" and rec["log_tail"]
    code, html, h = client.get(f"/api/jobs/{jid}/file/index.html")
    assert code == 200 and h["content-type"].startswith("text/html") and b"a test" in html
    v = client.get(f"/api/jobs/{jid}")[1]
    assert v["page"]["exists"] and v["rounds"][0]["record"] == body["record"]
    assert v["page"]["md5"] == v["rounds"][0]["page_md5"]


def test_a_grade_in_the_picks_shape_over_http(client: Client, fixture_pair: str, settings: Any) -> None:
    """Mutation: the picks route accepting a clip without its props, or the full render after the round starting
    before the grade, turns this red."""
    jid, root, _ = new_pair(client, fixture_pair)
    run(client, jid, "render", {"name": "f1"})
    assert client.post(f"/api/jobs/{jid}/page", {"override": True})[0] == 202
    code, body, _ = client.post(f"/api/jobs/{jid}/stages/render/run", {"knobs": {"name": "f2"}})
    assert code == 409 and body["round"] == 1  # the round gate: a new round's first full render waits for the grade
    bad = {"date": "d", "page": "p", "best": {"tiny_1": "f1"}, "clips": {"f1": {"acceptable": True, "note": ""}}}
    assert client.post(f"/api/jobs/{jid}/picks", {"round": 1, "picks": bad, "text": ""})[0] == 400
    props = {"one_picture": True, "transforms": True, "not_invented": True}
    good = dict(bad, clips={"f1": {"acceptable": True, "note": "fine", "props": props}})
    code, r, _ = client.post(f"/api/jobs/{jid}/picks", {"round": 1, "picks": good, "text": "his words"})
    assert code == 200 and r["grade"]["text"] == "his words"
    d = settings.root / root
    assert read_json(d / r["grade"]["picks"]) == good
    assert client.post(f"/api/jobs/{jid}/stages/render/run", {"knobs": {"name": "f2"}})[0] == 202


def test_every_row_of_the_pair_routes_is_hit(client: Client, fixture_pair: str, settings: Any) -> None:
    """One walk over the flow's list, so the coverage holds when this test runs alone. Mutation: a row added to
    routes_pair.ROUTES without a test that reaches it turns this red."""
    jid, root, _ = new_pair(client, fixture_pair)
    run(client, jid, "relation")
    for path in (
        "/api/fixtures",
        f"/api/jobs/{jid}/relation",
        f"/api/jobs/{jid}/relation/frame/0",
        f"/api/jobs/{jid}/verdict",
    ):
        assert client.get(path)[0] == 200, path
    missing = sorted(r.name for r in routes_pair.ROUTES if r.name not in HITS)
    assert not missing, f"pair routes no test reaches: {missing}"
    assert len(routes_pair.ROUTES) == 4
    names = [r.name for r in routes.ROUTES]
    assert all(names.index(r.name) < names.index("GET job_route_unknown") for r in routes_pair.ROUTES)
    assert md5_file(settings.root / root / "relation" / "transition.mp4")
