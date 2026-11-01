<!-- Provenance: written by an Opus 5.5 subagent (the readings track) of the Claude Code session of 2026-11-01 (the seasons loop; DECISIONS 2026-11-01); copied verbatim from benchmarks/runs/2026-11-01/seasons/agents/readings.md (sha256 21355d7ea6d095b7) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). Boxes of seven objects on the registered canvas, the skyline rows and the wire intercepts, read by eye from 1–3× crops (±4 px); four of the boxes drive the object plates of candidate s4. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# Seasons readings: object boxes on the registered canvas (1878x1420, x right, y down)

All seven boxes, three skyline rows and two wire intercepts are read below. Three box edges are occlusion lines, not object edges: the tower's base, the fir's base and the apartment block's base. Two edges are unresolved: the wall's left end and the house's right extent.

All boxes are [x0, y0, x1, y1] in canvas pixels, read by eye from cv2 crops with a labelled grid. The target accuracy is ±4 px for edges that are visible; an edge set by an occluder or by darkness is marked as such and is less precise. Crops are in `agents/readings_crops/`; `overview_k0/k1/k2.png` are full frames at 0.6x with a 100 px grid.

| # | object | still read | box [x0, y0, x1, y1] | outline the same on the other stills? | crop file |
|---|---|---|---|---|---|
| 1 | Dark tower block with white window columns (skyline centre) | k0, checked on k1 | [807, 657, 1077, 730]. The top is the highest rooftop box at x 950-975; the main parapet is at y 664-666. The bottom (y 730) is where trees cover it, not the building's base. | Yes for the walls and roofline: k1 agrees within about 2 px. On k2 fog takes most of the contrast; the roofline can be traced at about y 665, and the white columns are faint but sit at the same x. | tower_k0.png, tower_k1k2.png (k1 top, k2 bottom) |
| 2 | Tall fir (dark, conical; middle distance) | k2 (bare season, fir fully exposed) | [645, 705, 782, ~1150]. Tip at (710, 705); widest point about y 985. The bottom is not a visible base: below about 1150 the fir merges with dark trunks and ground. | No. On k0 deciduous foliage covers the fir below about y 960, so only the top part (tip about (708, 725) to y 960) is visible; the left flank at x 645-670 is also partly hidden. On k1 it is partly visible through thinning leaves (overview only). A second, smaller fir stands to its left, x ~590-655, tip ~(622, 765); it overlaps the tall fir's left edge. | fir_k2.png, fir_k0.png |
| 3 | Large apartment block, right edge (pink-orange facade, balconies) | k0, checked on k2 | [1572, 745, 1878, ~995]. The roof begins at x 1572 (chimney); the facade's left wall is at x ~1625. x1 is the frame edge (the block continues off-canvas). The bottom is set by occlusion: lower houses cover the left part from y ~940 and the right part from y ~990. | Yes, same geometry on k2 within about 2 px. Only colour differs: k2 is greyer and darker, and the balcony glazing reads the same. | apt_k0.png, apt_k2.png |
| 4 | Yellow two-storey house with dark roof (centre, below the tower) | k2 (walls visible), roof checked on k0 | [985, 803, 1145, 945]. Roof peak/chimneys at y 803-810, left eave x ~985, right eave x ~1140 at y ~845; the yellow wall is visible to y ~945. | Partly. On k0 the roof outline is the same (brown-red in sun, dark on k2), but the yellow walls are hidden by foliage below y ~870. On k2 a yellow structure with red/blue marks at x 1150-1205, y 878-935, under a dim roof plane, may be a wing of the same house. If it is, x1 becomes about 1205; UNVERIFIED. Note: a different, beige 4-storey block with a grey roof stands just above it, at [~1000, 728, ~1100, ~800]. | house_k0.png, house2_k0.png, house2_k2.png, house3_k2.png |
| 5 | Graffiti wall (long low wall above the lawn) | k0 (right end), k1/k2 (left end) | [~175, 1150, 1750, 1248]. The right end is crisp at x 1750; its top (coping) is at y ~1150 and its foot at y ~1200. The wall runs lower toward the left: the foot is at y ~1245 at x 300-450. The left end is uncertain. Graffiti is clear from x ~300; a white-painted stretch at x 175-300, y 1155-1215 is probably the same wall. | Wall geometry: yes, the same position on all three stills. Visibility differs a lot. On k0 leaves cover x ~0-850 and the chestnut covers x ~1230-1450, so only x ~850-1750 is clear. On k1 and k2 the whole length shows through bare branches. | wallR_k0.png, wallR_k2.png, wallL_k1.png, wallL_k2.png, wallL2_k2.png, lawn_k0.png |
| 6 | Lawn / open ground below the wall | k0, checked on k2 | Open ground [~850, 1200, 1878, 1420] on k0. The sandy patch is [1110, 1205, 1290, 1255]. On k0 the left edge is the near tree's crown, a diagonal from (~780, 1240) to (~1040, 1420). | No, the surface changes. k0 has green grass and a pale sand patch. On k2 the ground is covered in brown leaves, the sand patch is hard to see, and the open ground extends left to x ~0 under bare branches. The flowering chestnut on k0, [~1230, 1210, ~1700, 1420], covers the lawn's right-centre in summer; on k2 it is bare twigs. | lawn_k0.png, lawn_k2.png |
| 7 | Near tree, bottom-left (nearest tree; crown) | k0 | Crown [0, ~870, ~1040, 1420]. On the left the top is at y ~800 (x 0-100) and about 870-900 at x 200-500. The right edge is a diagonal (see row 6). Above y ~1150 the crown's right side merges with mid-distance trees behind the wall (x 780-1150, y 900-1200), so x1 is only firm below the wall line. | No. k2 shows bare branches over roughly [0, ~770, ~650, 1420], with the upper twigs reaching about y 770 at x 50-200. These are seen-through branches, not a solid crown. k1 shows thinning leaves and branches (overview and wallL_k1 only). | neartree_k0.png, neartree_k2.png |

## Skyline rows (k0; the y where the farthest visible thing meets the sky)

- x 400: y 682. The distant land/hills band meets the sky. A tall building just left of it (x 340-395) rises to y ~653; the near roofs start at y ~700.
- x 940: y 664. This is the tower block's parapet. A rooftop box at x 950-975 reaches y 657.
- x 1500: y 677. This is the distant land band; a tree crown at x 1490-1515 reaches y ~681.

## Wire intercepts (darkest-pixel trace; the right intercept was also checked on the 3x crop wireR_k0.png, the top intercept was not viewed)

- k0: top edge (y 0) at x 1037; right edge (x 1877) at y 397. Measured points: (1045, 4), (1071, 16), (1838, 379), (1870, 394).
- k2 agrees within 2 px: top x 1037, right y about 395.
- k1 differs, because the cable sits differently: top x 1044 (+7), right y about 391 (-6).

## Gaps

- The fir's base and the tower block's base are not visible on any still; their y1 values are occlusion lines.
- The wall's left end (x ~175 vs ~300) is not resolved: branches cover it on k1/k2 and leaves cover it on k0.
- The house's right extent (1145 vs ~1205) is UNVERIFIED.
- The near tree's crown cannot be separated from the mid-distance trees above y ~1150 on k0.
- k1 was checked by crop only for the tower block and the wall's left end; the other k1 statements come from the 0.6x overview. No sub-pixel checks were made; all boxes are visual reads at 1-3x.
