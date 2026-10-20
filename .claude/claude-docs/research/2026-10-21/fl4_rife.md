<!-- Provenance: written by an Opus 5.5 subagent (the FL4 probe: RIFE v4.26 in-betweens inside the café man's matte) of the Claude Code session of 2026-10-21 (the round-13 session; DECISIONS 2026-10-21), copied verbatim from benchmarks/runs/2026-10-21/agents/fl4_rife.md (sha256 b2b4982770951518) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

## Findings: FL4

RIFE v4.26 in-betweens between k1 and k3 fail rule 7. The double-exposure share inside the chain matte peaks at 13.6 % at t = 0.5 (bar 1 %; the plain blend reaches 75.9 %). Two bars pass: the man has one face in every frame, and the flow consistency between neighbouring frames (0.79–0.98) is far above k1 → k3 directly (0.153). CPU cost is 0.34 s per frame at 602×800 on an Apple M3 Pro. The double exposure has two sources: (1) the phone hand, which fades in as a see-through ghost over the woman in green at t 0.375–0.625; (2) the skin of the turning face, whose tone is mixed between the two keyframes and smeared on the cheek and nose at t = 0.5. Tier: real-pair, measured on mismatch_2's generated keyframes; the page has not been graded by the owner.

### Key facts

- The weights are the author's own Hugging Face copy, `hzwer/RIFE` at revision `01fdc7e97404120c243c3ea7b427046e5dc7643e`, file `RIFEv4.26_0921.zip` (22 869 906 bytes). From it come `flownet.pkl` (sha256 `45c7f741…`, 24 636 301 bytes) and `IFNet_HDv3.py`. `warplayer.py` and `LICENSE` (MIT) come from GitHub `hzwer/Practical-RIFE` at commit `bbfd2ea90910789a860ea3e2b32a240cd577b75e`. The full sha256 list is in `benchmarks/runs/2026-10-21/rife/RIFE_MANIFEST.json` (the manifest's own sha256 is `8f0caf32…`). No Google Drive or gdown was needed, and nothing else was fetched.
- `scripts/research/rife_probe.py` has three subcommands: `warmup` (the only network step), `matte`, and `run`. `run` sets `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1` and refuses to start without the manifest or on a sha256 mismatch. It imports the downloaded code by path under private module names, and loads the weights with `torch.load(..., weights_only=True)`. Missing keys: 0. Unexpected keys: only `teacher.*`, which inference does not use. Parameters: 5 664 776.
- The chain matte (`rife/matte/chain_matte.png`, 39.3 % of the canvas) copies `director_render.py`'s construction after a lead. It joins A's man (el_3), moved by the YuNet face similarity A → k1 (scale 0.894, rotation dropped), with B's man (el_10), then dilates by 19 px (3 % of 602) and feathers. `rife/matte/matte.json` holds the numbers.
- The keyframes are 608×800. The script resizes them to the 602×800 canvas with INTER_AREA, as the renderer does, so the in-betweens are already canvas-size.
- `faces in matte` is 2 on k1 itself, because the woman in green lies inside the matte. The screen therefore counts the man's faces: YuNet faces whose centre lies in the union of k1's and k3's man face boxes grown by 25 % (box x 0–230, y 230–640). That count is 1 on k1, on k3, and on all 7 in-betweens.

### The numbers

Arm (i), k1 → k3, n = 7, from `benchmarks/runs/2026-10-21/rife/arm1_k1_k3_n7/report.json`. "dexp" is rule 7's share against the mean of k1 and k3. "face" and "rest" split it into the man's face region and the remainder of the matte. "Blend" is the plain linear blend at the same t (the positive control). Laplacian is keyframe_screen's definition, taken inside the matte.

| k | t | s | man's faces | faces in matte | dexp | face | rest | blend dexp | blend dexp vs (1−t)k1+t·k3 | Laplacian in matte (blend) |
|---|---|---|---|---|---|---|---|---|---|---|
| k1 | 0 | – | 1 | 2 | – | – | – | – | – | 853.8 |
| 1 | 0.125 | 0.4 | 1 | 2 | 1.3 % | 1.4 % | 1.3 % | 0.0 % | 14.4 % | 681.9 (671.7) |
| 2 | 0.250 | 0.4 | 1 | 2 | 6.4 % | 7.1 % | 5.9 % | 0.0 % | 50.9 % | 541.6 (526.7) |
| 3 | 0.375 | 0.3 | 1 | 2 | 12.5 % | 16.6 % | 9.5 % | 52.4 % | 66.8 % | 456.0 (417.1) |
| 4 | 0.500 | 0.3 | 1 | 2 | 13.6 % | 16.9 % | 11.2 % | 75.9 % | 75.9 % | 374.3 (340.1) |
| 5 | 0.625 | 0.3 | 1 | 2 | 12.4 % | 14.9 % | 10.6 % | 52.4 % | 66.8 % | 295.2 (293.5) |
| 6 | 0.750 | 0.3 | 1 | 1 | 8.6 % | 10.6 % | 7.1 % | 0.0 % | 50.9 % | 253.2 (275.5) |
| 7 | 0.875 | 0.3 | 1 | 1 | 3.2 % | 3.7 % | 2.8 % | 0.0 % | 14.4 % | 257.5 (285.7) |
| k3 | 1 | – | 1 | 1 | – | – | – | – | – | 322.9 |

Flow consistency of the strip k1, in_1 … in_7, k3. cw is the renderer's consistency_mean on the face-guided DIS flow; fb1 is the share of matte pixels with forward-backward error ≤ 1 px.

| segment | k1→1 | 1→2 | 2→3 | 3→4 | 4→5 | 5→6 | 6→7 | 7→k3 | k1→k3 directly |
|---|---|---|---|---|---|---|---|---|---|
| cw | 0.984 | 0.936 | 0.916 | 0.787 | 0.844 | 0.826 | 0.878 | 0.933 | 0.153 |
| fb1 | 0.968 | 0.858 | 0.788 | 0.667 | 0.772 | 0.749 | 0.836 | 0.936 | 0.088 |

Arm (ii), k1 → k3, n = 3 (`arm2_k1_k3_n3/report.json`). Its frames are the same pictures as arm (i)'s k = 2, 4, 6, because RIFE is deterministic at the same t. dexp max is 13.6 %, and the man has one face in every frame. cw by segment is 0.900, 0.571, 0.582, 0.767; fb1 is 0.818, 0.478, 0.478, 0.693. Seconds per frame: 0.36.

Whole-frame Laplacian of the in-betweens is 759–806, against 875.1 for k1 and 855.5 for k3. The interpolation softens the frame a little, and its sharpness inside the matte stays at or just above the plain blend's in the middle of the turn.

### Verdict

- One face per frame (the man): pass in both arms.
- Double exposure ≤ 1 %: fail in both arms, at 1.3–13.6 % against a positive control of up to 75.9 %.
- Consistency above k1 → k3's: pass. The arm (i) minimum is 0.787 against 0.153; the arm (ii) minimum is 0.571.
- CPU seconds per frame at 602×800 (padded to 640×832): 0.34 mean (0.29–0.39), 6 torch threads, with other jobs on the machine.

Neither arm passes all three bars. Arm (i) is the better one: it doubles the consistency of the weakest segment (0.787 against 0.571) at the same double exposure. Arm (iii), the moved A man → k1, was not run because arm (i) failed. Its input `rife/matte/moved_A.png` is written.

Two readings of the failure need the owner's eye on `benchmarks/runs/2026-10-21/rife/index.html`:
1. The phone hand is a real ghost. RIFE cannot invent motion for a hand that is absent in k1, so the hand crossfades. This is rule 7's failure, the same as today's dissolve but over fewer frames.
2. In the face region the measure counts skin whose colour lies between the two keyframes' tones, even where the geometry is warped coherently. At t = 0.5 the in-between shows one face, where the plain blend shows two pairs of eyes. The cheek and nose are smeared. Rule 7's share does not separate a tone mix from a ghost, so 16.9 % on the face overstates the doubling visible in the frame [INFERRED from the overlay of flagged pixels on the t = 0.5 frame, viewed in this session; not a measured split].

### What the main session needs to wire it

The bar failed, so this is offered only for an A/B against round 12 with the owner's eye, not as a default. For arm (i), the `man_becomes_nearest_man` transform in `scripts/research/plans/mismatch_2_r12.json` would take `params.keyframes` in this order:

```json
["benchmarks/runs/2026-10-17/keyframes_r10/out/r10_m2_k1.png",
 "benchmarks/runs/2026-10-21/rife/arm1_k1_k3_n7/in_1.png",
 "benchmarks/runs/2026-10-21/rife/arm1_k1_k3_n7/in_2.png",
 "benchmarks/runs/2026-10-21/rife/arm1_k1_k3_n7/in_3.png",
 "benchmarks/runs/2026-10-21/rife/arm1_k1_k3_n7/in_4.png",
 "benchmarks/runs/2026-10-21/rife/arm1_k1_k3_n7/in_5.png",
 "benchmarks/runs/2026-10-21/rife/arm1_k1_k3_n7/in_6.png",
 "benchmarks/runs/2026-10-21/rife/arm1_k1_k3_n7/in_7.png",
 "benchmarks/runs/2026-10-17/keyframes_r10/out/r10_m2_k3.png"]
```

Keep `"frame": "canvas"`. The in-betweens are 602×800, so the renderer's resize is a no-op. Keep `times: "arc"`: the measured median displacements between neighbours are 0.9–5.4 px, so every RIFE segment sits at the arc floor (0.2 of the 283 px lead). The k1 → k3 part of the chain would then take 8 floor shares of 56.6 px each, about 453 px of arc against round 12's 72.2 px and the lead's 283 px, so the turn would take most of the chain window. `arc_floor` 0.05 (8 × 14.2 = 113 px), or explicit `times`, would keep the turn near its round-12 length. That choice is UNVERIFIED and needs a render. With `face_guide` on, the renderer's DIS flow and a linear mix still run on top of each RIFE segment, so the phone-hand ghost stays.

### Constraints discovered

- The author's own Hugging Face repo `hzwer/RIFE` hosts the v4.26 zip, so no Google Drive fetch is needed. The zip's `RIFE_HDv3.py` sets `self.version = 4.25` although the zip is named 4.26.
- Practical-RIFE v4.26 has no context or refinement network (`fastmode` only). The in-between is two warped inputs blended by a learned mask. It cannot generate content present in only one input: here the phone hand comes out as a crossfade, as `flow_research.md` Q2 predicted.
- The task's double-exposure control (mean of k1 and k3) gives 0.0 % for the plain blend at t = 0.125, 0.25, 0.75 and 0.875, because a blend near one endpoint lies within 20 levels of it. At those t the positive control is dead. The t-aware variant ((1 − t)·k1 + t·k3 as the reference) gives 14.4–75.9 % at every t; `report.json` carries it as `dexp_t` and `dexp_t_blend`.
- The chain matte contains the woman in green in k1, so a whole-matte face count reads 2. The face screen has to restrict itself to the man's face region.

### Confidence: 75%

The three measures and the timings come from `report.json` files written by this run. The verdict on rule 7's bar does not depend on any reading. Whether the face's 16.9 % is mostly a tone mix rather than a ghost is a visual reading, not a measurement. The owner's grade on the page decides whether any of this is usable.

### Gaps

- Arm (iii), the moved A man → k1, was not run, by the task's own condition (arm (i) failed).
- EMA-VFI was not tried: RIFE was fetched on the first attempt.
- The rule-7 measure cannot separate a tone mix from a ghost. A split by local structure (for example, whether gradients in the in-between line up with gradients in one endpoint) was not built.
- No render through `director_render.py`: the probe did not touch the renderer, so the effect on the clip, including the arc times above, is UNVERIFIED.
- The timings ran with other renders and a test harness on the machine. 0.34 s per frame is an upper bound for this machine idle [INFERRED].
- Tool failures: one `gh api` call failed because zsh expanded the `?ref=` in an unquoted URL (`no matches found`); quoting the URL fixed it. YuNet prints `setPreferableTarget Targets are not supported by the new graph engine` on every load (OpenCV 5.0.0); detection ran.
