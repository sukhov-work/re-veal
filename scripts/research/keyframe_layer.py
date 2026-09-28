#!/usr/bin/env python3
"""Keyframes inside the layered probe (research probe; 2026-09-28, Track B2).

Nothing here enters transitions.py. The layered composite C(t) comes from a FROZEN copy of the
round-5 probe (`git show a244d8a:scripts/research/layered_probe.py > _frozen_layered_probe_r5.py`,
md5 7544463a...), rendered exactly as its `render_score` does, so C(t) is the source clip's frame
byte for byte (checked: the re-encoded source mp4 must have the source clip's md5).

A keyframe K_k is a FLUX.2 klein 9B clean-up of C(t_k) made on the box. It gives the clip a
CORRECTION, not a picture to fade to:

    K_k      resized to the canvas (INTER_CUBIC), registered onto C(t_k) on locally normalised L (a
             global ECC affine, refused beyond 24 px at a corner, then a DIS residual smoothed by 16 px and
             capped at 8 px), then Lab-matched to C(t_k) per layer matte: for every rendered
             layer j of the probe at t_k its visible weight v_j = alpha_j * prod(1 - alpha_above);
             per channel (x - mean_K,j) * clip(std_C,j / std_K,j, gain_clip) + mean_C,j, blended by v_j
    D_k      = band(K'_k - C(t_k)) on the variant's channels; band = identity - GaussianBlur(sigma)
             (sigma 0 = the whole correction)
    frame(t) = C(t) + g * sum_k w_k(t) * carry_{t_k -> t}(D_k)            (Lab, then RGB, rounded)

carry: chained OpenCV DIS flows between consecutive composite frames (L channel, half resolution,
smoothed), composed outward from t_k: the probe does not expose one per-pixel motion of the
composite (each layer has its own field, progress and mix), so this is the named fallback.
w_k: a partition of unity of raised cosines over the knots [1, t_1, ..., t_K, n - 2] in frame index,
so w = 0 at frames 0, 1, n - 2, n - 1, sum_k w_k = 1 on [t_1, t_K], zero slope at every knot.
A frame whose total weight is 0 is the composite's own uint8 frame, untouched.

Subcommands
  select --probe FROZEN --score S --out DIR [--expect-md5 M] [--k 3] [--sep 15]
      renders C, checks the md5, measures per interior frame how far C_i stands from the nearer photo and
      picks up to k frames greedily by d_i = mean over pixels of min(|C_i - A|, |C_i - B|) (at least `sep` frames apart, frames 3..n-4); writes
      comp_fNNN.png (canvas size), A.png, B.png, select.json.
  clip --probe FROZEN --score S --select DIR --keys f22=kf.png,... --out DIR [--src-mp4 M]
      renders the variants a/b/c into DIR/<tag>/ (probe layout) and measures them beside the source.
  table --out DIR   prints the measures of every tag under DIR in one table.

numpy + cv2 + transitions + the frozen probe; no torch, no network.
"""
import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import transitions as T  # noqa: E402

VARIANTS = {
    # tag: (band sigma px at the canvas, channels, peak gain g)
    "keylayer_a": {"sigma": 4.0, "channels": [0], "g": 1.0,
                   "what": "fine detail band of the correction (L only, sigma 4 px)"},
    "keylayer_b": {"sigma": 24.0, "channels": [0, 1, 2], "g": 1.0,
                   "what": "detail + structure band of the correction (Lab, sigma 24 px)"},
    "keylayer_c": {"sigma": 0.0, "channels": [0, 1, 2], "g": 1.0,
                   "what": "the whole correction (Lab): at t_k the frame is the matched keyframe"},
}
GAIN_CLIP = (0.4, 2.5)          # the probe's default `gain_clip`
REG_SIGMA = 16.0                # px at the canvas: the registration flow's smoothing
FLOW_SIGMA = 4.0                # px at the canvas: the carry flows' smoothing


def load_probe(path):
    spec = importlib.util.spec_from_file_location("probe_frozen_r5", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_rgb(p):
    im = cv2.imread(str(p), cv2.IMREAD_COLOR)
    if im is None:
        raise SystemExit(f"cannot read {p}")
    return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)


def write_rgb(p, rgb):
    cv2.imwrite(str(p), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))


def mad(a, b):
    return float(np.abs(a.astype(np.int16) - b.astype(np.int16)).mean())


def md5_file(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def render_source(P, score, seed=0, sheet_path=None):
    """The source clip's frames exactly as the frozen probe's render_score makes them (the layer
    sheet is rendered first, as there, so every lazy field is prepared in the same order)."""
    A, B = P.canvas_pair(score["pair"], score.get("max_long", 1920))
    scene = P.Scene(A, B, seed)
    n = max(2, int(round(score.get("seconds", 2.0) * float(score.get("fps", 30)))))
    scene.n = n
    layers = P.build_layers(scene, score)
    P.layer_sheet(layers, sheet_path or (Path("/dev/null")))
    scene.n = n
    frames = []
    for i in range(n):
        if i == 0:
            frames.append(A.copy())
        elif i == n - 1:
            frames.append(B.copy())
        else:
            frames.append(P.composite(layers, i / (n - 1)))
    return A, B, scene, layers, frames, n


def encode(path, frames, fps=30.0):
    h, w = frames[0].shape[:2]
    enc = T.FrameEncoder(path, w, h, fps)
    try:
        for f in frames:
            enc.write(f)
        enc.close()
    except BaseException:
        enc.abort()
        raise
    return md5_file(path)


# ---------------------------------------------------------------------------
# select
# ---------------------------------------------------------------------------

def lap_var_L(rgb):
    L = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)[..., 0]
    return float(cv2.Laplacian(L, cv2.CV_32F, ksize=1).var())


def cmd_select(a):
    P = load_probe(a.probe)
    score = json.loads(Path(a.score).read_text())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    A, B, scene, layers, frames, n = render_source(P, score, a.seed, out / "layers.jpg")
    rs = round(time.time() - t0, 1)
    m = encode(out / "source_check.mp4", frames)
    if a.expect_md5 and m != a.expect_md5:
        raise SystemExit(f"source md5 {m} != expected {a.expect_md5}")
    rows = []
    for i in range(n):
        rows.append({"i": i, "t": round(i / (n - 1), 4), "mad_A": round(mad(frames[i], A), 3),
                     "mad_B": round(mad(frames[i], B), 3), "lap": round(lap_var_L(frames[i]), 2)})
        rows[-1]["d_global"] = min(rows[-1]["mad_A"], rows[-1]["mad_B"])
        # per pixel: how far the composite stands from the nearer photo at that pixel (a place that is
        # between the two photos, a double exposure or a seam, counts; a global brightness shift counts too)
        da = np.abs(frames[i].astype(np.int16) - A.astype(np.int16)).mean(-1)
        db = np.abs(frames[i].astype(np.int16) - B.astype(np.int16)).mean(-1)
        rows[-1]["d"] = round(float(np.minimum(da, db).mean()), 3)
    cand = sorted(range(3, n - 3), key=lambda i: -rows[i]["d"])
    pick = []
    for i in cand:
        if all(abs(i - j) >= a.sep for j in pick):
            pick.append(i)
        if len(pick) == a.k:
            break
    pick.sort()
    write_rgb(out / "A.png", A)
    write_rgb(out / "B.png", B)
    for i in pick:
        write_rgb(out / f"comp_f{i:03d}.png", frames[i])
    res = {"probe": str(a.probe), "probe_md5": md5_file(a.probe), "score": str(a.score), "pair": score["pair"],
           "canvas": [A.shape[1], A.shape[0]], "n": n, "render_s": rs, "source_md5": m,
           "rule": f"d_i = mean over pixels of min(|C_i - A|, |C_i - B|) (channel-mean, 8-bit RGB levels); greedy by d_i over frames 3..{n - 4}, "
                   f"at least {a.sep} frames apart, {a.k} at most",
           "picked": [{"i": i, "t": rows[i]["t"], "d": rows[i]["d"], "d_global": rows[i]["d_global"], "mad_A": rows[i]["mad_A"], "mad_B": rows[i]["mad_B"],
                       "lap": rows[i]["lap"], "file": f"comp_f{i:03d}.png"} for i in pick],
           "d_max": max(r["d"] for r in rows), "d_argmax": int(max(range(n), key=lambda i: rows[i]["d"])),
           "lap_min": min(r["lap"] for r in rows[1:-1]), "lap_argmin": int(min(range(1, n - 1), key=lambda i: rows[i]["lap"])),
           "per_frame": rows}
    (out / "select.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("pair", "source_md5", "render_s", "picked", "d_argmax", "lap_argmin")}))


# ---------------------------------------------------------------------------
# clip
# ---------------------------------------------------------------------------

def L_u8(rgb):
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)[..., 0]


def dis():
    d = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    return d


def half(img):
    return cv2.resize(img, (img.shape[1] // 2, img.shape[0] // 2), interpolation=cv2.INTER_AREA)


def flow_half(D, f0, f1, sigma_half):
    """DIS flow at half resolution from f0 to f1 (for x in f0: f0(x) ~ f1(x + flow)), smoothed; half-res px."""
    fl = D.calc(half(L_u8(f0)), half(L_u8(f1)), None)
    if sigma_half > 0:
        fl = cv2.GaussianBlur(fl, (0, 0), sigma_half)
    return fl


def to_full(disp_half, W, H):
    """A half-resolution displacement (half px) -> full-resolution absolute sampling maps."""
    d = cv2.resize(disp_half, (W, H), interpolation=cv2.INTER_LINEAR) * 2.0
    gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    return gx + d[..., 0], gy + d[..., 1]


REG_CAP = 8.0          # px at the canvas: the largest local registration residual
REG_AFFINE_MAX = 24.0  # px: an ECC affine that moves any corner farther is refused (identity)


def local_norm(rgb, sigma=12.0):
    """L with its local mean removed and divided by its local std (half resolution): structure
    without exposure, so a registration does not fit a brightness change."""
    L = half(cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)[..., 0]).astype(np.float32)
    m = cv2.GaussianBlur(L, (0, 0), sigma)
    d = L - m
    s = np.sqrt(cv2.GaussianBlur(d * d, (0, 0), sigma) + 4.0)
    return d / s


def register(C, K, D):
    """K (already at the canvas size) aligned onto C: ECC affine on local_norm, then a DIS
    residual on local_norm, smoothed by REG_SIGMA and capped at REG_CAP px. Returns K aligned and
    the numbers (affine corner shift px, ECC correlation, residual magnitude map)."""
    H, W = C.shape[:2]
    nc, nk = local_norm(C), local_norm(K)
    warp = np.eye(2, 3, dtype=np.float32)
    info = {}
    try:
        cc, warp = cv2.findTransformECC(nc, nk, warp, cv2.MOTION_AFFINE,
                                        (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6), None, 5)
        info["ecc_cc"] = round(float(cc), 4)
    except cv2.error as e:
        info["ecc_error"] = str(e)[:120]
        warp = np.eye(2, 3, dtype=np.float32)
    full = warp.copy()
    full[:, 2] *= 2.0
    corners = np.array([[0, 0, 1], [W, 0, 1], [0, H, 1], [W, H, 1]], np.float32)
    shift = float(np.abs(corners @ full.T - corners[:, :2]).max())
    info["affine_corner_px"] = round(shift, 2)
    if shift > REG_AFFINE_MAX:
        info["affine_refused"] = True
        full = np.eye(2, 3, dtype=np.float32)
    info["affine"] = [[round(float(x), 5) for x in r] for r in full]
    Ka = cv2.warpAffine(K, full, (W, H), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
    na = local_norm(Ka)
    u8 = lambda x: np.clip(x * 40.0 + 128.0, 0, 255).astype(np.uint8)
    fl = D.calc(u8(nc), u8(na), None)
    fl = cv2.GaussianBlur(fl, (0, 0), REG_SIGMA / 2.0)
    mag = np.sqrt((fl ** 2).sum(-1)) * 2.0
    scale = np.minimum(1.0, REG_CAP / np.maximum(mag, 1e-6))
    fl = fl * scale[..., None]
    info["residual_capped_share"] = round(float((mag > REG_CAP).mean()), 4)
    mx, my = to_full(fl, W, H)
    Kr = cv2.remap(Ka, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    # the residual is kept only when it raises the correlation of the normalised structure (on
    # kf_25 it lowered it, 0.391 -> 0.368: DIS fitted invented clouds)
    corr = lambda a, b: float(np.corrcoef(a.ravel(), b.ravel())[0, 1])
    c0, c1, c2 = corr(nc, nk), corr(nc, na), corr(nc, local_norm(Kr))
    info["struct_corr"] = {"raw": round(c0, 3), "affine": round(c1, 3), "affine+residual": round(c2, 3)}
    if c2 <= c1:
        info["residual_dropped"] = True
        info["_mag"] = np.zeros_like(mag)
        return Ka, info
    info["_mag"] = np.minimum(mag, REG_CAP)
    return Kr, info


def carry_maps(frames, k, lo, hi, sigma_half):
    """For every frame i in [lo, hi] the half-resolution displacement to frame k (where the pixel x
    of frame i was in frame k) and a validity map, composed from consecutive DIS flows."""
    H2, W2 = frames[0].shape[0] // 2, frames[0].shape[1] // 2
    gx, gy = np.meshgrid(np.arange(W2, dtype=np.float32), np.arange(H2, dtype=np.float32))
    D = dis()
    maps = {k: (np.zeros((H2, W2, 2), np.float32), np.ones((H2, W2), np.float32))}
    for step in (1, -1):
        disp, val = maps[k]
        i = k + step
        while lo <= i <= hi:
            fl = flow_half(D, frames[i], frames[i - step], sigma_half)      # x in frame i -> frame i - step
            mx, my = gx + fl[..., 0], gy + fl[..., 1]
            prev_abs = np.dstack([gx + disp[..., 0], gy + disp[..., 1]])
            new_abs = cv2.remap(prev_abs, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            inside = ((mx >= 0) & (mx <= W2 - 1) & (my >= 0) & (my <= H2 - 1)).astype(np.float32)
            val = cv2.remap(val, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0) * inside
            disp = np.dstack([new_abs[..., 0] - gx, new_abs[..., 1] - gy]).astype(np.float32)
            maps[i] = (disp, val)
            i += step
    return maps


def weights(n, knots_mid):
    """Partition of unity of raised cosines over [1] + knots_mid + [n - 2]; returns (K, n)."""
    knots = [1] + list(knots_mid) + [n - 2]
    K = len(knots_mid)
    w = np.zeros((K, n), np.float64)
    for j in range(K):
        a, c, b = knots[j], knots[j + 1], knots[j + 2]
        for i in range(n):
            if a < i <= c:
                s = (i - a) / float(c - a)
                w[j, i] = 0.5 - 0.5 * np.cos(np.pi * s)
            elif c < i < b:
                s = (i - c) / float(b - c)
                w[j, i] = 0.5 + 0.5 * np.cos(np.pi * s)
    # the outer ramps end at the guard knots: zero at frames <= 1 and >= n - 2
    w[:, :2] = 0.0
    w[:, n - 2:] = 0.0
    return w


def visible_weights(layers, t):
    """Per rendered layer its visible weight at t (alpha times the transparency of every layer above)."""
    alphas = []
    for lay in layers:
        _, al = lay.render(t)
        alphas.append(np.clip(np.asarray(al, np.float32), 0, 1))
    vis = []
    above = np.ones_like(alphas[0])
    for al in reversed(alphas):
        vis.append(al * above)
        above = above * (1.0 - al)
    vis.reverse()
    return vis


def match_per_layer(P, lab_k, lab_c, vis, names, gain_clip):
    """Lab statistics of the keyframe matched to the composite's per layer matte (weights vis)."""
    out = np.zeros_like(lab_k)
    tot = np.zeros(lab_k.shape[:2], np.float32)
    info = []
    area = lab_k.shape[0] * lab_k.shape[1]
    for v, nm in zip(vis, names):
        if float(v.sum()) < 0.005 * area:
            continue
        sk, sc = P.lab_stats(lab_k, v), P.lab_stats(lab_c, v)
        out += P.lab_match(lab_k, sk, sc, gain_clip) * v[..., None]
        tot += v
        info.append({"layer": nm, "share": round(float(v.sum()) / area, 4),
                     "K_mean": [round(float(x), 2) for x in sk[:, 0]], "C_mean": [round(float(x), 2) for x in sc[:, 0]],
                     "gain": [round(float(np.clip(sc[c, 1] / sk[c, 1], *gain_clip)), 3) for c in range(3)]})
    ones = np.ones(lab_k.shape[:2], np.float32)
    g = P.lab_match(lab_k, P.lab_stats(lab_k, ones), P.lab_stats(lab_c, ones), gain_clip)
    rest = np.clip(1.0 - tot, 0, 1)
    out = (out + g * rest[..., None]) / np.maximum(tot + rest, 1e-6)[..., None]
    return out.astype(np.float32), info


def lab_mean(lab):
    return [round(float(lab[..., c].mean()), 2) for c in range(3)]


def decode(path):
    cap = cv2.VideoCapture(str(path))
    fr = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        fr.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
    cap.release()
    return fr


def measures(frames, state_idx, D=None):
    """The table's measures on a decoded frame list; state_idx = [0, t_1.., n-1]."""
    n = len(frames)
    labs = [T.lab_of(f) for f in frames]
    Lm = [float(l[..., 0].mean()) for l in labs]
    jumps = np.abs(np.diff(Lm))
    steps = np.array([mad(frames[i], frames[i + 1]) for i in range(n - 1)])
    lap = np.array([lap_var_L(f) for f in frames])
    stalls = []
    for i in range(n - 1):
        nb = [steps[j] for j in range(max(0, i - 3), min(n - 1, i + 4)) if j != i]
        if steps[i] < 0.5 * float(np.mean(nb)):
            stalls.append(i)
    near = []
    for k in state_idx[1:-1]:
        js = list(range(max(0, k - 3), min(n - 1, k + 3)))
        jmin = min(js, key=lambda j: steps[j])
        nb = [steps[j] for j in range(max(0, jmin - 3), min(n - 1, jmin + 4)) if j != jmin]
        near.append({"t_k": k, "min_step": round(float(steps[jmin]), 3), "at": f"{jmin}->{jmin + 1}",
                     "nbr_mean": round(float(np.mean(nb)), 3), "ratio": round(float(steps[jmin] / max(np.mean(nb), 1e-6)), 3)})
    # fade R^2 of each step against the difference of the two nearest states, and the step's DIS displacement
    D = D or dis()
    r2, disp = [], []
    for i in range(n - 1):
        a = max(s for s in state_idx if s <= i)
        b = min(s for s in state_idx if s > i)
        d = (labs[i + 1][..., 0] - labs[i][..., 0]).ravel().astype(np.float64)
        Dv = (labs[b][..., 0] - labs[a][..., 0]).ravel().astype(np.float64)
        dd = float(d @ d)
        if dd < 1e-9 or float(Dv @ Dv) < 1e-9:
            r2.append(float("nan"))
        else:
            beta = float(d @ Dv) / float(Dv @ Dv)
            r2.append(1.0 - float(((d - beta * Dv) ** 2).sum()) / dd)
        fl = D.calc(half(L_u8(frames[i])), half(L_u8(frames[i + 1])), None)
        disp.append(2.0 * float(np.sqrt((fl ** 2).sum(-1)).mean()))
    r2 = np.array(r2)
    segs = []
    for a, b in zip(state_idx[:-1], state_idx[1:]):
        seg = r2[a:b]
        segs.append({"span": [a, b], "fade_r2_mean": round(float(np.nanmean(seg)), 3),
                     "disp_px_mean": round(float(np.mean(disp[a:b])), 2)})
    lapj = np.abs(np.diff(lap)) / np.maximum(np.minimum(lap[:-1], lap[1:]), 1e-6)
    return {
        "meanL": [round(x, 2) for x in Lm], "meanL_range": [round(min(Lm), 2), round(max(Lm), 2)],
        "meanL_max_jump": round(float(jumps.max()), 3), "meanL_max_jump_at": int(jumps.argmax()),
        "steps": [round(float(x), 3) for x in steps], "step_median": round(float(np.median(steps)), 3),
        "stalls": stalls, "near_keys": near,
        "lap": [round(float(x), 1) for x in lap], "lap_median": round(float(np.median(lap[1:-1])), 1),
        "lap_max_rel_jump": round(float(lapj.max()), 3), "lap_max_rel_jump_at": int(lapj.argmax()),
        "fade_r2": [None if np.isnan(x) else round(float(x), 3) for x in r2],
        "fade_r2_mean": round(float(np.nanmean(r2)), 3), "disp_px": [round(x, 2) for x in disp],
        "disp_px_mean": round(float(np.mean(disp)), 2), "segments": segs,
    }


def compact(m):
    return {k: m[k] for k in ("meanL_range", "meanL_max_jump", "meanL_max_jump_at", "step_median", "stalls", "near_keys",
                              "lap_median", "lap_max_rel_jump", "lap_max_rel_jump_at", "fade_r2_mean", "disp_px_mean", "segments")}


def cmd_clip(a):
    t_all = time.time()
    P = load_probe(a.probe)
    score = json.loads(Path(a.score).read_text())
    sel = json.loads((Path(a.select) / "select.json").read_text())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    work = out / "_work"
    work.mkdir(exist_ok=True)
    A, B, scene, layers, frames, n = render_source(P, score, a.seed, work / "layers.jpg")
    H, W = A.shape[:2]
    src_md5 = encode(work / "source_check.mp4", frames)
    if src_md5 != sel["source_md5"]:
        raise SystemExit(f"source render md5 {src_md5} != select's {sel['source_md5']}")
    if a.src_mp4 and md5_file(a.src_mp4) != src_md5:
        raise SystemExit(f"--src-mp4 md5 {md5_file(a.src_mp4)} != the re-encoded source {src_md5}")
    keys = []
    for tok in a.keys.split(","):
        fi, path = tok.split("=", 1)
        keys.append((int(fi.lstrip("f")), Path(path)))
    keys.sort()
    kidx = [k for k, _ in keys]
    names = [l.name for l in layers]
    Dreg = dis()
    corr = []          # per keyframe: the Lab correction K' - C(t_k) at the canvas (float32 Lab)
    kinfo = []
    for k, path in keys:
        t = k / (n - 1)
        Kr = read_rgb(path)
        Kup = cv2.resize(Kr, (W, H), interpolation=cv2.INTER_CUBIC)
        Ck = frames[k]
        # registration (a raw-L DIS flow fitted the keyframe's exposure change and moved kf_25 by
        # 217 px on average; first render 2026-09-28): on locally normalised L, a global affine by
        # ECC, then a smoothed DIS residual capped at REG_CAP px
        Kup, reg = register(Ck, Kup, Dreg)
        mag = reg.pop("_mag")
        Kreg = Kup
        lab_k, lab_c = T.lab_of(Kreg), T.lab_of(Ck)
        vis = visible_weights(layers, t)
        lab_km, minfo = match_per_layer(P, lab_k, lab_c, vis, names, GAIN_CLIP)
        corr.append(lab_km - lab_c)
        write_rgb(work / f"K_matched_f{k:03d}.png", T.to_u8(P.lab_to_rgb(lab_km)))
        kinfo.append({"frame": k, "t": round(t, 4), "file": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                      "size": [Kr.shape[1], Kr.shape[0]],
                      "reg_px": {"mean": round(float(mag.mean()), 2), "p95": round(float(np.percentile(mag, 95)), 2),
                                 "max": round(float(mag.max()), 2), **reg},
                      "meanLab_C": lab_mean(lab_c), "meanLab_K_raw": lab_mean(T.lab_of(Kup)), "meanLab_K_reg": lab_mean(lab_k),
                      "meanLab_K_matched": lab_mean(lab_km),
                      "mad_K_raw_vs_C": round(mad(Kup, Ck), 2), "mad_K_matched_vs_C": round(mad(T.to_u8(P.lab_to_rgb(lab_km)), Ck), 2),
                      "per_layer": minfo})
        print(json.dumps({x: kinfo[-1][x] for x in ("frame", "reg_px", "meanLab_C", "meanLab_K_raw", "meanLab_K_matched")}), flush=True)
    w = weights(n, kidx)
    lo_hi = []
    for j, k in enumerate(kidx):
        nz = np.nonzero(w[j])[0]
        lo_hi.append((int(nz.min()), int(nz.max())))
    maps = [carry_maps(frames, k, lo, hi, FLOW_SIGMA / 2.0) for k, (lo, hi) in zip(kidx, lo_hi)]
    carry_s = round(time.time() - t_all, 1)
    # the source clip's measures (decoded), once
    D = dis()
    src_dec = decode(a.src_mp4 or (work / "source_check.mp4"))
    states = [0] + kidx + [n - 1]
    src_meas = measures(src_dec, states, D)
    src_codec = [mad(x, y) for x, y in zip(src_dec, frames)]
    (out / "source_measures.json").write_text(json.dumps({"mp4": str(a.src_mp4 or ""), "md5": src_md5, "states": states,
                                                          "codec_loss_mad": {"mean": round(float(np.mean(src_codec)), 3),
                                                                             "max": round(float(np.max(src_codec)), 3)},
                                                          "measures": src_meas}, indent=1))
    tags = a.tags.split(",") if a.tags else list(VARIANTS)
    for tag in tags:
        v = VARIANTS[tag]
        t0 = time.time()
        ch = v["channels"]
        bands = []
        for c in corr:
            dcorr = np.zeros_like(c)
            for cc in ch:
                x = c[..., cc]
                dcorr[..., cc] = x - cv2.GaussianBlur(x, (0, 0), v["sigma"]) if v["sigma"] > 0 else x
            bands.append(dcorr)
        outf = []
        h = hashlib.md5()
        for i in range(n):
            tot = float(w[:, i].sum())
            if tot <= 0:
                f = frames[i]
            else:
                add = np.zeros((H, W, 3), np.float32)
                for j in range(len(kidx)):
                    if w[j, i] <= 0:
                        continue
                    disp, val = maps[j][i]
                    mx, my = to_full(disp, W, H)
                    vf = cv2.resize(val, (W, H), interpolation=cv2.INTER_LINEAR)
                    cb = cv2.remap(bands[j], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
                    add += np.float32(w[j, i]) * cb * vf[..., None]
                lab = T.lab_of(frames[i]) + np.float32(v["g"]) * add
                lab[..., 0] = np.clip(lab[..., 0], 0, 100)
                f = T.to_u8(P.lab_to_rgb(lab))
            outf.append(f)
            h.update(np.ascontiguousarray(f).tobytes())
        render_s = round(time.time() - t0, 1)
        d = out / tag
        d.mkdir(parents=True, exist_ok=True)
        mp4_md5 = encode(d / "transition.mp4", outf)
        stats = T.StreamStats(n)
        for i, f in enumerate(outf):
            stats.add(i, f)
            if i in (n // 4, n // 2, 3 * n // 4):
                cv2.imwrite(str(d / f"frame_{i:03d}.jpg"), cv2.cvtColor(f, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
        ok, buf = cv2.imencode(".jpg", cv2.cvtColor(stats.strip(), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
        if ok:
            (d / "strip.jpg").write_bytes(buf.tobytes())
        q = stats.quality(A, B)
        q["first_interior_vs_A"] = round(mad(outf[1], A), 2)
        q["last_interior_vs_B"] = round(mad(outf[n - 2], B), 2)
        dec = decode(d / "transition.mp4")
        meas = measures(dec, states, D)
        codec = [mad(x, y) for x, y in zip(dec, outf)]
        exact = {"frame0_equals_source": bool(np.array_equal(outf[0], frames[0])),
                 "last_equals_source": bool(np.array_equal(outf[-1], frames[-1])),
                 "frame0_equals_A": bool(np.array_equal(outf[0], A)), "last_equals_B": bool(np.array_equal(outf[-1], B)),
                 "untouched_frames": [i for i in range(n) if w[:, i].sum() <= 0],
                 "untouched_equal_source": all(np.array_equal(outf[i], frames[i]) for i in range(n) if w[:, i].sum() <= 0)}
        mad_src = [round(mad(outf[i], frames[i]), 3) for i in range(n)]
        rep = {"tool_version": T.VERSION, "probe": "keyframe_layer", "class": "L+K", "method": f"layered-score + keyframe correction ({tag})",
               "score": score, "layers": None, "canvas": [W, H], "n_frames": n, "render_s": render_s,
               "formula": "frame(t) = C(t) + g * sum_k w_k(t) * carry_{t_k->t}( band_sigma( K'_k - C(t_k) ) ) on the listed Lab channels; "
                          "K'_k = K_k resized (INTER_CUBIC), registered on locally normalised L (ECC affine + capped smoothed DIS residual), Lab mean/std matched to C(t_k) per layer matte",
               "params": {"variant": tag, **v, "gain_clip": list(GAIN_CLIP), "reg_sigma_px": REG_SIGMA, "reg_cap_px": REG_CAP, "reg_affine_max_px": REG_AFFINE_MAX, "flow_sigma_px": FLOW_SIGMA,
                          "carry": "chained DIS (PRESET_MEDIUM) between consecutive composite frames, L channel, half resolution",
                          "weights": "raised-cosine partition of unity over knots [1] + key frames + [n-2]"},
               "probe_file": str(a.probe), "probe_md5": md5_file(a.probe), "source_md5": src_md5,
               "keyframes": kinfo, "weights": [[round(float(x), 4) for x in row] for row in w],
               "carry_ranges": lo_hi, "frames_md5": h.hexdigest(), "mp4_md5": mp4_md5, "exact": exact,
               "mad_to_source_per_frame": mad_src, "codec_loss_mad": {"mean": round(float(np.mean(codec)), 3), "max": round(float(np.max(codec)), 3)},
               "quality": q, "measures": meas, "source_measures": compact(src_meas), "total_s": round(time.time() - t_all, 1),
               "outputs": ["transition.mp4", "strip.jpg", "report.json", "frame_022.jpg", "frame_045.jpg", "frame_067.jpg"]}
        (d / "report.json").write_text(json.dumps(rep, indent=1))
        print(json.dumps({"tag": tag, "mp4_md5": mp4_md5, "frames_md5": h.hexdigest(), "render_s": render_s, **exact,
                          "mad_to_source_max": max(mad_src), **{k2: meas[k2] for k2 in ("meanL_range", "meanL_max_jump", "stalls", "lap_median", "fade_r2_mean")}}), flush=True)
    print(json.dumps({"carry_prep_s": carry_s, "total_s": round(time.time() - t_all, 1)}))


def cmd_table(a):
    out = Path(a.out)
    rows = []
    for sm in sorted(out.glob("*/source_measures.json")):
        pair = sm.parent.name
        s = json.loads(sm.read_text())
        rows.append((pair, "source", compact(s["measures"]), s["codec_loss_mad"], s["md5"]))
        for rp in sorted(sm.parent.glob("keylayer_*/report.json")):
            r = json.loads(rp.read_text())
            rows.append((pair, rp.parent.name, compact(r["measures"]), r["codec_loss_mad"], r["mp4_md5"]))
    print("| pair | clip | mean L range | largest mean-L jump (at) | step median | stalls (step < half its neighbours) | "
          "min step near each t_k / neighbours | Laplacian var median | largest rel. Laplacian jump (at) | fade R^2 mean | DIS px/step mean | codec loss mean/max | mp4 md5 |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for pair, tag, m, cl, md in rows:
        nk = "; ".join(f"{x['min_step']}/{x['nbr_mean']} ({x['at']})" for x in m["near_keys"])
        print(f"| {pair} | {tag} | {m['meanL_range'][0]}–{m['meanL_range'][1]} | {m['meanL_max_jump']} ({m['meanL_max_jump_at']}) | "
              f"{m['step_median']} | {m['stalls'] or 'none'} | {nk} | {m['lap_median']} | {m['lap_max_rel_jump']} ({m['lap_max_rel_jump_at']}) | "
              f"{m['fade_r2_mean']} | {m['disp_px_mean']} | {cl['mean']}/{cl['max']} | `{md[:8]}…` |")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("select")
    s.add_argument("--probe", required=True)
    s.add_argument("--score", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--expect-md5", default="")
    s.add_argument("--k", type=int, default=3)
    s.add_argument("--sep", type=int, default=15)
    s.add_argument("--seed", type=int, default=0)
    c = sub.add_parser("clip")
    c.add_argument("--probe", required=True)
    c.add_argument("--score", required=True)
    c.add_argument("--select", required=True)
    c.add_argument("--keys", required=True, help="f22=KF.png,f45=KF.png,... (frame index = the composite it was made from)")
    c.add_argument("--out", required=True)
    c.add_argument("--src-mp4", default="")
    c.add_argument("--tags", default="")
    c.add_argument("--seed", type=int, default=0)
    t = sub.add_parser("table")
    t.add_argument("--out", required=True)
    a = ap.parse_args()
    return {"select": cmd_select, "clip": cmd_clip, "table": cmd_table}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
