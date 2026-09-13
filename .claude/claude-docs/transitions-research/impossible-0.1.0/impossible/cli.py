"""impossible CLI.

  python -m impossible probe                              environment report
  python -m impossible pair A.jpg B.jpg --out d [opts]     photo -> photo
  python -m impossible clips a.mov b.mov --cut-a 12.5 --cut-b 3.0 --out d
  python -m impossible sequence spec.json                 N items, N-1 transitions
  python -m impossible bench --out d                      local research runs (E1..)

Common options: --seconds 1.0 --preset morph|dissolve|flow-dissolve|
snap-morph|iris|luma|dream --dreaminess 0 --seed 0 --budget-min 10
--max-long 0 --anchors "ax,ay,bx,by;..." --class A|B
"""
import argparse
import json
import logging
import platform
import sys
import time
from pathlib import Path

import cv2
import numpy as np

from . import VERSION
from .grammar import SequenceSpec, spec_from
from .media import is_video, load_rgb
from .quality import assess, thumb_strip
from .render import prepare, render_frames

log = logging.getLogger("impossible")


def _common(ap):
    ap.add_argument("--out", required=True)
    ap.add_argument("--seconds", type=float, default=1.0)
    ap.add_argument("--fps", type=float, default=0.0, help="0 = from clip / 30")
    ap.add_argument("--preset", default="auto")
    ap.add_argument("--dreaminess", type=int, default=0)
    ap.add_argument("--backend", default="null")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--budget-min", type=float, default=10.0)
    ap.add_argument("--max-long", type=int, default=0)
    ap.add_argument("--anchors", default="")
    ap.add_argument("--class", dest="force_class", default="")
    ap.add_argument("--color", type=float, default=0.7)
    ap.add_argument("--warp", type=float, default=1.0)


def _spec(a, fps):
    anchors = []
    if a.anchors:
        for tok in a.anchors.split(";"):
            v = [float(x) for x in tok.split(",")]
            if len(v) == 4:
                anchors.append(v)
    return spec_from(a.preset, seconds=a.seconds, fps=fps, dreaminess=a.dreaminess,
                     seed=a.seed, budget_minutes=a.budget_min, max_long_edge=a.max_long,
                     anchors=anchors, force_class=a.force_class,
                     color_strength=a.color, warp_amount=a.warp)


def _write(out, frames, fps, name="transition.mp4", codec="libx264"):
    from .video import Writer
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    wr = Writer(out / name, frames[0].shape[1], frames[0].shape[0], fps, codec=codec)
    for f in frames:
        wr.write(f)
    wr.close()
    cv2.imwrite(str(out / "strip.jpg"), cv2.cvtColor(thumb_strip(frames), cv2.COLOR_RGB2BGR))
    return out / name


def cmd_probe(_):
    import av
    rows = [("impossible", VERSION), ("python", sys.version.split()[0]),
            ("platform", f"{platform.system()} {platform.machine()}"),
            ("opencv", cv2.__version__), ("pyav", av.__version__)]
    for enc in ("libx264", "libx265", "h264_videotoolbox", "hevc_videotoolbox"):
        try:
            av.codec.Codec(enc, "w")
            rows.append((f"encoder {enc}", "ok"))
        except Exception:
            rows.append((f"encoder {enc}", "missing"))
    try:
        import torch
        rows.append(("torch", f"{torch.__version__} mps={torch.backends.mps.is_available()}"))
    except Exception:
        rows.append(("torch", "not installed (deterministic tier only)"))
    for mod in ("kornia", "romatch", "mlx.core", "lpips", "transformers", "diffusers"):
        try:
            __import__(mod)
            rows.append((mod, "ok"))
        except Exception:
            rows.append((mod, "-"))
    for k, v in rows:
        print(f"  {k:<26} {v}")
    return 0


def cmd_pair(a):
    A, B = load_rgb(a.a), load_rgb(a.b)
    fps = a.fps or 30.0
    spec = _spec(a, fps)
    t = time.time()
    frames, rep = render_frames(A, B, spec, backend=a.backend)
    p = _write(a.out, frames, fps)
    rep["quality"] = assess(frames, frames[0], frames[-1])
    rep["total_s"] = round(time.time() - t, 2)
    Path(a.out, "report.json").write_text(json.dumps({"spec": spec.__dict__, **rep}, indent=2, default=str))
    print(json.dumps(rep, indent=2, default=str))
    print(f"wrote {p}")
    return 0


def cmd_clips(a):
    from .video import Writer, frame_at, frames_between, probe
    pa, pb = probe(a.a), probe(a.b)
    fps = a.fps or pa["fps"]
    tA, A = frame_at(a.a, a.cut_a)
    tB, B = frame_at(a.b, a.cut_b)
    spec = _spec(a, fps)
    t = time.time()
    A2, B2, corr = prepare(A, B, spec)
    frames, rep = render_frames(A2, B2, spec, corr=corr, backend=a.backend)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    _write(out, frames, fps)
    # stitched: [clip A up to cut] + transition + [clip B from cut]
    # v0.1 re-encodes everything (frame-accurate by construction; E12 adds
    # stream-copy of the untouched outer segments)
    w, h = frames[0].shape[1], frames[0].shape[0]
    wr = Writer(out / "stitched.mp4", w, h, fps)
    nA = nB = 0
    for _, f in frames_between(a.a, a.head_from, tA):
        wr.write(_fit(f, w, h)); nA += 1
    for f in frames[1:-1]:
        wr.write(f)
    for _, f in frames_between(a.b, tB, a.tail_to if a.tail_to > 0 else None):
        wr.write(_fit(f, w, h)); nB += 1
    total = wr.close()
    rep.update({"cut_a_actual": round(tA, 4), "cut_b_actual": round(tB, 4),
                "frames_from_a": nA, "frames_transition": len(frames) - 2,
                "frames_from_b": nB, "frames_total": total,
                "quality": assess(frames, frames[0], frames[-1]),
                "total_s": round(time.time() - t, 2)})
    Path(out, "report.json").write_text(json.dumps({"spec": spec.__dict__, **rep}, indent=2, default=str))
    print(json.dumps(rep, indent=2, default=str))
    print(f"wrote {out/'stitched.mp4'} and {out/'transition.mp4'}")
    return 0


def _fit(f, w, h):
    from .media import cover
    return f if (f.shape[1], f.shape[0]) == (w, h) else cover(f, w, h)


def cmd_sequence(a):
    """N items, N-1 transitions, one output. Images are held for
    item.hold seconds; videos contribute [cut_in, cut_out)."""
    from .video import Writer, frame_at, frames_between, probe
    seq = SequenceSpec.load(a.spec)
    kinds = [("video" if is_video(i.path) else "image") if i.kind == "auto" else i.kind
             for i in seq.items]
    first_vid = next((i for i, k in enumerate(kinds) if k == "video"), None)
    if seq.fps <= 0:
        seq.fps = probe(seq.items[first_vid].path)["fps"] if first_vid is not None else 30.0
    if seq.width <= 0 and first_vid is not None:
        p = probe(seq.items[first_vid].path)
        seq.width, seq.height = p["width"], p["height"]
    # endpoint frames per item
    ends = []
    for it, k in zip(seq.items, kinds):
        if k == "video":
            p = probe(it.path)
            t_out = it.cut_out if it.cut_out > 0 else (p["duration"] or 0) - 1.0 / p["fps"]
            ends.append((frame_at(it.path, it.cut_in)[1], frame_at(it.path, t_out)[1], t_out))
        else:
            im = load_rgb(it.path)
            ends.append((im, im, None))
    if seq.width <= 0:
        seq.width, seq.height = ends[0][0].shape[1], ends[0][0].shape[0]
    w, h = seq.width & ~1, seq.height & ~1
    out = Path(seq.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    wr = Writer(out, w, h, seq.fps)
    report = {"fps": seq.fps, "size": [w, h], "segments": []}
    for i, (it, k) in enumerate(zip(seq.items, kinds)):
        n0 = wr.n
        if k == "video":
            for _, f in frames_between(it.path, it.cut_in, ends[i][2]):
                wr.write(_fit(f, w, h))
        else:
            f = _fit(ends[i][0], w, h)
            for _ in range(int(round(it.hold * seq.fps))):
                wr.write(f)
        report["segments"].append({"item": it.path, "frames": wr.n - n0})
        if i < len(seq.items) - 1:
            sp = seq.transitions[i]
            sp.fps = seq.fps
            A = _fit(ends[i][1], w, h)
            B = _fit(ends[i + 1][0], w, h)
            frames, rep = render_frames(A, B, sp, backend=a.backend)
            for f in frames[1:-1]:
                wr.write(f)
            report["segments"].append({"transition": i, "frames": len(frames) - 2,
                                       "class": rep["class"], "method": rep["method"]})
    report["frames_total"] = wr.close()
    Path(str(out) + ".report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


def cmd_bench(a):
    """Local research runs. Writes bench/results.json for RESEARCH-PLAN.md.
    Deterministic tier only here; generative experiments are separate
    scripts the plan describes (E14-E16)."""
    from .video import Writer
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    res = {"platform": f"{platform.system()} {platform.machine()}", "runs": []}
    rng = np.random.default_rng(0)
    for (w, h) in ((1280, 720), (1920, 1080), (3840, 2160)):
        A = (rng.random((h, w, 3)) * 255).astype(np.uint8)
        A = cv2.GaussianBlur(A, (0, 0), 4)
        for _ in range(200):
            cv2.circle(A, (int(rng.integers(0, w)), int(rng.integers(0, h))),
                       int(rng.integers(8, 60)), tuple(int(v) for v in rng.integers(0, 255, 3)), -1)
        M = cv2.getRotationMatrix2D((w / 2, h / 2), 2.0, 1.05)
        M[0, 2] += w * 0.02
        B = cv2.warpAffine(A, M, (w, h), borderMode=cv2.BORDER_REFLECT)
        spec = spec_from("morph", seconds=1.0, fps=30)
        t = time.time()
        frames, rep = render_frames(A, B, spec)
        dt = time.time() - t
        t2 = time.time()
        wr = Writer(out / f"bench_{w}x{h}.mp4", w, h, 30)
        for f in frames:
            wr.write(f)
        wr.close()
        res["runs"].append({"res": f"{w}x{h}", "correspondence_s": rep["correspondence_s"],
                            "render_s": rep["render_s"], "per_frame_s": round(dt / len(frames), 3),
                            "encode_s": round(time.time() - t2, 2), "method": rep["method"]})
        print(res["runs"][-1])
    (out / "results.json").write_text(json.dumps(res, indent=2))
    return 0


def main(argv=None):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(prog="impossible", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("probe")
    p = sub.add_parser("pair"); p.add_argument("a"); p.add_argument("b"); _common(p)
    p = sub.add_parser("clips"); p.add_argument("a"); p.add_argument("b")
    p.add_argument("--cut-a", type=float, required=True)
    p.add_argument("--cut-b", type=float, required=True)
    p.add_argument("--head-from", type=float, default=0.0, help="start of clip A to keep")
    p.add_argument("--tail-to", type=float, default=-1.0, help="end of clip B to keep, -1 = all")
    _common(p)
    p = sub.add_parser("sequence"); p.add_argument("spec"); p.add_argument("--backend", default="null")
    p = sub.add_parser("bench"); p.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    return {"probe": cmd_probe, "pair": cmd_pair, "clips": cmd_clips,
            "sequence": cmd_sequence, "bench": cmd_bench}[a.cmd](a)
