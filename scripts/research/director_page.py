"""The director's review page (round 8, 2026-10-17): one page over a run folder of
`director_render.py` outputs (<pair>_<concept>/{transition.mp4, montage.jpg, info.json}), with the
plan's own words per concept, the resolved numbers, the faults to expect (from notes.json, written
by the agent after reading the frames) and the owner's grading boxes; exports director_picks.json in
the shape of the earlier picks files.

Usage: director_page.py RUN_DIR [--notes notes.json] [--title "..."] [--head head.html] [--key director_r8]

Round 10 (2026-10-17 night): a clip whose plan has a `keyframe_chain` shows its generated keyframes beside
the player, labelled as generated (model, seed, steps from keyframes.json when present), and every clip
lists its filled parts (the plate under A's layers, the plate under B's front, a hidden line target) with
their shares, so the page says which parts are the photos' pixels and which are not.
"""
import sys, json, argparse, html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLANS = ROOT / "scripts/research/plans"


def esc(s):
    return html.escape(str(s))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run"); ap.add_argument("--notes", default=None); ap.add_argument("--title", default="The director's first planned renders (2026-10-17)")
    ap.add_argument("--head", default=None); ap.add_argument("--key", default="director_r8")
    ap.add_argument("--keyframes", default=None, help="keyframes.json of the generated helpers (name -> model, seed, steps, size)")
    a = ap.parse_args()
    kf_index = {}
    if a.keyframes:
        kj = json.load(open(a.keyframes))
        for k in (kj if isinstance(kj, list) else kj.get("keyframes", [])):
            for key in ("png", "path", "file", "name"):
                if k.get(key):
                    kf_index[Path(k[key]).name] = k
    run = Path(a.run)
    notes = json.load(open(a.notes)) if a.notes else {}
    head = Path(a.head).read_text() if a.head else ""
    items = sorted(p for p in run.iterdir() if p.is_dir() and (p / "info.json").exists())
    pairs = {}
    for p in items:
        pair, concept = p.name.rsplit("_", 1)
        pairs.setdefault(pair, []).append((concept, p))
    out = [f"<!doctype html><html lang=en><head><meta charset=utf-8><title>{esc(a.title)}</title>",
           "<style>body{font:15px/1.45 -apple-system,Helvetica,Arial,sans-serif;margin:24px;max-width:1500px;color:#222}"
           "h1{font-size:20px} h2{font-size:17px;margin-top:36px;border-top:1px solid #ccc;padding-top:14px} h3{font-size:15px;margin:8px 0}"
           ".row{display:flex;gap:18px;flex-wrap:wrap;align-items:flex-start} video{max-width:640px;width:100%;background:#000}"
           ".clip{flex:0 1 640px} .look{background:#f6f6f6;padding:10px 14px;border-left:4px solid #888;margin:10px 0;max-width:700px}"
           ".plan{background:#eef4ff;padding:8px 12px;border-left:4px solid #58a;margin:8px 0;max-width:700px;font-size:14px}"
           "code{background:#eee;padding:0 3px} label{margin-right:14px} textarea{width:640px} button{padding:6px 12px} pre{background:#f0f0f0;padding:8px;white-space:pre-wrap}"
           "table{border-collapse:collapse;font-size:13px} td,th{border:1px solid #ccc;padding:2px 8px;text-align:left}</style></head><body>",
           f"<h1>{esc(a.title)}</h1>", head]
    tags = []
    for pair, cl in pairs.items():
        out.append(f"<h2>{esc(pair)}</h2>")
        plan = json.load(open(PLANS / f"{pair}.json"))
        out.append(f"<p class=plan><b>The planner's reading.</b> A: {esc(plan['reading']['a'])} B: {esc(plan['reading']['b'])} "
                   f"(planner: {esc(plan['planner']['model'])}, brief: {esc(plan['planner']['brief'])}, prompt sha256 {esc(plan['planner']['prompt_sha256'][:12])}…)</p>")
        out.append("<div class=row>")
        for concept, p in cl:
            info = json.load(open(p / "info.json"))
            base = concept.split("-")[0]           # a variant folder "c1-nosit" shows its base concept's plan with the knobs it was rendered with
            c = next((cc for cc in plan["concepts"] if cc["id"] == base), plan["concepts"][0])
            tag = f"{pair}_{concept}"; tags.append(tag)
            n = notes.get(tag, {})
            out.append(f"<div class=clip><h3>{esc(tag)} — rank {c.get('rank')} (<code>{esc(c['id'])}</code>)</h3>"
                       f"<video controls loop src='{esc(p.name)}/transition.mp4'></video>"
                       f"<p class=plan><b>The idea (the planner's sentence):</b> {esc(c['idea'])}</p>")
            if n.get("look"):
                out.append(f"<div class=look><p><b>Look at:</b> {esc(n['look'])}</p>")
            else:
                out.append("<div class=look>")
            if n.get("faults"):
                out.append(f"<p><b>Faults to expect (read from the frames by the agent):</b> {esc(n['faults'])}</p>")
            lays = ", ".join(f"{l['name']} ({l['by']}, {l['window'][0]}–{l['window'][1]})" for l in info.get("layers", []))
            unpl = "; ".join(f"{u['name']}: {u['why']}" for u in info.get("unplaced", [])) or "none"
            par = info.get("parallax") or {"gain": 0}
            out.append(f"<p><b>Resolved numbers:</b> canvas {info['canvas'][0]}×{info['canvas'][1]}; camera {esc(info.get('camera'))}, start zoom {info.get('start_zoom')}×"
                       f"{(', end scale ' + str(info['end_scale'])) if 'end_scale' in info else ''}; parallax gain {par.get('gain')}"
                       f"{(', push ' + str(par.get('push'))) if par.get('push') else ''}{(', sources ' + ','.join(par.get('sources', []))) if par.get('sources') else ''}; "
                       f"first / second / last interior step {info['step_first']} / {info['step_second']} / {info['step_last']} levels, peak {info['step_max']}; "
                       f"{info['frames']} frames ({info['seconds']} s at {info['fps']} fps), rendered in {info['wall_s']} s. Layers: {esc(lays)}. Unplaced or skipped: {esc(unpl)}.</p>")
            # round 12: the motion profile (the mean flow between consecutive frames) as a sparkline with the pauses and
            # jumps, and the rule measures (B inside A's region, edges in neither photo, the guard)
            mp = info.get("motion_px")
            if mp:
                mx = max(mp) or 1.0; w_, h_ = 600, 60
                pts = " ".join(f"{(j / max(1, len(mp) - 1)) * w_:.1f},{h_ - (v / mx) * (h_ - 4):.1f}" for j, v in enumerate(mp))
                mo = info.get("motion") or {}
                adj = "; ".join(f"{a_['name']} {a_['from']} → {a_['to']}" for a_ in mo.get("adjusted", [])) if mo else ""
                out.append(f"<p><b>Motion profile</b> (mean flow per frame, peak {mx:.1f} px; median {info.get('motion_median_px')} px; "
                           f"{info.get('motion_pauses')} pause frames, {info.get('motion_jumps')} jumps; model {esc(mo.get('kind', 'round 11: a smootherstep per layer'))}"
                           f"{(', beats moved to overlap: ' + esc(adj)) if adj else ''}):<br>"
                           f"<svg width={w_} height={h_} style='background:#f4f4f4;border:1px solid #ccc'><polyline fill=none stroke='#36c' stroke-width=1.5 points='{pts}'/></svg></p>")
                gd = info.get("guard") or []
                out.append(f"<p><b>Rule measures:</b> B inside A's region first above 1 % at frame {info.get('b_inside_first')}; "
                           f"edges in neither photo at most {info.get('residual_edge_max', 0) * 100:.2f} % of the frame; "
                           f"guarded targets {esc(', '.join(f"{g['name']} (until {g['arrive']}, {g['share_B'] * 100:.1f} % of B)" for g in gd)) or 'none'}"
                           f"{(', guard engaged on up to ' + format(info.get('guard_share_max', 0) * 100, '.1f') + ' % of the frame') if info.get('guard_share_max') else ''}.</p>")
            knobs = "; ".join(f"<code>{esc(k['name'])}</code> {esc(k.get('what', ''))} (range {k.get('range')}, default {k.get('default')})" for k in c.get("knobs", []))
            out.append(f"<p><b>Knobs you can turn (say which, and which way):</b> {knobs}</p>")
            if info.get("knobs"):
                out.append(f"<p><b>Knobs set on this render (the operator's hand):</b> <code>{esc(json.dumps(info['knobs']))}</code></p>")
            # generated and filled parts (round 10): the owner's 2026-09-29 conditions apply to the keyframes; a fill is cv2.inpaint
            gen = []
            for l in info.get("layers", []):
                ch = l.get("chain")
                if not ch:
                    continue
                tiles = []
                for kf in ch["keyframes"]:
                    rel = Path(kf)
                    try:
                        rel = Path(kf).resolve().relative_to(run.resolve().parent) if Path(kf).is_absolute() else (ROOT / kf).resolve().relative_to(run.resolve().parent)
                        src = "../" + str(rel)
                    except ValueError:
                        src = str(kf)
                    meta = kf_index.get(Path(kf).name, {})
                    cap = f"{Path(kf).name}: generated ({esc(meta.get('model', 'FLUX.3 image klein distilled bf16'))}, seed {esc(meta.get('seed', '?'))}, {esc(meta.get('steps', '?'))} steps, cfg {esc(meta.get('cfg', '?'))})"
                    tiles.append(f"<figure style='display:inline-block;margin:4px;max-width:220px'><img src='{esc(src)}' style='max-width:220px;max-height:220px;border:2px solid #c60'><figcaption style='font-size:12px'>{cap}</figcaption></figure>")
                gen.append(f"<p><b>Generated keyframes inside <code>{esc(l['name'])}</code> (frame {esc(ch['frame'])}, reached at {esc(ch['times'])} of the layer's window; the renderer morphs A → keyframes → B inside the matte):</b></p>{''.join(tiles)}")
            fills = []
            if info.get("plate_A_share"):
                fills.append(f"A filled under its lifted layers ({info['plate_A_share'] * 100:.1f} % of A's frame; cv2.inpaint)")
            if info.get("front_share"):
                fills.append(f"B filled under its front layer ({info['front_share'] * 100:.1f} % of B; cv2.inpaint), seen only until the front has entered")
            if info.get("plate_hidden_share"):
                fills.append(f"a line target hidden in B's plate ({info['plate_hidden_share'] * 100:.2f} % of B)")
            soft = [l["name"] for l in info.get("layers", []) if l.get("soft")]
            hard = [l["name"] for l in info.get("layers", []) if l.get("soft") is False]
            out.append(f"<p><b>What is not the photos' pixels:</b> {esc('; '.join(fills)) if fills else 'nothing filled'}; generated: {('the keyframes above' if gen else 'nothing')}. "
                       f"Soft mattes (the matting model): {esc(', '.join(soft)) or 'none'}; hard masks: {esc(', '.join(hard)) or 'none'}"
                       f"{('; matte fallbacks ' + esc(', '.join(info['matte_fallbacks']))) if info.get('matte_fallbacks') else ''}.</p>")
            out.extend(gen)
            out.append(f"<p><b>The planner's own risk note:</b> {esc(c.get('risk', ''))}</p></div>")
            out.append(f"<p><label><input type=checkbox id='p_{tag}_one_picture'> one picture</label><label><input type=checkbox id='p_{tag}_transforms'> content transforms</label>"
                       f"<label><input type=checkbox id='p_{tag}_not_invented'> nothing invented</label><label><input type=checkbox id='ok_{tag}'> acceptable as-is</label></p>"
                       f"<textarea id='note_{tag}' rows=3 placeholder='what is wrong, what should happen instead, which knob'></textarea></div>")
        out.append("</div>")
        opts = "".join(f"<option value='{esc(cc)}'>{esc(pair + '_' + cc)}</option>" for cc, _ in cl)
        out.append(f"<p><label>best for {esc(pair)}: <select id='best_{pair}'><option value='none'>none</option>{opts}</select></label></p>")
    out.append("<h2>Export</h2><p><button onclick='exportPicks()'>Download director_picks.json</button> (best per pair, and per clip: the three boxes, acceptable as-is, the note)</p><pre id=out></pre>")
    out.append("<script>const TAGS=" + json.dumps(tags) + ";const PAIRS=" + json.dumps(list(pairs.keys())) + ";const PROPS=['one_picture','transforms','not_invented'];"
               "function state(){const clips={};for(const t of TAGS){const props={};for(const k of PROPS)props[k]=document.getElementById(`p_${t}_${k}`).checked;"
               "clips[t]={acceptable:document.getElementById(`ok_${t}`).checked,note:document.getElementById(`note_${t}`).value,props};}"
               "const best={};for(const p of PAIRS)best[p]=document.getElementById(`best_${p}`).value;return {date:new Date().toISOString(),page:'" + a.key + "',best,clips};}"
               "function save(){try{localStorage.setItem('director_picks_" + a.key + "',JSON.stringify(state()));}catch(e){}}"
               "function load(){try{const s=JSON.parse(localStorage.getItem('director_picks_" + a.key + "')||'null');if(!s)return;for(const t of TAGS){const v=s.clips[t];if(!v)continue;"
               "document.getElementById(`ok_${t}`).checked=!!v.acceptable;document.getElementById(`note_${t}`).value=v.note;for(const k of PROPS)document.getElementById(`p_${t}_${k}`).checked=!!v.props[k];}"
               "for(const p of PAIRS){if(s.best&&s.best[p])document.getElementById(`best_${p}`).value=s.best[p];}}catch(e){}}"
               "function exportPicks(){const s=JSON.stringify(state(),null,1);document.getElementById('out').textContent=s;const a=document.createElement('a');"
               "a.href=URL.createObjectURL(new Blob([s],{type:'application/json'}));a.download='director_picks.json';a.click();}"
               "document.querySelectorAll('input,select,textarea').forEach(el=>el.addEventListener('input',save));load();</script></body></html>")
    (run / "index.html").write_text("\n".join(out))
    print(run / "index.html", len(tags), "clips")


if __name__ == "__main__":
    main()
