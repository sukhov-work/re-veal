#!/usr/bin/env python3
"""Automatic theme anchors between two UNRELATED photos: DINOv2 patch features with mutual nearest
neighbours, plus classical detectors for the textureless themes (the sun as the brightest blob,
the horizon as the strongest horizontal edge row, faces with OpenCV's YuNet).

Research script (2026-09-26, plan §Rank 2026-09-26 item 3, second half; Track B's recipe without
the panoptic model). Imports neither tool. Weights: DINOv2-S (facebook/dinov2-small, Apache-2.0,
88 MB) into a scratch HF_HOME given by --hf-home (never models/), YuNet (opencv_zoo, MIT, 230 KB)
into the same folder. Preprocessing with cv2 (no torchvision): 518 px short side, multiples of 14,
ImageNet statistics, as the model card's processor does.

  .venv/bin/python scripts/research/auto_anchors.py --pairs mismatch_1,... --out DIR --hf-home DIR
Writes per pair: matches.jpg (side by side with the surviving matches), anchors_auto.json
(the anchor list in canvas px of the tool's finish canvas capped at --max-long), and a summary.
"""
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

DINO = "facebook/dinov2-small"
YUNET_URL = ("https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/"
             "face_detection_yunet_2023mar.onnx")
MEAN = np.array([0.485, 0.456, 0.406], np.float32)
STD = np.array([0.229, 0.224, 0.225], np.float32)


def canvas_pair(pair, max_long):
    """The two photos on the tool's canvas (finish ratio, capped), exactly as `pair` renders them."""
    import transitions as T
    S = sorted((ROOT / "fixtures").glob(f"{pair}_S.*"))[0]
    F = sorted((ROOT / "fixtures").glob(f"{pair}_F.*"))[0]
    A = T.load_image_rgb(str(S))
    B = T.load_image_rgb(str(F))
    w, h = T.common_canvas(A, B, max_long, "finish")
    return T.cover(A, w, h), T.cover(B, w, h)


def dino_features(model, torch, rgb, short=518):
    h, w = rgb.shape[:2]
    s = short / min(h, w)
    nh, nw = max(14, int(round(h * s / 14)) * 14), max(14, int(round(w * s / 14)) * 14)
    x = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_CUBIC).astype(np.float32) / 255.0
    x = (x - MEAN) / STD
    t = torch.from_numpy(x.transpose(2, 0, 1)[None])
    with torch.no_grad():
        out = model(pixel_values=t)
    feats = out.last_hidden_state[0, 1:]           # drop the CLS token
    feats = torch.nn.functional.normalize(feats, dim=-1).numpy()
    gh, gw = nh // 14, nw // 14
    return feats, (gh, gw), (w / nw, h / nh)


def mutual_nn(fa, fb, ratio=0.9):
    sim = fa @ fb.T
    ab = sim.argmax(1)
    ba = sim.argmax(0)
    idx = np.arange(len(fa))
    mutual = ba[ab] == idx
    # a weak ratio test on the second best so flat regions do not match everywhere
    part = np.partition(sim, -2, axis=1)
    second = part[:, -2]
    best = sim[idx, ab]
    keep = mutual & (second < ratio * best)
    return idx[keep], ab[keep], best[keep]


def grid_xy(i, gh, gw, sx, sy):
    y, x = divmod(int(i), gw)
    return ((x + 0.5) * 14 * sx, (y + 0.5) * 14 * sy)


def sun(rgb):
    g = cv2.GaussianBlur(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), (0, 0), 5)
    _, mx, _, loc = cv2.minMaxLoc(g)
    mask = (g > 0.92 * mx).astype(np.uint8)
    n, lab, stats, cent = cv2.connectedComponentsWithStats(mask)
    if n < 2:
        return None
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    area = int(stats[k, cv2.CC_STAT_AREA])
    if area < 200 or mx < 230:
        return None
    return (float(cent[k][0]), float(cent[k][1]), float(np.sqrt(area / np.pi)))


def horizon(rgb):
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    gy = np.abs(cv2.Sobel(cv2.GaussianBlur(g, (0, 0), 2), cv2.CV_32F, 0, 1, ksize=3)).mean(axis=1)
    h = g.shape[0]
    lo, hi = int(h * 0.25), int(h * 0.85)
    return lo + int(np.argmax(gy[lo:hi])), float(gy[lo:hi].max() / (gy.mean() + 1e-6))


def faces(rgb, hf_home):
    onnx = Path(hf_home) / "face_detection_yunet_2023mar.onnx"
    if not onnx.exists():
        onnx.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(YUNET_URL, onnx)
    h, w = rgb.shape[:2]
    det = cv2.FaceDetectorYN.create(str(onnx), "", (w, h), 0.7, 0.3, 200)
    det.setInputSize((w, h))
    _, res = det.detect(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    out = []
    if res is not None:
        for r in res:
            x, y, bw, bh = r[:4]
            out.append({"box": [float(x), float(y), float(bw), float(bh)], "score": float(r[14]),
                        "landmarks": [[float(r[4 + 2 * i]), float(r[5 + 2 * i])] for i in range(5)]})
    out.sort(key=lambda f: -f["box"][2] * f["box"][3])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", default="mismatch_1,mismatch_2,mismatch_3,mismatch_4,mismatch_5,mismatch_6")
    ap.add_argument("--out", required=True)
    ap.add_argument("--hf-home", required=True)
    ap.add_argument("--max-long", type=int, default=1920)
    ap.add_argument("--min-sim", type=float, default=0.55)
    a = ap.parse_args()
    os.environ["HF_HOME"] = str(Path(a.hf_home).resolve())
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    import torch
    torch.set_num_threads(max(1, os.cpu_count() // 2))
    from transformers import AutoModel
    model = AutoModel.from_pretrained(DINO).eval()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    summary = {}
    for pair in a.pairs.split(","):
        A, B = canvas_pair(pair, a.max_long)
        fa, (gha, gwa), (sxa, sya) = dino_features(model, torch, A)
        fb, (ghb, gwb), (sxb, syb) = dino_features(model, torch, B)
        ia, ib, sim = mutual_nn(fa, fb)
        keep = sim >= a.min_sim
        ia, ib, sim = ia[keep], ib[keep], sim[keep]
        pa = np.array([grid_xy(i, gha, gwa, sxa, sya) for i in ia], np.float32).reshape(-1, 2)
        pb = np.array([grid_xy(i, ghb, gwb, sxb, syb) for i in ib], np.float32).reshape(-1, 2)
        inl = np.zeros(len(pa), bool)
        M = None
        if len(pa) >= 3:
            M, mask = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC, ransacReprojThreshold=60.0, maxIters=5000)
            if mask is not None:
                inl = mask.ravel().astype(bool)
        s_a, s_b = sun(A), sun(B)
        h_a, h_b = horizon(A), horizon(B)
        f_a, f_b = faces(A, a.hf_home), faces(B, a.hf_home)
        # draw
        h = max(A.shape[0], B.shape[0])
        side = np.zeros((h, A.shape[1] + B.shape[1], 3), np.uint8)
        side[:A.shape[0], :A.shape[1]] = A
        side[:B.shape[0], A.shape[1]:] = B
        off = A.shape[1]
        for (x1, y1), (x2, y2), ok, s in zip(pa, pb, inl, sim):
            col = (60, 220, 60) if ok else (200, 60, 60)
            cv2.line(side, (int(x1), int(y1)), (int(x2) + off, int(y2)), col, 2 if ok else 1)
        for img_off, sn, hz, fs in ((0, s_a, h_a, f_a), (off, s_b, h_b, f_b)):
            if sn:
                cv2.circle(side, (int(sn[0]) + img_off, int(sn[1])), int(sn[2]), (255, 255, 0), 3)
            cv2.line(side, (img_off, hz[0]), (img_off + (A.shape[1] if img_off == 0 else B.shape[1]), hz[0]), (0, 200, 255), 2)
            for f in fs[:6]:
                x, y, bw, bh = [int(v) for v in f["box"]]
                cv2.rectangle(side, (x + img_off, y), (x + bw + img_off, y + bh), (255, 0, 255), 3)
        cv2.putText(side, f"{pair}: DINOv2-S mutual NN {len(pa)} (sim>={a.min_sim}), similarity inliers {int(inl.sum())}; "
                    f"sun A/B {'yes' if s_a else 'no'}/{'yes' if s_b else 'no'}; faces {len(f_a)}/{len(f_b)}; horizon rows {h_a[0]}/{h_b[0]}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        cv2.imwrite(str(out / f"{pair}_matches.jpg"), cv2.cvtColor(side, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
        # candidate anchors: sun, faces (largest to largest), horizon endpoints, then the inlier matches thinned
        anchors, why = [], []
        if s_a and s_b:
            anchors.append([s_a[0], s_a[1], s_b[0], s_b[1]]); why.append("sun -> sun (brightest blob)")
        if f_a and f_b:
            for fa_, fb_ in zip(f_a[:2], f_b[:2]):
                ca = (fa_["box"][0] + fa_["box"][2] / 2, fa_["box"][1] + fa_["box"][3] / 2)
                cb = (fb_["box"][0] + fb_["box"][2] / 2, fb_["box"][1] + fb_["box"][3] / 2)
                anchors.append([ca[0], ca[1], cb[0], cb[1]]); why.append("face -> face (YuNet, largest first)")
        if h_a[1] > 2.0 and h_b[1] > 2.0:
            wA, wB = A.shape[1], B.shape[1]
            anchors += [[0.1 * wA, h_a[0], 0.1 * wB, h_b[0]], [0.9 * wA, h_a[0], 0.9 * wB, h_b[0]]]
            why.append("horizon -> horizon (strongest horizontal edge row)")
        if inl.sum():
            pts = [(x1, y1, x2, y2) for (x1, y1), (x2, y2), ok in zip(pa, pb, inl) if ok]
            step = max(1, len(pts) // 6)
            for x1, y1, x2, y2 in pts[::step][:6]:
                anchors.append([float(x1), float(y1), float(x2), float(y2)])
            why.append(f"{min(6, len(pts))} DINOv2 mutual-NN similarity inliers of {len(pts)}")
        summary[pair] = {"canvas": [int(A.shape[1]), int(A.shape[0])], "mutual_nn": int(len(pa)),
                         "similarity_inliers": int(inl.sum()), "mean_sim": float(sim.mean()) if len(sim) else None,
                         "sun": [s_a, s_b], "horizon": [h_a, h_b], "faces": [len(f_a), len(f_b)],
                         "anchors": anchors, "why": "; ".join(why)}
        print(pair, json.dumps({k: v for k, v in summary[pair].items() if k not in ("anchors",)}), flush=True)
        (out / f"{pair}_anchors_auto.json").write_text(json.dumps({pair: {"anchors": anchors, "why": summary[pair]["why"]}}, indent=1))
    (out / "summary.json").write_text(json.dumps(summary, indent=1))


if __name__ == "__main__":
    sys.exit(main())
