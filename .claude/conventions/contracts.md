# Contracts — the Hyrum inventory (seed 2026-09-13; the first audit authors it fully and later audits diff it against the code)

Every observable surface something outside `reveal.py` can depend on. Change one only with a
DECISIONS line and a harness check that pins the new shape.

| Contract | Where | Consumers |
|---|---|---|
| HTTP routes: `GET /`, `GET /api/job/{id}/status`, `GET /api/job/{id}/img/{before\|after}`, `GET /api/job/{id}/download/{before\|after_aligned\|video}`, `POST /api/job` (multipart), `POST /api/job/{id}/tune` (JSON), `POST /api/job/{id}/export` (JSON) | `Handler.do_GET/do_POST`, `reveal.py:1626–1735` | the embedded page; `verify.md` curl recipe; harness M |
| Multipart field names `before`, `after`, `mode` | `_post_job`, `reveal.py:1679` | page upload form; harness 38–51, 60 |
| Status JSON keys: `id state note error metrics params mode limits{shift,rot,scale} auto_exposure exports` | `Job.status`, `reveal.py:1218` | page polling; `metrics.json` written by `align` (same dict) |
| `metrics` keys: `method inliers rmse_px ecc_rho peripheral_ssim sharpness local_max edge_overlap luma_distance residual changed_pct passed confidence` | `run_alignment`, `reveal.py:1311–1338` | page metrics panel; harness 26–29, 70–76; the future benchmark sheet |
| Job states: `created decoding aligning refining rendering ready exporting failed` | `Job.__init__`, `reveal.py:1191` | page state machine |
| `MODES` keys `reshot`, `loose`; unknown → `reshot` | `reveal.py:157`, `profile()` | CLI `--mode` choices; multipart `mode`; harness 52–62 |
| `ASPECTS` keys `4:5 9:16 16:9 1:1 original`; `--style` values `wipe fade`; `--seconds` float | `reveal.py:191`, `:2550–2552`, `export_video` | CLI; page export form; harness 34–37 |
| Manual params: `shift_x shift_y rot scale keystone_x keystone_y exposure` as resolution-independent fractions, clamped per mode | `default_params`, `_clamp_params`, `manual_matrix` | page sliders; tune endpoint; harness 30–32, 53, 61 |
| Job dir layout `_reveal/jobs/<16-hex>/` with `before.jpg`, `after_aligned.jpg`, `reveal_<aspect>.mp4`; download allow-list | `Job.__init__`, `export_*`, `Handler` | user's Downloads; harness 44–47 |
| `models/MANIFEST.json`: `tool_version matcher verified self_test_matches files[{name,size,sha256}]` | `cmd_warmup`, `learned_manifest`, `learned_weights_cached` | `check`; the runtime download gate; harness 79–82 |
| `models/hub/checkpoints/` = `TORCH_HOME` | `_pin_torch_home` | kornia/torch.hub; copying the project folder must keep the matcher offline |
| CLI: `serve [--port --no-browser --workdir]`, `align BEFORE AFTER --out DIR [--mode --video --aspect --style --seconds]`, `check`, `warmup` | `main`, `reveal.py:2537` | `run.sh`, `setup.sh`, README, HANDOFF §10 |
| `VERSION` file == `reveal.py:91` `VERSION` string | both | setup/README/HANDOFF header; MANIFEST `tool_version` |
| Accepted extensions `RAW_EXTS HEIF_EXTS PIL_EXTS` | `reveal.py:186–189` | page file filter; harness 6–11 |
| Bind address 127.0.0.1, default port 8378 (8377 belongs to the organizer's viewer) | `serve`, `DEFAULT_PORT` | README; harness 51 |

## `transitions.py` (added 2026-09-13; harness = `transitions_harness.py`)
| Contract | Where | Consumers |
|---|---|---|
| CLI: `pair BEFORE AFTER --out DIR [--seconds --fps --preset --color --warp --max-long --canvas finish\|common --anchors --class --camera flat\|ramp\|model --zoom --anchor-falloff]`, `check`, `warmup` (the only command that downloads; 2026-09-23); exit 0 ok / 2 `FAILED: <message>` on stderr | `main`, `cmd_pair`, `cmd_check`, `cmd_warmup` | `TRANSITIONS.md §9`; harness 27–36, 39–40, 47–51; `scripts/bench_transitions.py` |
| `PRESETS` keys `morph dissolve flow-dissolve snap-morph iris wipe luma`; `STYLES` `morph dissolve warp-dissolve portal luma`; `PORTALS` `iris wipe`; `CURVES` `linear ease ease-in ease-out snap hold-then-go`; `CAMERAS` `flat ramp model` (2026-09-23); `--zoom` clamps to `zoom_range` [0.02, 0.5] | `transitions.py` Configuration | `--preset` / `--camera` choices; harness 5, 7, 21–22, 47 |
| Length clamp [0.1, 10] s; `n_frames = round(seconds × fps)` ≥ 2; frame 0 = A and frame n−1 = B byte-exact | `TransitionSpec`, `iter_frames` | harness 4, 6, 21, 29, 35 |
| Output files in `--out`: `transition.mp4` (H.264 yuv420p, canvas size, `--fps`), `strip.jpg` (8 tiles), `report.json` | `render_pair` | harness 27–33; the future benchmark sheet |
| `report.json` keys: `tool_version spec{…} class method sparse_inliers sparse_rmse mean_certainty median_disp_px correspondence_s canvas canvas_policy n_frames render_s quality{warping_error flicker{mean max spikiness edge_ratio} goal{feat_floor laplace_floor contrast_floor dissolve_fit motion_share} n_frames endpoint{first_vs_A last_vs_B} proxy_long} total_s outputs`; class B without anchors adds `pan_fraction [fA, fB]` (2026-09-14) and `camera`, `zoom` (2026-09-23; under `ramp`/`model` also `disparity_mean [A, B]`, and `mean_certainty` is then the mean depth importance); `spec` gains `camera`, `zoom` (2026-09-23) and `anchor_falloff` (2026-09-26; default 0.45 since the same day; with anchors the method is `mls-anchors+falloff` / `…+anchors+falloff` when it is above 0, `mls-anchors` at 0) | `render_pair`, `StreamStats.quality`, `goal_numbers` (2026-09-26) | harness 27, 31, 35, 43–47, 52–53 |
| `method` values: class A `homography+dis`, `dis-only`, either `+anchors`; class B `saliency-panzoom` (2026-09-14; was `saliency-similarity`), `saliency-panzoom+ramp`, `saliency-panzoom+model` (2026-09-23), `mls-anchors` | `dense_displacement` | `report.json`, the sheet, harness 12, 14, 16, 17, 43–45, 50 |
| Displacement convention: `dAB[y,x]=(dx,dy)` with `B[y+dy,x+dx] ≈ A[y,x]`, canvas pixels; anchors `"ax,ay,bx,by;…"` in canvas pixels, ≥ 3 pairs | `dense_displacement`, `parse_anchors` | harness 13, 15–16 |
| Isolation: no `reveal` import in `transitions.py`, no `transitions` import in `reveal.py`, no network-capable or weight-loading import at module level in `transitions.py`; torch / transformers / huggingface_hub only inside `depth_available _depth_model model_disparity cmd_warmup` (2026-09-23) | both files | harness 1–3 |
| `models/DEPTH_MANIFEST.json`: `tool_version model verified self_test{top20_mean,bottom20_mean} prep{size,multiple,mean,std} files[{name,size,sha256}] links[{name,target}]`; `models/depth/` = the tool's `HF_HOME` (both gitignored; `./setup.sh --learned` rebuilds them) | `cmd_warmup`, `depth_manifest`, `depth_weights_cached` | `check`; the runtime download gate; harness 48–51 |
| Accepted extensions = Reveal's `RAW_EXTS HEIF_EXTS PIL_EXTS` (duplicated on purpose) | `transitions.py` Decode | `load_image_rgb` |

## Name/identity fences (rule: two-way)
- **`transitions`** is the official name of the second tool (owner ruling 2026-09-13: "leave it as
  `transitions` and record as official name"). Persisted identifiers: `transitions.py`,
  `transitions_harness.py`, outputs `transition.mp4 strip.jpg report.json`, logger and argparse
  prog names. Fence checks: transitions harness 37 (a sweep rename fails) and 38 (the research
  codename "Impossible" never appears in the shipped module).
- Reveal: none recorded yet. The first rename or rebrand (e.g. `_reveal/` workdir, the
  `reveal_<aspect>.mp4` export name, `MODES` keys) must add the same two checks.
