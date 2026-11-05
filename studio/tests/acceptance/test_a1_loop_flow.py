"""The A1 acceptance of STUDIO.md §9 on the package: checks 3 to 13 of the drive of 2026-11-04
(.claude/claude-docs/research/2026-11-04/a1_acceptance.md), with its recorded values, through a `reveal-studio serve`
subprocess on a free port with a tmp lock against the real tree.

The test takes about 2 minutes on this laptop (107 s on 2026-11-05; the full a2 render alone takes 60 to 80 s). It
makes one new job from the owner's angel stills under benchmarks/runs/<today>/studio/ (gitignored, 67 MB): the prep,
the readers, the full a2, a 960 draft, a page and its round, a 480 draft across a server restart, and two cancelled
renders. It writes into no other job. Every `serve` start runs `reconcile_all` over every job of the tree. So before
the first start, and before the render that check 12 restarts the server under, the test waits until no other job has a
running record (it skips after 5 minutes); just before the restart it skips at once if another job's record started.

It skips when the repo root (REVEAL_STUDIO_ROOT, else discovery), the main venv's python, the recorded prep of
2026-11-04 or the stills (REVEAL_STUDIO_STILLS, default the Telegram folder) are absent, or when the stills are not
the angel pair whose sha256s the recorded values belong to. Run it alone:
`uv run pytest tests/acceptance -m acceptance -s`; `pytest tests -m acceptance` also runs
tests/integration/test_draft_render.py, which writes a draft into the job loop_angel_20261104-220719.

The impeccable detector and the page's DOM checks (checks 14 and 15) stay in the drive; they need a browser.
"""

from __future__ import annotations

import collections
import contextlib
import filecmp
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import IO, Any

import pytest

from reveal_studio.config import ConfigError, Settings, resolve_settings
from reveal_studio.fs import Json, md5_file, read_json, sha256_file

from ..conftest import Client, free_port, wait_for

pytestmark = pytest.mark.acceptance

STILLS = Path(os.environ.get("REVEAL_STUDIO_STILLS", "/Users/yevhens/Downloads/Telegram Desktop/angel-portrait"))
STILLS_SHA256 = [
    "c0bb68c6df26fd637408335c3c922f3b56be3b09c7c337070f6b842c38792f98",
    "b2a1dd82f5b6dcc5b9ec3daebf1d1c61564ed18c5cf4ddd897b430b10403a8f7",
]
RECORDED_PREP = Path("benchmarks/runs/2026-11-04/angel/in/angel")
PREP_FILES = ("k0.png", "k1.png", "depth_k0.npy", "depth_k1.npy")
LOCK_WINDOWS = "422,371,582,441;248,478,318,618;757,458,827,538"
MD5_A2 = "c302623f293eacd069218fd7518e0967"  # the full a2 of 2026-11-04 (a1_acceptance.md, check 6)
MD5_A2_960 = "3d453980f80eff43014646a6f65398a6"  # the a2d draft at 960 of the same drive
MD5_A2_480 = "2955c25c2611565b3ee57d2d081f8669"  # the a2r draft at 480 of the same drive
TERMINAL = ("done", "failed", "refused", "lost", "cancelled")
QUIET_WAIT_S = 300.0


def angel_stills() -> list[Path]:
    return sorted(p for p in STILLS.iterdir() if p.suffix.lower() in (".jpg", ".jpeg") and not p.name.startswith("."))


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


def foreign_running(settings: Settings, mine: Path | None) -> list[str]:
    """The running or cancelling records of every job but `mine`: a `serve` start would reconcile them."""
    out = []
    for sj in settings.runs.glob("*/studio/*/stages/*/stage.json"):
        if mine is not None and sj.is_relative_to(mine):
            continue
        r = read_json(sj) or {}
        if r.get("state") in ("running", "cancelling"):
            out.append(f"{sj.parents[2].name}/{r.get('id')}")
    return out


def wait_quiet(settings: Settings, mine: Path | None) -> None:
    deadline = time.time() + QUIET_WAIT_S
    while (busy := foreign_running(settings, mine)) and time.time() < deadline:
        time.sleep(2)
    if busy:
        pytest.skip(f"other jobs still run {busy} after {QUIET_WAIT_S:.0f} s: a serve start here would reconcile them")


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


class Server:
    """`reveal-studio serve` as a subprocess of this venv's python: the real start path, with `reconcile_all`."""

    def __init__(self, settings: Settings, log: Path) -> None:
        self.settings = settings
        self.log = log
        self.proc: subprocess.Popen[bytes] | None = None
        self._fh: IO[bytes] | None = None

    def start(self) -> Server:
        s = self.settings
        argv = [sys.executable, "-m", "reveal_studio", "serve", "--root", str(s.root), "--port", str(s.port)]
        argv += ["--no-browser", "--lock", str(s.lock_path)]
        self._fh = open(self.log, "ab")  # noqa: SIM115  # 2026-11-05: the server writes into it until stop()
        self.proc = subprocess.Popen(argv, stdout=self._fh, stderr=subprocess.STDOUT, cwd=str(s.root))
        client = Client(s.port)
        deadline = time.time() + 60
        while time.time() < deadline:
            assert self.proc.poll() is None, f"the server exited: {self.text()}"
            with contextlib.suppress(OSError):
                if client.get("/api/registry")[0] == 200:
                    return self
            time.sleep(0.1)
        raise AssertionError(f"the server did not answer in 60 s: {self.text()}")

    def stop(self) -> None:
        """SIGTERM, as a shell's `kill` stops it; the children run in their own sessions and outlive it."""
        if self.proc is not None and self.proc.poll() is None:
            self.proc.send_signal(signal.SIGTERM)
            try:
                self.proc.wait(10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(5)
        if self._fh is not None:
            self._fh.close()
            self._fh = None

    def text(self) -> str:
        return self.log.read_text(errors="replace") if self.log.exists() else ""


def poll(client: Client, jid: str, rid: str, timeout: float = 600.0) -> tuple[Json, list[Json]]:
    """The terminal record (a done one with its outputs) and every progress value seen while it ran."""
    seen: list[Json] = []
    deadline = time.time() + timeout
    while time.time() < deadline:
        code, rec, _ = client.get(f"/api/jobs/{jid}/stages/{rid}")
        assert code == 200, rec
        if rec["state"] == "running" and rec.get("progress") and rec["progress"] not in seen:
            seen.append(rec["progress"])
        if rec["state"] in TERMINAL and (rec["state"] != "done" or rec.get("outputs")):
            return dict(rec), seen
        time.sleep(0.4)
    raise AssertionError(f"{rid} did not finish in {timeout:.0f} s")


def start(client: Client, jid: str, stage: str, knobs: Json) -> str:
    code, body, _ = client.post(f"/api/jobs/{jid}/stages/{stage}/run", {"knobs": knobs})
    assert code == 202, body
    return str(body["record"])


def run(client: Client, jid: str, stage: str, knobs: Json) -> tuple[Json, list[Json]]:
    return poll(client, jid, start(client, jid, stage, knobs))


def md5s_of(rec: Json) -> dict[str, str]:
    return {Path(o["path"]).name: o["md5"] for o in rec["outputs"]}


def bands(tags: list[Json]) -> list[list[int]]:
    """The runs of generated frames, as the viewer's violet bands cover them."""
    out: list[list[int]] = []
    for t in tags:
        if not t["generated"]:
            continue
        if out and out[-1][1] == t["i"] - 1:
            out[-1][1] = t["i"]
        else:
            out.append([t["i"], t["i"]])
    return out


def cancel_soon(client: Client, jid: str, rid: str, part: Path, t0: float) -> Json:
    """Cancels once the render's .part folder exists (or 1.8 s after the start); returns the cancel's answer."""
    while not part.exists() and time.time() - t0 < 1.8:
        time.sleep(0.05)
    code, rec, _ = client.post(f"/api/jobs/{jid}/stages/{rid}/cancel")
    assert time.time() - t0 < 2.0, "the cancel was sent more than 2 s after the start"
    assert code == 200, rec
    return dict(rec)


def test_the_a1_loop_flow_on_the_angel_stills(settings: Settings, tmp_path: Path) -> None:
    s = settings
    client = Client(s.port)
    stills = angel_stills()
    mtimes = [p.stat().st_mtime_ns for p in stills]
    d: Path | None = None
    lines: list[str] = []
    wait_quiet(s, None)
    server = Server(s, tmp_path / "server1.log")
    try:
        server.start()
        # the Host check on the real server: red if Handler._host_ok answers any Host
        assert client.get("/api/jobs", {"Host": f"evil.example:{s.port}"})[0] == 403

        # check 3: a new loop job; red if create_job copies the stills or stops hashing them
        code, body, _ = client.post("/api/jobs", {"flow": "loop", "folder": str(STILLS), "seq": "angel"})
        assert code == 201, body
        jid, job = str(body["id"]), body["job"]
        d = s.root / job["root"]
        assert d.parent == s.runs / s.runs_date / "studio"
        assert jid in [j["id"] for j in client.get("/api/jobs")[1]]
        links = sorted((d / "raw" / "angel").iterdir())
        assert [p.name for p in links] == ["01.jpg", "02.jpg"]
        assert all(p.is_symlink() for p in links)
        assert [p.resolve() for p in links] == [p.resolve() for p in stills]
        assert [i["sha256"] for i in job["inputs"]] == STILLS_SHA256
        prep = d / "in" / "angel"

        # check 4: the registration with the recorded lock windows; red if a knob stops reaching `loop_seq.py prep`
        knobs = {"long": 1920, "ref": 0, "depth_maps": True, "lock_window": LOCK_WINDOWS}
        rec, _ = run(client, jid, "registration", knobs)
        assert rec["state"] == "done", rec.get("reason")
        assert rec["argv"][:2] == [str(s.python), "scripts/research/loop_seq.py"]  # a subprocess of the main venv
        p = read_json(prep / "prep.json")
        f1 = p["frames"][1]
        shift = (f1.get("lock") or {}).get("shift_px")
        assert (f1["method"], f1["inliers"], shift) == ("sift+magsac + lock", 467, [-4.93, 11.48])
        assert p["crop"] == [29, 0, 1395, 1770]
        for name in PREP_FILES:
            assert filecmp.cmp(prep / name, s.root / RECORDED_PREP / name, shallow=False), f"{name} differs"
        lines.append(f"registration {rec['id']} {rec['wall_s']} s: 467 inliers, prep identical to {RECORDED_PREP}")

        # check 5: the readers; red if the readers read the unlocked prep (0.1964) or stop counting faces
        rec, _ = run(client, jid, "readers", {})
        assert rec["state"] == "done", rec.get("reason")
        rd = read_json(prep / "readers" / "readers.json")
        assert [len(st["faces"]) for st in rd["stills"]] == [3, 2]
        assert rd["pairs"][0]["lab_above_14"] == 0.3021
        lines.append(f"readers {rec['id']} {rec['wall_s']} s: faces [3, 2], Lab above 14 on 0.3021")

        # check 6: the full a2 render; red if the argv, the plan or the prep path changes a byte of the mp4
        rec, seen = run(client, jid, "render", {"plan": "frozen:angel_a2", "name": "a2", "draft": 0})
        assert rec["state"] == "done", rec.get("reason")
        assert seen, "no progress number while a2 rendered (--progress lost from the argv?)"
        m = read_json(d / "angel" / "a2" / "measure.json")
        assert md5s_of(rec)["loop.mp4"] == m["md5_mp4"] == MD5_A2
        for o in rec["outputs"]:
            assert o["md5"] == md5_file(s.root / o["path"]), o["path"]
        assert rec["script_md5"] == m["script_md5"] == md5_file(s.loop_seq)
        # red if the render reads the plan's own `in` (the recorded prep, byte-identical) instead of the job's prep
        assert f'in="{prep.relative_to(s.root)}"' in rec["argv"]
        assert read_json(d / "angel" / "a2" / "plan.json")["in"] == str(prep.relative_to(s.root))
        lines.append(f"a2 {rec['id']} {rec['wall_s']} s: loop.mp4 {MD5_A2}, {len(seen)} progress values")
        lines.append(f"   script_md5 {rec['script_md5']}")

        # check 7: a 960 draft; red if a draft lands among the full renders or loses its long edge
        rec, seen = run(client, jid, "render", {"plan": "frozen:angel_a2", "name": "a2d", "draft": 960})
        assert rec["state"] == "done", rec.get("reason")
        assert seen, "no progress number while a2d rendered"
        cands = {(c["kind"], c["name"]): c for c in client.get(f"/api/jobs/{jid}")[1]["candidates"]}
        assert (cands[("draft", "a2d")]["draft"], cands[("draft", "a2d")]["md5_mp4"]) == (960, MD5_A2_960)
        assert ("full", "a2d") not in cands
        lines.append(f"a2d {rec['id']} {rec['wall_s']} s: loop.mp4 {MD5_A2_960}")

        # check 8: the viewer's data and a marked frame; red if frame_tag or the frames route changes
        code, rv, _ = client.get(f"/api/jobs/{jid}/render/full/a2")
        assert code == 200, rv
        tags = rv["frames_tags"]
        assert (rv["frames_available"], len(tags)) == (50, 50)
        assert collections.Counter(t["tag"] for t in tags) == {"photo": 26, "generated": 24}
        assert all(t["t"] is not None for t in tags if t["generated"])
        assert len(rv["measure"]["steps"]) == 49
        assert bands(tags) == [[14, 25], [38, 49]]
        code, jpg, h = client.get(f"/api/jobs/{jid}/render/full/a2/frame/25")
        assert (code, h["content-type"], jpg[:2]) == (200, "image/jpeg", b"\xff\xd8")
        note = "acceptance test: the breath's peak"
        code, mark, _ = client.post(
            f"/api/jobs/{jid}/frames/mark", {"kind": "full", "name": "a2", "frame": 25, "note": note}
        )
        assert code == 201, mark
        saved = read_json(d / "owner_frames" / "full_a2_f0025.json")
        assert (saved["frame"], saved["note"], saved["md5_mp4"]) == (25, note, MD5_A2)

        # check 9: a skeptic request listed by the CLI and the API; red if write_request drops the answer's shape
        code, req, _ = client.post(
            f"/api/jobs/{jid}/requests/skeptic", {"brief": "acceptance test", "candidates": ["a2"]}
        )
        assert code == 201, req
        rq = read_json(s.root / req["file"])
        assert rq["answer"]["shape"]["candidates"]["<name>"]["verdict"] == "READY | READY WITH A NOTE | NOT READY"
        assert [(c["name"], c["md5_mp4"]) for c in rq["candidates"]] == [("a2", MD5_A2)]
        assert [f["frame"] for f in rq["owner_frames"]] == [25]
        cli = subprocess.run(
            [sys.executable, "-m", "reveal_studio", "requests", "--root", str(s.root)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        line = next((ln for ln in cli.stdout.splitlines() if req["file"] in ln), "")
        assert re.match(r"^\s*\d+ (s|min)\s", line), cli.stdout
        assert any(r["file"] == req["file"] and r["age_s"] >= 0 for r in client.get("/api/requests")[1])

        # check 10: the page gate; red if build_page stops refusing an unjudged candidate or drops the override
        code, body, _ = client.post(f"/api/jobs/{jid}/page", {})
        assert code == 409 and body["refused"] == ["a2"], body
        assert "a2 (unjudged" in body["error"]
        assert not (d / "index.html").exists()
        footer = "acceptance test: override"
        code, body, _ = client.post(f"/api/jobs/{jid}/page", {"override": True, "footer": footer})
        assert code == 202, body
        override = body["override"]
        assert override.startswith("Override: built on his word with a2 (unjudged")
        rec, _ = poll(client, jid, body["record"])
        assert rec["state"] == "done", rec.get("reason")
        rounds = wait_for(lambda: client.get(f"/api/jobs/{jid}")[1]["rounds"], timeout=10)
        html = (d / "index.html").read_text()
        assert override in html and footer in html
        page_md5 = md5_file(d / "index.html")
        assert (d / "page.md5").read_text().split()[0] == page_md5 == rounds[0]["page_md5"]
        assert (rounds[0]["n"], rounds[0]["override"]) == (1, override)
        assert filecmp.cmp(d / "rounds" / "1" / "index.html", d / "index.html", shallow=False)
        lines.append(f"page {rec['id']}: index.html {page_md5}, round 1 opened with the override")

        # check 11: the round gate; red if start_stage lets a full render pass an ungraded round
        a3 = {"plan": "frozen:angel_a3", "name": "a3", "draft": 0}
        code, body, _ = client.post(f"/api/jobs/{jid}/stages/render/run", {"knobs": a3})
        assert code == 409 and body["round"] == 1, body
        assert body["error"].startswith("round 1 has no grade text")
        grade = "acceptance test: the grade text"
        code, rnd, _ = client.post(f"/api/jobs/{jid}/picks", {"round": 1, "text": grade})
        assert code == 200, rnd
        assert (rnd["grade"]["text"], rnd["grade"]["page_md5"]) == (grade, page_md5)
        t0 = time.time()
        rid = start(client, jid, "render", a3)
        rec = cancel_soon(client, jid, rid, d / "angel" / "a3.part", t0)
        assert (rec["state"], rec["reason"]) == ("cancelled", "cancelled by you")
        assert not (d / "angel" / "a3.part").exists() and not (d / "angel" / "a3").exists()

        # check 12: a restart during a render; red if a child dies with the server or reconcile skips a live pid
        wait_quiet(s, d)
        rid = start(client, jid, "render", {"plan": "frozen:angel_a2", "name": "a2restart", "draft": 480})
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
        assert attached in server.text(), f"no re-attach (did the draft end before the restart?): {server.text()}"
        rec, _ = poll(client, jid, rid)
        assert rec["state"] == "done", rec.get("reason")
        assert "finished after a restart" in rec["note"]
        assert md5s_of(rec)["loop.mp4"] == MD5_A2_480
        lines.append(f"a2restart {rec['id']} {rec['wall_s']} s: re-attached, done, loop.mp4 {MD5_A2_480}")

        # check 13: cancel within 2 s; red if cancel stops killing the group or leaves the .part folder
        t0 = time.time()
        rid = start(client, jid, "render", {"plan": "frozen:angel_a2", "name": "a2cancel", "draft": 480})
        rec = cancel_soon(client, jid, rid, d / "drafts" / "angel" / "a2cancel.part", t0)
        assert (rec["state"], rec["reason"]) == ("cancelled", "cancelled by you")
        assert not (d / "drafts" / "angel" / "a2cancel.part").exists()
        assert not (d / "drafts" / "angel" / "a2cancel").exists()
        assert not alive(int(rec["pid"]))

        # the originals: never modified (red if anything writes through the raw/ symlinks)
        assert [p.stat().st_mtime_ns for p in stills] == mtimes
        assert [sha256_file(p) for p in stills] == STILLS_SHA256
    finally:
        # No stage of this job outlives the test, and none stays `running` on disk (backlog T99): a failed assertion
        # right after a 202 left one so, and every later run's wait_quiet then waited 5 minutes and skipped. The
        # cancel route ends the record `cancelled` while the server is up; the kill is the fallback.
        if d is not None:
            for sj in (d / "stages").glob("*/stage.json"):
                r: Any = read_json(sj) or {}
                if r.get("state") not in ("running", "cancelling"):
                    continue
                with contextlib.suppress(OSError):
                    client.post(f"/api/jobs/{d.name}/stages/{r['id']}/cancel")
                if (read_json(sj) or {}).get("state") in ("running", "cancelling") and r.get("pid"):
                    with contextlib.suppress(OSError):
                        os.killpg(int(r["pid"]), signal.SIGTERM)
        server.stop()
    print(f"\njob {d}")
    for ln in lines:
        print(f"  {ln}")
