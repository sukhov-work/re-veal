<!-- Provenance: written 2026-10-17 by an Opus 5.5 subagent (Track D, evening) of the Claude Code session of that day (the round-8/9 session; DECISIONS 2026-10-17), copied verbatim from benchmarks/runs/2026-10-17/agents/flux3_run.md (sha256 be4385492b20f325) on the owner's order; folded into `TRANSITIONS.md §13.12`, DECISIONS 2026-10-17 fourth line. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# FLUX.3 image klein on the Strix Halo box: first run (round 8, Track D, 2026-10-17)

## Findings: flux3_run

FLUX.3 image klein (distilled, bf16) runs on the box through stable-diffusion.cpp's Vulkan image of 2026-10-17, and two runs with the same seed gave byte-identical PNGs. On the fabra boxes pair at 1024×1280 it took 312 s for the plate and 351 s for the keyframe, against 89 s for each with FLUX.2 klein 9B Q8_0. The time per step is about the same (18.5 s against 18.2 s); FLUX.3 needs 16 steps where klein 9B needs 4. The base model (bf16, 20 steps, cfg 3.5) took 923 s and 781 s. One fix was needed: the comfy repo's text encoder keeps Hugging Face tensor names that stable-diffusion.cpp f0aac52 rejects, so I wrote a copy with renamed tensors (the tensor bytes are unchanged). No klein 9B plate or keyframe of the fabra pair existed before today, so both models were run today with the same prompts, reference and size. The hold file on the box is removed (`ls: cannot access '/home/yevhen/halo-hold'`, 19:14:55 BST).

### Key facts (each with its log line or command output)

1. **Weights, all sha256 equal to the Hugging Face LFS sha256** (`sha256sum` on the box against `/api/models/black-forest-labs/flux-3-image-klein-comfy?blobs=true`):
   - `flux3-image-klein-bf16.safetensors` 11,097,404,512 B, `c3e9813c…0bd7c`. This file is the same as the distilled repo's root `model.safetensors`, which has the same sha256.
   - `flux3-image-klein-base-bf16.safetensors` 11,076,957,072 B, `5c921759…61b19c`.
   - `qwen3vl_4b_bf16.safetensors` 8,875,719,408 B, `f0b24fc5…9630f`.
   - `flux2-vae.safetensors` 336,211,292 B, `868fe7b3…ce8f3`.
   - The box's older VAE files could not be reused: `models_klein9` and `models_klein` hold `flux-2-klein-4b-vae.safetensors` at 168,120,878 B, and no file there is 336,211,292 B.
2. **Transfer speeds** (epoch stamps in the scratchpad logs `dl_start`/`dl_end`, `rs.log`):
   - Mac download of the distilled set (20.31 GB): 385 s, 52.7 MB/s. Base (11.08 GB): 234 s, 47 MB/s.
   - rsync Mac to box over Tailscale: VAE plus encoder 8.88 GB in 403 s, 22 MB/s. The two transformers ran in parallel by my mistake (see Gaps): 11.10 GB in 746 s and 11.08 GB in 717 s, about 15 MB/s each and 30 MB/s together.
3. **Container**: `ghcr.io/leejet/stable-diffusion.cpp@sha256:2ad8a48a1b1cbc207541e788a40f393c7cc1fecfc6be96387fbf0a211c2f5323`. This is tag `master-vulkan`, the only Vulkan tag; the registry lists five tags in total. Image id `sha256:2c97b20a62f3b4835dd312eb9248a2a6873d3f0faf3a8ad52c18287963d8c4aa`, 564 MB, label `org.opencontainers.image.revision f0aac524d3f2…` (= release master-973), created 2026-10-17T06:15Z. The pull took `pull_s=341`; the 2026-09-26 pull took 13 s. The old image `0ab8e0e0…` stays on the box for `MODEL=qwen|klein`.
4. **Flags** (`docs/flux3.md` at f0aac52): distilled `--cfg-scale 1.0 --steps 16 --sampling-method euler`, base `--cfg-scale 3.5 --steps 20`. `--llm` takes Qwen3-VL 4B and there is no `--llm_vision`. Up to 10 references via `-r`. "The default discrete scheduler uses the upstream time shift of 6.93 for both models. Use `--flow-shift` to override it." `docs/edit.md` gives FLUX.3 the `flux2` reference preset. I left `--flow-shift` unset (6.93) and used `--flash-attn off,diffusion=on` (the help text: "--diffusion-fa deprecated; use --flash-attn off,diffusion=on").
5. **Encoder name failure and fix**. First smoke run: `[E] Conditioner model tensor 'text_encoders.llm.model.embed_tokens.weight' not in model metadata`, then `new_sd_ctx_t failed`, `run_rc=1`. The file names its tensors `model.language_model.*`. At f0aac52 and on master as of 2026-10-17, `src/name_conversion.cpp` maps that prefix only for LLaDA (lines 778–781). The `Comfy-Org/Krea-2` encoder that the doc links has the same 713 names, so the doc's safetensors route should fail the same way [INFERRED from the header; not run]. `scripts/st_rename.py` rewrote the header (`renamed 398 of 713`) into `qwen3vl_4b_bf16_lm.safetensors` (8,875,713,440 B); every later run used it. The vision tensors keep their names, and no warning about them appears in the log.
6. **Smoke test, text to image, 512×512, seed 20260926**: `fx_smoke1` took 56 s wall, `sampling completed, taking 47.13s`, median step 2.54 s (first 9.42 s). `fx_smoke2` took 50 s, 42.89 s, 2.46 s. Both PNGs have sha256 `5f3f355d34472a8fe769e5b44f28affe573fbf29cc8384fbf1a0803b35287b6c` (`cmp`: identical). Log line: `total params memory size = 18416.35MB (VRAM 18416.35MB, RAM 0.00MB): text_encoders 7672.62MB(VRAM), diffusion_model 10583.29MB(VRAM), vae 160.43MB(VRAM)`. MemAvailable went 47.66 → min 30.46 → 47.65 GiB and GTT used 59.18 → max 76.46 → 59.18 GB. Image-to-image with one reference (`fx_i2i`, photo 1 at 512×640, "paint the left box bright blue") finished in 105 s, median step 5.78 s.
7. **Side by side, fabra_17, 1024×1280, one reference, seed 20260926** (`stats.json`, `measures.json`). "Outside" means outside the box zone (two hand-drawn rectangles, 17.8 % of the frame). "Changed >8" is the share of outside pixels whose largest channel difference is above 8 levels. The plate is measured against photo 1; the keyframe against its reference composite. Laplacian variance is taken on a 480-px grey proxy; photo 1 reads 1384.3 and the composite 882.5.

| run | wall s | median step s | MemAvailable min GiB | GTT max GB | MAD all / outside | changed >8 outside % | Laplacian var |
|---|---|---|---|---|---|---|---|
| plate, klein 9B Q8_0 | 89 | 18.24 (4 steps) | 66.22 (from 83.90) | 52.56 (from 34.30) | 23.10 / 14.18 | 63.12 | 728.3 |
| plate, FLUX.3 distilled | 312 | 18.51 (16) | 27.38 (from 47.16) | 79.76 (from 59.18) | 22.05 / 14.15 | 73.21 | 580.7 |
| plate, FLUX.3 base | 923 | 44.82 (20) | 24.89 (from 47.92) | 79.75 | 20.99 / 12.80 | 63.13 | 533.5 |
| keyframe, klein 9B Q8_0 | 89 | 18.27 (4) | 65.76 (from 84.01) | 52.56 | 25.83 / 17.99 | 81.98 | 782.4 |
| keyframe, FLUX.3 distilled | 351 | 20.74 (16) | 28.31 (from 47.78) | 79.49 | 17.32 / 15.14 | 79.58 | 702.5 |
| keyframe, FLUX.3 base | 781 | 36.59 (20) | 25.41 (from 45.02) | 79.49 | 15.84 / 10.72 | 58.17 | 785.7 |

   - Against photo 1 the keyframes read MAD 26.08 (klein 9B), 20.24 (FLUX.3 distilled) and 18.03 (base).
   - Every run logged `run_rc=0`, and the 10 GiB watchdog never fired.
   - The klein 9B runs began with 84 GiB available because the resident models had been unloaded at that moment. Their memory rise was 17.7–18.3 GiB, the same as on 2026-09-27.
   - The FLUX.3 rise was 17.2–23.0 GiB of MemAvailable and 17.3–20.6 GB of GTT.
8. **The repo recipe** (`scripts/research/strix_keyframe.sh`, now sha256 `d4cfd0ee285e209a…`, equal to `~/keyframes/strix_keyframe_flux3.sh` on the box) gains `MODEL=flux3` with its own image pinned in `IMG_FLUX3`. A script comparison found the qwen block (856 B), the klein block (691 B) and the qwen/klein manifest heredoc (981 B) byte-identical to before. Three lines changed in place: the `MODEL` comment, the `case` line, and `else` → `elif [ "$MODEL" = klein ]; then`. `bash -n` passes. Not committed.

### Relevant artifacts

- Mac, gitignored: `/Users/yevhens/Projects/personal/reveal-1.5.0/benchmarks/runs/2026-10-17/flux3/`.
  - `index.html` is the review page; its top line says it shows helper candidates, not transition candidates.
  - `out/` holds the 9 PNGs and their manifests, `log/` the run and memory logs, `in/` the references and the zone mask, `stats.json` and `measures.json` the numbers.
  - `scripts/` holds the recipe copy, `fx_run.sh`, the two queue scripts, `st_rename.py`, `runstats.py`, `measure.py`, `gen_page.py` and the prompts.
- Mac, tracked: `/Users/yevhens/Projects/personal/reveal-1.5.0/scripts/research/strix_keyframe.sh` (modified, uncommitted).
- Mac scratchpad: the weights (31 GB) under `/private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/a1e05a4f-8b00-4ec2-87b9-1d2d93772abd/scratchpad/flux3/`.
- Box, under `~/keyframes` (82 GB after this run):
  - `models_flux3/`: the four files plus `qwen3vl_4b_bf16_lm.safetensors`.
  - Scripts: `strix_keyframe_flux3.sh`, `fx_run.sh`, `fb_queue_klein.sh`, `fb_queue_flux3.sh`, `st_rename.py`.
  - Data: `in/fb_{A,kc50}_1024x1280.png`, `prompts/{fx_smoke,fx_i2i,fb_pl,fb_kf}.txt`, `out/{fx_*,fb_kl_*,fb_fx_*,fb_fxb_*}`, and `log/` with the same names.
  - The new Docker image `2c97b20a62f3` is the second host-side residue after the 2026-09-26 one.

### Constraints discovered

- The comfy encoder needs the name rewrite on stable-diffusion.cpp f0aac52 (fact 5). The alternative is `Qwen/Qwen3-VL-4B-Instruct-GGUF` F16 (8,051,286,144 B), which the docs' GGUF route names; not tried.
- At 1024×1280, a FLUX.3 distilled image costs 3.5–3.9 times a klein 9B image on this box, and the base model 8.8–10.4 times. The planning figure is about 5–6 min per distilled image and 13–15 min per base image.
- The bf16 set needs 26 GB in the pre-flight (file bytes + 6). The MemAvailable minimum was 24.89 GiB with 45–48 GiB free at the start. On a day with 35 GiB free beside the resident models, the minimum would be about 12–15 GiB [INFERRED from the measured 17–23 GiB rise].
- stable-diffusion.cpp still uses time shift 6.93; BFL's reference code moved to 16.0 on 2026-10-17 (the earlier report). I did not run `--flow-shift 16`.
- No prompt upsampler was used. BFL says results without it are "noticeably weaker", so these FLUX.3 images are a lower bound on what the model can do.

### Confidence: 80%

The timings, memory, hashes and determinism come from finished runs and their log lines. The image measures are single runs on one pair with one seed, and both models changed 58–82 % of the pixels outside the box zone by more than 8 levels. Those numbers mostly reflect a whole-frame tone shift and should not be read as a ranking. The owner grades the images.

### Gaps

- Tool failures:
  - openrsync on the Mac rejects `--info=progress2` ("unrecognized option"), so the first transfer failed and I re-ran it without the flag.
  - The comfy encoder failed the metadata check (fact 5).
  - My `while [ ! -f rs_end ]` gate found a stale `rs_end` from that failed rsync, so the base-model rsync started while the distilled rsync was still running. Both finished with rc=0 and sha256 equal to Hugging Face's; the per-file speeds in fact 2 are shared-link speeds.
  - Two `until` waits hit the 600 s tool limit and moved to the background. The runs themselves were not affected.
- The brief asked me to re-run the klein 9B plate and keyframe prompts of 2026-10-09. None exist: `~/keyframes/prompts` and `out` hold no fabra file (newest 2026-09-29), and `benchmarks/runs/2026-10-09/fabra/` holds no klein output. I wrote both prompts today in the style of `pl_03.txt` and `kf_23.txt` and ran klein 9B on them through the unchanged `kf_run4.sh`.
- `tr14/out/fabra_17/mask.jpg` is a grey picture, not a binary mask (44.7 % above 127), and a colour-difference mask covered 61.6 %. The zone is therefore two hand-drawn rectangles.
- Not run: `--flow-shift 16`, a second reference, sizes above 1024×1280, a determinism repeat at 1024×1280, and the prompt upsampler.
- The resident `llama-server` processes have start times of 18:00:45 and 18:12:01 BST, inside my session. No generation job was running at either time: the klein queue ran 18:06:38–18:10:16 and the first FLUX.3 container started at 18:24. A model swap by `llama-swap` is the likely cause [INFERRED; not checked in its log].
- `journalctl -k` since 17:50 printed no OOM or fence line through my filter. Whether the user can read the kernel journal is not verified.
- Nothing was written to `DECISIONS.md`, the memory leaf or the handover; that is left to the main thread.
