#!/usr/bin/env python3
"""Benchmark sheet over the fixture catalogue (slice TR2 / H2).

Incremental: an existing sheet.json in --out is merged, so `--only mismatch_6` re-runs one pair
and keeps the other rows (each row carries its own run_at).

Pairs are found in fixtures/ by name: <group>_<N>_S.<ext> (start, BEFORE) and
<group>_<N>_F.<ext> (finish, AFTER); groups are "match" and "mismatch". For every
pair it runs `transitions.py pair` per preset and length, and optionally
`reveal.py align` (reshot, then loose when reshot refuses a matched pair), then
writes sheet.json, sheet.md and index.html (thumbnails + strips) into --out.

Run: .venv/bin/python scripts/bench_transitions.py --out benchmarks/runs/<date> [--reveal]
     [--presets morph,flow-dissolve,snap-morph,dissolve] [--seconds 1.0] [--long-preset morph --long-seconds 3.0]
     [--max-long 1920] [--only match_1,mismatch_2]
     [--camera flat|ramp|model] [--zoom 0.25] [--class A|B]   passed through to `transitions.py pair`
                              (2026-09-23; the tag gains _<camera>, _z<zoom %> and _<class> suffixes)
     --render-only            rebuild sheet.md / index.html from sheet.json without running anything
     --picks picks.json       merge the owner's picks exported from index.html into the sheet

Review page: each strip is EIGHT FRAMES OF ONE TRANSITION (time-labelled), not eight variants;
the variants are the preset rows. The page plays every variant inline, explains what each preset
changes, and has a radio + note per pair whose "Export picks" button downloads picks.json.
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
TAG = re.compile(r"^(?P<preset>[a-z-]+)_(?P<sec>[\d.]+)s(?:_(?P<camera>flat|ramp|model))?(?:_z(?P<zoom>\d+))?(?:_(?P<cls>[AB]))?$")


def make_tag(preset, sec, camera="flat", zoom=None, force_class=""):
    return (f"{preset}_{sec:g}s" + (f"_{camera}" if camera != "flat" else "")
            + (f"_z{int(round(zoom * 100))}" if zoom is not None else "")
            + (f"_{force_class}" if force_class else ""))


def parse_tag(tag):
    """{preset, sec, camera, zoom, cls} from a run tag (the older `preset_1s` form parses too)."""
    m = TAG.match(tag)
    if not m:
        preset, sec = tag.rsplit("_", 1)
        return {"preset": preset, "sec": float(sec.rstrip("s")), "camera": None, "zoom": None, "cls": ""}
    return {"preset": m["preset"], "sec": float(m["sec"]), "camera": m["camera"],
            "zoom": int(m["zoom"]) / 100 if m["zoom"] else None, "cls": m["cls"] or ""}


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
    ap.add_argument("--render-only", action="store_true")
    ap.add_argument("--picks", default="", help="picks.json exported from index.html")
    ap.add_argument("--camera", default="flat", choices=["flat", "ramp", "model"],
                    help="passed to transitions.py pair (class B camera move)")
    ap.add_argument("--zoom", type=float, default=None, help="passed to transitions.py pair")
    ap.add_argument("--class", dest="force_class", default="", choices=["", "A", "B"],
                    help="passed to transitions.py pair")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    if a.render_only:
        runs = load_json(out / "sheet.json")
        if not runs:
            sys.exit("no sheet.json to render")
        # Rows written before a report key existed pick it up from their report.json on disk.
        for row in runs.get("pairs", []):
            for r in row.get("transitions", {}).values():
                if r.get("mp4") and any(k not in r for k in ("pan_fraction", "camera", "zoom")):
                    rj = load_json(out / Path(r["mp4"]).parent / "report.json")
                    for k in ("pan_fraction", "camera", "zoom", "disparity_mean"):
                        r.setdefault(k, rj.get(k))
        (out / "sheet.json").write_text(json.dumps(runs, indent=2))
        picks = load_json(a.picks) if a.picks else {}
        write_sheet(out, runs, picks)
        print(f"re-rendered {out/'sheet.md'} and {out/'index.html'}")
        return
    pairs = find_pairs(Path(a.fixtures))
    if a.only:
        keep = set(a.only.split(","))
        pairs = [p for p in pairs if p[0] in keep]
    print(f"{len(pairs)} pairs")
    # Merge into an existing sheet: pairs run now replace their earlier row, others are kept, so
    # the catalogue can grow one pair at a time without re-running everything.
    runs = load_json(out / "sheet.json") or {}
    prev_rows = {r.get("id"): r for r in runs.get("pairs", [])}
    runs = {"date": time.strftime("%Y-%m-%d %H:%M"), "max_long": a.max_long,
            "pairs": [r for r in runs.get("pairs", []) if r.get("id") not in {k for k, _, _ in pairs}]}
    for key, S, F in pairs:
        # a pair's earlier tags are kept (2026-09-23: one sheet can hold several camera runs);
        # a tag run again replaces its own entry
        prev = prev_rows.get(key, {})
        row = {"id": key, "before": S.name, "after": F.name, "run_at": time.strftime("%Y-%m-%d %H:%M"),
               "reveal": dict(prev.get("reveal", {})), "transitions": dict(prev.get("transitions", {}))}
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
        extra = (["--camera", a.camera] if a.camera != "flat" else []) \
            + (["--zoom", str(a.zoom)] if a.zoom is not None else []) \
            + (["--class", a.force_class] if a.force_class else [])
        for preset, sec in jobs:
            tag = make_tag(preset, sec, a.camera, a.zoom, a.force_class)
            d = out / key / tag
            rc, so, se, wall = run([PY, str(ROOT / "transitions.py"), "pair", str(S), str(F),
                                    "--out", str(d), "--preset", preset, "--seconds", str(sec),
                                    "--max-long", str(a.max_long)] + extra)
            rep = load_json(d / "report.json")
            q = rep.get("quality", {})
            row["transitions"][tag] = {
                "rc": rc, "wall_s": wall, "error": se.strip().splitlines()[-1] if rc and se.strip() else None,
                "class": rep.get("class"), "method": rep.get("method"),
                "sparse_inliers": rep.get("sparse_inliers"), "median_disp_px": rep.get("median_disp_px"),
                "mean_certainty": rep.get("mean_certainty"), "canvas": rep.get("canvas"),
                "pan_fraction": rep.get("pan_fraction"),
                "camera": rep.get("camera"), "zoom": rep.get("zoom"), "disparity_mean": rep.get("disparity_mean"),
                "n_frames": rep.get("n_frames"), "correspondence_s": rep.get("correspondence_s"),
                "render_s": rep.get("render_s"), "total_s": rep.get("total_s"),
                "warping_error": q.get("warping_error"),
                "edge_ratio": q.get("flicker", {}).get("edge_ratio"),
                "max_step": q.get("flicker", {}).get("max"),
                "endpoint": q.get("endpoint"), "strip": str(Path(key) / tag / "strip.jpg"),
                "mp4": str(Path(key) / tag / "transition.mp4")}
            print(f"  {key} {tag}: rc={rc} class={rep.get('class')} {rep.get('method')} "
                  f"inl={rep.get('sparse_inliers')} disp={rep.get('median_disp_px')} "
                  f"{('camera=' + str(rep.get('camera')) + ' zoom=' + str(rep.get('zoom')) + ' ') if rep.get('camera') else ''}"
                  f"edge={q.get('flicker', {}).get('edge_ratio')} we={q.get('warping_error')} "
                  f"render={rep.get('render_s')}s total={wall}s")
        runs["pairs"].append(row)
        runs["pairs"].sort(key=lambda r: (r["id"].split("_")[0], int(r["id"].split("_")[1])))
        (out / "sheet.json").write_text(json.dumps(runs, indent=2))
    write_sheet(out, runs, load_json(a.picks) if a.picks else {})
    print(f"wrote {out/'sheet.json'}, {out/'sheet.md'}, {out/'index.html'}")


def preset_legend(tags):
    """What differs between the variant rows, from transitions.PRESETS itself."""
    sys.path.insert(0, str(ROOT))
    import transitions as T
    base = T.TransitionSpec()
    rows = []
    for tag in tags:
        p = parse_tag(tag)
        spec = T.spec_from(p["preset"], seconds=p["sec"])
        diff = []
        for f in ("style", "warp_amount", "warp_curve", "mix_curve", "mix_delay", "portal"):
            v, b = getattr(spec, f), getattr(base, f)
            if v != b or f == "style":
                diff.append(f"{f}={v}")
        if p["camera"]:
            diff.append(f"camera={p['camera']}")
        if p["zoom"] is not None:
            diff.append(f"zoom={p['zoom']:g}")
        if p["cls"]:
            diff.append(f"class forced {p['cls']}")
        rows.append((tag, f"{spec.seconds:g} s, {spec.n_frames()} frames; " + ", ".join(diff)))
    return rows


def label_strip(src, dst, n_frames, seconds, k=8):
    """Write frame index and time under each tile of a strip."""
    img = cv2.imread(str(src))
    if img is None:
        return False
    h, w = img.shape[:2]
    band = np.full((38, w, 3), 24, np.uint8)
    idx = np.linspace(0, n_frames - 1, k).round().astype(int)
    tw = w / k
    fs = 0.42 if tw >= 90 else 0.36        # portrait canvases give narrow tiles
    for j, i in enumerate(idx):
        t = i / max(n_frames - 1, 1) * seconds
        x = int(j * tw) + 4
        cv2.putText(band, f"frame {i}", (x, 15), cv2.FONT_HERSHEY_SIMPLEX, fs, (200, 230, 255), 1, cv2.LINE_AA)
        cv2.putText(band, f"{t:.2f} s", (x, 32), cv2.FONT_HERSHEY_SIMPLEX, fs, (200, 230, 255), 1, cv2.LINE_AA)
    cv2.imwrite(str(dst), np.concatenate([img, band], 0), [cv2.IMWRITE_JPEG_QUALITY, 88])
    return True


def write_sheet(out, runs, picks=None):
    picks = (picks or {}).get("picks", {})
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
    md.append("| pair | preset | rc | class | method | inliers | median_disp_px | certainty | pan A/B | camera | zoom | canvas | frames | corr s | render s | wall s | warping_err | edge_ratio | max_step | endpoint |")
    md.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for row in runs["pairs"]:
        for tag, r in row["transitions"].items():
            cv = "x".join(str(v) for v in (r.get("canvas") or [])) or "-"
            ep = r.get("endpoint") or {}
            pan = "/".join(f"{v:.2f}" for v in r["pan_fraction"]) if r.get("pan_fraction") else "-"
            md.append(f"| {row['id']} | {tag} | {r['rc']} | {r.get('class')} | {r.get('method')} | {r.get('sparse_inliers')} | "
                      f"{r.get('median_disp_px')} | {r.get('mean_certainty')} | {pan} | {r.get('camera') or '-'} | {r.get('zoom') if r.get('zoom') is not None else '-'} | {cv} | {r.get('n_frames')} | {r.get('correspondence_s')} | "
                      f"{r.get('render_s')} | {r['wall_s']} | {r.get('warping_error')} | {r.get('edge_ratio')} | {r.get('max_step')} | "
                      f"{ep.get('first_vs_A')}/{ep.get('last_vs_B')} |")
    if picks:
        md.append("\n## Owner picks (from index.html → picks.json)\n")
        md.append("| pair | best variant | note |")
        md.append("|---|---|---|")
        for row in runs["pairs"]:
            pk = picks.get(row["id"]) or {}
            md.append(f"| {row['id']} | {pk.get('best', '')} | {(pk.get('note') or '').replace('|', '/')} |")
    (out / "sheet.md").write_text("\n".join(md) + "\n")

    tags = []
    for row in runs["pairs"]:
        for tag in row["transitions"]:
            if tag not in tags:
                tags.append(tag)
    legend = preset_legend(tags)
    for row in runs["pairs"]:
        for tag, r in row["transitions"].items():
            src = out / r["strip"]
            if src.exists() and r.get("n_frames"):
                sec = parse_tag(tag)["sec"]
                if label_strip(src, src.with_name("strip_labeled.jpg"), r["n_frames"], sec):
                    r["strip_labeled"] = str(Path(r["strip"]).with_name("strip_labeled.jpg"))
    html = ["<!doctype html><meta charset=utf-8><title>Transitions real-pair sheet</title>",
            "<style>body{font:14px system-ui;margin:16px;background:#111;color:#ddd;max-width:1600px}h2{margin-top:40px;border-top:1px solid #333;padding-top:16px}"
            ".pair{display:flex;gap:12px;align-items:flex-start;margin:8px 0}.pair img{height:140px}"
            ".run{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:14px;align-items:start;margin:10px 0 18px;padding:8px;background:#181818;border-radius:6px}"
            ".run img{max-width:100%;display:block}.run video{width:300px;max-height:360px;background:#000}"
            "code{color:#9cf}.legend td{padding:2px 10px;vertical-align:top}.pick{margin:8px 0 0}.pick label{margin-right:14px}"
            "textarea{width:100%;max-width:900px;background:#222;color:#ddd;border:1px solid #444}button{padding:6px 12px}"
            ".note{color:#bbb}.hint{background:#26210a;padding:10px;border-radius:6px;margin:12px 0}</style>",
            f"<h1>Real-pair sheet — {runs['date']}</h1>",
            f"<div class=hint><b>How to read this page.</b> Each pair has {len(tags)} variants, one per row. "
            "The strip under a variant shows <b>eight frames of that one transition</b>, labelled with the frame index and the time; "
            "the player next to it is the full clip (loops; the first and last frames are the two photos byte for byte). "
            f"Transitions canvas capped at {runs['max_long']} px. Pick the best variant per pair, add a note, then <b>Export picks</b> "
            "and drop the file next to sheet.json: <code>scripts/bench_transitions.py --render-only --picks picks.json</code> puts it in the sheet.</div>",
            "<h3>What differs between the variants</h3><table class=legend>"]
    for tag, desc in legend:
        html.append(f"<tr><td><code>{tag}</code></td><td>{desc}</td></tr>")
    html.append("</table><p class=note>style: <b>morph</b> = both photos forward-warped along the dense correspondence and cross-dissolved; "
                "<b>warp-dissolve</b> = same with the warp scaled by warp_amount and the dissolve shifted by mix_delay; <b>dissolve</b> = no geometry, crossfade only. "
                "Curves: <b>ease</b> = slow-fast-slow; <b>hold-then-go</b> = nothing for the first 35 %, then linear; <b>ease-in</b> = starts slow. "
                "class A = a homography plus DIS residual flow was found between the photos; class B = no geometric correspondence: each photo zooms in 10 % about its salient blob and pans toward the other photo's blob as far as the zoom allows without its edge entering the frame (pan = the fraction of that distance each photo travels; since 2026-09-14, before that the whole frame moved by a similarity and its border showed). "
                "certainty = mean forward-backward consistency of the dense field (1 = every pixel agrees both ways). "
                "camera (2026-09-23, class B only): <b>flat</b> = the pan-and-zoom as is; <b>ramp</b> = the same motion scaled by a top-to-bottom disparity ramp (bottom rows move 1.5×, top rows 0.5×), no model; "
                "<b>model</b> = the same scaled by Depth Anything V2 Small's disparity, near content moves more and wins the overlap; zoom = the per-frame zoom fraction (0.10 default).</p>")
    html.append("<p><button onclick='exportPicks()'>Export picks</button> <span id=status class=note></span></p>")
    for row in runs["pairs"]:
        html.append(f"<h2 id='{row['id']}'>{row['id']} <small>{row['before']} → {row['after']} · {row.get('size_before')} / {row.get('size_after')}</small></h2>")
        html.append(f"<div class=pair><img src='{row['id']}/thumb_S.jpg'><img src='{row['id']}/thumb_F.jpg'></div>")
        for mode, r in row["reveal"].items():
            html.append(f"<div><code>reveal {mode}</code> rc={r['rc']} {r.get('method')} inliers={r.get('inliers')} rmse={r.get('rmse_px')} "
                        f"conf={r.get('confidence')} {r['wall_s']}s {('<b>' + (r.get('error') or '') + '</b>') if r.get('error') else ''}</div>")
        pk = picks.get(row["id"]) or {}
        html.append(f"<div class=pick><b>Best variant:</b> " + " ".join(
            f"<label><input type=radio name='pick_{row['id']}' value='{tag}' {'checked' if pk.get('best') == tag else ''} onchange='save()'> {tag}</label>"
            for tag in row["transitions"]) + f" <label><input type=radio name='pick_{row['id']}' value='none' {'checked' if pk.get('best') == 'none' else ''} onchange='save()'> none usable</label></div>")
        html.append(f"<textarea id='note_{row['id']}' rows=2 placeholder='what is wrong / what works' oninput='save()'>{pk.get('note', '')}</textarea>")
        for tag, r in row["transitions"].items():
            strip = r.get("strip_labeled", r["strip"])
            pan = (" pan=" + "/".join(f"{v:.2f}" for v in r["pan_fraction"])) if r.get("pan_fraction") else ""
            cam = (f" camera={r.get('camera')} zoom={r.get('zoom')}" + (f" disparity={r.get('disparity_mean')}" if r.get("disparity_mean") else "")) if r.get("camera") else ""
            html.append(f"<div class=run><div><code>{tag}</code> class={r.get('class')} {r.get('method')} inliers={r.get('sparse_inliers')} "
                        f"disp={r.get('median_disp_px')}px certainty={r.get('mean_certainty')}{pan}{cam} edge_ratio={r.get('edge_ratio')} warping={r.get('warping_error')} "
                        f"render={r.get('render_s')}s<br><img src='{strip}'></div>"
                        f"<video src='{r['mp4']}' controls loop muted playsinline preload=metadata></video></div>")
    html.append("""<script>
const KEY='picks:'+location.pathname;
function collect(){const p={};document.querySelectorAll('h2[id]').forEach(h=>{const id=h.id;const r=document.querySelector(`input[name='pick_${id}']:checked`);
 const n=document.getElementById('note_'+id);if((r&&r.value)||(n&&n.value))p[id]={best:r?r.value:'',note:n?n.value:''};});return p;}
function save(){try{localStorage.setItem(KEY,JSON.stringify(collect()));document.getElementById('status').textContent='saved locally '+new Date().toLocaleTimeString();}catch(e){}}
function restore(){try{const p=JSON.parse(localStorage.getItem(KEY)||'{}');for(const id in p){const r=document.querySelector(`input[name='pick_${id}'][value='${p[id].best}']`);if(r)r.checked=true;
 const n=document.getElementById('note_'+id);if(n&&p[id].note)n.value=p[id].note;}}catch(e){}}
function exportPicks(){const blob=new Blob([JSON.stringify({date:new Date().toISOString(),picks:collect()},null,2)],{type:'application/json'});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='picks.json';a.click();document.getElementById('status').textContent='picks.json downloaded';}
restore();
</script>""")
    (out / "index.html").write_text("\n".join(html))


if __name__ == "__main__":
    main()
