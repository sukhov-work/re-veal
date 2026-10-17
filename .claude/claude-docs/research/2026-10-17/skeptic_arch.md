<!-- Provenance: written 2026-10-17 by an Opus 5.5 subagent (afternoon) of the Claude Code session of that day (the round-8/9 session; DECISIONS 2026-10-17), copied verbatim from benchmarks/runs/2026-10-17/agents/skeptic_arch.md (sha256 6943bd813bbcfb32) on the owner's order; folded into `TRANSITIONS.md §13.7`. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# Skeptic review of §13 draft — architect and standards lens (2026-10-17)

Verdict: three objections block the section as written. (1) The mismatch_3 probe clip has a hard cut
between frame 0 and frame 1: 20.33 levels mean step, 22.8 % of pixels change by more than 24 levels.
The draft calls the endpoints exact. (2) The 13.6 plan schema cannot express the probe it names as its
reference implementation. (3) The director's network call needs a dated DECISIONS line and an owner
yes for sending photos off the machine; the draft says "like the keyframe script", and that script
runs with no network. Line numbers below are the current `nest_probe.py` (262 lines). The file
changed on disk while I was reviewing (see O10).

Measurement I ran (decoding the two existing mp4s; nothing rendered):

| clip | step 0→1 | step 1→2 | step n−2→n−1 | pixels > 24 levels at 0→1 |
|---|---|---|---|---|
| mismatch_5 `transition.mp4` (md5 56239da8…, matches the draft) | 1.32 | 0.04 | 0.01 | 0.47 % |
| mismatch_3 `transition.mp4` (md5 da409ea6…, matches the draft) | **20.33** | 0.45 | 0.00 | **22.83 %** |

## Objections

### O1 — blocks. The mismatch_3 clip cuts at frame 1, and the frame-0 override hides it
- Draft: "with every pixel from A or B and exact endpoints" (line 7); "Frame 0 and the last frame are
  set to A and B" (line 48); "B is magnified … at the start, hidden behind A" (lines 52–53, 217).
- Code: under the `matte` rim, `aA = inside * cont` (`nest_probe.py:226-227`) from the first
  interior frame on. Wherever B's front elements (person, furniture, ceiling, wall, object;
  `:182`) fall inside A's footprint, B shows at once, magnified 1.95×. Frame 0 is replaced by A
  (`:236-237`), so frame 1 is the first frame the composite produces.
- Rules broken: `TRANSITIONS.md §12.4` (line 880) wants "the first and last interior step below
  1 level", and round 5 (§12.13, line 1303) requires "the frames beside the endpoints equal the
  photos". mismatch_5 also misses the 1-level bar (1.32).
- Change: at u = 0, A's alpha must be 1 everywhere, and B's front should ramp in, for example
  `aA = inside * (cont + (1 − cont) * (1 − w(u)))` with w(0) = 0. Report the §12.2 column
  "first / last interior step" and the tool's quality basket (`edge_ratio`, `endpoint`) for both
  clips. Strike "exact endpoints" until the steps are measured below 1 level.

### O2 — blocks. The 13.6 schema cannot express its own reference probe
- Draft: "Every element id the model names is snapped to the layer source by IoU ≥ 0.6 … a concept
  whose anchors do not snap is shown as 'unplaced', never rendered" (lines 178–180); "the probe of
  13.2 is their reference implementation" (line 182).
- The mismatch_5 anchors are not layer-source elements. The sun and the galaxy core come from
  `bright_disc` thresholds (0.90 on A, 0.80 on B inside the hard-coded box (850, 440, 1080, 600)),
  and the sun matte is a separate 0.70 threshold (`nest_probe.py:137-151`). In the merged source the
  sun sits at IoU 0.39 / 0.05 (`DECISIONS.md:99`), and no model finds a star (`DECISIONS.md:80`).
  The snap would mark the flagship concept "unplaced". mismatch_5 also has no container
  (`container = None`); its "soft rim" is A's own frame matte.
- `crop_anchor` moves A's crop, but the element masks are registered to the centred crop
  (`nest_probe.py:146`: "the layer source's masks sit on the centred crop, not on this one"). Any
  `layers [{element ids}]` from A is misregistered under `crop_anchor`. The planner's boxes are on
  ≤ 1024-px proxies of the uncropped photos (line 171); the draft names no transform between
  proxy, full photo and canvas.
- `camera {fixed point; z0}` duplicates the anchors: S_A fixes q and z0 (`camera_path`,
  `:108-118`). Any other fixed point breaks camera(0) = S_A⁻¹, so frame 0 is A only by the
  override. `q = t / (1 − s1)` divides by zero when the two anchor scales are equal. The code has no
  rotation, even though the draft says "similarity". `dolly`, `orbit` and `container.in: A` have no
  code at all.
- Change: derive the camera from the anchors (keep only `kind`, `ease`, `parallax`). Add anchor
  kinds that need no element id (`point+radius`, `bright_disc in box`) and snap those by distance,
  not IoU. State the coordinate frame of every box. Make `crop_anchor` re-crop the element masks
  from a full-frame layer source, or forbid it together with A-side element ids. Call the probe "two
  per-pair branches", not a reference implementation.

### O3 — blocks until decided. The director's network call and data egress
- Draft: "the renderer is offline; the planner is a separate script the operator runs on purpose,
  like the keyframe script" (lines 201–202); "A frontier call belongs in the box's prep script"
  (line 154); "Reversibility: every item is a research script or a default-off key" (lines 252–253).
- The keyframe script states "no network" (`scripts/research/strix_keyframe.sh:6`). Putting a
  frontier call into the box's prep script breaks that script's stated shape, and the analogy does
  not hold.
- `AGENTS.md` (hard constraints, line 50): "no external request at runtime" and "no network call
  outside `cmd_warmup`". By the letter this covers the tools, not research scripts. The precedent for
  research code outside the offline contract is backlog T20 (`tracked-backlog.md:47`), which came
  with a DECISIONS line. A director script needs the same: a dated DECISIONS line and a T20-style
  backlog row.
- Sending the owner's photos to OpenRouter or Gemini cannot be undone. `AGENTS.md` §Reversibility
  says an irreversible step needs an explicit owner yes before it starts, and the draft's
  reversibility sentence leaves egress out. An HTTP SDK in the shared `.venv` would also be "a new
  dependency … a decision" (`AGENTS.md:102`).
- Invariant 5 (deterministic, `TRANSITIONS.md §1`) does not hold for a sampled model. The plan must
  be frozen.
- Change: add a DECISIONS line naming the egress and the providers allowed, and put the
  egress question in 13.8 Q2. Use stdlib `urllib` or a scratch venv, as the layer source does.
  Store `plan.json` as a tracked input with the model id, temperature and a prompt hash, so the
  render reproduces from the file.

### O4 — weakens. The new keys duplicate or collide with existing names
- `camera` already names the tool's `--camera flat|ramp|model` and the `report.json` field
  `camera` (`TRANSITIONS.md §2` item 3). `finish` already names the canvas policy `finish`
  (`transitions.py:356-373`).
- `finish: luma` repeats an existing layer: `dissolve` with `order` luma over a window [0.78, 1]
  (§12.1, line 816 area: "the layer's own density, its blobs, its luma …"). `container` is the
  `element` mask rule with `groups` / `not_groups` (`layered_probe.py` docstring, Round-7 keys).
- The draft counts "three new keys" (line 163), names four (line 181), and 13.3 row 7 names two.
- The full-resolution claim cannot be met inside the grammar as it stands. `Layer.affine`
  (`layered_probe.py:2207-2236`) scales canvas-sized layers about the canvas centre with a linear
  scale. The camera must wrap the compositor and re-sample every source from its full-resolution
  file. The canvas-resolution mattes would then be magnified 3.09×.
- Change: rename (`pullback`, `view`, `end_effect`). Express the finish as an existing layer. Add
  only `pullback` + `anchors`. Write down where the camera sits in the compositor and at what
  resolution the mattes are kept.

### O5 — weakens. Visible upscaling, and "not measured" when it can be computed
- Draft: "how much magnified B is visible at mid-clip is not measured" (lines 53–54, 218).
- In closed form, z(u) = z0^(1 − e(u)), and B is upscaled while z > kB. For mismatch_5, z0 = 3.086
  and kB = 2, so B is upscaled until u ≈ 0.44 (frame ≈ 39), at most 1.54×. For mismatch_3, z0 = 1.951
  and kB = 1.33, so it lasts until u ≈ 0.53, at most 1.46×. On mismatch_3 that B is on screen from
  frame 1 (O1). On mismatch_5 it shows wherever the sky has dissolved [INFERRED].
- The canvas rule is "never upscaling" (`TRANSITIONS.md §2` item 2; `transitions.py:357`).
- Change: replace "not measured" with these numbers. Either cap z0 at kB or record a dated decision
  allowing in-camera magnification.

### O6 — weakens. Mechanism claims that do not match the code
- "the sun excluded" plus "the colour path skips a 13-px dilation of the sun" (lines 37, 50). The
  excluded set is `L ≥ 0.70·max` dilated by 13 px (`:151`), and `info.json` gives `sun_share`
  0.0929: 9.3 % of the canvas. The disc of radius 87 px is about 1.2 %. So the cause given for the
  ring is UNVERIFIED.
- "every pixel from A or B" (line 7) and "No pixel is generated" (line 48): the A pixels are
  re-coloured by a Lab transfer at strength 0.85·e (`:212`). Say "from A or B, A re-coloured".
- "A's frame → one pane of the window" (line 45): the code fits A inside the window element's
  bounding box (`:187-190`). It does not detect a pane.
- The crop anchor also centres A horizontally on the anchor (`cover_anchored`, `:64-74`), and only
  the mismatch_5 branch uses it; mismatch_3 uses `T.cover`.

### O7 — weakens. 13.5 claims more than the FLUX.3 report supports
- "it is a plate and keyframe model that fits the box today" (line 121). The report says the
  container re-pull is "UNVERIFIED that a Vulkan image tag carries it" (`flux3_report.md:47`), and
  its gaps list "no sd.cpp Vulkan reports for FLUX.3" (`:101`).
- The unsloth GGUF is listed "for stable-diffusion.cpp" (line 129), but the report says its card
  names diffusers and sd.cpp compatibility is UNVERIFIED (`:49`).
- "10.7 GB against 18.9 GB" leaves out the upsampler, which the draft itself calls required
  (9.5 GB Q8_0 plus 0.62 GB mmproj, `:43`). The like-for-like figure is about 20.8 GB, unless the
  director writes the caption.
- Left out: two or more references are each cut to ≤ 1 MP in the reference code (`:30`); boxes under
  about 40×25 px often fail (`:32`, `:70`); 4K memory on the box is UNVERIFIED.
- "renders only the `finish.helper` region" (line 186): neither model has a mask. Each renders a
  whole frame, and our code composites the region.

### O8 — weakens. Cheaper falsification tests exist
- Director: before any undescribed pair, run frontier top-10 item 8 blind. The planner, with no
  brief, on mismatch_5 and mismatch_3, against the owner's own descriptions in §12.25 (match 2 of
  2), plus IoU ≥ 0.6 of its boxes against SAM 3. This needs no render and no owner time. The
  session model that "produced the two probes today" had read the owner's descriptions, so it is
  not a blind test.
- New keys: first try one score file with no code. `morph_to` on an `all` layer with
  `map: {kind: "box"}` (`box_fields`, `layered_probe.py:425`, scale_max 4 ≥ 3.09) and
  `known_frame: true` already maps A's frame into a B box and carries B back. If its linear field
  reads the same as the geometric camera, the keys are not needed.
- FLUX.3: a 512² smoke test on the re-pulled sd.cpp image settles the "fits the box" claim in
  minutes, before the side-by-side.
- O1 and O5 each took seconds (a decode, or arithmetic).

### O9 — cosmetic. Reproducibility and default-off
- "reproduce byte for byte on two runs" (line 47): only one md5 per clip is on disk, and both match
  the draft. Record both runs' md5s in the DECISIONS line.
- "default-off" keys in `layered_probe.py`: earlier rounds each stated "rounds 1–N render
  byte-identical". Name that check as part of the revert for round 8 item 3.
- `transitions.py` is untouched (git status), so the "nothing enters `transitions.py`" rule holds.

### O10 — weakens. The probe changed under the draft
- While I reviewed, the mismatch_5 branch of `nest_probe.py` changed. The sky now dissolves
  "from the first frame on … over 0..0.75" (`es = smootherstep(u / 0.75)`, `:219-220`), not "from
  5 % to 75 %" (draft line 35). `sky_order` now mixes luminance with distance to the frame border
  (`:161-164`). A tapered bridge band (`keepA`, `:165-172`) replaces "a feathered rim that widens
  with the pull-back".
- The mismatch_5 clip on disk (15:49) and its md5 56239da8 come from the earlier code. The draft
  now describes neither the current code nor, fully, the clip.
- Change: re-render, re-hash, and rewrite the soft-rim sentence and the table row from the current
  code. Otherwise pin the commit the clip came from.

### Checked and correct
The table numbers match `info.json` and the arithmetic: 3.086×, 0.324, fixed point (939, 521),
1.951×, 0.5125, (1558, −1), window share 0.2679, canvases 1920×1080 and 1920×1440. Also correct: the
geometric zoom under smootherstep, the 0.78–1.0 luma finish, the matte composite, sampling B from
its full-resolution file (`:95-105`, `:132-134`) and the md5s. Nothing crosses the
permanently-out list in `AGENTS.md`.

### Confidence
80 %. O1 and O5 are measured or computed. O2 and O3 cite code and rules directly. O6's
dark-ring cause and the mismatch_5 visibility in O5 are by reasoning, not by looking at frames.

### Gaps
- I did not view frames. I did not re-render, so the byte-for-byte claim and the 9.5 s / 5.4 s
  timings are UNVERIFIED by me.
- I did not read `inventory_report.md`, so 13.3 rankings and quotes are not checked. I did not
  check 13.1's quotes or "0 of 12".
- I did not check whether the box-map `morph_to` route in O8 runs on a whole-frame `all` mask.
