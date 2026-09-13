"""Color path: time-varying Lab statistics transfer (Reinhard 2001 lineage,
re-implemented; no reveal import) and luminance masks for luma dissolves.

Idea: both endpoints are pulled toward an interpolated target statistic
so their colors MEET halfway along the transition instead of one snapping
to the other at the cut. Strength scales the pull. E11 evaluates OKLab and
optimal-transport alternatives for palette morphs."""
import cv2
import numpy as np


def lab_stats(img, mask=None):
    lab = cv2.cvtColor(img.astype(np.float32) / 255.0, cv2.COLOR_RGB2Lab)
    sel = np.ones(lab.shape[:2], bool) if mask is None else (mask > 0)
    if sel.sum() < 64:
        sel = np.ones(lab.shape[:2], bool)
    return np.array([[lab[..., c][sel].mean(), lab[..., c][sel].std() + 1e-6]
                     for c in range(3)], np.float32)          # (3, 2)


def lerp_stats(sa, sb, u):
    return sa * (1.0 - u) + sb * u


def apply_stats(img, src_stats, dst_stats, strength=1.0):
    if strength <= 0:
        return img
    lab = cv2.cvtColor(img.astype(np.float32) / 255.0, cv2.COLOR_RGB2Lab)
    for c in range(3):
        m0, s0 = src_stats[c]
        m1, s1 = dst_stats[c]
        gain = float(np.clip(s1 / s0, 0.4, 2.5))
        lab[..., c] = (lab[..., c] - m0) * gain + m1
    out = np.clip(cv2.cvtColor(lab, cv2.COLOR_Lab2RGB) * 255.0, 0, 255)
    out = out.astype(np.uint8)
    return out if strength >= 1 else cv2.addWeighted(out, strength, img, 1 - strength, 0)


def color_pair_at(A, B, sA, sB, u, strength):
    """Pull A and B toward the statistic at position u of the path."""
    target = lerp_stats(sA, sB, u)
    return (apply_stats(A, sA, target, strength),
            apply_stats(B, sB, target, strength))


def luma(img):
    return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0


def luma_mask(img, t, softness=0.15, bright_first=True):
    """Luma wipe: reveal in order of brightness. t in [0,1]."""
    L = luma(img)
    if not bright_first:
        L = 1.0 - L
    thr = 1.0 - t * (1.0 + softness) + softness * 0.5
    m = (L - thr) / softness + 0.5
    return np.clip(m, 0, 1).astype(np.float32)
