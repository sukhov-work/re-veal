#!/usr/bin/env python3
"""Looped short clips from a photo sequence (2–6 developed stills of the same scene, handheld).

Research script (2026-10-30; the Halloween sequences). Neither tool changes: transitions.py is imported for
its decode, its canvas cover, its morph (prepare + iter_frames) and nothing else; rife_probe.py is imported for
the RIFE v4.26 in-betweens (weights behind RIFE_MANIFEST.json, offline, refuse-to-download) when a plan asks
for them. Everything written goes under benchmarks/runs/<date>/halloween/ (gitignored); the sources are read
only.

Subcommands
  prep SEQ_DIR --out OUT [--long 1920]
      Reads the developed JPGs of SEQ_DIR (sorted by name = capture order; ARW and XMP ignored), decodes them
      as the tool does (EXIF orientation, ICC to sRGB), scales each to the long edge, and registers every
      frame onto frame 0 by a background homography: SIFT + MAGSAC on a 1200 px proxy, accepted when the
      inliers are >= 40 and the map is sane (scale 0.5–2.0, corner moves below 0.6 of the size: a photographer may step closer); otherwise an
      ECC affine on blurred 600 px proxies (the motion-blurred frames); otherwise identity, said on the log.
      Frame 0 is never warped. All frames are cropped to the common valid rectangle (even sides). Writes
      OUT/k<i>.png and OUT/prep.json (the method, inliers, residual, the map and the crop per frame).
      `--windows "name:x0,y0,x1,y1;..."` (2026-11-05, for the studio; frame-0 px before the crop) measures and never
      applies: per registered frame i >= 1 and window, where the window's content sits (dx, dy px, sub-pixel by template
      match, and the correlation) under every fit the prep made for the frame: `all` (every keypoint), `far` (with
      --bg-depth), `chain`, `ecc`, and `final` (frame i as the prep writes it, after --lock-window, read on the canvas
      before the crop). Written to prep.json (`frames[i].windows`, and the boxes as `windows`) and drawn on
      OUT/windows.jpg; without it prep.json is unchanged.
  render PLAN.json --out OUT [--fps 25] [--draft 0] [--progress] [--frames]
      Renders the loop the plan describes (see plans/loops/SCHEMA.md): keyframes by index into the prep
      folder, holds per visit, a `through` chain of stills under one global speed profile (the inner stills
      passed, never held; `weights` per segment, `soft` slows near a still), segments rendered by `morph` (transitions.py, the DIS flow
      and optional anchors), `rife` (in-betweens inside the change matte; generated content, labelled),
      `dissolve` (a plain blend inside the change matte; for content that exists in one frame only),
      `teleport` (a region's content squeezed out and another region's squeezed in; `mode: fade` fades the
      region's content in place instead, for a ghost that materializes while the rest moves by RIFE), or `rewind` (the
      frames of an earlier segment played backward, every k-th), or `slices` (2026-11-01: diagonal cells that slide
      the next still into place as cards, a lattice or chevrons, a wave through several stills, temporal motion blur;
      nothing generated). Post effects: `breath` (a push-in about a
      point, sin² over the loop, the endpoints untouched). Writes OUT/loop.mp4, OUT/loop.gif (two-pass
      palette, 40 ms per frame at 25 fps), OUT/sheet.jpg, OUT/frames.json (what each frame is) and
      OUT/measure.json (the step series, the seam step, faces per frame, the double-exposure share per
      generated frame, seconds, the md5 of this script as run, and the RIFE manifest's model string when the
      render loaded RIFE, else null). `--progress` (2026-11-04, for the studio) prints `PROGRESS i n phase` lines
      on stderr: `frames` (i of the planned total), `effects`, `encode`, `measure`; without it stderr is
      unchanged. `--frames` also writes OUT/frames/f0000.jpg, f0001.jpg, ... (JPEG quality 90): the decoded
      mp4's frames, the ones the measures read.
  readers PREP_DIR [--out DIR]
      What each still of a prep folder holds, read before a plan is written (2026-11-04): per k<i>.png its size,
      the YuNet face boxes, the depth model's map (the prep folder's depth_k<i>.npy; computed and saved there
      only when missing, as prep saves it), its min, max and mean, the grey mean, the counts of grey pixels
      above 250 and below 5, and the variance of the grey still's Laplacian; per neighbouring pair the shares
      of pixels whose Lab distance on 2 px blurred copies (the change matte's measure) is above 14 and above 30.
      Writes DIR/readers.json and DIR/depth_k<i>.jpg (the map stretched min..max); DIR defaults to
      PREP_DIR/readers.
  probe PREP_DIR --out DIR [--long 960] [--pairs i,j;...]
      The in-between methods side by side before a plan is written (2026-11-05): per adjacent pair of registered stills
      (or the listed pairs), scaled to the long edge, the in-betweens at t 0.25, 0.5 and 0.75 by RIFE over the whole frame
      (behind its manifest, offline; without the manifest the RIFE strip is skipped with a log line), the DIS morph
      (transitions.py's, the morph preset's own ease) and the plain dissolve. Writes DIR/probe_<i>_<j>_<method>.jpg (three
      tiles with their t), DIR/crops/ (1:1 crops at the YuNet face boxes) and DIR/probe.json (per frame the double-exposure
      share inside the change matte and over the whole frame, and the mean absolute step to each still).
  measure MP4 --out DIR [--frames-json PATH] [--window "name:x0,y0,x1,y1;..."] [--ref 0] [--margin 30]
      The measures of `render` on any mp4, without rendering (2026-11-05; `render` calls the same code): the step series,
      its mean, max and argmax, the seam step, YuNet faces per frame; with the render's frames.json also the faces on the
      stills' frames, the generated share and the largest double-exposure share; with --window each window's offset
      against frame --ref in every frame (an object's stability, dx, dy px and the correlation). Writes DIR/measure.json.
  page --root ROOT --out HTML [--order seq,...] [--notes JSON] [--title ...] [--intro ...] [--footer ...] [--variants a,b]
      The review page: per sequence the keyframes strip (written to ROOT/in/<seq>/keys.jpg), and per full render (a
      folder of ROOT/<seq>/ holding measure.json, in name order) the mp4, the gif, the numbers and the note. `--variants`
      (2026-11-05) lists only the named renders, in that order; a name that is not a full render is a FAILED exit 2.
"""
import argparse
import datetime
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts/research"))
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

PROXY_LONG = 1200
ECC_LONG = 600
MIN_INLIERS = 40
ECC_MIN_CC = 0.45
FACE_MODEL = ROOT / "benchmarks/runs/2026-10-18/face/face_detection_yunet_2023mar.onnx"


def log(msg):
    print(f"INFO {msg}", file=sys.stderr, flush=True)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def fail(msg):
    """A refusal of a malformed or missing input (2026-11-05): `FAILED: msg` on stderr and exit 2, the convention of
    reveal.py that the studio's runner reads."""
    print(f"FAILED: {msg}", file=sys.stderr, flush=True)
    sys.exit(2)


# `render --progress` (2026-11-04, for the studio): PROGRESS lines on stderr. The switch is off unless cmd_render sets
# it, so a render without the flag writes the same stderr as before. `i` counts the timeline's frames produced so far,
# `n` is the planned total (an estimate: the holds plus every step's `n`).
_PROG = {"on": False, "i": 0, "n": 0}


def progress(i, n, phase):
    """`PROGRESS i n phase` on stderr, flushed, when the switch is on; nothing otherwise."""
    if _PROG["on"]:
        print(f"PROGRESS {int(i)} {int(n)} {phase}", file=sys.stderr, flush=True)


def tick(k, every=1):
    """Frame k (1-based) of a timeline step is done: the frame counter moves on by one, and every `every`-th frame of
    the step prints a `frames` line."""
    _PROG["i"] += 1
    if k % every == 0:
        progress(_PROG["i"], _PROG["n"], "frames")


def replan(old, new):
    """A step whose frame count is known only when it runs (`slices`, `rewind`): the planned total trades the plan's
    `n` for the real count."""
    _PROG["n"] += int(new) - int(old)


# ------------------------------------------------------------------ prep: decode, scale, register, crop

def _scale_to(im, long):
    h, w = im.shape[:2]
    s = long / max(h, w)
    if s >= 1:
        return im
    return cv2.resize(im, (int(round(w * s)), int(round(h * s))), interpolation=cv2.INTER_AREA)


def _proxy_gray(bgr, long):
    p = _scale_to(bgr, long)
    return cv2.cvtColor(p, cv2.COLOR_BGR2GRAY), p.shape[1] / bgr.shape[1]


def _sane_h(H, w, h):
    """A background map of a handheld camera: near a similarity; the photographer may step closer."""
    if H is None or not np.all(np.isfinite(H)):
        return False, "none"
    sc = math.sqrt(abs(np.linalg.det(H[:2, :2])))
    if not 0.5 <= sc <= 2.0:
        return False, f"scale {sc:.3f}"
    c = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
    d = cv2.perspectiveTransform(c, H).reshape(-1, 2) - c.reshape(-1, 2)
    mv = float(np.hypot(d[:, 0], d[:, 1]).max())
    if mv > 0.6 * max(w, h):
        return False, f"corner move {mv:.0f} px"
    return True, f"scale {sc:.3f} corner max {mv:.1f} px"


def _scale_of(H):
    return math.sqrt(abs(np.linalg.det(np.asarray(H)[:2, :2])))


def register_sift(ref_bgr, bgr, mask_ref=None, mask=None):
    """Homography bgr -> ref on the proxies, returned at full scale, with its diagnostics. A mask (full-scale
    uint8, nonzero where keypoints may lie: the far field under `prep --bg-depth`) restricts the fit."""
    g0, s = _proxy_gray(ref_bgr, PROXY_LONG)
    g1, s1 = _proxy_gray(bgr, PROXY_LONG)
    sift = cv2.SIFT_create(6000)
    m0 = None if mask_ref is None else cv2.resize(mask_ref, (g0.shape[1], g0.shape[0]), interpolation=cv2.INTER_NEAREST)
    m1 = None if mask is None else cv2.resize(mask, (g1.shape[1], g1.shape[0]), interpolation=cv2.INTER_NEAREST)
    k0, d0 = sift.detectAndCompute(g0, m0)
    k1, d1 = sift.detectAndCompute(g1, m1)
    if d0 is None or d1 is None or len(k0) < 8 or len(k1) < 8:
        return None, {"method": "sift", "inliers": 0, "why": "too few keypoints"}
    m = cv2.BFMatcher().knnMatch(d1, d0, k=2)
    good = [a for a, b in m if a.distance < 0.75 * b.distance]
    if len(good) < 8:
        return None, {"method": "sift", "inliers": 0, "why": f"{len(good)} matches"}
    p1 = np.float32([k1[x.queryIdx].pt for x in good])
    p0 = np.float32([k0[x.trainIdx].pt for x in good])
    H, mask = cv2.findHomography(p1, p0, cv2.USAC_MAGSAC, 2.5, maxIters=5000, confidence=0.999)
    if H is None:
        return None, {"method": "sift", "inliers": 0, "why": "no model"}
    inl = int(mask.sum())
    ok, why = _sane_h(H, g0.shape[1], g0.shape[0])
    sel = mask.ravel() > 0
    proj = cv2.perspectiveTransform(p1[sel].reshape(-1, 1, 2), H).reshape(-1, 2)
    res = float(np.median(np.hypot(*(proj - p0[sel]).T))) / s if inl else None
    S0 = np.diag([1 / s, 1 / s, 1.0]); S1 = np.diag([1 / s1, 1 / s1, 1.0])
    Hf = S0 @ H @ np.linalg.inv(S1)
    info = {"method": "sift+magsac" + ("" if mask_ref is None else " (masked)"), "inliers": inl, "matches": len(good), "sane": ok, "why": why,
            "residual_px": None if res is None else round(res, 2), "_pts_ref": (p0[sel] / s).tolist()}
    if inl < MIN_INLIERS or not ok:
        return None, info
    return Hf, info


def register_ecc(ref_bgr, bgr, seed=None, mask=None, long=ECC_LONG, blur=3.0):
    """ECC affine on blurred proxies, seeded by a map bgr -> ref at full scale (the previous frame's):
    the path for a motion-blurred frame. `mask` (full-scale uint8 of bgr, the INPUT image) restricts the fit to those pixels."""
    g0, s = _proxy_gray(ref_bgr, long)
    g1, s1 = _proxy_gray(bgr, long)
    m1 = None if mask is None else cv2.resize(mask, (g1.shape[1], g1.shape[0]), interpolation=cv2.INTER_NEAREST)
    g0 = cv2.GaussianBlur(g0, (0, 0), blur).astype(np.float32) / 255
    g1 = cv2.GaussianBlur(g1, (0, 0), blur).astype(np.float32) / 255
    S0 = np.diag([1 / s, 1 / s, 1.0]); S1 = np.diag([1 / s1, 1 / s1, 1.0])
    Hs = np.eye(3) if seed is None else np.linalg.inv(S0) @ seed @ S1     # bgr -> ref on the proxies
    # findTransformECC maps the TEMPLATE (ref) to the INPUT (bgr): seed it with the inverse and invert back
    M = np.linalg.inv(Hs)[:2].astype(np.float32)
    try:
        cc, M = cv2.findTransformECC(g0, g1, M, cv2.MOTION_AFFINE,
                                     (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-6), m1, 5)
    except cv2.error as e:
        return None, {"method": "ecc-affine", "cc": None, "why": str(e).splitlines()[-1][:80]}
    H = np.linalg.inv(np.vstack([M, [0, 0, 1]]).astype(np.float64))
    ok, why = _sane_h(H, g0.shape[1], g0.shape[0])
    info = {"method": "ecc-affine" + ("" if mask is None else " (masked)"), "cc": round(float(cc), 4), "sane": ok, "why": why, "seeded": seed is not None}
    if cc < ECC_MIN_CC or not ok:
        return None, info
    return S0 @ H @ np.linalg.inv(S1), info


def _window_shift(a, b, box, margin=30):
    """Where the window `box` (x0, y0, x1, y1 px of a) sits in b: a template match of a's window inside b's box grown
    by `margin`, sub-pixel by a parabola on the peak. Returns (dx, dy, peak correlation)."""
    x0, y0, x1, y1 = box
    t = cv2.cvtColor(a[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
    ox, oy = max(0, x0 - margin), max(0, y0 - margin)
    reg = cv2.cvtColor(b[oy:y1 + margin, ox:x1 + margin], cv2.COLOR_BGR2GRAY)
    r = cv2.matchTemplate(reg, t, cv2.TM_CCOEFF_NORMED)
    _, mx, _, (px, py) = cv2.minMaxLoc(r)
    def sub(ax):
        if ax == 0 and 0 < px < r.shape[1] - 1:
            l, c, rr = r[py, px - 1], r[py, px], r[py, px + 1]
        elif ax == 1 and 0 < py < r.shape[0] - 1:
            l, c, rr = r[py - 1, px], r[py, px], r[py + 1, px]
        else:
            return 0.0
        d = l - 2 * c + rr
        return 0.0 if abs(d) < 1e-9 else float(0.5 * (l - rr) / d)
    return px - (x0 - ox) + sub(0), py - (y0 - oy) + sub(1), float(mx)


# `prep --windows` and `measure --window` (2026-11-05, the studio): named windows, their offsets per fit, windows.jpg
WINDOW_FITS = ("all", "far", "chain", "ecc", "final")
WINDOW_COLOURS = {"all": (0, 165, 255), "far": (255, 128, 0), "chain": (255, 0, 255), "ecc": (0, 200, 0), "final": (0, 0, 255)}   # BGR
WINDOW_ARROW = 8                       # windows.jpg draws each offset 8 times its length


def parse_windows(s, flag):
    """'name:x0,y0,x1,y1;...' -> {name: [x0, y0, x1, y1]} (int px, each side 4 px or more); a malformed list is a FAILED
    exit that names the flag and the part."""
    wins = {}
    for part in s.split(";"):
        if not part.strip():
            continue
        name, sep, rest = part.partition(":")
        name = name.strip()
        try:
            box = [int(v) for v in rest.split(",")]
        except ValueError:
            box = []
        if not sep or not name or len(box) != 4 or box[2] - box[0] < 4 or box[3] - box[1] < 4:
            fail(f"{flag}: {part.strip()!r} is not name:x0,y0,x1,y1 with x1 >= x0 + 4 and y1 >= y0 + 4")
        if name in wins:
            fail(f"{flag}: the name {name!r} is given twice")
        wins[name] = box
    if not wins:
        fail(f"{flag}: no window in {s!r}")
    return wins


def check_boxes(wins, W, H, flag, what):
    """Every window inside the image it is read on (W x H px), else a FAILED exit naming the window."""
    for name, (x0, y0, x1, y1) in wins.items():
        if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
            fail(f"{flag}: the window {name} [{x0}, {y0}, {x1}, {y1}] leaves {what} ({W}x{H} px)")


def _label(img, text, org, scale=0.5, colour=(255, 255, 255)):
    """Text with a dark outline, readable on any still: the text drawn dark 1 px off in the eight directions, then in
    `colour`, all at one thickness (OpenCV's glyph advance grows with the thickness, so a thicker outline drifts)."""
    th = max(1, int(round(2 * scale)))
    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            if ox or oy:
                cv2.putText(img, text, (org[0] + ox, org[1] + oy), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), th, cv2.LINE_AA)
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, colour, th, cv2.LINE_AA)


def _shift_edge(a, b, box, margin=30):
    """`_window_shift` plus whether its peak lies on the border of the search (the window grown by `margin` px, cut by b's
    edges): there the content may sit beyond the search, and the offset is a bound, not a measurement."""
    dx, dy, c = _window_shift(a, b, box, margin)
    x0, y0, x1, y1 = box
    lo_x, hi_x = max(0, x0 - margin) - x0, min(x1 + margin, b.shape[1]) - x1
    lo_y, hi_y = max(0, y0 - margin) - y0, min(y1 + margin, b.shape[0]) - y1
    return dx, dy, c, bool(dx < lo_x + 0.5 or dx > hi_x - 0.5 or dy < lo_y + 0.5 or dy > hi_y - 0.5)


def _carry_box(box, Hr, W, H):
    """A window of frame 0 (px) carried onto the canvas by Hr (frame 0 -> the canvas frame): the bounding box of its
    corners, clipped to W x H; None when less than 4 px of a side remain."""
    x0, y0, x1, y1 = box
    c = cv2.perspectiveTransform(np.float32([[x0, y0], [x1, y0], [x1, y1], [x0, y1]]).reshape(-1, 1, 2), Hr).reshape(-1, 2)
    b = [max(0, int(round(float(c[:, 0].min())))), max(0, int(round(float(c[:, 1].min())))),
         min(W, int(round(float(c[:, 0].max())))), min(H, int(round(float(c[:, 1].max()))))]
    return b if b[2] - b[0] >= 4 and b[3] - b[1] >= 4 else None


def window_offsets(frames, warped, regs, fits, wins, masks, Hr, crop, out):
    """`prep --windows`: per registered frame i >= 1 and named window (frame-0 px), where frame 0's window content sits in
    frame i (dx, dy px, sub-pixel by `_window_shift`, a ±30 px search), the peak correlation, and `edge` (the peak on the
    search's border: the offset is a bound), under every fit the prep produced for the frame. `all`, `far`, `chain`,
    `ecc`: frame i warped onto frame 0 by that fit (cubic), as the lock measures; the all-keypoint fit is computed for
    this when the prep's own fit is the far field's. `final`: frame i as the prep warps it onto the canvas (after
    `--lock-window`, with the written stills' resampling) against frame 0 on the canvas, before the crop, the window
    carried onto the canvas; `box_canvas` is that window in the written stills' px (less the crop's origin). A fit that
    produced no map has no entry. Writes regs[i]["windows"] and out/windows.jpg."""
    H0, W0 = frames[0].shape[:2]
    Hc, Wc = warped[0].shape[:2]
    fboxes = {name: _carry_box(box, Hr, Wc, Hc) for name, box in wins.items()}
    cboxes = {}
    for name, b in fboxes.items():
        cb = None if b is None else [max(0, b[0] - crop[0]), max(0, b[1] - crop[1]), min(crop[2], b[2]) - crop[0], min(crop[3], b[3]) - crop[1]]
        cboxes[name] = cb if cb is not None and cb[2] - cb[0] >= 4 and cb[3] - cb[1] >= 4 else None
    drawn = {}
    for i in range(1, len(frames)):
        if regs[i]["method"].startswith("cut"):
            continue
        maps_i = dict(fits.get(i, {}))
        if "all" not in maps_i:
            if masks is not None:
                Ha, ia = register_sift(frames[0], frames[i])
                if Ha is not None:
                    maps_i = {"all": Ha, **maps_i}
                else:
                    log(f"prep: frame {i} windows: the all-keypoint fit was rejected ({ia.get('inliers')} inliers, {ia.get('why')}); no `all` offsets")
            else:
                log(f"prep: frame {i} windows: the all-keypoint fit was rejected (the frame's `direct` entry); no `all` offsets")
        res = {name: {"box": list(box), "box_canvas": cboxes[name], "fits": {}} for name, box in wins.items()}
        for fit in WINDOW_FITS[:-1]:
            if fit not in maps_i:
                continue
            wf = cv2.warpPerspective(frames[i], maps_i[fit], (W0, H0), flags=cv2.INTER_CUBIC)
            for name, box in wins.items():
                dx, dy, c, e = _shift_edge(frames[0], wf, box)
                res[name]["fits"][fit] = {"dx": round(dx, 2), "dy": round(dy, 2), "corr": round(c, 3), "edge": e}
        for name in wins:
            if fboxes[name] is not None:
                dx, dy, c, e = _shift_edge(warped[0], warped[i], fboxes[name])
                res[name]["fits"]["final"] = {"dx": round(dx, 2), "dy": round(dy, 2), "corr": round(c, 3), "edge": e}
            log(f"prep: frame {i} window {name}: " + "; ".join(f"{fit} ({o['dx']:+.2f}, {o['dy']:+.2f}) corr {o['corr']:.3f}"
                                                              + (" AT THE SEARCH EDGE" if o["edge"] else "") for fit, o in res[name]["fits"].items()))
        regs[i]["windows"] = res
        drawn[i] = res
    draw_windows(frames[0], wins, drawn, out / "windows.jpg")


def draw_windows(img0, wins, per_frame, path, long=960):
    """windows.jpg: per frame i >= 1 a panel of frame 0 (scaled to `long` px) with the windows and their names, and per
    fit an arrow from the window's centre along its offset, WINDOW_ARROW times its length, in the fit's colour."""
    s = min(1.0, long / max(img0.shape[:2]))
    base = cv2.resize(img0, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else img0.copy()
    panels = []
    for i, res in per_frame.items():
        p = base.copy()
        for name, box in wins.items():
            bx0, by0, bx1, by1 = [int(round(v * s)) for v in box]
            cv2.rectangle(p, (bx0, by0), (bx1, by1), (255, 255, 255), 1, cv2.LINE_AA)
            _label(p, name, (bx0 + 2, max(14, by0 - 5)), 0.45)
            cx, cy = (bx0 + bx1) / 2.0, (by0 + by1) / 2.0
            for fit, o in res[name]["fits"].items():
                tip = (int(round(cx + WINDOW_ARROW * s * o["dx"])), int(round(cy + WINDOW_ARROW * s * o["dy"])))
                cv2.arrowedLine(p, (int(round(cx)), int(round(cy))), tip, WINDOW_COLOURS[fit], 2, cv2.LINE_AA, tipLength=0.25)
        _label(p, f"frame {i} on frame 0: offsets x{WINDOW_ARROW}", (8, 20), 0.55)
        for k, fit in enumerate(f for f in WINDOW_FITS if any(f in r["fits"] for r in res.values())):
            _label(p, fit, (8, 42 + 20 * k), 0.55, WINDOW_COLOURS[fit])
        panels.append(p)
    if panels:
        gap = np.full((base.shape[0], 6, 3), 24, np.uint8)
        cv2.imwrite(str(path), np.hstack([x for q in panels for x in (q, gap)][:-1]), [cv2.IMWRITE_JPEG_QUALITY, 88])


def register_all(frames, cuts=(), masks=None, ecc_refine=False, fits=None):
    """Maps frame i -> frame 0 for every frame: direct SIFT, else SIFT to the previous frame composed with
    its map, else ECC seeded by the previous frame's map, else identity (said on the log). A frame listed
    in cuts is not registered at all (identity, untrusted): the plan joins it by a cut. `fits` (a dict, given by
    `prep --windows` only) collects per frame index every map a fit produced: `all` (the direct SIFT fit without
    masks) or `far` (with them), `chain`, `ecc` (the fallback or the masked refinement)."""
    ref = frames[0]
    mk = (lambda i: None) if masks is None else (lambda i: masks[i])
    maps = [np.eye(3)]; regs = [{"method": "reference", "trusted": True}]
    for i, f in enumerate(frames[1:], 1):
        if i in cuts:
            maps.append(np.eye(3)); regs.append({"method": "cut (identity, excluded from the crop)", "trusted": False})
            log(f"prep: frame {i} is a cut: identity, excluded from the crop")
            continue
        H, info = register_sift(ref, f, mk(0), mk(i))
        if fits is not None and H is not None:
            fits.setdefault(i, {})["all" if masks is None else "far"] = H
        if H is None:
            log(f"prep: frame {i} direct sift rejected ({info.get('inliers')} inliers, {info.get('why')}); chaining")
            Hc, infoc = register_sift(frames[i - 1], f, mk(i - 1), mk(i))
            if Hc is not None and regs[i - 1]["trusted"]:
                H = maps[i - 1] @ Hc
                info = {"method": "sift+magsac via frame %d" % (i - 1), "direct": info, **{k: v for k, v in infoc.items() if k != "method"}}
                if fits is not None:
                    fits.setdefault(i, {})["chain"] = H
            else:
                log(f"prep: frame {i} chained sift rejected ({infoc.get('inliers')} inliers, {infoc.get('why')}); trying ECC")
                seed = maps[i - 1] if regs[i - 1]["trusted"] else None
                He, infoe = register_ecc(ref, f, seed=seed)
                info = {"direct": info, "chain": infoc, **infoe}
                H = He
                if fits is not None and He is not None:
                    fits.setdefault(i, {})["ecc"] = He
        if H is None:
            log(f"prep: frame {i} ECC rejected ({info.get('why')}, cc {info.get('cc')}); IDENTITY used")
            H = np.eye(3); info["method"] = "identity"; info["trusted"] = False
        else:
            info["trusted"] = True
            if ecc_refine and masks is not None and info["method"].startswith("sift"):
                He, infoe = register_ecc(ref, f, seed=H, mask=mk(i), long=PROXY_LONG, blur=2.0)
                if He is not None:
                    H = He; info["method"] += " + ecc (masked)"; info["ecc_cc"] = infoe["cc"]
                    if fits is not None:
                        fits.setdefault(i, {})["ecc"] = He
                else:
                    log(f"prep: frame {i} masked ECC refinement rejected ({infoe.get('why')}, cc {infoe.get('cc')}); the SIFT fit kept")
        maps.append(H); regs.append(info)
        log(f"prep: frame {i} {info['method']} inliers {info.get('inliers', '-')} {info.get('why', '')}")
    return maps, regs


def cmd_prep(args):
    import transitions as T
    src = Path(args.seq_dir)
    files = sorted(p for p in src.iterdir() if p.suffix.lower() in (".jpg", ".jpeg"))
    if len(files) < 2:
        sys.exit(f"{src}: {len(files)} developed JPGs, need 2 or more")
    named = parse_windows(args.windows, "prep --windows") if args.windows else None    # the named windows of --windows
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    frames, meta = [], []
    for p in files:
        rgb = T.load_image_rgb(p)
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        frames.append(_scale_to(bgr, args.long))
        meta.append({"source": str(p), "bytes": p.stat().st_size, "sha256": sha256(p),
                     "native": [rgb.shape[1], rgb.shape[0]], "scaled": [frames[-1].shape[1], frames[-1].shape[0]]})
        log(f"prep: {p.name} {rgb.shape[1]}x{rgb.shape[0]} -> {frames[-1].shape[1]}x{frames[-1].shape[0]}")
    cuts = tuple(int(c) for c in args.cut.split(",") if c != "")
    if named:
        check_boxes(named, frames[0].shape[1], frames[0].shape[0], "prep --windows", "frame 0")
    depths, masks = None, None
    if args.bg_depth > 0:
        # the far field by the depth model (offline): keypoints only where the relative depth is below the gate
        depths = [T.model_disparity(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) for f in frames]
        masks = [((D < args.bg_depth) * 255).astype(np.uint8) for D in depths]
        log(f"prep: bg-depth {args.bg_depth}: far-field shares " + ", ".join(f"{(m > 0).mean():.2f}" for m in masks))
    global MIN_INLIERS
    MIN_INLIERS = args.min_inliers
    fits = {} if named else None
    maps, regs = register_all(frames, cuts, masks, ecc_refine=args.ecc_refine, fits=fits)
    if args.lock_window:
        # the gag object stays put: each frame's map gains the translation that zeroes the mean offset of the listed
        # windows (reference-frame px) between the reference and the warped frame, measured by template match (sub-pixel)
        wins = [tuple(int(v) for v in w.split(",")) for w in args.lock_window.split(";")]
        for i in range(1, len(frames)):
            if not regs[i]["trusted"]:
                continue
            wf = cv2.warpPerspective(frames[i], maps[i], (frames[0].shape[1], frames[0].shape[0]), flags=cv2.INTER_CUBIC)
            offs = [_window_shift(frames[0], wf, w) for w in wins]
            dx = float(np.mean([o[0] for o in offs])); dy = float(np.mean([o[1] for o in offs]))
            maps[i] = np.array([[1, 0, -dx], [0, 1, -dy], [0, 0, 1.0]]) @ maps[i]
            regs[i]["lock"] = {"windows": wins, "offsets_px": [[round(o[0], 2), round(o[1], 2)] for o in offs], "shift_px": [round(-dx, 2), round(-dy, 2)],
                               "corr": [round(o[2], 3) for o in offs]}
            regs[i]["method"] += " + lock"
            log(f"prep: frame {i} lock: the windows sat at " + ", ".join(f"({o[0]:+.1f}, {o[1]:+.1f})" for o in offs) + f" px; shifted by ({-dx:+.2f}, {-dy:+.2f})")
    near = None
    if args.depth_blend:
        # a second fit on every keypoint (the subject plane); the warp blends the two by the reference frame's depth
        assert depths is not None, "--depth-blend needs --bg-depth"
        near = [(np.eye(3), {"method": "reference"})] + [register_sift(frames[0], f) for f in frames[1:]]
    # the canvas: the trusted frame with the closest framing (the largest background scale), so no frame is upscaled
    scales = [_scale_of(H) if r["trusted"] else 0.0 for H, r in zip(maps, regs)]
    ref_i = int(np.argmax(scales)) if args.ref < 0 else args.ref
    Hr = np.linalg.inv(maps[ref_i])
    H0, W0 = frames[ref_i].shape[:2]
    warped, valids = [], []
    for i, f in enumerate(frames):
        H = Hr @ maps[i]                      # frame i -> the reference canvas
        regs[i]["scale_to_canvas"] = round(_scale_of(H), 4)
        if i == ref_i:
            warped.append(f); valids.append(np.ones((H0, W0), np.uint8)); continue
        sc = _scale_of(H)
        if sc < 0.98:                          # downscale first (INTER_AREA), then the near-unit warp
            f2 = cv2.resize(f, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
            H = H @ np.diag([1 / sc, 1 / sc, 1.0])
        else:
            f2 = f
        ones = np.ones(f2.shape[:2], np.uint8) * 255
        Hn = None if near is None or near[i][0] is None or not regs[i]["trusted"] else Hr @ near[i][0]
        if Hn is not None and i != ref_i:
            # the depth-blended warp: far pixels follow the far-field fit, near pixels the subject-plane fit, linear in the
            # reference frame's relative depth between the two fits' median inlier depths (parallax is linear in disparity)
            Hn = Hn @ np.diag([1 / sc, 1 / sc, 1.0]) if sc < 0.98 else Hn
            Dr = depths[ref_i]
            # the fits' inlier points lie in frame 0; the canvas is frame ref_i: map them by Hr (a chained fit's points lie elsewhere: no blend)
            to_canvas = lambda pts: (cv2.perspectiveTransform(np.float32(pts).reshape(-1, 1, 2), Hr).reshape(-1, 2) if len(pts) else np.zeros((0, 2), np.float32))
            direct = regs[i]["method"].startswith("sift+magsac") and "via" not in regs[i]["method"]
            pf = np.int32(np.round(to_canvas(regs[i].get("_pts_ref", [])))) if direct else np.zeros((0, 2), np.int32)
            pn = np.int32(np.round(to_canvas(near[i][1].get("_pts_ref", []))))
            def med_depth(pts):
                pts = pts[(pts[:, 0] >= 0) & (pts[:, 0] < Dr.shape[1]) & (pts[:, 1] >= 0) & (pts[:, 1] < Dr.shape[0])]
                return float(np.median(Dr[pts[:, 1], pts[:, 0]])) if len(pts) else float("nan")
            d_far, d_near = med_depth(pf), med_depth(pn)
            if args.depth_blend != "auto":
                d_far, d_near = (float(v) for v in args.depth_blend.split(","))
            if not (d_near > d_far + 0.05):
                log(f"prep: frame {i} depth-blend: the fits' depths do not separate (far {d_far:.3f}, near {d_near:.3f}); far fit only")
                Hn = None
            else:
                w = np.clip((Dr - d_far) / (d_near - d_far), 0, 1).astype(np.float32)
                w = cv2.GaussianBlur(w, (0, 0), 3)
                ys, xs = np.mgrid[0:H0, 0:W0].astype(np.float32)
                grid = np.stack([xs, ys], -1).reshape(-1, 1, 2)
                sf = cv2.perspectiveTransform(grid, np.linalg.inv(H)).reshape(H0, W0, 2)
                sn = cv2.perspectiveTransform(grid, np.linalg.inv(Hn)).reshape(H0, W0, 2)
                src_xy = (1 - w[..., None]) * sf + w[..., None] * sn
                mx, my = np.ascontiguousarray(src_xy[..., 0]), np.ascontiguousarray(src_xy[..., 1])
                warped.append(cv2.remap(f2, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT))
                valids.append((cv2.remap(ones, mx, my, cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT) > 0).astype(np.uint8))
                sep = float(np.percentile(np.hypot(*(sf - sn).reshape(-1, 2).T), 95))
                regs[i]["depth_blend"] = {"d_far": round(d_far, 3), "d_near": round(d_near, 3), "near_fit": {k: v for k, v in near[i][1].items() if not k.startswith("_")},
                                          "fit_separation_p95_px": round(sep, 1)}
                regs[i]["H_to_canvas"] = np.round(H, 6).tolist(); regs[i]["H_near_to_canvas"] = np.round(Hn, 6).tolist()
                log(f"prep: frame {i} depth-blend: far fit (depth {d_far:.3f}) to near fit (depth {d_near:.3f}, {near[i][1].get('inliers')} inliers); the fits differ by up to {sep:.0f} px (p95)")
                continue
        warped.append(cv2.warpPerspective(f2, H, (W0, H0), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT))
        valids.append((cv2.warpPerspective(ones, H, (W0, H0), flags=cv2.INTER_NEAREST) > 0).astype(np.uint8))
        regs[i]["H_to_canvas"] = np.round(H, 6).tolist()
    # the common valid rectangle: shrink the full canvas from the worst edge until every pixel is valid
    v = np.min(np.stack([vv for vv, r in zip(valids, regs) if r["trusted"]]), 0) > 0
    y0, y1, x0, x1 = 0, H0, 0, W0
    while not v[y0:y1, x0:x1].all():
        r = v[y0:y1, x0:x1].mean(1); c = v[y0:y1, x0:x1].mean(0)
        if min(r[0], r[-1]) <= min(c[0], c[-1]):
            y0, y1 = (y0 + 1, y1) if r[0] <= r[-1] else (y0, y1 - 1)
        else:
            x0, x1 = (x0 + 1, x1) if c[0] <= c[-1] else (x0, x1 - 1)
    if (x1 - x0) % 2: x1 -= 1
    if (y1 - y0) % 2: y1 -= 1
    crop = [x0, y0, x1, y1]
    log(f"prep: canvas = frame {ref_i}; common crop {crop} of {W0}x{H0} -> {x1 - x0}x{y1 - y0}")
    if named:
        window_offsets(frames, warped, regs, fits, named, masks, Hr, crop, out)
    for i, wf in enumerate(warped):
        cv2.imwrite(str(out / f"k{i}.png"), wf[y0:y1, x0:x1])
        if depths is not None or args.depth_maps:   # the registered still's own map, for the depth effects of a plan
            np.save(str(out / f"depth_k{i}.npy"), T.model_disparity(cv2.cvtColor(wf[y0:y1, x0:x1], cv2.COLOR_BGR2RGB)))
    for r in regs:
        r.pop("_pts_ref", None)
    rep = {"date": datetime.datetime.now().isoformat(timespec="seconds"), "seq": src.parent.name if src.name == "raw" else src.name,
           "sources": meta, "long": args.long, "cuts": list(cuts), "bg_depth": args.bg_depth, "depth_blend": args.depth_blend or False,
           "min_inliers": args.min_inliers, "ecc_refine": bool(args.ecc_refine), "ref_requested": args.ref, "lock_window": args.lock_window or "",
           "reference": ref_i, "reference_size": [W0, H0], "crop": crop,
           "canvas": [x1 - x0, y1 - y0], "frames": regs}
    if named:                                  # only with --windows: without it prep.json keeps its keys and bytes
        rep["windows"] = named
    (out / "prep.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps({"seq": rep["seq"], "n": len(frames), "ref": ref_i, "canvas": rep["canvas"],
                      "methods": [r["method"] for r in regs],
                      "inliers": [r.get("inliers", r.get("cc")) for r in regs]}))


# ------------------------------------------------------------------ render: the plan's timeline

EASES = {
    "linear": lambda t: t,
    "smooth": lambda t: t * t * (3 - 2 * t),
    "snap": lambda t: (lambda u: u * u * (3 - 2 * u))(t * t * (3 - 2 * t)),
    "accel": lambda t: t * t,
    "accel3": lambda t: t * t * t,
    "decel": lambda t: 1 - (1 - t) ** 2,
    "sine": lambda t: 0.5 - 0.5 * math.cos(math.pi * t),
}


def knot_soft(t, a):
    """Slow the motion near a knot without stopping: t' = t - a sin(2πt) / 2π; the speed at the knot is 1 - a."""
    return t - a * math.sin(2 * math.pi * t) / (2 * math.pi)


def change_matte(A, B, thr=14.0, grow=0.015, feather=0.01, min_share=0.0005):
    """Where the two registered frames differ: a Lab distance above thr on 2 px blurred copies, opened and
    closed, specks dropped, grown by `grow` of the width, feathered by `feather` of the width (the core kept
    at 1). Returns the soft matte in [0, 1]."""
    la = cv2.cvtColor(cv2.GaussianBlur(A, (0, 0), 2), cv2.COLOR_BGR2LAB).astype(np.float32)
    lb = cv2.cvtColor(cv2.GaussianBlur(B, (0, 0), 2), cv2.COLOR_BGR2LAB).astype(np.float32)
    d = np.linalg.norm(la - lb, axis=2)
    W = A.shape[1]
    m = (d > thr).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    for k in range(1, n):
        if st[k, cv2.CC_STAT_AREA] >= min_share * m.size:
            keep[lab == k] = 1
    g = max(1, int(round(grow * W))) | 1
    core = cv2.dilate(keep, np.ones((g, g), np.uint8)).astype(np.float32)
    soft = cv2.GaussianBlur(core, (0, 0), max(1.0, feather * W))
    return np.maximum(soft, core * (soft > 0.5)).clip(0, 1)


def blend(A, B, t):
    return (1 - t) * A.astype(np.float32) + t * B.astype(np.float32)


class Rife:
    """RIFE v4.26 through rife_probe (weights behind the manifest; offline). Loaded on first use."""
    def __init__(self):
        self.net = None; self.info = None

    def at(self, A, B, t):
        if self.net is None:
            import rife_probe as R
            self.R = R
            self.net, self.info = R.load_rife()
            log(f"rife: loaded ({self.info['params']} params, {self.info['threads']} threads)")
        return self.R.rife_at(self.net, A, B, float(t))


_RIFE = Rife()


def _rife_version():
    """The RIFE manifest's `model` string when this render loaded RIFE, else None (measure.json's `rife_version`)."""
    if _RIFE.net is None:
        return None
    import rife_probe as R
    return json.loads(Path(R.MANIFEST).read_text())["model"]


def frames_rife(A, B, n, ease, matte_cfg, out_rows, step=None):
    """n in-betweens: RIFE inside the change matte, the plain blend outside. Generated content inside.
    `matte: {"all": true}` runs RIFE on the whole frame (a camera parallax between the stills is then motion too).
    Step keys: `margin` (t runs over [margin, 1 − margin], so no in-between hugs a still); `local`
    ([{"box": [x0, y0, x1, y1] (canvas fractions), "ease": "snap", "feather": 0.01}]: inside each box the in-between
    is RIFE at that box's own ease of u, blended over a feathered edge; a mouth that opens crosses its ambiguous half
    in fewer frames while the lean keeps the leg's ease)."""
    step = step or {}
    if matte_cfg.get("all"):
        m = np.ones(A.shape[:2], np.float32)
    else:
        m = change_matte(A, B, **{k: v for k, v in matte_cfg.items() if k != "all"})
    m3 = m[..., None]
    mg = float(step.get("margin", 0.0))
    H, W = A.shape[:2]
    locals_ = []
    for lc in step.get("local", []):
        x0, y0, x1, y1 = lc["box"]; bm = np.zeros((H, W), np.float32)
        bm[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)] = 1.0
        bm = cv2.GaussianBlur(bm, (0, 0), max(1.0, float(lc.get("feather", 0.01)) * W))
        locals_.append((bm[..., None], EASES[lc.get("ease", "snap")]))
    import rife_probe as R
    out = []
    for i in range(n):
        u = (i + 1) / (n + 1)
        t = mg + (1 - 2 * mg) * EASES[ease](u)
        t0 = time.perf_counter()
        X = _RIFE.at(A, B, t)
        for bm, le in locals_:
            tl = mg + (1 - 2 * mg) * le(u)
            Xl = _RIFE.at(A, B, tl)
            X = (bm * Xl.astype(np.float32) + (1 - bm) * X.astype(np.float32)).round().astype(np.uint8)
        sec = time.perf_counter() - t0
        bl = blend(A, B, t)
        f = (m3 * X + (1 - m3) * bl).round().astype(np.uint8)
        out.append(f)
        out_rows.append({"t": round(t, 4), "generated": "rife", "matte_share": round(float((m > 0.5).mean()), 4),
                         "dexp": R.dexp_share(X, A, B, m), "seconds": round(sec, 2)})
        tick(i + 1)
    return out, m


def frames_chain(keys, knots, n, weights, ease, soft, method, matte_cfg, out_rows, margin=0.0):
    """n frames along the chain of stills `knots` (the current still first) under ONE global speed profile:
    u = ease(j / (n + 1)) picks the segment by its weight and the local t; `soft` slows the motion near each
    inner still without stopping (speed 1 - soft there). The inner stills are passed through, never held."""
    K = len(knots) - 1
    w = np.array(weights if weights else [1.0] * K, np.float64); w = w / w.sum()
    b = np.concatenate([[0.0], np.cumsum(w)])
    mattes = {}
    import rife_probe as R
    out = []
    for j in range(1, n + 1):
        u = EASES[ease](j / (n + 1))
        i = min(K - 1, int(np.searchsorted(b, u, side="right") - 1))
        t = (u - b[i]) / (b[i + 1] - b[i])
        if soft:
            t = knot_soft(t, soft)
        if margin:                                   # never render within `margin` of a still (RIFE's frames there hug the still)
            t = margin + (1 - 2 * margin) * t
        A, B = keys[knots[i]], keys[knots[i + 1]]
        if i not in mattes:
            mattes[i] = change_matte(A, B, **matte_cfg)
        m = mattes[i]; m3 = m[..., None]
        if method == "dissolve":
            f = blend(A, B, t).round().astype(np.uint8); row = {"generated": "none (blend)"}
        else:
            t0 = time.perf_counter(); X = _RIFE.at(A, B, t); sec = time.perf_counter() - t0
            f = (m3 * X + (1 - m3) * blend(A, B, t)).round().astype(np.uint8)
            row = {"generated": "rife", "dexp": R.dexp_share(X, A, B, m), "seconds": round(sec, 2), "matte_share": round(float((m > 0.5).mean()), 4)}
        out.append(f)
        row.update({"u": round(float(u), 4), "segment": [int(knots[i]), int(knots[i + 1])], "t": round(float(t), 4)})
        out_rows.append(row)
        tick(j)
    return out


def frames_dissolve(A, B, n, ease, out_rows):
    out = []
    for i in range(n):
        t = EASES[ease]((i + 1) / (n + 1))
        out.append(blend(A, B, t).round().astype(np.uint8))
        out_rows.append({"t": round(t, 4), "generated": "none (blend)"})
        tick(i + 1, 10)
    return out


def frames_morph(A, B, n, ease, fps, step, out_rows):
    """transitions.py's morph (the DIS flow, optional anchors) with n in-betweens; the ease is the tool's own."""
    import transitions as T
    over = dict(seconds=(n + 2) / fps, fps=fps, max_long_edge=0, canvas="common",
                warp_amount=float(step.get("warp", 1.0)), color_strength=float(step.get("color", 0.7)))
    if step.get("anchors"):
        over["anchors"] = T.parse_anchors(step["anchors"]); over["anchor_falloff"] = float(step.get("falloff", 0.25))
    spec = T.spec_from(step.get("preset", "morph"), **over)
    assert spec.n_frames() == n + 2, (spec.n_frames(), n)
    A2, B2, corr = T.prepare(cv2.cvtColor(A, cv2.COLOR_BGR2RGB), cv2.cvtColor(B, cv2.COLOR_BGR2RGB), spec)
    fr = []
    for k, f in enumerate(T.iter_frames(A2, B2, spec, corr)):
        fr.append(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
        if 0 < k <= n:                                   # the step's own frames (the first and the last are the stills)
            tick(k, 10)
    assert fr[0].shape == A.shape, (fr[0].shape, A.shape)
    for i in range(n):
        out_rows.append({"t": round((i + 1) / (n + 1), 4), "generated": "none (morph)", "method": corr["method"]})
    return fr[1:-1]


def _box_px(box, W, H):
    x0, y0, x1, y1 = box
    return int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)


def box_matte(A, B, box_px, thr=30.0, open_frac=0.02, grow=0.01, feather=0.008):
    """The one moved person inside a teleport box: the Lab difference above thr (higher than the change
    matte's, so a neighbour's small shift drops out), opened by open_frac of the width (thin slivers of a
    neighbour's edge drop out), the largest component and any component at least 2 % of it (boots, a hand), grown and feathered. Soft matte in [0, 1]."""
    H, W = A.shape[:2]
    x0, y0, x1, y1 = box_px
    la = cv2.cvtColor(cv2.GaussianBlur(A, (0, 0), 2), cv2.COLOR_BGR2LAB).astype(np.float32)
    lb = cv2.cvtColor(cv2.GaussianBlur(B, (0, 0), 2), cv2.COLOR_BGR2LAB).astype(np.float32)
    d = np.linalg.norm(la - lb, axis=2)
    m = np.zeros((H, W), np.uint8)
    m[y0:y1, x0:x1] = d[y0:y1, x0:x1] > thr
    k = max(3, int(round(open_frac * W))) | 1
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n > 1:                                   # the person: the largest component and any part at least 2 % of it (boots, a hand)
        areas = st[1:, cv2.CC_STAT_AREA]; big = areas.max()
        keep = np.zeros_like(m)
        for k in range(1, n):
            if st[k, cv2.CC_STAT_AREA] >= 0.02 * big:
                keep[lab == k] = 1
        m = keep
    g = max(1, int(round(grow * W))) | 1
    core = cv2.dilate(m, np.ones((g, g), np.uint8)).astype(np.float32)
    soft = cv2.GaussianBlur(core, (0, 0), max(1.0, feather * W))
    return np.maximum(soft, core * (soft > 0.5)).clip(0, 1)


def frames_teleport(A, B, n, ease, step, matte_cfg, out_rows):
    """A region of A whose content is absent in B (`out_box`, canvas fractions) squeezes to a vertical line
    and brightens over B's background there; a region of B absent in A (`in_box`) does the reverse; the
    rest of the changed area goes by RIFE inside the change matte. The two halves overlap by `overlap`."""
    H, W = A.shape[:2]
    m = change_matte(A, B, **matte_cfg)
    ob = _box_px(step.get("out_box", [0, 0, 0, 0]), W, H); ib = _box_px(step.get("in_box", [0, 0, 0, 0]), W, H)
    box_mask = np.zeros((H, W), np.float32)
    for x0, y0, x1, y1 in (ob, ib):
        box_mask[y0:y1, x0:x1] = 1
    k = max(3, int(0.01 * W)) | 1
    box_soft = cv2.GaussianBlur(box_mask, (k, k), 0)
    m_rest = m * (1 - box_soft)
    bm = dict(thr=float(step.get("box_thr", 30.0)), open_frac=float(step.get("box_open", 0.02)))
    if step.get("box_mode", "person") == "change":      # the change matte inside the box, as the round-1 teleport did
        m_out = np.zeros_like(m); m_out[ob[1]:ob[3], ob[0]:ob[2]] = m[ob[1]:ob[3], ob[0]:ob[2]]
        m_in = np.zeros_like(m); m_in[ib[1]:ib[3], ib[0]:ib[2]] = m[ib[1]:ib[3], ib[0]:ib[2]]
    else:
        m_out = box_matte(A, B, ob, **bm) if ob[2] > ob[0] else np.zeros_like(m)
        m_in = box_matte(A, B, ib, **bm) if ib[2] > ib[0] else np.zeros_like(m)
    span = float(step.get("span", 0.6)); gain = float(step.get("glow", 0.6))
    rest = step.get("rest", "rife"); flash = int(step.get("flash", 0)); flash_gain = float(step.get("flash_gain", 0.6))
    import rife_probe as R
    out = []
    for i in range(n):
        t = EASES[ease]((i + 1) / (n + 1))
        if rest == "cut":                      # the rest of the frame stays the current still; the next hold is the cut
            X = A.astype(np.float32); base = X.copy()
        else:
            X = _RIFE.at(A, B, t)
            bl = blend(A, B, t)
            base = m_rest[..., None] * X + (1 - m_rest[..., None]) * bl
        # her old spot shows B's background, her new spot A's, underneath the squeezed layers
        base = m_out[..., None] * B.astype(np.float32) + (1 - m_out[..., None]) * base
        base = m_in[..., None] * A.astype(np.float32) + (1 - m_in[..., None]) * base
        p_out = min(1.0, max(0.0, t / span)); p_in = min(1.0, max(0.0, (t - (1 - span)) / span))
        mode = step.get("mode", "squeeze")
        for src, mm, p, box in ((A, m_out, p_out, ob), (B, m_in, 1 - p_in, ib)):
            if p >= 1.0:
                continue
            if mode == "fade":                     # the layer fades in place (a ghost materializing), no squeeze
                al = (mm * (1 - p))[..., None]
                base = base * (1 - al) + src.astype(np.float32) * al
                continue
            sx = max(0.004, 1 - p)
            cx = 0.5 * (box[0] + box[2])
            M = np.float32([[sx, 0, cx * (1 - sx)], [0, 1, 0]])
            lay = cv2.warpAffine(src.astype(np.float32) * mm[..., None], M, (W, H), flags=cv2.INTER_LINEAR)
            al = cv2.warpAffine(mm, M, (W, H), flags=cv2.INTER_LINEAR)[..., None]
            g = 1 + gain * math.sin(math.pi * p)
            base = base * (1 - al) + np.clip(lay * g, 0, 255)
        if flash and i >= n - flash:            # a brightness lift on the last frames before the cut
            base = base * (1 + flash_gain * (i - (n - flash) + 1) / flash)
        out.append(np.clip(base, 0, 255).round().astype(np.uint8))
        out_rows.append({"t": round(t, 4), "generated": "none (still + the squeezed layer)" if rest == "cut" else "rife (outside the boxes)",
                         "p_out": round(p_out, 3), "p_in": round(p_in, 3),
                         "dexp_rest": 0.0 if rest == "cut" else R.dexp_share(X, A, B, m_rest)})
    return out, m


def grabcut_matte(img, box_px, iters=5, proxy=None, feather=0.004):
    """A person inside a box by GrabCut (rect init on a proxy, the GMM colour model separates olive from
    beige where a Lab threshold cannot), upsampled and feathered. Soft matte in [0, 1]."""
    H, W = img.shape[:2]
    x0, y0, x1, y1 = box_px
    if proxy is None:
        proxy = min(1.0, 1000.0 / max(H, W))            # GrabCut on a long side of about 1000 px
    small = cv2.resize(img, None, fx=proxy, fy=proxy, interpolation=cv2.INTER_AREA) if proxy < 1 else img.copy()
    rect = (int(x0 * proxy), int(y0 * proxy), int((x1 - x0) * proxy), int((y1 - y0) * proxy))
    mask = np.zeros(small.shape[:2], np.uint8)
    bg = np.zeros((1, 65), np.float64); fg = np.zeros((1, 65), np.float64)
    cv2.grabCut(small, mask, rect, bg, fg, iters, cv2.GC_INIT_WITH_RECT)
    m = ((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n > 1:
        areas = st[1:, cv2.CC_STAT_AREA]; big = areas.max(); keep = np.zeros_like(m)
        for k in range(1, n):
            if st[k, cv2.CC_STAT_AREA] >= 0.02 * big:
                keep[lab == k] = 1
        m = keep
    m = cv2.resize(m.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    soft = cv2.GaussianBlur(m, (0, 0), max(1.0, feather * W))
    return np.clip(np.maximum(soft, m * (soft > 0.5)), 0, 1)


def _matte_for(img, other, box_px, spec):
    """A person matte by the plan's choice: {"kind": "grabcut"} or {"kind": "box", "thr": 24}; `exclude` lists
    boxes (canvas fractions) zeroed afterwards (a neighbour inside the box)."""
    H, W = img.shape[:2]
    if spec.get("kind", "box") == "grabcut":
        m = grabcut_matte(img, box_px, iters=int(spec.get("iters", 5)))
        if (m > 0.5).mean() < 0.002:
            log("matte: GrabCut found nothing in the box; the box matte (thr 24) used instead")
            m = box_matte(img, other, box_px, thr=24.0)
    else:
        m = box_matte(img, other, box_px, thr=float(spec.get("thr", 30.0)), open_frac=float(spec.get("open", 0.02)))
    for ex in spec.get("exclude", []):
        x0, y0, x1, y1 = _box_px(ex, W, H)
        m[y0:y1, x0:x1] = 0
    if spec.get("exclude"):
        m = cv2.GaussianBlur(m, (0, 0), max(1.0, 0.004 * W))
    er = float(spec.get("erode", 0.0))                                # shrink the matte by this fraction of the width (a halo of the old background)
    if er > 0:
        k = max(3, int(round(er * W))) | 1
        core = cv2.erode((m > 0.5).astype(np.uint8), np.ones((k, k), np.uint8)).astype(np.float32)
        soft = cv2.GaussianBlur(core, (0, 0), max(1.0, 0.004 * W))
        m = np.clip(np.maximum(soft, core * (soft > 0.5)), 0, 1)
    return m


def _centroid(m):
    ys, xs = np.nonzero(m > 0.5)
    return np.array([xs.mean(), ys.mean()], np.float32)


def _shift(img, d):
    M = np.float32([[1, 0, d[0]], [0, 1, d[1]]])
    return cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


def _hblur(img, length):
    """A horizontal box blur of the given length in px (a motion blur along a lateral move)."""
    k = int(round(length))
    if k < 2:
        return img
    return cv2.blur(img, (k, 1))


def fill_region(img, region, donor=None, donor_valid=None):
    """Fill `region` (uint8 0/1) of img: the donor's pixels where donor_valid says the donor shows background
    there, else a horizontal extension from the nearest filled pixel on the left of the row (the right when
    the row has none). Plain walls and floors extend well; a person's pixels never do."""
    out = img.copy()
    reg = region > 0
    if donor is not None:
        ok = reg & (donor_valid > 0 if donor_valid is not None else True)
        out[ok] = donor[ok]; reg = reg & ~ok
    H, W = img.shape[:2]
    for y in np.nonzero(reg.any(1))[0]:
        row = reg[y]; xs = np.nonzero(row)[0]
        # runs of pixels to fill
        start = xs[0]; prev = xs[0]
        runs = []
        for x in xs[1:]:
            if x != prev + 1:
                runs.append((start, prev)); start = x
            prev = x
        runs.append((start, prev))
        for a, b in runs:
            if a > 0:
                src = out[y, a - 1].astype(np.float32); src2 = out[y, b + 1].astype(np.float32) if b + 1 < W else src
                w = np.linspace(0, 1, b - a + 1, dtype=np.float32)[:, None]
                out[y, a:b + 1] = (src * (1 - w) + src2 * w).round().astype(np.uint8)
            elif b + 1 < W:
                out[y, a:b + 1] = out[y, b + 1]
    return out


def fill_vertical(img, region, floor_y=None, band=(8, 48)):
    """Fill `region` (uint8 0/1) column by column with the wall from above it and, below the row floor_y (a
    fraction of the height), the floor from below it: per column, the median of a band of rows above the
    region's top row (and below its bottom row), so a hat or a shadow at the region's edge does not streak.
    Donor-free; for a person standing against a plain wall and floor. The result is blurred by 2 px."""
    out = img.copy(); H, W = img.shape[:2]
    reg = region > 0
    rows = np.nonzero(reg.any(1))[0]
    if len(rows) == 0:
        return out
    y_top, y_bot = int(rows[0]), int(rows[-1])
    split = H if floor_y is None else int(floor_y * H)
    a0, a1 = max(0, y_top - band[1]), max(1, y_top - band[0])
    b0, b1 = min(H - 1, y_bot + band[0]), min(H, y_bot + band[1])
    top = np.median(img[a0:a1].astype(np.float32), axis=0) if a1 > a0 else img[y_top].astype(np.float32)
    bot = np.median(img[b0:b1].astype(np.float32), axis=0) if b1 > b0 else img[y_bot].astype(np.float32)
    fill = np.empty_like(out)
    fill[:split] = top[None].round().astype(np.uint8)
    fill[split:] = bot[None].round().astype(np.uint8)
    fill = cv2.GaussianBlur(fill, (0, 0), 2)
    out[reg] = fill[reg]
    return out


def frames_slide(A, B, n, ease, step, matte_cfg, out_rows):
    """One person slides laterally from her place in A to her place in B: her cutout (A's, crossfading to B's
    in flight, with a motion blur along the move) travels along the straight path between the two mattes'
    centroids inside the window [w0, w1] of the segment; underneath, the base morphs by RIFE between A' and B'
    (the stills with her removed: A' takes B's pixels at her A spot, B' is inpainted at her B spot, both
    labelled), so the remaining people move too."""
    H, W = A.shape[:2]
    ba = _box_px(step["box_a"], W, H); bb = _box_px(step["box_b"], W, H)
    mA = _matte_for(A, B, ba, step.get("matte_a", {"kind": "box", "thr": 24}))
    mB = _matte_for(B, A, bb, step.get("matte_b", {"kind": "grabcut"}))
    g = max(3, int(0.012 * W)) | 1
    hA = cv2.dilate((mA > 0.5).astype(np.uint8), np.ones((g, g), np.uint8))
    hB = cv2.dilate((mB > 0.5).astype(np.uint8), np.ones((g, g), np.uint8))
    A2 = fill_region(A, hA, donor=B, donor_valid=(1 - hB))                 # her A spot: B's pixels (the wall)
    if "donor_box_b" in step:                                               # at her B spot the donor A shows someone else: exclude him
        db = _box_px(step["donor_box_b"], W, H); mD = grabcut_matte(A, db)
        valid = 1 - cv2.dilate((mD > 0.5).astype(np.uint8), np.ones((g, g), np.uint8))
    else:
        valid = np.ones((H, W), np.uint8)
    fill = step.get("fill", "donor+vertical")
    if fill == "vertical":
        B2 = fill_vertical(B, hB, step.get("floor_y"))                      # her B spot: the wall from above, the floor from below
    elif fill == "donor+vertical":                                          # the vertical fill, then A's own background where A shows it
        B2 = fill_vertical(B, hB, step.get("floor_y"))
        ok = (hB > 0) & (valid * (1 - hA) > 0)
        B2[ok] = A[ok]
    else:
        B2 = fill_region(B, hB, donor=A, donor_valid=valid * (1 - hA))     # her B spot: A's background, else the wall extended
    m_rest = change_matte(A2, B2, **matte_cfg); m3 = m_rest[..., None]
    cA, cB = _centroid(mA), _centroid(mB)
    w0, w1 = step.get("window", [0.2, 0.8])
    cutA = A.astype(np.float32) * mA[..., None]; cutB = B.astype(np.float32) * mB[..., None]
    import rife_probe as R
    out = []; prev_p = None
    mode = step.get("mode", "fly")
    for i in range(n):
        t = EASES[ease]((i + 1) / (n + 1))
        X = _RIFE.at(A2, B2, t)
        base = m3 * X + (1 - m3) * blend(A2, B2, t)
        if mode == "dissolve":                    # no flight: the old cutout fades out in place, the new one fades in at the destination
            wo0, wo1 = step.get("window_out", [0.0, 0.55]); wi0, wi1 = step.get("window_in", [0.45, 1.0])
            qo = EASES["sine"](min(1.0, max(0.0, (t - wo0) / (wo1 - wo0)))); qi = EASES["sine"](min(1.0, max(0.0, (t - wi0) / (wi1 - wi0))))
            al = np.clip(mA * (1 - qo) + mB * qi, 0, 1)
            lay = cutA * (1 - qo) + cutB * qi                       # cutA is A premultiplied by mA already: one matte factor, not two
            al3 = al[..., None]
            frame = base * (1 - al3) + lay
            out.append(np.clip(frame, 0, 255).round().astype(np.uint8))
            out_rows.append({"t": round(t, 4), "generated": "rife (the base)", "fade_out": round(qo, 3), "fade_in": round(qi, 3), "dexp_rest": R.dexp_share(X, A2, B2, m_rest)})
            continue
        q = min(1.0, max(0.0, (t - w0) / (w1 - w0)))
        e = EASES[step.get("slide_ease", "sine")](q)
        p = cA + e * (cB - cA)
        speed = 0.0 if prev_p is None else float(np.hypot(*(p - prev_p)))
        prev_p = p
        # the two cutouts, each moved so its centroid sits at p; a crossfade between them over the window
        layA = _shift(cutA, p - cA); alA = _shift(mA, p - cA)
        layB = _shift(cutB, p - cB); alB = _shift(mB, p - cB)
        f = e
        lay = (1 - f) * layA + f * layB; al = (1 - f) * alA + f * alB
        if step.get("blur", True) and speed > 2:
            bl_k = speed * float(step.get("blur_k", 0.5))
            lay = _hblur(lay, bl_k); al = _hblur(al, bl_k)
        if i == n - 1:                                                      # the last in-between: B's own pixels cover the fill, with a soft edge
            cover = cv2.GaussianBlur(hB.astype(np.float32), (0, 0), max(1.0, 0.004 * W))
            lay = np.where((cover > al)[..., None], B.astype(np.float32), lay) if f >= 0.999 else lay
            al = np.maximum(al, cover * (f >= 0.999))
        al3 = np.clip(al, 0, 1)[..., None]
        frame = base * (1 - al3) + lay * (al3 / np.maximum(al3, 1e-6)) * al3
        out.append(np.clip(frame, 0, 255).round().astype(np.uint8))
        out_rows.append({"t": round(t, 4), "generated": "rife (the base) + an inpaint at her destination", "slide": round(e, 3), "speed_px": round(speed, 1),
                         "dexp_rest": R.dexp_share(X, A2, B2, m_rest)})
    return out, {"cA": cA.tolist(), "cB": cB.tolist(), "mA_share": round(float((mA > 0.5).mean()), 4), "mB_share": round(float((mB > 0.5).mean()), 4)}


def frames_rise(A, B, n, ease, step, matte_cfg, out_rows):
    """A person present only in B (the ghoul) comes up from behind another person (the man): B's cutout of the
    ghoul travels from its B position plus `start_offset` to its B position inside the window, drawn on the
    base (RIFE between A and B', B with the ghoul replaced by A's pixels) and then occluded by the man's own
    cutout from the base. `direction: down` reverses the move (the sink at the end)."""
    H, W = A.shape[:2]
    gb = _box_px(step["ghoul_box"], W, H); mb = _box_px(step["man_box"], W, H)
    src = B if step.get("direction", "up") == "up" else A         # the still that holds the ghoul
    other = A if src is B else B
    mG = _matte_for(src, other, gb, step.get("matte_ghoul", {"kind": "grabcut"}))
    mM = _matte_for(src, other, mb, step.get("matte_man", {"kind": "grabcut"}))
    g = max(3, int(0.012 * W)) | 1
    hG = cv2.dilate((mG > 0.5).astype(np.uint8), np.ones((g, g), np.uint8))
    if "man_box_other" in step:                                        # the other still shows the man where the ghoul stands: exclude him
        ob = _box_px(step["man_box_other"], W, H); mO = grabcut_matte(other, ob)
        valid = 1 - cv2.dilate((mO > 0.5).astype(np.uint8), np.ones((g, g), np.uint8))
    else:
        valid = np.ones((H, W), np.uint8)
    if step.get("fill", "vertical") == "vertical":
        src2 = fill_vertical(src, hG, step.get("floor_y"))              # the ghoul's spot: the wall from above
    else:
        src2 = fill_region(src, hG, donor=other, donor_valid=valid)    # the ghoul's spot: the other still's background, else the wall extended
    A2, B2 = (A, src2) if src is B else (src2, B)
    m_rest = change_matte(A2, B2, **matte_cfg); m3 = m_rest[..., None]
    off = np.array(step.get("start_offset", [0, 0.1]), np.float32) * np.array([W, H], np.float32)
    w0, w1 = step.get("window", [0.35, 1.0])
    cut = src.astype(np.float32) * mG[..., None]
    import rife_probe as R
    out = []
    for i in range(n):
        t = EASES[ease]((i + 1) / (n + 1))
        X = _RIFE.at(A2, B2, t)
        base = m3 * X + (1 - m3) * blend(A2, B2, t)
        q = min(1.0, max(0.0, (t - w0) / (w1 - w0)))
        e = EASES[step.get("rise_ease", "smooth")](q)
        vis = e if src is B else 1 - e                                   # how far the ghoul has risen
        d = off * (1 - vis)
        lay = _shift(cut, d); al = _shift(mG, d)[..., None]
        frame = base * (1 - al) + lay
        man = mM[..., None]                                              # the man in front, from the base
        frame = frame * (1 - man) + base * man
        out.append(np.clip(frame, 0, 255).round().astype(np.uint8))
        out_rows.append({"t": round(t, 4), "generated": "rife (the base)", "rise": round(vis, 3), "dexp_rest": R.dexp_share(X, A2, B2, m_rest)})
    return out, {"mG_share": round(float((mG > 0.5).mean()), 4), "mM_share": round(float((mM > 0.5).mean()), 4)}


def frames_snap(A, B, n, step, out_rows):
    """A fast change in n frames: the plain blend, blurred along `direction` by a line kernel whose length
    is blur_frac of the height times sin(πt) (a whip; the blur hides the double exposure of a big move).
    No generated pixels."""
    H, W = A.shape[:2]
    frac = float(step.get("blur_frac", 0.015)); horiz = step.get("direction", "vertical") == "horizontal"
    out = []
    for i in range(n):
        t = (i + 1) / (n + 1)
        f = blend(A, B, t)
        L = int(round(frac * H * math.sin(math.pi * t))) | 1
        if L >= 3:
            k = np.zeros((1, L), np.float32) if horiz else np.zeros((L, 1), np.float32)
            k[:] = 1.0 / L
            f = cv2.filter2D(f, -1, k, borderType=cv2.BORDER_REFLECT)
        out.append(np.clip(f, 0, 255).round().astype(np.uint8))
        out_rows.append({"t": round(t, 4), "generated": "none (blend + motion blur)", "blur_px": L})
        tick(i + 1, 10)
    return out


# ------------------------------------------------------------------ slices: diagonal cards that slide into place (2026-11-01, the seasons)

def _soft(u, lo, hi):
    """The weight of the interval [lo, hi) with a 1 px linear edge; adjacent intervals sum to 1."""
    return np.clip(u - lo + 0.5, 0.0, 1.0) * np.clip(hi - u + 0.5, 0.0, 1.0)


def _cell_bbox(m):
    ys = np.flatnonzero(m.any(1)); xs = np.flatnonzero(m.any(0))
    return int(xs[0]), int(ys[0]), int(xs[-1]) + 1, int(ys[-1]) + 1


def slices_cells(W, H, step):
    """The cells of the canvas for `slices`: bands between parallel lines at `angle` degrees from the horizontal
    (family 1, index i; `bands` of them, or relative `widths`), optionally crossed by a second family along the
    band axis (`families` 2: a lattice, index j), optionally folded about the centre column (`mirror`: a chevron,
    each band split into a left and a right half-cell with mirrored directions). Returns the coordinate fields
    u1 (across the bands) and u2 (along them), the unit vectors, and one dict per cell: its edges, its static
    soft mask on its bounding box, the static factor of the other family, its order index and its sign."""
    th = math.radians(float(step.get("angle", 62.0)))
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    mirror = bool(step.get("mirror", False))
    xm = np.abs(xs - (W - 1) / 2.0) if mirror else xs
    u1 = -xm * math.sin(th) + ys * math.cos(th)
    u2 = xm * math.cos(th) + ys * math.sin(th)
    n1 = (-math.sin(th), math.cos(th)); d1 = (math.cos(th), math.sin(th))
    families = int(step.get("families", 1))
    nb = int(step.get("bands", 12))
    lo1, hi1 = float(u1.min()), float(u1.max()) + 1e-3
    widths = step.get("widths")
    if widths:
        wv = np.array(widths, np.float64); wv = wv / wv.sum() * (hi1 - lo1); nb = len(wv)
    else:
        wv = np.full(nb, (hi1 - lo1) / nb)
    e1 = np.concatenate([[lo1], lo1 + np.cumsum(wv)]); e1t = e1.copy(); e1[0] -= 1e4; e1[-1] += 1e4   # e1t: the true edges (the card's interval); e1: membership reaches past the canvas
    if families == 2:
        lo2, hi2 = float(u2.min()), float(u2.max()) + 1e-3
        w2 = float(step.get("width2", 0)) or float(np.mean(wv))
        nb2 = max(1, int(math.ceil((hi2 - lo2) / w2)))
        e2 = lo2 + np.arange(nb2 + 1) * w2; e2t = e2.copy(); e2[0] -= 1e4; e2[-1] += 1e4
    else:
        nb2, e2, e2t = 1, None, None
    pattern = step.get("order", "up")
    rng = np.random.default_rng(int(step.get("seed", 1)))
    perm = rng.permutation(nb * nb2)
    alternate = bool(step.get("alternate", False)); base_dir = 1 if int(step.get("dir", 1)) >= 0 else -1
    lattice_axis = str(step.get("lattice_axis", "alt"))
    cells = []
    halves = (("L", xs < (W - 1) / 2.0), ("R", xs >= (W - 1) / 2.0)) if mirror else ((None, None),)
    for i in range(nb):
        for j in range(nb2):
            if pattern == "up": idx = i if families == 1 else i + j
            elif pattern == "down": idx = (nb - 1 - i) if families == 1 else (nb - 1 - i) + (nb2 - 1 - j)
            elif pattern == "centre": idx = abs(2 * i - (nb - 1)) // 2
            elif pattern == "edges": idx = (nb - 1) // 2 - abs(2 * i - (nb - 1)) // 2
            elif pattern == "random": idx = int(perm[i * nb2 + j])
            elif pattern == "diag": idx = i + j
            elif pattern == "antidiag": idx = i + (nb2 - 1 - j)
            else: sys.exit(f"slices: unknown order {pattern}")
            par = (i + j) if families == 2 else i
            sgn = base_dir * (-1 if (alternate and par % 2) else 1)
            if families == 2:
                axis = (1 if par % 2 == 0 else 2) if lattice_axis == "alt" else int(lattice_axis)
            else:
                axis = 1
            w1 = _soft(u1, e1[i], e1[i + 1])
            f2 = _soft(u2, e2[j], e2[j + 1]) if families == 2 else None
            for hname, hmask in halves:
                m = w1 if f2 is None else w1 * f2
                other = None if f2 is None else (f2 if axis == 1 else w1)   # the card's interval runs along its own family; the other family bounds it
                if hmask is not None:
                    m = m * hmask; other = hmask.astype(np.float32) if other is None else other * hmask
                if not m.any():
                    continue
                x0, y0, x1, y1 = _cell_bbox(m > 0)
                hs = 1.0 if hname in (None, "R") else -1.0       # the mirrored half slides the other way in x
                cells.append({"i": i, "j": j, "half": hname, "bbox": (x0, y0, x1, y1), "mask": m[y0:y1, x0:x1].copy(),
                              "other": None if other is None else other[y0:y1, x0:x1].copy(),
                              "e1": (float(e1t[i]), float(e1t[i + 1])), "e2": None if e2t is None else (float(e2t[j]), float(e2t[j + 1])),
                              "width": float(wv[i]) if axis == 1 else w2, "idx": int(idx), "sign": sgn, "axis": axis,
                              "vec": (hs * (n1[0] if axis == 1 else d1[0]), (n1[1] if axis == 1 else d1[1]))})
    ranks = {r: k for k, r in enumerate(sorted(set(c["idx"] for c in cells)))}
    for c in cells:
        c["idx"] = ranks[c["idx"]]
    return u1, u2, n1, d1, cells


def frames_slices(keys, knots, step, out_rows):
    """The canvas cut into diagonal cells; each cell's content slides from the current still to the next as a
    card that enters its cell (`slide` across: the card comes in from the neighbouring side over the cell's
    width; `slide` along: the whole band's content rolls along the band axis by `travel` × the canvas diagonal
    over the mirrored canvas and locks). Cells start in `order` with `stagger` frames between ranks, each over `dur`
    frames under `ease`; with `through` the cells cycle on through the stills every `period` frames (a wave).
    The moving content is motion-blurred by `samples` sub-frames over `shutter` of the frame's own motion (forward, so the
    last in-flight frame is blurred over the few px left); the borders are 1 px soft; a landed cell is the next still's
    pixels exactly. No generated pixels."""
    H, W = keys[knots[0]].shape[:2]
    u1, u2, n1, d1, cells = slices_cells(W, H, step)
    slide = step.get("slide", "across")
    dur = int(step.get("dur", 12)); stagger = int(step.get("stagger", 2)); ease = EASES[step.get("ease", "smooth")]
    K = max(1, int(step.get("samples", 6))); K_MAX = int(step.get("samples_max", 48)); shutter = float(step.get("shutter", 0.8))
    ramp = int(step.get("ramp", 3)); shadow = float(step.get("shadow", 0.0)); shadow_px = float(step.get("shadow_px", 24))
    flip_each = bool(step.get("flip_each", True)); reverse_each = bool(step.get("reverse_each", False))
    T = len(knots) - 1
    max_idx = max(c["idx"] for c in cells)
    period = int(step.get("period", max_idx * stagger + dur))
    diag = math.hypot(W, H); travel = float(step.get("travel", 0.4)) * diag
    # the schedule: per cell and transition m the start frame; the cell is in flight on (start, start + dur)
    def start_of(c, m):
        idx = (max_idx - c["idx"]) if (reverse_each and m % 2) else c["idx"]
        return m * period + idx * stagger
    n_total = max(start_of(c, m) + dur for c in cells for m in range(T))
    replan(step.get("n", 0), n_total - 1)               # the schedule's count replaces the plan's `n` in the progress total
    # the padded stills (mirrored beyond the canvas; `wrap: true` rolls the canvas round instead, which puts the canvas
    # edge as a hard line inside a rolling band) for content that comes from beyond the canvas
    pad = int(math.ceil(travel if slide == "along" else max(c["width"] for c in cells))) + 4
    border = cv2.BORDER_WRAP if (slide == "along" and step.get("wrap", False)) else cv2.BORDER_REFLECT_101
    if border == cv2.BORDER_REFLECT_101:
        pad = min(pad, min(H, W) - 2)
    padded = {k: cv2.copyMakeBorder(keys[k].astype(np.float32), pad, pad, pad, pad, border) for k in set(knots)}
    keysf = {k: keys[k].astype(np.float32) for k in set(knots)}
    out = []
    for f in range(1, n_total):
        frame = np.zeros((H, W, 3), np.float32)
        active = 0; disp_max = 0.0
        for c in cells:
            x0, y0, x1, y1 = c["bbox"]; m = c["mask"]
            done = sum(1 for mm in range(T) if f >= start_of(c, mm) + dur)
            cur = knots[done]
            frame[y0:y1, x0:x1] += m[..., None] * keysf[cur][y0:y1, x0:x1]
            if done >= T:
                continue
            st = start_of(c, done)
            if not (st < f < st + dur):
                continue
            active += 1
            nxt = knots[done + 1]
            sgn = c["sign"] * (-1 if (flip_each and done % 2) else 1)
            s0 = sgn * (travel if slide == "along" else c["width"])
            p_now, p_next = ease((f - st) / dur), ease(min(1.0, (f + 1 - st) / dur))
            s_now, s_next = s0 * (1 - p_now), s0 * (1 - p_next)
            disp_max = max(disp_max, abs(s_next - s_now))
            vx, vy = c["vec"]
            cx = (x0 + x1 - 1) / 2.0 + pad; cy = (y0 + y1 - 1) / 2.0 + pad
            bw, bh = x1 - x0, y1 - y0
            u1c = u1[y0:y1, x0:x1] if c["axis"] == 1 else u2[y0:y1, x0:x1]
            lo, hi = c["e1"] if c["axis"] == 1 else c["e2"]
            curc = keysf[cur][y0:y1, x0:x1]
            acc = np.zeros((bh, bw, 3), np.float32)
            alpha = min(1.0, (f - st) / ramp) if (slide == "along" and ramp > 0) else 1.0
            Kf = int(min(K_MAX, max(K, math.ceil(shutter * abs(s_next - s_now) / 2.0))))   # a sample every <= 2 px, or a thin line becomes a comb
            for k in range(Kf):
                tau = shutter * (k + 0.5) / Kf                      # forward: the window [f, f + shutter] of this frame's motion
                s = s_now + tau * (s_next - s_now)
                patch = cv2.getRectSubPix(padded[nxt], (bw, bh), (cx - s * vx, cy - s * vy))
                if slide == "along":
                    mk = m * alpha
                else:
                    mk = _soft(u1c, lo + max(s, 0.0), hi + min(s, 0.0))
                    if c["other"] is not None:
                        mk = mk * c["other"]
                acc += mk[..., None] * (patch - curc)
            frame[y0:y1, x0:x1] += acc / Kf
            if shadow > 0 and slide == "across":
                edge = lo + s_now if s_now > 0 else hi + s_now
                dist = (edge - u1c) if s_now > 0 else (u1c - edge)
                sh = shadow * np.clip(1.0 - dist / shadow_px, 0.0, 1.0) * (dist > 0) * m
                frame[y0:y1, x0:x1] *= (1.0 - sh)[..., None]
        out.append(np.clip(frame, 0, 255).round().astype(np.uint8))
        out_rows.append({"t": round(f / n_total, 4), "generated": "none (slices)", "active": active, "disp_px": round(disp_max, 1)})
        tick(f, 10)
    info = {"cells": len(cells), "frames": len(out), "period": period, "n_total": n_total, "slide": slide,
            "pad": pad, "width_px": round(float(np.mean([c["width"] for c in cells])), 1)}
    return out, info


# ------------------------------------------------------------------ sheets: whole pictures that slide across each other (2026-11-01, round 2)

def object_plates(keys, base_key, objects, feather_px):
    """Per object (a box read off the base still): a soft matte by GrabCut on the base still (feathered by
    `feather_px`), and per other season the object Poisson-blended into the base still once (`cv2.seamlessClone`,
    NORMAL_CLONE): static plates, so a frame costs one blend inside the matte and nothing flickers."""
    base = keys[base_key]; H, W = base.shape[:2]
    out = []
    for ob in objects:
        box = [int(v) for v in ob["box"]]
        m = grabcut_matte(base, box, feather=0.0005)
        hard = (m > 0.5).astype(np.uint8) * 255
        if hard.sum() == 0:                                   # GrabCut found nothing: the box itself
            hard[box[1]:box[3], box[0]:box[2]] = 255
        hard[:2, :] = 0; hard[-2:, :] = 0; hard[:, :2] = 0; hard[:, -2:] = 0    # seamlessClone needs the mask's box inside the image
        soft = cv2.GaussianBlur((hard / 255.0).astype(np.float32), (0, 0), feather_px)
        soft = np.clip(np.maximum(soft, (hard > 0) * soft), 0, 1)
        ys, xs = np.nonzero(hard); x0, x1, y0, y1 = int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1
        centre = (x0 + (x1 - x0) // 2, y0 + (y1 - y0) // 2)        # OpenCV places the mask's box at centre - size // 2: the identity
        plates = {}
        for k in ob.get("seasons", [k for k in keys if k != base_key]):
            plates[int(k)] = cv2.seamlessClone(keys[int(k)], base, hard, centre, cv2.NORMAL_CLONE)
        cx, cy = float(xs.mean()), float(ys.mean())
        out.append({"name": ob.get("name", str(box)), "box": box, "matte": soft, "plates": plates, "centre": (cx, cy),
                    "share": round(float((hard > 0).mean()), 4), "lead": int(ob.get("lead", 6)), "linger": int(ob.get("linger", 10))})
    return out


def frames_sheets(keys, cur, step, out_rows, src):
    """Whole pictures as sheets that slide across the base still at once and pass each other. Each sheet is a
    band (`width` × the canvas extent along the slide normal) bounded by edges at `angle`, home at the canvas
    centre, entering from its `side` and leaving at the other over the step's `n` frames under `ease`; its content
    moves with it by `carry` (1: the picture slides and is registered only at home; 0: a wipe over the static still).
    Sheets are listed back to front; where the front sheet covers a back one it shows at `overlap_alpha`. Depth
    cues: `shadow` (a contact shadow beyond a sheet's edges onto what lies beneath, `shadow_px` wide), `parallax`
    (the content's move scaled by 1 + parallax × (2 depth − 1) from the depth model's map, near more than far,
    zero where the sheet is home), `scale` per sheet (the front a little larger). `objects` on the base: per object
    a Poisson plate per season, faded in `lead` frames before a sheet reaches the object and out `linger` frames
    after it leaves. Motion blur by sub-samples over `shutter` of the frame's edge motion (forward window,
    one sample per 2 px, at most `samples_max`). A sheet's content exists only where its source lies inside its picture
    (a validity mask, no border fill): a carried picture shows its own edges, and a drift stays clean inside the plan's
    `crop` margin. The base still is the only one held; nothing is generated."""
    H, W = keys[cur].shape[:2]
    W0 = json.loads((Path(src) / "prep.json").read_text())["canvas"][0]
    sc_draft = W / float(W0)                                     # pixel knobs and boxes are in prep-canvas px; a draft scales them
    th = math.radians(float(step.get("angle", 62.0)))
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    cx0, cy0 = (W - 1) / 2.0, (H - 1) / 2.0
    motion = str(step.get("motion", "normal"))
    if motion == "lateral":                                        # the edge keeps its slant; the sheet moves along x
        nx, ny = 1.0, 0.0
        u = xs - (ys - cy0) * (math.cos(th) / math.sin(th))         # the edge line's x at the centre row
    else:
        nx, ny = -math.sin(th), math.cos(th)
        u = xs * nx + ys * ny
    cf = float(step.get("_crop", 1.0))                           # the plan's centre crop: the sheets travel the VISIBLE extent
    cw, ch = int(round(W * cf)) & ~1, int(round(H * cf)) & ~1; cx1, cy1 = (W - cw) // 2, (H - ch) // 2
    uv = u[cy1:cy1 + ch, cx1:cx1 + cw]
    u_min, u_max = float(uv.min()), float(uv.max()); E = u_max - u_min; home = 0.5 * (u_min + u_max)
    E_full = float(u.max()) - float(u.min())                     # a whole picture spans the canvas extent, not the visible one
    n = int(step["n"]); ease = EASES[step.get("ease", "linear")]
    vfeather = max(0.5, float(step.get("valid_feather", 1.0)) * sc_draft)   # the softness of a picture's own edge inside a sheet
    feather = max(0.5, float(step.get("feather", 1.5)) * sc_draft); shadow = float(step.get("shadow", 0.0)); shadow_px = float(step.get("shadow_px", 40)) * sc_draft
    overlap_alpha = float(step.get("overlap_alpha", 1.0)); shutter = float(step.get("shutter", 0.0)); K_MAX = int(step.get("samples_max", 24))
    parallax = float(step.get("parallax", 0.0)); shadow_from = str(step.get("shadow_from", "front"))
    sheets = step["sheets"]
    keysf = {k: keys[k].astype(np.float32) for k in set([cur] + [int(s["key"]) for s in sheets])}
    depth = {}
    if parallax:
        for s in sheets:
            k = int(s["key"]); D = np.load(Path(src) / f"depth_k{k}.npy")
            if D.shape != (H, W):
                D = cv2.resize(D, (W, H), interpolation=cv2.INTER_AREA)
            depth[k] = (2.0 * D - 1.0).astype(np.float32)            # -1 far .. +1 near
    edge_depth = float(step.get("edge_depth", 0.0)) * sc_draft    # px: the wipe edge reaches near pixels later than far ones
    D0 = None
    if edge_depth or any(s.get("layer") for s in step["sheets"]):
        D0 = np.load(Path(src) / f"depth_k{cur}.npy")
        if D0.shape != (H, W):
            D0 = cv2.resize(D0, (W, H), interpolation=cv2.INTER_AREA)
        D0 = cv2.GaussianBlur(D0.astype(np.float32), (0, 0), max(1.0, 8.0 * sc_draft))

    def band(s, f):
        """The sheet's displacement along the normal at (fractional) frame f, and its width in px (`width` "photo":
        the whole picture behind its leading diagonal edge; the picture's own edges then bound the sheet)."""
        sign = 1.0 if str(s.get("side", "+")) == "+" else -1.0
        if s.get("width") == "photo":                                 # the whole picture: its rectangle must clear the window
            Wb = E_full
            if sign > 0:
                reach = min((W - cx1) / abs(nx) if nx else 1e9, (cy1 + ch) / abs(ny) if ny else 1e9) + 2.0
            else:
                reach = min((cx1 + cw) / abs(nx) if nx else 1e9, (H - cy1) / abs(ny) if ny else 1e9) + 2.0
        else:
            Wb = float(s.get("width", 0.8)) * E; reach = E / 2 + Wb / 2 + 2.0
        if D0 is not None:
            reach += edge_depth * float(D0.max())                    # a bent edge trails behind on near pixels: travel that much more
        reach += feather / 2.0                                       # and the soft edge's half width, so nothing is left at the end
        lag = int(s.get("lag", 0)); span = max(1, int(s.get("dur", n - lag)))   # the sheet's own sweep length
        t = min(1.0, max(0.0, (f - lag) / span))
        return sign * reach * (1.0 - 2.0 * ease(t)), Wb

    layer_soft = float(step.get("layer_soft", 0.06))
    def layer_weight(s):
        """A sheet limited to a depth range [lo, hi] of the base still's map (0 far .. 1 near), soft at both ends."""
        lay = s.get("layer")
        if not lay or D0 is None:
            return None
        lo, hi = float(lay[0]), float(lay[1])
        w = 1.0 / (1.0 + np.exp(-(D0 - lo) / layer_soft)) * (1.0 / (1.0 + np.exp(-(hi - D0) / layer_soft)))
        if s.get("layer_y"):                                           # a row bound in prep-canvas px (the sky above the skyline)
            y0, y1 = float(s["layer_y"][0]) * sc_draft, float(s["layer_y"][1]) * sc_draft
            soft_y = max(2.0, 24.0 * sc_draft)
            w = w * np.clip((ys - y0) / soft_y + 0.5, 0, 1) * np.clip((y1 - ys) / soft_y + 0.5, 0, 1)
        return w.astype(np.float32)
    layers = [layer_weight(s) for s in step["sheets"]]

    objs = []
    if step.get("objects"):
        obs = [dict(ob, box=[v * sc_draft for v in ob["box"]]) for ob in step["objects"]]
        objs = object_plates(keys, cur, obs, max(1.0, float(step.get("object_feather", 6.0)) * sc_draft))
    for ob in objs:                                              # when each sheet covers the object's centre
        uo = (ob["centre"][0] - (ob["centre"][1] - cy0) * (math.cos(th) / math.sin(th))) if motion == "lateral" else (ob["centre"][0] * nx + ob["centre"][1] * ny)
        ob["cover"] = {}
        for si, s in enumerate(sheets):
            k = int(s["key"])
            if k not in ob["plates"]:
                continue
            lw = layers[si]
            if lw is not None and lw[int(ob["centre"][1]), int(ob["centre"][0])] < 0.5:
                continue                                           # this sheet does not touch the object's depth layer
            fr = [f for f in range(0, n + 1) if abs(home + band(s, f)[0] - uo) <= band(s, f)[1] / 2]
            if fr:
                ob["cover"][si] = (fr[0], fr[-1] + 1)
    def object_alpha(ob, si, f):
        if si not in ob.get("cover", {}):
            return 0.0
        f_in, f_out = ob["cover"][si]; lead, linger = ob["lead"], ob["linger"]
        if f < f_in:
            return EASES["smooth"](max(0.0, 1.0 - (f_in - f) / lead)) if lead > 0 else 0.0
        if f < f_out:
            return 1.0
        return EASES["smooth"](max(0.0, 1.0 - (f - f_out) / linger)) if linger > 0 else 0.0

    def composite(f):
        frame = keysf[cur].copy()
        for ob in objs:
            for si, s in enumerate(sheets):
                k = int(s["key"]); a = object_alpha(ob, si, f)
                if a > 0 and k in ob["plates"]:
                    am = (a * ob["matte"])[..., None]
                    frame = ob["plates"][k].astype(np.float32) * am + frame * (1.0 - am)
        under = None
        for si, s in enumerate(sheets):
            d, Wb = band(s, f); k = int(s["key"]); carry = float(s.get("carry", 1.0)); sc = 1.0 + float(s.get("scale", 0.0))
            sign = 1.0 if str(s.get("side", "+")) == "+" else -1.0
            lo, hi = home + d - Wb / 2, home + d + Wb / 2
            if s.get("width") == "photo":                             # the leading edge only; the picture's edges bound the rest
                lo, hi = (lo, 1e9) if sign > 0 else (-1e9, hi)
            if hi < u_min - feather - edge_depth or lo > u_max + feather + edge_depth:
                continue
            ue = u if D0 is None else u - sign * edge_depth * D0    # near pixels are reached later by the edge
            m = np.clip((ue - lo) / feather + 0.5, 0.0, 1.0) * np.clip((hi - ue) / feather + 0.5, 0.0, 1.0)
            if layers[si] is not None:
                m = m * layers[si]
            off = carry * d
            if off != 0.0 or sc != 1.0:
                mult = (1.0 + parallax * depth[k]) if parallax else 1.0
                mapx = cx0 + (xs - cx0) / sc - off * nx * mult
                mapy = cy0 + (ys - cy0) / sc - off * ny * mult
                content = cv2.remap(keysf[k], mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
                # the picture exists only where its source is inside it: never a mirrored or padded pixel (a soft edge)
                def _valid(px, py):
                    return (np.clip((px + 0.5) / vfeather, 0.0, 1.0) * np.clip((W - 0.5 - px) / vfeather, 0.0, 1.0)
                            * np.clip((py + 0.5) / vfeather, 0.0, 1.0) * np.clip((H - 0.5 - py) / vfeather, 0.0, 1.0))
                valid = _valid(mapx, mapy)
                m = m * valid
            else:
                content = keysf[k]; _valid = None
            sh_k = float(s.get("shadow", shadow))                     # a sheet may cast no shadow (a summer band over summer)
            if sh_k > 0 and m.max() > 0.01 and (shadow_from == "all" or s is sheets[-1]):
                # a contact shadow from the front sheet's leading edge only (two facing shadows turn the gap into a tube),
                # onto the uncovered side, only where the casting sheet pixel exists; faded while the sheet is a sliver
                dist = (lo - ue) if sign > 0 else (ue - hi)
                gain = min(1.0, float(m.mean()) / 0.02)
                sh = sh_k * gain * np.clip(1.0 - dist / shadow_px, 0.0, 1.0) * (dist > 0)
                if _valid is not None:                           # the casting pixel: `dist` back along the normal, then its source
                    sh = sh * _valid(mapx + dist * sign * nx, mapy + dist * sign * ny)
                frame *= (1.0 - sh)[..., None]
            alpha = m if (under is None or overlap_alpha >= 1.0) else m * (1.0 - (1.0 - overlap_alpha) * under)
            a3 = alpha[..., None]
            frame = content * a3 + frame * (1.0 - a3)
            under = m if under is None else np.maximum(under, m)
        return frame

    out = []
    for f in range(1, n):
        dmax = max(abs(band(s, f + 1)[0] - band(s, f)[0]) for s in sheets)
        K = int(min(K_MAX, max(1, math.ceil(shutter * dmax / 2.0)))) if shutter > 0 else 1
        if K == 1:
            fr = composite(f)
        else:
            acc = np.zeros((H, W, 3), np.float32)
            for k in range(K):
                acc += composite(f + shutter * (k + 0.5) / K)
            fr = acc / K
        out.append(np.clip(fr, 0, 255).round().astype(np.uint8))
        out_rows.append({"t": round(f / n, 4), "generated": "none (sheets)", "d": [round(band(s, f)[0], 1) for s in sheets],
                         "edge_px": round(dmax, 1), "samples": K,
                         "objects": {ob["name"]: {si: round(object_alpha(ob, si, f), 3) for si in range(len(sheets)) if object_alpha(ob, si, f) > 0} for ob in objs} if objs else None})
        tick(f, 10)
    info = {"frames": len(out), "extent_px": round(E, 1), "crop": cf, "motion": motion, "edge_depth_px": round(edge_depth, 1), "widths_px": [round(band(s, 0)[1], 1) for s in sheets],
            "objects": [{"name": ob["name"], "share": ob["share"], "cover": ob.get("cover")} for ob in objs]}
    return out, info


def apply_breath(frames, eff):
    """A push-in about (cx, cy) (canvas fractions) by 1 + z sin²(πu) over the loop; frame 0 untouched."""
    n = len(frames); H, W = frames[0].shape[:2]
    cx, cy = eff.get("cx", 0.5) * W, eff.get("cy", 0.5) * H
    out = []
    for i, f in enumerate(frames):
        u = i / n
        s = 1 + float(eff["z"]) * math.sin(math.pi * u) ** 2
        if i == 0:
            out.append(f); continue
        M = np.float32([[s, 0, cx * (1 - s)], [0, s, cy * (1 - s)]])
        out.append(cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT))
        if (i + 1) % 10 == 0:
            progress(i + 1, n, "effects")
    return out


def _depth_of_row(row, depths):
    """The frame's depth map: a still's own, or the two stills' maps blended by the in-between's t."""
    if "key" in row:
        return depths[int(row["key"])]
    a, b, t = int(row.get("from", 0)), int(row.get("to", 0)), float(row.get("t", 0.0))
    return (1 - t) * depths[a] + t * depths[b]


def _wave(shape, u):
    return math.sin(2 * math.pi * u) if shape == "sin" else math.sin(math.pi * u) ** 2


def apply_camera(frames, rows, effects, src, draft_scale=1.0):
    """One remap per frame composing `breath` (a push-in about (cx, cy) by 1 + z sin²(πu)) and `parallax` (a sway by
    depth: a pixel at relative depth d moves by amp·W·(d − ref)·wave(u) along `dir`, plus an optional second axis
    `dir2` with its own `shape2` and `amp2` share; the plane at depth `ref` (or the depth read at `ref_at`) stays put;
    the maps are the stills' `depth_k<i>.npy` blended by the frame's t). A breath with `depth_k` above 0 pushes in by depth
    (a dolly: the zoom at a pixel is z · (1 + depth_k · clip(d − ref, ±`depth_clip`)), so near content grows more than the
    reference plane and far content less). Frame 0 is untouched (the seam is a still)."""
    n = len(frames); H, W = frames[0].shape[:2]
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    br = [e for e in effects if e["kind"] == "breath"]
    px = [e for e in effects if e["kind"] == "parallax"]
    bd = br and float(br[0].get("depth_k", 0.0)) > 0
    depths = None
    if px or bd:
        depths = {}
        for p in sorted(Path(src).glob("depth_k*.npy")):
            D = np.load(p).astype(np.float32)
            if D.shape != (H, W):
                D = cv2.resize(D, (W, H), interpolation=cv2.INTER_LINEAR)
            sigma = float((px[0] if px else br[0]).get("sigma", 3.0))        # a breath by depth without a parallax reads its own sigma
            depths[int(p.stem[7:])] = cv2.GaussianBlur(D, (0, 0), sigma * draft_scale)
        assert depths, f"depth effects: no depth_k*.npy under {src} (prep --bg-depth writes them)"
        e = px[0] if px else br[0]
        if "ref_at" in e:
            fx, fy = e["ref_at"]; ref = float(depths[0][int(fy * H), int(fx * W)])
        else:
            ref = float(e.get("ref", 0.0))
        e["_ref_depth"] = round(ref, 4)
        if px:
            log(f"camera: parallax amp {e['amp']} of W ({e['amp'] * W:.1f} px at depth distance 1), reference depth {ref:.3f}")
        if bd:
            log(f"camera: breath by depth: z {br[0]['z']} × (1 + {br[0]['depth_k']} × clip(d − {ref:.3f}, ±{br[0].get('depth_clip', 0.6)}))")
    out = [frames[0]]
    for i in range(1, n):
        u = i / n
        mx, my = xs.copy(), ys.copy()
        if br:
            e = br[0]; cx, cy = e.get("cx", 0.5) * W, e.get("cy", 0.5) * H
            sc = 1 + float(e["z"]) * math.sin(math.pi * u) ** 2
            if bd:
                c = float(e.get("depth_clip", 0.6))
                sc = 1 + (sc - 1) * (1 + float(e["depth_k"]) * np.clip(_depth_of_row(rows[i], depths) - ref, -c, c))
            mx = cx + (mx - cx) / sc; my = cy + (my - cy) / sc
        if px:
            e = px[0]; D = _depth_of_row(rows[i], depths)
            d1 = np.float32(e.get("dir", [1, 0])); d1 /= max(1e-6, float(np.hypot(*d1)))
            disp = e["amp"] * W * _wave(e.get("shape", "sin"), u) * d1
            if "dir2" in e:
                d2 = np.float32(e["dir2"]); d2 /= max(1e-6, float(np.hypot(*d2)))
                disp = disp + e["amp"] * W * float(e.get("amp2", 0.5)) * _wave(e.get("shape2", "pulse"), u) * d2
            rel = (D - ref)
            mx = mx - disp[0] * rel; my = my - disp[1] * rel
        out.append(cv2.remap(frames[i], mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT))
        if (i + 1) % 10 == 0:
            progress(i + 1, n, "effects")
    return out


def apply_glow(frames, eff, draft_scale=1.0):
    """A light source breathing: the frame's bright pixels (above `thr`, inside `box` in canvas fractions) blurred at
    two radii (`sigma`, fractions of W; `mix` their shares) are added back at `gain`·wave(u) (a bloom; luminance only,
    no pixel moves). Frame 0 untouched."""
    n = len(frames); H, W = frames[0].shape[:2]
    x0, y0, x1, y1 = [int(round(v * (W if k % 2 == 0 else H))) for k, v in enumerate(eff.get("box", [0, 0, 1, 1]))]
    thr = float(eff.get("thr", 235)); sig = [float(v) * W for v in eff.get("sigma", [0.012, 0.05])]; mix = eff.get("mix", [0.6, 0.4])
    out = [frames[0]]
    for i in range(1, n):
        g = float(eff.get("gain", 0.15)) * _wave(eff.get("shape", "pulse"), i / n)
        f = frames[i].astype(np.float32)
        m = np.zeros((H, W), np.float32); sub = f[y0:y1, x0:x1]
        m[y0:y1, x0:x1] = (sub.max(2) > thr).astype(np.float32)
        light = f * m[..., None]
        bloom = sum(w * cv2.GaussianBlur(light, (0, 0), s) for w, s in zip(mix, sig))
        out.append(np.clip(f + g * bloom, 0, 255).round().astype(np.uint8))
        if (i + 1) % 10 == 0:
            progress(i + 1, n, "effects")
    return out


def render_plan(plan, out, fps, draft=0, frames_jpg=False):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    src = ROOT / plan["in"]
    keys = {}
    for p in sorted(src.glob("k*.png")):
        im = cv2.imread(str(p))
        if draft:
            im = _scale_to(im, draft)
            im = im[:im.shape[0] & ~1, :im.shape[1] & ~1]      # yuv420p needs even sides
        keys[int(p.stem[1:])] = im
    H, W = keys[0].shape[:2]
    matte_cfg = plan.get("matte", {})
    matte_kw = {k: v for k, v in matte_cfg.items() if k != "all"}    # `all` is read by `rife` only; the other methods take the change matte's keys
    frames, rows = [], []
    cur = None
    t_render = time.time()
    _PROG.update(i=0, n=sum(int(st.get("hold", 1)) if "key" in st else int(st.get("n", 0)) for st in plan["timeline"]))
    for si, step in enumerate(plan["timeline"]):
        if "key" in step:
            k = int(step["key"])
            for _ in range(int(step.get("hold", 1))):
                frames.append(keys[k]); rows.append({"step": si, "key": k, "generated": "none (photo)"})
            cur = k
            _PROG["i"] = len(frames)
            continue
        j = int(step["to"]); n = int(step.get("n", 0)); method = step.get("method", "rife"); ease = step.get("ease", "smooth")
        A, B = keys[cur], keys[j]
        seg_rows = []
        if method == "sheets":
            assert j == cur, "sheets: the step returns to the base still (`to` = the current key)"
            step["_crop"] = float(plan.get("crop", 1.0))
            fr, info = frames_sheets(keys, cur, step, seg_rows, src); log(f"render: sheets {info}")
        elif method == "slices":
            knots = [cur] + [int(k) for k in step.get("through", [])] + [j]
            fr, info = frames_slices(keys, knots, step, seg_rows); step["n"] = len(fr); log(f"render: slices {info}")
        elif "through" in step:
            knots = [cur] + [int(k) for k in step["through"]] + [j]
            fr = frames_chain(keys, knots, n, step.get("weights"), ease, float(step.get("soft", 0.0)), method, matte_kw, seg_rows, margin=float(step.get("knot_margin", 0.0)))
        elif method == "rife":
            fr, _ = frames_rife(A, B, n, ease, matte_cfg, seg_rows, step)
        elif method == "dissolve":
            fr = frames_dissolve(A, B, n, ease, seg_rows)
        elif method == "morph":
            fr = frames_morph(A, B, n, ease, fps, step, seg_rows)
        elif method == "teleport":
            fr, _ = frames_teleport(A, B, n, ease, step, matte_kw, seg_rows)
        elif method == "slide":
            fr, info = frames_slide(A, B, n, ease, step, matte_kw, seg_rows); log(f"render: slide {info}")
        elif method == "rise":
            fr, info = frames_rise(A, B, n, ease, step, matte_kw, seg_rows); log(f"render: rise {info}")
        elif method == "snap":
            fr = frames_snap(A, B, n, step, seg_rows)
        elif method == "cut":
            fr = []
        elif method == "rewind":
            stride = int(step.get("stride", 3))
            back = frames[int(step.get("from", 0)):][::-1][stride::stride]
            fr = [f for f in back]
            seg_rows = [{"generated": "none (rewind)"} for _ in fr]
            replan(step.get("n", 0), len(fr))
        else:
            sys.exit(f"unknown method {method}")
        for r in seg_rows:
            r.update({"step": si, "from": cur, "to": j, "method": method})
        frames.extend(fr); rows.extend(seg_rows)
        _PROG["i"] = len(frames)
        log(f"render: step {si} {cur}->{j} {method} n {len(fr)} ({time.time() - t_render:.0f} s so far)")
        cur = j
    effects = plan.get("effects", [])
    kinds = [e["kind"] for e in effects]
    unknown = [k for k in kinds if k not in ("breath", "parallax", "glow")]
    if unknown:
        sys.exit(f"unknown effect {unknown[0]}")
    draft_scale = W / float(json.loads((src / "prep.json").read_text())["canvas"][0]) if (src / "prep.json").exists() else 1.0
    breath_by_depth = any(e["kind"] == "breath" and float(e.get("depth_k", 0.0)) > 0 for e in effects)
    if "parallax" in kinds or breath_by_depth:
        frames = apply_camera(frames, rows, effects, src, draft_scale)     # breath and parallax in one remap (a breath by depth needs the maps too)
    elif "breath" in kinds:
        frames = apply_breath(frames, [e for e in effects if e["kind"] == "breath"][0])
    for eff in effects:
        if eff["kind"] == "glow":
            frames = apply_glow(frames, eff, draft_scale)
    if plan.get("crop"):                                             # the centre `crop` of the canvas (a fraction), even sides
        cf = float(plan["crop"]); cw, ch = int(round(W * cf)) & ~1, int(round(H * cf)) & ~1
        x0, y0 = (W - cw) // 2, (H - ch) // 2
        frames = [np.ascontiguousarray(f[y0:y0 + ch, x0:x0 + cw]) for f in frames]
        log(f"render: crop {cf} -> {cw}x{ch} at ({x0}, {y0})")
        W, H = cw, ch
    render_s = round(time.time() - t_render, 1)
    N = len(frames)
    # the mp4 and the gif
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    mp4 = out / "loop.mp4"
    progress(0, N, "encode")
    cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
           "-an", "-c:v", "libx264", "-preset", "medium", "-crf", str(plan.get("crf", 14)), "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", str(mp4)]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in frames:
        pr.stdin.write(np.ascontiguousarray(f).tobytes())
    pr.stdin.close(); assert pr.wait() == 0, "ffmpeg mp4 failed"
    gl = int(plan.get("gif_long", 540)); gs = gl / max(W, H)
    gw, gh = int(round(W * gs)) & ~1, int(round(H * gs)) & ~1
    gif = out / "loop.gif"
    cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{gw}x{gh}", "-r", str(fps), "-i", "-",
           "-filter_complex", "[0:v]split[a][b];[a]palettegen=max_colors=255:stats_mode=full[p];[b][p]paletteuse=dither=sierra2_4a",
           "-loop", "0", str(gif)]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in frames:
        pr.stdin.write(np.ascontiguousarray(cv2.resize(f, (gw, gh), interpolation=cv2.INTER_AREA)).tobytes())
    pr.stdin.close(); assert pr.wait() == 0, "ffmpeg gif failed"
    progress(N, N, "encode")
    # the sheet: every frame when short, else every 2nd, 8 per row
    every = 1 if N <= 48 else 2
    sel = list(range(0, N, every)); sc = 240 / W
    th = []
    for i in sel:
        t = cv2.resize(frames[i], None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
        lab = f"{i}" + ("" if rows[i]["generated"].startswith("none") else " g")
        cv2.putText(t, lab, (4, 18), 0, 0.55, (0, 0, 255), 2)
        th.append(t)
    while len(th) % 8:
        th.append(np.zeros_like(th[0]))
    sheet = np.vstack([np.hstack(th[i:i + 8]) for i in range(0, len(th), 8)])
    cv2.imwrite(str(out / "sheet.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 85])
    # measures on the decoded mp4 (`measures_of`, shared with the `measure` command; the keys keep their order)
    dec = decode_mp4(mp4)
    meas = {"frames": N, "fps": fps, "canvas": [W, H], "seconds": round(N / fps, 3), "render_s": render_s}
    meas.update(measures_of(dec, rows, N))
    meas.update({"md5_mp4": md5(mp4), "md5_gif": md5(gif), "gif_bytes": gif.stat().st_size, "mp4_bytes": mp4.stat().st_size,
                 "draft": draft, "plan_sha256": hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()[:16],
                 "script_md5": md5(Path(__file__)), "rife_version": _rife_version()})
    (out / "frames.json").write_text(json.dumps(rows, indent=0))
    (out / "measure.json").write_text(json.dumps(meas, indent=1))
    (out / "plan.json").write_text(json.dumps(plan, indent=1))
    if frames_jpg:                                                  # `--frames`: the decoded mp4's frames, for a scrubber by index
        fd = out / "frames"; fd.mkdir(exist_ok=True)
        for p in fd.glob("f*.jpg"):                                 # a shorter re-render into the same folder leaves no stale frame
            p.unlink()
        for i, f in enumerate(dec):
            cv2.imwrite(str(fd / f"f{i:04d}.jpg"), f, [cv2.IMWRITE_JPEG_QUALITY, 90])
    progress(len(dec), N, "measure")
    print(json.dumps({k: meas[k] for k in ("frames", "seconds", "canvas", "render_s", "step_mean", "step_max", "step_max_at", "seam_step",
                                            "faces_keyframes", "generated_share", "dexp_max", "md5_mp4", "gif_bytes")}))
    return meas


def cmd_render(args):
    plan = json.loads(Path(args.plan).read_text())
    for kv in args.set or []:
        k, v = kv.split("=", 1); plan[k] = json.loads(v)
    _PROG["on"] = bool(args.progress)
    render_plan(plan, args.out, args.fps, args.draft, frames_jpg=bool(args.frames))


# ------------------------------------------------------------------ measure: the render's measures on any decoded mp4 (2026-11-05, the studio)

def decode_mp4(mp4):
    """Every frame of an mp4 as decoded by OpenCV (BGR uint8), in order."""
    cap = cv2.VideoCapture(str(mp4)); dec = []
    while True:
        ok, f = cap.read()
        if not ok: break
        dec.append(f)
    return dec


def measures_of(dec, rows=None, n=None):
    """The measures `render` writes into measure.json, on decoded frames, in the render's key order: the step series (the
    mean absolute difference of neighbouring frames, 0..255), its mean, max and argmax, the seam step (last frame to the
    first), YuNet faces per frame; with `rows` (frames.json: what each frame is) also the face counts on the stills' frames,
    the generated frames and their share of `n` frames (default the decoded count), the largest double-exposure share
    recorded for a generated frame, and the mean RIFE seconds per in-between. Without `rows` those keys are null."""
    steps = [float(np.mean(cv2.absdiff(dec[i + 1], dec[i]))) for i in range(len(dec) - 1)]
    seam = float(np.mean(cv2.absdiff(dec[-1], dec[0])))
    faces = []
    try:
        import rife_probe as R
        faces = [len(R.faces_of(f)) for f in dec]
    except SystemExit:
        pass
    m = {"step_mean": round(float(np.mean(steps)), 3), "step_max": round(max(steps), 3), "step_max_at": int(np.argmax(steps)),
         "seam_step": round(seam, 3), "steps": [round(x, 2) for x in steps],
         "faces_per_frame": faces, "faces_keyframes": sorted(set(faces[i] for i, r in enumerate(rows) if "key" in r)) if faces and rows is not None else None}
    if rows is None:
        m.update({"generated_frames": None, "generated_share": None, "dexp_max": None, "rife_seconds_per_frame": None})
        return m
    N = len(dec) if n is None else n
    gen = [r for r in rows if not r["generated"].startswith("none")]
    m.update({"generated_frames": len(gen), "generated_share": round(len(gen) / N, 3),
              "dexp_max": max([r.get("dexp", r.get("dexp_rest", 0.0)) for r in gen], default=0.0),
              "rife_seconds_per_frame": round(float(np.mean([r["seconds"] for r in gen if "seconds" in r])), 2) if any("seconds" in r for r in gen) else None})
    return m


def window_series(dec, ref, wins, margin):
    """Per named window (px of the clip): frame `ref`'s window content found in every decoded frame by `_window_shift`
    (template match inside the window grown by `margin` px, sub-pixel by a parabola) as [dx, dy, corr]; and per window
    the largest |dx| and |dy| with the frames where they occur, the lowest correlation, and the frames whose peak lay on
    the search's border (`edge_frames`: there the offset is a bound, not a measurement)."""
    series, summary = {}, {}
    for name, box in wins.items():
        s = [_shift_edge(dec[ref], f, box, margin) for f in dec]
        series[name] = [[round(dx, 2), round(dy, 2), round(c, 3)] for dx, dy, c, _ in s]
        adx = [abs(v[0]) for v in s]; ady = [abs(v[1]) for v in s]
        summary[name] = {"box": list(box), "dx_max": round(max(adx), 2), "dx_max_at": int(np.argmax(adx)),
                         "dy_max": round(max(ady), 2), "dy_max_at": int(np.argmax(ady)), "corr_min": round(min(v[2] for v in s), 3),
                         "edge_frames": [k for k, v in enumerate(s) if v[3]]}
    return series, summary


def cmd_measure(args):
    """The measures of `render` on any mp4, without rendering: `measures_of` on the decoded frames, plus per --window the
    window's offset against frame --ref in every frame (an object's stability)."""
    mp4 = Path(args.mp4)
    if not mp4.is_file():
        fail(f"measure: no mp4 at {mp4}")
    wins = parse_windows(args.window, "measure --window") if args.window else {}
    rows = None
    if args.frames_json:
        fj = Path(args.frames_json)
        if not fj.is_file():
            fail(f"measure --frames-json: no file at {fj}")
        rows = json.loads(fj.read_text())
    dec = decode_mp4(mp4)
    if len(dec) < 2:
        fail(f"measure: {mp4} decodes to {len(dec)} frames; the measures need 2 or more")
    if rows is not None and len(rows) != len(dec):
        fail(f"measure --frames-json: {len(rows)} rows for {len(dec)} decoded frames (not this mp4's frames.json)")
    if not 0 <= args.ref < len(dec):
        fail(f"measure --ref: no frame {args.ref} in {len(dec)} decoded frames")
    H, W = dec[0].shape[:2]
    if wins:
        check_boxes(wins, W, H, "measure --window", "the clip")
    cap = cv2.VideoCapture(str(mp4)); fps = float(cap.get(cv2.CAP_PROP_FPS)); cap.release()
    fps = int(round(fps)) if abs(fps - round(fps)) < 0.01 else round(fps, 3)
    meas = {"mp4": str(mp4), "frames_json": str(args.frames_json) if args.frames_json else None,
            "frames": len(dec), "fps": fps, "canvas": [W, H], "seconds": round(len(dec) / fps, 3) if fps else None}
    meas.update(measures_of(dec, rows))
    meas["md5_mp4"] = md5(mp4)
    if wins:
        meas["stability_ref"] = args.ref
        meas["stability_margin"] = args.margin
        meas["stability"], meas["stability_max"] = window_series(dec, args.ref, wins, args.margin)
        for name, s in meas["stability_max"].items():
            log(f"measure: window {name} {s['box']} against frame {args.ref}: at most {s['dx_max']:.2f} px sideways (frame {s['dx_max_at']}) "
                f"and {s['dy_max']:.2f} px vertically (frame {s['dy_max_at']}); correlation at least {s['corr_min']:.3f}")
    meas["script_md5"] = md5(Path(__file__))
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out / "measure.json").write_text(json.dumps(meas, indent=1))
    print(json.dumps({k: meas.get(k) for k in ("frames", "seconds", "canvas", "step_mean", "step_max", "step_max_at", "seam_step",
                                               "faces_keyframes", "generated_share", "dexp_max", "md5_mp4", "stability_max")}))


# ------------------------------------------------------------------ readers: what each still holds, beside the prep (2026-11-04, the studio)

def _lab_distance(A, B):
    """The per-pixel Lab distance between two stills on 2 px blurred copies: the measure `change_matte` thresholds."""
    la = cv2.cvtColor(cv2.GaussianBlur(A, (0, 0), 2), cv2.COLOR_BGR2LAB).astype(np.float32)
    lb = cv2.cvtColor(cv2.GaussianBlur(B, (0, 0), 2), cv2.COLOR_BGR2LAB).astype(np.float32)
    return np.linalg.norm(la - lb, axis=2)


def cmd_readers(args):
    """Per still of a prep folder: the size, the YuNet faces, the depth map and its range, the exposure and focus
    statistics; per neighbouring pair the Lab-difference shares. A missing depth_k<i>.npy is computed by the depth model
    (offline) and saved into the prep folder as prep saves it, so a later plan's depth effects find it."""
    import rife_probe as R
    src = Path(args.prep_dir)
    out = Path(args.out) if args.out else src / "readers"
    stills = sorted((int(p.stem[1:]), p) for p in src.glob("k*.png") if p.stem[1:].isdigit())
    if not stills:
        sys.exit(f"{src}: no k<i>.png (loop_seq.py prep writes them)")
    if not R.FACE_MODEL.exists():
        sys.exit(f"refuse: no YuNet model at {R.FACE_MODEL}")
    out.mkdir(parents=True, exist_ok=True)
    entries, imgs = [], []
    for i, p in stills:
        bgr = cv2.imread(str(p)); H, W = bgr.shape[:2]
        faces = [[int(f[0]), int(f[1]), int(f[2]), int(f[3]), round(float(f[14]), 3)] for f in R.faces_of(bgr)]
        dp = src / f"depth_k{i}.npy"
        if dp.exists():
            D = np.load(dp); how = "read"
        else:
            import transitions as T
            D = T.model_disparity(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
            np.save(str(dp), D); how = "missing: computed by the depth model and saved into the prep folder"
        lo, hi = float(D.min()), float(D.max())
        cv2.imwrite(str(out / f"depth_k{i}.jpg"), np.round((D - lo) / max(hi - lo, 1e-6) * 255).astype(np.uint8),
                    [cv2.IMWRITE_JPEG_QUALITY, 90])
        g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        e = {"still": p.name, "size": [W, H], "faces": faces, "depth": dp.name,
             "depth_stats": {"min": round(lo, 3), "max": round(hi, 3), "mean": round(float(D.mean()), 3)},
             "mean_level": round(float(g.mean()), 1), "clipped_high_px": int((g > 250).sum()), "clipped_low_px": int((g < 5).sum()),
             "laplacian_var": round(float(cv2.Laplacian(g, cv2.CV_64F).var()), 1)}
        entries.append(e); imgs.append(bgr)
        log(f"readers: {p.name} {W}x{H}: {len(faces)} faces; {dp.name} {how} (mean {e['depth_stats']['mean']}); grey mean "
            f"{e['mean_level']}, clipped {e['clipped_high_px']} high / {e['clipped_low_px']} low px; Laplacian variance {e['laplacian_var']}")
    pairs = []
    for (ia, pa), (ib, pb), A, B in zip(stills, stills[1:], imgs, imgs[1:]):
        if A.shape != B.shape:
            sys.exit(f"readers: {pa.name} ({A.shape[1]}x{A.shape[0]}) and {pb.name} ({B.shape[1]}x{B.shape[0]}) differ in size: not one prep canvas")
        d = _lab_distance(A, B)
        pairs.append({"a": ia, "b": ib, "lab_above_14": round(float((d > 14).mean()), 4), "lab_above_30": round(float((d > 30).mean()), 4)})
        log(f"readers: k{ia}-k{ib}: the Lab distance is above 14 on {pairs[-1]['lab_above_14']:.4f} of the pixels, above 30 on {pairs[-1]['lab_above_30']:.4f}")
    (out / "readers.json").write_text(json.dumps({"prep": str(src), "stills": entries, "pairs": pairs}, indent=1))
    print(json.dumps({"stills": len(entries), "faces": [len(e["faces"]) for e in entries], "lab_above_14": [q["lab_above_14"] for q in pairs]}))


# ------------------------------------------------------------------ probe: the in-between methods side by side, before a plan (2026-11-05, the studio)

PROBE_TS = (0.25, 0.5, 0.75)


def _face_boxes(A, B, grow=0.25):
    """The crop boxes at a pair's faces: YuNet on both stills; a face of A and the nearest face of B (centres closer than
    half the larger side) share one box, their union; an unmatched face has its own; each box grown by `grow` of its
    size on every side and clipped to the still. Sorted left to right."""
    import rife_probe as R
    fa = [[int(v) for v in f[:4]] + [round(float(f[14]), 3)] for f in R.faces_of(A)]
    fb = [[int(v) for v in f[:4]] + [round(float(f[14]), 3)] for f in R.faces_of(B)]
    used, faces = set(), []
    for a in fa:
        best = None
        for k, b in enumerate(fb):
            d = math.hypot(b[0] + b[2] / 2 - a[0] - a[2] / 2, b[1] + b[3] / 2 - a[1] - a[3] / 2)
            if k not in used and d < 0.5 * max(a[2], a[3], b[2], b[3]) and (best is None or d < best[0]):
                best = (d, k)
        if best is not None:
            used.add(best[1])
        faces.append((a, fb[best[1]] if best is not None else None))
    faces += [(None, b) for k, b in enumerate(fb) if k not in used]
    H, W = A.shape[:2]; out = []
    for a, b in faces:
        bs = [x for x in (a, b) if x is not None]
        x0 = min(x[0] for x in bs); y0 = min(x[1] for x in bs); x1 = max(x[0] + x[2] for x in bs); y1 = max(x[1] + x[3] for x in bs)
        gx, gy = grow * (x1 - x0), grow * (y1 - y0)
        out.append({"box": [max(0, int(x0 - gx)), max(0, int(y0 - gy)), min(W, int(math.ceil(x1 + gx))), min(H, int(math.ceil(y1 + gy)))],
                    "a": a, "b": b})
    return sorted(out, key=lambda f: (f["box"][0], f["box"][1]))


def cmd_probe(args):
    """Per pair of registered stills, the in-betweens at t 0.25, 0.5 and 0.75 by RIFE (the whole frame), the DIS morph and
    the plain dissolve: a strip per method, the double-exposure share and the steps to both stills per frame, 1:1 crops at
    the faces. RIFE runs only behind its manifest (offline); without it the RIFE strip is skipped with a log line."""
    import rife_probe as R
    src = Path(args.prep_dir)
    stills = {int(p.stem[1:]): p for p in src.glob("k*.png") if p.stem[1:].isdigit()}
    if len(stills) < 2:
        fail(f"probe: {src} holds {len(stills)} k<i>.png; a probe needs 2 or more (loop_seq.py prep writes them)")
    idx = sorted(stills)
    if args.pairs:
        pairs = []
        for part in args.pairs.split(";"):
            if not part.strip():
                continue
            try:
                i, j = (int(v) for v in part.split(","))
            except ValueError:
                fail(f"probe --pairs: {part.strip()!r} is not i,j")
            if i not in stills or j not in stills or i == j:
                fail(f"probe --pairs: {i},{j} is not a pair of the stills {idx} of {src}")
            pairs.append((i, j))
        if not pairs:
            fail(f"probe --pairs: no pair in {args.pairs!r}")
    else:
        pairs = list(zip(idx, idx[1:]))
    keys = {}
    for i in sorted({k for p in pairs for k in p}):
        im = _scale_to(cv2.imread(str(stills[i])), args.long)
        keys[i] = im[:im.shape[0] & ~1, :im.shape[1] & ~1]          # even sides, as a draft render crops them
    H, W = keys[pairs[0][0]].shape[:2]
    if any(k.shape[:2] != (H, W) for k in keys.values()):
        fail(f"probe: the stills of {src} differ in size: not one prep canvas")
    out = Path(args.out); (out / "crops").mkdir(parents=True, exist_ok=True)
    rife_skip = None if R.MANIFEST.exists() else f"no {R.MANIFEST} (`rife_probe.py warmup` writes it once)"
    if rife_skip:
        log(f"probe: the RIFE strips are skipped: {rife_skip}")
    face_ok = R.FACE_MODEL.exists()
    if not face_ok:
        log(f"probe: no YuNet model at {R.FACE_MODEL}: no face crops")
    t_all = time.time(); rep_pairs = []
    for i, j in pairs:
        A, B = keys[i], keys[j]
        m = change_matte(A, B); ones = np.ones((H, W), np.float32)
        faces = _face_boxes(A, B) if face_ok else []
        for k, f in enumerate(faces):
            x0, y0, x1, y1 = f["box"]
            for name, im in ((f"k{i}", A), (f"k{j}", B)):
                cv2.imwrite(str(out / "crops" / f"{i}_{j}_{name}_face{k}.jpg"), im[y0:y1, x0:x1], [cv2.IMWRITE_JPEG_QUALITY, 92])
        methods = {}
        if rife_skip is None:                    # RIFE over the whole frame, as a `matte: {"all": true}` leg renders it
            try:
                fr, secs = [], []
                for t in PROBE_TS:
                    t0 = time.perf_counter(); fr.append(_RIFE.at(A, B, t)); secs.append(round(time.perf_counter() - t0, 2))
                methods["rife"] = (fr, secs, {})
            except SystemExit as e:              # rife_probe refuses (a weight missing or its sha256 off): skip, never crash
                rife_skip = str(e)
                log(f"probe: the RIFE strips are skipped: {rife_skip}")
        rows = []
        fr = frames_morph(A, B, len(PROBE_TS), "linear", 25, {}, rows)
        methods["morph"] = (fr, None, {"flow": rows[0]["method"]})
        methods["dissolve"] = (frames_dissolve(A, B, len(PROBE_TS), "linear", []), None, {})
        entry = {"a": i, "b": j, "matte_share": round(float((m > 0.5).mean()), 4), "faces": faces, "methods": {}}
        for name, (fr, secs, extra) in methods.items():
            strip = f"probe_{i}_{j}_{name}.jpg"
            tiles, rows_m = [], []
            for n, (X, t) in enumerate(zip(fr, PROBE_TS)):
                r = {"t": t, "dexp": R.dexp_share(X, A, B, m), "dexp_frame": R.dexp_share(X, A, B, ones),
                     "step_a": round(float(np.mean(cv2.absdiff(X, A))), 3), "step_b": round(float(np.mean(cv2.absdiff(X, B))), 3)}
                if secs is not None:
                    r["seconds"] = secs[n]
                r["crops"] = []
                for k, f in enumerate(faces):
                    x0, y0, x1, y1 = f["box"]
                    c = f"crops/{i}_{j}_{name}_t{t:g}_face{k}.jpg"
                    cv2.imwrite(str(out / c), X[y0:y1, x0:x1], [cv2.IMWRITE_JPEG_QUALITY, 92])
                    r["crops"].append(c)
                rows_m.append(r)
                tl = X.copy(); _label(tl, f"{name} t {t:g}", (10, 30), 0.9)
                tiles.append(tl)
            gap = np.full((H, 6, 3), 24, np.uint8)
            cv2.imwrite(str(out / strip), np.hstack([x for q in tiles for x in (q, gap)][:-1]), [cv2.IMWRITE_JPEG_QUALITY, 88])
            entry["methods"][name] = {"strip": strip, **extra, "frames": rows_m}
            log(f"probe: k{i}-k{j} {name}: double exposure " + ", ".join(f"{r['dexp']:.4f}" for r in rows_m)
                + " (inside the change matte), " + ", ".join(f"{r['dexp_frame']:.4f}" for r in rows_m) + " (the whole frame)")
        rep_pairs.append(entry)
    rep = {"prep": str(src), "long": args.long, "size": [W, H], "t": list(PROBE_TS),
           "matte": dict(zip(("thr", "grow", "feather", "min_share"), change_matte.__defaults__)), "rife_version": _rife_version(), "rife_skipped": rife_skip,
           "faces_model": face_ok, "pairs": rep_pairs, "seconds": round(time.time() - t_all, 1), "script_md5": md5(Path(__file__))}
    (out / "probe.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps({"pairs": [[p["a"], p["b"]] for p in rep_pairs], "size": [W, H], "rife_skipped": rife_skip,
                      "dexp": {name: [min(v), max(v)] for name in ("rife", "morph", "dissolve")
                               for v in [[r["dexp"] for p in rep_pairs if name in p["methods"] for r in p["methods"][name]["frames"]]] if v}}))


# ------------------------------------------------------------------ page: the review page

def _esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _keys_strip(seq_in, out_jpg, long=360):
    ks = sorted(seq_in.glob("k*.png"))
    tiles = []
    for k in ks:
        im = _scale_to(cv2.imread(str(k)), long)
        cv2.putText(im, k.stem, (6, 22), 0, 0.7, (0, 255, 255), 2)
        tiles.append(im)
    H = max(t.shape[0] for t in tiles); W = sum(t.shape[1] for t in tiles) + 6 * (len(tiles) - 1)
    strip = np.full((H, W, 3), 24, np.uint8); x = 0
    for t in tiles:
        strip[:t.shape[0], x:x + t.shape[1]] = t; x += t.shape[1] + 6
    cv2.imwrite(str(out_jpg), strip, [cv2.IMWRITE_JPEG_QUALITY, 82])
    return len(ks)


def _timeline_text(plan):
    parts = []
    for st in plan["timeline"]:
        if "key" in st:
            parts.append(f"k{st['key']} ×{st.get('hold', 1)}")
        else:
            parts.append(f"→k{st['to']} {st.get('method', 'rife')} n{st.get('n', 0)} {st.get('ease', 'smooth')}")
    eff = ", ".join(f"{e['kind']} {e.get('z', e.get('amp', e.get('gain', '')))}" for e in plan.get("effects", []))
    return " · ".join(parts) + (f" · effects: {eff}" if eff else " · no effects")


def cmd_page(args):
    root = Path(args.root)
    notes = json.loads(Path(args.notes).read_text()) if args.notes and Path(args.notes).exists() else {}
    order = args.order.split(",") if args.order else sorted(p.name for p in root.iterdir() if p.is_dir() and p.name not in ("in", "probe_morph", "probe_rife", "agents"))
    names = None
    if args.variants:                          # `--variants a,b` (2026-11-05): only these full renders, in this order, for every sequence
        names = [v.strip() for v in args.variants.split(",") if v.strip()]
        if not names:
            fail(f"page --variants: no name in {args.variants!r}")
        for n in names:
            if names.count(n) > 1:
                fail(f"page --variants: {n} is named twice")
        for seq in order:                      # checked before anything is written
            for n in names:
                if not (root / seq / n / "measure.json").is_file():
                    fail(f"page --variants: {n} is not a full render of {seq}: no {root / seq / n / 'measure.json'}")
    css = """:root{--bg:#fafaf8;--fg:#1b1b1b;--mut:#666;--card:#fff;--line:#ddd}
@media (prefers-color-scheme:dark){:root{--bg:#141414;--fg:#eee;--mut:#aaa;--card:#1e1e1e;--line:#333}}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0;padding:16px;max-width:1500px;margin:auto}
.c{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px;margin:18px 0}
.m{display:flex;gap:14px;flex-wrap:wrap;align-items:flex-start}video{max-height:560px;max-width:100%}img.g{max-height:560px;max-width:100%}
img.k{max-width:100%;height:auto}td,th{padding:2px 10px 2px 0;text-align:left;font-variant-numeric:tabular-nums;vertical-align:top}
p.mut{color:var(--mut)}code{font-size:13px}h2{margin:4px 0 6px}h3{margin:10px 0 4px;font-size:15px}.v{border-top:1px dashed var(--line);padding-top:8px;margin-top:8px}"""
    h = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
         f"<title>{_esc(args.title)}</title><style>{css}</style></head><body>"]
    h.append(f"<h1>{_esc(args.title)}</h1>")
    h.append(f"<p class='mut'>{_esc(args.intro)}</p>")
    for seq in order:
        d = root / seq
        if names is None:
            variants = sorted(v for v in d.iterdir() if v.is_dir() and (v / "measure.json").exists())
        else:
            variants = [d / n for n in names]
        if not variants:
            continue
        inp = root / "in" / seq
        prep = json.loads((inp / "prep.json").read_text())
        nk = _keys_strip(inp, inp / "keys.jpg")
        plan0 = json.loads((variants[0] / "plan.json").read_text())
        h.append(f"<section class='c' id='{_esc(seq)}'><h2>{_esc(seq)}</h2><p><b>The gag.</b> {_esc(plan0.get('gag', ''))}</p>")
        reg = "; ".join(f"k{i}: {_esc(r['method'])}" + (f" ({r['inliers']} inliers)" if r.get("inliers") else (f" (cc {r['cc']})" if r.get("cc") else "")) for i, r in enumerate(prep["frames"]))
        h.append(f"<p class='mut'>{nk} stills, registered onto frame {prep['reference']}'s background and cropped to the common area {prep['canvas'][0]}×{prep['canvas'][1]}: {reg}. Cuts: {prep.get('cuts', [])}.</p>")
        h.append(f"<img class='k' src='in/{_esc(seq)}/keys.jpg' alt='keyframes of {_esc(seq)}'>")
        for v in variants:
            m = json.loads((v / "measure.json").read_text()); plan = json.loads((v / "plan.json").read_text())
            rel = f"{seq}/{v.name}"
            h.append(f"<div class='v'><h3>{_esc(v.name)}: {_esc(plan.get('title', ''))}</h3>")
            h.append(f"<p class='mut'>Timeline: {_esc(_timeline_text(plan))}</p>")
            note = notes.get(seq, {}).get(v.name) or notes.get(seq, {}).get("*")
            if note:
                h.append(f"<p><b>What to look at.</b> {_esc(note)}</p>")
            h.append(f"<div class='m'><video src='{rel}/loop.mp4' autoplay loop muted playsinline controls></video><img class='g' src='{rel}/loop.gif' alt='{_esc(seq)} {_esc(v.name)} gif'></div>")
            fk = m.get("faces_keyframes"); fp = m.get("faces_per_frame") or []
            h.append("<table><tr><th>frames</th><th>s</th><th>canvas</th><th>generated frames</th><th>double exposure max</th><th>step mean / max (at)</th><th>seam step</th><th>faces: keys / min–max</th><th>render s</th><th>gif</th><th>md5 mp4</th></tr>"
                     f"<tr><td>{m['frames']}</td><td>{m['seconds']}</td><td>{m['canvas'][0]}×{m['canvas'][1]}</td><td>{m['generated_frames']} ({m['generated_share']:.0%})</td>"
                     f"<td>{m['dexp_max']:.3f}</td><td>{m['step_mean']} / {m['step_max']} ({m['step_max_at']})</td><td>{m['seam_step']}</td>"
                     f"<td>{fk} / {min(fp) if fp else '-'}–{max(fp) if fp else '-'}</td><td>{m['render_s']}</td><td>{m['gif_bytes'] / 1e6:.1f} MB</td><td><code>{m['md5_mp4'][:8]}</code></td></tr></table>")
            h.append(f"<p class='mut'><a href='{rel}/sheet.jpg'>contact sheet</a> (a red <b>g</b> marks a generated frame) · <a href='{rel}/measure.json'>measure.json</a> · <a href='{rel}/plan.json'>plan.json</a></p></div>")
        h.append("</section>")
    h.append(f"<p class='mut'>{_esc(args.footer)}</p></body></html>")
    out = Path(args.out); out.write_text("\n".join(h))
    print(json.dumps({"page": str(out), "md5": md5(out), "sequences": order}))


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("prep"); p.add_argument("seq_dir"); p.add_argument("--out", required=True)
    p.add_argument("--long", type=int, default=1920); p.add_argument("--ref", type=int, default=-1, help="the canvas frame (default: the widest trusted framing, so nothing is upscaled)")
    p.add_argument("--cut", default="", help="frame indices joined by a cut, not registered (e.g. 4,5)")
    p.add_argument("--bg-depth", type=float, default=0.0, help="register on the far field only: keypoints where the depth model's relative depth is below this (0 = off)")
    p.add_argument("--depth-blend", default="", help="with --bg-depth: warp near pixels by a second, all-keypoint fit, blended by the reference frame's depth from the far fit to the near fit over 'lo,hi' (or 'auto': the fits' median inlier depths); a camera parallax between the shots is undone per layer")
    p.add_argument("--min-inliers", type=int, default=MIN_INLIERS, help="the SIFT fit's inlier floor (a far field of a plain wall may hold 30)")
    p.add_argument("--ecc-refine", action="store_true", help="with --bg-depth: refine the far-field fit by a masked ECC on the far pixels")
    p.add_argument("--depth-maps", action="store_true", help="write depth_k<i>.npy (the depth model, offline) for the registered stills even without --bg-depth")
    p.add_argument("--lock-window", default="", help="windows of the reference frame (px, 'x0,y0,x1,y1;...') that must stay put: each map gains the translation that zeroes their mean measured offset (the gag object as the anchor)")
    p.add_argument("--windows", default="", help="named windows of frame 0 (px before the crop, as --lock-window: 'name:x0,y0,x1,y1;...'), "
                   "measured, never applied: per registered frame, where each window's content sits under every fit the prep made "
                   "(dx, dy px, sub-pixel, the template match's correlation, and edge when the peak lies on the ±30 px search's "
                   "border; fits all, far, chain, ecc and final), written to prep.json frames[i].windows and drawn on "
                   "OUT/windows.jpg (arrows 8 times the offset); without it prep.json is unchanged")
    p.set_defaults(fn=cmd_prep)
    p = sp.add_parser("render"); p.add_argument("plan"); p.add_argument("--out", required=True)
    p.add_argument("--fps", type=int, default=25); p.add_argument("--draft", type=int, default=0, help="render at this long edge (0 = the prep canvas)")
    p.add_argument("--set", action="append", help="override a top-level plan key: key=<json>")
    p.add_argument("--progress", action="store_true", help="print `PROGRESS i n phase` lines on stderr: frames (i of the planned total, an "
                   "estimate), effects, encode, measure; without the flag stderr is unchanged")
    p.add_argument("--frames", action="store_true", help="also write OUT/frames/f0000.jpg, f0001.jpg, ... (JPEG quality 90): the decoded "
                   "mp4's frames, after the measures; older f*.jpg there are removed first")
    p.set_defaults(fn=cmd_render)
    p = sp.add_parser("readers", description="Per still of a prep folder (k<i>.png): the size, the YuNet face boxes, the depth model's map "
                      "(the prep folder's depth_k<i>.npy, computed and saved there only when missing), its min, max and mean, the grey "
                      "mean, the counts of grey pixels above 250 and below 5, and the variance of the grey still's Laplacian; per "
                      "neighbouring pair the shares of pixels whose Lab distance on 2 px blurred copies is above 14 and above 30. "
                      "Writes readers.json and depth_k<i>.jpg (the map stretched min..max) into --out, and a one-line summary on stdout.")
    p.add_argument("prep_dir", help="a folder written by `loop_seq.py prep` (k<i>.png, prep.json)")
    p.add_argument("--out", default="", help="where readers.json and the depth previews go (default PREP_DIR/readers)")
    p.set_defaults(fn=cmd_readers)
    p = sp.add_parser("probe", description="Per pair of registered stills (adjacent by index, or --pairs), the in-betweens at t 0.25, "
                      "0.5 and 0.75 by three methods: RIFE over the whole frame (behind its manifest, offline; skipped with a log "
                      "line when the manifest is missing), the DIS morph (transitions.py's prepare and iter_frames, the morph "
                      "preset's own ease) and the plain dissolve. Writes OUT/probe_<i>_<j>_<method>.jpg (three tiles with their t), "
                      "OUT/crops/ (1:1 crops at the YuNet face boxes of both stills, for the stills and every in-between) and "
                      "OUT/probe.json: per frame the double-exposure share inside the change matte (dexp, the measure of a "
                      "render's frames.json) and over the whole frame (dexp_frame), and the mean absolute step to each still.")
    p.add_argument("prep_dir", help="a folder written by `loop_seq.py prep` (k<i>.png)")
    p.add_argument("--out", required=True, help="where the strips, crops/ and probe.json go")
    p.add_argument("--long", type=int, default=960, help="the long edge the stills are scaled to before the probe (px, downscale "
                   "only, sides made even; default 960: a probe is a look, not a render)")
    p.add_argument("--pairs", default="", help="the pairs to probe, 'i,j;k,l' by still index (default: every adjacent pair)")
    p.set_defaults(fn=cmd_probe)
    p = sp.add_parser("measure", description="The measures `render` writes, on any mp4, without rendering: the step series on "
                      "the decoded frames (mean absolute difference of neighbours, 0..255), its mean, max and argmax, the seam "
                      "step, YuNet faces per frame; with --frames-json the face counts on the stills' frames, the generated "
                      "share and the largest recorded double-exposure share; with --window each window's offset against frame "
                      "--ref in every frame (dx, dy px, sub-pixel, and the correlation). Writes OUT/measure.json and a summary line.")
    p.add_argument("mp4", help="the clip to measure (any mp4 OpenCV decodes)")
    p.add_argument("--out", required=True, help="where measure.json goes")
    p.add_argument("--frames-json", default="", help="the render's frames.json (what each frame is: a still, a blend, a generated "
                   "frame with its double-exposure share); its row count must equal the decoded frame count")
    p.add_argument("--window", default="", help="named windows in the clip's px, 'name:x0,y0,x1,y1;...': each window's content "
                   "of frame --ref found in every frame by template match (an object's stability)")
    p.add_argument("--ref", type=int, default=0, help="the frame the windows are read from (default 0)")
    p.add_argument("--margin", type=int, default=30, help="the template match searches the window grown by this many px on "
                   "every side (default 30, as prep's lock); a frame whose peak lies on the search's border is listed in "
                   "edge_frames, its offset a bound, not a measurement")
    p.set_defaults(fn=cmd_measure)
    p = sp.add_parser("page"); p.add_argument("--root", required=True); p.add_argument("--out", required=True)
    p.add_argument("--notes", default=""); p.add_argument("--order", default=""); p.add_argument("--title", default="Halloween loops")
    p.add_argument("--intro", default=""); p.add_argument("--footer", default="")
    p.add_argument("--variants", default="", help="the full renders to list, 'a2,a3' (folder names under <root>/<seq>/), in this "
                   "order, for every sequence on the page (default: every folder holding measure.json, in name order); a name "
                   "that is not a full render of a sequence is a FAILED exit 2 before anything is written")
    p.set_defaults(fn=cmd_page)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
