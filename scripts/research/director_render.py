"""The director's renderer (round 8, 2026-10-17; research only; imports transitions.py and the
layered probe for the canvas, the encoder, the optimal-transport field, the warp and the layer
source; changes nothing in either tool).

A plan (scripts/research/plans/SCHEMA.md) names a container in B, the anchors that attach A to it,
the camera's pull-back, the transforms of A's layers into things of B and the end effect. This
script resolves every name into pixels, renders the concept and writes the clip, a montage and
info.json with every resolved number.

What is new against nest_probe.py (the framing-only probe the owner graded on 2026-10-17):
- the sun is found by a circle fit to its limb, so a disc partly behind an object keeps its true
  centre and radius (the probe's brightest blob sat 130 px above the centre: "a bit off center");
- transforms inside the container: `recede` (a luminary contracts into the core), `line_to` (a
  band rotates and thins into a line), `morph_to` / `move_to` (a layer travels to a target with the
  target's pixels revealed inside the moving matte), `colour`, `hold`;
- a quad container with a homography camera (A sits in the glass plane of B's window);
- parallax by the depth model: each source's pull-back eases faster where the content is nearer,
  with both endpoints exact (z_p = z0^(1 - e^(1 - g (d_p - d_ref)))), so "Z depth" reads during the
  move without a cut at either end;
- a glass rim: B's own glass content over A at a small weight after the first frame.

Usage: director_render.py PLAN.json OUT_DIR [--concept c1] [--seconds 3] [--fps 30]
                          [--max-long 1920] [--set knob=value ...]
"""
import sys, json, math, argparse, hashlib, time
from pathlib import Path
import numpy as np, cv2

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts" / "research"))
import transitions as T
import layered_probe as LP
from nest_probe import smootherstep, cover_anchored, lab_transfer, luma_order, bright_disc

LAYERS = ROOT / "benchmarks/runs/2026-09-28/layers_v3"
MATTES = ROOT / "benchmarks/runs/2026-10-17/mattes"          # round 10: the matting model's alpha per element (matte_source.py)
MATTE_FALLBACKS = []
PHOTO = {"S": "_S", "F": "_F"}


# ----------------------------------------------------------------------------- small helpers
def ease01(u, t0, t1, kind="smootherstep"):
    if t1 <= t0:
        return 1.0 if u >= t1 else 0.0
    x = (u - t0) / (t1 - t0)
    if kind == "linear":
        return float(min(1.0, max(0.0, x)))
    return smootherstep(x)


def layer_e(u, lay):
    """A layer's progress in its window: smootherstep, or linear for a keyframe chain (round 11)."""
    return ease01(u, *lay["window"], kind=lay.get("ease", "smootherstep"))


def to3(M):
    return np.vstack([M, [0, 0, 1]]).astype(np.float64) if M.shape[0] == 2 else M.astype(np.float64)


def sim_about(s, cx, cy):
    """A 3x3 similarity that scales by s about (cx, cy)."""
    return np.array([[s, 0, cx - s * cx], [0, s, cy - s * cy], [0, 0, 1]], np.float64)


def lum(rgb):
    return cv2.cvtColor(np.ascontiguousarray(rgb, np.uint8), cv2.COLOR_RGB2LAB)[..., 0].astype(np.float32)


def feather(mask, sigma):
    return cv2.GaussianBlur(mask.astype(np.float32), (0, 0), sigma) if sigma > 0 else mask.astype(np.float32)


def box_of_mask(m):
    ys, xs = np.nonzero(m)
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def circle_fit(L, box, min_L, exclude_rows_from=None):
    """Least-squares circle through the boundary of the largest blob with L >= min_L inside box.
    Rows at or below exclude_rows_from (an occluder's top) are left out of the fit."""
    x0, y0, x1, y1 = [int(v) for v in box]
    sub = np.zeros(L.shape, bool); sub[y0:y1, x0:x1] = True
    m = ((L >= min_L) & sub).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    blob = (lab == k).astype(np.uint8)
    edge = blob - cv2.erode(blob, np.ones((3, 3), np.uint8))
    ys, xs = np.nonzero(edge)
    keep = np.ones(len(xs), bool)
    if exclude_rows_from is not None:
        keep &= ys < exclude_rows_from - 4
    rows = np.nonzero(blob.any(1))[0]; widths = blob.sum(1)
    if widths[rows[-1]] > 0.5 * widths.max():      # cut flat at the bottom (an occluder)
        keep &= ys < rows[-1] - 4
    if widths[rows[0]] > 0.5 * widths.max():       # cut flat at the top (the crop)
        keep &= ys > rows[0] + 4
    keep &= (xs > x0 + 2) & (xs < x1 - 3) & (ys > y0 + 2) & (ys < y1 - 3)
    xs, ys = xs[keep].astype(np.float64), ys[keep].astype(np.float64)
    for _round in range(3):
        A = np.stack([2 * xs, 2 * ys, np.ones_like(xs)], 1)
        b = xs ** 2 + ys ** 2
        sol, *_ = np.linalg.lstsq(A, b, rcond=None)
        cx, cy = sol[0], sol[1]
        r = math.sqrt(max(sol[2] + cx ** 2 + cy ** 2, 1.0))
        res = np.abs(np.hypot(xs - cx, ys - cy) - r)
        good = res <= max(2.0, 2.5 * float(np.median(res)))
        if good.sum() < 20 or good.all():
            break
        xs, ys = xs[good], ys[good]
    return (float(cx), float(cy)), float(r), {"fit_points": int(len(xs)), "fit_residual_px": round(float(res.mean()), 2), "blob_box": [int(v) for v in st[k][:4]]}


def line_fit(mask):
    """Principal axis of a thin mask: two end points on the mask's extent and the angle."""
    ys, xs = np.nonzero(mask)
    pts = np.stack([xs, ys], 1).astype(np.float64)
    c = pts.mean(0)
    u, s_, vt = np.linalg.svd(pts - c, full_matrices=False)
    d = vt[0]
    t = (pts - c) @ d
    p0, p1 = c + t.min() * d, c + t.max() * d
    if p0[0] > p1[0]:
        p0, p1 = p1, p0
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    width = float(2.0 * np.abs((pts - c) @ np.array([-d[1], d[0]])).mean())
    return p0, p1, ang, width


def dark_band(L, box, pct=25.0, sigma=6.0, wide=40.0):
    """The largest connected band inside box that is darker than its own surroundings (the
    difference of a narrow and a wide Gaussian of L under the box's pct-percentile): a dust lane
    inside a glow, not the darkest patch of the box (empty space is dark everywhere)."""
    x0, y0, x1, y1 = [int(v) for v in box]
    dog = cv2.GaussianBlur(L, (0, 0), sigma) - cv2.GaussianBlur(L, (0, 0), wide)
    sub = dog[y0:y1, x0:x1]
    thr = min(float(np.percentile(sub, pct)), -1.0)
    m = np.zeros(L.shape, np.uint8); m[y0:y1, x0:x1] = (sub < thr).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    return lab == k


# ----------------------------------------------------------------------------- the layer source
def layer_table(photo):
    return json.load(open(LAYERS / photo / "layers.json"))


def element_mask_ids(photo, ids, shift=(0, 0), shape=None):
    """Union of elements (ids) on the layer source's centred crop, shifted by (dx, dy) canvas px
    into another crop of the same scale; rows or columns the centred crop never saw are 0."""
    z = np.load(LAYERS / photo / "layers.npz")["element"]
    m = np.isin(z, list(ids))
    if shift == (0, 0) and (shape is None or shape == m.shape):
        return m
    H, W = shape if shape else m.shape
    out = np.zeros((H, W), bool)
    dx, dy = shift
    ys, xs = np.nonzero(m)
    xs2, ys2 = xs + dx, ys + dy
    ok = (xs2 >= 0) & (xs2 < W) & (ys2 >= 0) & (ys2 < H)
    out[ys2[ok], xs2[ok]] = True
    if dy > 0 and m[0].mean() > 0.5:          # the crop extends above what the source saw: the sky continues
        out[:dy] = m[0][None, :] if m.shape[1] == W else cv2.resize(m[0:1].astype(np.uint8), (W, 1), interpolation=cv2.INTER_NEAREST).astype(bool)
    if dy < 0 and m[-1].mean() > 0.5:
        out[H + dy:] = m[-1][None, :] if m.shape[1] == W else cv2.resize(m[-1:].astype(np.uint8), (W, 1), interpolation=cv2.INTER_NEAREST).astype(bool)
    return out


def element_mask_pred(photo, pred, shift=(0, 0), shape=None):
    ids = [e["id"] for e in layer_table(photo)["elements"] if pred(e)]
    return element_mask_ids(photo, ids, shift, shape)


def element_alpha_ids(photo, ids, shift=(0, 0), shape=None):
    """Round 10: the soft matte (float 0..1) of the union of elements (ids): the matting model's alpha
    (`MATTES/<photo>/el_<id>.png`, uint8 at the layer source's canvas, written by matte_source.py) where
    it exists, the hard element mask where it does not (recorded in MATTE_FALLBACKS, printed once as an
    INFO line). Shifted into another crop of the same scale like element_mask_ids."""
    z = np.load(LAYERS / photo / "layers.npz")["element"]
    a = np.zeros(z.shape, np.float32)
    for i in ids:
        f = MATTES / photo / f"el_{int(i)}.png"
        m = cv2.imread(str(f), cv2.IMREAD_GRAYSCALE) if f.exists() else None
        if m is not None and m.shape == z.shape:
            a = np.maximum(a, m.astype(np.float32) / 255.0)
            continue
        key = (photo, int(i))
        if key not in MATTE_FALLBACKS:
            MATTE_FALLBACKS.append(key)
            print(f"INFO matte: no soft matte for {photo} element {i} ({f.name}); the hard mask is used", file=sys.stderr)
        a = np.maximum(a, (z == i).astype(np.float32))
    if shift == (0, 0) and (shape is None or shape == a.shape):
        return a
    H, W = shape if shape else a.shape
    out = np.zeros((H, W), np.float32)
    dx, dy = shift
    ys0, ys1 = max(0, -dy), min(a.shape[0], H - dy); xs0, xs1 = max(0, -dx), min(a.shape[1], W - dx)
    if ys1 > ys0 and xs1 > xs0:
        out[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx] = a[ys0:ys1, xs0:xs1]
    if dy > 0 and a[0].mean() > 0.5:           # the crop extends above what the source saw: the sky continues
        row = a[0] if a.shape[1] == W else cv2.resize(a[0:1], (W, 1), interpolation=cv2.INTER_LINEAR)[0]
        out[:dy] = row[None, :]
    if dy < 0 and a[-1].mean() > 0.5:
        row = a[-1] if a.shape[1] == W else cv2.resize(a[-1:], (W, 1), interpolation=cv2.INTER_LINEAR)[0]
        out[H + dy:] = row[None, :]
    return out


def pull_push_fill(img, hole):
    """Fill `hole` (bool, True = unknown) of an RGB image by a pull-push pyramid: each level averages the known
    pixels under it, the coarsest fills the rest, and the way up keeps every known pixel and takes the coarser
    average where nothing is known. A smooth blend of the hole's surround with no direction of its own
    (cv2.inpaint's Telea marched a bow-tie into a 250 px sun disc from the dark deck below and the red sky above).
    A fill, not a generation."""
    w = (~hole).astype(np.float32)
    im = img.astype(np.float32) * w[..., None]
    ims, ws = [im], [w]
    while min(ims[-1].shape[:2]) > 4:
        ims.append(cv2.pyrDown(ims[-1])); ws.append(cv2.pyrDown(ws[-1]))
    up = ims[-1] / np.maximum(ws[-1], 1e-6)[..., None]
    for lvl in range(len(ims) - 2, -1, -1):
        up = cv2.resize(up, (ims[lvl].shape[1], ims[lvl].shape[0]), interpolation=cv2.INTER_LINEAR)
        wl = np.clip(ws[lvl], 0, 1)[..., None]
        known = ims[lvl] / np.maximum(ws[lvl], 1e-6)[..., None]
        up = known * wl + up * (1.0 - wl)
    out = img.astype(np.float32).copy(); out[hole] = up[hole]
    return out


FACE_MODEL = ROOT / "benchmarks/runs/2026-10-18/face/face_detection_yunet_2023mar.onnx"   # fetched once 2026-10-18; FACE_MANIFEST.json beside it
_FACE_DET = {"det": None, "missing": False}


def face_box(rgb, region=None):
    """The largest face YuNet (OpenCV's FaceDetectorYN, the model read offline from FACE_MODEL) finds, as
    (x, y, w, h, landmarks) with the five landmarks (eyes, nose, mouth corners) as an (5, 2) array; restricted to
    `region` (bool) when given; None when there is none or the model file is absent (an INFO line once).
    Used to align two faces before the flow of a keyframe chain. Deterministic."""
    if _FACE_DET["missing"]:
        return None
    if _FACE_DET["det"] is None:
        if not FACE_MODEL.exists():
            _FACE_DET["missing"] = True
            print(f"INFO face: no face model at {FACE_MODEL}; the chain runs without a face guide", file=sys.stderr)
            return None
        _FACE_DET["det"] = cv2.FaceDetectorYN.create(str(FACE_MODEL), "", (320, 320), 0.6, 0.3, 5000)
    det = _FACE_DET["det"]
    bgr = cv2.cvtColor(np.ascontiguousarray(rgb), cv2.COLOR_RGB2BGR)
    det.setInputSize((bgr.shape[1], bgr.shape[0]))
    _, faces = det.detect(bgr)
    best = None
    for f in (faces if faces is not None else []):
        x, y, w, h = [int(v) for v in f[:4]]
        if region is not None:
            cx, cy = min(region.shape[1] - 1, max(0, x + w // 2)), min(region.shape[0] - 1, max(0, y + h // 2))
            if not region[cy, cx]:
                continue
        if best is None or w * h > best[2] * best[3]:
            best = (x, y, w, h, np.array(f[4:14], np.float32).reshape(5, 2))
    return best


def is_soft(a):
    """True when an alpha carries a real edge band (more than 0.1 % of its pixels strictly between 0.02 and 0.98)."""
    return float(((a > 0.02) & (a < 0.98)).mean()) > 0.001


# ----------------------------------------------------------------------------- sampling
def sample_full(img_full, k, M3_img_to_frame, W, H, border=0, mask=None, replicate=False):
    """Sample a full-resolution image (its canvas px = full px / k) into the frame through the 3x3
    map M (image canvas -> frame). Minification goes through a pre-resize with INTER_AREA; a
    perspective map uses warpPerspective. mask: optional (H, W) 0-1 to sample along (returns both)."""
    M = M3_img_to_frame.copy()
    s = math.sqrt(abs(np.linalg.det(M[:2, :2]))) / k
    src = img_full
    if s < 1.0:
        src = cv2.resize(img_full, (max(1, int(round(img_full.shape[1] * s))), max(1, int(round(img_full.shape[0] * s)))), interpolation=cv2.INTER_AREA)
        ks = img_full.shape[1] / src.shape[1]
        M = M @ np.diag([ks / k, ks / k, 1.0])
    else:
        M = M @ np.diag([1.0 / k, 1.0 / k, 1.0])
    persp = abs(M[2, 0]) > 1e-12 or abs(M[2, 1]) > 1e-12 or abs(M[2, 2] - 1) > 1e-9
    bm = cv2.BORDER_REPLICATE if replicate else cv2.BORDER_CONSTANT
    if persp:
        return cv2.warpPerspective(src, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=bm, borderValue=border)
    return cv2.warpAffine(src, M[:2].astype(np.float32), (W, H), flags=cv2.INTER_LINEAR, borderMode=bm, borderValue=border)


def quad_distance(quad, X, Y):
    """Signed distance (px, positive inside) from the points (X, Y) to a convex quad given clockwise
    in image coordinates: the minimum over the four edges' half-planes."""
    q = np.asarray(quad, np.float64)
    d = None
    for i in range(4):
        x0, y0 = q[i]; x1, y1 = q[(i + 1) % 4]
        ex, ey = x1 - x0, y1 - y0
        L = math.hypot(ex, ey) + 1e-9
        # inside is to the right of the directed edge when the quad is clockwise in image coordinates (y down)
        di = ((Y - y0) * ex - (X - x0) * ey) / L
        d = di if d is None else np.minimum(d, di)
    return d.astype(np.float32)


def remap_img(img, mapx, mapy, border=cv2.BORDER_CONSTANT):
    return cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR, borderMode=border, borderValue=0)


# ----------------------------------------------------------------------------- the camera
class Camera:
    """camera(e): plate -> frame, with camera(0) = S_A^-1 (A fills the frame) and camera(1) = I.
    kind 'sim': a zoom about the fixed point q of S_A. kind 'homog': the four frame corners'
    plate pre-images move from the quad to the frame corners under the ease."""

    def __init__(self, S_A3, W, H, quad=None):
        self.S_A = S_A3
        self.W, self.H = W, H
        self.kind = "homog" if quad is not None else "sim"
        self.corners = np.array([[0, 0], [W, 0], [W, H], [0, H]], np.float64)
        if quad is None:
            s1 = float(S_A3[0, 0]); tx, ty = float(S_A3[0, 2]), float(S_A3[1, 2])
            if abs(1 - s1) < 1e-9:                      # no nesting: the camera is the identity
                self.q = np.array([W / 2.0, H / 2.0]); self.z0 = 1.0
            else:
                self.q = np.array([tx / (1 - s1), ty / (1 - s1)])
                self.z0 = 1.0 / s1
        else:
            self.quad = np.asarray(quad, np.float64)
            area_q = 0.5 * abs(np.dot(self.quad[:, 0], np.roll(self.quad[:, 1], -1)) - np.dot(self.quad[:, 1], np.roll(self.quad[:, 0], -1)))
            self.z0 = math.sqrt(W * H / max(area_q, 1.0))
            self.q = self.quad.mean(0)

    def zoom(self, e):
        return math.exp(math.log(self.z0) * (1 - e)) if self.z0 != 1.0 else 1.0

    def M(self, e):
        if self.kind == "sim":
            z = self.zoom(e)
            return sim_about(z, self.q[0], self.q[1])
        P = (1 - e) * self.quad + e * self.corners
        return cv2.getPerspectiveTransform(P.astype(np.float32), self.corners.astype(np.float32)).astype(np.float64)

    def inverse_map(self, e):
        """Plate coordinates of every frame pixel (mapx, mapy), float32 (H, W)."""
        Mi = np.linalg.inv(self.M(e))
        xx, yy = np.meshgrid(np.arange(self.W, dtype=np.float64), np.arange(self.H, dtype=np.float64))
        X = Mi[0, 0] * xx + Mi[0, 1] * yy + Mi[0, 2]
        Y = Mi[1, 0] * xx + Mi[1, 1] * yy + Mi[1, 2]
        Z = Mi[2, 0] * xx + Mi[2, 1] * yy + Mi[2, 2]
        return (X / Z).astype(np.float32), (Y / Z).astype(np.float32)


def parallax_map(mapx, mapy, e, cam, disp_plate, d_ref, gain, iters=2, push=0.0, push_floor=0.0):
    """Modulate the plate coordinates of each frame pixel by the plate's disparity (0 far .. 1 near)
    sampled at that point: nearer content eases faster, z_p = z0^(1 - e_p) with e_p = e + g (d - d_ref)
    e (1 - e), as an extra radial scale about the zoom centre q. Both endpoints exact (e = 0 and e = 1 give no change)
    unless `push` > 0: then near content is magnified a further exp(push (d - d_ref) (1 - e)^2) at
    the start, so what stands before the container (B's ceiling, sofas, a hand) lies beyond the
    frame at e = 0 and enters from the edges as the camera pulls back; the last frame is still exact."""
    if (gain <= 0.0 and push <= 0.0) or e >= 1.0 or disp_plate is None:
        return mapx, mapy
    z = cam.zoom(e)
    qx, qy = float(cam.q[0]), float(cam.q[1])
    px, py = mapx, mapy
    for _ in range(iters):
        d = cv2.remap(disp_plate, px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        # the per-pixel ease: e plus a bump g (d - d_ref) e (1 - e) that is zero at both ends with zero
        # slope at e = 0 (a power law there moved near pixels 4 px at frame 1: 9 levels on mismatch_3)
        ep = np.clip(e + gain * (d - d_ref) * e * (1.0 - e), 0.0, 1.0)
        zp = np.exp(np.log(cam.z0) * (1.0 - ep)) if cam.z0 != 1.0 else np.ones_like(d)
        if push > 0.0:
            zp = zp * np.exp(push * np.maximum(d - d_ref, push_floor) * (1.0 - e) ** 2)
        f = (z / zp).astype(np.float32)
        px = (qx + (mapx - qx) * f).astype(np.float32)
        py = (qy + (mapy - qy) * f).astype(np.float32)
    return px, py


# ----------------------------------------------------------------------------- the scene
class Scene:
    def __init__(self, plan, concept, max_long, knobs):
        self.plan, self.c, self.knobs = plan, concept, knobs
        pair = plan["pair"]
        S, F = LP.find_pair(pair)
        self.photoA, self.photoB = pair + "_S", pair + "_F"
        self.A_full, self.B_full = T.load_image_rgb(str(S)), T.load_image_rgb(str(F))
        W, H = T.common_canvas(self.A_full, self.B_full, max_long, "finish")
        self.W, self.H = W, H
        self.B = T.cover(self.B_full, W, H)
        same = abs(self.B_full.shape[1] / self.B_full.shape[0] - W / H) < 1e-6
        self.kB = self.B_full.shape[1] / W if same else 1.0
        self.B_src = self.B_full if same else self.B
        # the layer source's canvas (the tool's centred crop at 1920) and this canvas: one scale
        tabB = layer_table(self.photoB); self.lsW, self.lsH = tabB["canvas"]
        self.ls_scale = W / self.lsW
        self.info = {"canvas": [W, H], "ls_canvas": [self.lsW, self.lsH], "pair": pair, "concept": concept["id"]}
        self.LB = lum(self.B)
        self.orderB = luma_order(self.B)
        self.sky = {}
        self.anchors = {}
        self.A = None; self.shiftA = (0, 0)
        self.dark_alpha = None

    # --- coordinates of the plan (the layer source's canvas) -> this canvas
    def sc(self, v):
        return [float(x) * self.ls_scale for x in v]

    # --- B-side resolution
    def mask_B(self, spec):
        k = spec["kind"]
        W, H = self.W, self.H
        if k == "element":
            m = element_mask_ids(self.photoB, spec["ids"])
            return cv2.resize(m.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST).astype(bool) if m.shape != (H, W) else m
        if k == "box":
            x0, y0, x1, y1 = [int(round(v)) for v in self.sc(spec["box"])]
            m = np.zeros((H, W), bool); m[max(0, y0):y1, max(0, x0):x1] = True
            return m
        if k == "dark_band":
            return dark_band(self.LB, self.sc(spec["box"]), spec.get("pct", 25.0))
        if k == "line":
            if "ids" in spec:
                return self.mask_B({"kind": "element", "ids": spec["ids"]})
            p0, p1 = self.sc(spec["points"][0]), self.sc(spec["points"][1])
            m = np.zeros((H, W), np.uint8); cv2.line(m, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), 1, int(spec.get("width", 4)))
            return m.astype(bool)
        if k == "bright_disc":
            c, r = bright_disc(self.B, spec.get("frac", 0.8), [int(v) for v in self.sc(spec["box"])])
            yy, xx = np.mgrid[0:H, 0:W]
            return (xx - c[0]) ** 2 + (yy - c[1]) ** 2 <= r * r
        raise ValueError(f"B mask kind {k}")

    def point_B(self, spec):
        k = spec["kind"]
        if k == "bright_disc":
            c, r = bright_disc(self.B, spec.get("frac", 0.8), [int(v) for v in self.sc(spec["box"])])
            return np.array(c), r
        if k == "point":
            p = self.sc(spec["point"]); return np.array(p), float(spec.get("radius", 0) * self.ls_scale)
        m = self.mask_B(spec)
        ys, xs = np.nonzero(m)
        return np.array([xs.mean(), ys.mean()]), float(math.sqrt(len(xs) / math.pi))

    # --- A-side resolution (on A's crop of this canvas)
    def mask_A(self, spec):
        k = spec["kind"]; H, W = self.A.shape[:2]
        if k == "element":
            return element_mask_ids(self.photoA, spec["ids"], self.shiftA, (H, W)) if self.ls_scale == 1.0 else \
                cv2.resize(element_mask_ids(self.photoA, spec["ids"], self.shiftA_ls, (self.lsH, self.lsW)).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST).astype(bool)
        if k == "rows":
            y0, y1 = int(round(spec["from"] * self.ls_scale + self.shiftA[1])), int(round(spec["to"] * self.ls_scale + self.shiftA[1]))
            m = np.zeros((H, W), bool); m[max(0, y0):max(0, y1)] = True
            return m
        if k == "box":
            x0, y0, x1, y1 = [int(round(v)) for v in self.sc(spec["box"])]
            x0 += self.shiftA[0]; x1 += self.shiftA[0]; y0 += self.shiftA[1]; y1 += self.shiftA[1]
            m = np.zeros((H, W), bool); m[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = True
            return m
        if k == "disc":
            c, r = self.anchors[spec.get("anchor", "a0")]
            r = r * float(spec.get("scale", 1.0))
            yy, xx = np.mgrid[0:H, 0:W]
            return (xx - c[0]) ** 2 + (yy - c[1]) ** 2 <= r * r
        if k == "all":
            return np.ones((H, W), bool)
        if k == "dark_line":
            y0 = int(round(spec["rows"][0] * self.ls_scale + self.shiftA[1])); y1 = int(round(spec["rows"][1] * self.ls_scale + self.shiftA[1]))
            y0, y1 = max(0, y0), min(H, y1)
            # the row with the most pixels darker than the rows beside it (a thin wire is not the darkest row by
            # its median: the deck is)
            best, yl = -1.0, y0
            for y in range(max(12, y0), min(H - 12, y1)):
                ref_ = np.median(np.concatenate([self.LA[y - 10:y - 4], self.LA[y + 4:y + 10]], 0), axis=0)
                sc_ = float(((ref_ - self.LA[y]) > float(spec.get("contrast", 8.0))).mean())
                if sc_ > best:
                    best, yl = sc_, y
            t = int(spec.get("thickness", 7)); a, b = max(0, yl - t // 2), min(H, yl + t // 2 + 1)
            scores = {}
            for y in range(max(12, yl - 40), min(H - 12, yl + 41)):
                ref_ = np.median(np.concatenate([self.LA[y - 10:y - 4], self.LA[y + 4:y + 10]], 0), axis=0)
                scores[y] = float(((ref_ - self.LA[y]) > float(spec.get("contrast", 8.0))).mean())
            good = [y for y, v in scores.items() if v > 0.35 * best]
            a, b = min(a, min(good)), max(b, max(good) + 1)
            band = np.zeros((H, W), bool); band[a:b] = True
            above = self.LA[max(0, a - 12):max(1, a - 4)]; below = self.LA[min(H - 1, b + 4):min(H, b + 12)]
            ref = np.median(np.concatenate([above, below], 0), axis=0)[None, :] if (len(above) + len(below)) else np.median(self.LA, axis=1)[:, None]
            c_ = float(spec.get("contrast", 8.0))
            m = band & (self.LA < ref - c_)
            # round 10: the wire's alpha from its own pixels (how much darker than the rows beside it), not a band
            self.dark_alpha = (np.clip((ref - self.LA) / (2.0 * c_), 0, 1) * band).astype(np.float32)
            self.info.setdefault("dark_lines", []).append({"row": int(yl), "rows_searched": [y0, y1], "pixels": int(m.sum()), "share_darker": round(best, 3)})
            return m
        if k == "luma_above":
            return lum(self.A) >= float(spec["min_L"])
        raise ValueError(f"A mask kind {k}")

    def soft_A(self, spec):
        """Round 10: the soft matte (float 0..1) of an A-side spec on A's crop: the matting model's alpha for
        element kinds (the hard mask where no matte file exists), the hard mask as float for geometric kinds."""
        H, W = self.A.shape[:2]
        if spec.get("kind") == "element":
            if self.ls_scale == 1.0:
                return element_alpha_ids(self.photoA, spec["ids"], self.shiftA, (H, W))
            a = element_alpha_ids(self.photoA, spec["ids"], self.shiftA_ls, (self.lsH, self.lsW))
            return cv2.resize(a, (W, H), interpolation=cv2.INTER_LINEAR)
        return self.mask_A(spec).astype(np.float32)

    def soft_B(self, spec):
        if spec.get("kind") == "element":
            a = element_alpha_ids(self.photoB, spec["ids"])
            return cv2.resize(a, (self.W, self.H), interpolation=cv2.INTER_LINEAR) if a.shape != (self.H, self.W) else a
        return self.mask_B(spec).astype(np.float32)

    def resolve_A_anchor(self, spec, occluder_row=None):
        k = spec["kind"]
        if k == "circle_fit":
            box = [int(round(v)) for v in self.sc(spec["box"])]
            # a box that touched the source crop's top or bottom edge keeps touching this crop's edge
            # (the layer source never saw the rows an anchored crop adds)
            top0, bot0 = spec["box"][1] <= 0, spec["box"][3] >= self.lsH - 1
            box = [box[0] + self.shiftA[0], 0 if top0 else box[1] + self.shiftA[1], box[2] + self.shiftA[0], self.A.shape[0] if bot0 else box[3] + self.shiftA[1]]
            c, r, d = circle_fit(lum(self.A), box, float(spec.get("min_L", 120)), occluder_row)
            self.info["circle_fit"] = d
            return np.array(c), r
        if k == "point":
            p = self.sc(spec["point"]); return np.array([p[0] + self.shiftA[0], p[1] + self.shiftA[1]]), float(spec.get("radius", 0) * self.ls_scale)
        m = self.mask_A(spec)
        ys, xs = np.nonzero(m)
        return np.array([xs.mean(), ys.mean()]), float(math.sqrt(len(xs) / math.pi))

    # --- the crop of A, the anchors, the camera
    def build(self):
        c = self.c
        W, H = self.W, self.H
        cont = c.get("container") or {"kind": "none"}
        anchors = c.get("anchors", [])
        # B anchor first: it decides A's crop (A's anchor at the same relative height)
        if cont["kind"] == "disc" and anchors:
            b0 = anchors[0]["b"]
            cB, rB_blob = self.point_B(b0)
            # a disc container's radius: the plan's radius (ls px) or the b-anchor's
            rB = float(cont["spec"].get("radius", rB_blob)) * (self.ls_scale if "radius" in cont["spec"] else 1.0)
            # A's crop: the a-anchor at the same relative height as the core; a first pass on the
            # centred crop finds the anchor, the second pass re-crops
            A0 = T.cover(self.A_full, W, H)
            sA = max(W / self.A_full.shape[1], H / self.A_full.shape[0])
            sh = int(round(self.A_full.shape[0] * sA)); sw = int(round(self.A_full.shape[1] * sA))
            y0c, x0c = (sh - H) // 2, (sw - W) // 2
            self.A = A0; self.shiftA = (0, 0)
            a0 = anchors[0]["a"]
            occ = c.get("params", {}).get("occluder_row")
            occ_row = int(round(occ * self.ls_scale)) if occ else None
            cA0, rA = self.resolve_A_anchor(a0, occ_row)
            # the anchor in the scaled full image
            ax, ay = cA0[0] + x0c, cA0[1] + y0c
            self.A, cA = cover_anchored(self.A_full, W, H, (ax / sA, ay / sA), cB[1] / H)
            y0a = int(round(ay - cA[1])); x0a = int(round(ax - cA[0]))
            self.shiftA = (x0c - x0a, y0c - y0a)
            self.shiftA_ls = (int(round(self.shiftA[0] / self.ls_scale)), int(round(self.shiftA[1] / self.ls_scale)))
            occ_row = (occ_row + self.shiftA[1]) if occ_row else None
            cA, rA = self.resolve_A_anchor(a0, occ_row)
            self.anchors["a0"] = (cA, rA); self.anchors["b0"] = (cB, rB)
            p = {**c.get("params", {}), **c.get("pullback", {}).get("params", {})}
            s1 = float(self.knobs.get("end_scale", p.get("end_scale") or 0.0)) or rB / rA
            S_A = np.array([[s1, 0, cB[0] - s1 * cA[0]], [0, s1, cB[1] - s1 * cA[1]], [0, 0, 1]], np.float64)
            self.cam = Camera(S_A, W, H)
            self.info.update(A_anchor=[round(float(cA[0]), 1), round(float(cA[1]), 1)], A_r=round(rA, 1), B_anchor=[round(float(cB[0]), 1), round(float(cB[1]), 1)], B_r=round(rB, 1), end_scale=round(s1, 4), shiftA=list(self.shiftA), camera="sim")
        elif cont["kind"] in ("quad", "rect"):
            self.A = T.cover(self.A_full, W, H); self.shiftA = (0, 0); self.shiftA_ls = (0, 0)
            if cont["kind"] == "rect":
                x0, y0, x1, y1 = self.sc(cont["spec"]["box"])
                quad = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], np.float64)
            else:
                quad = np.array([self.sc(pt) for pt in cont["spec"]["points"]], np.float64)
            # B's front (what stands before the glass): by group, then kept only where it is nearer than
            # the container (the depth layer below); it becomes a layer of its own over an inpainted plate
            front = self.front_mask_B()
            # round 10: elements forced into B's front (the ceiling the depth margin dropped: "obscures part of the ceiling")
            self.front_ids = [int(v) for v in self.knobs.get("front_ids", cont.get("spec", {}).get("front_ids", []))]
            if self.front_ids:
                fm_ = element_mask_ids(self.photoB, self.front_ids)
                if fm_.shape != (H, W):
                    fm_ = cv2.resize(fm_.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST).astype(bool)
                front = front | fm_
            self.front = front
            # A's frame corners -> the quad: a homography (quad) or the similarity that fits the box
            src = np.array([[0, 0], [W, 0], [W, H], [0, H]], np.float32)
            if cont["kind"] == "rect":
                s1 = (x1 - x0) / W
                S_A = np.array([[s1, 0, x0], [0, s1, y0], [0, 0, 1]], np.float64)
                self.cam = Camera(S_A, W, H)
                self.S_A3 = S_A
            else:
                Hq = cv2.getPerspectiveTransform(src, quad.astype(np.float32)).astype(np.float64)
                self.S_A3 = Hq
                self.cam = Camera(Hq, W, H, quad=quad)
            self.quad = quad
            # the container matte in plate coordinates: the quad (the front composites over it as a layer)
            cm = np.zeros((H, W), np.uint8); cv2.fillConvexPoly(cm, quad.astype(np.int32), 1)
            intr = float((cm.astype(bool) & front).mean() / max(cm.mean(), 1e-6))
            self.quad_mask = cm.astype(bool)
            self.cont_feather_px = float(self.knobs.get("cont_feather", cont.get("params", {}).get("feather_px", 1.0)))
            self.cont_matte = feather(cm.astype(np.float32), 1.0)
            self.info.update(quad=[[round(float(v), 1) for v in pt] for pt in quad], front_in_quad_share=round(intr, 4), camera=self.cam.kind, start_zoom=round(self.cam.z0, 3))
        else:
            self.A = T.cover(self.A_full, W, H); self.shiftA = (0, 0); self.shiftA_ls = (0, 0)
            self.S_A3 = np.eye(3); self.cam = Camera(np.eye(3), W, H)
            self.front = self.front_mask_B()
            self.cont_matte = np.ones((H, W), np.float32)
        self.front_layer = None; self.B_plate = None
        if cont["kind"] == "disc":
            self.S_A3 = self.cam.S_A
            self.cB = cB
        self.cont = cont
        self.LA = lum(self.A)
        self.orderA = luma_order(self.A)
        self.A_f = self.A.astype(np.float32)
        # B in A's canvas coordinates (for the mix inside moving mattes): through S_A^-1
        Si = np.linalg.inv(self.S_A3)
        self.B_inA = sample_full(self.B_src, self.kB, Si, self.A.shape[1], self.A.shape[0])
        self.info.update(zoom_centre=[round(float(self.cam.q[0]), 1), round(float(self.cam.q[1]), 1)], start_zoom=round(self.cam.z0, 3))
        # depth (parallax)
        pl = c.get("pullback", {}).get("parallax", {"kind": "off"})
        self.parallax = None
        if pl.get("kind") == "depth" and float(pl.get("gain", 0)) > 0:
            srcs = self.knobs.get("parallax_sources", pl.get("sources", ["A", "B"]))
            g = float(self.knobs.get("parallax_gain", pl.get("gain", 0.3)))
            gA = float(self.knobs.get("parallax_gain_A", pl.get("gain_A", g)))
            blur_d = float(self.knobs.get("parallax_blur", pl.get("blur", 6.0)))
            dB = cv2.GaussianBlur(T.model_disparity(self.B), (0, 0), blur_d) if "B" in srcs else None
            dA = cv2.GaussianBlur(T.model_disparity(self.A), (0, 0), blur_d) if "A" in srcs else None
            # the reference disparity: the container's (far plane) on B; the a-anchor's on A
            if dB is not None:
                if hasattr(self, "cont_matte"):
                    refm = (self.cont_matte > 0.5) & ~self.front      # the container's far content, not what stands before it
                else:
                    yy, xx = np.mgrid[0:H, 0:W]; refm = (xx - self.cB[0]) ** 2 + (yy - self.cB[1]) ** 2 <= 60 ** 2
                dB_ref = float(dB[refm].mean()) if refm.any() else float(dB.mean())
            else:
                dB_ref = 0.0
            if dA is not None:
                if "a0" in self.anchors:
                    ca, ra = self.anchors["a0"]; yy, xx = np.mgrid[0:self.A.shape[0], 0:self.A.shape[1]]
                    refa = (xx - ca[0]) ** 2 + (yy - ca[1]) ** 2 <= ra * ra
                else:
                    refa = np.ones(dA.shape, bool)
                dA_ref = float(dA[refa].mean()) if refa.any() else float(dA.mean())
            else:
                dA_ref = 0.0
            # round 10: the parallax inside A confined to named elements (the bridge), the rest of A (the sky) at
            # the reference disparity, so no sky pixel is remapped ("vertical bands above the lamp posts")
            ae = self.knobs.get("parallax_A_elements", pl.get("a_elements"))
            if dA is not None and ae:
                wA_ = feather(self.soft_A({"kind": "element", "ids": [int(v) for v in ae]}), 8.0)
                dA = (dA_ref + (dA - dA_ref) * np.clip(wA_, 0, 1)).astype(np.float32)
                self.info["parallax_A_elements"] = [int(v) for v in ae]
            # A's disparity expressed on the plate (for the per-frame map of A)
            push = float(self.knobs.get("parallax_push", pl.get("push", 2.5 if self.cont["kind"] in ("quad", "rect") else 0.0)))
            self.parallax = {"gain": g, "gain_A": gA, "dB": dB, "dB_ref": dB_ref, "dA": dA, "dA_ref": dA_ref, "push": push,
                             "push_floor": float(self.knobs.get("push_floor", pl.get("push_floor", 0.3))),
                             "front_in": float(self.knobs.get("front_in", pl.get("front_in", 0.15)))}
            if dB is not None and self.cont["kind"] in ("quad", "rect"):
                # keep in the front only the elements nearer than the container by a margin (per element mean)
                margin = float(self.knobs.get("front_margin", self.cont.get("spec", {}).get("front_margin", 0.05)))
                z = np.load(LAYERS / self.photoB / "layers.npz")["element"]
                if z.shape != (H, W):
                    z = cv2.resize(z.astype(np.int32), (W, H), interpolation=cv2.INTER_NEAREST)
                keepf = np.zeros((H, W), bool); kept = []
                for eid in np.unique(z[self.front]):
                    m = (z == eid) & self.front
                    if m.sum() < 50:
                        continue
                    dm = float(dB[m].mean())
                    if int(eid) in getattr(self, "front_ids", []):
                        dm = max(dm, dB_ref + margin + 0.05)          # forced in front: it moves as the nearest of the far plane
                        keepf |= m; kept.append([int(eid), round(dm, 3), "forced"])
                    elif dm > dB_ref + margin:
                        keepf |= m; kept.append([int(eid), round(dm, 3)])
                self.front = keepf
                self.info["front_elements"] = kept
                # the front's disparity map: one value per element (the nearer wins at a border), so each
                # element moves as one piece and nothing inside it stretches
                dF = dB.copy()
                for eid, dm, *_ in sorted(kept, key=lambda t: t[1]):
                    m = cv2.dilate(((z == eid) & self.front).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
                    dF[m] = dm
                self.parallax["dF"] = dF
                self.build_front_layer()
            self.info.update(parallax={"gain": g, "push": push, "sources": srcs, "dB_ref": round(dB_ref, 3), "dA_ref": round(dA_ref, 3),
                                       "dB_range": [round(float(dB.min()), 3), round(float(dB.max()), 3)] if dB is not None else None,
                                       "dA_range": [round(float(dA.min()), 3), round(float(dA.max()), 3)] if dA is not None else None})
        if self.cont["kind"] in ("quad", "rect") and self.B_plate is None:
            self.build_front_layer()                     # parallax off: the front is a static layer over A
        self.build_layers()
        self.hide_targets_in_plate()

    def hide_targets_in_plate(self):
        """What a `line_to` layer becomes (B's streak) is taken out of the plate by a fill, so the line appears
        where the band lands and nowhere else; the render blends the plate back to B over the end effect."""
        lines = [tr for tr in self.c.get("transforms", []) if tr["by"] == "line_to" and tr["b"].get("kind") == "line" and tr.get("params", {}).get("hide_target", True)]
        if not lines:
            return
        m = np.zeros((self.H, self.W), np.uint8)
        for tr in lines:
            m |= self.mask_B(tr["b"]).astype(np.uint8)
        src = self.B_plate if self.B_plate is not None else self.B_src
        k = self.kB
        ms = cv2.resize(m, (src.shape[1], src.shape[0]), interpolation=cv2.INTER_NEAREST) if k != 1.0 else m
        ms = cv2.dilate(ms, np.ones((int(7 * k) | 1, int(7 * k) | 1), np.uint8))
        self.B_plate = cv2.inpaint(src, ms, 5, cv2.INPAINT_TELEA)
        self.info["plate_hidden_share"] = round(float(ms.mean()), 5)

    def build_front_layer(self):
        """B's front as a layer (its pixels and a feathered alpha) and the plate under it inpainted,
        at the source's resolution, so the front can enter from the frame's edge during the pull-back
        while the plate behind it shows no stretched pixels. Inpainting is a fill, not a generation."""
        H, W = self.H, self.W
        if not self.front.any():
            return
        fm = self.front.astype(np.uint8)
        fm = cv2.morphologyEx(fm, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
        holes = np.pad(fm, 1); ff = np.zeros((holes.shape[0] + 2, holes.shape[1] + 2), np.uint8)
        cv2.floodFill(holes, ff, (0, 0), 1)                      # the outside, seeded in the zero padding; what stays 0 is an enclosed hole
        enclosed = (holes[1:-1, 1:-1] == 0).astype(np.uint8)
        # only small holes are filled (a gap between a hand and a sofa); a large enclosed region is the glass view
        # between the ceiling and the sofas, and it is not in front (round 10: it entered over A as B's bushes)
        n_h, lab_h, st_h, _ = cv2.connectedComponentsWithStats(enclosed, 8)
        max_hole = float(self.knobs.get("front_hole_max", 0.005)) * H * W
        small = np.zeros_like(enclosed)
        for k_ in range(1, n_h):
            if st_h[k_, cv2.CC_STAT_AREA] <= max_hole:
                small[lab_h == k_] = 1
        self.info["front_holes"] = {"enclosed_share": round(float(enclosed.mean()), 4), "filled_share": round(float(small.mean()), 4)}
        fm = (fm | small).astype(np.uint8)
        self.front = fm.astype(bool)
        k = self.kB
        if k != 1.0:
            fm_src = cv2.resize(fm, (self.B_src.shape[1], self.B_src.shape[0]), interpolation=cv2.INTER_NEAREST)
        else:
            fm_src = fm
        grow = cv2.dilate(fm_src, np.ones((int(6 * k) | 1, int(6 * k) | 1), np.uint8))
        if str(self.knobs.get("plate_fill", "pullpush")) == "telea":
            small_k = max(1.0, self.B_src.shape[1] / 1280.0)          # inpaint at <= 1280 px wide, then upsample the fill
            if small_k > 1.0:
                bs = cv2.resize(self.B_src, (int(round(self.B_src.shape[1] / small_k)), int(round(self.B_src.shape[0] / small_k))), interpolation=cv2.INTER_AREA)
                gs = cv2.resize(grow, (bs.shape[1], bs.shape[0]), interpolation=cv2.INTER_NEAREST)
                filled = cv2.inpaint(bs, gs, 7, cv2.INPAINT_TELEA)
                filled = cv2.resize(filled, (self.B_src.shape[1], self.B_src.shape[0]), interpolation=cv2.INTER_LINEAR)
            else:
                filled = cv2.inpaint(self.B_src, grow, 7, cv2.INPAINT_TELEA)
            plate = self.B_src.copy(); plate[grow.astype(bool)] = filled[grow.astype(bool)]
        else:
            # round 11: a pull-push fill (smooth, no direction of its own); Telea's fill of a body was a flesh smear
            plate = np.clip(pull_push_fill(self.B_src, grow.astype(bool)), 0, 255).astype(np.uint8)
        self.B_plate = plate
        self.front_rgb = self.B_src
        # round 10: the front's alpha is the soft matte of its elements (the matting model), with the closing's and
        # the hole fill's additions kept as before, so a man's hair and a sofa's edge are not a cutout
        z = np.load(LAYERS / self.photoB / "layers.npz")["element"]
        zc = z if z.shape == (H, W) else cv2.resize(z.astype(np.int32), (W, H), interpolation=cv2.INTER_NEAREST)
        ids = [int(i) for i in np.unique(zc[self.front]) if i > 0 and ((zc == i) & self.front).sum() >= max(50, 0.5 * (zc == i).sum())]
        soft = element_alpha_ids(self.photoB, ids) if ids else np.zeros(z.shape, np.float32)
        if soft.shape != (H, W):
            soft = cv2.resize(soft, (W, H), interpolation=cv2.INTER_LINEAR)
        extra = (fm.astype(bool) & ~(np.isin(zc, ids) if ids else np.zeros((H, W), bool))).astype(np.float32)
        fa = np.maximum(soft, cv2.GaussianBlur(extra, (0, 0), 1.5))
        fa = np.clip(fa, 0, 1).astype(np.float32)
        self.front_alpha = cv2.resize(fa, (self.B_src.shape[1], self.B_src.shape[0]), interpolation=cv2.INTER_LINEAR) if k != 1.0 else fa
        self.info["front_share"] = round(float(self.front.mean()), 4)
        self.info["front_soft"] = bool(is_soft(fa))
        # round 11: one layer per front element (far to near), each with its own matte and its own depth, at the canvas
        if bool(self.knobs.get("front_per_element", True)) and ids:
            dmap = {int(e_[0]): float(e_[1]) for e_ in self.info.get("front_elements", [])}
            per = []
            for i in ids:
                a_i = element_alpha_ids(self.photoB, [i])
                if a_i.shape != (H, W):
                    a_i = cv2.resize(a_i, (W, H), interpolation=cv2.INTER_LINEAR)
                a_i = np.clip(a_i, 0, 1).astype(np.float32)
                if a_i.max() <= 0:
                    continue
                per.append({"id": int(i), "alpha": a_i, "d": dmap.get(int(i), float(self.parallax["dB"][zc == i].mean()) if self.parallax and self.parallax.get("dB") is not None else 0.0)})
            per.sort(key=lambda t: t["d"])          # far first, near last (composited last = on top)
            self.front_elements_layers = per
            self.info["front_per_element"] = len(per)

    def front_element_map(self, lay, e, cam, mapx, mapy):
        """The plate coordinates a front element samples from: the camera's map scaled about the zoom centre by this
        element's own depth (the same bump and push as parallax_map, with one disparity for the whole element)."""
        if self.parallax is None:
            return mapx, mapy
        d = lay["d"]; d_ref = self.parallax["dB_ref"]; gain = self.parallax["gain"]
        push = self.parallax["push"]; push_floor = self.parallax["push_floor"]
        z = cam.zoom(e)
        ep = min(1.0, max(0.0, e + gain * (d - d_ref) * e * (1.0 - e)))
        zp = math.exp(math.log(cam.z0) * (1.0 - ep)) if cam.z0 != 1.0 else 1.0
        if push > 0.0:
            zp = zp * math.exp(push * max(d - d_ref, push_floor) * (1.0 - e) ** 2)
        f = z / zp
        qx, qy = float(cam.q[0]), float(cam.q[1])
        return (qx + (mapx - qx) * f).astype(np.float32), (qy + (mapy - qy) * f).astype(np.float32)

    def front_mask_B(self):
        groups = self.cont.get("spec", {}).get("front_groups", ["person", "furniture", "ceiling", "wall", "object"]) if hasattr(self, "cont") else self.c.get("container", {}).get("spec", {}).get("front_groups", ["person", "furniture", "ceiling", "wall", "object"])
        m = element_mask_pred(self.photoB, lambda e: e["group"] in groups)
        if m.shape != (self.H, self.W):
            m = cv2.resize(m.astype(np.uint8), (self.W, self.H), interpolation=cv2.INTER_NEAREST).astype(bool)
        return m

    # --- layers (one per transform) in A's canvas coordinates
    def build_layers(self):
        c = self.c; H, W = self.A.shape[:2]
        self.layers = []
        self.unplaced = []
        covered = np.zeros((H, W), bool)
        covered_soft = np.zeros((H, W), np.float32)
        plate_union = np.zeros((H, W), np.uint8)              # round 10: what A is filled under (the lifted layers' footprints)
        use_plate = bool(self.knobs.get("plate", True))
        Si = np.linalg.inv(self.S_A3)
        trs = c.get("transforms", [])
        order = sorted(range(len(trs)), key=lambda i: 0 if trs[i].get("a", {}).get("kind") == "dark_line" else 1)
        built = {}
        for i_tr in order:
            tr = trs[i_tr]
            by = tr["by"]
            lay = {"name": tr["name"], "by": by, "window": tr.get("window", [0, 1]), "mix": tr.get("mix", "luma"), "params": dict(tr.get("params", {})), "depth": tr.get("depth", "inside")}
            lay["ease"] = tr.get("params", {}).get("ease", "linear" if by == "keyframe_chain" else "smootherstep")
            for k, v in self.knobs.items():
                if k.startswith(tr["name"] + "."):
                    key = k.split(".", 1)[1]
                    if key == "window":
                        lay["window"] = list(v)
                    elif key == "mix":
                        lay["mix"] = v
                    else:
                        lay["params"][key] = v
            p = lay["params"]
            if p.get("skip"):                      # an operator's cut ("name.skip=true"): the transform is left out, recorded
                self.unplaced.append({"name": tr["name"], "why": "skipped by the operator's knob"})
                continue
            if by == "colour":
                lay["maskA"] = self.mask_A(tr["a"]); lay["maskB"] = self.mask_B(tr["b"])
                lay["wsoft"] = feather(self.soft_A(tr["a"]), float(p.get("feather", 3.0)))      # round 10: a soft weight
                lay["weight"] = p.get("weight", "dark" if (c.get("container") or {}).get("kind") == "disc" else None)
                built[i_tr] = lay; continue
            if "a_group" in p or "a_elements" in p:
                ids = p.get("a_elements") or [e_["id"] for e_ in layer_table(self.photoA)["elements"] if e_["group"] == p["a_group"]]
                mA = self.mask_A({"kind": "element", "ids": ids})
                lay["a_override"] = {"ids": ids}
            elif tr["a"]["kind"] == "circle_fit":
                ca, ra = self.anchors["a0"]
                yy, xx = np.mgrid[0:H, 0:W]
                # the whole disc (its dark red limb included, so no second disc is left behind) but the silhouettes
                # across it (the deck, the lamp posts: L under min_L), which belong to their own layers or to the key
                mA = ((xx - ca[0]) ** 2 + (yy - ca[1]) ** 2 <= (ra * float(p.get("disc_scale", 1.02))) ** 2) & (self.LA >= float(p.get("min_L", 60)))
            else:
                mA = self.mask_A(tr["a"])
            # round 10: the layer's soft matte (the matting model's alpha for element kinds; the wire's own darkness)
            if "a_override" in lay:
                sA = self.soft_A({"kind": "element", "ids": lay["a_override"]["ids"]})
            elif tr["a"]["kind"] == "circle_fit":
                sA = mA.astype(np.float32)
            elif tr["a"]["kind"] == "dark_line" and self.dark_alpha is not None:
                sA = self.dark_alpha
            else:
                sA = self.soft_A(tr["a"])
            if tr["a"].get("exclude_covered", True):
                mA &= ~covered
                sA = (sA * (1.0 - covered_soft)).astype(np.float32)
            lay["soft"] = bool(is_soft(sA))
            plated = use_plate and bool(p.get("plate", True))
            if mA.sum() < 64:
                lay["unplaced"] = "the a-mask is empty on this crop"
                self.unplaced.append({"name": tr["name"], "why": lay["unplaced"]})
                continue
            if by == "hold":
                lay["alpha"] = sA if lay["soft"] else feather(mA.astype(np.float32), float(p.get("feather", 2.0)))
                built[i_tr] = lay; continue
            if by == "recede":
                ca, ra = self.anchors[tr["a"].get("anchor", "a0")]
                cb, rb = self.anchors["b0"]
                s1 = float(self.S_A3[0, 0])
                end_r_A = float(p.get("end_radius", 30.0)) * self.ls_scale / s1       # B px -> A canvas px
                lay.update(centre=ca, r=ra, k_end=min(1.0, end_r_A / ra), soften=float(p.get("soften", 0.0)))   # round 11: the ramp is the only radius
                disc = mA
                yy, xx = np.mgrid[0:H, 0:W]
                rr0 = np.hypot(xx - ca[0], yy - ca[1]) / max(1.0, ra)
                lay["rr0"] = rr0.astype(np.float32); lay["disc_f"] = disc.astype(np.float32)
                inner = disc & (rr0 < 0.7)
                mean_in = self.A_f[inner].mean(0) if inner.any() else self.A_f[disc].mean(0)
                lf = float(p.get("limb_flatten", 0.55))          # round 11: the limb levelled from the rim's start with a smooth weight (a linear one from 0.8 drew a paler inner disc in round 9)
                wflat = (np.clip((rr0 - lf) / max(1e-3, 1.0 - lf), 0, 1) if lf < 1.0 else np.zeros_like(rr0))
                wflat = (wflat * wflat * (3.0 - 2.0 * wflat))[..., None] * disc[..., None]
                lay["content"] = (self.A_f * (1 - wflat) + mean_in[None, None, :] * wflat).astype(np.float32)
                # round 10: a wide soft rim (alpha falls from rim_in to rim_out of the radius once the recede has started)
                lay["rim_in"], lay["rim_out"] = float(p.get("rim_in", 0.55)), float(p.get("rim_out", 1.0))
                lay["alpha0"] = feather(disc.astype(np.float32), 1.0)
                disc_full = rr0 <= float(p.get("disc_scale", 1.02))
                # the fitted circle plus the sun's own bright blob around it (an oblate sun is wider than its circle: the
                # left and right limbs outside the circle stayed in the base as bright crescents in round 9)
                blob = ((self.LA >= float(p.get("blob_L", 110))) & (rr0 <= float(p.get("blob_reach", 1.35)))).astype(np.uint8)
                n_, lab_, st_, _ = cv2.connectedComponentsWithStats(blob, 8)
                if n_ > 1:
                    kb = 1 + int(np.argmax(st_[1:, cv2.CC_STAT_AREA]))
                    bright = (lab_ == kb).astype(np.uint8)
                    # bridge the bright parts across the dark silhouettes between them (a vertical kernel of half the
                    # radius): the deck's chord joins the dome to the sliver under it; the truss below stays out
                    kh = max(3, int(0.5 * ra)) | 1; kw = max(3, int(0.08 * ra)) | 1
                    closed = cv2.morphologyEx(bright, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kw, kh)))
                    closed = cv2.morphologyEx(closed, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
                    blob = cv2.dilate(closed, np.ones((5, 5), np.uint8)).astype(bool) & (rr0 <= float(p.get("blob_reach", 1.35)))
                    circle_only = disc_full & ~blob
                    disc_full = blob if plated else (disc_full | blob)
                    lay["blob_share"] = round(float(blob.sum()) / max(1.0, float((rr0 <= 1.0).sum())), 4)
                    lay["circle_dropped_share"] = round(float(circle_only.sum()) / max(1.0, float((rr0 <= 1.0).sum())), 4)
                if plated:
                    lay["rr0"] = np.where(disc_full & (rr0 > 1.0), 1.0, rr0).astype(np.float32)     # the limb outside the circle counts as the limb
                covered |= disc_full if plated else disc           # with a plate the whole disc is the sun's (the chords fade into its fill)
                covered_soft = np.maximum(covered_soft, lay["alpha0"])
                if plated:
                    lay["foot_hard"] = cv2.dilate((disc_full | (rr0 <= float(p.get("plate_reach", 1.6)))).astype(np.uint8), np.ones((5, 5), np.uint8))   # the fill drawn from the glow at 1.6 r (the sky right at the limb is a dark red ring in A: a fill from 1.18 r was a dark trough)
                    plate_union |= lay["foot_hard"]
                built[i_tr] = lay; continue
            if by == "line_to":
                ca, _ = self.anchors[tr["a"].get("anchor", "a0")]
                mB = self.mask_B(tr["b"])
                p0, p1, ang, wB = line_fit(mB)
                # the target line in A's canvas coordinates
                q0 = Si @ np.array([p0[0], p0[1], 1.0]); q1 = Si @ np.array([p1[0], p1[1], 1.0])
                q0, q1 = q0[:2] / q0[2], q1[:2] / q1[2]
                ys, xs = np.nonzero(mA)
                band_rows = [int(ys.min()), int(ys.max()) + 1]
                thick = float(band_rows[1] - band_rows[0])
                yc = 0.5 * (band_rows[0] + band_rows[1])
                # the band's centre line passes through (ca.x, yc); the target passes through the foot of ca on the line
                d = (q1 - q0) / np.linalg.norm(q1 - q0)
                foot = q0 + np.dot(np.array([ca[0], yc]) - q0, d) * d if False else q0 + np.dot(np.array([ca[0], ca[1]]) - q0, d) * d
                # the pivot: the anchor; the band rotates about it and its centre line's offset from the
                # pivot (yc - ca.y, along the normal) shrinks to the target line's offset from the pivot
                n = np.array([-d[1], d[0]])
                off_end = float(np.dot(foot - np.array([ca[0], ca[1]]), n))
                lay.update(pivot=ca, theta=float(ang), off0=float(yc - ca[1]), off1=off_end, thick0=thick,
                           width_end=float(p.get("width", 4.0)) * self.ls_scale / float(self.S_A3[0, 0]), stretch=float(p.get("stretch", 1.0)), band_rows=band_rows)
                dark_wire = tr["a"]["kind"] == "dark_line" and self.dark_alpha is not None
                lay["alpha0"] = sA if dark_wire else feather(mA.astype(np.float32), 1.0)
                et_l = float(p.get("end_taper", 0.0 if dark_wire else 0.12))      # round 10: a wire keeps its ends (no taper band)
                if et_l > 0:
                    xs_ = np.arange(W, dtype=np.float32) / (W - 1)
                    taper = np.clip(np.minimum(xs_, 1 - xs_) / et_l, 0, 1)[None, :]
                    lay["alpha0"] = lay["alpha0"] * taper
                lay["content"] = self.A_f
                # B's pixels at the band's end position, in the band's own frame: M(1)^-1 applied to B_inA
                th1 = float(ang); off1 = off_end; sy1 = max(1e-3, lay["width_end"] / thick); sx1 = lay["stretch"]
                Tm1 = np.array([[1, 0, 0], [0, 1, -yc], [0, 0, 1]], np.float64); S1 = np.diag([sx1, sy1, 1.0])
                Tx1 = np.array([[1, 0, -ca[0]], [0, 1, 0], [0, 0, 1]], np.float64)
                R1 = np.array([[math.cos(th1), -math.sin(th1), 0], [math.sin(th1), math.cos(th1), 0], [0, 0, 1]], np.float64)
                Tp1 = np.array([[1, 0, ca[0]], [0, 1, ca[1]], [0, 0, 1]], np.float64); Off1 = np.array([[1, 0, 0], [0, 1, off1], [0, 0, 1]], np.float64)
                M1 = Tp1 @ R1 @ Off1 @ S1 @ Tx1 @ Tm1
                lay["targetB"] = cv2.warpAffine(self.B_inA, np.linalg.inv(M1)[:2].astype(np.float32), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                covered |= mA
                covered_soft = np.maximum(covered_soft, lay["alpha0"])
                if plated:
                    lay["foot_hard"] = cv2.dilate(mA.astype(np.uint8), np.ones((5, 5), np.uint8))
                    plate_union |= lay["foot_hard"]
                built[i_tr] = lay; continue
            if by in ("morph_to", "move_to"):
                mB = self.mask_B(tr["b"])
                lumA_n = self.LA / 255.0
                massmode_n = p.get("mass") or ("dark" if float(lumA_n[mA].mean()) < 0.35 else "bright")
                if p.get("alpha", "mass" if massmode_n == "dark" else "mask") == "mass":
                    lo_n, hi_n = (float(p.get("alpha_L", [0.12, 0.35])[0]), float(p.get("alpha_L", [0.12, 0.35])[1]))
                    wA_n = np.clip((hi_n - lumA_n) / (hi_n - lo_n), 0, 1) if massmode_n == "dark" else np.clip((lumA_n - lo_n) / (hi_n - lo_n), 0, 1)
                    carried = mA & (wA_n > 0.5)
                else:
                    wA_n = np.ones_like(lumA_n); carried = mA
                # the target mask in A's canvas coordinates (the layer's working frame may extend beyond A)
                bx = box_of_mask(mA)
                ysb, xsb = np.nonzero(mB)
                cornersB = np.array([[xsb.min(), ysb.min(), 1], [xsb.max() + 1, ysb.min(), 1], [xsb.max() + 1, ysb.max() + 1, 1], [xsb.min(), ysb.max() + 1, 1]], np.float64)
                cA_ = (Si @ cornersB.T).T; cA_ = cA_[:, :2] / cA_[:, 2:3]
                bxB = [float(cA_[:, 0].min()), float(cA_[:, 1].min()), float(cA_[:, 0].max()), float(cA_[:, 1].max())]
                m = float(p.get("margin", 0.15))
                x0 = min(bx[0], bxB[0]); y0 = min(bx[1], bxB[1]); x1 = max(bx[2], bxB[2]); y1 = max(bx[3], bxB[3])
                mw, mh = (x1 - x0) * m, (y1 - y0) * m
                ext = [int(math.floor(x0 - mw)), int(math.floor(y0 - mh)), int(math.ceil(x1 + mw)), int(math.ceil(y1 + mh))]
                ew, eh = ext[2] - ext[0], ext[3] - ext[1]
                wl = min(1.0, float(p.get("work_px", 3200)) / max(ew, eh))
                lw, lh = max(8, int(round(ew * wl))), max(8, int(round(eh * wl)))
                # the layer's working frame: A canvas -> work: translate by -ext, scale by wl
                Tw = np.array([[wl, 0, -ext[0] * wl], [0, wl, -ext[1] * wl], [0, 0, 1]], np.float64)
                contentA = cv2.warpAffine(self.A_f, Tw[:2].astype(np.float32), (lw, lh), flags=cv2.INTER_AREA if wl < 1 else cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                alphaA = cv2.warpAffine(sA, Tw[:2].astype(np.float32), (lw, lh), flags=cv2.INTER_LINEAR, borderValue=0)
                # B's content and the target matte in the working frame: B canvas -> A canvas (Si) -> work
                MB = Tw @ Si
                contentB = sample_full(self.B_src, self.kB, MB, lw, lh, replicate=True)
                sB = self.soft_B(tr["b"]) if tr["b"].get("kind") == "element" else mB.astype(np.float32)
                lay["soft_b"] = bool(is_soft(sB))
                alphaB = cv2.warpPerspective(sB, MB, (lw, lh), flags=cv2.INTER_LINEAR, borderValue=0) if abs(MB[2, 0]) + abs(MB[2, 1]) > 1e-12 else cv2.warpAffine(sB, MB[:2].astype(np.float32), (lw, lh), flags=cv2.INTER_LINEAR, borderValue=0)
                # the affine box -> box (a similarity on the boxes' centres and the geometric-mean size)
                bxa = box_of_mask(alphaA > 0.5); bxb = box_of_mask(alphaB > 0.5)
                ca_ = np.array([(bxa[0] + bxa[2]) / 2, (bxa[1] + bxa[3]) / 2]); cb_ = np.array([(bxb[0] + bxb[2]) / 2, (bxb[1] + bxb[3]) / 2])
                sx = (bxb[2] - bxb[0]) / max(1, bxa[2] - bxa[0]); sy = (bxb[3] - bxb[1]) / max(1, bxa[3] - bxa[1])
                yy, xx = np.mgrid[0:lh, 0:lw].astype(np.float32)
                mapmode = "axis" if p.get("rotate") else p.get("map", "box")
                if mapmode == "axis":
                    def pca(a):
                        ys_, xs_ = np.nonzero(a > 0.5); pts = np.stack([xs_, ys_], 1).astype(np.float64); c = pts.mean(0)
                        u_, s_, vt = np.linalg.svd(pts - c, full_matrices=False); d = vt[0]; n = np.array([-d[1], d[0]])
                        return c, math.atan2(d[1], d[0]), 2 * float(np.std((pts - c) @ d)), 2 * float(np.std((pts - c) @ n))
                    cA2, thA, lenA, widA = pca(alphaA); cB2, thB, lenB, widB = pca(alphaB)
                    if abs(thB - thA) > math.pi / 2:        # the same axis, the other way round
                        thB += math.pi if thB < thA else -math.pi
                    sl, sw = lenB / max(lenA, 1.0), widB / max(widA, 1.0)
                    Ra = np.array([[math.cos(-thA), -math.sin(-thA)], [math.sin(-thA), math.cos(-thA)]]); Rb = np.array([[math.cos(thB), -math.sin(thB)], [math.sin(thB), math.cos(thB)]])
                    Mx = Rb @ np.diag([sl, sw]) @ Ra
                    X = np.stack([xx - cA2[0], yy - cA2[1]], -1)
                    Xp = X @ Mx.T
                    Dx = (Xp[..., 0] + cB2[0] - xx).astype(np.float32); Dy = (Xp[..., 1] + cB2[1] - yy).astype(np.float32)
                    lay["axis"] = {"theta_a": round(math.degrees(thA), 1), "theta_b": round(math.degrees(thB), 1), "len": [round(lenA), round(lenB)], "wid": [round(widA), round(widB)]}
                else:
                    if mapmode == "box":
                        sx_, sy_ = sx, sy
                    else:
                        sx_ = sy_ = 1.0
                    if p.get("iso", True):
                        sx_ = sy_ = math.sqrt(sx_ * sy_)
                    Dx = ((cb_[0] + (xx - ca_[0]) * sx_) - xx).astype(np.float32); Dy = ((cb_[1] + (yy - ca_[1]) * sy_) - yy).astype(np.float32)
                D_aff = np.stack([Dx, Dy], -1).astype(np.float32)
                ot_w = float(p.get("ot_weight", 0.35 if mapmode == "axis" else 1.0))
                # the optimal-transport residual between the affinely placed mass and the target mass
                lumA = lum(np.clip(contentA, 0, 255).astype(np.uint8)) / 255.0; lumB = lum(np.clip(contentB, 0, 255).astype(np.uint8)) / 255.0
                massmode = p.get("mass") or ("dark" if float(lumA[alphaA > 0.5].mean()) < 0.35 else "bright")
                mass_a = (alphaA * (lumA if massmode == "bright" else (1 - lumA))).astype(np.float32)
                mass_b = (alphaB * (lumB if massmode == "bright" else (1 - lumB))).astype(np.float32)
                if p.get("alpha", "mass" if massmode == "dark" else "mask") == "mass":
                    lo, hi = (float(p.get("alpha_L", [0.12, 0.35])[0]), float(p.get("alpha_L", [0.12, 0.35])[1]))
                    wA = np.clip((hi - lumA) / (hi - lo), 0, 1) if massmode == "dark" else np.clip((lumA - lo) / (hi - lo), 0, 1)
                    alphaA = (alphaA * cv2.GaussianBlur(wA, (0, 0), 1.0)).astype(np.float32)
                    wB = np.clip((hi - lumB) / (hi - lo), 0, 1) if massmode == "dark" else np.clip((lumB - lo) / (hi - lo), 0, 1)
                    alphaB = (alphaB * cv2.GaussianBlur(wB, (0, 0), 1.0)).astype(np.float32)
                fpx_l = float(p.get("feather", 0.0))
                if fpx_l > 0:                                   # the operator's feather, on top of a hard mask only
                    alphaA = alphaA if lay["soft"] else feather(alphaA, fpx_l)
                    alphaB = alphaB if lay.get("soft_b") else feather(alphaB, fpx_l)
                et_ = float(p.get("end_taper", 0.0))
                if et_ > 0:
                    xs_t = (np.arange(lw, dtype=np.float32) - (-ext[0] * wl)) / max(1.0, W * wl)   # A's canvas x in 0..1 inside the work frame
                    alphaA = alphaA * np.clip(np.minimum(xs_t, 1 - xs_t) / et_, 0, 1)[None, :]
                if by == "morph_to":
                    placed = LP.warp_along(mass_a, D_aff, 1.0, exact=True)
                    f_ab, f_ba, oti = LP.ot_fields(placed, mass_b, grid=int(p.get("ot_grid", 64)), eps=float(p.get("ot_eps", 0.04)))
                    # the residual lives at the placed position: read it where each source pixel lands
                    rx = cv2.remap(f_ab[..., 0], xx + Dx, yy + Dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                    ry = cv2.remap(f_ab[..., 1], xx + Dx, yy + Dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                    D = np.stack([Dx + ot_w * rx, Dy + ot_w * ry], -1).astype(np.float32)
                    lay["ot"] = {**oti, "weight": ot_w}
                else:
                    D = D_aff
                lay.update(ext=ext, wl=wl, Tw=Tw, contentA=contentA, alphaA=alphaA, contentB=contentB, alphaB=alphaB, D=D, D_aff=D_aff, massmode=massmode,
                           orderA=luma_order(np.clip(contentA, 0, 255).astype(np.uint8)))
                if hasattr(self, "cont_matte") and tr.get("depth") is None:
                    inside_share = float((self.cont_matte > 0.5)[mB].mean()) if mB.any() else 1.0
                    lay["depth"] = "inside" if inside_share >= 0.5 else "front"
                    lay["target_inside_share"] = round(inside_share, 3)
                dist = cv2.distanceTransform((alphaA > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
                lay["edge"] = (1.0 - np.clip(dist / max(1.0, float(dist.max())), 0, 1)).astype(np.float32)   # the rim first
                lay["noise"] = cv2.GaussianBlur(np.random.RandomState(int(p.get("seed", 7))).rand(lh, lw).astype(np.float32), (0, 0), float(p.get("noise_px", 24)))
                lay["noise"] = (lay["noise"] - lay["noise"].min()) / max(1e-6, lay["noise"].max() - lay["noise"].min())
                if p.get("alpha", "mass" if massmode_n == "dark" else "mask") == "mass":
                    lay["alpha_native"] = (sA * cv2.GaussianBlur(wA_n.astype(np.float32), (0, 0), 1.0)).astype(np.float32)
                else:
                    lay["alpha_native"] = sA if lay["soft"] else feather(carried.astype(np.float32), 1.0)
                covered |= carried
                covered_soft = np.maximum(covered_soft, lay["alpha_native"])
                if plated:
                    lay["foot_hard"] = cv2.dilate(carried.astype(np.uint8), np.ones((5, 5), np.uint8))
                    plate_union |= lay["foot_hard"]
                built[i_tr] = lay; continue
            if by == "exit":
                direction = p.get("direction", "left"); fade = float(p.get("fade", 0.3))
                ys, xs = np.nonzero(mA)
                margin = 24
                dx, dy = 0.0, 0.0
                if direction == "left": dx = -(xs.max() + margin)
                elif direction == "right": dx = (W - xs.min()) + margin
                elif direction == "up": dy = -(ys.max() + margin)
                else: dy = (H - ys.min()) + margin
                lay.update(dx=float(dx), dy=float(dy), fade=fade)
                lay["alpha0"] = sA if lay["soft"] else feather(mA.astype(np.float32), float(p.get("feather", 1.5)))
                lay["content"] = self.A_f
                covered |= mA
                covered_soft = np.maximum(covered_soft, lay["alpha0"])
                if plated:
                    lay["foot_hard"] = cv2.dilate(mA.astype(np.uint8), np.ones((5, 5), np.uint8))
                    plate_union |= lay["foot_hard"]
                built[i_tr] = lay; continue
            if by == "keyframe_chain":
                # round 10 (items 3-4): generated keyframes inside the layer's matte. The chain A -> k_1 .. k_n -> B is
                # rendered by the tool's own morph between consecutive pictures (a box affine as the guide on the first
                # segment, DIS flow for the rest, forward splats with consistency weights, a linear mix), inside a matte
                # that travels with the content from A's soft matte to B's. The keyframes are helpers under the owner's
                # 2026-09-29 conditions; the page says they are generated.
                kfs = p.get("keyframes", [])
                if not kfs:
                    lay["unplaced"] = "no keyframes named"; self.unplaced.append({"name": tr["name"], "why": lay["unplaced"]}); continue
                frame_kind = p.get("frame", "canvas")
                imgs = [self.A_f]
                for kf in kfs:
                    path = (ROOT / kf) if not str(kf).startswith("/") else Path(kf)
                    kimg = T.load_image_rgb(str(path))
                    if frame_kind == "A":                     # the keyframe is in A's own geometry (the pane)
                        kimg = cv2.resize(kimg, (W, H), interpolation=cv2.INTER_AREA if kimg.shape[1] > W else cv2.INTER_LINEAR)
                        imgs.append(kimg.astype(np.float32))
                    else:                                     # the keyframe is the pair's canvas (B's layout): into A's coordinates like B_inA
                        kimg = cv2.resize(kimg, (self.W, self.H), interpolation=cv2.INTER_AREA if kimg.shape[1] > self.W else cv2.INTER_LINEAR)
                        imgs.append(sample_full(kimg, 1.0, Si, W, H, replicate=True).astype(np.float32))
                imgs.append(self.B_inA.astype(np.float32))
                whole = tr["a"]["kind"] == "all"
                sB_full = self.soft_B(tr["b"]) if tr.get("b") else np.ones((self.H, self.W), np.float32)
                sB_inA = np.ones((H, W), np.float32) if whole else np.clip(sample_full(sB_full, 1.0, Si, W, H), 0, 1)
                # the guide of the first segment: A's matte box -> B's matte box (a similarity on the boxes' centres and the
                # geometric-mean size); the identity when the layer is the whole frame
                if whole or (sB_inA > 0.5).sum() < 64:
                    Mg = np.eye(3)
                else:
                    bxa = box_of_mask(sA > 0.5); bxb = box_of_mask(sB_inA > 0.5)
                    sg = math.sqrt(((bxb[2] - bxb[0]) / max(1, bxa[2] - bxa[0])) * ((bxb[3] - bxb[1]) / max(1, bxa[3] - bxa[1])))
                    ca_ = np.array([(bxa[0] + bxa[2]) / 2, (bxa[1] + bxa[3]) / 2]); cb_ = np.array([(bxb[0] + bxb[2]) / 2, (bxb[1] + bxb[3]) / 2])
                    Mg = np.array([[sg, 0, cb_[0] - sg * ca_[0]], [0, sg, cb_[1] - sg * ca_[1]], [0, 0, 1]], np.float64)
                segs = []
                mattes = [sA]
                lead = bool(p.get("lead", True)) and not whole and not np.allclose(Mg, np.eye(3))
                if lead and bool(p.get("face_guide", True)) and len(imgs) > 2:
                    fA = face_box(np.clip(imgs[0], 0, 255).astype(np.uint8), sA > 0.5)
                    fK = face_box(np.clip(imgs[1], 0, 255).astype(np.uint8), cv2.dilate((sB_inA > 0.3).astype(np.uint8), np.ones((int(0.1 * W) | 1,) * 2, np.uint8)).astype(bool))
                    if fA is not None and fK is not None:
                        M2, _ = cv2.estimateAffinePartial2D(fA[4], fK[4], method=cv2.LMEDS)
                        if M2 is not None and np.isfinite(M2).all() and 0.3 < math.hypot(M2[0, 0], M2[1, 0]) < 3.0:
                            # keep the similarity's scale and translation, drop its rotation (a head tilt must not tilt the body)
                            sc_ = math.hypot(M2[0, 0], M2[1, 0]); cA_ = fA[4].mean(0); cK_ = fK[4].mean(0)
                            Mg = np.array([[sc_, 0, cK_[0] - sc_ * cA_[0]], [0, sc_, cK_[1] - sc_ * cA_[1]], [0, 0, 1]], np.float64)
                            lay["lead_guide"] = "faces"
                if lead:
                    # segment 0: A's layer moved by the guide (the renderer's own rigid move, exact field, no residual, no mix)
                    gx_, gy_ = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
                    Dg = np.stack([(Mg[0, 0] * gx_ + Mg[0, 1] * gy_ + Mg[0, 2]) - gx_, (Mg[1, 0] * gx_ + Mg[1, 1] * gy_ + Mg[1, 2]) - gy_], -1).astype(np.float32)
                    Mi_ = np.linalg.inv(Mg)
                    Dgi = np.stack([(Mi_[0, 0] * gx_ + Mi_[0, 1] * gy_ + Mi_[0, 2]) - gx_, (Mi_[1, 0] * gx_ + Mi_[1, 1] * gy_ + Mi_[1, 2]) - gy_], -1).astype(np.float32)
                    moved = cv2.warpAffine(self.A_f, Mg[:2].astype(np.float32), (W, H), flags=cv2.INTER_AREA if Mg[0, 0] < 1 else cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                    moved_m = np.clip(cv2.warpAffine(sA, Mg[:2].astype(np.float32), (W, H), flags=cv2.INTER_LINEAR), 0, 1)
                    imgs.insert(1, moved.astype(np.float32)); mattes.append(moved_m)
                    # the matte of every later node: the moved man joined with B's man, dilated by `matte_grow` of the
                    # width, so a keyframe's wider shoulders or a turned head are never cut by the matte's edge
                    g_ = int(round(float(p.get("matte_grow", 0.03)) * W)) | 1
                    union = np.maximum(moved_m, sB_inA)
                    union = cv2.dilate((union > 0.3).astype(np.uint8), np.ones((g_, g_), np.uint8)).astype(np.float32)
                    union = feather(union, max(1.0, 0.3 * g_))
                    chain_matte = np.clip(union, 0, 1).astype(np.float32)
                    segs.append({"dAB": Dg, "dBA": Dgi, "wA": np.ones((H, W), np.float32), "wB": np.ones((H, W), np.float32), "lead": True,
                                 "disp_median_px": round(float(np.median(np.linalg.norm(Dg, axis=2)[sA > 0.5])) if (sA > 0.5).any() else 0.0, 1)})
                face_guide = bool(p.get("face_guide", not whole))
                faces = []
                for j in range(1 if lead else 0, len(imgs) - 1):
                    gP = T.gray_of(np.clip(imgs[j], 0, 255).astype(np.uint8)); gQ = T.gray_of(np.clip(imgs[j + 1], 0, 255).astype(np.uint8))
                    Hg = Mg if (j == 0 and not whole and bool(p.get("guide", True))) else np.eye(3)
                    if face_guide and j >= (1 if lead else 0):
                        # round 11: align the faces before the flow (a similarity from the face box of P to the face box of Q,
                        # found by OpenCV's bundled Haar cascade inside the chain's matte); without it two faces dissolve unaligned
                        region = (chain_matte if lead else sA) > 0.5
                        fP = face_box(np.clip(imgs[j], 0, 255).astype(np.uint8), region); fQ = face_box(np.clip(imgs[j + 1], 0, 255).astype(np.uint8), region)
                        if fP is not None and fQ is not None:
                            # a similarity from the five landmarks of P to those of Q (the box's centre and size as the fallback)
                            M2, _ = cv2.estimateAffinePartial2D(fP[4], fQ[4], method=cv2.LMEDS)
                            if M2 is not None and np.isfinite(M2).all() and 0.5 < math.hypot(M2[0, 0], M2[1, 0]) < 2.0:
                                Hg = np.vstack([M2, [0, 0, 1]]).astype(np.float64)
                            else:
                                sgf = fQ[2] / max(1.0, fP[2])
                                cPx, cPy = fP[0] + fP[2] / 2, fP[1] + fP[3] / 2; cQx, cQy = fQ[0] + fQ[2] / 2, fQ[1] + fQ[3] / 2
                                Hg = np.array([[sgf, 0, cQx - sgf * cPx], [0, sgf, cQy - sgf * cPy], [0, 0, 1]], np.float64)
                        faces.append({"segment": j, "P": [int(v) for v in fP[:4]] if fP else None, "Q": [int(v) for v in fQ[:4]] if fQ else None})
                    dPQ = T._homography_guided(gP, gQ, np.linalg.inv(Hg)); dQP = T._homography_guided(gQ, gP, Hg)
                    wPQ = T.consistency_weight(dPQ, dQP); wQP = T.consistency_weight(dQP, dPQ)
                    damp = float(p.get("damp", 0.5 if face_guide else 1.0))
                    if damp > 0:
                        sPQ = cv2.GaussianBlur(wPQ, (0, 0), 12.0); sQP = cv2.GaussianBlur(wQP, (0, 0), 12.0)
                        dPQ = (dPQ * (1.0 - damp * (1.0 - sPQ))[..., None]).astype(np.float32)
                        dQP = (dQP * (1.0 - damp * (1.0 - sQP))[..., None]).astype(np.float32)
                    m_here = mattes[-1] if lead or j > 0 else sA
                    segs.append({"dAB": dPQ, "dBA": dQP, "wA": wPQ, "wB": wQP,
                                 "disp_median_px": round(float(np.median(np.linalg.norm(dPQ, axis=2)[m_here > 0.5])) if (m_here > 0.5).any() else 0.0, 1)})
                # the matte at every node: A's, then (after a lead) the union matte for every keyframe and B; without a lead
                # the matte is carried forward along each segment and B's matte closes the chain
                if lead:
                    while len(mattes) < len(imgs):
                        mattes.append(chain_matte)
                else:
                    for j in range(0, len(segs) - 1):
                        mw_, cov_ = T.forward_splat(mattes[-1], segs[j]["dAB"], 1.0, segs[j]["wA"])
                        mw_ = T.fill_holes(mw_, cov_, T.backward_warp(mattes[-1], -segs[j]["dAB"]).astype(np.float32), T.TCFG["hole_thresh"])
                        mattes.append(np.clip(cv2.GaussianBlur(mw_, (0, 0), 1.0), 0, 1).astype(np.float32))
                    mattes.append(sB_inA)
                n_seg = len(segs)
                times = [float(t) for t in (p.get("times") or [(j + 1) / n_seg for j in range(n_seg - 1)])]
                if len(times) != n_seg - 1:
                    times = [(j + 1) / n_seg for j in range(n_seg - 1)]
                    print(f"INFO chain: {tr['name']} has {n_seg} segments; the plan's times do not fit and were spaced evenly", file=sys.stderr)
                lay.update(imgs=imgs, segs=segs, mattes=mattes, times=times, keyframes=[str(k) for k in kfs], frame_kind=frame_kind,
                           alpha_native=sA, whole=whole)
                lay["chain"] = {"keyframes": [str(k) for k in kfs], "frame": frame_kind, "times": times, "lead": lead, "lead_guide": lay.get("lead_guide", "boxes"), "depth": lay["depth"], "faces": faces, "guide": [[round(float(v), 3) for v in r] for r in Mg[:2]],
                                "segments": [{"disp_median_px": sg_["disp_median_px"], "lead": bool(sg_.get("lead", False)),
                                              "consistency_mean": round(float(sg_["wA"][mattes[min(i_, len(mattes) - 1)] > 0.5].mean()) if (mattes[min(i_, len(mattes) - 1)] > 0.5).any() else 0.0, 3)} for i_, sg_ in enumerate(segs)]}
                covered |= sA > 0.5
                covered_soft = np.maximum(covered_soft, sA)
                if plated and not whole:
                    lay["foot_hard"] = cv2.dilate((sA > 0.5).astype(np.uint8), np.ones((5, 5), np.uint8))
                    plate_union |= lay["foot_hard"]
                built[i_tr] = lay; continue
            raise ValueError(f"transform kind {by}")
        self.layers = [built[i] for i in range(len(trs)) if i in built]      # the plan's order for compositing
        self.covered = covered
        self.info["unplaced"] = self.unplaced
        # round 10: A is filled under the lifted layers' footprints (cv2.inpaint, Telea, at <= 1280 px; a fill, not a
        # generation), so a layer that moves away uncovers A's own surround and not a hard-cut silhouette of B; the
        # rest's alpha is 1 there. A layer rendered without a plate (name.plate=false) keeps the hole.
        self.A_base = self.A_f
        self.rest_soft = np.ones((H, W), np.float32)
        for lay in self.layers:
            if lay["by"] == "colour":
                continue
            if not (use_plate and bool(lay["params"].get("plate", True))):
                nat = lay.get("alpha_native", lay.get("alpha0", lay.get("alpha")))
                if nat is not None:
                    self.rest_soft = self.rest_soft * (1.0 - np.clip(nat, 0, 1))
        if plate_union.any():
            A8 = np.clip(self.A_f, 0, 255).astype(np.uint8)
            grow = cv2.dilate(plate_union, np.ones((7, 7), np.uint8))
            gb = grow.astype(bool)
            self.A_base = pull_push_fill(A8, gb)
            self.info["plate_A_share"] = round(float(gb.mean()), 4)
            for lay in self.layers:
                if lay["by"] == "colour" or not (use_plate and bool(lay["params"].get("plate", True))):
                    continue
                # under a soft rim (a disc container) the keyed sky already gives way to B dark-first, so a departed layer's
                # footprint keys with it; a separate hole reveal there cut a dark slot into the glow
                lay["hole_reveal"] = bool(lay["params"].get("hole_reveal", (lay["by"] in ("exit", "morph_to", "move_to", "keyframe_chain") and self.cont["kind"] != "disc") or lay["by"] == "recede"))
                # the recede's vacated ring shows the core's glow at once (A's sky right at the limb is a dark red halo, so any
                # fill of it is a dark ring); other layers' holes open after a tenth of their window
                lay["hole_from"] = float(lay["params"].get("hole_from", 0.0 if lay["by"] == "recede" else 0.1))
                lay["hole_over"] = float(lay["params"].get("hole_over", 0.15 if lay["by"] == "recede" else 0.35))
                if lay["by"] == "recede":
                    # the whole disc, silhouettes included: the OTHER layers' chords across it (the deck, the wire) are
                    # filled from the disc's own pixels (the deck layer still carries the chord's dark pixels over it)
                    disc_full = lay["rr0"] <= float(lay["params"].get("disc_scale", 1.02))
                    lay["disc_f"] = disc_full.astype(np.float32); lay["alpha0"] = feather(lay["disc_f"], 1.0)
                    others = (plate_union & ~lay.get("foot_hard", np.zeros_like(plate_union))).astype(np.uint8)
                    chord = (others.astype(bool) & cv2.dilate(disc_full.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)).astype(np.uint8)
                    # the silhouettes across the disc that no other layer carries (the deck's chord): filled from the disc's
                    # own pixels, blended in over the first part of the recede (content0 -> content), so frame 1 is A
                    dark_in = disc_full & (self.LA < float(lay["params"].get("min_L", 60)))
                    chord = (chord.astype(bool) | dark_in).astype(np.uint8)
                    content = A8.copy()
                    if chord.any():
                        cb = cv2.dilate(chord, np.ones((5, 5), np.uint8)).astype(bool)
                        content_f = cv2.inpaint(A8, cb.astype(np.uint8), 7, cv2.INPAINT_TELEA)
                        content[cb] = content_f[cb]
                        lay["chord_share"] = round(float(cb.mean()), 5)
                    lay["content0"] = self.A_f.copy()
                    lay["content"] = content.astype(np.float32)
                    lay["fill_in"] = float(lay["params"].get("fill_in", 0.3))
                    lay["foot"] = feather(lay["foot_hard"].astype(np.float32), max(2.0, 0.5 * float(lay["r"])))    # the plate's circle must not show (0.08 r still did)
                else:
                    nat = lay.get("alpha_native", lay.get("alpha0", lay.get("alpha")))
                    lay["foot"] = feather(cv2.dilate((nat > 0.02).astype(np.uint8), np.ones((11, 11), np.uint8)).astype(np.float32), 2.0)
        # the rest of A: under a soft rim it is keyed by its luma (dark first) ahead of the camera;
        # under a matte or glass rim it holds inside the container until the end effect
        rest = ~covered
        if self.cont["kind"] == "disc":
            pr = self.c.get("params", {})
            sky = self.knobs.get("sky", self.cont.get("params", {}).get("sky")) or {}
            self.sky = sky
            lumr = cv2.GaussianBlur(lum(np.clip(self.A_base, 0, 255).astype(np.uint8)), (0, 0), 4.0)   # the key's order is the brightness of what is shown (the fill where a layer has left)
            lo, hi = np.percentile(lumr[rest], [1, 99]) if rest.any() else (0, 1)
            self.rest_order = np.clip((lumr - lo) / max(1.0, hi - lo), 0, 1).astype(np.float32)
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            self.dborder = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, H - 1 - yy)).astype(np.float32)
            self.rim_frac = float(sky.get("rim_frac", 0.35))
            self.rest_mask = rest
            kw = sky.get("key_window", [float(pr.get("key_start", 0.0)), float(self.knobs.get("key_end", pr.get("key_end", 0.45)))])
            self.key_window = [float(kw[0]), float(kw[1])]
            self.key_band = float(sky.get("key_band", pr.get("key_band", 0.10)))
            if sky.get("stars"):
                # B's bright points by a top-hat of its luminance, ordered by brightness (1 = the brightest)
                LBf = self.LB
                th = LBf - cv2.morphologyEx(LBf, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
                th = np.clip(th, 0, None); hi_t = float(np.percentile(th, 99.9)) or 1.0
                self.star_order = np.clip(th / hi_t, 0, 1).astype(np.float32)
                self.star_window = [float(v) for v in sky.get("star_window", [0.1, 0.9])]
                self.info["sky"] = {"stars": True, "star_window": self.star_window, "key_window": self.key_window, "key_band": self.key_band, "star_share": round(float((self.star_order > 0.2).mean()), 4)}
        else:
            self.rest_mask = rest
            self.sky = {}
        self.info["matte_fallbacks"] = [f"{ph}:{i}" for ph, i in MATTE_FALLBACKS]
        self.info["layers"] = [{"name": l["name"], "by": l["by"], "window": l["window"], **({"soft": l["soft"]} if "soft" in l else {}), **({"chain": l["chain"]} if "chain" in l else {}), **({"ot": l["ot"]} if "ot" in l else {}), **({"axis": l["axis"]} if "axis" in l else {}), **({"depth": l["depth"], "target_inside_share": l.get("target_inside_share")} if l["by"] in ("morph_to", "move_to") else {}),
                                **({"k_end": round(l["k_end"], 4)} if "k_end" in l else {}),
                                **({"theta_deg": round(math.degrees(l["theta"]), 2), "off0": round(l["off0"], 1), "off1": round(l["off1"], 1), "thick0": l["thick0"], "width_end": round(l["width_end"], 2)} if "theta" in l else {}),
                                **({"ext": l["ext"], "work_scale": round(l["wl"], 3)} if "ext" in l else {})} for l in self.layers]

    # --- per-frame composite of A's layers in A's canvas (rgb float, alpha float)
    def compose_A(self, u):
        H, W = self.A.shape[:2]
        # the base: A, turning into the plate under each layer's footprint as that layer departs (over the first
        # quarter of its window), so frame 1 is still A and a vacated footprint shows A's own surround
        rgb = self.A_f.copy()
        v = None; hole = None
        h0, h1 = float(self.knobs.get("hole_reveal_from", 0.1)), float(self.knobs.get("hole_reveal_over", 0.35))
        for lay in self.layers:
            if "foot" in lay:
                e_l = layer_e(u, lay)
                ei = min(1.0, 30.0 * e_l)                            # the plate is under the layer as soon as it moves
                if ei > 0:
                    vi = lay["foot"] * ei
                    v = vi if v is None else np.maximum(v, vi)
                h0l, h1l = lay.get("hole_from", h0), lay.get("hole_over", h1)
                if lay.get("hole_reveal") and e_l > h0l:
                    # round 10: the footprint a layer has left gives way to B over a short ramp (the layer's own soft
                    # matte is the edge), so the fill is a passing moment and not a pale silhouette
                    hi = lay["foot"] * min(1.0, (e_l - h0l) / max(1e-6, h1l))
                    hole = hi if hole is None else np.maximum(hole, hi)
        self.v_last = v
        self.hole_last = hole
        if v is not None:
            rgb = rgb * (1 - v[..., None]) + self.A_base * v[..., None]
        # colour transforms first (they re-colour the base); the layers then composite premultiplied
        for lay in self.layers:
            if lay["by"] == "colour":
                e = ease01(u, *lay["window"])
                if e > 0:
                    w = lay.get("wsoft", lay["maskA"].astype(np.float32))
                    if lay.get("weight") == "dark":
                        w = w * np.clip(1.0 - self.rest_order, 0, 1) if hasattr(self, "rest_order") else w
                    rgb = lab_transfer(np.clip(rgb, 0, 255).astype(np.uint8), self.B, lay["maskB"], float(lay["params"].get("strength", 0.85)) * e, weight=w)
        # the alpha of A's composite: the rest of A (no layer) is 1 under a matte or glass rim and keyed
        # dark-first ahead of the camera under a soft rim; a layer's pixels start at 0 and each layer
        # adds its own matte, so a region a layer vacates (the receding sun's ring) shows B
        if self.cont["kind"] == "disc":
            es = ease01(u, *self.key_window)
            key = -self.key_band + (1.0 + self.key_band) * es
            a_rest = np.clip((self.rest_order - key) / self.key_band, 0, 1)
            e_cam = smootherstep(u)
            if self.sky.get("shape", "radial") == "radial" and "a0" in self.anchors and e_cam > 0:
                # round 11: what remains of A's sky is a soft disc around the sun that shrinks with the pull-back
                # (the border feather left "a blurred square shape" that shrank in steps)
                ca0, ra0 = self.anchors["a0"]
                if not hasattr(self, "r_anchor"):
                    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
                    self.r_anchor = np.hypot(xx - ca0[0], yy - ca0[1]).astype(np.float32)
                    self.r_far = float(max(np.hypot(ca0[0], ca0[1]), np.hypot(W - ca0[0], ca0[1]), np.hypot(ca0[0], H - ca0[1]), np.hypot(W - ca0[0], H - ca0[1])))
                r_end = float(self.sky.get("radial_end", 1.6)) * ra0
                wfrac = float(self.sky.get("radial_width", 0.35))
                R0 = self.r_far / max(0.05, 1.0 - wfrac)          # fully open at the start: the ramp begins beyond the far corner
                r_near = float(min(ca0[0], W - ca0[0], ca0[1], H - ca0[1]))   # the nearest frame edge: inside it no rectangle can show
                t_near = float(self.sky.get("radial_near_at", 0.25)); t_end = float(self.sky.get("radial_end_at", 0.9))
                if u <= t_near:
                    R = R0 + (r_near - R0) * smootherstep(u / max(1e-6, t_near))
                else:
                    R = r_near + (r_end - r_near) * min(1.0, (u - t_near) / max(1e-6, t_end - t_near))
                wr = wfrac * R
                x_ = np.clip((R - self.r_anchor) / max(1.0, wr), 0, 1)
                a_rest = a_rest * (x_ * x_ * (3.0 - 2.0 * x_))
            elif e_cam > 0 and hasattr(self, "dborder"):
                wpx = min(self.rim_frac, 4.0 * e_cam) * min(H, W)
                a_rest = a_rest * np.clip(self.dborder / max(1.0, wpx), 0, 1)
            alpha = (a_rest * self.rest_soft).astype(np.float32)
        else:
            alpha = self.rest_soft.copy()
        if hole is not None:
            alpha = (alpha * (1.0 - np.clip(hole, 0, 1))).astype(np.float32)
        rgb = rgb * alpha[..., None]                      # premultiplied from here on; un-premultiplied at the end
        front_layers = []
        for lay in self.layers:
            by = lay["by"]
            if by == "colour":
                continue
            e = layer_e(u, lay)
            if by == "hold":
                a = lay["alpha"]
                rgb = rgb * (1 - a[..., None]) + self.A_f * a[..., None]
                alpha = alpha * (1 - a) + a
                continue
            if by == "recede":
                k = 1.0 + (lay["k_end"] - 1.0) * e
                ca = lay["centre"]
                M = sim_about(k, ca[0], ca[1])[:2].astype(np.float32)
                content = lay["content"]
                if "content0" in lay:
                    wf = smootherstep(min(1.0, e / max(1e-6, lay["fill_in"])))
                    content = lay["content0"] * (1 - wf) + lay["content"] * wf if wf < 1.0 else lay["content"]
                disc_rgb = cv2.warpAffine(content, M, (W, H), flags=cv2.INTER_AREA if k < 1 else cv2.INTER_LINEAR, borderValue=0)
                # the rim ramp opens with the recede: hard at e = 0 (frame 1 equals A), rim_in..rim_out of the radius later
                rim_in_e = 1.0 + (lay["rim_in"] - 1.0) * min(1.0, 4.0 * e)
                ramp = np.clip((lay["rim_out"] - lay["rr0"]) / max(1e-3, lay["rim_out"] - rim_in_e), 0, 1)
                ramp = (ramp * ramp * (3.0 - 2.0 * ramp)).astype(np.float32)        # a smooth start of the rim (a linear ramp read as a ring at rim_in)
                a_src0 = feather(lay["disc_f"] * ramp, float(lay["params"].get("feather", 2.0))) if e > 0 else lay["alpha0"]
                a0 = cv2.warpAffine(a_src0, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
                # the limb softens: the matte's edge width grows with e
                sig = 1.0 + lay["soften"] * lay["r"] * k * e
                a = feather(a0, sig) if sig > 1.5 else a0
                # the mix: the disc's content gives way to B's core inside the shrinking disc, centre last
                # round 10: the rim mixes into the core's glow from the start of the recede over a wide ramp (limb first,
                # centre last), so no ring and no second disc
                mw = lay["params"].get("mix_window", [0.55, 0.95]); ramp = float(lay["params"].get("mix_ramp", 0.5))
                em = ease01(e, *mw)
                yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
                rr = np.hypot(xx - ca[0], yy - ca[1]) / max(1.0, lay["r"] * k)
                order = np.clip(rr, 0, 1)                         # 0 centre .. 1 limb
                a_mix = np.clip((em * (1.0 + ramp) - (1 - order)) / ramp, 0, 1) if em > 0 else np.zeros((H, W), np.float32)
                src = disc_rgb * (1 - a_mix[..., None]) + self.B_inA.astype(np.float32) * a_mix[..., None]
                # the region the disc vacated shows what is under (the keyed sky -> B); the disc composites over
                rgb = rgb * (1 - a[..., None]) + src * a[..., None]
                alpha = alpha * (1 - a) + a
                continue
            if by == "exit":
                M = np.array([[1, 0, lay["dx"] * e], [0, 1, lay["dy"] * e]], np.float32)
                src = cv2.warpAffine(lay["content"], M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
                a = cv2.warpAffine(lay["alpha0"], M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
                a = a * (1.0 - ease01(e, 1.0 - lay["fade"], 1.0))
                rgb = rgb * (1 - a[..., None]) + src * a[..., None]
                alpha = alpha * (1 - a) + a
                continue
            if by == "line_to":
                th = lay["theta"] * e
                off = lay["off0"] + (lay["off1"] - lay["off0"]) * e
                et = e ** float(lay["params"].get("thin_power", 0.45))
                sy = 1.0 + (lay["width_end"] / lay["thick0"] - 1.0) * et
                sx = 1.0 + (lay["stretch"] - 1.0) * e
                piv = lay["pivot"]
                # the band's own centre line sits at y = piv.y + off0; move it to the pivot's normal offset off(e),
                # then rotate about the pivot and scale across the band
                yc0 = piv[1] + lay["off0"]
                Tm = np.array([[1, 0, 0], [0, 1, -(yc0)], [0, 0, 1]], np.float64)              # centre line -> y 0
                S = np.diag([sx, sy, 1.0])
                Tx = np.array([[1, 0, -piv[0]], [0, 1, 0], [0, 0, 1]], np.float64)
                R = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]], np.float64)
                # after S the centre line is y 0 and x is relative to the pivot's x: place it at offset `off` along the normal from the pivot
                Tp = np.array([[1, 0, piv[0]], [0, 1, piv[1]], [0, 0, 1]], np.float64)
                Off = np.array([[1, 0, 0], [0, 1, off], [0, 0, 1]], np.float64)
                M = Tp @ R @ Off @ S @ Tx @ Tm
                M2 = M[:2].astype(np.float32)
                band_rgb = cv2.warpAffine(lay["content"], M2, (W, H), flags=cv2.INTER_AREA if sy < 1 else cv2.INTER_LINEAR, borderValue=0)
                a = cv2.warpAffine(lay["alpha0"], M2, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
                a = feather(a, 1.0 + 4.0 * e)
                mw = lay["params"].get("mix_window", [0.3, 0.9])
                em = ease01(e, *mw)
                if em > 0:
                    tB = cv2.warpAffine(lay["targetB"], M2, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                    src = band_rgb * (1 - em) + tB.astype(np.float32) * em
                else:
                    src = band_rgb
                rgb = rgb * (1 - a[..., None]) + src * a[..., None]
                alpha = alpha * (1 - a) + a
                continue
            if by == "keyframe_chain":
                if e <= 0:
                    if lay["depth"] == "front":
                        front_layers.append((lay, None, None)); continue
                    a = lay["alpha_native"]
                    rgb = rgb * (1 - a[..., None]) + self.A_f * a[..., None]
                    alpha = alpha * (1 - a) + a
                    continue
                knots = [0.0] + list(lay["times"]) + [1.0]
                j = max(0, min(len(lay["segs"]) - 1, int(np.searchsorted(np.array(knots), e, side="right") - 1)))
                s = (e - knots[j]) / max(1e-6, knots[j + 1] - knots[j])
                s = float(np.clip(s, 0.0, 1.0))
                P, Q = lay["imgs"][j], lay["imgs"][j + 1]
                mP, mQ = lay["mattes"][j], lay["mattes"][j + 1]
                if lay["segs"][j].get("lead"):
                    s = smootherstep(s)                      # the rigid move eases in and out; the keyframe segments stay linear
                if s <= 0.0:
                    src, a = P, mP
                elif s >= 1.0:
                    src, a = Q, mQ
                else:
                    sg = lay["segs"][j]
                    src = T.morph_frame(P, Q, sg, s, s).astype(np.float32)
                    th = T.TCFG["hole_thresh"]
                    aP, cP = T.forward_splat(mP, sg["dAB"], s, sg["wA"]); aP = T.fill_holes(aP, cP, T.backward_warp(mP, -s * sg["dAB"]).astype(np.float32), th)
                    aQ, cQ = T.forward_splat(mQ, sg["dBA"], 1.0 - s, sg["wB"]); aQ = T.fill_holes(aQ, cQ, T.backward_warp(mQ, -(1.0 - s) * sg["dBA"]).astype(np.float32), th)
                    a = np.clip(aP * (1 - s) + aQ * s, 0, 1).astype(np.float32)
                if lay["depth"] == "front":
                    front_layers.append((lay, src, a)); continue
                rgb = rgb * (1 - a[..., None]) + src * a[..., None]
                alpha = alpha * (1 - a) + a
                continue
            if by in ("morph_to", "move_to"):
                # rendered in the layer's working frame, then placed into A's canvas (or kept for the frame when it leaves A)
                lw, lh = lay["contentA"].shape[1], lay["contentA"].shape[0]
                if e <= 0:
                    if lay["depth"] != "front":
                        a = lay["alpha_native"]
                        rgb = rgb * (1 - a[..., None]) + self.A_f * a[..., None]
                        alpha = alpha * (1 - a) + a
                    else:
                        front_layers.append((lay, None, None))
                    continue
                else:
                    rgbL = LP.warp_along(lay["contentA"], lay["D"], e, exact=True)
                    aL = LP.warp_along(lay["alphaA"], lay["D"], e, exact=True)
                    mw = lay["params"].get("mix_window", [0.25, 0.9])
                    em = ease01(e, *mw)
                    if em > 0:
                        # the target's pixels where the matte will be at e = 1 are at the same place in B; the matte at e
                        # is between, so B is read through the inverse of the remaining motion: approximate by the
                        # forward warp of B's content by the field's remainder (B sits at the end position)
                        bL = LP.warp_along(lay["contentB"], lay["D"], -(1.0 - e), exact=True)
                        src_order = {"luma": lay["orderA"], "noise": lay["noise"], "edge": lay["edge"]}.get(lay["mix"])
                        order = LP.warp_along(src_order, lay["D"], e, exact=True) if src_order is not None else None
                        if order is None:
                            a_mix = np.full((lh, lw), em, np.float32)
                        else:
                            a_mix = np.clip((order + em * 1.3 - 1.0) / 0.2, 0, 1)
                            a_mix = cv2.GaussianBlur(a_mix, (0, 0), 1.5)
                        # the matte grows toward B's matte as the mix completes
                        aB = LP.warp_along(lay["alphaB"], lay["D"], -(1.0 - e), exact=True)
                        aL = aL * (1 - em) + np.maximum(aL, aB) * em if lay["params"].get("grow_matte", True) else aL
                        rgbL = rgbL * (1 - a_mix[..., None]) + bL * a_mix[..., None]
                if lay["depth"] == "front":
                    front_layers.append((lay, rgbL, aL))
                    continue
                # back into A's canvas
                Ti = np.linalg.inv(lay["Tw"])[:2].astype(np.float32)
                rgbC = cv2.warpAffine(rgbL, Ti, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
                aC = cv2.warpAffine(aL, Ti, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
                rgb = rgb * (1 - aC[..., None]) + rgbC * aC[..., None]
                alpha = alpha * (1 - aC) + aC
                continue
        rgb = rgb / np.maximum(alpha, 1e-3)[..., None]
        rgb = np.where(alpha[..., None] > 1e-3, rgb, self.A_f)
        return np.clip(rgb, 0, 255), alpha, front_layers


# ----------------------------------------------------------------------------- the render
def render(plan, concept, out, seconds, fps, max_long, knobs):
    t_start = time.time()
    sc = Scene(plan, concept, max_long, knobs)
    sc.build()
    W, H = sc.W, sc.H
    n = int(round(seconds * fps))
    cam = sc.cam
    S_A3 = sc.S_A3
    end = dict(concept.get("end_effect") or {"kind": "luma_reveal", "window": [0.78, 1.0]})
    if "end_window" in knobs:
        end["window"] = [float(v) for v in knobs["end_window"]]
    glass = sc.cont.get("rim") == "glass"
    reflect = float(knobs.get("reflect", sc.cont.get("params", {}).get("reflect", sc.cont.get("spec", {}).get("reflect", 0.18))))
    enc = T.FrameEncoder(out / "transition.mp4", W, H, fps)
    keep = []
    one = np.ones((H, W), np.float32)
    ease = concept.get("pullback", {}).get("ease", "smootherstep")
    for i in range(n):
        u = i / (n - 1)
        e = smootherstep(u) if ease == "smootherstep" else u
        mapx, mapy = cam.inverse_map(e)                          # frame -> plate
        front_layer = getattr(sc, "front_alpha", None) is not None
        has_plate = getattr(sc, "B_plate", None) is not None
        if sc.parallax and sc.parallax["dB"] is not None:
            bx, by_ = parallax_map(mapx, mapy, e, cam, sc.parallax["dB"], sc.parallax["dB_ref"], sc.parallax["gain"], iters=3, push=0.0)
            if front_layer:
                fx, fy = parallax_map(mapx, mapy, e, cam, sc.parallax.get("dF", sc.parallax["dB"]), sc.parallax["dB_ref"], sc.parallax["gain"], iters=3, push=sc.parallax["push"], push_floor=sc.parallax["push_floor"])
            else:
                fx, fy = bx, by_
        else:
            bx, by_ = mapx, mapy; fx, fy = mapx, mapy
        # B through the camera, from its full-resolution file (minification by INTER_AREA pre-resize);
        # the plate is B with its front (and a line_to target) filled; it blends back to B over the end effect
        ef_plate = ease01(u, *end["window"])
        if has_plate and ef_plate > 0.0:
            plate_src = np.clip(sc.B_plate.astype(np.float32) * (1 - ef_plate) + sc.B_src.astype(np.float32) * ef_plate, 0, 255).astype(np.uint8)
        else:
            plate_src = sc.B_plate if has_plate else sc.B_src
        z = cam.zoom(e) / sc.kB
        if z < 1.0:
            Bs = cv2.resize(plate_src, (max(1, int(round(plate_src.shape[1] * z))), max(1, int(round(plate_src.shape[0] * z)))), interpolation=cv2.INTER_AREA)
            kk = plate_src.shape[1] / Bs.shape[1] / sc.kB            # plate px per Bs px
            Bf = remap_img(Bs, bx / kk, by_ / kk, cv2.BORDER_REPLICATE).astype(np.float32)
            if front_layer:
                Fs = cv2.resize(sc.front_rgb, (Bs.shape[1], Bs.shape[0]), interpolation=cv2.INTER_AREA)
                Fa = cv2.resize(sc.front_alpha, (Bs.shape[1], Bs.shape[0]), interpolation=cv2.INTER_AREA)
                Ff = remap_img(Fs, fx / kk, fy / kk).astype(np.float32); Fa_f = remap_img(Fa, fx / kk, fy / kk)
        else:
            Bf = remap_img(plate_src, bx * sc.kB, by_ * sc.kB, cv2.BORDER_REPLICATE).astype(np.float32)
            if front_layer:
                Ff = remap_img(sc.front_rgb, fx * sc.kB, fy * sc.kB).astype(np.float32); Fa_f = remap_img(sc.front_alpha, fx * sc.kB, fy * sc.kB)
        # A's composite, then through the camera (plate -> A canvas: S_A^-1), with A's own parallax
        rgbA, aA_c, front_layers = sc.compose_A(u)
        Si = np.linalg.inv(S_A3)
        if sc.parallax and sc.parallax["dA"] is not None:
            # A's disparity on the plate: sample dA at the plate point's A coordinates
            ax = (Si[0, 0] * mapx + Si[0, 1] * mapy + Si[0, 2]); ay = (Si[1, 0] * mapx + Si[1, 1] * mapy + Si[1, 2])
            if cam.kind == "homog":
                az = (Si[2, 0] * mapx + Si[2, 1] * mapy + Si[2, 2]); ax, ay = ax / az, ay / az
            dA_plate = cv2.remap(sc.parallax["dA"], ax.astype(np.float32), ay.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            px, py = parallax_map(mapx, mapy, e, cam, dA_plate, sc.parallax["dA_ref"], sc.parallax.get("gain_A", sc.parallax["gain"]), iters=1)
        else:
            px, py = mapx, mapy
        ax = (Si[0, 0] * px + Si[0, 1] * py + Si[0, 2]); ay = (Si[1, 0] * px + Si[1, 1] * py + Si[1, 2])
        if cam.kind == "homog":
            az = (Si[2, 0] * px + Si[2, 1] * py + Si[2, 2]); ax, ay = ax / az, ay / az
        ax, ay = ax.astype(np.float32), ay.astype(np.float32)
        # frame px per A-canvas px, read from the map itself (a homography's 2x2 block is not its scale;
        # that estimate read 0.98 at e = 0 and blurred the first frame by 9 levels on mismatch_3)
        s_now = 1.0 / max(1e-6, float(np.median(np.abs(ax[:, 1:] - ax[:, :-1]))))
        if s_now < 0.999:
            # minification: pre-resize A's composite with INTER_AREA
            wsm = max(1, int(round(rgbA.shape[1] * s_now))); hsm = max(1, int(round(rgbA.shape[0] * s_now)))
            rgbS = cv2.resize(rgbA, (wsm, hsm), interpolation=cv2.INTER_AREA); aS = cv2.resize(aA_c, (wsm, hsm), interpolation=cv2.INTER_AREA)
            kx = rgbA.shape[1] / wsm; ky = rgbA.shape[0] / hsm
            Af = remap_img(rgbS, ax / kx, ay / ky); aA = remap_img(aS, ax / kx, ay / ky)
        else:
            Af = remap_img(rgbA, ax, ay); aA = remap_img(aA_c, ax, ay)
        inside = remap_img(one, ax, ay)
        aA = aA * inside
        if sc.cont["kind"] in ("quad", "rect"):
            # the rim: the signed distance of each frame pixel's plate point to the quad's edges (valid beyond
            # the canvas, where a quad corner may lie); hard at e = 0, the soft width blended in over the first 20 %
            dist = quad_distance(sc.quad, mapx, mapy)
            wr = smootherstep(min(1.0, e / 0.2))
            width = 1.0 + (sc.cont_feather_px - 1.0) * wr
            cont = np.clip(dist / width + 0.5, 0, 1).astype(np.float32) if width <= 1.0 else np.clip(dist / width, 0, 1).astype(np.float32)
            aA = aA * cont
            if glass and e > 0:
                rho = reflect * smootherstep(min(1.0, e / 0.3))
                Af = Af * (1 - rho) + Bf * rho
        if sc.sky.get("stars") and hasattr(sc, "star_order"):
            es_ = ease01(u, *sc.star_window)
            if es_ > 0:
                so = remap_img(sc.star_order, bx, by_)
                a_star = np.clip((so - (1.0 - es_)) / 0.15, 0, 1) * (so > 0.05)
                sky_f = remap_img(sc.rest_mask.astype(np.float32), ax, ay)
                aA = aA * (1.0 - a_star * sky_f)
        # the end effect inside the container: B replaces what remains of A in A's brightness order
        ef = ease01(u, *end["window"])
        if ef > 0:
            of = remap_img(sc.orderA, ax, ay)
            kind_end = knobs.get("end_kind", end.get("kind"))
            band_end = float(knobs.get("end_band", end.get("params", {}).get("band", 0.16)))
            if kind_end == "edge_reveal":
                dist = cv2.distanceTransform((aA > 0.02).astype(np.uint8), cv2.DIST_L2, 5); of = 1.0 - np.clip(dist / max(1.0, dist.max()), 0, 1)
            elif kind_end == "radial_reveal" and "a0" in sc.anchors:
                ca0 = sc.anchors["a0"][0]; R0 = float(knobs.get("end_radius_px", 0.6 * max(sc.A.shape[:2])))
                of = np.clip(np.hypot(ax - ca0[0], ay - ca0[1]) / R0, 0, 1)          # far from the anchor first
            elif kind_end == "b_luma_reveal":
                of = remap_img(sc.orderB, bx, by_)                                       # B's brightest first
            vac = float(knobs.get("vacated_first", end.get("params", {}).get("vacated_first", 0.35)))
            if vac > 0 and getattr(sc, "v_last", None) is not None:
                of = np.clip(of + vac * remap_img(sc.v_last, ax, ay), 0, 1)   # round 10: where A's layer has left, B comes first (a higher order reveals earlier; 0..1 kept, so the end stays exact)
            a_fin = np.clip((of + ef * (1.0 + band_end) - 1.0) / band_end, 0, 1)
            a_fin = cv2.GaussianBlur(a_fin, (0, 0), 1.2)
            aA = aA * (1 - a_fin)
        frame = Bf * (1 - aA[..., None]) + Af * aA[..., None]
        if front_layer:
            fin = smootherstep(min(1.0, e / sc.parallax.get("front_in", 0.15))) if sc.parallax else 1.0
            per = getattr(sc, "front_elements_layers", None)
            if per:
                # one layer per element, far to near: B's pixels and the element's own matte through its own map
                src_rgb = Fs if z < 1.0 else sc.front_rgb          # B's own pixels (the plate is B with the front filled)
                kk_ = kk if z < 1.0 else 1.0 / sc.kB
                for lay_f in per:
                    ex, ey = sc.front_element_map(lay_f, e, cam, mapx, mapy)
                    a_f = remap_img(lay_f["alpha"], ex, ey) * fin
                    if a_f.max() <= 1e-3:
                        continue
                    rgb_f = remap_img(src_rgb, ex / kk_, ey / kk_).astype(np.float32)
                    frame = frame * (1 - a_f[..., None]) + rgb_f * a_f[..., None]
            else:
                Fa_f = Fa_f * fin
                frame = frame * (1 - Fa_f[..., None]) + Ff * Fa_f[..., None]
        # layers that leave the container (depth "front") composite over B's front, through the same camera
        for lay, rgbL, aL in front_layers:
            if rgbL is None:
                La = remap_img(lay["alpha_native"], ax, ay) * inside
                if sc.cont["kind"] in ("quad", "rect"):
                    La = La * cont
                frame = frame * (1 - La[..., None]) + Af * La[..., None]
                continue
            if "Tw" in lay:
                Tw = lay["Tw"]
                # work frame -> A canvas -> frame: the frame pixel's work coordinates = Tw(A coords)
                wx = (Tw[0, 0] * ax + Tw[0, 2]).astype(np.float32); wy = (Tw[1, 1] * ay + Tw[1, 2]).astype(np.float32)
                Lf = remap_img(rgbL, wx, wy); La = remap_img(aL, wx, wy)
                if ef > 0:
                    La = La * (1 - ease01(u, end["window"][0] + 0.5 * (end["window"][1] - end["window"][0]), end["window"][1]))
            else:
                # a keyframe chain in front: its content lives in A's canvas and ends on B, so it needs no fade
                Lf = remap_img(rgbL, ax, ay); La = remap_img(aL, ax, ay) * inside
            frame = frame * (1 - La[..., None]) + Lf * La[..., None]
        if i == 0:
            frame = sc.A.astype(np.float32)
        if i == n - 1:
            frame = sc.B.astype(np.float32)
        f8 = T.to_u8(frame)
        enc.write(f8)
        if i in {0, n // 8, n // 4, 3 * n // 8, n // 2, 5 * n // 8, 3 * n // 4, 7 * n // 8, n - 1}:
            keep.append(f8)
    enc.close()
    cap = cv2.VideoCapture(str(out / "transition.mp4")); prev = None; steps = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        if prev is not None:
            steps.append(float(np.abs(fr.astype(np.float32) - prev).mean()))
        prev = fr
    cap.release()
    sc.info.update(frames=len(steps) + 1, step_first=round(steps[0], 2), step_second=round(steps[1], 2), step_last=round(steps[-1], 2), step_max=round(max(steps), 2),
                   seconds=seconds, fps=fps, knobs=knobs, wall_s=round(time.time() - t_start, 1))
    return keep, sc.info


def montage(frames, path, cols=3):
    th = [cv2.resize(f, (f.shape[1] // 3, f.shape[0] // 3), interpolation=cv2.INTER_AREA) for f in frames]
    rows = [np.concatenate(th[i:i + cols], 1) for i in range(0, len(th) - len(th) % cols, cols)]
    cv2.imwrite(str(path), cv2.cvtColor(np.concatenate(rows, 0), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])


def parse_knob(s):
    k, v = s.split("=", 1)
    try:
        v = json.loads(v)
    except Exception:
        pass
    return k, v


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("plan"); ap.add_argument("out"); ap.add_argument("--concept", default=None)
    ap.add_argument("--seconds", type=float, default=3.0); ap.add_argument("--fps", type=int, default=30); ap.add_argument("--max-long", type=int, default=1920)
    ap.add_argument("--set", action="append", default=[], help="knob=value (JSON value); 'name.param' targets a transform's params")
    a = ap.parse_args()
    plan = json.load(open(a.plan))
    concepts = plan["concepts"]
    concept = next((c for c in concepts if c["id"] == a.concept), concepts[0]) if a.concept else concepts[0]
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    knobs = dict(parse_knob(s) for s in a.set)
    keep, info = render(plan, concept, out, a.seconds, a.fps, a.max_long, knobs)
    info["plan_sha256"] = hashlib.sha256(Path(a.plan).read_bytes()).hexdigest()[:16]
    montage(keep, out / "montage.jpg")
    json.dump(info, open(out / "info.json", "w"), indent=1)
    print(json.dumps(info))
