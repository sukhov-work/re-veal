"""Nested-scene zoom probe, one camera (2026-10-17, research only; imports transitions.py and
the layered probe for the canvas, the encoder and the layer source; changes nothing in either tool).

The idea under test, read from the owner's notes on mismatch_5 and mismatch_3 (layered_picks_L7):
scene A is CONTAINED in a region of scene B (the sun is the galaxy's core seen from far; the bar is
what one lounge pane looks onto), and the transition is ONE camera pulling back over a plate that
holds B with A pasted into its container. Nothing slides as a layer: A is rigidly attached to the
plate by a similarity S_A (A's anchor lands on B's anchor), and the camera goes from S_A^-1 (A fills
the frame: frame 0 is A, exactly) to the identity (frame n-1 is B, exactly, after a local finish
inside the container). B is sampled from its full-resolution file, so a magnified B keeps real pixels
up to its own size over the canvas (2x on mismatch_5, 1.33x on mismatch_3).

Canvas rule probed: A's cover crop is placed so that A's anchor sits at the same relative height as
B's anchor (the tool crops at the centre; `crop_anchor` is the director's knob).

Two rim kinds: `soft` (A's matte feathers inward as the camera pulls back and A's colour statistics
move to B's: a container with no hard edge, the core) and `matte` (A is clipped by B's container
matte, B's foreground composites over it: the window pane). Finish: inside the container, A gives
way to B in the order of A's brightness (the luma reveal the owner picked on the boxes), last 22 %.

Usage: nest_probe.py PAIR OUT [--seconds 3] [--fps 30]
"""
import sys, json, math, argparse
from pathlib import Path
import numpy as np, cv2

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts" / "research"))
import transitions as T
import layered_probe as LP

LAYERS = ROOT / "benchmarks/runs/2026-09-28/layers_v3"


def smootherstep(u):
    u = float(min(1.0, max(0.0, u)))
    return u * u * u * (u * (6.0 * u - 15.0) + 10.0)


def element_mask(photo, pred):
    z = np.load(LAYERS / photo / "layers.npz")
    d = json.load(open(LAYERS / photo / "layers.json"))
    el = z["element"]
    m = np.zeros(el.shape, bool)
    for e in d["elements"]:
        if pred(e):
            m |= el == e["id"]
    return m


def bright_disc(rgb, frac=0.90, box=None):
    """Centre and radius of the largest blob whose L is above frac * max L (inside box)."""
    L = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)[..., 0].astype(np.float32)
    sub = np.zeros(L.shape, bool)
    x0, y0, x1, y1 = box if box else (0, 0, L.shape[1], L.shape[0])
    sub[int(y0):int(y1), int(x0):int(x1)] = True
    m = (L >= frac * L[sub].max()) & sub
    n, lab, st, cen = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8)
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    ys, xs = np.nonzero(lab == k)
    return (float(xs.mean()), float(ys.mean())), float(math.sqrt(len(xs) / math.pi))


def cover_anchored(img, w, h, anchor_xy, rel_y):
    """Cover-crop img to w x h with the point anchor_xy (image px) at relative height rel_y
    (clamped so the crop stays inside the image). Returns the crop and the anchor in crop px."""
    H, W = img.shape[:2]
    s = max(w / W, h / H)
    sw, sh = int(round(W * s)), int(round(H * s))
    im = cv2.resize(img, (sw, sh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
    ax, ay = anchor_xy[0] * s, anchor_xy[1] * s
    y0 = int(round(min(max(ay - rel_y * h, 0), sh - h)))
    x0 = int(round(min(max(ax - 0.5 * w, 0), sw - w)))
    return im[y0:y0 + h, x0:x0 + w], (ax - x0, ay - y0)


def lab_transfer(rgb, dst_rgb, dst_mask, strength, weight=None):
    """Reinhard statistics transfer in float32 Lab (no uint8 round trip: that alone costs about
    1 level of mean error, which the first interior frame must not pay). `weight` (H x W in 0-1)
    scales the transfer per pixel. Returns float32 RGB 0-255."""
    if strength <= 0.0:
        return rgb.astype(np.float32)
    w = strength if weight is None else strength * weight[..., None]
    a = cv2.cvtColor(rgb.astype(np.float32) / 255.0, cv2.COLOR_RGB2LAB)
    b = cv2.cvtColor(dst_rgb.astype(np.float32) / 255.0, cv2.COLOR_RGB2LAB)
    out = a.copy()
    for c in range(3):
        ma, sa = a[..., c].mean(), a[..., c].std() + 1e-3
        mb, sb = b[..., c][dst_mask].mean(), b[..., c][dst_mask].std() + 1e-3
        tgt = (a[..., c] - ma) * (sb / sa) + mb
        out[..., c] = a[..., c] + (tgt - a[..., c]) * (w if weight is None else w[..., 0])
    out[..., 0] = np.clip(out[..., 0], 0, 100)
    return np.clip(cv2.cvtColor(out, cv2.COLOR_LAB2RGB) * 255.0, 0, 255).astype(np.float32)


def luma_order(rgb):
    L = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)[..., 0].astype(np.float32)
    L = cv2.GaussianBlur(L, (0, 0), 3.0)
    return (L - L.min()) / max(1.0, L.max() - L.min())


def sample(img_full, k, M_plate_to_frame, W, H, border=0):
    """Sample a full-resolution image (plate px = full px / k) into the frame through M
    (2x3, plate -> frame). Minification goes through a pre-resize with INTER_AREA."""
    s = M_plate_to_frame[0, 0] / k
    if s < 1.0:
        small = cv2.resize(img_full, (max(1, int(round(img_full.shape[1] * s))), max(1, int(round(img_full.shape[0] * s)))), interpolation=cv2.INTER_AREA)
        ks = img_full.shape[1] / small.shape[1]           # full px per small px
        M = M_plate_to_frame.copy(); M[:, :2] *= ks / k   # small -> frame
        return cv2.warpAffine(small, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=border)
    M = M_plate_to_frame.copy(); M[:, :2] /= k
    return cv2.warpAffine(img_full, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=border)


def camera_path(S_A, W, H):
    """Similarities camera(t) with camera(0) = S_A^-1 and camera(1) = I, a zoom about the fixed
    point of S_A. S_A is 2x3 (A canvas -> plate)."""
    s1 = float(S_A[0, 0]); tx, ty = float(S_A[0, 2]), float(S_A[1, 2])
    q = np.array([tx / (1 - s1), ty / (1 - s1)], np.float32)   # S_A q = q
    z0 = 1.0 / s1

    def cam(e):
        z = math.exp(math.log(z0) * (1 - e))
        return np.array([[z, 0, q[0] - z * q[0]], [0, z, q[1] - z * q[1]]], np.float32)
    return cam, q, z0


def compose(M2, M1):
    """M2 o M1 for 2x3 affines."""
    A2 = np.vstack([M2, [0, 0, 1]]); A1 = np.vstack([M1, [0, 0, 1]])
    return (A2 @ A1)[:2].astype(np.float32)


def run(pair, out, seconds, fps):
    S, F = LP.find_pair(pair)
    A_full, B_full = T.load_image_rgb(str(S)), T.load_image_rgb(str(F))
    W, H = T.common_canvas(A_full, B_full, 1920, "finish")
    B = T.cover(B_full, W, H)
    kB = B_full.shape[1] / W if abs(B_full.shape[1] / B_full.shape[0] - W / H) < 0.01 else None
    if kB is None:                                        # B's cover crop is not the full file: sample the canvas instead
        B_full, kB = B, 1.0
    info = {"canvas": [W, H]}
    if pair == "mismatch_5":
        cA_full, rA_full = bright_disc(A_full, 0.90)
        cB, rB = bright_disc(B, 0.80, (850, 440, 1080, 600))
        A, cA = cover_anchored(A_full, W, H, cA_full, cB[1] / H)
        rA = rA_full * max(W / A_full.shape[1], H / A_full.shape[0])
        s1 = rB / rA
        S_A = np.array([[s1, 0, cB[0] - s1 * cA[0]], [0, s1, cB[1] - s1 * cA[1]]], np.float32)
        info.update(A_sun=[round(cA[0]), round(cA[1])], A_r=round(rA), B_core=[round(cB[0]), round(cB[1])], B_r=round(rB), end_scale=round(s1, 4), rim="soft")
        skyB = element_mask("mismatch_5_F", lambda e: e["group"] == "sky")
        container = None
        # A's layers, photometric (the layer source's masks sit on the centred crop, not on this one):
        # the sun (bright disc, dilated), the silhouettes and the bridge (dark), the sky above the
        # bridge's top row, the water below it. The sky dissolves dark-first into B's sky (the rim goes
        # first); the sun, bridge and water stay until the finish.
        LA = cv2.cvtColor(A, cv2.COLOR_RGB2LAB)[..., 0].astype(np.float32)
        sunA = cv2.dilate((LA >= 0.70 * LA.max()).astype(np.uint8), np.ones((13, 13), np.uint8)).astype(bool)
        sunC = cv2.dilate((LA >= 0.85 * LA.max()).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)   # the disc itself, for the colour path
        # the bridge and the silhouettes are black (row median L 2-6) and the sky above the sun is dark
        # red-brown (row median L 9-40): the bridge's top is the first row under the sun's centre
        # whose median L falls under 8
        med = np.median(LA, axis=1)
        top_bridge = int(cA[1]) + int(np.argmax(med[int(cA[1]):] < 8))
        dark = LA < 8
        skyA = np.zeros((H, W), bool); skyA[:top_bridge] = True; skyA &= ~sunA
        # the sky's order: dark first AND from the frame's edge inward (the distance transform of
        # the sky to the frame border, normalised), so no straight border of A ever shows
        lum = cv2.GaussianBlur(LA, (0, 0), 4.0); lum = (lum - lum[skyA].min()) / max(1.0, lum[skyA].max() - lum[skyA].min())
        sky_order = np.clip(lum, 0, 1)
        cw = np.clip(1.0 - sky_order, 0, 1).astype(np.float32); cw[sunC] = 0.0   # the colour path's weight: dark sky 1, the glow 0
        # the rest of A (sun, bridge band) keeps its own soft matte: the sun's disc, the bridge band
        # with its ends tapered over the outer 15 % of the width (no cut end when A shrinks)
        keepA = (~skyA).astype(np.float32)
        xs = np.arange(W, dtype=np.float32) / (W - 1)
        taper = np.clip(np.minimum(xs, 1 - xs) / 0.15, 0, 1)[None, :]
        band = np.zeros((H, W), np.float32); band[top_bridge:] = 1.0
        ys = np.arange(H, dtype=np.float32) / (H - 1)
        vtaper = np.clip((1 - ys) / 0.10, 0, 1)[:, None]            # and over the bottom 10 % of the rows
        keepA = np.where(band > 0, keepA * taper * vtaper, keepA)
        keepA = cv2.GaussianBlur(keepA, (0, 0), 3.0)
        info.update(bridge_top_row=top_bridge, sun_glow_share=round(float(sunA.mean()), 4), sun_disc_share=round(float(sunC.mean()), 4), sky_share=round(float(skyA.mean()), 4))
    else:
        A = T.cover(A_full, W, H)
        win_el = element_mask("mismatch_3_F", lambda e: e["label"] == "window")
        ys, xs = np.nonzero(win_el)
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        # the container is the glass: the window's box minus what stands in front of the glass
        # (people, furniture, the ceiling, the walls); the trees and the building seen THROUGH the
        # glass are separate elements of the layer source and belong to the container
        front = element_mask("mismatch_3_F", lambda e: e["group"] in ("person", "furniture", "ceiling", "wall", "object"))
        win = np.zeros((H, W), np.uint8); win[y0:y1 + 1, x0:x1 + 1] = 1
        win[front] = 0
        win = cv2.morphologyEx(win, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        # A fits the largest canvas-aspect rectangle of clear glass (under 0.5 % of its pixels
        # covered by an element in front), so nothing stands in front of A at frame 0 and B's
        # people enter from the frame's edge as the camera pulls back
        integ = cv2.integral(1 - win)
        best = None
        for sc in np.linspace(0.70, 0.20, 51):
            rw, rh = int(round(sc * W)), int(round(sc * H))
            for ry in range(int(y0), int(y1) - rh + 2, 8):
                for rx in range(int(x0), int(x1) - rw + 2, 8):
                    bad = integ[ry + rh, rx + rw] - integ[ry, rx + rw] - integ[ry + rh, rx] + integ[ry, rx]
                    if bad <= 0.005 * rw * rh:
                        best = (sc, rx, ry, rw, rh); break
                if best: break
            if best: break
        sc, rx, ry, rw, rh = best
        s1 = float(sc)
        S_A = np.array([[s1, 0, rx], [0, s1, ry]], np.float32)
        win = cv2.GaussianBlur(win.astype(np.float32), (0, 0), 1.0)
        info.update(window_box=[int(x0), int(y0), int(x1), int(y1)], glass_share=round(float((win > 0.5).mean()), 4), pane=[int(rx), int(ry), int(rw), int(rh)], end_scale=round(s1, 4), rim="matte")
        container = win
    cam, q, z0 = camera_path(S_A, W, H)
    info.update(zoom_centre=[round(float(q[0])), round(float(q[1]))], start_zoom=round(z0, 3))
    orderA = luma_order(A)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dframe = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, H - 1 - yy))
    one = np.ones((H, W), np.float32)
    n = int(round(seconds * fps))
    enc = T.FrameEncoder(out / "transition.mp4", W, H, fps)
    keep = []
    for i in range(n):
        u = i / (n - 1)
        e = smootherstep(u)
        C = cam(e)                                   # plate -> frame
        MA = compose(C, S_A)                         # A canvas -> frame
        s = float(MA[0, 0])
        Bf = sample(B_full, kB, C, W, H)
        if pair == "mismatch_5":
            # the sky moves toward B's sky statistics by its darkness (the glow and the sun keep
            # their colour, so no ring forms at the sun's edge)
            Ac = lab_transfer(A, B, skyB, 0.85 * e, weight=cw) if e > 0 else A.astype(np.float32)
        else:
            Ac = A.astype(np.float32)
        Af = sample(Ac, 1.0, MA, W, H)
        inside = cv2.warpAffine(one, MA, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        if container is None:
            # A's sky dissolves into B's sky from the first frame on, dark pixels and the frame's edge
            # first, over 0..0.75 of the clip; the sun and the bridge band keep their own soft mattes
            # a luma key: every sky pixel's alpha falls with its darkness as the key rises, so the
            # matte is shaped by the sun's glow and never by A's frame
            es = smootherstep(u / 0.45)                  # the key runs ahead of the camera: the dark sky is gone before B's margin is wide
            key = -0.10 + 1.10 * es                      # -0.10: nothing keyed (frame 1 equals A); 1: all of the sky
            a_sky = np.clip((sky_order - key) / 0.10, 0, 1)   # a narrow band: the matte's edge is an iso-line of the glow, never the frame
            keep_t = 1.0 - (1.0 - keepA) * es                 # the band's tapers fade in with the key (frame 1 equals A)
            a_src = np.where(skyA, a_sky, keep_t).astype(np.float32)
            a_src = np.maximum(a_src, keep_t)
            aA = cv2.warpAffine(a_src, MA, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        else:
            cont = cv2.warpAffine(container, C, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
            aA = inside * cont                       # A is seen only through the glass; B's front is where the glass is not
        # the finish: inside the container, A gives way to B in A's brightness order (bright first)
        ef = smootherstep((u - 0.78) / 0.22)
        if ef > 0:
            of = cv2.warpAffine(orderA, MA, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
            a_fin = np.clip((of + ef * 1.3 - 1.0) / 0.16, 0, 1)
            a_fin = cv2.GaussianBlur(a_fin, (0, 0), 1.2)
            aA = aA * (1 - a_fin)
        frame = Bf * (1 - aA[..., None]) + Af * aA[..., None]
        if i == 0:
            frame = A.astype(np.float32)
        if i == n - 1:
            frame = B.astype(np.float32)
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
    info.update(frames=len(steps) + 1, step_first=round(steps[0], 2), step_second=round(steps[1], 2), step_last=round(steps[-1], 2), step_max=round(max(steps), 2))
    return keep, info


def montage(frames, path, cols=3):
    th = [cv2.resize(f, (f.shape[1] // 3, f.shape[0] // 3), interpolation=cv2.INTER_AREA) for f in frames]
    rows = [np.concatenate(th[i:i + cols], 1) for i in range(0, len(th) - len(th) % cols, cols)]
    cv2.imwrite(str(path), cv2.cvtColor(np.concatenate(rows, 0), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pair"); ap.add_argument("out"); ap.add_argument("--seconds", type=float, default=3.0); ap.add_argument("--fps", type=int, default=30)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    keep, info = run(a.pair, out, a.seconds, a.fps)
    montage(keep, out / "montage.jpg")
    json.dump(info, open(out / "info.json", "w"), indent=1)
    print(json.dumps(info))
