#!/usr/bin/env python3
"""Screen one generated keyframe against its two endpoint photos; print JSON.

Research script (2026-09-27, Track B of that session). numpy + cv2 only; no torch, no network.
It reads files and prints numbers; the owner's eye grades the keyframe, this script does not.

Usage:
  keyframe_screen.py --pair mismatch_4 --keyframe KF.png --before A.png --after B.png
                     [--log kf.log] [--memlog mem_kf.log] [--ref REF.png]

Numbers (A and B are resized to the keyframe's size with INTER_AREA first):
  sun      mismatch_4 only: centroid (x, y, px in the keyframe's frame) of the largest connected
           blob with Lab L > 92 in the top 60 % of the picture, for the keyframe, A and B; the
           rule of layered_probe.py's `sun` mask, with the top 60 % in place of the sky mask.
           Other pairs: null.
  mad      mean absolute difference in 8-bit levels over the three channels, keyframe vs A and
           keyframe vs B; with --ref (2026-09-27 evening) also keyframe vs the reference picture the
           run was given (e.g. the layered composite), resized to the keyframe's size the same way.
  laplace  variance of the Laplacian (ksize 1, CV_32F) of the 8-bit Lab L channel (cv2 uint8 Lab,
           L scaled 0..255) on an INTER_AREA proxy whose long side is 480 px, for the keyframe, A
           and B. On 2026-09-27 this definition gives kf_01 100.4, A 118.4, B 151.2; the 2026-09-26
           figures (kf_01 188, B 254) came from an unrecorded variant and do not compare.
  log      from the wrapper log: wall s (run_end - run_begin), sampling s, per-step s (the
           progress bar's s/it values, one per step), VAE decode s, the "preprocess ref" lines
           verbatim, the "auto-fit" warning if present.
  mem      from the 5 s sampler log (epoch, MemAvailable KiB, gtt_used bytes): MemAvailable
           first / min in GiB and the drop, gtt_used first / max in GB (decimal) and the rise.
"""
import argparse
import json
import re
import statistics

import cv2
import numpy as np

SUN_THR = 92.0
SUN_TOP = 0.60
PROXY_LONG = 480


def read_rgb(path):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"cannot read {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def lab_L(rgb):
    return cv2.cvtColor(rgb.astype(np.float32) / 255.0, cv2.COLOR_RGB2Lab)[..., 0]


def sun_centroid(rgb):
    """Centroid (x, y) of the largest blob with L > 92 in the top 60 % rows; None if no blob."""
    L = lab_L(rgb)
    h = L.shape[0]
    hard = (L > SUN_THR).astype(np.uint8)
    hard[int(round(h * SUN_TOP)):, :] = 0
    n, _, st, cen = cv2.connectedComponentsWithStats(hard)
    if n < 2:
        return None
    i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    return {"x": round(float(cen[i][0]), 1), "y": round(float(cen[i][1]), 1),
            "area_px": int(st[i, cv2.CC_STAT_AREA])}


def laplace_var(rgb):
    h, w = rgb.shape[:2]
    s = PROXY_LONG / max(h, w)
    small = cv2.resize(rgb, (max(1, round(w * s)), max(1, round(h * s))), interpolation=cv2.INTER_AREA)
    L8 = cv2.cvtColor(small, cv2.COLOR_RGB2Lab)[..., 0]
    return round(float(cv2.Laplacian(L8, cv2.CV_32F).var()), 1)


def mad(x, y):
    return round(float(np.abs(x.astype(np.int16) - y.astype(np.int16)).mean()), 2)


def parse_log(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    out = {}
    b = re.search(r"run_begin (\d+)", text)
    e = re.search(r"run_rc=(\d+) run_end (\d+)", text)
    if e:
        out["run_rc"] = int(e.group(1))
    if b and e:
        out["wall_s"] = int(e.group(2)) - int(b.group(1))
    m = re.search(r"sampling completed, taking ([\d.]+)s", text)
    out["sampling_s"] = float(m.group(1)) if m else None
    m = re.search(r"decode_first_stage completed, taking ([\d.]+)s", text)
    out["vae_decode_s"] = float(m.group(1)) if m else None
    m = re.search(r"generate_image completed in ([\d.]+)s", text)
    out["generate_image_s"] = float(m.group(1)) if m else None
    # the sampling bar: "| k/N - X s/it"; keep the last value seen for each step index
    steps = {}
    for k, n, v in re.findall(r"\|\s*(\d+)/(\d+) - ([\d.]+)s/it", text):
        steps[int(k)] = float(v)
    per = [steps[k] for k in sorted(steps)]
    out["per_step_s"] = per
    if per:
        out["per_step_s_min"] = min(per)
        out["per_step_s_median"] = round(statistics.median(per), 2)
        out["per_step_s_max"] = max(per)
        out["steps"] = len(per)
    if out.get("sampling_s") and per:
        out["sampling_s_per_step_mean"] = round(out["sampling_s"] / len(per), 2)
    out["preprocess_ref"] = [ln.strip() for ln in text.splitlines() if "preprocess ref" in ln]
    out["auto_fit_warning"] = [ln.strip() for ln in text.splitlines() if "auto-fit" in ln]
    out["refused"] = "REFUSED" in text
    return out


def parse_mem(path):
    rows = []
    for ln in open(path, encoding="utf-8", errors="replace"):
        p = ln.split()
        if len(p) == 3 and all(x.isdigit() for x in p):
            rows.append((int(p[0]), int(p[1]), int(p[2])))
    if not rows:
        return None
    avail = [r[1] for r in rows]
    gtt = [r[2] for r in rows]
    gib = 1048576.0
    return {"samples": len(rows), "span_s": rows[-1][0] - rows[0][0],
            "memavailable_first_gib": round(avail[0] / gib, 2),
            "memavailable_min_gib": round(min(avail) / gib, 2),
            "memavailable_drop_gib": round((avail[0] - min(avail)) / gib, 2),
            "gtt_used_first_gb": round(gtt[0] / 1e9, 2),
            "gtt_used_max_gb": round(max(gtt) / 1e9, 2),
            "gtt_used_rise_gb": round((max(gtt) - gtt[0]) / 1e9, 2)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pair", required=True)
    ap.add_argument("--keyframe", required=True)
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--log")
    ap.add_argument("--memlog")
    ap.add_argument("--ref", help="optional: the run's reference picture when it is neither A nor B")
    a = ap.parse_args()
    kf = read_rgb(a.keyframe)
    h, w = kf.shape[:2]
    A0, B0 = read_rgb(a.before), read_rgb(a.after)
    A = cv2.resize(A0, (w, h), interpolation=cv2.INTER_AREA)
    B = cv2.resize(B0, (w, h), interpolation=cv2.INTER_AREA)
    res = {"pair": a.pair, "keyframe": a.keyframe, "size_wh": [w, h],
           "before_size_wh": [A0.shape[1], A0.shape[0]], "after_size_wh": [B0.shape[1], B0.shape[0]]}
    if a.pair == "mismatch_4":
        s = {"kf": sun_centroid(kf), "A": sun_centroid(A), "B": sun_centroid(B)}
        if s["A"] and s["B"]:
            mid = ((s["A"]["x"] + s["B"]["x"]) / 2, (s["A"]["y"] + s["B"]["y"]) / 2)
            s["midpoint_AB"] = {"x": round(mid[0], 1), "y": round(mid[1], 1)}
            if s["kf"]:
                for k, ref in (("dist_to_midpoint_px", mid), ("dist_to_A_px", (s["A"]["x"], s["A"]["y"])),
                               ("dist_to_B_px", (s["B"]["x"], s["B"]["y"]))):
                    s[k] = round(float(np.hypot(s["kf"]["x"] - ref[0], s["kf"]["y"] - ref[1])), 1)
        res["sun"] = s
    else:
        res["sun"] = None
    res["mad_levels"] = {"to_A": mad(kf, A), "to_B": mad(kf, B)}
    if a.ref:
        R0 = read_rgb(a.ref)
        res["ref"] = a.ref
        res["ref_size_wh"] = [R0.shape[1], R0.shape[0]]
        res["mad_levels"]["to_ref"] = mad(kf, cv2.resize(R0, (w, h), interpolation=cv2.INTER_AREA))
    res["laplace_var_L"] = {"kf": laplace_var(kf), "A": laplace_var(A0), "B": laplace_var(B0)}
    if a.log:
        res["log"] = parse_log(a.log)
    if a.memlog:
        res["mem"] = parse_mem(a.memlog)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
