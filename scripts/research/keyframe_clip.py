#!/usr/bin/env python3
"""Keyframe-cleaned clip: A -> K1 -> K2 -> K3 -> B (research probe; 2026-09-28, Track B).

Nothing here enters transitions.py. The layered composite comes from the layered probe AT A
GIVEN GIT REVISION (a copy written by `git show`), so a probe being edited in the working tree
does not change the references. The segments between consecutive pictures are rendered by
transitions.py unchanged: its CLI (`transitions.py pair`) writes each segment's report.json and
mp4, and the same functions called in-process (prepare + iter_frames, deterministic) give the
lossless frames the clip is assembled from.

Subcommands
  composites --probe FILE --score JSON --times 0.25,0.5,0.75 --out DIR
      the probe's composite(layers, t) at each clip time as lossless PNG at the round-4 canvas.
  clip --pair P --a A.png --b B.png --keys K1.png,K2.png,K3.png --out DIR [--size WxH]
       [--frames 90] [--key-frames 22,45,67] [--preset morph] [--force-class ''|A|B]
      A and B are cover-resized to the working size (transitions.cover); keyframes too when
      --size differs from theirs. Segment k runs picture k -> k+1 with n_k frames including
      both ends; the clip drops the first frame of every segment after the first, so no frame
      is duplicated at a joint. Writes clip.mp4, frames/NNN.png, segments/<k>/ (CLI output),
      clip.json (per-segment class, inliers, displacement, goal numbers; per-step MAD;
      Laplacian variance of L per frame; md5 of the frame stack).
      --override 3=morph:A renders segment 3 with another preset or a forced class.
  page --config page.json --out DIR   the review page (shape of layered_probe.write_page at HEAD).
  measure --clip DIR   re-print the numbers of clip.json.

numpy + cv2 + transitions only; no torch, no network.
"""
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import transitions as T  # noqa: E402

PY = str(ROOT / ".venv" / "bin" / "python")


def load_probe(path):
    spec = importlib.util.spec_from_file_location("probe_rev", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.ROOT = ROOT
    mod.FIX = ROOT / "fixtures"
    return mod


def read_rgb(p):
    im = cv2.imread(str(p), cv2.IMREAD_COLOR)
    if im is None:
        raise SystemExit(f"cannot read {p}")
    return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)


def write_rgb(p, rgb):
    cv2.imwrite(str(p), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))


def mad(a, b):
    return float(np.abs(a.astype(np.int16) - b.astype(np.int16)).mean())


def lap_var_L(rgb):
    """Variance of the Laplacian (ksize 1, CV_32F) of the 8-bit Lab L channel at full frame size."""
    L = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)[..., 0]
    return float(cv2.Laplacian(L, cv2.CV_32F, ksize=1).var())


def cmd_composites(a):
    P = load_probe(a.probe)
    score = json.loads(Path(a.score).read_text())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    A, B = P.canvas_pair(score["pair"], score.get("max_long", 1920))
    scene = P.Scene(A, B, a.seed)
    n = max(2, int(round(score.get("seconds", 2.0) * float(score.get("fps", 30)))))
    scene.n = n                                    # as render_score sets it before build_layers
    t0 = time.time()
    layers = P.build_layers(scene, score)
    prep = round(time.time() - t0, 2)
    scene.n = n
    write_rgb(out / "A.png", A)
    write_rgb(out / "B.png", B)
    rows = []
    for t in [float(x) for x in a.times.split(",")]:
        f = P.composite(layers, t)
        name = f"comp_{t:.4f}".rstrip("0").rstrip(".") + ".png"
        write_rgb(out / name, f)
        rows.append({"t": t, "file": name, "mad_A": round(mad(f, A), 2), "mad_B": round(mad(f, B), 2)})
        print(json.dumps(rows[-1]), flush=True)
    meta = {"probe": str(a.probe), "probe_sha256": hashlib.sha256(Path(a.probe).read_bytes()).hexdigest(),
            "score": str(a.score), "pair": score["pair"], "canvas": [A.shape[1], A.shape[0]], "n": n,
            "seed": a.seed, "prep_s": prep, "composites": rows}
    (out / "composites.json").write_text(json.dumps(meta, indent=1))


def seg_counts(total, keys):
    marks = [0] + keys + [total - 1]
    return [marks[i + 1] - marks[i] + 1 for i in range(len(marks) - 1)], marks


def cmd_clip(a):
    out = Path(a.out)
    (out / "frames").mkdir(parents=True, exist_ok=True)
    (out / "work").mkdir(exist_ok=True)
    keys = [Path(k) for k in a.keys.split(",")] if a.keys else []
    kimgs = [read_rgb(k) for k in keys]
    if a.size:
        W, H = (int(v) for v in a.size.lower().split("x"))
    else:
        H, W = kimgs[0].shape[:2]
    pics = [T.cover(read_rgb(a.a), W, H)] + [T.cover(k, W, H) for k in kimgs] + [T.cover(read_rgb(a.b), W, H)]
    names = ["A"] + [f"K{i + 1}" for i in range(len(kimgs))] + ["B"]
    paths = []
    for nm, im in zip(names, pics):
        p = out / "work" / f"{nm}.png"
        write_rgb(p, im)
        paths.append(p)
    kf = [int(x) for x in a.key_frames.split(",")] if a.key_frames else []
    counts, marks = seg_counts(a.frames, kf)
    assert sum(counts) - (len(counts) - 1) == a.frames, (counts, a.frames)
    segs, frames = [], []
    fps = 30.0
    ovr = {}
    for o in a.override:                            # "3=morph:A" -> segment 3 preset morph, class A
        seg, v = o.split("=", 1)
        pr, _, cl = v.partition(":")
        ovr[int(seg)] = (pr or a.preset, cl)
    for k in range(len(pics) - 1):
        n_k = counts[k]
        preset, fcls = ovr.get(k + 1, (a.preset, a.force_class))
        seconds = n_k / fps
        sd = out / "segments" / f"{k + 1}_{names[k]}-{names[k + 1]}"
        cmd = [PY, str(ROOT / "transitions.py"), "pair", str(paths[k]), str(paths[k + 1]), "--out", str(sd),
               "--preset", preset, "--seconds", f"{seconds:.6f}", "--fps", "30"]
        if fcls:
            cmd += ["--class", fcls]
        t0 = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True)
        wall = round(time.time() - t0, 2)
        row = {"segment": f"{names[k]}->{names[k + 1]}", "preset": preset, "force_class": fcls, "n_frames": n_k, "frame_span": [marks[k], marks[k + 1]],
               "cmd": " ".join(cmd[1:]), "rc": r.returncode, "wall_s": wall}
        if r.returncode != 0:
            row["stderr"] = r.stderr[-800:]
            segs.append(row)
            print(json.dumps(row), flush=True)
            (out / "clip.json").write_text(json.dumps({"segments": segs, "failed": True}, indent=1))
            raise SystemExit(f"segment {row['segment']} failed rc={r.returncode}")
        rep = json.loads((sd / "report.json").read_text())
        q = rep.get("quality", {})
        row.update({k2: rep.get(k2) for k2 in ("class", "method", "inliers", "inlier_ratio", "disp_median",
                                                "disp_p95", "canvas", "n_frames", "correspondence_s")})
        row["diag"] = {k2: v for k2, v in rep.items() if k2 not in ("spec", "quality", "outputs", "tool_version")}
        row["goal"] = q.get("goal")
        row["quality"] = {k2: q.get(k2) for k2 in ("warping_error", "flicker", "endpoint")}
        # the same frames in process (deterministic; the CLI's mp4 is lossy)
        spec = T.spec_from(preset, seconds=seconds, fps=30.0, force_class=fcls or "")
        spec.clamp()
        A2, B2, corr = T.prepare(pics[k], pics[k + 1], spec)
        row["inproc_class"] = corr["cls"]
        fr = list(T.iter_frames(A2, B2, spec, corr))
        assert len(fr) == n_k, (len(fr), n_k)
        frames.extend(fr if k == 0 else fr[1:])
        segs.append(row)
        print(json.dumps({x: row.get(x) for x in ("segment", "n_frames", "class", "inproc_class", "method", "wall_s", "goal")}), flush=True)
    assert len(frames) == a.frames
    h = hashlib.md5()
    enc = T.FrameEncoder(out / "clip.mp4", W, H, 30.0)
    for i, f in enumerate(frames):
        write_rgb(out / "frames" / f"{i:03d}.png", f)
        h.update(np.ascontiguousarray(f).tobytes())
        enc.write(f)
    enc.close()
    steps = [round(mad(frames[i], frames[i + 1]), 3) for i in range(len(frames) - 1)]
    lap = [round(lap_var_L(f), 2) for f in frames]
    stats = T.StreamStats(len(frames))
    for i, f in enumerate(frames):
        stats.add(i, f)
    q = stats.quality(pics[0], pics[-1])
    ok, buf = cv2.imencode(".jpg", cv2.cvtColor(stats.strip(), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
    if ok:
        (out / "strip.jpg").write_bytes(buf.tobytes())
    res = {"pair": a.pair, "size": [W, H], "frames": len(frames), "key_frames": kf, "preset": a.preset,
           "force_class": a.force_class, "keys": [str(k) for k in keys], "segments": segs,
           "frame0_equals_A": bool(np.array_equal(frames[0], pics[0])),
           "last_equals_B": bool(np.array_equal(frames[-1], pics[-1])),
           "keyframes_in_clip_equal": [bool(np.array_equal(frames[m], pics[j + 1])) for j, m in enumerate(kf)],
           "first_interior_vs_A": round(mad(frames[1], pics[0]), 3),
           "last_interior_vs_B": round(mad(frames[-2], pics[-1]), 3),
           "steps": steps, "laplace_L": lap, "frames_md5": h.hexdigest(),
           "mp4_md5": hashlib.md5((out / "clip.mp4").read_bytes()).hexdigest(),
           "quality": {k2: q.get(k2) for k2 in ("warping_error", "flicker", "endpoint", "goal")}}
    (out / "clip.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k2: res[k2] for k2 in ("frames", "frame0_equals_A", "last_equals_B", "keyframes_in_clip_equal",
                                               "first_interior_vs_A", "last_interior_vs_B", "frames_md5", "mp4_md5")}))


def cmd_measure(a):
    r = json.loads((Path(a.clip) / "clip.json").read_text())
    s = np.array(r["steps"])
    print(json.dumps({"steps_max": float(s.max()), "argmax": int(s.argmax()), "steps_median": float(np.median(s)),
                      "md5": r["frames_md5"]}))


PROPS = (("one_picture", "one picture"), ("transforms", "content transforms"), ("not_invented", "nothing invented"))


def cmd_page(a):
    """index.html in the shape of layered_probe.write_page (HEAD 2026-09-27): the same CSS, boxes, pick
    radios, note and export script; clips from clip.json / report.json, the keyframes beside their composites."""
    out = Path(a.out)
    cfg = json.loads(Path(a.config).read_text())
    html = ["<!doctype html><meta charset=utf-8><title>Keyframe-cleaned clips</title>",
            "<style>body{font:14px system-ui;margin:16px;background:#111;color:#ddd;max-width:1600px}h2{margin-top:40px;border-top:1px solid #333;padding-top:16px}"
            ".run{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:14px;align-items:start;margin:10px 0 18px;padding:8px;background:#181818;border-radius:6px}"
            ".run img{max-width:100%;display:block}.run video{width:320px;max-height:420px;background:#000}code{color:#9cf}"
            ".boxes label{margin-right:12px;color:#fd9}.pick label{margin-right:14px}textarea{width:100%;max-width:900px;background:#222;color:#ddd;border:1px solid #444}"
            ".note{color:#bbb}.hint{background:#26210a;padding:10px;border-radius:6px;margin:12px 0}button{padding:6px 12px}"
            ".kf{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.kf figure{margin:0}.kf img{width:100%;display:block}"
            "@media (max-width:700px){.run{grid-template-columns:1fr}.run video{width:100%}.kf{grid-template-columns:1fr}}</style>",
            f"<h1>Keyframe-cleaned clips — {cfg['date']}</h1>",
            f"<div class=hint><b>What varies between the clips.</b> {cfg['note']}</div>",
            "<div class=hint>Under every clip the three boxes ask for the property, not the pick: <b>one picture</b> (the mid frame is one coherent picture, "
            "not two superimposed), <b>content transforms</b> (details move and change rather than the frame panning or fading), <b>nothing invented</b> "
            "(no content that is in neither photo). Pick the closer clip per pair, write a note, and <b>Export picks</b> (writes <code>keyclip_picks.json</code>).</div>",
            "<p><button onclick='exportPicks()'>Export picks</button> <span id=status class=note></span></p>"
            "<details><summary class=note>preview of what Export writes</summary><pre id=preview class=note></pre></details>"]
    for pair, pc in cfg["pairs"].items():
        html.append(f"<h2 id='{pair}'>{pair}</h2><p class=note>{pc.get('note', '')}</p>")
        html.append("<div class=pick><b>Closer to the goal:</b> " + " ".join(
            f"<label><input type=radio name='pick_{pair}' value='{v['tag']}' onchange='save()'> {v['tag']}</label>" for v in pc["variants"])
            + f" <label><input type=radio name='pick_{pair}' value='none' onchange='save()'> neither</label></div>")
        html.append(f"<textarea id='note_{pair}' rows=3 placeholder='what is wrong / what should change' oninput='save()'></textarea>")
        for v in pc["variants"]:
            boxes = " ".join(f"<label><input type=checkbox class=prop data-pair='{pair}' data-tag='{v['tag']}' data-k='{k}' onchange='save()'> {lab}</label>"
                             for k, lab in PROPS)
            html.append(f"<div class=run><div><code>{v['tag']}</code> {v['line']}<br><span class=boxes>{boxes}</span><br>"
                        f"<img src='{v['strip']}' alt='strip of {v['tag']}'></div>"
                        f"<video src='{v['mp4']}' controls loop muted playsinline preload=metadata></video></div>")
        html.append("<details open><summary><b>The three keyframes</b> (left: the deterministic composite given to the model; right: the keyframe; click for the lossless PNG)</summary><div class=kf>")
        for k in pc["keys"]:
            html.append(f"<figure><a href='{k['pair_img']}'><img src='{k['pair_img']}' alt='{k['name']}'></a><figcaption class=note>{k['caption']} "
                        f"<a href='{k['comp']}'>composite</a> · <a href='{k['kf']}'>keyframe</a></figcaption></figure>")
        html.append("</div></details>")
    html.append("""<script>
const KEY='picks:'+location.pathname;
function collect(){const p={};document.querySelectorAll('h2[id]').forEach(h=>{const id=h.id;const r=document.querySelector(`input[name='pick_${id}']:checked`);
 const n=document.getElementById('note_'+id);const props={};document.querySelectorAll(`input.prop[data-pair='${id}']`).forEach(b=>{if(b.checked){(props[b.dataset.tag]=props[b.dataset.tag]||{})[b.dataset.k]=true;}});
 if((r&&r.value)||(n&&n.value)||Object.keys(props).length)p[id]={best:r?r.value:'',note:n?n.value:'',props:props};});return p;}
function save(){try{const c=collect();localStorage.setItem(KEY,JSON.stringify(c));document.getElementById('status').textContent='saved locally '+new Date().toLocaleTimeString();document.getElementById('preview').textContent=JSON.stringify(c,null,1);}catch(e){}}
function restore(){try{const p=JSON.parse(localStorage.getItem(KEY)||'{}');for(const id in p){const r=document.querySelector(`input[name='pick_${id}'][value='${p[id].best}']`);if(r)r.checked=true;
 const n=document.getElementById('note_'+id);if(n&&p[id].note)n.value=p[id].note;const pr=p[id].props||{};for(const tag in pr){for(const k in pr[tag]){const b=document.querySelector(`input.prop[data-pair='${id}'][data-tag='${tag}'][data-k='${k}']`);if(b)b.checked=true;}}}}catch(e){}}
function exportPicks(){const blob=new Blob([JSON.stringify({date:new Date().toISOString(),page:'keyclip',picks:collect()},null,2)],{type:'application/json'});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='keyclip_picks.json';a.click();document.getElementById('status').textContent='keyclip_picks.json downloaded';}
restore();
</script>""")
    (out / "index.html").write_text("\n".join(html))
    print(f"wrote {out / 'index.html'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("composites")
    c.add_argument("--probe", required=True)
    c.add_argument("--score", required=True)
    c.add_argument("--times", default="0.25,0.5,0.75")
    c.add_argument("--seed", type=int, default=0)
    c.add_argument("--out", required=True)
    k = sub.add_parser("clip")
    k.add_argument("--pair", required=True)
    k.add_argument("--a", required=True)
    k.add_argument("--b", required=True)
    k.add_argument("--keys", default="")
    k.add_argument("--out", required=True)
    k.add_argument("--size", default="")
    k.add_argument("--frames", type=int, default=90)
    k.add_argument("--key-frames", default="22,45,67")
    k.add_argument("--preset", default="morph")
    k.add_argument("--force-class", default="")
    k.add_argument("--override", action="append", default=[], help="SEG=PRESET[:CLASS], segment numbered from 1 (repeatable)")
    g = sub.add_parser("page")
    g.add_argument("--config", required=True, help="page.json: date, note, pairs{variants[tag,line,strip,mp4], keys[...]}")
    g.add_argument("--out", required=True)
    m = sub.add_parser("measure")
    m.add_argument("--clip", required=True)
    a = ap.parse_args()
    return {"composites": cmd_composites, "clip": cmd_clip, "measure": cmd_measure, "page": cmd_page}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
