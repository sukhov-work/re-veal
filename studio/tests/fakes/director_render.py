"""A fake scripts/research/director_render.py for the studio's unit tests: the real flags and --help text, the real
output files in the real shapes, no depth model and no morph.

Under --resolve-only: canvas_A.png, canvas_B.png, anchors.json (the nine keys of director_render.py:1801-1805), then
info.json without the measures. A render: transition.mp4 (cv2's mp4v, a grey ramp from A to B), montage.jpg, then
info.json with the keys of b_director_research.md §3, written last; `PROGRESS i n` on stderr every 5 frames and at the
last under --progress. The step values are read back from the decoded mp4, as the renderer reads them.

The environment steers it as the fake loop_seq.py's does: FAKE_SLOW="render=3" spends 3 s across the frame loop
(resolve likewise), FAKE_FAIL="render" (or "resolve") exits 1 after a traceback's last line. The layer and matte roots
default to the ones under the script's repo root.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ROOTS = {"layers": ROOT / "benchmarks/runs/2026-09-28/layers_v3", "mattes": ROOT / "benchmarks/runs/2026-10-17/mattes"}


def parse_knob(s: str) -> tuple[str, Any]:
    k, v = s.split("=", 1)
    try:
        return k, json.loads(v)
    except ValueError:
        return k, v


def env_names(name: str) -> list[str]:
    return [x.split("=")[0] for x in os.environ.get(name, "").split(",") if x]


def slow_of(cmd: str) -> float:
    for x in os.environ.get("FAKE_SLOW", "").split(","):
        if x.startswith(cmd + "="):
            return float(x.split("=", 1)[1])
    return 0.0


def table(photo: str) -> Any:
    p = ROOTS["layers"] / photo / "layers.json"
    return json.loads(p.read_text()) if p.is_file() else None


def matte_fallbacks(pair: str) -> list[str]:
    """photo:id of every element of either table without an el_<id>.png."""
    out = []
    for side in ("S", "F"):
        photo = f"{pair}_{side}"
        for e in (table(photo) or {}).get("elements", []):
            if not (ROOTS["mattes"] / photo / f"el_{e['id']}.png").is_file():
                out.append(f"{photo}:{e['id']}")
    return out


def args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("out")
    ap.add_argument("--concept", default=None)
    ap.add_argument("--seconds", type=float, default=3.0)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--max-long", type=int, default=1920)
    ap.add_argument(
        "--set", action="append", default=[], help="knob=value (JSON value); 'name.param' targets a transform's params"
    )
    ap.add_argument(
        "--progress", action="store_true", help="print 'PROGRESS i n' to stderr every 5 frames and at the last"
    )
    ap.add_argument(
        "--resolve-only",
        action="store_true",
        help="build the scene, write canvas_A.png, canvas_B.png and anchors.json into OUT, and stop before the "
        "frame loop",
    )
    ap.add_argument(
        "--layers-dir", default=None, help="the layer tables' root (default benchmarks/runs/2026-09-28/layers_v3)"
    )
    ap.add_argument("--mattes-dir", default=None, help="the mattes' root (default benchmarks/runs/2026-10-17/mattes)")
    return ap.parse_args()


def scene(plan: Any, concept: Any, knobs: dict[str, Any], w: int, h: int) -> tuple[list[Any], dict[str, Any]]:
    """The placed layers (a skipped one left out) and the scene's info, as the resolve and the render share them."""
    kind = (concept.get("container") or {}).get("kind", "quad")
    layers, unplaced = [], []
    for tr in concept.get("transforms", []):
        if knobs.get(tr["name"] + ".skip"):
            unplaced.append({"name": tr["name"], "why": "skipped by the operator's knob"})
            continue
        lay = {
            "name": tr["name"],
            "by": tr["by"],
            "window": list(knobs.get(tr["name"] + ".window", tr.get("window", [0, 1]))),
            "depth": tr.get("depth", "inside"),
        }
        if tr["by"] == "keyframe_chain":
            p = tr.get("params") or {}
            lay["chain"] = {
                "keyframes": p.get("keyframes", []),
                "frame": p.get("frame", "canvas"),
                "times": p.get("times", []),
            }
        layers.append(lay)
    motion = dict(concept.get("motion") or {"kind": "legacy"})
    motion["adjusted"] = []
    motion["beats"] = [{"name": x["name"], "window": x["window"], "ease": "trapezoid", "edge": 0.35} for x in layers]
    info: dict[str, Any] = {
        "canvas": [w, h],
        "pair": plan["pair"],
        "concept": concept["id"],
        "camera": "sim" if kind == "disc" else "homog",
        "start_zoom": 1.5,
        "motion": motion,
        "guard": [],
        "unplaced": unplaced,
        "matte_fallbacks": matte_fallbacks(plan["pair"]),
        "layers": layers,
    }
    if kind in ("quad", "rect"):
        info["quad"] = [[w * 0.3, h * 0.1], [w * 1.0, 0.0], [w * 1.0, h * 0.65], [w * 0.3, h * 0.55]]
    return layers, info


def decoded_steps(mp4: Path) -> list[float]:
    cap = cv2.VideoCapture(str(mp4))
    prev, steps = None, []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        if prev is not None:
            steps.append(float(np.abs(fr.astype(np.float32) - prev).mean()))
        prev = fr.astype(np.float32)
    cap.release()
    return steps


def main() -> None:
    a = args()
    if a.layers_dir:
        ROOTS["layers"] = Path(a.layers_dir).resolve()
    if a.mattes_dir:
        ROOTS["mattes"] = Path(a.mattes_dir).resolve()
    cmd = "resolve" if a.resolve_only else "render"
    plan = json.loads(Path(a.plan).read_text())
    concepts = plan["concepts"]
    concept = next((c for c in concepts if c["id"] == a.concept), concepts[0]) if a.concept else concepts[0]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    knobs = dict(parse_knob(s) for s in a.set)
    if cmd in env_names("FAKE_FAIL"):
        print("Traceback (most recent call last):", file=sys.stderr)
        print(f"RuntimeError: the fake {cmd} failed on purpose", file=sys.stderr)
        sys.exit(1)
    ls = list((table(f"{plan['pair']}_S") or {}).get("canvas") or [64, 48])
    s = min(1.0, a.max_long / max(ls))
    w, h = max(8, round(ls[0] * s)) // 2 * 2, max(8, round(ls[1] * s)) // 2 * 2
    n = round(a.seconds * a.fps)
    t_start, slow = time.time(), slow_of(cmd)
    layers, info = scene(plan, concept, knobs, w, h)
    info["ls_canvas"] = ls
    tp = ROOT / "transitions.py"
    stamp = {
        "plan_sha256": hashlib.sha256(Path(a.plan).read_bytes()).hexdigest()[:16],
        "renderer_md5": hashlib.md5(Path(__file__).read_bytes(), usedforsecurity=False).hexdigest(),
        "transitions_md5": hashlib.md5(tp.read_bytes(), usedforsecurity=False).hexdigest() if tp.is_file() else None,
        "layers_dir": str(ROOTS["layers"]),
        "mattes_dir": str(ROOTS["mattes"]),
    }
    im_a, im_b = np.full((h, w, 3), 70, np.uint8), np.full((h, w, 3), 150, np.uint8)
    if a.resolve_only:
        time.sleep(slow)
        cv2.imwrite(str(out / "canvas_A.png"), im_a)
        cv2.imwrite(str(out / "canvas_B.png"), im_b)
        disc = info["camera"] == "sim"
        anchors = (
            {"a0": {"centre": [w / 2, h / 2], "radius": h / 4}, "b0": {"centre": [w / 2, h / 3], "radius": h / 8}}
            if disc
            else {}
        )
        cam = {"kind": info["camera"], "S_A3": [[0.27, 0.0, w * 0.3], [-0.12, 0.43, h * 0.1], [-0.0002, 0.0, 1.0]]}
        doc = {
            "pair": plan["pair"],
            "concept": concept["id"],
            "canvas": [w, h],
            "frames": n,
            "anchors": anchors,
            "layers": [{k: x[k] for k in ("name", "by", "window", "depth")} for x in layers],
            "info": info,
            "camera": cam,
            "renderer_md5": stamp["renderer_md5"],
        }
        (out / "anchors.json").write_text(json.dumps(doc, indent=1))
        info["resolve_only"] = True
        (out / "info.json").write_text(json.dumps({**info, **stamp}, indent=1))
        print(json.dumps({"resolve_only": True, "canvas": [w, h]}))
        return
    vw = cv2.VideoWriter(str(out / "transition.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), a.fps, (w, h))
    keep = []
    for i in range(n):
        if a.progress and (i % 5 == 0 or i == n - 1):
            print(f"PROGRESS {i} {n}", file=sys.stderr, flush=True)
        u = i / (n - 1)
        f = np.clip(im_a.astype(np.float32) * (1 - u) + im_b.astype(np.float32) * u, 0, 255).astype(np.uint8)
        vw.write(f)
        if i in {0, n // 2, n - 1}:
            keep.append(f)
        if slow:
            time.sleep(slow / n)
    vw.release()
    steps = decoded_steps(out / "transition.mp4")
    motion_px = [round(1.0 + 0.5 * math.sin(j / 5.0), 2) for j in range(len(steps))]
    mid = [m for j, m in enumerate(motion_px) if 0.1 * len(motion_px) <= j <= 0.9 * len(motion_px)]
    med = float(np.median(mid)) if mid else 0.0
    b_inside = [[f, round(min(1.0, max(0.0, (f / (n - 1) - 0.3) * 1.5)), 4)] for f in [*range(0, n - 1, 3), n - 1]]
    residual = [[f, round(0.001 * (1 + math.cos(f / 4.0)), 5)] for f in range(3, n - 1, 3)]
    halo = [[f, 10.0, 0.5, 30.0] for f in range(3, n - 1, 3)] if info["camera"] == "sim" else None
    cv2.imwrite(str(out / "montage.jpg"), np.concatenate(keep, 1), [cv2.IMWRITE_JPEG_QUALITY, 85])
    info.update(
        frames=len(steps) + 1,
        step_first=round(steps[0], 2),
        step_second=round(steps[1], 2),
        step_last=round(steps[-1], 2),
        step_max=round(max(steps), 2),
        seconds=a.seconds,
        fps=a.fps,
        knobs=knobs,
        wall_s=round(time.time() - t_start, 1),
        motion_px=motion_px,
        motion_median_px=round(med, 2),
        motion_pauses=sum(1 for m in mid if m < 0.2 * med),
        motion_jumps=sum(1 for p, q in itertools.pairwise(motion_px) if abs(q - p) > max(1.0, 0.5 * med)),
        guard_share_max=0.0,
        b_inside=b_inside,
        b_inside_first=next((f for f, v in b_inside if v > 0.01), None),
        residual_edges=residual,
        residual_edge_max=round(max(v for _, v in residual), 5) if residual else 0.0,
        halo=halo,
        halo_step_max=10.0 if halo else None,
        halo_ring_max=0.5 if halo else None,
    )
    (out / "info.json").write_text(json.dumps({**info, **stamp}, indent=1))
    print(json.dumps({k: info[k] for k in ("frames", "step_first", "motion_median_px")}))


if __name__ == "__main__":
    main()
