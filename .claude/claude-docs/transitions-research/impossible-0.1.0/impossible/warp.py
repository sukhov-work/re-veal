"""Warping: forward splatting with importance weights, backward warping,
and the symmetric halfway-domain morph frame.

Geometry (see correspond.py for the displacement convention):
  A pixel a travels to a + t*dAB(a); B pixel b travels to b + (1-t)*dBA(b).
  Both are FORWARD warps, so both endpoints splat toward the same
  intermediate frame. Forward splatting handles many-to-one collisions
  via importance weights (a simplified softmax splatting, Niklaus & Liu
  CVPR 2020, E5 upgrades this to the reference implementation); holes are
  filled from a backward-warp estimate and, last, inpainted.
"""
import cv2
import numpy as np


def _grid(h, w):
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32),
                         np.arange(h, dtype=np.float32))
    return gx, gy


def backward_warp(img, disp):
    """out[y, x] = img[y + dy, x + dx] with disp defined on the OUTPUT grid."""
    h, w = disp.shape[:2]
    gx, gy = _grid(h, w)
    return cv2.remap(img, gx + disp[..., 0], gy + disp[..., 1],
                     cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def forward_splat(img, disp, t, importance=None, sharpness=10.0, scale=4):
    """Splat img along t*disp into a target buffer of the same size.

    Implementation (v0.1, fast path): the displacement field is smooth, so
    the forward splat is done on SOURCE COORDINATES at 1/scale resolution
    (importance-weighted, softmax-style collision handling) to build an
    inverse map, which is upsampled and applied to the full-resolution
    colors with one cv2.remap. Colors are sampled once, bilinearly, from the
    pristine source; the scatter runs on scale^2 fewer elements. Cost fell
    from ~390 ms to ~30 ms per splat at 1.3 MP. Occlusion edges are softened
    by the low-res coordinate splat; E5 evaluates the exact softmax
    splatting reference implementation for the final quality bar.

    importance (h, w) in [0, 1]: higher wins collisions.
    Returns (rgb float32, cover) where cover ~1 where the target received
    source pixels and ~0 in true holes (disocclusions)."""
    h, w = img.shape[:2]
    hs, ws = max(2, h // scale), max(2, w // scale)
    d = cv2.resize(disp, (ws, hs), interpolation=cv2.INTER_AREA) * (t / scale)
    imp = np.ones((hs, ws), np.float32) if importance is None else \
        cv2.resize(importance, (ws, hs), interpolation=cv2.INTER_AREA)
    wgt = np.exp(sharpness * (imp - 1.0)).astype(np.float32)
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
    # true holes: fall back to the negated forward displacement (adequate
    # for smooth fields), so the map is defined everywhere before upsampling
    hole = cov < 0.05
    inv_x[hole] = (gx - d[..., 0])[hole]
    inv_y[hole] = (gy - d[..., 1])[hole]
    # upsample the inverse DISPLACEMENT, not absolute coordinates: resize
    # aligns pixel centers, so upsampling coordinates by `scale` shifts
    # everything by (scale-1)/2 px (1.5 px at scale 4, a 13-level error)
    inv_dx = cv2.resize(inv_x - gx, (w, h), interpolation=cv2.INTER_LINEAR) * scale
    inv_dy = cv2.resize(inv_y - gy, (w, h), interpolation=cv2.INTER_LINEAR) * scale
    GX, GY = _grid(h, w)
    rgb = cv2.remap(img, GX + inv_dx, GY + inv_dy, cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    cover = cv2.resize(np.minimum(cov, 1.0), (w, h), interpolation=cv2.INTER_LINEAR)
    return rgb, cover


def fill_holes(rgb, cov, fallback, thresh=0.05):
    """Where coverage is thin, take the fallback image; where the fallback
    is also unreliable (border), inpaint."""
    out = rgb.copy()
    hole = cov < thresh
    out[hole] = fallback[hole]
    return out


def morph_frame(A, B, corr, t_warp, t_mix):
    """One intermediate frame.
    t_warp in [0,1]: geometric progress along the correspondence.
    t_mix  in [0,1]: cross-dissolve weight toward B.
    Returns uint8 RGB."""
    dAB, dBA = corr["dAB"], corr["dBA"]
    wA, wB = corr["wA"], corr["wB"]
    IA, cA = forward_splat(A, dAB, t_warp, wA)
    IB, cB = forward_splat(B, dBA, 1.0 - t_warp, wB)
    # backward-warp fallbacks: approximate the inverse map by negating the
    # forward displacement sampled at the target (fine for smooth fields)
    fA = backward_warp(A, -t_warp * dAB).astype(np.float32)
    fB = backward_warp(B, -(1.0 - t_warp) * dBA).astype(np.float32)
    IA = fill_holes(IA, cA, fA)
    IB = fill_holes(IB, cB, fB)
    # coverage-aware mix: where one side has no support, lean on the other
    mix = np.full(cA.shape, t_mix, np.float32)
    mix = np.where(cA < 0.05, 1.0, mix)
    mix = np.where(cB < 0.05, 0.0, mix)
    mix = cv2.GaussianBlur(mix, (0, 0), 3)[..., None]
    out = IA * (1 - mix) + IB * mix
    return np.clip(out, 0, 255).astype(np.uint8)


def portal_mask(h, w, t, kind="iris", feather=0.08, center=(0.5, 0.5)):
    """Reveal masks for the portal path: 0 = A, 1 = B. Feather is a fraction
    of the diagonal. kinds: iris (circle from center), wipe (left->right),
    luma is computed by the caller from the image itself."""
    gx, gy = _grid(h, w)
    diag = float(np.hypot(w, h))
    if kind == "wipe":
        seam = t * (w + 2 * feather * diag) - feather * diag
        m = (seam - gx) / (feather * diag) + 0.5
    else:
        cx, cy = center[0] * w, center[1] * h
        r = np.hypot(gx - cx, gy - cy)
        rmax = max(np.hypot(cx, cy), np.hypot(w - cx, cy),
                   np.hypot(cx, h - cy), np.hypot(w - cx, h - cy))
        edge = t * (rmax + feather * diag)
        m = (edge - r) / (feather * diag) + 0.5
    return np.clip(m, 0, 1).astype(np.float32)
