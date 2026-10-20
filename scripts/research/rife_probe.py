#!/usr/bin/env python3
"""Probe P5 (slice FL4): RIFE in-betweens between two generated stills of the café man, inside his matte.

Research script (2026-10-21). numpy, cv2, torch (CPU only). A probe, not a change to either tool: it writes
candidate keyframes for the renderer's keyframe chain (`params.keyframes`, frame "canvas") and measures them.
Everything it writes is generated content (RIFE v4.26 synthesises the in-betweens); the page says so.

Subcommands
  warmup   fetch ONCE (network): the author's own Hugging Face copy of Practical-RIFE v4.26
           (hzwer/RIFE, file RIFEv4.26_0921.zip, pinned revision) and, from GitHub at a pinned commit of
           hzwer/Practical-RIFE, model/warplayer.py and LICENSE. Extracts flownet.pkl and IFNet_HDv3.py into
           their own directory and writes RIFE_MANIFEST.json (sha256, bytes, source URL, revision, licence).
  matte    build the chain matte on the 602x800 canvas the way director_render.py builds it after a lead:
           A's man (el_3) moved by the face similarity A -> k1 (scale and translation, rotation dropped),
           joined with B's nearest man (el_10), dilated by 3 % of the width, feathered. Also writes moved_A.png
           (the moved man over A's canvas picture) and moved_A_matte.png.
  run      offline (HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1; refuses without the manifest or on a sha256
           mismatch). run --a A.png --b B.png --matte M.png --n 7 --out DIR writes, for k = 1..n at
           t = k/(n+1): DIR/full_<k>.png (the whole interpolated frame) and DIR/in_<k>.png (the interpolated
           frame inside the matte, A's pixels outside: out = m * interp + (1 - m) * A), and DIR/report.json.
           Inputs are resized to the matte's size with INTER_AREA first (the renderer's own resize of a
           canvas keyframe), so the outputs are already on the canvas.

Measures (report.json, per in-between; the endpoints of the segment are P = --a and Q = --b):
  faces       YuNet (the renderer's model and call: FaceDetectorYN.create(path, "", (320, 320), 0.6, 0.3,
              5000)) on the full frame: all faces, and faces whose box centre lies inside the matte (> 0.5).
              The same count on P and Q is the control.
  dexp        rule 7's double-exposure share inside the matte (m > 0.5): pixels whose per-channel max
              difference is <= 20 from (P + Q) / 2 and > 20 from both P and Q. The same share for the plain
              linear blend (1 - t) P + t Q at the same t is the positive control. dexp_t is the variant with
              (1 - t) P + t Q in place of the mean.
  flow        between consecutive frames of the strip [P, in_1 .. in_n, Q] and between P and Q directly:
              fb1 = share of matte pixels whose DIS forward-backward error is <= 1 px (transitions._dis, plain);
              cw = the renderer's consistency_mean (transitions.consistency_weight mean inside the matte, on
              the flow after the renderer's face-landmark similarity when YuNet finds both faces), the number
              round 11 measured at 0.10-0.29 (backlog T40).
  laplace     keyframe_screen.py's definition: variance of the Laplacian (ksize 1, CV_32F) of the uint8 Lab L
              channel on an INTER_AREA proxy with long side 480 px; whole frame, and inside the matte.
  seconds     wall seconds per in-between on the CPU (torch threads as set by torch).
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import math
import os
import shutil
import sys
import time
import types
import zipfile
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "benchmarks/runs/2026-10-21/rife"
MANIFEST = OUT / "RIFE_MANIFEST.json"
WEIGHTS_DIR = OUT / "weights_v4_26"            # flownet.pkl + IFNet_HDv3.py from the author's zip
CODE_DIR = OUT / "practical_rife_code"          # warplayer.py + LICENSE from GitHub
HF_REPO = "hzwer/RIFE"
HF_REV = "01fdc7e97404120c243c3ea7b427046e5dc7643e"
HF_FILE = "RIFEv4.26_0921.zip"
GH_REPO = "hzwer/Practical-RIFE"
GH_COMMIT = "bbfd2ea90910789a860ea3e2b32a240cd577b75e"
GH_FILES = {"warplayer.py": "model/warplayer.py", "LICENSE": "LICENSE"}
FACE_MODEL = ROOT / "benchmarks/runs/2026-10-18/face/face_detection_yunet_2023mar.onnx"
FACE_MANIFEST = FACE_MODEL.parent / "FACE_MANIFEST.json"
KF = ROOT / "benchmarks/runs/2026-10-17/keyframes_r10"
A_CANVAS = KF / "in/mismatch_2_S_canvas.png"
B_CANVAS = KF / "in/mismatch_2_F_canvas.png"
EL_A = ROOT / "benchmarks/runs/2026-10-17/mattes/mismatch_2_S/el_3.png"
EL_B = ROOT / "benchmarks/runs/2026-10-17/mattes/mismatch_2_F/el_10.png"
DEXP_LEVELS = 20.0
PROXY_LONG = 480


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------ warmup (the only network step)
def cmd_warmup(args):
    import urllib.request
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    from huggingface_hub import hf_hub_download
    OUT.mkdir(parents=True, exist_ok=True)
    dl = OUT / "download"
    dl.mkdir(exist_ok=True)
    zp = Path(hf_hub_download(HF_REPO, HF_FILE, revision=HF_REV, local_dir=str(dl)))
    WEIGHTS_DIR.mkdir(exist_ok=True)
    with zipfile.ZipFile(zp) as z:
        for name in ("flownet.pkl", "IFNet_HDv3.py", "RIFE_HDv3.py", "refine.py"):
            with z.open(f"RIFEv4.26_0921/{name}") as src, open(WEIGHTS_DIR / name, "wb") as dst:
                shutil.copyfileobj(src, dst)
    CODE_DIR.mkdir(exist_ok=True)
    gh = {}
    for name, rel in GH_FILES.items():
        url = f"https://raw.githubusercontent.com/{GH_REPO}/{GH_COMMIT}/{rel}"
        with urllib.request.urlopen(url, timeout=60) as r:
            (CODE_DIR / name).write_bytes(r.read())
        gh[name] = url
    hf_url = f"https://huggingface.co/{HF_REPO}/resolve/{HF_REV}/{HF_FILE}"
    files = {}
    for p in [zp] + sorted(WEIGHTS_DIR.iterdir()) + sorted(CODE_DIR.iterdir()):
        if p.is_file():
            src = gh.get(p.name) if p.parent == CODE_DIR else (hf_url + ("" if p == zp else f" -> RIFEv4.26_0921/{p.name}"))
            files[str(p.relative_to(ROOT))] = {"sha256": sha256(p), "bytes": p.stat().st_size, "source": src}
    man = {"date": datetime.date.today().isoformat(), "model": "Practical-RIFE v4.26 (zip RIFEv4.26_0921; RIFE_HDv3.py inside says version 4.25)",
           "weights": {"repo": HF_REPO, "revision": HF_REV, "file": HF_FILE, "url": hf_url,
                       "licence": "MIT (Practical-RIFE LICENSE at the pinned commit; the HF repo has no licence tag)"},
           "code": {"repo": f"https://github.com/{GH_REPO}", "commit": GH_COMMIT, "licence": "MIT"},
           "used_at_run": ["weights_v4_26/flownet.pkl", "weights_v4_26/IFNet_HDv3.py", "practical_rife_code/warplayer.py"],
           "files": files}
    MANIFEST.write_text(json.dumps(man, indent=1))
    print(f"warmup: {HF_REPO}@{HF_REV[:10]} {HF_FILE}; {GH_REPO}@{GH_COMMIT[:10]}; manifest {MANIFEST}")


# ------------------------------------------------------------------ model (offline)
def load_rife():
    if not MANIFEST.exists():
        sys.exit(f"refuse: no {MANIFEST}; run `rife_probe.py warmup` once (the only step that downloads)")
    man = json.loads(MANIFEST.read_text())
    for rel in ["benchmarks/runs/2026-10-21/rife/" + u for u in man["used_at_run"]]:
        p = ROOT / rel
        if not p.exists() or sha256(p) != man["files"][rel]["sha256"]:
            sys.exit(f"refuse: {rel} is missing or its sha256 differs from the manifest")
    import torch
    torch.set_grad_enabled(False)
    # the downloaded code is imported by path, never run from its directory: warplayer as the module
    # `model.warplayer` that IFNet_HDv3.py imports, then IFNet_HDv3.py itself under a private name
    pkg = types.ModuleType("model"); pkg.__path__ = []
    sys.modules["model"] = pkg
    for modname, path in (("model.warplayer", CODE_DIR / "warplayer.py"), ("rife_ifnet_v4_26", WEIGHTS_DIR / "IFNet_HDv3.py")):
        spec = importlib.util.spec_from_file_location(modname, str(path))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[modname] = mod
        spec.loader.exec_module(mod)
    net = sys.modules["rife_ifnet_v4_26"].IFNet()
    sd = torch.load(str(WEIGHTS_DIR / "flownet.pkl"), map_location="cpu", weights_only=True)
    sd = {k.replace("module.", ""): v for k, v in sd.items()}
    res = net.load_state_dict(sd, strict=False)
    net.eval().to("cpu")
    info = {"missing_keys": list(res.missing_keys), "unexpected_keys": list(res.unexpected_keys),
            "params": int(sum(p.numel() for p in net.parameters())), "torch": torch.__version__,
            "threads": torch.get_num_threads(),
            "manifest_sha256": {u: man["files"]["benchmarks/runs/2026-10-21/rife/" + u]["sha256"] for u in man["used_at_run"]},
            "manifest_file_sha256": sha256(MANIFEST)}
    if res.missing_keys:
        sys.exit(f"refuse: the weights miss {len(res.missing_keys)} keys of IFNet: {res.missing_keys[:5]}")
    return net, info


def rife_at(net, bgr0, bgr1, t):
    """Practical-RIFE's inference_img.py path at scale 1: BGR / 255, padded to a multiple of 64, IFNet with
    scale_list [16, 8, 4, 2, 1], merged[-1], cropped back. Returns uint8 BGR."""
    import torch
    import torch.nn.functional as F
    h, w = bgr0.shape[:2]
    x0 = torch.from_numpy(bgr0.transpose(2, 0, 1).copy()).float()[None] / 255.0
    x1 = torch.from_numpy(bgr1.transpose(2, 0, 1).copy()).float()[None] / 255.0
    ph, pw = ((h - 1) // 64 + 1) * 64, ((w - 1) // 64 + 1) * 64
    pad = (0, pw - w, 0, ph - h)
    x0, x1 = F.pad(x0, pad), F.pad(x1, pad)
    _, _, merged = net(torch.cat((x0, x1), 1), float(t), [16, 8, 4, 2, 1])
    y = merged[-1][0, :, :h, :w].clamp(0, 1).numpy().transpose(1, 2, 0)
    return np.round(y * 255.0).astype(np.uint8)


# ------------------------------------------------------------------ measures
_DET = {}


def faces_of(bgr):
    if "d" not in _DET:
        _DET["d"] = cv2.FaceDetectorYN.create(str(FACE_MODEL), "", (320, 320), 0.6, 0.3, 5000)
    d = _DET["d"]
    d.setInputSize((bgr.shape[1], bgr.shape[0]))
    _, f = d.detect(np.ascontiguousarray(bgr))
    return [] if f is None else [x for x in f]


def face_count(bgr, m):
    fs = faces_of(bgr)
    inside = []
    for f in fs:
        x, y, w, h = [int(v) for v in f[:4]]
        cx = min(m.shape[1] - 1, max(0, x + w // 2)); cy = min(m.shape[0] - 1, max(0, y + h // 2))
        if m[cy, cx] > 0.5:
            inside.append([x, y, w, h, round(float(f[14]), 3)])
    return {"all": len(fs), "in_matte": len(inside), "boxes_in_matte": inside}


def largest_face(bgr, region):
    best = None
    for f in faces_of(bgr):
        x, y, w, h = [int(v) for v in f[:4]]
        cx = min(region.shape[1] - 1, max(0, x + w // 2)); cy = min(region.shape[0] - 1, max(0, y + h // 2))
        if region is not None and not region[cy, cx]:
            continue
        if best is None or w * h > best[2] * best[3]:
            best = (x, y, w, h, np.array(f[4:14], np.float32).reshape(5, 2))
    return best


def dexp_share(X, P, Q, m, ref=None):
    """Share of m > 0.5 pixels within 20 levels (per-channel max) of ref (default the mean of P and Q) and
    farther than 20 from both P and Q."""
    X = X.astype(np.float32); P = P.astype(np.float32); Q = Q.astype(np.float32)
    ref = (P + Q) / 2.0 if ref is None else ref.astype(np.float32)
    dm = np.abs(X - ref).max(2); dp = np.abs(X - P).max(2); dq = np.abs(X - Q).max(2)
    hit = (dm <= DEXP_LEVELS) & (dp > DEXP_LEVELS) & (dq > DEXP_LEVELS)
    sel = m > 0.5
    return round(float(hit[sel].mean()), 4)


def laplace(bgr, m=None):
    h, w = bgr.shape[:2]
    s = PROXY_LONG / max(h, w)
    sz = (max(1, int(round(w * s))), max(1, int(round(h * s))))
    p = cv2.resize(bgr, sz, interpolation=cv2.INTER_AREA)
    L = cv2.cvtColor(p, cv2.COLOR_BGR2LAB)[..., 0]
    lap = cv2.Laplacian(L, cv2.CV_32F, ksize=1)
    if m is None:
        return round(float(lap.var()), 1)
    mm = cv2.resize(m, sz, interpolation=cv2.INTER_AREA) > 0.5
    return round(float(lap[mm].var()), 1)


def flow_pair(T, P, Q, m):
    """fb1 on plain DIS; cw = the renderer's consistency_mean on the face-guided flow (identity guide when a
    face is missing)."""
    gP = T.gray_of(cv2.cvtColor(P, cv2.COLOR_BGR2RGB)); gQ = T.gray_of(cv2.cvtColor(Q, cv2.COLOR_BGR2RGB))
    d1 = T._dis(gP, gQ); d2 = T._dis(gQ, gP)
    h, w = gP.shape
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    back = cv2.remap(d2, gx + d1[..., 0], gy + d1[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    err = np.linalg.norm(d1 + back, axis=2)
    sel = m > 0.5
    fb1 = float((err[sel] <= 1.0).mean())
    Hg = np.eye(3); guide = "identity"
    fP = largest_face(P, sel); fQ = largest_face(Q, sel)
    if fP is not None and fQ is not None:
        M2, _ = cv2.estimateAffinePartial2D(fP[4], fQ[4], method=cv2.LMEDS)
        if M2 is not None and np.isfinite(M2).all() and 0.5 < math.hypot(M2[0, 0], M2[1, 0]) < 2.0:
            Hg = np.vstack([M2, [0, 0, 1]]).astype(np.float64); guide = "faces"
    dPQ = T._homography_guided(gP, gQ, np.linalg.inv(Hg)); dQP = T._homography_guided(gQ, gP, Hg)
    cw = float(T.consistency_weight(dPQ, dQP)[sel].mean())
    return {"fb1": round(fb1, 3), "cw": round(cw, 3), "guide": guide,
            "disp_median_px": round(float(np.median(np.linalg.norm(dPQ, axis=2)[sel])), 1)}


# ------------------------------------------------------------------ io
def read_to(path, size):
    im = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if im is None:
        sys.exit(f"cannot read {path}")
    if (im.shape[1], im.shape[0]) != size:
        im = cv2.resize(im, size, interpolation=cv2.INTER_AREA if im.shape[1] > size[0] else cv2.INTER_LINEAR)
    return im


def read_matte(path):
    m = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if m is None:
        sys.exit(f"cannot read {path}")
    if m.ndim == 3:
        m = m[..., 0]
    return (m.astype(np.float32) / 255.0) if m.dtype == np.uint8 else m.astype(np.float32)


def cmd_matte(args):
    """Chain matte and the moved A man, on the canvas (602x800)."""
    mA = read_matte(EL_A); mB = read_matte(EL_B)
    H, W = mA.shape
    A = read_to(A_CANVAS, (W, H)); k1 = read_to(args.k1, (W, H))
    fA = largest_face(A, mA > 0.5)
    regB = cv2.dilate((mB > 0.3).astype(np.uint8), np.ones((int(0.1 * W) | 1,) * 2, np.uint8)).astype(bool)
    fK = largest_face(k1, regB)
    if fA is None or fK is None:
        sys.exit(f"no face: A {fA is not None}, k1 {fK is not None}")
    M2, _ = cv2.estimateAffinePartial2D(fA[4], fK[4], method=cv2.LMEDS)
    sc = math.hypot(M2[0, 0], M2[1, 0]); cA = fA[4].mean(0); cK = fK[4].mean(0)
    Mg = np.array([[sc, 0, cK[0] - sc * cA[0]], [0, sc, cK[1] - sc * cA[1]]], np.float32)   # rotation dropped, as the renderer does
    moved = cv2.warpAffine(A, Mg, (W, H), flags=cv2.INTER_AREA if sc < 1 else cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    moved_m = np.clip(cv2.warpAffine(mA, Mg, (W, H), flags=cv2.INTER_LINEAR), 0, 1)
    movedA = (moved_m[..., None] * moved + (1 - moved_m[..., None]) * A).round().astype(np.uint8)
    g = int(round(0.03 * W)) | 1
    union = cv2.dilate((np.maximum(moved_m, mB) > 0.3).astype(np.uint8), np.ones((g, g), np.uint8)).astype(np.float32)
    k = max(1.0, 0.3 * g)
    chain = np.clip(cv2.GaussianBlur(union, (0, 0), k), 0, 1)
    chain = np.maximum(chain, union * (chain > 0.5))    # keep the dilated core at 1, feather outward
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out / "moved_A.png"), movedA)
    cv2.imwrite(str(out / "moved_A_matte.png"), (moved_m * 255).round().astype(np.uint8))
    cv2.imwrite(str(out / "chain_matte.png"), (chain * 255).round().astype(np.uint8))
    info = {"face_A": [int(v) for v in fA[:4]], "face_k1": [int(v) for v in fK[:4]], "similarity": Mg.round(4).tolist(),
            "scale": round(sc, 4), "grow_px": g, "chain_matte_share": round(float((chain > 0.5).mean()), 4)}
    (out / "matte.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info))


def cmd_run(args):
    os.environ["HF_HUB_OFFLINE"] = "1"; os.environ["TRANSFORMERS_OFFLINE"] = "1"
    sys.path.insert(0, str(ROOT))
    import transitions as T
    m = read_matte(args.matte)
    H, W = m.shape
    P = read_to(args.a, (W, H)); Q = read_to(args.b, (W, H))
    net, minfo = load_rife()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    m3 = m[..., None]
    # the man's face region: the union of the largest face inside the matte in P and in Q, grown by 25 % of its
    # size; a face whose centre lies there is the man's (the woman in green sits inside the matte in k1)
    fb = [largest_face(I, m > 0.5) for I in (P, Q)]
    fb = [f for f in fb if f is not None]
    face_reg = np.zeros((H, W), bool)
    if fb:
        x0 = min(f[0] for f in fb); y0 = min(f[1] for f in fb); x1 = max(f[0] + f[2] for f in fb); y1 = max(f[1] + f[3] for f in fb)
        gx_, gy_ = int(0.25 * (x1 - x0)), int(0.25 * (y1 - y0))
        face_reg[max(0, y0 - gy_):y1 + gy_, max(0, x0 - gx_):x1 + gx_] = True
    m_face = m * face_reg; m_rest = m * ~face_reg
    def man_faces(I):
        n = 0
        for b in face_count(I, m)["boxes_in_matte"]:
            n += int(face_reg[min(H - 1, b[1] + b[3] // 2), min(W - 1, b[0] + b[2] // 2)])
        return n
    frames, rows = [], []
    for k in range(1, args.n + 1):
        t = k / (args.n + 1)
        t0 = time.perf_counter()
        X = rife_at(net, P, Q, t)
        sec = time.perf_counter() - t0
        blend = ((1 - t) * P.astype(np.float32) + t * Q.astype(np.float32))
        comp = (m3 * X + (1 - m3) * P).round().astype(np.uint8)
        cv2.imwrite(str(out / f"full_{k}.png"), X)
        cv2.imwrite(str(out / f"in_{k}.png"), comp)
        rows.append({"k": k, "t": round(t, 4), "seconds": round(sec, 2), "faces": face_count(X, m), "man_faces": man_faces(X),
                     "dexp_face": dexp_share(X, P, Q, m_face), "dexp_rest": dexp_share(X, P, Q, m_rest),
                     "dexp_blend_face": dexp_share(blend, P, Q, m_face),
                     "dexp": dexp_share(X, P, Q, m), "dexp_blend": dexp_share(blend, P, Q, m),
                     "dexp_t": dexp_share(X, P, Q, m, blend), "dexp_t_blend": dexp_share(blend, P, Q, m, blend),
                     "laplace": laplace(X), "laplace_matte": laplace(X, m),
                     "laplace_blend_matte": laplace(blend.round().astype(np.uint8), m)})
        frames.append(X)
        print(f"k {k} t {t:.3f} {sec:.1f} s faces {rows[-1]['faces']['in_matte']}/{rows[-1]['faces']['all']} "
              f"man {rows[-1]['man_faces']} dexp {rows[-1]['dexp']} face {rows[-1]['dexp_face']} rest {rows[-1]['dexp_rest']} (blend {rows[-1]['dexp_blend']})", flush=True)
    strip = [P] + frames + [Q]
    flows = []
    for j in range(len(strip) - 1):
        flows.append(dict(seg=j, **flow_pair(T, strip[j], strip[j + 1], m)))
    direct = flow_pair(T, P, Q, m)
    ctrl = {"face_region_box": [int(v) for v in np.argwhere(face_reg).min(0)[::-1].tolist() + np.argwhere(face_reg).max(0)[::-1].tolist()] if face_reg.any() else None,
            "P": {"man_faces": man_faces(P), "faces": face_count(P, m), "laplace": laplace(P), "laplace_matte": laplace(P, m)},
            "Q": {"man_faces": man_faces(Q), "faces": face_count(Q, m), "laplace": laplace(Q), "laplace_matte": laplace(Q, m)}}
    secs = [r["seconds"] for r in rows]
    rep = {"date": datetime.datetime.now().isoformat(timespec="seconds"), "generated": True,
           "model": "Practical-RIFE v4.26 (hzwer/RIFE RIFEv4.26_0921.zip), CPU", "model_info": minfo,
           "face_model": {"path": str(FACE_MODEL.relative_to(ROOT)), "sha256": sha256(FACE_MODEL)},
           "a": str(args.a), "b": str(args.b), "matte": str(args.matte), "canvas": [W, H], "n": args.n,
           "matte_share": round(float((m > 0.5).mean()), 4),
           "seconds_per_frame": {"mean": round(float(np.mean(secs)), 2), "min": min(secs), "max": max(secs)},
           "frames": rows, "control": ctrl, "flow_consecutive": flows, "flow_direct_PQ": direct,
           "bars": {"one_man_face_each": all(r["man_faces"] == 1 for r in rows),
                    "one_face_in_matte_each": all(r["faces"]["in_matte"] == 1 for r in rows),
                    "dexp_face_max": max(r["dexp_face"] for r in rows), "dexp_rest_max": max(r["dexp_rest"] for r in rows),
                    "dexp_max": max(r["dexp"] for r in rows), "dexp_le_1pct": all(r["dexp"] <= 0.01 for r in rows),
                    "positive_control_min": min(r["dexp_blend"] for r in rows),
                    "cw_min_consecutive": min(f["cw"] for f in flows), "cw_direct": direct["cw"],
                    "fb1_min_consecutive": min(f["fb1"] for f in flows), "fb1_direct": direct["fb1"],
                    "consistency_above_direct": min(f["cw"] for f in flows) > direct["cw"]}}
    (out / "report.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep["bars"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("warmup")
    mp = sp.add_parser("matte"); mp.add_argument("--k1", required=True); mp.add_argument("--out", required=True)
    rp = sp.add_parser("run")
    for a in ("--a", "--b", "--matte", "--out"):
        rp.add_argument(a, required=True)
    rp.add_argument("--n", type=int, default=7)
    args = ap.parse_args()
    {"warmup": cmd_warmup, "matte": cmd_matte, "run": cmd_run}[args.cmd](args)


if __name__ == "__main__":
    main()
