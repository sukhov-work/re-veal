<!-- Provenance: written 2026-10-17 by an Opus 5.5 subagent (research track, afternoon) of the Claude Code session of that day (the round-8/9 session; DECISIONS 2026-10-17), copied verbatim from benchmarks/runs/2026-10-17/agents/frontier_report.md (sha256 306a7a8e4f9e3cb1) on the owner's order; folded into the candidates behind backlog T34 and the round-10 helpers. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# Frontier survey: techniques that break the 2D-compositing ceiling (2026-10-17)

The three named cases can be moved past "2D compositing" mostly with deterministic geometry: a perspective camera
pull-back through a homography chain (bar→lounge), a conformal log-polar warp that bends A's straight structures
into B's spiral arms (sunset→galaxy), and an ordered stroke decomposition of B painted over held A (boxes).
Generative video models (Wan VACE, Go-with-the-Flow, Framer) can be constrained by our own flow, depth or masks,
but every one of them still re-synthesises pixels, so each carries an F3 risk and a "full video generation" risk.
Only VACE has a stated path onto the Strix Halo box: stable-diffusion.cpp lists Wan2.1 VACE and has a Vulkan backend.
No surveyed generative video model states Mac/MPS support.

Scope: primary pages only (arXiv abstract pages, GitHub READMEs, Hugging Face model cards, vendor API docs),
read 2026-10-17 through WebFetch. A blank cell means the page did not state it; such cells are UNVERIFIED, not guessed.
Abbreviations: FLF = first+last frame conditioning; I2V = image-to-video; 3DGS = 3D Gaussian splats;
F1 crossfade / F2 2D decoration / F3 invention (owner's failure modes); NV = NVIDIA CUDA stated.

---

## Family 1. Guided inbetweening / video diffusion where motion is the control

| Technique | Source | Date | Code+weights public | Size | Licence (recorded) | Hardware stated | What it gives here | Rule risk | Box / Mac feasibility (best / worst) | Conf. |
|---|---|---|---|---|---|---|---|---|---|---|
| Framer (point-trajectory inbetweening) | https://github.com/aim-uofa/Framer ; arXiv 2410.18978 | arXiv 2024-10-25, ckpt 2024-12-19, ICLR 2025 | yes (HF wwen1997/framer_512x320 + SVD-img2vid-xt) | SVD-xt base; size not stated | BSD-2 academic; commercial by contact | PyTorch 1.13 + CUDA 11.6 (NV) | Start+end frame plus user keypoint trajectories; we can supply trajectories from RoMa/SIFT matches, so motion follows our correspondences | F3 (pixels between endpoints are synthesised); F1 if trajectories are sparse | best: runs on box under ROCm PyTorch (UNVERIFIED); worst: CUDA-only kernels. 512x320 only, too low for 1080 output without upscaling | med |
| Generative Inbetweening (Wang et al.) | arXiv 2408.15239 | 2024-08-27, ICLR 2025 | code not confirmed on abstract page | SVD-based (inferred from project URL, UNVERIFIED) | — | — | Bidirectional sampling of an I2V model between two keyframes | F3; no motion control input | low value: no control channel for our flow | low |
| Go-with-the-Flow (warped-noise motion control) | https://github.com/Eyeline-Labs/Go-with-the-Flow ; arXiv 2501.08331 | CVPR 2025 Oral | yes (HF Eyeline-Labs/Go-with-the-Flow; CogVideoX LoRAs per README) | CogVideoX base; size not stated | modified Apache-2.0 (film-credit clause §10) | "requires GPU" | Noise is warped by an optical-flow field derived from a driving video; we can render our deterministic draft as the driving video so the model's motion equals our flow | F3 on texture; "full video generation" | best: CogVideoX runs on box via ROCm PyTorch (UNVERIFIED); worst: none on Mac; I2V first-frame editing code "not yet released" per README | med |
| Diffusion as Shader (3D tracking video control) | https://github.com/IGL-HKUST/DiffusionAsShader ; arXiv 2501.03847 | SIGGRAPH 2025; news to 2025-06-05 | yes (HF EXCAI/Diffusion-As-Shader) | CogVideoX-5b-I2V base; Wan2.1-Fun-1.3B branch | Apache-2.0 | 32 GB GPU "sufficient", tested H800 | Conditions on a coloured 3D-point tracking video; our depth-unprojected points moved along our camera path become the control, so geometry is ours | F3 on texture; full video generation | 480x720, 49 frames. best: box with 128 GB unified + ROCm (UNVERIFIED); worst: CUDA-only. No Mac | med |
| MotionCanvas (scene-space camera+object motion) | arXiv 2502.04299; https://motion-canvas25.github.io/ (links github.com/Doubiiu/MotionCanvas) | 2025-02-06, SIGGRAPH 2025 | repo linked; contents not verified | — | — | — | Joint camera + object path design for I2V | F3; full video | UNVERIFIED whether weights are released | low |
| TrajectoryCrafter | https://github.com/TrajectoryCrafter/TrajectoryCrafter | 2025-02/03, ICCV 2025 Oral | yes (HF) | not stated | LICENSE files, terms not shown | ≥28 GB VRAM | Re-cameras a monocular VIDEO; not for a still pair | full video | box only; input must be video | med |
| ReCamMaster | https://github.com/KwaiVGI/ReCamMaster | ckpt 2025-04-09, ICCV 2025 | yes (HF KwaiVGI/ReCamMaster-Wan2.1) | Wan2.1-T2V-1.3B base | MIT (repo) | not stated | Re-cameras an 81-frame video along 10 preset paths | full video; input must be video | box only; relevant only when the input is video | med |
| Wan2.1 FLF2V-14B-720P | https://huggingface.co/Wan-AI/Wan2.1-FLF2V-14B-720P | 2025-04-17 | yes | 14B | Apache-2.0 | VRAM not stated; offload flags | Exact first and last frame; 720P only; trained mainly on Chinese captions | F3, F1 (owner already saw LTX FLF give "a cut or dumb fade") | box: ComfyUI/PyTorch-ROCm (UNVERIFIED); stable-diffusion.cpp lists Wan but FLF2V not named | high |
| Wan2.2 (T2V/I2V-A14B MoE, TI2V-5B) | https://github.com/Wan-Video/Wan2.2 | 2025-07-28 | yes | A14B MoE; 5B dense | Apache-2.0 | A14B 80 GB single GPU; TI2V-5B 24 GB (4090) at 720P/24 fps | Base for Fun/VACE variants below; FLF not mentioned in the official README | full video | 5B fits box memory easily; ROCm UNVERIFIED | high |
| Wan2.2-Fun (InP start/end; Control depth/canny/pose/trajectory; Control-Camera) and Wan2.2-VACE-Fun-A14B | https://github.com/aigc-apps/VideoX-Fun | dates not stated | yes | 5B and A14B | project Apache-2.0; per-weight not stated | tested 3060 12G…A100 80G with CPU-offload/qfloat8 modes | InP = start+end image; Control = our depth/flow-derived control video; VACE-Fun = control + masks. Whether control and end image combine in Wan2.2-Fun is not stated (CogVideoX-Fun does take control_video + validation_image_end) | F3 inside generated regions; full video | best: box via PyTorch-ROCm; worst: CUDA-only paths in VideoX-Fun | med |
| Wan VACE (1.3B / 14B; R2V, V2V, masked V2V; depth, inpaint, move/swap/expand-anything) | https://github.com/ali-vilab/VACE | 2025-03-31 preview; 2025-05-14 release | yes | 1.3B (81x480x832), 14B (81x720x1280) | Apache-2.0 | not stated | Masked V2V: freeze everything outside a mask and let the model render only inside it, conditioned on our depth/structure control video. This is the closest tool to "generated content as a helper held to a mask" | F3 inside mask; full video if mask is large | **best: stable-diffusion.cpp lists "Wan2.1 Vace" and a Vulkan backend → runs on the existing Strix Halo container**; worst: sd.cpp VACE lacks mask or control inputs (not checked) | med |
| LTX-2 / LTX-2.5 | https://github.com/Lightricks/LTX-2 | page undated; sd.cpp news: LTX-2.3 support 2026-05, LTX-2.5 2026-08 | yes (~66 GiB listed files) | 22B transformer + Gemma 4 12B encoder (from filenames) | LICENSE linked, terms not shown | fp8-cast + offload suggested | KeyframeInterpolationPipeline; IC-LoRAs listed are detailer/HDR/dub, no depth/pose control listed on that page | F1/F3 (owner rejected LTX: "a cut or dumb fade") | box via sd.cpp Vulkan (support listed) | med |
| CogVideoX-Interpolation (community) | Space roll-ai/CogVideoXInterp → feizc/CogvideX-Interpolation | — | weights ~20 GB auto-download (Space notes) | CogVideoX-5B | not checked | — | FLF on CogVideoX | F3 | not opened; UNVERIFIED | low |
| ToonCrafter | https://github.com/Doubiiu/ToonCrafter | 2024-05-29 | yes | ToonCrafter_512 | Apache-2.0 | ~24 GB (community ~10–12 GB) | 512x320, 16 frames, sketch guidance; cartoon-trained | F3; real-photo suitability not addressed | low value for photos | med |
| TVG (GPR latent interpolation, training-free) | arXiv 2408.13413; sobeymil.github.io/tvg | 2024-08-24 | code listed on project page (not opened) | uses DynamiCrafter-class model (UNVERIFIED) | — | — | Smoother latent path between two frames | F1/F3 | low | low |
| VTG (Versatile Transition Generation) | arXiv 2508.01698 | 2025-08-03, ICCV 2025 | code not linked on abstract page | I2V base unnamed | — | — | Interpolation-based init for concept blending and scene transitions; TransitBench (200 pairs) as an evaluation set | F3 | UNVERIFIED | low |
| ArbInterp (arbitrary-timestamp generative interpolation) | ICLR 2026 proceedings (36572cc8…) | 2026 | not checked | — | — | — | Frames at any continuous timestamp | F3 | UNVERIFIED | low |

Constraint answer for Family 1: Go-with-the-Flow (flow → noise), Diffusion as Shader (3D tracks), Wan-Fun Control and VACE
(depth/pose/trajectory video + masks) and Framer (trajectories) all accept a control signal we can compute from our own flow,
depth or mattes. None of them guarantees that output pixels come from A or B: each re-synthesises texture. VACE masked V2V is
the only one that keeps pixels outside the mask untouched by construction (stated task family MV2V; per-pixel fidelity outside
the mask UNVERIFIED).

## Family 2. Diffusion image morphing

| Technique | Source | Date | Code+weights | Base | Licence | Hardware | Endpoints exact? | What it gives | Risk | Feasibility | Conf. |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AlignMorph (OT transport then denoise) | arXiv 2609.24330; https://github.com/51xOne/Alignmorph | 2026-09-21 | code yes; uses SD2.1-768 | SD 2.1 + FreeMorph + FeatUp + DINOv2 | not stated (NOTICE.md only) | CUDA; examples on 24 GB | not stated; outputs 7-frame sequence | Entropic-OT semantic alignment before denoising; reported less ghosting. Closest to our optimal-transport matte transport | F3: intermediates are hybrid objects that are in neither photo | box (ROCm UNVERIFIED); 7 frames need our own inbetweening | med |
| CHIMERA | arXiv 2512.07155; cmlab-korea.github.io/CHIMERA | v1 2025-12-08, v9 2026-10-10 | code link not on abstract page | "diverse backbones" | — | — | not stated | VLM-generated shared anchor prompt; Global-Local Consistency Score metric | F3 | UNVERIFIED | low |
| FreeMorph | arXiv 2507.01953; https://github.com/yukangcao/FreeMorph | ICCV 2025 | code yes, weights none linked | not named on page | not stated | CUDA 12.1 | not stated | tuning-free, "10x–50x faster" than prior methods | F3 | box | low |
| DiffMorpher | https://github.com/Kevin-thu/DiffMorpher ; arXiv 2312.07409 | CVPR 2024 | yes | SD 2.1-base, one LoRA per image | repo LICENSE (terms not shown) | not stated | LoRA per endpoint reconstructs each endpoint closely; exactness not measured on page | AdaIN + reschedule options | F3, F1 at large layout gaps | box | med |
| IMPUS | https://github.com/gol2022/IMPUS ; arXiv 2311.06792 | ICLR 2024 | yes | SD v1.4 | — | — | — | perceptually uniform sampling | F3 | box | low |
| AID / PAID (attention interpolation) | https://github.com/QY-H00/attention-interpolation-diffusion | NeurIPS 2024 | yes | — | — | — | text-to-image interpolation, real-image endpoints not native | F3 | — | low |
| NoiseDiffusion, Smooth Diffusion | — | — | repo not found / not searched | — | — | — | — | — | — | — | none |

Answer for Family 2: no surveyed page claims pixel-exact endpoints. All of them interpolate semantically by producing hybrid
objects, which is the owner's F3 for whole frames. Usable only as a helper for one small layer (e.g. the sun disc → galaxy
core patch) and then held to that layer's matte.

## Family 3. Single-image 3D for perspective zooms and parallax

| Technique | Source | Date | Code+weights | Size | Licence | Hardware | Gives | Risk | Feasibility | Conf. |
|---|---|---|---|---|---|---|---|---|---|---|
| SHARP (Apple, feed-forward 3DGS from one photo, metric scale) | https://github.com/apple/ml-sharp ; arXiv 2512.10685 | 2025-12 | yes (sharp_2572gikvuh.pt, auto-download) | not stated | LICENSE + LICENSE_MODEL, names not shown | predict on CPU, CUDA or **MPS**; video render needs CUDA (gsplat) | A real 3D scene per photo; parallax dolly-out with disocclusion handled by splats, not by a 2.5D mesh | offline weight download must go through `warmup`; F3 small (occluded Gaussians are predicted) | **Mac best case: predict on MPS, render with our own CPU splat rasteriser** (needs writing; UNVERIFIED speed). Worst: rendering CUDA-only | med |
| 3D Photo Inpainting (Shih 2020) | https://github.com/vt-vl-lab/3d-photo-inpainting | CVPR 2020 | yes | — | MIT | CUDA 10.1 stack; 2–3 min per photo | LDI mesh + inpainted occlusions; paths zoom-in, swing, circle, dolly-zoom | F3 small (inpainted rims) | old PyTorch 1.4; CPU UNVERIFIED | med |
| 3D Ken Burns (Niklaus 2019) | https://github.com/sniklaus/3d-ken-burns | — | yes | — | CC BY-NC-SA 4.0 | CuPy/CUDA required | auto camera path + manual editor | F3 small | CUDA only; not Mac | high |
| Stable Virtual Camera (SEVA) | https://github.com/Stability-AI/stable-virtual-camera | 2025-03; v1.1 2025-06 | yes | 1.3B | non-commercial | torch ≥2.6, flash-attn | novel views along arbitrary camera paths from N input views, 576P | F3 outside frame | box (ROCm UNVERIFIED) | med |
| GEN3C | https://github.com/nv-tlabs/GEN3C | 2025-06-06, CVPR 2025 | yes | 7B (Cosmos) | code Apache-2.0; NVIDIA Open Model Licence | H100/A100, ~43 GB peak with offload | single-image mode, 8 preset paths incl. zoom in/out, 121 frames | F3 for out-of-frame; full video | box memory fits; ROCm UNVERIFIED | med |
| ViewCrafter | https://github.com/Drexubery/ViewCrafter | 2024-09 | yes | — | Apache-2.0 (repo) | 13.8–23.5 GB, 50–120 s on A100 | single image, 25 frames at 576x1024 or 320x512, point-cloud-guided path | F3 | box | med |
| HunyuanWorld 1.0 (+lite) | https://github.com/Tencent-Hunyuan/HunyuanWorld-1.0 | 2025-07-26; lite 2025-08-15 | yes | FLUX-based | LICENSE (name not shown) | lite on 4090 | image → 360° panorama → layered mesh with foreground labels | F3 (panorama outside frame is invented) | box | med |
| HY-World 2.0 | https://huggingface.co/tencent/HY-World-2.0 | 2026-04-16 → 2026-05-18 | yes | WorldMirror 1.2B, Pano 80B / 425M, WorldStereo 17B | tencent-hy-world-2.0-community | not stated | image → 3DGS world + mesh | F3 | 80B pano model too large; 425M variant plausible | med |
| WonderZoom (multi-scale 3D world) | https://wonderzoom.github.io/ ; arXiv 2512.09164; github.com/jin-cao-tma/WonderZoom | 2025 | repo linked | — | not stated | not stated | single image → 3D scene, prompt-driven finer scales with scale-adaptive surfels | F3: new detail at every scale | UNVERIFIED | low |
| Generative Powers of Ten | arXiv 2312.02149 (CVPR 2024) | 2023-12 | no official code found | — | — | — | zoom stack with one prompt per scale, jointly sampled | F3: intermediate scales are new objects; violates "no object in neither photo" | no code | med |
| LingBot-World (Wan2.2 I2V-A14B, camera poses) | https://github.com/robbyant/lingbot-world | 2026-01-29; unmaintained, successor lingbot-world-v2 | yes | A14B | Apache-2.0 | not stated | image + per-frame intrinsics/poses → up to 961 frames | full video generation | box (ROCm UNVERIFIED) | med |
| VGGT (two-photo 3D relation) | https://github.com/facebookresearch/vggt | CVPR 2025 Best Paper; update 2026-05-18 | yes (gated form) | VGGT-1B | code permissive; original ckpt non-commercial, separate commercial ckpt | CUDA or CPU fallback; MPS not mentioned | cameras, depth, point maps, tracks from 2+ photos <1 s on GPU | none (measurement) | Mac CPU feasible (speed UNVERIFIED) | high |
| DUSt3R/MASt3R, Flash3D | — | — | not fetched | — | — | — | — | — | — | none |

Answer for Family 3: SEVA, GEN3C, ViewCrafter and LingBot-World render a camera path from one photo; none of their pages
offers a mask that confines hallucinated out-of-frame content. For a dolly-out where B surrounds A (both named zoom cases),
out-of-frame content is B itself, so no hallucination is needed; SHARP (3DGS) plus our own renderer is the only
Mac-feasible 3D path found.

## Family 4. Semantic correspondence across unrelated scenes

| Technique | Source | Date | Code+weights | Licence | Hardware | Gives | Risk | Feasibility | Conf. |
|---|---|---|---|---|---|---|---|---|---|
| DINOv3 dense features | https://github.com/facebookresearch/dinov3 | HF 2025-08-14 | yes; ViT-S 21M … ViT-L 300M … 7B | DINOv3 License | CUDA recommended; PyTorch only dependency | patch-level semantic matches (sun disc ↔ galaxy core; person ↔ person) | none | ViT-L on Mac CPU (speed UNVERIFIED) | high |
| DIFT (diffusion features) | https://github.com/Tsingularity/dift | NeurIPS 2023 | yes | MIT | defaults 768², ensemble 8 | cross-category edit propagation (qualitative only) | none | SD-based; heavier than DINO | med |
| GeoAware-SC ("Telling Left from Right") | https://github.com/Junyi42/GeoAware-SC | CVPR 2024 | yes | not stated | RTX 3090 feature extraction ~2 h for SPair | 85.6 PCK@0.10 SPair-71k; SD1.5 + DINOv2 fused | none | in-category benchmark; cross-domain untested | med |
| MatchDiffusion | arXiv 2411.18677 | 2024-11 | code open per abstract | — | — | generates BOTH clips from prompts with shared early noise | full generation; our endpoints are fixed photos | not applicable | med |
| Semantic Progress Function (retiming) | arXiv 2604.22554 | 2026-04-24 | code not linked | — | — | per-frame embedding distance curve; retime so semantic change is constant-rate | none (post-process) | numpy + DINO embeddings, Mac | med |

Shape-aware matching: galaxy arms are fitted by logarithmic spirals and by the Ringermacher–Mead formula
(arXiv 0908.0892, MNRAS 397, 2009). Under the complex exponential map w = exp(a·z), straight lines become logarithmic
spirals (standard conformal-mapping fact; Escher Print-Gallery analysis: de Smit & Lenstra, Notices AMS 50(4), 2003 —
not fetched this session). This gives a deterministic, non-Euclidean route from A's straight bridge deck to B's arm.

## Family 5. Stylized and procedural

| Technique | Source | Date | Code+weights | Licence | Hardware | Gives | Risk | Feasibility | Conf. |
|---|---|---|---|---|---|---|---|---|---|
| Stylized Neural Painting | https://github.com/jiupinjia/stylized-neural-painting | CVPR 2021; CPU mode 2020-11-29 | yes | README CC BY-NC-SA 4.0; sidebar CC0 (conflict) | **CPU supported**; 4 GB GPU lightweight renderers | parameterised oil / watercolour / marker / tape strokes optimised to reproduce a target, progressive render | F2 if strokes read as an overlay; F3 none (stroke colours sampled from B) | Mac CPU | med |
| Paint Transformer | https://github.com/Huage001/PaintTransformer | ICCV 2021 | yes | Apache-2.0 | Linux/macOS, PyTorch 1.7+ | feed-forward stroke sets; serial render for animation | same | Mac | med |
| Paints-Undo | https://github.com/lllyasviel/Paints-UNDO | news to 2025-08-13 | yes | Apache-2.0 | NV 24 GB, 5–10 min/image | single-frame "undo step 0–999" + multi-frame (16 frames between two images) | F3: intermediate sketch states are invented; anime-trained | box (ROCm UNVERIFIED) | med |
| Inverse Painting | arXiv 2409.20556; https://github.com/ArmastusChen/inverse_painting | SIGGRAPH Asia 2024 (TOG) | repo linked, not opened | — | — | region-ordered painting from blank canvas, diffusion renderer | F3 moderate | UNVERIFIED | low |
| ProcessPainter | arXiv 2406.06062; github.com/nicolaus-huang/ProcessPainter | 2024-06 | listed | — | — | T2V painting process | F3, full video | UNVERIFIED | low |
| Droste / log-polar conformal warp, Möbius, particles, dolly-zoom, seam carving | de Smit & Lenstra 2003; Avidan & Shamir 2007 (not fetched) | — | numpy/OpenCV (`cv2.warpPolar`, `cv2.remap`) | — | Mac CPU | non-Euclidean, deterministic geometry over A and B pixels | F2 if applied as a whole-frame filter instead of per layer | Mac, seconds | high (math), owner-look UNVERIFIED |

Taichi (taichi-dev) was not fetched; star particles need nothing beyond numpy splatting of B's detected star peaks.

## Family 6. Tracking for mattes over time

| Technique | Source | Date | Licence | Hardware | Gives | Conf. |
|---|---|---|---|---|---|---|
| SAM 2.1 video predictor | https://github.com/facebookresearch/sam2 | 2024-09-29 | Apache-2.0 | GPU install intended; CPU/MPS not mentioned | Tiny 38.9M … Large 224.4M; points/box prompt then propagate; matte any generated clip back onto deterministic layers | high |
| CoTracker3 | https://github.com/facebookresearch/co-tracker | 2024-10-15 | CC-BY-NC (most) | "can run on CPU" for small tasks | offline and online point tracks; check that a generated clip's points follow our intended flow (a drift number per clip) | high |

## Family 7. VLM "director" (planning only; renderer stays offline)

| Model | Source | Multi-image | Spatial output | Structured output | Licence | Conf. |
|---|---|---|---|---|---|---|
| Gemini API (examples use `gemini-3.8-flash`) | https://ai.google.dev/gemini-api/docs/image-understanding | up to 3,600 images/request | boxes [ymin,xmin,ymax,xmax] 0–1000; segmentation as polygons 0–1000 | JSON schema via response_format | API | high |
| Claude (Opus 5.5, high-res tier 2576 px) | https://platform.claude.com/docs/en/build-with-claude/vision | 100–600 images/request | absolute pixel coordinates; docs call localisation "approximate" | via tools/JSON | API | high |
| Qwen3-VL 2B…235B-A22B (FP8 variants) | https://github.com/QwenLM/Qwen3-VL | yes, `add_vision_id` labels | boxes and points, relative coords; 3D boxes | not stated | Apache-2.0, local | med |

---

## Ranked top 10 for breaking the 2D ceiling on the three cases

Each probe is one pair, one command (a proposed scratch script unless a repo command is named), and the number or look that decides.

1. **Homography-chain camera pull-back through B's window (bar→lounge).** A is mapped by homography H_A into B's window quad;
   the virtual camera starts at H(0) = inverse of the quad-to-frame map (frame shows exactly A) and ends at H(1) = identity
   (frame shows B), with scale interpolated in log space and B's glass luminance screened over A. All pixels come from A or B;
   it is a true perspective change, not a slide. Mac, seconds.
   Probe: bar/lounge pair, `python scratch/window_pullback.py A B --quad <from SAM3/VLM>`. Decides: SSIM(frame0, A) ≥ 0.99,
   SSIM(frameN, B) ≥ 0.99, per-frame log-scale step constant within 5 %, and the owner sees no seam at the quad edge.
2. **Log-polar conformal warp of A's layers onto B's fitted spiral arm (sunset→galaxy).** Fit a log spiral to B's arm
   ridge, centre the map on the sun disc, and animate w = exp(a(t)·z) on the bridge layer only so the deck bends into the arm
   while the zoom-out shrinks A into B's core. Deterministic and non-Euclidean.
   Probe: sunset/galaxy pair, `python scratch/spiral_warp.py A B --layer bridge`. Decides: final-frame bridge-matte centreline
   lies within 8 px RMS of B's fitted arm curve, and the owner's look test on the mid frame.
3. **Ordered stroke decomposition of B's box zone painted over held A (boxes).** Stylized Neural Painting (CPU) or
   Paint Transformer fits strokes to B inside the aligned box matte; strokes land in order onto A's held plate, then a last
   short pass resolves to exact B. Stroke colours are sampled from B (no F3); geometry stays fixed.
   Probe: match_4 box pair, `python scratch/stroke_repaint.py A B --mask box --strokes 400` (wraps SNP `demo_prog.py`).
   Decides: final frame ΔE2000 vs B < 1 inside the matte, zero changed pixels outside it, and the owner says "repaint" not "overlay".
4. **Star field from B's own peaks with depth-ordered parallax (sunset→galaxy "stars passing").** Detect local maxima in B
   (galaxy), assign each a depth layer, and fly the camera through them during the zoom-out; stars fade in as B's alpha rises.
   Probe: galaxy photo, `python scratch/starfield.py B --n 2000`. Decides: every rendered star traces to a B pixel peak
   (100 %), and no frame-to-frame flicker above 2 luma levels in static regions.
5. **SHARP 3DGS per layer for real parallax in both zoom cases.** Gaussians from one photo on MPS; our own CPU rasteriser
   renders the dolly-out. Differs from the existing Depth-Anything dolly by carrying occluded surfaces.
   Probe: lounge photo, `sharp predict -i in/ -o out/` then `python scratch/splat_render.py out/*.ply --dolly -0.5`.
   Decides: disocclusion holes > 0.5 % of frame area at the end pose = fail; predict time on M-series MPS recorded.
6. **Wan VACE masked V2V as a texture helper over our deterministic draft (Strix Halo, stable-diffusion.cpp Vulkan).**
   Our render of cases 1–3 becomes the control video; the mask is limited to the transforming region (e.g. bridge→arm band).
   Probe: sunset/galaxy draft from #2, sd.cpp Wan2.1-VACE-1.3B at 480x832, 81 frames. Decides: CoTracker3 drift between draft
   and output < 2 px median inside the mask; outside the mask, max pixel change 0; owner rejects any new object (F3).
7. **Go-with-the-Flow with noise warped by our own flow.** The model's motion is our flow; it adds texture coherence that
   pure warping cannot. Probe: bar/lounge draft from #1 as driving video. Decides: same drift test as #6, plus endpoint
   SSIM ≥ 0.95 vs A and B. CUDA path; box ROCm UNVERIFIED.
8. **VLM director JSON plan (Gemini boxes/polygons 0–1000, or local Qwen3-VL).** Input A and B; output layers, matches
   (sun→core, bridge→arm, people→window), window quad, camera path, style. Probe: all three pairs, one API call each.
   Decides: IoU ≥ 0.6 between VLM boxes and SAM 3 masks for every named layer, and the plan names the same matches the
   owner named on 2026-10-17 for at least 2 of 3 pairs.
9. **DINOv3 ViT-L patch matching for theme correspondences.** Probe: sunset/galaxy, `python scratch/dino_match.py A B
   --query sun_disc`. Decides: top-1 match of the sun-disc patch falls inside B's core box; repeat for faces in bar→lounge.
10. **Semantic Progress Function retiming applied to any finished clip.** DINO embedding distance per frame, then retime
    to constant semantic speed. Probe: any current transition, `python scratch/spf_retime.py clip.mp4`. Decides: max
    deviation of the progress curve from linear drops below 0.05 after retiming and the owner prefers the retimed clip.

Excluded from the top 10 and why: whole-frame diffusion morphs (Family 2) and Powers-of-Ten zoom stacks produce objects that
are in neither photo (F3). Framer is 512x320. FLF2V-style models already failed the owner's look test once (LTX).

### Confidence: 60%

Facts in the tables are from the fetched primary pages (high for licences/dates/sizes that the pages state). The ranking is
reasoning, [INFERRED], and no probe has been run. The feasibility of every generative model on ROCm/Vulkan is UNVERIFIED
except that stable-diffusion.cpp lists Wan2.1 VACE, LTX-2.3/2.5 and a Vulkan backend.

### Gaps

- Pages that failed: CVF open-access page for VTG (HTTP 403); docs.anthropic.com vision page (301 redirect, re-fetched at platform.claude.com).
- Not stated on fetched pages: Framer frame count and VRAM; Go-with-the-Flow resolution, frames, VRAM, base-model sizes;
  LTX-2 licence terms and whether keyframes can sit at arbitrary frame indices; FreeMorph base model; AlignMorph licence and
  endpoint fidelity; SHARP licence names and checkpoint size; HunyuanWorld VRAM; SEVA single-image confirmation; Wan2.2-Fun
  control + end-image combination; VACE mask/control support inside stable-diffusion.cpp.
- Not searched or not found: NoiseDiffusion repo, Smooth Diffusion, PAID details, Flash3D, DUSt3R/MASt3R, Taichi,
  WonderJourney code, an official Powers-of-Ten implementation, MotionCanvas and Inverse Painting repo contents,
  CogVideoX-Interpolation README, Generative Inbetweening code.
- de Smit & Lenstra (2003) and Avidan & Shamir (2007) are cited from memory, not fetched.
- No Mac/MPS support is stated for any generative video model surveyed; SHARP predict is the only MPS statement found.
- Gemini model name `gemini-3.8-flash` is as printed in the Google docs example; availability not checked.
