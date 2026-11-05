"""The job as the page reads it: the strip's stage tiles (with the stale rule), the rail's row, the view, a record."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from reveal_studio.config import Settings
from reveal_studio.fs import Json, inside, md5_file, read_json, rel
from reveal_studio.jobs.candidates import candidates, requests_of, rounds, verdicts
from reveal_studio.jobs.grades import owner_frames
from reveal_studio.jobs.plans import frozen_plans, plans_of
from reveal_studio.jobs.records import elapsed_of, progress_of, record_detail, records
from reveal_studio.jobs.store import job_root, prep_dir
from reveal_studio.registry.loop import FLOWS
from reveal_studio.runner.process import Runner
from reveal_studio.views.fits import fits_summary
from reveal_studio.views.measures import measure_runs, probe_view

IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")


def prep_summary(settings: Settings, job: Json) -> Json | None:
    """The registration record (prep.json) as the registration panel shows it, or None before a prep exists."""
    p = read_json(prep_dir(settings, job) / "prep.json")
    if not p:
        return None
    frames = []
    for i, r in enumerate(p.get("frames", [])):
        frames.append(
            {
                "i": i,
                "method": r.get("method"),
                "trusted": r.get("trusted"),
                "inliers": r.get("inliers"),
                "matches": r.get("matches"),
                "residual_px": r.get("residual_px", r.get("rmse")),
                "cc": r.get("cc"),
                "scale_to_canvas": r.get("scale_to_canvas"),
                "lock": r.get("lock"),
                "depth_blend": bool(r.get("depth_blend")),
            }
        )
    return {
        "date": p.get("date"),
        "long": p.get("long"),
        "reference": p.get("reference"),
        "reference_size": p.get("reference_size"),
        "crop": p.get("crop"),
        "canvas": p.get("canvas"),
        "cuts": p.get("cuts"),
        "bg_depth": p.get("bg_depth"),
        "min_inliers": p.get("min_inliers"),
        "ecc_refine": p.get("ecc_refine"),
        "ref_requested": p.get("ref_requested"),
        "lock_window": p.get("lock_window"),
        "depth_maps": sorted(q.name for q in prep_dir(settings, job).glob("depth_k*.npy")),
        "windows": p.get("windows"),
        "fits": fits_summary(p),
        "windows_jpg": (
            f"/api/jobs/{job['id']}/file/{rel(prep_dir(settings, job), job_root(settings, job))}/windows.jpg"
            if (prep_dir(settings, job) / "windows.jpg").exists()
            else None
        ),
        "frames": frames,
        "n": len(frames),
        "sources": [
            {
                "name": Path(s["source"]).name,
                "sha256": s["sha256"],
                "native": s.get("native"),
                "scaled": s.get("scaled"),
            }
            for s in p.get("sources", [])
        ],
    }


def readers_summary(settings: Settings, job: Json) -> Any:
    """readers.json as `loop_seq.py readers` wrote it beside the prep, or None."""
    return read_json(prep_dir(settings, job) / "readers" / "readers.json")


def attempt_note(rec: Json) -> str:
    """The panel head's muted line when a tile says what the stage holds while its latest record did not finish: the
    attempt's state and reason, so the head never shows "done" beside a bare "cancelled by you" (critique A2, P2 4)."""
    state, reason = rec["state"], rec.get("reason") or ""
    if not reason:
        return f"last attempt {state}"
    return f"last attempt: {reason}" if reason.startswith(state) else f"last attempt {state}: {reason}"


def is_draft(rec: Json) -> bool:
    """A render record of a draft (knob draft above 0): its output goes under drafts/, never onto a page."""
    try:
        return int((rec.get("knobs") or {}).get("draft") or 0) > 0
    except (TypeError, ValueError):
        return False


def readers_moved(settings: Settings, job: Json, latest: Json) -> str | None:
    """Where the readers' folder went when a registration after the readers record moved the prep aside to
    in/<seq>_prev_<stamp>/: the first such folder that holds readers/readers.json, relative to the job root."""
    prep = prep_dir(settings, job)
    since = str(latest["id"]).split("_", 1)[0]  # the record id starts with its stamp, YYYYMMDD-HHMMSS
    for p in sorted(prep.parent.glob(prep.name + "_prev_*")):
        if p.name.rsplit("_prev_", 1)[1] >= since and (p / "readers" / "readers.json").is_file():
            return rel(p / "readers", job_root(settings, job))
    return None


def _probe_tile(v: Json, pv: Json | None, latest: Json | None) -> None:
    """The probe's tile: RIFE's double-exposure share at the three t of the first pair, the pairs, the first strip."""
    if pv and not latest:
        v["state"] = "done"  # a probe folder written from the shell
    if not pv:
        if not latest:
            v["detail"] = "optional, not run"
        return
    rife = [m for p in pv["pairs"] for m in p["methods"] if m["method"] == "rife"]
    shares = [f.get("dexp") for f in rife[0]["frames"]] if rife else []
    head = "rife dexp " + " / ".join(f"{x:.3f}" if isinstance(x, (int, float)) else "—" for x in shares)
    n = len(pv["pairs"])
    v["detail"] = (head if rife else "rife skipped") + f" · {n} pair" + ("s" if n != 1 else "")
    v["thumb"] = next((m["strip"] for p in pv["pairs"] for m in p["methods"] if m["strip"]), None)


def _measure_tile(v: Json, job: Json, runs: list[tuple[Json, Json]], latest: Json | None) -> None:
    """The measure's tile: the runs over every candidate and the latest one's first window, the render it measured."""
    if not runs:
        if not latest:
            v["detail"] = "optional, not run"
        return
    if not latest or latest["state"] in ("failed", "refused", "lost", "cancelled"):
        if latest:
            v["last_attempt"] = latest["state"]
            v["reason"] = attempt_note(latest)
        v["state"] = "done"  # the tile says what the stage holds; a failed attempt is beside it
    c, r = max(runs, key=lambda x: x[1]["at"])
    peak = next(iter(r["stability_max"].items()), None)
    v["detail"] = f"{len(runs)} run" + ("s" if len(runs) != 1 else "") + f"; latest on {c['name']}"
    if peak and isinstance(peak[1], dict):
        v["detail"] += f": {peak[0]} dx {peak[1].get('dx_max')} dy {peak[1].get('dy_max')} px"
    if v.get("last_attempt"):
        v["detail"] += f" · last attempt {v['last_attempt']}"
    v["thumb"] = f"/api/jobs/{job['id']}/thumb/render/{c['kind']}/{c['name']}"


def stage_views(runner: Runner, d: Path, job: Json) -> list[Json]:
    """One tile per stage of the job's flow: state, detail, wall time, thumbnail, history, stale and generated."""
    settings = runner.settings
    recs = [runner.reconcile(d, r) for r in records(d)]
    by: dict[str, list[Json]] = {}
    for r in recs:
        by.setdefault(r["stage"], []).append(r)
    root = job_root(settings, job)
    cands = candidates(settings, d, job)
    full = [c for c in cands if c["kind"] == "full"]
    drafts = [c for c in cands if c["kind"] == "draft"]
    reqs = requests_of(settings, d)
    rs = rounds(d)
    pl = plans_of(settings, d)
    prep = prep_summary(settings, job)
    views: list[Json] = []
    latest_started: dict[str, str] = {}
    for s in FLOWS[job["flow"]]["stages"]:
        name = s["name"]
        hist = by.get(name, [])
        latest = hist[-1] if hist else None
        v: Json = {
            "name": name,
            "title": s["title"],
            "kind": s["kind"],
            "optional": s["optional"],
            "parent": s.get("parent"),
            "branch": bool(s.get("branch")),
            "what": s["what"],
            "backend": s.get("backend"),
            "knobs": s["knobs"],
            "state": "none",
            "detail": "",
            "wall_s": None,
            "thumb": None,
            "latest": latest["id"] if latest else None,
            "history": [
                {
                    "id": r["id"],
                    "state": r["state"],
                    "started": r["started"],
                    "wall_s": r.get("wall_s"),
                    "reason": r.get("reason"),
                }
                for r in hist
            ],
            "stale": False,
            "generated": False,
            "progress": None,
            "reason": None,
        }
        if latest:
            v["state"] = latest["state"]
            v["wall_s"] = latest.get("wall_s")
            v["reason"] = latest.get("reason")
            v["unchanged_from"] = latest.get("unchanged_from")
            v["latest_knobs"] = latest.get("knobs") or {}
            if latest["state"] == "running":
                v["progress"] = progress_of(d / "stages" / latest["id"])
            latest_started[name] = latest["started"]
        if name == "import":
            v["state"] = "done"
            v["detail"] = f"{len(job['inputs'])} stills" + (" (adopted)" if job.get("adopted") else "")
            v["thumb"] = (
                f"/api/jobs/{job['id']}/thumb/still/0"
                if prep
                else (f"/api/jobs/{job['id']}/thumb/raw/0" if job["inputs"] else None)
            )
        elif name == "registration":
            if prep:
                if not latest:
                    v["state"] = "done"
                    v["detail"] = "adopted"
                regs = [
                    f"k{f['i']} {f['method']}" + (f" {f['inliers']} inl." if f.get("inliers") else "")
                    for f in prep["frames"][1:]
                ]
                v["detail"] = "; ".join(regs)[:160] + f" · {prep['canvas'][0]}×{prep['canvas'][1]}"
                v["thumb"] = f"/api/jobs/{job['id']}/thumb/still/0"
            elif not latest:
                v["state"] = "none"
                v["detail"] = "not run"
        elif name == "readers":
            rd = readers_summary(settings, job)
            if rd and not latest:
                v["state"] = "done"
                v["detail"] = "adopted"
            if rd:
                pairs = rd.get("pairs") or []
                v["detail"] = (
                    ("Lab>14 " + ", ".join(f"{p.get('lab_above_14', 0):.1%}" for p in pairs))
                    if pairs
                    else f"{len(rd.get('stills', []))} stills read"
                )
            elif latest and latest["state"] == "done":
                # a later registration moved the prep, and the readers' folder inside it, aside
                v["moved_to"] = readers_moved(settings, job, latest)
                v["detail"] = "moved with the previous prep" if v["moved_to"] else "readers.json is not in this prep"
            elif not latest:
                v["state"] = "none"
                v["detail"] = "optional, not run"
        elif name == "probe":
            _probe_tile(v, probe_view(settings, job), latest)
        elif name == "measure":
            _measure_tile(v, job, [(c, r) for c in cands for r in measure_runs(settings, d, c)], latest)
        elif name == "plan":
            v["state"] = "saved" if pl else "none"
            v["detail"] = (
                f"{len(pl)} saved in this job; {len(frozen_plans(settings))} frozen"
                if pl
                else "none saved; frozen plans available"
            )
        elif name == "render":
            unj = [c["name"] for c in full if c["unjudged"]]
            v["detail"] = f"{len(full)} full, {len(drafts)} drafts" + (f"; unjudged: {', '.join(unj)}" if unj else "")
            if latest and latest["state"] in ("failed", "refused", "lost", "cancelled") and (full or drafts):
                v["last_attempt"] = f"{latest['state']}: {(latest.get('knobs') or {}).get('name', latest['id'])}"
                v["detail"] += f" · last attempt {v['last_attempt']}"
                v["reason"] = attempt_note(latest)
                v["state"] = "done"  # the tile says what the stage holds; the attempt is beside it
            if not latest and full:
                v["state"] = "done"
            pick = full or drafts
            if pick:
                last = sorted(pick, key=lambda c: c["mtime"])[-1]
                v["thumb"] = f"/api/jobs/{job['id']}/thumb/render/{last['kind']}/{last['name']}"
                v["generated"] = any((c.get("generated_share") or 0) > 0 for c in full)
        elif name == "skeptic":
            sk = [r for r in reqs if r["kind"] == "skeptic"]
            if sk:
                last = sk[-1]
                v["state"] = "answered" if last["answered"] else "waiting"
                v["detail"] = (
                    f"{last['name']} · {last['age_s']} s old" if not last["answered"] else f"{last['name']} answered"
                )
                v["wall_s"] = None
            else:
                v["detail"] = "no request yet"
            v["verdicts"] = verdicts(d)
        elif name == "page":
            page = root / "index.html"
            if page.exists():
                if not latest:
                    v["state"] = "done"
                v["detail"] = f"md5 {md5_file(page)[:8]}… · round {rs[-1]['n'] if rs else '—'}"
                v["page"] = f"/api/jobs/{job['id']}/file/index.html"
            elif not latest:
                v["detail"] = "not built"
        elif name == "grades":
            if rs:
                last = rs[-1]
                v["state"] = (
                    "graded"
                    if last.get("grade")
                    else ("ungraded by his word" if last.get("ungraded_by_his_word") else "ungraded")
                )
                v["detail"] = f"round {last['n']}: " + (
                    last["grade"]["text"][:120] if last.get("grade") else v["state"]
                )
            else:
                v["detail"] = "no round yet"
        views.append(v)
    # stale: an earlier stage's latest record started after this stage's latest record. A branch (probe, measure)
    # writes into its own folder that no stage reads, so it makes no stage stale, and it goes stale only after the
    # stages its `stale_after` names (the probe after a registration; a measure of a finished mp4 never). The page
    # lists full renders only, so its upstream render is the latest full render's record, never a draft's (T98).
    defs = {s["name"]: s for s in FLOWS[job["flow"]]["stages"]}
    full_renders = [r for r in by.get("render", []) if not is_draft(r)]
    for i, v in enumerate(views):
        if v["state"] not in ("done",) or not v["latest"]:
            continue
        mine = latest_started.get(v["name"])
        after = defs[v["name"]].get("stale_after")
        ups = (
            [u for u in views if u["name"] in after]
            if after is not None
            else [u for u in views[:i] if not defs[u["name"]].get("branch")]
        )
        for u in ups:
            up = by.get(u["name"], [{}])[-1]
            if v["name"] == "page" and u["name"] == "render":
                up = full_renders[-1] if full_renders else {}
            if u["kind"] == "script" and up.get("started", "") > (mine or "") and up.get("state") == "done":
                v["stale"] = True
                v["stale_after"] = u["name"]
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
    """GET /api/jobs/<id>: the job, its stages (reconciled), candidates, plans, requests, rounds, prep and readers."""
    settings = runner.settings
    cands = candidates(settings, d, job)
    for c in cands:
        c.pop("dir", None)
    page = job_root(settings, job) / "index.html"
    return {
        "job": job,
        "stages": stage_views(runner, d, job),
        "candidates": cands,
        "plans": plans_of(settings, d),
        "frozen_plans": frozen_plans(settings),
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
