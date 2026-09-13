# Real-pair sheet — 2026-09-13 (first run of slice TR2; Reveal rows double as the first H2 sheet)

## Method
Ten pairs the owner placed in `fixtures/` (5 `match`, 5 `mismatch`; 18 JPEG + 2 HEIC; catalogue rows in
`fixtures/MANIFEST.md`). Command: `scripts/bench_transitions.py --out benchmarks/runs/2026-09-13 --reveal`.
Reveal ran `align --mode reshot` at native resolution (loose would have run only if strict refused a
matched pair; it never did). Transitions ran with the canvas capped at 1920 px, presets morph,
flow-dissolve, snap-morph and dissolve at 1.0 s and morph at 3.0 s: 60 runs in all, M3 Pro, one job
at a time. Strips and mp4s are local: open `benchmarks/runs/2026-09-13/index.html` (gitignored).

## Verdict against research gate E2
- Class routing: 10 of 10 as expected (5 match → A, 5 mismatch → B).
- `edge_ratio` on morph, dissolve and flow-dissolve: maximum 0.55 (mismatch_2 dissolve), every run
  below the 1.5 gate. snap-morph measures 1.23–1.99, which its hold-then-go curve produces by design.
- Endpoints: 0 / 0 on every run.
- Owner rating (gate: at least 6 of 10 pairs usable as-is at 1 s): **pending** — the owner reviews `index.html`.

## Observations (four strips looked at by the agent; not a rating)
- match_4, the roster pair: the mural dissolves onto the box while wall and pavement stay put; the box
  edges stay straight through the morph.
- match_5: smooth overall; the box edge doubles in the middle frames (103 px median displacement,
  certainty 0.33).
- match_1 (HEIC): the head ghosts in the middle frames; a non-rigid subject with 64 px of displacement.
- mismatch_4: the saliency similarity put the sun on the sun without anchors; the skylines cross-dissolve.
- mismatch_5: the sun is scaled toward the galaxy core and a rectangular bright patch shows in frames 4–6.
  That is the class B box similarity being crude by design; anchors and semantic matching are slice TR9.
- Reveal: strict passes all five matched pairs at confidence 90–97 and refuses all five mismatched pairs
  with the plain message. On match_3 the ECC stage returned no rho and the feature homography was kept
  (the designed degrade path; the pair still passed at 1059 inliers). The roster pair match_4 measures
  481 inliers and 0.79 px here against 458 and 0.74 in the 2026-07-13 sandbox; OpenCV is 5.0.0 here and
  no estimation code changed, so the delta is the environment, and this row is the new local baseline.

## Speed (canvas ≤ 1920 px, 1.3–2.8 MP)
morph 1 s (30 frames): render 4.7–7.9 s, or 0.16–0.26 s per frame; morph 3 s: 13–23 s; correspondence
0.4–0.65 s once per pair; Reveal `align` 2.2–7.7 s per pair at native resolution (48 MP HEIC: 7.7 s).


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
