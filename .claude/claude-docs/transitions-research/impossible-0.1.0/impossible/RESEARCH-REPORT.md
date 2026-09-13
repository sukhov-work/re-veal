# Impossible: An Engineered Pipeline for Steerable, Dream-like Video Transitions

Research report, current as of September 2026. Target: MacBook Pro M3 Pro,
36 GB unified memory, fully local, Python 3.12+, pip-installable, everything
downloadable up front then offline. Evidence labels: [VERIFIED] primary
source or two independent sources; [INFERRED] reasoned from evidence;
[UNVERIFIED] plausible but unconfirmed; [ASSUMPTION] stated default. The
condensed version; the RESEARCH-PLAN.md turns it into experiments.

## Summary

Build five tiers: (0) decode and analysis, (1) correspondence, (2) a
deterministic morph that is exact and reproducible, (3) optional generative
enrichment that only ever modifies a bounded, masked, seeded window of the
deterministic frames, (4) color and light, (5) render and stitch. The
dreaminess slider is SDEdit-style denoise strength applied on top of the
deterministic result. Ship tiers 0-2 and 4-5 as the product; treat tier 3 as
opt-in with a hard time budget, because local video diffusion on Apple
Silicon is minutes per second of 480-720p video and the Metal paths are
fragile [VERIFIED, section 4].

Recommended stack, all local: RoMa (dense warp + certainty, MIT) with
DISK+LightGlue and MAGSAC++ for related pairs; DINOv2/DINOv3 + DIFT/SD-DINO
features, SAM 2/3 masks and user control points through Moving Least
Squares for unrelated pairs; importance-weighted forward splatting for the
morph, FILM or RIFE for moderate motion; Depth Anything V2/V3 or Apple Depth
Pro for 2.5D camera moves; PyAV for exact-frame video I/O; time-varying
Reinhard or optimal-transport color transfer.

## 1. Transition mechanisms

Film transitions reduce to: match cut, morph cut (flow warp + dissolve),
whip pan / zoom-through (motion blur hides the cut), portal or mask reveal,
luma and gradient wipes, dissolves. Commercial "seamless" tools are one of
two mechanisms: optical-flow frame morphing (Premiere Morph Cut, Resolve
Smooth Cut, FCP flow) or template transforms with displacement maps
(FilmImpact, Motion Bro, Sapphire) [VERIFIED]. Adobe documents 10-20 frames
as the useful Morph Cut length with a 30-frame default; Resolve and FCP
practice keeps flow morphs to 2-4 frames [VERIFIED]. Short transitions hide
flow errors, long ones expose them; that is why long transitions need the
machinery below rather than a dissolve.

Academic lineage: Beier-Neely 1992 line-pair field morphing; mesh and
thin-plate-spline morphing; Liao et al. SIGGRAPH 2014, symmetric
optimization on a halfway domain [VERIFIED].

Grammar the tool exposes as composable paths, each with its own timing
curve and mask: warp, dissolve, portal, camera move, generative.

## 2. Correspondence

Related pairs. RoMa (Edstedt et al., CVPR 2024, arXiv 2305.15404, MIT; the
DINOv2 backbone is Apache-2.0) outputs a dense warp in [-1,1] plus a
per-pixel certainty, reports 80.1 mAA@10px on WxBS (a 36% improvement), is
on PyPI as `romatch`, default working size 560 with 864 upsample, and has a
lighter Tiny RoMa [VERIFIED]. VGGT (CVPR 2025) returns camera pose, depth
and point maps from two views in under a second on a GPU, for 3D camera
moves [VERIFIED]. Depth: Apple Depth Pro (2.25 MP in 0.3 s on a V100,
metric, no intrinsics) or Depth Anything V3 (Nov 2025, arXiv 2511.10647,
+44.3% pose and +25.1% geometry accuracy over VGGT) [VERIFIED]; on a
MacBook use Depth Anything V2 Small/Base or Depth Pro and cache the result.

Unrelated pairs. There is no geometric correspondence. DINOv2/DINOv3 patch
features (DINOv3 arXiv 2508.10104) and DIFT (NeurIPS 2023) give semantic
matches; the SD-DINO fusion (NeurIPS 2023) is the standard recipe
[VERIFIED]. Pipeline: SAM 2/3 or Grounded-SAM masks for the salient object
in each image, part-to-part matching on fused features, edge and shape
matching as a fallback, then the user overrides with a few dragged points.
Sparse points become a dense warp through Moving Least Squares (Schaefer et
al., SIGGRAPH 2006, closed-form affine/similarity/rigid) or thin-plate
splines [VERIFIED].

## 3. Deterministic morph

Estimate displacement both ways, forward-warp each endpoint toward the
intermediate frame, cross-dissolve. Forward warping needs collision
handling: softmax splatting (Niklaus and Liu, CVPR 2020) weights colliding
source pixels by an importance metric and has a reference PyTorch
implementation [VERIFIED]. Disocclusions: LaMa for fast deterministic fill,
diffusion inpainting for quality.

Frame interpolation networks work as morphers for moderate motion: FILM
(Google, Apache-2.0) is designed for large motion; RIFE (MIT) has a
`rife-ncnn-vulkan` port that runs on macOS through MoltenVK without PyTorch
[VERIFIED]. Both ghost on dissimilar content; that is where the RoMa morph
or the generative tier takes over.

## 4. Generative tier, with Apple Silicon numbers

Wan 2.2 (July 2025, Apache-2.0) is the last Wan with open weights; 2.5+
are API-only. TI2V-5B: 5 s of 720p in under 9 minutes on an RTX 4090 per
the model card; on a Mac, a measured M1 Max 64 GB GGUF run took 82 minutes
for a 2 s clip and FP8 fails on Metal; the MLX q8 build is 19.6 GB and runs
several times slower than a 4090 [VERIFIED].

LTX-2 (Lightricks, weights Jan 2026, 19B = 14B video + 5B audio, arXiv
2601.03233) has a first-party keyframe (first+last frame) pipeline, IC-LoRA
depth/pose/canny control and camera-move LoRAs. License: LTX-2 Community,
free under 10M USD annual revenue, not Apache. MLX int8 is about 21 GB and
fits; a measured ComfyUI/MPS GGUF run was 13 min 42 s for 33 frames of
768x512 on an M1 Max; the distilled 2-stage pipeline produces NaN on MPS.
The MLX port is the viable route and has no published end-to-end timing at
36 GB [VERIFIED].

Framer (ICLR 2025) adds point-trajectory control to an image-to-video
model; Generative Inbetweening (ICLR 2025) adapts I2V models to keyframe
interpolation [VERIFIED].

Steering, so the classical transition stays in charge:
- Go-with-the-Flow (Burgert et al., CVPR 2025 Oral, modified Apache-2.0
  with attribution) warps the initial noise along an optical-flow field,
  is model-agnostic and costs nothing extra at inference [VERIFIED]. This is
  the direct fit: compute the deterministic displacement, warp the noise
  with it, let the model add detail.
- Framer trajectories from the deterministic correspondence.
- LTX-2 IC-LoRA depth/canny from the deterministic frames. There is no
  first-party optical-flow channel.
- SDEdit: start denoising from the deterministic frames at strength =
  dreaminess.

Image morphing with diffusion for photo pairs: DreamMover (ECCV 2024, arXiv
2409.09605) is built for large motion, uses diffusion features to reason
about semantic correspondence, and is over 10x faster than video diffusion
[VERIFIED]. DiffMorpher (CVPR 2024), IMPUS and FreeMorph are the
alternatives.

MPS is not deterministic; a fixed seed reproduces only on CPU. Document it.

## 5. Color and light

Extend masked Reinhard transfer to a time-varying transfer by interpolating
Lab or OKLab statistics; use Monge-Kantorovich or sliced optimal transport
for palette morphs; interpolate LUTs for graded looks. Relighting: IC-Light
V1 is usable, V2 (Flux) is non-commercial only [VERIFIED]. HDR: keep the
transition in the clips' transfer function, use zscale/libplacebo to tone
map when mixing SDR and HDR, tag HEVC as hvc1 for Apple players [VERIFIED].

## 6. Video I/O

PyAV decodes HEVC with VideoToolbox on macOS. Timestamp seeking is
keyframe-accurate at best and iPhone footage is often variable frame rate,
so decode forward from the previous keyframe and select by PTS. Frame-exact
joins require re-encoding the touched neighborhood; stream copy snaps to
keyframes. ffmpeg concat can produce off-by-one and non-monotonic DTS near
joins, so re-encode a small neighborhood around each join to a common
codec, fps and color space, then concat [VERIFIED].

Motion carry-over: estimate velocity on the last frames before the cut
and the first after it with optical flow, extrapolate the outgoing motion
into the transition and ease into the incoming motion [INFERRED].

## 7. Quality

No single number. Use warping error (flow-warp frame t to t+1, measure the
residual; the standard blind temporal-consistency metric), VBench temporal
flicker and subject consistency, LPIPS and DISTS between adjacent frames,
FVD for generative candidates, and a hidden-cut detector on the join
[VERIFIED]. Present K candidates as thumbnail strips and let the operator
choose.

## 8. Make or wrap

Wrap: RoMa, kornia DISK/LightGlue, OpenCV MAGSAC++, softmax splatting
reference, FILM or rife-ncnn-vulkan, Depth Anything / Depth Pro, SAM 2/3,
PyAV, DreamMover, Go-with-the-Flow, the LTX-2 MLX port. Build: the grammar
and compositor, class routing, the anchor editor and MLS warp, the budget
engine, the color interpolator, exact-frame I/O and stitching, the
candidate scorer, the offline model manifest. Do not adopt ComfyUI or
Deforum as the runtime; reuse their model conversions as artifacts.

## 9. Risks

| Risk | Mitigation |
|---|---|
| Generative tier too slow or unstable on Metal (82 min per 2 s measured for Wan GGUF; LTX-2 FP8 NaN) | Deterministic tiers are the product; generative is opt-in with a budget; MLX int8 distilled; bounded window and mask |
| MPS non-determinism | Best-effort seed on MPS, CPU fallback when reproducibility matters |
| Unrelated-pair correspondence is ambiguous | Anchor editor is required, not optional; fall back to dissolve or portal |
| Frame-accurate concat, VFR iPhone clips | Re-encode join neighborhoods; PTS-based selection |
| HDR/HLG 10-bit | Stay in the clip's transfer function; test on real footage early |
| Licenses: LTX-2 Community, IC-Light V2 non-commercial, SAM custom | Default to Apache/MIT paths (Wan 2.2, FILM, RIFE, RoMa) |

## 10. Open questions

End-to-end LTX-2 and Wan 2.2 wall clock on an M3 Pro 36 GB through MLX at
480p and 720p; whether Go-with-the-Flow's fine-tuned bases run under MPS or
MLX; the right working color space for mixed SDR/HDR pairs; whether VGGT is
stable on unrelated pairs; whether RoMa certainty alone can route Class A
versus B.
