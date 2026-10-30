<!-- Provenance: written by an Opus 5.5 subagent (the skeptic, round 2) of the Claude Code session of 2026-10-30 (the Halloween loops; DECISIONS 2026-10-30); copied verbatim from benchmarks/runs/2026-10-30/halloween/agents/skeptic2.md (sha256 f3f386dae8f29650) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). The second pass on the 16 changed or new candidates of round 2 against the first pass's frame indices: 6 READY, 2 READY WITH A NOTE, 8 NOT READY; two of its fixes (the teleport's box to her boots; the thug c3's blur leg as a cut) were applied after the pass and are not re-judged. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy except where TRANSITIONS.md §13.24 says so. -->

# Skeptic pass 2: Halloween loops round 2 (2026-10-30)

Of the 16 changed or new candidates I judged, 6 are READY, 2 are READY WITH A NOTE and 8 are NOT READY. Most of the defects the first pass named are still there in fewer frames: shortening a RIFE leg cuts how long a ghost lasts but does not remove it.

- READY: zeke-back/c3, zeke-bite/c2, group1/c2, evgen-npc/c3, sveta-head/c2, nose/c2.
- READY WITH A NOTE: evgen-thug/c1 and c2 (a one-frame face ghost at 12), wand/c2 (the hat and the handle are blended at 11–12 and 29–30).
- NOT READY: group-teleport/c1 (her boots and an ear are left behind), group-teleport/c2, evgen-thug/c3 (the round-1 double pumpkin is back at frame 14), zeke-back/c2, zeke-bite/c1, talk/c1, talk/c2, group1/c3.

Crops are in `agents/skeptic2_crops/`. The source column says which crop each finding comes from. "Full size" means the crop was taken at 1:1 or larger. Where I cropped at 0.4–0.5x, the row gives the scale. dexp values are from `measure.json` (dexp_max) and from the per-frame `dexp` in `frames.json`. I did not play any clip at speed. Every call about timing or about how a cut reads comes from consecutive stills.

## group-teleport
| Cand | Verdict | Findings (frame, region, rule) |
|---|---|---|
| c1 | NOT READY | Round-1 defects: the box no longer cuts through her (gone, 13–21), the leopard mask is no longer doubled (gone, nothing is squeezed in) and the glowing rectangle is gone. New defect: **her yellow boots stay standing at full size for all of 14–23** while the rest of her squeezes into the line, because the plan's `out_box` y1 is 0.9 and her boots sit below that. At 23 the boots stand alone under the line, and at the cut (24) they vanish (rules 5 and 8). A crescent of her left pink ear stays on the wall at 19–23. A skin-coloured patch of her right hand stays beside the line at 20–23 (rule 8). At 17–19 a faint smear of her body remains just left of her matte. (`gt_c1_line_a.jpg`, `gt_c1_line_b.jpg`, full size) |
| c1 flash (page claim) | partly true | Frames 22–23 brighten the whole frame, most strongly at the top right. It reads as a bloom of light from her spot, not as a white flash. The flash coincides with the last two squeeze frames instead of following them. The line at 22–23 is still a ragged strip of her clothing, not a clean beam. Step 23→24 is 56.9, the clip's step_max. Under the cut every person changes place, so the shuffle reads as a cut to a different photo, and the flash does not hide it. (`gt_c1_flash.jpg`, at 0.48x) |
| c1 line 16–21 (page claim) | partly true | 19–21 read as a squeeze toward a line. 16–17 read as a white halo glowing around her outline. Seam step 25.6 at the cut back (by design). |
| c2 | NOT READY | A pale rectangle with straight edges around her at 13–16. The box's background comes from the other exposure, so a vertical seam crosses the black-coat man's sleeve and shoulder at 13–14, and at 16 a frosted rectangle stands where she was (rule 5). Squeeze-in at 19–23: a rectangle with a straight left edge and a straight bottom edge, and a second boot drawn outside the box to the right at 20–23 (rules 5 and 7). dexp_max 0.047, seam 5.635. (`gt_c2_out.jpg`, full size; `gt_c2_in.jpg`, at 0.5x) |
First change, c1: `out_box` y1 0.9 → 1.0 (or about 0.97, below her boot soles) and y0 a little lower, so the boots and the ear go into the squeeze. Then re-check frames 19–23.

## evgen-thug
| Cand | Verdict | Findings |
|---|---|---|
| c1 | READY WITH A NOTE | Round-1 frame-18 double pumpkin: gone (the leg is now a cut at 15). Round-1 yellow face ghost (13–14): reduced to one frame. At 12 (dexp 0.058) his eyes and cheeks are tinted yellow under the solid pumpkin. At 13 (dexp 0.1065, the clip's max) two faces are stacked under a blurred pumpkin, but the frame sits inside the real blur, so it reads as blur. Look-up leg 21–26 (dexp up to 0.10 at 24): one face. His left hand smears into two copies at 23–25, as in round 1 (mild, because still k3 is blurred there too). (`thug_c1_lift.jpg`, full size; `thug_c1_lookup.jpg`, at 0.28x) |
| c1 cuts (page claim) | beats, by my eye | 36→37 and 38→39 each read as a push-in: he grows larger each time while the glass edge at the right and the ceiling lamp stay at nearly the same x. Together the two cuts read as a stepped zoom onto the gun, not as a registration glitch. Caveat: I judged this from four stills, not at 25 fps. (`thug_c1_cuts.jpg`, at 0.375x) |
| c2 | READY WITH A NOTE | The same as c1 for frames 0–56. The rewind (57–74) replays photos only (`frames.json`: "none (rewind)"), seam 1.142. I did not crop the rewind, so whether it shows the frame-12/13 ghosts again at triple speed is unchecked. |
| c3 | NOT READY | Round-1 defect is back: the k1→k2 leg is RIFE again (n2 decel). At **14** (dexp 0.1059) a yellow pumpkin ghost covers his face while a translucent pumpkin is already at his belly: two pumpkins in one frame (rule 7, the named defect "the pumpkin doubles"). At 15 the face and hands are faintly doubled. (`thug_c3_k1k2.jpg`, at 0.32x) |
First change, c3: the k1→k2 leg → cut, as in c1.

## zeke-back
| Cand | Verdict | Findings |
|---|---|---|
| c2 | NOT READY | Round-1 double heads: still there. The ghoul's own fade is now confined to his box, but the man's 150 px move is carried by RIFE. At 16–17 the man has two heads and two pairs of glasses, and the girl's face is doubled (teleport `dexp_rest` 0.060 at 16; YuNet up to 4 faces). Blink-out: the girl has two faces at 75 and the man is doubled at 74–75. A straight horizontal edge crosses the girl's jacket at chest height at 14, 16, 17, 74 and 75 (rule 5). Round-1 seam jump: gone (seam 9.007 → 1.515). (`zb_c2_fadein.jpg`, `zb_c2_blink.jpg`, at 0.4x) |
| c3 | READY | Nothing is generated at the appear (16) or the vanish (cut at the seam, seam 23.78). Heads at 28, 40 and 52 are single and clean (`zb_c3_heads.jpg`, at 0.85x). Note for the owner: the pair change pose at the same cut as the ghoul appears, so they visibly "notice". |

## zeke-bite
| Cand | Verdict | Findings |
|---|---|---|
| c1 | NOT READY | Round-1 three-lens ghost: reduced from 2 frames per leg to 1, but still there. At **16** (dexp 0.087) and **25** (dexp 0.093) the face shows three red lenses. At 15 and 25 a translucent vampire face shows beside his cheek (rule 7). New: the smooth ease leaves frame 26 at t 0.84, so the seam jumps the rest: seam_step 8.027 (round 1: 2.014), and at 26 the vampire's hat is still smeared. No wall jump was visible at the ECC boundary (frames 13, 15, 17, 25, at 0.38x). (`bite_c1_in.jpg`, `bite_c1_out.jpg`, at 0.45x; `bite_c1_wall.jpg`) |
| c2 | READY | Two hard cuts into and out of the real blur still. Nothing generated. The wall lines up across 19→20 and 26→0 (`bite_c2_cuts.jpg`, at 0.38x). Step 45.8 and seam 45.4, by design. |

## talk
| Cand | Verdict | Findings |
|---|---|---|
| c1 | NOT READY | Round-1 two-stick wand: reduced to one frame on the poke and two on the settle, but still there. At **14** the wand has almost vanished (a faint stub and a faint vertical); at **24–25** a faded vertical stick and a short horizontal stub show together (rules 7 and 8). His face is half-faded at 14. dexp_max 0.050. The page states this limit itself. (`talk_c1_poke.jpg`, `talk_c1_settle.jpg`, at 0.55x) |
| c2 | NOT READY | The same RIFE limit three times over. The wand is nearly invisible at 11, 17 and 22 (each jab's middle frame). On the slow settle (34–41, n8) a faint vertical stick shows at 36–37, and a horizontal stub plus a ghost show at 38. dexp_max 0.051. (`talk_c2_wand.jpg`, full size; `talk_c2_mid.jpg`) |
First change for both: the morph with anchors on the wand's ends that the page names. A smaller n will not fix a stick that disappears in a single frame.

## wand, group1, evgen-npc, sveta-head, nose
| Cand | Verdict | Findings |
|---|---|---|
| wand c2 | READY WITH A NOTE | The hat brim shows a blend of two poses at 12 and 29, and the black handle is faintly doubled at 11 and 30 (rule 7, mild). The wand itself stays one stick. dexp_max 0.032. (`wand_c2_full.jpg`, at 0.5x; not checked at 1:1) |
| group1 c2 | READY | Two cuts, nothing generated, seam 28.07. I did not crop it. The page's claim of a 12-level brightness jump at each cut is not checked. |
| group1 c3 (morph) | NOT READY | The morph has c1's defects. Two red tridents, one with the child and one in front of the plaid-shirt man, at 15–17 (rule 7, the named defect "a prop that doubles"). The glove lies see-through over the girl's face at 15–17. The eyeball's iris shows through the pumpkin at 15–16. dexp_max reads 0.000 because the morph generates no pixels, but this is a cross-fade that the plan does not declare. (`g1_c3_full.jpg`, full size; `g1_c3_eye.jpg`, full size) |
| evgen-npc c3 | READY | Cuts only. The background stays steady at 6/7 and 13/14 (`npc_c3.jpg`, at 0.27x). Seam 5.5. |
| sveta-head c2 | READY | Hat, face and wand are single at 12–14 and 19–20 (`sveta_c2.jpg`, at 0.43x; not checked at 1:1). dexp_max 0.042. |
| nose c2 | READY | No breath, and the curtain no longer shimmers. The face is single at 15, 22, 29 and 45 (`nose_c2.jpg`, at 0.45x). dexp_max 0.040. |

## Gaps
- No clip was played at speed. Every timing call and every "reads as a beat" judgement comes from stills.
- These were not cropped: the evgen-thug c2 rewind, the group1 c2 cuts, evgen-thug c3's cuts and seam, and the return legs of group1 c3 (37–40; a crop file exists but I did not inspect it).
- Several crops are at 0.3–0.5x; each row gives its scale. A faint ghost could be missed at that size.
- I did not count faces per frame for this pass, apart from quoting the measured ranges on the page.

## Confidence
High for the NOT READY verdicts on group-teleport c1 and c2, evgen-thug c3, zeke-bite c1, talk c2 and group1 c3: each rests on a crop that plainly shows a second copy or a part left behind. Medium for zeke-back c2 and talk c1, which rest on 0.4–0.55x crops. Medium for the READY verdicts, which rest on 3–6 frames per clip at reduced scale.
