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
| Layered probe round 2 on mismatch_6, 2026-09-26 fourth session (§12.7; page `benchmarks/runs/2026-09-26/layered_r2/`; scores `mismatch_6_r2{,_L,_drift}.json`) | 1146×1524, 3 s, 90 frames: prep 3.4–5.0 s, render 7.2–8.0 s; first / last interior step 0.28 / 0.05 levels on all three clips; `edge_ratio` 0.097 / 0.0965 / 0.0934; two runs byte-identical (md5 `cddde79e…`, `f3efeeef…`, `7934592a…`); round 1's score still renders md5 `64a54eee…` through the changed probe; `transitions.py` untouched |
| Layered probe round 2 on mismatch_4, 2026-09-26 fourth session (§12.7; the same page; score `mismatch_4_r2.json`) | 1920×1092, 3 s, 90 frames: prep 4.3 s, render 9.6 s; steps 0.12 / 0.10 levels (round 1: 0.11 / 0.23); `edge_ratio` 0.172; two runs byte-identical (md5 `b7700b4c…`); `transitions.py` untouched |
| Layered probe round 3 on mismatch_6, 2026-09-27 (§12.9; page `benchmarks/runs/2026-09-27/layered_r3/`; scores `mismatch_6_r3{_clouds,_soft,}.json`) | 1146×1524, 3 s, 90 frames: prep 5.2–6.6 s, render 7.6 s (clouds), 13.9 s (both), 18.8 s (the shutter blur alone: 8 s over round 2's 10.6 s); first / last interior step 0.03 / 0.05 levels with the round-3 cloud matte, 0.28 / 0.05 without it; `edge_ratio` 0.0156 / 0.1056 / 0.0169; two runs byte-identical (md5 `748b68ed…` / `ecbbcb61…` / `f2c3c02f…`); round 2's `cddde79e…` unchanged through the changed probe; `transitions.py` unchanged |
| Layered probe round 3 on mismatch_4, 2026-09-27 (§12.9; the same page; score `mismatch_4_r3.json`, motion only) | 1920×1092, 3 s, 90 frames: prep 4.7 s, render 17.2 s; steps 0.12 / 0.10; `edge_ratio` 0.1745; md5 `a9f1e3d6…` on two runs; round 2's `b7700b4c…` unchanged; the four cloud-layer attempts: last step 0.42 / 0.75, `edge_ratio` 0.67 / 1.19, rejected on the frames |
| Layered probe round 4, 2026-09-27 evening (§12.10; page `benchmarks/runs/2026-09-27/layered_r4/`; scores `mismatch_4_r4.json`, `mismatch_6_r4.json`, `scores/auto/*.json`) | 3 s, 90 frames. mismatch_4 (1920×1092): prep 6.1 s (the transport plan included), render 14.2 s, steps 0.10 / 0.10, `edge_ratio` 0.0925, md5 `e7b331de…`. mismatch_6 (1146×1524): 7.3 / 11.9 s, steps 0.06 / 0.05, 0.0318, `1aef9fa5…`. Automatic scores: mismatch_1 (1444×1920) 4.6 / 9.7 s, 0.07 / 0.04, `80dc31a9…`; mismatch_5 (1920×1080) 15.3 / 9.5 s, 0.0 / 0.0, `08bb31de…`; mismatch_3 (1920×1440) 24.7 / 12.3 s, 0.0 / 0.0, `52c4e57a…` (a whole-frame plan of 2,304–3,072 cells a side costs 10–20 s). Two runs byte-identical; the nine md5s of rounds 1–3 unchanged; `transitions.py` unchanged |
| Mask routes on 18 fixture photos, 2026-09-27 evening (§12.11; `scripts/research/mask_routes.py`; page `benchmarks/runs/2026-09-27/masks/`; M3 Pro, CPU, 6 torch threads, beside other jobs) | Mask2Former Swin-Tiny COCO panoptic: 190,052,872 B, 47,436,800 parameters, 133 labels, load from cache 0.14 s, inference median 1.19 s (max 1.53 s) per photo, peak RSS 3.77 GiB. ADE20K semantic: 190,189,605 B (+ a second 190,070,416-B file fetched in the background), 150 labels, 0.62 s (max 1.06 s), 2.93 GiB. Offline re-run: 36 of 36 label maps byte-identical, 0 B downloaded. Rules: depth 0.28 s and the fixed rule set 0.36 s per photo (medians); the tuned masks 0.86 s (mismatch_4) and 2.41 s (mismatch_6) per pair |
| Layered probe round 5, 2026-09-28 (§12.13; page `benchmarks/runs/2026-09-28/layered_r5/`; scores `mismatch_{4,6}_r5*.json`, `scores/auto/*_v2.json`; M3 Pro, CPU) | 3 s, 90 frames, twelve clips byte-identical on three runs. mismatch_6 (1146×1524): prep 17.5–18.2 s, render 15.3 s; automatic 2.4 / 17.1 s. mismatch_4 (1920×1092): prep 4.2–5.6 s, render 14.0–18.7 s; automatic 6.0 / 33.1 s. Automatic on untuned pairs: mismatch_1 5.0 / 29.5 s, mismatch_5 8.6 / 18.5 s, mismatch_3 (1920×1440, 11 layers) 20.9 / 77.1 s, mismatch_2 (602×800) 23.8 / 9.7 s, mismatch_7 (1920×1488) 7.9 / 35.7 s. Frames beside the endpoints against the photos: mismatch_4 0.000 / 0.004 levels (round 4: 0.183 / 0.151) |
| Layer source on the 24 fixture photos, 2026-09-28 (§12.14; `scripts/research/layer_source.py`; page `benchmarks/runs/2026-09-28/layers/`; M3 Pro, CPU, 4 torch threads, beside render jobs) | OneFormer Swin-L ADE20K 880 MB (semantic 3.09 s, panoptic 2.58 s per photo, medians over 18 photos) + CLIPSeg rd64-refined 605 MB (1.99 s); the whole script 8.8–22.5 s per photo, 15.2 s for mismatch_4_S on the main thread; `layers.npz` and `layers.json` byte-identical on repeated runs; offline re-runs identical, no socket attempt |
| Keyframe-cleaned clip, 2026-09-28 (§12.15; `scripts/research/keyframe_clip.py`; page `benchmarks/runs/2026-09-28/keyclip/`) | FLUX.2 klein 9B Q8_0 on the second machine: 68–69 s per keyframe at 1344×768, 50–51 s at 768×1024, MemAvailable 37.0 → 18.2–19.3 GiB. Clips of 90 frames at the keyframe size, byte-identical on two renders; four segments per clip through `transitions.py pair --preset morph` |

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

Amendment 2026-09-27 (the owner restates the goal and warns against overfitting; verbatim, DECISIONS
2026-09-27 evening): "I want to re-corfirm once again general idea and warn you to not overfit on these
specific example pairs that i have provided, these are just random matches/mismathes, always remember
that eventually i want this to be universal solution (tunable and adjustable)  to achieve some absurd
but weirdly fitting and fluid transitions between both fully, partially and completely unrealted photos
and videos, hence the complexity and all experimentation". What it changes in practice: (1) a mechanism
is judged on pairs it was not tuned on, so every review page from 2026-09-27 on carries clips rendered
from an AUTOMATIC score (fixed rules, no per-pair parameter; §12.10) beside the hand-written ones; (2) a
hand-written score is the operator's tuning of a scene, never the proof that a mechanism works; (3)
per-pair mask rules count as tuning (§12.11 compares them with a model that names regions); (4) video
input is part of the goal; no slice covers it yet (TR4 in the plan is clip input and output only).
The owner's specification of it (2026-09-27 night; verbatim in DECISIONS): start with the last frame of
clip A into the first frame of clip B; the wanted form takes a chosen moment in each clip and reads
"several frames before last frame in clip A and several frames after target frame in clip B to better
capture flow and dynamic otherwise it can create inconsitent movement in transitions"; a photo has no
such frames ("there you work with what you have"); "hybrid mode" joins video A to photo B and photo A
to video B. Design reading [INFERRED, not built]: an endpoint is a frame plus a velocity field measured
from its neighbouring frames, and a layer's progress curve takes that velocity as its boundary
condition; a photo endpoint has zero velocity, so the three cases are one mechanism.

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

### 12.6 Owner picks on the first three probes (2026-09-26, 13:19 UTC; `benchmarks/runs/2026-09-26/layered/layered_picks.json`)

Verbatim. mismatch_6, closer: none; boxes `layered` and `layered_overlap` = content transforms +
nothing invented (one picture on none), `flat` and `anchors_falloff` = nothing invented: "anchors_falloff
and flat more or less same as in previous runs ( at least not worse ), layered variants added
intneresting movements of clouds / front objects but they leave a lot of countours , afterimages and
in general feel too direct and rushed , but i like how  you at least was able to isolate some objects
and themes in layered variants, still very junky and crossfade is present in all variants ( although
in anchors_falloff it is  rather subtle )". mismatch_4, closer: `anchors_alpha`; the layered clip has
no box: "anchors feel more or less same as in previous runs ( at least not worse, somewhat smooth,
still crossfade present ), layered variants in this example are very juny patchy dirty transitions ,
not useful at all , i feel like this is because for this example luma and colors vary between frames
and also lots of distinct edges". mismatch_3, closer: none; the layered clip has no box: the same
sentence without "somewhat smooth".

What follows, pair by pair (the agent's reading; the owner corrects it):
- mismatch_6: the two layered clips are the first on record with "content transforms" ticked (none
  of the 22 clips on the anchors page had it, nor any earlier page). "One picture" still fails.
  The faults the owner names map onto known parts of the probe [INFERRED]: "contours" onto the
  matte edges (the tree crown's `grow` band, the per-column skyline cut, the cloud fringe);
  "afterimages" onto what stays behind a moving layer (the extrapolated sky fit under the exiting
  buildings, the residual under soft edges); "too direct and rushed" onto a 2 s clip whose actions
  run one after another with eased translations; "crossfade is present" onto the backdrop's
  residual crossfade and the clouds' recolour while they erode. The next mismatch_6 probe removes
  each source in turn (§12.7 in the handover) before anything enters the tool.
- mismatch_4 and mismatch_3: noise-ordered dissolves and materialisations are rejected wherever a
  layer has internal structure (the whole mismatch_3 score; mismatch_4's clouds and skyline band).
  The owner's cause stands as the rule: a patch reveal shows the two photos' luma and colour
  side by side across many edges. The mismatch_3 depth-band family is out; mismatch_4's next probe
  keeps only the sun move and the two backdrops with a clean slide of the skyline band.
- The gate of §12.4 reads "graded one picture or content transforms": its letter is met by
  mismatch_6 `layered`; the owner's note grades the same clip "very junky". Recommendation: no
  tool build yet; one more probe round on mismatch_6 aimed at "one picture", then the owner grades
  again. The owner decides (handover question 1).

Owner answers to the two round-2 questions (2026-09-26, verbatim): "1) i see afterimage for tree
crown, distinct clouds, bottom buildings contours 2) keep 3s for now". Round 2 therefore targets, in
this order, the tree crown (the leaf tips outside the depth matte ghost in the sky residual; the
`grow` band), the distinct clouds (the cloud fringe left in the backdrop's residual while the clouds
erode, and their recolour), and the bottom buildings' contours (the skyline cut and the sky fit left
under the exiting buildings), at 3 s. The same message schedules the box run for the next session
without the owner present ("do not wait for me … just be careful with resources") and asks for more
work per session with Opus 5.5 subagents; DECISIONS 2026-09-26 (third session, last).

### 12.7 Round 2 on mismatch_6 at 3 s (2026-09-26, fourth session; page `benchmarks/runs/2026-09-26/layered_r2/index.html`; scores `scripts/research/scores/mismatch_6_r2{,_L,_drift}.json`)

Result: three 3-second clips stand beside round 1's `layered` and `flat` on the page, rendered from
one score that addresses the owner's three targets ("1) i see afterimage for tree crown, distinct
clouds, bottom buildings contours 2) keep 3s for now") at their source, plus two variants of the
clouds' colour and motion; ungraded as of 2026-09-26. Nothing in `transitions.py` changed. Round 1's
score renders md5 `64a54eee839d72d195b04d9dc6a06c1f` through the changed probe, so every new key
defaults to the old behaviour.

What round 1's frames showed, measured on the composite rather than by eye:
- Distinct clouds. At t = 0.5 the bright rings along every cloud edge are the cloud fringe (matte
  alpha under 0.9) left in A's sky residual at weight 0.21. After the sky window the sky layer
  equals B's fit plus residual to 0.28 levels in the sky interior, so nothing else leaks.
- Bottom buildings. The light band above the roofs and the light rectangle at the "far tower"
  polygon are the per-row day-sky fit extrapolated under the exiting buildings. The polygon
  (604–691 × 1177–1326 px on the canvas) encloses sky and cloud, not a tower: there is no luminance
  step at its top edge (L 66.7–67.3 across rows 1170–1210). The depth skyline sat 6–43 px above the
  roof edges; cloud edges have vertical steps under 6 L per px, roof edges 5–17.
- Tree crown. At t = 0.76 the leaf tips and the crown sit in the sky at their final position
  because B's residual excluded only the interior of the leaf-level matte; the dark branches at the
  crown's edge and the lit green leaves of an isolated branch (560–600 × 1180–1240 px) were outside it.

The mechanisms, all new score keys with the old behaviour as default:
- `region_of`: a wide soft matte (dilate 40 px, Gaussian 25 px) around a tight core, so the trees
  and the air-conditioning unit carry B's own sky between their leaves while they enter. The core
  (`trees_core`, not rendered) is the depth prior dilated 220 px, refined by `dark_or_chroma`
  (darker than the per-row sky, or (a*, b*) at least `chroma_d` = 10 from the per-row sky chroma,
  so lit leaves count), blobs under `min_blob` = 400 px dropped (stars have a leaf's chroma but not
  its area), and `components: bottom` decided after bridging blobs over `components_bridge` = 60 px
  (an isolated branch near the crown stays, the unit at the top does not).
- `snap_px` / `snap_up` / `snap_min`: the per-column depth skyline moves to the topmost vertical
  luminance step of at least 4.5 L per px between 8 px above and 45 px below the depth cut
  (1,104 of 1,146 columns snapped). `grow` now applies to every mask rule (2 px on the buildings).
- `minus` / `exclude` entries as `{"layer", "full": true, "dilate", "soft"}` remove a layer's
  full alpha from the backdrop's fit and residual; `minus_res` / `exclude_res` remove it from the
  residual only, so the fit still counts the sky seen between the leaves. The clouds' matte is
  opaque wherever any density exists (`opaque` 0.01) and erodes thin-first (`feather` 0.1); the sky
  under the clouds is the fit of the clear sky.
- `fill_sigma` = 60: the holes of each residual take a normalized convolution of the known
  residual at three scales (60, 180, 540 px) blended by confidence, computed at quarter resolution.
  `fit2d`: the backdrop's fit is a per-band weighted quadratic in x (linear when the band's samples
  span under half the width, constant under a quarter), so the lateral glow of B's sky is part of
  the fit and a hole filled from its rim carries no crown-shaped step.
- `recolor_mode: "L"` (the `_L` variant): the clouds darken in luminance only toward the night sky
  while they erode. `fit_under` was built (rows under A's skyline take B's fit) and is not used:
  the vacated band continues the interpolating sky instead.

Tried on the frames and rejected: a semi-transparent cloud matte (`opaque` 0.5; frame 1 differed
from A by 4.28 levels, 5.4 under the clouds, because the fringe no longer reproduced A); a hole fill
by a global quadratic in (x, y) (`fill_mode: poly2`; a dark crown-shaped hole and a dark top-left
corner); a fill that switches scales at a confidence threshold (an iso-distance contour inside the
hole); the wide region as the residual hole (a hole 600 px across shows its outline whatever fills
it); a 120-px depth prior with `components: bottom` (isolated branches dropped, leaves floated).

| clip | s | edge_ratio | feat_floor | laplace_floor | contrast_floor | dissolve_fit | motion_share | step first / last | prep / render s | md5 |
|---|---|---|---|---|---|---|---|---|---|---|
| `layered_r2` (clouds keep their colour) | 3 | 0.097 | 0.0 | 0.099 | 0.118 | 0.054 | 0.290 | 0.28 / 0.05 | 5.0 / 7.2 | `cddde79e…` |
| `layered_r2_L` (clouds darken in L) | 3 | 0.0965 | 0.0 | 0.099 | 0.118 | 0.211 | 0.317 | 0.28 / 0.05 | 3.4 / 8.0 | `f3efeeef…` |
| `layered_r2_drift` (clouds drift 4 % right, zoom 4 %) | 3 | 0.0934 | 0.0 | 0.099 | 0.118 | 0.050 | 0.311 | 0.28 / 0.05 | 3.4 / 7.5 | `7934592a…` |
| `layered` (round 1, reference) | 2 | 0.0105 | 0.055 | 0.241 | 0.197 | 0.226 | 0.290 | 0.05 / 0.05 | 3.7 / 5.8 | `64a54eee…` |

The 0.28-level first step is the 4–8 px band above the roofline and the cloud sliver where the
residual is excluded and the fill stands in for A's pixels; frame 0 is A exactly. `feat_floor` 0.0
measures the empty smooth sky between the clouds' exit (0.52) and the trees' entry (0.55); the goal
numbers do not see an orchestration (§12.2). Windows: clouds 0.05–0.52, sky 0–0.70, buildings
0.30–0.75, stars 0.45–0.90 (outside the wide regions; the stars near the trees arrive with the
trees), trees 0.55–0.95, AC unit 0.60–0.97, `ease` on every layer.

Defects still visible by my eye (not evidence; the owner's boxes decide): the last cloud cores
vanish as bright blobs on a dusk sky around t = 0.45–0.52 (the `_L` variant shows them dark grey);
the sky under the right-hand trees is filled from far away and reads darker at the bottom-right
corner before the trees arrive; the AC unit's region enters as a hard-edged dark wedge. Next: the
owner's three boxes and a note per clip; the tool shape of §12.4 is unchanged and waits for that grade.

mismatch_4 round 2 (the same session, Track D of the handover; the same page, section mismatch_4,
beside `flat` and `anchors_alpha`): the sun disc (6 px of margin) moves to the second sun's place by
the Gaussian map and a B sun layer materialises by luma once it arrives (0.68–0.80); A's skyline
band with its masts (`band_dark` with the bottom capped at 0.56 of the height, plus `dark_in`
silhouettes relative to the local sky brightness over 120 px) exits down as a whole behind the
water (0.15–0.70); B's band rises behind it (0.30–0.85); the water backdrop's top edge slides from
A's shore line to B's (`slide_between`); the sky backdrop (0–0.85, `fit2d`, `fill_sigma` 60) keeps
the suns' interiors out of both residuals and the bands out of the residuals only; no cloud layer
and no noise-ordered patch. Rejected on the frames: a cloud layer by L density (on a sunset sky the
rule takes the sun's glow for cloud; the fit under it fell to L 24 at the sun and a dark disc showed
at the target), suns carrying 40–80 px of glow behind full-alpha exclusions (a rounded patch of
filled residual around the sun), an absolute luminance threshold for the silhouettes (B's cranes
L 6–25, its dim sky 18–30). Numbers: steps 0.12 / 0.10 levels (round 1: 0.11 / 0.23), `edge_ratio`
0.172, feat_floor 0.155, laplace_floor 0.636, contrast_floor 0.844, dissolve_fit 0.175,
motion_share 0.078, prep 4.3 s, render 9.6 s at 1920×1092, md5 `b7700b4c…` on two runs. Defects by my
eye: a faint disc-shaped patch at the second sun's place from t ≈ 0.4 until the moved sun arrives;
the sky behind A's left buildings is a flat extrapolation until B's sky takes over; A's water
reflections stay as stripes at the old waterline while it slides; a horizontal cut at the far-left
structure's top as B's band rises. Ungraded as of 2026-09-26.

### 12.8 Owner picks on round 2 (2026-09-26, 20:49 UTC; `benchmarks/runs/2026-09-26/layered_r2/layered_picks.json`)

Verbatim. mismatch_6, closer `layered` (round 1); boxes: `flat` = nothing invented; `layered`,
`layered_r2`, `layered_r2_L`, `layered_r2_drift` = one picture + content transforms + nothing
invented: "I have picked layered ( although it is still very raw)  just to highlight that this is at
least remotely looks like right direction ( at least for this pair) . Removing individual objects
still is junky, like they are some cheap decorations in 2d scene with hard edges  , but at least you
attempt to decompose the scene now, also i like how stars appear. weakest part still are clouds that
dissolve in a very raw  and naive luma manner , i would expect them to dissolve more like real clouds
would do in nature ( but again , NOT crossfade) . Also still all parts of the image that move , have
hard distint edges that break immersion and move in very linear manner ". mismatch_4, closer
`layered_r2`; boxes: `flat`, `anchors_alpha` = nothing invented; `layered_r2` = transforms + nothing
invented: "I have picked layered_r2 ( although it is still very raw)  just to highlight that this is
at least remotely looks like right direction ( at least for this pair) . moving individual objects
still are junky, like they are some cheap decorations in 2d scene with hard edges  , but at least you
attempt to decompose the scene now and attempt to make transtions between some parts, like skyline
in this case and moving sun between the frames.  Clouds and sun reflections on water are  still
crossfaded and we still have some rough edges and afterimages but it all looks more dynamic now. ".
On §12.7's defect list: "pretty much accurate".

What follows, pair by pair: mismatch_6 carries the first "one picture" ticks on record (none of the
22 clips on the anchors page, none of the 6 on the round-1 page); the owner picks round 1's `layered`
as closer while ticking the four clips alike, so round 2's fixes removed the named afterimages
without changing the grade, and the note names what stands between "raw" and done: the cloud erosion
(a luma threshold; the wish is a cloud that thins the way a cloud does, and not a crossfade), the hard
edge on every moving layer, the linear motion; the stars are liked. mismatch_4 gains "transforms"
(round 1 had no box) and not "one picture"; the sun move and the skyline are the attempts that work;
the clouds and the sun's water reflection are named as crossfades. The §12.4 gate is met on its
letter; the build of `pair --score FILE` against a round 3 is the owner's decision. Round 3 targets,
in the owner's order: (1) a cloud dissolve that behaves like a cloud — erode from the cloud's edges
inward along its own density gradient (a distance-from-edge order rather than a luma order), thin the
whole matte's alpha with the erosion so a cloud fades where it is already thin, and let the erosion
front carry a soft, turbulent boundary (a noise-displaced front, not a noise-ordered patch); (2) soft
edges on every moving layer — a matte feather that follows the photo's own edge (guided by the
gradient) plus a short motion blur along the travel direction (proportional to the per-frame
displacement); (3) motion that is not linear — an ease that starts and ends slower than the cosine
(a smootherstep or a physical decay) and a small acceleration profile per layer.

### 12.9 Round 3 on mismatch_6 and mismatch_4 (2026-09-27; page `benchmarks/runs/2026-09-27/layered_r3/index.html`; scores `scripts/research/scores/mismatch_6_r3{_clouds,_soft,}.json`, `mismatch_4_r3.json`)

Result: three 3-second clips on mismatch_6 (one per fault the owner named on round 2, one with both
fixes) and one on mismatch_4 stand beside the round-1 and round-2 references; every clip is
byte-identical on two runs; the round-2 clips render md5 `cddde79e…` (mismatch_6) and `b7700b4c…`
(mismatch_4) through the changed probe, so every new key defaults to the old behaviour. Ungraded as
of 2026-09-27. Nothing in `transitions.py` changed. The probe now writes a `measure` block per clip
and the page prints it under each clip (§12.9.1).

12.9.1 What round 2's frames showed, measured on the composite:
- The cloud erosion (density plus noise order, feather 0.1): at a quarter and at half of the clouds'
  window 12–14 % of the cloud support is semi-transparent, in a band 9–10 px wide along the front, so
  the front is a hard cut in the shape of the 40-px noise. From frame 1 the thin cloud band at the
  right shows dark patches: the density map has holes under 0.01 there and the clear-sky fill shows
  through them (most of the 0.28-level first step).
- The moving layers: the cosine ease peaks at 1.59–1.62 × the mean speed and spends 27–29 % of the
  moving frames within 10 % of the peak (buildings 17.6 px per frame, trees 29.2, AC unit 37.0 at
  30 fps, 3 s). The trees' region carries B's sky from its source rows over the rows it slides across:
  the mean luminance mismatch between the carried sky and the sky under it is 3.97 L at the middle of
  the window and 2.15 L at three quarters. The step across a moving layer's boundary on the composite
  is 0.9 L (trees) and 0.7 L (AC unit) at the middle of their windows; the buildings' 30 L is the
  roofline against the sky, the photo's own edge.

12.9.2 The mechanisms (new score keys, all default-off; `scripts/research/layered_probe.py`):
1. `order: "edge"` on a dissolve: the front runs in pixels from the edge of the cloud's dense part
   (density at least `edge_thr` 0.1) inward along the distance transform, 2.5 × faster through thin
   parts (`speed_density` 0.6), with a 30-px soft band (`front_soft_px`), a 90-px thinning ramp ahead
   of it (`front_wide_px`, down to half the alpha at the cut) and a front displaced by two octaves of
   noise (±9 px at 16 and 48 px). Small clouds go first and the big cloud's core (227 px deep) last.
   The matte fills its enclosed holes up to 400 px (`fill_holes_px`) and grows 8 px so it covers
   everything the backdrop excludes (the sky's `minus` of the clouds is now dilate 0, soft 2): the
   first step falls from 0.28 to 0.03 levels. Tried on the frames and rejected: a front normalized to
   the largest inward distance with a 0.35 band (42 % of the support semi-transparent at a quarter of
   the window in a 90-px band: every cloud washed at once); a 10-px band with ±15 px of turbulence (a
   field of round holes); a morphological closing of the matte (it bridged the sky between the clouds,
   80 % of the canvas, and the backdrop's fit lost every pixel).
2. `shutter` on a moving layer: a line kernel along the velocity, shutter × the per-frame
   displacement long, applied to the pixels and the matte after the warp (0 at rest, so the endpoint
   frames stay exact); 0.5 is a 180-degree shutter. `carry_fit: "sky"`: the layer's Lab gains the
   backdrop's fit at the destination rows minus the fit at its source rows (the trees' carried-sky
   mismatch 3.97 → 1.95 L). `edge_feather` (a feather that follows the photo's gradient) was built and
   tested on the buildings' skyline: the first step stayed 0.28 and laplace_floor moved 0.099 → 0.077;
   not used, because the roofline is the photo's own edge and the regions are already soft.
3. Curves `smootherstep` (zero speed and zero acceleration at both ends; peak 1.87–1.89 × the mean,
   plateau 22–24 %), `fall` (u², a constant acceleration from rest) and `settle` (1 − (1 − u)³); round
   3 uses smootherstep on every moving layer, the clouds and the sky.

| clip | s | edge_ratio | feat / laplace / contrast / dissolve_fit / motion | step first / last | measured | prep / render s | md5 |
|---|---|---|---|---|---|---|---|
| mismatch_6 `layered_r3_clouds` (the clouds only) | 3 | 0.0156 | 0.0 / 0.0999 / 0.0916 / 0.0763 / 0.3357 | 0.03 / 0.05 | semi-transparent share 0.38 / 0.13 / 0.01, front width 89 / 54 / 40 px at 1/4, 1/2, 3/4 | 5.4 / 7.6 | `748b68ed…` |
| mismatch_6 `layered_r3_soft` (the moving layers only) | 3 | 0.1056 | 0.0 / 0.0814 / 0.1211 / 0.057 / 0.2389 | 0.28 / 0.05 | peaks 21.0 / 34.8 / 44.1 px per frame (buildings / trees / AC), 1.87–1.89 × mean, plateau 22–24 %; carried-sky mismatch 1.95 / 1.75 L | 6.6 / 18.8 | `ecbbcb61…` |
| mismatch_6 `layered_r3` (both) | 3 | 0.0169 | 0.0 / 0.0818 / 0.0875 / 0.0807 / 0.2934 | 0.03 / 0.05 | both of the above | 5.2 / 13.9 | `f2c3c02f…` |
| mismatch_4 `layered_r3` (motion only: `shutter` 0.5 and smootherstep on the two skylines and the sun) | 3 | 0.1745 | 0.1909 / 0.6399 / 0.8183 / 0.175 / 0.0721 | 0.12 / 0.10 | peaks 38.7 / 30.8 / 9.0 px per frame (band / band_b / sun), plateau 22–23 % (round 2: 32.4 / 25.8 / 7.6, plateau 28 %) | 4.7 / 17.2 | `a9f1e3d6…` |

The shutter blur costs 8 s of render on mismatch_6 (18.8 s against 10.6 s) and 6 s on mismatch_4.

12.9.3 mismatch_4's clouds, tried and rejected. The owner named the clouds and the sun's water
reflection as crossfades. A layer for B's thin bright clouds was cut by a new `clouds` rule variant
(`channel: "L_hp"`: a high-pass of L at 40 px with a 5-L noise floor, the sun's glow excluded within
110 px of its disc; B's sky measured: high-pass median −0.2 L, 99th percentile 16.4 L) and rendered
four ways: (a) `order: "edge"` — the streaks are 3.3 px deep at most, so the 70-px ramp makes the
whole layer semi-transparent at half its window (share 1.0), a plain fade; (b) density order with a
0.5 feather — the residual hole around every streak draws its own outline (frame 67), last step 0.42,
`edge_ratio` 0.67; (c) a softer matte (floor 2 L, blur 4) — last step 0.75, `edge_ratio` 1.19;
(d) the dark cloud bank as a second layer — its 200,000-px exclusion at the frame's top leaves a fill
with no lateral support, a grey sky at t ≈ 0.45. The rule stays in the probe; the clouds and the
reflection stay crossfades and are the next probe's targets: a streak layer whose matte boundary lies
in smooth sky and condenses along the streak, and a reflection layer that follows the sun.

Defects by my eye (not evidence; the owner's boxes decide): the eroding clouds' last remnants at
t ≈ 0.28–0.36 read as translucent cut-outs with soft edges; the motion blur streaks the trees' leaves at
their peak speed (17 px of blur); the right-hand tree crown at the bottom right of B enters as a dark
mass with a soft boundary; on mismatch_4 the moved sun leaves a dark disc at its origin (the excluded
residual; round 2 named the disc at the destination). Next: the owner's boxes and notes; the tool
shape of §12.4 waits.

### 12.10 Round 4: a layer transforms into its counterpart; an automatic score on untuned pairs (2026-09-27 evening; page `benchmarks/runs/2026-09-27/layered_r4/index.html`; scores `mismatch_4_r4.json`, `mismatch_6_r4.json`, `scores/auto/{mismatch_1,mismatch_5,mismatch_3}.json`)

Result: five 3-second clips, every one byte-identical on two runs, in which no layer slides in or out
of the frame: on mismatch_4 the first skyline transforms into the second, on mismatch_6 the row of
buildings transforms into the tree line, and on three pairs that were never tuned the same mechanisms
run from a score built by fixed rules. The nine md5s of rounds 1–3 are unchanged through the changed
probe. Ungraded as of 2026-09-27. Nothing in `transitions.py` changed.

12.10.1 The owner's picks on round 3 (2026-09-27 15:36 UTC; `benchmarks/runs/2026-09-27/layered_r3/layered_picks.json`;
verbatim). mismatch_6, closer "none"; `layered_r2`, `layered_r3`, `layered_r3_clouds`, `layered_r3_soft`
one picture + transforms + nothing invented, `layered` (round 1) transforms + nothing invented:
"layered_r3_soft is closer then previous ones , still clouds dissolve with cheap linear 2d effect and
not as real clouds would into the dark. In other regards, not better or worse than previous layered
approaches, sliding of different elemetns in and out of frame is too linear and naive , again as
decorations in 2d scene ". mismatch_4, closer "none"; `layered_r2` and `layered_r3` transforms only:
"not better or worse than previous layered approaches, sliding of different elemetns in and out of
frame is too linear and naive , again as decorations in 2d scene . ALso here it is especially important
as buildings skyline does not transform into final one but rather first frame skyline slides out and
final frame skyline slides in , very weird and junky. Also clouds and water are still simply
crossfaded. Only Sun movement is cool between frames. ". Reading: round 3 refined the finish of an
action (edge, blur, ease) and the grade did not move; the fault is the action. The one action praised
twice is the sun's: an element of A carried to its counterpart in B.

12.10.2 The mechanisms (new score keys, all default-off; `scripts/research/layered_probe.py`):
1. Action `morph_to` (`to`: a layer of B). An entropic optimal-transport plan between the two mattes
   is solved on a coarse grid (`ot_grid` 64 cells on the long side; regularisation `ot_eps` 0.04 of
   the long side, halved from 8 × that; log-domain Sinkhorn in numpy, no new dependency, no random
   start); its barycentric projection gives a displacement field A → B and one B → A, spread over the
   canvas by a normalized convolution. At window progress u the layer of A has moved along p × the
   field (p = the curve of u) and the layer of B has come back along (1 − p) × the reverse field; the
   two are mixed by q, which runs only inside `mix_window` (0.3–0.7 of the window), so the first part
   is A's content reshaping and the last part B's content settling. Both layers are given the same Lab
   statistics (A's and B's blended over `colour_window`, in clip time), so the mix changes structure
   and not colour, and a day-lit layer can darken with the sky before its structure changes. In the
   middle of the mix the matte is the union of the two warped mattes. `ot_mass` alpha | bright | dark
   chooses what is transported (the matte, or the layer's bright or dark features).
2. A backdrop's `flow`: its two residual textures move while they mix. `from: "layers"` takes the
   scene's one flow, a normalized convolution (σ 0.12 of the long side) of the matched layers' own
   motions (a `morph_to` field inside its matte, a `move_to` map at its blob; `layers` names which),
   falling to zero far from them; mirrored at the canvas border.
3. `advect` (a displacement along a divergence-free noise field that grows with the progress),
   `recolor_window` (a colour path with its own window), `extend_bottom_px` and `bottom_fit` on a band
   (the matte continues behind the water; the waterline is a polynomial through the columns within
   12 px of the running fit).
4. `--auto PAIR`: a score from fixed rules (`auto_score`). Both photos have a sky (the depth skyline
   leaves 5–90 % of the canvas below it): `ground` transforms into `ground_b` over a sky backdrop with
   the scene's flow, and a sun moves to a sun when both skies hold a blob above L 92 of 0.03–3 % of
   the canvas. Otherwise the whole frame transforms into the whole frame (transport between bright
   features) under a near layer cut at each photo's median disparity. The score is written to
   `scores/auto/<pair>.json`: the file an operator then edits.

| clip | edge_ratio | feat / laplace / contrast / dissolve_fit / motion | step first / last | measured | prep / render s | md5 |
|---|---|---|---|---|---|---|
| mismatch_4 `layered_r4` | 0.0925 | 0.2926 / 0.6636 / 0.7654 / 0.1669 / 0.1447 | 0.10 / 0.10 | skyline transport mean 245.2 px, 95th percentile 322.7 px (9.71 px per frame at the peak); sky texture flow mean 57.2 px (max 145.7), water 103.8 px (max 124.3); sun 235.8 px as before | 6.1 / 14.2 | `e7b331de…` |
| mismatch_6 `layered_r4` | 0.0318 | 0.0 / 0.1204 / 0.1214 / 0.3665 / 0.0948 | 0.06 / 0.05 | buildings → trees transport mean 77.9 px, 95th percentile 164.0 px; the buildings' mean L 43.2 → 32.0 (t 0.20) → 18.4 (0.34) → 9.2 (0.47); clouds as round 3 plus 50 px of advection and the L path | 7.3 / 11.9 | `1aef9fa5…` |
| mismatch_1 `auto_r4` (sky + ground; ground shares 0.193 / 0.398; no sun pair) | 0.0308 | 0.0508 / 0.4696 / 0.7811 / 0.1776 / 0.1795 | 0.07 / 0.04 | ground transport mean 187.3 px; sky flow mean 73.4 px | 4.6 / 9.7 | `80dc31a9…` |
| mismatch_5 `auto_r4` (whole frame + near layer; B has no ground under the rule) | 0.0 | 0.0 / 0.7627 / 0.9594 / 0.1894 / 0.2212 | 0.0 / 0.0 | whole-frame transport mean 154.4 px; near layer 438.9 px (95th percentile 740.5) | 15.3 / 9.5 | `08bb31de…` |
| mismatch_3 `auto_r4` (whole frame + near layer; an interior) | 0.0 | 0.054 / 0.5339 / 0.7924 / 0.1863 / 0.1601 | 0.0 / 0.0 | whole-frame transport mean 121.2 px; near layer 143.2 px (95th percentile 596.8) | 24.7 / 12.3 | `52c4e57a…` |

References on the page: mismatch_6 `layered_r3_soft`, mismatch_4 `layered_r3`, and `flat` (the shipped
pan-and-zoom) for the three automatic pairs.

12.10.3 Tried on the frames and changed (each visible in a scratch render of the same evening):
a matte mixed as (1 − q) a + q b left the skyline half transparent wherever the two warped shapes did
not overlap (the union in mid-mix replaced it); a free transport between the bright features of the
two sky textures moved them 200.6 px on average and 715.3 px at most and drew curtain-shaped smears
(the flow from the matched layers replaced it; the free transport stays an option); the band's bottom
line had notches under the bright reflection through which the water layer covered blocks of the
skyline, the light blocks of rounds 2–3 (the fitted waterline removed them); a colour window counted
inside the layer's own window left day-lit buildings under a night sky (it counts in clip time now).

12.10.4 What the automatic clips show, by my eye and not as evidence. mismatch_1 reads as one scene
changing. mismatch_5's whole-frame transport stretches the sun's texture into a grain pattern mid-way
and shows both photos at t ≈ 0.45–0.56. mismatch_3 is a warped double exposure of two groups of people
mid-way: with no layer for a person the mechanism has nothing to match, and the depth cut at the
median splits people. Both are what the mechanisms give unattended; the layers a scene needs are
§12.11's question. Other defects: the moved sun's dark disc at its origin (round 2's); the mismatch_6
tree crown at the left is stretched while it settles (t ≈ 0.70–0.76); the air-conditioning unit
appears as a dark shape growing from its core.

### 12.11 The two mask routes side by side (2026-09-27 evening; page `benchmarks/runs/2026-09-27/masks/index.html`; `scripts/research/mask_routes.py`; an Opus 5.5 subagent, its licence claim and two overlays re-checked on the main thread)

Result: on 18 of the owner's photos neither route is enough alone. One fixed rule set on the depth
model and the photo (no tuning) finds a "sky" on 18 of 18 photos, interiors included, because the
disparity is rescaled per photo and the farthest pixels always pass; its colour cloud test covers the
whole sunset sky of mismatch_4 and the night sky of mismatch_6. A panoptic model names regions and
returns nothing for an absent one (sky on 14 of 18 photos with the COCO model, 15 with ADE20K), but it
has no name for sun, cloud or star, no depth order, and it misnames what is unlike its training photos
(the river of mismatch_4 is "building" for the COCO model; the air-conditioning unit is "airplane" or
"bridge"). Where a real sky exists the two agree: IoU 0.96–1.00 on mismatch_1, 4, 6 and 7. Untuned,
the models match the hand-tuned mismatch_6 buildings at IoU 0.94–0.95 and trees at 0.70–0.76, masks
that took two sessions of per-pair rules.

| | rules (the depth model already offline + photometric tests) | panoptic model (Mask2Former Swin-Tiny) |
|---|---|---|
| knows | which pixels are far, bright, blue, dark | a name per region from 133 (COCO panoptic) or 150 (ADE20K semantic) labels |
| does not know | what a thing is; whether a photo has a sky at all | depth order; sun, cloud, star; things unlike its training photos |
| cost | 0 new bytes; depth 0.28 s + rules 0.36 s per photo (medians) | 190 MB of weights per model behind `warmup` + a manifest; 1.19 s (COCO) or 0.62 s (ADE20K) per photo on the CPU; peak RSS 3.8 GiB |
| licence | none new | the model cards say "license: other"; the upstream model zoo: "All models available for download through this document are licensed under the Creative Commons Attribution-NonCommercial 4.0 International License" [VERIFIED via github.com/facebookresearch/Mask2Former MODEL_ZOO.md, 2026-09-27]; the code is MIT |
| loads in this venv | yes | not by the stock path: `transformers` 5.17 needs scipy (the training loss) and torchvision (the image processor); the probe stubs the loss class and does the preprocessing and the segment assembly itself, with nothing installed |
| offline | yes (harness 48–51) | a second run with `HF_HUB_OFFLINE=1` reproduced 36 of 36 label maps byte for byte; `transformers` fetched a second 190 MB file for the ADE20K repo in the background, so a warmup must pin the revision and the file list |

Layer matching by name (the input of `morph_to`): sky is in both photos of 6 of 7 mismatch pairs,
building in both of mismatch_1, 4 and 7, tree in both of mismatch_1 and 6, person in both of mismatch_2
and 3; water on mismatch_4 matches only across names ("water" in the start photo, "sea" in the
finish), so pairing needs synonym groups. The options put to the owner: rules only; the panoptic
model behind a warmup; or both (the model for WHAT a region is and whether it exists, the depth model
for the ORDER, the photometric rules for the fine edge and for sun, cloud and star). Gaps: no Swin-Tiny
ADE20K panoptic checkpoint exists (the ADE20K tiles are semantic, one region per label); the IoUs
compare the routes with each other, not with a correct mask; the licence of the Hugging Face copies is
inferred from the upstream zoo. Two permissively licensed alternatives exist and were not run
(UNVERIFIED on these photos): `shi-labs/oneformer_ade20k_swin_tiny` (card licence "mit"; semantic,
instance and panoptic segmentation on ADE20K) and `facebook/detr-resnet-50-panoptic` (card licence
"apache-2.0"; COCO panoptic) [VERIFIED via their Hugging Face model cards, 2026-09-27]. OneFormer
Swin-Tiny is the first to measure if the owner chooses a model: it is the ADE20K panoptic model that
Mask2Former lacks at this size. Owner ruling 2026-09-27 (night; verbatim in DECISIONS): "Licensing for
ANY model is not a problem , this whole project is pure personal non-profit research" — a licence is
recorded as a fact and never filters or ranks a model; choose by measured accuracy, size and fit.

### 12.12 Owner picks on round 4 and the directions that follow (2026-09-27, 19:37 UTC; `benchmarks/runs/2026-09-27/layered_r4/layered_picks_.json`; verbatim in DECISIONS 2026-09-27 late evening)

Result: `layered_r4` is picked as closer on mismatch_6 and mismatch_4 and `auto_r4` on mismatch_1;
mismatch_5 and mismatch_3 get no pick and their automatic clips get all three boxes, the first "one
picture" ticks on those pairs. The owner on the mechanism: "at least content stopped sliding back and
forth and buildings this time transtitoned to tree nicely"; "skyline now tries to morph into new one
and moves correctly"; on the automatic clips "quite distorted with weird 3d wraps going on, but … at
least it is not crossfading".

| pair | closer | boxes (one picture / transforms / nothing invented) |
|---|---|---|
| mismatch_6 | `layered_r4` | `layered_r3_soft` yes/yes/yes; `layered_r4` yes/yes/yes |
| mismatch_4 | `layered_r4` | `layered_r3` no/yes/yes; `layered_r4` no/yes/yes |
| mismatch_1 | `auto_r4` | `flat` no/yes/yes; `auto_r4` no/yes/yes |
| mismatch_5 | none | `flat` no/no/yes; `auto_r4` yes/yes/yes |
| mismatch_3 | none | `flat` no/no/yes; `auto_r4` yes/yes/yes |

Round-5 targets, in the owner's words: mismatch_6's clouds "dissolved with quite a solid internal
borders , i wish they just  non-uniformly morphed into night sky parts"; mismatch_4 "at the very end
it still seems some boundary where it crossfades to final B shot( both buildings and river )". The
direction for matching, each given as one scene's example with "do not overfit": an element
transforms into its closest counterpart (a building into a building, a cloud into a cloud
independently, people into people, the sun into the galaxy's centre, the bridge into the meteor
streak), decided from depth, labels and rules; a wall or a ceiling transforms and never moves as a
"cheap 2d cutout". The layer source (§12.11): the owner wants "as much info you can get about frame
as possible", judged the ADE20K labels more accurate than COCO's, and asks for better models. The
keyframes: the round-4 composite of mismatch_4 is "something in the middle (but still like
crossfaded)"; kf_13's night tint on A's buildings "looks really cool" (the owner first wrote kf_09 and
corrected it to kf_13 the same evening: klein's clean-up of the round-4 composite at 0.62, not the prompt
on photo A). FLUX.2 [pro] through the API
is declined; a local quant of FLUX.2 [dev] was asked for and withdrawn the same night ("for now
probably makes no sense … both becauase of size and quants, i don't want degraded Q 4bit  anyways");
FLUX.2 klein 9B at 8-bit is tried instead. Round 5 comes before the tool build.

### 12.13 Round 5: the frames beside the endpoints equal the photos, the clouds transform, the automatic score matches elements (2026-09-28; page `benchmarks/runs/2026-09-28/layered_r5/index.html`; scores `mismatch_4_r5{,_stagger}.json`, `mismatch_6_r5{,_flow}.json`, `scores/auto/<pair>_v2.json`)

Result: twelve new 3-second clips on seven pairs, each byte-identical on three runs, and the fourteen
md5s of rounds 1–4 unchanged through the changed probe. Three faults were measured on round 4 before
anything changed, and each is gone in round 5 by its own number (12.13.3). Ungraded as of 2026-09-28.
Nothing in `transitions.py` changed. The measures are in `scripts/research/layered_diag.py`.

12.13.1 Measured on round 4 first.
1. mismatch_4, the owner's "at the very end it still seems some boundary where it crossfades to final
   B shot( both buildings and river )". The clip holds still from t = 0.854, 14 of its 90 frames. In
   those frames the composite stands 0.151 levels from B on average and 84 at most, and 1.096 % of the
   canvas is more than 4 levels off; 86 % of those pixels lie within 12 px of the skyline matte's
   contour, and the water's soft edge stands 9.35 levels off. All of it vanishes in the last frame.
   Frame 1 stands 0.183 levels from A, 140 at most. Cause: under a layer's soft edge, and in the 4 px
   by which the exclusion is dilated, the backdrop shows its hole fill, which stands 3.8 L (B) and
   5.0 L (A) off the photo in the first 2 px outside the matte. That this outline is the boundary the
   owner saw is [INFERRED]: it is the one defect measured at the end of the clip, and it lies on the
   buildings and on the waterline.
2. mismatch_6, the owner's "clouds dissolved with quite a solid internal borders". The clouds'
   contrast against the sky under them changes sign: +17.41 L at t = 0.01, +12.82 at 0.11, −1.18 at
   0.21, −9.79 at 0.32, −8.31 at 0.42. From t = 0.2 the clouds are darker than the sky around them,
   behind an erosion front.
3. `warp_along` scales the rows by the horizontal factor and resamples the picture at any progress
   above zero (found while measuring the two faults above). On a canvas whose width is not a multiple of 4 the rows are stretched
   (2.7 px at the bottom of mismatch_6's 1146 × 1524). In mismatch_6 `layered_r4` the step from frame
   81 to 82, where the buildings' window ends and the warp is switched off, is 1.422 levels (4.418 in
   the bottom 30 % of the rows, 15.03 % of them over 8 levels); the steps beside it are 0.03–0.12.
   Backlog T19.

One number decided nothing. In the last moving stretch of mismatch_4 (t 0.75–0.82) the frame step
fits a fade toward B with R² 0.92 on the skyline. A fade and a motion that decays toward B are the
same to first order once the remaining displacement is under 1 px, so that number cannot tell them
apart.

12.13.2 The mechanisms (new score keys, all default-off; `scripts/research/layered_probe.py`).
1. At the endpoints: a backdrop's `settle` keeps the photo's own residual under a layer's fringe
   while that layer rests, and the hole fill while it is under way (per hole, timed by the layer that
   owns it); `fill_scales` starts the fill at 6 px, so it meets the photo at the hole's rim; `exact`
   warps give a zero displacement back bit for bit.
2. A half-transparent layer: `unmix` gives a layer its own colour, F = (I − (1 − α) Bg) / α against
   the backdrop's filled estimate, with α raised to the least opacity a colour inside the gamut can
   explain; the backdrop keeps its fill under such a layer.
3. A layer that ends as a part of the backdrop: `morph_to` a matte of `parts` (the second photo's
   own structure, a band-pass of L) with `to_backdrop` (the target's pixels are the backdrop's end
   state), `colour_rel` (the layer's Lab statistics follow the backdrop's current state, so its
   contrast decays and never changes sign) and a fade-out after the mix.
4. Where and when a layer moves: `stagger` gives every place its own start (a smooth noise field
   carried along the transport); `ot_local` re-weights the target's mass to the source's at a scale,
   `ot_floor` leaves a share in place, `ot_border` pins the field at the canvas border, `ot_rigid`
   pulls the field toward its affine part.
5. `--auto2 PAIR` (`auto_score2`): the elements of both photos come from the layer source (§12.14).
   An element of A is matched to the element of B with the lowest cost: 0 for the same label, 0.15
   for the same group, 0.5 for a neighbour group, plus the centroid distance over the diagonal, plus
   0.25 × |ln of the area ratio|, plus 0.5 × the difference of median disparity; no match above a
   cost of 1.1 or farther than 0.35 of the diagonal; a leftover joins the matched group of its kind.
   Each matched group is one `morph_to` layer with its own field and its own start, the nearest
   first. The rest of the frame follows the flow interpolated from those layers.

Further rules of the automatic score, each from a fault seen on a render of the same night: a group
that keeps its shape (building, wall, furniture and nine more) moves with `ot_rigid` 0.6 and no
stagger; a ground whose counterpart holds under 0.4 of its area transforms into parts of the second
photo's sky where it stands; an element of B with no counterpart appears in place; when the labels
give no pair of lights, a compact blob above L 92 in each sky is the sun (it must fill 0.4 of its
enclosing circle: the suns of mismatch_4 fill 0.62 and 0.46, the bright clouds of mismatch_7 0.28 and
0.06).

12.13.3 Numbers.

| measure | round 4 | round 5 |
|---|---|---|
| mismatch_4, held frames against B: mean / largest / share over 4 levels | 0.151 / 84 / 1.096 % | 0.004 / 9 / 0.019 % |
| mismatch_4, frame 1 against A | 0.183 / 140 / 1.030 % | 0.000 / 1 / 0.000 % |
| mismatch_4, ridge of L along the skyline matte's contour, held frames (B itself: 0.077 L, 0.48 % over 2 L) | 0.518 L, 8.56 % | 0.077 L, 0.48 % |
| the same at frame 1 (A itself: 0.070 L, 0.64 %) | 1.155 L, 19.59 % | 0.070 L, 0.64 % |
| mismatch_6, held frames against B | 0.108 / 74 / 0.273 % | 0.020 / 1 / 0.000 % |
| mismatch_6, frame 1 against A | 0.119 / 86 / 0.269 % | 0.070 / 34 / 0.022 % |
| mismatch_6, clouds' contrast against the sky at t 0.01 / 0.11 / 0.21 / 0.32 / 0.42 / 0.52 | +17.41 / +12.82 / −1.18 / −9.79 / −8.31 / −0.18 | +13.47 / +12.85 / +10.58 / +6.44 / +2.80 / +0.32 |
| mismatch_6, the step from frame 81 to 82 (bottom 30 % of rows) | 1.422 (4.418) | 0.000 (0.000) |

| clip | edge_ratio | feat / laplace / contrast / dissolve_fit / motion | step first / last | measured | prep / render s | md5 |
|---|---|---|---|---|---|---|
| mismatch_6 `layered_r5` | 0.0229 | 0.0 / 0.1157 / 0.1667 / 0.4472 / 0.0893 | 0.04 / 0.01 | clouds → night-sky parts: transport mean 16.1 px, 95th percentile 36.9 px | 18.2 / 15.3 | `88ac8d96…` |
| mismatch_6 `layered_r5_flow` | 0.0229 | 0.0 / 0.1156 / 0.1636 / 0.4416 / 0.0928 | 0.04 / 0.01 | the same with larger parts: mean 40.4 px, 95th percentile 93.6 px | 17.5 / 15.3 | `fceb36e8…` |
| mismatch_6 `auto_r5` | 0.0086 | 0.1919 / 0.2377 / 0.3729 / 0.4515 / −0.0295 | 0.01 / 0.01 | building + tree → tree (cost 0.724); `building#2` of B appears in place | 2.4 / 17.1 | `a2fa0f41…` |
| mismatch_4 `layered_r5` | 0.0012 | 0.2863 / 0.6639 / 0.7654 / 0.1682 / 0.1459 | 0.0 / 0.0 | the round-4 score with `settle`, `fill_scales` and `exact` | 5.6 / 14.0 | `ff4c3cde…` |
| mismatch_4 `layered_r5_stagger` | 0.0012 | 0.283 / 0.7269 / 0.7665 / 0.1668 / 0.1215 | 0.0 / 0.0 | the same, every place with its own start | 4.2 / 18.7 | `af95007c…` |
| mismatch_4 `auto_r5` | 0.0025 | 0.2782 / 0.7669 / 0.8245 / 0.0607 / 0.0941 | 0.0 / 0.0 | three groups (building, earth, water); the sun by the photometric rule | 6.0 / 33.1 | `c4c4c976…` |
| mismatch_1 `auto_r5` | 0.013 | 0.2773 / 0.7139 / 0.9206 / 0.0402 / 0.2043 | 0.03 / 0.01 | building → building + tree + plant + wall (0.330); cloud → cloud, mean 365.7 px | 5.0 / 29.5 | `c817dc61…` |
| mismatch_5 `auto_r5` | 0.0116 | 0.0 / 0.6058 / 0.6659 / 0.136 / 0.116 | 0.01 / 0.0 | sun → the galaxy's centre (both labelled "sun"), mean 405.1 px; the ground transforms into parts of the sky | 8.6 / 18.5 | `66c665f2…` |
| mismatch_3 `auto_r5` | 0.0 | 0.108 / 0.5912 / 0.824 / 0.1264 / 0.2291 | 0.0 / 0.0 | 14 groups, 10 layers: 12 people of A into 4 of B in four groups, benches into chairs, a door and a wall into walls | 20.9 / 77.1 | `73d97640…` |
| mismatch_2 `auto_r5` | 0.0 | 0.2385 / 0.2745 / 0.7534 / 0.2699 / 0.2687 | 0.0 / 0.0 | one person into five, two trees into plants and a building | 23.8 / 9.7 | `3daaead5…` |
| mismatch_7 `auto_r5` | 0.0118 | 0.2016 / 0.6769 / 0.7946 / 0.0635 / 0.1892 | 0.02 / 0.04 | two building groups (0.705, 0.701); cloud → clouds, mean 251.8 px | 7.9 / 35.7 | `edc192fc…` |

Against round 4's automatic clips on the same pairs: `feat_floor` 0.0508 → 0.2773 on mismatch_1 and
0.054 → 0.108 on mismatch_3; `laplace_floor` 0.4696 → 0.7139 and 0.5339 → 0.5912; on mismatch_5
`laplace_floor` falls 0.7627 → 0.6058 and `contrast_floor` 0.9594 → 0.6659. The goal numbers do not
see an orchestration (§12.2); the owner's boxes grade.

References on the page: `layered_r4` for the two tuned pairs, `auto_r4` for mismatch_1, 5 and 3,
`flat` for mismatch_2 and mismatch_7, which the layered probe never rendered before.

12.13.4 Tried on the frames and changed, each with its number.
1. A balanced transport of the cloud layer (80 % of the canvas) into the parts (31 %) contracted the
   whole layer: mean 200.7 px, 95th percentile 453 px. Re-weighting the target locally, a floor of
   0.3 and the border pin give 16.1 px.
2. The cloud's opacity from its density alone left 5.5 % of its pixels outside the gamut (by any amount) after
   the un-mixing, and frame 1 stood more than 4 levels off A on 2.2 % of the canvas; the least-opacity
   bound and the rule that the fill wins where holes overlap give 0.022 %.
3. A matte with a 16-px soft fringe outward (`halo_px`) lowered the ridge mid-way (0.92 L → 0.38 L at
   t = 0.28) and, by my eye, drew dark smudges around the cranes; it is in no round-5 score.
4. A match by label and position alone sent a tree 1,037 px across mismatch_1; the distance cap
   removed that match.
5. Without the rule for an element with no counterpart, the ground of mismatch_6 was carried to the
   air-conditioning unit at the top of B; by my eye a smear across the sky.

12.13.5 Seen by my eye and not evidence. mismatch_4 `auto_r5` shows a second bright lobe beside the
sun between frames 28 and 48 (the sun's wider glow travels with the sky's flow; backlog T18).
mismatch_7 `auto_r5` shows a bubble-shaped distortion in the lower sky around frames 38–48.
mismatch_1's building bends while it reshapes (the part of its field the affine map leaves out is
73.6 px RMS). mismatch_3 mid-way is a crowd of half-changed people.

12.13.6 Limits.
- The rules of the automatic score carry eighteen constants (`AUTO2`). None is set per pair, and every
  one was chosen while looking at these seven pairs; two pairs the probe had never rendered
  (mismatch_2, mismatch_7) are on the page, and no pair outside the fixtures exists to test on.
- The labels are wrong on some photos (§12.14, limit 5), and the score inherits it: on mismatch_3 a
  fan is matched to a chair (cost 0.821), and on mismatch_5 the galaxy's centre is a "sun".
- The automatic score builds no layer for a star, a meteor streak or the bridge of mismatch_5: the
  owner's "bridge itself rotate and become meteor streak" has no rule.
- An element of B with no counterpart appears in place only when both photos hold a sky.

### 12.14 The layer source: elements with a label, a group and a depth (2026-09-28; `scripts/research/layer_source.py`; page `benchmarks/runs/2026-09-28/layers/index.html`; an Opus 5.5 subagent, re-checked on the main thread)

Result: one script cuts a photo into elements and runs in `.venv` with nothing installed:
OneFormer Swin-L ADE20K (a semantic pass names every pixel, a panoptic pass gives one element per
person or object) plus CLIPSeg with one fixed list of 20 words for what ADE20K lacks (sun, cloud, star,
moon, galaxy core, meteor streak, air-conditioning unit), ordered by the depth model the tool already
holds. It took 8.8–22.5 s per photo on the 24 fixture photos and writes byte-identical files on
repeated runs (the main thread re-ran mismatch_4_S: `layers.npz` md5 `932199b5…`, `layers.json`
`5515747c…`, 15.2 s). The per-element automatic score of §12.13 reads its output. Nothing entered
`transitions.py`; no dependency entered `requirements*.txt`.

What an element is: one instance of a thing, or one connected region of a label. ADE20K treats
building, tree and wall as regions without instances, so two buildings that touch are one element.
`layers.json` gives per element its label, its group (23 groups, with a neighbour list per group: a
proposal, tuned on no pair), its share of the canvas, its box and centroid, its median disparity and
depth rank, its mean Lab and a confidence.

| model | licence (card / upstream) | bytes | s per photo | published | IoU against the tuned mattes |
|---|---|---|---|---|---|
| Mask2Former Swin-T ADE20K semantic (the 2026-09-27 baseline) | other / CC BY-NC 4.0 | 190 MB | 0.62 | 47.7 mIoU | 0.746 |
| OneFormer Swin-T ADE20K | mit / MIT | 203 MB | 1.15 semantic, 0.80 panoptic | none found | 0.742, 0.712 |
| OneFormer Swin-L ADE20K (chosen) | mit / MIT | 880 MB | 3.09 semantic, 2.58 panoptic | PQ 49.8, mIoU 57.0 | 0.787, 0.788 |
| Mask2Former Swin-L ADE20K semantic | other / CC BY-NC 4.0 | 866 MB | 0.97 at 384², 2.41 at 640 | 56.1 mIoU | 0.784, 0.767 |
| Mask2Former Swin-L ADE20K panoptic | other / CC BY-NC 4.0 | 866 MB | 1.01 at 384², 2.37 at 640 | PQ 48.1 | 0.808, 0.707 |
| EoMT-L DINOv3 ADE20K semantic | mit / MIT | 1.26 GB | 3.94 | 59.5 mIoU | 0.786 |
| EoMT-L DINOv2 ADE20K panoptic | mit / MIT | 1.27 GB | 2.59 | PQ 50.6 | 0.751 |
| Grounding DINO base + SAM 2.1 Hiera-L | apache-2.0 | 934 MB + 898 MB | 13.7 | none | 0.614; sun 0.56 / 0.50; clouds 0.79 |
| CLIPSeg rd64-refined (chosen for the extra words) | apache-2.0 | 605 MB | 1.99 | none | 0.568; sun 0.12 / 0.04; clouds 0.77 |

Times are medians over 18 photos at 4 torch threads while render jobs ran on the same CPU. Licences
are recorded and never a filter (owner ruling 2026-09-27); the main thread read the three chosen
cards' licence lines on 2026-09-28. The IoU is the mean over 7 rendered mattes (sky, building, tree,
water) of mismatch_4 and mismatch_6.

Limits, each measured:
1. The reference cannot rank the large models: it covers 4 photos and 7 mattes, and every large
   ADE20K model lands between 0.707 and 0.808 on it. The choice of OneFormer Swin-L rests on its
   published numbers, on one MIT checkpoint serving both passes, and on the semantic pass leaving no
   pixel unnamed. No reference exists for people, walls or ceilings.
2. A panoptic map alone drops regions: OneFormer Swin-L panoptic leaves out a label its own semantic
   pass finds in 10 cases over 18 photos, among them a building over 40.9 % of mismatch_3_S and the sky
   over 99.8 % of mismatch_5_F. The script uses both passes for that reason.
3. No route found a star on any of the 18 photos, and both open-vocabulary routes missed the
   air-conditioning unit of mismatch_6_F (IoU 0.00). Stars and that unit still need the photometric
   rules or a hand score. SAM 3 was not run: the repository is gated and this machine holds no
   Hugging Face token (HTTP 401).
4. The sun: the photometric rule scores 0.64 / 0.60 on mismatch_4 and fires on 17 of 18 photos,
   interiors included; Grounding DINO + SAM 2.1 scores 0.56 / 0.50 and needs torchvision; CLIPSeg with
   a brightness core scores 0.40 / 0.05. Naming the sun with the model and cutting its edge with the
   rule is not built.
5. Labels are wrong on some photos and the script does not know it: mismatch_3_S's brick wall is a
   "building" over 40 % of the frame, and CLIPSeg names a "sun" on mismatch_3_S and match_5_F and a
   "moon" on mismatch_6_F (UNVERIFIED as true or false).

Two run-time workarounds are named in every `layers.json`: an empty module replaces the training loss
(its constructor requires scipy; inference never calls it), and a bilinear torch resize replaces a
torchvision call that OneFormer's post-processing makes without importing torchvision. The stock path
would need scipy 1.18.1 and torchvision 0.28.0; both were installed only into a scratch environment
under `benchmarks/runs/2026-09-28/layers/venv`. The weights (8.3 GB for every model measured) live
under `benchmarks/runs/2026-09-28/layers/hf_home`, outside `models/`; every route re-ran offline with
identical label maps and no socket attempt.

### 12.15 The keyframe-cleaned clip: generated keyframes, the deterministic engine between them (2026-09-28; `scripts/research/keyframe_clip.py`; page `benchmarks/runs/2026-09-28/keyclip/index.html`; an Opus 5.5 subagent, re-measured on the main thread)

Result: the clips A → K1 → K2 → K3 → B exist for mismatch_4 and mismatch_6 and three measured faults
stand against them; ungraded as of 2026-09-28. The keyframes are FLUX.2 klein 9B at Q8_0 clean-ups of
the round-4 composite at clip times 0.25, 0.5 and 0.75, run on the second machine (68 s and 50 s
each, 18–19 GiB of memory, every run exit 0, the box clean after). The engine between them is
`transitions.py pair --preset morph`, unchanged. The numbers and the prompts are in
`research/keyframe-prompting.md §5.4` and DECISIONS 2026-09-28 Track B.

1. The tool's class decision does not hold between generated pictures: class B (the pan-and-zoom)
   on 1 of 4 segments of mismatch_4 and on 4 of 4 of mismatch_6.
2. The model changes the exposure: mismatch_4's clip runs mean L 18.8, 36.7, 33.2, 46.5, 26.2 at
   frames 0, 22, 45, 67, 89, where `layered_r4` rises from 18.3 to 25.5.
3. The motion stalls at every keyframe (step 0.6–1.8 levels at the joints, 4.6–6.5 mid-segment).

The page shows each clip beside `layered_r4` with the three boxes, a second render with class A
forced, and on mismatch_6 a render with the dissolve preset.


### 12.16 Owner picks on round 5 and the directions that follow (2026-09-28, 12:44 UTC; `benchmarks/runs/2026-09-28/layered_r5/layered_picks.json`; verbatim in DECISIONS 2026-09-28 afternoon)

Result: the two hand-written round-5 scores are picked as closer, `layered_r5_flow` on mismatch_6 and
`layered_r5_stagger` on mismatch_4, and mismatch_4 gets its first "one picture" ticks. The automatic
score is picked on mismatch_5, mismatch_3 and mismatch_2 and called a regression on mismatch_1 and
mismatch_7, where the second photo's content shows twice. The keyframe-cleaned clips (§12.15) are
"not usable" as rendered. Round 6 is next.

| pair | closer | boxes (one picture / transforms / nothing invented) |
|---|---|---|
| mismatch_6 | `layered_r5_flow` | `layered_r4` no box ticked; `layered_r5` no box ticked; `layered_r5_flow` yes/yes/yes; `auto_r5` no box ticked |
| mismatch_4 | `layered_r5_stagger` | `layered_r4` no/yes/yes; `layered_r5` yes/yes/yes; `layered_r5_stagger` yes/yes/yes; `auto_r5` no/yes/no |
| mismatch_1 | `none` | `auto_r4` no/yes/no; `auto_r5` no/yes/no |
| mismatch_5 | `auto_r5` | `auto_r4` no/yes/no; `auto_r5` yes/yes/no |
| mismatch_3 | `auto_r5` | `auto_r4` yes/yes/no; `auto_r5` no box ticked |
| mismatch_2 | `auto_r5` | `flat` no/no/yes; `auto_r5` no box ticked |
| mismatch_7 | `none` | `flat` no/yes/no; `auto_r5` no/yes/no |

The owner's notes, verbatim:
- mismatch_6: "layered_r5_flow ( and layered_r5 ) look now closer to. what i expected , much more direction and stability present and transition is more seamless"
- mismatch_4: "layered_r5_stagger ( and layered_r5 ) look now closer to. what i expected , much more direction and stability present and transition is more seamless , still small crossfading and minor building boders overlap ,but better than all previous results "
- mismatch_1: "In this case auto_r5 looks like overfit and regression , what you did - you have target B image and you very forcefully morph A to B but at some point both final image and itermediate morph are stacked (composited ) in very ugly manner so picture morphs into some duplicate final picture that is already there, i would expect natural  flow from one building ( or building group to another in this case, also clouds skewed alot ( will attach screenshots) "
- mismatch_5: "In this case auto_r5 looks like promising but still transition has some borders and edges visible in intermediate frames, also components transition ( especially bridge ) no definitive enough  but this looks a bit more gradual and promising than before"
- mismatch_3: "In this case auto_r5 looks like promising but still transition has some borders and edges visible in intermediate frames, components and people transition look interesting here, definitely improvement"
- mismatch_2: "In this case auto_r5 looks like promising but still transition has some borders and edges visible in intermediate frames,    but this looks a bit more gradual and promising than before , fun transition from person to persons in B frame"
- mismatch_7: "Here is only. case where it looks worse in R5 and more even like regression. Similar case as in mismatch_1 but worse as here buidlings do match a bit and in flat you corectly transitioned between some of them ( although sky is broken) , in R5 both sky and buidlings transition is broken and also they suffer from the same duplicated composite as mismatch_1 ( and this seems like some general issue for such cases) , will attach screen as well"

12.16.1 The duplicate, measured the same afternoon (`scripts/research/layered_diag.py layers`). In the
automatic score the layer under the elements (`ground`, or `rest` on a pair without a sky) holds the
whole ground of both photos, the matched elements included, and each element layer holds its element
again. The two move along different fields and mix at different times.

| pair, clip time | `ground`: mix, canvas share, px to go | element layer: mix, canvas share, px to go | canvas share where both show the second photo |
|---|---|---|---|
| mismatch_1, 0.539 | 0.957, 38 %, 257 | `e0_building` 0.203, 27 %, 232 | 0 % |
| mismatch_1, 0.629 | 0.999, 40 %, 183 | 0.65, 32 %, 150 | 32 % |
| mismatch_1, 0.719 | 1.0, 40 %, 90 | 0.979, 35 %, 75 | 35 % |
| mismatch_1, 0.809 | 1.0, 40 %, 21 | 1.0, 38 %, 23 | 38 % |
| mismatch_7, 0.629 | 1.0, 17 %, 125 | `e1_building` 0.65, 12 %, 189 | 11 % |
| mismatch_7, 0.719 | 1.0, 17 %, 61 | 0.979, 14 %, 94 | 13 % |

Mix 0 is the first photo's content and 1 the second's. From t = 0.63 the second photo's buildings
stand in the frame twice, 30 to 60 px apart, until both arrive. My design note of the night, that the
lower layer's copy moves with the element and stays hidden under it, was wrong: the element layers
start later (each has its own window), move with `ot_rigid`, and the lower layer mixes place by place.
Backlog T21.

12.16.2 Second finding of the same measure: the automatic score's layers with `ot_rigid` and no
`stagger` render through the round-4 warp, because only `stagger`, `field`, `exact` and the keys of
§12.13.2 item 3 select the round-5 path. That is six layers on mismatch_3, two on mismatch_7 and one
each on mismatch_1, mismatch_4 and mismatch_6; on mismatch_6's 1146-px canvas the rows are stretched
(backlog T19).

12.16.3 Not measured: the pale outlines along the building mattes and the smooth dome in mismatch_7's
lower sky (the owner's screenshots, `benchmarks/runs/2026-09-28/layered_r5/owner_screens/`).
[INFERRED] Both are the sky backdrop's hole fill: the fill shows beside a matte that was cut from a
label map (a 640-px model output, upsampled) and then warped, and it shows as a dome where the ground
layer's matte has moved off a large hole.

12.16.4 Round-6 targets, in the owner's words: the duplicate ("picture morphs into some duplicate
final picture that is already there"; "some general issue for such cases"); "natural  flow from one
building ( or building group to another"; "clouds skewed alot"; on mismatch_7 "both sky and buidlings
transition is broken"; "borders and edges visible in intermediate frames" (mismatch_5, 3 and 2); the
bridge of mismatch_5 "no definitive enough"; on mismatch_4 "still small crossfading and minor
building boders overlap".

12.16.5 The owner's other answers (the message is verbatim in DECISIONS 2026-09-28 afternoon).
- The keyframe-cleaned clips: "mostly just sequences of crossfades betweeen interrmediate generated
  frames"; "not usable , if you plan to utilize those intermediate keyframes , lets see". The chain
  of the tool's morphs is out; a clip that uses the keyframes inside the layered probe is open.
- The layer source: "i really like aggreagted  accuracy for all examples in etween `Grounding DINO B
  + SAM 2.1 L` + `layer source (layers.npz elements)` and of course depth and normals , so lets
  utilize all we can". SAM 2.1's processor needs torchvision (in the scratch environment only).
- "sam3 is authorized": the owner's account has access; this laptop held no Hugging Face token at
  2026-09-28 15:57 EEST. Amended 16:10 EEST the same day: the owner logged in ("hf auth was granted"),
  and the access check on `facebook/sam3` passes from this laptop; nothing is downloaded yet (12
  files, 6.90 GB, of which one 3.44 GB weights file is needed). `layer_source.py` sets `HF_HOME` to
  the research weights folder, so the fetch names the token's path (`HF_TOKEN_PATH`).
- "round 6 next".
- Two questions of the owner, answered in the session's last message: the question on the clouds
  named no clips (it meant `layered_r5` against `layered_r5_flow` on mismatch_6, and the pick
  answers it); five pairs carry only automatic clips because hand-written scores exist for
  mismatch_6 and mismatch_4 only, and a mechanism is judged on pairs it was not tuned on (§11).
