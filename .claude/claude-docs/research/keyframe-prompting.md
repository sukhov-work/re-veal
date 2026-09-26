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
  copies instead. Next run, UNVERIFIED until measured: pre-resize the reference PNGs to the output
  size (1344×768) before upload, or pass `--image-preprocess target=ref,mode=fit-pad,…` — expect a
  per-step time well under 81 s; compare the log's "preprocess ref" lines and the step time.
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
