"""The A2 acceptance of STUDIO.md §9 on the package: the API half of the drive of 2026-11-05
(benchmarks/runs/2026-11-05/studio/agents/a2_acceptance.md, checks 1, 2, 4, 5, 6 and 10), with the recorded values of
.claude/claude-docs/research/2026-11-05/loopseq_a2.md, through a `reveal-studio serve` subprocess on a free port with a
tmp lock against the real tree.

The test took 83 s on this laptop on 2026-11-05; budget 3 minutes, since the full a2 render alone takes 60 to 80 s. It
makes one new job from the owner's angel stills under benchmarks/runs/<today>/studio/ (gitignored, 96 MB): three
registrations (the lock windows with ten named windows; a rerun with the ruled `ecc_refine` and `bg_depth` 0.15; a
rerun without them, which restores the locked prep byte for byte), the probe at 960, an unchanged copy of
frozen:angel_a2 saved in the job and rendered in full, a measure of that render, and a page that lists it by
`variants`. It writes into no other job. Every `serve` start reconciles the running records of every job of the tree
(backlog T88), so before the start the test waits until no other job has a running record (it skips after 5 minutes).

It skips as the A1 test does: when the repo root (REVEAL_STUDIO_ROOT, else discovery), the main venv's python, the
recorded prep of 2026-11-04 or the stills (REVEAL_STUDIO_STILLS) are absent, or when the stills are not the angel pair.
Run it alone: `uv run pytest tests/acceptance/test_a2_loop_flow.py -m acceptance -s -q`. The page's own checks (the plan
editor, the ruling chips, the comparator, the graph, the strip's branch row, the hints) stay in the drive; they need a
browser. The helpers (Server, poll, run, wait_quiet) are the A1 test's.
"""

from __future__ import annotations

import contextlib
import filecmp
import os
import signal
from pathlib import Path
from typing import Any

import pytest

from reveal_studio.config import ConfigError, Settings, resolve_settings
from reveal_studio.fs import Json, md5_file, read_json, sha256_file

from ..conftest import Client, free_port
from .test_a1_loop_flow import (
    LOCK_WINDOWS,
    MD5_A2,
    PREP_FILES,
    RECORDED_PREP,
    STILLS,
    STILLS_SHA256,
    Server,
    angel_stills,
    md5s_of,
    poll,
    run,
    wait_quiet,
)

pytestmark = pytest.mark.acceptance

WINDOWS = (
    "ring_top:422,371,582,441;ring_left:248,478,318,618;ring_right:757,458,827,538;lamp_arm:53,560,203,760;"
    "mirror_edge:534,300,834,360;exit_sign:1084,20,1284,130;couch_right:1134,900,1387,1300;"
    "laptop_edge:634,1520,1034,1620;left_face:334,700,594,1000;right_face:884,580,1134,900"
)  # loopseq_a2.md §3: the three ring boxes are the lock windows
KNOBS: Json = {"long": 1920, "ref": 0, "depth_maps": True, "lock_window": LOCK_WINDOWS, "windows": WINDOWS}
RING_TOP_CANVAS = "ring_top:393,371,553,441"  # the ring's top window on the locked canvas (loopseq_a2.md §5)
RENDER_FILES = ("loop.mp4", "measure.json", "frames.json", "plan.json")


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """The real tree's settings on a free port with a tmp lock; skips with the reason when an input is absent."""
    try:
        s = resolve_settings(port=free_port(), lock=tmp_path / "studio.lock", open_browser=False)
    except ConfigError as e:
        pytest.skip(f"no repo root: {e}")
    if not s.python.exists():
        pytest.skip(f"the main venv's python {s.python} is absent (./setup.sh at the root)")
    missing = [n for n in PREP_FILES if not (s.root / RECORDED_PREP / n).is_file()]
    if missing:
        pytest.skip(f"the recorded prep {RECORDED_PREP} lacks {missing}")
    if not STILLS.is_dir():
        pytest.skip(f"the stills folder {STILLS} is absent (set REVEAL_STUDIO_STILLS)")
    if [sha256_file(p) for p in angel_stills()] != STILLS_SHA256:
        pytest.skip(f"{STILLS} does not hold the angel pair the recorded values belong to")
    return s


def cell(fits: Json, name: str, fit: str) -> tuple[float, float]:
    """One window's (dx, dy) under one fit in frame 1, as the registration panel's table reads it."""
    row = next(r for r in fits["frames"][0]["rows"] if r["name"] == name)
    c: Json = row["cells"][fit]
    return c["dx"], c["dy"]


def same_prep(s: Settings, prep: Path) -> list[str]:
    """The prep files that differ from the recorded prep of 2026-11-04 (empty: byte-identical)."""
    return [n for n in PREP_FILES if not filecmp.cmp(prep / n, s.root / RECORDED_PREP / n, shallow=False)]


def test_the_a2_loop_flow_on_the_angel_stills(settings: Settings, tmp_path: Path) -> None:
    s = settings
    client = Client(s.port)
    stills = angel_stills()
    mtimes = [p.stat().st_mtime_ns for p in stills]
    d: Path | None = None
    lines: list[str] = []
    wait_quiet(s, None)
    server = Server(s, tmp_path / "server.log")
    try:
        server.start()
        code, body, _ = client.post("/api/jobs", {"flow": "loop", "folder": str(STILLS), "seq": "angel"})
        assert code == 201, body
        jid = str(body["id"])
        d = s.root / body["job"]["root"]
        prep = d / "in" / "angel"

        # check 1: the registration with the lock and the ten named windows; red if the windows knob stops reaching
        # `loop_seq.py prep --windows` or fits_summary drops a fit or swaps dx and dy
        rec, _ = run(client, jid, "registration", KNOBS)
        assert rec["state"] == "done", rec.get("reason")
        f1 = read_json(prep / "prep.json")["frames"][1]
        assert (f1["method"], f1["inliers"], f1["lock"]["shift_px"]) == ("sift+magsac + lock", 467, [-4.93, 11.48])
        fits = client.get(f"/api/jobs/{jid}")[1]["prep"]["fits"]
        assert fits["fits"] == ["all", "final"], fits["fits"]  # no `far` column: no --bg-depth
        assert fits["frames"][0]["lock_shift"] == [-4.93, 11.48]
        assert cell(fits, "ring_top", "final") == (1.40, -1.09)
        assert cell(fits, "ring_top", "all") == (6.14, -12.59)
        assert len(fits["frames"][0]["rows"]) == 10
        assert same_prep(s, prep) == [], "the locked prep differs from the recorded prep"
        lines.append(f"registration {rec['id']} {rec['wall_s']} s: ring_top final (+1.40, -1.09), all (+6.14, -12.59)")

        # check 4, the API half: a ruled value warns in the 202 body and the record, and the run still starts; red if
        # run_warnings stops reading the stage knobs or the route drops `warnings`
        ruled = dict(KNOBS, ecc_refine=True, bg_depth=0.15)
        code, body, _ = client.post(f"/api/jobs/{jid}/stages/registration/run", {"knobs": ruled})
        assert code == 202, body
        warn = [(w["knob"], w["value"], w["since"]) for w in body["warnings"]]
        assert warn == [("registration.ecc_refine", True, "2026-11-04")], body["warnings"]
        rec, _ = poll(client, jid, str(body["record"]))
        assert rec["state"] == "done", rec.get("reason")
        assert [w["knob"] for w in rec["warnings"]] == ["registration.ecc_refine"]
        p = read_json(prep / "prep.json")
        assert (p["ecc_refine"], p["bg_depth"]) == (True, 0.15)  # red if the two knobs stop reaching the script
        lines.append(f"ruled registration {rec['id']}: 202 warnings {warn}; {p['frames'][1]['method']}")

        # the restore: the knobs of check 1 again; red if a registration rerun stops moving the previous prep aside
        rec, _ = run(client, jid, "registration", KNOBS)
        assert rec["state"] == "done", rec.get("reason")
        assert "the previous prep moved to" in rec["note"]
        fits = client.get(f"/api/jobs/{jid}")[1]["prep"]["fits"]
        assert fits["fits"] == ["all", "final"] and cell(fits, "ring_top", "final") == (1.40, -1.09)
        assert same_prep(s, prep) == [], "the restored prep differs from the recorded prep"
        lines.append(f"restore {rec['id']}: ring_top final (+1.40, -1.09) again; prep identical to {RECORDED_PREP}")

        # check 2: the probe at 960 on the locked prep (after the reruns: a rerun moves in/angel/probe/ aside);
        # red if the long knob stops reaching `loop_seq.py probe` or probe_view drops a method or a t
        rec, _ = run(client, jid, "probe", {"long": 960})
        assert rec["state"] == "done", rec.get("reason")
        pv = client.get(f"/api/jobs/{jid}")[1]["probe"]
        assert (pv["size"], pv["rife_skipped"]) == ([740, 960], None)
        pair = pv["pairs"][0]
        assert (pair["a"], pair["b"], pair["matte_share"], pair["faces"]) == (0, 1, 0.4751, 2)
        dexp = {m["method"]: [f["dexp"] for f in m["frames"]] for m in pair["methods"]}
        assert dexp == {
            "rife": [0.0413, 0.0611, 0.0341],
            "morph": [0.0233, 0.065, 0.0245],
            "dissolve": [0.0012, 0.231, 0.0012],
        }, dexp
        for m in pair["methods"]:  # the three strips exist and are served
            code, jpg, _ = client.get(m["strip"])
            assert (code, jpg[:2]) == (200, b"\xff\xd8"), m["strip"]
        assert len(pair["crops"]) == 6 and all(c["a"] and c["b"] and len(c["mid"]) == 3 for c in pair["crops"])
        lines.append(f"probe {rec['id']} {rec['wall_s']} s: rife dexp {dexp['rife']} inside the matte")

        # check 5: frozen:angel_a2 saved unchanged in the job and rendered in full; red if save_plan writes a key the
        # render reads, or the render stops setting `in` to the job's prep
        code, plan, _ = client.get("/api/plans/frozen/angel_a2")
        assert code == 200, plan
        plan.pop("provenance", None)
        code, saved, _ = client.post(
            f"/api/jobs/{jid}/plans",
            {"name": "a2_copy", "plan": plan, "from": "frozen:angel_a2", "words": "A2 acceptance test: unchanged"},
        )
        assert code == 201 and saved["changes"] == [], saved
        rec, seen = run(client, jid, "render", {"plan": "job:a2_copy", "name": "a2copy", "draft": 0})
        assert rec["state"] == "done", rec.get("reason")  # a note "finished after a restart" is T88's race, not a fail
        assert seen, "no progress number while a2copy rendered"
        rd = d / "angel" / "a2copy"
        assert md5s_of(rec)["loop.mp4"] == read_json(rd / "measure.json")["md5_mp4"] == MD5_A2
        assert f'in="{prep.relative_to(s.root)}"' in rec["argv"]
        assert read_json(rd / "plan.json")["in"] == str(prep.relative_to(s.root))
        assert rec["script_md5"] == md5_file(s.loop_seq)
        lines.append(f"a2copy {rec['id']} {rec['wall_s']} s: loop.mp4 {MD5_A2}, {len(seen)} progress values")

        # check 6: the measure of the ring's top window on the full a2copy; red if the measure writes into the render's
        # own files, stops passing --window or --frames-json, or measure_runs stops reading its folder
        before = {n: md5_file(rd / n) for n in RENDER_FILES}
        listing = sorted(q.name for q in rd.iterdir())
        knobs = {"render": "full:a2copy", "windows": RING_TOP_CANVAS, "ref": 0}
        rec, _ = run(client, jid, "measure", knobs)
        assert rec["state"] == "done", rec.get("reason")
        folder = rd / "measures" / rec["id"].replace("_measure", "")
        m = read_json(folder / "measure.json")
        peak = m["stability_max"]["ring_top"]
        assert m["stability_ref"] == 0 and peak["box"] == [393, 371, 553, 441]
        assert (peak["dx_max_at"], peak["dy_max_at"]) == (13, 26), peak
        assert peak["dx_max"] == pytest.approx(1.18, abs=0.02) and peak["dy_max"] == pytest.approx(3.96, abs=0.02)
        assert peak["corr_min"] == pytest.approx(0.987, abs=0.002)
        assert {n: md5_file(rd / n) for n in RENDER_FILES} == before, "the measure changed the render's own files"
        assert sorted(q.name for q in rd.iterdir()) == sorted([*listing, "measures"])
        rv = client.get(f"/api/jobs/{jid}/render/full/a2copy")[1]
        assert rv["stability"]["record"] == rec["id"] and rv["stability"]["max"]["ring_top"] == peak
        sj = rv["stalls_and_jumps"]  # check 7's numbers: a flag here is a finding for the owner, not a failure
        lines.append(f"measure {rec['id']}: ring_top dx {peak['dx_max']} at f 13, dy {peak['dy_max']} at f 26")
        lines.append(f"   corr_min {peak['corr_min']}; the render's files unchanged; stalls and jumps {sj}")

        # check 10: the page lists the named renders; red if page_variants stops refusing an unknown name before the
        # script runs, or the round stops recording its variants
        stages = sorted(q.name for q in (d / "stages").iterdir())
        code, body, _ = client.post(f"/api/jobs/{jid}/page", {"variants": ["nope"]})
        assert code == 400 and "nope" in body["error"] and body["unknown"] == "nope", body
        assert sorted(q.name for q in (d / "stages").iterdir()) == stages and not (d / "index.html").exists()
        footer = "A2 acceptance test"
        code, body, _ = client.post(
            f"/api/jobs/{jid}/page", {"variants": ["a2copy"], "override": True, "footer": footer}
        )
        assert code == 202, body
        rec, _ = poll(client, jid, str(body["record"]))
        assert rec["state"] == "done", rec.get("reason")
        assert rec["argv"][-2:] == ["--variants", "a2copy"]
        rnd = read_json(d / "rounds" / "1" / "round.json")
        assert (rnd["variants"], rnd["candidates"], rnd["override"]) == (["a2copy"], ["a2copy"], body["override"])
        html = (d / "index.html").read_text()
        assert footer in html and body["override"] in html
        lines.append(f"page {rec['id']}: round 1 variants {rnd['variants']}, page md5 {rnd['page_md5']}")

        # the originals: never modified (red if anything writes through the raw/ symlinks)
        assert [q.stat().st_mtime_ns for q in stills] == mtimes
        assert [sha256_file(q) for q in stills] == STILLS_SHA256
    finally:
        # No stage of this job outlives the test, and none stays `running` on disk: a failed assertion right after a
        # 202 left one so on 2026-11-05, and every later run's wait_quiet then waits 5 minutes and skips. The cancel
        # route ends the record `cancelled` while the server is up; the kill is the fallback.
        if d is not None:
            for sj_path in (d / "stages").glob("*/stage.json"):
                r: Any = read_json(sj_path) or {}
                if r.get("state") not in ("running", "cancelling"):
                    continue
                with contextlib.suppress(OSError):
                    client.post(f"/api/jobs/{d.name}/stages/{r['id']}/cancel")
                if (read_json(sj_path) or {}).get("state") in ("running", "cancelling") and r.get("pid"):
                    with contextlib.suppress(OSError):
                        os.killpg(int(r["pid"]), signal.SIGTERM)
        server.stop()
    print(f"\njob {d}")
    for ln in lines:
        print(f"  {ln}")
