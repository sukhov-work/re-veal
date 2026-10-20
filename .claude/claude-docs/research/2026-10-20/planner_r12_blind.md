<!-- Provenance: written by an Opus 5.5 subagent (the planner, round 12 blind on mismatch_4, mismatch_6, mismatch_1, 2026-10-20 about 23:55; prompt sha256 e2c7615e…) of the Claude Code session of 2026-10-20 (the round-12 session; DECISIONS 2026-10-20), copied verbatim from benchmarks/runs/2026-10-20/agents/planner_r12_blind.md (sha256 ede3e9214d7c0427) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"); folded into `TRANSITIONS.md §13.21` (the held-out test), the grammar gaps in the backlog. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

<!-- Provenance: written 2026-10-20 by the round-12 blind planner (claude-opus-5-5, a Claude Code subagent), from the brief scripts/research/plans/PLANNER_PROMPT_2026-10-20_r12_blind.txt (sha256 e2c7615e…d4c2). No render was run. The round-12 plans of mismatch_5, mismatch_3 and mismatch_2 existed by the time the plans were written and were read as the worked examples; the _r11 plans were read first. -->

# Round 12 blind plans: mismatch_4, mismatch_6, mismatch_1

I wrote three plans, one concept each. All three stay inside the grammar of `SCHEMA.md` through round 12, and none is rendered yet. Two kinds were missing. The sky block (B's bright points first, then a slow key of A's sky) works only under a disc container, so two skies with no luminary cannot use it. The grammar also has no camera move for a pair with no shared region, so the camera on mismatch_6 is a rectangle container that goes beyond B's frame on every side. The full list is under Gaps.

Plans: `scripts/research/plans/mismatch_4_r12.json`, `mismatch_6_r12.json`, `mismatch_1_r12.json`. Each one has `motion` continuous (edge 0.35, overlap 0.1), the reveal guard on, at most three beats plus a colour lead, a last beat that ends at 1.0, and an end effect over the last 0.14–0.16 of the clip.

## mismatch_4: sunset over water into sunset over water

Reading. A: a white sun high in a red sky over a dark city on the left bank, with the reflection straight down the river. B: a white sun sitting on a chimney above a low port of cranes and pylons, in a golden sky under a dark cloud bank, with a gold reflection.

Idea (3 s). The camera tilts up and draws back a little, so the sun travels from row 225 to row 459. The red sky turns gold (0–1.8 s), the tall city folds down into the port (0.3–2.4 s), and the sun settles onto B's sun by centre and shape (0.75–3.0 s). A's sky closes in a circle around the sun, and the last of A gives way brightest-first (2.6–3.0 s).

Why each beat:
- The camera. I measured both suns. A's bright disc is at (940.9, 224.8) with radius 39.0 px, and B's is at (962.3, 459.3) with radius 33.2 px. The scale 33.2 / 39.0 = 0.85 maps A's waterline (row 545) to about row 731, against B's 736. So one similarity aligns the sun and the horizon, and a disc container with a camera fits the pair without any other alignment.
- The anchor thresholds. These need different values from mismatch_5. A's glow measures about 160 luma, so `circle_fit` needs `min_L` 220; round 11's 120 would fit the glow. B's glow measures 195–211, so `bright_disc` needs `frac` 0.9; at 0.8 it returns a 78 px disc centred 20 rows too high. For the same reason the recede's `blob_frac` is 0.9 instead of the default 0.6.
- `city_folds_into_port` (`morph_to`, dark mass, box map). This is a band onto a band. It delivers B's skyline, chimney included, under the reveal guard.
- `sun_onto_sun` (`recede`, `end_shape: b_blob`). After the camera's scale the two discs are almost the same size, so the recede shrinks the disc very little. Its job is rule 4: land the sun by shape and mix it limb-first. I named no rate, because a sun onto a sun of equal size asks for no fast shrink.
- The reflection columns. The camera already lands A's column on B's: x 931–996 against 905–1020. No beat is needed for them.

What the grammar lacked: nothing blocked the plan. The sky key inside the radial window is still a luma crossfade (rule 7), and the grammar has no other way for one sky to replace another inside a disc container.

## mismatch_6: day city under cumulus into a starry night under an eave

Reading. A: a blue daytime sky of large cumulus over a row of city buildings. B: a night sky of small stars seen looking up, with a roof eave and an air-conditioning unit in the top right corner and tree crowns along the bottom. The two photos share no object.

Idea (3 s). The camera pushes 12 % into A's sky, and B's eave and air-conditioning unit come in over the corner as the front. A darkens toward the night colour (0–1.95 s). The clouds' light flows onto the night sky's light (0.36–2.4 s). The roofline rises into the tree crowns (0.9–3.0 s), and the stars come through brightest-first at the end.

Why each beat:
- The camera. The pair has no luminary and no region of B that can hold A, so a disc or quad container has nothing to land on. I used a `rect` larger than B's frame on every side (box [-69, -107, 1215, 1600], scale 1.12). A covers B to the last frame, so no rectangle edge shows, and the camera still moves at every moment (rule 2). The box puts A's building tops (median row 1173) at row 1207, the median top of B's trees.
- The front (`front_ids` 2, 3). The eave and the unit are B's nearest things (disparity 0.89 and 0.67). This is the one early-B region the plan declares, which is the same exception he accepted on mismatch_3.
- `day_to_night_colour`, the colour lead. It covers all of A, so the buildings take a night tint; he praised that on L4 kf_13.
- `clouds_into_night_sky` (`morph_to`, bright mass). The grammar offers nothing else for clouds turning into stars without a disc container.
- `roofline_into_treeline` (`morph_to`, dark mass). This is a band onto a band; on L4 he said "buildings … transtitoned to tree nicely".

What the grammar lacked:
1. The sky block (`container.params.sky`: stars first by top-hat, then a slow key) is read only when the container is a disc (`director_render.py`, the `if self.cont["kind"] == "disc"` branch near line 1402). Clouds giving way to stars is the case it was built for, but a pair without a luminary cannot reach it.
2. A camera for unrelated pairs. Container `none` fixes the camera at the identity, and a camera tilt or push needs a rect or quad container. The oversized rect works, but it is a workaround: a `camera` kind such as a push or tilt that does not nest A would say the same thing directly.
3. A beat that delivers point targets (stars) from a mass (clouds). `morph_to` is optimal transport of luma mass, and B's luma mass sits mostly in the glow above the trees, not in the stars. The clouds may pool there as blobs, the failure T38 recorded for the crowd morph.

## mismatch_1: blue summer sky over a tower into a stormy sky over a brick city

Reading. A: a blue sky with a diagonal cirrus streak, a long cumulus bank and small clouds, over an office tower with antenna masts. B: a grey-blue sky with horizontal streaks, a sunlit cumulus tower and a grey deck, over a red-brick block, apartment towers and trees that fill the lower 40 % of the frame.

Idea (3 s). The camera tilts down by 359 rows, so A's roofline (row 1499) lands on B's (row 1140), and B's brick block and the trees in front come up from below by depth. The sky turns grey-blue (0–1.8 s). The streak turns and lies down into B's streaks (0.15–1.8 s). The cumulus bank gathers into the sunlit tower and the deck (0.45–2.55 s). The office tower spreads into the city behind the brick block (0.9–3.0 s).

Why each beat:
- The camera. It is a `rect` at scale 1 (box [0, -359, 1444, 1561]), a pure tilt. No similarity aligns both rooflines and also keeps A over the whole frame: that would need scale 1.85 or more. So the tilt opens a band of B below A's frame, and the front (`front_ids` 19, 33, 51, 54, 56, 62, 63: the brick block, the near trees and the wall) covers most of that band.
- `streak_lies_down` (`morph_to` with `rotate`). A thin streak onto thin streaks, the same direction as the wire into the satellite streak on mismatch_5.
- `cumulus_gathers` (`morph_to`, bright mass, `rate` fast_out). The fast_out rate is my guess that a cloud builds late; nothing in the pair demands it.
- `tower_into_city` (`morph_to`, box map). A band onto a band. Its target is B's city behind the brick block, so the block stays a front layer and is not a morph target.

What the grammar lacked:
1. A per-region early-B declaration. Rule 1's exception covers the container's surround and the named front as a whole. Between columns 959 and 1206 the surround below A's frame shows B's low buildings 39, 44 and 45, which are also the tower beat's guarded target. The plan cannot say which rule wins there.
2. A container edge that feathers by content. A `rect` with a `matte` rim has a straight edge wherever B's front does not cover it. A soft rim exists only for the disc.

## Confidence: 55 %

The geometry is measured on the canvases: the two suns, the scale 0.85, the waterline at 731 against 736, the box arithmetic and the element ids against `layers.json`. Every visual claim about the clips is UNVERIFIED, because nothing was rendered. mismatch_4 is the plan I trust most, because it reuses the luminary machinery from the pair he graded "best result so far". mismatch_6 is the one I trust least: its central beat, clouds into stars by optimal transport, has no precedent he graded well.

## Gaps

- The renderer reads `rect` boxes outside the canvas (it builds the similarity from the box corners, `director_render.py` near line 637). I did not check whether B's front push (`parallax_push` 2.5) behaves under an oversized rect.
- `colour` with `a: {"kind": "all"}` (mismatch_6) is accepted by `mask_A` ("all" returns the whole frame); no earlier plan used it for a colour transform.
- The sky key on mismatch_4 runs over A's water as well as A's sky, because the radial window keys everything that is not a lifted layer. Whether water giving way to water reads as a crossfade is UNVERIFIED.
- Mattes faults that touch these plans: mismatch_4_S bridge 17, which I left out of every layer; mismatch_1_F block 19, whose mask carries a strip of distant city that rides with the front; mismatch_1_F clouds 11 and 12, which split one cloud; and mismatch_1_S tower masts, which are lost from the matte.
- Missing kinds, as findings for the grammar: (1) the sky block outside a disc container; (2) a non-nesting camera (push, tilt, pan) for container `none`; (3) a mass-to-points beat (clouds into stars); (4) a per-region early-B declaration; (5) a soft, content-keyed edge for `rect` and `quad` containers.
