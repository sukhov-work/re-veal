<!-- Provenance: written 2026-10-17 by an Opus 5.5 subagent (the planner, late evening) of the Claude Code session of that day (the round-8/9 session; DECISIONS 2026-10-17), copied verbatim from benchmarks/runs/2026-10-17/agents/planner_r9.md (sha256 e1ebb20181067c5c) on the owner's order; folded into `TRANSITIONS.md §13.14`. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# Planner notes, round 9 (2026-10-17)

I wrote three plans, one concept each: `scripts/research/plans/mismatch_5_r9.json`, `mismatch_3_r9.json` and `mismatch_2_r9.json`. The round-8 plans are untouched. All three files load with `json.load`. None has been rendered, and the renderer does not yet parse the round-9 kinds (`b_luma_reveal`, `container.params.sky`, `dark_line`, `exit`, `gain_A`, `rotate`; a grep of `scripts/research/director_render.py` at 1098 lines finds none of them). Every visual claim below is therefore UNVERIFIED.

The prompt is saved in `scripts/research/plans/PLANNER_PROMPT_2026-10-17_r9.txt` (5482 bytes, no trailing newline). Its sha256 is `e1b01825cb9825291a78bbdc740c91f414afbbacf84659bc4824c8623b942fcf`. I pasted the text from the message I received, so whether those bytes match the dispatcher's original is UNVERIFIED. The likely differences are a trailing newline and the Unicode characters (→, −, –, ×, …).

The owner's grades I answer are in `.claude/claude-docs/benchmarks/2026-10-17-director.md`, section "Owner picks on the director's page" (18:48 UTC).

## mismatch_5 (sunset behind a bridge to the Andromeda galaxy)

Kept unchanged from round 8 c1:
- The disc container at (960, 521), radius 110, soft rim.
- The circle-fit anchor on the sun.
- `end_scale` 0.4 and depth parallax at gain 0.35.
- The sun's `recede` to 25 px with `soften` 0.6.
- The truss's morph to the dust lane, now named `bridge_to_arm`.

Changed, one schema element per named fault:
- "galaxy appears too quickly and simply ( iris wipe ) i would expect here brightest stars to appear first and then nice gradual luma cross fade": I added a sky block, `container.params.sky`. Stars come through over [0.08, 0.7], and A's sky gives way to B's background over [0.25, 0.92] with `key_band` 0.35. Round 8's key used band 0.10 over the first 45 % of the clip. The sky's `colour` transform now runs early, over [0.0, 0.5] instead of [0.0, 0.8], so it leads the key.
- "hard halo and luma borders around sun when transitioning into galazy": the finish is now `b_luma_reveal` over [0.72, 1.0] with band 0.45. B's core is its brightest region, so the core replaces the receded sun first and the glow follows outward, where the old `luma_reveal` kept the sun's bright disc for last. The early colour path also darkens A's sky before the key crosses it. If the halo is still hard after this, the knob to raise is `soften` (range 0.6–1.0).
- "would be cool if barely visible thin powerline which goes above the bridge transformed into that diagonal streak across galaxy": `wire_to_streak` is a `line_to` from `dark_line` rows [140, 185] to the round-8 streak line. It uses round 8's deck window start (0.12) and ends at 0.70. The deck (element 16) joins the truss (29) in one a-mask, `[16, 29]`, so the whole bridge becomes the arm.
- The glints-to-stars morph is dropped. The sky block now brings the stars, and the story rule allows at most three transforms.

I measured the wire on the centred crop (`transitions.cover`, 1920×1080) by taking the per-strip median luma minus a 25-row running mean. It sits at row 149 at x 0–160, row 165 at x 960–1120 and row 175 at x 1760–1919, 4 to 16 levels darker than its surround. The wire falls 26 px across the frame and crosses the sun disc between x 800 and 1190. The prompt says rows 140–160; my band [140, 185] covers the measured right end too.

The order in `idea` is: the sky darkens, the stars appear, the wire swings into the streak, the sun recedes, the bridge folds into the arm, the slow sky crossfade runs, and the core finishes.

## mismatch_3 (bar crowd behind a fence to a glass-walled lounge)

Kept from the round-8 c1 the owner graded "Like this one, almost acceptable". That clip is the rendered one: the operator had skipped the flag and the crowd moves and set `a_elements=[3]`.
- The glass quad `[[585,145],[1919,-152],[1919,925],[585,767]]`, with `reflect` 0.18.
- The pull-back with B's foreground entering over A.
- The wheels (A element 3) morphing to trunks 7 and 8 over [0.4, 0.8].
- The flag and crowd moves stay out. c1-full had them, and he called it "transformations for the sake of transformations, no continuity , no story , no sense".

Changed:
- "at last moment frame A cheaply dissolves into background of frame B, i would expect it to subtly tranform into trees etc": the finish is now `b_luma_reveal` over [0.55, 1.0] with band 0.5. It replaces round 8's luma reveal over the last 20 %. B's sky and lit pines arrive first and A's dark parts leave last.
- "it remains 2d plane till the end": I set `gain_A` 0.8 against the shared gain of 0.4, so A's crowd moves against its brick wall during the pull-back.
- The brick's `colour` target is now tree 10, the largest foliage mass (mean Lab 67, −6.6, 26), instead of the whole window element 3. The colour window moves from [0.3, 0.9] to [0.2, 0.7], so the wall is already green before the finish is halfway.

The concept has two transforms (brick colour, wheels morph) plus the finish.

## mismatch_2 (man in yellow behind a tree to a café group)

Both round-8 concepts are dropped; the owner called them "really weird" and said the phone "makes zero sense". This plan is his concept: "yellow man to rotate and gradually transform into closest to camera person from frame B and the tree from frame A go away".
- Container `none` (the camera is the identity) with parallax off. With no pull-back, the morph is the clip's motion.
- Beat 1, `tree_goes_away`: tree 1 (disparity 0.90, the nearest element of A) uses `exit` left with `fade` 0.3 over [0.05, 0.45]. It has no B target (`b: null`).
- Beat 2, `man_becomes_nearest_person`: person 3 morphs to person 10 (box [0, 268, 432, 799]) over [0.15, 0.85] with `map` box, `rotate` true, bright mass and `ot_weight` 0.5. The two mask axes are 10.8° and 24.6° from vertical. I did not check that both angles use the same sign, so the turn is about 14° and UNVERIFIED.
- Beat 3, `bokeh_to_cafe`: A's bokeh and background elements 2, 4, 5, 6 and 7 take the colours of B's cream wall (2) and monstera (3) over [0.0, 0.55].
- The finish is `b_luma_reveal` over [0.65, 1.0] with band 0.4. The wall and faces come first and the dark clothes last, so the morphed man is the last part of A to go.

One number differs from the prompt. The element table gives person 10 a median disparity of 0.51, while the prompt says 0.61.

## The three-transform rule on mismatch_5

mismatch_5 has four transform entries. The prompt asks for at most three transforms and also asks for an early colour path next to the recede, the wire `line_to` and the bridge morph, which makes four. I kept the colour as `sky_colour_leads` and wrote in its note that it leads the sky beat and adds no layer motion, so the owner sees three motion beats. If the renderer or the dispatcher enforces three entries, set `sky_colour_leads.skip=true`. The cost is that the sky key then crosses an undarkened red sky, which is the source of the luma borders he named.

### Confidence

- Medium-high for the mismatch_5 wire rows: I measured them on the centred canvas. How `dark_line` rows map into the anchored crop is the renderer's convention. I assumed it adds `shiftA` the way `rows` does.
- Medium for the mismatch_3 changes. They are parameter changes on a clip he liked, so the camera and quad are known to work. That `gain_A` 0.8 does not tear the crowd's outline is [INFERRED].
- Low-medium for mismatch_2. The concept is the owner's own, but person 10's mask is only 1.23 times longer than wide, so the axis the `rotate` uses is weak. A morph from a 0.49-area mask to a 0.31-area mask with no camera move has never been rendered.

### Gaps

- The renderer does not parse any round-9 kind yet, and nothing was rendered.
- Round 8's operator knobs on mismatch_5 are not in the plan because they are not schema fields: `parallax_sources=["A"]`, truss `feather=6` and `mix_window=[0.15,0.85]`, and deck `stretch=2.6`. I wrote `rotate: true` for the bridge in place of the operator's `map=axis`. The operator should re-apply the rest to reproduce the bridge he liked.
- `dark_line` is horizontal and 7 rows thick, while the wire falls 26 px across the frame, so the band can miss the wire's ends. The wire is also part of the sun disc between x 800 and 1190, where the recede layer and the `line_to` band would both carry it.
- On mismatch_3, the third anchor (brick to tree 10) only documents the colour pair. On mismatch_2, `container.spec` is `{}` and `rim` "soft" fill required keys of a `none` container; the renderer should ignore both.
- The sha256 covers my pasted copy of the prompt; byte equality with the dispatcher's text is UNVERIFIED.
