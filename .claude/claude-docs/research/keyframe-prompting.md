# Keyframe prompting — what the guides say, what the models actually see, and how the prompts are built (as of 2026-09-27)

Result: the first keyframe run (2026-09-26, DECISIONS Track B) asked Qwen-Image-Edit-2511 for "one
photograph that is exactly halfway between image 1 and image 2" with both photos as references and got
image 2 back (sun centroid 5 px from B's, 4.8 levels from B, 33.1 from A). The guides read on
2026-09-26/27 and the two pipelines' source agree on why: an edit model produces a described target
state from a base picture; "halfway" names no state, and the second reference is the only concrete
one. The next runs use prompts that (a) name the base picture, (b) describe the midpoint STATE layer
by layer in plain sentences, (c) say what stays, and (d) are generated from the layered score at a
clip time by `scripts/research/keyframe_prompt.py` ("dynamic prompts": the same score that drives the
deterministic clip drives the keyframe request). Owner request (2026-09-26, verbatim): "make sure to
check promting guide for flux ( e.g … prompting_editing_single_reference.md and …
prompting_unified_basics.md , also research for yourself , if you are going to use this or any other
models to make most efficient and precise dynamic promts."

## 1. Sources (read 2026-09-26/27; quotes are verbatim, the rest is my reading)

| Source | What it says that matters here |
|---|---|
| BFL, Single-Reference Editing (FLUX.2), https://docs.bfl.ai/guides/prompting_editing_single_reference.md | Specificity over vagueness; state what changes and what stays; direct verbs ("Change", "Replace", "Add", "Remove", "Turn into"); refer to "the image", "this", or an element by location; avoid "Make it better", "Improve the lighting", "Fix the image". Examples: "Change it to Night", "Remove all of the sprinkles while keeping the rest of the image unchanged", "Replace the flower in image 1 with a slice of lemon", "Add small goblins climbing the right wall of the gorge". |
| BFL, Prompting Basics, https://docs.bfl.ai/guides/prompting_unified_basics.md | A starting template "[SUBJECT], [LOCATION], [STYLE], [CAMERA SETTINGS], [LIGHTING], [COLORS], [EFFECT], [ADDITIONAL ELEMENTS]" — "a useful starting structure, not a strict formula"; natural language; iterate one detail at a time; quotation marks for text to render; English is most precise; image input up to 10 images with FLUX.2 and Kontext. |
| BFL, Building a Good Prompt, https://docs.bfl.ml/guides/prompting_unified_building.md | Order matters: subject and its attributes first, then context ("Person with a strong determined expression, forest fire in the background, close-up shot, realistic" beats the reversed order). "Start with a clear subject. Add the main action or state." "Specific detail helps. Filler hurts." "Start short. Add only what changes the image." |
| BFL, Multi-Reference Editing, https://docs.bfl.ai/guides/prompting_editing_multi_reference.md | Refer to references as "image 1", "image 2"; "Describe the role of each image so the model knows what to pull from where"; examples "Place the woman from image 2 on the swing in image 1", "Apply the pattern from image 2 onto the plate in image 1", "Change image 1 to match the style of image 2". FLUX.2 [klein] takes up to 4 references; the API has a 9 MP total input + output budget. |
| BFL, FLUX.2 Image Editing, https://docs.bfl.ml/flux_2/flux2_image_editing.md | Up to 8 references (API) / 10 (Playground); output up to 4 MP; the same "image N" wording ("Create a house for the chickens from image 1 using materials from images 2, 3, 4, and 5"). |
| Qwen, `Qwen/Qwen-Image-Edit-2511` model card, https://huggingface.co/Qwen/Qwen-Image-Edit-2511 | No prompting rules; the code example uses `num_inference_steps` 40, `true_cfg_scale` 4.0, `guidance_scale` 1.0, an empty negative prompt, two input images; Apache-2.0; "notably better consistency" than 2509 (image drift, character consistency, geometric reasoning). |
| Qwen, `prompt_utils.py` (the official edit-prompt rewriter), https://github.com/QwenLM/Qwen-Image/blob/main/src/examples/tools/prompt_utils.py | `polish_edit_prompt()` rules: keep the instruction "direct and specific" and the core intention unchanged; for add / delete / replace "preserve the original intent and only refine the grammar", supplement "minimal but sufficient details" when vague; text in double quotes; for multi-image tasks the rewritten prompt "must clearly point out which image's element is being modified"; add missing position information "based on composition". |
| Qwen, HF discussion "Prompt guide", https://huggingface.co/Qwen/Qwen-Image-Edit-2511/discussions/7 | No official guide; a user (2025-12-27): the model "is a LOT more flexible than all the various guides suggest", natural language works; settings "25-40 steps, cfg 3" for quality. |
| diffusers `QwenImageEditPlusPipeline` source, https://github.com/huggingface/diffusers/blob/main/src/diffusers/pipelines/qwenimage/pipeline_qwenimage_edit_plus.py | The model sees a system message ("Describe the key features of the input image … then explain how the user's text instruction should alter or modify the image …") and each input image labelled `"Picture {}: <\|vision_start\|><\|image_pad\|><\|vision_end\|>"`, concatenated "Picture 1: … Picture 2: …" before the user text; condition images go to the vision tower at a 384×384-pixel area; defaults `num_inference_steps` 50, `true_cfg_scale` 4.0. |
| stable-diffusion.cpp source (`src/conditioning/conditioner.hpp`, `src/model/te/llm.hpp`; read through the GitHub API 2026-09-27) | The same system message; each reference is labelled `"<Picture " + N + ">: "` (angle brackets) and resized for the vision tower between 3,136 and 12,845,056 pixels (`resize_for_vision`, area mode) — a 1920×1092 reference is NOT downscaled; the reference latents are preprocessed at the input size ("preprocess ref[0]: 1920x1092 … output=1920x1092" in `kf_01.log`). CLI: `-r/--ref-image` repeatable, `--increase-ref-index`, `--ref-image-args` (key-value, "empty = auto-detect"), `--image-preprocess target=ref,index=N,mode=…` (crop / crop-resize / fit-pad), `--steps` default 20. |
| stable-diffusion.cpp `docs/qwen_image_edit.md` | 2511 needs `--model-args qwen_image_zero_cond_t=true`; cfg 2.5, euler, flow-shift 3; the example uses one `-r` and a text-change prompt. |
| stable-diffusion.cpp `docs/flux2.md` (via track F §6) | FLUX.2 [klein] 4B: `--cfg-scale 1.0 --steps 4`, Qwen3-4B text encoder, `ae.safetensors`; no `--llm_vision`, no `--flow-shift`, no `--model-args`. |

## 2. Rules for this project's prompts (derived; each traces to a row above)

1. Name the base picture and edit it: "Edit Picture 1." (Qwen sees "Picture N"; FLUX guides use
   "image N"). Never "between image 1 and image 2" as the subject of the sentence — that is what
   returned image 2.
2. Describe the target STATE per element, in the order back to front (sky, then the skyline band,
   then the sun, then the water), each as one plain sentence with a direct verb: "has slid down as one
   solid piece and half of it is already out of the frame", "has moved most of the way from its place
   in Picture 1 to its place in Picture 2 (…)". Position words, not fractions of pixels.
3. Say what stays: "keep everything not mentioned exactly as it is in Picture 1", "the same camera
   and framing as Picture 1", "one continuous photograph, no split screen, no border, no text".
4. When the second photo is supplied, give it a role, not a weight: "Picture 2 shows where the moving
   parts end up." Take specific elements from it ("the stars from Picture 2"), never "blend with".
5. Progress is words, not numbers: "a third", "half", "most", "all"; "still mostly as in Picture 1,
   with a first hint of …", "midway between", "almost as in Picture 2, with a last trace of …".
6. Short beats long: one clause per moving layer, no adjectives that do not change the picture, no
   quality words stacked ("photorealistic" once).
7. Iterate one thing per run (the BFL advice): first the single-reference form, then the two-reference
   form, then a different t; never several changes at once, because a run costs about 32 minutes.

## 3. The generator (`scripts/research/keyframe_prompt.py`)

Input: a layered score (the same JSON that renders the clip), a clip time `--t`, a `--dialect`
(`qwen` → "Picture N", `flux` → "image N"), `--refs 1|2`. Each rendered layer gets one clause from its
action and its progress at `t` through the score's own window and curve (the same `CURVES` as the
tool); a layer's optional `"prompt": {"a", "b", "where", "plural"}` supplies the words (added to the
round-2 scores on 2026-09-27; the probe ignores the key, the render md5 is unchanged:
`b7700b4c…` on mismatch_4). Output: head (which picture is the base and, with two references, the
role of the second) + numbered clauses + the keep-and-format tail. The clip's midpoint prompt is
`--t 0.5`; a keyframe series is `--t 0.25 0.5 0.75` one run each.

## 4. Efficiency on the box (measured 2026-09-26; the recipe `scripts/research/strix_keyframe.sh`)

- One run: 1,804 / 1,941 s at 1344×768 with two 1920×1092 references, 20 steps, 81–103 s per step.
  The references are not downscaled by the CLI: the vision tower takes them at 2 MP each (up to
  12.8 MP allowed) and the reference latents at full size, so the transformer's context carries two
  2-MP pictures for a 1-MP output. The diffusers pipeline feeds the vision tower 384×384-pixel-area
  copies instead. Measured 2026-09-27 (kf_05 against kf_02, §5.1): a reference pre-resized to
  1344×768 gives 46.78 s per step against 46.74 s at 1920×1092, so the reference's pixel count does
  not set the time on this path; the second reference does (82.16 s per step in kf_03, 46.74 s with
  one). The expectation written here on 2026-09-27 morning ("well under 81 s") was wrong.
- Steps: 20 (the CLI default) gave a clean picture; the Qwen card uses 40–50, the community 25–40.
  Keep 20 for the prompt experiments (one variable at a time); raise steps only when a prompt works.
- Single-reference runs halve the reference context and remove the "copy Picture 2" pull; they are
  the first experiment.
- FLUX.2 [klein] 4B at 4 steps and cfg 1 is the speed fallback (about 9 GB of weights, `NEED_GB` 14);
  its multi-reference wording is "image 1 / image 2"; 4 references maximum.

## 5. The next runs (one variable per run; the owner's eye grades; `handover q2`)

| run | references | prompt | what it tests |
|---|---|---|---|
| kf_02 | Picture 1 only (mismatch_4 before) | `keyframe_prompt.py mismatch_4_r2.json --t 0.5 --refs 1` | does a described midpoint state beat "halfway" without the pull of the second picture |
| kf_03 | Picture 1 + Picture 2 | the same at `--refs 2` | does the second picture help the moved elements land where they belong, or pull the whole picture to itself again |
| kf_04 | Picture 1 only (mismatch_6 before) | `mismatch_6_r2.json --t 0.5 --refs 1` | the day-to-night pair, where the sky's state is the whole story |
| kf_05 | the best of the above, references pre-resized to 1344×768 | the same prompt | the time per step; the picture should not change much |
| later | FLUX.2 [klein] 4B, `--dialect flux` | the same prompts | speed and adherence of the fallback |

Screen every keyframe with the Track B numbers before the owner's eye: the sun centroid (mismatch_4),
the mean absolute difference to A and to B (a midpoint should sit far from both; kf_01 sat at 4.8 from
B), the Laplacian variance on the 480-px proxy (188 for kf_01, B 254). A keyframe is a helper element
only if the owner's boxes say so on two mismatched pairs (plan item 4).

### 5.1 Results (2026-09-27; DECISIONS 2026-09-27 fifth session, Track B; page `benchmarks/runs/2026-09-27/keyframes/index.html`)

| run | references | wall s | s per step | sun (keyframe px; B at (673.5, 323.0)) | MAD to A / B (levels) | sha256 |
|---|---|---|---|---|---|---|
| kf_02 | Picture 1 only, 1920×1092 | 1,084 | 46.74 | (679.8, 322.2): 6.4 px from B, 83.0 from the midpoint | 44.80 / 33.66 | `34aebeb9…` |
| kf_03 | Pictures 1 and 2 | 1,847 | 82.16 | 2.8 px from B | 32.80 / 4.26 (Picture 2 reproduced) | `6735a78d…` |
| kf_04 | mismatch_6's Picture 1 only, 1146×1524 → 768×1024 | 710 | 33.25 | no sun | 119.35 / 26.48 | `ac0f696d…` |
| kf_05 | kf_02's prompt, the reference pre-resized to 1344×768 | 1,066 | 46.78 | (684.7, 315.6): 13.4 px from B | 48.14 / 35.60 (6.01 from kf_02) | `789ad836…` |

Read: rule 1 (name the base picture, describe the state) moves the result away from both photos
once the second picture is absent; with both pictures supplied (kf_03) the model returns Picture 2
whatever the wording, so rule 4 (a role for the second picture) did not hold on this model. The
described progress words landed at the END state for the sun ("most of the way" → at B's place);
a midpoint needs the state said as a position ("between the tall buildings and the chimney, a third
of the way down from …"), not as a fraction of a move — the next prompt experiment. Pre-resizing the
reference (kf_05) changed the time per step by 0.04 s and the picture by 6.01 levels: the reference's
pixel count is not what costs time on this path (UNVERIFIED why; the log does not show the latent
size), the second reference is (82.16 s against 46.74 s per step). The Laplacian numbers of §5's
screening list changed definition on 2026-09-27 (`keyframe_screen.py`: kf_01 100.4, A 118.4, B 151.2;
the 2026-09-26 figures 188 / 254 do not compare). By my eye, not evidence: kf_02 invents a water
plume and a bridge, kf_04 keeps A's daylit buildings in place under a night sky. The owner's boxes
decide; no keyframe is graded as of 2026-09-27.

### 5.2 Results of the evening runs (2026-09-27; DECISIONS 2026-09-27 evening, Track B2; page `benchmarks/runs/2026-09-27/keyframes2/index.html`)

The owner on §5.1's keyframes (verbatim): "mismatch_6 (kf_04.png ) looks promising , maybe still too
hard edges , as for mismatch_4 - all keyframes came out either too close to before, or to after,
didn't see true blending, lets continue".

| run | model | the one reference | generate s | MAD to A / B / the reference (levels) | what it tests |
|---|---|---|---|---|---|
| kf_06 | Qwen-Image-Edit-2511 | photo A (mismatch_4) | 1,057 | 35.33 / 39.17 / — | the midpoint said as positions and as a transformation |
| kf_07 | Qwen | the round-3 composite at 0.5 | 969 | 32.52 / 18.30 / 14.87 | the composite as the base, a clean-up prompt |
| kf_08 | Qwen | mismatch_6's round-3 composite at 0.5 | 832 | 108.88 / 27.76 / 10.89 | the same on the day-to-night pair |
| kf_09 | Qwen | photo A (mismatch_6) | 737 | 123.74 / 14.61 / — | kf_04's prompt plus a clause on dusk light and soft edges |
| kf_10, kf_10b | FLUX.2 klein 4B | photo A (mismatch_4) | 38.43 | 67.43 / 78.41 / — | kf_06's prompt through klein; two runs byte-identical |
| kf_11 | klein | kf_07's reference | 38.56 | 48.60 / 34.06 / 32.85 | kf_07 through klein |
| kf_12 | klein | the round-4 composite at 0.5 | 38.83 | 50.53 / 45.65 / 39.22 | the skyline mid-transformation |
| kf_13 | klein | mismatch_6's round-4 composite at 0.62 | 28.97 | 120.92 / 14.26 / 12.11 | a double exposure of buildings and trees |

Read: a prompt on a photo gives a new scene whatever its wording (kf_02 with fractions, kf_06 with
positions: the sun 100.6 px from the midpoint, moved 108 px sideways); the edit model does not move a
large region on request (kf_09's buildings stand where they are in A, by my eye). Given the
deterministic composite as the base, the model keeps the layout (the sun within 1.1 px of the
composite's on kf_07 and kf_11) and changes appearance only: Qwen stays 14.87 levels from the
composite, klein 32.85. So rule 1 of §2 becomes: the base picture is the deterministic composite at
the clip time, and the prompt asks for one coherent photograph with every position kept. klein at 4
steps is 25 × faster than Qwen at 20 (38.6 s against 969 s) and deterministic on the box; it
recolours more. The screening script's sun rule failed on kf_10 (a cloud streak was the largest
bright blob). Next: clean-ups at three clip times (0.25, 0.5, 0.75) of one round-4 clip with klein
and with Qwen, then the deterministic engine between consecutive keyframes; the owner's boxes
decide. Not graded as of 2026-09-27.

### 5.3 FLUX.2 klein 9B at 8-bit (2026-09-27 night; DECISIONS 2026-09-27 night, Track B3)

The owner withdrew FLUX.2 [dev] ("both becauase of size and quants, i don't want degraded Q 4bit
anyways"), asked for klein 9B, and set 8-bit files as the standing precision. The same three clean-up
tasks as kf_11–kf_13, same references, prompts and seed:

| run | reference | generate s (4B) | MAD to the composite (4B) | MAD to its 4B twin |
|---|---|---|---|---|
| kf_14 | the round-3 composite of mismatch_4 | 68.12 (38.56) | 25.07 (32.85) | 17.44 |
| kf_15 | the round-4 composite of mismatch_4 | 67.49 (38.83) | 22.00 (39.22) | 20.37 |
| kf_16, kf_16b | the round-4 composite of mismatch_6 at 0.62 | 49.54 (28.97) | 11.97 (12.11) | 6.06; two runs byte-identical |

Read: 9B costs 1.7 × the time and twice the memory of 4B (−18 GiB against −9 GiB of MemAvailable) and
changes the composite less on the sunset pair; on the night pair the two are 6 levels apart. Qwen
(kf_07: 14.87 from the composite, 969 s) still changes it least. Owner's verdict (2026-09-27 night,
verbatim): "klein 9B looks best (mismatch_6- kf_16.png; mismatch_4 - kf_15.png) use it for next
session". klein 9B at Q8_0 is the keyframe model from here on; the base picture is the round-4
composite and the prompt the clean-up form.

### 5.4 The keyframe-cleaned clip (2026-09-28; DECISIONS 2026-09-28, Track B; page `benchmarks/runs/2026-09-28/keyclip/index.html`)

Result: two 3-second clips A → K1 → K2 → K3 → B exist, and three measured faults stand against them as
rendered. The clips: mismatch_4 at 1344×768 and mismatch_6 at 768×1024, 90 frames, the keyframes at
frames 22, 45 and 67, byte-identical on two renders (mp4 md5 `215afb9f…` and `486fb6e3…`). Ungraded as
of 2026-09-28. Script `scripts/research/keyframe_clip.py`; an Opus 5.5 subagent ran it, and the main
thread re-measured the byte identities, the mean L, the joint steps and the segment classes.

The keyframes are FLUX.2 klein 9B at Q8_0 clean-ups of the round-4 composite at clip times 0.25, 0.5
and 0.75 (seed 20260926, 4 steps, cfg 1.0, one reference; the prompts are verbatim in DECISIONS
2026-09-28 Track B and in `benchmarks/runs/2026-09-28/keyclip/box/prompts/`):

| run | pair, clip time | size | wall s | MemAvailable minimum GiB | MAD to its composite / A / B (levels) |
|---|---|---|---|---|---|
| kf_17 | mismatch_4, 0.25 | 1344×768 | 68 | 18.25 | 39.53 / 40.58 / 53.78 |
| kf_18 | mismatch_4, 0.5 | 1344×768 | 69 | 18.24 | 22.00 / 34.56 / 29.02 |
| kf_19 | mismatch_4, 0.75 | 1344×768 | 68 | 18.25 | 44.62 / 62.73 / 44.41 |
| kf_20, kf_20b | mismatch_6, 0.25 | 768×1024 | 50 | 19.26 | 26.27 / 95.90 / 40.70; two runs byte-identical |
| kf_21 | mismatch_6, 0.5 | 768×1024 | 50 | 19.26 | 11.71 / 114.88 / 21.03 |
| kf_22 | mismatch_6, 0.75 | 768×1024 | 51 | 19.28 | 13.85 / 121.15 / 13.71 |

kf_18 has kf_15's reference bytes and prompt and is byte-identical to kf_15, so the recipe reproduces
across sessions.

The three faults:
1. `transitions.py pair --preset morph`, unchanged, chose class B (the pan-and-zoom) on 1 of 4
   segments of mismatch_4 and on 4 of 4 of mismatch_6 (0 to 11 sparse inliers between two pictures that
   share a layout). Forcing class A falls back to `dis-only` on 3 of 4 segments of mismatch_6.
2. klein raised the brightness of mismatch_4's keyframes. Mean L of the composite against the keyframe:
   19.0 → 36.7 at 0.25, 23.2 → 33.2 at 0.5, 26.0 → 46.5 at 0.75 (A 18.8, B 26.1). The clip's mean L
   runs 18.8, 36.7, 33.2, 46.5, 26.2 at frames 0, 22, 45, 67, 89; `layered_r4` rises from 18.3 to 25.5.
   The sentence "make the light and the colour consistent" does not hold the composite's exposure.
3. The motion stalls at every keyframe: the step between frames is 0.6–1.8 levels at the joints
   against 4.6–6.5 mid-segment, because every segment eases in and out. Each segment's interior is 3 to
   10 times softer than its ends (Laplacian variance).

Not measured: whether kf_22's bright pixels along the bottom (2.14 % of the lowest 30 % of rows above
L 40, against 0.01 % in its composite) are invented buildings; the subagent read them so by eye. Qwen
was not run: the owner chose klein 9B. Next, in this order: hold the exposure (match each keyframe's
Lab statistics to its composite's before the clip is built), one timing curve across the four
segments, and the layered probe's own fields between the keyframes instead of the tool's class
decision.

Owner's verdict on the clips of §5.4 (2026-09-28, verbatim): "I have checked all keyclips , but as you
presented them they are mostly just sequences of crossfades betweeen interrmediate generated frames,
i cant see how final result will look like . If `benchmarks/runs/2026-09-28/keyclip` meant to be
final results, those transitions are just serieses of crossfades , not usable , if you plan to
utilize those intermediate keyframes , lets see." The chain of the tool's morphs between keyframes
is out. The page did not say whether its clips were candidates for a final result or a test of one
step; a review page states that at its head from now on.

### 5.5 Keyframes for the layered probe (2026-09-28; DECISIONS 2026-09-28 evening, Track B2; clips `benchmarks/runs/2026-09-28/keylayer/`)

Result: six klein 9B keyframes, kf_23–kf_28, clean up the round-5 composites at three frames of
each clip around its frame farthest from both photos; every run exited 0 and kf_23b is byte-identical
to kf_23. Inside the layered probe they lower the clip's detail (`TRANSITIONS.md §12.19`). An Opus
5.5 subagent ran them; the prompt bytes were re-checked with `cmp` while this section was drafted.
Ungraded as of 2026-09-28.

Recipe: FLUX.2 klein 9B Q8_0 through `~/keyframes/kf_run4.sh` (unchanged) with `MODEL=klein
MODELS=~/keyframes/models_klein9 KLEIN_DIFFUSION=flux-2-klein-9b-Q8_0.gguf KLEIN_LLM=Qwen3-8B-Q8_0.gguf
NEED_GB=23`, seed 20260926, 4 steps, cfg 1.0, one reference: the round-5 composite frame at canvas
size (1146×1524 for mismatch_6 from `mismatch_6_r5_flow`, 1920×1092 for mismatch_4 from
`mismatch_4_r5_stagger`). Queue `~/keyframes/kf_queue6.sh`, 14:46–14:57 BST on 2026-09-28. The
frames are 15 / 30 / 45 (mismatch_6) and 27 / 42 / 57 (mismatch_4), chosen by the rule in §12.19.

Wall s is `run_begin` → `run_end`, model load included. MemAvailable was 36.2–36.8 GiB before each
run; GTT used rose from 55.2 GB.

| run | reference | size | wall s | sampling s | MemAvailable min GiB | GTT max GB | sha256 |
|---|---|---|---|---|---|---|---|
| kf_23 | `kl_m6_f015.png` | 768×1024 | 77 | 59.99 | 18.61 | 73.55 | `2ae497e010d96ccee851bd3dd91e7982926b8a054e9180835f12bea21915336f` |
| kf_24 | `kl_m6_f030.png` | 768×1024 | 72 | 57.10 | 18.64 | 73.55 | `77b99770ee2b7a3558303b30b65ce5387715e25c5d2f4740f05665c2a4afc54f` |
| kf_25 | `kl_m6_f045.png` | 768×1024 | 74 | 56.36 | 17.90 | 73.55 | `31646c3a57a01de452a61b2af37645eb266672fe0ae986258f2b65e12ee6a6e0` |
| kf_26 | `kl_m4_f027.png` | 1344×768 | 95 | 78.83 | 17.60 | 74.59 | `c1cbf8b986e336fdc2754276bf840d350eeb0d48f0a02c4170fafe02734a0090` |
| kf_27 | `kl_m4_f042.png` | 1344×768 | 90 | 74.92 | 17.57 | 74.59 | `13e7526965426068e89c1b5ffc9c3c8632d9d76ebf2595d3b2600d8bc6c782f4` |
| kf_28 | `kl_m4_f057.png` | 1344×768 | 69 | 56.83 | 17.59 | 74.59 | `d887d1e08ac4c1dd196645392325bc6a949136f5bc821daa677c17abf1890481` |
| kf_23b | `kl_m6_f015.png` | 768×1024 | 50 | 40.72 | 18.96 | 73.55 | `2ae497e0…` (byte-identical to kf_23, `cmp`) |

kf_23b took 50 s against kf_23's 77 s for byte-identical output (median step 9.8 s against 14.2 s);
the cause is not measured. §5.4's 9B runs took 68–69 s at 1344×768 and 50–51 s at 768×1024.

Prompts, verbatim (`keylayer/box/prompts/`). kf_23 and kf_23b use the bytes of kf_20's prompt, kf_26
the bytes of kf_17's (`cmp` equal, checked by the subagent and again while drafting); the others differ
only in the stage words before the first semicolon or full stop. kf_23, kf_23b:

> image 1 is a rough composite of a view seen from a window, caught early in a change from day to night: the sky is darkening and the clouds are fading into it; the row of buildings along the bottom is still a row of buildings. Turn it into one coherent, natural photograph. Keep the shapes along the bottom, the sky and the clouds exactly where they are in image 1. Remove the double exposure, the outlines and the patches. Make the light consistent: dusk turning into night, the shapes along the bottom dimmed against the sky. Photorealistic, one continuous photograph, the same framing as image 1, no split screen, no border, no text.

kf_24:

> image 1 is a rough composite of a view seen from a window, caught midway through a change from day to night: the sky is darkening and the clouds are fading into it; the row of buildings along the bottom is still a row of buildings. Turn it into one coherent, natural photograph. Keep the shapes along the bottom, the sky and the clouds exactly where they are in image 1. Remove the double exposure, the outlines and the patches. Make the light consistent: dusk turning into night, the shapes along the bottom dimmed against the sky. Photorealistic, one continuous photograph, the same framing as image 1, no split screen, no border, no text.

kf_25:

> image 1 is a rough composite of a view seen from a window, caught late in a change from day to night: the sky is almost night and the last of the clouds are fading into it; the row of buildings along the bottom is still a row of buildings. Turn it into one coherent, natural photograph. Keep the shapes along the bottom, the sky and the clouds exactly where they are in image 1. Remove the double exposure, the outlines and the patches. Make the light consistent: dusk turning into night, the shapes along the bottom dimmed against the sky. Photorealistic, one continuous photograph, the same framing as image 1, no split screen, no border, no text.

kf_26:

> image 1 is a rough composite of a sunset over a wide river, caught early in a change from one skyline to another. Turn it into one coherent, natural photograph. Keep the sun, the horizon, the skyline silhouettes and the reflection on the water exactly where they are in image 1. Remove the seams, ghost outlines, double edges, dark discs and patches in the sky and on the water. Make the light and the colour consistent across the sky, the skyline and the water, as one sunset seen by one camera. Photorealistic, one continuous photograph, the same framing as image 1, no split screen, no border, no text.

kf_27:

> image 1 is a rough composite of a sunset over a wide river, caught midway through a change from one skyline to another. Turn it into one coherent, natural photograph. Keep the sun, the horizon, the skyline silhouettes and the reflection on the water exactly where they are in image 1. Remove the seams, ghost outlines, double edges, dark discs and patches in the sky and on the water. Make the light and the colour consistent across the sky, the skyline and the water, as one sunset seen by one camera. Photorealistic, one continuous photograph, the same framing as image 1, no split screen, no border, no text.

kf_28:

> image 1 is a rough composite of a sunset over a wide river, caught late in a change from one skyline to another. Turn it into one coherent, natural photograph. Keep the sun, the horizon, the skyline silhouettes and the reflection on the water exactly where they are in image 1. Remove the seams, ghost outlines, double edges, dark discs and patches in the sky and on the water. Make the light and the colour consistent across the sky, the skyline and the water, as one sunset seen by one camera. Photorealistic, one continuous photograph, the same framing as image 1, no split screen, no border, no text.

Screening (`keyframe_screen.py`, `keylayer/screen/kf_*.json`): MAD in levels, Laplacian variance on
the 480-px proxy.

| keyframe | MAD to A | MAD to B | MAD to reference | Laplacian var (A / B) | sun |
|---|---|---|---|---|---|
| kf_23 | 103.31 | 33.44 | 86.76 | 31.1 (727.6 / 107.6) | – |
| kf_24 | 98.69 | 38.82 | 30.38 | 24.1 | – |
| kf_25 | 74.80 | 64.52 | 53.28 | 165.4 | – |
| kf_26 | 44.00 | 55.70 | 42.41 | 223.0 (118.4 / 151.2) | 23.0 px from A's |
| kf_27 | 36.96 | 28.48 | 24.84 | 152.1 | 25.6 px from the midpoint of A's and B's |
| kf_28 | 58.41 | 41.04 | 40.76 | 249.8 | 13.5 px from B's |

Exposure: mean L of each keyframe against its composite frame, before the Lab match of §12.19. After
the match every keyframe is within 0.11 L of its composite; MAD to the composite falls from
24.5–86.8 levels to 6.9–22.1.

| keyframe | composite frame | composite mean L | keyframe mean L |
|---|---|---|---|
| kf_23 | mismatch_6, 15 | 53.8 | 18.2 |
| kf_24 | mismatch_6, 30 | 32.8 | 20.4 |
| kf_25 | mismatch_6, 45 | 12.2 | 31.3 |
| kf_26 | mismatch_4, 27 | 19.1 | 37.7 |
| kf_27 | mismatch_4, 42 | 23.3 | 34.0 |
| kf_28 | mismatch_4, 57 | 25.9 | 44.7 |

Two prompt findings:
1. The stage words of the kf_20 prompt ("dusk turning into night") do not fit mismatch_6's round-5
   composite at t = 0.17 (frame 15), which is still daylight: kf_23 came out at mean L 18.2 against
   the composite's 53.8. The prompt names a light state; the stage word should follow the composite
   at that frame [INFERRED].
2. The keyframes are made at 0.67–0.70 of the canvas, and the upscale and INTER_AREA round trip alone
   takes kf_26's Laplacian variance from 202.4 to 85.9 at 1344×768. A keyframe made at canvas size is
   not tried; its memory and time on the box are UNVERIFIED.

### 5.6 Generated backgrounds ("plates") for the layered probe (2026-09-29; Track B3; `benchmarks/runs/2026-09-29/plates/`)

Result: klein 9B Q8_0 removed the named objects from all four photos of mismatch_3 and mismatch_2 once the
prompt said what to leave in their place. The layer source counts 28 → 1, 17 → 2, 1 → 0 and 7 → 5 objects
(share ≥ 0.004) inside the objects' zone. A photo's zone is the union of its object-group elements with a
share of at least 0.004, dilated by 12 px. The plate is used only inside that zone. An Opus 5.5 subagent ran
the plates. As of 2026-09-29 they are ungraded.

Recipe: `~/keyframes/kf_run4.sh` unchanged, seed 20260926, 4 steps, cfg 1.0, one reference: the photo at
the probe's canvas (1920×1440 for mismatch_3, 602×800 for mismatch_2). Outputs are 1344×1008 and 608×800.
Wall time is 89–136 s and 34–54 s; MemAvailable was 34.8–36.1 GiB before and 15.60–17.93 GiB at the lowest.
pl_03b is byte-identical to pl_03 (`cmp`).

The prompt form: "Edit Picture 1." first, then one sentence per kind of object to remove, named by what it
is, then "Where they were, show …" naming the surfaces behind them, then the keep-and-format tail: "Keep … and
everything not mentioned exactly as it is in Picture 1. Photorealistic, one continuous photograph, the same
camera, colours and framing as Picture 1, no new people, no new objects, no split screen, no border, no text."

Hand-over prompts, verbatim:

pl_01r (mismatch_3_S):

> Edit Picture 1. Remove every person: the whole crowd standing and sitting behind the wire fence, including the men raising their arms. Remove the three slatted wooden benches and the small table with plates and cups in the foreground, and the bags. Remove the two large dark spoked wheels and the small wheel hanging on the brick wall, the white air conditioning unit and the blue and yellow flag, and put nothing in their place: bare white brick wall. Where the people and the benches were, show the plain grey concrete floor of the courtyard and the lower part of the brick wall with its painted panels, continuing their lines. Keep the chain-link fence, the metal rails, the strings of sequins, the window, the doorway, the painting of hills and everything not mentioned exactly as it is in Picture 1. Photorealistic, one continuous photograph, the same camera, colours and framing as Picture 1, no new people, no new objects, no split screen, no border, no text.

pl_02r (mismatch_3_F):

> Edit Picture 1. Remove every person: the nine men sitting on the sofas and the man leaning forward in the front. Remove the grey woven rope armchairs with green cushions, the low dark tables with the glasses, phones and ashtray, and the towel. Where they were, leave the dark wooden floor bare and show the long sofa with green cushions along the back wall, continuing its lines; put no furniture in their place. Keep the hanging light wooden ceiling rods, the red painting and the blue painting, the loudspeaker, the large window with the pine trees and the building outside, the green floor cushions at the left and everything not mentioned exactly as it is in Picture 1. Photorealistic, one continuous photograph, the same camera, colours and framing as Picture 1, no new people, no new objects, no split screen, no border, no text.

pl_03, pl_03b (mismatch_2_S):

> Edit Picture 1. Remove the man in the yellow suit peeking out from behind the tree. Where he was, show what was behind him: the soft, out-of-focus sunlit park with green foliage and pale sky, continuing its colours and blur. Keep the tree trunk at the left, its bark, the light and everything not mentioned exactly as it is in Picture 1. Photorealistic, one continuous photograph, the same camera and framing as Picture 1, no new people, no new objects, no split screen, no border, no text.

pl_04r (mismatch_2_F):

> Edit Picture 1. Remove every person: the man in the navy T-shirt holding up a phone in the front, the woman in the dark green top behind his hands, the smiling woman with long hair in the black dress, and the person cut off at the right edge. Remove the yellow plant pot and the painted bird at the top right of the mural. Where they were, show what was behind them: the brick wall with its painted mural, the large green leaves of the plants and the seat with pale blue patterned cushions, continuing their lines and patterns. Keep the pale yellow pipes, the window at the top, the dried palm leaves over the mural, the plants and everything not mentioned exactly as it is in Picture 1. Photorealistic, one continuous photograph, the same camera, colours and framing as Picture 1, no new people, no new objects, no split screen, no border, no text.

The first prompts pl_01, pl_02 and pl_04 are verbatim in `benchmarks/runs/2026-09-29/agents/B3_report.md` and
`plates/box/prompts/`. They were written from a channel-swapped view of the photos and name wrong colours.

What worked:
1. A replacement named as a surface: "put nothing in their place: bare white brick wall" and "leave the dark
   wooden floor bare … put no furniture in their place". With these, the wheels, the air conditioner, the flag,
   the armchairs and the tables left without replacements (sheet, by eye).
2. People are removed on all four photos, in a crowd of 24 behind a chain-link fence too; the fence stays.
3. The keep list holds what lies outside the zone in place: the window, the doorway, the paintings, the tree
   trunk. The framing is unchanged.

What did not work:
1. Colour words override the reference. "The hanging blue wooden ceiling" (the ceiling is light wood) gave a
   blue ceiling in pl_02.
2. "Remove X" with only "show what was behind" left room for a replacement in X's place: in pl_01 a yellow
   banner took the flag's place, a painted floor with artificial grass appeared, and the air conditioner stayed.
   In pl_02 sofas and a box table took the armchairs' place.
3. Small painted or held objects stay: in pl_04r the painted bird and the yellow pot were named and kept.
4. klein redraws what it keeps. The mismatch_2_F mural came back with new painted plants. Outside the zone
   the L difference to the photo is 16–21 levels on three plates and 4.7 on mismatch_2_S, so the plate cannot
   replace the photo outside the zone.

Colour: the specified match (Lab, plate + normalized convolution of (photo − plate) over the pixels outside
the zone, sigma 40 px) blurs into the zone the objects outside it that the plate removed, as dark discs on
mismatch_3. A match over the outside pixels that agree within 10 L* has no discs by eye; its seam step is
larger (46.16 against 22.64 L on mismatch_3_S). The layered probe reads the second variant
(`plate_agree.png`; decided on the main thread, `TRANSITIONS.md §12.23.3`).

One run at canvas size (1920×1440) failed in the recipe's `--max-vram 20` budget (5,298 MB needed, 5,274 MB
available); host memory stayed at 15.39 GiB or more.

In the probe (round 7, `TRANSITIONS.md §12.21`): the plate is the fill of a layer's `plate`
(`plate.image`) and is shown where a drawn object has left, on at most 12.4 % of the canvas on
mismatch_3 and 3.6 % on mismatch_2. An object un-premultiplied against the plate was measured and
dropped: the generated background is not the photo's own background at the object's edge, and the
object mattes read 2.0–4.3 on the outline measure against 1.2–2.1 without it.


## 6. Gaps

- No source states what Qwen-Image-Edit-2511 does with an instruction it cannot satisfy from the
  base picture (a state neither picture shows); the runs above measure it.
- Whether stable-diffusion.cpp's `--image-preprocess` for `target=ref` changes the reference latents
  as well as the vision copies is UNVERIFIED (the flag's help text lists the modes; the effect on the
  Qwen path was not read in the source).
- BFL's guides are written for the hosted FLUX.2 endpoints; the open-weights klein 4B through
  stable-diffusion.cpp may follow them less closely (UNVERIFIED).
- The "auto-fit: no GPU devices" warning in the run log is still unexplained; the weights reported
  as VRAM and the step time is what it is.
