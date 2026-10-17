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
| Layered probe round 6, 2026-09-28 evening (§12.17; page `benchmarks/runs/2026-09-28/layered_r6/`; scores `mismatch_{4,6}_r6.json`, `scores/auto/*_v3.json`; M3 Pro, CPU, beside two other jobs) | 3 s, 90 frames, nine clips byte-identical on two runs. Hand-written: mismatch_6 (1146×1524) prep 35.6 s, render 32.4 s, steps 0.04 / 0.01, md5 `fc42da91…`; mismatch_4 (1920×1092) 10.9 / 41.0 s, steps 0.0 / 0.0, `531895da…`. Automatic (`--auto3`, elements from `layers_v2`): mismatch_1 (1444×1920) 17.5 / 64.2 s, `fcbc8f44…`; mismatch_7 (1920×1488) 28.4 / 89.7 s, `a11cc816…`; mismatch_4 15.2 / 44.6 s, `caa9f3e1…`; mismatch_6 5.0 / 37.5 s, `348da836…`; mismatch_5 (1920×1080) 13.2 / 48.8 s, `4f8a73aa…`; mismatch_3 (1920×1440, ten layers) 49.8 / 182.0 s, `02400e79…`; mismatch_2 (602×800) 42.3 / 9.3 s, `151a5224…`. Probe md5 `2ac27ee6…`; the 25 md5s of rounds 1–5 unchanged; `transitions.py` untouched |
| Merged layer source on the 24 fixture photos, 2026-09-28 evening (§12.18; `scripts/research/layer_merge.py`; page `benchmarks/runs/2026-09-28/layers_v2/`; scratch environment with torchvision 0.28.0; CPU, 4 torch threads, beside render jobs) | Grounding DINO base + SAM 2.1 Hiera-L 12.2 s per photo (median; 10.2–15.1), SAM 3 28.6 s (25.2–35.0), the whole v2 run 23.4–39.8 s per photo; peak RSS 6.5–6.9 GB (v2), 12.7 GB (v3); SAM 3 weights 3,439,938,512 B; 14 of 14 mismatch photos byte-identical on two runs, 0 socket attempts; on the main thread mismatch_4_S gives md5 `fa677ab4…` / `3a782a94…` |
| Keyframes inside the layered probe, 2026-09-28 evening (§12.19; `scripts/research/keyframe_layer.py`; clips `benchmarks/runs/2026-09-28/keylayer/`) | FLUX.2 klein 9B Q8_0 on the second machine: seven runs of 50–95 s, MemAvailable 36.2–36.8 → 17.57–18.96 GiB; six clips of 90 frames at the canvas size, byte-identical on two renders; Laplacian variance of L at the keyframe frames 20–66 % under the source clip's |
| Layered probe round 7, 2026-09-29 (§12.21; page `benchmarks/runs/2026-09-29/layered_r7/`; scores `scores/auto/*_v4.json`; M3 Pro, CPU, beside a regression run) | 3 s, 90 frames, seven clips byte-identical on two runs. Automatic (`--auto4`, elements from `layers_v3`): mismatch_1 (1444×1920) prep 9.9 s, render 66.6 s, steps 0.04 / 0.02, md5 `8eeb239a…`; mismatch_7 (1920×1488) 20.3 / 92.1 s, 0.03 / 0.03, `c3ba476d…`; mismatch_6 (1146×1524) 5.3 / 28.8 s, `e0b588c5…`; mismatch_4 (1920×1092) 13.4 / 35.2 s, `bb70cc2f…`; mismatch_5 (1920×1080) 11.6 / 37.0 s, `6691169d…`; mismatch_3 (1920×1440, eight drawn objects) 29.3 / 103.3 s, `ffe2818a…`; mismatch_2 (602×800) 28.4 / 6.5 s, `049c60f9…`. The measure `change` takes about the clip's render time at every second step. Probe md5 `54e9ee97…` (3,711 lines), `layered_diag.py` `b5779a51…`; the 34 md5s of rounds 1–6 unchanged; `transitions.py` untouched |
| Merged layer source with SAM 3, second run, 2026-09-29 (§12.22; `benchmarks/runs/2026-09-29/e4/`; CPU, beside render jobs) | 24 of 24 photos byte-identical to `layers_v3`, 0 socket attempts, 61.3–99.6 s per photo (median 70.4; SAM 3 alone 45.6), wall 1,750 s, peak RSS 11.55 GB |
| Generated backgrounds, 2026-09-29 (§12.23; `benchmarks/runs/2026-09-29/plates/`; FLUX.2 klein 9B Q8_0 on the second machine) | nine runs: 89–136 s at 1344×1008, 34–54 s at 608×800, MemAvailable 34.8–36.1 → 15.60–17.93 GiB; one repeated run byte-identical; 1920×1440 does not fit `--max-vram 20` |

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

Amendment 2026-10-17 (the owner's answer to §13.8 question 3, verbatim: "if camera move is
intentional and has a correct artistic sense of direction ( like in above examples) it makes total
sense, both in 2d and 3d spaces"): the sentence "a camera move is decoration, not the transition"
is narrowed. A camera move whose direction carries the idea of the transition (one scene inside a
region of the other, one camera pulling back out of the first into the second, as he described on
mismatch_5 and mismatch_3) is the transition's spine, in 2D and in 3D, and the transformation of
the content inside it is still required; a camera move with no such direction remains decoration
(F2). The "cameras as a transition" item leaves the parked list for that case only.

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

### 12.17 Round 6: every pixel in one layer, fields that do not bend their layer, a sky that shows a fill last (2026-09-28 evening; page `benchmarks/runs/2026-09-28/layered_r6/index.html`; scores `mismatch_4_r6.json`, `mismatch_6_r6.json`, `scores/auto/<pair>_v3.json`)

Result: the automatic score of round 6 draws no pixel of a photo in two layers (round 5: two drawn
layers held the same pixels over 17.3 % and 39.7 % of the canvas on mismatch_1's two photos; round
6: 0.000 %), its clouds travel 9–38 px on average (round 5: 252–366 px) and bend 0.24–0.49 (2.81–
2.98), and the frames beside the endpoints stand at most 8 levels from the photos on the two pairs
the owner called a regression. Three faults stand, measured: an object that moves away leaves a
smooth fill (seen on up to 13.7 % of the canvas on mismatch_3, 5.0 % on mismatch_2); the ground
travels less than half as far as its field asks on mismatch_1, mismatch_7 and mismatch_2; mismatch_5's
bridge has no rule of its own. Nine clips are byte-identical on two runs; the 25 md5s of rounds 1–5
are unchanged on the final probe (md5 `2ac27ee6…`, 3,269 lines); nothing in `transitions.py`
changed. Ungraded as of 2026-09-28: the owner's boxes on the page are the next input.

12.17.1 Measures added to `scripts/research/layered_diag.py`, each run on round 5 before any change.

| measure | what it reads | control or calibration |
|---|---|---|
| `fields` | per `morph_to` layer and direction: travel (mean, 95th percentile of the field's length), strain (the singular values of I + grad field), `bend` (95th percentile of the strain of what the field's affine part leaves out), the share that folds | the clips the owner picked in round 5 bend 0.23–0.75 (`mismatch_4_r5_stagger` 0.23, `mismatch_6_r5_flow` 0.57–0.75); the clouds he called "skewed alot" 2.81–2.98, 4.0 % of mismatch_1's cloud folded |
| `rim` | the share of a matte's 4-px inner rim whose Lab colour is nearer to the local colour outside the matte than to the matte's core (means at 12 px; counted where the two means stand more than 10 apart) | eroding mismatch_1's building mattes by 12 px lowers it from 74.3 to 38.5 % and from 85.6 to 22.6 %: the measure responds to a tighter matte; on those photos it does not fall under 18–44 % |
| `holes` | per frame the share of the canvas where a backdrop's hole fill, or a fill under an object, is what the viewer sees (fill weight over 0.5, no layer above with alpha over 0.5) | at rest it reads the fill kept by design under a thin cloud (3.3 % on mismatch_1, 9.2 % on mismatch_7); read the largest value beside the value at rest |
| `layers`: `semi` | the share of the canvas where a layer's alpha lies between 0.05 and 0.95 | `mismatch_4_r5_stagger` 2.8 % at t 0.47 against 0.9–1.1 % at rest |
| `layers`: `overlap` | unchanged, with two refinements: two layers both at rest do not count; a layer that holds a fill under an object counts only where it holds the photo's own pixels | the round-5 score of mismatch_1 still reads 0.32 at t 0.629 and 0.35 at 0.719 |

12.17.2 What the owner's faults were, by these measures on the round-5 automatic clips.
1. The duplicate between layers (§12.16.1, backlog T21): two drawn layers hold the same pixels of a
   photo over 17.3 / 39.7 % of the canvas (first / second photo) on mismatch_1, 6.2 / 16.6 % on
   mismatch_7, 68.7 / 43.5 % on mismatch_4, 21.4 / 21.5 % on mismatch_6, 83.0 / 43.8 % on mismatch_3
   and 93.3 / 96.4 % on mismatch_2.
2. The duplicate inside one layer: a `morph_to` layer's matte is the union of its two warped mattes,
   and the part only the second photo covers stands at alpha 0.71 when the mix is 0.2. The owner:
   "both final image and itermediate morph are stacked (composited ) in very ugly manner".
3. The dome of mismatch_7: the cloud layer travels 252 px and leaves the lower sky; the backdrop
   shows its fill there. Fill seen: 5.5 % of the canvas at rest, 14.5 % at the largest.
4. The pale outline: 46–87 % of the rim pixels of the building and ground mattes of mismatch_1 and
   mismatch_7 hold the outside colour. The mattes come from a 640-px label map.
5. "clouds skewed alot": travel 366 px (mismatch_1) and 252 px (mismatch_7), bend 2.98 and 2.81.

12.17.3 Keys added to `scripts/research/layered_probe.py`, all default-off. `Backdrop.render` is
split into `_lab` and `_alpha`, and `fill_holes` calls `fill_field`; the 25 md5s prove both.

| key | on | what it does |
|---|---|---|
| `plate: {holes, dilate, sigma, scales, settle_px}` | a layer | inside the zones of the layers drawn over it the layer holds a fill made from its own pixels around them, and the photo's own pixels while the zone's layer rests within `settle_px` |
| `mix: "shape"` | `morph_to` | the matte is one shape, the level set of the two warped mattes' signed distances mixed by the mix; a place both cover mixes by the plain share, a place one covers is that one's |
| `ot_bend: cap` | `morph_to` | the field is its affine part plus a rest; the rest is blurred at the first of 12, 24, 48, 96, 192 px at which its bend is under the cap, then scaled; after the border pin (`ot_border`, §12.13: the field falls to zero at the canvas border) one gain on both directions brings the bend back under the cap |
| `ot_balance: s` | `morph_to` | the two masses are balanced place by place at s × the long side before the transport: a part with no counterpart near it stays and changes by the mix |
| `prefer_known`, `prefer_px` | a backdrop | the two residuals mix place by place: both known or both filled, the mix; only one known, that one; the change runs over `prefer_px` |
| `snap: {r, eps, iters}` | any mask rule | a guided filter of the hard matte by the photo's L moves the matte's edge to the photo's edge; a matte that loses over half its area keeps its own edge |
| `times_not: [names]` | any mask rule | the matte holds no pixel of an earlier mask; `{"layer", "thr"}` leaves out that mask's whole support |

Also new: `--auto3 PAIR` (writes `scores/auto/<pair>_v3.json`, tag `auto_r6`), `--write-only`,
`--looks FILE` (per pair, what to look at and the order of its clips, shown on the page).

12.17.4 The automatic score of round 6 (`auto_score2(..., r6=AUTO3)`). Matching is round 5's; the
elements come from the merged layer source (§12.18, `benchmarks/runs/2026-09-28/layers_v2`).
1. Surfaces (building, structure, tree, vegetation, water, mountain, ground, floor, wall, ceiling,
   opening) move as one layer, `ground` or `rest`. A matched surface is not drawn: its transport
   steers that layer where it stands (interpolated at 0.04 × the long side, the layer's own
   transport far from every match).
2. Objects (person, animal, vehicle, light, furniture, appliance, picture, object) are drawn by
   their own layers over it, and it holds a `plate` under them.
3. Every `morph_to` takes `exact` (backlog T19), `mix: "shape"` and `ot_bend` 0.75, the largest bend
   of the clips the owner picked.
4. The sky: a cloud pair takes `ot_balance` 0.1; a cloud's or a light's matte ends 8 px short of the
   ground and shares no pixel with another; the hole kept under it is its support and no wider;
   the backdrop takes `prefer_known` with `prefer_px` 0.03 × the long side.
5. The ground's and the objects' mattes take `snap` (r 20 px, eps 4, 2 passes).

12.17.5 Results, round-6 automatic clips (`layered_diag.py`, final probe). Pixels in two layers:
first / second photo. Fill seen: at rest / the largest / of it where a layer has moved off. Rest:
the largest difference from the photo in the two frames beside each endpoint, and the share of the
canvas over 4 levels.

| pair | pixels in two layers, round 5 → 6 (%) | ground or rest: travel px, bend, gain | clouds or light: travel px, bend | rim of the ground, first / second photo (%) | fill seen (%) | rest: max levels, share over 4 |
|---|---|---|---|---|---|---|
| mismatch_1 | 17.3 / 39.7 → 0.000 / 0.000 | 36, 0.28, 0.492 | 32, 0.43 | 29 / 28 (round 5: 78 / 87) | 3.3 / 5.9 / 2.84 | 3, 0.000 % |
| mismatch_7 | 6.2 / 16.6 → 0.000 / 0.000 | 14, 0.24, 0.431 | 38, 0.49 and 9, 0.24 | 7 / 12 (round 5: 53 / 70) | 9.2 / 13.0 / 2.09 | 8, 0.006 % |
| mismatch_4 | 68.7 / 43.5 → 0.000 / 0.000 | 117, 0.74, 0.924 | sun by the round-5 rule | 10 / 12 | 0.0 / 3.9 / 3.85 | 42, 0.118 % |
| mismatch_6 | 21.4 / 21.5 → 0.000 / 0.000 | 40, 0.56, 0.952 | none matched | 48 / 38 | 0.0 / 3.4 / 3.42 | 2, 0.000 % |
| mismatch_5 | 0.3 / 0.0 → 0.000 / 0.000 | 74, 0.56, 0.924 | light 412, 0.37 | 19 / – | 0.6 / 4.7 / 0.29 | 13, 0.062 % |
| mismatch_3 | 83.0 / 43.8 → 0.002 / 0.012 | 70, 0.75, 0.643 | nine objects 210–623, 0.11–0.73 | objects 8–32 | 0.0 / 13.7 / 13.72 | 0, 0.000 % |
| mismatch_2 | 93.3 / 96.4 → 0.000 / 0.000 | 20, 0.69, 0.314 | one object 147, 0.37 | object 25 / 24 | 0.0 / 5.0 / 5.04 | 0, 0.000 % |

Round 5 on the two regression pairs, the same measures: `overlap` 0.38 and 0.15 at the largest
(round 6: 0.01 and 0.01, a cloud layer passing over the ground layer; the two hold different
pixels); fill seen 3.2 / 6.3 / 1.87 % and 5.5 / 14.5 / 3.02 %; rest 35 levels at most (0.011 %) and
141 (0.075 %). The fill seen did not fall on mismatch_7 (14.5 → 13.0 % at the largest): 9.2 % is
the fill kept under thin cloud at rest, and the share under moved layers fell from 3.02 to 2.09 %.
Timings (M3 Pro, CPU, beside two other jobs): prep 5.0–49.8 s, render 9.3–182.0 s (mismatch_3, ten
layers); md5s of the nine clips in the sheet.

12.17.6 The hand-written scores of round 6 (`mismatch_4_r6.json`, `mismatch_6_r6.json`) are the
owner's round-5 picks with `mix: "shape"` on one layer each. The half-transparent share of that
layer falls from 2.8 to 0.7 % of the canvas on mismatch_4 (the band, t 0.47) and from 2.9–7.3 to
0.3–0.4 % on mismatch_6 (the buildings, t 0.61–0.67). The frames beside the endpoints are unchanged
(mismatch_4: 2 and 9 levels at most; mismatch_6: 34 and 1). The texture mix inside the band is
unchanged, so the owner's "small crossfading" on mismatch_4 is not addressed.

12.17.7 Tried and dropped.
1. Every matched element drawn by its own layer with no layer under them, the elements holding the
   ground between them: gaps open between neighbouring buildings and show the sky's fill (seen on
   the frames `layered_r6/diag/seq_mismatch_1_try4_v2.jpg`, not measured). Replaced by item 1 of
   12.17.4.
2. The cloud keys of the hand-written scores (`ot_local` 0.1, `ot_floor` 0.1) on a cloud pair:
   travel 63–124 px, bend 0.60–0.73, and the dome stayed (fill seen 15.1 % on mismatch_7). Replaced by
   `ot_balance`.
3. A flow between the signed distances of the pushed matte and its target, to register the two
   shapes: the overlap (IoU) went from 0.641 to 0.723 on mismatch_1 and from 0.387 to 0.158 on
   mismatch_7, and the bend rose to 3.75 and 16.21.
4. The border pin before the bend cap: bend at most 0.74, and the ground's layer pulled away from
   three sides of mismatch_2's canvas (black wedges, seen on the frames).
5. The border pin after the cap with no gain, and objects pinned too: bend 0.81–1.38 on the
   ground's field and 1.01–2.67 on nine of the ten objects of mismatch_3 and mismatch_2.

12.17.8 Limits of the result.
1. Neither photo shows what is behind an object. The fill under it is a normalized convolution of
   its surroundings and is seen as a blurred patch once the object has moved: 13.7 % of the canvas
   on mismatch_3 at t 0.55, 5.0 % on mismatch_2 (backlog T22).
2. The border pin bends a field, and the gain that restores the cap cuts the travel: 0.492 on
   mismatch_1, 0.431 on mismatch_7, 0.314 on mismatch_2, 0.643 on mismatch_3 (backlog T23).
3. The transport does not register two shapes: the pushed ground matte overlaps its target at IoU
   0.568 on mismatch_1 and 0.376 on mismatch_7, against 0.82–0.89 for the two picked hand-written
   clips. `mix: "shape"` then draws one shape whose outline is a level set of two distances, not an
   outline of either photo (backlog T24).
4. The mattes of clouds and lights are unchanged (blurred 16 and 12 px): their rim reads 28–64 %.
5. The ground's mix runs from t 0.27 to 0.58 on mismatch_1 (mix 0.01 → 0.99); after 0.6 the
   second photo's ground settles into place. The pace is round 5's and was not tuned.

12.17.9 Not done in this round.
1. mismatch_5's bridge ("no definitive enough"): an element of the first photo with no counterpart
   still has no layer and no window of its own.
2. mismatch_7 shows the same towers in both photos at different sizes (by my eye on the two
   photos); the matching by label, position, size and depth does not use it.
3. The elements with SAM 3 (`layers_v3`, §12.18) are read by no score.
4. The last interior frames of mismatch_4 stand 42 levels off the second photo at most (0.118 % of
   the canvas); the cause is not traced.

### 12.18 The merged layer source and SAM 3 (2026-09-28; `scripts/research/layer_merge.py`; outputs `benchmarks/runs/2026-09-28/layers_v2` and `layers_v3`; page `benchmarks/runs/2026-09-28/layers_v2/index.html`; an Opus 5.5 subagent, re-checked on the main thread)

Result: the merged layer source adds instance masks to the §12.14 layer source on all 24 fixture
photos, byte-identical on repeated runs, 0 socket attempts. `layers_v2` uses Grounding DINO base +
SAM 2.1 Hiera-L; `layers_v3` adds SAM 3 as a third route (`--routes gdino_sam2,sam3`, default off).
The round-6 automatic score (`layered_probe.py --auto3`) reads `layers_v2` by default and matches 5
groups on mismatch_1 (§12.14 source: 1) and 4 on mismatch_7 (2), re-checked on the main thread; no
score reads `layers_v3`. SAM 3 alone beats Grounding DINO + SAM 2.1 alone (IoU 0.690 against 0.614)
and is the only route to overlap mismatch_6_F's air-conditioning unit (IoU 0.26). Ungraded as of 2026-09-28.

The §12.14 source is reproduced inside the merge: on all 24 photos the base element map equals
`layers/<photo>/layers.npz` (`base check True`). Re-checked on the main thread, offline: mismatch_4_S
gives 13 → 14 elements, md5 `fa677ab4060b3264f592c4d714ae60b5` / `3a782a94c1a5e85c999140ef58139326`, 0
socket attempts; `layers_v2/_det_run2` is byte-identical on 14 of 14; the §12.14 source still gives 13
elements, `932199b5…`, `5515747c…`. v3: mismatch_1_S and mismatch_7_F re-run identical (2 of 2).

The merge rule (the script's docstring; no constant names a photo):
1. A SAM candidate is dropped below `MIN_SAM_IOU` 0.70 (SAM's predicted IoU), below `MIN_SHARE`
   0.0005 of the canvas, or in the group "opening" (`PART_GROUPS`: windows would cut a facade into
   pieces). Of two masks with IoU ≥ `DEDUP_IOU` 0.85 the higher score stays; masks are painted largest
   first, and one with less than `MIN_VISIBLE` 0.50 of itself visible is dropped.
2. Host share hs = the share of the visible mask on old pixels of the same group. With hs ≥
   `CONTAIN_MIN` 0.50 the mask is an instance of the old element it overlaps most and may reach
   `EDGE_BAND_PX` 8 px outward. With hs < `NEW_MAX_NAMED` 0.20, score ≥ `NEW_MIN_SCORE` 0.35, area ≤
   `NEW_MAX_SHARE` 0.20 and a group outside `STUFF_GROUPS` (sky, water, wall, ceiling, mountain) it is
   a new object. Every other mask is dropped with its reason in `merge.candidates`.
3. One hosted mask with IoU ≥ `EDGE_IOU` 0.80 against its element gives that element the SAM region
   and edge; otherwise the element splits into instances. Stuff groups never split.
4. Slivers (removed by an opening of radius `SLIVER_PX` 3) go to the nearest other element within
   `REASSIGN_MAX_PX` 16 px; residual bodies stay as elements with `instance_of` set. A smaller old
   element of another group keeps its pixels against a larger claim.
5. One uint16 id map holds all elements; two asserts check ids against records. New fields: `instance_of`,
   `base_id`, `edge_route`, `edge_sam_share`, `box`, `box_score`, `sam_iou`, `median_normal`.

Counts, 14 mismatch photos (the 10 match rows: `agents/E3_report.md`). Elements and building: §12.14
source / v2 / v3. SAM bld: building elements whose region a SAM mask drew. v2 s: the whole merged run.
SAM 3 s: vision pass plus 28 prompts. md5: first 8 hex of `layers.npz`, `layers.json`.

| photo | elements | building | SAM bld v2 / v3 | v2 s | SAM 3 s | md5 v2 | md5 v3 |
|---|---|---|---|---|---|---|---|
| mismatch_1_S | 15 / 34 / 59 | 2 / 9 / 12 | 4 / 8 | 35.5 | 25.6 | 41471115 28b267b7 | 0f44bba7 1e2c5b05 |
| mismatch_1_F | 10 / 16 / 63 | 1 / 3 / 34 | 1 / 26 | 38.4 | 26.3 | 4903670e c43d5443 | d7a3c9a7 f19bcca6 |
| mismatch_2_S | 5 / 5 / 7 | 0 / 0 / 0 | 0 / 0 | 29.6 | 28.5 | 158ccd82 74970284 | 34291fb4 d69cb008 |
| mismatch_2_F | 17 / 17 / 22 | 4 / 4 / 4 | 0 / 0 | 24.6 | 28.2 | 2cc4d509 f4339678 | 391be4b6 9f0efe01 |
| mismatch_3_S | 53 / 59 / 75 | 5 / 1 / 5 | 1 / 0 | 33.8 | 31.6 | f251706d f49bc4bd | 4ed1f258 53817439 |
| mismatch_3_F | 44 / 48 / 56 | 0 / 0 / 1 | 0 / 1 | 33.3 | 29.2 | a184be7f eef7d84a | 24a8c22b 48930a13 |
| mismatch_4_S | 13 / 14 / 22 | 3 / 3 / 12 | 0 / 8 | 27.5 | 26.6 | fa677ab4 3a782a94 | 49802f5c a38417f8 |
| mismatch_4_F | 8 / 10 / 28 | 1 / 1 / 7 | 0 / 5 | 29.0 | 28.6 | 35bc08ac ca307f38 | 41e851be ddb27b4a |
| mismatch_5_S | 24 / 23 / 38 | 0 / 0 / 1 | 0 / 1 | 28.1 | 28.6 | 0faf6cb3 10332f18 | 80c29aad b2c1f388 |
| mismatch_5_F | 5 / 7 / 9 | 0 / 0 / 0 | 0 / 0 | 32.2 | 35.0 | 710429cc 11a81304 | e4ce8d92 ebde3052 |
| mismatch_6_S | 11 / 22 / 38 | 1 / 6 / 16 | 1 / 10 | 23.4 | 26.0 | c4c571d9 48ccede8 | 25cca3b8 cad93ac6 |
| mismatch_6_F | 5 / 6 / 9 | 1 / 1 / 1 | 0 / 0 | 24.1 | 25.2 | 6c7dd3be e91c2332 | 63c01a12 4ba32332 |
| mismatch_7_S | 9 / 17 / 37 | 4 / 6 / 9 | 4 / 9 | 24.8 | 25.4 | 6244ef77 c9099928 | 16fc962b 58fb775a |
| mismatch_7_F | 10 / 18 / 35 | 2 / 9 / 21 | 6 / 16 | 26.3 | 30.4 | da3c4b60 bc4e4cbd | 389a21cb 52c9eeae |

Time and memory (4 torch threads; the main thread rendered on the same CPU): v2 419 s wall for the 14
mismatch photos (second run 524 s), v3 1061 s for 24 photos. Median s per photo: Grounding DINO + SAM
2.1 12.2 (10.2–15.1), SAM 3 28.6 (25.2–35.0; the report's summary says 26–35), §12.14 source 12–23.
Peak RSS: v2 6.5 GB (mismatch) and 6.9 GB (match), SAM 3 alone on 4 photos 7.6 GB, v3 12.7 GB.

Measurements (`layers_v2/measure_v2.py`, `numbers_v2.json`). IoU = |P ∩ R| / |P ∪ R| against 7
hand-tuned sky, building, tree and water mattes of 2026-09-27 (§12.14). BF2 = boundary F-score at 2
px against them. ES2 = share of element-border pixels within 2 px of a Canny edge minus that share 5–7
px from the borders (chance level).

| source | mean IoU | mean BF2 | sun mismatch_4_S / _F | AC unit mismatch_6_F | clouds mismatch_6_S | median ES2 margin, 24 photos |
|---|---|---|---|---|---|---|
| §12.14 source | 0.788 | 0.215 | 0.40 / 0.05 | 0.00 | 0.77 | 0.039 |
| Grounding DINO B + SAM 2.1 L alone | 0.614 | 0.072 (n 5) | 0.56 / 0.50 | 0.00 | 0.79 | – |
| SAM 3 alone | 0.690 | 0.149 | 0.57 / 0.51 | 0.26 | 0.56 | – |
| merged v2 | 0.785 | 0.140 | 0.39 / 0.05 | 0.00 | 0.77 | 0.111 |
| merged v3 (+ SAM 3) | 0.781 | 0.192 | 0.39 / 0.05 | 0.27 | 0.77 | 0.136 |

ES2: v2 beats the §12.14 source on 18 of 24 photos, v3 beats v2 on 18, v3 beats the source on 20.
Where borders moved (23 photos, `moved_borders`) v2's stretch has the higher ES2 on 15 and the lower
on 8, e.g. mismatch_4_S (0.23 against 0.72) and match_4_S (0.20 against 0.71).

SAM 3 setup: `facebook/sam3` at revision `3c879f39826c281e95690f02c7821c4de09afae7`, fetched into
`layers/hf_home/hub` in 98 s, 3,445,029,864 B in 10 files; `model.safetensors` 3,439,938,512 B, no
`sam3.pt` (both re-checked on the main thread). The hub-byte log moved by 3,445,029,958 B across the
mismatch run beside the fetch; the report does not reconcile the two. Token via `HF_TOKEN_PATH`, never
printed; licence "SAM License" of 2025-11-19, recorded only. transformers 5.17.0 has `Sam3Model`,
which requires torchvision (`modeling_sam3.py:814`), so SAM 3 runs only in the scratch environment
`layers/venv` (`.venv` + scipy 1.18.1 + torchvision 0.28.0 via a `.pth` file; torch 2.13.0; nothing
new installed). Hub config `sam3_video`, of which `Sam3Model` loads the detector. CPU only. Prompts,
one pass each, verbatim: sun, cloud, star, moon, galaxy core, meteor streak, air conditioning unit,
building, tree, person, water, sky, mountain, wall, ceiling, window, car, street lamp, bridge, boat,
house, skyscraper, tower, palm, bus, truck, bicycle, animal (Grounding DINO gets the first 20). Score
threshold 0.40, mask threshold 0.50. Verdict: more instances than Grounding DINO + SAM 2.1 (977 masks
against 214) and higher IoU and BF2 as one route, so it is the third route, default off; worse on
clouds (0.56 against 0.79).

Limits, none cut:
1. No reference exists for instances: whether v3's 34 building elements on mismatch_1_F are buildings
   or facade pieces is UNVERIFIED. In the subagent's `--auto2` run on mismatch_1, 2 of 5 matched groups
   send a building of mismatch_1_S to trees (building#21 → tree#9, cost 0.777; building#23 → tree#11
   + tree#6 + plant#14, 0.773): v2 has 9 building elements on mismatch_1_S against 3 on mismatch_1_F.
2. The edge claim is split: BF2 falls (0.215, 0.140, 0.192) while ES2 rises, and the ES2 gain mixes
   moved borders with new borders between instances. The tuned mattes come from photometric rules with
   grow and feather steps, a weak border reference. SAM 2.1 masks come from 256-px logits and SAM 3's
   from 288-px, against about 212 × 160 for OneFormer at 850 × 640, so the SAM edge is not much finer.
3. The sun stays at 0.39 / 0.05 in the merge though SAM 3 alone scores 0.57 / 0.51: its mask becomes
   an instance of the sky or splits from it (UNVERIFIED which; `layers_v3/mismatch_4_F/layers.json`
   holds the verdicts). mismatch_3_S's wall stays "building" (§12.14 limit 5). No route found a star.
4. Not done: `--auto2` on v3 or on pairs other than mismatch_1; a score reading `layers_v3`; a judged
   clip; v3 determinism beyond 2 of 24 photos; MPS for SAM 3. The constants are first values, untuned;
   the SAM 3 score threshold 0.40 is above the processor's default 0.30.
5. With torchvision present AutoProcessor picks other processors, so the §12.14 source runs as a `.venv`
   subprocess. The mismatch run's offline proof is the socket count only; the match and v3 runs show
   12,310,035,528 hub bytes before and after. `layers_v2/_smoke/` is left over (`rm -rf` was denied).

### 12.19 Generated keyframes used inside the layered probe (2026-09-28; `scripts/research/keyframe_layer.py`; clips `benchmarks/runs/2026-09-28/keylayer/`; an Opus 5.5 subagent, re-measured on the main thread)

Result: the layered probe now takes three FLUX.2 klein 9B keyframes per pair, and on both pairs the
keyframes lower the detail instead of adding it; none of the six clips is a candidate for a final
result. At the keyframe times the Laplacian variance of L falls by 20 to 66 % against the source clip
(re-measured on the main thread); mean L, the motion and the endpoints hold. The clips test whether a
cleaned keyframe improves a layered composite once its colour is held. Ungraded as of 2026-09-28. This
answers the owner's verdict on §12.15, verbatim: "mostly just sequences of crossfades betweeen
interrmediate generated frames" and "if you plan to utilize those intermediate keyframes , lets see".
Keyframes kf_23–kf_28 and their prompts: `research/keyframe-prompting.md §5.5`.

Formula (`keyframe_layer.py clip`), in Lab, on the variant's channels, rounded to 8 bits:
frame(t) = C(t) + g · Σ_k w_k(t) · carry_{t_k→t}(band_σ(K'_k − C(t_k))). C: the source clip
`mismatch_6_r5_flow` or `mismatch_4_r5_stagger` from the frozen probe (`HEAD`, md5 `7544463a…`).
1. K'_k: keyframe k resized to the canvas (INTER_CUBIC) and registered onto C(t_k) on locally
   normalised L: an ECC affine, refused if a corner moves more than 24 px, plus a DIS residual
   (smoothed at 16 px, capped at 8 px) kept only when it raises the structure correlation.
2. Lab match: per-channel mean and standard deviation matched to C(t_k) per layer matte, weighted by
   each layer's visible share at t_k; gain clipped to (0.4, 2.5), the probe's `gain_clip`.
3. band_σ = identity − GaussianBlur(σ). carry: OpenCV DIS (PRESET_MEDIUM) between consecutive
   composite frames on L at half resolution, smoothed at 4 px, composed outward from t_k (a fallback:
   the frozen probe has no per-pixel motion of the composite). w_k: raised cosines forming a
   partition of unity over the knots [1, t_1, t_2, t_3, n−2], so w = 0 at frames 0, 1, 88 and 89.
4. Variants, g = 1.0 in all three: `keylayer_a` σ 4 px on L; `keylayer_b` σ 24 px on L, a, b;
   `keylayer_c` σ 0 (the whole correction) on L, a, b, so at t_k its frame is the Lab-matched keyframe.

Keyframe times: d_i = the mean over pixels of min(|C_i − A|, |C_i − B|); frames are taken greedily
by d_i from 3..86, at least 15 apart, three at most. Each profile has one peak, so the rule gives the
peak and ±15: mismatch_6 frames 15 / 30 / 45 (d 16.55 / 60.16 / 16.55), mismatch_4 27 / 42 / 57 (d
5.99 / 12.58 / 5.89). A rule on frame means (14 / 29 / 44, 25 / 40 / 55) was tried first and dropped.

Measures (`cv2.VideoCapture`, the same code on every clip; `keylayer/<pair>/measure_table.md`). Stall:
a step under half the mean of the steps within ±3 frames. Fade R²: R² of the step in L against L(next
state) − L(previous state), the states being frames 0, t_1, t_2, t_3 and 89.
| pair | clip | mean L range | step median | stalls (frames) | Laplacian var median | fade R² | DIS px per step | mp4 md5 |
|---|---|---|---|---|---|---|---|---|
| mismatch_6 | source | 5.87–59.58 | 1.474 | 0,1,79,80,81,84,85 | 53.2 | 0.360 | 2.53 | `fceb36e8…` |
| mismatch_6 | a | 5.86–59.58 | 1.658 | 0,1,86,87 | 43.3 | 0.358 | 2.20 | `9f0b3cd2…` |
| mismatch_6 | b | 5.87–59.58 | 1.780 | 0,1,85 | 45.0 | 0.351 | 2.18 | `0e6c57c0…` |
| mismatch_6 | c | 5.85–59.58 | 2.027 | 0,1,86,87 | 42.7 | 0.361 | 2.49 | `8f16fe73…` |
| mismatch_4 | source | 18.19–25.45 | 1.426 | 1,2,3,10,11,74,75,83,85,86,87 | 34.8 | 0.052 | 1.47 | `af95007c…` |
| mismatch_4 | a | 18.18–25.43 | 1.582 | 1,2,84,85,86 | 28.7 | 0.056 | 1.47 | `a46553fd…` |
| mismatch_4 | b | 18.17–25.44 | 1.616 | 1,2,3,84,85,86 | 28.4 | 0.056 | 1.48 | `cce0d6b5…` |
| mismatch_4 | c | 18.15–25.45 | 1.648 | 1,2,3,86 | 27.3 | 0.088 | 1.57 | `928dc3e6…` |

Laplacian variance of L at the keyframe frames, source → a / b / c. The subagent's figures and the
main thread's (its own decode of the same mp4s) differ by up to 1.7; the cause is not measured.

| pair, frame | subagent | main thread |
|---|---|---|
| mismatch_6, 15 | 125.0 → 43.1 / 46.8 / 50.2 | 123.9 → 42.1 / 45.9 / 50.0 |
| mismatch_6, 30 | 38.1 → 15.5 / 17.1 / 17.3 | 36.8 → 14.6 / 16.1 / 16.4 |
| mismatch_6, 45 | 18.6 → 12.9 / 12.7 / 12.8 | 17.6 → 11.9 / 12.0 / 12.2 |
| mismatch_4, 27 | 33.9 → 16.9 / 17.0 / 15.5 | 32.3 → 15.4 / 15.5 / 14.2 |
| mismatch_4, 42 | 21.8 → 10.8 / 10.3 / 9.5 | 20.5 → 9.6 / 9.3 / 8.6 |
| mismatch_4, 57 | 31.1 → 24.9 / 24.6 / 23.9 | 29.6 → 23.2 / 22.9 / 22.6 |

Cause, traced on kf_26 (Laplacian variance of 8-bit L at 1344×768): raw keyframe 202.4, after the
upscale and INTER_AREA round trip 85.9, after the Lab match 21.3, composite 49.2. Matching the
standard deviation scales the keyframe's fine detail by the same gain (0.43–0.72 on the skyline band
and the water of mismatch_4). On kf_23 the match raises 18.8 to 48.7, but the composite has 185.7.

What holds:
1. Mean L stays within 0.4 L of the source clip at every keyframe time; each matched keyframe is
   within 0.11 L of its composite (10.7–35.6 L apart before matching, §5.5 exposure table).
2. No stall at a keyframe: the smallest step near each t_k is 0.84–1.03 of its neighbours' mean. The
   listed stalls are the probe's held end frames; the variants remove some (mismatch_4: 11 → 4–6).
3. Fade R² stays at the source's level (0.351–0.361 against 0.360; 0.056–0.088 against 0.052), except
   `keylayer_c` on mismatch_4's frames 0–27: 0.038 → 0.117 as the correction ramps in, at 0.56–0.74 px
   per step, under the 1 px below which R² cannot tell a fade from a decaying motion (§12.13.1).
4. Endpoints: every `report.json` holds `frame0_equals_A`, `last_equals_B` and `untouched_equal_source`
   true (re-checked on the main thread); frames 0, 1, 88, 89 equal the source byte for byte only
   because w is zero there; frames 2 and 87 carry 0.001–0.284 levels of correction.
5. Each clip is byte-identical on two renders; the main thread re-checked the six md5s above.

The first render was wrong and was overwritten (six mp4s, md5s in `agents/B2_report.md`): DIS on
raw L fitted the exposure difference and moved kf_25 by 217.5 px on average (p95 398 px) and kf_23 by
85.0 px. The locally normalised registration moves the mismatch_4 keyframes by 4.49 / 8.79 / 5.94 px
at a corner and raises structure correlation from 0.676 / 0.671 / 0.822 to 0.808 / 0.859 / 0.870. On
mismatch_6 it reaches only 0.522 / 0.611 / 0.403; the DIS residual was dropped on kf_25 and kf_28.

Limits and what was not tried:
1. A colour rule that matches Lab at low frequency and keeps the keyframe's own detail amplitude was
   not rendered; whether a keyframe can add detail under it is open.
2. The chained DIS carry reaches up to 43 frames; its error is not measured beyond the absence of a
   stall or a mean-L jump.
3. Whether the redrawn clouds of kf_23 and kf_25 read as invented content rests on structure
   correlation (0.52, 0.40) and the subagent's eye only.
4. `layered_diag.py` (seam, outline, rest) was not run: it imports the working-tree probe.

### 12.20 Owner picks on round 6 and the directions that follow (2026-09-28, 22:43 UTC; `benchmarks/runs/2026-09-28/layered_r6/layered_picks.json`; verbatim in DECISIONS 2026-09-29)

Result: `auto_r6` is picked as closer on mismatch_6, mismatch_5 and mismatch_3; no clip is picked on
mismatch_4, mismatch_1, mismatch_7 and mismatch_2. The duplicate is gone by the owner's eye ("R6
doens't have double building anymore"), and what replaced it on the two skyline pairs is rejected:
"some form of reveal with solid margin , it looks pretty 2d and fake, nothing is transforming
there". The keyframe clips invent too much on mismatch_6. Generated content is allowed as a helper,
the layer source goes to the merged source with SAM 3, and the five automatic pairs stay automatic.

| pair | closer | boxes (one picture / transforms / nothing invented) |
|---|---|---|
| mismatch_6 | `auto_r6` | `layered_r5_flow` yes/yes/yes; `layered_r6` yes/yes/no; `auto_r6` yes/yes/no; `keylayer_b` no/yes/no; `keylayer_c` yes/yes/no |
| mismatch_4 | no pick | `layered_r5_stagger` yes/yes/yes; `layered_r6` yes/yes/yes; `auto_r6` yes/yes/yes; `keylayer_b` yes/yes/no; `keylayer_c` yes/yes/no |
| mismatch_1 | `none` | `auto_r5` no/yes/yes; `auto_r6` no/yes/yes |
| mismatch_7 | `none` | `auto_r5` no/yes/no; `auto_r6` no/yes/yes |
| mismatch_5 | `auto_r6` | `auto_r5` no/yes/yes; `auto_r6` no/yes/yes |
| mismatch_3 | `auto_r6` | `auto_r5` yes/yes/yes; `auto_r6` yes/yes/yes |
| mismatch_2 | `none` | `auto_r5` yes/yes/yes; `auto_r6` yes/yes/yes |

The owner's notes, verbatim:
- mismatch_6: "auto_r6 looks interesting but a bit messy in some boudaries ( e.g tree in B and air conditioner on top closer to finish) compared to layered . All keylayers in this example are inventing too much stuff , but the main problem , transitions between states are just too discreet and dirty."
- mismatch_4: "auto_r6 here looks marginally better they layered_r6 and  layered_r5_stagger but still many critiques apply same as in mismatch_6"
- mismatch_1: "here auto_r6 looks better then auto_r5 but r5 simply looked horrible, so not much of an achievement. R6 doens't have double building anymore but instead you just do some form of reveal with solid margin , it looks pretty 2d and fake, nothing is transforming there, you simply replace buidling in A with cityscape from B via gradual reveal from the bottom"
- mismatch_7: "here auto_r6 looks better then auto_r5 but r5 simply looked horrible, so not much of an achievement. R6 doens't have double building anymore but instead you just do some form of reveal with solid margin , it looks pretty 2d and fake, nothing is transforming there, you simply replace buildings in A with cityscape from B via gradual reveal from the bottom. But in this case it is even worse than in mismatch_1, because as i said before, in earlier responses. You really got it somewhat right in benchmarks/runs/2026-09-23 (morph_2s) that zoom preserved buidlings shapes acrooss transitions ( because those are really same buldings ) and morphed stuff around them even clouds. Problem was that it had huge number of visual artifacts, noise , borders etc , but idea was cool. Check if you can iprove and generalize than using all our recent reserches and tests."
- mismatch_5: "i see very marginal improvement compared to r5, still very abstract transition , in parts of image still looks more like simple crossfade / luma transtions than anything else to me  "
- mismatch_3: "r6 marginally better but what i don't like is an effect for some objects to be very crudely cut out of background with rough edges , looks like cheap 2d animated photoshop work , conceptually though - looks promising with all this objects and people shuffling. Duplicating objects in start - finish are gone too so some improvement."
- mismatch_2: "r6 marginally better but what i don't like is an effect for some objects to be very crudely cut out of background with rough edges , looks like cheap 2d animated photoshop work , conceptually though - looks promising with all this objects and people shuffling. Duplicating objects in start - finish are gone too so some improvement."

12.20.1 The owner's message of 2026-09-29 (verbatim): "answered in `benchmarks/runs/2026-09-28/layered_r6/layered_picks (1).json` . ( for you first 4 Questions) ; 5) -  keep them automatic , but answer what is the difference for edited score? ; 6) Yes , i am up to any realistic ( for a given context ) generated content as long as it serves as a helper to fill stuff, to facilite with interesting transitions , keeping 50+% of objects original and consitnet between frames and not inventing completely new objects, but anything that helps with all kinds of tranformations are welcome, again remember our main goal,  surprise me, we must be able to achieve consitency with transtion from anything to anything , so feel free to try all approaches. 7 - all layer examples from `merged v3 (+ SAM 3)` look really cool and accurate to me, lets go this way.  Record everything and prepare for next session , we are out of context almost"

12.20.2 Reading, pair by pair and not generalised.
1. mismatch_1 and mismatch_7: the measures of §12.17.5 read the duplicate as gone and the owner
   confirms it, but one solid shape that grows from the bottom (`mix: "shape"`, §12.17.3) with a
   ground that travels 36 and 14 px (the gain of backlog T23) reads as a reveal. No measure of
   round 6 saw that: the share of a frame's change that a moving outline explains is not measured.
2. mismatch_7: the owner names the clip `benchmarks/runs/2026-09-23/mismatch_7/morph_2s`
   (`transitions.py`, class A, `homography+dis`, 70 sparse inliers, mean certainty 0.053, 2 s) as
   the right idea: "zoom preserved buidlings shapes acrooss transitions ( because those are really
   same buldings ) and morphed stuff around them even clouds", with "huge number of visual
   artifacts, noise , borders". The layered probe matches elements by label, position, size and
   depth and never by what the pixels show (§12.17.9 item 2).
3. mismatch_6 and mismatch_4: `auto_r6` is "a bit messy in some boudaries" at the tree and the
   air-conditioning unit. "transitions between states are just too discreet and dirty" names the
   keyframe clips and not the round-6 clips (amended 2026-09-29, 12.20.6).
4. mismatch_5: "still looks more like simple crossfade / luma transtions".
5. mismatch_3 and mismatch_2: the objects are "very crudely cut out of background with rough
   edges"; the shuffling of people and objects is "promising".

12.20.3 Rulings of the message.
1. Generated content is allowed as a helper (question 6): "any realistic ( for a given context )
   generated content as long as it serves as a helper to fill stuff", "keeping 50+% of objects
   original and consitnet between frames and not inventing completely new objects". This opens
   the generated background behind an object (backlog T22). The owner's rule of 2026-09-26
   against full video generation stands.
2. The layer source is the merged source with SAM 3 (question 7, `layers_v3`, §12.18): "lets go
   this way". `--auto3` reads `layers_v2` as of 2026-09-29; the change is round 7's first step.
3. The five pairs with automatic clips only stay automatic (question 5).
4. "surprise me"; "transtion from anything to anything"; "feel free to try all approaches".

12.20.4 My answer to "what is the difference for edited score?". An automatic score is written
by fixed rules that are the same for every pair: which elements become layers, how they are
matched, every window and every threshold. An edited score is that file changed by hand for one
pair: on mismatch_6 the clouds are a layer of their own that turns into parts of the night sky,
the tree crown's matte has depth thresholds chosen for that photo, and the windows are set by
hand. An edited score shows what the mechanisms reach on a pair; an automatic one shows what they
reach on a pair nobody tuned. On mismatch_6 the owner picked the automatic clip over the edited
ones, though it lacks the "nothing invented" tick that `layered_r5_flow` has; on mismatch_4 he
calls it "marginally better" and ticks the same three boxes for both.

12.20.5 Round-7 targets, in the owner's words: "nothing is transforming there" and "reveal
with solid margin" (mismatch_1, mismatch_7); buildings that are "really same buldings" keep
their shapes while the rest morphs around them (mismatch_7), "improve and generalize"; "a bit
messy in some boudaries" (`auto_r6` on mismatch_6, the same on mismatch_4); "crudely cut out of
background with rough edges" (mismatch_3, mismatch_2); "simple crossfade / luma transtions"
(mismatch_5).

12.20.6 Amendment, 2026-09-29. I asked which clips "transitions between states are just too
discreet and dirty" names on mismatch_6. The owner (verbatim): "this was meant for keylayers samples, not for r6s".
The sentence is a verdict on `keylayer_b` and `keylayer_c`, where a state is one of the three
generated keyframes. It is not a target for `auto_r6` or `layered_r6`. mismatch_4's "many critiques
apply same as in mismatch_6" then carries the boundaries of `auto_r6` and the keyframe clips. The
first version of 12.20.2 item 3 and of 12.20.5 listed it as a round-7 target for both pairs.

### 12.21 Round 7: a measure of what explains a frame's change, the same buildings keep their shapes, a ground whose outline travels with its content, generated backgrounds (2026-09-29; page `benchmarks/runs/2026-09-29/layered_r7/index.html`; scores `scores/auto/<pair>_v4.json`)

Result: on the two pairs the owner called a reveal, the share of the ground's change that a moving
outline explains falls from 34.3 to 21.2 % (mismatch_1) and from 48.3 to 13.4 % (mismatch_7), and the
share that moving content explains rises from 23.5 to 38.7 % and from 16.8 to 54.3 %. On mismatch_7
the ground follows a map fitted to 74 keypoints the two photos share (0.81 px), so the towers keep
their shapes. On mismatch_3 and mismatch_2 the place an object leaves shows a generated background,
and the outline of an object is 1.01–1.33 times its smoothed length (round 6: 1.08–2.14). Not met:
mismatch_5's crossfade has no change, the boundaries on mismatch_6 and mismatch_4 changed only
through the elements, and 21 % of mismatch_1's ground still changes by a moving outline. Seven clips
are byte-identical on two runs; the 34 md5s of rounds 1–6 are unchanged on the final probe (md5
`54e9ee97…`, 3,711 lines); nothing in `transitions.py` changed. Ungraded as of 2026-09-29.

12.21.1 The measure `change` (`scripts/research/layered_diag.py change`). A frame is the sum over
its parts of visibility × content, so a step between two frames is exactly the sum of (mean
visibility × change of content) and the sum of (mean content × change of visibility). A part is a
layer; a `morph_to` layer in mid-clip is two parts, the first photo's content and the second's,
each with its weight in the layer's picture (the probe sets `last_parts`). Every part's content
has its own dense flow (DIS, medium preset) between its two pictures. On the luminance at a
960-px long side, per pixel:

| share | what it counts |
|---|---|
| `mix` | the change of content that remains after each part's picture is warped back along its flow, and the change of visibility that no flow explains where both photos are present or the visibility changes by under 0.1 per step |
| `reveal` | the change of visibility that no flow explains elsewhere: an edge moves and its content does not move with it |
| `motion` | the rest: content travels, and outlines with it |

Controls (`--control`, three scores from the pair's two photos, measured through the same path): a
wipe reads 92.5 % reveal, a crossfade 99.2 % mix, a pan of a quarter of the width 91.4 % motion.
Against the owner's verdicts on the ground or the buildings of five clips:

| clip | the owner | motion / reveal / mix (%) |
|---|---|---|
| `layered_r5_flow`, mismatch_6 | yes / yes / yes | 33.0 / 6.9 / 60.1 |
| `auto_r6`, mismatch_6 | picked as closer | 27.7 / 6.1 / 66.3 |
| `auto_r6`, mismatch_4 | "marginally better", yes / yes / yes | 30.3 / 7.7 / 62.1 |
| `auto_r6`, mismatch_1 | "some form of reveal with solid margin" | 23.5 / 34.3 / 42.3 |
| `auto_r6`, mismatch_7 | "even worse than in mismatch_1" | 16.8 / 48.3 / 34.9 |

The reveal share orders the five clips as the owner did. The mix share is the largest in the
three accepted clips (60–66 %), so the measure does not say that a crossfade inside a layer is a
fault. Two first versions were dropped the same day. One flow between the two composites read
72.2 % of the wipe control as motion: a flow moves a soft edge over a plain sky. One content per
layer read mismatch_1's ground as 54.4 % motion and 11.8 % reveal: a morph layer's picture holds
the outline between its two photos, and the flow explained that outline as motion.

12.21.2 The measure `edge` (`layered_diag.py edge`), per object matte at rest: `rough`, the
length of the outline over the length of the same outline smoothed at 6 px; `soft_px`, the width
of the matte's ramp; `fringe`, the share of the inner rim whose colour is nearer to the colour
outside the matte than to the matte's core (the `rim` measure of round 6, on the colour the layer
carries). Controls: a disc reads rough 1.000, the disc with its outline displaced by up to 12 px
1.354, the disc blurred at 4 px soft 12.6 px. The owner's verdict "rough edges" is on the round-6
mattes, which read 1.22–2.14 on mismatch_3; no verdict exists yet on a smooth matte.

12.21.3 Keys added to `scripts/research/layered_probe.py`, all default-off (the module docstring
carries a paragraph on the round-6 keys and one on these).

| key | on | what it does |
|---|---|---|
| `map: {kind, fallback, keep_if_iou, inward}` | `morph_to` | the layer's field comes from a map in place of the transport between the mattes. `kind: "features"`: the keypoints the two photos share (SIFT, ratio 0.75) within 8 px of the two mattes, a homography by MAGSAC at 2.5 px, held with at least 30 inliers and a sane shape (the constants of `transitions.py`). `kind: "box"`: the axis-aligned map between the two mattes' boxes, anchored at a border both mattes touch, each scale within 1/4–4. `kind: "columns"`: a scale per column (dropped, 12.21.6). `fallback` engages with a line on the log |
| `keep_if_iou: x` inside `map` | a layer that follows the scene's flow | the map from the mattes is used only when the flow does not register the two mattes: the first matte pushed along the flow overlaps its target at an IoU under x |
| `known_frame`, `known_px` | `morph_to` with a map | where the field has carried a photo's frame into the canvas, the mattes continue past the frame's edge and the other photo is shown, from `known_px` inside the edge on |
| `inward: share` inside `map`; `ot_border: {"inward": share}` | `morph_to` | only the component of the field that pulls content away from a border falls to zero at that border (backlog T23) |
| `plate.image`, `plate.keep`; `unmix: PLATE` | a plate; an object | the plate's fill is a picture; a kept zone holds the fill at rest too, for an object un-premultiplied against it (built, measured, off: 12.21.6) |
| `shrink: px` | mask rule `element` | the matte ends that far inside the element's mask |

Also new: `--auto4 PAIR` (writes `scores/auto/<pair>_v4.json`, tag `auto_r7`) with `--r7 columns`
(`_v4c`, tag `auto_r7c`) and `--r7 whole` (`_v4w`, tag `auto_r7w`); the report's `morph` block
records the map and the flow's IoU.

12.21.4 The automatic score of round 7 (`auto_score2(..., r6=AUTO3, r7=AUTO4)`). Matching and
every rule not named here are round 6's.
1. The elements come from the merged layer source with SAM 3 (`benchmarks/runs/2026-09-28/layers_v3`,
   §12.22; the owner's ruling of 2026-09-29).
2. The ground under a sky takes `map: {features, fallback box, keep_if_iou 0.7, inward 0.08}`
   and `known_frame`. The threshold 0.7 lies between the flow's IoU on the two accepted pairs
   (0.842, 0.829) and on the two reveal pairs (0.601, and mismatch_7 takes the features). A ground
   that melts into the sky (mismatch_5) and the rest of a scene with no sky (mismatch_3,
   mismatch_2) keep round 6's fields.
3. The matched clouds are one layer (round 6: up to three, each cut against the others).
4. A plate takes the generated background of its photo where one exists
   (`benchmarks/runs/2026-09-29/plates/<photo>/plate_agree.png`, §12.23) and a zone 8 px wider than
   the object's matte.
5. An object's matte is its element's mask shrunk 3 px and blurred 2 px, with no guided filter; an
   object takes `map: {features, fallback ot}`. On the 16 object mattes of mismatch_3 the guided
   filter of round 6 (r 20, two passes) reads rough 1.46 and fringe 15.3 % (medians), the mask
   blurred 2 px 1.06 and 33.7 %, the mask shrunk 3 px and blurred 2 px 1.04 and 20.6 %.

12.21.5 Results, round 6 → round 7 (`layered_diag.py`, the final probe). Shares: motion / reveal /
mix of the ground's or the rest's region. Fill seen: the largest share of the canvas where a fill
is what the viewer sees (on mismatch_3 and mismatch_2 in round 7 the fill is the generated
background). At rest: the largest difference from the photo in the two frames beside each
endpoint.

| pair | the ground's field in round 7 | travel px | shares (%) | fill seen (%) | at rest, levels | md5 of `auto_r7` |
|---|---|---|---|---|---|---|
| mismatch_1 | box, 1.61 × in height (the flow's IoU 0.601) | 36 → 124 | 23.5 / 34.3 / 42.3 → 38.7 / 21.2 / 40.1 | 5.9 → 10.2 | 3 → 3 | `8eeb239a…` |
| mismatch_7 | features, 74 inliers of 139, 0.81 px | 14 → 227 | 16.8 / 48.3 / 34.9 → 54.3 / 13.4 / 32.3 | 12.8 → 11.2 | 8 → 7 | `c3ba476d…` |
| mismatch_6 | round 6's flow kept (IoU 0.842) | 40 → 46 | 27.7 / 6.1 / 66.3 → 31.9 / 5.9 / 62.1 | 3.4 → 3.6 | 2 → 2 | `e0b588c5…` |
| mismatch_4 | round 6's flow kept (IoU 0.829) | 117 → 110 | 30.3 / 7.7 / 62.1 → 29.7 / 7.9 / 62.4 | 3.7 → 4.2 | 42 → 44 | `bb70cc2f…` |
| mismatch_5 | the ground melts into the sky (round 6) | 74 → 79 | 41.9 / 5.6 / 52.5 → 40.1 / 6.2 / 53.7 | 3.9 → 3.9 | 13 → 12 | `6691169d…` |
| mismatch_3 | the rest follows its surfaces (round 6) | 70 → 61 | 36.2 / 3.6 / 60.2 → 34.4 / 3.4 / 62.3 | 13.7 → 12.4 | 0 → 0 | `ffe2818a…` |
| mismatch_2 | the rest follows its surfaces (round 6) | 20 → 22 | 24.6 / 3.2 / 72.2 → 21.1 / 2.3 / 76.6 | 5.0 → 3.6 | 0 → 0 | `049c60f9…` |

Object mattes (`edge`), round 6 → round 7: mismatch_3 rough 1.22–2.14 (median 1.54, 18 mattes) →
1.01–1.33 (1.03, 16 mattes), fringe median 17.1 → 20.3 %, ramp 21.4 → 6.2 px; mismatch_2 rough
1.08–1.17 → 1.03–1.04, fringe 24.2 → 21.2 %. On mismatch_4, mismatch_5 and mismatch_6 the clip
equals the round-6 rules on the new elements: a subagent's render with the round-6 probe frozen
at `0f97537` has the same md5s (§12.22). Timings (M3 Pro, CPU, beside a regression run): prep
5.3–29.3 s, render 28.8–103.3 s (mismatch_3, eight drawn objects).

12.21.6 Tried and dropped, fields.
1. The ground steered by element maps from the mattes' boxes, blended at 0.04 × the long side,
   bend cap on: the field's bend stood at 3.13 and the office building of mismatch_1 leaned and
   fanned out (by my eye on frames 28–40, `benchmarks/runs/2026-09-29/look/m1_try1.jpg`).
2. The same blended at 0.012 × the long side with no cap: the field folds beside the building
   (swirls on frames 28–40, `look/m1_try2.jpg`).
3. The column map (`kind: "columns"`): bend 4.17 and 1.34, IoU of the pushed matte 0.569 (box:
   0.675), reveal 22.1 % (box: 21.2 %); roofs turn wavy (`look/m1_columns.jpg`).
4. One layer for the whole frame on mismatch_7 (`--r7 whole`): the first photo's frame, carried
   into the canvas, stands in the sky as a rounded rectangle from 0.7 s to 1.8 s
   (`look/m7_whole.jpg`). The measure reads 26.5 / 0.0 / 73.5 and does not see the rectangle: it
   is a change of the mix, not of a matte.
5. Three cloud layers from the new elements on mismatch_7: seams between the cloud layers (by my
   eye, `look/m7_try1_f42_f50.jpg`). Between that render and the final one the sky's reveal share
   fell from 23.6 to 13.7 %; the two renders also differ in which layers make the sky's flow.

12.21.7 Tried and dropped, objects.
1. An object un-premultiplied against the generated plate (`unmix`, `plate.keep`): on mismatch_3
   the mattes read rough 2.0–4.3 and fringe 21–71 %, and the frames beside the endpoints stood
   0.42 and 0.49 levels off the photos. A generated background is not the photo's own background
   at the object's edge, and the opacity the un-premultiplication needs rises wherever the two
   differ.
2. The plate matched in colour over every pixel outside the zone (`plate.png`): dark discs about
   40 px across inside the zone on mismatch_3 (§12.23).

12.21.8 Limits of the result.
1. mismatch_1: the pushed ground overlaps its target at IoU 0.675, and the rest of the second
   photo's skyline still comes up inside a growing shape (reveal 21.2 %). A map that registers
   the two skylines bends the buildings (12.21.6 item 3); none was found that does both.
2. mismatch_1: the fill seen in the sky rises from 5.9 to 10.2 % of the canvas at the largest;
   the ground travels farther and uncovers more of the sky's fill.
3. mismatch_7: a thin blue rim along some cloud edges and a pale pink band above the skyline at
   the right between 1.0 s and 1.8 s (by my eye); no measure reads either. The second photo's
   buildings at the left and the right appear in place: the first photo holds none there.
4. mismatch_3: the flag (group object) is matched to the window of the second photo (group
   opening, 16.1 % of the canvas, cost 1.048) and drawn as an object; the layer grows into a large
   patch between 1.2 s and 1.8 s (backlog T29).
5. The fringe of the object mattes rose from 17.1 to 20.3 % (median, mismatch_3): the shrunk
   matte carries more of the place the object left than the filtered one.

12.21.9 Not done in this round.
1. mismatch_5's crossfade and the bridge with no rule of its own (target 5 of the handover).
2. The boundaries of `auto_r6` on mismatch_6 and mismatch_4 (target 4): no rule changed; the
   elements did.
3. The cause of mismatch_4's 44 levels in its last interior frames.
4. The join rule for small elements (§12.22) is not in the score.

### 12.22 The layer source with SAM 3 behind the automatic score (2026-09-29; outputs `benchmarks/runs/2026-09-29/e4/`; an Opus 5.5 subagent, re-checked on the main thread)

Result: the merged layer source with SAM 3 reproduces byte for byte on 24 of 24 photos, and the
round-7 automatic score reads it (`AUTO4["layers_dir"]`); by match cost it is a gain on
mismatch_7 and mismatch_1 and a loss on mismatch_3 and mismatch_6. The owner's ruling of
2026-09-29: "all layer examples from `merged v3 (+ SAM 3)` look really cool and accurate to me,
lets go this way". `--auto3` still reads `layers_v2`, so the round-6 clips keep their md5s.

12.22.1 Determinism. A second run of `layer_merge.py --routes gdino_sam2,sam3` on the 24 photos
(`e4/layers_v3_run2`, offline, the old source's stage reused by `--skip-base`): `layers.npz` and
`layers.json` equal `benchmarks/runs/2026-09-28/layers_v3` on 24 of 24 (`cmp`, repeated on the
main thread: 48 of 48 files), 0 socket attempts in 24 `timing.json`, hub bytes 12,310,035,528
before and after. Per photo 61.3–99.6 s (median 70.4; SAM 3 alone 45.6) beside the main thread's
jobs, peak RSS 11.55 GB. The run does not re-prove the old source's stage; §12.18 did on 14 photos.

12.22.2 The matching from `layers_v3` against `layers_v2` (`auto_score2`, round-6 rules; elements
first / second photo; mean cost over the matched groups).

| pair | elements | matched groups | mean cost | what changed |
|---|---|---|---|---|
| mismatch_1 | 34 / 16 → 59 / 63 | 5 → 3 | 0.606 → 0.384 | one building of 1.25 % of the canvas collects 13 elements of 12.75 % |
| mismatch_7 | 17 / 18 → 37 / 35 | 4 → 5 | 0.479 → 0.334 | every building goes to a building |
| mismatch_4 | 14 / 10 → 22 / 28 | 4 → 5 | 0.551 → 0.548 | the left skyline is two groups |
| mismatch_6 | 22 / 6 → 38 / 9 | 2 → 3 | 0.856 → 0.901 | every building of the first photo goes to a tree: the second photo's one building stands 0.60–0.84 of the diagonal away, past `max_dist` 0.35 |
| mismatch_3 | 59 / 48 → 75 / 56 | 15 → 19 (10 drawn) | 0.498 → 0.570 | a flag is matched to a window at cost 1.048 (backlog T29) |
| mismatch_2 | 5 / 17 → 7 / 22 | 3 → 5 | 0.754 → 0.667 | a tree is still matched to a building (0.942) |
| mismatch_5 | 23 / 7 → 38 / 9 | 0 → 0 | – | the second photo holds no element over 0.004 outside its sky |

12.22.3 The grain. Of the 34 building elements of mismatch_1_F, 26 are SAM 3 masks and 8 are what
the label map leaves; 23 lie under `min_share` 0.004, so the matcher never considers them. Across
the 24 photos 77 of 134 building elements lie under 0.004. By the subagent's eye on five overlays
the SAM 3 elements are whole buildings and the label map's remainders are roof strips or blocks
that span several buildings (up to 14.8 % of the canvas); no reference exists (UNVERIFIED). A join
rule was measured and is not in the score: a surface element under 0.004 joins the touching
element of its group whose median disparity lies within 0.10. It takes the building elements of
the 14 mismatch photos from 123 to 82 and mismatch_1's mean cost to 0.303; the matches of
mismatch_2, 3, 5 and 6 stay the same; on mismatch_1_F it joins towers a viewer sees as separate
(the subagent's eye on `e4/overlays_v3j/mismatch_1_F_building.jpg`).

12.22.4 A cross-check. The subagent rendered the seven scores from `layers_v3` with the round-6
probe frozen at `0f97537`. Its clips of mismatch_4, mismatch_5 and mismatch_6 have the md5s of the
main thread's `auto_r7` clips (`bb70cc2f…`, `6691169d…`, `e0b588c5…`): on these three pairs round
7 changes the elements and nothing else.

### 12.23 Generated backgrounds for the objects' places (2026-09-29; `benchmarks/runs/2026-09-29/plates/`; `research/keyframe-prompting.md §5.6`; an Opus 5.5 subagent on the second machine, re-checked on the main thread)

Result: FLUX.2 klein 9B at Q8_0 made one background per photo of mismatch_3 and mismatch_2 with
the named objects removed, and the probe shows it where an object has moved away: on at most
12.4 % of the canvas on mismatch_3 and 3.6 % on mismatch_2 (round 6 showed a smooth fill on 13.7
and 5.0 %). The owner's ruling of 2026-09-29 allows it under three conditions: "realistic ( for a
given context )", "keeping 50+% of objects original and consitnet between frames", "not inventing
completely new objects". Ungraded as of 2026-09-29.

12.23.1 The runs. Seed 20260926, 4 steps, cfg 1.0, the photo at the probe's canvas as the one
reference, outputs 1344×1008 (mismatch_3) and 608×800 (mismatch_2). Wall 89–136 s and 34–54 s;
MemAvailable 34.8–36.1 GiB before, 15.60–17.93 GiB at the lowest. One run repeated is
byte-identical (sha256 `8533f5fb…`, read again from the main thread). One run at 1920×1440 failed
inside the recipe's `--max-vram 20` budget (5,298 MB needed, 5,274 MB available); host memory
stayed at 15.39 GiB or more. The second machine after the runs, read from the main thread at
01:17 BST: no hold file, 0 containers, 34 GB available, `~/keyframes` 44 GB. The seven prompts
are verbatim in DECISIONS 2026-09-29 (Track B3) and in the prompting note.

12.23.2 Screening (`plates/screen_plate.py`; the layer source run on the plate counts the
elements of the object groups of at least 0.004 inside the objects' zone).

| photo | zone, share of the canvas | objects in the zone, photo → plate | what stays |
|---|---|---|---|
| mismatch_3_S | 54.1 % | 28 → 1 | a person of 0.4 % |
| mismatch_3_F | 39.2 % | 17 → 2 | the long sofa, which stands in the photo too, and a cushion |
| mismatch_2_S | 54.2 % | 1 → 0 | nothing |
| mismatch_2_F | 59.0 % | 7 → 5 | the painted bird and the yellow pot (named in the prompt, kept), the seat and two pillows |

The control reads the photo's own objects (28, 17, 1, 7) and 2–3 objects on a smooth fill, so
counts of 2 or less are within the detector's noise. The zone is the union of every object
element of the photo; the probe shows the plate only where a drawn object has left, which is the
12.4 and 3.6 % above. Three zones cover more than half of their photo: the first condition of the
ruling is the owner's to judge.

12.23.3 What the main thread took and what it did not. The plate the probe reads is
`plate_agree.png`: matched to the photo in colour over the outside pixels that agree with it
within 10 L*. The match over every outside pixel (`plate.png`) draws dark discs about 40 px across
into the zone on mismatch_3, because objects just outside the zone differ from the plate; the
`plate_agree.png` variant pays with a larger step at the zone's edge (46.16 against 22.64 L on
mismatch_3_S). Outside the zone a plate stands 4.7–21.0 levels of L off its photo, so a plate
never replaces the photo there. The first three prompts named wrong colours (written from a
channel-swapped view) and klein followed the words: a light wooden ceiling came back blue. By the
subagent's eye the only content that may count as invented is the mural of mismatch_2_F, redrawn
with new painted leaves, and the posters redrawn along the wall of mismatch_3_S.

### 12.24 A one-off on the owner's box photos: the graded approaches on a real repaint, the pick, the mix, the merged clip (2026-10-09; outputs `benchmarks/runs/2026-10-09/fabra/`, gitignored; sheet `benchmarks/2026-10-09-fabra-boxes.md`)

Result: on a real re-shot sequence (seven iPhone HEIC photos of two utility boxes beside a roller
door, 4:5, graffiti → primer → pink → painted trees, shot 2026-09-20 to 2026-10-04) the owner
picked two TR14 variants, `luma` and `melt-soft`, over Reveal's wipe and fade, the tool's seven
presets, the other TR14 variants and the layered probe's automatic clip; a new variant
`luma-melt-soft` combines them, six 2 s pair clips were rendered and joined into one 20.3 s mp4
at 1536×1920 and at the Instagram post size 1080×1350. Nothing in `transitions.py` or `reveal.py`
changed; the variant lives in `scripts/research/tr14_variants.py`. Ungraded as of 2026-10-09 15:00 EEST.

12.24.1 What ran on the triage pair 1→7 (`benchmarks/runs/2026-10-09/fabra/1-7/index.html`, 15 clips, 3 s):

| approach | clips | numbers |
|---|---|---|
| Reveal `align --video`, strict `reshot` | wipe, fade | sift 1452 inliers, 0.59 px, ecc_rho 0.973, 13.3 % changed, confidence 98; 7.9 s; 1524×1920 |
| transitions presets | morph, flow-dissolve, luma, dissolve, snap-morph, iris, wipe | class A, 875 inliers, 0.66 px, certainty 0.614, median disp 31.4 px; 1536×1920; 11–18 s each; morph warping 0.0042, feat 0.431, dissolve_fit 0.058 |
| TR14 variants (RoMa field stubbed by the DIS field) | dis, hold-dis, luma, edge-grow, melt-soft | mask 13.3 %, in-mask disp 25–28 px, wobble 7.0–7.5 px (the photos' own edge 6.28 / 5.42); `dis` = `morph` byte for byte |
| layered probe `--auto4` | auto_r7 | 9 elements per photo, matched building, signboard, road; the boxes in the rest layer; a whole-frame morph |

The layer source's prompts have no word for a utility box, so the thing that changes never became
an element (backlog T32). The owner's words on the page: "I really liked effects in tr14_luma_3s and
tr14_melt-soft_3s verysmooth and elements on boxes flow and transtion more naturally. For final
video, try to mix those two approaches, do a 2s transitions instead of three and do all pairs ( and
then merge to final mp4 clip, suitable for instagram".

12.24.2 The mix. `luma-melt-soft` = the hold field, luma's reveal order inside the changed-region
mask (B appears where A is bright first) and melt-soft's divergence-free swirl on the composited
frame, zero at both ends. On 1→7 at 2 s: md5 6d33188f, edge_ratio 0.1763 (luma 0.1199, melt-soft
0.1802), wobble 7.49 px, endpoints exact.

12.24.3 The six pairs at 2 s (`run_pairs.sh tr14:luma-melt-soft 2`; 14–15 s per pair; endpoints 0.0 / 0.0 on all):

| pair | inliers | mask of canvas | in-mask disp px | wobble px | edge_ratio |
|---|---|---|---|---|---|
| 1→2 | 728 | 20.5 % | 11.84 | 7.70 | 0.243 |
| 2→3 | 658 | 15.1 % | 6.01 | 2.21 | 0.261 |
| 3→4 | 1186 | 17.4 % | 4.58 | 0.59 | 0.182 |
| 4→5 | 1970 | 18.2 % | 21.30 | 8.07 | 0.102 |
| 5→6 | 1566 | 15.8 % | 19.22 | 1.90 | 0.113 |
| 6→7 | 1194 | 25.8 % | 14.20 | 3.95 | 0.170 |

12.24.4 The merge (`merge.py`): 1.5 s on photo 1, 1.0 s on each photo between clips, 2.0 s on
photo 7; 609 frames, 20.3 s. The same photo decoded from two clips differs by 2.5–3.3 levels mean
(0.6–0.7 after a 3 px blur, phase shift under 0.1 px): codec noise, so the hold is a linear blend
of the two decoded endpoint frames and the frame step at every join is 0.00; the largest step in
the clip is 4.77 levels inside the 4→5 transition. Outputs `final/fabra_boxes_1536x1920.mp4`
(md5 cb43ca07…) and `final/fabra_boxes_instagram_1080x1350.mp4` (md5 52836583…), libx264 crf 18.

12.24.5 The chain (the owner's third order of the day, verbatim: "lets try something different, take
`tr14_luma_3s` , but lets drop 3.heic and 4 heic (their open window creates noise) and lets try to
pin and anchor image around left and right box as much as possible so they don;t float and make it
all one smnooth animation instead of several joined transitions , also total clip lengs - 6 sec, 3
sec for all transitions and 3 sec to hold final image"). `scripts/research/chain_luma.py`: photos
1, 2, 5, 6 are warped onto photo 7's full frame by `reveal.run_alignment` (strict; 1312–1995
inliers, 0.58–1.2 px, confidence 86–98), cropped once (canvas 1494×1920), then pinned to photo 7 by
a homography from SIFT matches in the wall ring around the two boxes (the ring: the box grown 35 %,
the box plus 10 px blanked). Measured by phase correlation of each ring against photo 7, the stills
drift up to 1.78 px after Reveal alone (still 6) and within 0.5 px after the pin, on both boxes. A
similarity pin left still 6 at 3.08 px on the left box. Between two pinned stills the field is the
mask-held form with no camera motion, so the boxes' content never moves; the luma order runs inside
the feathered mask. One smootherstep over the four segments (32 / 13 / 13 / 32 frames) or a linear
ease (22–23 each), 90 frames, then photo 7 for 90 frames. Outputs under
`benchmarks/runs/2026-10-09/fabra/chain_final_{smootherstep,linear}/` and `final/fabra_boxes_chain_luma_{eased,even}_1080x1350.mp4`
(md5 7cbc94c7…, c596f9c9…). Ungraded as of 2026-10-09 15:40 EEST.

12.24.6 All seven photos, the tool's `luma`, no crop; the pinned pair with the swirl (the owner's
fourth and fifth orders of the day, verbatim in DECISIONS 2026-10-09 fourth line). The chain keeps
photo 7's full frame (`--crop none`): the other photos cover 94.8–98.1 % of it, and a pixel none of
them covers keeps its last known content (the fill reaches at most 3.1 % of a box, still 5, right
box). `--variant tool-luma` runs the tool's `luma_mask` over the whole frame, no field. Six segments
under one smootherstep get 27 / 10 / 8 / 8 / 10 / 27 frames; the frame step peaks at 12.9 levels in
the 8-frame 3→4 step (the open roller door), 7.7 with the linear ease. The pinned 1→7 pair with the
luma reveal and melt-soft's swirl inside the changed region (`tool-luma-melt-soft`): still 1 within
0.1 px of photo 7 on both rings; `final/fabra_boxes_pair17_luma_melt_1080x1350.mp4` (md5 7b9a2bdc…),
beside the TR14-luma form of the mix (e52fa072…). The drift measure subtracts phaseCorrelate's
self-reading (0.5 px on this pair's windows). Ungraded as of 2026-10-09 15:55 EEST.

12.24.7 The `draw` variant (the owner's sixth order of the day, verbatim in DECISIONS 2026-10-09
fifth line: "really gradual and elaborate drawing process on those boxes", the luma and melt clips
"too crude and global", the chains with "hard jumps and visible cuts and stops", the boxes that
"still shift a little"). Three changes answer the three complaints. The background outside the box
zone is one slow dissolve from photo 1 to photo 7, so nothing outside the boxes ever steps. Inside
the zone each repaint spreads as a soft irregular front ordered by the new paint's edges, the old
coat's brightness and noise, and consecutive repaints overlap by 0.35 of a step, so a pixel's state
changes once per repaint through a soft front and the box never changes everywhere at once; the
frame step peaks at 1.7 levels (the luma chains: 4–13). Each box is pinned a second time by its own
ring shift, to 0.06 px (the global pin alone: 0.7 px). The clip's encoder places one keyframe: the
periodic one at frame 250 popped 1.45 levels in a hold. Clips `final/fabra_boxes_draw5_{3s,6s}_1080x1350.mp4`
(md5 060881c6…, 1dd840d9…). Ungraded as of 2026-10-09 16:15 EEST.

12.24.8 The box pinned on itself (the owner's seventh order of the day, verbatim in DECISIONS
2026-10-09 sixth line: "boxes positions and dimenstions need to be even more stable", the last
frames' drawing "visibly jump", "do all 7 images"). The afternoon's pin locked the wall ring around a
box, and the ring measure read 0.06 px; the box stands in front of the wall, and SIFT matches inside
the box (73–875 inliers per still) showed it 14 px off on photo 5 and 8–10 px on photo 6. The pin is
now that in-box similarity, two passes: every box within 0.25 px and 0.04 % of size on every still but
one (0.8 px). Each still's light is matched to photo 7 over the wall rings (Lab mean and spread), and
the same drawing of photos 6 and 7 differs by 9–12 levels inside the boxes instead of 17–18. A pin
from the four outline edges was tried and dropped (a shadow edge on photo 3 fooled it by 9 px). Clips
`final/fabra_boxes_draw7_{3s,6s}_1080x1350.mp4` (md5 e7b1d005…, 4f6ce7dd…). Ungraded as of
2026-10-09 16:35 EEST. Lesson for the tool: a changed object in front of the aligned plane needs its
own pin; the wall's registration says nothing about it.

12.24.9 The owner's verdict on the box clips (2026-10-17, by message, verbatim): "real life task
experiment  is done, I  ended up not fully satisfied ,  I  liked mix of tr14_luma_3s, tr14_edge-grow_3s
and tr14_melt-soft but none of those  was fully ideal, I wanted boxes to be motionless and whole scene
as consistent as possible with content on boxes very subtly and naturally evolve to show before - after
process of repainting them.  I was unpleasantly surprised how jagged  the layered_auto_r7 version came
out just wipe without respecting edges positions and not fluid at all ( and this is considering the
photos are really close match! ). Do not redraw anything this is simply my feedback." Reading: of the
fifteen approaches on the triage pair (12.24.1) the three TR14 in-mask effects (luma, edge-grow,
melt-soft) are the closest and none is accepted; the layered automatic clip is rejected on this case
(the boxes are no element, backlog T32, so the clip is a whole-frame morph that reads as a wipe); the
chain, `draw` and pin clips of 12.24.5–12.24.8 are not named and stay ungraded; nothing is redrawn.
The wish is a time-varying repaint of the box surface while the boxes stand still: §13.4 item 3.

### 12.25 Owner picks on round 7 (2026-10-17, 12:15 UTC; `benchmarks/runs/2026-09-29/layered_picks_L7.json`, ingested into the page and `sheet.md` the same day; verbatim in DECISIONS 2026-10-17)

Result: no clip is picked on five of the seven pairs; `auto_r7` is picked as closer on mismatch_7
and mismatch_4; on mismatch_6 the round-5 hand clip beats it. The owner's reading of the whole
family: "still at its core 2 separate pictures and flat 2d effect" (mismatch_1); "all variants still
feel like very advanced crossfade" (mismatch_6); "just 2d mixup/melt  of different layers you have
extrancted into one another without single consistent them, The feel is as if you hardcut specific
subjects and then simply linearly move them around in 2d plane. And still do crossfade in background"
(mismatch_3). On two pairs he describes the transition he wants, and both are a camera move that
places one scene inside the other: mismatch_5, "a super out zoom with nice layers and stuff and make
it like sun became very distant and eventually converted to galaxy core and the bridge super fluidly
tranformed into part of galaxy sleeve and stars were  popping , or passing during zoom or before
final image settles"; mismatch_3, "a would zoom out as if people from the first phote are in the
window pane of the second photo and then finalize ttransition in some creative manner". His caveat:
"This whole pair shows how subjective each mismatch case can be and how much artistic direction it
requires". His message with the file: "i feel like we are make small incremental fixes but we are
stuck conceptually".

| pair | best | boxes (one picture / transforms / nothing invented) |
|---|---|---|
| mismatch_1 | none | auto_r6 –/yes/yes; auto_r7 –/yes/yes |
| mismatch_7 | auto_r7 | morph_2s yes/yes/yes; auto_r6 –/yes/yes; auto_r7 –/yes/yes |
| mismatch_6 | none | layered_r5_flow yes/yes/yes; auto_r6 yes/yes/yes; auto_r7 yes/yes/yes |
| mismatch_4 | auto_r7 | layered_r5_stagger yes/yes/yes; auto_r6 yes/yes/yes; auto_r7 yes/yes/yes |
| mismatch_5 | none | auto_r6 –/yes/yes; auto_r7 –/yes/yes |
| mismatch_3 | none | auto_r6 –/yes/yes; auto_r7 –/yes/yes |
| mismatch_2 | none | auto_r6 –/yes/yes; auto_r7 –/yes/yes |

The notes, verbatim:
- mismatch_1: "r7 is marginally smoother but they still seem like hiden wipe , just a bit fancier as you wipe along actual buidlings skyline edges and clouds so it is a bit more subtler, still at its core 2 separate pictures and flat 2d effect "
- mismatch_7: "r7 is marginally better than morph and better than r6 but sky still seem like hiden crossfade , just a bit fancier as you wipe along actual cloud edges and clouds so it is a bit more subtler, worth than morph ( altough morph as i asaid before has really dirty clouds as well ,but at least there something happens in cloud details ) . Building do attempt to tranform , albeit quite dirty except from two main ones ( but they already did this in morph ( kept their shape correctly through transition)  so no improvement here) "
- mismatch_6: "r7 is actually more dull and less smoother than r5_flow , more flat and more ugly edges around content (e,g bottom tree) , all variants still feel like very advanced crossfade"
- mismatch_4: "r7 is a bit better then previous ones, but i don't like that skyline transforms in weird wavy pattern, also final sun has weird oval shape before settle, but skyline at least a bit more uniform"
- mismatch_5: "no improvement here , the context is completely disregarded here , sun tries to become center of the galaxy in weird way dropping down. I would expect ( and i  understand that this is very specific  non -generalizable taste pick and core of the problem we are trying to solve!!!) that in this case you would do a super out zoom with nice layers and stuff and make it like sun became very distant and eventually converted to galaxy core and the bridge super fluidly tranformed into part of galaxy sleeve and stars were  popping , or passing during zoom or before final image settles. This whole pair shows how subjective each mismatch case can be and how much artistic direction it requires  "
- mismatch_3: "both are just 2d mixup/melt  of different layers you have extrancted into one another without single consistent them, The feel is as if you hardcut specific subjects and then simply linearly move them around in 2d plane. And still do crossfade in background . Here , again , very specific art choice, a would zoom out as if people from the first phote are in the window pane of the second photo and then finalize ttransition in some creative manner "
- mismatch_2: "similar problem to mismatch_3"

Reading, pair by pair, not generalised: (1) round 7's two ground maps (the shared-keypoint
homography on mismatch_7, the one-piece scaling on mismatch_1) lowered the measured reveal share
(§12.21.1: 48.3 → 13.4 % and 34.3 → 21.2 %) and did not change the verdict in kind; a ground that
follows a map is still "2 separate pictures" to him. (2) mismatch_7: the towers' kept shapes are
credited to `morph_2s` of 2026-09-23, "so no improvement here". (3) mismatch_6: `auto_r7` loses to the
round-5 hand clip on smoothness and on the tree's edge; the SAM 3 elements did not help this pair.
(4) mismatch_4: the `morph_to` skyline "transforms in weird wavy pattern" (the transport field's
bend) and the sun "has weird oval shape before settle" (the Gaussian map's anisotropy). (5)
mismatch_5, mismatch_3 and mismatch_2: the fix he names is a camera, one scene contained in a region
of the other and revealed by a pull-back; no layer rule of rounds 1–7 produces that. Round 8 starts
there (§13), and the measure `change` is not a target until it is calibrated on these verdicts
(it read `auto_r7` on mismatch_1 at 21.2 % reveal, which he still calls a wipe).

## 13. The nested camera and the director: why the layered family reads as 2D, what breaks that ceiling, and a flow where a model plans each transition (2026-10-17; Deep design pass; two skeptic passes and a blind planner test applied; subagent reports under `benchmarks/runs/2026-10-17/agents/`, gitignored; probe `scripts/research/nest_probe.py`, page `benchmarks/runs/2026-10-17/nest/index.html`, sheet `benchmarks/2026-10-17-director.md`)

Result: on the two pairs where the owner described the transition he wants (§12.25), both
descriptions have the same framing, which no round built: scene A placed inside a region of scene B
(the sun inside the galaxy's core; the bar behind the lounge's window pane) and one camera pulling
back from "A fills the frame" to "B fills the frame". Both descriptions also have a transformation
at their centre (the bridge becomes a galaxy arm; the people of A become the people of B), and a
camera alone is decoration by the goal statement he confirmed (§11: "a camera move is decoration,
not the transition"). The probe on the page renders the framing and none of the transformation, so
by §11 its two clips are F2 until a transformation exists inside the container; the page says so,
asks the narrower question (is the framing right?) and carries hand-written clips only. A blind
planner test the same day (13.6) found that a vision-language model given only the photos proposes
the owner's mismatch_5 transition in kind (the sun into the core, the bridge deck tilted into the
streak, the glints into stars) without having read his words. Around that, this section ranks the
techniques the repo has built by the owner's verdicts (13.3: closest picks, none accepted), names
what is missing (13.4), reports FLUX.3 image klein (13.5) and designs the director flow (13.6), to
be built renderer-first (13.9).

### 13.1 Diagnosis, from the record

1. Every mechanism of rounds 1–7 composites 2D layers under one fixed camera; the per-layer motion
   is a transport or a map inside the picture plane (§12.1, §12.10.2, §12.21.3). In the clips the
   owner accepted, 60–66 % of the frame change is still a mix inside a layer (§12.21.1). His words
   on 2026-10-17 name both: "flat 2d effect", "very advanced crossfade".
2. The automatic score decides by 18 fixed constants on label, position, area and depth
   (§12.13.6). No model reads the pair. The owner: "how much artistic direction it requires".
3. The three TR14 effects he picked on the boxes change the surface in place (luma, melt-soft,
   edge-grow; §10.4, §12.24) and he still wants the content to "very subtly and naturally evolve".
   Each of the three is an ordered reveal of B's pixels; the `draw` variant (§12.24.7–12.24.8) is
   a per-pixel repaint front and is ungraded.
4. The camera has been an option, never the transition: `--camera` (§2 item 3) was graded 0 of 12
   on 2026-09-25 ("unnecessary pans and basiaclly cross fading"), §11 says "a camera move is
   decoration, not the transition", and "the cameras as a transition" is on the parked list of the
   handover. Those rulings stand. The owner's two descriptions of 2026-10-17 put a camera at the
   frame of the transition and a transformation at its centre; the probe below reopens the parked
   item for these two pairs only, and the reopening is recorded in DECISIONS 2026-10-17 (second
   line) as pending his word on the page (13.8 question 3).

### 13.2 The nested camera, probed on the two pairs (2026-10-17; the framing half; two per-pair branches of one script)

Definition: a plate = B with A pasted into a container (a region of B) by one similarity S_A that
lands A's anchor on B's anchor; camera(t) runs from S_A⁻¹ (frame 0 shows A) to the identity (the
last frame shows B) as a zoom about the fixed point of S_A, geometric in scale under a smootherstep
ease. Nothing slides as a layer. The camera wraps the compositor: every source is re-sampled from its
full-resolution file at every frame, so a magnified B keeps real pixels up to its own size over the
canvas (2× on mismatch_5, 1.33× on mismatch_3); the mattes are canvas-sized and get magnified with
the camera (up to 3.09×). Two rims. `soft` (mismatch_5): A's sky is luma-keyed into B's sky over the
first 45 % of the clip (its alpha falls with its darkness through a band 0.10 wide, so the matte's
edge is an iso-line of the sun's glow); the sun's disc and the bridge band keep their own soft
mattes, the band's ends and bottom tapered (15 % and 10 %), and the tapers fade in with the key so
frame 1 equals A; A's sky colour statistics move toward B's sky by a Lab transfer weighted by
darkness (the glow and the disc keep their colour). `matte` (mismatch_3): A fills the largest
canvas-aspect rectangle of clear glass (no element in front of it), is seen only through the glass
(the window's box minus every element in front of the glass), and B's people enter from the frame's
edge as the camera pulls back. The finish inside the container is a dissolve ordered by A's
brightness over the last 22 % (an existing layer of the grammar, §12.1). One canvas rule changed:
on mismatch_5 A's cover crop is placed so A's anchor sits at B's anchor's relative height (the
tool crops at the centre, which cuts the sun's top). The anchors on mismatch_5 are photometric
(the brightest disc of each photo by a threshold on L), not layer-source elements: the merged source
finds the galaxy's core as four "sun" elements and no star (§12.14 limit 3, 13.6).

| pair | container and anchors | zoom | end scale | render (90 frames, 1920 px) | first / last interior step (levels) | md5, two runs |
|---|---|---|---|---|---|---|
| mismatch_5 | the sun's glow and disc (7.0 % of A; the glow dilated 9.3 %) and the bridge band (rows from 802); A's sky 65.4 % of A, keyed; A's sun centre (1004, 521), r 87 px → B's core (960, 521), r 28 px; zoom centre (939, 521) | 3.09× | 0.324 | 9.1–10.0 s | 0.12 / 0.01 | 74c165eb, 74c165eb |
| mismatch_3 | the clear-glass rectangle 749×562 px at (1128, 136) inside B's window box [584, 0, 1919, 737]; the glass 26.8 % of the canvas; zoom centre (1849, 223) | 2.56× | 0.390 | 6.2 s | 0.25 / 0.02 | e5f51910, e5f51910 |

The §12.4 bar for the frames beside the endpoints is 1 level; the first render of mismatch_3 had a
20.33-level step at frame 1 (B's foreground showed at once under the matte; the frame-0 override hid
it), found by the architecture skeptic from the decoded file. The steps inside the clips peak at 6.0
(mismatch_5) and 38.2 levels (mismatch_3) at the zoom's fastest frames: the step measure cannot
tell a cut from motion, and a 2.56× zoom moves every pixel. B is shown above its own resolution from
the first frames: up to 1.92× on mismatch_3 until 1.8 s (the people enter at that magnification) and
up to 1.54× on mismatch_5 until 1.3 s, in closed form from z(u) = z0^(1−e(u)); the canvas rule says
"never upscaling" (§2 item 2), so this needs a dated decision or a plate at higher resolution.

What the clips lack, against the owner's words and the record (the owner-lens skeptic read the
montages frame by frame; "by my eye" marks a reading, not a measure):
- The transformation. mismatch_5 (2026-09-27, DECISIONS archive): "sun … shrink and transform into
  andromeda bright center in B and the bridge itself rotate and become meteor streak"; 2026-10-17:
  "the bridge super fluidly tranformed into part of galaxy sleeve". In the clip the bridge band only
  shrinks and the sun only shrinks. mismatch_3 (2026-09-27): "people to tranfrom into other people
  from A group to B group … transforming and not just moving it as cheap 2d cutout!". In the clip
  A's wall and crowd shrink as one rigid rectangle behind the glass. By §11 both clips are F2.
- A straight edge of A's frame against B's brighter galaxy glow in the first 0.3–0.5 s of
  mismatch_5, where A's sky is still opaque near its border (the parked failure of 2026-09-29, "the
  carried frame stands in the sky as a rectangle"). The key runs ahead of the camera to shorten it;
  a content-shaped matte from frame 1 would remove it and would break the 1-level bar wherever A's
  dark sky and B's sky differ by more than a level. The two bars conflict on this pair.
- Two objects at once: from about 2.0 s the sun's disc sits inside the core's glow until the finish
  replaces it (by my eye F1 for about 0.6 s). The anchors lock the centres, not the look.
- A local double exposure at the finish (the last 22 %): the bar's flag and crowd half-transparent
  over B's trees; the sun's disc over the core. His "And still do crossfade in background".
- No parallax (a flat zoom); on mismatch_3 A's pane may read as a poster on the glass as much as a
  distant room (by my eye); the pane keeps A's aspect, with B's own glass beside it.

### 13.3 The machinery, ranked by the owner's verdicts: closest picks, none accepted (the 52-row inventory with every quote and citation: `benchmarks/runs/2026-10-17/agents/inventory_report.md`)

A pick is not acceptance (2026-09-14). Seven techniques carry a pick or a liked sentence and each
one also carries a named defect.

| rank | technique | where | the owner's words (date) | reuse in the director flow |
|---|---|---|---|---|
| 1 | `morph_to`, a layer carried into its counterpart by optimal transport, with the round-5 keys | §12.10.2, §12.13.2 | closer on both hand-scored pairs in rounds 4 and 5; "weird wavy pattern" (2026-10-17) | the transformation inside a container (bridge → arm, crowd → group) |
| 2 | `move_to`, the sun's Gaussian map | §12.1 | "Only Sun movement is cool" (2026-09-27); "weird oval shape before settle" (2026-10-17) | superseded on mismatch_5 by the anchored zoom; stays for a blob with no container |
| 3 | TR14 luma, melt-soft, edge-grow inside the changed mask on the hold field | §10.4, §12.24 | his pick on the boxes (2026-10-09, 2026-10-17: "none of those was fully ideal") | the finish inside a container |
| 4 | the class A homography + DIS morph | §2 | mismatch_7 `morph_2s` three boxes yes (2026-10-17); "dirty clouds" | the engine for related pairs and for a related container |
| 5 | the merged layer source with SAM 3 | §12.18, §12.22 | "really cool and accurate" (2026-09-29); no word for a utility box (T32); the galaxy's core as four suns, no star (13.6) | every element the planner names is snapped to it; the planner corrects it |
| 6 | the in-box feature pin (position and size) | §12.24.8 | ordered twice on 2026-10-09; "boxes to be motionless" (2026-10-17) | the pin of any changed object in front of the aligned plane |
| 7 | the score grammar and the automatic score | §12.1, §12.21 | "remotely looks like right direction" (2026-09-26); "2d mixup/melt" (2026-10-17) | the plan's output format; the pull-back and the anchors are new keys in it |
| 8 | the depth model and the camera dolly | §2 item 3 | liked as an effect, rejected as the transition (2026-09-23/25) | parallax inside the pull-back |
| 9 | FLUX.2 klein 9B keyframes and plates on the second machine | §12.15, §12.23 | "klein 9B looks best" (2026-09-27); every whole-frame use rejected | the helper confined to a container's finish |
| 10 | the stars rule (materialise bright-first) | §12.1 | "i like how stars appear" (2026-09-26) | stars inside the pull-back |

Measures (§12.13, §12.17, §12.21): `change` orders five graded clips as the owner did and reads
`auto_r7` on mismatch_1 at 21.2 % reveal, which he calls a wipe; no measure reads "2d" or "advanced
crossfade". A measure is not a target until it is calibrated on the 2026-10-17 verdicts.

### 13.4 What is missing, ranked by what the owner's words demand (external candidates from `benchmarks/runs/2026-10-17/agents/frontier_report.md`, primary sources read 2026-10-17; none run)

1. A transformation inside the container, which is what makes a nested camera a transition by
   §11: the bridge carried onto B's dust lane and bent toward it (`morph_to` between the two mattes,
   or the log-polar map w = exp(a·z), which bends straight lines into logarithmic spirals;
   `cv2.warpPolar` / `cv2.remap`, seconds on the Mac); A's crowd carried onto B's group by
   `morph_to` on the person elements. Nothing of this exists in the probe. The blind planner's plan
   for mismatch_5 (13.6) is a written specification of it.
2. A semantic correspondence across unrelated scenes, so item 1 knows what becomes what: DINOv3
   patch features (github.com/facebookresearch/dinov3, DINOv3 licence, ViT-S 21M to ViT-L 300M)
   inside label-matched elements, or the planner's named match snapped to the layer source. The
   automatic score matches by label, position, area and depth only (backlog T34).
3. Content that changes in time for a same-scene repaint, for future pairs like the boxes (the
   box experiment is closed by the owner's word: "Do not redraw anything"): strokes fitted to the
   finish photo inside the changed mask and drawn in painting order over the held, pinned plate
   (Stylized Neural Painting, CPU mode, github.com/jiupinjia/stylized-neural-painting, CC BY-NC-SA 4.0
   by its README; Paint Transformer, Apache-2.0, macOS). The existing answer to the same wish is the
   `draw` variant of §12.24.7, ungraded. A stroke render ends on the finish photo only through a
   last blend, which is a crossfade in those frames [INFERRED]; a ΔE test of the stroke renderer on
   one photo alone comes before any clip.
4. Parallax and a tilted container: the depth model's disparity per layer (holes at layer edges,
   T18), or SHARP, Apple's one-photo Gaussian model (arXiv 2512.10685; predicts on MPS; its renderer
   is CUDA-only, so a CPU splat renderer would be ours to write); a `quad` container (a homography
   into a tilted pane); the crop anchor as a canvas option.
5. A model that reads the pair and decides: 13.6, after items 1–2 exist.
6. A generative helper held to a region rather than a whole frame: FLUX.3 klein's multi-reference
   edit (13.5) for a container's finish; Wan VACE masked video-to-video (github.com/ali-vilab/VACE,
   Apache-2.0, 1.3B at 81×480×832) as the only video model with a stated route onto the box
   (stable-diffusion.cpp lists Wan2.1 VACE and a Vulkan backend; mask and control support inside
   sd.cpp UNVERIFIED). Either one re-synthesises pixels inside its region and carries F3 there; the
   owner's 2026-09-26 ruling ("never full video generation") makes VACE a question for him, not a
   plan item.

Also found and not ranked above: alpha matting for the "cheap 2d cutout" rim (no matting model has
been probed; T28); a retiming of any finished clip to constant semantic speed (the Semantic Progress
Function, arXiv 2604.22554, DINO embedding distance per frame, numpy); Framer (512×320, trajectory-
guided inbetweening, CUDA) and Go-with-the-Flow (warped noise, CogVideoX base, "requires GPU") as
motion-controlled video models with no Mac path and an F3 risk on every pixel; every diffusion
morpher surveyed (AlignMorph 2026-09, FreeMorph, DiffMorpher, IMPUS) makes hybrid objects and claims
no exact endpoints, so they are out for whole frames by the F3 rule.

### 13.5 FLUX.3 image klein (research only; nothing downloaded or run; `benchmarks/runs/2026-10-17/agents/flux3_report.md`)

Verdict: a plate and keyframe model with support in stable-diffusion.cpp since 2026-10-15 by that
project's changelog (its Vulkan backend with FLUX.3 is UNVERIFIED), which brings two capabilities
the pipeline can use (multi-reference composition up to 10 references; bounding boxes in the prompt)
and none that answers the owner's verdicts, which are about geometry and time, not image quality.
Adopt it only on a measured side-by-side against FLUX.2 klein 9B on one plate and one keyframe,
after a 512² smoke test on the re-pulled container.

- Sizes (Hugging Face API, 2026-10-17): the bf16 transformer 11,097,404,512 B (distilled) and
  11,076,957,072 B (base); fp8r 6,270,949,144 B; the Qwen3-VL-4B text encoder 8.9 GB bf16; the
  autoencoder 336 MB; the prompt upsampler `flux-3-image-klein-pup` 18,819,722,392 B (a Qwen3.5-9B
  fine-tune, Apache-2.0, not gated). Q8_0 GGUF: `DogukanUrker/FLUX.3-Image-Klein-GGUF` 5,991,734,144 B
  (built and tested with sd.cpp ≥ 8cd731e) and `unsloth/flux-3-image-klein-GGUF` 6,092,755,872 B
  (LPIPS 0.006 against bf16 by unsloth's own test; its card names diffusers, sd.cpp compatibility
  UNVERIFIED); encoder `Qwen/Qwen3-VL-4B-Instruct-GGUF` Q8_0 4,280,406,144 B. The 8-bit set is about
  10.7 GB without the upsampler and about 20.8 GB with its Q8_0 GGUF (9.5 GB plus a 0.6 GB
  projector), against 18.9 GB for klein 9B; the upsampler is not needed when the planner writes
  the caption.
- Licence, recorded: FLUX Kommunity License v1.0 (non-commercial; commercial output under US$5M
  revenue). The distilled, base and comfy repos are click-through gated; on 2026-10-17 the owner's
  token read the base repo and got "requires approval" on the distilled and comfy repos.
- The box: stable-diffusion.cpp merged FLUX.3 klein support on 2026-10-15 (PR #2143, release
  master-968-8cd731e; distilled runs at `--cfg-scale 1.0 --steps 16`); the pinned container
  `sha256:0ab8e0e0…` predates it and needs a re-pull (backlog T35). 16 steps against klein 9B's 4:
  a keyframe at 1344×768 would take about 120 s against 68 s if step time scales with parameters
  [INFERRED, not measured]. ROCm 10.1 lists gfx1151 under Ubuntu 26.04 or 24.04 with kernel 7.0;
  the box runs Ubuntu 25.10 and kernel 6.17, so the diffusers and ComfyUI paths are untested there.
  The reference code pins CUDA 13 and vLLM and runs on neither machine as shipped.
- The Mac (36 GB): an MLX 8-bit build (`VisualInference/FLUX-3-Image-Klein-MLX-8bit`) reports
  115 s per image and 14.3 GB peak at 1024² on an M4 Pro; diffusers on MPS is UNVERIFIED.
- The interface (reference code, commit bfc8889): every image starts from pure noise; references
  steer it through a separate token stream; no mask, no inpainting, no strength; two or more
  references are each cut to 1 MP. Boxes are text in the prompt on a 0–1000 grid ("Boxes guide
  placement and scale; they do not constrain pixels to a hard mask"; boxes under about 40×25 px
  often fail); the pixel restoration that keeps unedited regions exact is a BFL API step absent
  from the open code. One third-party test (kingy.ai, upsampler off, Fal endpoints) measured 6.23 %
  of pixels outside the edited region changing by over 8 levels (Nano Banana 1.44 %). Neither this
  model nor klein 9B has a mask: each renders a whole frame and our code composites the region.
- The prompt upsampler is required by BFL ("noticeably weaker" without it); since 2026-10-17 BFL
  ships system prompts for an external vision-language model to write the caption instead, so the
  planner model of 13.6 can write it. A network call belongs in a separate prep script with its
  own decision line, never in `transitions.py`.
- Quality: BFL's own +91 Elo (text-to-image) and +70 Elo (editing) over FLUX.2 klein 9B; no
  independent leaderboard entry as of 2026-10-17. On 2026-10-17 the reference code moved its
  sampler shift from 6.93 to 16.0 while sd.cpp and diffusers keep 6.93 (`--flow-shift` overrides).

### 13.6 The director flow (design; nothing built except the probe and one blind test; built after 13.4 items 1–2)

Intent in one sentence: a vision-language model reads both photos and the layer source's elements,
proposes two transition concepts as plans in the score grammar plus two new keys, the deterministic
engine renders each at proxy size, the owner grades and guides on a review page, and the chosen
plan renders at full size with any generative helper confined to a named region.

What it changes and what it does not: the planner chooses among the renderer's actions; if every
action still reads as 2D to the owner, a planner changes which rule is picked, not what he sees
(the owner-lens skeptic, 13.7). So the renderer gains the container, the pull-back and the
transformation inside the container first (13.4 items 1–2), and the planner script is built once
one rendered action is not called 2D. The flow is process; the answer to "stuck conceptually" is
13.4.

The blind test (2026-10-17; an Opus 5.5 subagent given only the six proxies and the element tables
of mismatch_5, mismatch_3 and mismatch_2, with the client's rules and the renderer's actions in its
brief and no access to the owner's words; `benchmarks/runs/2026-10-17/agents/blind_plans.md`):
- mismatch_5, concept 1: "The sun sinks and cools into the galaxy core while the bridge deck pivots
  −19 degrees about it and thins into the satellite streak, the dark truss below it becomes the dust
  lane, and the orange reflection column on the water rotates up and spreads out into the inclined
  galaxy disk, its ripple glints becoming stars." This is the owner's description of 2026-09-27 and
  2026-10-17 in kind, unseen. Concept 2: a swirl winding A's strata into a spiral.
- mismatch_3, concept 1: element-to-element transformations ("everything in A takes a seat": the
  flag's blue band into the blue painting, the wheels into the pine trunks, the fence mesh into the
  woven sofa frames, five people walking into the seated men). Concept 2: a push into A's small
  mural, the painted hills carried onto B's real pines, then a pull-back out of B's glass wall into
  the lounge, "so the mural turns out to be the window": the nested camera, in the other direction
  from the owner's pane.
- mismatch_2: a structure match (the peeking face behind the tree becomes the woman peeking in B;
  the clasped hands rise into the hand holding the phone in the same place).
- It corrected the layer source where it was wrong: the galaxy's four "sun" elements are one core,
  "wall" 9 is a star, the dust lane and the disk are not detected; "fan" 3 on mismatch_3 is the two
  cart wheels.
Pass criterion (frontier report probe 8): the plan names the owner's own matches on 1 of the 2
described pairs. The plans are text; none is rendered; the test says what a planner proposes, not
what the owner will accept.

Stages:
0. Reading (exists): `layer_merge.py` (elements with label, group, box, area, depth, normals),
   `reveal.py align` on the pair (related or refused, inliers), the canvas.
1. Plan (new, `scripts/research/director_plan.py`): inputs are the two photos as proxies of at most
   1024 px, the element tables, the Reveal verdict and an optional owner brief; the output is
   `plan.json` with `reading` (one sentence per photo), `relation` (aligned, themed or unrelated)
   and `concepts` (at most 2). Each concept: `idea` (one sentence), `container` (an `element` mask
   rule with a role: `in` A or B, `rim` soft, matte or quad, or null), `anchors` [{a, b, how}] where
   an anchor is an element id, a box, or a kind that needs no element (`bright_disc` in a box, a
   point with a radius) and is snapped to the layer source by IoU ≥ 0.6 for an element or by
   distance for a point, `pullback` {`ease`, `parallax` off or depth} with the camera derived from
   the anchors (the fixed point and the start zoom follow from S_A; equal anchor scales give a pure
   translation), `transform` [{a → b, by: morph_to or log-polar, window}], `end_effect` (an
   existing dissolve or morph layer in the container's last window, or a helper), `helper` {model,
   prompt, what it must keep} or null, `knobs` [{name, range, default}] and `risk` (F1, F2 or F3
   named). Boxes are stated in one frame (the canvas of the pair; the proxy's scale and the crop
   offset are written into the plan). A concept whose anchors do not snap is shown as "unplaced",
   never rendered. The plan is frozen as a tracked input: model id, temperature 0, a hash of the
   prompt, so a render reproduces from the file (invariant 5 of §1 does not hold for a sampled model,
   and the file is what holds it).
2. Draft (new keys in `layered_probe.py`, default-off, with rounds 1–7 byte-identical through them:
   `pullback` and `anchors`; the camera wraps the compositor and re-samples sources from their files;
   the crop anchor re-crops the element masks or is refused together with A-side element ids; the
   probe of 13.2 is two per-pair branches, not an implementation of the keys). Before any key is
   written, one score file with no code: `morph_to` on an `all` layer with `map: {kind: "box"}` and
   `known_frame: true` already maps A's frame into a box of B and carries B back; if its field reads
   as the camera does, the keys are not needed. Each concept at 960 px, with the concept's text as
   the page's paragraph and its knobs as the question. Every page carries the automatic clip of the
   pair-blind rule in force (the 2026-09-27 rule) or says that it does not and why.
3. Grade: the owner's picks file, as today, with a separate "acceptable as-is" answer. His notes
   and the plan go into the next call as examples (the picks files since 2026-09-26 are that memory).
4. Final: the chosen plan at full size; the helper (klein 9B today, FLUX.3 klein after 13.5's
   side-by-side) renders a whole frame on the box and our code composites the `end_effect` region
   through the container's matte.

The planner model and the network. Three options, all with multi-image input and boxes (frontier
report family 7): Claude (the session's own model, or the Anthropic API; absolute pixel coordinates,
"approximate" by its docs), Gemini through the API (boxes on a 0–1000 grid, polygons), Qwen3-VL on
the box (local, boxes and points; the 4B is already FLUX.3's encoder). The owner holds an OpenRouter
account in another project (`OPENROUTER_API_KEY` in that project's environment); this repo has no
key. Sending a photo to an API cannot be undone, and no research script in this repo calls the
network today (`strix_keyframe.sh` states "no network"; the layer source fetches weights once and
runs offline, T20): the planner script needs the owner's yes on the egress and the providers, a
dated DECISIONS line and a T20-style backlog row before it exists, and it uses the standard library
or a scratch environment (an HTTP SDK in the shared `.venv` is a new dependency, a decision). The
session's own model as the planner moves no photo off the machine beyond what this session already
does. Recommendation: the session's model for the first planned renders; the script after the
owner's yes; Qwen3-VL on the box as the offline option.

Invariants kept: frame 0 is A and the last frame is B; every pixel from A or B (A re-coloured where a
colour path says so) except the declared helper region; the renderer is offline; the planner is a
separate script the operator runs on purpose; nothing enters `transitions.py` before the owner says
so.

The test of the flow with the owner, not run: every pair of the fixture set has a dated description
by him (mismatch_6 in time, 2026-09-26; mismatch_1 and mismatch_4, 2026-09-27; mismatch_2 only
"similar problem to mismatch_3"), so no pair is undescribed. The test is a new pair outside the
seven (inventory gap 10: no held-out pair exists; the handover asks the owner for one), the blind
planner's top concept rendered, his note. The flow is worth building as a script only if that
concept is one he did not ask for and does not call 2D.

### 13.7 Risks, and the two skeptic passes (Opus 5.5 subagents, 2026-10-17; `benchmarks/runs/2026-10-17/agents/skeptic_owner.md` and `skeptic_arch.md`; every objection rated "blocks" is answered above or named here)

- The pull-back without a transformation is F2 by §11 (owner-lens, blocks): the page and 13.2 say
  so; 13.9 builds the transformation first.
- The two clips are hand-written for their pairs (owner-lens, blocks): per-pair branches and
  constants in `nest_probe.py` (the key band 0.10 over 45 %, the 15 % and 10 % tapers, the 13-px
  glow dilation, the 22 % finish), so they are tuning, not proof of a mechanism (§11 amendment); the
  page carries no automatic clip and says so; "the primitive is general" is not claimed.
- The carried frame as a rectangle (parked 2026-09-29): seen in the first render, shortened by the
  key, still expected in the first 0.3–0.5 s of mismatch_5 (13.2).
- The first-frame cut on mismatch_3 (architecture lens, blocks): 20.33 levels in the first render,
  0.25 after the clear-glass pane; the step measure now runs in the probe on every render.
- The schema could not express the probe (architecture lens, blocks): answered by anchor kinds
  without element ids, one coordinate frame, the camera derived from the anchors, and the probe
  named as two branches (13.6).
- The egress of the owner's photos to an API (architecture lens, blocks until decided): named in
  13.6 and 13.8 question 4; nothing is sent until he says yes.
- B above its own resolution during the pull-back (1.92× and 1.54×, 13.2) against the canvas rule.
- The finish is still a local dissolve inside the container (22 % of the clip); two objects at
  once for about 0.6 s on mismatch_5.
- A's pane keeps A's aspect inside B's window; a `quad` container needs a homography path.
- The planner's boxes are approximate (Claude's docs say so); the snap guards it and a concept can
  be lost by the snap; the blind planner also repaired four wrong elements by eye (13.6).
- Where a nested camera has nothing to hold [INFERRED, none measured]: mismatch_1 and mismatch_7
  are the same city (nesting would destroy the shared geometry he credited on mismatch_7);
  mismatch_4 is sun to sun at similar size, so the zoom ratio falls near 1; mismatch_6 asks for a
  vertical, in-time score; mismatch_2 shows no window or container element by the fixture
  description (UNVERIFIED against the layer source; the blind planner proposed a structure match
  there).
- The planner changes the choice, not the vocabulary (owner-lens): 13.9 is renderer-first and the
  concepts are capped at two per pair.
- Refutation kept: the owner liked a camera once as an effect and rejected it as the transition
  (2026-09-25). The difference here is that the camera carries A into B's geometry (the anchors
  lock) and the transformation of 13.4 item 1 happens inside the container; whether that difference
  is visible to him is what the page decides, and nothing on the page is a candidate.

### 13.8 Questions for the owner (each with my recommended answer; also on the page)

1. The two probe clips on `benchmarks/runs/2026-10-17/nest/index.html` show the framing only (the
   camera half of your two descriptions; by §11 they are F2 until the bridge and the crowd
   transform inside the container). Is the framing right, before the transformation is added?
   Recommended: yes on both; 13.4 item 1 is round 8's first build.
2. The page carries hand-written clips only and no automatic clip (the rule of 2026-09-27): waive
   it for this page, or wait for a pair-blind rule? Recommended: waive for this page; the planner
   is the pair-blind route.
3. "A camera move is decoration, not the transition" (§11, 2026-09-26) and "cameras as a transition"
   (parked): reopened for the nested camera with a transformation inside the container, or kept?
   Recommended: reopen for that case only; DECISIONS 2026-10-17 (second line) records the
   reopening as pending your word.
4. The planner: the session's own model for the first planned renders, then a script against the
   Anthropic API or OpenRouter (which model)? Sending your photos to an API cannot be undone: yes
   or no, and which providers? And a held-out pair for the test: a new photo pair outside the
   seven? Recommended: the session's model now; one new pair of your choice; the egress is yours
   to decide.
5. FLUX.3 klein: accept the click-through terms on the distilled and comfy repos, then a 512² smoke
   test on the re-pulled container and one plate and one keyframe side-by-side against klein 9B on
   the box? Recommended: yes, as a measured swap.

### 13.9 Round 8 (renderer-first; order by the owner's answers)

1. Record his picks on the probe page and his answers. 2. The transformation inside the container
(13.4 item 1): the bridge onto the dust lane by `morph_to` or the log-polar map, A's crowd onto B's
group by `morph_to`, on the probe; the blind plan for mismatch_5 is the specification. 3. The
no-code test of 13.6 stage 2, then the keys `pullback` and `anchors` (default-off; rounds 1–7
byte-identical) with parallax by depth as a knob. 4. The correspondence (13.4 item 2) for the match
the transformation needs. 5. The planner's first planned render on a held-out pair (13.6), at most
two concepts, by the session's model unless the owner has said yes to the egress. 6. FLUX.3 klein on
the box after the terms and a container re-pull; the 512² smoke test; one side-by-side.
Reversibility: every item is a research script or a default-off key; nothing in either tool.

### 13.10 The owner's answers and his grades on the probe page (2026-10-17 evening, verbatim)

His picks file `benchmarks/runs/2026-10-17/nest/nest_picks.json` (16:35 UTC): no best, not
acceptable, on both pairs; "nothing invented" ticked, "one picture" and "content transforms" not.
mismatch_5: "zoom out is cool, sun correspondence to galaxy center is  the right direction, its a bit
off center and still too large at the end  + notihing happens to the bridge and we have harsh
transitions and borders around edges of sun but this is starting too look like something, framing
not bad   , also missing Z depth/ parallax when zooming out". mismatch_3: "feedback is similar to
mismatch_5, somewhat right direction , but picture A remains a static tranformed photo with hard
edges , poorly aligned and thematically detached from B and simply crossfades out in the end , zoom
out effect  is nice here and framing not bad , but also missing Z depth/ parallax when zooming out".
Read: the framing is accepted as a direction on these two pairs and nothing else is; six faults are
named (off centre, too large at the end, the bridge unchanged, harsh borders at the sun, no
parallax; on mismatch_3 a static photo with hard edges, poorly aligned, detached, a crossfade).
"Off centre" and "too large" have one cause: the probe's sun was the brightest blob (L ≥ 0.90 of the
maximum), 87 px of a 275 px disc, 130 px above its centre (the disc darkens toward the horizon); the
renderer of round 8 fits a circle to the limb instead (§13.11).

His answers to the five questions of §13.8, by message with the order "continue, finish the design
and ship it":
1. "in these specific cases one camera looks roughly correct" — the one-camera framing stands on
   mismatch_5 and mismatch_3; nothing is claimed for another pair.
2. "What does it mean ?" — the question was not clear. The rule of 2026-09-27 asks every review
   page to carry, beside the hand-tuned clips, one clip from an automatic path that never saw the
   pair, so that a result cannot be tuned to the pair under review. In the director flow the
   planner writes the plan without the renderer's author and the clip is rendered from that plan,
   so the planned clip is this flow's automatic clip; the renderer's own constants (the key band,
   the feathers, the mix windows) are the hand part and the page lists them. The round-8 page says
   so; no waiver is needed.
3. "Same , explaine the question, if camera move is intentional and has a correct artistic sense of
   direction ( like in above examples) it makes total sense, both in 2d and 3d spaces" — recorded
   as the §11 amendment of 2026-10-17: a camera move whose direction carries the idea is the
   transition's spine; the transformation inside it is still required.
4. "yes to both , lets start with current claude code anthropic client that we are working in, can
   add openrouter integration later to compare" — the egress of his photos to a planner model is
   approved, and the planner of record for round 8 is a Claude Opus 5.5 subagent run from this
   Claude Code session (the plans carry the model id, temperature 0, the prompt's sha256 and the
   brief); an API script against OpenRouter is later work (backlog T36). The photos already reach
   Anthropic through this session's own reads.
5. "FLUX 3 - yes , i have acccepted all terms and conditions from my HF account" — his token
   answered 200 on `flux-3-image-klein`, `-base` and `-comfy` at 19:46 EEST (the repository I called
   "distilled" on the page is `flux-3-image-klein`); Track D ran on the box (§13.12).
No held-out pair was named; mismatch_2 (his only words on it: "similar problem to mismatch_3",
2026-09-27) is the nearest thing to one, and its plan was written blind (§13.11).

### 13.11 Round 8: the director's renderer and the first planned renders (2026-10-17 evening; `scripts/research/director_render.py`, plans under `scripts/research/plans/`, page `benchmarks/runs/2026-10-17/director/index.html`, UNGRADED)

What was built. `director_render.py` (research, imports the two tools and the layered probe's
`ot_fields` and `warp_along`; neither tool changed) reads a plan in the grammar of
`scripts/research/plans/SCHEMA.md` and renders one concept: a container in B (`disc`, `quad`,
`rect` or `none`), anchors that attach A to it (`circle_fit` fits a circle to a luminary's limb with
the flat cuts of an occluder or the crop left out and two rounds of outlier rejection; `element`,
`box`, `point`, `rows`; on B `bright_disc`, `element`, `box`, `line` by the principal axis,
`dark_band` as a band darker than its surroundings by a difference of Gaussians), one camera (a
similarity zoom about the fixed point of S_A, or a homography whose four frame corners move from the
quad to the frame), transforms of A's layers (`recede`: a disc contracts about its centre while its
limb softens; `line_to`: a band rotates about the anchor, thins to a width and takes the line's
pixels; `morph_to`: a box-to-box or axis-to-axis affine plus an optimal-transport residual, the
target's pixels revealed inside the moving matte by luma, edge or noise order; `move_to`; `colour`;
`hold`), an end effect (`luma_reveal`, `edge_reveal`) and parallax by the depth model: each source's
pull-back eases by e_p = e + g (d − d_ref) e (1 − e), zero at both ends, so nearer content moves ahead
mid-way without a cut at either end. In a quad or rect container B's foreground (the front groups,
kept where the depth model reads an element nearer than the container by 0.05) is a layer of its
own over a plate filled by `cv2.inpaint`; it starts beyond the frame (a push of exp(2.5 · max(d −
d_ref, 0.3)) at e = 0) and fades in over the first 15 % of the clip, each element moving as one
piece. Knobs: `--set name.param=value`, `name.window=[a, b]`, `name.a_group=person`,
`name.skip=true`, `parallax_sources`, `parallax_gain`, `cont_feather`, `end_scale`. Every resolved
number goes to `info.json`; the first, second and last interior steps and the peak are decoded from
the file. Two runs are byte-identical (mismatch_5 c1 at 960 px, md5 2ccb74a6… twice).

The plans (an Opus 5.5 subagent, prompt sha256 a715f8ed…, saved beside the plans): mismatch_5 and
mismatch_3 with his notes of 2026-10-17 as the brief, mismatch_2 blind. Rank 1 on mismatch_5: the sun
falls away into the core while the deck turns into the streak and the truss sweeps into the dust
lane; on mismatch_3: A in the glass plane, the foreground closing in front, then the wheels to the
trunks, the flag to the painting, the brick to foliage and the crowd stepping through the glass onto
the men; on mismatch_2 (blind): the peeking man shrinks until his eyes sit on the peeking woman's,
B's man and the raised hand hide him as his tree did, and an edge reveal passes the peek on. The
planner's notes name what the grammar could not say (stars in B's own order, a push-in before the
pull-back, landmark warps) in `benchmarks/runs/2026-10-17/agents/planner_r8.md`.

The renders (full size, 3 s, 30 fps; the operator's knobs on each are on the page):

| Clip | Camera | Steps first / second / last, peak | Wall | md5 |
|---|---|---|---|---|
| mismatch_5 c1 | sim 2.5× about (938, 475); the sun's fit (993.5, 590.5) r 246.5 (residual 21.8 px: the disc is flattened by refraction) onto the core (960, 521) r 110; end scale 0.4; the disc ends at 25 px; the deck −19.17°, 121 → 7.5 px; the truss by its axis −1.4° → 20.3°, 987 → 1137 px long, the OT residual 146 px at 0.35 | 0.62 / 0.05 / 0.03, 7.03 | 39 s | 3232b74f… |
| mismatch_3 c1 | homography, 1.562× about (1252, 421); the quad [[585, 145], [1919, −152], [1919, 925], [585, 767]]; 42 front elements (61.6 % of B) over the filled plate; the wheels 104 px, the crowd 1098 px at 0.3 | 0.29 / 0.74 / 0.39, 30.7 | 67 s | b259ec1e… |
| mismatch_3 c1-nosit | c1 with the crowd's and the flag's moves skipped by the operator (`name.skip=true`) | 0.14 / 0.73 / 0.37, 30.6 | 49 s | 7c0b3b30… |
| mismatch_3 c2 | the exact pane [[585, 251], [1919, 31], [1919, 741], [585, 661]], 1.924×, the glass at 0.35 | 0.27 / 1.25 / 0.38, 29.6 | 50 s | 63d67ebd… |
| mismatch_2 c1 | sim 2.221× about (258, 722); the rect [142, 397, 413, 757] with a 10 px soft rim; the front = B's man (disparity 0.613 against the wall's 0.425) | 1.17 / 0.07 / 0.42, 19.3 | 14 s | 51d638a7… |
| mismatch_2 c2 | the phone's quad, 9.03× | 1.38 / 1.40 / 0.03, 22.3 | 23 s | 815706f9… |
| mismatch_5 c2 | not rendered at full size: at end scale 0.1 the truss's and the water's masses have no cells on the working grid (the 960 px draft stepped 2.04 at frame 1 and moved neither) | — | — | — |

What the frames show (my eye; the owner grades; the page says the same under each clip). mismatch_5:
the sun is centred and ends as the core's bright heart inside the glow, the deck becomes the streak,
the truss reaches the lane; a thin dark ring at the limb from 0.9 to 1.4 s, the deck's hard top edge
until it thins, a grey ghost where the lamp posts were keyed, the truss as a dark cluster for 0.4 s
before it dissolves; "stars popping" has no path (T38). mismatch_3: 1.2–1.6 s is the owner's
framing with depth (the crowd behind the glass, the group in front); the filled plate shows beside
the quad for a few frames, the men enter magnified and fade in, and the planned crowd-onto-men morph
smears into blobs between 2.1 and 2.6 s (a second render with that move and the flag's move skipped
by the operator is on the page). mismatch_2 (blind): the peek is passed on and the hand hides him;
the rectangle reads as a card between 0.9 and 1.5 s; the face-to-face finish is a reveal.

Rulings kept: frame 0 is A and the last frame is B (forced after the composite; the first and last
interior steps are read from the file); every pixel from A or B except the inpainted fill behind
B's lifted foreground, which the page names; the renderer is offline; nothing in `transitions.py`;
no key in `layered_probe.py` (rounds 1–7 byte-identical by construction, so the 41 md5 watches do
not need a run). Reversibility: delete the two scripts and the plans folder; strike §13.10–§13.12
by a dated amendment.

After the skeptic's pass (2026-10-17, about 21:00–21:50 EEST). A skeptic subagent (Opus 5.5, the
owner's eye) read the first full-size render frame by frame (`benchmarks/runs/2026-10-17/agents/skeptic_r8.md`,
every item with frame numbers) and found 20 faults the page had not named; eight were renderer bugs
and were fixed before the page was shown: (1) the receding sun left a second disc with a dark rim
behind it and a strip of the deck rode inside it (the brightness-thresholded disc; the recede now
takes the whole geometric disc but the silhouettes under L 60, and its rim ramp opens with the
recede so frame 1 stays A); (2) B's own streak ran beside the deck bar from 0.4 s, so the deck never
"became" anything (a `line_to` target is now filled out of the plate by `cv2.inpaint` until the end
effect blends the plate back to B; the deck stretched 2.6× along its line); (3) a local cut of 30
levels at 1.35 s on mismatch_3 where the wheels' dark layer took its whole box out of A and the bright
brick vanished (a layer now covers only what it carries), and the flag torn under that box (the
wheels by their element, `a_elements=[3]`); (4) the inpainted fill down the whole left edge for 0.8 s
(the depth margin 0.3 keeps the wall and the ceiling in the plate; only the men and sofas are lifted);
(5) holes in the lifted foreground (closed and filled); (6) a rectangle around the café man's face
for 2.4 s (a `hold` no longer takes its box out of the rest of A); (7) the planner's crowd-onto-men
and flag-onto-painting moves on mismatch_3 (blob cut-outs, black voids, a duplicate painting, a
second copy of the lounge on a card) cut by the operator in `c1` and kept in `c1-full` so the plan
as written is on the page; (8) the café clip's last remnant, a strip across her eyes (a
`radial_reveal` toward his eyes, by knob). The page's "faults" texts were rewritten from the
skeptic's timings, and the page now says which number is the clip length and which the render time.
What remains, named on the page: the sky key's dark halo and the lamp-post ghost in the first
0.6 s; a faint limb ring; the deck's hard top edge until it thins; the truss as three soft-edged
slabs for about 1 s; the men entering magnified and fading in over 0.45 s; the wheels as a dissolve
over the trunks; the pane clearing as a reveal (bright first, the crowd last); the café rectangle as
a card for 0.7 s and his face on hers for half a second; mismatch_2 c2 as the planner's own F3 risk.
The final renders' numbers are in the table below (the first set is in the sheet as the superseded
table).

The final renders (after the skeptic's pass; full size, 3 s at 30 fps; page md5 282d6f3a…):

| Clip | Steps first / second / last, peak | Render | md5 |
|---|---|---|---|
| mismatch_5 c1 | 0.59 / 0.04 / 0.37, 7.02 | 40 s | d410b519… |
| mismatch_3 c1 (the operator's cut) | 0.69 / 0.72 / 0.03, 26.1 | 49 s | 8ae49c38… |
| mismatch_3 c1-full (the plan as written) | 0.77 / 0.74 / 0.04, 36.5 | 67 s | 10beef0e… |
| mismatch_3 c2 | 0.88 / 1.25 / 0.03, 42.9 | 50 s | da059d5c… |
| mismatch_2 c1 | 1.03 / 0.09 / 0.04, 19.4 | 13 s | 798cdae1… |
| mismatch_2 c2 | 1.48 / 1.49 / 0.03, 19.4 | 23 s | d3cbde6b… |

The first and last interior steps are under the 1-level bar on the three mismatch_5 and mismatch_3
clips and on the café clips' last frames; the café clips' first steps (1.03, 1.48) are over it by
the soft rim's border and the quad's small size (T38 names them).

### 13.12 FLUX.3 image klein on the box (2026-10-17 evening, Track D, an Opus 5.5 subagent; report `benchmarks/runs/2026-10-17/agents/flux3_run.md`, page `benchmarks/runs/2026-10-17/flux3/index.html`, UNGRADED)

The bf16 files of `black-forest-labs/flux-3-image-klein-comfy` (the distilled and the base
transformer, the Qwen3-VL-4B text encoder, the FLUX.2 VAE; sha256 equal to Hugging Face's on the
box) were downloaded on the Mac at 47–53 MB/s and moved to the box at 15–22 MB/s. The
stable-diffusion.cpp image `master-vulkan` of 2026-10-17 (commit f0aac52, digest sha256:2ad8a48a…)
is pinned for the recipe's new `MODEL=flux3` branch only; the qwen and klein branches and their
manifest are byte-identical to before. One fix: that build rejects the comfy encoder's tensor names
("Conditioner model tensor 'text_encoders.llm.model.embed_tokens.weight' not in model metadata"), so
`flux3/scripts/st_rename.py` writes a renamed copy with the tensor bytes unchanged.

Smoke test at 512×512, 16 steps: 56 s and 50 s wall, about 2.5 s per step, "total params memory
size = 18416.35MB", MemAvailable 47.66 → 30.46 GiB, GTT 59.18 → 76.46 GB; two runs with the same seed
byte-identical. One image-to-image run with one reference: 105 s.

Side by side on the box pair (the fabra boxes) at 1024×1280, the same prompt, reference and size per
row (the 2026-10-09 run had no klein 9B plate or keyframe of this pair, so both prompts were written
tonight in the style of the earlier ones and klein 9B ran them too); the zone is two hand-drawn
rectangles over the boxes, 17.8 % of the frame:

| Run | Wall | Mean abs. difference outside the zone (levels) | Pixels outside changed by more than 8 levels |
|---|---|---|---|
| plate, klein 9B | 89 s | 14.18 | 63.1 % |
| plate, FLUX.3 distilled | 312 s | 14.15 | 73.2 % |
| plate, FLUX.3 base | 923 s | 12.80 | 63.1 % |
| keyframe, klein 9B | 89 s | 17.99 | 82.0 % |
| keyframe, FLUX.3 distilled | 351 s | 15.14 | 79.6 % |
| keyframe, FLUX.3 base | 781 s | 10.72 | 58.2 % |

Time per step is the same (18.5 s against 18.2 s); FLUX.3 takes 16 steps where klein 9B takes 4, so
the distilled model costs 3.5–3.9× the time and the base 8.8–10.4×. Lowest MemAvailable in any
FLUX.3 run 24.89 GiB; every run `run_rc=0`; the hold file removed at 19:14:55 BST and no container
left. Reading: on the keyframe the base model keeps more of the frame outside the zone (58 % of
those pixels changed against 82 %, 10.7 levels against 18.0); the distilled model matches klein 9B
in fidelity at 3.5× the time. Neither has a mask, so every number is "how much the model moved what
it was told to keep", and the choice of the plate and keyframe model of record (T35) is the owner's
by eye on the page. Not run: `--flow-shift 16`, a second reference, the prompt upsampler. Two
resident `llama-server` processes restarted at 18:00 and 18:12 BST while no job of the track ran
(a `llama-swap` model swap is likely; its log was not read). The weights on the Mac (31 GB) sit in
the session scratchpad and are not needed again.

### 13.13 The owner's grades on the director's page (2026-10-17 18:48 UTC, verbatim in the director sheet) and what round 9 builds from them

Best: mismatch_5 c1 ("looks promising"), mismatch_3 c1 ("Like this one, almost acceptable"),
mismatch_2 none. Nothing acceptable as-is. Reading, pair by pair:
- mismatch_5: the camera and the transformations "look better", "bridge trasforms into arm , nice".
  Three asks: the sun's "hard halo and luma borders" when it enters the galaxy; the galaxy "appears
  too quickly and simply ( iris wipe )": he wants "brightest stars to appear first and then nice
  gradual luma cross fade" while the sun and bridge transform; and the "barely visible thin
  powerline which goes above the bridge" should become the diagonal streak (the deck then joins the
  truss into the arm).
- mismatch_3: "camera move, transition of foreground of B into frame and transformation of A is
  really cool"; the fault is the end: A "remains 2d plane till the end and then just dissolves"; he
  expects it "to subtly tranform into trees etc in window pane of B". c1-full is the counter-example
  he names: "transformations for the sake of transformations, no continuity , no story , no sense";
  c2 "crossfade hidden behind zoom in of frame B".
- mismatch_2: both concepts "really weird"; the phone "makes zero sense"; his own concept: "yellow
  man to rotate and gradually transform into closest to camera person from frame B and the tree from
  frame A go away".
Rules from it: fewer transforms with a story beat each, never a shuffle of layers; the end of a
nested clip must be a transformation of the pane's content, not a reveal; B's brightest points
come first and the background last when a sky gives way to a sky.

### 13.14 Round 9: the three asks rendered (2026-10-17 evening, after his grades; plans `scripts/research/plans/mismatch_{5,3,2}_r9.json`, page `benchmarks/runs/2026-10-17/director_r9/index.html`, UNGRADED)

What the renderer gained, one element per named fault (schema v1 "Additions of round 9"):
`container.params.sky` for a soft rim: B's bright points (a top-hat of its luminance, ordered by
brightness) come through A's sky first over `star_window`, A's sky background gives way to B's
dark-first over `key_window` with a wide `key_band` (a slow luma crossfade), and the edge of A's frame
is feathered inward by a width of min(0.35, 4 e) of the short side, so the carried frame never
shows as a rectangle while the key is slow; the end effect `b_luma_reveal` (B's brightest first
inside the container, band 0.4–0.5); the a-kind `dark_line` (the row inside a range with the most
pixels darker than the rows beside it, the band grown to the neighbouring rows that also score, so a
wire that falls 26 px across the frame is caught, its dark pixels only); the transform `exit` (a
layer leaves the frame in a direction and fades); `gain_A` (the depth gain inside A, separate from
B's); `morph_to` `rotate` (the axis map's turn with the box map's placement). Two fixes under them:
A's composite is premultiplied (a layer over a covered region no longer mixes with the base's hidden
pixels: the receding sun's rim had drawn a dark ring from A's limb), and the dark-line layers take
their pixels before any other layer (the wire's chord across the sun belongs to the wire).

The plans (the planner re-run with his notes as the brief; its notes in
`benchmarks/runs/2026-10-17/agents/planner_r9.md`): mismatch_5 — the sky darkens and the brightest
stars come first, the wire swings into the streak, the sun recedes, deck and truss together fold
into the arm, the sky background crossfades slowly, the core takes the last of the sun brightest
first; mismatch_3 — the quad, the entry and the wheels unchanged, the crowd moves against its wall
by depth, the brick greens toward the foliage early, the pane becomes B's view brightest first over
the last 45 %; mismatch_2 — no camera, the tree exits left, the yellow man turns to the nearest
man's axis and morphs onto him, the bokeh takes the café's colours, the café takes over brightest
first. The planner kept the colour path on mismatch_5 as a fourth entry that adds no motion.

Operator's knobs on the renders: mismatch_5 `parallax_sources=["A"]`, `bridge_to_arm.feather=6`,
`bridge_to_arm.mix_window=[0.15,0.85]`, `wire_to_streak.stretch=2.6`,
`sun_recedes.mix_window=[0.2,0.95]`; mismatch_3 `front_margin=0.3`; mismatch_2
`man_becomes_nearest_person.mix=luma`, `man_becomes_nearest_person.ot_weight=0.35`. The full-size
numbers are in the table below.

The renders (full size, 3 s at 30 fps):

| Clip | Steps first / second / last, peak | Render | md5 |
|---|---|---|---|
| mismatch_5_r9 c1 | 0.33 / 0.03 / 0.18, 4.94 | 32 s | 27175af2… |
| mismatch_3_r9 c1 | 0.69 / 0.70 / 0.04, 25.8 | 37 s | b40e9836… |
| mismatch_2_r9 c1 | 0.37 / 0.04 / 0.00, 13.4 | 6 s | 34ea1312… |

The wire on mismatch_5 was found at row 639 of the anchored canvas (the search rows 612–657, 4,412
dark pixels in the band, 17.9 % of the best row's pixels darker than the rows beside it). Every
first and last interior step is under the 1-level bar.

After the skeptic's pass on round 9 (`benchmarks/runs/2026-10-17/agents/skeptic_r9.md`, on the
first full-size render): mismatch_5 was worse than round 8 in three places and all three were
renderer faults, fixed before the page: a second sun disc (the rim mixed into the core's glow from
0.2 of the recede; now from 0.45, and the limb is flattened toward the disc's inner colour over its
outer 20 % before it fades), red vertical streaks above the lamp posts (the depth map stretched the
sky around thin near objects; the gain inside A is 0.15 and the map is blurred at σ 20), the bridge
turning into a pale slab (the bands showed the glow under them on their way; the mix now starts at
0.5 of their travel and their ends taper over 8 % of the width), and the wire showing the glow
instead of the streak (a `line_to` layer now carries B's pixels from its END position with it, M(1)⁻¹
applied to B_inA, so the mix shows the streak's own pixels). mismatch_2's black void came from a
morph layer's working frame beyond the canvas (black border); the frame's edge is replicated now.
mismatch_3 is rated the same as round 8 up to its end, and its end a brightness-keyed crossfade;
the pane's left edge gained a 14 px soft rim. Not fixed and named on the page: a thin outline at
the sun's rim for half a second; the bridge as two soft bands; the lamp posts keyed with the sky;
the café man's head on the other man's body for about 0.15 s (a morph between two people, T39);
the window pane's finish a dissolve ordered by B's brightness (a real transformation of the wall
into trees needs a correspondence, T34). The re-render was not read by the skeptic again. Its
table follows.

The final round-9 renders (full size, 3 s at 30 fps; page md5 71fe5a66…):

| Clip | Steps first / second / last, peak | Render | md5 |
|---|---|---|---|
| mismatch_5_r9 c1 | 0.57 / 0.03 / 0.03, 5.09 | 31 s | f621c9be… |
| mismatch_3_r9 c1 | 0.83 / 0.68 / 0.03, 25.7 | 37 s | 89f65354… |
| mismatch_2_r9 c1 | 0.36 / 0.04 / 0.00, 14.7 | 6 s | 7253f581… |

Operator's knobs on the final renders: mismatch_5 `parallax_sources=["A"]`, `parallax_gain_A=0.15`,
`parallax_blur=20`, `bridge_to_arm.feather=14`, `bridge_to_arm.mix_window=[0.5,0.95]`,
`bridge_to_arm.end_taper=0.08`, `wire_to_streak.stretch=2.6`, `wire_to_streak.end_taper=0.02`,
`wire_to_streak.mix_window=[0.3,0.85]`, `sun_recedes.mix_window=[0.45,0.95]`, the sky block with
`key_window` [0.2, 0.8]; mismatch_3 `front_margin=0.3`, `cont_feather=14`; mismatch_2
`man_becomes_nearest_person.mix=luma`, `ot_weight=0.35`, `mix_window=[0.55,0.9]`. Every first and
last interior step is under the 1-level bar.
