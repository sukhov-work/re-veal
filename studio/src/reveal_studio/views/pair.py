"""The pair flow's views: its stage tiles, its keys on the job view (the relation and Reveal's verdict), its render
view, the fixture pairs the new-job form offers, and the review page the studio writes (a builtin page stage).

The relation's A and B are its decoded frames 0 and n-1 (cv2 reads no HEIC, so the originals are never shown; the
frames are the cover-cropped canvas). The bars are the ones b_pair_research.md Part 1 lists from transitions.py,
transitions_harness.py and TRANSITIONS.md; a measure without a recorded bar says so and gets no verdict.
"""

from __future__ import annotations

import html
import os
import shutil
from pathlib import Path
from typing import Any

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, log, md5_file, now_iso, read_json, rel, stamp, write_json
from reveal_studio.jobs.candidates import cached_md5, candidates, rounds, verdicts
from reveal_studio.jobs.records import records
from reveal_studio.jobs.rounds import open_round
from reveal_studio.jobs.store import fixture_photos, job_root
from reveal_studio.media.pair import step_series
from reveal_studio.media.pictures import frames_dir
from reveal_studio.registry.pair import RELATION_LONG
from reveal_studio.registry.schema import NAME_RE
from reveal_studio.runner.argv import coerce
from reveal_studio.views.base import TileContext, TileFn, attempt_note, base_render_view, file_url

DEFAULT_FPS = 30
"""The playback rate when neither the terminal file nor the record names one: a pair's report.json keeps the
clip's fps under spec (transitions.py's default, 30)."""
THUMB_SUFFIXES = (".jpg", ".jpeg", ".png")
"""The originals the studio's thumbnails read (cv2.imread); a HEIC one shows the relation's frame 0 instead."""
UNFINISHED = ("failed", "refused", "lost", "cancelled")
PAGE_A, PAGE_B = "page_A.jpg", "page_B.jpg"
"""A and B as the written page shows them, beside index.html (a name with a dot: no pair's name, so no folder)."""

BASKET: list[Json] = [
    {"key": "endpoint.first_vs_A", "label": "frame 0 against A", "unit": "levels", "bar": "eq", "at": 0},
    {"key": "endpoint.last_vs_B", "label": "the last frame against B", "unit": "levels", "bar": "eq", "at": 0},
    {"key": "flicker.edge_ratio", "label": "edge ratio", "unit": "", "bar": "lt", "at": 1.5},
    {"key": "flicker.max", "label": "flicker max", "unit": "0..1 grey", "bar": "lt", "at": 0.12},
    {"key": "flicker.mean", "label": "flicker mean", "unit": "0..1 grey", "bar": None},
    {"key": "flicker.spikiness", "label": "spikiness", "unit": "max / mean", "bar": None},
    {"key": "warping_error", "label": "warping error", "unit": "0..1 grey", "bar": None},
    {"key": "goal.feat_floor", "label": "feat floor", "unit": "", "bar": None},
    {"key": "goal.laplace_floor", "label": "laplace floor", "unit": "", "bar": None},
    {"key": "goal.contrast_floor", "label": "contrast floor", "unit": "", "bar": None},
    {"key": "goal.dissolve_fit", "label": "dissolve fit", "unit": "", "bar": None},
    {"key": "goal.motion_share", "label": "motion share", "unit": "", "bar": None},
]
"""The quality basket of report.json as the panels and the page read it, each row with its bar: the endpoints are A
and B byte for byte before the encode (invariant 4; harness checks 21 and 31), the edge ratio below 1.5 for every
preset and the largest flicker step below 0.12 (harness check 21); the rest carry no fixed bar."""
HINT_OF = {"flicker.max": "report.flicker_max", "flicker.mean": "report.flicker_mean"}
"""A row's hint key where the key's last part alone would be ambiguous; else report.<the last part>."""


def hint_key(key: str) -> str:
    return HINT_OF.get(key) or "report." + key.rsplit(".", 1)[-1]


def dig(obj: Any, dotted: str) -> Any:
    """obj["a"]["b"] for "a.b", or None where a key is missing."""
    for part in dotted.split("."):
        if not isinstance(obj, dict):
            return None
        obj = obj.get(part)
    return obj


def _judge(row: Json, v: Any) -> str | None:
    if row["bar"] is None or not isinstance(v, int | float) or isinstance(v, bool):
        return None
    if row["bar"] == "eq":
        return "within" if v == row["at"] else "past bar"
    return "within" if v < row["at"] else "past bar"


def bars(report: Json | None) -> list[Json]:
    """The basket's rows: the value under report.quality, the bar as text and the verdict (None without a bar)."""
    q = (report or {}).get("quality") or {}
    out: list[Json] = []
    for row in BASKET:
        v = dig(q, row["key"])
        bar = None if row["bar"] is None else (f"{row['at']}" if row["bar"] == "eq" else f"below {row['at']}")
        out.append(
            {
                "key": row["key"],
                "label": row["label"],
                "unit": row["unit"],
                "value": v,
                "bar": bar,
                "verdict": _judge(row, v),
                "hint": hint_key(row["key"]),
            }
        )
    return out


# ------------------------------------------------------------------ the relation and the verdict


def _latest(d: Path, stage: str) -> tuple[Json | None, Json | None]:
    recs = [r for r in records(d) if r["stage"] == stage]
    done = next((r for r in reversed(recs) if r["state"] == "done"), None)
    return (recs[-1] if recs else None), done


def _md5_of(d: Path, rec: Json | None, f: Path) -> str | None:
    """The file's md5 from the record that wrote it, else hashed once and cached."""
    mine = [o for o in (rec or {}).get("outputs") or [] if Path(o.get("path", "")).name == f.name]
    return str(mine[0]["md5"]) if mine else cached_md5(d, f)


def relation_frames(settings: Settings, d: Path, job: Json, view: Json | None = None) -> Path | None:
    """The folder of the relation's decoded frames (media/pictures.frames_dir on the relation's mp4), or None."""
    v = view or relation_view(settings, d, job)
    if not v["exists"] or not v.get("md5_mp4"):
        return None
    pseudo = {
        "dir": job_root(settings, job) / "relation",
        "mp4": "transition.mp4",
        "kind": "relation",
        "name": "relation",
        "md5_mp4": v["md5_mp4"],
    }
    return frames_dir(d, pseudo)


def relation_view(settings: Settings, d: Path, job: Json) -> Json:
    """GET /api/jobs/<id>/relation and the job view's `relation`: the latest record's state and reason, the report's
    numbers (its class labelled at 480 px), the basket's bars, the strip and mp4 URLs, the URLs of the decoded frames
    0 (A) and n-1 (B), the two md5s and the renders whose class differs. Nothing here decodes: the frame route does."""
    root = job_root(settings, job)
    latest, done = _latest(d, "relation")
    rep = read_json(root / "relation" / "report.json")
    base = f"/api/jobs/{job['id']}"
    v: Json = {
        "exists": isinstance(rep, dict),
        "long": RELATION_LONG,
        "state": latest["state"] if latest else "none",
        "record": latest["id"] if latest else None,
        "reason": (latest or {}).get("reason"),
        "wall_s": (done or {}).get("wall_s"),
        "done_record": done["id"] if done else None,
        "unchanged_from": (done or {}).get("unchanged_from"),
    }
    if not isinstance(rep, dict):
        return v
    n = int(rep.get("n_frames") or 0)
    md5 = _md5_of(d, done, root / "relation" / "transition.mp4")
    q = f"?m={(md5 or 'x')[:8]}"  # a rerun with another mp4 gets other URLs: the frame route's answer is cacheable
    v.update(
        {
            "report": {k: x for k, x in rep.items() if k != "outputs"},
            "bars": bars(rep),
            "n_frames": n,
            "strip_url": f"{base}/file/relation/strip.jpg",
            "mp4_url": f"{base}/file/relation/transition.mp4",
            "a_url": f"{base}/relation/frame/0{q}",
            "b_url": f"{base}/relation/frame/{max(0, n - 1)}{q}",
            "mid_url": f"{base}/relation/frame/{max(0, n - 1) // 2}{q}",
            "md5_mp4": md5,
            "md5_strip": _md5_of(d, done, root / "relation" / "strip.jpg"),
        }
    )
    cls = rep.get("class")
    v["differs"] = [
        {"name": c["name"], "kind": c["kind"], "class": c.get("class")}
        for c in candidates(settings, d, job)
        if c.get("class") and cls and c.get("class") != cls
    ]
    return v


def verdict_view(settings: Settings, d: Path, job: Json) -> Json:
    """GET /api/jobs/<id>/verdict and the job view's `verdict`: the latest record's state and its FAILED: reason, and
    from the latest done record the metrics Reveal wrote (method, inliers, rmse_px, confidence, passed) with the URLs
    of its two aligned stills."""
    latest, done = _latest(d, "verdict")
    v: Json = {
        "state": latest["state"] if latest else "none",
        "record": latest["id"] if latest else None,
        "reason": (latest or {}).get("reason"),
        "wall_s": (latest or {}).get("wall_s"),
        "done_record": done["id"] if done else None,
        "metrics": None,
        "stills": None,
    }
    folder = d / "verdict"
    m = read_json(folder / "metrics.json") if done else None
    if isinstance(m, dict):
        mm = m.get("metrics") or {}
        v["metrics"] = {k: mm.get(k) for k in ("method", "inliers", "rmse_px", "confidence", "passed")}
        base = f"/api/jobs/{job['id']}/file/verdict/"
        v["stills"] = {n: base + f"{n}.jpg" for n in ("before", "after_aligned") if (folder / f"{n}.jpg").is_file()}
    return v


def extras(settings: Settings, d: Path, job: Json) -> Json:
    """The pair flow's keys on the job view: the relation and Reveal's verdict."""
    return {"relation": relation_view(settings, d, job), "verdict": verdict_view(settings, d, job)}


def fixture_pairs(settings: Settings) -> list[Json]:
    """GET /api/fixtures: every pair fixtures/<name>_S.* and _F.* (any group), in name order, each photo the first in
    name order (jobs/store.fixture_photos' rule), with its name and size."""
    folder = settings.fixtures
    if not folder.is_dir():
        return []
    names = sorted(
        {p.name.rsplit("_S.", 1)[0] for p in folder.glob("*_S.*") if p.is_file() and not p.name.startswith(".")}
    )
    out: list[Json] = []
    for name in names:
        if not NAME_RE.match(name):
            continue
        try:
            a, b = fixture_photos(settings, name)
        except StudioError:
            continue
        out.append(
            {
                "name": name,
                "A": {"name": a.name, "bytes": a.stat().st_size},
                "B": {"name": b.name, "bytes": b.stat().st_size},
            }
        )
    return out


# ------------------------------------------------------------------ the tiles


def _relation(ctx: TileContext) -> Json:
    v: Json = ctx.once("relation", lambda: relation_view(ctx.settings, ctx.d, ctx.job))
    return v


def tile_import(ctx: TileContext, v: Json, latest: Json | None) -> None:
    job = ctx.job
    by = {i.get("role"): i for i in job.get("inputs") or []}
    v["state"] = "done"
    v["detail"] = " · ".join(f"{r} {by[r]['name']}" for r in ("A", "B") if r in by)
    rv = _relation(ctx)
    a = by.get("A") or {}
    if rv["exists"]:
        v["thumb"] = rv["a_url"]
    elif Path(str(a.get("name", ""))).suffix.lower() in THUMB_SUFFIXES:
        v["thumb"] = f"/api/jobs/{job['id']}/thumb/raw/0"


def tile_relation(ctx: TileContext, v: Json, latest: Json | None) -> None:
    rv = _relation(ctx)
    if not rv["exists"]:
        if not latest:
            v["detail"] = "not run"
        return
    r = rv["report"]
    v["detail"] = (
        f"class {r.get('class')} at {RELATION_LONG} px · {r.get('method')} · {r.get('sparse_inliers')} inliers"
        f" · {r.get('median_disp_px')} px"
    )
    v["thumb"] = rv["mid_url"]
    if not latest:
        v["state"] = "done"  # a relation folder written from the shell
    elif latest["state"] in UNFINISHED:
        v["last_attempt"] = latest["state"]
        v["reason"] = attempt_note(latest)
        v["state"] = "done"  # the tile says what the stage holds; the attempt is beside it
    if rv["differs"]:
        v["warnings"] = [class_differs(rv)]


def class_differs(rv: Json) -> Json:
    names = ", ".join(c["name"] for c in rv["differs"])
    return {"key": "relation.class_differs", "text": f"class differs from {rv['report'].get('class')}: {names}"}


def tile_verdict(ctx: TileContext, v: Json, latest: Json | None) -> None:
    if not latest:
        v["detail"] = "optional, not run"
        return
    vv = verdict_view(ctx.settings, ctx.d, ctx.job)
    if latest["state"] == "done" and vv["metrics"]:
        m = vv["metrics"]
        v["detail"] = (
            f"{m.get('method')} · {m.get('inliers')} inliers · rmse {m.get('rmse_px')} px · confidence"
            f" {m.get('confidence')}"
        )
    elif latest.get("reason"):
        v["detail"] = str(latest["reason"])[:160]


def tile_render(ctx: TileContext, v: Json, latest: Json | None) -> None:
    job, full, drafts = ctx.job, ctx.full, ctx.drafts
    unj = [c["name"] for c in full if c["unjudged"]]
    v["detail"] = f"{len(full)} full, {len(drafts)} drafts" + (f"; unjudged: {', '.join(unj)}" if unj else "")
    if latest and latest["state"] in UNFINISHED and (full or drafts):
        v["last_attempt"] = f"{latest['state']}: {(latest.get('knobs') or {}).get('name') or latest['id']}"
        v["detail"] += f" · last attempt {v['last_attempt']}"
        v["reason"] = attempt_note(latest)
        v["state"] = "done"
    if not latest and full:
        v["state"] = "done"
    pick = full or drafts
    if pick:
        last = sorted(pick, key=lambda c: c["mtime"])[-1]
        v["thumb"] = f"/api/jobs/{job['id']}/thumb/render/{last['kind']}/{last['name']}"
    rv = _relation(ctx)
    if rv["exists"] and rv["differs"]:
        v["warnings"] = [class_differs(rv)]


def tile_skeptic(ctx: TileContext, v: Json, latest: Json | None) -> None:
    sk = [r for r in ctx.reqs if r["kind"] == "skeptic"]
    if sk:
        last = sk[-1]
        v["state"] = "answered" if last["answered"] else "waiting"
        v["detail"] = f"{last['name']} answered" if last["answered"] else f"{last['name']} · {last['age_s']} s old"
    else:
        v["detail"] = "no request yet"
    v["verdicts"] = verdicts(ctx.d)


def tile_page(ctx: TileContext, v: Json, latest: Json | None) -> None:
    page = ctx.root / "index.html"
    rs = ctx.rounds
    if page.exists():
        if not latest:
            v["state"] = "done"
        v["detail"] = f"md5 {md5_file(page)[:8]}… · round {rs[-1]['n'] if rs else '—'}"
        v["page"] = f"/api/jobs/{ctx.job['id']}/file/index.html"
    elif not latest:
        v["detail"] = "not built"


def tile_grades(ctx: TileContext, v: Json, latest: Json | None) -> None:
    rs = ctx.rounds
    if not rs:
        v["detail"] = "no round yet"
        return
    last = rs[-1]
    g = last.get("grade")
    v["state"] = "graded" if g else ("ungraded by his word" if last.get("ungraded_by_his_word") else "ungraded")
    if not g:
        v["detail"] = f"round {last['n']}: {v['state']}"
        return
    picks = read_json(ctx.d / g["picks"]) if g.get("picks") else None
    best = ", ".join(str(x) for x in ((picks or {}).get("best") or {}).values())
    words = str(g.get("text") or "")
    v["detail"] = f"round {last['n']}: " + "; ".join(x for x in (f"best {best}" if best else "", words[:120]) if x)


TILES: dict[str, TileFn] = {
    "import": tile_import,
    "relation": tile_relation,
    "verdict": tile_verdict,
    "render": tile_render,
    "skeptic": tile_skeptic,
    "page": tile_page,
    "grades": tile_grades,
}
"""The pair flow's tile function per stage name."""


# ------------------------------------------------------------------ the render view


def frame_tags(n: int) -> list[Json]:
    """Frames 0 and n-1 are A and B byte for byte before the encode (transitions.py's invariant 4): photo; every frame
    between is a blend of the two at clip place t = i / (n - 1)."""
    ends = (0, n - 1)
    return [
        {
            "i": i,
            "tag": "photo" if i in ends else "blend",
            "t": None if i in ends else round(i / (n - 1), 3),
            "generated": False,
        }
        for i in range(n)
    ]


def decode_checks(dec: Json, report: Json) -> list[Json]:
    """The decoded mp4 against the report (transitions_harness.py section H): the frame count and the size (check 28),
    the rate, and the darkest frame's mean above 5 (check 30)."""
    if not dec:
        return []
    spec = report.get("spec") or {}
    n, canvas, fps = report.get("n_frames"), report.get("canvas"), spec.get("fps")
    rows = [
        ("frames", dec.get("frames"), f"= n_frames {n}", dec.get("frames") == n),
        ("size", dec.get("size"), f"= canvas {canvas}", dec.get("size") == canvas),
        ("fps", dec.get("fps"), f"= spec fps {fps}", isinstance(fps, int | float) and abs(dec["fps"] - fps) < 0.01),
        ("darkest", dec.get("darkest_mean"), "above 5", (dec.get("darkest_mean") or 0) > 5),
    ]
    return [
        {"key": k, "value": val, "bar": bar, "verdict": "within" if ok else "past bar", "hint": f"report.decode_{k}"}
        for k, val, bar, ok in rows
    ]


def render_view(settings: Settings, d: Path, job: Json, kind: str, name: str) -> Json:
    """GET /api/jobs/<id>/render/<kind>/<name> for a pair job: the base view (the frames, the URLs, fps from the
    report's spec) with the report, the basket's bars, the frame tags, the decoded step series with the decode's
    checks, the report's flicker numbers and the relation's class."""
    own = base_render_view(settings, d, job, kind, name, DEFAULT_FPS)
    folder = settings.root / own["path"]
    rep: Json = read_json(folder / "report.json") or {}
    c = dict(own, dir=folder)
    dec = step_series(d, c)
    n = int(own.get("frames_available") or own.get("frames") or 0)
    own["report"] = {k: x for k, x in rep.items() if k != "outputs"}
    own["bars"] = bars(rep)
    own["frames_tags"] = frame_tags(n)
    own["steps"] = dec.get("steps") or []
    own["decode"] = decode_checks(dec, rep)
    own["flicker"] = dig(rep, "quality.flicker") or {}
    own["strip_url"] = file_url(settings, d, job, f"{own['path']}/strip.jpg")
    rv = relation_view(settings, d, job)
    own["relation_class"] = (rv.get("report") or {}).get("class")
    rc = own["relation_class"]
    own["class_differs"] = bool(rc and rep.get("class") and rep.get("class") != rc)
    return own


# ------------------------------------------------------------------ the page the studio writes


def _e(x: Any) -> str:
    return html.escape("" if x is None else str(x))


def strip_labels(n: int, seconds: float) -> list[tuple[int, float]]:
    """The strip's tiles as frame and clip time: min(8, n) frames evenly spaced, the first and last included
    (transitions.py StreamStats: np.linspace(0, n - 1, k).round(); no tie falls on a half for k = 8)."""
    k = min(8, n)
    if k < 2:
        return [(0, 0.0)] if n else []
    idx = [round(j * (n - 1) / (k - 1)) for j in range(k)]
    return [(i, round(i / max(n - 1, 1) * seconds, 2)) for i in idx]


def _fmt(v: Any) -> str:
    if isinstance(v, float):
        return f"{v:.4g}"
    return _e(v)


def _basket_html(rows: list[Json]) -> str:
    out = ["<table class=basket><tr><th>measure</th><th>value</th><th>bar</th><th>reading</th></tr>"]
    for r in rows:
        verdict = r["verdict"] or "no bar recorded"
        cls = {"within": "ok", "past bar": "bad"}.get(r["verdict"] or "", "muted")
        out.append(
            f"<tr><td>{_e(r['label'])}</td><td class=num>{_fmt(r['value'])} <span class=unit>{_e(r['unit'])}</span>"
            f"</td><td>{_e(r['bar'] or '—')}</td><td class={cls}>{_e(verdict)}</td></tr>"
        )
    out.append("</table>")
    return "".join(out)


PAGE_CSS = (
    "body{font:14px/1.45 system-ui,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;margin:24px;background:#141618;"
    "color:#e8e8e6;max-width:1500px}h1{font-size:1.25rem}h2{font-size:1rem;margin:0 0 8px}a{color:#6aa9f0}"
    ".meta,.muted,.unit{color:#9aa1a8}.ab{display:flex;gap:16px;flex-wrap:wrap}.ab img{height:300px;max-width:100%}"
    "figure{margin:0}figcaption{color:#9aa1a8;font-size:.8rem}.cand{border-top:1px solid #30353a;padding:16px 0}"
    ".run{display:grid;grid-template-columns:minmax(0,1fr) 420px;gap:16px;align-items:start}"
    ".run video{width:420px;background:#000}.strip img{width:100%;display:block}.labels{display:grid;"
    "font:12px ui-monospace,Menlo,monospace;color:#9aa1a8}.basket{border-collapse:collapse;margin-top:8px}"
    ".basket td,.basket th{border-bottom:1px solid #30353a;padding:2px 10px 2px 0;text-align:left}"
    ".num{font-family:ui-monospace,Menlo,monospace}.ok{color:#5cc48a}.bad{color:#e8706a}.warn{color:#e0a65a}"
    "footer{border-top:1px solid #30353a;margin-top:24px;padding-top:12px;color:#9aa1a8}"
)


def _cand_html(c: Json, seq: str, note: str, rel_class: Any) -> str:
    rep: Json = read_json(Path(c["dir"]) / "report.json") or {}
    spec = rep.get("spec") or {}
    n = int(rep.get("n_frames") or c.get("frames") or 0)
    seconds = float(spec.get("seconds") or c.get("seconds") or 0)
    labels = strip_labels(n, seconds)
    sub = f"{seq}/{c['name']}"
    vd = c.get("verdict")
    verdict = f"{vd['verdict']} on md5 {str(vd.get('judged_md5') or '')[:8]}" if vd else "unjudged"
    cls = rep.get("class")
    differs = (
        f" <span class=warn>(the relation at {RELATION_LONG} px read class {_e(rel_class)})</span>"
        if rel_class and cls and cls != rel_class
        else ""
    )
    canvas = "×".join(str(x) for x in rep.get("canvas") or [])
    facts = (
        f"class {_e(cls)}{differs} · {_e(rep.get('method'))} · {_e(rep.get('sparse_inliers'))} inliers · median"
        f" displacement {_e(rep.get('median_disp_px'))} px · certainty {_e(rep.get('mean_certainty'))} · preset"
        f" {_e(c.get('preset') or '—')} · canvas {_e(canvas)} · {n} frames at {_e(spec.get('fps'))} fps ·"
        f" {_e(seconds)} s"
    )
    cells = "".join(f"<span>frame {i}<br>{t:.2f} s</span>" for i, t in labels)
    return (
        f"<section class=cand id='{_e(c['name'])}'><h2>{_e(c['name'])} <span class=muted>{_e(verdict)}</span></h2>"
        f"<div class=run><div><div class=strip><img src='{sub}/strip.jpg' alt='the strip of {_e(c['name'])}'>"
        f"<div class=labels style='grid-template-columns:repeat({len(labels)},1fr)'>{cells}</div></div>"
        f"<p>{facts}</p>{_basket_html(bars(rep))}"
        + (f"<p>Note: {_e(note)}</p>" if note else "")
        + (f"<p class=muted>Skeptic: {_e(vd.get('note'))}</p>" if vd and vd.get("note") else "")
        + f"<p class=muted>transition.mp4 md5 {_e(c.get('md5_mp4'))}</p></div>"
        f"<video src='{sub}/transition.mp4' controls loop muted playsinline preload=metadata></video></div></section>"
    )


def _page_pictures(settings: Settings, d: Path, job: Json, root: Path, rv: Json, first: Json) -> list[Path]:
    """page_A.jpg and page_B.jpg beside the page: the relation's decoded frames 0 and n-1, else the first listed
    render's (copies of the decoded JPEGs; nothing here imports cv2)."""
    folder = relation_frames(settings, d, job, rv) if rv["exists"] else frames_dir(d, first)
    frames = sorted(folder.glob("f*.jpg")) if folder else []
    if not frames:
        return []
    out = []
    for src, name in ((frames[0], PAGE_A), (frames[-1], PAGE_B)):
        shutil.copyfile(src, root / name)
        out.append(root / name)
    return out


def page_html(
    settings: Settings, job: Json, knobs: Json, listed: list[Json], rv: Json, n_round: int, pictures: bool
) -> str:
    """The page: the title, the intro, A and B, the relation's line, then per listed render the strip with its frame
    labels, the player, the class and the method, the basket with its bars and the note; the footer (the override is
    in it)."""
    seq = job["seq"]
    by = {i.get("role"): i for i in job.get("inputs") or []}
    title = knobs.get("title") or f"{seq}: round {n_round}"
    rep = rv.get("report") or {}
    last = max(0, int(rv.get("n_frames") or 1) - 1)
    where = f"frame {{}} of the relation at {RELATION_LONG} px" if rv["exists"] else "frame {} of " + listed[0]["name"]
    ab = "".join(
        f"<figure><img src='{pic}' alt='{role}'><figcaption>{role} · {_e((by.get(role) or {}).get('name'))} ·"
        f" {_e(where.format(i))}</figcaption></figure>"
        for role, pic, i in (("A", PAGE_A, 0), ("B", PAGE_B, last if rv["exists"] else "n-1"))
    )
    relation = (
        f"<p>The relation at {RELATION_LONG} px: class {_e(rep.get('class'))} · {_e(rep.get('method'))} ·"
        f" {_e(rep.get('sparse_inliers'))} inliers · median displacement {_e(rep.get('median_disp_px'))} px.</p>"
        if rv["exists"]
        else "<p class=muted>No relation was run for this pair.</p>"
    )
    notes = knobs.get("notes") or {}
    parts = [
        f"<!doctype html><html lang=en><meta charset=utf-8><title>{_e(title)}</title>",
        "<meta name=viewport content='width=device-width,initial-scale=1'>",
        f"<style>{PAGE_CSS}</style><h1>{_e(title)}</h1>",
        f"<p>{_e(knobs.get('intro'))}</p>" if knobs.get("intro") else "",
        f"<p class=meta>{_e(seq)} · {_e(job['id'])} · round {n_round} · {len(listed)} render"
        f"{'' if len(listed) == 1 else 's'} · written by {_e(settings.ui_version)} at {_e(now_iso())}</p>",
        f"<div class=ab>{ab}</div>" if pictures else "",
        relation,
        *(_cand_html(c, seq, str(notes.get(c["name"]) or ""), rep.get("class")) for c in listed),
        f"<footer>{_e(knobs.get('footer'))}</footer>" if knobs.get("footer") else "",
    ]
    return "".join(parts) + "\n"


def build_pair_page(settings: Settings, d: Path, job: Json, stage: Json, knobs: Json) -> Json:
    """POST /api/jobs/<id>/page for a pair job, after views/page.py's gate: writes <root>/index.html (through
    index.part.html), page_A.jpg and page_B.jpg, a record of the builtin stage (state done, no argv, the listed mp4s
    with their md5s as inputs, the page's files as outputs) and opens the round (jobs/rounds.open_round). The
    previous page is kept beside the record and under its round."""
    knobs = coerce(stage, knobs)
    root = job_root(settings, job)
    full = {c["name"]: c for c in candidates(settings, d, job) if c["kind"] == "full"}
    variants = list(knobs.get("variants") or [])
    listed = [full[n] for n in variants if n in full] if variants else list(full.values())
    if not listed:
        raise StudioError("no full render to put on a page", 409)
    started = now_iso()
    rid = f"{stamp()}_page"
    rec_dir, k = d / "stages" / rid, 1
    while rec_dir.exists():
        k += 1
        rec_dir = d / "stages" / f"{rid}_{k}"
    rec_dir.mkdir(parents=True)
    rid = rec_dir.name
    rv = relation_view(settings, d, job)
    n_round = len(rounds(d)) + 1
    page, part = root / "index.html", root / "index.part.html"
    pictures = _page_pictures(settings, d, job, root, rv, listed[0])
    part.write_text(page_html(settings, job, knobs, listed, rv, n_round, bool(pictures)))
    note = None
    if page.exists():
        shutil.copy2(page, rec_dir / "previous_index.html")
        note = "the previous page is kept under its round and beside this record"
    os.replace(part, page)
    outputs = [
        {"path": rel(p, settings.root), "md5": md5_file(p), "bytes": p.stat().st_size} for p in [page, *pictures]
    ]
    rec: Json = {
        "id": rid,
        "stage": "page",
        "state": "done",
        "builtin": True,
        "argv": [],
        "pid": None,
        "started": started,
        "ended": now_iso(),
        "wall_s": 0.0,
        "exit_code": None,
        "knobs": knobs,
        "inputs": [{"path": rel(Path(c["dir"]) / c["mp4"], settings.root), "md5": c["md5_mp4"]} for c in listed],
        "outputs": outputs,
        "script_md5": None,
        "out_part": rel(part, settings.root),
        "out_final": rel(page, settings.root),
        "terminal": "index.html",
        "log": "log.txt",
        "ui_version": settings.ui_version,
        "warnings": [],
    }
    if note:
        rec["note"] = note
    (rec_dir / "log.txt").write_text(
        f"{started} the studio wrote {rel(page, settings.root)} (md5 {outputs[0]['md5']}) over"
        f" {', '.join(c['name'] for c in listed)}; round {n_round} opens on it\n"
    )
    write_json(rec_dir / "stage.json", rec)
    (rec_dir / "done").write_text(now_iso())
    names = [c["name"] for c in listed]
    open_round(d, page, names, variants=variants, record=rid, override=knobs.get("override") or None)
    log(f"{job['id']} {rid}: the studio wrote the page over {names}")
    return rec
