# Real-pair sheet — 2026-09-13 (first run of slice TR2; Reveal rows double as the first H2 sheet)

## Method
Twelve pairs the owner placed in `fixtures/` (5 `match`, 7 `mismatch`; 21 JPEG + 2 HEIC + 1 PNG; catalogue rows in
`fixtures/MANIFEST.md`). Command: `scripts/bench_transitions.py --out benchmarks/runs/2026-09-13 --reveal`.
Reveal ran `align --mode reshot` at native resolution (loose would have run only if strict refused a
matched pair; it never did). Transitions ran with the canvas capped at 1920 px, presets morph,
flow-dissolve, snap-morph and dissolve at 1.0 s and morph at 3.0 s: 72 runs in all (60 on the first
ten pairs, 12 on mismatch_6 and mismatch_7 added later the same evening), M3 Pro, one job at a time. Strips and mp4s are local: open `benchmarks/runs/2026-09-13/index.html` (gitignored).

## Verdict against research gate E2
- Class routing: 11 of 12 as the owner labelled (5 match → A, 6 mismatch → B). mismatch_7 routed to
  class A: the two photos share the city skyline (70 sparse inliers, homography sane), so the
  routing is right by its own rule; the owner's label says the pair is only vaguely related.
- `edge_ratio` on morph, dissolve and flow-dissolve: maximum 0.79 (mismatch_6 dissolve), every run
  below the 1.5 gate. snap-morph measures 1.23–1.99, which its hold-then-go curve produces by design.
- Endpoints: 0 / 0 on every run.
- Owner rating (gate: at least 6 of 10 pairs usable as-is at 1 s; 12 pairs now): **pending** — the owner reviews `index.html`.

## Observations (four strips looked at by the agent; not a rating)
- match_4, the roster pair: the mural dissolves onto the box while wall and pavement stay put; the box
  edges stay straight through the morph.
- match_5: smooth overall; the box edge doubles in the middle frames (103 px median displacement,
  certainty 0.33).
- match_1 (HEIC): the head ghosts in the middle frames; a non-rigid subject with 64 px of displacement.
- mismatch_4: the saliency similarity put the sun on the sun without anchors; the skylines cross-dissolve.
- mismatch_5: the sun is scaled toward the galaxy core and a rectangular bright patch shows in frames 4–6.
  That is the class B box similarity being crude by design; anchors and semantic matching are slice TR9.
- mismatch_7 (same skyline, different skies): mean certainty 0.053, the lowest of the sheet. The morph
  tears the clouds into blocky patches in the middle frames: the DIS residual chases unrelated sky
  content, the same mechanism as Reveal's field defect #1. A class A pair with certainty this low
  should fall back to the homography-only skeleton (proposed slice TR2b; waits for the rating).
- mismatch_6 (day → night): class B with 0 sparse inliers; the rectangular saliency box shows during
  the morph as on mismatch_5. The canvas is the small start frame (1146×1528).
- Reveal: strict passes all five matched pairs at confidence 90–97, refuses six of the seven mismatched
  pairs with the plain message, and passes mismatch_7 (78 inliers, 0.89 px, confidence 92): the
  skyline is one scene from a similar spot, so strict mode accepted it although 34 % of the frame
  changed. On match_3 the ECC stage returned no rho and the feature homography was kept
  (the designed degrade path; the pair still passed at 1059 inliers). The roster pair match_4 measures
  481 inliers and 0.79 px here against 458 and 0.74 in the 2026-07-13 sandbox; OpenCV is 5.0.0 here and
  no estimation code changed, so the delta is the environment, and this row is the new local baseline.

## Owner review (2026-09-13 night, verbatim)
> I went through benchmarks/runs/2026-09-13/index.html , so several important notes here. 1) If the idea was to let me judge different variations of each type of each case ( e.g match_1 - morph_1s , variants 1-8 ( if this is what you intended) ) then i need a way to pick best for each pair and case and also need to undestand the difference , what went into those 8 options . Next, some matches like match_1, match_4 and match_5 look promising, at least somewhat resembling nice dynamic  transition ( still missing accuracy and those interesing intermediate transformations of parts of image ). Match_2 suffers that person in frame is shifted sideways ( because before/after not perfectly aligned) and only then morphs. Match_3 - basically person from start of frame erased/ dissolved into person in end frame. I am not saying that you must finetune now all cases to accomodate for people or something else specifically, but such junky transition show how we miss to grasp some themes or objects or ideas about given frame and build flows around them even if they are quite detached both physically and conceptually from each other.  As for mismatches - no miracle here, almost all results are just naive  cross-dissolves with very simple frame movements animation , looks very generic ( but maybe this is intent for this phase )

The E2 gate ("at least 6 of 10 usable as-is") is not met: three of the five matched pairs are
"promising", two are "junky", the seven mismatched pairs are "naive cross-dissolves". A per-pair
pick is still to come through the page's picks.json.

## What the page got wrong, and the fix
The eight tiles under each variant were eight time-sampled frames of one transition, not eight
variants, and nothing on the page said so. The page now labels every tile with its frame index and
time, plays each variant inline, lists what each preset changes, and has a "best variant" radio
plus a note per pair that exports to `picks.json`
(`scripts/bench_transitions.py --render-only --picks picks.json` puts them into this sheet).

## Diagnosis per remark (mechanism, not excuse)
- **match_2, "shifted sideways and only then morphs".** The engine aligns the two photos by the
  background homography and the person, who moved between the shots, becomes a large residual
  displacement (141 px median). The forward splat slides the person along that displacement while
  the crossfade runs on the same eased curve, so the eye reads a slide first and a dissolve second.
  The `flow-dissolve` variant (warp 0.6, dissolve delayed 0.1) and a negative `mix_delay` soften
  this, but no preset produces motion of the person's parts: there is no part-level correspondence.
- **match_3, "person erased into person".** The two poses share no consistent flow, so the
  forward-backward certainty collapses on the person and the coverage-aware mix degrades to a
  crossfade there, while the dome and lake stay put. Correct for the field it has, wrong for the
  theme: a person should become the person.
- **match_1, match_4, match_5, "promising, missing accuracy and the interesting intermediate
  transformations".** The DIS residual on a pre-aligned pair is a phase-1 dense field; a learned
  dense matcher (RoMa, slice TR5) is the accuracy step, and intermediate transformations of parts
  are what the generative tier (TR6) exists for.
- **mismatches, "naive cross-dissolves, generic".** Class B in this phase is a similarity between
  two salient blobs plus a crossfade, by design; the object-and-theme correspondence the owner
  describes (a person to a person, a sun to a sun, the box to the box, across unrelated scenes) is
  slice TR9: SAM 2 masks, DINOv2 part matches, user anchors through Moving Least Squares.

## Owner picks (2026-09-14, `picks_1-14-10-2026.json`, verbatim notes)
Usable as-is: 3 of 12 (match_1, match_4, match_5). The research gate E2 (at least 6 of 10) is **not met**.

| pair | best variant | note |
|---|---|---|
| match_1 | flow-dissolve_1s | dissolve_1s is very junky, just cross dissove; Best are morph_1s , flow_dissolve and snap_morph , they are pretty close, morph_3s too slow, in  this case as movement is subtle. |
| match_2 | none | dissolve_1s is very junky, just cross dissove; Partially ok:  morph_1s , flow_dissolve and snap_morph , they are pretty close and all have the same bug that image shifts first ,then morphs; morph_3s too slow, in  this case as movement is subtle |
| match_3 | none | dissolve_1s is very junky, just cross dissove; Somewhat ok:  morph_1s , morph_3s, flow_dissolve and snap_morph , they are curious , but if we aim for person here- it just disintegrates and then starts materializing in finishing position out or random direction |
| match_4 | morph_3s | dissolve_1s is junky, just cross dissove; Best are morph_3s, but morph_1s ,  flow_dissolve and snap_morph , they are pretty close but  have one  small-medium issue , that new image textures come from the right on the box , altough nothing in the picture indicates directionality and i would expect it to transform unidirectiobally ( in this case!)  |
| match_5 | morph_3s | dissolve_1s is junky, just cross dissove; Best are morph_3s , probably the best morph across this run ,but only because images were very well aligned from the start. Also i wish the boxes ( which are main subject here) didn't shift at all ( or as little as possible ) and that changes whould come a bit more subtly at different parts of the image, but this is more taste matter |
| mismatch_1 | none | here on all samples are just cross-dissolve/ fade with primitive movement animation between frames , also you can see next frame square  borders which is especially ugly in transition  |
| mismatch_2 | none | here on all samples are just cross-dissolve/ fade with primitive movement animation between frames , also you can see next frame square  borders which is especially ugly in transition  |
| mismatch_3 |  | here on all samples are just cross-dissolve/ fade with primitive movement animation between frames , also you can see next frame square  borders which is especially ugly in transition  |
| mismatch_4 | none | here on all samples are just cross-dissolve/ fade with primitive movement animation between frames , also you can see next frame square  borders which is especially ugly in transition  |
| mismatch_5 | none | here on all samples are just cross-dissolve/ fade with primitive movement animation between frames , also you can see next frame square  borders which is especially ugly in transition   |
| mismatch_6 | none | here on all samples are just cross-dissolve/ fade with primitive movement animation between frames , also you can see next frame square  borders which is especially ugly in transition , worst of the batch  |
| mismatch_7 | none | here on all samples are just cross-dissolve/ fade with primitive movement animation between frames , also you can see next frame square  borders which is especially ugly in transition , but in this pair there it at least some inkling ( tiny ) of transformation  |

Three findings the picks add to the diagnosis above:
- **Class B frame border walks through the picture** (every mismatched pair: "you can see next frame
  square borders which is especially ugly"). The similarity warp moves the whole finish frame, so its
  rectangular edge enters the canvas and the hole fill shows it. Defect, backlog T13; fix = warp only
  the salient region under a soft mask and crossfade the rest, or feather the warped frame's validity.
- **Directional texture inflow where nothing implies a direction** (match_4: "new image textures come
  from the right on the box"; match_5: "i wish the boxes … didn't shift at all"). Inside a repainted
  region there is no true correspondence; the DIS residual still picks a direction and the splat
  follows it. Candidate lever: scale the displacement by the per-pixel certainty so low-certainty
  regions dissolve in place (plan TR2d). Reveal's §5a warning about spatially varying fields applies
  and is the thing to measure.
- **Timing taste**: 1 s is right when the movement is subtle (match_1); 3 s won on the two box
  pairs; the plain dissolve is "junky" everywhere and stays a baseline only.

## Speed (canvas ≤ 1920 px, 1.3–2.8 MP)
morph 1 s (30 frames): render 4.7–13.4 s, or 0.16–0.45 s per frame (the 1920×1488 canvas of mismatch_7
is the slowest); morph 3 s: 13–37 s; correspondence 0.4–0.65 s once per pair; Reveal `align` 2.2–16 s
per pair at native resolution (48 MP HEIC: 7.7 s; mismatch_7 at 2535×3792 vs 2470×1914: 16.2 s).


## Reveal align (native resolution)

| pair | mode | rc | method | inliers | rmse_px | ecc_rho | periph_ssim | residual | changed_% | confidence | wall s | error |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| match_1 | reshot | 0 | sift | 368 | 0.74 | 0.998 | 0.849 | False | 10.4 | 95 | 7.7 |  |
| match_2 | reshot | 0 | sift | 913 | 1.01 | 0.9971 | 0.884 | False | 26.2 | 90 | 2.2 |  |
| match_3 | reshot | 0 | sift | 1059 | 1.0 | None | 0.876 | False | 19.0 | 90 | 3.7 |  |
| match_4 | reshot | 0 | sift | 481 | 0.79 | 0.9461 | 0.539 | False | 28.3 | 94 | 5.0 |  |
| match_5 | reshot | 0 | sift | 121 | 0.67 | 0.9033 | 0.504 | False | 52.3 | 97 | 4.8 |  |
| mismatch_1 | reshot | 2 | None | None | None | None | None | None | None | None | 5.5 | FAILED: Could not find enough common detail between the two photos. They need to |
| mismatch_2 | reshot | 2 | None | None | None | None | None | None | None | None | 4.0 | FAILED: Could not find enough common detail between the two photos. They need to |
| mismatch_3 | reshot | 2 | None | None | None | None | None | None | None | None | 5.4 | FAILED: Could not find enough common detail between the two photos. They need to |
| mismatch_4 | reshot | 2 | None | None | None | None | None | None | None | None | 4.3 | FAILED: Could not find enough common detail between the two photos. They need to |
| mismatch_5 | reshot | 2 | None | None | None | None | None | None | None | None | 5.0 | FAILED: Could not find enough common detail between the two photos. They need to |
| mismatch_6 | reshot | 2 | None | None | None | None | None | None | None | None | 14.8 | FAILED: Could not find enough common detail between the two photos. They need to |
| mismatch_7 | reshot | 0 | sift | 78 | 0.89 | None | 0.701 | False | 34.2 | 92 | 16.2 |  |

## Transitions (`transitions.py pair`)

| pair | preset | rc | class | method | inliers | median_disp_px | certainty | canvas | frames | corr s | render s | wall s | warping_err | edge_ratio | max_step | endpoint |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| match_1 | morph_1s | 0 | A | homography+dis | 492 | 63.66 | 0.482 | 1440x1920 | 30 | 0.52 | 6.9 | 11.8 | 0.0064 | 0.2299 | 0.0131 | 0.0/0.0 |
| match_1 | flow-dissolve_1s | 0 | A | homography+dis | 492 | 63.66 | 0.482 | 1440x1920 | 30 | 0.45 | 6.57 | 11.3 | 0.0066 | 0.2288 | 0.013 | 0.0/0.0 |
| match_1 | snap-morph_1s | 0 | A | homography+dis | 492 | 63.66 | 0.482 | 1440x1920 | 30 | 0.65 | 6.66 | 11.5 | 0.0058 | 1.5482 | 0.0138 | 0.0/0.0 |
| match_1 | dissolve_1s | 0 | A | homography+dis | 492 | 63.66 | 0.482 | 1440x1920 | 30 | 0.5 | 3.81 | 8.4 | 0.0045 | 0.2587 | 0.0052 | 0.0/0.0 |
| match_1 | morph_3s | 0 | A | homography+dis | 492 | 63.66 | 0.482 | 1440x1920 | 90 | 0.48 | 20.54 | 25.3 | 0.0034 | 0.0629 | 0.0053 | 0.0/0.0 |
| match_2 | morph_1s | 0 | A | homography+dis | 899 | 140.79 | 0.806 | 896x1920 | 30 | 0.38 | 4.7 | 5.6 | 0.0109 | 0.1209 | 0.0492 | 0.0/0.0 |
| match_2 | flow-dissolve_1s | 0 | A | homography+dis | 899 | 140.79 | 0.806 | 896x1920 | 30 | 0.36 | 4.47 | 5.3 | 0.0108 | 0.1208 | 0.0493 | 0.0/0.0 |
| match_2 | snap-morph_1s | 0 | A | homography+dis | 899 | 140.79 | 0.806 | 896x1920 | 30 | 0.37 | 4.43 | 5.5 | 0.0082 | 1.5129 | 0.0507 | 0.0/0.0 |
| match_2 | dissolve_1s | 0 | A | homography+dis | 899 | 140.79 | 0.806 | 896x1920 | 30 | 0.39 | 2.34 | 3.4 | 0.006 | 0.0311 | 0.0087 | 0.0/0.0 |
| match_2 | morph_3s | 0 | A | homography+dis | 899 | 140.79 | 0.806 | 896x1920 | 90 | 0.37 | 13.22 | 14.2 | 0.0084 | 0.0363 | 0.0208 | 0.0/0.0 |
| match_3 | morph_1s | 0 | A | homography+dis | 986 | 38.46 | 0.41 | 1438x1920 | 30 | 0.51 | 7.5 | 8.5 | 0.0038 | 0.117 | 0.0061 | 0.0/0.0 |
| match_3 | flow-dissolve_1s | 0 | A | homography+dis | 986 | 38.46 | 0.41 | 1438x1920 | 30 | 0.52 | 7.2 | 8.2 | 0.0038 | 0.4785 | 0.0061 | 0.0/0.0 |
| match_3 | snap-morph_1s | 0 | A | homography+dis | 986 | 38.46 | 0.41 | 1438x1920 | 30 | 0.52 | 6.92 | 7.9 | 0.0037 | 1.7125 | 0.0069 | 0.0/0.0 |
| match_3 | dissolve_1s | 0 | A | homography+dis | 986 | 38.46 | 0.41 | 1438x1920 | 30 | 0.51 | 3.71 | 4.7 | 0.0031 | 0.0066 | 0.004 | 0.0/0.0 |
| match_3 | morph_3s | 0 | A | homography+dis | 986 | 38.46 | 0.41 | 1438x1920 | 90 | 0.51 | 21.08 | 22.2 | 0.0017 | 0.0558 | 0.0028 | 0.0/0.0 |
| match_4 | morph_1s | 0 | A | homography+dis | 295 | 15.12 | 0.652 | 1536x1920 | 30 | 0.6 | 6.86 | 8.2 | 0.0102 | 0.2446 | 0.016 | 0.0/0.0 |
| match_4 | flow-dissolve_1s | 0 | A | homography+dis | 295 | 15.12 | 0.652 | 1536x1920 | 30 | 0.61 | 7.25 | 8.6 | 0.0102 | 0.4297 | 0.0157 | 0.0/0.0 |
| match_4 | snap-morph_1s | 0 | A | homography+dis | 295 | 15.12 | 0.652 | 1536x1920 | 30 | 0.57 | 6.84 | 8.1 | 0.0098 | 1.6343 | 0.0174 | 0.0/0.0 |
| match_4 | dissolve_1s | 0 | A | homography+dis | 295 | 15.12 | 0.652 | 1536x1920 | 30 | 0.58 | 4.13 | 5.4 | 0.0062 | 0.264 | 0.0073 | 0.0/0.0 |
| match_4 | morph_3s | 0 | A | homography+dis | 295 | 15.12 | 0.652 | 1536x1920 | 90 | 0.58 | 20.27 | 21.8 | 0.0043 | 0.1096 | 0.0063 | 0.0/0.0 |
| match_5 | morph_1s | 0 | A | homography+dis | 73 | 103.45 | 0.329 | 1518x1920 | 30 | 0.76 | 7.86 | 9.7 | 0.0221 | 0.1651 | 0.0507 | 0.0/0.0 |
| match_5 | flow-dissolve_1s | 0 | A | homography+dis | 73 | 103.45 | 0.329 | 1518x1920 | 30 | 0.58 | 8.25 | 9.9 | 0.0222 | 0.2493 | 0.0492 | 0.0/0.0 |
| match_5 | snap-morph_1s | 0 | A | homography+dis | 73 | 103.45 | 0.329 | 1518x1920 | 30 | 0.58 | 8.05 | 9.6 | 0.0182 | 1.8636 | 0.0649 | 0.0/0.0 |
| match_5 | dissolve_1s | 0 | A | homography+dis | 73 | 103.45 | 0.329 | 1518x1920 | 30 | 0.66 | 4.24 | 6.0 | 0.0074 | 0.0922 | 0.0098 | 0.0/0.0 |
| match_5 | morph_3s | 0 | A | homography+dis | 73 | 103.45 | 0.329 | 1518x1920 | 90 | 0.6 | 22.96 | 24.9 | 0.0139 | 0.0646 | 0.0228 | 0.0/0.0 |
| mismatch_1 | morph_1s | 0 | B | saliency-similarity | 10 | 320.84 | 0.5 | 1444x1920 | 30 | 1.61 | 7.42 | 10.2 | 0.0128 | 0.1707 | 0.0329 | 0.0/0.0 |
| mismatch_1 | flow-dissolve_1s | 0 | B | saliency-similarity | 10 | 320.84 | 0.5 | 1444x1920 | 30 | 1.59 | 7.17 | 9.9 | 0.0133 | 0.3665 | 0.035 | 0.0/0.0 |
| mismatch_1 | snap-morph_1s | 0 | B | saliency-similarity | 10 | 320.84 | 0.5 | 1444x1920 | 30 | 1.59 | 7.48 | 10.2 | 0.0121 | 1.4673 | 0.0359 | 0.0/0.0 |
| mismatch_1 | dissolve_1s | 0 | B | saliency-similarity | 10 | 320.84 | 0.5 | 1444x1920 | 30 | 1.61 | 3.78 | 6.5 | 0.0077 | 0.2536 | 0.0109 | 0.0/0.0 |
| mismatch_1 | morph_3s | 0 | B | saliency-similarity | 10 | 320.84 | 0.5 | 1444x1920 | 90 | 1.69 | 21.12 | 24.2 | 0.0064 | 0.0828 | 0.0143 | 0.0/0.0 |
| mismatch_2 | morph_1s | 0 | B | saliency-similarity | 6 | 239.39 | 0.5 | 730x800 | 30 | 0.3 | 1.97 | 2.7 | 0.016 | 0.2036 | 0.0922 | 0.0/0.0 |
| mismatch_2 | flow-dissolve_1s | 0 | B | saliency-similarity | 6 | 239.39 | 0.5 | 730x800 | 30 | 0.29 | 2.18 | 2.9 | 0.0157 | 0.2459 | 0.0864 | 0.0/0.0 |
| mismatch_2 | snap-morph_1s | 0 | B | saliency-similarity | 6 | 239.39 | 0.5 | 730x800 | 30 | 0.29 | 1.92 | 2.7 | 0.015 | 1.9394 | 0.1091 | 0.0/0.0 |
| mismatch_2 | dissolve_1s | 0 | B | saliency-similarity | 6 | 239.39 | 0.5 | 730x800 | 30 | 0.29 | 0.83 | 1.6 | 0.0105 | 0.5486 | 0.0147 | 0.0/0.0 |
| mismatch_2 | morph_3s | 0 | B | saliency-similarity | 6 | 239.39 | 0.5 | 730x800 | 90 | 0.29 | 5.59 | 6.6 | 0.0081 | 0.1166 | 0.0464 | 0.0/0.0 |
| mismatch_3 | morph_1s | 0 | B | saliency-similarity | 6 | 889.16 | 0.5 | 1920x1440 | 30 | 1.84 | 8.13 | 10.7 | 0.0337 | 0.3068 | 0.147 | 0.0/0.0 |
| mismatch_3 | flow-dissolve_1s | 0 | B | saliency-similarity | 6 | 889.16 | 0.5 | 1920x1440 | 30 | 1.97 | 8.11 | 10.8 | 0.0338 | 0.3082 | 0.1502 | 0.0/0.0 |
| mismatch_3 | snap-morph_1s | 0 | B | saliency-similarity | 6 | 889.16 | 0.5 | 1920x1440 | 30 | 1.84 | 8.4 | 11.0 | 0.0279 | 1.5616 | 0.1592 | 0.0/0.0 |
| mismatch_3 | dissolve_1s | 0 | B | saliency-similarity | 6 | 889.16 | 0.5 | 1920x1440 | 30 | 1.85 | 3.75 | 6.4 | 0.0093 | 0.0994 | 0.0138 | 0.0/0.0 |
| mismatch_3 | morph_3s | 0 | B | saliency-similarity | 6 | 889.16 | 0.5 | 1920x1440 | 90 | 1.86 | 23.35 | 26.2 | 0.0225 | 0.0602 | 0.0997 | 0.0/0.0 |
| mismatch_4 | morph_1s | 0 | B | saliency-similarity | 9 | 269.29 | 0.5 | 1920x1236 | 30 | 1.15 | 6.44 | 8.3 | 0.0052 | 0.2543 | 0.0196 | 0.0/0.0 |
| mismatch_4 | flow-dissolve_1s | 0 | B | saliency-similarity | 9 | 269.29 | 0.5 | 1920x1236 | 30 | 1.12 | 6.1 | 7.9 | 0.0051 | 0.3414 | 0.0192 | 0.0/0.0 |
| mismatch_4 | snap-morph_1s | 0 | B | saliency-similarity | 9 | 269.29 | 0.5 | 1920x1236 | 30 | 1.25 | 5.79 | 7.8 | 0.0047 | 1.9861 | 0.027 | 0.0/0.0 |
| mismatch_4 | dissolve_1s | 0 | B | saliency-similarity | 9 | 269.29 | 0.5 | 1920x1236 | 30 | 1.14 | 3.33 | 5.2 | 0.0052 | 0.4141 | 0.0071 | 0.0/0.0 |
| mismatch_4 | morph_3s | 0 | B | saliency-similarity | 9 | 269.29 | 0.5 | 1920x1236 | 90 | 1.14 | 17.69 | 19.8 | 0.0034 | 0.096 | 0.01 | 0.0/0.0 |
| mismatch_5 | morph_1s | 0 | B | saliency-similarity | 36 | 367.85 | 0.5 | 1920x1080 | 30 | 1.44 | 5.67 | 8.6 | 0.0086 | 0.2567 | 0.0238 | 0.0/0.0 |
| mismatch_5 | flow-dissolve_1s | 0 | B | saliency-similarity | 36 | 367.85 | 0.5 | 1920x1080 | 30 | 1.28 | 5.9 | 8.7 | 0.0086 | 0.2821 | 0.0238 | 0.0/0.0 |
| mismatch_5 | snap-morph_1s | 0 | B | saliency-similarity | 36 | 367.85 | 0.5 | 1920x1080 | 30 | 1.25 | 5.65 | 8.4 | 0.0075 | 1.2323 | 0.0236 | 0.0/0.0 |
| mismatch_5 | dissolve_1s | 0 | B | saliency-similarity | 36 | 367.85 | 0.5 | 1920x1080 | 30 | 1.25 | 2.7 | 5.4 | 0.0054 | 0.2732 | 0.0083 | 0.0/0.0 |
| mismatch_5 | morph_3s | 0 | B | saliency-similarity | 36 | 367.85 | 0.5 | 1920x1080 | 90 | 1.25 | 16.37 | 19.3 | 0.0049 | 0.0703 | 0.0138 | 0.0/0.0 |
| mismatch_6 | morph_1s | 0 | B | saliency-similarity | 0 | 232.19 | 0.5 | 1146x1528 | 30 | 1.29 | 8.75 | 11.2 | 0.0213 | 0.521 | 0.0372 | 0.0/0.0 |
| mismatch_6 | flow-dissolve_1s | 0 | B | saliency-similarity | 0 | 232.19 | 0.5 | 1146x1528 | 30 | 1.24 | 8.77 | 11.1 | 0.0215 | 0.722 | 0.0383 | 0.0/0.0 |
| mismatch_6 | snap-morph_1s | 0 | B | saliency-similarity | 0 | 232.19 | 0.5 | 1146x1528 | 30 | 1.29 | 8.59 | 11.0 | 0.02 | 1.1331 | 0.0365 | 0.0/0.0 |
| mismatch_6 | dissolve_1s | 0 | B | saliency-similarity | 0 | 232.19 | 0.5 | 1146x1528 | 30 | 1.46 | 4.44 | 7.1 | 0.0173 | 0.7864 | 0.02 | 0.0/0.0 |
| mismatch_6 | morph_3s | 0 | B | saliency-similarity | 0 | 232.19 | 0.5 | 1146x1528 | 90 | 1.25 | 23.55 | 26.2 | 0.0083 | 0.4358 | 0.0153 | 0.0/0.0 |
| mismatch_7 | morph_1s | 0 | A | homography+dis | 70 | 249.85 | 0.053 | 1920x1488 | 30 | 0.65 | 13.44 | 15.4 | 0.012 | 0.2608 | 0.0476 | 0.0/0.0 |
| mismatch_7 | flow-dissolve_1s | 0 | A | homography+dis | 70 | 249.85 | 0.053 | 1920x1488 | 30 | 0.67 | 12.96 | 14.8 | 0.0114 | 0.3044 | 0.0472 | 0.0/0.0 |
| mismatch_7 | snap-morph_1s | 0 | A | homography+dis | 70 | 249.85 | 0.053 | 1920x1488 | 30 | 0.61 | 12.35 | 14.1 | 0.011 | 1.8519 | 0.0532 | 0.0/0.0 |
| mismatch_7 | dissolve_1s | 0 | A | homography+dis | 70 | 249.85 | 0.053 | 1920x1488 | 30 | 0.63 | 6.59 | 8.4 | 0.0085 | 0.3719 | 0.0123 | 0.0/0.0 |
| mismatch_7 | morph_3s | 0 | A | homography+dis | 70 | 249.85 | 0.053 | 1920x1488 | 90 | 0.64 | 36.85 | 38.9 | 0.0073 | 0.1045 | 0.0267 | 0.0/0.0 |
