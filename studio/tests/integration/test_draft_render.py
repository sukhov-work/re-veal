"""A 480 px draft of the frozen angel_a2 plan on the 2026-11-04 job, by a server on the real tree and the main venv.

It writes under benchmarks/runs/2026-11-04/studio/loop_angel_20261104-220719/ only (gitignored): one record under
stages/ and the draft under drafts/angel/port_check_<stamp>/. The server never runs reconcile_all here: the owner's
server holds the tree's lock, so this one reconciles nothing but its own record.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from reveal_studio.config import resolve_settings
from reveal_studio.fs import Json, md5_file, read_json, stamp
from reveal_studio.runner.argv import ScriptFlags
from reveal_studio.server.app import App, StudioServer

from ..conftest import REPO, Client, free_port

pytestmark = pytest.mark.acceptance  # 2026-11-05: opt-in, it writes an 8 MB draft into the owner's job each run

JOB = "loop_angel_20261104-220719"
JOB_DIR = REPO / "benchmarks/runs/2026-11-04/studio" / JOB

if not (REPO / ".venv/bin/python").exists() or not (JOB_DIR / "in/angel/prep.json").is_file():
    pytest.skip(f"the main venv or the job {JOB} with its prep is absent", allow_module_level=True)


def test_a_draft_render_of_angel_a2_runs_to_done(tmp_path: Path) -> None:
    settings = resolve_settings(root=REPO, port=free_port(), lock=tmp_path / "studio.lock", open_browser=False, env={})
    app = App.build(settings)
    assert app.flags == ScriptFlags(progress=True, frames=True, readers=True)
    httpd = StudioServer(app)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    client = Client(settings.port)
    name = f"port_check_{stamp()}"
    t0 = time.time()
    try:
        code, body, _ = client.post(
            f"/api/jobs/{JOB}/stages/render/run", {"knobs": {"plan": "frozen:angel_a2", "name": name, "draft": 480}}
        )
        assert code == 202, body
        rid = body["record"]
        rec: Json = {}
        while time.time() - t0 < 600:
            code, rec, _ = client.get(f"/api/jobs/{JOB}/stages/{rid}")
            assert code == 200
            if rec["state"] not in ("running", "cancelling") and (rec["state"] != "done" or rec["outputs"]):
                break
            time.sleep(0.5)
    finally:
        httpd.shutdown()
        httpd.server_close()
    wall = time.time() - t0
    out = JOB_DIR / "drafts" / "angel" / name
    assert rec["state"] == "done", rec.get("reason")
    m = read_json(out / "measure.json")
    assert m is not None and m["draft"] == 480
    md5s = {Path(o["path"]).name: o["md5"] for o in rec["outputs"]}
    for o in rec["outputs"]:
        assert o["md5"] == md5_file(REPO / o["path"]), o["path"]
    assert md5s["loop.mp4"] == m["md5_mp4"]
    assert rec["script_md5"] == m["script_md5"]  # the script the record started is the one the render stamped
    assert f'in="benchmarks/runs/2026-11-04/studio/{JOB}/in/angel"' in rec["argv"]
    print(f"\nrecord {rid} · {wall:.1f} s wall · record wall_s {rec['wall_s']} · script_md5 {rec['script_md5']}")
    for k in ("loop.mp4", "loop.gif", "measure.json", "frames.json", "plan.json", "sheet.jpg"):
        print(f"  {k} md5 {md5s.get(k)}")
    print(f"  frames {m['frames']} canvas {m['canvas']} plan_sha256 {m['plan_sha256']} render_s {m['render_s']}")
