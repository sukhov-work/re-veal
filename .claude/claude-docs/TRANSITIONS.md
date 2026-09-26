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
2. **Offline, local, CPU.** No import that can reach the network or load model weights at module
   level; torch and transformers are imported lazily inside the depth section only (check 3, amended
   2026-09-23). The one model, Depth Anything V2 Small behind `--camera model` (2026-09-23, §2.3),
   lives in `models/depth/` behind `transitions.py warmup` + `models/DEPTH_MANIFEST.json` +
   refuse-to-download, the shape of Reveal's decisions 24–27 (checks 48–51); a run never downloads.
   Reveal's decision 9 (no MPS) holds for the deterministic tier and for the depth model (CPU and MPS
   disparities agree to 2e-5, so no device flag exists); the device for model stages is decided per
   slice by measurement (`HANDOFF.md §11`).
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
     Least Squares (affine; Schaefer 2006) with the splat-and-inpaint inverse. Its frame edge
     showed on the 2026-09-26 anchored renders (backlog T16); since 2026-09-26 `--anchor-falloff F`
     (default 0.45; 0 = off) multiplies the anchored field by `border_weight`, a
     smoothstep from 0 at the canvas border to 1 at F × the short edge inward, so the border
     stays put and the frame keeps covering the canvas (check 54: a 120-px whole-frame anchor
     translation leaves 9.1 % of the mid frame uncovered at 0, 0.00 % at 0.2; the field at the
     centre is unchanged). Method `mls-anchors+falloff`; in class A the same weight applies to the
     anchor correction (`…+anchors+falloff`). Default 0.45 since 2026-09-26 (late; owner picks: the
     frame edge is "hard ugly" on every pair where it shows); `--anchor-falloff 0` gives the
     2026-09-13 field. On the real pairs (2026-09-26,
     `benchmarks/runs/2026-09-26/anchors/contact_falloff_0_02_045.jpg`) a band of 0.2 tears the
     picture where the anchored field is large (mismatch_2's three-anchor rotation, mismatch_1's
     sky): the weighted field's gradient compresses content; at 0.45 mismatch_1 renders with no
     frame edge and no tearing, mismatch_2 stays a soft blend with striping in the trunk. Use
     0.4–0.5 on real pairs; the fold itself needs a similarity or rigid MLS (not built). Certainty is 0.5 everywhere under `flat` because nothing
     photometric supports it. In class A, anchors are blended over the dense field with weight 0.7.
   - **Camera move** (`--camera flat|ramp|model`, `--zoom`; TR10, built 2026-09-23). `ramp` scales
     the pan-and-zoom field by `1 − g/2 + g·d` with `g = 1` and `d` a top-to-bottom disparity ramp
     (0 far at the top row, 1 near at the bottom), so the bottom rows move 1.5× and the top rows
     0.5× (parallax), and the splat importance becomes `0.2 + 0.8·d` so near content wins the
     collisions. `model` puts Depth Anything V2 Small's relative inverse depth in place of the
     ramp: the canvas image is handed to the model at ≤ 1024 px on the long edge, the model's own
     DPT preprocessing (short side 518, sides a multiple of 14, bicubic, ImageNet statistics) is
     done with cv2 from the model card's `preprocessor_config.json`, and the raw output is clipped
     to its 2nd–98th percentile → 0..1 at the canvas size. `flat` is the field above, byte for
     byte (check 44; the 14 preset × class frame hashes were equal before and after the build).
     Every factor is positive, so the coverage guarantee is kept (check 46). `--zoom` sets the
     zoom fraction (default 0.10 = `classb_zoom`, clamped to [0.02, 0.5]; the owner liked 0.25).
     Method becomes `saliency-panzoom+ramp` / `+model`; `report.json` carries `camera`, `zoom`
     and, under a camera move, `disparity_mean [A, B]`; `mean_certainty` is then the mean depth
     importance, not 0.5. On a class A pair or with anchors a camera other than `flat` has no
     effect and says so on the log (check 44).
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
   Pixel scales depend on the scene, so a pair is compared against itself. Since 2026-09-26 the
   basket also carries `goal` (`goal_numbers`, §11): `feat_floor` (the minimum over the interior
   frames of SIFT matches to A over A's count plus matches to B over B's count — details of A or
   B must survive), `laplace_floor` and `contrast_floor` (the minimum ratio of the frame's
   Laplacian variance, and of its median 24-px patch standard deviation, to the endpoints'
   interpolated value — sharpness and local contrast kept), `dissolve_fit` (the mean R² of the fit
   frame(t+1) − frame(t) ≈ β·(B − A): the share of the change a plain crossfade explains; a
   dissolve scores near 1) and `motion_share` (the mean share of the frame change that DIS
   motion explains; a crossfade scores near 0). The first block screens defects; `goal` grades
   the transition against the owner's verdicts (calibration in the retrospective §5). The
   numbers cost about 1 s per 30 proxy frames and do not touch the frames (hashes equal).

## 3. Grammar and CLI
| Preset | style | Notes |
|---|---|---|
| `morph` (default) | morph | eased warp, eased dissolve |
| `dissolve` | dissolve | warp amount 0 |
| `flow-dissolve` | warp-dissolve | warp 0.6, dissolve delayed by 0.1 |
| `snap-morph` | morph | hold-then-go warp, ease-in mix; inflates `edge_ratio` by design |
| `iris`, `wipe` | portal | feather 0.08 of the diagonal; the wipe shows B left of the seam, as Reveal's video does |
| `luma` | luma | brightness-ordered reveal, softness 0.15 |

Camera (class B only, 2026-09-23): `flat` (default) · `ramp` (weight-free, bottom rows near) ·
`model` (Depth Anything V2 Small; needs `transitions.py warmup` once). `--zoom` 0.02–0.5, default 0.10.

Curves: `linear ease ease-in ease-out snap hold-then-go`. Length clamps to [0.1, 10] s, fps to
≥ 1; `n_frames = round(seconds × fps)`, at least 2.

```
transitions.py pair BEFORE AFTER --out DIR [--seconds 1.0] [--fps 30] [--preset morph]
               [--color 0.7] [--warp 1.0] [--max-long 0] [--anchors "ax,ay,bx,by;…"] [--class A|B]
transitions.py pair … [--camera flat|ramp|model] [--zoom 0.10] [--anchor-falloff 0.45]
transitions.py check                  # incl. the "depth model" row
transitions.py warmup                 # the only command that downloads (2026-09-23)
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

## 5. Harness: `transitions_harness.py`, 54 checks, about 10 s (as of 2026-09-26; own numbering)
Coverage by section. A: isolation both ways and the no-network import set at module level, with
torch / transformers / huggingface_hub allowed only inside the four named depth functions (1–3). B: grammar —
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
L: the camera move (2026-09-23) — `--camera model` on a class A pair renders the flat bytes, loads
no model and says so; class B `flat` at the default zoom equals the 2026-09-14 field byte for byte
(44); `ramp` at zoom 0.25 moves the bottom fifth 127 px against 52 px at the top (2.44×; flat 1.03×)
and the near rows carry weight 1.0 against 0.2 (45); holes 0.00 % at the mid frame, edge step 4
levels, coverage ≥ 0.49, and a gain of 3 (top factor −0.5) opens 2.2 % holes (46); the CLI clamps
`--zoom 0.9` to 0.5 and reports camera / zoom, an unknown camera is refused (47); the model files
live in `models/depth/` with a verified manifest (5 files, 99 MB, 4 links) and are checksum-intact
(48); with every socket patched to raise, the model cold-loads from disk and reads the self-test
floor (0.866) nearer than the sky (0.0), two runs byte-identical, 0.9 s for load + one 640×400
image (49); `model` and `ramp` agree in sign on the self-test scene forced to class B (2.42×) (50);
with the manifest removed, `--camera model` refuses before touching the model or the network and
names warmup (51). Checks 48–51 print a loud skip line when torch or transformers are absent.
Section M (52–53, 2026-09-26), the goal numbers: a plain crossfade of two unrelated harness
scenes scores `dissolve_fit` 0.97 and the aligned morph of `affine_pair()` 0.23 (52; mutation:
feed the crossfade's frames as the morph → red); the aligned morph keeps `feat_floor` 0.97 while a
clip whose interior is a scene from neither photo reads 0.07 (53; mutation: interior = A → 1.13,
red); `report.json` carries the five goal keys. Both mutations were applied on 2026-09-26 and
turned exactly the two checks red. `laplace_floor` and `contrast_floor` are NOT pinned on the
harness textures: there the forward splat's resampling blurs the discs more than a blend of two
unrelated textures does (aligned morph 0.45 against the crossfade's 0.85), the opposite of the
real clips (retrospective §5); the real-clip calibration is their reference.
Section N (54, 2026-09-26), the anchor border falloff: with the default 0 the anchored field is
byte-identical to the 2026-09-13 MLS field; at 0.2 it is 0 on the four border lines, equal to the
plain field at the centre, and the mid-frame hole fraction of a 120-px whole-frame anchor
translation falls from 9.1 % to 0.00 % (mutation: a constant weight → holes stay, red; paid
2026-09-26).

Mutations applied: on 2026-09-13, making `to_u8` truncate turned checks 11, 20, 21 and 24 red
(32 of 36 at the time); on 2026-09-14, removing the pan clip in `panzoom_field` turned 42 and 43
red (coverage 0.00, a 56-level step); on 2026-09-23 check 46 applies its own mutation every run
(`depth_gain` 3 opens 2.2 % holes) and the lazy `import torch` inside the depth section turned the
old check 3 red (it walked every import) before the amendment. Gaps: the harness inputs are synthetic by rule; the real-pair tier lives in
`fixtures/` and the dated sheets under `.claude/claude-docs/benchmarks/` (first sheet 2026-09-13, ten
pairs); DNG and ARW have never been decoded from a real file; the owner's usability rating was 0 of 12 on every review round from 2026-09-14 to 2026-09-25 (§11 and the retrospective of 2026-09-26 take it from there).

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
| TR6, LTX-2.3 int4 keyframe through the `dgrauet/ltx-2-mlx` port (MLX, dev transformer + CFG 3.0, 1.1 distilled LoRA for stage 2), match_4 A → B at 384×512, seed 0, 2026-09-15 (`§10.7`) | 25 frames 335.7 s wall, peak RSS 9.8 GB (stage 1: 20 guided steps at 12.9–13.3 s; stage 2: 3 steps; decode 7.8 s); 49 frames 436.1 s, 13.0 GB (stage 1 at 17.6 s per step); the same seed byte-identical (one md5 for the two 25-frame mp4s); `--low-ram` costs 16–18 s per step and needs the pre-fused distilled transformer for stage 2. Both clips are a cut (the finish photo takes over at frame 14 of 25 and 18 of 49; adjacent step 34 levels = the A–B gap); endpoints re-encoded (MAD 21 / 16 levels) |
| TR6, LTX-2.3 int4 keyframe levers, match_4 A → B, 49 frames at 384×512, seed 0, 2026-09-15 late (`§10.7`; clips in `benchmarks/runs/2026-09-15/ltx/`) | motion prompt alone ("time-lapse: a street artist paints over the graffiti …"): still a cut, now at frame 7 (step 38.6 levels), then a slow drift toward B (MAD to B 22.9 → 15.7 over 40 frames), 479.8 s. Start/end conditioning strength 0.8 (default prompt): a CONTINUOUS clip — distance to A rises 21.6 → 35.6 and to B falls 37.0 → 16.2 monotonically over the 49 frames, largest adjacent step 4.23 levels (no cut); the graffiti thins while the mosaic emerges under it, the box and wall hold; 539.7 s wall (stage 1 at 21 s per step beside another run), peak RSS 14.4 GB |
| TR6-A, the bridge on the skeleton: SD 1.5 inpainting SDEdit over the tool's skeleton frames, three pairs, 30 frames at 512 px, 2026-09-15 fourth session (`benchmarks/2026-09-15-generative.md §1`; page `benchmarks/runs/2026-09-15/gen/`) | Mean adjacent step, skeleton → fresh noise → warped noise at strength 0.4 (levels): mismatch_1 3.36 → 11.88 → 9.19, mismatch_4 2.08 → 7.21 → 6.91, match_4 2.06 → 9.45 → 4.75. Strength ramp 0.6 · sin(πu) + flow-guided filter: 3.86 / 2.89 / 2.65 (1.15× / 1.39× / 1.29× the skeleton), steps into B 3.1 / 2.6 / 2.9, content 11.6 / 7.7 / 7.9 levels from the skeleton; lifted to the native canvas 4.58 / 3.40 / 3.68 against skeletons 4.00 / 2.69 / 3.18. Same seed byte-identical (5 frames, max abs diff 0). Generator 6.0–13.4 s per frame at 0.4, 13.3–18.0 at 0.6, beside other GPU jobs; peak RSS ≤ 0.8 GB. Over the depth skeleton the warped clip's step is 13.6 / 13.3 (mismatch_4 / mismatch_1) against 6.9 / 9.2 over the pan-zoom skeleton |
| TR10, depth camera move v0 (Depth Anything V2 Small on MPS via transformers 5.17; the pan-zoom field × (0.5 + disparity), near wins the splat), mismatch_1 / mismatch_4, 2 s clips, 2026-09-15 (`§4` of the same sheet) | depth 0.3–2.7 s per image at the native canvas; mid-frame holes ≤ 0.9 % of the canvas at 10 % and 25 % zoom; mean step 1.61 / 1.05 (10 %) and 2.24 / 1.38 (25 %) against the uniform pan-zoom 1.79 / 1.15 and 2.60 / 1.61; warping error equal or lower; render 14–34 s per 60 frames |
| TR6-B and TR6-A2, 2026-09-15 fourth session (`§2–3` of the same sheet; clips under `benchmarks/runs/2026-09-15/{ltx,morphers}/`) | LTX keyframe 0.8 on mismatch_1 / mismatch_4: cut at frame 28 (38 levels) / 31 (21 levels), 1849 / 1961 s beside two GPU jobs, endpoints 5.3 / 5.3 and 7.4 / 10.7; match_4 at 0.6: continuous, max step 4.8, 736 s. LTX `generate` with five skeleton frames anchored, mismatch_1: continuous, mean step 2.28, max 3.87, endpoints 4.4 / 8.4, 11.3 levels from the skeleton clip, 1107 s, RSS 13.8 GB. DreamMover on MPS: 18.2 / 12.0 min (mismatch_1, two runs) and 8.8 min (mismatch_4), memory footprint 18–20 GB, endpoints 6.6 / 4.5 and 3.7 / 4.6 levels off, deterministic to 1 level, no licence. DiffMorpher: weights 404 (gated, not granted), 0.502 s per UNet step and 2.43 s per LoRA step → 42 min per pair at the README's recipe, 7.5 min minimal |
| TR10 built as `--camera flat\|ramp\|model` + `--zoom` (2026-09-23; sheet `benchmarks/2026-09-23-camera.md`, run dir `benchmarks/runs/2026-09-23/`) | Depth Anything V2 Small through transformers 5.17.0 + torch 2.13.0 on the CPU (6 threads): 24,785,089 parameters, 99,173,660-byte safetensors, 0.27–0.31 s per 1024-px image, 1.2 s model load per process (4.9 s cold from disk); MPS 0.06 s warm, CPU-vs-MPS normalized disparity median 0 / p99 0 / max 2e-5 (no device flag built); two CPU runs byte-identical on five inputs. Harness pair: `flat` byte-identical (14 preset × class hashes equal before and after); `ramp` at zoom 0.25 moves the bottom fifth 127.4 px against 52.3 px at the top (2.44×; flat 1.03×), holes 0.00 % at the mid frame, edge step 4 levels. Six mismatched fixtures at ≤ 1920 px, morph 2 s, zoom 0.25: `model` median displacement 26–46 % below `flat` (disparity means 0.12–0.43), mean step 4–14 % lower, warping error ≤ flat on five of six, `edge_ratio` within ±0.06 except mismatch_2 0.19 → 0.24 and mismatch_6 0.53 → 0.59; correspondence 2.4–2.9 s (model) against 0.08–0.45 s (flat), render 2.6–13.3 s per 60 frames; run 2 byte-identical (mp4 md5) on all six. Six class A pairs forced to class B with `model`: mean step 2.1–10.6 against the class A morph's 0.5–5.3. Research push-in (zero at both ends) on the class A field: `edge_ratio` 1.1–1.8 on all twelve clips, the endpoint slope of sin(πu) |

| Layered probe, `scripts/research/layered_probe.py` from hand-written scores, 2026-09-26 third session (§12; sheet `benchmarks/2026-09-26-layered.md`; page `benchmarks/runs/2026-09-26/layered/`) | mismatch_6 at 1146×1524, 60 frames: prep 1.8–3.7 s (the depth model 1.3 s per photo), render 5.8 s, first / last interior step 0.05 / 0.05 levels, `edge_ratio` 0.0105; mismatch_4 at 1920×1092: render 8.0 s, steps 0.11 / 0.23, `edge_ratio` 0.188; mismatch_3 at 1920×1440: render 7.1 s, steps 0.14 / 0.00; two runs byte-identical per pair (md5 `64a54eee…`, `1d2e8bbb…`); `transitions.py` untouched |

Goal numbers on the real surface (2026-09-26, `benchmarks/runs/2026-09-26/surface/` and `bench/`, morph 2 s, canvas ≤ 1920 px, 480-px proxy; run 1 through the CLI and run 2 through the bench script give identical numbers):

| pair | class | feat_floor | laplace_floor | contrast_floor | dissolve_fit | motion_share | total s |
|---|---|---|---|---|---|---|---|
| match_4 (the roster pair) | A homography+dis | 0.420 | 0.728 | 0.809 | 0.070 | −0.031 | 10.6 |
| mismatch_4 (`flat` pan-and-zoom) | B saliency-panzoom | 0.085 | 0.455 | 0.806 | 0.195 | 0.139 | 6.4 |

Reading: `dissolve_fit` as built sees a STATIC crossfade (0.97 on the harness pair; 0.79 AUC on the
pooled real clips) and not a panned one — mismatch_4's pan-and-zoom moves the frame, so the change
is not explained by β·(B − A) in place and the number reads 0.195 although the owner calls the clip
a crossfade. The motion-compensated form (fit after removing the global similarity) is the next
candidate (retrospective §5). `feat_floor` at the 480-px proxy on a smooth sunset is 0.085 with
about 60 SIFT features per endpoint; read it with the feature count in mind.

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
   Owner picks 2026-09-15: 0 of 4 acceptable, "hardly see any improbements since previous runs";
   the owner's direction (verbatim in `EXPLORATION_PLAN.md §Rank, revised 2026-09-15 late`): the
   mismatched pairs are the main problem, the generative tier is the route, and the deterministic
   skeleton stays as the steering and detail source; experiments and resources approved in blanket.
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
.venv/bin/python transitions.py warmup     # once, with the learned deps: fetches the depth model into models/depth/
.venv/bin/python transitions.py pair fixtures/mismatch_1_S.jpg fixtures/mismatch_1_F.jpg --out out/cam --seconds 2 --camera model --zoom 0.25
.venv/bin/python transitions.py pair out/before.jpg out/after_aligned.jpg --out out/tr --seconds 1.5 --preset flow-dissolve
.venv/bin/python transitions.py pair fixtures/mismatch_4_S.jpg fixtures/mismatch_4_F.jpg --out out/anc --seconds 2 \
    --anchors "941,214,960,452;150,530,150,670;1770,530,1770,670" --anchor-falloff 0.45   # theme anchors (2026-09-26)
open out/tr/strip.jpg; cat out/tr/report.json      # report.json: quality.goal = the goal numbers (§2 item 6)
.venv/bin/python transitions_harness.py            # Gate 1b (54 checks, §5)
.venv/bin/python scripts/research/theme_anchors.py --anchors benchmarks/runs/2026-09-26/anchors/anchors.json \
    --out benchmarks/runs/2026-09-26/anchors --page-only --picks theme_anchors_picks.json   # ingest the owner's boxes
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

**Owner picks, 2026-09-15 (`benchmarks/2026-09-15-real-pairs.md §Owner picks`, verbatim there):**
acceptable as-is 0 of 4; overall "hardly see any improbements since previous runs". match_4 → `dis`,
match_5 → `hold-dis`, match_3 → `roma`, mismatch_7 → none; `melt` "too wobly"; the wanted direction
on the box pairs is "even more transformation" with "a bit luma" mixed in, and the owner suspects
`dis`/`hold-dis` + `luma` "work only because it is very close match". Effect on the recommendation:
the position hold is necessary (match_5's pick is the held field) but reads as a fade on its own;
the next probe combines a motion-bearing field with the `luma` reveal at partial strength
(`reveal_strength` k: mix = crossfade × (1 − k) + luma order × k), and adds a stroke-flow motion
along the new content's structure; `melt` is dropped. `hold` stays the named "fade in place" mode.
The `changed` option shape above stands; which values ship waits for a pick that is acceptable.

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
LTX-2.3 int4 through the MLX port, measured 2026-09-15 (match_4 A → B, 384×512, 25 fps, seed 0,
`--dev-transformer transformer-dev.safetensors --cfg-scale 3.0`, the 1.1 distilled LoRA for
stage 2, no `--low-ram`; the pack subset 29.5 GB + the pre-fused distilled transformer 11.3 GB +
Gemma-3-12B 4-bit 8.1 GB in the session scratchpad): 25 frames in 335.7 s wall (Gemma 3.9 s, prompt
15.8 s, stage 1 twenty guided steps at 12.9–13.3 s each, stage 2 three steps at 12–19 s, decode
7.8 s), peak RSS 9.8 GB; 49 frames in 436.1 s (stage 1 at 17.6 s per step, stage 2 51 s), peak
RSS 13.0 GB; with `--low-ram` stage 1 ran at 16–18 s per step and stage 2 refused without the
pre-fused distilled file. The same seed reproduces byte for byte (the two 25-frame mp4s have one
md5). The clips are a CUT, not a transition: the start photo holds (gray MAD to A 21, to B 37 at
384×512) and the finish photo takes over at frame 14 of 25 and frame 18 of 49 (MAD to A 36, to B 16)
with an adjacent-frame step of 34 levels, the size of the A–B gap; no frame lies between the two
photos. Endpoints are not the inputs (MAD 21 / 16 levels: the pipeline re-encodes and re-grades
them). Not established why: the prompt ("static camera"), the conditioning strengths (1.0 both
ends), the int4 pack and the port's keyframe recipe are each untested levers (`--start-strength`
/ `--end-strength` below 1, a prompt that names the change as motion, 97 frames, the q8 pack).
Levers, 2026-09-15 late (49 frames each): the motion prompt alone keeps the cut (frame 7) and
adds a slow drift toward B; start/end conditioning strength 0.8 removes the cut: a continuous clip
whose distance to A rises and to B falls monotonically (largest adjacent step 4.2 levels), the
graffiti thinning while the mosaic emerges under it, box and wall holding (`benchmarks/runs/2026-09-15/ltx/
match_4_kf49_strength08.mp4`, strip beside it). So the video route works with the endpoints held
at 0.8, at 6–9 min per 49-frame clip; whether the in-between reads as a transformation or a
graded fade is the owner's verdict; the endpoints are re-encoded (MAD 21 / 16), so the tool's
byte-exact endpoints must come from the skeleton (splice the model's frames between frame 1 and
n−2, or blend the first/last few frames toward the photos). Reading: the video route is affordable
under the owner's timing rule and now produces an in-between; the masked SD 1.5 pass gives an
intermediate but no coherence. Neither is adoptable yet; the strength-0.8 clip is the first
generative candidate for a verdict, and the q8 pack and strengths 0.6 / 0.9 are the next levers.
Gate for adopting any of it (unchanged from the plan): a fixed seed reproduces, s/frame stated
on this Mac, the license recorded, the weights behind warmup + manifest + refuse-to-download.
Fourth session, 2026-09-15 (sheet `benchmarks/2026-09-15-generative.md`; scripts
`scripts/research/gen_bridge.py` and `depth_dolly.py`; the research artifact's `warp_noise_along_flow`
and `frequency_split_blend` ported into the script): the bridge on the skeleton was measured, and
the strength ramp with a flow-guided filter is the first configuration that passes the research
plan's E17 gate on every pair tried. Five facts:
1. SDEdit from the skeleton frames (SD 1.5 inpainting, 512 px long edge, guidance 6) at strength
   0.4 re-draws the skeleton's double exposure into one scene, but flickers at 2.7–3.5× the
   skeleton's adjacent step with fresh noise per frame. Noise carried along the skeleton's
   displacement (frame 0's noise, nearest-neighbour warp at pixel resolution, 8×8 block sums to
   the latent grid) cuts that by 4 % (mismatch_4), 23 % (mismatch_1) and 50 % (match_4), and the
   same seed reproduces byte for byte. The last generated frame still jumps 7–15 levels into B.
2. Ramping the strength as 0.6 · sin(πu) removes the endpoint jump (steps into B 3–4 levels), and a
   filter along the skeleton's flow (each frame averaged with two neighbours each side warped into
   it, weights 1 2 3 2 1) brings the mean adjacent step to 1.15× (mismatch_1), 1.39× (mismatch_4)
   and 1.29× (match_4) the skeleton's, with the content 7.7–11.6 levels from the skeleton (not a
   collapse back to it). Lifted to the native canvas with the frequency split (σ 3 px) the ratios
   are 1.15–1.26×. Generator cost 3.5–6.5 min per 30-frame clip beside other GPU jobs.
3. What the basket does not see, by the agent's eye: match_4 gets a different mural in every frame
   (a per-frame model has no memory), mismatch_4 at 512×288 gets blocky tiles in the sky and water,
   mismatch_1 is the one clip that reads as a transformation. The TR10 depth skeleton (Depth
   Anything V2 Small, 0.3–2.7 s per image; a pan-zoom scaled by 0.5 + disparity) doubles the
   flicker under the bridge and, alone, is a crossfade with parallax: no tearing, holes ≤ 0.9 %.
4. LTX-2.3 keyframe interpolation at endpoint strength 0.8 is a cut on both mismatched pairs
   (mismatch_1 frame 28, 38 levels; mismatch_4 frame 31, 21 levels) after each photo drifts
   toward the other's composition; strength 0.6 on match_4 is continuous like 0.8 (largest step
   4.8). With five skeleton frames anchored (`generate --image`, strengths 0.8 / 0.6 / 0.6 / 0.6
   / 0.8) mismatch_1 is continuous (mean step 2.28, max 3.87, endpoints 4.4 / 8.4, 1107 s beside
   the SD batch) and copies the skeleton's double exposure instead of resolving it. `retake` of the
   skeleton clip's middle latents (pixel frames 9–32, 30 steps) is a re-encoding of the skeleton:
   continuous (mean step 1.97), endpoints 4.4 / 4.0, and 4.6 levels from the skeleton where it
   regenerated against 2.4 where it kept (the codec), 1505 s. The same five-anchor recipe on
   mismatch_4 (512×256): continuous, mean step 1.32, endpoints 7.6 / 12.7, 11.7 levels from the
   skeleton, two suns visible mid-clip as in the skeleton, 512 s alone.
5. The two published two-image morphers fail the E16 gate: DreamMover (SD 1.5, five MPS patches)
   takes 8.8–18.2 min per pair, re-draws the endpoints (3.7–6.6 levels off) and has no licence
   file, so it cannot be vendored; DiffMorpher's SD 2.1-base weights are gated and return 404 to
   the owner's token, and its measured step costs give 42 min per pair. DreamMover's sun-to-sun
   clip is the most morph-like result of the session (the sun travels with its reflection).
Reading: the per-frame SD bridge is the cheapest route that passes the plan's own gate and the
only one whose endpoints are the tool's byte-exact frames. Its two visible defects need either
the video model with the skeleton as a weak guide (anchor strengths below 0.6, or `retake` on the
skeleton clip re-encoded it, so the guide has to be weaker than 0.6 or a different kind) or an
auto-regressive input (the previous generated frame warped by the skeleton's displacement as the
next frame's input). Nothing is adopted until the owner's picks; if one is, the shape is a
research script behind `transitions.py` with the weights under warmup + manifest (decisions
24–27), the generator on the 512 px canvas and the lift to the native canvas.
Owner verdict, 2026-09-22/23 (sheet §6): every bridge clip rejected ("horrible neural slop …
halucinations artifacts in almost all intermediate frames which preserve no features"), and the
LTX clips too ("animated in weird way … individual before/after images but transition between
animations are usually a cut or dumb fade so this defeats all purpose ( at least for that test
run )"). The generative tier is parked as measured. The one thing the owner liked is the TR10
depth camera move ("really liked the effect on all individual images especially z25 … at least as
option"), approved on 2026-09-23 with its model leg ("yes to model, and run it on matched pairs
too ( as a test, need to compare)"): it becomes a `transitions.py` option (plan §Rank 2026-09-23).
Built the same day as `--camera flat|ramp|model` + `--zoom` (§2.3, harness L); the sweep with the
three cameras is `benchmarks/2026-09-23-camera.md`; the owner's picks of 2026-09-25 (its §5): 0 of 12, every camera "unnecessary pans and basically cross fading"; `--camera` stays an option, not the transition.

### 10.9 Found on the way, not TR14's
`hold` on mismatch_7 exposes the start frame's moved border as a rectangle at mid-transition:
the pair's homography is a 250 px zoom and shift, and where the moved start frame no longer
covers the canvas the coverage-aware mix in `morph_frame` switches to the finish frame (the
class A twin of defect T13; DIS hides it by tearing the sky). It shows on any class A pair with
a large camera motion (match_5: a 35 px band at one edge at mid-frame). A canvas rule answers it
(TR13's shared-area mode), or a reflected fill without the mix switch for content like sky.
Recorded as backlog T14.

### 10.8 Open questions for the owner
1. Answered 2026-09-15 (picks above): none acceptable; "even more transformation", `dis`/`hold-dis`
   + "a bit luma" is the direction; the next page carries the partial-strength luma and a stroke-flow.
2. `hold` (RoMa) against `hold-dis` (DIS + mask): is the background motion RoMa gives on match_4
   worth the dense matcher, or is the weight-free `hold-dis` enough?
3. TR6: which backend may be fetched first (license and size in §10.7). Answered 2026-09-22/23 and
   2026-09-26: the per-frame bridge and the LTX clips are rejected as measured; the generative role is
   generated keyframes on the second machine (§11, plan §Rank 2026-09-26 item 4), route approved by
   the owner on 2026-09-26 ("i am ok with your reccomended route in general").

## 11. Goal statement and goal metrics (2026-09-26; the owner confirms the statement)

Retrospective: `audits/retrospective-2026-09-26.md`. After six review rounds and about 340 clips
with no accepted clip, the record shows that every slice since TR1 varied the correspondence field,
the border or the camera, while the combination of A and B in `morph_frame` stayed the alpha
crossfade; the owner grades the combination. The goal, as read from the owner's words (verbatim in
the retrospective §1; to be confirmed): every intermediate frame is one coherent picture made only of
details that exist in A or B; those details move and change continuously from A to B; for unrelated
photos the motion is organised by shared themes (sun to sun, skyline to skyline, face to face); a
subject that does not move keeps its place while its surface transforms; nothing is invented; a
camera move is decoration, not the transition. Three failure modes: F1 double exposure, F2 decoration
without transformation, F3 invention.

Goal metrics (candidates, calibrated on the owner's recorded verdicts by
`scripts/research/verdict_metrics.py`; numbers in the retrospective §5 and
`benchmarks/runs/2026-09-26/metrics/scores.md`): `feat_floor` (SIFT feature survival to the nearer
endpoint, minimum over the clip), `laplace_floor` and `contrast_floor` (sharpness and local contrast
against the endpoints' interpolation, minimum), `local_share` (non-rigid share of the frame-to-frame
flow), `dissolve_fit` (the share of the frame change a plain crossfade explains). The shipped basket
(§2 item 6) screens defects; it does not separate the owner's "crossfade" verdicts from the closest
picks (AUC 0.46–0.48). Built 2026-09-26 (the owner confirmed the statement the same day and ordered the build, DECISIONS
2026-09-26): `goal_numbers` in the Quality section, `assess()` gains `goal`, harness section M
(52–53, both mutations paid), the bench sheet and the review page carry the five numbers and
three per-property boxes per clip (one picture · content transforms · nothing invented; exported
under `props` in `picks.json`), frames byte-identical (14 preset × class hashes equal), numbers
identical across two runs on match_4 and mismatch_4 (§6). Owner answers of 2026-09-26 (verbatim
in DECISIONS): the goal paragraph is "totally right" and gains two sentences — the transition is
tunable per scene; colours, luminosity and transparency stay natural even where the content is
impossible, adhering to one higher-order flow; F3 is refined: invented content is allowed as a
generative helper element, executed deterministically and fluently, preserving the start and end
details, seamless — one or several generated KEYFRAMES that deterministic interpolation bridges,
never full video generation; a second machine (Strix Halo, 128 GB) exists for the image models;
the ideal for mismatch_4 is a LAYERED transition (sun → sun, skyline with depth, river, clouds
materialising, each independently and consistently); per-pixel switches with hard colour borders
are junk. The class B anchors path (`--anchors`, MLS) was
exercised on a real pair for the first time on 2026-09-26 (mismatch_4, three auto-detected theme
anchors): one sun instead of two at mid-frame; its moved-frame edge shows at the left (the T13 twin
on the MLS path).

Research of 2026-09-26 that the next design pass starts from (primary sources; reports under
`benchmarks/runs/2026-09-26/research/`, gitignored, copied out of the session scratchpad):
- **Track E, the layered scene transition** (`track_E.md`): every step of the owner's sentence for
  mismatch_4 has a deterministic, CPU-feasible technique with no generative step — semantic layers
  from OneFormer or Mask2Former on ADE20K (MIT; a new weights file behind warmup + manifest; ADE20K
  has no sun or cloud class, both come from rules on the sky layer), the sun moved by the closed-form
  Bures–Wasserstein map between two Gaussians (one sun sliding and reshaping, never two), the cloud
  mass moved by convolutional Wasserstein displacement (Solomon 2015) with Neyret's advected texture
  (works for isotropic texture such as clouds and water, not for a skyline), the skyline and horizon
  by Lipman's four-point Möbius map (bijective, spreads distortion; MLS folds and concentrates it) plus
  the existing MLS detail, a per-layer Lab colour path so no two-tone border exists, and a
  Laplacian-pyramid composite ordered by the existing depth. Estimated 1–3 min per 1080p clip
  [INFERRED]; nothing measured; `opencv-python-headless` 5.0.0 has no `xphoto` / `ximgproc`;
  POT would be a new dependency (the Gaussian formula and a Sinkhorn loop need none).
- **Track D, generated keyframes on the second machine** (`track_D.md`): Qwen-Image-Edit-2511
  (20 B, Apache-2.0, 1–3 input images natively, 57.5 GB bf16, 113 s cold per 1.6 MP image on a
  Strix Halo with the 4-step Lightning LoRA, one input image measured) is the first candidate,
  FLUX.2 [klein] 4B (Apache-2.0, 7.75 GB, about 22 s at 1024² on gfx1151) the fallback; FLUX.2 [dev]
  and HunyuanImage-3.0 do not fit the box or the licence. Recipe: the tool's own mid frame as the
  starting image, both photos as references, a partial-denoise pass, a fixed seed, the keyframe
  cached with a manifest (model and LoRA sha256, workflow hash, seed, denoise, prompt, software
  versions); the engine interpolates A → keyframes → B segment by segment. Strix Halo: ROCm 10.0
  lists gfx1151 with PyTorch 2.11–2.13, FP16 validated (not BF16), the GPU pool defaults to half the
  RAM, kernel ≥ 6.18.4, fast attention behind an experimental flag. The offline contract holds only
  if keyframes are made by a separate script the operator runs on purpose and `transitions.py`
  reads cached files. Published two-image morphers (FreeMorph, AlignMorph) fall back to plain
  interpolation on unrelated pairs by their own account. Nothing measured; every speed is reported
  or inferred. Track F (2026-09-26, `track_F.md`) chose the container: stable-diffusion.cpp's Vulkan
  image pinned by digest (`/dev/dri` only, no ROCm) with the Qwen-Image-Edit-2511 GGUF set (19 GB),
  one-shot with caps and a pre-flight (`scripts/research/strix_keyframe.sh`); the owner approved the
  route in general the same day; the box was probed read-only (35 GB available, Vulkan 1.4 RADV
  GFX1151, rootful Docker → `sudo docker --user`, Tailscale logged out on the box, reach through the
  prod box as a jump host). Not run yet.

Theme anchors, 2026-09-26 (late; owner: "Go on with theme anchors , feel free to explore"): the
hand-placed anchors page `benchmarks/runs/2026-09-26/anchors/index.html` renders the six mismatched
pairs as `flat`, `anchors_alpha` (hand-placed theme anchors through `--anchors`), `anchors_falloff`
(the same at `--anchor-falloff 0.45`) and `anchors_auto` (automatic anchors, where three or more were
found: mismatch_1–4), with the goal numbers and the three boxes per clip
(`scripts/research/theme_anchors.py`; sheet `sheet.md`). The automatic probe
(`scripts/research/auto_anchors.py`, DINOv2-S at 518 px with mutual nearest neighbours and a ratio
test, a brightest-blob sun, the strongest horizontal edge row as the horizon, YuNet faces) found 0–6
mutual patch matches per pair at similarity ≥ 0.55 (0 on mismatch_4 and 5), faces on mismatch_2 (1 / 3)
and mismatch_3 (11 / 9), the sun on mismatch_4 (both), and false suns (a bright cloud) on mismatch_1 and
6: DINOv2 patch matching across whole unrelated scenes is not an anchor source; the classical detectors
and label-matched panoptic layers (Track B recipe 1) are. The owner's boxes (2026-09-26, verbatim in
DECISIONS 2026-09-26 late): `one_picture` and `transforms` on no clip, `not_invented` on every graded
clip; the frame edge "hard ugly"; a few-anchor whole-frame warp reads as "one picture rotates" or a
"3D plane flip"; mismatch_3 asks for depth layers moving independently; mismatch_6 is scored in time
(clouds dissolve, the sky darkens, stars appear, buildings exit downward, trees and the
air-conditioning unit enter). The next design pass (§12, to be written) is the orchestrated layered
transition with a per-scene score; the anchors' default falloff is 0.45 since the same day.

## 12. The orchestrated layered transition: the score, the probe, the first three clips (2026-09-26, third session)

Result: a hand-written per-scene SCORE (layers × one action each × a time window) rendered by a
research script gives clips in which every interior frame is a composite of layers, each layer
showing one photo's content; the first three probes (mismatch_6 exactly as the owner scored it,
mismatch_4 from the owner's sentence of the same day, mismatch_3 by depth bands) are on
`benchmarks/runs/2026-09-26/layered/index.html` beside the two clips the owner graded on the
theme-anchors page, ungraded as of 2026-09-26. Nothing in `transitions.py` changed. The script is
`scripts/research/layered_probe.py`; the scores are `scripts/research/scores/<pair>[_variant].json`
(tracked); the sheet is `.claude/claude-docs/benchmarks/2026-09-26-layered.md`. Sources: the owner's
mismatch_6 score and mismatch_3 note (verbatim in DECISIONS 2026-09-26, late), the mismatch_4
sentence (plan §Rank 2026-09-26 item 1), Track E's ten steps (`benchmarks/runs/2026-09-26/research/track_E.md §6`),
Track B's recipe (`track_B.md §5`).

### 12.1 The score: what the owner edits

One JSON file per pair: `pair`, `seconds`, `fps`, `max_long`, the owner's sentence under `owner`,
and `layers`. A layer has a `name`, a source photo `from` (A or B), a `mask` rule with parameters,
a compositing `depth` (0 is the back), one `action`, a `window` [t0, t1] in clip fractions, a
`curve` (the tool's `CURVES`), and optional terms: `recolor_to` + `recolor_strength` (the colour
path), `drift` (canvas fractions over the window), `zoom` ([z0, z1] about the canvas centre over
the window), `direction` and `travel_px` (exit / enter / move), `order` and its noise parameters
(dissolve / materialise), `render: false` (a layer that only lends its mask and statistics).

Mask rules in the probe, all from the two photos and the offline depth model (Depth Anything V2
Small through `transitions.model_disparity`, the 2026-09-23 weights):
- `depth_fg` / `depth_bg`: disparity between `lo` and `hi`; `dilate` widens the region, `refine:
  dark` keeps only pixels darker than the per-row brightness of the rest of the photo (leaf-level
  detail the depth lacks), `grow` lets a moving layer carry the background within a few px of its
  edge, `components` keeps the connected parts touching one border.
- `skyline_below` / `skyline_above`: a per-column skyline from the depth (the topmost row whose
  next 20 rows are 70 % near and whose rows down to the bottom are 60 % near), with a texture veto
  (the depth model rounds a roof into a dome of "near" sky) and hand polygons `union` for what the
  depth misses (the far glass tower of mismatch_6 sits at disparity 0–0.03 and was added by hand).
- `band_dark`, `above_band`, `below_band`: the dark silhouette band under the sky per column
  (from the first near row through the run of rows with L below `dark_L`), and the sky above or
  the water below it; `depth_band` for a disparity interval; `polygon`, `invert`, `invert_any`, `all`.
- `clouds`: a density against the clear sky of the same rows (a low percentile of b* over a window
  of rows for a day sky, of L for a sunset); `stars`: white top-hat blobs, ordered bright-first with
  jitter; `sun`: the brightest blob inside a layer with its Gaussian moments.

Actions: `backdrop` (the per-row Lab fit of the layer moves from the A layer's to the B layer's
while the residual textures crossfade; alpha 1 for the base, or a matte that moves from the A mask
to `mask_to`), `hold`, `recolor`, `dissolve` and `materialise` (the matte erodes or grows through an
order field: the layer's own density, its blobs, its luma, its row position, or noise), `exit`,
`enter` and `move` (a translation until the layer's box leaves or reaches the canvas), `move_to`
(the closed-form Bures–Wasserstein map between the layer's Gaussian and the target's, interpolated
as ((1 − p) I + p T) x + p b; Track E §2.4). The colour path is per layer and per row (48 bands):
Reinhard's statistics transfer toward the counterpart layer by the layer's own progress, so a sky
darkens as a gradient and a cloud dims toward the night sky while it erodes. Compositing is the
over operator back to front on soft mattes; frame 0 is A and the last frame is B, exactly. The one
mixed quantity is the backdrop's residual (the sky texture after the fit; on mismatch_4 also the
water's, which carries the sun road), faded from A's to B's over the backdrop's window.

### 12.2 What the three probes measured (2 s, 30 fps, canvas ≤ 1920 px, the tool's basket on the 480-px proxy)

| pair (canvas) | clip | edge_ratio | feat_floor | laplace_floor | contrast_floor | dissolve_fit | motion_share | first / last interior step, levels | wall s |
|---|---|---|---|---|---|---|---|---|---|
| mismatch_6 (1146×1524) | `layered` (the owner's sequence) | 0.0105 | 0.055 | 0.241 | 0.197 | 0.226 | 0.290 | 0.05 / 0.05 | 9.4 |
| mismatch_6 | `layered_overlap` (windows overlap; the clouds drift and zoom out 6 %, the buildings zoom out 8 % as they leave) | 0.0132 | 0.006 | 0.195 | 0.193 | 0.245 | 0.304 | 0.06 / 0.05 | 9.5 |
| mismatch_6 | `flat` / `anchors_falloff` (graded 2026-09-26: not one picture, no transformation) | 0.672 / 0.789 | 0.128 / 0.159 | 0.330 / 0.340 | 0.639 / 0.665 | 0.492 / 0.803 | 0.016 / −0.001 | — | 6.9 / 6.9 |
| mismatch_4 (1920×1092) | `layered` (sun moved by the Gaussian map, scale 0.86 × 0.83, translation (156, 271) px; the A skyline sinks and dissolves top-down while drifting 26 % of the height; B's skyline rises; B's clouds materialise by density) | 0.188 | 0.108 | 0.518 | 0.713 | 0.215 | 0.003 | 0.11 / 0.23 | 13.2 |
| mismatch_4 | `flat` / `anchors_alpha` (the owner's pick of the day) | 0.164 / 0.134 | 0.085 / 0.171 | 0.455 / 0.619 | 0.806 / 0.814 | 0.195 / 0.046 | 0.139 / 0.448 | — | 6.4 / 8.2 |
| mismatch_3 (1920×1440) | `layered` (three depth bands per photo; A's bands dissolve by noise back to front with 4–8 % zoom-in, B's materialise in the same order over B as the base) | 0.0707 | 0.445 | 0.914 | 0.949 | 0.195 | −0.064 | 0.14 / 0.00 | 10.1 |
| mismatch_3 | `flat` / `anchors_falloff` (the owner's pick of the day) | 0.059 / 0.056 | 0.065 / 0.051 | 0.457 / 0.474 | 0.710 / 0.712 | 0.024 / 0.019 | 0.189 / 0.422 | — | 9.1 / 10.1 |

Two runs of the final script give byte-identical clips (md5 `64a54eee…` for mismatch_6 `layered`,
`1d2e8bbb…` for mismatch_4; seeds are fixed). The depth model costs 1.3 s per photo inside `prep`.
Reading the numbers: the goal numbers were calibrated on crossfade-versus-closer verdicts (§11)
and do not see an orchestration. The low `feat_floor` and `laplace_floor` on mismatch_6 (0.055 and
0.24) measure the frames in which the sky is a smooth gradient with the clouds gone and the trees
not yet in, which is what the owner's sequence asks for; the same numbers on mismatch_3 (0.45,
0.91, 0.95) show a composite that keeps every layer sharp, because no pixel is a mix of A and B
content. Whether any of this is "one picture" or "content transforms" is the owner's verdict; my
eye is not evidence.

### 12.3 Defects seen while building (by my eye; the owner's boxes decide the rest)

- The depth model is smooth at edges: the tips of a tree crown sit at disparity 0, the sky beside
  the trees at 0.08–0.13, a dome of "near" sky (0.05–0.15) sits above the left roof of mismatch_6,
  and the far glass tower is as far as the sky. Every foreground matte needed a photo-based
  refinement (darkness, texture, a hand polygon). A panoptic model (Track B recipe 1) is the
  next mask source and is a new weights file behind `warmup` and a manifest: the owner's decision.
- The moved sun carries its blob and 40 px of glow; the wider glow stays in A's residual and B's
  glow fades in at the target before the sun arrives (the F1 remnant of this pair). Track E step 4
  (a radial glow re-rendered around the moving centre) is not built.
- The sinking A skyline of mismatch_4 shows vertical streaks at its tall left shore, and B's clouds
  come in as blotches (density order plus 50-px noise).
- The mismatch_3 clip is a depth-ordered patch reveal with parallax, the honest deterministic
  answer where no correspondence exists; content does not transform inside a layer. That needs
  generated keyframes (plan item 4) or a correspondence that does not exist for this pair.
- Four probe bugs fixed on the way, each a trap for the tool: the cosine ease is not monotone
  outside 0..1 (clip the window progress before the curve); an entering layer's travel must be
  measured along the reverse of its direction; a per-column texture skyline spikes at cloud edges;
  a half-weighted residual under a layer's soft edge stays behind as a ghost when the layer
  moves (the residual is interior-only; a moving layer carries the background near its edge).

### 12.4 The shape it takes in the tool, when a probe is graded

Nothing enters `transitions.py` before the owner grades a probe "one picture" or "content
transforms" (handover rule of 2026-09-26). The shape then: `pair … --score FILE` renders the score
instead of the preset (the experimental lane: a new option, the default path and the 14 frame
hashes untouched; class `L`, method `layered-score` in `report.json`); the rules and actions
become one new section "Layers" between Depth and Morph; the harness pins frame 0 and the last
frame byte-exact, every matte in 0..1, the first and last interior step below 1 level on the
synthetic pair, and the determinism of a seeded score, with a paid mutation (the unclipped ease).
The score file is the operator surface the owner asked for ("flexibly tune and control per
scene"); its keys above are the contract to record in `contracts.md` on that day.

### 12.5 Questions for the owner

1. Grade the three probes with the three boxes; the score files are the knobs, say what a layer
   should do differently.
2. mismatch_6: the literal sequence (an empty sky between the clouds' exit and the trees' entry) or
   the overlapping one?
3. Layer masks: keep rules on the depth model and the photo, or fetch a panoptic model (Mask2Former
   Swin-Tiny, MIT, about 190 MB per Track B, UNVERIFIED size) behind `warmup`?
4. The moved sun's glow: re-render it around the moving centre, or accept the fade?
5. mismatch_3: is a per-layer patch reveal with parallax a family worth tuning, or is it "cross
   fade with cheap effects"?
