<!-- Provenance: written by an Opus 5.5 subagent (the skeptic, pass 2) of the Claude Code session of 2026-11-01 (the seasons loop; DECISIONS 2026-11-01); copied verbatim from benchmarks/runs/2026-11-01/seasons/agents/skeptic2.md (sha256 d5a42a10b2108774) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). The pass on the first four round-2 renders (the crossing sheets, 1920 px prep): mirrored content inside a carried sheet (up to 31 % of a sheet: a picture sliding diagonally runs out of picture at the frame corners and the reflect fill mirrored it), a corner shadow before the sheet enters, two facing contact shadows turning the gap between the sheets into a tube, a 21 px blur erasing detail, a colour cast ahead of the sheet on an object plate; s4 READY WITH A NOTE, the others NOT READY. Five fixes followed (a validity mask instead of any border fill, a 75 % output crop on a 3600 px prep so a drift stays inside the margin, the shadow from the front sheet's leading edge only and faded at entry and exit, shutter 0.1, lead 2) and the set was re-rendered and judged again in pass 3; the judged renders are under round2a/. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# Skeptic pass 2: the seasons loop, round 2 (2026-11-01)

Verdicts: s1 NOT READY, s2 NOT READY, s3 NOT READY, s4 READY WITH A NOTE. Three of the four clips show mirrored
content inside the moving sheets: s1 and s2 badly, s3 lightly. s4 has none, but s4 is a wipe over still pictures, not
pictures that move. I judged frames decoded from each `loop.mp4` (1878×1420, 119 frames), using crops at 1:1, 2× or 4×
under `agents/skeptic2_crops/`, plus `frames.json` and `measure.json`. I did not play any clip at speed or re-render anything.

## The defect in s1, s2 and s3: mirrored content inside the sheet
`frames_sheets` in `scripts/research/loop_seq.py` moves a sheet's picture by `carry × d` with
`cv2.remap(..., borderMode=cv2.BORDER_REFLECT_101)`. When a diagonal band is shifted along its normal, its corner
pixels sample from outside the source rectangle, and the reflect border fills those pixels with a mirror image. I counted
them from the sheet geometry in `plan.json` and `d` in `frames.json` (scale applied, parallax not):

| clip | carry, width | sheet pixels sampled outside the source, worst frame |
|---|---|---|
| s1 | 1.0, 0.85 | 31.0 % of each sheet at f60 and f88 (402,168 px); 23 % at f66; 20 % at f80 |
| s2 | 1.0, 0.75 | 24.7 % at f60 and f88 (295,916 px) |
| s3 | 0.2, 0.80 | 3.9 % at f60 and f88 (48,903 px) |
| s4 | 0.0 | 0 |

What the mirror looks like in the crops:
- s1 f60: a Rorschach copy of late autumn's foreground. The graffiti wall appears twice and the yellow marks are
  mirrored (`s1_f60_mirror_trees_1x.png`).
- s1 f81: the wall appears twice, the bare tree is mirrored, and a bush becomes a green diamond on the lawn
  (`s1_f81_mirror_grass_1x.png`; also f76–f80 in `s1_crossing_f70-80_third.jpg`).
- s1 f88: the wire folds into a sharp "<" across the sky (`s1_f88_wire_chevron_1x.png`); the same happens at f67 and f70.
- s3 f67 and f81: the same wire "<", at half strength under the overlap (`s3_f67_wire_chevron_1x.png`).

The brief expected no mirrored or foreign content. He asked for "no ugly cheap 2d effects" and told us to "check all
previous runs issues", so the mirror decides the verdicts for s1–s3. The `sheets` paragraph in `SCHEMA.md` (lines 71–89)
does not mention the reflect fill. The only knob that removes the mirror is `carry` 0. Keeping the moving pictures needs
a code change [INFERRED: pad the source by the largest `carry × |d|`, or clamp the offset so every sample stays inside].

## Defects in all four clips
- **A dark corner appears before the sheet does, and disappears in one frame at the loop seam.** At f30 the top-right
  12×6 px corner falls to 0.686–0.689 of its f29 brightness, although no sheet pixel is visible yet: the contact shadow
  (0.35) is drawn while the sheet is still inside the 1.5 px feather margin beyond the frame. Going from f118 back to f0,
  the bottom-left corner brightens by the same amount (f118 is 0.676–0.688 of f0). Crop:
  `s1_corners_TR_f29-30-31_BL_f117-118-0_4x.png`. Severity LOW: the darkened triangle is about 3,800 px [INFERRED from
  `shadow_px` 56 at 62°]. It is still a one-frame change at the start and end of the hold, and he ruled out flashes.
- **The strip of summer between the two sheets looks like a glossy rod.** Before the sheets meet (about f50–f60) and
  after they part (about f88–f95), both sheets' contact shadows fall into that strip from opposite sides. The strip turns
  into a blue cylinder with a light centre (`s4_f60_gap_tube_1x.png`). In s3 at f67, the front sheet's edge with shadow
  on both sides looks like a grey tube (`s3_f67_wire_chevron_1x.png`). Severity MEDIUM: it reads as a third object, not as
  two sheets lying on the scene. Whether it reads that way in motion is UNVERIFIED.
- **Step series:** the change rate drops at f59→f60 and rises at f87→f88 in every clip (s4 4.75 → 2.51, 1.9×; s3
  14.34 → 12.88; s1 24.95 → 23.53; s2 21.39 → 19.39). No step exceeds 3× its neighbours. These are the frames where the
  gap between the sheets closes and reopens [INFERRED from `d` and the widths].
- **Hold and seam:** no landing pop. Steps 0–28 are 0.00–0.01, and no picture lands; summer is the only still held. The
  seam step (f118 → f0) is 0.97–1.02, against 0.04 at the first sheet frame; the corner shadow above is part of it.
- **The gif (s1):** 119 frames at 40 ms, looping, 540×408. A 240×100 px sky patch at f10 has 30 colours in the gif and
  1,226 in the downsized mp4, and shows dither speckle at 4× (`s1_gif_vs_mp4_sky_f10_4x.png`). Severity LOW.

## s1 cross (carry 1, opaque front): NOT READY
| check | result | crop |
|---|---|---|
| three pictures slide, pass, summer at the end | yes: each sheet enters at f31–f32 (133 px), they cross at f74–f75 (d ±75), and leave by f118 (moving 1.3 px/frame) | `s1_overview_f40-100.jpg` |
| all three on one frame | f50–f100. At f74 the back sheet shows only as a band about 150 px wide at the top-right, with summer beyond it [geometry] | `s1_crossing_f70-80_third.jpg` |
| mirrored content | yes, up to 31 % of each sheet | crops above |
| back sheet emerging at the crossing | clean: a dark wedge at the bottom-left at f76, the fog sheet with its shadow at f78 | `s1_crossing_f70-80_third.jpg` |
| wire inside a moving sheet | sharp, no comb; folded into a "<" by the mirror at f67–f88 | `s2_vs_s1_f74_wire_blur_2x.png` |

Defects: the mirror (HIGH, f50–f100), the rod (MEDIUM), the corner shadow (LOW). First knob: `carry`. At carry 0.2,
s3's geometry gives 3.9 % [INFERRED for s1's width 0.85]; carry 0 gives none. Keeping carry 1 needs the code change.

## s2 cross, mixed and blurred: NOT READY
| check | result | crop |
|---|---|---|
| mechanism, all three | as s1, f50–f100 | `s2_overview_f40-100.jpg` |
| mirrored content | up to 24.7 % of each sheet: the wire "<" at f60, f67 and f88, a mirrored lawn at f88 | `s2_overview_f40-100.jpg` |
| blur at the crossing | edge 70.9 px/frame × shutter 0.3 = a 21 px streak, 11 sub-samples (`frames.json` f72–f81) | |
| does the blur hide content | yes. At f74 the tower block's windows cannot be read at 2×, while s3 and s4 show the same block sharp; at f81 the trees are smeared | `s2_s3_s4_f74_overlap_skyline_2x.png`, `s2_f81_ghost_1x.png` |
| wire comb | none at 2×; the wire becomes a pale band about 30 px wide with a light centre stripe | `s2_vs_s1_f74_wire_blur_2x.png` |
| overlap | the two pictures move in opposite directions and mix 50/50, so the overlap is a double exposure with the scenes 2·d apart (142 px at f74) | `s2_f81_ghost_1x.png` |

Defects: the mirror (HIGH); a blur that erases detail rather than reading as speed (HIGH; he asked for "small motion
blur"); the misregistered double exposure (MEDIUM); the corner shadow (LOW). First knob: `shutter` 0.3 → 0.1 or lower
(about a 7 px streak at the crossing [INFERRED]), then `carry` as in s1.

## s3 drift with depth: NOT READY
| check | result | crop |
|---|---|---|
| mechanism, all three | yes, f50–f100; summer at f118 | `s3_overview_f40-100.jpg` |
| mirrored content | up to 3.9 %; the wire "<" is visible at f67 and f81 | `s3_f67_wire_chevron_1x.png` |
| borders while sliding | not aligned: at f52 the horizon inside the left sheet sits about 130 px lower than summer's at the edge | `s3_f52_f60_spruce_parallax_1x.png` |
| parallax at the spruce | no tear or stretch at 1:1 at f52 or f60. The near-far difference is about 0.06 × 2 × 290 px ≈ 35 px at entry, spread over about 30 frames [INFERRED]; whether it reads as depth at speed is UNVERIFIED | same |
| 1 % scale at the crossing | no doubling visible at 2× on the tower block at f74. The contents are 2 × 0.2 × 73 ≈ 29 px apart, plus up to 9 px from the scale at the frame sides [INFERRED]; the low-contrast fog picture hides it in this crop | `s2_s3_s4_f74_overlap_skyline_2x.png` |

Defects: the wire "<" (MEDIUM: small, but he will see a mirror), the rod (MEDIUM), the corner shadow (LOW). First knob:
`carry` 0.2 → 0.1 [INFERRED: about halves the mirrored share]. The code change is the real fix.

## s4 wipe with objects: READY WITH A NOTE
| check | result | crop |
|---|---|---|
| mechanism, all three | the edges sweep and the pictures stay still; all three show f50–f100 | `s4_overview_f40-100.jpg` |
| mirror, misregistration | none (carry 0); the overlap at f74 is sharp at 2× | `s2_s3_s4_f74_overlap_skyline_2x.png` |
| objects visible? | peak mean abs(frame − k0) inside each box while the whole box is clear of both sheets and their shadows: apartments 12.2 (f104), tower 8.7 (f91), house 10.3 (f91), block 3.9 (f91). f0 against k0 gives 2.85 (codec noise), so the block barely changes | numbers |
| matte shapes (from the diff, not the masks) | tower: the dark block's facade only, the tree in front excluded. House: the matte also takes the foliage and flowering bush below the roof. Block: a small patch near the top of the beige building, not the whole building | `s4_obj_centre_tower_block_house_f50_f58_f93_2x.png`, `s4_obj_tower_f58_2x.png` |
| cast or seam | apartments at f48 (late-autumn plate, alpha 0.84): a grey-brown smudge over the pink facade, just ahead of the incoming sheet's edge. At f104 (early-autumn plate) the change follows the roofline cleanly | `s4_obj_apartments_f40_f48_f104_1x.png` |
| two plates on one object | tower and house fade in both seasons at equal alpha (f54–f100); `composite()` draws early autumn second, so at alpha 1 it hides late autumn | code, `frames.json` |

Defects: the apartments' smudge at f45–f49 (MEDIUM: a colour cast at the matte), the rod (MEDIUM), the house matte
taking vegetation (LOW), the block object barely changing (LOW), the corner shadow (LOW). First knob for the rod:
`shadow_px` 56 → 20 or `shadow` 0.35 → 0.2. For the objects: `lead` 8 → 2, so a plate changes under the sheet's edge
rather than ahead of it [INFERRED].

## Ranking by my confidence that he calls it what he asked for
1. **s4**: no mirror, no ghosting, every border aligned. Risk: he asked for pictures that "move simultaneously … slide
   past each other", and here only the edges move [INFERRED]; he may call it another 2D wipe.
2. **s3**: the pictures drift, which is closer to his motion. The wire "<" and the misaligned border are visible at 1:1.
3. **s1**: the clearest pictures sliding past each other, but up to 31 % of a sheet is mirrored.
4. **s2**: the mirror, a 21 px blur that erases detail, and a 50/50 double exposure.

## Two changes across the set
1. Remove the reflect fill: pad each sheet's source by its `carry × |d|`, or clamp the offset so no sample leaves the
   picture. This is code, not a knob; after it, document the limit in the `sheets` paragraph of `SCHEMA.md`.
2. Weaken the contact shadow (`shadow_px` 56 → about 20, or cast it from the front sheet only), and draw it only while
   its sheet has pixels inside the frame. The first part thins the rod; the second removes the corner shadow at entry
   and at the seam.

## What I could not determine
- Anything that needs playback: whether the rod reads as a rod in motion, whether s3's parallax reads as depth, whether
  s4 reads as sliding pictures or a wipe, and the tempo.
- The exact GrabCut mattes; I read them from frame − k0 differences.
- s3's overlap ghost on a high-contrast area; my one crop of it was on the fog picture.
- The palettes of the s2–s4 gifs (I checked their timing only).
