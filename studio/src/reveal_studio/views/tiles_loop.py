"""The loop flow's stage tiles, one function per stage (phase B's slice moved them out of views/job.stage_views,
2026-11-05; tests/test_loop_snapshot.py pins the tiles of two jobs), and the loop's prep and readers summaries.

Each tile function takes the context, the stage's base tile and its latest record, and fills the tile in place.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from reveal_studio.config import Settings
from reveal_studio.fs import Json, md5_file, read_json, rel
from reveal_studio.jobs.candidates import verdicts
from reveal_studio.jobs.plans import frozen_plans
from reveal_studio.jobs.store import job_root, prep_dir
from reveal_studio.views.base import TileContext, TileFn, attempt_note
from reveal_studio.views.fits import fits_summary
from reveal_studio.views.measures import measure_runs, probe_view

SO_FAR = 6
"""The longest sequence of the loops work before the studio (evgen-thug, 6 stills, 2026-10-30; b_pair_research.md
Part 4). The chip's threshold stays 6: the boxes' seven stills of 2026-11-05 were the first above it, through the
studio (b_loop_build.md)."""
DESIGN_RANGE = (2, 10)
"""Stills per sequence in the design of record (STUDIO.md §1); no script states a limit, so neither refuses."""


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


def readers_moved(settings: Settings, job: Json, latest: Json) -> str | None:
    """Where the readers' folder went when a registration after the readers record moved the prep aside to
    in/<seq>_prev_<stamp>/: the first such folder that holds readers/readers.json, relative to the job root."""
    prep = prep_dir(settings, job)
    since = str(latest["id"]).split("_", 1)[0]  # the record id starts with its stamp, YYYYMMDD-HHMMSS
    for p in sorted(prep.parent.glob(prep.name + "_prev_*")):
        if p.name.rsplit("_prev_", 1)[1] >= since and (p / "readers" / "readers.json").is_file():
            return rel(p / "readers", job_root(settings, job))
    return None


def _prep(ctx: TileContext) -> Json | None:
    prep: Json | None = ctx.once("prep", lambda: prep_summary(ctx.settings, ctx.job))
    return prep


def still_count_warnings(n: int) -> list[Json]:
    """The import's chips for a long sequence: a hint, never a refusal (no script states a limit)."""
    out: list[Json] = []
    if n > SO_FAR:
        out.append(
            {
                "key": "chip.above_6",
                "text": f"above the longest sequence of the loops work before the studio ({SO_FAR})",
            }
        )
    if n > DESIGN_RANGE[1]:
        out.append(
            {
                "key": "chip.above_10",
                "text": f"above the design's range of {DESIGN_RANGE[0]} to {DESIGN_RANGE[1]} stills",
            }
        )
    return out


def tile_import(ctx: TileContext, v: Json, latest: Json | None) -> None:
    job = ctx.job
    v["state"] = "done"
    v["detail"] = f"{len(job['inputs'])} stills" + (" (adopted)" if job.get("adopted") else "")
    v["thumb"] = (
        f"/api/jobs/{job['id']}/thumb/still/0"
        if _prep(ctx)
        else (f"/api/jobs/{job['id']}/thumb/raw/0" if job["inputs"] else None)
    )
    warnings = still_count_warnings(len(job["inputs"]))
    if warnings:  # only then: the tile of a sequence of 6 stills or fewer keeps its keys
        v["warnings"] = warnings


def tile_registration(ctx: TileContext, v: Json, latest: Json | None) -> None:
    job, prep = ctx.job, _prep(ctx)
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


def tile_readers(ctx: TileContext, v: Json, latest: Json | None) -> None:
    rd = readers_summary(ctx.settings, ctx.job)
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
        v["moved_to"] = readers_moved(ctx.settings, ctx.job, latest)
        v["detail"] = "moved with the previous prep" if v["moved_to"] else "readers.json is not in this prep"
    elif not latest:
        v["state"] = "none"
        v["detail"] = "optional, not run"


def tile_probe(ctx: TileContext, v: Json, latest: Json | None) -> None:
    """The probe's tile: RIFE's double-exposure share at the three t of the first pair, the pairs, the first strip."""
    pv = probe_view(ctx.settings, ctx.job)
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


def tile_measure(ctx: TileContext, v: Json, latest: Json | None) -> None:
    """The measure's tile: the runs over every candidate and the latest one's first window, the render it measured."""
    job = ctx.job
    runs = [(c, r) for c in ctx.cands for r in measure_runs(ctx.settings, ctx.d, c)]
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


def tile_plan(ctx: TileContext, v: Json, latest: Json | None) -> None:
    pl = ctx.plans
    v["state"] = "saved" if pl else "none"
    v["detail"] = (
        f"{len(pl)} saved in this job; {len(frozen_plans(ctx.settings))} frozen"
        if pl
        else "none saved; frozen plans available"
    )


def tile_render(ctx: TileContext, v: Json, latest: Json | None) -> None:
    job, full, drafts = ctx.job, ctx.full, ctx.drafts
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


def tile_skeptic(ctx: TileContext, v: Json, latest: Json | None) -> None:
    sk = [r for r in ctx.reqs if r["kind"] == "skeptic"]
    if sk:
        last = sk[-1]
        v["state"] = "answered" if last["answered"] else "waiting"
        v["detail"] = f"{last['name']} · {last['age_s']} s old" if not last["answered"] else f"{last['name']} answered"
        v["wall_s"] = None
    else:
        v["detail"] = "no request yet"
    v["verdicts"] = verdicts(ctx.d)


def tile_page(ctx: TileContext, v: Json, latest: Json | None) -> None:
    job, rs = ctx.job, ctx.rounds
    page = ctx.root / "index.html"
    if page.exists():
        if not latest:
            v["state"] = "done"
        v["detail"] = f"md5 {md5_file(page)[:8]}… · round {rs[-1]['n'] if rs else '—'}"
        v["page"] = f"/api/jobs/{job['id']}/file/index.html"
    elif not latest:
        v["detail"] = "not built"


def tile_grades(ctx: TileContext, v: Json, latest: Json | None) -> None:
    rs = ctx.rounds
    if rs:
        last = rs[-1]
        v["state"] = (
            "graded"
            if last.get("grade")
            else ("ungraded by his word" if last.get("ungraded_by_his_word") else "ungraded")
        )
        v["detail"] = f"round {last['n']}: " + (last["grade"]["text"][:120] if last.get("grade") else v["state"])
    else:
        v["detail"] = "no round yet"


TILES: dict[str, TileFn] = {
    "import": tile_import,
    "registration": tile_registration,
    "readers": tile_readers,
    "probe": tile_probe,
    "measure": tile_measure,
    "plan": tile_plan,
    "render": tile_render,
    "skeptic": tile_skeptic,
    "page": tile_page,
    "grades": tile_grades,
}
"""The loop's tile function per stage name."""


def extras(settings: Settings, d: Path, job: Json) -> Json:
    """The loop's keys on the job view: the frozen loop plans (the plan select of the render's knobs)."""
    return {"frozen_plans": frozen_plans(settings)}
