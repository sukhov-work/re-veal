---
reader: the next session building phase C of the studio, cold
shape: report
date: 2026-11-18
---
# What the wall pairs added over stock Reveal, and what phase C takes

## Summary

Verdict: the method is accepted. The owner graded the delivered set on 2026-11-18: "all 3 variants
look amazing , exactly what was needed". The three variants are the full-frame, real-pixels and 4:5
versions of each pair.

Stock Reveal could not do this job: on a wall repainted whole it found no inlier on the painted
face. Fourteen additions, all in `scripts/research/wall_pairs.py` (740 lines, md5
`bcd921bc148cd12320ffe77d3aaf91d6`), did it. Phase C of `STUDIO.md` builds the align flow; its
section 14 says which additions become stages, knobs and views there.

Actions asked of the next session: read section 14 of `STUDIO.md` before designing phase C; give
`wall_pairs.py` its inputs by arguments first (backlog T125).

Open question: whether any of this enters `reveal.py` itself (backlog T122 and T123; his word decides).

## Glossary

- Stock Reveal: `reveal.py align` as shipped, strict (`reshot`) or `loose`.
- Pair 1 is `1.jpg` → `2.jpg`; pair 2 is `1b.jpg` → `2b.jpg`. In `fixtures/` they are `wall_1_S/F` and `wall_2_S/F`.
- BEFORE, AFTER: the earlier and the later photo. Stock Reveal warps AFTER onto BEFORE's frame.
- Frame of record: the photo whose pixels stay untouched; the other photo is warped onto it.
- Groove map: an image of dark thin structures only (block joints, cracks). Paint does not show in it.
- Held-out windows: a quarter of the matched windows, never used by the fit, only to judge it.
- Field: a smooth displacement added to the homography, at most a few px, varying over 200 px and more.
- Completion: pixels invented for BEFORE where its photo ended inside AFTER's frame.
- Real-pixel rectangle: the largest rectangle of the frame in which BEFORE has no completed pixel.
- The skeptic: an Opus subagent that measures the delivered files by its own method.

## The pipeline, in order

1. Run stock Reveal in both modes and draw where its inliers sit.
2. Draw the subject polygon on BEFORE (here the wall face).
3. Take a seed homography from Reveal's learned matcher under the loose profile.
4. Warp AFTER by the seed, build both groove maps, run the learned matcher on them, fit, repeat once.
5. Match windows of the groove maps by normalised cross-correlation, coarse to fine; fit with a quarter held out.
6. Fit the field to the window residuals; keep it only if an independent measure improves.
7. Choose the frame of record; warp the other photo once, supersampled.
8. Complete BEFORE where it has no pixel; write the coverage mask.
9. Compute the real-pixel rectangle and the 4:5 window; check that marked text and credits are inside each.
10. Write the stills, the three wipes and the slider page; decode every video.
11. Measure joints on the delivered stills with a control shift; hand the files to the skeptic.

## The additions

| # | Addition | What it solved, with the number | Where |
|---|---|---|---|
| 1 | The inlier map | A passed fit hung on the wrong plane: pair 1 had 76 inliers at confidence 31, all on the fence; pair 2 had 86 at confidence 86, all on the cap course | `benchmarks/runs/2026-11-17/wall/probe1.py` |
| 2 | The subject polygon | The fit and every measure are restricted to the plane that matters | `PAIRS[...]["wall"]`, `poly_mask` |
| 3 | The groove map | Appearance changed everywhere; relief did not. A black-hat (15 px) over a contrast-normalised luminance keeps the relief | `groove_map` |
| 4 | The learned matcher on groove maps | 423 of 798 matches inliers on pair 1, 169 of 507 on pair 2; the stock seed was 252 px and 36 px off on the wall | `groove_matches`, `seed_h` |
| 5 | Window refinement with held-out windows | Held-out RMSE 1.18 px (174 windows) and 1.41 px (93) at full resolution; the plot shows fitted, held-out and rejected vectors | `window_matches`, `fit`, `residual_plot` |
| 6 | The smooth field | The skeptic's median seam step went from 0.65 to 0.44 px (pair 1) and from 1.07 to 0.44 px (pair 2); pair 2's left edge from −4.00 to −0.92 px; it moves at most 2.04 and 2.14 px | `smooth_field`, `--field 200` |
| 7 | Models measured and dropped | Radial terms and polynomials of degree 2 and 3 gained under 0.4 px on held-out windows and extrapolate off the wall | `probe3.py`, `probe5.py` |
| 8 | AFTER as the frame of record | The first set cropped AFTER to the rectangle inside its footprint and lost the text and the credit; now `after.png` equals the decoded source photo | `render_after`, `warp_before` |
| 9 | Coverage mask and completion | BEFORE is real on 77.6 % (pair 1) and 97.4 % (pair 2) of AFTER's frame; the mask says where it is not | `complete_before`, `before_coverage.png` |
| 10 | Crops that keep marked content | Real-pixel rectangles 3008×2748 and 3008×3664; 4:5 windows 3024×3780 (82.8 % real) and 2930×3664 (100 %); both hold the text and the handle | `rv.crop_rect` on the mask, `real_window_4x5`, `win45` |
| 11 | Exports | sRGB-tagged PNG and 4:4:4 JPEG; three wipes per pair (full frame 2606×3474, real rectangle, 4:5 at 1080×1350), one keyframe, bt709 tags | `save_srgb`, `wipe_video` |
| 12 | The joint measure with a control | A shift of (2.0, −1.5) px reads as (1.95, −1.52); delivered stills read 0.32 and 0.48 px median on level joints | `joint_offsets`, `verify`, `verify_after` |
| 13 | The skeptic's A/B | It found pair 2's 2 to 3 px errors that my own measure missed, then graded the fix | `research/2026-11-17/wall_skeptic.md` |
| 14 | The slider page | One local page, three views per pair, AFTER left of the seam as in the videos | `benchmarks/runs/2026-11-17/wall/stage.py` |

## How each part works, briefly

- Groove map. Subtract a 25 px Gaussian mean, divide by the local spread, clip to ±3, take the
  black-hat with a 15 px ellipse, blur by 1.2 px. Only dark thin structures answer.
- Window matching. A window is skipped when its grooves run in one direction only (the smaller
  eigenvalue of the structure tensor under 8 % of the larger): a single course line slides along
  itself. A peak on the search border is not a measurement. Levels: half resolution with 160 px
  windows and a 20 px search, then 112 px and 8 px, then full resolution with 160 px and 8 px.
- Field. Gaussian kernel regression of the window residuals on a 32 px grid. The denominator
  carries one extra unit, so the field fades to zero where under one window supports it. Cap 4 px.
- Warp onto AFTER. An AFTER pixel y reads BEFORE at H(y) + f(H(y)); the field changes by under
  0.02 px per px, so no iteration is needed. Lanczos at twice the size, then an area average.
- Completion of the ground. Per column, the colour of BEFORE's real ground just above the photo's
  edge. A local object (a stain) fades into a running median of 601 columns within about 200 px.
  A weak shade comes from AFTER's ground after a 168 px median. Seeded noise in three bands (under
  1.5 px, 1.5 to 5 px, 5 to 14 px) takes the robust spread of the real ground. A 32 px cross-fade.
- Completion above the wall. AFTER's canopy with BEFORE's colour mean and spread from a band beside the edge.
- Videos. The full frame is scaled to stay under 96 % of the H.264 level 5.1 frame size. Check a
  level by its 16 px blocks: 2774×3400 passed the pixel count and still came out at level 6.0.

## What failed, with the reason

| Tried | Result | Lesson |
|---|---|---|
| SIFT on the photos | 5 to 7 inliers | A repaint leaves no shared appearance |
| Four hand-picked landmarks as the seed | A sheared transform | Reading coordinates off a downscaled view is not a measurement |
| Window search straight from the stock seed | 0 windows kept | Course lines repeat every 115 to 270 px; a search from over half a course off locks onto the wrong joint |
| My joint tracker as the judge of the field | It read under 0.1 px of gain | A measure that shares the fit's method cannot grade a correction to the fit |
| A crop rectangle inside AFTER's footprint on BEFORE's frame | It cut the text and the credit | Look at what a crop removes before showing a set |
| Mirroring real ground texture below the edge | Symmetric figures | Use noise with the real spread |
| One colour per column for the completed ground | A stain became a dark streak | Fade local objects into the neighbourhood |
| Grey noise in one band | The skeptic called it fake at 1080×1350 | Match three bands, and the tone at the edge |

## Acceptance anchors for phase C (this laptop, 2026-11-18)

Sources: `1.jpg` 58bc0a96973f12f13d319d2f0cebccb4, `2.jpg` 2a2811d7f5546b4d07d32675e151a3f2,
`1b.jpg` b6a3fe5c3a97750c3f198a24d0cfa4d8, `2b.jpg` ffcb3bf91a4171319a642721dfe042b3.

| File | Pair 1 md5 | Pair 2 md5 |
|---|---|---|
| `after.png` | 89370fd4a77919a9859b7b8c0a4bd2fc | 72c2166e8687e7e789c7ee05e9afe79b |
| `before_aligned.png` | 69ecc53c1a3784889f57114766a6dbdd | 5ba2e598480beee22ba91e9687b26ce1 |
| `before_coverage.png` | 04bb2549d7ddcf753a9488c8ff264d66 | e5d6ad74883d13a5e7455a431476a4f5 |
| `reveal_native.mp4` | c7c1e0a9ca1051a4bc9d6e2344fa80b5 | 86b0761ee32fe747d8c744356760efe8 |
| `reveal_real_pixels.mp4` | 84bedfda1d733e616666a44fc9d75c8c | c19a020c918915b1cff17a99a3caba55 |
| `reveal_4x5.mp4` | 500352734fb3adae3321e8e0c1188e2c | 424e13bd863d6c6bcebf32b954c30c1f |

Verified: the real-pixels and 4:5 videos came back with the same md5 on a second render. Assumed,
not re-run: that `fit` gives the same homography twice (`fit_a/H.npy` 70a3dc5d3da0e7f7769f9a97bf471a4a,
`fit_b/H.npy` e71db0a1ae5dd1feb9cb7c893486812a, one run each). A cheaper anchor is the fit's log:
423 and 169 groove inliers, held-out RMSE 1.18 and 1.41 px.

## What the script lacks before the studio can run it

- Its pairs, source folder and polygons are constants (`PAIRS`, `SRC`). The studio passes inputs as
  arguments, so the script needs `--before`, `--after`, `--wall` and `--win45`, default-off and
  proved byte-identical on these two pairs (backlog T125).
- The 4:5 window that keeps marked content was set by hand for pair 1. It needs keep boxes as input.
- It writes no progress line; the loop script's `--progress` is the model.
- It handles one plane. A pipe that stands off the wall stays 3.5 to 3.9 px off in pair 2; the owner
  accepted that.

## Evidence

Every number above is measured on the owner's four photos. The fit's log is `fit_a/fit.json` and
`fit_b/fit.json`; the renders' rectangles are in each `render.json`; the skeptic's tables are in
`wall_skeptic.md`; all under `benchmarks/runs/2026-11-17/wall/` (gitignored) or beside this file.
