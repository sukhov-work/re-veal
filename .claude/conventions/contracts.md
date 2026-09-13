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

## Name/identity fences (rule: two-way)
None recorded yet. The first rename or rebrand (e.g. `_reveal/` workdir, the `reveal_<aspect>.mp4`
export name, `MODES` keys) must add two checks: one that fails if the internal name leaks to the
user, one that fails if a sweep renames a persisted identifier.
