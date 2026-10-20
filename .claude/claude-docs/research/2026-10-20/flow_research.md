<!-- Provenance: written by an Opus 5.5 subagent (the flow and in-between research track, 2026-10-20 about 23:50; its probe measured LoFTR, DISK+LightGlue and DIS on three pairs from weights already on disk) of the Claude Code session of 2026-10-20 (the round-12 session; DECISIONS 2026-10-20), copied verbatim from benchmarks/runs/2026-10-20/agents/flow_research.md (sha256 2dca07af9a5d5a5e) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"); folded into `EXPLORATION_PLAN.md` slices FL1–FL5, backlog T47–T51, the tooling list (readers). A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# Flow, tracking, in-betweens and shape correspondence for the director (research, 2026-10-20)

Written 2026-10-20 by an Opus 5.5 research subagent on the owner's order of the same day ("we need to use some kind of flow analysis (and maybe some other techniques we already explored like LoFTR, anything vectors-related) on adjacent video frames to better inform transitions"). It extends `research/2026-10-17/frontier_report.md` and does not repeat its seven families. Labels: [DOCS url] a primary page read today; [CODE file:line] this repo; [MEASURED] a run made today in the scratchpad (script `scratchpad/flowprobe/probe.py`, venv torch 2.13.0, kornia 0.8.3, OpenCV 5.0.0, Apple M3 Pro, 8 threads, nothing downloaded); [ASSUMPTION]; [OPEN].

## Verdict

Better flow does not fix the two-faces segments of the chain (T40). On two different people, every estimator measured today finds no correspondence on the face: LoFTR gives 141 matches on the café pair with none above 0.8 confidence, and DISK+LightGlue gives 19 [MEASURED]. The chain's consistency of 0.10–0.29 (T40) is a fact about the content, so what closes T40 and T45 is in-betweens close enough for flow to work and shape alignment (contour and landmark thin-plate spline, DINOv3 patches) before the flow. Flow and point tracking on adjacent frames are worth adopting as measures. The renderer's exact displacement maps are a free ground truth for choosing the estimator, and DIS costs 0.022–0.044 s per pair at 960 px on the Mac [MEASURED]. RAFT (torchvision, 5.26 M parameters, 20.1 MB [DOCS torchvision raft.py]) and CoTracker3 are the two learned candidates for a probe. Frame interpolation (RIFE, EMA-VFI, FILM) synthesises the occluded and refined pixels, so whether it may be used is a question for the owner (Q2). LoFTR adds nothing over DISK+LightGlue on themed pairs [MEASURED], and decision 22 should stay closed.

## Q1. Flow and tracking between adjacent frames

What the repo does today: `_homography_guided` pre-warps B by a homography and adds DIS (preset MEDIUM) on the residual [CODE transitions.py:442-459]. `consistency_weight` is exp(−e²/2σ²) of the forward-backward error [CODE transitions.py:462-471]. `forward_splat` moves colours along t·disp [CODE transitions.py:927]. Inside `keyframe_chain`, every segment after the lead is aligned by YuNet's five landmarks, then DIS forward and backward, and the flow is damped by the blurred consistency (`damp` 0.5 with the face guide) [CODE scripts/research/director_render.py:1236-1260]. A segment with consistency 0.1–0.3 is therefore mostly a cross-mix: a dissolve.

| Method | Licence | Weights | CPU on M3 Pro | Gives the director | Would close | Verdict |
|---|---|---|---|---|---|---|
| DIS (OpenCV, have it) | Apache-2.0 (OpenCV) [ASSUMPTION, not fetched] | none | 0.022 s per pair at 960×728, 0.044 s at 960×640 (preset MEDIUM, mean of 3) [MEASURED] | dense flow; occlusion and confidence only through the forward-backward check we already compute | rule 2's speed curve on an mp4 (retrospective §4 rule 2 already names it) | keep as the default; P1 measures its error against the renderer's maps |
| RAFT (torchvision `raft_large` / `raft_small`) | BSD-3 for torchvision [ASSUMPTION, LICENSE not fetched] | large 5,257,536 params, 20.1 MB; small 990,162 params, 3.8 MB; Sintel-train final EPE 2.72 (large C_T_V2) [DOCS https://github.com/pytorch/vision/blob/main/torchvision/models/optical_flow/raft.py] | UNVERIFIED; torchvision is not installed in `.venv` [CODE: `import torchvision` fails] | dense flow, more robust than DIS on large motion and low texture [ASSUMPTION] | the same as DIS, where DIS fails P1 | adopt for probe P1 |
| SEA-RAFT | BSD-3 [DOCS https://github.com/princeton-vl/SEA-RAFT] | one checkpoint named (`Tartan-C-T-TSKH-spring540x960-M`, HF `MemorySlices/...`); size not stated | not stated; "at least 2.3x faster than existing methods" on GPU [DOCS https://arxiv.org/abs/2405.14793] | dense flow; Spring EPE 3.69 | as RAFT | park behind RAFT; second arm of P1 only if RAFT fails |
| GMFlow / UniMatch | MIT [DOCS https://github.com/autonomousvision/unimatch] | sizes in MODEL_ZOO.md (not read) | not stated | dense flow (bidirectional and occlusion outputs not mentioned on the README) | as RAFT | park |
| CoTracker3 (offline, online) | CC-BY-NC for most of the code [DOCS https://github.com/facebookresearch/co-tracker]; licence is not a constraint here (memory rule) | size not stated; torch.hub `cotracker3_offline` | "can run on CPU" for small tasks; GPU strongly recommended; no timing [DOCS same] | tracks (B,T,N,2) plus visibility per point and frame; tracks through occlusion [DOCS https://arxiv.org/abs/2410.11831] | rule 2 (per-element speed curve with plateaus and jumps) and rule 3 (template drift of an element) on an mp4 the renderer did not make, including a real video from the owner | adopt for probe P2 |
| TAPIR / BootsTAPIR / TAPNext++ | code and checkpoints Apache-2.0 [DOCS https://github.com/google-deepmind/tapnet] | sizes not stated; PyTorch ports exist for TAPIR, BootsTAPIR, TAPNext++ | no CPU mention; 17 fps at 480×480 on a Quadro RTX 4000 (online TAPIR) [DOCS same] | tracks plus visibility; no uncertainty output named | as CoTracker3 | park; the fallback if CoTracker3 fails P2 |
| SpaTracker (V1; V2 named) | "follows the licence of CoTracker" [DOCS https://github.com/henry123-boy/SpaTracker] | `spaT_final.pth` plus a depth model (ZoeDepth default) | tested on an RTX A6000; 22 GB for about 10k points; no CPU mention [DOCS same] | 3D trajectories | nothing the 2D trackers do not already give the three measures | out for now (CUDA-sized; adds a second depth model) |

What none of them gives: a correspondence between two different faces. A tracker on our own rendered clip only reports what the renderer did. It is a measure, and it is useful because the skeptic now measures rule 2 by hand (retrospective §3e, §3f).

## Q2. Frame interpolation as the in-between of a subject's turn

Every network below estimates bidirectional flow between the two inputs, warps both, and blends them with a learned mask; most add a learned residual on top [ASSUMPTION from the papers' architecture as I know it; none of the READMEs read today states it]. The synthesised pixels are: (a) every pixel in a region occluded in one input (the far side of a turning head, the background a moving shoulder uncovers), which the fusion mask fills from the other input or invents; (b) the refinement residual over the whole frame; (c) any pixel where the two inputs disagree in content (two different faces), which comes out as a blend. Endpoints are exact at t = 0 and t = 1 by construction [ASSUMPTION]. These networks are trained on small motion between consecutive video frames, so on k1 → k3, two faces 5–6 levels apart (`research/2026-10-18/keyframes_r10.md`), I expect a ghosted blend like today's dissolve [ASSUMPTION]. P5 tests that.

| Method | Licence | Weights / framework | CPU on M3 Pro | Synthesises | Verdict |
|---|---|---|---|---|---|
| RIFE (ECCV 2022; Practical-RIFE successor) | MIT [DOCS https://github.com/hzwer/ECCV2022-RIFE] | PyTorch; Google Drive; size not stated | no CPU or MPS statement; "30+ FPS for 2X 720p" on a 2080 Ti [DOCS same] | occluded regions, fusion, residual; arbitrary timestep supported | the candidate if the owner says yes (P5) |
| FILM (Google) | Apache-2.0 [DOCS https://github.com/google-research/frame-interpolation] | TensorFlow 2 SavedModels on Google Drive; TensorFlow is a new dependency (a decision) | CUDA 11.2 environment; CPU mode "for debugging" [DOCS same] | the same; built for "large motion" (no number given) | park (TensorFlow) |
| AMT | CC-BY-NC 4.0 [DOCS https://github.com/MCG-NKU/AMT] | S / L / G; Google Drive, Baidu, Hugging Face; parameters not stated | not stated | the same | park |
| EMA-VFI | Apache-2.0 [DOCS https://github.com/MCG-NJU/EMA-VFI] | "Ours" and "Ours_small"; Google Drive, Baidu | not stated | the same; arbitrary timestep | the second arm of P5 |
| VFIMamba | Apache-2.0 [DOCS https://github.com/MCG-NJU/VFIMamba] | HF `MCG-NJU/VFIMamba_ckpts`; needs `mamba_ssm` and `causal_conv1d` | those packages are CUDA kernels, so no Mac path [ASSUMPTION] | the same | out on the Mac |

Where this stands against the rulings: no object is added, both endpoints are our own frames, and the motion follows estimated flow, so it is not "full video generation" in the sense of a model that writes a clip from a prompt or one image. It does paint pixels that exist in neither input, which makes it a generated helper under the 2026-09-29 conditions (realistic; at least half of the objects original and consistent; no new objects). That is his call, not this report's.

**Question for the owner:** May a frame-interpolation network (RIFE) paint the in-between frames of a subject's turn between two of our own stills, only inside the subject's matte and labelled as generated on the page, as a helper under your 2026-09-29 conditions? Recommended answer: yes, inside the matte only, and only between stills that already show the same person at nearby poses (denser FLUX.3 keyframes first, retrospective §6 item 4(i)). Between two different faces it would blend them, which is the dissolve you already rejected.

## Q3. Correspondence by shape and semantics between two different photos

Measured today at 640 px long side, MAGSAC homography at 4 px [MEASURED]:

| Pair | LoFTR outdoor (kornia) | DISK + LightGlue (kornia, reveal's weights) |
|---|---|---|
| café `mismatch_2` A → B (two different men) | 141 matches, 0 above 0.8 confidence, 15 homography inliers, 1.22 s | 19 matches, 11 above 0.8, 5 inliers, 1.64 s |
| sunset → galaxy `mismatch_5` | 20 matches, 0 above 0.8, 5 inliers, 0.80 s | 1 match, 0 inliers, 1.02 s |
| keyframes k1 → k3 (adjacent stills of one chain) | 2,840 matches, 2,698 inliers, 1.64 s | 1,525 matches, 1,519 inliers, 1.23 s |

On k1 → k3 the inliers are a homography, so they lie on the shared background. I did not count matches inside the man's matte, and that count is what T40 needs [OPEN]. LoFTR's weights came from `~/.cache/torch/hub/checkpoints/loftr_outdoor.ckpt` (46.3 MB, July 2026, outside `models/`). kornia 0.8.3 still fetches them over plain HTTP from `cmp.felk.cvut.cz` [CODE kornia/feature/loftr/loftr.py URL list], which is decision 22's first reason, unchanged.

| Method | Licence | Weights | CPU | Could land… | Verdict |
|---|---|---|---|---|---|
| Contour matching: sample each element's soft-matte contour at N points, align by Procrustes (similarity), then a thin-plate spline from matched contour points plus YuNet's five landmarks where a face exists | none: the thin-plate spline is a small numpy solve (`cv2.createThinPlateSplineShapeTransformer` is absent from this OpenCV 5.0.0 build and scipy is not installed [CODE: import checks today]) | none | ms [ASSUMPTION] | a sun disc on a core by shape (rule 4's Chamfer ≤ 8 px RMS is the test); a band on a band (truss, dust lane); a man on a man by silhouette plus landmarks, replacing the rotation-free similarity of the lead [CODE director_render.py:1206-1215] | adopt for P4; no dependency |
| DINOv3 patch features (ViT-S/16 21 M, ViT-B/16 86 M, ViT-L/16 300 M) | DINOv3 License [DOCS https://github.com/facebookresearch/dinov3] | HF `facebook/dinov3-*` via Transformers ≥ 4.56; the venv has 5.17.0 and `DINOv3ViTModel` exists [CODE: import check]; whether the HF repos are gated is not stated | UNVERIFIED | semantic part matches inside label-matched elements (head to head, hand to hand, sun to core), which feed the contour spline as extra pairs | adopt for P4 |
| DIFT | MIT [DOCS https://github.com/Tsingularity/dift] | Stable Diffusion (version not stated) or ADM; 768² input, ensemble of 8 | no CPU mention; a GPU assumed | the same as DINOv3, cross-category (qualitative only, frontier report) | park: an SD backbone for each pair, about eight forward passes, CPU cost UNVERIFIED |
| GeoAware-SC ("Telling Left from Right", CVPR 2024; one repo) | not stated [DOCS https://github.com/Junyi42/GeoAware-SC] | SD 1.5 + DINOv2 ViT-B/14 + a trained aggregator, 768×60×60 descriptors | CUDA demo; SPair-71k extraction about 2 h on an RTX 3090 | left/right-aware parts (which hand is which), 85.6 PCK@0.10 on SPair-71k (frontier report) | park; reopen if P4 shows left/right flips on the man |
| LoFTR | Apache-2.0 [DOCS https://github.com/zju3dv/LoFTR]; four checkpoints of about 45 MB | see above | 0.8–1.6 s at 640 px [MEASURED] | nothing semantic: 0 confident matches on either themed pair | out by decision 22; do not reopen for transitions (above) |
| DISK + LightGlue (have it) | in reveal | 47.6 MB [CODE models/hub/checkpoints] | 1.0–1.6 s at 640 px [MEASURED] | adjacent stills of one scene only | keep for alignment; not a semantic reader |
| RoMa | — | 1.7 GB | 35–55 s | 0–6 matches, false suns | rejected by measurement (`director-tooling.md §1`) |

What LoFTR would add over DISK+LightGlue: about twice the matches on near-identical stills (2,840 against 1,525 on k1 → k3), where dense DIS already gives a vector per pixel. On themed pairs it adds no confident match. A reopening line would buy nothing and bring back the HTTP fetch.

## Q4. Measurement plan

Every probe is a research script under `scripts/research/`, writes to `benchmarks/runs/<date>/flow/`, and takes weights only through a `warmup` subcommand that records sha256 in a manifest in the research tree (the `matte_source.py` pattern, `MATTE_MANIFEST.json`, `director-tooling.md §1`). `run` refuses without the manifest and sets `HF_HUB_OFFLINE=1`. Nothing enters `transitions.py`.

| Probe | Candidate | Pair and frames | Number that decides | Cost |
|---|---|---|---|---|
| P1 flow fidelity | DIS against RAFT-large (SEA-RAFT if RAFT fails) | the round-11 café and window clips re-rendered at 480 px with the renderer dumping its exact per-layer displacement between adjacent frames (it holds every map, retrospective §6 item 1) | median end-point error inside each moving element's matte. DIS stays if ≤ 0.5 px and the plateau and jump counts of rule 2 agree with the exact maps; RAFT is adopted for mp4 measures only if it halves DIS's error | 6 h (dump 2 h, script 2 h, torchvision in the research tree 2 h) |
| P2 tracker as skeptic measure | CoTracker3 offline (TAPIR if it fails) | café r11 mp4 (`mismatch_2`), a 20×20 grid inside the man's frame-0 matte | reproduces skeptic_r11b's plateau of frames 54–71 within ±2 frames and the lead's 1.0 → 13.6 px jump; CPU time per 90-frame clip at 480 px recorded (UNVERIFIED today) | 5 h |
| P3 chain segments by estimator | DIS, RAFT, LoFTR-seeded DIS, all after YuNet alignment | `r10_m2_k1.png` → `k3`, `k3` → `k2` | consistency mean inside the union matte (today 0.10–0.29, T40). If none reaches 0.5, the cause is the content, and slice FL3 moves to denser keyframes | 2 h after P1 |
| P4 shape correspondence | contour Procrustes plus TPS; DINOv3 ViT-S and ViT-B patches inside label-matched elements | `mismatch_5` sun → core and truss → dust lane; `mismatch_2` man → man (contour plus five landmarks) | rule 4: symmetric Chamfer ≤ 8 px RMS at 1920 px at the beat's end; DINOv3: ≥ 80 % of the sun-disc patches' top-1 matches inside B's core box, the head patches inside B's head box | 1 day |
| P5 interpolation (only on the owner's yes) | RIFE (EMA-VFI second) | k1 → k3 at t = 0.25, 0.5, 0.75 inside the matte, and the moved A man → k1 | `keyframe_screen.py` counts one face per frame; rule 7's double-exposure share ≤ 1 % inside the matte; CPU seconds per frame recorded | 4 h |

## Q5. Research slices for EXPLORATION_PLAN.md (ranked)

| # | Slice | Closes | Cost | Ruling it touches | Decision line it needs |
|---|---|---|---|---|---|
| 1 | FL1 Flow measures on adjacent frames (P1 then P2) | rule 2's continuity measure and rule 3's drift on any mp4, including a real video; feeds retrospective §6 item 1 | 1.5 days | offline contract; a new research dependency (torchvision for RAFT; CoTracker3 by torch.hub) | "torchvision and CoTracker3 weights in the research tree behind warmup + manifest; nothing in transitions.py [revert: delete the script and the manifest]" |
| 2 | FL2 Shape correspondence readers (P4) | T34, rule 4, the lead's rigid similarity (part of T45) | 1 day | none for contours; DINOv3 weights in the research tree | "DINOv3 ViT-S/B as the semantic reader of the research tree [revert: delete]" |
| 3 | FL3 Chain segments: estimator first, then dense keyframes (P3, then 4–8 FLUX.3 keyframes per turn) | T40, T45 | 0.5 day plus 3–6 min per keyframe on the box | 2026-09-29 helper conditions (already in force for keyframes) | none if P3 only measures; one line if the chain's segment rule changes |
| 4 | FL4 Frame interpolation in a matte (P5) | the turn's in-betweens (T45) | 0.5 day | "never full video generation" and the 2026-09-29 conditions | the owner's answer to the Q2 question, verbatim, then a line naming RIFE and its weights |
| 5 | FL5 LoFTR for transitions | nothing measured | 0 | decision 22 | none: recommend it stays closed (Q3 table) |

Backlog rows implied (T47 onward, for the session to add):

- T47: no measure of motion continuity runs on a decoded clip; the skeptic counts plateaus by hand. Candidates: DIS against the renderer's exact maps (P1), CoTracker3 (P2). OPEN.
- T48: the chain's lead and `morph_to` align by centres and boxes; no contour or landmark spline exists (rule 4, T34). Candidate: contour Procrustes plus TPS with YuNet landmarks; DINOv3 parts as extra pairs (P4). OPEN.
- T49: no measure tells whether a chain segment's low consistency is the estimator's fault or the content's (T40). Candidate: P3. OPEN.
- T50: whether frame interpolation inside a matte is allowed is unanswered; the question is in this report's Q2. Waiting on the owner.
- T51: LoFTR measured on themed pairs, no confident match (this report); decision 22 stays. Close at once as a recorded measurement.

### Confidence

70 % on the verdict. The LoFTR and DISK numbers and the DIS timings are measured today on three pairs at one size (640 px; 960 px for DIS), which is a small sample. Licences, parameter counts and checkpoint names come from the pages cited. How the interpolation networks synthesise pixels, and the prediction that they blend two different faces, is reasoning that P5 tests.

### Gaps

- Not sourced: CPU or MPS speed on an M3 Pro for RAFT, SEA-RAFT, UniMatch, CoTracker3, TAPIR, RIFE, EMA-VFI, AMT, DINOv3, DIFT, GeoAware-SC (no page states one).
- Not stated on the pages read: weight sizes for SEA-RAFT, UniMatch, CoTracker3, TAPIR family, RIFE, AMT, EMA-VFI, VFIMamba; SEA-RAFT parameter count; GeoAware-SC licence; whether `facebook/dinov3-*` on Hugging Face is gated; DIFT's SD version.
- Not fetched: OpenCV's and torchvision's licence files; the original RAFT repository; UniMatch MODEL_ZOO.md; the RIFE, FILM, AMT and EMA-VFI papers (the synthesis description in Q2 is from memory); SpaTrackerV2; MediaPipe or other dense face-landmark models (a candidate for more than YuNet's five points, not surveyed).
- Not measured: matches inside the man's matte on k1 → k3; the contour spline's run time.
- The LoFTR checkpoint used today sits in `~/.cache/torch/hub`, outside any manifest; it was read, not downloaded.
