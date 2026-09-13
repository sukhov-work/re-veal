# Architecture conventions — Reveal

Design of record is `HANDOFF.md` (§2 invariants, §3 pipeline, §4 HTTP, §5 frontend, §6 decisions).
This page adds only what agents need to navigate and extend the single file without breaking it.

## The single-file rule
`reveal.py` is one module by design (mirrors the media-organizer's `organize.py`/`viewer.py`).
New capability = a new function inside the matching section below, or a new section with the same
`# ----` divider style. No packages, no `src/`, no second module — a helper that needs its own file
is a design decision for `DECISIONS.md`, not a refactor.

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
