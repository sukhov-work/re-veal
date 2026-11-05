"""Jobs: a new job from a folder (symlinks, sha256s, the sequence's name), an adopted run folder, find and load, the
still listing, and the candidates' rules."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, md5_file, read_json, sha256_file, write_json
from reveal_studio.jobs.candidates import candidates, rounds, verdicts
from reveal_studio.jobs.store import create_job, find_job, job_dirs, job_root, list_stills, load_job, prep_dir


def test_a_new_job_links_the_stills_in_order_and_hashes_them(settings: Settings, stills: Path) -> None:
    before = {p.name: sha256_file(p) for p in list_stills(stills)}
    j = create_job(settings, "loop", folder=str(stills))
    assert j["seq"] == "tiny_stills"  # the folder's name, lowercased, non-alphanumerics as underscores
    assert j["id"].startswith("loop_tiny_stills_")
    d = settings.root / j["root"]
    assert d.parent == settings.runs / "2026-11-05" / "studio"
    links = sorted((d / "raw" / "tiny_stills").iterdir())
    assert [p.name for p in links] == ["01.jpg", "02.jpg"]
    for link, inp in zip(links, j["inputs"], strict=True):
        assert link.is_symlink()
        assert Path(os.readlink(link)) == stills.resolve() / inp["name"]
        assert inp["sha256"] == before[inp["name"]]
        assert inp["bytes"] == (stills / inp["name"]).stat().st_size
    assert [i["name"] for i in j["inputs"]] == ["IMG_0001.jpg", "IMG_0002.jpg"]
    assert {p.name: sha256_file(p) for p in list_stills(stills)} == before  # originals untouched
    assert read_json(d / "job.json") == j
    assert (j["adopted"], j["flow"], j["ui_version"]) == (False, "loop", "reveal-studio 0.2.0")
    assert j["source_folder"] == str(stills.resolve())


def test_list_stills_reads_jpg_and_jpeg_only(tmp_path: Path) -> None:
    for name in ("a.JPG", "b.jpeg", "c.png", "d.HEIC", "e.ARW", ".f.jpg", "g.jpg.xmp"):
        (tmp_path / name).write_bytes(b"x")
    assert [p.name for p in list_stills(tmp_path)] == ["a.JPG", "b.jpeg"]


@pytest.mark.parametrize(
    ("kwargs", "code", "text"),
    [
        ({"flow": "align"}, 400, "the flow is one of ['loop']"),
        ({}, 400, "a new job needs a folder"),
        ({"folder": "/no/such/folder"}, 400, "is not a folder"),
        ({"seq": "bad name!"}, 400, "the sequence's name is letters"),
    ],
)
def test_create_job_refuses(settings: Settings, stills: Path, kwargs: Json, code: int, text: str) -> None:
    args: Json = {"flow": "loop", "folder": str(stills), **kwargs}
    if kwargs == {}:
        args["folder"] = None
    with pytest.raises(StudioError) as e:
        create_job(settings, args.pop("flow"), **args)
    assert e.value.code == code
    assert text in str(e.value)


def test_create_job_needs_two_developed_stills(settings: Settings, tmp_path: Path) -> None:
    one = tmp_path / "one"
    one.mkdir()
    (one / "a.jpg").write_bytes(b"x")
    (one / "b.png").write_bytes(b"x")
    with pytest.raises(StudioError, match=r"1 developed JPGs, need 2 or more .*convert HEIC or PNG"):
        create_job(settings, "loop", folder=str(one))


def test_a_relative_folder_is_read_from_the_root(settings: Settings, stills: Path) -> None:
    inside_root = settings.root / "photos"
    inside_root.mkdir()
    for p in list_stills(stills):
        (inside_root / p.name).write_bytes(p.read_bytes())
    j = create_job(settings, "loop", folder="photos", seq="rel")
    assert j["source_folder"] == str(inside_root)


def make_run_folder(settings: Settings, name: str = "myrun", seq: str = "angel") -> Path:
    """A run folder made before the studio: its prep, two full renders, a draft, a page and page.md5."""
    run = settings.runs / "2026-11-04" / name
    write_json(
        run / "in" / seq / "prep.json",
        {
            "seq": seq,
            "canvas": [64, 48],
            "frames": [{"method": "reference"}, {"method": "sift+magsac", "inliers": 99}],
            "sources": [
                {"source": "/gone/scratch/raw/1.jpg", "sha256": "a" * 64, "bytes": 10, "native": [640, 480]},
                {"source": "/gone/scratch/raw/2.jpg", "sha256": "b" * 64, "bytes": 11, "native": [640, 480]},
            ],
        },
    )
    for v in ("a1", "a2"):
        write_json(run / seq / v / "measure.json", {"md5_mp4": f"{v}md5", "frames": 50})
        write_json(run / seq / v / "plan.json", {"title": f"title {v}"})
    write_json(run / "drafts" / "a1" / "measure.json", {"md5_mp4": "d1", "frames": 50, "draft": 480})
    (run / "index.html").write_text("<html>the page the session built</html>\n")
    (run / "page.md5").write_text(md5_file(run / "index.html") + "  index.html\n")
    (run / "agents").mkdir()
    (run / "agents" / "skeptic1.md").write_text("judged")
    return run


def test_adopting_a_run_folder_opens_round_1_on_its_page(settings: Settings) -> None:
    run = make_run_folder(settings)
    j = create_job(settings, "loop", adopt="benchmarks/runs/2026-11-04/myrun", seq="angel")
    d = find_job(settings, j["id"])
    assert (j["adopted"], j["root"], j["adopted_from"]) == (True, "benchmarks/runs/2026-11-04/myrun", j["root"])
    assert [i["path"] for i in j["inputs"]] == ["/gone/scratch/raw/1.jpg", "/gone/scratch/raw/2.jpg"]
    assert job_root(settings, j) == run.resolve()
    (r1,) = rounds(d)
    assert r1["n"] == 1
    assert r1["candidates"] == ["a1", "a2"]
    assert r1["page_md5"] == r1["page_md5_recorded"] == md5_file(run / "index.html")
    assert (r1["grade"], r1["ungraded_by_his_word"], r1["override"]) == (None, None, None)
    assert (d / "rounds" / "1" / "index.html").read_bytes() == (run / "index.html").read_bytes()
    full = [c for c in candidates(settings, d, j) if c["kind"] == "full"]
    assert all("judged before it: skeptic1.md" in c["unjudged_reason"] for c in full)
    assert sorted(p.name for p in run.iterdir()) == ["agents", "angel", "drafts", "in", "index.html", "page.md5"]


@pytest.mark.parametrize(
    ("adopt", "seq", "code", "text"),
    [
        ("../outside", "angel", 400, "lies under benchmarks/runs/"),
        ("benchmarks/runs/2026-11-04/myrun", None, 400, "adopt needs the sequence's name"),
        ("benchmarks/runs/2026-11-04/myrun", "other", 404, "prep.json not found"),
    ],
)
def test_adopt_refuses(settings: Settings, adopt: str, seq: str | None, code: int, text: str) -> None:
    make_run_folder(settings)
    with pytest.raises(StudioError) as e:
        create_job(settings, "loop", adopt=adopt, seq=seq)
    assert (e.value.code, text in str(e.value)) == (code, True)


def test_find_and_load_a_job(settings: Settings, job: tuple[Path, Json]) -> None:
    d, j = job
    assert find_job(settings, j["id"]) == d
    assert load_job(settings, j["id"]) == (d, j)
    for bad, code in (("../x", 400), ("", 400), ("loop_none_1", 404)):
        with pytest.raises(StudioError) as e:
            find_job(settings, bad)
        assert e.value.code == code
    (d / "job.json").write_text("{not json")
    with pytest.raises(StudioError) as e:
        load_job(settings, j["id"])
    assert e.value.code == 500


def test_job_dirs_spans_dates_oldest_first(settings: Settings) -> None:
    for date, created in (("2026-11-06", "2026-11-06T09:00:00"), ("2026-11-01", "2026-11-01T09:00:00")):
        write_json(
            settings.runs / date / "studio" / f"job_{date}" / "job.json", {"id": f"job_{date}", "created": created}
        )
    assert [d.name for d in job_dirs(settings)] == ["job_2026-11-01", "job_2026-11-06"]


def test_candidates_skip_part_folders_and_folders_without_measures(
    settings: Settings, registered: tuple[Path, Json]
) -> None:
    d, j = registered
    root = job_root(settings, j)
    write_json(root / "tiny" / "c1" / "measure.json", {"md5_mp4": "m1", "frames": 9})
    write_json(root / "tiny" / "c2.part" / "measure.json", {"md5_mp4": "m2", "frames": 9})  # still running
    (root / "tiny" / "c3").mkdir()  # no measure.json yet
    write_json(root / "drafts" / "tiny" / "c1d" / "measure.json", {"md5_mp4": "m4", "frames": 9, "draft": 480})
    names = [(c["kind"], c["name"]) for c in candidates(settings, d, j)]
    assert names == [("full", "c1"), ("draft", "c1d")]
    c1 = candidates(settings, d, j)[0]
    assert (c1["unjudged"], c1["unjudged_reason"]) == (True, "no skeptic verdict for this candidate")


def test_verdicts_merge_in_time_order_and_judge_one_md5(settings: Settings, registered: tuple[Path, Json]) -> None:
    d, j = registered
    write_json(job_root(settings, j) / "tiny" / "c1" / "measure.json", {"md5_mp4": "m1", "frames": 9})
    write_json(
        d / "answers" / "skeptic_20261105-100000.json",
        {"at": "t1", "candidates": {"c1": {"verdict": "NOT READY", "judged_md5": "m1"}}},
    )
    write_json(
        d / "answers" / "skeptic_20261105-110000.json",
        {"at": "t2", "candidates": {"c1": {"verdict": "READY", "judged_md5": "m0"}, "x": {"verdict": "MAYBE"}}},
    )
    v = verdicts(d)
    assert set(v) == {"c1"}
    assert (v["c1"]["verdict"], v["c1"]["from"]) == ("READY", "skeptic_20261105-110000.json")
    (c1,) = [c for c in candidates(settings, d, j) if c["kind"] == "full"]
    assert c1["unjudged"] is True  # the verdict was given on another md5
    assert c1["unjudged_reason"] == "the render changed after the verdict (judged md5 differs)"


def test_prep_dir_is_in_seq_of_the_run_folder(settings: Settings, job: tuple[Path, Json]) -> None:
    d, j = job
    assert prep_dir(settings, j) == d / "in" / "tiny"
    assert json.loads((d / "job.json").read_text())["root"] == str(d.relative_to(settings.root))
