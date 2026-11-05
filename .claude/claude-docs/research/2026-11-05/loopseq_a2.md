<!-- provenance: copied verbatim on 2026-11-05 from benchmarks/runs/2026-11-05/studio/agents/loopseq_a2.md (gitignored), the report of the research-script subagent (Opus 5.5, max effort) of the 2026-11-05 session; a research artifact whose claims carry the author's own confidence and gaps; not re-verified at the copy except the md5 table's a2, s6 and angel-prep rows, which the main thread's standing watches confirm -->

# loop_seq.py additions for studio phase A2: windows, probe, measure, variants (2026-11-05)

Written by the research-script subagent of the 2026-11-05 session for the main thread, the session's lead agent, which
builds the studio: the local page over the loop flow (`.claude/claude-docs/STUDIO.md`). Phase A2 is the studio's second
build phase (`STUDIO.md` §9). Every number was measured on 2026-11-05 on this laptop. Paths are relative to the
repository root.

## Summary

All four additions are built in `scripts/research/loop_seq.py`, each off unless named, and
`scripts/research/plans/loops/SCHEMA.md` documents them in a dated section. The script went from md5
`eba20856bdccd17bbfedde0d7ae17b08` (1,787 lines) to `474d57b324c6c7b815aa13c4444862bb` (2,238 lines).

- Byte identity holds on the default paths: a2 still renders `c302623f…`, s6 `5908af3d…`, and the angel prep's stills
  and depth maps equal the recorded ones. Only clock keys and the script's md5 differ (section 1).
- The angel benchmark sheet (`.claude/claude-docs/benchmarks/2026-11-04-angel.md`) reproduces within its bars. The 27
  window offsets agree within 0.05 px (bar 0.2 px). RIFE's double-exposure share is 0.0223–0.0494 (sheet 0.022–0.049).
  The ring's top window moves at most 1.22 px sideways and 4.15 px up over a1–a3 (sheet 1.2 and 4.2).
- Asked of the main thread: copy the new help sentences and the SCHEMA section into the studio's stage registry, and
  pass `--order <seq>` to every `page` call. The sheet needs a correction: its "mirror edge" and "couch" readings
  measure a wall and a hoodie (section 3).
- Left out of `measure`: stall runs, jumps, the corner-box count and the bands-moving count (section 7).

## Terms

| term | meaning |
|---|---|
| a1–a5 | the five candidate loops of the angel portrait (two stills of two women, a ring light behind the left one); a2 and a3 were accepted on 2026-11-04 |
| s6 | the accepted seasons loop (three stills of one balcony view in three seasons) |
| the ring, the lock | the ring light, the gag object of the angel loop; `prep --lock-window` shifts each registered still so that three windows on the ring hold still |
| canvas | the frame the prep warps every still onto, before the common crop; frame 0 for the angel prep |
| the far prep | the angel prep with `--bg-depth 0.15 --min-inliers 25`, registered on far-field keypoints only |
| change matte | the pixels where two stills differ: a Lab distance above 14 on 2 px blurred copies (`change_matte`) |
| breath | a plan effect that zooms in and out once per loop about one point (1.8 % in a2) |
| stage registry | the studio's table of stages and knobs (`STUDIO.md` §2), whose sentences are copied from the scripts' `--help` and `SCHEMA.md` |

## 1. Byte identity, before and after

The protocol is the one of `.claude/claude-docs/research/2026-11-04/loopseq_flags.md`. Before the first edit the old
script rendered a2 (`scripts/research/plans/loops/angel_a2.json`) and s6 (`seasons_s6.json`) and ran the angel prep into
`benchmarks/runs/2026-11-05/loopseq/before/`. After the last edit the final script did the same into `after/`. The runs
went one at a time, and `ps` showed no other `loop_seq.py` process before the second set of runs. The angel prep is
`prep <the two angel stills, symlinked as 1.jpg and 2.jpg> --long 1920 --ref 0 --depth-maps --lock-window
"422,371,582,441;248,478,318,618;757,458,827,538"`. Both runs gave 467 inliers, the lock's shift (−4.93, +11.48) and the
crop [29, 0, 1395, 1770], and both runs' `k*.png` and `depth_k*.npy` are `cmp`-equal to
`benchmarks/runs/2026-11-04/angel/in/angel/`.

| output | before | after | equal |
|---|---|---|---|
| a2/loop.mp4 | `c302623f293eacd069218fd7518e0967` | `c302623f293eacd069218fd7518e0967` | yes |
| a2/loop.gif | `a97f9a2dd958dd4183e867c6e5edc16e` | `a97f9a2dd958dd4183e867c6e5edc16e` | yes |
| a2/sheet.jpg | `fc9b2fed09dffe40b0d3ef1e70ae236e` | `fc9b2fed09dffe40b0d3ef1e70ae236e` | yes |
| a2/plan.json | `9eac9d033b9caab756f0a96705f0d01c` | `9eac9d033b9caab756f0a96705f0d01c` | yes |
| a2/measure.json | `9a05ccd0e3afa9b015728f3ed82912ba` | `8e6591fd9f454e63e08f147ed3179112` | no (clock keys, below) |
| a2/frames.json | `cdb975c034476cc6a7a680f9f7afd837` | `83fcf713d1fd3123500dddc40c7c4549` | no (clock keys, below) |
| a2/measure.json without render_s, rife_seconds_per_frame, script_md5 | `a0d76c9ae52c0afd56842f932e77d9ba` | `a0d76c9ae52c0afd56842f932e77d9ba` | yes |
| a2/frames.json without each row's seconds | `b703197a5382f62e1ca6d20b9a2f265e` | `b703197a5382f62e1ca6d20b9a2f265e` | yes |
| s6/loop.mp4 | `5908af3d5300046579548848679b0cbb` | `5908af3d5300046579548848679b0cbb` | yes |
| s6/loop.gif | `20ece4651fff75657a6a562344be1a79` | `20ece4651fff75657a6a562344be1a79` | yes |
| s6/sheet.jpg | `579c98e6e48b31c50384edfcc2b4dbdf` | `579c98e6e48b31c50384edfcc2b4dbdf` | yes |
| s6/plan.json | `0adc2f257919af8de659affd72718204` | `0adc2f257919af8de659affd72718204` | yes |
| s6/frames.json | `836e7389917ff7358790deeacdf85e36` | `836e7389917ff7358790deeacdf85e36` | yes |
| s6/measure.json | `d2fef568dc7b7ea2b242d1dc67f5049f` | `2c0f158b8e0d3c6c4c1a093072485d4f` | no (clock keys, below) |
| s6/measure.json without render_s, rife_seconds_per_frame, script_md5 | `fc6fc04f4457b1615011d8d7d1bb7b79` | `fc6fc04f4457b1615011d8d7d1bb7b79` | yes |
| angel_prep/k0.png | `ccdb458cc6f25c5440640136e2862877` | `ccdb458cc6f25c5440640136e2862877` | yes |
| angel_prep/k1.png | `558688ea70079c924092838738f5caa1` | `558688ea70079c924092838738f5caa1` | yes |
| angel_prep/depth_k0.npy | `be5f197b14139379a68bf778378f7203` | `be5f197b14139379a68bf778378f7203` | yes |
| angel_prep/depth_k1.npy | `abc016300ed337e4e653cba82599b08f` | `abc016300ed337e4e653cba82599b08f` | yes |
| angel_prep/prep.json | `888376114bae25be2eafb7d62234f8bf` | `f27976c956e085082086c628ea4f4ef1` | no (date) |
| angel_prep/prep.json without date | `8220b91d87305442800b3d80bf846d77` | `8220b91d87305442800b3d80bf846d77` | yes |
| page, default, on the angel copy | `72dadc4f5ea4db16152fe0c7062a3f94` | `72dadc4f5ea4db16152fe0c7062a3f94` | yes |
| page with `--variants a1,a2,a3,a4,a5` | (no such flag) | `72dadc4f5ea4db16152fe0c7062a3f94` | equals the default |
| loop_seq.py | `eba20856bdccd17bbfedde0d7ae17b08` | `474d57b324c6c7b815aa13c4444862bb` | no (the change) |

The four raw files that differ hold a clock or the script's md5, and their key order is unchanged:
- a2's `measure.json`: `render_s` (66.7 → 56.5 s), `rife_seconds_per_frame` (2.62 → 2.2) and `script_md5`;
- s6's `measure.json`: `render_s` (73.6 → 63.7 s) and `script_md5`;
- a2's `frames.json`: each RIFE row's `seconds`;
- `prep.json`: `date`.

The page check ran on a copy of the angel run (`benchmarks/runs/2026-11-05/loopseq/angel_copy/`), with the recorded
title, intro, footer and notes and `--order angel`. Old and new script give `72dadc4f…`, the md5 of the page the owner
graded on 2026-11-04. An a2 render made right after the measures were factored out (`check_refactor/a2`) already gave
the same md5s for `measure.json` without its clock keys and for `frames.json` without `seconds`.

Gate 0 (`py_compile` of `reveal.py`, `harness.py`, `transitions.py`, `transitions_harness.py` and `loop_seq.py`)
passes. I did not run `harness.py`, `transitions_harness.py` or the two `check` commands: `git status` lists
`loop_seq.py` and `SCHEMA.md` as my only edits, and neither `reveal.py` nor `transitions.py` changed. `find -newer`
over the 2026-10-21, 2026-10-30, 2026-11-01 and 2026-11-04 run folders and `models/` printed nothing.

## 2. The four additions: command lines and JSON keys

Each addition is a new flag or a new command; reverting the two files removes all four. A malformed or missing input
prints one `FAILED: …` line on stderr and exits 2. I ran ten refusals, and each exited 2 with a line naming the input.
They cover a missing mp4, a malformed or duplicated window, a window outside the clip or frame 0, a frames.json of
another clip, `--ref` out of range, a malformed or foreign pair, and a folder without stills.

### 2.1 prep --windows

`loop_seq.py prep SEQ_DIR --out OUT [the existing flags] --windows "name:x0,y0,x1,y1;…"`

The windows are in frame-0 px before the crop (the px of `--lock-window`) and are measured, never applied.
- `prep.json`, top level, only with the flag: `"windows": {"<name>": [x0, y0, x1, y1]}`.
- `prep.json`, `frames[i]` for every frame i ≥ 1 that is not a cut: `"windows": {"<name>": {"box": [x0, y0, x1, y1],
  "box_canvas": [x0, y0, x1, y1] | null, "fits": {"<fit>": {"dx": float, "dy": float, "corr": float, "edge": bool}}}}`.
- The fits, in this order when present: `all` (every keypoint), `far` (`--bg-depth`), `chain` (through frame i − 1),
  `ecc` (the fallback or `--ecc-refine`), `final` (frame i as written, after the lock). SCHEMA.md defines each.
- `OUT/windows.jpg`: per measured frame a panel of frame 0 at 960 px with the boxes, the names and one arrow per fit,
  8 times the offset.

The prep reads `final` on its canvas before the crop: it compares frame i, warped as the prep writes it, with frame 0.
I measured two other readings and rejected both:
- Reading the cropped stills is how the sheet measured its locked row, and on the angel lock it gives the same values.
  On the far prep, though, the lamp-arm box starts at the crop's edge (x 53). There the cropped reading gave
  (+0.00, +5.82) with its peak on the search border, while the far fit itself reads (−1.82, +8.28).
- Warping frame i directly by the final map, the way the other fits are read, puts the ring top at +1.62 against the
  sheet's +1.4. That is 0.22 px off, over the 0.2 px bar: the prep writes a frame scaled below 0.98 (0.9605 here) by an
  area downscale before the warp, and the sheet read the written stills.

`edge` marks a read whose peak lies on the border of the ±30 px search; `_window_shift` then returns the border offset
as if it were measured. It fired on two of the four arbitrary seasons boxes (`top`, correlation −0.68, and frame 2's
`left`) and on none of the angel windows.

### 2.2 probe

`loop_seq.py probe PREP_DIR --out DIR [--long 960] [--pairs "i,j;k,l"]`

- Files: `DIR/probe_<i>_<j>_<rife|morph|dissolve>.jpg`, `DIR/crops/<i>_<j>_k<i>_face<k>.jpg`,
  `DIR/crops/<i>_<j>_k<j>_face<k>.jpg`, `DIR/crops/<i>_<j>_<method>_t<t>_face<k>.jpg`, `DIR/probe.json`.
- `probe.json` top level: `prep`, `long`, `size`, `t`, `matte` {`thr`, `grow`, `feather`, `min_share`}, `rife_version`,
  `rife_skipped`, `faces_model`, `pairs`, `seconds`, `script_md5`.
- Per pair: `a`, `b`, `matte_share`, `faces` [{`box`, `a`, `b`}], `methods` {`rife` | `morph` | `dissolve`:
  {`strip`, `flow` (morph only), `frames`: [{`t`, `dexp`, `dexp_frame`, `step_a`, `step_b`, `seconds` (rife only),
  `crops`}]}}.
- stdout: `{"pairs", "size", "rife_skipped", "dexp": {"<method>": [min, max]}}`.

The skip paths ran through a wrapper (`scratchpad/lsq/probe_skip.py`) that points `rife_probe` at other model paths and
touches no real file. A missing manifest, a manifest whose sha256 values are wrong, and a missing YuNet model each
exit 0: the first two skip the RIFE strip with the reason in `rife_skipped`, the third writes no crops. The real
`RIFE_MANIFEST.json` kept md5 `a8a3b8ebd1e0d69dbb1a1485351ddc7a`.

### 2.3 measure

`loop_seq.py measure MP4 --out DIR [--frames-json PATH] [--window "name:x0,y0,x1,y1;…"] [--ref 0] [--margin 30]`

- `measure.json` keys, in order: `mp4`, `frames_json`, `frames`, `fps`, `canvas`, `seconds`, `step_mean`, `step_max`,
  `step_max_at`, `seam_step`, `steps`, `faces_per_frame`, `faces_keyframes`, `generated_frames`, `generated_share`,
  `dexp_max`, `rife_seconds_per_frame`, `md5_mp4`.
- With `--window` it adds `stability_ref`, `stability_margin`, `stability` {"<name>": [[dx, dy, corr], …]} and
  `stability_max` {"<name>": {`box`, `dx_max`, `dx_max_at`, `dy_max`, `dy_max_at`, `corr_min`, `edge_frames`}}.
- The last key is `script_md5`.
- The five keys that need frames.json (`faces_keyframes`, `generated_frames`, `generated_share`, `dexp_max`,
  `rife_seconds_per_frame`) are null without `--frames-json`.
- stdout: the main measures and `stability_max` on one line.

`render` now calls the same two functions, `decode_mp4` and `measures_of`, in a new section of the script, and builds
its `measure.json` in the old key order. On the five recorded angel candidates `measure` with `--frames-json` gives the
16 shared keys equal to the render's own `measure.json`.

### 2.4 page --variants (backlog row T76 of `.claude/skills/reveal/references/tracked-backlog.md`)

`loop_seq.py page --root ROOT --out HTML [the existing flags] --variants a2,a3`

The page adds no JSON key. On the angel copy the default page and `--variants a1,a2,a3,a4,a5` both give `72dadc4f…`;
`--variants a2,a3` gives `4a9b0f263e66f40145b61207ea04bec4` with a2 then a3; `--variants "a3, a2"` gives
`2d0bee16fcd766abcb3222cd287002cd` with a3 then a2. `--variants a2,zz` printed `FAILED: page --variants: zz is not a full
render of angel: no benchmarks/runs/2026-11-05/loopseq/angel_copy/angel/zz/measure.json`, exited 2 and wrote no page.
A name given twice and `round1a` (a folder without measure.json) were refused the same way. One list applies to every
sequence on the page.

## 3. The windows against the sheet's registration table

The boxes, in frame-0 px, come from `windows_canvas.json` of the 2026-11-04 scratch probe (canvas px of the far prep)
plus that prep's crop origin, x 53. The three ring boxes equal the lock windows, and the ring top lands on the sheet's
(393, 371, 553, 441) on the locked canvas. They are recorded here because the scratchpad is temporary:

```
ring_top:422,371,582,441;ring_left:248,478,318,618;ring_right:757,458,827,538;lamp_arm:53,560,203,760;mirror_edge:534,300,834,360;exit_sign:1084,20,1284,130;couch_right:1134,900,1387,1300;laptop_edge:634,1520,1034,1620;left_face:334,700,594,1000;right_face:884,580,1134,900
```

I looked at the boxes on `windows.jpg` and on 1:1 crops of frame 0. The ring boxes sit on the ring's top, left and
right arcs; the lamp arm, exit sign, laptop and face boxes sit on those objects. Two boxes do not hold what their names
say:
- `couch_right` covers the right woman's grey hoodie, with the couch only at its right edge.
- `mirror_edge` covers plain wall about 75 px below the mirror's lower edge, which lies outside its ±30 px search.

The sheet's prose quotes both under the lock ("the mirror edge 13 px", "the couch 13 px"); they measure a nearly
textureless stretch of wall and the hoodie. `mirror_edge` is outside the sheet's table and reads (+1.43, +12.89) under
`final`.

Commands: `windows/angel_lock` is the sequence's prep plus `--windows`; `windows/angel_far` uses `--bg-depth 0.15
--min-inliers 25` without the lock. Largest difference over the 27 cells: 0.05 px.

| window | fit | sheet dx, dy | measured dx, dy | corr | largest difference px |
|---|---|---|---|---|---|
| ring_top | all keypoints (`all`) | +6.1, -12.6 | +6.14, -12.59 | 0.992 | 0.04 |
| ring_left | all keypoints (`all`) | +4.7, -10.9 | +4.70, -10.90 | 0.993 | 0.00 |
| ring_right | all keypoints (`all`) | +4.0, -11.0 | +3.96, -10.97 | 0.976 | 0.04 |
| lamp_arm | all keypoints (`all`) | +4.0, -12.0 | +3.96, -12.00 | 0.981 | 0.04 |
| exit_sign | all keypoints (`all`) | +1.6, +15.6 | +1.58, +15.62 | 0.977 | 0.02 |
| couch_right | all keypoints (`all`) | +0.6, +1.2 | +0.64, +1.19 | 0.969 | 0.04 |
| laptop_edge | all keypoints (`all`) | -9.1, -10.2 | -9.13, -10.16 | 0.886 | 0.04 |
| left_face | all keypoints (`all`) | -18.0, -9.9 | -17.95, -9.86 | 0.840 | 0.05 |
| right_face | all keypoints (`all`) | -0.9, +0.4 | -0.86, +0.37 | 0.958 | 0.04 |
| ring_top | far field (`far`) | +5.3, -7.3 | +5.25, -7.32 | 0.994 | 0.05 |
| ring_left | far field (`far`) | +0.2, +0.3 | +0.15, +0.27 | 0.993 | 0.05 |
| ring_right | far field (`far`) | +2.0, -6.1 | +2.04, -6.10 | 0.976 | 0.04 |
| lamp_arm | far field (`far`) | -1.8, +8.3 | -1.82, +8.28 | 0.970 | 0.02 |
| exit_sign | far field (`far`) | -0.4, +1.4 | -0.35, +1.39 | 0.975 | 0.05 |
| couch_right | far field (`far`) | -5.0, -1.7 | -4.98, -1.66 | 0.923 | 0.04 |
| laptop_edge | far field (`far`) | +4.1, -19.0 | +4.06, -19.03 | 0.867 | 0.04 |
| left_face | far field (`far`) | -13.6, +3.2 | -13.60, +3.18 | 0.863 | 0.02 |
| right_face | far field (`far`) | -2.4, +3.1 | -2.39, +3.05 | 0.960 | 0.05 |
| ring_top | all keypoints + ring lock (`final`) | +1.4, -1.1 | +1.40, -1.09 | 0.994 | 0.01 |
| ring_left | all keypoints + ring lock (`final`) | -0.4, +0.6 | -0.40, +0.59 | 0.993 | 0.01 |
| ring_right | all keypoints + ring lock (`final`) | -0.1, +2.1 | -0.11, +2.14 | 0.978 | 0.04 |
| lamp_arm | all keypoints + ring lock (`final`) | -2.3, +0.6 | -2.25, +0.63 | 0.980 | 0.05 |
| exit_sign | all keypoints + ring lock (`final`) | -3.4, +27.1 | -3.39, +27.09 | 0.977 | 0.01 |
| couch_right | all keypoints + ring lock (`final`) | -4.5, +13.0 | -4.53, +13.03 | 0.972 | 0.03 |
| laptop_edge | all keypoints + ring lock (`final`) | -13.0, +1.1 | -13.00, +1.11 | 0.887 | 0.01 |
| left_face | all keypoints + ring lock (`final`) | -23.0, +1.6 | -23.03, +1.63 | 0.843 | 0.03 |
| right_face | all keypoints + ring lock (`final`) | -5.7, +11.8 | -5.66, +11.82 | 0.960 | 0.04 |

Under the lock, `final` holds the three ring windows within 2.14 px, the sheet's "within 2.1 px". Two more runs
exercised the other fits:
- `windows/angel_far_ecc` (`--ecc-refine`) adds an `ecc` entry: ring top (+1.38, −12.29) under `ecc`.
- `windows/seasons` reran the recorded three-still seasons prep with four arbitrary boxes. Frame 2 chains through
  frame 1, the canvas is frame 2, and the all-keypoint fit of frame 2 is rejected (31 inliers). It wrote `chain` and
  `final` entries and a log line for the missing `all`, and its stills are `cmp`-equal to the recorded prep.

## 4. The probe's numbers

The probe's double-exposure share is the render's own measure (`rife_probe.dexp_share`): the share of pixels within
20 levels of the two stills' mean and more than 20 from each. `dexp` reads it inside the change matte, `dexp_frame`
over the whole frame. The unlocked prep (`probe/angel_unlocked_prep`, `prep --long 1920` without the lock) has stills
`cmp`-equal to the 2026-11-04 scratch prep `angel_subject` that the sheet's probe read. The probe ran at `--long 960`.

| prep | method | dexp inside the change matte, t 0.25 / 0.5 / 0.75 | dexp over the whole frame | step to still 0 / still 1 at t 0.5 |
|---|---|---|---|---|
| unlocked, 744×960, change matte 30.4 % | rife | 0.0250 / 0.0494 / 0.0223 | 0.0080 / 0.0166 / 0.0070 | 6.21 / 5.82 |
| unlocked, 744×960, change matte 30.4 % | morph | 0.0191 / 0.0552 / 0.0159 | 0.0059 / 0.0193 / 0.0050 | 5.96 / 6.00 |
| unlocked, 744×960, change matte 30.4 % | dissolve | 0.0008 / 0.1801 / 0.0008 | 0.0002 / 0.0599 / 0.0002 | 5.23 / 5.24 |
| locked, 740×960, change matte 47.5 % | rife | 0.0413 / 0.0611 / 0.0341 | 0.0203 / 0.0303 / 0.0164 | 8.54 / 8.44 |
| locked, 740×960, change matte 47.5 % | morph | 0.0233 / 0.0650 / 0.0245 | 0.0113 / 0.0323 / 0.0118 | 8.41 / 8.51 |
| locked, 740×960, change matte 47.5 % | dissolve | 0.0012 / 0.2310 / 0.0012 | 0.0006 / 0.1131 / 0.0006 | 6.87 / 6.88 |

RIFE on the unlocked prep gives 0.0223–0.0494, the sheet's 0.022–0.049, on a change matte of 30.4 % of the frame
(the sheet: 30 %).
The morph's flow is `homography+dis`, as the sheet names it. YuNet finds 2 faces at 960 px; the third face of k0 at
full size, a cookie's print, is too small there. At t 0.5 the dissolve's face crop shows a doubled mouth while RIFE's
and the morph's do not (looked at on `probe/angel_locked/crops/0_1_*_t0.5_face0.jpg`). On the locked prep the
whole-frame share at t 0.5, 0.0303, is close to a2's recorded `dexp_max` of 0.0309 at full size.

## 5. The ring's stability on the angel candidates

`measure` with the window `ring_top:393,371,553,441` (canvas px) and `--frames-json`, on each recorded
`benchmarks/runs/2026-11-04/angel/angel/<candidate>/loop.mp4`:

| candidate | max abs dx px (frame) | max abs dy px (frame; signed) | lowest corr | sheet |
|---|---|---|---|---|
| a1 | 1.22 (38) | 3.97 (24; −3.97) | 0.991 | at most 1.2 and 4.2 over a1–a3 |
| a2 | 1.18 (13) | 3.96 (26; −3.96) | 0.987 | at most 1.2 and 4.2 over a1–a3 |
| a3 | 1.18 (13) | 4.15 (26; −4.15) | 0.986 | at most 1.2 and 4.2 over a1–a3 |
| a4 | 0.79 (52) | 3.97 (42; −3.97) | 0.987 | 0.8 and 4.0 |
| a5 | 1.14 (41) | 3.56 (25; −3.56) | 0.982 | 1.1 and 3.6 |

The negative dy is up, at the breath's peak (frames 24–26), as the sheet says. Every frame's peak lay inside the
search. The sheet's script used a 12 px search; `--margin 12` and the default 30 give the same numbers on a2.

On a2 the left ring window moves at most 5.10 px sideways (frame 24) and 0.67 px vertically. The plan's breath zooms
1.8 % about a point 257 px to the window's right, which alone moves the window 4.6 px [inference from the plan]. The
right ring window reads up to 5.81 px sideways and 7.30 px vertically at frame 37. Its series jumps by whole pixels
between neighbouring frames (frame 24: −1.0, −6.0; frame 26: +1.0, −3.0). I read that as the match sliding along a
near-vertical stretch of the arc [inference]; the top and left windows change smoothly. A stability window needs texture in both directions.

## 6. Wall times

| command | wall |
|---|---|
| `prep` of the angel pair with the lock, without `--windows` | 4.7 s |
| the same with `--windows` (10 windows) | 4.5 s |
| `prep --bg-depth 0.15 --min-inliers 25 --windows` (10 windows, an extra all-keypoint fit) | 5.2 s |
| `probe` at 960 px, one pair, RIFE loaded | 3.1 s |
| `measure` on a2 (50 frames, 3 windows, `--frames-json`) | 2.2 s |
| `page --variants a2,a3` | 0.6 s |
| protocol runs before the edit: a2, s6, prep | 73 s, 93 s, 5 s |
| protocol runs after the edit: a2, s6, prep | 62 s, 82 s, 6 s |

## 7. Gaps and limits

- Reproduction: every number of the sheet's registration table, the probe's dexp range and the ring-top stability
  reproduced within its bar. The sheet's two prose readings for the couch and the mirror reproduce as numbers, but
  their boxes hold the right woman's hoodie and plain wall (section 3).
- `measure` does not compute stall runs (steps below 0.3 while motion is open) or jumps (a step above 3 times its
  neighbours). It also lacks the still-frame count and the corner-box count (the pixels of a corner box that differ
  between the last frame and frame 0, a residue check of the seasons loop). The studio's research distillation
  (`.claude/claude-docs/research/2026-11-04/trackB_distill.md`) lists them; the task's key list does not. The first
  three follow from `steps` and the bars in `.claude/skills/reveal/references/loops.md` §6; the corner box needs a box
  definition.
- The count of bands moving at once is absent too: the number of sheets in flight per frame in a seasons plan (s9, a
  later seasons plan, had 8 or more on 107 of 269 frames). It counts the plan's schedule (each sheet's displacement
  `d` in `frames.json`), so it does not fall out of the decoded-frame code.
- `prep --windows` refuses a box outside frame 0 after the out folder exists, so a refusal leaves an empty folder. A
  cut frame gets no `windows` entry; when every frame is a cut, no `windows.jpg` is written.
- The probe reads the change matte at its defaults (threshold 14), not a plan's `matte`.
- The tree holds edits by other agents of this session (`DECISIONS.md`, `AGENTS.md`, `.claude/settings.json` and six
  more); I did not touch them, and I did not commit.

## 8. Found, not changed

1. The render's face count catches `SystemExit` only. Without the YuNet model, `cv2.FaceDetectorYN.create` raises
   `cv2.error`, so a render exits 1 after writing `loop.mp4`, `loop.gif` and `sheet.jpg` and before `measure.json`,
   `frames.json` and `plan.json`. Shown with `measure` and the model path pointed elsewhere (exit 1, `cv2.error`); the
   render calls the same `measures_of`, so the render's failure is an inference, not a run.
2. `page` without `--order` reads every folder of the root except `in`, `probe_morph`, `probe_rife` and `agents`. On
   the angel run (`drafts/`, `round1a/`) it exits 1 on `in/drafts/prep.json` after writing `in/angel/keys.jpg`. The
   studio should pass `--order <seq>` on every call.
3. `_window_shift` returns the search border's offset when the content lies beyond its ±30 px search, and the lock
   applies that value as a measurement. The new outputs flag it (`edge`); the lock is unchanged.
4. `rife_probe.dexp_share` measures closeness to the stills' mean, so it misses a dissolve's ghost away from t 0.5:
   0.0008 at t 0.25 and 0.75 against 0.1801 at t 0.5 on the unlocked pair. A render's `dexp_max` can therefore
   understate double exposure on frames far from mid-leg. `rife_probe`'s docstring describes a `dexp_t` variant
   with the blend at t as the reference.
5. `frames_morph` writes each row's `t` as the frame's position in the leg (0.25, 0.5 and 0.75 for three
   in-betweens). The morph itself follows the preset's sine ease, so its warp and mix sit at 0.15, 0.5 and 0.85. A
   morph leg's `t` in `frames.json` is therefore the frame position, not the morph's progress.

## Appendix: commands and folders

The protocol's commands, from the repository root (`$R` is `benchmarks/runs/2026-11-05/loopseq/before` or `…/after`):

```
.venv/bin/python scripts/research/loop_seq.py render scripts/research/plans/loops/angel_a2.json --out $R/a2
.venv/bin/python scripts/research/loop_seq.py render scripts/research/plans/loops/seasons_s6.json --out $R/s6
.venv/bin/python scripts/research/loop_seq.py prep <folder of 1.jpg, 2.jpg> --out $R/angel_prep --long 1920 --ref 0 --depth-maps --lock-window "422,371,582,441;248,478,318,618;757,458,827,538"
.venv/bin/python scripts/research/loop_seq.py page --root benchmarks/runs/2026-11-05/loopseq/angel_copy --out $R/page_default.html --notes benchmarks/runs/2026-11-05/loopseq/angel_copy/notes.json --order angel --title <recorded> --intro <recorded> --footer <recorded>
```

The page's title, intro and footer are read from `benchmarks/runs/2026-11-04/angel/index.html` (`<title>` and the first
and last `<p class='mut'>`, html-unescaped).

All outputs are under `benchmarks/runs/2026-11-05/loopseq/` (gitignored):
- `before/`, `after/`: the protocol runs, `summary.txt` (exit codes, walls, script md5 per run) and `md5.json`;
- `check_refactor/a2`: the a2 render right after the measures were factored out;
- `angel_copy/`: the copy of `benchmarks/runs/2026-11-04/angel` the page ran on;
- `windows/`, `probe/`, `measure/`, `page/`, `errors/`, `timing/`: the runs of sections 2–6.

The scratch scripts live in
`/private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/d9082b8f-cf5b-4b41-ba3c-c8c2ee5b8bc6/scratchpad/lsq/`:
`run_proto.sh` (the protocol), `md5table.py` and `compare.py` (the md5 table), `run_page.sh` (the page with the recorded
title, intro and footer), `probe_skip.py` (the skip paths), `tables.py` (sections 3–5). The angel stills are read
through `…/scratchpad/lsq/angel/raw/1.jpg` and `2.jpg`, symlinks to
`/Users/yevhens/Downloads/Telegram Desktop/angel-portrait/PXL_20261104_103732636.PORTRAIT~2.jpg` and
`PXL_20261104_103736727.PORTRAIT~2.jpg`.
