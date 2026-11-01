#!/usr/bin/env python3
"""Generate a seasons plan of many narrow lateral bands from the accepted s6 (2026-11-01, round 4).
Usage: gen_seasons_bands.py OUT.json --seed 1 --bands 10 --stagger 11 --dur 100 --feather 80 [--layers]
Each band: a season in random order (early autumn, late autumn, summer at 0.4 / 0.4 / 0.2), a random side, a width
of 0.22-0.38 of the visible extent, a start at index x stagger, and (with --layers) a depth layer of the base still's
map (sky, far, mid, near, or all) so seasons cross by layer. All else is s6's: lateral motion, edge_depth, the objects,
the overlap, the crop. The plan is written out in full (hand-tunable; the seed is recorded in the title)."""
import argparse, json, random
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("--seed", type=int, default=1); ap.add_argument("--bands", type=int, default=10)
ap.add_argument("--stagger", type=int, default=11); ap.add_argument("--dur", type=int, default=100)
ap.add_argument("--feather", type=float, default=80.0); ap.add_argument("--layers", action="store_true")
ap.add_argument("--shadow", type=float, default=0.15); ap.add_argument("--edge-depth", type=float, default=120.0)
ap.add_argument("--base", default=str(Path(__file__).parent / "seasons_s6.json"))
a = ap.parse_args()
rng = random.Random(a.seed)
base = json.loads(Path(a.base).read_text()); st = json.loads(json.dumps(base["timeline"][1]))
LAYERS = [("sky", [-1.0, 0.06]), ("far", [0.04, 0.3]), ("mid", [0.26, 0.62]), ("near", [0.56, 2.0]), ("all", None)]
SKY_Y = [0, 1190]        # the sky layer also stops above the skyline (prep-canvas rows; the depth map cannot separate sky from the far buildings)
sheets = []
for i in range(a.bands):
    key = rng.choices([1, 2, 0], weights=[0.4, 0.4, 0.2])[0]
    side = rng.choice(["+", "-"])
    width = round(rng.uniform(0.22, 0.38), 3)
    lname, lay = rng.choices(LAYERS, weights=[1, 1, 1, 1, 1.5])[0] if a.layers else ("all", None)
    s = {"key": key, "side": side, "carry": 0.0, "width": width, "lag": i * a.stagger, "dur": a.dur, "name": f"b{i}_{['summer','early','late'][key]}_{lname}"}
    if lay: s["layer"] = lay
    if lname == "sky": s["layer_y"] = SKY_Y
    if key == 0: s["shadow"] = 0.0                                   # a summer band over summer shows only as its shadow: none
    sheets.append(s)
st["sheets"] = sheets; st["n"] = (a.bands - 1) * a.stagger + a.dur
st["feather"] = a.feather; st["shadow"] = a.shadow; st["shadow_from"] = "all"; st["edge_depth"] = a.edge_depth
base["timeline"][1] = st
base["title"] = (f"bands on s6: {a.bands} narrow lateral bands (0.22-0.38 of the frame) in random order (seed {a.seed}) carrying all three seasons, "
                 f"starting every {a.stagger} frames and each sweeping for {a.dur}, so about {min(a.bands, a.dur // a.stagger)} move at once; "
                 + ("each band limited to a depth layer of the scene (sky, far, mid, near, or all) so seasons cross by layer; " if a.layers else "")
                 + f"edges feathered over {a.feather:.0f} px and half-transparent where bands overlap; the depth bend {a.edge_depth:.0f} px; the objects, the crop and the lateral motion as in s6; summer is the base, so the loop closes when the last band leaves")
Path(a.out).write_text(json.dumps(base, indent=1))
print(json.dumps({"out": a.out, "n": st["n"], "sheets": [(s["name"], s["side"], s["width"], s["lag"]) for s in sheets]}))
