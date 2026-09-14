# Real-pair sheet, re-run 2026-09-14 — after TR2c (class B pan-and-zoom) and the `finish` canvas default

Run: `scripts/bench_transitions.py --out benchmarks/runs/2026-09-14 --reveal` (M3 Pro, OpenCV 5.0.0,
transitions canvas capped at 1920 px; the review page with strips, players and pick controls is
`benchmarks/runs/2026-09-14/index.html`, gitignored). Same twelve fixtures and five variants as
`2026-09-13-real-pairs.md`; two things changed since that sheet:

1. **TR2c (defect T13).** Class B no longer moves the whole frame by a similarity. Each frame zooms
   in 10 % about its salient blob and pans toward the other frame's blob as far as the zoom's slack
   allows (`pan A/B` in the table: the fraction of the center-to-center distance each frame
   travels; 1.00 on both means the blobs meet). No frame edge enters the canvas on any of the six
   class B pairs (min splat coverage 0.86; before, 9–52 % of a mid frame was one endpoint only).
   Pan fractions (morph 1 s): mismatch_1 0.20 / 0.87; mismatch_2 0.15 / 0.16; mismatch_3 0.06 / 0.06; mismatch_4 0.79 / 0.19; mismatch_5 0.15 / 0.34; mismatch_6 0.23 / 0.57.
2. **Canvas policy `finish`** (owner ruling 2026-09-14). Four canvases changed: match_5
   1518×1920 → 1438×1920 (89 inliers, 84.6 px median displacement; was 73 and 103.5 px),
   mismatch_2 730×800 → 602×800, mismatch_4 1920×1236 → 1920×1092, mismatch_6 1146×1528 → 1146×1524.

Unchanged: class routing (11 of 12 as labelled; mismatch_7 routes A by rule), endpoints 0 / 0 on all
60 runs, every run exit 0. Class A pairs render byte-identically to the 2026-09-13 code path
(hash check on the harness pair), so their rows differ from the earlier sheet only where the
canvas changed (match_5) or by wall time. `edge_ratio` on morph 1 s: match pairs 0.12–0.24,
mismatch pairs 0.13–0.66 (mismatch_6, day → night, 0.66; it was 0.52 with the whole-frame
similarity, and its flow-dissolve reads 1.04, the only value above 1 on a smooth preset).

## Owner review (2026-09-15, verbatim)
> regarding runs/2026-09-14 , i went through all and didn't notice much difference since first run ( at least it didn't get worse) , the only marginal improvement is mismatch_7 where you at least started to somewhat keep couple of focal buildings in between transitions , clouds are a mess though. other mismatches stayd more or less same  simple junky cross-dissolves  but at least you made it more subtle. Still none of the mismatch pairs can be accepted. Also same grading and remarks from first picks.json apply here for matches, as i said , if there are improvements they are marginal. For roma samples - create me full run with video transitions, it is very hard to judge low-res static frames

Reading of the record against this review:
- **mismatch_7 did not change.** It routes class A, so TR2c (a class B change) did not reach it; its
  five clips have the same quality basket as on 2026-09-13 and the morph 1 s mp4 has the same md5
  (`df5e516d…`) in both run folders. The improvement seen there is a difference in viewing, not in
  code. The clouds tearing is the TR2b case (certainty 0.053), now expected to be answered by the
  RoMa field (its certainty is low where content differs, so those regions dissolve in place).
- **The mismatched pairs, TR2c's target:** the frame border is gone and the motion is "more subtle",
  and the pairs stay "simple junky cross-dissolves"; none is accepted. E2 stays unmet. The object
  and theme correspondence the owner wants there is slice TR9, unchanged.
- **Matched pairs:** the 2026-09-14 picks and notes stand; class A was byte-identical by construction,
  so nothing could have changed except match_5's canvas.
- **Next review surface:** real clips from the RoMa field beside the DIS clips, six class A pairs,
  four field-using variants (`benchmarks/runs/2026-09-14/roma/index.html`, built by
  `scripts/research/compare_fields.py --render` and `--page`).

## Reveal align (native resolution)

| pair | mode | rc | method | inliers | rmse_px | ecc_rho | periph_ssim | residual | changed_% | confidence | wall s | error |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| match_1 | reshot | 0 | sift | 368 | 0.74 | 0.998 | 0.849 | False | 10.4 | 95 | 8.4 |  |
| match_2 | reshot | 0 | sift | 913 | 1.01 | 0.9971 | 0.884 | False | 26.2 | 90 | 2.5 |  |
| match_3 | reshot | 0 | sift | 1059 | 1.0 | None | 0.876 | False | 19.0 | 90 | 4.4 |  |
| match_4 | reshot | 0 | sift | 481 | 0.79 | 0.9461 | 0.539 | False | 28.3 | 94 | 6.4 |  |
| match_5 | reshot | 0 | sift | 121 | 0.67 | 0.9033 | 0.504 | False | 52.3 | 97 | 6.4 |  |
| mismatch_1 | reshot | 2 | None | None | None | None | None | None | None | None | 9.7 | FAILED: Could not find enough common detail between the two photos. They need to |
| mismatch_2 | reshot | 2 | None | None | None | None | None | None | None | None | 6.4 | FAILED: Could not find enough common detail between the two photos. They need to |
| mismatch_3 | reshot | 2 | None | None | None | None | None | None | None | None | 7.3 | FAILED: Could not find enough common detail between the two photos. They need to |
| mismatch_4 | reshot | 2 | None | None | None | None | None | None | None | None | 9.3 | FAILED: Could not find enough common detail between the two photos. They need to |
| mismatch_5 | reshot | 2 | None | None | None | None | None | None | None | None | 9.8 | FAILED: Could not find enough common detail between the two photos. They need to |
| mismatch_6 | reshot | 2 | None | None | None | None | None | None | None | None | 10.3 | FAILED: Could not find enough common detail between the two photos. They need to |
| mismatch_7 | reshot | 0 | sift | 78 | 0.89 | None | 0.701 | False | 34.2 | 92 | 14.7 |  |

## Transitions (`transitions.py pair`)

| pair | preset | rc | class | method | inliers | median_disp_px | certainty | pan A/B | canvas | frames | corr s | render s | wall s | warping_err | edge_ratio | max_step | endpoint |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| match_1 | morph_1s | 0 | A | homography+dis | 492 | 63.66 | 0.482 | - | 1440x1920 | 30 | 0.46 | 7.42 | 12.0 | 0.0064 | 0.2299 | 0.0131 | 0.0/0.0 |
| match_1 | flow-dissolve_1s | 0 | A | homography+dis | 492 | 63.66 | 0.482 | - | 1440x1920 | 30 | 0.48 | 7.28 | 11.9 | 0.0066 | 0.2288 | 0.013 | 0.0/0.0 |
| match_1 | snap-morph_1s | 0 | A | homography+dis | 492 | 63.66 | 0.482 | - | 1440x1920 | 30 | 0.5 | 6.91 | 11.5 | 0.0058 | 1.5482 | 0.0138 | 0.0/0.0 |
| match_1 | dissolve_1s | 0 | A | homography+dis | 492 | 63.66 | 0.482 | - | 1440x1920 | 30 | 0.5 | 4.38 | 9.1 | 0.0045 | 0.2587 | 0.0052 | 0.0/0.0 |
| match_1 | morph_3s | 0 | A | homography+dis | 492 | 63.66 | 0.482 | - | 1440x1920 | 90 | 0.49 | 21.56 | 26.6 | 0.0034 | 0.0629 | 0.0053 | 0.0/0.0 |
| match_2 | morph_1s | 0 | A | homography+dis | 899 | 140.79 | 0.806 | - | 896x1920 | 30 | 0.39 | 4.88 | 5.8 | 0.0109 | 0.1209 | 0.0492 | 0.0/0.0 |
| match_2 | flow-dissolve_1s | 0 | A | homography+dis | 899 | 140.79 | 0.806 | - | 896x1920 | 30 | 0.38 | 4.9 | 5.8 | 0.0108 | 0.1208 | 0.0493 | 0.0/0.0 |
| match_2 | snap-morph_1s | 0 | A | homography+dis | 899 | 140.79 | 0.806 | - | 896x1920 | 30 | 0.38 | 4.79 | 5.7 | 0.0082 | 1.5129 | 0.0507 | 0.0/0.0 |
| match_2 | dissolve_1s | 0 | A | homography+dis | 899 | 140.79 | 0.806 | - | 896x1920 | 30 | 0.38 | 2.57 | 3.5 | 0.006 | 0.0311 | 0.0087 | 0.0/0.0 |
| match_2 | morph_3s | 0 | A | homography+dis | 899 | 140.79 | 0.806 | - | 896x1920 | 90 | 0.38 | 14.22 | 15.3 | 0.0084 | 0.0363 | 0.0208 | 0.0/0.0 |
| match_3 | morph_1s | 0 | A | homography+dis | 986 | 38.46 | 0.41 | - | 1438x1920 | 30 | 0.57 | 7.88 | 8.9 | 0.0038 | 0.117 | 0.0061 | 0.0/0.0 |
| match_3 | flow-dissolve_1s | 0 | A | homography+dis | 986 | 38.46 | 0.41 | - | 1438x1920 | 30 | 0.54 | 7.93 | 8.9 | 0.0038 | 0.4785 | 0.0061 | 0.0/0.0 |
| match_3 | snap-morph_1s | 0 | A | homography+dis | 986 | 38.46 | 0.41 | - | 1438x1920 | 30 | 0.55 | 8.69 | 9.7 | 0.0037 | 1.7125 | 0.0069 | 0.0/0.0 |
| match_3 | dissolve_1s | 0 | A | homography+dis | 986 | 38.46 | 0.41 | - | 1438x1920 | 30 | 0.54 | 4.17 | 5.2 | 0.0031 | 0.0066 | 0.004 | 0.0/0.0 |
| match_3 | morph_3s | 0 | A | homography+dis | 986 | 38.46 | 0.41 | - | 1438x1920 | 90 | 0.54 | 24.44 | 25.7 | 0.0017 | 0.0558 | 0.0028 | 0.0/0.0 |
| match_4 | morph_1s | 0 | A | homography+dis | 295 | 15.12 | 0.652 | - | 1536x1920 | 30 | 0.67 | 8.2 | 9.7 | 0.0102 | 0.2446 | 0.016 | 0.0/0.0 |
| match_4 | flow-dissolve_1s | 0 | A | homography+dis | 295 | 15.12 | 0.652 | - | 1536x1920 | 30 | 0.64 | 8.11 | 9.6 | 0.0102 | 0.4297 | 0.0157 | 0.0/0.0 |
| match_4 | snap-morph_1s | 0 | A | homography+dis | 295 | 15.12 | 0.652 | - | 1536x1920 | 30 | 0.68 | 8.8 | 10.3 | 0.0098 | 1.6343 | 0.0174 | 0.0/0.0 |
| match_4 | dissolve_1s | 0 | A | homography+dis | 295 | 15.12 | 0.652 | - | 1536x1920 | 30 | 0.75 | 4.51 | 6.1 | 0.0062 | 0.264 | 0.0073 | 0.0/0.0 |
| match_4 | morph_3s | 0 | A | homography+dis | 295 | 15.12 | 0.652 | - | 1536x1920 | 90 | 0.63 | 24.06 | 25.7 | 0.0043 | 0.1096 | 0.0063 | 0.0/0.0 |
| match_5 | morph_1s | 0 | A | homography+dis | 89 | 84.61 | 0.322 | - | 1438x1920 | 30 | 0.8 | 9.19 | 11.2 | 0.0195 | 0.1658 | 0.0456 | 0.0/0.0 |
| match_5 | flow-dissolve_1s | 0 | A | homography+dis | 89 | 84.61 | 0.322 | - | 1438x1920 | 30 | 0.62 | 9.35 | 11.1 | 0.0196 | 0.2645 | 0.0442 | 0.0/0.0 |
| match_5 | snap-morph_1s | 0 | A | homography+dis | 89 | 84.61 | 0.322 | - | 1438x1920 | 30 | 0.61 | 8.82 | 10.6 | 0.016 | 1.8677 | 0.0585 | 0.0/0.0 |
| match_5 | dissolve_1s | 0 | A | homography+dis | 89 | 84.61 | 0.322 | - | 1438x1920 | 30 | 0.62 | 4.92 | 6.7 | 0.007 | 0.1101 | 0.0097 | 0.0/0.0 |
| match_5 | morph_3s | 0 | A | homography+dis | 89 | 84.61 | 0.322 | - | 1438x1920 | 90 | 0.62 | 23.3 | 25.3 | 0.012 | 0.0673 | 0.0196 | 0.0/0.0 |
| mismatch_1 | morph_1s | 0 | B | saliency-panzoom | 10 | 105.04 | 0.5 | 0.20/0.87 | 1444x1920 | 30 | 0.48 | 7.58 | 9.4 | 0.0111 | 0.1943 | 0.0184 | 0.0/0.0 |
| mismatch_1 | flow-dissolve_1s | 0 | B | saliency-panzoom | 10 | 105.04 | 0.5 | 0.20/0.87 | 1444x1920 | 30 | 0.38 | 7.76 | 9.4 | 0.0115 | 0.7695 | 0.0183 | 0.0/0.0 |
| mismatch_1 | snap-morph_1s | 0 | B | saliency-panzoom | 10 | 105.04 | 0.5 | 0.20/0.87 | 1444x1920 | 30 | 0.42 | 7.38 | 9.2 | 0.0109 | 1.9772 | 0.0259 | 0.0/0.0 |
| mismatch_1 | dissolve_1s | 0 | B | saliency-panzoom | 10 | 105.04 | 0.5 | 0.20/0.87 | 1444x1920 | 30 | 0.4 | 4.91 | 6.6 | 0.0077 | 0.2536 | 0.0109 | 0.0/0.0 |
| mismatch_1 | morph_3s | 0 | B | saliency-panzoom | 10 | 105.04 | 0.5 | 0.20/0.87 | 1444x1920 | 90 | 0.43 | 20.13 | 22.1 | 0.0048 | 0.1422 | 0.007 | 0.0/0.0 |
| mismatch_2 | morph_1s | 0 | B | saliency-panzoom | 5 | 46.06 | 0.5 | 0.15/0.16 | 602x800 | 30 | 0.09 | 1.5 | 2.0 | 0.0138 | 0.2367 | 0.0312 | 0.0/0.0 |
| mismatch_2 | flow-dissolve_1s | 0 | B | saliency-panzoom | 5 | 46.06 | 0.5 | 0.15/0.16 | 602x800 | 30 | 0.09 | 1.5 | 2.0 | 0.0141 | 0.6327 | 0.0286 | 0.0/0.0 |
| mismatch_2 | snap-morph_1s | 0 | B | saliency-panzoom | 5 | 46.06 | 0.5 | 0.15/0.16 | 602x800 | 30 | 0.09 | 1.47 | 2.0 | 0.0135 | 2.2786 | 0.0453 | 0.0/0.0 |
| mismatch_2 | dissolve_1s | 0 | B | saliency-panzoom | 5 | 46.06 | 0.5 | 0.15/0.16 | 602x800 | 30 | 0.09 | 0.77 | 1.3 | 0.0102 | 0.4611 | 0.0144 | 0.0/0.0 |
| mismatch_2 | morph_3s | 0 | B | saliency-panzoom | 5 | 46.06 | 0.5 | 0.15/0.16 | 602x800 | 90 | 0.09 | 4.11 | 4.9 | 0.0057 | 0.4239 | 0.0114 | 0.0/0.0 |
| mismatch_3 | morph_1s | 0 | B | saliency-panzoom | 6 | 121.92 | 0.5 | 0.06/0.06 | 1920x1440 | 30 | 0.44 | 6.57 | 7.8 | 0.0262 | 0.1339 | 0.0583 | 0.0/0.0 |
| mismatch_3 | flow-dissolve_1s | 0 | B | saliency-panzoom | 6 | 121.92 | 0.5 | 0.06/0.06 | 1920x1440 | 30 | 0.45 | 6.8 | 8.0 | 0.0259 | 0.2916 | 0.0625 | 0.0/0.0 |
| mismatch_3 | snap-morph_1s | 0 | B | saliency-panzoom | 6 | 121.92 | 0.5 | 0.06/0.06 | 1920x1440 | 30 | 0.45 | 6.59 | 7.8 | 0.0235 | 1.5718 | 0.0661 | 0.0/0.0 |
| mismatch_3 | dissolve_1s | 0 | B | saliency-panzoom | 6 | 121.92 | 0.5 | 0.06/0.06 | 1920x1440 | 30 | 0.45 | 4.14 | 5.4 | 0.0093 | 0.0994 | 0.0138 | 0.0/0.0 |
| mismatch_3 | morph_3s | 0 | B | saliency-panzoom | 6 | 121.92 | 0.5 | 0.06/0.06 | 1920x1440 | 90 | 0.45 | 26.53 | 28.0 | 0.0138 | 0.037 | 0.0239 | 0.0/0.0 |
| mismatch_4 | morph_1s | 0 | B | saliency-panzoom | 8 | 97.6 | 0.5 | 0.79/0.19 | 1920x1092 | 30 | 0.3 | 7.89 | 9.2 | 0.0059 | 0.2308 | 0.0112 | 0.0/0.0 |
| mismatch_4 | flow-dissolve_1s | 0 | B | saliency-panzoom | 8 | 97.6 | 0.5 | 0.79/0.19 | 1920x1092 | 30 | 0.29 | 7.15 | 8.4 | 0.0062 | 0.7861 | 0.0112 | 0.0/0.0 |
| mismatch_4 | snap-morph_1s | 0 | B | saliency-panzoom | 8 | 97.6 | 0.5 | 0.79/0.19 | 1920x1092 | 30 | 0.33 | 7.36 | 8.6 | 0.0058 | 1.9237 | 0.0158 | 0.0/0.0 |
| mismatch_4 | dissolve_1s | 0 | B | saliency-panzoom | 8 | 97.6 | 0.5 | 0.79/0.19 | 1920x1092 | 30 | 0.29 | 4.31 | 5.5 | 0.0049 | 0.3528 | 0.007 | 0.0/0.0 |
| mismatch_4 | morph_3s | 0 | B | saliency-panzoom | 8 | 97.6 | 0.5 | 0.79/0.19 | 1920x1092 | 90 | 0.3 | 20.39 | 21.9 | 0.0029 | 0.1382 | 0.0045 | 0.0/0.0 |
| mismatch_5 | morph_1s | 0 | B | saliency-panzoom | 36 | 85.06 | 0.5 | 0.15/0.34 | 1920x1080 | 30 | 0.33 | 7.5 | 9.8 | 0.0076 | 0.1816 | 0.0144 | 0.0/0.0 |
| mismatch_5 | flow-dissolve_1s | 0 | B | saliency-panzoom | 36 | 85.06 | 0.5 | 0.15/0.34 | 1920x1080 | 30 | 0.31 | 7.07 | 9.3 | 0.0076 | 0.4513 | 0.0143 | 0.0/0.0 |
| mismatch_5 | snap-morph_1s | 0 | B | saliency-panzoom | 36 | 85.06 | 0.5 | 0.15/0.34 | 1920x1080 | 30 | 0.31 | 7.31 | 9.5 | 0.0069 | 1.3836 | 0.013 | 0.0/0.0 |
| mismatch_5 | dissolve_1s | 0 | B | saliency-panzoom | 36 | 85.06 | 0.5 | 0.15/0.34 | 1920x1080 | 30 | 0.31 | 4.57 | 6.8 | 0.0054 | 0.2732 | 0.0083 | 0.0/0.0 |
| mismatch_5 | morph_3s | 0 | B | saliency-panzoom | 36 | 85.06 | 0.5 | 0.15/0.34 | 1920x1080 | 90 | 0.32 | 19.95 | 22.4 | 0.0037 | 0.1124 | 0.0059 | 0.0/0.0 |
| mismatch_6 | morph_1s | 0 | B | saliency-panzoom | 0 | 84.66 | 0.5 | 0.23/0.57 | 1146x1524 | 30 | 0.24 | 6.63 | 8.0 | 0.0197 | 0.6639 | 0.0246 | 0.0/0.0 |
| mismatch_6 | flow-dissolve_1s | 0 | B | saliency-panzoom | 0 | 84.66 | 0.5 | 0.23/0.57 | 1146x1524 | 30 | 0.24 | 6.33 | 7.6 | 0.0199 | 1.0366 | 0.0242 | 0.0/0.0 |
| mismatch_6 | snap-morph_1s | 0 | B | saliency-panzoom | 0 | 84.66 | 0.5 | 0.23/0.57 | 1146x1524 | 30 | 0.24 | 6.69 | 8.0 | 0.0191 | 1.4056 | 0.0274 | 0.0/0.0 |
| mismatch_6 | dissolve_1s | 0 | B | saliency-panzoom | 0 | 84.66 | 0.5 | 0.23/0.57 | 1146x1524 | 30 | 0.24 | 3.73 | 5.0 | 0.0173 | 0.7858 | 0.02 | 0.0/0.0 |
| mismatch_6 | morph_3s | 0 | B | saliency-panzoom | 0 | 84.66 | 0.5 | 0.23/0.57 | 1146x1524 | 90 | 0.24 | 18.82 | 20.5 | 0.0069 | 0.6522 | 0.0087 | 0.0/0.0 |
| mismatch_7 | morph_1s | 0 | A | homography+dis | 70 | 249.85 | 0.053 | - | 1920x1488 | 30 | 0.66 | 11.67 | 13.5 | 0.012 | 0.2608 | 0.0476 | 0.0/0.0 |
| mismatch_7 | flow-dissolve_1s | 0 | A | homography+dis | 70 | 249.85 | 0.053 | - | 1920x1488 | 30 | 0.66 | 11.67 | 13.5 | 0.0114 | 0.3044 | 0.0472 | 0.0/0.0 |
| mismatch_7 | snap-morph_1s | 0 | A | homography+dis | 70 | 249.85 | 0.053 | - | 1920x1488 | 30 | 0.59 | 11.2 | 13.0 | 0.011 | 1.8519 | 0.0532 | 0.0/0.0 |
| mismatch_7 | dissolve_1s | 0 | A | homography+dis | 70 | 249.85 | 0.053 | - | 1920x1488 | 30 | 0.6 | 5.87 | 7.6 | 0.0085 | 0.3719 | 0.0123 | 0.0/0.0 |
| mismatch_7 | morph_3s | 0 | A | homography+dis | 70 | 249.85 | 0.053 | - | 1920x1488 | 90 | 0.61 | 33.09 | 35.1 | 0.0073 | 0.1045 | 0.0267 | 0.0/0.0 |

## RoMa clips (2026-09-15) — `benchmarks/runs/2026-09-14/roma/index.html`
Six class A pairs × four field-using variants rendered from the RoMa outdoor field (CPU, 35–55 s
per pair for the field; certainty as the splat weight; everything else identical to the DIS clips
above), each beside the DIS clip of this run. Endpoints 0 / 0 on all 24 clips; every clip decodes
to its frame count. The `dissolve` variant is omitted (it uses no field). Verdicts below (`roma_picks.json`, 2026-09-15).

| pair | variant | edge_ratio DIS → RoMa | warping error DIS → RoMa | RoMa render s |
|---|---|---|---|---|
| match_1 | morph_1s | 0.23 → 0.26 | 0.0064 → 0.0070 | 9.67 |
| match_1 | flow-dissolve_1s | 0.23 → 0.64 | 0.0066 → 0.0083 | 10.04 |
| match_1 | snap-morph_1s | 1.55 → 1.49 | 0.0058 → 0.0057 | 9.72 |
| match_1 | morph_3s | 0.06 → 0.13 | 0.0034 → 0.0034 | 27.06 |
| match_2 | morph_1s | 0.12 → 0.15 | 0.0109 → 0.0121 | 6.82 |
| match_2 | flow-dissolve_1s | 0.12 → 0.50 | 0.0108 → 0.0129 | 6.89 |
| match_2 | snap-morph_1s | 1.51 → 1.43 | 0.0082 → 0.0097 | 7.05 |
| match_2 | morph_3s | 0.04 → 0.09 | 0.0084 → 0.0086 | 19.78 |
| match_3 | morph_1s | 0.12 → 0.07 | 0.0038 → 0.0037 | 10.56 |
| match_3 | flow-dissolve_1s | 0.48 → 0.70 | 0.0038 → 0.0038 | 10.6 |
| match_3 | snap-morph_1s | 1.71 → 1.68 | 0.0037 → 0.0036 | 10.21 |
| match_3 | morph_3s | 0.06 → 0.02 | 0.0017 → 0.0017 | 29.64 |
| match_4 | morph_1s | 0.24 → 0.22 | 0.0102 → 0.0080 | 10.87 |
| match_4 | flow-dissolve_1s | 0.43 → 0.79 | 0.0102 → 0.0082 | 10.96 |
| match_4 | snap-morph_1s | 1.63 → 1.63 | 0.0098 → 0.0079 | 11.05 |
| match_4 | morph_3s | 0.11 → 0.03 | 0.0043 → 0.0032 | 30.58 |
| match_5 | morph_1s | 0.17 → 0.15 | 0.0195 → 0.0176 | 10.59 |
| match_5 | flow-dissolve_1s | 0.26 → 0.66 | 0.0196 → 0.0196 | 10.85 |
| match_5 | snap-morph_1s | 1.87 → 1.85 | 0.0160 → 0.0135 | 10.78 |
| match_5 | morph_3s | 0.07 → 0.05 | 0.0120 → 0.0115 | 30.28 |
| mismatch_7 | morph_1s | 0.26 → 0.19 | 0.0120 → 0.0194 | 12.91 |
| mismatch_7 | flow-dissolve_1s | 0.30 → 0.58 | 0.0114 → 0.0190 | 12.82 |
| mismatch_7 | snap-morph_1s | 1.85 → 1.41 | 0.0110 → 0.0185 | 12.1 |
| mismatch_7 | morph_3s | 0.10 → 0.09 | 0.0073 → 0.0102 | 36.11 |

Reading: warping error falls with RoMa on match_4 and match_5 on every variant and on match_3's
morphs, is level on match_1 and match_2 (0.0064 → 0.0070 and 0.0109 → 0.0121 on morph 1 s) and
rises on mismatch_7 (0.0120 → 0.0194): RoMa's field there is 350 px off the global motion at
certainty 0.03, the TR2d case. `edge_ratio` on flow-dissolve rises with RoMa on every pair
(0.23 → 0.64 on match_1); cause not established, the clips decide whether it is visible.

## Owner verdicts on the RoMa clips (2026-09-15, `benchmarks/runs/2026-09-14/roma/roma_picks.json`, verbatim)
Score: RoMa better 1 (match_3) · same 1 (match_1) · DIS better 3 (match_4, match_5, mismatch_7) ·
neither usable 1 (match_2). The plan's adoption rule for TR5 (RoMa wins on at least 5 of 7 related
pairs) is not met; RoMa is not adopted as a drop-in class A field.

| pair | verdict | note (verbatim) |
|---|---|---|
| match_1 | same | both ok-ish , can't see visible improvement with RoMa |
| match_2 | neither usable | they look similar , both just do a lateral move as before ( see my complaint in previous picks file for this match_2 ) , roma did worse here as side edges become more distorted |
| match_3 | roma better | This is one case where roma transition looks more natural (as if person grows, although still quite messy, especially person's edges) |
| match_4 | dis better | roma does better transition for background here ( like wall and floor, more natural movement) , but box itself looks a bit boring as if prev image on it simply  fades out and new one fades in, no transformations ( although this may be useful as transition mode in our reveal app)  |
| match_5 | dis better | as in previous match_4, same issue - box itself looks a bit boring as if prev image on it simply  fades out and new one fades in, no transformations |
| mismatch_7 | dis better | roma here look very unnatural , as if after image unwraps with some cheap 3d cloth effect with lots of artifacts and visible edges. Dis version partially suffers as well and both are unusable but it at least more promising |

What the notes say beyond the score:
- **match_4 / match_5:** the box holding its position is a win the owner confirms (2026-09-15,
  verbatim: "i liked how the box itself holds position"); what is "boring" is the content on the
  box, which "faded in a boring manner". So RoMa satisfies one of the two requirements (the box
  stays put; the basket saw that) and neither field satisfies the other (the paint must transform,
  not fade; no number in the basket sees that). RoMa's background motion ("wall and floor, more
  natural movement") is liked. The fade-in-place look "may be useful as transition mode in our
  reveal app".
- **match_3:** RoMa "more natural (as if person grows)", edges still messy.
- **match_2:** both slide; RoMa distorts the side edges more.
- **mismatch_7:** RoMa "cheap 3d cloth effect with lots of artifacts and visible edges" — the 350 px
  low-certainty field predicted above; DIS "more promising", both unusable.
