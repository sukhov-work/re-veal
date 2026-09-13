"""Render a transition from two endpoint frames and a TransitionSpec.

Order of operations per frame (the deterministic skeleton):
  1. color path: pull both endpoints toward the interpolated statistic
  2. geometry: symmetric forward-splat morph at t_warp (or portal/luma mask)
  3. mix: cross-dissolve at t_mix
Then, optionally, the generative tier (bounded, budgeted) and a frequency
split back onto the full-resolution skeleton.
"""
import logging
import time

import numpy as np

from . import color as C
from . import correspond as CO
from . import warp as W
from .generative import run_enrichment
from .media import common_canvas, cover

log = logging.getLogger("impossible.render")


def prepare(A, B, spec):
    """Shared canvas + correspondence, computed once per transition."""
    w, h = common_canvas(A, B, spec.max_long_edge or None)
    A2, B2 = cover(A, w, h), cover(B, w, h)
    anchors = None
    if spec.anchors:
        a = np.array(spec.anchors, np.float32)
        anchors = (a[:, :2], a[:, 2:])
    t = time.time()
    corr = CO.dense_displacement(A2, B2, anchors=anchors,
                                 force_class=spec.force_class or None)
    corr["diag"]["correspondence_s"] = round(time.time() - t, 2)
    return A2, B2, corr


def render_frames(A, B, spec, corr=None, backend="null"):
    """Returns (frames, report). frames[0] ~ A, frames[-1] ~ B."""
    spec.clamp()
    if corr is None:
        A, B, corr = prepare(A, B, spec)
    n = spec.n_frames()
    sA, sB = C.lab_stats(A), C.lab_stats(B)
    frames, disps = [], []
    t0 = time.time()
    for i in range(n):
        tw, tm, u = spec.progress(i)
        Ai, Bi = C.color_pair_at(A, B, sA, sB, u, spec.color_strength)
        if spec.style in ("morph", "warp-dissolve"):
            f = W.morph_frame(Ai, Bi, corr, tw, tm)
        elif spec.style == "portal":
            m = W.portal_mask(A.shape[0], A.shape[1], tm, spec.portal, spec.portal_feather)[..., None]
            f = (Ai * (1 - m) + Bi * m).astype(np.uint8)
        elif spec.style == "luma":
            m = C.luma_mask(Ai, tm)[..., None]
            f = (Ai * (1 - m) + Bi * m).astype(np.uint8)
        else:                                       # dissolve
            f = (Ai.astype(np.float32) * (1 - tm) + Bi * tm).astype(np.uint8)
        frames.append(f)
        disps.append(corr["dAB"] / max(n - 1, 1))
    # pin the endpoints exactly: the transition must begin and end on the
    # true frames whatever the color path did in between
    frames[0], frames[-1] = A.copy(), B.copy()
    report = {"class": corr["cls"], "method": corr["method"], **corr["diag"],
              "render_s": round(time.time() - t0, 2), "n_frames": n,
              "canvas": [A.shape[1], A.shape[0]]}
    frames, gen = run_enrichment(frames, disps, spec, backend=backend)
    report["generative"] = gen
    return frames, report
