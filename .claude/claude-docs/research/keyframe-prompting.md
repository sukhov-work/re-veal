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
