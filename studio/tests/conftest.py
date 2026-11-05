"""Fixtures: a tmp repo root with the fake loop_seq.py and a fake main-venv python, Settings on it, the Runner, the App,
and a live server on a free port with a small HTTP client."""

from __future__ import annotations

import http.client
import json
import socket
import sys
import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest

from reveal_studio.config import Settings, resolve_settings
from reveal_studio.fs import Json, read_json
from reveal_studio.jobs.store import create_job
from reveal_studio.runner.argv import ScriptFlags
from reveal_studio.runner.process import Runner
from reveal_studio.server.app import App, StudioServer

FAKE = Path(__file__).parent / "fakes" / "loop_seq.py"
REPO = Path(__file__).resolve().parents[2]
"""The real repo root (the integration tests read it; the unit tests never do)."""

FROZEN_PLAN: Json = {
    "seq": "tiny",
    "in": "benchmarks/runs/2026-11-05/somewhere/in/tiny",
    "title": "two holds, a rife leg and a dissolve back",
    "gag": "a test plan",
    "timeline": [
        {"key": 0, "hold": 3},
        {"to": 1, "n": 2, "method": "rife", "ease": "smooth"},
        {"key": 1, "hold": 2},
        {"to": 0, "n": 2, "method": "dissolve", "ease": "linear"},
    ],
    "matte": {"thr": 14},
    "crf": 14,
    "gif_long": 540,
}
FLAGS = ScriptFlags(progress=True, frames=True, readers=True)
TERMINAL = ("done", "failed", "refused", "lost", "cancelled")


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def wait_for(cond: Callable[[], Any], timeout: float = 30.0, step: float = 0.05) -> Any:
    """Polls `cond` until it returns a truthy value; fails the test after `timeout` seconds."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        v = cond()
        if v:
            return v
        time.sleep(step)
    raise AssertionError(f"timed out after {timeout} s waiting for {cond}")


def wait_record(d: Path, rid: str, timeout: float = 30.0) -> Json:
    """The record once it is terminal; a done record once its outputs are written too."""

    def ready() -> Json | None:
        r: Json | None = read_json(d / "stages" / rid / "stage.json")
        if r and r["state"] in TERMINAL and (r["state"] != "done" or r.get("outputs")):
            return r
        return None

    rec: Json = wait_for(ready, timeout)
    return rec


def make_root(base: Path) -> Path:
    """A repo root: reveal.py and AGENTS.md stubs, benchmarks/runs/, one frozen plan, the fake script and python."""
    r = base / "repo"
    (r / "benchmarks/runs").mkdir(parents=True)
    (r / "reveal.py").write_text("# a stub: the marker of a Reveal repo root\n")
    (r / "AGENTS.md").write_text("# a stub: the marker of a Reveal repo root\n")
    plans = r / "scripts/research/plans/loops"
    plans.mkdir(parents=True)
    (plans / "tiny_a1.json").write_text(json.dumps(FROZEN_PLAN, indent=1))
    (r / "scripts/research/loop_seq.py").write_text(FAKE.read_text())
    py = r / ".venv/bin/python"
    py.parent.mkdir(parents=True)
    py.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')  # the main venv's python, played by this one
    py.chmod(0o755)
    return r


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return make_root(tmp_path)


@pytest.fixture
def settings(root: Path, tmp_path: Path) -> Settings:
    return resolve_settings(
        root=root, port=free_port(), lock=tmp_path / "studio.lock", runs_date="2026-11-05", open_browser=False, env={}
    )


@pytest.fixture
def runner(settings: Settings) -> Runner:
    return Runner(settings, FLAGS)


@pytest.fixture
def app(settings: Settings, runner: Runner) -> App:
    return App(settings=settings, flags=FLAGS, runner=runner)


def write_stills(folder: Path, n: int = 2) -> Path:
    """n tiny developed JPGs (capture order = name order) plus files prep ignores: a raw, an xmp, a hidden jpg."""
    import cv2
    import numpy as np

    folder.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        cv2.imwrite(str(folder / f"IMG_{i + 1:04d}.jpg"), np.full((48, 64, 3), 60 + 40 * i, np.uint8))
    (folder / "IMG_0001.ARW").write_bytes(b"raw")
    (folder / "IMG_0001.xmp").write_text("<x/>")
    (folder / ".hidden.jpg").write_bytes(b"not a still")
    return folder


@pytest.fixture
def stills(tmp_path: Path) -> Path:
    return write_stills(tmp_path / "Tiny Stills")


@pytest.fixture
def job(settings: Settings, stills: Path) -> tuple[Path, Json]:
    """A new loop job (not registered yet) and its folder."""
    j = create_job(settings, "loop", folder=str(stills), seq="tiny")
    return settings.root / j["root"], j


def run(runner: Runner, d: Path, job: Json, stage: str, knobs: Json | None = None) -> Json:
    """Starts a stage and waits for its terminal record."""
    from reveal_studio.registry.loop import stage_def

    rec = runner.start_stage(d, job, stage_def("loop", stage), knobs or {})
    return wait_record(d, rec["id"])


@pytest.fixture
def registered(runner: Runner, job: tuple[Path, Json]) -> tuple[Path, Json]:
    """The job after one registration (with depth maps)."""
    d, j = job
    rec = run(runner, d, j, "registration", {"depth_maps": True})
    assert rec["state"] == "done", rec
    return d, j


class Client:
    """http.client against the live server: (status, parsed JSON or bytes, headers)."""

    def __init__(self, port: int) -> None:
        self.port = port

    def request(
        self, method: str, path: str, body: Any = None, headers: dict[str, str] | None = None, raw: bytes | None = None
    ) -> tuple[int, Any, dict[str, str]]:
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=60)
        h = {"Host": f"127.0.0.1:{self.port}"}
        data = raw
        if body is not None:
            data = json.dumps(body).encode()
            h["Content-Type"] = "application/json"
        h.update(headers or {})
        try:
            conn.request(method, path, body=data, headers=h)
            resp = conn.getresponse()
            payload = resp.read()
            hdrs = {k.lower(): v for k, v in resp.getheaders()}
        finally:
            conn.close()
        out: Any = payload
        if hdrs.get("content-type", "").startswith("application/json"):
            out = json.loads(payload)
        return resp.status, out, hdrs

    def get(self, path: str, headers: dict[str, str] | None = None) -> tuple[int, Any, dict[str, str]]:
        return self.request("GET", path, headers=headers)

    def post(
        self, path: str, body: Any = None, headers: dict[str, str] | None = None
    ) -> tuple[int, Any, dict[str, str]]:
        return self.request("POST", path, body={} if body is None else body, headers=headers)


@pytest.fixture
def client(app: App) -> Iterator[Client]:
    httpd = StudioServer(app)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        yield Client(app.settings.port)
    finally:
        httpd.shutdown()
        httpd.server_close()
