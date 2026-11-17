#!/usr/bin/env python3
"""wall_pairs.py: a repainted planar wall, BEFORE and AFTER, aligned on the wall plane (research only).

A one-off beside the tools (owner order 2026-11-17). Reveal's matchers find no inlier on a wall whose
whole face was repainted: the stock fit hangs on the fence behind the wall (pair `a`) or on the unpainted
cap course (pair `b`). The block joints survive the paint, so this script fits the homography on them:

  fit     seed (Reveal's learned matcher, loose profile) -> groove maps (black-hat of a
          contrast-normalised luminance) -> window matches by normalised cross-correlation, coarse to
          fine -> MAGSAC homography B->A with a held-out share of the windows -> `fit.json`, `H.npy`
  render        AFTER warped onto BEFORE's frame, the valid rectangle, the stills and the videos
  verify        the residual of the joints per zone on the rendered stills
  render-after  BEFORE warped onto AFTER's frame (owner order 2026-11-17: the AFTER photo is the
                source of truth for detail and keeps its full frame); BEFORE is completed outside
                its footprint and a coverage mask says where
  verify-after  the same joint measure on those stills

`render` keeps BEFORE as the reference frame, Reveal's rule. `render-after` reverses it for this
one-off by the owner's word; the homography is the same one, inverted.
Nothing here enters `reveal.py`; the script imports it for the decoder and the learned matcher only.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageCms

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import reveal as rv  # noqa: E402  (research only)

SRC = Path("/Users/yevhens/Downloads/wall")

# Polygons are in BEFORE's full-resolution pixels. `wall` is the painted face (the fit lives here);
# `skip` are things standing in front of it in either photo (never fitted, never measured).
PAIRS = {
    "a": {
        "before": "1.jpg", "after": "2.jpg",
        "wall": [(0, 1010), (4032, 1010), (4032, 2840), (0, 2840)],
        "skip": [], "strip": 96,
        "win45": (0, 0, 3024, 3780),      # AFTER px: full width, so the text (left) and the handle (right) stay
    },
    "b": {
        "before": "1b.jpg", "after": "2b.jpg",
        "wall": [(0, 880), (4032, 1130), (4032, 3024), (3300, 3024), (1400, 2530), (0, 2000)],
        "skip": [], "strip": 32,          # the joints slope in this BEFORE: shorter strips
        "win45": None,                    # the largest 4:5 window of real pixels
    },
}

# (level scale, window px, grid step px, search radius px), all at the level's resolution
LEVELS = [(0.5, 160, 64, 20), (0.5, 112, 48, 8), (1.0, 160, 80, 8)]
RANSAC_PX_FULL = [8.0, 4.0, 3.0]           # MAGSAC threshold per level, full-resolution px
GROOVE_ROUNDS = 2                          # learned matches on the groove maps before the windows
MIN_SCORE, MAX_RATIO = 0.22, 0.90
HOLD_OUT = 0.25
SEED = 20261117


def load_pair(tag):
    cfg = PAIRS[tag]
    return rv.load_image_rgb(SRC / cfg["before"]), rv.load_image_rgb(SRC / cfg["after"]), cfg


def poly_mask(shape, polys, scale=1.0):
    m = np.zeros(shape[:2], np.uint8)
    for p in polys:
        cv2.fillPoly(m, [np.round(np.array(p, np.float64) * scale).astype(np.int32)], 255)
    return m


def groove_map(gray, k=15):
    """Dark thin structures (block joints, cracks): black-hat over a contrast-normalised luminance."""
    g = gray.astype(np.float32)
    mu = cv2.GaussianBlur(g, (0, 0), 25)
    sd = np.sqrt(np.maximum(cv2.GaussianBlur((g - mu) ** 2, (0, 0), 25), 1.0))
    n8 = ((np.clip((g - mu) / (sd + 4.0), -3, 3) + 3) / 6 * 255).astype(np.uint8)
    bh = cv2.morphologyEx(n8, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    return cv2.GaussianBlur(bh.astype(np.float32), (0, 0), 1.2)


def seed_h(A, B):
    """Reveal's learned matcher under the loose profile, at 2400 px: a start, not a result."""
    p = rv.profile("loose")
    wa, sa = rv.scaled_copy(A, 2400)
    wb, sb = rv.scaled_copy(B, 2400)
    pts = rv._match_learned(rv.gray_of(wa), rv.gray_of(wb), p)
    if pts is None:
        raise SystemExit("FAILED: the learned matcher gave no seed (run ./setup.sh --learned)")
    est = rv._estimate_h(pts[0], pts[1], p)
    if est is None:
        raise SystemExit("FAILED: no seed homography")
    H, n, rmse = est
    return rv.scale_h(H, 1.0 / sa, 1.0 / sb), n, rmse


def warp_level(B, H, s, size):
    """B warped by H (full-res B->A) into A's frame at level scale s."""
    Bs = cv2.resize(B, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else B
    D, Di = np.diag([s, s, 1.0]), np.diag([1 / s, 1 / s, 1.0])
    return cv2.warpPerspective(Bs, D @ H @ Di, size, flags=cv2.INTER_LINEAR)


def groove_u8(g, ok):
    g = cv2.GaussianBlur(g, (0, 0), 1.5)
    g = np.clip(g / max(float(np.percentile(g[ok > 0], 99.5)), 1e-6), 0, 1)
    g[ok == 0] = 0
    return (g * 255).astype(np.uint8)


def groove_matches(A, B, H, wall_full, s=0.5):
    """DISK + LightGlue on the two groove maps (B warped by H first), inside the wall. The paint is
    gone from a groove map, so the matcher sees the same drawing twice. Returns full-res (pA, pB)."""
    size = (round(A.shape[1] * s), round(A.shape[0] * s))
    As = cv2.resize(A, size, interpolation=cv2.INTER_AREA)
    Bw = warp_level(B, H, s, size)
    ok = cv2.resize(wall_full, size, interpolation=cv2.INTER_NEAREST) & warp_level(np.full(B.shape[:2], 255, np.uint8), H, s, size)
    gA, gB = groove_u8(groove_map(rv.gray_of(As)), ok), groove_u8(groove_map(rv.gray_of(Bw)), ok)
    pts = rv._match_learned(gA, gB, rv.profile("loose"))
    if pts is None:
        raise SystemExit("FAILED: the learned matcher found nothing on the groove maps")
    pA = pts[0].astype(np.float64) / s
    pB = cv2.perspectiveTransform((pts[1].astype(np.float64) / s).reshape(-1, 1, 2), np.linalg.inv(H)).reshape(-1, 2)
    return pA, pB


def window_matches(gA, gB, okA, okB, win, step, radius):
    """For each grid window of A's groove map inside the mask, the offset (dx, dy) at which B's map
    correlates best. Returns rows (cx, cy, dx, dy, score, ratio); the texture test drops windows with
    grooves in one direction only (a single course line slides along itself)."""
    h, w = gA.shape
    half = win // 2
    gxx = cv2.Sobel(gA, cv2.CV_32F, 1, 0, ksize=3)
    gyy = cv2.Sobel(gA, cv2.CV_32F, 0, 1, ksize=3)
    rows = []
    for cy in range(half + radius, h - half - radius, step):
        for cx in range(half + radius, w - half - radius, step):
            sl = (slice(cy - half, cy + half), slice(cx - half, cx + half))
            if okA[sl].mean() < 0.85 * 255:
                continue
            big = (slice(cy - half - radius, cy + half + radius), slice(cx - half - radius, cx + half + radius))
            if okB[big].mean() < 0.97 * 255:
                continue
            t = gA[sl]
            if t.std() < 2.0:
                continue
            ix, iy = gxx[sl], gyy[sl]
            a, b, c = float((ix * ix).mean()), float((ix * iy).mean()), float((iy * iy).mean())
            lmin = 0.5 * (a + c - np.sqrt((a - c) ** 2 + 4 * b * b))
            lmax = 0.5 * (a + c + np.sqrt((a - c) ** 2 + 4 * b * b))
            if lmin < 0.08 * lmax:
                continue
            r = cv2.matchTemplate(gB[big], t, cv2.TM_CCOEFF_NORMED)
            _, s1, _, (px, py) = cv2.minMaxLoc(r)
            rr = r.copy()
            ex = max(3, win // 10)
            rr[max(0, py - ex):py + ex + 1, max(0, px - ex):px + ex + 1] = -1
            s2 = float(rr.max())

            def sub(v0, v1, v2):
                d = v0 - 2 * v1 + v2
                return 0.0 if abs(d) < 1e-9 else float(np.clip(0.5 * (v0 - v2) / d, -0.5, 0.5))
            fx = sub(r[py, px - 1], r[py, px], r[py, px + 1]) if 0 < px < r.shape[1] - 1 else 0.0
            fy = sub(r[py - 1, px], r[py, px], r[py + 1, px]) if 0 < py < r.shape[0] - 1 else 0.0
            if px in (0, r.shape[1] - 1) or py in (0, r.shape[0] - 1):
                continue                      # a peak on the search border is not a measurement
            rows.append((cx, cy, px + fx - radius, py + fy - radius, s1, s2 / max(s1, 1e-6)))
    return np.array(rows, np.float64).reshape(-1, 6)


def fit(tag, out):
    A, B, cfg = load_pair(tag)
    hA, wA = A.shape[:2]
    H, n_seed, rmse_seed = seed_h(A, B)
    log = {"pair": tag, "seed": {"inliers": int(n_seed), "rmse_px_work": round(rmse_seed, 2)}, "levels": []}
    rng = np.random.default_rng(SEED)
    wall_full = poly_mask(A.shape, [cfg["wall"]])
    for p in cfg["skip"]:
        cv2.fillPoly(wall_full, [np.array(p, np.int32)], 0)
    final = None
    for r in range(GROOVE_ROUNDS):
        pA, pB = groove_matches(A, B, H, wall_full)
        thr = 8.0 if r == 0 else 4.0
        Hn, inl = cv2.findHomography(pB, pA, cv2.USAC_MAGSAC, thr, maxIters=20000, confidence=0.9999)
        if Hn is None or int(inl.sum()) < 30:
            raise SystemExit(f"FAILED: groove round {r}: {0 if inl is None else int(inl.sum())} inliers of {len(pA)}")
        err = np.linalg.norm(cv2.perspectiveTransform(pB.reshape(-1, 1, 2), Hn).reshape(-1, 2) - pA, axis=1)
        moved = np.linalg.norm(cv2.perspectiveTransform(pB.reshape(-1, 1, 2), H).reshape(-1, 2) - pA, axis=1)
        row = {"groove_round": r, "matches": int(len(pA)), "inliers": int(inl.sum()), "thr_full_px": thr,
               "rmse_full_px": round(float(np.sqrt((err[inl.ravel() > 0] ** 2).mean())), 2),
               "median_offset_before_full_px": round(float(np.median(moved[inl.ravel() > 0])), 1)}
        log["levels"].append(row)
        print(json.dumps(row), flush=True)
        H = Hn / Hn[2, 2]
    for li, (s, win, step, radius) in enumerate(LEVELS):
        for it in range(2):
            size = (round(wA * s), round(hA * s))
            As = cv2.resize(A, size, interpolation=cv2.INTER_AREA) if s < 1 else A
            Bw = warp_level(B, H, s, size)
            okB = warp_level(np.full(B.shape[:2], 255, np.uint8), H, s, size)
            okA = cv2.resize(wall_full, size, interpolation=cv2.INTER_NEAREST)
            gA, gB = groove_map(rv.gray_of(As)), groove_map(rv.gray_of(Bw))
            m = window_matches(gA, gB, okA, okB, win, step, radius)
            good = m[(m[:, 4] >= MIN_SCORE) & (m[:, 5] <= MAX_RATIO)]
            if len(good) < 12:
                raise SystemExit(f"FAILED: level {li} kept {len(good)} windows of {len(m)}")
            pA = good[:, :2] / s
            pBw = (good[:, :2] + good[:, 2:4]) / s             # where that content sits in the warped B
            pB = cv2.perspectiveTransform(pBw.reshape(-1, 1, 2), np.linalg.inv(H)).reshape(-1, 2)
            held = rng.random(len(good)) < HOLD_OUT
            Hn, inl = cv2.findHomography(pB[~held], pA[~held], cv2.USAC_MAGSAC, RANSAC_PX_FULL[li], maxIters=20000, confidence=0.9999)
            if Hn is None:
                raise SystemExit(f"FAILED: level {li} no homography")
            proj = cv2.perspectiveTransform(pB.reshape(-1, 1, 2), Hn).reshape(-1, 2)
            err = np.linalg.norm(proj - pA, axis=1)
            thr = RANSAC_PX_FULL[li]
            fit_in = (err < thr) & ~held
            ho_in = (err < thr) & held
            row = {"level": li, "iter": it, "scale": s, "win": win, "radius": radius, "windows": int(len(m)), "kept": int(len(good)),
                   "fit_inliers": int(fit_in.sum()), "fit_n": int((~held).sum()),
                   "fit_rmse_full_px": round(float(np.sqrt((err[fit_in] ** 2).mean())), 2) if fit_in.any() else None,
                   "held_inliers": int(ho_in.sum()), "held_n": int(held.sum()),
                   "held_rmse_full_px": round(float(np.sqrt((err[ho_in] ** 2).mean())), 2) if ho_in.any() else None,
                   "held_median_full_px": round(float(np.median(err[held])), 2) if held.any() else None,
                   "median_offset_before_full_px": round(float(np.median(np.linalg.norm(good[:, 2:4], axis=1)) / s), 2)}
            log["levels"].append(row)
            print(json.dumps(row), flush=True)
            H = Hn / Hn[2, 2]
            final = dict(pA=pA, pB=pB, err=err, held=held, thr=thr, score=good[:, 4])
    out.mkdir(parents=True, exist_ok=True)
    np.save(out / "H.npy", H)
    np.savez(out / "matches.npz", **final)
    log["H"] = H.tolist()
    (out / "fit.json").write_text(json.dumps(log, indent=1))
    residual_plot(A, final, H, out / "residuals.jpg")
    return H


def residual_plot(A, f, H, path, gain=40):
    """Residual vectors (B->A projection minus A), drawn `gain` times longer: fitted green, held-out
    yellow, rejected red."""
    s = 2000 / A.shape[1]
    im = cv2.resize(A, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    im = (im * 0.55).astype(np.uint8)
    proj = cv2.perspectiveTransform(f["pB"].reshape(-1, 1, 2), H).reshape(-1, 2)
    for (xa, ya), (xp, yp), e, h in zip(f["pA"], proj, f["err"], f["held"]):
        c = (255, 0, 0) if e >= f["thr"] else ((255, 255, 0) if h else (0, 255, 0))
        p0 = (int(xa * s), int(ya * s))
        p1 = (int((xa + (xp - xa) * gain) * s), int((ya + (yp - ya) * gain) * s))
        cv2.circle(im, p0, 3, c, -1)
        if e < f["thr"]:
            cv2.line(im, p0, p1, c, 1, cv2.LINE_AA)
    cv2.imwrite(str(path), cv2.cvtColor(im, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])


# ---------------------------------------------------------------------------
# render: the stills and the videos
# ---------------------------------------------------------------------------
FIELD_CAP = 4.0            # px in BEFORE's frame: the smooth field never moves a pixel further
FIELD_STEP = 32
VIDEO_FPS, VIDEO_CRF, VIDEO_SECONDS, FEATHER_AT_1080 = 30, 16, 5.0, 12.0


def smooth_field(fitdir, shape, sigma):
    """A low-order field over BEFORE's frame: the Gaussian kernel regression (width `sigma` px) of the
    window residuals left by the homography. It fades to zero away from the windows and is capped.
    Returns (fx, fy) on a FIELD_STEP grid: add it to H(B) to land on A."""
    m = np.load(fitdir / "matches.npz")
    H = np.load(fitdir / "H.npy")
    ok = m["err"] < 8.0
    pA = m["pA"][ok]
    e = pA - cv2.perspectiveTransform(m["pB"][ok].reshape(-1, 1, 2), H).reshape(-1, 2)
    gy, gx = np.mgrid[0:shape[0] + FIELD_STEP:FIELD_STEP, 0:shape[1] + FIELD_STEP:FIELD_STEP].astype(np.float64)
    g = np.stack([gx.ravel(), gy.ravel()], 1)
    f = np.zeros_like(g)
    for i in range(0, len(g), 4000):
        d2 = ((g[i:i + 4000, None, :] - pA[None, :, :]) ** 2).sum(2)
        w = np.exp(-0.5 * d2 / sigma ** 2)
        ws = w.sum(1, keepdims=True)
        f[i:i + 4000] = (w @ e) / (ws + 1.0)          # + 1.0: with under one window of support the field fades out
    mag = np.linalg.norm(f, axis=1, keepdims=True)
    f *= np.minimum(1.0, FIELD_CAP / np.maximum(mag, 1e-9))
    return f[:, 0].reshape(gx.shape).astype(np.float32), f[:, 1].reshape(gx.shape).astype(np.float32)


def warp_after(B, H, shapeA, scale=1.0, field=None, ss=2):
    """AFTER on BEFORE's canvas (uniformly scaled by `scale`), supersampled `ss` times and averaged
    down, so a shrinking warp does not alias. Returns (rgb, valid)."""
    hA, wA = shapeA[:2]
    W, Hh = round(wA * scale), round(hA * scale)
    k = scale * ss
    ys, xs = np.mgrid[0:Hh * ss, 0:W * ss].astype(np.float32)
    xa, ya = (xs + 0.5) / k - 0.5, (ys + 0.5) / k - 0.5          # BEFORE-frame coordinates of each sample
    if field is not None:
        fx = cv2.resize(field[0], None, fx=FIELD_STEP, fy=FIELD_STEP, interpolation=cv2.INTER_CUBIC)
        fy = cv2.resize(field[1], None, fx=FIELD_STEP, fy=FIELD_STEP, interpolation=cv2.INTER_CUBIC)
        # the grid node (i, j) sits at pixel (j*STEP, i*STEP); cv2.resize centres differ by half a cell
        sh = FIELD_STEP / 2 - 0.5
        mx = np.clip(xa + sh, 0, fx.shape[1] - 1)
        my = np.clip(ya + sh, 0, fx.shape[0] - 1)
        dx = cv2.remap(fx, mx, my, cv2.INTER_LINEAR)
        dy = cv2.remap(fy, mx, my, cv2.INTER_LINEAR)
        xa, ya = xa - dx, ya - dy
    Hi = np.linalg.inv(H).astype(np.float32)
    den = Hi[2, 0] * xa + Hi[2, 1] * ya + Hi[2, 2]
    mapx = (Hi[0, 0] * xa + Hi[0, 1] * ya + Hi[0, 2]) / den
    mapy = (Hi[1, 0] * xa + Hi[1, 1] * ya + Hi[1, 2]) / den
    del xa, ya, den, xs, ys
    big = cv2.remap(B, mapx, mapy, cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    hB, wB = B.shape[:2]
    inside = ((mapx >= 1) & (mapx <= wB - 2) & (mapy >= 1) & (mapy <= hB - 2)).astype(np.uint8) * 255
    del mapx, mapy
    rgb = cv2.resize(big, (W, Hh), interpolation=cv2.INTER_AREA) if ss > 1 else big
    valid = cv2.resize(inside, (W, Hh), interpolation=cv2.INTER_AREA) if ss > 1 else inside
    return rgb, (valid >= 255).astype(np.uint8) * 255


def save_srgb(rgb, path, quality=95):
    """Pixels are sRGB (the decoder converted from Display P3); the file says so."""
    icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    im = Image.fromarray(rgb)
    if str(path).endswith(".png"):
        im.save(path, icc_profile=icc, compress_level=6)
    else:
        im.save(path, quality=quality, subsampling=0, icc_profile=icc)


def window_4x5(w, h):
    """The largest centred 4:5 window inside (w, h): (x, y, cw, ch) with even sides."""
    cw = min(w, int(h * 4 / 5)) & ~1
    ch = min(h, int(cw * 5 / 4)) & ~1
    cw = int(ch * 4 / 5) & ~1
    return (w - cw) // 2, (h - ch) // 2, cw, ch


def wipe_video(a, b, path, seconds=VIDEO_SECONDS):
    """Reveal's wipe (hold BEFORE, an eased seam left to right with AFTER behind it, hold AFTER),
    one keyframe per clip, sRGB tagged as bt709."""
    th, tw = a.shape[:2]
    A, Bf = a.astype(np.float32), b.astype(np.float32)
    hold = max(0.8, seconds * 0.22)
    n_hold, n_sweep = round(hold * VIDEO_FPS), round(max(0.8, seconds - 2 * hold) * VIDEO_FPS)
    feather = max(2.0, FEATHER_AT_1080 * tw / 1080.0)
    xs = np.arange(tw, dtype=np.float32)[None, :, None]
    n = 2 * n_hold + n_sweep
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{tw}x{th}", "-r", str(VIDEO_FPS), "-i", "-", "-an", "-c:v", "libx264", "-preset", "medium",
           "-crf", str(VIDEO_CRF), "-g", str(n), "-keyint_min", str(n), "-sc_threshold", "0",
           "-vf", "scale=out_color_matrix=bt709:out_range=tv", "-colorspace", "bt709", "-color_primaries", "bt709",
           "-color_trc", "bt709", "-color_range", "tv",
           "-x264-params", "colorprim=bt709:transfer=bt709:colormatrix=bt709",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for _ in range(n_hold):
            proc.stdin.write(a.tobytes())
        for i in range(n_sweep):
            t = rv._ease((i + 1) / n_sweep)
            seam = t * (tw + 2 * feather) - feather
            alpha = np.clip((seam - xs) / feather + 0.5, 0.0, 1.0)
            proc.stdin.write(np.rint(A * (1.0 - alpha) + Bf * alpha).astype(np.uint8).tobytes())
        for _ in range(n_hold):
            proc.stdin.write(b.tobytes())
        proc.stdin.close()
        if proc.wait(timeout=1800) != 0:
            raise SystemExit("FAILED: ffmpeg: " + proc.stderr.read().decode("utf8", "replace")[:400])
    finally:
        if proc.poll() is None:
            proc.kill()
    return n


def render(tag, fitdir, out, scale=1.0, sigma=0.0, video=True):
    A, B, cfg = load_pair(tag)
    H = np.load(fitdir / "H.npy")
    field = smooth_field(fitdir, A.shape, sigma) if sigma > 0 else None
    warped, valid = warp_after(B, H, A.shape, scale, field)
    x, y, w, h = rv.crop_rect(valid)
    if valid[y:y + h, x:x + w].min() == 0:
        raise SystemExit("FAILED: the crop rectangle holds a pixel the AFTER photo does not cover")
    canvasA = A if scale == 1.0 else cv2.resize(A, (warped.shape[1], warped.shape[0]), interpolation=cv2.INTER_CUBIC)
    before, after = np.ascontiguousarray(canvasA[y:y + h, x:x + w]), np.ascontiguousarray(warped[y:y + h, x:x + w])
    out.mkdir(parents=True, exist_ok=True)
    for name, img in (("before", before), ("after_aligned", after)):
        save_srgb(img, out / f"{name}.png")
        save_srgb(img, out / f"{name}.jpg")
    cx, cy, cw, ch = window_4x5(w, h)
    info = {"pair": tag, "before": cfg["before"], "after": cfg["after"], "canvas_scale": scale, "field_sigma_px": sigma,
            "field_max_px": None if field is None else round(float(np.hypot(*field).max()), 2),
            "crop_in_before_px": [round(v / scale, 1) for v in (x, y, w, h)], "size": [w, h],
            "window_4x5": {"x": cx, "y": cy, "w": cw, "h": ch, "slack_x_px": w - cw, "slack_y_px": h - ch}}
    if video:
        info["video_native"] = {"file": "reveal_native.mp4", "size": [w, h], "frames": wipe_video(before, after, out / "reveal_native.mp4")}
        tw, th = rv.ASPECTS["4:5"]
        a45 = cv2.resize(before[cy:cy + ch, cx:cx + cw], (tw, th), interpolation=cv2.INTER_AREA)
        b45 = cv2.resize(after[cy:cy + ch, cx:cx + cw], (tw, th), interpolation=cv2.INTER_AREA)
        info["video_4x5"] = {"file": "reveal_4x5.mp4", "size": [tw, th], "frames": wipe_video(a45, b45, out / "reveal_4x5.mp4")}
    (out / "render.json").write_text(json.dumps(info, indent=1))
    np.save(out / "wall_mask_crop.npy", poly_mask(A.shape, [cfg["wall"]])[y:y + h, x:x + w] if scale == 1.0 else
            cv2.resize(poly_mask(A.shape, [cfg["wall"]]), (warped.shape[1], warped.shape[0]), interpolation=cv2.INTER_NEAREST)[y:y + h, x:x + w])
    print(json.dumps(info), flush=True)


# ---------------------------------------------------------------------------
# verify: joint by joint, on the delivered stills
# ---------------------------------------------------------------------------
def joint_offsets(gA, gB, mask, axis, strip=96, reach=6, guard=14):
    """Signed offsets of single joints. axis 0: vertical joints (offset along x), strips of rows;
    axis 1: horizontal joints. A joint is a peak of A's strip profile with no second peak within
    `guard` px; B's peak is searched within `reach` px and refined by a quadratic. Rows: (x, y, d)."""
    if axis == 1:
        r = joint_offsets(gA.T, gB.T, mask.T, 0, strip, reach, guard)
        return r[:, [1, 0, 2]] if len(r) else r
    h, w = gA.shape
    rows = []
    for y0 in range(0, h - strip + 1, strip):
        ok = mask[y0:y0 + strip].mean(0) > 250
        pa, pb = gA[y0:y0 + strip].mean(0), gB[y0:y0 + strip].mean(0)
        pa, pb = pa - np.median(pa[ok]) if ok.any() else pa, pb - np.median(pb[ok]) if ok.any() else pb
        thr = max(4.0, 3.0 * float(np.std(pa[ok]))) if ok.any() else 1e9
        for x in range(guard + 1, w - guard - 1):
            if not ok[x - guard:x + guard + 1].all() or pa[x] < thr or pa[x] != pa[x - guard:x + guard + 1].max():
                continue
            side = np.r_[pa[x - guard:x - 4], pa[x + 5:x + guard + 1]]
            if side.max() > 0.5 * pa[x]:
                continue                                  # a second structure beside it
            seg = pb[x - reach:x + reach + 1]
            j = int(seg.argmax())
            if j in (0, len(seg) - 1) or seg[j] < 0.35 * pa[x]:
                continue

            def sub(v, i):
                d = v[i - 1] - 2 * v[i] + v[i + 1]
                return 0.0 if abs(d) < 1e-9 else float(np.clip(0.5 * (v[i - 1] - v[i + 1]) / d, -0.5, 0.5))
            rows.append((x + sub(pa, x), y0 + strip / 2, (x - reach + j + sub(pb, x - reach + j)) - (x + sub(pa, x))))
    return np.array(rows, np.float64).reshape(-1, 3)


def verify(out, shift=(0.0, 0.0), strip=96):
    """Per zone of a 3x3 grid over the wall inside the crop: the median signed offset of vertical joints
    (dx) and horizontal joints (dy), px at the delivered size. `shift` moves AFTER first: the control."""
    a = np.asarray(Image.open(out / "before.png").convert("RGB"))
    b = np.asarray(Image.open(out / "after_aligned.png").convert("RGB"))
    if shift != (0.0, 0.0):
        b = cv2.warpAffine(b, np.float32([[1, 0, shift[0]], [0, 1, shift[1]]]), (b.shape[1], b.shape[0]), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    mask = np.load(out / "wall_mask_crop.npy")
    gA, gB = groove_map(rv.gray_of(a)), groove_map(rv.gray_of(b))
    v, hz = joint_offsets(gA, gB, mask, 0, strip), joint_offsets(gA, gB, mask, 1, strip)
    ys, xs = np.nonzero(mask)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    zones = []
    for r in range(3):
        for c in range(3):
            zx0, zx1 = x0 + (x1 - x0) * c / 3, x0 + (x1 - x0) * (c + 1) / 3
            zy0, zy1 = y0 + (y1 - y0) * r / 3, y0 + (y1 - y0) * (r + 1) / 3
            sv = v[(v[:, 0] >= zx0) & (v[:, 0] < zx1) & (v[:, 1] >= zy0) & (v[:, 1] < zy1), 2] if len(v) else np.array([])
            sh = hz[(hz[:, 0] >= zx0) & (hz[:, 0] < zx1) & (hz[:, 1] >= zy0) & (hz[:, 1] < zy1), 2] if len(hz) else np.array([])
            zones.append({"zone": f"r{r}c{c}", "n_v": int(len(sv)), "dx_med": None if not len(sv) else round(float(np.median(sv)), 2),
                          "n_h": int(len(sh)), "dy_med": None if not len(sh) else round(float(np.median(sh)), 2)})
    allv, allh = (v[:, 2] if len(v) else np.array([0.0])), (hz[:, 2] if len(hz) else np.array([0.0]))
    res = {"shift_control": list(shift), "joints_v": int(len(v)), "joints_h": int(len(hz)),
           "dx_median": round(float(np.median(allv)), 2), "dx_abs_median": round(float(np.median(np.abs(allv))), 2), "dx_abs_p90": round(float(np.percentile(np.abs(allv), 90)), 2),
           "dy_median": round(float(np.median(allh)), 2), "dy_abs_median": round(float(np.median(np.abs(allh))), 2), "dy_abs_p90": round(float(np.percentile(np.abs(allh), 90)), 2),
           "zones": zones}
    return res


def blink_sheet(out, n=3, size=420):
    """100 % crops on a 3x3 grid over the wall: BEFORE, AFTER, and a 60 px checker of the two."""
    a = np.asarray(Image.open(out / "before.png").convert("RGB"))
    b = np.asarray(Image.open(out / "after_aligned.png").convert("RGB"))
    mask = np.load(out / "wall_mask_crop.npy")
    ys, xs = np.nonzero(mask)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    yy, xx = np.mgrid[0:size, 0:size]
    chk = ((yy // 60 + xx // 60) % 2 == 0)[..., None]
    rows = []
    for r in range(n):
        cells = []
        for c in range(n):
            cx = int(x0 + (x1 - x0) * (c + 0.5) / n - size / 2)
            cy = int(y0 + (y1 - y0) * (r + 0.5) / n - size / 2)
            cx, cy = min(max(cx, 0), a.shape[1] - size), min(max(cy, 0), a.shape[0] - size)
            ca, cb = a[cy:cy + size, cx:cx + size], b[cy:cy + size, cx:cx + size]
            cells.append(np.hstack([ca, cb, np.where(chk, ca, cb)]))
        rows.append(np.hstack(cells))
    sheet = np.vstack(rows)
    Image.fromarray(sheet).save(out / "blink.jpg", quality=88)


# ---------------------------------------------------------------------------
# render-after: AFTER is the frame; BEFORE is warped onto it and completed
# ---------------------------------------------------------------------------
H264_MAX_PX = int(36864 * 256 * 0.96)   # under the level 5.1 frame size after rounding to 16 px blocks; a larger native video is scaled to fit
SEAM_FEATHER = 32              # px of real BEFORE cross-faded into the completion along the seam


def warp_before(A, H, shapeB, ss=2, field=None):
    """BEFORE on AFTER's full frame. Returns (rgb, real): `real` is 255 where BEFORE has a pixel.
    With a field f (defined over BEFORE's frame, A = H(B) + f), an AFTER pixel y reads BEFORE at
    H(y) + f(H(y)); f changes by under 0.02 px per px, so the fixed point needs no iteration."""
    hB, wB = shapeB[:2]
    if field is not None:
        ys, xs = np.mgrid[0:hB * ss, 0:wB * ss].astype(np.float32)
        xb, yb = (xs + 0.5) / ss - 0.5, (ys + 0.5) / ss - 0.5
        del xs, ys
        Hf = H.astype(np.float32)
        den = Hf[2, 0] * xb + Hf[2, 1] * yb + Hf[2, 2]
        x0 = (Hf[0, 0] * xb + Hf[0, 1] * yb + Hf[0, 2]) / den
        y0 = (Hf[1, 0] * xb + Hf[1, 1] * yb + Hf[1, 2]) / den
        del xb, yb, den
        gx = np.clip(x0 / FIELD_STEP, 0, field[0].shape[1] - 1)       # node (i, j) sits at BEFORE pixel (j*STEP, i*STEP)
        gy = np.clip(y0 / FIELD_STEP, 0, field[0].shape[0] - 1)
        x0 += cv2.remap(field[0], gx, gy, cv2.INTER_CUBIC)
        y0 += cv2.remap(field[1], gx, gy, cv2.INTER_CUBIC)
        del gx, gy
        big = cv2.remap(A, x0, y0, cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        ones = ((x0 >= 1) & (x0 <= A.shape[1] - 2) & (y0 >= 1) & (y0 <= A.shape[0] - 2)).astype(np.uint8) * 255
        del x0, y0
        rgb = cv2.resize(big, (wB, hB), interpolation=cv2.INTER_AREA)
        real = (cv2.resize(ones, (wB, hB), interpolation=cv2.INTER_AREA) >= 255).astype(np.uint8) * 255
        return rgb, cv2.erode(real, np.ones((5, 5), np.uint8))
    C = np.array([[ss, 0, (ss - 1) / 2], [0, ss, (ss - 1) / 2], [0, 0, 1.0]])
    M = C @ np.linalg.inv(H)
    big = cv2.warpPerspective(A, M, (wB * ss, hB * ss), flags=cv2.INTER_LANCZOS4)
    ones = cv2.warpPerspective(np.full(A.shape[:2], 255, np.uint8), M, (wB * ss, hB * ss), flags=cv2.INTER_NEAREST)
    rgb = cv2.resize(big, (wB, hB), interpolation=cv2.INTER_AREA)
    real = (cv2.resize(ones, (wB, hB), interpolation=cv2.INTER_AREA) >= 255).astype(np.uint8) * 255
    return rgb, cv2.erode(real, np.ones((5, 5), np.uint8))


def _band(L, lo, hi):
    return (cv2.GaussianBlur(L, (0, 0), lo) if lo else L) - cv2.GaussianBlur(L, (0, 0), hi)


def complete_before(before, real, after):
    """BEFORE has no pixel where its photo ended. Those pixels are completed, never measured:
      above the wall (tree canopy): AFTER's pixels with BEFORE's colour statistics from a band beside the seam;
      below it (ground): per column, the colour of BEFORE's real ground just above the seam (a local
      object such as a stain fades into the neighbourhood's colour within about 200 px), a weak shade
      from AFTER's ground with its leaves and furniture removed (a wide median), and seeded noise in three
      bands (under 1.5 px, 1.5-5 px, 5-14 px), each with the robust spread of BEFORE's real ground.
    The completion is cross-faded into SEAM_FEATHER px of real pixels. Returns (rgb, completed_mask)."""
    h, w = real.shape
    miss = real == 0
    if not miss.any():
        return before, np.zeros_like(real)
    labB = cv2.cvtColor(before, cv2.COLOR_RGB2LAB).astype(np.float32)
    labA = cv2.cvtColor(after, cv2.COLOR_RGB2LAB).astype(np.float32)
    yy = (np.arange(h)[:, None] * np.ones((1, w), np.int32)).astype(np.int32)
    fill = labB.copy()
    top = miss & (yy < h // 2)
    ground = miss & (yy >= h // 2)
    near = lambda zone: cv2.dilate(zone.astype(np.uint8), np.ones((2 * SEAM_FEATHER + 1,) * 2, np.uint8)) > 0
    if top.any():
        band = (cv2.dilate(top.astype(np.uint8), np.ones((241, 241), np.uint8)) > 0) & (real > 0)
        src = labA.copy()
        for c in range(3):
            ma, sa = float(labA[..., c][band].mean()), float(labA[..., c][band].std()) + 1e-3
            mb, sb = float(labB[..., c][band].mean()), float(labB[..., c][band].std())
            src[..., c] = (labA[..., c] - ma) * min(1.5, sb / sa) + mb
        z = near(top) & (yy < h // 2)
        fill[z] = src[z]
    if ground.any():
        cols = ground.any(0)
        seam = np.where(cols, np.argmax(ground, 0), h).astype(np.int32)             # first missing row per column
        r0, r1 = np.clip(seam - 118, 0, h - 1), np.clip(seam - 8, 0, h - 1)          # the real ground rows sampled
        ok = (real > 0).astype(np.float32)
        cnt = np.cumsum(ok, 0)
        n = np.maximum(np.take_along_axis(cnt, r1[None], 0) - np.take_along_axis(cnt, r0[None], 0), 1.0)[0]
        base = np.zeros((3, w), np.float32)
        calm = np.zeros((3, w), np.float32)      # the same colour with local objects (a stain, a brush) voted out
        for c in range(3):
            cs = np.cumsum(labB[..., c] * ok, 0)
            v = (np.take_along_axis(cs, r1[None], 0) - np.take_along_axis(cs, r0[None], 0))[0] / n
            v[~cols] = np.interp(np.flatnonzero(~cols), np.flatnonzero(cols), v[cols]) if (~cols).any() else v[~cols]
            base[c] = cv2.GaussianBlur(v[None, :], (0, 0), 40)[0]
            med = np.median(np.lib.stride_tricks.sliding_window_view(np.pad(v, 300, mode="edge"), 601), axis=1)
            calm[c] = cv2.GaussianBlur(med[None, :].astype(np.float32), (0, 0), 150)[0]
        small = cv2.resize(after, None, fx=0.125, fy=0.125, interpolation=cv2.INTER_AREA)
        low = cv2.resize(cv2.medianBlur(small, 21), (w, h), interpolation=cv2.INTER_CUBIC)
        lowL = cv2.GaussianBlur(cv2.cvtColor(low, cv2.COLOR_RGB2LAB).astype(np.float32)[..., 0], (0, 0), 24)
        shade = 0.5 * (lowL - np.take_along_axis(lowL, np.clip(seam, 0, h - 1)[None], 0))
        sample = (yy >= r0[None]) & (yy < r1[None]) & (real > 0) & cols[None]
        rng = np.random.default_rng(SEED)
        white = rng.standard_normal((h, w)).astype(np.float32)
        noise = np.zeros((h, w), np.float32)
        for lo, hi in ((0, 1.5), (1.5, 5.0), (5.0, 14.0)):
            ref = _band(labB[..., 0], lo, hi)[sample]
            sd = 1.4826 * float(np.median(np.abs(ref - np.median(ref))))            # robust: a leaf or a stain does not set it
            syn = _band(white, lo, hi)
            noise += syn / float(syn.std()) * sd
        z = near(ground) & (yy >= h // 2)
        keep = np.exp(-np.clip(yy - seam[None], 0, None) / 90.0).astype(np.float32)   # a local object fades out below the seam
        col = [calm[c][None] + (base[c] - calm[c])[None] * keep for c in range(3)]
        fill[..., 0][z] = np.clip(col[0] + shade + noise, 0, 255)[z]
        fill[..., 1][z] = col[1][z]
        fill[..., 2][z] = col[2][z]
    filled = cv2.cvtColor(np.clip(fill, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float32)
    dist = cv2.distanceTransform(real, cv2.DIST_L2, 3)
    a = np.clip(dist / SEAM_FEATHER, 0, 1)[..., None]
    a = a * a * (3 - 2 * a)
    out = np.where(dist[..., None] < SEAM_FEATHER, a * before.astype(np.float32) + (1 - a) * filled, before.astype(np.float32))
    return np.rint(np.clip(out, 0, 255)).astype(np.uint8), (dist < SEAM_FEATHER).astype(np.uint8) * 255


def real_window_4x5(real):
    """The largest 4:5 window holding real pixels only: full height of the widest real rectangle, slid sideways."""
    x, y, w, h = rv.crop_rect(real)
    best = None
    for hh in range(h & ~1, 400, -2):
        ww = int(hh * 4 / 5) & ~1
        if ww > real.shape[1]:
            continue
        for yy0 in (y, y + h - hh):
            for xx in range(0, real.shape[1] - ww + 1, 4):
                if real[yy0:yy0 + hh, xx:xx + ww].min() > 0:
                    best = (xx, yy0, ww, hh)
                    break
            if best:
                break
        if best:
            break
    return best


def render_after(tag, fitdir, out, sigma=0.0, video=True):
    A, B, cfg = load_pair(tag)
    H = np.load(fitdir / "H.npy")
    field = smooth_field(fitdir, A.shape, sigma) if sigma > 0 else None
    warped, real = warp_before(A, H, B.shape, field=field)
    before, completed = complete_before(warped, real, B)
    out.mkdir(parents=True, exist_ok=True)
    hB, wB = B.shape[:2]
    save_srgb(B, out / "after.png")
    save_srgb(B, out / "after.jpg")
    save_srgb(before, out / "before_aligned.png")
    save_srgb(before, out / "before_aligned.jpg")
    Image.fromarray(255 - completed).save(out / "before_coverage.png")
    rx, ry, rw, rh = rv.crop_rect(255 - completed)
    w45 = cfg["win45"] or real_window_4x5(255 - completed)
    cx, cy, cw, ch = w45
    share = lambda x, y, w, h: round(float((completed[y:y + h, x:x + w] == 0).mean()), 4)
    info = {"pair": tag, "frame": "after", "before": cfg["before"], "after": cfg["after"], "size": [wB, hB],
            "field_sigma_before_px": sigma, "field_max_before_px": None if field is None else round(float(np.hypot(*field).max()), 2),
            "before_real_share_of_frame": share(0, 0, wB, hB),
            "real_rectangle": {"x": rx, "y": ry, "w": rw, "h": rh, "before_real_share": share(rx, ry, rw, rh)},
            "window_4x5": {"x": cx, "y": cy, "w": cw, "h": ch, "before_real_share": share(cx, cy, cw, ch)}}
    np.save(out / "H_before_to_after.npy", np.linalg.inv(H))
    if video:
        def fit_level(a, b):
            k = min(1.0, (H264_MAX_PX / (a.shape[0] * a.shape[1])) ** 0.5)
            if k < 1.0:
                tw, th = int(a.shape[1] * k) & ~1, int(a.shape[0] * k) & ~1
                a, b = cv2.resize(a, (tw, th), interpolation=cv2.INTER_AREA), cv2.resize(b, (tw, th), interpolation=cv2.INTER_AREA)
            return np.ascontiguousarray(a), np.ascontiguousarray(b), round(k, 4)
        # the whole AFTER frame (BEFORE completed where the mask is black), then the real-pixel rectangle
        a, b, k = fit_level(before, B)
        info["video_native"] = {"file": "reveal_native.mp4", "shows": "the full frame", "size": [a.shape[1], a.shape[0]], "scale": k,
                                "before_real_share": share(0, 0, wB, hB), "frames": wipe_video(a, b, out / "reveal_native.mp4")}
        a, b, k = fit_level(before[ry:ry + rh, rx:rx + rw], B[ry:ry + rh, rx:rx + rw])
        info["video_real_pixels"] = {"file": "reveal_real_pixels.mp4", "shows": "real_rectangle", "size": [a.shape[1], a.shape[0]], "scale": k,
                                     "before_real_share": 1.0, "frames": wipe_video(a, b, out / "reveal_real_pixels.mp4")}
        tw, th = rv.ASPECTS["4:5"]
        a45 = cv2.resize(before[cy:cy + ch, cx:cx + cw], (tw, th), interpolation=cv2.INTER_AREA)
        b45 = cv2.resize(B[cy:cy + ch, cx:cx + cw], (tw, th), interpolation=cv2.INTER_AREA)
        info["video_4x5"] = {"file": "reveal_4x5.mp4", "size": [tw, th], "frames": wipe_video(a45, b45, out / "reveal_4x5.mp4")}
    (out / "render.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info), flush=True)


def verify_after(tag, fitdir, out):
    """The joint measure on the AFTER-frame stills. The joints slope in AFTER's frame, so both delivered
    stills are resampled by ONE common homography (AFTER -> BEFORE's frame, where joints run along the
    axes) and measured there; a common resampling moves both alike. Px are BEFORE-frame px."""
    A, B, cfg = load_pair(tag)
    H = np.load(fitdir / "H.npy")
    b = np.asarray(Image.open(out / "before_aligned.png").convert("RGB"))
    a = np.asarray(Image.open(out / "after.png").convert("RGB"))
    cov = np.asarray(Image.open(out / "before_coverage.png"))
    size = (A.shape[1], A.shape[0])
    tmp = out / "_verify"
    tmp.mkdir(exist_ok=True)
    wa = cv2.warpPerspective(b, H, size, flags=cv2.INTER_CUBIC)            # BEFORE back in its own frame
    wb = cv2.warpPerspective(a, H, size, flags=cv2.INTER_CUBIC)
    ok = cv2.warpPerspective(cov, H, size, flags=cv2.INTER_NEAREST) & cv2.warpPerspective(np.full(a.shape[:2], 255, np.uint8), H, size, flags=cv2.INTER_NEAREST)
    mask = poly_mask(A.shape, [cfg["wall"]]) & cv2.erode(ok, np.ones((31, 31), np.uint8))
    Image.fromarray(wa).save(tmp / "before.png")
    Image.fromarray(wb).save(tmp / "after_aligned.png")
    np.save(tmp / "wall_mask_crop.npy", mask)
    st = cfg["strip"]
    q = cv2.perspectiveTransform(np.array([[[2000., 1900.]], [[2100., 1900.]], [[2000., 2000.]]]), np.linalg.inv(H)).reshape(-1, 2)
    res = {"strip_px": st, "measured_in": "BEFORE-frame px after one common resampling of both stills",
           "delivered_px_per_measured_px_at_wall_centre": [round(float(np.linalg.norm(q[1] - q[0]) / 100), 3), round(float(np.linalg.norm(q[2] - q[0]) / 100), 3)],
           "measure": verify(tmp, strip=st), "control_shift_2_-1.5": verify(tmp, (2.0, -1.5), st)}
    (out / "verify.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k not in ("measure", "control_shift_2_-1.5")}))
    for k in ("measure", "control_shift_2_-1.5"):
        print(k, json.dumps({kk: vv for kk, vv in res[k].items() if kk != "zones"}))
    for z in res["measure"]["zones"]:
        print("  ", json.dumps(z))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["fit", "render", "verify", "render-after", "verify-after"])
    ap.add_argument("pair", choices=sorted(PAIRS))
    ap.add_argument("--out", required=True)
    ap.add_argument("--fit", help="render: the fit folder (H.npy, matches.npz)")
    ap.add_argument("--scale", type=float, default=1.0, help="render: uniform canvas scale over BEFORE's frame")
    ap.add_argument("--field", type=float, default=0.0, help="render: width in px of the smooth residual field; 0 is the homography alone")
    ap.add_argument("--no-video", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    if a.cmd == "fit":
        fit(a.pair, out)
    elif a.cmd == "render":
        render(a.pair, Path(a.fit), out, a.scale, a.field, not a.no_video)
    elif a.cmd == "render-after":
        render_after(a.pair, Path(a.fit), out, a.field, not a.no_video)
    elif a.cmd == "verify-after":
        verify_after(a.pair, Path(a.fit), out)
    else:
        st = PAIRS[a.pair]["strip"]
        res = {"strip_px": st, "measure": verify(out, strip=st), "control_shift_2_-1.5": verify(out, (2.0, -1.5), st)}
        blink_sheet(out)
        (out / "verify.json").write_text(json.dumps(res, indent=1))
        for k in ("measure", "control_shift_2_-1.5"):
            print(k, json.dumps({kk: vv for kk, vv in res[k].items() if kk != "zones"}))
        for z in res["measure"]["zones"]:
            print("  ", json.dumps(z))


if __name__ == "__main__":
    main()
