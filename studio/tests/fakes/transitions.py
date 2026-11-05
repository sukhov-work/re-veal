#!/usr/bin/env python3
"""A stand-in for transitions.py in the unit tests: `pair BEFORE AFTER --out DIR` with the real CLI's flags, help
sentences, choices and defaults (transitions.py main(), 2026-11-05; tests/test_pair_flow.py compares the two flag
sets), and the files of a real run in its order: DIR/transition.mp4 (cv2's mp4v), DIR/strip.jpg, then
DIR/report.json last.

The frames: frame 0 is A covered onto the canvas, the last frame B, the frames between a linear blend. The canvas
takes B's aspect (or the smaller sides of the two under --canvas common), its long edge capped by --max-long and its
sides made even. The report holds the real keys: class, method, sparse_inliers, sparse_rmse, median_disp_px,
mean_certainty, pan_fraction, camera and zoom (class B), canvas, canvas_policy, n_frames, the three clock keys (which
vary run to run, as the real ones do), spec, quality (warping_error, flicker with edge_ratio, goal, endpoint,
n_frames, proxy_long), tool_version and outputs. Class B unless --class A, which reports homography+dis with 120
inliers. Fewer than three anchor pairs is a FAILED: line and exit 2, as the real CLI's.

The environment steers it: FAKE_SLOW="pair=3" sleeps that many seconds before writing, FAKE_REFUSE="pair" prints a
FAILED: line on stderr and exits 2 with nothing written, FAKE_FAIL="pair" exits 1 after a traceback line.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

PRESETS = ["morph", "dissolve", "flow-dissolve", "snap-morph", "iris", "wipe", "luma"]
STYLE = {"morph": "morph", "dissolve": "dissolve", "flow-dissolve": "warp-dissolve", "snap-morph": "morph"}


def steer(name: str) -> None:
    slow = dict(kv.split("=") for kv in os.environ.get("FAKE_SLOW", "").split(",") if "=" in kv)
    if name in slow:
        time.sleep(float(slow[name]))
    if name in os.environ.get("FAKE_REFUSE", "").split(","):
        print("FAILED: the fake transitions.py refuses this pair", file=sys.stderr, flush=True)
        sys.exit(2)
    if name in os.environ.get("FAKE_FAIL", "").split(","):
        print("Traceback (most recent call last):", file=sys.stderr)
        print(f"RuntimeError: the fake {name} failed", file=sys.stderr, flush=True)
        sys.exit(1)


def canvas_of(a_shape: tuple[int, ...], b_shape: tuple[int, ...], max_long: int, policy: str) -> tuple[int, int]:
    (ha, wa), (hb, wb) = a_shape[:2], b_shape[:2]
    w, h = (min(wa, wb), min(ha, hb)) if policy == "common" else (wb, hb)
    if max_long and max(w, h) > max_long:
        s = max_long / max(w, h)
        w, h = round(w * s), round(h * s)
    return max(2, w - w % 2), max(2, h - h % 2)


def cmd_pair(a: argparse.Namespace) -> int:
    import cv2
    import numpy as np

    anchors = [x for x in a.anchors.split(";") if x.strip()]
    if anchors and len(anchors) < 3:
        print("FAILED: At least three anchor pairs are needed.", file=sys.stderr, flush=True)
        return 2
    steer("pair")
    t0 = time.time()
    A, B = cv2.imread(a.before), cv2.imread(a.after)
    if A is None or B is None:
        print("FAILED: Unsupported file type", file=sys.stderr, flush=True)
        return 2
    seconds = min(10.0, max(0.1, a.seconds))
    fps = max(1.0, a.fps)
    n = max(2, round(seconds * fps))
    w, h = canvas_of(A.shape, B.shape, a.max_long, a.canvas)
    A2, B2 = cv2.resize(A, (w, h), interpolation=cv2.INTER_AREA), cv2.resize(B, (w, h), interpolation=cv2.INTER_AREA)
    frames = [A2] + [cv2.addWeighted(A2, 1 - i / (n - 1), B2, i / (n - 1), 0) for i in range(1, n - 1)] + [B2]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    vw = cv2.VideoWriter(str(out / "transition.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for f in frames:
        vw.write(f)
    vw.release()
    k = min(8, n)
    picks = [round(j * (n - 1) / (k - 1)) for j in range(k)] if k > 1 else [0]
    cv2.imwrite(str(out / "strip.jpg"), np.concatenate([frames[i] for i in picks], axis=1))
    grey = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0 for f in frames]
    d = [float(np.abs(grey[i + 1] - grey[i]).mean()) for i in range(n - 1)]
    interior = d[1:-1] if len(d) > 2 else d
    cls = a.force_class or "B"
    report = {
        "tool_version": "0.1.0",
        "spec": {
            "seconds": seconds,
            "fps": fps,
            "style": STYLE.get(a.preset, "portal" if a.preset in ("iris", "wipe") else a.preset),
            "warp_amount": a.warp,
            "color_strength": a.color,
            "max_long_edge": a.max_long,
            "canvas": a.canvas,
            "anchors": [[float(v) for v in x.split(",")] for x in anchors],
            "force_class": a.force_class,
            "camera": a.camera,
            "zoom": a.zoom,
            "anchor_falloff": a.anchor_falloff,
        },
        "class": cls,
        "method": "homography+dis" if cls == "A" else "saliency-panzoom",
        "sparse_inliers": 120 if cls == "A" else 0,
        "sparse_rmse": 0.8 if cls == "A" else None,
        "mean_certainty": 0.93 if cls == "A" else 0.5,
        "median_disp_px": 3.21 if cls == "A" else 24.71,
        "canvas": [w, h],
        "canvas_policy": a.canvas,
        "n_frames": n,
        "quality": {
            "warping_error": 0.0207,
            "flicker": {
                "mean": round(float(np.mean(d)), 5),
                "max": round(float(np.max(d)), 5),
                "spikiness": round(float(np.max(d) / (np.mean(d) + 1e-6)), 4),
                "edge_ratio": round(float(max(d[0], d[-1]) / (np.mean(interior) + 1e-6)), 4),
            },
            "goal": {
                "feat_floor": 0.0826,
                "laplace_floor": 0.9,
                "contrast_floor": 0.95,
                "dissolve_fit": 0.99,
                "motion_share": 0.0,
            },
            "endpoint": {"first_vs_A": 0.0, "last_vs_B": 0.0},
            "n_frames": n,
            "proxy_long": 480,
        },
        "correspondence_s": round(time.time() - t0, 4),
        "render_s": round(time.time() - t0, 4),
        "total_s": round(time.time() - t0, 6),
        "outputs": ["transition.mp4", "strip.jpg", "report.json"],
    }
    if cls == "B":
        report.update({"pan_fraction": [0.09, 0.25], "camera": a.camera, "zoom": a.zoom})
    (out / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "spec"}, indent=2))
    print(f"Wrote {', '.join(report['outputs'])} in {out.resolve()}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="transitions.py", description="A fake transitions.py for the studio's tests.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pp = sub.add_parser("pair", help="render the transition between two photos")
    pp.add_argument("before")
    pp.add_argument("after")
    pp.add_argument("--out", required=True)
    pp.add_argument("--seconds", type=float, default=1.0)
    pp.add_argument("--fps", type=float, default=30.0)
    pp.add_argument("--preset", default="morph", choices=PRESETS)
    pp.add_argument("--color", type=float, default=0.7, help="color path strength 0..1")
    pp.add_argument("--warp", type=float, default=1.0, help="geometric warp amount 0..1")
    pp.add_argument("--max-long", type=int, default=0, help="cap the canvas long edge (0 = native)")
    pp.add_argument(
        "--canvas",
        default="finish",
        choices=["finish", "common"],
        help="canvas aspect: finish = the AFTER photo's ratio (default); "
        "common = the smaller width and height of the two",
    )
    pp.add_argument("--anchors", default="", help='"ax,ay,bx,by;..." canvas pixels, A -> B, >= 3 pairs')
    pp.add_argument(
        "--anchor-falloff",
        type=float,
        default=0.45,
        help="anchors: fade the anchored field to zero at the canvas "
        "border over this fraction of the short edge (default 0.45; "
        "0 = the plain MLS field, whose frame edge shows; T16)",
    )
    pp.add_argument("--class", dest="force_class", default="", choices=["", "A", "B"], help="force the pair class")
    pp.add_argument(
        "--camera",
        default="flat",
        choices=["flat", "ramp", "model"],
        help="class B camera move: flat = the pan-and-zoom as is; "
        "ramp = near content (bottom rows) moves more, no "
        "model; model = the same from Depth Anything V2 Small "
        "(needs `transitions.py warmup` once)",
    )
    pp.add_argument("--zoom", type=float, default=0.1, help="class B zoom fraction per frame, clamped to [0.02, 0.5]")
    sub.add_parser("check", help="environment self-test")
    sub.add_parser("warmup", help="fetch and verify the depth model once (the only command that downloads)")
    args = ap.parse_args(argv)
    if args.cmd != "pair":
        print(f"the fake transitions.py has no {args.cmd}")
        return 0
    return cmd_pair(args)


if __name__ == "__main__":
    sys.exit(main())
