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
2. **Common canvas.** The smaller frame's size, optionally capped by `--max-long`, even
   dimensions for yuv420p. Each endpoint is cover-cropped onto it. Anchors are canvas pixels.
3. **Correspondence** (`dense_displacement`). Fields are canvas pixels on the source grid:
   `dAB[y,x] = (dx,dy)` means `B[y+dy, x+dx] ≈ A[y,x]`.
   - **Class A, related pair.** SIFT, ratio test 0.75, MAGSAC++ homography `H_BA` at 2.5 px;
     sanity: convex warped quad with area ratio in [0.15, 6]; at least 30 inliers. Then DIS flow on
     the pre-aligned pair, composed back through `inv(H_BA)`, in both directions. Certainty per
     pixel is `exp(−e²/2σ²)` of the forward-backward error with σ = 3 px. Method
     `homography+dis`; `dis-only` when the class is forced and no usable H exists.
   - **Class B, unrelated pair.** A similarity between the two salient blobs (gradient energy,
     70th percentile, largest component), or the user's three or more anchor pairs through Moving
     Least Squares (affine; Schaefer 2006). The inverse field comes from splat-and-inpaint.
     Certainty is 0.5 everywhere because nothing photometric supports it. In class A, anchors
     are blended over the dense field with weight 0.7.
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

## 5. Harness: `transitions_harness.py`, 38 checks, about 5 s (as of 2026-09-13; own numbering)
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
length floor, `check` (27–36). I: identity fence (37–38).

Mutation applied on 2026-09-13: making `to_u8` truncate turned checks 11, 20, 21 and 24 red
(32 of 36 at the time). Gaps: every input is synthetic; no real photo pair has been through the
tool (backlog T4, T9); timings were taken with other work running on the machine.

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

## 7. Risks and open questions, ranked
1. **No real pair yet.** On a real re-shot the changed subject makes DIS chase content inside the
   patch; how that looks in a morph is unknown. Slice TR2 measures it once `fixtures/MANIFEST.md`
   has rows.
2. **Class B is crude by design.** Unrelated pairs need anchors; an anchor editor is research E10.
3. **`edge_ratio` is sensitive to sub-level bias.** Smooth presets measure 0.3–0.8 on the harness
   pair; `snap-morph` measures 1.44, and 1.55 under the truncation mutation. The rounding contract
   exists for this reason.
4. **Speed.** 4K costs about 0.69 s per frame on the CPU, so a 10 s 4K transition takes about
   3.5 min. Slice TR7 (rank 1) targets 0.10 s at 1080p and 0.45 s at 4K with the profile above.
5. **No seam from Reveal.** `export_video --style morph` cannot reach this tool; adding a one-way
   lazy import to `reveal.py` is a Reveal-side change (backlog T10, slice TR3).

## 8. Runbook
```
.venv/bin/python transitions.py check
.venv/bin/python transitions.py pair out/before.jpg out/after_aligned.jpg --out out/tr --seconds 1.5 --preset flow-dissolve
open out/tr/strip.jpg; cat out/tr/report.json
.venv/bin/python transitions_harness.py            # Gate 1b
```
