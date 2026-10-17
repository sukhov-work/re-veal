<!-- Provenance: written 2026-10-17 by an Opus 5.5 subagent (the planner, evening) of the Claude Code session of that day (the round-8/9 session; DECISIONS 2026-10-17), copied verbatim from benchmarks/runs/2026-10-17/agents/planner_r8.md (sha256 6d036256a27d12aa) on the owner's order; folded into `TRANSITIONS.md §13.11`. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# Planner notes, round 8 Track P (2026-10-17)

I wrote three plan files under `scripts/research/plans/`: `mismatch_5.json` and `mismatch_3.json` from the owner's notes of 2026-09-27 and 2026-10-17, and `mismatch_2.json` blind (the photos, the element table and `SCHEMA.md` only). Each file has two concepts. Every `by` value is one of the six that `SCHEMA.md` lists. No plan has been rendered, so every visual claim below is UNVERIFIED until `director_render.py` runs.

The prompt is saved verbatim in `scripts/research/plans/PLANNER_PROMPT_2026-10-17.txt` (7301 bytes, no trailing newline). Its sha256 is `a715f8eda5822bc162a6e4aba6fd9c4f58c3115155c1cdd2c441c2b07d600e05`. I pasted the text from the message I received; whether those bytes match the dispatcher's original exactly is UNVERIFIED (possible differences: trailing newline, Unicode dashes or the ≥ and − signs).

I placed coordinates by drawing a 100 px grid on the actual canvases (`transitions.common_canvas(A, B, 1920, "finish")` plus `transitions.cover`). The canvases are 1920x1080 for mismatch_5, 1920x1440 for mismatch_3 and 602x800 for mismatch_2, which matches `elements.json`. The proxies in the blind folder are the uncropped photos, not the canvas, so I did not read coordinates off them.

## mismatch_5 (sunset behind a bridge to the Andromeda galaxy)

Rank 1 (c1): the sun falls away into the core, and the bridge becomes the galaxy's arm. A disc container sits at the measured core centre (960, 521) with radius 110. That radius is the glow's half-maximum, so the sun is centred exactly; the owner wrote on 2026-10-17 that it was "a bit off center". `end_scale` 0.4 brings the sun's 275 px radius down to 110 px. A `recede` then shrinks it to 25 px (the L≥200 core) and softens its limb, which answers his notes "still too large at the end" and "harsh transitions and borders around edges of sun".

The bridge layers answer "nothing happens to the bridge":
- The deck (element 16) goes to the satellite streak by `line_to`, width 3. The geometry already fits: the deck lies 0.62 sun radii below the sun's centre, and the streak lies 0.55 glow radii below the core. Only the −19° turn is new motion.
- The truss (element 29) goes to the dust lane by `morph_to` with dark mass.
- The bright mass of the reflection column goes to the star-rich lower-right arm by `morph_to`. This is the closest the schema gets to his "stars were popping".

The camera uses depth parallax at gain 0.35, because he wrote "missing Z depth/parallax".

Rank 2 (c2): a deeper pull-back (`end_scale` 0.1) makes the sun core-sized by the camera alone, while the bridge layers stay full width. The bridge then grows into the arm as everything else shrinks. I ranked it second because the detached bridge floats over the star field while A's frame is tiny, which risks F2.

## mismatch_3 (bar crowd behind a fence to a glass-walled lounge)

Rank 1 (c1): the bar crowd stands outside the lounge's glass wall, behind the seated men, and then steps in. On 2026-10-17 the owner wrote "picture A remains a static tranformed photo with hard edges, poorly aligned". My reading is that mapping A's 4:3 frame onto the exact pane squeezes it to about 0.6 of its aspect and leaves all four edges visible.

The c1 quad keeps the glass's measured perspective: the top and bottom edges converge with a height ratio of 1.73. I scaled the quad about 1.5x about the glass midline. A then keeps 85% of its aspect, and each edge of A lies behind a B occluder: the dark wall on the left, the ceiling above, and the wall and sofas below. A's crowd lands with heads near y 490, about 200 px above B's seated heads. With the glass rim (`reflect` 0.18) and depth parallax at gain 0.4, the two groups sit at different depths instead of side by side.

The finish answers "thematically detached" and "simply crossfades out":
- The wheels go to the pine trunks (`morph_to`, dark mass).
- The flag moves out of the glass onto the blue painting (`move_to`).
- The brick wall takes the window's colours (`colour`).
- The crowd comes forward through the glass onto the men (`morph_to`, bright mass, map box).
- An `edge_reveal` closes the clip.

Rank 2 (c2): the exact pane, read as a reflection (`reflect` 0.35), with the wheels-to-trunks link and a `luma_reveal`. It is the safer variant. I ranked it second because it keeps the squeezed framing the owner already graded.

## mismatch_2 (blind: a man peeking from behind a tree to a café group)

Rank 1 (c1): the peeking man takes over the peeking woman's place. A rect container keeps A's 602:800 aspect. A's eye midpoint (285, 128) lands on the woman's eye midpoint (270, 455), and the ratio of eye spacings (40 px to 90 px) gives `end_scale` 0.45. At that scale A's clasped hands land at about (268, 604), on the open palm in front of her (element 19, centre (260, 560)). With the matte rim, B's man at the left (disparity 0.51) and the raised hand (0.59) cover the man from A the way his tree did.

Three transforms support the landing:
- The bokeh takes the cream wall's colour, to hide the container's top and right edges, which no occluder covers.
- The jacket darkens toward her green cardigan.
- The jacket's yellow pours into the yellow planter beside the container (`morph_to`).

An `edge_reveal` then replaces him with her from the rim inward.

Rank 2 (c2): the meme shrinks onto the phone the man holds up. I read the quad on a 3x zoom of B: (321, 282), (358, 296), (348, 460), (315, 450). I ranked it second because the phone shows its back, so "the meme on the phone" is a story B does not show (F3). It also squeezes A from 3:4 to about 1:4.

## Blind plans (benchmarks/runs/2026-10-17/agents/blind_plans.md): kept and dropped

Kept:
- Pair 1, sun to core, deck to streak, truss to dust lane, glints to stars: all of these are in mismatch_5 c1. I used the measured core centre (960, 521), not the blind planner's (955, 515).
- Pair 2, flag to blue painting and wheels to trunks: I moved both into the window concept.
- Pair 3, "the peek is passed on" (A's face to the peeking woman, A's hands on B's hand, yellow to the planter): this became mismatch_2 c1, rebuilt as one camera on a rect container with a matte rim instead of free-floating moves. Pair 3's phone concept became c2.

Dropped:
- Pair 1 concept 2 (a swirl into a spiral): the schema has no swirl or log-polar kind.
- Pair 2 concept 1 (everyone sits down, no container): the owner asked for the window zoom.
- Pair 2 concept 2 (a push into the mural, then a pull-back out of the window): the schema has one pull-back camera, so a push-in followed by a pull-back is impossible. It also needed an upscale helper, and helpers are null this round.
- MLS warps, the lamp posts collapsing to stars, the trunk-to-man morph in pair 3 c1, and every helper keyframe: the schema has no `mls` kind, and helpers are off.

## What the schema could not express

- Stars appearing in B's own brightness order. `luma_reveal` orders by A's brightness and acts only inside the container, so "stars popping" can only be approximated by moving glint mass onto stars.
- A camera that pushes in before it pulls back (pair 2 concept 2 of the blind plans).
- Point-to-point warps (MLS, landmarks). Hands, faces and limbs can only ride rigidly (`move_to`, `hold`) or move by optimal transport (`morph_to`).
- Rotation and swirl fields, apart from the single rotation inside `line_to`.
- Where `params` live for the container and the camera. The schema names `params.end_scale` and `params.reflect` but gives `container` and `pullback` no `params` field. I wrote `pullback.params.end_scale` and `container.params.reflect`; the renderer must read them there or the plans need moving.
- The anchor object's format. The schema names the kinds but not the key that carries the kind, so I wrote `{"kind": "...", ...}` on every anchor, transform side and end effect. A knob that is not a schema parameter (mismatch_3 c1's quad scale) is described in words; it changes the quad points by hand.
- Whether a transformed layer may leave the container. mismatch_3 c1's flag-to-painting move crosses from the glass to the wall; if the renderer clips layers to the container, that transform will fail.
- A quad corner outside the canvas. mismatch_3 c1 has a corner at y −152; `SCHEMA.md` does not say whether that is allowed.

### Confidence

- Medium-high for the mismatch_5 geometry. The core centre, the 110 and 25 px radii and the streak points come from today's measurements and my grid reading. The match between the deck's and the streak's offsets is arithmetic on those numbers.
- Medium for mismatch_3 c1. The quad corners are computed from the measured glass edges. That B's occluders hide all four of A's edges is reasoned from the element table's disparities ([INFERRED]), not rendered.
- Medium for mismatch_2 c1. I read the eye positions by eye on a 3x zoom, at about ±5 px. Whether the edge reveal looks like a sweep or like a face crossfade is UNVERIFIED.

### Gaps

- Nothing was rendered, and no frame of any concept has been seen.
- The sha256 is computed over my pasted copy of the prompt; that it matches the original bytes is UNVERIFIED.
- The `kind` key on anchors and the `params` on container and pullback are my extensions to the schema's undefined object format. They must be checked against `director_render.py`'s parser when it exists.
- The galaxy disk box, the lower-right arm box [1000, 560, 1900, 1000] and the blue painting box [200, 261, 528, 642] come from grid reading, not from a detector.
- I did not look up the owner's words on mismatch_2, as the prompt required.
