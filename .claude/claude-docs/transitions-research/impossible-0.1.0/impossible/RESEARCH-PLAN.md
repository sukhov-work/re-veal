# Impossible: Local Research Plan

For the agent working on Yevhen's M3 Pro (36 GB). The design report
(`impossible/RESEARCH-REPORT.md`, Sept 2026) covers the reasoning. This file
lists the experiments to run, the numbers to record, and the gate to pass
after each phase. Every experiment appends to
`impossible/bench/results.json`. The gates are not optional: v0.1 was built
in a Linux sandbox and nothing has been measured on Apple Silicon yet.

## 0. Ground rules

- **Isolation.** Nothing in `reveal.py`, `setup.sh`, `run.sh`, `README.md`,
  `HANDOFF.md`, `harness.py`, `requirements*.txt` or `VERSION` changes.
  Verify with `sha256sum` against `impossible/REVEAL-BASELINE.sha256` before
  every commit. `impossible_harness.py` checks 1-2 enforce no import in
  either direction.
- **Offline contract.** Model weights go to `impossible/models` via
  `python -m impossible warmup <backend>` (to be written in E14-E16),
  never mid-job. Same manifest-and-forward-pass proof Reveal earned in
  v1.5.0: download, run a real forward pass, record sha256, refuse to
  download at runtime.
- **Budget policy.** "Minutes are fine, hours are not." Every generative
  path must estimate before it runs and decline when the estimate exceeds
  `budget_minutes` (default 10). Measure, then replace the placeholders in
  `generative.COST_PER_FRAME_480P`.
- **Resolution policy.** Deterministic tier at native canvas (1080p and 4K
  both). Generative tier at the largest rung of `RES_LADDER` that fits the
  budget (854x480 -> 1024x576 -> 1280x720), lifted to native with
  `frequency_split_blend` (low frequencies from the generator, high
  frequencies from the deterministic skeleton).
- **Evidence.** Label claims [VERIFIED] [INFERRED] [UNVERIFIED]
  [ASSUMPTION] in results and notes. Record wall-clock, peak memory (Activity
  Monitor or `psutil`), resolution, frame count, seed.

## 1. What already works (sandbox-verified on x86, 34/34 harness checks)

- Deterministic skeleton end to end: photo pair, clip pair with PTS-exact
  cuts and frame-exact stitch, N-item sequences of mixed images and clips.
- Correspondence: SIFT+MAGSAC++ routing into Class A (homography-guided
  DIS dense field, 0.06 px median error vs ground truth on an affine test)
  or Class B (saliency similarity, user anchors via Moving Least Squares).
- Warp engine: importance-weighted forward splat on a 1/4-res coordinate
  grid + one full-res remap (63 ms per splat at 1.3 MP; exact on a
  translation field; endpoints within 1.5 levels).
- Color path: time-varying Lab statistics, both endpoints meeting halfway.
- Grammar: presets morph / dissolve / flow-dissolve / snap-morph / iris /
  luma / dream; curves linear / ease / ease-in / ease-out / snap /
  hold-then-go; 0.1-10 s.
- Generative contracts: `Enricher` interface, budget planner, warped-noise
  steering primitive (simplified Go-with-the-Flow), frequency-split lift.
- Quality basket: warping error, flicker with `edge_ratio` (hidden-cut
  detector), endpoint fidelity, thumbnail strip.

Known limits, all addressed in phase 1 or 2: v0.1 re-encodes the whole
output, which is correct but slow (E8 adds stream copy); decode and encode
are 8-bit (E12); the DIS-based dense field degrades on wide baselines (E4
replaces it with RoMa); Class B without anchors only aligns the two
salient blobs (E9).

## 2. Phase 1: deterministic core on real material (target: 1 week)

**E1 Bench on the Mac.** `python -m impossible bench --out impossible/bench`.
Record s/frame at 720p, 1080p, 2160p for the morph preset. Gate: 1080p
<= 0.3 s/frame, 2160p <= 1.2 s/frame on M3 Pro. If slower, port
`forward_splat` to torch `index_add_` on MPS (E6) before anything else.

**E2 Real pairs, deterministic.** Ten pairs from the operator's own
material: 3 Dnipro box re-shots, 2 cityscape/landscape pairs (Class A), 2
day->night, 3 unrelated (person->sky, box->galaxy, etc). For each run
`pair` with presets morph, flow-dissolve, snap-morph at 1.0 s and 3.0 s.
Write `bench/e2/<pair>/<preset>.json` (the report) and look at every
`strip.jpg`. Record which class was routed and whether it was right.
Gate: Class A routing correct on all 7 related pairs; no `edge_ratio` >
1.5 on morph/dissolve/flow-dissolve (hold-then-go presets inflate it by
design); operator rates >= 6 of 10 pairs "usable as-is" for the 1.0 s morph.

**E3 Real clips, cuts and stitch.** Three clip pairs from the iPhone (HEVC,
possibly HLG) and three from the a6700 (XAVC/H.264 or HEVC). Run `clips`
with 0.3 s, 1.0 s, 2.0 s transitions. Verify frame accounting in
`report.json` against `ffprobe -count_frames`. Check for VFR iPhone footage:
`probe()` fps vs actual PTS spacing. Gate: cuts land within half a frame
of the requested time; stitched frame count = head + transition + tail;
no audio (audio is out of scope for v0.1; note it).

**E4 RoMa as the Class A dense field.** `pip install romatch` in the venv,
weights via `python -m impossible warmup roma` (write it: pins TORCH_HOME
to `impossible/models`, runs `roma_outdoor` once on a tiny pair, records
sha256). Run E2's 7 related pairs with RoMa vs homography+DIS. Compare
warping error and the operator's eye on the strips; record s/pair on MPS
and on CPU (`PYTORCH_ENABLE_MPS_FALLBACK=1`). Gate: RoMa wins on >= 5 of
7 pairs and runs < 20 s/pair at the 560/864 default. Then make it the
default when installed. Verify `_roma_displacements` output layout on
unequal sizes; the sandbox could not.

**E5 Splat quality.** Compare `forward_splat` (1/4-res coordinate splat)
against the reference softmax-splatting implementation (Niklaus & Liu,
CUDA/PyTorch; CPU fallback exists) on 3 pairs with strong occlusion
(person in front of background). Gate: if the reference is visibly
better at disocclusion edges, port its importance metric; else keep.

**E6 Speed on MPS.** Port `forward_splat` scatter to torch `index_add_`
(MPS) and `morph_frame` end to end on tensors. Gate: 4K <= 0.4 s/frame.

**E7 Motion carry-over.** Use `video.context()` (4 frames before/after the
cut). Estimate outgoing velocity with DIS on the last 4 frames of A and
incoming velocity on the first 4 of B; extrapolate A's motion into the
first third of the transition and blend to B's motion over the last
third. Implement as a per-frame additive displacement in `render.py`
behind `spec.motion_carry` (default on for clips, off for photos).
Gate: on a pan->pan cut, the transition's mean flow direction is
continuous (no reversal) and the operator sees "momentum".

**E8 Stream-copy stitch.** Re-encode only [cut-2s, cut+transition+2s]
and stream-copy the outer segments (PyAV remux with `bitstream`
passthrough, or ffmpeg `-c copy` on keyframe boundaries + concat demuxer).
Gate: byte-identical outer segments, frame-exact join, 10x faster than
full re-encode on a 2-minute clip.

**Phase 1 exit:** E1-E3 gates green, E4 decided, E7 implemented. Tag
`impossible 0.2.0`.

## 3. Phase 2: depth and portals (target: 1 week)

**E9 Class B semantics.** Replace `salient_box` with SAM 2 masks (largest
salient object) and match parts with DINOv2 ViT-B patch features (cosine
NN between the two masks' patches, mutual-NN filter, then RANSAC on a
similarity). Feed the surviving matches as anchors into `mls_affine`.
Gate: on the 3 unrelated pairs of E2, the morph "lands" the salient
subject on the salient subject without the operator adding anchors.

**E10 Anchor editor.** A stdlib `http.server` page (clip-path preview as in
Reveal, plus draggable anchor pairs drawn on both endpoints, saved to the
spec's `anchors`). Gate: operator produces a face->cloud morph he likes
with <= 5 anchors.

**E11 Depth camera-move path.** Depth Anything V2 Small (transformers,
MPS) per endpoint; 2.5D dolly/zoom-through: build a layered mesh from
depth, move a virtual camera, LaMa-inpaint disocclusions (or
`cv2.inpaint` as the v0 fallback). Gate: a 2 s zoom-through on a
cityscape pair without visible tearing; s/frame recorded.

**E12 Color science.** Evaluate OKLab statistics and MKL/optimal-transport
transfer vs the Lab path on the day->night pairs; add 10-bit decode
(`to_ndarray(format="rgb48le")`), keep HLG/PQ clips in their transfer
function, encode `yuv420p10le` HEVC tagged `hvc1`. Gate: an HLG iPhone
clip round-trips without banding or a brightness step at the join.

**E13 Portals.** SAM-mask portal (reveal B through the salient object of
A), plus luma-driven reveals with the softness curve exposed. Gate:
operator has three distinct portal looks.

## 4. Phase 3: generative enrichment (target: 2 weeks, opt-in feature)

Order by expected payoff per hour of setup. Each experiment writes a
`warmup` for its backend, measures, then decides.

**E14 LTX-2 keyframe interpolation on MLX.** Install the MLX LTX-2 port,
int8 distilled (8 steps, CFG 1). Implement `LTX2KeyframeEnricher.enrich`:
first/last frame = the deterministic frames at the window edges; run at
the planner's resolution; `frequency_split_blend` back to native.
Measure s/frame at 480p and 720p for 24 and 48 frames, peak memory, and
whether the same seed reproduces on two runs. Gate: <= 10 s/frame at
480p (i.e. a 2 s @ 24 fps window in <= 8 min) AND reproducible on a
fixed seed, else keep it off by default. License: LTX-2 Community, fine
for personal use; record it.

**E15 Wan 2.2 TI2V-5B FLF2V on MLX.** Same protocol. Expected slower;
Apache-2.0. Gate as E14. Keep whichever backend wins as default.

**E16 DreamMover for photo pairs.** SD 1.5 based; the natural "dream"
backend for unrelated PHOTO pairs (large motion). Measure minutes per
pair at 512-768 px. Gate: <= 6 min per pair, output lands on the
deterministic frames when strength is low.

**E17 Steering.** With the winning video backend: (a) SDEdit-style
partial denoise from the deterministic frames with strength = dreaminess
(the base mechanism); (b) warped-noise init from
`generative.warp_noise_along_flow` (simplified Go-with-the-Flow) and, if
the backend exposes trajectories (Framer) or depth/canny IC-LoRA (LTX-2),
feed the skeleton's displacement/depth. Measure: does the generated
motion follow the skeleton (warping error between generated frames and
skeleton frames, and the operator's judgment)? Gate: at dreaminess 30,
the subject's path is recognizably the skeleton's; at 80, "dream-like but
not random".

**E18 Candidate sweep UI.** K seeds, thumbnail strips, `composite` score
for ordering only; operator picks. Gate: picking among 4 candidates takes
under a minute.

## 5. Phase 4: product surface

- `sequence` gets a JSON editor page: items, cut points with frame
  scrubbing, one transition card per join with the top-level sliders
  (length, preset, dreaminess, motion carry, color) and an "advanced"
  disclosure (curves, anchors, window, seed, budget).
- Audio: crossfade the two clips' audio across the transition window
  (PyAV audio resample + linear crossfade). Out of scope until here.
- Presets saved as named JSON in `impossible/presets/`.

## 6. Where the numbers go

`impossible/bench/results.json`:
```json
{"platform": "...", "runs": [{"exp": "E1", "res": "1920x1080",
  "per_frame_s": 0.21, "peak_gb": 1.2, "notes": "..."}]}
```
Replace `generative.COST_PER_FRAME_480P` placeholders with E14-E16
measurements and note the date. Every gate decision gets one line in this
file's "Decisions" section below with the evidence.

## 7. Decisions (append-only)

- 2026-09-13 v0.1.0 built in a Linux sandbox; nothing measured on Apple
  Silicon yet. All timing numbers in `generative.py` are placeholders
  [ASSUMPTION].
