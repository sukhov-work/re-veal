"""Correspondence between the two endpoint frames.

Two classes of pair (see RESEARCH-PLAN.md, section 2):
  A  related: same/similar scene. Dense displacement from a homography
     pre-alignment plus residual DIS flow (fast, CPU), or RoMa when
     installed (dense warp + per-pixel certainty, the better default).
  B  unrelated: no geometric correspondence exists. Route to a saliency
     alignment (similarity transform between the salient blobs) refined by
     user control points via Moving Least Squares. Semantic anchors from
     DINO/DIFT are a documented TODO (experiment E9); this file exposes the
     hook they plug into (`anchors` argument of `dense_displacement`).

All displacement fields are in PIXELS, defined on the source image grid:
  dAB[y, x] = (dx, dy) such that B[y+dy, x+dx] ~ A[y, x].
"""
import logging

import cv2
import numpy as np

log = logging.getLogger("impossible.correspond")

RATIO = 0.75
MAGSAC_PX = 2.5
MIN_INLIERS = 30          # Class A floor
CONSISTENCY_SIGMA = 3.0   # px; forward-backward error -> certainty


# ---------------------------------------------------------------------------
# sparse
# ---------------------------------------------------------------------------

def sparse_homography(gA, gB):
    """SIFT + ratio + MAGSAC++. Returns (H_BA, inliers, rmse) or None.
    H_BA maps B pixels to A pixels."""
    det = cv2.SIFT_create(nfeatures=6000)
    kA, dA = det.detectAndCompute(gA, None)
    kB, dB = det.detectAndCompute(gB, None)
    if dA is None or dB is None or len(dA) < 8 or len(dB) < 8:
        return None
    knn = cv2.BFMatcher(cv2.NORM_L2).knnMatch(dB, dA, k=2)
    good = [m for m, n in (p for p in knn if len(p) == 2)
            if m.distance < RATIO * n.distance]
    if len(good) < 12:
        return None
    pB = np.float32([kB[m.queryIdx].pt for m in good])
    pA = np.float32([kA[m.trainIdx].pt for m in good])
    flag = getattr(cv2, "USAC_MAGSAC", cv2.RANSAC)
    H, mask = cv2.findHomography(pB, pA, flag, MAGSAC_PX,
                                 maxIters=10000, confidence=0.999)
    if H is None or mask is None:
        return None
    inl = mask.ravel().astype(bool)
    if inl.sum() < 4:
        return None
    proj = cv2.perspectiveTransform(pB[inl].reshape(-1, 1, 2), H)
    rmse = float(np.sqrt(np.mean(np.sum((proj.reshape(-1, 2) - pA[inl]) ** 2, 1))))
    return H, int(inl.sum()), rmse


def _sane(H, shape):
    h, w = shape[:2]
    c = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
    q = cv2.perspectiveTransform(c, H).reshape(-1, 2)
    if not cv2.isContourConvex(q.astype(np.float32)):
        return False
    area = cv2.contourArea(q.astype(np.float32)) / float(w * h)
    return 0.15 <= area <= 6.0


# ---------------------------------------------------------------------------
# dense
# ---------------------------------------------------------------------------

def _grid(h, w):
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32),
                         np.arange(h, dtype=np.float32))
    return gx, gy


def _dis(gA, gB):
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    nA = cv2.normalize(gA, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    nB = cv2.normalize(gB, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    return dis.calc(nA, nB, None)          # A[y,x] ~ B[y+fy, x+fx]


def _homography_guided(gA, gB, H_BA):
    """Total displacement A->B = homography + residual DIS flow measured on
    the pre-aligned pair. Robust where DIS alone is not (large motion)."""
    h, w = gA.shape
    Bw = cv2.warpPerspective(gB, H_BA, (w, h), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_REFLECT)
    r = _dis(gA, Bw)                        # A[x] ~ Bw[x + r]
    gx, gy = _grid(h, w)
    pts = np.stack([gx + r[..., 0], gy + r[..., 1]], -1).reshape(-1, 1, 2)
    src = cv2.perspectiveTransform(pts, np.linalg.inv(H_BA)).reshape(h, w, 2)
    return np.stack([src[..., 0] - gx, src[..., 1] - gy], -1).astype(np.float32)


def consistency_weight(dAB, dBA):
    """exp(-e^2/2s^2) with e = forward-backward error, per A pixel."""
    h, w = dAB.shape[:2]
    gx, gy = _grid(h, w)
    back = cv2.remap(dBA, gx + dAB[..., 0], gy + dAB[..., 1],
                     cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    err = np.linalg.norm(dAB + back, axis=2)
    return np.exp(-(err ** 2) / (2 * CONSISTENCY_SIGMA ** 2)).astype(np.float32)


def roma_available():
    try:
        import romatch  # noqa: F401
        import torch  # noqa: F401
        return True
    except Exception:
        return False


def _roma_displacements(A, B):
    """RoMa dense warp both ways. API verified against the repo README:
    model.match(imA, imB) -> warp (H, 2W, 4) in [-1,1], certainty (H, 2W).
    TODO(E4): confirm output layout for unequal sizes and MPS device."""
    import torch
    from romatch import roma_outdoor
    from PIL import Image
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    model = roma_outdoor(device=dev)
    hA, wA = A.shape[:2]
    hB, wB = B.shape[:2]
    warp, cert = model.match(Image.fromarray(A), Image.fromarray(B), device=dev)
    warp, cert = warp.cpu().numpy(), cert.cpu().numpy()
    Hm, W2 = warp.shape[:2]
    Wm = W2 // 2
    # left half: A grid -> B coords; right half: B grid -> A coords
    def to_disp(block, h_dst, w_dst, h_src, w_src):
        xs = (block[..., 2] + 1) / 2 * (w_dst - 1)
        ys = (block[..., 3] + 1) / 2 * (h_dst - 1)
        gx, gy = np.meshgrid(np.linspace(0, w_src - 1, block.shape[1]),
                             np.linspace(0, h_src - 1, block.shape[0]))
        d = np.stack([xs - gx, ys - gy], -1).astype(np.float32)
        return cv2.resize(d, (w_src, h_src))
    dAB = to_disp(warp[:, :Wm], hB, wB, hA, wA)
    dBA = to_disp(warp[:, Wm:], hA, wA, hB, wB)
    cA = cv2.resize(cert[:, :Wm].astype(np.float32), (wA, hA))
    cB = cv2.resize(cert[:, Wm:].astype(np.float32), (wB, hB))
    return dAB, dBA, cA, cB


# ---------------------------------------------------------------------------
# Class B: saliency alignment + control points
# ---------------------------------------------------------------------------

def salient_box(img):
    """Cheap saliency: gradient energy blurred, thresholded at its 70th
    percentile, largest blob's bounding box. Good enough to bring a face
    and a cloud roughly on top of each other; the control points do the
    rest. TODO(E9): replace with DINO/SAM saliency."""
    g = gray(img) if img.ndim == 3 else img
    e = cv2.magnitude(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
    e = cv2.GaussianBlur(e, (0, 0), max(3, min(g.shape) / 40))
    thr = np.percentile(e, 70)
    m = (e > thr).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n <= 1:
        h, w = g.shape
        return 0, 0, w, h
    i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    x, y, w, h = st[i, :4]
    return int(x), int(y), int(w), int(h)


def gray(img):
    return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)


def similarity_from_boxes(boxA, boxB):
    """2x3 similarity mapping A box center/size onto B's (uniform scale by
    the geometric mean of the size ratios)."""
    xa, ya, wa, ha = boxA
    xb, yb, wb, hb = boxB
    s = float(np.sqrt((wb / max(wa, 1)) * (hb / max(ha, 1))))
    s = float(np.clip(s, 0.3, 3.0))
    ca = np.array([xa + wa / 2, ya + ha / 2])
    cb = np.array([xb + wb / 2, yb + hb / 2])
    M = np.array([[s, 0, cb[0] - s * ca[0]], [0, s, cb[1] - s * ca[1]]], np.float64)
    return M


def mls_affine(p_src, p_dst, h, w, alpha=1.0, stride=8):
    """Moving Least Squares (affine) deformation, Schaefer et al. 2006.
    Returns a dense displacement (h, w, 2) mapping src grid -> dst, evaluated
    on a coarse grid and bilinearly upsampled (smoothness is a feature).
    p_src, p_dst: (n, 2) arrays of control points in pixels, n >= 3."""
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
    A = np.einsum("mn,mni,mnj->mij", wgt, ph, ph)        # (m, 2, 2)
    Bm = np.einsum("mn,mni,mnj->mij", wgt, ph, qh)
    A += np.eye(2)[None] * 1e-6
    M = np.linalg.solve(A, Bm)                           # (m, 2, 2)
    f = np.einsum("mi,mij->mj", v - pstar, M) + qstar
    disp = (f - v).reshape(len(ys), len(xs), 2).astype(np.float32)
    return cv2.resize(disp, (w, h), interpolation=cv2.INTER_LINEAR)


def _affine_to_disp(M, h, w):
    gx, gy = _grid(h, w)
    x2 = M[0, 0] * gx + M[0, 1] * gy + M[0, 2]
    y2 = M[1, 0] * gx + M[1, 1] * gy + M[1, 2]
    return np.stack([x2 - gx, y2 - gy], -1).astype(np.float32)


def _invert_disp(d):
    """Approximate inverse of a smooth displacement field by forward
    splatting -d, then filling gaps. Adequate for similarity/MLS fields."""
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
            inv[..., c] = cv2.inpaint((inv[..., c] * 16 + 32768).astype(np.uint16),
                                      hole, 5, cv2.INPAINT_TELEA).astype(np.float32)
            inv[..., c] = (inv[..., c] - 32768) / 16
    return cv2.GaussianBlur(inv, (0, 0), 2)


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

def dense_displacement(A, B, anchors=None, force_class=None, use_roma=True):
    """Returns dict: dAB, dBA (float32 HxWx2 px), wA, wB (certainty 0..1),
    cls ('A'|'B'), method, and diagnostics.

    anchors: optional (n,2)+(n,2) user control points (A px -> B px). In
    Class B they define the deformation (MLS); in Class A they are
    blended in as a correction on top of the dense field (E10)."""
    assert A.shape[:2] == B.shape[:2], "endpoints must share a canvas"
    h, w = A.shape[:2]
    gA, gB = gray(A), gray(B)
    sp = sparse_homography(gA, gB)
    cls = force_class
    if cls is None:
        cls = "A" if (sp and sp[1] >= MIN_INLIERS and _sane(sp[0], B.shape)) else "B"
    diag = {"sparse_inliers": sp[1] if sp else 0,
            "sparse_rmse": None if not sp else round(sp[2], 2)}

    if cls == "A":
        if use_roma and roma_available():
            dAB, dBA, wA, wB = _roma_displacements(A, B)
            method = "roma"
        else:
            H = sp[0] if (sp and _sane(sp[0], B.shape)) else np.eye(3)
            dAB = _homography_guided(gA, gB, H)
            dBA = _homography_guided(gB, gA, np.linalg.inv(H))
            wA, wB = consistency_weight(dAB, dBA), consistency_weight(dBA, dAB)
            method = "homography+dis"
        if anchors is not None and len(anchors[0]) >= 3:
            # blend user intent on top of the automatic field (E10)
            corr = mls_affine(anchors[0], anchors[1], h, w) - dAB
            dAB = dAB + 0.7 * corr
            dBA = _invert_disp(dAB)
            method += "+anchors"
    else:
        if anchors is not None and len(anchors[0]) >= 3:
            dAB = mls_affine(anchors[0], anchors[1], h, w)
            method = "mls-anchors"
        else:
            M = similarity_from_boxes(salient_box(A), salient_box(B))
            dAB = _affine_to_disp(M, h, w)
            method = "saliency-similarity"
        dBA = _invert_disp(dAB)
        wA = np.full((h, w), 0.5, np.float32)   # honest: no photometric proof
        wB = wA.copy()
    diag.update({"mean_certainty": round(float(wA.mean()), 3),
                 "median_disp_px": round(float(np.median(np.linalg.norm(dAB, axis=2))), 2)})
    return {"dAB": dAB, "dBA": dBA, "wA": wA, "wB": wB, "cls": cls,
            "method": method, "diag": diag}
