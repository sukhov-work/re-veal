# Architecture conventions — Reveal

Design of record is `HANDOFF.md` (§2 invariants, §3 pipeline, §4 HTTP, §5 frontend, §6 decisions).
This page adds only what agents need to navigate and extend the single file without breaking it.

## The single-file rule
`reveal.py` is one module by design (mirrors the media-organizer's `organize.py`/`viewer.py`).
New capability = a new function inside the matching section below, or a new section with the same
`# ----` divider style. No packages, no `src/` — a helper that needs its own file is a design
decision for `DECISIONS.md`, not a refactor. One such decision exists (2026-09-13): `transitions.py`
is a SECOND single-file tool with the same section style and its own harness; the two never import
each other (transitions harness 1–2). Its design of record is `TRANSITIONS.md`.

## Section map (line anchors as of 2026-09-13, v1.5.0 — re-grep `^# ---` after edits)
| Section | Lines | Owns |
|---|---|---|
| Configuration | 98–199 | `CFG`, `MODES`, `profile()`, extension sets, `ASPECTS`, `AlignError` |
| Decode | 201–279 | `load_image_rgb` (Pillow/HEIF/rawpy routing, EXIF, ICC→sRGB), `scaled_copy`, `gray_of` |
| Matching + estimation | 280–727 | SIFT/ORB/learned matchers, MAGSAC++, similarity fallback, sanity gate, ECC refine, phase-corr, `_arbitrate`, `estimate_alignment` |
| Coordinate transport | 728–772 | `scale_h`, `manual_matrix`, `default_params` |
| Valid mask + crop | 773–834 | `warp_valid_mask`, `largest_interior_rect`, `crop_rect` |
| Change / periphery / metrics | 835–1012 | `ssim_map`, `changed_region_mask`, `peripheral_mask`, `edge_overlap`, `bhattacharyya`, `peak_sharpness`, `confidence_score` |
| Exposure | 1013–1051 | `exposure_params`, `apply_exposure` |
| Residual field (phase 3) | 1052–1171 | `residual_flow` (DIS samples → cubic IRLS fit), `apply_residual` |
| Job + pipeline | 1172–1400 | `Job`, `run_alignment`, `_render_pair`, `render_previews` |
| Export | 1401–1516 | `export_images`, `_cover`, `_ease`, `export_video` (frames piped to ffmpeg), `run_export` |
| HTTP | 1517–1752 | `parse_multipart`, `_clamp_params`, `Handler`, `serve` |
| Frontend | 1753–2404 | one embedded HTML/CSS/JS string |
| CLI | 2405–2570 | `cmd_check`, `cmd_warmup`, `cmd_align`, `main` |

## `transitions.py` section map (line anchors as of 2026-09-13, v0.1.0 — re-grep `^# ---` after edits)
| Section | Lines | Owns |
|---|---|---|
| Configuration | 98–218 | `TCFG`, `CURVES`, `STYLES`, `PORTALS`, `TransitionSpec` (`n_frames`, `clamp`, `progress`), `PRESETS`, `spec_from`, `TransitionError` |
| Decode and canvas | 219–324 | `load_image_rgb` (re-implemented), `gray_of`, `even`, `to_u8` (rounding cast), `cover`, `common_canvas`, `_grid` |
| Correspondence | 325–548 | `sparse_homography`, `_sane`, `_dis`, `_homography_guided`, `consistency_weight`, `salient_box`, `similarity_from_boxes`, `mls_affine`, `_affine_to_disp`, `_invert_disp`, `dense_displacement` (class A/B routing, INFO line on B) |
| Warp | 549–676 | `backward_warp`, `forward_splat` (1/4-res coordinate splat → one remap), `fill_holes`, `morph_frame`, `portal_mask` |
| Color path | 677–730 | `lab_stats`, `lerp_stats`, `apply_stats` (float correction, rounded once), `color_pair_at`, `luma_mask` |
| Quality basket | 731–827 | `warping_error`, `flicker` (`edge_ratio` = hidden-cut detector), `endpoint_fidelity`, `assess`, `proxy_of`, `StreamStats` |
| Render | 828–894 | `prepare` (canvas + correspondence once), `iter_frames` (generator, endpoints pinned), `render_frames` (in-memory convenience) |
| Encode | 895–978 | `FrameEncoder` (imageio-ffmpeg rawvideo pipe → libx264), `render_pair` (the whole job: mp4 + strip + report) |
| CLI | 979–1076 | `cmd_check`, `parse_anchors`, `cmd_pair`, `main` (exit 0 / 2) |

Seams: a **new preset** = a `PRESETS` entry + a harness assertion in section F (byte-exact
endpoints, `edge_ratio`, monotone approach) — nothing else changes; a **new style** = a branch in
`iter_frames` + `STYLES` + a section-H check that decodes the mp4 and asserts the style's own
observable (the wipe's monotone seam is the model, check 32); a **new correspondence method** =
a branch in `dense_displacement` that fills `dAB dBA wA wB method` and a section-D check against a
known field; any **model or weights** first need Reveal's warmup + manifest + refuse-to-download
shape (decisions 24–27) — no download path exists in `transitions.py` and check 3 keeps it so.

## Extension seams (the experimental lane, `AGENTS.md §Reversibility`)
- **New matching mode** → a new key in `MODES` (overrides only; `reshot` stays `{}`), a harness
  section with a calibrated scenario pair (see N, checks 56–58), the CLI `--mode` picks it up
  through `choices=list(MODES)`, the page reads limits from `/status` (nothing hardcoded twice).
- **New video transition** → a new `style` branch in `export_video`; `wipe` and `fade` untouched;
  the CLI `--style` choices list (`reveal.py:2551`) and the page's export form both need the value;
  a harness check decodes the mp4 with `cv2.VideoCapture` and asserts frame count, size, and the
  style's own observable (seam position monotone, first/last frame equals the stills, no all-black
  frame).
- **New estimator or refinement** → competes as a candidate inside `estimate_alignment`'s ladder
  and is arbitrated on peripheral SSIM (decision 23); never ranked on its own inlier count.

## Data flow contract (do not reorder)
decode → working copies (1600 px) → estimate (B→A homography) → ECC refine (masked to the static
scene) → residual field (auto-gated, `reshot` only) → changed mask / periphery / metrics → exposure
(warp-then-match) → crop → preview / export. Manual params compose AFTER the automatic H, in the A
frame, as resolution-independent fractions.
