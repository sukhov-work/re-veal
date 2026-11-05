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
from reveal_studio.jobs import store
from reveal_studio.jobs.candidates import candidates, rounds, verdicts
from reveal_studio.jobs.grades import save_grade
from reveal_studio.jobs.records import records
from reveal_studio.jobs.rounds import open_round
from reveal_studio.jobs.store import (
    create_director_job,
    create_job,
    create_pair_job,
    find_job,
    job_dirs,
    job_root,
    list_stills,
    load_job,
    prep_dir,
)
from reveal_studio.registry import pair as pair_registry
from reveal_studio.registry.flows import ALL_FLOWS

from .conftest import HELPER, write_stills

PAIR_SPEC: Json = {
    "full": ["{root}/{seq}"],
    "draft": ["{root}/drafts/{seq}"],
    "terminal": "report.json",
    "mp4": "transition.mp4",
    "record_knobs": ["preset"],
    "fields": ["class", "method", "median_disp_px"],
}
"""A candidate spec of the shape registry/pair.py holds, fixed here so the spec reader's test holds whatever spec the
pair flow carries later."""


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
        ({"flow": "align"}, 400, "the flow is one of ["),
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


# ---------------------------------------------------------------- phase B's slice: the pair and director creators


def test_every_flow_writes_seq_into_job_json(settings: Settings, stills: Path, fixture_pair: str) -> None:
    """A job.json without `seq` makes GET /api/jobs answer 500 for every job (b_seams_research.md, key fact 1).
    Mutation: a creator that leaves `seq` out turns this red."""
    make_run_folder(settings)
    made = [
        create_job(settings, "loop", folder=str(stills), seq="tiny"),
        create_job(settings, "loop", adopt="benchmarks/runs/2026-11-04/myrun", seq="angel"),
        create_pair_job(settings, fixture=fixture_pair),
        create_pair_job(settings, a=f"fixtures/{fixture_pair}_S.jpg", b=f"fixtures/{fixture_pair}_F.jpg"),
        create_director_job(settings, fixture_pair),
    ]
    for j in made:
        on_disk = read_json(find_job(settings, j["id"]) / "job.json")
        assert on_disk == j and isinstance(j["seq"], str) and j["seq"], j["id"]
    assert [j["seq"] for j in made] == ["tiny", "angel", "tiny_1", "tiny_1_s_tiny_1_f", "tiny_1"]


def test_a_pair_job_links_the_two_photos_with_their_extensions(settings: Settings, fixture_pair: str) -> None:
    """Mutation: a link without the original's extension (transitions.py then picks no reader), a copied photo, or a
    missing sha256 turns this red."""
    fx = settings.fixtures
    before = {n: sha256_file(fx / n) for n in (f"{fixture_pair}_S.jpg", f"{fixture_pair}_F.jpg")}
    j = create_pair_job(settings, fixture=fixture_pair)
    d = find_job(settings, j["id"])
    assert j["id"].startswith("pair_tiny_1_") and (j["flow"], j["fixture"], j["adopted"]) == ("pair", "tiny_1", False)
    assert j["root"] == str(d.relative_to(settings.root))  # a pair's run folder is the job folder
    links = sorted((d / "raw" / "tiny_1").iterdir())
    assert [p.name for p in links] == ["A.jpg", "B.jpg"] and all(p.is_symlink() for p in links)
    assert [i["role"] for i in j["inputs"]] == ["A", "B"]
    assert [(i["name"], i["sha256"]) for i in j["inputs"]] == list(before.items())
    assert [Path(os.readlink(p)) for p in links] == [(fx / n).resolve() for n in before]
    assert {n: sha256_file(fx / n) for n in before} == before  # the originals untouched
    other = settings.root / "photos"
    other.mkdir()
    (other / "Start Photo.PNG").write_bytes((fx / f"{fixture_pair}_S.jpg").read_bytes())
    j2 = create_pair_job(settings, a=str(other / "Start Photo.PNG"), b=f"fixtures/{fixture_pair}_F.jpg")
    assert (j2["seq"], j2["fixture"]) == ("start_photo_tiny_1_f", None)
    assert [Path(i["link"]).name for i in j2["inputs"]] == ["A.PNG", "B.jpg"]


@pytest.mark.parametrize(
    ("kwargs", "code", "text"),
    [
        ({}, 400, "a pair job needs a fixture pair's name, or two photos a and b"),
        ({"a": "fixtures/tiny_1_S.jpg"}, 400, "a pair job needs"),
        ({"fixture": "nope_9"}, 404, "no fixture pair nope_9"),
        ({"fixture": "../x"}, 400, "a pair's name is letters"),
        ({"a": "fixtures/none.jpg", "b": "fixtures/tiny_1_F.jpg"}, 400, "photo A:"),
        ({"fixture": "tiny_1", "seq": "a b"}, 400, "the pair's name is letters"),
    ],
)
def test_a_pair_job_refuses_before_it_makes_a_folder(
    settings: Settings, fixture_pair: str, kwargs: Json, code: int, text: str
) -> None:
    with pytest.raises(StudioError) as e:
        create_pair_job(settings, **kwargs)
    assert (e.value.code, text in str(e.value)) == (code, True), str(e.value)
    assert not (settings.runs / "2026-11-05" / "studio").exists()


def test_a_director_job_counts_the_tables_and_mattes_and_hashes_the_helpers(
    settings: Settings, fixture_pair: str
) -> None:
    """Mutation: the matte count taken from every file of the folder (mattes.json and sheet.jpg counted, the 53 of
    mismatch_3_F), the missing ids not read from the layer table, or a helper left unhashed turns this red."""
    mf = settings.mattes_dir / f"{fixture_pair}_S"
    (mf / "mattes.json").write_text("{}")
    (mf / "sheet.jpg").write_bytes(b"x")
    j = create_director_job(settings, fixture_pair)
    d = find_job(settings, j["id"])
    assert j["id"].startswith("director_tiny_1_") and (j["flow"], j["seq"], j["pair"]) == (
        "director",
        "tiny_1",
        "tiny_1",
    )
    assert j["root"] == str((d / "run").relative_to(settings.root)) and (d / "run").is_dir()
    assert [(i["role"], Path(i["link"]).name) for i in j["inputs"]] == [("A", "A.jpg"), ("B", "B.jpg")]
    assert (j["layers_dir"], j["mattes_dir"]) == (
        "benchmarks/runs/2026-09-28/layers_v3",
        "benchmarks/runs/2026-10-17/mattes",
    )
    table = settings.layers_dir / "tiny_1_S" / "layers.json"
    assert j["tables"]["A"] == {
        "path": str(table.relative_to(settings.root)),
        "sha256": sha256_file(table),
        "elements": 3,
    }
    assert j["tables"]["B"]["elements"] == 3
    assert j["mattes"] == {"A": {"count": 2, "missing": [3]}, "B": {"count": 0, "missing": [1, 2, 3]}}
    assert j["helpers"] == [{"path": HELPER, "sha256": sha256_file(settings.root / HELPER)}]


def test_a_director_job_without_tables_or_mattes_still_opens(settings: Settings, fixture_pair: str) -> None:
    """The refusal for a missing root belongs to the resolve stage. Mutation: the import raising on a missing layer
    root turns this red."""
    gone = Settings(
        **{**settings.__dict__, "layers_dir": settings.root / "no-layers", "mattes_dir": settings.root / "x"}
    )
    j = create_director_job(gone, fixture_pair)
    assert j["tables"] == {"A": None, "B": None}
    assert j["mattes"] == {"A": {"count": 0, "missing": None}, "B": {"count": 0, "missing": None}}


@pytest.mark.parametrize(
    ("pair", "code", "text"),
    [
        ("mismatch_7", 400, "no plan under scripts/research/plans/ names the pair mismatch_7"),
        ("", 400, "a director job names its pair"),
        ("bad name", 400, "a director job names its pair"),
    ],
)
def test_a_director_job_needs_a_plan_and_makes_no_folder_without_one(
    settings: Settings, fixture_pair: str, pair: str, code: int, text: str
) -> None:
    with pytest.raises(StudioError) as e:
        create_director_job(settings, pair)
    assert (e.value.code, text in str(e.value)) == (code, True), str(e.value)
    assert not (settings.runs / "2026-11-05" / "studio").exists()


def test_create_job_refuses_a_flow_that_is_not_enabled(
    settings: Settings, fixture_pair: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """POST /api/jobs reaches create_job; the test disables the pair and director flows itself, so it holds once they
    are built. Mutation: create_job dispatching on ALL_FLOWS (a disabled flow's job then made from the page) turns
    this red."""
    monkeypatch.setattr(store, "FLOWS", {"loop": ALL_FLOWS["loop"]})
    for flow, kw in (("pair", {"fixture": fixture_pair}), ("director", {"pair": fixture_pair})):
        with pytest.raises(StudioError) as e:
            create_job(settings, flow, **kw)
        assert e.value.code == 400
        assert str(e.value) == "the flow is one of ['loop'] (pair and director are registered but not built yet)"
    assert not (settings.runs / "2026-11-05" / "studio").exists()


def pair_render(settings: Settings, d: Path, folder: Path, frames: int = 30) -> None:
    """A finished pair render in the shape transitions.py writes: transition.mp4, strip.jpg, report.json last."""
    folder.mkdir(parents=True)
    (folder / "transition.mp4").write_bytes(b"an mp4 " + folder.name.encode())
    (folder / "strip.jpg").write_bytes(b"jpg")
    report = {
        "class": "B",
        "method": "saliency-panzoom",
        "sparse_inliers": 0,
        "median_disp_px": 24.71,
        "mean_certainty": 0.5,
        "canvas": [480, 360],
        "n_frames": frames,
        "spec": {"seconds": 1.0, "fps": 30.0},
        "quality": {"flicker": {"edge_ratio": 0.132}},
    }
    write_json(folder / "report.json", report)


def test_the_spec_reader_lists_a_flows_renders_with_their_md5_and_numbers(
    settings: Settings, fixture_pair: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A flow's candidates come from the spec in its registry entry (here a fixed one). Mutation: the md5 taken from
    the folder instead of the record's outputs, the cache keyed without the mtime (a changed file keeps the old md5),
    or the report's numbers not copied, turns this red."""
    monkeypatch.setitem(pair_registry.FLOW, "candidates", PAIR_SPEC)
    j = create_pair_job(settings, fixture=fixture_pair)
    d = find_job(settings, j["id"])
    pair_render(settings, d, d / "tiny_1" / "r1")
    pair_render(settings, d, d / "drafts" / "tiny_1" / "d1", frames=12)
    (d / "tiny_1" / "r2.part").mkdir()  # a render still running
    rec = {
        "id": "20261105-120000_render",
        "stage": "render",
        "state": "done",
        "out_final": str((d / "tiny_1" / "r1").relative_to(settings.root)),
        "knobs": {"preset": "morph", "draft": 0},
        "outputs": [{"path": "x/transition.mp4", "md5": "the-records-md5"}],
        "started": "2026-11-05T12:00:00",
    }
    write_json(d / "stages" / rec["id"] / "stage.json", rec)
    assert [r["id"] for r in records(d)] == [rec["id"]]
    full, draft = candidates(settings, d, j)
    assert (full["kind"], full["name"], full["mp4"], full["md5_mp4"]) == (
        "full",
        "r1",
        "transition.mp4",
        "the-records-md5",
    )
    assert (full["frames"], full["seconds"], full["fps"], full["canvas"]) == (30, 1.0, 30.0, [480, 360])
    assert (full["class"], full["method"], full["median_disp_px"], full["preset"]) == (
        "B",
        "saliency-panzoom",
        24.71,
        "morph",
    )
    assert (full["unjudged"], full["unjudged_reason"], full["record"]) == (
        True,
        "no skeptic verdict for this candidate",
        rec["id"],
    )
    mp4 = d / "drafts" / "tiny_1" / "d1" / "transition.mp4"
    assert (draft["kind"], draft["draft"], draft["md5_mp4"], draft["record"]) == ("draft", 480, md5_file(mp4), None)
    (memo,) = (d / "cache" / "md5").iterdir()
    assert memo.read_text() == md5_file(mp4)
    mp4.write_bytes(b"changed")
    os.utime(mp4, ns=(1, 2))
    assert [c["md5_mp4"] for c in candidates(settings, d, j)][1] == md5_file(mp4)


def test_every_loop_candidate_names_its_mp4(settings: Settings, registered: tuple[Path, Json]) -> None:
    """Mutation: a loop candidate without `mp4` (frames_dir then opens nothing) turns this red."""
    d, j = registered
    write_json(job_root(settings, j) / "tiny" / "c1" / "measure.json", {"md5_mp4": "m1", "frames": 9})
    (c1,) = candidates(settings, d, j)
    assert c1["mp4"] == "loop.mp4"


def test_open_round_opens_a_round_on_a_page_the_studio_wrote(settings: Settings, fixture_pair: str) -> None:
    """The pair's page is written by the studio, not by a record. Mutation: page.md5 written into the job folder
    instead of beside the page (a director's page lives in run/) turns this red."""
    j = create_director_job(settings, fixture_pair)
    d = find_job(settings, j["id"])
    page = d / "run" / "index.html"
    page.write_text("<html>a page</html>\n")
    r = open_round(d, page, ["r1"])
    assert (d / "run" / "page.md5").read_text() == md5_file(page) + "\n" and not (d / "page.md5").exists()
    assert r == read_json(d / "rounds" / "1" / "round.json")
    assert {k: r[k] for k in ("n", "candidates", "variants", "page", "record", "override", "grade")} == {
        "n": 1,
        "candidates": ["r1"],
        "variants": [],
        "page": "index.html",
        "record": None,
        "override": None,
        "grade": None,
    }
    assert (d / "rounds" / "1" / "index.html").read_bytes() == page.read_bytes()
    assert open_round(d, page, ["r1", "r2"], variants=["r2", "r1"], override="on his word")["n"] == 2


PICKS: Json = {
    "date": "2026-11-05",
    "page": "director_tiny_1_r1",
    "best": {"tiny_1_r1": "c1-a"},
    "clips": {
        "tiny_1_r1_c1-a": {
            "acceptable": True,
            "note": "the square brightens too soon",
            "props": {"one_picture": True, "transforms": True, "not_invented": False},
            "frames": [47],
            "draft": True,
        }
    },
}


def test_the_picks_writer_saves_the_file_and_the_rounds_grade(settings: Settings, fixture_pair: str) -> None:
    """POST /api/jobs/<id>/picks with {round, picks, text}. Mutation: the round's grade keeping the picks object
    instead of the file's path, or a second save in the same second overwriting the first, turns this red."""
    j = create_director_job(settings, fixture_pair)
    d = find_job(settings, j["id"])
    (d / "run" / "index.html").write_text("<html>p</html>\n")
    r = open_round(d, d / "run" / "index.html", ["tiny_1_r1_c1-a"])
    g = save_grade(d, {"round": 1, "picks": PICKS, "text": "  his words  "})["grade"]
    assert list(g) == ["at", "page_md5", "picks", "text"]
    assert (g["page_md5"], g["text"]) == (r["page_md5"], "his words")
    assert g["picks"].startswith("picks/director_picks_") and read_json(d / g["picks"]) == PICKS
    g2 = save_grade(d, {"round": 1, "picks": PICKS})["grade"]
    assert g2["picks"] != g["picks"] and g2["text"] == "" and len(list((d / "picks").iterdir())) == 2
    assert read_json(d / "rounds" / "1" / "round.json")["grade"] == g2


@pytest.mark.parametrize(
    ("picks", "text"),
    [
        ({**PICKS, "extra": 1}, "picks keys must be exactly ['best', 'clips', 'date', 'page']"),
        ({k: v for k, v in PICKS.items() if k != "page"}, "picks keys must be exactly"),
        ([PICKS], "picks keys must be exactly"),
        ({**PICKS, "best": []}, "best and clips must be objects"),
        ({**PICKS, "clips": {"x": {"acceptable": True, "note": ""}}}, "clip x: keys ['acceptable', 'note']"),
        ({**PICKS, "clips": {"x": {"acceptable": True, "note": "", "props": {}, "colour": 1}}}, "clip x: keys"),
        (
            {**PICKS, "clips": {"x": {"acceptable": True, "note": "", "props": {"one_picture": 1, "transforms": 1}}}},
            "clip x: props must be exactly ['not_invented', 'one_picture', 'transforms']",
        ),
    ],
)
def test_the_picks_writer_refuses_another_shape(
    settings: Settings, fixture_pair: str, picks: object, text: str
) -> None:
    """The shape check of director_ui.py:688-707. Mutation: dropping the exact-keys check of the top or of props
    turns the matching row red."""
    j = create_director_job(settings, fixture_pair)
    d = find_job(settings, j["id"])
    (d / "run" / "index.html").write_text("<html>p</html>\n")
    open_round(d, d / "run" / "index.html", [])
    with pytest.raises(StudioError) as e:
        save_grade(d, {"round": 1, "picks": picks})
    assert (e.value.code, text in str(e.value)) == (400, True), str(e.value)
    assert not (d / "picks").exists() and read_json(d / "rounds" / "1" / "round.json")["grade"] is None


def test_the_loops_grade_text_keeps_its_shape(settings: Settings, tmp_path: Path) -> None:
    """Mutation: the text branch writing the picks shape (or `picks: null`) for a loop grade turns this red."""
    j = create_job(settings, "loop", folder=str(write_stills(tmp_path / "s")), seq="g")
    d = find_job(settings, j["id"])
    (d / "index.html").write_text("<html>p</html>\n")
    open_round(d, d / "index.html", ["c1"])
    g = save_grade(d, {"round": 1, "text": "c1 is fine"})["grade"]
    assert list(g) == ["text", "at", "page_md5"] and g["text"] == "c1 is fine"
