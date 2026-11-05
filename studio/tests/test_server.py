"""The live server on 127.0.0.1: the page and its assets, the API's JSON shapes and codes, a stage run through the API,
the file route's Range answer, the Host check, the body rules, the page gate, and every route of the table hit."""

from __future__ import annotations

import http.client
import json
import re
import time
from pathlib import Path
from typing import Any

import pytest

from reveal_studio.config import Settings
from reveal_studio.fs import Json
from reveal_studio.jobs import store
from reveal_studio.jobs.store import create_director_job, create_pair_job
from reveal_studio.registry.flows import ALL_FLOWS, stage_order
from reveal_studio.registry.hints import HINTS
from reveal_studio.server import routes, routes_director, routes_pair
from reveal_studio.server.app import App, StudioServer

from .conftest import HELPER, Client

HITS: set[str] = set()
TERMINAL = ("done", "failed", "refused", "lost", "cancelled")


@pytest.fixture(autouse=True)
def record_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every route the dispatcher matches is recorded, so the last test can assert the table is covered."""
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
        if rec["state"] in TERMINAL and (rec["state"] != "done" or rec["outputs"]):
            return dict(rec)
        time.sleep(0.1)
    raise AssertionError(f"{rid} did not finish in {timeout} s")


def new_job(client: Client, stills: Path) -> str:
    code, body, _ = client.post("/api/jobs", {"flow": "loop", "folder": str(stills), "seq": "tiny"})
    assert code == 201, body
    assert body["job"]["id"] == body["id"]
    return str(body["id"])


def run_stage(client: Client, jid: str, stage: str, knobs: Json) -> Json:
    code, body, _ = client.post(f"/api/jobs/{jid}/stages/{stage}/run", {"knobs": knobs})
    assert code == 202, body
    assert body["state"] == "running" and body["argv"][1] == "scripts/research/loop_seq.py"
    return poll(client, jid, body["record"])


def rendered_job(client: Client, stills: Path) -> str:
    jid = new_job(client, stills)
    assert run_stage(client, jid, "registration", {"depth_maps": True})["state"] == "done"
    assert run_stage(client, jid, "render", {"plan": "frozen:tiny_a1", "name": "c1"})["state"] == "done"
    return jid


def test_the_page_and_its_assets(client: Client) -> None:
    code, html, h = client.get("/")
    assert code == 200 and h["content-type"] == "text/html; charset=utf-8" and h["cache-control"] == "no-store"
    page = html.decode()
    scripts = re.findall(r'<script src="/static/js/([a-z]+)\.js"></script>', page)
    # the flows' scripts after graph.js and before boot.js (phase B's slice): boot.js reads every entry they register
    assert scripts == [
        "core",
        "rail",
        "strip",
        "panels",
        "plan",
        "viewer",
        "inspector",
        "graph",
        "pair",
        "director",
        "boot",
    ]
    assert re.findall(r'href="/static/css/([a-z]+)\.css"', page) == [
        "studio",
        "plan",
        "viewer",
        "graph",
        "pair",
        "director",
    ]
    for asset, ctype in (
        ("js/core.js", "text/javascript; charset=utf-8"),
        ("css/studio.css", "text/css; charset=utf-8"),
    ):
        code, body, h = client.get(f"/static/{asset}")
        assert (code, h["content-type"], h["cache-control"]) == (200, ctype, "no-store")
        assert len(body) > 100
    for bad in ("/static/../x", "/static/../../pyproject.toml", "/static/js/absent.js", "/static/"):
        code, body, _ = client.get(bad)
        assert code == 404, bad
    assert client.get("/favicon.ico")[0] == 204


def test_head_answers_without_a_body(client: Client) -> None:
    conn = http.client.HTTPConnection("127.0.0.1", client.port, timeout=10)
    conn.request("HEAD", "/api/registry", headers={"Host": f"127.0.0.1:{client.port}"})
    r = conn.getresponse()
    assert r.status == 200 and int(r.getheader("Content-Length") or 0) > 0 and r.read() == b""
    conn.close()


def test_the_registry_route(client: Client, app: App) -> None:
    code, reg, _ = client.get("/api/registry")
    assert code == 200
    assert reg["hints"] == HINTS and len(reg["hints"]) >= 85
    assert reg["stage_order"][0] == "import" and reg["port"] == app.settings.port
    assert reg["ui_version"] == "reveal-studio 0.2.0"
    assert reg["flows"]["loop"]["stages"][1]["knobs"][0]["flag"] == "--long"


def test_a_job_made_and_run_through_the_api(client: Client, stills: Path) -> None:
    assert client.get("/api/jobs")[1] == []
    jid = rendered_job(client, stills)
    code, rows, _ = client.get("/api/jobs")
    assert code == 200 and [r["id"] for r in rows] == [jid]
    assert (rows[0]["candidates"], rows[0]["unjudged"], rows[0]["last_render"]) == (1, 1, "done")
    code, view, _ = client.get(f"/api/jobs/{jid}")
    assert code == 200 and [c["name"] for c in view["candidates"]] == ["c1"]
    reg = {s["name"]: s for s in view["stages"]}["registration"]
    code, rec, _ = client.get(f"/api/jobs/{jid}/stages/{reg['latest']}")
    assert code == 200 and rec["command"].split()[1:3] == ["scripts/research/loop_seq.py", "prep"]
    code, rv, _ = client.get(f"/api/jobs/{jid}/render/full/c1")
    assert code == 200 and rv["frames_available"] == 9 and len(rv["frames_tags"]) == 9
    for path in (
        f"/api/jobs/{jid}/render/full/c1/frame/0",
        f"/api/jobs/{jid}/thumb/still/0",
        f"/api/jobs/{jid}/thumb/raw/1",
        f"/api/jobs/{jid}/thumb/render/full/c1",
    ):
        code, body, h = client.get(path)
        assert (code, h["content-type"], h["cache-control"]) == (200, "image/jpeg", "private, max-age=3600"), path
        assert body[:2] == b"\xff\xd8"
    assert client.get(f"/api/jobs/{jid}/render/full/c1/frame/99")[0] == 404
    assert client.get(f"/api/jobs/{jid}/thumb/still/7")[0] == 404
    assert client.get(f"/api/jobs/{jid}/render/full/zz")[0] == 404


def test_post_jobs_refuses_a_bad_folder(client: Client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    code, body, _ = client.post("/api/jobs", {"flow": "loop", "folder": str(tmp_path / "none")})
    assert code == 400 and "is not a folder" in body["error"]
    # the enabled flows set by the test itself, so the refusal holds whichever flows the registry enables (builder
    # D enabled the director flow on 2026-11-05)
    monkeypatch.setattr(store, "FLOWS", {"loop": ALL_FLOWS["loop"]})
    code, body, _ = client.post("/api/jobs", {"flow": "pair", "folder": str(tmp_path)})
    assert code == 400 and body["error"].startswith("the flow is one of ['loop']")


def test_the_file_route_answers_ranges_and_refuses_escapes(client: Client, stills: Path) -> None:
    jid = rendered_job(client, stills)
    path = f"/api/jobs/{jid}/file/tiny/c1/loop.mp4"
    code, whole, h = client.get(path)
    assert (code, h["content-type"], h["accept-ranges"]) == (200, "video/mp4", "bytes")
    code, part, h = client.get(path, {"Range": "bytes=10-19"})
    assert (code, part, h["content-range"]) == (206, whole[10:20], f"bytes 10-19/{len(whole)}")
    code, tail, h = client.get(path, {"Range": "bytes=-5"})
    assert (code, tail) == (206, whole[-5:])
    assert client.get(path, {"Range": f"bytes={len(whole)}-"})[0] == 416
    assert client.get(path, {"Range": "bytes=x-y"})[0] == 416
    assert client.get(f"/api/jobs/{jid}/file/job.json")[0] == 200  # the job folder's own files
    assert client.get(f"/api/jobs/{jid}/file/../../x")[0] == 403
    assert client.get(f"/api/jobs/{jid}/file/raw/tiny/01.jpg")[0] == 404  # a symlink out of the job
    assert client.get(f"/api/jobs/{jid}/file/absent.txt")[0] == 404


def test_the_host_check(client: Client) -> None:
    assert client.get("/api/jobs", {"Host": f"evil.example:{client.port}"})[:2] == (
        403,
        {"error": "the studio answers 127.0.0.1 only"},
    )
    assert client.get("/api/jobs", {"Host": f"localhost:{client.port}"})[0] == 200
    assert client.post("/api/jobs", {"folder": "x"}, {"Host": "127.0.0.2"})[0] == 403


def test_the_body_rules(client: Client) -> None:
    code, body, _ = client.request("POST", "/api/jobs", raw=b'{"folder": "x"}', headers={"Content-Type": "text/plain"})
    assert (code, body["error"]) == (415, "POST bodies are application/json (a cross-site form cannot send that)")
    assert client.request("POST", "/api/nothing", raw=b"", headers={})[0] == 415  # the body rules come before the route
    assert client.request("POST", "/api/jobs", raw=b"{nope", headers={"Content-Type": "application/json"})[0] == 400
    assert client.request("POST", "/api/jobs", raw=b"[1]", headers={"Content-Type": "application/json"})[1] == {
        "error": "the body is a JSON object"
    }
    conn = http.client.HTTPConnection("127.0.0.1", client.port, timeout=10)
    conn.putrequest("POST", "/api/jobs", skip_host=True)
    conn.putheader("Host", f"127.0.0.1:{client.port}")
    conn.putheader("Content-Type", "application/json")
    conn.putheader("Content-Length", str(2 * 1024 * 1024 + 1))
    conn.endheaders()
    r = conn.getresponse()
    assert (r.status, r.read()) == (413, b'{"error": "the body is above 2 MB"}')
    conn.close()


def test_the_page_gate_over_http(client: Client, stills: Path) -> None:
    jid = rendered_job(client, stills)
    code, body, _ = client.post(f"/api/jobs/{jid}/page", {"title": "round one"})
    assert code == 409 and body["refused"] == ["c1"] and body["error"].startswith("the page is refused: c1 (unjudged")
    code, body, _ = client.post(f"/api/jobs/{jid}/page", {"title": "round one", "override": True})
    assert code == 202 and body["override"].startswith("Override: built on his word with c1")
    assert poll(client, jid, body["record"])["state"] == "done"
    deadline = time.time() + 10
    while not client.get(f"/api/jobs/{jid}")[1]["rounds"] and time.time() < deadline:
        time.sleep(0.05)
    view = client.get(f"/api/jobs/{jid}")[1]
    assert view["rounds"][0]["override"] == body["override"]
    assert view["page"]["exists"] is True
    page = client.get(f"/api/jobs/{jid}/file/index.html")[1].decode()
    assert body["override"] in page
    code, rnd, _ = client.post(f"/api/jobs/{jid}/picks", {"text": "  c1 is fine, keep it  "})
    assert code == 200 and rnd["grade"]["text"] == "c1 is fine, keep it" and rnd["grade"]["page_md5"] == rnd["page_md5"]
    assert client.post(f"/api/jobs/{jid}/picks", {"round": "x", "text": "t"})[:2] == (
        400,
        {"error": "round is a number"},
    )
    assert client.post(f"/api/jobs/{jid}/picks", {"text": "  "})[0] == 400
    assert client.post(f"/api/jobs/{jid}/picks", {"round": 9, "text": "t"})[0] == 404
    code, body, _ = client.post(f"/api/jobs/{jid}/stages/page/run", {"knobs": {}})
    assert code == 409 and "the review gate" in body["error"]


def test_marks_requests_and_plans_over_http(client: Client, stills: Path) -> None:
    jid = rendered_job(client, stills)
    code, mark, _ = client.post(f"/api/jobs/{jid}/frames/mark", {"name": "c1", "frame": 3, "note": "the edge"})
    assert code == 201 and (mark["frame"], mark["note"]) == (3, "the edge")
    assert client.post(f"/api/jobs/{jid}/frames/mark", {"name": "c1", "frame": 9})[0] == 400
    assert client.post(f"/api/jobs/{jid}/frames/mark", {"name": "c1", "frame": None})[:2] == (
        400,
        {"error": "frame is a number"},
    )
    code, req, _ = client.post(f"/api/jobs/{jid}/requests/skeptic", {"brief": "look at the edge"})
    assert code == 201 and req["name"].startswith("skeptic_")
    assert client.post(f"/api/jobs/{jid}/requests/evil", {})[0] == 400
    assert client.post(f"/api/jobs/{jid}/requests/Evil", {})[:2] == (404, {"error": "no such route"})
    code, opened, _ = client.get("/api/requests")
    assert code == 200 and [r["name"] for r in opened] == [req["name"]]
    code, frozen, _ = client.get("/api/plans/frozen/tiny_a1")
    assert code == 200 and frozen["seq"] == "tiny"
    frozen["timeline"][1]["n"] = 3
    code, saved, _ = client.post(
        f"/api/jobs/{jid}/plans", {"name": "tiny_v2", "plan": frozen, "from": "frozen:tiny_a1", "words": "one more"}
    )
    assert code == 201 and saved["changes"] == [{"path": "/timeline/1/n", "old": 2, "new": 3}]
    code, plan, _ = client.get(f"/api/jobs/{jid}/plans/tiny_v2")
    assert code == 200 and plan["provenance"]["words"] == "one more"
    assert client.post(f"/api/jobs/{jid}/plans", {"name": "tiny_v2", "plan": frozen})[0] == 409
    assert client.get("/api/plans/frozen/absent")[0] == 404


def test_cancel_over_http(client: Client, stills: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    jid = new_job(client, stills)
    assert run_stage(client, jid, "registration", {})["state"] == "done"
    monkeypatch.setenv("FAKE_SLOW", "render=30")
    code, body, _ = client.post(
        f"/api/jobs/{jid}/stages/render/run", {"knobs": {"plan": "frozen:tiny_a1", "name": "s", "draft": 480}}
    )
    assert code == 202
    code, rec, _ = client.post(f"/api/jobs/{jid}/stages/{body['record']}/cancel")
    assert code == 200 and rec["state"] == "cancelled" and rec["reason"] == "cancelled by you"
    code, err, _ = client.post(f"/api/jobs/{jid}/stages/{body['record']}/cancel")
    assert code == 409 and err["error"].endswith("is cancelled, not running")


def test_unknown_routes_and_ids(client: Client, stills: Path) -> None:
    jid = new_job(client, stills)
    assert client.get("/api/nothing")[:2] == (404, {"error": "no such route"})
    assert client.get(f"/api/jobs/{jid}/nothing")[:2] == (404, {"error": "no such route"})
    assert client.get("/api/jobs/no.such.job/nothing")[:2] == (404, {"error": "no job no.such.job"})
    assert client.get("/api/jobs/bad%id")[0] == 400
    assert client.post(f"/api/jobs/{jid}/nothing")[:2] == (404, {"error": "no such route"})
    assert client.post("/api/nothing")[:2] == (404, {"error": "no such route"})
    assert client.get(f"/api/jobs/{jid}/stages/../x")[0] == 404
    assert client.get(f"/api/jobs/{jid}/stages/norecord")[:2] == (404, {"error": "no record norecord"})
    assert client.post(f"/api/jobs/{jid}/stages/warp/run", {})[0] == 404


def test_the_server_binds_127_0_0_1_only(app: App) -> None:
    httpd = StudioServer(app)
    try:
        assert httpd.server_address[0] == "127.0.0.1"
    finally:
        httpd.server_close()


def test_models_route(client: Client) -> None:
    code, ms, _ = client.get("/api/models")
    # the four models, then the director flow's layer tables and mattes (none in the tmp root; builder D, 2026-11-05)
    names = ["reveal matcher", "depth model", "RIFE", "faces (YuNet)", "layer tables", "mattes"]
    assert code == 200 and [m["name"] for m in ms] == names


def test_every_route_in_the_table_is_hit(client: Client, stills: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """One walk over the whole grammar, so the coverage holds even when this test runs alone."""
    for path in (
        "/",
        "/favicon.ico",
        "/static/js/core.js",
        "/api/registry",
        "/api/jobs",
        "/api/requests",
        "/api/models",
        "/api/plans/frozen/tiny_a1",
    ):
        assert client.get(path)[0] in (200, 204), path
    jid = rendered_job(client, stills)
    rec = client.get(f"/api/jobs/{jid}")[1]["stages"][1]["latest"]
    gets: list[tuple[str, Any]] = [
        (f"/api/jobs/{jid}", 200),
        (f"/api/jobs/{jid}/stages/{rec}", 200),
        (f"/api/jobs/{jid}/file/job.json", 200),
        (f"/api/jobs/{jid}/thumb/still/0", 200),
        (f"/api/jobs/{jid}/thumb/render/full/c1", 200),
        (f"/api/jobs/{jid}/render/full/c1", 200),
        (f"/api/jobs/{jid}/render/full/c1/frame/0", 200),
        (f"/api/jobs/{jid}/nope", 404),
    ]
    for path, code in gets:
        assert client.get(path)[0] == code, path
    frozen = client.get("/api/plans/frozen/tiny_a1")[1]
    assert client.post(f"/api/jobs/{jid}/plans", {"name": "walk", "plan": frozen})[0] == 201
    assert client.get(f"/api/jobs/{jid}/plans/walk")[0] == 200
    assert client.post(f"/api/jobs/{jid}/requests/skeptic", {})[0] == 201
    assert client.post(f"/api/jobs/{jid}/frames/mark", {"name": "c1", "frame": 0})[0] == 201
    code, page, _ = client.post(f"/api/jobs/{jid}/page", {"override": True})
    assert code == 202 and poll(client, jid, page["record"])["state"] == "done"
    deadline = time.time() + 10
    while client.post(f"/api/jobs/{jid}/picks", {"text": "fine"})[0] != 200 and time.time() < deadline:
        time.sleep(0.05)
    monkeypatch.setenv("FAKE_SLOW", "render=30")
    code, slow, _ = client.post(
        f"/api/jobs/{jid}/stages/render/run", {"knobs": {"plan": "frozen:tiny_a1", "name": "w", "draft": 480}}
    )
    assert code == 202
    assert client.post(f"/api/jobs/{jid}/stages/{slow['record']}/cancel")[0] == 200
    assert client.post(f"/api/jobs/{jid}/nope")[0] == 404
    missing = sorted(r.name for r in routes.CORE if r.name not in HITS)
    assert not missing, f"routes no test reaches: {missing}"
    # the 26 shared rows; each flow's list is walked and counted in its own test file (tests/test_pair_flow.py,
    # tests/test_director_flow.py), with a spy of its own: this file's spy sees this file's requests only. Mutation:
    # a flow's row spliced after the fallbacks (it then never answers), or a shared row dropped by the split, turns
    # this red.
    assert len(routes.CORE) == 26 and len(routes.FALLBACKS) == 2
    spliced = [r for r in routes.CORE if r not in routes.FALLBACKS] + routes_pair.ROUTES + routes_director.ROUTES
    assert spliced + routes.FALLBACKS == routes.ROUTES
    assert routes.ROUTES[-2:] == routes.FALLBACKS and {r.method for r in routes.FALLBACKS} == {"GET", "POST"}


# ---------------------------------------------------------------- phase B's slice: the jobs of the other flows


def test_a_pair_jobs_folder_keeps_the_rail_and_its_view_answering(
    client: Client, settings: Settings, stills: Path, fixture_pair: str
) -> None:
    """A job.json without `seq` made GET /api/jobs answer 500 for every job (b_seams_research.md, key fact 1); every
    creator writes it. Mutation: job_row reading a loop-only key of every job, or a pair job's view raising, turns
    this red."""
    jid = new_job(client, stills)
    pair = create_pair_job(settings, fixture=fixture_pair)
    director = create_director_job(settings, fixture_pair)
    code, rows, _ = client.get("/api/jobs")
    assert code == 200 and [r["id"] for r in rows] == [jid, pair["id"], director["id"]]
    assert [(r["flow"], r["seq"]) for r in rows] == [("loop", "tiny"), ("pair", "tiny_1"), ("director", "tiny_1")]
    for j in (pair, director):
        code, v, _ = client.get(f"/api/jobs/{j['id']}")
        assert code == 200 and v["job"] == j, j["flow"]
        assert [s["name"] for s in v["stages"]] == stage_order(j["flow"])  # empty in the slice; the flow's own later


def test_post_jobs_refuses_a_flow_that_is_not_enabled_and_passes_its_fields(
    client: Client, fixture_pair: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The route passes fixture, a, b and pair to create_job. The test sets the enabled flows itself, so it holds
    whichever flows the registry enables. Mutation: post_job dropping `fixture` (the enabled pair flow then answers
    400 "needs a fixture pair's name") turns this red."""
    monkeypatch.setattr(store, "FLOWS", {"loop": ALL_FLOWS["loop"]})
    code, body, _ = client.post("/api/jobs", {"flow": "pair", "fixture": fixture_pair})
    assert (code, body["error"]) == (
        400,
        "the flow is one of ['loop'] (pair and director are registered but not built yet)",
    )
    monkeypatch.setattr(store, "FLOWS", dict(ALL_FLOWS))
    code, body, _ = client.post("/api/jobs", {"flow": "pair", "fixture": fixture_pair})
    assert code == 201 and (body["job"]["flow"], body["job"]["fixture"]) == ("pair", fixture_pair)
    a, b = f"fixtures/{fixture_pair}_S.jpg", f"fixtures/{fixture_pair}_F.jpg"
    code, body, _ = client.post("/api/jobs", {"flow": "pair", "a": a, "b": b, "seq": "two"})
    assert code == 201 and body["job"]["seq"] == "two"
    code, body, _ = client.post("/api/jobs", {"flow": "director", "pair": fixture_pair})
    assert code == 201 and body["job"]["pair"] == fixture_pair
    code, body, _ = client.post("/api/jobs", {"flow": "director", "pair": "mismatch_7"})
    assert code == 400 and "no plan under scripts/research/plans/" in body["error"]


def test_the_file_route_serves_the_read_only_bases_of_a_director_job(
    client: Client, settings: Settings, fixture_pair: str
) -> None:
    """fixtures/, layers/, mattes/ and the helpers a job names, one check per base, each with its refusals. Mutation:
    serving any repo path (a helper the job does not name), or a base tried before the job's own folders (a loop
    job's seq named "fixtures" then loses its renders), turns this red."""
    j = create_director_job(settings, fixture_pair)
    jid = j["id"]
    base = f"/api/jobs/{jid}/file/"
    cases = [
        ("fixtures/tiny_1_S.jpg", settings.fixtures / "tiny_1_S.jpg"),
        ("layers/tiny_1_S/layers.json", settings.layers_dir / "tiny_1_S" / "layers.json"),
        ("mattes/tiny_1_S/el_1.png", settings.mattes_dir / "tiny_1_S" / "el_1.png"),
        (HELPER, settings.root / HELPER),
    ]
    for path, f in cases:
        code, data, _ = client.get(base + path)
        assert code == 200, path
        if path.endswith(".json"):  # a JSON file comes back parsed
            assert data == json.loads(f.read_text()), path
        else:
            assert data == f.read_bytes(), path
    (settings.root / "benchmarks/runs/2026-10-17/keyframes/out/k2.png").write_bytes(b"not named")
    for path, code in (
        ("benchmarks/runs/2026-10-17/keyframes/out/k2.png", 404),  # a helper the job's plans do not name
        ("fixtures/../reveal.py", 403),
        ("layers/../../AGENTS.md", 403),
        ("mattes/tiny_1_F/el_1.png", 404),  # no such matte
        ("fixtures/", 404),
        ("job.json", 200),  # the job folder itself, as before
        ("raw/tiny_1/A.jpg", 404),  # a link out of the job folder is never served through it (the loop's rule)
    ):
        assert client.get(base + path)[0] == code, path
