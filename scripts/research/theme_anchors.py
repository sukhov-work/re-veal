#!/usr/bin/env python3
"""Theme anchors on the mismatched fixtures: render each pair through the tool's `--anchors`
path from a hand-placed anchors file, and build a review page with the three per-property
boxes (one picture / content transforms / nothing invented), a pick and a note per pair.

Research script (2026-09-26; plan §Rank 2026-09-26 item 3, first half). Imports neither tool;
calls `transitions.py pair` through the CLI like scripts/bench_transitions.py does.

Anchors file (JSON): {"<pair>": {"anchors": [[ax, ay, bx, by], ...], "why": "sun -> sun, ..."}}
in CANVAS pixels of the tool's `finish` canvas capped at --max-long (the gridded canvases under
benchmarks/runs/2026-09-26/anchors/<pair>_grid.jpg show the coordinates).

  .venv/bin/python scripts/research/theme_anchors.py --anchors anchors.json --out DIR [--only pair]
  .venv/bin/python scripts/research/theme_anchors.py --anchors anchors.json --out DIR --page-only
  ... --picks picks.json   (merge the owner's export into the sheet)
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = str(ROOT / ".venv" / "bin" / "python")
FIX = ROOT / "fixtures"


def find_pair(pair):
    s = sorted(FIX.glob(f"{pair}_S.*"))
    f = sorted(FIX.glob(f"{pair}_F.*"))
    if not s or not f:
        raise SystemExit(f"fixture {pair} not found under {FIX}")
    return s[0], f[0]


def render(pair, anchors, out, seconds, max_long, variants):
    S, F = find_pair(pair)
    rows = {}
    astr = ";".join(",".join(f"{v:g}" for v in a) for a in anchors)
    for tag, extra in variants.items():
        d = out / pair / tag
        cmd = [PY, str(ROOT / "transitions.py"), "pair", str(S), str(F), "--out", str(d),
               "--preset", "morph", "--seconds", str(seconds), "--max-long", str(max_long)] + extra
        if "anchors" in tag:
            cmd += ["--anchors", astr]
        t = time.time()
        p = subprocess.run(cmd, capture_output=True, text=True)
        wall = round(time.time() - t, 1)
        rep = {}
        if (d / "report.json").exists():
            rep = json.loads((d / "report.json").read_text())
        q = rep.get("quality", {})
        rows[tag] = {"rc": p.returncode, "wall_s": wall, "class": rep.get("class"), "method": rep.get("method"),
                     "canvas": rep.get("canvas"), "n_frames": rep.get("n_frames"),
                     "warping_error": q.get("warping_error"), "edge_ratio": (q.get("flicker") or {}).get("edge_ratio"),
                     "goal": q.get("goal"), "mp4": f"{pair}/{tag}/transition.mp4", "strip": f"{pair}/{tag}/strip.jpg",
                     "error": p.stderr.strip().splitlines()[-1] if p.returncode and p.stderr.strip() else None}
        print(f"  {pair} {tag}: rc={p.returncode} {rep.get('method')} goal={q.get('goal')} {wall}s", flush=True)
    return rows


def write_page(out, sheet, picks):
    picks = (picks or {}).get("picks", {})
    html = ["<!doctype html><meta charset=utf-8><title>Theme anchors — mismatched pairs</title>",
            "<style>body{font:14px system-ui;margin:16px;background:#111;color:#ddd;max-width:1600px}h2{margin-top:40px;border-top:1px solid #333;padding-top:16px}"
            ".run{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:14px;align-items:start;margin:10px 0 18px;padding:8px;background:#181818;border-radius:6px}"
            ".run img{max-width:100%;display:block}.run video{width:320px;max-height:380px;background:#000}code{color:#9cf}"
            ".boxes label{margin-right:12px;color:#fd9}.pick label{margin-right:14px}textarea{width:100%;max-width:900px;background:#222;color:#ddd;border:1px solid #444}"
            ".note{color:#bbb}.hint{background:#26210a;padding:10px;border-radius:6px;margin:12px 0}button{padding:6px 12px}</style>",
            f"<h1>Theme anchors on the mismatched pairs — {sheet['date']}</h1>",
            "<div class=hint><b>What varies.</b> <code>flat</code> is the shipped class B pan-and-zoom (the 2026-09-23 default). "
            "<code>anchors_alpha</code> is the same tool with hand-placed theme anchors (listed under each pair) through Moving Least Squares, "
            "the combination still the alpha crossfade. <code>anchors_falloff</code> is the same anchored field faded to zero at the canvas border over 45 % of the short edge "
            "(<code>--anchor-falloff 0.45</code>, 2026-09-26: the frame edge stays off the picture; a narrow band of 0.2 tore the picture where the field is large, so the wide band is shown). "
            "<code>anchors_auto</code> uses anchors found automatically (a brightest-blob sun, the strongest horizontal edge row as the horizon, YuNet faces largest-first, DINOv2 mutual patch matches) with the same falloff; "
            "it exists only where three or more anchors were found. Every clip: morph, 2 s, canvas ≤ 1920 px. Under every clip three boxes ask for the property, not the pick: "
            "<b>one picture</b> (the mid frame is one coherent picture, not two superimposed), <b>content transforms</b> (details move and change rather than the frame panning or fading), "
            "<b>nothing invented</b> (no content that is in neither photo). The goal numbers beside each clip are calibrated on your earlier verdicts and are there to be checked against your eye. "
            "Then pick the closer variant per pair, write what is wrong, and <b>Export picks</b>; drop the file beside sheet.json and run "
            "<code>scripts/research/theme_anchors.py --anchors anchors.json --out DIR --page-only --picks picks.json</code>.</div>",
            "<p><button onclick='exportPicks()'>Export picks</button> <span id=status class=note></span></p>"
            "<details><summary class=note>preview of what Export writes</summary><pre id=preview class=note></pre></details>"]
    for pair, row in sheet["pairs"].items():
        pk = picks.get(pair) or {}
        html.append(f"<h2 id='{pair}'>{pair} <small>canvas {'x'.join(str(v) for v in (row['canvas'] or []))}</small></h2>")
        for tag, ab in (row.get("anchors_by_tag") or {"anchors_alpha": {"anchors": row["anchors"], "why": row["why"]}}).items():
            html.append(f"<p class=note><code>{tag}</code> anchors (A → B, canvas px): {ab['why']}<br><code>{'; '.join(','.join(f'{v:g}' for v in a) for a in ab['anchors'])}</code></p>")
        html.append(f"<div class=pick><b>Closer to the goal:</b> " + " ".join(
            f"<label><input type=radio name='pick_{pair}' value='{tag}' {'checked' if pk.get('best') == tag else ''} onchange='save()'> {tag}</label>"
            for tag in row["variants"]) + f" <label><input type=radio name='pick_{pair}' value='none' {'checked' if pk.get('best') == 'none' else ''} onchange='save()'> neither</label></div>")
        html.append(f"<textarea id='note_{pair}' rows=2 placeholder='what is wrong / what works' oninput='save()'>{pk.get('note', '')}</textarea>")
        for tag, r in row["variants"].items():
            g = r.get("goal") or {}
            goal_txt = (f" goal: feat={g.get('feat_floor')} laplace={g.get('laplace_floor')} contrast={g.get('contrast_floor')} "
                        f"dissolve_fit={g.get('dissolve_fit')} motion={g.get('motion_share')}") if g else ""
            pp = (pk.get("props") or {}).get(tag) or {}
            boxes = " ".join(
                f"<label><input type=checkbox class=prop data-pair='{pair}' data-tag='{tag}' data-k='{k}' {'checked' if pp.get(k) else ''} onchange='save()'> {lab}</label>"
                for k, lab in (("one_picture", "one picture"), ("transforms", "content transforms"), ("not_invented", "nothing invented")))
            html.append(f"<div class=run><div><code>{tag}</code> class={r.get('class')} {r.get('method')} edge_ratio={r.get('edge_ratio')} warping={r.get('warping_error')}{goal_txt}"
                        f"{' <b>' + r['error'] + '</b>' if r.get('error') else ''}<br><span class=boxes>{boxes}</span><br><img src='{r['strip']}'></div>"
                        f"<video src='{r['mp4']}' controls loop muted playsinline preload=metadata></video></div>")
    html.append("""<script>
const KEY='picks:'+location.pathname;
function collect(){const p={};document.querySelectorAll('h2[id]').forEach(h=>{const id=h.id;const r=document.querySelector(`input[name='pick_${id}']:checked`);
 const n=document.getElementById('note_'+id);const props={};document.querySelectorAll(`input.prop[data-pair='${id}']`).forEach(b=>{if(b.checked){(props[b.dataset.tag]=props[b.dataset.tag]||{})[b.dataset.k]=true;}});
 if((r&&r.value)||(n&&n.value)||Object.keys(props).length)p[id]={best:r?r.value:'',note:n?n.value:'',props:props};});return p;}
function save(){try{const c=collect();localStorage.setItem(KEY,JSON.stringify(c));document.getElementById('status').textContent='saved locally '+new Date().toLocaleTimeString();document.getElementById('preview').textContent=JSON.stringify(c,null,1);}catch(e){}}
function restore(){try{const p=JSON.parse(localStorage.getItem(KEY)||'{}');for(const id in p){const r=document.querySelector(`input[name='pick_${id}'][value='${p[id].best}']`);if(r)r.checked=true;
 const n=document.getElementById('note_'+id);if(n&&p[id].note)n.value=p[id].note;const pr=p[id].props||{};for(const tag in pr){for(const k in pr[tag]){const b=document.querySelector(`input.prop[data-pair='${id}'][data-tag='${tag}'][data-k='${k}']`);if(b)b.checked=true;}}}}catch(e){}}
function exportPicks(){const blob=new Blob([JSON.stringify({date:new Date().toISOString(),page:'theme_anchors',picks:collect()},null,2)],{type:'application/json'});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='theme_anchors_picks.json';a.click();document.getElementById('status').textContent='theme_anchors_picks.json downloaded';}
restore();
</script>""")
    (out / "index.html").write_text("\n".join(html))


def write_sheet_md(out, sheet, picks):
    picks = (picks or {}).get("picks", {})
    md = [f"# Theme anchors — {sheet['date']}", "",
          "| pair | variant | class | method | edge_ratio | warping | feat_floor | laplace_floor | contrast_floor | dissolve_fit | motion_share | wall s |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for pair, row in sheet["pairs"].items():
        for tag, r in row["variants"].items():
            g = r.get("goal") or {}
            md.append(f"| {pair} | {tag} | {r.get('class')} | {r.get('method')} | {r.get('edge_ratio')} | {r.get('warping_error')} | "
                      f"{g.get('feat_floor')} | {g.get('laplace_floor')} | {g.get('contrast_floor')} | {g.get('dissolve_fit')} | {g.get('motion_share')} | {r.get('wall_s')} |")
    md += ["", "## Anchors (A → B, canvas px)", ""]
    for pair, row in sheet["pairs"].items():
        for tag, ab in (row.get("anchors_by_tag") or {"anchors_alpha": {"anchors": row["anchors"], "why": row["why"]}}).items():
            md.append(f"- {pair} `{tag}`: {ab['why']} — `" + "; ".join(",".join(f"{v:g}" for v in a) for a in ab["anchors"]) + "`")
    if picks:
        md += ["", "## Owner picks (theme_anchors_picks.json)", "", "| pair | closer | note | boxes (one picture / transforms / nothing invented) |", "|---|---|---|---|"]
        for pair in sheet["pairs"]:
            pk = picks.get(pair) or {}
            props = pk.get("props") or {}
            boxes = "; ".join(f"{tag}: " + "/".join("yes" if v.get(k) else "no" for k in ("one_picture", "transforms", "not_invented")) for tag, v in props.items())
            md.append(f"| {pair} | {pk.get('best', '')} | {(pk.get('note') or '').replace('|', '/')} | {boxes} |")
    (out / "sheet.md").write_text("\n".join(md) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anchors", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="")
    ap.add_argument("--seconds", type=float, default=2.0)
    ap.add_argument("--max-long", type=int, default=1920)
    ap.add_argument("--page-only", action="store_true")
    ap.add_argument("--picks", default="")
    ap.add_argument("--tag", default="", help="render ONLY the anchored variant under this tag (e.g. anchors_auto, anchors_falloff)")
    ap.add_argument("--extra", default="", help="extra CLI args for that variant, e.g. '--anchor-falloff 0.2'")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    spec = json.loads(Path(a.anchors).read_text())
    sheet_path = out / "sheet.json"
    sheet = json.loads(sheet_path.read_text()) if sheet_path.exists() else {"date": time.strftime("%Y-%m-%d"), "pairs": {}}
    variants = {a.tag: a.extra.split()} if a.tag else {"flat": [], "anchors_alpha": []}
    if not a.page_only:
        for pair, cfg in spec.items():
            if a.only and pair not in a.only.split(","):
                continue
            if not cfg.get("anchors") or len(cfg["anchors"]) < 3:
                print(f"  {pair}: fewer than 3 anchors, skipped", flush=True)
                continue
            rows = render(pair, cfg["anchors"], out, a.seconds, a.max_long, variants)
            canvas = next((r["canvas"] for r in rows.values() if r.get("canvas")), None)
            row = sheet["pairs"].setdefault(pair, {"anchors": cfg["anchors"], "why": cfg.get("why", ""), "canvas": canvas, "variants": {}})
            row["variants"].update(rows)
            row.setdefault("anchors_by_tag", {})
            for tag in rows:
                if "anchors" in tag:
                    row["anchors_by_tag"][tag] = {"anchors": cfg["anchors"], "why": cfg.get("why", "")}
            sheet_path.write_text(json.dumps(sheet, indent=1))
    picks = json.loads(Path(a.picks).read_text()) if a.picks else None
    write_page(out, sheet, picks)
    write_sheet_md(out, sheet, picks)
    print(f"wrote {out / 'index.html'}, {out / 'sheet.md'}")


if __name__ == "__main__":
    sys.exit(main())
