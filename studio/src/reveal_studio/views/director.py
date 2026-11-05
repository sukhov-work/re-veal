"""The director flow's views (builder D): its stage tiles, its keys on the job view, the pairs and plan views the page
opens, and its render view.

- TILES: one function per stage (import, verdict, resolve, plan, render, skeptic, page, grades) over the base tile.
- extras: the job view's `director` (the pair, its photos, layer tables and mattes, the element tables, the plans),
  `resolve` (the latest done resolve: the anchors, the camera, the layers' windows, motion.adjusted and motion.held,
  the canvases' URLs), `verdict` (Reveal's verdict, the shared branch) and `frozen_plans` (this pair's director plans,
  which the inspector's plan select lists).
- pairs_view: GET /api/pairs, the fixture pairs a director plan names, with each photo's layer and matte status.
- plan_view: GET /api/plans/director/<stem> (and a job's saved plan): the plan's identity, idea and risk; the concept's
  knob map in both name forms; the `--set` rows of registry/director.SET_KEYS with this concept's effective defaults
  and conditions; the beats and the end effect as bars in clip time; the last round's knobs for the button.
- render_view: a director render with fps from the record, frames_tags from the beats' windows, the measures of
  b_director_research.md §3 with their bars, the series motion_px, b_inside, residual_edges and halo each at its own
  frame index, and the step series decoded from the mp4 (media/overlays.py).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, md5_file, read_json, rel, sha256_file
from reveal_studio.jobs.candidates import candidate, verdicts
from reveal_studio.jobs.plans import frozen_plans, resolve_plan
from reveal_studio.jobs.records import records
from reveal_studio.jobs.store import fixture_photos
from reveal_studio.media.overlays import matte_dir, photo_of, step_series, table_dir
from reveal_studio.registry.director import GLOBAL_KEYS, SET_KEYS, TRANSFORM_KEYS
from reveal_studio.views.base import TileContext, TileFn, attempt_note, base_render_view, skeptic_state

DEFAULT_FPS = 30
"""The playback rate when neither the terminal file nor the record names one: director clips run at 30 fps
(director_render.py's default; info.json carries fps)."""
RESIDUAL_BAR = 0.002
"""Rule 5's bar for residual_edge_max: 0.2 % of the pixels (research/2026-10-20/retrospective.md §4 rule 5)."""
B_INSIDE_THRESHOLD = 0.01
"""b_inside_first's own threshold: the first sampled frame above 1 % (director_render.py:2055)."""
DEFAULT_END: Json = {"kind": "luma_reveal", "window": [0.78, 1.0]}
"""The end effect a concept without one renders (director_render.py:1809)."""
LAST_ROUND_GLOB = "*/director_r*/{stem}_{cid}/info.json"
"""The round renders of the director work (rounds 9 to 13), the workbench's source of the last round's knobs
(director_ui.py:270-280)."""
IMAGE = (".jpg", ".jpeg", ".png")


def _g(d: Any, *path: str, default: Any = None) -> Any:
    """The value at a key path, else `default`; a key present with null is the null (the renderer's .get)."""
    for k in path:
        if not isinstance(d, dict) or k not in d:
            return default
        d = d[k]
    return d


# ---------------------------------------------------------------- the photos, the tables and the plans


def element_rows(settings: Settings, job: Json, side: str) -> list[Json]:
    """The layer table of photo A or B as the import panel's element table: id, label, group, the canvas share, the
    depth rank, the median disparity and whether its el_<id>.png exists."""
    t = read_json(table_dir(settings, job, side) / "layers.json")
    if not isinstance(t, dict):
        return []
    mdir = matte_dir(settings, job, side)
    have = {p.stem[3:] for p in mdir.glob("el_*.png")} if mdir.is_dir() else set()
    rows = []
    for e in t.get("elements") or []:
        if not isinstance(e, dict) or "id" not in e:
            continue
        rows.append(
            {
                "id": e["id"],
                "label": e.get("label"),
                "group": e.get("group"),
                "area_share": e.get("area_share"),
                "depth_rank": e.get("depth_rank"),
                "median_disparity": e.get("median_disparity"),
                "matte": str(e["id"]) in have,
            }
        )
    return rows


def label_overlap(a: list[Json], b: list[Json]) -> list[Json]:
    """The labels found in both photos with each photo's summed canvas share, the largest first."""

    def by_label(rows: list[Json]) -> dict[str, float]:
        out: dict[str, float] = {}
        for e in rows:
            out[str(e["label"])] = round(out.get(str(e["label"]), 0.0) + float(e.get("area_share") or 0), 4)
        return out

    la, lb = by_label(a), by_label(b)
    both = sorted(set(la) & set(lb), key=lambda k: (-(la[k] + lb[k]), k))
    return [{"label": k, "A": la[k], "B": lb[k]} for k in both]


def pair_plans(settings: Settings, pair: str) -> list[Json]:
    """The frozen director plans of the pair as the plan select lists them (name, ref, path, concepts, relation), in
    round order: the bare <pair> plan (round 8) first, the newest round last."""
    rows = [p for p in frozen_plans(settings, "director") if p.get("pair") == pair]
    return sorted(rows, key=lambda p: _round_key(str(p["name"])))


def _photo_status(settings: Settings, photo: Path) -> Json:
    """One photo of a pair for the pair picker: the file, its layer table's element count and its matte files."""
    t = read_json(settings.layers_dir / photo.stem / "layers.json")
    ids = [int(e["id"]) for e in (t or {}).get("elements") or [] if isinstance(e, dict) and "id" in e]
    mdir = settings.mattes_dir / photo.stem
    have = {int(p.stem[3:]) for p in mdir.glob("el_*.png") if p.stem[3:].isdigit()} if mdir.is_dir() else set()
    return {
        "file": photo.name,
        "layers": isinstance(t, dict),
        "elements": len(ids),
        "mattes": len(have),
        "missing": [i for i in ids if i not in have] if isinstance(t, dict) else None,
    }


def pairs_view(settings: Settings) -> list[Json]:
    """GET /api/pairs: every pair a frozen director plan names, its plans in name order (the last is the newest
    round), and each photo's status; a pair whose photos are absent says so instead of a status."""
    by: dict[str, list[str]] = {}
    for p in frozen_plans(settings, "director"):
        if isinstance(p.get("pair"), str):
            by.setdefault(p["pair"], []).append(p["name"])
    out = []
    for pair in sorted(by):
        row: Json = {"pair": pair, "plans": sorted(by[pair], key=_round_key)}
        try:
            a, b = fixture_photos(settings, pair)
            row["photos"] = {"A": _photo_status(settings, a), "B": _photo_status(settings, b)}
        except StudioError as e:
            row["photos"] = None
            row["missing"] = str(e)
        out.append(row)
    return out


def _round_key(stem: str) -> tuple[int, str]:
    """A plan stem's round: <pair>_r<n> sorts by n, the bare <pair> (round 8) first."""
    m = re.search(r"_r(\d+)$", stem)
    return (int(m.group(1)) if m else 8, stem)


# ---------------------------------------------------------------- the plan view


SKY_SHAPES = (
    ("shape radial or radial_out", ("radial", "radial_out")),
    ("shape radial_out", ("radial_out",)),
    ("shape radial", ("radial",)),
)
"""A sky row's shape condition by the words of its `when` (the longer phrases first: one holds the next)."""
GLOBAL_CONDITIONS: dict[str, tuple[str, ...]] = {
    "guard": ("guarded",),
    "end_scale": ("disc",),
    "front_ids": ("quad",),
    "cont_feather": ("quad",),
    "parallax_A_elements": ("gate", "A"),
    "push_floor": ("gate", "push"),
    "front_margin": ("quad", "gate", "B"),
    "sky": ("disc",),
    "key_end": ("disc", "no_key_window"),
    "reflect": ("quad", "glass"),
    "end_radius_px": ("disc", "radial_reveal"),
}
"""A top-level row's condition as the facts of the plan it needs (registry/director.py's `when`, D:n there)."""
FRONT_KEYS = ("front_hole_max", "plate_fill", "front_per_element")
"""Rows read only when B has a front layer: a quad or rect container may, and its resolve says whether it does."""


def _facts(c: Json) -> dict[str, bool]:
    """What the plan alone says about a concept's conditions."""
    kind = _g(c, "container", "kind", default="none")
    pl = _g(c, "pullback", "parallax", default={"kind": "off"}) or {}
    sources = pl.get("sources", ["A", "B"])
    quad = kind in ("quad", "rect")
    return {
        "disc": kind == "disc",
        "quad": quad,
        "gate": pl.get("kind") == "depth" and float(pl.get("gain", 0) or 0) > 0,  # director_render.py:676
        "A": "A" in sources,
        "B": "B" in sources,
        "push": float(pl.get("push", 2.5 if quad else 0.0) or 0) > 0,
        "glass": _g(c, "container", "rim") == "glass",
        "no_key_window": "key_window" not in (_g(c, "container", "params", "sky", default={}) or {}),
        "radial_reveal": _g(c, "end_effect", "kind") == "radial_reveal",
        "guarded": any(
            t.get("b") is not None and t.get("by") not in ("colour", "hold", "exit") for t in c.get("transforms") or []
        ),
    }


def _sky_applies(when: str, c: Json) -> bool:
    """A sky row's condition: a disc container, then the sky's shape, band and stars its `when` names."""
    if _g(c, "container", "kind") != "disc":
        return False
    sky = _g(c, "container", "params", "sky", default={}) or {}
    shape = sky.get("shape", "radial")
    shapes = next((s for text, s in SKY_SHAPES if text in when), None)
    checks = [
        shapes is None or shape in shapes,
        "border feather" not in when or shape not in ("radial", "radial_out"),
        "band limb" not in when or sky.get("band") == "limb",
        "stars true" not in when or bool(sky.get("stars")),
    ]
    return all(checks)


def _applies(row: Json, c: Json) -> bool | None:
    """Whether the concept meets the row's condition, as far as the plan alone decides it (None: the resolve
    decides, such as whether B has front elements)."""
    if row["readonly"]:
        return False
    if row["scope"] == "sky":
        return _sky_applies(row["when"], c)
    f, key = _facts(c), row["key"]
    if key in GLOBAL_CONDITIONS:
        return all(f[x] for x in GLOBAL_CONDITIONS[key])
    if key in FRONT_KEYS:
        return True if f["quad"] else None
    if key == "vacated_first":
        return None
    if key.startswith("parallax_") or key == "front_in":
        return f["gate"]
    return True


def _effective(key: str, c: Json) -> tuple[Any, str | None]:
    """A top-level key's value for the concept when the set dict leaves it alone (the plan's, else the code's
    default), and the key it follows when the renderer takes that key's value (parallax_gain_A takes the gain)."""
    kind = _g(c, "container", "kind", default="none")
    pl = _g(c, "pullback", "parallax", default={}) or {}
    end = c.get("end_effect") or DEFAULT_END
    quad = kind in ("quad", "rect")
    table: dict[str, Callable[[], Any]] = {
        "motion": lambda: _g(c, "motion", "kind") or "legacy",
        "guard": lambda: bool(_g(c, "reveal", "guard", default=_g(c, "motion", "kind") == "continuous")),
        "end_scale": lambda: _g(c, "pullback", "params", "end_scale", default=_g(c, "params", "end_scale")),
        "front_ids": lambda: _g(c, "container", "spec", "front_ids", default=[]),
        "cont_feather": lambda: _g(c, "container", "params", "feather_px", default=1.0),
        "parallax_sources": lambda: pl.get("sources", ["A", "B"]),
        "parallax_gain": lambda: pl.get("gain", 0.3),
        "parallax_gain_A": lambda: pl.get("gain_A", pl.get("gain", 0.3)),
        "parallax_blur": lambda: pl.get("blur", 6.0),
        "parallax_A_elements": lambda: pl.get("a_elements"),
        "parallax_push": lambda: pl.get("push", 2.5 if quad else 0.0),
        "push_floor": lambda: pl.get("push_floor", 0.3),
        "front_in": lambda: pl.get("front_in", 0.15),
        "front_margin": lambda: _g(c, "container", "spec", "front_margin", default=0.05),
        "sky": lambda: _g(c, "container", "params", "sky", default={}),
        "key_end": lambda: _g(c, "params", "key_end", default=0.45),
        "reflect": lambda: _g(
            c, "container", "params", "reflect", default=_g(c, "container", "spec", "reflect", default=0.18)
        ),
        "end_window": lambda: end.get("window", [0.78, 1.0]),
        "end_kind": lambda: end.get("kind", "luma_reveal"),
        "end_band": lambda: _g(end, "params", "band", default=0.16),
        "vacated_first": lambda: _g(end, "params", "vacated_first", default=0.35),
    }
    follows = "parallax_gain" if key == "parallax_gain_A" and "gain_A" not in pl else None
    if key in table:
        return table[key](), follows
    return GLOBAL_KEYS[key]["default"], follows


def _sky_default(row: Json, c: Json) -> Any:
    sky = _g(c, "container", "params", "sky", default={}) or {}
    if row["key"] in sky:
        return sky[row["key"]]
    if row["key"] == "key_window":
        return [_g(c, "params", "key_start", default=0.0), _g(c, "params", "key_end", default=0.45)]
    if row["key"] == "key_band":
        return _g(c, "params", "key_band", default=0.10)
    return row["default"]


def _row(r: Json, default: Any, applies: bool | None, set_key: str, follows: str | None = None) -> Json:
    out = {k: r[k] for k in ("key", "table", "scope", "hint", "type", "when", "plan_path", "choices", "range")}
    out.update(set_key=set_key, default=default, applies=applies, readonly=r["readonly"], source=r["source"])
    if follows:
        out["follows"] = follows
    return out


PATH_KEYS: dict[tuple[str, ...], str] = {
    tuple(r["plan_path"].split(".")): r["set_key"]
    for r in SET_KEYS
    if r["scope"] in ("global", "sky") and r["plan_path"] and not r["readonly"]
}
"""A plan path the renderer reads under a --set key of another name (director_ui.py:190-201, completed from the
table): pullback.parallax.push is parallax_push, container.params.sky.shape is sky.shape."""
KNOB_NAME_RE = re.compile(r"([A-Za-z_]\w*)((?:\.[A-Za-z_]\w*|\[\d+\])*)")
TRANSFORM_FIELDS = ("window", "mix", "skip")


def parse_knob_name(name: Any) -> list[Any] | None:
    """A plan knob's name as tokens: `pane_becomes_view.params.times[0]` is [pane_becomes_view, params, times, 0]."""
    m = KNOB_NAME_RE.fullmatch(str(name or ""))
    if not m:
        return None
    toks: list[Any] = [m.group(1)]
    toks += [t[0] if t[0] else int(t[1]) for t in re.findall(r"\.([A-Za-z_]\w*)|\[(\d+)\]", m.group(2))]
    return toks


def map_knob(name: Any, c: Json) -> Json:
    """A planner's knob as the --set key it becomes: {set_key, base, path} (base the plan's value under the key, path
    the index path from it to the knob's leaf), or {readonly: reason}. Both name forms map: the plan path
    (`<name>.params.<key>`) and the key form (`<name>.<key>`, as mismatch_1_r13.json writes two of them)."""
    toks = parse_knob_name(name)
    if not toks:
        return {"readonly": "not a dotted path; no renderer key reads it"}
    trs = {t.get("name"): t for t in c.get("transforms") or [] if isinstance(t, dict)}
    head = toks[0]
    if head in trs:
        t = trs[head]
        if len(toks) < 2 or not isinstance(toks[1], str):
            return {"readonly": "a transform's name without a field"}
        f = toks[1]
        if f in TRANSFORM_FIELDS:
            key, base, rest = f"{head}.{f}", t.get(f, [0, 1] if f == "window" else None), toks[2:]
        elif f == "params" and len(toks) >= 3 and isinstance(toks[2], str):
            key, base, rest = f"{head}.{toks[2]}", (t.get("params") or {}).get(toks[2]), toks[3:]
        else:
            key, base, rest = f"{head}.{f}", (t.get("params") or {}).get(f), toks[2:]
        row = TRANSFORM_KEYS.get(key.split(".", 1)[1])
        if row is not None and row["readonly"]:
            return {"readonly": row["readonly"]}
    else:
        found = next(((n, PATH_KEYS[tuple(toks[:n])]) for n in (4, 3, 2) if tuple(toks[:n]) in PATH_KEYS), None)
        if found is not None:
            n, key = found
            base, rest = _g(c, *[str(x) for x in toks[:n]]), toks[n:]
        elif head in GLOBAL_KEYS and not GLOBAL_KEYS[head]["readonly"]:
            key, rest = head, toks[1:]
            base = _effective(head, c)[0]
        else:
            return {"readonly": f"no --set key of director_render.py reads {name}"}
    if rest and base is None:
        return {"readonly": f"{name} indexes into a value the plan does not hold"}
    return {"set_key": key, "base": base, "path": rest}


def _transform_rows(t: Json) -> list[Json]:
    """The table C rows a transform of this kind reads, each at the plan's value else the kind's code default, then
    the read-only rows of table D."""
    by, name = str(t.get("by")), str(t.get("name"))
    out = []
    for r in SET_KEYS:
        if r["scope"] != "transform":
            continue
        if r["readonly"]:
            out.append(_row(r, None, False, f"{name}.{r['key']}"))
            continue
        if by not in (r["kinds"] or {}):
            continue
        if r["key"] in ("window", "mix"):
            default = t.get(r["key"], r["kinds"][by])
        else:
            default = (t.get("params") or {}).get(r["key"], r["kinds"][by])
        out.append(_row(r, default, True, f"{name}.{r['key']}"))
    return out


def last_round(settings: Settings, stem: str, cid: str) -> Json | None:
    """The knobs of the newest round render of this plan and concept, which the button loads on request (never on its
    own: b_design.md decision 2)."""
    found = sorted(settings.runs.glob(LAST_ROUND_GLOB.format(stem=stem, cid=cid)), key=lambda p: p.stat().st_mtime)
    if not found:
        return None
    info = read_json(found[-1]) or {}
    return {
        "from": rel(found[-1], settings.root),
        "knobs": info.get("knobs") or {},
        "wall_s": info.get("wall_s"),
        "canvas": info.get("canvas"),
    }


def concept_view(settings: Settings, stem: str, c: Json) -> Json:
    """One concept as the plan panel shows it."""
    globals_ = []
    for r in SET_KEYS:
        if r["scope"] != "global":
            continue
        if r["readonly"]:
            globals_.append(_row(r, r["default"], False, r["set_key"]))
            continue
        default, follows = _effective(r["key"], c)
        globals_.append(_row(r, default, _applies(r, c), r["set_key"], follows))
    sky = [_row(r, _sky_default(r, c), _applies(r, c), r["set_key"]) for r in SET_KEYS if r["scope"] == "sky"]
    trs = [t for t in c.get("transforms") or [] if isinstance(t, dict)]
    end = c.get("end_effect") or DEFAULT_END
    knobs = []
    for k in c.get("knobs") or []:
        if isinstance(k, dict):
            row = {
                "name": k.get("name"),
                "range": k.get("range"),
                "default": k.get("default"),
                "what": k.get("what", ""),
            }
            row.update(map_knob(k.get("name"), c))
            knobs.append(row)
    cid = str(c.get("id"))
    return {
        "id": cid,
        "rank": c.get("rank"),
        "idea": c.get("idea", ""),
        "risk": c.get("risk", ""),
        "container": {"kind": _g(c, "container", "kind"), "rim": _g(c, "container", "rim")},
        "motion": c.get("motion"),
        "reveal": c.get("reveal"),
        "knobs": knobs,
        "globals": globals_,
        "sky": sky,
        "transforms": [
            {
                "name": t.get("name"),
                "by": t.get("by"),
                "window": t.get("window", [0, 1]),
                "note": t.get("note", ""),
                "keyframes": (t.get("params") or {}).get("keyframes") or [],
                "rows": _transform_rows(t),
            }
            for t in trs
        ],
        "beats": [
            {
                "name": t.get("name"),
                "by": t.get("by"),
                "window": t.get("window", [0, 1]),
                "key": f"{t.get('name')}.window",
            }
            for t in trs
        ],
        "end": {"kind": end.get("kind", "luma_reveal"), "window": end.get("window", [0.78, 1.0]), "key": "end_window"},
        "helpers": (c.get("helper") or {}).get("keyframes") or [],
        "last_round": last_round(settings, stem, cid),
    }


def plan_view(settings: Settings, d: Path | None, ref: str) -> Json:
    """GET /api/plans/director/<stem> (a frozen plan) or a job's saved director plan: its identity and concepts."""
    p = resolve_plan(settings, d, ref, "director")
    plan = read_json(p)
    if not isinstance(plan, dict) or not isinstance(plan.get("concepts"), list):
        raise StudioError(f"{rel(p, settings.root)} is no director plan (no concepts)", 400)
    prov = plan.get("provenance") or {}
    src = prov.get("from")
    stem = Path(src).stem if ref.startswith("job:") and isinstance(src, str) else p.stem
    planner = plan.get("planner")
    return {
        "ref": ref,
        "stem": stem,
        "name": p.stem,
        "path": rel(p, settings.root),
        "sha256": sha256_file(p),
        "pair": plan.get("pair"),
        "relation": plan.get("relation"),
        "reading": plan.get("reading"),
        "planner": planner if isinstance(planner, dict) else {"model": planner},
        "provenance": prov or None,
        "concepts": [concept_view(settings, stem, c) for c in plan["concepts"] if isinstance(c, dict)],
    }


# ---------------------------------------------------------------- the job view's keys


def _done(recs: list[Json], stage: str) -> Json | None:
    return next((r for r in reversed(recs) if r["stage"] == stage and r["state"] == "done"), None)


def resolve_view(settings: Settings, d: Path, job: Json) -> Json | None:
    """The latest done resolve: its anchors.json and info.json as the resolve panel draws them, with the URLs of the
    canvases, the files and their thumbnails; None before the first one."""
    rec = _done(records(d), "resolve")
    if rec is None:
        return None
    folder = settings.root / rec["out_final"]
    anchors = read_json(folder / "anchors.json") or {}
    info = anchors.get("info") or read_json(folder / "info.json") or {}
    motion = info.get("motion") or {}
    base = f"/api/jobs/{job['id']}/file/{folder.relative_to(d)}"
    return {
        "record": rec["id"],
        "folder": rel(folder, settings.root),
        "plan": (rec.get("knobs") or {}).get("plan"),
        "concept": anchors.get("concept"),
        "set": (rec.get("knobs") or {}).get("set") or {},
        "keys": sorted(anchors),
        "canvas": anchors.get("canvas"),
        "frames": anchors.get("frames"),
        "anchors": anchors.get("anchors") or {},
        "camera": anchors.get("camera"),
        "layers": anchors.get("layers") or [],
        "quad": info.get("quad"),
        "motion": {
            "kind": motion.get("kind"),
            "edge": motion.get("edge"),
            "overlap": motion.get("overlap"),
            "beats": motion.get("beats") or [],
            "adjusted": motion.get("adjusted") or [],
            "held": motion.get("held") or [],
        },
        "front_elements": len(info.get("front_elements") or []),
        "front_per_element": info.get("front_per_element"),
        "matte_fallbacks": info.get("matte_fallbacks") or [],
        "guard": info.get("guard") or [],
        "unplaced": info.get("unplaced") or [],
        "parallax": info.get("parallax"),
        "start_zoom": info.get("start_zoom"),
        "renderer_md5": anchors.get("renderer_md5"),
        "urls": {
            "canvas_A": f"{base}/canvas_A.png",
            "canvas_B": f"{base}/canvas_B.png",
            "anchors": f"{base}/anchors.json",
            "info": f"{base}/info.json",
            "thumb_A": f"/api/jobs/{job['id']}/thumb/canvas/A?r={rec['id']}",
            "thumb_B": f"/api/jobs/{job['id']}/thumb/canvas/B?r={rec['id']}",
        },
    }


def verdict_view(settings: Settings, d: Path, job: Json) -> Json | None:
    """Reveal's verdict, the shared branch: the latest record's state and reason, and metrics.json when it aligned."""
    rec = next((r for r in reversed(records(d)) if r["stage"] == "verdict"), None)
    if rec is None:
        return None
    m = read_json(d / "verdict" / "metrics.json") if rec["state"] == "done" else None
    return {"record": rec["id"], "state": rec["state"], "reason": rec.get("reason"), "metrics": m}


def director_view(settings: Settings, d: Path, job: Json) -> Json:
    """The pair, its photos with their tables and mattes, the element tables and the labels in both, the plans."""
    elements = {side: element_rows(settings, job, side) for side in ("A", "B")}
    photos = {}
    for side in ("A", "B"):
        i = photo_of(job, side)
        p = Path(i["path"])
        photos[side] = {
            "name": i["name"],
            "path": rel(p, settings.root),
            "sha256": i["sha256"],
            "bytes": i["bytes"],
            "readable": p.suffix.lower() in IMAGE,
            "npz": (table_dir(settings, job, side) / "layers.npz").is_file(),
        }
    return {
        "pair": job.get("pair"),
        "photos": photos,
        "tables": job.get("tables") or {},
        "mattes": job.get("mattes") or {},
        "helpers": job.get("helpers") or [],
        "elements": elements,
        "overlap": label_overlap(elements["A"], elements["B"]),
        "plans": pair_plans(settings, str(job.get("pair"))),
        "overlay_url": f"/api/jobs/{job['id']}/overlay/",
        # the layer table's sha256 in the overlay's query: the cached picture changes when the table does
        "overlay_v": {s: str(((job.get("tables") or {}).get(s) or {}).get("sha256") or "")[:8] for s in ("A", "B")},
    }


def extras(settings: Settings, d: Path, job: Json) -> Json:
    """The director flow's keys on the job view; `frozen_plans` holds this pair's director plans, so the inspector's
    plan select of the resolve and the render lists them."""
    return {
        "frozen_plans": pair_plans(settings, str(job.get("pair"))),
        "director": director_view(settings, d, job),
        "resolve": resolve_view(settings, d, job),
        "verdict": verdict_view(settings, d, job),
    }


# ---------------------------------------------------------------- the tiles


def tile_import(ctx: TileContext, v: Json, latest: Json | None) -> None:
    job = ctx.job
    v["state"] = "done"
    parts = []
    for side in ("A", "B"):
        t = (job.get("tables") or {}).get(side) or {}
        m = (job.get("mattes") or {}).get(side) or {}
        parts.append(f"{side} {t.get('elements', 0)} el. · {m.get('count', 0)} mattes" if t else f"{side} no table")
    v["detail"] = "; ".join(parts)
    resolved = ctx.once("resolve", lambda: _done(records(ctx.d), "resolve"))
    a = next((i for i in job.get("inputs") or [] if i.get("role") == "A"), None)
    if resolved:  # the record in the query: a new resolve is a new URL, so a cached thumbnail never shows the old one
        v["thumb"] = f"/api/jobs/{job['id']}/thumb/canvas/A?r={resolved['id']}"
    elif a and Path(a["path"]).suffix.lower() in IMAGE:
        v["thumb"] = f"/api/jobs/{job['id']}/thumb/raw/0"


def tile_verdict(ctx: TileContext, v: Json, latest: Json | None) -> None:
    if latest is None:
        v["detail"] = "optional, not run"
        return
    if latest["state"] == "done":
        m = read_json(ctx.d / "verdict" / "metrics.json") or {}
        bits = [str(m[k]) for k in ("method",) if m.get(k)] + [f"{m[k]} {k}" for k in ("inliers",) if m.get(k)]
        v["detail"] = "aligned" + (": " + ", ".join(bits) if bits else "")
    elif latest["state"] == "refused":
        v["detail"] = "refused: the photos share too little detail to align"
        v["reason"] = None  # the panel prints the refusal once, in its box (critique B, minor 5)


def tile_resolve(ctx: TileContext, v: Json, latest: Json | None) -> None:
    rec = ctx.once("resolve", lambda: _done(records(ctx.d), "resolve"))
    if rec is None:
        v["detail"] = "not run"
        return
    a = read_json(ctx.settings.root / rec["out_final"] / "anchors.json") or {}
    canvas = a.get("canvas") or []
    cam = (a.get("camera") or {}).get("kind")
    n = len(a.get("layers") or [])
    v["detail"] = f"{a.get('concept')} · {'×'.join(str(x) for x in canvas)} · camera {cam} · {n} layer" + (
        "s" if n != 1 else ""
    )
    v["thumb"] = f"/api/jobs/{ctx.job['id']}/thumb/canvas/B?r={rec['id']}"
    if latest and latest["state"] in ("failed", "refused", "lost", "cancelled"):
        v["state"] = "done"
        v["reason"] = attempt_note(latest)


def tile_plan(ctx: TileContext, v: Json, latest: Json | None) -> None:
    frozen = pair_plans(ctx.settings, str(ctx.job.get("pair")))
    saved = ctx.plans
    n = len(frozen) + len(saved)  # the chip counts the plans the panel offers (critique B, minor 13: it read "none")
    v["state"] = f"{n} plan" + ("s" if n != 1 else "")
    v["chip_key"] = "director.plans"
    v["detail"] = f"{len(frozen)} frozen plan" + ("s" if len(frozen) != 1 else "") + f"; {len(saved)} saved in this job"


def tile_render(ctx: TileContext, v: Json, latest: Json | None) -> None:
    job, full, drafts = ctx.job, ctx.full, ctx.drafts
    unj = [c["name"] for c in full if c["unjudged"]]
    v["detail"] = f"{len(full)} full, {len(drafts)} drafts" + (f"; unjudged: {', '.join(unj)}" if unj else "")
    if latest and latest["state"] in ("failed", "refused", "lost", "cancelled") and (full or drafts):
        v["last_attempt"] = f"{latest['state']}: {(latest.get('knobs') or {}).get('name') or latest['id']}"
        v["detail"] += f" · last attempt {v['last_attempt']}"
        v["reason"] = attempt_note(latest)
        v["state"] = "done"
    if not latest and (full or drafts):
        v["state"] = "done"
    pick = full or drafts
    if pick:
        last = sorted(pick, key=lambda c: c["mtime"])[-1]
        v["thumb"] = f"/api/jobs/{job['id']}/thumb/render/{last['kind']}/{last['name']}"
    v["generated"] = any(_chain_layers(read_json(c["dir"] / "info.json") or {}) for c in pick)


def tile_skeptic(ctx: TileContext, v: Json, latest: Json | None) -> None:
    sk = [r for r in ctx.reqs if r["kind"] == "skeptic"]
    if sk:
        v["state"], v["detail"] = skeptic_state(ctx.settings, sk[-1])
    else:
        v["detail"] = "no request yet"
    v["verdicts"] = verdicts(ctx.d)


def tile_page(ctx: TileContext, v: Json, latest: Json | None) -> None:
    page = ctx.root / "index.html"
    if page.exists():
        if not latest:
            v["state"] = "done"
        rs = ctx.rounds
        v["detail"] = f"md5 {md5_file(page)[:8]}… · round {rs[-1]['n'] if rs else '—'}"
        v["page"] = f"/api/jobs/{ctx.job['id']}/file/index.html"
    elif not latest:
        v["detail"] = "not built"
    if latest and latest.get("previous"):  # the page before this record's, copied beside it before the run
        v["previous"] = f"/api/jobs/{ctx.job['id']}/file/stages/{latest['id']}/{latest['previous']}"


def tile_grades(ctx: TileContext, v: Json, latest: Json | None) -> None:
    rs = ctx.rounds
    if not rs:
        v["detail"] = "no round yet"
        return
    last = rs[-1]
    g = last.get("grade")
    v["state"] = "graded" if g else ("ungraded by his word" if last.get("ungraded_by_his_word") else "ungraded")
    if g:
        v["detail"] = f"round {last['n']}: " + (g.get("text") or g.get("picks") or "")[:120]
    else:
        v["detail"] = f"round {last['n']}: {v['state']}"


TILES: dict[str, TileFn] = {
    "import": tile_import,
    "verdict": tile_verdict,
    "resolve": tile_resolve,
    "plan": tile_plan,
    "render": tile_render,
    "skeptic": tile_skeptic,
    "page": tile_page,
    "grades": tile_grades,
}
"""The director flow's tile function per stage name (see views/tiles_loop.py for the shape)."""


# ---------------------------------------------------------------- the render view


def _chain_layers(info: Json) -> list[Json]:
    """The keyframe_chain layers that name generated keyframes: their frames show model-made pixels."""
    return [
        x
        for x in info.get("layers") or []
        if isinstance(x, dict) and x.get("by") == "keyframe_chain" and (x.get("chain") or {}).get("keyframes")
    ]


def _record_of(d: Path, c: Json) -> Json | None:
    return next((r for r in reversed(records(d)) if r.get("out_final") == c["path"] and r.get("state") == "done"), None)


def _end_window(settings: Settings, rec: Json | None, info: Json) -> list[float]:
    """The end effect's window the render used: the record's set dict, else the plan's concept, else the default."""
    knobs = (rec or {}).get("knobs") or {}
    w = (knobs.get("set") or {}).get("end_window")
    if isinstance(w, list) and len(w) == 2:
        return [float(x) for x in w]
    plan = None
    for i in (rec or {}).get("inputs") or []:
        if str(i.get("path", "")).endswith(".json") and "sha256" in i:
            plan = read_json(settings.root / i["path"])
            break
    c = next((c for c in (plan or {}).get("concepts") or [] if c.get("id") == info.get("concept")), None)
    window: list[Any] = ((c or {}).get("end_effect") or DEFAULT_END).get("window") or [0.78, 1.0]
    return [float(x) for x in window]


def frame_tags(info: Json, n: int, end: list[float]) -> list[Json]:
    """A tag per frame from the beats' windows: photo at frame 0 (A exactly) and the last (B exactly); else the open
    beats' names, `end` inside the end effect's window, `camera` when only the pull-back moves. A frame inside a
    keyframe chain's window carries generated pixels (the violet mark)."""
    layers = [x for x in info.get("layers") or [] if isinstance(x, dict) and isinstance(x.get("window"), list)]
    chains = {x["name"] for x in _chain_layers(info)}
    out = []
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0.0
        if i in (0, n - 1):
            out.append({"i": i, "tag": "photo", "t": round(t, 3), "beats": [], "generated": False})
            continue
        beats = [str(x["name"]) for x in layers if float(x["window"][0]) <= t <= float(x["window"][1])]
        in_end = end[0] <= t <= end[1]
        tag = " + ".join(beats + (["end"] if in_end else [])) or "camera"
        gen = any(b in chains for b in beats)
        out.append({"i": i, "tag": tag, "t": round(t, 3), "beats": beats, "end": in_end, "generated": gen})
    return out


def _measure(key: str, value: Any, unit: str, bar: Json | None = None, past: bool | None = None) -> Json:
    return {"key": key, "value": value, "unit": unit, "bar": bar, "past": past, "hint": f"info.{key}"}


def measures(info: Json, first_beat: int | None) -> list[Json]:
    """The measures of b_director_research.md §3 with their units; the two with a bar carry it and whether the value
    is past it: residual_edge_max against 0.2 % of the pixels (rule 5), b_inside_first against the first beat's
    start (rule 1). Every other measure states no bar."""
    rem = info.get("residual_edge_max")
    bif = info.get("b_inside_first")
    bif_bar = None
    bif_past = None
    if first_beat is not None:
        bif_bar = {
            "at_or_after": first_beat,
            "text": f"at or after the first beat's start, frame {first_beat} (rule 1)",
        }
        bif_past = bif is not None and int(bif) < first_beat
    return [
        _measure("motion_median_px", info.get("motion_median_px"), "px"),
        _measure("motion_pauses", info.get("motion_pauses"), "frames"),
        _measure("motion_jumps", info.get("motion_jumps"), "frames"),
        _measure("b_inside_first", bif, "frame", bif_bar, bif_past),
        _measure(
            "residual_edge_max",
            rem,
            "share of pixels",
            {"max": RESIDUAL_BAR, "text": "0.2 % of the pixels (rule 5)"},
            None if rem is None else float(rem) > RESIDUAL_BAR,
        ),
        _measure("halo_step_max", info.get("halo_step_max"), "levels"),
        _measure("halo_ring_max", info.get("halo_ring_max"), "levels"),
        _measure("guard_share_max", info.get("guard_share_max"), "share of the frame"),
        _measure("step_first", info.get("step_first"), "levels"),
        _measure("step_second", info.get("step_second"), "levels"),
        _measure("step_last", info.get("step_last"), "levels"),
        _measure("step_max", info.get("step_max"), "levels"),
        _measure("plate_A_share", info.get("plate_A_share"), "share of A"),
        _measure("matte_fallbacks", info.get("matte_fallbacks") or [], "elements"),
        _measure("unplaced", info.get("unplaced") or [], "transforms"),
        _measure("wall_s", info.get("wall_s"), "s"),
    ]


def motion_marks(mp: list[float]) -> tuple[list[int], list[int]]:
    """The renderer's pauses and jumps on motion_px (director_render.py:2047-2051): a pause is an entry between 10 %
    and 90 % of the list under a fifth of their median; a jump is an entry that differs from the one before by more
    than the larger of 1 px and half that median (the jump's second entry is marked)."""
    n = len(mp)
    mid = [(j, m) for j, m in enumerate(mp) if 0.1 * n <= j <= 0.9 * n]
    vals = sorted(m for _, m in mid)
    if not vals:
        return [], []
    k = len(vals)
    med = vals[k // 2] if k % 2 else (vals[k // 2 - 1] + vals[k // 2]) / 2
    pauses = [j for j, m in mid if m < 0.2 * med] if med > 0 else [j for j, _ in mid]
    jumps = [j + 1 for j in range(n - 1) if abs(mp[j + 1] - mp[j]) > max(1.0, 0.5 * med)]
    return pauses, jumps


def series(info: Json, steps: list[float]) -> Json:
    """The plots' series, each at its own frame index: motion_px and the decoded steps between frames j and j + 1,
    b_inside on every third frame and the last, residual_edges and halo on every third interior frame."""
    mp = [float(x) for x in info.get("motion_px") or []]
    pauses, jumps = motion_marks(mp)
    halo = info.get("halo")
    return {
        "motion_px": {
            "points": [[j, v] for j, v in enumerate(mp)],
            "pairwise": True,
            "unit": "px",
            "pauses": pauses,
            "jumps": jumps,
            "hint": "info.motion_px",
        },
        "steps": {
            "points": [[j, v] for j, v in enumerate(steps)],
            "pairwise": True,
            "unit": "levels",
            "source": "decoded",
            "hint": "info.steps_decoded",
        },
        "b_inside": {
            "points": [list(p) for p in info.get("b_inside") or []],
            "pairwise": False,
            "unit": "share",
            "first": info.get("b_inside_first"),
            "threshold": B_INSIDE_THRESHOLD,
            "hint": "info.b_inside",
        },
        "residual_edges": {
            "points": [list(p) for p in info.get("residual_edges") or []],
            "pairwise": False,
            "unit": "share of pixels",
            "bar": RESIDUAL_BAR,
            "hint": "info.residual_edges",
        },
        "halo": None
        if halo is None
        else {"points": [list(p) for p in halo], "pairwise": False, "unit": "levels", "hint": "info.halo"},
    }


def provenance(rec: Json | None, info: Json) -> Json:
    """What made the render: the record's script md5 and inputs (the plan's full sha256, transitions.py's md5) beside
    the stamps info.json carries (the renderer's md5, transitions.py's, the plan's first 16 characters)."""
    inputs = (rec or {}).get("inputs") or []
    plan_in = next((i for i in inputs if str(i.get("path", "")).endswith(".json") and "sha256" in i), None)
    tr_in = next((i for i in inputs if str(i.get("path", "")).endswith("transitions.py")), None)
    return {
        "record": (rec or {}).get("id"),
        "renderer_md5": info.get("renderer_md5"),
        "script_md5": (rec or {}).get("script_md5"),
        "transitions_md5": info.get("transitions_md5"),
        "transitions_md5_record": (tr_in or {}).get("md5"),
        "plan": (plan_in or {}).get("path"),
        "plan_sha256": (plan_in or {}).get("sha256"),
        "plan_sha256_16": info.get("plan_sha256"),
    }


def render_view(settings: Settings, d: Path, job: Json, kind: str, name: str) -> Json:
    """GET /api/jobs/<id>/render/<kind>/<name> for a director job: the base view plus info.json's measures, series
    and frame tags, the record's provenance (the plan's full sha256, transitions.py's md5) and its knobs."""
    own = base_render_view(settings, d, job, kind, name, DEFAULT_FPS)
    c = candidate(settings, d, job, kind, name)
    info = read_json(c["dir"] / "info.json") or {}
    rec = _record_of(d, c)
    n = int(info.get("frames") or own.get("frames") or 0)
    starts = [float(x["window"][0]) for x in info.get("layers") or [] if isinstance(x, dict) and x.get("window")]
    first_beat = round(min(starts) * (n - 1)) if starts and n > 1 else None
    own["frames_tags"] = frame_tags(info, n, _end_window(settings, rec, info))
    own["measures"] = measures(info, first_beat)
    own["series"] = series(info, step_series(d, c))
    own["provenance"] = provenance(rec, info)
    own["knobs"] = info.get("knobs") or {}
    own["record_knobs"] = (rec or {}).get("knobs") or {}
    own["concept"] = info.get("concept")
    own["layers"] = [
        {k: x.get(k) for k in ("name", "by", "window", "depth", "soft")}
        for x in info.get("layers") or []
        if isinstance(x, dict)
    ]
    own["motion"] = info.get("motion") or {}
    own["guard"] = info.get("guard") or []
    own["generated_layers"] = [
        {"name": x["name"], "keyframes": (x.get("chain") or {}).get("keyframes") or []} for x in _chain_layers(info)
    ]
    return own
