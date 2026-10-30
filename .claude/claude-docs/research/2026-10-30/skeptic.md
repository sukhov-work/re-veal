<!-- Provenance: written by an Opus 5.5 subagent (the skeptic, round 1) of the Claude Code session of 2026-10-30 (the Halloween loops; DECISIONS 2026-10-30); copied verbatim from benchmarks/runs/2026-10-30/halloween/agents/skeptic.md (sha256 8263ab4337e9743b) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). The skeptic's pass on the round-1 page: twelve candidates, 1 READY, 4 READY WITH A NOTE, 7 NOT READY, every defect from a full-size crop. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy except where TRANSITIONS.md §13.24 says so. -->

# Skeptic pass: Halloween loops round 1 (2026-10-30)

Verdict: READY 1 (sveta-head/c1); READY WITH A NOTE 4 (evgen-npc/c1, evgen-npc/c2, nose/c1, wand/c1); NOT READY 7 (group-teleport/c1, group1/c1, zeke-back/c1, zeke-bite/c1, talk/c1, evgen-thug/c1, evgen-thug/c2). The blocking defects are ghosted second copies of props and faces in RIFE and dissolve frames (rule 7) and, in group-teleport, box edges that cut a person in half (rule 5).

Every defect below was seen in a full-size crop decoded from loop.mp4 and saved under `agents/skeptic_crops/` (file named per row). Numbers are from each candidate's `measure.json` and per-frame `dexp` from `frames.json`. The breath effect cannot produce reflected border pixels: `apply_breath` (loop_seq.py:412) scales by 1 + z·sin²(πu) ≥ 1, so it only ever pushes in. I found no breath border artifact.

## group-teleport/c1 — NOT READY
measure.json: dexp_max 0.052 (dexp_rest, outside the boxes), step_max 7.735 at 44, seam_step 2.169, faces 9–14 against keyframe counts 10–14 (noisy on a group).

| Frames | Region | Defect | Rule |
|---|---|---|---|
| 16, 18 | out_box, the woman in green (right) | The box's left edge (x 0.845) runs through her body. Her left half stays in place while the right half squeezes, so frame 18 shows two half-faces side by side. The wall monitor is drawn twice (16, 18). | 5, 7 |
| 16–22 | out_box border | A glowing rectangle with a straight bottom edge at about y 0.88 and straight vertical sides; it reads as a box, not a beam. | 5 |
| 20, 22 | left of out_box | A translucent ghost of her arm and torso remains in the RIFE region after she has squeezed out. | 7, 8 |
| 22, 24, 26 | in_box (left), leopard-mask man | The in_box (x 0.14–0.30) contains the leopard-mask man from still k1, so the squeeze brings in a second leopard mask while the k0 one stands just right of the box: two masks at 22 and 24. A vertical seam at the box's right edge cuts through his pyjamas and, at 26, through the mask and the orange-hoodie man's pumpkin. | 5, 7, 8 |

Crops: `group-teleport_c1_outbox.jpg`, `group-teleport_c1_inbox.jpg`. The gag does not read: the people around her also change places between the stills, and RIFE cannot move them that far.
First change: out_box x0 0.845 → about 0.79 so the box contains her whole body (her left edge measures at about x 0.80 in frame 13). The in_box problem needs a second change (a box that excludes the leopard-mask man, or a different still pair).

## group1/c1 — NOT READY
measure.json: dexp_max 0.049 (frame 42; frame 17 0.0487), step_max 8.822 at 41, seam_step 2.003, faces 10–13 against keyframes 11–13.

| Frames | Region | Defect | Rule |
|---|---|---|---|
| 17 | child in the striped hat and centre | The red trident is drawn twice at half opacity: once in the child's hands (k0) and once in front of the plaid-shirt man (k1). | 7 (named 10-20 defect: a prop that doubles) |
| 17, 18 | girl in the sequin jacket | A translucent white glove lies over her face at 17 and is still half-transparent at 18. | 7 |
| 17 | eyeball in the top-hat man's hands | The eyeball's iris shows through the orange pumpkin. This is a cross-fade, and the plan does not declare a dissolve here. | 7 |

Crops: `group1_c1_girl.jpg`, `group1_c1_eyeball.jpg`, `group1_c1_faces.jpg`. The same defects are expected at 41–42 on the return leg (dexp 0.046/0.049); I did not crop them.
First change: the two legs' n 12 → 4–5, so the ghost frames last about 2 frames instead of 4–5. This shortens the defect but does not remove it; a clean fix needs these props handled as a dissolve or cut that the page declares.

## evgen-thug/c1 and c2 — NOT READY (both)
measure.json: dexp_max 0.138 (frame 17), the highest of the twelve; frames 13–15 0.075–0.099, 18–19 0.101–0.107, 29–30 0.093–0.101. step_max 51.541 at 44 (the declared cut). seam_step c1 49.644 (cut back, by design), c2 1.182. Faces drop to 0 at 15–18 (c2 also 78) during the motion-blur stills; this is expected for blur.

| Frames | Region | Defect | Rule |
|---|---|---|---|
| 13, 14 | head | A yellow ghost of the pumpkin lies over his face while the solid pumpkin sits above it. | 7 |
| 18 | torso | A translucent pumpkin (the k2 pumpkin) is laid over the hoodie under a ghosted face: two pumpkins in the frame. | 7 (named: the pumpkin doubles) |
| 29–31 | his right hand and the handcuff | The hand and the hanging cuff smear into two faint copies. The real still k3 is blurred there too, so this is mild. | 7 |
| c2 72–78 | rewind | The rewind replays frames 13–19, so the same ghosts appear again, at triple speed. | 7 |

Crops: `evgen-thug_c1_lift.jpg`, `evgen-thug_c1_hand.jpg`. The gag reads: the pumpkin leaves, he looks up, the cut to the gun lands. The 2-frame k4 hold (42–43) before the k5 cut is short enough that it may read as a flash; this is at thumbnail size only. Of the two endings, c2's rewind makes the seam continuous (1.182 against 49.644).
First change: the k1→k2 leg (rife n4 decel) → cut. Still k1 already carries the real motion blur, and a cut removes the frame-18 double pumpkin.

## zeke-back/c1 — NOT READY
measure.json: dexp_max 0.0589 (frame 44), step_max 8.445 at 31, seam_step 9.007, faces 2–4 against keyframe counts 2–3; the 4 is frame 17.

| Frames | Region | Defect | Rule |
|---|---|---|---|
| 13–20 | the man and the girl | The dissolve meant for the ghoul also covers the pair, who change pose between k0 and k1. Frames 16 and 18 show two heads and two pairs of red glasses on the man, and two faces on the girl. YuNet counts 4 faces at frame 17. | 7 (named 10-20 defect: a dissolve inside a region that should move) |
| 74–77 | the same | The 4-frame dissolve back repeats the double heads and faces. | 7 |
| 77 → 0 | whole frame | The return dissolve uses accel ease with n4, so frame 77 is only at t 0.64. The loop then jumps the remaining 36 % at the seam: seam_step 9.007, the largest non-cut seam on the page. | seam |

The three RIFE legs (28–35, 41–47, 53–59) look clean in the crop of 28–35 (`zeke-back_c1_legs.jpg`); I did not crop 41–47 or 53–59. Crops: `zeke-back_c1_fadein.jpg`, `zeke-back_c1_seam.jpg`.
First change: k0→k1 method dissolve → teleport with `mode: fade` and a box on the ghoul, so only the ghoul fades and the pair move by RIFE. Then the return leg needs the same change and an ease that reaches t 1.

## zeke-bite/c1 — NOT READY
measure.json: dexp_max 0.109 (frame 29; 17 0.107, 28 0.086), step_max 17.079 at 17, seam_step 2.014, faces 1–3 against keyframes 1–2 (3 at frame 28).

| Frames | Region | Defect | Rule |
|---|---|---|---|
| 17, 18 | the man's face | Three red lenses: the k0 glasses and a ghost of the k1 glasses turned sideways. | 7 (the 10-20 defect of a faint second eye) |
| 28, 29 | the man's face and the vampire | The same three-lens ghost, held longer because the return leg has 8 frames; a translucent vampire face shows beside his cheek; YuNet counts 3 faces at 28. | 7 |

Crop: `zeke-bite_c1_face.jpg`. The wall behind shows no jump at the k1 boundary at thumbnail size; I did not crop it.
First change: the return leg k1→k0 rife n8 → n3. The slow settle is what makes the ghost readable.

## talk/c1 — NOT READY
measure.json: dexp_max 0.0509 (frame 29), step_max 3.719 at 29, seam_step 1.665, faces 2 on every frame.

| Frames | Region | Defect | Rule |
|---|---|---|---|
| 16 | the wand | The wand fades out horizontally and fades in vertically: a short horizontal stub toward his hand and a faint vertical stick. It does not swing as one stick. | 7 (named: the wand doubles) |
| 29, 30 | the wand | The same on the way back. | 7 |

Crop: `talk_c1_wand.jpg`. The gag reads weakly: in still k1 the wand rests against her shoulder near his chin, not in his face.
First change: the forward leg's n 6 → 3. A swing that short reads as motion blur, and the two-stick frames drop to one.

## wand/c1 — READY WITH A NOTE
measure.json: dexp_max 0.0311 (frame 23), the lowest of the RIFE candidates; step_max 5.073 at 23, seam_step 1.501, faces 2–3 against keyframe 2 (3 at frame 12).
Note: at frames 10–11 a faint second black handle shows under his hands next to the real one (`wand_c1_hands.jpg`). The wand itself stays one stick and the top hat stays whole (`wand_c1_mid.jpg`). The tug reads.
First change: none needed to ship; if the owner names the handle, the legs' n 8 → 6.

## sveta-head/c1 — READY
measure.json: dexp_max 0.0423 (frame 31), step_max 3.106 at 27, seam_step 1.4, faces 1 on every frame.
I found no defect in the hat brim, the wand tip or the eyes at frames 7, 10–14, 18, 30–31 (`sveta-head_c1_head.jpg`, `sveta-head_c1_eyes.jpg`). The sway is small; the owner should judge whether it reads.
First change: none.

## nose/c1 — READY WITH A NOTE
measure.json: dexp_max 0.0408 (frame 28), step_mean 6.046, step_max 10.055 at frame 8, seam_step 2.524, faces 1 on every frame.
Note: the largest step (10.055) falls in the k0 hold (frames 0–13), and the hold steps (5–10) are larger than the snap leg's (frames 14–17, about 3–8). The breath at z 0.02 over 33 frames moves the fine curtain weave more than the twitch changes the face. The face crop at 13, 15, 16, 18, 27, 28, 32 and 0 shows no ghost (`nose_c1_face.jpg`), but the twitch is hard to see.
First change: remove the breath (z 0.02 → 0).

## evgen-npc/c1 (RIFE) and c2 (morph) — READY WITH A NOTE (both)
measure.json c1: dexp_max 0.0468 (frame 45), step_max 2.83 at 42, seam_step 1.441, 21 generated frames (43 %). c2: dexp_max 0.0 (morph, no generated pixels), step_max 3.033 at 28, seam_step 1.799. Faces 1 on every frame in both.
Neither candidate shows a doubled hand, knife or pumpkin edge at frames 9, 13, 24, 28, 41, 45 (`evgen-npc_c1_mid.jpg`, `evgen-npc_c2_mid.jpg`, `evgen-npc_*_hand.jpg`). The two methods are indistinguishable at full size, so c2 is the better choice: same look, no generated content. Note: the three gestures differ only slightly (head tilt, hand angle), so the "NPC idle" gag depends on the owner reading small motion.
First change: none to ship; prefer c2.

## Gaps
- I cropped selected frames only; the return legs of group1 (36–47), zeke-back legs 2–3 (41–59), the evgen-thug c2 rewind (63–82) and the zeke-bite wall were checked at thumbnail size or not at all.
- I did not play any clip at speed, so the pop at the seams (other than measured seam_step) and timing calls are from the step series and the sheets, not from watching.
- I did not open the gifs; the 540 px gif may hide or exaggerate the ghosts differently from the mp4.
- The YuNet face counts on group-teleport and group1 vary by 1–3 across frames that are real photos, so I did not use them as evidence for rule 8 there.

## Confidence
High for the seven NOT READY verdicts: each rests on a full-size crop that shows a second copy of a face, prop or body part. Medium for the READY and READY WITH A NOTE verdicts: they rest on 3–8 cropped frames per clip, and a ghost could sit in an uncropped frame.
