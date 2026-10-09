#!/usr/bin/env python3
"""Chain research (2026-10-09, the owner's box photos): several photos of one subject become ONE
continuous transition in ONE frame. Every photo but the last is warped onto the LAST photo's frame
by Reveal's own aligner (reveal.run_alignment: BEFORE = the reference, the strict `reshot` profile,
ECC and the gated residual) and kept in the reference's FULL frame (`--crop none`, the default since
the owner's "do not crop anything"; a pixel no photo covers keeps its last known content: the
previous still's, or for the first still the next still's, or the reference's; `--crop valid` crops
to the rectangle every warped photo covers instead),
then each still is pinned to the last one by a homography (MAGSAC++; `--pin similarity` for 4 DOF)
estimated from SIFT matches in the WALL RING around the two boxes (the changed objects; `--no-anchor`
skips it), and the TR14 `luma` effect (inside the changed-region mask B appears in order of A's
brightness) runs across the consecutive pairs under a single ease over --seconds; then the last photo
holds --hold s. The field between two pinned stills is the mask-held one (`--field hold-dis`: no
camera motion, the DIS residual zeroed inside the feathered mask, so the boxes' content stays put;
`--field hold` is the TR14 `luma` clip's field, the residual scaled by the DIS certainty).
`--variant tool-luma` is the transitions tool's own `luma` preset instead (no field, no mask: the
whole frame of B appears in order of A's brightness, the tool's `luma_mask`), on the pinned stills;
`--variant tool-luma-melt-soft` adds melt-soft's swirl inside the changed-region mask to it.
`--variant draw` (2026-10-09, the owner's "really gradual and elaborate drawing process on those
boxes"): outside the box zone one slow dissolve from the first photo to the last; inside it every
repaint spreads as a soft irregular front (order = the new paint's edge distance, the old paint's
brightness and two scales of noise; width --front), the repaints overlapping in time by --overlap of
a step so no boundary is synchronized across the box; no field, no swirl, no colour path. The zone
is the union of the changed regions eroded --zone-erode px and feathered. On top of the global pin,
each box gets a local pin (`--local-pin sift`, the default since 2026-10-09 evening): SIFT matches
INSIDE the box between the still and the last one (the hardware and the drawing persist through the
repaints; 75-869 inliers per box on the owner's photos) give a similarity, position AND size, applied
to the box's zone and blended over the ring. The box stands in front of the wall, so a locked wall
leaves the box 7-14 px off on two of the photos; this pin sees it. `--local-pin edges` fits the four
outline edges instead (a shadow edge fooled it on photo 3); `--local-pin ring` is the wall-ring
translation of the afternoon; `--no-local-pin` skips it. `--match-light` (on for `draw`) matches every still's Lab mean and spread
over the wall rings to the last still's, so the same drawing does not change brightness between
two photos.
Not part of either tool; imports reveal and transitions (research only, as tr14_variants.py does).
Runs in `.venv`.

  chain_luma.py PHOTO... --out DIR [--seconds 3] [--hold 3] [--lead 0] [--max-long 1920]
                [--mode reshot|loose] [--ease smootherstep|linear] [--variant luma|hold-dis|luma-melt-soft]
                [--size 1080x1350] [--fps 30] [--color 0.7] [--no-anchor] [--pin homography|similarity]
                [--field hold-dis|hold] [--crop none|valid]
Outputs in DIR: aligned/<i>_<name>.jpg (the stills in the common frame, after the pin),
chain.mp4 (and chain_<size>.mp4), strip.jpg (one tile per 0.25 s, labelled), boxes.jpg (the two
boxes and their rings on the first still), report.json: Reveal's metrics per warped photo, the
boxes, the ring drift of every still against the last (dx, dy, response) before and after the
pin, per segment the inliers left between stills, the changed-region share and the largest corner
motion of the leftover homography, and the timeline.
"""
import argparse
import json
import sys
import time
import uuid
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "research"))
import transitions as T  # noqa: E402
import reveal as rv  # noqa: E402  (research only: the two tools never import each other)
import tr14_variants as V  # noqa: E402

import subprocess
import imageio_ffmpeg


class OneKeyframeEncoder(T.FrameEncoder):
    """The tool's encoder with ONE keyframe: libx264's periodic keyframe (every 250 frames) decodes
    1.4 levels off the drifted P-frames before it, a visible pop inside a long hold (seen at frame
    250 of the 9 s draw clip, 2026-10-09)."""

    def __init__(self, path, w, h, fps, n_frames, crf=None):
        self.path = Path(path)
        self.w, self.h = int(w), int(h)
        self.n = 0
        g = str(max(1, int(n_frames)))
        cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{self.w}x{self.h}", "-r", f"{float(fps):g}", "-i", "-",
               "-an", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf if crf is not None else T.TCFG["video_crf"]),
               "-g", g, "-keyint_min", g, "-sc_threshold", "0",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(self.path)]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)


RING_GROW = 0.35          # the ring around a box: its box grown by this fraction of its size
RING_INSET = 10           # px: the box interior blanked that far outside the box too
RANSAC_PX = 3.0


def smootherstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * x * (x * (x * 6.0 - 15.0) + 10.0)


def align_onto(ref_path, path, workdir, mode):
    """Reveal's alignment of PATH onto REF_PATH (B onto A). Returns (A_full, warped_full, valid, metrics)."""
    for m in ((mode,) if mode == "loose" else ("reshot", "loose")):
        job = rv.Job(uuid.uuid4().hex[:16], workdir, m)
        rv.run_alignment(job, str(ref_path), str(path))
        if job.state != "failed":
            break
        print(f"  {Path(path).name}: Reveal {m} refused: {job.error}", flush=True)
    else:
        raise SystemExit(f"{path}: Reveal refused in every mode")
    A, B = job.fullA, job.fullB
    hA, wA = A.shape[:2]
    H = job.H_full / job.H_full[2, 2]
    warped = cv2.warpPerspective(B, H, (wA, hA), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    valid = rv.warp_valid_mask(B.shape, H, (wA, hA))
    if job.flow_work is not None:
        warped = rv.apply_residual(warped, job.flow_work, 1.0)
        valid = (rv.apply_residual(valid, job.flow_work, 1.0) > 200).astype(np.uint8) * 255
    return A, warped, valid, dict(job.metrics, mode=m, residual=job.flow_work is not None)


def find_boxes(S0, S1):
    """The two largest components of the changed region between the first two stills (the repainted objects)."""
    gA, gB = T.gray_of(S0), T.gray_of(S1)
    H, _, _, _ = V.homography_fields(gA, gB)
    mask = V.changed_mask(S0, S1, H)
    n, lab, st, _ = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8), 8)
    comps = sorted(range(1, n), key=lambda i: -st[i, cv2.CC_STAT_AREA])[:2]
    return [tuple(int(v) for v in st[i, :4]) for i in sorted(comps, key=lambda i: st[i, 0])], mask


def ring_mask(shape, boxes):
    """uint8 mask of the wall rings: each box grown by RING_GROW, minus the box itself grown by RING_INSET."""
    h, w = shape
    m = np.zeros((h, w), np.uint8)
    for x, y, bw, bh in boxes:
        gx, gy = int(bw * RING_GROW), int(bh * RING_GROW)
        m[max(0, y - gy):min(h, y + bh + gy), max(0, x - gx):min(w, x + bw + gx)] = 255
    for x, y, bw, bh in boxes:
        m[max(0, y - RING_INSET):min(h, y + bh + RING_INSET), max(0, x - RING_INSET):min(w, x + bw + RING_INSET)] = 0
    return m


def ring_shift(gref, g, box, shape):
    """Phase correlation of the wall ring around one box between two stills -> (dx, dy, response)."""
    h, w = shape
    x, y, bw, bh = box
    gx, gy = int(bw * RING_GROW), int(bh * RING_GROW)
    X0, Y0, X1, Y1 = max(0, x - gx), max(0, y - gy), min(w, x + bw + gx), min(h, y + bh + gy)
    X1, Y1 = X1 - (X1 - X0) % 2, Y1 - (Y1 - Y0) % 2     # an odd window biases phaseCorrelate by 0.5 px
    a, b = gref[Y0:Y1, X0:X1].astype(np.float32).copy(), g[Y0:Y1, X0:X1].astype(np.float32).copy()
    ix0, iy0 = max(0, x - X0 - RING_INSET), max(0, y - Y0 - RING_INSET)
    ix1, iy1 = x - X0 + bw + RING_INSET, y - Y0 + bh + RING_INSET
    for im in (a, b):
        im[iy0:iy1, ix0:ix1] = im.mean()
    win = cv2.createHanningWindow((a.shape[1], a.shape[0]), cv2.CV_32F)
    (dx, dy), r = cv2.phaseCorrelate(a, b, win)
    return round(float(dx), 2), round(float(dy), 2), round(float(r), 3)


def tight_box(mask, box):
    """The dense core of a changed-region component (its bbox may carry a cable or a shadow):
    rows and columns whose coverage is at least half of the largest."""
    x, y, w, h = box
    sub = (mask[y:y + h, x:x + w] > 0)
    rows, cols = sub.sum(1), sub.sum(0)
    ry = np.flatnonzero(rows >= 0.5 * rows.max())
    cx = np.flatnonzero(cols >= 0.5 * cols.max())
    return (x + int(cx[0]), y + int(ry[0]), int(cx[-1] - cx[0] + 1), int(ry[-1] - ry[0] + 1))


def track_edge(gray, axis, lo, hi, b0, b1, min_frac=0.3):
    """The position of the strongest edge across [lo, hi) (columns for axis 'x', rows for 'y'),
    tracked per row (or column) inside the band [b0, b1) and taken as the median; sub-pixel by a
    parabola. None when fewer than min_frac of the rows hold an edge above a fifth of the band's
    strongest."""
    g = cv2.GaussianBlur(gray.astype(np.float32), (0, 0), 1.2)
    if axis == "x":
        sob = np.abs(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3))[b0:b1, lo:hi]
    else:
        sob = np.abs(cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3))[lo:hi, b0:b1].T
    if sob.size == 0:
        return None
    k = np.argmax(sob, axis=1)
    peak = sob[np.arange(sob.shape[0]), k]
    ok = (peak > 0.2 * peak.max()) & (k > 0) & (k < sob.shape[1] - 1)
    if ok.sum() < min_frac * sob.shape[0]:
        return None
    rows = np.flatnonzero(ok)
    kk = k[rows]
    l, c, r = sob[rows, kk - 1], sob[rows, kk], sob[rows, kk + 1]
    sub = np.clip((r - l) / (2.0 * (2.0 * c - l - r) + 1e-9), -0.5, 0.5)
    return float(lo + np.median(kk + sub))


def box_edges(gray, core, ref=None, win=12, search=45):
    """(left, right, top, bottom) of a box's outline. With no reference the edges are searched from
    the core's sides inward by `search` px; with one, within +-win of the reference's edges."""
    x, y, w, h = core
    bx0, bx1 = x + int(0.2 * w), x + int(0.8 * w)
    by0, by1 = y + int(0.2 * h), y + int(0.8 * h)
    H_, W_ = gray.shape
    if ref is None:
        wins = [(max(0, x - 10), x + search), (x + w - search, min(W_, x + w + 10)),
                (max(0, y - 10), y + search), (y + h - search, min(H_, y + h + 10))]
    else:
        wins = [(max(0, int(round(v)) - win), min(W_ if i < 2 else H_, int(round(v)) + win + 1)) for i, v in enumerate(ref)]
    return (track_edge(gray, "x", *wins[0], by0, by1), track_edge(gray, "x", *wins[1], by0, by1),
            track_edge(gray, "y", *wins[2], bx0, bx1), track_edge(gray, "y", *wins[3], bx0, bx1))


def match_light(img, ref, mask):
    """img with its Lab mean and spread over mask matched to ref's (the wall rings: the same material
    under different light). Returns (matched, the L shift applied at the mean)."""
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB).astype(np.float32)
    labr = cv2.cvtColor(ref, cv2.COLOR_RGB2LAB).astype(np.float32)
    m = mask > 0
    shift = 0.0
    for c in range(3):
        mu, sd = float(lab[..., c][m].mean()), float(lab[..., c][m].std())
        mur, sdr = float(labr[..., c][m].mean()), float(labr[..., c][m].std())
        lab[..., c] = (lab[..., c] - mu) * (sdr / max(sd, 1e-3)) + mur
        if c == 0:
            shift = mur - mu
    return cv2.cvtColor(np.clip(lab + 0.5, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB), round(shift, 2)


def box_similarity(gref, g, core, grow=10, min_inliers=20):
    """A similarity mapping the box of still g onto the reference's from SIFT matches inside the
    box core grown by `grow` px. Returns (M 2x3 | None, matches, inliers, centre shift (dx, dy))."""
    x, y, w, h = core
    H_, W_ = gref.shape
    m = np.zeros((H_, W_), np.uint8)
    m[max(0, y - grow):min(H_, y + h + grow), max(0, x - grow):min(W_, x + w + grow)] = 255
    sift = cv2.SIFT_create(contrastThreshold=0.02)
    kr, dr = sift.detectAndCompute(gref, m)
    kg, dg = sift.detectAndCompute(g, m)
    if dr is None or dg is None or len(kr) < 8 or len(kg) < 8:
        return None, 0, 0, (0.0, 0.0)
    good = [a for a, b in cv2.BFMatcher(cv2.NORM_L2).knnMatch(dg, dr, k=2) if a.distance < 0.8 * b.distance]
    if len(good) < 6:
        return None, len(good), 0, (0.0, 0.0)
    src = np.float32([kg[a.queryIdx].pt for a in good]).reshape(-1, 1, 2)
    dst = np.float32([kr[a.trainIdx].pt for a in good]).reshape(-1, 1, 2)
    M, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=2.0, confidence=0.999, refineIters=10)
    ni = int(inl.sum()) if inl is not None else 0
    if M is None or ni < min_inliers:
        return None, len(good), ni, (0.0, 0.0)
    cx, cy = x + w / 2.0, y + h / 2.0
    dx = float(M[0, 0] * cx + M[0, 1] * cy + M[0, 2] - cx)
    dy = float(M[1, 0] * cx + M[1, 1] * cy + M[1, 2] - cy)
    return M, len(good), ni, (dx, dy)


def pin_to(gref, g, rmask, kind="similarity"):
    """A similarity (4 DOF) or a homography (8 DOF, MAGSAC++) mapping still g onto the reference from
    SIFT matches inside the ring mask. Returns (M 2x3 | H 3x3 | None, matches, inliers)."""
    sift = cv2.SIFT_create()
    kr, dr = sift.detectAndCompute(gref, rmask)
    kg, dg = sift.detectAndCompute(g, rmask)
    if dr is None or dg is None or len(kr) < 8 or len(kg) < 8:
        return None, 0, 0
    bf = cv2.BFMatcher(cv2.NORM_L2)
    good = [m for m, n in bf.knnMatch(dg, dr, k=2) if m.distance < 0.75 * n.distance]
    if len(good) < 8:
        return None, len(good), 0
    src = np.float32([kg[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst = np.float32([kr[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    if kind == "homography":
        M, inl = cv2.findHomography(src, dst, cv2.USAC_MAGSAC, RANSAC_PX, confidence=0.999)
    else:
        M, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=RANSAC_PX, confidence=0.999, refineIters=10)
    return M, len(good), int(inl.sum()) if inl is not None else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("photos", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seconds", type=float, default=3.0, help="the whole chain of transitions")
    ap.add_argument("--hold", type=float, default=3.0, help="seconds on the last photo")
    ap.add_argument("--lead", type=float, default=0.0, help="seconds on the first photo")
    ap.add_argument("--max-long", type=int, default=1920)
    ap.add_argument("--mode", default="reshot", choices=("reshot", "loose"))
    ap.add_argument("--ease", default="smootherstep", choices=("smootherstep", "linear"))
    ap.add_argument("--variant", default="luma", choices=("luma", "hold-dis", "luma-melt-soft", "tool-luma", "tool-luma-melt-soft", "draw"))
    ap.add_argument("--overlap", type=float, default=0.35, help="draw: a repaint starts this fraction of a step before its turn and ends as late")
    ap.add_argument("--front", type=float, default=0.35, help="draw: the width of a repaint's front in order units (TR14's luma uses 0.15)")
    ap.add_argument("--zone-erode", type=int, default=15, help="draw: the union changed region eroded this many px is the drawing zone")
    ap.add_argument("--no-local-pin", action="store_true", help="skip the per-box pin after the global one")
    ap.add_argument("--local-pin", default="sift", choices=("sift", "edges", "ring"), help="the per-box pin: SIFT inside the box (similarity), the outline edges (axis-aligned affine) or the wall ring's translation")
    ap.add_argument("--pin-min-inliers", type=int, default=20, help="sift pin: below this many inliers the still keeps the global pin")
    ap.add_argument("--match-light", default="auto", choices=("auto", "on", "off"), help="match each still's Lab statistics over the wall rings to the last still's (auto = on for draw)")
    ap.add_argument("--crop", default="none", choices=("none", "valid"), help="none = the reference's full frame (default); valid = the rectangle every warped photo covers")
    ap.add_argument("--size", default="", help="also write chain_<WxH>.mp4 scaled to this size")
    ap.add_argument("--fps", type=float, default=30.0)
    ap.add_argument("--color", type=float, default=0.7, help="the tool's color path strength")
    ap.add_argument("--no-anchor", action="store_true", help="skip the pin to the last still from the wall rings")
    ap.add_argument("--pin", default="homography", choices=("homography", "similarity"), help="the map of the pin (default homography, MAGSAC++)")
    ap.add_argument("--field", default="hold-dis", choices=("hold-dis", "hold"), help="the field between two pinned stills (see the head)")
    a = ap.parse_args()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "aligned").mkdir(exist_ok=True)
    photos = [Path(p).expanduser().resolve() for p in a.photos]
    if len(photos) < 2:
        raise SystemExit("two photos at least")
    ref = photos[-1]
    report = {"photos": [p.name for p in photos], "reference": ref.name, "args": vars(a), "align": {}, "segments": []}

    # 1. every photo onto the last photo's frame (Reveal), one common crop, one canvas
    t0 = time.time()
    warped, valids, refA = [], [], None
    for p in photos[:-1]:
        t1 = time.time()
        A, W, Vm, met = align_onto(ref, p, out / "reveal", a.mode)
        refA = A
        warped.append(W)
        valids.append(Vm)
        met["seconds"] = round(time.time() - t1, 1)
        report["align"][p.name] = met
        print(f"  {p.name} -> {ref.name}: {met.get('method')} {met.get('inliers')} inliers, {met.get('rmse_px')} px, "
              f"confidence {met.get('confidence')}, mode {met['mode']}, residual {met['residual']}, {met['seconds']} s", flush=True)
    fill_share = []
    if a.crop == "valid":
        valid_all = valids[0].copy()
        for v in valids[1:]:
            valid_all = cv2.bitwise_and(valid_all, v)
        x, y, w, h = rv.crop_rect(valid_all)
    else:
        # the full frame; a pixel a photo does not cover keeps its last known content
        x, y, w, h = 0, 0, refA.shape[1], refA.shape[0]
        base = refA
        for j in range(len(warped) - 1, 0, -1):
            base = np.where(valids[j][..., None] > 0, warped[j], base)
        # a pixel a photo does not cover takes the NEXT photo's content when that covers it (the
        # repaint has not reached it yet: the next state is the closer one), else the previous
        # filled still's, else the reference's
        nxt = [None] * len(warped)
        later = refA
        for j in range(len(warped) - 1, -1, -1):
            nxt[j] = later
            later = np.where(valids[j][..., None] > 0, warped[j], later)
        filled = []
        prev = None
        for k, (W, Vm) in enumerate(zip(warped, valids)):
            f = np.where(Vm[..., None] > 0, W, nxt[k])
            filled.append(f)
            fill_share.append(round(float((Vm == 0).mean()), 4))
        warped = filled
    stills = [W[y:y + h, x:x + w] for W in warped] + [refA[y:y + h, x:x + w]]
    report["fill_share"] = fill_share
    stills = [rv.scaled_copy(s, a.max_long)[0] for s in stills]
    H0, W0 = stills[0].shape[:2]
    W0, H0 = W0 - W0 % 2, H0 - H0 % 2
    stills = [np.ascontiguousarray(s[:H0, :W0]) for s in stills]
    report["crop"] = {"full": [int(x), int(y), int(w), int(h)], "canvas": [W0, H0]}
    print(f"  aligned {len(stills)} stills onto {ref.name}: crop {a.crop} {w}x{h} at ({x},{y}) of the full frame, canvas {W0}x{H0}, "
          f"filled share per still {fill_share}, {time.time() - t0:.1f} s", flush=True)

    # 2. the boxes (from the first repaint), the ring drift before the pin, the pin, the drift after
    boxes, mask01 = find_boxes(stills[0], stills[1])
    report["boxes"] = [list(b) for b in boxes]
    if a.crop == "none":
        sc = W0 / refA.shape[1]
        box_fill = []
        for Vm in valids:
            vs = cv2.resize(Vm, (W0, H0), interpolation=cv2.INTER_NEAREST)
            box_fill.append([round(float((vs[by:by + bh, bx:bx + bw] == 0).mean()), 4) for bx, by, bw, bh in boxes])
        report["box_fill_share"] = box_fill
        print(f"  filled share inside the boxes per still (left, right): {box_fill}", flush=True)
    rmask = ring_mask((H0, W0), boxes)
    grays = [T.gray_of(s) for s in stills]
    # phaseCorrelate's sub-pixel peak carries a bias of up to 0.5 px on some windows (the reference
    # against itself read dy 0.5 on the 1->7 pair): every shift is reported minus that self-reading
    def drift(b):
        bias = ring_shift(grays[-1], grays[-1], b, (H0, W0))
        return [(round(dx - bias[0], 2), round(dy - bias[1], 2), r) for dx, dy, r in (ring_shift(grays[-1], g, b, (H0, W0)) for g in grays)], bias
    before, biases = zip(*[drift(b) for b in boxes])
    before = list(before)
    report["ring_bias"] = [list(bb) for bb in biases]
    for bi, b in enumerate(boxes):
        print(f"  box {bi} {b}: ring drift vs the last still before the pin {before[bi]} (self-reading {biases[bi]} subtracted)", flush=True)
    pins = []
    if not a.no_anchor:
        for k in range(len(stills) - 1):
            M, nm, ni = pin_to(grays[-1], grays[k], rmask, a.pin)
            if M is None:
                pins.append({"still": photos[k].name, "matches": nm, "inliers": ni, "applied": False})
                print(f"  pin {photos[k].name}: no similarity ({nm} matches): left as Reveal aligned it", flush=True)
                continue
            if M.shape[0] == 3:
                M = M / M[2, 2]
                stills[k] = cv2.warpPerspective(stills[k], M, (W0, H0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            else:
                stills[k] = cv2.warpAffine(stills[k], M, (W0, H0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            s = float(np.hypot(M[0, 0], M[0, 1]))
            rot = float(np.degrees(np.arctan2(M[0, 1], M[0, 0])))
            grays[k] = T.gray_of(stills[k])
            pins.append({"still": photos[k].name, "matches": nm, "inliers": ni, "applied": True,
                         "scale": round(s, 5), "rotation_deg": round(rot, 3), "shift_px": [round(float(M[0, 2]), 2), round(float(M[1, 2]), 2)]})
            print(f"  pin {photos[k].name}: {ni} of {nm} ring matches, scale {s:.5f}, rotation {rot:.3f} deg, shift ({M[0, 2]:.2f}, {M[1, 2]:.2f}) px", flush=True)
    after = [drift(b)[0] for b in boxes]
    for bi, b in enumerate(boxes):
        print(f"  box {bi}: ring drift after the pin {after[bi]}", flush=True)
    local = []
    cores = [tight_box(mask01, b) for b in boxes]
    report["box_cores"] = [list(c) for c in cores]
    ref_edges = [box_edges(grays[-1], c) for c in cores]
    print(f"  box cores {cores}; outline edges in the last still (L, R, T, B) {[tuple(None if v is None else round(v, 1) for v in e) for e in ref_edges]}", flush=True)
    edges_before = [[box_edges(g, c, e) for g in grays] for c, e in zip(cores, ref_edges)]
    report["edges_before"] = edges_before
    if not a.no_local_pin and a.local_pin == "sift":
        for bi, ((bx, by, bw, bh), core) in enumerate(zip(boxes, cores)):
            gx_, gy_ = int(bw * RING_GROW), int(bh * RING_GROW)
            X0, Y0 = max(0, bx - gx_), max(0, by - gy_)
            X1, Y1 = min(W0, bx + bw + gx_), min(H0, by + bh + gy_)
            wgt = np.zeros((H0, W0), np.float32)
            wgt[Y0 + 20:Y1 - 20, X0 + 20:X1 - 20] = 1.0
            wgt = cv2.GaussianBlur(wgt, (0, 0), 8)[..., None]
            for k in range(len(stills) - 1):
                for pass_ in (1, 2):        # two passes: the first estimate from a few hundred matches can leave 1-2 px
                    M, nm, ni, (dx, dy) = box_similarity(grays[-1], T.gray_of(stills[k]), core, min_inliers=a.pin_min_inliers)
                    if M is None:
                        if pass_ == 1:
                            local.append({"still": photos[k].name, "box": bi, "applied": False, "matches": nm, "inliers": ni})
                            print(f"  box {bi} {photos[k].name}: {ni} inliers of {nm} matches inside the box: no pin, kept as pinned globally", flush=True)
                        break
                    if pass_ == 2 and abs(dx) < 0.3 and abs(dy) < 0.3:
                        break
                    sc = float(np.hypot(M[0, 0], M[0, 1])); rot = float(np.degrees(np.arctan2(M[0, 1], M[0, 0])))
                    moved = cv2.warpAffine(stills[k], M, (W0, H0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                    stills[k] = T.to_u8(stills[k] * (1 - wgt) + moved * wgt)
                    local.append({"still": photos[k].name, "box": bi, "pass": pass_, "applied": True, "matches": nm, "inliers": ni, "scale": round(sc, 5),
                                  "rotation_deg": round(rot, 3), "centre_shift_px": [round(dx, 2), round(dy, 2)]})
                    print(f"  box {bi} {photos[k].name} pass {pass_}: {ni} inliers of {nm}; the box sat ({dx:.2f}, {dy:.2f}) px off at its centre, scale {sc:.4f}, rotation {rot:.2f} deg: pinned", flush=True)
        grays = [T.gray_of(s) for s in stills]
        check = []
        for bi, core in enumerate(cores):
            row = []
            for k in range(len(stills) - 1):
                M, nm, ni, (dx, dy) = box_similarity(grays[-1], grays[k], core, min_inliers=a.pin_min_inliers)
                row.append(None if M is None else [round(dx, 2), round(dy, 2), round(float(np.hypot(M[0, 0], M[0, 1])), 5), ni])
            check.append(row)
            print(f"  box {bi}: after the pin, per still (centre shift dx, dy, scale, inliers) {row}", flush=True)
        report["box_pin_check"] = check
        after_local = [drift(b)[0] for b in boxes]
        report["local_pin"] = local
        report["ring_drift_after_local"] = after_local
    elif not a.no_local_pin and a.local_pin == "edges":
        for bi, ((bx, by, bw, bh), core, e_ref) in enumerate(zip(boxes, cores, ref_edges)):
            if any(v is None for v in e_ref):
                print(f"  box {bi}: an outline edge was not found in the last still ({e_ref}): no edge pin", flush=True)
                continue
            gx_, gy_ = int(bw * RING_GROW), int(bh * RING_GROW)
            X0, Y0 = max(0, bx - gx_), max(0, by - gy_)
            X1, Y1 = min(W0, bx + bw + gx_), min(H0, by + bh + gy_)
            wgt = np.zeros((H0, W0), np.float32)
            wgt[Y0 + 20:Y1 - 20, X0 + 20:X1 - 20] = 1.0
            wgt = cv2.GaussianBlur(wgt, (0, 0), 8)[..., None]
            for k in range(len(stills) - 1):
                e = edges_before[bi][k]
                if any(v is None for v in e):
                    local.append({"still": photos[k].name, "box": bi, "applied": False, "edges": e})
                    print(f"  box {bi} {photos[k].name}: an outline edge was not found ({e}): left as pinned globally", flush=True)
                    continue
                L, R, Tp, Bt = e
                Lr, Rr, Tr, Br = e_ref
                sx, sy = (Rr - Lr) / max(R - L, 1e-6), (Br - Tr) / max(Bt - Tp, 1e-6)
                tx, ty = Lr - sx * L, Tr - sy * Tp
                M = np.float32([[sx, 0, tx], [0, sy, ty]])
                moved = cv2.warpAffine(stills[k], M, (W0, H0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                stills[k] = T.to_u8(stills[k] * (1 - wgt) + moved * wgt)
                local.append({"still": photos[k].name, "box": bi, "applied": True, "scale": [round(sx, 5), round(sy, 5)], "shift": [round(tx, 2), round(ty, 2)],
                              "edges": [round(v, 2) for v in e]})
                print(f"  box {bi} {photos[k].name}: edges (L, R, T, B) {[round(v, 1) for v in e]} -> scale ({sx:.4f}, {sy:.4f}), shift ({tx:.1f}, {ty:.1f}) px", flush=True)
        grays = [T.gray_of(s) for s in stills]
        edges_after = [[box_edges(g, c, e) for g in grays] for c, e in zip(cores, ref_edges)]
        report["edges_after"] = edges_after
        for bi, e_ref in enumerate(ref_edges):
            dims = [(None if (e[1] is None or e[0] is None) else round(e[1] - e[0], 1), None if (e[3] is None or e[2] is None) else round(e[3] - e[2], 1)) for e in edges_after[bi]]
            devs = [None if any(v is None for v in e) else round(max(abs(e[i] - e_ref[i]) for i in range(4)), 2) for e in edges_after[bi]]
            print(f"  box {bi}: after the edge pin, (width, height) per still {dims}; largest edge deviation from the last still {devs} px", flush=True)
        after_local = [drift(b)[0] for b in boxes]
        for bi, b in enumerate(boxes):
            print(f"  box {bi}: ring drift after the edge pin {after_local[bi]}", flush=True)
        report["local_pin"] = local
        report["ring_drift_after_local"] = after_local
    elif not a.no_local_pin:
        for bi, (bx, by, bw, bh) in enumerate(boxes):
            gx_, gy_ = int(bw * RING_GROW), int(bh * RING_GROW)
            X0, Y0 = max(0, bx - gx_), max(0, by - gy_)
            X1, Y1 = min(W0, bx + bw + gx_), min(H0, by + bh + gy_)
            wgt = np.zeros((H0, W0), np.float32)
            wgt[Y0 + 20:Y1 - 20, X0 + 20:X1 - 20] = 1.0
            wgt = cv2.GaussianBlur(wgt, (0, 0), 8)[..., None]
            for k in range(len(stills) - 1):
                dx, dy, r = after[bi][k]
                if abs(dx) < 0.05 and abs(dy) < 0.05:
                    local.append({"still": photos[k].name, "box": bi, "shift": [dx, dy], "applied": False})
                    continue
                M = np.float32([[1, 0, -dx], [0, 1, -dy]])    # the ring reads the still (dx, dy) off the reference: move it back (a +(dx, dy) move doubled the error on the first try)
                moved = cv2.warpAffine(stills[k], M, (W0, H0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                stills[k] = T.to_u8(stills[k] * (1 - wgt) + moved * wgt)
                local.append({"still": photos[k].name, "box": bi, "shift": [dx, dy], "applied": True})
        grays = [T.gray_of(s) for s in stills]
        after_local = [drift(b)[0] for b in boxes]
        for bi, b in enumerate(boxes):
            print(f"  box {bi}: ring drift after the local pin {after_local[bi]}", flush=True)
        report["local_pin"] = local
        report["ring_drift_after_local"] = after_local
    report["pin"] = pins
    report["ring_drift"] = {"before": before, "after": after,
                            "max_abs_before_px": round(max(max(abs(r[0]), abs(r[1])) for rows in before for r in rows), 2),
                            "max_abs_after_px": round(max(max(abs(r[0]), abs(r[1])) for rows in after for r in rows), 2)}
    if a.match_light == "on" or (a.match_light == "auto" and a.variant == "draw"):
        shifts = []
        for k in range(len(stills) - 1):
            stills[k], sh = match_light(stills[k], stills[-1], rmask)
            shifts.append(sh)
        grays = [T.gray_of(s) for s in stills]
        report["light_match_L_shift"] = shifts
        print(f"  light matched over the wall rings: L shift per still {shifts}", flush=True)
    for i, (s, p) in enumerate(zip(stills, photos)):
        cv2.imwrite(str(out / "aligned" / f"{i}_{p.stem}.jpg"), cv2.cvtColor(s, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])
    vis = V.mask_overlay(stills[0], mask01, None)
    for cx_, cy_, cw_, ch_ in cores:
        cv2.rectangle(vis, (cx_, cy_), (cx_ + cw_, cy_ + ch_), (255, 255, 0), 2)
    for bx, by, bw, bh in boxes:
        cv2.rectangle(vis, (bx, by), (bx + bw, by + bh), (0, 255, 0), 3)
    vis[rmask > 0] = T.to_u8(vis[rmask > 0] * 0.6 + np.array([0, 0, 255]) * 0.4)
    cv2.imwrite(str(out / "boxes.jpg"), cv2.cvtColor(vis, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])

    # 3. the segments: what is left between consecutive stills, the changed region, the luma order
    segs = []
    segs_masks = []
    for k in range(len(stills) - 1):
        t1 = time.time()
        A, B = stills[k], stills[k + 1]
        gA, gB = grays[k], grays[k + 1]
        H, dH_AB, dH_BA, sp = V.homography_fields(gA, gB)
        if not a.no_anchor:
            # the stills are pinned in one frame: a whole-frame homography between two of them fits a
            # mix of the wall and the pavement planes and moves the boxes by 1-3 px; the field carries none
            H, dH_AB, dH_BA = np.eye(3), np.zeros_like(dH_AB), np.zeros_like(dH_BA)
        corners = np.array([[0, 0], [W0, 0], [W0, H0], [0, H0]], np.float32).reshape(-1, 1, 2)
        moved = cv2.perspectiveTransform(corners, np.linalg.inv(H)).reshape(-1, 2) - corners.reshape(-1, 2)
        centres = np.array([[bx + bw / 2, by + bh / 2] for bx, by, bw, bh in boxes], np.float32).reshape(-1, 1, 2)
        box_moved = cv2.perspectiveTransform(centres, np.linalg.inv(H)).reshape(-1, 2) - centres.reshape(-1, 2)
        mask = V.changed_mask(A, B, H)
        F = cv2.GaussianBlur((mask > 0).astype(np.float32), (0, 0), V.MIX_FEATHER_SIGMA)
        F_B = cv2.warpPerspective(F, H, (W0, H0), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
        if a.variant in ("tool-luma", "tool-luma-melt-soft", "draw"):
            dis, corr = {"diag": {}}, None
        else:
            dis = T.dense_displacement(A, B)
            fields = {"dis": dis, "roma": dis}       # the RoMa field was never adopted: the DIS field stands in
            corr = V.build_corr(fields, a.field, dH_AB, dH_BA, F, F_B)
        order = V.order_map(A, B, mask, "luma") if a.variant in ("luma", "luma-melt-soft") else None
        if a.variant == "draw":
            # the drawing order inside this step: the new paint's edges first (as a drawing starts with
            # its lines), the old coat's bright parts early, and noise at two scales for an irregular front
            edges = cv2.Canny(gB, 60, 160)
            dist = cv2.distanceTransform(255 - edges, cv2.DIST_L2, 5).astype(np.float32)
            rng = np.random.default_rng(k + 1)
            noise = (cv2.GaussianBlur(rng.standard_normal((H0, W0)).astype(np.float32), (0, 0), 6)
                     + 0.5 * cv2.GaussianBlur(rng.standard_normal((H0, W0)).astype(np.float32), (0, 0), 24))
            full = np.full((H0, W0), 255, np.uint8)
            order = (0.5 * V.rank_order(dist, full) + 0.3 * V.rank_order(-gA.astype(np.float32), full)
                     + 0.2 * V.rank_order(noise, full))
            order = V.rank_order(order, full)
            segs_masks.append(mask)
        flow = V.curl_noise(H0, W0, mask, feather_px=64) if a.variant in ("luma-melt-soft", "tool-luma-melt-soft") else None
        cache = T.color_cache(A, B)
        sA, sB = T.lab_stats(A, lab=cache[0]), T.lab_stats(B, lab=cache[2])
        segs.append(dict(A=A, B=B, corr=corr, F=F, order=order, flow=flow, cache=cache, sA=sA, sB=sB))
        info = {"pair": f"{photos[k].stem}->{photos[k + 1].stem}", "inliers_left": int(sp[1]) if sp else 0,
                "corner_motion_px": round(float(np.linalg.norm(moved, axis=1).max()), 2),
                "box_centre_motion_px": [round(float(v), 2) for v in np.linalg.norm(box_moved, axis=1)],
                "mask_share": round(float((mask > 0).mean()), 3), "median_disp_px": dis["diag"].get("median_disp_px"),
                "mean_certainty": dis["diag"].get("mean_certainty"), "prep_s": round(time.time() - t1, 1)}
        report["segments"].append(info)
        print(f"  segment {info['pair']}: {info['inliers_left']} inliers between the stills, corner motion "
              f"{info['corner_motion_px']} px, at the box centres {info['box_centre_motion_px']} px, mask {info['mask_share']:.3f}, {info['prep_s']} s", flush=True)

    zone = None
    if a.variant == "draw":
        uni = np.zeros((H0, W0), np.uint8)
        for m in segs_masks:
            uni = cv2.bitwise_or(uni, m)
        ke = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * a.zone_erode + 1,) * 2)
        zone = cv2.GaussianBlur(cv2.erode(uni, ke).astype(np.float32) / 255.0, (0, 0), 8)[..., None]
        cv2.imwrite(str(out / "zone.jpg"), cv2.cvtColor(T.to_u8(stills[0] * (0.4 + 0.6 * zone)), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
        report["draw"] = {"zone_share": round(float((zone > 0.5).mean()), 4), "overlap": a.overlap, "front": a.front, "zone_erode": a.zone_erode}
        print(f"  draw zone: {report['draw']['zone_share']:.3f} of the canvas", flush=True)

    # 4. the frames: one ease over the whole chain, then the hold
    nseg = len(segs)
    N = int(round(a.seconds * a.fps))
    n_lead, n_hold = int(round(a.lead * a.fps)), int(round(a.hold * a.fps))
    ease = smootherstep if a.ease == "smootherstep" else (lambda v: np.clip(v, 0.0, 1.0))
    gx, gy = T._grid(H0, W0)
    amp = V.MELT_AMP * max(H0, W0)
    total = n_lead + N + n_hold
    enc = OneKeyframeEncoder(out / "chain.mp4", W0, H0, a.fps, total)
    enc2 = None
    if a.size:
        sw, sh = [int(v) for v in a.size.lower().split("x")]
        enc2 = OneKeyframeEncoder(out / f"chain_{sw}x{sh}.mp4", sw, sh, a.fps, total)
    tiles, every = [], max(1, int(round(a.fps / 4)))
    timeline = []

    def put(f, i_global):
        enc.write(f)
        if enc2 is not None:
            enc2.write(cv2.resize(f, (sw, sh), interpolation=cv2.INTER_AREA))
        if i_global % every == 0:
            tl = cv2.resize(f, (int(W0 * 240 / H0), 240), interpolation=cv2.INTER_AREA)
            lab_ = f"f{i_global} {i_global / a.fps:.2f}s"
            cv2.rectangle(tl, (0, 0), (len(lab_) * 9 + 6, 18), (0, 0, 0), -1)
            cv2.putText(tl, lab_, (3, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
            tiles.append(tl)

    t0 = time.time()
    g_i = 0
    for _ in range(n_lead):
        put(stills[0], g_i); g_i += 1
    for i in range(N):
        g = float(ease(i / (N - 1))) if N > 1 else 1.0
        pos = g * nseg
        seg = min(int(np.floor(pos)), nseg - 1)
        u = pos - seg
        if a.variant == "draw" and 0 < i < N - 1:
            beta = pos / nseg
            bg = stills[0].astype(np.float32) * (1 - beta) + stills[-1].astype(np.float32) * beta
            fin = stills[0].astype(np.float32)
            for k2, s2 in enumerate(segs):
                lead_ = 0.0 if k2 == 0 else a.overlap
                tail_ = 0.0 if k2 == nseg - 1 else a.overlap
                t_k = float(np.clip((pos - k2 + lead_) / (1.0 + lead_ + tail_), 0.0, 1.0))
                if t_k <= 0.0:
                    break
                m = V.reveal_mix(s2["order"], t_k, a.front)[..., None]
                fin = fin * (1 - m) + s2["B"].astype(np.float32) * m
            f = T.to_u8(bg * (1 - zone) + fin * zone)
        elif i == N - 1 or (u >= 1.0 - 1e-9):
            f, u = stills[seg + 1].copy(), 1.0
        elif u <= 1e-9:
            f = stills[seg].copy()
        else:
            s = segs[seg]
            Ai, Bi = T.color_pair_at(s["A"], s["B"], s["sA"], s["sB"], u, a.color, T.TCFG, s["cache"])
            if a.variant in ("tool-luma", "tool-luma-melt-soft"):
                m = T.luma_mask(Ai, u)[..., None]
                f = T.to_u8(Ai * (1 - m) + Bi * m)
            else:
                override = None
                if s["order"] is not None:
                    override = u * (1.0 - s["F"]) + V.reveal_mix(s["order"], u) * s["F"]
                f = V.morph_frame_mixed(Ai, Bi, s["corr"], u, u, override)
            if s["flow"] is not None:
                sw_ = amp * float(np.sin(np.pi * u))
                f = cv2.remap(f, gx + sw_ * s["flow"][..., 0], gy + sw_ * s["flow"][..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        timeline.append((i, seg, round(u, 4)))
        put(f, g_i); g_i += 1
    for _ in range(n_hold):
        put(stills[-1], g_i); g_i += 1
    n1 = enc.close()
    n2 = enc2.close() if enc2 is not None else None
    rows = [np.hstack(tiles[j:j + 12]) for j in range(0, len(tiles) - len(tiles) % 12, 12)] or [np.hstack(tiles)]
    cv2.imwrite(str(out / "strip.jpg"), cv2.cvtColor(np.vstack(rows), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 82])
    bounds = {}
    for i, seg, u in timeline:
        bounds.setdefault(seg, [i, i])[1] = i
    report["timeline"] = {"lead_frames": n_lead, "transition_frames": N, "hold_frames": n_hold, "written": n1, "written_scaled": n2,
                          "segment_frames": {report["segments"][k]["pair"]: v for k, v in bounds.items()},
                          "render_s": round(time.time() - t0, 1)}
    (out / "report.json").write_text(json.dumps(report, indent=2))
    print(f"  wrote {out / 'chain.mp4'}: {n1} frames ({n_lead} lead + {N} transition + {n_hold} hold) at {W0}x{H0}, "
          f"render {report['timeline']['render_s']} s; segments by frame: {report['timeline']['segment_frames']}", flush=True)


if __name__ == "__main__":
    main()
