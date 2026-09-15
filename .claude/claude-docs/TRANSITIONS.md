# Transitions — design of record (`transitions.py` v0.1.0, as of 2026-09-13)

Transitions renders the change between two photos as a short video. Reveal (`reveal.py`,
`HANDOFF.md`) lines two photos up and hides the change behind a slider; Transitions takes a pair,
typically Reveal's `before.jpg` and `after_aligned.jpg`, and animates one becoming the other: a
flow-guided morph, a dissolve, a portal reveal or a luma wipe, with the colors of both photos meeting
halfway. It is a second single-file tool beside `reveal.py`, in the same virtualenv, with its own
harness (`transitions_harness.py`). The name `transitions` is official (owner, 2026-09-13).

Reference research: `.claude/claude-docs/transitions-research/` holds the "Impossible" v0.1.0
artifact (`RESEARCH-REPORT.md`, `RESEARCH-PLAN.md`, code). This file records what was shipped and
measured here. Decisions live in `DECISIONS.md` (dated lines from 2026-09-13); plan slices in
`EXPLORATION_PLAN.md §TR`.

## 1. Invariants (a violation is a bug; the harness check that pins each one is named)
1. **Isolation.** `transitions.py` never imports `reveal`, and `reveal.py` never imports
   `transitions` (checks 1–2). A change to one tool cannot break the other. The decode, cover and
   SIFT helpers are duplicated on purpose.
2. **Offline, local, CPU.** No import that can reach the network or load model weights (check 3).
   No model files. Reveal's decision 9 (no MPS) holds for the deterministic tier; the device for
   model stages is decided per slice by measurement (`HANDOFF.md §11`).
3. **Inputs are never modified.** Every output is a new file in `--out`: `transition.mp4`,
   `strip.jpg`, `report.json`.
4. **Exact endpoints.** Frame 0 is A and frame n−1 is B, byte for byte, whatever the color path did
   in between (check 21). The decoded mp4 opens on A and closes on B within codec loss (check 29).
5. **Deterministic.** No random source anywhere. Two runs give identical frames in memory
   (check 23) and through ffmpeg (check 33). A performance change must keep the frames
   byte-identical or state in `DECISIONS.md` what moved and by how many levels.
6. **Degradation is visible.** Class B routing prints an INFO line that names the method and says
   how to steer it (check 14). A missing layer or a bad input prints `FAILED: <message>` and exits
   2, never a traceback (check 34).
7. **Constants, no settings file.** Every knob is a CLI option or a `TCFG` constant, as in `reveal.py`.
8. **Identity.** The persisted names (`transitions.py`, `transition.mp4`, `strip.jpg`,
   `report.json`, logger `transitions`) are pinned by check 37; the research codename does not
   occur in the shipped module (check 38).

## 2. Pipeline
1. **Decode** to sRGB uint8 with EXIF orientation applied (Pillow, pillow-heif, rawpy; the same
   routing as Reveal).
2. **Common canvas.** Policy `finish` (default; owner ruling 2026-09-14 "finish target ratio
   wins"): the canvas has the FINISH photo's aspect ratio and is the largest such rectangle both
   photos cover without upscaling; `--canvas common` keeps the older rule (the smaller width and
   the smaller height). Optionally capped by `--max-long`; even dimensions for yuv420p. Each
   endpoint is cover-cropped onto it; a letterbox mode is slice TR13. Anchors are canvas pixels.
3. **Correspondence** (`dense_displacement`). Fields are canvas pixels on the source grid:
   `dAB[y,x] = (dx,dy)` means `B[y+dy, x+dx] ≈ A[y,x]`.
   - **Class A, related pair.** SIFT, ratio test 0.75, MAGSAC++ homography `H_BA` at 2.5 px;
     sanity: convex warped quad with area ratio in [0.15, 6]; at least 30 inliers. Then DIS flow on
     the pre-aligned pair, composed back through `inv(H_BA)`, in both directions. Certainty per
     pixel is `exp(−e²/2σ²)` of the forward-backward error with σ = 3 px. Method
     `homography+dis`; `dis-only` when the class is forced and no usable H exists.
   - **Class B, unrelated pair.** One pan-and-zoom per frame (`panzoom_field`, method
     `saliency-panzoom`, since 2026-09-14): each frame zooms in by `classb_zoom` (10 %) about
     its own salient center (gradient energy, 70th percentile, largest component) and pans toward
     the other frame's salient center as far as the zoom's slack allows, so a frame edge never
     enters the canvas (defect T13). A zooms from 1 to 1.1 while it fades out; B settles from 1.1
     to 1 so the last frame is B itself. The pan keeps its direction and is scaled by the largest
     feasible fraction (`report.json` `pan_fraction`, one value per frame; 1.0 means the two
     salient centers meet throughout). Before 2026-09-14 the field was one similarity between the
     two salient boxes and its splat-and-inpaint inverse; the moved frame's rectangle was visible
     on every mismatched fixture (`§7.2`). With three or more anchor pairs the field is Moving
     Least Squares (affine; Schaefer 2006) with the splat-and-inpaint inverse, unchanged, and its
     frame edge can still show. Certainty is 0.5 everywhere because nothing photometric supports
     it. In class A, anchors are blended over the dense field with weight 0.7.
4. **Per frame** (`iter_frames`). With `u = i/(n−1)`: `t_warp = curve(warp)·warp_amount +
   (1−warp_amount)·u` and `t_mix = curve(mix)(u − mix_delay)`.
   - **Color path.** Both endpoints move toward the Lab statistic interpolated at `u` (per-channel
     mean and standard deviation; the gain is clipped to [0.4, 2.5]). The correction is computed in
     float, scaled by `color_strength`, and rounded once. The Lab and float32 copies of both
     endpoints are computed once per transition (`color_cache`); the frames are byte-identical to
     the per-frame version.
   - **Geometry.** `morph` and `warp-dissolve` forward-splat A along `t·dAB` and B along
     `(1−t)·dBA`. The splat runs on source coordinates at 1/4 resolution with importance weights,
     builds an inverse map, and applies it with one full-resolution `remap`; holes take a
     backward-warp fallback. A coverage-aware cross-dissolve mixes the two. `portal` uses an
     iris mask from the center or a wipe seam moving left to right, feathered by a fraction of the
     diagonal. `luma` reveals B in order of A's brightness. `dissolve` is the plain crossfade.
   - **Rounding.** Every float-to-uint8 cast goes through `to_u8`, which rounds. Truncation
     biases every frame half a level low; against a byte-exact last frame that is a 0.8-level
     step, and the hidden-cut detector read 1.96 on a clean dissolve. Found and fixed 2026-09-13;
     check 24 pins it.
5. **Encode.** Frames stream as rawvideo into the imageio-ffmpeg binary: libx264, crf 18,
   yuv420p, faststart. Memory stays bounded at any canvas.
6. **Quality basket**, computed on a 480-px proxy of every frame and written to `report.json`:
   `warping_error` (flow-warp frame t onto t+1, mean residual on gray), `flicker` with `mean`,
   `max`, `spikiness` and `edge_ratio` (an endpoint step divided by the interior mean; a hidden
   cut scores far above 1), and `endpoint` fidelity, which must be 0. Several numbers, never one.
   Pixel scales depend on the scene, so a pair is compared against itself.

## 3. Grammar and CLI
| Preset | style | Notes |
|---|---|---|
| `morph` (default) | morph | eased warp, eased dissolve |
| `dissolve` | dissolve | warp amount 0 |
| `flow-dissolve` | warp-dissolve | warp 0.6, dissolve delayed by 0.1 |
| `snap-morph` | morph | hold-then-go warp, ease-in mix; inflates `edge_ratio` by design |
| `iris`, `wipe` | portal | feather 0.08 of the diagonal; the wipe shows B left of the seam, as Reveal's video does |
| `luma` | luma | brightness-ordered reveal, softness 0.15 |

Curves: `linear ease ease-in ease-out snap hold-then-go`. Length clamps to [0.1, 10] s, fps to
≥ 1; `n_frames = round(seconds × fps)`, at least 2.

```
transitions.py pair BEFORE AFTER --out DIR [--seconds 1.0] [--fps 30] [--preset morph]
               [--color 0.7] [--warp 1.0] [--max-long 0] [--anchors "ax,ay,bx,by;…"] [--class A|B]
transitions.py check
```
Exit 0 on success, 2 with `FAILED: <message>` on stderr.

## 4. Not ported from the research artifact, and why (reopen only with a dated `DECISIONS.md` line)
- **The 12-module package, the separate venv and `setup-impossible.sh`.** This repo's single-file
  rule and operator surface (`AGENTS.md`) win. Same venv, no new dependency.
- **PyAV.** Needed only for PTS-exact clip decoding (research §6). Photo pairs need nothing beyond
  imageio-ffmpeg. Installing `av` beside `opencv-python-headless` on this Mac printed an
  Objective-C duplicate-class warning for `libavdevice` (cv2 ships 61.3, av ships 62.3) on
  2026-09-13. Decision pending as backlog T8, before slice TR4.
- **RoMa on MPS with a first-call weight download.** Two rulings forbid it as written: decision 9
  and decisions 24–27. Slice TR5 brings a dense matcher in behind a warmup, a manifest and a
  refuse-to-download gate, measured on the CPU first (backlog T11).
- **The generative stubs, budget planner, noise warp and frequency split.** Nothing measured on
  Apple Silicon yet, and unexercised optional code is a liability (`HANDOFF.md §5b`). Slice TR6
  starts with a measurement, not code.
- **`clips` and `sequence`.** Wait for the PyAV decision (slice TR4).

## 5. Harness: `transitions_harness.py`, 43 checks, about 8 s (as of 2026-09-14; own numbering)
Coverage by section. A: isolation both ways and the no-network import set (1–3). B: grammar —
frame count, monotone progress for every curve and warp amount, length clamp, unknown names fail
cleanly (4–7). C: warp — a translation field equals `warpAffine` within 0.5 levels, no fake holes,
t=0 is the identity, `to_u8` rounds (8–11). D: correspondence — class A routing with inliers, dense
field within 1.5 px of a known affine, class B routing with the INFO line, MLS identity and
translation, anchors honoured, forced class, mismatched canvases refused (12–18). E: color path —
midpoint pull; strength 0 and identical statistics are no-ops (19–20). F: render — byte-exact
endpoints, `edge_ratio` below 1.5 and no step above 0.12 for every preset, monotone approach to B,
determinism, no manufactured endpoint step (21–24). G: quality basket — the hidden-cut detector
fires on a cut and not on a dissolve; warping error separates a pan from noise (25–26). H: CLI and
the decoded mp4 — files, frame count, size, fps, endpoints within codec loss, no black frame,
report basket, monotone wipe seam, identical frames across two CLI runs, missing input exits 2,
length floor, `check` (27–36). I: identity fence (37–38). J: canvas policy — the finish ratio wins
without upscaling, `common` keeps the old rule, `max_long` caps, an unknown policy is refused (39–40).
K: class B coverage (defect T13) — a positive control shows the old whole-frame shape leaves 12 %
of the canvas without A and steps 56 levels at the exposed edge; `panzoom_field` keeps coverage
≥ 0.81 at every t while moving the frame up to 64 px, pans 2 % of the way to a far target and
100 % to a near one; end to end on two flat frames with one blob each, saliency finds the blob
within 5 px, coverage stays ≥ 0.86 and the mid frame's largest 12-px profile step is 4 levels (41–43).

Mutations applied: on 2026-09-13, making `to_u8` truncate turned checks 11, 20, 21 and 24 red
(32 of 36 at the time); on 2026-09-14, removing the pan clip in `panzoom_field` turned 42 and 43
red (coverage 0.00, a 56-level step). Gaps: the harness inputs are synthetic by rule; the real-pair tier lives in
`fixtures/` and the dated sheets under `.claude/claude-docs/benchmarks/` (first sheet 2026-09-13, ten
pairs); DNG and ARW have never been decoded from a real file; the owner's usability rating is pending.

## 6. Measurements (2026-09-13, M3 Pro, `.venv` Python 3.13.5, OpenCV 5.0.0)
| What | Result |
|---|---|
| Research artifact, its own harness, scratch venv with `av` | 34 of 34 in 4.5 s |
| Research artifact E1 bench, morph, 30 frames, s/frame at 720p / 1080p / 4K | 0.086 / 0.226 / 0.728 (Reveal's harness ran concurrently; upper bounds) |
| This port on a Reveal-aligned synthetic pair, 1200×900, 30 frames | morph 3.1 s, flow-dissolve 3.2 s, wipe 1.6 s; class A, 214 inliers, median displacement 0.19 px |
| Per-frame profile, morph, 1080p / 4K, before the color cache | total 0.160 / 0.689 s: color path 0.055 / 0.243, hole fill + mix + cast 0.049 / 0.213, two splats 0.040 / 0.159, two backward warps 0.017 / 0.071 |
| Correspondence once, 1080p / 4K | 0.36 / 1.51 s |
| Encode per frame, 1080p / 4K | 0.037 / 0.064 s |
| Color cache + in-place hole fill (frames byte-identical, hash equal) | 1080p morph frame 0.163 → 0.151 s |
| `REVEAL-BASELINE.sha256` in the artifact vs this repo | all nine files identical: the research targeted exactly this code |
| First real pairs, 12 owner fixtures, canvas ≤ 1920 px (`benchmarks/2026-09-13-real-pairs.md`) | class routing 11 of 12 as labelled (mismatch_7 shares its skyline and routes A by rule); `edge_ratio` ≤ 0.79 on the smooth presets; endpoints 0 / 0; morph 1 s renders in 4.7–13.4 s |
| Lowest certainty seen: mismatch_7 (same skyline, different skies) | mean certainty 0.053; the morph tears the clouds; a certainty floor for the DIS residual is proposed (TR2b) |
| Two iPhone HEIC files (6048×8064, ICC) | decode 1.9 s each; class A, 492 inliers, 63.7 px median displacement |
| Owner picks 2026-09-14 (`benchmarks/2026-09-13-real-pairs.md §Owner picks`) | 0 of 12 usable as-is; 3 pairs have a closest-to-intent pick (match_1 flow-dissolve 1 s, match_4 and match_5 morph 3 s), "very far from perfect"; E2 gate not met |
| Class B frame border (T13), seven mismatched fixtures at ≤ 1920 px, mid frame t = 0.5, 2026-09-14 | before: the moved frame leaves 9–52 % of the canvas without one endpoint (mismatch_1 B 18.6 %, mismatch_3 B 36 %, mismatch_4 A 27 %); after `panzoom_field`: 0 % holes, min coverage 0.86 on every pair; pan fractions A / B: mismatch_1 0.20 / 0.87, _2 0.15 / 0.16, _3 0.06 / 0.06, _4 0.79 / 0.19, _5 0.15 / 0.34, _6 0.23 / 0.57, _7 0.14 / 1.00 (salient centers 107–720 px apart); field 0.03–0.15 s per pair |
| Class A frames under the class B change | byte-identical: sha256 over all seven presets on the harness pair equal before and after |
| Re-run of the twelve fixtures, 2026-09-14 (`benchmarks/2026-09-14-real-pairs.md`) | 60 runs, all exit 0, endpoints 0 / 0, routing unchanged; class B `saliency-panzoom` on the six mismatched pairs with median displacement 46–122 px (was 232–889) and `edge_ratio` on morph 1 s 0.13–0.66 (mismatch_6 0.66, was 0.52; its flow-dissolve 1.04, was 0.72); the `finish` policy changed four canvases (match_5 → 1438×1920: 89 inliers, 84.6 px); morph 1 s renders in 1.5–11.7 s |
| RoMa vs the DIS field on match_2 / match_3 / match_5 (`scripts/research/`, 2026-09-14 late, timed alone; DECISIONS line of that time) | match 55.4 / 37.2 / 34.8 s per pair on the CPU; RoMa certainty mean 0.43 / 0.16 / 0.27 (DIS consistency 0.81 / 0.41 / 0.32); fields differ by 0.5 / 9.2 / 22.1 px median. Morph 1 s from each field, DIS → RoMa: warping error 0.0068 → 0.0068, 0.0038 → 0.0035, 0.0211 → 0.0162; `edge_ratio` 0.16 → 0.19, 0.13 → 0.09, 0.24 → 0.21. By eye: match_3's person stays coherent instead of smearing across the umbrella; match_5's boxes keep straight edges and stay in place; match_2 unchanged. Owner: timings "below 1-2 min per pair is not that much issue for now, lets achieve best quality" |
| RoMa clips, six class A pairs × four variants (2026-09-15; `benchmarks/2026-09-14-real-pairs.md §RoMa clips`) | 24 mp4s, endpoints 0 / 0; warping error DIS → RoMa on morph 1 s: match_1 0.0064 → 0.0070, match_2 0.0109 → 0.0121, match_3 0.0038 → 0.0037, match_4 0.0102 → 0.0080, match_5 0.0195 → 0.0176, mismatch_7 0.0120 → 0.0194; flow-dissolve `edge_ratio` rises on every pair (0.23 → 0.64 on match_1), cause not established; render 6.8–12.9 s per 30 frames |
| RoMa on match_1 / match_4 / mismatch_7 (2026-09-15, timed alone) | 46.4 / 46.4 / 46.1 s; certainty mean 0.13 / 0.55 / 0.03 (DIS 0.48 / 0.65 / 0.05); fields differ by 5.4 / 0.57 / 297.9 px median; RoMa forward-backward error 0.66 / 0.17 / 227.7 px. In RoMa's low-certainty regions the displacement relative to the global motion is roma / dis: match_1 9.3 / 11.9, match_3 15.7 / 32.2, match_5 24.3 / 46.4, mismatch_7 350 / 243 px |
| RoMa outdoor (romatch 0.1.2, torch 2.14, CPU, 12 threads) on match_4 at 1536×1920, scratch venv, 2026-09-14, concurrent with the sweep | weights 1,217,586,395 + 445,647,516 bytes (DINOv2 ViT-L/14 Apache-2.0, RoMa MIT), load 80 s incl. download; match 40.6–44.8 s per pair (4 runs) against 0.74 s for homography+DIS; the input is resized to 560×560 coarse and 864×864 for the field, aspect ignored; certainty mean 0.553 (62 % of pixels above 0.5); median displacement 9.9 px (DIS 15.1); median difference to the DIS field 0.57 px over the canvas, 0.20 px where both are confident (52 % of pixels) |
| TR14 probe, nine variants on match_3 / match_4 / match_5 / mismatch_7, morph 1 s (+ 3 s on the box pairs), 2026-09-15 (`benchmarks/2026-09-15-real-pairs.md`, `§10`) | 66 clips, endpoints 0 / 0. Median displacement inside the changed mask, match_4: `dis` 20.9 px, `roma` 3.1, `roma-x-cert` 1.0, `hold` 5.2 (= the camera motion); match_5: 79.7 / 74.3 / 2.9 / 72.8 (camera 72.8); mismatch_7: 312 / 489 / 0.4 / 330 (camera 330). Box-edge straightness (p90 of the harness O tracker), match_4 photo 2.54 px: `dis` 6.3, `roma` 2.4, `hold` 2.54, `hold-dis` 4.4, `luma` 3.96, `edge-grow` 3.49, `melt` 5.31, `melt-soft` 2.42. Warping error on mismatch_7: `dis` 0.012, `roma` 0.0194, `hold` 0.0081. Effects add 0–1 s per 30 frames |
| TR6 first measurement, SD 1.5 inpainting (diffusers, torch 2.14.0, MPS fp16) as a masked SDEdit pass on match_4's `hold` mid frame, 512×640, strength 0.5, 20 scheduled steps (10 run), 2026-09-15 (`§10.7`) | 1.43–1.62 s per step, 14.3–16.2 s per image, model load 49.8 s including the 2.0 GB download, peak RSS 2.41 GB; the same seed reproduces byte for byte (max abs diff 0), another seed differs by 13.0 levels mean; output: a coherent painted panel inside the mask, the wall untouched, no temporal coherence across frames |

## 7. Risks and open questions, ranked
1. **Object-level correspondence is the top gap (owner review, 2026-09-13).** Three matched pairs
   are "promising" but miss accuracy and any transformation of parts; a person who moved reads as a
   slide (match_2); two poses that share no flow crossfade into each other (match_3); every
   unrelated pair is "a naive cross-dissolve". The engine matches pixels, not themes. Order of
   remedies: a learned dense matcher (TR5), object and part correspondence with anchors (TR9), a
   generative backend for the intermediate transformations (TR6). Verbatim review and per-pair
   mechanism: `benchmarks/2026-09-13-real-pairs.md`. Measured 2026-09-14 (§6): RoMa's field fixes
   match_3 (the person no longer smears) and match_5 (the boxes stay put) and leaves match_2 as it
   is. Why (measured 2026-09-15, correcting the first reading): in the regions RoMa marks uncertain
   (certainty < 0.3; 78 % of match_3, 66 % of match_5) its displacement departs from the pair's
   global motion by half as much as DIS (15.7 vs 32.2 px and 24.3 vs 46.4 px median), so changed
   content is moved less. The certainty itself only weights splat collisions and does not hold a
   region in place: on mismatch_7 (certainty 0.03) RoMa's field is 350 px off the global motion and
   its clip is expected to be worse than DIS. Scaling the displacement by the certainty (TR2d) is
   the designed answer for that case and is measured next. Owner verdicts on the 24 RoMa clips
   (2026-09-15, `benchmarks/2026-09-14-real-pairs.md §Owner verdicts`): RoMa better on match_3
   only, DIS better on match_4, match_5 and mismatch_7 — not adopted as a drop-in. The owner
   rejects both fields' handling of the paint on the box: DIS for "textures come from the right",
   RoMa for "fades out and fades in, no transformations"; the box holding its position (RoMa) and
   RoMa's background motion are liked (owner, 2026-09-15: "i liked how the box itself holds
   position"). Timing for experiments (owner, 2026-09-15): 3–5 min per pair is fine for tests, no
   hard upper limit within reason. The next
   slice is TR14, a design pass on what the changed region should do (TR2d floor, a designed
   effect inside the changed mask over RoMa's background field, or the generative tier); the
   speed gate stays lifted ("below 1-2 min per pair is not that much issue for now").
   Design written 2026-09-15 (`§10`): TR2d as written detaches the object from the camera motion
   and is rejected; `hold` (camera motion + residual × certainty) is the floor and fixes
   mismatch_7's tearing; three deterministic effects and a weight-free `hold-dis` are on the
   review page for the owner's picks; the generative tier is researched and first-measured (§10.7).
2. **Class B showed the warped frame's border** (owner, every mismatched pair: "next frame square
   borders … especially ugly"). Mechanism (measured 2026-09-14): the similarity moved the whole
   frame, and where the moved frame no longer covered the canvas the coverage-aware mix switched
   to the other endpoint, a rectangle of pure B (or A) inside the picture. Fixed the same day
   (`§2.3`, harness K): each frame keeps covering the canvas by construction. Cost: the pan is
   capped by the 10 % zoom's slack, so on far-apart salient blobs (mismatch_3: 720 px) the motion
   is mostly the zoom and the two blobs no longer meet (mismatch_4's two suns stay 64 px apart at
   mid-transition). `classb_zoom` is the one knob; the owner's picks on the re-rendered mismatch
   strips decide whether it moves. Class B stays crude by design: the object and theme
   correspondence the owner wants is slice TR9; the anchors path (MLS) still moves the whole frame.
2c. **Directional texture inflow and subject shift on the box pairs** (match_4, match_5). Inside a
   repainted region no true correspondence exists; the DIS residual still chooses a direction and
   the splat follows it. Slice TR2d scales displacement by certainty so such regions dissolve in
   place; Reveal's §5a warning (spatially varying fields bend straight edges) is the metric to
   watch, on the box edges themselves.
2b. **Class A with near-zero certainty tears.** mismatch_7 shares a skyline, so it routes to class A
   correctly, but its skies differ and the DIS residual chases cloud content (mean certainty 0.053).
   Reveal met the same mechanism as field defect #1 and answered with a low-order field. Proposed
   TR2b: below a certainty floor, drop the DIS residual and morph on the homography alone, with a
   visible INFO line; the floor is calibrated on the sheet (match pairs 0.33–0.81, mismatch_7 0.05).
3. **`edge_ratio` is sensitive to sub-level bias.** Smooth presets measure 0.3–0.8 on the harness
   pair; `snap-morph` measures 1.44, and 1.55 under the truncation mutation. The rounding contract
   exists for this reason.
4. **Speed.** 4K costs about 0.69 s per frame on the CPU, so a 10 s 4K transition takes about
   3.5 min. Slice TR7 (rank 1) targets 0.10 s at 1080p and 0.45 s at 4K with the profile above.
5. **No seam from Reveal.** `export_video --style morph` cannot reach this tool; adding a one-way
   lazy import to `reveal.py` is a Reveal-side change (backlog T10, slice TR3).

## 8. Research artifact coverage (every module and experiment of `impossible-0.1.0`, as of 2026-09-13)
Owner order (2026-09-13): "make sure we account ( maybe you already did ) for any useful content in
`…/transitions-research/impossible-0.1.0/impossible` artifact prototype". Status values: **ported**
(in `transitions.py`, TR1), **slice** (planned; `EXPLORATION_PLAN.md §TR`), **not ported by ruling**
(`§4` above), **research first** (measure before code).

| Artifact item | Status | Where |
|---|---|---|
| `grammar.py` TransitionSpec, curves, presets `morph dissolve flow-dissolve snap-morph iris luma`, clamp, `progress` | ported | Configuration section; `wipe` added |
| `grammar.py` `dream` preset, `dreaminess`, `gen_window`, `seed`, `budget_minutes`; preset `auto` | slice TR6 | generative fields return with the first measured backend |
| `grammar.py` MediaItem, SequenceSpec, the sequence JSON (`items`, `transitions`, `output`) | slice TR4 | clips and sequences |
| `render.py` prepare / render_frames, endpoint pin | ported | Render section, streamed |
| `warp.py` forward_splat, backward_warp, fill_holes, morph_frame, portal_mask | ported | Warp section |
| `correspond.py` sparse_homography, homography-guided DIS, consistency weight, salient_box, similarity_from_boxes, mls_affine, invert_disp, class routing, anchors | ported | Correspondence section |
| `correspond.py` `_roma_displacements`, `roma_available` (RoMa on MPS, download on first call) | slice TR5, not ported by ruling as written | warmup + manifest first; CPU measured first |
| `color.py` Lab statistics path, `luma_mask` | ported | Color section; Lab cached per transition |
| `media.py` load_rgb, cover, common_canvas | ported | Decode and canvas section |
| `media.py` `is_video`, VIDEO extensions | slice TR4 | |
| `video.py` probe, frames_between (PTS-exact), frame_at, `context` (frames around a cut), Writer (PyAV), count_frames | slice TR4 | PyAV decision T8 first |
| `quality.py` warping_error, flicker with edge_ratio, endpoint_fidelity, assess, thumb_strip | ported | Quality section; proxy at 480 px |
| `quality.py` `composite` ranking score | slice TR6 (E18 candidate sweep) | ranking only, never a verdict |
| `generative.py` Enricher contract, NullEnricher, warp_noise_along_flow, frequency_split_blend, COST table, RES_LADDER, plan_generation, LTX-2 / Wan / DreamMover stubs | research first, slice TR6 | E14–E17 measurements come before code |
| `cli.py` `pair`, `--anchors`, `--class`, `--max-long`, `--color`, `--warp`; `probe` | ported | `pair`, `check` |
| `cli.py` `clips` (`--cut-a --cut-b --head-from --tail-to`), `sequence` | slice TR4 | |
| `cli.py` `bench` (E1 synthetic timing) | replaced | `scripts/bench_transitions.py` runs the fixture catalogue (TR2); the profile lives in §6 |
| `cli.py` `--dreaminess --backend --seed --budget-min` | slice TR6 | |
| `impossible_harness.py` checks 1–16 | ported and extended | transitions harness 1–24 |
| `impossible_harness.py` checks 17–22 (generative contracts) | slice TR6 | |
| `impossible_harness.py` checks 23–29 (video I/O, clips, sequence) | slice TR4 | |
| `RESEARCH-PLAN` E1 bench on the Mac | done 2026-09-13 | §6 |
| E2 real pairs | slice TR2, started 2026-09-13 | `fixtures/`, `scripts/bench_transitions.py` |
| E3 real clips, cuts, stitch; E8 stream-copy stitch | slice TR4 | |
| E4 RoMa | slice TR5 | |
| E5 splat quality vs the softmax-splatting reference; E6 MPS splat | E5 → slice TR8; E6 not pursued | CPU meets the E1 gates; TR7 covers speed |
| E7 motion carry-over across a cut | slice TR4 follow-up (TR4b) | needs clips |
| E9 SAM 2 + DINOv2 class B semantics; E10 anchor editor page | slice TR9 | class B is crude by design until then |
| E11 depth camera-move path (Depth Anything V2, 2.5D dolly) | slice TR10 | |
| E12 OKLab / optimal-transport color, 10-bit and HLG round trip | slice TR11 | 10-bit needs the video I/O of TR4 |
| E13 SAM-mask portals and luma softness control | slice TR9 | |
| E14–E17 generative backends and steering; E18 candidate sweep UI | slice TR6 | licenses: LTX-2 Community, Wan 2.2 Apache-2.0, DreamMover SD 1.5 |
| Phase 4 product surface: sequence editor page, audio crossfade, presets as JSON | slice TR12 | after TR4 |
| `REVEAL-BASELINE.sha256` isolation idea | ported as checks 1–3 and `git diff` on the roster files | |
| `setup-impossible.sh`, `requirements-impossible.txt`, `.venv-impossible` | not ported by ruling | shared venv; PyAV is T8 |

## 9. Runbook
```
.venv/bin/python transitions.py check
.venv/bin/python transitions.py pair out/before.jpg out/after_aligned.jpg --out out/tr --seconds 1.5 --preset flow-dissolve
open out/tr/strip.jpg; cat out/tr/report.json
.venv/bin/python transitions_harness.py            # Gate 1b
```

## 10. TR14 design: what the changed region does between the endpoints (2026-09-15)

Design pass ordered by the handover of 2026-09-15 after the owner's verdicts on the RoMa clips.
Probe: `scripts/research/tr14_variants.py` (nine variants, four pairs, morph 1 s and 3 s; page
`benchmarks/runs/2026-09-15/tr14/index.html`, numbers in `benchmarks/2026-09-15-real-pairs.md`).
No tool code changed in this pass; the owner's picks on the page decide what is built.

### 10.1 The brief (the owner's words, 2026-09-14 and 2026-09-15)
1. The changed object keeps its place relative to its surroundings: "i liked how the box itself
   holds position" (match_4); "i wish the boxes … didn't shift at all" (match_5).
2. Its content transforms; neither "new image textures come from the right on the box" (DIS,
   match_4) nor "prev image on it simply fades out and new one fades in, no transformations"
   (RoMa, match_4 and match_5).
3. No tearing where the field is uncertain: "cheap 3d cloth effect with lots of artifacts"
   (RoMa, mismatch_7); the clouds tear with DIS (2026-09-13).
4. The background keeps a natural motion: "roma does better transition for background here (like
   wall and floor, more natural movement)" (match_4).
5. "fade in place" stays available as a named mode ("may be useful as transition mode in our
   reveal app").
6. Changes "come a bit more subtly at different parts of the image" (match_5).
A person who re-posed (match_1, match_3: "as if person grows … especially person's edges") is
slice TR9; this pass only checks that the candidates do not make match_3 worse.

### 10.2 Why neither field meets item 2, and why TR2d as written breaks item 1
- **DIS** has no true correspondence inside a repainted region but still matches texture, and its
  forward-backward consistency is confident on that wrong match (the DIS weight is high inside the
  box on match_4, `scratchpad look/match_4_look.jpg`). The splat follows it: the median displacement
  inside match_4's changed mask is 20.9 px against 5.2 px of camera motion, and the box edge bends
  (straightness 6.3 px at t = ¼..¾ against 2.5 px on the photo itself).
- **RoMa** marks the repainted region uncertain and moves it little (3.1 px inside match_4's mask),
  so the box holds; the mix stays the uniform crossfade, which is the fade the owner rejects.
- **TR2d as written** (displacement × certainty, `roma-x-cert`): an uncertain region stops following
  the camera. On match_5 the camera moves the boxes 70 px between the photos; `roma-x-cert` moves
  them 2.9 px, so they detach from the wall and pavement and land 70 px off at the end. The basket
  cannot see this (its warping error falls, 0.0176 → 0.0119, because less moves). Rejected.
- **TR2d in residual form** (`hold`): camera motion + (field − camera motion) × certainty. The camera
  motion stays everywhere and only the content-chasing residual is dropped where the field is
  uncertain. Inside the mask the displacement equals the camera motion (match_4 5.2 px, match_5
  72.8 px) and the box edge stays as straight as on the photo (match_4 2.54 px, A 2.54). On
  mismatch_7 (certainty 0.03) this is the homography-only morph slice TR2b proposed, per pixel.
- **`hold-dis`**: the same construction from the tool's own DIS field, gated by the photometric
  changed mask instead of a certainty (the DIS weight cannot gate it: it is confident on the
  wrong match). Needs no weights. Measured (morph 3 s): match_4 in-mask displacement 6.6 px (hold 5.2), straightness 4.42 px (hold 2.54, the photo 2.54), `edge_ratio` 0.136 (hold 0.027); match_5 71.9 px, 7.42 px (hold 7.03), 0.063 (hold 0.048). The 8 px feather of the gate lets the DIS residual act in the dilation band around the box edge, where DIS is confidently wrong; widening the gate past the detector's 21 px dilation is the fix to measure before `hold-dis` is preferred.

### 10.3 The mask
Reveal's changed-region detector (`reveal.py changed_region_mask`) on the homography-aligned pair:
per-channel exposure-normalized absolute difference, 9 px blur, Otsu threshold (floor 40 of 255),
close 7 / open 5, hole fill, dilation 21 px. Fractions of the canvas: match_4 0.276, match_5 0.49,
match_3 0.189, mismatch_7 0.432 (the sky). Why not RoMa's certainty as the mask: certainty says where the
matcher cannot see, not where the content changed. On match_3 78 % of the frame is below 0.3 and
most of it is the unchanged sky; on match_4 the certainty mask includes wall patches. The two
gates do different jobs: a certainty (or the mask, in `hold-dis`) gates the residual motion, the
photometric mask gates the effect. Cost of carrying the detector into `transitions.py`: about 35
lines re-implemented (invariant 1, no import from `reveal`), plus a section-D harness check on a
synthetic changed patch.

### 10.4 The effects (deterministic, inside the mask, over the `hold` field)
| Effect | Mechanism | What it reads as (mid frames, agent's eye) |
|---|---|---|
| `luma` | the tool's `luma_mask` order (A's brightness, bright first), rank-normalized inside the mask, front width 0.15; the mix outside the mask is the ordinary crossfade; the mask is feathered 8 px | the old graffiti's dark strokes stay while the mural fills in behind them; the strokes go last |
| `edge-grow` | order = distance from B's Canny edges (60/160), rank-normalized; lines first, fills after | the mural is drawn in outline over the old box, then painted |
| `melt` | the composited frame is re-sampled through a divergence-free noise field (Gaussian ψ at σ = 4 % of the short edge, curl of ψ), amplitude 1.2 % of the long edge × sin(πu), feathered inside the mask; zero at both endpoints | the paint swirls and re-forms; subtle at 23 px |
| generative (TR6) | the `hold` frames are the skeleton; a masked first+last-frame or inpainting model repaints only the mask | not measured; §10.7 |
Defect found in `melt`: with a 32 px feather the swirl reaches the object's edge, because the mask
is dilated 21 px past it (match_4 straightness 2.54 → 5.31 px). Fixed as `melt-soft`: the ramp starts 24 px inside the mask boundary and is fully on 64 px further in; match_4 straightness 2.42 px (the photo 2.54), `edge_ratio` 0.28 (the swirl's own motion; `melt` 0.41, `hold` 0.23). The rule for the implementation: any displacement effect inside the mask is zero across the detector's dilation band.

### 10.5 Probe numbers
See `benchmarks/2026-09-15-real-pairs.md` (the same table as the page). The straightness column
is the 90th percentile of the tracked edge's residual from a fitted quadratic (Reveal harness O's
tracker in a ±10 px window that follows the camera motion), measured on the photos' own edge
first: match_4 A 2.54 / B 3.89 px, match_5 A 6.91 / B 7.32 px (a busier edge; the metric
separates little there), match_3 A 6.0 / B 7.21 px on the railing (not a box; reported, not
interpreted), mismatch_7 no vertical edge inside the sky mask (not measurable).

### 10.6 Recommendation and the shape it takes in `transitions.py`
Build the floor now; the page decides the effect. The floor is `hold`: the changed object
follows the camera motion and nothing else. It meets items 1, 3 and 5 on every measured pair and
is the only variant that is right on mismatch_7 (warping error 0.0081 against DIS 0.012 and RoMa
0.0194; no cloth, no tear; a moved-frame rectangle remains, see §10.9). Which effect goes on top
is the owner's pick; the agent's eye ranks `edge-grow` first on the box pairs (the mural is
drawn in outline before it is painted: a transformation with no direction), `luma` second,
`melt-soft` third (subtle at 23 px). The generative tier stays behind those as a fourth value
once the video route is measured (§10.7).
- One option on the spec, `changed`, with values `flow` (today's behaviour, the default),
  `hold`, `luma`, `edge-grow`, `melt`; CLI `--changed`; a preset may carry it. `hold` is the named
  "fade in place" mode of item 5. `report.json` gains `changed` and `changed_frac` (the mask's
  fraction of the canvas); the INFO line names the mask fraction when `changed != flow`.
- Field: `hold` in the DIS shape unless the owner's picks say RoMa's background motion is worth
  35–55 s and 1.7 GB per pair; RoMa then re-enters through TR5 as the field behind the same option.
- Timing: 3 s on the box pairs (the owner's 2026-09-14 picks were morph 3 s there).
- Harness checks to add with the implementation, each with its red-making mutation:
  1. `changed=flow` leaves every preset byte-identical on the harness pair (sha256 before/after;
     mutation: default `hold`).
  2. `hold` on `affine_pair()` with its changed patch: the displacement inside the patch equals the
     ground-truth affine within 1 px while `flow` departs from it (positive control; mutation: gate
     the residual with the DIS weight instead of the mask).
  3. An effect changes pixels only inside the feathered mask: outside, the frame equals the `hold`
     frame within 1 level; inside, the revealed fraction at u = 0.5 lies in [0.3, 0.7] (mutation:
     apply the order map to the whole frame).
  4. `melt` keeps a straight edge at the mask boundary straight (harness O's tracker on the
     synthetic box edge; mutation: no feather).
  5. Endpoints byte-exact and two runs identical (checks 21, 23, 33 already cover; the effects
     must not add a random source: the curl field is seeded).
- Reversibility: `[revert: option value; default flow untouched]`; the experimental lane of
  `AGENTS.md` (a new option value, the default path byte-identical).

### 10.7 The generative tier
Research first (`scratchpad/tr6_backends.md`, primary sources only, 2026-09-15), then one
measurement. Facts that decide the shape:
- Only one candidate takes a start frame and an end frame and renders the transition natively on
  this Mac: LTX-2.3 through the third-party MLX port `dgrauet/ltx-2-mlx` (port MIT; weights under
  the LTX-2 Community License, `license:other` on Hugging Face, not gated). Its `keyframe`
  command needs `transformer-dev` + the distilled LoRA + connector + VAEs + audio VAE and the
  Gemma-3-12B 4-bit text encoder: about 30 GB (int4 pack) + 8 GB. No Apple-hardware speed is
  published. The port runs `snapshot_download` on the whole pack (60–88 GB), so the subset must
  be fetched by hand.
- Wan 2.2 does not document first+last-frame video; Wan 2.1 FLF2V-14B does and weighs 82 GB
  against 36 GB of unified memory: out for this machine.
- The image-morphing models are licensed or built against this project: DiffMorpher (S-Lab 1.0,
  non-commercial; SD 2.1-base, gated download), Framer (BSD, academic only), DreamMover (no
  license file; CUDA-oriented install). Generative Inbetweening needs SVD-XT (19 GB, community
  license) and was tested on A100/A40 only.
- The cheapest generative route for a MASKED region is SD 1.5 inpainting through diffusers on
  MPS fp16 (the only reduced precision diffusers documents for MPS); the live repo is
  `stable-diffusion-v1-5/stable-diffusion-inpainting` (creativeml-openrail-m, not gated, 2.0 GB).
- RIFE (MIT) and FILM (Apache-2.0) are deterministic learned inbetweeners; neither repo mentions
  Apple Silicon. They are a TR9 (people) candidate, not a paint transformation.
Measured (this Mac, scratch venv, torch 2.14.0 on MPS fp16, `scratchpad/sd/sd_probe.py`):
SD 1.5 inpainting as a masked SDEdit pass on match_4's `hold` mid frame at 512×640, prompt
"a painted mural on a street utility box, photo", strength 0.5, 20 scheduled steps (10 run),
guidance 6: 1.43–1.62 s per step, 14.3–16.2 s per image, model load 49.8 s including the
download, peak RSS 2.41 GB; the same seed reproduces byte for byte (max abs diff 0), another
seed differs by 13.0 levels mean. The result is a coherent painted panel inside the mask (a
figure, flowers), the wall untouched: an intermediate that is neither photo, which is the
"dream" the research plan describes. What it does not give: temporal coherence (each frame is an
independent sample; a 30-frame clip at 15 s per frame is 7.5 min and would flicker), so the
video route (LTX-2 keyframe, or warped-noise steering, research E17) is the next measurement.
LTX-2.3 int4 pack subset (transformer-dev, distilled LoRA 1.1, connector, VAEs, upscalers, audio VAE, vocoder: 29.5 GB) and Gemma-3-12B 4-bit (8.1 GB) fetched into the session scratchpad on 2026-09-15; the first `keyframe` run (match_4 A → B, 384×512, 25 frames at 25 fps, seed 0, `--low-ram`, run twice) is recorded in the handover and, when it finishes, as a §6 row.
Gate for adopting any of it (unchanged from the plan): a fixed seed reproduces, s/frame stated
on this Mac, the license recorded, the weights behind warmup + manifest + refuse-to-download.

### 10.9 Found on the way, not TR14's
`hold` on mismatch_7 exposes the start frame's moved border as a rectangle at mid-transition:
the pair's homography is a 250 px zoom and shift, and where the moved start frame no longer
covers the canvas the coverage-aware mix in `morph_frame` switches to the finish frame (the
class A twin of defect T13; DIS hides it by tearing the sky). It shows on any class A pair with
a large camera motion (match_5: a 35 px band at one edge at mid-frame). A canvas rule answers it
(TR13's shared-area mode), or a reflected fill without the mix switch for content like sky.
Recorded as backlog T14.

### 10.8 Open questions for the owner
1. On the page: which variant per pair is closest, and is any acceptable as-is? If none, what
   should the paint do — the note field.
2. `hold` (RoMa) against `hold-dis` (DIS + mask): is the background motion RoMa gives on match_4
   worth the dense matcher, or is the weight-free `hold-dis` enough?
3. TR6: which backend may be fetched first (license and size in §10.7).
