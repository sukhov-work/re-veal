#!/usr/bin/env python3
"""
Reveal: a before/after photo aligner with a local web slider.

Give it two photos of the same subject taken at different times (a painted
utility box before and after, a wall, a landscape) and it lines the second
photo up with the first automatically: perspective, position, rotation,
scale, and optionally exposure. The result is an interactive slider in the
browser, an exported aligned photo, and a short transition video ready for
social media.

Pipeline (single global homography, built for deliberate re-shots with
small parallax):
  decode -> working copies -> SIFT (ORB / learned / phase-corr fallbacks)
  + MAGSAC++ homography -> ECC photometric refine -> optional DIS residual
  flow -> changed-region estimate -> optional masked exposure match ->
  crop to the largest clean rectangle -> preview / export.

Convergence is decided on MAGSAC++ inlier statistics (count + reprojection
RMSE), NOT on pixel similarity: the two photos legitimately differ where
the subject changed, and inlier statistics ignore that region by
construction. Pixel metrics (peripheral SSIM, edge overlap) are computed
only on the presumed-static periphery and only for display/validation.

Hard properties (mirrors the organizer's viewer.py contract):
  * localhost only: binds 127.0.0.1, nothing is exposed to the network.
  * originals are never modified; all outputs land in the job folder.
  * stdlib HTTP server; heavy work runs in a background thread per job.
  * degrades gracefully: RAW/HEIC decode and the learned matcher are
    optional layers; their absence produces a clear message, not a crash.

Usage:
  python reveal.py                       # serve on 127.0.0.1:8378, open browser
  python reveal.py serve --port 8400 --no-browser
  python reveal.py align BEFORE AFTER --out DIR [--video] [--aspect 4:5]
  python reveal.py check                 # environment self-test
"""

import argparse
import hashlib
import io
import json
import logging
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import threading
import time
import traceback
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

try:
    import cv2
except Exception as e:  # pragma: no cover
    sys.exit(f"OpenCV is required (pip install -r requirements.txt): {e}")

from PIL import Image, ImageOps, ImageCms

# Optional decode layers -----------------------------------------------------
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

VERSION = "1.5.0"
DEFAULT_PORT = 8378          # viewer.py owns 8377; stay adjacent, distinct

log = logging.getLogger("reveal")
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")

# ---------------------------------------------------------------------------
# Configuration (constants by design: this tool has no operator-tunable
# settings file; every knob a user needs is a slider in the UI)
# ---------------------------------------------------------------------------

CFG = {
    # geometry
    "work_long": 1600,        # long edge of the alignment working copies, px
    "render_long": 2000,      # long edge of the interactive preview source
    "preview_long": 1400,     # long edge of the JPEG sent to the browser
    "sift_features": 8000,
    "orb_features": 8000,
    "ratio": 0.75,            # Lowe ratio test
    "min_matches": 12,        # below this the method is considered failed
    "magsac_thresh": 2.0,     # px at working resolution
    "min_inliers": 30,        # primary stop metric floor
    "good_rmse": 2.0,         # px at working resolution: primary stop metric
    "max_corner_shift": 0.40, # sanity: fraction of working diagonal
    "area_ratio": (0.45, 2.2),# sanity: warped quad area vs image area
    "ecc_iters": 120,
    "ecc_eps": 1e-6,
    "ecc_trust_px": 12.0,     # reject ECC drifting further than this (work px)
    # residual flow (phase 3)
    "residual_mode": "auto",  # auto | off  (on = force, engineer only)
    "residual_cap": 6.0,      # max residual displacement, work px
    "residual_min": 0.4,      # below this median it's noise: skip
    "residual_gain": 0.01,    # required peripheral-SSIM improvement to keep
    "residual_min_samples": 2000,   # gradient-supported static samples
    "residual_gate_erode": 25,      # gate SSIM measured this far from edges
    # changed-region / metrics
    "changed_dilate": 21,
    "edge_dilate": 3,
    "sharpness_probe_px": 3.0,   # perturbation used to probe the SSIM peak
    "not_max_penalty": 0.6,      # score multiplier when H is not a peak
    # exposure
    "expo_auto_bhatta": 0.05, # auto-enable threshold (Bhattacharyya distance)
    "expo_auto_strength": 70, # initial strength when auto-enabled, percent
    # manual slider ranges (UI mirrors these)
    "tune_shift": 0.05,       # +-fraction of width/height
    "tune_rot": 3.0,          # +-degrees
    "tune_scale": 0.06,       # +-fraction
    "tune_keystone": 3e-5,    # +-per-px perspective term at slider extreme
    # video
    "video_fps": 30,
    "video_crf": 18,
    "video_feather": 12,      # px at 1080 width, scaled with output
    "upload_cap": 2 << 30,    # 2 GiB request body cap
    # model ladder switches (mode profiles override these)
    "similarity_fallback": False,  # try a 4-DOF similarity when H is weak
    "learned_always": False,       # loose mode: always consult LoFTR
}

# Matching modes. "reshot" (default) keeps the strict deliberate-re-shot
# prior; "loose" is for pairs that are only SIMILAR: a different person in
# the same scene, or two look-alike objects in different scenes. Loose
# relaxes the matcher and sanity gates, prefers a rigid similarity model
# when a full homography would overfit sketchy matches, widens the manual
# sliders, and disables residual flow (which would chase content
# differences between two genuinely different subjects).
MODES = {
    "reshot": {},
    "loose": {
        "ratio": 0.82,
        "min_matches": 8,
        "magsac_thresh": 5.0,
        "min_inliers": 12,
        "good_rmse": 4.0,
        "max_corner_shift": 0.80,
        "area_ratio": (0.2, 5.0),
        "ecc_trust_px": 24.0,
        "residual_mode": "off",
        "tune_shift": 0.15,
        "tune_rot": 15.0,
        "tune_scale": 0.30,
        "tune_keystone": 6e-5,
        "similarity_fallback": True,
        "learned_always": True,
    },
}


def profile(mode):
    """CFG overlaid with the chosen mode's overrides."""
    p = dict(CFG)
    p.update(MODES.get(mode, {}))
    p["mode"] = mode if mode in MODES else "reshot"
    return p

RAW_EXTS = {".dng", ".arw"}
HEIF_EXTS = {".heic", ".heif", ".hif"}
PIL_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}
ACCEPT_EXTS = RAW_EXTS | HEIF_EXTS | PIL_EXTS

ASPECTS = {
    "4:5": (1080, 1350), "9:16": (1080, 1920), "16:9": (1920, 1080),
    "1:1": (1080, 1080), "original": None,
}


class AlignError(Exception):
    """A pipeline failure with an operator-readable message."""


# ---------------------------------------------------------------------------
# Decode layer
# ---------------------------------------------------------------------------

def _srgb_from_pil(img):
    """Convert a PIL image to sRGB, honoring an embedded ICC profile
    (iPhone HEIC is commonly Display P3). Falls back to a plain RGB
    convert when there is no profile or the transform fails."""
    icc = img.info.get("icc_profile")
    if icc:
        try:
            src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            dst = ImageCms.createProfile("sRGB")
            img = ImageCms.profileToProfile(
                img, src, dst, outputMode="RGB",
                renderingIntent=ImageCms.Intent.PERCEPTUAL)
            return img
        except Exception as e:
            log.warning("ICC transform failed (%s); using plain convert", e)
    return img.convert("RGB")


def load_image_rgb(path):
    """Decode any accepted format to an sRGB uint8 HxWx3 numpy array with
    EXIF orientation applied. Raises AlignError with a plain message."""
    p = Path(path)
    ext = p.suffix.lower()
    if not p.exists():
        raise AlignError(f"File not found: {p}")
    if ext in RAW_EXTS:
        if rawpy is None:
            raise AlignError(
                f"RAW file ({ext}) needs the rawpy package, which failed to "
                f"load: {_RAWPY_ERR}. Re-run ./setup.sh.")
        try:
            with rawpy.imread(str(p)) as raw:
                # rawpy applies the camera flip during postprocess; do NOT
                # apply EXIF orientation again on top of this output.
                rgb = raw.postprocess(use_camera_wb=True, output_bps=8,
                                      no_auto_bright=False)
            return np.ascontiguousarray(rgb)
        except AlignError:
            raise
        except Exception as e:
            raise AlignError(f"Could not decode RAW file {p.name}: {e}")
    if ext in HEIF_EXTS and pillow_heif is None:
        raise AlignError(
            f"HEIC support failed to load: {_HEIF_ERR}. Re-run ./setup.sh.")
    if ext not in ACCEPT_EXTS:
        raise AlignError(
            f"Unsupported file type {ext or '(none)'}. Accepted: "
            + ", ".join(sorted(ACCEPT_EXTS)))
    try:
        with Image.open(p) as img:
            img = ImageOps.exif_transpose(img)
            img = _srgb_from_pil(img)
            return np.asarray(img, dtype=np.uint8).copy()
    except AlignError:
        raise
    except Exception as e:
        raise AlignError(f"Could not decode {p.name}: {e}")


def scaled_copy(rgb, long_edge):
    """Downscale (never upscale) so the long edge equals long_edge.
    Returns (image, scale) with scale = new/full."""
    h, w = rgb.shape[:2]
    s = min(1.0, long_edge / max(h, w))
    if s >= 1.0:
        return rgb, 1.0
    out = cv2.resize(rgb, (max(1, round(w * s)), max(1, round(h * s))),
                     interpolation=cv2.INTER_AREA)
    return out, out.shape[1] / w


def gray_of(rgb):
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)


# ---------------------------------------------------------------------------
# Geometry: feature matching, homography, refinement
# ---------------------------------------------------------------------------

def _match_ratio(desA, desB, norm, p):
    """kNN match with Lowe ratio test; returns list of cv2.DMatch."""
    bf = cv2.BFMatcher(norm)
    if desA is None or desB is None or len(desA) < 2 or len(desB) < 2:
        return []
    knn = bf.knnMatch(desB, desA, k=2)   # query=B, train=A
    good = []
    for pair in knn:
        if len(pair) == 2 and pair[0].distance < p["ratio"] * pair[1].distance:
            good.append(pair[0])
    return good


def _pts_from_matches(kpA, kpB, matches):
    ptsB = np.float32([kpB[m.queryIdx].pt for m in matches])
    ptsA = np.float32([kpA[m.trainIdx].pt for m in matches])
    return ptsA, ptsB


def _detect_and_match(grayA, grayB, method, p):
    """Detect + match with 'sift' or 'orb'. Returns (ptsA, ptsB) or None."""
    if method == "sift":
        if not hasattr(cv2, "SIFT_create"):
            return None
        det = cv2.SIFT_create(nfeatures=CFG["sift_features"])
        norm = cv2.NORM_L2
    else:
        det = cv2.ORB_create(nfeatures=CFG["orb_features"])
        norm = cv2.NORM_HAMMING
    kpA, desA = det.detectAndCompute(grayA, None)
    kpB, desB = det.detectAndCompute(grayB, None)
    good = _match_ratio(desA, desB, norm, p)
    if len(good) < p["min_matches"]:
        return None
    return _pts_from_matches(kpA, kpB, good)


# --- Learned matcher (phase 2, optional) -----------------------------------

_LEARNED = None
_LEARNED_LOCK = threading.Lock()
LEARNED_CAP = 1024        # long edge fed to DISK, px
LEARNED_FEATS = 2048      # keypoints per image

MODELS_DIR = Path(__file__).resolve().parent / "models"
LEARNED_MANIFEST = MODELS_DIR / "MANIFEST.json"
_ALLOW_DOWNLOAD = False   # ONLY `reveal.py warmup` ever flips this


def _pin_torch_home():
    """Pin torch's model cache INSIDE the project folder.

    Without this, kornia's weights land in the global ~/.cache/torch, which
    (a) does not travel with the project, (b) any cache cleaner can delete,
    and (c) would then be silently re-downloaded mid-job, breaking both the
    'fully local' promise and offline use. With models/ pinned here, the
    project folder is self-contained: copy it to another machine and the
    learned matcher still works with no network."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    os.environ["TORCH_HOME"] = str(MODELS_DIR)
    return MODELS_DIR


def _ckpt_dir():
    return MODELS_DIR / "hub" / "checkpoints"


def learned_available():
    try:
        import torch  # noqa: F401
        import kornia  # noqa: F401
        return True
    except Exception:
        return False


def learned_manifest():
    """The record `warmup` writes after downloading AND verifying every
    model file with a real forward pass. Its presence is the tool's only
    proof that the learned matcher is offline-ready."""
    try:
        return json.loads(LEARNED_MANIFEST.read_text())
    except Exception:
        return None


def learned_weights_cached(deep=False):
    """True when every model file recorded by warmup is present and intact,
    so a run needs no network at all. deep=True re-hashes the files."""
    man = learned_manifest()
    if not man or not man.get("files") or not man.get("verified"):
        return False
    for f in man["files"]:
        p = _ckpt_dir() / f["name"]
        if not p.exists() or p.stat().st_size != f["size"]:
            return False
        if deep and hashlib.sha256(p.read_bytes()).hexdigest() != f["sha256"]:
            return False
    return True


def _learned_models():
    """DISK detector + LightGlue matcher, loaded once, CPU.

    DISK+LightGlue replaced LoFTR in v1.4.0 for three measured reasons.
    (1) Weights: kornia fetches LoFTR from a plain-HTTP personal academic
    page (http://cmp.felk.cvut.cz/~mishkdmy/models/loftr_outdoor.ckpt),
    an unauthenticated download of a pickled checkpoint; DISK and
    LightGlue come over HTTPS from github (cvlab-epfl/disk and
    cvg/LightGlue releases). (2) Correctness: kornia's LoFTR derives its
    fine-matching stride and its keypoint x-scale from the HEIGHT ratio
    alone (fine_preprocess.py:62, coarse_matching.py:286), so inputs whose
    dimensions are not multiples of 8 get misplaced keypoints; the old
    prep() resized to arbitrary sizes. DISK takes pad_if_not_divisible and
    handles it natively. (3) Testability: LoFTR could never be exercised
    here (its weights are unreachable), so it shipped unverified through
    three releases. DISK+LightGlue is verified end to end.

    CPU by design: this is a one-shot fallback and PyTorch MPS has known
    op-coverage gaps that can fail silently."""
    global _LEARNED
    _pin_torch_home()
    if not _ALLOW_DOWNLOAD and not learned_weights_cached():
        # never reach for the network during a real job: fail clearly here
        # instead, so the user is told to run setup rather than silently
        # waiting on a download (or hanging with no internet)
        raise AlignError(
            "The learned matcher is installed but its model files are "
            "missing. Run  ./setup.sh --learned  once (a single download; "
            "after that it works offline forever).")
    import torch
    import kornia.feature as KF
    with _LEARNED_LOCK:
        if _LEARNED is None:
            disk = KF.DISK.from_pretrained("depth").eval()
            lg = KF.LightGlueMatcher("disk").eval()
            _LEARNED = (torch, KF, disk, lg)
    return _LEARNED


def _match_learned(grayA, grayB, p):
    """DISK keypoints + LightGlue matching, for pairs that defeat SIFT and
    ORB (low texture, repetitive structure, heavy illumination change).
    Weights (~40 MB) download once; ./setup.sh --learned pre-fetches them
    so that first real use is fully offline. Returns (ptsA, ptsB) in
    working-resolution coordinates, or None."""
    try:
        torch, KF, disk, lg = _learned_models()
    except Exception as e:
        log.info("learned matcher unavailable: %s", e)
        return None
    try:
        def feats(g):
            h, w = g.shape
            s = min(1.0, LEARNED_CAP / max(h, w))
            gg = cv2.resize(g, (round(w * s), round(h * s)),
                            interpolation=cv2.INTER_AREA) if s < 1.0 else g
            t = torch.from_numpy(gg)[None, None].float().div(255.0)
            t = t.repeat(1, 3, 1, 1)          # DISK expects 3 channels
            with torch.inference_mode():
                f = disk(t, LEARNED_FEATS, window_size=5,
                         score_threshold=0.0, pad_if_not_divisible=True)[0]
            return f, s, gg.shape

        fA, sA, shA = feats(grayA)
        fB, sB, shB = feats(grayB)
        with torch.inference_mode():
            _, idx = lg(fA.descriptors, fB.descriptors,
                        KF.laf_from_center_scale_ori(fA.keypoints[None]),
                        KF.laf_from_center_scale_ori(fB.keypoints[None]),
                        hw1=shA, hw2=shB)
        if idx.shape[0] < p["min_matches"]:
            return None
        ptsA = (fA.keypoints[idx[:, 0]].cpu().numpy() / sA).astype(np.float32)
        ptsB = (fB.keypoints[idx[:, 1]].cpu().numpy() / sB).astype(np.float32)
        return ptsA, ptsB
    except Exception as e:
        log.warning("learned matcher failed: %s", e)
        return None


# --- Homography estimation and sanity ---------------------------------------

def _reproj_stats(ptsA, ptsB, H, mask):
    inl = mask.ravel().astype(bool)
    n = int(inl.sum())
    if n < 4:
        return None
    proj = cv2.perspectiveTransform(ptsB[inl].reshape(-1, 1, 2), H)
    err = np.linalg.norm(proj.reshape(-1, 2) - ptsA[inl], axis=1)
    return n, float(np.sqrt(np.mean(err ** 2)))


def _estimate_h(ptsA, ptsB, p):
    """MAGSAC++ homography mapping B -> A. Returns (H, inliers, rmse_px)
    or None. RANSAC fallback covers builds without USAC."""
    flag = getattr(cv2, "USAC_MAGSAC", cv2.RANSAC)
    H, mask = cv2.findHomography(ptsB, ptsA, flag, p["magsac_thresh"],
                                 maxIters=10000, confidence=0.999)
    if H is None or mask is None:
        return None
    st = _reproj_stats(ptsA, ptsB, H, mask)
    return None if st is None else (H, st[0], st[1])


def _estimate_similarity(ptsA, ptsB, p):
    """4-DOF similarity (translation, rotation, uniform scale) mapping
    B -> A, lifted to a 3x3. The right model for 'two similar objects':
    with few, sketchy cross-content matches an 8-DOF homography overfits
    outlier structure that a rigid model shrugs off."""
    M, mask = cv2.estimateAffinePartial2D(
        ptsB, ptsA, method=cv2.RANSAC,
        ransacReprojThreshold=p["magsac_thresh"],
        maxIters=10000, confidence=0.999)
    if M is None or mask is None:
        return None
    H = np.vstack([M, [0.0, 0.0, 1.0]]).astype(np.float64)
    st = _reproj_stats(ptsA, ptsB, H, mask)
    return None if st is None else (H, st[0], st[1])


def _h_sane(H, shapeB, shapeA, p):
    """Reject homographies incompatible with a deliberate re-shot: the
    warped frame must stay convex, roughly the same size, and close to
    where it started."""
    hB, wB = shapeB[:2]
    hA, wA = shapeA[:2]
    corners = np.float32([[0, 0], [wB, 0], [wB, hB], [0, hB]]).reshape(-1, 1, 2)
    warped = cv2.perspectiveTransform(corners, H).reshape(-1, 2)
    if not cv2.isContourConvex(warped.astype(np.float32)):
        return False
    area = cv2.contourArea(warped.astype(np.float32))
    ratio = area / float(wB * hB)
    lo, hi = p["area_ratio"]
    if not (lo <= ratio <= hi):
        return False
    diag = math.hypot(wA, hA)
    shift = np.linalg.norm(warped - corners.reshape(-1, 2), axis=1).max()
    return shift <= p["max_corner_shift"] * diag


def _ecc_refine(grayA, grayB, H_ba, p, motion="homography",
                input_mask=None):
    """Photometric refinement of a B->A transform with cv2.findTransformECC.
    ECC's warp W maps template(A) coordinates into input(B) coordinates
    (it is applied with WARP_INVERSE_MAP), i.e. W ~ inv(H_ba). We seed it
    with inv(H_ba) and return (inv(W), rho) on success, (H_ba, None) on
    failure or when the refinement drifts outside the trust region.
    motion="affine" refines with 6 DOF (used for similarity-model results,
    where letting ECC add perspective would reintroduce the overfit the
    similarity fallback exists to avoid). input_mask (uint8, B-frame
    coordinates) restricts the correlation to the static scene so a large
    repainted subject cannot bias the refinement."""
    try:
        W_full = np.linalg.inv(H_ba)
        W_full /= W_full[2, 2]
    except np.linalg.LinAlgError:
        return H_ba, None
    crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
            CFG["ecc_iters"], CFG["ecc_eps"])
    tA = grayA.astype(np.float32) / 255.0
    tB = grayB.astype(np.float32) / 255.0
    affine = motion == "affine"
    W0 = W_full[:2, :] if affine else W_full
    mt = cv2.MOTION_AFFINE if affine else cv2.MOTION_HOMOGRAPHY
    try:
        rho, W = cv2.findTransformECC(tA, tB, W0.astype(np.float32),
                                      mt, crit, input_mask, 5)
    except cv2.error as e:
        log.info("ECC did not converge (%s); keeping feature transform", e)
        return H_ba, None
    try:
        W3 = np.vstack([W, [0.0, 0.0, 1.0]]) if affine else W
        H_ref = np.linalg.inv(W3.astype(np.float64))
        H_ref /= H_ref[2, 2]
    except np.linalg.LinAlgError:
        return H_ba, None
    # trust region: the refined warp must stay near the feature solution
    hB, wB = grayB.shape
    corners = np.float32([[0, 0], [wB, 0], [wB, hB], [0, hB]]).reshape(-1, 1, 2)
    d = np.linalg.norm(
        cv2.perspectiveTransform(corners, H_ref).reshape(-1, 2)
        - cv2.perspectiveTransform(corners, H_ba).reshape(-1, 2), axis=1).max()
    if d > p["ecc_trust_px"]:
        log.info("ECC drifted %.1f px (> %.1f trust); keeping feature "
                 "transform", d, p["ecc_trust_px"])
        return H_ba, None
    return H_ref, float(rho)


def _phase_corr_h(grayA, grayB):
    """Last-resort translation-only initialization via phase correlation,
    to give ECC something to start from when features fail entirely."""
    fA = np.float32(grayA) * cv2.createHanningWindow(grayA.shape[::-1], cv2.CV_32F)
    fB = np.float32(grayB) * cv2.createHanningWindow(grayB.shape[::-1], cv2.CV_32F)
    if fA.shape != fB.shape:
        fB = cv2.resize(fB, fA.shape[::-1])
    (dx, dy), resp = cv2.phaseCorrelate(fB, fA)
    if resp < 0.03:
        return None
    H = np.eye(3, dtype=np.float64)
    H[0, 2], H[1, 2] = dx, dy
    return H


def _arbitrate(cands, grayA, grayB, colorA, colorB, ref_H):
    """Pick between candidates from DIFFERENT matchers on the visual
    outcome, never on inlier count.

    Inlier COUNT IS NOT COMPARABLE ACROSS MATCHERS: a different detector
    has a different keypoint density, threshold and localization
    accuracy. Measured on a real pair (2026-07-13): SIFT 458 inliers ->
    peripheral SSIM 0.566, DISK+LightGlue 408 inliers -> 0.429. Ranking
    those by inlier count is a coin flip on a 0.14 SSIM gap, and a
    slightly denser learned result would have won with a visibly worse
    alignment. So the arbiter is peripheral SSIM, scored for every
    candidate against ONE fixed mask (built from the inlier leader), which
    keeps the comparison fair and costs one warp per candidate.

    Returns the winner, or None when the mask is too small to judge."""
    size = (grayA.shape[1], grayA.shape[0])
    try:
        w = cv2.warpPerspective(colorB, ref_H, size)
        v = warp_valid_mask(colorB.shape, ref_H, size)
        peri = peripheral_mask(v, changed_region_mask(colorA, w, v))
    except cv2.error:
        return None
    if int((peri > 0).sum()) < 4096:
        return None
    best, best_s = None, -1.0
    for c in cands:
        g = cv2.warpPerspective(grayB, c[1], size, flags=cv2.INTER_LINEAR)
        s = float(np.mean(ssim_map(grayA, g)[peri > 0]))
        log.info("arbitration: %s -> peripheral SSIM %.3f (%d inliers)",
                 c[0], s, c[2])
        if s > best_s:
            best, best_s = c, s
    return best


def estimate_alignment(grayA, grayB, p=None, colorA=None, colorB=None):
    """Full estimation chain at working resolution. Returns dict with
    H (B->A, working coords), method, inliers, rmse, ecc_rho.
    Raises AlignError when nothing usable comes out. When colorA/colorB
    are provided, a preliminary changed-region estimate masks ECC to the
    static scene (photometric stages must never see the changed subject).

    Model ladder: homography per matcher; in loose mode a 4-DOF similarity
    is estimated from the same matches and competes (methods tagged
    '+sim'). Candidates that pass the stop bar (min_inliers, good_rmse)
    outrank ones that don't; homography outranks similarity on ties so the
    richer model wins only when it is actually supported."""
    p = p or CFG

    def add_candidates(tag, pts, out):
        est = _estimate_h(*pts, p)
        if est and _h_sane(est[0], grayB.shape, grayA.shape, p):
            out.append((tag,) + est)
        if p.get("similarity_fallback"):
            est = _estimate_similarity(*pts, p)
            if est and _h_sane(est[0], grayB.shape, grayA.shape, p):
                out.append((tag + "+sim",) + est)

    def rank(c):
        tag, H, inliers, rmse = c
        passed = inliers >= p["min_inliers"] and rmse <= p["good_rmse"]
        return (passed, "+sim" not in tag if passed else True, inliers, -rmse)

    candidates = []
    for method in ("sift", "orb"):
        pts = _detect_and_match(grayA, grayB, method, p)
        if pts is None:
            continue
        add_candidates(method, pts, candidates)
        top = max(candidates, key=rank) if candidates else None
        if (method == "sift" and top and top[2] >= p["min_inliers"]
                and top[3] <= p["good_rmse"] and not p.get("learned_always")):
            break   # SIFT already passed the stop metric: done
    best = max(candidates, key=rank) if candidates else None
    # learned matcher: fallback when classical is below the bar, or always
    # in loose mode (cross-content pairs are exactly LoFTR's advantage)
    if learned_available() and (p.get("learned_always") or best is None
                                or best[2] < p["min_inliers"]):
        pts = _match_learned(grayA, grayB, p)
        if pts is not None:
            before = len(candidates)
            add_candidates("learned", pts, candidates)
            # the learned matcher can return points that every sanity gate
            # rejects, leaving the candidate list still empty: max() on an
            # empty list crashed here (latent since v1.1.0, dormant only
            # because the learned path had never executed)
            best = max(candidates, key=rank) if candidates else None
            # a learned candidate now competes with classical ones: inlier
            # counts do not compare across matchers, so arbitrate visually
            if (best is not None and len(candidates) > before
                    and colorA is not None):
                passing = [c for c in candidates
                           if c[2] >= p["min_inliers"] and c[3] <= p["good_rmse"]]
                pool = passing if len(passing) > 1 else candidates
                if len({c[0].split("+")[0] for c in pool}) > 1:
                    won = _arbitrate(pool, grayA, grayB, colorA, colorB,
                                     best[1])
                    if won is not None:
                        best = won
    if best is None:
        # translation + ECC rescue for feature-hostile content
        H0 = _phase_corr_h(grayA, grayB)
        if H0 is not None:
            H_ref, rho = _ecc_refine(grayA, grayB, H0, p)
            if rho is not None and rho > 0.35 and _h_sane(
                    H_ref, grayB.shape, grayA.shape, p):
                return {"H": H_ref, "method": "phase+ecc",
                        "inliers": 0, "rmse": float("nan"), "ecc_rho": rho}
        raise AlignError(
            "Could not find enough common detail between the two photos. "
            "They need to show the same scene from roughly the same spot."
            if p.get("mode", "reshot") == "reshot" else
            "Could not find enough matching detail, even with loose "
            "matching. The two subjects may be too different in shape, "
            "angle, or size for an automatic fit.")
    method, H, inliers, rmse = best
    mask_in = None
    if colorA is not None and colorB is not None:
        try:
            sizeA = (grayA.shape[1], grayA.shape[0])
            warpedB = cv2.warpPerspective(colorB, H, sizeA)
            validp = warp_valid_mask(colorB.shape, H, sizeA)
            changedp = changed_region_mask(colorA, warpedB, validp)
            perip = peripheral_mask(validp, changedp)
            if (perip > 0).sum() > 0.05 * perip.size:
                mask_in = cv2.warpPerspective(
                    perip, np.linalg.inv(H),
                    (grayB.shape[1], grayB.shape[0]),
                    flags=cv2.INTER_NEAREST)
        except (cv2.error, np.linalg.LinAlgError) as e:
            log.info("ECC mask prep failed (%s); refining unmasked", e)
            mask_in = None
    H_ref, rho = _ecc_refine(grayA, grayB, H, p,
                             "affine" if method.endswith("+sim")
                             else "homography", mask_in)
    return {"H": H_ref, "method": method, "inliers": inliers,
            "rmse": rmse, "ecc_rho": rho}


# ---------------------------------------------------------------------------
# Coordinate transport and manual adjustment
# ---------------------------------------------------------------------------

def scale_h(H, scaleA, scaleB):
    """Transport a B->A homography to another resolution pair.
    scaleA / scaleB are target/source factors for the A and B frames
    (e.g. full/work when the H was estimated on working copies):
      x_A_target = D(scaleA) x_A_source, so
      H_target = D(scaleA) @ H @ D(1/scaleB)   with D(s)=diag(s, s, 1)."""
    out = np.diag([scaleA, scaleA, 1.0]) @ H \
        @ np.diag([1.0 / scaleB, 1.0 / scaleB, 1.0])
    return out / out[2, 2]


def manual_matrix(params, wA, hA, p=None):
    """Compose the user's fine-tune sliders into a 3x3 applied on the A
    frame AFTER the automatic homography: translation, rotation and scale
    about the image center, plus two small keystone (perspective) terms.
    Params are resolution-independent: dx/dy as fraction of width/height,
    rot in degrees, scale as a factor, kh/kv in [-1, 1]."""
    dx = float(params.get("dx", 0.0)) * wA
    dy = float(params.get("dy", 0.0)) * hA
    rot = math.radians(float(params.get("rot", 0.0)))
    s = float(params.get("scale", 1.0))
    p = p or CFG
    kh = float(params.get("kh", 0.0)) * p["tune_keystone"]
    kv = float(params.get("kv", 0.0)) * p["tune_keystone"]
    cx, cy = wA / 2.0, hA / 2.0
    T1 = np.array([[1, 0, -cx], [0, 1, -cy], [0, 0, 1]], dtype=np.float64)
    K = np.array([[1, 0, 0], [0, 1, 0], [kh, kv, 1]], dtype=np.float64)
    RS = np.array([[s * math.cos(rot), -s * math.sin(rot), 0],
                   [s * math.sin(rot),  s * math.cos(rot), 0],
                   [0, 0, 1]], dtype=np.float64)
    T2 = np.array([[1, 0, cx + dx], [0, 1, cy + dy], [0, 0, 1]],
                  dtype=np.float64)
    M = T2 @ RS @ K @ T1
    return M / M[2, 2]


def default_params():
    return {"dx": 0.0, "dy": 0.0, "rot": 0.0, "scale": 1.0,
            "kh": 0.0, "kv": 0.0, "exposure": 0}


# ---------------------------------------------------------------------------
# Valid region and crop
# ---------------------------------------------------------------------------

def warp_valid_mask(shapeB, H, sizeA):
    """uint8 mask of where warped B has real pixels inside the A frame."""
    hB, wB = shapeB[:2]
    ones = np.full((hB, wB), 255, np.uint8)
    m = cv2.warpPerspective(ones, H, sizeA, flags=cv2.INTER_NEAREST)
    return m


def largest_interior_rect(mask):
    """Largest axis-aligned rectangle of nonzero cells in a binary mask.
    Classic histogram-of-heights + monotonic stack, O(H*W).
    Returns (x, y, w, h) in mask coordinates."""
    m = (mask > 0).astype(np.int32)
    h, w = m.shape
    heights = np.zeros(w + 1, dtype=np.int32)
    best = (0, 0, 0, 0)
    best_area = 0
    for y in range(h):
        row = m[y]
        heights[:w] = np.where(row > 0, heights[:w] + 1, 0)
        stack = []
        for x in range(w + 1):
            start = x
            while stack and stack[-1][1] >= heights[x]:
                sx, sh = stack.pop()
                area = sh * (x - sx)
                if area > best_area:
                    best_area = area
                    best = (sx, y - sh + 1, x - sx, sh)
                start = sx
            stack.append((start, heights[x]))
    return best


def crop_rect(valid_mask, small_long=700):
    """Compute the crop rectangle (x, y, w, h) at valid_mask resolution:
    largest interior rectangle found on a downscaled copy for speed, then
    mapped back with a conservative inset so it never touches invalid
    border pixels."""
    H, W = valid_mask.shape
    s = min(1.0, small_long / max(H, W))
    small = cv2.resize(valid_mask, (max(1, round(W * s)), max(1, round(H * s))),
                       interpolation=cv2.INTER_NEAREST) if s < 1.0 else valid_mask
    x, y, w, h = largest_interior_rect(small)
    if w == 0 or h == 0:
        return 0, 0, W, H
    inv = 1.0 / (small.shape[1] / W)
    inset = int(math.ceil(inv)) + 2
    X = max(0, int(math.floor(x * inv)) + inset)
    Y = max(0, int(math.floor(y * inv)) + inset)
    X2 = min(W, int(math.ceil((x + w) * inv)) - inset)
    Y2 = min(H, int(math.ceil((y + h) * inv)) - inset)
    if X2 - X < 16 or Y2 - Y < 16:
        return 0, 0, W, H
    # keep dimensions even: the video encoder wants mod-2
    return X, Y, (X2 - X) & ~1, (Y2 - Y) & ~1


# ---------------------------------------------------------------------------
# Metrics: SSIM, changed-region estimate, peripheral scores, confidence
# ---------------------------------------------------------------------------

def ssim_map(grayA, grayB):
    """Standard single-scale SSIM map (gaussian window sigma 1.5) on
    float grays in [0, 1]. Returns the per-pixel map."""
    a = grayA.astype(np.float32) / 255.0
    b = grayB.astype(np.float32) / 255.0
    C1, C2 = (0.01) ** 2, (0.03) ** 2
    blur = lambda x: cv2.GaussianBlur(x, (11, 11), 1.5)
    mA, mB = blur(a), blur(b)
    vA = blur(a * a) - mA * mA
    vB = blur(b * b) - mB * mB
    cAB = blur(a * b) - mA * mB
    num = (2 * mA * mB + C1) * (2 * cAB + C2)
    den = (mA * mA + mB * mB + C1) * (vA + vB + C2)
    return num / np.maximum(den, 1e-9)


def _norm_gray(g, mask):
    """Zero-mean unit-std normalize within a mask: removes global exposure
    difference before pixel comparisons."""
    v = g[mask > 0].astype(np.float32)
    if v.size < 16:
        return g.astype(np.float32)
    mu, sd = float(v.mean()), float(v.std() + 1e-6)
    return (g.astype(np.float32) - mu) / sd


def _fill_holes(mask255):
    """Fill enclosed zero-regions of a binary mask. A repainted physical
    object is contiguous; interior 'unchanged' islands are detection
    misses (both paint jobs can alias in normalized channel space), and
    they are precisely what leaks the static periphery into the subject."""
    inv = (mask255 == 0).astype(np.uint8)
    n, lab = cv2.connectedComponents(inv)
    border = np.unique(np.concatenate(
        [lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]]))
    out = mask255.copy()
    out[~np.isin(lab, border)] = 255
    return out


def changed_region_mask(imgA, imgB_warped, valid):
    """Estimate where the CONTENT changed between before and after (the
    subject itself), as opposed to residual misalignment. Works per color
    channel (a repaint can change hue at equal luminance), with exposure
    normalized out per channel first; the result is dilated so downstream
    'static periphery' masks stay clear of the changed area."""
    if imgA.ndim == 2:
        chansA, chansB = [imgA], [imgB_warped]
    else:
        chansA = [imgA[..., c] for c in range(imgA.shape[2])]
        chansB = [imgB_warped[..., c] for c in range(imgB_warped.shape[2])]
    d = None
    for ca, cb in zip(chansA, chansB):
        dc = np.abs(_norm_gray(ca, valid) - _norm_gray(cb, valid))
        d = dc if d is None else np.maximum(d, dc)
    d[valid == 0] = 0
    d = cv2.GaussianBlur(d, (9, 9), 0)
    vals = d[valid > 0]
    if vals.size < 64:
        return np.zeros_like(valid)
    d8 = np.clip(d / max(1e-6, float(vals.max())) * 255, 0, 255).astype(np.uint8)
    try:
        thr, _ = cv2.threshold(d8[valid > 0], 0, 255,
                               cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    except cv2.error:
        thr = float(d8[valid > 0].mean() + 2.0 * d8[valid > 0].std())
    changed = ((d8 > max(thr, 40)) & (valid > 0)).astype(np.uint8) * 255
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    changed = cv2.morphologyEx(changed, cv2.MORPH_CLOSE, k)
    changed = cv2.morphologyEx(changed, cv2.MORPH_OPEN,
                               cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    changed = _fill_holes(changed)
    kd = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (CFG["changed_dilate"], CFG["changed_dilate"]))
    return cv2.dilate(changed, kd)


def peripheral_mask(valid, changed):
    """The presumed-static region: valid overlap, minus the changed area,
    minus a safety band along the warp border (interpolation zone)."""
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    core = cv2.erode(valid, k)
    return ((core > 0) & (changed == 0)).astype(np.uint8) * 255


def edge_overlap(grayA, grayB_warped, mask):
    """Fraction of B's Canny edges that land within 3 px of an A edge,
    inside the mask. Display metric only (content change contaminates it)."""
    eA = cv2.Canny(grayA, 60, 160)
    eB = cv2.Canny(grayB_warped, 60, 160)
    k = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (2 * CFG["edge_dilate"] + 1,) * 2)
    eA = cv2.dilate(eA, k)
    sel = (mask > 0) & (eB > 0)
    n = int(sel.sum())
    if n < 32:
        return None
    return float((eA[sel] > 0).mean())


def bhattacharyya(grayA, grayB, mask):
    """Bhattacharyya distance between 64-bin luminance histograms within
    the mask; drives the exposure-match auto-enable decision."""
    hA = cv2.calcHist([grayA], [0], mask, [64], [0, 256])
    hB = cv2.calcHist([grayB], [0], mask, [64], [0, 256])
    cv2.normalize(hA, hA)
    cv2.normalize(hB, hB)
    return float(cv2.compareHist(hA, hB, cv2.HISTCMP_BHATTACHARYYA))


def peak_sharpness(grayA, grayB, H, peri, size):
    """Is H a local maximum of peripheral SSIM, and how sharp is the peak?

    This replaces raw SSIM as the visual term of the score (v1.3.1). The
    RAW value is not comparable across pairs: its ceiling is set by
    texture, sensor noise, JPEG and resampling, none of which alignment
    can fix. Real photographs cap near 0.55 even when perfectly aligned;
    synthetic scenes reach 0.89. Scoring against a fixed ceiling
    therefore penalized every real pair by roughly 15 points. The peak
    ratio cancels the ceiling: it asks whether the found homography sits
    at the top of the similarity surface, which is the question the score
    is actually meant to answer, and it stays robust to the legitimate
    content change that contaminates absolute similarity.

    Returns (ssim, relative_drop, is_local_max) or None when the static
    periphery is too small to measure."""
    if int((peri > 0).sum()) < 4096:
        return None

    def at(M):
        g = cv2.warpPerspective(grayB, M, size, flags=cv2.INTER_LINEAR)
        return float(np.mean(ssim_map(grayA, g)[peri > 0]))

    d = CFG["sharpness_probe_px"]
    s0 = at(H)
    probes = []
    for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d)):
        T = np.array([[1, 0, dx], [0, 1, dy], [0, 0, 1]], dtype=np.float64)
        probes.append(at(T @ H))
    rel = (s0 - float(np.mean(probes))) / max(s0, 1e-6)
    return s0, float(rel), bool(s0 >= max(probes))


def confidence_score(inliers, rmse, local_max=True):
    """0-100 human-facing score, on scene-independent evidence only.

    Scored terms: reprojection RMSE (70 pts, full marks near 0.5 px, zero
    at 4 px) and inlier count (30 pts, 'plenty' = 75, since a sparse scene
    can still align exactly). Multiplied by a penalty when the alignment
    is not even a local maximum of peripheral similarity, which means the
    geometry and the pixels disagree.

    v1.3.1 removed the raw-SSIM term. Two pixel-similarity scales were
    tried and both proved scene-dependent, so neither is comparable across
    pairs: (a) absolute peripheral SSIM has a ceiling set by texture,
    sensor noise, JPEG and resampling, none of which alignment can fix
    (real photographs cap near 0.55 when perfectly aligned, synthetic
    scenes reach 0.89), so a fixed divisor docked every real pair by
    roughly 15 points; (b) the SSIM peak's sharpness cancels that ceiling
    but is confounded by texture density in the opposite direction (a
    perfectly aligned smooth scene measures 0.016, a textured one 0.263),
    so it would punish clean scenes. Both survive in metrics.json as
    DIAGNOSTICS. Only the local-maximum test, which is a yes/no about
    whether the found homography sits at the top of the similarity
    surface, is robust enough to influence the score."""
    r = 0.0 if (rmse is None or math.isnan(rmse)) else \
        max(0.0, min(1.0, 1.0 - (rmse - 0.5) / 3.5))
    n = max(0.0, min(1.0, inliers / 75.0))
    score = 100.0 * (0.70 * r + 0.30 * n)
    if not local_max:
        score *= CFG["not_max_penalty"]
    return int(round(score))


# ---------------------------------------------------------------------------
# Exposure matching (masked Reinhard in Lab)
# ---------------------------------------------------------------------------

def exposure_params(rgbA, rgbB_warped, mask):
    """Per-channel Lab (mean, std) of both images over the static mask.
    Returns transfer parameters, computed once at working resolution and
    applied at any resolution."""
    labA = cv2.cvtColor(rgbA.astype(np.float32) / 255.0, cv2.COLOR_RGB2Lab)
    labB = cv2.cvtColor(rgbB_warped.astype(np.float32) / 255.0,
                        cv2.COLOR_RGB2Lab)
    sel = mask > 0
    if sel.sum() < 256:
        return None
    stats = []
    for ch in range(3):
        a, b = labA[..., ch][sel], labB[..., ch][sel]
        stats.append((float(a.mean()), float(a.std() + 1e-6),
                      float(b.mean()), float(b.std() + 1e-6)))
    return stats


def apply_exposure(rgbB, stats, strength):
    """Reinhard transfer B -> A statistics, blended by strength [0..100]."""
    if not stats or strength <= 0:
        return rgbB
    s = min(100, max(0, int(strength))) / 100.0
    lab = cv2.cvtColor(rgbB.astype(np.float32) / 255.0, cv2.COLOR_RGB2Lab)
    for ch, (mA, sA, mB, sB) in enumerate(stats):
        gain = sA / sB
        gain = float(np.clip(gain, 0.4, 2.5))     # guard degenerate stats
        lab[..., ch] = (lab[..., ch] - mB) * gain + mA
    out = cv2.cvtColor(lab, cv2.COLOR_Lab2RGB)
    out = np.clip(out * 255.0, 0, 255).astype(np.uint8)
    if s >= 1.0:
        return out
    return cv2.addWeighted(out, s, rgbB, 1.0 - s, 0)


# ---------------------------------------------------------------------------
# Residual flow (phase 3): bounded local correction after the homography
# ---------------------------------------------------------------------------

def residual_flow(grayA, grayB_warped, peri, valid, changed=None):
    """Phase-3 residual, redesigned (v1.3.0): DIS optical flow provides
    SAMPLES; the field that gets APPLIED is a robustly fitted low-order
    model (2D cubic per component, 20 parameters), evaluated everywhere.

    Why: the physical residual after a good homography is lens distortion
    plus small parallax, which is inherently smooth and low-order, and it
    affects the changed subject exactly as much as the wall behind it. A
    20-parameter field structurally cannot content-chase, cannot wobble,
    and needs no masks, kill zones, or blend ramps in the applied field:
    all three earlier designs (dense flow with interpolation, feathered
    suppression, per-subject rigidification) failed by putting spatial
    structure into the field near subjects, which either bends them or
    starves their surroundings of correction.

    Protection layers: samples come only from the static periphery with
    gradient support (textureless pixels carry no flow evidence); Huber
    IRLS rejects incoherent leftovers; a fitted field exceeding the cap
    anywhere is rejected outright (clipping would reintroduce gradients);
    the caller's far-periphery SSIM gate has the final word.
    Returns float32 HxWx2 field or None."""
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    nA = cv2.normalize(grayA, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    nB = cv2.normalize(grayB_warped, None, 0, 255,
                       cv2.NORM_MINMAX).astype(np.uint8)
    flow = dis.calc(nA, nB, None)          # A(x) ~ B_warped(x + flow(x))
    gm = cv2.magnitude(cv2.Sobel(nA, cv2.CV_32F, 1, 0, ksize=3),
                       cv2.Sobel(nA, cv2.CV_32F, 0, 1, ksize=3))
    ref = float(np.percentile(gm[peri > 0], 75)) if (peri > 0).any() else 1.0
    wq = np.clip(gm / max(ref, 1e-6), 0.0, 1.0)
    strict = (peri > 0) & (wq > 0.1)
    if changed is not None:
        strict &= changed == 0
    if int(strict.sum()) < CFG["residual_min_samples"]:
        return None
    mag = np.linalg.norm(flow, axis=2)
    med = float(np.median(mag[strict]))
    if med < CFG["residual_min"] or med > CFG["residual_cap"] * 1.5:
        return None
    hh, ww = grayA.shape

    def basis(x, y):
        return np.stack([np.ones_like(x), x, y, x * x, x * y, y * y,
                         x ** 3, x * x * y, x * y * y, y ** 3], axis=-1)

    # light ridge on the higher-order terms tames extrapolation into
    # corners the samples do not reach
    ridge = np.diag([0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 3.0, 3.0, 3.0, 3.0])
    ridge *= 1e-3

    def fit(idx):
        ys, xs = np.divmod(idx, ww)
        Phi = basis(xs / ww * 2.0 - 1.0, ys / hh * 2.0 - 1.0)
        wgt0 = wq.ravel()[idx]
        out = []
        for c in range(2):
            t = flow[..., c].ravel()[idx].astype(np.float64)
            wgt = wgt0.copy()
            coef = None
            for _ in range(3):                   # Huber IRLS, delta 1 px
                Ws = wgt[:, None]
                A_ = Phi.T @ (Phi * Ws) + ridge
                b_ = Phi.T @ (t * wgt)
                coef = np.linalg.solve(A_, b_)
                r = np.abs(Phi @ coef - t)
                wgt = wgt0 * np.minimum(1.0, 1.0 / np.maximum(r, 1e-6))
            out.append(coef)
        return out

    def sub(mask):
        idx = np.flatnonzero(mask)
        return idx[::max(1, idx.size // 20000)]

    coefs = fit(sub(strict))
    if changed is not None and (changed > 0).any():
        # second pass: re-admit "changed" pixels whose DIS flow agrees
        # with the smooth fit. Residual DISPLACEMENT gets misclassified
        # as change (a shifted grille diffs strongly); its flow is
        # consistent with the field, unlike content-chasing, so the fit
        # itself is the discriminator. Recovers the strongest-signal
        # samples (frame corners) that exclusion would starve the fit of.
        cand = (wq > 0.1) & (valid > 0) & (changed > 0)
        ci = np.flatnonzero(cand)
        if ci.size:
            ci = ci[::max(1, ci.size // 20000)]
            ys, xs = np.divmod(ci, ww)
            Pc = basis(xs / ww * 2.0 - 1.0, ys / hh * 2.0 - 1.0)
            pred = np.stack([Pc @ coefs[0], Pc @ coefs[1]], axis=1)
            obs = flow.reshape(-1, 2)[ci].astype(np.float64)
            agree = np.linalg.norm(pred - obs, axis=1) < 1.0
            if agree.any():
                keep = np.concatenate([sub(strict), ci[agree]])
                coefs = fit(keep)
    gx, gy = np.meshgrid(np.linspace(-1, 1, ww), np.linspace(-1, 1, hh))
    Pg = basis(gx.ravel(), gy.ravel())
    field = np.stack([(Pg @ coefs[0]).reshape(hh, ww),
                      (Pg @ coefs[1]).reshape(hh, ww)],
                     axis=2).astype(np.float32)
    if float(np.abs(field[valid > 0]).max()) > CFG["residual_cap"]:
        return None                              # wild fit: reject whole
    return field


def apply_residual(img, flow_work, work_scale):
    """Remap an image (any resolution) by the working-resolution residual
    flow: corrected(x) = img(x + flow(x)), flow scaled to the target."""
    h, w = img.shape[:2]
    s = w / flow_work.shape[1]
    fx = cv2.resize(flow_work[..., 0], (w, h)) * s
    fy = cv2.resize(flow_work[..., 1], (w, h)) * s
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32),
                         np.arange(h, dtype=np.float32))
    return cv2.remap(img, gx + fx, gy + fy, cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_REPLICATE)


# ---------------------------------------------------------------------------
# Job: one before/after pair through the whole pipeline
# ---------------------------------------------------------------------------

class Job:
    """State for one aligned pair. Full-resolution originals stay in
    memory for the session (a 61 MP pair is ~0.4 GB, fine on the target
    machine); mid-resolution copies drive interactive tuning."""

    def __init__(self, job_id, workdir, mode="reshot"):
        self.id = job_id
        self.mode = mode if mode in MODES else "reshot"
        self.prof = profile(self.mode)
        self.dir = Path(workdir) / "jobs" / job_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.state = "created"      # decoding aligning refining rendering
                                    # ready exporting failed
        self.note = ""
        self.error = None
        self.params = default_params()
        self.metrics = {}
        self.auto_exposure = 0
        # numpy payloads
        self.fullA = self.fullB = None
        self.midA = self.midB = None        # render_long copies
        self.H_mid = None                    # B->A at (midA, midB) scales
        self.H_full = None
        self.expo_stats = None
        self.flow_work = None                # residual, working res of midA
        self.flow_scale = 1.0                # midA -> flow grid scale
        self.preview_key = None
        self.exports = {}                    # name -> Path

    def set(self, state, note=""):
        with self.lock:
            self.state = state
            self.note = note
        log.info("job %s: %s %s", self.id, state, note)

    def fail(self, msg):
        with self.lock:
            self.state = "failed"
            self.error = msg
        log.warning("job %s failed: %s", self.id, msg)

    def status(self):
        with self.lock:
            return {"id": self.id, "state": self.state, "note": self.note,
                    "error": self.error, "metrics": self.metrics,
                    "params": self.params, "mode": self.mode,
                    "limits": {"shift": self.prof["tune_shift"],
                               "rot": self.prof["tune_rot"],
                               "scale": self.prof["tune_scale"]},
                    "auto_exposure": self.auto_exposure,
                    "exports": {k: v.name for k, v in self.exports.items()}}


def run_alignment(job, path_before, path_after):
    """The autonomous pass: decode, estimate, refine, measure, prepare
    interactive rendering. Runs in a background thread."""
    try:
        job.set("decoding", "Reading the two photos")
        A = load_image_rgb(path_before)          # BEFORE is the reference
        B = load_image_rgb(path_after)
        job.fullA, job.fullB = A, B
        job.midA, sA_mid = scaled_copy(A, CFG["render_long"])
        job.midB, sB_mid = scaled_copy(B, CFG["render_long"])

        job.set("aligning", "Finding common detail")
        workA, sA_w = scaled_copy(A, CFG["work_long"])
        workB, sB_w = scaled_copy(B, CFG["work_long"])
        gA, gB = gray_of(workA), gray_of(workB)
        p = job.prof
        est = estimate_alignment(gA, gB, p, workA, workB)
        H_work = est["H"]

        job.set("refining", "Polishing the fit")
        # transport to mid and full coordinate frames (scales are new/full
        # from scaled_copy and always > 0)
        job.H_mid = scale_h(H_work, sA_mid / sA_w, sB_mid / sB_w)
        job.H_full = scale_h(H_work, 1.0 / sA_w, 1.0 / sB_w)

        # measurements at working resolution
        sizeA = (gA.shape[1], gA.shape[0])
        warpedB = cv2.warpPerspective(workB, H_work, sizeA,
                                      flags=cv2.INTER_LINEAR)
        valid = warp_valid_mask(workB.shape, H_work, sizeA)
        gW = gray_of(warpedB)
        changed = changed_region_mask(workA, warpedB, valid)
        peri = peripheral_mask(valid, changed)

        # peak sharpness: probed on the pure homography, before any
        # residual field, since it scores the GLOBAL alignment
        sharp = peak_sharpness(gA, gB, H_work, peri, sizeA)

        # phase 3: residual flow, auto-gated on measured improvement
        # (forced off in loose mode: on genuinely different subjects the
        # flow would chase content, which invariant 5 forbids)
        rmode = p["residual_mode"]
        if rmode in ("auto", "on"):
            flow = residual_flow(gA, gW, peri, valid, changed)
            if flow is not None:
                gW2 = apply_residual(gW, flow, 1.0)
                # judge on the FAR periphery: pixels near the changed
                # boundary can carry leaked content difference, and a
                # content-chasing flow "improves" exactly those, so they
                # must not vote on whether the flow is kept
                ke = cv2.getStructuringElement(
                    cv2.MORPH_ELLIPSE,
                    (2 * CFG["residual_gate_erode"] + 1,) * 2)
                far = cv2.erode(peri, ke)
                gate = far if (far > 0).sum() > 4096 else peri
                s_before = float(np.mean(ssim_map(gA, gW)[gate > 0])) \
                    if gate.sum() else 0.0
                s_after = float(np.mean(ssim_map(gA, gW2)[gate > 0])) \
                    if gate.sum() else 0.0
                if rmode == "on" or s_after >= s_before + CFG["residual_gain"]:
                    job.flow_work = flow
                    warpedB = apply_residual(warpedB, flow, 1.0)
                    gW = gW2 if (rmode == "on" or s_after > s_before) \
                        else gray_of(warpedB)
                    log.info("residual flow kept: peripheral SSIM %.3f -> %.3f",
                             s_before, s_after)
                else:
                    log.info("residual flow skipped: SSIM %.3f -> %.3f "
                             "(gain < %.3f)", s_before, s_after,
                             CFG["residual_gain"])
        job.flow_scale = 1.0 / sA_w if sA_w else 1.0   # work -> full factor

        peri_ssim = float(np.mean(ssim_map(gA, gW)[peri > 0])) \
            if peri.sum() else None
        edges = edge_overlap(gA, gW, peri)
        bh = bhattacharyya(gA, gW, peri)
        job.expo_stats = exposure_params(workA, warpedB, peri)
        if bh > CFG["expo_auto_bhatta"] and job.expo_stats:
            job.auto_exposure = CFG["expo_auto_strength"]
            job.params["exposure"] = job.auto_exposure

        job.metrics = {
            "method": est["method"],
            "inliers": est["inliers"],
            "rmse_px": None if math.isnan(est["rmse"]) else
                round(est["rmse"], 2),
            "ecc_rho": None if est["ecc_rho"] is None else
                round(est["ecc_rho"], 4),
            "peripheral_ssim": None if peri_ssim is None else
                round(peri_ssim, 3),          # diagnostic: ceiling is
                                              # scene-dependent, do not
                                              # read as a quality scale
            "sharpness": None if sharp is None else round(sharp[1], 3),
            "local_max": None if sharp is None else sharp[2],
            "edge_overlap": None if edges is None else round(edges, 3),
                                              # blind below ~4 px (3 px
                                              # Canny dilation): coarse
                                              # sanity check only
            "luma_distance": round(bh, 4),
            "residual": job.flow_work is not None,
            "changed_pct": round(100.0 * float((changed > 0).sum())
                                 / max(1, (valid > 0).sum()), 1),
            "passed": bool(est["inliers"] >= p["min_inliers"]
                           and not math.isnan(est["rmse"])
                           and est["rmse"] <= p["good_rmse"]),
        }
        job.metrics["confidence"] = confidence_score(
            est["inliers"], est["rmse"],
            True if sharp is None else sharp[2])

        job.set("rendering", "Preparing the preview")
        render_previews(job)
        job.set("ready")
    except AlignError as e:
        job.fail(str(e))
    except Exception as e:
        log.error("job %s crashed:\n%s", job.id, traceback.format_exc())
        job.fail(f"Unexpected problem while aligning: {e}")


def _render_pair(job, longe, params):
    """Render the aligned, exposure-matched, cropped pair at the given
    long edge from the appropriate source copies. Returns (imgA, imgB)."""
    use_full = longe > max(job.midA.shape[:2])
    srcA = job.fullA if use_full else job.midA
    srcB = job.fullB if use_full else job.midB
    sA = srcA.shape[1] / job.fullA.shape[1]
    sB = srcB.shape[1] / job.fullB.shape[1]
    H = scale_h(job.H_full, sA, sB)
    hA, wA = srcA.shape[:2]
    M = manual_matrix(params, wA, hA, job.prof)
    Hm = M @ H
    Hm /= Hm[2, 2]
    warped = cv2.warpPerspective(srcB, Hm, (wA, hA), flags=cv2.INTER_LINEAR)
    valid = warp_valid_mask(srcB.shape, Hm, (wA, hA))
    if job.flow_work is not None:
        warped = apply_residual(warped, job.flow_work, 1.0)
        valid = apply_residual(valid, job.flow_work, 1.0)
        valid = (valid > 200).astype(np.uint8) * 255
    strength = int(params.get("exposure", 0))
    if strength > 0 and job.expo_stats:
        matched = apply_exposure(warped, job.expo_stats, strength)
        matched[valid == 0] = warped[valid == 0]
        warped = matched
    x, y, w, h = crop_rect(valid)
    outA = srcA[y:y + h, x:x + w]
    outB = warped[y:y + h, x:x + w]
    if max(outA.shape[:2]) > longe:
        outA, _ = scaled_copy(outA, longe)
        outB, _ = scaled_copy(outB, longe)
        if outA.shape != outB.shape:
            outB = cv2.resize(outB, (outA.shape[1], outA.shape[0]))
    return np.ascontiguousarray(outA), np.ascontiguousarray(outB)


def _params_key(params):
    return "-".join(f"{k}{params[k]}" for k in sorted(params))


def render_previews(job):
    """Write the browser preview JPEGs for the current params."""
    a, b = _render_pair(job, CFG["preview_long"], job.params)
    for name, img in (("before", a), ("after", b)):
        ok, buf = cv2.imencode(".jpg", cv2.cvtColor(img, cv2.COLOR_RGB2BGR),
                               [cv2.IMWRITE_JPEG_QUALITY, 88])
        if not ok:
            raise AlignError("Could not encode the preview image.")
        (job.dir / f"preview_{name}.jpg").write_bytes(buf.tobytes())
    job.preview_key = _params_key(job.params)


# ---------------------------------------------------------------------------
# Export: aligned stills and the transition video
# ---------------------------------------------------------------------------

def export_images(job):
    a, b = _render_pair(job, 10 ** 6, job.params)   # full resolution
    for name, img in (("before", a), ("after_aligned", b)):
        p = job.dir / f"{name}.jpg"
        ok, buf = cv2.imencode(".jpg", cv2.cvtColor(img, cv2.COLOR_RGB2BGR),
                               [cv2.IMWRITE_JPEG_QUALITY, 95])
        if not ok:
            raise AlignError("Could not encode the export image.")
        p.write_bytes(buf.tobytes())
        job.exports[name] = p
    return a, b


def _cover(img, tw, th):
    """Scale-to-fill + center-crop to exactly (tw, th)."""
    h, w = img.shape[:2]
    s = max(tw / w, th / h)
    r = cv2.resize(img, (max(tw, round(w * s)), max(th, round(h * s))),
                   interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    y = (r.shape[0] - th) // 2
    x = (r.shape[1] - tw) // 2
    return np.ascontiguousarray(r[y:y + th, x:x + tw])


def _ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * min(1.0, max(0.0, t)))


def export_video(job, aspect="4:5", style="wipe", seconds=4.6):
    """Render the reveal as H.264 yuv420p via the bundled ffmpeg binary,
    frames piped as rawvideo. Timeline: hold before, eased sweep, hold
    after. The seam sweeps left to right; left of the seam shows AFTER,
    matching the web slider."""
    if imageio_ffmpeg is None:
        raise AlignError(f"Video export needs imageio-ffmpeg: {_FFMPEG_ERR}")
    a, b = export_images(job)
    tgt = ASPECTS.get(aspect)
    if tgt is None:
        h, w = a.shape[:2]
        s = min(1.0, 1920 / max(h, w))
        tw, th = (round(w * s) & ~1) or 2, (round(h * s) & ~1) or 2
    else:
        tw, th = tgt
    A = _cover(a, tw, th).astype(np.float32)
    B = _cover(b, tw, th).astype(np.float32)
    fps = CFG["video_fps"]
    seconds = float(min(12.0, max(2.5, seconds)))
    hold = max(0.8, seconds * 0.22)
    sweep = max(0.8, seconds - 2 * hold)
    n_hold = round(hold * fps)
    n_sweep = round(sweep * fps)
    feather = max(2.0, CFG["video_feather"] * tw / 1080.0)
    xs = np.arange(tw, dtype=np.float32)[None, :, None]

    out = job.dir / "transition.mp4"
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{tw}x{th}",
           "-r", str(fps), "-i", "-", "-an", "-c:v", "libx264",
           "-preset", "medium", "-crf", str(CFG["video_crf"]),
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    try:
        def emit(frame):
            proc.stdin.write(frame.astype(np.uint8).tobytes())
        before8 = A.astype(np.uint8)
        after8 = B.astype(np.uint8)
        for _ in range(n_hold):
            emit(before8)
        for i in range(n_sweep):
            t = _ease((i + 1) / n_sweep)
            if style == "fade":
                emit(A * (1.0 - t) + B * t)
            else:
                seam = t * (tw + 2 * feather) - feather
                alpha = np.clip((seam - xs) / feather + 0.5, 0.0, 1.0)
                emit(A * (1.0 - alpha) + B * alpha)
        for _ in range(n_hold):
            emit(after8)
        proc.stdin.close()
        rc = proc.wait(timeout=600)
        if rc != 0:
            raise AlignError("ffmpeg failed: "
                             + proc.stderr.read().decode("utf8", "replace")[:400])
    finally:
        if proc.poll() is None:
            proc.kill()
    job.exports["video"] = out
    return out


def run_export(job, spec):
    try:
        job.set("exporting", "Saving the aligned photos")
        export_images(job)
        if spec.get("video"):
            job.set("exporting", "Rendering the video")
            export_video(job, aspect=spec.get("aspect", "4:5"),
                         style=spec.get("style", "wipe"),
                         seconds=float(spec.get("seconds", 4.6)))
        job.set("ready", "Export finished")
    except AlignError as e:
        job.set("ready", "")
        with job.lock:
            job.error = str(e)
    except Exception as e:
        log.error("export crashed:\n%s", traceback.format_exc())
        job.set("ready", "")
        with job.lock:
            job.error = f"Unexpected problem while exporting: {e}"


# ---------------------------------------------------------------------------
# HTTP layer (stdlib only; Python 3.13 removed cgi, so multipart is parsed
# by hand: two known fields, bounded body, binary-safe)
# ---------------------------------------------------------------------------

JOBS = {}
JOBS_LOCK = threading.Lock()
WORKDIR = Path(__file__).resolve().parent / "_reveal"
JOB_ID_RE = re.compile(r"^[a-f0-9]{12,32}$")
SAFE_EXPORTS = {"before", "after_aligned", "video"}


def parse_multipart(body, content_type):
    """Minimal, binary-safe multipart/form-data parser for exactly the
    fields this tool accepts. Returns {name: {filename, data}}."""
    m = re.search(r'boundary="?([^";]+)"?', content_type or "")
    if not m:
        raise ValueError("multipart boundary missing")
    delim = b"--" + m.group(1).encode("utf8")
    fields = {}
    for part in body.split(delim)[1:]:
        if part.startswith(b"--"):
            break                      # closing delimiter
        part = part[2:] if part.startswith(b"\r\n") else part
        head, sep, data = part.partition(b"\r\n\r\n")
        if not sep:
            continue
        if data.endswith(b"\r\n"):
            data = data[:-2]
        hd = head.decode("utf8", "replace")
        nm = re.search(r'name="([^"]*)"', hd)
        if not nm:
            continue
        fn = re.search(r'filename="([^"]*)"', hd)
        fields[nm.group(1)] = {
            "filename": os.path.basename(fn.group(1)) if fn else None,
            "data": data}
    return fields


def _clamp_params(raw, prof=None):
    prof = prof or CFG
    p = default_params()
    def num(k, lo, hi, default):
        try:
            v = float(raw.get(k, default))
        except (TypeError, ValueError):
            return default
        return min(hi, max(lo, v))
    p["dx"] = num("dx", -prof["tune_shift"], prof["tune_shift"], 0.0)
    p["dy"] = num("dy", -prof["tune_shift"], prof["tune_shift"], 0.0)
    p["rot"] = num("rot", -prof["tune_rot"], prof["tune_rot"], 0.0)
    p["scale"] = num("scale", 1 - prof["tune_scale"],
                     1 + prof["tune_scale"], 1.0)
    p["kh"] = num("kh", -1.0, 1.0, 0.0)
    p["kv"] = num("kv", -1.0, 1.0, 0.0)
    p["exposure"] = int(num("exposure", 0, 100, 0))
    return p


class Handler(BaseHTTPRequestHandler):
    server_version = f"Reveal/{VERSION}"
    protocol_version = "HTTP/1.1"

    # -- plumbing -----------------------------------------------------------
    def log_message(self, fmt, *args):
        log.debug("http %s", fmt % args)

    def _send(self, code, body, ctype="application/json", extra=None):
        data = body if isinstance(body, (bytes, bytearray)) else \
            json.dumps(body).encode("utf8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _err(self, code, msg):
        self._send(code, {"error": msg})

    def _job(self, jid):
        if not JOB_ID_RE.match(jid or ""):
            return None
        with JOBS_LOCK:
            return JOBS.get(jid)

    def _read_body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            raise ValueError("empty request body")
        if n > CFG["upload_cap"]:
            raise ValueError("request too large")
        buf = b""
        while len(buf) < n:
            chunk = self.rfile.read(min(1 << 20, n - len(buf)))
            if not chunk:
                break
            buf += chunk
        if len(buf) != n:
            raise ValueError("truncated request body")
        return buf

    # -- routes -------------------------------------------------------------
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/":
            html = INDEX_HTML.replace("{{VERSION}}", VERSION)
            self._send(200, html.encode("utf8"), "text/html; charset=utf-8")
            return
        m = re.match(r"^/api/job/([^/]+)/status$", path)
        if m:
            job = self._job(m.group(1))
            if not job:
                return self._err(404, "unknown job")
            return self._send(200, job.status())
        m = re.match(r"^/api/job/([^/]+)/img/(before|after)$", path)
        if m:
            job = self._job(m.group(1))
            if not job:
                return self._err(404, "unknown job")
            p = job.dir / f"preview_{m.group(2)}.jpg"
            if not p.exists():
                return self._err(404, "preview not ready")
            return self._send(200, p.read_bytes(), "image/jpeg")
        m = re.match(r"^/api/job/([^/]+)/download/([a-z_]+)$", path)
        if m:
            job = self._job(m.group(1))
            name = m.group(2)
            if not job or name not in SAFE_EXPORTS:
                return self._err(404, "unknown export")
            p = job.exports.get(name)
            if not p or not p.exists():
                return self._err(404, "not exported yet")
            ctype = "video/mp4" if p.suffix == ".mp4" else "image/jpeg"
            return self._send(200, p.read_bytes(), ctype, {
                "Content-Disposition": f'attachment; filename="{p.name}"'})
        self._err(404, "not found")

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        try:
            if path == "/api/job":
                return self._post_job()
            m = re.match(r"^/api/job/([^/]+)/tune$", path)
            if m:
                return self._post_tune(m.group(1))
            m = re.match(r"^/api/job/([^/]+)/export$", path)
            if m:
                return self._post_export(m.group(1))
            self._err(404, "not found")
        except ValueError as e:
            self._err(400, str(e))
        except Exception as e:
            log.error("POST %s crashed:\n%s", path, traceback.format_exc())
            self._err(500, f"server error: {e}")

    def _post_job(self):
        fields = parse_multipart(self._read_body(),
                                 self.headers.get("Content-Type"))
        missing = [k for k in ("before", "after") if k not in fields
                   or not fields[k]["data"]]
        if missing:
            return self._err(400, f"missing file field(s): {missing}")
        jid = uuid.uuid4().hex[:16]
        mode = (fields.get("mode", {}).get("data") or b"reshot") \
            .decode("utf8", "replace").strip()
        job = Job(jid, WORKDIR, mode)
        paths = []
        for k in ("before", "after"):
            fn = fields[k]["filename"] or f"{k}.bin"
            ext = Path(fn).suffix.lower()
            if ext not in ACCEPT_EXTS:
                shutil.rmtree(job.dir, ignore_errors=True)
                return self._err(400,
                                 f"'{fn}': unsupported type {ext or '(none)'}."
                                 f" Accepted: {', '.join(sorted(ACCEPT_EXTS))}")
            p = job.dir / f"input_{k}{ext}"
            p.write_bytes(fields[k]["data"])
            paths.append(p)
        with JOBS_LOCK:
            JOBS[jid] = job
        threading.Thread(target=run_alignment, args=(job, *paths),
                         daemon=True).start()
        self._send(200, {"id": jid})

    def _post_tune(self, jid):
        job = self._job(jid)
        if not job:
            return self._err(404, "unknown job")
        if job.state not in ("ready",):
            return self._err(409, "job is busy")
        raw = json.loads(self._read_body().decode("utf8"))
        job.params = _clamp_params(raw, job.prof)
        try:
            render_previews(job)
        except AlignError as e:
            return self._err(500, str(e))
        self._send(200, job.status())

    def _post_export(self, jid):
        job = self._job(jid)
        if not job:
            return self._err(404, "unknown job")
        if job.state not in ("ready",):
            return self._err(409, "job is busy")
        spec = json.loads(self._read_body().decode("utf8") or "{}")
        with job.lock:
            job.error = None
        threading.Thread(target=run_export, args=(job, spec),
                         daemon=True).start()
        self._send(200, {"ok": True})


def serve(port=DEFAULT_PORT, open_browser=True, workdir=None):
    global WORKDIR
    if workdir:
        WORKDIR = Path(workdir).expanduser().resolve()
    WORKDIR.mkdir(parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    print(f"Reveal {VERSION} is running at {url}  (Ctrl+C to stop)")
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return httpd


# ---------------------------------------------------------------------------
# The page (single file, vanilla JS, no build step)
# ---------------------------------------------------------------------------

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reveal</title>
<style>
:root{
  --bg:#191210; --panel:#221a15; --panel2:#2a2019; --line:#3b2d22;
  --ink:#f2e8da; --dim:#a5937f; --faint:#6f6153;
  --amber:#eda45c; --amber-hi:#ffc078; --amber-dim:#8a5c2e;
  --paper:#f5eee2; --ok:#a8c686; --warn:#d98a6a;
  --serif:ui-serif,"New York",Georgia,"Times New Roman",serif;
  --sans:-apple-system,BlinkMacSystemFont,"SF Pro Text",system-ui,sans-serif;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.55 var(--sans)}
body{min-height:100vh;display:flex;flex-direction:column;align-items:center;
  padding:0 20px 64px}
a{color:var(--amber)}
header{width:100%;max-width:1100px;display:flex;align-items:baseline;
  gap:14px;padding:26px 4px 8px}
.wordmark{font-family:var(--serif);font-style:italic;font-size:26px;
  letter-spacing:.5px;color:var(--ink)}
.wordmark b{color:var(--amber);font-weight:600}
.tag{color:var(--faint);font-size:12.5px}
.ver{margin-left:auto;color:var(--faint);font-size:11.5px}
main{width:100%;max-width:1100px}
.screen{display:none}
.screen.on{display:block;animation:rise .35s ease}
@keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1}}
@media (prefers-reduced-motion:reduce){
  .screen.on{animation:none}
  *{transition:none!important;animation:none!important}
}

/* ---- drop screen ---- */
.lede{max-width:560px;color:var(--dim);margin:26px 0 22px;font-size:15.5px}
.lede em{color:var(--ink);font-style:normal}
.drops{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:720px){.drops{grid-template-columns:1fr}}
.drop{position:relative;border:1.5px dashed var(--line);border-radius:10px;
  background:var(--panel);min-height:240px;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:8px;cursor:pointer;
  transition:border-color .15s,background .15s;overflow:hidden;padding:14px}
.drop:hover,.drop.hover{border-color:var(--amber-dim);background:var(--panel2)}
.drop.set{border-style:solid;border-color:var(--line)}
.drop .slot{font-family:var(--serif);font-size:19px;color:var(--ink)}
.drop .hint{color:var(--faint);font-size:12.5px;text-align:center}
.drop img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;
  opacity:.92}
.drop .badge{position:absolute;left:10px;top:10px;background:rgba(20,13,9,.82);
  border:1px solid var(--line);color:var(--ink);font-size:12px;
  padding:3px 10px;border-radius:99px;z-index:2}
.drop input{display:none}
.actions{margin-top:22px;display:flex;align-items:center;gap:16px}
button{font:600 14.5px var(--sans);border-radius:99px;padding:11px 22px;
  cursor:pointer;border:1px solid var(--line);background:var(--panel2);
  color:var(--ink);transition:border-color .15s,background .15s}
button:hover{border-color:var(--amber-dim)}
button.primary{background:var(--amber);border-color:var(--amber);
  color:#241609}
button.primary:hover{background:var(--amber-hi);border-color:var(--amber-hi)}
button:disabled{opacity:.42;cursor:default}
button:focus-visible,.drop:focus-visible,.compare:focus-visible{
  outline:2px solid var(--amber);outline-offset:2px}
.formats{color:var(--faint);font-size:12px}
.modes{display:flex;gap:0;margin-top:20px;border:1px solid var(--line);
  border-radius:99px;overflow:hidden;width:fit-content;max-width:100%}
.modes label{padding:10px 18px;cursor:pointer;color:var(--dim);
  font-size:13.5px;transition:background .15s,color .15s;white-space:nowrap}
.modes label+label{border-left:1px solid var(--line)}
.modes input{position:absolute;opacity:0;pointer-events:none}
.modes input:checked+span{color:#241609}
.modes label:has(input:checked){background:var(--amber);color:#241609}
.modes label:has(input:focus-visible){outline:2px solid var(--amber);
  outline-offset:2px}
.modehint{color:var(--faint);font-size:12.5px;margin:10px 2px 0}

/* ---- working screen ---- */
.stages{margin:44px auto;max-width:420px;background:var(--panel);
  border:1px solid var(--line);border-radius:12px;padding:26px 30px}
.stage{display:flex;gap:14px;align-items:center;padding:9px 0;
  color:var(--faint)}
.stage .dot{width:10px;height:10px;border-radius:50%;
  border:1.5px solid var(--faint);flex:none}
.stage.done{color:var(--dim)}
.stage.done .dot{background:var(--amber-dim);border-color:var(--amber-dim)}
.stage.now{color:var(--ink)}
.stage.now .dot{background:var(--amber);border-color:var(--amber);
  animation:pulse 1.1s ease-in-out infinite}
@keyframes pulse{50%{box-shadow:0 0 0 6px rgba(237,164,92,.18)}}

/* ---- viewer ---- */
.print{background:var(--paper);padding:12px;border-radius:3px;
  box-shadow:0 18px 50px rgba(0,0,0,.5);margin-top:22px}
.compare{position:relative;overflow:hidden;user-select:none;
  touch-action:none;cursor:ew-resize;--pos:50%;line-height:0}
.compare img{width:100%;display:block;pointer-events:none}
.compare .top{position:absolute;inset:0;
  clip-path:inset(0 calc(100% - var(--pos)) 0 0)}
.compare .seam{position:absolute;top:0;bottom:0;left:var(--pos);width:0;
  border-left:1.5px solid var(--amber);
  box-shadow:0 0 12px rgba(237,164,92,.55)}
.compare .grip{position:absolute;top:50%;left:var(--pos);
  transform:translate(-50%,-50%);width:40px;height:40px;border-radius:50%;
  background:rgba(25,18,14,.85);border:1.5px solid var(--amber);
  color:var(--amber);display:flex;align-items:center;justify-content:center;
  font-size:13px;letter-spacing:2px}
.lbl{position:absolute;top:10px;font-size:11px;letter-spacing:1.5px;
  text-transform:uppercase;background:rgba(25,18,14,.7);color:var(--ink);
  padding:3px 9px;border-radius:99px}
.lbl.a{left:10px}.lbl.b{right:10px}

.metrics{display:flex;flex-wrap:wrap;align-items:baseline;gap:26px;
  margin:18px 2px 6px}
.metric .n{font-family:var(--serif);font-size:30px;color:var(--ink)}
.metric.co .n{color:var(--amber)}
.metric .u{color:var(--faint);font-size:11.5px;letter-spacing:1.2px;
  text-transform:uppercase;display:block;margin-top:-3px}
.chip{margin-left:auto;color:var(--dim);font-size:12.5px;
  border:1px solid var(--line);padding:4px 12px;border-radius:99px}
.note{color:var(--dim);font-size:13px;margin:6px 2px}
.note.warn{color:var(--warn)}

/* ---- panels ---- */
details{margin-top:20px;background:var(--panel);border:1px solid var(--line);
  border-radius:12px}
summary{cursor:pointer;padding:15px 20px;font-weight:600;color:var(--ink);
  list-style:none;display:flex;align-items:center}
summary::after{content:"";width:8px;height:8px;margin-left:auto;
  border-right:1.5px solid var(--dim);border-bottom:1.5px solid var(--dim);
  transform:rotate(45deg);transition:transform .15s}
details[open] summary::after{transform:rotate(-135deg)}
.panelbody{padding:4px 20px 20px}
.sliders{display:grid;grid-template-columns:1fr 1fr;gap:6px 34px}
@media(max-width:720px){.sliders{grid-template-columns:1fr}}
.sl{display:grid;grid-template-columns:96px 1fr 58px;align-items:center;
  gap:12px;padding:7px 0}
.sl label{color:var(--dim);font-size:13px}
.sl output{color:var(--ink);font-size:12.5px;text-align:right;
  font-variant-numeric:tabular-nums}
input[type=range]{-webkit-appearance:none;appearance:none;height:3px;
  background:var(--line);border-radius:2px;outline:none}
input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:16px;
  height:16px;border-radius:50%;background:var(--amber);cursor:pointer;
  border:2px solid #241609}
input[type=range]:focus-visible::-webkit-slider-thumb{
  box-shadow:0 0 0 4px rgba(237,164,92,.3)}
.panelfoot{display:flex;gap:14px;margin-top:12px;align-items:center}
.linkish{background:none;border:none;color:var(--dim);padding:6px 2px;
  font-size:13px;text-decoration:underline;text-underline-offset:3px}
.linkish:hover{color:var(--ink);border:none}
.hinttext{color:var(--faint);font-size:12px}

.exports{display:flex;flex-wrap:wrap;gap:14px;align-items:center}
select{font:14px var(--sans);background:var(--panel2);color:var(--ink);
  border:1px solid var(--line);border-radius:8px;padding:9px 12px}
.exports .grow{flex:1}
.foot{margin-top:26px;display:flex;gap:18px;align-items:center}

/* ---- failure ---- */
.failbox{margin:44px auto;max-width:520px;background:var(--panel);
  border:1px solid var(--line);border-left:3px solid var(--warn);
  border-radius:12px;padding:26px 30px}
.failbox h2{font-family:var(--serif);font-weight:600;margin:0 0 10px}
.failbox p{color:var(--dim)}
</style>
</head>
<body>
<header>
  <span class="wordmark">Re<b>veal</b></span>
  <span class="tag">line up a before and an after, then slide</span>
  <span class="ver">v{{VERSION}}</span>
</header>
<main>

<section id="s-drop" class="screen on">
  <p class="lede">Drop in two photos of the <em>same subject</em> taken at
  different times, shot from roughly the same spot. Reveal lines the second
  one up with the first: position, angle, scale, perspective, and light.</p>
  <div class="drops">
    <div class="drop" id="drop-before" tabindex="0">
      <span class="badge">Before</span>
      <span class="slot">The earlier photo</span>
      <span class="hint">drop it here, or click to choose</span>
      <input type="file" accept=".jpg,.jpeg,.png,.heic,.heif,.hif,.dng,.arw,.webp,.tif,.tiff,.bmp">
    </div>
    <div class="drop" id="drop-after" tabindex="0">
      <span class="badge">After</span>
      <span class="slot">The later photo</span>
      <span class="hint">drop it here, or click to choose</span>
      <input type="file" accept=".jpg,.jpeg,.png,.heic,.heif,.hif,.dng,.arw,.webp,.tif,.tiff,.bmp">
    </div>
  </div>
  <div class="modes" role="radiogroup" aria-label="How alike are the photos">
    <label><input type="radio" name="mode" value="reshot" checked>
      <span>Same scene, re-shot</span></label>
    <label><input type="radio" name="mode" value="loose">
      <span>Just similar</span></label>
  </div>
  <p class="modehint" id="modehint">The same place photographed again:
    Reveal expects the frames to nearly agree and holds itself to a
    strict fit.</p>
  <div class="actions">
    <button class="primary" id="go" disabled>Line them up</button>
    <span class="formats">JPEG · PNG · HEIC · DNG · ARW</span>
  </div>
  <p class="note warn" id="drop-err" hidden></p>
</section>

<section id="s-work" class="screen">
  <div class="stages" id="stages">
    <div class="stage" data-s="decoding"><span class="dot"></span>Reading the two photos</div>
    <div class="stage" data-s="aligning"><span class="dot"></span>Finding common detail</div>
    <div class="stage" data-s="refining"><span class="dot"></span>Polishing the fit</div>
    <div class="stage" data-s="rendering"><span class="dot"></span>Preparing the preview</div>
  </div>
</section>

<section id="s-view" class="screen">
  <div class="print">
    <div class="compare" id="compare" tabindex="0"
         aria-label="Before and after comparison. Use left and right arrow keys to move the seam.">
      <img id="img-before" alt="Before">
      <div class="top"><img id="img-after" alt="After"></div>
      <span class="lbl a">After</span><span class="lbl b">Before</span>
      <div class="seam"></div>
      <div class="grip">◂▸</div>
    </div>
  </div>

  <div class="metrics">
    <span class="metric co"><span class="n" id="m-conf">–</span>
      <span class="u">match score</span></span>
    <span class="metric"><span class="n" id="m-inl">–</span>
      <span class="u">anchor points</span></span>
    <span class="metric"><span class="n" id="m-rmse">–</span>
      <span class="u">drift, px</span></span>
    <span class="metric"><span class="n" id="m-chg">–</span>
      <span class="u">changed area</span></span>
    <span class="chip" id="m-method">–</span>
  </div>
  <p class="note" id="view-note"></p>

  <details id="tune">
    <summary>Fine-tune by hand</summary>
    <div class="panelbody">
      <div class="sliders">
        <div class="sl"><label for="t-dx">Sideways</label>
          <input type="range" id="t-dx" min="-100" max="100" value="0">
          <output for="t-dx">0</output></div>
        <div class="sl"><label for="t-dy">Up / down</label>
          <input type="range" id="t-dy" min="-100" max="100" value="0">
          <output for="t-dy">0</output></div>
        <div class="sl"><label for="t-rot">Rotate</label>
          <input type="range" id="t-rot" min="-100" max="100" value="0">
          <output for="t-rot">0°</output></div>
        <div class="sl"><label for="t-scale">Size</label>
          <input type="range" id="t-scale" min="-100" max="100" value="0">
          <output for="t-scale">100%</output></div>
        <div class="sl"><label for="t-kh">Lean left / right</label>
          <input type="range" id="t-kh" min="-100" max="100" value="0">
          <output for="t-kh">0</output></div>
        <div class="sl"><label for="t-kv">Lean back / forward</label>
          <input type="range" id="t-kv" min="-100" max="100" value="0">
          <output for="t-kv">0</output></div>
        <div class="sl"><label for="t-expo">Match the light</label>
          <input type="range" id="t-expo" min="0" max="100" value="0">
          <output for="t-expo">off</output></div>
      </div>
      <div class="panelfoot">
        <button class="linkish" id="t-reset">Reset all</button>
        <span class="hinttext">double-click any slider to reset it ·
          changes apply when you let go</span>
      </div>
    </div>
  </details>

  <details id="exp" open>
    <summary>Save the result</summary>
    <div class="panelbody">
      <div class="exports">
        <select id="e-aspect" aria-label="Video format">
          <option value="4:5">Portrait 4:5 (Instagram post)</option>
          <option value="9:16">Vertical 9:16 (Stories, Reels)</option>
          <option value="16:9">Wide 16:9</option>
          <option value="1:1">Square 1:1</option>
          <option value="original">Original shape</option>
        </select>
        <select id="e-style" aria-label="Transition style">
          <option value="wipe">Sliding reveal</option>
          <option value="fade">Cross-fade</option>
        </select>
        <select id="e-secs" aria-label="Video length">
          <option value="3.5">Quick · 3.5 s</option>
          <option value="4.6" selected>Classic · 4.6 s</option>
          <option value="6.5">Slow · 6.5 s</option>
        </select>
        <span class="grow"></span>
        <button class="primary" id="e-video">Save video</button>
        <button id="e-photos">Save aligned photos</button>
      </div>
      <p class="note" id="exp-note"></p>
    </div>
  </details>

  <div class="foot">
    <button class="linkish" id="restart">Start over with two new photos</button>
  </div>
</section>

<section id="s-fail" class="screen">
  <div class="failbox">
    <h2>That pair didn't line up</h2>
    <p id="fail-msg"></p>
    <button class="primary" id="fail-loose" hidden>Retry with loose
      matching</button>
    <button id="fail-restart">Try another pair</button>
  </div>
</section>

</main>
<script>
"use strict";
const $ = s => document.querySelector(s);
const state = {job:null, files:{before:null, after:null}, params:null,
               rendered:null, timer:null, exporting:false, swept:false,
               mode:"reshot"};
let LIM = {shift:0.05, rot:3.0, scale:0.06};
const MODEHINT = {
  reshot:"The same place photographed again: Reveal expects the frames "+
    "to nearly agree and holds itself to a strict fit.",
  loose:"Different but alike: another person in the same spot, or two "+
    "look-alike subjects. Reveal matches what it can and hands you "+
    "wider sliders."
};
document.querySelectorAll('input[name="mode"]').forEach(r=>{
  r.addEventListener("change", ()=>{
    state.mode = r.value;
    $("#modehint").textContent = MODEHINT[r.value];
  });
});

function show(id){
  document.querySelectorAll(".screen").forEach(s=>s.classList.remove("on"));
  $(id).classList.add("on");
}

/* ---------- drop screen ---------- */
function wireDrop(which){
  const el = $("#drop-"+which), input = el.querySelector("input");
  const set = f => {
    if(!f) return;
    state.files[which]=f;
    el.classList.add("set");
    el.querySelectorAll("img").forEach(i=>i.remove());
    if(/\\.(jpe?g|png|webp)$/i.test(f.name)){
      const img=document.createElement("img");
      img.src=URL.createObjectURL(f); el.appendChild(img);
    } else {
      el.querySelector(".slot").textContent=f.name;
      el.querySelector(".hint").textContent="ready";
    }
    $("#go").disabled = !(state.files.before && state.files.after);
  };
  el.addEventListener("click", ()=>input.click());
  el.addEventListener("keydown", e=>{
    if(e.key==="Enter"||e.key===" "){e.preventDefault();input.click();}});
  input.addEventListener("change", ()=>set(input.files[0]));
  el.addEventListener("dragover", e=>{e.preventDefault();el.classList.add("hover");});
  el.addEventListener("dragleave", ()=>el.classList.remove("hover"));
  el.addEventListener("drop", e=>{
    e.preventDefault(); el.classList.remove("hover");
    set(e.dataTransfer.files[0]);
  });
}
wireDrop("before"); wireDrop("after");

async function submitPair(){
  $("#go").disabled = true;
  $("#drop-err").hidden = true;
  const fd = new FormData();
  fd.append("before", state.files.before);
  fd.append("after", state.files.after);
  fd.append("mode", state.mode);
  show("#s-work"); markStage(null);
  try{
    const r = await fetch("/api/job", {method:"POST", body:fd});
    const j = await r.json();
    if(!r.ok) throw new Error(j.error || "upload failed");
    state.job = j.id; state.params = null;
    poll();
  }catch(err){
    show("#s-drop");
    $("#go").disabled=false;
    const e=$("#drop-err"); e.textContent=err.message; e.hidden=false;
  }
}
$("#go").addEventListener("click", submitPair);

/* ---------- progress ---------- */
const ORDER = ["decoding","aligning","refining","rendering"];
function markStage(s){
  const idx = ORDER.indexOf(s);
  document.querySelectorAll(".stage").forEach((el,i)=>{
    el.classList.toggle("done", idx>i);
    el.classList.toggle("now", idx===i);
  });
}
async function poll(){
  clearTimeout(state.timer);
  let j;
  try{
    const r = await fetch(`/api/job/${state.job}/status`);
    j = await r.json();
    if(!r.ok) throw new Error(j.error||"lost the job");
  }catch(err){ return fail(err.message); }
  if(j.state==="failed") return fail(j.error);
  if(ORDER.includes(j.state)){ markStage(j.state);
    state.timer=setTimeout(poll, 600); return; }
  if(j.state==="exporting"){
    $("#exp-note").textContent = j.note || "Working…";
    state.timer=setTimeout(poll, 700); return; }
  if(j.state==="ready"){
    if(state.exporting){ state.exporting=false; exportDone(j); }
    else if(!state.params) ready(j);
  }
}
function fail(msg){
  $("#fail-msg").textContent = msg ||
    "Something went wrong reading or matching the photos.";
  $("#fail-loose").hidden = !(state.mode==="reshot"
    && state.files.before && state.files.after);
  show("#s-fail");
}
$("#fail-loose").addEventListener("click", ()=>{
  state.mode = "loose";
  const r = document.querySelector('input[name="mode"][value="loose"]');
  if(r){ r.checked = true; $("#modehint").textContent = MODEHINT.loose; }
  submitPair();
});

/* ---------- viewer ---------- */
function imgURL(which){
  return `/api/job/${state.job}/img/${which}?k=${encodeURIComponent(state.renderedKey||"0")}`;
}
function loadImages(){
  state.renderedKey = JSON.stringify(state.rendered);
  $("#img-before").src = imgURL("before");
  $("#img-after").src  = imgURL("after");
  $("#img-after").style.transform = "";
}
function ready(j){
  if(j.limits) LIM = j.limits;
  state.params  = {...j.params};
  state.rendered= {...j.params};
  fillMetrics(j);
  syncSliders();
  loadImages();
  show("#s-view");
  if(!state.swept){ state.swept=true; sweep(); }
}
function fillMetrics(j){
  const m=j.metrics||{};
  $("#m-conf").textContent = m.confidence ?? "–";
  $("#m-inl").textContent  = m.inliers ?? "–";
  $("#m-rmse").textContent = m.rmse_px==null ? "–" : m.rmse_px.toFixed(1);
  $("#m-chg").textContent  = m.changed_pct==null ? "–" : m.changed_pct+"%";
  const NAMES = {sift:"matched on fine detail", orb:"matched on corners",
    learned:"matched by the neural matcher",
    "phase+ecc":"matched by brightness patterns",
    "sift+sim":"rigid fit on fine detail", "orb+sim":"rigid fit on corners",
    "learned+sim":"rigid fit by the neural matcher"};
  $("#m-method").textContent = (NAMES[m.method]||m.method||"–")
    + (j.mode==="loose" ? " · loose" : "");
  const note=$("#view-note");
  if(m.passed===false && j.mode==="loose"){
    note.textContent="Similar-but-different photos rarely score high: the "+
      "numbers compare pixels that genuinely differ. Trust your eyes and "+
      "the sliders below.";
    note.classList.remove("warn");
  } else if(m.passed===false){
    note.textContent="The automatic fit is below Reveal's usual bar. It may "+
      "still look right; nudge it by hand below if it doesn't.";
    note.classList.add("warn");
  } else if((j.auto_exposure||0)>0){
    note.textContent="The two photos were lit differently, so the light was "+
      "matched automatically. The slider below controls how strongly.";
    note.classList.remove("warn");
  } else { note.textContent=""; }
}

/* seam drag */
const cmp = $("#compare");
let pos = 50;
function setPos(p){
  pos = Math.max(0, Math.min(100, p));
  cmp.style.setProperty("--pos", pos+"%");
}
cmp.addEventListener("pointerdown", e=>{
  cmp.setPointerCapture(e.pointerId);
  const move = ev=>{
    const r = cmp.getBoundingClientRect();
    setPos((ev.clientX - r.left)/r.width*100);
  };
  move(e);
  cmp.addEventListener("pointermove", move);
  cmp.addEventListener("pointerup", ()=>
    cmp.removeEventListener("pointermove", move), {once:true});
});
cmp.addEventListener("keydown", e=>{
  if(e.key==="ArrowLeft"){ setPos(pos-3); e.preventDefault(); }
  if(e.key==="ArrowRight"){ setPos(pos+3); e.preventDefault(); }
});
function sweep(){
  if(matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const t0 = performance.now(), D=2100;
  const step = t=>{
    const u = Math.min(1,(t-t0)/D);
    const e = .5-.5*Math.cos(Math.PI*u);          /* ease in-out */
    setPos(u<.5 ? e*2*100 : 100-(e*2-1)*50);      /* 0→100→50 */
    if(u<1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

/* ---------- tuning ---------- */
const SL = {dx:"#t-dx", dy:"#t-dy", rot:"#t-rot", scale:"#t-scale",
            kh:"#t-kh", kv:"#t-kv", exposure:"#t-expo"};
function sliderToParam(k,v){
  v = Number(v);
  if(k==="dx"||k==="dy") return v/100*LIM.shift;
  if(k==="rot")   return v/100*LIM.rot;
  if(k==="scale") return 1+v/100*LIM.scale;
  if(k==="kh"||k==="kv") return v/100;
  return v;                                   /* exposure 0..100 */
}
function paramToSlider(k,v){
  if(k==="dx"||k==="dy") return Math.round(v/LIM.shift*100);
  if(k==="rot")   return Math.round(v/LIM.rot*100);
  if(k==="scale") return Math.round((v-1)/LIM.scale*100);
  if(k==="kh"||k==="kv") return Math.round(v*100);
  return Math.round(v);
}
function fmtOut(k,v){
  if(k==="rot")   return (v>=0?"+":"")+v.toFixed(LIM.rot>5?1:2)+"°";
  if(k==="scale") return Math.round(v*100)+"%";
  if(k==="exposure") return v>0 ? v+"%" : "off";
  if(k==="dx"||k==="dy") return (v>=0?"+":"")+(v*100).toFixed(1)+"%";
  return String(Math.round(v*100)/100);
}
function syncSliders(){
  for(const k in SL){
    const el=$(SL[k]);
    el.value = paramToSlider(k, state.params[k]);
    el.nextElementSibling.textContent = fmtOut(k, state.params[k]);
  }
}
function cssPreview(){
  /* approximate live preview: transform the AFTER layer by the delta
     between the pending params and the last rendered params */
  const img=$("#img-after"), r=img.getBoundingClientRect();
  const p=state.params, q=state.rendered;
  const dx=(p.dx-q.dx)*r.width, dy=(p.dy-q.dy)*r.height;
  const rot=p.rot-q.rot, s=p.scale/q.scale;
  img.style.transform =
    `translate(${dx}px,${dy}px) rotate(${rot}deg) scale(${s})`;
}
let tuneBusy=false;
async function pushTune(){
  if(tuneBusy) return;
  tuneBusy=true;
  try{
    const r = await fetch(`/api/job/${state.job}/tune`,
      {method:"POST", body:JSON.stringify(state.params)});
    const j = await r.json();
    if(!r.ok) throw new Error(j.error||"tune failed");
    state.params  = {...j.params};
    state.rendered= {...j.params};
    fillMetrics(j);
    loadImages();
  }catch(err){
    $("#view-note").textContent = err.message;
    $("#view-note").classList.add("warn");
  }finally{ tuneBusy=false; }
}
for(const k in SL){
  const el=$(SL[k]);
  el.addEventListener("input", ()=>{
    state.params[k]=sliderToParam(k, el.value);
    el.nextElementSibling.textContent=fmtOut(k, state.params[k]);
    if(["dx","dy","rot","scale"].includes(k)) cssPreview();
  });
  el.addEventListener("change", pushTune);
  el.addEventListener("dblclick", ()=>{
    el.value = k==="scale"?0:0;
    state.params[k] = k==="scale"?1:0;
    el.nextElementSibling.textContent=fmtOut(k, state.params[k]);
    pushTune();
  });
}
$("#t-reset").addEventListener("click", ()=>{
  state.params={dx:0,dy:0,rot:0,scale:1,kh:0,kv:0,exposure:0};
  syncSliders(); pushTune();
});

/* ---------- export ---------- */
function download(name){
  const a=document.createElement("a");
  a.href=`/api/job/${state.job}/download/${name}`;
  a.download=""; document.body.appendChild(a); a.click(); a.remove();
}
$("#e-video").addEventListener("click", async ()=>{
  $("#exp-note").textContent="Rendering the video…";
  state.exporting=true;
  await fetch(`/api/job/${state.job}/export`, {method:"POST",
    body:JSON.stringify({video:true, aspect:$("#e-aspect").value,
      style:$("#e-style").value, seconds:Number($("#e-secs").value)})});
  poll();
});
$("#e-photos").addEventListener("click", async ()=>{
  $("#exp-note").textContent="Saving the aligned photos…";
  state.exporting=true;
  await fetch(`/api/job/${state.job}/export`,
    {method:"POST", body:JSON.stringify({video:false})});
  poll();
});
function exportDone(j){
  if(j.error){
    $("#exp-note").textContent=j.error; return;
  }
  $("#exp-note").textContent="Saved. Your downloads are on their way.";
  if(j.exports.video) download("video");
  download("after_aligned"); download("before");
}

/* ---------- restart ---------- */
function restart(){ location.reload(); }
$("#restart").addEventListener("click", restart);
$("#fail-restart").addEventListener("click", restart);
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _learned_status():
    if not learned_available():
        return "off (optional; ./setup.sh --learned)"
    if not learned_weights_cached():
        return "installed, but model files are MISSING: ./setup.sh --learned"
    man = learned_manifest()
    mb = sum(f["size"] for f in man["files"]) / 1e6
    intact = learned_weights_cached(deep=True)
    return (f"ready, offline ({man['matcher']}, {len(man['files'])} files, "
            f"{mb:.0f} MB in ./models"
            + ("" if intact else ", CHECKSUM MISMATCH: re-run setup") + ")")


def cmd_check():
    rows = [
        ("python", sys.version.split()[0], True),
        ("opencv", cv2.__version__, True),
        ("numpy", np.__version__, True),
        ("SIFT", "available" if hasattr(cv2, "SIFT_create") else "missing",
         hasattr(cv2, "SIFT_create")),
        ("MAGSAC++", "available" if hasattr(cv2, "USAC_MAGSAC")
         else "RANSAC fallback", True),
        ("HEIC decode", "ok" if pillow_heif else f"OFF ({_HEIF_ERR})",
         pillow_heif is not None),
        ("RAW decode", "ok" if rawpy else f"OFF ({_RAWPY_ERR})",
         rawpy is not None),
        ("video export", "ok" if imageio_ffmpeg else f"OFF ({_FFMPEG_ERR})",
         imageio_ffmpeg is not None),
        ("learned matcher", _learned_status(),
         (not learned_available()) or learned_weights_cached()),
    ]
    bad = 0
    for name, val, ok in rows:
        print(f"  {'OK ' if ok else '!! '}{name:<16} {val}")
        bad += 0 if ok else 1
    if bad:
        print(f"\n{bad} problem(s); re-run ./setup.sh")
    return 1 if bad else 0


def _selftest_pair(w=512, h=384):
    """A textured synthetic pair with a known shift, used to force every
    lazy code path (and therefore every lazy download) to execute during
    warmup rather than during a real job."""
    r = np.random.default_rng(0)
    img = np.full((h, w), 120, np.uint8)
    for _ in range(220):
        cv2.circle(img, (int(r.integers(0, w)), int(r.integers(0, h))),
                   int(r.integers(3, 14)), int(r.integers(20, 240)), -1)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    M = np.float32([[1, 0, 9], [0, 1, -5]])
    return img, cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)


def cmd_warmup():
    """Download EVERYTHING the learned matcher will ever need, prove it
    works, and record it. After this, no run touches the network."""
    global _ALLOW_DOWNLOAD
    if not learned_available():
        print("The learned matcher is not installed.\n"
              "Run:  ./setup.sh --learned")
        return 1
    _ALLOW_DOWNLOAD = True
    d = _pin_torch_home()
    print(f"Downloading model files into {d} ...")
    try:
        _learned_models()
        # Force a REAL forward pass. Constructing the models downloads the
        # checkpoints, but only running them proves nothing else is fetched
        # lazily at inference. Any hidden download happens here, at setup,
        # where it can fail loudly, instead of mid-job with no internet.
        gA, gB = _selftest_pair()
        pts = _match_learned(gA, gB, profile("reshot"))
        if pts is None or len(pts[0]) < 10:
            print("The model files downloaded but the matcher produced no "
                  "matches on its self-test. Something is wrong; the "
                  "learned matcher will stay disabled.")
            return 1
        n_match = len(pts[0])
    except Exception as e:
        print(f"Could not prepare the learned matcher: {e}")
        return 1
    finally:
        _ALLOW_DOWNLOAD = False

    files, total = [], 0
    for p in sorted(_ckpt_dir().glob("*")):
        if p.is_file():
            b = p.read_bytes()
            files.append({"name": p.name, "size": len(b),
                          "sha256": hashlib.sha256(b).hexdigest()})
            total += len(b)
    if not files:
        print("No model files were written. The learned matcher stays off.")
        return 1
    LEARNED_MANIFEST.write_text(json.dumps(
        {"tool_version": VERSION, "matcher": "DISK+LightGlue",
         "verified": True, "self_test_matches": n_match,
         "files": files}, indent=2))
    for f in files:
        print(f"  {f['name']}  {f['size']/1e6:.1f} MB")
    print(f"\nVerified: {n_match} matches on the self-test pair.")
    print(f"{len(files)} file(s), {total/1e6:.1f} MB in {_ckpt_dir()}")
    print("The learned matcher is now fully offline. It will never "
          "download anything again.")
    return 0


def cmd_align(args):
    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    job = Job(uuid.uuid4().hex[:16], out, getattr(args, "mode", "reshot"))
    job.dir = out                       # headless: write straight to --out
    run_alignment(job, args.before, args.after)
    if job.state == "failed":
        print(f"FAILED: {job.error}", file=sys.stderr)
        return 2
    export_images(job)
    if args.video:
        export_video(job, aspect=args.aspect, style=args.style,
                     seconds=args.seconds)
    (out / "metrics.json").write_text(json.dumps(job.status(), indent=2))
    print(json.dumps(job.metrics, indent=2))
    print(f"Wrote: {', '.join(p.name for p in job.exports.values())} "
          f"+ metrics.json in {out}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="reveal.py", description=__doc__)
    sub = ap.add_subparsers(dest="cmd")
    ps = sub.add_parser("serve", help="run the local web app (default)")
    ps.add_argument("--port", type=int, default=DEFAULT_PORT)
    ps.add_argument("--no-browser", action="store_true")
    ps.add_argument("--workdir", default=None)
    pa = sub.add_parser("align", help="headless: align two files")
    pa.add_argument("before")
    pa.add_argument("after")
    pa.add_argument("--out", required=True)
    pa.add_argument("--mode", default="reshot", choices=list(MODES))
    pa.add_argument("--video", action="store_true")
    pa.add_argument("--aspect", default="4:5", choices=list(ASPECTS))
    pa.add_argument("--style", default="wipe", choices=["wipe", "fade"])
    pa.add_argument("--seconds", type=float, default=4.6)
    sub.add_parser("check", help="environment self-test")
    sub.add_parser("warmup", help="download the optional learned-matcher "
                                  "weights (once; then fully offline)")
    args = ap.parse_args(argv)
    if args.cmd == "warmup":
        return cmd_warmup()
    if args.cmd == "check":
        return cmd_check()
    if args.cmd == "align":
        return cmd_align(args)
    port = getattr(args, "port", DEFAULT_PORT)
    serve(port=port, open_browser=not getattr(args, "no_browser", False),
          workdir=getattr(args, "workdir", None))
    return 0


if __name__ == "__main__":
    sys.exit(main())
