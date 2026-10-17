<!-- Provenance: written by an Opus 5.5 subagent (Track M, soft mattes, 2026-10-17 late night) of the Claude Code session of 2026-10-17/18 (the round-10 session; DECISIONS 2026-10-18), copied verbatim from benchmarks/runs/2026-10-17/agents/matte_report.md (sha256 ff5a5aa3c0b23642) on the owner's standing order of 2026-10-17; folded into `TRANSITIONS.md §13.17`, the tooling list (readers), DECISIONS 2026-10-18. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

## Findings: matte_source

ViTMatte (`hustvl/vitmatte-small-composition-1k`, trimap-guided) produced a soft alpha for every element of at least 0.2 % of the canvas, plus every priority element, on all six photos: 140 mattes, no empty alpha, no hard fallback. CPU runs are byte-identical. It softens a band of 6–14 px around each SAM 3 mask. It does not fix a mask that is wrong by more than that band: filled lattices stay filled unless they get the opt-in lattice trimap, and the ceiling's stick ends that the mask missed stay missing.

### Key facts
- Model choice: ViTMatte small, composition-1k. Probe on mismatch_2_S id 3 (the man): 0.65–1.08 s on the CPU; band soft share 0.508; the outer ring of the band averages alpha 0.037, so the forced zero past the band makes no visible step. distinctions-646 gave soft share 0.448 and mean |alpha − hard| 0.184, against 0.508 and 0.191 for composition-1k, and looked the same on the zoomed head (scratch `probe/cmp3z.jpg`). I kept composition-1k. RMBG-2.0 / BiRefNet was not tried because ViTMatte did not fail.
- API: I read the installed source, not Context7. `VitMatteImageProcessorPil._preprocess` (`.venv/lib/python3.13/site-packages/transformers/models/vitmatte/image_processing_pil_vitmatte.py:121-150`) rescales the image and trimap by 1/255, normalises the image only (mean and std 0.5, lines 44-51), concatenates the trimap as a fourth channel, and zero-pads bottom and right to a multiple of 32 (lines 60-88). `matte_source.infer` reproduces this in numpy. The output is `model(pixel_values).alphas` (`modeling_vitmatte.py:211,289`). The torchvision processor is not used.
- Crop geometry: `T.cover(T.load_image_rgb(fixture), W, H)` reproduces the element map. The element edges hug the man and the trunk in `mattes/mismatch_2_S/crop_check.jpg` (checked by eye on this one photo only).
- Determinism: on the CPU, the man's matte (md5 `b5e6a1c2…5881`) and the truss lattice matte (`68655e1b…6811`) were each identical across two runs. MPS was identical run to run (`1295f43b…`) but differed from the CPU by 1 level on 2 pixels. The default is the CPU.
- Wider band (2×, r = 12 px on the 602×800 canvas): the man's soft share fell 0.508 → 0.284 and mean |a − hard| 0.191 → 0.107; the tree's fell 0.589 → 0.388 and 0.238 → 0.153. The extra width resolves to 0 or 1, so the model agrees with SAM 3 farther from the edge. I kept the 1 % default.
- Lattices: the bridge truss (mismatch_5_S id 29) and the wheels (mismatch_3_S id 3, labelled "fan" in layers.json) have filled hard masks. With the band trimap, the share of each mask with alpha below 0.5 was 0.091 (truss) and 0.003 (wheels). The opt-in `--lattice-ids` trimap uses a core of pixels at or below the mask's Otsu luma, background seeds on the brighter mask pixels, and unknown for the rest. It raises the share to 0.271 and 0.267. Sky now shows between the girders. Brick shows inside the wheel spokes, but mortar lines and garland sequins stay foreground. Both canonical files use the lattice trimap (`"trimap": "lattice"` in mattes.json).
- The lattice trimap fails on the ceiling of sticks (mismatch_3_F id 1). The sticks are lighter than the gaps between them, so it inverts: the gaps become the core (scratch `probe/ceil_cmp.jpg`). The canonical ceiling uses the band trimap. Its hard mask stops above the stick ends (by eye, about 50 px at x 300–500), and a 14 px band cannot recover them.
- Neighbouring mattes overlap inside their bands. The per-pixel sum of all of a photo's mattes exceeds 1.05 on 2.0–5.3 % of the canvas (maximum 2.97 on mismatch_5_F). It falls below 0.5 on 0–7.2 % (the mask gaps between elements).

### Relevant artifacts
| path | purpose |
|---|---|
| `scripts/research/matte_source.py` | warmup / run / sheet / check-crop |
| `benchmarks/runs/2026-10-17/mattes/MATTE_MANIFEST.json` | the two repos at pinned revisions (composition-1k `6a58ad76…`, distinctions-646 `6a0e75d7…`), sha256 per file, date |
| `benchmarks/runs/2026-10-17/mattes/hf_home/` | weights, 2 × 103 MB safetensors (gitignored under `/benchmarks/runs/`) |
| `benchmarks/runs/2026-10-17/mattes/<photo>/el_<id>.png` | the mattes |
| `benchmarks/runs/2026-10-17/mattes/<photo>/mattes.json` | per id: box, area_px, matte_sum, band_soft_share, band_mean_abs_diff_hard, outer_ring_mean_alpha, r_in, r_out, trimap, wall_s, device, md5 |
| `benchmarks/runs/2026-10-17/mattes/<photo>/sheet.jpg` | photo / red hard edge / matte, per priority element, every tile labelled (mismatch_5_F: all 6 elements; it has no priority ids) |
| `benchmarks/runs/2026-10-17/mattes/mismatch_2_S/crop_check.jpg` | element edges over the cover crop |

### Numbers
CPU, 1 % band (r = 6 px on the 602×800 canvases, 14 px on 1920×1440, 11 px on 1920×1080); the model load adds 1.9–2.8 s per process.

| photo | mattes | sum of element wall (s) | slowest element |
|---|---|---|---|
| mismatch_2_S | 7 | 1.6 | id 3 person 0.65 s |
| mismatch_2_F | 18 | 2.4 | id 2 building 0.52 s |
| mismatch_3_S | 43 | 25.4 | id 2 building 9.1 s (16.1 s in the first run) |
| mismatch_3_F | 43 | 23.4 | id 3 window 3.2 s |
| mismatch_5_S | 23 | 9.8 | id 36 water 1.8 s |
| mismatch_5_F | 6 | 9.9 | id 2 meteor streak 4.8 s |

Priority elements. "soft" is the share of band pixels with 0.05 < alpha < 0.95; |a−h| is the mean |alpha − hard| in the band.

| photo | id label | r_in | soft | \|a−h\| |
|---|---|---|---|---|
| 2_S | 1 tree / 3 person | 6 / 6 | 0.589 / 0.508 | 0.238 / 0.191 |
| 2_F | 10, 11, 15, 17 person | 6 | 0.333, 0.294, 0.369, 0.251 | 0.149, 0.121, 0.128, 0.140 |
| 3_F | 1 ceiling | 14 | 0.132 | 0.130 |
| 3_F | people 14–18, 21, 22, 28, 31, 33, 36 | 6–14 | 0.082–0.243 | 0.054–0.201 |
| 3_F | furniture 23, 27, 29, 30, 34, 35, 37–40 | 6–14 | 0.106–0.357 (37 seat: 0.357) | 0.057–0.477 (37: 0.477) |
| 3_S | 2 building (band) / 3 wheels (lattice) | 14 / 1 | 0.224 / 0.428 | 0.128 / 0.441 |
| 5_S | 16 deck (band) / 29 truss (lattice) | 11 / 1 | 0.283 / 0.535 | 0.140 / 0.377 |
| 5_S | 2, 3, 9 lamp posts | 2, 4, 3 | 0.259, 0.083, 0.193 | 0.174, 0.237, 0.115 |

Lamp post id 2 (0.05 % of the canvas) comes out grey along its length (alpha about 0.5–0.7, by eye on the sheet): ViTMatte reads a 2–3 px pole as partly transparent. Ids 3 and 9 come out near 1.

### Reading contract for director_render.py
1. Path: `benchmarks/runs/2026-10-17/mattes/<photo>/el_<id>.png`, where `<photo>` is the layer-source name (e.g. `mismatch_5_S`) and `<id>` is the element id from `layers.json`.
2. Read with `cv2.imread(p, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255`. The file is a uint8 alpha of shape (H, W), with W, H from `layers.json["canvas"]`, on the same centred cover crop as `layers.npz["element"]`. It covers every pixel and needs no offset.
3. Alpha is 1 inside the eroded core and 0 past the dilated band. It never extends more than r_out px (`mattes.json` `r_out`) outside the hard mask.
4. If an id has no file (an element under 0.2 % that was not a priority id), fall back to `(element == id).astype(np.float32)`. Treat `"fallback": "hard"` in mattes.json the same way (no element hit it).
5. Neighbours overlap in their bands (sums up to 2.97). For a union of ids, take `np.maximum` over their mattes. Composite layers in depth order with "over" (`out = a*fg + (1-a)*out`) and never add alphas.

### Constraints discovered
- `run` refuses without the manifest or on a sha256 mismatch. The refusal was tested before warmup existed: "no manifest at …; run `matte_source.py warmup` first. The run step never downloads." `run` sets HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1 before importing transformers.
- The band trimap cannot fix an error in the SAM 3 mask wider than r_out. The ceiling's stick ends and the wheel's filled spokes are mask errors, and a matting model does not correct them.
- Some elements in mismatch_3_* carry no `box` in layers.json (21 ids on 3_S, 26 on 3_F). The script uses the mask extent and records `"box_from": "mask"`.
- No new packages and no scratch venv were needed. Nothing was written to `models/`.

### Confidence: 75 %
The files, numbers and determinism are measured. That the mattes remove the owner's "rough cutout" reading is UNVERIFIED until a rendered clip uses them.

### Gaps
- Context7 was not used. The API is cited from the installed source instead.
- RMBG-2.0 / BiRefNet were not run, so there is no comparison number against ViTMatte.
- The ceiling of sticks has no working rule. An inverted-polarity lattice trimap (bright core, dark seeds) is the next probe, UNVERIFIED.
- The wheels' lattice matte keeps mortar lines and sequins as foreground (by eye; not measured).
- The crop geometry was checked by eye on mismatch_2_S only. The other five photos match on their sheets' red edges, also by eye.
- mismatch_3_S id 2's wall time varied 16.1 s → 9.1 s between runs (machine load, not measured).
- Mattes overlap in their bands. Whether "over" in depth order looks clean where two moving layers touch is UNVERIFIED.
