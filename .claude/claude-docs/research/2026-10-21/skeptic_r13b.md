<!-- Provenance: written by an Opus 5.5 subagent (the skeptic, round 13, second pass on the three re-rendered clips) of the Claude Code session of 2026-10-21 (the round-13 session; DECISIONS 2026-10-21), copied verbatim from benchmarks/runs/2026-10-21/agents/skeptic_r13b.md (sha256 cfa300372efa1e50) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

<!-- Provenance: written 2026-10-21 by the round-13 skeptic subagent, second pass (claude-opus-5-5), from the three re-rendered clips (renderer md5 58bee77a21e2c3def6dc3be1623c06a4), their first versions under director_r13/drafts2/, the control and the round-12 references, decoded frame by frame. No render was run; the only files written are this report and director_r13/notes.json. Scratch scripts and arrays are in the session scratchpad under sk13b/. -->

# Skeptic r13b: the three re-rendered clips against their first versions

One of the three re-renders is better and ready. The outward-sky sunset (mismatch_5_r13_c1-out)
lost its rectangle: the 4-px edge step along A's frame is at most 2 levels at frames 12-42,
down from 17-20. The sun-to-sun clip (mismatch_4_r13_c1) lost the gold disc's edge, and the
front now stays at 10.6 levels per 10 px or less against B's own 10.8. The wider fade brings B's
sky, half of B's water and round 12's clamped stripes in from frame 12, so the rule-1 failure
skeptic_r12 named has come back. The pinned RIFE café (mismatch_2_r13_c1-rife) now matches the
control up to frame 44. It replaces the first version's 2-frame squeeze with a 1-frame cut at
frame 45, and its turn between the keyframes is no longer longer than the control's.

Method. I decoded all 90 frames of each clip with cv2. All six md5s match the brief. For the
sunset I re-used the first pass's sun fit and radial profiles (`sk13/sun.py`, `limb.py`). I
measured the frame edges as the largest step over 4 px and over 32 px in row-median profiles
(rows 150-650, for the left and right edges) and column-median profiles (columns 500-1400, for
the top edge). The limb ring is the deepest valley against the profile's envelope out to
2.6 sun radii. The core ring is the largest rim-minus-centre value from a grid search for the
ring's centre. For the sun-to-sun clip I re-used `sk13/m4p.py`: sun centre and 10-px radial bins
in the upper sector. The orange lines are a 15 px white top-hat above 12 levels on pixels that
are dark in A and carry no top-hat line in A or B. Clamped rows are bottom rows within 1.2 levels
of the row above. On the café I used YuNet
(`benchmarks/runs/2026-10-18/face/face_detection_yunet_2023mar.onnx`) restricted to the man's
face (x < 300), NCC of 64 × 64 face crops against frame 0, `rife/k1_canvas.png` and
`rife/k3_canvas.png`, and the first pass's hand box (x 290-460, y 330-800). I re-ran each
measure on the first versions and checked that it reproduced the first pass's numbers before
reading the new ones. Every number below matched except the two named in Gaps.

## mismatch_5_r13_c1-out (outward sky, frame border feather): better, ready

| Rule | Grade | Frames and measurement (method) | First version / bar |
|---|---|---|---|
| 5 frame edge | PASS | 4-px step ≤ 2.0 levels on the left edge and ≤ 3.0 on the top edge at every frame 12-42; 32-px step 4.5-6.5 left, 4-10 top (row- and column-median profiles). mismatch_5_r13_c1 reads ≤ 3.0 and 4-9 in the same places, from the sky's own gradient. The right-edge maximum (7-9 levels at 6-24) is the lamp mast at x 1534-1557, which mismatch_5_r13_c1 also shows | first version: left 18-20 at 12-42, top 16-17 at 12-21, right 17-18 at 6-27 |
| 5 frame edge, early | FAIL, minor | A dark band about 100 px wide along A's left and top border at frames 6-15. At frame 12 luma falls 34 → 19 over x 16-112, and the 32-px step is 13-17 at frames 6-9 (profiles; by eye on crops) | first version and mismatch_5_r13_c1 have a hard 14-18-level border at 6-9 instead |
| 5 limb | PASS | deepest ring ≤ 2.3 levels at every frame 14-33 (2.3 at 17, 1.7 at 18) | first version 2.4 by the same measure; mismatch_5_r13_c1 11.3 at 17; round 12 21.3 at 20 |
| 5/7 core ring | FAIL, unchanged | rim minus centre +20.3, +16.7, +21.1, +13.1 at frames 34-37 | first version +20.7, +16.1, +20.8, +12.8; mismatch_5_r13_c1 +20.0, +14.8, +20.6, +13.1 |
| 1 | PASS (declared surround) | b_inside 0.09 at 12, 0.16 at 15, 0.32 at 18, 0.52 at 21 (info.json); b_inside_first 6 | first version 0.0, 0.003, 0.08, 0.22; mismatch_5_r13_c1 0.37 at 15 |
| 2 | FAIL, unchanged | motion_jumps 0, pauses 2; the bridge vanishes at 50-52 | same |

What else moved (direct differences against the first version, share of pixels more than 12
levels apart): 4-9 % at frames 9-12, 15-31 % at 15-24, ≤ 4 % from 33, ≤ 0.3 % from 48. In the
sun's area (x 510-1410, y < 760) the change is 9-21 % at 15-21 and ≤ 0.3 % from 30. The limb
measure above shows that the change there is the stars arriving earlier, not a new ring. The
edge under the truss steps 22 levels at frame 18 against 26 in the first version (row profile
over columns 300-1600), the same as mismatch_5_r13_c1.

Verdict: better than the first version. Ready. The page must say: the core arrives as a bright
ring at frames 34-37; the bridge vanishes at 50-52; A's frame fades into the stars through a dark
border at 6-15.

## mismatch_4_r13_c1 (sky.radial_width 0.6): worse than the first version, not ready

| Rule | Grade | Frames and measurement (method) | First version / round 12 |
|---|---|---|---|
| 5 front | PASS | steepest radial drop 8.1 / 10.3 / 7.1 / 6.8 / 10.6 / 10.3 / 9.6 levels per 10 px at frames 30 / 33 / 36 / 39 / 42 / 45 / 48; B's last frame 10.9 (10-px radial bins beyond 1.6 sun radii) | first version 24.5 / 25.6 / 17.9 / 16.2 / 14.1 / 10.1 / 9.7; round 12 9.1-13.4 |
| 5 halo | PASS | ring depth 4.3 at frame 30, 4.1 at 36, 5.8 at 45, 7.2 at 60; B 7.1. A faint ring of 9.9 at r 170 px at frame 15 | first version 8.0, 7.4, 4.6, 7.4 |
| 5 city lines | FAIL, unchanged | 2.26 / 2.45 / 2.54 / 2.10 % of dark city pixels at frames 18 / 24 / 30 / 36 | first version 2.48 / 2.70 / 2.82 / 2.24 %; round 12 1.31 / 1.12 / 0.86 / 0.44 % |
| 1 | FAIL, regression | b_inside 0.11 at 12, 0.29 at 18, 0.40 at 21; the sun beat starts at t 0.25, frame 22. B's gold cloud bands show at the top of the frame from frame 12 (by eye on the contact sheet). Water box (x 1100-1800, y 760-1060) distance to frame 89: 14.6 at 12, 12.0 at 18, 10.1 at 21, 10.2 at 36, 7.7 at 48, 5.9 at 54 | first version b_inside ≤ 0.01 to 30, water 14.6-14.9 to 36; round 12 water 8.2 at 12 |
| 5 clamped rows | FAIL, regression | 17 rows at 9, 41 at 12, 48 at 15, 42 at 24, 30 at 36, 23 at 42, 17 at 48, 7 at 60 | first version 0 until 42, 16 at 48; round 12 49 at 12, 48 at 15, the same counts from 15 on |
| 7 | FAIL | the water changes in two steps: half over 12-21, a hold to 39, the rest over 42-54 | first version one dissolve over 39-54 |
| 2 | PASS | motion_jumps 0, pauses 1 | same |

The renderer and the knob both changed between the two versions, so I cannot say which one
brought B forward. Both new clips moved b_inside_first to frame 6, against 18 and 33 before.

Verdict: worse than the first version. It fixes the front (17.9 → 7.1 levels per 10 px at frame 36)
and brings back round 12's early water and stripes (0 → 41 clamped rows at frame 12). Not ready.
If it goes on the page it must name B's clouds and water arriving at 12-21 and the vertical
stripes at the bottom at 9-42. The first version with its gold front at 36-42 is the better
candidate of the two.

## mismatch_2_r13_c1-rife (times pinned to the control): better than the first version on the matte, worse at the cut; not ready

| Rule | Grade | Frames and measurement (method) | First version / control |
|---|---|---|---|
| outside the matte | FAIL by 0.33 points | pixels outside `chain_matte.png` (value > 0) more than 12 levels from the control: ≤ 0.05 % at 0-24, ≤ 0.28 % at 25-58, 0.50 % at 59, 0.70 / 0.83 / 0.63 % at 60 / 61 / 62, 0 from 64. The differing pixels lie a median 6-14 px and at most about 25 px outside the matte edge. With the matte grown by 9 px the maximum is 0.46 % (frame 61). With the matte cut at 50 % (value > 127) the maximum is 2.0 % (60-61) | first version up to 37.9 % at 32 (grown 9 px) |
| glide | PASS | the face box reaches (33, 299) at frame 44 in both clips; frames 0-44 equal the control | first version landed at 60 |
| 6 / 3 identity | FAIL | A → first keyframe in one frame: NCC to A 0.65 → 0.26, to k1 0.44 → 0.96 at 44 → 45; face-crop step 23.5. k1 → k3 over 46-53: NCC to k3 0.41 → 0.90. One face of the man in every frame 36-89 | first version: A → k1 over 57-59, k1 → k3 over 61-77; control: A → k1 over 46-51, k1 → k3 over 56-63 |
| 2 | FAIL | whole-frame step 7.3 at 44, 20.7 at 45, 3.0 at 46; then 0.6-1.1 at 55-64, so the frame nearly freezes for 10 frames. motion_pauses 21, jumps 4 (info.json) | first version stop at 59-60 (11.0 → 1.4), pauses 3; control 6.6 → 3.2 at 44-45, pauses 14 |
| 1 | FAIL | pale silhouette of B's hand at 31-41, identical to the control (42 % of the hand box at 40). B's hand with the phone is there at 43-44 (box 9 levels from B) | control the same; first version 38-55 |
| 7 / 8 | FAIL | the hand vanishes at the cut (box 54-57 levels from B at 45-48). At 49-53 it returns as a translucent hand over the face of the woman in green (by eye on full-size frames). It is solid from 54 (box 17 → 14 levels) | control: hand present 43-48, gone 52-58, back 62; first version: smear at 66-70 |

The turn between the two keyframes now takes about 8 frames, the same as the control's 56-63.
The first version's 16 frames came from the slower glide, not from the in-betweens. With the
times pinned, the in-betweens only replace the control's dissolve over the same span. The cut at
45 comes from placing k1 at t 0.4 (frame 36) while the man stays A's until the glide lands at
frame 44 [INFERRED from info.json `times` and the face track].

Verdict: better than the first version on the comparison (37.9 % → 0.83 % outside the matte),
worse on the face (a 1-frame cut instead of a 2-frame squeeze). Not ready.

## Across the round

Which sunset first: mismatch_5_r13_c1-out. It has no limb ring (≤ 2.3 levels against 11.3 at
frame 17) and no rectangle now. mismatch_5_r13_c1 still shows his limb for 3 frames. Both carry
the same core ring at 34-37 (21 levels at 36) and the bridge at 50-52. The page should name the
dark border band at 6-15 on the first and the limb at 16-18 on the second.

Should the RIFE variant be on the page: no, not this round. The pinned render answers the
first pass's confound, and it shows that RIFE does not lengthen the turn (8 frames, as in the
control). It adds a one-frame cut at 45 and a near-still stretch at 55-64. His 2026-09-29
condition "realistic (for a given context)" fails at 49-53, where a translucent hand lies over
the woman's face. Rule 8 fails there too. If it is shown anyway, the page must label it as
generated and name the cut at frame 45, the translucent hand at 49-53 and the still frames at
55-64. A re-render with k1 placed at the glide's landing (t about 0.49, frame 44) and the chain
spread over 0.49-0.8 would test whether the in-betweens help at all.

### Confidence: 80%

85 % on the sunset: the edge and ring measures reproduced the first pass on the first version
before I read the new one. 80 % on the sun-to-sun clip: the front, halo and clamped-row measures
reproduced exactly, my city-line measure reads 0.2-0.5 points higher than the first pass's, and
the clouds at the top are by eye. 75 % on the café: the face track, the steps and the matte
shares are measured, while the translucent hand at 49-53 is by eye.

### Gaps

- I did not watch any clip at speed; the cut at 45 and the still frames at 55-64 are frame
  measurements, not viewings.
- My edge-under-the-truss numbers (22 and 26 levels at frame 18) do not reproduce the first
  pass's 32 for the first version; I used columns 300-1600 and give only the comparison
  between clips.
- My city-line share reads 2.2-2.8 % on the first version against the first pass's 1.7-2.3 %;
  the comparison between clips uses one measure throughout.
- The bar "outside the matte" depends on where the soft matte is cut; I report three cuts.
- I cannot separate the renderer change from the radial_width change on mismatch_4.
- Tool failures: two inline Python commands failed with syntax errors and were rerun from
  script files. The first face run chose the woman's face as k3's face and was rerun restricted
  to x < 300. No other tool failed.
- In passing I found that mismatch_5_r13_c1 has a hard top border of 15 levels at frame 12 and 7 at
  frame 15, which the first pass did not report. Its note is left unchanged, as the brief asked.
