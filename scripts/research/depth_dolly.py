#!/usr/bin/env python3
"""TR10 research: a depth-aware camera move for the unrelated (class B) pairs (research plan E11).

The tool's class B skeleton zooms each photo about its salient center and pans toward the other's
(`panzoom_field`), the same motion at every depth. Here a monocular depth map modulates that
motion: near content moves more than far content (parallax), and near content wins the splat's
collisions (the depth is the importance weight). Everything else is the tool's morph. Not part of
either tool.

  --depth GEN OUT PAIR...     (the SD scratch venv: torch + transformers, no cv2) Depth Anything V2
        Small (`depth-anything/Depth-Anything-V2-Small-hf`, Apache-2.0) on MPS over GEN/<pair>/A.png
        and B.png -> OUT/<pair>/disp_A.npy, disp_B.npy (relative inverse depth, 0 far .. 1 near, at the
        native canvas), disp_A.jpg / disp_B.jpg, depth.json (s per image, model, sizes)
  --render GEN OUT PAIR...    (.venv) six clips per pair, 2 s at 30 fps, morph preset: the tool's
        pan-and-zoom at 10 % and 25 % zoom, the depth-modulated field at the same two zooms, and
        a weight-free control (`ramp`: disparity 0 at the top row, 1 at the bottom) at both zooms;
        OUT/<pair>/<variant>/{transition.mp4, strip.jpg, mid.jpg, report.json}; OUT/depth_dolly.json
  --page OUT PAIR...          (.venv) OUT/index.html with a pick per pair
  --export GEN OUT PAIR...    (.venv) hand the depth field (25 % zoom) to the generative bridge: writes
        GEN/<pair>-depth25/ in gen_bridge.py's pair-dir layout (30 frames, 1 s) so `gen_bridge.py
        --generate / --measure / --page` run on it unchanged

Depth modulation (v0): disp_depth(p) = disp_panzoom(p) * (1 - g/2 + g * d(p)) with d in [0, 1] and
g = 1: the nearest content moves 1.5x, the farthest 0.5x, the mean about 1x. Coverage holes that the
modulation opens at the frame border are measured at the mid frame (the T13 number). 2026-09-15.
"""
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MODEL = "depth-anything/Depth-Anything-V2-Small-hf"
SECONDS = 2.0
ZOOMS = (0.10, 0.25)
GAIN = 1.0
W_FLOOR = 0.2            # importance = W_FLOOR + (1 - W_FLOOR) * disparity


# ---- depth (the SD scratch venv) --------------------------------------------------------

def depth(gen, out, pairs):
    import resource
    import torch
    from PIL import Image
    from transformers import pipeline
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    t0 = time.time()
    pipe = pipeline("depth-estimation", model=MODEL, device=dev)
    load_s = round(time.time() - t0, 1)
    for pid in pairs:
        o = Path(out) / pid
        o.mkdir(parents=True, exist_ok=True)
        rep = {"pair": pid, "model": MODEL, "device": dev, "load_s": load_s, "images": {}}
        for side in ("A", "B"):
            img = Image.open(Path(gen) / pid / f"{side}.png").convert("RGB")
            if dev == "mps":
                torch.mps.synchronize()
            t = time.time()
            res = pipe(img)
            if dev == "mps":
                torch.mps.synchronize()
            wall = round(time.time() - t, 2)
            d = res["predicted_depth"].detach().float().cpu().numpy()
            if d.ndim == 3:
                d = d[0]
            if d.shape != (img.height, img.width):
                d = np.asarray(Image.fromarray(d).resize((img.width, img.height), Image.BILINEAR), np.float32)
            lo, hi = np.percentile(d, 2), np.percentile(d, 98)
            disp = np.clip((d - lo) / max(hi - lo, 1e-6), 0, 1).astype(np.float32)
            np.save(str(o / f"disp_{side}.npy"), disp)
            Image.fromarray((disp * 255).astype(np.uint8)).resize((img.width // 4, img.height // 4)).save(o / f"disp_{side}.jpg", quality=80)
            rep["images"][side] = {"wall_s": wall, "size": [img.width, img.height], "raw_shape": list(d.shape),
                                   "raw_range": [round(float(d.min()), 3), round(float(d.max()), 3)],
                                   "disp_mean": round(float(disp.mean()), 3)}
            print(pid, side, json.dumps(rep["images"][side]), flush=True)
        rep["peak_rss_gb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e9, 2)
        (o / "depth.json").write_text(json.dumps(rep, indent=2))


# ---- render (.venv) -------------------------------------------------------------------------

def encode_clip(T, cv2, frames, path, fps, A, B):
    h, w = frames[0].shape[:2]
    stats = T.StreamStats(len(frames))
    enc = T.FrameEncoder(path, w, h, fps)
    try:
        for i, f in enumerate(frames):
            enc.write(f)
            stats.add(i, f)
        written = enc.close()
    except BaseException:
        enc.abort()
        raise
    ok, buf = cv2.imencode(".jpg", cv2.cvtColor(stats.strip(), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
    Path(path).with_name("strip.jpg").write_bytes(buf.tobytes())
    return written, stats.quality(A, B)


def render(gen, out, pairs):
    import cv2
    sys.path.insert(0, str(ROOT))
    import transitions as T
    OUT = Path(out)
    summary_path = OUT / "depth_dolly.json"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    rd = lambda p: cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2RGB)
    th = T.TCFG["hole_thresh"]
    for pid in pairs:
        A, B = rd(Path(gen) / pid / "A.png"), rd(Path(gen) / pid / "B.png")
        h, w = A.shape[:2]
        dA, dB = np.load(str(OUT / pid / "disp_A.npy")), np.load(str(OUT / pid / "disp_B.npy"))
        cA, cB = T._box_center(T.salient_box(A)), T._box_center(T.salient_box(B))
        rows = summary.setdefault(pid, {"canvas": [w, h], "salient_centers": [list(map(round, cA)), list(map(round, cB))]})
        spec = T.spec_from("morph", seconds=SECONDS)
        n = spec.n_frames()
        for z in ZOOMS:
            pz_AB, fA = T.panzoom_field(h, w, cA, cB, z)
            pz_BA, fB = T.panzoom_field(h, w, cB, cA, z)
            ramp = np.repeat(np.linspace(0, 1, h, dtype=np.float32)[:, None], w, 1)
            for variant in ("panzoom", "depth", "ramp"):
                tag = f"{variant}_z{int(z * 100)}"
                if variant == "panzoom":
                    dAB, dBA = pz_AB, pz_BA
                    wA = np.full((h, w), 0.5, np.float32)
                    wB = wA.copy()
                else:
                    # ramp: a weight-free stand-in for the depth map — disparity 0 at the top row,
                    # 1 at the bottom (a landscape prior; correlates 0.62–0.93 with the model's
                    # disparity on mismatch_1 / mismatch_4, measured 2026-09-23)
                    dA_, dB_ = (dA, dB) if variant == "depth" else (ramp, ramp)
                    dAB = pz_AB * (1 - GAIN / 2 + GAIN * dA_)[..., None]
                    dBA = pz_BA * (1 - GAIN / 2 + GAIN * dB_)[..., None]
                    wA = (W_FLOOR + (1 - W_FLOOR) * dA_).astype(np.float32)
                    wB = (W_FLOOR + (1 - W_FLOOR) * dB_).astype(np.float32)
                corr = {"dAB": dAB.astype(np.float32), "dBA": dBA.astype(np.float32), "wA": wA, "wB": wB,
                        "cls": "B", "method": tag, "diag": {}}
                o = OUT / pid / tag
                o.mkdir(parents=True, exist_ok=True)
                t0 = time.time()
                frames = list(T.iter_frames(A, B, spec, corr))
                render_s = round(time.time() - t0, 2)
                written, q = encode_clip(T, cv2, frames, o / "transition.mp4", spec.fps, A, B)
                cv2.imwrite(str(o / "mid.jpg"), cv2.cvtColor(frames[n // 2], cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
                # coverage at the mid frame: where a side's splat leaves no support (the T13 number)
                _, covA = T.forward_splat(A, corr["dAB"], 0.5, wA)
                _, covB = T.forward_splat(B, corr["dBA"], 0.5, wB)
                holeA, holeB = float((covA < th).mean()), float((covB < th).mean())
                rep = {"pair": pid, "variant": variant, "zoom": z, "gain": GAIN if variant == "depth" else 0.0,
                       "pan_fraction": [round(fA, 2), round(fB, 2)], "n_frames": written, "render_s": render_s,
                       "median_disp_px": round(float(np.median(np.linalg.norm(dAB, axis=2))), 2),
                       "disp_near_px": round(float(np.percentile(np.linalg.norm(dAB, axis=2), 90)), 2),
                       "disp_far_px": round(float(np.percentile(np.linalg.norm(dAB, axis=2), 10)), 2),
                       "hole_mid_A": round(holeA, 4), "hole_mid_B": round(holeB, 4),
                       "quality": q}
                (o / "report.json").write_text(json.dumps(rep, indent=2))
                rows[tag] = {k: rep[k] for k in ("n_frames", "render_s", "median_disp_px", "disp_near_px", "disp_far_px",
                                                 "hole_mid_A", "hole_mid_B", "pan_fraction")}
                rows[tag].update({"warping_error": q["warping_error"], "edge_ratio": q["flicker"]["edge_ratio"],
                                  "step_mean": round(q["flicker"]["mean"] * 255, 3), "step_max": round(q["flicker"]["max"] * 255, 3),
                                  "endpoint": [q["endpoint"]["first_vs_A"], q["endpoint"]["last_vs_B"]]})
                print(pid, tag, json.dumps(rows[tag]), flush=True)
                summary_path.write_text(json.dumps(summary, indent=2))


def export(gen, out, pairs, zoom=0.25):
    """The depth-modulated field as a generative-bridge skeleton (gen_bridge.write_pair_dir)."""
    import cv2
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "scripts" / "research"))
    import transitions as T
    import gen_bridge as GB
    rd = lambda p: cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2RGB)
    for pid in pairs:
        A, B = rd(Path(gen) / pid / "A.png"), rd(Path(gen) / pid / "B.png")
        h, w = A.shape[:2]
        dA, dB = np.load(str(Path(out) / pid / "disp_A.npy")), np.load(str(Path(out) / pid / "disp_B.npy"))
        cA, cB = T._box_center(T.salient_box(A)), T._box_center(T.salient_box(B))
        pz_AB, fA = T.panzoom_field(h, w, cA, cB, zoom)
        pz_BA, fB = T.panzoom_field(h, w, cB, cA, zoom)
        corr = {"dAB": (pz_AB * (1 - GAIN / 2 + GAIN * dA)[..., None]).astype(np.float32),
                "dBA": (pz_BA * (1 - GAIN / 2 + GAIN * dB)[..., None]).astype(np.float32),
                "wA": (W_FLOOR + (1 - W_FLOOR) * dA).astype(np.float32),
                "wB": (W_FLOOR + (1 - W_FLOOR) * dB).astype(np.float32),
                "cls": "B", "method": f"depth-panzoom z{int(zoom * 100)}", "diag": {"pan_fraction": [round(fA, 2), round(fB, 2)]}}
        tag = f"{pid}-depth{int(zoom * 100)}"
        meta = {"pair": tag, "canvas": [w, h], "class": "B", "method": corr["method"], **corr["diag"],
                "prompt": GB.PROMPTS.get(pid, ""), "skeleton": corr["method"], "mask_frac": 1.0,
                "depth_model": MODEL, "gain": GAIN}
        GB.write_pair_dir(Path(gen), tag, A, B, corr, np.full((h, w), 255, np.uint8), meta)


# ---- page (.venv) ------------------------------------------------------------------------

def page(out, pairs):
    sys.path.insert(0, str(ROOT / "scripts"))
    from bench_transitions import label_strip
    OUT = Path(out)
    summary = json.loads((OUT / "depth_dolly.json").read_text())
    rel = lambda p: os.path.relpath(p, OUT)
    html = ["<!doctype html><meta charset=utf-8><title>TR10 — depth camera move</title>",
            "<style>body{font:14px system-ui;margin:16px;background:#111;color:#ddd;max-width:1750px}h2{margin-top:40px;border-top:1px solid #333;padding-top:16px}"
            ".top{display:flex;gap:12px;align-items:flex-start;margin:8px 0}.top img{height:200px}"
            ".row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:10px 0 18px;padding:8px;background:#181818;border-radius:6px}"
            ".cell video{width:100%;max-height:560px;background:#000}.cell img{max-width:100%;display:block;margin-top:6px}"
            "code{color:#9cf}.pick label{margin-right:12px}textarea{width:100%;max-width:900px;background:#222;color:#ddd;border:1px solid #444}button{padding:6px 12px}"
            ".note{color:#bbb}.hint{background:#26210a;padding:10px;border-radius:6px;margin:12px 0}"
            "table.num{border-collapse:collapse;font-size:13px}table.num td,table.num th{border:1px solid #333;padding:3px 8px;text-align:right}table.num th:first-child,table.num td:first-child{text-align:left}</style>",
            "<h1>TR10 — a depth-aware camera move for unrelated pairs (2026-09-15)</h1>",
            "<div class=hint><b>What varies: the zoom (10 % = the tool today, 25 %) and whether a depth map shapes the motion.</b> "
            "<code>panzoom</code> is the tool's class B skeleton: each photo zooms about its salient center and pans toward the other's, "
            "the same motion at every depth. <code>depth</code> multiplies that motion by the photo's own depth (Depth Anything V2 Small): "
            "the nearest content moves 1.5×, the farthest 0.5×, and near content wins where the warp overlaps. <code>ramp</code> is the "
            "same modulation with no model at all: disparity 0 at the top row and 1 at the bottom (a landscape prior). Every clip is the "
            "<code>morph</code> preset, 2 s, native canvas. Numbers: hole = the share of the canvas a side leaves uncovered at the "
            "mid frame (the tool fills it by stretching); the rest is the tool's basket. Pick the clip closest to what you want per pair, "
            "tick <b>acceptable as-is</b> only if it is, say what is wrong, then <b>Export picks</b> (depth_dolly_picks.json).</div>",
            "<p><button onclick='exportPicks()'>Export picks</button> <span id=status class=note></span></p>"]
    for pid in pairs:
        s = summary.get(pid, {})
        d = OUT / pid
        keys = [k for k in s if isinstance(s[k], dict) and "n_frames" in s[k]]
        html.append(f"<h2 id='{pid}'>{pid} <small>canvas {s.get('canvas')} · salient centers {s.get('salient_centers')}</small></h2>")
        html.append(f"<div class=top><img src='{rel(d / 'disp_A.jpg')}' title='A depth (bright = near)'><img src='{rel(d / 'disp_B.jpg')}' title='B depth'></div>")
        html.append("<table class=num><tr><th>clip</th><th>disp median / far / near px</th><th>pan fraction</th><th>hole mid A / B</th>"
                    "<th>step mean / max</th><th>warping error</th><th>edge_ratio</th><th>endpoints</th><th>render s</th></tr>")
        for k in keys:
            r = s[k]
            html.append(f"<tr><td><code>{k}</code></td><td>{r['median_disp_px']} / {r['disp_far_px']} / {r['disp_near_px']}</td><td>{r['pan_fraction']}</td>"
                        f"<td>{r['hole_mid_A']} / {r['hole_mid_B']}</td><td>{r['step_mean']} / {r['step_max']}</td><td>{r['warping_error']}</td>"
                        f"<td>{r['edge_ratio']}</td><td>{r['endpoint'][0]} / {r['endpoint'][1]}</td><td>{r['render_s']}</td></tr>")
        html.append("</table>")
        html.append(f"<div class=pick><b>Closest to what you want:</b> " + " ".join(
            f"<label><input type=radio name='pick_{pid}' value='{k}' onchange='save()'> {k}</label>" for k in keys)
            + f" <label><input type=radio name='pick_{pid}' value='none' onchange='save()'> none</label>"
            + f" &nbsp; <label><input type=checkbox id='ok_{pid}' onchange='save()'> <b>acceptable as-is</b></label></div>")
        html.append(f"<textarea id='note_{pid}' rows=2 placeholder='does the move read as a camera going through the scene? where does it tear?' oninput='save()'></textarea>")
        cells = []
        for k in keys:
            r = s[k]
            o = d / k
            if (o / "strip.jpg").exists() and not (o / "strip_labeled.jpg").exists():
                label_strip(o / "strip.jpg", o / "strip_labeled.jpg", r["n_frames"], SECONDS)
            cells.append(f"<div class=cell><code>{k}</code> · hole {r['hole_mid_A']} / {r['hole_mid_B']} · step {r['step_mean']} / {r['step_max']} · "
                         f"warping {r['warping_error']} · edge_ratio {r['edge_ratio']}"
                         f"<br><video src='{rel(o / 'transition.mp4')}' controls loop muted playsinline preload=metadata></video>"
                         f"<img src='{rel(o / 'strip_labeled.jpg')}'></div>")
        for i in range(0, len(cells), 2):
            html.append("<div class=row>" + "".join(cells[i:i + 2]) + "</div>")
    html.append("""<script>
const KEY='depth_dolly_picks:'+location.pathname;
function collect(){const p={};document.querySelectorAll('h2[id]').forEach(h=>{const id=h.id;const r=document.querySelector(`input[name='pick_${id}']:checked`);
 const n=document.getElementById('note_'+id);const ok=document.getElementById('ok_'+id);
 if((r&&r.value)||(n&&n.value)||(ok&&ok.checked))p[id]={pick:r?r.value:'',acceptable_as_is:!!(ok&&ok.checked),note:n?n.value:''};});return p;}
function save(){try{localStorage.setItem(KEY,JSON.stringify(collect()));document.getElementById('status').textContent='saved locally '+new Date().toLocaleTimeString();}catch(e){}}
function restore(){try{const p=JSON.parse(localStorage.getItem(KEY)||'{}');for(const id in p){const r=document.querySelector(`input[name='pick_${id}'][value='${p[id].pick}']`);if(r)r.checked=true;
 const n=document.getElementById('note_'+id);if(n&&p[id].note)n.value=p[id].note;const ok=document.getElementById('ok_'+id);if(ok)ok.checked=!!p[id].acceptable_as_is;}}catch(e){}}
function exportPicks(){const blob=new Blob([JSON.stringify({date:new Date().toISOString(),page:'depth_dolly',picks:collect()},null,2)],{type:'application/json'});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='depth_dolly_picks.json';a.click();document.getElementById('status').textContent='depth_dolly_picks.json downloaded';}
restore();
</script>""")
    (OUT / "index.html").write_text("\n".join(html))
    print(f"wrote {OUT / 'index.html'}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) > 3 and a[0] == "--depth":
        depth(a[1], a[2], a[3:])
    elif len(a) > 3 and a[0] == "--render":
        render(a[1], a[2], a[3:])
    elif len(a) > 2 and a[0] == "--page":
        page(a[1], a[2:])
    elif len(a) > 3 and a[0] == "--export":
        export(a[1], a[2], a[3:])
    else:
        sys.exit(__doc__)
