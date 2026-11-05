"""The records the research script wrote on 2026-11-04 load through the package, read-only, on the real tree."""

from __future__ import annotations

from pathlib import Path

import pytest

from reveal_studio.config import Settings, resolve_settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, read_json
from reveal_studio.jobs.records import records
from reveal_studio.jobs.store import job_dirs, load_job
from reveal_studio.media import pictures
from reveal_studio.runner.process import Runner
from reveal_studio.views.job import job_row, job_view, record_view
from reveal_studio.views.render import render_view

from .conftest import FLAGS, REPO, free_port

pytestmark = pytest.mark.integration

STUDIO_0411 = REPO / "benchmarks/runs/2026-11-04/studio"
JOBS = ("loop_angel_20261104-220708", "loop_angel_20261104-220719", "loop_angel_20261104-223204")
ADOPTED = "loop_angel_20261104-220708"
HIS_GRADE = "record that for angel page, options 2 and 3 are fine , close this effort"


class ReadOnlyRunner(Runner):
    """A runner that never reconciles: the owner's server owns the records of the real tree."""

    def reconcile(self, d: Path, rec: Json) -> Json:
        return rec


@pytest.fixture
def real(tmp_path: Path) -> Settings:
    if not STUDIO_0411.is_dir():
        pytest.skip(f"{STUDIO_0411} is absent: the records of 2026-11-04 are on the owner's laptop only")
    return resolve_settings(root=REPO, port=free_port(), lock=tmp_path / "lock", open_browser=False, env={})


def test_job_dirs_lists_the_three_jobs_of_2026_11_04(real: Settings) -> None:
    names = {d.name for d in job_dirs(real)}
    assert set(JOBS) <= names  # other agents may add jobs under 2026-11-05/studio/ today


def test_the_adopted_job_opens_with_round_1_and_his_grade(real: Settings) -> None:
    d, job = load_job(real, ADOPTED)
    assert (job["adopted"], job["root"], job["ui_version"]) == (
        True,
        "benchmarks/runs/2026-11-04/angel",
        "studio A1 2026-11-04",
    )
    v = job_view(ReadOnlyRunner(real, FLAGS), d, job)
    (r1,) = v["rounds"]
    assert (r1["n"], r1["grade"]["text"], r1["page_md5"]) == (1, HIS_GRADE, "72dadc4f5ea4db16152fe0c7062a3f94")
    assert [c["name"] for c in v["candidates"] if c["kind"] == "full"] == ["a1", "a2", "a3", "a4", "a5"]
    tiles = {s["name"]: s for s in v["stages"]}
    assert (tiles["grades"]["state"], tiles["registration"]["state"], tiles["page"]["state"]) == (
        "graded",
        "done",
        "done",
    )
    row = job_row(real, d)
    assert row is not None and (row["round"], row["graded"], row["candidates"]) == (1, True, 5)


def test_every_a1_record_loads_through_record_view(real: Settings) -> None:
    runner = ReadOnlyRunner(real, FLAGS)
    n = 0
    for name in JOBS:
        d = STUDIO_0411 / name
        for rec in records(d):
            if rec.get("ui_version") != "studio A1 2026-11-04":
                continue
            v = record_view(runner, d, rec)
            assert v["command"].startswith(f"{REPO}/.venv/bin/python scripts/research/loop_seq.py "), v["command"]
            assert isinstance(v["log_tail"], list) and v["progress"] is None
            assert v["state"] in ("done", "failed", "refused", "lost", "cancelled")
            n += 1
    assert n >= 17  # 17 records on 2026-11-05 (6 in 220719, 11 in 223204)


def test_a_render_with_its_own_frames_opens_read_only(real: Settings) -> None:
    d, job = load_job(real, "loop_angel_20261104-223204")
    v = render_view(real, d, job, "full", "a2")
    assert (v["md5_mp4"], v["frames_available"], v["has_frames"]) == ("c302623f293eacd069218fd7518e0967", 50, True)
    assert sum(1 for t in v["frames_tags"] if t["generated"]) == 24


def test_the_adopted_inputs_point_at_a_scratchpad_the_view_tolerates(
    real: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    d, job = load_job(real, ADOPTED)
    src = Path(job["inputs"][0]["path"])
    assert "/scratchpad/angel/raw/" in str(src)  # a session's scratchpad: alive today, gone after a reboot
    monkeypatch.setattr(pictures, "jpeg_thumb", lambda settings, s, dest, long=160: dest)  # write nothing
    try:
        dest = pictures.thumb_path(real, d, job, "raw", "0")
        assert src.exists() and dest.name == f"raw_0_{job['inputs'][0]['sha256'][:8]}.jpg"
    except StudioError as e:
        assert (e.code, str(e), src.exists()) == (404, "the original is not reachable", False)
    assert job_view(ReadOnlyRunner(real, FLAGS), d, job)["job"]["inputs"][0]["path"] == str(src)
    assert read_json(d / "job.json")["inputs"][0]["path"] == str(src)
