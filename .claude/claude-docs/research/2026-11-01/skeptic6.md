<!-- Provenance: written by an Opus 5.5 subagent (the skeptic, pass 6) of the Claude Code session of 2026-11-01 (the seasons loop; DECISIONS 2026-11-01 fourth line); copied verbatim from benchmarks/runs/2026-11-01/seasons/agents/skeptic6.md (sha256 979e6cef06b274a7) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). The pass on s7 and s8 (the band experiments on the accepted s6): no content motion; s7 READY WITH A NOTE, s8 NOT READY (its summer bands over the summer base show only as shadow lines); neither keeps 6–10 bands moving (s7 peaks at 7 on 38 frames, mean 3.3); a corner residue at the seam from the feather missing in the travel; the depth map puts the skyline buildings in the sky layer. Three fixes and two denser plans followed (s9, s10). A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# Skeptic pass 6: s7 and s8 against the accepted s6 (2026-11-01)

**s7: READY WITH A NOTE. s8: NOT READY.** Neither clip keeps the 6 to 10 moving bands he asked for. s7 shows at most 7 bands at once, on 38 of 228 frames (1.5 s). s8 shows at most 6 bands that change the season, on 9 frames. s8's four summer bands change no pixel over the summer base. Their contact shadows remain as dark diagonal lines in the sky. Both clips leave a residue of about 50×80 px in the bottom-left corner, and it drops at the seam. Not played at speed; findings come from decoded frames, `frames.json`, `plan.json`, `measure.json` and `loop_seq.py`.

## Against his words
- **"around 6-10 lateral wipes":** I counted the bands per frame with the mask formula of `loop_seq.py` (feather, edge bend and layer weight) on a 1/8 grid. A band counts when its mask exceeds 0.05 on at least 0.3 % of the frame.

  | | max | frames with ≥ 6 | mean over the sweep |
  |---|---|---|---|
  | s7 | 7 | 38 (frames 111-152) | 3.3 |
  | s8, all bands | 8 (on 9 frames) | 70 | 3.9 |
  | s8, non-summer | 6 | 9 | 2.6 |

- **"mix all 3":** s7 has 5 early-autumn and 5 late-autumn bands; summer appears only as the base. s8 drew 4 summer bands out of 12 (b0, b3, b5, b10; the generator weights summer at 0.2).
- **"depth … layers":** s7 has mid ×3, sky ×2, far ×1, all ×4 and **no near band**, so the foreground never crosses in s7. s8 has far ×5, mid ×3, near ×1, sky ×1, all ×2.
- **"lines more blurry and transparent":** One clean edge in s7 (frame 90, row 600) measures 82 px from 10 % to 90 %. That fits the 80 px feather. I found no clean single edge in s8's sky rows 250 and 600 at frame 130: the bands there blend over runs of 400 to 600 px.

## Check table (crops in `agents/skeptic6_crops/`)
| # | Check | s7 | s8 | Evidence |
|---|---|---|---|---|
| 1 | No content motion | pass | pass | Pixels more than 20 levels from any blend of the three stills (shadow factor 0.8-1.0 allowed), outside the object boxes: 577 at frame 0 (codec floor). s7: 317 to 918 at frames 60, 90, 130, 150, 184, 227 (largest cluster 239 px). s8: 382 to 1,862 (largest cluster 636 px, frame 97). All at most 0.035 % of 5.27 M px. `*_i130_blendresid_heat_0.3x.jpg` |
| 3 | Depth layers at 1:1 | The sky layer is depth below 0.06. It covers the skyline buildings and the far hills, so the fog band also hazes the tower block. Its lower boundary runs through the low roofs at y≈980-1040. Soft; no halo or jag seen | Near band at the left tree: no halo or jag seen | `_m2_skyline.jpg` (s7 frame 90, s8 frame 133), `s8_i097_nearband_tree_1x.jpg` |
| 5 | Loop end: last frame against frame 0, pixels off by more than 12 levels | 378 px, max 46, at x 0-55, y 1917-1994. Still falling over the last 6 frames: 2,710 → 378 | 586 px, max 44, same corner. Constant over frames 222-227 | `s7/s8_i227_vs_i0_bottomleft_2x_last_first_diffx5.jpg`. s6 for comparison: 16 px |
| 6 | Objects | Each object rises 2 to 3 times from 5 or 6 bands; alpha changes by at most 0.34 per frame; the tower is on for 108 frames | Tower and left blocks rise once (30 and 31 frames); apartments and house twice | `frames.json` |
| 7 | Tempo and step series | Largest step 3.16 at frame 184. The step rises from 1.68 to 2.86 at frame 180 and stays near 3.1 for 6 frames. No step is above 3× its neighbours | Largest step 2.53 at frame 131; smooth | `measure.json` |

## Defects
1. **Fewer bands than he asked for (both; high against his words).** The count reaches 6 only in a plateau of 1.5 s (s7) or 0.4 s (s8, non-summer).
2. **Shadow lines from the summer bands (s8; medium).** In frame 130, row 200, there are dark strips 34, 71, 30 and 21 px wide at 0.86 to 0.92 of summer brightness, where the content equals summer. They show as about 6 diagonal lines across the sky in `_m1_overviews_i130.jpg`. s7 has one such strip in the same row (31 px at 0.92).
3. **Residue in the corner at the seam (both; low).** Cause: `band()` in `loop_seq.py` sets the band's travel distance (the reach) to `E/2 + Wb/2 + 2 + edge_depth·max(D0)`, which leaves out feather/2. The depth bend holds back near pixels: depth is 0.978 at the bottom-left corner. So a "+" band that exits to the left keeps a mask of about 0.44 on a wedge about 35 px wide. Derived from the code; matches the measured 55×77 px cluster. In s8 the residue comes from b2_early_near, which finishes at frame 147, so it stays on the corner for 80 frames. In s7 it comes from b9_late_all, which is still leaving in the last frames. The residue is visible only in the ×5 difference crop over foliage. [INFERRED] It pops for one frame at the seam.
4. **The "sky" layer is sky plus skyline (both; note).** The fog band takes the far buildings with it.

## First knob
- **Band count:** raise `--dur` or lower `--stagger` so that 0.8·dur/stagger is at least 8, and set `--bands` to 12 or more. For example `--dur 140 --stagger 9 --bands 14`. [INFERRED] Under the sine ease a band is on screen for about 80 % of its sweep.
- **s8's shadow lines:** change the summer bands' per-sheet `key` to 1 or 2 in the plan, or drop summer from the generator's season draw. `--shadow` applies to all bands at once.
- **Corner residue:** no flag turns it off. The fix is code: add feather/2 to the reach in `loop_seq.py`. That code change needs its own decision line.

## s7 against s8
s7 first. It has no shadow lines and every band changes the season. Its weak points are the missing near band and the 7-band ceiling. s8 has more depth layers, but one band in three is summer and shows only as a shadow line.

## What I could not determine
- How the clips read at speed: wipe or smear, the corner pop, whether the shadow lines flicker. I did not play the clips at speed.
- The cause of s7's step rise at frame 180. The object alphas change by at most 0.1 per frame there, so a fading object plate does not explain it.
- Flicker along the layer boundaries across frames. I wrote the frame-91 crop but did not view it. The layer weight comes from the static depth map (`loop_seq.py` 1034-1040), so the boundary cannot move; only the band edge sliding across it changes.
- The gifs; I did not check them.
