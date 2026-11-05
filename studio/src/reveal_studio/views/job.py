"""The job as the page reads it: the strip's stage tiles (with the stale rule), the rail's row, the view, a record.

The tiles come from each flow's table of tile functions (views/tiles_loop.py, views/pair.py, views/director.py) over
the base tile of views/base.py; the job view is the keys every flow shares plus the flow's own (its `extras`).
"""

from __future__ import annotations

from pathlib import Path

from reveal_studio.config import Settings
from reveal_studio.fs import Json, inside, md5_file, read_json, rel
from reveal_studio.jobs.candidates import candidates, requests_of, rounds
from reveal_studio.jobs.grades import owner_frames
from reveal_studio.jobs.plans import plans_of
from reveal_studio.jobs.records import elapsed_of, progress_of, record_detail, records
from reveal_studio.jobs.store import job_root
from reveal_studio.registry.flows import flow_def
from reveal_studio.runner.process import Runner
from reveal_studio.views import director, pair, tiles_loop
from reveal_studio.views.base import ExtrasFn, TileContext, TileFn, base_tile, mark_stale
from reveal_studio.views.measures import probe_view
from reveal_studio.views.tiles_loop import prep_summary, readers_summary

IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")
TILES: dict[str, dict[str, TileFn]] = {"loop": tiles_loop.TILES, "pair": pair.TILES, "director": director.TILES}
"""Each flow's tile functions by stage name; a stage without one shows its base tile."""
EXTRAS: dict[str, ExtrasFn] = {"loop": tiles_loop.extras, "pair": pair.extras, "director": director.extras}
"""Each flow's own keys on the job view."""


def stage_views(runner: Runner, d: Path, job: Json) -> list[Json]:
    """One tile per stage of the job's flow: state, detail, wall time, thumbnail, history, stale and generated."""
    by: dict[str, list[Json]] = {}
    for r in [runner.reconcile(d, r) for r in records(d)]:
        by.setdefault(r["stage"], []).append(r)
    ctx = TileContext(runner.settings, d, job, by)
    stages: list[Json] = flow_def(job["flow"])["stages"]
    table = TILES.get(job["flow"], {})
    views: list[Json] = []
    for s in stages:
        hist = by.get(s["name"], [])
        v = base_tile(d, s, hist)
        fn = table.get(s["name"])
        if fn is not None:
            fn(ctx, v, hist[-1] if hist else None)
        views.append(v)
    mark_stale(views, stages, by)
    return views


def _port(settings: Settings, d: Path, job: Json, path: str) -> Json:
    """A node's port: the file's name and path, and the URL the viewer opens when it is an image of the job."""
    p = Path(path)
    out: Json = {"name": p.name, "path": path}
    full = p if p.is_absolute() else settings.root / p
    if p.suffix.lower() in IMAGE_SUFFIXES:
        for base in (job_root(settings, job), d):
            if inside(full, base):
                out["url"] = f"/api/jobs/{job['id']}/file/{rel(full, base)}"
                break
    return out


def graph_view(settings: Settings, d: Path, job: Json, recs: list[Json]) -> Json:
    """The graph view's ports and lines: {"ports": {stage: {"in": [port], "out": [port]}}, "edges": [{from, to,
    file}]}. A stage's ports are the files its latest done record (else its latest record) read and wrote; the
    import's are the originals and the plan's the plan files a render read, since builtin stages write no record. A
    line joins a file one record wrote, matched by path, to the stage whose latest record read it."""
    latest: dict[str, Json] = {}
    for r in recs:
        latest[r["stage"]] = r
    used = {
        s: next((r for r in reversed(recs) if r["stage"] == s and r.get("state") == "done"), latest[s]) for s in latest
    }
    originals = [i["path"] for i in job.get("inputs") or [] if i.get("path")]
    plans = sorted(
        {
            i["path"]
            for r in recs
            if r["stage"] == "render"
            for i in r.get("inputs") or []
            if str(i.get("path", "")).endswith(".json") and not str(i["path"]).endswith("prep.json")
        }
    )
    ports: dict[str, Json] = {
        "import": {"in": [], "out": [_port(settings, d, job, p) for p in originals]},
        "plan": {"in": [], "out": [_port(settings, d, job, p) for p in plans]},
    }
    writer: dict[str, str] = dict.fromkeys(originals, "import") | dict.fromkeys(plans, "plan")
    for r in recs:
        if r.get("state") == "done":
            writer.update({o["path"]: r["stage"] for o in r.get("outputs") or [] if o.get("path")})
    edges: list[Json] = []
    seen: set[tuple[str, str, str]] = set()
    for name, r in used.items():
        ins = [i["path"] for i in r.get("inputs") or [] if i.get("path")]
        outs = [o["path"] for o in r.get("outputs") or [] if o.get("path")]
        ports[name] = {
            "in": [_port(settings, d, job, p) for p in ins],
            "out": [_port(settings, d, job, p) for p in outs],
        }
        for p in ins:
            key = (writer.get(p, ""), name, Path(p).name)
            if key[0] and key[0] != name and key not in seen:
                seen.add(key)
                edges.append({"from": key[0], "to": name, "file": key[2]})
    return {"ports": ports, "edges": edges}


def job_view(runner: Runner, d: Path, job: Json) -> Json:
    """GET /api/jobs/<id>: the job, its stages (reconciled), candidates, plans, requests, rounds, the loop's prep,
    readers and probe (None for a job of another flow: the page's shared scripts read them), the graph, the page, and
    the flow's own keys (the loop's frozen plans; a pair's or a director's keys from its view module)."""
    settings = runner.settings
    cands = candidates(settings, d, job)
    for c in cands:
        c.pop("dir", None)
    page = job_root(settings, job) / "index.html"
    v: Json = {
        "job": job,
        "stages": stage_views(runner, d, job),
        "candidates": cands,
        "plans": plans_of(settings, d),
        "frozen_plans": [],
        "requests": requests_of(settings, d),
        "rounds": rounds(d),
        "prep": prep_summary(settings, job),
        "readers": readers_summary(settings, job),
        "probe": probe_view(settings, job),
        "graph": graph_view(settings, d, job, records(d)),
        "page": {
            "exists": page.exists(),
            "md5": md5_file(page) if page.exists() else None,
            "url": f"/api/jobs/{job['id']}/file/index.html",
        },
        "owner_frames": owner_frames(d),
        "script_flags": runner.flags.as_dict(),
    }
    extras = EXTRAS.get(job["flow"])
    if extras is not None:
        v.update(extras(settings, d, job))
    return v


def running_entry(d: Path, rec: Json) -> Json:
    """A running record as the rail's Running list prints it: "render · a2 · 12/50 · 38 s"."""
    knobs = rec.get("knobs") or {}
    return {
        "id": rec["id"],
        "stage": rec["stage"],
        "name": knobs.get("name") or knobs.get("render"),
        "elapsed_s": elapsed_of(rec),
        "progress": progress_of(d / "stages" / rec["id"]),
    }


def job_row(settings: Settings, d: Path, runner: Runner | None = None) -> Json | None:
    """The rail's row for one job: the last render's state, the candidates, the round and the running records.

    With the Runner, a running record whose process is gone is reconciled first, as the job view does (STUDIO.md §4:
    on every read), so a record left running by a dead wait thread does not show as running in the rail.
    """
    job: Json = read_json(d / "job.json") or {}
    if not job:
        return None
    recs = records(d)
    if runner is not None:
        recs = [runner.reconcile(d, r) for r in recs]
    running = [running_entry(d, r) for r in recs if r["state"] == "running"]
    cands = candidates(settings, d, job)
    full = [c for c in cands if c["kind"] == "full"]
    rs = rounds(d)
    last_render = next((r for r in reversed(recs) if r["stage"] == "render"), None)
    last_state = last_render["state"] if last_render else ("done" if full else "none")
    if cands and last_state in ("failed", "refused", "lost", "cancelled"):
        last_state = "done"  # as the render tile: the row says what the job holds, drafts included
    source = (
        Path(job["source_folder"]).name
        if job.get("source_folder")
        else ("adopted: " + Path(job.get("adopted_from", "")).name if job.get("adopted") else None)
    )
    return {
        "id": job["id"],
        "flow": job["flow"],
        "seq": job["seq"],
        "created": job["created"],
        "adopted": job.get("adopted", False),
        "root": job["root"],
        "source": source,
        "stills": len(job.get("inputs", [])),
        "candidates": len(full),
        "unjudged": sum(1 for c in full if c["unjudged"]),
        "round": rs[-1]["n"] if rs else 0,
        "graded": bool(rs and rs[-1].get("grade")),
        "ungraded_by_his_word": bool(rs and rs[-1].get("ungraded_by_his_word")),
        "last_render": last_state,
        "last_attempt": last_render["state"] if last_render and last_render["state"] != last_state else None,
        "running": running,
    }


def record_view(runner: Runner, d: Path, rec: Json) -> Json:
    """GET /api/jobs/<id>/stages/<rid>: the record reconciled first, then its progress, log tail and command."""
    return record_detail(d, runner.reconcile(d, rec))
