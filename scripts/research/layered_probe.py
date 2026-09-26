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
stars (white top-hat blobs `within` a layer), polygon (hand-drawn, canvas fractions), all (1).
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
            if m.get("grow", 0):
                # a moving layer carries the background within `grow` px of
                # its edge, so its soft edge never mixes with the backdrop
                k = int(m["grow"])
                a = np.maximum(a, cv2.GaussianBlur(cv2.dilate(a, np.ones((2 * k + 1, 2 * k + 1), np.uint8)), (0, 0), 1.0))
            if rule == "depth_bg":
                a = 1.0 - a
            if m.get("components"):
                a = keep_components(a, m["components"], m.get("min_area", 200))
            if m.get("blur", 0):
                a = cv2.GaussianBlur(a, (0, 0), m["blur"])
        elif rule in ("skyline_below", "skyline_above"):
            a = self._skyline(src, m)
            if rule == "skyline_above":
                a = 1.0 - a
        elif rule == "invert":
            a = 1.0 - self.masks[m["of"]]
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
        self.masks[name] = a.astype(np.float32)
        return self.masks[name]

    def _darkness(self, src, bg, m):
        """0..1: how much darker than the per-row brightness of `bg` (the rest
        of the photo) a pixel is; 1 at `dark_hi` of the way to black."""
        lab = self.lab[src]
        st = row_stats(lab, np.clip(bg, 0, 1), min_px=300)
        Lfit = np.maximum(st[:, 0, 0], float(m.get("dark_floor", 4.0)))[:, None]
        return ramp((Lfit - lab[..., 0]) / Lfit, m.get("dark_lo", 0.35), m.get("dark_hi", 0.7))

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
        k = int(m.get("median", 9))
        for arr in (top, bottom):
            pad = np.pad(arr, k // 2, mode="edge")
            arr[:] = np.median(np.lib.stride_tricks.sliding_window_view(pad, k), axis=1)
        self.masks["_band_" + name] = (top, bottom)
        yy = np.arange(h, dtype=np.float32)[:, None]
        f = float(m.get("feather", 3.0))
        return smoothstep((yy - top[None, :] + 1.0) / f) * smoothstep((bottom[None, :] - yy + 1.0) / f)

    def _clouds(self, src, within, m):
        """Cloud density against the clear sky of the same rows: the clear sky
        is a low percentile of the channel over a window of rows (so a row
        full of cloud still finds the clear sky beside it); a cloud is where
        the channel rises toward the cloud value. channel "b": b* rises from
        blue toward b_cloud (a day sky); channel "L": L rises by `delta` (a
        sunset). Density 0..1; the matte is opaque above `opaque`."""
        lab = self.lab[src]
        chan = m.get("channel", "b")
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
        return T.curve(self.curve, u)

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
            else:
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

    def colour(self, t):
        """The layer's RGB at time t after its colour path (float32)."""
        sp = self.spec
        to = sp.get("recolor_to") or (sp.get("to") if self.action == "recolor" else None)
        if not to:
            return self.rgb
        p = self.progress(t) * float(sp.get("recolor_strength", 1.0))
        if p <= 0:
            return self.rgb
        dst = self.by_name[to].stats
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
        rgb = self.colour(t)
        p = self.progress(t)
        if self.action == "dissolve":
            # the threshold rises from below the support's lowest order value
            # to its highest: at p = 0 the whole matte, at p = 1 nothing
            theta = -self.feather + (1.0 + self.feather) * p
            alpha = self.alpha0 * np.clip((self.E - theta) / self.feather, 0, 1)
        elif self.action == "materialise":
            if self.order_kind == "blobs":
                alpha = self.alpha0 * np.clip((p - self.order) / self.each, 0, 1)
            else:
                # the reverse of dissolve: the highest order value comes first
                theta = (1.0 + self.feather) * (1.0 - p) - self.feather
                alpha = self.alpha0 * np.clip((self.E - theta) / self.feather, 0, 1)
        else:
            alpha = self.alpha0
        M = self.affine(t)
        if M is not None:
            h, w = self.scene.h, self.scene.w
            rgb = cv2.warpAffine(rgb, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            alpha = cv2.warpAffine(alpha, M, (w, h), flags=cv2.INTER_LINEAR,
                                   borderMode=cv2.BORDER_CONSTANT, borderValue=0)
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
        clearA = np.ones_like(self.alpha0)
        for name in sp.get("minus", []):
            clearA = clearA * (1.0 - ramp(s.masks[name], 0.9, 1.0))
        clearB = np.ones_like(self.alpha0)
        excl = sp.get("exclude") or []
        for name in ([excl] if isinstance(excl, str) else excl):
            clearB = clearB * (1.0 - ramp(s.masks[name], 0.9, 1.0))
        # the region: the base backdrop covers the canvas; a partial one (the
        # water) moves from its A mask to its B mask over the window
        self.alpha_to = s.masks[sp["mask_to"]] if sp.get("mask_to") else None
        self.opaque = bool(sp.get("opaque", self.depth == 0))
        # the FIT counts every sky pixel, including the sky seen between the
        # leaves of a foreground layer (its soft alpha), so the gradient under
        # that layer follows the photo; the RESIDUAL is interior-only
        self.fitA = row_stats(self.lab, self.alpha0 * clearA, min_px=300)
        self.fitB = row_stats(other.lab, other.alpha0 * clearB, min_px=300)
        self.stats = self.fitA
        wA = ramp(self.alpha0, 0.9, 1.0) * clearA
        wB = ramp(other.alpha0, 0.9, 1.0) * clearB
        self.resA = (self.lab - self.fitA[:, None, :, 0]) * wA[..., None]
        self.resB = (other.lab - self.fitB[:, None, :, 0]) * wB[..., None]

    def render(self, t):
        p = self.progress(t)
        fit = self.fitA[:, None, :, 0] * (1 - p) + self.fitB[:, None, :, 0] * p
        lab = fit + self.resA * (1 - p) + self.resB * p
        if self.opaque:
            alpha = np.ones((self.scene.h, self.scene.w), np.float32)
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
    t0 = time.time()
    layers = build_layers(scene, score)
    prep_s = round(time.time() - t0, 2)
    layer_sheet(layers, out / "layers.jpg")
    fps = float(score.get("fps", 30))
    n = max(2, int(round(score.get("seconds", 2.0) * fps)))
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
    report = {"tool_version": T.VERSION, "probe": "layered_probe", "score": score,
              "class": "L", "method": "layered-score",
              "layers": [{"name": l.name, "from": l.src, "action": l.action, "window": l.window,
                          "depth": l.depth, "alpha_share": round(float(l.alpha0.mean()), 4)} for l in layers],
              "canvas": [w, h], "n_frames": written, "prep_s": prep_s, "render_s": render_s,
              "quality": q, "total_s": round(time.time() - t_all, 2),
              "outputs": ["transition.mp4", "strip.jpg", "report.json", "layers.jpg"]}
    (out / "report.json").write_text(json.dumps(report, indent=2))
    return report


# ---------------------------------------------------------------------------
# Sheet and page (the shape of scripts/research/theme_anchors.py)
# ---------------------------------------------------------------------------

def row_from_report(pair, tag, rep, wall):
    q = rep.get("quality", {})
    return {"wall_s": wall, "class": rep.get("class"), "method": rep.get("method"), "canvas": rep.get("canvas"),
            "n_frames": rep.get("n_frames"), "warping_error": q.get("warping_error"),
            "edge_ratio": (q.get("flicker") or {}).get("edge_ratio"), "goal": q.get("goal"),
            "first_interior_vs_A": q.get("first_interior_vs_A"), "last_interior_vs_B": q.get("last_interior_vs_B"),
            "mp4": f"{pair}/{tag}/transition.mp4", "strip": f"{pair}/{tag}/strip.jpg",
            "layers": rep.get("layers"), "score": rep.get("score")}


def write_page(out, sheet, picks):
    picks = (picks or {}).get("picks", {})
    html = ["<!doctype html><meta charset=utf-8><title>Layered transitions — mismatched pairs</title>",
            "<style>body{font:14px system-ui;margin:16px;background:#111;color:#ddd;max-width:1600px}h2{margin-top:40px;border-top:1px solid #333;padding-top:16px}"
            ".run{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:14px;align-items:start;margin:10px 0 18px;padding:8px;background:#181818;border-radius:6px}"
            ".run img{max-width:100%;display:block}.run video{width:320px;max-height:420px;background:#000}code{color:#9cf}"
            ".boxes label{margin-right:12px;color:#fd9}.pick label{margin-right:14px}textarea{width:100%;max-width:900px;background:#222;color:#ddd;border:1px solid #444}"
            ".note{color:#bbb}.hint{background:#26210a;padding:10px;border-radius:6px;margin:12px 0}button{padding:6px 12px}"
            "table.score{border-collapse:collapse;font-size:13px}table.score td,table.score th{border:1px solid #333;padding:2px 8px}details{margin:6px 0}</style>",
            f"<h1>Layered, orchestrated transitions — {sheet['date']}</h1>",
            "<div class=hint><b>What varies.</b> <code>flat</code> and <code>anchors_falloff</code> are the two clips you graded on the theme-anchors page (the shipped class B pan-and-zoom, "
            "and the hand-placed anchors with the border falloff), copied here unchanged for the comparison. Every <code>layered…</code> clip is rendered by a research script "
            "(<code>scripts/research/layered_probe.py</code>) from a hand-written SCORE, shown under the pair: the photos are cut into layers by rules (depth from the offline "
            "depth model, cloud density from the sky's blue, stars as bright blobs), each layer gets one action with its own time window (the sky gradient darkens on its own, "
            "the clouds erode through their own density, the stars appear in brightness order, the buildings slide out, the trees and the air-conditioning unit slide in), "
            "and the layers are composited back to front. No pixel is a crossfade of A-content and B-content; the only mixed quantity is the low-amplitude sky texture. "
            "Nothing in <code>transitions.py</code> changed. Every clip: 2 s, canvas ≤ 1920 px. Under every clip the three boxes ask for the property, not the pick: "
            "<b>one picture</b> (the mid frame is one coherent picture, not two superimposed), <b>content transforms</b> (details move and change rather than the frame panning or fading), "
            "<b>nothing invented</b> (no content that is in neither photo). Pick the closer clip per pair, write what is wrong or what the score should say instead, and <b>Export picks</b>; "
            "drop the file beside sheet.json and run <code>scripts/research/layered_probe.py --out DIR --page-only --picks layered_picks.json</code>.</div>",
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
            html.append(f"<div class=run><div><code>{tag}</code> class={r.get('class')} {r.get('method')} edge_ratio={r.get('edge_ratio')} warping={r.get('warping_error')}{goal_txt}{step}"
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
    ap.add_argument("--out", required=True)
    ap.add_argument("--ref", action="append", default=[], help="tag=DIR: copy a reference clip's outputs beside the probe (pair from the first --score)")
    ap.add_argument("--pair", default="", help="pair for --ref when no --score is given")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--page-only", action="store_true")
    ap.add_argument("--picks", default="")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    sheet_path = out / "sheet.json"
    sheet = json.loads(sheet_path.read_text()) if sheet_path.exists() else {"date": time.strftime("%Y-%m-%d"), "pairs": {}}
    pair = a.pair
    if not a.page_only:
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
    write_page(out, sheet, picks)
    write_sheet_md(out, sheet, picks)
    print(f"wrote {out / 'index.html'}, {out / 'sheet.md'}")


if __name__ == "__main__":
    sys.exit(main())
