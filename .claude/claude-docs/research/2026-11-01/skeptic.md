<!-- Provenance: written by an Opus 5.5 subagent (the skeptic, pass 1) of the Claude Code session of 2026-11-01 (the seasons loop; DECISIONS 2026-11-01); copied verbatim from benchmarks/runs/2026-11-01/seasons/agents/skeptic.md (sha256 a0b7b5b61645a125) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). The first pass on the seven round-1 candidates: none of the six slice candidates clean; the first cell of a cascade switches whole in one frame (c1, c3, c5, c6), two foreign patches inside the lattice's diamonds (c6), a blur-to-sharp landing on every cell; c2, c4, c5, c7 READY WITH A NOTE. Four renderer fixes followed (the record names them); the candidates were re-rendered and judged again in pass 2. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# Skeptic pass: the seasons loop, round 1 (2026-11-01)

Verdict: none of the six slice candidates (c1–c6) is clean. c2 and c7 come closest. c6 is NOT READY because two foreign patches show inside moving diamonds. c1, c3 and c5 share one defect: at the start of each leg the first cell, in the top-right corner, switches whole in one frame instead of sliding in. That is the first thing to fix across the set.

Method: I decoded every `loop.mp4` with cv2 and judged crops at 1:1 or 2× from the decoded frames, plus the `steps` series in `measure.json` and the rows of `frames.json`. I did not play any clip at speed, so motion feel at 25 fps is UNVERIFIED throughout. Crops are in `agents/skeptic_crops/`. The `*_auto.png` sheets are crops picked by a script: the frames where the change is largest in the first leg (leg 1) at the leg start, the wire box, the near tree, the canvas edges and the buildings band.

## Findings shared by all candidates

- **Loop seam.** In c1–c6 the clip ends inside the last leg: the last frame has t = 0.97 and one cell still 10.5 px from rest (c4: 11 px; `frames.json`). Frame 0 is the landed still, so the seam step (1.70–2.26) is the last landing plus encoder noise. In c1, frame 188 against frame 0 differs by 1.5–2.8 mean over the textured lower half. Frames 187→188 differ only inside the last cell. The lower half of frames 188 and 0 has the same mean (72.41 vs 72.39) and the same Laplacian variance (3262 vs 3266). The extra difference is therefore x264 noise across the I-frame at frame 0 and is invisible [INFERRED]. The seam is not a defect.
- **Hold frames.** The decoded hold frames differ from the stills `k0.png`/`k1.png`/`k2.png` by 2.5–2.8 mean (frame 0 vs k0: 2.85). This is encoding (crf 14, yuv420) and applies to every candidate equally.
- **Landing pop.** Every landing goes from motion-blurred to sharp in one frame. Under `ease: smooth` a cell's next-to-last frame is blurred over a 10.5 px move (shutter 0.8), and the next frame is sharp with 3.8 px of travel left. In c1's last cell (near tree, x 20–80, y 1300–1400) the Laplacian variance goes 226 (f62) → 1555 (f63), a 7× jump. A sliver of the old still, about 8 px wide, disappears in the same frame (`c1_landing_zoom2x_f60-63.png`). The same pattern shows on the tower block in c2 (f42 → f43) and on the roofs in c3 (f48 → f49), where the blur at the last in-flight frame looks wider than 10 px (`c2_auto.png` row 5, `c3_auto.png` row 5). Severity: medium; whether it reads as a pop at speed is UNVERIFIED.

## c1 blinds — NOT READY

| Check | Frames | Crop | Result |
|---|---|---|---|
| 1 Borders | 35–41 | `c1_wire_landing.png` | the leading edge is clean; no doubled line or seam line seen |
| 2 Landing | 58–63 | `c1_landing_zoom2x_f60-63.png` | blur → sharp pop, Laplacian variance 226 → 1555 |
| 3 Wire | 33–41 | `c1_wire_landing.png` | one blurred copy of the wire inside the card (a grey bar about 30 px wide); not a comb; a jog at the border |
| 4 Canvas edge | — | — | not isolated for c1; see "Could not determine" |
| 5 Activation | 29–33 | `c1_start_corner_f29-33.png` | the corner cell switches whole at f30 |
| 6 Steps | all | `measure.json` | 29: 0.84 → 30: 0.08 (10×); same at 92 (1.03 vs 0.14) and 155 (0.88 vs 0.01); the stagger sawtooth is mild (44–46: 6.09/5.50/6.19); seam 1.80 |
| 7 Near tree | 58–63 | as 2 | no artefact on the border itself; the pop at landing |
| 9 GIF | f10 | `c1_gif_vs_mp4_sky_f10_4x.png` | all 189 frames at 40 ms, loop 0 (infinite); the sky is dithered (29 colours in a 190×110 patch vs 1339 in the downscaled mp4); dither texture is visible at 4×, no banding |

Defects:
- Corner cell switches whole (rule "no flashes"; f29→f30, f92→f93, f155→f156; `c1_start_corner_f29-33.png`; high). The top-right band, 194 px wide (one full band width, measured from the border line to the corner), goes from blue k0 sky to cloudy k1 in one frame. `frames.json` gives that frame disp 3.8 px. The top-right 468×352 block changes by 12.8 mean. After that the content shifts inside the cell, but the cell's edge stays put through f33.
- Landing pop (see the shared findings; medium).

First knob: I cannot name a plan key that removes the corner switch. It looks like a renderer behaviour for the first cell (its mechanism is UNDETERMINED from the frames). Of the documented keys, `order: centre` (c2) avoids it. For the landing pop: `dur` 12 → 16 cuts the next-to-last delta from 10.5 to about 6 px at the same band width [INFERRED from smoothstep]. Alternatively, a lower `shutter` (0.8 → 0.5) narrows the blur.

## c2 zipper — READY WITH A NOTE

| Check | Frames | Crop | Result |
|---|---|---|---|
| 1 Borders | 29–32, 42–45 | `c2_auto.png` rows 1, 5 | strips grow from thin slivers; the 2× crop at f42 shows a stair-stepped notch where the blurred card meets the roofline |
| 2 Landing | 42→43, 53→55 | rows 3, 5 | the tower block goes from heavy blur at f42 to sharp at f43; the near tree is soft at f53–54 and sharp at f55 |
| 3 Wire | 40–43 | rows 2, 4 | one short blurred dark stub of the k1 wire at the card's leading edge; no comb |
| 4 Canvas edge | 41–43 right edge | row 4 | no mirrored strip visible |
| 5/6 Activation, steps | all | `measure.json` | starts at 0.09/0.29/0.63, no jump; peak 41–42 (10.27, 10.05) and 151–152 (11.45, 12.02); the largest neighbour ratio is 1.2; seam 1.70 |
| 7 Near tree | 53–55 | row 3 | no border artefact |

Defects: the landing pop on the tower block, f42→f43 (medium). It has the highest steps of the across-sliding set (max 12.02).
First knob: `dur` 14 → 18. The expected effect is a narrower blur at landing and a lower peak step [INFERRED].

## c3 chevron — NOT READY

| Check | Frames | Crop | Result |
|---|---|---|---|
| 1 Borders | 44–49 | `c3_auto.png` rows 4–5 | no doubled line; a sharp k0 strip stays visible between blurred cards (old content still uncovered, expected) |
| 2 Landing | 48→49; 57–59 | rows 5, 3 | roofs: heavy blur at f48 → sharp at f49; near tree f57–59 smooth |
| 3 Wire | 39–42 | row 2 | one blurred grey copy per moving card; a jog at the band edge (explained); no comb |
| 4 Canvas edge | 44–46 left edge | row 4 | heavy blur; no mirrored strip identifiable |
| 5 Activation | 29–32 | row 1 | both top corners switch whole at f30 (top-left block 5.3 mean, top-right 7.7) |
| 6 Steps | all | `measure.json` | 29: 0.83 vs 0.06; 88: 0.56 vs 0.07; 147: 1.00 vs 0.02; seam 1.73 |

Centre column: I found no vertical seam after a landing in the crops I took. The hold frames were not scanned for it reliably (my seam detector fired on real poles and was discarded).
Defects: the corner switch (high, as in c1); the landing pop at f48→f49 (medium).
First knob: as for c1 (`order` / `dur`).

## c4 streak — READY WITH A NOTE

| Check | Frames | Crop | Result |
|---|---|---|---|
| 5 Ramp | 29–32 | `c4_auto.png` row 1 | the band fades in over 3 frames; no hard switch; at f32 faint crossed light streaks show inside the band |
| 3 Wire | 32–35 | row 2 | the wire stays sharp across the translucent band during the ramp, then is lost in the streaks; no comb |
| 2 Landing | 52–54 | row 3 | blur → sharp at f53→f54 on the near tree, with the right part sharp a frame earlier |
| 4 Canvas edge | 31–33 right edge | row 4 | a grey-green veil (rolled ground content at partial alpha) covers sky and skyline during the ramp; no hard line from the canvas edge seen (the round-1 wrap line is gone) |
| 1 Borders | 37–40 | row 5 | sky streaks roll down over the trees; a pale wash over the trees at f37 |
| 6 Steps | all | `measure.json` | rises monotonically 0.33 → 19.56 (f37) and falls; no step above 3× its neighbours except the declared ramp start (29→30: 0.33 → 2.80); mean 4.19, the heaviest in the set; seam 2.26 |

Defects: the partial-alpha veil of ground content over sky (f30–f33; `c4_auto.png` rows 1, 4; medium, a taste question). Ground colours smear across the sky for about 1 s per leg (steps above 10 for 15 frames).
First knob: `travel` 0.4 → 0.25 shortens the streak and lowers the peak step. `ramp` 3 → 5 softens the veil but lengthens it [INFERRED].

## c5 wave — READY WITH A NOTE

| Check | Frames | Crop | Result |
|---|---|---|---|
| 5 Constant motion | 30–32 | `c5_seam_front.png` row 2 | the front crosses the skyline cleanly; no seam line |
| 6 Steps | all | `measure.json` | a 3-frame sawtooth (e.g. 24–26: 3.24/3.66/4.19, ratio 1.3); 0: 0.85 vs 1: 0.08 (the corner switch at the clip start); max 5.26; seam 1.71 |
| 2/7 Seam landing, near tree | 114–116 → 0 | row 1 | a blurred summer card covers a dark diagonal strip of the previous still that narrows over f114–116; at f0 everything is sharp; the same pop as elsewhere |

Defects: the corner switch at f0→f1 (step 0.85 vs 0.08; the same top-right bbox as c1; medium, because the clip never rests, so it falls inside continuous motion [INFERRED]). The blur → sharp landing sits exactly on the loop seam.
First knob: `stagger` 3 → 2 removes the 3-frame sawtooth [INFERRED]; the corner switch needs the renderer fix.

## c6 lattice — NOT READY

| Check | Frames | Crop | Result |
|---|---|---|---|
| 5 Activation | 30–34 | `c6_auto.png` rows 1–2, `c6_start_corner_f33-36.png` | f30–32 identical to the hold (active 0, steps 0.00); at f34 a whole diamond, about 300 px, switches at once in the top right (that block changes by 20.7 mean) |
| 4 Canvas edge, top | 39–45 | `c6_edge_top_f39-45_bottom_f48-52.png` row 1 | a peach-coloured patch with a vertical edge at x ≈ 938 (the canvas centre column) and a horizontal edge at y ≈ 95, inside moving diamonds; a second rectangle with axis-aligned edges in the top right at f41 |
| 7 Near tree | 48–52 | same file, row 2 | a violet/chartreuse triangle like a false-colour patch at about x 330–410, y 1290–1420, sharp while its surroundings are blurred; gone at f52; the region changes by 9.5–22.6 per frame |
| 3 Wire | 41–43 | `c6_auto.png` row 4 | two or three blurred wire copies in separate cells; not a comb inside one card |
| 1 Borders | 47–50 | row 5 | the tower block lands sharp at f48 after heavy blur at f47 |
| 6 Steps | all | `measure.json` | 33: 1.37 vs 34: 0.45 (the diamond switch); 139: 1.30 vs 0.41; max 16.32 at 151; seam 2.22 |

Defects:
- Foreign peach patch with axis-aligned edges (frames 41–45; high; cause UNDETERMINED; the centre-column edge points at how the content outside the canvas is filled in).
- Violet/chartreuse patch at the bottom (frames 48–51; high; cause UNDETERMINED).
- Diamond switch at f33→f34 and f138→f139 (high).
- Dead frames 30–32, 82–84 and 136–138 inside a transition (low; they lengthen the hold to 33 frames).

First knob: none is safe before the two patches are explained. Re-render with `lattice_axis: 1` (one slide axis) to test whether the patches belong to one family's slide direction [INFERRED].

## c7 RIFE classic — READY WITH A NOTE

| Check | Frames | Crop | Result |
|---|---|---|---|
| 8 Mid-leg | 43 (dexp 0.388) | `c7_mid_leg_f43_f147.png` rows 1–3 | the tower block's edges are intact and sharp; the wire is single and straight; the sky is a plain blend; the near tree shows a faint double exposure of summer leaves and bare branches |
| 8 Leg 3 | 147 (dexp 0.267) | row 4 | the tower block is half fogged, read as fog lifting; no doubled windows |
| 6 Steps | all | `measure.json` | max 6.89 at 147; 42–44: 5.00/6.42/5.52 then 45: 3.15 (ratio 2.0, under 3×); seam 1.84; 72 generated frames (44.4 % of the clip) |

dexp: 10 frames above 0.2; the maximum is 0.485 at f149. Defects: the double exposure in the near tree around f43 and f147–150 (low to medium; the frames with dexp above 0.45 are 148–149 and I did not crop them).
First knob: this is not a slices plan. More RIFE in-betweens per leg (`n` 24 → 36) spreads the blend; whether that lowers dexp is UNVERIFIED.

## Ranking (confidence the owner calls it clean)

1. c2 zipper: no corner switch; only the landing pop.
2. c7 classic: clean edges; the near-tree double exposure. It does not meet the "sliding" order.
3. c5 wave: the corner switch is hidden in continuous motion; the pop at the seam.
4. c4 streak: the smoothest step series in shape, but the heaviest motion and the veil.
5. c3 chevron: corner switch at two corners; a strong landing pop.
6. c1 blinds: corner switch at every leg start.
7. c6 lattice: two foreign patches and the diamond switch.

## Two fixes across the set

1. **The first cell must slide in, not switch.** In c1, c3, c5 and c6 the first-ranked cell becomes the next still in one frame (step ratio 10× in c1, 3× in c6). The corner of the canvas where the cascade starts is the first thing the eye sees. The fix belongs in the renderer's coverage of the first cell, not in a plan key; c2 (`order: centre`) is the evidence that the other cells wipe correctly.
2. **The landing.** Every cell goes from a 10.5 px blur to sharp in one frame, and on high-detail targets (tower block, roofs, near tree) that reads as a snap [INFERRED for speed]. Plan-level options are a longer `dur` or a lower `shutter`. A renderer-level option is to blur over the motion of the frame being rendered, not the previous one, so that the blur at the next-to-last frame matches the 3.8 px still to travel.

## Could not determine

- Motion at 25 fps: no clip was played at speed.
- The mechanism behind the corner switch and the two c6 patches.
- Whether other legs of c6 carry the same patches (I cropped leg 1 only).
- Mirrored content at the canvas edges in c1 and c2–c4: the edge crops show blur but no identifiable mirrored strip; I did not compare against the mirrored canvas directly.
- c3's centre seam in the hold frames (the automatic seam scan was too noisy to use).
- c7 frames 148–149 (the dexp maximum) were not cropped.
- GIF: frame timing and the sky dither were checked for c1 only; dither crawl between frames was not measured.
