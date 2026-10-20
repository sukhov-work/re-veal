<!-- Provenance: written by an Opus 5.5 subagent (the skeptic, round 13, first pass on the six clips and the two round-12 references) of the Claude Code session of 2026-10-21 (the round-13 session; DECISIONS 2026-10-21), copied verbatim from benchmarks/runs/2026-10-21/agents/skeptic_r13.md (sha256 66a48b4670762f52) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

<!-- Provenance: written 2026-10-21 by the round-13 skeptic subagent (claude-opus-5-5) of the Claude Code session of 2026-10-21, from the six round-13 clips, the two round-12 reference clips beside them and the round-12 mismatch_1 clip, decoded frame by frame. No render was run and no tracked file other than this report and director_r13/notes.json was written. Scratch work (decoded arrays, contact sheets, measuring scripts sun.py, limb.py, m4p.py) is in the session scratchpad under sk13/. -->

# Skeptic r13: six round-13 clips against the owner's words, his frame and the eleven rules

Three clips improve on their bar and none is ready without a caveat on the page. The sunset
with the shorter recede (mismatch_5_r13_c1) shows his limb for 3 frames instead of 8 and loses
round 12's bright ring at 53-59; the same ring now appears around the core at 34-37. The
outward-sky sunset (mismatch_5_r13_c1-out) has no limb ring at all, but shows A's photo frame
as a straight-edged rectangle for 25 frames. The sun-to-sun clip (mismatch_4_r13_c1) loses the
red disc he named (ring 61 → 8 levels at frame 30) and the early water. It adds a gold disc
front with an edge at 36-42 and brighter orange lines through the city. The zoom-out
(mismatch_1_r13_c1) reads as a zoom-out and keeps B out until the end effect. Its container
edges are visible to frame 30, and the clouds still overlap as two clouds at 39-45. The RIFE
café is smoother only on the second-keyframe turn and worse elsewhere. It also changed frames
outside the man's matte, so it is not a clean comparison with the control.

Method, kept from skeptic_r12 and r12b. I decoded all 90 frames of each clip with cv2 and
compared frames directly against the bar clip and against the clip's own first and last
frames (A and B through the camera at frames 0 and 89). On the sunsets I fitted the sun as the
largest component with R > 200 and G/R > 0.72. I read radial luma profiles in the upper
126-degree sector (above the wire and bridge) in 8 or 16 px bins. "Ring" means the depth of
the deepest valley against the profile's envelope. On mismatch_4 the centre is the blob within
20 levels of the frame's maximum. On mismatch_1 I fitted the container rect per frame by
maximising the gradient along its expected right and top edges, at scale s about the fixed
point (0, 674). On mismatch_2 I used YuNet (`benchmarks/runs/2026-10-18/face/face_detection_yunet_2023mar.onnx`)
for the man's face and normalised cross-correlation of 64 × 64 face crops against frame 0,
k1 and k3. All eight md5s match the brief. The two café clips are 602 × 800, not 1920 px.
Frame numbers run 0-89 at 30 fps.

## mismatch_5_r13_c1 (sunset into Andromeda, recede window [0.15, 0.6]): better than the bar

| Rule | Grade | Frames and measurement (method) | Against round 12 |
|---|---|---|---|
| 1 B before its beat | PASS (declared surround) | b_inside 0.37 at 15, 0.62 at 18, 0.73 at 21 (info.json); stars and sky key through the disc container's surround | same (0.36, 0.55, 0.62) |
| 2 continuous motion | FAIL | The bridge vanishes at 50-52: frames differ from round 12 by ≤ 1.2 levels mean below row 700 at 42-54 (direct difference). motion_jumps 5 at 8-9, 9-10, 10-11, 14-15, 16-17 (info.json motion_px, renderer's threshold 0.5 × median): the starfield key | same |
| 4 shape alignment | NOT RE-MEASURED | the core arrives at the same place as round 12 (frame differences ≤ 0.3 % of pixels above 12 levels from 42 on) | same |
| 5 no foreign edges | FAIL, better | Limb: pale disc and dark ring at 16-18, ring 11-13 levels at 1.7-1.9 sun radii, 4 levels at frame 19 (radial profile). Core ring at 34-37: rim minus centre +9, +14, +22, +17 at r 25-37 px (radial profile round the darkest centre). Edge under the truss +27 levels at row 1047 (frame 18), +20 at frame 24 (column-median profile) | limb 16-23, up to 21 levels; ring at 53-59 (+23 at 57); truss edge +27, +18 |
| 7 declared dissolve | FAIL | the last of A's sun dissolves into the core as a ring (34-37) | same fault, 18 frames earlier |
| 11 rate | PASS | sun equivalent radius 149 → 90 px over frames 17-21, peak 17 px/frame at 19-20, largest frame-to-frame speed change 5 px/frame (29 % of peak); core peak luma 187 → 239 over 32-40 (t 0.36-0.44) | peak 10 px/frame at 24-26; core 52-62 |

His limb against his frame. His frame is round-12 frame 23 (template match 0.995 at 1.5×,
crop x 609-1332, y 259-814). At that frame the profile reads 161 at the sun's edge, a pale
shelf of 88-71 levels out to about 1.4 sun radii, a valley of 55 at 1.6 radii, and 64 at
2.2 radii. This clip reaches the same sun size (equivalent radius about 123 px) at frame 19,
where the shelf decays smoothly from 97 to 59 and the valley is 4 levels deep. The pale disc
with a ring outside it remains only at frames 16-18. So the disc is smaller in time (3 frames
against 8) and shallower at its deepest (13 levels against 21); its radius in sun radii is the
same, about 1.4.

Rapid or a jump: the shrink accelerates over 4 frames (3, 8, 11, 16, 17 px/frame) and
decelerates over 5. No frame changes speed by more than 30 % of the peak. The five
motion_jumps are not the sun; they are the starfield key at frames 8-17, where round 12 had
four. I count it as "rapidly shrink". Whether it reads to him as a jump at 30 fps is
UNVERIFIED; I did not watch it at speed.

Verdict: better. Ready for the page if the page names the core ring at 34-37 and the bridge at 50-52.

## mismatch_5_r13_c1-out (the same, `sky.shape=radial_out`): cleaner at the limb, worse at the frame edge

| Rule | Grade | Frames and measurement (method) | Against round 12 |
|---|---|---|---|
| 1 | PASS, better | b_inside 0.003 at 15, 0.08 at 18, 0.37 at 24 (info.json): B's stars come later | earlier B (0.36 at 15) |
| 2 | FAIL | motion_jumps 0, peak motion 11.6 px/frame at 18 (info.json); bridge vanishes at 50-52 (unchanged) | better in the sky, same at the bridge |
| 5 | FAIL, new fault | No limb ring: ≤ 2 levels at every frame 14-33 (radial profile). A's frame as a rectangle against B's stars: left edge 20-22 levels over 4 px at frames 12-36 (x 16 → 242), top edge 16-18 levels to frame 24, 5-7 at 30-36, gone by 42-48 (column- and row-median profiles; mismatch_5_r13_c1 and round 12 read ≤ 2). Core ring as mismatch_5_r13_c1 (+22 at 36). Truss edge +32 at 18, +14 at 27 | limb gone; a straight rectangle edge about 1700 px long that round 12 does not have |
| 7 | FAIL | the core ring at 34-37 | 18 frames earlier |
| 11 | PASS | sun radius as mismatch_5_r13_c1 within 2 px per frame | |

Does the outward front show an edge of its own? Around the sun, no: the profile at frames
18-21 falls monotonically at about 0.45 levels per px. The edge it brings is at the frame
border, where A's sky survives farthest from the sun and meets B's starfield along A's
photo edge. Does it show B early? No; it shows B later than either other sunset.

Verdict: worse than mismatch_5_r13_c1 because of the rectangle; better than round 12 at the
limb. Show it second.

## mismatch_4_r13_c1 (sun over water into sun over water, `sky.shape=radial_out`): better on his fault, not ready

| Rule | Grade | Frames and measurement (method) | Against round 12 |
|---|---|---|---|
| 1 | PASS (inside the recede's beat, 0.25-1.0) | b_inside ≤ 0.01 to frame 30, 0.18 at 39, 0.76 at 48. Water box (x 1100-1800, y 760-1060) 14.9 levels from B at 36, 14.1 at 39, 8.3 at 48, 5.9 at 54 (direct distance to frame 89). The water and sky arrive with the outward front, which the plan names only as a knob | water in place at 9-12; rule-1 failure gone |
| 2 | PASS | motion_jumps 0, pauses 1 (info.json) | 8 jumps |
| 4 | PASS | the sun ends on B's sun (unchanged plan) | same |
| 5 | FAIL | Red disc gone: ring 8.0 levels at frame 30, 4.6 at 45, 7.4 at 60; B's own last frame reads 7.1 (radial profile). New: the gold front's steepest radial drop 17.9 levels/10 px at r 130 (frame 36), 16.2 at 39, 14.1 at 42; B's own frame 89 peaks at 10.8. Thin bright lines in the city band (white top-hat > 12 levels, 15 px kernel, not in A or B, where A is dark): 1.7-2.3 % at 18-36. Edge-clamped bottom rows: 0 to frame 36, 17 at 48, 7 at 60 | ring 60.6, 56.9, 28.6; lines 0.8-1.0 %; clamped rows 49 at 12 |
| 7 | PASS (declared) | the water dissolves over 15 frames (39-54) under the front | 5 frames |
| 11 | NOT EXERCISED | no rate named | |

His "too distinct orange halo" is gone by the measure that saw it (the ring depth at frames
30-60 is at B's own level). skeptic_r12's rule-1 and rule-7 failure, B's water at frames 7-12, is gone.
The new front is a disc of B's gold sky with a defined edge at 36-42, 1.7 times steeper than
any gradient in B. A's red sky now stands unchanged to frame 33, and the whole sky turns over
36-48. The bright contour lines of the folding city are about 2.4 times the round-12 share.
In round 12 the red disc partly covered them [INFERRED from crops at 24-36].

Verdict: better. Not ready without naming the gold front at 36-42 and the city lines at 18-36.

## mismatch_1_r13_c1 (the zoom-out re-plan; bar: mismatch_1_r12_c1): better, not ready

| Rule | Grade | Frames and measurement (method) | Against round 12 |
|---|---|---|---|
| 1 | PASS | b_inside ≤ 0.011 until frame 66, then 0.08 at 72, 0.38 at 75, 0.90 at 78 (info.json). b_inside_first 39 is a flat 1.0-1.1 % from 36 to 66, about the area of a 14 px feather band round the rect [INFERRED from the rect's perimeter, not measured from the renderer's maps] | 0.024 at 27, 0.13 at 48, 0.31 at 60 |
| 2 | PASS | motion_jumps 0, pauses 1; motion rises from 2.4 at frame 4 to 14.0 at 44 and falls to 0.5 at 85 (info.json) | 3 jumps (9.5 px at 81-82) |
| 5 | FAIL | Right edge of the container (median step over rows y+20 to y+300 at the fitted edge): 54 levels at frame 6, 35 at 18, 20 at 24, 9 at 30, ≤ 3 from 36. Top edge: 56 at 15, 23 at 24, 13 at 30, ≤ 2 from 36. Right edge beside the city at 60-75: 16-row bands up to 50-85 levels, 6-12 of 56 bands above 8. By eye on full-size crops: the container edge cuts A's bank straight at 30-39; a dark drip about 150 px long at the bank's right end at 39-42; A's small upper clouds as flat grey shapes with blue rims at 36-39; a pale patch on B's apartment tower at 77-81; blocks of A's blue sky with straight tops left of the tower at 60-79 | the tower shredded, ghost contours (r12) |
| 7 | FAIL | A's bank and B's lit cumulus overlap as two clouds at 39-45, a remnant puff at 48 (by eye). Share of the container's sky nearer to A than to B: 63 % at 30, 41 % at 39, 20 % at 51, 6 % at 72. End effect: city rect pixels > 20 levels from B 37 % at 73, 17 % at 77, 0.7 % at 84; the tower is see-through at 73-75 | similar overlap, tower tore at 45-57 |
| 8 | FAIL | the tower's masts fade with the sky (the planner's mattes fault 6); the pale patch at 77-81 | |
| 11 | FAIL | the fitted scale is 0.985 at frame 12, 0.76 at 39, 0.5 at 75: smootherstep over the whole clip. "Rapid" has no plan field | the camera tilted |

Does it read as a zoom-out? Yes: one camera move, scale 1.0 → 0.5, with A's frame landing on
the brick block's roof. It is not rapid. The first 12 frames move the rect by 22 px at the
right edge, and the second half of the scale change takes frames 39-75. The rule-7 share above
is confounded by the colour lead, which moves A's sky toward B's from frame 0. I give it only
as the beat's progress, not as a double-exposure measure.

Verdict: better than round 12 on his "clip into B in the middle" (B held to the end effect)
and on "direction". Not ready: the clouds still overlap as two clouds and the container's
straight edges show to frame 30.

## mismatch_2_r13_c1-rife (the café with seven RIFE in-betweens; bar: the control mismatch_2_r13_c1 = round 12): worse overall

| Rule | Grade | Frames and measurement (method) | Against the control |
|---|---|---|---|
| outside the matte | CHANGED | Outside `rife/matte/chain_matte.png` dilated 9 px: pixels more than 12 levels from the control 5 % at 9, 36 % at 33-36, 19 % at 51, ≤ 0.6 % from 57 (direct difference). Cause: the glide lands at frame 60 instead of 45 (YuNet face centre reaches (103, 400) at 60; control (108, 398) at 45), and `motion.held` holds the tree to t 0.63 instead of 0.49 | should be identical |
| 1 | FAIL, worse | pale silhouette of B's hand in the hand box (x 290-460, y 330-800; S < 45, V > 140): 7 % at 36 rising to 46 % at 52, present 38-55. B's hand with the phone fully there at 56-58 (box 8 levels from B at 56) beside A's yellow man | 32-41, peak 42 %; hand at 44-48 |
| 2 | FAIL | the glide stops in one frame: whole-frame step 11.0 at 59, 1.4 at 60. A step at 76 → 77 (face box 1.1 → 6.0). motion_pauses 3, jumps 1 (info.json) | stop at 43-44 (6.6 → 3.2); pauses 14, jumps 3 |
| 6 / 3 | mixed | k1 → k3 takes 16 frames: face match to k3 rises monotonically 0.38 → 0.99 over 61-77. A → k1 takes 2 frames: match to A 0.70 → 0.25 and to k1 0.49 → 0.86 at 57-59 (NCC of face crops) | k1 → k3 over 57-63 (6 frames); A → k1 over 45-51 (6 frames) |
| 7 | FAIL | the woman in green and the hand are doubled at 58-59; a translucent hand at 54 (by eye) | doubled at 48-50 and 57-63 |
| 8 | FAIL | one face of the man in every frame (YuNet). The interpolated hand is a smear at 66-70 (by eye). The hand is present at 56-58, gone at 60-68 (box 52-57 levels from B), back from about 70 | present 44-48, gone 52-58, back 62 |

Where the identity changes: A's face holds to frame 57, becomes k1 at 59, and turns into
k3 smoothly over 61-77; there is no double face. The phone hand that the FL4 probe measured
at 13.6 % double exposure shows in the clip as a smear at 66-70 more than as a ghost. The
torn hand of round 11 (44-51) is now the smear at 66-70. motion_pauses 14 → 3 is real for
the k1 → k3 segment and does not show the 2-frame A → k1 dissolve or the hard stop at 59-60.

Verdict: worse than the control as a clip, better on the k1 → k3 segment alone.

## mismatch_2_r13_c1 (the control) and the two round-12 references

mismatch_2_r13_c1 is byte-identical to the round-12 clip he graded (md5 e5fe7cf2); skeptic_r12's
table stands. I re-measured the hand box (pale share 42 % at 40, B's hand at 44-48, gone 52-58)
and the glide's stop (step 6.6 → 3.2 at 43-44), and both agree. mismatch_5_r12_c1 (md5
0485681a) and mismatch_4_r12_c1 (md5 565f0316) are the round-12 clips he graded, unchanged.

## Across the round

Which sunset to show first: mismatch_5_r13_c1. It answers his limb words with the
smaller change (3 frames of shallower ring against 8) and adds no new edge. The outward
version removes the ring but brings A's photo frame as a straight rectangle for 25 frames. He
has named straight frame borders before ("next frame square borders", 09-13). Show it second
and name the rectangle.

Should the RIFE variant be on the page? Only labelled as generated, with the page saying that
it is not a clean comparison. His 2026-09-29 conditions are "realistic (for a given context)",
"keeping 50+% of objects original and consistent between frames" and "not inventing
completely new objects". The in-betweens stay inside the man's matte and add no object, so
conditions 2 and 3 hold. Condition 1 fails at frames 66-70, where the hand is a smear, and at
58-59, where the woman and the hand are doubled. Rule 8 fails there too. The clip changed
outside the matte (36 % of pixels at 33-36), so his grade would mix RIFE with a slower glide
and a later tree. My recommendation: keep it off the page as a candidate and re-render it with the glide's landing and
the A → k1 segment pinned to the control's frames, so only frames 57-77 differ. If it goes on
the page this round, the page must name the confound.

What the renderer should change next (mechanism, then the measure that checks it):
1. A keyframe-chain change must not move other beats. Pin the lead's end and the guard's
   hold to the control's times when only the chain's keyframes change. Measure: outside the
   chain matte, ≥ 99.5 % of pixels within 12 levels of the control at every frame (now 64 %
   at frame 33).
2. The vacated ring at the core: the recede's last disc fades as a ring (+22 levels at frame
   36 on both round-13 sunsets, +23 at 57 in round 12). Fill the disc's centre with B's core
   before its rim, or end the recede on B's core profile. Measure: rim minus centre ≤ 3 levels
   in the core profile at every frame.
3. `radial_out` meets the frame border: A's far sky survives along A's photo edge. Key the
   surround's A sky under the front as well, or bound the front's reach to the frame edge.
   Measure: the 4-px step along the container edge ≤ 3 levels (now 20-22 at frames 12-36).
4. The outward front's steepness: scale `radial_width` with the front's radius so that its
   gradient never exceeds B's own steepest radial gradient. Measure: on mismatch_4, ≤ 10.8
   levels/10 px (now 17.9 at frame 36).
5. A rect container's straight edge in a zoom-out: apply the colour lead to A's sky near the
   container edge before the edge is large, or feather by a share of the rect's size rather
   than a fixed 14 px. Measure: the right-edge median step ≤ 8 levels from frame 1 (now 54 at
   6 and 35 at 18). The `halo` measure should also be read round the core at small radii;
   today it reads 0.0 at frames 33-39 and misses the core ring.

### Confidence: 75%

85 % on the sunset limb and core-ring numbers: radial profiles on directly compared frames,
and the owner's frame located at 0.995 correlation. 80 % on the sun-to-sun halo and water
numbers. 65 % on mismatch_1: the edge steps are measured on my own fit of the rect, and the
cloud faults are by eye. 70 % on the café: face matching and box shares are measured, and the
hand smear and doubles are by eye.

### Gaps

- I did not watch any clip at speed; "rapidly shrink against a jump" on the sunset is a
  measurement of radius per frame, not a viewing.
- I did not compute b_inside independently; the 1 % plateau on mismatch_1 is an inference
  from the rect's perimeter.
- The rule-7 double-exposure measure on mismatch_1 is confounded by the colour lead; I report
  only the beat's progress.
- Rule 4 (shape alignment at the beat's end) was not re-measured on the sunsets or the zoom-out.
- My first sun-edge script had a sign error and produced nonsense; I replaced it with raw
  profiles and the ring-depth script. One core-ring search minimised instead of maximised and
  was rerun. No other tool failed.
- The café clips are 602 × 800, not 1920 px as the brief says; every café number is at that
  size.
