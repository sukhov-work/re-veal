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
PHOTO = {"S": "_S", "F": "_F"}


# ----------------------------------------------------------------------------- small helpers
def ease01(u, t0, t1):
    if t1 <= t0:
        return 1.0 if u >= t1 else 0.0
    return smootherstep((u - t0) / (t1 - t0))


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


# ----------------------------------------------------------------------------- sampling
def sample_full(img_full, k, M3_img_to_frame, W, H, border=0, mask=None):
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
    if persp:
        return cv2.warpPerspective(src, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=border)
    return cv2.warpAffine(src, M[:2].astype(np.float32), (W, H), flags=cv2.INTER_LINEAR, borderValue=border)


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
        self.anchors = {}
        self.A = None; self.shiftA = (0, 0)

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
        if k == "luma_above":
            return lum(self.A) >= float(spec["min_L"])
        raise ValueError(f"A mask kind {k}")

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
            dB = cv2.GaussianBlur(T.model_disparity(self.B), (0, 0), 6.0) if "B" in srcs else None
            dA = cv2.GaussianBlur(T.model_disparity(self.A), (0, 0), 6.0) if "A" in srcs else None
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
            # A's disparity expressed on the plate (for the per-frame map of A)
            push = float(self.knobs.get("parallax_push", pl.get("push", 2.5 if self.cont["kind"] in ("quad", "rect") else 0.0)))
            self.parallax = {"gain": g, "dB": dB, "dB_ref": dB_ref, "dA": dA, "dA_ref": dA_ref, "push": push,
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
                    if dm > dB_ref + margin:
                        keepf |= m; kept.append([int(eid), round(dm, 3)])
                self.front = keepf
                self.info["front_elements"] = kept
                # the front's disparity map: one value per element (the nearer wins at a border), so each
                # element moves as one piece and nothing inside it stretches
                dF = dB.copy()
                for eid, dm in sorted(kept, key=lambda t: t[1]):
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
        holes = fm.copy(); ff = np.zeros((fm.shape[0] + 2, fm.shape[1] + 2), np.uint8)
        cv2.floodFill(holes, ff, (0, 0), 1)                      # the outside; what stays 0 is an enclosed hole
        fm = (fm | (holes == 0).astype(np.uint8)).astype(np.uint8)
        self.front = fm.astype(bool)
        k = self.kB
        if k != 1.0:
            fm_src = cv2.resize(fm, (self.B_src.shape[1], self.B_src.shape[0]), interpolation=cv2.INTER_NEAREST)
        else:
            fm_src = fm
        grow = cv2.dilate(fm_src, np.ones((int(6 * k) | 1, int(6 * k) | 1), np.uint8))
        small_k = max(1.0, self.B_src.shape[1] / 1280.0)          # inpaint at <= 1280 px wide, then upsample the fill
        if small_k > 1.0:
            bs = cv2.resize(self.B_src, (int(round(self.B_src.shape[1] / small_k)), int(round(self.B_src.shape[0] / small_k))), interpolation=cv2.INTER_AREA)
            gs = cv2.resize(grow, (bs.shape[1], bs.shape[0]), interpolation=cv2.INTER_NEAREST)
            filled = cv2.inpaint(bs, gs, 7, cv2.INPAINT_TELEA)
            filled = cv2.resize(filled, (self.B_src.shape[1], self.B_src.shape[0]), interpolation=cv2.INTER_LINEAR)
        else:
            filled = cv2.inpaint(self.B_src, grow, 7, cv2.INPAINT_TELEA)
        plate = self.B_src.copy(); plate[grow.astype(bool)] = filled[grow.astype(bool)]
        self.B_plate = plate
        self.front_rgb = self.B_src
        self.front_alpha = cv2.GaussianBlur(fm_src.astype(np.float32), (0, 0), 1.5)
        self.info["front_share"] = round(float(self.front.mean()), 4)

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
        Si = np.linalg.inv(self.S_A3)
        for tr in c.get("transforms", []):
            by = tr["by"]
            lay = {"name": tr["name"], "by": by, "window": tr.get("window", [0, 1]), "mix": tr.get("mix", "luma"), "params": dict(tr.get("params", {})), "depth": tr.get("depth", "inside")}
            for k, v in self.knobs.items():
                if k.startswith(tr["name"] + "."):
                    key = k.split(".", 1)[1]
                    if key == "window":
                        lay["window"] = list(v)
                    else:
                        lay["params"][key] = v
            p = lay["params"]
            if p.get("skip"):                      # an operator's cut ("name.skip=true"): the transform is left out, recorded
                self.unplaced.append({"name": tr["name"], "why": "skipped by the operator's knob"})
                continue
            if by == "colour":
                lay["maskA"] = self.mask_A(tr["a"]); lay["maskB"] = self.mask_B(tr["b"])
                lay["weight"] = p.get("weight", "dark" if (c.get("container") or {}).get("kind") == "disc" else None)
                self.layers.append(lay); continue
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
            if tr["a"].get("exclude_covered", True):
                mA &= ~covered
            if mA.sum() < 64:
                lay["unplaced"] = "the a-mask is empty on this crop"
                self.unplaced.append({"name": tr["name"], "why": lay["unplaced"]})
                continue
            if by == "hold":
                lay["alpha"] = feather(mA.astype(np.float32), float(p.get("feather", 2.0)))
                self.layers.append(lay); continue
            if by == "recede":
                ca, ra = self.anchors[tr["a"].get("anchor", "a0")]
                cb, rb = self.anchors["b0"]
                s1 = float(self.S_A3[0, 0])
                end_r_A = float(p.get("end_radius", 30.0)) * self.ls_scale / s1       # B px -> A canvas px
                lay.update(centre=ca, r=ra, k_end=min(1.0, end_r_A / ra), soften=float(p.get("soften", 0.5)))
                disc = mA
                yy, xx = np.mgrid[0:H, 0:W]
                rr0 = np.hypot(xx - ca[0], yy - ca[1]) / max(1.0, ra)
                lay["rr0"] = rr0.astype(np.float32); lay["disc_f"] = disc.astype(np.float32)
                lay["rim_in"], lay["rim_out"] = float(p.get("rim_in", 0.9)), float(p.get("rim_out", 1.0))
                lay["alpha0"] = feather(disc.astype(np.float32), 1.0)
                lay["content"] = self.A_f
                covered |= disc
                self.layers.append(lay); continue
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
                lay["alpha0"] = feather(mA.astype(np.float32), 1.0)
                xs_ = np.arange(W, dtype=np.float32) / (W - 1)
                taper = np.clip(np.minimum(xs_, 1 - xs_) / float(p.get("end_taper", 0.12)), 0, 1)[None, :]
                lay["alpha0"] = lay["alpha0"] * taper
                lay["content"] = self.A_f
                lay["targetB"] = self.B_inA
                covered |= mA
                self.layers.append(lay); continue
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
                contentA = cv2.warpAffine(self.A_f, Tw[:2].astype(np.float32), (lw, lh), flags=cv2.INTER_AREA if wl < 1 else cv2.INTER_LINEAR, borderValue=0)
                alphaA = cv2.warpAffine(mA.astype(np.float32), Tw[:2].astype(np.float32), (lw, lh), flags=cv2.INTER_LINEAR, borderValue=0)
                # B's content and the target mask in the working frame: B canvas -> A canvas (Si) -> work
                MB = Tw @ Si
                contentB = sample_full(self.B_src, self.kB, MB, lw, lh)
                alphaB = cv2.warpPerspective(mB.astype(np.float32), MB, (lw, lh), flags=cv2.INTER_LINEAR, borderValue=0) if abs(MB[2, 0]) + abs(MB[2, 1]) > 1e-12 else cv2.warpAffine(mB.astype(np.float32), MB[:2].astype(np.float32), (lw, lh), flags=cv2.INTER_LINEAR, borderValue=0)
                # the affine box -> box (a similarity on the boxes' centres and the geometric-mean size)
                bxa = box_of_mask(alphaA > 0.5); bxb = box_of_mask(alphaB > 0.5)
                ca_ = np.array([(bxa[0] + bxa[2]) / 2, (bxa[1] + bxa[3]) / 2]); cb_ = np.array([(bxb[0] + bxb[2]) / 2, (bxb[1] + bxb[3]) / 2])
                sx = (bxb[2] - bxb[0]) / max(1, bxa[2] - bxa[0]); sy = (bxb[3] - bxb[1]) / max(1, bxa[3] - bxa[1])
                yy, xx = np.mgrid[0:lh, 0:lw].astype(np.float32)
                mapmode = p.get("map", "box")
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
                if fpx_l > 0:
                    alphaA = feather(alphaA, fpx_l); alphaB = feather(alphaB, fpx_l)
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
                lay["alpha_native"] = feather(carried.astype(np.float32), 1.0)
                covered |= carried
                self.layers.append(lay); continue
            raise ValueError(f"transform kind {by}")
        self.covered = covered
        self.info["unplaced"] = self.unplaced
        # the rest of A: under a soft rim it is keyed by its luma (dark first) ahead of the camera;
        # under a matte or glass rim it holds inside the container until the end effect
        rest = ~covered
        if self.cont["kind"] == "disc":
            pr = self.c.get("params", {})
            lumr = cv2.GaussianBlur(self.LA, (0, 0), 4.0)
            lo, hi = np.percentile(lumr[rest], [1, 99]) if rest.any() else (0, 1)
            self.rest_order = np.clip((lumr - lo) / max(1.0, hi - lo), 0, 1).astype(np.float32)
            self.rest_mask = rest
            self.key_window = [float(pr.get("key_start", 0.0)), float(self.knobs.get("key_end", pr.get("key_end", 0.45)))]
            self.key_band = float(pr.get("key_band", 0.10))
        else:
            self.rest_mask = rest
        self.info["layers"] = [{"name": l["name"], "by": l["by"], "window": l["window"], **({"ot": l["ot"]} if "ot" in l else {}), **({"axis": l["axis"]} if "axis" in l else {}), **({"depth": l["depth"], "target_inside_share": l.get("target_inside_share")} if l["by"] in ("morph_to", "move_to") else {}),
                                **({"k_end": round(l["k_end"], 4)} if "k_end" in l else {}),
                                **({"theta_deg": round(math.degrees(l["theta"]), 2), "off0": round(l["off0"], 1), "off1": round(l["off1"], 1), "thick0": l["thick0"], "width_end": round(l["width_end"], 2)} if "theta" in l else {}),
                                **({"ext": l["ext"], "work_scale": round(l["wl"], 3)} if "ext" in l else {})} for l in self.layers]

    # --- per-frame composite of A's layers in A's canvas (rgb float, alpha float)
    def compose_A(self, u):
        H, W = self.A.shape[:2]
        rgb = self.A_f.copy()
        # colour transforms first (they re-colour the base)
        for lay in self.layers:
            if lay["by"] == "colour":
                e = ease01(u, *lay["window"])
                if e > 0:
                    w = lay["maskA"].astype(np.float32)
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
            alpha = np.where(self.rest_mask, a_rest, 0.0).astype(np.float32)
        else:
            alpha = self.rest_mask.astype(np.float32)
        front_layers = []
        for lay in self.layers:
            by = lay["by"]
            if by == "colour":
                continue
            e = ease01(u, *lay["window"])
            if by == "hold":
                alpha = np.maximum(alpha, lay["alpha"])
                continue
            if by == "recede":
                k = 1.0 + (lay["k_end"] - 1.0) * e
                ca = lay["centre"]
                M = sim_about(k, ca[0], ca[1])[:2].astype(np.float32)
                disc_rgb = cv2.warpAffine(lay["content"], M, (W, H), flags=cv2.INTER_AREA if k < 1 else cv2.INTER_LINEAR, borderValue=0)
                # the rim ramp opens with the recede: hard at e = 0 (frame 1 equals A), rim_in..rim_out of the radius later
                rim_in_e = 1.0 + (lay["rim_in"] - 1.0) * min(1.0, 4.0 * e)
                ramp = np.clip((lay["rim_out"] - lay["rr0"]) / max(1e-3, lay["rim_out"] - rim_in_e), 0, 1).astype(np.float32)
                a_src0 = feather(lay["disc_f"] * ramp, float(lay["params"].get("feather", 2.0))) if e > 0 else lay["alpha0"]
                a0 = cv2.warpAffine(a_src0, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
                # the limb softens: the matte's edge width grows with e
                sig = 1.0 + lay["soften"] * lay["r"] * k * e
                a = feather(a0, sig) if sig > 1.5 else a0
                # the mix: the disc's content gives way to B's core inside the shrinking disc, centre last
                mw = lay["params"].get("mix_window", [0.45, 0.95])
                em = ease01(e, *mw)
                yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
                rr = np.hypot(xx - ca[0], yy - ca[1]) / max(1.0, lay["r"] * k)
                order = np.clip(rr, 0, 1)                         # 0 centre .. 1 limb
                a_mix = np.clip((em * 1.3 - (1 - order)) / 0.25, 0, 1) if em > 0 else np.zeros((H, W), np.float32)
                src = disc_rgb * (1 - a_mix[..., None]) + self.B_inA.astype(np.float32) * a_mix[..., None]
                # the region the disc vacated shows what is under (the keyed sky -> B); the disc composites over
                rgb = rgb * (1 - a[..., None]) + src * a[..., None]
                alpha = np.maximum(alpha, a)
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
                    src = band_rgb * (1 - em) + lay["targetB"].astype(np.float32) * em
                else:
                    src = band_rgb
                rgb = rgb * (1 - a[..., None]) + src * a[..., None]
                alpha = np.maximum(alpha, a)
                continue
            if by in ("morph_to", "move_to"):
                # rendered in the layer's working frame, then placed into A's canvas (or kept for the frame when it leaves A)
                lw, lh = lay["contentA"].shape[1], lay["contentA"].shape[0]
                if e <= 0:
                    if lay["depth"] != "front":
                        alpha = np.maximum(alpha, lay["alpha_native"])
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
                alpha = np.maximum(alpha, aC)
                continue
        return rgb, alpha, front_layers


# ----------------------------------------------------------------------------- the render
def render(plan, concept, out, seconds, fps, max_long, knobs):
    t_start = time.time()
    sc = Scene(plan, concept, max_long, knobs)
    sc.build()
    W, H = sc.W, sc.H
    n = int(round(seconds * fps))
    cam = sc.cam
    S_A3 = sc.S_A3
    end = concept.get("end_effect") or {"kind": "luma_reveal", "window": [0.78, 1.0]}
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
            px, py = parallax_map(mapx, mapy, e, cam, dA_plate, sc.parallax["dA_ref"], sc.parallax["gain"], iters=1)
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
        # the end effect inside the container: B replaces what remains of A in A's brightness order
        ef = ease01(u, *end["window"])
        if ef > 0:
            of = remap_img(sc.orderA, ax, ay)
            kind_end = knobs.get("end_kind", end.get("kind"))
            if kind_end == "edge_reveal":
                dist = cv2.distanceTransform((aA > 0.02).astype(np.uint8), cv2.DIST_L2, 5); of = 1.0 - np.clip(dist / max(1.0, dist.max()), 0, 1)
            elif kind_end == "radial_reveal" and "a0" in sc.anchors:
                ca0 = sc.anchors["a0"][0]; R0 = float(knobs.get("end_radius_px", 0.6 * max(sc.A.shape[:2])))
                of = np.clip(np.hypot(ax - ca0[0], ay - ca0[1]) / R0, 0, 1)          # far from the anchor first
            a_fin = np.clip((of + ef * 1.3 - 1.0) / 0.16, 0, 1)
            a_fin = cv2.GaussianBlur(a_fin, (0, 0), 1.2)
            aA = aA * (1 - a_fin)
        frame = Bf * (1 - aA[..., None]) + Af * aA[..., None]
        if front_layer:
            fin = smootherstep(min(1.0, e / sc.parallax.get("front_in", 0.15))) if sc.parallax else 1.0
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
            Tw = lay["Tw"]
            # work frame -> A canvas -> frame: the frame pixel's work coordinates = Tw(A coords)
            wx = (Tw[0, 0] * ax + Tw[0, 2]).astype(np.float32); wy = (Tw[1, 1] * ay + Tw[1, 2]).astype(np.float32)
            Lf = remap_img(rgbL, wx, wy); La = remap_img(aL, wx, wy)
            if ef > 0:
                La = La * (1 - ease01(u, end["window"][0] + 0.5 * (end["window"][1] - end["window"][0]), end["window"][1]))
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
