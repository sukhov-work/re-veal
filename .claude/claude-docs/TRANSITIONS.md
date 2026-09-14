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
| RoMa outdoor (romatch 0.1.2, torch 2.14, CPU, 12 threads) on match_4 at 1536×1920, scratch venv, 2026-09-14, concurrent with the sweep | weights 1,217,586,395 + 445,647,516 bytes (DINOv2 ViT-L/14 Apache-2.0, RoMa MIT), load 80 s incl. download; match 40.6–44.8 s per pair (4 runs) against 0.74 s for homography+DIS; the input is resized to 560×560 coarse and 864×864 for the field, aspect ignored; certainty mean 0.553 (62 % of pixels above 0.5); median displacement 9.9 px (DIS 15.1); median difference to the DIS field 0.57 px over the canvas, 0.20 px where both are confident (52 % of pixels) |

## 7. Risks and open questions, ranked
1. **Object-level correspondence is the top gap (owner review, 2026-09-13).** Three matched pairs
   are "promising" but miss accuracy and any transformation of parts; a person who moved reads as a
   slide (match_2); two poses that share no flow crossfade into each other (match_3); every
   unrelated pair is "a naive cross-dissolve". The engine matches pixels, not themes. Order of
   remedies: a learned dense matcher (TR5), object and part correspondence with anchors (TR9), a
   generative backend for the intermediate transformations (TR6). Verbatim review and per-pair
   mechanism: `benchmarks/2026-09-13-real-pairs.md`. Measured 2026-09-14 (§6): RoMa's field fixes
   match_3 (the person no longer smears) and match_5 (the boxes stay put) and leaves match_2 as it
   is; its certainty is low exactly where content changed, so the splat lets those regions dissolve
   in place — the effect TR2d was going to build by hand. TR5 integration is the next slice; the
   owner lifted the speed gate ("below 1-2 min per pair is not that much issue for now").
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
