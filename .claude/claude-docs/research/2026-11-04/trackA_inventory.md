<!-- Provenance: written by an Opus 5.5 subagent (Track A, the inventory of every stage, knob, model and manual step of the four flows) of the Claude Code session of 2026-11-04 (the studio design; DECISIONS 2026-11-04 second line); copied verbatim from benchmarks/runs/2026-11-04/studio/agents/trackA_inventory.md (sha256 56ec05e37ee24c9b) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). The stage tables of the align, transition, director and loop flows with file:line anchors, the plan grammars, the models table, the workbench and the aligner page today, the review pages, the manual work no script covers, two loop_seq.py defects (both fixed the same session: `matte.all` crashed the chain, teleport, slide and rise methods; `breath.depth_k` did nothing without a parallax effect). A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

---
reader: the UI design session (cold; has the repo, not this thread)
shape: report
---
## Findings: Track A (inventory)

Summary. The owner asks for a transition or a loop. The operator (a Claude Code session) then runs one of four flows:
- `reveal.py align`, the aligner;
- `transitions.py pair`, the two-photo transition;
- `director_render.py`, which renders a hand-written or planner-written plan;
- `loop_seq.py prep → render → page`, the loop from a photo sequence.

Each flow writes a JSON file a UI can read without code changes (`metrics.json`, `report.json`, `info.json`, `measure.json` plus `prep.json`). Each also writes a contact sheet and an mp4.

Four facts limit a UI:
1. Most `CFG` keys in `reveal.py` and some `TCFG` keys in `transitions.py` are read as globals. No per-job setting reaches them, so exposing them needs code changes.
2. The workbench (`director_ui.py`) covers only the director flow. The loop flow has no UI (backlog T68 / plan row LP2).
3. Nine kinds of work have no script. Examples: reading boxes off a photo, writing a plan, choosing the registration anchor, the skeptic pass, page notes, grades, and moving files to and from the Strix Halo box. The full list is in the manual-work section.
4. I confirmed two `loop_seq.py` bugs in code. `matte: {"all": true}` crashes every method except plain `rife` (L488). `breath.depth_k` does nothing without a `parallax` effect (L1442–1446).

Method. Five read-only subagents each read one area in full. I spot-checked their anchors (manifests, `map_knob` lines, both bugs). Nothing was rendered; only `--help` ran.

Glossary:
- *The box*: the Strix Halo machine, reached by `ssh strix`. It runs the image models in Docker. The Mac is the M3 Pro laptop.
- *Skeptic pass*: an Opus 5.5 subagent crops every candidate at full size and judges it before the owner's page is built.
- *Class A / B* (`transitions.py`): A means the photos register by a homography (inliers ≥ 30). B is the pan-and-zoom fallback.

Line references: `R` = `reveal.py`, `T` = `transitions.py`, `D` = `scripts/research/director_render.py`, `U` = `scripts/research/director_ui.py`, `P` = `scripts/research/director_page.py`, `L` = `scripts/research/loop_seq.py`, `F` = `scripts/research/rife_probe.py`, `T.md` = `.claude/claude-docs/TRANSITIONS.md`, `PB` = `.claude/skills/reveal/references/loops.md` (the loops playbook), `DT` = `.claude/claude-docs/research/director-tooling.md`.

### Stages table

#### Align flow (`reveal.py`)

| flow | stage | script and entry point | inputs | outputs (files, keys) | knobs (name: default, range) | wall time as stated | what a UI could show | runs on |
|---|---|---|---|---|---|---|---|---|
| align | CLI `align` | `cmd_align` R:2517; argparse R:2544–2552 | before, after | `--out`/`before.jpg`, `after_aligned.jpg`, `transition.mp4` (with `--video`), `metrics.json` (the whole `status()` dict, R:2530); exit 0, or 2 with `FAILED:` | `--mode` reshot\|loose (reshot); `--video`; `--aspect` 4:5\|9:16\|16:9\|1:1\|original (4:5); `--style` wipe\|fade (wipe); `--seconds` 4.6, clamped [2.5, 12] (R:1451) | 2.2–16 s per real pair at native size (benchmarks/2026-09-13-real-pairs.md:115–134) | a run form; stage dots | Mac |
| align | CLI `serve` | `serve` R:1736 | — | HTTP on 127.0.0.1 | `--port` 8378 (R:92), `--no-browser`, `--workdir ./_reveal` | browser opens after 0.4 s (R:1745) | — | Mac |
| align | CLI `check` | `cmd_check` R:2422 | — | an OK / `!!` matrix: python, opencv, numpy, SIFT, MAGSAC++, HEIC, RAW, video, learned matcher (deep sha256, R:2409) | — | about 19 s (AGENTS.md: 18.5 s) | an environment health panel | Mac |
| align | CLI `warmup` | `cmd_warmup` R:2463 | network | `models/hub/checkpoints/*`, `models/MANIFEST.json` | — | not stated | a one-time setup step | Mac |
| align | modes | `MODES` R:157–176, `profile()` R:179 | — | — | reshot = `{}`. loose: ratio 0.82, min_matches 8, magsac_thresh 5.0, min_inliers 12, good_rmse 4.0, max_corner_shift 0.80, area_ratio (0.2, 5.0), ecc_trust_px 24, residual off, tune_shift 0.15, tune_rot 15, tune_scale 0.30, tune_keystone 6e-5, similarity_fallback, learned_always | — | a mode picker with a diff against reshot | Mac |
| align | CFG (R:103–148) | — | — | — | Read through the profile, so a mode can change them: ratio 0.75, min_matches 12, magsac_thresh 2.0, min_inliers 30, good_rmse 2.0, max_corner_shift 0.40, area_ratio (0.45, 2.2), ecc_trust_px 12, residual_mode auto, tune_* (±0.05 shift, ±3° rotation, ±0.06 scale, 3e-5 keystone), similarity_fallback F, learned_always F. Read as globals only: work_long 1600, render_long 2000, preview_long 1400, sift/orb_features 8000, ecc_iters 120, ecc_eps 1e-6, residual_cap 6, residual_min 0.4, residual_gain 0.01, residual_min_samples 2000, residual_gate_erode 25, changed_dilate 21, edge_dilate 3, sharpness_probe_px 3, not_max_penalty 0.6, expo_auto_bhatta 0.05, expo_auto_strength 70, video_fps 30, video_crf 18, video_feather 12, upload_cap 2 GiB. `residual_mode: on` has no surface at all | — | an "advanced" panel; the global-only keys need code first | Mac |
| align | decode | `load_image_rgb` R:223 | jpg/png/webp/tif/heic/dng/arw (R:186–189) | sRGB uint8; EXIF transpose; ICC to sRGB; rawpy applies the camera flip itself (R:236–241) | — | HEIC 1.9 s per file (HANDOFF §11) | format, size, ICC and orientation badges (none kept today) | Mac |
| align | working copies | `scaled_copy` R:264 | full images | 2000 px mid copy, 1600 px work copy, gray | work_long, render_long | — | the resolution ladder | Mac |
| align | SIFT / ORB matching | `_detect_and_match` R:303 | gray work copies | point pairs | sift/orb_features, ratio, min_matches | SIFT plus matching about 5 s of about 6 s (HANDOFF §8, sandbox) | keypoints and match lines | Mac |
| align | MAGSAC++ and similarity | `_estimate_h` R:477, `_estimate_similarity` R:489 | points | H, inliers, rmse; `+sim` tag | magsac_thresh; 10000 iterations, confidence 0.999 (R:482) | — | inlier and outlier overlay | Mac |
| align | sanity gate | `_h_sane` R:505 | H | bool (convex, area ratio, corner shift) | area_ratio, max_corner_shift | — | the warped quad over A, red when rejected | Mac |
| align | ladder and ranking | `estimate_alignment` R:624, `rank` R:647 | gray, colour | the winner `{H, method, inliers, rmse, ecc_rho}` | min_inliers, good_rmse; stops early when SIFT passes (R:659) | — | a candidate table (not serialized today) | Mac |
| align | learned matcher | `_match_learned` R:424, `_learned_models` R:385 | gray, capped at 1024 px | points or None | LEARNED_CAP 1024, LEARNED_FEATS 2048 (R:325–326); runs if learned_always, if there is no candidate, or if the best is below min_inliers (R:665) | 15 s at 768 px, 34 s at 1280 px on 4 sandbox threads (HANDOFF §5b); Mac time [INFERRED] | a "neural matcher used" badge | Mac CPU |
| align | arbitration | `_arbitrate` R:589 | candidates from more than one matcher family | winner by mean peripheral SSIM on one fixed mask | periphery ≥ 4096 px, else None (R:611) | — | per-candidate SSIM bars (log only today, R:617) | Mac |
| align | phase-correlation rescue | `_phase_corr_h` R:574, used R:689–696 | gray | translation, then ECC; accepted at rho > 0.35 | response floor 0.03 | — | a fallback badge | Mac |
| align | ECC refine | `_ecc_refine` R:525; mask R:705–720 | H, periphery moved to B's frame | H_ref, rho; the feature H is kept when drift exceeds the trust region | ecc_iters, ecc_eps, ecc_trust_px | — | drift before and after, rho | Mac |
| align | manual params | `manual_matrix` R:743, `_clamp_params` R:1557 | dx, dy (fractions), rot (°), scale, kh, kv in [-1, 1], exposure 0–100 | M applied after H, in A's frame | tune_* clamped per mode | re-render about 0.4 s (HANDOFF §8), 0.3–1 s (§4) | live overlay, grid, onion skin | Mac |
| align | valid mask and crop | `warp_valid_mask` R:777, `largest_interior_rect` R:785, `crop_rect` R:811 | warped mask | crop rectangle, even sides | small_long 700, min 16 px (inline) | — | the crop rectangle; the crop jumps while tuning (HANDOFF §9.3) | Mac |
| align | changed mask and periphery | `changed_region_mask` R:879, `peripheral_mask` R:916 | A, warped B, valid mask | uint8 masks | changed_dilate 21; Otsu with floor 40; periphery erode 15 | — | change heatmap, static-region tint (not kept) | Mac |
| align | residual field | `residual_flow` R:1056, `apply_residual` R:1159, gate R:1268–1299 | gray, periphery, valid, changed | a 2-channel field or None | residual_mode auto (off in loose), cap 6 px, median within (0.4, 9), min_samples 2000; DIS MEDIUM, cubic IRLS with 3 Huber iterations | — | field quiver or heatmap; s_before and s_after (log only, R:1294) | Mac |
| align | confidence score | `confidence_score` R:982 | inliers, rmse, local_max | 0–100 = 100·(0.70·r + 0.30·n), r = clip(1 − (rmse − 0.5)/3.5), n = clip(inliers/75); ×0.6 when not a local max | not_max_penalty 0.6 | — | the score split into its terms | Mac |
| align | metrics | R:1302–1338; `edge_overlap` R:924; `bhattacharyya` R:939; `peak_sharpness` R:949 | — | `metrics{method, inliers, rmse_px, ecc_rho, peripheral_ssim, sharpness, local_max, edge_overlap, luma_distance, residual, changed_pct, passed, confidence}` | sharpness_probe_px 3 | — | a full diagnostics panel | Mac |
| align | exposure | `exposure_params` R:1017, `apply_exposure` R:1035 | A, warped B, periphery | Reinhard Lab transfer, gain [0.4, 2.5]; auto at 70 when Bhattacharyya > 0.05 | expo_auto_*, the `exposure` param | — | histograms before and after | Mac |
| align | previews | `render_previews` R:1389 | params | `preview_{before,after}.jpg` 1400 px q88 | preview_long | — | — | Mac |
| align | stills and video export | `export_images` R:1405, `export_video` R:1433, `run_export` R:1496 | aspect, style, seconds | `before.jpg`, `after_aligned.jpg` q95, `transition.mp4` (H.264, yuv420p) | ASPECTS R:191 (4:5 1080×1350, 9:16 1080×1920, 16:9 1920×1080, 1:1 1080², original ≤ 1920); fps 30, crf 18, feather 12 px; hold = max(0.8, 0.22·s); cosine ease R:1429; wipe or fade | 3 s 1080² video about 4 s (HANDOFF §8, sandbox) | timeline and ease curve | Mac |

#### Transition flow (`transitions.py`)

| flow | stage | script and entry point | inputs | outputs (files, keys) | knobs (name: default, range) | wall time as stated | what a UI could show | runs on |
|---|---|---|---|---|---|---|---|---|
| transition | CLI `pair` | `cmd_pair` T:1566; argparse T:1587–1618 | before, after | `--out`/`transition.mp4`, `strip.jpg`, `report.json`; exit 0, or 2 with `FAILED:` | `--seconds` 1.0 [0.1, 10]; `--fps` 30 (≥ 1); `--preset` morph\|dissolve\|flow-dissolve\|snap-morph\|iris\|wipe\|luma; `--color` 0.7 [0, 1]; `--warp` 1.0 [0, 1]; `--max-long` 0 (native); `--canvas` finish\|common; `--anchors` "" ("ax,ay,bx,by;…", 0 or ≥ 3 pairs); `--anchor-falloff` 0.45 [0, 0.5]; `--class` ""\|A\|B; `--camera` flat\|ramp\|model; `--zoom` 0.10 [0.02, 0.5] | 12 real pairs ≤ 1920 px, 1 s morph: 4.7–13.4 s (T.md:241), 1.5–11.7 s (T.md:247); 1200×900 synthetic: morph 3.1 s, wipe 1.6 s (T.md:235) | a form with a preset picker | Mac |
| transition | spec, presets and curves | `TransitionSpec` T:180, `clamp` T:205, `PRESETS` T:245, `CURVES` T:161, `progress` T:232 | — | the clamped spec | No CLI flag, presets only: style, warp_curve, mix_curve, mix_delay, portal, portal_feather 0.08. Curves: linear, ease, ease-in, ease-out, snap, hold-then-go. The CLI always passes `--warp`, so the presets' warp_amount is overwritten (inferred from T:1569, T:262; not run) | — | t_warp and t_mix plotted against u | Mac |
| transition | decode and canvas | `load_image_rgb` T:289, `common_canvas` T:356 | A, B | an even canvas; both photos cover-cropped | canvas, max_long | HEIC 1.9 s (T.md:243) | crop rectangle on both photos | Mac |
| transition | correspondence router | `dense_displacement` T:813 | A2, B2, anchors, class, camera, zoom | dAB, dBA, wA, wB, class, method, diag | class A when the H is sane and inliers ≥ 30; the camera is ignored on class A or with anchors (T:842–845) | 0.36 s at 1080p, 1.51 s at 4K (T.md:237) | class badge, method string, INFO lines | Mac |
| transition | class A matching | `sparse_homography` T:402, `_sane` T:431, `_homography_guided` T:449, `consistency_weight` T:462 | gray | H plus a residual DIS field; a certainty map | sift 6000, ratio 0.75, min_matches 12, magsac 2.5 px, area (0.15, 6.0), consistency_sigma 3 px | — | match lines, flow colour wheel, certainty heatmap | Mac |
| transition | anchors | `parse_anchors` T:1549, `mls_affine` T:522, `border_weight` T:549 | point pairs | MLS field, with the falloff band | falloff 0.45 smoothstep; anchor_blend 0.7 on class A (T:129) | — | draggable point pairs, falloff overlay | Mac |
| transition | class B | `salient_box` T:473, `panzoom_field` T:496 | images | pan-and-zoom field, pan_fraction | zoom 0.10; certainty fixed at 0.5 | field 0.03–0.15 s (T.md:245) | salient boxes, animated zoom rectangle | Mac |
| transition | camera move | `ramp_disparity` T:771, `model_disparity` T:745, `depth_modulate` T:776 | disparity in [0, 1] | scaled field | depth_gain 1.0 (0.5× far to 1.5× near), w_floor 0.2, percentiles (2, 98), depth_long 1024 | correspondence 2.4–2.9 s with `model`, 0.08–0.45 s with `flat` (T.md:259) | disparity heatmap | Mac CPU |
| transition | warp, splat, mix | `forward_splat` T:927, `fill_holes` T:991, `morph_frame` T:999, `portal_mask` T:1020, `luma_mask` T:1104 | frames, field, t | uint8 frame | splat_scale 4, sharpness 10, hole_thresh 0.05, mix_blur 3; portal centre (0.5, 0.5) and luma softness 0.15 fixed in code | morph frame 0.16 s at 1080p, 0.69 s at 4K (T.md:236) | coverage and hole map, mask preview | Mac |
| transition | colour path | `lab_stats` T:1052, `apply_stats` T:1065, `color_pair_at` T:1089 | A, B, u | colour-shifted pair | color_strength 0.7, gain clip (0.4, 2.5) | 0.055 s at 1080p per frame (T.md:236) | Lab mean and std across u | Mac |
| transition | quality measures | `assess` T:1252, `flicker` T:1156, `endpoint_fidelity` T:1167, `goal_numbers` T:1198 | proxy frames at 480 px | `quality{warping_error, flicker{mean, max, spikiness, edge_ratio}, goal{feat_floor, laplace_floor, contrast_floor, dissolve_fit, motion_share}, endpoint{first_vs_A, last_vs_B}}` | quality_long 480; edge_ratio below 1.5 is the harness bar (T.md:183) | about 1 s per 30 frames (T.md:132) | step bar chart, cut warning, goal gauges | Mac |
| transition | encode and strip | `FrameEncoder` T:1378, `render_pair` T:1421 | frames | mp4 (libx264 crf 18, yuv420p); `strip.jpg` (min(8, n) tiles, 160 px tall, first and last included) | video_crf read as a global, so `cfg=` does not reach it (T:1390) | 0.037 s per frame at 1080p (T.md:238) | contact sheet | Mac |
| transition | `check`, `warmup` | `cmd_check` T:1461, `cmd_warmup` T:1490 | — | an OK matrix with a depth row; the depth manifest | warmup self-test needs bottom > top + 0.3 | warmup time not stated | health panel | Mac |

#### Director plan flow (`director_render.py`)

| flow | stage | script and entry point | inputs | outputs (files, keys) | knobs (name: default, range) | wall time as stated | what a UI could show | runs on |
|---|---|---|---|---|---|---|---|---|
| director plan | CLI | D:2077–2097 | plan.json, out dir | `transition.mp4`, `montage.jpg` (3 columns), `info.json`, JSON on stdout | `--concept` (first), `--seconds` 3, `--fps` 30, `--max-long` 1920, `--set k=JSON`, `--progress` (`PROGRESS i n` to stderr every 5 frames, D:1824), `--resolve-only`, `--layers-dir`, `--mattes-dir` | full 1920 px: 32.8–66.4 s total `wall_s` (on-disk info.json, rounds 12–13); 480 px draft: 10.3–13.4 s (ui1_build.md:9, ui1_review.md:163) | progress bar | Mac |
| director plan | scene, anchors, camera | D:418–672 | `fixtures/<pair>_S/_F`, `layers_v3/<photo>/layers.json` | canvas, camera (similarity or homography), quad, front mask | `end_scale` (disc only), `front_ids`, `cont_feather` 1.0 | not stated per stage | anchor and camera overlay | Mac |
| director plan | depth parallax | D:674–742 | disparity (`T.model_disparity`) | dA, dB maps | parallax_gain 0.3, gain_A = gain, blur 6, sources [A,B], push 2.5 for quad/rect else 0, push_floor 0.3, front_in 0.15, front_margin 0.05 | — | disparity map | Mac CPU |
| director plan | B front layer and plate | D:748–836 | B's element mattes | B_plate, front alpha | front_hole_max 0.005, plate_fill pullpush\|telea, front_per_element true | — | front matte | Mac |
| director plan | layers (one per transform) | D:862–1303 | transforms | layers; `unplaced` | `<name>.window`, `.mix`, `.skip`, `.<param>`; `plate` true | — | per-layer mattes, timeline bars | Mac |
| director plan | motion model and reveal guard | D:1307–1379 | `motion{continuous, edge 0.35, overlap 0.1}`, `reveal{guard, ramp 0.08, band 0.01}` | adjusted windows, holds | `motion`, `guard`, `<name>.arrive`, `.reveal_ahead` | — | the resolved timeline (the workbench draws only the requested one) | Mac |
| director plan | plate A and sky window | D:1384–1468 | footprints | A_base, sky config | `sky`, `sky.<k>`, `key_end` 0.45 | — | sky window | Mac |
| director plan | resolve-only exit | D:1796–1807 | — | `canvas_A.png`, `canvas_B.png`, `anchors.json`, `info.json` | — | about 4 s at 480 px (ui1_build.md:105) | the overlay source | Mac |
| director plan | frame loop | D:1821–1998, `compose_A` D:1471 | everything above | frames; frame 0 = A and the last frame = B, byte-exact | end_window, reflect 0.18, end_kind, end_band 0.16, end_radius_px 0.6·max(A), vacated_first 0.35, hole_reveal_from 0.1, hole_reveal_over 0.35 | — | scrubber | Mac |
| director plan | decoded-clip measures | D:2000–2058 | the mp4 | `info.json` keys in the next table | — | — | motion, step and b_inside charts | Mac |

#### Loop flow (`loop_seq.py`)

| flow | stage | script and entry point | inputs | outputs (files, keys) | knobs (name: default, range) | wall time as stated | what a UI could show | runs on |
|---|---|---|---|---|---|---|---|---|
| loop | prep: decode | `cmd_prep` L:234 | `*.jpg` in a folder, sorted by name (≥ 2) | frames | `--long` 1920 (downscale only) | none in code | thumbnails | Mac |
| loop | prep: far-field mask | L:251–255 | depth maps | depth < T masks | `--bg-depth` 0 (off), 0–1 | — | far-field share per still | Mac CPU |
| loop | prep: register | `register_all` L:193 | frames, cuts, masks | one map per still | SIFT 6000 on a 1200 px proxy, ratio 0.75, MAGSAC 2.5 px; `--min-inliers` 40; then a chain through i−1, then ECC affine (cc ≥ 0.45), then identity; `--cut i,j` declares identity. The sanity range in code is scale 0.5–2.0 and corner move ≤ 0.6 (L:98, L:103); `--help` says 0.85–1.15 | — | per still: method, inliers, overlay montage | Mac |
| loop | prep: ECC refine | L:223–228 | SIFT map and mask | refined map | `--ecc-refine` off; only with `--bg-depth` | — | `ecc_cc` | Mac |
| loop | prep: lock windows | L:259–273, `_window_shift` L:172 | windows on the reference still | map plus a translation | `--lock-window "x0,y0,x1,y1;…"`; 30 px search margin | — | drawable boxes; offsets and correlation | Mac |
| loop | prep: depth blend | L:275–333 | depths, a second all-keypoint fit | per-pixel remap | `--depth-blend` ""\|lo,hi\|auto (needs `--bg-depth`); separation gate 0.05 | — | `fit_separation_p95_px` | Mac |
| loop | prep: canvas, crop, write | L:280–363 | maps | `k<i>.png`, `depth_k<i>.npy` (with `--bg-depth` or `--depth-maps`), `prep.json` | `--ref` −1 (the trusted still with the largest scale); crop shrinks from the worst edge | — | canvas and crop | Mac |
| loop | render: timeline | `render_plan` L:1373 | plan, `in/k*.png` | frames, `frames.json` rows | `--fps` 25, `--draft` 0 (else a long edge), `--set key=<json>` (top-level keys only, L:1525) | RIFE 0.96–1.77 s per in-between (measure.json of 2026-10-30); about 1.3 s at 1900 px (PB §7) | timeline editor | Mac CPU |
| loop | render: effects | L:1436–1448 | frames, depth maps | frames | breath, parallax, glow (see the grammar table) | — | effect toggles with curves | Mac |
| loop | render: crop and encode | L:1449–1477 | frames | `loop.mp4` (crf 14, libx264), `loop.gif` (gif_long 540, 255 colours, sierra2_4a dither) | `crop` (centre fraction), `crf`, `gif_long` | full size `sheets`: render_s 22–594 s; 640/960 px drafts 1.7–21 s (run outputs) | mp4 and gif players | Mac |
| loop | render: sheet and measures | L:1478–1520 | decoded mp4 | `sheet.jpg` (all frames if ≤ 48, else every second; red `g` on generated frames), `measure.json`, `plan.json` | — | — | sheet, step chart | Mac |
| loop | page | `cmd_page` L:1562 | `--root`, `--notes {seq:{variant\|"*": text}}` | `index.html`, `in/<seq>/keys.jpg` | `--order`, `--title` "Halloween loops", `--intro`, `--footer` | — | see the review-pages section | Mac |

### Plan and timeline grammars

#### Director plan (`scripts/research/plans/SCHEMA.md` and D)

Where the code default differs from SCHEMA's value, the code default is the one that takes effect. SCHEMA's value is an example.

| key | values and defaults (cite) |
|---|---|
| top level | `pair`, `planner{model, temperature, prompt_sha256, date, brief}`, `reading{a,b}`, `relation` themed\|unrelated\|aligned, `concepts[]` (SCHEMA:12–26) |
| concept | `id`, `rank`, `idea`, `container`, `anchors[]`, `pullback`, `transforms[]` (at most 3, SCHEMA:87), `end_effect`, `helper` (not built), `knobs[{name, range, default, what}]`, `risk`, `motion`, `reveal`, `params.occluder_row`, `params.key_start`, `key_end`, `key_band` |
| container | `kind` disc\|quad\|rect\|none; `rim` soft\|matte\|glass (reflect 0.18); `spec{front_ids, front_margin 0.05, front_groups}`; `params{feather_px 1.0, reflect, sky}` (D:587–656, 855) |
| A anchors | `circle_fit{box, min_L 120}`, `element`, `box`, `point`, `rows`, `dark_line{rows, thickness 7, contrast 8}`, `disc`, `all`, `luma_above` (not in SCHEMA) (D:494–578) |
| B anchors | `bright_disc{box, frac 0.8}`, `element`, `box`, `point`, `line{ids or points, width 4}`, `dark_band{box, pct 25}` (D:458–491) |
| pullback | `ease` smootherstep\|linear; `parallax{kind, gain 0.3, gain_A, blur 6, sources, a_elements, push, push_floor, front_in}`; `params.end_scale` (disc only) |
| transform, common keys | `name`, `by`, `a`, `b`, `window`, `mix` luma\|edge\|noise\|none (luma), `depth` inside\|front, `params.ease`, `edge` 0.35, `rate`, `plate`, `skip`, `hole_reveal`, `hole_from`, `hole_over`, `reveal_ahead`, `arrive` |
| `colour` / `hold` / `exit` | colour: feather 3, strength 0.85. hold: feather 2. exit: direction left, fade 0.3, feather 1.5 |
| `recede` | end_radius 30, profile linear\|geometric, end_shape b_blob, limb_flatten 0.55, rim_in 0.55, rim_out 1.0, blob_L 110, mix_window [0.55, 0.95], mix_ramp 0.5, and 10 more (D:932–998) |
| `line_to` | width 4, stretch 1, end_taper 0.12 (0 for a wire), thin_power 0.45, mix_window [0.3, 0.9], hide_target true |
| `morph_to` / `move_to` | mass bright\|dark, alpha mask\|mass, margin 0.15, work_px 3200, ot_grid 64, ot_eps 0.04, seed 7, noise_px 24, mix_window [0.25, 0.9], grow_matte true (D:1041–1153) |
| `keyframe_chain` | keyframes [], frame canvas\|A, times (even, a list, or "arc"), arc_floor 0.2, lead, face_guide, guide, matte_grow 0.03, damp 0.5 or 1.0 (D:1172–1302) |
| end_effect | kind luma_reveal\|edge_reveal\|b_luma_reveal\|radial_reveal (radial is not in SCHEMA); window [0.78, 1.0]; band 0.16; vacated_first 0.35 |
| sky window | shape radial\|radial_out\|frame-feather; radial_end 1.6, radial_width 0.35, follow 2.0, band window\|limb, ring b\|window, key_window [0, 0.45], key_band 0.10, stars, star_window [0.1, 0.9] (D:1448–1596) |
| layers and mattes | soft matte `<mattes>/<photo>/el_<id>.png`, falling back to the hard mask (recorded in `matte_fallbacks`) (D:212–244) |

`--set` knobs (D `knobs.get`): motion, guard, end_scale, front_ids, cont_feather 1.0, parallax_sources, parallax_gain 0.3, parallax_gain_A, parallax_blur 6, parallax_A_elements, parallax_push, push_floor 0.3, front_in 0.15, front_margin 0.05, front_hole_max 0.005, plate_fill pullpush, front_per_element true, plate true, sky and sky.<k>, key_end 0.45, hole_reveal_from 0.1, hole_reveal_over 0.35, end_window, reflect 0.18, end_kind, end_band 0.16, end_radius_px, vacated_first 0.35, plus `<transform>.window`, `.mix`, `.skip` and `.<param>`.

`info.json` keys:
- scene: canvas, pair, concept;
- the container's anchors and camera, and circle_fit;
- conditionally: parallax{…}, front_holes, front_share, motion{kind, edge, overlap, adjusted, beats, held}, guard[{name, arrive, share_B}], sky{…}, layers[] (per layer: name, by, window, chain{…segments}, ot, depth, …), unplaced, matte_fallbacks;
- after the frame loop: frames, step_first, step_second, step_last, step_max, seconds, fps, knobs, wall_s, motion_px[], motion_median_px, motion_pauses, motion_jumps, guard_share_max, b_inside[[i,v]], b_inside_first, residual_edges, residual_edge_max, halo[[f, step, ring, r]], halo_step_max, halo_ring_max;
- provenance: plan_sha256, renderer_md5, transitions_md5, layers_dir, mattes_dir (D:2052–2058, 2099–2102).

#### Loop plan (`scripts/research/plans/loops/SCHEMA.md` and L)

Top-level keys: `seq`, `in`, `title`, `gag`, `timeline`, `effects` [], `matte{thr 14, grow 0.015, feather 0.01, min_share 0.0005, all false}`, `crf` 14, `gif_long` 540, `crop`. Ease names: linear, smooth, snap, accel, accel3, decel, sine (L:368–376). SCHEMA omits accel3 and sine.

| op | keys | defaults | file:line |
|---|---|---|---|
| hold | key, hold | hold 1 | L:1389–1394 |
| transition (every method) | to, n, method, ease | method rife, ease smooth | L:1395 |
| `rife` | margin, local[{box, ease, feather}] | margin 0.0 in code (SCHEMA shows 0.04, the angel value); local ease snap, feather 0.01; each box costs one extra RIFE call per frame | L:427–465 |
| chain (`through`) | through[], weights, soft, knot_margin | equal weights, soft 0, knot margin 0; method dissolve or RIFE | L:468–499 |
| `dissolve` | — | a whole-frame blend (not inside the matte) | L:502–508 |
| `morph` | preset, warp, color, anchors, falloff | morph, 1.0, 0.7, —, 0.25 (calls `transitions.py`) | L:511–525 |
| `teleport` | out_box, in_box, mode squeeze\|fade, span, glow, box_mode, box_thr, box_open, rest, flash, flash_gain | squeeze, 0.6, 0.6, person, 30, 0.02, rife, 0, 0.6 | L:561–618 |
| `slide` | box_a, box_b (required), matte_a/b{kind box\|grabcut, thr, open, iters, exclude[], erode}, donor_box_b, fill, floor_y, window, mode fly\|dissolve, window_out, window_in, slide_ease, blur, blur_k | grabcut iters 5; window [0.2, 0.8]; fly; [0, 0.55]; [0.45, 1]; sine; blur true; 0.5 | L:647–815 |
| `rise` | ghoul_box, man_box (required), direction, mattes, fill, floor_y, start_offset, window, rise_ease | up, grabcut, vertical, [0, 0.1], [0.35, 1.0], smooth | L:818–861 |
| `snap` | blur_frac, direction | 0.015, vertical | L:864–881 |
| `cut` / `rewind` | rewind: from, stride | 0, 3 | L:1422–1428 |
| `slices` | angle, bands, widths, families, slide, travel, order, seed, stagger, dur, ease, samples, shutter, shadow and about 20 more | 62, 12, …; `n` is computed and written back | L:896–1055 |
| `sheets` (step) | n, angle, motion normal\|lateral, ease, feather, shadow, shadow_px, shadow_from, overlap_alpha, shutter, samples_max, parallax, edge_depth, layer_soft, objects | 62, normal, **linear** in code (SCHEMA says sine), 1.5 px, 0, 40 px, front, 1.0, 0, 24, 0, 0, 0.06 | L:1086–1269 |
| per sheet | key, side ±, width (fraction or "photo"), carry, lag, dur, scale, layer [lo, hi], layer_y, shadow, name; the reach is computed (L:1144–1154) | +, 0.8, 1.0, 0, n−lag, 0 | L:1140–1236 |
| sheet objects[] | name, box, lead, linger, seasons | lead 6, linger 10 in code (SCHEMA shows 8/14); GrabCut plus seamlessClone | L:1060–1199 |
| `breath` | z (required), cx, cy, depth_k, depth_clip | —, 0.5, 0.5, 0, 0.6; 1 + z·sin²(πu) | L:1272–1340 |
| `parallax` | amp (required), ref_at or ref, dir, shape sin\|pulse, dir2, shape2, amp2, sigma | ref 0, [1, 0], sin, pulse, 0.5, 3 px; needs `depth_k*.npy` | L:1299–1351 |
| `glow` | box, thr, sigma, mix, gain, shape | [0,0,1,1], 235, [0.012, 0.05], [0.6, 0.4], 0.15, pulse | L:1354–1370 |

`prep.json` keys:
- top level: date, seq, sources[{source, bytes, sha256, native, scaled}], long, cuts, bg_depth, depth_blend (a boolean only), reference, reference_size, crop, canvas;
- per still (`frames[i]`): method, trusted, inliers, matches, sane, why, residual_px, direct, chain, cc, seeded, ecc_cc, lock{windows, offsets_px, shift_px, corr}, scale_to_canvas, H_to_canvas, H_near_to_canvas, depth_blend{…}.

`prep.json` does not record `--min-inliers`, `--ecc-refine`, the requested `--ref`, or the `--depth-blend` numbers. `plan.json` does not record `--fps`.

`measure.json` keys (L:1506–1514):
- frames, fps, seconds, canvas;
- render_s (timeline start to after the crop);
- step_mean, step_max, step_max_at, steps[] (mean absolute difference between consecutive decoded frames);
- seam_step (the last frame against the first);
- faces_per_frame, faces_keyframes (YuNet counts);
- generated_frames, generated_share;
- dexp_max (the double-exposure share, `dexp_share` F:212);
- rife_seconds_per_frame;
- md5_mp4, md5_gif, gif_bytes, mp4_bytes, draft, plan_sha256.

The playbook's bars:
- no run of steps below 0.3 while motion is open;
- no step above 3× its neighbours outside a declared cut or snap;
- the seam step about 1–3;
- dexp 3–11 % is the floor on these pairs (PB §6).

### Models table

| model | task | weights path | manifest / offline gate | loader (file:line) | time per call | device |
|---|---|---|---|---|---|---|
| DISK + LightGlue (kornia) | learned feature matcher in the align ladder | `models/hub/checkpoints/` (`depth-save.pth` 4.4 MB, `disk_lightglue_v0-1_arxiv-pth` 47.6 MB); TORCH_HOME pinned (R:333) | `models/MANIFEST.json` (sha256 per file, self_test_matches 658); `_ALLOW_DOWNLOAD` only in `reveal.py warmup`; a missing manifest falls back to `None` silently (R:432–434) | `_learned_models` R:385, `_match_learned` R:424 | 15 s at 768 px, 34 s at 1280 px (HANDOFF §5b, sandbox) | Mac CPU |
| Depth Anything V2 Small (24.8 M params, 99 MB) | disparity for `--camera model`, director parallax, loop `--bg-depth`, `depth_k*.npy`, parallax and sheets layers; also inside layer_source | `models/depth/hub/…` (HF_HOME, T:600–621) | `models/DEPTH_MANIFEST.json` (files and links, prep 518/14, self-test 0.0/0.866); only `transitions.py warmup` downloads; HF_HUB_OFFLINE set | `_depth_model` T:704, `model_disparity` T:745 | 0.27–0.31 s per 1024 px image on 6 CPU threads; load 1.2 s, 4.9 s cold (T.md:259) | Mac CPU (no device flag) |
| RIFE v4.26 (Practical-RIFE IFNet_HDv3) | in-between frames for loops and the director's keyframe chain | `benchmarks/runs/2026-10-21/rife/weights_v4_26/` and `practical_rife_code/` (F:61–62) | `RIFE_MANIFEST.json` in that folder; the run checks sha256 and refuses on a mismatch (F:127–155); only `warmup` downloads (HF `hzwer/RIFE@01fdc7e9`, GitHub `Practical-RIFE@bbfd2ea9`) | `load_rife` F:126, `rife_at` F:160; lazy wrapper L:410–421 | 0.96–1.77 s per frame (run outputs); about 1.3 s at 1900 px (PB §7) | Mac CPU |
| YuNet 2023mar | face count, as a measure only | `benchmarks/runs/2026-10-18/face/face_detection_yunet_2023mar.onnx` (L:59) | `FACE_MANIFEST.json` exists but nothing checks it (F:70) | `faces_of` F:180 | not stated | Mac cv2 |
| ViTMatte small (composition-1k) | soft alpha per element | `benchmarks/runs/2026-10-17/mattes/hf_home/` | `MATTE_MANIFEST.json` (repo, revision, sha256); `run` refuses without it | `load_model` matte_source.py:79 | 0.5–16 s per element, 2–25 s per photo (DT:22) | Mac CPU (`--device mps` optional) |
| OneFormer Swin-L, CLIPSeg (Grounding DINO + SAM 2.1 optional) | element cut: label, group, depth rank | `benchmarks/runs/2026-09-28/layers/hf_home` | no manifest file; pinned revisions in code, `local_files_only` unless `--fetch` | `_load` layer_source.py:274 | 8.8–22.5 s per photo (T.md:269) | Mac `.venv` |
| SAM 3 (`facebook/sam3` rev 3c879f39), Grounding DINO + SAM 2.1 | instance split and merge of elements | the same hf_home | pinned revisions, offline env vars, socket connects refused and counted (layer_merge.py:169–180) | `Sam3` layer_merge.py:261, `GdinoSam2` :204 | 23.4–39.8 s per photo, SAM 3 28.6 s; peak RSS 6.5–12.7 GB (T.md:272) | Mac, scratch venv `benchmarks/runs/2026-09-28/layers/venv` |
| FLUX.2 klein 4B / 9B Q8_0 | generated keyframes and plates | `$MODELS` on the box (`~/keyframes/models_klein*`) | Docker `--network none --read-only`, image pinned by digest; memory pre-flight exits 3; writes `<NAME>.manifest.json` | `strix_keyframe.sh` :115–127 | 4B 38 s; 9B 50–95 s; plates 89–136 s (`.serena/memories/project/strix-halo-box.md`) | the box (Vulkan) |
| Qwen-Image-Edit-2511 Q4_K_M | keyframe edit (the script's default `MODEL`) | `~/keyframes/models` on the box | as above | `strix_keyframe.sh` :100–114 | 1,084 s with one reference, 1,804–1,941 s with two (strix-halo-box.md:46–68) | the box |
| FLUX.3 image klein bf16 | keyframes (research) | `~/keyframes/models_flux3` | as above | `strix_keyframe.sh` :128–145 | 312 s at 1024×1280, 16 steps (script :34); 180–923 s (DT:78) | the box |
| SD 1.5 inpainting, DINOv2-S, RoMa, Mask2Former (research only) | gen_bridge, auto_anchors, roma_probe, mask_routes | the default HF cache or per-script hf_home | **no offline gate** on gen_bridge, auto_anchors (YuNet fetched by `urlretrieve`), roma_probe, `depth_dolly --depth` | see each script | SD 8.6–18 s per frame; RoMa 35–55 s per pair | Mac (scratch venvs) |

Keyframe helpers with no model of their own (Mac):
- `keyframe_clip.py`: composites, clip, page with `keyclip_picks.json`.
- `keyframe_layer.py`: registers a keyframe onto C(t) with colour per layer.
- `keyframe_prompt.py`: prints the per-layer edit prompt.
- `keyframe_screen.py`: sun centroid, MAD, Laplacian variance, box log parsing.
- `theme_anchors.py`: renders hand anchors through `transitions.py`.
- `chain_luma.py`: a several-still chain through `reveal.run_alignment`; 34 s per render (benchmarks/2026-10-09-fabra-boxes.md:69).

`strix_keyframe.sh` runs on the box against folders already there. It copies nothing (details in the manual-work section).

### The workbench today (`director_ui.py`, 127.0.0.1:8379)

Endpoints:

| method | path | params | returns |
|---|---|---|---|
| GET | `/` | — | the page (U:812) |
| GET | `/api/pairs` | — | pairs with plans, layers, mattes; renderer flags (U:814, 131–147) |
| GET / POST | `/api/jobs` | POST `{pair}` | list, or `{id}`; the POST also starts the analysis (U:816, 865) |
| GET | `/api/plans/<stem>` | — | plan_view: sha256, relation, reading, planner, concepts (U:823) |
| GET | `/api/jobs/<id>` | — | job, tasks, analysis, plans, renders, last_picks (U:834, 711) |
| GET | `/api/jobs/<id>/overlay/<A\|B>/<kind>.png` | base, elements, disparity, matte_<id> | a 960 px PNG, cached (U:836, 526) |
| GET / HEAD | `/api/jobs/<id>/file/<path>` | a path under the job, fixtures, layers or mattes | the file with Range support; 403 otherwise (U:840, 727) |
| GET | `/api/jobs/<id>/tasks/<tid>` | — | state, progress, elapsed_s, log_tail, expected_s (U:844, 383) |
| GET / POST | `/api/jobs/<id>/frame` | `rid, i` / `{rid, index, mark}` | a PNG; a marked frame saves to `owner_frames/` (U:848, 883) |
| POST | `/api/jobs/<id>/analyze` | — | three tasks (U:874, 430) |
| POST | `/api/jobs/<id>/render` | `{plan, concept, knobs, max_long 480\|1920, seconds 0.5–20, fps 1–60}` or `{from_render}` | `{rid, task}` (U:876, 583) |
| POST | `/api/jobs/<id>/tasks/<tid>/cancel` | — | `{ok}` via killpg SIGTERM (U:880, 414) |
| POST | `/api/jobs/<id>/picks` | the picks object | `{path}` (U:896, 695) |

Job folder `benchmarks/runs/<date>/workbench/<pair>_<stamp>_<hex4>/` (U:12–20, 304):
- `job.json`;
- `tasks/<tid>.{json,log}`;
- `analysis/`:
  - `reveal/` with `verdict.json`, from `reveal.py align`;
  - `transitions/report.json`, from `pair --max-long 480 --seconds 1`;
  - `resolve/` with `anchors.json` and the canvases, from `--resolve-only` on `concepts[0]` only (U:444–451);
  - `overlays/`;
- `plans/` (copies);
- `renders/<rid>/`: `render.json` (argv, knobs, md5s, wall_s), `transition.mp4`, `montage.jpg`, `info.json`, `log.txt`, `frames/<i>.png`, `steps.json`;
- `picks/director_picks_<stamp>.json`;
- `owner_frames/`.

Panels:
1. **Inputs**: the pairs table (files, layers, matte count, plans); "new job".
2. **Analysis**: Reveal's verdict and numbers, the transitions class, element and disparity overlays with opacity, element tables with a click-to-matte view, labels in both photos. It changes nothing.
3. **Plan**: plan and concept selects, idea, risk, sha256. The timeline bars are draggable, and a dragged bar becomes a `<name>.window` or `end_window` knob. Mute sets `.skip`; solo mutes the rest. Also: the concept knob table (unmappable knobs read-only with the reason), the globals table, an extra `--set` box, and a preview of the argv. Knobs are seeded from the newest round render (U:270–280).
4. **Render and review**: seconds and fps, draft 480, full 1920, re-render, the progress line and log tail. A scrubber with SVG charts of `motion_px` (pauses and jumps marked), steps and `b_inside`. An A | frame | B strip and "mark this frame".
5. **Grade**: per render, the boxes one_picture, transforms and not_invented, plus acceptable, a note, marked frames and best per stem.

Knob mapping:
- `map_knob` U:213–252 maps a transform knob to `.window`, `.<param>`, `.skip` or `.mix`.
- `PATH_KEYS` U:190–201 maps plan paths to `--set` keys:
  - `pullback.parallax.{gain, gain_A, push, blur, sources, a_elements, push_floor, front_in}`;
  - `pullback.params.end_scale`;
  - `container.params.{reflect, feather_px, sky}`;
  - `container.spec.{front_ids, front_margin}`;
  - `end_effect.{window, kind, params.band, params.vacated_first}`.
- `GLOBALS` U:165–187 lists 21 renderer globals with UI defaults.

Drift between the workbench and the renderer:
- The UI reads `key_end` from `sky.key_end`, but the renderer reads `concept.params.key_end`.
- `end_radius_px` and `end_kind` are reachable only through the extra box; `key_start` is not reachable at all.
- A knob key may hold one dot at most.
- `--layers-dir` and `--mattes-dir` are never passed.

Progress is polled, not streamed:
1. The renderer prints `PROGRESS i n` to stderr every 5 frames.
2. The task log captures it; `parse_progress` regex-reads the last 64 KB (U:361).
3. The page polls the task every 500 ms and the job every 1500 ms.
4. Without progress lines, the fallback compares elapsed time to the last `wall_s` of the same plan and size (U:404).

Gaps, as named by the Fable review (`.claude/claude-docs/research/2026-10-21/ui1_review.md`) and the build report (`ui1_build.md`):

| severity | gap | cite |
|---|---|---|
| medium | Completion is recorded only by the in-process wait thread. After a restart, finished work shows as pending, running or lost; cancel answers `ok: false`; CLI renders are not listed | ui1_review.md:31–51 |
| low | Child processes outlive the server and cannot be cancelled after a restart | :53–64 |
| low | `from_render` is not checked against `ID_RE` (a cross-job path is accepted) | :66–77 |
| low | No `Host` check; JSON is parsed whatever the Content-Type | :79–86 |
| low | Picks `best` holds `concept-rid`, not `concept`; `page` is `workbench_<jid>` | :88–99 |
| low (later) | `__pycache__` gets written; the overlay cache is not atomic; names go unescaped into innerHTML | :103–115 |
| low, CONTESTED | localStorage remembers the open job | :116–118 |
| no severity | `--runs-date` defaults to today, so the rail is empty after midnight; a reused pid stays "running" | :135–138 |
| build report, no severity | The timeline draws requested windows, not `motion.adjusted`; no progress fallback on a job's first draft; faces, discs and lines are not drawn as overlays; a cancelled render's folder stays counted; favicon 404; not tested headed or in Safari, at 1920 from the UI, or on pairs other than mismatch_3 | ui1_build.md:11–13, 129–161 |

Backlog T60 records these as OPEN, restart recovery first (`.claude/skills/reveal/references/tracked-backlog.md:87`). The workbench has no loop flow (T68, line 95) and no aligner flow.

### The aligner page today (`reveal.py`, 127.0.0.1:8378)

Routes:
- GET `/`;
- GET `/api/job/{id}/status`;
- GET `/api/job/{id}/img/{before|after}`;
- GET `/api/job/{id}/download/{before|after_aligned|video}`;
- POST `/api/job` (multipart `before`, `after`, `mode`);
- POST `/api/job/{id}/tune` (`{dx, dy, rot, scale, kh, kv, exposure}`, re-renders in the request);
- POST `/api/job/{id}/export` (`{video, aspect, style, seconds}`, a background thread).

Status JSON (R:1218): `{id, state, note, error, mode, auto_exposure, params{…}, limits{shift, rot, scale}, exports{…}, metrics{…}}`. The states are created, decoding, aligning, refining, rendering, ready, exporting and failed. The job folder `_reveal/jobs/<16hex>/` holds the inputs, previews, stills and `transition.mp4`. The server never writes `metrics.json`. Jobs live in memory and are never evicted (HANDOFF §9.4).

The page shows:
- drop zones and a mode radio;
- four stage dots;
- a compare slider;
- confidence, inliers, rmse "drift", changed %, and a method chip;
- seven tune sliders (−100..100; exposure 0..100);
- export with aspect, style and length 3.5 / 4.6 / 6.5 s;
- on failure, "retry with loose".

It hides data already in the status JSON:
- ecc_rho, peripheral_ssim, sharpness, local_max, edge_overlap, luma_distance;
- residual, raw passed, auto_exposure;
- the limits; the keystone limit is missing from `limits` itself.

It hides data that is computed but never serialized:
- the ladder candidates and the per-candidate arbitration SSIM;
- ECC drift and its rejection reason;
- the residual field and its gate numbers;
- point sets, inlier masks and the H matrices;
- the valid, changed and periphery masks, and the crop rectangle;
- exposure stats and decode info;
- per-stage timings, which nothing records.

### Review pages

| page | per candidate it shows | grade form and picks shape |
|---|---|---|
| `director_page.py` (P:41–172) | the planner's reading and brief per pair; **the mp4 only** (no strip, no gif; `montage.jpg` is not embedded); idea; `notes.json` `look` and `faults`; resolved numbers (canvas, camera, zoom, parallax, steps, wall); a motion sparkline; `b_inside_first`, `residual_edge_max`, guard, halo; plan knobs and set knobs; generated keyframe tiles; filled parts and matte fallbacks; risk | the boxes one_picture, transforms and not_invented, plus acceptable and a note; best per pair; localStorage; an export button that writes `{date, page, best{pair: concept\|none}, clips{tag:{acceptable, note, props{…}}}}` |
| `loop_seq.py page` (L:1562–1608) | per sequence: the gag, the prep summary (reference, canvas, method and inliers per still, cuts), a 360 px keyframe strip. Per variant: the timeline as text, a "what to look at" note, mp4 (autoplay, loop) beside the gif, a table (frames, s, canvas, generated, dexp, step mean, max and position, seam, faces, render s, gif MB, md5), links to sheet, measure and plan | **no grade form and no picks file.** Grades come back as chat text and are recorded by hand |
| `bench_transitions.py` (B:306–373) | per pair: S and F thumbnails, Reveal's reshot and loose lines; per variant: class, method, inliers, displacement, certainty, pan, camera, edge_ratio, warping, render time, goal floors; an 8-frame labelled strip beside the mp4 | three boxes per clip, a "best" radio (incl. "none usable") and a note per pair; export `{date, picks{pair:{best, note, props{tag:{k: true}}}}}` |

### What the operator does by hand that no script covers

**Intake and registration**
- **Read the stills.** Look at thumbnails and a per-pair Lab diff, then write one line per sequence: what moves, what appears, the gag (PB:13–15).
- **Choose cuts.** Declare a cut for a still that will not register (`--cut i,j`) (PB:22–25; benchmarks/2026-10-30-halloween.md:9).
- **Read background anchors.** Pick three by hand for a subject-filled still (backlog T64; PB:25). No flag accepts them.
- **Choose the registration.** All-keypoint, far-field (`--bg-depth`) or lock windows; park the rejected runs (benchmarks/2026-11-04-angel.md:29–37; PB:26–32).
- **Draw lock windows.** Draw them on the still and check them by eye. Once they sat 150 px off the ring, and the skeptic caught it (angel.md:24, 43–46; NEXT_SESSION_PROMPT.md:65–66).
- **Pin the reference.** Pass `--ref 0` when comparing two registrations (PB:134–135).
- **Read the relation.** Take aligned, themed or unrelated from `reveal.py align` into the plan's `relation`; force a class (`--class`, `--override`) (T.md:2688–2689; keyframe_clip.py:288–289).

**Planning**
- **Compare in-between methods.** Look at the morph and RIFE strips per adjacent pair (PB:33–36).
- **Write the plan JSON.** Write one per sequence, by hand or by a planner subagent. The operator writes the planner prompt, records its sha256 and writes the brief. `director_plan.py` from the design (T.md:2687) does not exist (PB:37–39; DT:103).
- **Get readings.** Boxes, skyline rows, anchors and GrabCut `exclude` boxes are read off gridded crops at ±4 px by an Opus 5.5 subagent, about 12 minutes (PB:84, 116–117; research/2026-11-01/readings.md:7).
- **Run director tracks.** A subagent drafts one alternative plan per sequence at 640 px, 5–11 minutes (PB:117–118).
- **Turn grades into knobs.** "20 % faster" becomes frame counts, `--set name.param=…` or `name.skip=true`, from his words only (PB:46, 58–59; T.md:2880, 3211, 3245).

**Keyframes and the box**
- **Place theme anchors.** Put them in canvas px off gridded canvases (theme_anchors.py:9–11; T.md:738–741).
- **Write prompts.** Per-layer `prompt{a, b, where}` and plate prompts (keyframe_prompt.py:19–23; research/keyframe-prompting.md:347).
- **Pick keyframe times.** `--times`, `--key-frames`, `--keys` (keyframe_clip.py:275, 286).
- **Run a box session.** Wake the box, `touch ~/halo-hold`, copy inputs and prompts over, write the queue script with its EXIT trap, run it under nohup, check the box is clean, copy outputs back. Run each keyframe twice and compare sha256 (strix_keyframe.sh:14–22, 41–42; strix-halo-box.md:24–28, 88–89, 109–125).
- **Screen keyframes.** Run `keyframe_screen.py`, then judge by eye (keyframe_screen.py:5).
- **Judge mattes.** Choose `--lattice-ids` and judge mattes on the sheets by eye (matte_source.py:360; research/2026-10-20/mattes_r12.md:45).

**Review and record**
- **Run the skeptic pass.** It crops every candidate at full size, 5–6 minutes, 20–60 tool calls, and a second pass follows any re-render. The retrospective's 11 rules are its checklist (PB:40–42, 114–118; DT:105–114).
- **Write page notes.** Per candidate: what moves, which frames are generated, where to look, the skeptic's verdict. Choose `--order` (PB:43–45; NEXT_SESSION_PROMPT.md:27, 72).
- **Collect grades.** Open the page in his browser and take the grades as text or as a picks JSON. Record them verbatim in the sheet and a DECISIONS line before the next render (PB:18–19, 45; DECISIONS.md:91).
- **Keep the record.** Each round: sheet, DECISIONS, TRANSITIONS §13.N, tooling rows, backlog, memory leaf, handover, research copies with a provenance header, commit and push (PB:121–122, 138–142).
- **Hand-code calibration labels.** Verdict labels for metric calibration come from the picks files (verdict_metrics.py:190).

### Confidence: 80%

Every row comes from a full read of the file by one of five subagents. I checked their anchors on the manifests, `map_knob`/`PATH_KEYS` (U:190–213), the `CFG`/`MODES` lines and both `loop_seq.py` bugs, and they held. Line numbers outside those were not re-checked by me. The wall times come from docs and on-disk run outputs, not from new runs.

### Gaps

1. **Bugs a UI would trigger.** `matte.all` crashes the chain, teleport, slide and rise methods (L:488, 566, 772, 841). `breath.depth_k` without `parallax` does nothing (L:1442). The YuNet manifest is never checked (F:70).
2. **Knobs no surface reaches.**
   - `reveal.py`: 23 global-only `CFG` keys and `residual_mode: on`.
   - `transitions.py`: six spec fields without flags, and `video_crf`.
   - `director_render.py`: `key_start`.
   - `loop_seq.py`: `--set` takes top-level keys only.
3. **Code and docs that disagree.**
   - Loop SCHEMA: the sheets ease, the rife margin and the object lead/linger.
   - `loop_seq.py --help`: the sanity range.
   - `contracts.md`: the aligner video name (`transition.mp4`) and the manual param names.
   - `T.md:217`: the anchor falloff default.
   - `T.md:63`: `pan_fraction` is one value per endpoint, not per frame.
4. **Missing records.**
   - No per-stage timings in any tool except `correspondence_s` in `report.json`.
   - `prep.json` omits four prep flags.
   - The aligner page's ladder candidates and masks are never serialized.
5. **UNVERIFIED.**
   - `nest_probe.py` and `layered_probe.py` internals (the keys inside `layers[].ot`);
   - the venv `matte_source.py` uses and the SD scratch venv path;
   - per-call times of `keyframe_clip`, `keyframe_layer`, `theme_anchors` and `verdict_metrics`;
   - how box outputs come back (scp is inferred);
   - TRANSITIONS.md §7–§8, §10 and most of §12 were grep-searched only;
   - a possible aligner page race where a poll lands before `exporting` is set.
