#!/usr/bin/env python3
"""Benchmark sheet over the fixture catalogue (slice TR2 / H2).

Pairs are found in fixtures/ by name: <group>_<N>_S.<ext> (start, BEFORE) and
<group>_<N>_F.<ext> (finish, AFTER); groups are "match" and "mismatch". For every
pair it runs `transitions.py pair` per preset and length, and optionally
`reveal.py align` (reshot, then loose when reshot refuses a matched pair), then
writes sheet.json, sheet.md and index.html (thumbnails + strips) into --out.

Run: .venv/bin/python scripts/bench_transitions.py --out benchmarks/runs/<date> [--reveal]
     [--presets morph,flow-dissolve,snap-morph,dissolve] [--seconds 1.0] [--long-preset morph --long-seconds 3.0]
     [--max-long 1920] [--only match_1,mismatch_2]
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
PAT = re.compile(r"^(match|mismatch)_(\d+)_([SF])\.(jpe?g|png|heic|heif|hif|dng|arw|tiff?|webp)$", re.I)


def find_pairs(fixtures):
    found = {}
    for p in sorted(fixtures.iterdir()):
        m = PAT.match(p.name)
        if not m:
            continue
        key = f"{m.group(1).lower()}_{int(m.group(2))}"
        found.setdefault(key, {})[m.group(3).upper()] = p
    pairs = []
    for key, d in found.items():
        if "S" in d and "F" in d:
            pairs.append((key, d["S"], d["F"]))
        else:
            print(f"  ! {key}: missing {'S' if 'S' not in d else 'F'} half, skipped")
    return sorted(pairs, key=lambda t: (t[0].split("_")[0], int(t[0].split("_")[1])))


def run(cmd, timeout=1800):
    t = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr, round(time.time() - t, 1)


def load_json(p):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return {}


def thumb(path, height=180):
    sys.path.insert(0, str(ROOT))
    import transitions as T
    img = T.load_image_rgb(path)
    h, w = img.shape[:2]
    out = cv2.resize(img, (max(2, int(w * height / h)), height), interpolation=cv2.INTER_AREA)
    return out, (w, h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--fixtures", default=str(ROOT / "fixtures"))
    ap.add_argument("--presets", default="morph,flow-dissolve,snap-morph,dissolve")
    ap.add_argument("--seconds", type=float, default=1.0)
    ap.add_argument("--long-preset", default="morph")
    ap.add_argument("--long-seconds", type=float, default=3.0)
    ap.add_argument("--max-long", type=int, default=1920)
    ap.add_argument("--reveal", action="store_true", help="also run reveal.py align")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    pairs = find_pairs(Path(a.fixtures))
    if a.only:
        keep = set(a.only.split(","))
        pairs = [p for p in pairs if p[0] in keep]
    print(f"{len(pairs)} pairs")
    runs = {"date": time.strftime("%Y-%m-%d %H:%M"), "max_long": a.max_long, "pairs": []}
    for key, S, F in pairs:
        row = {"id": key, "before": S.name, "after": F.name, "reveal": {}, "transitions": {}}
        try:
            tS, szS = thumb(S); tF, szF = thumb(F)
            row["size_before"], row["size_after"] = list(szS), list(szF)
            (out / key).mkdir(exist_ok=True)
            cv2.imwrite(str(out / key / "thumb_S.jpg"), cv2.cvtColor(tS, cv2.COLOR_RGB2BGR))
            cv2.imwrite(str(out / key / "thumb_F.jpg"), cv2.cvtColor(tF, cv2.COLOR_RGB2BGR))
        except Exception as e:
            row["decode_error"] = str(e)
        if a.reveal:
            for mode in ("reshot", "loose"):
                d = out / key / f"reveal_{mode}"
                rc, so, se, wall = run([PY, str(ROOT / "reveal.py"), "align", str(S), str(F),
                                        "--out", str(d), "--mode", mode])
                st = load_json(d / "metrics.json")
                m = st.get("metrics", {})
                row["reveal"][mode] = {"rc": rc, "wall_s": wall, "state": st.get("state"),
                                       "error": (st.get("error") or se.strip().splitlines()[-1:] or [""])[0] if rc else None,
                                       **{k: m.get(k) for k in ("method", "inliers", "rmse_px", "ecc_rho",
                                                                  "peripheral_ssim", "residual", "changed_pct",
                                                                  "passed", "confidence")}}
                print(f"  {key} reveal/{mode}: rc={rc} {m.get('method')} inl={m.get('inliers')} "
                      f"rmse={m.get('rmse_px')} conf={m.get('confidence')} {wall}s")
                if rc == 0 or not key.startswith("match"):
                    break
        jobs = [(p, a.seconds) for p in a.presets.split(",") if p]
        if a.long_preset:
            jobs.append((a.long_preset, a.long_seconds))
        for preset, sec in jobs:
            tag = f"{preset}_{sec:g}s"
            d = out / key / tag
            rc, so, se, wall = run([PY, str(ROOT / "transitions.py"), "pair", str(S), str(F),
                                    "--out", str(d), "--preset", preset, "--seconds", str(sec),
                                    "--max-long", str(a.max_long)])
            rep = load_json(d / "report.json")
            q = rep.get("quality", {})
            row["transitions"][tag] = {
                "rc": rc, "wall_s": wall, "error": se.strip().splitlines()[-1] if rc and se.strip() else None,
                "class": rep.get("class"), "method": rep.get("method"),
                "sparse_inliers": rep.get("sparse_inliers"), "median_disp_px": rep.get("median_disp_px"),
                "mean_certainty": rep.get("mean_certainty"), "canvas": rep.get("canvas"),
                "n_frames": rep.get("n_frames"), "correspondence_s": rep.get("correspondence_s"),
                "render_s": rep.get("render_s"), "total_s": rep.get("total_s"),
                "warping_error": q.get("warping_error"),
                "edge_ratio": q.get("flicker", {}).get("edge_ratio"),
                "max_step": q.get("flicker", {}).get("max"),
                "endpoint": q.get("endpoint"), "strip": str(Path(key) / tag / "strip.jpg"),
                "mp4": str(Path(key) / tag / "transition.mp4")}
            print(f"  {key} {tag}: rc={rc} class={rep.get('class')} {rep.get('method')} "
                  f"inl={rep.get('sparse_inliers')} disp={rep.get('median_disp_px')} "
                  f"edge={q.get('flicker', {}).get('edge_ratio')} we={q.get('warping_error')} "
                  f"render={rep.get('render_s')}s total={wall}s")
        runs["pairs"].append(row)
        (out / "sheet.json").write_text(json.dumps(runs, indent=2))
    write_sheet(out, runs)
    print(f"wrote {out/'sheet.json'}, {out/'sheet.md'}, {out/'index.html'}")


def write_sheet(out, runs):
    md = [f"# Real-pair sheet — {runs['date']} (transitions canvas capped at {runs['max_long']} px)\n"]
    md.append("## Reveal align (native resolution)\n")
    md.append("| pair | mode | rc | method | inliers | rmse_px | ecc_rho | periph_ssim | residual | changed_% | confidence | wall s | error |")
    md.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for row in runs["pairs"]:
        for mode, r in row["reveal"].items():
            md.append(f"| {row['id']} | {mode} | {r['rc']} | {r.get('method')} | {r.get('inliers')} | {r.get('rmse_px')} | "
                      f"{r.get('ecc_rho')} | {r.get('peripheral_ssim')} | {r.get('residual')} | {r.get('changed_pct')} | "
                      f"{r.get('confidence')} | {r['wall_s']} | {(r.get('error') or '')[:80]} |")
    md.append("\n## Transitions (`transitions.py pair`)\n")
    md.append("| pair | preset | rc | class | method | inliers | median_disp_px | certainty | canvas | frames | corr s | render s | wall s | warping_err | edge_ratio | max_step | endpoint |")
    md.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for row in runs["pairs"]:
        for tag, r in row["transitions"].items():
            cv = "x".join(str(v) for v in (r.get("canvas") or [])) or "-"
            ep = r.get("endpoint") or {}
            md.append(f"| {row['id']} | {tag} | {r['rc']} | {r.get('class')} | {r.get('method')} | {r.get('sparse_inliers')} | "
                      f"{r.get('median_disp_px')} | {r.get('mean_certainty')} | {cv} | {r.get('n_frames')} | {r.get('correspondence_s')} | "
                      f"{r.get('render_s')} | {r['wall_s']} | {r.get('warping_error')} | {r.get('edge_ratio')} | {r.get('max_step')} | "
                      f"{ep.get('first_vs_A')}/{ep.get('last_vs_B')} |")
    (out / "sheet.md").write_text("\n".join(md) + "\n")
    html = ["<!doctype html><meta charset=utf-8><title>Transitions real-pair sheet</title>",
            "<style>body{font:14px system-ui;margin:16px;background:#111;color:#ddd}h2{margin-top:32px}"
            ".pair{display:flex;gap:12px;align-items:flex-start;margin:8px 0}.pair img{height:120px}"
            ".run{margin:6px 0 14px}.run img{max-width:100%;display:block}code{color:#9cf}</style>",
            f"<h1>Real-pair sheet — {runs['date']}</h1><p>Transitions canvas capped at {runs['max_long']} px. Click a strip to open the mp4.</p>"]
    for row in runs["pairs"]:
        html.append(f"<h2>{row['id']} <small>{row['before']} → {row['after']} · {row.get('size_before')} / {row.get('size_after')}</small></h2>")
        html.append(f"<div class=pair><img src='{row['id']}/thumb_S.jpg'><img src='{row['id']}/thumb_F.jpg'></div>")
        for mode, r in row["reveal"].items():
            html.append(f"<div><code>reveal {mode}</code> rc={r['rc']} {r.get('method')} inliers={r.get('inliers')} rmse={r.get('rmse_px')} "
                        f"conf={r.get('confidence')} {r['wall_s']}s {('<b>' + (r.get('error') or '') + '</b>') if r.get('error') else ''}</div>")
        for tag, r in row["transitions"].items():
            html.append(f"<div class=run><code>{tag}</code> class={r.get('class')} {r.get('method')} inliers={r.get('sparse_inliers')} "
                        f"disp={r.get('median_disp_px')}px edge_ratio={r.get('edge_ratio')} warping={r.get('warping_error')} "
                        f"render={r.get('render_s')}s<br><a href='{r['mp4']}'><img src='{r['strip']}'></a></div>")
    (out / "index.html").write_text("\n".join(html))


if __name__ == "__main__":
    main()
