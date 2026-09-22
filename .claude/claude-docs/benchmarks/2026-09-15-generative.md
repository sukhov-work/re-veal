# Generative sheet, 2026-09-15 (fourth session) — the bridge on the deterministic skeleton

Runs: `scripts/research/gen_bridge.py` (TR6-A: skeleton → SD 1.5 SDEdit → measure → page),
`scripts/research/depth_dolly.py` (TR10: a depth-modulated pan-zoom, exported as a skeleton),
two sub-agent tracks on the published two-image morphers (TR6-A2), and the LTX-2.3 keyframe
levers plus two skeleton-conditioned LTX modes (TR6-B). M3 Pro 36 GB; three GPU jobs ran at
once for most of the evening, so every wall time here is an upper bound on an idle machine.
Pages (gitignored): `benchmarks/runs/2026-09-15/gen/index.html` (pick control exports
`gen_bridge_picks.json`), `benchmarks/runs/2026-09-15/depth/index.html` (`depth_dolly_picks.json`),
morpher clips and reports under `benchmarks/runs/2026-09-15/morphers/`, LTX clips under
`benchmarks/runs/2026-09-15/ltx/`. Design of record: `TRANSITIONS.md §10.7` (amended this session).

**What varies in the bridge page:** whether a diffusion model re-draws the in-between frames, how
much (SDEdit strength: 0.4 = 8 of 20 steps, 0.6 = 12 of 20), whether its noise follows the
skeleton's motion, and two post-passes. The skeleton is the tool's own clip: class B pan-and-zoom
for mismatch_1 (skies over the city, 1444×1920 → 384×512 for the generator) and mismatch_4
(sunset to sunset, 1920×1092 → 512×288), TR14's `hold-dis` field for match_4 (graffiti box to
mural, 1536×1920 → 408×512; the generator works inside the changed mask, 27.6 % of the canvas,
the skeleton is pasted back outside it). 30 frames, 1 s. Frames 0 and 29 are the skeleton's in
every clip. Prompts (recorded in each pair's `meta.json`): mismatch_1 "clouds drifting over the
city, the blue daytime sky turning to a cloudy dusk, photo"; mismatch_4 "the sun sinking toward
the horizon over the river, its reflection on the water, the skyline in silhouette, photo";
match_4 "a painted mosaic mural on a street utility box, photo". Guidance 6, seed 0.

| clip | what it is |
|---|---|
| `skeleton_small` / `skeleton_native` | the tool's clip at the generator's canvas / at the native canvas (the floor every number is read against) |
| `gen_indep_s0.4` / `_s0.6` | every in-between frame re-drawn from fresh Gaussian noise (seed 1000·0 + i) |
| `gen_warped_s0.4` / `_s0.6` | frame 0's noise carried along the skeleton's cumulative displacement (nearest neighbour at pixel resolution, 8×8 block sums / 8 to the latent grid: Gaussian preserved; the research artifact's `warp_noise_along_flow`, simplified) |
| `gen_warped-ramp_s0.6` | warped noise, strength ramped as 0.6 · sin(πu): nothing re-drawn at the endpoints |
| `smooth_*` | a warped clip filtered along the skeleton's flow: each frame averaged with two neighbours each side warped into it (weights 1 2 3 2 1; the endpoints take part) |
| `lift_*` / `lift-smooth_*` | the warped / smoothed clip lifted to the native canvas: the generator's low frequencies under the skeleton's fine detail (`frequency_split_blend`, σ 3 px) |
| `mismatch_N-depth25/*` | the same bridge over the TR10 depth skeleton (25 % zoom) |

Columns: `step` = mean / max adjacent-frame gray change (levels); `first / last` = the step out
of A and into B; `skeleton-flow error` = mean |frame i+1 − frame i warped by the skeleton's
inter-frame displacement| on gray in [0, 1] (the skeleton clip's own value is the floor: how far a
clip's motion is from the skeleton's); `warping error` and `edge_ratio` are the tool's basket;
`vs skeleton` = mean absolute difference of the in-between frames to the skeleton's (levels);
`s / frame` = generator wall time per frame (beside other GPU jobs).

## 1. TR6-A — the bridge (SD 1.5 inpainting, MPS fp16, diffusers 0.40, torch 2.14)

Endpoints are 0 / 0 in every clip (the skeleton's frames). The same seed reproduces byte for byte (the `_rep` row).

**mismatch_1** — skeleton `saliency-panzoom`, canvas 1444×1920 → generator 384×512, mask 1.0 of the canvas.

| clip | step mean / max | first / last | skeleton-flow error | warping error | edge_ratio | vs skeleton | s / frame |
|---|---|---|---|---|---|---|---|
| `skeleton_native` | 4.00 / 5.36 | 0.7 / 1.0 | 0.0112 | 0.0111 | 0.19 |  |  |
| `skeleton_small` | 3.36 / 4.70 | 0.6 / 0.7 | 0.0102 | 0.0102 | 0.20 |  |  |
| `gen_indep_s0.4` | 11.88 / 13.79 | 10.9 / 9.1 | 0.0458 | 0.0541 | 0.89 | 11.36 | 8.58 |
| `gen_indep_s0.6` | 17.83 / 21.00 | 15.8 / 12.3 | 0.0692 | 0.0793 | 0.86 | 16.49 | 17.95 |
| `gen_warped-ramp_s0.6` | 8.80 / 15.14 | 4.5 / 4.0 | 0.0336 | 0.0338 | 0.45 | 13.43 | 10.65 |
| `gen_warped_s0.4` | 9.19 / 15.13 | 10.8 / 15.1 | 0.0352 | 0.0357 | 1.73 | 14.16 | 10.78 |
| `gen_warped_s0.4_rep` | seed repeat of `gen_warped_s0.4`: max abs diff 0 over 5 frames | | | | | | |
| `gen_warped_s0.6` | 16.36 / 32.80 | 15.6 / 32.8 | 0.0634 | 0.0620 | 2.11 | 25.11 | 14.14 |
| `smooth-ramp_s0.6` | 3.86 / 5.49 | 3.1 / 3.1 | 0.0130 | 0.0149 | 0.74 | 11.56 |  |
| `smooth_s0.4` | 4.02 / 9.42 | 6.9 / 9.4 | 0.0139 | 0.0160 | 2.56 | 12.08 |  |
| `smooth_s0.6` | 6.39 / 21.11 | 10.2 / 21.1 | 0.0227 | 0.0243 | 3.75 | 21.0 |  |
| `lift-ramp_s0.6` | 8.43 / 14.21 | 3.4 / 3.2 | 0.0313 | 0.0321 | 0.39 | 12.38 |  |
| `lift-smooth-ramp_s0.6` | 4.58 / 6.16 | 2.5 / 2.8 | 0.0142 | 0.0154 | 0.63 | 10.83 |  |
| `lift-smooth_s0.4` | 4.77 / 8.90 | 6.1 / 8.9 | 0.0151 | 0.0166 | 2.27 | 11.34 |  |
| `lift-smooth_s0.6` | 6.83 / 20.09 | 9.4 / 20.1 | 0.0229 | 0.0244 | 3.56 | 20.12 |  |
| `lift_s0.4` | 8.82 / 14.03 | 9.5 / 14.0 | 0.0328 | 0.0343 | 1.72 | 13.11 |  |
| `lift_s0.6` | 15.42 / 30.73 | 14.2 / 30.7 | 0.0592 | 0.0589 | 2.12 | 23.71 |  |

**mismatch_4** — skeleton `saliency-panzoom`, canvas 1920×1092 → generator 512×288, mask 1.0 of the canvas.

| clip | step mean / max | first / last | skeleton-flow error | warping error | edge_ratio | vs skeleton | s / frame |
|---|---|---|---|---|---|---|---|
| `skeleton_native` | 2.69 / 3.36 | 0.6 / 0.6 | 0.0081 | 0.0059 | 0.23 |  |  |
| `skeleton_small` | 2.08 / 2.85 | 0.4 / 0.5 | 0.0071 | 0.0053 | 0.25 |  |  |
| `gen_indep_s0.4` | 7.21 / 9.59 | 5.8 / 6.9 | 0.0279 | 0.0261 | 0.93 | 6.68 | 6.0 |
| `gen_indep_s0.6` | 11.59 / 16.39 | 7.9 / 9.2 | 0.0451 | 0.0425 | 0.77 | 10.09 | 13.25 |
| `gen_warped-ramp_s0.6` | 7.02 / 16.64 | 3.0 / 3.6 | 0.0273 | 0.0257 | 0.47 | 9.29 | 7.5 |
| `gen_warped_s0.4` | 6.91 / 11.98 | 5.2 / 12.0 | 0.0268 | 0.0256 | 1.79 | 9.35 | 7.71 |
| `gen_warped_s0.6` | 13.43 / 29.77 | 10.0 / 29.8 | 0.0526 | 0.0501 | 2.32 | 17.2 | 13.71 |
| `smooth-ramp_s0.6` | 2.89 / 4.97 | 1.8 / 2.6 | 0.0100 | 0.0099 | 0.87 | 7.67 |  |
| `smooth_s0.4` | 2.79 / 6.85 | 3.2 / 6.8 | 0.0099 | 0.0098 | 2.63 | 7.76 |  |
| `smooth_s0.6` | 4.88 / 16.44 | 6.3 / 16.4 | 0.0176 | 0.0173 | 3.79 | 13.77 |  |
| `lift-ramp_s0.6` | 6.79 / 15.54 | 2.6 / 3.1 | 0.0256 | 0.0244 | 0.45 | 8.65 |  |
| `lift-smooth-ramp_s0.6` | 3.40 / 5.06 | 1.6 / 2.4 | 0.0110 | 0.0102 | 0.78 | 7.28 |  |
| `lift-smooth_s0.4` | 3.38 / 6.39 | 3.1 / 6.4 | 0.0110 | 0.0102 | 2.34 | 7.39 |  |
| `lift-smooth_s0.6` | 5.13 / 15.51 | 6.1 / 15.5 | 0.0177 | 0.0171 | 3.65 | 13.18 |  |
| `lift_s0.4` | 6.76 / 11.07 | 4.8 / 11.1 | 0.0253 | 0.0244 | 1.75 | 8.76 |  |
| `lift_s0.6` | 12.71 / 27.83 | 9.6 / 27.8 | 0.0492 | 0.0474 | 2.32 | 16.2 |  |

**match_4** — skeleton `hold-dis`, canvas 1536×1920 → generator 408×512, mask 0.276 of the canvas.

| clip | step mean / max | first / last | skeleton-flow error | warping error | edge_ratio | vs skeleton | s / frame |
|---|---|---|---|---|---|---|---|
| `skeleton_native` | 3.18 / 4.52 | 0.7 / 0.8 | 0.0079 | 0.0083 | 0.26 |  |  |
| `skeleton_small` | 2.06 / 3.03 | 0.5 / 0.6 | 0.0073 | 0.0067 | 0.29 |  |  |
| `gen_indep_s0.4` | 9.45 / 11.53 | 10.9 / 7.2 | 0.0361 | 0.0323 | 1.16 | 8.16 | 12.05 |
| `gen_indep_s0.6` | 11.27 / 13.75 | 13.2 / 9.3 | 0.0432 | 0.0382 | 1.19 | 10.15 | 16.97 |
| `gen_warped-ramp_s0.6` | 5.03 / 6.67 | 5.4 / 4.0 | 0.0189 | 0.0162 | 1.04 | 8.06 | 13.27 |
| `gen_warped_s0.4` | 4.75 / 10.71 | 10.7 / 7.1 | 0.0178 | 0.0154 | 2.64 | 8.4 | 13.4 |
| `gen_warped_s0.6` | 5.69 / 13.32 | 13.3 / 9.2 | 0.0215 | 0.0185 | 2.81 | 10.62 | 16.53 |
| `smooth-ramp_s0.6` | 2.65 / 3.88 | 3.9 / 2.9 | 0.0096 | 0.0090 | 1.41 | 7.88 |  |
| `smooth_s0.4` | 2.59 / 7.26 | 7.3 / 4.8 | 0.0094 | 0.0088 | 3.24 | 8.24 |  |
| `smooth_s0.6` | 2.84 / 9.03 | 9.0 / 6.2 | 0.0104 | 0.0097 | 3.87 | 10.24 |  |
| `lift-ramp_s0.6` | 4.80 / 6.76 | 3.4 / 2.6 | 0.0146 | 0.0148 | 0.80 | 6.05 |  |
| `lift-smooth-ramp_s0.6` | 3.68 / 4.71 | 2.7 / 2.1 | 0.0101 | 0.0103 | 0.93 | 5.66 |  |
| `lift-smooth_s0.4` | 3.67 / 5.82 | 5.8 / 3.7 | 0.0100 | 0.0103 | 2.31 | 5.94 |  |
| `lift-smooth_s0.6` | 3.85 / 7.54 | 7.5 / 5.0 | 0.0107 | 0.0110 | 2.93 | 7.9 |  |
| `lift_s0.4` | 4.70 / 8.41 | 8.4 / 5.3 | 0.0141 | 0.0145 | 2.40 | 6.36 |  |
| `lift_s0.6` | 5.32 / 10.96 | 11.0 / 7.3 | 0.0166 | 0.0170 | 2.75 | 8.46 |  |

**mismatch_1-depth25** — skeleton `depth-panzoom z25`, canvas 1444×1920 → generator 384×512, mask 1.0 of the canvas.

| clip | step mean / max | first / last | skeleton-flow error | warping error | edge_ratio | vs skeleton | s / frame |
|---|---|---|---|---|---|---|---|
| `skeleton_native` | 4.80 / 6.54 | 1.2 / 1.1 | 0.0136 | 0.0123 | 0.20 |  |  |
| `skeleton_small` | 4.04 / 5.70 | 0.8 / 0.7 | 0.0121 | 0.0112 | 0.20 |  |  |
| `gen_warped_s0.4` | 13.27 / 21.28 | 10.7 / 21.3 | 0.0514 | 0.0506 | 1.66 | 18.03 | 11.26 |
| `smooth_s0.4` | 5.58 / 12.40 | 6.8 / 12.4 | 0.0178 | 0.0202 | 2.38 | 14.57 |  |
| `lift-smooth_s0.4` | 6.30 / 11.71 | 6.2 / 11.7 | 0.0190 | 0.0206 | 2.17 | 13.74 |  |
| `lift_s0.4` | 12.62 / 19.68 | 9.5 / 19.7 | 0.0477 | 0.0479 | 1.64 | 16.7 |  |

**mismatch_4-depth25** — skeleton `depth-panzoom z25`, canvas 1920×1092 → generator 512×288, mask 1.0 of the canvas.

| clip | step mean / max | first / last | skeleton-flow error | warping error | edge_ratio | vs skeleton | s / frame |
|---|---|---|---|---|---|---|---|
| `skeleton_native` | 3.00 / 3.87 | 0.9 / 0.8 | 0.0101 | 0.0068 | 0.24 |  |  |
| `skeleton_small` | 2.36 / 3.32 | 0.5 / 0.6 | 0.0087 | 0.0062 | 0.25 |  |  |
| `gen_warped_s0.4` | 13.61 / 24.70 | 5.1 / 24.7 | 0.0530 | 0.0500 | 1.84 | 17.34 | 8.65 |
| `smooth_s0.4` | 6.00 / 14.84 | 3.3 / 14.8 | 0.0179 | 0.0187 | 2.60 | 13.36 |  |
| `lift-smooth_s0.4` | 6.18 / 14.04 | 3.2 / 14.0 | 0.0184 | 0.0186 | 2.52 | 12.79 |  |
| `lift_s0.4` | 12.88 / 22.83 | 4.8 / 22.8 | 0.0497 | 0.0470 | 1.82 | 16.23 |  |

## 2. TR6-A2 — the two published two-image morphers (sub-agent tracks; reports beside the clips)

| | DreamMover (`leoShen917/DreamMover`, SD 1.5) | DiffMorpher (`Kevin-thu/DiffMorpher`, SD 2.1-base) |
|---|---|---|
| Install | one `uv` install (Python 3.11, torch 2.14.0 MPS, diffusers 0.17.1) after five source patches: the cupy softsplat kernel rewritten in PyTorch (agrees to 1.2e-6), a chunked `scaled_dot_product_attention` in place of xformers, `.cuda()` → device helper, a vectorised `feature_flow`, batch 34 | one `uv` install (Python 3.11, torch 2.5.1, diffusers 0.17.1) after five CUDA-to-MPS patches; imports and runs |
| Weights | `stable-diffusion-v1-5/stable-diffusion-v1-5` fp32, 4.0 GB, not gated | `stabilityai/stable-diffusion-2-1-base` is GATED and returns 404 to the owner's token (`whoami` OK, `stabilityai/sd-vae-ft-mse` fetches): the licence has not been accepted on that model page. No run was possible |
| Minutes per pair, 512 px, repo defaults | mismatch_1 18.2 (run 1) and 12.0 (run 2), mismatch_4 8.8; peak memory footprint 18–20 GB (the port swapped 28 GB before attention was chunked) | measured on a random-weight UNet of the exact SD 2.1-base shape (865.9 M parameters): 0.502 s per fp32 UNet step, 2.43 s per rank-16 LoRA training step → 42 min per pair at the README's recipe (16 min of LoRA fitting + 26 min of sampling; `--use_reschedule` runs the morph twice), 7.5 min with no LoRA and the smallest frame count; fp16 is 2.5× SLOWER than fp32 on this torch build |
| Reproducible | yes to 1 level (325 of 20 M subpixels differ); no seed exists: latents come from DDIM inversion | untested (no weights); the code samples nothing at inference |
| Endpoints | re-drawn, never the photos: frame 0 vs A 6.6 / frame 33 vs B 4.5 gray MAD on mismatch_1 (A–B 53.5), 3.7 / 4.6 on mismatch_4 (A–B 33.5); rooftop antennas redrawn, a haze band not in B | — |
| Motion | a morph: pixels travel along the model's correspondence (clouds deform, the sun and its reflection travel together on mismatch_4); one seam at frame 16 where the two latents swap (step 11.2 / 9.7 levels against means 4.2 / 2.7) | — |
| Licence | NONE (no licence file at commit `bdfaa3a`, 2024-09-20): all rights reserved; nothing can be vendored | S-Lab 1.0, non-commercial: personal use is within it |
| Gate E16 (≤ 6 min per pair, lands on the endpoints) | FAIL on both counts | FAIL on cost in every configuration; the look is unmeasured |

Reading: DreamMover's mismatch_4 clip is the closest thing to a "truthful continuous
transformation" of the sun-to-sun pair seen so far (the sun travels with its reflection), at
8.8 min and with re-drawn endpoints that the tool's byte-exact frames 0 and n−1 would have to
replace; its lack of a licence rules it out as code, and its mechanism (DDIM inversion of both
photos + feature-matched flow + a latent swap at the midpoint) is what a Reveal-native version
would have to re-implement. DiffMorpher's cost model rules it out before the licence question.

## 3. TR6-B — LTX-2.3 (int4, MLX port), keyframe levers and two skeleton-conditioned modes

| clip (49 frames, seed 0, dev transformer + CFG 3.0 + 1.1 LoRA) | wall / RSS | endpoints (MAD to A / to B; A–B) | adjacent step mean / max (at frame) | reading |
|---|---|---|---|---|
| `match_4_kf49_strength08` (previous session) | 540 s / 14.4 GB | 21.6 / 16.2; 54 | — / 4.2 | continuous: the first generative candidate |
| `mismatch_1_kf49_s08` (start/end strength 0.8) | 1849 s beside two GPU jobs / 8.4 GB | 5.3 / 5.3; 54.6 | 4.5 / 38.0 (28) | a CUT at frame 28: the clouds drift for 27 frames (distance to A rises 5 → 29), then the finish scene replaces the start scene in one step |
| `mismatch_4_kf49_s08` | 1961 s / 7.7 GB | 7.4 / 10.7; 32.6 | 3.8 / 21.1 (31) | a cut at frame 31 after the sun and its reflection drift toward B's composition (distance to A 7 → 30) |
| `match_4_kf49_s06` (start/end strength 0.6) | 736 s beside the SD batch / 14.6 GB | 22.4 / 16.8; 34.4 | 4.0 / 4.8 (41) | continuous like 0.8: distance to A rises 22 → 36 and to B falls 37 → 17 monotonically; the endpoints are no closer to the photos than at 0.8 |
| `mismatch_1_anchors5` (`generate --two-stage` with the skeleton's frames 0 / 12 / 24 / 36 / 48 anchored at strengths 0.8 / 0.6 / 0.6 / 0.6 / 0.8) | 1107 s beside the SD batch / 13.8 GB | 4.4 / 8.4; 54.6 | 2.28 / 3.87 (29) | no cut, monotone; the clip follows the skeleton's crossfade (11.3 levels from the 49-frame skeleton clip on average, 3–15 per frame) and reproduces its double exposure at frames 24–32 instead of resolving it: the middle anchors at 0.6 carry the crossfade into the model |
| `mismatch_1_retake` (`retake` of latent frames 2–4 = pixel frames 9–32 of the 49-frame skeleton clip, 30 steps, CFG 3.0) | 1505 s beside the SD batch / 15.0 GB | 4.4 / 4.0; 54.6 | 1.97 / 2.73 (11) | continuous and monotone, and a re-encoding of the skeleton: the regenerated frames are 4.6 levels from the skeleton clip on average (the kept frames 2.4, which is the codec), so the model kept the skeleton's crossfade instead of re-dreaming the middle |
| `mismatch_4_anchors5` (same five-anchor recipe; the port rendered 512×256, not 288) | 512 s alone / 14.4 GB | 7.6 / 12.7; 32.6 | 1.32 / 3.41 (1) | continuous; distance to B rises 35 → 37.5 over the first eight frames before it falls; 11.7 levels from the skeleton clip (resized), the same order as mismatch_1's anchored run: the skeleton's crossfade carried through the model |

Not run this session (dropped for the skeleton-conditioned modes above; the owner's priority is
the mismatches): match_4 at strength 0.9 and at 97 frames; the q8 pack.

## 4. TR10 — the depth camera move (Depth Anything V2 Small, Apache-2.0, transformers 5.17 on MPS)

Depth: 0.3–2.7 s per image at the native canvas (the first call includes warm-up), model 99 MB.
Motion: the tool's pan-zoom field × (0.5 + disparity), disparity in [0, 1] from the 2nd–98th
percentile of the model's relative inverse depth; near content wins the splat (importance
0.2 + 0.8 · disparity). 2 s clips, morph preset, native canvas.

| pair · clip | disp median / far / near px | hole at mid frame A / B | step mean / max | warping error | edge_ratio | render s |
|---|---|---|---|---|---|---|
| mismatch_1 `panzoom_z10` (the tool) | 105 / 42 / 178 | 0 / 0 | 1.79 / 2.55 | 0.0064 | 0.14 | 24.5 |
| mismatch_1 `depth_z10` | 57 / 31 / 90 | 0.0001 / 0.006 | 1.61 / 2.32 | 0.0062 | 0.16 | 23.2 |
| mismatch_1 `panzoom_z25` | 263 / 105 / 445 | 0 / 0 | 2.60 / 3.75 | 0.0081 | 0.12 | 24.9 |
| mismatch_1 `depth_z25` | 142 / 77 / 225 | 0.0016 / 0.009 | 2.24 / 3.26 | 0.0076 | 0.13 | 33.6 |
| mismatch_4 `panzoom_z10` | 98 / 37 / 156 | 0 / 0 | 1.15 / 1.61 | 0.0038 | 0.16 | 21.5 |
| mismatch_4 `depth_z10` | 69 / 22 / 170 | 0 / 0 | 1.05 / 1.45 | 0.0038 | 0.18 | 14.5 |
| mismatch_4 `panzoom_z25` | 155 / 65 / 297 | 0 / 0 | 1.61 / 2.24 | 0.0044 | 0.14 | 19.2 |
| mismatch_4 `depth_z25` | 116 / 37 / 291 | 0.0001 / 0.0002 | 1.38 / 1.86 | 0.0043 | 0.15 | 20.2 |

Reading: no tearing by eye at either zoom (holes ≤ 0.9 % of the canvas at the mid frame), the
mean step 10–14 % below the uniform pan-zoom, warping error equal or lower. The median
displacement halves because most of each canvas is far content (sky, water). A mid frame is
still a crossfade of two zoomed photos: the depth move alone does not change the character the
owner objects to; its value is as the generator's skeleton (§1, the `-depth25` rows).

## 5. Reading (the agent's; the owner's picks decide)

1. The first configuration that passes the research plan's E17 gate on every pair tried is the
   per-frame SD bridge with warped noise, the strength ramped as 0.6 · sin(πu), and the filter
   along the skeleton's flow (`smooth-ramp_s0.6`): mean adjacent step 1.15× (mismatch_1), 1.39×
   (mismatch_4) and 1.29× (match_4) the skeleton's, the step into B 2.6–3.1 levels, the content
   7.7–11.6 levels away from the skeleton (so the filter does not collapse it back). Lifted to the
   native canvas the ratios are 1.15–1.26×. Each 30-frame clip costs 3.5–6.5 min of generator time
   at strength 0.6 peak beside other GPU jobs, and the endpoints are the tool's.
2. What the basket does not see: match_4 gets a different mural in every frame (the per-frame
   model has no memory of the previous frame); mismatch_4 at 512×288 gets blocky tiles in the sky
   and water at both strengths; mismatch_1 is the one clip that reads as a transformation by the
   agent's eye (the city stays a city while the sky changes). The owner's picks decide.
3. The depth skeleton (TR10) doubles the bridge's flicker (its larger motion moves the warped
   noise more) and, alone, is a crossfade with parallax. Not a route on its own.
4. The video model with the skeleton anchored (LTX `generate`, five skeleton frames) is continuous
   on mismatch_1 where plain keyframe interpolation cuts, but it copies the skeleton's double
   exposure; weaker middle anchors (0.3) or `retake` on the skeleton clip are the next levers.
   Keyframe interpolation at strength 0.8 cuts on both mismatched pairs (frame 28 / 31).
5. Neither published morpher is adoptable: DreamMover fails the 6-minute gate (8.8–18.2 min) and
   re-draws the endpoints, and has no licence; DiffMorpher's weights are not granted to the
   owner's account and its cost model is 42 min per pair. DreamMover's sun-to-sun clip is still
   the most morph-like result of the session and is on the page for the owner's eye.

## 6. Owner picks (2026-09-22 `benchmarks/runs/2026-09-15/gen/gen_bridge_picks.json`; 2026-09-23 message)

Bridge page: all five pairs `none`, acceptable as-is unticked. Note on mismatch_1, mismatch_4,
mismatch_1-depth25 and mismatch_4-depth25 (one text): "motion transformation is horrible neural
slop very low resolution transitions with neural network heavy halucinations artifacts in almost
all intermediate frames which preserve no features and make both images unrecognizable  ( except
skeletons, which are again dumb crossfades) ". Note on match_4: "motion transformation is horrible
neural slop transitions with neural network heavy halucinations artifacts in all intermediate
frames which do even more harm because boxes are pretty closely matched , they do generate random
(changing )images on boxes for all intermediate frames  ( except skeletons, which are too
resembling  to some simple  crossfades) ". Message (2026-09-23): "overall experience was horrible,
heavy neural arifacts, or halucinated intermediate images, noise, chaotic and same crossdes", with
three screenshots: a hallucinated pier and building in a mismatch_4 frame, a blurred and noisy
mismatch_1 frame (its caption "skeleton-flow 0.0229 · warping 0.0244" is `lift-smooth_s0.6`), and
a hallucinated box image on match_4.

Depth page (message, 2026-09-23): "regarding `TR10 — a depth-aware camera move for unrelated
pairs` i really liked the effect on all individual images especially z25 … Transitions still mostly
simple crossfades , nothing imporoved there but this depth animation added really cool dynamics to
before and after images , i think we can utilize that in addition to anything else ( at least as
option )". No `depth_dolly_picks.json` was exported.

Effect: TR6-A as measured is rejected; the E17 gate measured flicker, not the hallucinations the
owner sees, so the basket needs a feature-preservation number before any further generative run
(candidate: SIFT matches between each in-between frame and the nearer endpoint, against the
skeleton's own count). TR10 moves to the top of the plan as an option to build; the `ramp` control
(§4, added 2026-09-23) is on the depth page beside the model's clips for the owner's eye.

Owner answers (2026-09-23, verbatim): "yes to model, and run it on matched pairs too ( as a test,
need to compare) , also note to you:  i watched some videos in benchmarks/runs/2026-09-15/ltx folder,
what it did mostly animated in weird way(generated some content, somewhat realistic but unasked
for)  individual before/after images but transition between animations are usually a cut or dumb
fade so this defeats all purpose ( at least for that test run )  . Prepare for next session".
Effect: the `model` leg of the TR10 option is approved (torch + `transformers` + the 99 MB weight
behind warmup + manifest); the depth move is to be rendered on the matched pairs as a comparison
test before its class A semantics are fixed; the LTX clips are rejected as measured (§3 stays as
the record; the video route is parked with the rest of the generative tier).

Added 2026-09-23 to §4: `ramp_z10` / `ramp_z25` = the same modulation with a top-to-bottom ramp
in place of the model (disparity 0 at the top row, 1 at the bottom; correlation with the model's
disparity 0.62 / 0.82 on mismatch_1 A / B and 0.93 / 0.83 on mismatch_4): mismatch_1 step
1.94 / 2.75 (z10) and 2.83 / 4.08 (z25), mismatch_4 1.15 / 1.61 and 1.58 / 2.24, holes 0 / 0,
warping error 0.0066 / 0.0083 and 0.0039 / 0.0045. Depth Anything V2 Small re-timed in a fresh
environment (torch 2.14.0, transformers, the image processor resizes to 518 px so the cost barely
depends on the input): CPU 0.34 s per image at 1024 px long edge (12 threads), MPS 0.08–0.09 s
after a 1.5 s warm-up; 24.8 M parameters, 99 MB fp32, Apache-2.0.
