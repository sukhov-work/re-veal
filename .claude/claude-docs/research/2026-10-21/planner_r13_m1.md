<!-- Provenance: written by an Opus 5.5 subagent (the round-13 planner for mismatch_1, prompt sha256 1ddc5725…) of the Claude Code session of 2026-10-21 (the round-13 session; DECISIONS 2026-10-21), copied verbatim from benchmarks/runs/2026-10-21/agents/planner_r13_m1.md (sha256 048ba29c978dbf0a) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

<!-- Provenance: written 2026-10-21 by the round-13 planner for mismatch_1 (claude-opus-5-5, a Claude Code subagent), from the brief scripts/research/plans/PLANNER_PROMPT_2026-10-21_r13_m1.txt (sha256 1ddc5725619f06201be143f041d4c3ff3e2c22d1b421a94c721789a4a15540b6). Plan: scripts/research/plans/mismatch_1_r13.json (sha256 ae72f2fd465924167e8fa0a83529b02b3f5b9bb66b114df504d49538002deddf). Draft: benchmarks/runs/2026-10-21/planner_m1/draft (480 px, concept c1). Probes beside it: probe_a, probe_b, probe_ot0.3, probe_ot0.15, probe_ids. No tracked file other than the plan was edited. -->

# mismatch_1, round 13: a zoom-out into B's sky

Concept c1 resolves at 480 px: `unplaced` is empty, step_first is 0.35 and step_last 0.03 levels, b_inside_first is frame 69 (t 0.78, inside the end effect), motion_pauses is 2 (frames 79–80), and motion_jumps is 0. All numbers come from `benchmarks/runs/2026-10-21/planner_m1/draft/info.json`. In c1 the camera pulls back from A filling the frame until A is the left half of B, standing on the brick block's roof. Inside A's frame, A's cumulus re-forms into B's sky. Then A's tower gives way to B's city. Concept c2 exists. It is a keyframe request with `"keyframes": []`, and it renders only once that file exists.

## What changed from the blind plan, and why

1. The camera. The blind plan tilted at scale 1: a rect of the frame's size moved down 359 rows. c1 is a zoom-out: a rect of A's aspect at scale 0.5, `[0, 337, 722, 1297]`, with start zoom 2.0 about the fixed point (0, 674), computed as 337 / (1 − 0.5); info.json reads `start_zoom` 2.0 and `zoom_centre` (0, 168) at 480 px. This answers "this whole transition should have been a rapid zoom out, current direction doesn't work as skylines and focal lenghts too different". I no longer align the two skylines. A's median city top lands 53.5 rows above B's (row 1086.5 against 1140).
2. The cloud beat's target is the sky part of the container, the box `[0, 337, 722, 1136]`. It is no longer a list of B's cloud elements. Rule 1: the reveal guard now holds every pixel of B inside the container's sky until the beat delivers it, so no hole shows B partway through. This answers "clip into B inthe middle of transition". The box has no inner edge, so B's clouds 11 and 12 are not split. B's clouds 4, 6, 7 and 8 lie wholly inside it and 11 lies 91 % inside (element maps against the box).
3. The colour lead covers the cloud footprints as well as A's sky ids, and the cloud mix starts with the beat (`mix_window` [0.0, 0.9], `mix` "edge", rim first). In draft 1 the mix used the default window [0.25, 0.9] and the colour lead covered the sky ids only. That draft showed A's thin streak 5 as a dark blue band (frame 36) and a dark blue halo around the lower cumulus (frames 24–45). The cause is that the morph layer carries A's own pixels, which the colour lead never re-colours. This answers "not leave ugly contours" (rule 5).
4. The cloud set is `[2, 3, 6, 10, 12, 13, 14, 18, 27, 28, 35, 37]`. Through the camera, its union box `[0, 0, 1444, 1633]` maps to `[0, 337, 722, 1153.5]`, against the target's `[0, 337, 722, 1136]`, so the box map is nearly the identity. Draft 2 used `[6, 10, 12, 13, 14, 18]` instead, and its box map shifted B's content by about 100 rows: an inner rectangle edge was visible at frames 39–63. I checked this on probe_ids. The streak 5 stays in A's base.
5. `ot_weight` is 0.3. The optimal-transport field reads mean 50.9 px and max 124.9 px at 360 px wide (info.json `layers[].ot`). Probes at 0.6, 0.3 and 0.15 looked alike on frames 33–63, and the lowest weight that still moves the bank is the safest against edges.
6. A `hold` on A's tower and roofs (24, 32, 34, 44) is listed after the morph, so the cloud beat's growing matte does not cover the tower's top, which lies inside the sky box between rows 1009 and 1136. Nothing else of A transforms: the streak and the rest of A ride the camera and give way to the end effect, `b_luma_reveal` over [0.76, 1.0] (band 0.4). The blind plan's window was [0.86, 1.0]; skeptic_r12 measured that window switching most of the container to B in 3 frames (81–83), and the wider window answers rule 7.
7. Parallax is off. With a flat zoom, A's bottom edge stays on the block's roofline in every frame (rule 5). With depth parallax the near block moves against the container. No `front_ids` are set, because nothing of B needs to stand before A: B's only default front element, the wall 63, lies outside the rect, and `front_share` is 0.0066.

The beats are the pull-back (0–3.0 s), the clouds (0.18–3.0 s; B's clouds arrive inside the moving matte from 0.18 s and are delivered by 2.4 s, when the guard releases at t 0.79), and the end effect (2.3–3.0 s). The colour lead runs 0–1.8 s and is not a beat. No transform carries `"ease": "linear"`.

## Measured geometry (layer-source canvas, 1444 × 1920)

- B's brick block roof: row 1297, the median over x 100–718 (step 4) of the largest rise of Lab a* in rows 1240–1360 (p10 1262, p90 1323), measured with cv2 on `fixtures/mismatch_1_F.jpg` resized to the canvas. The rect's bottom edge sits on this roof.
- Rect scale 0.5 (722 × 960). The left edge is B's left edge, so the lit cumulus 7 (box x 0–632) and cloud 8 (x 607–720) lie inside it. Boxes are from `layers.npz` `element`.
- A's bank 6: its luma-weighted centroid (762.5, 786.5) lands at (381.3, 730.2) in B. B's cumulus 6+7 centroid is (278.8, 801.5). The camera alone brings the bank within 125 px of B's cumulus.
- A's tower matte top: row 1345 (element 24, min over columns 220–1440), which lands at B row 1009.5.
- B's luma inside the target box: sky holds 39 % of the luma mass (cloud luma-mass share 0.612), with sky median luma 0.639 and cloud median 0.706. OT onto this box therefore spreads A's cloud light over B's sky as well as B's clouds. This is why `ot_weight` is low.

## Draft numbers (c1, 480 px, 90 frames, 9.0 s wall)

step_first 0.35 · step_second 0.07 · step_last 0.03 · step_max 7.51 · motion_median_px 2.52 (peak 3.5 at frame 44) · motion_pauses 2 (frames 79–80, the end effect while the camera settles) · motion_jumps 0 · b_inside_first 69 (b_inside 0.0133 at 69, 0.42 at 75, 0.92 at 78) · guard_share_max 0.1486 · residual_edge_max 0.00307 (frame 3) · plate_A_share 0.3711 · matte_fallbacks none. The renderer printed no INFO lines.

What the frames show (my reading of draft frames 6–84 at 360 × 480; UNVERIFIED at 1920 px):
- The zoom-out reads as one camera move, with A ending on B's block roof.
- The container's top and right edges are visible as thin straight lines from about frame 18 to frame 75.
- At frames 39–48, A's bank and B's lit cumulus overlap as two clouds, a dissolve inside the beat.
- At frame 39 a small dark drip hangs under the bank.
- At frame 75 the tower ghosts during the end effect.

## What the schema cannot express for a zoom-out

1. A rate for the camera. `pullback.ease` accepts only "smootherstep" (any other value is a linear `u`, `director_render.py` render loop), and the camera always spans the whole clip. "Rapid" therefore has no plan field. The zoom is geometric in e (`Camera.zoom`), and smootherstep is the fastest ease the schema names that does not cut frame 1.
2. A soft edge for a rect. The renderer has a feather (`container.params.feather_px`, `director_render.py` near line 653), but SCHEMA.md does not name it, so c1 cannot use it.
3. A command-line knob for a rect's end size. `end_scale` is read only under a disc container (line 613), so the camera-size knob `container.spec.box` is a plan edit.
4. The colour lead does not reach a lifted layer's content. `compose_A` re-colours the base, while morph layers composite `contentA` taken from the un-re-coloured A. This is a renderer gap, and I planned around it with an early `mix_window`.
5. A morph target clipped to the container. Element targets that cross the container's edge (B's 11 and 12) would stretch the box map, so the target became a `box`. Its optimal transport then weighs B's bright sky as mass.

## Process notes

- I did not patch the renderer, as the brief ordered. `mix_window` on a `morph_to` is named in SCHEMA.md only through the guard's arrival ("the end of a transform's `mix_window`") and the recede's parameters. I read it as allowed. The main session should confirm.
- Probes probe_ids used the knob `clouds_become_clouds.a_elements`, which is not in the schema. I used it only to try a cloud set, then wrote the ids into the plan's `a`.
- The hold names a `b` that the renderer does not read. I added it because the brief requires a `b` on every transform that lifts A.
- c2's helper names the model "FLUX.3 image klein distilled bf16", a prompt, two references and a region. Whether that model reproduces A's tower byte for byte outside the region is UNVERIFIED.
- No 1920 px render was made. Every visual claim above comes from 360 × 480 frames.

### Confidence

60 % that c1 answers "rapid zoom out" and "clip into B": the geometry and the guard are measured, and the draft shows no B inside the container's sky before t 0.78. 40 % that the clouds read as "nicely morph into each other". At 480 px the bank still dissolves into B's cumulus more than it re-forms, and the container's straight edges stay visible until the cloud beat ends.

### Gaps

- Rule 5: the rect's top and right edges in the sky (t 0.1–0.8); the right edge beside A's city until the end effect.
- Rule 7: the bank and the cumulus overlapping at t 0.44–0.54 (frames 39–48); the tower dissolving at t 0.76–0.95.
- Rule 8: the tower's masts lie mostly outside element 24's matte (mattes fault 6) and fade with the sky box.
- Rule 11: the camera has no rate field.
