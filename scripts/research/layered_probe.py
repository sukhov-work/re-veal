#!/usr/bin/env python3
"""Orchestrated layered transition probe: render a mismatched pair from a hand-written per-scene
SCORE (layers x actions x time windows), and build a review page with the three per-property boxes
(one picture / content transforms / nothing invented), a pick and a note per pair.

Research script (2026-09-26; plan §Rank 2026-09-26 item 3; the owner's score for mismatch_6 is
the first specification, verbatim in DECISIONS 2026-09-26 late). Imports `transitions.py` for the
canvas, the encoder, the depth model and the quality basket only; changes nothing in either tool.

A score file (JSON) names the layers of ONE pair. Each layer has a source photo (A or B), a mask
rule with parameters, a depth order for compositing (0 = back), an action with a time window in
clip fractions and a curve, and optional colour, drift and zoom terms:

  {"pair": "mismatch_6", "tag": "layered", "seconds": 2.0, "fps": 30, "max_long": 1920,
   "layers": [{"name": "sky", "from": "A", "mask": {"rule": "depth_bg", "lo": 0.02, "hi": 0.08},
               "depth": 0, "action": "backdrop", "to": "sky_b", "window": [0, 0.7], "curve": "ease"},
              ...]}

Mask rules: depth_fg / depth_bg (Depth Anything V2 Small disparity between lo and hi, offline
through transitions.py; `components` = bottom | top | left | right keeps the connected components
touching that border), clouds (cloud density from the per-row blue of the sky, `within` a layer),
stars (white top-hat blobs `within` a layer), polygon (hand-drawn, canvas fractions), all (1),
region_of (a wide soft region around a tight mask; round 2). Round-2 keys (2026-09-26): a backdrop's
`minus` / `exclude` entry as {"layer", "full", "dilate", "soft"} removes the layer's full alpha from
the fit and the residual; `fit_under` gives the rows under A's skyline B's fit from the start;
`snap_px` snaps the depth skyline to the photo's strongest vertical step; `recolor_mode: "L"`;
`fill_sigma` fills the holes of a backdrop's residual by a normalized convolution (three scales),
`fill_mode: "poly2"` by a weighted quadratic in x and y of the known residual (shape-free);
`minus_res` / `exclude_res` remove a layer from the residual only (the fit keeps its pixels);
`fit2d` makes the backdrop's fit a per-band quadratic in x; `refine: "dark_or_chroma"` + `chroma_d`;
`slide_between: [bandA, bandB]` slides a backdrop's top edge from one band's bottom line to the other's;
`dark_in` (near-black pixels in a row range), `minus_mask`, and `or: [names]` on any rule.
Round-3 keys (2026-09-27, all default-off; the round-2 renders are byte-identical through them):
a dissolve / materialise with `order: "edge"` erodes each cloud from its edge inward along the
distance transform of its dense part (`edge_norm` px, the default: the front runs in px at one speed
from every edge, `edge_thr` density bounds the dense part, `speed_density` lets it run faster through
thin parts, `front_soft_px` is the soft band, `front_wide_px` / `wide_gain` a wide thinning ramp ahead
of it, `turb_px_amp` at `turb_px` and 3 x `turb_px` displaces the front; global | blob: the same normalized to the largest inward distance, with `front_soft` and
`turb` in those units) and a thinning of the thin parts (`thin`); `shutter` on a moving layer blurs its pixels and
its alpha along the travel direction by shutter x the per-frame displacement (0.5 = a 180-degree
shutter); `carry_fit: BACKDROP` relights a moving layer's carried sky to the backdrop's fit at the
destination rows (a region that carries B's sky and slides shows the sky of other rows otherwise);
`edge_feather: {min, max, grad}` on a mask rule widens the matte's feather where the photo's own
gradient is soft; `fill_holes_px: n` on a mask rule fills its enclosed holes of up to n px; the `clouds`
rule takes `channel: "L_hp"` (a high-pass of L at `hp_px`, `hp_sign` -1 for dark clouds); curves `smootherstep`, `fall`, `settle`. The report gains a `measure` block: the
per-frame displacement of every moving layer, the semi-transparent share and the front width of every
dissolve, and the luminance step across every moving layer's boundary on the composite.
Round-4 keys (2026-09-27 evening; the owner rejected layers that slide in and out, "decorations in
2d scene", and asked the skyline to "transform into final one"; all default-off): action `morph_to`
carries a layer of A into a matched layer of B (`to`): an entropic optimal-transport map between the
two mattes on a coarse grid (`ot_grid`, `ot_eps`, `ot_mass` alpha | bright | dark) gives a smooth
displacement field each way; A's layer moves along it by the progress, B's layer comes back along the
reverse field, the two are mixed inside `mix_window` with their Lab statistics matched, so the first
part of the window is A's content reshaping and the last part B's content settling; a backdrop's
`flow` moves its two residual textures while they mix (no fade in place): `from: "layers"` along the
scene's one flow, interpolated from the matched layers' own motions; otherwise along a free transport
between the textures' bright or dark features; `extend_bottom_px` continues a band's matte below its line;
`advect: {amp_px, scale_px}` deforms a layer along a divergence-free noise field that grows with the
progress; `recolor_window` gives the colour path its own window (a cloud darkens with the sky, then
thins). `--auto PAIR` writes and renders a score built by fixed rules with no per-pair parameter.
Actions: backdrop (the low-order sky gradient of A moves to B's with the residual textures
crossfaded; alpha 1 everywhere), hold, recolor (per-row Lab statistics of the layer move to the
`to` layer's), dissolve (the layer erodes through its own density plus noise; thin parts first),
materialise (blobs appear in brightness order with jitter), exit / enter / move (a translation
along `direction` until the layer's box leaves or reaches the canvas; `zoom` scales about the
centre). Frame 0 is A and the last frame is B, exactly; every other frame is the composite.

  .venv/bin/python scripts/research/layered_probe.py --score scripts/research/scores/mismatch_6.json --out DIR
  ... --ref flat=benchmarks/runs/2026-09-26/anchors/mismatch_6/flat   (copy a reference clip beside it)
  .venv/bin/python scripts/research/layered_probe.py --out DIR --page-only [--picks picks.json]
"""
import argparse
import json
import math
import shutil
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import transitions as T  # noqa: E402

FIX = ROOT / "fixtures"
PROPS = (("one_picture", "one picture"), ("transforms", "content transforms"),
         ("not_invented", "nothing invented"))


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

def find_pair(pair):
    s = sorted(FIX.glob(f"{pair}_S.*"))
    f = sorted(FIX.glob(f"{pair}_F.*"))
    if not s or not f:
        raise SystemExit(f"fixture {pair} not found under {FIX}")
    return s[0], f[0]


def canvas_pair(pair, max_long):
    S, F = find_pair(pair)
    A, B = T.load_image_rgb(str(S)), T.load_image_rgb(str(F))
    w, h = T.common_canvas(A, B, max_long, "finish")
    return T.cover(A, w, h), T.cover(B, w, h)


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


# round 3 (2026-09-27): curves that start and end slower than the cosine ease. The cosine's middle
# half runs at nearly constant speed (its peak speed is 1.57 x its mean), which the owner read as
# "very linear"; smootherstep peaks at 1.875 x and has zero acceleration at both ends; `fall` is a
# constant acceleration from rest (an exit that drops away); `settle` a decelerating arrival.
CURVES_R3 = {
    "smootherstep": lambda u: u * u * u * (u * (6.0 * u - 15.0) + 10.0),
    "fall": lambda u: u * u,
    "settle": lambda u: 1.0 - (1.0 - u) ** 3,
}


def curve_of(name, u):
    if name in CURVES_R3:
        return float(min(1.0, max(0.0, CURVES_R3[name](u))))
    return T.curve(name, u)


def line_kernel(v, length):
    """A normalized line kernel `length` px long along the unit vector v: a box
    along x with fractional ends, rotated onto v (bilinear)."""
    k = int(2 * math.ceil(length / 2.0)) + 3
    c = k // 2
    base = np.zeros((k, k), np.float32)
    x0, x1 = c - length / 2.0, c + length / 2.0
    for x in range(k):
        base[c, x] = max(0.0, min(x + 0.5, x1) - max(x - 0.5, x0))
    ang = math.degrees(math.atan2(float(v[1]), float(v[0])))
    M = cv2.getRotationMatrix2D((float(c), float(c)), -ang, 1.0)
    kern = cv2.warpAffine(base, M, (k, k), flags=cv2.INTER_LINEAR)
    return kern / max(float(kern.sum()), 1e-6)


# ---------------------------------------------------------------------------
# Round 4 (2026-09-27 evening): a layer transforms into its counterpart
# ---------------------------------------------------------------------------

def _logsumexp(a, axis):
    m = a.max(axis=axis, keepdims=True)
    return (m + np.log(np.exp(a - m).sum(axis=axis, keepdims=True))).squeeze(axis)


def ot_fields(mass_a, mass_b, grid=64, eps=0.04, iters=60, smooth=1.5):
    """Entropic optimal transport between two non-negative mass maps (h, w),
    solved on a coarse grid (`grid` cells on the long side) in the log domain
    with the regularisation halved from 8 eps down to eps (eps in units of the
    long side). Returns the displacement field A -> B and the field B -> A in
    px, (h, w, 2) float32 each: the barycentric projection of the plan at the
    cells that hold mass, spread over the whole grid by a normalized
    convolution and upsampled. Deterministic (no random start)."""
    h, w = mass_a.shape
    long_ = float(max(h, w))
    gw, gh = max(4, int(round(w * grid / long_))), max(4, int(round(h * grid / long_)))
    a = cv2.resize(mass_a.astype(np.float32), (gw, gh), interpolation=cv2.INTER_AREA).astype(np.float64).ravel()
    b = cv2.resize(mass_b.astype(np.float32), (gw, gh), interpolation=cv2.INTER_AREA).astype(np.float64).ravel()
    ys, xs = np.mgrid[0:gh, 0:gw]
    pos = np.stack([(xs + 0.5) / gw * w, (ys + 0.5) / gh * h], -1).reshape(-1, 2) / long_
    ia, ib = a > 1e-3 * max(a.max(), 1e-12), b > 1e-3 * max(b.max(), 1e-12)
    zero = np.zeros((h, w, 2), np.float32)
    if ia.sum() < 4 or ib.sum() < 4:
        return zero, zero.copy(), {"cells": [int(ia.sum()), int(ib.sum())], "mean_px": 0.0, "max_px": 0.0}
    xa, xb = pos[ia], pos[ib]
    wa, wb = a[ia] / a[ia].sum(), b[ib] / b[ib].sum()
    C = ((xa[:, None, :] - xb[None, :, :]) ** 2).sum(-1)
    la, lb = np.log(wa), np.log(wb)
    f, g = np.zeros(len(xa)), np.zeros(len(xb))
    for k in (8.0, 4.0, 2.0, 1.0):
        e = (eps * k) ** 2
        for _ in range(iters):
            f = -e * _logsumexp((g[None, :] - C) / e + lb[None, :], axis=1)
            g = -e * _logsumexp((f[:, None] - C) / e + la[:, None], axis=0)
    P = np.exp((f[:, None] + g[None, :] - C) / e + la[:, None] + lb[None, :])
    d_a = ((P @ xb) / np.maximum(P.sum(1, keepdims=True), 1e-300) - xa) * long_
    d_b = ((P.T @ xa) / np.maximum(P.sum(0)[:, None], 1e-300) - xb) * long_

    def spread(d, idx):
        field = np.zeros((gh * gw, 2), np.float32)
        field[idx] = d
        m = idx.astype(np.float32)
        out = np.zeros((gh, gw, 2), np.float32)
        left = np.ones((gh, gw), np.float32)
        # the known cells keep their own value; the rest take the nearest
        # known values at three scales blended by confidence (no threshold)
        for i, sc in enumerate((smooth, 4.0 * smooth, 16.0 * smooth)):
            num = cv2.GaussianBlur((field * m[:, None]).reshape(gh, gw, 2), (0, 0), sc)
            den = cv2.GaussianBlur(m.reshape(gh, gw), (0, 0), sc)
            wk = left if i == 2 else np.clip(den / 0.2, 0, 1) * left
            out = out + num / np.maximum(den, 1e-6)[..., None] * wk[..., None]
            left = left - wk
        return cv2.resize(out, (w, h), interpolation=cv2.INTER_CUBIC)

    info = {"cells": [int(ia.sum()), int(ib.sum())],
            "mean_px": round(float(np.sqrt((d_a ** 2).sum(1)) @ wa), 1),
            "max_px": round(float(np.sqrt((d_a ** 2).sum(1)).max()), 1)}
    return spread(d_a, ia), spread(d_b, ib), info


def warp_along(img, field, p, border=cv2.BORDER_CONSTANT):
    """Move img along p x field (a smooth forward displacement, px): the
    backward map comes from a fixed-point inversion at quarter resolution."""
    if p == 0:
        return img
    h, w = field.shape[:2]
    hs, ws = max(2, h // 4), max(2, w // 4)
    fs = cv2.resize(field, (ws, hs), interpolation=cv2.INTER_AREA) * (ws / float(w))
    gx, gy = np.meshgrid(np.arange(ws, dtype=np.float32), np.arange(hs, dtype=np.float32))
    mx, my = gx - p * fs[..., 0], gy - p * fs[..., 1]
    for _ in range(3):
        fx = cv2.remap(fs[..., 0], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        fy = cv2.remap(fs[..., 1], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        mx, my = gx - p * fx, gy - p * fy
    sx = float(w) / ws
    mxf = cv2.resize(mx, (w, h), interpolation=cv2.INTER_LINEAR) * sx + (sx - 1) / 2.0
    myf = cv2.resize(my, (w, h), interpolation=cv2.INTER_LINEAR) * sx + (sx - 1) / 2.0
    return cv2.remap(img, mxf, myf, cv2.INTER_LINEAR, borderMode=border, borderValue=0)


def lab_stats(lab, alpha):
    """Alpha-weighted mean and std of a layer's Lab, (3, 2)."""
    wsum = max(float(alpha.sum()), 1e-6)
    out = np.zeros((3, 2), np.float32)
    for c in range(3):
        m = float((lab[..., c] * alpha).sum() / wsum)
        out[c, 0] = m
        out[c, 1] = float(np.sqrt((((lab[..., c] - m) ** 2) * alpha).sum() / wsum)) + 1e-3
    return out


def lab_match(lab, src, dst, clip=(0.4, 2.5)):
    """Give lab (statistics src) the statistics dst, both (3, 2)."""
    out = np.empty_like(lab)
    for c in range(3):
        gain = float(np.clip(dst[c, 1] / src[c, 1], clip[0], clip[1]))
        out[..., c] = (lab[..., c] - src[c, 0]) * gain + dst[c, 0]
    return out


def curl_field(h, w, scale_px, seed):
    """A divergence-free unit field (h, w, 2) from a smooth noise potential."""
    psi = noise_field(h, w, scale_px, seed)
    psi = cv2.GaussianBlur(psi, (0, 0), max(1.0, scale_px / 6.0))
    gy, gx = np.gradient(psi)
    v = np.stack([gy, -gx], -1).astype(np.float32)
    return v / max(float(np.sqrt((v ** 2).sum(-1)).max()), 1e-6)


def ramp(x, lo, hi):
    return smoothstep((x - lo) / max(hi - lo, 1e-6))


def noise_field(h, w, scale_px, seed):
    """Smooth noise in 0..1 at the given scale (a blurred seeded random field)."""
    rng = np.random.default_rng(seed)
    hs, ws = max(2, int(round(h / scale_px))), max(2, int(round(w / scale_px)))
    n = rng.random((hs, ws), dtype=np.float32)
    n = cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC)
    n = cv2.GaussianBlur(n, (0, 0), max(1.0, scale_px / 4))
    lo, hi = float(n.min()), float(n.max())
    return ((n - lo) / max(hi - lo, 1e-6)).astype(np.float32)


# ---------------------------------------------------------------------------
# Per-row Lab statistics (the colour path of a layer is per row: a sky is a
# vertical gradient, so one global mean would flatten it)
# ---------------------------------------------------------------------------

def row_stats(lab, alpha, bands=48, min_px=40):
    """(h, 3, 2) per-row Lab (mean, std), estimated per band on alpha-weighted
    pixels, interpolated across bands without pixels, smoothed over rows."""
    h = lab.shape[0]
    edges = np.linspace(0, h, bands + 1).astype(int)
    mean = np.full((bands, 3), np.nan, np.float32)
    std = np.full((bands, 3), np.nan, np.float32)
    for i in range(bands):
        sl = slice(edges[i], edges[i + 1])
        wgt = alpha[sl].ravel()
        if wgt.sum() < min_px:
            continue
        for c in range(3):
            v = lab[sl, :, c].ravel()
            m = float((v * wgt).sum() / wgt.sum())
            mean[i, c] = m
            std[i, c] = float(np.sqrt(((v - m) ** 2 * wgt).sum() / wgt.sum())) + 1e-3
    centers = (edges[:-1] + edges[1:]) / 2.0
    rows = np.arange(h, dtype=np.float32)
    out = np.zeros((h, 3, 2), np.float32)
    ok = ~np.isnan(mean[:, 0])
    if ok.sum() == 0:
        raise SystemExit("row_stats: the mask selects no pixels")
    for c in range(3):
        for k, arr in enumerate((mean, std)):
            v = np.interp(rows, centers[ok], arr[ok, c])
            out[:, c, k] = cv2.GaussianBlur(v.reshape(-1, 1), (0, 0), h / bands * 1.5).ravel()
    return out


def sky_fit2d(lab, alpha, bands=48, min_px=300):
    """(h, w, 3) low-order fit of a sky: per band a weighted least-squares
    quadratic in x (linear when the samples span under half the width,
    constant under a quarter), coefficients interpolated across bands and
    smoothed over rows. The per-row mean alone misses a lateral glow, and
    the hole a layer leaves in the residual then shows the layer's outline
    whatever fills it (round 2, 2026-09-26)."""
    h, w = alpha.shape
    edges = np.linspace(0, h, bands + 1).astype(int)
    xs = (np.arange(w, dtype=np.float32) / max(w - 1, 1)) * 2 - 1
    coef = np.full((bands, 3, 3), np.nan, np.float32)      # band, channel, (a, b, c)
    for i in range(bands):
        sl = slice(edges[i], edges[i + 1])
        wgt = np.clip(alpha[sl], 0, 1)
        if wgt.sum() < min_px:
            continue
        cols = wgt.sum(axis=0) > 0.5
        span = (xs[cols].max() - xs[cols].min()) / 2.0 if cols.any() else 0.0
        order = 2 if span >= 0.5 else (1 if span >= 0.25 else 0)
        X = np.stack([np.ones_like(xs), xs, xs * xs], axis=1)[:, :order + 1]
        Xb = np.repeat(X[None, :, :], edges[i + 1] - edges[i], axis=0).reshape(-1, order + 1)
        sw = np.sqrt(wgt).reshape(-1, 1)
        for c in range(3):
            y = lab[sl, :, c].reshape(-1, 1)
            sol, *_ = np.linalg.lstsq(Xb * sw, y * sw, rcond=None)
            coef[i, c, :order + 1] = sol.ravel()
            coef[i, c, order + 1:] = 0.0
    centers = (edges[:-1] + edges[1:]) / 2.0
    rows = np.arange(h, dtype=np.float32)
    ok = ~np.isnan(coef[:, 0, 0])
    if ok.sum() == 0:
        raise SystemExit("sky_fit2d: the mask selects no pixels")
    out = np.zeros((h, w, 3), np.float32)
    for c in range(3):
        cr = np.zeros((h, 3), np.float32)
        for k in range(3):
            v = np.interp(rows, centers[ok], coef[ok, c, k])
            cr[:, k] = cv2.GaussianBlur(v.reshape(-1, 1), (0, 0), h / bands * 1.5).ravel()
        out[..., c] = cr[:, 0:1] + cr[:, 1:2] * xs[None, :] + cr[:, 2:3] * (xs * xs)[None, :]
    return out


def row_transfer(lab, src, dst, strength, clip=(0.4, 2.5)):
    """Move lab's per-row statistics from src toward dst (both (h, 3, 2)) by
    strength in 0..1. Returns float32 Lab."""
    if strength <= 0:
        return lab
    out = np.empty_like(lab)
    for c in range(3):
        m0, s0 = src[:, c, 0][:, None], src[:, c, 1][:, None]
        m1, s1 = dst[:, c, 0][:, None], dst[:, c, 1][:, None]
        gain = np.clip(s1 / s0, clip[0], clip[1])
        out[..., c] = (lab[..., c] - m0) * gain + m1
    return lab + strength * (out - lab)


def lab_to_rgb(lab):
    return cv2.cvtColor(lab.astype(np.float32), cv2.COLOR_Lab2RGB) * 255.0


def fill_poly2(res, w):
    """Fill the holes (w < 1) of a residual with a weighted least-squares
    quadratic in (x, y) of the known part: shape-free by construction, so a
    hole never shows its own outline (the normalized convolution filled a
    tree-crown hole with a crown-shaped patch of the glow at its rim)."""
    h, w_ = w.shape
    hs, ws = max(8, h // 4), max(8, w_ // 4)
    rw = cv2.resize(res, (ws, hs), interpolation=cv2.INTER_AREA)
    ws_ = cv2.resize(w, (ws, hs), interpolation=cv2.INTER_AREA)

    def design(hh, ww):
        yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
        xx = xx / max(ww - 1, 1) * 2 - 1
        yy = yy / max(hh - 1, 1) * 2 - 1
        return np.stack([np.ones_like(xx), xx, yy, xx * xx, xx * yy, yy * yy], axis=-1).reshape(-1, 6)

    Xs = design(hs, ws)
    sw = np.sqrt(np.clip(ws_, 0, 1)).reshape(-1, 1)
    Xf = design(h, w_)
    fill = np.empty_like(res)
    for c in range(res.shape[2]):
        coef, *_ = np.linalg.lstsq(Xs * sw, rw[..., c].reshape(-1, 1) * sw, rcond=None)
        fill[..., c] = (Xf @ coef).reshape(h, w_)
    return res * w[..., None] + fill * (1.0 - w)[..., None]


def fill_holes(res, w, sigma):
    """A residual (h, w, 3) known where w is 1: fill the holes (w < 1) with a
    normalized convolution of the known part at three scales (sigma, 3 sigma,
    9 sigma), so a hole wider than the kernel still takes the surrounding
    low-frequency structure (a sky's lateral glow) and never the row mean
    alone. Round 2, 2026-09-26: a hole filled by the per-row fit showed as
    a dark silhouette in the shape of the excluded layer."""
    # the fill is low-frequency: computed at 1/4 resolution (16x cheaper at
    # the 9-sigma scale) and resized back
    h, w_ = w.shape
    hs, ws = max(8, h // 4), max(8, w_ // 4)
    rw = cv2.resize(res * w[..., None], (ws, hs), interpolation=cv2.INTER_AREA)
    ws_ = cv2.resize(w, (ws, hs), interpolation=cv2.INTER_AREA)
    # the scales blend by their confidence (the known fraction under the
    # kernel) instead of switching at a threshold: a switch draws the
    # iso-distance line from the hole's rim as a contour inside the hole
    fill = np.zeros_like(rw)
    left = np.ones(ws_.shape, np.float32)
    for i, sc in enumerate((sigma, 3.0 * sigma, 9.0 * sigma)):
        num = cv2.GaussianBlur(rw, (0, 0), sc / 4.0)
        den = cv2.GaussianBlur(ws_, (0, 0), sc / 4.0)
        f = num / np.maximum(den, 1e-6)[..., None]
        wk = left if i == 2 else np.clip(den / 0.2, 0, 1) * left
        fill = fill + f * wk[..., None]
        left = left - wk
    fill = cv2.resize(fill, (w_, h), interpolation=cv2.INTER_LINEAR)
    return res * w[..., None] + fill * (1.0 - w)[..., None]


# ---------------------------------------------------------------------------
# Mask rules
# ---------------------------------------------------------------------------

def keep_components(mask, touch, min_area=200):
    """Keep the connected components of a soft mask (> 0.5) that touch the
    named border (bottom | top | left | right | any)."""
    h, w = mask.shape
    hard = (mask > 0.5).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(hard)
    keep = np.zeros(n, bool)
    for i in range(1, n):
        x, y, bw, bh, area = st[i]
        if area < min_area:
            continue
        hit = {"bottom": y + bh >= h, "top": y <= 0, "left": x <= 0,
               "right": x + bw >= w, "any": True}[touch]
        keep[i] = hit
    sel = keep[lab]
    return np.where(sel, mask, 0.0).astype(np.float32)


class Scene:
    """Both photos on the canvas with their Lab, depth and the layer masks."""

    def __init__(self, A, B, seed=0):
        self.A, self.B = A, B
        self.h, self.w = A.shape[:2]
        self.lab = {"A": T.lab_of(A), "B": T.lab_of(B)}
        self.disp = {}
        self.masks = {}
        self.seed = seed
        self.n = 2          # frames of the clip; set by render_score (the shutter needs px per frame)
        self.layers_all = []    # every layer of the score, rendered or not (set by build_layers)

    def layer_flow(self, sigma=0.12, kappa=0.02, names=None):
        """One flow for the whole scene, interpolated from the motions of its
        matched layers (a `morph_to` layer's transport field inside its matte,
        a `move_to` layer's map at its blob): a normalized convolution at
        `sigma` x the long side, falling to zero far from every matched layer
        (`kappa`). Returns the field A -> B and the field B -> A, px."""
        key = ("_flow", sigma, kappa, tuple(names) if names else None)
        if key in self.masks:
            return self.masks[key]
        h, w = self.h, self.w
        hs, ws = max(8, h // 8), max(8, w // 8)
        gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
        num = [np.zeros((hs, ws, 2), np.float32), np.zeros((hs, ws, 2), np.float32)]
        den = [np.zeros((hs, ws), np.float32), np.zeros((hs, ws), np.float32)]
        for lay in self.layers_all:
            if names and lay.name not in names:
                continue
            if lay.action == "morph_to":
                pairs = ((lay.F, lay.alpha0), (lay.G, lay.tgt.alpha0))
            elif lay.action == "move_to":
                Tm, b = lay.T_bw, lay.b_bw
                Ti = np.linalg.inv(Tm)
                fwd = np.stack([(Tm[0, 0] - 1) * gx + Tm[0, 1] * gy + b[0], Tm[1, 0] * gx + (Tm[1, 1] - 1) * gy + b[1]], -1)
                bi = -Ti @ b
                rev = np.stack([(Ti[0, 0] - 1) * gx + Ti[0, 1] * gy + bi[0], Ti[1, 0] * gx + (Ti[1, 1] - 1) * gy + bi[1]], -1)
                pairs = ((fwd.astype(np.float32), lay.alpha0), (rev.astype(np.float32), lay.by_name[lay.spec["to"]].alpha0))
            else:
                continue
            for k, (fld, a) in enumerate(pairs):
                a_s = cv2.resize(a, (ws, hs), interpolation=cv2.INTER_AREA)
                f_s = cv2.resize(fld * a[..., None], (ws, hs), interpolation=cv2.INTER_AREA)
                num[k] += f_s
                den[k] += a_s
        sg = sigma * max(hs, ws)
        out = []
        for k in range(2):
            n_ = cv2.GaussianBlur(num[k], (0, 0), sg)
            d_ = cv2.GaussianBlur(den[k], (0, 0), sg)
            out.append(cv2.resize(n_ / (d_ + kappa)[..., None], (w, h), interpolation=cv2.INTER_CUBIC))
        self.masks[key] = (out[0], out[1])
        return self.masks[key]

    def disparity(self, src):
        if src not in self.disp:
            self.disp[src] = T.model_disparity(self.A if src == "A" else self.B)
        return self.disp[src]

    def mask(self, layer):
        name = layer["name"]
        if name in self.masks:
            return self.masks[name]
        m = layer["mask"]
        rule, src = m["rule"], layer["from"]
        h, w = self.h, self.w
        if rule == "all":
            a = np.ones((h, w), np.float32)
        elif rule in ("depth_fg", "depth_bg"):
            d = self.disparity(src)
            a = ramp(d, m.get("lo", 0.02), m.get("hi", 0.08))
            if m.get("dilate", 0):
                # the depth is 0 at the tips of a tree crown: widen the region
                # the refinement below is allowed to keep
                k = int(m["dilate"])
                a = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1)))
            if m.get("refine") == "dark":
                # the depth model is smooth at leaf level; darkness against
                # the per-row brightness of the rest of the photo is not
                a = a * self._darkness(src, 1.0 - a, m)
            elif m.get("refine") == "dark_or_chroma":
                # a lit leaf is not dark; its chroma is far from the sky's
                # per-row chroma (round 2, 2026-09-26: green leaf tips stayed
                # in the sky residual and floated before the trees arrived)
                a = a * np.maximum(self._darkness(src, 1.0 - a, m), self._chroma_far(src, 1.0 - a, m))
            if m.get("min_blob", 0):
                # drop the small blobs a refinement keeps (a star has the
                # chroma of a leaf but not its area; round 2, 2026-09-26)
                n_, lab_, st_, _ = cv2.connectedComponentsWithStats((a > 0.5).astype(np.uint8))
                small = np.zeros(n_, bool)
                small[1:] = st_[1:, cv2.CC_STAT_AREA] < int(m["min_blob"])
                a = np.where(small[lab_], 0.0, a).astype(np.float32)
            if m.get("grow", 0):
                # a moving layer carries the background within `grow` px of
                # its edge, so its soft edge never mixes with the backdrop
                k = int(m["grow"])
                a = np.maximum(a, cv2.GaussianBlur(cv2.dilate(a, np.ones((2 * k + 1, 2 * k + 1), np.uint8)), (0, 0), 1.0))
            if rule == "depth_bg":
                a = 1.0 - a
            if m.get("components"):
                if m.get("components_bridge", 0):
                    # keep the blobs that touch the border once bridged over
                    # `components_bridge` px: an isolated branch near the
                    # crown stays, a unit at the top does not (round 2)
                    kb = int(m["components_bridge"])
                    bridged = cv2.dilate((a > 0.5).astype(np.float32), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * kb + 1, 2 * kb + 1)))
                    keep = keep_components(bridged, m["components"], m.get("min_area", 200)) > 0.5
                    a = np.where(keep, a, 0.0).astype(np.float32)
                else:
                    a = keep_components(a, m["components"], m.get("min_area", 200))
            if m.get("blur", 0):
                a = cv2.GaussianBlur(a, (0, 0), m["blur"])
        elif rule in ("skyline_below", "skyline_above"):
            a = self._skyline(src, m)
            if rule == "skyline_above":
                a = 1.0 - a
        elif rule == "invert":
            a = 1.0 - self.masks[m["of"]]
        elif rule == "region_of":
            # a wide, soft region around a tight mask: the rendered layer then
            # carries the photo's own background between its leaves instead of
            # a leaf-level cut (round 2, 2026-09-26: the tree crown afterimage)
            k = int(m.get("dilate", 40))
            a = (self.masks[m["of"]] > float(m.get("thr", 0.5))).astype(np.float32)
            if k:
                a = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1)))
            if m.get("components"):
                a = keep_components(a, m["components"], m.get("min_area", 200))
            if m.get("soft", 0):
                a = cv2.GaussianBlur(a, (0, 0), float(m["soft"]))
        elif rule == "invert_any":
            a = 1.0 - np.max([self.masks[n] for n in m["of"]], axis=0)
        elif rule == "depth_band":
            d = self.disparity(src)
            s = float(m.get("soft", 0.04))
            a = ramp(d, m["lo"], m["lo"] + s) * (1.0 - ramp(d, m["hi"], m["hi"] + s))
        elif rule == "sun":
            a = self._sun(src, self.masks[m["within"]], m, name)
        elif rule == "band_dark":
            a = self._band_dark(src, m, name)
        elif rule in ("below_band", "above_band"):
            top, bottom = self.masks["_band_" + m["of"]]
            yy = np.arange(h, dtype=np.float32)[:, None]
            f = float(m.get("feather", 3.0))
            a = (smoothstep((yy - bottom[None, :]) / f) if rule == "below_band"
                 else smoothstep((top[None, :] - yy) / f))
        elif rule == "dark_in":
            # the near-black pixels (L below `L`) inside a row range (canvas
            # fractions): the thin masts and cranes a per-column band misses
            # (round 2 on mismatch_4, 2026-09-26)
            L = self.lab[src][..., 0]
            r0, r1 = m.get("rows", [0.0, 1.0])
            if m.get("relative") == "local":
                # dark against the local mean of the `within` region (a
                # normalized convolution over `local_px`): a crane against
                # the glow counts, the dim sky at the frame's side does not
                # (an absolute L threshold cannot tell them apart: B's cranes
                # L 6–25, its dim sky 18–30, measured 2026-09-26)
                wm = (self.masks[m["within"]] > 0.5).astype(np.float32) if m.get("within") else np.ones_like(L)
                sg = float(m.get("local_px", 120))
                Lloc = cv2.GaussianBlur(L * wm, (0, 0), sg) / np.maximum(cv2.GaussianBlur(wm, (0, 0), sg), 1e-3)
                a = (ramp((Lloc - L) / np.maximum(Lloc, 4.0), m.get("dark_lo", 0.35), m.get("dark_hi", 0.6)) > 0.5).astype(np.float32)
            else:
                a = (L < float(m.get("L", 15.0))).astype(np.float32)
            a[: int(r0 * h)] = 0.0
            a[int(r1 * h):] = 0.0
            if m.get("within"):
                a = a * (self.masks[m["within"]] > 0.5)
            if m.get("min_blob", 0):
                n_, lab_, st_, _ = cv2.connectedComponentsWithStats(a.astype(np.uint8))
                small = np.zeros(n_, bool)
                small[1:] = st_[1:, cv2.CC_STAT_AREA] < int(m["min_blob"])
                a = np.where(small[lab_], 0.0, a).astype(np.float32)
            k = int(m.get("dilate", 2))
            if k:
                a = cv2.dilate(a, np.ones((2 * k + 1, 2 * k + 1), np.uint8))
            a = cv2.GaussianBlur(a, (0, 0), float(m.get("feather", 1.0)))
        elif rule == "minus_mask":
            a = self.masks[m["of"]] * (1.0 - self.masks[m["minus"]])
        elif rule == "polygon":
            pts = np.array([[x * w, y * h] for x, y in m["points"]], np.int32)
            a = np.zeros((h, w), np.uint8)
            cv2.fillPoly(a, [pts], 255)
            a = cv2.GaussianBlur(a.astype(np.float32) / 255.0, (0, 0), m.get("feather", 3))
        elif rule == "clouds":
            a = self._clouds(src, self.masks[m["within"]], m)
        elif rule == "stars":
            a = self._stars(src, self.masks[m["within"]], m)
        else:
            raise SystemExit(f"unknown mask rule {rule!r}")
        for other in m.get("or", []):
            a = np.maximum(a, self.masks[other])      # the union with an earlier mask
        if m.get("fill_holes_px", 0):
            # round 3: fill the ENCLOSED holes of the support up to
            # `fill_holes_px` px of area (a thin cloud band whose haze falls
            # under the density floor left holes through which the clear-sky
            # fill showed from frame 1: the dark patches of round 2). A
            # morphological closing was tried first and bridged the sky
            # between the clouds (55 % cover, many small clouds): the
            # backdrop's fit lost every pixel.
            hard = (a > 0.5).astype(np.uint8)
            n_, lab_, st_, _ = cv2.connectedComponentsWithStats(1 - hard)
            fill = np.zeros(n_, bool)
            for i in range(1, n_):
                x, y, bw, bh, area = st_[i]
                touches = x <= 0 or y <= 0 or x + bw >= w or y + bh >= h
                fill[i] = (area <= int(m["fill_holes_px"])) and not touches
            filled = np.where(fill[lab_], 1.0, hard).astype(np.float32)
            a = np.maximum(a, cv2.GaussianBlur(filled, (0, 0), 1.0))
        if rule not in ("depth_fg", "depth_bg") and m.get("grow", 0):
            # any moving layer may carry the background within `grow` px of
            # its edge (the depth rules apply it before their inversion)
            k = int(m["grow"])
            a = np.maximum(a, cv2.GaussianBlur(cv2.dilate(a, np.ones((2 * k + 1, 2 * k + 1), np.uint8)), (0, 0), 1.0))
        ef = m.get("edge_feather")
        if ef:
            # round 3: a feather that follows the photo's own edge — tight
            # (sigma `min`) where the L gradient under the matte edge is at
            # least `grad` L per px, wide (sigma `max`) where the photo is smooth
            L = cv2.GaussianBlur(self.lab[src][..., 0], (0, 0), 1.0)
            gx = cv2.Sobel(L, cv2.CV_32F, 1, 0, ksize=3) / 8.0
            gy = cv2.Sobel(L, cv2.CV_32F, 0, 1, ksize=3) / 8.0
            gs = np.clip(cv2.GaussianBlur(np.sqrt(gx * gx + gy * gy), (0, 0), 3.0) / float(ef.get("grad", 6.0)), 0, 1)
            tight = cv2.GaussianBlur(a, (0, 0), float(ef.get("min", 1.0)))
            wide = cv2.GaussianBlur(a, (0, 0), float(ef.get("max", 10.0)))
            a = gs * tight + (1.0 - gs) * wide
        self.masks[name] = a.astype(np.float32)
        return self.masks[name]

    def _darkness(self, src, bg, m):
        """0..1: how much darker than the per-row brightness of `bg` (the rest
        of the photo) a pixel is; 1 at `dark_hi` of the way to black."""
        lab = self.lab[src]
        st = row_stats(lab, np.clip(bg, 0, 1), min_px=300)
        Lfit = np.maximum(st[:, 0, 0], float(m.get("dark_floor", 4.0)))[:, None]
        return ramp((Lfit - lab[..., 0]) / Lfit, m.get("dark_lo", 0.35), m.get("dark_hi", 0.7))

    def _chroma_far(self, src, bg, m):
        """0..1: how far a pixel's (a*, b*) sits from the per-row chroma of
        `bg`; 1 at `chroma_d` and beyond, 0 at half of it."""
        lab = self.lab[src]
        st = row_stats(lab, np.clip(bg, 0, 1), min_px=300)
        da = lab[..., 1] - st[:, 1, 0][:, None]
        db = lab[..., 2] - st[:, 2, 0][:, None]
        d = float(m.get("chroma_d", 10.0))
        return ramp(np.sqrt(da * da + db * db), 0.5 * d, d)

    def _skyline(self, src, m):
        """1 below a per-column skyline found from the depth: the topmost row
        whose next `run` rows hold at least `frac` near pixels (disparity >
        `d`) and whose rows down to the bottom hold at least `bottom` of them
        (a ground that fills the frame to its bottom edge). Texture was tried
        first and spikes at cloud edges (2026-09-26). `union`: polygons (canvas
        fractions) added by hand for what the depth misses (a far tower)."""
        d = self.disparity(src)
        h, w = self.h, self.w
        near = (d > float(m.get("d", 0.03))).astype(np.float32)
        run, frac, bottom = int(m.get("run", 20)), float(m.get("frac", 0.7)), float(m.get("bottom", 0.6))
        ys = np.arange(h)
        y2 = np.minimum(ys + run, h)

        def run_fraction(score):
            csum = np.cumsum(np.vstack([np.zeros((1, w), np.float32), score]), axis=0)
            return ((csum[y2] - csum[ys]) / np.maximum(y2 - ys, 1)[:, None],
                    (csum[h] - csum[ys]) / np.maximum(h - ys, 1)[:, None])

        nxt, tob = run_fraction(near)
        ok = (nxt >= frac) & (tob >= bottom)
        if m.get("tex_sd", 0):
            # the depth model rounds a roof into a dome of "near" sky above
            # it; a roof has texture, the sky above it has none
            L = self.lab[src][..., 0]
            mu = cv2.blur(L, (15, 15))
            sd = np.sqrt(np.maximum(cv2.blur(L * L, (15, 15)) - mu * mu, 0))
            ntx, _ = run_fraction((sd > float(m["tex_sd"])).astype(np.float32))
            ok &= ntx >= float(m.get("tex_frac", 0.3))
        sky_row = np.full(w, h, np.int32)
        for x in range(w):
            idx = np.where(ok[:, x])[0]
            if len(idx):
                sky_row[x] = idx[0]
        snap = int(m.get("snap_px", 0))
        if snap:
            # the depth cut sits a few px off the roof edge: within +-snap px
            # of it, take the row of the strongest vertical L step, when that
            # step is at least `snap_min` L per px (round 2, 2026-09-26)
            # the depth cut sits ABOVE the roof (26-43 px on mismatch_6's
            # left block, measured 2026-09-26; cloud edges stay under 6 L/px
            # while roof edges are 5-17): take the TOPMOST step >= snap_min
            # from `snap_up` px above the cut down to `snap_px` px below it
            L = cv2.GaussianBlur(self.lab[src][..., 0], (0, 0), 1.0)
            g = np.abs(np.gradient(L, axis=0))
            snap_min = float(m.get("snap_min", 6.0))
            snap_up = int(m.get("snap_up", 8))
            snapped = 0
            for x in range(w):
                y0 = int(sky_row[x])
                if y0 >= h:
                    continue
                lo_, hi_ = max(1, y0 - snap_up), min(h - 1, y0 + snap + 1)
                col = g[lo_:hi_, x]
                hit = np.where(col >= snap_min)[0]
                if len(hit):
                    sky_row[x] = lo_ + int(hit[0])
                    snapped += 1
            self.masks["_snapped_" + src] = snapped
        k = int(m.get("median", 9))
        pad = np.pad(sky_row.astype(np.float32), k // 2, mode="edge")
        sk = np.median(np.lib.stride_tricks.sliding_window_view(pad, k), axis=1)
        self.masks["_skyline_" + src] = sk
        yy = np.arange(h, dtype=np.float32)[:, None]
        a = smoothstep((yy - sk[None, :] + 1.0) / float(m.get("feather", 3.0)))
        for poly in m.get("union", []):
            pts = np.array([[x * w, y * h] for x, y in poly], np.int32)
            p = np.zeros((h, w), np.uint8)
            cv2.fillPoly(p, [pts], 255)
            a = np.maximum(a, cv2.GaussianBlur(p.astype(np.float32) / 255.0, (0, 0), 2))
        return a

    def _sun(self, src, within, m, name):
        """The brightest blob inside a layer: its mask (dilated by `grow` px,
        soft) and its Gaussian moments (centroid, 2x2 covariance) for the
        closed-form transport of the move_to action."""
        L = self.lab[src][..., 0]
        hard = ((L > float(m.get("thr", 92.0))) & (within > 0.5)).astype(np.uint8)
        n, lab_, st, cen = cv2.connectedComponentsWithStats(hard)
        if n < 2:
            raise SystemExit(f"sun: no blob above L {m.get('thr', 92)} in {src}")
        i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        ys, xs = np.where(lab_ == i)
        pts = np.stack([xs, ys]).astype(np.float64)
        self.masks["_blob_" + name] = (pts.mean(1), np.cov(pts) + np.eye(2) * 1e-3, float(len(xs)))
        blob = (lab_ == i).astype(np.float32)
        k = int(m.get("grow", 12))
        a = cv2.dilate(blob, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1)))
        return cv2.GaussianBlur(a, (0, 0), max(1.0, k / 2.0))

    def _band_dark(self, src, m, name):
        """The dark silhouette band under the sky: per column, from the first
        near row (disparity > sky_d) down through the contiguous run of dark
        rows (L < dark_L; gaps up to `gap` rows bridged). Stores the per-column
        top and bottom rows for below_band / above_band."""
        d = self.disparity(src)
        L = self.lab[src][..., 0]
        h, w = self.h, self.w
        near = d > float(m.get("sky_d", 0.02))
        dark = L < float(m.get("dark_L", 10.0))
        gap = int(m.get("gap", 20))
        top = np.zeros(w, np.float32)
        bottom = np.zeros(w, np.float32)
        for x in range(w):
            idx = np.where(near[:, x])[0]
            t0 = int(idx[0]) if len(idx) else h - 1
            y, last = t0, t0
            while y < h:
                if dark[y, x]:
                    last = y
                elif y - last > gap:
                    break
                y += 1
            top[x], bottom[x] = t0, last
        if m.get("max_bottom"):
            # the dark run continues into a dark water reflection: cap the
            # band's bottom at a row fraction (round 2 on mismatch_4)
            bottom = np.minimum(bottom, float(m["max_bottom"]) * h)
        k = int(m.get("median", 9))
        for arr in (top, bottom):
            pad = np.pad(arr, k // 2, mode="edge")
            arr[:] = np.median(np.lib.stride_tricks.sliding_window_view(pad, k), axis=1)
        if m.get("bottom_fit") is not None:
            # round 4: a waterline is a smooth line; the per-column dark run
            # ends early under a bright reflection and the notch let the water
            # layer cover a block of the skyline (the light blocks of rounds
            # 2-4). A polynomial of order `bottom_fit` through the columns
            # within 12 px of the running fit (three passes from the median).
            xs_ = np.arange(w, dtype=np.float64)
            fit = np.full(w, float(np.median(bottom)))
            for _ in range(3):
                ok = np.abs(bottom - fit) < 12.0
                if ok.sum() < 10:
                    break
                fit = np.polyval(np.polyfit(xs_[ok], bottom[ok].astype(np.float64), int(m["bottom_fit"])), xs_)
            bottom[:] = fit.astype(np.float32)
        self.masks["_band_" + name] = (top, bottom)
        yy = np.arange(h, dtype=np.float32)[:, None]
        f = float(m.get("feather", 3.0))
        # round 4: `extend_bottom_px` continues the matte below its bottom
        # line (the band lines stay): a band that transforms behind a water
        # layer never shows a gap between its bottom and the moving waterline
        low = bottom + float(m.get("extend_bottom_px", 0.0))
        return smoothstep((yy - top[None, :] + 1.0) / f) * smoothstep((low[None, :] - yy + 1.0) / f)

    def _clouds(self, src, within, m):
        """Cloud density against the clear sky of the same rows: the clear sky
        is a low percentile of the channel over a window of rows (so a row
        full of cloud still finds the clear sky beside it); a cloud is where
        the channel rises toward the cloud value. channel "b": b* rises from
        blue toward b_cloud (a day sky); channel "L": L rises by `delta` (a
        sunset). Density 0..1; the matte is opaque above `opaque`."""
        lab = self.lab[src]
        chan = m.get("channel", "b")
        if chan == "L_hp":
            # round 3 (2026-09-27): a high-pass of L at `hp_px` — thin bright
            # streaks stand out, a smooth glow cancels (the L-density rule took
            # the sunset glow for cloud on mismatch_4; measured on B's sky:
            # 99th percentile of the 40-px high-pass 16.4 L, median -0.2).
            # `hp_sign` -1 takes the dark clouds instead.
            L = lab[..., 0]
            hp = (L - cv2.GaussianBlur(L, (0, 0), float(m.get("hp_px", 40)))) * float(m.get("hp_sign", 1))
            # `hp_floor`: the noise floor of the high-pass (without it 74 % of
            # B's sky counted as cloud at an opaque threshold of 0.02)
            dens = np.clip((hp - float(m.get("hp_floor", 4.0))) / float(m.get("delta", 12.0)), 0, 1)
            dens = cv2.GaussianBlur(dens.astype(np.float32), (0, 0), m.get("blur", 2.0)) * within
            self.masks["_density_" + m["within"]] = dens
            return np.clip(dens / float(m.get("opaque", 0.35)), 0, 1)
        v = lab[..., 2] if chan == "b" else lab[..., 0]
        h = self.h
        half = int(m.get("window", 100))
        step = 16
        clear = np.full(h, np.nan, np.float32)
        for r in range(0, h, step):
            sl = slice(max(0, r - half), min(h, r + half))
            sel = within[sl] > 0.5
            if sel.sum() > 500:
                clear[r:r + step] = np.percentile(v[sl][sel], m.get("clear_pct", 5))
        rows = np.arange(h, dtype=np.float32)
        ok = ~np.isnan(clear)
        v_clear = np.interp(rows, rows[ok], clear[ok]).astype(np.float32)
        v_clear = cv2.GaussianBlur(v_clear.reshape(-1, 1), (0, 0), 40).ravel()
        if chan == "b":
            span = np.maximum(float(m.get("b_cloud", -4.0)) - v_clear[:, None], 1.0)
        else:
            span = float(m.get("delta", 25.0))
        dens = np.clip((v - v_clear[:, None]) / span, 0, 1)
        dens = cv2.GaussianBlur(dens.astype(np.float32), (0, 0), m.get("blur", 2.0)) * within
        self.masks["_density_" + m["within"]] = dens
        return np.clip(dens / float(m.get("opaque", 0.35)), 0, 1)

    def _stars(self, src, within, m):
        """Bright small blobs inside the sky: white top-hat on L, thresholded,
        each blob given an appearance order (bright first, with jitter)."""
        L = self.lab[src][..., 0]
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        th = cv2.morphologyEx(L, cv2.MORPH_TOPHAT, k) * (within > 0.5)
        hard = (th > float(m.get("tophat", 8.0))).astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(hard)
        max_area = int(m.get("max_area", 80))
        peaks = []
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] > max_area:
                hard[lab == i] = 0
            else:
                peaks.append((i, float(th[lab == i].max())))
        rng = np.random.default_rng(self.seed + 7)
        order = np.zeros(n, np.float32)
        if peaks:
            idx = np.array([p[0] for p in peaks])
            val = np.array([p[1] for p in peaks])
            rank = np.argsort(np.argsort(-val)) / max(1, len(val) - 1)
            jit = float(m.get("jitter", 0.4))
            order[idx] = np.clip((1 - jit) * rank + jit * rng.random(len(val)), 0, 1)
        self.masks["_order_" + src] = order[lab].astype(np.float32)
        a = cv2.dilate(hard, np.ones((3, 3), np.uint8)).astype(np.float32)
        a = cv2.GaussianBlur(a, (0, 0), 0.8)
        self.masks["_hard_" + src] = hard
        return np.clip(a, 0, 1)


# ---------------------------------------------------------------------------
# Layers and actions
# ---------------------------------------------------------------------------

class Layer:
    def __init__(self, scene, spec, by_name):
        self.scene, self.spec = scene, spec
        self.name = spec["name"]
        self.src = spec["from"]
        self.img = scene.A if self.src == "A" else scene.B
        self.rgb = self.img.astype(np.float32)
        self.lab = scene.lab[self.src]
        self.alpha0 = scene.mask(spec)
        self.depth = spec.get("depth", 0)
        self.action = spec.get("action", "hold")
        self.window = spec.get("window", [0.0, 1.0])
        self.curve = spec.get("curve", "ease")
        self.render_it = spec.get("render", True)
        self.by_name = by_name
        h, w = scene.h, scene.w
        ys, xs = np.where(self.alpha0 > 0.05)
        self.bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1) if len(xs) else (0, 0, w, h)
        self.stats = row_stats(self.lab, self.alpha0)
        # _prep runs from build_layers once every layer's mask exists

    def progress(self, t):
        # clip BEFORE the curve: the cosine ease is not monotone outside 0..1
        t0, t1 = self.window
        u = min(1.0, max(0.0, (t - t0) / max(t1 - t0, 1e-6)))
        return curve_of(self.curve, u)

    def _prep(self):
        s, sp = self.scene, self.spec
        h, w = s.h, s.w
        if self.action in ("dissolve", "materialise"):
            # the order in which the layer's pixels go (dissolve) or come
            # (materialise): its own density (clouds), its blobs (stars), its
            # luma, or noise alone (any textured layer)
            order = sp.get("order", "density" if ("_density_" + sp["mask"].get("within", "")) in s.masks
                           else ("blobs" if ("_order_" + self.src) in s.masks and sp["mask"]["rule"] == "stars"
                                 else "noise"))
            n = noise_field(h, w, sp.get("noise_px", 40), s.seed + 1)
            if order == "density":
                base = s.masks["_density_" + sp["mask"]["within"]]
            elif order == "luma":
                base = self.lab[..., 0] / 100.0
            elif order == "luma_rev":
                base = 1.0 - self.lab[..., 0] / 100.0
            elif order in ("rows", "rows_rev"):
                # row position within the layer's box: a band sinks from its
                # top (rows) or rises from its bottom (rows_rev). One box for
                # the whole layer: a per-column extent made adjacent columns
                # vanish at different rates and read as vertical streaks
                yy = np.arange(h, dtype=np.float32)[:, None]
                y1, y2 = self.bbox[1], self.bbox[3]
                base = np.clip((yy - y1) / max(y2 - y1, 1.0), 0, 1) * np.ones((1, w), np.float32)
                if order == "rows":
                    base = 1.0 - base          # the top goes first when dissolving
            elif order == "blobs":
                base = None
            elif order == "edge":
                # round 3 (2026-09-27): the erosion runs from each cloud's edge
                # inward along the distance transform of its support, so the
                # front is the cloud's own outline receding, not a threshold
                # on density plus noise (which cuts noise-shaped holes; the
                # owner: "a very raw and naive luma manner"). `edge_norm`
                # global: one scale for all clouds, so the small ones go first;
                # blob: each cloud on its own scale, all gone together.
                mode = sp.get("edge_norm", "px")
                dens = s.masks.get("_density_" + sp["mask"].get("within", ""))
                self.dn = np.clip(dens, 0, 1).astype(np.float32) if dens is not None else np.ones((h, w), np.float32)
                tp = float(sp.get("turb_px", 24))
                n1 = noise_field(h, w, tp, s.seed + 3)
                n2 = noise_field(h, w, 3.0 * tp, s.seed + 4)
                if mode == "px":
                    # px mode (the physical one; 2026-09-27): the front eats
                    # inward at one speed from every edge of the dense part
                    # (density above `edge_thr`; the fringe outside it goes
                    # first, and a thin spot inside a cloud opens up as a hole),
                    # faster through thin parts (`speed_density`), with a
                    # `front_soft_px`-wide band and a front displaced by two
                    # octaves of noise (`turb_px_amp` px at `turb_px` and 3 x
                    # `turb_px`). Small clouds go early, the big core last.
                    # The normalized modes below washed every cloud at once
                    # (semi-transparent share 0.42 at a quarter of the window
                    # with a 90-px band; measured 2026-09-27).
                    thr = float(sp.get("edge_thr", 0.15))
                    sup8 = ((self.alpha0 > 0.5) & (self.dn > thr)).astype(np.uint8)
                    D = cv2.distanceTransform(sup8, cv2.DIST_L2, 5)
                    sd = float(sp.get("speed_density", 0.6))
                    if sd > 0:
                        dl = cv2.GaussianBlur(self.dn, (0, 0), 30.0)
                        dl = dl / max(float(dl.max()), 1e-6)
                        D = D * ((1.0 - sd) + sd * dl)
                    amp = float(sp.get("turb_px_amp", 12.0))
                    self.r_edge = (D + amp * (n1 - 0.5) + 0.5 * amp * (n2 - 0.5)).astype(np.float32)
                    self.front_soft = float(sp.get("front_soft_px", 30.0))
                    # a second, wide ramp ahead of the cut: the cloud thins
                    # over `front_wide_px` before its edge goes (an evaporating
                    # shell), down to (1 - wide_gain) at the cut itself; with
                    # a 10-px band and 20 px of turbulence alone the front was
                    # a field of round holes (measured on the frames 2026-09-27)
                    self.front_wide = float(sp.get("front_wide_px", 90.0))
                    self.wide_gain = float(sp.get("wide_gain", 0.5))
                    self.turb_max = 0.75 * amp
                    self.d_max = max(float(D.max()), 1.0)
                else:
                    sup8 = (self.alpha0 > 0.5).astype(np.uint8)
                    D = cv2.distanceTransform(sup8, cv2.DIST_L2, 5)
                    if mode == "blob":
                        n_, lab_ = cv2.connectedComponents(sup8)
                        mx = np.zeros(n_, np.float32)
                        np.maximum.at(mx, lab_.ravel(), D.ravel())
                        r = D / np.maximum(mx[lab_], 1.0)
                    else:
                        r = D / max(float(D.max()), 1.0)
                    ta = float(sp.get("turb", 0.3))
                    self.r_edge = (r + ta * (n1 - 0.5) + 0.5 * ta * (n2 - 0.5)).astype(np.float32)
                    self.front_soft = float(sp.get("front_soft", 0.35))
                    self.front_wide, self.wide_gain = 0.0, 0.0
                    self.turb_max = 0.75 * ta
                    self.d_max = 1.0
                self.thin = float(sp.get("thin", 0.0))
                self.edge_mode = mode
                self.d_max_px = round(float(D.max()), 1)
                base = None
            else:
                base = np.zeros((h, w), np.float32)
            self.order_kind = order
            if base is not None:
                E = base + float(sp.get("noise_gain", 0.35)) * (n - 0.5)
                sup = self.alpha0 > 0.05
                lo = float(E[sup].min()) if sup.any() else 0.0
                hi = float(E[sup].max()) if sup.any() else 1.0
                self.E = ((E - lo) / max(hi - lo, 1e-6)).astype(np.float32)   # 0..1 on the support
                self.feather = float(sp.get("feather", 0.12))
            elif order == "blobs":
                self.order = s.masks["_order_" + self.src]
                self.each = float(sp.get("each", 0.12))
        if self.action == "move_to":
            # closed-form optimal transport between two Gaussians (the
            # Bures-Wasserstein map): x -> T x + b, interpolated as
            # ((1 - p) I + p T) x + p b (McCann); Track E §2.4
            ms, Ss, _ = s.masks["_blob_" + self.name]
            mt, St, _ = s.masks["_blob_" + sp["to"]]
            ev, U = np.linalg.eigh(Ss)
            Ss_h = U @ np.diag(np.sqrt(np.maximum(ev, 1e-9))) @ U.T
            Ss_ih = U @ np.diag(1.0 / np.sqrt(np.maximum(ev, 1e-9))) @ U.T
            mid = Ss_h @ St @ Ss_h
            ev2, U2 = np.linalg.eigh(mid)
            mid_h = U2 @ np.diag(np.sqrt(np.maximum(ev2, 1e-9))) @ U2.T
            self.T_bw = Ss_ih @ mid_h @ Ss_ih
            self.b_bw = mt - self.T_bw @ ms
        if self.action in ("exit", "enter", "move"):
            d = np.array(sp.get("direction", [0, 1]), np.float32)
            d = d / max(np.linalg.norm(d), 1e-6)
            x1, y1, x2, y2 = self.bbox
            # the distance the layer's box travels along v until it is off the
            # canvas: v = the exit direction, or the reverse of the entry direction
            v = -d if self.action == "enter" else d
            tx = (w - x1) / v[0] if v[0] > 0 else (x2 / -v[0] if v[0] < 0 else np.inf)
            ty = (h - y1) / v[1] if v[1] > 0 else (y2 / -v[1] if v[1] < 0 else np.inf)
            travel = float(sp.get("travel_px", min(tx, ty) + 8))
            self.dir, self.travel = d, travel
        # round 3: a moving layer that carries sky between its leaves shows the
        # sky of its source rows at its destination rows; `carry_fit` names
        # the backdrop whose fit relights the carried pixels (fit at the
        # destination minus fit at the source, in Lab; zero at the endpoints)
        self.carry = self.by_name[sp["carry_fit"]] if sp.get("carry_fit") else None
        self.shutter = float(sp.get("shutter", 0.0))
        adv = sp.get("advect")
        self.adv = None
        if adv:
            self.adv = curl_field(h, w, float(adv.get("scale_px", 160)), s.seed + int(adv.get("seed", 11))) * float(adv.get("amp_px", 40))
        if self.action == "morph_to":
            # round 4: the layer of A is carried into the layer `to` of B
            tgt = self.by_name[sp["to"]]
            self.tgt = tgt
            kind = sp.get("ot_mass", "alpha")

            def mass(lay):
                if kind == "alpha":
                    return lay.alpha0
                L = lay.lab[..., 0]
                mu = float((L * lay.alpha0).sum() / max(float(lay.alpha0.sum()), 1e-6))
                dev = (L - mu) if kind == "bright" else (mu - L)
                return lay.alpha0 * (0.15 + np.clip(dev, 0, None) / 25.0)
            self.F, self.G, self.ot_info = ot_fields(mass(self), mass(tgt), int(sp.get("ot_grid", 64)),
                                                     float(sp.get("ot_eps", 0.04)))
            gain = float(sp.get("ot_gain", 1.0))
            self.F, self.G = self.F * gain, self.G * gain
            self.mix_window = sp.get("mix_window", [0.3, 0.7])
            # `colour_window` (CLIP time, like `recolor_window`): the window in
            # which the two layers' shared Lab statistics go from A's to B's;
            # by default the mix window mapped into clip time. An earlier one
            # lets a day-lit layer darken with the sky before its structure
            # changes (day-lit buildings stood under a night sky otherwise).
            t0_, t1_ = self.window
            self.colour_window = sp.get("colour_window", [t0_ + (t1_ - t0_) * self.mix_window[0], t0_ + (t1_ - t0_) * self.mix_window[1]])
            self.st_a = lab_stats(self.lab, self.alpha0)
            self.st_b = lab_stats(tgt.lab, tgt.alpha0)
            self.match = bool(sp.get("match_colour", True))

    def linear(self, t, window=None):
        """The clipped linear progress through a window (the layer's own by default)."""
        t0, t1 = window or self.window
        return min(1.0, max(0.0, (t - t0) / max(t1 - t0, 1e-6)))

    def offset(self, t):
        """The translation (px) of the layer at t: exit / enter / move, the
        drift, and the centroid transport of move_to."""
        sp = self.spec
        off = np.zeros(2, np.float32)
        p = self.progress(t)
        if self.action == "exit":
            off = self.dir * self.travel * p
        elif self.action == "enter":
            off = -self.dir * self.travel * (1.0 - p)
        elif self.action == "move":
            off = self.dir * float(sp.get("travel_px", 0)) * p
        elif self.action == "move_to":
            ms = self.scene.masks["_blob_" + self.name][0]
            pos = ((1 - p) * np.eye(2) + p * self.T_bw) @ ms + p * self.b_bw
            off = off + (pos - ms).astype(np.float32)
        drift = sp.get("drift")
        if drift:
            off = off + np.array([drift[0] * self.scene.w, drift[1] * self.scene.h], np.float32) * p
        return off

    def velocity(self, t):
        """px per frame at t (a central difference over one frame each side)."""
        dt = 1.0 / max(self.scene.n - 1, 1)
        t0, t1 = max(0.0, t - dt), min(1.0, t + dt)
        if t1 - t0 <= 0:
            return np.zeros(2, np.float32)
        return (self.offset(t1) - self.offset(t0)) / ((t1 - t0) / dt)

    def render_morph(self, t):
        """The layer of A carried into its counterpart of B: geometry by the
        progress p along the transport field, appearance by the mix q inside
        `mix_window`, with both layers given the same Lab statistics (the
        blend of A's and B's by q), so the mix changes structure, not colour."""
        tgt = self.tgt
        u = self.linear(t)
        p = curve_of(self.curve, u)
        m0, m1 = self.mix_window
        q = float(smoothstep((u - m0) / max(m1 - m0, 1e-6)))
        qc = float(smoothstep(self.linear(t, self.colour_window))) if self.match else q
        st = (1.0 - qc) * self.st_a + qc * self.st_b
        if u <= 0:
            return (self.rgb if qc <= 0 else lab_to_rgb(lab_match(self.lab, self.st_a, st))), self.alpha0
        if u >= 1:
            return (tgt.rgb if qc >= 1 else lab_to_rgb(lab_match(tgt.lab, self.st_b, st))), tgt.alpha0
        if self.match:
            rgb_a = lab_to_rgb(lab_match(self.lab, self.st_a, st)) if qc > 0 else self.rgb
            rgb_b = lab_to_rgb(lab_match(tgt.lab, self.st_b, st)) if qc < 1 else tgt.rgb
        else:
            rgb_a, rgb_b = self.rgb, tgt.rgb
        a_a = warp_along(self.alpha0, self.F, p)
        a_b = warp_along(tgt.alpha0, self.G, 1.0 - p)
        c_a = warp_along(np.ascontiguousarray(rgb_a), self.F, p, cv2.BORDER_REPLICATE)
        c_b = warp_along(np.ascontiguousarray(rgb_b), self.G, 1.0 - p, cv2.BORDER_REPLICATE)
        # the two warped shapes only approximate one shape: in the middle of
        # the mix the matte is their union (a plain (1 - q) a + q b leaves the
        # layer half transparent wherever they do not overlap: holes in a
        # skyline, measured on the first render of 2026-09-27), and a pixel
        # that only one of them covers takes that one's colour
        c = 4.0 * q * (1.0 - q)
        lin = a_a * (1.0 - q) + a_b * q
        alpha = lin + c * (np.maximum(a_a, a_b) - lin)
        w_a = a_a * ((1.0 - q) + 0.5 * c)
        w_b = a_b * (q + 0.5 * c)
        rgb = (c_a * w_a[..., None] + c_b * w_b[..., None]) / np.maximum(w_a + w_b, 1e-4)[..., None]
        return rgb, np.clip(alpha, 0, 1)

    def edge_alpha(self, p):
        """The matte of an order-`edge` dissolve at progress p: the front f
        runs from below the support's edge (every pixel opaque at p = 0) to
        beyond its deepest point (nothing left at p = 1); the thin parts lose
        opacity with `thin` x p on top."""
        f0 = -(max(self.front_soft, self.front_wide) + self.turb_max)
        f1 = self.d_max + self.turb_max
        f = f0 + (f1 - f0) * p
        a = self.alpha0 * smoothstep((self.r_edge - f) / self.front_soft)
        if self.front_wide > 0:
            a = a * ((1.0 - self.wide_gain) + self.wide_gain * smoothstep((self.r_edge - f) / self.front_wide))
        if self.thin > 0:
            a = a * (1.0 - self.thin * p * (1.0 - self.dn))
        return a

    def colour(self, t):
        """The layer's RGB at time t after its colour path (float32)."""
        sp = self.spec
        to = sp.get("recolor_to") or (sp.get("to") if self.action == "recolor" else None)
        if not to:
            return self.rgb
        rw = sp.get("recolor_window")
        p = (curve_of(self.curve, self.linear(t, rw)) if rw else self.progress(t)) * float(sp.get("recolor_strength", 1.0))
        if p <= 0:
            return self.rgb
        dst = self.by_name[to].stats
        if sp.get("recolor_mode") == "L":
            # luminance only: a* and b* keep the layer's own statistics
            dst = dst.copy()
            dst[:, 1:, :] = self.stats[:, 1:, :]
        return lab_to_rgb(row_transfer(self.lab, self.stats, dst, p))

    def affine(self, t):
        """The 2x3 matrix of the layer's motion at t, or None."""
        sp = self.spec
        off = np.zeros(2, np.float32)
        if self.action in ("exit", "enter", "move"):
            p = self.progress(t)
            if self.action == "exit":
                off = self.dir * self.travel * p
            elif self.action == "enter":
                off = -self.dir * self.travel * (1.0 - p)
            else:
                off = self.dir * float(sp.get("travel_px", 0)) * p
        drift = sp.get("drift")
        if drift:
            p = self.progress(t)
            off = off + np.array([drift[0] * self.scene.w, drift[1] * self.scene.h], np.float32) * p
        z = sp.get("zoom")
        scale = 1.0
        if z:
            scale = z[0] + (z[1] - z[0]) * self.progress(t)   # inside the window, like the drift
        if self.action == "move_to":
            p = self.progress(t)
            Tm = (1 - p) * np.eye(2) + p * self.T_bw
            return np.array([[Tm[0, 0], Tm[0, 1], p * self.b_bw[0] + off[0]],
                             [Tm[1, 0], Tm[1, 1], p * self.b_bw[1] + off[1]]], np.float32)
        if scale == 1.0 and not off.any():
            return None
        cx, cy = self.scene.w / 2.0, self.scene.h / 2.0
        return np.array([[scale, 0, cx - scale * cx + off[0]],
                         [0, scale, cy - scale * cy + off[1]]], np.float32)

    def render(self, t):
        """(rgb float32, alpha float32) of this layer at time t."""
        sp = self.spec
        if self.action == "morph_to":
            return self.render_morph(t)
        rgb = self.colour(t)
        p = self.progress(t)
        if self.action == "dissolve":
            if self.order_kind == "edge":
                alpha = self.edge_alpha(p)
            else:
                # the threshold rises from below the support's lowest order value
                # to its highest: at p = 0 the whole matte, at p = 1 nothing
                theta = -self.feather + (1.0 + self.feather) * p
                alpha = self.alpha0 * np.clip((self.E - theta) / self.feather, 0, 1)
        elif self.action == "materialise":
            if self.order_kind == "blobs":
                alpha = self.alpha0 * np.clip((p - self.order) / self.each, 0, 1)
            elif self.order_kind == "edge":
                alpha = self.edge_alpha(1.0 - p)      # the reverse: the cloud condenses from its core outward
            else:
                # the reverse of dissolve: the highest order value comes first
                theta = (1.0 + self.feather) * (1.0 - p) - self.feather
                alpha = self.alpha0 * np.clip((self.E - theta) / self.feather, 0, 1)
        else:
            alpha = self.alpha0
        if self.adv is not None and p > 0:
            # the layer deforms along a divergence-free field that grows with
            # its progress (a cloud's body drifts and twists while it thins)
            rgb = warp_along(np.ascontiguousarray(rgb), self.adv, p, cv2.BORDER_REPLICATE)
            alpha = warp_along(alpha, self.adv, p)
        M = self.affine(t)
        if M is not None:
            h, w = self.scene.h, self.scene.w
            if self.carry is not None:
                off = self.offset(t)
                if abs(float(off[0])) + abs(float(off[1])) > 0.01:
                    fit = self.carry.fitA_img if self.src == "A" else self.carry.fitB_img
                    Mf = np.array([[1, 0, -off[0]], [0, 1, -off[1]]], np.float32)
                    fit_dest = cv2.warpAffine(np.ascontiguousarray(fit), Mf, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                    rgb = lab_to_rgb(self.lab + (fit_dest - fit))
            rgb = cv2.warpAffine(rgb, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            alpha = cv2.warpAffine(alpha, M, (w, h), flags=cv2.INTER_LINEAR,
                                   borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            if self.shutter > 0:
                # motion blur along the travel: the pixels and the matte both,
                # by shutter x the per-frame displacement (0 at rest, so the
                # endpoint frames stay exact)
                v = self.velocity(t)
                length = self.shutter * float(np.linalg.norm(v))
                if length >= 1.0:
                    kern = line_kernel(v / max(float(np.linalg.norm(v)), 1e-6), length)
                    rgb = cv2.filter2D(rgb, -1, kern, borderType=cv2.BORDER_REPLICATE)
                    alpha = cv2.filter2D(alpha, -1, kern, borderType=cv2.BORDER_CONSTANT)
        return rgb, alpha


class Backdrop(Layer):
    """The sky gradient: a low-order per-row fit of A's clear sky moves to B's,
    while the residual textures (A's clear-sky pixels minus the fit, B's minus
    its fit) crossfade. Alpha 1 everywhere: the layers vacate onto it."""

    def _prep(self):
        s, sp = self.scene, self.spec
        other = self.by_name[sp["to"]]
        # the residual lives only where the sky is certain (the interior of the
        # matte) and clear (not under a layer named in `minus` / `exclude`):
        # a half-weighted residual at a layer edge is a ghost that stays behind
        # when the layer moves
        # a layer drawn over the backdrop removes only its INTERIOR from the
        # residual: at its soft edge the layer's pixel composites over the
        # photo's own residual, so the endpoint frames stay exact there
        # an entry given as {"layer": name, "full": true, "dilate": k, "soft": s}
        # removes the layer's FULL alpha (dilated, softened) from the fit and
        # the residual: the fit fills under it, so nothing of the layer's
        # fringe stays behind when it erodes or moves (round 2, 2026-09-26)
        def clear_of(entries):
            c = np.ones_like(self.alpha0)
            for e in ([entries] if isinstance(entries, str) else entries):
                if isinstance(e, str):
                    c = c * (1.0 - ramp(s.masks[e], 0.9, 1.0))
                    continue
                a = (s.masks[e["layer"]] > float(e.get("thr", 0.02))).astype(np.float32)
                k = int(e.get("dilate", 0))
                if k:
                    a = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1)))
                if e.get("soft", 0):
                    a = cv2.GaussianBlur(a, (0, 0), float(e["soft"]))
                c = c * (1.0 - a)
            return c
        clearA = clear_of(sp.get("minus", []))
        clearB = clear_of(sp.get("exclude") or [])
        # `minus_res` / `exclude_res`: removed from the RESIDUAL only, so the
        # fit still counts the sky seen between the leaves of a wide region
        # (a fit that misses the bottom rows misses the horizon glow, and a
        # hole filled from a wrong fit is a dark dome; round 2, 2026-09-26)
        clearA_res = clearA * clear_of(sp.get("minus_res", []))
        clearB_res = clearB * clear_of(sp.get("exclude_res", []))
        # the region: the base backdrop covers the canvas; a partial one (the
        # water) moves from its A mask to its B mask over the window
        self.alpha_to = s.masks[sp["mask_to"]] if sp.get("mask_to") else None
        self.opaque = bool(sp.get("opaque", self.depth == 0))
        # slide_between: [bandA, bandB] — the backdrop's top edge is the
        # per-column bottom line of bandA moving to bandB's over the window
        # (a waterline that drops), instead of a blend of the two masks,
        # which fades the strip between them (round 2, 2026-09-26)
        self.slide = None
        sl = sp.get("slide_between")
        if sl:
            self.slide = (s.masks["_band_" + sl[0]][1], s.masks["_band_" + sl[1]][1], float(sp.get("slide_feather", 3.0)))
        # the FIT counts every sky pixel, including the sky seen between the
        # leaves of a foreground layer (its soft alpha), so the gradient under
        # that layer follows the photo; the RESIDUAL is interior-only
        self.fitA = row_stats(self.lab, self.alpha0 * clearA, min_px=300)
        self.fitB = row_stats(other.lab, other.alpha0 * clearB, min_px=300)
        self.stats = self.fitA
        # fit2d: the fit is a per-band quadratic in x (a lateral glow is part
        # of the fit, not of the residual); the row stats stay for the colour path
        self.fit2d = bool(sp.get("fit2d", False))
        if self.fit2d:
            self.fitA_img = sky_fit2d(self.lab, self.alpha0 * clearA)
            self.fitB_img = sky_fit2d(other.lab, other.alpha0 * clearB)
        else:
            self.fitA_img = np.broadcast_to(self.fitA[:, None, :, 0], self.lab.shape)
            self.fitB_img = np.broadcast_to(self.fitB[:, None, :, 0], self.lab.shape)
        # fit_under: the rows below the per-column skyline of A (no sky pixel
        # of A exists there) take B's fit from the start, so the band vacated
        # by an exiting skyline layer is never an extrapolated day sky
        self.under = None
        fu = sp.get("fit_under")
        if fu:
            sk = s.masks["_skyline_" + fu.get("skyline", "A")]
            yy = np.arange(s.h, dtype=np.float32)[:, None]
            self.under = smoothstep((yy - sk[None, :] + float(fu.get("offset", 0.0))) / float(fu.get("feather", 24.0)))
        wA = ramp(self.alpha0, 0.9, 1.0) * clearA_res
        wB = ramp(other.alpha0, 0.9, 1.0) * clearB_res
        fs = float(sp.get("fill_sigma", 0.0))
        if sp.get("fill_mode") == "poly2":
            self.resA = fill_poly2(self.lab - self.fitA_img, wA)
            self.resB = fill_poly2(other.lab - self.fitB_img, wB)
        elif fs > 0:
            # the holes in each residual (under an excluded layer, under the
            # layer's own soft edge) take the surrounding low-frequency
            # residual instead of the row fit alone
            self.resA = fill_holes(self.lab - self.fitA_img, wA, fs)
            self.resB = fill_holes(other.lab - self.fitB_img, wB, fs)
        else:
            self.resA = (self.lab - self.fitA_img) * wA[..., None]
            self.resB = (other.lab - self.fitB_img) * wB[..., None]
        # round 4: `flow` moves the two residual textures along a transport
        # map between their bright (or dark) features while they mix, so a
        # texture travels to its counterpart instead of fading in place
        self.flow = None
        fl = sp.get("flow")
        if fl and fl.get("from") == "layers":
            # the scene's one flow, from the matched layers' own motions; the
            # fields are read at the first render (every layer is prepared by then)
            self.flow = ("layers", float(fl.get("sigma", 0.12)), float(fl.get("kappa", 0.02)), fl.get("mix_window", [0.25, 0.75]),
                         float(fl.get("gain", 1.0)), fl.get("layers"))
        elif fl:
            # a free transport between the two textures' bright (or dark)
            # features. Measured 2026-09-27 on mismatch_4: mean 200 px, max
            # 715 px, curtain-shaped smears in the sky; kept as an option.
            sign = -1.0 if fl.get("mass", "bright") == "dark" else 1.0
            floor = float(fl.get("floor", 2.0))
            reg_a = self.alpha0 if self.alpha_to is None else self.alpha0
            reg_b = other.alpha0
            ma = np.clip(sign * self.resA[..., 0] - floor, 0, None) * reg_a * wA
            mb = np.clip(sign * self.resB[..., 0] - floor, 0, None) * reg_b * wB
            F, G, info = ot_fields(ma, mb, int(fl.get("grid", 64)), float(fl.get("eps", 0.05)))
            gain = float(fl.get("gain", 1.0))
            self.flow = (F * gain, G * gain, fl.get("mix_window", [0.25, 0.75]), info)

    def render(self, t):
        p = self.progress(t)
        fA, fB = self.fitA_img, self.fitB_img
        if self.under is not None:
            u = self.under[..., None]
            fA = fA * (1 - u) + fB * u
        fit = fA * (1 - p) + fB * p
        if self.flow is not None and 0 < p < 1:
            if self.flow[0] == "layers":
                _, sg, kp, mw, gain, names = self.flow
                F, G = self.scene.layer_flow(sg, kp, names)
                F, G = F * gain, G * gain
            else:
                F, G, mw, _ = self.flow
            uu = self.linear(t)
            q = float(smoothstep((uu - mw[0]) / max(mw[1] - mw[0], 1e-6)))
            ra = warp_along(np.ascontiguousarray(self.resA), F, p, cv2.BORDER_REFLECT_101)
            rb = warp_along(np.ascontiguousarray(self.resB), G, 1.0 - p, cv2.BORDER_REFLECT_101)
            lab = fit + ra * (1 - q) + rb * q
        else:
            lab = fit + self.resA * (1 - p) + self.resB * p
        if self.opaque:
            alpha = np.ones((self.scene.h, self.scene.w), np.float32)
        elif self.slide is not None:
            la, lb, f = self.slide
            line = la * (1 - p) + lb * p
            yy = np.arange(self.scene.h, dtype=np.float32)[:, None]
            alpha = smoothstep((yy - line[None, :]) / f)
        elif self.alpha_to is not None:
            alpha = self.alpha0 * (1 - p) + self.alpha_to * p
        else:
            alpha = self.alpha0
        return lab_to_rgb(lab), alpha


def build_layers(scene, score):
    by_name = {}
    layers = []
    for sp in score["layers"]:
        cls = Backdrop if sp.get("action") == "backdrop" else Layer
        lay = cls(scene, sp, by_name)
        by_name[lay.name] = lay
        layers.append(lay)
    scene.layers_all = layers
    for lay in layers:          # masks first, then the actions that read other masks
        lay._prep()
    return sorted([l for l in layers if l.render_it], key=lambda l: l.depth)


def composite(layers, t):
    out = None
    for lay in layers:
        rgb, alpha = lay.render(t)
        if out is None:
            out = rgb * alpha[..., None]
            continue
        a = alpha[..., None]
        out = out * (1 - a) + rgb * a
    return T.to_u8(out)


# ---------------------------------------------------------------------------
# The automatic score (round 4, 2026-09-27 evening): fixed rules, no per-pair
# parameter. The owner: "not overfit on these specific example pairs ... i want
# this to be universal solution (tunable and adjustable)". The hand-written
# scores tune a pair; this one is what the same mechanisms give unattended,
# and the score it writes is the file an operator then edits.
# ---------------------------------------------------------------------------

AUTO_SKYLINE = {"rule": "skyline_below", "d": 0.03, "run": 20, "frac": 0.7, "bottom": 0.6, "grow": 2}


def auto_score(pair, seconds=3.0, fps=30, max_long=1920, seed=0):
    """A score for any pair from fixed rules. Both photos have a sky (the
    depth skyline leaves 5-90 % of the canvas below it): the ground of A
    transforms into the ground of B over a sky backdrop whose textures follow
    the scene's flow, and a sun moves to a sun when both skies hold one.
    Otherwise: the whole frame of A transforms into the whole frame of B
    (transport between bright features) under a near layer cut at each
    photo's median disparity, which transforms into B's near layer."""
    A, B = canvas_pair(pair, max_long)
    sc = Scene(A, B, seed)
    h, w = sc.h, sc.w
    ga = sc.mask({"name": "_ga", "from": "A", "mask": dict(AUTO_SKYLINE)})
    gb = sc.mask({"name": "_gb", "from": "B", "mask": dict(AUTO_SKYLINE)})
    share = (float(ga.mean()), float(gb.mean()))
    facts = {"ground_share": [round(v, 3) for v in share]}

    def sun_of(src, ground):
        L = sc.lab[src][..., 0]
        hard = ((L > 92.0) & (ground < 0.5)).astype(np.uint8)
        n, _, st, _ = cv2.connectedComponentsWithStats(hard)
        if n < 2:
            return 0.0
        return float(st[1:, cv2.CC_STAT_AREA].max()) / (h * w)

    base = {"pair": pair, "tag": "auto_r4", "seconds": seconds, "fps": fps, "max_long": max_long,
            "owner": "Automatic score (fixed rules, no per-pair parameter; layered_probe.py --auto): edit this file to tune the scene."}
    if all(0.05 < v < 0.9 for v in share):
        suns = (sun_of("A", ga), sun_of("B", gb))
        facts["sun_share"] = [round(v, 5) for v in suns]
        both_suns = all(0.0003 < v < 0.03 for v in suns)
        layers = [{"name": "ground_b", "from": "B", "mask": dict(AUTO_SKYLINE), "render": False},
                  {"name": "sky_b", "from": "B", "mask": {"rule": "invert", "of": "ground_b"}, "render": False}]
        if both_suns:
            layers.append({"name": "sun_b", "from": "B", "mask": {"rule": "sun", "within": "sky_b", "thr": 92, "grow": 6}, "render": False})
        layers.append({"name": "ground", "from": "A", "mask": dict(AUTO_SKYLINE), "depth": 2, "action": "morph_to", "to": "ground_b",
                       "window": [0.15, 0.85], "curve": "smootherstep", "mix_window": [0.3, 0.7], "colour_window": [0.0, 0.6],
                       "ot_grid": 64, "ot_eps": 0.04, "ot_mass": "alpha"})
        sky = {"name": "sky", "from": "A", "mask": {"rule": "invert", "of": "ground"}, "depth": 0, "action": "backdrop", "to": "sky_b",
               "opaque": True, "fit2d": True, "fill_sigma": 60, "window": [0.0, 0.85], "curve": "smootherstep",
               "minus_res": [{"layer": "ground", "full": True, "dilate": 4, "soft": 2}],
               "exclude_res": [{"layer": "ground_b", "full": True, "dilate": 4, "soft": 2}],
               "flow": {"from": "layers", "sigma": 0.12, "kappa": 0.02, "mix_window": [0.25, 0.75]}}
        if both_suns:
            sky["minus"] = ["sun"]
            sky["exclude"] = ["sun_b"]
            sky["flow"]["layers"] = ["sun"]
        layers.append(sky)
        if both_suns:
            layers.append({"name": "sun", "from": "A", "mask": {"rule": "sun", "within": "sky", "thr": 92, "grow": 6}, "depth": 1.5,
                           "action": "move_to", "to": "sun_b", "window": [0.15, 0.7], "curve": "smootherstep", "recolor_to": "sun_b",
                           "shutter": 0.5})
            layers.append({"name": "sun_b_layer", "from": "B", "mask": {"rule": "sun", "within": "sky_b", "thr": 92, "grow": 6}, "depth": 1.6,
                           "action": "materialise", "order": "luma", "noise_gain": 0.0, "feather": 0.3, "window": [0.68, 0.8], "curve": "ease"})
        facts["route"] = "sky + ground" + (" + sun" if both_suns else "")
    else:
        med = (float(np.median(sc.disparity("A"))), float(np.median(sc.disparity("B"))))
        facts["median_disparity"] = [round(v, 3) for v in med]
        layers = [{"name": "all_b", "from": "B", "mask": {"rule": "all"}, "render": False},
                  {"name": "near_b", "from": "B", "mask": {"rule": "depth_fg", "lo": round(med[1], 3), "hi": round(med[1] + 0.1, 3), "blur": 3}, "render": False},
                  {"name": "base", "from": "A", "mask": {"rule": "all"}, "depth": 0, "action": "morph_to", "to": "all_b", "ot_mass": "bright",
                   "window": [0.1, 0.9], "curve": "smootherstep", "mix_window": [0.3, 0.7], "ot_grid": 64, "ot_eps": 0.05},
                  {"name": "near", "from": "A", "mask": {"rule": "depth_fg", "lo": round(med[0], 3), "hi": round(med[0] + 0.1, 3), "blur": 3},
                   "depth": 1, "action": "morph_to", "to": "near_b", "window": [0.2, 0.9], "curve": "smootherstep", "mix_window": [0.35, 0.75],
                   "ot_grid": 64, "ot_eps": 0.04, "ot_mass": "alpha"}]
        facts["route"] = "whole frame + near layer"
    base["auto_facts"] = facts
    base["layers"] = layers
    return base


# ---------------------------------------------------------------------------
# Measurements on the composite (round 3, 2026-09-27): the numbers behind the
# owner's three faults, so a fix is judged against a figure, not by eye
# ---------------------------------------------------------------------------

def measure_layers(layers, n):
    """motion: per moving layer the per-frame displacement (max, mean, the
    peak-to-mean ratio, the share of moving frames within 10 % of the peak =
    the constant-speed plateau); dissolve: at a quarter, half and three
    quarters of the window the share of the support that is semi-transparent
    (0.05 < alpha < 0.95) and the mean width of that band along the front
    (its area over the front's length); boundary: at half and three quarters
    of a moving layer's window the mean L step across its boundary on the
    composite (a 12-px band inside against a 12-px band outside the alpha 0.5
    contour; the canvas edge does not count); carried: for a `region_of`
    layer, the mean |L| difference between the composite and the layers under
    it at the region's opaque pixels outside its core (the sky it carries
    against the sky it covers)."""
    out = {"motion": {}, "dissolve": {}, "boundary": {}}
    ts = [i / (n - 1) for i in range(n)]
    for lay in layers:
        moving = lay.action in ("exit", "enter", "move", "move_to")
        if moving or lay.spec.get("drift"):
            offs = np.array([lay.offset(t) for t in ts])
            d = np.linalg.norm(np.diff(offs, axis=0), axis=1)
            mv = d[d > 0.01]
            if len(mv):
                mx = float(d.max())
                out["motion"][lay.name] = {
                    "curve": lay.curve, "travel_px": round(float(np.linalg.norm(offs[-1] - offs[0])), 1),
                    "frames_moving": int(len(mv)), "max_px_per_frame": round(mx, 2),
                    "mean_px_per_frame": round(float(mv.mean()), 2),
                    "peak_ratio": round(mx / max(float(mv.mean()), 1e-6), 2),
                    "plateau_share": round(float((mv >= 0.9 * mx).sum() / len(mv)), 2)}
        if lay.action == "morph_to":
            mag = np.sqrt((lay.F ** 2).sum(-1))
            sel = lay.alpha0 > 0.5
            us = [lay.linear(t) for t in ts]
            ps = np.array([curve_of(lay.curve, u) for u in us])
            dp = float(np.abs(np.diff(ps)).max())
            out.setdefault("morph", {})[lay.name] = {
                "to": lay.spec["to"], "curve": lay.curve, "cells": lay.ot_info["cells"],
                "field_mean_px": round(float(mag[sel].mean()), 1) if sel.any() else 0.0,
                "field_p95_px": round(float(np.percentile(mag[sel], 95)), 1) if sel.any() else 0.0,
                "peak_px_per_frame_p95": round(float(np.percentile(mag[sel], 95)) * dp, 2) if sel.any() else 0.0,
                "mix_window": lay.mix_window}
        if getattr(lay, "flow", None) is not None:
            if lay.flow[0] == "layers":
                F, _ = lay.scene.layer_flow(lay.flow[1], lay.flow[2], lay.flow[5])
                mag = np.sqrt((F ** 2).sum(-1)) * lay.flow[4]
                reg = lay.alpha0 > 0.5
                out.setdefault("flow", {})[lay.name] = {"from": "layers", "transport_mean_px": round(float(mag[reg].mean()), 1),
                                                         "transport_max_px": round(float(mag[reg].max()), 1), "mix_window": lay.flow[3]}
            else:
                F, G, mw, info = lay.flow
                out.setdefault("flow", {})[lay.name] = {"from": "ot", "cells": info["cells"], "transport_mean_px": info["mean_px"],
                                                         "transport_max_px": info["max_px"], "mix_window": mw}
        if lay.action in ("dissolve", "materialise") and lay.spec["mask"]["rule"] != "stars":
            t0, t1 = lay.window
            shares, widths = [], []
            sup = lay.alpha0 > 0.5
            for q in (0.25, 0.5, 0.75):
                _, a = lay.render(t0 + (t1 - t0) * q)
                semi = (a > 0.05) & (a < 0.95) & sup
                shares.append(float(semi.sum()) / max(float(sup.sum()), 1.0))
                cs, _ = cv2.findContours((a > 0.5).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
                per = sum(cv2.arcLength(c, True) for c in cs)
                widths.append(float(semi.sum()) / max(per, 1.0))
            out["dissolve"][lay.name] = {"order": getattr(lay, "order_kind", "") + (":" + lay.edge_mode if getattr(lay, "edge_mode", "") else ""),
                                         "semi_share_q": [round(v, 3) for v in shares],
                                         "front_width_px_q": [round(v, 1) for v in widths],
                                         "d_max_px": getattr(lay, "d_max_px", None)}
        if moving:
            steps = {}
            carried = {}
            k = np.ones((25, 25), np.uint8)
            core = lay.spec["mask"].get("of") if lay.spec["mask"].get("rule") == "region_of" else None
            below = [l for l in layers if l.depth < lay.depth]
            for q in (0.5, 0.75):
                t = lay.window[0] + (lay.window[1] - lay.window[0]) * q
                comp = composite(layers, t)
                Lc = T.lab_of(comp)[..., 0]
                _, a = lay.render(t)
                m = (a > 0.5).astype(np.uint8)
                inner = (m > 0) & (cv2.erode(m, k) == 0)
                outer = (m == 0) & (cv2.dilate(m, k) > 0)
                if inner.sum() > 50 and outer.sum() > 50:
                    steps[str(q)] = round(float(abs(Lc[inner].mean() - Lc[outer].mean())), 2)
                if core and below:
                    # the sky a region carries between its leaves against the
                    # backdrop it covers: the composite of the layers under it,
                    # at the region's opaque pixels that are not the core
                    # (the core warped with the layer; dilated 12 px)
                    M = lay.affine(t)
                    c = lay.scene.masks[core]
                    if M is not None:
                        c = cv2.warpAffine(c, M, (lay.scene.w, lay.scene.h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
                    c = cv2.dilate((c > 0.1).astype(np.uint8), np.ones((25, 25), np.uint8))
                    sel = (a > 0.9) & (c == 0)
                    if sel.sum() > 200:
                        Lb = T.lab_of(composite(below, t))[..., 0]
                        carried[str(q)] = round(float(np.abs(Lc[sel] - Lb[sel]).mean()), 2)
            out["boundary"][lay.name] = steps
            if carried:
                out.setdefault("carried", {})[lay.name] = carried
    return out


def measure_text(meas):
    """One line for the page and the sheet."""
    if not meas:
        return ""
    parts = []
    for name, m in (meas.get("motion") or {}).items():
        parts.append(f"{name} {m['curve']} peak {m['max_px_per_frame']} px/f (x{m['peak_ratio']} mean, plateau {int(round(100 * m['plateau_share']))} %)")
    for name, m in (meas.get("dissolve") or {}).items():
        parts.append(f"{name} {m['order']} semi-transparent share {'/'.join(f'{v:.2f}' for v in m['semi_share_q'])}, front width {'/'.join(f'{v:.0f}' for v in m['front_width_px_q'])} px at 1/4, 1/2, 3/4")
    for name, m in (meas.get("boundary") or {}).items():
        if m:
            parts.append(f"{name} boundary step " + ", ".join(f"{v} L at {q}" for q, v in m.items()))
    for name, m in (meas.get("carried") or {}).items():
        parts.append(f"{name} carried-sky mismatch " + ", ".join(f"{v} L at {q}" for q, v in m.items()))
    for name, m in (meas.get("morph") or {}).items():
        parts.append(f"{name} transforms into {m['to']}: transport mean {m['field_mean_px']} px, 95th percentile {m['field_p95_px']} px "
                     f"({m['peak_px_per_frame_p95']} px/f at the peak), appearance mixed inside {m['mix_window'][0]}–{m['mix_window'][1]} of its window")
    for name, m in (meas.get("flow") or {}).items():
        parts.append(f"{name} texture flow: mean {m['transport_mean_px']} px, max {m['transport_max_px']} px")
    return " · ".join(parts)


# ---------------------------------------------------------------------------
# Render one score to the tool's outputs
# ---------------------------------------------------------------------------

def layer_sheet(layers, path):
    tiles = []
    for lay in layers:
        rgb, a = lay.render(lay.window[0])
        im = (rgb * a[..., None] + 40 * (1 - a[..., None])).astype(np.uint8)
        im = cv2.resize(im, (200, int(200 * lay.scene.h / lay.scene.w)), interpolation=cv2.INTER_AREA)
        cv2.putText(im, f"{lay.name} {lay.action}", (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)
        tiles.append(im)
    sheet = np.concatenate(tiles, axis=1)
    cv2.imwrite(str(path), cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])


def render_score(score, out, seed=0):
    out.mkdir(parents=True, exist_ok=True)
    t_all = time.time()
    A, B = canvas_pair(score["pair"], score.get("max_long", 1920))
    h, w = A.shape[:2]
    scene = Scene(A, B, seed)
    scene.n = max(2, int(round(score.get("seconds", 2.0) * float(score.get("fps", 30)))))
    t0 = time.time()
    layers = build_layers(scene, score)
    prep_s = round(time.time() - t0, 2)
    layer_sheet(layers, out / "layers.jpg")
    fps = float(score.get("fps", 30))
    n = max(2, int(round(score.get("seconds", 2.0) * fps)))
    scene.n = n
    stats = T.StreamStats(n)
    enc = T.FrameEncoder(out / "transition.mp4", w, h, fps)
    t0 = time.time()
    first_step = last_step = None
    try:
        for i in range(n):
            t = i / (n - 1)
            if i == 0:
                f = A.copy()
            elif i == n - 1:
                f = B.copy()
            else:
                f = composite(layers, t)
            if i == 1:
                first_step = float(np.abs(f.astype(int) - A.astype(int)).mean())
            if i == n - 2:
                last_step = float(np.abs(f.astype(int) - B.astype(int)).mean())
            if i in (n // 4, n // 2, 3 * n // 4):
                cv2.imwrite(str(out / f"frame_{i:03d}.jpg"), cv2.cvtColor(f, cv2.COLOR_RGB2BGR),
                            [cv2.IMWRITE_JPEG_QUALITY, 88])
            enc.write(f)
            stats.add(i, f)
        written = enc.close()
    except BaseException:
        enc.abort()
        raise
    render_s = round(time.time() - t0, 2)
    ok, buf = cv2.imencode(".jpg", cv2.cvtColor(stats.strip(), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
    if ok:
        (out / "strip.jpg").write_bytes(buf.tobytes())
    q = stats.quality(A, B)
    q["first_interior_vs_A"] = round(first_step, 2)
    q["last_interior_vs_B"] = round(last_step, 2)
    t0 = time.time()
    meas = measure_layers(layers, n)
    meas["measure_s"] = round(time.time() - t0, 2)
    report = {"tool_version": T.VERSION, "probe": "layered_probe", "score": score,
              "class": "L", "method": "layered-score",
              "layers": [{"name": l.name, "from": l.src, "action": l.action, "window": l.window,
                          "depth": l.depth, "alpha_share": round(float(l.alpha0.mean()), 4)} for l in layers],
              "canvas": [w, h], "n_frames": written, "prep_s": prep_s, "render_s": render_s,
              "quality": q, "measure": meas, "total_s": round(time.time() - t_all, 2),
              "outputs": ["transition.mp4", "strip.jpg", "report.json", "layers.jpg"]}
    (out / "report.json").write_text(json.dumps(report, indent=2))
    return report


# ---------------------------------------------------------------------------
# Sheet and page (the shape of scripts/research/theme_anchors.py)
# ---------------------------------------------------------------------------

def row_from_report(pair, tag, rep, wall):
    q = rep.get("quality", {})
    sc = rep.get("score") or {}
    seconds = sc.get("seconds") or (rep.get("n_frames") or 0) / float(sc.get("fps") or 30)
    return {"wall_s": wall, "class": rep.get("class"), "method": rep.get("method"), "canvas": rep.get("canvas"),
            "n_frames": rep.get("n_frames"), "seconds": round(float(seconds), 2), "warping_error": q.get("warping_error"),
            "edge_ratio": (q.get("flicker") or {}).get("edge_ratio"), "goal": q.get("goal"),
            "first_interior_vs_A": q.get("first_interior_vs_A"), "last_interior_vs_B": q.get("last_interior_vs_B"),
            "mp4": f"{pair}/{tag}/transition.mp4", "strip": f"{pair}/{tag}/strip.jpg",
            "layers": rep.get("layers"), "score": rep.get("score"), "measure": rep.get("measure")}


def write_page(out, sheet, picks, note=""):
    picks = (picks or {}).get("picks", {})
    html = ["<!doctype html><meta charset=utf-8><title>Layered transitions — mismatched pairs</title>",
            "<style>body{font:14px system-ui;margin:16px;background:#111;color:#ddd;max-width:1600px}h2{margin-top:40px;border-top:1px solid #333;padding-top:16px}"
            ".run{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:14px;align-items:start;margin:10px 0 18px;padding:8px;background:#181818;border-radius:6px}"
            ".run img{max-width:100%;display:block}.run video{width:320px;max-height:420px;background:#000}code{color:#9cf}"
            ".boxes label{margin-right:12px;color:#fd9}.pick label{margin-right:14px}textarea{width:100%;max-width:900px;background:#222;color:#ddd;border:1px solid #444}"
            ".note{color:#bbb}.hint{background:#26210a;padding:10px;border-radius:6px;margin:12px 0}button{padding:6px 12px}"
            "table.score{border-collapse:collapse;font-size:13px}table.score td,table.score th{border:1px solid #333;padding:2px 8px}details{margin:6px 0}</style>",
            f"<h1>Layered, orchestrated transitions — {sheet['date']}</h1>",
            "<div class=hint><b>What is on this page.</b> A reference clip (<code>flat</code>, or an earlier round's clip) is copied here unchanged for the comparison. "
            "Every <code>layered…</code> or <code>auto…</code> clip is rendered by a research script (<code>scripts/research/layered_probe.py</code>) from a SCORE, shown under "
            "the clip: the two photos are cut into layers by rules, each layer gets one action with its own time window, and the layers are composited back to front. "
            "A <code>layered…</code> score is written by hand for its pair; an <code>auto…</code> score is built by fixed rules with no per-pair parameter. "
            "Nothing in <code>transitions.py</code> changed. The seconds of each clip are on its line; canvas ≤ 1920 px. Under every clip the three boxes ask for the property, not the pick: "
            "<b>one picture</b> (the mid frame is one coherent picture, not two superimposed), <b>content transforms</b> (details move and change rather than the frame panning or fading), "
            "<b>nothing invented</b> (no content that is in neither photo). Pick the closer clip per pair, write what is wrong or what the score should say instead, and <b>Export picks</b>; "
            "drop the file beside sheet.json and run <code>scripts/research/layered_probe.py --out DIR --page-only --picks layered_picks.json</code>.</div>",
            (f"<div class=hint><b>This page.</b> {note}</div>" if note else ""),
            "<p><button onclick='exportPicks()'>Export picks</button> <span id=status class=note></span></p>"
            "<details><summary class=note>preview of what Export writes</summary><pre id=preview class=note></pre></details>"]
    for pair, row in sheet["pairs"].items():
        pk = picks.get(pair) or {}
        html.append(f"<h2 id='{pair}'>{pair} <small>canvas {'x'.join(str(v) for v in (row.get('canvas') or []))}</small></h2>")
        if row.get("owner"):
            html.append(f"<p class=note><b>Your score (verbatim):</b> {row['owner']}</p>")
        html.append(f"<div class=pick><b>Closer to the goal:</b> " + " ".join(
            f"<label><input type=radio name='pick_{pair}' value='{tag}' {'checked' if pk.get('best') == tag else ''} onchange='save()'> {tag}</label>"
            for tag in row["variants"]) + f" <label><input type=radio name='pick_{pair}' value='none' {'checked' if pk.get('best') == 'none' else ''} onchange='save()'> neither</label></div>")
        html.append(f"<textarea id='note_{pair}' rows=3 placeholder='what is wrong / what the score should say' oninput='save()'>{pk.get('note', '')}</textarea>")
        for tag, r in row["variants"].items():
            g = r.get("goal") or {}
            goal_txt = (f" goal: feat={g.get('feat_floor')} laplace={g.get('laplace_floor')} contrast={g.get('contrast_floor')} "
                        f"dissolve_fit={g.get('dissolve_fit')} motion={g.get('motion_share')}") if g else ""
            pp = (pk.get("props") or {}).get(tag) or {}
            boxes = " ".join(
                f"<label><input type=checkbox class=prop data-pair='{pair}' data-tag='{tag}' data-k='{k}' {'checked' if pp.get(k) else ''} onchange='save()'> {lab}</label>"
                for k, lab in PROPS)
            score_html = ""
            if r.get("layers"):
                rows_ = "".join(f"<tr><td>{l['depth']}</td><td>{l['name']}</td><td>{l['from']}</td><td>{l['action']}</td>"
                                f"<td>{l['window'][0]:.2f}–{l['window'][1]:.2f}</td><td>{l['alpha_share']:.3f}</td></tr>" for l in r["layers"])
                score_html = (f"<details><summary class=note>the score: {len(r['layers'])} layers (depth · layer · photo · action · window · share of the canvas)</summary>"
                              f"<table class=score><tr><th>depth</th><th>layer</th><th>from</th><th>action</th><th>window</th><th>share</th></tr>{rows_}</table>"
                              f"<pre class=note>{json.dumps(r.get('score', {}).get('layers', []), indent=1)}</pre></details>")
            step = (f" step first/last={r.get('first_interior_vs_A')}/{r.get('last_interior_vs_B')}"
                    if r.get("first_interior_vs_A") is not None else "")
            secs = f" {r.get('seconds')} s ({r.get('n_frames')} frames)" if r.get("seconds") else ""
            mt = measure_text(r.get("measure"))
            mt_html = f"<br><span class=note>measured: {mt}</span>" if mt else ""
            html.append(f"<div class=run><div><code>{tag}</code>{secs} class={r.get('class')} {r.get('method')} edge_ratio={r.get('edge_ratio')} warping={r.get('warping_error')}{goal_txt}{step}{mt_html}"
                        f"<br><span class=boxes>{boxes}</span><br><img src='{r['strip']}'>{score_html}</div>"
                        f"<video src='{r['mp4']}' controls loop muted playsinline preload=metadata></video></div>")
    html.append("""<script>
const KEY='picks:'+location.pathname;
function collect(){const p={};document.querySelectorAll('h2[id]').forEach(h=>{const id=h.id;const r=document.querySelector(`input[name='pick_${id}']:checked`);
 const n=document.getElementById('note_'+id);const props={};document.querySelectorAll(`input.prop[data-pair='${id}']`).forEach(b=>{if(b.checked){(props[b.dataset.tag]=props[b.dataset.tag]||{})[b.dataset.k]=true;}});
 if((r&&r.value)||(n&&n.value)||Object.keys(props).length)p[id]={best:r?r.value:'',note:n?n.value:'',props:props};});return p;}
function save(){try{const c=collect();localStorage.setItem(KEY,JSON.stringify(c));document.getElementById('status').textContent='saved locally '+new Date().toLocaleTimeString();document.getElementById('preview').textContent=JSON.stringify(c,null,1);}catch(e){}}
function restore(){try{const p=JSON.parse(localStorage.getItem(KEY)||'{}');for(const id in p){const r=document.querySelector(`input[name='pick_${id}'][value='${p[id].best}']`);if(r)r.checked=true;
 const n=document.getElementById('note_'+id);if(n&&p[id].note)n.value=p[id].note;const pr=p[id].props||{};for(const tag in pr){for(const k in pr[tag]){const b=document.querySelector(`input.prop[data-pair='${id}'][data-tag='${tag}'][data-k='${k}']`);if(b)b.checked=true;}}}}catch(e){}}
function exportPicks(){const blob=new Blob([JSON.stringify({date:new Date().toISOString(),page:'layered_probe',picks:collect()},null,2)],{type:'application/json'});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='layered_picks.json';a.click();document.getElementById('status').textContent='layered_picks.json downloaded';}
restore();
</script>""")
    (out / "index.html").write_text("\n".join(html))


def write_sheet_md(out, sheet, picks):
    picks = (picks or {}).get("picks", {})
    md = [f"# Layered transitions — {sheet['date']}", "",
          "| pair | variant | class | method | edge_ratio | warping | feat_floor | laplace_floor | contrast_floor | dissolve_fit | motion_share | step first/last | wall s |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for pair, row in sheet["pairs"].items():
        for tag, r in row["variants"].items():
            g = r.get("goal") or {}
            md.append(f"| {pair} | {tag} | {r.get('class')} | {r.get('method')} | {r.get('edge_ratio')} | {r.get('warping_error')} | "
                      f"{g.get('feat_floor')} | {g.get('laplace_floor')} | {g.get('contrast_floor')} | {g.get('dissolve_fit')} | {g.get('motion_share')} | "
                      f"{r.get('first_interior_vs_A')}/{r.get('last_interior_vs_B')} | {r.get('wall_s')} |")
    md += ["", "## Measured on the composite (per-frame displacement · dissolve front · boundary step)", ""]
    for pair, row in sheet["pairs"].items():
        for tag, r in row["variants"].items():
            if r.get("measure"):
                md.append(f"- {pair} `{tag}`: {measure_text(r['measure'])}")
    md += ["", "## Scores (layer · photo · action · window · share of the canvas)", ""]
    for pair, row in sheet["pairs"].items():
        for tag, r in row["variants"].items():
            if r.get("layers"):
                md.append(f"- {pair} `{tag}`: " + "; ".join(
                    f"{l['name']} ({l['from']}, {l['action']} {l['window'][0]:.2f}–{l['window'][1]:.2f}, share {l['alpha_share']:.3f})" for l in r["layers"]))
    if picks:
        md += ["", "## Owner picks (layered_picks.json)", "", "| pair | closer | note | boxes (one picture / transforms / nothing invented) |", "|---|---|---|---|"]
        for pair in sheet["pairs"]:
            pk = picks.get(pair) or {}
            props = pk.get("props") or {}
            boxes = "; ".join(f"{tag}: " + "/".join("yes" if v.get(k) else "no" for k, _ in PROPS) for tag, v in props.items())
            md.append(f"| {pair} | {pk.get('best', '')} | {(pk.get('note') or '').replace('|', '/')} | {boxes} |")
    (out / "sheet.md").write_text("\n".join(md) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--score", action="append", default=[], help="a score JSON (repeatable)")
    ap.add_argument("--auto", action="append", default=[], help="a pair id: write scores/auto/<pair>.json by the fixed rules and render it (repeatable)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--ref", action="append", default=[], help="tag=DIR: copy a reference clip's outputs beside the probe (pair from the first --score)")
    ap.add_argument("--pair", default="", help="pair for --ref when no --score is given")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--page-only", action="store_true")
    ap.add_argument("--picks", default="")
    ap.add_argument("--note", default="", help="a paragraph for the page's head (what this round varies)")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    sheet_path = out / "sheet.json"
    sheet = json.loads(sheet_path.read_text()) if sheet_path.exists() else {"date": time.strftime("%Y-%m-%d"), "pairs": {}}
    pair = a.pair
    if not a.page_only:
        for pair_id in a.auto:
            auto = auto_score(pair_id)
            dst = ROOT / "scripts" / "research" / "scores" / "auto" / f"{pair_id}.json"
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(json.dumps(auto, indent=1) + "\n")
            print(f"  auto {pair_id}: {auto['auto_facts']}", flush=True)
            a.score.append(str(dst))
        for sc in a.score:
            score = json.loads(Path(sc).read_text())
            pair, tag = score["pair"], score.get("tag", Path(sc).stem)
            t = time.time()
            rep = render_score(score, out / pair / tag, a.seed)
            wall = round(time.time() - t, 1)
            row = sheet["pairs"].setdefault(pair, {"canvas": rep["canvas"], "owner": score.get("owner", ""), "variants": {}})
            row["owner"] = score.get("owner", row.get("owner", ""))
            row["variants"][tag] = row_from_report(pair, tag, rep, wall)
            g = rep["quality"]["goal"]
            print(f"  {pair} {tag}: {rep['n_frames']} frames, prep {rep['prep_s']}s, render {rep['render_s']}s, "
                  f"edge_ratio={rep['quality']['flicker']['edge_ratio']} step={rep['quality']['first_interior_vs_A']}/{rep['quality']['last_interior_vs_B']} goal={g}", flush=True)
            sheet_path.write_text(json.dumps(sheet, indent=1))
        for ref in a.ref:
            tag, src = ref.split("=", 1)
            src = Path(src)
            if not pair:
                raise SystemExit("--ref needs a pair: give a --score or --pair")
            d = out / pair / tag
            d.mkdir(parents=True, exist_ok=True)
            for f in ("transition.mp4", "strip.jpg", "report.json"):
                shutil.copy2(src / f, d / f)
            rep = json.loads((d / "report.json").read_text())
            row = sheet["pairs"].setdefault(pair, {"canvas": rep.get("canvas"), "owner": "", "variants": {}})
            row["variants"][tag] = row_from_report(pair, tag, rep, rep.get("total_s"))
            row["variants"][tag]["layers"] = None
            row["variants"][tag]["score"] = None
            sheet_path.write_text(json.dumps(sheet, indent=1))
        # references first on the page, then the probes
        for p, row in sheet["pairs"].items():
            v = row["variants"]
            row["variants"] = {k: v[k] for k in sorted(v, key=lambda k: (0 if v[k].get("layers") is None else 1, k))}
        sheet_path.write_text(json.dumps(sheet, indent=1))
    picks = json.loads(Path(a.picks).read_text()) if a.picks else None
    if a.note:
        sheet["note"] = a.note
        sheet_path.write_text(json.dumps(sheet, indent=1))
    write_page(out, sheet, picks, sheet.get("note", ""))
    write_sheet_md(out, sheet, picks)
    print(f"wrote {out / 'index.html'}, {out / 'sheet.md'}")


if __name__ == "__main__":
    sys.exit(main())
