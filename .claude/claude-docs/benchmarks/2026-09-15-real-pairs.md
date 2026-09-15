# TR14 probe sheet, 2026-09-15 — what the changed region does between the endpoints

Run: `scripts/research/tr14_variants.py --render <pair dirs> benchmarks/runs/2026-09-15/tr14 {1,3} …`
then `--page` (M3 Pro, `.venv` OpenCV 5.0.0; the RoMa fields from the 2026-09-14 probe, canvas
capped at 1920 px). Review page with players, labelled strips, the mask overlay and a pick per
pair: `benchmarks/runs/2026-09-15/tr14/index.html` (gitignored; the pick control exports
`tr14_picks.json`). Design of record for this pass: `TRANSITIONS.md §10`.

**What varies:** the correspondence field and what happens inside the changed-region mask. Every
clip is the `morph` preset (ease curves, color path 0.7); the encoder and the quality basket are
the tool's. The mask is Reveal's changed-region detector on the homography-aligned pair
(per-channel exposure-normalized difference, Otsu, morphological clean, 21 px dilation).

| variant | field | inside the mask |
|---|---|---|
| `dis` | homography + DIS residual, DIS consistency as the splat weight (the current tool) | the ordinary crossfade |
| `roma` | the RoMa outdoor field, RoMa certainty as the splat weight (the 2026-09-15 clips) | the ordinary crossfade |
| `roma-x-cert` | RoMa displacement × certainty, both directions (TR2d as written) | the ordinary crossfade |
| `hold` | camera motion + (RoMa − camera motion) × certainty (TR2d, residual form) | the ordinary crossfade, in place |
| `hold-dis` | camera motion + (DIS − camera motion) × (1 − feathered mask); no weights | the ordinary crossfade, in place |
| `luma` | `hold` | the new content appears in order of the old content's brightness, bright first (rank-normalized `luma_mask`) |
| `edge-grow` | `hold` | the new content grows outward from its own Canny edges (60/160): lines first, fills after |
| `melt` | `hold` | the frame is re-sampled through a curl-noise field, 1.2 % of the long edge × sin(πu), feathered 32 px inside the mask |
| `melt-soft` | `hold` | `melt` with the feather zero across the detector's 24 px dilation band, then a 64 px ramp |

Columns: `in-mask disp` = median displacement of the field inside the mask (the camera motion
alone is match_4 5.2 px, match_5 72.8 px, match_3 4.2 px, mismatch_7 330 px); `edge straightness`
= 90th percentile of the tracked edge's residual from a fitted quadratic (Reveal harness O's
tracker, ±10 px window following the camera motion) on the start photo / the finish photo / the
worst of the clip's frames at t = ¼, ½, ¾; the rest is the tool's basket.

| pair | s | variant | in-mask disp px | edge straightness px (A / B / clip) | warping error | edge_ratio | endpoints | render s |
|---|---|---|---|---|---|---|---|---|
| match_4 | 1 | `dis` | 20.89 | 2.54 / 3.89 / 6.3 | 0.0102 | 0.2446 | 0.0 / 0.0 | 7.26 |
| match_4 | 1 | `roma` | 3.06 | 2.54 / 3.89 / 2.4 | 0.008 | 0.2201 | 0.0 / 0.0 | 7.2 |
| match_4 | 1 | `roma-x-cert` | 1.02 | 2.54 / 3.89 / 2.88 | 0.0068 | 0.249 | 0.0 / 0.0 | 6.9 |
| match_4 | 1 | `hold` | 5.19 | 2.54 / 3.89 / 2.54 | 0.0076 | 0.2293 | 0.0 / 0.0 | 7.14 |
| match_4 | 1 | `hold-dis` | 6.64 | 2.54 / 3.89 / 4.4 | 0.0083 | 0.2633 | 0.0 / 0.0 | 10.87 |
| match_4 | 1 | `luma` | 5.19 | 2.54 / 3.89 / 3.96 | 0.008 | 0.2193 | 0.0 / 0.0 | 7.22 |
| match_4 | 1 | `edge-grow` | 5.19 | 2.54 / 3.89 / 3.49 | 0.0081 | 0.2168 | 0.0 / 0.0 | 7.33 |
| match_4 | 1 | `melt` | 5.19 | 2.54 / 3.89 / 5.31 | 0.0084 | 0.5302 | 0.0 / 0.0 | 7.31 |
| match_4 | 1 | `melt-soft` | 5.19 | 2.54 / 3.89 / 2.42 | 0.0078 | 0.2785 | 0.0 / 0.0 | 8.22 |
| match_4 | 3 | `dis` | 20.89 | 2.54 / 3.89 / 6.63 | 0.0043 | 0.1096 | 0.0 / 0.0 | 20.84 |
| match_4 | 3 | `roma` | 3.06 | 2.54 / 3.89 / 2.39 | 0.0032 | 0.0309 | 0.0 / 0.0 | 20.31 |
| match_4 | 3 | `roma-x-cert` | 1.02 | 2.54 / 3.89 / 2.8 | 0.0027 | 0.0215 | 0.0 / 0.0 | 20.22 |
| match_4 | 3 | `hold` | 5.19 | 2.54 / 3.89 / 2.54 | 0.003 | 0.0268 | 0.0 / 0.0 | 20.21 |
| match_4 | 3 | `hold-dis` | 6.64 | 2.54 / 3.89 / 4.42 | 0.0033 | 0.1361 | 0.0 / 0.0 | 23.25 |
| match_4 | 3 | `luma` | 5.19 | 2.54 / 3.89 / 3.62 | 0.0031 | 0.0261 | 0.0 / 0.0 | 20.69 |
| match_4 | 3 | `edge-grow` | 5.19 | 2.54 / 3.89 / 3.85 | 0.0032 | 0.0257 | 0.0 / 0.0 | 21.05 |
| match_4 | 3 | `melt` | 5.19 | 2.54 / 3.89 / 5.17 | 0.0033 | 0.4676 | 0.0 / 0.0 | 21.63 |
| match_4 | 3 | `melt-soft` | 5.19 | 2.54 / 3.89 / 2.62 | 0.0031 | 0.1858 | 0.0 / 0.0 | 23.77 |
| match_5 | 1 | `dis` | 79.66 | 6.91 / 7.32 / 7.49 | 0.0195 | 0.1658 | 0.0 / 0.0 | 7.79 |
| match_5 | 1 | `roma` | 74.32 | 6.91 / 7.32 / 6.92 | 0.0176 | 0.1466 | 0.0 / 0.0 | 7.82 |
| match_5 | 1 | `roma-x-cert` | 2.93 | 6.91 / 7.32 / 7.8 | 0.0119 | 0.1567 | 0.0 / 0.0 | 7.7 |
| match_5 | 1 | `hold` | 72.83 | 6.91 / 7.32 / 6.88 | 0.0152 | 0.1454 | 0.0 / 0.0 | 7.76 |
| match_5 | 1 | `hold-dis` | 71.9 | 6.91 / 7.32 / 6.99 | 0.0167 | 0.1567 | 0.0 / 0.0 | 11.64 |
| match_5 | 1 | `luma` | 72.83 | 6.91 / 7.32 / 6.96 | 0.0174 | 0.1378 | 0.0 / 0.0 | 7.91 |
| match_5 | 1 | `edge-grow` | 72.83 | 6.91 / 7.32 / 6.82 | 0.0175 | 0.136 | 0.0 / 0.0 | 8.03 |
| match_5 | 1 | `melt` | 72.83 | 6.91 / 7.32 / 7.26 | 0.0166 | 0.2963 | 0.0 / 0.0 | 7.88 |
| match_5 | 1 | `melt-soft` | 72.83 | 6.91 / 7.32 / 7.26 | 0.0157 | 0.2026 | 0.0 / 0.0 | 8.8 |
| match_5 | 3 | `dis` | 79.66 | 6.91 / 7.32 / 7.23 | 0.012 | 0.0673 | 0.0 / 0.0 | 22.79 |
| match_5 | 3 | `roma` | 74.32 | 6.91 / 7.32 / 7.13 | 0.0115 | 0.0473 | 0.0 / 0.0 | 22.43 |
| match_5 | 3 | `roma-x-cert` | 2.93 | 6.91 / 7.32 / 7.67 | 0.0054 | 0.052 | 0.0 / 0.0 | 21.79 |
| match_5 | 3 | `hold` | 72.83 | 6.91 / 7.32 / 7.03 | 0.011 | 0.0476 | 0.0 / 0.0 | 22.19 |
| match_5 | 3 | `hold-dis` | 71.9 | 6.91 / 7.32 / 7.42 | 0.0114 | 0.0634 | 0.0 / 0.0 | 24.94 |
| match_5 | 3 | `luma` | 72.83 | 6.91 / 7.32 / 7.57 | 0.0116 | 0.0453 | 0.0 / 0.0 | 23.48 |
| match_5 | 3 | `edge-grow` | 72.83 | 6.91 / 7.32 / 6.84 | 0.0118 | 0.0447 | 0.0 / 0.0 | 23.2 |
| match_5 | 3 | `melt` | 72.83 | 6.91 / 7.32 / 7.19 | 0.011 | 0.2211 | 0.0 / 0.0 | 24.87 |
| match_5 | 3 | `melt-soft` | 72.83 | 6.91 / 7.32 / 7.05 | 0.0109 | 0.1125 | 0.0 / 0.0 | 24.85 |
| match_3 | 1 | `dis` | 20.8 | 6.0 / 7.21 / 8.6 | 0.0038 | 0.117 | 0.0 / 0.0 | 7.62 |
| match_3 | 1 | `roma` | 14.85 | 6.0 / 7.21 / 7.86 | 0.0037 | 0.0749 | 0.0 / 0.0 | 7.3 |
| match_3 | 1 | `roma-x-cert` | 1.15 | 6.0 / 7.21 / 6.82 | 0.0032 | 0.0379 | 0.0 / 0.0 | 7.44 |
| match_3 | 1 | `hold` | 4.2 | 6.0 / 7.21 / 7.98 | 0.0032 | 0.0413 | 0.0 / 0.0 | 7.19 |
| match_3 | 1 | `hold-dis` | 2.51 | 6.0 / 7.21 / 8.56 | 0.0033 | 0.0911 | 0.0 / 0.0 | 8.04 |
| match_3 | 1 | `luma` | 4.2 | 6.0 / 7.21 / 8.64 | 0.0035 | 0.0374 | 0.0 / 0.0 | 7.56 |
| match_3 | 1 | `edge-grow` | 4.2 | 6.0 / 7.21 / 7.74 | 0.0035 | 0.0377 | 0.0 / 0.0 | 7.36 |
| match_3 | 1 | `melt` | 4.2 | 6.0 / 7.21 / 8.65 | 0.0035 | 0.364 | 0.0 / 0.0 | 7.73 |
| match_3 | 1 | `melt-soft` | 4.2 | 6.0 / 7.21 / 7.98 | 0.0032 | 0.0593 | 0.0 / 0.0 | 8.42 |
| mismatch_7 | 1 | `dis` | 312.55 | n/a | 0.012 | 0.2608 | 0.0 / 0.0 | 8.51 |
| mismatch_7 | 1 | `roma` | 489.19 | n/a | 0.0194 | 0.1948 | 0.0 / 0.0 | 8.9 |
| mismatch_7 | 1 | `roma-x-cert` | 0.39 | n/a | 0.0096 | 0.3244 | 0.0 / 0.0 | 7.1 |
| mismatch_7 | 1 | `hold` | 330.04 | n/a | 0.0081 | 0.2806 | 0.0 / 0.0 | 8.04 |
| mismatch_7 | 1 | `hold-dis` | 327.06 | n/a | 0.0125 | 0.2575 | 0.0 / 0.0 | 9.19 |
| mismatch_7 | 1 | `luma` | 330.04 | n/a | 0.0099 | 0.2693 | 0.0 / 0.0 | 8.0 |
| mismatch_7 | 1 | `edge-grow` | 330.04 | n/a | 0.0098 | 0.2666 | 0.0 / 0.0 | 7.95 |
| mismatch_7 | 1 | `melt` | 330.04 | n/a | 0.0086 | 0.2929 | 0.0 / 0.0 | 8.2 |
| mismatch_7 | 1 | `melt-soft` | 330.04 | n/a | 0.0083 | 0.2826 | 0.0 / 0.0 | 9.04 |

- match_4: canvas [1536, 1920], mask 0.276 of the canvas, sparse inliers 295, edge x = 1014, rows 425–1478, camera shift 3.4 px
- match_5: canvas [1438, 1920], mask 0.49 of the canvas, sparse inliers 89, edge x = 771, rows 150–1357, camera shift -70.0 px
- match_3: canvas [1438, 1920], mask 0.189 of the canvas, sparse inliers 986, edge x = 209, rows 1006–1597, camera shift -0.19 px
- mismatch_7: canvas [1920, 1488], mask 0.432 of the canvas, sparse inliers 70, edge none (no vertical edge inside the mask)

## Reading (the agent's; the owner's picks decide)
- **TR2d as written is wrong in principle.** `roma-x-cert` stops an uncertain region from
  following the camera: match_5's boxes move 2.9 px while the camera moves them 70 px, so they
  detach from the wall and pavement; on mismatch_7 the sky freezes (0.39 px) while the skyline
  moves 330 px, and the buildings double at mid-frame. The basket cannot see it: its warping error
  falls (match_5 0.0176 → 0.0119) because less moves.
- **`hold` meets the position requirement on every pair and fixes mismatch_7.** Inside the mask
  the displacement equals the camera motion; the box edge is as straight as on the photo
  (match_4 2.54 px = A's 2.54, against `dis` 6.3); on mismatch_7 the warping error is 0.0081
  against `dis` 0.012 and `roma` 0.0194, and the mid frame is a clean crossfade of the two skies
  (no cloth effect, no torn clouds). What remains there is the start frame's moved border as a
  rectangle at mid-transition (backlog T14: a canvas rule, not a field).
- **`hold-dis` (no weights) is close but not equal to `hold`:** match_4 straightness 4.4 px and
  `edge_ratio` 0.136 at 3 s against 2.54 px and 0.027, because the gate's 8 px feather lets the DIS
  residual act in the dilation band around the box edge where DIS is confidently wrong. Widening
  the gate past the detector's dilation is the fix to measure before it is preferred.
- **The three effects change nothing outside the mask** (same field as `hold`, same in-mask
  displacement) and leave the box edge at the photo's straightness once `melt` got its offset
  feather (`melt` 5.31 px → `melt-soft` 2.42 on match_4). By the agent's eye on the mid frames:
  `edge-grow` draws the mural in outline before it is painted; `luma` keeps the old graffiti's dark
  strokes while the mural fills in behind them; `melt-soft` swirls the paint and re-forms it,
  subtle at 23 px. None is a fade; whether any is the transformation the owner wants is the pick.
- **match_3 (a person who moved) is not made worse** by any `hold`-based variant (warping error
  0.0032–0.0035 against `dis` 0.0038); it stays a TR9 case.
- Render cost: the effects add 0–1 s per 30 frames over `hold`; `hold-dis` and `melt-soft` rows
  carry 1–3 s more because they ran beside another job.

## Owner picks
Pending (`tr14_picks.json` next to the page: closest variant per pair, "acceptable as-is", note).
