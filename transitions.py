#!/usr/bin/env python3
"""
Transitions: animate the change between two photos as a short video.

Reveal lines two photos up and hides the change behind a slider. This tool
takes two photos (typically Reveal's before.jpg and after_aligned.jpg, but
any pair) and renders the change itself as a transition: a flow-guided
morph, a dissolve, a portal reveal or a luma wipe, with the colors of both
photos meeting halfway along the way.

It is a second single-file tool that lives beside reveal.py in the same
repository and the same virtualenv. Contract (transitions_harness.py pins
it):
  * this module never imports reveal, and reveal.py never imports this
    module; a Reveal change cannot break a transition or the reverse.
  * everything runs locally, on the CPU, offline. The one optional model
    (Depth Anything V2 Small behind --camera model) is fetched ONCE by
    `transitions.py warmup` into models/depth/ and recorded in a manifest;
    a run never downloads and refuses to start the model without it.
  * the inputs are never modified; every output is a new file in --out.
  * the first and last frame of a transition are the two input photos,
    byte-exact, whatever the color path did in between.
  * the result is deterministic: the same inputs and options produce the
    same frames (no random source anywhere in the pipeline).

Pipeline (the deterministic tier of the transitions research plan under
.claude/claude-docs/transitions-research/; the generative tier is not
built until it has been measured):
  decode -> common canvas (cover-crop) -> correspondence (class A: SIFT +
  MAGSAC++ homography, then DIS residual flow on the pre-aligned pair, both
  directions, forward-backward consistency as certainty; class B: no
  geometric correspondence, saliency similarity or user anchors through
  Moving Least Squares; --camera ramp|model scales the class B pan-and-zoom
  by a disparity so near content moves more than far content) -> per
  frame: time-varying Lab color path, forward splat of both endpoints
  toward the intermediate frame, coverage-aware cross-dissolve -> frames
  piped to the bundled ffmpeg as rawvideo ->
  libx264 mp4, plus an 8-tile thumbnail strip and report.json with the
  quality basket (warping error, flicker with the hidden-cut detector,
  endpoint fidelity, and the goal numbers: feature survival, sharpness
  and contrast floors, the crossfade fit and the motion share).

Usage:
  python transitions.py pair BEFORE AFTER --out DIR [--seconds 1.0]
        [--preset morph|dissolve|flow-dissolve|snap-morph|iris|wipe|luma]
        [--fps 30] [--color 0.7] [--warp 1.0] [--max-long 0]
        [--anchors "ax,ay,bx,by;..."] [--class A|B]
        [--camera flat|ramp|model] [--zoom 0.10]
  python transitions.py check
  python transitions.py warmup      # fetch + verify the depth model once
"""

import argparse
import hashlib
import io
import json
import logging
import math
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

try:
    import cv2
except Exception as e:  # pragma: no cover
    sys.exit(f"OpenCV is required (pip install -r requirements.txt): {e}")

from PIL import Image, ImageCms, ImageOps

# Optional layers (same set as reveal.py; absence is a plain message) -------
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    _HEIF_ERR = None
except Exception as _e:  # pragma: no cover
    pillow_heif = None
    _HEIF_ERR = str(_e)

try:
    import rawpy
    _RAWPY_ERR = None
except Exception as _e:  # pragma: no cover
    rawpy = None
    _RAWPY_ERR = str(_e)

try:
    import imageio_ffmpeg
    _FFMPEG_ERR = None
except Exception as _e:  # pragma: no cover
    imageio_ffmpeg = None
    _FFMPEG_ERR = str(_e)

VERSION = "0.1.0"

log = logging.getLogger("transitions")


class TransitionError(Exception):
    """A pipeline failure with an operator-readable message."""


# ---------------------------------------------------------------------------
# Configuration (constants by design, like reveal.py: no settings file)
# ---------------------------------------------------------------------------

TCFG = {
    # timeline
    "fps": 30.0,
    "min_seconds": 0.1,
    "max_seconds": 10.0,
    # sparse correspondence (class routing)
    "sift_features": 6000,
    "ratio": 0.75,             # Lowe ratio test
    "min_matches": 12,
    "magsac_thresh": 2.5,      # px on the canvas
    "min_inliers": 30,         # class A floor
    "area_ratio": (0.15, 6.0), # sanity: warped quad area vs canvas area
    "consistency_sigma": 3.0,  # px; forward-backward error -> certainty
    # dense warp
    "splat_scale": 4,          # coordinate splat runs at 1/scale resolution
    "splat_sharpness": 10.0,   # softmax-style collision weighting
    "hole_thresh": 0.05,       # coverage below this is a true hole
    "mix_blur": 3.0,           # px, softens the coverage-aware mix
    "anchor_blend": 0.7,       # class A: weight of user anchors over the field
    "anchor_falloff": 0.0,     # anchors: fraction of the short edge over which the
                               # anchored field fades to zero at the canvas border, so
                               # the moved frame keeps covering the canvas (T16);
                               # 0 = off, the 2026-09-13 field byte for byte
    "anchor_falloff_max": 0.5,
    "classb_zoom": 0.10,       # class B: each frame zooms in by this much about its
                               # salient center; the pan toward the other frame's
                               # salient center is capped by the zoom's slack so a
                               # frame edge never enters the canvas (defect T13)
    "zoom_range": (0.02, 0.5), # --zoom is clamped to this
    # camera move (TR10, 2026-09-23): the class B pan-and-zoom is scaled by
    # (1 - gain/2 + gain * d) with d = disparity, 0 far .. 1 near, so the nearest
    # content moves 1.5x and the farthest 0.5x (parallax), and near content
    # wins the splat's collisions through the importance below
    "depth_gain": 1.0,
    "depth_w_floor": 0.2,      # splat importance = floor + (1 - floor) * d
    "depth_percentiles": (2, 98),  # the model's raw output clipped to this range -> 0..1
    "depth_long": 1024,        # long edge handed to the model (it resizes to 518 itself)
    # color path
    "color_gain_clip": (0.4, 2.5),
    # quality basket (computed on a proxy so 4K stays cheap)
    "quality_long": 480,
    "goal_features": 1500,     # SIFT keypoints per endpoint for feat_floor
    "goal_patch": 24,          # patch size (proxy px) for contrast_floor
    "strip_tiles": 8,
    "strip_height": 160,
    # encode
    "video_crf": 18,
}

CURVES = {
    "linear": lambda u: u,
    "ease": lambda u: 0.5 - 0.5 * math.cos(math.pi * u),
    "ease-in": lambda u: u * u,
    "ease-out": lambda u: 1 - (1 - u) ** 2,
    "snap": lambda u: 0.0 if u < 0.5 else 1.0,
    "hold-then-go": lambda u: 0.0 if u < 0.35 else (u - 0.35) / 0.65,
}

STYLES = ("morph", "dissolve", "warp-dissolve", "portal", "luma")
PORTALS = ("iris", "wipe")
CAMERAS = ("flat", "ramp", "model")   # class B: no parallax | a top-to-bottom
                                      # disparity ramp | Depth Anything V2 Small


def curve(name, u):
    return float(min(1.0, max(0.0, CURVES.get(name, CURVES["ease"])(u))))


@dataclass
class TransitionSpec:
    """What the user can say about one transition. Presets are named
    specs; every field is overridable."""
    seconds: float = 1.0
    fps: float = TCFG["fps"]
    style: str = "morph"           # one of STYLES
    warp_curve: str = "ease"       # geometric progress over u in [0,1]
    mix_curve: str = "ease"        # cross-dissolve progress
    mix_delay: float = 0.0         # shift the dissolve later (+) / earlier (-)
    warp_amount: float = 1.0       # 0 = plain dissolve on the skeleton
    color_strength: float = 0.7    # time-varying color pull, 0..1
    portal: str = "iris"           # style=portal: iris | wipe
    portal_feather: float = 0.08   # fraction of the canvas diagonal
    max_long_edge: int = 0         # 0 = native canvas
    canvas: str = "finish"         # canvas policy: finish | common
    anchors: list = field(default_factory=list)   # [[ax, ay, bx, by], ...] canvas px
    force_class: str = ""          # "", "A", "B"
    camera: str = "flat"           # class B camera move: one of CAMERAS
    zoom: float = TCFG["classb_zoom"]   # class B zoom fraction, clamped to zoom_range
    anchor_falloff: float = TCFG["anchor_falloff"]   # anchors: border falloff fraction

    def n_frames(self):
        return max(2, int(round(self.seconds * self.fps)))

    def clamp(self):
        self.seconds = float(min(TCFG["max_seconds"],
                                 max(TCFG["min_seconds"], self.seconds)))
        self.fps = float(max(1.0, self.fps))
        self.warp_amount = float(min(1.0, max(0.0, self.warp_amount)))
        self.color_strength = float(min(1.0, max(0.0, self.color_strength)))
        self.portal_feather = float(min(0.5, max(0.005, self.portal_feather)))
        lo, hi = TCFG["zoom_range"]
        self.zoom = float(min(hi, max(lo, self.zoom)))
        self.anchor_falloff = float(min(TCFG["anchor_falloff_max"],
                                        max(0.0, self.anchor_falloff)))
        if self.camera not in CAMERAS:
            raise TransitionError(f"Unknown camera {self.camera!r}. "
                                  f"Cameras: {', '.join(CAMERAS)}")
        if self.style not in STYLES:
            raise TransitionError(f"Unknown style {self.style!r}. "
                                  f"Styles: {', '.join(STYLES)}")
        if self.portal not in PORTALS:
            raise TransitionError(f"Unknown portal {self.portal!r}. "
                                  f"Portals: {', '.join(PORTALS)}")
        if self.force_class not in ("", "A", "B"):
            raise TransitionError("--class must be A or B")
        if self.canvas not in CANVAS_POLICIES:
            raise TransitionError(f"Unknown canvas policy {self.canvas!r}. "
                                  f"Policies: {', '.join(CANVAS_POLICIES)}")
        return self

    def progress(self, i):
        """(t_warp, t_mix, u) for frame i of n_frames()."""
        n = self.n_frames()
        u = i / (n - 1)
        tw = (curve(self.warp_curve, u) * self.warp_amount
              + (1.0 - self.warp_amount) * u)
        if self.mix_delay >= 0:
            um = min(1.0, max(0.0, u - self.mix_delay))
        else:
            um = min(1.0, max(0.0, u / (1.0 + self.mix_delay)))
        return tw, curve(self.mix_curve, um), u


PRESETS = {
    "morph": {"style": "morph", "warp_curve": "ease", "mix_curve": "ease"},
    "dissolve": {"style": "dissolve", "warp_amount": 0.0},
    "flow-dissolve": {"style": "warp-dissolve", "warp_amount": 0.6,
                      "mix_delay": 0.1},
    "snap-morph": {"style": "morph", "warp_curve": "hold-then-go",
                   "mix_curve": "ease-in"},
    "iris": {"style": "portal", "portal": "iris"},
    "wipe": {"style": "portal", "portal": "wipe"},
    "luma": {"style": "luma"},
}


def spec_from(preset="morph", **over):
    if preset not in PRESETS:
        raise TransitionError(f"Unknown preset {preset!r}. "
                              f"Presets: {', '.join(PRESETS)}")
    return TransitionSpec(**{**PRESETS[preset], **over}).clamp()


# ---------------------------------------------------------------------------
# Decode and canvas (re-implemented, not imported: the isolation contract)
# ---------------------------------------------------------------------------

RAW_EXTS = {".dng", ".arw"}
HEIF_EXTS = {".heic", ".heif", ".hif"}
PIL_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}
ACCEPT_EXTS = RAW_EXTS | HEIF_EXTS | PIL_EXTS


def _srgb_from_pil(img):
    icc = img.info.get("icc_profile")
    if icc:
        try:
            src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            dst = ImageCms.createProfile("sRGB")
            return ImageCms.profileToProfile(
                img, src, dst, outputMode="RGB",
                renderingIntent=ImageCms.Intent.PERCEPTUAL)
        except Exception as e:
            log.warning("ICC transform failed (%s); using plain convert", e)
    return img.convert("RGB")


def load_image_rgb(path):
    """sRGB uint8 HxWx3 with EXIF orientation applied. Raises
    TransitionError with a plain message."""
    p = Path(path)
    ext = p.suffix.lower()
    if not p.exists():
        raise TransitionError(f"File not found: {p}")
    if ext in RAW_EXTS:
        if rawpy is None:
            raise TransitionError(
                f"RAW file ({ext}) needs the rawpy package, which failed to "
                f"load: {_RAWPY_ERR}. Re-run ./setup.sh.")
        try:
            with rawpy.imread(str(p)) as raw:
                # rawpy applies the camera flip itself; never re-apply EXIF
                rgb = raw.postprocess(use_camera_wb=True, output_bps=8,
                                      no_auto_bright=False)
            return np.ascontiguousarray(rgb)
        except Exception as e:
            raise TransitionError(f"Could not decode RAW file {p.name}: {e}")
    if ext in HEIF_EXTS and pillow_heif is None:
        raise TransitionError(
            f"HEIC support failed to load: {_HEIF_ERR}. Re-run ./setup.sh.")
    if ext not in ACCEPT_EXTS:
        raise TransitionError(
            f"Unsupported file type {ext or '(none)'}. Accepted: "
            + ", ".join(sorted(ACCEPT_EXTS)))
    try:
        with Image.open(p) as img:
            img = ImageOps.exif_transpose(img)
            img = _srgb_from_pil(img)
            return np.asarray(img, dtype=np.uint8).copy()
    except Exception as e:
        raise TransitionError(f"Could not decode {p.name}: {e}")


def gray_of(rgb):
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)


def even(n):
    return max(2, int(n) & ~1)


def to_u8(x):
    """float -> uint8 by ROUNDING. A plain astype truncates, which biases
    every composited frame down by half a level and manufactures a visible
    step against the byte-exact pinned endpoints (measured: 0.8 levels at
    the last frame of a clean dissolve, edge_ratio 1.96 -> 0.x)."""
    return np.clip(np.asarray(x, np.float32) + 0.5, 0, 255).astype(np.uint8)


def cover(img, w, h):
    """Scale-to-fill and center-crop to exactly (w, h)."""
    H, W = img.shape[:2]
    if (W, H) == (w, h):
        return np.ascontiguousarray(img)
    s = max(w / W, h / H)
    r = cv2.resize(img, (max(w, round(W * s)), max(h, round(H * s))),
                   interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    y, x = (r.shape[0] - h) // 2, (r.shape[1] - w) // 2
    return np.ascontiguousarray(r[y:y + h, x:x + w])


CANVAS_POLICIES = ("finish", "common")


def common_canvas(a, b, max_long=0, policy="finish"):
    """The shared canvas for two images, even dimensions (yuv420p), never
    upscaling either source, optionally capped by max_long.

    finish (default; owner ruling 2026-09-14 "finish target ratio wins"):
        the canvas has the FINISH image's aspect ratio and is the largest
        such rectangle both images can cover without upscaling.
    common: the smaller frame's width and the smaller frame's height (the
        largest area both can cover; the aspect is neither's when they
        differ). A letterbox mode is planned (EXPLORATION_PLAN TR13)."""
    hA, wA = a.shape[:2]
    hB, wB = b.shape[:2]
    if policy == "common":
        w, h = min(wA, wB), min(hA, hB)
    elif policy == "finish":
        r = wB / hB
        w = min(wA, hA * r, wB)
        h = w / r
    else:
        raise TransitionError(f"Unknown canvas policy {policy!r}. "
                              f"Policies: {', '.join(CANVAS_POLICIES)}")
    if max_long and max(h, w) > max_long:
        s = max_long / max(h, w)
        h, w = h * s, w * s
    return even(round(w)), even(round(h))


def _grid(h, w):
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32),
                         np.arange(h, dtype=np.float32))
    return gx, gy


# ---------------------------------------------------------------------------
# Correspondence: where does every pixel of A go in B?
#
# All displacement fields are in canvas PIXELS on the source grid:
#   dAB[y, x] = (dx, dy)  such that  B[y + dy, x + dx] ~ A[y, x].
# Two classes of pair. Class A (related: same or similar scene) gets a
# homography pre-alignment plus residual DIS flow, in both directions, with
# forward-backward consistency as per-pixel certainty. Class B (unrelated:
# no geometric correspondence exists) gets one pan-and-zoom per frame about
# its salient blob, capped so the frame keeps covering the canvas, or the
# user's anchor points through Moving Least Squares.
# ---------------------------------------------------------------------------

def sparse_homography(gA, gB, cfg=TCFG):
    """SIFT + ratio test + MAGSAC++. Returns (H_BA, inliers, rmse) or None.
    H_BA maps B pixels onto A pixels."""
    det = cv2.SIFT_create(nfeatures=cfg["sift_features"])
    kA, dA = det.detectAndCompute(gA, None)
    kB, dB = det.detectAndCompute(gB, None)
    if dA is None or dB is None or len(dA) < 8 or len(dB) < 8:
        return None
    knn = cv2.BFMatcher(cv2.NORM_L2).knnMatch(dB, dA, k=2)
    good = [m for m, n in (p for p in knn if len(p) == 2)
            if m.distance < cfg["ratio"] * n.distance]
    if len(good) < cfg["min_matches"]:
        return None
    pB = np.float32([kB[m.queryIdx].pt for m in good])
    pA = np.float32([kA[m.trainIdx].pt for m in good])
    flag = getattr(cv2, "USAC_MAGSAC", cv2.RANSAC)
    H, mask = cv2.findHomography(pB, pA, flag, cfg["magsac_thresh"],
                                 maxIters=10000, confidence=0.999)
    if H is None or mask is None:
        return None
    inl = mask.ravel().astype(bool)
    if inl.sum() < 4:
        return None
    proj = cv2.perspectiveTransform(pB[inl].reshape(-1, 1, 2), H)
    rmse = float(np.sqrt(np.mean(np.sum(
        (proj.reshape(-1, 2) - pA[inl]) ** 2, 1))))
    return H, int(inl.sum()), rmse


def _sane(H, shape, cfg=TCFG):
    h, w = shape[:2]
    c = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
    q = cv2.perspectiveTransform(c, H).reshape(-1, 2).astype(np.float32)
    if not cv2.isContourConvex(q):
        return False
    area = cv2.contourArea(q) / float(w * h)
    lo, hi = cfg["area_ratio"]
    return lo <= area <= hi


def _dis(gA, gB):
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    nA = cv2.normalize(gA, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    nB = cv2.normalize(gB, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    return dis.calc(nA, nB, None)          # A[y,x] ~ B[y+fy, x+fx]


def _homography_guided(gA, gB, H_BA):
    """Total displacement A->B = homography + residual DIS flow measured on
    the pre-aligned pair (DIS alone fails on large motion)."""
    h, w = gA.shape
    Bw = cv2.warpPerspective(gB, H_BA, (w, h), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_REFLECT)
    r = _dis(gA, Bw)                        # A[x] ~ Bw[x + r]
    gx, gy = _grid(h, w)
    pts = np.stack([gx + r[..., 0], gy + r[..., 1]], -1).reshape(-1, 1, 2)
    src = cv2.perspectiveTransform(pts, np.linalg.inv(H_BA)).reshape(h, w, 2)
    return np.stack([src[..., 0] - gx, src[..., 1] - gy], -1).astype(np.float32)


def consistency_weight(dAB, dBA, cfg=TCFG):
    """exp(-e^2 / 2 sigma^2) with e = forward-backward error, per A pixel."""
    h, w = dAB.shape[:2]
    gx, gy = _grid(h, w)
    back = cv2.remap(dBA, gx + dAB[..., 0], gy + dAB[..., 1],
                     cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    err = np.linalg.norm(dAB + back, axis=2)
    s = cfg["consistency_sigma"]
    return np.exp(-(err ** 2) / (2 * s * s)).astype(np.float32)


def salient_box(img):
    """Cheap saliency: gradient energy, blurred, thresholded at its 70th
    percentile, largest blob's bounding box. Enough to bring a face and a
    cloud roughly on top of each other; anchors do the rest."""
    g = gray_of(img) if img.ndim == 3 else img
    e = cv2.magnitude(cv2.Sobel(g, cv2.CV_32F, 1, 0),
                      cv2.Sobel(g, cv2.CV_32F, 0, 1))
    e = cv2.GaussianBlur(e, (0, 0), max(3, min(g.shape) / 40))
    m = (e > np.percentile(e, 70)).astype(np.uint8)
    n, _, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n <= 1:
        h, w = g.shape
        return 0, 0, w, h
    i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    x, y, w, h = st[i, :4]
    return int(x), int(y), int(w), int(h)


def _box_center(box):
    x, y, w, h = box
    return (x + w / 2.0, y + h / 2.0)


def panzoom_field(h, w, pivot, toward, zoom):
    """Displacement of a frame that zooms in by `zoom` about `pivot` and
    pans toward `toward`, capped so the frame keeps covering the canvas:
        x -> x + zoom * (x - pivot) + tau
    The frame's left edge lands at tau - zoom * px and its right edge at
    w + zoom * (w - px) + tau, so the canvas stays covered at every
    fraction t of the field iff -zoom * (w - px) <= tau <= zoom * px (the
    same in y). The wanted pan keeps its direction and is scaled by the
    largest feasible fraction. Returns (disp float32 HxWx2, pan_fraction)."""
    px, py = float(pivot[0]), float(pivot[1])
    want = np.array([toward[0] - px, toward[1] - py], np.float64)
    lo = np.array([-zoom * (w - px), -zoom * (h - py)])
    hi = np.array([zoom * px, zoom * py])
    frac = 1.0
    for i in range(2):
        if want[i] > 1e-9:
            frac = min(frac, hi[i] / want[i])
        elif want[i] < -1e-9:
            frac = min(frac, lo[i] / want[i])
    frac = max(0.0, frac)
    tau = want * frac
    gx, gy = _grid(h, w)
    disp = np.stack([zoom * (gx - px) + tau[0], zoom * (gy - py) + tau[1]], -1)
    return disp.astype(np.float32), float(frac)


def mls_affine(p_src, p_dst, h, w, alpha=1.0, stride=8):
    """Moving Least Squares (affine) deformation, Schaefer et al. 2006.
    Returns a dense displacement (h, w, 2) mapping the source grid onto
    the destination, evaluated on a coarse grid and bilinearly upsampled
    (smoothness is the point). p_src, p_dst: (n, 2) px, n >= 3."""
    p = np.asarray(p_src, np.float64)
    q = np.asarray(p_dst, np.float64)
    ys = np.arange(0, h, stride, dtype=np.float64)
    xs = np.arange(0, w, stride, dtype=np.float64)
    gx, gy = np.meshgrid(xs, ys)
    v = np.stack([gx, gy], -1).reshape(-1, 2)           # (m, 2)
    d2 = ((v[:, None, :] - p[None, :, :]) ** 2).sum(-1) + 1e-6
    wgt = 1.0 / d2 ** alpha                              # (m, n)
    ws = wgt.sum(1, keepdims=True)
    pstar = (wgt @ p) / ws
    qstar = (wgt @ q) / ws
    ph = p[None, :, :] - pstar[:, None, :]               # (m, n, 2)
    qh = q[None, :, :] - qstar[:, None, :]
    M = np.einsum("mn,mni,mnj->mij", wgt, ph, ph)        # (m, 2, 2)
    Bm = np.einsum("mn,mni,mnj->mij", wgt, ph, qh)
    M += np.eye(2)[None] * 1e-6
    T = np.linalg.solve(M, Bm)                           # (m, 2, 2)
    f = np.einsum("mi,mij->mj", v - pstar, T) + qstar
    disp = (f - v).reshape(len(ys), len(xs), 2).astype(np.float32)
    return cv2.resize(disp, (w, h), interpolation=cv2.INTER_LINEAR)


def border_weight(h, w, falloff):
    """A weight that is 1 in the interior and falls smoothly to 0 at the
    canvas border over `falloff` * min(h, w) px (smoothstep). Multiplying an
    anchored field by it pins the border, so the moved frame keeps covering
    the canvas and no frame edge walks through the picture (backlog T16,
    the anchors twin of T13)."""
    gx, gy = _grid(h, w)
    dist = np.minimum(np.minimum(gx, w - 1 - gx), np.minimum(gy, h - 1 - gy))
    t = np.clip(dist / max(1.0, falloff * min(h, w)), 0.0, 1.0)
    return (t * t * (3.0 - 2.0 * t)).astype(np.float32)


def _invert_disp(d):
    """Approximate inverse of a smooth displacement field: forward-splat
    -d, fill the gaps by inpainting, smooth. Adequate for similarity and
    MLS fields."""
    h, w = d.shape[:2]
    gx, gy = _grid(h, w)
    tx = np.rint(gx + d[..., 0]).astype(int).ravel()
    ty = np.rint(gy + d[..., 1]).astype(int).ravel()
    ok = (tx >= 0) & (tx < w) & (ty >= 0) & (ty < h)
    inv = np.zeros_like(d)
    cnt = np.zeros((h, w), np.float32)
    np.add.at(inv, (ty[ok], tx[ok]), -d.reshape(-1, 2)[ok])
    np.add.at(cnt, (ty[ok], tx[ok]), 1.0)
    inv /= np.maximum(cnt, 1)[..., None]
    hole = (cnt == 0).astype(np.uint8)
    if hole.any():
        for c in range(2):
            q = (inv[..., c] * 16 + 32768).astype(np.uint16)
            q = cv2.inpaint(q, hole, 5, cv2.INPAINT_TELEA).astype(np.float32)
            inv[..., c] = (q - 32768) / 16
    return cv2.GaussianBlur(inv, (0, 0), 2)



# ---------------------------------------------------------------------------
# Depth: the disparity behind --camera (TR10, 2026-09-23)
#
# `ramp` is weight-free: disparity 0 at the top row and 1 at the bottom, a
# landscape prior (correlates 0.62-0.93 with the model on the two landscape
# fixtures). `model` is Depth Anything V2 Small (Apache-2.0, 24.8 M
# parameters, 99 MB) through transformers, on the CPU, with the same offline
# shape as reveal.py's learned matcher (its decisions 24-27): the weights
# live in models/depth/ (HF_HOME pinned there), `transitions.py warmup` is
# the ONLY command that downloads, it proves the model with a real forward
# pass and records every file's sha256 in models/DEPTH_MANIFEST.json, and a
# run refuses to start the model without an intact manifest. torch and
# transformers are imported lazily inside this section only (harness 3).
# ---------------------------------------------------------------------------

MODELS_DIR = Path(__file__).resolve().parent / "models"
DEPTH_DIR = MODELS_DIR / "depth"               # HF_HOME for this tool
DEPTH_MANIFEST = MODELS_DIR / "DEPTH_MANIFEST.json"
DEPTH_MODEL = "depth-anything/Depth-Anything-V2-Small-hf"
# The model card's preprocessor_config.json (DPTImageProcessor): resize so
# the scale is as close to 1 as possible (the short side lands on 518),
# both sides a multiple of 14, bicubic, no padding, ImageNet statistics.
# Done here with cv2 so the tool needs no torchvision; warmup checks the
# card's file against these constants.
DEPTH_PREP = {"size": 518, "multiple": 14,
              "mean": (0.485, 0.456, 0.406), "std": (0.229, 0.224, 0.225)}
_ALLOW_DOWNLOAD = False   # ONLY `transitions.py warmup` ever flips this
_DEPTH = None             # the loaded model, once per process


def _pin_hf_home():
    """Pin the Hugging Face cache INSIDE the project (models/depth/), so the
    project folder is self-contained and no cache cleaner can force a
    silent re-download mid-job. Offline is declared to the library as
    well; the manifest gate below is the guard that matters."""
    DEPTH_DIR.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(DEPTH_DIR)
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    if not _ALLOW_DOWNLOAD:
        os.environ["HF_HUB_OFFLINE"] = "1"
    for name in ("httpx", "huggingface_hub", "transformers"):
        logging.getLogger(name).setLevel(logging.WARNING)
    return DEPTH_DIR


def depth_available():
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
        return True
    except Exception:
        return False


def depth_manifest():
    """The record `warmup` writes after downloading AND verifying the model
    with a real forward pass. Its presence is the only proof that
    --camera model is offline-ready."""
    try:
        return json.loads(DEPTH_MANIFEST.read_text())
    except Exception:
        return None


def _depth_files():
    """(files, links) under the cache: regular files as (relative name,
    size, sha256), symlinks as (name, target). huggingface_hub 1.x keeps
    a large blob in a shared store (hub/blobs/<xx>/<hash>) and links the
    repo's blob to it, so the whole hub folder is walked, not the repo's
    folder alone; locks and dot-files are bookkeeping and skipped."""
    files, links = [], []
    root = DEPTH_DIR / "hub"
    for p in sorted(root.rglob("*")):
        rel = str(p.relative_to(DEPTH_DIR))
        parts = p.relative_to(DEPTH_DIR).parts
        if any(part.startswith(".") for part in parts) or p.suffix in (".lock", ".refs"):
            continue
        if p.is_symlink():
            links.append({"name": rel, "target": os.readlink(p)})
        elif p.is_file():
            b = p.read_bytes()
            files.append({"name": rel, "size": len(b),
                          "sha256": hashlib.sha256(b).hexdigest()})
    return files, links


def depth_weights_cached(deep=False):
    """True when every file warmup recorded is present with its size (and
    its sha256 when deep) and every snapshot link resolves."""
    man = depth_manifest()
    if not man or not man.get("files") or not man.get("verified"):
        return False
    for f in man["files"]:
        p = DEPTH_DIR / f["name"]
        if not p.is_file() or p.stat().st_size != f["size"]:
            return False
        if deep and hashlib.sha256(p.read_bytes()).hexdigest() != f["sha256"]:
            return False
    for l in man.get("links", []):
        p = DEPTH_DIR / l["name"]
        if not (p.is_symlink() and p.exists()):
            return False
    return True


def _depth_status():
    if not depth_available():
        return "off (optional; ./setup.sh --learned)"
    if not depth_weights_cached():
        return "installed, but model files are MISSING: transitions.py warmup"
    man = depth_manifest()
    mb = sum(f["size"] for f in man["files"]) / 1e6
    intact = depth_weights_cached(deep=True)
    return (f"ready, offline ({man['model'].split('/')[-1]}, "
            f"{len(man['files'])} files, {mb:.0f} MB in ./models/depth"
            + ("" if intact else ", CHECKSUM MISMATCH: re-run warmup") + ")")


def _depth_model():
    """Depth Anything V2 Small, loaded once, CPU. Refuses without the
    manifest: a job never downloads (the same rule as reveal.py)."""
    global _DEPTH
    if _DEPTH is not None:
        return _DEPTH
    if not depth_available():
        raise TransitionError(
            "--camera model needs the optional learned dependencies (torch, "
            "transformers). Run:  ./setup.sh --learned")
    if not _ALLOW_DOWNLOAD and not depth_weights_cached():
        raise TransitionError(
            "The depth model files are not installed or not intact. Run:  "
            "transitions.py warmup  (or ./setup.sh --learned). A run never "
            "downloads.")
    _pin_hf_home()
    import torch
    import transformers
    from transformers import AutoModelForDepthEstimation
    transformers.logging.set_verbosity_error()
    transformers.logging.disable_progress_bar()
    torch.set_grad_enabled(False)
    _DEPTH = AutoModelForDepthEstimation.from_pretrained(
        DEPTH_MODEL, cache_dir=str(DEPTH_DIR / "hub"),
        local_files_only=not _ALLOW_DOWNLOAD).eval()
    return _DEPTH


def _dpt_size(h, w, prep=DEPTH_PREP):
    """transformers' DPT rule (image_processing_dpt.get_resize_output_image_size
    with keep_aspect_ratio): the scale nearer to 1 wins, then each side is
    rounded to a multiple of 14."""
    sh, sw = prep["size"] / h, prep["size"] / w
    if abs(1 - sw) < abs(1 - sh):
        sh = sw
    else:
        sw = sh
    m = prep["multiple"]
    return int(round(sh * h / m) * m), int(round(sw * w / m) * m)


def model_disparity(rgb, cfg=TCFG):
    """Relative inverse depth of one image from Depth Anything V2 Small,
    0 (far) .. 1 (near) at the image's own size. Deterministic on the CPU
    (two runs byte-identical, harness 49)."""
    import torch
    m = _depth_model()
    h, w = rgb.shape[:2]
    s = cfg["depth_long"] / float(max(h, w))
    small = (cv2.resize(rgb, (int(round(w * s)), int(round(h * s))),
                        interpolation=cv2.INTER_AREA) if s < 1 else rgb)
    nh, nw = _dpt_size(small.shape[0], small.shape[1])
    x = cv2.resize(small, (nw, nh), interpolation=cv2.INTER_CUBIC)
    x = (x.astype(np.float32) / 255.0 - np.float32(DEPTH_PREP["mean"])) \
        / np.float32(DEPTH_PREP["std"])
    t = torch.from_numpy(np.ascontiguousarray(x.transpose(2, 0, 1)))[None]
    with torch.no_grad():
        d = m(pixel_values=t).predicted_depth[0].float().cpu().numpy()
    d = cv2.resize(d, (w, h), interpolation=cv2.INTER_CUBIC)
    return _normalize_disparity(d, cfg)


def _normalize_disparity(d, cfg=TCFG):
    lo, hi = np.percentile(d, cfg["depth_percentiles"])
    return np.clip((d - lo) / max(hi - lo, 1e-6), 0, 1).astype(np.float32)


def ramp_disparity(h, w):
    """The weight-free landscape prior: 0 at the top row, 1 at the bottom."""
    return np.repeat(np.linspace(0, 1, h, dtype=np.float32)[:, None], w, 1)


def depth_modulate(disp, d, cfg=TCFG):
    """Scale a displacement field by the disparity so near content moves
    more: factor 1 - gain/2 + gain * d (0.5 .. 1.5 at gain 1). Every
    factor is positive, so a field that keeps the frame covering the
    canvas still does (the edge condition is a sign condition). Returns
    (field, splat importance floor + (1 - floor) * d)."""
    g = cfg["depth_gain"]
    fac = (1.0 - g / 2.0 + g * d).astype(np.float32)
    imp = (cfg["depth_w_floor"] + (1.0 - cfg["depth_w_floor"]) * d).astype(np.float32)
    return (disp * fac[..., None]).astype(np.float32), imp


def _selftest_scene(w=640, h=400):
    """A sky gradient over a checkerboard floor in one-point perspective:
    the bottom rows are nearer than the top rows, which the model must
    report (warmup and harness 49 assert it). No random source."""
    img = np.zeros((h, w, 3), np.uint8)
    hz = int(h * 0.42)
    for y in range(hz):
        img[y] = (int(90 + 100 * y / hz), int(140 + 80 * y / hz), 230)
    fy = 300.0
    for y in range(hz, h):
        z = fy / max(y - hz, 1)
        xs = (np.arange(w) - w / 2.0) * z / fy
        chk = ((np.floor(xs * 2) + np.floor(z * 2)) % 2).astype(np.uint8)
        img[y] = np.where(chk[:, None] == 1, np.uint8([200, 200, 200]),
                          np.uint8([60, 60, 60]))
    return img


def depth_selftest(disp):
    """(mean disparity of the top 20 % rows, of the bottom 20 % rows)."""
    h = disp.shape[0]
    return (round(float(disp[: int(h * 0.2)].mean()), 3),
            round(float(disp[int(h * 0.8):].mean()), 3))


def dense_displacement(A, B, anchors=None, force_class=None, cfg=TCFG,
                       camera="flat", zoom=None, anchor_falloff=None):
    """Returns dict: dAB, dBA (float32 HxWx2 px), wA, wB (the splat's
    importance: the certainty in class A, 0.5 in class B, the depth
    importance under a camera move), cls ('A' | 'B'), method, diag.

    anchors: optional ((n,2), (n,2)) user control points, A px -> B px on
    the canvas. In class B they define the deformation (MLS); in class A
    they are blended in as a correction on top of the dense field.
    camera / zoom: the class B camera move (CAMERAS) and zoom fraction;
    `flat` at the default zoom is the field of 2026-09-14, byte for byte.
    A camera other than flat has no effect on class A or on anchors and
    says so on the log. anchor_falloff (default TCFG["anchor_falloff"], 0 =
    off): the anchored field is multiplied by border_weight so the border
    stays put (T16)."""
    if A.shape[:2] != B.shape[:2]:
        raise TransitionError("Endpoints must share a canvas.")
    h, w = A.shape[:2]
    gA, gB = gray_of(A), gray_of(B)
    sp = sparse_homography(gA, gB, cfg)
    have_h = bool(sp) and _sane(sp[0], B.shape, cfg)
    cls = force_class or ("A" if (have_h and sp[1] >= cfg["min_inliers"])
                          else "B")
    diag = {"sparse_inliers": sp[1] if sp else 0,
            "sparse_rmse": None if not sp else round(sp[2], 2)}
    n_anchor = 0 if anchors is None else len(anchors[0])
    falloff = cfg["anchor_falloff"] if anchor_falloff is None else float(anchor_falloff)
    bw = border_weight(h, w, falloff)[..., None] if (n_anchor >= 3 and falloff > 0) else None

    if camera != "flat" and (cls == "A" or n_anchor >= 3):
        log.info("camera: %s requested, but the pair is class %s%s; the camera "
                 "move applies to the class B pan-and-zoom only", camera, cls,
                 " with anchors" if n_anchor >= 3 else "")
    if cls == "A":
        H = sp[0] if have_h else np.eye(3)
        dAB = _homography_guided(gA, gB, H)
        dBA = _homography_guided(gB, gA, np.linalg.inv(H))
        wA = consistency_weight(dAB, dBA, cfg)
        wB = consistency_weight(dBA, dAB, cfg)
        method = "homography+dis" if have_h else "dis-only"
        if n_anchor >= 3:
            corr = mls_affine(anchors[0], anchors[1], h, w) - dAB
            if bw is not None:
                corr = corr * bw
            dAB = dAB + cfg["anchor_blend"] * corr
            dBA = _invert_disp(dAB)
            method += "+anchors" + ("+falloff" if bw is not None else "")
    else:
        if n_anchor >= 3:
            dAB = mls_affine(anchors[0], anchors[1], h, w)
            if bw is not None:
                dAB = dAB * bw
                log.info("anchors: border falloff %.2f of the short edge; the frame "
                         "edge stays on the canvas edge", falloff)
            dBA = _invert_disp(dAB)
            method = "mls-anchors" + ("+falloff" if bw is not None else "")
            steer = ""
        else:
            # Each frame zooms in about its own salient center and pans
            # toward the other frame's as far as the zoom's slack allows,
            # so neither frame's edge enters the canvas (defect T13). A
            # zooms from 1 to 1+z while it fades out; B settles from 1+z
            # to 1 so the last frame is B itself. The two salient centers
            # meet throughout only when neither pan is capped.
            cA, cB = _box_center(salient_box(A)), _box_center(salient_box(B))
            z = cfg["classb_zoom"] if zoom is None else float(zoom)
            dAB, fA = panzoom_field(h, w, cA, cB, z)
            dBA, fB = panzoom_field(h, w, cB, cA, z)
            method = "saliency-panzoom"
            diag["pan_fraction"] = [round(fA, 2), round(fB, 2)]
            diag["camera"], diag["zoom"] = camera, round(z, 3)
            steer = (f"; zoom {z:.0%}, pan {fA:.0%} / {fB:.0%} of the way "
                     f"between the salient centers; camera {camera}")
        wA = np.full((h, w), 0.5, np.float32)   # honest: no photometric proof
        wB = wA.copy()
        if camera != "flat" and n_anchor < 3:
            # the camera move: near content moves more and wins collisions
            if camera == "model":
                dA_, dB_ = model_disparity(A, cfg), model_disparity(B, cfg)
            else:
                dA_ = dB_ = ramp_disparity(h, w)
            dAB, wA = depth_modulate(dAB, dA_, cfg)
            dBA, wB = depth_modulate(dBA, dB_, cfg)
            method += "+" + camera
            diag["disparity_mean"] = [round(float(dA_.mean()), 3),
                                      round(float(dB_.mean()), 3)]
        # the degrade path is visible, never silent
        log.info("correspondence: class B (%s) — no geometric correspondence "
                 "(%d sparse inliers)%s; pass --anchors to steer the morph",
                 method, diag["sparse_inliers"], steer)
    diag.update({"mean_certainty": round(float(wA.mean()), 3),
                 "median_disp_px": round(float(np.median(
                     np.linalg.norm(dAB, axis=2))), 2)})
    return {"dAB": dAB, "dBA": dBA, "wA": wA, "wB": wB, "cls": cls,
            "method": method, "diag": diag}


# ---------------------------------------------------------------------------
# Warp: importance-weighted forward splat, backward warp, the halfway morph
#
# A pixel a travels to a + t*dAB(a); a B pixel b travels to b + (1-t)*dBA(b).
# Both are FORWARD warps toward the same intermediate frame. Collisions are
# resolved by importance weights (a simplified softmax splatting, Niklaus &
# Liu CVPR 2020); holes fall back to a backward-warp estimate.
# ---------------------------------------------------------------------------

def backward_warp(img, disp):
    """out[y, x] = img[y + dy, x + dx] with disp on the OUTPUT grid."""
    h, w = disp.shape[:2]
    gx, gy = _grid(h, w)
    return cv2.remap(img, gx + disp[..., 0], gy + disp[..., 1],
                     cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def forward_splat(img, disp, t, importance=None, cfg=TCFG):
    """Splat img along t*disp into a target buffer of the same size.

    The field is smooth, so the splat runs on SOURCE COORDINATES at
    1/scale resolution (importance-weighted collision handling) to build an
    inverse map, which is upsampled and applied to the full-resolution
    colors with one cv2.remap: colors are sampled once, bilinearly, from
    the pristine source, and the scatter touches scale^2 fewer elements.

    importance (h, w) in [0, 1]: higher wins collisions.
    Returns (rgb float32, cover) where cover ~1 where the target received
    source pixels and ~0 in true holes (disocclusions)."""
    scale = cfg["splat_scale"]
    h, w = img.shape[:2]
    hs, ws = max(2, h // scale), max(2, w // scale)
    d = cv2.resize(disp, (ws, hs), interpolation=cv2.INTER_AREA) * (t / scale)
    imp = (np.ones((hs, ws), np.float32) if importance is None else
           cv2.resize(importance, (ws, hs), interpolation=cv2.INTER_AREA))
    wgt = np.exp(cfg["splat_sharpness"] * (imp - 1.0)).astype(np.float32)
    gx, gy = _grid(hs, ws)
    tx, ty = gx + d[..., 0], gy + d[..., 1]
    x0 = np.floor(tx).astype(np.int32)
    y0 = np.floor(ty).astype(np.int32)
    fx = (tx - x0).astype(np.float32)
    fy = (ty - y0).astype(np.float32)
    n = hs * ws
    accx = np.zeros(n, np.float64)
    accy = np.zeros(n, np.float64)
    cov_w = np.zeros(n, np.float64)
    cov_raw = np.zeros(n, np.float64)
    sx, sy, wf = gx.ravel(), gy.ravel(), wgt.ravel()
    for dx, dy, bw in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)),
                       (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        xs = (x0 + dx).ravel()
        ys = (y0 + dy).ravel()
        bwr = bw.ravel()
        ok = (xs >= 0) & (xs < ws) & (ys >= 0) & (ys < hs) & (bwr > 1e-6)
        idx = ys[ok] * ws + xs[ok]
        ww = bwr[ok] * wf[ok]
        accx += np.bincount(idx, weights=sx[ok] * ww, minlength=n)
        accy += np.bincount(idx, weights=sy[ok] * ww, minlength=n)
        cov_w += np.bincount(idx, weights=ww, minlength=n)
        cov_raw += np.bincount(idx, weights=bwr[ok], minlength=n)
    inv_x = (accx / np.maximum(cov_w, 1e-12)).reshape(hs, ws).astype(np.float32)
    inv_y = (accy / np.maximum(cov_w, 1e-12)).reshape(hs, ws).astype(np.float32)
    cov = cov_raw.reshape(hs, ws).astype(np.float32)
    # true holes: the negated forward displacement keeps the map defined
    # everywhere before upsampling (adequate for smooth fields)
    hole = cov < cfg["hole_thresh"]
    inv_x[hole] = (gx - d[..., 0])[hole]
    inv_y[hole] = (gy - d[..., 1])[hole]
    # Upsample the inverse DISPLACEMENT, never absolute coordinates: resize
    # aligns pixel centers, so upsampling coordinates by `scale` would shift
    # everything by (scale-1)/2 px (1.5 px at scale 4, a 13-level error).
    inv_dx = cv2.resize(inv_x - gx, (w, h), interpolation=cv2.INTER_LINEAR) * scale
    inv_dy = cv2.resize(inv_y - gy, (w, h), interpolation=cv2.INTER_LINEAR) * scale
    GX, GY = _grid(h, w)
    rgb = cv2.remap(img, GX + inv_dx, GY + inv_dy, cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    cover_map = cv2.resize(np.minimum(cov, 1.0), (w, h),
                           interpolation=cv2.INTER_LINEAR)
    return rgb, cover_map


def fill_holes(rgb, cov, fallback, thresh):
    """Where coverage is below thresh, take the fallback. In place: rgb is
    the fresh array forward_splat returned, nobody else holds it."""
    hole = cov < thresh
    rgb[hole] = fallback[hole]
    return rgb


def morph_frame(A, B, corr, t_warp, t_mix, cfg=TCFG):
    """One intermediate frame. t_warp: geometric progress along the
    correspondence; t_mix: cross-dissolve weight toward B. uint8 RGB."""
    dAB, dBA = corr["dAB"], corr["dBA"]
    IA, cA = forward_splat(A, dAB, t_warp, corr["wA"], cfg)
    IB, cB = forward_splat(B, dBA, 1.0 - t_warp, corr["wB"], cfg)
    # backward-warp fallbacks approximate the inverse map by negating the
    # forward displacement sampled at the target (fine for smooth fields)
    fA = backward_warp(A, -t_warp * dAB).astype(np.float32)
    fB = backward_warp(B, -(1.0 - t_warp) * dBA).astype(np.float32)
    th = cfg["hole_thresh"]
    IA = fill_holes(IA, cA, fA, th)
    IB = fill_holes(IB, cB, fB, th)
    # coverage-aware mix: where one side has no support, lean on the other
    mix = np.full(cA.shape, t_mix, np.float32)
    mix = np.where(cA < th, 1.0, mix)
    mix = np.where(cB < th, 0.0, mix)
    mix = cv2.GaussianBlur(mix, (0, 0), cfg["mix_blur"])[..., None]
    return to_u8(IA * (1 - mix) + IB * mix)


def portal_mask(h, w, t, kind="iris", feather=0.08, center=(0.5, 0.5)):
    """Reveal masks for the portal style: 0 = A, 1 = B. Feather is a
    fraction of the diagonal. iris grows a circle from center; wipe sweeps
    a seam left to right (left of the seam shows B, like Reveal's video)."""
    gx, gy = _grid(h, w)
    fd = feather * float(np.hypot(w, h))
    if kind == "wipe":
        seam = t * (w + 2 * fd) - fd
        m = (seam - gx) / fd + 0.5
    else:
        cx, cy = center[0] * w, center[1] * h
        r = np.hypot(gx - cx, gy - cy)
        rmax = max(np.hypot(cx, cy), np.hypot(w - cx, cy),
                   np.hypot(cx, h - cy), np.hypot(w - cx, h - cy))
        edge = t * (rmax + fd)
        m = (edge - r) / fd + 0.5
    return np.clip(m, 0, 1).astype(np.float32)


# ---------------------------------------------------------------------------
# Color path: time-varying Lab statistics (Reinhard 2001 lineage). Both
# endpoints are pulled toward an interpolated target statistic so their
# colors MEET halfway instead of one snapping to the other at the cut.
# ---------------------------------------------------------------------------

def lab_of(img):
    """float32 Lab of an sRGB uint8 image (L 0..100, a/b about -127..127).
    Converted ONCE per endpoint per transition: the RGB->Lab half of the
    color path was 17 % of a morph frame at 1080p (profile 2026-09-13)."""
    return cv2.cvtColor(img.astype(np.float32) / 255.0, cv2.COLOR_RGB2Lab)


def lab_stats(img, mask=None, lab=None):
    lab = lab_of(img) if lab is None else lab
    sel = np.ones(lab.shape[:2], bool) if mask is None else (mask > 0)
    if sel.sum() < 64:
        sel = np.ones(lab.shape[:2], bool)
    return np.array([[lab[..., c][sel].mean(), lab[..., c][sel].std() + 1e-6]
                     for c in range(3)], np.float32)          # (3, 2)


def lerp_stats(sa, sb, u):
    return sa * (1.0 - u) + sb * u


def apply_stats(img, src_stats, dst_stats, strength=1.0, cfg=TCFG,
                lab=None, src=None):
    """Move img's Lab statistics from src_stats toward dst_stats. The
    correction is applied in float and rounded ONCE, so strength scales it
    continuously and identical statistics give the input back.
    lab / src: the caller may pass img's Lab (from lab_of) and float32
    copy, computed once per transition; the result is byte-identical."""
    if strength <= 0:
        return img
    if src is None:
        src = img.astype(np.float32)
    if lab is None:
        lab = lab_of(img)
    lo, hi = cfg["color_gain_clip"]
    out = np.empty_like(lab)
    for c in range(3):
        m0, s0 = src_stats[c]
        m1, s1 = dst_stats[c]
        gain = float(np.clip(s1 / s0, lo, hi))
        out[..., c] = (lab[..., c] - m0) * gain + m1
    out = cv2.cvtColor(out, cv2.COLOR_Lab2RGB) * 255.0
    return to_u8(src + strength * (out - src))


def color_pair_at(A, B, sA, sB, u, strength, cfg=TCFG, cache=None):
    """Pull A and B toward the statistic at position u of the path.
    cache: optional (labA, srcA, labB, srcB) from color_cache()."""
    target = lerp_stats(sA, sB, u)
    labA, srcA, labB, srcB = cache if cache is not None else (None,) * 4
    return (apply_stats(A, sA, target, strength, cfg, labA, srcA),
            apply_stats(B, sB, target, strength, cfg, labB, srcB))


def color_cache(A, B):
    """Per-transition constants of the color path: Lab and float32 copies
    of both endpoints (four full-resolution arrays)."""
    return (lab_of(A), A.astype(np.float32), lab_of(B), B.astype(np.float32))


def luma_mask(img, t, softness=0.15, bright_first=True):
    """Luma wipe: reveal B in order of A's brightness. t in [0, 1]."""
    L = gray_of(img).astype(np.float32) / 255.0
    if not bright_first:
        L = 1.0 - L
    thr = 1.0 - t * (1.0 + softness) + softness * 0.5
    m = (L - thr) / softness + 0.5
    return np.clip(m, 0, 1).astype(np.float32)


# ---------------------------------------------------------------------------
# Quality basket: several numbers, never one pretending to be the truth
# (pixel scales are scene-dependent; compare a pair against itself).
#   warping_error     mean |I_{t+1} - warp(I_t, flow)| on 0..1 gray: the
#                     classic blind temporal-consistency metric
#   flicker           adjacent-frame change; edge_ratio is the hidden-cut
#                     detector (an endpoint step far above the interior)
#   endpoint_fidelity first/last frame vs the inputs (must be 0)
#   goal              the numbers that see what the owner grades (2026-09-26,
#                     retrospective §5; calibrated on 343 graded clips):
#     feat_floor      min over interior frames of SIFT matches to A / nA +
#                     matches to B / nB — details of A or B must survive
#     laplace_floor   min over interior frames of Laplacian variance /
#                     the endpoints' interpolated value — sharpness kept
#     contrast_floor  the same on the median patch std — local contrast kept
#     dissolve_fit    mean R^2 of (I[t+1]-I[t]) ~ beta (B-A): the share of
#                     the change a plain crossfade explains (dissolve ~1)
#     motion_share    mean (|dI| - |dI after DIS warp|) / |dI|: the share
#                     of the change that motion explains (crossfade ~0)
# The first three screen defects; `goal` grades the transition. A number
# means nothing across pairs: compare a pair against itself.
# All computed on a proxy of long edge TCFG["quality_long"] so 4K is cheap.
# ---------------------------------------------------------------------------

def _g(f):
    return cv2.cvtColor(f, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0


def warping_error(frames):
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_FAST)
    errs = []
    for a, b in zip(frames[:-1], frames[1:]):
        ga, gb = _g(a), _g(b)
        f = dis.calc((ga * 255).astype(np.uint8), (gb * 255).astype(np.uint8),
                     None)
        h, w = ga.shape
        gx, gy = _grid(h, w)
        wb = cv2.remap(gb, gx + f[..., 0], gy + f[..., 1], cv2.INTER_LINEAR)
        errs.append(float(np.abs(wb - ga).mean()))
    return float(np.mean(errs)) if errs else 0.0


def flicker(frames):
    d = [float(np.abs(_g(a) - _g(b)).mean())
         for a, b in zip(frames[:-1], frames[1:])]
    if not d:
        return {"mean": 0.0, "max": 0.0, "spikiness": 0.0, "edge_ratio": 0.0}
    interior = d[1:-1] if len(d) > 2 else d
    return {"mean": float(np.mean(d)), "max": float(np.max(d)),
            "spikiness": float(np.max(d) / (np.mean(d) + 1e-6)),
            "edge_ratio": float(max(d[0], d[-1]) / (np.mean(interior) + 1e-6))}


def endpoint_fidelity(frames, A, B):
    return {"first_vs_A": float(np.abs(frames[0].astype(int)
                                       - A.astype(int)).mean()),
            "last_vs_B": float(np.abs(frames[-1].astype(int)
                                      - B.astype(int)).mean())}


def _gray8(f):
    return cv2.cvtColor(f, cv2.COLOR_RGB2GRAY)


def _patch_std_median(g, patch):
    g = g.astype(np.float32)
    h, w = g.shape
    hh, ww = h // patch * patch, w // patch * patch
    if hh == 0 or ww == 0:
        return float(g.std())
    p = g[:hh, :ww].reshape(hh // patch, patch, ww // patch, patch)
    return float(np.median(p.transpose(0, 2, 1, 3).std(axis=(2, 3))))


def _sift_matches(des_q, des_t, bf):
    if des_q is None or des_t is None or len(des_q) < 2 or len(des_t) < 2:
        return 0
    good = 0
    for m in bf.knnMatch(des_q, des_t, k=2):
        if len(m) == 2 and m[0].distance < 0.75 * m[1].distance:
            good += 1
    return good


def goal_numbers(frames, cfg=TCFG):
    """The goal numbers on a list of uint8 RGB frames (proxies), the first
    and last being the endpoints. See the section comment. Frames with no
    interior (n < 3) give zeros."""
    n = len(frames)
    if n < 3:
        return {"feat_floor": 0.0, "laplace_floor": 0.0, "contrast_floor": 0.0,
                "dissolve_fit": 0.0, "motion_share": 0.0}
    gs = [_gray8(f) for f in frames]
    A, B = gs[0], gs[-1]
    sift = cv2.SIFT_create(nfeatures=int(cfg["goal_features"]))
    bf = cv2.BFMatcher(cv2.NORM_L2)
    dA = sift.detectAndCompute(A, None)[1]
    dB = sift.detectAndCompute(B, None)[1]
    nA = len(dA) if dA is not None else 0
    nB = len(dB) if dB is not None else 0
    patch = int(cfg["goal_patch"])
    psA, psB = _patch_std_median(A, patch), _patch_std_median(B, patch)
    lvA = float(cv2.Laplacian(A, cv2.CV_32F).var())
    lvB = float(cv2.Laplacian(B, cv2.CV_32F).var())
    feat, lap, con = [], [], []
    for i in range(1, n - 1):
        u = i / (n - 1)
        g = gs[i]
        d = sift.detectAndCompute(g, None)[1]
        feat.append(_sift_matches(d, dA, bf) / max(1, nA)
                    + _sift_matches(d, dB, bf) / max(1, nB))
        lap.append(float(cv2.Laplacian(g, cv2.CV_32F).var())
                   / max(1e-6, (1 - u) * lvA + u * lvB))
        con.append(_patch_std_median(g, patch)
                   / max(1e-6, (1 - u) * psA + u * psB))
    e = (B.astype(np.float32) - A.astype(np.float32)).ravel()
    ee = float(np.dot(e, e)) + 1e-6
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_FAST)
    h, w = A.shape
    gx, gy = _grid(h, w)
    fits, shares = [], []
    for a, b in zip(gs[:-1], gs[1:]):
        dd = (b.astype(np.float32) - a.astype(np.float32)).ravel()
        beta = float(np.dot(dd, e)) / ee
        res = dd - beta * e
        fits.append(1.0 - float(np.dot(res, res)) / (float(np.dot(dd, dd)) + 1e-6))
        f = dis.calc(a, b, None)
        wb = cv2.remap(b, gx + f[..., 0], gy + f[..., 1], cv2.INTER_LINEAR)
        d_raw = float(np.abs(b.astype(np.float32) - a.astype(np.float32)).mean())
        d_warp = float(np.abs(wb.astype(np.float32) - a.astype(np.float32)).mean())
        shares.append((d_raw - d_warp) / max(d_raw, 1e-6))
    return {"feat_floor": round(float(min(feat)), 4),
            "laplace_floor": round(float(min(lap)), 4),
            "contrast_floor": round(float(min(con)), 4),
            "dissolve_fit": round(float(np.mean(fits)), 4),
            "motion_share": round(float(np.mean(shares)), 4)}


def assess(frames, A=None, B=None, cfg=TCFG):
    r = {"warping_error": round(warping_error(frames), 4),
         "flicker": {k: round(v, 4) for k, v in flicker(frames).items()},
         "goal": goal_numbers(frames, cfg),
         "n_frames": len(frames)}
    if A is not None and B is not None:
        r["endpoint"] = {k: round(v, 2)
                         for k, v in endpoint_fidelity(frames, A, B).items()}
    return r


def proxy_of(frame, long_edge=None):
    long_edge = long_edge or TCFG["quality_long"]
    h, w = frame.shape[:2]
    s = min(1.0, long_edge / max(h, w))
    if s >= 1.0:
        return frame
    return cv2.resize(frame, (max(2, round(w * s)), max(2, round(h * s))),
                      interpolation=cv2.INTER_AREA)


class StreamStats:
    """Collects, while frames stream to the encoder, what the report and
    the thumbnail strip need: a proxy of every frame and the strip tiles.
    Memory stays bounded whatever the canvas."""

    def __init__(self, n_frames, cfg=TCFG):
        self.cfg = cfg
        self.proxies = []
        k = min(cfg["strip_tiles"], n_frames)
        self.tile_at = set(np.linspace(0, n_frames - 1, k).round().astype(int))
        self.tiles = []

    def add(self, i, frame):
        self.proxies.append(proxy_of(frame, self.cfg["quality_long"]))
        if i in self.tile_at:
            hh = self.cfg["strip_height"]
            ww = max(2, int(frame.shape[1] * hh / frame.shape[0]))
            self.tiles.append(cv2.resize(frame, (ww, hh),
                                         interpolation=cv2.INTER_AREA))

    def strip(self):
        return np.concatenate(self.tiles, axis=1)

    def quality(self, A, B):
        q = assess(self.proxies, proxy_of(A, self.cfg["quality_long"]),
                   proxy_of(B, self.cfg["quality_long"]))
        q["proxy_long"] = self.cfg["quality_long"]
        return q


# ---------------------------------------------------------------------------
# Render: one transition from two endpoint frames and a TransitionSpec
# Per frame: color path -> geometry (morph / portal / luma mask) -> mix.
# Frames 0 and n-1 are the inputs themselves, byte-exact.
# ---------------------------------------------------------------------------

def _anchor_arrays(spec):
    if not spec.anchors:
        return None
    a = np.array(spec.anchors, np.float32).reshape(-1, 4)
    return a[:, :2], a[:, 2:]


def prepare(A, B, spec, cfg=TCFG):
    """Shared canvas + correspondence, computed once per transition.
    Returns (A_canvas, B_canvas, corr)."""
    w, h = common_canvas(A, B, spec.max_long_edge, spec.canvas)
    A2, B2 = cover(A, w, h), cover(B, w, h)
    t = time.time()
    corr = dense_displacement(A2, B2, anchors=_anchor_arrays(spec),
                              force_class=spec.force_class or None, cfg=cfg,
                              camera=spec.camera, zoom=spec.zoom,
                              anchor_falloff=spec.anchor_falloff)
    corr["diag"]["correspondence_s"] = round(time.time() - t, 2)
    return A2, B2, corr


def iter_frames(A, B, spec, corr, cfg=TCFG):
    """Yield the n_frames() uint8 RGB frames of the transition, A first,
    B last, exactly."""
    n = spec.n_frames()
    h, w = A.shape[:2]
    cache = color_cache(A, B)
    sA, sB = lab_stats(A, lab=cache[0]), lab_stats(B, lab=cache[2])
    for i in range(n):
        if i == 0:
            yield A.copy()
            continue
        if i == n - 1:
            yield B.copy()
            continue
        tw, tm, u = spec.progress(i)
        Ai, Bi = color_pair_at(A, B, sA, sB, u, spec.color_strength, cfg, cache)
        if spec.style in ("morph", "warp-dissolve"):
            f = morph_frame(Ai, Bi, corr, tw, tm, cfg)
        elif spec.style == "portal":
            m = portal_mask(h, w, tm, spec.portal, spec.portal_feather)[..., None]
            f = to_u8(Ai * (1 - m) + Bi * m)
        elif spec.style == "luma":
            m = luma_mask(Ai, tm)[..., None]
            f = to_u8(Ai * (1 - m) + Bi * m)
        else:                                       # dissolve
            f = to_u8(Ai.astype(np.float32) * (1 - tm) + Bi * tm)
        yield f


def render_frames(A, B, spec, corr=None, cfg=TCFG):
    """Convenience for small canvases (the harness): all frames in memory.
    Returns (frames, report)."""
    spec.clamp()
    if corr is None:
        A, B, corr = prepare(A, B, spec, cfg)
    t0 = time.time()
    frames = list(iter_frames(A, B, spec, corr, cfg))
    report = {"class": corr["cls"], "method": corr["method"], **corr["diag"],
              "render_s": round(time.time() - t0, 2), "n_frames": len(frames),
              "canvas": [A.shape[1], A.shape[0]]}
    return frames, report


# ---------------------------------------------------------------------------
# Encode: frames piped as rawvideo to the bundled ffmpeg (imageio-ffmpeg),
# H.264 yuv420p +faststart. Same shape as reveal.py's export_video.
# ---------------------------------------------------------------------------

class FrameEncoder:
    def __init__(self, path, w, h, fps, crf=None):
        if imageio_ffmpeg is None:
            raise TransitionError(
                f"Video export needs imageio-ffmpeg: {_FFMPEG_ERR}")
        self.path = Path(path)
        self.w, self.h = int(w), int(h)
        self.n = 0
        cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{self.w}x{self.h}", "-r", f"{float(fps):g}", "-i", "-",
               "-an", "-c:v", "libx264", "-preset", "medium",
               "-crf", str(crf if crf is not None else TCFG["video_crf"]),
               "-pix_fmt", "yuv420p", "-movflags", "+faststart",
               str(self.path)]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                     stderr=subprocess.PIPE)

    def write(self, frame):
        if frame.shape[1] != self.w or frame.shape[0] != self.h:
            raise TransitionError(
                f"Frame {frame.shape[1]}x{frame.shape[0]} does not match the "
                f"encoder canvas {self.w}x{self.h}")
        self.proc.stdin.write(np.ascontiguousarray(frame, np.uint8).tobytes())
        self.n += 1

    def close(self):
        try:
            self.proc.stdin.close()
            rc = self.proc.wait(timeout=600)
            if rc != 0:
                err = self.proc.stderr.read().decode("utf8", "replace")[:400]
                raise TransitionError(f"ffmpeg failed: {err}")
        finally:
            if self.proc.poll() is None:
                self.proc.kill()
        return self.n

    def abort(self):
        if self.proc.poll() is None:
            self.proc.kill()


def render_pair(A, B, spec, out_dir, cfg=TCFG):
    """The whole job for one photo pair: prepare, stream frames to
    transition.mp4, write strip.jpg and report.json. Returns the report."""
    spec.clamp()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    t_all = time.time()
    A2, B2, corr = prepare(A, B, spec, cfg)
    h, w = A2.shape[:2]
    n = spec.n_frames()
    stats = StreamStats(n, cfg)
    enc = FrameEncoder(out / "transition.mp4", w, h, spec.fps)
    t0 = time.time()
    try:
        for i, f in enumerate(iter_frames(A2, B2, spec, corr, cfg)):
            enc.write(f)
            stats.add(i, f)
        written = enc.close()
    except BaseException:
        enc.abort()
        raise
    render_s = round(time.time() - t0, 2)
    ok, buf = cv2.imencode(".jpg", cv2.cvtColor(stats.strip(), cv2.COLOR_RGB2BGR),
                           [cv2.IMWRITE_JPEG_QUALITY, 90])
    if ok:
        (out / "strip.jpg").write_bytes(buf.tobytes())
    report = {"tool_version": VERSION, "spec": asdict(spec),
              "class": corr["cls"], "method": corr["method"], **corr["diag"],
              "canvas": [w, h], "canvas_policy": spec.canvas, "n_frames": written,
              "render_s": render_s, "quality": stats.quality(A2, B2),
              "total_s": round(time.time() - t_all, 2),
              "outputs": ["transition.mp4", "strip.jpg", "report.json"]}
    (out / "report.json").write_text(json.dumps(report, indent=2))
    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_check():
    dis_ok = hasattr(cv2, "DISOpticalFlow_create")
    rows = [
        ("python", sys.version.split()[0], True),
        ("opencv", cv2.__version__, True),
        ("numpy", np.__version__, True),
        ("SIFT", "available" if hasattr(cv2, "SIFT_create") else "missing",
         hasattr(cv2, "SIFT_create")),
        ("MAGSAC++", "available" if hasattr(cv2, "USAC_MAGSAC")
         else "RANSAC fallback", True),
        ("DIS flow", "available" if dis_ok else "missing", dis_ok),
        ("HEIC decode", "ok" if pillow_heif else f"OFF ({_HEIF_ERR})",
         pillow_heif is not None),
        ("RAW decode", "ok" if rawpy else f"OFF ({_RAWPY_ERR})",
         rawpy is not None),
        ("video export", "ok" if imageio_ffmpeg else f"OFF ({_FFMPEG_ERR})",
         imageio_ffmpeg is not None),
        ("depth model", _depth_status(),
         (not depth_available()) or depth_weights_cached()),
    ]
    bad = 0
    for name, val, ok in rows:
        print(f"  {'OK ' if ok else '!! '}{name:<16} {val}")
        bad += 0 if ok else 1
    if bad:
        print(f"\n{bad} problem(s); re-run ./setup.sh")
    return 1 if bad else 0


def cmd_warmup():
    """Download EVERYTHING --camera model will ever need, prove it works
    with a real forward pass, and record it. After this, no run touches
    the network (the same shape as reveal.py warmup)."""
    global _ALLOW_DOWNLOAD, _DEPTH
    if not depth_available():
        print("The depth model's dependencies are not installed.\n"
              "Run:  ./setup.sh --learned")
        return 1
    _ALLOW_DOWNLOAD = True
    _DEPTH = None
    d = _pin_hf_home()
    print(f"Downloading {DEPTH_MODEL} into {d} ...")
    try:
        from huggingface_hub import hf_hub_download
        card = json.loads(Path(hf_hub_download(
            DEPTH_MODEL, "preprocessor_config.json",
            cache_dir=str(DEPTH_DIR / "hub"))).read_text())
        want = {"size": {"height": DEPTH_PREP["size"], "width": DEPTH_PREP["size"]},
                "ensure_multiple_of": DEPTH_PREP["multiple"],
                "keep_aspect_ratio": True, "do_pad": False, "resample": 3,
                "image_mean": list(DEPTH_PREP["mean"]),
                "image_std": list(DEPTH_PREP["std"])}
        drift = {k: card.get(k) for k, v in want.items() if card.get(k) != v}
        if drift:
            print(f"The model card's preprocessing differs from this tool's "
                  f"constants: {drift}. Not recorded; the tool stays as it was.")
            return 1
        # A REAL forward pass on the self-test scene: the floor must read
        # nearer than the sky. Any hidden lazy download happens here.
        top, bottom = depth_selftest(model_disparity(_selftest_scene()))
        if not bottom > top + 0.3:
            print(f"The model files downloaded but the self-test failed "
                  f"(top {top}, bottom {bottom}); --camera model stays off.")
            return 1
    except Exception as e:
        print(f"Could not prepare the depth model: {e}")
        return 1
    finally:
        _ALLOW_DOWNLOAD = False
    files, links = _depth_files()
    if not files:
        print("No model files were written. --camera model stays off.")
        return 1
    total = sum(f["size"] for f in files)
    DEPTH_MANIFEST.write_text(json.dumps(
        {"tool_version": VERSION, "model": DEPTH_MODEL, "verified": True,
         "self_test": {"top20_mean": top, "bottom20_mean": bottom},
         "prep": {k: list(v) if isinstance(v, tuple) else v
                  for k, v in DEPTH_PREP.items()},
         "files": files, "links": links}, indent=2))
    for f in files:
        print(f"  {f['name']}  {f['size']/1e6:.1f} MB")
    print(f"\nVerified: floor {bottom} nearer than sky {top} on the self-test scene.")
    print(f"{len(files)} file(s), {total/1e6:.1f} MB in {d}")
    print("--camera model is now fully offline. It will never download again.")
    return 0


def parse_anchors(text):
    """'ax,ay,bx,by;ax,ay,bx,by;...' in canvas pixels -> [[...], ...]."""
    out = []
    for tok in (text or "").split(";"):
        tok = tok.strip()
        if not tok:
            continue
        v = [float(x) for x in tok.split(",")]
        if len(v) != 4:
            raise TransitionError(
                f"Anchor {tok!r} must be four numbers ax,ay,bx,by")
        out.append(v)
    if out and len(out) < 3:
        raise TransitionError("At least three anchor pairs are needed.")
    return out


def cmd_pair(args):
    A = load_image_rgb(args.before)
    B = load_image_rgb(args.after)
    spec = spec_from(args.preset, seconds=args.seconds, fps=args.fps,
                     color_strength=args.color, warp_amount=args.warp,
                     max_long_edge=args.max_long, canvas=args.canvas,
                     anchors=parse_anchors(args.anchors),
                     anchor_falloff=args.anchor_falloff,
                     force_class=args.force_class,
                     camera=args.camera, zoom=args.zoom)
    report = render_pair(A, B, spec, args.out)
    print(json.dumps({k: v for k, v in report.items() if k != "spec"},
                     indent=2))
    print(f"Wrote {', '.join(report['outputs'])} in {Path(args.out).resolve()}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="transitions.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    pp = sub.add_parser("pair", help="render the transition between two photos")
    pp.add_argument("before")
    pp.add_argument("after")
    pp.add_argument("--out", required=True)
    pp.add_argument("--seconds", type=float, default=1.0)
    pp.add_argument("--fps", type=float, default=TCFG["fps"])
    pp.add_argument("--preset", default="morph", choices=list(PRESETS))
    pp.add_argument("--color", type=float, default=0.7,
                    help="color path strength 0..1")
    pp.add_argument("--warp", type=float, default=1.0,
                    help="geometric warp amount 0..1")
    pp.add_argument("--max-long", type=int, default=0,
                    help="cap the canvas long edge (0 = native)")
    pp.add_argument("--canvas", default="finish", choices=list(CANVAS_POLICIES),
                    help="canvas aspect: finish = the AFTER photo's ratio (default); "
                         "common = the smaller width and height of the two")
    pp.add_argument("--anchors", default="",
                    help='"ax,ay,bx,by;..." canvas pixels, A -> B, >= 3 pairs')
    pp.add_argument("--anchor-falloff", type=float, default=TCFG["anchor_falloff"],
                    help="anchors: fade the anchored field to zero at the canvas "
                         "border over this fraction of the short edge (0 = off; "
                         "keeps the frame edge off the picture, T16)")
    pp.add_argument("--class", dest="force_class", default="",
                    choices=["", "A", "B"], help="force the pair class")
    pp.add_argument("--camera", default="flat", choices=list(CAMERAS),
                    help="class B camera move: flat = the pan-and-zoom as is; "
                         "ramp = near content (bottom rows) moves more, no "
                         "model; model = the same from Depth Anything V2 Small "
                         "(needs `transitions.py warmup` once)")
    pp.add_argument("--zoom", type=float, default=TCFG["classb_zoom"],
                    help="class B zoom fraction per frame, clamped to "
                         f"[{TCFG['zoom_range'][0]}, {TCFG['zoom_range'][1]}]")
    sub.add_parser("check", help="environment self-test")
    sub.add_parser("warmup", help="fetch and verify the depth model once "
                                  "(the only command that downloads)")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "check":
            return cmd_check()
        if args.cmd == "warmup":
            return cmd_warmup()
        return cmd_pair(args)
    except TransitionError as e:
        print(f"FAILED: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    sys.exit(main())
