#!/usr/bin/env python3
"""TR5 research: the DIS field vs the RoMa field on the same canvas (runs in `.venv`).

  --prepare DIR PAIR...        write A.png, B.png (the transitions canvas, --max-long 1920) and the
                               homography+DIS field (dis_dAB/dBA/wA/wB.npy, dis.json) into
                               DIR/pair_<PAIR>/ for scripts/research/roma_probe.py
  --compare DIR OUT PAIR...    after the probe ran on those dirs: render morph 1 s (30 frames) from
                               both fields through transitions.iter_frames and write
                               OUT/<pair>/{dis,roma}_mid.jpg, mid_dis_vs_roma.jpg,
                               strips_dis_vs_roma.jpg and OUT/compare.json (quality basket)
Not part of either tool. The 2026-09-14 numbers are in TRANSITIONS.md §6.
"""
import glob
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import transitions as T  # noqa: E402


def prepare(base, pairs):
    for pid in pairs:
        d = Path(base) / f"pair_{pid}"
        d.mkdir(parents=True, exist_ok=True)
        a = glob.glob(str(ROOT / "fixtures" / f"{pid}_S.*"))[0]
        b = glob.glob(str(ROOT / "fixtures" / f"{pid}_F.*"))[0]
        A, B = T.load_image_rgb(a), T.load_image_rgb(b)
        w, h = T.common_canvas(A, B, 1920)
        A2, B2 = T.cover(A, w, h), T.cover(B, w, h)
        cv2.imwrite(str(d / "A.png"), cv2.cvtColor(A2, cv2.COLOR_RGB2BGR))
        cv2.imwrite(str(d / "B.png"), cv2.cvtColor(B2, cv2.COLOR_RGB2BGR))
        t = time.time()
        corr = T.dense_displacement(A2, B2)
        dt = time.time() - t
        for k in ("dAB", "dBA", "wA", "wB"):
            np.save(str(d / f"dis_{k}.npy"), corr[k])
        info = {"pair": pid, "canvas": [w, h], "method": corr["method"], **corr["diag"],
                "dis_s": round(dt, 2)}
        (d / "dis.json").write_text(json.dumps(info))
        print(json.dumps(info))


def strip(frames, k=8, height=220):
    idx = np.linspace(0, len(frames) - 1, k).round().astype(int)
    tiles = []
    for i in idx:
        f = frames[i]
        h, w = f.shape[:2]
        t = cv2.resize(f, (max(2, int(w * height / h)), height), interpolation=cv2.INTER_AREA)
        cv2.putText(t, f"f{i}", (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        tiles.append(t)
    return np.concatenate(tiles, 1)


def band(txt, w):
    img = np.full((24, w, 3), 30, np.uint8)
    cv2.putText(img, txt, (6, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 230, 255), 1, cv2.LINE_AA)
    return img


def compare(base, out, pairs):
    OUT = Path(out)
    results = {}
    for pid in pairs:
        d = Path(base) / f"pair_{pid}"
        o = OUT / pid
        o.mkdir(parents=True, exist_ok=True)
        A = cv2.cvtColor(cv2.imread(str(d / "A.png")), cv2.COLOR_BGR2RGB)
        B = cv2.cvtColor(cv2.imread(str(d / "B.png")), cv2.COLOR_BGR2RGB)
        spec = T.spec_from("morph", seconds=1.0, fps=30)
        strips = []
        for name in ("dis", "roma"):
            corr = {k: np.load(str(d / f"{name}_{k}.npy")) for k in ("dAB", "dBA", "wA", "wB")}
            corr.update({"cls": "A", "method": name, "diag": {}})
            t = time.time()
            frames = list(T.iter_frames(A, B, spec, corr))
            render_s = round(time.time() - t, 2)
            q = T.assess(frames, A, B)
            cv2.imwrite(str(o / f"{name}_mid.jpg"), cv2.cvtColor(frames[15], cv2.COLOR_RGB2BGR),
                        [cv2.IMWRITE_JPEG_QUALITY, 90])
            strips.append(strip(frames))
            results.setdefault(pid, {})[name] = {
                "render_s": render_s, "warping_error": q["warping_error"],
                "edge_ratio": q["flicker"]["edge_ratio"], "max_step": q["flicker"]["max"],
                "endpoint": q["endpoint"], "cert_mean": round(float(corr["wA"].mean()), 3),
                "median_disp_px": round(float(np.median(np.linalg.norm(corr["dAB"], axis=2))), 2)}
        w = strips[0].shape[1]
        img = np.concatenate([band(f"{pid} morph 1 s, DIS field (current)", w), strips[0],
                              band(f"{pid} morph 1 s, RoMa field", w), strips[1]], 0)
        cv2.imwrite(str(o / "strips_dis_vs_roma.jpg"), cv2.cvtColor(img, cv2.COLOR_RGB2BGR),
                    [cv2.IMWRITE_JPEG_QUALITY, 88])
        mA, mB = cv2.imread(str(o / "dis_mid.jpg")), cv2.imread(str(o / "roma_mid.jpg"))
        h, w = mA.shape[:2]
        side = np.concatenate([cv2.resize(mA, (w // 2, h // 2)), cv2.resize(mB, (w // 2, h // 2))], 1)
        cv2.imwrite(str(o / "mid_dis_vs_roma.jpg"), side, [cv2.IMWRITE_JPEG_QUALITY, 88])
        print(pid, json.dumps(results[pid]))
    (OUT / "compare.json").write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    if len(sys.argv) > 3 and sys.argv[1] == "--prepare":
        prepare(sys.argv[2], sys.argv[3:])
    elif len(sys.argv) > 4 and sys.argv[1] == "--compare":
        compare(sys.argv[2], sys.argv[3], sys.argv[4:])
    else:
        sys.exit(__doc__)
