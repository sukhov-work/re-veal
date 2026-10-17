<!-- Provenance: written by an Opus 5.5 subagent (the round-11 planner, 2026-10-18 about 02:25) of the Claude Code session of 2026-10-17/18 (the round-10/11 session; DECISIONS 2026-10-18), copied verbatim from benchmarks/runs/2026-10-17/agents/planner_r11.md (sha256 043788f68e0f0778) on the owner's standing order of 2026-10-17; folded into `TRANSITIONS.md §13.19`. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# Planner notes, round 11 (2026-10-18)

I wrote three plans, one concept each: `scripts/research/plans/mismatch_5_r11.json`, `mismatch_3_r11.json` and `mismatch_2_r11.json`. The round-10 plans are untouched. All three files load with `json.load`. Nothing was rendered, so every visual claim below is UNVERIFIED.

The prompt is `scripts/research/plans/PLANNER_PROMPT_2026-10-18_r11.txt`. `shasum -a 256` gives `6406cc1b6e759f9e46bd6c5c5db784ef4f255e09867c36e35f54aa6c494ffb88`, the digest the dispatcher gave, and each plan carries it in `planner.prompt_sha256`. The owner's grades I answer are the verbatim quotes in `TRANSITIONS.md §13.18` (2026-10-17 22:42 UTC). I checked the round-11 field names against `scripts/research/director_render.py` in the working tree: a transform's `depth` is read at the transform level (line 822), `ease` from `params` (line 823), and `hole_reveal`, `face_guide`, `matte_grow`, `damp`, `sky.shape`, `sky.radial_end`, `vacated_first` and `front_per_element` are all read there.

Clip durations below assume a clip of about 3.0 s. I derived that from the prompt's spans: a lead of 0.41 s over 0.22 × 0.62 of the clip gives 3.0 s.

## mismatch_5 (sunset behind a bridge to the Andromeda galaxy)

Kept unchanged from round 10:
- The disc container at (960, 521), radius 110, soft rim, and the three anchors.
- The pull-back with depth parallax on the bridge only (`a_elements` [16, 29]).
- The stars first over [0.08, 0.7] and the slow key over [0.25, 0.92], band 0.35.
- The three beats with their windows: `sun_recedes` [0.15, 0.9], `wire_to_streak` [0.12, 0.7], `bridge_to_arm` [0.2, 0.85].
- The `b_luma_reveal` finish over [0.72, 1.0].

Changed, one schema element per fault:
- "sky around sun ... shrinks in two distinct steps and preserving blurred square shape": `container.params.sky.shape` "radial" with `radial_end` 1.6. I also wrote the other radial fields at their renderer defaults (`radial_width` 0.35, `radial_near_at` 0.25, `radial_end_at` 0.9) so the knob values are visible in the plan.
- "or transform color into galaxy that surrounds core": the colour lead `glow_to_galaxy_colour` is back, A elements [1, 5, 10, 12, 36] toward B element 1 over [0.0, 0.6]. It is a lead under the round-11 rule, so the concept still has three beats.
- "sun itself has some residual concentric bands": on `sun_recedes`, `soften` 0, `limb_flatten` 0.55, `mix_window` [0.55, 0.95] and `mix_ramp` 0.5. Round 10 wrote an early mix [0.0, 0.95] and `limb_flatten` 1.0; both go back to the renderer's round-11 defaults. The plate's feather over half the radius and the vacated ring keep A's glow by renderer rules that have no plan field.

## mismatch_3 (bar crowd behind a fence to a glass-walled lounge)

Kept, from "overall composition, camera movement, fludity and precision with which you put frame A into window pane of B, also intermediate generated r10_m3_pane.png looks nice":
- The glass quad with `reflect` 0.18 and `front_ids` [1].
- The pull-back at gain 0.4 with `gain_A` 0.8.
- The single chain on the whole frame with the one pane keyframe.

Changed:
- "crossfaded into forest in window pane during single frame ( too fast, was expecting people from A to dissolve into forest)": the chain runs over [0.3, 0.92] with `times` [0.4] and `ease` "linear". The wall turns into trees over clip t 0.30–0.55 (about 0.75 s), and the crowd dissolves into the forest over t 0.55–0.92 (about 1.1 s). In round 10 that dissolve showed in about 0.24 s.
- "frame B during movement still overlapped several foreground people": B's front is one layer per element. That is a renderer default with no plan field, so I made it the knob `front_per_element` (default true).
- The end effect moves from [0.85, 1.0] to [0.92, 1.0], so it starts when the chain reaches B instead of cutting into the crowd's dissolve.

## mismatch_2 (man in yellow behind a tree to a café group)

Kept: "intermediate generated static frames r10_m2_k1, k2 and k3 look promising". All three keyframes stay in the order k1, k3, k2. I kept k2 because tonight's test spans include the k3 → k2 → B segments and read as a story. Also kept: his pairing (A element 3 to B element 10), container `none` with parallax off, and the tree's `exit` left over [0.05, 0.45].

Changed, in the order a viewer sees it:
1. The café arrives first, behind the man. The end effect is `b_luma_reveal` over [0.05, 0.5] with `vacated_first` 0, and the tree's `exit` has `hole_reveal` false. This answers "two girls in the background of B are visible through the cut and just stay there": the women arrive with the rest of the café, not through the trunk's outline.
2. The man glides over the café. The chain has `"depth": "front"`, so he composites after the end effect and leaves no footprint. This answers "hard cutting". The lead moves him by his face onto k1's face. It is still a rigid move: 0.41 s at clip t 0.30–0.44.
3. The keyframes inside the grown matte (`matte_grow` 0.03) with `face_guide` true. This answers "very jittery morphs only part of face ( also ugly and distorted )". The spans are the turn to k1 0.33 s (t 0.44–0.55), k1 → k3 0.37 s (t 0.55–0.67), k3 → k2 0.47 s (t 0.67–0.83) and k2 → B 0.28 s (t 0.83–0.92). All five are tonight's test spans unchanged.

The colour lead `bokeh_to_cafe` now ends at 0.5 instead of 0.55, with the café's arrival.

## What I could not express in the schema

- mismatch_2, "really ugly linear 2d move of cut man": the schema has no way to turn or reshape him during the lead. The lead is a rigid similarity, and the turn only starts in the k1 segment. A shorter lead is the only lever, and I did not shorten it beyond tonight's 0.41 s because the prompt asks to keep the spans.
- mismatch_2, "background of A just fades into them": `b_luma_reveal` is still a brightest-first dissolve of the whole background. Making it come behind the man changes where it happens, not what it is. No reveal kind in the schema moves A's bokeh into the café.
- mismatch_3: no keyframe shows the crowd half gone, so the crowd → forest segment is a flow-guided dissolve. He asked for a dissolve ("expecting people from A to dissolve into forest"), so this may be acceptable, but it is not a transformation.
- `front_per_element` is a knob, not a plan field, so the plan answers his mismatch_3 overlap fault only through a knob default.

### Confidence

- Medium on mismatch_5. Each change maps to one of the four radii §13.18 names, plus the radial sky window. Whether the radial window still closes in visible steps is UNVERIFIED.
- Medium-high on mismatch_3. He called it the best result so far, and the plan changes only the chain's timing and the end effect's start.
- Medium-low on mismatch_2. The beat order now matches what he asked for. The keyframe segments are still face-aligned dissolves, and the lead is still a rigid move.

### Gaps

- Nothing was rendered, and no skeptic pass has run on these plans.
- The 3.0 s clip length is derived from the prompt's spans, not read from a render.
- On mismatch_2, if the café is not complete beside the man by t 0.30, A's plate shows next to him during the glide (`end_effect.window` is the knob).
- The grown matte on mismatch_2 (about 18 px at 602 px width) carries the keyframes' café around his shoulders. Where a keyframe's café differs from B's, a halo can show during t 0.44–0.92.
- Knobs whose values are lists or booleans have their `range` written as two lists or two booleans, because the schema's `range` assumes a scalar.
