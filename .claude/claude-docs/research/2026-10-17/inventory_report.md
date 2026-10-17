<!-- Provenance: written 2026-10-17 by an Opus 5.5 subagent (research track, afternoon) of the Claude Code session of that day (the round-8/9 session; DECISIONS 2026-10-17), copied verbatim from benchmarks/runs/2026-10-17/agents/inventory_report.md (sha256 a2de918f037db92a) on the owner's order; folded into the seed of `research/director-tooling.md`. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# Inventory of techniques in Reveal / Transitions, ranked by the owner's verdicts (as of 2026-10-17)

## Findings

The repo has built or probed 52 techniques (table A). The owner has accepted none as-is. Seven
have a positive owner verdict: the sun's Gaussian move, the layer-to-counterpart transport
(`morph_to`), the round-5 hand scores, the TR14 in-mask effects (luma, melt-soft, edge-grow) on
the real box photos, and the class A homography+DIS morph on mismatch_7. Every positive verdict
also names a defect. The owner's two verdicts of 2026-10-17 say the whole family is still a 2D
composite ("still at its core 2 separate pictures and flat 2d effect"; "all variants still feel
like very advanced crossfade"). His fix for mismatch_5 and mismatch_3 is a camera move through
scale (a super zoom-out, a picture inside a window pane). Nothing in the repo builds that, and
he names the cost himself: "how much artistic direction it requires".

Source of the 2026-10-17 verdicts: `benchmarks/runs/2026-09-29/layered_picks_L7.json` (dated
2026-10-17T12:15Z) and the caller's quote for the box clip. No doc under `.claude/` records them
yet: grep for "2026-10-17" over `.claude/` and `scripts/` returns nothing.

Legend. Generality: **tuned** = per-pair hand parameters; **auto** = fixed rules on any pair;
**tool** = shipped in `transitions.py` / `reveal.py`. Failure modes (TRANSITIONS.md §11): F1
double exposure, F2 decoration without transformation, F3 invention; plus the owner's words
"crossfade", "reveal"/"wipe", "cutout". T = TRANSITIONS.md, D = DECISIONS.md, DA =
DECISIONS_ARCHIVE.md, B = tracked-backlog.md.

### A. Every technique built or probed (52 rows)

#### A1. Alignment and correspondence

| # | Name | Where | What it does | Gen. | Cost | Owner verdict (quote, date) | Failure | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | Reveal estimation chain (SIFT/ORB, MAGSAC++, ECC masked to static scene) | HANDOFF §3.2; `reveal.py align` | Registers B onto A | tool | 7.9 s per box pair (T §12.24.1) | Wipe/fade output not picked on the boxes, 2026-10-09; alignment itself ungraded as a look | — | shipped |
| 2 | DISK+LightGlue fallback, peripheral-SSIM arbitration | HANDOFF §3.2 step 3, §5b | Learned matcher when SIFT is weak | tool | UNVERIFIED | ungraded | — | shipped |
| 3 | Reveal residual cubic field (10-term, Huber IRLS) | HANDOFF §3.3a | Low-order fix of residual misalignment | tool | in align | ungraded | — | shipped |
| 4 | Reveal changed-region mask (per-channel, Otsu, 21 px dilation) | HANDOFF §3.4; T §10.3 | Marks the repainted region | tool | in align | Indirect: gates TR14 luma/melt-soft (rows 30–32) | — | shipped (Reveal); reimplemented in research |
| 5 | Reveal exposure match (masked Reinhard Lab) | HANDOFF §3.5 | Matches light on static periphery | tool | in align | ungraded | — | shipped |
| 6 | Class A homography+DIS morph (forward splat, certainty weights) | T §2.3–4; `pair --preset morph` | Default transition for related pairs | tool | 11–18 s per 3 s clip at 1536×1920 (T §12.24.1) | match_4/match_5 morph_3s picked 2026-09-14 ("very far from perfect"); mismatch_7 morph_2s: "idea was cool" 2026-09-29; all three boxes 2026-10-17 | F1 on boxes (agent eye, fabra sheet); "dirty clouds" | shipped |
| 7 | Class B saliency pan-and-zoom | T §2.3; `panzoom_field` | One pan-zoom per frame for unrelated pairs | tool | ~6.4–9.1 s (T §12.2) | "naive cross-dissolves", 2026-09-13; "simple junky cross-dissolves but at least … more subtle", 2026-09-15 | crossfade | shipped |
| 8 | Theme anchors via MLS (`--anchors`, `--anchor-falloff 0.45`) | T §2.3; `theme_anchors.py` | Hand anchor pairs warp the whole frame | tuned | ~8–10 s | anchors_alpha closer on mismatch_4 (sun landing); "one picture rotates", "image plane 3d flip", 2026-09-26 | crossfade, F2 | shipped option; whole-frame use parked |
| 9 | Auto anchors (DINOv2-S mutual NN, brightest blob, horizon row, YuNet faces) | `auto_anchors.py`; T §11 | Finds anchors on unrelated pairs | auto | UNVERIFIED | ungraded: 0–6 matches, false suns on mismatch_1/6 | — | research; rejected by measurement |
| 10 | RoMa dense field | `roma_probe.py`, `compare_fields.py`; T §7.1 | Learned dense matcher in place of DIS | auto | 35–55 s, 1.7 GB per pair (T §10.6) | Better on match_3 only ("as if person grows"); background liked; box "simply fades out and new one fades in", 2026-09-15 | crossfade | rejected for TR5 (1 of 6 pairs) |
| 11 | `hold` field (camera motion + residual × certainty) | T §10.2; `tr14_variants.py hold` | Changed object follows the camera only | auto | per clip ~15 s | "i liked how the box itself holds position", 2026-09-15; on its own reads as a fade | crossfade | research; floor of TR14 |
| 12 | `hold-dis` (mask-gated DIS residual) | T §10.2 | `hold` without weights | auto | ~15 s | Picked closer on match_5, 2026-09-15 | crossfade | research |
| 13 | `roma-x-cert` (TR2d as written) | T §10.2 | Displacement × certainty | auto | — | ungraded (agent-rejected: boxes 70 px off) | — | rejected |
| 14 | Feature map inside a layer (`map: {kind: features}`) | T §12.21.3; `layered_probe.py` | Shared-keypoint homography per layer | auto | in render | mismatch_7: "Building do attempt to tranform, albeit quite dirty except from two main ones … so no improvement here", 2026-10-17 | "dirty" | research key |
| 15 | Box map / column map | T §12.21.3, §12.21.6 | Axis-aligned or per-column map between mattes | auto | — | box: inside auto_r7 (row 26); columns ungraded | wavy roofs | box research; columns dropped |
| 16 | In-box SIFT pin, two passes (`chain_luma.py --local-pin sift`) | T §12.24.8 | Pins each changed box on its own features (≤ 0.25 px) | auto on chains | ~10–34 s per chain | Order "boxes positions and dimenstions need to be even more stable", 2026-10-09; 2026-10-17 wants "boxes to be motionless" | — | research; clip ungraded |
| 17 | Wall-ring homography pin + ring-shift local pin | T §12.24.5, §12.24.7 | Pins stills by the wall around the box | auto | — | "box position stability is nice at least", 2026-10-09 (fifth order) | parallax 8–14 px off | superseded by row 16 |

#### A2. Layer source (masks, labels, depth)

| # | Name | Where | What it does | Gen. | Cost | Owner verdict | Failure | Status |
|---|---|---|---|---|---|---|---|---|
| 18 | Depth Anything V2 Small disparity | T §2.3; `transitions.model_disparity`; `warmup` | Relative depth per photo | tool | 0.34 s CPU / 1.3 s in prep | (as camera, row 39) | edges smooth, T18 | shipped behind warmup |
| 19 | Photometric mask rules (depth_fg/bg, skyline, band_dark, clouds, stars, sun, region_of, snap) | T §12.1, §12.7 | Per-pair rule mattes | tuned | 0.36 s per photo (T §12.11) | Stars: "i like how stars appear", 2026-09-26 | contours, afterimages | research |
| 20 | Mask2Former Swin-T (COCO / ADE20K) | `mask_routes.py`; T §12.11 | Panoptic or semantic labels | auto | 0.62–1.19 s, 190 MB | "p-ade on averge was much more accurate then p-coco", 2026-09-27 | misnames | research; superseded |
| 21 | Layer source: OneFormer Swin-L ADE20K + CLIPSeg (20 words) + depth | `layer_source.py`; T §12.14 | Elements with label, group, depth | auto | 8.8–22.5 s per photo, 880+605 MB | Part of "aggreagted accuracy", 2026-09-28 | no star, no AC unit, no utility box (T32) | research, outside offline contract (T20) |
| 22 | Grounding DINO B + SAM 2.1 L | `layer_merge.py --routes gdino_sam2` | Instance masks | auto | 12.2 s per photo | "i really like aggreagted accuracy … lets utilize all we can", 2026-09-28 | — | research |
| 23 | SAM 3 route (merged v3) | `layer_merge.py --routes gdino_sam2,sam3`; T §12.18, §12.22 | More instances, AC unit IoU 0.26 | auto | 61–100 s per photo, 12.7 GB RSS | "look really cool and accurate to me, lets go this way", 2026-09-29 | grain: 77 of 134 buildings under 0.004 | research; ruled the layer source |
| 24 | Normals, edges, saliency in layers.npz (`--extras`) | `layer_source.py` docstring | Extra per-pixel maps | auto | in row 21 | "of course depth and normals", 2026-09-28 | — | built; no score reads the normals (grep in layered_probe.py: 0 hits) |

#### A3. Layered probe: score grammar and actions (`scripts/research/layered_probe.py`, 3,711 lines)

| # | Name | Where | What it does | Gen. | Cost | Owner verdict | Failure | Status |
|---|---|---|---|---|---|---|---|---|
| 25 | Score grammar (layers × action × window × curve, depth compositing) | T §12.1, §12.4 | Owner-editable per-scene JSON | tuned | 6–20 s per 3 s clip | "remotely looks like right direction", 2026-09-26 | "decorations in 2d scene" | research; tool shape `--score` waits |
| 26 | Automatic scores `--auto/--auto2/--auto3/--auto4` (`AUTO2` has 18 constants) | T §12.10, §12.13, §12.17, §12.21 | Score from element matching by label/position/size/depth | auto | prep 2–50 s, render 9–182 s | Closer on mismatch_5/3/2 (r5), mismatch_6/5/3 (r6), mismatch_7/4 (r7); "conceptually though - looks promising with all this objects and people shuffling", 2026-09-29; "hiden wipe", "2d mixup/melt", 2026-10-17 | reveal, cutout, crossfade | research |
| 27 | `move_to`: Bures–Wasserstein Gaussian map (sun) | T §12.1 | Moves a blob to its counterpart | auto | in render | "Only Sun movement is cool between frames", 2026-09-27; "final sun has weird oval shape before settle", 2026-10-17; mismatch_5: "sun tries to become center of the galaxy in weird way dropping down", 2026-10-17 | glow left behind (T18) | research |
| 28 | `morph_to`: entropic OT (log-domain Sinkhorn) between mattes, mix window, Lab-matched | T §12.10.2 | A layer becomes its counterpart in B | auto | in render | "buildings this time transtitoned to tree nicely"; "skyline now tries to morph into new one", 2026-09-27; "skyline transforms in weird wavy pattern", 2026-10-17 | crossfade inside the layer (60–66 % mix share, T §12.21.1) | research |
| 29 | Round-5 endpoint and cloud keys: `settle`, `fill_scales`, `exact`, `unmix`, `parts`+`to_backdrop`, `colour_rel`, `stagger`, `ot_local/floor/rigid/border` | T §12.13.2 | Exact endpoints; clouds become sky parts; staggered starts | tuned | 14–19 s render | r5_flow / r5_stagger closer, all three boxes: "much more direction and stability present and transition is more seamless", 2026-09-28; r5_flow beats r7, 2026-10-17 | "small crossfading" | research |
| 30 | Edge-order cloud erosion (`order: "edge"`, turbulent front) | T §12.9.2 | Cloud thins from its edge inward | tuned | +0–2 s | "still clouds dissolve with cheap linear 2d effect", 2026-09-27 | crossfade | research; superseded by row 29 |
| 31 | Noise/density/luma-ordered dissolve and materialise | T §12.1 | Patch reveal of a layer | tuned | — | "very juny patchy dirty transitions , not useful at all", 2026-09-26 | reveal | rejected for structured layers |
| 32 | `exit`/`enter`/`move` slides | T §12.1 | A layer translates out or in | tuned | — | "decorations in 2d scene", "too linear and naive", 2026-09-27 | F2, cutout | parked as main action |
| 33 | Finish keys: `shutter` motion blur, `smootherstep`/`fall`/`settle` curves, `carry_fit`, `edge_feather` | T §12.9.2 | Softer edges, non-linear motion | tuned | +6–8 s | "not better or worse than previous layered approaches", 2026-09-27 | — | research |
| 34 | Backdrop: per-row Lab fit + residual, `fit2d`, normalized-convolution hole fill, `flow` from layers | T §12.1, §12.7, §12.10.2 | Sky or water as one moving texture | tuned/auto | in render | "Clouds and sun reflections on water are still crossfaded", 2026-09-26 | crossfade, holes (T22) | research |
| 35 | Round-6 keys: `plate`, `mix: "shape"`, `ot_bend`, `ot_balance`, `prefer_known`, `snap` guided filter | T §12.17.3 | One layer per pixel; bend cap | auto | — | Duplicate gone ("R6 doens't have double building anymore"); "some form of reveal with solid margin , it looks pretty 2d and fake, nothing is transforming there", 2026-09-29 | reveal | research; `mix: "shape"` named in T26 |
| 36 | Round-7 keys: `known_frame`, `inward`, `shrink`, plate image | T §12.21.3 | Ground outline travels with content | auto | render 29–103 s | "r7 is marginally smoother but they still seem like hiden wipe", 2026-10-17 | reveal | research |
| 37 | `advect` divergence-free deformation | T §12.10.2 | Noise warp of a layer | tuned | — | ungraded alone | — | research key |
| 38 | Depth-band patch reveal (mismatch_3) | T §12.2 | Bands dissolve back to front | tuned | 10 s | "very juny patchy dirty" (same sentence), 2026-09-26 | reveal | parked |

#### A4. Camera and effects

| # | Name | Where | What it does | Gen. | Cost | Owner verdict | Failure | Status |
|---|---|---|---|---|---|---|---|---|
| 39 | Depth camera `--camera ramp|model --zoom` | T §2.3; `depth_dolly.py` | Parallax-scaled pan-zoom | tool | 0.3–2.7 s depth per image | "really liked the effect on all individual images especially z25 … at least as option", 2026-09-23; 0 of 12, "unnecessary pans and basiaclly cross fading", 2026-09-25 | F2 | shipped option, parked as a transition |
| 40 | Presets dissolve, flow-dissolve, snap-morph, iris, wipe, luma (whole frame) | T §3 | Shipped styles | tool | 11–18 s | dissolve "very junky, just cross dissove", 2026-09-14; flow-dissolve closer on match_1; none of the others picked on the boxes, 2026-10-09 | crossfade | shipped |
| 41 | TR14 `luma` in-mask reveal on the hold field | T §10.4; `tr14_variants.py` | B appears in the box in order of A's brightness | auto | ~15 s per pair | "I really liked effects in tr14_luma_3s and tr14_melt-soft_3s verysmooth", 2026-10-09; "I liked mix of tr14_luma_3s, tr14_edge-grow_3s and tr14_melt-soft but none of those was fully ideal", 2026-10-17 | "crude and global" (fifth order, 2026-10-09) | research |
| 42 | TR14 `melt` / `melt-soft` (curl-noise swirl, zero at the box edge) | T §10.4 | Paint swirls and re-forms | auto | ~15 s | melt "too wobly", 2026-09-15; melt-soft liked, 2026-10-09 and 2026-10-17 | — | research |
| 43 | TR14 `edge-grow` (Canny distance order) | T §10.4 | New paint drawn in outline first | auto | ~15 s | Named in the liked mix, 2026-10-17 | — | research |
| 44 | `luma-melt-soft` and `tool-luma-melt-soft` mixes | T §12.24.2, §12.24.6 | Luma reveal plus swirl | auto | 14–15 s per pair | pair17_luma_melt "came closest to what i meant but need even more subtle", 2026-10-09 | "too crude and global" | research |
| 45 | Chain over many stills in one frame, one ease (`chain_luma.py`) | T §12.24.5–6 | One continuous animation over 5 or 7 photos | auto | 10–34 s | "hard jumps and visible cuts and stops between frames", 2026-10-09 | — | research |
| 46 | `draw` variant (per-pixel soft repaint fronts, background in one dissolve, `--match-light`) | T §12.24.7–8 | Gradual drawing on the boxes | auto | 11–21 s | Ordered by the owner 2026-10-09; not named in the 2026-10-17 verdict: ungraded | — | research |
| 47 | Layered `--auto4` on the boxes (`layered_auto_r7`) | T §12.24.1 | Whole-frame morph; the boxes are not elements | auto | 142 s layer source | "jagged … just wipe without respecting edges positions and not fluid at all", 2026-10-17 | reveal | rejected for this case |

#### A5. Generative

| # | Name | Where | What it does | Gen. | Cost | Owner verdict | Failure | Status |
|---|---|---|---|---|---|---|---|---|
| 48 | SD 1.5 inpainting bridge on the skeleton (warped noise, strength ramp, flow filter, frequency split) | `gen_bridge.py`; T §10.7 | Per-frame SDEdit of in-between frames | auto | 3.5–6.5 min per 30 frames, MPS | "horrible neural slop", 2026-09-22 | F3 | parked |
| 49 | LTX-2.3 keyframe video (MLX, int4); DreamMover; DiffMorpher | T §10.7 | Video or two-image morph models | auto | 6–9 min per 49 frames | LTX "a cut or dumb fade so this defeats all purpose", 2026-09-23; morphers failed the E16 gate | crossfade, F3 | parked; full video generation ruled out 2026-09-26 |
| 50 | FLUX.2 klein 9B Q8_0 keyframes on Strix Halo (`strix_keyframe.sh`, `keyframe_prompt.py`, `keyframe_screen.py`) | T §11, §12.15; research/keyframe-prompting.md | Edits a composite into a cleaner mid frame | auto | 50–68 s per keyframe, 18–19 GiB | "klein 9B looks best", 2026-09-27; kf_13 night tint "looks really cool", 2026-09-27 | — | research; the model of record |
| 51 | Keyframe chain (`keyframe_clip.py`) and keyframe correction inside the probe (`keyframe_layer.py`) | T §12.15, §12.19 | A→K1→K2→K3→B; band-limited correction of the composite | auto | — | "mostly just sequences of crossfades betweeen interrmediate generated frames … not usable", 2026-09-28; "inventing too much stuff", 2026-09-29 | crossfade, F3 | both parked |
| 52 | Generated plates (klein 9B removes the objects) | T §12.23 | Background behind a moved object | auto | 34–136 s per photo | ungraded; allowed by the 2026-09-29 ruling | F3 risk on zones > 50 % | research |

Measures (tools for grading, listed in C): quality basket and goal numbers (T §2 item 6),
`verdict_metrics.py`, `layered_diag.py` with 13 subcommands, the straightness tracker (T §10.5),
ring drift by phase correlation (T §12.24.5).

### B. Top 15, ranked

Order: owner acceptance first, then generality, then reuse as a building block in a pipeline
where a director picks the action per scene.

| Rank | Technique (row) | Why it ranks here |
|---|---|---|
| 1 | `morph_to` OT layer-to-counterpart (28) with the round-5 keys (29) | It is the only mechanism picked as closer on both tuned pairs in two rounds (r4, r5), and it carries the first "one picture" ticks on mismatch_4 (T §12.16). It runs from a fixed rule (auto). The flaw is the crossfade inside the layer: 60–66 % of the change in accepted clips is mix (T §12.21.1). |
| 2 | Sun `move_to` Gaussian map (27) | The owner praised it on 2026-09-26 and 2026-09-27 ("Only Sun movement is cool"). It is the one action that carries an element to its counterpart as a whole. It is closed-form and fully general for a compact blob. Its 2026-10-17 faults are the oval before it settles and the galaxy-centre case. |
| 3 | TR14 luma / melt-soft / edge-grow in the changed mask (41–43) | These are the owner's picks on his only real-life task (2026-10-09, re-confirmed 2026-10-17). They need no per-pair parameter. They work only where Reveal registers the pair (the owner on 2026-09-15: "work only becouse it is very close match"). |
| 4 | Class A homography+DIS morph (6) | It got all three boxes on mismatch_7 on 2026-10-17, and the owner called the idea "cool" on 2026-09-29. It is shipped and keeps shared structure in shape. Its faults are dirty clouds and borders. |
| 5 | Merged layer source v3 with SAM 3 (21–23) | The owner ruled it "really cool and accurate" (2026-09-29). It is automatic and deterministic, and every element-level design needs it. Its gaps: the vocabulary is closed (T32: no utility box), and it runs outside the offline contract (T20). |
| 6 | Box pin on its own features (16) | It answers the owner's top wish on 2026-10-17 ("boxes to be motionless"). It is general for any changed object in front of an aligned plane (T §12.24.8 lesson). The clip that uses it is ungraded. |
| 7 | Score grammar (25) | It is the operator surface the owner asked for ("flexibly tune and control per scene"). A director model would write into it (D2). The owner judges the 2D actions it currently holds, not the grammar. |
| 8 | Automatic score with element matching (26) | Picked as closer on 8 pair-rounds (r5: 3, r6: 3, r7: 2). Rated "conceptually … promising" on 2026-09-29, then "2d mixup/melt" and "hiden wipe" on 2026-10-17. It is the only untuned route to the mismatched pairs. |
| 9 | Depth camera move (39, 18) | The owner liked it as an effect ("especially z25", 2026-09-23) and rejected it as a transition. The depth map is the base for the zoom-out the owner now asks for (D1). |
| 10 | FLUX.2 klein 9B on the second machine (50) | The owner ruled it the best model ("klein 9B looks best") and called the kf_13 relight "really cool". Every use as a whole-frame keyframe was rejected. The open use is a layer or plate helper under the 2026-09-29 ruling. |
| 11 | Hold field / hold-dis (11–12) | The owner confirmed it is necessary ("box itself holds position") but not sufficient (it reads as a fade). Every TR14 effect runs on it. |
| 12 | Stars materialise rule (19) | One liked sentence, 2026-09-26 ("i like how stars appear"). It is narrow, but it is the only element the owner liked appearing in place. |
| 13 | `layered_diag.py change` measure | It orders five clips as the owner did, by reveal share (T §12.21.1). It is the only measure on record that sees "reveal". It still reads accepted clips as 60 % mix, so it cannot see "advanced crossfade". |
| 14 | `draw` variant and the light match (46) | It answers the owner's "really gradual and elaborate drawing process"; its peak frame step is 1.7 levels against 4–13 for the luma chains (T §12.24.7). It is ungraded. |
| 15 | Generated plates (52) | Allowed by the 2026-09-29 ruling. It fills T22 (13.7 % of the canvas showed a smooth fill on mismatch_3). Ungraded. Plates must not be un-premultiplied against (T §12.21.7). |

### C. Building blocks that can be reused whatever the verdict (entry points)

| Block | Entry point |
|---|---|
| Registration of a related pair | `reveal.py align BEFORE AFTER --out DIR [--mode loose]`; in code `reveal.run_alignment` (as `chain_luma.py` uses it) |
| Changed-region mask | `reveal.py changed_region_mask`; re-implemented in `tr14_variants.py` |
| Dense correspondence and splat morph | `transitions.py pair --preset morph`; `prepare` + `iter_frames` in-process (`keyframe_clip.py`) |
| Depth | `transitions.py warmup` once, then `transitions.model_disparity`; `--camera model` |
| Layer source with instances, depth, normals | `layer_source.py <photo> --extras`; `layer_merge.py --routes gdino_sam2,sam3` (scratch venv `benchmarks/runs/2026-09-28/layers/venv`) |
| Score render, automatic score | `layered_probe.py --auto4 PAIR` (writes `scores/auto/<pair>_v4.json`), render of a hand score JSON from `scripts/research/scores/` |
| Transport and maps | `morph_to` (OT Sinkhorn, `ot_*` keys), `move_to` (Gaussian map), `map: features/box` inside a score |
| Mattes and edges | mask rules + `snap` guided filter + `shrink`; `unmix` (half-transparent layer colour) |
| Colour path | `transitions.py` Lab statistics path (`--color`); per-row Lab backdrop fit; `colour_rel`; `chain_luma.py --match-light` |
| Pins for a changed object | `chain_luma.py --local-pin sift` (also `ring`, `edges`) |
| Chains, merges, encoder | `chain_luma.py --variant draw|luma|tool-luma[-melt-soft] --crop none`; `benchmarks/runs/2026-10-09/fabra/merge.py --middle-speed --tail`; `OneKeyframeEncoder` in `chain_luma.py` |
| Generated keyframes and plates (second machine) | `strix_keyframe.sh` (klein 9B Q8_0, seed 20260926, 4 steps, cfg 1.0), `keyframe_prompt.py --dialect flux --refs 1`, `keyframe_screen.py`, `plates/screen_plate.py` |
| Keyframe correction and carry | `keyframe_layer.py clip` (ECC + DIS registration, band-limited Lab correction, chained DIS carry) |
| Generative bridge parts | `gen_bridge.py` (`warp_noise_along_flow`, `frequency_split_blend`, strength ramp) |
| Measures | `report.json quality.goal`; `verdict_metrics.py`; `layered_diag.py end|outline|rest|contrast|step|layers|seam|fields|rim|holes|change|edge`; Reveal harness O straightness tracker |
| Review surface | `layered_probe` page with three boxes, a pick and a note per pair → `layered_picks.json`; `theme_anchors.py --page-only --picks` |

### D. What the record shows is missing [INFERRED unless cited]

1. **A camera path through a 3D scene.** Depth only orders mattes and scales a 2D pan (T §2.3,
   §12.1). No layered mesh, no inpainted disocclusion and no scale-space zoom exist. The TR10 plan
   row lists "layered mesh, virtual dolly/zoom-through, inpainted disocclusions" (EXPLORATION_PLAN
   TR10), and that part was never built. The owner's 2026-10-17 asks (mismatch_5 "super out zoom";
   mismatch_3 "zoom out as if people from the first phote are in the window pane") need a nested
   picture-in-picture zoom.
2. **A model that decides the transition per scene.** `auto_score2` matches by label, position,
   area and depth with 18 fixed constants (T §12.13.6). No VLM or LLM reads the pair and writes
   the score. The owner: "how much artistic direction it requires" (2026-10-17), and on 2026-09-27
   "such art direction very hard to derive in generic way ( an this is what we want eventually)"
   (DA). No rule exists for "the bridge itself rotate and become meteor streak" (T §12.13.6).
3. **Transformation inside a layer.** Content still changes by mix: 60–66 % in the accepted clips
   (T §12.21.1). No structure-aware texture morph (texture synthesis, a feature-space or
   generative per-layer in-between) has been built. "very advanced crossfade" (2026-10-17).
4. **Compositing beyond alpha-over.** Track E proposed a Laplacian-pyramid composite, Lipman's
   Möbius map and Neyret's advected texture (T §11). grep finds none of them in
   `layered_probe.py`. There is no conformal or log-polar warp.
5. **Alpha matting and object relighting.** Mattes are cut from 640-px label maps or 256–288-px
   SAM logits (T §12.18 limit 2). "crudely cut out … cheap 2d animated photoshop work" (T28). No
   matting model was probed. Day-to-night is Lab statistics only. The liked kf_13 relight came
   from the generative model.
6. **Generative help per layer.** Generated content was used only on whole frames (rejected) and
   on plates (ungraded). Not tried: a generated in-between of one layer under the "50+% original"
   rule.
7. **Video input.** TR4 has not started. The velocity boundary condition is [INFERRED, not built]
   (D 2026-09-27 night).
8. **An open vocabulary for "the thing that changes".** No utility box among the prompts (T32),
   no star found on 18 photos (T §12.14 limit 3).
9. **Measures that see what the owner sees.** Rim 8–32 % does not see "rough edges" (T28). The
   stall measure does not see "too discreet" (D 2026-09-29). No measure sees "2d" or "advanced
   crossfade".
10. **Pairs outside the tuning set.** Every constant was chosen on these 7 pairs (T §12.13.6). No
    held-out pair exists.

Parked list of record (NEXT_SESSION_PROMPT §8): per-frame bridge, cameras as a transition, TR7,
whole-frame anchor warps, one layer for the whole frame, column map, un-premultiply against a
plate, depth-band patch reveal, slides as the main action, a prompt on a photo as a midpoint,
morph chains between keyframes, keyframe as whole-frame correction.

### E. Rulings in force (verbatim, dated)

| Date | Ruling | Source |
|---|---|---|
| 2026-09-26 | Generated KEYFRAMES as helper elements, deterministic interpolation between them, "never full video generation" | D 2026-09-26; T §11 |
| 2026-09-29 | Generated content allowed: "realistic ( for a given context )", "keeping 50+% of objects original and consitnet between frames", "not inventing completely new objects"; "surprise me"; "transtion from anything to anything"; "feel free to try all approaches" | D 2026-09-29 (rulings); memory note generated-content-allowed-as-helper ("do not re-ask") |
| 2026-09-27 night | "Licensing for ANY model is not a problem , this whole project is pure personal non-profit research" | D 2026-09-27 |
| 2026-09-27 night | "lets proceed with 8bit full quants for now"; "i don't want degraded Q 4bit anyways"; FLUX locally ("no , i want fux locally") | D 2026-09-27; T §12.12 |
| 2026-09-26 | Nothing enters `transitions.py` before the owner grades a probe "one picture" or "content transforms"; `pair --score FILE` waits for an explicit word | D 2026-09-26; T §12.4 |
| 2026-09-27 evening | "not overfit on these specific example pairs … universal solution (tunable and adjustable)"; judge on untuned pairs; hand rules count as tuning; "photos and videos" | T §11 amendment |
| 2026-09-26 | "be carefull also not to generalize" (per pair) | DA 2026-09-26 late |
| 2026-09-14 | A pick is not acceptance: "they simply resable what i am looking for but very far from perfect"; a separate "acceptable as-is" answer | benchmarks/2026-09-13 §Owner picks; D 2026-09-14 |
| 2026-09-27 | Layers that slide in and out are rejected ("decorations in 2d scene"); a wall transforms, never a "cheap 2d cutout" | D 2026-09-27 evening |
| 2026-09-15 | "timings below 1-2  min per pair  is not that much issue"; 3–5 min per pair for experiments | D 2026-09-15 |
| 2026-09-14 | "YES, this is personal project, fetch anything you need", each weight behind warmup + manifest + refuse-to-download | D 2026-09-14 |
| standing | Offline contract: no network outside `cmd_warmup` / `transitions.py warmup`; `models/` write-protected; the two tools never import each other; single-file modules; a new dependency is a decision | AGENTS.md §Hard constraints |
| standing | Permanently out: LoFTR, MPS for Reveal (decision 9), operator settings file, ffmpeg `xfade`, dense residual flow on Reveal pixels, pixel similarity in the score, lazy download | AGENTS.md §Permanently out |
| 2026-09-29 | The five automatic pairs stay automatic ("keep them automatic") | D 2026-09-29 |
| 2026-09-26 | Strix Halo runs: no host change, user-scoped, pre-flight memory check, `~/halo-hold` | D 2026-09-26 |
| 2026-09-25/26 | `--camera` stays an option, not the transition | benchmarks/2026-09-23 §5 |

### Key facts
- 52 techniques; 0 accepted as-is; positive verdicts on rows 6, 16/17 (stability), 23, 27, 28/29, 41–44, 50.
- Round 7: no pick on 5 of 7 pairs; auto_r7 is closer on mismatch_7 and mismatch_4 only (layered_picks_L7.json).
- The accepted layered clips change 60–66 % by mix (T §12.21.1): the measured form of "advanced crossfade".

### Relevant artifacts
- /Users/yevhens/Projects/personal/reveal-1.5.0/.claude/claude-docs/TRANSITIONS.md (§10–§12.24)
- /Users/yevhens/Projects/personal/reveal-1.5.0/benchmarks/runs/2026-09-29/layered_picks_L7.json
- /Users/yevhens/Projects/personal/reveal-1.5.0/scripts/research/{layered_probe,tr14_variants,chain_luma,layer_merge,layered_diag}.py
- /Users/yevhens/Projects/personal/reveal-1.5.0/.claude/skills/reveal/references/tracked-backlog.md (T18–T32)

### Constraints discovered
- The 2026-10-17 verdicts are in no DECISIONS line yet; the next session must record them (append-only).
- `layer_merge.py` SAM routes need the scratch venv with torchvision; the tool venv cannot run them (T §12.18).

### Confidence: 80%
High for the rows and quotes taken from TRANSITIONS.md, DECISIONS.md and the picks files. Lower
for the ranking, which is my weighting, and for the cost figures, which were measured beside
other jobs.

### Gaps
- Read in part only: DECISIONS_ARCHIVE.md (321 KB, grepped for owner quotes), `layered_probe.py`
  (docstring and §12 tables only), `audits/retrospective-2026-09-26.md` (not opened),
  `research/keyframe-prompting.md` (not opened), benchmark sheet `2026-09-26-layered.md` (headings
  only; its picks match T §12).
- The 2026-10-17 box-clip verdict comes from the caller's quote; I found no file holding it.
- Owner verdicts on the keyframe runs kf_01–kf_16 come from archive excerpts, not the full lines.
- The `draw` and in-box-pin clips: I cannot tell whether the 2026-10-17 box verdict covers them.
  It names only the TR14 clips and layered_auto_r7.
