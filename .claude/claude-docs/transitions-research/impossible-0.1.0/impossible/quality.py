"""Transition quality: a basket of metrics, never one number pretending to
be truth (Reveal's lesson: pixel scales are scene-dependent).

  warping_error  mean |I_{t+1} - warp(I_t, flow)| on 0..1 gray: temporal
                 consistency, the classic blind-video-consistency metric.
  flicker        VBench-style mean abs diff between adjacent frames.
  endpoint_fidelity  first/last frame vs the inputs (must be ~0).
  composite      a ranking score for candidate selection ONLY.
"""
import cv2
import numpy as np


def _g(f):
    return cv2.cvtColor(f, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0


def warping_error(frames):
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_FAST)
    errs = []
    for a, b in zip(frames[:-1], frames[1:]):
        ga, gb = _g(a), _g(b)
        f = dis.calc((ga * 255).astype(np.uint8), (gb * 255).astype(np.uint8), None)
        h, w = ga.shape
        gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
        wb = cv2.remap(gb, gx + f[..., 0], gy + f[..., 1], cv2.INTER_LINEAR)
        errs.append(float(np.abs(wb - ga).mean()))
    return float(np.mean(errs)) if errs else 0.0


def flicker(frames):
    """Adjacent-frame change. `spikiness` (max/mean) is informational
    only: an eased mask reveal legitimately concentrates its change
    mid-transition (bell-shaped, measured 2.6-3.4 on iris/luma). The
    defect this exists to catch is a CUT hiding inside a transition, whose
    signature is an endpoint step far above the interior: `edge_ratio`."""
    d = [float(np.abs(_g(a) - _g(b)).mean()) for a, b in zip(frames[:-1], frames[1:])]
    if not d:
        return {"mean": 0.0, "max": 0.0, "spikiness": 0.0, "edge_ratio": 0.0}
    interior = d[1:-1] if len(d) > 2 else d
    return {"mean": float(np.mean(d)), "max": float(np.max(d)),
            "spikiness": float(np.max(d) / (np.mean(d) + 1e-6)),
            "edge_ratio": float(max(d[0], d[-1]) / (np.mean(interior) + 1e-6))}


def endpoint_fidelity(frames, A, B):
    return {"first_vs_A": float(np.abs(frames[0].astype(int) - A.astype(int)).mean()),
            "last_vs_B": float(np.abs(frames[-1].astype(int) - B.astype(int)).mean())}


def assess(frames, A=None, B=None):
    r = {"warping_error": round(warping_error(frames), 4),
         "flicker": {k: round(v, 4) for k, v in flicker(frames).items()},
         "n_frames": len(frames)}
    if A is not None and B is not None:
        r["endpoint"] = {k: round(v, 2) for k, v in endpoint_fidelity(frames, A, B).items()}
    # ranking only: penalize spikes (cuts hiding inside a "transition") and
    # warping error; reward nothing, because smoothness alone is a dissolve
    r["composite"] = round(-(r["warping_error"] * 10 + max(0.0, r["flicker"]["edge_ratio"] - 1.0)), 4)
    return r


def thumb_strip(frames, k=8, height=160):
    idx = np.linspace(0, len(frames) - 1, k).round().astype(int)
    tiles = []
    for i in idx:
        f = frames[i]
        w = int(f.shape[1] * height / f.shape[0])
        tiles.append(cv2.resize(f, (w, height), interpolation=cv2.INTER_AREA))
    return np.concatenate(tiles, axis=1)
