<!-- Provenance: written by an Opus 5.5 subagent (the round-10 planner, 2026-10-18) of the Claude Code session of 2026-10-17/18 (the round-10 session; DECISIONS 2026-10-18), copied verbatim from benchmarks/runs/2026-10-17/agents/planner_r10.md (sha256 8c9f5b3c8ac71ef9) on the owner's standing order of 2026-10-17; folded into `TRANSITIONS.md §13.17`, DECISIONS 2026-10-18. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# Planner notes, round 10 (2026-10-18)

I wrote three plans, one concept each: `scripts/research/plans/mismatch_5_r10.json`, `mismatch_3_r10.json` and `mismatch_2_r10.json`. The round-9 plans are untouched. All three files load with `json.load`. Nothing was rendered, so every visual claim below is UNVERIFIED.

The prompt is `scripts/research/plans/PLANNER_PROMPT_2026-10-18_r10.txt`. I hashed that file with `shasum -a 256` and got `512dc0e2c55cdf569b749d98d7c98cfbb26d4b319ca7c498f8c654c0713472ef`, the digest the dispatcher gave. Each plan carries it in `planner.prompt_sha256`.

The owner's grades I answer are the verbatim quotes in `TRANSITIONS.md §13.15` (2026-10-17 19:42 UTC). I checked the round-10 kinds against `scripts/research/director_render.py` as it stands in the working tree: `keyframe_chain`, `front_ids`, `a_elements`, `vacated_first`, `mix_window`, `mix_ramp`, `limb_flatten` and `end_taper` are all read there. Soft mattes exist under `benchmarks/runs/2026-10-17/mattes/` for every element the plans name: A 16 and 29 on mismatch_5, B 1 on mismatch_3, A 1 and 3 and B 10 on mismatch_2.

## mismatch_5 (sunset behind a bridge to the Andromeda galaxy)

Kept unchanged from round 9:
- The disc container at (960, 521), radius 110, soft rim.
- The sky block: stars over [0.08, 0.7], the key over [0.25, 0.92] with band 0.35.
- The three anchors.
- The sun's `recede` to 25 px over [0.15, 0.9].
- The wire's `line_to` over [0.12, 0.7].
- The bridge's `morph_to` over [0.2, 0.85].
- The `b_luma_reveal` finish over [0.72, 1.0].

Changed, one schema element per fault in "still some hard edges around sun and bridge":
- The sun's rim (his frame shows a bright ring and a dark gap). `sun_recedes` now sets `mix_window` [0.0, 0.95], `mix_ramp` 0.6 and `limb_flatten` 1.0. I wrote all three explicitly because the code defaults (`mix_window` [0.55, 0.95], `mix_ramp` 0.5, at line 1233) differ from the values `SCHEMA.md` gives ([0.0, 0.95], 0.6).
- The bridge (the deck as a hard bar with a grey band, and the vertical bands above the lamp posts). I set `pullback.parallax.a_elements` to [16, 29], so the sky is not remapped. The soft mattes for 16 and 29 apply without a plan field.
- The wire (a tilted bar in his frame). The round-10 `dark_line` alpha is the wire's own darkness. I wrote `end_taper` 0 on `wire_to_streak` so the intent is visible.
- I dropped `sky_colour_leads` to meet the three-transform rule. Round 9 kept it as a fourth entry. The cost is that the slow key now crosses an undarkened red sky; `risk` names it and `key_band` is the knob for it.

## mismatch_3 (bar crowd behind a fence to a glass-walled lounge)

Kept: the glass quad `[[585,145],[1919,-152],[1919,925],[585,767]]` with `reflect` 0.18, the pull-back with B's foreground entering, and depth parallax at gain 0.4 with `gain_A` 0.8.

Changed:
- "obscures part of the ceiling of B which should have been in foreground": `container.spec.front_ids` [1].
- "wheels on the wal of A tranform into sky , weird": the `wheels_to_trunks` morph is dropped. The `brick_to_foliage` colour is dropped too, because the chain covers the whole frame and the keyframe already replaces the brick. No crowd morph is planned.
- "still crossfades , just less obviously": one `keyframe_chain` named `pane_becomes_view`, with `a` {"kind": "all"}, `b` null, `frame` "A" and the single keyframe `r10_m3_pane.png`. It runs over [0.3, 0.85] with `times` [0.55], so the keyframe is reached at clip t 0.60. The finish is `b_luma_reveal` over [0.85, 1.0] with band 0.4.

The prompt says "with two pane keyframes `times` lists two values". Only one pane keyframe passed the screen (`r10_m3_pane2` failed on the cream flowers), so the chain has two segments and `times` has one value. A whole-frame chain has no rigid lead segment (`lead` is false when `whole`, line 1044).

## mismatch_2 (man in yellow behind a tree to a café group)

Kept: his concept, the container `none` with parallax off, `tree_goes_away` (`exit` left, fade 0.3, [0.05, 0.45]) and `bokeh_to_cafe` (colour, [0.0, 0.55]).

Changed:
- "rough cutout of man from A is just moved and then hard crossfaded onto man from B": the `morph_to` becomes `man_becomes_nearest_man`, a `keyframe_chain` from A element 3 to B element 10 with `frame` "canvas". The keyframes are k1, k3, k2 in the order the prompt gives. With three keyframes and the renderer's rigid lead, the chain has five segments, and `times` [0.25, 0.42, 0.6, 0.86] marks when the moved picture, k1, k3 and k2 are reached.
  - The window [0.22, 0.92] puts the rigid glide at clip t 0.22–0.40.
  - The identity change from k1 to k2 (chain 0.42–0.86, clip t 0.51–0.82) is the longest span.
- "rest of frame A is just left with hard cut silhuette revealing B underneath": the soft mattes and A's plate apply without a field. I moved the end effect to [0.45, 1.0] with `vacated_first` 0.35, so the fill in the footprints is replaced early. The chain's note gives my estimate: the fill shows from about t 0.25, is widest at t 0.40, and is gone after about half a second (UNVERIFIED).

## What I could not express in the schema, and one possible renderer fault

- `vacated_first` looks inverted in the code. At line 1470 the renderer computes `of = of - vac * v_last`, and B replaces A where `of + ef*(1+band) - 1 > 0`, so a high order value comes first. Subtracting therefore delays the vacated footprints instead of bringing them first. The prompt reports that tonight's test renders showed the footprints going first, so either I misread the code or the test did not isolate the effect. If the sign is wrong, the fill on mismatch_2 shows for well over half a second. I did not edit the renderer.
- On mismatch_2, the end effect covers the whole frame, the man's region included. No field limits a reveal to the background. B's face, at mid luma, should arrive around t 0.65–0.7, while the chain is between k3 and k2. That is a partial crossfade of the face, and `risk` names it.
- On mismatch_5, the early colour lead cannot be kept inside three transforms, and there is no container field for it.
- On mismatch_3, no keyframe shows the crowd leaving, so the chain's second segment carries the crowd into B's lower view by flow and a linear mix.

### Confidence

- Medium-high on mismatch_5. Every change is a parameter on a concept he graded close, and each answers a defect he showed in his frame. Whether the red sky leaves a border without the colour lead is UNVERIFIED.
- Medium on mismatch_3. The first segment (A to the pane keyframe) has a real in-between. The second segment (keyframe to B) dissolves the crowd, which may read as the "people and furniture" noise he named.
- Medium-low on mismatch_2. The keyframes are screened, but no full chain has been rendered at these times. The timing of the vacated footprints depends on the sign question above.

### Gaps

- Nothing was rendered, and the skeptic pass has not run.
- The sign of `vacated_first` at `director_render.py:1470` should be checked before the mismatch_2 render.
- The knobs `parallax_A_elements` and `front_ids` take lists. I wrote their `range` as the default list twice, because the schema's `range` assumes a scalar.
- The pane keyframe's two named changes (one closed hand, one pair of sunglasses) stay in the clip during t 0.45–0.75. The page must show the keyframe and say that it is generated.
