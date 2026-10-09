# 2026-10-09 — the owner's box photos: a one-off real-life run (design of record `TRANSITIONS.md §12.24`)

Inputs: `/Users/yevhens/Pictures/fabra_boxes/1.heic` … `7.heic`, iPhone HEIC, 3778–4599 × 4722–5749
(all 4:5), shot 2026-09-20 to 2026-10-04: two utility boxes beside a roller door, graffiti → primer
grey → pink → painted trees; the roller door is open in photos 3 and 4. Copies under `fixtures/`
as `fabra_17_S/F.heic` and `fabra_12 … fabra_67` (gitignored; `fixtures/MANIFEST.md` rows).
Outputs: `benchmarks/runs/2026-10-09/fabra/` (gitignored): `1-7/index.html` (the triage page),
`page.py`, `run_pairs.sh`, `merge.py`, `seq/tr14_luma-melt-soft/<pair>/`, `final/`.

## Stage 1 — the triage page on 1→7 (15 clips, 3 s, 30 fps)

| tag | what it is | numbers |
|---|---|---|
| reveal_wipe, reveal_fade | `reveal.py align --video --aspect original`, strict `reshot` | sift 1452 · 0.59 px · ecc_rho 0.973 · 13.3 % changed · confidence 98 · 7.9 s · 1524×1920 |
| morph_3s, flow-dissolve_3s, luma_3s, dissolve_3s, snap-morph_3s, iris_3s, wipe_3s | `transitions.py pair --max-long 1920` | class A homography+dis · 875 inliers · 0.66 px · certainty 0.614 · median disp 31.4 px · 1536×1920 · 11–18 s each; morph warping 0.0042 · feat 0.431 · dissolve_fit 0.058 · motion −0.147 |
| tr14_dis, tr14_hold-dis, tr14_luma, tr14_edge-grow, tr14_melt-soft | `scripts/research/tr14_variants.py --render` after `compare_fields.py --prepare`; the RoMa field stubbed by the DIS field (`ROMA_STUB_README.txt`) | mask 13.3 % · in-mask disp 25–28 px · wobble 7.0–7.5 px (photos' own edge 6.28 / 5.42) · edge_ratio 0.072–0.136 · `dis_3s` = `morph_3s` byte for byte (md5 8b4f8e71) |
| layered_auto_r7 | `layered_probe.py --auto4 fabra_17` after `layer_merge.py --routes gdino_sam2,sam3` (scratch venv, offline; an Opus 5.5 subagent, re-checked) | layer source 142 s for both photos, 0 socket attempts · route "elements" · 9 elements per photo · matched building, signboard, road (cost 0.007–0.016) · the boxes in the rest layer · md5 2bed31ce… |

By the agent's eye on the mid frames (not a grade): every morph-family clip shows both paintings on
the boxes at once around frame 45 (failure F1); the Reveal wipe is the only clip without it.

## Owner pick (2026-10-09, by message, verbatim)
"I really liked effects in tr14_luma_3s and tr14_melt-soft_3s verysmooth and elements on boxes flow
and transtion more naturally. For final video, try to mix those two approaches, do a 2s transitions
instead of three and do all pairs ( and then merge to final mp4 clip, suitable for instagram"

## Stage 2 — `luma-melt-soft` at 2 s on the six pairs (`run_pairs.sh tr14:luma-melt-soft 2`)

The variant (new in `tr14_variants.py`, 2026-10-09): the hold field, luma's reveal order inside the
changed-region mask, melt-soft's swirl on the composited frame. On 1→7 at 2 s: md5 6d33188f
(luma 5caa6a5f, melt-soft 382c0b95), edge_ratio 0.1763 (0.1199, 0.1802), wobble 7.49 px.

| pair | inliers | rmse px | certainty | median disp px | mask | in-mask disp px | wobble px | edge_ratio | warping | render s |
|---|---|---|---|---|---|---|---|---|---|---|
| 1→2 | 728 | 1.04 | 0.703 | 17.3 | 20.5 % | 11.84 | 7.70 | 0.243 | 0.0045 | 9.8 |
| 2→3 | 658 | 0.73 | 0.357 | 15.9 | 15.1 % | 6.01 | 2.21 | 0.261 | 0.0053 | 9.2 |
| 3→4 | 1186 | 0.86 | 0.548 | 9.8 | 17.4 % | 4.58 | 0.59 | 0.182 | 0.0043 | 9.4 |
| 4→5 | 1970 | 1.14 | 0.500 | 28.0 | 18.2 % | 21.30 | 8.07 | 0.102 | 0.0054 | 9.6 |
| 5→6 | 1566 | 1.41 | 0.656 | 25.0 | 15.8 % | 19.22 | 1.90 | 0.113 | 0.0048 | 9.8 |
| 6→7 | 1194 | 1.47 | 0.802 | 19.8 | 25.8 % | 14.20 | 3.95 | 0.170 | 0.0038 | 9.2 |

Endpoints 0.0 / 0.0 on every pair; 60 frames each; 14–15 s wall per pair including the prepare step.

## Stage 3 — the merged clip (`merge.py`)
1.5 s on photo 1, 1.0 s on each photo between clips, 2.0 s on photo 7: 609 frames, 20.3 s. The
same photo decoded from two clips differs by 2.5–3.3 levels mean (0.6–0.7 after a 3 px blur, phase
shift under 0.1 px): codec noise, not a crop mismatch, so each hold is a linear blend of the two
decoded endpoint frames; the frame step is 0.00 at every join and 4.77 levels at the largest
(inside the 4→5 transition). `final/fabra_boxes_1536x1920.mp4` (md5 cb43ca07…, 30.7 MB) and
`final/fabra_boxes_instagram_1080x1350.mp4` (md5 52836583…, 15.3 MB; the 4:5 feed size), libx264
crf 18, yuv420p, 30 fps, no audio. Opened for the owner at 14:58 EEST; ungraded.

## Found on the way
- The layer source's detection prompts have no word for a utility box or cabinet; the boxes stayed
  inside the building element in both photos (backlog T32).
- `tr14_variants.py --render` loads `roma_*.npy` unconditionally; the stub is documented beside the field files.
