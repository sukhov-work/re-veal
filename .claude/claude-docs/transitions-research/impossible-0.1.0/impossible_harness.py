#!/usr/bin/env python3
"""Harness for the `impossible` package. Independent of Reveal's harness.py
by contract. Run: python3 impossible_harness.py"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from impossible import color as C          # noqa: E402
from impossible import correspond as CO    # noqa: E402
from impossible import generative as G     # noqa: E402
from impossible import quality as Q        # noqa: E402
from impossible import warp as W           # noqa: E402
import contextlib, io as _io               # noqa: E402
from impossible.cli import main as _main   # noqa: E402


def main(argv):
    with contextlib.redirect_stdout(_io.StringIO()):
        return _main(argv)
from impossible.grammar import SequenceSpec, spec_from  # noqa: E402
from impossible.render import render_frames             # noqa: E402
from impossible.video import Writer, count_frames, frame_at, probe  # noqa: E402

PASS = FAIL = 0


def check(n, desc, cond):
    global PASS, FAIL
    ok = bool(cond)
    PASS += ok
    FAIL += not ok
    print(f"  [{'ok' if ok else 'XX'}] {n:>3} {desc}")


TMP = Path(tempfile.mkdtemp(prefix="impossible-"))
rng = np.random.default_rng(0)


def textured(seed, w=640, h=400):
    r = np.random.default_rng(seed)
    img = cv2.GaussianBlur((r.random((h, w, 3)) * 255).astype(np.uint8), (0, 0), 5)
    for _ in range(120):
        cv2.circle(img, (int(r.integers(0, w)), int(r.integers(0, h))),
                   int(r.integers(5, 30)), tuple(int(v) for v in r.integers(0, 255, 3)), -1)
    return img


def mad(x, y):
    return float(np.abs(x.astype(np.float32) - y.astype(np.float32)).mean())


print("== isolation ==")
import ast


def _imports(path):
    tree = ast.parse(Path(path).read_text())
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


check(1, "package never imports reveal (AST-level)",
      not any(n == "reveal" or n.startswith("reveal.")
              for p in Path("impossible").rglob("*.py") for n in _imports(p)))
check(2, "reveal.py never imports impossible (AST-level)",
      not any(n == "impossible" or n.startswith("impossible.") for n in _imports("reveal.py")))

print("== grammar ==")
s = spec_from("morph", seconds=0.5, fps=24)
check(3, "n_frames = round(seconds*fps)", s.n_frames() == 12)
tw = [s.progress(i)[0] for i in range(s.n_frames())]
check(4, "warp progress monotone, 0 -> 1", tw[0] == 0.0 and tw[-1] == 1.0
      and all(b >= a for a, b in zip(tw[:-1], tw[1:])))
check(5, "seconds clamp to [0.1, 10]", spec_from("morph", seconds=99).seconds == 10.0
      and spec_from("morph", seconds=0.01).seconds == 0.1)

print("== warp ==")
A = textured(1)
h, w = A.shape[:2]
T = np.zeros((h, w, 2), np.float32)
T[..., 0], T[..., 1] = 17.0, -9.0
out, cov = W.forward_splat(A, T, 1.0)
ref = cv2.warpAffine(A, np.float32([[1, 0, 17], [0, 1, -9]]), (w, h), borderMode=cv2.BORDER_REFLECT)
inner = (slice(40, h - 40), slice(40, w - 40))
check(6, f"translation field reproduces warpAffine ({mad(out[inner], ref[inner]):.2f} levels)",
      mad(out[inner], ref[inner]) < 0.5)
check(7, "importance weighting does not fake holes (coverage ~1 at t=0)",
      (W.forward_splat(A, T, 0.0, np.full((h, w), 0.6, np.float32))[1] > 0.5).mean() > 0.99)

print("== correspondence ==")
M = cv2.getRotationMatrix2D((w / 2, h / 2), 3.0, 1.06)
M[0, 2] += 12
B = cv2.warpAffine(A, M, (w, h), borderMode=cv2.BORDER_REFLECT)
corr = CO.dense_displacement(A, B)
check(8, f"related pair routed to class A ({corr['method']}, {corr['diag']['sparse_inliers']} inl)",
      corr["cls"] == "A" and corr["diag"]["sparse_inliers"] >= 30)
gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
# ground truth A->B displacement for the affine: where does A pixel land in B
# warpAffine's M maps SOURCE -> DEST: A pixel a appears in B at M a
tx = M[0, 0] * gx + M[0, 1] * gy + M[0, 2]
ty = M[1, 0] * gx + M[1, 1] * gy + M[1, 2]
gt = np.stack([tx - gx, ty - gy], -1)
err = np.linalg.norm(corr["dAB"] - gt, axis=2)[inner]
check(9, f"dense field matches ground truth (median err {np.median(err):.2f} px < 1.5)",
      np.median(err) < 1.5)
U = textured(9)[::-1, ::-1].copy()
corr_u = CO.dense_displacement(A, U)
check(10, f"unrelated pair routed to class B ({corr_u['method']})", corr_u["cls"] == "B")
p = np.float32([[100, 100], [500, 100], [500, 300], [100, 300], [300, 200]])
d0 = CO.mls_affine(p, p, h, w)
d1 = CO.mls_affine(p, p + [25, -10], h, w)
check(11, "MLS: identity anchors -> zero field; translated anchors -> translation",
      np.abs(d0).max() < 1e-3 and np.abs(d1[inner] - [25, -10]).max() < 0.5)
corr_b = CO.dense_displacement(A, U, anchors=(p, p + [25, -10]), force_class="B")
check(12, "class B honours user anchors (MLS)", corr_b["method"] == "mls-anchors")

print("== color ==")
sA, sB = C.lab_stats(A), C.lab_stats(B)
Ai, Bi = C.color_pair_at(A, B, sA, sB, 0.5, 1.0)
check(13, "color path pulls both endpoints toward the midpoint statistic",
      abs(C.lab_stats(Ai)[0, 0] - C.lab_stats(Bi)[0, 0]) < abs(sA[0, 0] - sB[0, 0]) + 1e-6)
check(14, "strength 0 is a no-op", np.array_equal(C.apply_stats(A, sA, sB, 0.0), A))

print("== render ==")
for preset in ("morph", "dissolve", "flow-dissolve", "iris", "luma", "snap-morph"):
    fr, rep = render_frames(A, B, spec_from(preset, seconds=0.4, fps=20))
    q = Q.assess(fr, A, B)
    check(15, f"{preset:<13} 8 frames, exact endpoints, no endpoint step "
              f"(edge_ratio {q['flicker']['edge_ratio']:.2f})",
          len(fr) == 8 and q["endpoint"]["first_vs_A"] == 0 and q["endpoint"]["last_vs_B"] == 0
          and q["flicker"]["edge_ratio"] < 1.5 and q["flicker"]["max"] < 0.1)
fr, rep = render_frames(A, B, spec_from("morph", seconds=0.4, fps=20))
check(16, "penultimate frame is close to B (no endpoint jump)", mad(fr[-2], B) < 6.0)

print("== generative contracts ==")
disps = [corr["dAB"] / 10] * 5
noise = G.warp_noise_along_flow((h, w, 3), disps, seed=1)
check(17, "warped noise stays unit-variance per frame",
      all(abs(n.std() - 1) < 0.05 and abs(n.mean()) < 0.05 for n in noise))
n2 = G.warp_noise_along_flow((h, w, 3), disps, seed=1)
check(18, "noise warp is seed-deterministic", np.array_equal(noise[3], n2[3]))
lo = cv2.resize(B, (w // 3, h // 3))
blend = G.frequency_split_blend(A, lo, sigma=4, amount=1.0)
hiA = (A.astype(np.float32) - cv2.GaussianBlur(A.astype(np.float32), (0, 0), 4)).ravel()
hiO = (blend.astype(np.float32) - cv2.GaussianBlur(blend.astype(np.float32), (0, 0), 4)).ravel()
hiB = (cv2.resize(lo, (w, h)).astype(np.float32)
       - cv2.GaussianBlur(cv2.resize(lo, (w, h)).astype(np.float32), (0, 0), 4)).ravel()
cA, cB = np.corrcoef(hiO, hiA)[0, 1], np.corrcoef(hiO, hiB)[0, 1]
check(19, f"frequency split: output high-pass correlates with the deterministic frame "
          f"({cA:.2f}) not the generated one ({cB:.2f})", cA > 0.85 and cA > cB + 0.3)
fr2, rep2 = render_frames(A, B, spec_from("dream", seconds=0.3, fps=20), backend="null")
check(20, "dreaminess with null backend: reported not-applied, frames untouched",
      rep2["generative"]["applied"] is False)
plan = G.plan_generation("ltx2-mlx-int8-distilled", 24, 600)
check(21, "budget planner picks a ladder resolution or declines", plan is None or plan[0] >= 854)
check(22, "over-budget generation is declined", G.plan_generation("ltx2-mlx-int8", 300, 5) is None)

print("== video ==")
clip = TMP / "clip.mp4"
wr = Writer(clip, w, h, 25)
for i in range(50):
    f = A.copy()
    cv2.circle(f, (60 + i * 10, 200), 30, (255, 255, 255), -1)
    wr.write(f)
n = wr.close()
info = probe(clip)
check(23, f"writer/probe roundtrip: 50 frames @25fps ({info['fps']:.0f} fps, {info['codec']})",
      n == 50 and abs(info["fps"] - 25) < 0.01 and count_frames(clip) == 50)
t, f20 = frame_at(clip, 20 / 25)
check(24, f"frame_at is PTS-exact (asked 0.800 s, got {t:.3f} s)", abs(t - 0.8) < 1e-3)
# the white disc at frame 20 is at x = 60 + 200 = 260
white = np.all(f20[200] >= 250, axis=1)
cx = float(np.mean(np.flatnonzero(white))) if white.any() else -1
check(25, f"the extracted frame is the right one (disc at x={cx:.0f}, expect 260)", 245 < cx < 275)

print("== clips + sequence CLI ==")
clip2 = TMP / "clip2.mp4"
wr = Writer(clip2, w, h, 25)
for i in range(50):
    f = textured(4).copy()
    cv2.rectangle(f, (300 - i * 4, 100), (360 - i * 4, 160), (0, 0, 0), -1)
    wr.write(f)
wr.close()
out = TMP / "clips"
rc = main(["clips", str(clip), str(clip2), "--cut-a", "1.0", "--cut-b", "0.4",
           "--seconds", "0.4", "--preset", "morph", "--out", str(out)])
rep = json.loads((out / "report.json").read_text())
check(26, "clips: exit 0, transition + stitched written",
      rc == 0 and (out / "transition.mp4").exists() and (out / "stitched.mp4").exists())
check(27, f"clips: frame accounting exact (25 + 8 + 40 = {rep['frames_total']})",
      rep["frames_from_a"] == 25 and rep["frames_transition"] == 8
      and rep["frames_from_b"] == 40 and rep["frames_total"] == 73
      and count_frames(out / "stitched.mp4") == 73)
img = TMP / "still.png"
cv2.imwrite(str(img), cv2.cvtColor(textured(11), cv2.COLOR_RGB2BGR))
spec = {"items": [{"path": str(clip), "cut_out": 0.4},
                  {"path": str(img), "hold": 0.4},
                  {"path": str(clip2), "cut_in": 0.4, "cut_out": 0.8}],
        "transitions": [{"preset": "iris", "seconds": 0.2}, {"preset": "morph", "seconds": 0.2}],
        "output": str(TMP / "seq.mp4")}
(TMP / "seq.json").write_text(json.dumps(spec))
rc = main(["sequence", str(TMP / "seq.json")])
srep = json.loads((TMP / "seq.mp4.report.json").read_text())
check(28, f"sequence: 10 + 3 + 10 + 3 + 10 = {srep['frames_total']} frames, mixed media",
      rc == 0 and srep["frames_total"] == 36 and count_frames(TMP / "seq.mp4") == 36)
check(29, "sequence spec roundtrips through SequenceSpec.load/dump",
      SequenceSpec.load(TMP / "seq.json").dump()["output"] == str(TMP / "seq.mp4"))

print(f"\n{PASS} passed, {FAIL} failed")
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if FAIL else 0)
