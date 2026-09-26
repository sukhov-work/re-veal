# Reveal + Transitions — Exploration plan (RANKED by the owner on 2026-09-13)

Status: **RANKED.** Authority: `HANDOFF.md` and `TRANSITIONS.md` (both under `.claude/claude-docs/`)
win; a slice that contradicts a recorded decision needs a new dated `DECISIONS.md` line before it
starts. This file is iterated in place (dated amendment rows at the bottom), never forked.

## Rank (revised 2026-09-13 night after the owner's first review; ordering is the agent's under the owner's "At your discretion")
Owner's review of the first sheet (verbatim, `benchmarks/2026-09-13-real-pairs.md §Owner review`):
match_1, match_4, match_5 "look promising … still missing accuracy and those interesing intermediate
transformations of parts of image"; match_2 "shifted sideways … and only then morphs"; match_3
"person from start of frame erased/ dissolved into person in end frame"; "such junky transition show
how we miss to grasp some themes or objects or ideas about given frame and build flows around them";
mismatches are "naive cross-dissolves … very generic ( but maybe this is intent for this phase )".
1. **TR5** dense matcher (RoMa): the accuracy step on the promising pairs; its per-pixel certainty
   replaces the DIS consistency weight and answers TR2b.
2. **TR9** object and theme correspondence: SAM 2 masks + DINOv2 part matches as automatic anchors,
   the anchor editor, mask portals. The answer to match_3 and to every mismatch.
3. **TR6** generative tier: "interesting intermediate transformations of parts" come from a
   generative backend steered by the deterministic skeleton; measure one backend first.
4. **TR7** speed: byte-identical levers only, when iteration time blocks 1–3.
5. **TR2b** certainty floor: folded into TR5 unless the owner asks for it earlier (S-sized).
6. **TR3 · TR4**, then **H1 · H3 · H2 · E1 · E2**.
Approval for 1–3 (owner, 2026-09-14, verbatim): "YES, this is personal project, fetch anything you
need" — weights and packages may be fetched at setup time without asking again; each backend still
lands behind warmup + manifest + refuse-to-download (`HANDOFF.md §11`) and its license is recorded.
PyAV for TR4: approved ("`T8 PyAV before slice TR4 ...` - ok"). Order within the rank: TR2c first
(small, the owner's most repeated complaint), then TR5 with TR2d measured beside it.

### Rank, revised 2026-09-15 (late) — the owner's direction after the TR14 picks
Owner (verbatim): "schedule everything relevant above for next session and to proceed with the plan , i
am ok with any experiments , tests and additional resources as long as we have more options to test.
While we want to imporve and make match pairs more interesting , the main problem remains with
mismatches , the still more reseble simple crossfades with various cheap effects on top and not
truthful continous transformations ( i guess this is where we will venture into generative area but i
want it also to keep all good computational,  flow and other tech aspects and math  we have in project
if this helps to keep as many details from both pictures and bridge them with unexpected cool flowing
transition - this is just my rant, not some specific instructions for you , simply to give you piece
of my mind, we still have .claude/claude-docs/transitions-research/impossible-0.1.0/impossible/RESEARCH-PLAN.md,
see where we can push it even more". Reading: mismatched pairs are the main problem; the generative
tier is the route, with the deterministic skeleton (fields, splat, color path, masks) kept as the
steering and the detail source (research E17: SDEdit from the skeleton frames, warped noise along the
skeleton's flow, frequency-split lift). Experiments, tests and resources are approved in blanket.
1. **TR6-A, the generative bridge on the skeleton** (research E17 + E14/E16 gates): SD 1.5 inpainting
   on MPS (installed, 15 s per 512-px frame) over the class B / `hold-dis` skeleton frames of
   mismatch_1 and mismatch_4 (+ match_4 as the control): independent noise vs warped noise along the
   skeleton's displacement (`generative.warp_noise_along_flow`, ported into the research script),
   then the frequency-split lift to the native canvas; measure adjacent-frame steps and warping error
   against the skeleton's flow; clips on a page. Then DiffMorpher (SD 2.1-base, S-Lab non-commercial:
   personal use, license recorded; gated weights need the owner's Hugging Face click-through) and
   DreamMover (SD 1.5) as the two published two-image morphers: minutes per pair on this Mac, look.
2. **TR6-B, LTX-2.3 levers** (background, 6–8 min each): motion prompt, end-frame strengths 0.8, 97
   frames, the q8 pack. Park the video route if none yields an in-between.
3. **TR10 depth camera move** (research E11): Depth Anything V2 Small on MPS, a 2.5D dolly from A into
   B on a mismatched pair — a continuous camera motion that keeps both photos' detail; s/frame.
4. **TR9 semantics** (research E9/E13): SAM 2 + DINOv2 anchors so the salient subjects land on each
   other; SAM-mask portals.
5. **TR14 second probe on the match pairs**: partial-strength luma over `dis` / `hold-dis`, a stroke-flow
   along the new content's structure, RoMa + partial luma on match_3.
Then TR2b/TR5 as components, TR7 speed only when iteration time blocks 1–5, TR3/TR4/H/E as before.

### Rank, revised 2026-09-23 — the owner's verdict on the bridge and on the depth move
Owner (verbatim, 2026-09-23): "regarding `TR10 — a depth-aware camera move for unrelated pairs` i
really liked the effect on all individual images especially z25, what was used to achieve that and
what is the cost? Transitions still mostly simple crossfades , nothing imporoved there but this
depth animation added really cool dynamics to before and after images , i think we can utilize that
in addition to anything else ( at least as option ).  As for the neural get bridge , added my picks
here: `benchmarks/runs/2026-09-15/gen/gen_bridge_picks.json` . But overall experience was horrible,
heavy neural arifacts, or halucinated intermediate images, noise, chaotic and same crossdes."
Picks: all five pairs `none` ("horrible neural slop … halucinations artifacts in almost all
intermediate frames which preserve no features"). Reading: the per-frame generative bridge is
rejected as measured; the E17 gate does not see what the owner sees (a feature-preservation number
is needed before any further generative run). The depth camera move is the one thing the owner
liked, and it is asked for as an option.
1. **TR10 as an option in `transitions.py`** (build; the dependency question is the owner's):
   `--camera flat|ramp|model` (working name) for the class B skeleton — `flat` = today, byte-identical;
   `ramp` = the pan-zoom field × (0.5 + a top-to-bottom disparity ramp), no weights; `model` = the
   same with Depth Anything V2 Small (99 MB, Apache-2.0; torch + `transformers`, a new dependency)
   behind `transitions.py warmup` + manifest + refuse-to-download, CPU by default (0.34 s per image
   at 1024 px), MPS only with a CPU-equivalence check (`HANDOFF.md §11`); `--zoom` exposed (the
   owner liked 25 %). Harness: offline proof as Reveal 80–82, frame hash for `flat`, a decoded-mp4
   check that near rows move more than far rows under `ramp`. Owner 2026-09-23: "yes to model, and
   run it on matched pairs too ( as a test, need to compare)" → the `model` leg is approved; the
   class A use is a research render first (the matched fixtures through the class B camera move,
   and a push-in that is zero at both ends on top of the class A field), one page, the owner's eye,
   then the option's class A semantics.
   **Built 2026-09-23** (the option, its harness section and the sweep; DECISIONS 2026-09-23 third line).
2. **A feature-preservation number in the basket** before any generative run: SIFT matches from
   each in-between frame to the nearer endpoint against the skeleton's count; the owner's three
   screenshots are the calibration cases.
3. **TR9 semantics** (research E9/E13) as before.
4. **Generative route**: parked as measured (TR6-A rejected by the picks; TR6-B rejected 2026-09-23:
   "transition between animations are usually a cut or dumb fade so this defeats all purpose";
   TR6-A2 failed its gate); the remaining levers (auto-regressive input, weaker LTX anchors, 768 px canvas) only
   after item 2 exists and only if the owner asks.

### Rank, revised 2026-09-26 — after the retrospective (RANKED: the owner confirmed the goal paragraph and ordered the metrics the same day; DECISIONS 2026-09-26 second line)
Owner (verbatim, 2026-09-26, with the 2026-09-23 picks): "run was auwful , i feel like we are stuck ,
conceptually. I went ahead and repeated for every junky mismathing pair same logic with applied z
depth pass, which was not expected to help with transition in any way and as i said can be at most
nice additioal touch to image. Revisit full plan and my original goals , do additional deep reseatch,
analyze in retrospect all recent runs and my answers and  see what is not working for us in our
research and what prevents you from understanding my goals clearly and designing precise metrics to
pursue." Retrospective: `.claude/claude-docs/audits/retrospective-2026-09-26.md` (the goal in one
paragraph for the owner to confirm, the method failures, four goal metrics calibrated on the recorded
verdicts, the mismatch_4 anchor probe, five questions). Diagnosis in one line: every slice since
2026-09-13 varied geometry and none varied the combination of A and B (an alpha crossfade since TR1),
which is what the owner grades; the basket could not see it (AUC 0.46–0.48 against the owner's
"crossfade" verdicts).
1. **Goal paragraph + reference** (owner): CONFIRMED 2026-09-26 ("totally right") with two added
   sentences (tunable per scene; colours, luminosity and transparency natural, one higher-order flow)
   and a refined F3 (generated KEYFRAMES as helper elements, deterministic interpolation between
   them, never full video generation). The reference for mismatch_4 is the owner's sentence: sun →
   sun, skyline with depth and river → their counterparts independently and consistently, clouds
   materialising, "the scene basically got rebuilt and transformed in real time".
2. **Goal metrics in the basket** — **BUILT 2026-09-26** (DECISIONS 2026-09-26 third line;
   `TRANSITIONS.md §2` item 6, §5 section M, §6, §11): `feat_floor`, `laplace_floor`, `contrast_floor`,
   `dissolve_fit`, `motion_share` in `assess()` (`local_share` dropped: within-pair AUC 0.46), harness
   52–53 with paid mutations, the numbers on the sheet and the page, three per-property boxes per clip
   exported under `props`. Open: the motion-compensated `dissolve_fit` (a panned crossfade reads 0.195
   on mismatch_4) and a seam / colour-border number (the partition probes).
3. **Layered scene transition, designed first** (Deep design pass; research tracks D and E of
   2026-09-26 under `benchmarks/runs/2026-09-26/research/`): the owner's sentence for mismatch_4 is
   the specification — semantic layers (sky, clouds, sun, skyline with depth, water), a
   correspondence and a field per layer (theme anchors from Track B's recipe: Mask2Former-tiny
   panoptic + DINOv2-S mutual-NN inside label-matched masks + YuNet faces + a brightest-blob sun,
   about 280 MB; the depth model already offline), a combination per layer that is not a global
   alpha and not a hard switch (colour-harmonised, gradient-domain or flow-advected), compositing
   by depth. Hand-placed anchors on all six mismatches first (the `--anchors` path; fix T16 there),
   graded with the three boxes. Track E (2026-09-26, `research/track_E.md`) gives every step a
   deterministic technique: OneFormer / Mask2Former on ADE20K (MIT) for the layers, the closed-form
   Bures–Wasserstein map for the sun, convolutional Wasserstein displacement + Neyret's advected
   texture for the clouds, Lipman's four-point Möbius map + MLS for the skyline, a per-layer Lab
   colour path, a Laplacian-pyramid composite ordered by the existing depth; estimated 1–3 min per
   1080p clip [INFERRED]. First probe: the sun layer (one sun sliding and reshaping) plus a
   horizon-aligned water layer on mismatch_4, nothing else changed.
   **Progress 2026-09-26 (second half; owner: "Go on with theme anchors , feel free to explore")**:
   the hand-placed anchors page exists (`benchmarks/runs/2026-09-26/anchors/index.html`: six
   mismatches × flat / anchors_alpha / anchors_falloff 0.45 / anchors_auto, three boxes per clip;
   `scripts/research/theme_anchors.py`); T16 closed by `--anchor-falloff` (default 0); the automatic
   probe (`scripts/research/auto_anchors.py`: DINOv2-S mutual patch matches + brightest-blob sun +
   strongest-edge horizon + YuNet faces) gives 0–6 DINOv2 matches across the unrelated pairs, faces on
   mismatch_2 / 3, the sun on mismatch_4, and wrong "suns" and "horizons" on mismatch_1 / 6: patch
   matching across whole unrelated scenes is not the anchor source; label-matched panoptic layers
   (Track B recipe 1, Mask2Former-tiny) and the classical detectors are. Owner boxes pending.
4. **Generated keyframes as helper elements** (Research on the Strix Halo box; Track D): one or
   several intermediate keyframes from a multi-reference image model (FLUX.2-class), fixed seed,
   both photos as references, screened by `feat_floor` against both endpoints, then the
   deterministic engine interpolates between consecutive keyframes. No build before a measured
   keyframe passes the owner's boxes on two mismatched pairs. Full video generation stays out.
   Track D (2026-09-26, `research/track_D.md`): Qwen-Image-Edit-2511 (20 B, Apache-2.0, 1–3 input
   images, 57.5 GB bf16, 113 s cold per 1.6 MP image on a Strix Halo with the 4-step Lightning LoRA)
   first, FLUX.2 [klein] 4B (Apache-2.0, 7.75 GB) as the fallback; FLUX.2 [dev] and HunyuanImage-3.0
   do not fit the box or the licence; ROCm 10.0 lists gfx1151 with PyTorch 2.11–2.13 (FP16 validated,
   BF16 not; GPU pool defaults to half the RAM). The keyframes are made by a separate script the
   operator runs on the box and cached with a manifest; `transitions.py` only reads files (the
   offline contract holds). Every speed is reported or inferred, nothing measured.
   **Box facts 2026-09-26 (`mem:project/strix-halo-box`; track F `research/track_F.md`)**: the box is
   a shared production LLM sidecar (llama-swap on Vulkan RADV, 34 GB + 8B models resident, about
   30 GB free), auto-suspends, reboots Thu 05:00 BST, "never global changes". Least invasive route:
   stable-diffusion.cpp's Vulkan container pinned by digest (`/dev/dri` only, no ROCm), Qwen-Image-
   Edit-2511 Q4_K_M + Qwen2.5-VL-7B Q4_K_M + mmproj + VAE = 19 GB, one-shot with caps and a
   pre-flight (`scripts/research/strix_keyframe.sh`, NOT RUN); a container memory cap does not cover
   GPU pages on this APU, so the pre-flight and the quant budget are the protection. Lemonade covers
   image editing only with FLUX.2 klein and runs as a daemon. Probed read-only on 2026-09-26 (late;
   `mem:project/strix-halo-box`): 35 GB available beside the resident LLMs, GTT 53 of 123 GB used,
   Vulkan 1.4 RADV GFX1151, Docker 28.2 rootful (the user is not in the `docker` group → `sudo docker`
   with `--user`), the box's Tailscale logged out (reach = `ssh -J beelink yevhen@10.10.10.2`). Owner
   2026-09-26: "i am ok with your reccomended route in general" → the first one-shot run is the next
   session's item, with the owner reachable.
5. **The combination where nothing aligns** (Design): Track A's candidates (Regenerative Morphing as
   the reference; per-pixel switches only with colour harmonisation), after 3.
6. **Parked**: `--camera` stays an option (not a default); the per-frame generative bridge; TR7.

## H — harness before exploration (evidence: `HANDOFF.md §7`, `harness.py`, backlog T2–T5)
| Slice | Goal (acceptance) | Seam | Revert | Gate / check | Size | Depends on |
|---|---|---|---|---|---|---|
| **H1** section selection | `harness.py --only C,O` runs the named lettered sections in ~seconds; default (no flag) runs all 82 unchanged; numbering untouched | `harness.py` top: wrap sections in `if want("C"):` guards; argparse | `[revert: commit]` — default path identical | full run still 82/82; `--only A` runs exactly checks 1–5 (count asserted) | S | — |
| **H2** benchmark sheet | `scripts/bench.sh` (or `reveal.py bench`) runs `align` over every `fixtures/MANIFEST.md` row and writes one table row per pair (pair · mode · method · inliers · rmse_px · confidence · residual · changed_pct · wall s) to `benchmarks/<date>.md`; a baseline is committed once and every later run is diffed against it pair-by-pair | CLI section (`cmd_align` already writes `metrics.json`) or a script | `[revert: commit]` — no product behaviour changes | the sheet reproduces itself on a second run (deterministic); a deliberately broken constant changes the row | M | T4 (done); `scripts/bench_transitions.py --reveal` already writes the Reveal rows — H2 is the diff-against-baseline step on top of it |
| **H3** video frame-level checks | harness section R: decode the exported mp4 and assert per style — frame count = fps × seconds ± 1, first/last frames equal the stills, wipe seam position monotone, no all-black frame, fade luminance monotone between holds | `harness.py` after section L (checks 34–37 stay) | `[revert: commit]` | each new check names its red-making mutation (e.g. drop the last hold → frame-count check red) | S–M | — |

## E — exploration directions (each needs its own design pass in `/reveal` Design type before code)
| Slice | Direction (owner's words → concrete candidate) | Lane | Must not touch | First falsification probe |
|---|---|---|---|---|
| **E1** additional modes | a third `MODES` key for a pair class `reshot` refuses and `loose` mis-fits (candidates the owner names — e.g. large parallax, mirrored/rotated re-shots, night/day) | new key; `reshot` and `loose` byte-identical | `CFG` defaults; the strict profile (`§9.8`) | one synthetic scenario triple (strict refuses · new aligns · same-scene still passes) in the harness N style, before any ladder change |
| **E2** algorithm improvements | a candidate estimator or refinement competing inside `estimate_alignment` (e.g. a second learned matcher, a better ECC seed, residual-field order/regularisation) | competes as a candidate; arbitrated on peripheral SSIM (decision 23) | ranking by inlier count; the score formula (decision 21); masked/dense flow (18, 20) | the H2 sheet before/after on every catalogued pair — no sheet, no claim |
| **E3** video transitions | new `--style` values beyond `wipe`/`fade` (e.g. radial wipe, split/blinds, zoom-reveal, morph-through-residual) + easing/hold parameters | new style branch in `export_video`; `wipe` default untouched | the frames-piped renderer (decision 6 rules out the xfade filtergraph) | H3 checks for the style's observable, on a synthetic pair, before the page control exists |

## TR — the transitions engine (added 2026-09-13; supersedes E3's "new `--style` values" as the home of transition work)
Owner order (verbatim, 2026-09-13): "we need to start building transitions feature/engine, alogside
existing logic ( do not alter and regress it )". Reference: `.claude/claude-docs/transitions-research/`
(the Impossible v0.1.0 artifact; its `RESEARCH-PLAN.md` E-numbers are cited below). Design of record:
`TRANSITIONS.md`. Every slice: zero diff to `reveal.py` unless the slice says otherwise.
| Slice | Goal (acceptance) | Seam | Revert | Gate / check | Size | Depends on | State |
|---|---|---|---|---|---|---|---|
| **TR1** deterministic core (rank: done) | `transitions.py pair A B --out DIR` renders morph / dissolve / flow-dissolve / snap-morph / iris / wipe / luma to mp4 + strip + report; harness with isolation, ground-truth field, byte-exact endpoints, decoded-mp4 checks | new files `transitions.py`, `transitions_harness.py` | `[revert: delete both files + the doc rows]` | Gate 1b 36/36; paid mutation (truncating casts → 4 red) | L | — | **DONE 2026-09-13** (synthetic only) |
| **TR2** real pairs (research E2; rank 2) | ten catalogued pairs × {morph, flow-dissolve, snap-morph} × {1 s, 3 s}: one sheet of `report.json` rows + strips; class routing right on every related pair; `edge_ratio` ≤ 1.5 on the smooth presets; owner rates ≥ 6/10 "usable as-is" | a bench script over `fixtures/MANIFEST.md` (shares H2's catalogue) | `[revert: commit]` | the sheet reproduces on a second run | M | T4 (done) | **first sheet 2026-09-13**, 12 pairs; owner picks 2026-09-14: 0 of 12 usable as-is; 3 closest-to-intent picks (match_1 flow-dissolve 1 s, match_4 and match_5 morph 3 s), "very far from perfect" — E2 gate NOT met; findings → TR2c, TR2d, TR9 |
| **TR3** Reveal seam (rank 5) | `reveal.py align … --video --style morph` (and the page) renders through `transitions` when importable, else degrades to `wipe` with a visible INFO line | `export_video` gains a lazy `import transitions` branch; `wipe`/`fade` untouched | new `--style` value (experimental lane) | H3-style decoded-mp4 checks in `harness.py` section R; 82 → N/N | M | TR2 verdict; owner yes on the one-way import (backlog T10) | OPEN |
| **TR4** clips and sequences (research E3, E8; rank 5) | `clips a.mov b.mov --cut-a --cut-b`, `sequence spec.json`, PTS-exact cuts, frame-exact stitch | new sections in `transitions.py`; video decode dependency | `[revert: commit]` | frame accounting vs `ffprobe -count_frames` | L | **T8** PyAV decision (duplicate `libavdevice` warning beside cv2, measured) | OPEN |
| **TR5** dense matcher upgrade (research E4; rank 3) | RoMa as the class A field when installed, behind `transitions.py warmup` with manifest + refuse-to-download; measured on the CPU first, then on MPS with a CPU-equivalence check on a fixture (median field difference stated in px); adopted when it wins on ≥ 5 of 7 related pairs by warping error and the owner's eye | correspondence branch | new method value; default path untouched | harness: offline proof as Reveal 80–82; device equivalence check | L | T11; a `fixtures/` row for the equivalence check | **NOT ADOPTED as a drop-in (owner verdicts 2026-09-15)** — 24 clips on six pairs: RoMa better 1 (match_3), same 1, DIS better 3 (match_4, match_5, mismatch_7), neither 1 (match_2); the ≥ 5 of 7 rule fails. Kept alive as a component: the owner likes RoMa's background motion (match_4 "wall and floor, more natural") and match_3 ("person grows"); rejected as the changed-region behaviour ("box … simply fades out and new one fades in, no transformations") and on low-certainty pairs (mismatch_7 "cheap 3d cloth effect"). Re-enter through TR14 (hybrid: RoMa where confident, a designed transformation inside the changed region) once TR14's design says what the changed region should do; speed 35–55 s per pair accepted by the owner, and on 2026-09-15: "i am ok even with 3-5 min of claculations pair for tests, if that will be needed, in general no hard upper limit ( reasonably still) while we experimenting". Scripts: `scripts/research/`. 2026-09-15: `hold-dis` (the tool's DIS field gated by the photometric changed mask, no weights) measured beside `hold` (RoMa): match_4 straightness 4.42 vs 2.54 px, `edge_ratio` 0.136 vs 0.027 — the owner's eye decides whether RoMa's background motion is worth 35–55 s and 1.7 GB per pair (`TRANSITIONS.md §10.8`) |
| **TR6** generative tier (research E14–E17) | measured s/frame and seed reproducibility for one backend on this Mac BEFORE any code lands; the device (MPS via torch, or MLX) is chosen by that measurement, with a CPU-equivalence check where a CPU run is feasible | — (research first) | — | the numbers in `TRANSITIONS.md §6` | XL | owner opt-in per backend (license, size) | **RESEARCHED + FIRST MEASUREMENT 2026-09-15** (`TRANSITIONS.md §10.7`): candidates and licenses from primary sources; SD 1.5 inpainting on MPS fp16 as a masked SDEdit pass on match_4: 1.43–1.62 s/step at 512×640, 14–16 s per image, seed-reproducible byte for byte, 2.4 GB RSS, a coherent intermediate mural but no temporal coherence; LTX-2.3 int4 through the MLX port (`keyframe`, start+end frame) is the video route — int4 pack subset 30 GB + Gemma 8 GB fetched into the session scratchpad, first run's status in the handover. **Fourth session 2026-09-15 (`TRANSITIONS.md §10.7`, sheet `benchmarks/2026-09-15-generative.md`)**: the bridge on the skeleton measured — SD 1.5 SDEdit with warped noise, a sin(πu) strength ramp and a flow-guided filter passes the E17 gate on all three pairs (mean step 1.15–1.39× the skeleton, endpoints the tool's), with identity drift on match_4 and tile artifacts on the wide mismatch_4 by eye; LTX keyframe cuts on both mismatches at 0.8, is continuous on match_4 at 0.6, and with five skeleton frames anchored is continuous on mismatch_1 but copies the skeleton's crossfade; DreamMover and DiffMorpher fail the E16 gate (time, endpoints, licence, gated weights). Owner picks 2026-09-22: all five pairs `none`, "horrible neural slop"; **REJECTED as measured** (Rank revised 2026-09-23) |
| **TR8** splat quality (research E5) | compare `forward_splat` against the softmax-splatting reference (Niklaus & Liu 2020, CPU fallback) on three fixture pairs with strong occlusion; port its importance metric only if disocclusion edges are visibly better | Warp section | `[revert: commit]` | frame hash + the owner's eye on strips | M | TR2 sheet | OPEN — rank after TR6 |
| **TR9** class B semantics and the anchor editor (research E9, E10, E13) | SAM 2 masks + DINOv2 patch matches as automatic anchors for unrelated pairs; a stdlib `http.server` page to drag anchor pairs and preview; SAM-mask portals | Correspondence section; a new page (its own module is a decision) | new method values; default path untouched | on the 5 mismatch fixtures the morph lands the salient subject without hand anchors; the owner produces a liked morph with ≤ 5 anchors | XL | TR2 verdict on mismatch pairs; weights need the TR5 warmup shape | OPEN — after TR6 |
| **TR10** depth camera move (research E11) | Depth Anything V2 Small per endpoint, layered mesh, virtual dolly/zoom-through, inpainted disocclusions | new style | new `STYLES` value | a 2 s zoom-through on a landscape fixture without tearing; s/frame recorded | XL | TR5 warmup shape | **FIRST MEASUREMENT 2026-09-15** (`scripts/research/depth_dolly.py`, sheet `benchmarks/2026-09-15-generative.md §4`): Depth Anything V2 Small on MPS, 0.3–2.7 s per image; v0 = the class B pan-zoom scaled by 0.5 + disparity with the depth as the splat importance (no layered mesh, no inpainting): no tearing at 10 % or 25 % zoom, holes ≤ 0.9 % at the mid frame, mean step 10–14 % below the uniform pan-zoom; still a crossfade with parallax by eye, and as the bridge's skeleton it doubles the flicker. The layered mesh with inpainted disocclusions is not built. **Owner 2026-09-23: "really liked the effect on all individual images especially z25 … at least as option" → rank 1, build as `--camera` (Rank revised 2026-09-23)**; `ramp` control added the same day (weight-free, correlation 0.62–0.93 with the model's disparity on the two landscape pairs)). **BUILT 2026-09-23** as `transitions.py pair --camera flat|ramp|model --zoom` (`TRANSITIONS.md §2.3`; harness L 44–51, 51/51; `flat` byte-identical on 14 preset × class hashes; `model` = Depth Anything V2 Small behind `transitions.py warmup` + `models/DEPTH_MANIFEST.json`, CPU, 0.3 s per image; sweep with the three cameras on the twelve fixtures `benchmarks/2026-09-23-camera.md`, the owner's picks 2026-09-25: 0 of 12, every camera "unnecessary pans and basically cross fading"; `--camera` stays an option, not the transition (DECISIONS 2026-09-26) |
| **TR11** color science and HDR (research E12) | OKLab and optimal-transport transfer vs the Lab path on day→night pairs; 10-bit decode, HLG/PQ kept in the clip's transfer function, `yuv420p10le` HEVC tagged `hvc1` | Color and Encode sections | new option values | an HLG iPhone clip round-trips without banding or a brightness step | L | TR4 (video I/O) | OPEN — after TR4 |
| **TR12** product surface (research phase 4) | sequence editor page (items, cut points, one transition card per join, advanced disclosure), audio crossfade across the window, presets saved as JSON | new page; sequence JSON | — | the owner edits a sequence without the CLI | XL | TR4 | OPEN — last |
| **TR4b** motion carry-over (research E7) | velocity from the 4 frames before and after a cut, extrapolated into the first third of the transition and eased into B's motion | Render section, `motion_carry` flag (default on for clips, off for photos) | flag | on a pan→pan cut the mean flow direction never reverses | M | TR4 | OPEN — with TR4 |
| **TR2b** certainty floor for the DIS residual (proposed from the sheet) | in class A, when the mean forward-backward certainty is below a floor calibrated on the sheet (match pairs 0.33–0.81; mismatch_7 0.05), morph on the homography alone and print an INFO line; mismatch_7's clouds stop tearing, the five match pairs are byte-identical | `dense_displacement` | new method value `homography-only`; default untouched above the floor | harness: a synthetic pair with an inconsistent region routes to the fallback and the INFO line appears; sheet re-run diffed pair by pair | S | the owner's rating of mismatch_7 | PROPOSED |
| **TR2c** class B frame border (defect, backlog T13) | on the seven mismatched fixtures no rectangular edge of the warped finish frame is visible in any frame: warp only the salient region under a soft mask and crossfade the rest, or feather by the warped frame's validity; the mismatch strips re-rendered and re-picked | Warp / Render sections, class B path | new behaviour behind the class B branch only; class A byte-identical (hash) | harness: a synthetic class B pair whose finish frame is shifted shows no border step inside the canvas (column profile has no edge); sheet re-run on `mismatch_*` | S–M | — | **DONE 2026-09-14** — shipped as a coverage-preserving pan-and-zoom per frame (`panzoom_field`, method `saliency-panzoom`, `classb_zoom` 10 %) instead of a masked warp: the seven mismatched fixtures go from 9–52 % uncovered canvas to none; harness K 41–43 with the paid mutation; class A byte-identical; sheet re-run 2026-09-14; the owner's review of the re-rendered strips (2026-09-15): none accepted, "more subtle", still "junky cross-dissolves" |
| **TR2d** certainty-weighted warp | inside low-certainty regions the displacement is scaled toward zero so textures dissolve in place instead of arriving from one side (match_4) and the subject does not shift (match_5); measured against §5a's warning: no straight edge bends (signed-edge metric from Reveal harness O on the box edges) | `morph_frame` | new `TCFG` switch, default on only after the sheet and the edge metric agree | frame hash on match pairs when off; box-edge straightness on match_4/match_5 when on | M | TR2 picks (done) | **MEASURED 2026-09-15, as written REJECTED**: displacement × certainty detaches the changed object from the camera motion (match_5 2.9 px vs 70 px; mismatch_7's sky freezes while the skyline moves 330 px); the basket cannot see it (warping error falls). Superseded by the residual form `hold` inside TR14 (`TRANSITIONS.md §10.2`) |
| **TR13** canvas modes | `--canvas letterbox` (pad instead of crop, both photos fully visible) and `--canvas shared` (the largest area both photos cover, the old `common` rule) beside the default `finish`; the owner ruled 2026-09-14: "finish target ratio wins, also may want to add letterbox optional mode + find least common ration/area mode" | `common_canvas`, `cover` | new option values; default untouched | harness J | S | — | OPEN — when a pair needs it |
| **TR14** changed-region transformation (owner verdicts 2026-09-15) | design pass first: what a repainted box, a re-posed person or a changed sky should DO between the endpoints — the owner rejects both "texture arrives from one side" (DIS, 2026-09-14 picks) and "fades out and fades in, no transformations" (RoMa, 2026-09-15) for the paint on the box, likes the box holding its position ("i liked how the box itself holds position"), and asks for "interesting intermediate transformations of parts". Candidates to measure on match_4 / match_5 / match_3, cheapest first: (1) certainty-scaled displacement (TR2d) as the floor, (2) a designed deterministic effect inside the low-certainty mask (luma-ordered or gradient-flow reveal, structured dissolve) over RoMa's background field, (3) the generative tier (TR6) steered by the mask; keep "fade in place" as a named mode (owner: "may be useful as transition mode in our reveal app") | Correspondence + Render sections; a mask from RoMa certainty or the DIS changed-region detector | new mode / option values; default untouched | box-edge straightness (Reveal harness O) on match_4/5; the owner's clips verdict | M design, then L | TR5 probe scripts; TR6 measurement for candidate (3) | **DESIGN WRITTEN 2026-09-15** (`TRANSITIONS.md §10`; probe `scripts/research/tr14_variants.py`, nine variants on match_3/4/5 + mismatch_7, page `benchmarks/runs/2026-09-15/tr14/index.html`, numbers `benchmarks/2026-09-15-real-pairs.md`). TR2d as written rejected (an uncertain region stops following the camera: match_5's boxes move 2.9 px against 70 px of camera motion). The floor is `hold` = camera motion + (field − camera motion) × certainty: the object holds its place on every pair and mismatch_7 loses the cloth effect (warping error 0.0081 vs DIS 0.012, RoMa 0.0194). Three deterministic effects inside the photometric changed mask (`luma`, `edge-grow`, `melt`) and a weight-free `hold-dis` await the owner's picks. Implementation shape: one spec option `--changed flow\|hold\|luma\|edge-grow\|melt`, default `flow` byte-identical; five harness checks named in §10.6. Owner picks 2026-09-15: 0 of 4 acceptable, "hardly see any improbements since previous runs"; match_4 → `dis`, match_5 → `hold-dis`, match_3 → `roma`, mismatch_7 none; `melt` out ("too wobly"); direction = "even more transformation" with "a bit luma": next probe = motion-bearing field + partial-strength luma reveal + a stroke-flow along B's structure (sheet §Owner picks) |
| **TR7** speed pass, deterministic tier | per-frame cost at 1080p from 0.160 s toward ≤ 0.10 s and at 4K from 0.69 s toward ≤ 0.45 s, frames byte-identical (hash before/after on the harness pair) or the DECISIONS line says what moved and by how many levels. Profile 2026-09-13 (morph, M3 Pro, per frame at 1080p / 4K): color path 0.055 / 0.243 s (34 %), hole fill + mix + cast 0.049 / 0.213 s (30 %), two forward splats 0.040 / 0.159 s (25 %), two backward warps 0.017 / 0.071 s (10 %); correspondence once 0.36 / 1.51 s; encode 0.037 / 0.064 s per frame. Levers in order: Lab of A and B converted once per transition instead of per frame; in-place hole fill; `cv2.blendLinear` for the per-pixel mix; skip the backward-warp fallback when coverage has no hole; splat both endpoints in one scatter | `transitions.py` Color / Warp / Render sections | `[revert: commit]`; output unchanged by contract | Gate 1b + the frame hash | M | — | **rank 1** |

## Open decisions — answered by the owner on 2026-09-13 (verbatim; DECISIONS line of the same date)
1. **Rank:** "speed up phases so we have results including potential models quicker" → the Rank
   section above; TR slices before H/E slices.
2. **Fixture location (T4):** "gitignored fixtures INSIDE project" → `fixtures/` at the repo root,
   `/fixtures/*` ignored, `fixtures/MANIFEST.md` tracked.
3. **Lint gate (T6):** "At your discretion , i want to get to dense matcher upgrade and generative
   tier soon enough" → no lint gate now (agent's call: the two harnesses and `py_compile` are the
   gates; revisit at the first phase boundary). Backlog T6 → DEFERRED.
4. **Push policy:** "direct to `origin main` all the time , no need for branches" → the agent commits
   on `main` and pushes at Phase 4; no branches, no PRs.
5. **`HANDOFF.md` role:** "migrate and adjust as needed" → moved to `.claude/claude-docs/HANDOFF.md`
   with a dated §11 Amendments section; `TRANSITIONS.md` lives beside it.
Open now: none from this list. Standing questions live in `NEXT_SESSION_PROMPT.md §5`.

## Amendments
| Date | Change | By |
|---|---|---|
| 2026-09-13 | Drafted at bootstrap from the owner's directions and `HANDOFF.md §7/§9`; unranked | bootstrap session |
| 2026-09-13 | Added §TR (transitions engine, six slices) from the owner's order and the Impossible research artifact; TR1 shipped the same day; E3 stays as the Reveal-side `--style` lane and is now reached through TR3. H1/H3 unchanged, still unranked | transitions session |
| 2026-09-13 | Owner answered the five open decisions (quoted above); plan RANKED; TR7 (speed pass) added with the measured profile; TR5/TR6 carry the device rule from `HANDOFF.md §11`; design docs moved under `.claude/claude-docs/` | transitions session, evening |
| 2026-09-14 | Owner picks ingested (0 of 12 usable as-is, 3 closest-to-intent picks; E2 not met); canvas ruling "finish target ratio wins" implemented as the default policy; TR2c (class B border defect), TR2d (certainty-weighted warp), TR13 (canvas modes) added; blanket approval to fetch backends; PyAV approved | transitions session, 2026-09-14 |
| 2026-09-13 | Rank revised after the owner's first review of the sheet: TR5 → TR9 → TR6 → TR7 → TR2b → TR3/TR4 → H/E (quotes in §Rank) | transitions session, night |
| 2026-09-23 | TR10 built as the `--camera flat|ramp|model` + `--zoom` option of `transitions.py` (rank item 1 of 2026-09-23); TR10 row and §Rank item 1 marked built | transitions session, 2026-09-23 (second) |
| 2026-09-14 | TR2c shipped (class B pan-and-zoom within the coverage slack; T13 closed); TR5 preparation started in a scratch venv (romatch 0.1.2, MIT; DINOv2 backbone Apache-2.0; two weight files) | transitions session, 2026-09-14 evening |
| 2026-09-15 | Rank revised after the owner's direction (mismatches first, generative bridge on the deterministic skeleton, blanket approval for experiments and resources); TR6-A/TR6-B, TR10, TR9, TR14 second probe scheduled | transitions session, 2026-09-15 (third, late) |
| 2026-09-15 | Owner picks on the TR14 page ingested: 0 of 4 acceptable; the position hold reads as a fade; next probe = motion-bearing field + partial luma + stroke-flow; `melt` out | transitions session, 2026-09-15 (third, late) |
| 2026-09-15 | TR14 design written (`TRANSITIONS.md §10`): TR2d as written rejected, `hold` (residual form) is the floor, three deterministic effects + `hold-dis` on the review page for the owner's picks; TR6 researched and first-measured (SD 1.5 inpainting on MPS; LTX-2.3 MLX keyframe fetched) | transitions session, 2026-09-15 (third) |
| 2026-09-15 | Owner verdicts on the RoMa clips: 1 better / 1 same / 3 DIS better / 1 neither → TR5 not adopted as a drop-in; TR14 (changed-region transformation) added as the next design pass; rank now TR14 design → TR2d measure → TR6 measurement → TR9 → TR5 hybrid | transitions session, 2026-09-15 |
| 2026-09-14 | TR5 probe on match_2/3/5 at the owner's order: 2 wins, 2 ties of 4 pairs; speed gate for the dense matcher lifted by the owner; TR5 integration is the next slice, TR2d folds into it (RoMa's certainty is the weight) | transitions session, 2026-09-14 late |
| 2026-09-13 | Coverage map of the research artifact written (`TRANSITIONS.md §8`); every experiment not yet planned got a slice: TR8 splat quality, TR9 class B semantics + anchor editor + SAM portals, TR10 depth camera move, TR11 color science + HDR, TR12 product surface, TR4b motion carry-over. Owner: "make sure we account … for any useful content in … impossible artifact prototype" | transitions session, late |
| 2026-09-26 | Owner picks on the camera sweep ingested (0 of 12; all cameras "unnecessary pans and basically cross fading"); retrospective written (`audits/retrospective-2026-09-26.md`); §Rank 2026-09-26 PROPOSED, owner to confirm: goal paragraph → goal metrics → theme anchors (hand-placed, then Track B's recipe) → the combination where nothing aligns → cameras and generative parked | retrospective session, 2026-09-26 |
| 2026-09-26 | Owner confirmed the goal paragraph and refined F3 (verbatim in DECISIONS); §Rank 2026-09-26 RANKED; item 2 (goal metrics) BUILT; items 3–4 rewritten as the layered scene transition and generated keyframes on the second machine | retrospective session, 2026-09-26 (second half) |
| 2026-09-26 | Second half: owner named the second machine's docs and ordered the theme anchors; hand-placed anchors page (four variants × six pairs) + automatic probe rendered; `--anchor-falloff` built (T16 closed); Strix Halo route researched (track F) and recorded, not run | retrospective session, 2026-09-26 (late) |
