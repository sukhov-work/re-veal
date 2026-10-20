<!-- Provenance: written by an Opus 5.5 subagent (the skeptic, round 12, 2026-10-21 about 01:35; the six round-12 clips and the three round-11 clips decoded frame by frame) of the Claude Code session of 2026-10-20 (the round-12 session; DECISIONS 2026-10-20), copied verbatim from benchmarks/runs/2026-10-20/agents/skeptic_r12.md (sha256 cdb916046853cb92) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"); folded into `TRANSITIONS.md §13.21`, the page `director_r12/notes.json`, backlog T55–T56. The sunset was re-rendered after this pass with the wire's target set as the director's intention; the second pass on that render is skeptic_r12b.md. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

<!-- Provenance: written 2026-10-20 by the round-12 skeptic subagent (claude-opus-5-5) of the Claude Code session of 2026-10-20, from the six round-12 clips and the three round-11 clips decoded frame by frame. No render was run and no tracked file was edited. Scratch work (decoded frames, contact sheets, measuring scripts) is in the session scratchpad under sk12/. -->

# Skeptic r12: the six round-12 clips against the owner's words and the eleven rules

None of the six clips is ready for the owner's page without a caveat, and two break rule 1. The
window (mismatch_3) matches the accepted round-11 clip: its first 27 frames are the same clip,
its front-layer clipping is unchanged, and the only change is that the two pane dissolves start
later and run about 1.5 times faster at their peak (computed from the renderer's `trapezoid01`,
total span unchanged). It can go on the page. The café (mismatch_2) is the same as round 11 on
balance and is not ready. The tear is gone: the box where B's man showed reads 42–69 levels from
B up to frame 57, against 20.9 at frame 15 in round 11. In its place, the guard shows a flat pale
silhouette of B's man's raised hand for 11 frames (31–41). B's hand then appears beside A's
yellow man at 42–48, leaves at 51–57 and comes back at 60–66. The sunset (mismatch_5) is worse.
The sun now shrinks faster, which answers "rapidly shrink". Two new edges appear: a dark diagonal
band along the streak's path at frames 15–48 (35 levels below the sky) and a bright ring around
the shrunk sun at 55–59. The bridge's motion is unchanged from round 11. Of the three held-out
clips, mismatch_4 breaks rule 1 (B's water and sky by frame 12) and shows a red ring and
smeared bottom rows. mismatch_6 swaps day for night in 6 frames (38–43) and invents grey bars.
mismatch_1 moves continuously but shreds the tower and tears the tree line.

Method, kept from skeptic_r11 and skeptic_r11b. I decoded all 90 frames of each clip with cv2,
made contact sheets of every 6th frame, and looked at single frames and crops at full size. I
computed steps (mean absolute difference between consecutive frames, in 8-bit levels) and
recomputed `motion_px` with the renderer's own DIS recipe; my numbers match `info.json` for r12
and give the r11 series that r11's `info.json` lacks. I compared the first and last frames with
the photos (A is `_S`, B is `_F`, scaled to cover). I tracked named elements by template
matching, colour masks, radial and column luma profiles, and region distances to the end frames.
Clips (md5): mismatch_5 `fd23da82`, mismatch_3 `a2a4d55f`, mismatch_2 `e5fe7cf2`, mismatch_4
`565f0316`, mismatch_6 `2d6009ce`, mismatch_1 `fb2cadab`. Round 11: `cc153097`, `4eefd616`,
`d1dd9762`. Every md5 matches the brief. Frame numbers are 0–89 at 30 fps; coordinates are canvas
pixels.

What the round-12 measures read, in general:
- `b_inside` is computed before the guard is applied (`director_render.py`, the series is
  appended about ten lines before the guard block). It reads B behind A's region whether or not
  the guard covers it. Under container `none` it reads the café background, so it cannot see B's
  hand on mismatch_2.
- `residual_edges` (Canny at 720 px against A and B through the camera) misses the edge-clamped
  bottom rows and the red ring on mismatch_4. On mismatch_3 it reads the generated keyframe's
  trees as foreign edges (5.7 %), which is a false alarm.
- `motion.adjusted` is empty on all six clips: the motion model moved no beat.

## mismatch_2_r12_c1 (yellow man behind a tree into the café): same as r11, not ready

| Rule | Grade | Frames and measurement |
|---|---|---|
| 1 B before its beat | FAIL | Pale share in the hand box (x 290–460, y 330–800) rises from 4.6 % at frame 30 to 43.3 % at 41. That is the guard's fill in the outline of B's man's raised hand, with a hard edge. Between 41 and 43 the box goes from 29.4 to 9.0 levels from B, so B's hand appears at full opacity beside A's man while A's face is still on him (template match 0.83–0.85). |
| 2 continuous motion | FAIL | A's face moves 1.4 px/frame at 13 and 14–15 px/frame at 36–43, then 11.4 at 44, 2.0 at 45 and 0.7 at 46: it stops in one frame. Frames 44–53 read `motion_px` 0.8 (dissolve only). From 66 to 87 only the man changes; the rest of the frame steps at 0.02–0.09. |
| 3 deforms | FAIL | The glide is rigid: template match 0.95–1.00 to frame 28 and 0.82–0.89 to frame 44 at scale 1.00 → 0.88. It now takes 32 frames (13–44), against 16 in r11. |
| 4 shape alignment | FAIL | At 47–50 two head outlines show (the k1 head larger than A's). Eyes and mouth line up. |
| 5 no foreign edges | FAIL | The pale hand silhouette (31–41). A straight-edged pale strip where the tree was (15–27). A pale outline round the head at 45. Ghost contours at 48–63 (`residual_edges` 1.0–2.3 % at 18–60). |
| 6 whole subject | PASS, rest frozen | Face and shirt now change together (face step 2.9, shirt 7.9 at 67–75). r11 changed the face alone at 54–71, then the shirt alone at 72–82. The rest of the frame is frozen from 55 to 89. |
| 7 declared dissolve | FAIL | The chain segments are double exposures: the woman in green doubled at 48–50, a translucent hand at 57–63. The café's `b_luma_reveal` is declared, but it still shows a translucent face at 21–24. |
| 8 nothing invented or missing | FAIL | B's hand is present at 42–48, gone at 51–57 (hand box 30–55 levels from B), and back at 60–66. At 54 the phone floats with no hand, as in r11. |
| 10 depth order | PASS | The man stays in front of the café throughout. |
| 11 rate | PASS | The lead lands at frame 44 (t 0.49), close to the guard's `arrive` (0.4 of the chain under the trapezoid). The plan states no rate. |

His faults against r11:
- "reveal man in B (because of tear …)": reduced in pixels, unchanged in what he sees. The
  tear-box distance to B stays ≥ 42.3 until frame 60 (r11: 20.9 at 15). The guard replaced the
  tear with a pale hand-shaped hole, then shows B's hand before B's man is there.
- "cut out yellow man, move him onto man B": unchanged and longer (32 frames, rigid).
- "transform shape, transform face and finalize rest of image … weird pauses": reduced. Face
  and shirt are simultaneous, and the 7 still end frames of r11 (step 0.0 at 83–89) are now 2
  (88–89). The new order is the café first, then the man alone for 35 frames.
- "very linear": reduced at the start (an eased glide from 1.4 px/frame), worse at the landing
  (14 → 2 px/frame in one frame).

New faults: the pale hand silhouette at 31–41, the hard landing at 44–45, and the hand that
comes, goes and comes back (42–66).

Measures against my eye. `motion_pauses` 14 agrees (frames 68–81, the tail). `motion_jumps` 3
agrees: 42–43 and 43–44 at the landing, 53–54 at k1. `b_inside` reaches 1.0 at frame 42 and
reads the café, not the man. `guard_share_max` 0.327 is the region I see as the pale silhouette.

## mismatch_3_r12_c1 (the window, against the ACCEPTED r11 clip): same, ready

| Rule | Grade | Frames and measurement |
|---|---|---|
| 1 | PASS (declared front) | `b_inside` ≤ 0.66 % to frame 81, first above 1 % at 84. The front layer's clipping over the crowd is unchanged: frames 0–27 differ from r11 by 1.3–1.8 levels mean, with ≤ 0.09 % of pixels above 12 levels. |
| 2 | PASS | `motion_px` identical to r11 within 0.1 (my recompute); 0 jumps; the 3 pauses are frames 79–81, where the camera settles (motion below 1.7 px/frame). |
| 3, 4 | NOT EXERCISED | No body moves. |
| 5 | as r11 | The front's ragged lower edge is unchanged. `residual_edges` 5.7 % reads the keyframe's trees. |
| 6 | NOT EXERCISED | |
| 7 | PASS (declared) | Two pane dissolves. The flag's saturated-blue share halves at about frame 39 (r11: 32). The frames differ most from r11 at 33–39 (up to 28.7 % of pixels above 12 levels) and at 63–72 (up to 13.1 %). Computed from `trapezoid01` (edge 0.35, window 0.30–0.92): the wall-to-trees segment starts slower and peaks at 1.54× r11's linear rate. The crowd-to-forest segment runs from about frame 51 to 82 (r11: 49–82), also 1.54× faster at its peak and slower at the end. |
| 8, 10, 11 | as r11 | The pane's lower band over the reclining man's head (r11b, 36–54) is unchanged. |

His fault "minor clipping of plane B over some people" is unchanged (frames 0–27 equal r11). I
found nothing worse than r11, so there is no regression to block. Whether a faster middle of the
crowd's dissolve reads to him as the round-10 "single frame" fault is UNVERIFIED. The total span
is the same, so I expect not.

## mismatch_5_r12_c1 (sunset behind a bridge into Andromeda): worse than r11

| Rule | Grade | Frames and measurement |
|---|---|---|
| 1 | PASS (declared surround) | The stars and the sky key come through the disc container's surround (`b_inside` 0.39 at 15, 0.61 at 18), as in r11. |
| 2 | FAIL (unchanged) | The bridge deck's top row (column x 500) matches r11 within 2 px at every frame. It rises at −6 px/frame at 25–43, slows to −2 at 45–49, and vanishes between frames 50 and 51 (a row jump of 22–53 px). `motion_px` matches r11 within 0.3 at every frame from 20 on. |
| 3 | FAIL | The recede is a scale; truss and car fragments ride inside the disc at 46–53. |
| 4 | FAIL (unchanged) | At the beat's end (51–57) the disc's centre is 13–15 px from the core (r11: 9–13). The sun arrives as a ring, not as B's blob. |
| 5 | FAIL, worse | New: a dark diagonal band along the streak's path at 15–48. At frame 27, column x 1500 dips to 30 levels against 61–68 around it, about 80 px wide; r11 at the same place reads 61–65. New: a bright ring round the shrunk sun at 55–59. At frame 57 the centre reads 190 and the rim (r 15 px) 207; r11 reads ≤ 3 levels of rim. The dark ring in the sky at 18–24 is in both. |
| 6 | PASS | |
| 7 | FAIL | The last of the disc dissolves as a ring (55–63). |
| 8 | PASS | Nothing invented that I saw. |
| 10 | PASS | |
| 11 | improved | Yellow-disc equivalent radius (G/R > 0.72, R > 200): from 168 px to half at about frame 27 (r11: 37), and 40 px at 42 (r11: about 55). It then holds at 35–37 px from 45 to 57 before the ring. |

His faults: "elements (especially bridge) move a bit discretely": unchanged (deck rows equal to
r11). "sun limb still is not fully uniform": worse (the bright ring at 55–59). "rapidly shrink":
reduced (half radius 10 frames earlier). "neither by the centers nor by shapes": unchanged.
"dissolve into that dense gas": replaced by a ring.

New faults: the dark band at 15–48 (the planner's predicted risk: the guard holds A's dark sky
inside the streak's line) and the bright ring at 55–59.

Measures against my eye. `motion_jumps` 5 at frames 9–15 equals r11's 3 at 10–15: they read the
sky key and the stars, not the bridge, and they miss the deck's vanishing at 50–51.
`residual_edges` peaks at 0.9 % at 24, during the band; it reads 0 at 54–60 and misses the ring.

## mismatch_4_r12_c1 (held out: sunset over water into sunset over water): not ready

| Rule | Grade | Frames and measurement |
|---|---|---|
| 1 | FAIL | B's water is in place between frames 7 and 12: the distance from the water box to frame 0 goes from 1.2 to 13.8 levels, then the box holds at 7.4 levels from B. `b_inside` reads 0.15 at 9 and 0.54 at 12. The plan declares the sky's give-way at 2.6–3.0 s (frames 78–89), so this is about 66 frames early. |
| 2 | FAIL | `motion_px` 2 → 7.7 → 18.0 → 8.8 → 12.8 at frames 7–11 (the water swap). After frame 15 it is smooth. |
| 3 | FAIL | The city folds by optimal transport; B's pylons and cranes appear as silhouettes over A's blocks at 24–36. |
| 4 | PASS | The sun ends on B's sun (scale 0.85, radii 38.8 and 33.0). |
| 5 | FAIL | A red disc of A's sky, about 250 px in radius with a defined boundary, sits on B's gold sky at 18–60. Orange halos sit on the building tops at 24–36. The bottom rows are smeared into vertical stripes (edge-clamped B): 46 rows at frame 12, shrinking to 14 at 48. `residual_edges` (max 0.13 %) misses all three. |
| 7 | FAIL | The water swap takes 5 frames. `b_inside` goes from 0.87 at 81 to 0.98 at 84 (the end effect). |
| 8, 10 | PASS | |
| 11 | NOT EXERCISED | No rate named. |

Against his standing complaints, this clip has a crossfade (the water), rings and bands (the
red disc, the stripes) and B shown in advance.

## mismatch_6_r12_c1 (held out: day city into a starry night): not ready

| Rule | Grade | Frames and measurement |
|---|---|---|
| 1 | PASS (declared front) | The eave and the air-conditioning unit (front 2, 3) enter from frame 37. `b_inside` 0.02 at 27, after the clouds' beat starts (frame 11). |
| 2 | FAIL | Steps 3.6 at 37, 11.0 at 39, 25.6 at 41, 26.9 at 42, 5.2 at 44; median step about 1.9. `motion_jumps` 9, `motion_pauses` 6. |
| 3 | FAIL | The clouds keep their shapes, turn dark grey at 40–42 and are gone by 45. |
| 5 | FAIL | The left frame edge reads 19–21 levels for 4 px at frame 30 (A: 145). Dark rims run along the cloud outlines at 24–36, and a brown band shows where the big cloud's top was. `residual_edges` max 0.34 %. |
| 7 | FAIL | Day becomes night in 6 frames (38–43). The city stays under the night sky at 43–60 and then shows through the trees as a double exposure. `b_inside` goes from 0.31 at 81 to 0.93 at 84. |
| 8 | FAIL | Two flat grey bars at frames 18–36 (frame 30: luma 112–117 against 180 in A, at x 680–830 and 980–1130, y about 940–980). |
| 10 | PASS | The eave stays in front. |
| 4, 6, 11 | NOT EXERCISED | |

Against his standing complaints: a crossfade, a cut-out (the clouds), hard edges and invention.

## mismatch_1_r12_c1 (held out: blue sky over a tower into a brick city): page-able as a probe

| Rule | Grade | Frames and measurement |
|---|---|---|
| 1 | PASS (declared front) | The brick block and the trees rise from below as the front. `b_inside` holds at 0.024 over frames 27–39 and rises from 42, after the tower beat opens at frame 27. |
| 2 | PASS with one jump | `motion_px` climbs smoothly to 14.4 at 42 and falls to 1.2 at 79. It jumps to 9.5 at frames 81–82 (the end effect); `motion_jumps` 3, `motion_pauses` 1. Steps never exceed 8.4. |
| 3 | FAIL | The tower breaks into vertical slivers at 51–63 and ghosts over B's buildings. |
| 5 | FAIL | A white jagged edge runs along the top of the tree line at 57–66. Flat grey plate patches sit bottom right at 45–57. A flat grey ribbon replaces the diagonal streak at 24–36. `residual_edges` peaks at 1.2 % at 60. |
| 7 | FAIL | At 81–83 the remaining blue sky and white buildings switch to B in 3 frames (`b_inside` 0.50 at 81 → 0.96 at 84). |
| 8 | FAIL | The torn tower. |
| 10 | PASS | |
| 4, 6, 11 | NOT EXERCISED or UNVERIFIED | I did not measure the streak's or the cumulus's end shape against B's. |

Against his standing complaints: continuous motion (the best of the three held-out clips) and a
camera tilt that carries the idea, but hard edges, an end crossfade and invention in the tower.

### What works

- The tear on mismatch_2 is gone: B's man no longer shows between the tree and A's man.
- On mismatch_2 the face and the shirt change together, and the clip no longer ends on 7 still
  frames.
- The sun on mismatch_5 shrinks earlier, which is the rate he asked for.
- mismatch_3 is unharmed by the motion model: no frame is worse than the accepted clip.
- mismatch_1's motion is continuous over 80 frames, and its front rising by depth reads as one
  camera tilt.

### Confidence

80 % on the rule-1 and rule-5 findings on mismatch_2, mismatch_5 and mismatch_4: each rests on a
measured number and on the frames I looked at. 60 % on the mismatch_3 verdict: the frame
differences are measured, but the dissolve rates are computed from the renderer's function, not
read off the video. 55 % on the held-out grades of rules 3 and 8, which are judged by eye from
crops.

### Gaps

- I did not measure mismatch_3's pane mix curve from the video. The 1.54× peak rate is computed
  from `trapezoid01`, and the flag's blue share is a threshold proxy.
- The sun's radius on mismatch_5 comes from a colour mask that merges with the core's glow after
  frame 55. The ring's numbers come from a radial profile around a fitted centre.
- I did not run the keyframe screen (faces and hands) on any clip. The hand and phone findings on
  mismatch_2 are box distances plus my eye.
- r11's `info.json` files carry none of the round-12 measures. My r11 `motion_px` is a recompute
  with the same recipe. I did not recompute `b_inside` or `residual_edges` for r11, because both
  need the renderer's maps.
- On the held-out clips I did not check rule 4's end shapes (streak, cumulus, roofline) against
  B's, and I did not compare against any earlier clip of those pairs.
