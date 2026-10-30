<!-- Provenance: written by an Opus 5.5 subagent (the skeptic, round 4) of the Claude Code session of 2026-10-30 (the Halloween loops; DECISIONS 2026-10-30 round 4); copied verbatim from benchmarks/runs/2026-10-30/halloween/agents/skeptic4.md (sha256 0e434da98037b96a) on the owner's standing order of 2026-10-17. The fourth pass on the two candidates re-graded after round 3: both NOT READY (the teleport: a pale halo along her outline, a stroke and a forearm piece from the right-side colour matte, a grey square on her chest; the ghoul: a stall after the snap under the sine ease, a one-frame stop at each middle still, the speed dropping 2.5× after the second still). Fixes applied after the pass and not re-judged: the cutout's matte applied once (the halo), GrabCut on both sides, a linear profile with the first leg weighted 2 and no frame within 4 % of a still, the snap's blur 2.2 %. A research artifact. -->

# Skeptic pass 4: group-teleport c2 and zeke-back c2, round 4 (2026-10-30)

Both round-4 candidates are NOT READY. group-teleport c2 does what the owner asked (she dissolves out in place and in at the destination, 18 % shorter), but a pale halo outlines her in every dissolve frame, a solid blue stroke runs down her right side at 42–45, and a loose piece of her forearm floats at her old spot at 14–21. zeke-back c2 gets the snap and puts the ghoul behind the man, but the creep is not one constant-speed motion: it stalls for 3 steps after the snap, stops for one frame at each of the two middle stills, and runs about 2.5 times slower after still 2.

Method, as in pass 3: steps from `measure.json`, where steps[i] is frame i to frame i+1 (0-based, the numbering of `frames.json`). A stall is a step below 0.3 while motion is open; a jump is a step more than 3x both neighbours. Crops in `agents/skeptic4_crops/`, decoded from `loop.mp4`, with the scale given per crop. I did not play either clip at speed.

## group-teleport c2 — NOT READY

| check | finding |
|---|---|
| Owner's ask | "just dissolve morph person into background and do inverse in destination, all other people stay as in c2, whole scene 20 % faster" |
| Does it | Yes in kind. Fade-out 10–16 at the right end (fade_out 0.04→0.98), fade-in 16–22 at the left end (fade_in 0.02→0.96), still 1 at 23; reverse 33–45. Both alphas sit near 0/1 at frame 16–17, so she is absent for about 2 frames. 46 frames / 1.84 s against 56 / 2.24 s: 18 % shorter, a 1.22x speed-up. |
| Steps | No stall and no jump inside a dissolve: 3.8–5.1 on 10–21 and 3.7–4.9 on 33–44. Step 9→10 is 0.82 and 22→23 is 1.6 (the ends of the fade). seam_step 3.522 (45→0; round 3: 2.072). step_max 5.074 at 10. |
| dexp | dexp_max 0.0527 (round 3: 0.0529); dexp_rest peaks at 0.0527 at frame 40. |
| Faces | 10–12 per frame against keyframes 11 and 12; 10 at 14, 39, 42. Round 3 dropped to 8. |

Defects:
- **Halo outline, frames 10–14, 19–22, 33–35, 40–45 (rule 5).** A pale band about 15–20 px wide follows her silhouette in every dissolve frame on both sides, plus a flat flange at floor level at 21–22 (left). It is strongest at 42–45, where she is nearly opaque, so the band is not her alpha fading: the fill under her is wider than her cutout [INFERRED from the crops]. `gt_right_out.jpg` (0.8x), `gt_left_in.jpg` (0.76x), `gt_right_in.jpg` (0.82x), `gt_left_out.jpg` (0.95x).
- **Blue stroke, frames 42–45, right side of her body, shoulder to knee (rule 5).** A solid dark-blue line about 8–10 px wide, already a blue smear at 40. Neither still has it; at 0 it is gone, so it pops off at the loop seam. It is the round-3 blue edge, now a full stroke. `gt_right_in.jpg` (0.82x), `gt_patch_series_1to1.jpg` frame 45 (1:1).
- **Floating forearm patch, frames about 13–21, between her right arm and hip at her old spot (rules 5 and 8).** A skin-coloured quadrilateral about 30 px across stays opaque after the rest of her has faded (crisp at 16–17), then fades with the base by 22. It is the gap between her arm and hip that the right-side box matte did not cover. `gt_hand_1to1.jpg`, `gt_patch_series_1to1.jpg` (1:1).
- **Grey square on her white top, frames 19–22 and 33–35 (rule 5).** A flat grey patch about 25 px on her chest, absent from still 1 (frame 23). `gt_left_in.jpg`, `gt_left_out.jpg`.
- **Leopard-mask man doubled, frames 35–37 (rule 7).** A translucent copy of his torso and arm sits beside him in the RIFE base. The owner asked for the others "as in c2", so this is unchanged base behaviour, not new.

Page note: the page gives fade-in as 15–23; `frames.json` has 16–22 with the still at 23.

First knob: on the right side (step 1 `matte_a`, step 3 `matte_b`), change `kind: box, thr 24` to `kind: grabcut`. Both the blue stroke and the forearm patch sit only on the box-matte side. The halo appears on the GrabCut side too, so I expect it to need a change in the slide composite (fill no wider than her alpha), not a plan knob [INFERRED].

## zeke-back c2 — NOT READY

| check | finding |
|---|---|
| Owner's ask | "a more immediate snap from frame 1 to 2 like in c3 but more fluid and with slight motion blur and then nice gradual single clean motion animation (currently still in steps between frames)" |
| Snap | Done: 3 frames (12–14, 120 ms), blur_px 21/29/21, steps 9.52, 7.25, 7.51, 9.76 (11→15). c3 used a hard cut (one step of 29.63). Each snap frame is a whole-frame blend of two stills where both people moved, so at 13 and 65 the man has two heads, four red lenses and two ties, and the ceiling lights double (`zb_snap_in.jpg` 0.35x, `zb_snap_in_heads.jpg` 0.8x, `zb_snap_out.jpg` 0.35x). The plan declares it a blend, so it is not a rule-7 breach. Whether 3 blurred double frames read as "fluid" or as a smeared dissolve is for the owner's eye. The blur is vertical, but the people move mostly sideways between still 0 and still 1. |
| Ghoul | Behind the man, hands on his shoulders, one face each, at 25, 32, 33, 42 (dexp 0.064, 0.057, 0.060, 0.052) at 0.85x (`zb_ghoul_dexp.jpg`). The round-3 pasted ghoul and grey holes are gone. faces_per_frame is 3 on 15–64; 1 at 13 and 65 (the blurred snap). dexp_max 0.0644 at 25. |
| Single motion | Not met. See the step series below. |

Step series of the creep (frames 15–52):
- **Stall after the snap:** steps 15→16, 16→17, 17→18 are 0.00, 0.01, 0.04. Frame 15 is the 1-frame hold on still 1, then frames 16–17 sit at u 0.002 and 0.007. That is 4 near-identical frames (160 ms) right after the snap. The cause is the plan's `ease: sine` across the whole chain; the page and plan title call it "constant-speed", which the plan does not do.
- **Stops at the middle stills:** step 29→30 is **0.26** (neighbours 4.86 and 1.73) at still 2, and 37→38 is **0.15** (neighbours 1.09 and 2.11) at still 3. Both are one-frame stops: the "steps between frames" the owner named. Round 3 had 0.13 at 44 and 0.21/0.23 at 50–51, so the stops are shorter but still there.
- **Speed change at still 2:** steps run 1.9–4.9 on leg 1→2 (18→29, matte_share 0.61) and 1.1–2.1 on legs 2→3 and 3→4 (30→48, matte_share 0.14 and 0.20). Each leg gets the same third of u, so the bigger change on leg 1→2 plays about 2.5x faster.
- **Ease-out into the hold:** 48→49 0.76, then 0.09, 0.03, 0.02 on 49→52; with the 12-frame hold that is about 16 still frames before the snap back. That is acceptable as an ease-out but adds to the stall count.
- No jump outside the declared snaps. seam_step 8.498 is the last snap step (66→0), declared.

Page note: the page numbers frames from 1 (snap 13–15, motion 17–52); `frames.json` and `measure.json` use 0 (12–14 and 16–51).

First knob: `ease` `sine` → `linear` on the `through` segment. That removes the stall at 15–18 and the slow-down at 48–51. It will not remove the one-frame stops at still 2 and still 3 (29→30, 37→38): RIFE frames at t 0.94 and t 0.06 both come out almost equal to the still (dexp 0.0003 and 0.0). Next: weight leg 1→2 more heavily so the speed matches across stills, then check whether `soft` above 0 closes the stops at the stills.

## Gaps
- Neither clip was played at speed. "Fluid", the feel of the 3-frame snap, and how visible a one-frame stop is at 25 fps are judged from consecutive stills and steps.
- The group-teleport crops are at 0.76–0.95x except the 1:1 forearm crops; the leopard-mask man's move and the faces in the back row were checked at 0.76–0.95x only.
- zeke-back: I did not crop the girl's jacket edge (an open item since pass 3) or frames 44–51 at full size.

## Confidence
High on group-teleport: the halo, the blue stroke and the forearm patch are plain at 0.8x and 1:1. High on the zeke-back step numbers. Medium on the zeke-back verdict: the creep has no visual defect I could find, and the owner may accept one-frame stops that the 0.3 rule counts as stalls.
