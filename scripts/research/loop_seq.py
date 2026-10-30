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
      inliers are >= 40 and the map is sane (scale 0.85–1.15, corner moves < 15 % of the size); otherwise an
      ECC affine on blurred 600 px proxies (the motion-blurred frames); otherwise identity, said on the log.
      Frame 0 is never warped. All frames are cropped to the common valid rectangle (even sides). Writes
      OUT/k<i>.png and OUT/prep.json (the method, inliers, residual, the map and the crop per frame).
  render PLAN.json --out OUT [--fps 25] [--draft 0]
      Renders the loop the plan describes (see plans/loops/SCHEMA.md): keyframes by index into the prep
      folder, holds per visit, segments between keyframes rendered by `morph` (transitions.py, the DIS flow
      and optional anchors), `rife` (in-betweens inside the change matte; generated content, labelled),
      `dissolve` (a plain blend inside the change matte; for content that exists in one frame only),
      `teleport` (a region's content squeezed out and another region's squeezed in; `mode: fade` fades the
      region's content in place instead, for a ghost that materializes while the rest moves by RIFE), or `rewind` (the
      frames of an earlier segment played backward, every k-th). Post effects: `breath` (a push-in about a
      point, sin² over the loop, the endpoints untouched). Writes OUT/loop.mp4, OUT/loop.gif (two-pass
      palette, 40 ms per frame at 25 fps), OUT/sheet.jpg, OUT/frames.json (what each frame is) and
      OUT/measure.json (the step series, the seam step, faces per frame, the double-exposure share per
      generated frame, seconds).
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


def register_sift(ref_bgr, bgr):
    """Homography bgr -> ref on the proxies, returned at full scale, with its diagnostics."""
    g0, s = _proxy_gray(ref_bgr, PROXY_LONG)
    g1, s1 = _proxy_gray(bgr, PROXY_LONG)
    sift = cv2.SIFT_create(6000)
    k0, d0 = sift.detectAndCompute(g0, None)
    k1, d1 = sift.detectAndCompute(g1, None)
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
    info = {"method": "sift+magsac", "inliers": inl, "matches": len(good), "sane": ok, "why": why,
            "residual_px": None if res is None else round(res, 2)}
    if inl < MIN_INLIERS or not ok:
        return None, info
    return Hf, info


def register_ecc(ref_bgr, bgr, seed=None):
    """ECC affine on blurred proxies, seeded by a map bgr -> ref at full scale (the previous frame's):
    the path for a motion-blurred frame."""
    g0, s = _proxy_gray(ref_bgr, ECC_LONG)
    g1, s1 = _proxy_gray(bgr, ECC_LONG)
    g0 = cv2.GaussianBlur(g0, (0, 0), 3).astype(np.float32) / 255
    g1 = cv2.GaussianBlur(g1, (0, 0), 3).astype(np.float32) / 255
    S0 = np.diag([1 / s, 1 / s, 1.0]); S1 = np.diag([1 / s1, 1 / s1, 1.0])
    Hs = np.eye(3) if seed is None else np.linalg.inv(S0) @ seed @ S1     # bgr -> ref on the proxies
    # findTransformECC maps the TEMPLATE (ref) to the INPUT (bgr): seed it with the inverse and invert back
    M = np.linalg.inv(Hs)[:2].astype(np.float32)
    try:
        cc, M = cv2.findTransformECC(g0, g1, M, cv2.MOTION_AFFINE,
                                     (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-6), None, 5)
    except cv2.error as e:
        return None, {"method": "ecc-affine", "cc": None, "why": str(e).splitlines()[-1][:80]}
    H = np.linalg.inv(np.vstack([M, [0, 0, 1]]).astype(np.float64))
    ok, why = _sane_h(H, g0.shape[1], g0.shape[0])
    info = {"method": "ecc-affine", "cc": round(float(cc), 4), "sane": ok, "why": why, "seeded": seed is not None}
    if cc < ECC_MIN_CC or not ok:
        return None, info
    return S0 @ H @ np.linalg.inv(S1), info


def register_all(frames, cuts=()):
    """Maps frame i -> frame 0 for every frame: direct SIFT, else SIFT to the previous frame composed with
    its map, else ECC seeded by the previous frame's map, else identity (said on the log). A frame listed
    in cuts is not registered at all (identity, untrusted): the plan joins it by a cut."""
    ref = frames[0]
    maps = [np.eye(3)]; regs = [{"method": "reference", "trusted": True}]
    for i, f in enumerate(frames[1:], 1):
        if i in cuts:
            maps.append(np.eye(3)); regs.append({"method": "cut (identity, excluded from the crop)", "trusted": False})
            log(f"prep: frame {i} is a cut: identity, excluded from the crop")
            continue
        H, info = register_sift(ref, f)
        if H is None:
            log(f"prep: frame {i} direct sift rejected ({info.get('inliers')} inliers, {info.get('why')}); chaining")
            Hc, infoc = register_sift(frames[i - 1], f)
            if Hc is not None and regs[i - 1]["trusted"]:
                H = maps[i - 1] @ Hc
                info = {"method": "sift+magsac via frame %d" % (i - 1), "direct": info, **{k: v for k, v in infoc.items() if k != "method"}}
            else:
                log(f"prep: frame {i} chained sift rejected ({infoc.get('inliers')} inliers, {infoc.get('why')}); trying ECC")
                seed = maps[i - 1] if regs[i - 1]["trusted"] else None
                He, infoe = register_ecc(ref, f, seed=seed)
                info = {"direct": info, "chain": infoc, **infoe}
                H = He
        if H is None:
            log(f"prep: frame {i} ECC rejected ({info.get('why')}, cc {info.get('cc')}); IDENTITY used")
            H = np.eye(3); info["method"] = "identity"; info["trusted"] = False
        else:
            info["trusted"] = True
        maps.append(H); regs.append(info)
        log(f"prep: frame {i} {info['method']} inliers {info.get('inliers', '-')} {info.get('why', '')}")
    return maps, regs


def cmd_prep(args):
    import transitions as T
    src = Path(args.seq_dir)
    files = sorted(p for p in src.iterdir() if p.suffix.lower() in (".jpg", ".jpeg"))
    if len(files) < 2:
        sys.exit(f"{src}: {len(files)} developed JPGs, need 2 or more")
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
    maps, regs = register_all(frames, cuts)
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
    for i, wf in enumerate(warped):
        cv2.imwrite(str(out / f"k{i}.png"), wf[y0:y1, x0:x1])
    rep = {"date": datetime.datetime.now().isoformat(timespec="seconds"), "seq": src.parent.name if src.name == "raw" else src.name,
           "sources": meta, "long": args.long, "cuts": list(cuts), "reference": ref_i, "reference_size": [W0, H0], "crop": crop,
           "canvas": [x1 - x0, y1 - y0], "frames": regs}
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
    "decel": lambda t: 1 - (1 - t) ** 2,
}


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


def frames_rife(A, B, n, ease, matte_cfg, out_rows):
    """n in-betweens: RIFE inside the change matte, the plain blend outside. Generated content inside."""
    m = change_matte(A, B, **matte_cfg); m3 = m[..., None]
    import rife_probe as R
    out = []
    for i in range(n):
        t = EASES[ease]((i + 1) / (n + 1))
        t0 = time.perf_counter()
        X = _RIFE.at(A, B, t)
        sec = time.perf_counter() - t0
        bl = blend(A, B, t)
        f = (m3 * X + (1 - m3) * bl).round().astype(np.uint8)
        out.append(f)
        out_rows.append({"t": round(t, 4), "generated": "rife", "matte_share": round(float((m > 0.5).mean()), 4),
                         "dexp": R.dexp_share(X, A, B, m), "seconds": round(sec, 2)})
    return out, m


def frames_dissolve(A, B, n, ease, out_rows):
    out = []
    for i in range(n):
        t = EASES[ease]((i + 1) / (n + 1))
        out.append(blend(A, B, t).round().astype(np.uint8))
        out_rows.append({"t": round(t, 4), "generated": "none (blend)"})
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
    fr = [cv2.cvtColor(f, cv2.COLOR_RGB2BGR) for f in T.iter_frames(A2, B2, spec, corr)]
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
    return out


def render_plan(plan, out, fps, draft=0):
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
    frames, rows = [], []
    cur = None
    t_render = time.time()
    for si, step in enumerate(plan["timeline"]):
        if "key" in step:
            k = int(step["key"])
            for _ in range(int(step.get("hold", 1))):
                frames.append(keys[k]); rows.append({"step": si, "key": k, "generated": "none (photo)"})
            cur = k
            continue
        j = int(step["to"]); n = int(step.get("n", 0)); method = step.get("method", "rife"); ease = step.get("ease", "smooth")
        A, B = keys[cur], keys[j]
        seg_rows = []
        if method == "rife":
            fr, _ = frames_rife(A, B, n, ease, matte_cfg, seg_rows)
        elif method == "dissolve":
            fr = frames_dissolve(A, B, n, ease, seg_rows)
        elif method == "morph":
            fr = frames_morph(A, B, n, ease, fps, step, seg_rows)
        elif method == "teleport":
            fr, _ = frames_teleport(A, B, n, ease, step, matte_cfg, seg_rows)
        elif method == "cut":
            fr = []
        elif method == "rewind":
            stride = int(step.get("stride", 3))
            back = frames[int(step.get("from", 0)):][::-1][stride::stride]
            fr = [f for f in back]
            seg_rows = [{"generated": "none (rewind)"} for _ in fr]
        else:
            sys.exit(f"unknown method {method}")
        for r in seg_rows:
            r.update({"step": si, "from": cur, "to": j, "method": method})
        frames.extend(fr); rows.extend(seg_rows)
        log(f"render: step {si} {cur}->{j} {method} n {len(fr)} ({time.time() - t_render:.0f} s so far)")
        cur = j
    for eff in plan.get("effects", []):
        if eff["kind"] == "breath":
            frames = apply_breath(frames, eff)
        else:
            sys.exit(f"unknown effect {eff['kind']}")
    render_s = round(time.time() - t_render, 1)
    N = len(frames)
    # the mp4 and the gif
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    mp4 = out / "loop.mp4"
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
    # measures on the decoded mp4
    cap = cv2.VideoCapture(str(mp4)); dec = []
    while True:
        ok, f = cap.read()
        if not ok: break
        dec.append(f)
    steps = [float(np.mean(cv2.absdiff(dec[i + 1], dec[i]))) for i in range(len(dec) - 1)]
    seam = float(np.mean(cv2.absdiff(dec[-1], dec[0])))
    faces = []
    try:
        import rife_probe as R
        faces = [len(R.faces_of(f)) for f in dec]
    except SystemExit:
        pass
    gen = [r for r in rows if not r["generated"].startswith("none")]
    meas = {"frames": N, "fps": fps, "canvas": [W, H], "seconds": round(N / fps, 3), "render_s": render_s,
            "step_mean": round(float(np.mean(steps)), 3), "step_max": round(max(steps), 3), "step_max_at": int(np.argmax(steps)),
            "seam_step": round(seam, 3), "steps": [round(x, 2) for x in steps],
            "faces_per_frame": faces, "faces_keyframes": sorted(set(faces[i] for i, r in enumerate(rows) if "key" in r)) if faces else None,
            "generated_frames": len(gen), "generated_share": round(len(gen) / N, 3),
            "dexp_max": max([r.get("dexp", r.get("dexp_rest", 0.0)) for r in gen], default=0.0),
            "rife_seconds_per_frame": round(float(np.mean([r["seconds"] for r in gen if "seconds" in r])), 2) if any("seconds" in r for r in gen) else None,
            "md5_mp4": md5(mp4), "md5_gif": md5(gif), "gif_bytes": gif.stat().st_size, "mp4_bytes": mp4.stat().st_size,
            "draft": draft, "plan_sha256": hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()[:16]}
    (out / "frames.json").write_text(json.dumps(rows, indent=0))
    (out / "measure.json").write_text(json.dumps(meas, indent=1))
    (out / "plan.json").write_text(json.dumps(plan, indent=1))
    print(json.dumps({k: meas[k] for k in ("frames", "seconds", "canvas", "render_s", "step_mean", "step_max", "step_max_at", "seam_step",
                                            "faces_keyframes", "generated_share", "dexp_max", "md5_mp4", "gif_bytes")}))
    return meas


def cmd_render(args):
    plan = json.loads(Path(args.plan).read_text())
    for kv in args.set or []:
        k, v = kv.split("=", 1); plan[k] = json.loads(v)
    render_plan(plan, args.out, args.fps, args.draft)


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
    eff = ", ".join(f"{e['kind']} {e.get('z', '')}" for e in plan.get("effects", []))
    return " · ".join(parts) + (f" · effects: {eff}" if eff else " · no effects")


def cmd_page(args):
    root = Path(args.root)
    notes = json.loads(Path(args.notes).read_text()) if args.notes and Path(args.notes).exists() else {}
    order = args.order.split(",") if args.order else sorted(p.name for p in root.iterdir() if p.is_dir() and p.name not in ("in", "probe_morph", "probe_rife", "agents"))
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
        variants = sorted(v for v in d.iterdir() if v.is_dir() and (v / "measure.json").exists())
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
    p.add_argument("--cut", default="", help="frame indices joined by a cut, not registered (e.g. 4,5)"); p.set_defaults(fn=cmd_prep)
    p = sp.add_parser("render"); p.add_argument("plan"); p.add_argument("--out", required=True)
    p.add_argument("--fps", type=int, default=25); p.add_argument("--draft", type=int, default=0, help="render at this long edge (0 = the prep canvas)")
    p.add_argument("--set", action="append", help="override a top-level plan key: key=<json>"); p.set_defaults(fn=cmd_render)
    p = sp.add_parser("page"); p.add_argument("--root", required=True); p.add_argument("--out", required=True)
    p.add_argument("--notes", default=""); p.add_argument("--order", default=""); p.add_argument("--title", default="Halloween loops")
    p.add_argument("--intro", default=""); p.add_argument("--footer", default=""); p.set_defaults(fn=cmd_page)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
