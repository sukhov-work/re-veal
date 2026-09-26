#!/usr/bin/env python3
"""
Harness for transitions.py. Same working method as harness.py: numbered
assertions, synthetic inputs with known ground truth, a real mp4 decoded
back with cv2.VideoCapture. Run: .venv/bin/python transitions_harness.py

Numbering: this file has its OWN check space (1..N), independent of
harness.py's 1-82. Numbers here are never reused either; a new check takes
the next number in the lettered section it belongs to.

Independent of harness.py by contract: transitions.py never imports
reveal, reveal.py never imports transitions (checks 1-2), and nothing in
transitions.py can reach the network at module level; torch and
transformers are imported lazily inside the depth functions only, behind
`transitions.py warmup` + models/DEPTH_MANIFEST.json (checks 3, 48-51).
"""

import ast
import contextlib
import hashlib
import io
import json
import logging
import shutil
import socket
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import cv2

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import transitions as T  # noqa: E402

PASS = 0
FAIL = 0


def check(n, desc, cond):
    global PASS, FAIL
    ok = bool(cond)
    PASS += ok
    FAIL += (not ok)
    print(f"  [{'ok' if ok else 'XX'}] {n:>3} {desc}")
    return ok


def textured(seed, w=640, h=400):
    """Blurred noise + discs + a grid: SIFT-friendly, DIS-friendly."""
    r = np.random.default_rng(seed)
    img = cv2.GaussianBlur((r.random((h, w, 3)) * 255).astype(np.uint8),
                           (0, 0), 5)
    for _ in range(120):
        cv2.circle(img, (int(r.integers(0, w)), int(r.integers(0, h))),
                   int(r.integers(5, 30)),
                   tuple(int(v) for v in r.integers(0, 255, 3)), -1)
    for x in range(0, w, 80):
        cv2.line(img, (x, 0), (x, h), (240, 240, 240), 1)
    return img


def mad(x, y):
    return float(np.abs(x.astype(np.float32) - y.astype(np.float32)).mean())


def affine_pair(seed=1, w=640, h=400, expose=True, patch=True):
    """(A, B, M): B = A under the 2x3 affine M (A pixel a lands at M a),
    plus an exposure change and a changed-content patch like reveal's
    harness pair, so the color path and the morph both have work to do."""
    A = textured(seed, w, h)
    M = cv2.getRotationMatrix2D((w / 2, h / 2), 3.0, 1.06)
    M[0, 2] += 12
    B = cv2.warpAffine(A, M, (w, h), borderMode=cv2.BORDER_REFLECT)
    if expose:
        B = np.clip(B.astype(np.float32) * 1.25 + 12, 0, 255).astype(np.uint8)
    if patch:
        cv2.rectangle(B, (int(w * .35), int(h * .30)), (int(w * .65), int(h * .70)),
                      (200, 40, 160), -1)
    return A, B, M


def frames_hash(frames):
    hsh = hashlib.sha256()
    for f in frames:
        hsh.update(np.ascontiguousarray(f).tobytes())
    return hsh.hexdigest()


def decode_all(path):
    cap = cv2.VideoCapture(str(path))
    meta = {"fps": cap.get(cv2.CAP_PROP_FPS),
            "n": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "w": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "h": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
    cap.release()
    return meta, frames


def _imports(path):
    tree = ast.parse(Path(path).read_text())
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def _imports_by_scope(path):
    """(module-level import names incl. the optional-layer try blocks,
    {function name: import names inside it})."""
    tree = ast.parse(Path(path).read_text())

    def names(node):
        out = []
        for n in ast.walk(node):
            if isinstance(n, ast.Import):
                out += [a.name for a in n.names]
            elif isinstance(n, ast.ImportFrom) and n.module:
                out.append(n.module)
        return out
    top = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Try, ast.If)):
            top += names(node)
    funcs = {n.name: names(n) for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    return top, funcs


def _refused_policy():
    try:
        T.spec_from("morph", canvas="nope")
        return False
    except T.TransitionError:
        return True


def profile_step(frame, ref, win=12):
    """Largest jump of the mean |frame - ref| between the `win` columns (or
    rows) on either side of any position. A frame edge inside the canvas
    reads as a step of about half the A-B gap; scene content moves it by a
    few levels."""
    d = np.abs(frame.astype(np.float32) - ref.astype(np.float32))
    best = 0.0
    for prof in (d.mean(axis=(0, 2)), d.mean(axis=(1, 2))):
        c = np.cumsum(np.insert(prof, 0, 0.0))
        n = len(prof)
        left = (c[win:n - win + 1] - c[:n - 2 * win + 1]) / win
        right = (c[2 * win:] - c[win:n - win + 1]) / win
        best = max(best, float(np.abs(right - left).max()))
    return best


def blob_pair(w=640, h=400):
    """Two unrelated flat frames, each with one textured blob: A dark with
    the blob left of center, B bright with it right of center. Saliency
    has exactly one thing to find in each."""
    A = np.full((h, w, 3), 60, np.uint8)
    B = np.full((h, w, 3), 200, np.uint8)
    r = np.random.default_rng(3)
    pa, pb = (140, 200), (500, 210)
    for img, (cx, cy) in ((A, pa), (B, pb)):
        for _ in range(60):
            ang, rad = r.random() * 2 * np.pi, r.random() * 55
            cv2.circle(img, (int(cx + rad * np.cos(ang)), int(cy + rad * np.sin(ang))),
                       int(r.integers(3, 9)), tuple(int(v) for v in r.integers(0, 255, 3)), -1)
    return A, B, pa, pb


def min_coverage(img, disp, ts):
    return min(float(T.forward_splat(img, disp, t)[1].min()) for t in ts)


def run_cli(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = T.main(argv)
    return rc, out.getvalue(), err.getvalue()


TMP = Path(tempfile.mkdtemp(prefix="transitions-harness-"))
inner = (slice(40, 400 - 40), slice(40, 640 - 40))

# ===========================================================================
print("== A. isolation and the offline contract ==")
names_t = _imports(ROOT / "transitions.py")
names_r = _imports(ROOT / "reveal.py")
check(1, "transitions.py never imports reveal (AST-level)",
      not any(n == "reveal" or n.startswith("reveal.") for n in names_t))
check(2, "reveal.py never imports transitions (AST-level)",
      not any(n == "transitions" or n.startswith("transitions.")
              for n in names_r))
NET = ("socket", "urllib", "http", "ssl", "requests", "torch", "kornia",
       "torchvision", "huggingface_hub", "transformers")
DEPTH_FUNCS = {"depth_available", "_depth_model", "model_disparity", "cmd_warmup"}
top_t, funcs_t = _imports_by_scope(ROOT / "transitions.py")
leaks = sorted({n for n in top_t if n.split(".")[0] in NET})
stray = sorted({f for f, ns in funcs_t.items() if f not in DEPTH_FUNCS
                and any(n.split(".")[0] in NET for n in ns)})
check(3, f"transitions.py imports nothing that can reach the network or load "
         f"weights at module level ({', '.join(NET[:4])}, ..., torch, kornia); "
         f"torch / transformers / huggingface_hub appear only inside the depth "
         f"functions ({', '.join(sorted(DEPTH_FUNCS))})"
         + (f" — LEAK: {leaks}" if leaks else "")
         + (f" — STRAY: {stray}" if stray else ""), not leaks and not stray)

# ===========================================================================
print("== B. grammar ==")
s = T.spec_from("morph", seconds=0.5, fps=24)
check(4, "n_frames = round(seconds * fps) (0.5 s @ 24 -> 12)", s.n_frames() == 12)
mono = True
for cv in T.CURVES:
    for wa in (1.0, 0.6, 0.0):
        sp = T.spec_from("morph", seconds=0.5, fps=24, warp_curve=cv, warp_amount=wa)
        tw = [sp.progress(i)[0] for i in range(sp.n_frames())]
        mono &= (abs(tw[0]) < 1e-9 and abs(tw[-1] - 1) < 1e-9
                 and all(b >= a - 1e-9 for a, b in zip(tw[:-1], tw[1:])))
check(5, f"warp progress is monotone 0 -> 1 for all {len(T.CURVES)} curves x 3 warp amounts", mono)
check(6, "seconds clamp to [0.1, 10]",
      T.spec_from("morph", seconds=99).seconds == 10.0
      and T.spec_from("morph", seconds=0.01).seconds == 0.1)
bad = 0
for kw in ({"preset": "nope"}, {"style": "nope"}, {"portal": "nope"},
           {"force_class": "C"}):
    try:
        T.spec_from(kw.pop("preset", "morph"), **kw)
    except T.TransitionError:
        bad += 1
    except Exception:
        pass
check(7, "unknown preset / style / portal / class -> TransitionError, never a crash", bad == 4)

# ===========================================================================
print("== C. warp ==")
A = textured(1)
h, w = A.shape[:2]
Tf = np.zeros((h, w, 2), np.float32)
Tf[..., 0], Tf[..., 1] = 17.0, -9.0
out, cov = T.forward_splat(A, Tf, 1.0)
ref = cv2.warpAffine(A, np.float32([[1, 0, 17], [0, 1, -9]]), (w, h),
                     borderMode=cv2.BORDER_REFLECT)
check(8, f"translation field reproduces warpAffine ({mad(out[inner], ref[inner]):.2f} levels < 0.5)",
      mad(out[inner], ref[inner]) < 0.5)
_, cov0 = T.forward_splat(A, Tf, 0.0, np.full((h, w), 0.6, np.float32))
check(9, "importance weighting does not fake holes (coverage ~1 at t=0)",
      (cov0 > 0.5).mean() > 0.99)
id0, _ = T.forward_splat(A, Tf, 0.0)
check(10, f"t=0 splat is the identity ({mad(id0[inner], A[inner]):.3f} levels)",
      mad(id0[inner], A[inner]) < 0.01)
check(11, "to_u8 ROUNDS (1.4 -> 1, 1.6 -> 2, 254.7 -> 255), never truncates",
      T.to_u8(np.float32([1.4, 1.6, 254.7, -3.0])).tolist() == [1, 2, 255, 0])

# ===========================================================================
print("== D. correspondence ==")
A, B, M = affine_pair(expose=False, patch=False)
corr = T.dense_displacement(A, B)
check(12, f"related pair routed to class A ({corr['method']}, "
          f"{corr['diag']['sparse_inliers']} inliers >= {T.TCFG['min_inliers']})",
      corr["cls"] == "A" and corr["diag"]["sparse_inliers"] >= T.TCFG["min_inliers"])
gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
tx = M[0, 0] * gx + M[0, 1] * gy + M[0, 2]
ty = M[1, 0] * gx + M[1, 1] * gy + M[1, 2]
gt = np.stack([tx - gx, ty - gy], -1)
err = np.linalg.norm(corr["dAB"] - gt, axis=2)[inner]
check(13, f"dense field matches the ground-truth affine (median err {np.median(err):.2f} px < 1.5)",
      np.median(err) < 1.5)
U = textured(9)[::-1, ::-1].copy()
_logbuf = io.StringIO()
_hd = logging.StreamHandler(_logbuf)
T.log.addHandler(_hd)
T.log.setLevel(logging.INFO)
corr_u = T.dense_displacement(A, U)
T.log.removeHandler(_hd)
check(14, f"unrelated pair routed to class B ({corr_u['method']}) AND says so "
          f"on the log (degrade path is visible)",
      corr_u["cls"] == "B" and "class B" in _logbuf.getvalue())
p = np.float32([[100, 100], [500, 100], [500, 300], [100, 300], [300, 200]])
d0 = T.mls_affine(p, p, h, w)
d1 = T.mls_affine(p, p + [25, -10], h, w)
check(15, "MLS: identity anchors -> zero field; translated anchors -> that translation",
      np.abs(d0).max() < 1e-3 and np.abs(d1[inner] - [25, -10]).max() < 0.5)
corr_b = T.dense_displacement(A, U, anchors=(p, p + [25, -10]), force_class="B")
check(16, "class B honours user anchors (MLS; the default border falloff is on)",
      corr_b["method"] == "mls-anchors+falloff")
corr_f = T.dense_displacement(A, U, force_class="A")
check(17, f"--class A overrides routing on an unrelated pair ({corr_f['method']})",
      corr_f["cls"] == "A" and corr_f["method"].startswith("dis"))
try:
    T.dense_displacement(A, A[:-2])
    _mis = False
except T.TransitionError:
    _mis = True
check(18, "mismatched canvases raise TransitionError", _mis)

# ===========================================================================
print("== E. color path ==")
A, B, M = affine_pair()
sA, sB = T.lab_stats(A), T.lab_stats(B)
Ai, Bi = T.color_pair_at(A, B, sA, sB, 0.5, 1.0)
check(19, "color path pulls both endpoints toward the midpoint statistic",
      abs(T.lab_stats(Ai)[0, 0] - T.lab_stats(Bi)[0, 0]) < abs(sA[0, 0] - sB[0, 0]) + 1e-6)
_same = np.abs(T.apply_stats(A, sA, sA, 1.0).astype(int) - A.astype(int))
check(20, "strength 0 is a no-op; identical statistics give the input back "
          f"(mean {_same.mean():.4f} < 0.02 levels, max {_same.max()} <= 1; "
          f"truncating casts gave 0.92)",
      np.array_equal(T.apply_stats(A, sA, sB, 0.0), A)
      and _same.mean() < 0.02 and _same.max() <= 1)

# ===========================================================================
print("== F. render ==")
all_ok = True
for preset in T.PRESETS:
    fr, rep = T.render_frames(A, B, T.spec_from(preset, seconds=0.4, fps=20))
    q = T.assess(fr, A, B)
    ok = (len(fr) == 8 and q["endpoint"]["first_vs_A"] == 0
          and q["endpoint"]["last_vs_B"] == 0
          and q["flicker"]["edge_ratio"] < 1.5 and q["flicker"]["max"] < 0.12)
    all_ok &= ok
    print(f"        {preset:<13} edge_ratio {q['flicker']['edge_ratio']:.2f}  "
          f"max step {q['flicker']['max']*255:.1f} levels  {'ok' if ok else 'XX'}")
check(21, f"every preset ({len(T.PRESETS)}): 8 frames, byte-exact endpoints, "
          f"edge_ratio < 1.5, no step > 0.12", all_ok)
approach = True
for preset in T.PRESETS:
    frp, _ = T.render_frames(A, B, T.spec_from(preset, seconds=0.4, fps=20))
    seq = [mad(f, B) for f in frp]
    approach &= (all(b <= a + 0.2 for a, b in zip(seq[:-1], seq[1:]))
                 and mad(frp[-2], B) < mad(frp[-2], A))
check(22, "every preset approaches B monotonically (MAD to B non-increasing frame "
          "to frame) and its penultimate frame is nearer B than A", approach)
fr, rep = T.render_frames(A, B, T.spec_from("morph", seconds=0.4, fps=20))
fr2, _ = T.render_frames(A, B, T.spec_from("morph", seconds=0.4, fps=20))
check(23, "rendering is deterministic (two runs, identical bytes)",
      frames_hash(fr) == frames_hash(fr2))
frd, _ = T.render_frames(A, B, T.spec_from("dissolve", seconds=1.0, fps=30, color_strength=0.0))
g = [T._g(f) for f in frd]
d = [float(np.abs(a - b).mean()) * 255 for a, b in zip(g[:-1], g[1:])]
fl = T.flicker(frd)
check(24, f"no manufactured endpoint step: clean dissolve, last step {d[-1]:.2f} levels "
          f"< 0.1, edge_ratio {fl['edge_ratio']:.2f} < 0.2 (truncating casts gave 0.79 / 1.17)",
      d[-1] < 0.1 and fl["edge_ratio"] < 0.2)

# ===========================================================================
print("== G. quality basket ==")
cut = [A] + [B] * 9
lin = [T.to_u8(A.astype(np.float32) * (1 - t) + B.astype(np.float32) * t)
       for t in np.linspace(0, 1, 10)]
er_cut, er_lin = T.flicker(cut)["edge_ratio"], T.flicker(lin)["edge_ratio"]
check(25, f"hidden-cut detector: a cut hidden at the start scores {er_cut:.0f} (> 10), "
          f"a linear dissolve {er_lin:.2f} (< 1.5)", er_cut > 10 and er_lin < 1.5)
pan = [cv2.warpAffine(A, np.float32([[1, 0, 3 * i], [0, 1, 0]]), (w, h),
                      borderMode=cv2.BORDER_REFLECT) for i in range(6)]
rnd = [textured(s) for s in range(6)]
we_pan, we_rnd = T.warping_error(pan), T.warping_error(rnd)
check(26, f"warping error separates a coherent pan ({we_pan:.3f} < 0.03) from "
          f"unrelated frames ({we_rnd:.3f} > 0.1)", we_pan < 0.03 and we_rnd > 0.1)

# ===========================================================================
print("== H. CLI + the real mp4 ==")
pa, pb = TMP / "A.png", TMP / "B.png"
cv2.imwrite(str(pa), cv2.cvtColor(A, cv2.COLOR_RGB2BGR))
cv2.imwrite(str(pb), cv2.cvtColor(B, cv2.COLOR_RGB2BGR))
out1 = TMP / "morph"
rc, so, se = run_cli(["pair", str(pa), str(pb), "--out", str(out1),
                      "--seconds", "1.0", "--preset", "morph"])
rep = json.loads((out1 / "report.json").read_text()) if (out1 / "report.json").exists() else {}
check(27, "pair: exit 0; transition.mp4 + strip.jpg + report.json written; "
          f"report n_frames = 30 (got {rep.get('n_frames')})",
      rc == 0 and (out1 / "transition.mp4").exists() and (out1 / "strip.jpg").exists()
      and rep.get("n_frames") == 30)
meta, dec = decode_all(out1 / "transition.mp4")
check(28, f"mp4 decodes: {meta['w']}x{meta['h']} @ {meta['fps']:.0f} fps, "
          f"{meta['n']} indexed / {len(dec)} decoded frames == 30",
      meta["w"] == w and meta["h"] == h and abs(meta["fps"] - 30) < 0.5
      and meta["n"] == 30 and len(dec) == 30)
_gap = mad(A, B)
ok_end = (len(dec) == 30 and mad(dec[0], A) < 6.0 and mad(dec[-1], B) < 6.0
          and mad(dec[0], A) < 0.2 * _gap and mad(dec[-1], B) < 0.2 * _gap)
check(29, "first decoded frame is A and the last is B "
          f"({mad(dec[0], A) if dec else 99:.2f} / {mad(dec[-1], B) if dec else 99:.2f} levels: "
          f"< 6 and < 20% of the A-B gap {_gap:.1f}; yuv420p alone costs ~3.5)",
      ok_end)
check(30, "no all-black frame in the mp4",
      len(dec) == 30 and min(float(f.mean()) for f in dec) > 5.0)
check(31, "report quality basket: byte-exact endpoints on the proxy and edge_ratio < 1.0 "
          f"(got {rep.get('quality', {}).get('flicker', {}).get('edge_ratio')})",
      rep.get("quality", {}).get("endpoint", {}).get("first_vs_A") == 0
      and rep["quality"]["endpoint"]["last_vs_B"] == 0
      and rep["quality"]["flicker"]["edge_ratio"] < 1.0)

out2 = TMP / "wipe"
rc, so, se = run_cli(["pair", str(pa), str(pb), "--out", str(out2),
                      "--seconds", "1.0", "--preset", "wipe", "--color", "0"])
_, decw = decode_all(out2 / "transition.mp4")
seams = []
for f in decw:
    ca = np.abs(f.astype(np.float32) - A).mean(axis=(0, 2))
    cb = np.abs(f.astype(np.float32) - B).mean(axis=(0, 2))
    seams.append(int((cb < ca).sum()))            # columns already showing B
check(32, f"wipe: the seam sweeps left -> right monotonically "
          f"(B-columns {seams[0] if seams else '-'} -> {seams[-1] if seams else '-'} of {w})",
      rc == 0 and len(seams) == 30 and seams[0] < 8 and seams[-1] > w - 8
      and all(b >= a - 2 for a, b in zip(seams[:-1], seams[1:])))

out3 = TMP / "morph2"
rc, _, _ = run_cli(["pair", str(pa), str(pb), "--out", str(out3),
                    "--seconds", "1.0", "--preset", "morph"])
_, dec2 = decode_all(out3 / "transition.mp4")
check(33, "two CLI runs decode to identical frames (end-to-end deterministic)",
      rc == 0 and len(dec2) == len(dec) and frames_hash(dec) == frames_hash(dec2))

rc, so, se = run_cli(["pair", str(TMP / "missing.jpg"), str(pb), "--out", str(TMP / "x")])
check(34, "missing input -> exit 2, 'FAILED:' on stderr, no traceback",
      rc == 2 and se.startswith("FAILED:") and "Traceback" not in se)
rc, so, _ = run_cli(["pair", str(pa), str(pb), "--out", str(TMP / "tiny"),
                     "--seconds", "0.01", "--fps", "30"])
tiny = json.loads((TMP / "tiny" / "report.json").read_text())
check(35, f"--seconds below the floor clamps to 0.1 s (3 frames; got {tiny['n_frames']})",
      rc == 0 and tiny["spec"]["seconds"] == 0.1 and tiny["n_frames"] == 3)
rc, so, _ = run_cli(["check"])
check(36, "check exits 0 with every row OK", rc == 0 and "!!" not in so)

# ===========================================================================
print("== J. canvas policy (owner ruling 2026-09-14: the finish ratio wins) ==")
_S = np.zeros((2000, 1000, 3), np.uint8)      # portrait start
_F = np.zeros((1500, 1500, 3), np.uint8)      # square finish
_w, _h = T.common_canvas(_S, _F)
check(39, f"finish policy: the canvas takes the FINISH ratio and upscales neither source "
          f"(portrait 1000x2000 + square 1500x1500 -> {_w}x{_h}, expect 1000x1000)",
      (_w, _h) == (1000, 1000))
_w2, _h2 = T.common_canvas(_S, _F, policy="common")
_w3, _h3 = T.common_canvas(_S, _F, max_long=500)
check(40, f"common policy keeps the old rule ({_w2}x{_h2}, expect 1000x1500); "
          f"max_long caps the finish canvas ({_w3}x{_h3}, expect 500x500); unknown policy refused",
      (_w2, _h2) == (1000, 1500) and (_w3, _h3) == (500, 500) and _refused_policy())

# ===========================================================================
print("== K. class B keeps both frames covering the canvas (defect T13, 2026-09-14) ==")
_h, _w = 400, 640
_A0 = np.full((_h, _w, 3), 60, np.uint8)
_B0 = np.full((_h, _w, 3), 200, np.uint8)
_shift = np.zeros((_h, _w, 2), np.float32)
_shift[..., 0] = 160.0
_half = np.full((_h, _w), 0.5, np.float32)
_corr_old = {"dAB": _shift, "dBA": -_shift, "wA": _half, "wB": _half}
_hole = float((T.forward_splat(_A0, _shift, 0.5)[1] < T.TCFG["hole_thresh"]).mean())
_mid_old = T.morph_frame(_A0, _B0, _corr_old, 0.5, 0.5)
_step_old = profile_step(_mid_old, _B0)
check(41, "positive control: a whole-frame translation (the old class B shape) leaves "
          f"{_hole:.0%} of the canvas without A and its mid frame steps {_step_old:.0f} levels "
          "at the exposed edge (> 10 % and > 40): the border the owner saw",
      _hole > 0.10 and _step_old > 40)
_ts = (0.25, 0.5, 0.75, 1.0)
_dfar, _ffar = T.panzoom_field(_h, _w, (100, 200), (600, 200), 0.10)
_dback, _fback = T.panzoom_field(_h, _w, (600, 200), (100, 200), 0.10)
_dnear, _fnear = T.panzoom_field(_h, _w, (300, 200), (330, 210), 0.10)
_cov = min(min_coverage(_A0, _dfar, _ts), min_coverage(_B0, _dback, _ts),
           min_coverage(_A0, _dnear, _ts))
check(42, f"panzoom_field keeps the frame covering the canvas at t = 0.25..1 (min coverage "
          f"{_cov:.2f} >= 0.5) while moving it (max {np.abs(_dfar).max():.0f} px >= 8); a far "
          f"target is panned {_ffar:.0%} of the way (the 10 % zoom's slack), a near one "
          f"{_fnear:.0%} so the pivot lands on it",
      _cov >= 0.5 and np.abs(_dfar).max() >= 8 and 0 < _ffar < 0.05 and _fnear == 1.0
      and np.abs(_dnear[200, 300] - [30, 10]).max() < 1e-3)
_Ab, _Bb, _pa, _pb = blob_pair()
_corr_b = T.dense_displacement(_Ab, _Bb)
_boxc = T._box_center(T.salient_box(_Ab))
_cov_b = min(min_coverage(_Ab, _corr_b["dAB"], _ts[:3]),
             min_coverage(_Bb, _corr_b["dBA"], _ts[:3]))
_mid_b = T.morph_frame(_Ab, _Bb, _corr_b, 0.5, 0.5)
_step_b = max(profile_step(_mid_b, _Bb), profile_step(_mid_b, _Ab))
check(43, f"class B end to end ({_corr_b['method']}): saliency finds the blob "
          f"({np.hypot(_boxc[0] - _pa[0], _boxc[1] - _pa[1]):.0f} px from it, < 30), the field "
          f"moves (max {np.abs(_corr_b['dAB']).max():.0f} px >= 8), no hole at t = 0.25..0.75 "
          f"(min coverage {_cov_b:.2f} >= 0.5) and the mid frame's largest profile step is "
          f"{_step_b:.0f} levels (< 30; the whole-frame shape measured {_step_old:.0f})",
      _corr_b["cls"] == "B" and _corr_b["method"] == "saliency-panzoom"
      and np.hypot(_boxc[0] - _pa[0], _boxc[1] - _pa[1]) < 30
      and np.abs(_corr_b["dAB"]).max() >= 8 and _cov_b >= 0.5 and _step_b < 30
      and "pan_fraction" in _corr_b["diag"])


# ===========================================================================
print("== L. camera move: --camera flat|ramp|model, --zoom (TR10, 2026-09-23) ==")
_A1, _B1, _ = affine_pair()
_fr_flat, _rep_flat = T.render_frames(_A1, _B1, T.spec_from("morph", seconds=0.4, fps=20))
_lb = io.StringIO()
_hd = logging.StreamHandler(_lb)
T.log.addHandler(_hd)
_fr_req, _rep_req = T.render_frames(_A1, _B1, T.spec_from("morph", seconds=0.4, fps=20,
                                                          camera="model", zoom=0.25))
T.log.removeHandler(_hd)
_Ab, _Bb, _, _ = blob_pair()
_c0 = T.dense_displacement(_Ab, _Bb)
_c1 = T.dense_displacement(_Ab, _Bb, camera="flat", zoom=T.TCFG["classb_zoom"])
check(44, "the camera is a class B option: on the class A pair `--camera model` renders the "
          "flat bytes, loads no model and says so on the log; class B `flat` at the default zoom "
          f"is the 2026-09-14 field byte for byte ({_c1['method']}, weight 0.5, report camera "
          f"{_c1['diag'].get('camera')} / zoom {_c1['diag'].get('zoom')})",
      frames_hash(_fr_flat) == frames_hash(_fr_req) and T._DEPTH is None
      and "camera move applies to the class B" in _lb.getvalue() and "camera" not in _rep_req
      and np.array_equal(_c0["dAB"], _c1["dAB"]) and np.array_equal(_c0["dBA"], _c1["dBA"])
      and _c1["method"] == "saliency-panzoom" and float(_c1["wA"].min()) == 0.5 == float(_c1["wA"].max())
      and _c1["diag"]["camera"] == "flat" and _c1["diag"]["zoom"] == T.TCFG["classb_zoom"])
_cr = T.dense_displacement(_Ab, _Bb, camera="ramp", zoom=0.25)
_cu = T.dense_displacement(_Ab, _Bb, camera="flat", zoom=0.25)
_hb = _Ab.shape[0] // 5
_mag, _magu = np.linalg.norm(_cr["dAB"], axis=2), np.linalg.norm(_cu["dAB"], axis=2)
_top, _bot = float(np.median(_mag[:_hb])), float(np.median(_mag[-_hb:]))
_ratio_u = float(np.median(_magu[-_hb:]) / max(np.median(_magu[:_hb]), 1e-6))
check(45, f"ramp at zoom 0.25: the bottom fifth of the frame moves {_bot:.1f} px against "
          f"{_top:.1f} px at the top ({_bot / max(_top, 1e-6):.2f}x >= 1.5; flat gives "
          f"{_ratio_u:.2f}x), near rows win the splat (weight {_cr['wA'][-1, 0]:.2f} > "
          f"{_cr['wA'][0, 0]:.2f}), method {_cr['method']}, report carries camera / zoom / "
          f"disparity_mean {_cr['diag'].get('disparity_mean')}",
      _bot >= 1.5 * _top and _ratio_u < 1.5 and _cr["wA"][-1, 0] > _cr["wA"][0, 0]
      and _cr["method"] == "saliency-panzoom+ramp" and _cr["diag"]["camera"] == "ramp"
      and _cr["diag"]["zoom"] == 0.25 and "disparity_mean" in _cr["diag"])
_ts3 = (0.25, 0.5, 0.75)
_cov_r = min(min_coverage(_Ab, _cr["dAB"], _ts3), min_coverage(_Bb, _cr["dBA"], _ts3))
_th = T.TCFG["hole_thresh"]
_hole_r = max(float((T.forward_splat(_Ab, _cr["dAB"], 0.5, _cr["wA"])[1] < _th).mean()),
              float((T.forward_splat(_Bb, _cr["dBA"], 0.5, _cr["wB"])[1] < _th).mean()))
_mid_r = T.morph_frame(_Ab, _Bb, _cr, 0.5, 0.5)
_step_r = max(profile_step(_mid_r, _Bb), profile_step(_mid_r, _Ab))
# the mutation, applied: a gain of 3 makes the factor -0.5 at the top row, so the top edge
# moves INTO the canvas and the coverage guarantee (a sign condition) breaks
_cb = T.dense_displacement(_Ab, _Bb, camera="ramp", zoom=0.25, cfg=dict(T.TCFG, depth_gain=3.0))
_hole_bad = float((T.forward_splat(_Ab, _cb["dAB"], 0.5, _cb["wA"])[1] < _th).mean())
check(46, f"ramp keeps both frames covering the canvas: mid-frame holes {_hole_r:.2%} <= 1 % "
          f"(the T13 number), largest profile step {_step_r:.0f} levels < 30, min coverage "
          f"{_cov_r:.2f} >= 0.25 at t = 0.25..0.75 (coverage is the inverse of the local stretch, "
          f"about 1 / (1 + 0.25 x 1.5)^2 = 0.53 on the bottom rows, not a hole); a gain that turns "
          f"the top factor negative (3.0) opens {_hole_bad:.1%} holes (> 1 %): the positive factor "
          "is the guarantee",
      _hole_r <= 0.01 and _step_r < 30 and _cov_r >= 0.25 and _hole_bad > 0.01)
out4 = TMP / "ramp"
rc, so, se = run_cli(["pair", str(pa), str(pb), "--out", str(out4), "--seconds", "0.5",
                      "--preset", "morph", "--class", "B", "--camera", "ramp", "--zoom", "0.9"])
rep4 = json.loads((out4 / "report.json").read_text()) if (out4 / "report.json").exists() else {}
try:
    T.spec_from("morph", camera="nope")
    _bad_cam = False
except T.TransitionError:
    _bad_cam = True
check(47, f"CLI: --zoom 0.9 is clamped to {T.TCFG['zoom_range'][1]} and report.json says camera "
          f"{rep4.get('camera')} / zoom {rep4.get('zoom')} (spec.zoom "
          f"{rep4.get('spec', {}).get('zoom')}), method {rep4.get('method')}; an unknown camera "
          "is refused",
      rc == 0 and rep4.get("camera") == "ramp" and rep4.get("zoom") == T.TCFG["zoom_range"][1]
      and rep4.get("spec", {}).get("zoom") == T.TCFG["zoom_range"][1]
      and rep4.get("method") == "saliency-panzoom+ramp" and _bad_cam)

if not T.depth_available():
    print("  [--]  48-51 skipped: torch + transformers not installed (optional; ./setup.sh --learned)")
else:
    _man = T.depth_manifest() or {}
    _mb = sum(f["size"] for f in _man.get("files", [])) / 1e6
    _st = _man.get("self_test", {})
    check(48, f"depth model files live INSIDE the project ({len(_man.get('files', []))} files, "
              f"{_mb:.0f} MB, {len(_man.get('links', []))} links in ./models/depth), the manifest "
              f"is verified by a self-test (floor {_st.get('bottom20_mean')} nearer than sky "
              f"{_st.get('top20_mean')}) and every recorded file is present and checksum-intact",
          bool(_man) and str(T.DEPTH_DIR).startswith(str(T.MODELS_DIR)) and T.MODELS_DIR.exists()
          and _man.get("verified") is True and _man.get("model") == T.DEPTH_MODEL
          and _st.get("bottom20_mean", 0) > _st.get("top20_mean", 1) + 0.3
          and T.depth_weights_cached(deep=True))

    # THE offline proof: kill every socket, reload the model from disk, run it.
    class _DeadSocket:
        def __init__(self, *a, **k):
            raise OSError("network blocked by harness")

    def _dead(*a, **k):
        raise OSError("network blocked by harness")
    _rs, _rc = socket.socket, socket.create_connection
    socket.socket, socket.create_connection = _DeadSocket, _dead
    try:
        T._DEPTH = None                       # force a cold load from disk
        _S = T._selftest_scene()
        _t0 = time.time()
        _d1 = T.model_disparity(_S)
        _s1 = time.time() - _t0
        _d2 = T.model_disparity(_S)
        _top_m, _bot_m = T.depth_selftest(_d1)
    finally:
        socket.socket, socket.create_connection = _rs, _rc
    check(49, "runs with ALL sockets blocked: cold-loads from ./models/depth and reads the "
              f"self-test floor nearer ({_bot_m}) than the sky ({_top_m}); disparity at the input "
              f"size in 0..1, finite, two runs byte-identical ({_s1:.2f} s for the load + one "
              "640x400 image on the CPU)",
          _d1.shape == _S.shape[:2] and bool(np.isfinite(_d1).all()) and _bot_m > _top_m + 0.3
          and np.array_equal(_d1, _d2) and float(_d1.min()) >= 0 and float(_d1.max()) <= 1)
    _cm = T.dense_displacement(_S, _Bb, force_class="B", camera="model", zoom=0.25)
    _magm = np.linalg.norm(_cm["dAB"], axis=2)
    _topm, _botm = float(np.median(_magm[:_hb])), float(np.median(_magm[-_hb:]))
    check(50, f"model on the self-test scene forced to class B: the floor (bottom fifth) moves "
              f"{_botm:.1f} px against {_topm:.1f} px for the sky ({_botm / max(_topm, 1e-6):.2f}x "
              f">= 1.5, the same sign as ramp), method {_cm['method']}, disparity means "
              f"{_cm['diag'].get('disparity_mean')}",
          _botm >= 1.5 * _topm and _cm["method"] == "saliency-panzoom+model"
          and _cm["diag"]["camera"] == "model")
    # and it must never silently reach for the network, or for ramp, during a job
    _bak = T.DEPTH_MANIFEST.read_text()
    T.DEPTH_MANIFEST.unlink()
    T._DEPTH = None
    socket.socket, socket.create_connection = _DeadSocket, _dead
    try:
        T.dense_displacement(_S, _Bb, force_class="B", camera="model", zoom=0.25)
        _guard, _msg = False, ""
    except T.TransitionError as e:
        _guard, _msg = True, str(e)
    except Exception as e:
        _guard, _msg = False, str(e)
    finally:
        socket.socket, socket.create_connection = _rs, _rc
        T.DEPTH_MANIFEST.write_text(_bak)
        T._DEPTH = None
    check(51, "with the manifest missing, --camera model REFUSES before touching the model or "
              "the network, names warmup, and never falls back to ramp silently",
          _guard and "warmup" in _msg and T._DEPTH is None)

# ===========================================================================
print("== M. goal numbers: the basket sees a crossfade and invented content (2026-09-26) ==")
# Calibrated on 343 graded real clips (retrospective 2026-09-26 §5). On the harness
# textures the sharpness and contrast floors invert (the splat's resampling blurs the
# discs more than a blend does), so only the crossfade fit and the feature survival
# are pinned here; the real-clip calibration is the reference for the other two.
_U1, _U2 = textured(1), textured(7)                      # two unrelated scenes
_xf, _ = T.render_frames(_U1, _U2, T.spec_from("dissolve", seconds=0.4, fps=20))
_Aa, _Ba, _ = affine_pair()
_mo, _ = T.render_frames(_Aa, _Ba, T.spec_from("morph", seconds=0.4, fps=20))
_g_xf = T.goal_numbers([T.proxy_of(f) for f in _xf])
_g_mo = T.goal_numbers([T.proxy_of(f) for f in _mo])
check(52, f"dissolve_fit sees a plain crossfade of two unrelated scenes ({_g_xf['dissolve_fit']:.2f} > 0.9) "
          f"and not an aligned morph ({_g_mo['dissolve_fit']:.2f} < 0.5); "
          "mutation: feed the crossfade's frames as the morph -> red",
      _g_xf["dissolve_fit"] > 0.9 and _g_mo["dissolve_fit"] < 0.5
      and _g_mo["dissolve_fit"] < _g_xf["dissolve_fit"])
_r = np.random.default_rng(5)
_inv = (_r.random((400, 640, 3)) * 255).astype(np.uint8)          # a scene in neither photo
cv2.rectangle(_inv, (60, 60), (300, 340), (250, 250, 250), -1)
_invented = [_xf[0]] + [_inv] * (len(_xf) - 2) + [_xf[-1]]
_g_inv = T.goal_numbers([T.proxy_of(f) for f in _invented])
_cli = (rep.get("quality") or {}).get("goal", {})
check(53, f"feat_floor keeps the details of A or B through an aligned morph ({_g_mo['feat_floor']:.2f} > 0.5) "
          f"and reads invented interior frames as none ({_g_inv['feat_floor']:.2f} < 0.1); "
          "report.json carries the five goal keys; mutation: interior = A -> red",
      _g_mo["feat_floor"] > 0.5 and _g_inv["feat_floor"] < 0.1
      and all(k in _cli for k in ("feat_floor", "laplace_floor", "contrast_floor",
                                  "dissolve_fit", "motion_share")))

# ===========================================================================
print("== N. anchors keep the frame on the canvas: border falloff (defect T16, 2026-09-26) ==")
_hN, _wN = 400, 640
_A0n = textured(21, _wN, _hN)
_B0n = textured(22, _wN, _hN)
# three anchors that translate the whole frame by 120 px: the old MLS field moves the border
_src = np.array([[100, 100], [540, 100], [320, 300]], np.float32)
_dst = _src + np.array([120, 0], np.float32)
_def = T.dense_displacement(_A0n, _B0n, anchors=(_src, _dst), force_class="B")
_off = T.dense_displacement(_A0n, _B0n, anchors=(_src, _dst), force_class="B", anchor_falloff=0.0)
_fal = T.dense_displacement(_A0n, _B0n, anchors=(_src, _dst), force_class="B", anchor_falloff=0.2)
_plain_mls = T.mls_affine(_src, _dst, _hN, _wN)
_hole_off = float((T.forward_splat(_A0n, _off["dAB"], 0.5)[1] < T.TCFG["hole_thresh"]).mean())
_hole_fal = float((T.forward_splat(_A0n, _fal["dAB"], 0.5)[1] < T.TCFG["hole_thresh"]).mean())
_hole_def = float((T.forward_splat(_A0n, _def["dAB"], 0.5)[1] < T.TCFG["hole_thresh"]).mean())
_edge = np.abs(np.concatenate([_fal["dAB"][0].ravel(), _fal["dAB"][-1].ravel(),
                               _fal["dAB"][:, 0].ravel(), _fal["dAB"][:, -1].ravel()])).max()
_centre = float(np.abs(_fal["dAB"][_hN // 2, _wN // 2] - _off["dAB"][_hN // 2, _wN // 2]).max())
check(54, f"--anchor-falloff 0 gives the 2026-09-13 MLS field byte for byte ({_off['method']}); the "
          f"default ({T.TCFG['anchor_falloff']}) is {_def['method']} with {_hole_def:.2%} holes; at 0.2 the field "
          f"is 0 on the border (max {_edge:.3f} px), equals the plain field at the centre (diff {_centre:.3f} px), "
          f"and the mid-frame hole fraction falls from {_hole_off:.1%} to {_hole_fal:.2%}; "
          "mutation: a constant weight -> holes stay, red",
      np.array_equal(_off["dAB"], _plain_mls) and _off["method"] == "mls-anchors"
      and _def["method"] == "mls-anchors+falloff" and _hole_def < 0.01
      and _fal["method"] == "mls-anchors+falloff" and _edge < 1e-3 and _centre < 1e-3
      and _hole_off > 0.05 and _hole_fal < 0.01)

# ===========================================================================
print("== I. identity fence (the tool is called transitions; owner ruling 2026-09-13) ==")
_src = (ROOT / "transitions.py").read_text()
check(37, "persisted identifiers are pinned: module transitions.py, outputs transition.mp4 / "
          "strip.jpg / report.json, logger 'transitions', argparse prog 'transitions.py'",
      (ROOT / "transitions.py").exists() and T.log.name == "transitions"
      and 'prog="transitions.py"' in _src
      and all(n in _src for n in ('"transition.mp4"', '"strip.jpg"', '"report.json"'))
      and rep.get("outputs") == ["transition.mp4", "strip.jpg", "report.json"])
check(38, "the research codename never leaks into the shipped tool "
          "(the word 'impossible' does not occur in transitions.py)",
      "impossible" not in _src.lower())

# ===========================================================================
print(f"\n{PASS} passed, {FAIL} failed")
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if FAIL else 0)
