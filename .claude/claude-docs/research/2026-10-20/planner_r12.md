<!-- Provenance: written by an Opus 5.5 subagent (the planner, round 12, 2026-10-20 about 23:45; prompt sha256 eb8589e7…) of the Claude Code session of 2026-10-20 (the round-12 session; DECISIONS 2026-10-20), copied verbatim from benchmarks/runs/2026-10-20/agents/planner_r12.md (sha256 cb0dbfcedcb2bba9) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"); folded into `TRANSITIONS.md §13.21`. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# Planner notes, round 12 (2026-10-20)

I wrote three plans with one concept each: `scripts/research/plans/mismatch_5_r12.json`, `mismatch_3_r12.json` and `mismatch_2_r12.json`. I did not edit the round-11 plans. All three files load with `json.load`. Nothing was rendered, so every visual claim below is UNVERIFIED.

The prompt is `scripts/research/plans/PLANNER_PROMPT_2026-10-20_r12.txt`. `shasum -a 256` gives `eb8589e753208ebdf48201beb84fccc10efbb221a826ff7a3c05b8d252b8d4d3`, and each plan carries it in `planner.prompt_sha256`. The owner's words I answer are his grades of 2026-10-20 19:28 UTC (`director_r11/director_picks_11.json`). Rule numbers refer to `benchmarks/runs/2026-10-20/agents/retrospective.md` section 4.

All three concepts carry `"motion": {"kind": "continuous", "edge": 0.35, "overlap": 0.1}` and `"reveal": {"guard": true}`. No transform writes `"ease"`. I checked the field names against `scripts/research/director_render.py` in the working tree. Clip times assume 90 frames at 30 fps (3.0 s), the length measured in each round-11 `info.json`. Times "about t x" come from the renderer's own `trapezoid01` and `rate_profile` functions, which I evaluated in Python. They are computed, not seen.

## mismatch_5 (sunset behind a bridge to the Andromeda galaxy)

Kept from round 11, which he called "best result so far": the disc container, the camera, the radial sky window, the colour lead, the wire's and the bridge's windows, and the end effect over [0.72, 1.0].

The core is now measured, not typed. The first anchor's `b` and the recede's `b` are `bright_disc` over the box [860, 421, 1060, 621] at frac 0.8. On B's 1920 x 1080 canvas this measures centre (960.0, 520.6) and radius 28.2 px. That is 0.4 px from round 11's point, so the camera does not move.

Changed against his words:
1. "whole sun to rapidly shrink at the very small core" (rule 11). The recede has `profile` "geometric", `rate` "fast_in" and `edge` 0.2, a sharper start than the concept's 0.35. With an end scale of about 0.16 (my estimate from the blob's size), the disc keeps 0.72 of its radius at t 0.30, 0.32 at t 0.50 and 0.24 at t 0.60.
2. "do not align (perfectly ) neither by the centers nor by shapes" (rule 4). `end_shape` is "b_blob" with `blob_frac` 0.85. I measured B's blob at 1920 px for each value. At 0.7 it is the 68 x 56 px gas, matching the prompt's 34 x 28 at 960 px. At 0.8 it is 31 x 26 px (area 2499 px, an equivalent radius of 28 px, larger than round 11's end radius of 25). At 0.85 it is 19 x 16 px (area 945 px, an equivalent radius of 17 px). At 0.9 it is 10 x 8 px. I chose 0.85 because its blob is smaller than round 11's end radius of 25 px, while the 0.9 blob (10 x 8 px) is close to a single point.
3. "it should shrink and dissolve into that dense gas". `mix_window` is on the beat's progress after the rate, so `fast_in` would have moved round 11's [0.55, 0.95] earlier in clip time. [0.65, 0.98] places the dissolve at about t 0.51–0.82, after most of the shrink. The recede's window now ends at 1.0, so the last beat ends at the last frame.
4. "sun limb still is not fully uniform" (rule 5). `limb_flatten` is 0.4 and `rim_in` 0.5. Both values are a guess, as the prompt says.
5. "elements ( especially bridge move a bit discretely" (rule 2). Every beat takes the trapezoid. The bridge also gets `edge` 0.5, one smooth hump, because he named it.

`reveal_ahead` true is written out on the recede (it is also the default). The ring the sun vacates shows the core's glow, because a fill of a luminary's footprint is a dark ring (T46). The guard holds back B's streak and dust lane until their beats deliver them.

## mismatch_3 (bar crowd behind a fence to a glass-walled lounge)

He accepted round 11 "tentatively", so the round-12 plan is the round-11 plan with the `motion` and `reveal` keys added. The quad, the chain, the end effect, the front and the knobs are unchanged.

I made one change the prompt did not list. I removed `params.ease` "linear" from the chain, because the prompt forbids writing it on any transform. The renderer also reads a written ease before the trapezoid (line 876), so keeping it would have turned the motion model off for the only beat, and the page could not show what the motion model changes. I appended one sentence to the chain's note saying so. Under the trapezoid the pane keyframe is reached at about t 0.57 instead of 0.55. The chain has no `b`, so the guard has nothing to hold here.

The accepted clip used the operator knobs `cont_feather=14`, `front_margin=0.3` and `parallax_push=1.5`. Those are not plan fields. The round-12 render should repeat them, or the page compares two things at once.

His one fault, "minor clipping of plane B over some people in frame A ( while B gets into position)" (rule 10), is not answered by this plan. The prompt asked for no other change.

## mismatch_2 (man in yellow behind a tree to a café group)

Kept: "direction and steps look close to what i wanted". The pairing (A element 3 to B element 10), no camera, the tree's exit to the left, the café arriving behind the man by `b_luma_reveal`, the chain as a front layer with the face guide and `matte_grow` 0.03, and the colour lead.

Changed, one per caveat:
1. "When starting to move man in frame A you reveal man in B (because of tear in frame A" (rule 1). The concept's guard holds A's base inside B's man's matte, grown by 1 % of the width, until the chain's lead lands (the default `arrive`). The tree keeps `hole_reveal` false, the round-11 plan's value. The round-11 page clip had the operator's `hole_reveal=true`, which is the likely source of his tear frame (my inference from the knob list in TRANSITIONS.md §13.19, not checked on the clip).
2. "several transitions happen very discretely ... with weird pauses and in very linear way" (rule 2). The chain runs from t 0.10 to 1.0 under the trapezoid. The tree's exit is moved to [0.03, 0.40] and the café to [0.03, 0.50], so both overlap the glide. The clip's last beat ends at 1.0, where round 11 held 7 still frames.
3. "transform shape, transform face and finalize rest of image" as separate steps (rule 6). I dropped k2, so there is one dissolve fewer and the face and the shirt change together in the last segment (k3 to B).
4. `times` is "arc", so the glide and the face steps run at one visual speed. With round 11's measured segment displacements (lead 283 px, lead to k1 31 px, k1 to k3 72.2 px) and k3 to B assumed below the floor, the knots are 0.60, 0.73 and 0.88. In clip time the lead lands at about t 0.61 (1.8 s), k1 at about 0.68, k3 at about 0.78, and B at 1.0.

These faults remain by construction. The glide is a rigid move of A's man (rule 3, T45). The segments between faces are face-aligned dissolves (rules 6 and 7, T40). The café still arrives as a brightest-first dissolve of the bokeh (rule 7).

Arc times make one fault worse. The rigid glide now takes about 0.60 of the chain, about 1.5 s against round 11's 0.41 s, so the cut-out move he named is longer. The knob `arc_floor` 0.5 cuts it to about 0.40 of the chain.

## What the schema still cannot express

- A body that deforms while it moves (rule 3). Nothing in the schema bends or turns the man during the glide, and the recede only scales the sun.
- An in-between between two faces (rule 6). Keyframe segments are dissolves. Only a new keyframe could add an in-between, and the prompt allows none.
- The guard's region. It is the `b` element's matte grown by a fixed band. B's man's raised hand, the woman in green behind it, or a ceiling element cannot be named as extra guarded targets.
- An arc time with a cap on the rigid lead's share. Only `arc_floor` acts on it, and only indirectly.
- The operator knobs of the accepted mismatch_3 clip. They live on the command line, not in the plan.
- Plan knobs whose values are lists or booleans still write `range` as two lists or two booleans.

### Confidence

- mismatch_3, high that the plan matches the accepted one plus the two keys. Whether the trapezoid on a single dissolve beat looks better or worse to him is UNVERIFIED.
- mismatch_5, medium. The blob, the rate and the dissolve timing rest on my measurements and computed curves. The limb values are a guess.
- mismatch_2, medium-low. The tear and the end hold are answered. The rigid glide and the dissolves remain, and arc times make the glide about 3.7 times longer.

### Gaps

- Nothing was rendered, and no skeptic has read these plans.
- The k3-to-B displacement is assumed to be under the arc floor (k3 to k2 measured 1.4 px and k2 to B 0.3 px in round 11). If it is larger, the knots move.
- The end scale of about 0.16 for the sun is estimated from the blob's area, not read from `info.json`.
- The guard on mismatch_5 holds A's base inside the streak's line and the dust-lane band until those beats arrive. The sky key may leave a band-shaped edge of A's sky there (rule 5).
- On mismatch_2, A's inpainted plate shows inside B's man's matte until the lead lands, wherever neither man covers it (t 0.3–0.6).
