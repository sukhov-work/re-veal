<!-- Provenance: written by an Opus 5.5 subagent (the mattes track, 2026-10-20 about 23:20; 214 mattes on eight photos) of the Claude Code session of 2026-10-20 (the round-12 session; DECISIONS 2026-10-20), copied verbatim from benchmarks/runs/2026-10-20/agents/mattes_r12.md (sha256 fb2d915140d7da27) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"); folded into the round-12 held-out renders; the planner's blind brief. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

## Findings: mattes_r12 (ViTMatte small, CPU, 2026-10-20)

All 214 elements of the eight photos now have a soft matte under `benchmarks/runs/2026-10-17/mattes/<photo>/el_<id>.png` + `mattes.json`, the directory `MATTES` in `director_render.py:36` reads. No hard fallback occurred and nothing was downloaded: `run` verified the sha256 values in `MATTE_MANIFEST.json` and ran with HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1. No `--lattice-ids` was used, because none of the eight photos has a filled mask over a truss or spokes (checked by eye on the element-edge previews). Seven mattes on the sheets are wrong by more than their band; they are listed under Faults.

### Commands (one process at a time; band = round(1 % of the short side))
```
.venv/bin/python scripts/research/matte_source.py run <photo> --device cpu            # default: area_share >= 0.002
.venv/bin/python scripts/research/matte_source.py run <photo> --device cpu --ids ...  # second pass: every id below 0.002
.venv/bin/python scripts/research/matte_source.py sheet <photo> --ids ...
```
I ran the second pass so that small elements the planner names (the sun core in mismatch_4_S, the sun disc and the chimney in mismatch_4_F, the shirt circle in match_1_F) get a matte and no reader falls back to a hard mask. In `mattes.json`, `run_wall_s` and `model_load_s` hold the LAST pass's values; the first-pass values below come from the stdout logs.

### Runs
| photo | canvas | band px | default ids / wall s | below-share ids / wall s | process real s | slowest id |
|---|---|---|---|---|---|---|
| mismatch_4_S | 1920x1092 | 11 | 16 / 14.8 | 6 (3 4 9 13 17 20) / 0.8 | 19.4 | 21 water 6.4 s |
| mismatch_4_F | 1920x1092 | 11 | 15 / 17.3 | 13 (4 10-13 16 18-23 25) / 2.0 | 21.7 | 1 sky 7.1 s |
| mismatch_6_S | 1146x1524 | 11 | 30 / 24.6 | 8 (3 4 7 8 14 22 23 38) / 1.8 | 29.8 | 6 cloud 9.0 s |
| mismatch_6_F | 1146x1524 | 11 | 7 / 15.3 | 2 (4 7) / 0.5 | 20.8 | 1 sky 9.3 s |
| mismatch_1_S | 1444x1920 | 14 | 25 / 28.6 | 34 / 3.6 | 33.6 | 11 sky 7.1 s |
| mismatch_1_F | 1444x1920 | 14 | 38 / 30.6 | 25 / 3.2 | 35.3 | 1 sky 11.6 s |
| match_1_S | 1440x1920 | 14 | 3 / 33.0 | 0 | 40.1 | 1 wall 20.7 s |
| match_1_F | 1440x1920 | 14 | 4 / 27.8 | 2 (3 6) / 0.2 | 35.4 | 1 wall 14.4 s |
Model load: 2.6–3.9 s per process. Total default wall 192 s plus 12 s for the second passes.

### Element tables (label, group, area %; ids from `layers_v3/<photo>/layers.json`)
- **mismatch_4_S** (22): 1 sky 27.7 · 21 water 48.3 · 15 tree 6.8 (dark shoreline band) · 18, 19 earth 4.2, 0.9 · 22 wall 0.8 · 10 fountain 0.45 · buildings 2, 5, 6, 7, 8, 9, 11, 12, 13, 14, 16, 20 (0.07–2.0) · 3 sun 0.16 · 4 "boat" 0.08 (the sun's core: a hole inside id 3) · 17 bridge 0.07 (thin, 15 px tall).
- **mismatch_4_F** (28): 1 sky 45.0 · 27 sea 32.5 · 24 building 8.7 (the whole skyline with cranes and pylons) · 9 "sun" 4.5 (the glow around the disc, with a hole at the disc) · 19 "street lamp" 0.08 (the sun disc) · 21 "tower" 0.08 (the chimney under the sun) · 20, 23 chimneys · 26 bridge 0.69 · 28 earth · 7, 16, 25 buildings · 16 clouds (2–6, 8, 10–15, 17, 18) · 22 tree.
- **mismatch_6_S** (38, day city): 1 sky 14.7 plus sky patches 7, 10, 11, 15, 22, 25 · clouds 2 (22.6), 6 (20.9), 9 (8.6), 5 (5.5) and 3, 4, 8, 12, 13, 14, 19, 30 · buildings 16–18, 20, 21, 24, 26–29, 31–34, 37, 38 (17 at 5.4 and 28 at 5.2 are the largest) · 35 tree 0.76 · 36 wall · 23 "street lamp" 0.10 (a pole on building 17's facade; thin).
- **mismatch_6_F** (9, night): 1 sky 67.1 (the stars are inside it; there is no star element) · 2 "building" 7.5 (a roof eave) · 3 air conditioning unit 3.3 · trees 5 (12.6), 8 (5.7), 9 (3.3), 4 (0.06) · 6 "moon" 0.28 (out-of-focus leaves at the left edge, not a moon) · 7 sky 0.14.
- **mismatch_1_S** (59): 1 sky 29.6, 11 sky 12.9, 17 sky 4.3 · clouds 6 (16.7), 12 (4.9), 2, 3, 5 (the cirrus streak), 10, 13, 14, 18 and 30 small fragments · 24 building 14.6 (the tower, with roof masts) · 34 building 1.3 · 15 small buildings, 7 trees/plants, 55 wall, 57 signboard, 58 car, 59 road, 40 air unit.
- **mismatch_1_F** (63): 1 sky 36.6, 12 sky 5.6 · clouds 4, 7 (the lit cumulus, 3.5), 9, 11 (5.6), 2, 5, 6 and 5 small ones · 19 building 14.8 (the brick block) · 31 more buildings · trees 33 (spruce, 3.2), 51 (3.8), 56 (2.5), 54 and 11 small trees/plants · 63 wall.
- **match_1_S** (3): 1 wall 52.9 · 2 person 46.9 · 3 "animal" 0.20 (a tiger print on the shorts, a hole in id 2).
- **match_1_F** (6): 1 wall 52.1 · 2 person 47.2 · 3 "moon" 0.05 (the white circle in the shirt print) · 4, 5, 6 "animal" (shorts print). Each is a hole in id 2.

### What the planner needs (element-map geometry, measured on `layers.npz`)
- **mismatch_4 sun.** S: disc = ids 3 ∪ 4, bbox [898, 188, 981, 265], centroid (940.7, 226.1), 4972 px; the luma ≥ 245 blob is 4574 px with r 38 px. F: disc = id 19, bbox [936, 437, 983, 483], centroid (959.1, 459.7), r 23 px in the mask; the luma ≥ 245 blob has r 32 px, bbox [929, 430, 996, 488], and the matte above 0.5 covers 3232 px against the blob's 3207. F glow = id 9, bbox [677, 307, 1220, 565], centroid (953.9, 429.6). The chimney (id 21, bbox [952, 489, 973, 640]) stands directly under the F disc.
- **mismatch_4 water and horizon.** Neither table has a reflection element: the sun's column of light is inside water id 21 (S) and sea id 27 (F). The water's top row has p10/median/p90 of 510/545/675 in S and 703/736/769 in F. The sky's bottom row has a median of 315 in S (buildings cut into it) and 628 in F; the F skyline id 24 has its top at median 632.
- **mismatch_6.** S is a day city under cumulus; F is a night sky with trees and an AC unit under an eave. The two photos share no object. S sky = 1, 7, 10, 11, 15, 22, 25 (298 k px); clouds = 1.07 M px; building tops at median row 1173. F sky = 1 (stars inside, no star element); trees 4, 5, 8, 9 with tops at median row 1207; eave = 2; AC = 3.
- **mismatch_1.** City top (median row): S 1499 (ids 24, 32, 34, 44), F 1140. The sky/cloud bottom matches it: S 1502, F 1136. The horizon is about 360 rows apart between the two photos.
- **match_1.** Person = id 2 in both photos: S bbox [183, 109, 1254, 1919], centroid (710.3, 1177.5); F bbox [119, 81, 1197, 1919], centroid (649.7, 1157.6). Union with the print ids (S: 3; F: 3, 4, 5, 6) or the person shows holes. Background = wall id 1 alone (grey wall + white pillar).

### Faults seen on the sheets (by eye; T43: a mask wrong by more than the band stays wrong)
1. mismatch_4_S id 17 bridge: the matte keeps only the left ~half of the hard mask (matte sum / mask area 0.32). The bridge is dark on dark water.
2. mismatch_4_S id 4 (sun core): the matte fills the whole dilated band (ratio 2.28, ring 0.97). Use it only together with id 3 via `np.maximum`; then it matches the bright disc.
3. mismatch_4_F id 2 cloud: SAM 3 gave a box-shaped mask over a streaky cloud; the matte is a soft box. Clouds 3 and 14 share this shape on the overview.
4. mismatch_6_S id 2 cloud and mismatch_1_F id 11/12: the cloud-versus-sky split runs through continuous cloud, so a sky key that uses these ids cuts a cloud in two.
5. mismatch_1_F id 19 building: the hard mask includes a strip of distant city above the brick roof; the matte keeps it.
6. mismatch_1_S id 24: the roof masts are mostly lost (2–4 px wide; the band softens them to grey or cuts them).
7. match_1 id 2 person: the flyaway hair strands past the mask are cut (soft share 0.125 S, 0.105 F); the outline is clean otherwise.
Mechanical flags (matte sum / mask area outside 0.8–1.25): 7 ids on 4_S, 10 on 4_F, 6 on 6_S, 1 on 6_F, 14 on 1_S, 12 on 1_F, none on match_1; most are small cloud or sky fragments.

### Confidence: 75 %
The files, wall times, geometry and mass ratios are measured. The fault list comes from 46 sheet rows and 3 zoom crops, not from every element. Whether these mattes look clean in a rendered clip is UNVERIFIED (the renderer was not run, by instruction).

### Gaps
- The lattice trimap was not probed; I judged by eye that no element needs it. The mismatch_6_F tree crowns show no sky between the leaves in their mattes.
- One sheet per photo is kept (`<photo>/sheet.jpg`); the hair and bridge zoom crops are in scratch only.
- Determinism was not re-checked on these photos (the 2026-10-18 report measured it on two elements).
- Several mislabels (the sun disc as "street lamp", the sun core as "boat", leaves as "moon", a shirt circle as "moon") come from the layer tables and were left as they are.
