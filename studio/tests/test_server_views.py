"""The A2 stages and views over HTTP: the registration's windows and the fits table, the probe into the prep (a rerun
replaces it), a measure run under a render (a new folder, the render's own files untouched) with its stability
series, stalls and jumps in the render view, the graph's ports and lines, and the files the panels open."""

from __future__ import annotations

from pathlib import Path

import pytest

from reveal_studio.fs import md5_file
from reveal_studio.server.app import App

from .conftest import Client
from .test_server import new_job, rendered_job, run_stage


def render_files(root: Path) -> dict[str, str]:
    """The md5 of every file of the render's own folder (the measures/ subfolder aside)."""
    return {p.name: md5_file(p) for p in sorted(root.iterdir()) if p.is_file()}


def test_the_windows_reach_the_fits_table_and_windows_jpg(client: Client, stills: Path) -> None:
    jid = new_job(client, stills)
    rec = run_stage(client, jid, "registration", {"windows": "ring:10,10,30,30;rim:0,5,20,25"})
    assert rec["state"] == "done", rec
    assert rec["argv"][-2:] == ["--windows", "ring:10,10,30,30;rim:0,5,20,25"]
    view = client.get(f"/api/jobs/{jid}")[1]
    fits = view["prep"]["fits"]
    assert fits["names"] == ["ring", "rim"] and fits["fits"] == ["all", "final"] and fits["unmeasured"] == []
    rows = {r["name"]: r["cells"] for r in fits["frames"][0]["rows"]}
    assert rows["ring"]["final"]["dx"] == 1.4 and rows["rim"]["all"]["edge"] is True  # the rim touches frame 0's edge
    assert view["prep"]["windows"] == {"ring": [10, 10, 30, 30], "rim": [0, 5, 20, 25]}
    url = view["prep"]["windows_jpg"]
    assert url == f"/api/jobs/{jid}/file/in/tiny/windows.jpg"
    code, body, h = client.get(url)
    assert (code, h["content-type"]) == (200, "image/jpeg") and body[:4] == b"\x89PNG"  # the fake writes PNG bytes
    # An empty knob passes no flag: the next prep measures nothing and the panel draws no table.
    rec = run_stage(client, jid, "registration", {})
    assert "--windows" not in rec["argv"] and "previous prep moved" in rec["note"]
    view = client.get(f"/api/jobs/{jid}")[1]
    assert view["prep"]["fits"] is None and view["prep"]["windows_jpg"] is None


def test_a_malformed_window_is_refused_with_the_scripts_line(client: Client, stills: Path) -> None:
    jid = new_job(client, stills)
    rec = run_stage(client, jid, "registration", {"windows": "ring:10,10,12"})
    assert rec["state"] == "refused" and rec["reason"].startswith("FAILED: prep --windows: 'ring:10,10,12'")


def test_the_probe_runs_into_the_prep_and_a_rerun_replaces_its_folder(
    client: Client, stills: Path, settings_root: Path
) -> None:
    jid = rendered_job(client, stills)
    rec = run_stage(client, jid, "probe", {"long": 480, "pairs": "0,1"})
    assert rec["state"] == "done", rec
    view = client.get(f"/api/jobs/{jid}")[1]
    root = view["job"]["root"]
    prep = f"{root}/in/tiny"
    assert rec["argv"][2:] == ["probe", prep, "--out", f"{prep}/probe.part", "--long", "480", "--pairs", "0,1"]
    assert rec["out_final"] == f"{prep}/probe"
    assert [i["path"].rsplit("/", 1)[1] for i in rec["inputs"]] == ["prep.json", "k0.png", "k1.png"]
    tile = {s["name"]: s for s in view["stages"]}["probe"]
    assert (tile["state"], tile["detail"]) == ("done", "rife dexp 0.041 / 0.061 / 0.034 · 1 pair")
    assert (tile["parent"], tile["branch"], tile["optional"]) == ("registration", True, True)
    pair = view["probe"]["pairs"][0]
    for url in (pair["methods"][0]["strip"], pair["crops"][0]["a"], pair["crops"][0]["mid"][1]):
        code, _body, h = client.get(url)
        assert (code, h["content-type"]) == (200, "image/jpeg"), url
    marker = settings_root / rec["out_final"] / "left_by_the_first_run.txt"
    marker.write_text("x")
    # A rerun replaces the folder (the readers rule) and says nothing about "unchanged": the probe has no identity
    # files. Mutation: an IDENTITY entry for the probe marks the rerun unchanged and turns this red.
    rec2 = run_stage(client, jid, "probe", {})
    assert rec2["state"] == "done" and rec2.get("unchanged_from") is None and "--pairs" not in rec2["argv"]
    assert not marker.exists() and (marker.parent / "probe.json").is_file()
    assert client.get(f"/api/jobs/{jid}")[1]["probe"]["long"] == 960
    bad = run_stage(client, jid, "probe", {"pairs": "0,7"})
    assert bad["state"] == "refused" and bad["reason"].startswith("FAILED: probe --pairs")


def test_a_measure_writes_a_new_folder_under_the_render_and_never_its_files(client: Client, stills: Path) -> None:
    jid = rendered_job(client, stills)
    root = Path(client.get(f"/api/jobs/{jid}")[1]["job"]["root"])
    rec0 = client.get(f"/api/jobs/{jid}")[1]["stages"]
    render = next(s for s in rec0 if s["name"] == "render")
    out = client.get(f"/api/jobs/{jid}/stages/{render['latest']}")[1]["out_final"]
    assert out == f"{root}/tiny/c1"
    rec = run_stage(client, jid, "measure", {"render": "full:c1", "windows": "ring:10,10,30,30", "ref": 0})
    assert rec["state"] == "done", rec
    stamp = rec["id"].replace("_measure", "")
    assert rec["argv"][2:] == [
        "measure",
        f"{root}/tiny/c1/loop.mp4",
        "--out",
        f"{root}/tiny/c1/measures/{stamp}.part",
        "--frames-json",
        f"{root}/tiny/c1/frames.json",
        "--window",
        "ring:10,10,30,30",
        "--ref",
        "0",
    ]
    assert rec["out_final"] == f"{root}/tiny/c1/measures/{stamp}"
    assert [o["path"].rsplit("/", 1)[1] for o in rec["outputs"]] == ["measure.json"]
    rv = client.get(f"/api/jobs/{jid}/render/full/c1")[1]
    (run1,) = rv["measures"]
    assert (run1["record"], run1["windows"], run1["ref"]) == (rec["id"], {"ring": [10, 10, 30, 30]}, 0)
    st = rv["stability"]
    assert st["record"] == rec["id"] and len(st["series"]["ring"]) == 9 and st["max"]["ring"]["dy_max_at"] == 4
    # The fake's tiny render: step 4 (5.6, a rife frame into the hold of k1) is above 3 × the mean of 3.3 and 0.0.
    assert rv["frame_kinds"] == ["hold"] * 3 + ["generated"] * 2 + ["hold"] * 2 + ["blend"] * 2
    assert rv["stalls_and_jumps"] == {"stalls": [], "jumps": [4]}
    rec2 = run_stage(client, jid, "measure", {"render": "full:c1"})
    assert rec2["state"] == "done" and "--window" not in rec2["argv"]
    rv = client.get(f"/api/jobs/{jid}/render/full/c1")[1]
    assert [r["record"] for r in rv["measures"]] == [rec["id"], rec2["id"]]
    assert rv["stability"]["record"] == rec["id"]  # the latest run that measured windows
    tile = {s["name"]: s for s in client.get(f"/api/jobs/{jid}")[1]["stages"]}["measure"]
    assert tile["state"] == "done" and tile["detail"] == "2 runs; latest on c1" and tile["parent"] == "render"
    assert tile["thumb"] == f"/api/jobs/{jid}/thumb/render/full/c1"


def test_the_measure_leaves_the_renders_files_as_they_were(client: Client, stills: Path, settings_root: Path) -> None:
    jid = rendered_job(client, stills)
    root = settings_root / client.get(f"/api/jobs/{jid}")[1]["job"]["root"]
    before = render_files(root / "tiny" / "c1")
    assert run_stage(client, jid, "measure", {"render": "full:c1", "windows": "ring:10,10,30,30"})["state"] == "done"
    # Mutation: an out path at the render's own folder overwrites measure.json and turns this red.
    assert render_files(root / "tiny" / "c1") == before
    assert not list((root / "tiny" / "c1" / "measures").glob("*.part"))


def test_the_measure_refuses_what_it_cannot_measure(client: Client, stills: Path) -> None:
    jid = rendered_job(client, stills)
    for knobs, code, start in (
        ({}, 400, "choose the render to measure"),
        ({"render": "full:zz"}, 404, "no full render zz"),
        ({"render": "c1"}, 400, "choose the render to measure"),
    ):
        got, body, _ = client.post(f"/api/jobs/{jid}/stages/measure/run", {"knobs": knobs})
        assert (got, body["error"][: len(start)]) == (code, start), knobs
    rec = run_stage(client, jid, "measure", {"render": "full:c1", "windows": "ring:1,2"})
    assert rec["state"] == "refused" and rec["reason"].startswith("FAILED: measure --window")


def test_the_graph_joins_the_files_one_record_wrote_and_another_read(client: Client, stills: Path) -> None:
    jid = rendered_job(client, stills)
    assert run_stage(client, jid, "probe", {})["state"] == "done"
    assert run_stage(client, jid, "measure", {"render": "full:c1"})["state"] == "done"
    g = client.get(f"/api/jobs/{jid}")[1]["graph"]
    edges = {(e["from"], e["to"], e["file"]) for e in g["edges"]}
    # Mutation: matching producers by basename instead of path joins every loop.mp4 to every reader; matching only
    # the latest record of a stage loses the import's and the plan's lines (builtin stages write no record).
    assert edges == {
        ("import", "registration", "IMG_0001.jpg"),
        ("import", "registration", "IMG_0002.jpg"),
        ("registration", "render", "prep.json"),
        ("plan", "render", "tiny_a1.json"),
        ("registration", "probe", "prep.json"),
        ("registration", "probe", "k0.png"),
        ("registration", "probe", "k1.png"),
        ("render", "measure", "loop.mp4"),
        ("render", "measure", "frames.json"),
    }
    out = {p["name"]: p for p in g["ports"]["registration"]["out"]}
    assert set(out) == {"k0.png", "k1.png", "depth_k0.npy", "depth_k1.npy", "prep.json"}
    assert out["k0.png"]["url"] == f"/api/jobs/{jid}/file/in/tiny/k0.png" and "url" not in out["prep.json"]
    code, _body, h = client.get(out["k0.png"]["url"])
    assert (code, h["content-type"]) == (200, "image/png")
    assert [p["name"] for p in g["ports"]["import"]["out"]] == ["IMG_0001.jpg", "IMG_0002.jpg"]
    assert "url" not in g["ports"]["import"]["out"][0]  # an original outside the job: the viewer cannot open it


@pytest.fixture
def settings_root(app: App) -> Path:
    return app.settings.root
