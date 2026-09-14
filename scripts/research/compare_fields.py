#!/usr/bin/env python3
"""TR5 research: the DIS field vs the RoMa field on the same canvas (runs in `.venv`).

  --prepare DIR PAIR...        write A.png, B.png (the transitions canvas, --max-long 1920) and the
                               homography+DIS field (dis_dAB/dBA/wA/wB.npy, dis.json) into
                               DIR/pair_<PAIR>/ for scripts/research/roma_probe.py
  --compare DIR OUT PAIR...    after the probe ran on those dirs: render morph 1 s (30 frames) from
                               both fields through transitions.iter_frames and write
                               OUT/<pair>/{dis,roma}_mid.jpg, mid_dis_vs_roma.jpg,
                               strips_dis_vs_roma.jpg and OUT/compare.json (quality basket)
  --render DIR OUT PAIR...     render the four field-using variants (morph 1 s, flow-dissolve 1 s,
                               snap-morph 1 s, morph 3 s) from the RoMa field as real mp4s:
                               OUT/<pair>/<tag>/{transition.mp4,strip.jpg,report.json}
  --page OUT DISRUN PAIR...    write OUT/index.html: per pair and variant the DIS clip from the
                               bench run DISRUN beside the RoMa clip, numbers, labelled strips,
                               a verdict per pair exported as roma_picks.json
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


VARIANTS = (("morph", 1.0), ("flow-dissolve", 1.0), ("snap-morph", 1.0), ("morph", 3.0))


def load_roma(d):
    corr = {k: np.load(str(d / f"roma_{k}.npy")) for k in ("dAB", "dBA", "wA", "wB")}
    corr.update({"cls": "A", "method": "roma", "diag": {}})
    return corr


def render(base, out, pairs):
    """Real mp4s from the RoMa field, the same encoder, basket and strip as transitions.render_pair."""
    for pid in pairs:
        d = Path(base) / f"pair_{pid}"
        A = cv2.cvtColor(cv2.imread(str(d / "A.png")), cv2.COLOR_BGR2RGB)
        B = cv2.cvtColor(cv2.imread(str(d / "B.png")), cv2.COLOR_BGR2RGB)
        h, w = A.shape[:2]
        corr = load_roma(d)
        probe = json.loads((d / "roma.json").read_text()) if (d / "roma.json").exists() else {}
        for preset, sec in VARIANTS:
            tag = f"{preset}_{sec:g}s"
            o = Path(out) / pid / tag
            o.mkdir(parents=True, exist_ok=True)
            spec = T.spec_from(preset, seconds=sec)
            n = spec.n_frames()
            stats = T.StreamStats(n)
            enc = T.FrameEncoder(o / "transition.mp4", w, h, spec.fps)
            t0 = time.time()
            try:
                for i, f in enumerate(T.iter_frames(A, B, spec, corr)):
                    enc.write(f)
                    stats.add(i, f)
                written = enc.close()
            except BaseException:
                enc.abort()
                raise
            render_s = round(time.time() - t0, 2)
            ok, buf = cv2.imencode(".jpg", cv2.cvtColor(stats.strip(), cv2.COLOR_RGB2BGR),
                                   [cv2.IMWRITE_JPEG_QUALITY, 90])
            if ok:
                (o / "strip.jpg").write_bytes(buf.tobytes())
            rep = {"field": "roma", "pair": pid, "tag": tag, "spec": T.asdict(spec), "class": "A",
                   "method": "roma", "canvas": [w, h], "n_frames": written, "render_s": render_s,
                   "roma_cert_mean": round(float(corr["wA"].mean()), 3),
                   "median_disp_px": round(float(np.median(np.linalg.norm(corr["dAB"], axis=2))), 2),
                   "match_s": probe.get("match_s"), "quality": stats.quality(A, B)}
            (o / "report.json").write_text(json.dumps(rep, indent=2))
            q = rep["quality"]
            print(f"  {pid} {tag}: {written} frames, render {render_s}s, edge_ratio "
                  f"{q['flicker']['edge_ratio']}, warping {q['warping_error']}, endpoints "
                  f"{q['endpoint']['first_vs_A']}/{q['endpoint']['last_vs_B']}", flush=True)


def page(out, disrun, pairs):
    import os
    sys.path.insert(0, str(ROOT / "scripts"))
    from bench_transitions import label_strip, preset_legend, load_json
    OUT, DIS = Path(out), Path(disrun)
    sheet = {r["id"]: r for r in load_json(DIS / "sheet.json").get("pairs", [])}
    tags = [f"{p}_{s:g}s" for p, s in VARIANTS]
    legend = preset_legend(tags)
    rel = lambda p: os.path.relpath(p, OUT)
    html = ["<!doctype html><meta charset=utf-8><title>RoMa field vs DIS field — real clips</title>",
            "<style>body{font:14px system-ui;margin:16px;background:#111;color:#ddd;max-width:1700px}h2{margin-top:40px;border-top:1px solid #333;padding-top:16px}"
            ".pair{display:flex;gap:12px;align-items:flex-start;margin:8px 0}.pair img{height:140px}"
            ".row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:10px 0 18px;padding:8px;background:#181818;border-radius:6px}"
            ".cell video{width:100%;max-height:520px;background:#000}.cell img{max-width:100%;display:block;margin-top:6px}"
            "code{color:#9cf}.legend td{padding:2px 10px;vertical-align:top}.pick label{margin-right:14px}"
            "textarea{width:100%;max-width:900px;background:#222;color:#ddd;border:1px solid #444}button{padding:6px 12px}"
            ".note{color:#bbb}.hint{background:#26210a;padding:10px;border-radius:6px;margin:12px 0}</style>",
            "<h1>RoMa field vs the current DIS field — real clips, 2026-09-15</h1>",
            "<div class=hint><b>What varies: only the dense correspondence field.</b> Left = the current tool (homography + DIS residual, "
            "the clips of the 2026-09-14 run). Right = the same photos, canvas, preset and length rendered from the RoMa outdoor field "
            "(romatch 0.1.2, CPU, 35–55 s per pair for the field) with RoMa's certainty as the splat weight. Class routing, color path, "
            "splat and encoder are identical; the <code>dissolve</code> preset is omitted because it uses no field and would be the same clip twice. "
            "Clips loop; the first and last frames are the two photos byte for byte. Give a verdict per pair and a note, then <b>Export verdicts</b> "
            "(downloads roma_picks.json; drop it next to this page).</div>",
            "<h3>The four variants</h3><table class=legend>"]
    for tag, desc in legend:
        html.append(f"<tr><td><code>{tag}</code></td><td>{desc}</td></tr>")
    html.append("</table><p><button onclick='exportPicks()'>Export verdicts</button> <span id=status class=note></span></p>")
    for pid in pairs:
        row = sheet.get(pid, {})
        html.append(f"<h2 id='{pid}'>{pid} <small>{row.get('before')} → {row.get('after')} · {row.get('size_before')} / {row.get('size_after')}</small></h2>")
        html.append(f"<div class=pair><img src='{rel(DIS / pid / 'thumb_S.jpg')}'><img src='{rel(DIS / pid / 'thumb_F.jpg')}'></div>")
        html.append(f"<div class=pick><b>Verdict:</b> " + " ".join(
            f"<label><input type=radio name='pick_{pid}' value='{v}' onchange='save()'> {v}</label>"
            for v in ("roma better", "dis better", "same", "neither usable")) + "</div>")
        html.append(f"<textarea id='note_{pid}' rows=2 placeholder='what changed for the better or worse; is any clip acceptable as-is?' oninput='save()'></textarea>")
        for tag in tags:
            dr = (row.get("transitions") or {}).get(tag, {})
            rr = load_json(OUT / pid / tag / "report.json")
            q = rr.get("quality", {})
            for base_dir, r in ((DIS / pid / tag, None), (OUT / pid / tag, rr)):
                src = base_dir / "strip.jpg"
                if src.exists() and not (base_dir / "strip_labeled.jpg").exists():
                    n = (r or {}).get("n_frames") or dr.get("n_frames") or 30
                    label_strip(src, base_dir / "strip_labeled.jpg", n, float(tag.rsplit("_", 1)[1].rstrip("s")))
            html.append(f"<div class=row><div class=cell><code>{tag}</code> <b>DIS</b> (current) · certainty={dr.get('mean_certainty')} "
                        f"disp={dr.get('median_disp_px')}px edge_ratio={dr.get('edge_ratio')} warping={dr.get('warping_error')}"
                        f"<br><video src='{rel(DIS / pid / tag / 'transition.mp4')}' controls loop muted playsinline preload=metadata></video>"
                        f"<img src='{rel(DIS / pid / tag / 'strip_labeled.jpg')}'></div>"
                        f"<div class=cell><code>{tag}</code> <b>RoMa</b> · certainty={rr.get('roma_cert_mean')} disp={rr.get('median_disp_px')}px "
                        f"edge_ratio={q.get('flicker', {}).get('edge_ratio')} warping={q.get('warping_error')} field {rr.get('match_s')}s"
                        f"<br><video src='{rel(OUT / pid / tag / 'transition.mp4')}' controls loop muted playsinline preload=metadata></video>"
                        f"<img src='{rel(OUT / pid / tag / 'strip_labeled.jpg')}'></div></div>")
    html.append("""<script>
const KEY='roma_picks:'+location.pathname;
function collect(){const p={};document.querySelectorAll('h2[id]').forEach(h=>{const id=h.id;const r=document.querySelector(`input[name='pick_${id}']:checked`);
 const n=document.getElementById('note_'+id);if((r&&r.value)||(n&&n.value))p[id]={verdict:r?r.value:'',note:n?n.value:''};});return p;}
function save(){try{localStorage.setItem(KEY,JSON.stringify(collect()));document.getElementById('status').textContent='saved locally '+new Date().toLocaleTimeString();}catch(e){}}
function restore(){try{const p=JSON.parse(localStorage.getItem(KEY)||'{}');for(const id in p){const r=document.querySelector(`input[name='pick_${id}'][value='${p[id].verdict}']`);if(r)r.checked=true;
 const n=document.getElementById('note_'+id);if(n&&p[id].note)n.value=p[id].note;}}catch(e){}}
function exportPicks(){const blob=new Blob([JSON.stringify({date:new Date().toISOString(),picks:collect()},null,2)],{type:'application/json'});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='roma_picks.json';a.click();document.getElementById('status').textContent='roma_picks.json downloaded';}
restore();
</script>""")
    (OUT / "index.html").write_text("\n".join(html))
    print(f"wrote {OUT / 'index.html'}")


if __name__ == "__main__":
    if len(sys.argv) > 3 and sys.argv[1] == "--prepare":
        prepare(sys.argv[2], sys.argv[3:])
    elif len(sys.argv) > 4 and sys.argv[1] == "--compare":
        compare(sys.argv[2], sys.argv[3], sys.argv[4:])
    elif len(sys.argv) > 4 and sys.argv[1] == "--render":
        render(sys.argv[2], sys.argv[3], sys.argv[4:])
    elif len(sys.argv) > 4 and sys.argv[1] == "--page":
        page(sys.argv[2], sys.argv[3], sys.argv[4:])
    else:
        sys.exit(__doc__)
