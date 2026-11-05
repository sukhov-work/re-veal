"""The phase B acceptance of the director flow (STUDIO.md §9 row B; b_director_research.md §7; both anchors of
b_design.md decision 1), through a `reveal-studio serve` subprocess on a free port with a tmp lock against the real
tree.

One new job of the pair mismatch_3 under benchmarks/runs/<today>/studio/ (gitignored): the resolve of
frozen:mismatch_3_r12 c1 at 1920 px; the plan view's knob map; three 480 px drafts (the two knobs of the §9 row at
md5 01b3cf3c…, the workbench's four knobs at md5 5b3ee379…, and a re-render of the first from its record's knobs under
a new tag); the measures, the series and the decoded steps of the first; a marked frame; a full 1920 render across a
server restart; the page through director_page.py behind the gate with an override and a rebuild; a grade in the picks
shape. About 3 minutes on this laptop; it writes into no other job. Every `serve` start reconciles the running records
of every job of the tree (backlog T88), so the test waits until no other job has a running record before its start and
before the full render, and skips at the restart when another job's record started meanwhile.

It skips when the main venv's python, the renderer at md5 05cd6e1d…, the pair's photos at their sha256s, the layer
tables, the mattes, the depth model's manifest or the plan's keyframe are absent. Run it alone:
`make -C studio acceptance` runs it beside the loop's two, or
`studio/.venv/bin/pytest tests/acceptance/test_b_director_flow.py -m acceptance -s -q` from studio/.
"""

from __future__ import annotations

import contextlib
import os
import signal
import struct
import time
from pathlib import Path
from typing import Any

import pytest

from reveal_studio.config import ConfigError, Settings, resolve_settings
from reveal_studio.fs import Json, md5_file, read_json, sha256_file

from ..conftest import Client, free_port
from .test_a1_loop_flow import TERMINAL, Server, alive, foreign_running, poll, wait_quiet

pytestmark = pytest.mark.acceptance

PAIR, STEM, CONCEPT = "mismatch_3", "mismatch_3_r12", "c1"
PLAN = f"frozen:{STEM}"
PLAN_SHA256 = "adec1345aeb6cc96100b29c63a5e440c95ce37cadc720780207b7bc47a9e5aaa"
RENDERER_MD5 = "05cd6e1d95adbb3c83313b98b3f43815"
TRANSITIONS_MD5 = "7ef5dcae070c223e360c9c2e533df6c1"
PHOTO_SHA256 = {
    "A": "b40d042bc390244796ecee27a9164529a7713533df0963bb6765080e444e27c9",
    "B": "bd04d1e782ce2f842e912203f513019d1304deb90d6af3a96d35d02a41d617ed",
}
TWO: Json = {"parallax_push": 2, "pane_becomes_view.window": [0.35, 0.97]}
"""The two knobs of the STUDIO.md §9 row B argv (DECISIONS 2026-11-05, eighth line)."""
FOUR: Json = {"cont_feather": 14, "front_margin": 0.3, **TWO}
"""The workbench's four knobs: two pre-filled from the round-12 render, then the §9 row's two (the ninth line)."""
MD5_TWO = "01b3cf3c769ee45e44a73f1ade36a3b6"
MD5_FOUR = "5b3ee379776ae4e8ce2dec4fa3293740"
DRAFT: Json = {"plan": PLAN, "concept": CONCEPT, "draft": 480, "seconds": 3, "fps": 30}
KEYFRAME = "benchmarks/runs/2026-10-17/keyframes_r10/out/r10_m3_pane.png"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """The real tree's settings on a free port with a tmp lock; skips with the reason when an input is absent."""
    try:
        s = resolve_settings(port=free_port(), lock=tmp_path / "studio.lock", open_browser=False)
    except ConfigError as e:
        pytest.skip(f"no repo root: {e}")
    if not s.python.exists():
        pytest.skip(f"the main venv's python {s.python} is absent (./setup.sh at the root)")
    if not s.director_render.is_file() or md5_file(s.director_render) != RENDERER_MD5:
        pytest.skip(f"director_render.py is not at md5 {RENDERER_MD5}: the recorded md5s belong to that renderer")
    for side, suffix in (("A", "S"), ("B", "F")):
        p = s.fixtures / f"{PAIR}_{suffix}.jpg"
        if not p.is_file() or sha256_file(p) != PHOTO_SHA256[side]:
            pytest.skip(f"{p} is absent or not the photo the recorded values belong to")
    for need in (
        s.layers_dir / f"{PAIR}_S" / "layers.npz",
        s.layers_dir / f"{PAIR}_F" / "layers.npz",
        s.mattes_dir / f"{PAIR}_F",
        s.root / "models" / "DEPTH_MANIFEST.json",
        s.root / KEYFRAME,
    ):
        if not need.exists():
            pytest.skip(f"{need} is absent")
    return s


def png_size(p: Path) -> tuple[int, int]:
    """A PNG's width and height from its IHDR chunk."""
    w, h = struct.unpack(">II", p.read_bytes()[16:24])
    return int(w), int(h)


def run_stage(client: Client, jid: str, stage: str, knobs: Json, timeout: float = 600.0) -> tuple[Json, list[Json]]:
    code, body, _ = client.post(f"/api/jobs/{jid}/stages/{stage}/run", {"knobs": knobs})
    assert code == 202, body
    return poll(client, jid, str(body["record"]), timeout)


def md5_of(rec: Json, name: str) -> str:
    return next(str(o["md5"]) for o in rec["outputs"] if Path(o["path"]).name == name)


def newer(marker: Path, roots: list[Path]) -> list[str]:
    """The files under the roots modified after the marker (the `find -newer` sweep of b_director_research.md §7)."""
    t = marker.stat().st_mtime
    out = []
    for r in roots:
        for p in r.rglob("*"):
            if p.is_file() and p.stat().st_mtime > t:
                out.append(str(p))
    return out


def test_the_director_flow_on_mismatch_3(settings: Settings, tmp_path: Path) -> None:
    s = settings
    client = Client(s.port)
    lines: list[str] = []
    frozen = [s.fixtures / f"{PAIR}_S.jpg", s.fixtures / f"{PAIR}_F.jpg", s.director_plans / f"{STEM}.json"]
    before = {str(p): (p.stat().st_mtime_ns, sha256_file(p)) for p in frozen}
    marker = tmp_path / "marker"
    marker.write_text("before the drive")
    time.sleep(0.05)
    sweep = [s.director_plans, s.fixtures, s.layers_dir, s.mattes_dir]  # the whole roots, every pair's files
    d: Path | None = None
    wait_quiet(s, None)
    server = Server(s, tmp_path / "server.log")
    try:
        server.start()
        t0 = time.time()

        # check 1: a job by pair name; red if the import copies a photo, or the matte count counts mattes.json
        jobs_before = len(list(s.runs.glob("*/studio/*/job.json")))
        code, body, _ = client.post("/api/jobs", {"flow": "director", "pair": "mismatch_7"})
        assert code == 400 and len(list(s.runs.glob("*/studio/*/job.json"))) == jobs_before, body
        code, body, _ = client.post("/api/jobs", {"flow": "director", "pair": PAIR})
        assert code == 201, body
        job = body["job"]
        jid = str(body["id"])
        d = (s.root / job["root"]).parent  # the job folder; its root is <job>/run
        assert {i["role"]: i["sha256"] for i in job["inputs"]} == PHOTO_SHA256
        for i in job["inputs"]:
            assert (s.root / i["link"]).is_symlink() and (s.root / i["link"]).resolve() == Path(i["path"]).resolve()
        assert (job["tables"]["A"]["elements"], job["mattes"]["A"]["count"]) == (75, 43)
        assert (job["tables"]["B"]["elements"], job["mattes"]["B"]["count"]) == (56, 51)
        assert job["mattes"]["B"]["missing"] == [9, 19, 24, 26, 32]
        lines.append(f"job {jid}: A 75 elements, 43 mattes; B 56 and 51, missing 9, 19, 24, 26, 32; mismatch_7 400")

        # check 2: the resolve at 1920; red if it writes under run/ or --layers-dir is dropped
        rec, _ = run_stage(client, jid, "resolve", {"plan": PLAN, "concept": CONCEPT})
        assert rec["state"] == "done", rec.get("reason")
        assert rec["wall_s"] < 30, rec["wall_s"]
        out = s.root / rec["out_final"]
        assert out.parent == d / "resolve" and not str(out).startswith(str(d / "run"))
        assert png_size(out / "canvas_A.png") == png_size(out / "canvas_B.png") == (1920, 1440)
        anchors = read_json(out / "anchors.json")
        assert sorted(anchors) == sorted(
            ["pair", "concept", "canvas", "frames", "anchors", "layers", "info", "camera", "renderer_md5"]
        )
        assert (anchors["camera"]["kind"], anchors["anchors"]) == ("homog", {})
        assert anchors["layers"] == [
            {"name": "pane_becomes_view", "by": "keyframe_chain", "window": [0.3, 0.92], "depth": "inside"}
        ]
        fallbacks = anchors["info"]["matte_fallbacks"]
        assert "--layers-dir" in rec["argv"] and "--mattes-dir" in rec["argv"] and "--resolve-only" in rec["argv"]
        lines.append(f"resolve {rec['id']} {rec['wall_s']} s: 1920×1440, camera homog, fallbacks {fallbacks}")

        # check 3: the plan opened; red if the plan stage pre-fills the round-12 knobs or a name form fails to map
        code, pv, _ = client.get(f"/api/plans/director/{STEM}")
        assert code == 200 and pv["sha256"] == PLAN_SHA256
        c1 = next(c for c in pv["concepts"] if c["id"] == CONCEPT)
        knobs = {k["name"]: (k.get("set_key"), k.get("path")) for k in c1["knobs"]}
        assert knobs == {
            "front_per_element": ("front_per_element", []),
            "pane_becomes_view.params.times[0]": ("pane_becomes_view.times", [0]),
            "pane_becomes_view.window[1]": ("pane_becomes_view.window", [1]),
        }
        g = {r["key"]: r for r in c1["globals"]}
        assert g["parallax_push"]["default"] == 2.5 and len(g) == 28
        bars = [b["window"] for b in c1["beats"]] + [c1["end"]["window"]]
        assert bars == [[0.3, 0.92], [0.92, 1.0]]
        assert c1["last_round"]["knobs"] == {"cont_feather": 14, "front_margin": 0.3, "parallax_push": 1.5}
        lines.append(
            "plan: three knobs mapped, parallax_push 2.5 here, two bars; the last round's knobs on request only"
        )

        # check 4: the two-knob draft; red if --progress is dropped or a knob is sent with another value
        rec, seen = run_stage(client, jid, "render", {**DRAFT, "name": "two", "set": TWO})
        assert rec["state"] == "done", rec.get("reason")
        assert seen and (seen[-1]["i"], seen[-1]["n"]) == (89, 90), seen[-3:]
        assert rec["argv"].count("--set") == 2 and "--progress" in rec["argv"]
        name = f"{STEM}_{CONCEPT}-two"
        folder = d / "drafts" / name
        assert rec["out_final"] == str(folder.relative_to(s.root))
        assert md5_of(rec, "transition.mp4") == md5_file(folder / "transition.mp4") == MD5_TWO
        assert rec["script_md5"] == RENDERER_MD5
        assert next(i for i in rec["inputs"] if i["path"] == "transitions.py")["md5"] == TRANSITIONS_MD5
        assert rec["inputs"][0] == {"path": f"scripts/research/plans/{STEM}.json", "sha256": PLAN_SHA256}
        info = read_json(folder / "info.json")
        assert info["renderer_md5"] == RENDERER_MD5 and info["transitions_md5"] == TRANSITIONS_MD5
        lines.append(f"draft two {rec['id']} {rec['wall_s']} s: {MD5_TWO}, {len(seen)} progress values, last 89/90")

        # check 4b: the workbench's four knobs; red if the studio's argv differs from the workbench's record
        rec4, _ = run_stage(client, jid, "render", {**DRAFT, "name": "four", "set": FOUR})
        assert rec4["state"] == "done", rec4.get("reason")
        assert md5_of(rec4, "transition.mp4") == MD5_FOUR and rec4["argv"].count("--set") == 4
        lines.append(f"draft four {rec4['id']} {rec4['wall_s']} s: {MD5_FOUR}")

        # check 5: a re-render from the record's knobs into a new tag; red if a finished render is overwritten
        files = {p.name: md5_file(p) for p in folder.iterdir()}
        code, full_rec, _ = client.get(f"/api/jobs/{jid}/stages/{rec['id']}")
        again_knobs = {**full_rec["knobs"], "name": "two-again"}
        rec5, _ = run_stage(client, jid, "render", again_knobs)
        assert rec5["state"] == "done" and md5_of(rec5, "transition.mp4") == MD5_TWO
        assert {p.name: md5_file(p) for p in folder.iterdir()} == files
        code, body, _ = client.post(f"/api/jobs/{jid}/stages/render/run", {"knobs": again_knobs})
        assert code == 409 and "never overwritten" in body["error"], body
        lines.append(f"re-render {rec5['id']}: {MD5_TWO} again; the first draft's files unchanged; the same tag 409")

        # check 6: the measures shown; red if the view reads measure.json or the decode reads loop.mp4
        code, rv, _ = client.get(f"/api/jobs/{jid}/render/draft/{name}")
        assert code == 200 and rv["fps"] == 30
        m = {x["key"]: x for x in rv["measures"]}
        assert (m["motion_median_px"]["value"], m["motion_pauses"]["value"], m["motion_jumps"]["value"]) == (2.37, 4, 0)
        assert m["b_inside_first"]["value"] == 84
        assert m["residual_edge_max"]["value"] == 0.09647 and m["residual_edge_max"]["past"] is True
        assert m["matte_fallbacks"]["value"] == ["mismatch_3_F:24", "mismatch_3_F:26", "mismatch_3_F:32"]
        sr = rv["series"]
        assert sr["halo"] is None and info["halo"] is None
        assert [len(sr[k]["points"]) for k in ("motion_px", "b_inside", "residual_edges")] == [89, 31, 29]
        steps = [p[1] for p in sr["steps"]["points"]]
        assert len(steps) == 89 and round(steps[0], 2) == 0.27 == info["step_first"]
        lines.append("measures: 2.37 px, 4 pauses, 0 jumps, B first f 84, residual 0.09647 past 0.2 %, halo null")
        lines.append(f"   series 89, 31, 29; decoded steps 89, first {round(steps[0], 2)}; fallbacks 24, 26, 32")

        # check 7: a frame marked; red if the frame bound ignores info.json's frames
        code, mk, _ = client.post(
            f"/api/jobs/{jid}/frames/mark", {"kind": "draft", "name": name, "frame": 47, "note": "the pane"}
        )
        assert code == 201 and mk["md5_mp4"] == MD5_TWO
        assert (d / "owner_frames" / f"draft_{name}_f0047.json").is_file()
        code, _, _ = client.post(f"/api/jobs/{jid}/frames/mark", {"kind": "draft", "name": name, "frame": 90})
        assert code == 400

        # check 9: a full 1920 render across a restart; red if the pid check looks for loop_seq.py
        wait_quiet(s, d)
        code, body, _ = client.post(
            f"/api/jobs/{jid}/stages/render/run", {"knobs": {**DRAFT, "draft": 0, "name": "full", "set": TWO}}
        )
        assert code == 202, body
        rid = str(body["record"])
        deadline = time.time() + 120
        while time.time() < deadline:
            r = client.get(f"/api/jobs/{jid}/stages/{rid}")[1]
            if r.get("progress") or r["state"] in TERMINAL:
                break
            time.sleep(0.3)
        busy = foreign_running(s, d)
        if busy:
            pytest.skip(f"another job's record started before the restart: {busy}")
        server.stop()
        r = read_json(d / "stages" / rid / "stage.json")
        assert r["state"] == "running" and alive(int(r["pid"])), r["state"]
        server.start()
        deadline = time.time() + 300
        while time.time() < deadline:
            r = client.get(f"/api/jobs/{jid}/stages/{rid}")[1]
            if r["state"] == "running":
                assert alive(int(r["pid"])), "a running record whose child is gone"
            if r["state"] in TERMINAL and (r["state"] != "done" or r.get("outputs")):
                break
            time.sleep(0.5)
        assert r["state"] == "done", (r["state"], r.get("reason"))
        md5_full = md5_of(r, "transition.mp4")
        lines.append(f"full {rid} {r['wall_s']} s across a restart: done, {md5_full}; {r.get('note', '')}")

        # the page behind the gate with an override, then a rebuild that keeps the previous page beside its record
        code, body, _ = client.post(f"/api/jobs/{jid}/page", {})
        assert code == 409 and body["refused"] == [f"{STEM}_{CONCEPT}-full"], body
        code, body, _ = client.post(f"/api/jobs/{jid}/page", {"override": True})
        assert code == 202, body
        page, _ = poll(client, jid, str(body["record"]))
        assert page["state"] == "done", page.get("reason")
        page_md5 = md5_file(d / "run" / "index.html")
        html = (d / "run" / "index.html").read_text()
        assert body["override"] in html and f"{STEM}_{CONCEPT}-full" in html
        rnd = read_json(d / "rounds" / "1" / "round.json")
        assert rnd["page_md5"] == page_md5 and rnd["candidates"] == [f"{STEM}_{CONCEPT}-full"]
        lines.append(f"page {page['id']}: md5 {page_md5}, round 1 on the override")

        # check 8: a grade in the picks shape; red if the key checks of director_ui.py:695-707 are dropped
        clip = {
            "acceptable": False,
            "note": "the drive's note",
            "props": {"one_picture": True, "transforms": True, "not_invented": False},
        }
        picks = {
            "date": "2026-11-05",
            "page": f"{jid}_r1",
            "best": {STEM: f"{CONCEPT}-full"},
            "clips": {f"{STEM}_{CONCEPT}-full": {**clip, "render": rid, "draft": False, "frames": [47]}},
        }
        assert client.post(f"/api/jobs/{jid}/picks", {"round": 1, "picks": {**picks, "extra": 1}})[0] == 400
        bad = {
            **picks,
            "clips": {f"{STEM}_{CONCEPT}-full": {**clip, "props": {"one_picture": True, "transforms": True}}},
        }
        assert client.post(f"/api/jobs/{jid}/picks", {"round": 1, "picks": bad})[0] == 400
        code, graded, _ = client.post(f"/api/jobs/{jid}/picks", {"round": 1, "picks": picks, "text": "the drive"})
        assert code == 200, graded
        saved = read_json(d / graded["grade"]["picks"])
        assert sorted(saved) == ["best", "clips", "date", "page"] and saved["best"] == {STEM: f"{CONCEPT}-full"}
        lines.append(f"grade: {graded['grade']['picks']}; an extra key and props without not_invented answered 400")

        code, body, _ = client.post(f"/api/jobs/{jid}/page", {"override": True, "title": f"{PAIR}: the rebuild"})
        assert code == 202, body
        page2, _ = poll(client, jid, str(body["record"]))
        assert page2["state"] == "done" and page2["previous"] == "previous_index.html"
        assert md5_file(d / "stages" / page2["id"] / "previous_index.html") == page_md5
        lines.append(
            f"rebuild {page2['id']}: md5 {md5_file(d / 'run' / 'index.html')}; previous page kept ({page_md5})"
        )

        # check 10: the originals and the frozen files; red if anything writes through a raw/ link or a frozen plan
        assert {str(p): (p.stat().st_mtime_ns, sha256_file(p)) for p in frozen} == before
        assert newer(marker, sweep) == []
        lines.append(
            f"originals and frozen files unchanged; nothing new under the plans, fixtures, layers and mattes; "
            f"{time.time() - t0:.0f} s"
        )
    finally:
        if d is not None:
            for sj_path in (d / "stages").glob("*/stage.json"):
                r2: Any = read_json(sj_path) or {}
                if r2.get("state") not in ("running", "cancelling"):
                    continue
                with contextlib.suppress(OSError):
                    client.post(f"/api/jobs/{d.name}/stages/{r2['id']}/cancel")
                if (read_json(sj_path) or {}).get("state") in ("running", "cancelling") and r2.get("pid"):
                    with contextlib.suppress(OSError):
                        os.killpg(int(r2["pid"]), signal.SIGTERM)
        server.stop()
    print(f"\njob {d}")
    for ln in lines:
        print(f"  {ln}")
