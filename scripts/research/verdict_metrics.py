#!/usr/bin/env python3
"""Candidate goal metrics, computed on every graded clip, scored against the owner's verdicts.

Research script (2026-09-26). Imports neither tool. Reads the clips under benchmarks/runs/<date>/
(mp4 or PNG frame folders), computes per-clip numbers that are meant to see what the owner grades
(crossfade / pan-only / hallucination / transformation), and writes:
  <out>/metrics.json   one row per clip
  <out>/labels.json    the verdict label per clip (from the picks files and the sheets, hand-coded below)
  <out>/scores.md      per metric: AUC for each label separation + the per-clip table

Metrics (all on a gray proxy of long edge PROXY px; endpoints = the clip's first and last frame):
  contrast_floor   min over interior frames of median patch std / lerp(median patch std A, B).
                   A blend of uncorrelated content loses local contrast; a partition or an aligned
                   morph keeps it.
  laplace_floor    same with the variance of the Laplacian (sharpness).
  feat_floor       SIFT: min over interior frames of (matches to A / nA + matches to B / nB).
                   Detail preservation: every frame must still carry features of A or of B.
  feat_mid         the same sum at the middle frame.
  motion_share     mean over frame pairs of (|diff| - |diff after DIS warp|) / |diff|:
                   the share of the frame change that motion explains (a crossfade: ~0).
  flow_px          mean DIS flow magnitude per frame pair (proxy px).
  local_share      mean over pairs of mean|flow - fitted similarity| / mean|flow|:
                   non-rigid (content) motion vs a global pan/zoom.
  local_px         mean residual flow magnitude after the fitted similarity (proxy px).
  dissolve_fit     mean over frame pairs of the R^2 of the fit  (I[t+1] - I[t]) ~ beta * (B - A):
                   the share of the frame change that a plain crossfade explains (a dissolve: ~1;
                   Track C 2026-09-26, the "dissolve-explained fraction").
"""
import argparse
import glob
import json
import os
import sys

import cv2
import numpy as np

PROXY = 640
MAX_FRAMES = 31
PATCH = 24
NFEAT = 1500


def load_clip(d):
    mp4 = os.path.join(d, "transition.mp4")
    if not os.path.exists(mp4):
        m = sorted(glob.glob(os.path.join(d, "*.mp4")))
        mp4 = m[0] if m else None
    frames = []
    if mp4:
        cap = cv2.VideoCapture(mp4)
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if n <= 1:
            cap.release()
            return None
        idx = np.unique(np.round(np.linspace(0, n - 1, min(n, MAX_FRAMES))).astype(int))
        want = set(idx.tolist())
        i = 0
        while True:
            ok, f = cap.read()
            if not ok:
                break
            if i in want:
                frames.append(f)
            i += 1
        cap.release()
    else:
        pngs = sorted(glob.glob(os.path.join(d, "f*.png")))
        if len(pngs) <= 1:
            return None
        idx = np.unique(np.round(np.linspace(0, len(pngs) - 1, min(len(pngs), MAX_FRAMES))).astype(int))
        frames = [cv2.imread(pngs[i]) for i in idx]
    if len(frames) < 3:
        return None
    h, w = frames[0].shape[:2]
    s = min(1.0, PROXY / max(h, w))
    if s < 1.0:
        frames = [cv2.resize(f, (int(round(w * s)), int(round(h * s))), interpolation=cv2.INTER_AREA)
                  for f in frames]
    return frames


def gray(f):
    return cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)


def patch_std_median(g):
    g = g.astype(np.float32)
    h, w = g.shape
    hh, ww = h // PATCH * PATCH, w // PATCH * PATCH
    p = g[:hh, :ww].reshape(hh // PATCH, PATCH, ww // PATCH, PATCH).transpose(0, 2, 1, 3)
    return float(np.median(p.std(axis=(2, 3))))


def laplace_var(g):
    return float(cv2.Laplacian(g, cv2.CV_32F).var())


def sift_desc(g, sift):
    kp, des = sift.detectAndCompute(g, None)
    return des


def match_count(des_q, des_t, bf):
    if des_q is None or des_t is None or len(des_q) < 2 or len(des_t) < 2:
        return 0
    m = bf.knnMatch(des_q, des_t, k=2)
    good = 0
    for pair in m:
        if len(pair) == 2 and pair[0].distance < 0.75 * pair[1].distance:
            good += 1
    return good


def flow_terms(ga, gb, dis):
    f = dis.calc(ga, gb, None)
    h, w = ga.shape
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    wb = cv2.remap(gb, gx + f[..., 0], gy + f[..., 1], cv2.INTER_LINEAR)
    d = float(np.abs(gb.astype(np.float32) - ga.astype(np.float32)).mean())
    r = float(np.abs(wb.astype(np.float32) - ga.astype(np.float32)).mean())
    mag = np.linalg.norm(f, axis=2)
    step = 8
    ys, xs = np.mgrid[0:h:step, 0:w:step]
    src = np.stack([xs.ravel(), ys.ravel()], axis=1).astype(np.float32)
    dst = src + f[ys, xs].reshape(-1, 2)
    M, _ = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=1.0)
    if M is None:
        resid = mag
    else:
        gx2 = M[0, 0] * gx + M[0, 1] * gy + M[0, 2]
        gy2 = M[1, 0] * gx + M[1, 1] * gy + M[1, 2]
        resid = np.linalg.norm(np.stack([gx2 - gx - f[..., 0], gy2 - gy - f[..., 1]], axis=2), axis=2)
    return d, r, float(mag.mean()), float(resid.mean())


def measure(frames):
    gs = [gray(f) for f in frames]
    A, B = gs[0], gs[-1]
    n = len(gs)
    sift = cv2.SIFT_create(nfeatures=NFEAT)
    bf = cv2.BFMatcher(cv2.NORM_L2)
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    dA, dB = sift_desc(A, sift), sift_desc(B, sift)
    nA = len(dA) if dA is not None else 0
    nB = len(dB) if dB is not None else 0
    psA, psB = patch_std_median(A), patch_std_median(B)
    lvA, lvB = laplace_var(A), laplace_var(B)
    contrast, lap, feat = [], [], []
    for i in range(1, n - 1):
        u = i / (n - 1)
        g = gs[i]
        contrast.append(patch_std_median(g) / max(1e-6, (1 - u) * psA + u * psB))
        lap.append(laplace_var(g) / max(1e-6, (1 - u) * lvA + u * lvB))
        d = sift_desc(g, sift)
        sa = match_count(d, dA, bf) / max(1, nA)
        sb = match_count(d, dB, bf) / max(1, nB)
        feat.append(sa + sb)
    ms, fl, ls, lp, df = [], [], [], [], []
    e = (B.astype(np.float32) - A.astype(np.float32)).ravel()
    ee = float(np.dot(e, e)) + 1e-6
    for a, b in zip(gs[:-1], gs[1:]):
        dd = (b.astype(np.float32) - a.astype(np.float32)).ravel()
        beta = float(np.dot(dd, e)) / ee
        num = float(np.dot(dd - beta * e, dd - beta * e))
        den = float(np.dot(dd, dd)) + 1e-6
        df.append(1.0 - num / den)
        d, r, mag, resid = flow_terms(a, b, dis)
        ms.append((d - r) / max(d, 1e-6))
        fl.append(mag)
        ls.append(resid / max(mag, 1e-6))
        lp.append(resid)
    mid = (n - 2) // 2
    return {
        "n_sampled": n, "nA": nA, "nB": nB,
        "contrast_floor": round(float(min(contrast)), 4),
        "contrast_mid": round(float(contrast[mid]), 4),
        "laplace_floor": round(float(min(lap)), 4),
        "feat_floor": round(float(min(feat)), 4),
        "feat_mid": round(float(feat[mid]), 4),
        "feat_curve": [round(float(x), 3) for x in feat],
        "motion_share": round(float(np.mean(ms)), 4),
        "flow_px": round(float(np.mean(fl)), 3),
        "local_share": round(float(np.mean(ls)), 4),
        "local_px": round(float(np.mean(lp)), 3),
        "dissolve_fit": round(float(np.mean(df)), 4),
    }


# ---- the verdict labels (hand-coded from the picks files and the sheets; verbatim sources named)
# XFADE  = the owner called it a crossfade / fade in-out / dumb crossfade
# PAN    = the owner called it an unnecessary pan / cheap effect with no transformation (a subset of XFADE)
# HALLUC = the owner called it hallucinated / neural slop / animated then cut
# POS    = the owner's closest-to-intent pick or "makes sense" / "promising" / "more natural"
# NEG    = rejected for another reason (slide first, wobbly, cloth artefacts, disintegrates)
# none   = not graded individually


def label_of(run, pair, tag):
    mism = pair.startswith("mismatch") and pair != "mismatch_7"
    if run == "2026-09-13" or run == "2026-09-14":
        # picks_1-14-10-2026.json; the 2026-09-15 review says the same grading applies to 2026-09-14
        if tag.startswith("dissolve"):
            return "XFADE"
        if mism or pair == "mismatch_7":
            return "XFADE"
        if pair == "match_1":
            return "POS" if tag in ("morph_1s", "flow-dissolve_1s", "snap-morph_1s") else "none"
        if pair == "match_2":
            return "NEG"
        if pair == "match_3":
            return "NEG"
        if pair in ("match_4", "match_5"):
            return "POS"
        return "none"
    if run == "2026-09-14/roma":
        # roma_picks.json 2026-09-15
        if pair == "match_3":
            return "POS"
        if pair in ("match_4", "match_5"):
            return "XFADE"       # "prev image on it simply fades out and new one fades in"
        if pair == "mismatch_7":
            return "NEG"         # "cheap 3d cloth effect"
        if pair == "match_2":
            return "NEG"
        return "none"            # match_1 "same"
    if run == "2026-09-15/tr14":
        # tr14_picks.json
        base = tag.rsplit("_", 1)[0]
        if pair == "match_4":
            if base == "dis":
                return "POS"
            if base in ("hold", "hold-dis", "roma", "roma-x-cert"):
                return "XFADE"
            if base.startswith("melt"):
                return "NEG"
            return "none"        # luma / edge-grow: "a bit luma looks promising" (partial)
        if pair == "match_5":
            if base == "hold-dis":
                return "POS"
            if base in ("hold", "roma", "roma-x-cert"):
                return "XFADE"
            if base.startswith("melt"):
                return "NEG"
            return "none"
        if pair == "match_3":
            if base == "roma":
                return "POS"
            if base.startswith("melt"):
                return "NEG"
            return "XFADE"       # "other approaches still just fade out - fade in of a person"
        if pair == "mismatch_7":
            if base in ("hold", "hold-dis"):
                return "NEG"     # "nice attempt … too chaotic"
            return "XFADE"       # "simple crossfades with additional motion or too noisy"
        return "none"
    if run == "2026-09-15/gen":
        if tag.startswith("skeleton"):
            return "XFADE"       # "skeletons, which are again dumb crossfades"
        if tag in ("small",):
            return "none"
        return "HALLUC"
    if run == "2026-09-15/ltx":
        if "skeleton" in tag:
            return "XFADE"
        return "HALLUC"          # "animated … individual images but transition … a cut or dumb fade"
    if run == "2026-09-15/depth":
        return "PAN"             # liked as an effect on the images; "transitions still mostly simple crossfades"
    if run == "2026-09-23":
        # picks.json 2026-09-25
        if mism:
            return "PAN"         # "unnecessary pans and basically cross fading"
        if tag == "morph_2s":
            return "POS" if pair in ("match_1", "match_2", "match_4", "match_5") else "none"
        if tag.endswith("_B"):
            return "PAN"
        return "none"
    if run == "2026-09-23/matched":
        return "none"            # no picks exported for the push-in page
    return "none"


def inventory(root):
    rows = []
    runs = {
        "2026-09-13": "benchmarks/runs/2026-09-13",
        "2026-09-14": "benchmarks/runs/2026-09-14",
        "2026-09-14/roma": "benchmarks/runs/2026-09-14/roma",
        "2026-09-15/tr14": "benchmarks/runs/2026-09-15/tr14",
        "2026-09-15/gen": "benchmarks/runs/2026-09-15/gen",
        "2026-09-15/depth": "benchmarks/runs/2026-09-15/depth",
        "2026-09-23": "benchmarks/runs/2026-09-23",
        "2026-09-23/matched": "benchmarks/runs/2026-09-23/matched",
    }
    for run, rel in runs.items():
        base = os.path.join(root, rel)
        if not os.path.isdir(base):
            continue
        for pair in sorted(os.listdir(base)):
            pd = os.path.join(base, pair)
            if not os.path.isdir(pd) or pair in ("roma", "matched"):
                continue
            for tag in sorted(os.listdir(pd)):
                td = os.path.join(pd, tag)
                if not os.path.isdir(td) or tag.startswith("reveal_"):
                    continue
                has = os.path.exists(os.path.join(td, "transition.mp4")) or glob.glob(os.path.join(td, "f*.png"))
                if has:
                    rows.append({"run": run, "pair": pair, "tag": tag, "dir": td,
                                 "label": label_of(run, pair, tag)})
    ltx = os.path.join(root, "benchmarks/runs/2026-09-15/ltx")
    if os.path.isdir(ltx):
        for mp4 in sorted(glob.glob(os.path.join(ltx, "*.mp4"))):
            tag = os.path.basename(mp4)[:-4]
            pair = "_".join(tag.split("_")[:2])
            rows.append({"run": "2026-09-15/ltx", "pair": pair, "tag": tag, "dir": mp4,
                         "label": label_of("2026-09-15/ltx", pair, tag)})
    return rows


def auc(pos, neg):
    """Probability that a positive scores above a negative (ties count half)."""
    if not pos or not neg:
        return None
    pos, neg = np.asarray(pos, float), np.asarray(neg, float)
    gt = (pos[:, None] > neg[None, :]).sum()
    eq = (pos[:, None] == neg[None, :]).sum()
    return float((gt + 0.5 * eq) / (len(pos) * len(neg)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="", help="substring filter on run/pair/tag")
    ap.add_argument("--score-only", action="store_true", help="re-score an existing metrics.json")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    mpath = os.path.join(a.out, "metrics.json")
    if a.score_only and os.path.exists(mpath):
        rows = json.load(open(mpath))
    else:
        rows = inventory(a.root)
        if a.only:
            rows = [r for r in rows if a.only in f"{r['run']}/{r['pair']}/{r['tag']}"]
        done = {}
        if os.path.exists(mpath):
            for r in json.load(open(mpath)):
                done[r["dir"]] = r
        out = []
        for i, r in enumerate(rows):
            if r["dir"] in done and "metrics" in done[r["dir"]]:
                r["metrics"] = done[r["dir"]]["metrics"]
                out.append(r)
                continue
            src = r["dir"] if os.path.isdir(r["dir"]) else os.path.dirname(r["dir"])
            frames = load_clip(r["dir"]) if os.path.isdir(r["dir"]) else load_clip_mp4(r["dir"])
            if frames is None:
                r["metrics"] = None
            else:
                r["metrics"] = measure(frames)
            out.append(r)
            print(f"[{i + 1}/{len(rows)}] {r['run']}/{r['pair']}/{r['tag']} {r['label']} "
                  f"{json.dumps({k: v for k, v in (r['metrics'] or {}).items() if k != 'feat_curve'})}",
                  flush=True)
            json.dump(out, open(mpath, "w"), indent=1)
        rows = out
    # labels
    json.dump({f"{r['run']}/{r['pair']}/{r['tag']}": r["label"] for r in rows},
              open(os.path.join(a.out, "labels.json"), "w"), indent=1)
    # scores
    # the shipped basket's numbers, from report.json where a clip has one, for the same separations
    for r in rows:
        if not r.get("metrics"):
            continue
        rp = os.path.join(r["dir"], "report.json") if os.path.isdir(r["dir"]) else ""
        q = {}
        if rp and os.path.exists(rp):
            try:
                j = json.load(open(rp))
                q = j.get("quality") or j.get("assess") or j
            except Exception:
                q = {}
        fl = q.get("flicker") or {}
        r["metrics"]["old_warping_error"] = float(q.get("warping_error", float("nan")))
        r["metrics"]["old_flicker_mean"] = float(fl.get("mean", float("nan")))
        r["metrics"]["old_edge_ratio"] = float(fl.get("edge_ratio", float("nan")))
    keys = ["contrast_floor", "contrast_mid", "laplace_floor", "feat_floor", "feat_mid",
            "motion_share", "flow_px", "local_share", "local_px", "dissolve_fit",
            "old_warping_error", "old_flicker_mean", "old_edge_ratio"]
    seps = [("POS vs XFADE", "POS", ("XFADE",)), ("POS vs PAN", "POS", ("PAN",)),
            ("POS vs XFADE+PAN", "POS", ("XFADE", "PAN")),
            ("not-HALLUC vs HALLUC", None, ("HALLUC",))]
    lines = ["# Candidate metrics against the owner's verdicts", "",
             f"Clips measured: {sum(1 for r in rows if r.get('metrics'))} of {len(rows)}; labels: "
             + ", ".join(f"{l} {sum(1 for r in rows if r['label'] == l)}"
                         for l in ("POS", "XFADE", "PAN", "HALLUC", "NEG", "none")), "",
             "AUC = probability that a clip of the first group scores ABOVE one of the second (0.5 = blind;"
             " a metric meant to be LOWER on the second group wants AUC near 1; near 0 means it separates"
             " in the opposite direction).", "",
             "| metric | " + " | ".join(s[0] for s in seps) + " |", "|---|" + "---|" * len(seps)]
    for k in keys:
        cells = []
        for name, pos_l, neg_ls in seps:
            if pos_l is None:
                pos = [r["metrics"][k] for r in rows if r.get("metrics") and r["label"] not in neg_ls + ("none",)]
            else:
                pos = [r["metrics"][k] for r in rows if r.get("metrics") and r["label"] == pos_l]
            neg = [r["metrics"][k] for r in rows if r.get("metrics") and r["label"] in neg_ls]
            pos = [x for x in pos if x == x]
            neg = [x for x in neg if x == x]
            v = auc(pos, neg)
            cells.append("-" if v is None else f"{v:.2f} (n={len(pos)}/{len(neg)})")
        lines.append(f"| {k} | " + " | ".join(cells) + " |")
    pairs_both = sorted({r["pair"] for r in rows if r.get("metrics") and r["label"] == "POS"}
                        & {r["pair"] for r in rows if r.get("metrics") and r["label"] in ("XFADE", "PAN")})
    lines += ["", "## Within-pair AUC, POS vs XFADE+PAN (the same photo pair on both sides; removes the"
              " related-vs-unrelated confound). Pairs: " + ", ".join(pairs_both), "",
              "| metric | " + " | ".join(pairs_both) + " | mean |", "|---|" + "---|" * (len(pairs_both) + 1)]
    for k in keys:
        cells, vals = [], []
        for pr in pairs_both:
            pos = [r["metrics"][k] for r in rows if r.get("metrics") and r["pair"] == pr and r["label"] == "POS"]
            neg = [r["metrics"][k] for r in rows if r.get("metrics") and r["pair"] == pr and r["label"] in ("XFADE", "PAN")]
            pos = [x for x in pos if x == x]; neg = [x for x in neg if x == x]
            v = auc(pos, neg)
            cells.append("-" if v is None else f"{v:.2f} ({len(pos)}/{len(neg)})")
            if v is not None:
                vals.append(v)
        lines.append(f"| {k} | " + " | ".join(cells) + f" | {np.mean(vals):.2f} |" if vals else f"| {k} | " + " | ".join(cells) + " | - |")
    lines += ["", "## Per-label medians", "", "| label | n | " + " | ".join(keys) + " |",
              "|---|---|" + "---|" * len(keys)]
    for l in ("POS", "XFADE", "PAN", "HALLUC", "NEG", "none"):
        sub = [r["metrics"] for r in rows if r.get("metrics") and r["label"] == l]
        if not sub:
            continue
        lines.append(f"| {l} | {len(sub)} | " + " | ".join(f"{np.nanmedian([m[k] for m in sub]):.3f}" for k in keys) + " |")
    lines += ["", "## Every clip", "", "| run | pair | tag | label | " + " | ".join(keys) + " |",
              "|---|---|---|---|" + "---|" * len(keys)]
    for r in rows:
        m = r.get("metrics")
        if not m:
            lines.append(f"| {r['run']} | {r['pair']} | {r['tag']} | {r['label']} | unreadable |")
            continue
        lines.append(f"| {r['run']} | {r['pair']} | {r['tag']} | {r['label']} | "
                     + " | ".join(f"{m[k]:.3f}" for k in keys) + " |")
    open(os.path.join(a.out, "scores.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines[:40]))


def load_clip_mp4(mp4):
    d = os.path.dirname(mp4)
    tmp = {"mp4": mp4}
    cap = cv2.VideoCapture(mp4)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if n <= 1:
        cap.release()
        return None
    idx = np.unique(np.round(np.linspace(0, n - 1, min(n, MAX_FRAMES))).astype(int))
    want = set(idx.tolist())
    frames, i = [], 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if i in want:
            frames.append(f)
        i += 1
    cap.release()
    if len(frames) < 3:
        return None
    h, w = frames[0].shape[:2]
    s = min(1.0, PROXY / max(h, w))
    if s < 1.0:
        frames = [cv2.resize(f, (int(round(w * s)), int(round(h * s))), interpolation=cv2.INTER_AREA)
                  for f in frames]
    return frames


if __name__ == "__main__":
    sys.exit(main())
