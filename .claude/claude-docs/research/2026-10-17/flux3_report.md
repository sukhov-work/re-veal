<!-- Provenance: written 2026-10-17 by an Opus 5.5 subagent (research track, afternoon) of the Claude Code session of that day (the round-8/9 session; DECISIONS 2026-10-17), copied verbatim from benchmarks/runs/2026-10-17/agents/flux3_report.md (sha256 3d2b88b192ffa7c0) on the owner's order; folded into `TRANSITIONS.md §13.5`. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# FLUX.3 Image Klein vs FLUX.2 klein 9B Q8_0 as a keyframe/plate helper (research, 2026-10-17)

## Findings

FLUX.3 Image Klein (distilled) runs on the Strix Halo box today. stable-diffusion.cpp merged support on 2026-10-15 (PR #2143, release `master-968-8cd731e`), and an 8-bit GGUF exists (unsloth Q8_0, 6,092,755,872 B). Its weights total about 10.7 GB at Q8_0 with the Qwen3-VL-4B Q8_0 encoder, against 18.9 GB for the current FLUX.2 klein 9B set. Against that, it needs 16 steps where klein 9B needs 4. It has no mask, no inpainting and no partial-strength mode in the reference code, and it expects a 9B prompt-upsampler caption in front of it. BFL reports it as better than FLUX.2 klein 9B (+91 Elo text-to-image, +70 Elo editing); those are internal numbers, and no independent leaderboard lists it yet. The one hands-on test I found measured the largest changes outside the edited region among 11 hosted configurations. Nothing was downloaded or run; every speed below for the box is [INFERRED].

### Key facts (each with URL)

**1. Weight sizes and gating** (HF API `?blobs=true`, read 2026-10-17)

| File | distilled `flux-3-image-klein` | base `flux-3-image-klein-base` |
|---|---|---|
| `model.safetensors` (bf16 DiT, BFL format) | 11,097,404,512 B | 11,076,957,072 B |
| `transformer/` (diffusers, 2 shards) | 9,907,529,352 + 1,189,878,064 B | 9,887,081,880 + 1,189,878,064 B |
| `variants/fp8r/model.safetensors` | 6,270,949,144 B | 6,250,501,712 B |
| `variants/nvfp4/model.safetensors` (4-bit, excluded by rule) | 5,277,674,144 B | 5,257,226,696 B |
| `ae.safetensors` (= `vae/…` 336,213,556 B) | 336,211,292 B | 336,211,292 B |
| `text_encoder/` Qwen3-VL-4B bf16 | 4,967,229,296 + 3,908,490,048 B | same |

- Upsampler `flux-3-image-klein-pup`: `model.safetensors` 18,819,722,392 B, Apache-2.0, **not gated**.
- `flux-3-image-klein`, `-base` and `-comfy` are `gated: auto`, which is click-through licence acceptance. On 2026-10-17 the owner's token downloaded files from `-base`. It got "Access denied. This repository requires approval" on `-comfy` and on most files of the distilled repo; the distilled README did download. The owner has to accept the terms on each repo page.
- Base manifest: 5,538,458,368 params, 357 tensors; fp8r is `FP8_PER_CHANNEL_PER_TOKEN` with the text-stream blocks left in bf16.
- Licence, recorded and not a filter: FLUX Kommunity License v1.0, which covers non-commercial use and commercial output for Qualifying Users under US$5M revenue. The Qwen3-VL text encoder and the upsampler are Apache-2.0. https://huggingface.co/black-forest-labs/flux-3-image-klein-base
- Comfy repo: bf16 11,097,404,512 B; int8-convrot 5,827,874,779 B (distilled); `qwen3vl_4b_bf16` 8,875,719,408 B; `flux2-vae.safetensors` 336,211,292 B, the same size as `ae.safetensors`. https://huggingface.co/black-forest-labs/flux-3-image-klein-comfy

**2. Editing interface in the reference code** (https://github.com/black-forest-labs/flux-3-image-klein, commit bfc8889, `src/flux3/pipeline.py`, `generate.py`, `bbox.py`)

- Up to 10 references. The autoencoder encodes each reference into 128-channel tokens that ride in a separate `image_cond` stream. The 4th RoPE axis is set to `-(1+index)` to tell references apart. The concatenated tokens go in beside the text and the noise tokens. Generation always starts from pure noise: no reference supplies an init latent, and no strength or denoise parameter exists.
- One reference: fitted to at most 4 MiB pixels (`MATCH_MAX_PIXELS = 4*1024*1024`), each side 64–4096 and rounded up to 16, then reflect-padded. The output defaults to that size and the padding is cropped off.
- Two or more references: each one is fitted under 1 MP (`MULTI_REFERENCE_MAX_PIXELS`) and centre-cropped to the 16-px grid. The output defaults to the first reference's size. Diffusers behaves differently: each reference keeps its own resolution up to 16 MP, and the output defaults to 1 MP at the first reference's aspect ratio. https://github.com/huggingface/diffusers/blob/main/docs/source/en/api/pipelines/flux3.md
- No mask or inpainting mode: a grep for `mask|inpaint` finds only the text-encoder attention mask. BFL's "pixel restoration", which "preserves unedited regions of an image exactly", belongs to the BFL API; the open reference code has no compositing step. https://bfl.ai/blog/flux-3-image-klein
- Bounding boxes go into the text prompt and are not a mask. The caption tags each element `<id>`, and a JSON array follows the caption. Generation rows are `{"id","bbox","desc"}`. Edit rows are `{"id","from":"ref_image_N"|"target","src_bbox","tgt_bbox","desc"}`. Boxes are `[y_min, x_min, y_max, x_max]` on a 0–1000 grid; the CLI's `--boxes` file uses 0–1. A `null` `tgt_bbox` removes the element, and equal src/tgt boxes keep it in place. The card says: "Boxes guide placement and scale; they do not constrain pixels to a hard mask … Edits can change content outside the requested region." BFL's docs add that new elements in boxes of about 40×25 px "often did not appear". https://docs.bfl.ml/flux_3/flux3_image_layout
- Resolution: the reference code allows sides of 64–4096. The API takes width/height in [64, 6256] up to 16,822,272 px ("4k" tier). https://docs.bfl.ml/api-reference/utility/generate-an-image-with-flux-3-klein
- Two references of different scenes: the i2i upsampler system prompt switches to a "generation request" voice ("Create a photograph of …") that says what to take from each image by ordinal and what is newly generated. The card says: "reference images anchor content, they do not lock structure."
- Sampler drift as of 2026-10-17: commit 62e90b9 (2026-10-17) changed the reference code's time-shift `alpha` from 6.93 to **16.0** and base CFG from 3.5 to **4.0**. The HF `config.json`, the diffusers docs and sd.cpp still use 6.93 and 3.5. sd.cpp exposes `--flow-shift` to override it.

**3. Prompt upsampler** (https://huggingface.co/black-forest-labs/flux-3-image-klein-pup)

- A full fine-tune of Qwen3.5-9B with the vision tower frozen: SFT, then preference tuning on Klein renders. It takes the request, up to 10 references (resized to ≤1 MP for one, 724² for two, 512² for three or more) and optional boxes. It returns one long caption of about 220–240 words in English. Four system prompts ship with it: `t2i`, `i2i`, `t2i_bbox`, `i2i_bbox`.
- `--no-pup`: the README says "the results are noticeably weaker" and allows it only "unless the prompt already is an upsampler caption". The card says "Do not use the model without a prompt upsampler."
- Size and memory: 18.8 GB bf16; "adds about 28 GB" GPU memory; the reference code runs it on **vLLM** at 0.35 of the GPU.
- External writers are supported. Commit 458dcc0 (2026-10-17) added `src/flux3/pup_prompts_external_vlm.json` (t2i 46,615 chars, i2i 6,194, t2i_bbox 27,258, i2i_bbox 21,614) "for external VLMs". BFL's own instruction is: "Any other LLM can take its place … pass the caption it returns as `prompt`." That covers Qwen3-VL or a frontier model.
- GGUF of the upsampler: `prithivMLmods/flux-3-image-klein-prompt-upsampler-GGUF` Q8_0 9,527,501,888 B plus mmproj-q8_0 624,229,728 B; `ND911/flux3-image-klein-pup-Q8_0-GGUFs`. Whether llama.cpp loads the Qwen3.5 vision path is UNVERIFIED.

**4. Runtime fit**

- (a) Box, sd.cpp Vulkan: PR #2143 "feat: add FLUX.3 Image Klein and Klein Base support", merged 2026-10-15 (merge commit 8cd731e). It covers the Qwen3-VL encoder path, reference-image editing (`-r` repeated up to 10) and "a dedicated flow denoiser". https://github.com/leejet/stable-diffusion.cpp/pull/2143 · docs https://github.com/leejet/stable-diffusion.cpp/blob/master/docs/flux3.md (distilled: `--cfg-scale 1.0 --steps 16 --sampling-method euler`). The page does not mention Vulkan, flow-map handling, bounding boxes or known issues. Latest release is `master-973-f0aac52` (17 Oct). The box's pinned container `sha256:0ab8e0e0…` predates this support and must be re-pulled (UNVERIFIED that a Vulkan image tag carries it).
- 8-bit GGUF repos for sd.cpp:
  - `unsloth/flux-3-image-klein-GGUF` Q8_0 6,092,755,872 B. Its LPIPS against bf16 is 0.006 and SSIM 0.989 (unsloth's own test, 19 renders); the card names diffusers as the loader, so sd.cpp compatibility is UNVERIFIED.
  - `DogukanUrker/FLUX.3-Image-Klein-GGUF` Q8_0 5,991,734,144 B, built and tested with sd.cpp ≥ 8cd731e (RTX 3060, 9.8 GB peak at 1024²).
  - `molbal/Flux-3-Klein-GGUF` (`sd` = distilled) Q8_0 5,895,533,344 B, built for ComfyUI-GGUF-Reboot, not sd.cpp.
  - Encoder: `Qwen/Qwen3-VL-4B-Instruct-GGUF` Q8_0 4,280,406,144 B. VAE: the FLUX.2 VAE, and the box's klein-9B set may already hold it (sha256 check UNVERIFIED).
- ComfyUI: "FLUX 3 Klein templates need ComfyUI 0.41.0 or later" (0.41.1 backport, ComfyUI#17070). It offers t2i, i2i and multi-reference templates, a `Create Bounding Boxes` node and an `enable_prompt_upsampler` switch. https://docs.comfy.org/tutorials/flux/flux-3-klein. The page has no AMD notes.
- ROCm on the box: the ROCm 10.1.0 matrix lists gfx1151 (Ryzen AI Max+ 395) and requires Ubuntu 26.04.1 or 24.04.5 with kernel 7.0 (https://rocm.docs.amd.com/en/latest/compatibility/compatibility-matrix.html). The box runs Ubuntu 25.10, kernel 6.17, ROCm 7.1.0. The ComfyUI and diffusers paths would therefore need a ROCm container and an untested PyTorch build. The repo's own earlier note, "BF16 not validated", stands UNVERIFIED for FLUX.3.
- The reference code pins `torch==2.11.0` cu130, `triton`, `vllm==0.21.0` and Python <3.13. It is CUDA-only and does not run on the box or the Mac as shipped.
- (b) Mac: M3 Pro, 38,654,705,664 B = 36 GB (`sysctl hw.memsize`). Diffusers MPS in bf16 is UNVERIFIED; no source covers it. The pipeline without the upsampler "loads about 20 GB" (diffusers docs), and with the upsampler 39 GB, which does not fit beside macOS. The MLX path has a report: `VisualInference/FLUX-3-Image-Klein-MLX-8bit` (transformer 6,151,786,641 B) via `flux3-mlx` takes "~115 s per image, 14.3 GB peak" at 1024², 16 steps, on an M4 Pro with 48 GB. https://huggingface.co/VisualInference/FLUX-3-Image-Klein-MLX-8bit. Also available: `vanch007/FLUX.3-Image-Klein-mlx-bf16` and an 8-bit pup MLX repo.

**5. Quality claims**

- Vendor: +91 Elo text-to-image and +70 Elo editing over FLUX.2 [klein] 9B, with 38% fewer parameters; internal Elo; no FLUX.2 klein 4B comparison. https://bfl.ai/blog/flux-3-image-klein
- Third-party, one outlet: Kingy.ai, on Fal endpoints with the **upsampler disabled** and a GPT judge. Distilled text-to-image passed 24/32 and base 23/32 (Nano Banana 2.1 passed 31). Editing passed the semantic check 12/12, but on average 6.23% of the pixels outside the edited region changed by more than 8 levels (5.66% base), against 1.44% for Nano Banana and 0.26% for Ideogram. Multi-reference was not tested. https://kingy.ai/blog/flux-3-image-klein-tested-benchmarks-costs/
- Quantization fidelity (unsloth, vendor-of-quant): Q8_0 LPIPS 0.006; Q4_K_M 0.060.
- No Artificial Analysis entry as of 2026-10-17 (kingy.ai; the-decoder.com).

**6. Capabilities new for this project** (recipes from the docs; none tried)

- Keyframe between two unrelated photos: no interpolation primitive exists. Recipe: `--image A --image B` with an i2i request naming what to take from "the first image" and "the second image". The upsampler writes a "Create a photograph of …" composition. The output takes A's size, each reference is ≤1 MP, and structure is not locked. Suitability as an in-between frame is UNVERIFIED.
- Plate where an object left: one reference plus an edit row `{"id":"box_1","from":"ref_image_0","src_bbox":[…],"tgt_bbox":null,"desc":"…"}` with an instruction "Remove the … <box_1> … everything else stays identical". The i2i system prompt tells the upsampler to "say what fills a removed region". Expect pixels outside the box to drift, because pixel restoration is API-only; the plate must be composited back through a mask in our code [INFERRED].
- "Boxes 30 % repainted": no strength parameter and no mask exist. The only routes are wording (for example "repaint the lower third of the boxes …", UNVERIFIED) or our own mask blend of a full repaint at 30% coverage [INFERRED]. sd.cpp `--strength` img2img for FLUX.3 is UNVERIFIED.
- Placing an element: an edit row with `"from":"target","src_bbox":null,"tgt_bbox":[y0,x0,y1,x1]`, or a `"from":"ref_image_1"` row to bring an element in from the second photo. Boxes under about 40×25 px often fail.
- Multi-reference composition: up to 10 refs, addressed as `<ref_image_n>`. BFL's docs example is "the person from image 1 wears the jacket from image 2 and stands in the kitchen from image 3".
- 4K: up to 4096 per side in the reference code and a single reference up to 4 MiB px. The box memory at 4K is UNVERIFIED; klein 9B already failed at 1920×1440 on `--max-vram 20` (pl_05).

**7. Release and ecosystem**

- Release 2026-10-15 (blog; GitHub first commit 45e57c9, 2026-10-15; HF repos created 2026-10-13).
- Diffusers: in `main` only, not in the latest PyPI release 0.41.0 (2026-10-06); `_diffusers_version` `0.41.0.dev0`. Upsampler block PR #15058 merged 2026-10-16; docs PR #15069 merged 2026-10-16.
- GitHub issues on the BFL repo: 1 open (#4 "Language-Conditioned Layout Control", a feature request); 5 merged README and parameter PRs. No bug reports as of 2026-10-17.

### Relevant artifacts

- Cards and configs (no weights): `/private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/a1e05a4f-8b00-4ec2-87b9-1d2d93772abd/scratchpad/dl/`; reference-code clone: `/private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/a1e05a4f-8b00-4ec2-87b9-1d2d93772abd/scratchpad/gh/flux-3-image-klein/`. The upsampler system prompts are in `dl/pup_sys.json` and in the clone's `src/flux3/pup_prompts_external_vlm.json`.
- Box baseline: `.serena/memories/project/strix-halo-box.md` lines 92–102. Klein 9B Q8_0 takes 67.5–68.1 s per keyframe at 1344×768 in 4 steps, with MemAvailable −17.7 to −18.9 GiB.

### Constraints discovered

- 16 steps against 4. The DiT is 5.54B parameters against about 9B. If per-step time scales with parameters, a keyframe on the box would take about 16 × 0.62 × 12 s ≈ 120 s, roughly twice klein 9B [INFERRED, not measured]. The diffusers docs say the distilled model "is trained for 4 to 16 steps"; the MLX card reports 4 steps as "visibly under-denoised".
- The upsampler roughly doubles the stack: 9.5 GB at Q8_0 GGUF, or a separate LLM call. Without it, quality is "noticeably weaker" by BFL's account. A frontier-model API would make a network call; that is acceptable only in the offline keyframe-prep script on the box, never in `transitions.py`. The box already runs llama-swap and llama-server, so the upsampler could be served there [INFERRED].
- Excluded by owner rules: NVFP4 (4-bit), all Q4/Q3/Q2 GGUFs, `w4a8` and INT4-convrot. Allowed: Q8_0, int8-convrot (ComfyUI), fp8r (needs Ada/Hopper/Blackwell; not usable on gfx1151 or MPS), MLX 8-bit, bf16.
- Weights go under `~/keyframes/…` on the box or `benchmarks/runs/<date>/…/hf_home`, never under `models/`.

### Confidence: 75%

High for the file sizes, interface and code facts (read from the HF API and the source). Low for quality and box speed: one vendor Elo source, one third-party test with the upsampler off, and no run on our pairs.

### Gaps

- Gated pages not read: the comfy repo README and `workflows/README.md`, and the distilled repo's `config.json`/`modular_model_index.json` ("requires approval").
- `gh api` searches hung for 300 s and were killed; I used the unauthenticated REST API instead. The ComfyUI releases API returned an error, so ComfyUI#17070 is not verified.
- The BFL bounding-boxes page is 139 KB of mostly JS; I read about 100 KB plus a grep, and saw no worked removal example with `null`.
- Not found: any FLUX.3 vs FLUX.2 klein 4B comparison, diffusers MPS reports, ROCm FLUX.3 reports, and sd.cpp Vulkan reports for FLUX.3.
- Not checked: whether sd.cpp honours flow-map sampling (`ref_time_in`) exactly, and whether it supports `--strength` img2img and box prompts for FLUX.3 (box prompts are plain text, so they probably pass through [INFERRED]).
