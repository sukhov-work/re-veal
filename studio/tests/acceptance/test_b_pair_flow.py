"""The pair flow's acceptance (phase B, builder P) on the fixture pair mismatch_3 (a crowded bar and a lounge group,
fixtures/MANIFEST.md), through a `reveal-studio serve` subprocess on a free port with a tmp lock against the real tree.

It makes one new pair job under benchmarks/runs/<today>/studio/ (gitignored) and writes into no other job: the
relation twice (class B, saliency-panzoom, 0 inliers, a median displacement of 24.71 px, the mp4 md5
25c0f77ce05ce8ed53580bb36da24acb and the strip md5 8bd77a4dbbd9763ccd1fd95ca9cdddef, b_pair_research.md Part 1; the
rerun reproduces both and says unchanged), Reveal's verdict refused with its FAILED: reason, a 480 draft of the morph
preset at 1 s (the relation's own spec, so its mp4 md5 is the relation's), a full render at 1920 and a second one under
another name with the same md5 (harness check 33), the render view's frames, tags, step series and bars, a skeptic
request the test answers itself, the page behind the gate with an override, a grade in the picks shape, and a server
restart during a render that the new server re-attaches. The acceptance driver of phase B added the fixture list and
the request's listing by `reveal-studio requests` before and after its answer (b_acceptance.md, 2026-11-05). Every
`serve` start reconciles the running records of every job of the tree (backlog T88), so before each start the test
waits until no other job has a running record (it skips after 5 minutes).

It skips when the repo root, the main venv's python, transitions.py at md5 7ef5dcae070c223e360c9c2e533df6c1 (the
tool the recorded md5s belong to), reveal.py or the two photos at their recorded sha256s are absent. Run it alone:
`studio/.venv/bin/pytest tests/acceptance/test_b_pair_flow.py -m acceptance -s -q`. The page's own checks (the panels,
the fixture picker, the viewer's playback, the hints) stay in the drive; they need a browser.
"""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from reveal_studio.config import ConfigError, Settings, resolve_settings
from reveal_studio.fs import Json, md5_file, now_iso, read_json, sha256_file, write_json

from ..conftest import Client, free_port
from .test_a1_loop_flow import Server, alive, foreign_running, md5s_of, poll, run, start, wait_quiet

pytestmark = pytest.mark.acceptance

PAIR = "mismatch_3"
PHOTOS = {
    "fixtures/mismatch_3_S.jpg": "b40d042bc390244796ecee27a9164529a7713533df0963bb6765080e444e27c9",
    "fixtures/mismatch_3_F.jpg": "bd04d1e782ce2f842e912203f513019d1304deb90d6af3a96d35d02a41d617ed",
}
TRANSITIONS_MD5 = "7ef5dcae070c223e360c9c2e533df6c1"
RELATION_MP4 = "25c0f77ce05ce8ed53580bb36da24acb"
RELATION_STRIP = "8bd77a4dbbd9763ccd1fd95ca9cdddef"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """The real tree's settings on a free port with a tmp lock; skips with the reason when an input is absent."""
    try:
        s = resolve_settings(port=free_port(), lock=tmp_path / "studio.lock", open_browser=False)
    except ConfigError as e:
        pytest.skip(f"no repo root: {e}")
    if not s.python.exists():
        pytest.skip(f"the main venv's python {s.python} is absent (./setup.sh at the root)")
    if not s.transitions.is_file() or md5_file(s.transitions) != TRANSITIONS_MD5:
        pytest.skip(f"transitions.py is absent or not at md5 {TRANSITIONS_MD5}, the tool the recorded md5s belong to")
    if not s.reveal.is_file():
        pytest.skip("reveal.py is absent")
    for rel_path, sha in PHOTOS.items():
        p = s.root / rel_path
        if not p.is_file() or sha256_file(p) != sha:
            pytest.skip(f"{rel_path} is absent or not the photo the recorded values belong to")
    return s


def out_md5(rec: Json, name: str) -> str:
    return md5s_of(rec)[name]


def test_the_pair_flow_on_mismatch_3(settings: Settings, tmp_path: Path) -> None:
    s = settings
    client = Client(s.port)
    photos = [s.root / p for p in PHOTOS]
    mtimes = [p.stat().st_mtime_ns for p in photos]
    fixtures_before = sorted(p.name for p in s.fixtures.iterdir())
    d: Path | None = None
    lines: list[str] = []
    wait_quiet(s, None)
    server = Server(s, tmp_path / "server.log")
    try:
        server.start()
        code, body, _ = client.post("/api/jobs", {"flow": "pair", "fixture": PAIR})
        assert code == 201, body
        jid, job = str(body["id"]), body["job"]
        d = s.root / job["root"]
        assert (job["seq"], [i["sha256"] for i in job["inputs"]]) == (PAIR, list(PHOTOS.values()))
        assert [os.readlink(s.root / i["link"]) for i in job["inputs"]] == [str(p) for p in photos]  # linked
        lines.append(f"job {jid}: A and B linked under raw/{PAIR}/")

        # the fixture picker's list (GET /api/fixtures, b_acceptance.md, 2026-11-05): every <name>_S.<ext> with a
        # <name>_F.<ext> under fixtures/, whatever the two extensions (mismatch_7 is .jpg and .png, the fabra pairs
        # .heic); red if the scan reads one extension only or drops a pair
        code, fx, _ = client.get("/api/fixtures")
        on_disk = {q.name.rsplit("_S.", 1)[0] for q in s.fixtures.glob("*_S.*")} & {
            q.name.rsplit("_F.", 1)[0] for q in s.fixtures.glob("*_F.*")
        }
        assert code == 200 and {f["name"] for f in fx} == on_disk, (code, sorted(on_disk))
        mine = next(f for f in fx if f["name"] == PAIR)
        assert (mine["A"]["name"], mine["B"]["name"]) == (f"{PAIR}_S.jpg", f"{PAIR}_F.jpg")
        assert (mine["A"]["bytes"], mine["B"]["bytes"]) == tuple(p.stat().st_size for p in photos)

        # the relation; red if its argv drifts from --max-long 480 --seconds 1, the view reads another file, or the
        # runner hashes another script than the record's argv[1]
        rec, _ = run(client, jid, "relation", {})
        assert rec["state"] == "done", rec.get("reason")
        assert rec["argv"][1:3] == ["transitions.py", "pair"] and rec["argv"][-4:] == [
            "--max-long",
            "480",
            "--seconds",
            "1",
        ]
        assert (out_md5(rec, "transition.mp4"), out_md5(rec, "strip.jpg")) == (RELATION_MP4, RELATION_STRIP)
        assert rec["script_md5"] == TRANSITIONS_MD5
        code, v, _ = client.get(f"/api/jobs/{jid}/relation")
        p = v["report"]
        assert code == 200 and (p["class"], p["method"], p["sparse_inliers"], p["median_disp_px"]) == (
            "B",
            "saliency-panzoom",
            0,
            24.71,
        )
        assert (p["canvas"], v["n_frames"], v["md5_mp4"], v["md5_strip"]) == (
            [480, 360],
            30,
            RELATION_MP4,
            RELATION_STRIP,
        )
        first = rec
        lines.append(f"relation {rec['id']} {rec['wall_s']} s: class B, 0 inliers, 24.71 px, mp4 {RELATION_MP4}")

        # the rerun reproduces both md5s and says unchanged; red if the identity names report.json (its clock keys
        # differ run to run) or the run is not deterministic
        rec, _ = run(client, jid, "relation", {})
        assert rec["state"] == "done", rec.get("reason")
        assert (out_md5(rec, "transition.mp4"), out_md5(rec, "strip.jpg")) == (RELATION_MP4, RELATION_STRIP)
        assert rec.get("unchanged_from") == first["id"]
        assert out_md5(rec, "report.json") != out_md5(first, "report.json")
        for i in (0, 29):  # A and B from the relation's decoded frames: cv2 reads no HEIC, so the studio shows these
            code, jpg, _ = client.get(f"/api/jobs/{jid}/relation/frame/{i}")
            assert code == 200 and jpg[:2] == b"\xff\xd8", i
        lines.append(f"relation rerun {rec['id']} {rec['wall_s']} s: the same two md5s, unchanged from {first['id']}")

        # Reveal's verdict on demand: refused with its FAILED: line and no metrics; red if the runner reads exit 2
        # with a FAILED: line as a failure, or the view shows metrics left by no run
        rec, _ = run(client, jid, "verdict", {})
        assert rec["state"] == "refused" and str(rec["reason"]).startswith("FAILED:"), rec
        code, v, _ = client.get(f"/api/jobs/{jid}/verdict")
        assert code == 200 and (v["state"], v["reason"], v["metrics"]) == ("refused", rec["reason"], None)
        assert not (d / "verdict" / "metrics.json").exists()
        lines.append(f"verdict {rec['id']} {rec['wall_s']} s: refused, {rec['reason']}")

        # a 480 draft of the morph preset at 1 s: the relation's own spec, so the same mp4; red if the render's argv
        # adds a second --max-long or a knob's default drifts from the CLI's
        rec, _ = run(client, jid, "render", {"name": "morph480", "draft": 480, "preset": "morph", "seconds": 1})
        assert rec["state"] == "done", rec.get("reason")
        assert rec["argv"].count("--max-long") == 1 and rec["argv"][rec["argv"].index("--max-long") + 1] == "480"
        assert (out_md5(rec, "transition.mp4"), out_md5(rec, "strip.jpg")) == (RELATION_MP4, RELATION_STRIP)
        assert (d / "drafts" / PAIR / "morph480" / "report.json").is_file()
        lines.append(f"draft morph480 {rec['id']} {rec['wall_s']} s: mp4 {RELATION_MP4}, the relation's")

        # the full render at 1920 and a second one under another name: one md5 (harness check 33); red if the full
        # render's long edge is not max_long's, or a finished render can be overwritten
        rec, _ = run(client, jid, "render", {"name": "morph1920", "preset": "morph", "seconds": 1})
        assert rec["state"] == "done", rec.get("reason")
        full_md5 = out_md5(rec, "transition.mp4")
        rep = read_json(d / PAIR / "morph1920" / "report.json")
        assert (rep["canvas"], rep["n_frames"], rep["class"]) == ([1920, 1440], 30, "B")
        files = {q.name: md5_file(q) for q in (d / PAIR / "morph1920").iterdir()}
        rec2, _ = run(client, jid, "render", {"name": "morph1920b", "preset": "morph", "seconds": 1})
        assert rec2["state"] == "done", rec2.get("reason")
        assert out_md5(rec2, "transition.mp4") == full_md5
        assert {q.name: md5_file(q) for q in (d / PAIR / "morph1920").iterdir()} == files
        code, body, _ = client.post(f"/api/jobs/{jid}/stages/render/run", {"knobs": {"name": "morph1920"}})
        assert code == 409 and "never overwritten" in body["error"]
        lines.append(f"full morph1920 {rec['id']} {rec['wall_s']} s and morph1920b {rec2['wall_s']} s: mp4 {full_md5}")

        # the render view: the spec's fps, the tags, the decoded steps, the decode checks and the bars; red if the
        # view falls back to the loop's (25 fps, no tags) or a bar's verdict flips
        code, r, _ = client.get(f"/api/jobs/{jid}/render/full/morph1920")
        assert code == 200 and (r["fps"], r["frames"], r["frames_available"], len(r["steps"])) == (30.0, 30, 30, 29)
        tags = [t["tag"] for t in r["frames_tags"]]
        assert tags == ["photo"] + ["blend"] * 28 + ["photo"]
        assert {c["key"]: c["verdict"] for c in r["decode"]} == dict.fromkeys(
            ("frames", "size", "fps", "darkest"), "within"
        )
        bars = {b["key"]: b for b in r["bars"]}
        assert bars["endpoint.first_vs_A"]["verdict"] == bars["endpoint.last_vs_B"]["verdict"] == "within"
        assert bars["flicker.edge_ratio"]["verdict"] == "within" and r["class_differs"] is False
        fl = r["flicker"]
        lines.append(
            f"render view: 30 fps, decoded step max {max(r['steps']):.4f} against the report's flicker max"
            f" {fl['max']:.4f}; edge ratio {fl['edge_ratio']:.3f}"
        )

        # a skeptic request, written and answered by the test itself (an empty candidates map: answered, no verdict);
        # red if the request drops the crops or the answer file stops closing it
        crops = [
            {"candidate": n, "frames": [1, 28, 14], "pairs": [[0, 1], [28, 29]]} for n in ("morph1920", "morph1920b")
        ]
        code, req, _ = client.post(
            f"/api/jobs/{jid}/requests/skeptic",
            {"brief": "B pair acceptance test", "candidates": ["morph1920", "morph1920b"], "crops": crops},
        )
        assert code == 201, req
        assert read_json(s.root / req["file"])["crops"] == crops
        # the request is listed by `reveal-studio requests` (STUDIO.md §9 row "B (continued)", b_acceptance.md) until
        # its answer exists; red if the CLI's scan of open requests skips a pair job
        cli = [sys.executable, "-m", "reveal_studio", "requests", "--root", str(s.root)]
        out = subprocess.run(cli, capture_output=True, text=True, timeout=60).stdout
        assert any(req["file"] in ln for ln in out.splitlines()), out
        write_json(
            d / "answers" / req["name"],
            {"at": now_iso(), "candidates": {}, "note": "the acceptance test answered its own request; nothing judged"},
        )
        assert req["name"] not in [q["name"] for q in client.get("/api/requests")[1]]
        out = subprocess.run(cli, capture_output=True, text=True, timeout=60).stdout
        assert not any(req["file"] in ln for ln in out.splitlines()), out
        lines.append(f"skeptic {req['name']}: written with the crops and answered by the test")

        # the page behind the gate with an override; red if the builtin page skips the gate, the override leaves the
        # footer, or the round opens on another file than the page
        code, body, _ = client.post(f"/api/jobs/{jid}/page", {})
        assert code == 409 and sorted(body["refused"]) == ["morph1920", "morph1920b"], body
        assert not (d / "index.html").exists()
        footer = "B pair acceptance test"
        code, body, _ = client.post(
            f"/api/jobs/{jid}/page", {"override": True, "footer": footer, "variants": ["morph1920b", "morph1920"]}
        )
        assert code == 202 and body["state"] == "done", body
        html = (d / "index.html").read_text()
        rnd = read_json(d / "rounds" / "1" / "round.json")
        assert (rnd["record"], rnd["candidates"], rnd["override"]) == (
            body["record"],
            ["morph1920b", "morph1920"],
            body["override"],
        )
        assert rnd["page_md5"] == md5_file(d / "index.html") == (d / "page.md5").read_text().strip()
        assert footer in html and body["override"] in html and f"{PAIR}/morph1920/transition.mp4" in html
        assert html.index("id='morph1920b'") < html.index("id='morph1920'")
        assert (d / "page_A.jpg").is_file() and (d / "page_B.jpg").is_file()
        lines.append(f"page {body['record']}: round 1 on md5 {rnd['page_md5']}, the override in the footer")

        # a grade in the picks shape; red if the shape check is skipped or the round's grade loses the page md5
        props = {"one_picture": False, "transforms": False, "not_invented": True}
        picks = {
            "date": now_iso(),
            "page": f"{jid} round 1",
            "best": {PAIR: "none"},
            "clips": {
                "morph1920": {"acceptable": False, "note": "the acceptance test's grade", "props": props},
                "morph1920b": {"acceptable": False, "note": "the acceptance test's grade", "props": props},
            },
        }
        code, r, _ = client.post(f"/api/jobs/{jid}/picks", {"round": 1, "picks": picks, "text": footer + ": a grade"})
        assert code == 200 and r["grade"]["page_md5"] == rnd["page_md5"], r
        assert read_json(d / r["grade"]["picks"]) == picks
        lines.append(f"grade: {r['grade']['picks']}")

        # a restart during a render (a 3 s clip at 1920): the child outlives the server and the new one re-attaches
        # it; red if the child dies with the server or reconcile marks a live pair render lost
        wait_quiet(s, d)
        rid = start(client, jid, "render", {"name": "restart3s", "preset": "morph", "seconds": 3})
        rec_path = d / "stages" / rid / "stage.json"
        child = int(read_json(rec_path)["pid"])
        assert read_json(rec_path)["state"] == "running" and alive(child)
        server.stop()
        assert alive(child), "the render died with the server (it should run in its own session)"
        assert read_json(rec_path)["state"] == "running"
        if busy := foreign_running(s, d):
            pytest.skip(f"{busy} started in another job during the restart: a serve start here would reconcile it")
        server = Server(s, tmp_path / "server2.log")
        server.start()
        attached = f"{rid}: pid {child} still runs after a restart; re-attached"
        assert attached in server.text(), f"no re-attach (did the render end before the restart?): {server.text()}"
        rec, _ = poll(client, jid, rid)
        assert rec["state"] == "done" and "finished after a restart" in rec["note"], rec
        lines.append(
            f"restart3s {rec['id']} {rec['wall_s']} s: re-attached, done, mp4 {out_md5(rec, 'transition.mp4')}"
        )

        # the originals: never modified, nothing new under fixtures/
        assert [q.stat().st_mtime_ns for q in photos] == mtimes
        assert [sha256_file(q) for q in photos] == list(PHOTOS.values())
        assert sorted(q.name for q in s.fixtures.iterdir()) == fixtures_before
    finally:
        # no stage of this job outlives the test or stays `running` on disk (the A2 test's rule)
        if d is not None:
            for sj in (d / "stages").glob("*/stage.json"):
                rr: Any = read_json(sj) or {}
                if rr.get("state") not in ("running", "cancelling"):
                    continue
                with contextlib.suppress(OSError):
                    client.post(f"/api/jobs/{d.name}/stages/{rr['id']}/cancel")
                if (read_json(sj) or {}).get("state") in ("running", "cancelling") and rr.get("pid"):
                    with contextlib.suppress(OSError):
                        os.killpg(int(rr["pid"]), signal.SIGTERM)
        server.stop()
    print(f"\njob {d}")
    for ln in lines:
        print(f"  {ln}")
