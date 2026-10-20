#!/usr/bin/env python3
"""The director's workbench, phase 1 (slice UI1, 2026-10-21; a research script, not a tool).

One local page over the grade -> plan -> render -> grade loop of the director rounds
(design: .claude/claude-docs/research/2026-10-20/ui_design.md sections 3-5 and 7). It serves
127.0.0.1 only, opens no outbound connection, imports neither `reveal` nor `transitions` nor any
research script: every heavy call is a subprocess of .venv/bin/python (`reveal.py align`,
`transitions.py pair`, `scripts/research/director_render.py`). numpy and cv2 are used in this
process only to turn layers.npz, the mattes and the rendered mp4 into PNGs.

State is the job folder on disk and nothing else:
  benchmarks/runs/<runs-date>/workbench/<job_id>/
    job.json                       {id, kind, pair, inputs: [{path, sha256}], created, ui_version}
    tasks/<tid>.json, <tid>.log    one per subprocess: argv, pid, state, progress, started, ended, exit_code
    analysis/reveal/ (metrics.json or verdict.json with the refusal), analysis/transitions/,
    analysis/resolve/ (only when the renderer has --resolve-only), analysis/overlays/ (cache)
    plans/                         byte copies of the frozen plans a render used
    renders/<rid>/                 transition.mp4, montage.jpg, info.json, render.json, log.txt, frames/
    picks/director_picks_<stamp>.json
    owner_frames/                  frames the owner marked

Usage:
  .venv/bin/python scripts/research/director_ui.py [--port 8379] [--no-browser] [--runs-date 2026-10-21]
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
import cv2

UI_VERSION = "ui1-2026-10-21"
ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / ".venv" / "bin" / "python"
FIX = ROOT / "fixtures"
LAYERS = ROOT / "benchmarks/runs/2026-09-28/layers_v3"
MATTES = ROOT / "benchmarks/runs/2026-10-17/mattes"
PLANS = ROOT / "scripts/research/plans"
RENDERER = ROOT / "scripts/research/director_render.py"
TRANSITIONS = ROOT / "transitions.py"
REVEAL = ROOT / "reveal.py"
RUNS = ROOT / "benchmarks/runs"
WORK = None                                   # set in main(): RUNS / <runs-date> / "workbench"
ID_RE = re.compile(r"^[A-Za-z0-9_\-]{1,80}$")
BODY_CAP = 1 << 20
OVERLAY_LONG = 960                            # overlays and the base photo are served at this long side
PROCS = {}                                    # (job_id, tid) -> Popen, only processes this server started
TASK_LOCK = threading.Lock()
FRAME_LOCKS = {}


def now_iso():
    return dt.datetime.now().isoformat(timespec="seconds")


def stamp():
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def md5_file(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_json(p, default=None):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return default


def write_json(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1))
    os.replace(tmp, p)


def renderer_flags():
    """Which of the three default-off renderer flags exist today (the main session adds them)."""
    try:
        src = RENDERER.read_text()
    except OSError:
        src = ""
    return {"progress": "--progress" in src, "resolve_only": "--resolve-only" in src,
            "stamp": "renderer_md5" in src}


# ----------------------------------------------------------------------------- inputs
def fixture_photo(photo):
    """fixtures/<photo>.<ext> for photo ids like mismatch_3_S."""
    hits = sorted(p for p in FIX.glob(f"{photo}.*") if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".heic", ".tif", ".tiff"))
    return hits[0] if hits else None


def plan_round(p):
    m = re.search(r"_r(\d+)$", p.stem)
    return int(m.group(1)) if m else 0


def plans_for(pair):
    ps = [p for p in PLANS.glob(f"{pair}*.json") if re.fullmatch(re.escape(pair) + r"(_r\d+)?", p.stem)]
    return sorted(ps, key=lambda p: (plan_round(p), p.stem))


def list_pairs():
    out = []
    for s in sorted(FIX.glob("*_S.*")):
        pair = s.stem[:-2]
        plans = plans_for(pair)
        if not plans:
            continue
        row = {"pair": pair, "plans": [p.stem for p in plans], "default_plan": plans[-1].stem, "photos": {}}
        for side, suf in (("A", "_S"), ("B", "_F")):
            ph = pair + suf
            fp = fixture_photo(ph)
            mdir = MATTES / ph
            row["photos"][side] = {"photo": ph, "file": fp.name if fp else None,
                                   "layers": (LAYERS / ph / "layers.json").exists() and (LAYERS / ph / "layers.npz").exists(),
                                   "mattes": len(list(mdir.glob("el_*.png"))) if mdir.exists() else 0}
        out.append(row)
    return out


def layer_table(photo):
    return read_json(LAYERS / photo / "layers.json")


# ----------------------------------------------------------------------------- knob map (plan knob name -> --set key)
# The renderer's global keys and where it reads their defaults (director_render.py, grep `knobs.get(`).
# Each row: key, kind, a function of the concept giving the renderer's effective default, the note.
def _g(d, *path, default=None):
    for k in path:
        if not isinstance(d, dict) or k not in d:
            return default
        d = d[k]
    return d


GLOBALS = [
    ("parallax_push", "num", lambda c: _g(c, "pullback", "parallax", "push", default=2.5 if _g(c, "container", "kind") in ("quad", "rect") else 0.0), "how far B's near content is pushed toward the camera during the pull-back"),
    ("parallax_gain", "num", lambda c: _g(c, "pullback", "parallax", "gain", default=0.3), "depth parallax gain"),
    ("parallax_gain_A", "num", lambda c: _g(c, "pullback", "parallax", "gain_A", default=_g(c, "pullback", "parallax", "gain", default=0.3)), "depth parallax gain inside A"),
    ("parallax_blur", "num", lambda c: _g(c, "pullback", "parallax", "blur", default=6.0), "blur of the disparity map, px"),
    ("push_floor", "num", lambda c: _g(c, "pullback", "parallax", "push_floor", default=0.3), "the push's floor"),
    ("front_in", "num", lambda c: _g(c, "pullback", "parallax", "front_in", default=0.15), "when B's front layer enters"),
    ("front_margin", "num", lambda c: _g(c, "container", "spec", "front_margin", default=0.05), "margin around the container for B's front"),
    ("front_per_element", "bool", lambda c: True, "B's front as one layer per element"),
    ("front_hole_max", "num", lambda c: 0.005, "largest enclosed hole in B's front that is filled (share of frame)"),
    ("cont_feather", "num", lambda c: _g(c, "container", "params", "feather_px", default=1.0), "the container's edge feather, px"),
    ("reflect", "num", lambda c: _g(c, "container", "params", "reflect", default=_g(c, "container", "spec", "reflect", default=0.18)), "glass rim: B's glass over A"),
    ("end_scale", "num", lambda c: _g(c, "pullback", "params", "end_scale"), "the pull-back's end scale (empty: the renderer derives it)"),
    ("plate", "bool", lambda c: True, "fill A under its lifted layers"),
    ("plate_fill", "enum:pullpush|telea", lambda c: "pullpush", "the plate fill method"),
    ("motion", "enum:continuous|legacy", lambda c: _g(c, "motion", "kind", default="legacy"), "the motion model (round 12)"),
    ("guard", "bool", lambda c: bool(_g(c, "reveal", "guard", default=_g(c, "motion", "kind") == "continuous")), "the reveal guard (round 12)"),
    ("end_band", "num", lambda c: _g(c, "end_effect", "params", "band", default=0.16), "the end effect's band"),
    ("vacated_first", "num", lambda c: _g(c, "end_effect", "params", "vacated_first", default=0.35), "the end effect's vacated-first share"),
    ("hole_reveal_from", "num", lambda c: 0.1, "when holes start to reveal"),
    ("hole_reveal_over", "num", lambda c: 0.35, "over how long holes reveal"),
    ("key_end", "num", lambda c: _g(c, "container", "params", "sky", "key_end", default=0.45), "sky key window end"),
]
GLOBAL_KEYS = {g[0] for g in GLOBALS}
# pullback / container / end_effect paths the renderer reads under a different key
PATH_KEYS = {
    ("pullback", "parallax", "gain"): "parallax_gain", ("pullback", "parallax", "gain_A"): "parallax_gain_A",
    ("pullback", "parallax", "push"): "parallax_push", ("pullback", "parallax", "blur"): "parallax_blur",
    ("pullback", "parallax", "sources"): "parallax_sources", ("pullback", "parallax", "a_elements"): "parallax_A_elements",
    ("pullback", "parallax", "push_floor"): "push_floor", ("pullback", "parallax", "front_in"): "front_in",
    ("pullback", "params", "end_scale"): "end_scale",
    ("container", "params", "reflect"): "reflect", ("container", "params", "feather_px"): "cont_feather",
    ("container", "params", "sky"): "sky", ("container", "spec", "front_ids"): "front_ids",
    ("container", "spec", "front_margin"): "front_margin",
    ("end_effect", "window"): "end_window", ("end_effect", "kind"): "end_kind",
    ("end_effect", "params", "band"): "end_band", ("end_effect", "params", "vacated_first"): "vacated_first",
}
DIRECT_KEYS = GLOBAL_KEYS | {"front_ids", "parallax_A_elements", "parallax_sources", "sky", "end_window"}


def parse_knob_name(name):
    m = re.fullmatch(r"([A-Za-z_]\w*)((?:\.[A-Za-z_]\w*|\[\d+\])*)", name or "")
    if not m:
        return None
    toks = [t[0] if t[0] else int(t[1]) for t in re.findall(r"\.([A-Za-z_]\w*)|\[(\d+)\]", m.group(2))]
    return [m.group(1)] + toks


def map_knob(name, c):
    """A plan knob -> {cli_key, base, path} or {readonly: reason}. `base` is the plan's value under
    the CLI key, `path` the index/key path from it to the knob's leaf (empty: the knob is the value)."""
    toks = parse_knob_name(name)
    if not toks:
        return {"readonly": "not a dotted path; no renderer key"}
    trs = {t["name"]: t for t in c.get("transforms", [])}
    head = toks[0]
    if head in trs:
        t = trs[head]
        if len(toks) < 2 or not isinstance(toks[1], str):
            return {"readonly": "a transform name without a field"}
        f = toks[1]
        if f == "window":
            key, base, rest = f"{head}.window", t.get("window", [0, 1]), toks[2:]
        elif f == "params" and len(toks) >= 3 and isinstance(toks[2], str):
            key, base, rest = f"{head}.{toks[2]}", (t.get("params") or {}).get(toks[2]), toks[3:]
        elif f in ("skip", "mix"):
            key, base, rest = f"{head}.{f}", t.get(f), toks[2:]
        else:
            return {"readonly": f"the renderer reads only window, mix, skip and params.* of a transform, not '{f}'"}
    else:
        key = base = rest = None
        for n in (3, 2):
            pk = tuple(toks[:n])
            if len(pk) == n and pk in PATH_KEYS:
                key = PATH_KEYS[pk]; base = _g(c, *[x for x in pk]); rest = toks[n:]
                break
        if key is None:
            if head in DIRECT_KEYS:
                key, rest = head, toks[1:]
                base = {"front_ids": _g(c, "container", "spec", "front_ids")}.get(head)
                if base is None:
                    g = next((g for g in GLOBALS if g[0] == head), None)
                    base = g[2](c) if g else None
            else:
                return {"readonly": f"no renderer key reads '{name}' (director_render.py knobs.get list)"}
    if rest and base is None:
        return {"readonly": f"'{name}' indexes into a value the plan does not hold"}
    return {"cli_key": key, "base": base, "path": rest}


def concept_view(plan, c, last_knobs):
    knobs = []
    for k in c.get("knobs", []):
        row = {"name": k.get("name"), "range": k.get("range"), "default": k.get("default"), "what": k.get("what", "")}
        row.update(map_knob(k.get("name"), c))
        knobs.append(row)
    globs = [{"key": g[0], "kind": g[1], "default": g[2](c), "what": g[3]} for g in GLOBALS]
    beats = [{"name": t["name"], "by": t.get("by"), "window": t.get("window", [0, 1])} for t in c.get("transforms", [])]
    ee = c.get("end_effect") or {}
    return {"id": c["id"], "rank": c.get("rank"), "idea": c.get("idea", ""), "risk": c.get("risk", ""),
            "motion": c.get("motion"), "reveal": c.get("reveal"), "knobs": knobs, "globals": globs, "beats": beats,
            "end_effect": {"kind": ee.get("kind"), "window": ee.get("window")} if ee else None,
            "last_round": last_knobs}


def last_round_knobs(stem, cid):
    """The operator knobs of the newest round render of this plan and concept (director_r*/<stem>_<cid>/info.json)."""
    best = None
    for p in RUNS.glob(f"*/director_r*/{stem}_{cid}/info.json"):
        if best is None or p.stat().st_mtime > best.stat().st_mtime:
            best = p
    if not best:
        return None
    info = read_json(best, {})
    return {"from": str(best.relative_to(ROOT)), "knobs": info.get("knobs") or {}, "wall_s": info.get("wall_s"),
            "canvas": info.get("canvas")}


def plan_view(stem):
    p = PLANS / f"{stem}.json"
    plan = read_json(p)
    if not plan:
        return None
    return {"stem": stem, "path": str(p.relative_to(ROOT)), "sha256": sha256_file(p), "pair": plan.get("pair"),
            "relation": plan.get("relation"), "reading": plan.get("reading"), "planner": plan.get("planner"),
            "concepts": [concept_view(plan, c, last_round_knobs(stem, c["id"])) for c in plan.get("concepts", [])]}


# ----------------------------------------------------------------------------- jobs and tasks
def job_dir(jid):
    if not ID_RE.match(jid or ""):
        return None
    d = WORK / jid
    return d if (d / "job.json").exists() else None


def create_job(pair):
    if not any(r["pair"] == pair for r in list_pairs()):
        raise ValueError(f"unknown pair or no plan: {pair}")
    jid = f"{pair}_{stamp()}_{secrets.token_hex(2)}"
    d = WORK / jid
    for sub in ("tasks", "analysis", "plans", "renders", "picks", "owner_frames"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    inputs = []
    for suf in ("_S", "_F"):
        fp = fixture_photo(pair + suf)
        inputs.append({"path": str(fp.relative_to(ROOT)), "sha256": sha256_file(fp)})
    write_json(d / "job.json", {"id": jid, "kind": "pair", "pair": pair, "inputs": inputs, "created": now_iso(), "ui_version": UI_VERSION})
    start_analyze(d)
    return jid


def task_path(d, tid):
    return d / "tasks" / f"{tid}.json"


def start_task(d, kind, argv, meta=None, ok_codes=(0,), on_done=None, log_copy=None):
    tid = f"{kind}_{stamp()}_{secrets.token_hex(2)}"
    (d / "tasks").mkdir(exist_ok=True)
    logp = d / "tasks" / f"{tid}.log"
    t = {"id": tid, "kind": kind, "argv": [str(a) for a in argv], "pid": None, "state": "running", "progress": None,
         "started": now_iso(), "started_ts": time.time(), "ended": None, "exit_code": None, "wall_s": None, "meta": meta or {}}
    logf = open(logp, "wb")
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    p = subprocess.Popen([str(a) for a in argv], cwd=str(ROOT), stdout=logf, stderr=subprocess.STDOUT, env=env,
                         stdin=subprocess.DEVNULL, start_new_session=True)
    t["pid"] = p.pid
    with TASK_LOCK:
        PROCS[(d.name, tid)] = p
        write_json(task_path(d, tid), t)

    def wait():
        rc = p.wait()
        logf.close()
        with TASK_LOCK:
            cur = read_json(task_path(d, tid), t)
            cur.update(exit_code=rc, ended=now_iso(), wall_s=round(time.time() - t["started_ts"], 1))
            cur["state"] = "cancelled" if cur.get("cancel") else ("done" if rc in ok_codes else "failed")
            cur["progress"] = parse_progress(logp) or cur.get("progress")
            write_json(task_path(d, tid), cur)
            PROCS.pop((d.name, tid), None)
        if log_copy:
            try:
                shutil.copyfile(logp, log_copy)
            except OSError:
                pass
        if on_done:
            try:
                on_done(cur)
            except Exception as e:                      # recorded, never raised into the server
                with open(logp, "a") as f:
                    f.write(f"\n[director_ui] on_done failed: {e!r}\n")
    threading.Thread(target=wait, daemon=True).start()
    return tid


def parse_progress(logp):
    try:
        with open(logp, "rb") as f:
            f.seek(0, 2); n = f.tell(); f.seek(max(0, n - 65536))
            tail = f.read().decode("utf8", "replace")
    except OSError:
        return None
    hits = re.findall(r"PROGRESS\s+(\d+)\s+(\d+)", tail)
    return [int(hits[-1][0]), int(hits[-1][1])] if hits else None


def log_tail(logp, n=20):
    try:
        with open(logp, "rb") as f:
            f.seek(0, 2); size = f.tell(); f.seek(max(0, size - 16384))
            lines = f.read().decode("utf8", "replace").splitlines()
    except OSError:
        return []
    lines = [l if len(l) < 400 else l[:400] + " …" for l in lines if not re.match(r"^PROGRESS \d+ \d+$", l)]
    return lines[-n:]


def task_status(d, tid):
    t = read_json(task_path(d, tid))
    if not t:
        return None
    logp = d / "tasks" / f"{tid}.log"
    if t["state"] == "running" and (d.name, tid) not in PROCS:
        alive = False
        try:
            os.kill(int(t["pid"]), 0); alive = True
        except (OSError, TypeError, ValueError):
            pass
        if not alive:
            t["state"] = "lost"
    t["progress"] = parse_progress(logp) or t.get("progress")
    t["elapsed_s"] = round((time.time() - t["started_ts"]) if t["state"] == "running" else (t.get("wall_s") or 0), 1)
    t["log_tail"] = log_tail(logp)
    if t["kind"] == "render" and t["state"] == "running":
        t["expected_s"] = expected_wall(d, t["meta"])
    return t


def expected_wall(d, meta):
    """The fallback progress when the renderer prints no PROGRESS: the last wall_s of the same plan and size."""
    best = None
    for rj in sorted((d / "renders").glob("*/render.json")):
        r = read_json(rj, {})
        if r.get("plan_path") == meta.get("plan_path") and r.get("max_long") == meta.get("max_long") and r.get("wall_s"):
            best = r["wall_s"]
    return best


def cancel_task(d, tid):
    with TASK_LOCK:
        p = PROCS.get((d.name, tid))
        if not p:
            return False
        cur = read_json(task_path(d, tid), {})
        cur["cancel"] = True
        write_json(task_path(d, tid), cur)
    try:
        os.killpg(p.pid, signal.SIGTERM)             # the session we started (start_new_session) and nothing else
    except OSError:
        p.terminate()
    return True


# ----------------------------------------------------------------------------- analysis
def start_analyze(d):
    job = read_json(d / "job.json")
    S, F = (ROOT / job["inputs"][0]["path"]), (ROOT / job["inputs"][1]["path"])
    a = d / "analysis"
    tids = {}
    rv = a / "reveal"; rv.mkdir(parents=True, exist_ok=True)

    def reveal_done(t):
        logt = (d / "tasks" / f"{t['id']}.log").read_text(errors="replace")
        m = re.search(r"^FAILED:\s*(.*)$", logt, re.M)
        met = read_json(rv / "metrics.json")
        write_json(rv / "verdict.json", {"exit_code": t["exit_code"], "refused": t["exit_code"] == 2,
                                         "reason": m.group(1).strip() if m else None, "wall_s": t["wall_s"],
                                         "status": met})
    tids["reveal"] = start_task(d, "reveal", [PY, REVEAL, "align", S, F, "--out", rv], ok_codes=(0, 2), on_done=reveal_done)
    tp = a / "transitions"; tp.mkdir(parents=True, exist_ok=True)
    tids["transitions"] = start_task(d, "transitions", [PY, TRANSITIONS, "pair", S, F, "--out", tp, "--max-long", "480", "--seconds", "1"])
    fl = renderer_flags()
    if fl["resolve_only"]:
        stem = read_pairs_default(job["pair"])
        rs = a / "resolve"; rs.mkdir(parents=True, exist_ok=True)
        tids["resolve"] = start_task(d, "resolve", [PY, RENDERER, PLANS / f"{stem}.json", rs, "--resolve-only"])
    jj = read_json(d / "job.json"); jj["analysis_tasks"] = tids; write_json(d / "job.json", jj)
    return tids


def read_pairs_default(pair):
    ps = plans_for(pair)
    return ps[-1].stem if ps else None


def verdict_text(rv, tp):
    cls = (tp or {}).get("class")
    if rv is None:
        return "pending (Reveal still running)"
    st = (rv.get("status") or {})
    met = st.get("metrics") or {}
    if rv.get("refused"):
        rel = "unrelated" if cls == "B" else ("related, not aligned" if cls == "A" else "unrelated?")
        return f"{rel} (Reveal refused, class {cls or '?'})"
    if rv.get("exit_code") == 0:
        passed = met.get("passed", st.get("passed"))
        return f"{'aligned' if passed else 'aligned, Reveal did not pass its own check'} (Reveal confidence {met.get('confidence')}, class {cls or '?'})"
    return f"Reveal failed with exit {rv.get('exit_code')} (class {cls or '?'})"


def analysis_summary(d, job):
    a = d / "analysis"
    rv = read_json(a / "reveal" / "verdict.json")
    tp = read_json(a / "transitions" / "report.json")
    tps = None
    if tp:
        tps = {k: tp.get(k) for k in ("class", "method", "median_disp_px", "sparse_inliers", "sparse_rmse", "mean_certainty",
                                      "pan_fraction", "camera", "canvas", "total_s")}
    pair = job["pair"]
    tables = {}
    for side, suf in (("A", "_S"), ("B", "_F")):
        lt = layer_table(pair + suf)
        if lt:
            mdir = MATTES / (pair + suf)
            tables[side] = {"photo": pair + suf, "canvas": lt.get("canvas"),
                            "elements": [{"id": e["id"], "label": e.get("label"), "group": e.get("group"),
                                          "area_share": e.get("area_share"), "depth_rank": e.get("depth_rank"),
                                          "median_disparity": e.get("median_disparity"),
                                          "matte": (mdir / f"el_{e['id']}.png").exists()} for e in lt.get("elements", [])]}
    overlap = []
    if "A" in tables and "B" in tables:
        def by_label(t):
            o = {}
            for e in t["elements"]:
                o[e["label"]] = round(o.get(e["label"], 0) + (e["area_share"] or 0), 4)
            return o
        la, lb = by_label(tables["A"]), by_label(tables["B"])
        overlap = [{"label": k, "A": la[k], "B": lb[k]} for k in sorted(set(la) & set(lb), key=lambda k: -(la[k] + lb[k]))]
    resolve = None
    if (a / "resolve" / "anchors.json").exists():
        resolve = {"anchors": "analysis/resolve/anchors.json", "canvas_A": "analysis/resolve/canvas_A.png", "canvas_B": "analysis/resolve/canvas_B.png"}
    return {"verdict": verdict_text(rv, tp) if (rv or tp) else "pending", "reveal": rv, "transitions": tps,
            "tables": tables, "overlap": overlap, "resolve": resolve,
            "resolve_note": None if renderer_flags()["resolve_only"] else "the renderer has no --resolve-only yet: overlays come from the layer tables and mattes only"}


# ----------------------------------------------------------------------------- overlays (numpy + cv2 only)
GROUP_COLOURS = {"person": (230, 60, 60), "sky": (90, 160, 240), "building": (200, 160, 90), "wall": (170, 170, 120),
                 "plant": (60, 190, 80), "water": (40, 120, 200), "furniture": (180, 100, 200), "ceiling": (140, 140, 200),
                 "object": (240, 180, 40), "ground": (150, 110, 70), "vehicle": (240, 120, 20), "light": (255, 240, 120)}


def cover(img, w, h):
    H, W = img.shape[:2]
    s = max(w / W, h / H)
    r = cv2.resize(img, (max(w, round(W * s)), max(h, round(H * s))), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    y, x = (r.shape[0] - h) // 2, (r.shape[1] - w) // 2
    return r[y:y + h, x:x + w]


def overlay_png(d, side, kind):
    job = read_json(d / "job.json")
    photo = job["pair"] + ("_S" if side == "A" else "_F")
    cache = d / "analysis" / "overlays" / f"{side}_{kind}.png"
    if cache.exists():
        return cache.read_bytes(), None
    lt = layer_table(photo)
    if not lt:
        return None, f"no layer table for {photo}"
    w, h = lt["canvas"]
    s = min(1.0, OVERLAY_LONG / max(w, h))
    ow, oh = int(round(w * s)), int(round(h * s))
    if kind == "base":
        fp = fixture_photo(photo)
        img = cv2.imread(str(fp), cv2.IMREAD_COLOR) if fp else None
        if img is None:
            return None, f"cv2 cannot read {fp}"
        out = cv2.resize(cover(img, w, h), (ow, oh), interpolation=cv2.INTER_AREA)
    else:
        z = np.load(LAYERS / photo / "layers.npz")
        if kind == "elements":
            el = z["element"]
            col = np.zeros((h, w, 4), np.uint8)
            for e in lt["elements"]:
                c = np.array(GROUP_COLOURS.get(e.get("group"), (200, 200, 200)), np.float32)
                c = np.clip(c * (0.7 + 0.6 * ((e["id"] * 0.618) % 1.0)), 0, 255)
                col[el == e["id"]] = (int(c[2]), int(c[1]), int(c[0]), 150)
            edge = cv2.morphologyEx(el.astype(np.uint16).astype(np.float32), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
            col[edge] = (255, 255, 255, 230)
            out = cv2.resize(col, (ow, oh), interpolation=cv2.INTER_NEAREST)
        elif kind == "disparity":
            dsp = np.clip(z["disparity"], 0, 1)
            cm = cv2.applyColorMap((dsp * 255).astype(np.uint8), cv2.COLORMAP_TURBO)
            out = cv2.resize(np.dstack([cm, np.full((h, w), 200, np.uint8)]), (ow, oh), interpolation=cv2.INTER_AREA)
        elif re.fullmatch(r"matte_\d+", kind):
            eid = int(kind.split("_")[1])
            mf = MATTES / photo / f"el_{eid}.png"
            a = cv2.imread(str(mf), cv2.IMREAD_GRAYSCALE) if mf.exists() else None
            if a is None:
                a = (z["element"] == eid).astype(np.uint8) * 255      # no matte file: the hard element mask
            if a.shape != (h, w):
                a = cv2.resize(a, (w, h), interpolation=cv2.INTER_LINEAR)
            col = np.zeros((h, w, 4), np.uint8)
            col[..., 0] = 255; col[..., 1] = 0; col[..., 2] = 255
            col[..., 3] = (a.astype(np.float32) * 0.75).astype(np.uint8)
            cnt, _ = cv2.findContours((a > 127).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(col, cnt, -1, (0, 255, 255, 255), max(2, int(3 / s)))
            out = cv2.resize(col, (ow, oh), interpolation=cv2.INTER_AREA)
        else:
            return None, f"unknown overlay kind {kind}"
    ok, buf = cv2.imencode(".png", out)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(buf.tobytes())
    return buf.tobytes(), None


# ----------------------------------------------------------------------------- renders
def start_render(d, spec):
    plan_rel = spec.get("plan") or ""
    plan_p = (ROOT / plan_rel).resolve()
    if plan_p.parent != PLANS.resolve() or plan_p.suffix != ".json" or not plan_p.exists():
        raise ValueError(f"plan must be a file in scripts/research/plans/: {plan_rel}")
    plan = read_json(plan_p)
    concept = spec.get("concept") or plan["concepts"][0]["id"]
    if not any(c["id"] == concept for c in plan["concepts"]):
        raise ValueError(f"no concept {concept} in {plan_p.name}")
    max_long = int(spec.get("max_long", 480))
    if max_long not in (480, 1920):
        raise ValueError("max_long must be 480 or 1920")
    seconds = float(spec.get("seconds", 3.0)); fps = int(spec.get("fps", 30))
    if not (0.5 <= seconds <= 20 and 1 <= fps <= 60):
        raise ValueError("seconds 0.5-20, fps 1-60")
    knobs = spec.get("knobs") or {}
    if not isinstance(knobs, dict):
        raise ValueError("knobs must be an object {cli_key: value}")
    for k in knobs:
        if not re.fullmatch(r"[A-Za-z_]\w*(\.[A-Za-z_]\w*)?", k):
            raise ValueError(f"bad knob key {k!r}")
    rid = f"r{stamp()}_{max_long}_{secrets.token_hex(2)}"
    rdir = d / "renders" / rid
    rdir.mkdir(parents=True)
    copy = d / "plans" / plan_p.name
    if not copy.exists() or md5_file(copy) != md5_file(plan_p):
        shutil.copyfile(plan_p, copy)
    argv = [PY, RENDERER, plan_p.relative_to(ROOT), rdir.relative_to(ROOT), "--concept", concept,
            "--max-long", str(max_long), "--seconds", f"{seconds:g}", "--fps", str(fps)]
    for k, v in knobs.items():
        argv += ["--set", f"{k}={json.dumps(v)}"]
    fl = renderer_flags()
    if fl["progress"]:
        argv.append("--progress")
    rj = {"argv": [str(a) for a in argv], "plan_path": str(plan_p.relative_to(ROOT)), "plan_sha256": sha256_file(plan_p),
          "concept": concept, "knobs": knobs, "max_long": max_long, "seconds": seconds, "fps": fps,
          "draft": max_long < 1920, "renderer_md5": md5_file(RENDERER), "transitions_md5": md5_file(TRANSITIONS),
          "renderer_flags": fl, "started": now_iso(), "wall_s": None, "md5_mp4": None, "state": "running",
          "from_render": spec.get("from_render")}
    write_json(rdir / "render.json", rj)

    def done(t):
        r = read_json(rdir / "render.json", rj)
        info = read_json(rdir / "info.json") or {}
        mp4 = rdir / "transition.mp4"
        r.update(state=t["state"], exit_code=t["exit_code"], task=t["id"], wall_s=info.get("wall_s"), process_wall_s=t["wall_s"],
                 md5_mp4=md5_file(mp4) if mp4.exists() and t["state"] == "done" else None, ended=t["ended"])
        for k in ("renderer_md5", "transitions_md5"):
            if info.get(k) and info[k] != r[k]:
                r[k + "_info"] = info[k]                # the renderer's own stamp disagrees with the launch-time hash
        write_json(rdir / "render.json", r)
    meta = {"rid": rid, "plan_path": rj["plan_path"], "max_long": max_long, "progress_flag": fl["progress"]}
    tid = start_task(d, "render", argv, meta=meta, on_done=done, log_copy=rdir / "log.txt")
    r = read_json(rdir / "render.json"); r["task"] = tid; write_json(rdir / "render.json", r)
    return rid, tid


def rerender_spec(d, rid):
    r = read_json(d / "renders" / rid / "render.json")
    if not r:
        raise ValueError(f"no render.json for {rid}")
    return {"plan": r["plan_path"], "concept": r["concept"], "knobs": r["knobs"], "max_long": r["max_long"],
            "seconds": r["seconds"], "fps": r["fps"], "from_render": rid}


def list_renders(d):
    out = []
    for rj in sorted((d / "renders").glob("*/render.json")):
        r = read_json(rj, {})
        r["rid"] = rj.parent.name
        r["has_info"] = (rj.parent / "info.json").exists()
        out.append(r)
    return out


def extract_frames(d, rid):
    """Decode the clip once into frames/<i>.png and the step profile (mean |frame_i - frame_i-1|, the
    renderer's step measure) into frames/steps.json."""
    rdir = d / "renders" / rid
    fdir = rdir / "frames"
    meta = fdir / "steps.json"
    lock = FRAME_LOCKS.setdefault((d.name, rid), threading.Lock())
    with lock:
        if meta.exists():
            return read_json(meta)
        mp4 = rdir / "transition.mp4"
        if not mp4.exists():
            raise ValueError("no transition.mp4 yet")
        fdir.mkdir(exist_ok=True)
        cap = cv2.VideoCapture(str(mp4))
        prev = None; steps = []; i = 0
        while True:
            ok, fr = cap.read()
            if not ok:
                break
            cv2.imwrite(str(fdir / f"{i:05d}.png"), fr)
            if prev is not None:
                steps.append(round(float(np.abs(fr.astype(np.float32) - prev).mean()), 3))
            prev = fr.astype(np.float32); i += 1
        cap.release()
        m = {"n": i, "steps": steps}
        write_json(meta, m)
        return m


# ----------------------------------------------------------------------------- picks
PICK_TOP = {"date", "page", "best", "clips"}
PICK_CLIP = {"acceptable", "note", "props"}
PICK_CLIP_OPT = {"frames", "render", "draft"}
PICK_PROPS = {"one_picture", "transforms", "not_invented"}


def save_picks(d, obj):
    if set(obj) != PICK_TOP:
        raise ValueError(f"picks keys must be exactly {sorted(PICK_TOP)}")
    if not isinstance(obj["best"], dict) or not isinstance(obj["clips"], dict):
        raise ValueError("best and clips must be objects")
    for tag, c in obj["clips"].items():
        if not (PICK_CLIP <= set(c) <= PICK_CLIP | PICK_CLIP_OPT):
            raise ValueError(f"clip {tag}: keys {sorted(c)}")
        if set(c["props"]) != PICK_PROPS:
            raise ValueError(f"clip {tag}: props must be exactly {sorted(PICK_PROPS)}")
    p = d / "picks" / f"director_picks_{stamp()}.json"
    write_json(p, obj)
    return p


# ----------------------------------------------------------------------------- job status
def job_status(d):
    job = read_json(d / "job.json")
    tasks = []
    for tp in sorted((d / "tasks").glob("*.json")):
        t = task_status(d, tp.stem)
        if t:
            tasks.append({k: t.get(k) for k in ("id", "kind", "state", "progress", "elapsed_s", "exit_code", "started", "ended", "wall_s", "meta", "pid")})
    picks = sorted((d / "picks").glob("director_picks_*.json"))
    return {"job": job, "tasks": tasks, "analysis": analysis_summary(d, job),
            "plans": [p.stem for p in plans_for(job["pair"])], "default_plan": read_pairs_default(job["pair"]),
            "renders": list_renders(d), "renderer_flags": renderer_flags(),
            "last_picks": read_json(picks[-1]) if picks else None,
            "last_picks_path": str(picks[-1].relative_to(ROOT)) if picks else None,
            "dir": str(d.relative_to(ROOT))}


def safe_file(d, rel):
    """A path under the job folder, or under fixtures/, layers/ or mattes/ (prefix names); anything else is refused."""
    rel = rel.lstrip("/")
    roots = {"fixtures/": FIX, "layers/": LAYERS, "mattes/": MATTES}
    base = d
    for pre, r in roots.items():
        if rel.startswith(pre):
            base, rel = r, rel[len(pre):]
            break
    p = (base / rel).resolve()
    b = base.resolve()
    if p != b and b not in p.parents:
        return None
    return p if p.is_file() else None


CTYPES = {".mp4": "video/mp4", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".json": "application/json",
          ".txt": "text/plain; charset=utf-8", ".log": "text/plain; charset=utf-8"}


# ----------------------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    server_version = f"DirectorUI/{UI_VERSION}"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _send(self, code, body, ctype="application/json", extra=None):
        data = body if isinstance(body, (bytes, bytearray)) else json.dumps(body).encode("utf8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        try:
            if self.command != "HEAD":
                self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _err(self, code, msg):
        self._send(code, {"error": msg})

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > BODY_CAP:
            raise ValueError("request too large")
        buf = b""
        while len(buf) < n:
            chunk = self.rfile.read(min(1 << 16, n - len(buf)))
            if not chunk:
                break
            buf += chunk
        if len(buf) != n:
            raise ValueError("truncated request body")
        return json.loads(buf.decode("utf8") or "{}") if n else {}

    def _file(self, p):
        size = p.stat().st_size
        ctype = CTYPES.get(p.suffix.lower(), "application/octet-stream")
        rng = self.headers.get("Range")
        m = re.match(r"bytes=(\d*)-(\d*)$", rng or "")
        if m and (m.group(1) or m.group(2)):
            if m.group(1):
                a = int(m.group(1)); b = int(m.group(2)) if m.group(2) else size - 1
            else:
                a = max(0, size - int(m.group(2))); b = size - 1
            b = min(b, size - 1)
            if a > b:
                return self._send(416, b"", "text/plain", {"Content-Range": f"bytes */{size}"})
            with open(p, "rb") as f:
                f.seek(a); data = f.read(b - a + 1)
            return self._send(206, data, ctype, {"Content-Range": f"bytes {a}-{b}/{size}", "Accept-Ranges": "bytes"})
        return self._send(200, p.read_bytes(), ctype, {"Accept-Ranges": "bytes"})

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        q = dict(kv.split("=", 1) for kv in (self.path.split("?", 1)[1].split("&") if "?" in self.path else []) if "=" in kv)
        try:
            if path == "/":
                return self._send(200, PAGE.encode("utf8"), "text/html; charset=utf-8")
            if path == "/api/pairs":
                return self._send(200, {"pairs": list_pairs(), "renderer_flags": renderer_flags(), "work": str(WORK.relative_to(ROOT))})
            if path == "/api/jobs":
                jobs = []
                for jj in sorted(WORK.glob("*/job.json"), reverse=True):
                    j = read_json(jj, {})
                    jobs.append({"id": j.get("id"), "pair": j.get("pair"), "created": j.get("created"),
                                 "renders": len(list((jj.parent / "renders").glob("*/render.json")))})
                return self._send(200, {"jobs": jobs})
            m = re.match(r"^/api/plans/([A-Za-z0-9_\-]+)$", path)
            if m:
                v = plan_view(m.group(1))
                return self._send(200, v) if v else self._err(404, "unknown plan")
            m = re.match(r"^/api/jobs/([^/]+)(/.*)?$", path)
            if not m:
                return self._err(404, "not found")
            d = job_dir(m.group(1))
            if not d:
                return self._err(404, "unknown job")
            sub = m.group(2) or ""
            if sub == "":
                return self._send(200, job_status(d))
            mm = re.match(r"^/overlay/(A|B)/([a-z0-9_]+)\.png$", sub)
            if mm:
                data, err = overlay_png(d, mm.group(1), mm.group(2))
                return self._send(200, data, "image/png") if data else self._err(404, err)
            mm = re.match(r"^/file/(.+)$", sub)
            if mm:
                p = safe_file(d, mm.group(1))
                return self._file(p) if p else self._err(403, "refused: not a file under the job folder, fixtures/, layers/ or mattes/")
            mm = re.match(r"^/tasks/([^/]+)$", sub)
            if mm and ID_RE.match(mm.group(1)):
                t = task_status(d, mm.group(1))
                return self._send(200, t) if t else self._err(404, "unknown task")
            if sub == "/frame":
                rid, i = q.get("rid", ""), int(q.get("i", "0"))
                if not ID_RE.match(rid):
                    return self._err(400, "bad rid")
                meta = extract_frames(d, rid)
                i = max(0, min(meta["n"] - 1, i))
                return self._file(d / "renders" / rid / "frames" / f"{i:05d}.png")
            return self._err(404, "not found")
        except ValueError as e:
            return self._err(400, str(e))
        except Exception as e:
            return self._err(500, f"server error: {e!r}")

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        try:
            body = self._body()
            if path == "/api/jobs":
                return self._send(200, {"id": create_job(str(body.get("pair", "")))})
            m = re.match(r"^/api/jobs/([^/]+)(/.*)$", path)
            if not m:
                return self._err(404, "not found")
            d = job_dir(m.group(1))
            if not d:
                return self._err(404, "unknown job")
            sub = m.group(2)
            if sub == "/analyze":
                return self._send(200, {"tasks": start_analyze(d)})
            if sub == "/render":
                spec = rerender_spec(d, body["from_render"]) if body.get("from_render") else body
                rid, tid = start_render(d, spec)
                return self._send(200, {"rid": rid, "task": tid})
            mm = re.match(r"^/tasks/([^/]+)/cancel$", sub)
            if mm and ID_RE.match(mm.group(1)):
                return self._send(200, {"ok": cancel_task(d, mm.group(1))})
            if sub == "/frame":
                rid, i = str(body.get("rid", "")), int(body.get("index", 0))
                if not ID_RE.match(rid):
                    return self._err(400, "bad rid")
                meta = extract_frames(d, rid)
                i = max(0, min(meta["n"] - 1, i))
                rel = f"renders/{rid}/frames/{i:05d}.png"
                out = {"path": rel, "index": i, "n": meta["n"], "steps": meta["steps"]}
                if body.get("mark"):
                    dst = d / "owner_frames" / f"{rid}_f{i:05d}.png"
                    shutil.copyfile(d / rel, dst)
                    out["marked"] = f"owner_frames/{dst.name}"
                return self._send(200, out)
            if sub == "/picks":
                p = save_picks(d, body)
                return self._send(200, {"path": str(p.relative_to(ROOT))})
            return self._err(404, "not found")
        except (ValueError, KeyError) as e:
            return self._err(400, str(e))
        except Exception as e:
            return self._err(500, f"server error: {e!r}")


# ----------------------------------------------------------------------------- the page
PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>director workbench</title>
<style>
body{font:13px/1.4 Menlo,Monaco,monospace;margin:0;color:#111;background:#fafafa}
#rail{position:fixed;left:0;top:0;bottom:0;width:230px;overflow:auto;border-right:1px solid #bbb;padding:6px;background:#f0f0f0}
#main{margin-left:246px;padding:6px 12px}
.tabs button{margin-right:4px} .tabs button.on{background:#333;color:#fff}
.panel{display:none} .panel.on{display:block}
table{border-collapse:collapse} td,th{border:1px solid #ccc;padding:1px 5px;text-align:left;vertical-align:top}
tr.sel{background:#ffe9a8} .ro{color:#999} .warn{color:#b40} .ok{color:#070} .muted{color:#777}
.stack{position:relative;display:inline-block;margin:4px} .stack img{display:block;max-width:560px} .stack img.ov{position:absolute;left:0;top:0;width:100%}
#tl{position:relative;width:900px;border:1px solid #888;background:#fff;user-select:none}
.bar{position:absolute;height:18px;background:#7ab;border:1px solid #246;cursor:grab;font-size:11px;overflow:hidden;white-space:nowrap;color:#012}
.bar.end{background:#c9a} .bar.mute{opacity:.3} .bar.changed{background:#fb6}
pre{background:#eee;padding:4px;max-height:260px;overflow:auto;white-space:pre-wrap;margin:2px 0}
video{max-width:640px;background:#000;display:block} .cmp img{max-width:300px;margin-right:4px}
input[type=number]{width:70px} textarea{width:640px} svg{background:#fff;border:1px solid #ccc;display:block;margin:2px 0}
h3{margin:10px 0 4px;font-size:13px}
</style></head><body>
<div id="rail"><b>director workbench</b> <span class="muted">127.0.0.1, phase 1</span>
<h3>pairs</h3><div id="pairs"></div><h3>jobs</h3><div id="jobs"></div><h3>tasks</h3><div id="tasks"></div></div>
<div id="main">
<div class="tabs" id="tabs"></div>
<div id="hdr" class="muted"></div>
<div class="panel" id="p_inputs"></div>
<div class="panel" id="p_analysis"></div>
<div class="panel" id="p_plan"></div>
<div class="panel" id="p_render"></div>
<div class="panel" id="p_grade"></div>
</div>
<script>
const PANELS=[["inputs","Inputs"],["analysis","Analysis"],["plan","Plan"],["render","Render and review"],["grade","Grade"]];
const S={pairs:[],job:null,jid:null,st:null,plan:null,cid:null,set:{},extra:"",task:null,rid:null,info:null,steps:null,frame:0,ovl:{A:{},B:{}},grades:{}};
const $=id=>document.getElementById(id);
const esc=s=>String(s==null?"":s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const J=v=>JSON.stringify(v);
async function get(u){const r=await fetch(u);if(!r.ok)throw new Error((await r.json()).error||r.status);return r.json();}
async function post(u,b){const r=await fetch(u,{method:"POST",headers:{"Content-Type":"application/json"},body:J(b||{})});const j=await r.json();if(!r.ok)throw new Error(j.error||r.status);return j;}
function tab(n){for(const[k]of PANELS){$("p_"+k).classList.toggle("on",k===n);}document.querySelectorAll("#tabs button").forEach(b=>b.classList.toggle("on",b.dataset.k===n));try{localStorage.setItem("dui_tab",n)}catch(e){}}
$("tabs").innerHTML=PANELS.map(([k,l])=>`<button data-k="${k}" onclick="tab('${k}')">${l}</button>`).join("");
const api=p=>`/api/jobs/${S.jid}${p}`;

// ---------------- inputs
async function loadPairs(){const r=await get("/api/pairs");S.pairs=r.pairs;
 $("pairs").innerHTML=r.pairs.map(p=>`<div><a href="#" onclick="newJob('${p.pair}');return false">${p.pair}</a></div>`).join("");
 const fl=r.renderer_flags;
 $("p_inputs").innerHTML=`<h3>fixture pairs with a plan</h3><p class=muted>jobs go to ${esc(r.work)}/. renderer flags: --progress ${fl.progress?"yes":"no"}, --resolve-only ${fl.resolve_only?"yes":"no"}, stamp ${fl.stamp?"yes":"no"}</p>
 <table><tr><th>pair</th><th>A file</th><th>A layers</th><th>A mattes</th><th>B file</th><th>B layers</th><th>B mattes</th><th>plans (default last)</th><th></th></tr>`+
 r.pairs.map(p=>{const a=p.photos.A,b=p.photos.B;return `<tr><td>${p.pair}</td><td>${esc(a.file)}</td><td>${a.layers?"yes":"<span class=warn>no</span>"}</td><td>${a.mattes}</td><td>${esc(b.file)}</td><td>${b.layers?"yes":"<span class=warn>no</span>"}</td><td>${b.mattes}</td><td>${p.plans.join(" ")}</td><td><button onclick="newJob('${p.pair}')">new job</button></td></tr>`}).join("")+"</table>";
 const js=await get("/api/jobs");$("jobs").innerHTML=js.jobs.map(j=>`<div><a href="#" onclick="openJob('${j.id}');return false">${esc(j.id)}</a> <span class=muted>${j.renders}r</span></div>`).join("")||"<span class=muted>none</span>";}
async function newJob(pair){const r=await post("/api/jobs",{pair});await openJob(r.id);tab("analysis");loadPairs();}
async function openJob(id){S.jid=id;S.st=null;S.ov={};S.mt={};S.plan=null;S.rid=null;S.info=null;S.set={};S.grades={};S._seeded=false;S.best={};S.task=null;S.progLine=null;S.progLog=null;for(const k of["analysis","plan","render","grade"])$("p_"+k).innerHTML="<p class=muted>loading "+esc(id)+"</p>";try{localStorage.setItem("dui_job",id)}catch(e){}await refresh();}

// ---------------- job refresh loop
let busy=false;
async function refresh(){if(!S.jid||busy)return;busy=true;try{
 const st=await get(api(""));const prev=S.st;S.st=st;
 $("hdr").textContent=`job ${st.job.id} · pair ${st.job.pair} · ${st.dir}`;
 $("tasks").innerHTML=st.tasks.slice().reverse().map(t=>`<div>${t.kind} <b class="${t.state=="done"?"ok":t.state=="running"?"":"warn"}">${t.state}</b> ${t.progress?t.progress.join("/"):""} ${t.elapsed_s}s ${t.state=="running"?`<a href="#" onclick="cancelTask('${t.id}');return false">cancel</a>`:""}</div>`).join("");
 if(!prev||J(prev.analysis)!==J(st.analysis))drawAnalysis();
 if(!S.plan){S.plan=st.default_plan;await loadPlan();}
 if(!prev||J(prev.renders)!==J(st.renders)){drawRenders();if(prev)loadPairs();}
 if(!prev||J(prev.renders)!==J(st.renders)||!$("g_form"))drawGrade();
}catch(e){$("hdr").textContent="error: "+e.message}finally{busy=false}}
setInterval(refresh,1500);
async function cancelTask(t){await post(api(`/tasks/${t}/cancel`));refresh();}

// ---------------- analysis
function drawAnalysis(){const a=S.st.analysis;const rv=a.reveal,tp=a.transitions;
 let h=`<h3>relation</h3><p style="font-size:15px"><b>${esc(a.verdict)}</b></p>`;
 h+=`<table><tr><th>reader</th><th>numbers</th></tr>`;
 if(rv){const m=(rv.status||{}).metrics||{};h+=`<tr><td>Reveal align</td><td>exit ${rv.exit_code}${rv.refused?" (refused)":""}; ${rv.reason?esc(rv.reason)+"; ":""}${Object.keys(m).length?["method","inliers","rmse_px","ecc_rho","changed_pct","passed","confidence"].map(k=>`${k} ${esc(m[k])}`).join(", ")+"; ":""}wall ${rv.wall_s} s</td></tr>`;}
 else h+=`<tr><td>Reveal align</td><td class=muted>running</td></tr>`;
 if(tp)h+=`<tr><td>transitions pair</td><td>class <b>${tp.class}</b>, method ${esc(tp.method)}, median displacement ${tp.median_disp_px} px, sparse inliers ${tp.sparse_inliers}, rmse ${tp.sparse_rmse}, certainty ${tp.mean_certainty}, canvas ${J(tp.canvas)}, ${tp.total_s} s</td></tr>`;
 else h+=`<tr><td>transitions pair</td><td class=muted>running</td></tr>`;
 h+=`</table>`;
 if(a.resolve_note)h+=`<p class=muted>${esc(a.resolve_note)}</p>`;
 if(a.resolve)h+=`<p>resolved scene: <a target=_blank href="${api('/file/'+a.resolve.anchors)}">anchors.json</a></p>`;
 h+=`<h3>overlays</h3><div>`;for(const s of["A","B"]){h+=`<label><input type=checkbox id="o_${s}_elements" onchange="ovl('${s}')"> ${s} elements</label> <label><input type=checkbox id="o_${s}_disparity" onchange="ovl('${s}')"> ${s} disparity</label> &nbsp; `;}
 h+=` <label><input type=checkbox id="o_both" checked> toggle both photos together</label> opacity <input type=range id=o_op min=0 max=100 value=70 oninput="ovlOp()"></div>`;
 h+=`<div>`+["A","B"].map(s=>`<div class=stack id="st_${s}"><img src="${api('/overlay/'+s+'/base.png')}"><img class=ov id="ov_${s}_elements" style="display:none"><img class=ov id="ov_${s}_disparity" style="display:none"><img class=ov id="ov_${s}_matte" style="display:none"><div class=muted>${s} = ${S.st.job.pair}_${s=="A"?"S":"F"}</div></div>`).join("")+`</div>`;
 h+=`<p class=muted>click an element row to show its matte (soft alpha from the matte file; the hard element mask when there is no file)</p><div style="display:flex;gap:12px;align-items:flex-start">`;
 for(const s of["A","B"]){const t=a.tables[s];if(!t){h+=`<div class=warn>no layer table for ${s}</div>`;continue;}
  h+=`<div><b>${t.photo}</b> canvas ${J(t.canvas)}<div style="max-height:360px;overflow:auto"><table><tr><th>id</th><th>label</th><th>group</th><th>area</th><th>depth rank</th><th>disp</th><th>matte</th></tr>`+
  t.elements.map(e=>`<tr id="er_${s}_${e.id}" onclick="matte('${s}',${e.id})" style="cursor:pointer"><td>${e.id}</td><td>${esc(e.label)}</td><td>${esc(e.group)}</td><td>${e.area_share}</td><td>${e.depth_rank}</td><td>${e.median_disparity}</td><td>${e.matte?"file":"<span class=muted>hard</span>"}</td></tr>`).join("")+`</table></div></div>`;}
 h+=`<div><b>labels in both</b><table><tr><th>label</th><th>A share</th><th>B share</th></tr>`+a.overlap.map(o=>`<tr><td>${esc(o.label)}</td><td>${o.A}</td><td>${o.B}</td></tr>`).join("")+`</table></div></div>`;
 $("p_analysis").innerHTML=h;const ov=S.ov||{};for(const k in ov){const c=$("o_"+k);if(c)c.checked=ov[k];const im=$("ov_"+k);if(im&&ov[k]){im.src=api(`/overlay/${k.replace("_","/")}.png`);im.style.display="";}}
 for(const s in (S.mt||{})){if(S.mt[s]!=null){const im=$(`ov_${s}_matte`);im.dataset.id=S.mt[s];im.src=api(`/overlay/${s}/matte_${S.mt[s]}.png`);im.style.display="";const r=$(`er_${s}_${S.mt[s]}`);if(r)r.classList.add("sel");}}ovlOp();}
function ovl(s){const both=$("o_both").checked;const sides=both?["A","B"]:[s];S.ov=S.ov||{};
 for(const k of["elements","disparity"]){const v=$(`o_${s}_${k}`).checked;for(const x of sides){$(`o_${x}_${k}`).checked=v;S.ov[`${x}_${k}`]=v;const im=$(`ov_${x}_${k}`);if(v&&!im.src)im.src=api(`/overlay/${x}/${k}.png`);im.style.display=v?"":"none";}}ovlOp();}
function ovlOp(){const o=$("o_op").value/100;document.querySelectorAll(".stack img.ov").forEach(i=>i.style.opacity=o);}
function matte(s,id){const im=$(`ov_${s}_matte`);const on=im.dataset.id==String(id)&&im.style.display!="none";document.querySelectorAll(`[id^=er_${s}_]`).forEach(r=>r.classList.remove("sel"));
 S.mt=S.mt||{};S.mt[s]=on?null:id;if(on){im.style.display="none";return;}im.dataset.id=id;im.src=api(`/overlay/${s}/matte_${id}.png`);im.style.display="";$(`er_${s}_${id}`).classList.add("sel");ovlOp();}

// ---------------- plan
async function loadPlan(){S.pv=await get(`/api/plans/${S.plan}`);if(!S.cid||!S.pv.concepts.find(c=>c.id==S.cid))S.cid=S.pv.concepts[0].id;S.set={};seedLastRound();drawPlan();}
function C(){return S.pv.concepts.find(c=>c.id==S.cid);}
function seedLastRound(){const lr=C().last_round;if(!lr)return;for(const[k,v]of Object.entries(lr.knobs||{}))S.set[k]=v;}
const clone=v=>v===undefined?undefined:JSON.parse(J(v));
function getPath(v,p){for(const k of p){if(v==null)return undefined;v=v[k];}return v;}
function setPath(v,p,x){if(!p.length)return x;v=clone(v)??(typeof p[0]=="number"?[]:{});let o=v;for(let i=0;i<p.length-1;i++){if(o[p[i]]==null)o[p[i]]=typeof p[i+1]=="number"?[]:{};o=o[p[i]];}o[p[p.length-1]]=x;return v;}
function eff(key,base){return key in S.set?S.set[key]:base;}
function setKey(key,base,v){if(J(v)===J(base))delete S.set[key];else S.set[key]=v;}
function knobInput(id,range,val,on){if(Array.isArray(range)&&range.length==2&&typeof range[0]=="number"&&typeof range[1]=="number"){const st=Number.isInteger(range[0])&&Number.isInteger(range[1])&&Math.abs(range[1]-range[0])>2?1:0.01;return `<input type=number id="${id}" min=${range[0]} max=${range[1]} step=${st} value="${esc(val)}" onchange="${on}">`;}
 if(Array.isArray(range)&&range.every(x=>typeof x=="boolean"))return `<input type=checkbox id="${id}" ${val?"checked":""} onchange="${on}">`;
 if(Array.isArray(range)){const opts=range.slice();if(!opts.some(o=>J(o)===J(val)))opts.push(val);return `<select id="${id}" onchange="${on}">`+opts.map(o=>`<option value='${esc(J(o))}' ${J(o)===J(val)?"selected":""}>${esc(J(o))}</option>`).join("")+`</select>`;}
 return `<input id="${id}" value='${esc(J(val))}' onchange="${on}">`;}
function readInput(id){const el=$(id);if(el.type=="checkbox")return el.checked;if(el.type=="number")return parseFloat(el.value);try{return JSON.parse(el.value)}catch(e){return el.value}}
function drawPlan(){const pv=S.pv,c=C();
 let h=`<p>plan <select onchange="S.plan=this.value;loadPlan()">${S.st.plans.map(p=>`<option ${p==S.plan?"selected":""}>${p}</option>`).join("")}</select>
 concept <select onchange="S.cid=this.value;S.set={};seedLastRound();drawPlan()">${pv.concepts.map(x=>`<option ${x.id==S.cid?"selected":""}>${x.id}</option>`).join("")}</select>
 <span class=muted>${esc(pv.path)} sha256 ${pv.sha256.slice(0,16)}… relation ${esc(pv.relation)}; planner ${esc((pv.planner||{}).model)}</span></p>
 <p><b>idea</b> ${esc(c.idea)}</p><p class=muted><b>risk</b> ${esc(c.risk)}</p>`;
 h+=`<h3>timeline (drag a bar to move its window, drag an end to resize; becomes a &lt;name&gt;.window knob)</h3><div id=tl></div><div class=muted id=tl_note></div>`;
 h+=`<h3>the concept's knobs</h3><table><tr><th>knob</th><th>range</th><th>default</th><th>value</th><th>--set key</th><th>what</th></tr>`;
 c.knobs.forEach((k,i)=>{if(k.readonly){h+=`<tr class=ro><td>${esc(k.name)}</td><td>${esc(J(k.range))}</td><td>${esc(J(k.default))}</td><td>read-only</td><td>${esc(k.readonly)}</td><td>${esc(k.what)}</td></tr>`;return;}
  const cur=getPath(eff(k.cli_key,k.base),k.path);const v=cur===undefined?k.default:cur;
  h+=`<tr class="${k.cli_key in S.set?"sel":""}"><td>${esc(k.name)}</td><td>${esc(J(k.range))}</td><td>${esc(J(k.default))}</td><td>${knobInput("k_"+i,k.range,v,`knob(${i})`)}</td><td>${esc(k.cli_key)}${k.path.length?esc(J(k.path)):""}</td><td>${esc(k.what)}</td></tr>`;});
 h+=`</table>`;
 const lr=c.last_round;
 h+=`<h3>renderer globals (checked = sent as --set)</h3><p class=muted>${lr?`seeded from the last round's render ${esc(lr.from)}: ${esc(J(lr.knobs))} (wall ${lr.wall_s} s at canvas ${esc(J(lr.canvas))})`:"no earlier round render of this plan and concept"} <button onclick="S.set={};drawPlan()">clear all knobs</button> <button onclick="S.set={};seedLastRound();drawPlan()">reset to last round</button></p>
 <table><tr><th>set</th><th>key</th><th>renderer default for this concept</th><th>value</th><th>what</th></tr>`;
 c.globals.forEach((g,i)=>{const on=g.key in S.set;const v=on?S.set[g.key]:g.default;let inp;
  if(g.kind=="bool")inp=`<input type=checkbox id="g_${i}" ${v?"checked":""} onchange="glob(${i})">`;
  else if(g.kind.startsWith("enum:"))inp=`<select id="g_${i}" onchange="glob(${i})">`+g.kind.slice(5).split("|").map(o=>`<option ${o==v?"selected":""}>${o}</option>`).join("")+`</select>`;
  else inp=`<input type=number step=0.01 id="g_${i}" value="${v==null?"":v}" onchange="glob(${i})">`;
  h+=`<tr class="${on?"sel":""}"><td><input type=checkbox id="gs_${i}" ${on?"checked":""} onchange="glob(${i})"></td><td>${g.key}</td><td>${esc(J(g.default))}</td><td>${inp}</td><td>${esc(g.what)}</td></tr>`;});
 h+=`</table><h3>extra --set lines (key=JSON value, one per line; for keys the tables do not show)</h3><textarea id=extra rows=2 onchange="S.extra=this.value;drawSetPreview()">${esc(S.extra)}</textarea>
 <h3>what the next render sends</h3><pre id=setprev></pre>`;
 $("p_plan").innerHTML=h;drawTimeline();drawSetPreview();}
function knob(i){const k=C().knobs[i];const v=readInput("k_"+i);setKey(k.cli_key,k.base,setPath(eff(k.cli_key,k.base),k.path,v));drawPlan();}
function glob(i){const g=C().globals[i];if(!$("gs_"+i).checked){delete S.set[g.key];}else{let v=readInput("g_"+i);if(g.kind=="num"&&(v===""||isNaN(v)))v=g.default;S.set[g.key]=v;}drawPlan();}
function allKnobs(){const k=clone(S.set);for(const line of(S.extra||"").split("\n")){const m=line.trim().match(/^([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)=(.*)$/);if(!m)continue;try{k[m[1]]=JSON.parse(m[2])}catch(e){k[m[1]]=m[2]}}return k;}
function drawSetPreview(){const k=allKnobs();$("setprev").textContent=Object.keys(k).length?Object.entries(k).map(([a,b])=>`--set ${a}=${J(b)}`).join("\n"):"(no knobs: the plan as written)";}
// timeline
function beats(){const c=C();const rows=c.beats.map(b=>({name:b.name,key:b.name+".window",base:b.window,by:b.by}));if(c.end_effect&&c.end_effect.window)rows.push({name:"end_effect ("+c.end_effect.kind+")",key:"end_window",base:c.end_effect.window,end:true});return rows;}
function drawTimeline(){const tl=$("tl");const rows=beats();const W=900,RH=24;tl.style.height=(rows.length*RH+22)+"px";let h="";
 for(let t=0;t<=10;t++)h+=`<div style="position:absolute;left:${t*W/10}px;top:${rows.length*RH+2}px;font-size:10px;color:#777">${(t/10).toFixed(1)}</div><div style="position:absolute;left:${t*W/10}px;top:0;bottom:16px;border-left:1px dotted #ddd"></div>`;
 rows.forEach((r,i)=>{const w=eff(r.key,r.base);const skip=!r.end&&S.set[r.name+".skip"]===true;const ch=r.key in S.set;
  h+=`<div class="bar ${r.end?"end":""} ${skip?"mute":""} ${ch?"changed":""}" data-i=${i} style="left:${w[0]*W}px;width:${Math.max(4,(w[1]-w[0])*W)}px;top:${i*RH+2}px" title="${esc(r.name)} ${J(w)}">${esc(r.name)} ${w[0].toFixed(2)}–${w[1].toFixed(2)}</div>`;
  if(!r.end)h+=`<div style="position:absolute;left:${W+6}px;top:${i*RH+2}px;white-space:nowrap"><label><input type=checkbox ${skip?"checked":""} onchange="mute('${r.name}',this.checked)">mute</label> <label><input type=checkbox ${isSolo(r.name)?"checked":""} onchange="solo('${r.name}',this.checked)">solo</label></div>`;});
 tl.innerHTML=h;tl.querySelectorAll(".bar").forEach(b=>b.addEventListener("pointerdown",dragStart));
 const mo=C().motion;$("tl_note").textContent=mo&&mo.kind=="continuous"?"motion model continuous: the renderer may move beats to overlap (info.json motion.adjusted shows where)":"";}
let drag=null;
function dragStart(e){const b=e.currentTarget;const r=beats()[+b.dataset.i];const w=eff(r.key,r.base);const rect=b.getBoundingClientRect();const x=e.clientX-rect.left;
 drag={r,w0:w.slice(),x0:e.clientX,mode:x<6?"l":(x>rect.width-6?"r":"m"),el:b};b.setPointerCapture(e.pointerId);b.addEventListener("pointermove",dragMove);b.addEventListener("pointerup",dragEnd);e.preventDefault();}
function dragMove(e){if(!drag)return;const dx=(e.clientX-drag.x0)/900;let[a,b]=drag.w0;const len=b-a;
 if(drag.mode=="m"){a=Math.min(Math.max(0,a+dx),1-len);b=a+len;}else if(drag.mode=="l"){a=Math.min(Math.max(0,a+dx),b-0.02);}else{b=Math.max(Math.min(1,b+dx),a+0.02);}
 a=Math.round(a*100)/100;b=Math.round(b*100)/100;drag.cur=[a,b];drag.el.style.left=(a*900)+"px";drag.el.style.width=((b-a)*900)+"px";drag.el.textContent=`${drag.r.name} ${a.toFixed(2)}–${b.toFixed(2)}`;}
function dragEnd(e){if(!drag)return;const d=drag;drag=null;if(d.cur)setKey(d.r.key,d.r.base,d.cur);drawPlan();}
function mute(n,on){if(on)S.set[n+".skip"]=true;else delete S.set[n+".skip"];drawPlan();}
function isSolo(n){const o=C().beats.filter(b=>b.name!=n);return o.length>0&&o.every(b=>S.set[b.name+".skip"]===true)&&!S.set[n+".skip"];}
function solo(n,on){for(const b of C().beats){if(on&&b.name!=n)S.set[b.name+".skip"]=true;else delete S.set[b.name+".skip"];}drawPlan();}

// ---------------- render and review
async function render(maxLong){const sec=parseFloat($("r_sec").value),fps=parseInt($("r_fps").value);
 const r=await post(api("/render"),{plan:S.pv.path,concept:S.cid,knobs:allKnobs(),max_long:maxLong,seconds:sec,fps});S.task=r.task;S.rid=r.rid;S.info=null;S.steps=null;pollTask();refresh();}
async function rerender(){if(!S.rid)return;const r=await post(api("/render"),{from_render:S.rid});S.task=r.task;S.rid=r.rid;S.info=null;S.steps=null;pollTask();refresh();}
async function pollTask(){if(!S.task)return;let t;try{t=await get(api(`/tasks/${S.task}`));}catch(e){return;}
 const p=t.progress;let line=`${t.kind} ${t.state}`;
 if(p)line+=` · frame ${p[0]+1}/${p[1]} (${Math.round(100*(p[0]+1)/Math.max(1,p[1]))} %)`;
 line+=` · ${t.elapsed_s} s`;if(!p&&t.expected_s)line+=` of about ${t.expected_s} s (last wall time of this plan at this size; ${Math.min(99,Math.round(100*t.elapsed_s/t.expected_s))} %)`;
 if(!p&&t.state=="running")line+=t.meta&&t.meta.progress_flag?" (building the scene; no frame yet)":(!t.expected_s?" (this renderer prints no PROGRESS lines and there is no earlier wall time at this size)":"");
 if(t.state!="running")line+=` · exit ${t.exit_code}`;
 S.progLine=line;S.progLog=t.log_tail.join("\n");if($("r_prog"))$("r_prog").textContent=line;if($("r_log"))$("r_log").textContent=S.progLog;
 if(t.state=="running")setTimeout(pollTask,500);else{await refresh();if(t.state=="done")selectRender(S.rid);}}
function drawRenders(){const rs=S.st.renders;let h=`<p>seconds <input type=number id=r_sec value=3 step=0.5> fps <input type=number id=r_fps value=30>
 <button onclick="render(480)"><b>draft</b> 480</button> <button onclick="render(1920)">full 1920</button> <button onclick="rerender()">re-render the selected render from its render.json</button></p>
 <div id=r_prog class=muted>${esc(S.progLine||"no task")}</div><pre id=r_log>${esc(S.progLog||"")}</pre>
 <h3>renders</h3><table><tr><th>rid</th><th>plan</th><th>concept</th><th>size</th><th>knobs</th><th>state</th><th>wall s</th><th>md5 mp4</th><th>from</th></tr>`+
 rs.slice().reverse().map(r=>`<tr class="${r.rid==S.rid?"sel":""}" style="cursor:pointer" onclick="selectRender('${r.rid}')"><td>${r.rid}</td><td>${esc((r.plan_path||"").split("/").pop())}</td><td>${r.concept}</td><td>${r.max_long}${r.draft?" draft":""}</td><td>${esc(J(r.knobs))}</td><td>${r.state}</td><td>${r.wall_s??""}</td><td>${r.md5_mp4?r.md5_mp4.slice(0,12):""}</td><td>${r.from_render||""}</td></tr>`).join("")+`</table><div id=review></div>`;
 const keep=[$("r_sec")&&$("r_sec").value,$("r_fps")&&$("r_fps").value];$("p_render").innerHTML=h;if(keep[0]){$("r_sec").value=keep[0];$("r_fps").value=keep[1];}
 if(S.rid&&S.info)drawReview();}
async function selectRender(rid){S.rid=rid;const r=S.st.renders.find(x=>x.rid==rid);document.querySelectorAll("#p_render tr").forEach(t=>t.classList.remove("sel"));
 if(!r||r.state!="done"){ $("review").innerHTML=`<p class=muted>${rid}: ${r?r.state:"unknown"}</p>`;return;}
 const info=await get(api(`/file/renders/${rid}/info.json`));const f=await post(api("/frame"),{rid,index:0});if(S.rid!==rid)return;S.info=info;S.steps=f.steps;S.nframes=f.n;S.frame=0;drawReview();tab("render");}
function seriesSvg(vals,xs,n,marks,label,fmt){const W=640,H=70;const mx=Math.max(1e-9,...vals);let pts=vals.map((v,j)=>`${(xs[j]/Math.max(1,n-1)*W).toFixed(1)},${(H-4-(v/mx)*(H-10)).toFixed(1)}`).join(" ");
 let m=marks.map(([x,c])=>`<line x1=${x/Math.max(1,n-1)*W} x2=${x/Math.max(1,n-1)*W} y1=0 y2=${H} stroke="${c}" stroke-width=2 opacity=.6 />`).join("");
 return `<div class=muted>${label} (peak ${fmt(mx)})</div><svg width=${W} height=${H} onclick="seekSvg(event,${n})"><polyline fill=none stroke="#36c" stroke-width=1.5 points="${pts}"/>${m}<line class=cur x1=0 x2=0 y1=0 y2=${H} stroke="#000" /></svg>`;}
function seekSvg(e,n){const r=e.currentTarget.getBoundingClientRect();scrub(Math.round((e.clientX-r.left)/r.width*(n-1)));}
function drawReview(){const I=S.info,n=S.nframes,rid=S.rid;const mp=I.motion_px||[];const med=I.motion_median_px||0;
 const pauses=[],jumps=[];mp.forEach((m,j)=>{if(j>=0.1*mp.length&&j<=0.9*mp.length&&m<0.2*med)pauses.push(j+1);});for(let j=0;j+1<mp.length;j++)if(Math.abs(mp[j+1]-mp[j])>Math.max(1,0.5*med))jumps.push(j+2);
 const marks=[...pauses.map(x=>[x,"#e90"]),...jumps.map(x=>[x,"#d00"])];
 const r=S.st.renders.find(x=>x.rid==rid)||{};
 let h=`<h3>${rid} · ${esc(r.concept)} · ${r.max_long}${r.draft?" (draft)":""} · ${I.frames} frames, ${I.seconds} s at ${I.fps} fps, wall ${I.wall_s} s · md5 ${esc(r.md5_mp4)}</h3>
 <p class=muted>knobs ${esc(J(I.knobs))}; render.json <a target=_blank href="${api(`/file/renders/${rid}/render.json`)}">open</a>, log <a target=_blank href="${api(`/file/renders/${rid}/log.txt`)}">open</a>, montage <a target=_blank href="${api(`/file/renders/${rid}/montage.jpg`)}">open</a></p>
 <video id=vid src="${api(`/file/renders/${rid}/transition.mp4`)}" controls loop muted preload=auto></video>
 <p><button onclick="scrub(S.frame-1)">&lt; frame</button> <input type=range id=scr min=0 max=${n-1} value=${S.frame} style="width:520px" oninput="scrub(+this.value)"> <button onclick="scrub(S.frame+1)">frame &gt;</button> <span id=fl></span> <button onclick="markFrame()">mark this frame</button> <span id=marked class=muted></span></p>
 ${seriesSvg(mp,mp.map((_,j)=>j+1),n,marks,`motion_px (mean flow between consecutive frames; median ${med} px; ${I.motion_pauses} pause frames orange, ${I.motion_jumps} jumps red)`,v=>v.toFixed(1)+" px")}
 ${seriesSvg(S.steps,S.steps.map((_,j)=>j+1),n,marks,`step profile (mean |frame - previous| in levels; first/second/last ${I.step_first}/${I.step_second}/${I.step_last}, max ${I.step_max}; pauses and jumps from motion_px)`,v=>v.toFixed(1))}
 ${seriesSvg((I.b_inside||[]).map(p=>p[1]),(I.b_inside||[]).map(p=>p[0]),n,I.b_inside_first!=null?[[I.b_inside_first,"#d00"]]:[],`b_inside (share of B inside A's region; first above 1 % at frame ${I.b_inside_first}; guard max ${I.guard_share_max})`,v=>(v*100).toFixed(2)+" %")}
 <div class=cmp><div class=muted>A (frame 0) | frame <span id=fi></span> | B (frame ${n-1})</div><img src="${api(`/frame?rid=${rid}&i=0`)}"><img id=fimg><img src="${api(`/frame?rid=${rid}&i=${n-1}`)}"></div>`;
 $("review").innerHTML=h;scrub(S.frame);}
function scrub(i){const n=S.nframes;i=Math.max(0,Math.min(n-1,i|0));S.frame=i;const I=S.info;const v=$("vid");if(v){v.pause();v.currentTime=(i+0.5)/I.fps;}
 $("scr").value=i;const mp=I.motion_px||[];const bi=(I.b_inside||[]).filter(p=>p[0]<=i).pop();
 $("fl").textContent=`frame ${i}/${n-1}  t=${(i/(n-1)).toFixed(3)}  motion ${i>0&&mp[i-1]!=null?mp[i-1].toFixed(2):"-"} px  step ${i>0&&S.steps[i-1]!=null?S.steps[i-1].toFixed(2):"-"}  b_inside ${bi?(bi[1]*100).toFixed(2)+" % @"+bi[0]:"-"}`;
 $("fi").textContent=i;$("fimg").src=api(`/frame?rid=${S.rid}&i=${i}`);
 document.querySelectorAll("#review svg line.cur").forEach(l=>{const x=i/Math.max(1,n-1)*640;l.setAttribute("x1",x);l.setAttribute("x2",x);});}
async function markFrame(){const r=await post(api("/frame"),{rid:S.rid,index:S.frame,mark:true});const g=gradeFor(S.rid);g.frames=g.frames||[];if(!g.frames.includes(r.marked))g.frames.push(r.marked);$("marked").textContent="saved "+r.marked;drawGrade();}
document.addEventListener("keydown",e=>{if(!$("p_render").classList.contains("on")||!S.info||/INPUT|TEXTAREA|SELECT/.test(e.target.tagName))return;if(e.key=="ArrowLeft"){scrub(S.frame-1);e.preventDefault();}if(e.key=="ArrowRight"){scrub(S.frame+1);e.preventDefault();}});

// ---------------- grade
function stemOf(r){return (r.plan_path||"").split("/").pop().replace(/\.json$/,"");}
function tagOf(r){return `${stemOf(r)}_${r.concept}-${r.rid}`;}
function gradeFor(rid){if(!S.grades[rid])S.grades[rid]={acceptable:false,note:"",props:{one_picture:false,transforms:false,not_invented:false}};return S.grades[rid];}
function drawGrade(){if(!S.st)return;const rs=S.st.renders.filter(r=>r.state=="done");const lp=S.st.last_picks;
 if(lp&&!S._seeded){S._seeded=true;for(const r of rs){const c=lp.clips[tagOf(r)];if(c)S.grades[r.rid]=clone(c);}S.best=clone(lp.best);}
 S.best=S.best||{};
 let h=`<p class=muted>one row per finished render; tag = &lt;plan&gt;_&lt;concept&gt;-&lt;rid&gt; (the variant-folder convention of director_page.py); a 480 render is saved with draft: true. ${S.st.last_picks_path?"last saved: "+esc(S.st.last_picks_path):""}</p><div id=g_form>`;
 for(const r of rs){const g=gradeFor(r.rid);const t=tagOf(r);
  h+=`<div style="border-top:1px solid #ccc;padding:4px 0"><b>${esc(t)}</b> ${r.draft?"<span class=warn>draft 480</span>":"full"} <a href="#" onclick="selectRender('${r.rid}');return false">review</a> <span class=muted>knobs ${esc(J(r.knobs))}</span><br>
  ${["one_picture","transforms","not_invented"].map(k=>`<label><input type=checkbox ${g.props[k]?"checked":""} onchange="gradeFor('${r.rid}').props['${k}']=this.checked"> ${k.replace("_"," ")}</label>`).join(" ")}
  <label><input type=checkbox ${g.acceptable?"checked":""} onchange="gradeFor('${r.rid}').acceptable=this.checked"> acceptable as-is</label>
  ${g.frames&&g.frames.length?`<span class=muted>frames ${esc(g.frames.join(", "))}</span>`:""}<br>
  <textarea rows=3 placeholder="what is wrong, what should happen instead, which knob" oninput="gradeFor('${r.rid}').note=this.value">${esc(g.note)}</textarea></div>`;}
 const stems=[...new Set(rs.map(stemOf))];
 for(const s of stems){const opts=rs.filter(r=>stemOf(r)==s).map(r=>`${r.concept}-${r.rid}`);h+=`<p>best for ${esc(s)}: <select onchange="S.best['${s}']=this.value"><option value=none>none</option>${opts.map(o=>`<option ${S.best[s]==o?"selected":""}>${o}</option>`).join("")}</select></p>`;}
 h+=`</div><p><button onclick="savePicks()">save picks to the job folder</button> <span id=g_out></span></p><pre id=g_json></pre>`;
 $("p_grade").innerHTML=rs.length?h:"<p class=muted>no finished render to grade</p>";}
async function savePicks(){const rs=S.st.renders.filter(r=>r.state=="done");const clips={};
 for(const r of rs){const g=gradeFor(r.rid);const c={acceptable:!!g.acceptable,note:g.note||"",props:{one_picture:!!g.props.one_picture,transforms:!!g.props.transforms,not_invented:!!g.props.not_invented},render:r.rid,draft:!!r.draft};if(g.frames&&g.frames.length)c.frames=g.frames;clips[tagOf(r)]=c;}
 const best={};for(const s of new Set(rs.map(stemOf)))best[s]=(S.best||{})[s]||"none";
 const obj={date:new Date().toISOString(),page:"workbench_"+S.jid,best,clips};
 const r=await post(api("/picks"),obj);$("g_out").textContent="saved "+r.path;$("g_json").textContent=JSON.stringify(obj,null,1);}

loadPairs().then(()=>{let j=null,t="inputs";try{j=localStorage.getItem("dui_job");t=localStorage.getItem("dui_tab")||t}catch(e){}tab(t);if(j)openJob(j).catch(()=>{});});
</script></body></html>
"""


def main():
    global WORK
    ap = argparse.ArgumentParser(description="the director's workbench (phase 1), 127.0.0.1 only")
    ap.add_argument("--port", type=int, default=8379)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--runs-date", default=dt.date.today().isoformat())
    a = ap.parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.runs_date):
        raise SystemExit("--runs-date must be YYYY-MM-DD")
    WORK = RUNS / a.runs_date / "workbench"
    WORK.mkdir(parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    httpd.daemon_threads = True
    url = f"http://127.0.0.1:{a.port}/"
    print(f"director workbench {UI_VERSION} at {url}  jobs in {WORK.relative_to(ROOT)}  pid {os.getpid()}  (Ctrl+C to stop)", flush=True)
    if not a.no_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
